# dotnet-debugging 知识库（三期）：WPF 桌面 dump 归因设计

**日期**：2026-09-05
**领域**：`knowledge-base/dotnet-debugging/`
**目标版本**：1.1.0 → 1.2.0
**一期 spec**：`docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md`
**二期 spec**：`docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-phase2-design.md`

## 目录

- [1. 背景与定位调整](#1-背景与定位调整)
- [2. 范围](#2-范围)
- [3. 篇目结构与接口契约](#3-篇目结构与接口契约)
- [4. 判据范式：沿用一期布尔判据](#4-判据范式沿用一期布尔判据)
- [5. 与 wpf 领域的边界](#5-与-wpf-领域的边界)
- [6. applies_to 约定](#6-applies_to-约定)
- [7. 事实核验与待核验清单](#7-事实核验与待核验清单)
- [8. 完成判定](#8-完成判定)
- [9. 不在本期范围](#9-不在本期范围)

---

## 1. 背景与定位调整

### 1.1 三期的来源

一期 spec 的分期路标登记三期为「WPF 桌面 dump 归因」，范围为 Dispatcher 死锁与四类 WPF 泄漏，并给出收窄依据：这两个主题**dump 快照可答**，而 UI 卡顿归因需要时间线数据，已随二期活体诊断交付。

一期同时声明「后续期次在本 spec 只登记路标与范围，不写实现细节——各期到时各自走一遍 brainstorming」。本 spec 即该 brainstorming 的产物。

与二期不同，三期**不回填任何欠条**——一期正文中没有对 WPF 归因的未兑现承诺，本期是纯增量扩展。

### 1.2 定位调整：从「三运行时共性层」到「共性层 + WPF 分支」

一期 README 将本领域定位为「覆盖 .NET Framework 4.x、.NET 6/8+ 与 Linux 容器三种运行时」的共性层。三期引入 WPF 专属内容，该定位需要显式调整。

考虑过的两个方案：

| 方案 | 做法 | 否决/采纳理由 |
|---|---|---|
| **A（采纳）** | 三期正文与索引标注 `applies_to` 含 `Windows`，领域 README 定位段补一句「以三运行时共性层为主干，WPF 专属归因作为独立分支收录」 | 改动小；WPF 是本仓库核心技术栈（`knowledge-base/wpf/` 已至 7.2.1、17 篇规则），专属分支有实际需求 |
| B | 另起 `knowledge-base/wpf-debugging/` 独立领域 | 定位纯净，但四类泄漏的取证命令全在 dotnet-debugging，拆开等于把一条推理链切成两半，且会产生大量跨领域引用 |

采纳 A。二期已经打破过一次「三运行时通吃」——EventPipe 不支持 .NET Framework 4.x，本期是同一类边界收窄，用同一种手段（`applies_to` 标注 + 文件头声明）处理。

### 1.3 为什么是 Minor

本期定为 **1.2.0**。纯新增两篇 reference 与约 10 条索引，无删除、无重命名，一期与二期的全部条目 id / anchor / 文件路径原样保留。符合仓库版本规则中 Minor 的「新增」语义。

本期不改动 `plugins/` 与 `.claude/`，因此**不升 `.claude-plugin/marketplace.json`**。

---

## 2. 范围

### 2.1 本期收录

两篇 reference：

| 文件 | 责任 | 对应一期决策树征象 |
|---|---|---|
| `reference/wpf-dispatcher-deadlock.md` | UI 线程卡死的取证：UI 线程在等什么、谁持有它要的锁、队列积压与真死锁的区分 | § 1. 进程挂起 / 无响应 |
| `reference/wpf-leak-patterns.md` | 四类 WPF 泄漏在托管堆里的形态图鉴：先认对象、再认根链 | § 2. 内存持续增长 |

**本期不新增任何命令。** 全部复用一期已交付的 SOS 命令（`!threads` / `!clrstack` / `!dumpstack` / `!dso` / `!syncblk` / `!dumpheap` / `!gcroot` / `!objsize`）。三期的增量是**WPF 特有的读法**：同一条 `!gcroot` 输出，通用读法给出一条类型链，WPF 读法能指出这条链意味着「XAML 里某个绑定没解开」。

这也是收录判据（单命令粒度进知识库）在本期的体现方式——本期条目不是「命令条目」而是「征象归因条目」，与一期 `debugging-decision-tree.md` 同类。

### 2.2 明确不含

| 排除项 | 理由 |
|---|---|
| UI 卡顿归因（掉帧时间线、渲染线程 vs UI 线程耗时占比） | 本质需要时间线采样，已随二期活体诊断交付；dump 只是一个时刻 |
| WPF 预防性编码规范 | 属 `knowledge-base/wpf/` 职责，见第 5 节 |
| `dotnet-gcdump` 的托管引用图 | 一期 spec 已标注「移出、留待后续期次」，纳入会把三期扩大到工具链层面 |
| WinForms / WinUI / MAUI 的同类归因 | 本仓库技术栈为 WPF，其余 UI 框架无实际需求 |
| Visual Studio 内存分析器 / JetBrains dotMemory | GUI 工具，操作流程依赖线性阅读顺序，拆成索引条目会破坏可读性（与仓库对 PerfView 的既定判断一致） |

---

## 3. 篇目结构与接口契约

两篇 reference，沿用一期目录结构平铺在 `reference/` 下。**小节标题为篇目间的接口契约，实施时必须逐字一致**——索引 `anchor` 按 `anchor in heading` 子串匹配。

### 3.1 `wpf-dispatcher-deadlock.md`（UI 线程卡死归因）

| 小节标题（逐字） | 内容要点 | 复用的一期命令 |
|---|---|---|
| `## 1. 从 !threads 认出 UI 线程` | UI 线程不是「0 号线程」——它是创建了 `Dispatcher` 的那个线程。识别依据：栈底有 `Dispatcher.Run` / `Dispatcher.PushFrame`，Apartment 为 STA。多 UI 线程场景（每个线程各有独立 `Dispatcher`）的识别方式 | `!threads`、`!clrstack` |
| `## 2. UI 线程栈的三类等待形态` | 等锁（栈顶 `Monitor.Enter` / `ReliableEnter`）、等异步结果（`Task.Wait` / `.Result` / `WaitHandle.WaitOne`）、等 COM 编组（`CoWaitForMultipleHandles`）。三者下一步动作完全不同 | `!clrstack`、`!dumpstack` |
| `## 3. Dispatcher 队列积压 vs 真死锁` | **本篇核心区分点**：UI 线程在跑长任务（栈上看得到业务帧、队列积压）vs UI 线程被阻塞（栈顶是等待原语）。两者都表现为「界面无响应」，处置方向相反 | `!clrstack`、`!dso` |
| `## 4. 定位持锁方与互等闭环` | `!syncblk` 找到 owner 线程 ID → 回 `!threads` 映射到托管线程 → `!clrstack` 看它在干什么。给出 UI 线程与后台线程互等的完整闭环读法 | `!syncblk`、`!threads`、`!clrstack` |

**接口产出**：§ 3 的判据被 `debugging-decision-tree.md § 1. 进程挂起 / 无响应` 以 ` § ` 引用（见 3.3）。

### 3.2 `wpf-leak-patterns.md`（四类泄漏形态图鉴）

| 小节标题（逐字） | 内容要点 |
|---|---|
| `## 1. WPF 泄漏的共同取证起点` | `!dumpheap -stat` 该盯哪些类型名（`Window` / `UserControl` / `BindingExpression` / `DispatcherTimer` / 委托类型等）。**判定「该被回收却还在」的前提是知道预期实例数**——已关闭的 Window 应为 0，这个前提不成立时整条推理链失效 |
| `## 2. Binding 泄漏` | 绑定源未实现 `INotifyPropertyChanged` 时 WPF 退化为 `PropertyDescriptor` 订阅，静态表持有源对象 |
| `## 3. 可视化树泄漏` | 元素已从树上移除但仍被静态资源 / 逻辑父级 / 未退订的事件持有 |
| `## 4. 弱事件泄漏` | **反直觉点**：用了 `WeakEventManager` 不等于不泄漏——弱的是监听者一侧，管理器内部表的清理是摊销式的 |
| `## 5. DispatcherTimer 泄漏` | `Dispatcher` 强引用 timer、timer 强引用 `Tick` 处理器 → 整条对象图被应用级生命周期的 `Dispatcher` 钉住 |
| `## 6. 根链形态图鉴速查表` | 四类泄漏的 `!gcroot` 输出特征链一览，含「看到这个内部类型 = 哪类泄漏」的反查列 |

§ 2–5 每节固定三段结构：

```
### 堆上的可见特征     ← !dumpheap 看什么，实例数说明什么
### 根链形态           ← !gcroot 输出长什么样，哪个内部类型是标志物
### 判据与下一步       ← 能证实/排除什么，接下来查哪
```

该三段结构是本篇特有的——一期命令篇用四段（用途/开关/输出语义/判据），但本期条目不是命令条目，没有「语法与关键开关」可写。三段与一期决策树的三段（候选根因/取证命令与判据/常见误判）同源。

**§ 6 单独成节的理由**：四类泄漏的排查入口是双向的。已知泄漏类型时读 § 2–5；只拿到一条 `!gcroot` 输出、不知道属于哪类时，需要按内部类型名反查——这是排查现场更常见的方向，散落在四节里无法检索。

### 3.3 对一期决策树的两处增补

本期在 `debugging-decision-tree.md` 增补交叉引用，**不改结论、不删原文**（与二期回填的处理方式一致）：

| 位置 | 增补内容 |
|---|---|
| `§ 1. 进程挂起 / 无响应` | 候选根因表补一行「WPF UI 线程阻塞」，指向 `reference/wpf-dispatcher-deadlock.md § 3. Dispatcher 队列积压 vs 真死锁` |
| `§ 2. 内存持续增长` | 取证命令段补一句：目标为 WPF 应用时，`!dumpheap -stat` 之后转 `reference/wpf-leak-patterns.md § 1. WPF 泄漏的共同取证起点` 按 WPF 类型名筛查 |

两处均标注适用条件为 WPF 应用，非 WPF 读者读到即可跳过。这两处增补**不新增索引条目**，只改正文——`symptom-hang` 与 `symptom-memory-growth` 两条既有索引的 `summary` 相应微调，`id` / `anchor` / `file` 不动。

### 3.4 实施顺序

```
篇目 1（Dispatcher 死锁）──┐
篇目 2（泄漏形态图鉴）─────┴─→ 决策树增补 ─→ 版本与元数据收尾
```

两篇之间**无依赖**（不像一期术语篇被后续引用、二期机制篇被后续引用），可任意顺序甚至并行。决策树增补须待两篇落地（要指向其 anchor）。

---

## 4. 判据范式：沿用一期布尔判据

### 4.1 不用二期三元组

二期为时间序列数据引入了「基线形态 / 异常形态 / 区分点」三元组，并在其 spec § 4.2 写明例外：判据对象不是时间序列时用简单 `### 判据`，判断标准是「这条判据需要『和之前比』才能下结论吗」。

三期判据对象是 **dump 单时点快照**，不需要和之前比：

> 堆上存在 N 个 `BindingExpression`，且 `!gcroot` 显示其根链指向已关闭的 Window → 绑定未解除。

这是可直接判定的布尔事实。硬套三元组会写出空洞的「基线形态」。因此三期一律用一期的简单 `### 判据`。

### 4.2 判据的写法要求

沿用一期约定：每条判据须写明**能证实什么**与**能排除什么**。只写证实方向的判据在排查中价值减半——排除同样推进定位。

例：

> `!dumpheap -stat -type DispatcherTimer` 计数为 0 → **排除** DispatcherTimer 泄漏，转查 § 4 弱事件。
> 计数大于预期活动定时器数 → **证实**存在未 `Stop()` 的定时器，转 `!gcroot` 确认其 `Tick` 处理器持有的对象图。

### 4.3 不写绝对阈值

沿用二期 § 4.4 的约定。「堆上有超过 100 个 Window 实例即异常」这类阈值不写——预期实例数由应用自身决定（单窗口应用与 MDI 应用完全不同）。判据表述为「超出该应用预期的活动实例数」这一相对形态。

---

## 5. 与 wpf 领域的边界

### 5.1 切线：写代码时 vs 读现场时

一期 README 边界表已声明本领域与 `knowledge-base/wpf/` 的切线为「兜住 vs 验尸」。三期**沿用不新造**，但需要具体到条目级别——因为本期主题与 wpf 领域现有条目高度相邻。

已核查的 wpf 领域相邻条目：

| wpf 条目 | 它负责（预防） | 三期负责（验尸） |
|---|---|---|
| `wpf.09.no-sync-wait-deadlock`（`rules/09-threading.md § 5. 死锁防护`） | UI 线程禁止同步等待异步任务 | 已经死锁了，从栈上认出这就是同步等待 |
| `wpf.09.dispatcher-usage`（`§ 2. Dispatcher 使用规范`） | 异步调度用 `InvokeAsync`，禁止同步 `Invoke` | dump 里 `Dispatcher` 队列的状态怎么读 |
| `wpf.09.timer-scheduling`（`§ 7. 定时器与调度`） | UI 周期任务须用 `DispatcherTimer` | `DispatcherTimer` 没 `Stop()` 时在堆里的形态 |
| `wpf.10.memory-leak`（`rules/10-performance.md § 7. 内存与泄漏`） | 事件订阅须配对取消，禁止静态字段持有 Window | 已经泄漏了，从根链认出是哪种持有方式 |
| `wpf.03.event-subscription`（`rules/03-mvvm.md § 7. 事件与订阅`） | 跨 ViewModel 通信须配对取消订阅 | 未退订的事件在 `!gcroot` 输出里的标志物 |

**这五条是本期查重时的重点比对对象。** `find_duplicates.py` 若报三期条目与其中任一相似度 ≥ 0.5，说明判据被写成了预防规范的复述，须改写为「从 dump 里认出它」的视角。

### 5.2 引用方向

单向：三期正文可以 ` § ` 引用 wpf 领域条目（作为「这条泄漏对应的预防规范在哪」的出口），wpf 侧**不反向声明**。这与一期 README「引用单向」的既定约定一致。

跨领域引用一律写在正文，形式 `knowledge-base/wpf/rules/NN-x.md § 章节`——写进索引 `source` 字段会被 `check_index.py` 的路径越界检查拦截。

---

## 6. applies_to 约定

WPF 不跨平台，本期全部条目取值统一：

```json
"applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"]
```

三点说明：

1. **不含 `Linux`**——这是与一期条目最大的差异。一期多数条目为 `[".NET Framework 4.x", ".NET 6+", "Linux"]` 或三者全含
2. **含 `.NET Framework 4.x`**——与二期相反。二期不含 Framework 是因为 EventPipe 是 .NET Core+ 特性；三期复用的是 SOS 命令，Framework 完全适用，且 WPF 在 Framework 4.x 上仍有大量存量应用
3. `applies_to` 平台标注是本领域已知易错点（一期因此单独提交过修正 commit `c8603f8`，二期 spec § 7.2 亦重申），实施时须逐条核对

该边界同时写入两篇的**文件头**，而非仅体现在索引字段——读者按征象查表时须第一时间知道是否适用（沿用二期 § 7.3 的做法）。

---

## 7. 事实核验与待核验清单

### 7.1 本期的核验困难

二期在设计阶段先行核验了官方文档，实施时直接引用。三期做不到同等程度，原因是**WPF 内部持有链的具体形态官方从未文档化**：

- 微软官方文档讲的是「怎么避免泄漏」（预防），不讲「泄漏后 `!gcroot` 输出长什么样」
- 本机无真实 WPF 泄漏 dump 可供实测验证
- 网络教程多数只说到「用 `!gcroot` 找持有者」就停了，不给内部类型链的解读

这正是三期的价值所在——外部资料最缺的就是这一层。但也意味着事实定性必须格外谨慎。

### 7.2 事实分级与标注规则

本期内容按可核验性分三级，标注方式不同：

| 级别 | 判定 | 标注方式 |
|---|---|---|
| **一级：源码/文档可核实** | 类型名、字段名、公开 API 行为可从 `dotnet/wpf` 源码或官方文档直接查到 | 照实写，正文注明出处 |
| **二级：机制可推导** | 从一级事实与 CLR/GC 语义可逻辑推导（如「`Dispatcher` 强引用 timer ⇒ timer 的对象图被应用生命周期钉住」） | 照实写，写明推导依据 |
| **三级：经验性** | 典型输出排版、常见现场形态、实践中的高频顺序 | **显式标注为经验性知识**，沿用一期对《Advanced .NET Debugging》类内容的处理方式 |

**硬约束：三级内容不得冒充一级。** 具体的内部字段名若查不到源码佐证，宁可写「根链上会出现 WPF 内部类型」的模糊表述，也不编造一个看似精确的字段名——错误的精确比正确的模糊危害大得多，读者会拿着不存在的类型名去 grep 输出。

### 7.3 待核验清单（实施时逐条查证）

以下事实本次设计阶段**未核验**，实施对应小节前须查 `dotnet/wpf` 源码或官方文档。查不到的按 7.2 降级标注。

| # | 待核验事实 | 用于 | 查证来源 |
|---|---|---|---|
| 1 | 绑定源未实现 `INotifyPropertyChanged` 时，WPF 走 `PropertyDescriptor` 订阅路径上实际出现在根链里的类型名 | `wpf-leak-patterns.md § 2` | `dotnet/wpf` 中 `PropertyPathWorker` / `DependencySource` 相关实现；官方 data binding 文档 |
| 2 | `WeakEventManager` 内部表的类型名与清理时机（是否为摊销式、何时触发） | `§ 4` | `dotnet/wpf` 中 `WeakEventManager` / `WeakEventTable` 实现 |
| 3 | `DispatcherTimer` 到 `Dispatcher` 的实际引用字段与方向 | `§ 5` | `dotnet/wpf` 中 `DispatcherTimer` 实现 |
| 4 | `Dispatcher` 自身的生命周期锚点（静态表持有 / 线程关联方式） | `§ 5`、`wpf-dispatcher-deadlock.md § 1` | `dotnet/wpf` 中 `Dispatcher` 实现 |
| 5 | UI 线程栈底出现的实际方法名（`Dispatcher.Run` / `PushFrame` / `PushFrameImpl` 的调用层次） | `wpf-dispatcher-deadlock.md § 1` | `dotnet/wpf` 源码；一期 `!clrstack` 篇的输出格式 |
| 6 | `!syncblk` 输出的 owner 线程 ID 与 `!threads` 的哪一列对应 | `wpf-dispatcher-deadlock.md § 4` | **一期正文已有**（`sos-locks-and-async.md § 1`、`sos-threads-and-stacks.md § 1`），实施时读一期正文核对而非重新查证 |

第 6 条特别说明：它是一期已交付内容，三期只是复用。**不重新查证，直接读一期正文对齐**——若发现一期写错，属一期缺陷，单独修正并升 patch 版本，不混进三期。

### 7.4 实测替代方案（可选）

若实施期间需要验证某条形态，最低成本的做法是构造最小复现：写一个 20 行的 WPF 应用制造对应泄漏，用一期 `dump-capture.md § 2. dotnet-dump collect` 抓 dump，再按本期写法读一遍。

**这不是本期的必要步骤**——列在此处是因为它是解决三级事实的唯一硬手段。是否执行取决于实施时的成本判断；不执行则相应内容保持三级标注。

---

## 8. 完成判定

三期完成需同时满足：

- [ ] `check_index.py`（全局）PASS。记录数 = 566 + 本期新增条目数（写实施计划时按逐篇条目清单定死，验收时按该数字核对，不接受「约」）
- [ ] `check_index.py dotnet-debugging --audit` 无孤儿文件，`rule` 仍为 5 条（本期不新增 rule），`reference` = 59 + 本期新增
- [ ] `check_refs.py` PASS
- [ ] `find_duplicates.py` 中本期条目与 § 5.1 所列五条 wpf 条目相似度低于 0.5；若超过，说明判据写成了预防规范的复述，须改写为验尸视角
- [ ] 全部本期条目 `applies_to` 为 `[".NET Framework 4.x", ".NET 6+", "Windows"]`，**不含 `Linux`**
- [ ] 两篇文件头均含 WPF 专属 + Windows 限定的声明
- [ ] 领域 README：定位段已补 WPF 分支说明（见 1.2）；文件地图 13 → **15 行**；阅读路径表补两行；版本行 `1.2.0` 与 CHANGELOG 最新条目一致
- [ ] `debugging-decision-tree.md` 两处增补完成，且**未删除任何原有内容**
- [ ] `catalog.json` 的 `dotnet-debugging` 条目 `notes` 已更新（现文末句为「暂不含 PerfView/ETW 与 WPF 专属归因」，本期须修订该表述）
- [ ] 一期 spec 分期路标表的三期行标注为已交付
- [ ] 待核验清单（7.3）六条全部处理：查到的写实并注明出处，查不到的按 7.2 降级标注为经验性
- [ ] 全部改动已推送 master

---

## 9. 不在本期范围

以下已识别但明确不做，登记以免后续误认为遗漏：

| 项 | 归属 |
|---|---|
| PerfView 与 ETW 会话管理 | 后续期次；.NET Framework 4.x 的活体诊断依赖此项 |
| `dotnet-gcdump` 与托管引用图 | 后续期次（一期已标注移出） |
| Linux 容器专属调试（缺符号降级、PID namespace、容器内存限制与 GC 交互、SIGSEGV） | 一期 spec 登记的四期（可选） |
| `AssemblyLoadContext` 与可收集程序集卸载 | 一期已登记的已知缺口 |
| `docs/sysinternals/` 中 4 篇 .NET 相关文档的改造入库 | 未排期。二期已评估：改造为四段结构属重写而非平移 |
| WinForms / WinUI / MAUI 归因 | 无需求，本仓库技术栈为 WPF |
| 消费本领域的诊断编排 skill | 未排期。`catalog.json` 的 `consumers` 目前为空，三期后仍为空 |
| UI 卡顿归因 | 已随二期活体诊断交付（一期 spec 的期次收窄依据） |
