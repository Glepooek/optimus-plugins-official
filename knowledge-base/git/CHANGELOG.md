# Changelog — Git 版本控制与协作

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 4.0.1 - 2026-08-28

`check_refs.py` 扫描范围扩到知识库正文后的首轮修复（此前该校验器只看 `plugins/*/skills/`，正文内的 `§` 引用无人看守）。

- **Fixed**：`git/reference/commit-message-tooling.md` §3.1 末段声称 `rules/02-commit-messages.md` §2 有「CI 侧二次校验」这一说法——**该措辞在规范中不存在**，§2 只约束本地 pre-commit / commit-msg hook，并明确把耗时检查「交给 CI」而未规定 CI 侧二次校验。真正对应的是 §3 的「CI 集成 secret scanning，在 PR 阶段拦截」。已改为引用 §3。
- **Changed**：补齐知识库正文内 11 处只写章节号、未写标题的 `§` 引用（`git/rules/02-commit-messages.md` 1 处、`git/reference/branching-workflows.md` 3 处、`git/reference/commit-message-tooling.md` 7 处）。裸章节号引用无法与标题交叉校验，章节重编号后会静默指向别的内容。全库 `check_refs.py --strict` 由 12 处问题降为 0。

### 衍生自全局 1.8.0 - 2026-08-23

- **Added**：`git` 领域新增 `reference/pull-request-concepts.md`：Pull Request 概念讲解——PR 不是 GitHub 特有（GitLab 叫 Merge Request）、PR 的代码评审/CI 门禁/合并关卡三大作用、何时该用 PR，是 `03-pull-requests.md` 的配套参考
- **Added**：`git/index.jsonl` 新增 1 条 reference 索引记录 `git.ref.pull-request-concepts`
- **Changed**：`03-pull-requests.md` 正文头部补充指向配套 reference 的引用说明

### 衍生自全局 1.7.0 - 2026-08-23

- **Added**：`git/02-commit-messages.md` §1 新增规范条：提交中若有 AI 协作者，须用 `Co-Authored-By` footer 明确标注，禁止隐去 AI 参与事实
- **Added**：`git/reference/commit-message-tooling.md` 新增第 4 节「AI 协作者标注」：Co-Authored-By 格式讲解、为何用结构化 footer 而非自由文本、常见误区
- **Added**：`git/index.jsonl` 新增 1 条规范索引记录 `git.02.ai-coauthor`，`git.ref.commit-message-tooling` 的 `tags`/`summary` 同步补充 AI 协作相关关键词

### 衍生自全局 1.6.0 - 2026-08-23

- **Added**：`git` 领域新增 `reference/branching-workflows.md`：GitHub Flow/Git Flow/Trunk-Based 工作流对比、分支命名示例大全、分支生命周期管理（创建/同步/清理），是 `01-branching.md` 的配套参考
- **Added**：`git` 领域新增 `reference/commit-message-tooling.md`：Conventional Commits 完整规范（type 清单、BREAKING CHANGE、多行 body）、commit-msg hook 实现（commitlint/husky、纯 Shell）、敏感信息扫描工具对比（gitleaks/git-secrets/truffleHog），是 `02-commit-messages.md` 的配套参考
- **Added**：`git/index.jsonl` 补充对应 2 条 reference 索引记录
- **Changed**：`01-branching.md`、`02-commit-messages.md` 正文头部补充指向配套 reference 的引用说明
- **Changed**：`git/00-README.md`「索引与机器消费」补充 `reference/` 目录说明

### 衍生自全局 1.5.0 - 2026-08-23

- **Added**：新增 `git` 领域：Git 协作规范总纲（00-README + 01-05 五篇规范文件），覆盖分支策略与命名、提交信息与敏感信息防护、PR 与合并策略、版本与发布、代码所有权
- **Added**：`git/index.jsonl` 首批 11 条索引记录

原条目另一半（`csharp/16-collaboration.md` 五节迁出至 git 侧的改造）记在 `knowledge-base/csharp/CHANGELOG.md`。
