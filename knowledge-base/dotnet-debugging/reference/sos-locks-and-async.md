# SOS 命令：锁与异步

> 本篇覆盖「卡住了但 CPU 不高」这类问题的取证命令——死锁、异步挂起、线程池饥饿三种形态在表象上相似，判据不同。

异步编码规范（为何禁止 `.Result`、如何正确传播 `CancellationToken`）见 `knowledge-base/csharp/rules/04-async-programming.md`。本篇讲的是**违反之后在 dump 里的形态**。

## 1. !syncblk

### 用途与前置条件
列出所有已膨胀的同步块（sync block），是判定 Monitor 死锁的核心命令。当 `reference/sos-threads-and-stacks.md § 1. !threads` 中出现多个线程 `Lock Count` 非零、或 `reference/sos-threads-and-stacks.md § 2. !clrstack` 显示线程停在 `Monitor.Enter`/`Monitor.ReliableEnter` 帧时，用 `!syncblk` 找出这些锁分别被谁持有、谁在等——是判定循环等待、构成死锁证据链的下一步。同步块与瘦锁的机制区别见 `reference/clr-runtime-anatomy.md § 3. 同步块表`。任何类型的 dump 都支持。

### 语法与关键开关
```
!syncblk
!syncblk -all
!syncblk <同步块编号>
```
不加参数时列出全部已分配的同步块（含空闲的）；`-all` 与不加参数语义等价，用于兼容旧版本 SOS 的显式写法；给定编号则只显示该编号对应的单个同步块详情。

### 输出逐列语义

| 列 | 含义 | 异常信号 |
|---|---|---|
| `Index` | 同步块表中的索引号 | 用于查单条同步块详情 |
| `SyncBlock` | 同步块结构体地址 | —— |
| `MonitorHeld` | 编码值：持有线程记 1，此后每多一个等待线程记 2；等待线程数 = (MonitorHeld − 1) / 2 | 值为 1 表示持有但无竞争；≥3 表示存在等待线程，即发生了锁竞争 |
| `Recursion` | 持有线程对该锁的递归进入次数（`lock` 语句重入计数） | —— |
| `Owning Thread Info` | 三个子列：线程对象地址 / OS 线程 ID（十六进制）/ SOS 线程索引 | 线程索引可直接喂给 `setthread` 切换到该线程 |
| `SyncBlock Owner` | 被加锁的对象地址与类型（通常显示为 `System.Object`） | 可用 `!dumpobj` 展开该地址，确认具体是哪个业务对象被锁定 |

**注意**：SOS 输出本身没有单独一列叫 "Waiting Threads"——等待线程的**数量**是从 `MonitorHeld` 按上述公式反算出来的，`!syncblk` 不会逐个列出等待线程的身份。要确认具体是哪些线程在等，需要交叉比对 `reference/sos-threads-and-stacks.md § 2. !clrstack`（用 `-all` 找出停在 `Monitor.Enter`/`Monitor.ReliableEnter` 帧的线程）确定它们在等哪个 `SyncBlock Owner`。

### 判据：能证实 / 排除什么

用输出构造等待图：每行给出「Owning Thread 持有该锁」；再用 `!clrstack -all` 找出哪些线程的调用栈停在 `Monitor.Enter`/`Monitor.ReliableEnter` 帧，确定它们在等哪个 `SyncBlock Owner`。若存在线程 A 持锁 1 等锁 2、线程 B 持锁 2 等锁 1 的循环，**证实** Monitor 死锁。

- 输出为空、或全部 `MonitorHeld` 为 1（无竞争）→ **排除** Monitor 死锁，转 `§ 2. !dumpasync`（异步死锁不占用 Monitor，不会在 `!syncblk` 中留下痕迹）
- 单个锁的 `MonitorHeld` 极高（换算等待线程数极多）但按上述方法构不成循环 → **排除**死锁，**证实**锁竞争，属性能问题（热点锁）而非挂起

## 2. !dumpasync

### 用途与前置条件
遍历托管堆，找出全部 async 状态机对象（`async void`/`async Task`/`async Task<T>`/`async ValueTask`/`async ValueTask<T>` 编译后生成的状态机）并逐个还原其字段、延续（continuation）与 GC 根。`§ 1. !syncblk` 排除 Monitor 死锁之后的下一步——**异步死锁（同步等待异步，如 `.Result`/`.Wait()` 阻塞在一个永远等不到调度的 `await` 上）不占用 Monitor，不会出现在 `!syncblk` 里，也常常不在 `!clrstack` 的托管栈上直接可见**（挂起的 `await` 之后的延续代码尚未被调度执行，此刻并不占据任何线程的调用栈），`!dumpasync` 是定位这类"看不见的挂起点"的核心命令。

**限制（须显式说明）**：仅 **.NET 6+** 提供此命令。**.NET Framework 的 SOS 没有 `!dumpasync`**——Framework 下排查异步死锁只能退回 `!dumpheap`（详见 `reference/sos-heap-and-objects.md § 1. !dumpheap`）配合 `-type` 筛出 `Task`、`AsyncStateMachine` 等相关类型的实例，再手工展开字段还原状态机当前处于哪个 `await` 点。这不是环境配置问题，而是命令在该运行时上不存在。

### 语法与关键开关
```
!dumpasync
!dumpasync -mt <MethodTable 地址>   # 只显示指定类型的状态机实例
!dumpasync -type <类型名子串>        # 按类型名子串筛选
!dumpasync -waiting                 # 只显示当前挂起在某个 await 点（尚未完成）的状态机
!dumpasync -roots                   # 额外计算并显示每个状态机对象的 GC 根，耗时较高，大堆上默认不开
```

`-waiting` 用于从海量已完成或已释放的状态机对象中过滤出"真正卡住"的那些；`-roots` 在需要确认某个挂起的状态机是否仍被外部持有（例如被一个不会再被观察的 `Task` 字段引用）时使用，相当于对状态机对象跑一次 `!gcroot`（见 `reference/sos-heap-and-objects.md § 4. !gcroot`），但集成进了同一条命令。

### 输出逐列语义

每个状态机对象输出一个信息块，而非单一表格：

| 输出片段 | 含义 | 异常信号 |
|---|---|---|
| 首行 `Address` / `MT` / `Size` / `Name` | 状态机装箱对象的堆地址、方法表地址、大小、编译器生成的装箱类型全名（形如 `AsyncStateMachineBox<T>`） | —— |
| `StateMachine:` 一行 | 状态机的实际类型（形如 `<MethodName>d__N`），即业务方法名的直接线索 | 可据此定位是哪个业务方法的状态机卡住 |
| 字段表（`<>1__state`、`<>t__builder`、`<>u__1` 等编译器生成字段） | `<>1__state` 是当前挂起在第几个 `await` 点的原始状态值（编译器生成、无稳定公开语义，微软官方文档未逐值定义，不同编译器版本可能有出入）；`<>u__1` 等字段通常持有当前等待的 awaiter | 长时间反复采样同一状态机、`<>1__state` 值不再前进 → 挂起未被调度的信号 |
| `Continuation:` 一行 | 该状态机完成后要恢复执行的下一个延续对象地址与类型 | 延续链可逐个状态机手工跟进，还原完整的异步调用链 |
| `GC roots:`（仅 `-roots` 时输出） | 该状态机对象当前的根路径（线程栈、句柄表等），格式与 `!gcroot` 一致 | 无根路径 → 状态机对象已可回收，并非"卡住"而是已完成但对象尚未被 GC |

### 判据：能证实 / 排除什么
- 多次间隔采样后同一状态机对象仍存在且 `<>1__state` 未变化，同时该状态机对应的方法在任何线程的 `!clrstack` 栈上都找不到 → **证实**异步挂起（等待的操作本身没有完成，或完成后的延续未被调度），转查其 `Continuation` 链或用 `-roots` 确认外部持有者
- `!dumpasync -waiting` 输出为空 → **排除**"存在挂起中的 async 状态机"这一假设，卡顿根因需转查 `§ 1. !syncblk`（若尚未排除 Monitor 死锁）或 `§ 3. !threadpool`（若怀疑是调度延迟而非真正挂起）
- 当前运行时是 .NET Framework（命令本身不存在）→ 不构成"无法排查"的结论，改用 `!dumpheap -type Task`（见 `reference/sos-heap-and-objects.md § 1. !dumpheap`）列出全部 `Task`/状态机实例地址，逐个 `!dumpobj` 展开 `m_stateFlags`/状态机字段手工还原

## 3. !threadpool

### 用途与前置条件
报告线程池的整体状态：CPU 利用率、工作线程与完成端口线程的数量、工作队列积压情况。`§ 1. !syncblk` 与 `§ 2. !dumpasync` 都排除之后仍表现为"卡住但 CPU 不高"时的收口命令——用于区分是线程池饥饿（队列积压但线程数补不上来）还是别的原因。线程池的分级队列与爬坡算法机制见 `reference/clr-runtime-anatomy.md § 5. 线程池内部结构`。

### 语法与关键开关
```
!threadpool
```
不带任何参数或开关，一次性输出全部信息。

### 输出逐列语义

| 字段 | 含义 | 异常信号 |
|---|---|---|
| `CPU utilization` | 整台机器（不是当前进程）的 CPU 占用百分比 | GC 进行时该值可能被运行时人为抬高以抑制线程注入，不能单独作为"CPU 是否真的打满"的证据，须结合任务管理器/`!eeheap`交叉核对 |
| `Worker Thread: Total` | 当前工作线程总数 | 持续逼近 `MaxLimit` 且仍不够用 → 饥饿信号之一 |
| `Worker Thread: Running` | 正在执行工作项的线程数 | —— |
| `Worker Thread: Idle` | 空闲工作线程数 | 长期为 0 且队列非空 → 线程数不足以消化积压 |
| `Worker Thread: MaxLimit` / `MinLimit` | 线程池配置的线程数上下限 | `Total` 接近 `MaxLimit` 仍不够用，说明上限本身可能设置过低 |
| `Work Request in Queue` | 全局队列中等待执行的工作项数量 | 数值持续走高而 `Total` 增长缓慢 → 饥饿的直接证据 |
| `Completion Port Thread: Total` | 处理异步 I/O 完成通知的线程数 | 与 Worker Thread 是两套独立线程，队列积压若集中在这里指向 I/O 完成回调本身耗时过长，而非 CPU 绑定任务过多 |

### 判据：能证实 / 排除什么
- `Work Request in Queue` 数值很大且 `Worker Thread: Total` 接近 `MaxLimit` 却仍不见增长（或按 500 毫秒量级的爬坡节奏缓慢增长）、同时 `CPU utilization` 明显低于 100% → **证实**线程池饥饿：任务在排队而非在跑，线程数受注入速率限制补不上来。根因多为 `!dumpasync` 或 `!dumpheap`（见 `reference/sos-heap-and-objects.md § 1. !dumpheap`）能找到的同步阻塞异步方法占满了线程池，成因侧规范见 `knowledge-base/csharp/rules/04-async-programming.md § 1. 全链路异步`、`knowledge-base/csharp/rules/04-async-programming.md § 2. 反模式表`
- `Work Request in Queue` 为 0 或很小、`Worker Thread` 各项数值平稳 → **排除**线程池饥饿，卡顿应转查 `§ 1. !syncblk`（Monitor 死锁）或 `§ 2. !dumpasync`（异步挂起）
- `CPU utilization` 接近 100% 且各线程 `!clrstack`（见 `reference/sos-threads-and-stacks.md § 2. !clrstack`）栈顶均为业务代码而非等待帧 → **排除**"卡住"这一前提，问题是真实的 CPU 密集型负载而非挂起，不属于本篇范围
