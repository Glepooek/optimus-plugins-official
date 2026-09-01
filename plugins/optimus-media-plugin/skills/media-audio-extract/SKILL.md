---
name: media-audio-extract
description: Use when user wants to pull the audio track out of a video file — 提取音频、提取音轨、视频转音频、扒音频、从视频里提取声音、视频转mp3、只要声音不要画面。Not for audio-to-audio format conversion (that is media-audio-convert), video container conversion, or codec/format inspection.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg/ffprobe 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 视频音轨提取

## 功能概述

从单个视频文件中提取音频流，产出纯音频文件，丢弃视频流。默认使用流复制（`-c:a copy`）直接搬出原始音频流，无损且极快；仅当用户要求的输出格式装不下源音频编码时，才降级为重新编码。仅支持单文件，输出路径必须由用户或 Claude 显式指定。

产出物为纯音频，是本 skill 的任务终态——不自动衔接后续处理，如需继续转换音频格式或调整采样率/码率，另行触发 `media-audio-convert`。

## 使用方法

### Step 0-3：前置校验

执行 `../media-ffmpeg-common/PREFLIGHT.md` 的 Step 0-3 完整流程：需求预告 → 确认环境 → 校验输入文件 → 确认输出路径（含父目录可写、输出路径不得与输入路径相同两项校验）。

本 skill 的必需信息：**输入视频路径、输出音频路径**。

输出音频格式由输出路径的扩展名决定，用户只说"提取音频"而未指定扩展名时，不要擅自假定 `.mp3`——`.mp3` 在多数情况下都需要重新编码（见 Step 4），属于有损选择。应在 Step 0 询问目标格式，或建议用"与源编码匹配的无损搬运格式"（Step 4 查得源编码后即可给出具体建议）。

### Step 4：执行前校验

先无条件执行以下命令查询源文件的音频流编码：

```bash
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 <input>
```

依次判定三种情况：

**① 源文件无音频流**（命令输出为空）

⛔ **STOP**：属于硬约束——没有音频流可提取，操作在物理上无法完成，用户确认也无法绕过。返回错误信息告知用户该视频不含音频轨道，终止任务，不进入 Step 5。

不要把"无音频流"与"文件损坏"混为一谈：ffprobe 命令本身报错或非零退出码属于后者，应按 media-analyze 的失败处理排查文件是否可读。

**② 源音频编码与目标扩展名兼容**

直接进入 Step 5 的流复制模式，无损提取。常见兼容关系：

| 源音频编码 | 可无损搬入的扩展名 |
|---|---|
| `aac` | `.m4a`、`.aac` |
| `mp3` | `.mp3` |
| `flac` | `.flac` |
| `alac` | `.m4a` |
| `opus` | `.opus`、`.ogg` |
| `vorbis` | `.ogg` |
| `pcm_s16le` 等 PCM | `.wav` |

> 容器与编码的关系、"后缀不等于真实编码"见 [`knowledge-base/media/reference/audio-container-formats.md`](../../../../knowledge-base/media/reference/audio-container-formats.md) §1「音频文件的构成」与 §3「后缀 vs 编码的判断方法」；各编码的有损/无损性质见 [`audio-codecs.md`](../../../../knowledge-base/media/reference/audio-codecs.md) §2「常见音频编解码器对比」。

**③ 源音频编码与目标扩展名不兼容**

🔴 **CHECKPOINT**：最典型的是源为 `aac` 而用户要 `.mp3`。此时 `-c:a copy` 会直接报 `Could not find tag for codec aac in stream #0`，无法靠流复制完成。

告知用户：目标格式装不下当前音频编码（说出具体编码名与目标扩展名），需要重新编码；源编码已是有损时，重新编码是**二次有损压缩**，音质损失比首次压缩明显，且体积未必更小。询问用户二选一——改用可无损搬运的扩展名（按上表给出具体建议），或接受重新编码。未确认前不得进入 Step 5。

用户改选无损扩展名则回到情况②；坚持原目标格式则进入 Step 5 的重新编码模式。

### Step 5：执行提取

**默认模式（流复制，无损，情况②）：**

```bash
ffmpeg -y -i <input> -vn -c:a copy <output>
```

**重新编码模式（情况③，用户确认后）：**

```bash
ffmpeg -y -i <input> -vn -c:a <目标编码器> -b:a 192k <output>
```

目标编码器按输出扩展名选取：`.mp3` → `libmp3lame`；`.m4a`/`.aac` → `aac`；`.opus` → `libopus`；`.flac` → `flac`（无损，不需要 `-b:a`）；`.wav` → `pcm_s16le`（无损，不需要 `-b:a`）。

- `-vn`：丢弃视频流，只保留音频。这是本 skill 与 `media-convert` 的根本区别——不是换容器，而是只取其中一条流
- `-c:a copy`：直接搬运原始音频流，不解码不重编码，无任何音质损失，速度取决于磁盘 I/O 而非 CPU
- `-b:a 192k`：仅重新编码模式需要，是有损编码下音质与体积的常见平衡点。用户要求"音质优先"可提到 256k/320k，"体积优先"可降到 128k；无损编码器（`flac`/`pcm_s16le`）不接受该参数，须省略
- `-y`：覆盖策略见 `../media-ffmpeg-common/PREFLIGHT.md` 的「覆盖策略」，不得省略

> 音频码率与音质的关系、采样率/位深/声道概念见 [`knowledge-base/media/reference/audio-parameters.md`](../../../../knowledge-base/media/reference/audio-parameters.md)；编码器选型见 [`audio-codecs.md`](../../../../knowledge-base/media/reference/audio-codecs.md) §4「怎么选」。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

前置校验（Step 0-3）的失败场景、磁盘空间不足与编码器错误等通用场景见 `../media-ffmpeg-common/PREFLIGHT.md` 的「通用失败处理」；执行中暴露的 ffmpeg 报错见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 原因 | 处理建议 |
|---|---|---|
| `Could not find tag for codec <编码> in stream #0` | 流复制模式下目标容器装不下源音频编码，即 Step 4 情况③被漏判 | 回到 Step 4 重新查询源编码并走 CHECKPOINT 流程，不要直接静默改为重新编码 |
| `Unknown encoder 'libmp3lame'` / `'libopus'` | 当前 ffmpeg 构建未包含该音频编码器（与视频编码器缺失同类问题） | 执行 `ffmpeg -encoders` 确认可用编码器，提示用户更换含完整编码器的发行版，或改选构建已支持的输出格式 |
| 提取出的音频文件时长与源视频不一致 | 源文件含多条音频流（如多语言音轨），`a:0` 只取了第一条 | 说明本 skill 固定提取第一条音频流；用户需要其他音轨时，告知当前定位不支持多音轨选择 |
| 源文件有音频流但产出文件无声 | 源音频流本身是静音轨，或编码不受当前构建支持 | 用 media-analyze 复核源音频流参数，确认是源文件本身问题而非提取环节 |

本 skill 产出纯音频，是任务终态，不参与 `../media-ffmpeg-common/REFERENCE.md` "组合请求处理约定"中的顺序编排——产出物无法再进入 trim/resize/framerate/compress/convert 的视频处理链。用户提出提取后还要转换音频格式时，告知另行调用 `media-audio-convert`。

## 不要做什么

前置校验相关的通用反例见 `../media-ffmpeg-common/PREFLIGHT.md` 的「不要做什么（前置校验部分）」。以下是本 skill 特有的反例：

- 不要在源文件无音频流时继续执行，应立即返回错误信息并终止（Step 4 情况①，硬约束不可用户确认绕过）
- 不要把"无音频流"与"ffprobe 命令本身失败"混为一谈——后者是文件损坏/格式不受支持，应按 media-analyze 的失败处理排查（Step 4）
- 不要跳过 Step 4 的源编码查询直接执行 `-c:a copy`——目标扩展名装不下源编码时命令会失败，且报错信息不指向真实原因
- 不要在编码不兼容时未经用户确认就静默切换为重新编码——必须先告知这可能是二次有损压缩（Step 4 情况③的检查点）
- 不要在用户未指定输出扩展名时擅自假定 `.mp3`——多数源编码搬入 `.mp3` 都需要重新编码，属于有损选择，应先询问或给出无损建议（Step 0-3）
- 不要给无损编码器（`flac`/`pcm_s16le`）传 `-b:a`——它们不接受码率参数
- 不要省略 `-vn`——缺了它 ffmpeg 会尝试把视频流也写进音频容器，导致失败或产出非预期文件
- 不要承接纯音频到纯音频的格式转换（如 wav→mp3、flac→aac）——本 skill 的输入必须是含音频流的视频文件，纯音频转换应调用 `media-audio-convert`
- 不要在提取完成后自动调用其他 media-* skill 做后续处理，也不写入组合请求编排链条
