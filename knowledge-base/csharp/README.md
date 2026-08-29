# C# 开发规范

> 版本：7.2.1

> 面向团队的全覆盖 C# 开发总纲。**版本中立**——不绑定特定 .NET 版本，适用于所有主流 .NET 版本；编码风格与工程实践并重。

本领域负责 C# 语言、编码风格、设计原则和通用 .NET 工程实践；.NET Runtime、SDK、目标框架、Windows 兼容性与生命周期事实归 `knowledge-base/dotnet/`，WPF/XAML 专属规则归 `knowledge-base/wpf/`，语言无关的架构风格、分层契约与设计原则归 `knowledge-base/architecture/`，设计模式的选用判据与误用识别归 `knowledge-base/design-patterns/`。需要判断运行环境时引用 `dotnet`，架构层面的「该不该、选哪个、边界在哪」引用 `architecture`，模式层面的「该不该用、误用信号」引用 `design-patterns`，不要在本领域复制平台支持矩阵、架构通用条款或模式选用判据。

## 文档目的

本规范统一团队 C# 项目的编码风格、设计原则与工程实践，目标是让代码**可读、可维护、可演进**。它不是约束的堆砌，而是对"什么样的代码算好代码"的团队共识。

## 适用范围与读者

- **适用范围**：所有 C# / .NET 代码库；新增代码、存量代码改造、Code Review 与 CI 门禁均适用
- **读者**：团队全部开发者。新人用于建立基线，资深成员用于对齐边界

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义。各篇正文使用对应措辞，级别决定违反后的处置：

| 级别 | 措辞 | 含义 | 违反处置 |
|---|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 | 视为缺陷，CI / review 拦截 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 | review 说明理由后可豁免 |
| **建议 MAY** | "可以"、"建议" | 可选做法，团队不强制 | 无 |

## 规范如何执行

规范不是纸面文档，通过以下手段落地：

1. **静态分析门禁**：`.editorconfig` + Roslyn 分析器（见 `rules/01-project-structure.md`），严重级别告警按 **warnings-as-errors** 处理
2. **CI 校验**：`restore → build(-warnaserror) → test` 三关
3. **Code Review**：审查内容重点按 `rules/15-quality-review.md`（PR 流程与合并门禁见 `knowledge-base/git/`）；编码层面问题由 `csharp-code-review` skill 辅助检出
4. **模板兜底**：新增项目 / 文件按 `rules/01-project-structure.md` 的布局约定生成

## 阅读路径

| 读者 | 必读 | 选读 |
|---|---|---|
| 新人（前两周） | `01` `02` `04` | `03` `12` |
| 资深成员 | `03` `07` `08` `14` | 其余 |
| 全部成员 | 本文件、`02` | — |

## 文件地图

| 编号 | 文件 | 主题 |
|---|---|---|
| — | `README.md` | 总则、级别、执行、索引 |
| 01 | `rules/01-project-structure.md` | 环境与技术选型、解决方案与项目结构 |
| 02 | `rules/02-coding-style.md` | 命名规范、编码风格、语言特性使用准则 |
| 03 | `rules/03-design-principles.md` | 面向对象与设计原则 |
| 04 | `rules/04-async-programming.md` | 异步编程 |
| 05 | `rules/05-error-handling.md` | 异常处理与错误设计 |
| 06 | `rules/06-memory-resource.md` | 内存与资源管理 |
| 07 | `rules/07-performance.md` | 性能 |
| 08 | `rules/08-concurrency.md` | 并发与线程安全 |
| 09 | `rules/09-data-access.md` | 数据访问与数据库 |
| 10 | `rules/10-dependency-management.md` | 依赖管理与 NuGet（CPM） |
| 11 | `rules/11-observability.md` | 日志与可观测性 |
| 12 | `rules/12-testing.md` | 测试规范 |
| 13 | `rules/13-api-design.md` | API 设计与版本化 |
| 14 | `rules/14-security.md` | 安全规范 |
| 15 | `rules/15-quality-review.md` | 静态分析、代码度量与 review 内容重点（CI 门禁/PR 流程见 `knowledge-base/git/`） |
| 16 | `rules/16-collaboration.md` | CHANGELOG 规范（分支/提交/PR/发布/所有权见 `knowledge-base/git/`） |
| 17 | `rules/17-comments-docs.md` | 注释与文档 |

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。`reference/` 目录存放不带 MUST/SHOULD/MAY 语气的描述性知识（语法讲解、API 用法），与 `rules/` 下的规范文件是并列关系，不是从属关系——新增/修改任一类内容都需同步 `index.jsonl`，建议通过 `/knowledge-base-maintain` skill 完成。

## 更新与豁免

- 每篇文件头部记录本文件更新历史（日期 + 变更摘要），随变更提交
- 规范修订走 PR，review 通过后合入，并同步更新本文件的地图与阅读路径
- **豁免**：遇规范与场景冲突，在 PR 中显式注明"豁免原因"，由 reviewer 裁量；系统性豁免需求应推动规范修订，而非长期例外

## 与仓库已有资产的关系

- `csharp-code-review` skill：本规范 `02` 章的编码层面是它的审查依据；review 流程见 `15`
- `dotnet-upgrade` 系列 skills：版本升级与迁移以它们为准，本规范保持版本中立，不重复迁移细节
- `knowledge-base/dotnet/`：提供 Runtime、SDK、目标框架、Windows 兼容性与生命周期 reference
- `knowledge-base/architecture/`：语言无关的架构风格与设计原则。本领域 `01` 章第 6 节、`03` 章第 1、2、6、8 节的通用约束在该领域，本领域只保留 C# 特有增量
- `knowledge-base/design-patterns/`：设计模式的选用判据与误用识别。本领域 `03` 章第 7 节只保留 DI 容器时代单例的 C# 侧禁令与替代模式的语言构件选择，模式该不该引入的判据在该领域
- `dotnet-nuget:convert-to-cpm`：`10` 章强制中央包管理（CPM），落地用该 skill
- `reference/refit.md`：Refit REST 客户端实践参考，见 `13` 章 API 设计相关条目

## 权威参考

- [Microsoft C# 编码规范](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [Microsoft 标识符命名准则](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/identifier-names)
- [Framework Design Guidelines](https://learn.microsoft.com/zh-cn/dotnet/standard/design-guidelines/)
- [.NET Runtime 编码风格](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
