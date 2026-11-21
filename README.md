# 言札 · YanZha

**v0.7.0** · 2026-11-21

把录音、播客、会议、视频，变成能直接用的文字稿。

**不上传、不联网、不要账号、不限时长、不花钱。**

Windows 10/11 64 位 · 单文件程序 + 本地模型 · MIT 开源

> 仓库地址：**https://github.com/podcatcher962/YanZha**
> 作者：**永远的兰兰（Lanlan Eternal）**
> 下载：**[Releases](https://github.com/podcatcher962/YanZha/releases)**

*Turn recordings, podcasts, meetings and videos into usable transcripts.
Fully offline — nothing uploaded, no account, no time limit, free.
Five languages auto-detected (Chinese / English / Japanese / Korean /
Cantonese), speaker diarization, glossary, 8 export formats. Windows x64, MIT.*
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
| **区分说话人** | 多人播客/访谈按人分段，标「说话人 1 / 2 / 3」；单人录音自动去掉标注；知道总人数可以指定（1 就是单人），改人数只重跑分人 |
| **亮色主题** | 顶栏一点就切「☀ 亮色」，纸白底加深字，白天、投影、屏幕偏暗的笔记本上更好认；暗色下本来就偏灰的时间码、状态行也一起提亮了。选择记在本机，下次打开照旧 |
| **语种锁定** | 默认锁中文。中文录音在底噪、笑声、远场混响上容易猜成日文/韩文，锁上以后可疑段用中文重认、残留的假名谚文清掉；录外语就切「自动 · 中英日韩粤」 |
| **按人数分人** | 知道自己录的是几个人（1~6，1 就是单人）就选上，按人数硬分，比自动判更准；改人数只重跑分人，不重新识别。自动分出 4 人以上时，结果上方会直接问「这段其实几个人」，点一下就重分 |
| **说话人改名** | 点一下「说话人 1」改成「主持人」「嘉宾」，导出全部格式跟着变 |
| **断句 / 并句 / 换人** | 一句里其实是两个人在说？点「断」，光标放到分开的地方切开，后半句顺手指定是谁；识别器把一句话切碎了就点「并」接回去；整句归错人，点句尾的小标只改这一句 |
| **校对改字** | 双击句子听原音，就地改字、删句、撤销，改完直接导出 |
| **查找替换** | 一个错词满篇都是：「替」→ 填正确的词 →「全部替换」一次改完，`Ctrl+Z` 整批退回；替换框留空即删掉这个词 |
| **术语表** | 同一个人名、书名、公司名，在同一个人的每一期里都错成同一样子。右上角「术语表」填左右两栏（左＝错的词，右＝改成什么），**不用敲箭头**，转完自动改掉；改错了 `Ctrl+Z` 整批退回。更省事：在稿子上用「替」改对后勾上替换条里的**「记住」**，这条替换自动进表 |
| **读音校对** | 只知道正确写法的字（"张小燕"不知道被写成啥），只写对的就行：软件按**拼音**去稿子里找读音对得上、字却不一样的地方，列成清单逐条勾选，`an/ang`、`z/zh`、`l/n` 这类口音差异也认。**不勾就不改一个字** |
| **稿子不会丢** | 改到一半直接关程序也不丢：改完随时存一份本机草稿（不上传、不进源文件夹），下次打开左栏提示「有 N 份没导出的稿子」，点一下接着改 |
| **导出前检查** | 点导出时先扫一遍，只报**根本没人说过的**东西：只剩标点的空壳句、（音乐）（掌声）这类标注、同一段被识别两遍（按时间戳重叠判定）。句子长短、口头重复一概不管——不改也能照样导；真没问题就不弹窗 |
| **八种导出** | txt / md / Word / srt / vtt / 带时间戳 txt / 结构化 json / 校对稿 |
| **拿出去改再粘回来** | 「导出 → 校对稿」存一份一行一句、行首带编号的 txt，拿给任何工具改；改完「导出 → 粘贴改好的稿子」把整篇贴回来，按编号逐句落回，时间戳和说话人都保留。删了编号的行跳过，其余照常回填；程序全程不联网，稿子出不出这台电脑由你决定 |
| **批量导出** | 一次转了十个文件，选一个文件夹按同一种格式全部导出；撞名不覆盖，自动加 `-2` |
| **音视频通吃** | 音频 mp3 m4a wav flac aac ogg opus wma；视频 mp4 mkv mov avi flv webm ts m4v |
| **自动标点断句** | 模型自带标点，按句整理成段，不是一坨没有标点的流水 |
| **逐字时间戳** | 字幕能精确到每一句的起止，导入剪映、Premiere、B 站 |
| **字幕自动折行** | srt / vtt 里一句太长会断成两行，剪映里不溢屏 |
| **可中断** | 进度实时、还剩几分钟也一起算给你；随时能停；改「区分说话人」勾选不用重跑识别 |

---

## v0.7.0 改了什么（实测过的）

来自一位拿言札转访谈的用户：**分人分错了，只能整组改名，改不了单句**。
更麻烦的是有些句子其实是两个人抢话，识别器把两句话并成了一句 ——
这一行里既有 A 也有 B，可句尾只挂得下一个说话人，怎么改都是错的。

**① 单句换人** — 鼠标移到任意一句，右下角出现「讲1 改 断 并」。
点前面那个小标就是「这一句是谁说的」：列出稿子里已有的说话人，点一下就换；
也可以现写一个新称呼（主持人 / 嘉宾 / 旁白）。**只动这一句**，同一组里别的句子不动。
整组改名还是点稿子左边的小标题。

**② 断句** — 点「断」，这一句摊在框里，光标放到要分开的地方，
下面实时显示「前 8 字（00:00 → 00:01）　后 9 字（00:01 → 00:02）」，
后半句还能顺手指定给另一个人。点「切开」，一行变两行、各归各人。

时间怎么分：句子里没有「每个字的时间」，声纹也只在句级，所以切点按**字数比例**插值。
字幕会有半秒上下的偏差 —— 比整句归错人强。

**③ 并句** — 识别器把一句话切碎了（「前半句，」「后半句。」），点「并」和下一句接起来。
两句不同人时按前一句算，状态栏会说明。

**撤销照旧**：换人、断句、并句都进同一个撤销栈，`Ctrl+Z` 一路退回去；
断句时顺手改的错字算同一步，不用按两次。

**本版实测**：

| 项目 | 结果 |
|---|---|
| 逻辑单测 `tools/test_yanzha_v070.py` | **125 项全过**：切点边界、时间插值、撤销、raw 同步、200 句拆 60 次再并回 |
| 界面冒烟 `_video/test_ui_v070.py`（真实 84 秒双人对话） | **29 项全过**：按钮 → 弹窗 → 后端 → 重绘整条线，截 7 张图 |
| 旧回归（v0.4 改字 / v0.5 术语与草稿） | **119 项全过**，改字、替换、草稿、导出没受影响 |
| 拆并往返 | 200 句稿子拆 60 次再并回，字数、说话人、时间三样全对得上 |

**一个必须说清的取舍**：断句会同步改 `raw`（重跑分人用的底稿，不改的话拆出来的行会被吞掉），
但**手动指定的说话人在重跑分人后会被重算** —— 那是"整批重新聚类"，本来就会推翻上一次的结果。
真发生了，状态栏会写「手动改的 N 句人已按新结果重算」，不闷着。

## v0.6.2 改了什么（实测过的）

这条还是接着上面那位用户：他要「能自动改错字的 AI」，又说不出错成什么样——
真实情况是他只知道**"张小燕"这三个字怎么写**，不知道模型写成"张晓燕"还是"张小艳"。
术语表要求先填"错的样子"，这一步他填不出来。

**新增「读音校对」** — 右上角一个按钮。这次**只写正确的写法**，一行一个：

```
张小燕
同济路
嘉立创
```

点「看看会改哪儿」，软件把稿子里**读音对得上、字却不一样**的地方全找出来，
一条条列成「第 8 句 张晓燕 → 张小燕（同音 1.00）」，逐条勾选，
点「改勾选的」才动——**默认一个字都不改**，也不会背着你改。
改完一次 `Ctrl+Z` 整批退回，草稿同步回退。

近音也认：`an/ang`、`z/zh`、`l/n`、前后鼻音这类口音差异按权重降分，不直接判死。
实测「桶吉路 → 同济路」相似度 0.91 也能命中。

**本版实测**（脚本 `_tmp/test_terms.py`、`_tmp/test_harm.py`、`_tmp/test_speed.py`）：

| 项目 | 结果 |
|---|---|
| 注入 4 处错字（同音/近音混合） | **4 处全中**，同音 1.00、近音 0.98 / 0.91 |
| 误伤压力测试（10 个常用词 + 168 个三字片段扫真实稿） | **0 处误改** |
| 扫描速度 | 一万字 **0.41 秒**（一小时录音约一万字，等于没耗时） |
| 安装包增量 | 43,788,405 → 44,641,122 B，**+852 KB（+1.9%）** |
| 真稿验证 | 53.6 秒真实录音转写稿，未加词表时零改动 |

**为什么不做「AI 自动润色」** — 试过了，数据不支持。市面上最贴这件事的开源模型是
`shibing624/macbert4csc-base-chinese`（110M，专修同音形近字）。实测 int8 版：
真实稿子上**只抓对 1 处**（"演都"→"演得"），**还改错 1 处**（"他的"→"她的"）。
体积代价却是 **+206 MB**（42.6 → 239 MiB），因为 onnxruntime 自己就吃掉一百多兆。
更关键的是它没有"这个位置到底有没有错"的检测头，只能靠概率门控硬压，
压到不误伤的时候，真错也基本抓不到了。

词表这条路没有这些问题：**纯本地、零幻觉、毫秒级、可解释**——改了就是改了，
没写进表里就一个字不动，出了问题能查出是哪条规则干的。

> 读音校对只解决"读音对、字写错"。意思写错但读音也对的（"守法"其实是"犯法"），
> 软件不猜，必须人来判断——这条也写进了使用说明。

## v0.6.1 改了什么（实测过的）

这条是按用户反馈改的：两人通话被分成了 8 个人，还想把稿子拿给 AI 改。

**① 分多了，程序自己会问** — 自动模式分出 4 人以上时，稿子上方直接出一句
「自动分出 5 个人？这段其实几个人」，两个按钮：「只有 1 个人」「是 2 人」。
点了只重跑分人，**不重新识别，你手改过的字一个不动**。
实测一段 14 句的独白（真实单人录音）被自动切成 5 个人（簇 5/4/2/2/1）；
点「只有 1 个人」后 0.8 秒变单人、标注全部清空，先前手改的那句仍在原处。

**② 人数下拉补了「1 人」** — 原来只有 2~6，单人录音只能靠关掉「区分说话人」。
现在有「1 人（单人）」，按 1 个簇硬分，标注直接清掉。

**③ 稿子能拿出去改，也能拿回来** — 新增「导出 → 校对稿」：一行一句、
行首带编号、**不带时间戳**（不干扰 AI 读），扔给任何工具改都行。
改完「导出 → 粘贴改好的稿子」贴回来，按编号逐句落回，时间轴和说话人全留着。
编号被弄丢的行只跳过那几行，其余照常回填；文字被清空的行按跳过处理（防手滑丢句）；
整批算一次 `Ctrl+Z`。导出因此从七种变**八种**。

> 为什么不内置 AI 接口：录音稿多是访谈、通话，传出去就是隐私问题，出事得我们担。
> 程序自己不上传，改成「你拿出去、改好贴回来」，这条也写进了使用说明。

## v0.6.0 改了什么（实测过的）

这一版是按用户反馈改的，四件事。

**① 太黑了，看不见** — 顶栏加了「☀ 亮色 / ☾ 暗色」，一点就换，选择存在本机。
顺手把暗色里偏灰的字提亮了：时间码、状态行这类次要文字原来对比度只有 3.2:1，
现在 5.4:1（WCAG AA 对正文要求 4.5:1）。界面里 57 种颜色全部收进 CSS 变量，
切主题只切一块，不会再出现"切了亮色还剩一块黑的"。

**② 转录里冒出日语、韩语，而我全是中文** — 模型自带一个语种判别头，遇到底噪、
笑声、远场混响这类"不太像话"的片段会乱猜语种，中文录音里就蹦出平假名和谚文。
现在默认**锁中文**：整个文件按中文解码，再把残留的假名、谚文清掉。
实测三份远场样片：自动模式分别冒出 2 / 0 / 4 个日韩字，锁中文后全是 0；
两份结果的字级相似度 0.76~0.86，差的只是被纠正的那几处。
中英混说照旧——"Today is Tuesday" 在锁定模式下照样出来。
录的是外语、或真要日韩语混说，把「语种」切到「自动」即可。

**③ 多人说话，一直只分出两个人** — 查下来是两个独立的毛病，都修了：

*其一，声音小的人会被整段丢掉。* VAD（判断"这段是不是人在说话"）的门槛是
silero 的默认 0.5，对手机录音偏高。同一段 5 人录音里，最轻的那位只有 **4~7%**
的话被切出来 —— 等于这个人在稿子里根本不存在，剩下的自然就是声音最大的两个人。
把门槛降到 0.40（最短语音 0.30→0.25 秒）后，同一位的覆盖率升到 **53~89%**，
那份样本从 0 句变成 6 句，整体语音覆盖从 55% 升到 73%，碎句（≤3 字）没有变多。

*其二，聚类的合并条件太松。* 原来逐句提声纹（一句话常常只有一两秒，声纹本身就抖），
再用固定 0.62 的相似度合并 —— 远场混响会把**不同人**的声纹相似度抬到 0.5~0.6，
0.62 正好落在这条缝里，一屋子人被并成两三个人。现在：

- 按"提声纹的单位"提，碎句跟前一句粘起来，长句自己一个（不粘，免得把两个人的话
  混进同一段声纹）
- 换成分层聚类（sherpa-onnx 的 FastClustering）
- 合并阈值提到 **0.78**：宁可多分一个人（点一下就能改名），也不把两个人糊成一个，
  糊在一起是改不回来、重跑也还是糊的
- 占比不足 2% 的小簇不再一律并进大簇，且必须"很像"才并 —— 全程只说了三句话的人
  也是一位说话人
- 句子级再对一次质心，处理"一个人说完另一个马上接、中间没静音"的情况

实测 5 人远场样片（20 dB / RT60 0.35 / 正常换人间隔）：自动分出 **5 人，纯度 100%**。

*顺带加了个「人数」下拉*：你清楚知道自己录的是几个人，就选上（1~6 人，1 就是单人），
按人数硬分。同一个样本指定 5 人 → **5 人、纯度 100%**。已经转好的稿子改一下人数
再点「开始转写」，**只重跑分人**（几秒），不重新识别。

**④ 识别不准** — 手机录音常常整段偏小。解码后做去直流 + 峰值归一，峰值本来就够的
样本一个采样都不动。实测：衰减 20 dB 的样片归一后峰值回到 0.85；干净样本归一前后
逐字一致。

这一版两套自测全绿：**引擎 20 项**（音量归一 4、语种清理 6、整份文件锁语种 4、多人分人 5、
单人录音 1）、**界面 36 项**（颜色变量化、两套主题的对比度、控件接线、语种判据）。

> 手上没有反馈里那份手机录音，上面的数字是在「5 个真人声 + 混响 + 底噪」的远场
> 合成样本上量的。真实录音受重叠、抢话、底噪影响，分得准不准仍要看素材；
> 分不准时先动「人数」下拉 —— 比自动判靠得住。

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
- 左下角 **「人数」** 默认自动。自动分人最常出的错是「明明四五个人，只分出两个」——远场录音里不同人的声纹会互相靠拢，硬阈值一裁就裁掉了。你清楚知道自己录的是几个人，就选上（1 到 6 人，1 就是单人），**按人数硬分，比任何自动判据都准**
- 分人的取舍是**宁可多分一个人，也不把两个人糊成一个**：糊在一起改不回来，重跑一遍还是糊的；多出来的人点一下就能改名
- 声音重叠、抢话、笑声多的时候，分人仍然可能有偏差，这是这类技术的通病；这时指定人数比自动稳得多

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

但**源码本身是能跑的**：界面、识别、说话人、八种导出都一样，只是窗口换成系统自带的 WebView。

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
| **Light theme** | One click on "☀ 亮色" in the header — warm paper background plus dark text, easier in daylight, on projectors and on dim laptop screens. The dimmest text in dark mode was lifted too. The choice is remembered locally |
| **Language lock** | Chinese is locked by default: on noise, laughter and far-field reverb the tagger sometimes guesses Japanese or Korean for Chinese audio. Suspicious segments are re-decoded as Chinese and leftover kana/hangul removed. Switch the "语种" dropdown to "自动 · 中英日韩粤" to let the model decide again |
| **Fixed speaker count** | If you know how many people are in the recording (1–6, 1 = solo), pick it and clustering is forced to that count — far more reliable than automatic. Changing the count re-runs diarization only, never recognition |
| **Rename speakers** | Click "Speaker 1" → rename to "Host" / "Guest"; applies to every export format |
| **Proofreading** | Double-click any line to hear that moment, edit in place, clear a line to drop it, `Ctrl+Z` to undo |
| **Find & replace** | One misheard word appearing everywhere: hit "替", type the right one, "全部替换" — the whole batch reverts with one `Ctrl+Z`; leave the box empty to delete that word |
| **Export check** | Before exporting it lists only things **nobody actually said**: punctuation-only lines, `(music)` / `(applause)` tags written into the text, and the same span decoded twice (proven by overlapping timestamps). Sentence length, stutters and verbal tics are never flagged — export as it is, and you are not interrupted when there is nothing to report |
| **Glossary** | The same name is misheard the same way in every episode. Open 术语表 (glossary): fill the left column with the wrong word and the right column with the correct one — no arrow typing needed (the → key does not exist on most keyboards). Applied automatically after each run; one `Ctrl+Z` reverts the whole batch |
| **Reading-match proofreading** | When you only know how a name is *spelled* (but not how the model mangled it), write just the correct form: the app matches by **pinyin** and lists every spot whose reading matches but whose characters differ. Accent pairs like `an/ang`, `z/zh`, `l/n` are tolerated. Nothing changes unless you tick it |
| **Nothing gets lost** | Edit for an hour and close the app — it is fine. Each edit is saved to a local draft (never uploaded, never written beside your source files); next launch the sidebar offers "N drafts not exported yet" |
| **8 export formats** | txt / md / Word / srt / vtt / timestamped txt / structured json / proof copy |
| **Batch export** | Ten finished files, pick one folder, export them all in one format; existing names are never overwritten (`-2` is appended) |
| **Audio + video input** | mp3 m4a wav flac aac ogg opus wma; mp4 mkv mov avi flv webm ts m4v |
| **Punctuation & paragraphs** | Built into the model — real sentences, not one unreadable wall of text |
| **Word-level timestamps** | Subtitles precise enough for Premiere / Final Cut / Bilibili |
| **Resumable** | Live progress with an estimated time remaining, stop anytime; toggling diarization does not re-run recognition |

### v0.7.0 — what changed (measured)

From a user transcribing interviews: **the speaker is wrong and there is no way to fix
a single line** — renaming only works for a whole speaker. Worse, some lines are two
people talking at once: the recognizer merged two utterances into one, so the line holds
both A and B while only one speaker can be attached to it.

**① Reassign one line.** Hover any sentence and a small bar appears at its lower right:
「讲1 改 断 并」. Click the badge to say *who said this line* — pick an existing speaker
or type a new label. **Only that line changes**; the rest of the group stays put.

**② Split a line.** Click 「断」, put the caret where the two speakers meet, and the dialog
previews "first 8 chars (00:00 → 00:01), last 9 chars (00:01 → 00:02)" live. The second
half can be assigned to another speaker in the same step.

Timing is interpolated **by character count**: there is no per-character timestamp, and
speaker embedding is sentence-level. Subtitles can be off by half a second — better than
attributing the whole line to the wrong person.

**③ Merge two lines.** When the recognizer cut one sentence in half, click 「并」 to join
the next line. If the two belong to different speakers, the first one wins and the status
bar says so.

Undo is unchanged: reassign, split and merge share the same undo stack, and text edited
inside the split dialog is reverted in the same step.

**Measured this release:** 125 logic assertions (`tools/test_yanzha_v070.py`), 29 UI
assertions driven through the real window with an 84-second two-speaker recording, and
the two older suites (119 assertions) still green.

### v0.6.2 — what changed (measured)

Same user as above. He wanted "an AI that fixes the typos", but could not say how they
were misspelled — what he actually knows is how **"张小燕" is written**, not whether the
model produced "张晓燕" or "张小艳". The existing glossary needs the *wrong* form typed in
first, and that is exactly the part he cannot supply.

**New: reading-match proofreading (读音校对).** One button in the header. This time you
write **only the correct forms**, one per line:

```
张小燕
同济路
嘉立创
```

Click "看看会改哪儿" and every place in the transcript whose **pronunciation matches but
whose characters differ** is listed as "line 8: 张晓燕 → 张小燕 (homophone 1.00)". Tick the
ones you want, then confirm — **nothing is changed by default**, and it never edits behind
your back. One `Ctrl+Z` reverts the batch together with the draft.

Near-homophones are accepted too: `an/ang`, `z/zh`, `l/n` and front/back nasal pairs are
scored with a weight rather than rejected outright — "桶吉路 → 同济路" was caught at 0.91.

**What was actually tested** (`_tmp/test_terms.py`, `_tmp/test_harm.py`, `_tmp/test_speed.py`):

| Item | Result |
|---|---|
| 4 injected typos (homophone + near-homophone) | **All 4 caught** — 1.00, 0.98, 0.91 |
| False-positive stress test (10 common words + 168 three-char fragments over a real transcript) | **0 wrong edits** |
| Scanning speed | 10,000 characters in **0.41 s** (an hour of speech is roughly that, i.e. no perceptible cost) |
| Installer growth | 43,788,405 → 44,641,122 bytes, **+852 KB (+1.9%)** |
| Real transcript | no word list attached → zero changes, as expected |

**Why there is no "AI polishing".** It was measured, and the numbers did not support it.
The closest open model is `shibing624/macbert4csc-base-chinese` (110M, tuned for
homophone/shape errors). On a real transcript its int8 export **caught exactly 1 real typo**
("演都"→"演得") and **introduced 1 new error** ("他的"→"她的"). The size cost was **+206 MB**
(42.6 → 239 MiB) because onnxruntime alone is over a hundred megabytes. It also has no
"is this position wrong?" detection head, so it can only be gated by probabilities — and
once gated hard enough to stop the false edits, it stops finding the real ones too.

A word list has none of these problems: **fully local, zero hallucination, millisecond
fast, explainable** — a change is a change, nothing outside the list is touched, and any
result can be traced to one rule.

> Reading-match proofreading only fixes "right sound, wrong character". Errors that read
> correctly but mean the wrong thing ("守法" where "犯法" was said) are left alone — the
> software does not guess meaning.

### v0.6.1 — what changed (measured)

Reported by a user: a two-person call came back as **eight speakers**.

- **The app now asks when it over-splits.** If automatic diarization finds four or
  more speakers, a bar appears above the transcript: "5 speakers — how many are
  really in this recording?" with two buttons ("Only one", "Two"). Clicking one
  re-runs diarization only — **recognition is not repeated and your edits stay**.
  Measured on a real 14-sentence monologue that auto-split into 5 speakers
  (cluster sizes 5/4/2/2/1): after "Only one" it became a single speaker in
  0.8 s, every label was cleared, and a sentence hand-edited beforehand was
  untouched.
- **"1 speaker" added to the count selector** (was 2–6), so a solo recording no
  longer requires turning diarization off.
- **Take the transcript out, bring it back.** "Export → proof copy" writes one
  sentence per line as `index|speaker|text`, with no timestamps, so an external
  tool can edit it without fighting time codes. "Export → paste corrected copy"
  reads it back line by line and restores timing and speakers. Lines whose index
  got lost are skipped one by one; an empty line is treated as skipped rather
  than deleting the sentence; the whole paste is a single `Ctrl+Z`. Export
  formats therefore go from seven to **eight**.

> Why there is no built-in AI API: these recordings are interviews and phone
> calls. Uploading them is a privacy problem and the liability would be ours.
> The app never uploads anything — you take the text out and paste it back.

### v0.6.0 — what changed (measured)

- **Light theme.** One click in the header; the choice is remembered. The dimmest
  text in dark mode (timestamps, status line) went from 3.2:1 to 5.4:1 contrast
  (WCAG AA asks 4.5:1 for body text). All 57 colours are CSS variables, so
  switching themes leaves nothing behind.
- **Chinese locked by default.** The built-in language tagger guesses on noise,
  laughter and far-field reverb, so Chinese audio occasionally produced kana or
  hangul. In locked mode the whole file is decoded as Chinese and any leftover
  kana/hangul is dropped. On three far-field samples the auto mode produced
  2 / 0 / 4 foreign characters, the locked mode 0, with 0.76–0.86 character-level
  similarity between the two transcripts. Mixed Chinese/English still works
  ("Today is Tuesday" survives), and "自动" restores free language detection.
- **Diarization: two separate bugs fixed.**
  1. *Quiet speakers were dropped entirely.* The VAD threshold was silero's
     default 0.5, too high for phone recordings: the quietest of five speakers had
     only **4–7 %** of their speech detected — the person simply did not exist in
     the transcript. At 0.40 (and minimum speech 0.30 → 0.25 s) the same speaker
     reaches **53–89 %**, the sample goes from 0 to 6 sentences for them, overall
     speech coverage rises from 55 % to 73 %, and no extra fragments appear.
  2. *Clustering merged too eagerly.* Sentence-level embeddings (1–2 s, unstable)
     were merged at a fixed 0.62 similarity; reverberation pushes *different*
     speakers to 0.5–0.6, right through that threshold. Now the units are
     sentence groups (fragments glued, long sentences kept separate to avoid
     mixing two voices into one voiceprint), clustering is hierarchical
     (sherpa-onnx FastClustering), the merge threshold is **0.78**, and clusters
     below 2 % are no longer absorbed unless they are genuinely close.
     On a five-speaker far-field sample: **5 speakers, 100 % purity**.
- **Speaker-count selector (2–6).** If you know how many people are in the room,
  say so: the same sample forced to 5 gives **5 speakers, 100 % purity**.
  Changing the count re-runs diarization only, never recognition.
- **Loudness conditioning** before recognition (DC removal + peak normalisation,
  a no-op when the level is already fine).

> The recording from the feedback is not in hand, so these numbers come from
> synthetic far-field samples built from five real speakers (reverb + noise).
> Overlap and crosstalk still limit real-world accuracy; when it is off, set the
> speaker count.

---

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

The source itself does run: same UI, same recognition, same eight export formats.

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
版本 / Version：v0.7.0 · 2026-11-21
