---
name: media-resize
description: Use when user wants to change a video's resolution — 分辨率转换、1080p转720p、改分辨率、缩放视频、视频转清晰度。Not for compression at the same resolution, trimming, or codec/format analysis.
metadata:
  version: "1.0.1"
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

🔴 CHECKPOINT：向用户确认或由 Claude 根据上下文给出明确的输出文件路径，不得省略 `-o`/输出参数直接执行；未确认前不得进入 Step 3。

### Step 3：执行前校验

🔴 CHECKPOINT：先无条件执行 media-analyze 对应的 `ffprobe` 命令确认原始分辨率，再判断以下两种情况——命中任一情况都需在执行前主动确认，而非等 ffmpeg 报错后处理，未确认前不得进入 Step 4：

- **放大**：若目标分辨率高于原始分辨率，告知用户放大会损失画质，需用户明确确认后才能继续
- **宽高比不一致**：若用户给出的目标宽高比与原始视频不一致，告知用户画面会被拉伸变形，询问是否改为等比例缩放（用 `-2` 占位一边）；用户坚持强制双边宽高则按指定值执行，但需在执行前明确告知会拉伸变形

### Step 4：执行转换

```bash
ffmpeg -i <input> -vf scale=-2:<目标高度> -c:a copy <output>
```

- `-2` 表示按另一边等比例自动计算并保证结果为偶数，避免用户口头描述"转 720p"时还需手动换算对应宽度
- 常见目标：1080p→720p 用 `scale=-2:720`；720p→480p 用 `scale=-2:480`
- 若用户直接给出目标宽高（而非标准分辨率名称），改为 `scale=<宽>:<高>`
- `-c:a copy`：分辨率转换不涉及音频处理，音频流直接透传，避免不必要的有损重新编码

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 用户直接给出的目标宽或高为奇数，ffmpeg 报 `width/height not divisible by 2` | 改用 `-2` 占位该边，由 ffmpeg 按另一边自动计算偶数值 | 若两边都被用户强制指定为奇数，向用户说明 ffmpeg 编码器要求偶数尺寸，请求放宽其中一边 |

## 不要做什么

- 不要在用户未确认输出路径前执行命令（Step 2 的检查点）
- 不要在用户未确认放大画质损失前直接执行放大命令（Step 3 的检查点）
- 不要在宽高比不一致时静默拉伸画面而不告知用户
- 不要凭空假设输入文件名或路径——用户描述模糊时应先向用户确认具体文件
- 不要在本 skill 的命令中叠加 `-crf`/`-preset` 等压缩参数——用户同时提出压缩体积诉求时，压缩部分应另行调用 `media-compress` skill 处理，组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"
