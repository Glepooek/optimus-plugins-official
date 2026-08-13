---
name: media-trim
description: Use when user wants to cut a specific segment out of a media file — 片段截取、截取视频、剪切一段、掐头去尾、截取某个时间段。Not for resolution changes, compression, or codec/format inspection.
metadata:
  version: "1.0.1"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频片段截取

## 功能概述

从单个音视频文件中截取指定时间段。默认使用流复制（`-c copy`）快速截取，速度极快但会对齐到最近关键帧，实际起止时间可能与用户输入相差数百毫秒；如需帧精确的截取，使用重新编码的精确模式。输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffmpeg` 可用。

### Step 2：确认输出路径与截取模式

向用户确认输出文件路径。默认使用快速模式；仅当用户明确要求"精确到帧"或对截取点精度有要求时，才使用精确模式。

### Step 3：执行截取

**默认模式（快速，流复制）：**

```bash
ffmpeg -ss <start> -to <end> -i <input> -c copy <output>
```

**精确模式（重新编码，帧精确）：**

```bash
ffmpeg -i <input> -ss <start> -to <end> -c:v libx264 -crf 18 -c:a aac <output>
```

⚠️ **注意：`-ss` 参数在 `-i` 前后位置决定截取行为，不是可以随意调换的写法差异。** 放在 `-i` 之前是输入端 seek（快速模式所用），会对齐到最近的关键帧；放在 `-i` 之后是输出端 seek（精确模式所用），帧精确但速度慢很多。两种模式的命令模板中 `-ss`/`-to` 与 `-i` 的相对顺序不可互换。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

除 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表外，本 skill 特有的失败场景：

| 触发条件 | 处理 |
|---|---|
| 起始时间超过视频总时长 | 提示用户核对时间戳，可用 media-analyze skill 先查看视频的准确时长 |
| 快速模式下截取起点画面出现绿屏/花屏 | 说明是因为对齐到了非关键帧附近，建议改用精确模式重新截取 |

若用户同时提出分辨率转换或压缩体积诉求，不要在本 skill 命令中叠加 `-vf scale`/`-crf` 等参数，应分别调用对应 skill；组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"。
