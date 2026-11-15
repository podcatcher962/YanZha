# 第三方组件与许可 · Third-Party Notices

言札本身以 **MIT License** 发布（见 [LICENSE](LICENSE)）。
发行包内还包含下列第三方组件与模型，它们各自遵循自己的许可，本文件用于说明来源与声明。

---

## 运行时依赖（随发行包分发）

### FFmpeg
- 文件：`ffmpeg.exe`
- 来源：https://ffmpeg.org/ （Windows 构建取自 gyan.dev essentials 版）
- 许可：**LGPL / GPL**（该构建启用 GPL 组件，按 GPL 分发）
- 使用方式：程序仅以**独立进程调用**其可执行文件完成音视频解码，不链接其库。
- 源码：https://ffmpeg.org/download.html

### sherpa-onnx
- 用途：语音识别、语音检测、声纹提取的推理运行时
- 来源：https://github.com/k2-fsa/sherpa-onnx
- 许可：**Apache-2.0**

### pywebview
- 用途：界面容器（调用系统 WebView2）
- 来源：https://github.com/r0x0r/pywebview
- 许可：**BSD-3-Clause**

### python-docx
- 用途：导出 Word (.docx)
- 来源：https://github.com/python-openxml/python-docx
- 许可：**MIT**

### PyInstaller
- 用途：打包为单文件 exe（仅在构建时使用，运行时不额外分发其源码）
- 来源：https://github.com/pyinstaller/pyinstaller
- 许可：**GPL-2.0 with bootloader exception**

---

## 模型文件（随发行包分发）

模型许可归各自的上游作者所有。若你将模型用于商业用途，请先阅读上游许可条款。

### SenseVoice Small（语音识别）
- 文件：`models/asr/model.int8.onnx`、`models/asr/tokens.txt`
- 上游：FunAudioLLM / SenseVoice — https://github.com/FunAudioLLM/SenseVoice
- 分发格式：sherpa-onnx 转换版
  https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models
  （`sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17`）
- 许可：见上游仓库 LICENSE

### silero-vad（语音活动检测）
- 文件：`models/vad/silero_vad.onnx`
- 来源：https://github.com/snakers4/silero-vad
- 许可：**MIT**

### 3D-Speaker CAM++（说话人声纹）
- 文件：`models/speaker/campplus.onnx`
- 来源：https://github.com/modelscope/3D-Speaker
- 许可：**Apache-2.0**

---

## 说明

- 本项目不包含任何音视频内容、字幕库、训练数据集。
- 所有模型均在本地 CPU 上推理，程序不发起任何网络请求。
- 若你是权利人并认为上述分发方式不妥，请通过
  [Issues](https://github.com/podcatcher962/YanZha/issues) 联系，我们会调整或移除。

---

**© 永远的兰兰 · Lanlan Eternal** — https://github.com/podcatcher962/YanZha
