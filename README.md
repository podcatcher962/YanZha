# 言札 · YanZha

**v0.5.0** · 2026-11-16

把录音、播客、会议、视频，变成能直接用的文字稿。

**不上传、不联网、不要账号、不限时长、不花钱。**

Windows 10/11 64 位 · 单文件程序 + 本地模型 · MIT 开源

> 仓库地址：**https://github.com/podcatcher962/YanZha**
> 作者：**永远的兰兰（Lanlan Eternal）**
> 下载：**[Releases](https://github.com/podcatcher962/YanZha/releases)**

*Turn recordings, podcasts, meetings and videos into usable transcripts.
Fully offline — nothing uploaded, no account, no time limit, free.
Five languages auto-detected (Chinese / English / Japanese / Korean /
Cantonese), speaker diarization, glossary, 7 export formats. Windows x64, MIT.*
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
| **查找替换** | 一个错词满篇都是：「替」→ 填正确的词 →「全部替换」一次改完，`Ctrl+Z` 整批退回；替换框留空即删掉这个词 |
| **术语表** | 同一个人名、书名、公司名，在同一个人的每一期里都错成同一样子。右上角「术语表」填左右两栏（左＝错的词，右＝改成什么），**不用敲箭头**，转完自动改掉；改错了 `Ctrl+Z` 整批退回。更省事：在稿子上用「替」改对后勾上替换条里的**「记住」**，这条替换自动进表 |
| **稿子不会丢** | 改到一半直接关程序也不丢：改完随时存一份本机草稿（不上传、不进源文件夹），下次打开左栏提示「有 N 份没导出的稿子」，点一下接着改 |
| **导出前检查** | 点导出时先扫一遍，只报**根本没人说过的**东西：只剩标点的空壳句、（音乐）（掌声）这类标注、同一段被识别两遍（按时间戳重叠判定）。句子长短、口头重复一概不管——不改也能照样导；真没问题就不弹窗 |
| **七种导出** | txt / md / Word / srt / vtt / 带时间戳 txt / 结构化 json |
| **批量导出** | 一次转了十个文件，选一个文件夹按同一种格式全部导出；撞名不覆盖，自动加 `-2` |
| **音视频通吃** | 音频 mp3 m4a wav flac aac ogg opus wma；视频 mp4 mkv mov avi flv webm ts m4v |
| **自动标点断句** | 模型自带标点，按句整理成段，不是一坨没有标点的流水 |
| **逐字时间戳** | 字幕能精确到每一句的起止，导入剪映、Premiere、B 站 |
| **字幕自动折行** | srt / vtt 里一句太长会断成两行，剪映里不溢屏 |
| **可中断** | 进度实时、还剩几分钟也一起算给你；随时能停；改「区分说话人」勾选不用重跑识别 |

---

## 怎么用

1. 双击 `YanZha.exe`
2. 点「添加音视频文件」，或把文件拖进窗口，选一个或一批
3. 点「开始转写」，等进度条走完
4. 点左边转好的文件，右边就是稿子
5. **双击任意一句听原音**，点句子右边的「改」就地改字（回车保存、清空即删句、`Ctrl+Z` 撤销）
6. 同一个错词出现很多次：搜索框输进去，点右边的**「替」**→ 填上正确的词 →「全部替换」，`Ctrl+Z` 整批退回
7. 点说话人名字可以改成「主持人」「嘉宾」；点「导出」时会先扫一遍「不是你或对方说出来的东西」，改不改都照导
8. 同一批录音老在那几个词上出错：右上角**「术语表」**填两栏（左＝转写里错的词，右＝改成什么），不用敲箭头，往后每期转完自动改

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
| 导出前检查 | 2000 句的稿子 **30 ms**；一次全部替换 414 句 **27 ms**，`Ctrl+Z` 整批退回 **<1 ms** |

### 为什么「可疑句提醒」只留三类

言札只做一件事：**把录音里那个人说过的话，一字不差地变成字**。

所以「一句话说 50 字」「同一个词连说三遍」「嗯…那个…然后绕回来又讲一遍」都不是错误——
那个人当时就是这么说的，改掉他就不像他了。按长度或重复报警，在一份千句的两人对话里
刷出 94 条，全是完全正常的普通话长句，用户直接把弹窗关掉。

现在只报**客观上没人说过的**东西：

| 类型 | 为什么算错 |
|---|---|
| 整句只剩标点 | 人不会「说」一个句号 |
| （音乐）（掌声）这类标注 | 是识别器自己写进去的，不是谁说的话 |
| 同一段被识别两遍 | 唯一硬证据是**时间戳重叠**——人不可能同时说两段话 |

第三类值得单说：文本完全相同的两句，如果**各占各的时间段**（比如 `6.26→9.02` 和
`20.24→23.00`，各 2.76 秒），说明音频里人真的说了两遍，**一个字都不报**。
这是拿真实录音验出来的形态，早先按「文本相同」判重复，把它冤枉成识别错误了。

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

### 在 macOS / Linux 上跑源码

没有 macOS / Linux 安装包，短期也不打算做：PyInstaller 不能交叉编译，macOS 不签名会被
Gatekeeper 拦（签名要 99 美元/年），Linux 每个发行版的窗口库还得各验一遍——现在的下载量
撑不起这份维护成本。

但**源码本身是能跑的**：界面、识别、说话人、七种导出都一样，只是窗口换成系统自带的 WebView。

```bash
# 1) Python 依赖
python3 -m pip install -r requirements.txt

# 2) 系统依赖
#    macOS —— pywebview 用系统自带的 WKWebView，不用额外装东西
brew install ffmpeg
#    Linux（Debian / Ubuntu 系）—— pywebview 必须显式选一个窗口后端
sudo apt install ffmpeg python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
python3 -m pip install "pywebview[gtk]"

# 3) 模型（约 256 MB，放进仓库根的 models/）
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
tar xf sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
mkdir -p models/asr models/vad models/speaker
cp sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/model.int8.onnx models/asr/
cp sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/tokens.txt models/asr/
curl -L -o models/vad/silero_vad.onnx \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
curl -L -o models/speaker/campplus.onnx \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_campplus_sv_zh_en_16k-common_advanced.onnx

# 4) 跑
python3 yanzha_ui.py
```

两处 Windows 专属的东西会自己退让，**不用改代码**：

- **文件对话框**：Windows 上用原生 comdlg32（为了不弹到主窗口后面），其他系统自动退回
  pywebview 自带的对话框
- **深色标题栏**：只有 Windows 会去调 `DwmSetWindowAttribute`，其他系统保持系统默认

**坦白一句**：我手上只有 Windows 机器，这条路没在真机上验过。能跑起来最好，跑不起来欢迎开 issue。

国产系统（麒麟 V10 / 统信 UOS）走的就是 Linux 这条路：x86_64 和飞腾、鲲鹏的 aarch64 都有
官方 onnxruntime 轮子；**龙芯 LoongArch 没有轮子**，得自己编 onnxruntime，不值当。

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
pip install -r requirements.txt pyinstaller
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
| **Proofreading** | Double-click any line to hear that moment, edit in place, clear a line to drop it, `Ctrl+Z` to undo |
| **Find & replace** | One misheard word appearing everywhere: hit "替", type the right one, "全部替换" — the whole batch reverts with one `Ctrl+Z`; leave the box empty to delete that word |
| **Export check** | Before exporting it lists only things **nobody actually said**: punctuation-only lines, `(music)` / `(applause)` tags written into the text, and the same span decoded twice (proven by overlapping timestamps). Sentence length, stutters and verbal tics are never flagged — export as it is, and you are not interrupted when there is nothing to report |
| **Glossary** | The same name is misheard the same way in every episode. Open 术语表 (glossary): fill the left column with the wrong word and the right column with the correct one — no arrow typing needed (the → key does not exist on most keyboards). Applied automatically after each run; one `Ctrl+Z` reverts the whole batch |
| **Nothing gets lost** | Edit for an hour and close the app — it is fine. Each edit is saved to a local draft (never uploaded, never written beside your source files); next launch the sidebar offers "N drafts not exported yet" |
| **7 export formats** | txt / md / Word / srt / vtt / timestamped txt / structured json |
| **Batch export** | Ten finished files, pick one folder, export them all in one format; existing names are never overwritten (`-2` is appended) |
| **Audio + video input** | mp3 m4a wav flac aac ogg opus wma; mp4 mkv mov avi flv webm ts m4v |
| **Punctuation & paragraphs** | Built into the model — real sentences, not one unreadable wall of text |
| **Word-level timestamps** | Subtitles precise enough for Premiere / Final Cut / Bilibili |
| **Resumable** | Live progress with an estimated time remaining, stop anytime; toggling diarization does not re-run recognition |

### Quick start

1. Run `YanZha.exe` (keep `models/` and `ffmpeg.exe` beside it)
2. "添加音视频文件" (Add files) — or drag files into the window
3. "开始转写" (Start) — wait for the progress bar
4. Click a file on the left, the transcript appears on the right; export as needed
5. Double-click a line to hear it; hit "改" to edit in place (Enter saves, clearing the line drops it, `Ctrl+Z` undoes)
6. Same word wrong throughout: type it in the search box, hit **"替"**, type the correct one, **"全部替换"** — one `Ctrl+Z` reverts the whole batch
7. Exporting first scans for suspicious lines and lists them; you can export anyway
8. Same words wrong every episode: open **术语表** (glossary, top right) and fill the two columns — wrong word on the left, correct one on the right (no arrow typing)

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
pip install -r requirements.txt pyinstaller
python build.py
```

Models are not in the repo (size). Download from
[sherpa-onnx releases](https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models):

| Path | Files |
|---|---|
| `models/asr/` | `model.int8.onnx` + `tokens.txt` from `sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17` |
| `models/vad/` | `silero_vad.onnx` |
| `models/speaker/` | `campplus.onnx` |

### Running from source on macOS / Linux

There is no macOS / Linux build and none is planned: PyInstaller cannot cross-compile, an
unsigned macOS app is blocked by Gatekeeper (codesigning is $99/year), and every Linux
distribution needs its own windowing stack verified — the current download numbers do not
justify that maintenance.

The source itself does run: same UI, same recognition, same seven export formats.

```bash
python3 -m pip install -r requirements.txt
brew install ffmpeg                       # macOS — pywebview uses the built-in WKWebView
sudo apt install ffmpeg python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1   # Debian/Ubuntu
python3 -m pip install "pywebview[gtk]"   # Linux only — a backend must be chosen explicitly
# put the models under models/ (table above), then:
python3 yanzha_ui.py
```

Two Windows-only pieces step aside automatically: the native file dialogs (comdlg32) fall back
to pywebview's own, and the dark title bar simply does nothing outside Windows.

Caveat: these paths were **not** verified on real hardware — there is only a Windows machine here.

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
版本 / Version：v0.5.0 · 2026-11-16
