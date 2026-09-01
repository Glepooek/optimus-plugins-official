# Changelog

## [1.0.3] - 2026-09-01

### Changed
- 边界声明改为指向新增的音频 skill：概述与「不要做什么」中原先只写"不支持纯音频格式转换"（一个没有承接者的空边界），现明确纯音频转换转交 `media-audio-convert`、视频提取音轨转交 `media-audio-extract`
- description 的 "Not for ..." 补充 `pure audio format conversion (that is media-audio-convert)`，让触发阶段就能正确分流
- 「不要做什么」新增一条：识别到用户实际想要纯音频产出（如"把这个 mp4 转成 mp3"）而非换容器时，应转交 `media-audio-extract`，不在本 skill 内兼容

## [1.0.2] - 2026-09-01

### Fixed
- remux 模式与转码模式的命令模板均补上 `-y`：Claude 非交互执行下，缺 `-y` 会在输出文件已存在时让 ffmpeg 等待 stdin，结果是静默失败（`Not overwriting - exiting`）或阻塞。本 skill 受影响尤其明显——remux 失败后降级转码时，第一次 remux 尝试可能已在输出路径留下残留文件，缺 `-y` 会让转码这一步撞上"文件已存在"而卡住，表现为"用户确认转码后却什么都没发生"

### Changed
- Step 0-3 收敛为引用 `../media-ffmpeg-common/PREFLIGHT.md`，本 skill 只声明必需信息（输入文件路径、目标格式、输出文件路径）与 Step 3 的追加要求（输出扩展名须与目标格式一致）；Step 4 编号不变，不影响正文内既有的 Step 交叉引用
- 「失败处理」「不要做什么」的通用条目收敛到 PREFLIGHT.md，本文只保留特有场景

## [1.0.1] - 2026-08-26

### Changed
- Step 4 remux/转码说明补充概念引用：remux（重封装）/ 转码 / 流复制三者的区别与"容器≠编码"指向 `knowledge-base/media/reference/media-stream-basics.md` §3

## [1.0.0] - 2026-08-19

### Added
- 新增 media-convert skill：基于 ffmpeg 实现音视频容器格式转换，默认流复制（remux）不重新编码，目标容器不支持源编码时经用户确认后降级为重新编码（转码）模式
