# Changelog

## [3.2.0] - 2026-07-11

### Added
- 新增"第二步 — 补齐 .kiro/skills 符号链接"：仅当本次改动包含 `.claude/skills/`
  下 SKILL.md 的新增或删除时触发（GATE门禁，避免每次提交都做无谓检查），
  自动检测缺失的符号链接并补齐（新增skill）或清理（删除skill），纳入本次提交
- "常见错误"表补充对应反例行

## [3.1.4] - 2026-07-11

### Fixed
- Co-Authored-By 原硬编码"Claude Sonnet 4.6 (1M context)"，与实际使用的模型不符；改为要求填写当前会话实际使用的模型名

## [3.1.3] - 2026-07-11

### Changed
- 随全仓库 unipus 前缀重命名为 optimus 同步更新（机械性文本替换，无行为变更）

## [3.1.2] - 2026-06-30

### Removed
- 移除 disable-model-invocation 限制

## [3.1.1] - 2026-06-26

### Changed
- "常见错误"表补充 force push 和 --no-verify 反例

## [3.1.0] - 2026-06-26

### Added
- 第一步"遗留暂存文件处理"检查点
- 第三步"原子性自查三问"加 🔴 CHECKPOINT 显性标记

## [3.0.1] - 2026-06-23

### Fixed
- 修复 disable-model-invocation 的 YAML 格式错误

## [3.0.0] - 2026-06-19

### Changed
- Skill 重命名：`publish-cc-plugin` → `commit-cc-plugin`（破坏性变更，需使用新名称调用）

## [2.0.0] - 2026-06-19

### Changed
- Skill 重命名：`unipus-commit` → `publish-cc-plugin`（破坏性变更，需使用新名称调用），精简步骤结构

## [1.0.0] - 2026-05-29

### Added
- 初始创建（原名 `unipus-commit`），本仓库专用发布工作流：版本决策、选择性暂存、提交、推送
