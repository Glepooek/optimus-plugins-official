# .NET 高级调试知识库设计（dotnet-debugging 领域）

> 日期：2026-09-05
> 状态：已定稿，待实现
> 范围：新建 `knowledge-base/dotnet-debugging/` 领域，一期交付共性层

## 背景与问题

仓库知识库已有 10 个领域，覆盖 C#、WPF、架构、设计模式等，但**「调试与诊断」是明确空白**。现有相关内容全部是**预防侧规范**：

- `csharp/rules/06-memory-resource.md`：IDisposable、事件泄漏、LOH、终结器
- `csharp/rules/11-observability.md`：日志与指标埋点
- `wpf/rules/12-exceptions-crash.md`：UI 线程异常、全局兜底、崩溃恢复

它们回答「怎么写才不出事」，**没有一处回答「已经出事了，怎么定位」**。当生产环境出现内存持续增长、UI 挂起、间歇崩溃时，团队缺少可检索的取证依据——每次都靠个人经验重新摸索。

本设计新建 `dotnet-debugging` 领域填补该空白。

## 目标与非目标

**目标**

- 建立「征象 → 根因假设 → 取证命令 → 输出解读 → 判据」的可检索知识
- 覆盖 .NET Framework 4.x、.NET 6/8+、Linux 容器三种运行时
- 索引粒度支持按命令名、按征象词精确检索单条，而非整篇加载
- 为未来的调试类 skill 提供稳定的引用锚点

**非目标**

- 不建 skill（一期）。知识库先落地并被实际查阅，暴露真实检索路径后再建
- 不收多命令编排的排查流程（属 skill 范畴，见「收录判据」）
- 不改动 `plugins/` 下任何文件，不升 `.claude-plugin/marketplace.json` 版本号

## 目录

- [1. 领域边界与命名](#1-领域边界与命名)
- [2. 一期文档清单](#2-一期文档清单)
- [3. 索引条目粒度](#3-索引条目粒度)
- [4. rules 层范围](#4-rules-层范围)
- [5. 分期路标与交付物](#5-分期路标与交付物)
- [6. 未来 skill 的接口契约](#6-未来-skill-的接口契约)
- [7. 实现约束与验证](#7-实现约束与验证)

---

## 1. 领域边界与命名

**域名**：`dotnet-debugging`
**id 前缀**：`dotnet-debugging.ref.<slug>`（reference）/ `dotnet-debugging.<NN>.<slug>`（rule）

`check_index.py` 的 `ID_RE = ^[a-z0-9-]+\.(?:\d{2}|ref)\.[a-z0-9-]+$` 允许域名含连字符（`data-structures-algorithms.ref.*` 已验证），无需修改校验器。

**领域职责一句话**：程序已经出问题之后，如何从运行中进程或 dump 里取证并定位根因。

### 与既有领域的四条边界

| 已有资产 | 它负责 | dotnet-debugging 负责 | 切线 |
|---|---|---|---|
| `csharp/rules/06-memory-resource.md` § 4 / § 6 / § 9 | 怎么写才不泄漏 | 已经泄漏了，如何在托管堆里认出它（`!gcroot` 追事件持有者、LOH 碎片形态、终结队列积压读法） | 写代码时 vs 读现场时 |
| `csharp/rules/11-observability.md` § 7 | 应用内部该埋什么指标 | 从外部读取运行中进程的计数器与事件流 | 埋点 vs 采集 |
| `wpf/rules/12-exceptions-crash.md` § 1–3 | 怎么捕获并优雅退出 | 崩溃 dump 里如何找到抛出点与第一现场 | 兜住 vs 验尸 |
| `dotnet` 领域 | 目标框架能跑在哪 | 目标框架决定用哪套工具链 | 能不能跑 vs 用什么诊断 |

**引用方向单向**：本领域正文可指向 `csharp`/`wpf`；被指向的领域不反向声明，与仓库根 README「引用单向」约定一致。

### 收录判据（写入领域 README）

> **单命令粒度进知识库，多命令编排进 skill。**
> 检验标准：这条内容能独立成为一个「查一下就照着用」的条目吗？能 → 知识库。它是否必须知道「上一步做了什么」才有意义？是 → skill。

据此，抓取 dump 的完整命令行（`procdump`、`dotnet-dump collect`、`createdump` 等）**进知识库**——它们单条可查。而「先判断征象 → 决定抓哪种 dump → 引导装工具 → 抓 → 分析 → 回报」这条编排属 skill。

**判据的适用范围说明**：`media` 领域的「不收命令模板」先例不适用于本领域。ffmpeg 命令是变换操作（改文件、参数组合无穷、随版本漂移）；调试命令的输出字段语义稳定（`!syncblk` 的列语义多年未变），本身就是可长期复用的知识。

---

## 2. 一期文档清单

### 设计依据：SOS 命令面本身就是共性层

`!dumpheap` `!gcroot` `!clrstack` `!syncblk` `!pe` `!finalizequeue` 在三种运行时下**同名同语义**——Framework 4.x 走 WinDbg + `.loadby sos clr`，.NET 6/8+ 走 `dotnet-dump analyze`（内置 SOS）或 `dotnet-sos install`，Linux 容器走同一个 `dotnet-dump analyze`。

三者真正分叉的只有三件事：**怎么拿到 dump、怎么加载 SOS、活体监控用什么**。因此一期能把最大的价值块（命令 + 输出字段语义）完整交付，后续期次只补分叉。

### 一期 8 篇 reference

| 文件 | 内容 | 在一期的理由 |
|---|---|---|
| `debugging-decision-tree.md` | 六类征象（进程挂起 / 内存持续增长 / CPU 打满 / 崩溃退出 / 间歇抖动 / 句柄耗尽）→ 候选根因假设 → 该用哪条命令取证。**查表结构，非步骤编排** | 领域入口，其余篇目都是它的落点 |
| `clr-runtime-anatomy.md` | 托管堆分代（gen0/1/2 + LOH + POH）、同步块表、终结队列、线程池内部结构、GC 模式（workstation/server × concurrent/background）、AssemblyLoadContext、句柄表 | 读懂任何命令输出的前提，且完全不随工具版本变化 |
| `dump-types-and-capability.md` | 四种 dump 类型（mini / heap-only / full / triage）各能答与不能答什么、位数匹配、快照时点性 | 选错 dump 类型是最贵的返工 |
| `dump-capture.md` | 三运行时 × 抓取工具的完整命令与开关语义：`procdump`、`dotnet-dump collect`、`createdump`、WER LocalDumps 注册表、`DOTNET_DbgEnableMiniDump`；含「崩溃时自动抓」与「挂起时手动抓」两类触发条件 | 见下「一期覆盖 dump 维度全部运行时差异」 |
| `sos-threads-and-stacks.md` | `!threads` `!clrstack` `!dumpstack` `!pe` `!dso`——逐列输出语义、托管/非托管栈交错读法 | 命令层，三运行时共用 |
| `sos-heap-and-objects.md` | `!dumpheap -stat` `!dumpobj` `!objsize` `!gcroot` `!eeheap` `!gchandles`——堆统计读法、`!gcroot` 根路径如何指向泄漏持有者 | 同上；对接 `csharp/06` 泄漏规则 |
| `sos-locks-and-async.md` | `!syncblk` `!dumpasync` `!threadpool`——死锁判定依据、async 状态机还原、线程池饥饿征象 | 同上；对接 `csharp/04` 异步规范 |
| `symbols-and-tool-matching.md` | 符号服务器、PDB 类型（portable / full）、SOS 与运行时版本匹配、缺符号时的降级读法 | 最高频踩坑点，且是其余全部命令的前置条件 |

`reference/` 下不加数字前缀，与 `media`、`mcp` 一致（数字前缀只用于 `rules/`）。

### 一期覆盖 dump 维度的全部运行时差异

抓 dump 是三运行时分叉最明显的一维（Framework 用 `procdump`/DebugDiag/WER，6/8+ 多了 `dotnet-dump collect`，Linux 容器是 `createdump` + PID namespace 约束）。命令进库意味着一期被动覆盖这部分差异。

**处置：把 dump 抓取的三运行时一次写完。** 该维度有界（工具可穷举），跨期拆一篇文档会留下「半篇待补」的脏状态。真正无界的分叉是活体监控（PerfView/ETW/`dotnet-trace`/lldb），留后续期次。

### 一期明确不含

活体监控工具（`dotnet-counters` / `dotnet-trace` / PerfView / ETW）不写正文，仅在 `debugging-decision-tree.md` 的「间歇抖动」分支留指向。理由：这三者是运行时分叉最厉害处（PerfView/ETW 为 Windows 专属，`dotnet-*` 只覆盖 5+，Linux 还有 lldb 变体），塞进一期会破坏共性层的完整性。

---

## 3. 索引条目粒度

### 跨领域引用不走 source 字段

`check_source_refs` 用 `domain_dir / rel` 解析路径，配合路径越界检查，写 `../csharp/rules/06-*.md` 会被拦截。全库现有 `source` 零条跨领域（7 个领域核查确认）。

`architecture` 领域给出既有解法：**跨领域引用写在正文里**，用 `knowledge-base/<domain>/rules/NN-x.md § 章节` 的完整形式（该领域有 10 处先例）。

因此：
- 第 1 节四条边界 → 落地为**正文交叉引用**
- 索引 `source` 字段 → **只用于领域内**（如某条 SOS 命令条目指向 `reference/clr-runtime-anatomy.md#托管堆分代`）

### reference 破例按小节登记

仓库根 README 允许该破例：「仅当一篇 reference 内部存在多个会被独立检索的主题时，才拆成多条」。本领域正属此情形，且这是领域可用性的关键。

按整篇登记会退化为 `dotnet-debugging.ref.sos-heap-and-objects` 一条，摘要写「堆相关 SOS 命令」——skill 遇到「内存涨了」检索到它只能整篇加载。按命令登记则是：

```
dotnet-debugging.ref.dumpheap-stat   tags: [heap, statistics, memory-growth, leak-triage]
dotnet-debugging.ref.gcroot          tags: [root-path, leak, event-handler, static-reference]
dotnet-debugging.ref.finalizequeue   tags: [finalizer, queue-backlog, dispose-missing]
dotnet-debugging.ref.syncblk         tags: [deadlock, monitor, lock-contention]
```

skill 按 `leak` + `event-handler` 直接命中一条，读一节。这是本领域与 `media`（整篇登记，因「编解码器」无法更细拆）的实质差别：**调试知识天然按命令/征象分片，而这正好是检索键。**

### 一期条目估算（42 条）

| 来源文件 | 条数 | 登记单位 |
|---|---|---|
| `debugging-decision-tree.md` | 6 | 每类征象一条（tags 用征象词：`hang` / `memory-growth` / `high-cpu` / `crash` 等） |
| `clr-runtime-anatomy.md` | 7 | 每个运行时结构一条 |
| `dump-types-and-capability.md` | 1 | 整篇（选型对比表，拆开失去对比语义） |
| `dump-capture.md` | 5 | 每个抓取工具一条 |
| `sos-threads-and-stacks.md` | 5 | 每命令一条 |
| `sos-heap-and-objects.md` | 6 | 每命令一条 |
| `sos-locks-and-async.md` | 3 | 每命令一条 |
| `symbols-and-tool-matching.md` | 4 | PDB 类型 / 符号服务器 / SOS 版本匹配 / 缺符号降级 |
| `rules/01-dump-handling.md` | 5 | 每条款一条 |

密度介于 `mcp`（14 条）与 `csharp`（143 条）之间，对 9 篇文档（8 reference + 1 rules）合理。估算为下限，实际登记时若某命令的开关组合值得独立检索可再拆，不设上限。

### 与既有惯例对齐的三条约定

1. **`tags` 全英文小写连字符**——全库 305 个 tag 零中文，严格遵守；正文用中文（与全库一致）
2. **`anchor` 用中文标题文本**——与全库一致，`check_index.py` 按 `anchor in heading` 子串匹配
3. **命令名 slug 去掉特殊字符**——`ID_RE` 不允许 `!` 与下划线，故 id 写 `dotnet-debugging.ref.dumpheap-stat`，感叹号只出现在 `title` 与正文中

### 治理字段填写要求

仓库根 README 规定：新增 `rule` 条目须一并填写 `enforcement`、`status`、`applies_to`、`reviewed_at`、`owner`——schema 层面可选，漏填不报错，但会让条目成为治理数据里的空洞。本领域 5 条 rule 全部填满：

- `owner`: `desktop client team`（与既有领域一致）
- `status`: `active`
- `reviewed_at`: 实际撰写日期（语义是「正文被人读过并确认成立」，不得批量刷）

**`applies_to` 在本领域对 reference 条目同样必填**——这是本领域相对其他领域的额外约定。原因：同一条 SOS 命令在不同运行时的可用性不同（`!dumpasync` 需要较新 SOS，`procdump` 仅 Windows，`createdump` 仅 .NET Core+/Linux）。检索者拿到一条命令却不知道自己的运行时能不能用，等于没拿到。取值示例：`[".NET Framework 4.x", ".NET 6+", "Windows"]`。


---

## 4. rules 层范围

### 发现：dump 的敏感数据风险存在真空

`csharp/rules/14-security.md § 8 日志与脱敏` 的约束对象是**日志**（禁止记录密码/Token/PII），而 full dump 是**整个进程内存的完整副本**——必然含明文密码、Token、密钥与全部用户 PII，且**任何脱敏中间件都拦不住它**。§ 8 推荐的解法（统一脱敏过滤器）在 dump 面前完全失效。

全库 10 个领域没有一条规则约束 dump 怎么存、怎么传、多久删。

### rules/01-dump-handling.md（一期唯一一篇）

| 条款 | level | enforcement |
|---|---|---|
| 生产 full dump 视同最高密级数据，禁止提交仓库、禁止发 IM/邮件附件 | MUST | `review` |
| `*.dmp` / `*.dump` 必须进 `.gitignore` | MUST | `ci` |
| 对外交付/工单场景应优先用 triage 或 heap-only，而非 full | SHOULD | `review` |
| 生产 dump 须有明确留存期限与销毁责任人 | MUST | `review` |
| 崩溃自动抓取（WER / `DOTNET_DbgEnableMiniDump`）在生产启用前须评估落盘位置的访问控制 | SHOULD | `review` |

第 2 条是第 1 条中可被工具无歧义判定的外壳部分，故独立成条并标 `ci`——与 `git.02.commit-hooks` 的「外壳可自动判定、实质需人工判断」处理方式一致。

### 为什么只有这一篇

调试知识里能成为 MUST/SHOULD 的极少。「内存涨了应该先看 `!dumpheap -stat`」不是规范而是判据，写成 rule 即是假规范。真正带强制性的只有 **dump 作为数据资产的处置**——它有明确的违反后果（泄密）与明确的正确做法。其余全部归 `reference/`。

### 与 csharp/14 的关系

本篇正文应指向 `knowledge-base/csharp/rules/14-security.md § 8. 日志与脱敏`，说明两者是**同一威胁的两个面**：§ 8 管日志脱敏，本篇管 dump 处置，脱敏手段对 dump 无效。

**不在 `csharp/14 § 8` 加反向指向**：仓库 README 明确「引用单向」，且改动他域正文会牵动 `csharp` 的版本号与 CHANGELOG。该缺口留待未来真有人从安全侧检索时再补。

领域分类因此定为 `["rules", "reference"]`，与 `mcp` 同形态。

---

## 5. 分期路标与交付物

### 一期交付物

```
knowledge-base/dotnet-debugging/
├── README.md                  # 版本 1.0.0，含第 1 节边界表 + 收录判据
├── CHANGELOG.md               # [1.0.0] 建域
├── index.jsonl                # 42 条（见第 3 节估算）
├── rules/
│   └── 01-dump-handling.md    # 5 条款
└── reference/
    ├── debugging-decision-tree.md
    ├── clr-runtime-anatomy.md
    ├── dump-types-and-capability.md
    ├── dump-capture.md
    ├── sos-threads-and-stacks.md
    ├── sos-heap-and-objects.md
    ├── sos-locks-and-async.md
    └── symbols-and-tool-matching.md
```

### 同期必须改动的既有文件

| 文件 | 改动 | 不改的后果 |
|---|---|---|
| `knowledge-base/catalog.json` | 登记新领域（`categories: ["rules","reference"]`、`consumers: []`） | `check_index.py` 双向一致性检查直接报错 |
| `knowledge-base/README.md` | 首段领域列表、「领域职责边界」长句加入 `dotnet-debugging` | 导航缺口，无校验拦截但属不完整交付 |

### 明确不改动

`.claude-plugin/marketplace.json` 版本号**不升**。仓库版本规则只约束 `.claude/` 与 `plugins/` 两条路径；`knowledge-base/` 走领域独立版本号（新建域 = `1.0.0`，与 `mcp` 一致）。本期无插件消费者，不改 `plugins/` 下任何文件。

### 后续期次路标

| 期次 | 主题 | 范围 |
|---|---|---|
| **二期** | WPF 桌面 dump 归因 | Dispatcher 死锁（UI 线程等在哪、谁持锁）、四类 WPF 泄漏在堆里的形态（Binding / 可视化树 / 弱事件 / `DispatcherTimer`）。对接 `wpf/12-exceptions-crash.md` |
| **三期** | 活体诊断与工具链分叉 | `dotnet-counters` / `dotnet-trace` / `dotnet-gcdump`；PerfView / ETW / WPR；**UI 卡顿时间线归因**；三运行时工具选择矩阵 |
| **四期（可选）** | Linux 容器专属 | 缺符号降级、PID namespace 约束、容器内存限制与 GC 交互、SIGSEGV 排查 |

**二期收窄依据**：WPF 诊断主题按「dump 快照能否回答」二分——

| 主题 | 快照可答 | 归期 |
|---|---|---|
| Dispatcher 死锁 | ✅ `!clrstack` + `!syncblk`（一期已交付） | 二期 |
| 四类 WPF 泄漏 | ✅ `!gcroot`（一期已交付） | 二期 |
| UI 卡顿归因（渲染线程 vs UI 线程、GC 暂停占比、掉帧时间线） | ❌ 本质需要时间线采样，dump 只是一个时刻 | 三期 |

二期因此完全建立在一期已交付的 SOS 命令之上，无外部依赖；卡顿归因随活体诊断进三期，那里才有帧时间线数据。

后续期次在本 spec 只登记路标与范围，不写实现细节——各期到时各自走一遍 brainstorming。

---

## 6. 未来 skill 的接口契约

本节定的是「知识库写成什么样，将来 skill 才用得上」。现在不定，将来 skill 会被迫复制正文。

### 契约一：skill 引用条目 ID，不复制正文

沿用 `csharp-code-review` 已验证的「固定映射」消费模式（仓库根 README 认可的两种方式之一）：skill 在自己的文档里写死 `reference/sos-heap-and-objects.md § !gcroot`，不把命令说明抄进 SKILL.md。

### 契约二：每条命令条目的四段固定结构

```
### !gcroot                    ← anchor（含命令名，便于检索）
1. 用途与前置条件              ← 什么情况下用、需要什么类型的 dump
2. 语法与关键开关
3. 输出逐列语义                ← skill 转述的主体
4. 判据：能证实 / 排除什么假设  ← skill 据此决定下一步走哪个分支
```

第 4 段是关键——它把「单命令知识」与「多命令编排」缝合：知识库给出每条命令的**出口条件**，skill 只负责按出口条件选下一条命令。编排逻辑留在 skill，判据留在知识库，两边都不重复。

### 契约三：一期不建 skill

知识库先落地并被实际查阅一段时间，暴露真实检索路径后再建——否则会照着想象中的流程建 skill。与 `mcp` 领域先例一致（建域至今 `consumers: []`）。

---

## 7. 实现约束与验证

### 内容来源

- **主干**：微软官方诊断文档（learn.microsoft.com 的 .NET diagnostics 专区）+ `dotnet/diagnostics` 仓库，可联网核对、版本明确
- **深度补充**：《Advanced .NET Debugging》等书籍知识体系（CLR 内部、GC 堆结构、同步块表）。该来源无法逐条取证，**凡出自此来源且无官方文档佐证的内容，正文须标注为经验性知识**，不与官方文档事实混排

### 分段写入约束

单篇 reference 预计数百行，按用户全局规则**必须分段写入**：先 `Write` 骨架或首章节，再多次 `Edit` 逐段填充。禁止单次输出整篇。

### 验证方式

| 检查项 | 命令 / 方式 |
|---|---|
| 索引一致性、id 唯一性、锚点匹配、catalog 双向一致 | `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging` |
| 健康报告（记录数、kind/level 分布、覆盖率、孤儿文件） | 同上加 `--audit` |
| 语义查重（与 csharp/wpf 是否重复登记同一事实） | `find_duplicates.py` |
| 正文交叉引用有效性 | `check_refs.py` |

### 完成判定

- `check_index.py dotnet-debugging` 零报错
- `--audit` 输出中无孤儿文件，reference 覆盖率符合第 3 节的按小节登记预期
- `find_duplicates.py` 未报出与 `csharp`/`wpf` 的重复条目
- 第 5 节两处既有文件改动已完成

### 提交方式

按仓库强制约定使用 `commit-cc-plugin` skill，不手动执行 git 工作流。



