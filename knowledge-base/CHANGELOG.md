# Changelog

## [7.2.0] - 2026-08-29

补齐 `algorithms` 领域的 `rules/` 侧，该领域由纯 reference 变为规范条款 + 参考混合。7.1.0 只建了理由出处（《Hello 算法》15 章），本次给出可用于 review 的判断条款——纯新增，未改动任何已有领域的内容或索引。

**本次的条款全部自撰，一句未抄。** `reference/` 以 CC BY-NC-SA 4.0 授权且 SA 在目录级别隔离，`rules/` 不得整段复制其正文，只能通过 `source` 引用其章节作为理由出处。这一约束与教材本身的性质叠合：全书「禁止」0 次、「必须」15 次，没有现成条款可搬——做法是从书中事实推出可判断的条款（如「哈希表平均 $O(1)$、最坏 $O(n)$」推出「键来自外部输入时禁止依赖平均复杂度」）。

### Added

- **`algorithms` 领域：4 篇 rules，索引 24 条（全部 `kind: rule`、`level: MUST`）**，覆盖率 92.3%。
  - `01-complexity.md`（5 节）：复杂度声明与规模上限、量级取舍的可接受边界、最差复杂度是默认判据、空间复杂度何时成为主约束、时间与空间的交换须声明代价。本篇是另外三篇的共同前提。核心立场是「复杂度是一个带定义域的承诺」——只写量级不写 $n$ 的取值范围，等于给了无从检验因而无从违反的承诺
  - `02-data-structure-selection.md`（7 节 + 1 张不登记的对照表）：选型输入、连续与离散存储、栈与队列、哈希表、有序结构、堆、图的两种表示。含两条易被忽略的前提：离散存储的 $O(1)$ 插入删除以「已持有目标位置引用」为前提，须先查找时总代价仍是 $O(n)$；量级相同时默认选连续存储，因其缓存命中率更高（占用空间、缓存行、预取机制、空间局部性四方面）
  - `03-recursion-iteration.md`（5 节）：递归与迭代的选择、递归深度的硬性上限、尾递归不得作为深度保证、递归的重复计算、递归的终止与正确性。本篇的存在理由是**递归与迭代的失败形态不同**——迭代的过度循环表现为慢，可观测、可中断；递归的过度深入表现为栈耗尽，不可捕获、进程终止，没有降级余地。因此深度是可用性问题而非性能问题
  - `04-algorithm-strategy.md`（7 节 + 1 张不登记的对照表）：策略选择的共同前提、查找、排序、分治、动态规划、回溯、贪心。策略对照表的「后果」一列全部是**结果错误或不可用**而非「变慢」——这是本篇与 `01`/`02` 的关键差别：结构选错通常只影响效率，策略前提不成立会影响正确性
- **每条 rule 固定给出「怎样算违反」一行。** 这是本领域的质量标尺，直接落实计划的「写不出怎样算违反的内容不该做成 rule，应留在 reference」。24 条全部具备，无一条靠概念解释充数
- **`enforcement` 全部 24 条为 `review`**，是外壳检验的结果而非默认填值。算法条款的实质普遍是「这个前提在本问题上是否成立」——工具能查出代码里有一处递归、有一个哈希查找，但判不出该处递归的深度是否受控、该键是否外部可控。唯一接近 `ci` 的是 `03.recursion-depth-limit` 的一半内容（捕获栈溢出的代码形态可静态检出），但该节实质要求是「深度必须事前受控」，只判外壳故仍取 `review`
- **`source` 24 条填满**：22 条指向 `reference/hello-algo-*.md` 的具体章节，2 条指向 Microsoft Learn（栈溢出不可捕获、尾调用前缀语义）——这两条的依据不在书中，书通篇未点名任何运行时
- **三处同词不同义在正文中显式挡掉**，防的不是查重分数而是语义误命中（分数低但人会拿错条目）：
  - 「复杂度」——本领域指渐近时间/空间复杂度；`csharp.15.complexity-metrics` 是**圈**复杂度（方法内分支数），`architecture.06.cost-complexity-match` 是**问题域**复杂度。三者语义无关，`01` 篇首逐一点名区分
  - 「策略」——本领域指算法策略（怎么计算）；`design-patterns.04.strategy` 是策略**模式**（行为怎么被替换的类结构）。两者正交，`04` 篇首写明一个策略模式的实现体内部可采用本篇任一算法策略
  - 「集合预分配」——`csharp.07.collection-preallocation` 讲怎么写，本领域 `02 § 2` 讲扩容为何有摊还代价
- `catalog.json` 的 `algorithms.categories` 由 `["reference"]` 改为 `["rules", "reference"]`，`notes` 末句由「`rules/` 为自撰内容，待后续版本补入」改为「`rules/` 为自撰内容，不受 SA 传染」

### Changed

- 根 `README.md`：版本号 7.1.0 → 7.2.0；纯描述性参考领域由 `dotnet`、`media`、`algorithms` 三个回到 `dotnet`、`media` 两个——`algorithms` 已有规范条款
- `algorithms/00-README.md`：文件地图补入四篇 rules；删去「`rules/` 尚未建立」一句，改为四篇的判断链说明（`01` 给语汇、`02` 选结构、`03` 管递归安全、`04` 判策略前提）与两张对照表有意不登记索引的理由

### 两处覆盖率缺口是正确状态

`02 § 8. 选型对照` 与 `04 § 8. 策略对照` **有意不登记索引**，故覆盖率为 92.3%（7/8 + 7/8 + 5/5 + 5/5）而非 100%。两节的措辞统计均为「必须/禁止/应该/可以」各 0 次——它们是各节条款的速查汇总，每一行的适用前提都写在对应小节内，登记会给同一约束造第二个检索入口，正是根 `README.md`「覆盖率不追求 100%」第三类要防的形态。

**验收**：`check_index.py` 459 → **483** 条 OK；`check_refs.py --strict` 136 → **140** 文件 OK；`--audit` 显示 `algorithms` 的 `enforcement` 填写率 100%、无孤儿文件、`catalog.json` 9 领域双向一致；`unittest` 133 全绿。

**硬性查重判据通过，且余量远超预期**：`algorithms` 与全库的最高候选仅 **0.238**（`01.magnitude-threshold` ↔ `csharp.07.reflection-avoidance`），不仅低于 0.6 的硬性线，连 0.4 的逐对判定线都未触及，0.4-0.6 区间**无一对候选**，无需逐对判定。这与 A/B 阶段形成对照：`architecture` 建域后与 `csharp` 有六对 ≥0.5（最高 0.917）、必须走 Major 收窄，而本次零重叠——原因是没有寄生源可摘。建域前按 13 个关键词反查全库，确认 `csharp.07.*`/`csharp.08.*` 全 19 条都是「怎么用不踩坑」，全库对递归深度、栈溢出、复杂度量级、策略前提**零条款**，这个语义面此前完全空白。

另有一条实测结论：**语义防撞在措辞阶段完成，不靠事后查重发现**。`04.strategy-precondition` ↔ `design-patterns.04.strategy` 只有 0.139，是因为写正文时就做了「本篇的策略不是策略模式」的区分，进而把 `title`/`summary` 写成「算法策略的前提条件」而非泛泛的「策略选择」。若先按泛化措辞写完再查重，得到的分数会高得多，而且此时改措辞已经要连带改 `id` 与 `anchor`。

## [7.1.0] - 2026-08-29

新增 `algorithms` 领域（第 9 个领域）的 `reference/` 侧：《Hello 算法》全书 15 章，作为算法与数据结构判据的理由出处。`rules/` 尚未建立，随后续版本补入——本次是纯新增，未改动任何已有领域的内容或索引。

**本领域有一项其他领域都没有的属性：`reference/` 的许可证独立于本仓库**（CC BY-NC-SA 4.0，全文见 `reference/LICENSE`）。SA 条款在**目录级别**隔离：`rules/` 为自撰内容、不受传染，但不得整段复制 `reference/` 正文，只能通过 `source` 字段引用。约束同时写入 `algorithms/00-README.md`、根 `README.md` 维护约定与 `catalog.json` 的 `notes`。

### Added

- **`algorithms` 领域：15 篇 reference，索引 15 条（全部 `kind: reference`）**。逐章对应《Hello 算法》1.3.0 第 1–15 章：初识算法、复杂度分析、数据结构、数组与链表、栈与队列、哈希表、树、堆、图、搜索、排序、分治、回溯、动态规划、贪心。每篇含 164 个 C# 代码块中的对应部分，合计 287 KB
- `algorithms/reference/LICENSE`：CC BY-NC-SA 4.0 许可证全文。非 Markdown 文件，实测确认不被 `check_index.py` 报为孤儿——该校验器只扫 `.md`
- 每篇头部的**来源声明块**：原作者 krahets、书名、版本 1.3.0、原书地址、源码仓库（含 tag）、许可证、提取日期，以及相对原书的两项改动说明。BY 条款要求该块不得删除或简化
- 根 `README.md` 维护约定新增「外部作品的许可证隔离」一条

### Changed

- 根 `README.md`：版本号 7.0.0 → 7.1.0；领域列表与「领域职责边界」补入 `algorithms`；纯描述性参考领域从 `dotnet`、`media` 两个扩为三个
- `catalog.json`：追加 `algorithms` 条目。`categories` 只填 `["reference"]`——`rules/` 目录尚不存在，按「只填实际存在的分类目录」约定

### 提取路线的两处实测结论

这两条不影响本次产物，但**下次从外部书籍建 reference 时会再次遇到**，记在此处避免重走：

- **有上游 markdown 源时不要从 PDF 提取。** 最初按 PDF 路线做，其符号连字损坏（`//` 渲染为 `^/`）不可完备逆向：实测 `^.` 同时来自 `..`（省略号）与 `->`（C++ 箭头），同一输出对应多个输入，任何单一替换规则都会在一边静默写错且语法仍合法、grep 检不出。改走上游 markdown 源后这一整类问题消失，且额外拿回了代码缩进、行内代码标记与真实图片路径——PDF 路线里这三样全部丢失
- **按 tag 抓取而非默认分支。** 来源声明写「版本 1.3.0」就必须取 `1.3.0` tag 的内容；`main` 会随上游提交漂移（实测比 1.3.0 多出 13 个 `exercises.md`），抓 `main` 会让声明变成不可复现的假声明

## [7.0.0] - 2026-08-29

新增 `design-patterns` 领域（第 8 个领域），承载设计模式的**判断层**——该不该引入某个模式、什么信号说明用错了、语言特性能否替代。此前这块不是「没写」而是「只写了落地、没写判断」：模式的落地条目有 20+ 条（`wpf.03.icommand`、`wpf.16.behavior-*`、`csharp.06.idisposable-implementation` 等），但全库精确匹配「XX模式」「GoF」只有 2 行，都在 `csharp/rules/03-design-principles.md` § 7——一个被压缩到 4 条条款的占位节，其中一条把策略/观察者/仓储/工厂四个模式压成了一行。

**不兼容性**：`csharp.03.design-pattern-moderation` 的正文范围与 `summary` 收窄，按 `id` 检索的消费者拿到的内容变了。`id`/`file`/`anchor` 全部不动。经 grep 确认该条目**零消费者 skill 引用**。

### Added

- **`design-patterns` 领域：6 篇 rules + 2 篇 reference，索引 35 条（rule 33 / reference 2）**，覆盖率 100.0%。
  - `01-pattern-selection.md`（5 节）：引入门槛（三个必须同时成立的条件）、语言原生特性优先、模式成本与复杂度匹配、「写简单代码」是正确答案的四种情形、模式的退出条件。含「两个实现」的正确计数方式（测试替身算一个，「以后可能加的那个」不算）与退出评估的操作性问法（「如果今天从零写，还会引入它吗」）
  - `02-creational.md`（4 节）：单例、工厂方法、建造者、抽象工厂与原型（低频合并）
  - `03-structural.md`（5 节）：适配器、装饰器、外观、代理、组合与桥接与享元（低频合并）。含代理与装饰器的区分判据（代理管**是否/何时/何处**访问，装饰器管访问时**额外做什么**）
  - `04-behavioral.md`（7 节）：策略、观察者、命令、模板方法、责任链、状态、低频五模式（中介者/迭代器/访问者/备忘录/解释器）合并
  - `05-antipatterns.md`（6 节）：过度模式化、上帝对象、贫血领域模型、服务定位器、单例滥用、模式套模式。每条给「识别信号 + 为什么错 + 正确做法指向」，落地禁令引用对应技术领域而非重写
  - `06-modern-alternatives.md`（6 节）：**本领域唯一允许点名语言特性的一篇**——替代关系总览、委托替代策略与命令、事件机制替代观察者、值语义类型替代原型、模式匹配替代访问者、容器生命周期替代单例与简单工厂。约束是「只点名特性，不写 API 用法」，4 处 .NET 类型名命中均为替代关系表中的特性点名
  - `reference/gof-pattern-catalog.md`：23 个 GoF 模式速查（意图 + 典型误用 + 现代替代），**不含代码**；另附按「已被替代程度」的四分组（已被语言完全覆盖 / 多数场景被替代 / 前提严格但未被替代 / 仍是常用正解），该分组在引入决策时比 GoF 的三分类更有用
  - `reference/pattern-decision-guide.md`：从症状到模式的反向索引——按代码中观察到的九类现象反查候选模式。**每个症状的第一步都是「先确认」**，多数情况下这一步就得出「不需要改」
- **每条 rule 固定四要素：意图 → 引入信号 → 误用信号 → 不该用的情形。** 「误用信号」是本领域的质量标尺——写不出误用信号的内容不做成 rule。实测 `02`-`04` 三篇「误用」出现 5/6/8 次，等于各篇小节数加合并条目的共同误用信号一处，每条都有判据。
- **`level` 全部 33 条为 MUST，是实测结果而非默认填值**——按小节统计正文的「必须/禁止/应该/可以」措辞数后定级，33 个二级小节每节都含至少一条「必须」或「禁止」。
- **`enforcement` 分布 `review` 27 / `ci` 3 / `advisory` 3**。「该不该引入某模式」本质是设计意图判断，工具只能判外壳（存在一个叫 `XxxStrategy` 的接口）判不了实质（这个抽象是否必要），故 `review` 占压倒多数。3 条 `ci` 均通过外壳检验：`02.singleton` 与 `05.singleton-abuse`（静态自身访问点是可被分析器直接查出的成员形态，且该形态本身就是被禁的实质）、`05.service-locator`（全局按类型解析的调用可查）。3 条 `advisory` 是三篇的低频模式合并条目。
- **低频模式按型合并而非各造一条**：抽象工厂+原型、组合+桥接+享元、中介者+迭代器+访问者+备忘录+解释器共合并为 3 条。给解释器单独一条会让按 `level: MUST` 检索的消费者拿到一条在桌面客户端场景永不适用的硬性要求。
- **与 `architecture` 的边界写死在两处**：`00-README.md` 的四领域边界表（同一主题「策略模式」下四方各回答什么），以及 `01-pattern-selection.md § 3` 只留引用不重写——「模式成本与复杂度匹配」的权威是 `architecture/rules/06-style-selection.md § 1. 架构成本与问题复杂度匹配`。实测该措施有效：两条同名条目的查重分数只有 **0.203**。
- `catalog.json` 追加 `design-patterns` 领域记录，`consumers` 为空数组（尚无消费者 skill，消费者建设是后续独立决策）。

### Changed

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

### Fixed

- **补齐 6.0.0 漏改的 `README.md` 领域职责边界清单**。6.0.0 更新了首段的领域列表（含 `architecture`），但「领域职责边界」那一段仍是六领域，`architecture` 未登记职责。本次一并补入 `architecture` 与 `design-patterns` 两条职责说明。

**验收**：`check_index.py` 409 → **444** 条 OK；`check_refs.py --strict` 113 → **121** 文件 OK（新增 6 篇 rules + 2 篇 reference 进入扫描范围，32 处跨领域引用无一处标题写错）；`--audit` 显示 `design-patterns` 覆盖率 100.0%、`enforcement` 填写率 100%、无孤儿文件；`unittest` 133 全绿；`git diff --check` 无空白污染。

**三项硬性查重判据全部通过**：

| 判据 | 结果 |
|---|---|
| `design-patterns` ↔ `csharp.03.*` 无 ≥0.6 候选 | ✅ 最高 0.188 |
| `design-patterns` ↔ `architecture.06.style-selection` 无 ≥0.6 候选（两新领域间未造语义环的证据） | ✅ 最高 0.507，且同名条目 `cost-complexity-match` 仅 0.203 |
| `design-patterns` ↔ `wpf.03.*`/`wpf.16.*` 的 0.4-0.6 候选逐对判定 | ✅ 仅 1 对（0.443） |

0.4-0.6 区间四对候选的判定理由（均为**合理分层**，不迁移）：`architecture.09.lifetime-architecture-impact` ↔ `02.singleton`（0.509，前者讲生命周期的状态共享含义，后者讲单例模式的引入与误用信号）；`architecture.06.no-style-legitimate` ↔ `01.simple-code-is-correct`（0.507，同一立场的系统级与类族级两个粒度，正是 spec 定死的分工形态）；`architecture.01.assembly-location` ↔ `05.service-locator`（0.469，共有词项来自「全局访问点」但约束对象不同）；`06.events-over-observer` ↔ `wpf.03.event-subscription`（0.443，判断层 vs 落地层，本领域已显式引用该 wpf 条目）。

## [6.0.0] - 2026-08-29

`csharp` 五条架构条款的通用部分收窄，改为引用 5.1.0 新建的 `architecture` 领域。这是 5.1.0 预告的迁移改造——新建领域只完成了一半工作，若不做本次收窄，同一条约束会在两个领域各自完整表述一遍，等于把重复从一处变成两处。

**不兼容性**：五条 `csharp` 条目的正文范围与 `summary` 收窄，按 `id` 检索的消费者拿到的内容变了。`id`/`file`/`anchor` 全部不动，检索仍能命中；但读到的约束只剩 C# 特有增量，通用部分需按正文中的引用跳转到 `architecture`。经 grep 确认这五条**无任何消费者 skill 引用**，实际影响面仅限直接检索索引的使用者。

### Changed

- **五条 `csharp` 条目的正文收窄为「引用 + C# 特有增量」**，通用约束归入 `architecture`：

  | `id` | 摘除的通用部分（去向） | 保留的 C# 特有增量 |
  |---|---|---|
  | `csharp.01.layering-direction` | 分层模型的选择与统一、依赖单向向内、禁循环与越层、跨层契约（`architecture/rules/01-layering.md` § 1、§ 2、§ 3） | 层与项目（程序集）一一对应，依赖方向由 `ProjectReference` 承载以便编译器直接拦截；跨层接口定义在内层项目；测试项目引用边界 |
  | `csharp.03.solid-principles` | 五原则的可执行检查项表、SRP 常见误读（`architecture/rules/02-design-principles.md` § 1） | `public` 接口新增成员会破坏所有实现者（C# 特有的演进成本）、DIP 抽象归属内层项目、上帝类不通过 review |
  | `csharp.03.composition-over-inheritance` | 复用优先组合、禁为复用方法而继承、深继承链须 review（`architecture/rules/02-design-principles.md` § 2） | 用 `sealed` 标记不打算被继承的类 |
  | `csharp.03.dependency-injection` | 组合根唯一性、禁服务定位器与静态服务、生命周期的架构含义、构造期不得阻塞（`architecture/rules/09-composition-root.md` § 1、§ 3、§ 4） | 构造函数注入（禁属性注入与 `IServiceProvider` 直注）、`Transient`/`Scoped`/`Singleton` 的对应用途、`HttpClient` 注册为 `Singleton`、`Lazy<T>` 惰性推迟 |
  | `csharp.03.domain-modeling-ddd` | 聚合根唯一入口、一次事务一个聚合、领域事件、领域层纯净性（`architecture/rules/03-ddd.md` § 4、§ 6、§ 7） | 值对象用 `record` / 实体用 `class` + 身份标识、领域层项目禁引 EF Core 与 `HttpClient`、领域类型禁带 `[Table]`/`[JsonPropertyName]` 标注 |

- **`csharp.03.composition-over-inheritance` 的 `level` 由 MUST 降为 SHOULD**。摘除三条「必须/禁止」通用条款后，该节仅剩「**应该**：用 `sealed` 标记不打算被继承的类」一条——`level` 取小节最强条款级别，实测即为 SHOULD。级别声明必须跟随正文实际措辞，否则索引宣称的强度高于正文，review 时无从执行。
- **两条 `enforcement` 由 `review` 改为 `ci`**，因为收窄后剩下的内容变成了工具可无歧义判定的落地约束（通过外壳检验：判的是实质而非外壳）：
  - `csharp.01.layering-direction`：剩余条款是「层与项目一一对应、依赖方向由 `ProjectReference` 承载」——项目引用关系由编译器与架构测试库直接判定
  - `csharp.03.domain-modeling-ddd`：剩余条款是「值对象用 `record`、领域层项目禁引 EF Core、领域类型禁带持久化标注」——类型选择、项目引用与特性标注均可由分析器判定
- 五条的 `summary` 改写为反映收窄后的实际内容，并注明通用部分的去向；`reviewed_at` 更新为 2026-08-29（正文本次被实读并确认）。
- `csharp/00-README.md`：领域边界声明补入 `architecture`（「架构层面的『该不该、选哪个、边界在哪』引用 architecture」）；「与仓库已有资产的关系」新增一行，点明 `01` 章第 6 节与 `03` 章第 1、2、6、8 节的通用约束在该领域。
- `architecture/00-README.md`：C# 落地侧的章节清单由「§ 6 与 § 1、§ 8」更正为「§ 6 与 § 1、§ 2、§ 6、§ 8」——5.1.0 写入时按当时预定的三条迁移清单，实际迁移为五条。
- `csharp/rules/01-project-structure.md`、`csharp/rules/03-design-principles.md` 篇首「更新历史」记录本次去重。

### Fixed

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

## [5.1.0] - 2026-08-29

新增 `architecture` 领域（第 7 个领域），承载**语言无关**的架构风格、分层契约、设计原则与选型判据。此前这类约束零散寄生在 `csharp` 领域内——架构级判断（依赖该指向哪、边界怎么定、什么规模该引入 DDD）挂在「C# 语言与通用工程实践」下，检索者无法按架构维度找到它们，非 C# 场景也无从复用。

本次是**纯新增**，故按 Minor。`csharp` 侧的重复条款尚未收窄——下一个版本做迁移改造，届时按 Major（`csharp` 五条条目的正文范围与 `summary` 会变）。

### Added

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

### Changed

- 根 README 顶部版本号与「当前收纳领域」一句补入 `architecture`。

### 已知待处理（下一版本）

`find_duplicates.py` 检出 6 对 `architecture` ↔ `csharp` 的 ≥0.4 候选，最高 0.917（`architecture.02.composition-over-inheritance` ↔ `csharp.03.composition-over-inheritance`）。这是**预期状态**——本次只建领域，`csharp` 侧收窄在下一版本做。其中两对（0.917 与 0.537 的 `09.composition-root-uniqueness` ↔ `csharp.03.dependency-injection`）不在原定迁移清单内，是调研阶段按「架构/分层/SOLID/DDD」关键词反查时漏掉的——这两条的条款措辞里不含这些词。与 1.5.0 那次「按文件迁移会漏」是同一类教训的另一个变体，已补入 spec 的迁移清单（3 条 → 5 条）。

## [5.0.0] - 2026-08-28

治理元数据从 `git` 试点推广到全部规范领域：`enforcement` 填写率 3.7%（12/326）→ **100%（326/326）**。此前该字段只在 12 条 `git` 规则上有值，等于一套定义完整、有校验器保护、但实际只覆盖 3.7% 内容的元数据——消费者无法用它做任何全库判断。

按 Major 升版的原因是 `skill-authoring` 三条 `level` 由 `SHOULD` 改为 `MUST`（见下方 Changed），这是不兼容语义变化。治理字段本身的补齐是纯增量。

### Changed

- **`skill-authoring` 三条 `level` 由 `SHOULD` 修正为 `MUST`**——正文含「必须/禁止」措辞，索引却标 `SHOULD`，违反根 README 已写明的「`level` 取该小节最强条款的级别」。逐条读正文判 `enforcement` 时暴露：
  - `skill-authoring.04.self-contained`（§3 自包含脚本）：正文含「**禁止**：依赖 `node_modules`/`Gemfile` 等外部安装步骤才可运行的脚本」
  - `skill-authoring.05.gotchas`（§5.1 Gotchas 章节）：正文含两条「**必须**」（Gotchas 须放 `SKILL.md` 内；纠正后须回填）
  - `skill-authoring.05.plan-validate-execute`（§5.5 Plan-Validate-Execute）：正文含「**必须**：关键在中间的校验脚本」

  对消费者的影响：按 `level: MUST` 过滤硬性要求的消费者此前会漏掉这三条；按 `SHOULD` 检索推荐做法的消费者会少三条命中。三条的 `id`/`file`/`anchor` 均未变更，无需改引用。
- 根 README 的「可选字段是渐进引入的治理元数据」改为反映现状：`enforcement`/`status`/`applies_to`/`reviewed_at`/`owner` 已在全部 `rule` 条目填满，schema 层仍可选（漏填不报错），实际是新增条目时的约定。漏填不会被校验拦住，只会在治理数据里留空洞。
- 根 README 的 `enforcement` 判定表例子由清一色 git 场景扩为覆盖三个领域，并补入判 `ci` 的操作性检验：**工具判的是该小节的实质，还是只是它的外壳？只判外壳的填 `review`。** 原型是 `git.02.commit-hooks`——"hook 是否存在"可自动判定（外壳），但该节实质要求是"不得绕过"，只能人判。同时明确该字段的语义归属：本仓库无 CI 也无 hook，`enforcement` 对自身是声明性元数据，标 `ci` 的 130 条指的是被这些规范约束的**项目**的 CI 该拦什么。

### Added

- `csharp`（142 条）、`wpf`（132 条）、`skill-authoring`（40 条）全部 `rule` 条目补齐五个治理字段：`enforcement`、`status: active`、`applies_to`、`reviewed_at: 2026-08-28`、`owner: desktop client team`。全库 `enforcement` 分布 `ci` 130 / `review` 183 / `advisory` 13。
  - `csharp` 58 `ci`：集中在 01 章工程配置（csproj/global.json/.editorconfig/CI 顺序）、02 章命名与布局（10 条，分析器 + `.editorconfig` 主场）、04 章异步反模式（`.Result`/`.Wait()`/`async void`/`ConfigureAwait` 是 Roslyn 强项）、06 章 Dispose 模式与终结器（成套 CA 规则）、10 章依赖清单（CPM/浮动版本/包源/漏洞/许可证）、12 章测试工程形态（框架统一、命名布局、断言库、覆盖率门禁）、14 章注入与弱算法（扫描器专长）、11/17 章的日志库统一与 XML 注释完整性
  - `wpf` 51 `ci`：01/02 章工程与命名（`-windows` 后缀、Desktop workload、生成文件标记、`x:Name` 形态）、04 章 XAML 结构（命名空间、`x:Name`/`x:Key` 分工、BAML 编译）、09 章线程（Timer 类型选择、`.Result`、`async void`、`ConfigureAwait`）、13 章安全（硬编码密钥、拼接 SQL、明文 HTTP、弱哈希、签名）、14 章可访问性与本地化（`AutomationProperties` 缺失、硬编码字号与字符串、硬编码日期格式）、15 章打包（Release/版本一致/pdb/签名）、以及 06/16 章的依赖属性与 Behavior 生命周期（`DependencyProperty` 声明形态、`OnAttached`/`OnDetaching` 配对可静态检出）
  - `skill-authoring` 13 `ci`：一半是 `skills-ref validate` 直接判定的（frontmatter 六字段、目录结构、正文行数上限、相对路径引用、`uv run` 自包含脚本、禁止交互提示），另一半是 eval 流程里有明确数值门槛的（触发率阈值、train/validation 切分比例、带/不带 skill 双跑基线、benchmark delta 记录）——这类的判定标准写在规则里，脚本能核对
  - `advisory` 13 条为横向对比表与优先级排序类内容（测试框架对比、Mock 框架对比、推荐语言特性、性能优先级、弱引用适用场景等），它们不表达可拦截的约束
  - `csharp.13.repo-asset-contract` 补 `source` 指向 `reference/refit.md`。其余条目按"规则自解释时不填"的既定判据留空，`source` 不追求覆盖率
- 根 README 新增「reviewed_at：读过才填」章节：该字段语义是"正文最近一次被人实际读过并确认仍成立的日期"，不是"索引行最近编辑日期"。批量刷新而不读正文会让它变成看起来在治理、实际零保证的数字，比留空更糟。因此批量填元数据须按领域逐文件读正文，不按 `id` 列表批处理——本次即按此执行，也正是这一约束让上述三条 `level` 不符被发现。

## [4.2.0] - 2026-08-28

`csharp` 领域索引覆盖率补齐（81.8% → 96.2%，超过 `wpf` 的 94.3%）。补之前先修了覆盖率算法本身——旧算法用 `min(条目数, 二级章节数)` 封顶，只比数量不看落点，会让条目集中的文件掩盖真实空缺。

### Added

- `csharp/index.jsonl` 新增 19 条 rule 条目（124 → 143）：`05-error-handling.md` 日志与异常，`06-memory-resource.md` 弱引用/终结器，`07-performance.md` 热点路径识别/字符串/异步性能/基准测试，`08-concurrency.md` 锁选择矩阵/静态可变状态，`09-data-access.md` 数据访问基础/模型验证/数据访问测试，`10-dependency-management.md` 中央包管理（CPM），`11-observability.md` 指标与追踪/配置，`13-api-design.md` 客户端契约同步/与仓库资产，`14-security.md` 日志与脱敏，`17-comments-docs.md` 文档质量。
- 根 README 索引粒度规范新增「覆盖率不追求 100%」章节：明确覆盖率是**诊断指标而非达标指标**，列出三类有意不登记的小节（落地模板与快速上手、通篇跨章导航的小节、约束已由其他章节承载），并记录「联动 X 章」措辞是重复的可靠信号。此前该数字缺少"什么算满"的定义——把它追平会逼出两类坏条目：给操作指南强造 rule 条目，以及给已有真源的约束造第二个检索入口。

### Changed

- **`csharp/rules/13-api-design.md` §6「契约测试」去重**：该节与 `csharp.12.contract-test`（`12-testing.md` §10）互写「联动」，实则「公共契约变更配契约测试」与 12 章的「变更须跑回归」「禁止无测试保护上线」是同一约束的两次表述——两边互认权威、实则无单一真源，与 3.0.0 处理的 `git` ↔ `csharp` 语义环同型。通用条改为引用 `rules/12-testing.md` § 10. 契约测试，本节只留 API 设计侧特有的「后端契约变更须同步回归客户端契约」。`anchor` 未变更，无消费者需同步。
- 根 README 覆盖率说明补充：`anchor` 指向三级标题时其父二级章节记为已覆盖。

### Fixed

- 覆盖率统计从「条目数与章节数取小」改为按 `anchor` 落点计算。旧算法让 `csharp/rules/12-testing.md` 的 17 条记为 14/14 满分，真实只覆盖 13 个二级章节——多出的条目把另一个小节的真实空缺掩盖成了满分。修正后 `csharp` 由虚高的 82.6% 回到真实的 81.8%，差距确认为真实存在后才开始补条目。

## [4.1.0] - 2026-08-28

### Added

- 根 README 新增「status：废弃条目的过渡期」章节。此前 `status` 只在字段表里列了 `active`/`deprecated`/`experimental` 三个枚举值，没有任何关于"怎么废弃一条规则"的规定——结果全库 326 条无一使用 `deprecated`，3.0.0 废弃 `csharp.15.quality-gate-overview` 时只能直接删索引行，按旧 `id` 检索的消费者只得到「查不到」而非「已废弃，改用 `git.03.pr-conventions`」。
- 废弃机制定为**保留正文 + 标题加「已废弃」标记 + `anchor` 不变**，配三条强制要求（正文标题带标记、`summary` 含替代去向、不得保留 `enforcement: ci`），并禁止其他条目的 `source` 指向已废弃小节。四项均由 `check_index.py` 校验。`anchor` 保持不变是关键取舍——改 `anchor` 会让按 `file`+`anchor` 固定映射的消费者立刻失效，等于用破坏性变更实现一个本意是给过渡期的机制。
- 明确废弃属不兼容语义变化按 Major 升版本，废弃条目在下一个 Major 移除正文与索引行；并给出例外：从未被引用且刚建立不久的条目（当次提交内的笔误、重复登记）直接删除即可。

### Changed

- 字段表 `status` 行补充指引，指向新增章节的三条要求。

## [4.0.1] - 2026-08-28

`check_refs.py` 扫描范围扩到知识库正文后的首轮修复（此前该校验器只看 `plugins/*/skills/`，正文内的 `§` 引用无人看守）。

### Fixed

- `git/reference/commit-message-tooling.md` §3.1 末段声称 `rules/02-commit-messages.md` §2 有「CI 侧二次校验」这一说法——**该措辞在规范中不存在**，§2 只约束本地 pre-commit / commit-msg hook，并明确把耗时检查「交给 CI」而未规定 CI 侧二次校验。真正对应的是 §3 的「CI 集成 secret scanning，在 PR 阶段拦截」。已改为引用 §3。

### Changed

- 补齐知识库正文内 11 处只写章节号、未写标题的 `§` 引用（`git/rules/02-commit-messages.md` 1 处、`git/reference/branching-workflows.md` 3 处、`git/reference/commit-message-tooling.md` 7 处）。裸章节号引用无法与标题交叉校验，章节重编号后会静默指向别的内容。全库 `check_refs.py --strict` 由 12 处问题降为 0。

## [4.0.0] - 2026-08-28

用 `knowledge-base-maintain` 1.4.0 新增的 `find_duplicates.py` 做全库跨领域查重，处理评分最高的 4 对 C# ↔ WPF 重复。这批重复是自动查重的首次实战产出——3.0.0 那次 `git` ↔ `csharp` 语义环靠人工通读才发现，本次 4 对中的 3 对排在候选前三名。

### Changed

- **破坏性：`wpf.11.integration-test` 的 `level` 由 `MUST` 降为 `SHOULD`**。通用条款（验证真实协作、可控环境、禁止连生产资源、禁止写成慢速 E2E）迁出后，该小节只剩一条 `应该` 级的 WPF 特有条款，原 `MUST` 已不反映正文实际措辞。按 `level` 取小节内最强条款级别的既定规则，此处只能是 `SHOULD`。按 `level` 做拦截强度分档的消费者需重新评估该条目。
- **`wpf/rules/11-testing.md` §1「测试分层」去重**：通用分层原则改为引用 `csharp/rules/12-testing.md` § 1. 测试策略与金字塔，本篇只保留 WPF 侧的术语对应（通用规范的 E2E 层在 WPF 即 UI 自动化测试）与「禁止只有 UI 自动化没有单元测试」。
- **`wpf/rules/11-testing.md` §7「集成测试」去重**：验证对象、可控环境与两条禁止项改为引用 `csharp/rules/12-testing.md` § 7. 集成测试，本篇只补 WPF 特有的一条（重点验证 ViewModel ↔ 服务 ↔ 持久化链路）。
- **`wpf/rules/01-environment.md` §1「目标框架策略」去重**：统一 `TargetFramework`、优先 LTS、用 `global.json` / `Directory.Build.props` 固化等通用约束改为引用 `csharp/rules/01-project-structure.md` § 1. 目标框架策略，本篇只保留 `-windows` 后缀必需性与 LTS 支持期语义两条 WPF 特有约束。
- **`wpf/rules/01-environment.md` §7「构建与 CI」去重**：CI 步骤顺序、SDK 与 `global.json` 一致、NuGet 缓存、构建可复现、产物不入库等通用约束改为引用 `csharp/rules/01-project-structure.md` § 8. 构建与 CI，本篇只保留 Desktop workload 安装、workload 缓存、禁止依赖本地设计器三条。
- 上述 4 个条目的 `title`/`summary` 同步收窄为其正文实际保留的 WPF 特有内容，并注明通用约束所在的 csharp 章节——去重后仍按旧 summary 检索会误以为 wpf 侧承载完整规则。
- 两个 wpf 规范文件的 `anchor` **未变更**，按 `file` + `anchor` 定位的消费者不受影响；本仓库两个 review skill（`wpf-code-review` / `csharp-code-review`）均未引用这两个文件，无消费者需同步。

### Fixed

- `wpf/rules/11-testing.md` 篇首原已声明「通用测试策略沿用团队约定，本篇聚焦 WPF 特有测试问题」，但 §1 与 §7 的正文把通用条款完整重述了一遍，与自身声明矛盾。本次去重使正文与该声明一致。

## [3.0.0] - 2026-08-27

按 `docs/superpowers/plans/2026-08-27-knowledge-base-optimization.md` 执行 Phase 2（规则内容质量治理），以 `git` 领域为试点，并处理试点中发现的 `git` ↔ `csharp` 跨领域重复。

### Removed

- **破坏性：删除索引条目 `csharp.15.quality-gate-overview`**——其承载的「CI 全绿才可合并」「禁止红灯合并」「门禁配置随仓库提交、禁止 `--no-verify`」属通用协作约束，已由 `git.03.branch-protection`、`git.03.pr-conventions`、`git.02.commit-hooks` 承载。按旧 ID 做固定映射的外部消费者需改引用 `git` 领域对应条目；本仓库内无消费者引用该条目（`csharp-code-review` 审查清单 10 类均为编码层面，不涉及 15 章）。
- `csharp/rules/15-quality-review.md` 删除原 §1「质量门禁总览」整节与 §4 中「所有变更走 PR + review」「PR 描述说明变更意图、测试情况、验证方式」两条，改为在篇首与节首引用 `knowledge-base/git/`。

### Changed

- **破坏性：`csharp.15.*` 其余 4 条条目的 `anchor` 随章节重编号变更**（`3.→2.` 复杂度与代码度量、`4. Code Review 流程→3. Code Review 内容重点`、`5.→4.` review 标准、`6.→5.` 技术债务管理）。
- `csharp.15.code-review-process` 的 `title`/`summary` 收窄为「C# code review 的内容重点与结论要求」——PR 流程条款迁出后，原措辞已不覆盖该条目实际内容。
- **解开 `git` ↔ `csharp` 语义环**：`git/rules/03-pull-requests.md` §1 原写「CI 通过 + review 批准才可合并（联动 `csharp/rules/15-quality-review.md`）」，而 csharp 又独立重述同一条 git 规则，形成两边互认权威、实则无单一真源的环。现按领域职责（README 载明 `git` 负责版本控制协作）归入 git，并把「禁止红灯合并」并入该条，`git.03.pr-conventions` 的 `summary` 同步补录。
- `csharp/00-README.md` 落地手段第 3 条与文件地图第 15 行同步更新，标明 CI 门禁与 PR 流程见 `knowledge-base/git/`。
- 根 README 记录实测结论：**76% 的索引条目所在小节混有不同级别条款，`level` 取该小节最强条款的级别**。这是对消费者安全的默认（不会把强制条款误判为推荐），但命中 `MUST` 条目不代表该小节每句话都是硬性要求，消费者仍需按 `file` + `anchor` 读正文。该结论修正了优化计划中"WPF 132 条全 MUST 说明规则被过度强化"的原始判断——真实原因是索引粒度与条款级别的粒度不匹配，而非规则本身被写强。
- 根 README 索引字段表中 `source` 的说明由"内部 ADR / issue / PR 路径"改为明确的 `<file>#<标题文本>` 形式，与校验器实际解析规则一致。
- 迁移/重命名文件时需同步的引用由四处增加为五处，新增"索引 `source` 字段中的内部引用"。

### Added

- `git` 领域 12 条 rule 补齐治理元数据：`enforcement`（`ci` 8 / `review` 3 / `advisory` 1）、`status`、`applies_to`、`reviewed_at`、`owner`，该领域治理字段覆盖率 100%。
- `git` 领域 8 条 rule 补齐 `source`，指向承载其理由的 `reference/` 小节或权威外部规范（如 `git.02.commit-hooks` → `reference/commit-message-tooling.md#2.3 为什么不能靠"团队自觉"代替 hook`）。理由不复制进规范正文——规范给约束、reference 给理由是既定分层，复制会产生两份需同步的同一事实。
- 根 README 新增"level 与 enforcement 的分工"章节：`level` 表达违反的严重程度（由正文措辞决定），`enforcement` 表达靠什么拦住（由能否被工具无歧义判定决定），附三档判定标准与例子。
- 根 README 新增"source：规则到理由的连接"章节：内部引用形式 `<file>#<标题文本>`、外部 URL、校验范围与不追求全覆盖的取值约定。

### Fixed

- 补上 2026-08-23（v1.5.0）那次迁移的漏项：当时按 `csharp/16-collaboration.md` 这一个文件迁移协作条款，但同类条款还散落在 `15-quality-review.md` 的「质量门禁」「Code Review 流程」标题下未被扫到——重复按语义分布，按文件迁移会漏。

## [2.0.0] - 2026-08-27

按 `docs/superpowers/plans/2026-08-27-knowledge-base-optimization.md` 执行 Phase 0（基线与保护网）+ Phase 1（索引粒度与目录册）。

### Changed

- **破坏性：领域目录结构调整为"元数据在根、内容按类型分组"**——各领域下的编号规范文件迁移到 `<domain>/rules/`，`00-README.md` 与 `index.jsonl` 保留在领域根目录，`reference/` 与 `rules/` 同级并列。涉及 `csharp`（17 篇）、`wpf`（17 篇）、`git`（5 篇）、`skill-authoring`（5 篇），共 44 个文件（`git mv` 迁移，保留历史）。
- **破坏性：索引 `file` 字段路径变更**——266 条记录的 `file` 从 `NN-*.md` 改为 `rules/NN-*.md`（仅此一字段变动，其余字段逐字未改）。按旧路径做固定映射引用的外部消费者需同步更新；本仓库内引用已全部同步。
- 同步更新全部内部与消费者引用（共 4 类）：各领域 `00-README.md` 文件地图、`reference/` 与 `rules/` 正文交叉引用（74 处）、`csharp-code-review` / `wpf-code-review` SKILL.md 的审查清单定位表（23 处）、`.claude/rules/skill-conventions.md`（2 处）、`.claude/skills/commit-cc-plugin/SKILL.md`（含 10 处 Markdown 链接目标）。正文头部"更新历史"与本 CHANGELOG 中记录当时事实的路径不改写。
- 领域 README"索引与机器消费"章节措辞更新：`reference/` 的并列对象由"本篇编号规范文件"改为"`rules/` 下的规范文件"。

### Added

- 根级 `catalog.json` 领域目录册：登记 6 个领域的内容分类、维护者、状态、主要消费者与最近审阅日期，纳入一致性校验（与实际领域目录双向一致，登记缺失或多余均报错）。
- 根 README 新增"索引粒度规范"章节：可独立判断的规则单独登记、导航标题不登记、`reference` 默认按整篇登记、文件级汇总条目与节级条目可并存。
- 根 README 索引字段表扩展为必填/可选两栏，新增可选治理字段 `enforcement`（`ci`/`review`/`advisory`）、`status`（`active`/`deprecated`/`experimental`）、`source`、`applies_to`、`reviewed_at`、`owner`——渐进引入，未填不报错，填了必须合法。
- 补齐 `csharp/rules/12-testing.md` 细粒度索引 7 条：测试项目布局、断言风格、覆盖率目标、测试数据自包含、契约测试、慢测试过滤、CI 覆盖率采集（覆盖率 79.7% → 82.7%）。
- 补齐 `skill-authoring` 节级索引 35 条：格式规约 6 条、描述优化 6 条、质量评估 8 条、脚本使用 7 条、最佳实践 8 条（覆盖率 14.7% → 100%）。原 5 条文件级汇总条目保留为文件入口，ID 不变。
- 根 README 维护约定补充：校验的单领域/全局作用域划分、`--audit` 报告用法、迁移文件时须同步的四处引用。

索引记录总数 285 → 327（rule 266 → 308，reference 19 条不变）。

## [1.11.0] - 2026-08-27

### Added
- 新增 `dotnet` 领域：收纳 .NET Framework、现代 .NET、Windows 兼容性与生命周期的描述性知识
- 新增 `dotnet/reference/windows-dotnet-support-matrix.md`：Windows 与 .NET Framework / .NET 5+ 支持矩阵整理稿
- 根知识库领域说明补充 `dotnet`、`csharp`、`wpf` 三者的职责边界

## [1.10.4] - 2026-08-26

### Changed
- `media/reference/media-parameters.md` 扩展：§2 帧率新增「提高帧率的两种方式」（复制帧 vs 运动插帧）与「降低帧率=丢帧」；§4 新增「由目标体积反推目标码率」（two-pass 场景的 `目标大小×8192÷时长−音频码率` 公式及 8192 的进制来源）
- `media/reference/video-codecs.md` §1 新增「关键帧（I/P/B 帧）与 GOP」小节：帧间预测、关键帧间隔与 seek/截取精度的权衡、`-c copy` 对齐关键帧的实际影响
- `media/index.jsonl` 同步更新 `media.ref.media-parameters`、`media.ref.video-codecs` 的 `summary`/`tags`

## [1.10.3] - 2026-08-26

### Changed
- `media/reference/streaming-protocols.md` 第 8 节扩展为「与 ffprobe / ffplay 的关系」：新增 ffplay 能直接播放 HLS/RTSP/RTMP 网络流的说明与命令示例，及 RTSP TCP 传输、RTMP 构建依赖、直播不可回拖、DRM 不可解密等注意点
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `tags`/`summary`（新增 `ffplay` 标签）

## [1.10.2] - 2026-08-26

### Changed
- `media/reference/streaming-protocols.md` 重构为面向零基础读者的通俗版：新增"为什么切分片"问题引入、播放器播放 HLS 的 4 步流程、各协议 URL 实例与一句话人话总结、CDN 说明、文末术语速查表，并在常见误区补充"扩展名非铁律"条目
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `summary`

## [1.10.1] - 2026-08-26

### Changed
- `media/reference/streaming-protocols.md`：标题改为"流媒体传输与分发协议：HLS、RTMP、RTSP、DASH 与 WebRTC"（去除 M3U8 平列与赘余的"与相关协议"）；将 M3U8 并入 HLS 章节作为其播放清单组件介绍，并展开 HLS 完整组成——分片、两级清单（Media/Master Playlist）、码率自适应、加密与 DRM、直播/点播差异
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `title`/`summary`

## [1.10.0] - 2026-08-26

### Added
- `media` 领域新增 `reference/streaming-protocols.md`：流媒体传输与分发协议讲解——M3U8 播放清单、HLS/DASH HTTP 分片分发、RTMP 推流、RTSP 会话控制协议、WebRTC 实时互动，及直播生态推流/分发/互动分工
- `media/index.jsonl` 登记 1 条 reference 索引记录 `media.ref.streaming-protocols`
- `media/00-README.md` 阅读路径与文件地图同步补充 streaming-protocols 条目

## [1.9.1] - 2026-08-26

### Changed
- `media/reference/media-parameters.md` 扩展：新增常用视频比例表（16:9/4:3/21:9/9:16/1:1）与横屏/竖屏判定方法、码率单位进制换算（码率 1000 进制 vs 存储 1024 进制、bit 与 Byte 换算）
- `media/reference/video-quality.md` 扩展：新增第 6 节 LUT（Look-Up Table）——1D/3D LUT 机制、常见文件格式、与 HDR/SDR 色调映射的关系、常见注意点
- `media/index.jsonl` 同步更新 `media.ref.media-parameters`、`media.ref.video-quality` 的 `summary`/`tags`/`title`

## [1.9.0] - 2026-08-26

### Added
- 新增 `media` 领域：纯描述性知识库（无规范条款，全部为 reference），含 10 篇参考文档——媒体流结构基础、视频/音频封装格式、视频/音频编解码器、媒体参数（分辨率/帧率/码率）、音频参数（采样率/位深/声道）、视频质量（有损无损/CRF/HDR/色度采样）、字幕格式、ffprobe 字段映射
- `media/index.jsonl` 登记 10 条 reference 索引记录

## [1.8.0] - 2026-08-23

### Added
- `git` 领域新增 `reference/pull-request-concepts.md`：Pull Request 概念讲解——PR 不是 GitHub 特有（GitLab 叫 Merge Request）、PR 的代码评审/CI 门禁/合并关卡三大作用、何时该用 PR，是 `03-pull-requests.md` 的配套参考
- `git/index.jsonl` 新增 1 条 reference 索引记录 `git.ref.pull-request-concepts`

### Changed
- `03-pull-requests.md` 正文头部补充指向配套 reference 的引用说明

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
