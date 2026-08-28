# architecture 与 algorithms 双领域新建设计文档

**日期：** 2026-08-29
**版本：** 1.0.0
**状态：** 待批准

---

## 背景

知识库现有 6 个领域（`dotnet`/`csharp`/`wpf`/`git`/`media`/`skill-authoring`），缺两块：

- **软件架构**：DDD、六边形、整洁架构等**语言无关**的架构风格与选型判据。现状是零散地寄生在 `csharp` 领域内——`csharp.01.layering-direction`（分层与依赖方向）、`csharp.03.solid-principles`（SOLID）、`csharp.03.domain-modeling-ddd`（领域建模）三条承载了架构级约束，却挂在「C# 语言与通用工程实践」领域下。
- **数据结构与算法**：现有条目全是「用哪个集合、避免装箱」的工程约束（`csharp.07.*`、`csharp.08.*`），没有「为什么这个规模下 O(n²) 不可接受」「什么时候该换数据结构」的判断依据。外部素材为 `hello-algo` 1.3.0 C# 版（356 页，`C:\Users\Administrator\Desktop\pdf\hello-algo_1.3.0_zh_csharp.pdf`）。

## 调研事实（决定方案的实测依据）

### 架构侧

| 事实 | 依据 | 影响 |
|---|---|---|
| 三条待迁移条目**无任何消费者 skill 引用** | `grep -rn "layering-direction\|solid-principles\|domain-modeling-ddd\|分层与依赖方向\|SOLID\|领域建模" plugins/ .claude/` 零命中（排除 CHANGELOG） | 迁移的引用同步面极小，只需改 `csharp/00-README.md` 文件地图与 `csharp` 正文自身。**注：此调研按关键词反查，漏掉了两条措辞中不含这些词的条款——见第四节的 2026-08-29 修正，实际待迁移为 5 条** |
| `wpf/rules/01-environment.md` 已有两处引用指向 `csharp/rules/01-project-structure.md`（§1 目标框架、§8 构建与 CI） | 该文件第 9、85 行 | 这两处**不涉及**本次迁移的 §6，但迁移时须确认未连带破坏 |
| `csharp` 01 章 175 行 / 03 章 179 行 | `wc -l` | 摘除三节后两文件仍各有 5-7 节，不会空壳化 |

### 算法侧

| 事实 | 依据 | 影响 |
|---|---|---|
| PDF 规范性措辞**极稀疏**：22.5 万字正文中「必须」15 次、「禁止」**0** 次，而「需要」252 次、「注意」63 次 | 全书扫描计数 | 教材语气，**不能按小节切成 rule**。rules 必须由维护者从内容中**提炼**：判断依据取自书中事实，条款措辞由本仓库撰写 |
| 图解为 PDF 图片对象，前 60 页即 47 张，全书 300+ 张 | `pdfplumber` `page.images` 统计 | 纯文本提取会丢失全书核心价值载体。已决定：**图解改为指针**（`见原书图 2-6 / www.hello-algo.com`），不导出二进制入库 |
| 代码注释符被 PDF 连字替换破坏：`//` → `^/`、`===` → `^^=`、`...` → `^^.` | p33/p34 实读 | 提取脚本**必须**含字符修复层，否则示例代码全部损坏 |
| 表格纯文本提取错行（「实现方/式」被拆两行） | p33 实读 | 表格须走 `extract_table` 而非 `extract_text` |
| 全书 16 章：0 前言、1 初识算法、2 复杂度分析、3 数据结构、4 数组与链表、5 栈与队列、6 哈希表、7 树、8 堆、9 图、10 搜索、11 排序、12 分治、13 回溯、14 动态规划、15 贪心、16 附录 | 目录页提取 | 除 0/16 两章外的 15 章为 `reference/` 分篇依据 |

## 一、领域定位与边界

### architecture

| 项 | 值 |
|---|---|
| `domain` | `architecture` |
| `title` | 软件架构风格与设计原则 |
| `categories` | `["rules", "reference"]` |
| `owner` | desktop client team |
| 定位 | **语言无关**的架构风格、分层契约、设计原则与选型判据 |

**与 csharp 的分工（避免语义环的硬边界）：**

- `architecture` 承载「架构层面该怎么切、依赖该指向哪、边界怎么定」——不涉及任何 C# 语法或 .NET 类型。
- `csharp` 承载「在 C# 里如何落地」——`ServiceLocator` 反模式、`HttpClient` 生命周期、`record` vs `class` 这类语言级细化。
- 三条被迁移条目的**通用部分迁入 architecture**，`csharp` 原位置改为引用（带章节标题，可被 `check_refs.py` 交叉校验），并保留 C# 特有增量。这与 3.0.0 处理 `wpf` ↔ `csharp` 目标框架去重的做法同型。

### algorithms

| 项 | 值 |
|---|---|
| `domain` | `algorithms` |
| `title` | 数据结构与算法 |
| `categories` | `["rules", "reference"]` |
| `owner` | desktop client team |
| 定位 | 复杂度判断、数据结构选型、算法策略适用边界 |

**与 csharp 07/08 章的分工：**

- `algorithms` 回答「为什么」与「选哪个」——某规模下哪个复杂度量级不可接受、查找场景该用哪种结构、递归何时必须改迭代。
- `csharp.07.*` / `csharp.08.*` 回答「在 C# 里怎么写不踩坑」——`List` 预分配容量、避免装箱、并发集合原子方法。
- 两者是**合理分层**关系，不做迁移。但 `algorithms` 的 rule 撰写时须逐条对照 `csharp.07`/`csharp.08` 查重，命中真重复的改为引用。

## 二、architecture 领域内容结构

```
knowledge-base/architecture/
├── 00-README.md              # 文档目的、适用范围、规范级别（复用 csharp 的 MUST/SHOULD/MAY 定义）、阅读路径、文件地图
├── index.jsonl
├── rules/
│   ├── 01-layering.md              # 分层与依赖方向（承接 csharp.01.layering-direction 的通用部分）
│   ├── 02-design-principles.md     # SOLID 及其可执行检查项（承接 csharp.03.solid-principles）
│   ├── 03-ddd.md                   # DDD 战术+战略：聚合根、限界上下文、上下文映射（承接 csharp.03.domain-modeling-ddd 并补 csharp 完全没有的战略设计）
│   ├── 04-hexagonal.md             # 六边形架构：端口/适配器、驱动侧与被驱动侧
│   ├── 05-clean-architecture.md    # 整洁架构：四层同心圆、依赖规则、跨层数据传递
│   ├── 06-style-selection.md       # 风格选型判据：什么规模/团队/变更频率下选哪个，以及不选任何风格的合法情形
│   ├── 07-cqrs-and-slices.md       # CQRS 与垂直切片：读写分离的引入门槛与代价、按功能组织 vs 按技术层组织
│   ├── 08-module-boundaries.md     # 模块与程序集边界：何时拆项目、单体内模块化、循环依赖的架构级处置
│   ├── 09-composition-root.md      # 组合根与依赖装配：注册集中化、生命周期的架构含义、启动期校验
│   └── 10-cross-cutting.md         # 横切关注点归属：日志/缓存/事务/校验/授权 各自该落在哪一层
└── reference/
    ├── architecture-styles-comparison.md    # 分层/六边形/整洁/DDD 四种风格横向对比与取舍理由
    └── dotnet-architecture-decisions.md     # .NET/C# 生态的具体架构决策记录：单体 vs 微服务的实际门槛、MediatR 的收益与代价、Repository 在 EF Core 下是否仍必要、AutoMapper 类工具的取舍、模块化单体的落地形态
```

**预估条目数：** 38-46 条 rule + 2 条 reference。

> **阶段 A 实际产出（2026-08-29 落地后修正）：62 条 rule + 2 条 reference。** 高于预估的原因是按**小节**登记而非按篇合并——10 篇共 61 个二级小节，逐节实测措辞后确认每节都含至少一条「必须/禁止」，属可独立用于合规判断的规则，按根 README 的索引粒度判据须单独登记。不为贴合预估而合并条目。`enforcement` 分布 `review` 50 / `ci` 8 / `advisory` 4，`level` 61 节全部 MUST（实测每节最强条款级别，非默认值）。


### 扩充范围的选定依据（实测）

对 15 个候选架构主题逐一核对现有知识库覆盖后，确认这些是**架构决策层空白**——现有条目全属实现层：

| 主题 | 现有最接近的条目 | 它回答的 | 未回答的（架构决策层） |
|---|---|---|---|
| CQRS / 中介者 | 无任何条目 | — | 读写模型何时该分离、`MediatR` 这类中介者的收益是否抵得上间接层成本 |
| 垂直切片 | 无任何条目 | — | 按功能组织还是按技术层组织、切片间共享代码怎么放 |
| 缓存归属 | `csharp.07.caching-strategy` | 缓存必须设上限与过期策略 | 缓存该放哪一层、哪些数据不该缓存、缓存失效是谁的职责 |
| 模式引入 | `csharp.03.design-pattern-moderation` | 不为单例而单例、不照搬 GoF | 什么规模下该引入某个架构模式、引入门槛怎么定 |
| 组合根 | `csharp.01.project-type-conventions` | 可执行项目入口极薄、仅做组合根 | 注册该怎么组织、生命周期选择的架构含义、启动期是否校验依赖图 |
| 数据访问抽象 | `csharp.09.data-access-basics` | ORM 查询须异步、领域层禁用数据访问类型 | EF Core 之上是否仍需 Repository、`DbContext` 本身算不算 UoW |
| 服务边界 | `csharp.11.metrics-tracing` | 指标追踪走统一管道 | 单体拆微服务的实际门槛、模块化单体作为中间态 |
| 横切关注点 | `csharp.14.log-redaction` 等分散条目 | 各自的实现要求 | 这些关注点该由中间件/装饰器/拦截器中的哪个承载 |

**边界原则不变：** `architecture` 只写「该不该、选哪个、边界在哪」；一旦涉及 C# 语法或 .NET 类型的落地细节（`IOptions<T>` 怎么绑定、`IMemoryCache` 怎么配过期），归 `csharp`，architecture 处改为引用。`07`-`10` 四篇尤其容易越界，撰写时须逐条自检。

**必须写进 `06-style-selection.md` 的一条反向约束**（防止知识库变成「架构风格推销册」）：小规模 CRUD 应用不应为「显得规范」引入 DDD 战术模式，架构风格的成本必须与问题复杂度匹配。这与 `csharp.03.design-pattern-moderation`（模式适度使用）是同一立场在架构层的延伸，需在两处间建立引用而非重写。

## 三、algorithms 领域内容结构

```
knowledge-base/algorithms/
├── 00-README.md
├── index.jsonl
├── rules/
│   ├── 01-complexity.md      # 复杂度判断：量级取舍边界、最坏/平均之别、空间复杂度何时成为主约束
│   ├── 02-data-structure-selection.md  # 数据结构选型矩阵：数组/链表/栈/队列/哈希/树/堆/图 各自的适用与禁用场景
│   ├── 03-recursion-iteration.md  # 递归与迭代：栈深度风险、何时必须改迭代、尾递归在 .NET 的实际状况
│   └── 04-algorithm-strategy.md   # 算法策略适用边界：搜索/排序/分治/回溯/DP/贪心 各自的前提条件与误用代价
└── reference/
    ├── hello-algo-01-intro.md          # 第 1 章 初识算法
    ├── hello-algo-02-complexity.md     # 第 2 章 复杂度分析
    ├── hello-algo-03-data-structure.md # 第 3 章 数据结构
    ├── hello-algo-04-array-linkedlist.md
    ├── hello-algo-05-stack-queue.md
    ├── hello-algo-06-hash-table.md
    ├── hello-algo-07-tree.md
    ├── hello-algo-08-heap.md
    ├── hello-algo-09-graph.md
    ├── hello-algo-10-search.md
    ├── hello-algo-11-sort.md
    ├── hello-algo-12-divide-conquer.md
    ├── hello-algo-13-backtracking.md
    ├── hello-algo-14-dynamic-programming.md
    └── hello-algo-15-greedy.md
```

**预估条目数：** 15-20 条 rule + 15 条 reference（每章一条）。

### reference 提取规格

| 项 | 规格 |
|---|---|
| 工具 | `pdfplumber`（已确认可用），一次性脚本，**不入库**（提取是一次动作，不是可复用能力） |
| 章节切分 | 按 PDF 章标题（`第N章 ...`）分篇，跳过第 0 章前言与第 16 章附录 |
| 字符修复 | `^/` → `//`、`^^=` → `===`、`^^.` → `...`、`‑`（U+2011）→ `-`。修复表须在脚本里显式列出并在提取后抽样验证 |
| 表格 | 走 `extract_table`，输出 Markdown 表格 |
| 图解 | 原位置替换为 `> 📊 原书图 N-M：<图题>（图解见 https://www.hello-algo.com/chapter_xxx/）` |
| 页眉页脚 | 剔除 `第N章 ... www.hello-algo.com <页码>` 与孤立页码行 |
| 每篇头部 | 加一行来源声明：书名、版本、章号、许可证、原书地址、提取日期 |
| 许可证 | **已确认为 CC BY-NC-SA 4.0**（github.com/krahets/hello-algo 明示："The texts, code, images, photos, and videos in this repository are licensed under CC BY-NC-SA 4.0"）。三项条件均适用，其中 **SA 有实质影响**——见下方「许可证决策」 |

### 许可证决策（CC BY-NC-SA 4.0 的 SA 条款）

三项条件对本次的实际含义：

| 条件 | 对本仓库的要求 | 满足难度 |
|---|---|---|
| **BY** 署名 | 每篇 reference 头部标注作者（krahets）、书名、版本、原书地址 | 低，已在提取规格中 |
| **NC** 非商业 | 本仓库为内部开发工具链插件仓库，不销售、不作为商业产品交付 | 低，符合 |
| **SA** 相同方式共享 | **逐字提取的演绎作品须沿用 CC BY-NC-SA 4.0** | **有实质影响**——会在仓库内引入一块与其余内容授权不同的区域 |

SA 是本次唯一需要决策的点：15 篇逐字提取属演绎作品，须挂 CC BY-NC-SA 4.0；而 `rules/` 里由维护者**自行撰写**的条款只是「受该书启发的判断依据」，不构成演绎，不受 SA 约束（`source` 指向原书即满足学术引用惯例）。

**已定方案：逐字提取 + 目录级许可证隔离。** 具体落地：

- `knowledge-base/algorithms/reference/LICENSE`：放 CC BY-NC-SA 4.0 全文
- 每篇 `hello-algo-*.md` 头部：署名原作者（krahets）、书名、版本、章号、原书地址、许可证、提取日期
- `algorithms/00-README.md`：明确 `reference/` 目录内容授权为 CC BY-NC-SA 4.0，独立于仓库其余部分；`rules/` 为本仓库自撰内容，不受此约束
- **BY 条款要求署名原作者**，这是许可证的强制条件，不可省略

## 四、跨领域引用改造清单（architecture 迁移）

> **2026-08-29 修正：迁移清单由 3 条扩为 5 条。** 阶段 A 落地后跑 `find_duplicates.py` 实测，除原定三条外还检出两对高分候选：`architecture.02.composition-over-inheritance` ↔ `csharp.03.composition-over-inheritance`（**0.917，全库最高分**）与 `architecture.09.composition-root-uniqueness` ↔ `csharp.03.dependency-injection`（0.537）。前者是我写 `02-design-principles.md` § 2 时按通用原则表述，与 csharp 侧原文几乎逐字相同；后者是组合根条款与 csharp DI 章的重叠。这两条若不迁移，B 阶段做完仍会留下两对未处理的高分重复——等于新建领域只把重复从一处变成两处。调研阶段按「架构」「分层」「SOLID」「DDD」关键词反查时未命中它们，是因为它们的条款措辞里没有这些词。

| # | 位置 | 改动 |
|---|---|---|
| 1 | `csharp/rules/01-project-structure.md` § 6. 分层与依赖方向 | 通用条款（依赖单向向内、禁循环、禁越层、接口定契约）改为引用 `architecture/rules/01-layering.md § 2. 依赖方向` 与 `§ 3. 跨层契约`；分层模型选择部分引用 `§ 1. 分层模型的选择与统一`；保留 C# 特有的「测试项目引用边界」 |
| 2 | `csharp/rules/03-design-principles.md` § 1. SOLID 原则落地 | 通用条款改为引用 `architecture/rules/02-design-principles.md § 1. SOLID 原则的可执行检查项`；保留「上帝类不通过 review」这类 C# review 侧表述 |
| 3 | `csharp/rules/03-design-principles.md` § 8. 领域建模（若采用 DDD） | 通用条款改为引用 `architecture/rules/03-ddd.md § 4. 聚合`、`§ 6. 领域事件`、`§ 7. 领域层的纯净性`；保留「值对象用 `record`、实体用 `class` + 身份标识」这条 C# 类型选择 |
| 4 | **`csharp/rules/03-design-principles.md` § 2. 组合优于继承**（新增，0.917） | 通用条款（复用优先组合、禁为复用方法而继承、深继承链须 review）改为引用 `architecture/rules/02-design-principles.md § 2. 组合优于继承`；保留 C# 特有的「用 `sealed` 标记不打算被继承的类」 |
| 5 | **`csharp/rules/03-design-principles.md` § 6. 依赖注入**（新增，0.537） | 通用条款（依赖显式、禁服务定位器与静态服务、生命周期贴近用途、禁构造期阻塞）改为引用 `architecture/rules/09-composition-root.md § 1. 组合根的唯一性`、`§ 3. 生命周期选择的架构含义`、`§ 4. 构造期的约束`；保留 C# 特有的「`HttpClient` 注册为 `Singleton`」「`Lazy<T>` 惰性推迟」与两段 C# 代码示例 |
| 6 | `csharp/index.jsonl` 五条的 `summary` | 改为反映收窄后的内容，`anchor` **不变**（无消费者引用，但保持 `anchor` 稳定是既定原则）。涉及 `csharp.01.layering-direction`、`csharp.03.solid-principles`、`csharp.03.domain-modeling-ddd`、`csharp.03.composition-over-inheritance`、`csharp.03.dependency-injection` |
| 7 | `csharp/00-README.md` 文件地图 | 若 01/03 章标题因摘除小节而变化则同步；同时在「权威参考」类位置提及新领域 |
| 8 | `architecture/rules/*` 反向引用 | 架构条款需要 C# 落地细节时，反向引用 `csharp`（带章节标题）。A 阶段已在 `01`/`02`/`03`/`08`/`09` 五篇篇首写入 |

**关键约束：** 引用一律带章节标题（`§ 6. 分层与依赖方向` 形式），否则 `check_refs.py --strict` 会告警，且章节重编号时静默失效。

## 五、治理字段规格（两个领域一致）

| 字段 | 值 |
|---|---|
| `status` | `active` |
| `reviewed_at` | 落地当日 |
| `owner` | `desktop client team` |
| `applies_to` | architecture：`["软件架构", "语言无关"]`；algorithms：`["数据结构与算法", "C#"]`（PDF 是 C# 版，代码示例为 C#） |
| `enforcement` | 逐条判，预期以 `review` 为主——架构与算法判断几乎都需人工评估意图；`ci` 仅用于真能被工具判定的（如「禁止在项目引用中形成循环」编译器可判）；`advisory` 用于选型对比表 |
| `source` | `algorithms` 的 rule 指向 `reference/hello-algo-*.md#<标题>` 或 `https://www.hello-algo.com/`；`architecture` 的 rule 指向 `reference/architecture-styles-comparison.md#<标题>` |

## 六、版本影响

| 项 | 变化 | 级别 |
|---|---|---|
| `knowledge-base` | 5.0.0 → **6.0.0** | **Major**——五条 csharp 条目的 `summary` 与正文范围收窄属不兼容语义变化（按 `id` 检索的消费者拿到的内容变了）。新增领域本身是 Minor，但取最高级别。**阶段 A 单独提交时为 5.1.0（Minor，纯新增）**，Major 由 B 阶段的迁移触发 |
| `catalog.json` | 追加 `architecture` 与 `algorithms` 两条领域记录 | 随上 |
| `knowledge-base-maintain` | 预期无需升版（无脚本改动）。若提取过程暴露 `check_index.py` 缺口则另计 | — |
| `.claude-plugin/marketplace.json` | **不升级**——本次不涉及 `plugins/` | — |

## 七、验收标准

1. `check_index.py`（全库，不传 domain）→ `OK`，记录数由 345 增至约 445（阶段 A 实测已到 409）
2. `check_index.py --audit` → 两个新领域的 `enforcement` 填写率 100%，覆盖率有数值（不强求高，按「覆盖率不追求 100%」判据）
3. `check_refs.py --strict` → `OK`，且扫描文件数由 101 增至约 132（阶段 A 实测已到 113；新增 31 篇正文进入扫描范围：architecture 10+2、algorithms 4+15；`00-README.md` 在领域根目录，不在扫描范围内）
4. `python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts` → 133 全绿（无脚本改动则应无变化）
5. `find_duplicates.py --top 20` → 新领域条目与 `csharp.01`/`csharp.03`/`csharp.07`/`csharp.08` **不出现 ≥0.6 的高分候选**；若出现须逐对判定并处置（这是本次最关键的验收项——迁移的目的就是消除重复，若做完还有高分重复说明迁移没到位）。**阶段 A 落地后的基线（B 阶段的消除目标）**：0.917 `02.composition-over-inheritance`、0.691 `03.aggregate`、0.613 `02.solid-checkpoints`、0.556 `01.dependency-direction`、0.537 `09.composition-root-uniqueness`、0.511 `01.layering-model-choice`
6. `reference/hello-algo-*.md` 抽样验证：随机 3 篇，确认代码块无 `^/`/`^^=` 残留、表格未错行、图解指针位置与原书对应

## 八、风险与未决项

| 风险 | 处置 |
|---|---|
| **hello-algo 许可证的 SA 条款** | 已确认为 CC BY-NC-SA 4.0，方案已定为**逐字提取 + 目录级许可证隔离**（`algorithms/reference/LICENSE` + 每篇署名声明 + `00-README.md` 说明该目录授权独立）。执行时须确认：署名信息完整（BY 强制）、`reference/LICENSE` 不被 `check_index.py` 报为孤儿文件（非 Markdown，预期不在扫描范围，需实测确认） |
| 迁移后 `csharp` 条目变「空壳引用」 | 每条保留至少一项 C# 特有增量；若某条摘除通用部分后无任何 C# 特有内容，则该条应走 Step 4.5 **废弃**流程（`status: deprecated` + `summary` 指向 architecture），而非留一条只有引用的空条目 |
| PDF 提取质量不达标 | 抽样验证不通过则不提交该篇，先修字符修复表；宁可少几篇也不入库损坏内容 |
| 15 篇 reference 使 `check_refs.py` 扫描范围与耗时上升 | 预期可接受（当前 101 文件耗时 <1s）；若显著变慢则在 plan 阶段记录，不阻断 |
| 工作量超出单次会话 | 已在 plan 中切为 4 个可独立提交的阶段，每阶段自带验收 |

## 九、明确不做

- **不把 PDF 二进制或导出图片入库**——已决定图解走指针
- **不提取第 0 章（前言）与第 16 章（附录）**——无判断依据价值
- **不做 architecture-review / algorithm-review skill**——本次只建知识库，消费者 skill 是后续独立决策
- **不动 `csharp.07`/`csharp.08` 的性能与并发条目**——与 algorithms 是合理分层，不是重复
- **不处理上轮遗留的 19 对 ≥0.4 查重候选**——用户已明确「剩余暂不加入」
