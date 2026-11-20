# -*- coding: utf-8 -*-
"""热词表 —— 把听错的专名改回来，一个别的字都不碰。

做法：整句和词条都转成拼音，用词条长度做定长滑窗比对。
音对上了、字不一样，就按词条的写法替换。全程规则，不改写、不增删、不联网。

为什么不交给生成式模型：录音稿是证据性文本。模型再准也会顺手润色，
把口语洗成书面语，人回头对音频就对不上。这里只换字，
改了什么一眼可见，而且能逐条撤回。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

try:
    from pypinyin import pinyin as _pinyin, Style as _Style
    _HAS_PINYIN = True
except Exception:                                    # 没装拼音库就退化成纯文字匹配
    _HAS_PINYIN = False

# 声母/韵母里常见的听混对。只放真的分不清的，放宽太多会误伤。
NEAR = {
    ('zh', 'z'), ('ch', 'c'), ('sh', 's'),
    ('n', 'l'), ('f', 'h'), ('r', 'l'),
    ('in', 'ing'), ('en', 'eng'), ('an', 'ang'),
    ('ian', 'iang'), ('uan', 'uang'), ('an', 'uan'),
    ('ong', 'eng'), ('un', 'ong'),
}

# 音节拆成 声母 + 韵母 + 声调
_SYL = re.compile(r'^([a-z]+?)([1-5])$')

_TONE_MAP = dict(zip('12345', '12345'))


def _split(syl: str):
    """'zhang1' -> ('zhang', '1')；没有声调数字返回 ('zhang', '')。"""
    m = _SYL.match(syl)
    if m:
        return m.group(1), m.group(2)
    return syl, ''


def _near(a: str, b: str) -> bool:
    """两个拼音（无声调）是不是听混对。"""
    if a == b:
        return True
    for x, y in NEAR:
        if (a.startswith(x) and b.startswith(y)) or (a.startswith(y) and b.startswith(x)):
            return True
        if (a.endswith(x) and b.endswith(y)) or (a.endswith(y) and b.endswith(x)):
            return True
    return False


def _sim(a: str, b: str, strict_tone: bool = False) -> float:
    """两个音节的相似度。1.0 完全一样，0.92 只差声调，0.72 听混对，0 不相干。"""
    if a == b:
        return 1.0
    ba, ta = _split(a)
    bb, tb = _split(b)
    if ba == bb:
        if strict_tone and ta != tb:
            return 0.0
        return 0.92
    if _near(ba, bb):
        return 0.72
    return 0.0


def _is_cjk(ch: str) -> bool:
    return '\u4e00' <= ch <= '\u9fff'


_CACHE: dict[str, str] = {}


def _one(ch: str) -> str:
    """单个汉字的拼音（带声调数字）。整段调 pypinyin 会因英文数字合并而错位，
    这里逐字取；常用字只有几百个，缓存后不慢。"""
    if not _is_cjk(ch):
        return ''
    got = _CACHE.get(ch)
    if got is not None:
        return got
    if _HAS_PINYIN:
        try:
            item = _pinyin(ch, style=_Style.TONE3, neutral_tone_with_five=True)
            got = (item[0][0] if item and item[0] else '').lower()
        except Exception:
            got = ''
    else:
        got = ''
    _CACHE[ch] = got
    return got


def _encode(text: str):
    """逐字符转拼音，返回 [(原字, 拼音, 是否汉字)]。非汉字拼音给空串。
    长度严格等于 len(text)，后面的滑窗靠这个。"""
    return [(ch, _one(ch), _is_cjk(ch)) for ch in (text or '')]


@dataclass
class Term:
    text: str                       # 正确写法
    reading: list[str] = field(default_factory=list)   # 可选，用户手写的拼音
    aliases: list[str] = field(default_factory=list)   # 可选，明确认定是错的写法

    def keys(self, strict_tone: bool = False):
        raw = self.reading if self.reading else [p for _, p, _ in _encode(self.text)]
        return [p.lower() for p in raw]

    @property
    def ok(self) -> bool:
        return len(self.text) >= 2 and all('\u4e00' <= c <= '\u9fff' for c in self.text)


@dataclass
class Hit:
    index: int          # 第几句（0 起）
    start: int          # 句中字符起点
    end: int            # 句中字符终点（不含）
    old: str            # 原来的字
    new: str            # 换成什么
    term: str           # 命中的词条
    score: float        # 音相似度
    kind: str = 'phon'  # alias / phon

    @property
    def how(self) -> str:
        if self.kind == 'alias':
            return '别名'
        return '同音' if self.score >= 0.999 else '近音'


def parse_terms(text: str) -> tuple[list[Term], list[str]]:
    """解析热词表。一行一条，三种写法都认：

    ```
    张小燕                                 只写正确写法，靠拼音自己找
    张小燕 zhang1 xiao3 yan4               附带读音，多音字用这个钉死
    张小燕 张晓燕 张小艳                    列别名：这些写法一定是错的，直接换掉
    ```

    第二列往后，长得像拼音的算读音，是汉字的算别名，可以混着写。
    返回 (词表, 被丢掉的坏行说明)。
    """
    terms, bad = [], []
    for no, raw in enumerate((text or '').splitlines(), 1):
        ln = raw.strip()
        if not ln or ln.startswith('#'):
            continue
        parts = ln.replace('\u3000', ' ').split()
        word = parts[0]
        reading, aliases = [], []
        for p in parts[1:]:
            if re.fullmatch(r'[a-zA-Z]+[1-5]?', p):
                reading.append(p.lower())
            else:
                if len(p) == len(word):
                    aliases.append(p)
                else:
                    bad.append('第 %d 行：别名「%s」和「%s」字数不一致，已忽略'
                               % (no, p, word))
        t = Term(word, reading, aliases)
        if not t.ok:
            bad.append('第 %d 行「%s」：不足两个字或含非汉字，已跳过' % (no, ln))
            continue
        terms.append(t)
    return terms, bad


def dump_terms(terms: list[Term]) -> str:
    lines = ['# 热词表：一行一条，先写希望稿子里出现的样子',
             '# 后面可以跟读音：  张小燕 zhang1 xiao3 yan4',
             '# 也可以跟错法：    张小燕 张晓燕 张小艳',
             '']
    for t in terms:
        lines.append(' '.join([t.text] + list(t.reading) + list(t.aliases)))
    return '\n'.join(lines) + '\n'


def scan(sentences, terms: list[Term], thr: float = 0.86,
         strict_tone: bool = False, min_len: int = 2) -> list[Hit]:
    """找出所有该改的地方，不改动句子本身。"""
    if not terms:
        return []
    pool = [t for t in terms if len(t.text) >= min_len]
    if not pool:
        return []
    # 长词优先，避免「小燕」抢了「张小燕」
    pool.sort(key=lambda t: -len(t.text))
    keys = [(t, t.keys()) for t in pool]

    hits: list[Hit] = []
    for si, s in enumerate(sentences):
        enc = _encode(s.text)
        text = s.text
        cands = []
        taken = []
        # 1) 别名：用户明说了这些写法是错的，认字不认音，优先占位
        for term in pool:
            for al in term.aliases:
                pos = text.find(al)
                while pos >= 0:
                    if not any(not (pos + len(al) <= a or pos >= b) for a, b in taken):
                        taken.append((pos, pos + len(al)))
                        cands.append((1.0, len(al), pos, al, term.text, term.text, 'alias'))
                    pos = text.find(al, pos + 1)
        # 2) 拼音滑窗
        for term, tk in keys:
            n = len(tk)
            if n < 2 or n > len(enc):
                continue
            for i in range(0, len(enc) - n + 1):
                if any(not (i + n <= a or i >= b) for a, b in taken):
                    continue
                win = enc[i:i + n]
                if not all(cjk for _, _, cjk in win):
                    continue
                old = text[i:i + n]
                if old == term.text:
                    continue
                lim = 0.90 if n == 2 else thr
                sc = sum(_sim(win[k][1], tk[k], strict_tone) for k in range(n)) / n
                if sc >= lim:
                    cands.append((sc, n, i, old, term.text, term.text, 'phon'))
        # 分高的先占位，位置不重叠才收
        cands.sort(key=lambda x: (-x[0], -x[1], x[2]))
        taken = []
        for sc, n, i, old, new, term_text, kind in cands:
            if any(not (i + n <= a or i >= b) for a, b in taken):
                continue
            taken.append((i, i + n))
            hits.append(Hit(si, i, i + n, old, new, term_text, sc, kind))
    return hits


def apply_hits(sentences, hits: list[Hit]) -> int:
    """按扫描结果改句子，一句里多处从后往前改，避免位移。返回改了几处。"""
    by_sent: dict[int, list[Hit]] = {}
    for h in hits:
        by_sent.setdefault(h.index, []).append(h)
    n = 0
    for si, hs in by_sent.items():
        s = sentences[si]
        t = s.text
        for h in sorted(hs, key=lambda x: -x.start):
            if t[h.start:h.end] != h.old:      # 前面那处改过就跳过，不硬改
                continue
            t = t[:h.start] + h.new + t[h.end:]
            n += 1
        s.text = t
    return n


def revert_hits(sentences, hits: list[Hit]) -> int:
    """把某一批改动撤回（只撤文字没被别人再改过的）。"""
    by_sent: dict[int, list[Hit]] = {}
    for h in hits:
        by_sent.setdefault(h.index, []).append(h)
    n = 0
    for si, hs in by_sent.items():
        s = sentences[si]
        t = s.text
        for h in sorted(hs, key=lambda x: -x.start):
            if t[h.start:h.end] != h.new:
                continue
            t = t[:h.start] + h.old + t[h.end:]
            n += 1
        s.text = t
    return n


# 提候选时要滤掉的虚词。专名几乎不会是这些，留着只会把真名淹掉。
_STOP = set('''
我们 你们 他们 她们 它们 咱们 大家 自己 别人 人家
这个 那个 这些 那些 这样 那样 这么 那么 这里 那里
什么 怎么 为什么 因为 所以 但是 然后 而且 就是 也是 还是 只是 可是
如果 虽然 不过 已经 可以 应该 需要 觉得 认为 知道 看到 听到 说到
一个 一些 一样 一直 一下 一点 一次 时候 现在 以后 以前 今天 明天 昨天
由于 对于 关于 根据 通过 按照 为了 以及 并且 或者 不是 没有 不会 不能
最后 首先 其次 其实 大概 可能 真的 非常 比较 有点 有些 特别 一定
'''.split())


def suggest_terms(sentences, limit: int = 40) -> list[str]:
    """从稿子里挑出「像专名」的词，给用户当热词表草稿。

    判据：2~4 个汉字、稿子里出现 >= 2 次、不是虚词。
    这只是草稿，用户来删改。自动提不出真专名，提个方向就够了。
    """
    from collections import Counter
    cnt: Counter[str] = Counter()
    for s in sentences:
        t = re.sub(r'[^\u4e00-\u9fff]', ' ', s.text or '')
        for seg in t.split():
            for n in (4, 3, 2):
                for i in range(len(seg) - n + 1):
                    cnt[seg[i:i + n]] += 1
    out = []
    for w, c in cnt.most_common(300):
        if c < 2 or len(w) < 2 or w in _STOP:
            continue
        # 已经被更长的候选包含的片段不要，免得表里一堆重叠词
        if any(w in o for o in out):
            continue
        out.append(w)
        if len(out) >= limit:
            break
    return out
