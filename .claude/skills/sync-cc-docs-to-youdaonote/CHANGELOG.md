## [1.0.2] - 2026-07-05

### Changed
- 本地文档按分类路径存储：`docs/claude_docs/<Tab中文名>/<group_zh>/`，而非平铺在 `docs/claude_docs/` 下

## [1.0.1] - 2026-07-05

### Changed
- 上传有道云笔记时，使用文档内容的 `#` 标题作为笔记名，而非文件名

## [1.0.0] - 2026-07-05

### Added
- 初始版本：`resolve_category.py` 提供 `resolve`/`get-folder` 两个子命令
- `folder-map.json` 持久化 Tab/分组/页面的有道文件夹映射与幂等同步记录
- SKILL.md 编排完整的解析→定位文件夹→交叉验证→逐篇同步→汇总报告流程
