# Changelog — 设计模式选用与反模式

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 7.0.0 - 2026-08-29

新增 `design-patterns` 领域（第 8 个领域），承载设计模式的**判断层**——该不该引入某个模式、什么信号说明用错了、语言特性能否替代。此前这块不是「没写」而是「只写了落地、没写判断」：模式的落地条目有 20+ 条（`wpf.03.icommand`、`wpf.16.behavior-*`、`csharp.06.idisposable-implementation` 等），但全库精确匹配「XX模式」「GoF」只有 2 行，都在 `csharp/rules/03-design-principles.md § 7`——一个被压缩到 4 条条款的占位节，其中一条把策略/观察者/仓储/工厂四个模式压成了一行。

**不兼容性**：`csharp.03.design-pattern-moderation` 的正文范围与 `summary` 收窄，按 `id` 检索的消费者拿到的内容变了。`id`/`file`/`anchor` 全部不动。经 grep 确认该条目**零消费者 skill 引用**。收窄详情记在 `knowledge-base/csharp/CHANGELOG.md`。

#### Added

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

#### Fixed

- **补齐 6.0.0 漏改的 `README.md` 领域职责边界清单**。6.0.0 更新了首段的领域列表（含 `architecture`），但「领域职责边界」那一段仍是六领域，`architecture` 未登记职责。本次一并补入 `architecture` 与 `design-patterns` 两条职责说明。

**验收**：`check_index.py` 409 → **444** 条 OK；`check_refs.py --strict` 113 → **121** 文件 OK（新增 6 篇 rules + 2 篇 reference 进入扫描范围，32 处跨领域引用无一处标题写错）；`--audit` 显示 `design-patterns` 覆盖率 100.0%、`enforcement` 填写率 100%、无孤儿文件；`unittest` 133 全绿；`git diff --check` 无空白污染。

**三项硬性查重判据全部通过**：

| 判据 | 结果 |
|---|---|
| `design-patterns` ↔ `csharp.03.*` 无 ≥0.6 候选 | ✅ 最高 0.188 |
| `design-patterns` ↔ `architecture.06.style-selection` 无 ≥0.6 候选（两新领域间未造语义环的证据） | ✅ 最高 0.507，且同名条目 `cost-complexity-match` 仅 0.203 |
| `design-patterns` ↔ `wpf.03.*`/`wpf.16.*` 的 0.4-0.6 候选逐对判定 | ✅ 仅 1 对（0.443） |

0.4-0.6 区间四对候选的判定理由（均为**合理分层**，不迁移）：`architecture.09.lifetime-architecture-impact` ↔ `02.singleton`（0.509，前者讲生命周期的状态共享含义，后者讲单例模式的引入与误用信号）；`architecture.06.no-style-legitimate` ↔ `01.simple-code-is-correct`（0.507，同一立场的系统级与类族级两个粒度，正是 spec 定死的分工形态）；`architecture.01.assembly-location` ↔ `05.service-locator`（0.469，共有词项来自「全局访问点」但约束对象不同）；`06.events-over-observer` ↔ `wpf.03.event-subscription`（0.443，判断层 vs 落地层，本领域已显式引用该 wpf 条目）。
