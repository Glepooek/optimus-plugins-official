# design-patterns 领域新建实施计划

**日期：** 2026-08-29
**对应 spec：** `docs/superpowers/specs/2026-08-29-design-patterns-domain.md`
**状态：** 待批准

---

## 与 architecture / algorithms 的执行关系

本领域**必须在 architecture 阶段 A 之后执行**，理由是单向依赖：

```
architecture 阶段 A（10 篇 rules，含 06-style-selection.md）
        │
        │ design-patterns 的「模式成本与复杂度匹配」要引用
        │ architecture/rules/06-style-selection.md § N. <标题>
        ▼
design-patterns 阶段 P（本计划）
```

`06-style-selection.md` 的章节号与标题在 A 阶段写完才确定，提前引用等于凭空猜一个 `§ N`——`check_refs.py` 会直接报「无 § N 章节」。

**已确认的全局顺序：** A（architecture）→ B（csharp 架构迁移）→ **P（本领域）**→ C（hello-algo 提取）→ D（algorithms rules）。

## 工作量预估

| 阶段 | 内容 | 产出 | 预估 | 可独立提交 |
|---|---|---|---|---|
| P1 | 领域骨架 + catalog 登记 | 2 文件 + 1 处登记 | 小 | ❌（并入 P2） |
| P2 | `01` + `05` + `06` 三篇（判断层核心） | 16-19 条 rule | 中等 | ✅ |
| P3 | `02`-`04` 三篇（23 个 GoF 模式） | 16-21 条 rule | 大 | ✅ |
| P4 | 2 篇 reference + 索引 + csharp §7 迁移改造 | 2 条 reference + 3 处改造 | 中等 | ✅（须紧随 P3） |

**总计：** 34-42 条新条目，2-3 次提交（P1 并入 P2；P3、P4 可合并提交）。

**关键路径上的不确定性**：P3 的 23 个模式最容易写成教材。缓解手段是 P2 先做——`01-pattern-selection.md` 定下「误用信号」的写法范式后，P3 照该范式套用；反过来先写 P3 会得到 21 条教材式条目再返工。

---

## 阶段 P1：领域骨架与登记

1. 创建 `knowledge-base/design-patterns/00-README.md`——参照 `csharp/00-README.md` 章节结构，规范级别复用 csharp 的 MUST/SHOULD/MAY 定义。**额外必须包含 spec 第一节的四领域边界表**（`architecture` / `design-patterns` / `csharp` / `wpf` 各回答什么问题）——这张表是本领域最容易被误用的地方，放进 README 让后续维护者第一眼看到
2. 创建空的 `knowledge-base/design-patterns/index.jsonl`
3. `knowledge-base/catalog.json` 的 `domains` 追加记录：

   ```
   domain: "design-patterns"
   title: "设计模式选用与反模式"
   categories: ["rules", "reference"]
   owner: "desktop client team"
   status: "active"
   consumers: []          # 尚无消费者 skill
   reviewed_at: "2026-08-29"
   notes: "模式的选用判据与误用识别；架构风格选型引用 architecture，语言落地引用 csharp，WPF 特有形态引用 wpf"
   ```

**验证：** `check_index.py design-patterns` 不报「领域未登记到 catalog.json」

---

## 阶段 P2：判断层核心三篇

**先做这三篇的理由**：它们确立「误用信号」的写法范式，P3 的 21 条按此套用。

### P2.1 `01-pattern-selection.md`

必须包含的小节（每节一条索引）：

| 小节 | 必须回答 | 引用约束 |
|---|---|---|
| 引入门槛 | 一个模式要满足什么条件才值得引入（扩展点是否真实存在、实现数是否 >1、变化是否已发生而非预期会发生） | — |
| 语言原生特性优先 | 什么情况下语言特性能替代模板类模式 | 详细替代关系见 `06-modern-alternatives.md` |
| 模式成本与复杂度匹配 | **只留引用，不重写** | 引用 `architecture/rules/06-style-selection.md § N. <标题>` |
| 「写简单代码」是正确答案的情形 | 什么时候不用任何模式才是对的 | — |
| 模式的退出条件 | 已引入的模式什么时候该拆掉（唯一实现存续 N 个版本、扩展点从未被用过） | — |

🔴 **CHECKPOINT**：写「模式成本与复杂度匹配」这节前，先读 A 阶段产出的 `architecture/rules/06-style-selection.md`，确认其实际章节号与标题，再写引用。**不要凭 spec 里的预期标题猜**。

### P2.2 `05-antipatterns.md`

按反模式登记，每条给「识别信号 + 为什么错 + 正确做法指向」：

| 反模式 | 落地条款已在何处（本篇只写判断层，落地改引用） |
|---|---|
| 过度模式化 | 无落地条款，本篇为唯一真源 |
| 上帝对象 | `csharp.03.solid-principles`（§1 含「上帝类不通过 review」）→ 引用 |
| 贫血领域模型 | `architecture/rules/03-ddd.md`（A 阶段产出）→ 引用 |
| ServiceLocator | `csharp` §6 依赖注入 + `wpf.03.no-servicelocator` → **引用两处**，本篇只写「为什么它是反模式」 |
| 单例滥用 | `csharp.03.design-pattern-moderation`（P4 改造后保留的 C# 侧禁令）→ 引用 |
| 模式套模式 | 无落地条款，本篇为唯一真源 |

### P2.3 `06-modern-alternatives.md`

**唯一允许点名 .NET 特性的一篇**，但只点名不写 API 用法。按替代关系登记：

| 替代关系 | 允许写 | 禁止写 |
|---|---|---|
| 委托 / lambda ← 策略、命令 | 「简单算法族用委托参数替代策略接口」 | `Func<Order,decimal>` 的注册方式、`Action<T>` 签名 |
| 事件 / `IObservable` ← 观察者 | 「语言内置的事件机制已实现观察者，不需手写 Subject」 | `IObservable<T>.Subscribe` 的实现细节 |
| 不可变值类型 ← 原型 | 「带值语义拷贝的类型使原型模式失去必要性」 | `record` 的 `with` 表达式语法 |
| 模式匹配 / `switch` 表达式 ← 访问者 | 「封闭类型层次上的分派用模式匹配，不引入访问者」 | `switch` 表达式的具体语法形态 |
| DI 容器 ← 单例、工厂方法 | 「实例生命周期由容器管理，模式层不再需要单例」 | `AddSingleton` vs `AddScoped` 的 API |

### P2 验证

```bash
# 确认是规范条款而非叙述
grep -c '必须\|禁止\|应该\|不应' knowledge-base/design-patterns/rules/0{1,5,6}*.md
# 语言无关自检：01 与 05 应无命中，06 的命中须逐处人工确认是「特性点名」非「API 用法」
grep -n 'IServiceCollection\|IObservable\|Func<\|Action<\|record\|AddSingleton\|switch 表达式' knowledge-base/design-patterns/rules/0{1,5,6}*.md
```

🔴 **CHECKPOINT — 范式确认**：P2 写完后，从 `01`/`05` 中挑 3 条，逐条问「怎样算违反这条」。答不出的说明写成了教材，须改写或移入 reference。**这 3 条的最终形态即 P3 的范式**，不通过不进入 P3。

---

## 阶段 P3：23 个 GoF 模式三篇

按 spec 第二节的粒度表登记（高频模式各一条，低频合并一条）。每条固定四要素：

```
意图（一句话）→ 引入信号（什么现象出现时考虑它）→ 误用信号（什么现象说明用错了）→ 不该用的情形
```

**「误用信号」是本阶段的质量标尺**——写不出误用信号的条目等于没有判据，应合并进低频条目或移入 `reference/`。

### P3.1 `02-creational.md`（4-5 条）

| 条目 | 关键判据 |
|---|---|
| 单例 | 误用信号：类内静态 `Instance` 属性、单例持有可变状态、为「全局访问方便」而非「实例唯一性约束」而用。通用禁令在此，C# 的 DI 侧表述引用 `csharp.03.design-pattern-moderation` |
| 工厂方法 | 引入信号：创建逻辑需按运行时条件分派且分派点多于一处。误用信号：只有一个产品类型的「工厂」、工厂只是 `new` 的一层包装 |
| 建造者 | 引入信号：必填参数 >4 或存在参数组合约束。误用信号：为 3 个参数的对象写建造者 |
| 抽象工厂 + 原型（合并） | 共同判据：无明确的产品族切换需求 / 无深拷贝需求时不引入。原型在支持值语义类型的语言中多数已被替代（详见 `06`） |

### P3.2 `03-structural.md`（5-6 条）

| 条目 | 关键判据 |
|---|---|
| 适配器 | 引入信号：外部契约与内部契约不一致且外部不可改。误用信号：用适配器掩盖内部设计缺陷（两个自己写的接口之间加适配器） |
| 装饰器 | 引入信号：横切能力需可组合叠加。误用信号：装饰链超过 3 层、装饰器改变了被装饰者的契约语义 |
| 外观 | 引入信号：子系统对外暴露面过大且调用序列固定。误用信号：外观变成上帝对象（转发数十个方法） |
| 代理 | 引入信号：访问控制/延迟加载/远程访问需对调用方透明。误用信号：代理与被代理者接口不一致 |
| 组合 + 桥接 + 享元（合并） | 共同判据：树形结构无递归遍历需求 / 抽象与实现无独立变化维度 / 无大量细粒度对象的内存压力时，三者均不引入 |

### P3.3 `04-behavioral.md`（7-8 条）

| 条目 | 关键判据 |
|---|---|
| 策略 | 引入信号：出现按类型分派的连续 `if`/`switch` 且算法族需运行时切换。误用信号：只有一个实现且无扩展预期。简单场景优先委托（引用 `06`） |
| 观察者 | 引入信号：一对多通知且发布方不该知道订阅方。误用信号：订阅未配对取消导致泄漏（WPF 侧落地引用 `wpf.03.event-subscription`） |
| 命令 | 引入信号：操作需可撤销/可排队/可记录。误用信号：为无撤销需求的简单调用套命令对象（WPF 侧引用 `wpf.03.icommand`） |
| 模板方法 | 引入信号：算法骨架固定、步骤可变且变化点 ≤3。误用信号：钩子方法过多导致子类必须理解全部骨架；组合优于继承的既定立场（引用 `csharp.03` §2）意味着优先考虑策略 |
| 责任链 | 引入信号：处理者集合运行时可变、处理与否由处理者自决。误用信号：链上顺序隐式依赖、链断裂无兜底 |
| 状态 | 引入信号：对象行为随状态显著变化且状态迁移规则复杂。误用信号：状态类之间互相直接跳转导致迁移图不可读 |
| 中介者 + 迭代器 + 访问者 + 备忘录 + 解释器（合并） | 共同判据：这五个在桌面客户端场景低频。中介者易退化为上帝对象；迭代器已被语言内置迭代机制覆盖；访问者在支持模式匹配的语言中多被替代（引用 `06`）；备忘录仅在真有撤销栈需求时引入；解释器仅在真需自定义 DSL 时引入 |

### P3 验证

```bash
grep -c '必须\|禁止\|应该\|不应' knowledge-base/design-patterns/rules/0{2,3,4}*.md
# 语言无关：三篇均应无命中
grep -n 'IServiceCollection\|IObservable\|Func<\|Action<\|record\|IEnumerable\|AddSingleton' knowledge-base/design-patterns/rules/0{2,3,4}*.md
# 每条都有误用信号：三篇中「误用」出现次数应 ≥ 条目数
grep -c '误用' knowledge-base/design-patterns/rules/0{2,3,4}*.md
```

---

## 阶段 P4：reference、索引与 csharp 迁移改造

### P4.1 两篇 reference

1. `reference/gof-pattern-catalog.md`：23 个模式速查表——意图一句话 + 典型误用 + 现代替代。**不含代码**（spec 硬约束，防止顺手抄一遍 GoF 示例）
2. `reference/pattern-decision-guide.md`：从症状到模式的反向索引——「代码里出现 X 现象 → 考虑哪几个模式 → 各自代价」。这篇是本领域对消费者最有用的入口，因为实际提问方式是「这段代码该怎么改」而非「策略模式是什么」

### P4.2 索引登记

1. 逐条写 `index.jsonl`（**末尾追加，不重排**），必填八字段 + 五个治理字段
2. `enforcement` 按外壳检验逐条判：
   - `ci`（少数）：单例的静态 `Instance` 属性、`ServiceLocator.Get<T>()` 调用——Roslyn 可无歧义查出
   - `review`（绝大多数）：「该不该引入」「抽象是否必要」都是设计意图判断，工具只能判外壳（有个叫 `XxxStrategy` 的接口存在）判不了实质
   - `advisory`：模式对比表、低频模式合并条目
3. `applies_to`：`["设计模式", "语言无关"]`；**`06-modern-alternatives.md` 的条目为 `["设计模式", "C#", ".NET"]`**（该篇点名语言特性）
4. `source`（数组形式）：`01`/`05`/`06` → `reference/pattern-decision-guide.md#<标题>`；`02`-`04` → `reference/gof-pattern-catalog.md#<标题>`

### P4.3 csharp §7 迁移改造

对 `csharp/rules/03-design-principles.md` § 7. 设计模式适度使用（现有 4 条）：

| 原条款 | 处置 |
|---|---|
| 必须：模式服务目标，不为模式而模式；优先语言原生表达力替代模板类模式 | **迁出** → `design-patterns/rules/01-pattern-selection.md` 与 `06-modern-alternatives.md` |
| 应该：常见模式按需采用（策略/观察者/仓储/工厂） | **迁出** → 拆入 `02`/`04` 对应条目 |
| 禁止：为单例而单例——实例由 DI 容器管理，类内静态 `Instance` 反模式禁止 | **保留**（DI 容器是 .NET 具体机制），通用禁令部分改指 `design-patterns/rules/02-creational.md § N. <标题>` |
| 禁止：照搬 GoF 模板而不评估是否真正解决当前问题 | **迁出** → `01-pattern-selection.md` |

节首加引用行：`模式选用判据见 knowledge-base/design-patterns/rules/01-pattern-selection.md § N. <标题>。C# 侧的附加要求：`

🔴 **CHECKPOINT**：摘除三条后该节只剩单例一条。按 spec 判断这仍是**有效的 C# 特有增量**（DI 容器管理生命周期是 .NET 机制），不走废弃流程。但要实际确认收窄后的正文不是「只有一行引用 + 一条条款」的空壳——若确实过薄，考虑将其并入 §6 依赖注入而非独立成节（此时 `anchor` 变更属破坏性，须按 Major 处理并在 CHANGELOG 写明）。

### P4.4 索引与文件地图同步

1. `csharp/index.jsonl` 的 `csharp.03.design-pattern-moderation`：`summary` 收窄为「DI 容器时代单例的 C# 侧禁令」；`title` 同步；`id`/`file`/`anchor` **不动**
2. `csharp/00-README.md`：03 章说明补「设计模式选用判据见 `knowledge-base/design-patterns/`」
3. `design-patterns/rules/*` 中需要 C#/WPF 落地细节的位置，反向引用（带章节标题）

### P4 阶段验收

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py" --top 20
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

**三项硬性验收**（缺一项即返工，不是「记录理由后放行」）：

| # | 判据 | 不通过说明什么 |
|---|---|---|
| 1 | `design-patterns` ↔ `csharp.03.*` 无 ≥0.6 候选 | §7 迁移没到位，通用条款在两处都还写着 |
| 2 | `design-patterns` ↔ `architecture.06.style-selection` 无 ≥0.6 候选 | **两个新领域间造出了语义环**——本领域最大风险，必须回到 `01-pattern-selection.md` 把该节收成纯引用 |
| 3 | `design-patterns` ↔ `wpf.03.*`/`wpf.16.*` 的 0.4-0.6 候选逐对判定 | 属「判断层 vs 落地层」合理分层，记录理由后放行；若出现 ≥0.6 说明本领域写了 WPF 落地 |

版本：`knowledge-base` → **Major**（`csharp.03.design-pattern-moderation` 的 `summary` 与正文范围收窄属不兼容语义变化）。具体版本号按本领域实际提交时的当前版本递增。

---

## 全局验收（P1-P4 完成后）

| # | 检查 | 期望 |
|---|---|---|
| 1 | `check_index.py`（全库） | `OK`，记录数增加 34-42 |
| 2 | `check_index.py --audit` | `design-patterns` 的 `enforcement` 填写率 100%；`catalog.json` 双向一致；无孤儿文件 |
| 3 | `check_refs.py --strict` | `OK`，扫描文件数增加 8 篇 |
| 4 | `unittest discover` | 133 全绿 |
| 5 | `find_duplicates.py --top 20` | 上表三项硬性判据全部通过 |
| 6 | 语言无关自检 | `rules/` 中 .NET 类型名仅在 `06-modern-alternatives.md` 命中，且为特性点名非 API 用法 |
| 7 | 误用信号自检 | `02`-`04` 三篇中「误用」出现次数 ≥ 条目数 |
| 8 | `git diff --check` | 无空白污染 |

---

## 已定决策（不再询问）

| 项 | 结论 | 依据 |
|---|---|---|
| 独立成域 vs 扩写 csharp 03 章 | **独立成域**——模式判据语言无关；03 章 179 行 8 节已达容量上限，§7 只有 4 条容不下 23 个模式；判断层与落地层需分档检索 | spec 第二节，含实测行数 |
| 执行时机 | **architecture 阶段 A 之后**——本领域要引用 `architecture/rules/06-style-selection.md`，其章节号 A 阶段才确定 | 单向依赖，提前引用必然报「无 § N 章节」 |
| 与 architecture 的边界 | 通用立场「模式成本与复杂度匹配」权威在 `architecture.06`，本领域只引用不重写；`architecture` 不写任何单个 GoF 模式判据 | spec 第一节；验收第 5 项第 2 条作为硬性门禁 |
| 索引粒度 | 按**判断单元**登记，非按模式名——高频模式各一条，低频（抽象工厂/原型/组合/桥接/享元/中介者/迭代器/访问者/备忘录/解释器）按型合并 | 给解释器单独一条会让按 `MUST` 检索的消费者拿到永不适用的硬性要求 |
| 代码示例 | `rules/` 与 `reference/` **均不含代码**——实现归 `csharp` | 防止 reference 变成 GoF 示例抄本 |
