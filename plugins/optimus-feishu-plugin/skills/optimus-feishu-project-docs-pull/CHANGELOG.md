## [1.0.0] - 2026-07-12

### Changed
- Skill 由 `optimus-feishu-doc-load` 重命名为 `optimus-feishu-project-docs-pull`，与 `optimus-feishu-project-docs-push` 组成"拉/推"对称命名，明确二者共用同一套部门/项目/版本目录规范
- 修复文末指向不存在的 `optimus-feishu-doc-sync` 的死引用，改为指向 `optimus-feishu-project-docs-push`
