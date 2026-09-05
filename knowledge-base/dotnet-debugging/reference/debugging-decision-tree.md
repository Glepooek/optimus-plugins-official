# 调试决策树

> 本篇是本领域的入口：按**观察到的征象**查出候选根因与对应的取证命令。

**这是一张查找表，不是操作流程。** 它回答"这个征象该用哪条命令取证"，不规定"先做什么再做什么"——多命令的编排属于 skill 的职责，见 `README.md § 收录判据`。

抓 dump 之前先读 `reference/dump-types-and-capability.md` 确定该抓哪种类型；命令报错先查 `reference/symbols-and-tool-matching.md`。

## 1. 进程挂起 / 无响应

### 候选根因
Monitor 死锁、异步死锁（同步等待异步）、线程池饥饿、长时间 GC 暂停、等待外部 I/O 无超时。

### 取证命令与判据

| 命令 | 看什么 | 结论 |
|---|---|---|
| `!threads`（`reference/sos-threads-and-stacks.md § 1. !threads`） | `Lock Count` 列 | 全 0 → 排除 Monitor 死锁 |
| `!syncblk`（`reference/sos-locks-and-async.md § 1. !syncblk`） | 等待图是否成环 | 成环 → 证实 Monitor 死锁，定位到具体两条线程 |
| `!dumpasync`（`reference/sos-locks-and-async.md § 2. !dumpasync`） | 挂起的状态机延续链 | 有挂起状态机且无线程在跑 → 证实异步死锁（.NET 6+ 限定） |
| `!threadpool`（`reference/sos-locks-and-async.md § 3. !threadpool`） | 队列长度与工作线程数 | 队列长、线程数已达上限、CPU 低 → 证实饥饿 |

### 常见误判
线程数多**不等于**饥饿——须同时看队列长度与 CPU 利用率。CPU 高而队列长是业务压力，CPU 低而队列长才是饥饿。

## 2. 内存持续增长

### 候选根因
托管对象泄漏（静态集合、事件订阅未解绑）、LOH 碎片化、非托管内存泄漏（P/Invoke 分配未释放）、加载器堆增长（反射生成程序集未卸载）。

### 取证命令与判据

| 命令 | 看什么 | 结论 |
|---|---|---|
| `!dumpheap -stat`（`reference/sos-heap-and-objects.md § 1. !dumpheap`） | 间隔采样两次，某类型 `Count` 是否持续上涨 | 持续上涨 → 证实该类型是泄漏嫌疑，转 `!gcroot` |
| `!gcroot`（`reference/sos-heap-and-objects.md § 4. !gcroot`） | 根路径末端形态（静态字段 / 事件 `_invocationList` / pinned handle / 无根） | 静态字段或事件订阅 → 证实托管泄漏；无根路径 → 排除托管泄漏 |
| `!eeheap -gc`（`reference/sos-heap-and-objects.md § 5. !eeheap`） | `GC Heap Size` 总计是否接近进程实际内存占用；LOH 段数是否增长但对象计数未同比增长 | 差距悬殊 → 排除托管堆是主因；LOH 段增长但计数未涨 → 证实碎片化而非真实增长 |
| `!gchandles`（`reference/sos-heap-and-objects.md § 6. !gchandles`） | `Strong Handles`/`Pinned Handles` 是否单调增长而对应托管对象计数稳定 | 是 → 证实句柄泄漏而非对象泄漏 |

### 常见误判
`TotalSize` 高**不等于**泄漏——体积大可能是合法的大缓存或一次性大对象分配；泄漏的判据是 `Count` 持续上涨，而非单次快照的绝对值大小。`!eeheap -gc` 排除托管堆是主因后，若 `!gchandles` 也稳定，指向非托管代码自身分配（已超出 SOS 取证范围）。

## 3. CPU 打满

### 候选根因
业务代码热点（真实计算密集）、自旋等待（错误使用忙等代替阻塞等待）、GC 压力（频繁 gen2 回收或服务器 GC 配置与核数不匹配）、无限循环（逻辑错误导致的死循环）。

### 取证命令与判据

| 命令 | 看什么 | 结论 |
|---|---|---|
| `!threads`（`reference/sos-threads-and-stacks.md § 1. !threads`） | 线程数是否远超预期且多数栈相同 | 是 → 转查是热点还是死循环，而非线程池饥饿（后者 CPU 通常不高） |
| `!clrstack -all`（`reference/sos-threads-and-stacks.md § 2. !clrstack`） | 栈顶是否停在同一业务方法 | 多线程栈顶落在同一方法且非等待帧 → 证实真实 CPU 密集负载或死循环 |
| `procdump -c -s -n`（`reference/dump-capture.md § 1. procdump（Windows，全运行时）`） | 连抓多个 dump 对比 `!clrstack` 栈顶是否变化 | 栈顶位置不变 → 证实死循环（卡在同一行）；栈顶持续变化 → 证实是正常的高频计算而非卡死 |
| `!eeheap -gc`（`reference/sos-heap-and-objects.md § 5. !eeheap`） | 堆数量是否与预期的工作站/服务器 GC 模式一致 | 服务器进程只见 1 个堆 → 证实 GC 模式配置未生效，可能是 CPU 打满的间接成因（见 `reference/clr-runtime-anatomy.md § 6. GC 模式`） |

### 常见误判
CPU 高**不等于**业务热点——服务器 GC 模式配置错误（应为多堆却只有 1 个堆）会导致 GC 本身成为 CPU 消耗大户，须先用 `!eeheap -gc` 核对堆数量再下结论。单次 dump 的 `!clrstack` 只能看到一个时点的栈顶，区分"真实计算"与"死循环"必须连抓多个 dump 对比栈顶是否变化。

## 4. 崩溃退出

### 候选根因
未处理的托管异常、栈溢出（`StackOverflowException`，通常为无限递归）、OOM（`OutOfMemoryException`）、原生代码崩溃（访问违规、P/Invoke 传参错误）。

### 取证命令与判据

| 命令 | 看什么 | 结论 |
|---|---|---|
| `!threads`（`reference/sos-threads-and-stacks.md § 1. !threads`） | `Exception` 列是否非空 | 非空 → 证实该线程有待处理异常，是崩溃第一现场候选 |
| `!pe -nested`（`reference/sos-threads-and-stacks.md § 4. !pe`） | 异常类型、`InnerException` 链 | `InnerException` 非 `<none>` → 须完整展开才能看到根因异常，只看最外层会误判 |
| `!dumpstack`（`reference/sos-threads-and-stacks.md § 3. !dumpstack`） | 是否卡在 `[InlinedCallFrame]` 附近 | 是 → 证实崩溃发生在非托管侧的 P/Invoke 调用，需非托管符号进一步定位 |

抓取自动化的选择：Windows 长期运行进程用 `reference/dump-capture.md § 4. WER LocalDumps（Windows，崩溃自动抓取）`；容器场景用 `reference/dump-capture.md § 5. DOTNET_DbgEnableMiniDump（.NET Core 3.0+，崩溃自动抓取）`——两者的选择依据见后者判据段。

### 常见误判
崩溃已发生但事先未启用自动抓取（WER 或 `DOTNET_DbgEnableMiniDump`），dump 已永久丢失，**不能**事后补抓——这不是取证方法的问题，而是前置配置缺失。栈溢出场景默认抓取的 Mini dump 通常够用（栈本身完整），无需强求 Full dump；但内存相关的崩溃（OOM）必须用 Heap 或 Full 类型，见 `reference/dump-types-and-capability.md § 1. 四种类型的能力对照`。

## 5. 间歇性抖动

### 候选根因
不适用——本节不给出候选根因列表，见下方局限说明。

### 取证命令与判据：当前范围内的已知局限与近似替代

dump 是单时点快照（`reference/dump-types-and-capability.md § 3. dump 是单时点快照`），只能回答"此刻堆里有什么、此刻线程在等什么"，无法回答"延迟尖峰是何时开始、持续多久、期间发生了什么"——这类问题本质上需要跨时间点的持续采样（如 `dotnet-counters`、`dotnet-trace`、PerfView 一类时间线工具），而这些工具不在本领域一期收录范围内。

一期可用的近似手段是连抓多个 dump 对比：`procdump -n`（`reference/dump-capture.md § 1. procdump（Windows，全运行时）` 的判据段）在抖动窗口内连续抓取多份 dump，逐份对比 `!threads`/`!clrstack`（`reference/sos-threads-and-stacks.md § 1. !threads`、`§ 2. !clrstack`）与 `!threadpool`（`reference/sos-locks-and-async.md § 3. !threadpool`）的输出差异。若抖动期间某次抓取恰好落在延迟窗口内，可能捕捉到线程池队列积压或某条线程栈异常，间接指向 `§ 1. 进程挂起 / 无响应` 或 `§ 3. CPU 打满` 中的某个根因；但抓取时机与抖动窗口不重合时，dump 里只会看到正常状态，此为方法本身的局限而非操作失误。

完整的时间线采样方案（持续指标采集、火焰图、按时间轴定位延迟尖峰对应的调用）留待后续期次收录。

### 常见误判
"抓了 dump 却什么都没看出来"**不等于**排查失败——若抓取时机未覆盖抖动发生的瞬间，这是方法的已知局限，而非取证步骤有误。不要因为单次 dump 无异常就得出"无问题"的结论，应先确认抓取时刻与抖动窗口是否重合。

## 6. 句柄 / 资源耗尽

### 候选根因
GC 句柄泄漏（强句柄/固定句柄未释放）、未释放的文件句柄或套接字（非托管资源持有未按 `IDisposable` 释放）、COM 互操作引用计数未归零。

### 取证命令与判据

| 命令 | 看什么 | 结论 |
|---|---|---|
| `!gchandles`（`reference/sos-heap-and-objects.md § 6. !gchandles`） | `Strong Handles`/`Pinned Handles`/`Ref Count Handles` 是否单调增长 | 是 → 证实 GC 句柄层面的泄漏，转 `!gcroot` 定位持有者 |
| `!gcroot`（`reference/sos-heap-and-objects.md § 4. !gcroot`） | 根路径末端是否为 `(strong handle)`/`(pinned handle)` | 是 → 证实该对象仅靠未释放的句柄维持存活 |
| `!finalizequeue`（`reference/clr-runtime-anatomy.md § 4. 终结队列`） | F-Reachable 队列条目数是否持续增长不回落 | 是 → 证实终结器线程执行速度跟不上，依赖终结器释放的非托管资源（文件句柄、套接字）迟迟不回收 |

### 常见误判
`!gchandles` 全部计数稳定**不等于**没有资源泄漏——文件句柄、套接字等操作系统级资源若从未通过 GC 句柄或终结器管理（例如原生代码里直接 `CreateFile` 后忘记 `CloseHandle`），不会在 GC 句柄表或终结队列中留下任何痕迹，已超出 SOS 命令的取证范围，需要操作系统级工具（如 Windows 的句柄查看器、Linux 的 `lsof`/`/proc/<pid>/fd`）。
