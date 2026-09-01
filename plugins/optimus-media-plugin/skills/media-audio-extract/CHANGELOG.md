# Changelog

## [1.0.0] - 2026-09-01

### Added
- 新增 media-audio-extract skill：从视频中提取音频流产出纯音频文件，默认 `-vn -c:a copy` 流复制无损搬运，仅在目标扩展名装不下源音频编码时降级为重新编码
- Step 0-3 前置校验引用 `../media-ffmpeg-common/PREFLIGHT.md`，不重复维护流程骨架
- Step 4 执行前校验三分支：① 源无音频流（硬约束终止）② 源编码与目标扩展名兼容（走流复制）③ 不兼容（🔴 CHECKPOINT 告知可能为二次有损，用户确认后转码），含 7 种常见编码的无损搬运扩展名对照表
- 概念引用指向 `knowledge-base/media/reference/` 的 `audio-container-formats.md`（容器与编码关系、后缀≠编码）、`audio-codecs.md`（编码选型）、`audio-parameters.md`（码率与音质）——此前这三份 reference 无任何 skill 消费
- 「失败处理」含 4 条特有场景（codec tag 报错、音频编码器缺失、多音轨只取 a:0、静音轨）；「不要做什么」含 9 条特有反例
