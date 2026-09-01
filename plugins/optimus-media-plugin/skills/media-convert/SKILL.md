---
name: media-convert
description: Use when user wants to change a media file's container format — 格式转换、转成mp4、转成mov、转换容器、mp4转mkv、avi转mp4、换个格式。Not for resolution changes, frame rate changes, compression at the same format, trimming, or pure audio format conversion (that is media-audio-convert).
metadata:
  version: "1.0.3"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频格式转换

## 功能概述

将单个音视频文件转换到指定容器格式（如 mp4↔mov↔mkv↔avi）。默认使用流复制（remux，`-c copy`）不重新编码，速度快且无画质损失；仅当目标容器不支持源文件的编码时才降级为重新编码（转码）。仅支持单文件，输出路径必须由用户或 Claude 显式指定。

本 skill 只处理**视频容器**格式转换。纯音频到纯音频的格式转换（如 wav→mp3、flac→aac）由 `media-audio-convert` 承接；从视频中提取音轨由 `media-audio-extract` 承接——两者的输入输出形态与判断逻辑都与本 skill 不同，不在此扩展。

## 使用方法

### Step 0-3：前置校验

执行 `../media-ffmpeg-common/PREFLIGHT.md` 的 Step 0-3 完整流程：需求预告 → 确认环境 → 校验输入文件 → 确认输出路径（含父目录可写、输出路径不得与输入路径相同两项校验）。

本 skill 的必需信息：**输入文件路径、目标格式、输出文件路径**。

本 skill 在 Step 3 追加要求：输出文件的扩展名须与用户要求的目标格式一致。

### Step 4：执行转换

**默认先尝试 remux 模式（流复制，不重新编码）：**

```bash
ffmpeg -y -i <input> -c copy <output>
```

- **remux 成功**：任务完成，无画质损失。
- **remux 失败**（报错如 `Could not find tag for codec` / `codec not currently supported in container` 等编码与目标容器不兼容的信息）：说明目标容器不支持源文件的编码，无法仅靠改变封装完成转换。🔴 CHECKPOINT 告知用户"目标格式不支持当前编码，需要重新编码才能转换，会产生一次有损压缩（画质会有轻微损失）"，询问用户是否接受转码继续，还是改选其他目标格式；用户确认接受转码后才能进入下方转码模式，未确认不得继续。

> remux（重封装）/ 转码 / 流复制三者的区别与"容器≠编码"概念见 [`knowledge-base/media/reference/media-stream-basics.md`](../../../../knowledge-base/media/reference/media-stream-basics.md) §3「转码、重封装、流复制」。

**转码模式（remux 失败且用户确认后）：**

```bash
ffmpeg -y -i <input> -c:v libx264 -crf 18 -c:a aac <output>
```

- `-crf 18`：格式转换本身不应引入明显额外画质损失，取"画质优先"档位，与 media-trim 精确模式、media-framerate 的画质取值保持一致
- `-y`：覆盖策略见 `../media-ffmpeg-common/PREFLIGHT.md` 的「覆盖策略」，remux 与转码两条命令均不得省略
- 转码模式若仍失败（非编码兼容性原因，如文件本身损坏），参见"失败处理"

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

前置校验（Step 0-3）的失败场景、磁盘空间不足与编码器错误等通用场景见 `../media-ffmpeg-common/PREFLIGHT.md` 的「通用失败处理」；执行中暴露的 ffmpeg 报错见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 原因 | 处理建议 |
|---|---|---|
| remux 命令报编码与容器不兼容 | 目标容器格式不支持源文件的视频/音频编码 | Step 4 的 CHECKPOINT 流程：告知用户需要转码，用户确认后降级为重新编码模式 |
| 转码模式仍报 `Invalid data found when processing input` | 输入文件本身已损坏或编码不受当前 ffmpeg 构建支持，与容器兼容性无关 | 建议先用 media-analyze 排查该文件是否可正常解析 |

若用户同时提出分辨率转换、压缩体积、片段截取或帧率转换诉求，不要在本 skill 命令中叠加 `-vf scale`/`-crf`（压缩用途）/`-ss`/`-to`/`-r` 等参数，应分别调用对应 skill；组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"——本 skill 在该顺序中位于末位。

## 不要做什么

前置校验相关的通用反例见 `../media-ffmpeg-common/PREFLIGHT.md` 的「不要做什么（前置校验部分）」。以下是本 skill 特有的反例：

- 不要在 remux 失败时未经用户确认就直接静默切换为转码模式——必须先告知会产生画质损失（Step 4 的检查点）
- 不要凭空维护一份容器/编码兼容性对照表预判是否需要转码——直接尝试 remux，以实际报错结果驱动降级判断
- 不要支持纯音频格式转换（如 wav→mp3、flac→aac）——那是 `media-audio-convert` 的职责，本 skill 仅处理视频容器格式转换；用户提出纯音频转换诉求时，告知调用 `media-audio-convert`，不要为此放开 remux-first 逻辑去兼容纯音频
- 不要承接从视频提取音轨的诉求（如"把这个 mp4 转成 mp3"实际是想要音频）——那是 `media-audio-extract` 的职责；识别到用户想要的是纯音频产出而非换容器时，转交对应 skill
- 不要在本 skill 的命令中叠加 `-vf scale`/`-crf`（压缩用途）/`-ss`/`-to`/`-r` 等参数——用户同时提出分辨率/压缩/截取/帧率诉求时，应分别另行调用对应 skill，组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"
