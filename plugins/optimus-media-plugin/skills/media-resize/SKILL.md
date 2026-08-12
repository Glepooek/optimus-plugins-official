---
name: media-resize
description: Use when user wants to change a video's resolution — 分辨率转换、1080p转720p、改分辨率、缩放视频、视频转清晰度。Not for compression at the same resolution, trimming, or codec/format analysis.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 视频分辨率转换

## 功能概述

将单个视频文件转换到指定分辨率（如 1080p → 720p），音频流直接透传不重新编码。仅支持单文件，输出路径必须由用户或 Claude 显式指定，不做隐式命名推导。

## 使用方法

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffmpeg` 可用。

### Step 2：确认输出路径

向用户确认或由 Claude 根据上下文给出明确的输出文件路径，不得省略 `-o`/输出参数直接执行。

### Step 3：执行转换

```bash
ffmpeg -i <input> -vf scale=-2:<目标高度> -c:a copy <output>
```

- `-2` 表示按另一边等比例自动计算并保证结果为偶数，避免用户口头描述"转 720p"时还需手动换算对应宽度
- 常见目标：1080p→720p 用 `scale=-2:720`；720p→480p 用 `scale=-2:480`
- 若用户直接给出目标宽高（而非标准分辨率名称），改为 `scale=<宽>:<高>`
- `-c:a copy`：分辨率转换不涉及音频处理，音频流直接透传，避免不必要的有损重新编码

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。
