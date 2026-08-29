# Changelog — C# 语言与通用工程实践

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 7.0.0 - 2026-08-29

**不兼容性**：`csharp.03.design-pattern-moderation` 的正文范围与 `summary` 收窄，按 `id` 检索的消费者拿到的内容变了。`id`/`file`/`anchor` 全部不动。经 grep 确认该条目**零消费者 skill 引用**。

#### Changed

- **`csharp/rules/03-design-principles.md` § 7. 设计模式适度使用收窄为「引用 + C# 特有增量」**。原 4 条条款的处置：

  | 原条款 | 处置 |
  |---|---|
  | 必须：模式服务目标，优先语言原生表达力替代模板类模式 | 迁出 → `design-patterns/rules/01-pattern-selection.md § 1. 引入门槛` 与 `06-modern-alternatives.md § 1. 替代关系总览` |
  | 应该：常见模式按需采用（策略/观察者/仓储/工厂） | 迁出 → 拆入 `design-patterns/rules/02`-`04` 对应条目 |
  | 禁止：为单例而单例，实例由 DI 容器管理，类内静态 `Instance` 反模式 | **保留**（DI 容器是 .NET 具体机制） |
  | 禁止：照搬 GoF 模板而不评估适用性 | 迁出 → `01-pattern-selection.md § 1. 引入门槛` |

  收窄后新增两条 C# 特有条款以免留下空壳：替代模板类模式的语言构件按场景选择（委托 / `switch` 表达式与模式匹配 / 事件与 `IObservable<T>` / `IEnumerable<T>` + `yield`）、禁止为 .NET 已提供实现的模式手写类结构（Dispose 模式、迭代器）。该节现有 3 条条款含 2 条「禁止」，`level` 保持 MUST，不走废弃流程也不并入 § 6。
- **`csharp.03.design-pattern-moderation` 的 `enforcement` 由 `review` 改为 `ci`**：收窄后剩余条款是「类内静态 `Instance` 属性」「为已有实现的模式手写类结构」，均为分析器可无歧义判定的成员与类型形态，通过外壳检验。`title` 与 `summary` 同步改写，`reviewed_at` 更新为 2026-08-29。
- `csharp/00-README.md`：领域边界声明与「与仓库已有资产的关系」补入 `design-patterns`，点明 `03` 章 § 7 只保留 C# 侧禁令、模式选用判据在新领域。
- `csharp/rules/03-design-principles.md` 篇首「更新历史」追加本次去重记录。

design-patterns 领域侧的新建内容（6 篇 rules + 2 篇 reference，35 条索引）记在 `knowledge-base/design-patterns/CHANGELOG.md`。

### 衍生自全局 6.0.0 - 2026-08-29

`csharp` 五条架构条款的通用部分收窄，改为引用 5.1.0 新建的 `architecture` 领域。这是 5.1.0 预告的迁移改造——新建领域只完成了一半工作，若不做本次收窄，同一条约束会在两个领域各自完整表述一遍，等于把重复从一处变成两处。

**不兼容性**：五条 `csharp` 条目的正文范围与 `summary` 收窄，按 `id` 检索的消费者拿到的内容变了。`id`/`file`/`anchor` 全部不动，检索仍能命中；但读到的约束只剩 C# 特有增量，通用部分需按正文中的引用跳转到 `architecture`。经 grep 确认这五条**无任何消费者 skill 引用**，实际影响面仅限直接检索索引的使用者。

#### Changed

- **五条 `csharp` 条目的正文收窄为「引用 + C# 特有增量」**，通用约束归入 `architecture`：

  | `id` | 摘除的通用部分（去向） | 保留的 C# 特有增量 |
  |---|---|---|
  | `csharp.01.layering-direction` | 分层模型的选择与统一、依赖单向向内、禁循环与越层、跨层契约（`architecture/rules/01-layering.md` § 1、§ 2、§ 3） | 层与项目（程序集）一一对应，依赖方向由 `ProjectReference` 承载以便编译器直接拦截；跨层接口定义在内层项目；测试项目引用边界 |
  | `csharp.03.solid-principles` | 五原则的可执行检查项表、SRP 常见误读（`architecture/rules/02-design-principles.md § 1`） | `public` 接口新增成员会破坏所有实现者（C# 特有的演进成本）、DIP 抽象归属内层项目、上帝类不通过 review |
  | `csharp.03.composition-over-inheritance` | 复用优先组合、禁为复用方法而继承、深继承链须 review（`architecture/rules/02-design-principles.md § 2`） | 用 `sealed` 标记不打算被继承的类 |
  | `csharp.03.dependency-injection` | 组合根唯一性、禁服务定位器与静态服务、生命周期的架构含义、构造期不得阻塞（`architecture/rules/09-composition-root.md § 1、§ 3、§ 4`） | 构造函数注入（禁属性注入与 `IServiceProvider` 直注）、`Transient`/`Scoped`/`Singleton` 的对应用途、`HttpClient` 注册为 `Singleton`、`Lazy<T>` 惰性推迟 |
  | `csharp.03.domain-modeling-ddd` | 聚合根唯一入口、一次事务一个聚合、领域事件、领域层纯净性（`architecture/rules/03-ddd.md § 4、§ 6、§ 7`） | 值对象用 `record` / 实体用 `class` + 身份标识、领域层项目禁引 EF Core 与 `HttpClient`、领域类型禁带 `[Table]`/`[JsonPropertyName]` 标注 |

- **`csharp.03.composition-over-inheritance` 的 `level` 由 MUST 降为 SHOULD**。摘除三条「必须/禁止」通用条款后，该节仅剩「**应该**：用 `sealed` 标记不打算被继承的类」一条——`level` 取小节最强条款级别，实测即为 SHOULD。级别声明必须跟随正文实际措辞，否则索引宣称的强度高于正文，review 时无从执行。
- **两条 `enforcement` 由 `review` 改为 `ci`**，因为收窄后剩下的内容变成了工具可无歧义判定的落地约束（通过外壳检验：判的是实质而非外壳）：
  - `csharp.01.layering-direction`：剩余条款是「层与项目一一对应、依赖方向由 `ProjectReference` 承载」——项目引用关系由编译器与架构测试库直接判定
  - `csharp.03.domain-modeling-ddd`：剩余条款是「值对象用 `record`、领域层项目禁引 EF Core、领域类型禁带持久化标注」——类型选择、项目引用与特性标注均可由分析器判定
- 五条的 `summary` 改写为反映收窄后的实际内容，并注明通用部分的去向；`reviewed_at` 更新为 2026-08-29（正文本次被实读并确认）。
- `csharp/00-README.md`：领域边界声明补入 `architecture`（「架构层面的『该不该、选哪个、边界在哪』引用 architecture」）；「与仓库已有资产的关系」新增一行，点明 `01` 章第 6 节与 `03` 章第 1、2、6、8 节的通用约束在该领域。
- `csharp/rules/01-project-structure.md`、`csharp/rules/03-design-principles.md` 篇首「更新历史」记录本次去重。

#### Fixed

- **消除 5.1.0 遗留的六对 `architecture` ↔ `csharp` 高分重复候选**，`find_duplicates.py` 实测全部降至 0.6 以下（此前最高 0.917，为全库最高分）：

  | 候选对 | 5.1.0 | 6.0.0 |
  |---|---|---|
  | `architecture.02.composition-over-inheritance` ↔ `csharp.03.composition-over-inheritance` | 0.917 | 已出前 20（< 0.447） |
  | `architecture.03.aggregate` ↔ `csharp.03.domain-modeling-ddd` | 0.691 | 已出前 20 |
  | `architecture.02.solid-checkpoints` ↔ `csharp.03.solid-principles` | 0.613 | 已出前 20 |
  | `architecture.01.dependency-direction` ↔ `csharp.01.layering-direction` | 0.556 | 已出前 20 |
  | `architecture.09.composition-root-uniqueness` ↔ `csharp.03.dependency-injection` | 0.537 | 已出前 20 |
  | `architecture.01.layering-model-choice` ↔ `csharp.01.layering-direction` | 0.511 | 已出前 20 |

  两领域间的最高残留为 0.477（`architecture.09.lifetime-architecture-impact` ↔ `csharp.09.dbcontext-lifecycle`），判定为**合理分层**：前者讲生命周期决定状态共享范围的架构含义，后者讲 `DbContext` 具体生命周期的踩坑点，不做迁移。

**验收**：`check_index.py` 409 条 OK（条目数不变，未误删误增）、`check_refs.py --strict` 113 文件 OK、`unittest` 133 全绿、`git diff --check` 无空白污染、`architecture/rules/` 仍零 .NET 类型名。

### 衍生自全局 5.1.0 - 2026-08-29

新增 `architecture` 领域（第 7 个领域），承载语言无关的架构风格、分层契约、设计原则与选型判据（内容详见 `knowledge-base/architecture/CHANGELOG.md`）。此前这类约束零散寄生在 `csharp` 领域内。

本次是**纯新增**，故按 Minor。`csharp` 侧的重复条款尚未收窄——下一个版本（6.0.0）做迁移改造，届时按 Major。

#### 已知待处理（下一版本）

`find_duplicates.py` 检出 6 对 `architecture` ↔ `csharp` 的 ≥0.4 候选，最高 0.917（`architecture.02.composition-over-inheritance` ↔ `csharp.03.composition-over-inheritance`）。这是**预期状态**——本次只建领域，`csharp` 侧收窄在下一版本做。其中两对（0.917 与 0.537 的 `09.composition-root-uniqueness` ↔ `csharp.03.dependency-injection`）不在原定迁移清单内，是调研阶段按「架构/分层/SOLID/DDD」关键词反查时漏掉的——这两条的条款措辞里不含这些词。与 1.5.0 那次「按文件迁移会漏」是同一类教训的另一个变体，已补入 spec 的迁移清单（3 条 → 5 条）。

### 衍生自全局 4.2.0 - 2026-08-28

`csharp` 领域索引覆盖率补齐（81.8% → 96.2%，超过 `wpf` 的 94.3%）。补之前先修了覆盖率算法本身——旧算法用 `min(条目数, 二级章节数)` 封顶，只比数量不看落点，会让条目集中的文件掩盖真实空缺。

#### Added

- `csharp/index.jsonl` 新增 19 条 rule 条目（124 → 143）：`05-error-handling.md` 日志与异常，`06-memory-resource.md` 弱引用/终结器，`07-performance.md` 热点路径识别/字符串/异步性能/基准测试，`08-concurrency.md` 锁选择矩阵/静态可变状态，`09-data-access.md` 数据访问基础/模型验证/数据访问测试，`10-dependency-management.md` 中央包管理（CPM），`11-observability.md` 指标与追踪/配置，`13-api-design.md` 客户端契约同步/与仓库资产，`14-security.md` 日志与脱敏，`17-comments-docs.md` 文档质量。
- 根 README 索引粒度规范新增「覆盖率不追求 100%」章节：明确覆盖率是**诊断指标而非达标指标**，列出三类有意不登记的小节（落地模板与快速上手、通篇跨章导航的小节、约束已由其他章节承载），并记录「联动 X 章」措辞是重复的可靠信号。此前该数字缺少"什么算满"的定义——把它追平会逼出两类坏条目：给操作指南强造 rule 条目，以及给已有真源的约束造第二个检索入口。

#### Changed

- **`csharp/rules/13-api-design.md` §6「契约测试」去重**：该节与 `csharp.12.contract-test`（`12-testing.md` §10）互写「联动」，实则「公共契约变更配契约测试」与 12 章的「变更须跑回归」「禁止无测试保护上线」是同一约束的两次表述——两边互认权威、实则无单一真源，与 3.0.0 处理的 `git` ↔ `csharp` 语义环同型。通用条改为引用 `rules/12-testing.md § 10. 契约测试`，本节只留 API 设计侧特有的「后端契约变更须同步回归客户端契约」。`anchor` 未变更，无消费者需同步。
- 根 README 覆盖率说明补充：`anchor` 指向三级标题时其父二级章节记为已覆盖。

#### Fixed

- 覆盖率统计从「条目数与章节数取小」改为按 `anchor` 落点计算。旧算法让 `csharp/rules/12-testing.md` 的 17 条记为 14/14 满分，真实只覆盖 13 个二级章节——多出的条目把另一个小节的真实空缺掩盖成了满分。修正后 `csharp` 由虚高的 82.6% 回到真实的 81.8%，差距确认为真实存在后才开始补条目。

### 衍生自全局 1.5.0 - 2026-08-23

- `csharp/16-collaboration.md` 的分支策略、提交信息、PR 规范、版本与发布、代码所有权五节迁移至 `git/` 领域对应文件，本篇仅保留与语言相关的 CHANGELOG 条款并重新编号为 §1
- `csharp/index.jsonl` 移除已迁移的 4 条记录（`branch-strategy`/`commit-message`/`pr-conventions`/`release-versioning`），`changelog` 记录 anchor 同步更新
- `csharp/00-README.md` 文件地图第 16 行主题说明同步更新，指向 `knowledge-base/git/`

新建 `git` 领域首批 11 条索引记录，记在 `knowledge-base/git/CHANGELOG.md`。

### 衍生自全局 1.4.0 - 2026-08-23

- `csharp/index.jsonl` 补齐至全量覆盖 01-17 全部规范文件：9 → 122 条（新增 113 条，`02-coding-style.md`/`12-testing.md` 按三级子节粒度，其余按二级章节粒度）
- 两领域索引一致性校验通过：`check_index.py csharp wpf` → 共检查 254 条记录，未发现问题

### 衍生自全局 1.2.1 - 2026-08-22

- `csharp/README.md` 重命名为 `00-README.md`（纳入编号体系，文件地图同步更新）

### 衍生自全局 1.2.0 - 2026-08-22

- 首个 reference 条目 `csharp.ref.refit`：`refit.md` 迁入 `csharp/reference/`，登记索引
- 相关引用路径更新（`13-api-design.md`、`csharp/README.md` 中 `refit.md` → `reference/refit.md`）

### 衍生自全局 1.1.0 - 2026-08-22

- `02-coding-style.md` 新增 2.5 节：委托选择规则（优先 Func/Action），原 2.5 注释风格顺移为 2.6
- `13-api-design.md` 补充隐式依赖契约需显式说明的规则
- 对应索引记录 `csharp.02.delegate-func-action`、`csharp.13.implicit-dependency-contract`
