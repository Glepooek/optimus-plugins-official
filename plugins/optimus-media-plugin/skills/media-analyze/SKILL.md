---
name: media-analyze
description: Use when user wants to inspect a media file's codec, resolution, bitrate, frame rate, or duration — 分析视频、分析音频、查看编码格式、查看分辨率码率帧率、这个视频什么编码、ffprobe。Not for editing, converting, compressing, or trimming media.
metadata:
  version: "1.0.1"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg/ffprobe 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频信息分析

## 功能概述

分析单个音视频文件，输出容器格式、视频/音频编码、分辨率、帧率、码率、时长、文件大小。仅支持单文件分析，不支持批量目录扫描。

## 使用方法

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffprobe` 可用。若不可用，引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装。

### Step 2：执行分析

```bash
ffprobe -v quiet -print_format json -show_format -show_streams <input>
```

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

### Step 3：整理输出

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

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。

本 skill 为只读查询，可在组合请求（分辨率转换/压缩/截取的组合）中随时按需先行调用以确认原始参数，不参与 `../media-ffmpeg-common/REFERENCE.md` "组合请求处理约定"中的顺序编排。
