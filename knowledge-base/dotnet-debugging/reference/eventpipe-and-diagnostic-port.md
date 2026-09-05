# EventPipe 与诊断端口

> **运行时要求**：EventPipe 是 .NET Core+ 的运行时内置特性，**.NET Framework 4.x 完全不可用**。Framework 的活体诊断依赖 ETW / PerfView，不在本领域当前范围内。

本篇只讲机制不讲命令，是 `reference/dotnet-counters.md` 与 `reference/dotnet-trace.md` 的术语基础。两篇中每条命令的「用途与前置条件」段都会指回本篇。

## 1. EventPipe 与 ETW 的关系

**用途**：EventPipe 是 .NET Core+ 内置的跨平台事件采集通道，与 Windows 专属的 ETW（Event Tracing for Windows）、Linux 专属的 `perf_events` 是三条不同的采集通道，能力边界并不相同：

| 能力 | EventPipe | EventPipe（`user_events`） | ETW | `perf_events` |
|---|---|---|---|---|
| 跨平台 | 是 | 否（仅受支持的 Linux 发行版） | 否（仅 Windows） | 否（仅 Linux） |
| 需要 admin/root | 否 | 是 | 是 | 是 |
| 可获取 OS/内核事件 | 否 | 是 | 是 | 是 |
| 可解析原生调用栈 | 否 | 是 | 是 | 是 |

两条结论：

1. 「无需 admin/root」是 EventPipe 相对 ETW 的关键实用优势——只要采集工具与目标进程以同一用户运行即可发起采集，不需要提权，这也是容器、CI、共享主机等受限环境下仍能做诊断的前提。
2. EventPipe 的作用域**限于托管代码与运行时自身**，采到的调用栈只含托管帧，既不包含内核态事件，也无法解析原生（native）调用栈。这解释了本领域为何暂不含 PerfView/ETW 相关内容，也划出了何时必须转向 OS 级工具（ETW 或 `perf_events`）的边界：一旦问题涉及内核态行为或原生代码栈，EventPipe 本身给不出答案。

## 2. 诊断端口与连接建立

**用途**：诊断端口（Diagnostic Port）是采集工具与目标 .NET 进程之间建立 IPC 连接的通道，`dotnet-counters`、`dotnet-trace`、`dotnet-dump` 等诊断工具都通过它与目标进程通信。

**传输形式**：Windows 上为命名管道（named pipe）；Linux / macOS 上为 Unix domain socket，落在 `TMPDIR` 指向的目录下；移动端场景为 IP:port。

**连接方向**：由环境变量 `DOTNET_DiagnosticPorts` 控制，有两个方向：

- **默认方向**：运行时启动时在诊断端口上 listen，采集工具随后 connect 上去。这是最常见的用法——进程先起，工具后连。
- **反向（`,connect` 后缀）**：工具先在某个端口上监听，进程启动时反过来 connect 到工具。这种方向用于工具需要**先于目标进程启动**才能捕获数据的场景（例如需要覆盖进程启动最早期阶段的采集），是 § 6 基线采集中「启动阶段采集」的机制基础。

**容器踩坑**：Linux / macOS 上 `-p`（进程 ID）或 `-n`（进程名）定位目标进程时，要求采集工具与目标进程**共享同一个 `TMPDIR`**——诊断端口的 Unix domain socket 文件就落在这个目录下。如果工具运行在与目标进程不同的容器（不同 PID namespace 或挂载了不同的临时目录），工具找不到对应的 socket 文件，表现为命令**超时**，而不是明确报出「找不到进程」。跨 PID namespace 采集时，必须显式指定诊断端口路径，不能依赖按进程名/ID 的默认定位方式。

**权限**：诊断端口不做额外的身份校验，但操作系统层面要求采集工具与目标进程以同一用户运行，或以 root/管理员身份运行。

**位数匹配**：与 dump 分析一致，采集工具的位数必须与目标进程的位数匹配，否则连接建立会报 `System.ComponentModel.Win32Exception (299)` 而非明确的位数不匹配提示，具体成因与识别方式见 reference/dump-types-and-capability.md § 2. 位数必须匹配。

## 3. Provider / Keyword / Level 三级过滤

**用途**：采集工具指定要采集哪些事件时，遵循统一的过滤语法：

```
KnownProviderName[:Flags[:Level[:KeyValueArgs]]]
```

三段过滤依次收窄：

- **Provider**：事件的来源，如 `Microsoft-Windows-DotNETRuntime`（CLR 运行时事件）、`System.Runtime`（运行时计数器）、或应用自定义的 `EventSource` 名称。
- **Flags（Keyword）**：十六进制位掩码，用于在一个 provider 内部再筛选事件类别（如只要 GC 事件、只要异常事件）。CLR provider 的 keyword 既有原始的十六进制位掩码取值，也有对应的字符串别名（如 `GCKeyword`），两者语义等价，字符串别名更不容易写错位。
- **Level（详细程度）**：六档取值，由粗到细依次为 `logalways`（0）、`critical`、`error`、`warning`、`informational`、`verbose`（5）。Level 是阈值语义——指定某一档，等于要该档及更详细的全部事件。

**风险提示**：Keyword 或 Level 写窄了，效果是**静默少采**事件，而不是报错或警告——采集会正常结束、文件正常生成，但里面缺了本该有的事件类别，往往要等到分析阶段发现关键事件缺失才会察觉。这与 § 5 缓冲区溢出丢事件同属「采集结果看似正常实则残缺」的静默失败类风险，排查时应把两者列为并列的候选成因。

## 4. EventCounter 与 Meter 两套计数器体系

**用途**：.NET 的计数器体系在 .NET 9 前后发生了一次命名分水岭：.NET 9 引入了基于 `System.Diagnostics.Metrics` 的 `System.Runtime` **Meter**，与早期的 **EventCounter** 是两套并存但不等价的体系。

- **.NET 8 及更低版本**：不存在 `System.Runtime` Meter，`dotnet-counters` 等工具会自动 **fallback** 到旧的 `System.Runtime` EventCounters。
- **.NET 9 及更高版本**：两套体系可以同时存在，但新指标以 Meter 形式发布，命名与单位表示方式都变了。

六行对照示例：

| 含义 | .NET 9+（Meter） | .NET 8-（EventCounter） |
|---|---|---|
| GC 堆大小 | `dotnet.gc.last_collection.heap.size (By)` | `GC Heap Size (MB)` |
| 线程池队列 | `dotnet.thread_pool.queue.length ({work_item})` | `ThreadPool Queue Length` |
| 线程池线程数 | `dotnet.thread_pool.thread.count ({thread})` | `ThreadPool Thread Count` |
| 锁竞争 | `dotnet.monitor.lock_contentions ({contention})` | `Monitor Lock Contention Count` |
| GC 暂停 | `dotnet.gc.pause.time (s)` | `% Time in GC since last GC (%)` |
| 工作集 | `dotnet.process.memory.working_set (By)` | `Working Set (MB)` |

两点必须写明：

1. .NET 8 及更低版本无 `System.Runtime` Meter，工具自动 fallback 到旧 EventCounters——判据引用计数器名时必须先确认目标运行时版本，同一份判据文字在两个版本上可能指向完全不同的名称。
2. 新命名的单位随名称一并独立显示（`(By)` 字节、`(s)` 秒），旧命名的单位内嵌在名称字符串里（`(MB)`、`(%)`）。涉及单位换算的判据（例如把字节换算成 MB 再比较阈值）必须先确认拿到的是哪一套命名，混用会导致换算基数错误。

具体计数器与判据的完整对照见 reference/dotnet-counters.md § 3. 内置计数器与判据对照。

## 5. 采集开销与缓冲区

**用途**：EventPipe 采集涉及两个不同层级的缓冲区，名称相近但作用范围与生效条件完全不同，必须明确区分——混为一谈会写出自相矛盾的默认值。

- **工具侧缓冲区**：`dotnet-trace collect --buffersize`，默认 **256 MB**。这是采集工具与目标进程之间传输事件时使用的缓冲区，由发起采集的工具决定大小。
- **运行时侧缓冲区**：环境变量 `DOTNET_EventPipeCircularMB`，默认 **`400`（十六进制），即 1024 MB**。这是运行时内部维护 EventPipe 会话的环形缓冲区大小，仅在以 `DOTNET_EnableEventPipe` 直接启动会话（应用自身落盘 trace，不经工具连接）时生效。

**风险提示**：无论哪一层缓冲区，当事件产生速度快于消费/落盘速度时，缓冲区会发生溢出，溢出部分的事件被**直接丢弃且不报错**——采集会正常结束、trace 文件正常生成、命令退出码正常，但文件里已经丢失了部分事件。这与 § 3 过滤写窄导致的静默少采是同一类风险：采集结果表面正常，实则残缺，只有在分析阶段发现关键事件缺失或计数对不上时才会暴露。

完整的 EventPipe 环境变量表：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DOTNET_EnableEventPipe` | `0` | 置 `1` 启动直接写文件的 EventPipe 会话 |
| `DOTNET_EventPipeOutputPath` | `trace.nettrace` | 输出路径；.NET 6 起字符串 `{pid}` 会被替换为进程 ID |
| `DOTNET_EventPipeCircularMB` | `400`（十六进制，即 1024 MB） | 内部缓冲区大小，**十六进制取值**。仅在经 `DOTNET_EnableEventPipe` 启动时生效 |
| `DOTNET_EventPipeProcNumbers` | `0` | 置 `1` 在事件头中记录处理器编号 |
| `DOTNET_EventPipeThreadSamplingRate` | 10 ms（约 100 Hz） | .NET 11+ 可用。**进程全局，影响所有 EventPipe 会话**，含工具发起的按需采集 |
| `DOTNET_EventPipeConfig` | 见下 | 语法 `<provider>:<keyword>:<level>`，多个以逗号分隔 |

未设 `DOTNET_EventPipeConfig` 而启用了 EventPipe 时，默认启用三个 provider：`Microsoft-Windows-DotNETRuntime:4c14fccbd:5`、`Microsoft-Windows-DotNETRuntimePrivate:4002000b:5`、`Microsoft-DotNETCore-SampleProfiler:0:5`。

## 6. 基线采集：时间线判据的前置条件

**用途**：本领域二期引入的时间线类判据（观察某个计数器随时间的变化趋势），全部依赖一个共用前提——有可比的基线数据。没有基线，单份时间线采样几乎不可判读：同一个数值（例如「堆占用 800 MB」）可能是这台服务正常水位下的稳态值，也可能是内存泄漏进行到一半，还可能是即将触发 gen2 回收前的正常峰值。三种情况在数值上完全相同，只有对照基线才能区分。

**基线的采集要求**：

- **时机**：应在业务**稳态期**采集，即系统处于正常负载、无发布、无异常流量的时段，避免把非典型状态误当作正常基线。
- **时长**：应覆盖**至少一个完整业务周期**（如一天的高峰-低谷循环，或一周的工作日-周末循环，取决于业务的周期性特征），避免把周期内某个局部片段误当作全局常态。
- **对齐方式**：故障期采集与基线采集必须使用**同一组 provider 和同一采样率**，否则两次数据在维度或粒度上不对齐，无法直接比较——采样率不同会导致同一段时间窗口内的数据点数量不同，provider 不同则可能连要对比的计数器都缺失。

不满足以上任一条件，基线与故障期数据之间的比较就失去意义，时间线判据也就无从成立。这一前提是本领域全部时间线判据的共用基础，后续涉及趋势判断的小节均以此为默认已满足的条件。
