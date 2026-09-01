---
name: media-resize
description: Use when user wants to change a video's resolution — 分辨率转换、1080p转720p、改分辨率、缩放视频、视频转清晰度。Not for compression at the same resolution, trimming, or codec/format analysis.
metadata:
  version: "1.2.4"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 视频分辨率转换

## 功能概述

将单个视频文件转换到指定分辨率（如 1080p → 720p）。`-vf scale` 缩放必然触发视频流重新编码（取"画质优先"档位 CRF 18），音频流直接透传不重新编码。仅支持单文件，输出路径必须由用户或 Claude 显式指定，不做隐式命名推导。

## 使用方法

### Step 0-3：前置校验

执行 `../media-ffmpeg-common/PREFLIGHT.md` 的 Step 0-3 完整流程：需求预告 → 确认环境 → 校验输入文件 → 确认输出路径（含父目录可写、输出路径不得与输入路径相同两项校验）。

本 skill 的必需信息：**输入文件路径、目标分辨率、输出文件路径**。

### Step 4：执行前校验

先无条件执行 media-analyze 对应的 `ffprobe` 命令确认原始分辨率：

- **ffprobe 命令本身执行失败（无输出或报错，查不出原始分辨率）**：说明文件可能已损坏或编码格式不受当前 ffmpeg 构建支持，而非放大/宽高比判断问题。返回错误信息告知用户文件可能已损坏，建议先用 media-analyze 单独排查，终止任务，不进入 Step 5

ffprobe 查询成功后，🔴 CHECKPOINT：判断以下两种情况——命中任一情况都需在执行前主动确认，而非等 ffmpeg 报错后处理，未确认前不得进入 Step 5：

- **放大**：若目标分辨率高于原始分辨率，告知用户放大会损失画质，需用户明确确认后才能继续
- **宽高比不一致**：若用户给出的目标宽高比与原始视频不一致，告知用户画面会被拉伸变形，询问是否改为等比例缩放（用 `-2` 占位一边）；用户坚持强制双边宽高则按指定值执行，但需在执行前明确告知会拉伸变形

> 分辨率档位、宽高比与横/竖屏判定等概念见 [`knowledge-base/media/reference/media-parameters.md`](../../../../knowledge-base/media/reference/media-parameters.md) §1「分辨率」。

### Step 5：执行转换

```bash
ffmpeg -y -i <input> -vf scale=-2:<目标高度> -c:v libx264 -crf 18 -c:a copy <output>
```

- `-2` 表示按另一边等比例自动计算并保证结果为偶数，避免用户口头描述"转 720p"时还需手动换算对应宽度
- 常见目标：1080p→720p 用 `scale=-2:720`；720p→480p 用 `scale=-2:480`
- 若用户直接给出目标宽高（而非标准分辨率名称），改为 `scale=<宽>:<高>`
- `-c:v libx264 -crf 18`：`-vf scale` 必然触发视频重新编码，显式指定编码器与画质档位，不依赖 ffmpeg 按输出容器推断默认值（输出为 `.mkv` 等容器时默认编码器可能并非 libx264）；`-crf 18` 取"画质优先"档位，与 media-framerate、media-trim 精确模式、media-convert 转码模式的取值保持一致
- `-c:a copy`：分辨率转换不涉及音频处理，音频流直接透传，避免不必要的有损重新编码
- `-y`：覆盖策略见 `../media-ffmpeg-common/PREFLIGHT.md` 的「覆盖策略」，不得省略

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

前置校验（Step 0-3）的失败场景与通用 ffmpeg 报错见 `../media-ffmpeg-common/PREFLIGHT.md` 的「通用失败处理」与 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 用户直接给出的目标宽或高为奇数，ffmpeg 报 `width/height not divisible by 2` | 改用 `-2` 占位该边，由 ffmpeg 按另一边自动计算偶数值 | 若两边都被用户强制指定为奇数，向用户说明 ffmpeg 编码器要求偶数尺寸，请求放宽其中一边 |

## 不要做什么

前置校验相关的通用反例见 `../media-ffmpeg-common/PREFLIGHT.md` 的「不要做什么（前置校验部分）」。以下是本 skill 特有的反例：

- 不要在 ffprobe 查询原始分辨率本身失败时，误判为放大/宽高比问题并要求用户核对目标分辨率，应告知文件可能已损坏（Step 4）
- 不要在用户未确认放大画质损失前直接执行放大命令（Step 4 的检查点）
- 不要在宽高比不一致时静默拉伸画面而不告知用户
- 不要凭空假设输入文件名或路径——用户描述模糊时应先向用户确认具体文件
- 不要省略命令中的 `-c:v libx264`，让 ffmpeg 按输出容器推断编码器——缩放必然重新编码，编码器与画质档位必须显式指定
- 不要把命令中固定的 `-crf 18` 当作可调的压缩旋钮——它是本 skill 的固定画质档位，不是压缩手段；用户提出压缩体积诉求时应另行调用 `media-compress`，不在本 skill 命令中叠加 `-preset` 等压缩参数，也不叠加 `-r`/`minterpolate` 等帧率参数（帧率诉求调 `media-framerate`），组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"
