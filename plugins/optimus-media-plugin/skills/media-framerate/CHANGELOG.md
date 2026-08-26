# Changelog

## [1.0.3] - 2026-08-26

### Changed
- Step 4 提高/降低帧率判断补充概念引用：帧率概念与复制帧/运动插帧/丢帧机制指向 `knowledge-base/media/reference/media-parameters.md` §2「帧率」

## [1.0.2] - 2026-08-17

### Fixed
- 失败处理表补充 Step 5 转换命令本身执行失败的分支（编码器错误、磁盘空间不足）

## [1.0.1] - 2026-08-17

### Fixed
- 失败处理表改为"触发条件 / 一线修复 / 仍失败兜底"三段式，补充输出目录不存在/无写权限、ffprobe 查询失败等此前未覆盖的失败分支

## [1.0.0] - 2026-08-13

### Added
- 新增 media-framerate skill：基于 ffmpeg `-r` 实现视频帧率转换，提高帧率时提供简单复制与 `minterpolate` 运动插帧两种模式供用户选择
