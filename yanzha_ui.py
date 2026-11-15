# -*- coding: utf-8 -*-
"""言札 · 桌面端（pywebview 壳 + 单文件 HTML 界面）。

窗口里的活都交给 yanzha_core；这里只负责：选文件、排队、报进度、导出。
全程不联网，不上传，不写注册表。
"""
from __future__ import annotations

import functools
import json
import logging
import os
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
VERSION = '0.2.0'


_init_log()
log = logging.getLogger('yanzha')
log.info('=== 启动 v%s | frozen=%s | python=%s',
         VERSION, getattr(sys, 'frozen', False), sys.version.split()[0])
log.info('程序目录 %s', HERE)
log.info('日志 %s', LOG_PATH)


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
                 'error': it['error']}
                for i, it in enumerate(self._items)]

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
                'last_spk': None,     # 上次转写时的「区分说话人」取值
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

    def start(self):
        if self._running:
            return {'ok': False, 'msg': '正在转写'}
        todo = []
        for i, it in enumerate(self._items):
            if it['status'] == 'run':
                continue
            # 已经转好的、参数又没变，就别重跑（改了说话人勾选才需要重来）
            if it['status'] == 'done' and it.get('last_spk') == self._speaker_on:
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
                reuse = bool(it.get('raw')) and it.get('last_spk') != self._speaker_on
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
                    it['last_spk'] = self._speaker_on
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
                    it['msg'] = '%d 句 · %d 字%s' % (
                        len(res['sentences']), res['chars'], extra)
                    log.info('转写完成 %s：%d 句 %d 字 %d 人 语种=%s',
                             it['name'], len(res['sentences']), res['chars'],
                             nspk, res.get('lang') or '-')
            except C.DecodeError as e:
                it['status'] = 'error'
                it['error'] = str(e)
            except Exception as e:
                it['status'] = 'error'
                it['error'] = '出错：%s' % e
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
        return {'ok': True, 'n': n}

    @_logged
    def export(self, idx, kind, path=None):
        if not (0 <= idx < len(self._items)):
            return {'ok': False, 'msg': '没有内容'}
        it = self._items[idx]
        if not it['sentences']:
            return {'ok': False, 'msg': '这个文件还没转完'}
        stem = os.path.splitext(it['name'])[0]
        ext = {'txt': 'txt', 'srt': 'srt', 'vtt': 'vtt', 'md': 'md',
               'docx': 'docx', 'tsv': 'txt', 'json': 'json'}[kind]
        if not path:
            try:
                path = ND.save_file('导出为', [('%s 文件' % ext.upper(), '*.%s' % ext)],
                                    filename='%s.%s' % (stem, ext), default_ext=ext)
            except Exception:
                log.exception('保存对话框失败，退回系统接口')
                p = self._window.create_file_dialog(
                    webview.SAVE_DIALOG, save_filename='%s.%s' % (stem, ext),
                    file_types=('文件 (*.%s)' % ext,))
                path = (p if isinstance(p, str) else (p[0] if p else ''))
            if not path:
                return {'ok': False, 'msg': '已取消'}

        meta = stem
        if kind == 'docx':
            C.to_docx(it['sentences'], path, meta)
            return {'ok': True, 'msg': '已保存', 'path': path}

        if kind == 'srt':
            data = C.to_srt(it['sentences'])
        elif kind == 'vtt':
            data = C.to_vtt(it['sentences'])
        elif kind == 'md':
            data = C.to_md(it['sentences'], meta)
        elif kind == 'json':
            data = C.to_json(it['sentences'], meta)
        elif kind == 'tsv':
            data = C.to_tsv(it['sentences'])
        else:
            data = C.to_txt(it['sentences'], meta)

        enc = 'utf-8-sig' if kind not in ('srt', 'vtt', 'json') else 'utf-8'
        with open(path, 'w', encoding=enc, newline='\n') as f:
            f.write(data)
        log.info('导出 %s → %s', kind, path)
        return {'ok': True, 'msg': '已保存', 'path': path}

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


def _dark_titlebar(title):
    """把 Windows 标题栏压成深色，跟界面一个调子（Win11/10 都吃这个）。"""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if not hwnd:
            return
        on = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(on), 4)
        # 边框色 + 标题栏色（Win11）
        for attr, rgb in ((34, 0x003C3633), (35, 0x00201C1B)):
            c = ctypes.c_int(rgb)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(c), 4)
        # 文字改成浅色
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(ctypes.c_int(0x00E3E6E8)), 4)
    except Exception:
        pass


def _after_start():
    import time as _t
    for _ in range(6):
        _t.sleep(0.25)
        try:
            _dark_titlebar(APP_TITLE)
        except Exception:
            pass


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
    window = webview.create_window(
        APP_TITLE, url=html, js_api=api,
        width=1180, height=760, min_size=(900, 600),
        background_color='#1b1c1f', text_select=True)
    api.bind(window)
    threading.Thread(target=_diag, args=(window,), daemon=True).start()
    webview.start(_after_start, debug=False)


if __name__ == '__main__':
    main()
