---
name: media-framerate
description: Use when user wants to change a video's frame rate — 帧率转换、改帧率、转帧率、60fps转30fps、提高帧率、降低帧率、补帧。Not for resolution changes, compression, trimming, or codec/format inspection.
metadata:
  version: "1.0.4"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 视频帧率转换

## 功能概述

将单个视频文件转换到指定帧率（如 60fps → 30fps）。降低帧率为丢帧操作，画质无损失；提高帧率默认为简单复制帧，不会让画面更流畅，如需真正提升流畅度需使用运动补偿插帧模式（速度显著更慢）。音频流直接透传不重新编码。仅支持单文件，输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 0-3：前置校验

执行 `../media-ffmpeg-common/PREFLIGHT.md` 的 Step 0-3 完整流程：需求预告 → 确认环境 → 校验输入文件 → 确认输出路径（含父目录可写、输出路径不得与输入路径相同两项校验）。

本 skill 的必需信息：**输入文件路径、目标帧率、输出文件路径**。转换模式（简单复制/运动插帧）有默认取值（简单复制），不属于必需信息，缺失不阻塞。

### Step 4：执行前校验

🔴 CHECKPOINT：先无条件执行 media-analyze 对应的 `ffprobe` 命令确认原始帧率，再判断以下情况——命中需在执行前主动确认，而非等用户看到效果不满意后才解释，未确认前不得进入 Step 5：

- **提高帧率**：若目标帧率高于原始帧率，告知用户简单转换（复制帧）不会让画面更流畅，画面运动感与原始视频一致，仅是元数据层面的帧率变化；如需真正提升流畅度，需使用运动补偿插帧模式（速度显著更慢，且可能引入插值伪影），询问用户选择"简单复制"还是"运动插帧"，默认简单复制
- **降低帧率**：无风险操作（丢帧），无需确认，直接执行

> 帧率概念、提高帧率（复制帧 vs 运动插帧）与降低帧率（丢帧）的机制见 [`knowledge-base/media/reference/media-parameters.md`](../../../../knowledge-base/media/reference/media-parameters.md) §2「帧率」。

### Step 5：执行转换

**默认模式（简单复制/丢帧）：**

```bash
ffmpeg -y -i <input> -r <目标帧率> -c:v libx264 -crf 18 -c:a copy <output>
```

**运动插帧模式（用户选择，仅提高帧率时可用）：**

```bash
ffmpeg -y -i <input> -filter:v "minterpolate=fps=<目标帧率>" -c:v libx264 -crf 18 -c:a copy <output>
```

- `-r <目标帧率>`：设定输出帧率，高于原始帧率时机械复制已有帧凑数，低于原始帧率时均匀丢帧
- `minterpolate=fps=<目标帧率>`：运动补偿插帧滤镜，通过分析相邻帧的运动矢量生成中间帧，仅用于提高帧率场景
- `-crf 18`：帧率转换本身不应引入额外画质损失，取"画质优先"档位，与 media-trim 精确模式的画质取值保持一致
- `-c:a copy`：帧率转换不涉及音频处理，音频流直接透传
- `-y`：覆盖策略见 `../media-ffmpeg-common/PREFLIGHT.md` 的「覆盖策略」，不得省略

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

前置校验（Step 0-3）的失败场景、磁盘空间不足与编码器错误等通用场景见 `../media-ffmpeg-common/PREFLIGHT.md` 的「通用失败处理」；执行中暴露的 ffmpeg 报错见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景，按"触发条件 / 一线修复 / 仍失败兜底"三段式列出：

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| Step 4：ffprobe 查询原始帧率失败或返回空 | 该异常与 media-analyze 判定文件损坏/格式不支持为同一类问题，先按 media-analyze 的失败处理排查该文件是否可读 | media-analyze 判定文件确实无法解析：终止本次帧率转换任务，不得跳过帧率判断直接假设"提高"或"降低"场景 |
| Step 5：运动插帧模式下命令长时间无输出 | 告知用户 `minterpolate` 计算量远高于普通编码，处理时长可能是简单模式的数倍到数十倍，属正常现象 | 用户明确表示无法接受该等待时长：改用简单复制模式重新执行 Step 5 |
| Step 5：运动插帧结果出现画面扭曲/伪影 | 说明运动矢量估算在高速运动、遮挡、场景切换处容易失真，属算法固有局限 | 用户要求消除伪影：告知无法通过调参完全消除，需在"改用简单复制模式"与"接受该权衡"之间二选一 |

若用户同时提出分辨率转换或压缩体积诉求，不要在本 skill 命令中叠加 `-vf scale`/`-preset` 等参数，应分别调用对应 skill；组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"。

## 不要做什么

前置校验相关的通用反例见 `../media-ffmpeg-common/PREFLIGHT.md` 的「不要做什么（前置校验部分）」。以下是本 skill 特有的反例：

- 不要在提高帧率场景下不加说明就默认使用简单复制模式——应先告知用户该模式不会提升流畅度，并询问是否改用运动插帧（Step 4 的检查点）
- 不要把命令中固定的 `-crf 18` 当作可调的压缩旋钮——它是本 skill 的固定画质档位，不是压缩手段；用户提出压缩体积诉求时应另行调用 `media-compress`，不在本 skill 命令中叠加 `-preset` 等压缩参数，也不叠加 `-vf scale` 分辨率参数（分辨率诉求调 `media-resize`），组合请求的执行顺序与方式见 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"
