---
name: media-play
description: Use when user wants to play or preview a media file — 播放视频、播放音频、预览一下这个视频、听一下这段音频、ffplay。Not for editing, converting, compressing, trimming, or codec/format inspection.
metadata:
  version: "1.2.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffplay（随 ffmpeg 套件提供，部分精简发行版可能未包含）并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md；播放窗口依赖本机图形显示环境，无 GUI 的远程会话无法弹出播放窗口。
allowed-tools: Bash
---

# 音视频播放

## 功能概述

使用 ffplay 播放单个音视频目标，弹出独立播放窗口。支持两种输入形态，执行前必须先明确是哪种：

- **本地文件播放**：播放本机已存在的音视频文件（如 `C:\videos\demo.mp4`），是 skill 的原有能力
- **网络流播放**：播放网络媒体地址（如 `https://.../index.m3u8`、`rtsp://...`、`rtmp://...`），依赖本机 ffmpeg 构建对相应协议的支持；其中 HLS（m3u8）若为含多档清晰度的主清单，支持指定清晰度档位播放，其余协议与本地文件为单档，无清晰度可选

两种形态的校验方式与命令模板不同，不可混用；仅支持单目标播放，不支持播放列表/多文件；不产出任何文件，播放窗口关闭或播放结束即任务完成。网络流协议（HLS/RTSP/RTMP/DASH 等）概念见 [`knowledge-base/media/reference/streaming-protocols.md`](../../../../knowledge-base/media/reference/streaming-protocols.md)；本地文件的容器/编码/流结构见 `media-stream-basics.md` §1。

## 使用方法

### Step 0：需求预告

处理用户请求的第一步：对比本 skill 需要的信息与用户在触发语句或上下文中已提供的信息，一次性列出缺失项统一询问，不逐个 Step 反应式追问。

- 需要比对的信息：播放目标——本地文件路径 或 网络流 URL，用户已明确提供则跳过本步骤直接进入 Step 1
- （网络流且为 HLS/m3u8 时可选）目标清晰度——用户未指定则用 ffplay 默认档位，缺失不阻塞
- ffplay 依赖是否安装**不参与本环节比对**：这是系统状态而非用户可主动提供的信息，不作为缺失项询问用户，也不影响是否跳过本步骤的判断；依赖状态由 Step 1 实际检测

本步骤不做实际系统调用，仅做信息是否齐全的静态比对。

### Step 1：确认环境

```bash
ffplay -version
```

检查失败（命令不存在）：引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装，返回错误信息并终止任务，不进入后续步骤。

`ffplay` 与 `ffmpeg`/`ffprobe` 并非同一二进制，部分精简版 ffmpeg 发行包会裁剪掉 `ffplay`，因此不能复用 `../media-ffmpeg-common/REFERENCE.md` 中 `ffmpeg -version && ffprobe -version` 的检测命令，需单独检测。

### Step 2：确认播放目标类型并校验

先判断播放目标类型，再走对应的校验路径——本地文件与网络流是两种不同的输入形态，不可混用：

- **判断依据**：输入含 `://` 协议头（`http://`、`https://`、`rtsp://`、`rtmp://` 等）视为**网络流 URL**，否则视为**本地文件路径**
- **本地文件**：检查路径是否存在。不存在时返回错误信息告知用户核对路径，终止任务，不进入后续步骤
- **网络流 URL**：检查是否为合法 URL 格式（含协议头及基本结构），并明确告知用户本次为**网络流播放**；若 Step 0 给出了清晰度偏好，记录该偏好供 Step 3 使用。不做本地文件存在性校验（网络流不存在于本地文件系统）；地址能否真正解析/连接由 Step 3 运行时暴露，属失败处理范畴

### Step 3：执行播放

按 Step 2 确认的播放目标类型选择对应命令模板，启动前向用户明确指出本次是**本地文件播放**还是**网络流播放**：

**本地文件播放：**

```bash
ffplay -window_title "<文件名>" -autoexit <input>
```

**网络流播放：**

HLS（m3u8）按是否指定清晰度分两种命令；RTMP/RTSP 为单档流，直接播：

```bash
# HLS 未指定清晰度（ffplay 默认播主清单中的第一个档位）
ffplay -window_title "<流标题>" -autoexit "https://.../master.m3u8"

# HLS 指定清晰度：先探测主清单的所有视频档位，再按档位序号播放（v:<n> 为第 n 个视频流，0 基）
ffprobe -v error -show_streams -select_streams v "https://.../master.m3u8"
ffplay -window_title "<流标题>" -vst v:<n> -ast a:<n> -autoexit "https://.../master.m3u8"

# RTMP（rtmp://...）与 RTSP（摄像头等，rtsp://...）—— RTSP 建议加 -rtsp_transport tcp
ffplay -window_title "<流标题>" -autoexit "rtmp://..."
ffplay -window_title "<流标题>" -rtsp_transport tcp -autoexit "rtsp://..."
```

使用后台非阻塞方式启动该命令，不等待其退出。启动后告知用户播放窗口已打开、本次为本地文件或网络流播放，播放结束会自动关闭窗口退出（`-autoexit`），用户也可随时手动关闭窗口提前结束；不得使用前台阻塞方式启动，否则会卡住整个对话直至用户手动关闭播放窗口。

- `-window_title "<文件名>"`：以输入文件名作为窗口标题，便于用户在同时播放多个文件时区分；网络流取 URL 末尾路径段作为流标题（如 `index.m3u8`）
- `-autoexit`：播放结束后自动关闭窗口，无需用户手动操作。注意直播流不结束，`-autoexit` 不会自动触发，由用户手动关闭窗口
- `-vst v:<n>` / `-ast a:<n>`：选择第 n 个视频流及同档音频流（HLS 主清单里每个清晰度档是一个 variant，各含一条视频流 + 一条音频流，序号 0 基，`v:0` 为第一个视频流）。不指定时 ffplay 播主清单中第一个 variant
- **清晰度选择的适用范围**：仅对 HLS（m3u8）多档主清单有效——本地文件、HTTP 直链 mp4、RTMP/RTSP 均为单档流，没有多档变体可供选择，加 `-vst`/`-ast` 无意义
- **档位匹配**：ffprobe 探测（`-select_streams v`）后按输出顺序列出各档分辨率（如 720p、480p、288p），用户口语描述（"720p""最高清晰度""低清"）就近匹配最接近的一档，取该档序号作为 `<n>`；用户未指定清晰度时不探测、不传 `-vst`/`-ast`
- RTSP 默认走 UDP 传输，弱网下丢包易花屏，加 `-rtsp_transport tcp` 改为 TCP 传输
- 直播流是实时的，不能往回拖进度条；DRM（Widevine/FairPlay 等）加密内容 ffplay 无法解密播放

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`；网络流协议细节见 [`knowledge-base/media/reference/streaming-protocols.md`](../../../../knowledge-base/media/reference/streaming-protocols.md) §8「与 ffprobe / ffplay 的关系」。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 原因 | 处理建议 |
|---|---|---|
| 提示 SDL 初始化失败 / 无法打开显示设备 | 当前会话无图形显示环境（如无 GUI 的远程终端） | 告知用户 ffplay 需要本机桌面会话才能弹出播放窗口，无图形环境无法使用本 skill |
| 网络流报连接失败 / 无法解析 URL | 地址失效、站点不可达或需登录鉴权 | 告知用户核对 URL 与网络状态，本 skill 不支持需登录凭据的流；不自动重试 |
| RTSP 播放花屏 / 卡顿 | 默认 UDP 传输在弱网下丢包 | 改用 `-rtsp_transport tcp` 重试 |
| RTMP 提示协议不支持（`Unknown protocol`） | 当前 ffmpeg 构建未包含 RTMP 支持 | 说明需安装含 RTMP 协议的 ffmpeg 构建，或改用 HLS 地址 |
| DRM 加密流无法播放 | Widevine/FairPlay 等版权保护 ffplay 无法解密 | 告知用户该内容受 DRM 保护，本 skill 无法播放 |
| HLS 指定清晰度时 ffprobe 探测失败 | 主清单无法解析（非 HLS/损坏/需鉴权） | 说明该地址无法探测出清晰度档位，询问是否直接默认播放 |
| 直播流拖动进度条无效 | 实时流只播当前时刻，无历史缓冲 | 说明直播流不可回拖，属正常现象 |

本 skill 为只读终态操作（不产出文件），可在组合请求（分辨率转换/压缩/截取的组合）中随时按需调用以预览效果，不参与 `../media-ffmpeg-common/REFERENCE.md` "组合请求处理约定"中的顺序编排。

## 不要做什么

- 不要在 ffplay 环境检测失败时继续执行，应立即返回错误信息并终止（Step 1）
- 不要对网络流 URL 做本地文件存在性校验——网络流不存在于本地文件系统，应做 URL 格式校验（Step 2）
- 不要把网络流 URL 当作本地文件路径处理，命令模板与校验路径必须按类型区分（Step 2/Step 3）
- 不要以前台阻塞方式启动 ffplay，应使用后台非阻塞方式并告知用户窗口已打开（Step 3）
- 不要把 `ffplay -version` 检测替换为复用 `ffmpeg -version`/`ffprobe -version`，两者不保证同时存在
- 不要对直播流声称可回拖进度条、不要对 DRM 加密流承诺可播放
- 不要对本地文件、HTTP 直链 mp4、RTMP/RTSP 使用 `-vst`/`-ast` 选清晰度——这些均为单档流，无多档变体
- 不要臆测 HLS 档位序号——必须先经 ffprobe 探测确认各档分辨率后再匹配 `<n>`
