# Changelog

## [1.0.0] - 2026-09-01

### Added
- 新增 media-frame-extract skill：从视频提取静态图片，支持单帧模式（指定时间点截一张）与多帧等间隔模式（每 N 秒一张）
- Step 0-3 前置校验引用 `../media-ffmpeg-common/PREFLIGHT.md`，不重复维护流程骨架；必需信息按模式区分
- Step 4 按模式分流校验：单帧模式校验时间点 ≤ 总时长（硬约束终止）；多帧模式预估产出张数，超过 200 张时 🔴 CHECKPOINT 确认（产出数百文件不易撤销）
- Step 5 显式声明本 skill **只有一种 `-ss` 写法**，并解释为何不照搬 media-trim 的快速/精确双模式——trim 的双模式前提是 `-c copy` 不解码只能对齐关键帧，而截图必然解码，`-ss` 置于 `-i` 之前已是帧精确
- 概念引用指向 `knowledge-base/media/reference/` 的 `video-codecs.md`（关键帧与 GOP）、`media-parameters.md` §2（帧率与时间采样）
- 「失败处理」含 5 条特有场景（缺 %03d 只出一个文件、黑场帧、缺 -frames:v 1 导出到结尾、源无视频流、元数据时长偏差）；「不要做什么」含 10 条特有反例
- 明确不做雪碧图（tile 缩略图矩阵）：需额外约定 tile 布局与总帧数匹配关系，不属本 skill 定位
