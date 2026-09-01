---
name: media-frame-extract
description: Use when user wants to capture still images out of a video — 视频截图、截帧、抽帧、导出封面图、截取某一帧、每隔几秒截一张、生成预览图。Not for playing or previewing video (that is media-play), clip trimming, or codec/format inspection.
metadata:
  version: "1.0.2"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg/ffprobe 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 视频画帧提取

## 功能概述

从单个视频文件中提取静态图片，支持两种模式：

- **单帧模式（默认）**：截取指定时间点的一帧，用于取封面图、查看某一瞬间的画面
- **多帧等间隔模式**：每隔固定秒数截一张，用于生成预览图序列

产出物为图片文件，是本 skill 的任务终态——不自动衔接后续处理。仅支持单个视频输入，输出路径必须由用户或 Claude 显式指定。

不产出雪碧图（缩略图矩阵）：那是播放器进度条预览的专用形态，需要额外约定 tile 布局与总帧数的匹配关系，不属于本 skill 定位。

## 使用方法

### Step 0-3：前置校验

执行 `../media-ffmpeg-common/PREFLIGHT.md` 的 Step 0-3 完整流程：需求预告 → 确认环境 → 校验输入文件 → 确认输出路径（含父目录可写、输出路径不得与输入路径相同两项校验）。

本 skill 的必需信息按模式区分：

| 模式 | 必需信息 |
|---|---|
| 单帧 | 输入视频路径、时间点、输出图片路径 |
| 多帧等间隔 | 输入视频路径、间隔秒数、输出路径模板 |

模式判定依据用户措辞：出现"每隔""一系列""每N秒""批量""预览图"等表述即为多帧模式，否则为单帧模式。单帧模式下用户未给时间点时，不要擅自取 `00:00:00`——首帧常是黑场或片头，多数情况下不是用户想要的封面图，应在 Step 0 询问。

图片格式由输出扩展名决定：`.png` 无损、体积大（默认建议）；`.jpg` 有损、体积小，适合大量抽帧。

### Step 4：执行前校验

先无条件执行以下命令，一次性查询视频流是否存在与视频总时长：

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=codec_type -show_entries format=duration -of default=nw=1 <input>
```

⛔ **STOP**：命令报错或无法解析出 `duration` 时，说明文件可能已损坏或编码格式不受当前 ffmpeg 构建支持，而非时间点问题。返回错误信息告知用户，建议先用 media-analyze 排查，终止任务，不进入 Step 5。

⛔ **STOP**：输出中**没有 `codec_type=video` 这一行**时，说明源文件不含视频流（如把纯音频文件当视频传入），没有画面可截取。这是硬约束，用户确认也无法绕过：返回错误信息告知用户该文件不含视频流，终止任务，不进入 Step 5。

判据必须是"`codec_type=video` 行是否存在"，**不是退出码**——纯音频文件执行上述命令同样返回退出码 0 并正常输出 `duration`（实测 wav 返回 `duration=3.000000`、exit=0），只看退出码或只看时长必然放行到 Step 5，届时才吃 `Output file does not contain any stream` 报错。

再按模式判定：

**单帧模式：时间点是否落在合法区间内**

⛔ **STOP**：时间点超过视频总时长时属于硬约束——该时间点的画面在物理上不存在，用户确认也无法绕过。返回错误信息告知用户核对时间点（可参考刚查得的总时长），终止任务，不进入 Step 5。

这项预检不可省略：时间点超范围时 ffmpeg **不会报错**，而是以退出码 0 结束、不产出任何文件、仅打印 `Output file is empty`——只看退出码的判断会把它当成成功。

**多帧等间隔模式：预估产出张数与抽帧位置**

按 `round(总时长(秒) ÷ 间隔(秒))` 估算张数，**四舍五入（余数达到半个间隔才进位），不是向上取整**。实测：4 秒视频按 3 秒间隔得 1 张、7 秒按 3 秒得 2 张、10 秒按 3 秒得 3 张——用 `ceil` 会在这些情形下各多报 1 张。

⚠️ **抽出的帧不在 `t=0`、`t=N`、`t=2N`，而在每个区间的中段**：`-vf fps=1/N` 的实现是对每个输入帧计算 `round(t ÷ N)` 映射到输出序号（默认 `round=near`），同一序号内后来的帧会顶掉先前的，因此每个区间最终留下的是**跨过中点前的最后一帧**。实测 5 秒 30fps 视频按 2 秒间隔，三张图的画面分别取自源帧 29、89、149（t≈0.97、2.97、4.97），与源帧 0/60/120 的画面逐字节不同。

向用户预告时须说明这一点：**第一张不是视频首帧**。用户若明确要"第一帧"或某个精确时间点的画面，应改用单帧模式（`-ss` + `-frames:v 1 -update 1`），那才是帧精确定位。

🔴 **CHECKPOINT**：预估张数超过 200 时，必须在执行前告知用户具体预估数量与输出目录，询问是否继续或改用更大的间隔——一条命令产出数百个文件属于不易撤销的操作，用户往往没有意识到间隔取小了。未确认前不得进入 Step 5。

预估张数在 200 以内时无需确认，直接执行。

### Step 5：执行提取

**单帧模式：**

```bash
ffmpeg -y -ss <时间点> -i <input> -frames:v 1 -update 1 <output>
```

**多帧等间隔模式：**

```bash
ffmpeg -y -i <input> -vf fps=1/<间隔秒数> <输出目录>/<前缀>_%03d.<ext>
```

执行后确认输出文件（多帧模式为输出目录下的图片序列）确实存在，**不得仅凭退出码判定成功**——见 Step 4 中"时间点超范围时 exit=0 却不产文件"的说明。

⚠️ **注意：本 skill 只有一种 `-ss` 写法，不要照搬 media-trim 的"快速模式 / 精确模式"双模式设计。**

media-trim 需要双模式，是因为它的快速模式用 `-c copy` 不解码，只能对齐到最近关键帧。截图必然要解码画面，而 ffmpeg 在 `-ss` 位于 `-i` 之前时会先 seek 到目标点前的关键帧、再解码并丢弃到目标时间戳——**既快又帧精确**。因此单帧模式固定把 `-ss` 放在 `-i` 之前，不存在需要用户选择的精度权衡，也不要为此造一个"精确模式"。

- `-ss <时间点>`：格式 `HH:MM:SS`、`HH:MM:SS.mmm` 或纯秒数。放在 `-i` 之前是输入端 seek，对需要解码的输出同样帧精确
- `-frames:v 1` 与 `-update 1`：这两个参数**必须成对出现**，单帧模式缺一不可，原因见下方「单帧模式为何需要 `-update 1`」
- `-vf fps=1/<间隔秒数>`：按固定时间间隔抽帧，如 `fps=1/60` 为每 60 秒一帧、`fps=1/5` 为每 5 秒一帧。取帧位置在每个区间的中段而非区间起点，张数按 `round` 而非 `ceil`，详见 Step 4。这是滤镜层的时间重采样，与 media-framerate 的 `-r`（改变输出视频帧率、在输出端丢帧）机制不同，产出张数也不同——同一 5 秒视频 `-r 0.5` 得 4 张、`-vf fps=1/2` 得 3 张，本 skill 固定用后者
- `%03d`：ffmpeg 的序号占位符，产出 `_001`、`_002` 递增编号；多帧模式**必须**带该占位符，缺失时 image2 muxer 只允许写入第一张，写第二张即报错并中断整个任务（完整报错见「失败处理」表）
- `-y`：覆盖策略见 `../media-ffmpeg-common/PREFLIGHT.md` 的「覆盖策略」，不得省略

**单帧模式为何需要 `-update 1`**

不带 `-update 1` 时，命令仍能正确产出图片（退出码 0），但 ffmpeg 每次都会打印两行 image2 警告，提示文件名不含序号 pattern 并建议改用 `-update`。产出无误而输出里有 warning，极易被误判成执行失败并向用户上报。带上 `-update 1` 后警告消失，产出的图片与不带时逐字节一致（实测 md5 相同），因此固定带上。

⛔ **不得只带 `-update 1` 而漏掉 `-frames:v 1`**：`-update 1` 的语义是允许反复写入同一个文件，此时缺少帧数限制会让 ffmpeg 一路解码到视频结尾、用后续每一帧覆盖输出文件，**最终留下的是视频最后一帧而非目标时间点那一帧**，且退出码为 0、无任何报错（实测产物 md5 等于视频末帧）。这是本 skill 唯一会静默产出错误内容的组合，比报错中断更难发现。


> 关键帧（I/P/B 帧）与 GOP 概念见 [`knowledge-base/media/reference/video-codecs.md`](../../../../knowledge-base/media/reference/video-codecs.md) 的「关键帧（I / P / B 帧）与 GOP」小节；帧率与时间采样概念见 [`media-parameters.md`](../../../../knowledge-base/media/reference/media-parameters.md) §2「帧率」。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

前置校验（Step 0-3）的失败场景、磁盘空间不足与编码器错误等通用场景见 `../media-ffmpeg-common/PREFLIGHT.md` 的「通用失败处理」；执行中暴露的 ffmpeg 报错见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 原因 | 处理建议 |
|---|---|---|
| 多帧模式中断并只产出一个文件，stderr 出现 `Cannot write more than one file with the same name. Are you missing the -update option or a sequence pattern?`，末尾为 `Conversion failed!` | 输出路径缺少 `%03d` 序号占位符。image2 muxer 对不含 pattern 的文件名只允许写入一张，写第二张即失败 | 在输出文件名中加入 `%03d`，重新执行；已产出的单个文件是序列中的**第一张**（内容本身正确），不是最后一张。识别该失败请匹配上述 `Cannot write more than one file...` 行（直接点明根因）或 `Conversion failed!`；下游的 `Error muxing a packet` 与 `Task finished with error: Invalid argument` 是**两行**，不存在 `Error muxing a packet: Invalid argument` 这个拼接串，按它匹配永远匹配不到 |
| 截出的图片是黑屏或纯色 | 该时间点恰为黑场、转场或片头片尾 | 属源视频内容本身，非命令问题；建议换一个时间点重截 |
| 单帧模式退出码 0，但产出的画面不是指定时间点，而是视频末帧 | 命令带了 `-update 1` 却漏掉 `-frames:v 1`，ffmpeg 一路解码到结尾并用每一帧覆盖输出文件 | 补上 `-frames:v 1` 重新执行。该组合无任何报错，须靠核对画面内容发现（见 Step 5 的成对出现要求） |
| 执行时报 `Output file does not contain any stream` | 源文件无视频流（如纯音频文件），没有画面可截取。正常情况下 Step 4 已拦截，出现该报错说明预检被跳过或只看了退出码 | 告知用户该文件不含视频流，无法截图；播放音频请调用 media-play。同时回头补做 Step 4 的 `codec_type=video` 判定 |
| 退出码 0，但输出文件不存在，日志中有 `Output file is empty` | 时间点超出视频总时长。ffmpeg 对此不报错，正常退出但不写任何内容 | 用 Step 4 查得的总时长核对时间点后重试。该现象说明不能仅凭退出码判定成功 |
| 输出中出现 `does not contain an image sequence pattern` 之类的 image2 警告 | 单帧命令漏了 `-update 1`。属**警告不是错误**，图片已正确产出 | 不要据此向用户上报失败；补上 `-update 1` 即可消除警告，产出内容与之前逐字节一致 |
| 多帧模式产出数量与预估差异较大 | 视频实际时长与容器元数据声明的时长不一致（常见于流式录制的文件） | 属预期偏差，说明预估基于元数据时长；以实际产出为准。若只差 1 张，先检查预估是否误用了 `ceil` 而非 `round`（见 Step 4） |
| 用户反馈多帧模式的第一张不是视频开头的画面 | 这是 `-vf fps` 的固有行为：取帧落在每个区间中段，而非区间起点（见 Step 4） | 属预期行为，非命令问题。用户需要首帧或某个精确时间点的画面时，改用单帧模式指定 `-ss` |

本 skill 产出图片，是任务终态，不参与 `../media-ffmpeg-common/REFERENCE.md` "组合请求处理约定"中的顺序编排——产出物无法再进入 trim/resize/framerate/compress/convert 的视频处理链。

## 不要做什么

前置校验相关的通用反例见 `../media-ffmpeg-common/PREFLIGHT.md` 的「不要做什么（前置校验部分）」。以下是本 skill 特有的反例：

- 不要为本 skill 设计"快速模式 / 精确模式"双模式——截图必然解码，`-ss` 在 `-i` 之前已经是帧精确的，media-trim 的双模式前提（`-c copy` 不解码）在此不成立（Step 5）
- 不要在单帧模式下省略 `-frames:v 1`——它与 `-update 1` 必须成对出现，只带 `-update 1` 会静默产出视频末帧而非目标帧（退出码 0、无报错，最难发现）；两者都漏则中断，报错与缺 `%03d` 完全同构（见失败处理表）（Step 5）
- 不要在单帧模式下省略 `-update 1`——每次执行都会打印 image2 pattern 警告，产出虽正确但极易被误判为失败（Step 5）
- 不要把 image2 pattern 警告当作执行失败上报——那是 warning 不是 error，图片已正确产出
- 不要在多帧模式的输出路径中省略 `%03d` 序号占位符——image2 muxer 只允许写入第一张，写第二张即报错中断（三行报错原文见失败处理表）；残留文件是序列第一张，不是最后一张
- 不要仅凭退出码 0 判定截图成功——时间点超范围时 ffmpeg 正常退出却不产出任何文件，须确认输出文件确实存在（Step 5）
- 不要靠退出码或能否查到时长来判断源文件有无视频流——纯音频文件同样返回退出码 0 与正常时长，判据是 `codec_type=video` 行是否存在（Step 4）
- 不要在时间点超过视频总时长时继续执行，应立即返回错误信息并终止（Step 4，硬约束不可用户确认绕过）
- 不要在 ffprobe 查询总时长本身失败时，误判为时间点问题并要求用户核对时间点，应告知文件可能已损坏（Step 4）
- 不要在多帧模式预估产出超过 200 张时不加告知就执行——产出数百个文件不易撤销，须先确认（Step 4 的检查点）
- 不要在用户未指定时间点时擅自取 `00:00:00`——首帧常为黑场或片头，多数情况下不是用户要的封面图，应先询问
- 不要用 `-r` 或 `minterpolate` 处理多帧抽取——那是 media-framerate 改变视频帧率的参数，本 skill 用滤镜层的 `-vf fps=1/N`
- 不要用 `ceil(时长 ÷ 间隔)` 预估多帧张数——实测真实规则是 `round`（四舍五入），`ceil` 会在余数不足半个间隔时多报 1 张（如 4s@3s、7s@3s、10s@3s 各多报 1）（Step 4）
- 不要声称多帧模式抽出的是 `t=0`、`t=N`、`t=2N` 的画面或"第一张是首帧"——实测取帧落在每个区间中段（5s 视频按 2s 间隔取自源帧 29/89/149，而非 0/60/120）。用户要首帧或精确时间点时应改用单帧模式（Step 4）
- 不要产出雪碧图/缩略图矩阵（`tile` 滤镜）——不属于本 skill 定位
- 不要在提取完成后自动调用其他 media-* skill 做后续处理，也不写入组合请求编排链条
