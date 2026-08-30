# Changelog — Skill 创建与维护规范

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [7.3.0] - 2026-08-30

### Added
- 新增 `rules/06-continuous-improvement.md`（持续优化）：创建后强制 darwin-skill 基线评估、`known-issues.md` 使用期反馈记录规范、"待处理"满3条强制触发优化循环、与 darwin-skill 的现实边界说明
- `index.jsonl` 新增 3 条 `skill-authoring.06.*` rule 索引；补登 `reference/darwin-skill-optimization.md` 的 reference 索引（修复此前的孤儿文件警告）
- README 文件地图新增 `06` 行，阅读路径表补入 `06`

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 1.3.1 - 2026-08-22

- `.claude/rules/skill-authoring.md` 重命名为 `skill-conventions.md`（规则文件覆盖 skill 全生命周期约定，`authoring` 名偏窄），README 与 `skill-authoring/00-README.md`、`01-skill-format.md` 引用同步更新

### 衍生自全局 1.3.0 - 2026-08-22

- 新增 `skill-authoring` 领域（Skill 创建规范）：00-README + 01-05 规范篇 + 3 个 reference 讲解篇
- `01-skill-format.md`：SKILL.md 格式规约（目录结构/frontmatter/正文/progressive disclosure/文件引用）
- `02-description-optimization.md`：描述优化（触发机制/写作原则/trigger eval/train-validation 切分）
- `03-skill-evaluation.md`：质量评估（evals/assertions/grading/benchmark/迭代循环）
- `04-script-usage.md`：脚本使用（one-off 命令/自包含脚本/agentic 设计）
- `05-best-practices.md`：最佳实践（真实经验/上下文预算/控制校准/指令模式）
- `reference/`：trigger-eval-workflow、eval-workspace-structure、self-contained-scripts 三篇讲解
- `.claude/rules/skill-authoring.md` frontmatter 节改为引用知识库 `skill-authoring/`（通用规范归知识库，仓库专属约定留规则文件）
