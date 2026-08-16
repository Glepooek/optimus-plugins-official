---
name: media-analyze
description: Use when user wants to inspect a media file's codec, resolution, bitrate, frame rate, or duration — 分析视频、分析音频、查看编码格式、查看分辨率码率帧率、这个视频什么编码、ffprobe。Not for editing, converting, compressing, or trimming media.
metadata:
  version: "1.1.2"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg/ffprobe 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频信息分析

## 功能概述

分析单个音视频文件，输出容器格式、视频/音频编码、分辨率、帧率、码率、时长、文件大小。仅支持单文件分析，不支持批量目录扫描。

## 使用方法

### Step 0：需求预告

处理用户请求的第一步：对比本 skill 需要的信息与用户在触发语句或上下文中已提供的信息，一次性列出缺失项统一询问，不逐个 Step 反应式追问。

- 需要比对的信息：输入文件路径——用户已明确提供则跳过本步骤直接进入 Step 1
- ffprobe 依赖是否安装**不参与本环节比对**：这是系统状态而非用户可主动提供的信息，不作为缺失项询问用户，也不影响是否跳过本步骤的判断；依赖状态由 Step 1 实际检测

🔴 **CHECKPOINT**：输入文件路径缺失时，必须在此处停下一次性询问用户，禁止带着缺失信息继续往下执行。

本步骤不做实际系统调用，仅做信息是否齐全的静态比对。

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffprobe` 可用。

⛔ **STOP**：检查失败（命令不存在）时，引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装，返回错误信息并终止任务，不进入后续步骤。

### Step 2：校验输入文件

检查用户提供的输入文件路径是否存在。

⛔ **STOP**：路径不存在时，返回错误信息告知用户核对路径，终止任务，不进入后续步骤。

### Step 3：执行分析

```bash
ffprobe -v quiet -print_format json -show_format -show_streams <input>
```

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

⛔ **STOP**：命令返回非零退出码，或输出 JSON 中 `streams` 为空数组（文件已损坏、格式不受支持、非媒体文件）时，返回错误信息告知用户该文件无法被 ffprobe 解析，终止任务，不进入 Step 4。

### Step 4：整理输出

解析上一步的 JSON 输出，提取以下字段整理为表格展示给用户，不直接把原始 JSON 贴给用户：

| 项目 | 值 |
|---|---|
| 容器格式 | 从 `format.format_name` 提取 |
| 视频编码 | 从视频流 `codec_name` 提取 |
| 分辨率 | 从视频流 `width`x`height` 提取 |
| 帧率 | 从视频流 `r_frame_rate` 计算（如 `30000/1001` → `29.97 fps`） |
| 视频码率 | 从视频流或 `format.bit_rate` 提取，换算为 kbps |
| 音频编码 | 从音频流 `codec_name` 提取 |
| 音频码率 | 从音频流 `bit_rate` 提取，换算为 kbps |
| 时长 | 从 `format.duration` 提取，格式化为 `HH:MM:SS` |
| 文件大小 | 从 `format.size` 提取，换算为可读单位（KB/MB/GB） |

无视频流（纯音频文件）时省略视频相关行；无音频流同理。

流本身存在但某个字段缺失（如 PCM 等无损编码的音频流通常不提供 `bit_rate` 字段）时，与"无该流"是两种不同情况：该字段对应值展示为"未知"，不展示 `undefined`/`null`，也不因单个字段缺失判定为整体解析失败——判定解析失败仅适用于 Step 3 中 `streams` 为空数组的场景。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。

本 skill 为只读查询，可在组合请求（分辨率转换/压缩/截取的组合）中随时按需先行调用以确认原始参数，不参与 `../media-ffmpeg-common/REFERENCE.md` "组合请求处理约定"中的顺序编排。

## 不要做什么

- 不要在 ffprobe 环境检测失败时继续执行，应立即返回错误信息并终止（Step 1）
- 不要在输入文件路径不存在时继续执行，应立即返回错误信息并终止（Step 2）
- 不要在 ffprobe 返回非零退出码或 `streams` 为空时继续解析，应立即返回错误信息并终止（Step 3）
- 不要把原始 JSON 直接贴给用户，应整理为结构化表格（Step 4）
- 不要把"流存在但字段缺失"（如 PCM 音频无 `bit_rate`）误判为整体解析失败或展示为 `undefined`/`null`，应展示"未知"（Step 4）
