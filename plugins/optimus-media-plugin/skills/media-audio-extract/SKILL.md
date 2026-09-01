---
name: media-audio-extract
description: Use when user wants to pull the audio track out of a video file — 提取音频、提取音轨、视频转音频、扒音频、从视频里提取声音、视频转mp3、只要声音不要画面。Not for audio-to-audio format conversion (that is media-audio-convert), video container conversion, or codec/format inspection.
metadata:
  version: "1.0.3"
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

先无条件执行以下命令，一次性列出源文件的全部流及其类型、编码与码率：

```bash
ffprobe -v error -show_entries stream=index,codec_type,codec_name,bit_rate -of default=nw=1 <input>
```

不要给该命令加 `-select_streams a:0`：只探第一条音频流会看不到"有没有视频流""有几条音轨"，而这两项各自对应一条硬约束（见下）。一条命令拿到全部流信息，后续四项判定都基于同一份输出。

⚠️ **`bit_rate` 可能取不到，这是探测能力的边界，不要编造替代值**：mkv 容器不在流头部存码率，实测其中的音频流与视频流 `bit_rate` **均返回 `N/A`**（mp4 里的 aac 则正常返回，如 59997）。此时**不得用 `format=bit_rate` 顶替**——那是含视频流的总码率（实测同一文件为 489595，而音频只占其中一小部分），拿它当音频码率会严重高估。源码率取不到时按 Step 5 的"源码率未知"一档处理，即向用户说明无法探测并让用户决定，不要默默套用默认值。

**先判定流结构（三项），再判定编码兼容性：**

**① 源文件无音频流**（输出中没有 `codec_type=audio`）

⛔ **STOP**：属于硬约束——没有音频流可提取，操作在物理上无法完成，用户确认也无法绕过。返回错误信息告知用户该视频不含音频轨道，终止任务，不进入 Step 5。

不要把"无音频流"与"文件损坏"混为一谈：ffprobe 命令本身报错或非零退出码属于后者，应按 media-analyze 的失败处理排查文件是否可读。

**② 源文件无视频流**（输出中没有 `codec_type=video`）

⛔ **STOP**：输入是纯音频文件而非视频，不存在"把音轨从画面里提取出来"的语义。返回错误信息说明该文件本身就是音频，并告知：如需转换音频格式或调整码率/采样率，应调用 `media-audio-convert`。终止任务，不进入 Step 5。

判据必须是"输出中有无 `codec_type=video`"，**不能靠退出码或能否查到音频编码**——纯音频文件执行上述命令同样返回退出码 0 并正常给出音频编码（实测 wav 返回 `codec_name=pcm_s16le`、exit=0），只看音频信息无法与视频文件区分。

**③ 源文件含多条音频流**（输出中有多个 `codec_type=audio`）

🔴 **CHECKPOINT**：列出各条音频流的索引、编码、码率（以及 ffprobe 可查到的 `language`/`title` 标签），让用户指认要提取哪一条，未确认前不得进入 Step 5。

不得依赖 ffmpeg 的默认选轨行为，也不要假定"默认就是第一条"：不带 `-map` 时 ffmpeg 按流的 disposition 与属性挑选"最佳"轨，`-map 0:a:0` 则按索引取第一条，二者判据不同。实测同一双轨文件，把 `default` 标记移到第二条轨后，不带 `-map` 复制的是第二条（196620bps）、带 `-map 0:a:0` 复制的是第一条（56137bps），产物 md5 不同。这也是 Step 5 必须显式带 `-map` 的原因——否则本步骤探测的流与实际提取的流可能不是同一条，编码兼容性的判定会张冠李戴。

**再判定编码兼容性**（以用户选定的那条音频流为准）：

**④ 源音频编码与目标扩展名兼容**

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

**⑤ 源音频编码与目标扩展名不兼容**

🔴 **CHECKPOINT**：最典型的是源为 `aac` 而用户要 `.mp3`。此时 `-c:a copy` 无法完成搬运。

告知用户：目标格式装不下当前音频编码（说出具体编码名与目标扩展名），需要重新编码。同时按源编码性质据实说明代价：

- **源编码已是有损**（`aac`/`mp3`/`opus`/`vorbis`）：转换会在已丢失细节的基础上再压一次，结果质量只会低于现有文件、不存在变好的可能（这是实测中唯一无例外的结论）。但**不要给出固定的损失量级**——实测额外信噪比降幅跨度达 0.02～28.7 dB，随素材宽带程度、目标编码器与码率档剧烈变化，"仅差约 X dB"与"损失惨重"都会在相当一部分场景下误导用户
- **源编码是无损**（`flac`/`alac`/PCM）：这是首次有损压缩，不可逆，建议保留原文件
- **体积走向**：对照本步骤查得的源 `bit_rate` 与将要使用的目标码率据实说明——目标码率低于源码率则体积减小，高于则反而增大。不要给出方向固定的结论

询问用户二选一——改用可无损搬运的扩展名（按上表给出具体建议），或接受重新编码。未确认前不得进入 Step 5。

用户改选无损扩展名则回到情况④；坚持原目标格式则进入 Step 5 的重新编码模式。

⛔ **不兼容组合的失败方式并不一致，不得把"命令会自己报错"当作安全网**：必须靠本步骤的兼容表事先拦截，而不是依赖 ffmpeg 失败来兜底。实测同一批不兼容组合分成两类——

- **会报错的（相对安全）**，且各 muxer 措辞完全不同：aac→`.mp3` 报 `Invalid audio stream. Exactly one MP3 audio stream is required.`；alac→`.aac` 报 `adts muxer supports only codec aac for type audio`；flac→`.m4a` 报 `Could not find tag for codec flac in stream #0`；alac/opus→`.wav` 报 `Codec <编码> not supported in WAVE format`
- **静默成功的（危险）**：aac/mp3/flac→`.wav` 以退出码 0 完成，产出 `format_name=wav` 而 `codec_name=aac` 的容器/编码错配文件，解码时报 `Input buffer exhausted before END element found`（且解码命令退出码仍为 0）；flac→`.opus`、flac→`.ogg` 同样退出码 0 且无告警，产出"扩展名声称 Opus、内容是 FLAC"的文件——后者甚至解码正常、数据无损，**只有后缀在撒谎，比 wav 错配更难发现**

因此目标扩展名不在兼容表对应行内时，一律在此拦下走本情况的 CHECKPOINT。**不要按扩展名去猜哪些组合会静默、哪些会报错**：同一个 `.wav` 对 aac 静默、对 alac 报错，规律不可靠。


### Step 5：执行提取

**默认模式（流复制，无损，情况④）：**

```bash
ffmpeg -y -i <input> -vn -map 0:a:0 -c:a copy <output>
```

**重新编码模式（情况⑤，用户确认后）：**

```bash
ffmpeg -y -i <input> -vn -map 0:a:0 -c:a <目标编码器> -b:a <目标码率> <output>
```

源文件含多条音频流且用户在 Step 4 情况③指定了其他轨时，把 `-map 0:a:0` 换成用户选定的索引（如第二条音频流为 `-map 0:a:1`）。

目标编码器按输出扩展名选取：`.mp3` → `libmp3lame`；`.m4a`/`.aac` → `aac`；`.opus` → `libopus`；`.flac` → `flac`（无损，省略 `-b:a`）；`.wav` → `pcm_s16le`（无损，省略 `-b:a`）。

`<目标码率>` 依据 Step 4 查得的源 `bit_rate` 决定，**不得固定填 192k**：

| 源码率 | 目标码率取值 |
|---|---|
| 高于 192k | 取 192k（常见平衡点）；用户要求"音质优先"可取 256k/320k |
| 接近 192k（约 128k–256k） | 取与源码率相同或略低的值 |
| 明显低于 192k（如录屏、语音录制常见的 64k 上下） | 取不高于源码率的值 |
| 取不到（`bit_rate=N/A`，常见于 mkv 容器） | 🔴 **CHECKPOINT**：向用户说明源码率无法探测（容器未记录），询问是接受 192k 默认值还是指定具体码率。不得默默套用 192k——若源音轨本是低码率，那会白白放大体积；也不得用 `format=bit_rate` 推算，那是含视频的总码率 |

源码率低而目标码率高时，音质不会提升（已丢失的信息无法恢复），只会让文件变大——实测源 60k 的音轨套用 192k，产出体积是源音轨的 2.6～3.1 倍（随目标编码器而异）且无任何音质收益。

- `-vn`：丢弃视频流，只保留音频。这是本 skill 与 `media-convert` 的根本区别——不是换容器，而是只取其中一条流
- `-map 0:a:0`：显式指定提取第一条音频流。不可省略——不带 `-map` 时 ffmpeg 按 disposition 与属性挑选"最佳"轨，与按索引取的 `a:0` 未必是同一条（见 Step 4 情况③的实测），会导致 Step 4 的探测对象与实际提取的流不一致
- `-c:a copy`：直接搬运原始音频流，不解码不重编码，无任何音质损失，速度取决于磁盘 I/O 而非 CPU
- `-b:a <目标码率>`：仅重新编码模式需要，取值见上表。无损编码器（`flac`/`pcm_s16le`）应省略该参数——传入不会报错也不会告警，属完全无效（实测带与不带产物 MD5 相同），但保留它会误导读者以为码率对无损编码有意义
- `-y`：覆盖策略见 `../media-ffmpeg-common/PREFLIGHT.md` 的「覆盖策略」，不得省略


> 音频码率与音质的关系、采样率/位深/声道概念见 [`knowledge-base/media/reference/audio-parameters.md`](../../../../knowledge-base/media/reference/audio-parameters.md)；编码器选型见 [`audio-codecs.md`](../../../../knowledge-base/media/reference/audio-codecs.md) §4「怎么选」。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

前置校验（Step 0-3）的失败场景、磁盘空间不足与编码器错误等通用场景见 `../media-ffmpeg-common/PREFLIGHT.md` 的「通用失败处理」；执行中暴露的 ffmpeg 报错见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 原因 | 处理建议 |
|---|---|---|
| 流复制报容器装不下编码，各 muxer 报错串不同：`Invalid audio stream. Exactly one MP3 audio stream is required.`（→`.mp3`）、`adts muxer supports only codec aac for type audio`（→`.aac`）、`Could not find tag for codec <编码> in stream #0`（→`.m4a`/`.mov`）、`Codec <编码> not supported in WAVE format`（alac/opus→`.wav`） | 目标容器装不下源音频编码，即 Step 4 情况⑤被漏判 | 回到 Step 4 重新查询源编码并走 CHECKPOINT 流程，不要直接静默改为重新编码。不要按单一报错串去匹配——不同 muxer 措辞完全不同，判据应是"流复制失败"这一事实 |
| 流复制退出码 0，但产物的容器与编码不匹配：`ffprobe` 显示 `format_name` 与扩展名声称的格式不符（如 `format_name=wav` 而 `codec_name=aac`，或扩展名为 `.opus` 而 `codec_name=flac`） | `-c:a copy` 对部分不兼容组合不报错，直接把编码塞进目标容器。实测 aac/mp3/flac→`.wav` 与 flac→`.opus`/`.ogg` 均属此类 | 改用重新编码模式重做，或改用能无损承载源编码的扩展名。`.wav` 错配文件解码时会报 `Input buffer exhausted before END element found` 且**解码命令退出码仍是 0**；`.opus`/`.ogg` 错配文件解码完全正常、数据无损，只有后缀在撒谎，更难发现——两者都只能靠核对 `format_name` 与 `codec_name` 是否匹配来判断 |
| `Stream map '' matches no streams.` / `Failed to set value '0:a:0' for option 'map'` | `-map` 指向的音频流不存在，即 Step 4 情况①（无音频流）被漏判 | 回到 Step 4 用完整流列表确认音频流是否存在，不要改为去掉 `-map` 让 ffmpeg 自动选流——那会掩盖"源文件没有音轨"这个真实原因 |
| `Unknown encoder 'libmp3lame'` / `'libopus'` | 当前 ffmpeg 构建未包含该音频编码器（与视频编码器缺失同类问题） | 执行 `ffmpeg -encoders` 确认可用编码器，提示用户更换含完整编码器的发行版，或改选构建已支持的输出格式 |
| 提取出的音频不是用户想要的那条音轨（如要中文得到英文） | 源文件含多条音频流，而命令按索引取了第一条 | 该问题**不会**表现为时长差异（多语言音轨时长通常一致，实测双轨均为 5.000000），只能靠核对内容发现。回到 Step 4 情况③列出全部音轨让用户指认，再用对应的 `-map 0:a:<索引>` 重做 |
| 源文件有音频流但产出文件无声 | 源音频流本身是静音轨，或编码不受当前构建支持 | 用 media-analyze 复核源音频流参数，确认是源文件本身问题而非提取环节 |

本 skill 产出纯音频，是任务终态，不参与 `../media-ffmpeg-common/REFERENCE.md` "组合请求处理约定"中的顺序编排——产出物无法再进入 trim/resize/framerate/compress/convert 的视频处理链。用户提出提取后还要转换音频格式时，告知另行调用 `media-audio-convert`。

## 不要做什么

前置校验相关的通用反例见 `../media-ffmpeg-common/PREFLIGHT.md` 的「不要做什么（前置校验部分）」。以下是本 skill 特有的反例：

- 不要在源文件无音频流时继续执行，应立即返回错误信息并终止（Step 4 情况①，硬约束不可用户确认绕过）
- 不要把"无音频流"与"ffprobe 命令本身失败"混为一谈——后者是文件损坏/格式不受支持，应按 media-analyze 的失败处理排查（Step 4）
- 不要跳过 Step 4 的流探测直接执行 `-c:a copy`——目标扩展名装不下源编码时多数容器会失败且报错不指向真实原因，而目标为 `.wav` 时更糟：命令会静默成功并产出容器/编码错配的坏文件
- 不要在编码不兼容时未经用户确认就静默切换为重新编码——必须先按源编码性质据实告知代价（Step 4 情况⑤的检查点）
- 不要在用户未指定输出扩展名时擅自假定 `.mp3`——多数源编码搬入 `.mp3` 都需要重新编码，属于有损选择，应先询问或给出无损建议（Step 0-3）
- 不要给无损编码器（`flac`/`pcm_s16le`）传 `-b:a`——传入不会报错也不会告警，属完全无效参数（实测产物 MD5 与不传时相同），保留它会误导读者以为码率对无损编码有意义
- 不要省略 `-vn`——缺了它 ffmpeg 会尝试把视频流也写进音频容器，导致失败或产出非预期文件
- 不要省略 `-map 0:a:0`——不带 `-map` 时 ffmpeg 按 disposition 挑"最佳"轨，与按索引取的 `a:0` 未必是同一条，会导致 Step 4 探测的流与实际提取的流不一致（Step 5）
- 不要给 Step 4 的探测命令加 `-select_streams a:0`——只看第一条音频流就看不到有无视频流、有几条音轨，两项硬约束都会失守（Step 4）
- 不要固定用 `-b:a 192k`——须依据 Step 4 查得的源码率取值，源码率低时套用 192k 只会让体积变大而音质毫无提升（实测源 60k 套 192k，体积涨到 2.6～3.1 倍，随编码器而异）；源码率取不到（`N/A`）时也不得默默套用 192k，须按 Step 5 的"源码率未知"一档走 CHECKPOINT
- 不要用 `format=bit_rate` 顶替音频流码率——本 skill 的输入含视频流，format 级是总码率（实测同一文件 489595 bps 而音频只占一小部分），据此选码率会严重高估（Step 4）
- 不要给出固定的二次有损音质损失量级——实测额外降幅跨度达 0.02～28.7 dB，随素材、编码器与码率档剧烈变化（机制：二代信噪比被一代封顶）。"仅差约 X dB"与"损失惨重"都会误导；可确定的只有方向："只会更差、不会更好"
- 不要靠时长差异判断是否取错了音轨——多语言音轨时长通常一致（实测双轨均为 5.000000），只能靠核对内容发现
- 不要按单一报错串去识别"容器装不下编码"——不同 muxer 的措辞完全不同（`.mp3`/`.aac`/`.m4a`/`.wav` 四种报错串各异），判据应是流复制失败这一事实
- 不要预设不兼容组合会自己报错来兜底——实测 aac/mp3/flac→`.wav` 与 flac→`.opus`/`.ogg` 都是退出码 0 静默产出错配文件，而同一个 `.wav` 对 alac/opus 却会报错，规律不可按扩展名推断；拦截必须由 Step 4 的兼容表在执行前完成
- 不要把"扩展名与产物 `format_name` 一致"当作成功判据——flac 塞进 `.opus` 时 `format_name=ogg` 看着合理、解码也正常，但内容是 FLAC 而非 Opus，须同时核对 `codec_name`
- 不要靠退出码判断解码是否正常——容器/编码错配的文件解码时会打印错误但退出码仍为 0（实测）
- 不要承接纯音频到纯音频的格式转换（如 wav→mp3、flac→aac）——本 skill 的输入必须是含视频流的文件，Step 4 情况②会硬拦截纯音频输入，纯音频转换应调用 `media-audio-convert`
- 不要在提取完成后自动调用其他 media-* skill 做后续处理，也不写入组合请求编排链条
