# dotnet-debugging 知识库（二期）：活体监控工具链设计

**日期**：2026-09-05
**领域**：`knowledge-base/dotnet-debugging/`
**目标版本**：1.0.1 → 1.1.0
**一期 spec**：`docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md`

## 目录

- [1. 背景与期次顺序变更](#1-背景与期次顺序变更)
- [2. 范围](#2-范围)
- [3. 篇目结构与接口契约](#3-篇目结构与接口契约)
- [4. 判据范式：时间线三元组](#4-判据范式时间线三元组)
- [5. 版本分叉：两套计数器命名](#5-版本分叉两套计数器命名)
- [6. 回填一期三处欠条](#6-回填一期三处欠条)
- [7. 能力边界与 applies_to 约定](#7-能力边界与-applies_to-约定)
- [8. 事实核验记录](#8-事实核验记录)
- [9. 完成判定](#9-完成判定)
- [10. 不在本期范围](#10-不在本期范围)

---

## 1. 背景与期次顺序变更

### 1.1 一期留下的欠条

一期（1.0.0，8 篇 reference + 1 篇 rules，42 条索引）交付了 dump 与 SOS 这条**单时点取证**轴线。但在三处正文明确写下了未兑现的承诺：

| 位置 | 原文承诺 |
|---|---|
| `reference/debugging-decision-tree.md § 5. 间歇性抖动` | 「完整的时间线采样方案……留待后续期次收录」，且「候选根因」段写的是「不适用」 |
| `reference/dump-types-and-capability.md § 3. dump 是单时点快照` | 「一期知识库不含专门的时间线采样工具链……完整的时间线分析方法留待二期路标」 |
| `reference/dump-capture.md § 1. procdump` 判据段 | 「在没有时间线采样工具时的替代手段」 |

其中第一处最严重：决策树的六类征象里，唯独「间歇性抖动」给出的是**否定结论**——告诉读者这个问题当前答不了。这是一期唯一对读者承诺了却没兑现的分支。

### 1.2 期次顺序的变更及其理由

一期 spec 的分期路标把二期定为 **WPF 桌面 dump 归因**，活体诊断排在三期（原文：「卡顿归因随活体诊断进三期，那里才有帧时间线数据」）。本期调换该顺序，理由：

- WPF 归因在一期正文里**没有任何未兑现承诺**——它是纯增量扩展，晚做不产生矛盾
- 活体监控对应三处已写下的欠条，晚做则文档持续自相矛盾
- 一期 spec 已声明「后续期次在本 spec 只登记路标与范围，不写实现细节——各期到时各自走一遍 brainstorming」，路标可调整

WPF 桌面 dump 归因顺延为三期，范围不变（Dispatcher 死锁 + 四类 WPF 泄漏，完全建立在一期已交付的 SOS 命令之上）。

### 1.3 为什么是 Minor 而非 Major

本期定为 **1.1.0**（Minor）。

`debugging-decision-tree.md § 5` 的结论确实从「dump 答不了，只能连抓碰运气」变为「用 dotnet-counters 采集」，但这不构成破坏性变更：

- **无删除、无重命名**。一期的全部条目 id、anchor、文件路径原样保留，既有引用不失效
- **旧路径仍然有效**。连抓 dump 的做法保留不删（见 6.3），.NET Framework 4.x 下它仍是唯一可用路径。读者原有的操作方式不会失效，只是多了一条更好的路径
- 按仓库版本规则，Major 保留给「删除或重命名用户可见功能、破坏性架构变更」。本期是**在既有结构上新增篇目并补全一个此前留白的分支**，符合 Minor 的「新增」语义

本期不改动 `plugins/` 与 `.claude/`，因此**不升 `.claude-plugin/marketplace.json`**。

---

## 2. 范围

### 2.1 本期收录

`dotnet-counters`、`dotnet-trace`，以及二者共同依赖的 EventPipe / 诊断端口机制。四篇 reference，约 20 条索引。

**收录判据沿用一期**：单命令粒度进知识库，多命令编排进 skill。据此，`dotnet-counters collect --counters <...> --format csv` 这条完整命令**收录**；而「先监控发现异常 → 决定采哪些 provider → 采集 → 转换格式 → 分析」这条编排**不收**。

### 2.2 明确不含

| 排除项 | 理由 |
|---|---|
| PerfView | GUI 工具、Windows 专属，其操作流程天然依赖线性阅读顺序，拆成索引条目会破坏可读性（与仓库对 `SUPERPOWERS_GUIDE.md` 一类文档的既定判断一致） |
| ETW 会话管理（`logman` / `wpr`） | Windows 内核级机制，与 EventPipe 是两套体系；.NET Framework 4.x 的活体诊断依赖它，随 PerfView 一并留后续期次 |
| `docs/sysinternals/` 的迁移 | 19 篇中仅 4 篇属 .NET 调试（handle、procdump、vmmap ×2），且改造为四段结构是重写而非平移（新写部分占成品 45–50%）。本期只在决策树加交叉引用 |
| OpenTelemetry / 应用内埋点 | 属 `knowledge-base/csharp/rules/11-observability.md § 7` 的职责，见 2.3 |

### 2.3 与既有领域的边界

一期 README 的边界表已声明「埋点 vs 采集」这条切线，本期**沿用不新造**：

| 已有资产 | 它负责 | 本期负责 |
|---|---|---|
| `csharp/rules/11-observability.md § 7. 指标与追踪` | 应用自己该埋什么指标（OpenTelemetry 统一管道、埋点生命周期治理） | 从外部读取运行时**已内置**的计数器，无需应用改代码 |

已核实：一期全部正文**零处**提及 EventPipe / 诊断端口 / dotnet-counters，本期为干净新建，无重复风险。

---

## 3. 篇目结构与接口契约

四篇 reference，沿用一期的目录结构（`reference/` 下平铺）。**小节标题为篇目间的接口契约，实施时必须逐字一致**——索引 `anchor` 按 `anchor in heading` 子串匹配，写错会在校验时暴露，但改起来要连带改所有引用方。

### 3.1 `eventpipe-and-diagnostic-port.md`（机制基础）

对应一期的 `clr-runtime-anatomy.md`：只讲机制不讲命令，是后续三篇的术语基础。

| 小节标题（逐字） | 内容要点 |
|---|---|
| `## 1. EventPipe 与 ETW 的关系` | EventPipe 为运行时内置、跨平台、进程内；ETW 为 Windows 内核级。二者数据源重叠但采集通道不同 |
| `## 2. 诊断端口与连接建立` | `DOTNET_DiagnosticPorts` 环境变量；listen / connect 两个方向；Linux/macOS 为 Unix domain socket、Windows 为命名管道、移动端为 IP:port；容器跨 PID namespace 时必须显式指定端口 |
| `## 3. Provider / Keyword / Level 三级过滤` | `KnownProviderName[:Flags[:Level[:KeyValueArgs]]]` 语法；CLR provider 的 keyword 字符串别名与 hex 值映射；Level 六档（`logalways`=0 至 `verbose`=5） |
| `## 4. EventCounter 与 Meter 两套计数器体系` | .NET 9 为分水岭；`System.Runtime` Meter 在 .NET 8 及更低版本不存在，工具自动 fallback 到旧 EventCounters；两套命名并存的后果 |
| `## 5. 采集开销与缓冲区` | `--buffersize` 默认 256 MB；**目标进程产生事件快于落盘时缓冲区溢出会静默丢事件**，不报错；采样率与开销的权衡 |
| `## 6. 基线采集：时间线判据的前置条件` | 无基线的时间线数据不可判读；基线应在何时采、采多久、与故障期采集的对齐方式 |

**接口产出**：篇目 2 与 3 的每条命令在「用途与前置条件」段统一指向 `§ 2`、`§ 4`、`§ 6`——与一期「所有 SOS 命令指向 `symbols-and-tool-matching.md`」同构。

`§ 6` 单独成节而非散落提醒，因为它是所有判据的共用前置条件，与 `§ 2`、`§ 4` 同级。

### 3.2 `dotnet-counters.md`（实时指标）

| 小节标题（逐字） | 结构 |
|---|---|
| `## 1. dotnet-counters monitor` | 一期四段结构 |
| `## 2. dotnet-counters collect` | 一期四段结构 |
| `## 3. 内置计数器与判据对照` | 双列对照表，见第 5 节 |

第 3 节是本篇价值核心，也是全领域唯一一处「一张表承载多条判据」的形态——因为计数器判据的差异只在指标本身，四段结构中的前三段（用途/开关/输出语义）对所有计数器完全相同，逐个展开会产生大量重复。

### 3.3 `dotnet-trace.md`（事件流采集）

| 小节标题（逐字） | 内容要点 |
|---|---|
| `## 1. dotnet-trace collect` | 一期四段结构；`--providers` / `--clrevents` / `--duration` / `--buffersize` / `--stopping-event-*` |
| `## 2. profile 选择` | 五个内置 profile；**必须写明 `cpu-sampling` 在 `collect` 下已被移除**，见 8.1 |
| `## 3. dotnet-trace report topN` | 无需外部工具即可读出栈上耗时最长的 N 个方法；`--inclusive` 与默认 exclusive 的语义差异 |
| `## 4. 格式转换与查看` | `--format` 三值（`NetTrace` 默认 / `Speedscope` / `Chromium`）；转换不可逆，原 `.nettrace` 必须保留 |

### 3.4 `live-monitoring-decision.md`（决策查表）

六节，与一期决策树的六类征象对应，但回答「该采什么」而非「该抓哪种 dump」：

| 小节标题（逐字） | 与一期的关系 |
|---|---|
| `## 1. 延迟尖峰` | **回填**一期 `debugging-decision-tree.md § 5. 间歇性抖动` 的空洞 |
| `## 2. 内存持续增长` | 与一期同名征象互补：活体定方向，SOS 定根因 |
| `## 3. CPU 打满` | 同上 |
| `## 4. 异常风暴` | 一期无对应节——异常速率是时间线特有的观测量 |
| `## 5. 线程池饥饿` | 一期在「进程挂起」下作为候选根因之一，本期独立成节（活体能看到注入速率，dump 看不到） |
| `## 6. 启动阶段问题` | **一期完全没有的能力**——`-- <command>` 与 `--diagnostic-port` 可在进程启动前建立采集，dump 做不到（进程尚未存在） |

每节沿用一期决策树的三段结构：`### 候选根因` / `### 采集方案与判据` / `### 常见误判`。

### 3.5 实施顺序

```
篇目 1（机制基础）
   ├─→ 篇目 2（dotnet-counters）  ┐
   └─→ 篇目 3（dotnet-trace）     ┴─→ 篇目 4（决策查表）─→ 回填一期三处
```

依据与一期一致：术语篇最先（其定义的诊断端口、Provider 模型被后续引用），决策篇倒数第二（要指向前三篇的全部 anchor，须待其落地），回填最后（要指向决策篇的新 anchor）。

---

## 4. 判据范式：时间线三元组

### 4.1 为什么不能沿用一期的布尔判据

一期判据是对单时点快照的布尔判定，例如「`Lock Count` 全为 0 → **排除** Monitor 死锁」。这种形态依赖一个前提：被观测量在快照时刻有确定值，且该值本身即可判定。

时间序列不满足该前提。「GC 堆大小 = 800 MB」这个事实无法判定任何东西——它可能是正常水位，可能是泄漏中途，也可能是回收前的峰值。**信息在趋势里，不在数值里。**

### 4.2 三元组结构

本期每条判据的小节标题固定为：

```
### 判据：基线形态 / 异常形态 / 区分点
```

| 段 | 回答什么 | 为什么不可省 |
|---|---|---|
| **基线形态** | 正常运行时该指标呈什么形态 | 无基线则任何数值都不可判读，这是与 dump 最大的操作差异 |
| **异常形态** | 出问题时形态如何变化（趋势，非阈值） | 趋势是时间线特有的信息 |
| **区分点** | 与相邻根因如何区分 | 「涨了 = 泄漏」不可操作，须说清「涨了但回落 = 压力大而非泄漏」 |

### 4.3 范例（GC 堆大小）

- **基线形态**：锯齿波动，每次 gen2 回收后回落到相近水位，包络线水平。
- **异常形态**：锯齿仍在，但每次回落的低点逐次抬高，包络线呈上升台阶。
- **区分点**：包络线上升 = 泄漏；包络线水平而振幅增大 = 分配压力增大，不是泄漏。**这两者在单时点 dump 中完全无法区分**——两次抓取都只能看到「堆里有 N 个对象」，无法得知 N 处于回落前还是回落后。

末句是本期的存在理由，每篇的判据段都应有对应表述：说清这条判据**为什么必须用时间线工具而非 dump**。

### 4.4 不写绝对阈值

本期判据一律**不给绝对数值阈值**（如「gen2 GC 超过 N 次/分钟即异常」）。理由：此类阈值强依赖业务场景与硬件规格，官方文档亦几乎不给绝对值，写死会误导。

例外：官方文档或运行时默认值本身给出的硬数字（如 `--buffersize` 默认 256 MB、`dotnet-sampled-thread-time` 约 100 Hz 采样率）属于事实而非阈值，照实写并标注出处。

### 4.5 判据必须接回一期命令

每条判据的「区分点」段落须给出下一步动作，指向一期的具体命令。这是二期与一期的咬合方式：

> **活体监控定位方向，SOS 定位根因。**

例：线程池队列持续 > 0 且线程数达上限 → 转 `reference/sos-locks-and-async.md § 3. !threadpool` 确认工作项内容。

---

## 5. 版本分叉：两套计数器命名

### 5.1 问题

`System.Runtime` 计数器在 .NET 9 前后是两套体系，名称完全不同（详见 8.2 的核验记录）。判据引用计数器名，而名称随运行时版本变化。

### 5.2 采用方案：双列对照表

`dotnet-counters.md § 3. 内置计数器与判据对照` 用一张表承载，两列分别给两套名称，判据文字只写一次：

| 指标 | .NET 9+ 名 | .NET 8- 名 | 基线形态 | 异常形态 → 指向 |
|---|---|---|---|---|
| GC 堆大小 | `dotnet.gc.last_collection.heap.size` | `GC Heap Size (MB)` | 锯齿波动，包络线水平 | 包络线呈上升台阶 → 泄漏，转 `sos-heap-and-objects.md § 4. !gcroot` |
| 线程池队列长度 | `dotnet.thread_pool.queue.length` | `ThreadPool Queue Length` | 接近 0，尖峰后迅速回落 | 持续 > 0 且线程数达上限、CPU 不高 → 饥饿，转 `sos-locks-and-async.md § 3. !threadpool` |
| 锁竞争次数 | `dotnet.monitor.lock_contentions` | `Monitor Lock Contention Count` | 低速率平稳 | 速率陡升伴随吞吐下降 → 锁竞争，转 `sos-locks-and-async.md § 1. !syncblk` |
| GC 暂停时间 | `dotnet.gc.pause.time` | `% Time in GC since last GC` | 短暂尖峰，占比低 | 占比持续偏高 → GC 压力，查分配速率与 GC 模式 |
| 异常速率 | `dotnet.exceptions`（**待核验**，见 8.4） | `Exception Count` | 接近 0 或稳定低速率 | 速率陡升 → 异常风暴，转 `sos-threads-and-stacks.md § 4. !pe` |

（上表为结构示范，实施时补齐全部纳入判据的计数器。标注「待核验」的名称未经官方样例确认，实施前须查证。）

### 5.3 被否决的方案

| 方案 | 否决理由 |
|---|---|
| 分节写两遍（`## 3a. .NET 9+` / `## 3b. .NET 8-`） | 判据文字重复两处，将来修订判据须改两处，违反单一真源 |
| 只写 .NET 9+ 新名 | .NET 6/8 仍是主流生产版本，忽略等于放弃相当比例的读者 |

双列表把随版本变化的部分隔离在两列内，不变的判据只写一次。该形态与一期 `!threads` 的「列 → 含义 → 异常信号」表同构，读者无需切换阅读模式。

---

## 6. 回填一期三处欠条

本期的硬约束：三处全部回填，否则新旧文档自相矛盾（新篇说「用 dotnet-counters 采集」，旧篇说「留待后续期次」）。

### 6.1 `debugging-decision-tree.md § 5. 间歇性抖动`（重写整节）

现状：`### 候选根因` 段写「不适用——本节不给出候选根因列表」，正文以「留待后续期次收录」结尾。

改法：

- `### 候选根因` 补齐实际列表（GC 暂停、线程池注入延迟、锁竞争、外部 I/O 抖动、JIT 首次编译）
- `### 取证命令与判据` 改为指向 `reference/live-monitoring-decision.md § 1. 延迟尖峰`
- **保留**「dump 是单时点快照、抓取时机可能不覆盖抖动窗口」的说明，但其角色从**终点结论**变为**转向时间线工具的理由**
- **保留**连抓多个 dump 的近似手段，并标注其适用条件：.NET Framework 4.x 下这仍是唯一可用路径（见第 7 节）

### 6.2 `dump-types-and-capability.md § 3. dump 是单时点快照`（改 1 段）

现状：「一期知识库不含专门的时间线采样工具链……完整的时间线分析方法留待二期路标。」

改法：改为指向新篇 `reference/dotnet-counters.md` 与 `reference/dotnet-trace.md`，并说明该能力仅覆盖 .NET 5+。

### 6.3 `dump-capture.md § 1. procdump` 判据段（加 1 句）

现状：`-n` 连抓多个 dump 被描述为「在没有时间线采样工具时的替代手段」。

改法：**保留该做法**（.NET Framework 4.x 与无法安装诊断工具的环境仍需要），补一句：目标为 .NET 5+ 且可安装诊断工具时，应优先用 `dotnet-counters collect` 采集时间线，连抓 dump 退化为受限环境下的备选。

**不可直接删除或标记为过时**——这是本节最易出错处。删除会让 .NET Framework 读者失去唯一可用路径。

### 6.4 回填的验收方式

全库检索 `留待后续期次`、`二期路标`、`一期不含` 一类措辞，回填后应**只剩 CHANGELOG 中 `AssemblyLoadContext` 一处**（一期已登记的已知缺口，不属本期范围）。

---

## 7. 能力边界与 applies_to 约定

### 7.1 运行时可用性

EventPipe 是 .NET Core+ 的运行时特性，**.NET Framework 4.x 完全不可用**。这是本期与一期最大的覆盖面差异——一期三运行时通吃，本期不含 Framework。

| 运行时 | 活体监控可用性 |
|---|---|
| .NET Framework 4.x | **不可用**。该运行时的活体诊断依赖 ETW / PerfView，随后续期次交付；当前仍只能走一期的 dump 路径 |
| .NET 5–8 | 可用；`System.Runtime` 计数器走 EventCounters 旧命名 |
| .NET 9+ | 可用；`System.Runtime` 计数器走 Meter 新命名 |
| .NET 10+ / Linux | 额外可用 `dotnet-trace collect-linux`（预览特性，需内核 6.4+、root 权限、glibc 2.27+） |

### 7.2 applies_to 取值约定

一期条目多以 `[".NET Framework 4.x", ".NET 6+"]` 打头，本期**绝大多数条目不含 .NET Framework**：

- `dotnet-counters` 相关条目：`[".NET 5+", "Windows", "Linux"]`（官方声明计数器可从 .NET 5 或更高版本的应用读取）
- `dotnet-trace collect` 相关条目：`[".NET 5+", "Windows", "Linux"]`
- `collect-linux` 相关条目：`[".NET 10+", "Linux"]`
- EventPipe 机制篇条目：`[".NET 5+", "Windows", "Linux"]`

**这条约定必须严格执行**——一期曾出现 `applies_to` 平台标注错误并单独提交修正（commit `c8603f8`），是已知的易错点。

### 7.3 该边界在正文中的落位

写入 `live-monitoring-decision.md` 的文件头，而非仅在索引字段中体现：读者按征象查表时，须第一时间知道自己的运行时是否适用，而不是读到命令处才发现用不了。

---

## 8. 事实核验记录

一期交付后出现 5 次事实修正提交（SOS 语义、运行时版本、Triage 产出途径、平台标注、引用格式）。本期在设计阶段先行核验官方文档，以下为已确认的事实，实施时直接采用，不再重新查证。

核验来源：`learn.microsoft.com/dotnet/core/diagnostics/dotnet-counters`、`learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace`（均于 2026-09-05 取得）。

### 8.1 `cpu-sampling` profile 在 `collect` 下已被移除

官方原文：「In past versions of the dotnet-trace tool, the collect verb supported a profile called `cpu-sampling`. **This profile was removed** because the name was misleading. It sampled all threads regardless of their CPU usage.」

- `dotnet-trace collect` 当前默认启用 `dotnet-common` + `dotnet-sampled-thread-time`
- 官方给出的近似等价写法：`--profile dotnet-sampled-thread-time,dotnet-common`
- 精确复刻旧行为：`--profile dotnet-sampled-thread-time --providers "Microsoft-Windows-DotNETRuntime:0x14C14FCCBD:4"`
- **同名陷阱**：`cpu-sampling` 在 `collect-linux` 子命令下**仍然存在**，但语义不同（基于 perf 的内核 CPU 采样，发射为 `Universal.Events/cpu`）。同名不同义，正文须显式区分

此条为当前网络教程与官方文档偏离最大处，`dotnet-trace.md § 2. profile 选择` 必须写明，否则读者照抄旧教程会直接报错。

### 8.2 计数器命名在 .NET 9 前后分叉

官方原文：「If the app uses .NET version 8 or lower, the `System.Runtime` Meter doesn't exist in those versions and `dotnet-counters` will **fall back** to display the older `System.Runtime` EventCounters instead.」

对照示例（取自官方文档的两段输出样例）：

| 含义 | .NET 9+（Meter） | .NET 8-（EventCounter） |
|---|---|---|
| GC 堆大小 | `dotnet.gc.last_collection.heap.size (By)` | `GC Heap Size (MB)` |
| 线程池队列 | `dotnet.thread_pool.queue.length ({work_item})` | `ThreadPool Queue Length` |
| 线程池线程数 | `dotnet.thread_pool.thread.count ({thread})` | `ThreadPool Thread Count` |
| 锁竞争 | `dotnet.monitor.lock_contentions ({contention})` | `Monitor Lock Contention Count` |
| GC 暂停 | `dotnet.gc.pause.time (s)` | `% Time in GC since last GC (%)` |
| 工作集 | `dotnet.process.memory.working_set (By)` | `Working Set (MB)` |

新命名的单位随名称一并显示（`(By)` 字节、`(s)` 秒），旧命名的单位内嵌在名称中（`(MB)`、`(%)`）——判据涉及单位换算时须注意。

### 8.3 其他已核验事实

| 事实 | 出处与影响 |
|---|---|
| `dotnet-counters` 读取计数器要求应用运行 **.NET 5 或更高**（非 .NET Core 3.0） | 决定 `applies_to` 取值 |
| `--buffersize` 默认 **256 MB**；溢出时事件被丢弃且不报错 | 写入 `eventpipe-and-diagnostic-port.md § 5`，属静默失败类风险 |
| `--format` 默认 `NetTrace`，可选 `Speedscope` / `Chromium`；**转换不可逆**，原 `.nettrace` 须保留 | 写入 `dotnet-trace.md § 4` |
| `dotnet-counters` / `dotnet-trace` 须与目标进程**同用户或 root** 运行 | 各命令的「用途与前置条件」段 |
| Linux/macOS 上 `-p` / `-n` 要求工具与目标进程共享同一 `TMPDIR`，否则命令超时 | 容器场景高频踩坑点 |
| 工具与目标进程**位数必须匹配**，否则报 `System.ComponentModel.Win32Exception (299)` | 与一期 `dump-types-and-capability.md § 2. 位数必须匹配` 呼应 |
| `collect-linux` 需 .NET 10+、内核 6.4+、root、glibc 2.27+，且为**预览特性** | 决定其 `applies_to` 与风险标注 |
| `dotnet-trace report topN` 默认按 **exclusive** 时间排序，`--inclusive` 切换 | 两者语义差异须写明，否则结论相反 |

### 8.4 需在实施时补充核验的项

以下事实本次未核验，实施对应小节前须查证官方文档：

- 各 `--profile` 展开后的完整 provider 与 keyword 组合（`dotnet-trace list-profiles` 的实际输出）
- `Microsoft.AspNetCore.Hosting` 等非运行时 provider 的计数器清单
- `dotnet.exceptions` 在 .NET 9+ 下的确切名称与单位（5.2 表中该行为推定，未经官方样例确认）

---

## 9. 完成判定

二期完成需同时满足：

- [ ] `check_index.py`（全局）PASS。记录数 = 544 + 本期新增条目数（写实施计划时按逐篇条目清单定死，验收时按该数字核对，不接受「约」）
- [ ] `check_index.py dotnet-debugging --audit` 无孤儿文件，`rule` 仍为 5 条（本期不新增 rule），`reference` = 37 + 本期新增
- [ ] `check_refs.py` PASS。**本期交叉引用密度高于一期**（每条判据均指回一期命令），是最易出错处
- [ ] `find_duplicates.py` 中本期条目与 `csharp.11.*`（可观测性）相似度低于 0.5；若超过，说明判据写成了埋点规范的复述，须改写
- [ ] 三处欠条全部回填；全库检索「留待后续期次」类措辞仅剩 CHANGELOG 中 `AssemblyLoadContext` 一处
- [ ] 全部本期条目的 `applies_to` 不含 `.NET Framework 4.x`（EventPipe 不支持该运行时）
- [ ] 领域 README 文件地图 **13 行**（一期 9 + 本期 4），版本行 `1.1.0` 与 CHANGELOG 最新条目一致
- [ ] `catalog.json` 的 `dotnet-debugging` 条目 `notes` 已更新（原文写有「一期不含活体监控工具（PerfView/ETW/dotnet-counters）」，本期须修订该表述）
- [ ] 一期 spec 的分期路标表已更新，反映期次顺序变更
- [ ] 全部改动已推送 master

---

## 10. 不在本期范围

以下已识别但明确不做，登记以免后续误认为遗漏：

| 项 | 归属 |
|---|---|
| WPF 桌面 dump 归因（Dispatcher 死锁、四类 WPF 泄漏） | 三期（原二期，本次顺延） |
| PerfView 与 ETW 会话管理 | 后续期次；.NET Framework 4.x 的活体诊断依赖此项 |
| `docs/sysinternals/` 中 4 篇 .NET 相关文档的改造入库（handle、procdump、vmmap ×2） | 未排期。已评估：改造为四段结构属重写（新写部分占成品 45–50%），docs 的价值是事实素材来源而非可平移成品 |
| `AssemblyLoadContext` 与可收集程序集卸载 | 一期已登记的已知缺口 |
| 消费本领域的诊断编排 skill | 未排期。`catalog.json` 的 `consumers` 目前为空 |
| 绝对数值阈值（如「gen2 GC 超过 N 次/分钟」） | 有意不做，理由见 4.4 |






