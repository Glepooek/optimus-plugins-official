---
name: media-compress
description: Use when user wants to reduce a media file's size while keeping the same resolution — 压缩视频、压缩音频、音视频压缩、减小文件体积、CRF调画质。Not for resolution changes, clip trimming, or pure codec/format inspection.
metadata:
  version: "1.1.1"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频压缩

## 功能概述

在不改变分辨率的前提下压缩单个音视频文件体积。仅支持 CRF（画质因子）模式，不支持"压缩到指定文件大小"的目标码率模式——后者需要二次编码估算码率，复杂度与当前定位不匹配。输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 0：需求预告

处理用户请求的第一步：对比本 skill 需要的信息与用户在触发语句或上下文中已提供的信息，一次性列出缺失项统一询问，不逐个 Step 反应式追问。

- 需要比对的信息：输入文件路径、输出文件路径——用户已明确提供的项不重复询问，若已经齐全，跳过本步骤直接进入 Step 1；画质偏好描述（如"画质优先"）有默认取值（CRF 23），不属于必需信息，缺失不阻塞
- ffmpeg 依赖是否安装**不参与本环节比对**：这是系统状态而非用户可主动提供的信息，不作为缺失项询问用户，也不影响是否跳过本步骤的判断；依赖状态由 Step 1 实际检测

本步骤不做实际系统调用，仅做信息是否齐全的静态比对。

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffmpeg` 可用。检查失败（命令不存在）：引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装，返回错误信息并终止任务，不进入后续步骤。

### Step 2：校验输入文件

检查用户提供的输入文件路径是否存在。不存在时返回错误信息告知用户核对路径，终止任务，不进入后续步骤。

### Step 3：确认输出路径

🔴 CHECKPOINT：向用户确认或根据上下文给出明确的输出文件路径，不得省略直接执行；未确认前不得进入 Step 4。

确认路径后校验其父目录是否存在且可写。父目录不存在或无写权限时返回错误信息告知用户，终止任务；输出文件本身此刻不存在属正常状态，不作为失败条件。

### Step 4：确定 CRF 取值

默认 CRF 23（视觉无损与体积的常见平衡点）。根据用户口语化描述调整：

| 用户描述 | CRF 取值 |
|---|---|
| 画质优先 / 画质别损失太多 | 18-20 |
| 默认 / 没有特殊要求 | 23 |
| 体积优先 / 压缩狠一点 | 26-28 |

### Step 5：执行压缩

```bash
ffmpeg -i <input> -c:v libx264 -crf <取值> -preset medium -c:a aac -b:a 128k <output>
```

`-preset medium` 是编码速度与压缩率的常见平衡点，用户明确要求"更快"可改为 `fast`，要求"压缩率更高不介意慢"可改为 `slow`。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。

若用户同时提出分辨率转换、片段截取或帧率转换诉求，不要在本 skill 命令中叠加 `-vf scale`/`-ss`/`-to`/`-r` 等参数，应分别调用对应 skill；组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"。

## 不要做什么

- 不要在 ffmpeg 环境检测失败时继续执行，应立即返回错误信息并终止（Step 1）
- 不要在输入文件路径不存在时继续执行，应立即返回错误信息并终止（Step 2）
- 不要在用户未确认输出路径前执行命令（Step 3 的检查点）
- 不要在输出目录不存在或不可写时继续执行，应立即返回错误信息并终止（Step 3）
