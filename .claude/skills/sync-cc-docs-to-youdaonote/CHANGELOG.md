## [1.2.1] - 2026-07-12

### Fixed
- Step 0 询问模板按 `never_checked`/`stale` 分开措辞，避免 `days_since_verified` 为
  `null` 时机械套用天数模板产生"已经 null 天"这种不通顺话术（darwin-skill 实测发现）

## [1.2.0] - 2026-07-12

### Added
- 新增 `scripts/finalize_page.py`：把 Step 4 里 post_process → verify → verify_quality →
  上传 → 更新 folder-map.json → 清理临时文件这条确定性收尾链路封装成一次脚本调用，
  避免手动逐步执行时漏掉清理/更新步骤；任一环节失败原样停止，不清理现场
- `resolve_category.py` 的 `resolve` 命令在 Tab/分组名找不到时，用 `difflib` 模糊匹配
  给出候选名提示，减少来回翻 catalog.md 核对拼写

## [1.1.0] - 2026-07-12

### Added
- 新增 Step 0：`catalog.md` 过期检测（默认 14 天阈值），到期后先询问用户是否重新核对
  站点导航，用户同意才抓取，抓取后生成 diff 报告，用户确认才覆写——全程不做无提示的
  自动抓取或自动覆写
- 新增 `scripts/catalog_freshness.py`：`check-freshness`/`record-check`/`diff-catalog`/
  `apply-diff` 四个子命令，`apply-diff` 以 `(tab_en, url)` 为 key 复用旧文件原始整行
  文本，保留 `[x]`/`[ ]` 完成标记与行尾批注，不做"parse → 重新序列化"
- 新增 `data/catalog-check-meta.json` 记录上次核对/询问时间

### Changed
- `folder-map.json` 迁移到 `data/folder-map.json`，与新增的过期检测状态文件归入同一目录

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
