---
name: media-convert
description: Use when user wants to change a media file's container format — 格式转换、转成mp4、转成mov、转换容器、mp4转mkv、avi转mp4、换个格式。Not for resolution changes, frame rate changes, compression at the same format, or trimming.
metadata:
  version: "1.0.1"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频格式转换

## 功能概述

将单个音视频文件转换到指定容器格式（如 mp4↔mov↔mkv↔avi）。默认使用流复制（remux，`-c copy`）不重新编码，速度快且无画质损失；仅当目标容器不支持源文件的编码时才降级为重新编码（转码）。仅支持单文件，不支持纯音频格式转换（如 wav→mp3），输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 0：需求预告

处理用户请求的第一步：对比本 skill 需要的信息与用户在触发语句或上下文中已提供的信息，一次性列出缺失项统一询问，不逐个 Step 反应式追问。

- 需要比对的信息：输入文件路径、目标格式、输出文件路径——用户已明确提供的项不重复询问，若这三项已经齐全，跳过本步骤直接进入 Step 1
- ffmpeg 依赖是否安装**不参与本环节比对**：这是系统状态而非用户可主动提供的信息，不作为缺失项询问用户，也不影响是否跳过本步骤的判断；依赖状态由 Step 1 实际检测

本步骤不做实际系统调用，仅做信息是否齐全的静态比对。

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffmpeg` 可用。检查失败（命令不存在）：引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装，返回错误信息并终止任务，不进入后续步骤。

### Step 2：校验输入文件

检查用户提供的输入文件路径是否存在。不存在时返回错误信息告知用户核对路径，终止任务，不进入后续步骤。

### Step 3：确认输出路径

🔴 CHECKPOINT：向用户确认或根据上下文给出明确的输出文件路径，不得省略直接执行；未确认前不得进入 Step 4。输出文件的扩展名须与用户要求的目标格式一致。

确认路径后校验其父目录是否存在且可写。父目录不存在或无写权限时返回错误信息告知用户，终止任务；输出文件本身此刻不存在属正常状态，不作为失败条件。

### Step 4：执行转换

**默认先尝试 remux 模式（流复制，不重新编码）：**

```bash
ffmpeg -i <input> -c copy <output>
```

- **remux 成功**：任务完成，无画质损失。
- **remux 失败**（报错如 `Could not find tag for codec` / `codec not currently supported in container` 等编码与目标容器不兼容的信息）：说明目标容器不支持源文件的编码，无法仅靠改变封装完成转换。🔴 CHECKPOINT 告知用户"目标格式不支持当前编码，需要重新编码才能转换，会产生一次有损压缩（画质会有轻微损失）"，询问用户是否接受转码继续，还是改选其他目标格式；用户确认接受转码后才能进入下方转码模式，未确认不得继续。

> remux（重封装）/ 转码 / 流复制三者的区别与"容器≠编码"概念见 [`knowledge-base/media/reference/media-stream-basics.md`](../../../../knowledge-base/media/reference/media-stream-basics.md) §3「转码、重封装、流复制」。

**转码模式（remux 失败且用户确认后）：**

```bash
ffmpeg -i <input> -c:v libx264 -crf 18 -c:a aac <output>
```

- `-crf 18`：格式转换本身不应引入明显额外画质损失，取"画质优先"档位，与 media-trim 精确模式、media-framerate 的画质取值保持一致
- 转码模式若仍失败（非编码兼容性原因，如文件本身损坏），参见"失败处理"

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 原因 | 处理建议 |
|---|---|---|
| remux 命令报编码与容器不兼容 | 目标容器格式不支持源文件的视频/音频编码 | Step 4 的 CHECKPOINT 流程：告知用户需要转码，用户确认后降级为重新编码模式 |
| 转码模式仍报 `Invalid data found when processing input` | 输入文件本身已损坏或编码不受当前 ffmpeg 构建支持，与容器兼容性无关 | 建议先用 media-analyze 排查该文件是否可正常解析 |

若用户同时提出分辨率转换、压缩体积、片段截取或帧率转换诉求，不要在本 skill 命令中叠加 `-vf scale`/`-crf`（压缩用途）/`-ss`/`-to`/`-r` 等参数，应分别调用对应 skill；组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"——本 skill 在该顺序中位于末位。

## 不要做什么

- 不要在 ffmpeg 环境检测失败时继续执行，应立即返回错误信息并终止（Step 1）
- 不要在输入文件路径不存在时继续执行，应立即返回错误信息并终止（Step 2）
- 不要在用户未确认输出路径前执行命令（Step 3 的检查点）
- 不要在输出目录不存在或不可写时继续执行，应立即返回错误信息并终止（Step 3）
- 不要在 remux 失败时未经用户确认就直接静默切换为转码模式——必须先告知会产生画质损失（Step 4 的检查点）
- 不要凭空维护一份容器/编码兼容性对照表预判是否需要转码——直接尝试 remux，以实际报错结果驱动降级判断
- 不要支持纯音频格式转换（如 wav→mp3、flac→aac），仅处理音视频容器格式转换
- 不要在本 skill 的命令中叠加 `-vf scale`/`-crf`（压缩用途）/`-ss`/`-to`/`-r` 等参数——用户同时提出分辨率/压缩/截取/帧率诉求时，应分别另行调用对应 skill，组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"
