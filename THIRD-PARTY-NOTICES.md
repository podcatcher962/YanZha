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

### SenseVoice Small（语音识别模型）
- 文件：`models/asr/model.int8.onnx`、`models/asr/tokens.txt`
- 模型名称（**必须保留**）：**SenseVoice Small** / `sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17`
- 上游作者：**FunAudioLLM / SenseVoice**（阿里巴巴集团通义实验室）
  - https://github.com/FunAudioLLM/SenseVoice
  - https://www.modelscope.cn/models/iic/SenseVoiceSmall
- 本包内分发格式：sherpa-onnx 转换版
  https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models
- **许可：FunASR Model Open Source License Agreement v1.1**
  （版权所有 © 2023-2028 Alibaba Group，全文见
  [`licenses/FunASR-MODEL-LICENSE.txt`](licenses/FunASR-MODEL-LICENSE.txt) 与
  https://github.com/modelscope/FunASR/blob/main/MODEL_LICENSE ）

**该许可对本项目的约束与我们如何遵守：**

| 许可条款 | 内容 | 本项目做法 |
|---|---|---|
| 2.1 许可 | 可自由使用、复制、修改、分享 | 随包分发模型，仅本地推理 |
| **2.2 限制** | **必须注明出处与作者信息，并保留模型名称** | 模型原名 `SenseVoice Small` 原样保留在 `models/asr/` 目录名、README、程序「关于」页、本文件与 `NOTICE` 中；出处与作者如上所列；许可全文随包提供 |
| 3 责任 | 模型仅作参考学习之用，阿里不承担任何责任 | 已在「免责声明」中声明转写结果可能有错，需人工核对 |
| 4.2 社区 | 不得无理贬损 | 本项目仅客观陈述许可与来源，无任何贬损表述 |
| 5 终止 | 违反条款即自动终止许可 | 如上条款均已遵守 |

> 说明：这是**模型权重**的许可，不是 OSI 标准许可，但与 MIT 兼容（MIT 允许聚合与分发第三方组件）。
> 言札自身的代码仍为 MIT；模型部分按其上游许可分发。若你将本软件用于商业用途，
> 请自行再核对一次上游许可的最新版本。


### silero-vad（语音活动检测）
- 文件：`models/vad/silero_vad.onnx`
- 来源：https://github.com/snakers4/silero-vad
- 许可：**MIT**

### 3D-Speaker CAM++（说话人声纹）
- 文件：`models/speaker/campplus.onnx`
- 上游：https://github.com/modelscope/3D-Speaker
- 分发格式：sherpa-onnx 转换版（speaker-recognition-models release）
- 许可：**Apache-2.0**（版权归 modelscope / 3D-Speaker 作者）

---

## 说明

- 本项目不包含任何音视频内容、字幕库、训练数据集。
- 所有模型均在本地 CPU 上推理，程序不发起任何网络请求。
- 若你是权利人并认为上述分发方式不妥，请通过
  [Issues](https://github.com/podcatcher962/YanZha/issues) 联系，我们会调整或移除。

---

**© 永远的兰兰 · Lanlan Eternal** — https://github.com/podcatcher962/YanZha
