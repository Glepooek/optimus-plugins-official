---
name: media-download
description: Use when user wants to download a single online video or audio by URL — 下载视频、下载这个视频、视频下载、帮我下载这个链接的视频、yt-dlp。Not for playlist/channel batch downloads, content requiring login credentials, or local file transcoding/compression/trimming.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 yt-dlp 并加入 PATH（见下方安装指引），以及 ffmpeg（供 yt-dlp 合并分离的音视频流），参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 在线视频下载

## 功能概述

基于 yt-dlp 下载单个在线视频/音频链接到本地指定路径。下载前先查询该链接所有可用格式供用户选择，不臆测清晰度。仅支持单个链接，不支持播放列表/频道批量下载；仅下载用户本人有权访问且平台允许下载的公开内容，不支持需要登录凭据（cookies）才能访问的内容（会员专享、地区限制等），遇到此类内容直接报错终止，不引导用户配置 cookies。下载完成即任务终态，不自动衔接 media-trim/media-resize/media-compress/media-framerate 等后续处理，如需继续编辑请另行触发对应 skill。

## 使用方法

### Step 0：需求预告

处理用户请求的第一步：对比本 skill 需要的信息与用户在触发语句或上下文中已提供的信息，一次性列出缺失项统一询问，不逐个 Step 反应式追问。

- 需要比对的信息：视频/音频链接 URL、输出保存路径——用户已明确提供的项不重复询问，若这两项已经齐全，跳过本步骤直接进入 Step 1
- 清晰度/格式**不参与本环节比对**：必须先在 Step 4 查询该链接实际可用格式后才能让用户选择，不能在需求预告阶段要求用户凭空报一个可能不存在的清晰度，缺失不阻塞本步骤
- yt-dlp/ffmpeg 依赖是否安装**不参与本环节比对**：这是系统状态而非用户可主动提供的信息，不作为缺失项询问用户，也不影响是否跳过本步骤的判断；依赖状态由 Step 1 实际检测

本步骤不做实际系统调用，仅做信息是否齐全的静态比对。

### Step 1：确认环境

```bash
yt-dlp --version
```

检查失败（命令不存在）：告知用户参考 yt-dlp 官方安装方式（`pip install yt-dlp` 或访问 [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases) 下载对应平台可执行文件），返回错误信息并终止任务，不进入后续步骤。

再执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令确认 `ffmpeg` 可用（yt-dlp 下载到分离的视频流+音频流时需要 ffmpeg 合并封装）。检查失败：引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装，返回错误信息并终止任务。

`yt-dlp` 与 `ffmpeg`/`ffprobe` 是两个独立工具，均需检测通过才能继续，任一缺失都终止任务。

### Step 2：校验输入 URL

检查用户提供的字符串是否为合法 URL 格式（包含协议头 `http://`/`https://` 及基本结构）。这一步是**格式校验**，不是本地文件是否存在的检查——与其他 media-* skill 的"校验输入文件"步骤有本质区别，不要混用判断逻辑。

格式不合法：返回错误信息告知用户核对链接，终止任务，不进入后续步骤。

### Step 3：确认输出路径

🔴 CHECKPOINT：向用户确认保存路径，不得省略直接执行；未确认前不得进入 Step 4。

确认路径后校验其父目录是否存在且可写。父目录不存在或无写权限时返回错误信息告知用户，终止任务；输出文件本身此刻不存在属正常状态，不作为失败条件。

### Step 4：执行前校验

执行以下命令查询该链接所有可用格式：

```bash
yt-dlp -F <url>
```

- **查询失败**（网络错误、站点不支持、链接失效、需要登录凭据）：属于硬约束——无法通过用户确认绕过。如实报告 yt-dlp 返回的具体错误原因，终止任务，不进入 Step 5：
  - 提示 `Unsupported URL`：说明该站点不在 yt-dlp 支持列表内，告知用户并终止，不尝试降级为通用网页抓取
  - 提示需要登录/年龄验证/会员专享等信息（如 `Sign in to confirm your age`）：明确告知用户本 skill 不支持需要登录凭据的内容，终止任务，不引导用户配置 cookies
- **查询成功**：向用户展示 yt-dlp 原生输出的格式列表（含 format id、分辨率、编码、文件大小等），🔴 CHECKPOINT 用户从列表中选择具体 format id 后才能进入 Step 5；用户选择的 format id 不在列表内时，提示核对列表重新选择，不代为猜测最接近的格式。

### Step 5：执行下载

```bash
yt-dlp -f <format_id> -o <output> <url>
```

若所选格式为分离的视频流+音频流，yt-dlp 会自动调用本机 ffmpeg 合并封装，本 skill 不需要手动拼接额外的 ffmpeg 合并命令。

参数说明：`-f` 指定 Step 4 中用户选择的 format id；`-o` 指定 Step 3 确认的输出路径（yt-dlp 语法，支持模板变量，但本 skill 场景下始终传入用户确认的具体路径，不使用模板变量）。

## 失败处理

除 Step 1-4 中已描述的终止条件外，本 skill 特有的失败场景：

| 触发条件 | 处理 |
|---|---|
| 下载中途网络中断 | 如实告知用户下载失败及具体原因，不自动重试；用户可自行决定是否重新触发本 skill |
| 输出路径所在磁盘空间不足 | 如实告知用户 yt-dlp/ffmpeg 报出的磁盘空间错误，终止任务，不做自动清理或换路径重试 |

若用户同时提出下载后的转码/压缩/截取/帧率转换诉求，不在本 skill 中衔接执行，应告知用户下载完成后另行调用 media-trim/media-resize/media-compress/media-framerate 处理；本 skill 不参与 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"顺序编排。

## 不要做什么

- 不要在 yt-dlp 或 ffmpeg 环境检测失败时继续执行，应立即返回错误信息并终止（Step 1）
- 不要在 URL 格式不合法时继续执行，应立即返回错误信息并终止（Step 2）
- 不要在用户未确认输出路径前执行命令（Step 3 的检查点）
- 不要在输出目录不存在或不可写时继续执行，应立即返回错误信息并终止（Step 3）
- 不要跳过 Step 4 的格式查询直接下载"最佳画质"，必须让用户从实际可用列表中选择具体 format id
- 不要在 Step 4 查询格式失败时臆测原因强行重试，应如实报告 yt-dlp 返回的错误信息并终止
- 不要支持播放列表/频道批量下载，仅处理单个视频/音频链接
- 不要支持需要登录凭据（cookies）才能访问的内容，遇到直接报错终止，不引导用户提供 cookies
- 不要在下载完成后自动调用 media-trim/media-resize/media-compress/media-framerate 做后续处理，也不写入组合请求编排链条
