---
name: media-play
description: Use when user wants to play or preview a media file — 播放视频、播放音频、预览一下这个视频、听一下这段音频、ffplay。Not for editing, converting, compressing, trimming, or codec/format inspection.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffplay（随 ffmpeg 套件提供，部分精简发行版可能未包含）并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md；播放窗口依赖本机图形显示环境，无 GUI 的远程会话无法弹出播放窗口。
allowed-tools: Bash
---

# 音视频播放

## 功能概述

使用 ffplay 播放单个音视频文件，弹出独立播放窗口。仅支持单文件播放，不支持播放列表；不产出任何文件，播放窗口关闭或播放结束即任务完成。

## 使用方法

### Step 0：需求预告

处理用户请求的第一步：对比本 skill 需要的信息与用户在触发语句或上下文中已提供的信息，一次性列出缺失项统一询问，不逐个 Step 反应式追问。

- 需要比对的信息：输入文件路径——用户已明确提供则跳过本步骤直接进入 Step 1
- ffplay 依赖是否安装**不参与本环节比对**：这是系统状态而非用户可主动提供的信息，不作为缺失项询问用户，也不影响是否跳过本步骤的判断；依赖状态由 Step 1 实际检测

本步骤不做实际系统调用，仅做信息是否齐全的静态比对。

### Step 1：确认环境

```bash
ffplay -version
```

检查失败（命令不存在）：引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装，返回错误信息并终止任务，不进入后续步骤。

`ffplay` 与 `ffmpeg`/`ffprobe` 并非同一二进制，部分精简版 ffmpeg 发行包会裁剪掉 `ffplay`，因此不能复用 `../media-ffmpeg-common/REFERENCE.md` 中 `ffmpeg -version && ffprobe -version` 的检测命令，需单独检测。

### Step 2：校验输入文件

检查用户提供的输入文件路径是否存在。不存在时返回错误信息告知用户核对路径，终止任务，不进入后续步骤。

### Step 3：执行播放

```bash
ffplay -window_title "<文件名>" -autoexit <input>
```

使用后台非阻塞方式启动该命令，不等待其退出。启动后告知用户播放窗口已打开，播放结束会自动关闭窗口退出（`-autoexit`），用户也可随时手动关闭窗口提前结束；不得使用前台阻塞方式启动，否则会卡住整个对话直至用户手动关闭播放窗口。

- `-window_title "<文件名>"`：以输入文件名作为窗口标题，便于用户在同时播放多个文件时区分
- `-autoexit`：播放结束后自动关闭窗口，无需用户手动操作

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。以下是本 skill 特有的失败场景：

| 触发条件 | 原因 | 处理建议 |
|---|---|---|
| 提示 SDL 初始化失败 / 无法打开显示设备 | 当前会话无图形显示环境（如无 GUI 的远程终端） | 告知用户 ffplay 需要本机桌面会话才能弹出播放窗口，无图形环境无法使用本 skill |

本 skill 为只读终态操作（不产出文件），可在组合请求（分辨率转换/压缩/截取的组合）中随时按需调用以预览效果，不参与 `../media-ffmpeg-common/REFERENCE.md` "组合请求处理约定"中的顺序编排。

## 不要做什么

- 不要在 ffplay 环境检测失败时继续执行，应立即返回错误信息并终止（Step 1）
- 不要在输入文件路径不存在时继续执行，应立即返回错误信息并终止（Step 2）
- 不要以前台阻塞方式启动 ffplay，应使用后台非阻塞方式并告知用户窗口已打开（Step 3）
- 不要把 `ffplay -version` 检测替换为复用 `ffmpeg -version`/`ffprobe -version`，两者不保证同时存在
