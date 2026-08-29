# Changelog — 软件架构风格与设计原则

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 6.0.0 - 2026-08-29

`csharp` 五条架构条款的通用部分收窄，改为引用本领域（迁移改造详情见 `knowledge-base/csharp/CHANGELOG.md`）。本领域侧承接迁出的通用约束：

- `architecture/rules/01-layering.md § 1、§ 2、§ 3`：分层模型的选择与统一、依赖单向向内、禁循环与越层、跨层契约——承接自 `csharp.01.layering-direction`
- `architecture/rules/02-design-principles.md § 1`：SOLID 五原则的可执行检查项表、SRP 常见误读——承接自 `csharp.03.solid-principles`
- `architecture/rules/02-design-principles.md § 2`：复用优先组合、禁为复用方法而继承、深继承链须 review——承接自 `csharp.03.composition-over-inheritance`
- `architecture/rules/09-composition-root.md § 1、§ 3、§ 4`：组合根唯一性、禁服务定位器与静态服务、生命周期的架构含义、构造期不得阻塞——承接自 `csharp.03.dependency-injection`
- `architecture/rules/03-ddd.md § 4、§ 6、§ 7`：聚合根唯一入口、一次事务一个聚合、领域事件、领域层纯净性——承接自 `csharp.03.domain-modeling-ddd`
- `architecture/00-README.md`：C# 落地侧的章节清单由「§ 6 与 § 1、§ 8」更正为「§ 6 与 § 1、§ 2、§ 6、§ 8」——5.1.0 写入时按当时预定的三条迁移清单，实际迁移为五条

消除 5.1.0 遗留的六对 `architecture` ↔ `csharp` 高分重复候选（最高 0.917），全部降至 0.6 以下，详见 `csharp` 侧记录。两领域间的最高残留为 0.477（`architecture.09.lifetime-architecture-impact` ↔ `csharp.09.dbcontext-lifecycle`），判定为合理分层，不做迁移。

### 衍生自全局 5.1.0 - 2026-08-29

新增 `architecture` 领域（第 7 个领域），承载**语言无关**的架构风格、分层契约、设计原则与选型判据。此前这类约束零散寄生在 `csharp` 领域内——架构级判断（依赖该指向哪、边界怎么定、什么规模该引入 DDD）挂在「C# 语言与通用工程实践」下，检索者无法按架构维度找到它们，非 C# 场景也无从复用。

本次是**纯新增**，故按 Minor。`csharp` 侧的重复条款尚未收窄——下一个版本做迁移改造，届时按 Major（`csharp` 五条条目的正文范围与 `summary` 会变）。

#### Added

- **`architecture` 领域：10 篇 rules + 2 篇 reference，索引 64 条（rule 62 / reference 2）**，覆盖率 100.0%。
  - `01-layering.md`（6 节）：分层模型的选择与统一、依赖方向、跨层契约、层间数据传递、实现装配的位置、分层约束的可执行性。依赖方向的操作性检验是「把最内层单独取出来编译/构建，它应当能独立成功」
  - `02-design-principles.md`（5 节）：SOLID 的可执行检查项、组合优于继承、抽象的引入门槛、显式优于隐式、原则冲突时的取舍。含 SRP 常见误读（判据是**变更的来源**而非职责数量）与单实现抽象的三种正当例外
  - `03-ddd.md`（8 节）：子域划分、限界上下文、上下文映射、聚合、实体与值对象、领域事件、领域层的纯净性、通用语言。**战略设计为主体**——这是 `csharp` 完全没有的部分，原有内容只覆盖战术模式
  - `04-hexagonal.md`（6 节）：应用核心的边界、端口的定义与归属、驱动侧与被驱动侧、适配器的职责、测试策略的对应关系、常见误用
  - `05-clean-architecture.md`（5 节）：同心圆层次、依赖规则、依赖倒置跨越边界、跨层数据传递、与六边形架构的选择。只写整洁架构特有部分，与六边形共有的约束引用 `04`，不重复
  - `06-style-selection.md`（7 节）：架构成本与问题复杂度匹配、不引入任何风格的合法情形、引入 DDD 的门槛、引入六边形/整洁架构的门槛、四种风格的选择顺序、风格混用的边界、风格的演进与退出
  - `07-cqrs-and-slices.md`（6 节）：CQRS 的三个层级（契约/模型/存储）、读写模型分离的判据、中介者与命令分发、垂直切片 vs 技术分层、切片间的共享代码、与其他风格的组合
  - `08-module-boundaries.md`（7 节）：三种边界的区分（目录/构建单元/部署单元）、拆构建单元的判据、循环依赖的架构级处置、内部可见性、模块化单体、拆分独立部署单元的门槛、边界稳定性
  - `09-composition-root.md`（7 节）：组合根的唯一性、注册的组织方式、生命周期选择的架构含义、构造期的约束、启动期校验、装配与配置的关系、测试中的装配
  - `10-cross-cutting.md`（5 节）：归属判断的通用判据、各关注点的归属（九类对照表）、装饰与拦截的选择、关注点之间的顺序、常见误用
  - `reference/architecture-styles-comparison.md`：四种风格各自解决的问题、代价、什么情况下不该用、组合形态、选型常见误区、决策记录该写什么
  - `reference/dotnet-architecture-decisions.md`：单体 vs 微服务的实际门槛、MediatR 类中介者库的收益与代价、Repository 在 EF Core 之上是否仍必要、AutoMapper 类映射工具的取舍、模块化单体在 .NET 的落地形态、横切关注点在 ASP.NET Core 的承载机制对照、依赖装配的启动期校验
- **`level` 全部 62 条为 MUST，是实测结果而非默认填值**——按小节统计正文的「必须/禁止/应该/可以」措辞数后定级，61 个二级小节每节都含至少一条「必须」或「禁止」，按根 README 的「`level` 取该小节最强条款级别」即为 MUST。
- **`enforcement` 分布 `review` 50 / `ci` 8 / `advisory` 4**。架构条款绝大多数判的是设计意图，工具无从判定，故 `review` 占多数。8 条 `ci` 均通过外壳检验（判的是该小节的实质，不是外壳）：`01.dependency-direction`（架构测试库可断言层间引用）、`01.assembly-location`、`03.domain-purity`、`04.core-boundary`、`04.port-ownership`、`05.dependency-rule`、`09.composition-root-uniqueness`、`10.concern-ownership`。
- **语言无关是硬约束**：`rules/` 正文禁止出现语言专有类型名（`record`/`HttpClient`/`IOptions<T>`/`DbContext` 等），需要落地细节时引用 `csharp` 并带章节标题。唯一例外是 `reference/dotnet-architecture-decisions.md`——它按定位就是 .NET 生态的决策记录，允许点名具体库与类型。
- `catalog.json` 追加 `architecture` 领域记录，`consumers` 为空数组（尚无消费者 skill，消费者建设是后续独立决策）。

#### 已知待处理（下一版本）

`find_duplicates.py` 检出 6 对 `architecture` ↔ `csharp` 的 ≥0.4 候选，最高 0.917（`architecture.02.composition-over-inheritance` ↔ `csharp.03.composition-over-inheritance`）。这是**预期状态**——本次只建领域，`csharp` 侧收窄在下一版本做。其中两对（0.917 与 0.537 的 `09.composition-root-uniqueness` ↔ `csharp.03.dependency-injection`）不在原定迁移清单内，是调研阶段按「架构/分层/SOLID/DDD」关键词反查时漏掉的——这两条的条款措辞里不含这些词。与 1.5.0 那次「按文件迁移会漏」是同一类教训的另一个变体，已补入 spec 的迁移清单（3 条 → 5 条）。
