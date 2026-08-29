# 软件架构规范

> 面向团队的软件架构风格与设计原则总纲。**语言无关**——不绑定任何编程语言或框架；只回答「该怎么切、依赖指向哪、边界在哪」，不回答「用什么类型怎么写」。

本领域负责架构风格、分层契约、设计原则与选型判据；C# 语言与 .NET 落地细节归 `knowledge-base/csharp/`，WPF/XAML 专属规则归 `knowledge-base/wpf/`，平台与运行时事实归 `knowledge-base/dotnet/`。需要落地手段时引用对应领域，不要在本领域出现语言专有类型名。

## 文档目的

本规范给出架构决策的**判断依据**，目标是让「为什么这样切分」有可检验的答案，而不是团队口头共识或个人偏好。它不推销任何架构风格——风格的成本必须与问题复杂度匹配，「不引入任何风格」在很多场景下是正确答案。

## 适用范围与读者

- **适用范围**：所有需要做架构决策的代码库；新系统设计、既有系统重构、架构 review 均适用。语言与技术栈无关
- **读者**：做架构决策的开发者与 reviewer。新人用于理解现有结构的成因，资深成员用于对齐边界判断

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义，与 `knowledge-base/csharp/README.md` 同一套定义。各篇正文使用对应措辞，级别决定违反后的处置：

| 级别 | 措辞 | 含义 | 违反处置 |
|---|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 | 视为缺陷，CI / review 拦截 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 | review 说明理由后可豁免 |
| **建议 MAY** | "可以"、"建议" | 可选做法，团队不强制 | 无 |

## 与相邻领域的边界

架构决策与语言落地容易混淆，四方各自回答一个不同的问题。判断某条内容归谁时按此表：

| 领域 | 回答的问题 | 同一主题「缓存」的例子 |
|---|---|---|
| **`architecture`（本领域）** | **缓存该放哪一层、哪些数据不该缓存、失效是谁的职责** | 「缓存必须置于应用层与基础设施层之间，领域层禁止感知缓存存在」 |
| `csharp` | 在 C# 里怎么落地 | 「缓存必须设上限与过期策略」（`csharp.07.caching-strategy`） |
| `wpf` | 在 WPF 里的特有形态 | 「UI 虚拟化下的数据缓存要求」 |
| `dotnet` | 平台提供什么能力 | 「各 .NET 版本的缓存 API 可用性」 |

**判据一句话**：出现「哪一层、哪个边界、该不该拆」→ 本领域；出现具体类型名与 API → `csharp`/`wpf`；出现平台版本事实 → `dotnet`。

本领域正文**禁止**出现语言专有类型名（如 `IServiceCollection`、`DbContext`、`IMemoryCache`）——需要指明落地手段时改为引用对应领域的章节（带章节标题）。唯一例外是 `reference/dotnet-architecture-decisions.md`，该篇专门记录 .NET 生态的具体架构决策，允许点名具体库与类型。

## 规范如何执行

架构约束大多无法被工具无歧义判定，落地手段与编码规范不同：

1. **架构 review**：结构性决策（拆项目、引入风格、定边界）须在 review 中说明判据，判据取自本规范
2. **架构测试**：依赖方向、层间引用、循环依赖可用架构测试库断言，属可自动化的少数部分（索引中 `enforcement: ci` 的条目）
3. **选型记录**：风格选型与「为什么不选」的理由记入 `reference/`，避免同一决策被反复重开
4. **落地引用**：具体技术手段不在本规范内展开，由被引用的领域承载

## 阅读路径

| 读者 | 必读 | 选读 |
|---|---|---|
| 新人（前两周） | `01` `02` | `06` |
| 做架构决策前 | `06` + 对应风格篇（`03`/`04`/`05`） | `reference/` 两篇 |
| .NET 项目决策 | `06` `07` `08` `09` `10` | `reference/dotnet-architecture-decisions.md` |
| 全部成员 | 本文件、`01` `02` | 其余 |

## 文件地图

| 编号 | 文件 | 主题 |
|---|---|---|
| — | `README.md` | 总则、级别、领域边界、执行、索引 |
| 01 | `rules/01-layering.md` | 分层与依赖方向 |
| 02 | `rules/02-design-principles.md` | 设计原则（SOLID 及其可执行检查项） |
| 03 | `rules/03-ddd.md` | 领域驱动设计：战术模式与战略设计 |
| 04 | `rules/04-hexagonal.md` | 六边形架构：端口与适配器 |
| 05 | `rules/05-clean-architecture.md` | 整洁架构：同心圆与依赖规则 |
| 06 | `rules/06-style-selection.md` | 架构风格选型判据 |
| 07 | `rules/07-cqrs-and-slices.md` | CQRS 与垂直切片 |
| 08 | `rules/08-module-boundaries.md` | 模块与部署边界 |
| 09 | `rules/09-composition-root.md` | 组合根与依赖装配 |
| 10 | `rules/10-cross-cutting.md` | 横切关注点的层次归属 |
| — | `reference/architecture-styles-comparison.md` | 四种架构风格横向对比与取舍理由 |
| — | `reference/dotnet-architecture-decisions.md` | .NET/C# 生态的具体架构决策记录 |

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。`reference/` 目录存放不带 MUST/SHOULD/MAY 语气的描述性知识（风格对比、决策记录），与 `rules/` 下的规范文件是并列关系，不是从属关系——新增/修改任一类内容都需同步 `index.jsonl`，建议通过 `/knowledge-base-maintain` skill 完成。

## 更新与豁免

- 每篇文件头部记录本文件更新历史（日期 + 变更摘要），随变更提交
- 规范修订走 PR，review 通过后合入，并同步更新本文件的地图与阅读路径
- **豁免**：架构决策的场景差异比编码规范大，豁免更常见。在 PR 中显式注明「豁免原因」与「该决策的已知代价」，由 reviewer 裁量；系统性豁免需求应推动规范修订

## 与仓库已有资产的关系

- `knowledge-base/csharp/`：本规范的 C# 落地侧。`rules/01-project-structure.md` § 6 与 `rules/03-design-principles.md` § 1、§ 2、§ 6、§ 8 保留 C# 特有增量，通用约束在本领域
- `knowledge-base/wpf/`：桌面 UI 的架构落地形态（MVVM 属分层在 UI 侧的具体形态）
- `knowledge-base/design-patterns/`：单个设计模式的选用判据。本领域只做**架构风格**级别的选型（`rules/06-style-selection.md`），不写任何单个 GoF 模式的判据

## 权威参考

- [Clean Architecture（Robert C. Martin）](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture（Alistair Cockburn）](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design Reference（Eric Evans）](https://www.domainlanguage.com/ddd/reference/)
- [Microsoft .NET 应用架构指南](https://learn.microsoft.com/zh-cn/dotnet/architecture/)
- [Microsoft 微服务架构电子书](https://learn.microsoft.com/zh-cn/dotnet/architecture/microservices/)
