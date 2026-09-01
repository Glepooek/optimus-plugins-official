---
name: media-trim
description: Use when user wants to cut a specific segment out of a media file — 片段截取、截取视频、剪切一段、掐头去尾、截取某个时间段。Not for resolution changes, compression, or codec/format inspection.
metadata:
  version: "1.1.4"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频片段截取

## 功能概述

从单个音视频文件中截取指定时间段。默认使用流复制（`-c copy`）快速截取，速度极快但会对齐到最近关键帧，实际起止时间可能与用户输入相差数百毫秒；如需帧精确的截取，使用重新编码的精确模式。输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 0-3：前置校验

执行 `../media-ffmpeg-common/PREFLIGHT.md` 的 Step 0-3 完整流程：需求预告 → 确认环境 → 校验输入文件 → 确认输出路径（含父目录可写、输出路径不得与输入路径相同两项校验）。

本 skill 的必需信息：**输入文件路径、起止时间点、输出文件路径**。截取模式（快速/精确）有默认取值（快速），不属于必需信息，缺失不阻塞。

本 skill 在 Step 3 追加确认截取模式：默认使用快速模式；仅当用户明确要求"精确到帧"或对截取点精度有要求时，才使用精确模式。

### Step 4：执行前校验

先执行 media-analyze 对应的 `ffprobe` 命令确认视频总时长，再判断起始/结束时间点是否落在合法区间内：

- **ffprobe 命令本身执行失败（无输出或报错，查不出总时长）**：说明文件可能已损坏或编码格式不受当前 ffmpeg 构建支持，而非时间戳问题。返回错误信息告知用户文件可能已损坏，建议先用 media-analyze 单独排查，终止任务，不进入 Step 5
- **起始或结束时间超过视频总时长**：属于硬约束——截取区间在物理上不存在，无法通过用户确认绕过。返回错误信息告知用户核对时间戳（可参考刚查得的总时长），终止任务，不进入 Step 5

### Step 5：执行截取

**默认模式（快速，流复制）：**

```bash
ffmpeg -y -ss <start> -to <end> -i <input> -c copy <output>
```

**精确模式（重新编码，帧精确）：**

```bash
ffmpeg -y -i <input> -ss <start> -to <end> -c:v libx264 -crf 18 -c:a aac <output>
```

⚠️ **注意：`-ss` 参数在 `-i` 前后位置决定截取行为，不是可以随意调换的写法差异。** 放在 `-i` 之前是输入端 seek（快速模式所用），会对齐到最近的关键帧；放在 `-i` 之后是输出端 seek（精确模式所用），帧精确但速度慢很多。两种模式的命令模板中 `-ss`/`-to` 与 `-i` 的相对顺序不可互换。

`-y` 是全局选项，固定放在命令最前，不参与上述 seek 语义——它位于 `-i` 之前不代表"输入端"含义，也不影响 `-ss` 与 `-i` 的相对位置判断。覆盖策略见 `../media-ffmpeg-common/PREFLIGHT.md` 的「覆盖策略」，不得省略。

> 流复制（`-c copy`）快速模式与转码（重新编码）精确模式的取舍见 [`knowledge-base/media/reference/media-stream-basics.md`](../../../../knowledge-base/media/reference/media-stream-basics.md) §3「转码、重封装、流复制」；"对齐到最近关键帧"中的关键帧概念见 `video-codecs.md` 的「关键帧（I / P / B 帧）与 GOP」小节。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

前置校验（Step 0-3）的失败场景、磁盘空间不足与编码器错误等通用场景见 `../media-ffmpeg-common/PREFLIGHT.md` 的「通用失败处理」；执行中暴露的 ffmpeg 报错见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 处理 |
|---|---|
| 快速模式下截取起点画面出现绿屏/花屏 | 说明是因为对齐到了非关键帧附近，建议改用精确模式重新截取 |

若用户同时提出分辨率转换、压缩体积或帧率转换诉求，不要在本 skill 命令中叠加 `-vf scale`/`-preset`/`-r` 等参数，应分别调用对应 skill；组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"。

## 不要做什么

前置校验相关的通用反例见 `../media-ffmpeg-common/PREFLIGHT.md` 的「不要做什么（前置校验部分）」。以下是本 skill 特有的反例：

- 不要在起始/结束时间超过视频总时长时继续执行，应立即返回错误信息并终止（Step 4，硬约束不可用户确认绕过）
- 不要在 ffprobe 查询总时长本身失败时，误判为时间戳问题并要求用户核对时间戳，应告知文件可能已损坏（Step 4）
- 不要互换 `-ss`/`-to` 与 `-i` 的相对顺序——两种模式的 seek 语义由该顺序决定（Step 5）
- 不要把精确模式命令中固定的 `-crf 18` 当作可调的压缩旋钮——它是本 skill 的固定画质档位，不是压缩手段；用户提出压缩体积诉求时应另行调用 `media-compress`，不在本 skill 命令中叠加 `-preset` 等压缩参数，也不叠加 `-vf scale`/`-r` 等参数，组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"
