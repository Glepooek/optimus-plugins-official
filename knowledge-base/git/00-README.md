# Git 协作规范

> 面向团队的 Git 工作流总纲。**语言与平台中立**——不绑定特定技术栈，适用于仓库内任何语言/项目的版本控制实践。

## 文档目的

本规范统一团队的分支策略、提交信息、PR 与合并、版本发布、代码所有权约定，目标是让协作历史**可追溯、可回滚、可审查**。它不涉及具体语言的编码规范（那部分见 `knowledge-base/csharp/`、`knowledge-base/wpf/` 等领域）。

## 适用范围与读者

- **适用范围**：仓库内所有 Git 版本控制活动；新建分支、提交、PR、发布、Code Review 均适用
- **读者**：团队全部开发者。新人用于建立协作基线，资深成员用于对齐分支/发布边界

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义。各篇正文使用对应措辞，级别决定违反后的处置：

| 级别 | 措辞 | 含义 | 违反处置 |
|---|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 | 视为缺陷，CI / review 拦截 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 | review 说明理由后可豁免 |
| **建议 MAY** | "可以"、"建议" | 可选做法，团队不强制 | 无 |

## 规范如何执行

1. **提交信息校验**：CI / commit-msg hook 校验 Conventional Commits 格式（见 `02` 章）
2. **分支保护**：主干分支设保护规则，禁止直接推送，只能通过 PR 合入（见 `01`、`03` 章）
3. **CI 门禁**：PR 合并前必须 CI 全绿（见 `03` 章）
4. **密钥扫描**：CI 集成 secret scanning，拦截敏感信息误提交（见 `02` 章）

## 阅读路径

| 读者 | 必读 | 选读 |
|---|---|---|
| 新人（前两周） | `01` `02` | `03` |
| 资深成员 | `03` `04` `05` | 其余 |
| 全部成员 | 本文件、`01`、`02` | — |

## 文件地图

| 编号 | 文件 | 主题 |
|---|---|---|
| 00 | `00-README.md` | 总则、级别、执行、索引 |
| 01 | `rules/01-branching.md` | 分支策略与命名规范 |
| 02 | `rules/02-commit-messages.md` | 提交信息规范、提交前检查与敏感信息防护 |
| 03 | `rules/03-pull-requests.md` | PR 规范与合并策略 |
| 04 | `rules/04-versioning-release.md` | 版本与发布 |
| 05 | `rules/05-ownership.md` | 代码所有权与约定 |

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。`reference/` 目录存放不带 MUST/SHOULD/MAY 语气的描述性知识（工作流对比、命名示例、工具讲解），与 `rules/` 下的规范文件是并列关系，不是从属关系。

## 更新与豁免

- 每篇文件头部记录本文件更新历史（日期 + 变更摘要），随变更提交
- 规范修订走 PR，review 通过后合入，并同步更新本文件的地图与阅读路径
- **豁免**：遇规范与场景冲突，在 PR 中显式注明"豁免原因"，由 reviewer 裁量；系统性豁免需求应推动规范修订，而非长期例外

## 与仓库已有资产的关系

- `commit-cc-plugin` skill：本规范 `02` 章提交信息格式是它生成提交信息时的依据
- `knowledge-base/csharp/rules/16-collaboration.md`：原分支/提交/PR/发布/所有权条款已迁移至本领域，`csharp/16` 仅保留与语言相关的 CHANGELOG 条款

## 权威参考

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [语义化版本 SemVer](https://semver.org/lang/zh-CN/)
- [GitHub Flow](https://docs.github.com/zh/get-started/using-github/github-flow)
