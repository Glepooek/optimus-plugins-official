---
name: media-compress
description: Use when user wants to reduce a media file's size while keeping the same resolution — 压缩视频、压缩音频、音视频压缩、减小文件体积、CRF调画质。Not for resolution changes, clip trimming, or pure codec/format inspection.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频压缩

## 功能概述

在不改变分辨率的前提下压缩单个音视频文件体积。仅支持 CRF（画质因子）模式，不支持"压缩到指定文件大小"的目标码率模式——后者需要二次编码估算码率，复杂度与当前定位不匹配。输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffmpeg` 可用。

### Step 2：确认输出路径

向用户确认或根据上下文给出明确的输出文件路径。

### Step 3：确定 CRF 取值

默认 CRF 23（视觉无损与体积的常见平衡点）。根据用户口语化描述调整：

| 用户描述 | CRF 取值 |
|---|---|
| 画质优先 / 画质别损失太多 | 18-20 |
| 默认 / 没有特殊要求 | 23 |
| 体积优先 / 压缩狠一点 | 26-28 |

### Step 4：执行压缩

```bash
ffmpeg -i <input> -c:v libx264 -crf <取值> -preset medium -c:a aac -b:a 128k <output>
```

`-preset medium` 是编码速度与压缩率的常见平衡点，用户明确要求"更快"可改为 `fast`，要求"压缩率更高不介意慢"可改为 `slow`。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。
