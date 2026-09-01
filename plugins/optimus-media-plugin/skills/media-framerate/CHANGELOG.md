# Changelog

## [1.0.4] - 2026-09-01

### Fixed
- 两种模式的命令模板均补上 `-y`：Claude 非交互执行下，缺 `-y` 会在输出文件已存在时让 ffmpeg 等待 stdin，结果是静默失败（`Not overwriting - exiting`）或阻塞，且报错原因与"文件已存在"看不出关联。`../media-ffmpeg-common/REFERENCE.md` 与 `CLI-REFERENCE.md` 早已声明该用 `-y`，命令模板未落实
- 「不要做什么」末条修正自相矛盾的表述：原文写"不要在本 skill 命令中叠加 `-crf`"，而两条命令模板本身都带固定的 `-crf 18`，改为区分"固定画质档位"与"作为压缩手段的可调 CRF"；「失败处理」末段的同类表述一并修正

### Changed
- Step 0-3 收敛为引用 `../media-ffmpeg-common/PREFLIGHT.md`，本 skill 只声明必需信息（输入文件路径、目标帧率、输出文件路径）与默认项（转换模式默认简单复制）；Step 4/5 编号不变，不影响正文内既有的 Step 交叉引用
- 「失败处理」三段式表格从 9 行精简为 3 行：其中 4 行（ffmpeg 命令不存在、输入路径不存在、输出目录不存在、输出目录无写权限）与 2 行（磁盘空间不足、编码器错误）本就对全部 media-* skill 通用，已迁入 PREFLIGHT.md 的「通用失败处理」，本文只保留 ffprobe 查询帧率失败与 minterpolate 特有的两项
- 「不要做什么」的前置校验通用条目收敛到 PREFLIGHT.md

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
