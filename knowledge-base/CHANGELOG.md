# Changelog

## [1.7.0] - 2026-08-23

### Added
- `git/02-commit-messages.md` §1 新增规范条：提交中若有 AI 协作者，须用 `Co-Authored-By` footer 明确标注，禁止隐去 AI 参与事实
- `git/reference/commit-message-tooling.md` 新增第 4 节「AI 协作者标注」：Co-Authored-By 格式讲解、为何用结构化 footer 而非自由文本、常见误区
- `git/index.jsonl` 新增 1 条规范索引记录 `git.02.ai-coauthor`，`git.ref.commit-message-tooling` 的 `tags`/`summary` 同步补充 AI 协作相关关键词

## [1.6.0] - 2026-08-23

### Added
- `git` 领域新增 `reference/branching-workflows.md`：GitHub Flow/Git Flow/Trunk-Based 工作流对比、分支命名示例大全、分支生命周期管理（创建/同步/清理），是 `01-branching.md` 的配套参考
- `git` 领域新增 `reference/commit-message-tooling.md`：Conventional Commits 完整规范（type 清单、BREAKING CHANGE、多行 body）、commit-msg hook 实现（commitlint/husky、纯 Shell）、敏感信息扫描工具对比（gitleaks/git-secrets/truffleHog），是 `02-commit-messages.md` 的配套参考
- `git/index.jsonl` 补充对应 2 条 reference 索引记录

### Changed
- `01-branching.md`、`02-commit-messages.md` 正文头部补充指向配套 reference 的引用说明
- `git/00-README.md`「索引与机器消费」补充 `reference/` 目录说明

## [1.5.0] - 2026-08-23

### Added
- 新增 `git` 领域：Git 协作规范总纲（00-README + 01-05 五篇规范文件），覆盖分支策略与命名、提交信息与敏感信息防护、PR 与合并策略、版本与发布、代码所有权
- `git/index.jsonl` 首批 11 条索引记录

### Changed
- `csharp/16-collaboration.md` 的分支策略、提交信息、PR 规范、版本与发布、代码所有权五节迁移至 `git/` 领域对应文件，本篇仅保留与语言相关的 CHANGELOG 条款并重新编号为 §1
- `csharp/index.jsonl` 移除已迁移的 4 条记录（`branch-strategy`/`commit-message`/`pr-conventions`/`release-versioning`），`changelog` 记录 anchor 同步更新
- `csharp/00-README.md` 文件地图第 16 行主题说明同步更新，指向 `knowledge-base/git/`

## [1.4.0] - 2026-08-23

### Added
- `csharp/index.jsonl` 补齐至全量覆盖 01-17 全部规范文件：9 → 122 条（新增 113 条，`02-coding-style.md`/`12-testing.md` 按三级子节粒度，其余按二级章节粒度）
- `wpf/index.jsonl` 补齐至全量覆盖 01-17 全部规范文件：6 → 132 条（新增 126 条，全部按二级章节粒度，wpf 规范文件基本无三级子节）
- 两领域索引一致性校验通过：`check_index.py csharp wpf` → 共检查 254 条记录，未发现问题

## [1.3.3] - 2026-08-23

### Changed
- README「消费方式」补充"动态检索 vs 固定映射"两种消费模式说明，明确 `csharp-code-review`/`wpf-code-review` 直接引用 `file`+`anchor` 属于被认可的固定映射模式
- README「维护约定」补充索引覆盖是渐进式的，新增/优化 skill 引用到未登记规则时随手补录即可，不必专项排期回填

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
