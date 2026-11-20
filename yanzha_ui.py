# -*- coding: utf-8 -*-
"""言札 · 桌面端（pywebview 壳 + 单文件 HTML 界面）。

窗口里的活都交给 yanzha_core；这里只负责：选文件、排队、报进度、导出。
全程不联网，不上传，不写注册表。
"""
from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import traceback

import webview

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ---------------- 日志（出了问题才有迹可循） ----------------
DATA_DIR = os.path.join(
    os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'YanZha')
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    DATA_DIR = HERE
LOG_PATH = os.path.join(DATA_DIR, 'yanzha.log')


def _init_log():
    try:
        # 超过 4096 字节就滚动一次，只留最近两轮
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 4 * 1024 * 1024:
            try:
                os.replace(LOG_PATH, LOG_PATH + '.1')
            except Exception:
                pass
        logging.basicConfig(
            filename=LOG_PATH, level=logging.INFO,
            format='%(asctime)s %(levelname)-5s [%(threadName)s] %(message)s',
            datefmt='%m-%d %H:%M:%S', encoding='utf-8', force=True)
    except Exception:
        logging.basicConfig(level=logging.INFO)


APP_TITLE = '言札'
VERSION = '0.6.1'


_init_log()
log = logging.getLogger('yanzha')
log.info('=== 启动 v%s | frozen=%s | python=%s',
         VERSION, getattr(sys, 'frozen', False), sys.version.split()[0])
log.info('程序目录 %s', HERE)
log.info('日志 %s', LOG_PATH)

# ---------------- 导出前检查（纯函数，能单独测） ----------------
# 言札的定位是「原声转字」：转出来的每一个字都要是那个人真的说过的。
# 所以这里只报「根本没人说过的东西」，一律不评价说话风格——
#   句子长短、口吃、拖音、一个词重复三遍、绕回来把话再说一遍，全都是原声，不报。
# 试过按长度/重复报警，一份千句的两人对话刷出 94 条，全是正常句子，用户直接把弹窗关掉。
#
# 只留三类，共同点是「客观可证、不涉及判断」：
#   empty   整句只剩标点——人不会「说」一个句号
#   ghost   （音乐）（掌声）这类标注——是识别器自己写的，不是谁说的
#   overlap 同一段被解码两遍——唯一硬证据是时间戳重叠，因为人不可能同时说两段话
NOISE_RE = re.compile(
    r'[\[【（(〔]\s*(?:背景)?(?:音乐|掌声|笑声|噪声|噪音|静音|无声|字幕|广告|口哨|哭声|咳嗽)'
    r'\s*[\]】）)〕]')
OVERLAP_MIN = 0.5        # 时间段重叠超过一半，才认定是同一段音频被识别了两次


def weight_len(text):
    """等效字数：中文 1，ASCII 0.55。给需要估行宽的地方用（字幕折行同一口径）。"""
    return sum(1.0 if ord(ch) > 127 else 0.55 for ch in text)


def _overlap_ratio(a, b):
    """两句时间段的交集占较短那句的比例；任一时间戳无效就返回 0。"""
    try:
        s1, e1, s2, e2 = float(a.start), float(a.end), float(b.start), float(b.end)
    except (TypeError, ValueError):
        return 0.0
    if e1 <= s1 or e2 <= s2:
        return 0.0
    inter = min(e1, e2) - max(s1, s2)
    if inter <= 0:
        return 0.0
    return inter / min(e1 - s1, e2 - s2)


def audit_sentences(sents, window=8):
    """找出「不是人说的话」：[(kind, si, text, hint)]，按 si 升序。

    kind：empty 只剩标点 / ghost 识别器标注 / overlap 同一段被识别两遍
    """
    out, recent = [], []             # recent = [(si, text, sent)]，最近 window 句
    for i, s in enumerate(sents):
        t = (s.text or '').strip()
        if not t:
            continue
        if not any(ch.isalnum() for ch in t):
            # 只剩标点不是句子，但也不必往回看
            out.append(('empty', i, t, ''))
            recent.append((i, t, s))
            if len(recent) > window:
                recent.pop(0)
            continue

        m = NOISE_RE.search(t)
        if m:
            out.append(('ghost', i, t, m.group(0)))

        # 文本相同才可能是一条音频被识别两遍；且必须时间重叠——
        # 各占各的时间说明人真的说了两遍，那是原声，不报。
        for j, pt, ps in reversed(recent):
            if t != pt:
                continue
            r = _overlap_ratio(ps, s)
            if r >= OVERLAP_MIN:
                out.append(('overlap', i, t, '与第 %d 句时间重叠 %d%%'
                            % (j + 1, int(r * 100))))
                break

        recent.append((i, t, s))
        if len(recent) > window:
            recent.pop(0)
    return out


def text_replace(text, q, r, ci=True):
    """把 text 里的 q 换成 r，返回 (新文本, 替换次数)。q 为空则原样返回。"""
    if not q:
        return text, 0
    if not ci:
        return text.replace(q, r), text.count(q)
    pat = re.compile(re.escape(q), re.I)
    return pat.subn(lambda m: r, text)


# ---------------- 术语表 ----------------
# 解决的问题：同一个人名/书名/公司名，在同一个主播的每一期里都错成同一个样子。
# 每转完一期就去搜索框一个一个改，改的其实是同一批词。存成表就不用再改。
#
# 一行一条，用箭头分隔：`错→对`（`->`、`=>`、Tab、= 都认）。
# 右边留空 = 把这个词删掉。`#` 开头的行是注释。
# 只做「用户自己声明的错」，不做任何自动推断——言札不猜哪个字该改。
TERM_SEPS = ('→', '->', '=>', '\t')


def parse_terms(text: str) -> list:
    """把术语表文本解析成 [(错, 对), ...]。看不懂的行直接跳过，不报错。"""
    out = []
    for raw in (text or '').splitlines():
        s = raw.strip()
        if not s or s.startswith('#'):
            continue
        a = b = None
        for sep in TERM_SEPS:
            if sep in s:
                a, b = s.split(sep, 1)
                break
        if a is None:
            # 没有箭头时认 =，但不认英文里常见的「=」写法（x==y 之类不在这里）
            if '=' in s:
                a, b = s.split('=', 1)
            else:
                continue
        a, b = a.strip(), (b or '').strip()
        if not a or a == b:
            continue
        out.append((a, b))
    return out


def terms_text() -> str:
    v = load_settings().get('terms')
    return v if isinstance(v, str) else ''


def terms_from_pairs(pairs, comments=None) -> str:
    """把界面上两栏填的 [[错, 对], ...] 拼成存盘用的文本。

    界面是两栏（左「错的」右「改成」），用户不用敲箭头；存盘统一用 `错→对`，
    这样老的术语表、手改的文本、以后的导入导出还是同一套格式。
    右栏留空 = 删掉这个词，拼成 `错→`。
    左栏里若还带着箭头（手打或粘进来），这里再拆一次，别把它当成一个词。
    """
    out = []
    for p in (pairs or []):
        try:
            a, b = p[0], p[1]
        except Exception:
            continue
        a = str(a or '').strip()
        b = str(b or '').strip()
        if not a:
            continue
        for sep in TERM_SEPS:
            if sep in a:
                a, tail = a.split(sep, 1)
                a, tail = a.strip(), tail.strip()
                if not b:
                    b = tail
                break
        if not a or a == b:
            continue
        out.append('%s→%s' % (a, b))
    for c in (comments or []):
        c = str(c or '').strip()
        if c.startswith('#'):
            out.append(c)
    return ('\n'.join(out) + '\n') if out else ''


# ---------------- 小设置（记住上次导出到哪） ----------------
SETTINGS_PATH = os.path.join(DATA_DIR, 'settings.json')


def load_settings():
    try:
        with open(SETTINGS_PATH, encoding='utf-8') as f:
            v = json.load(f)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def save_setting(k, v):
    d = load_settings()
    if d.get(k) == v:
        return
    d[k] = v
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except Exception:
        log.exception('写设置失败')


# ---------------- 草稿（关窗口不丢稿） ----------------
# 用户在稿子上改一小时，关掉程序就全没了 —— 只有主动「导出」才会落盘。
# 这里把改过的稿子随时存一份到本机 AppData（不进源文件夹、不上传），
# 下次开程序左栏出现「有 N 份没导出的稿子」，点一下接着改。
DRAFT_DIR = os.path.join(DATA_DIR, 'drafts')
DRAFT_KEEP_DAYS = 60          # 已导出的草稿留 60 天，之后自动清


def draft_key(path: str) -> str:
    try:
        raw = os.path.abspath(path).lower().encode('utf-8')
    except Exception:
        return ''
    return hashlib.sha1(raw).hexdigest()[:16]


def draft_file(key: str) -> str:
    return os.path.join(DRAFT_DIR, key + '.json')


def _excepthook(t, e, tb):
    log.error('未捕获异常\n%s', ''.join(traceback.format_exception(t, e, tb)))


sys.excepthook = _excepthook


def _threadhook(a):
    log.error('线程 %s 异常\n%s', a.thread.name if a.thread else '?',
              ''.join(traceback.format_exception(a.exc_type, a.exc_value, a.exc_traceback)))


threading.excepthook = _threadhook

import yanzha_core as C          # noqa: E402
import native_dialog as ND       # noqa: E402

EXPORT_KINDS = [('txt', '纯文本 .txt'), ('srt', '字幕 .srt'), ('vtt', '字幕 .vtt'),
                ('md', 'Markdown .md'), ('docx', 'Word .docx'),
                ('tsv', '带时间戳 .txt'), ('json', '结构化 .json')]


def human_size(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return '%.1f %s' % (n, unit) if unit != 'B' else '%d B' % n
        n /= 1024.0


def _logged(fn):
    """把界面对后端的每次调用记进日志：卡住时最后一行就是卡点。"""
    @functools.wraps(fn)
    def w(self, *a, **k):
        parts = [repr(x)[:60] for x in a]
        parts += ['%s=%s' % (kk, repr(vv)[:40]) for kk, vv in k.items()]
        log.info('→ %s(%s)', fn.__name__, ', '.join(parts))
        t0 = time.time()
        try:
            r = fn(self, *a, **k)
        except Exception:
            log.exception('✗ %s 异常', fn.__name__)
            raise
        log.info('← %s %.0f ms', fn.__name__, (time.time() - t0) * 1000)
        return r
    return w


class Api:
    def __init__(self):
        self._window = None
        self._engine = C.Transcriber()
        self._items = []          # [{path,name,size,duration,status,progress,msg,sentences,error}]
        self._lock = threading.Lock()
        self._worker = None
        self._running = False
        self._speaker_on = self._engine.has_speaker_model()
        st = load_settings()
        # 语种与人数存过就照上次来；语种默认锁中文（中文录音里会冒日文/韩文）
        self._engine.lang_pref = 'auto' if st.get('lang') == 'auto' else 'zh'
        try:
            n = int(st.get('nspk') or 0)
        except Exception:
            n = 0
        self._engine.n_speakers = n if 1 <= n <= 8 else 0
        self._clips = {}          # (path,start,dur) → data URI，重复听同一句不再调 ffmpeg
        self._undo = []           # 改字/删句的撤销栈
        self._batch_no = 0        # 「全部替换」的批次号，一次 Ctrl+Z 整批退回
        self._no_touch = False    # 批量套术语时先别一句一存盘
        log.info('说话人模型：%s', '有' if self._speaker_on else '无')

    # ---------------- 窗口
    def bind(self, window):
        self._window = window

    def _push(self, fn, *args):
        """把状态推给界面（安全失败，界面关了也不崩）。"""
        try:
            self._window.evaluate_js('%s(%s)' % (fn, ','.join(json.dumps(a, ensure_ascii=False) for a in args)))
        except Exception:
            pass

    def _state(self):
        return [{'idx': i, 'name': it['name'], 'status': it['status'],
                 'progress': it['progress'], 'msg': it['msg'],
                 'duration': it['duration'], 'chars': sum(len(s.text) for s in it['sentences']),
                 'speakers': len({s.speaker for s in it['sentences'] if s.speaker}),
                 'hints': it.get('hints') or [],
                 'error': it['error']}
                for i, it in enumerate(self._items)]

    def _sig(self):
        """这次的转写参数。转完存一份，参数没变就不用重跑。"""
        return (self._speaker_on, self._engine.lang_pref,
                self._engine.n_speakers)

    def _sync(self):
        self._push('renderList', self._state())

    # ---------------- 基本信息
    def first_run(self):
        """第一次启动返回 True，之后一直 False。用来弹一次免责声明。"""
        p = os.path.join(DATA_DIR, '.welcomed')
        if os.path.exists(p):
            log.info('first_run: 不是首次')
            return {'first': False}
        try:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(VERSION)
            log.info('first_run: 首次，已写标记 %s', p)
        except Exception:
            log.exception('first_run 写标记失败')
        return {'first': True}

    @_logged
    def app_info(self):
        ok, miss = self._engine.models_ok()
        return {'title': APP_TITLE, 'version': VERSION, 'models_ok': ok,
                'models_missing': miss, 'offline': True,
                'has_speaker': self._engine.has_speaker_model(),
                'speaker_on': self._speaker_on,
                'first': self.first_run()['first'],
                'engine': self._engine.engine_name(),
                'theme': 'light' if load_settings().get('theme') == 'light' else 'dark',
                'lang': 'auto' if self._engine.lang_pref == 'auto' else 'zh',
                'nspk': int(self._engine.n_speakers or 0),
                'langs': ['中文', 'English', '日本語', '한국어', '粤语']
                          if self._engine.use_sv else ['中文']}

    # ---------------- 文件
    @_logged
    def pick_files(self):
        pairs = [
            ('音视频文件', '*.mp3;*.m4a;*.wav;*.flac;*.aac;*.ogg;*.opus;*.wma;'
                          '*.mp4;*.mkv;*.mov;*.avi;*.flv;*.webm;*.ts;*.m4v'),
            ('音频文件', '*.mp3;*.m4a;*.wav;*.flac;*.aac;*.ogg;*.opus;*.wma'),
            ('视频文件', '*.mp4;*.mkv;*.mov;*.avi;*.flv;*.webm;*.ts;*.m4v'),
            ('所有文件', '*.*'),
        ]
        t0 = time.time()
        log.info('打开文件对话框…')
        try:
            paths = ND.open_files('添加音视频文件', pairs)
        except Exception:
            log.exception('原生对话框失败，退回系统接口')
            paths = self._window.create_file_dialog(
                webview.OPEN_DIALOG, allow_multiple=True)
        log.info('对话框返回 %d 个，耗时 %.1f 秒', len(paths or []), time.time() - t0)
        if not paths:
            return []
        return self.add_paths(list(paths))

    def add_paths(self, paths):
        added = []
        for p in paths:
            p = os.path.abspath(p)
            if not os.path.isfile(p):
                continue
            if any(it['path'] == p for it in self._items):
                continue
            self._items.append({
                'path': p, 'name': os.path.basename(p),
                'size': os.path.getsize(p), 'duration': 0.0,
                'status': 'wait', 'progress': 0.0, 'msg': '',
                'sentences': [], 'error': '',
                'raw': [],            # 不带说话人的句子，改勾选时复用
                'sig': None,          # 上次转写用的参数组合（分人/语种/人数）
                'lang': '',           # 上次锁的语种：语种变了只能重新识别
            })
            added.append(p)
        self._sync()
        return added

    def remove(self, idx):
        if 0 <= idx < len(self._items) and not self._running:
            self._items.pop(idx)
            self._sync()

    def clear(self):
        if not self._running:
            self._items = []
            self._sync()

    # ---------------- 转写
    def set_speaker(self, on):
        self._speaker_on = bool(on) and self._engine.has_speaker_model()
        log.info('区分说话人：%s', self._speaker_on)
        return {'on': self._speaker_on}

    # ---------------- 外观与识别参数（存设置，下次开机照旧）
    def set_theme(self, v):
        """亮色 / 暗色。只改界面，不碰识别。"""
        v = 'light' if str(v) == 'light' else 'dark'
        save_setting('theme', v)
        log.info('主题：%s', v)
        try:
            _title_bar(APP_TITLE, v)
        except Exception:
            pass
        return {'theme': v}

    def set_lang(self, v):
        """语种：'zh' 锁中文（默认） / 'auto' 交给模型自己判。

        中文录音里冒出日语韩语，是模型在底噪/笑声这类片段上乱猜语种；
        锁中文后只对可疑段用强制中文重认，正常段不动。
        """
        v = 'auto' if str(v) == 'auto' else 'zh'
        save_setting('lang', v)
        self._engine.lang_pref = v
        log.info('语种：%s', v)
        return {'lang': v}

    def set_nspk(self, v):
        """说话人数：0=自动，1=单人（不分人），2~8=按人数硬分。

        很多人清清楚楚知道自己录的是几个人，这条比任何自动判据都准 ——
        自动分人最容易出的错就是「明明四五个人，只分出两个」。
        """
        try:
            n = int(v)
        except Exception:
            n = 0
        n = n if 1 <= n <= 8 else 0
        save_setting('nspk', n)
        self._engine.n_speakers = n
        log.info('说话人数：%s', n or '自动')
        return {'nspk': n}

    def start(self):
        if self._running:
            return {'ok': False, 'msg': '正在转写'}
        todo = []
        for i, it in enumerate(self._items):
            if it['status'] == 'run':
                continue
            # 已经转好的、参数又没变，就别重跑（改了说话人勾选才需要重来）
            if it['status'] == 'done' and it.get('sig') == self._sig():
                continue
            todo.append(i)
        if not todo:
            return {'ok': False, 'msg': '没有需要转写的文件'}
        for i in todo:
            it = self._items[i]
            it['status'] = 'wait'
            it['progress'] = 0.0
            it['error'] = ''
            it['sentences'] = []
        self._running = True
        self._worker = threading.Thread(target=self._run, args=(todo,), daemon=True)
        self._worker.start()
        return {'ok': True}

    def _run(self, todo):
        t_all = time.time()
        for n, i in enumerate(todo, 1):
            if not self._running:
                break
            it = self._items[i]
            it['status'] = 'run'
            self._sync()

            def prog(p, msg, idx=i):
                it2 = self._items[idx]
                it2['progress'] = p
                it2['msg'] = msg
                self._push('onItemProgress', idx, p, msg)

            try:
                reuse = bool(it.get('raw')) and it.get('lang') == self._engine.lang_pref
                if reuse:
                    # 只有「区分说话人」变了：复用识别结果，只重跑分人
                    log.info('复用识别结果，只重跑分人：%s', it['name'])
                    res = self._engine.assign_only(
                        it['path'], it['raw'], prog, speaker=self._speaker_on)
                else:
                    res = self._engine.transcribe(it['path'], prog, speaker=self._speaker_on)
                it['sentences'] = res['sentences']
                it['duration'] = res['duration']
                if not res.get('canceled') and res['sentences']:
                    it['raw'] = [(s.start, s.end, s.text) for s in res['sentences']]
                    it['sig'] = self._sig()
                    it['lang'] = self._engine.lang_pref
                if res.get('canceled'):
                    it['status'] = 'wait'
                    it['msg'] = '已停止'
                elif not res['sentences']:
                    it['status'] = 'error'
                    it['error'] = '没听出内容（静音或全是噪声？）'
                else:
                    it['status'] = 'done'
                    it['progress'] = 1.0
                    nspk = res.get('speakers', 0)
                    if nspk > 1:
                        extra = ' · %d 人' % nspk
                    elif nspk == 1 and self._speaker_on:
                        extra = ' · 单人'
                    else:
                        extra = ''
                    lg = (res.get('lang') or '').strip()
                    if lg and lg != 'zh':
                        extra += ' · ' + {'en': 'English', 'ja': '日本語',
                                          'ko': '한국어', 'yue': '粤语'}.get(lg, lg)
                    if res.get('dropped'):
                        extra += ' · 清掉 %d 处外语误字' % res['dropped']
                    # 术语表：用户自己声明过的错词，转完直接改掉，不用再搜一遍
                    if load_settings().get('terms_auto', True) and terms_text():
                        tr = self._apply_terms(i)
                        if tr.get('occ'):
                            extra += ' · 术语 %d 处' % tr['occ']
                    it['msg'] = '%d 句 · %d 字%s' % (
                        len(it['sentences']),
                        sum(len(x.text) for x in it['sentences']), extra)
                    # 自动分人最容易出的错是「分多了」：两人对话切成七八个人。
                    # 只在参数栏挂一个「人数」下拉没人会去看，所以在这儿点一句，
                    # 并且给一个直接改人数重跑的按钮（见 yanzha.html 的 tipped）。
                    hints = []
                    if nspk >= 4 and not self._engine.n_speakers:
                        hints.append({'kind': 'spk', 'n': nspk})
                    elif not terms_text() and not load_settings().get('terms_tip_off'):
                        hints.append({'kind': 'terms'})
                    it['hints'] = hints
                    log.info('转写完成 %s：%d 句 %d 字 %d 人 语种=%s',
                             it['name'], len(res['sentences']), res['chars'],
                             nspk, res.get('lang') or '-')
            except C.DecodeError as e:
                it['status'] = 'error'
                it['error'] = str(e)
            except Exception as e:
                it['status'] = 'error'
                it['error'] = '出错：%s' % e
            if it['status'] == 'done':
                self._draft_save(i)       # 转完先存一份，关窗口也不丢
            self._sync()
            if it['status'] == 'done':
                self._push('showResult', i)
        self._running = False
        self._sync()
        self._push('onAllDone', round(time.time() - t_all, 1))

    def stop(self):
        self._running = False
        self._engine.cancel_event.set()
        return {'ok': True}

    # ---------------- 结果
    def result(self, idx):
        if not (0 <= idx < len(self._items)):
            return {'sentences': []}
        it = self._items[idx]
        return {'name': it['name'], 'duration': it['duration'],
                'speakers': len({s.speaker for s in it['sentences'] if s.speaker}),
                'sentences': [{'start': s.start, 'end': s.end, 'text': s.text,
                               'speaker': s.speaker}
                              for s in it['sentences']]}

    @_logged
    def rename_speaker(self, idx, old, new):
        """把「说话人 1」改名成「主持人」之类，导出时一并生效。"""
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        old = str(old).strip()
        new = str(new).strip()[:24]
        if not new or new == old:
            return {'ok': False, 'msg': '名字没变'}
        n = 0
        for s in self._items[idx]['sentences']:
            if str(s.speaker).strip() == old:
                s.speaker = new
                n += 1
        log.info('改说话人名 %s → %s，%d 句', old, new, n)
        if n:
            self._touch(idx)
        return {'ok': True, 'n': n}

    # ---------------- 校对：听原音 · 改错字
    @_logged
    def clip(self, idx, si, ahead=1):
        """切出「这一句 + 后面 ahead 句」给界面播放，校对时边听边改。"""
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        it = self._items[idx]
        sents = it['sentences']
        if not (0 <= si < len(sents)):
            return {'ok': False, 'msg': '没有这一句'}
        s = sents[si]
        end = s.end
        for k in range(1, max(0, int(ahead)) + 1):
            if si + k < len(sents):
                end = sents[si + k].end
        start = max(0.0, s.start - 0.25)      # 往前留一点，听得到衔接
        dur = max(1.2, min(end - start + 0.5, 40.0))
        key = (it['path'], round(start, 2), round(dur, 2))
        hit = self._clips.get(key)
        if hit:
            return {'ok': True, 'url': hit, 'start': s.start, 'dur': dur, 'cached': True}
        t0 = time.time()
        try:
            url = C.make_clip_b64(it['path'], start, dur)
        except Exception as e:
            log.exception('切片失败')
            return {'ok': False, 'msg': '切不出这段音频：%s' % e}
        if len(self._clips) >= 8:             # 只留最近几段，别把内存吃满
            for k in list(self._clips)[:len(self._clips) - 7]:
                self._clips.pop(k, None)
        self._clips[key] = url
        log.info('切片 @%.2fs 长 %.2fs → %d KB，用时 %.0f ms',
                 s.start, dur, len(url) // 1365, (time.time() - t0) * 1000)
        return {'ok': True, 'url': url, 'start': s.start, 'dur': dur}

    @staticmethod
    def _raw_index(it, s):
        """这句在 raw（识别原始结果）里是第几行，找不到给 -1。"""
        for j, row in enumerate(it.get('raw') or []):
            if abs(row[0] - s.start) < 0.05 and abs(row[1] - s.end) < 0.05:
                return j
        return -1

    @_logged
    def set_text(self, idx, si, text):
        """就地改一句的字。改完 txt / srt / Word 全都跟着变。"""
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        it = self._items[idx]
        sents = it['sentences']
        if not (0 <= si < len(sents)):
            return {'ok': False, 'msg': '没有这一句'}
        s = sents[si]
        new = ' '.join(str(text or '').split())
        old = s.text
        if new == old:
            return {'ok': True, 'changed': False, 'text': old}

        ri = self._raw_index(it, s)
        rows = it.get('raw') or []
        # 存副本：Sentence 是可变的，存引用的话改完原文就跟着没了
        self._push_undo({
            'idx': idx, 'si': si, 'deleted': not new,
            'sent': C.Sentence(s.start, s.end, s.text, s.speaker),
            'raw_i': ri,
            'raw_row': rows[ri] if 0 <= ri < len(rows) else None,
        })

        if not new:
            # 清空 = 这一句不要了（多半是识别出的噪声/语气词）
            sents.pop(si)
            if 0 <= ri < len(rows):
                rows.pop(ri)
            log.info('删句 [%d:%d] %r', idx, si, old[:30])
        else:
            s.text = new
            # 同步回 raw：回头重跑「区分说话人」时，改过的字也得留着
            if 0 <= ri < len(rows):
                rows[ri] = (rows[ri][0], rows[ri][1], new)
            log.info('改字 [%d:%d] %r → %r', idx, si, old[:30], new[:30])
        self._touch(idx)
        return {'ok': True, 'changed': True, 'text': new,
                'left': len(sents),
                'chars': sum(len(x.text) for x in sents)}

    def _push_undo(self, e):
        """记一条撤销（改字 / 删句），栈满就丢最老的。"""
        self._undo.append(e)
        while len(self._undo) > 300:
            self._undo.pop(0)

    def _restore(self, u):
        """把一条撤销记录写回句子（改字 / 删句共用）。"""
        it = self._items[u['idx']]
        sents = it['sentences']
        rows = it.get('raw') or []
        si = u['si']
        row = u.get('raw_row')
        if u['deleted']:
            sents.insert(min(si, len(sents)), u['sent'])
            if row is not None:
                rows.insert(min(u['raw_i'], len(rows)) if u['raw_i'] >= 0 else len(rows), row)
        elif 0 <= si < len(sents):
            sents[si] = u['sent']
            if row is not None and 0 <= u['raw_i'] < len(rows):
                rows[u['raw_i']] = (row[0], row[1], u['sent'].text)
        else:
            sents.insert(min(si, len(sents)), u['sent'])

    @_logged
    def replace_all(self, idx, q, r, push=True, collect=None):
        """当前文件里把 q 全部换成 r。一次 Ctrl+Z 整批退回，不是退一句。

        push=False + collect=[...] 时不动撤销栈，把记录交给调用方合并
        （术语表一次要跑好几条，得压成一条，否则 Ctrl+Z 要按十几次）。
        """
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        q = (q or '').strip()
        r = str(r or '')
        if not q:
            return {'ok': False, 'msg': '要先填要替换的词'}
        if q == r:
            return {'ok': True, 'n': 0, 'occ': 0, 'msg': '替换前后一样'}
        it = self._items[idx]
        sents = it['sentences']
        rows = it.get('raw') or []

        # 先只算，不改：删句会挪索引，边算边改容易串行
        changes = []
        for si, s in enumerate(sents):
            new, k = text_replace(s.text, q, r)
            if not k:
                continue
            new = ' '.join(new.split())       # 换完别留一串空格
            if not r:
                # 删词时顺手去掉因此露在句首的逗号顿号（把「嗯」去掉别留下「，我」）
                new = new.lstrip('，,、；;：: ')
            if new == s.text:
                continue
            changes.append([si, new, k, self._raw_index(it, s)])
        if not changes:
            return {'ok': True, 'n': 0, 'occ': 0, 'msg': '没找到要替换的词',
                    'left': len(sents), 'chars': sum(len(x.text) for x in sents)}

        # 一次替换只占一个撤销位：几百句的稿子也只压一条，Ctrl+Z 才能整批回来
        entries = []
        n_del = 0
        for si, new, _k, ri in changes:
            # 换完只剩标点（例如把「嗯」去掉只剩一个「。」）= 这句没内容了，按删句处理
            killed = not any(ch.isalnum() for ch in new)
            s = sents[si]
            entries.append({
                'idx': idx, 'si': si, 'deleted': killed,
                'sent': C.Sentence(s.start, s.end, s.text, s.speaker),
                'raw_i': ri,
                'raw_row': rows[ri] if 0 <= ri < len(rows) else None,
            })
            if killed:
                n_del += 1
                continue
            s.text = new
            # 同步回 raw：回头重跑「区分说话人」时，改过的字也得留着
            if 0 <= ri < len(rows):
                rows[ri] = (rows[ri][0], rows[ri][1], new)

        # 删句从后往前，索引才不会错位
        for si, new, _k, ri in reversed(changes):
            if any(ch.isalnum() for ch in new):
                continue
            sents.pop(si)
            if 0 <= ri < len(rows):
                rows.pop(ri)

        if push:
            self._undo.append({'idx': idx, 'items': entries})
            while len(self._undo) > 300:
                self._undo.pop(0)
        elif collect is not None:
            collect.extend(entries)

        n_sent = len(changes) - n_del
        n_occ = sum(k for _si, _n, k, _ri in changes)
        log.info('全部替换 %r → %r：%d 句 / %d 处，另删空句 %d', q[:20], r[:20],
                 n_sent, n_occ, n_del)
        self._touch(idx)
        return {'ok': True, 'n': n_sent, 'occ': n_occ, 'deleted': n_del,
                'left': len(sents), 'chars': sum(len(x.text) for x in sents)}

    # ---------------- 术语表
    def terms_get(self):
        t = terms_text()
        pairs = parse_terms(t)
        cm = [l.strip() for l in (t or '').splitlines() if l.strip().startswith('#')]
        return {'ok': True, 'text': t, 'n': len(pairs),
                'pairs': [[a, b] for a, b in pairs],
                'comments': cm,
                'auto': bool(load_settings().get('terms_auto', True))}

    @_logged
    def tip_off(self, kind):
        """用户点掉某条一次性提示，以后不再出现（目前只有术语表那条）。"""
        if kind == 'terms':
            save_setting('terms_tip_off', 1)
        return {'ok': True}

    @_logged
    def terms_set(self, text, auto=True):
        save_setting('terms', str(text or ''))
        save_setting('terms_auto', bool(auto))
        n = len(parse_terms(text))
        log.info('术语表存了 %d 条，转完自动套用=%s', n, auto)
        return {'ok': True, 'n': n}

    @_logged
    def terms_set_pairs(self, pairs, auto=True, comments=None):
        """界面两栏直接存。格式拼装在 Python 这一处，前后端不会各写一套。"""
        return self.terms_set(terms_from_pairs(pairs, comments), auto)

    @_logged
    def terms_add(self, pairs):
        """把刚才在替换条里做的一次替换记进术语表。

        用户发现错词的现场是稿子上的「替」，不是术语表弹窗；让他换个地方
        重打一遍「李蛋→李诞」是多余的。勾上「记住」就存进来。
        同一个左栏词被覆盖，顺序按原有表；`#` 注释留在末尾。
        """
        t = terms_text()
        new = parse_terms(terms_from_pairs(pairs, None))
        if not new:
            return {'ok': False, 'msg': '这条不值得记', 'n': len(parse_terms(t))}
        d, order = {}, []
        for a, b in parse_terms(t) + new:
            if a not in d:
                order.append(a)
            d[a] = b                      # 同左栏：后来者覆盖
        cm = [l.strip() for l in (t or '').splitlines() if l.strip().startswith('#')]
        save_setting('terms', terms_from_pairs([[a, d[a]] for a in order], cm))
        n = len(d)
        log.info('术语表追加 %d 条，现共 %d 条', len(new), n)
        return {'ok': True, 'n': n, 'added': len(new)}

    def _apply_terms(self, idx):
        """把术语表套到一份稿子上；整套只占一个撤销位。"""
        pairs = parse_terms(terms_text())
        if not pairs:
            return {'n': 0, 'occ': 0, 'terms': 0}
        merged = []
        sent = occ = 0
        self._no_touch = True            # 一条术语一次存盘就够了，别写十遍
        try:
            for q, r in pairs:
                # 别让每次替换各压一条撤销：攒到 merged 里，最后压成一条整批
                res = self.replace_all(idx, q, r, push=False, collect=merged)
                if res.get('ok') and res.get('occ'):
                    sent += res.get('n', 0)
                    occ += res.get('occ', 0)
        finally:
            self._no_touch = False
        if merged:
            self._undo.append({'idx': idx, 'items': merged})
            while len(self._undo) > 300:
                self._undo.pop(0)
        self._touch(idx)
        return {'n': sent, 'occ': occ, 'terms': len(pairs)}

    @_logged
    def apply_terms(self, idx):
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        if not parse_terms(terms_text()):
            return {'ok': False, 'msg': '术语表还是空的'}
        r = self._apply_terms(idx)
        if not r['occ']:
            return {'ok': True, 'n': 0, 'occ': 0,
                    'msg': '术语表里的词，这份稿子一个都没出现'}
        return {'ok': True, 'n': r['n'], 'occ': r['occ'],
                'msg': '按术语表改了 %d 处（%d 句）' % (r['occ'], r['n']),
                'left': len(self._items[idx]['sentences']),
                'chars': sum(len(x.text) for x in self._items[idx]['sentences'])}

    # ---------------- 草稿
    def _touch(self, idx):
        """动过稿子就存一份草稿。存不下也不能影响改字。"""
        if getattr(self, '_no_touch', False):
            return
        try:
            self._draft_save(idx)
        except Exception:
            log.exception('存草稿失败')

    def _draft_save(self, idx, exported=False):
        if not (0 <= idx < len(self._items)):
            return
        it = self._items[idx]
        if not it.get('sentences'):
            return
        key = draft_key(it['path'])
        if not key:
            return
        try:
            os.makedirs(DRAFT_DIR, exist_ok=True)
        except Exception:
            return
        data = {
            'v': 1, 'key': key, 'path': it['path'], 'name': it['name'],
            'duration': it['duration'], 'saved_at': time.time(),
            'exported': bool(exported),
            'sentences': [[s.start, s.end, s.text, s.speaker]
                          for s in it['sentences']],
        }
        fp = draft_file(key)
        tmp = fp + '.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, fp)
        except Exception:
            log.exception('写草稿失败 %s', fp)
            try:
                os.remove(tmp)
            except Exception:
                pass

    def drafts(self):
        """列出本机存着的草稿（只给摘要，不太占带宽）。"""
        out = []
        try:
            names = os.listdir(DRAFT_DIR)
        except Exception:
            return out
        now = time.time()
        for fn in names:
            if not fn.endswith('.json'):
                continue
            fp = os.path.join(DRAFT_DIR, fn)
            try:
                with open(fp, encoding='utf-8') as f:
                    d = json.load(f)
            except Exception:
                continue
            if not isinstance(d, dict) or not d.get('sentences'):
                continue
            age = (now - float(d.get('saved_at') or 0)) / 86400.0
            if d.get('exported') and age > DRAFT_KEEP_DAYS:
                try:                     # 导出去过了、又放了两个月，清掉
                    os.remove(fp)
                except Exception:
                    pass
                continue
            rows = d['sentences']
            out.append({
                'key': d.get('key') or fn[:-5],
                'name': d.get('name') or '',
                'alive': os.path.isfile(d.get('path') or ''),
                'n': len(rows),
                'chars': sum(len(str(x[2])) for x in rows if len(x) > 2),
                'saved_at': float(d.get('saved_at') or 0),
                'exported': bool(d.get('exported')),
            })
        out.sort(key=lambda x: -x['saved_at'])
        return out

    @_logged
    def restore_draft(self, key):
        """把一份草稿接回列表，接着改。源文件删了也能看/能导出。"""
        if self._running:
            return {'ok': False, 'msg': '正在转写，等它跑完再恢复'}
        try:
            with open(draft_file(key), encoding='utf-8') as f:
                d = json.load(f)
        except Exception:
            log.exception('读草稿失败 %s', key)
            return {'ok': False, 'msg': '这份草稿读不出来了'}
        path = d.get('path') or ''
        name = d.get('name') or (os.path.basename(path) or '草稿')
        if path and any(it['path'] == path for it in self._items):
            return {'ok': False, 'msg': '这个文件已经在列表里了'}
        sents = []
        for row in d.get('sentences') or []:
            if not isinstance(row, (list, tuple)) or len(row) < 3:
                continue
            sents.append(C.Sentence(float(row[0]), float(row[1]), str(row[2]),
                                    str(row[3]) if len(row) > 3 else ''))
        if not sents:
            return {'ok': False, 'msg': '这份草稿是空的'}
        self._items.append({
            'path': path, 'name': name, 'size': 0,
            'duration': float(d.get('duration') or 0),
            'status': 'done', 'progress': 1.0,
            'msg': '%d 句 · 上次没导出的稿子' % len(sents),
            'sentences': sents, 'error': '',
            'raw': [(s.start, s.end, s.text) for s in sents],
            'last_spk': None,
        })
        log.info('恢复草稿 %s：%d 句', name, len(sents))
        self._sync()
        return {'ok': True, 'idx': len(self._items) - 1, 'n': len(sents), 'name': name}

    @_logged
    def drop_draft(self, key):
        if not key:
            return {'ok': False}
        for fn in os.listdir(DRAFT_DIR) if os.path.isdir(DRAFT_DIR) else []:
            if fn.startswith(key) and fn.endswith('.json'):
                try:
                    os.remove(os.path.join(DRAFT_DIR, fn))
                except Exception:
                    log.exception('删草稿失败 %s', fn)
        return {'ok': True}

    @_logged
    def audit(self, idx):
        """导出前扫一遍，把值得看一眼的句子挑出来。"""
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        sents = self._items[idx]['sentences']
        rows = audit_sentences(sents)
        counts = {}
        for k, _si, _t, _h in rows:
            counts[k] = counts.get(k, 0) + 1
        return {'ok': True, 'n': len(sents), 'counts': counts, 'total': len(rows),
                'items': [{'kind': k, 'si': si,
                           'text': (t if len(t) <= 90 else t[:90] + '…'), 'hint': h}
                          for k, si, t, h in rows[:12]]}

    @_logged
    def undo_text(self, idx=None):
        """撤销上一次改字/删句；上一次若是「全部替换」，整批一起退回。"""
        while self._undo:
            u = self._undo.pop()
            if idx is not None and u.get('idx') != idx:
                self._undo.append(u)
                return {'ok': False, 'msg': '这条不属于当前文件'}
            if u.get('items'):                     # 一次全部替换压成的一条
                if u['idx'] >= len(self._items):
                    continue
                items = u['items']
                for e in reversed(items):          # 倒序还原，删句的索引才不会错位
                    if e['idx'] < len(self._items):
                        self._restore(e)
                log.info('撤销整批 %d 句', len(items))
                self._touch(u['idx'])
                return {'ok': True, 'batch': True, 'n': len(items)}
            if u['idx'] >= len(self._items):
                continue
            self._restore(u)
            log.info('撤销 [%d:%d] → %r', u['idx'], u['si'], u['sent'].text[:30])
            self._touch(u['idx'])
            return {'ok': True, 'idx': u['idx'], 'si': u['si'],
                    'text': u['sent'].text, 'deleted': u['deleted']}
        return {'ok': False, 'msg': '没有可撤销的'}

    @_logged
    def apply_proof(self, idx, text):
        """把外部改好的校对稿按编号写回句子。整批算一次撤销。

        用户把稿子复制出去、用别的工具改完再粘回来 —— 这条路是刻意留的：
        程序自己不联网，改由用户自己拿出去改，隐私和责任都留在他那一边。
        """
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        it = self._items[idx]
        sents = it['sentences']
        if not sents:
            return {'ok': False, 'msg': '这个文件还没转完'}
        rows = it.get('raw') or []
        old = [(s.start, s.end, s.text, s.speaker, self._raw_index(it, s))
               for s in sents]
        changed, bad, empty, unknown = C.apply_proof(sents, text)
        if not changed:
            msg = '没有可回填的改动'
            if bad:
                msg += '（%d 行格式不认，检查是不是把「编号|说话人|正文」的竖线删了）' % bad
            return {'ok': False, 'msg': msg, 'changed': 0,
                    'bad': bad, 'empty': empty, 'unknown': unknown}
        entries = []
        for k, (st, en, tx, spk, ri) in enumerate(old):
            if k >= len(sents):
                break
            new_t = sents[k].text
            if new_t == tx:
                continue
            entries.append({
                'idx': idx, 'si': k, 'deleted': False,
                'sent': C.Sentence(st, en, tx, spk),
                'raw_i': ri,
                'raw_row': rows[ri] if 0 <= ri < len(rows) else None,
            })
            if 0 <= ri < len(rows):        # 同步回 raw，回头重跑分人时字还在
                rows[ri] = (rows[ri][0], rows[ri][1], new_t)
        if entries:
            self._undo.append({'idx': idx, 'items': entries})
            while len(self._undo) > 300:
                self._undo.pop(0)
        self._touch(idx)
        log.info('回填校对稿：改 %d 句，不认 %d 行，空 %d 行，越界 %d 行',
                 changed, bad, empty, unknown)
        msg = '回填了 %d 句' % changed
        if bad:
            msg += '，%d 行格式不认已跳过' % bad
        if empty:
            msg += '，%d 行是空的没动' % empty
        if unknown:
            msg += '，%d 行编号对不上' % unknown
        return {'ok': True, 'msg': msg, 'changed': changed, 'bad': bad,
                'empty': empty, 'unknown': unknown,
                'left': len(sents),
                'chars': sum(len(x.text) for x in sents)}

    @_logged
    def export(self, idx, kind, path=None):
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        it = self._items[idx]
        if not it['sentences']:
            return {'ok': False, 'msg': '这个文件还没转完'}
        stem = os.path.splitext(it['name'])[0]
        ext = {'txt': 'txt', 'srt': 'srt', 'vtt': 'vtt', 'md': 'md',
               'docx': 'docx', 'tsv': 'txt', 'json': 'json',
               'proof': 'txt'}[kind]
        if kind == 'proof':
            stem += '-校对稿'      # 别和正式稿同名，改完分不清哪个是哪个
        if not path:
            try:
                path = ND.save_file('导出为', [('%s 文件' % ext.upper(), '*.%s' % ext)],
                                    filename='%s.%s' % (stem, ext), default_ext=ext,
                                    initial_dir=load_settings().get('outdir') or None)
            except Exception:
                log.exception('保存对话框失败，退回系统接口')
                p = self._window.create_file_dialog(
                    webview.SAVE_DIALOG, save_filename='%s.%s' % (stem, ext),
                    file_types=('文件 (*.%s)' % ext,))
                path = (p if isinstance(p, str) else (p[0] if p else ''))
            if not path:
                return {'ok': False, 'msg': '已取消'}

        meta = stem
        if not self._write(idx, kind, path, meta):
            return {'ok': False, 'msg': '写文件失败，换个位置试试'}
        self._draft_save(idx, exported=True)
        self._remember_dir(path)
        log.info('导出 %s → %s', kind, path)
        return {'ok': True, 'msg': '已保存', 'path': path}

    def _render(self, kind, sents, meta):
        if kind == 'srt':
            return C.to_srt(sents)
        if kind == 'vtt':
            return C.to_vtt(sents)
        if kind == 'md':
            return C.to_md(sents, meta)
        if kind == 'json':
            return C.to_json(sents, meta)
        if kind == 'tsv':
            return C.to_tsv(sents)
        if kind == 'proof':
            return C.to_proof(sents, meta)
        return C.to_txt(sents, meta)

    def _write(self, idx, kind, path, meta=''):
        """把第 idx 份稿子按 kind 写到 path。批量导出和单份导出共用。"""
        it = self._items[idx]
        meta = meta or os.path.splitext(it['name'])[0]
        try:
            if kind == 'docx':
                C.to_docx(it['sentences'], path, meta)
                return True
            data = self._render(kind, it['sentences'], meta)
            enc = 'utf-8-sig' if kind not in ('srt', 'vtt', 'json') else 'utf-8'
            with open(path, 'w', encoding=enc, newline='\n') as f:
                f.write(data)
            return True
        except Exception:
            log.exception('写文件失败 %s', path)
            return False

    @_logged
    def export_all(self, kind):
        """把所有转好的文件按同一种格式导到同一个文件夹。

        一期播客转完改完，导一种格式就够了；十个文件点十次对话框没有意义。
        """
        done = [i for i, it in enumerate(self._items)
                if it['status'] == 'done' and it['sentences']]
        if not done:
            return {'ok': False, 'msg': '还没有转好的文件'}
        try:
            d = ND.open_folder('选一个文件夹，放导出的稿子')
        except Exception:
            log.exception('目录对话框失败，退回系统接口')
            r = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            d = r[0] if isinstance(r, (list, tuple)) and r else (r or '')
        if not d:
            return {'ok': False, 'msg': '已取消'}
        ext = {'txt': 'txt', 'srt': 'srt', 'vtt': 'vtt', 'md': 'md',
               'docx': 'docx', 'tsv': 'txt', 'json': 'json',
               'proof': 'txt'}[kind]
        n = fail = 0
        for i in done:
            stem = os.path.splitext(self._items[i]['name'])[0]
            p = os.path.join(d, '%s.%s' % (stem, ext))
            k = 2
            while os.path.exists(p):        # 不覆盖同名的旧文件
                p = os.path.join(d, '%s-%d.%s' % (stem, k, ext))
                k += 1
            if self._write(i, kind, p):
                self._draft_save(i, exported=True)
                n += 1
            else:
                fail += 1
        if n:
            save_setting('outdir', d)
        log.info('批量导出 %s：%d 份成功 %d 份失败 → %s', kind, n, fail, d)
        return {'ok': bool(n), 'n': n, 'fail': fail, 'dir': d,
                'msg': '导出 %d 份到 %s' % (n, d) if n else '一份都没写成功'}

    def _remember_dir(self, path):
        """记住这次导到哪，下次对话框直接开在那儿。"""
        d = os.path.dirname(os.path.abspath(path or ''))
        if d and os.path.isdir(d):
            save_setting('outdir', d)

    def copy_text(self, idx):
        if not (0 <= idx < len(self._items)):
            return ''
        txt = C.to_txt(self._items[idx]['sentences'])
        try:
            self._window.evaluate_js('navigator.clipboard.writeText(%s)' % json.dumps(txt))
        except Exception:
            pass
        return txt

    def open_path(self, path):
        try:
            if os.path.isdir(path):
                os.startfile(path)
            else:
                subprocess.Popen(['explorer', '/select,', path])
        except Exception:
            pass

    def open_output_dir(self, idx):
        if 0 <= idx < len(self._items):
            self.open_path(os.path.dirname(self._items[idx]['path']))

    # ---------------- 帮助
    def open_help(self):
        p = os.path.join(HERE, '帮助.md')
        if os.path.exists(p):
            os.startfile(p)

    def open_repo(self):
        try:
            os.startfile('https://podcatcher962.github.io/yanzha/')
        except Exception:
            pass


def _find_main_window(title):
    """找到真正的程序主窗。

    FindWindowW(None, title) 在这里不可靠：同名的还有一个隐藏小窗
    （实测 136×39），着色着到它身上，主窗毫无变化。改成枚举可见顶层窗口，
    取同名里面积最大的那个。
    """
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32
    best = [0, 0]
    CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        try:
            if not u.IsWindowVisible(hwnd):
                return True
            n = u.GetWindowTextLengthW(hwnd)
            if n <= 0:
                return True
            buf = ctypes.create_unicode_buffer(n + 1)
            u.GetWindowTextW(hwnd, buf, n + 1)
            if buf.value != title:
                return True
            r = wintypes.RECT()
            u.GetWindowRect(hwnd, ctypes.byref(r))
            area = (r.right - r.left) * (r.bottom - r.top)
            if area > best[1]:
                best[0], best[1] = hwnd, area
        except Exception:
            pass
        return True

    try:
        u.EnumWindows(CB(cb), 0)
    except Exception:
        return 0
    return best[0]


def _title_bar(title, theme='dark'):
    """把 Windows 标题栏压成跟界面一个调子（Win11/10 都吃这个）。

    暗色：标题栏深色 + 浅色字；亮色：标题栏浅色 + 深色字。
    不这么做的时候，切到亮色界面会顶着一根黑标题栏，看着像没切干净。
    """
    try:
        import ctypes
        hwnd = _find_main_window(title)
        if not hwnd:
            return False
        light = (theme == 'light')
        on = ctypes.c_int(0 if light else 1)          # 20 = 沉浸式深色标题栏
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(on), 4)
        border, caption, text = ((0x00D0CBC2, 0x00F6F3EC, 0x00221F1A) if light
                                 else (0x003C3633, 0x00201C1B, 0x00E3E6E8))
        for attr, rgb in ((34, border), (35, caption)):
            c = ctypes.c_int(rgb)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(c), 4)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 36, ctypes.byref(ctypes.c_int(text)), 4)   # 标题栏文字色
        return True
    except Exception:
        pass


def _after_start(api=None):
    import time as _t
    th = 'light' if load_settings().get('theme') == 'light' else 'dark'
    # 冷启动要 2~3 秒才把窗口建出来，早几轮 FindWindow 必然落空。
    # 原来只试 6 次 × 0.25 秒，正好全错过 —— 亮色界面上就顶着一根黑标题栏。
    # 现在试到成功才停（最多约 12 秒），失败也只是标题栏不好看，不影响功能。
    for _ in range(60):
        try:
            if _title_bar(APP_TITLE, th):
                break
        except Exception:
            pass
        _t.sleep(0.2)
    # 把文件拖到 exe 图标上、或「右键 → 打开方式 → 言札」时，直接排进队列
    try:
        files = [p for p in sys.argv[1:] if os.path.isfile(p)]
        if files and api is not None:
            api.add_paths(files)
            log.info('命令行带入 %d 个文件', len(files))
    except Exception:
        log.exception('处理命令行文件失败')


def _diag(window):
    """启动后盯着界面状态，把关键信息写进日志（排查用，正式版保留无妨）。"""
    import time as _t
    for i in range(8):
        _t.sleep(2)
        try:
            a = window.evaluate_js('typeof window.pywebview')
            b = window.evaluate_js('(window.pywebview && typeof window.pywebview.api) || "none"')
            c = window.evaluate_js('typeof booted === "undefined" ? "noVar" : (booted ? "booted" : "idle")')
            log.info('UI 状态 %ds: pywebview=%s api=%s boot=%s', (i + 1) * 2, a, b, c)
        except Exception as e:
            log.info('UI 状态 %ds: 取不到（%s）', (i + 1) * 2, e)


def main():
    api = Api()
    html = os.path.join(HERE, 'yanzha.html')
    # 窗口底色跟主题走：亮色主题下开窗不再先闪一下黑
    bg = '#f6f3ec' if load_settings().get('theme') == 'light' else '#1b1c1f'
    window = webview.create_window(
        APP_TITLE, url=html, js_api=api,
        width=1180, height=760, min_size=(900, 600),
        background_color=bg, text_select=True)
    api.bind(window)
    threading.Thread(target=_diag, args=(window,), daemon=True).start()
    webview.start(lambda: _after_start(api), debug=False)


if __name__ == '__main__':
    main()
