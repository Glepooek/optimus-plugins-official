---
name: media-audio-convert
description: Use when user wants to convert an audio file to another audio format or change its bitrate, sample rate, or channel count — 音频格式转换、wav转mp3、flac转aac、音频转码、改音频码率、改采样率、音频转单声道、无损转有损。Not for extracting audio from video (that is media-audio-extract), video container conversion, or codec/format inspection.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg/ffprobe 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音频格式与参数转换

## 功能概述

将单个纯音频文件转换到指定格式（如 wav→mp3、flac→aac），或调整其码率、采样率、声道数。输入与输出都必须是纯音频文件——从视频中提取音轨属于 `media-audio-extract` 的职责，本 skill 不承接。

本 skill 的核心价值不在于跑一条转换命令，而在于**先查清源文件的真实编码再告知用户损失类型**：音频文件的扩展名不能代表其内部编码（同一个 `.m4a` 里可能是 AAC 有损，也可能是 ALAC 无损），不查真实编码就无法判断这次转换是首次有损、二次有损，还是根本只需重封装。

仅支持单文件，输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 0-3：前置校验

执行 `../media-ffmpeg-common/PREFLIGHT.md` 的 Step 0-3 完整流程：需求预告 → 确认环境 → 校验输入文件 → 确认输出路径（含父目录可写、输出路径不得与输入路径相同两项校验）。

本 skill 的必需信息：**输入音频路径、输出音频路径**（目标格式由输出扩展名承载）。

以下参数均有默认取值，不属于必需信息，缺失不阻塞：

| 参数 | 缺省行为 |
|---|---|
| 码率 `-b:a` | 有损目标编码取 192k；无损目标编码不适用 |
| 采样率 `-ar` | 不传该参数，沿用源文件采样率 |
| 声道数 `-ac` | 不传该参数，沿用源文件声道数 |

### Step 4：执行前校验

先无条件执行以下命令查询源文件的**真实音频编码**，不得依据扩展名推断：

```bash
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=nw=1 <input>
```

⛔ **STOP**：命令报错、非零退出码或输出为空时，说明文件已损坏、不是音频文件，或编码不受当前 ffmpeg 构建支持。返回错误信息告知用户，建议先用 media-analyze 排查，终止任务，不进入 Step 5。

> 「后缀 ≠ 真实编码」的判断方法与常见格式辨析见 [`knowledge-base/media/reference/audio-container-formats.md`](../../../../knowledge-base/media/reference/audio-container-formats.md) §2「常见音频格式辨析」与 §3「后缀 vs 编码的判断方法」；各编码的有损/无损性质见 [`audio-codecs.md`](../../../../knowledge-base/media/reference/audio-codecs.md) §1「音频编码分类」。

查得真实编码后，按下表判定本次转换的性质。🔴 **CHECKPOINT**：命中"需告知"的行，必须在执行前主动说明，而非等用户听出音质问题才解释；未确认前不得进入 Step 5：

| 源真实编码 → 目标编码 | 性质 | 需告知用户什么 |
|---|---|---|
| 无损 → 无损（FLAC→ALAC、WAV→FLAC） | 无损转换 | 无音质损失，可直接执行；WAV→FLAC 还会显著减小体积 |
| 无损 → 有损（FLAC→MP3、WAV→AAC） | 首次有损 | 会产生首次有损压缩、不可逆，原文件建议保留；体积会明显减小 |
| **有损 → 有损（AAC→MP3、MP3→AAC）** | **二次有损** | 🔴 音质损失比首次压缩明显（在已丢失细节的基础上再压一次），且体积未必更小。询问用户是否确有必要，或改为保留原格式 |
| 有损 → 无损（MP3→FLAC、AAC→WAV） | 无意义放大 | 🔴 已丢失的细节无法恢复，转成无损格式只会让体积大幅增加而音质不变。询问用户是否确认继续 |
| **编码相同，仅容器不同（AAC in `.m4a` → `.aac`）** | **只需重封装** | 🔴 无需转码。告知用户可用流复制无损换容器，避免无谓的二次有损，走 Step 5 的重封装模式 |

判定要点：

- **必须用查得的真实编码判定，不能用扩展名**。用户说"把 .m4a 转 mp3"时，`.m4a` 里是 ALAC 则属"无损→有损"，是 AAC 则属"二次有损"——两者要告知的内容完全不同
- 目标编码由输出扩展名推定：`.mp3`→MP3（有损）、`.aac`/`.m4a`→AAC（有损，`.m4a` 也可装 ALAC 但本 skill 默认取 AAC）、`.opus`→Opus（有损）、`.ogg`→Vorbis（有损）、`.flac`→FLAC（无损）、`.wav`→PCM（无损）
- 用户明确指定了 `-ar`/`-ac` 且数值低于源文件时（如 48000→44100、立体声→单声道），额外告知这是不可逆的信息丢失

> 采样率与声道数的含义、降采样/缩混的影响见 [`audio-parameters.md`](../../../../knowledge-base/media/reference/audio-parameters.md) §1「采样率」与 §3「声道数」。

### Step 5：执行转换

**默认模式（重新编码）：**

```bash
ffmpeg -y -i <input> -c:a <目标编码器> -b:a 192k <output>
```

**重封装模式（Step 4 判定为"编码相同，仅容器不同"，用户确认后）：**

```bash
ffmpeg -y -i <input> -c:a copy <output>
```

**带参数调整（用户明确指定采样率/声道数时，按需追加）：**

```bash
ffmpeg -y -i <input> -c:a <目标编码器> -b:a 192k -ar 44100 -ac 2 <output>
```

目标编码器按输出扩展名选取：

| 输出扩展名 | 编码器 | 是否接受 `-b:a` |
|---|---|---|
| `.mp3` | `libmp3lame` | 是 |
| `.m4a`、`.aac` | `aac` | 是 |
| `.opus` | `libopus` | 是 |
| `.ogg` | `libvorbis` | 是 |
| `.flac` | `flac` | **否**（无损） |
| `.wav` | `pcm_s16le` | **否**（无压缩） |

- `-b:a 192k`：有损编码下音质与体积的常见平衡点。用户要求"音质优先"可提到 256k/320k，"体积优先"可降到 128k；无损编码器不接受该参数，须省略，否则 ffmpeg 会忽略或报错
- `-ar <采样率>`：仅在用户明确要求时传入。不传则沿用源采样率——**不要主动"标准化"到 44100**，那是不必要的重采样，会引入额外失真
- `-ac <声道数>`：仅在用户明确要求时传入。`-ac 1` 缩混为单声道会永久丢失立体声信息
- `-c:a copy`：重封装模式专用，不解码不重编码，无音质损失
- `-y`：覆盖策略见 `../media-ffmpeg-common/PREFLIGHT.md` 的「覆盖策略」，不得省略

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

前置校验（Step 0-3）的失败场景、磁盘空间不足与编码器错误等通用场景见 `../media-ffmpeg-common/PREFLIGHT.md` 的「通用失败处理」；执行中暴露的 ffmpeg 报错见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 原因 | 处理建议 |
|---|---|---|
| `Unknown encoder 'libmp3lame'` / `'libopus'` / `'libvorbis'` | 当前 ffmpeg 构建未包含该音频编码器 | 执行 `ffmpeg -encoders` 确认可用编码器，提示用户更换含完整编码器的发行版，或改选构建已支持的输出格式 |
| 重封装模式报 `Could not find tag for codec` | Step 4 误判为"编码相同仅容器不同"，实际目标容器装不下该编码 | 回到 Step 4 复核真实编码与目标扩展名的对应关系，改走重新编码模式 |
| 转换后文件体积反而变大 | 有损→无损（如 MP3→FLAC），或有损→有损时目标码率高于源码率 | 属预期现象，说明 Step 4 已告知的权衡；建议改回与源相当或更低的码率，或保留原格式 |
| 输入是视频文件而非纯音频 | 用户混淆了本 skill 与 media-audio-extract 的职责 | 明确告知从视频提取音轨应调用 `media-audio-extract`，本 skill 只处理纯音频到纯音频，不代为兼容 |
| 转换后音质明显下降但参数看起来正常 | 源文件本就是低码率有损编码，二次编码放大了失真 | 复核 Step 4 查得的源编码与码率，说明这是二次有损的固有结果，无法通过调高目标码率挽回 |

本 skill 输入输出都是纯音频，与视频处理链无交集，不参与 `../media-ffmpeg-common/REFERENCE.md` "组合请求处理约定"中的顺序编排。

## 不要做什么

前置校验相关的通用反例见 `../media-ffmpeg-common/PREFLIGHT.md` 的「不要做什么（前置校验部分）」。以下是本 skill 特有的反例：

- 不要依据扩展名推断源编码——必须先 ffprobe 查真实编码，`.m4a` 里可能是 AAC 也可能是 ALAC，两者的转换性质完全不同（Step 4）
- 不要跳过 Step 4 的损失类型告知直接执行转换——用户有权在动手前知道这次是首次有损、二次有损还是无意义放大
- 不要在"有损→有损"场景下不加说明就转换——这是本 skill 最容易造成用户不满的场景（音质降了、体积还没小）
- 不要在"编码相同仅容器不同"时执行重新编码——应走 `-c:a copy` 重封装，避免无谓的二次有损（Step 4 末行）
- 不要在 ffprobe 查询源编码失败时继续执行，应立即返回错误信息并终止（Step 4）
- 不要给无损编码器（`flac`/`pcm_s16le`）传 `-b:a`——它们不接受码率参数
- 不要主动"标准化"采样率或声道数——用户未要求时不传 `-ar`/`-ac`，重采样与缩混都是不可逆的信息丢失
- 不要承接从视频提取音轨的诉求（输入是 `.mp4`/`.mkv` 等视频文件）——那是 `media-audio-extract` 的职责，本 skill 输入必须是纯音频
- 不要支持视频容器格式转换（如 mp4→mkv）——那是 `media-convert` 的职责
