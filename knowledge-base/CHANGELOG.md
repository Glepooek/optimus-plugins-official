# Changelog

## [1.3.2] - 2026-08-22

### Changed
- wpf 规范引用 skill 改名同步：`wpf-xaml-performance` → `wpf-code-review`（wpf/00-README、10/08/07 篇头部与联动措辞更新，性能操作层改为指向 skill 的「性能专项诊断速查」章节）

## [1.3.1] - 2026-08-22

### Changed
- `.claude/rules/skill-authoring.md` 重命名为 `skill-conventions.md`（规则文件覆盖 skill 全生命周期约定，`authoring` 名偏窄），README 与 `skill-authoring/00-README.md`、`01-skill-format.md` 引用同步更新

## [1.3.0] - 2026-08-22

### Added
- 新增 `skill-authoring` 领域（Skill 创建规范）：00-README + 01-05 规范篇 + 3 个 reference 讲解篇
- `01-skill-format.md`：SKILL.md 格式规约（目录结构/frontmatter/正文/progressive disclosure/文件引用）
- `02-description-optimization.md`：描述优化（触发机制/写作原则/trigger eval/train-validation 切分）
- `03-skill-evaluation.md`：质量评估（evals/assertions/grading/benchmark/迭代循环）
- `04-script-usage.md`：脚本使用（one-off 命令/自包含脚本/agentic 设计）
- `05-best-practices.md`：最佳实践（真实经验/上下文预算/控制校准/指令模式）
- `reference/`：trigger-eval-workflow、eval-workspace-structure、self-contained-scripts 三篇讲解
- `.claude/rules/skill-authoring.md` frontmatter 节改为引用知识库 `skill-authoring/`（通用规范归知识库，仓库专属约定留规则文件）

## [1.2.1] - 2026-08-22

### Changed
- `csharp/README.md`、`wpf/README.md` 重命名为 `00-README.md`（纳入编号体系，文件地图同步更新）

## [1.2.0] - 2026-08-22

### Added
- 首个 reference 条目 `csharp.ref.refit`：`refit.md` 迁入 `csharp/reference/`，登记索引
- 相关引用路径更新（`13-api-design.md`、`csharp/README.md` 中 `refit.md` → `reference/refit.md`）

## [1.1.1] - 2026-08-22

### Changed
- 校验脚本 `check_index.py`、`test_check_index.py` 迁至 `knowledge-base-maintain` skill 的 `scripts/` 子目录，随 skill 分发；`base_dir` 定位逻辑相应调整（`parents[4]` 定位仓库根再进 `knowledge-base/`）；运行命令更新为 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>`

## [1.1.0] - 2026-08-22

### Added
- `02-coding-style.md` 新增 2.5 节：委托选择规则（优先 Func/Action），原 2.5 注释风格顺移为 2.6
- `13-api-design.md` 补充隐式依赖契约需显式说明的规则
- 对应索引记录 `csharp.02.delegate-func-action`、`csharp.13.implicit-dependency-contract`

## [1.0.0] - 2026-08-22

### Added
- 迁移 `docs/csharp_doc` → `knowledge-base/csharp`，`docs/wpf_doc` → `knowledge-base/wpf`
- 建立 JSON Lines 索引机制（`index.jsonl`）与一致性校验脚本 `check_index.py`
- csharp、wpf 两领域首批索引条目（各 6 条）
