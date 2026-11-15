# 言札 · YanZha

**v0.3.0** · 2026-11-15

把录音、播客、会议、视频，变成能直接用的文字稿。

**不上传、不联网、不要账号、不限时长、不花钱。**

Windows 10/11 64 位 · 单文件程序 + 本地模型 · MIT 开源

> 仓库地址：**https://github.com/podcatcher962/YanZha**
> 作者：**永远的兰兰（Lanlan Eternal）**
> 下载：**[Releases](https://github.com/podcatcher962/YanZha/releases)**

*Turn recordings, podcasts, meetings and videos into usable transcripts.
Fully offline — nothing uploaded, no account, no time limit, free.
Five languages auto-detected (Chinese / English / Japanese / Korean /
Cantonese), speaker diarization, 7 export formats. Windows x64, MIT.*
*— [English section below ↓](#english)*

---

## 它是什么

一个完全离线的音视频转文字工具。声音只在这台电脑上处理，一个字节都不上传；
断网拔网线也能跑，程序里没有任何联网代码。

一小时录音，普通笔记本约 **三分钟**出稿，纯 CPU、不要显卡。

---

## 能干这些

| 能力 | 说明 |
|---|---|
| **五门语言** | 中文、English、日本語、한국어、粤语，自动判断语种，中英混说也认 |
| **区分说话人** | 多人播客/访谈按人分段，标「说话人 1 / 2 / 3」；单人录音自动去掉标注 |
| **说话人改名** | 点一下「说话人 1」改成「主持人」「嘉宾」，导出全部格式跟着变 |
| **校对改字** | 双击句子听原音，就地改字、删句、撤销，改完直接导出 |
| **七种导出** | txt / md / Word / srt / vtt / 带时间戳 txt / 结构化 json |
| **音视频通吃** | 音频 mp3 m4a wav flac aac ogg opus wma；视频 mp4 mkv mov avi flv webm ts m4v |
| **自动标点断句** | 模型自带标点，按句整理成段，不是一坨没有标点的流水 |
| **逐字时间戳** | 字幕能精确到每一句的起止，导入剪映、Premiere、B 站 |
| **字幕自动折行** | srt / vtt 里一句太长会断成两行，剪映里不溢屏 |
| **可中断** | 进度实时、随时能停；改「区分说话人」勾选不用重跑识别 |

---

## 怎么用

1. 双击 `YanZha.exe`
2. 点「添加音视频文件」，或把文件拖进窗口，选一个或一批
3. 点「开始转写」，等进度条走完
4. 点左边转好的文件，右边就是稿子
5. **双击任意一句听原音**，点句子右边的「改」就地改字（回车保存、清空即删句、`Ctrl+Z` 撤销）
6. 点说话人名字可以改成「主持人」「嘉宾」；按需要「导出」

> 一小时录音约三分钟（普通笔记本，不插电也跑）。
> 勾了「区分说话人」再多花半分钟左右，不会翻倍。

---

## 区分说话人

多人播客、访谈、对谈，勾上左下角的 **「区分说话人」**，稿子会按人分段。

- **单人录音勾了也没关系**：只分出一个人时标注自动去掉，导出的就是干净稿子
- 默认开着；确定是单人朗读、讲座，关掉更快
- 分几人不影响文字本身，只影响分段和标注
- 声音重叠、抢话、笑声多的时候，分人可能有偏差，这是这类技术的通病

---

## 关于隐私

- 声音**只在这台电脑上处理**，一个字节都不上传
- 程序里没有任何联网代码，不上报、不统计、不检查更新
- 不装服务、不写注册表、不改系统设置
- 断网也能正常用——可以自己拔掉网线试

---

## 性能实测

在同一台机器、同一批真实人声上量的，不是估算：

| 指标 | 数值 |
|---|---|
| 实时率 RTF | **0.026 ~ 0.047**（53.6 秒音频 → 2.96 秒出稿） |
| 一小时录音 | 约 2.8 ~ 3.3 分钟 |
| 分人额外开销 | 每句约 32 ms（84 秒双人对话 → 3 秒） |
| 模型加载 | 1.4 秒 |
| 冷启动 | 2 ~ 3 秒 |
| 内存 | 4 GB 可用（长录音建议 8 GB） |

---

## 常见问题

**转出来的字有错怎么办？**
先看录音质量（远场、回声、背景音重最容易出错）。稿子导出后可以直接改。人名、数字、专业词最容易错，重要内容请人工核对。

**能转哪些语言？**
中文、English、日本語、한국어、粤语，不用手动选，模型自己判断；一段里中英混说也认。普通话最准。四川话、天津话这类方言能认出大意，不保证每个字都对。

**要不要显卡？**
不要。纯 CPU，核显也能跑。

**文件特别大（两小时以上）？**
可以转，只是多等一会儿。进度实时，随时能停。

**出错了我该做什么？**
日志在 `%LOCALAPPDATA%\YanZha\yanzha.log`，把日志发到 [Issues](https://github.com/podcatcher962/YanZha/issues) 就能定位。

**改了勾选要重新转一遍吗？**
不用。识别结果留着，只重跑分人那一步，几十秒就好。

---

## 系统要求

- Windows 10 / 11（64 位）
- 内存 4 GB 以上（长录音建议 8 GB）
- 硬盘 400 MB 可用空间（程序 42 MB + 模型 256 MB + 解码器 79 MB）

### 发行包目录

```
YanZha.exe        主程序
ffmpeg.exe        音频解码（79 MB）
models/           模型（256 MB，不要删）
  asr/            识别（SenseVoice，中英日韩粤，自带标点）
  vad/            语音检测
  speaker/        说话人声纹
LICENSE           MIT 许可证
README-使用说明.md 离线版使用说明
```

**不要只把 exe 单独拷出来**，它要靠同目录的 `models` 才能启动。

---

## 技术实现

- **识别**：[sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) · SenseVoice Small int8
  一个模型顶掉原来「识别 + 标点」两套，自带标点、语种判定与逐字时间戳
- **语音检测**：silero-vad（先切出有人声的段，跳过静音，长音频才不浪费算力）
- **说话人**：3D-Speaker CAM++ 声纹（每句提一个向量）+ 余弦聚类。
  没有用滑窗分割模型——那个 0.08~0.11× 实时，一小时播客要 6 分钟；
  改成句级声纹后 84 秒对话只要 3 秒
- **界面**：pywebview（WebView2）+ 纯单文件 HTML，无框架无网络请求
- **文件对话框**：ctypes 直调 `comdlg32.GetOpenFileNameW`，跑在 STA 线程并设置 owner，
  避免对话框弹到主窗口后面
- **解码**：FFmpeg（仅调用其可执行文件）

### 从源码构建

```bash
pip install sherpa-onnx pywebview python-docx pyinstaller
# 把模型放好（目录结构见上），然后：
python build.py
```

模型不进仓库（体积原因），从 [sherpa-onnx releases](https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models) 下载：

| 目录 | 需要的文件 |
|---|---|
| `models/asr/` | `sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17` 的 `model.int8.onnx` + `tokens.txt` |
| `models/vad/` | `silero_vad.onnx` |
| `models/speaker/` | `campplus.onnx` |

---

## 免责声明

1. 本软件是**本地转写工具**，只处理你自己提供的音视频文件，**不提供**任何音视频、文字内容的获取、下载、搜索或传播服务。
2. 你应当确保对所处理的音视频**享有合法权利**，或已取得权利人许可。因内容来源产生的任何纠纷，由使用者自行承担。
3. 转写结果由机器自动生成，**可能存在错误**，不构成任何形式的证据或凭据。涉及法律、医疗、财务、人事等重大事项时，请以人工核对为准。
4. 软件按「现状」提供，作者不对使用后果承担任何责任。
5. 程序不联网、不上传、不写注册表、不收集任何使用数据。

---

## 授权与署名（重要）

本项目以 **MIT License** 发布，可自由使用、修改、分发、商业使用。全文见 [LICENSE](LICENSE)。

**但署名必须一直保留。** 按 MIT 许可的强制要求，任何使用、复制、修改、合并、发布、
分发、再许可或销售本软件及其副本的行为，都必须：

1. 保留 `LICENSE` 与 [`NOTICE`](NOTICE) 中的版权声明；
2. 保留作者署名 **永远的兰兰 / Lanlan Eternal**；
3. **不得**声称原作品由自己创作。

修改后的版本可以署你自己的名字，但**必须同时保留原作者的版权声明**——
这是许可条件，不是请求。fork 或二次开发请在 README 或「关于」页保留一行：

```
基于 言札 YanZha © 永远的兰兰 (Lanlan Eternal)
https://github.com/podcatcher962/YanZha
```

### 第三方组件与模型

代码是 MIT，但**模型和 FFmpeg 各有自己的许可**，随包分发须遵守：

| 组件 | 许可 | 要点 |
|---|---|---|
| SenseVoice Small（识别模型） | **FunASR Model License v1.1** © Alibaba | 必须注明出处与作者、**保留模型名称** |
| silero-vad（语音检测） | MIT | 保留声明 |
| CAM++ / 3D-Speaker（声纹） | Apache-2.0 | 保留声明 |
| sherpa-onnx / pywebview / python-docx | Apache-2.0 / BSD-3 / MIT | 保留声明 |
| FFmpeg（解码） | LGPL / GPL | 仅调用其可执行文件，按 GPL 分发 |

识别模型是**开源可商用**的（FunASR 自有许可，非 OSI 标准但允许使用、修改、分发），
条件就是署名与保留模型名——本项目已在上文、[`NOTICE`](NOTICE)、
[`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md)、
[`licenses/FunASR-MODEL-LICENSE.txt`](licenses/FunASR-MODEL-LICENSE.txt)
以及程序「关于」页五处一并保留。逐条对照见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。

---

<a id="english"></a>
## English

### What it is

A fully offline audio/video-to-text tool for Windows. Audio never leaves the
machine — there is no networking code in the program at all. No account,
no time limit, no cost.

About **3 minutes per hour** of audio on an ordinary laptop, CPU only,
no GPU required.

### Features

| | |
|---|---|
| **5 languages** | Chinese, English, Japanese, Korean, Cantonese — auto-detected, no manual switch; mixed zh/en in one file works |
| **Speaker diarization** | Splits multi-speaker podcasts/interviews by person, labelled "Speaker 1 / 2 / 3"; automatically removed for single-speaker files |
| **Rename speakers** | Click "Speaker 1" → rename to "Host" / "Guest"; applies to every export format |
| **7 export formats** | txt / md / Word / srt / vtt / timestamped txt / structured json |
| **Audio + video input** | mp3 m4a wav flac aac ogg opus wma; mp4 mkv mov avi flv webm ts m4v |
| **Punctuation & paragraphs** | Built into the model — real sentences, not one unreadable wall of text |
| **Word-level timestamps** | Subtitles precise enough for Premiere / Final Cut / Bilibili |
| **Resumable** | Live progress, stop anytime; toggling diarization does not re-run recognition |

### Quick start

1. Run `YanZha.exe` (keep `models/` and `ffmpeg.exe` beside it)
2. "添加音视频文件" (Add files) — or drag files into the window
3. "开始转写" (Start) — wait for the progress bar
4. Click a file on the left, the transcript appears on the right; export as needed

### Performance (measured, not estimated)

| | |
|---|---|
| Real-time factor | **0.026 – 0.047** (53.6 s audio → 2.96 s transcript) |
| One hour of audio | ≈ 2.8 – 3.3 minutes |
| Diarization overhead | ≈ 32 ms per sentence (84 s two-speaker clip → 3 s) |
| Model load | 1.4 s |
| Cold start | 2 – 3 s |

### Privacy

- Audio is processed **locally only** — nothing is uploaded
- No telemetry, no analytics, no update check, no network code
- No service installed, no registry writes, no system settings changed
- Works with the network cable unplugged

### Requirements

- Windows 10 / 11 (64-bit)
- 4 GB RAM (8 GB recommended for long recordings)
- ~400 MB disk (program 42 MB + models 256 MB + decoder 79 MB)

### Build from source

```bash
pip install sherpa-onnx pywebview python-docx pyinstaller
python build.py
```

Models are not in the repo (size). Download from
[sherpa-onnx releases](https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models):

| Path | Files |
|---|---|
| `models/asr/` | `model.int8.onnx` + `tokens.txt` from `sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17` |
| `models/vad/` | `silero_vad.onnx` |
| `models/speaker/` | `campplus.onnx` |

### License & attribution

Released under the **MIT License** — free to use, modify and redistribute,
including commercially. **Attribution must be preserved** (MIT requires it):
keep the copyright notice and the author credit
**永远的兰兰 / Lanlan Eternal**, and do not claim the original work as yours.
Derivative works may carry your own name but must also retain the original
notice. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

The bundled **SenseVoice Small** recognition model is distributed under the
**FunASR Model License v1.1** (© Alibaba Group), which permits use,
modification and redistribution on condition that the source, author
information and **model name** are retained. See
[`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md) for the clause-by-clause
compliance table and [`licenses/`](licenses/) for the full text.

### Disclaimer

1. This is a **local transcription tool**. It processes only the audio/video
   files you provide. It does **not** provide any service for obtaining,
   downloading, searching or distributing audio, video or text content.
2. You must own the rights to the media you process, or have the rightsholder's
   permission. Any dispute arising from the content's origin is the user's
   responsibility.
3. Transcripts are machine-generated and **may contain errors**. They are not
   evidence of any kind. For legal, medical, financial or HR matters, verify
   manually.
4. Provided "as is", without warranty of any kind.
5. The program makes no network requests and collects no usage data.

---

**© 永远的兰兰 · Lanlan Eternal**

仓库 / Repository：https://github.com/podcatcher962/YanZha
版本 / Version：v0.3.0 · 2026-11-15
