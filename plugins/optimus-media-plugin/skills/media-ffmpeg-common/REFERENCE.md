# 环境检测与通用报错处理

## 环境检测

执行任何 media-* skill 的命令前，先确认 ffmpeg/ffprobe 已安装：

```bash
ffmpeg -version && ffprobe -version
```

若提示命令不存在，引导用户参考 `INSTALL.md` 完成安装，不要尝试自动安装。

## 通用报错处理表

| 错误现象 | 原因 | 处理建议 |
|---|---|---|
| `Unknown encoder 'libx264'` | ffmpeg 编译时未包含该编码器 | 执行 `ffmpeg -encoders \| grep x264` 确认，提示用户更换包含完整编码器的发行版（如 Windows 用 gyan.dev 的 full 构建） |
| `Permission denied` | 输出路径无写权限，或目标文件正被其他程序（如播放器）占用 | 确认输出目录存在且当前用户有写权限；关闭占用该文件的程序后重试 |
| `Invalid data found when processing input` | 输入文件已损坏，或格式/编码不受当前 ffmpeg 构建支持 | 先用 media-analyze 对应的 `ffprobe` 命令探测确认文件是否可读 |
| 命令挂起无输出，等待用户输入 | ffmpeg 检测到输出文件已存在，交互式询问是否覆盖 | 命令中加入 `-y`（覆盖）或 `-n`（不覆盖，存在则跳过） |
