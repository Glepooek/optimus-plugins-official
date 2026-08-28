# design-patterns 领域新建设计文档

**日期：** 2026-08-29
**版本：** 1.0.0
**状态：** 待批准

---

## 背景

知识库现有 6 个领域，即将新增 `architecture` 与 `algorithms`（见 `2026-08-29-architecture-algorithms-domains.md`）。设计模式是第三块空白，且性质与前两者都不同——**它不是「没写」，而是「只写了落地、没写判断」**。

现状实测：

| 事实 | 依据 | 含义 |
|---|---|---|
| 全库精确匹配「XX模式」「GoF」只有 **2 行**，均在 `csharp/rules/03-design-principles.md:166-171`（§7 设计模式适度使用） | `grep -rn -E '单例模式\|工厂模式\|…\|GoF\|设计模式' knowledge-base/` | 模式的**判断层**几乎为零 |
| 模式的**落地条目有 20+ 条**：`wpf.03.icommand`（命令）、`wpf.03.event-subscription`（事件聚合器 = 观察者/中介者）、`wpf.06.attached-property`、`wpf.16.behavior-*`（装饰/策略在 WPF 的形态）、`csharp.06.idisposable-implementation`（Dispose 模式）、`csharp.03.design-pattern-moderation` | 逐条读 `title` 确认 | 落地不缺，缺的是「该不该用、什么时候是误用」 |
| `csharp/rules/03-design-principles.md` §7 只有 **4 条**条款，其中「常见模式按需采用」一条把策略/观察者/仓储/工厂四个模式压成了一行 | `sed -n '166,172p'` | 该节是一个被压缩到极限的占位，容不下任何模式的实际判据 |
| `csharp.03.design-pattern-moderation` **零消费者引用** | `grep -rn 'design-pattern-moderation\|03-design-principles' plugins/ .claude/` 零命中 | 迁移改造的引用同步面极小 |

## 为什么独立成域，而不是扩写 `csharp` 03 章

三条理由，按分量排序：

1. **模式是语言无关的**。策略模式在 C#/Java/TypeScript 里的判据完全相同（算法族需运行时切换、条件分支按类型分派）。把它放在「C# 语言与通用工程实践」域下，与 `architecture` 独立出去的理由同型——`catalog.json` 已载明 `csharp` 负责语言层。
2. **`csharp` 03 章已达容量上限**。179 行 8 节，§7 只有 4 条。要给 23 个 GoF 模式 + .NET 常见模式写判据，至少需要 5-8 篇正文，塞进 03 章会让它膨胀到 1000 行以上，与其余 16 章的形态完全脱节。
3. **判断层与落地层需要分档检索**。消费者问「这里该不该上策略模式」和「C# 里策略模式怎么写」是两个不同的问题，前者属 `design-patterns`，后者属 `csharp`/`wpf`。混在一处则无法按 `id` 分档命中。

## 一、领域定位与边界

| 项 | 值 |
|---|---|
| `domain` | `design-patterns` |
| `title` | 设计模式选用与反模式 |
| `categories` | `["rules", "reference"]` |
| `owner` | desktop client team |
| 定位 | **模式的选用判据与误用识别**——该不该用某个模式、什么信号表示用错了、语言原生特性能否替代 |

### 与三个相邻领域的硬边界

这是本领域最需要说清的部分。四方各自回答一个不同的问题：

| 领域 | 回答的问题 | 例子（同一主题「策略模式」） |
|---|---|---|
| `architecture` | 系统该怎么切分、边界在哪 | 「算法族属于领域层还是应用层」 |
| **`design-patterns`** | **该不该用这个模式、用错的信号是什么** | **「只有一个实现且无扩展预期时禁止引入策略模式；条件分支按类型分派是引入信号」** |
| `csharp` | 在 C# 里怎么落地 | 「策略用接口 + DI 注册，简单场景优先 `Func<T,TResult>` 委托」 |
| `wpf` | 在 WPF 里的特有形态 | 「WPF 中交互策略走 Behavior，见 `wpf.16.behavior-command-division`」 |

**判据一句话**：出现「什么时候」「该不该」「误用信号」→ `design-patterns`；出现具体类型名与 API → `csharp`/`wpf`；出现「哪一层、哪个边界」→ `architecture`。

### 与 architecture 的重叠风险（必须先划界）

`architecture/rules/06-style-selection.md`（阶段 A 即将写）与本领域是**同一立场在两个粒度上的表述**，若不划界会造出新的语义环：

| | `architecture.06.style-selection` | `design-patterns` 的选用条款 |
|---|---|---|
| 粒度 | **架构风格**（分层/六边形/整洁/DDD） | **单个模式**（策略/工厂/装饰…） |
| 决策影响面 | 整个系统或一个限界上下文 | 一个类族 / 一处扩展点 |
| 典型问句 | 「这个项目该不该上 DDD」 | 「这三个 if 分支该不该改成策略」 |

**执行约束**：`design-patterns` 的「模式成本须与问题复杂度匹配」这条通用立场，**权威在 `architecture.06.style-selection`**，本领域只留引用（带章节标题），不重写。反向地，`architecture` 不写任何单个 GoF 模式的判据。

## 二、内容结构

```
knowledge-base/design-patterns/
├── 00-README.md              # 文档目的、适用范围、规范级别（复用 csharp 的 MUST/SHOULD/MAY 定义）、阅读路径、文件地图、四领域边界表
├── index.jsonl
├── rules/
│   ├── 01-pattern-selection.md      # 选用总则：引入门槛、语言原生特性优先、模式成本与复杂度匹配（引用 architecture.06）、什么时候「写简单代码」是正确答案
│   ├── 02-creational.md             # 创建型：单例（含 DI 时代的禁令）、工厂方法、抽象工厂、建造者、原型
│   ├── 03-structural.md             # 结构型：适配器、装饰器、外观、代理、组合、桥接、享元
│   ├── 04-behavioral.md             # 行为型：策略、观察者、命令、模板方法、责任链、状态、中介者、迭代器、访问者、备忘录、解释器
│   ├── 05-antipatterns.md           # 反模式识别：过度模式化、上帝对象、贫血模型、ServiceLocator、单例滥用、模式套模式
│   └── 06-modern-alternatives.md    # 现代语言特性对模式的替代：委托/lambda 替代策略与命令、`IObservable`/事件替代观察者、`record` 替代原型、`switch` 表达式替代访问者
└── reference/
    ├── gof-pattern-catalog.md              # 23 个 GoF 模式速查：意图一句话 + 典型误用 + 现代替代（不含代码，代码归 csharp）
    └── pattern-decision-guide.md           # 从症状到模式的反向索引：「代码里出现 X 现象 → 考虑哪几个模式 → 各自代价」
```

**预估条目数：** 32-40 条 rule + 2 条 reference。

### 各篇的条目粒度判断

`02`-`04` 三篇覆盖 23 个 GoF 模式，若每个模式登记一条会得到 23 条颗粒极细的条目。按根 README 的「可独立用于合规判断的规则单独登记」判据，实际按**判断单元**登记而非按模式名：

| 篇 | 登记方式 | 预估 |
|---|---|---|
| `01-pattern-selection.md` | 按小节，每节一条 | 5-6 条 |
| `02-creational.md` | 高频模式（单例、工厂、建造者）各一条；低频模式（抽象工厂、原型）合并一条 | 4-5 条 |
| `03-structural.md` | 高频（适配器、装饰器、外观、代理）各一条；低频（组合、桥接、享元）合并一条 | 5-6 条 |
| `04-behavioral.md` | 高频（策略、观察者、命令、模板方法、责任链、状态）各一条；低频（中介者、迭代器、访问者、备忘录、解释器）合并一条 | 7-8 条 |
| `05-antipatterns.md` | 按反模式，每条一个 | 6-7 条 |
| `06-modern-alternatives.md` | 按替代关系，每条一组 | 5-6 条 |

**低频模式合并成一条的理由**：解释器模式在桌面客户端场景几乎不出现，给它单独一条会让按 `level: MUST` 检索的消费者拿到一条永不适用的硬性要求。合并条目的 `summary` 写明「低频模式的共同判据：无明确复用需求时不引入」。

### 撰写约束

- **语言无关**：`rules/` 正文出现 `IServiceCollection`、`IObservable<T>`、`record`、`Func<T,TResult>` 这类 .NET 类型名即越界——`06-modern-alternatives.md` 是**唯一例外**，因为「现代语言特性替代模式」必须点名特性；该篇的处置是**点名特性但不写 API 用法**（可以说「用委托替代策略接口」，不能说「`Func<Order,decimal>` 的注册方式」）
- **每条必须给「误用信号」**：只说「策略模式用于算法族」是教材语气，无法用于合规判断。必须写成可检验的形式——「只有一个实现且无扩展预期时禁止引入策略；出现按类型分派的连续 `if/switch` 是引入信号」
- **不写代码示例**：模式的代码实现归 `csharp`，本领域给判据。`reference/gof-pattern-catalog.md` 也不含代码（spec 明确约束，防止提取时顺手抄一遍 GoF 示例）

## 三、跨领域引用改造清单

| # | 位置 | 改动 |
|---|---|---|
| 1 | `csharp/rules/03-design-principles.md` § 7. 设计模式适度使用 | 四条条款中前两条（模式服务目标、常见模式按需采用）与第四条（禁止照搬 GoF）属通用判断，迁入 `design-patterns/rules/01-pattern-selection.md`，本节改为引用；**保留第三条**「为单例而单例——实例由 DI 容器管理，类内静态 `Instance` 反模式」的 C# 侧表述（DI 容器是 .NET 具体机制），但通用禁令部分改指 `design-patterns/rules/02-creational.md` |
| 2 | `csharp/index.jsonl` 的 `csharp.03.design-pattern-moderation` | `summary` 收窄为「DI 容器时代单例的 C# 侧禁令」；`id`/`file`/`anchor` **不变** |
| 3 | `csharp/00-README.md` 文件地图与「权威参考」 | 03 章说明补「设计模式选用判据见 `knowledge-base/design-patterns/`」 |
| 4 | `design-patterns/rules/01-pattern-selection.md` | 「模式成本与复杂度匹配」改为引用 `architecture/rules/06-style-selection.md § N. <标题>`，不重写 |
| 5 | `design-patterns/rules/04-behavioral.md` 命令/观察者条目 | 反向引用 `wpf.03.icommand`、`wpf.03.event-subscription`，标明 WPF 侧的具体形态 |
| 6 | `design-patterns/rules/05-antipatterns.md` ServiceLocator 条 | 该反模式在 `csharp.03`（§6 依赖注入）与 `wpf.03.no-servicelocator` 已各有落地条款，本领域只写「为什么它是反模式」的判断层，落地引用两处 |

**关键约束：** 引用一律带章节标题（`§ 7. 设计模式适度使用` 形式），否则 `check_refs.py --strict` 告警且章节重编号时静默失效。

## 四、治理字段规格

| 字段 | 值 |
|---|---|
| `status` | `active` |
| `reviewed_at` | 落地当日 |
| `owner` | `desktop client team` |
| `applies_to` | `["设计模式", "语言无关"]`；`06-modern-alternatives.md` 的条目为 `["设计模式", "C#", ".NET"]`（该篇点名语言特性） |
| `enforcement` | 预期**以 `review` 为主**——「该不该引入某模式」本质是设计意图判断，工具只能判外壳（有没有一个叫 `XxxStrategy` 的接口），判不了实质（这个抽象是否必要）。`ci` 仅给真能机械判定的：单例的静态 `Instance` 属性、`ServiceLocator.Get<T>()` 调用（Roslyn 可查）。`advisory` 给模式对比表与低频模式合并条目 |
| `source` | `01`/`05`/`06` 指向 `reference/pattern-decision-guide.md#<标题>`；`02`-`04` 指向 `reference/gof-pattern-catalog.md#<标题>` |

## 五、版本影响

| 项 | 变化 | 级别 |
|---|---|---|
| `knowledge-base` | 视与 architecture/algorithms 的提交顺序而定，**本领域自身触发 Major**——`csharp.03.design-pattern-moderation` 的 `summary` 与正文范围收窄属不兼容语义变化 | **Major** |
| `catalog.json` | 追加 `design-patterns` 领域记录 | 随上 |
| `knowledge-base-maintain` | 预期无需升版（无脚本改动） | — |
| `.claude-plugin/marketplace.json` | **不升级**——不涉及 `plugins/` | — |

## 六、验收标准

1. `check_index.py`（全库）→ `OK`，记录数增加 34-42 条
2. `check_index.py --audit` → `design-patterns` 的 `enforcement` 填写率 100%，覆盖率有数值
3. `check_refs.py --strict` → `OK`，扫描文件数增加 8 篇
4. `python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts` → 133 全绿（无脚本改动）
5. `find_duplicates.py --top 20` → **三项硬性判据**：
   - `design-patterns` ↔ `csharp.03.*` 无 ≥0.6 候选（§7 迁移到位的证据）
   - `design-patterns` ↔ `architecture.06.style-selection` 无 ≥0.6 候选（两个新领域间未造语义环的证据）
   - `design-patterns` ↔ `wpf.03.*`/`wpf.16.*` 的 0.4-0.6 候选逐对判定，属「判断层 vs 落地层」合理分层的记录理由后放行
6. `rules/` 语言无关自检：`grep -n 'IServiceCollection\|IObservable\|Func<\|record\|IEnumerable' design-patterns/rules/*.md` 仅在 `06-modern-alternatives.md` 有命中，且命中处为特性点名而非 API 用法

## 七、风险与未决项

| 风险 | 处置 |
|---|---|
| **与 architecture 造出新语义环**（本领域最大风险） | 已在第一节定死边界：通用立场「模式成本与复杂度匹配」权威在 `architecture.06`，本领域只引用。验收第 5 项把它作为硬性判据检出 |
| 23 个 GoF 模式写成教材而非规范 | 撰写约束已定「每条必须给误用信号」；写完逐条自问「怎样算违反这条」，答不出的移入 `reference/` |
| 低频模式（解释器、备忘录、桥接）强行凑条目 | 已定按判断单元而非模式名登记，低频合并成一条，`summary` 写明共同判据 |
| `06-modern-alternatives.md` 越界成 C# 教程 | 该篇是唯一允许点名 .NET 特性的，但只点名不写 API；验收第 6 项逐处核对 |
| 与 architecture/algorithms 三个新领域并行导致版本号打结 | 三份 spec 各自标明版本影响，实际按提交顺序取最高级别；本领域按 Major |

## 八、明确不做

- **不写模式的代码实现**——归 `csharp`；`reference/gof-pattern-catalog.md` 也不含代码
- **不做 pattern-review skill**——本次只建知识库，消费者 skill 是后续独立决策
- **不动 `wpf.03.*` / `wpf.16.*` 的 23 条落地条目**——它们与本领域是判断层 vs 落地层的合理分层
- **不在 `architecture` 里写任何单个 GoF 模式的判据**——边界的另一半，同样是硬约束
- **不为 23 个模式各造一条索引**——按判断单元登记，低频合并
