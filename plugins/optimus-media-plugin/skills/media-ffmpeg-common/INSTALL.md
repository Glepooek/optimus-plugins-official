# ffmpeg / ffprobe 安装与环境变量配置

本仓库的 media-* 系列 skill（media-analyze/media-resize/media-compress/media-trim）依赖用户本机已安装 ffmpeg 与 ffprobe，并加入系统 PATH。以下按平台给出安装步骤。

## Windows

**方式一：winget（推荐）**

```powershell
winget install ffmpeg
```

安装完成后重新打开终端，`ffmpeg`/`ffprobe` 命令即可直接使用（winget 会自动配置 PATH）。

**方式二：手动下载全量构建**

1. 从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下载 `ffmpeg-release-full.7z`，或从 [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) 下载 `ffmpeg-*-win64-gpl.zip`（文件名含版本号/commit hash，非固定文件名；`gyan.dev` 为 `.7z`，`BtbN` 为 `.zip`，解压工具需对应）
2. 解压到固定目录，如 `C:\ffmpeg`
3. 将 `C:\ffmpeg\bin` 加入系统 PATH：
   - 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"系统变量"中找到 `Path`，点击"编辑" → "新建"，填入 `C:\ffmpeg\bin`
   - 确定保存后，重新打开终端生效

## macOS

```bash
brew install ffmpeg
```

## Linux

```bash
# Debian/Ubuntu
sudo apt install ffmpeg

# Fedora/RHEL
sudo dnf install ffmpeg
```

## 验证安装

```bash
ffmpeg -version
ffprobe -version
```

两个命令均应输出版本号（如 `ffmpeg version 6.1...`）。若提示命令不存在，说明安装未完成或 PATH 未生效，请重新打开终端或检查上述步骤。
