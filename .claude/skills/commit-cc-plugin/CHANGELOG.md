# Changelog

## [3.4.2] - 2026-08-27

### Changed
- Git 提交、分支、PR 与发布规则改为引用 `knowledge-base/git/`，skill 仅保留本仓库专用的发布编排与 checkpoint

## [3.4.1] - 2026-08-27

### Fixed
- 增加 PowerShell 提交信息的正确写法与提交后真实换行校验，明确禁止使用字面量 `\n` 拼接 message

## [3.4.0] - 2026-08-23

### Added
- 第二步扩展到同时维护 `.agents/skills/` 符号链接镜像：检查缺失、自动补齐、清理及暂存均覆盖
  `.kiro/skills/` 与 `.agents/skills/` 两个镜像（本仓库支持 Codex CLI，需在 `.agents/skills/`
  暴露与 kiro 一致的镜像）

## [3.3.0] - 2026-08-04

### Added
- 新增"第五步 — Unpushed 提交检测与 Amend 合并"：写 commit message 前检测当前分支相对
  `origin/master` 是否已有未推送的提交，若有则询问用户是否 amend 合并而非直接新建 commit，
  避免同一逻辑任务被拆成多个碎片提交（借鉴 appskills 仓库 fltrp-git-commit-helper 的
  unpushed 检测设计）
- "常见错误"表补充对应反例行
- 原"第五/六步"顺移为"第六/七步"

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
