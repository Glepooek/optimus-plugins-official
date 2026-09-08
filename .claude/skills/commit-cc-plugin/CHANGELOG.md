# Changelog

## [4.0.0] - 2026-09-08

### Removed
- **第二步「版本号决策」整节移出**（含落点判断、两份同步、阻断式校验、「白名单冲突」元流程共 48 行）：版本一致性失效损害的是仓库长期状态而非本次提交，且原实现要求 LLM 逐行读并自觉执行——Codex 侧走标准 git 时完全不生效。校验脚本迁至 `.githooks/`，由 `pre-commit` 强制执行
- **§A「补齐符号链接」条件小节移出**（36 行）：同上，改由 `pre-commit` 检测。原实现的 GATE 使其仅在新增/删除 skill 时触发，执行频率极低，其中「未排除 gitignore 目录」的缺陷（会误报 `darwin-skill` 缺失）因此长期未暴露，迁移时一并修正
- `allowed-tools` 去掉 `Edit`：不再需要在提交流程内改写 `plugin.json` 与校验脚本

### Added
- 开篇新增「职责边界」表，明确本 skill 与 `.githooks/pre-commit` 的分工判据：失效后坏的是「这一次提交」还是「仓库长期状态」
- 第四步新增 CHECKPOINT：`pre-commit` 阻断时按报错分类处置，四类各有对应动作，明令禁止 `--no-verify`
- 第五步补齐 rebase 撞上未暂存改动的处置（`git stash push <文件>` → push → `git stash pop`），解决 known-issues 2026-09-07 条：该失败与第一步「排除无关改动」的规范互为因果，越守规范越必然撞上
- `metadata.category: workflow`（此前缺失）

### Changed
- 流程由「6 步 + 2 条件小节」收敛为「5 步 + 1 条件小节」，🔴 CHECKPOINT 由 4 个减至 3 个，SKILL.md 由 278 行降至 216 行
- 常见错误表重写：删除 6 条版本号/符号链接相关（已随门禁移出），新增 3 条（禁止 `--no-verify` 的理由、rebase 阻塞的正确解法、版本决策发生在改动时而非提交时）
- 正文不写职责边界说明：`description` 与 `allowed-tools: Bash`（无 `Edit`）已界定范围，散文式的分工表在流程正常时也要读、读完却不产生任何动作。设计决策的记录归 `.githooks/README.md` 与本文件

## [3.7.0] - 2026-09-08

### Added
- 第二步 CHECKPOINT 新增失败模式分流表：`check_plugin_versions.py` 的四种失败模式此前只有「版本号写错」一类有处置指引，撞上「有多余字段」（白名单校验）时无章可循
- 新增「白名单冲突」小节：以「该字段在 Claude 侧有无独立消费方」为可观测判据二选一——无消费方则删字段，有消费方则放宽门禁白名单，并明确放宽必须同时完成改脚本、改测试、记 `known-issues.md` 三件事
- 常见错误表增两行：报「有多余字段」直接删字段、放宽白名单只改脚本

### Changed
- `known-issues.md` 的 2026-09-08 条目标记为「已优化」，解决版本 3.7.0

## [3.6.1] - 2026-09-06

### Fixed
- `test_check_plugin_versions.py` 的 `test_agents_field_is_allowed` 固件路径由 `./agents/x.agent.md` 改为 `./agents/x.md`——避免测试固件成为 `.agent.md` 命名的残留示范，断言本身不受影响

## [3.6.0] - 2026-09-06

### Added
- 第二步新增阻断式校验：`scripts/check_plugin_versions.py` 比对每插件两份 `plugin.json` 的 `version`，不一致则禁止提交（配 11 个 unittest 用例，含「报错措辞不得写以某一份为准」一条）

### Changed
- 第二步「版本号决策」整节重写：版本落点从 `.claude-plugin/marketplace.json` 顶层下移至每插件的两份 `plugin.json`；升级幅度表删除，统一以 `AGENTS.md` 版本管理规则为唯一依据（原表与 AGENTS.md 有两行差异）
- 第三步暂存示例改为两份 `plugin.json`，不再示范 `git add .claude-plugin/marketplace.json`
- 常见错误表增两行：只升一份 `plugin.json`、改插件内容却升 marketplace 顶层

## [3.5.0] - 2026-09-04

### Changed
- 流程重组为「5 步主路径 + 2 条件小节」：将原第二步（.kiro/.agents/skills 符号链接）收敛为 §A 条件小节、原第五步 amend 合并收敛为 §B 条件小节，仅在该场景触发，主路径更短
- 去重：第四步 `git fetch` 一次，第六步 `git pull --rebase` 复用其结果，消除重复 fetch；第一步去掉与 `git status` 内容重复的 `git diff HEAD --stat`
- 修正「常见错误」表中「未提交 → 未推送」表述错误，步骤编号随重组同步更新

## [3.4.4] - 2026-08-30

### Added
- 新增 `known-issues.md` 使用期反馈记录机制（空模板），配套仓库新增的 skill 持续优化硬性约定，见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`

## [3.4.3] - 2026-08-29

### Changed
- Git 知识库入口链接随知识库领域元数据文件改名同步：`knowledge-base/git/00-README.md` → `README.md`

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
