# -*- coding: utf-8 -*-
"""言札 · 核心引擎：音频/视频 → 带时间戳的中文稿。

设计要点：
  1. ffmpeg 解码成 16k 单声道 float32，走管道，不落临时文件。
  2. silero-vad 切语音段，切成 3~20 秒的块，避免长音频一次识别。
  3. paraformer 每段识别，同时拿到**每个字的秒级时间戳**。
  4. 全篇拼起来一次性加标点（0.08 秒/337 字，快到可忽略），上下文越完整越准。
  5. 标点加完后，用「非标点字符与 token 一一对应」把句子时间反推出来 —— 句级时间戳就是这么来的。
  6. 全部本地，不联网，不写注册表，不碰用户目录以外的东西。

作者：永远的兰兰｜Lanlan Eternal
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field

import numpy as np

SR = 16000
PUNCT_CHARS = '，。？！；：、,.?!;:'
SENT_END = '。？！.?!'


class _Canceled(Exception):
    """用户点了停止。用它跳出深层循环，别被宽泛的 except 吃掉。"""

# 中文常见标点 → 输出时统一成全角
_TO_FULL = {',': '，', '.': '。', '?': '？', '!': '！', ';': '；', ':': '：'}


def app_dir() -> str:
    """exe 所在目录（打包后）或项目根（开发时）。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_model(rel_candidates) -> str:
    """按候选路径找模型，打包内外都能用。"""
    base = app_dir()
    roots = [os.path.join(base, 'models'), base,
             os.path.dirname(os.path.abspath(__file__)),
             os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')]
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        roots.append(os.path.join(meipass, 'models'))
    for root in roots:
        for rel in rel_candidates:
            p = os.path.join(root, rel)
            if os.path.exists(p):
                return p
    return ''


def ffmpeg_path() -> str:
    if getattr(sys, 'frozen', False):
        p = os.path.join(app_dir(), 'ffmpeg.exe')
        if os.path.exists(p):
            return p
    p = find_model(['ffmpeg.exe',
                    os.path.join('_tools', 'ffmpeg_lite.exe'),
                    os.path.join('_tools', 'ffmpeg.exe')])
    return p or 'ffmpeg'


# ---------------------------------------------------------------- 解码

class DecodeError(RuntimeError):
    pass


def decode_audio(path: str) -> np.ndarray:
    """任何音视频 → 16k 单声道 float32。失败抛 DecodeError。"""
    exe = ffmpeg_path()
    cmd = [exe, '-nostdin', '-v', 'error', '-i', path,
           '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-acodec', 'pcm_f32le', '-']
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=3600)
    except FileNotFoundError:
        raise DecodeError('找不到 ffmpeg，无法解码音频')
    except subprocess.TimeoutExpired:
        raise DecodeError('解码超时（文件过大或已损坏）')
    if r.returncode != 0 or not r.stdout:
        msg = (r.stderr or b'').decode('utf-8', 'ignore').strip().splitlines()
        raise DecodeError('这个文件解不开：%s' % (msg[-1] if msg else '未知错误'))
    a = np.frombuffer(r.stdout, dtype=np.float32)
    if a.size == 0:
        raise DecodeError('这个文件里没有声音')
    return np.ascontiguousarray(a)


def duration_of(path: str) -> float:
    """用 ffmpeg 读时长，读不到返回 0。"""
    cmd = [ffmpeg_path(), '-nostdin', '-v', 'error', '-i', path, '-f', 'null', '-']
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=120)
    except Exception:
        return 0.0
    txt = (r.stderr or b'').decode('utf-8', 'ignore')
    m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', txt)
    if m:
        h, mi, s = m.groups()
        return int(h) * 3600 + int(mi) * 60 + float(s)
    return 0.0


def make_clip_b64(src: str, start: float, dur: float, kbps: int = 48) -> str:
    """切一小段音频给界面播放（校对时听原音），返回 base64 data URI。

    不落盘：临时文件用完就删，目录里不留任何痕迹。
    """
    import base64
    import tempfile
    start = max(0.0, float(start))
    dur = max(0.5, min(float(dur), 90.0))
    fd, tmp = tempfile.mkstemp(suffix='.mp3', prefix='yz_')
    os.close(fd)
    try:
        cmd = [ffmpeg_path(), '-nostdin', '-v', 'error', '-y',
               '-ss', '%.3f' % start, '-t', '%.3f' % dur, '-i', src,
               '-vn', '-ac', '1', '-ar', '16000',
               '-acodec', 'libmp3lame', '-b:a', '%dk' % kbps, tmp]
        r = subprocess.run(cmd, capture_output=True, timeout=90)
        if r.returncode != 0:
            log = (r.stderr or b'').decode('utf-8', 'ignore').strip().splitlines()
            raise DecodeError('切片失败：%s' % (log[-1] if log else '未知错误'))
        with open(tmp, 'rb') as f:
            raw = f.read()
        if not raw:
            raise DecodeError('这段没有声音')
        return 'data:audio/mpeg;base64,' + base64.b64encode(raw).decode('ascii')
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass


# ---------------------------------------------------------------- 语音分段

@dataclass
class SpeechSpan:
    start: float
    end: float


def split_speech(audio: np.ndarray, vad_model: str,
                 min_silence: float = 0.35, min_speech: float = 0.30,
                 max_span: float = 22.0) -> list[SpeechSpan]:
    """用 silero-vad 找语音区间；超长段就地切开，免得识别时爆内存/掉精度。"""
    import sherpa_onnx as so

    cfg = so.VadModelConfig()
    cfg.silero_vad.model = vad_model
    cfg.silero_vad.threshold = 0.5
    cfg.silero_vad.min_silence_duration = min_silence
    cfg.silero_vad.min_speech_duration = min_speech
    cfg.sample_rate = SR
    vad = so.VoiceActivityDetector(cfg, buffer_size_in_seconds=60)

    spans: list[SpeechSpan] = []
    win = 512
    n = len(audio)
    for i in range(0, n, win):
        vad.accept_waveform(audio[i:i + win])
        while not vad.empty():
            seg = vad.front
            st = seg.start / SR
            en = (seg.start + len(seg.samples)) / SR
            spans.append(SpeechSpan(st, en))
            vad.pop()
    vad.flush()
    while not vad.empty():
        seg = vad.front
        spans.append(SpeechSpan(seg.start / SR, (seg.start + len(seg.samples)) / SR))
        vad.pop()

    # 太长就等分切开（切点落在段内部，标点会兜住）
    out: list[SpeechSpan] = []
    for s in spans:
        d = s.end - s.start
        if d <= max_span:
            out.append(s)
            continue
        k = int(np.ceil(d / max_span))
        step = d / k
        for j in range(k):
            out.append(SpeechSpan(s.start + j * step, s.start + (j + 1) * step))
    return out


# ---------------------------------------------------------------- 句子与对齐

@dataclass
class Sentence:
    start: float
    end: float
    text: str
    speaker: str = ''       # 说话人编号（'1'/'2'…），空表示未做分离

    def __post_init__(self):
        self.text = self.text.strip()


def text_from_tokens(tokens: list[str], times: list[float], seg_ids=None):
    """把识别出的 token 还原成人读的文本，并给出**每个字符**的时间。

    paraformer 的英文是 sentencepiece 子词，词内用 '@@' 续接，
    这里把 '@@' 去掉、英文词之间补空格、中文直接连。
    返回的 chars 与 ctimes 严格一一对应，后面切句靠它反推时间。
    seg_ids 给了的话，再返回每个字属于哪个 VAD 段（段边界要强制断句）。
    """
    chars: list[str] = []
    ctimes: list[float] = []
    csegs: list[int] = []
    prev_cont = False
    for ti, (tok, ts) in enumerate(zip(tokens, times)):
        seg = seg_ids[ti] if seg_ids is not None else 0
        cont = tok.endswith('@@')
        body = tok[:-2] if cont else tok
        if not body:
            prev_cont = cont
            continue
        # 一个新词开始（前一个 token 不是续接）：中英之间、英英之间补空格，
        # 中文之间不补，数字之间也不补（免得 "1997" 变成 "1 997"）
        if (not prev_cont) and chars:
            last_a = chars[-1].isascii() and chars[-1].isalnum()
            cur_a = body[0].isascii() and body[0].isalnum()
            if (last_a or cur_a) and not (chars[-1].isdigit() and body[0].isdigit()):
                chars.append(' ')
                ctimes.append(ts)
                csegs.append(seg)
        for c in body:
            chars.append(c)
            ctimes.append(ts)
            csegs.append(seg)
        prev_cont = cont
    return chars, ctimes, csegs


def chars_from_tokens(tokens: list[str], times: list[float], seg_ids=None):
    """SenseVoice 版还原：它的 token 自带前置空格，直接拼就是原文。

    中文是逐字、英文是子词（' tri' 'bal' → ' tribal'），所以
    **不做任何补空格/去 @@ 的处理**，原样拼接，文本与模型输出逐字一致。
    一个 token 里有多个字时（英文子词），在这段时间里按字数均分，
    英文子词一般 2~4 个字母，误差在几十毫秒内，够切字幕用。
    """
    chars: list[str] = []
    ctimes: list[float] = []
    csegs: list[int] = []
    n = len(tokens)
    for i, tok in enumerate(tokens):
        if not tok:
            continue
        seg = seg_ids[i] if seg_ids is not None else 0
        ts = float(times[i]) if i < len(times) else 0.0
        nxt = float(times[i + 1]) if i + 1 < len(times) else ts + 0.08
        if nxt <= ts:
            nxt = ts + 0.08
        step = (nxt - ts) / len(tok)
        for k, c in enumerate(tok):
            chars.append(c)
            ctimes.append(ts + step * k)
            csegs.append(seg)
    return chars, ctimes, csegs


def align_sentences(fixed_text: str, chars: list[str], ctimes: list[float],
                    audio_end: float, soft_limit: int = 120,
                    char_seg: list[int] | None = None) -> list[Sentence]:
    """按标点切句，并用每个字的时间反推句子的起止。

    fixed_text 是标点模型的输出，和 chars 只在标点/空白上有差别，
    所以这里跳过标点和空白，用双指针匹配；万一标点模型改动了字，
    就钳到最后一个已知位置，不抛异常。

    两块要紧的规矩（v0.1.2 之前都错了）：
      1. **标点必须写回句子**。以前遇到标点直接 continue，标点全丢，
         导出的 txt 既没标点、又因为判不出句末而挤成一大坨。
      2. **只在句末标点切句**。以前逗号、顿号、分号都切，
         一句话被剁成四五截，句数虚高十几倍。
    """
    pool = list(zip(chars, ctimes))
    nt = len(pool)
    out: list[Sentence] = []
    buf: list[str] = []
    j = 0
    t_start = None

    def time_at(k):
        if nt == 0:
            return 0.0
        return pool[min(max(k, 0), nt - 1)][1]

    def close(t_end, tail='', force=False):
        nonlocal buf, t_start
        txt = ''.join(buf).strip()
        if txt:
            if tail and not txt.endswith(tail):
                txt += tail
            elif force:
                # 在停顿处硬切开的句子，末尾若还挂着逗号，补个句号收尾。
                # 不补的话这段文字判不出句末，导出 txt 时又挤成一坨。
                while txt and txt[-1] in '，、；：,;:':
                    txt = txt[:-1]
                if not txt or txt[-1] not in SENT_END:
                    txt += '。'
            a = t_start if t_start is not None else time_at(j)
            b = t_end if t_end is not None else a + 0.6
            if b <= a:
                b = a + 0.4
            out.append(Sentence(round(a, 2), round(min(b, audio_end), 2), txt))
        buf = []
        t_start = None

    for ch in fixed_text:
        if ch in '\n\r':
            close(time_at(j))
            continue
        if ch in PUNCT_CHARS:
            full = _TO_FULL.get(ch, ch)
            if ch in SENT_END:
                close(time_at(j), tail=full)     # 句末：切，并把标点带上
            else:
                buf.append(full)                 # 句中标点：留在句内
            continue
        if ch.isspace():
            continue
        # 标点模型会吃掉中英文之间的空格，所以文字一律以 pool 为准，
        # 它只负责告诉我们"在哪儿断句"。
        while j < nt and pool[j][0].isspace():
            buf.append(' ')
            j += 1
        if j >= nt:
            break
        # VAD 段边界 = 说话人停顿过的地方，这里一定断句。
        # 不这么做，两个人换人的那一处会被连成一句，后面分人就全乱了。
        if char_seg and j > 0 and buf and char_seg[j] != char_seg[j - 1]:
            close(time_at(j), force=True)
            if j >= nt:
                break
        if t_start is None:
            t_start = time_at(j)
        buf.append(pool[j][0])
        j += 1
        # 兜底：标点模型偶尔漏出超长无标点串，别让它变成一句话
        if len(buf) >= soft_limit:
            close(time_at(j), force=True)
    close(audio_end, force=True)
    return out


def sentences_from_stream(chars: list[str], ctimes: list[float], audio_end: float,
                          soft_limit: int = 120, char_seg: list[int] | None = None
                          ) -> list[Sentence]:
    """SenseVoice 专用切句：标点已经在字流里，只需扫一遍。

    不能复用 align_sentences：那个函数是「文本走一条游标、字流走另一条」的
    双指针结构，前提是标点由标点模型后加（文本里有、字流里没有）。
    SenseVoice 的标点本来就在字流里，同一处标点会被消费两次，
    实测算出「，，」重复、词被从中间剁断、句数从 14 虚高到 21。
    这里单游标扫一遍，一个字一个字对齐，不会错位。

    另一处要小心的是中英标点：英文的 '.' ',' 不该变成「。」「，」，
    按前一个字符是不是 ASCII 判断；硬切时补的句号也跟着语种走。
    """
    out: list[Sentence] = []
    buf: list[str] = []
    t_start = None

    def is_ascii_ctx() -> bool:
        for c in reversed(buf):
            if c.isspace():
                continue
            return c.isascii() and (c.isalnum() or c in ".,?!'\"")

    def tail_mark() -> str:
        return '.' if is_ascii_ctx() else '。'

    def punct_of(ch: str) -> str:
        if ch in '.,?!;:':
            return ch if is_ascii_ctx() else _TO_FULL.get(ch, ch)
        return _TO_FULL.get(ch, ch)

    def close(t_end, force=False):
        nonlocal buf, t_start
        txt = ''.join(buf).strip()
        if txt:
            if force:
                while txt and txt[-1] in '，、；：,;:':
                    txt = txt[:-1]
                if not txt:
                    txt = ''
                elif txt[-1] not in SENT_END:
                    txt += tail_mark()
            if txt:
                a = t_start if t_start is not None else 0.0
                b = t_end if t_end is not None else a + 0.6
                if b <= a:
                    b = a + 0.4
                out.append(Sentence(round(a, 2), round(min(b, audio_end), 2), txt))
        buf = []
        t_start = None

    for i, ch in enumerate(chars):
        t = ctimes[i] if i < len(ctimes) else audio_end
        if ch in '\n\r':
            close(t, force=True)
            continue
        if ch in PUNCT_CHARS:
            mark = punct_of(ch)
            if ch in SENT_END:
                # 同一处连着来两个句末标点（"，，" "。。"）只留一个
                if buf and buf[-1] in PUNCT_CHARS:
                    buf[-1] = mark
                else:
                    buf.append(mark)
                close(t + 0.12, force=True)
            else:
                if buf and buf[-1] in PUNCT_CHARS:
                    continue
                if buf and not buf[-1].isspace():
                    buf.append(mark)
            continue
        if ch.isspace():
            if buf and not buf[-1].isspace():
                buf.append(' ')
            continue
        if char_seg and i > 0 and buf and char_seg[i] != char_seg[i - 1]:
            close(t, force=True)      # VAD 段边界 = 换人/停顿处，必须断句
        if t_start is None:
            t_start = t
        buf.append(ch)
        if len(buf) >= soft_limit:
            close(t, force=True)
    close(audio_end, force=True)
    return out


# ---------------------------------------------------------------- 主引擎

class Transcriber:
    def __init__(self, asr_dir: str = '', punct_dir: str = '', vad_path: str = '',
                 seg_path: str = '', emb_path: str = '', threads: int = 4):
        # 首选 SenseVoice：中英日韩粤五语合一，自带标点与逐字时间戳，
        # 228 MB 换掉了原来「识别 233.7 + 标点 76」两套，包还小一截，速度也更快。
        self.sv_model = find_model([
            os.path.join('_tools', 'dl', 'asr',
                         'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17',
                         'model.int8.onnx'),
            os.path.join('models', 'asr', 'model.int8.onnx')])
        self.sv_tokens = find_model([
            os.path.join('_tools', 'dl', 'asr',
                         'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17',
                         'tokens.txt'),
            os.path.join('models', 'asr', 'tokens.txt')])
        # 老路线留作兜底：SenseVoice 模型缺失时才用 paraformer + 标点模型
        self.asr_dir = asr_dir or find_model([
            os.path.join('_tools', 'dl', 'asr', 'sherpa-onnx-paraformer-zh-2023-09-14'),
            os.path.join('models', 'asr_zh')])
        self.punct_path = punct_dir or find_model([
            os.path.join('_tools', 'dl', 'punct',
                         'sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12-int8',
                         'model.int8.onnx'),
            os.path.join('models', 'punct', 'model.int8.onnx')])
        self.use_sv = bool(self.sv_model and self.sv_tokens)
        self.vad_path = vad_path or find_model([
            os.path.join('_tools', 'dl', 'vad', 'silero_vad.onnx'),
            os.path.join('models', 'vad', 'silero_vad.onnx')])
        # 说话人分离用 fp32 分割模型：int8 版会漏掉整段低能量语音（实测 5.6 秒全丢）
        self.seg_path = seg_path or find_model([
            os.path.join('_tools', 'dl', 'speaker',
                         'sherpa-onnx-pyannote-segmentation-3-0', 'model.onnx'),
            os.path.join('models', 'speaker', 'model.onnx'),
            os.path.join('models', 'speaker', 'seg.onnx')])
        self.emb_path = emb_path or find_model([
            os.path.join('_tools', 'dl', 'speaker', 'campplus.onnx'),
            os.path.join('models', 'speaker', 'campplus.onnx')])
        self.threads = threads
        self.lang = ''          # 最近一次转写判出的语种
        self._rec = None
        self._punct = None
        self._diar = None
        self._emb = None
        self.cancel_event = threading.Event()

    # -- 资源
    def has_speaker_model(self) -> bool:
        # 现在只用声纹模型，pyannote 分割模型不再需要（留着兼容旧目录）
        return bool(self.emb_path and os.path.isfile(self.emb_path))

    def engine_name(self) -> str:
        return 'SenseVoice' if self.use_sv else 'Paraformer'

    def models_ok(self) -> tuple[bool, str]:
        miss = []
        if self.use_sv:
            pass
        elif self.asr_dir and os.path.isdir(self.asr_dir):
            if not self.punct_path:
                miss.append('标点模型')
        else:
            miss.append('识别模型')
        if self.use_sv and not (self.sv_tokens and os.path.isfile(self.sv_tokens)):
            miss.append('词表')
        if not self.vad_path:
            miss.append('VAD 模型')
        return (not miss), '、'.join(miss)

    def _recognizer(self):
        if self._rec is None:
            import sherpa_onnx as so
            if self.use_sv:
                # language='auto'：让模型自己判断中英日韩粤；
                # use_itn=True：把「二零二四年」写成「2024年」，读起来省事。
                self._rec = so.OfflineRecognizer.from_sense_voice(
                    model=self.sv_model, tokens=self.sv_tokens,
                    num_threads=self.threads, sample_rate=SR,
                    decoding_method='greedy_search', debug=False, provider='cpu',
                    language='auto', use_itn=True)
            else:
                self._rec = so.OfflineRecognizer.from_paraformer(
                    paraformer=os.path.join(self.asr_dir, 'model.int8.onnx'),
                    tokens=os.path.join(self.asr_dir, 'tokens.txt'),
                    num_threads=self.threads, sample_rate=SR, feature_dim=80,
                    decoding_method='greedy_search', debug=False, provider='cpu')
        return self._rec

    def _punctuator(self):
        if self._punct is None:
            import sherpa_onnx as so
            cfg = so.OfflinePunctuationConfig(
                model=so.OfflinePunctuationModelConfig(
                    ct_transformer=self.punct_path, num_threads=self.threads,
                    debug=False, provider='cpu'))
            self._punct = so.OfflinePunctuation(cfg)
        return self._punct

    def _diarizer(self):
        if self._diar is None:
            import sherpa_onnx as so
            cfg = so.OfflineSpeakerDiarizationConfig(
                segmentation=so.OfflineSpeakerSegmentationModelConfig(
                    pyannote=so.OfflineSpeakerSegmentationPyannoteModelConfig(
                        model=self.seg_path),
                    num_threads=self.threads),
                embedding=so.SpeakerEmbeddingExtractorConfig(
                    model=self.emb_path, num_threads=self.threads,
                    debug=False, provider='cpu'),
                clustering=so.FastClusteringConfig(num_clusters=-1, threshold=0.55),
                min_duration_on=0.25, min_duration_off=0.35)
            self._diar = so.OfflineSpeakerDiarization(cfg)
        return self._diar

    def _embedder(self):
        """声纹提取器。只用它，不跑 pyannote 的滑窗分割。

        pyannote 是在整段音频上滑窗跑分割模型的，实测 0.08~0.11× 实时，
        1 小时播客要 6 分钟以上 —— 用户等到以为死机。
        而句子边界我们本来就有（VAD + 标点），逐句提声纹只要 32ms/句，
        1000 句 30 秒，快一个数量级，而且对播客这种「一人说一段」更贴。
        """
        if self._emb is None:
            import sherpa_onnx as so
            self._emb = so.SpeakerEmbeddingExtractor(
                so.SpeakerEmbeddingExtractorConfig(
                    model=self.emb_path, num_threads=self.threads,
                    debug=False, provider='cpu'))
        return self._emb

    # -- 只重跑分人
    def assign_only(self, path: str, rows: list[tuple], on_progress=None,
                    speaker: bool = True) -> dict:
        """拿已转好的句子重新分人，不碰识别。

        用户改一下「区分说话人」的勾选就要重等三分钟，那是没法用的。
        识别结果和音频都在手边，重跑分人只花解码 + 声纹的时间。
        rows 是 [(start, end, text), ...]。
        """
        self.cancel_event.clear()

        def tick(p, msg=''):
            if on_progress:
                on_progress(p, msg)

        tick(0.10, '读音频…')
        audio = decode_audio(path)
        dur = len(audio) / SR
        sents = [Sentence(round(a, 2), round(b, 2), t) for a, b, t in rows]
        n_spk = 0
        if speaker and self.has_speaker_model() and len(sents) > 1:
            total = len(sents)
            tick(0.2, '区分说话人 0/%d…' % total)

            def sp(p):
                if self.cancel_event.is_set():
                    raise _Canceled()
                tick(0.2 + 0.78 * p, '区分说话人 %d/%d…'
                     % (min(total, int(p * total) + 1), total))
            try:
                n_spk = assign_speakers(sents, audio, self._embedder(), sp)
            except _Canceled:
                for s in sents:
                    s.speaker = ''
                return {'sentences': [], 'duration': dur, 'chars': 0, 'canceled': True}
        tick(1.0, '完成')
        return {'sentences': sents, 'duration': dur, 'speakers': n_spk,
                'chars': sum(len(s.text) for s in sents)}

    # -- 转写
    def transcribe(self, path: str, on_progress=None, speaker: bool = False) -> dict:
        """返回 {'sentences': [...], 'duration': 秒, 'chars': n, 'speakers': n}"""
        self.cancel_event.clear()

        def tick(p, msg=''):
            if on_progress:
                on_progress(p, msg)

        tick(0.02, '解码音频…')
        audio = decode_audio(path)
        dur = len(audio) / SR
        if self.cancel_event.is_set():
            return {'sentences': [], 'duration': dur, 'chars': 0, 'canceled': True}

        tick(0.10, '找语音段…')
        spans = split_speech(audio, self.vad_path)
        if not spans:
            return {'sentences': [], 'duration': dur, 'chars': 0}

        tick(0.18, '识别 %d 段语音…' % len(spans))
        rec = self._recognizer()
        tokens: list[str] = []
        times: list[float] = []
        seg_ids: list[int] = []
        langs: list[str] = []
        for k, sp in enumerate(spans):
            if self.cancel_event.is_set():
                return {'sentences': [], 'duration': dur, 'chars': 0, 'canceled': True}
            a = int(sp.start * SR)
            b = int(sp.end * SR)
            st = rec.create_stream()
            st.accept_waveform(SR, audio[a:b])
            rec.decode_stream(st)
            res = st.result
            toks = list(getattr(res, 'tokens', []) or [])
            tss = list(getattr(res, 'timestamps', []) or [])
            if self.use_sv:
                lg = str(getattr(res, 'lang', '') or '').strip('<>|')
                if lg:
                    langs.append(lg)
            for t, s in zip(toks, tss):
                tokens.append(t)
                times.append(sp.start + float(s))
                seg_ids.append(k)
            tick(0.18 + 0.62 * (k + 1) / len(spans), '识别中 %d/%d' % (k + 1, len(spans)))

        if not tokens:
            return {'sentences': [], 'duration': dur, 'chars': 0}

        if self.use_sv:
            # SenseVoice 自带标点，不再跑标点模型；文本与 token 逐字对齐
            tick(0.82, '整理标点…')
            chars, ctimes, csegs = chars_from_tokens(tokens, times, seg_ids)
            fixed = ''.join(chars)
            self.lang = max(set(langs), key=langs.count) if langs else ''
        else:
            tick(0.82, '加标点…')
            chars, ctimes, csegs = text_from_tokens(tokens, times, seg_ids)
            raw = ''.join(chars)
            try:
                fixed = self._punctuator().add_punctuation(raw)
            except Exception:
                fixed = raw
            self.lang = ''

        tick(0.90, '整理段落…')
        if self.use_sv:
            sents = sentences_from_stream(chars, ctimes, dur, char_seg=csegs)
        else:
            sents = align_sentences(fixed, chars, ctimes, dur, char_seg=csegs)

        n_spk = 0
        if speaker and self.has_speaker_model() and len(sents) > 1:
            if self.cancel_event.is_set():
                return {'sentences': [], 'duration': dur, 'chars': 0, 'canceled': True}
            total = len(sents)
            tick(0.90, '区分说话人 0/%d…' % total)

            def sp(p):
                if self.cancel_event.is_set():
                    raise _Canceled()
                tick(0.90 + 0.09 * p, '区分说话人 %d/%d…'
                     % (min(total, int(p * total) + 1), total))
            try:
                n_spk = assign_speakers(sents, audio, self._embedder(), sp)
            except _Canceled:
                for s in sents:
                    s.speaker = ''
                return {'sentences': [], 'duration': dur, 'chars': 0, 'canceled': True}
            except Exception:
                for s in sents:          # 分人失败别拖累转写结果
                    s.speaker = ''
                n_spk = 0

        tick(1.0, '完成')
        return {'sentences': sents, 'duration': dur, 'speakers': n_spk,
                'chars': sum(len(s.text) for s in sents), 'fixed': fixed,
                'lang': self.lang}


# ---------------------------------------------------------------- 说话人

def _l2(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-8 else v


def voice_print(extractor, audio, a: float, b: float, sr: int = SR):
    """截一小段音频提声纹，返回归一化向量；提不出来返回 None。"""
    i = max(0, int(a * sr))
    j = min(len(audio), int(b * sr))
    if j - i < int(sr * 0.35):
        return None
    seg = audio[i:j]
    if len(seg) > sr * 4:               # 声纹 4 秒足够，长了只是白费时间
        mid = (len(seg) - sr * 4) // 2
        seg = seg[mid:mid + sr * 4]
    try:
        st = extractor.create_stream()
        st.accept_waveform(sr, seg)
        st.input_finished()
        if not extractor.is_ready(st):
            return None
        v = np.array(extractor.compute(st), dtype=np.float32)
    except Exception:
        return None
    return _l2(v)


def _cluster(vecs, thr: float = 0.62):
    """贪心余弦聚类，只用来给 k-means 找初始质心。

    阈值故意取得比"同一人"的门槛高一点：宁可先多分几个簇，
    后面 k-means 会按整体重新分配，错分的能纠正回来。
    """
    cents: list[np.ndarray] = []
    labels: list[int] = []
    for v in vecs:
        if not cents:
            cents.append(v.copy())
            labels.append(0)
            continue
        sims = [float(v @ c) for c in cents]
        k = int(max(range(len(sims)), key=lambda x: sims[x]))
        if sims[k] >= thr:
            labels.append(k)
        else:
            cents.append(v.copy())
            labels.append(len(cents) - 1)
    return labels


def _refine(vecs, labels, iters: int = 12):
    """k-means：每轮用簇内平均向量当质心，把所有点重新分配到最像的质心。

    只跑一次贪心聚类是不够的 —— 早出现的一个"不像"的句子会新建一个簇，
    后面同一个人全被吸进去，标签就乱了。反复重分配能把它拉回来。
    """
    V = np.stack(vecs)
    lab = np.array(labels)
    for _ in range(iters):
        uniq = sorted(set(lab.tolist()))
        if len(uniq) <= 1:
            break
        cents = np.stack([V[lab == u].mean(axis=0) for u in uniq])
        cents /= np.maximum(np.linalg.norm(cents, axis=1, keepdims=True), 1e-8)
        new = np.array(uniq)[np.argmax(V @ cents.T, axis=1)]
        if np.array_equal(new, lab):
            break
        lab = new
    return lab.tolist()


def _merge_similar(vecs, labels, thr: float = 0.62):
    """两个簇的质心太像就并掉 —— 同一个人被拆成两簇是最常见的错。

    阈值 0.62 是实测出来的：同一个人不同句子之间，质心相似度会掉到 0.68；
    不同人之间只有 0.12~0.25。0.78 会把前者漏掉（一句语气不同的短话
    就自成一个「说话人」），0.62 两边都不碰。
    """
    V = np.stack(vecs)
    while True:
        uniq = sorted(set(labels))
        if len(uniq) <= 1:
            break
        cents = {}
        for u in uniq:
            c = V[[i for i, l in enumerate(labels) if l == u]].mean(axis=0)
            cents[u] = c / max(float(np.linalg.norm(c)), 1e-8)
        best, pair = 0.0, None
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                s = float(cents[uniq[i]] @ cents[uniq[j]])
                if s > best:
                    best, pair = s, (uniq[i], uniq[j])
        if pair is None or best < thr:
            break
        a, b = pair
        cnt_a = labels.count(a)
        cnt_b = labels.count(b)
        keep, drop = (a, b) if cnt_a >= cnt_b else (b, a)
        labels = [keep if l == drop else l for l in labels]
    return labels


def _smooth(labels: list[int], conf: list[float] | None = None,
            thr: float = 0.55, max_run: int = 2) -> list[int]:
    """把夹在两个同一个人中间的短促异类抹平。

    只动**置信度低**的句子。真实播客里一个人插一句话太常见了，
    那句插话的声纹往往很明确（0.7 以上），抹掉它才是错。
    """
    n = len(labels)
    lab = list(labels)
    i = 1
    while i < n - 1:
        if conf is not None and conf[i] >= thr:
            i += 1
            continue
        if lab[i] == lab[i - 1] or lab[i] == lab[i + 1]:
            i += 1
            continue
        j = i
        while j + 1 < n and lab[j + 1] == lab[i]:
            j += 1
        if j - i + 1 <= max_run and lab[i - 1] == lab[i + 1]:
            for k in range(i, j + 1):
                lab[k] = lab[i - 1]
        i = j + 1
    return lab


def _merge_small(labels, weights, cents, min_share: float = 0.04):
    """占比太小的簇并进最像的那个 —— 咳嗽、笑声被单独分出一个「人」很常见。"""
    total = sum(weights) or 1.0
    share: dict[int, float] = {}
    for l, w in zip(labels, weights):
        share[l] = share.get(l, 0.0) + w
    keep = [l for l in share if share[l] / total >= min_share]
    if not keep:
        keep = [max(share, key=lambda x: share[x])]
    if len(keep) == len(share):
        return labels
    remap = {}
    for l in share:
        if l in keep:
            continue
        remap[l] = max(keep, key=lambda k: float(cents[l] @ cents[k]))
    return [remap.get(l, l) for l in labels]


def assign_speakers(sents: list[Sentence], audio, extractor,
                    on_progress=None) -> int:
    """把每个句子归到某个说话人身上，返回说话人总数。

    做法：逐句提声纹 → 在线聚类 → 抹掉一两句的抖动 → 把小簇并进大簇。
    一个人说话时返回 1，调用方据此把标注全清掉（不标注比标错好）。
    """
    n = len(sents)
    if n == 0:
        return 0
    vecs: list[np.ndarray] = []
    idx: list[int] = []
    for i, s in enumerate(sents):
        v = voice_print(extractor, audio, s.start - 0.12, s.end + 0.15)
        if v is not None:
            vecs.append(v)
            idx.append(i)
        if on_progress and (i % max(1, n // 50) == 0):
            on_progress(min(0.999, i / n))
    if len(vecs) < 2:
        return 0

    labels = _cluster(vecs)
    labels = _refine(vecs, labels)
    labels = _merge_similar(vecs, labels)

    V = np.stack(vecs)
    cents: dict[int, np.ndarray] = {}
    for l in set(labels):
        c = V[[i for i, x in enumerate(labels) if x == l]].mean(axis=0)
        cents[l] = c / max(float(np.linalg.norm(c)), 1e-8)

    # 每句跟自己簇质心有多像；只有不像的才允许被平滑掉
    conf = [float(v @ cents[l]) for v, l in zip(vecs, labels)]
    labels = _smooth(labels, conf)

    weights = [max(0.3, sents[i].end - sents[i].start) for i in idx]
    labels = _merge_small(labels, weights, cents)
    if on_progress:
        on_progress(0.999)

    for i, l in zip(idx, labels):
        sents[i].speaker = 'k%d' % l

    # 落在空隙里、或太短提不出声纹的句子，跟前一句走
    prev = ''
    for s in sents:
        if s.speaker:
            prev = s.speaker
        else:
            s.speaker = prev

    # 重排成 1..N，按首次出现的顺序
    order: dict[str, int] = {}
    for s in sents:
        if s.speaker and s.speaker not in order:
            order[s.speaker] = len(order) + 1
    for s in sents:
        if s.speaker:
            s.speaker = str(order[s.speaker])

    # 只分出一个人：全清掉。单人录音被标成「说话人1」纯属添乱
    if len(order) <= 1:
        for s in sents:
            s.speaker = ''
    return len(order)


# ---------------------------------------------------------------- 导出

def _ts(sec: float, srt: bool = True) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    if srt:
        return '%02d:%02d:%02d,%03d' % (h, m, int(s), int((s - int(s)) * 1000))
    return '%02d:%02d:%02d' % (h, m, int(s))


def _spk_label(spk: str) -> str:
    """编号原样显示成「说话人 1」；用户改过名（如「主持人」）就照原名输出。"""
    return '说话人 %s' % spk if str(spk).isdigit() else str(spk)


def _cw(ch: str) -> float:
    """一个字符占多宽：中日韩全角算 1，ASCII 算 0.55。"""
    return 0.55 if ord(ch) < 128 else 1.0


def wrap_subtitle(text: str, limit: float = 16.0) -> str:
    """字幕太长就折成两行。

    剪映、PR 里一行超过 16 个中文字就会顶到画幅边缘，折一下最省事。
    断点优先挑中间的标点，挑不到才按宽度硬切。
    """
    text = (text or '').strip()
    if not text or sum(_cw(c) for c in text) <= limit:
        return text
    total = sum(_cw(c) for c in text)
    mid = total / 2.0

    acc, best, best_d = 0.0, -1, 1e9
    for i, ch in enumerate(text):
        acc += _cw(ch)
        if ch in '，。！？；：、,.!?;:）)》」” ' and i + 1 < len(text):
            d = abs(acc - mid)
            if d < best_d:
                best_d, best = d, i + 1
    if best <= 0:
        acc = 0.0
        for i, ch in enumerate(text):
            acc += _cw(ch)
            if acc >= mid:
                best = i + 1
                break
    if best <= 0 or best >= len(text):
        return text
    return text[:best].rstrip() + '\n' + text[best:].lstrip()


def _paragraphs(sentences: list[Sentence], soft: int = 150):
    """切段落，返回 [(speaker, text), ...]。

    两条规矩：换人一定断；同一个人的话攒到 soft 字左右再断。
    以前是「见句号就断」，结果一句话一个空行，读起来比原文还碎。
    """
    out = []
    cur = None
    buf: list[str] = []
    n = 0

    def flush():
        nonlocal buf, n
        t = ''.join(buf).strip()
        if t:
            out.append((cur, t))
        buf = []
        n = 0

    for s in sentences:
        spk = (getattr(s, 'speaker', '') or '').strip()
        if buf and spk != cur:
            flush()
        cur = spk
        buf.append(s.text)
        n += len(s.text)
        if n >= soft and s.text and s.text[-1] in SENT_END:
            flush()
    flush()
    return out


DISCLAIMER = '本文由言札自动转写，可能存在错漏；涉及法律、医疗、财务等重要事项，请以人工核对为准。'


def to_txt(sentences: list[Sentence], meta: str = '') -> str:
    lines = []
    if meta:
        lines.append(meta)
        lines.append('')
    for spk, text in _paragraphs(sentences):
        lines.append(('【%s】%s' % (_spk_label(spk), text)) if spk else text)
        lines.append('')
    while lines and not lines[-1]:
        lines.pop()
    lines.append('')
    lines.append('—' * 18)
    lines.append(DISCLAIMER)
    return '\n'.join(lines) + '\n'


def to_md(sentences: list[Sentence], meta: str = '') -> str:
    lines = ['# %s' % meta] if meta else []
    if lines:
        lines.append('')
    for spk, text in _paragraphs(sentences):
        lines.append(('**%s**：%s' % (_spk_label(spk), text)) if spk else text)
        lines.append('')
    while lines and not lines[-1]:
        lines.pop()
    lines.append('')
    lines.append('---')
    lines.append('*%s*' % DISCLAIMER)
    return '\n'.join(lines) + '\n'


def to_srt(sentences: list[Sentence], wrap: float = 16.0) -> str:
    out = []
    for i, s in enumerate(sentences, 1):
        spk = (getattr(s, 'speaker', '') or '').strip()
        out.append(str(i))
        out.append('%s --> %s' % (_ts(s.start), _ts(s.end)))
        body = wrap_subtitle(s.text, wrap) if wrap else s.text
        out.append(('%s：%s' % (_spk_label(spk), body)) if spk else body)
        out.append('')
    return '\n'.join(out)


def _ts_vtt(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return '%02d:%02d:%06.3f' % (h, m, s)


def to_vtt(sentences: list[Sentence], wrap: float = 16.0) -> str:
    out = ['WEBVTT', '']
    for s in sentences:
        spk = (getattr(s, 'speaker', '') or '').strip()
        body = wrap_subtitle(s.text, wrap) if wrap else s.text
        out.append('%s --> %s' % (_ts_vtt(s.start), _ts_vtt(s.end)))
        out.append(('<v %s>%s' % (_spk_label(spk), body)) if spk else body)
        out.append('')
    return '\n'.join(out)


def to_json(sentences: list[Sentence], meta: str = '') -> str:
    import json as _json
    data = {
        'app': '言札 YanZha',
        'source': meta,
        'sentences': [
            {'start': round(s.start, 3), 'end': round(s.end, 3),
             'text': s.text,
             **({'speaker': s.speaker} if getattr(s, 'speaker', '') else {})}
            for s in sentences],
    }
    return _json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def to_docx(sentences: list[Sentence], path: str, meta: str = '',
            timed: bool = False) -> None:
    """写一份 Word。默认是干净稿（带说话人分段），timed=True 时每行加时间码。"""
    from docx import Document
    from docx.shared import Pt, RGBColor

    doc = Document()
    st = doc.styles['Normal']
    st.font.name = '微软雅黑'
    st.font.size = Pt(10.5)

    if meta:
        h = doc.add_heading(meta, level=1)
        for r in h.runs:
            r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    for spk, text in _paragraphs(sentences):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.4
        if spk:
            r = p.add_run(_spk_label(spk) + '：')
            r.bold = True
            r.font.color.rgb = RGBColor(0x8A, 0x6D, 0x2F)
        p.add_run(text)

    if timed:
        doc.add_page_break()
        doc.add_heading('带时间码', level=2)
        for s in sentences:
            spk = (getattr(s, 'speaker', '') or '').strip()
            prefix = '[%s] ' % _ts(s.start, srt=False)
            if spk:
                prefix += _spk_label(spk) + '：'
            doc.add_paragraph(prefix + s.text)

    # 尾注：机器转写必然有错，落在文件里比只写在「关于」里更有用
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run(DISCLAIMER)
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    doc.save(path)


def to_tsv(sentences: list[Sentence]) -> str:
    """带时间戳的纯文本，方便贴进笔记/表格。"""
    out = []
    for s in sentences:
        spk = (getattr(s, 'speaker', '') or '').strip()
        head = '[%s]' % _ts(s.start, srt=False)
        out.append('%s\t%s\t%s' % (head, _spk_label(spk), s.text)
                   if spk else '%s\t%s' % (head, s.text))
    return '\n'.join(out) + '\n'
