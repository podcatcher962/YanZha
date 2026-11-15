# -*- coding: utf-8 -*-
"""原生文件对话框（ctypes 直调 comdlg32）。

为什么不用 pywebview 自带的 create_file_dialog：
它底层要 marshal 到 GUI 线程，从 js_api 工作线程调用时偶发卡死，
表现为"点一下窗口就无响应"。

这里踩过的三个坑，都修了：
  1. hwndOwner 传 None → 对话框没有主人，弹到主窗口后面去了。
     用户看不见，以为卡住，再点一次才偶然点到 —— 就是"要连点两次"。
     现在先找到本进程的可见主窗口当 owner，并在弹出前置前。
  2. 在非 STA 线程里调 GetOpenFileNameW，偶发长时间不返回。
     现在固定开一个 CoInitialize 过的临时线程来跑。
  3. 多选时返回值是 "目录\\0文件1\\0文件2\\0\\0"，而 create_unicode_buffer
     的 [:] 切片在第一个 \\0 就断了，只能拿到目录。改用 string_at 取全内存。
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
import threading

_OPEN = 0x00000008          # OFN_FILEMUSTEXIST
_MULTI = 0x00000200         # OFN_ALLOWMULTISELECT
_EXPLORER = 0x00080000      # OFN_EXPLORER
_OVERWRITE = 0x00000002     # OFN_OVERWRITEPROMPT
_HIDEREADONLY = 0x00000004
_PATHMUSTEXIST = 0x00000800
_NOCHANGEDIR = 0x00000008


class _OPENFILENAMEW(ctypes.Structure):
    _fields_ = [
        ('lStructSize', wt.DWORD),
        ('hwndOwner', wt.HWND),
        ('hInstance', wt.HINSTANCE),
        ('lpstrFilter', wt.LPCWSTR),
        ('lpstrCustomFilter', wt.LPWSTR),
        ('nMaxCustFilter', wt.DWORD),
        ('nFilterIndex', wt.DWORD),
        ('lpstrFile', wt.LPWSTR),
        ('nMaxFile', wt.DWORD),
        ('lpstrFileTitle', wt.LPWSTR),
        ('nMaxFileTitle', wt.DWORD),
        ('lpstrInitialDir', wt.LPCWSTR),
        ('lpstrTitle', wt.LPCWSTR),
        ('Flags', wt.DWORD),
        ('nFileOffset', wt.WORD),
        ('nFileExtension', wt.WORD),
        ('lpstrDefExt', wt.LPCWSTR),
        ('lCustData', wt.LPARAM),
        ('lpfnHook', wt.LPVOID),
        ('lpTemplateName', wt.LPCWSTR),
    ]


def _filter(pairs):
    """[('音视频文件', '*.mp3;*.m4a'), ...] → 双 \0 结尾的过滤器串"""
    s = []
    for name, pat in pairs:
        s.append('%s (%s)' % (name, pat.replace(';', ', ')))
        s.append(pat)
    s.append('')
    return '\0'.join(s) + '\0'


def _main_hwnd():
    """找本进程那个有标题的可见窗口，拿来当对话框的 owner。"""
    try:
        u = ctypes.windll.user32
        pid = os.getpid()
        hits: list[tuple[int, str]] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
        def cb(h, _l):
            if not u.IsWindowVisible(h):
                return True
            p = wt.DWORD()
            u.GetWindowThreadProcessId(h, ctypes.byref(p))
            if p.value != pid:
                return True
            n = u.GetWindowTextLengthW(h)
            if n <= 0:
                return True
            b = ctypes.create_unicode_buffer(n + 1)
            u.GetWindowTextW(h, b, n + 1)
            r = wt.RECT()
            u.GetWindowRect(h, ctypes.byref(r))
            if (r.right - r.left) > 300:
                hits.append((h, b.value))
            return True

        u.EnumWindows(cb, 0)
        return hits[0][0] if hits else None
    except Exception:
        return None


def _dialogs():
    """找所有系统对话框窗口（类名 #32770）。"""
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def cb(h, _l):
        cls = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(h, cls, 256)
        if cls.value == '#32770':
            found.append(h)
        return True

    try:
        ctypes.windll.user32.EnumWindows(cb, 0)
    except Exception:
        pass
    return found


def _ensure_front(delay: float = 0.35):
    """桌面版里 WebView2 会把对话框压到后面，用户看不见就以为卡死。

    实测：对话框 1.7 秒内就建好了，但从顶栏一点反应都没有，
    用户等十几秒再点一次才偶然看到 —— 就是"要点两次"。
    这里在弹窗后强行把它提到最前，不依赖 owner 的 z-order。
    """
    import time
    time.sleep(delay)
    u = ctypes.windll.user32
    for _ in range(6):
        ds = _dialogs()
        if ds:
            for h in ds:
                try:
                    u.ShowWindow(h, 5)          # SW_SHOW
                    u.BringWindowToTop(h)
                    u.SetForegroundWindow(h)
                except Exception:
                    pass
            return
        time.sleep(0.25)


def _sta(fn, timeout: float = 600.0):
    """在一个 CoInitialize(STA) 过的线程里跑对话框。

    comdlg32 在没有初始化 COM 的线程里会自己初始化成 MTA，
    偶发弹出后不响应；固定走 STA 就没有这个问题。
    """
    box: dict = {}

    def work():
        try:
            ctypes.windll.ole32.CoInitialize(None)
        except Exception:
            pass
        try:
            box['r'] = fn()
        except Exception as e:       # 别让异常从裸线程里跑掉
            box['e'] = e
        finally:
            try:
                ctypes.windll.ole32.CoUninitialize()
            except Exception:
                pass

    t = threading.Thread(target=work, daemon=True)
    t.start()
    threading.Thread(target=_ensure_front, daemon=True).start()
    t.join(timeout)
    if 'e' in box:
        raise box['e']
    return box.get('r')


def open_files(title='选择文件', pairs=None, initial_dir=None):
    """多选。返回绝对路径列表；取消返回 []。"""
    if pairs is None:
        pairs = [('所有文件', '*.*')]
    size = 32768
    buf = ctypes.create_unicode_buffer(size)

    def go():
        ofn = _OPENFILENAMEW()
        ofn.lStructSize = ctypes.sizeof(_OPENFILENAMEW)
        owner = _main_hwnd()
        ofn.hwndOwner = owner
        ofn.lpstrFilter = _filter(pairs)
        ofn.nFilterIndex = 1
        ofn.lpstrFile = ctypes.cast(buf, wt.LPWSTR)
        ofn.nMaxFile = size
        ofn.lpstrTitle = title
        ofn.lpstrInitialDir = initial_dir
        ofn.Flags = _OPEN | _MULTI | _EXPLORER | _PATHMUSTEXIST | _NOCHANGEDIR
        if owner:
            try:
                ctypes.windll.user32.SetForegroundWindow(owner)
            except Exception:
                pass
        return bool(ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)))

    if not _sta(go):
        return []

    # 整块内存取出来，别用 buf[:]（它在第一个 \0 就断）
    raw = ctypes.string_at(ctypes.addressof(buf), size * 2).decode('utf-16-le', 'ignore')
    parts = [x for x in raw.split('\x00')]
    while parts and not parts[-1]:
        parts.pop()
    if not parts:
        return []
    # 只选了一个：整串就是完整路径
    if len(parts) == 1:
        return [os.path.normpath(parts[0])]
    # 选了多个：第一段是目录，后面是文件名
    base = parts[0]
    out = []
    for name in parts[1:]:
        if not name:
            break
        out.append(os.path.normpath(os.path.join(base, name)))
    return out


def save_file(title='保存为', pairs=None, filename='', default_ext='',
              initial_dir=None):
    """单选保存。返回路径；取消返回 ''。"""
    if pairs is None:
        pairs = [('所有文件', '*.*')]
    buf = ctypes.create_unicode_buffer(4096)
    if filename:
        buf.value = filename

    def go():
        ofn = _OPENFILENAMEW()
        ofn.lStructSize = ctypes.sizeof(_OPENFILENAMEW)
        owner = _main_hwnd()
        ofn.hwndOwner = owner
        ofn.lpstrFilter = _filter(pairs)
        ofn.nFilterIndex = 1
        ofn.lpstrFile = ctypes.cast(buf, wt.LPWSTR)
        ofn.nMaxFile = 4096
        ofn.lpstrTitle = title
        ofn.lpstrInitialDir = initial_dir
        ofn.lpstrDefExt = default_ext or None
        ofn.Flags = _OVERWRITE | _HIDEREADONLY | _EXPLORER | _NOCHANGEDIR
        if owner:
            try:
                ctypes.windll.user32.SetForegroundWindow(owner)
            except Exception:
                pass
        return bool(ctypes.windll.comdlg32.GetSaveFileNameW(ctypes.byref(ofn)))

    if not _sta(go):
        return ''
    return os.path.normpath(buf.value)


def open_folder(title='选择文件夹'):
    """选目录（用 FOS_PICKFOLDERS 太绕，这里用 SHBrowseForFolder 简版）。"""
    BIF_RETURNONLYFSDIRS = 0x0001
    BIF_NEWDIALOGSTYLE = 0x0040

    class BROWSEINFOW(ctypes.Structure):
        _fields_ = [('hwndOwner', wt.HWND), ('pidlRoot', ctypes.c_void_p),
                    ('pszDisplayName', wt.LPWSTR), ('lpszTitle', wt.LPCWSTR),
                    ('ulFlags', wt.UINT), ('lpfn', ctypes.c_void_p),
                    ('lParam', wt.LPARAM), ('iImage', ctypes.c_int)]

    bi = BROWSEINFOW()
    bi.pszDisplayName = ctypes.create_unicode_buffer(260)
    bi.lpszTitle = title
    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE
    pidl = ctypes.windll.shell32.SHBrowseForFolderW(ctypes.byref(bi))
    if not pidl:
        return ''
    path = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetPathFromIDListW(pidl, path)
    ctypes.windll.ole32.CoTaskMemFree(pidl)
    return path.value
