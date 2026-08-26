# Changelog

## [1.0.1] - 2026-08-26

### Changed
- Step 4 remux/转码说明补充概念引用：remux（重封装）/ 转码 / 流复制三者的区别与"容器≠编码"指向 `knowledge-base/media/reference/media-stream-basics.md` §3

## [1.0.0] - 2026-08-19

### Added
- 新增 media-convert skill：基于 ffmpeg 实现音视频容器格式转换，默认流复制（remux）不重新编码，目标容器不支持源编码时经用户确认后降级为重新编码（转码）模式
