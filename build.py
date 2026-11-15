# -*- coding: utf-8 -*-
"""言札 · 打包脚本：PyInstaller 出 exe，再把模型和 ffmpeg 摆到同级目录。

产物在 dist/ 下：
    dist/YanZha.exe          主程序（不含模型，启动快）
    dist/models/             三个模型
    dist/ffmpeg.exe          解码用
发布时把 dist 整个打成 zip。
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

MODELS = [
    # v0.2.0 起用 SenseVoice：中英日韩粤五语合一，自带标点与逐字时间戳。
    # 一个 228 MB 的模型替掉了原来「识别 233.7 + 标点 76」，包反而小 81 MB。
    (os.path.join(ROOT, '_tools', 'dl', 'asr',
                  'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'),
     os.path.join('models', 'asr'), ['model.int8.onnx', 'tokens.txt']),
    (os.path.join(ROOT, '_tools', 'dl', 'vad'),
     os.path.join('models', 'vad'), ['silero_vad.onnx']),
    # 说话人只用声纹模型（每句提一次，再聚类）。
    # pyannote 分割模型不放了：它 0.08× 实时，1 小时播客要 6 分钟，已经弃用。
    (os.path.join(ROOT, '_tools', 'dl', 'speaker'),
     os.path.join('models', 'speaker'), ['campplus.onnx']),
]


def run(cmd, cwd=None):
    print('>', ' '.join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd or HERE)
    if r.returncode != 0:
        raise SystemExit('命令失败，退出码 %d' % r.returncode)


def main():
    # 1. 清掉旧产物
    for d in ('build', 'dist'):
        p = os.path.join(HERE, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)

    # 2. PyInstaller
    run([PY, '-m', 'PyInstaller', '--noconfirm', '--clean',
         '--onefile', '--noconsole', '--name', 'YanZha',
         '--icon', os.path.join(HERE, 'yanzha.ico'),
         '--add-data', 'yanzha.html;.',
         '--hidden-import', 'sherpa_onnx',
         '--hidden-import', 'webview.platforms.edgechromium',
         '--hidden-import', 'docx',
         '--collect-binaries', 'sherpa_onnx',
         # 这些一个都用不上，带上只是白占体积
         '--exclude-module', 'tkinter',
         '--exclude-module', 'unittest',
         '--exclude-module', 'pydoc',
         '--exclude-module', 'doctest',
         '--exclude-module', 'lib2to3',
         '--exclude-module', 'test',
         'yanzha_ui.py'], cwd=HERE)

    dist = os.path.join(HERE, 'dist')
    # 3. 模型
    for src_dir, dst_rel, files in MODELS:
        dst = os.path.join(dist, dst_rel)
        os.makedirs(dst, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(src_dir, f), os.path.join(dst, f))
            print('  + %s / %s' % (dst_rel, f))

    # 4. ffmpeg
    # 用 essentials build（79MB），比原版全编解码器版省 21MB。
    # 实测 aac/mp3/vorbis/opus/flac/h264 解码齐全，转写只用得到这些。
    ff = os.path.join(ROOT, '_tools', 'ffmpeg_lite.exe')
    if not os.path.exists(ff):
        ff = os.path.join(ROOT, '_tools', 'ffmpeg.exe')
    if os.path.exists(ff):
        shutil.copy2(ff, os.path.join(dist, 'ffmpeg.exe'))
        print('  + ffmpeg.exe (%.0f MB)' % (os.path.getsize(ff) / 1048576))

    # 5. 说明
    for doc in ('README-使用说明.md', 'LICENSE'):
        p = os.path.join(HERE, doc)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(dist, doc))
            print('  + %s' % doc)

    # 6. 报体积
    total = 0
    for root, _, files in os.walk(dist):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    exe = os.path.join(dist, 'YanZha.exe')
    print('\n完成：dist/  共 %.1f MB' % (total / 1048576))
    if os.path.exists(exe):
        print('  YanZha.exe  %.1f MB' % (os.path.getsize(exe) / 1048576))


if __name__ == '__main__':
    main()
