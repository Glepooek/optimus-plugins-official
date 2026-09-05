# dotnet-counters

> 前置概念（provider/keyword/level 过滤语法、EventCounter 与 Meter 两套计数器体系、诊断端口连接方式）见 `reference/eventpipe-and-diagnostic-port.md`，本篇只讲 `dotnet-counters` 这一具体工具的命令与判据。

## 1. dotnet-counters monitor

### 用途与前置条件

`dotnet-counters monitor` 在终端里实时刷新显示目标进程的计数器数值，用于现场观察某个指标当下的走势。前置条件见 `reference/eventpipe-and-diagnostic-port.md § 2. 诊断端口与连接建立`（进程定位与权限）与 `§ 6. 基线采集：时间线判据的前置条件`（没有基线时本命令的输出不可判读）。

安装：
```
dotnet tool install --global dotnet-counters
```

**`monitor` 无历史留存**：终端刷新是覆盖式的，只显示当前采样点，关掉命令或翻篇即丢，不产出可回看的文件。只适合已经确认问题正在复现、可以现场盯着看的场景；间歇性问题**必须**改用 `§ 2. dotnet-counters collect` 落盘，事后才能比对复现窗口前后的数据。

### 语法与关键开关

用 PID 监控默认计数器集合（`System.Runtime`）：
```
dotnet-counters monitor -p <PID>
```

指定 provider 与具体计数器，并设置刷新间隔为 1 秒：
```
dotnet-counters monitor -p <PID> --counters System.Runtime[cpu-usage,gc-heap-size],Microsoft.AspNetCore.Hosting --refresh-interval 1
```

按进程名或诊断端口路径定位：
```
dotnet-counters monitor -n <进程名>
dotnet-counters monitor --diagnostic-port <端口路径>
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `-p, --process-id <PID>` | 按进程 ID 定位目标 | 与 `-n`、`--diagnostic-port` 三选一，缺一个定位方式命令无法确定目标进程 |
| `-n, --name <进程名>` | 按进程名定位目标 | 同上；容器跨 PID namespace 场景下按名定位可能连接超时，须改用 `--diagnostic-port` |
| `--diagnostic-port <路径>` | 直接指定诊断端口路径连接 | 跨 PID namespace 或 `TMPDIR` 不一致时，`-p`/`-n` 默认定位方式会超时，只能显式指定端口路径 |
| `--counters <provider[计数器列表],...>` | 指定要监控的 provider 与计数器子集 | 不指定时默认只监控 `System.Runtime`，其余 provider（如 ASP.NET Core 请求指标）的计数器不会出现在面板上 |
| `--refresh-interval <秒>` | 设置采样刷新间隔 | 默认 1 秒；间隔太短在高频计数器上会产生视觉噪声，太长会错过短暂尖峰 |

### 输出逐列语义

面板按 provider 分组，每个 provider 下逐行列出计数器名与当前值：

- **计数器名**：随运行时版本不同而不同，见 `§ 3. 内置计数器与判据对照` 的双列对照——面板上直接显示 .NET 9+ 的 Meter 名或 .NET 8- 的 EventCounter 名，取决于目标进程的运行时版本。
- **当前值**：多数计数器显示的是采样瞬间的即时值（Gauge 语义），少数计数器（如 GC 次数、异常数）是自进程启动的累计值（Counter 语义）——判断某个值属于哪种语义，需要对照 `§ 3. 内置计数器与判据对照` 中的说明，不能仅凭数值大小猜测。
- **单位**：.NET 9+ 的 Meter 名称自带单位后缀（如 `(By)` 字节、`(s)` 秒），.NET 8- 的 EventCounter 名称把单位内嵌在名字字符串里（如 `(MB)`、`(%)`），详见 `reference/eventpipe-and-diagnostic-port.md § 4. EventCounter 与 Meter 两套计数器体系`。

### 判据：基线形态 / 异常形态 / 区分点

**基线形态**：面板上各计数器数值在业务稳态期内围绕某个中枢值小幅波动，无持续单向变化。

**异常形态**：某个计数器的数值出现持续单向变化（只涨不跌，或跌到某个新水位后不再回升），且这一变化跨越了多次自然波动周期，不是单次尖峰。

**区分点**：单次刷新看到的高值本身不能判断异常——必须与 `reference/eventpipe-and-diagnostic-port.md § 6. 基线采集：时间线判据的前置条件` 中采集的稳态基线比对，同一个数值在基线之上是异常、在基线波动范围之内则是正常。`monitor` 因为不落盘，只能靠肉眼记忆或截图与历史基线做粗略比对；需要精确比对时应改用 `§ 2. dotnet-counters collect` 落盘后逐点比较。具体指标的判据表见 `§ 3. 内置计数器与判据对照`。

## 2. dotnet-counters collect

### 用途与前置条件

`dotnet-counters collect` 把计数器数据按固定间隔落盘为文件，供事后比对分析。前置条件见 `reference/eventpipe-and-diagnostic-port.md § 2. 诊断端口与连接建立`（进程定位与权限）与 `§ 6. 基线采集：时间线判据的前置条件`（没有基线时本命令的输出不可判读）。

**`collect` 落盘留存**：数据写入文件后可随时打开重看，也能与基线文件按时间戳对齐比对。间歇性问题（现场没人盯着、复现时刻不可预知）**必须**用 `collect`——这是唯一能在无人值守的情况下把复现窗口前后的完整数据都留下来的方式；`monitor` 关掉即丢，赶不上复现时刻就永久错过。

### 语法与关键开关

用 PID 采集，输出为 CSV：
```
dotnet-counters collect -p <PID> --format csv -o metrics.csv
```

指定计数器子集，输出为 JSON，采样间隔 5 秒：
```
dotnet-counters collect -p <PID> --format json -o metrics.json --counters System.Runtime,System.Runtime[gc-heap-size,threadpool-queue-length] --refresh-interval 5
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `-p, --process-id <PID>` / `-n, --name <进程名>` / `--diagnostic-port <路径>` | 进程定位方式，语义与 `monitor` 一致 | 三选一缺失则命令无法确定目标进程 |
| `--format <csv\|json>` | 输出文件格式 | 默认 `csv`；需要程序化解析嵌套结构时选 `json`，人工用表格软件比对时选 `csv` |
| `-o, --output <路径>` | 指定输出文件路径 | 不指定时落在当前目录，文件名含时间戳；批量采集多台机器时应显式命名，避免文件互相覆盖或混淆来源 |
| `--counters <provider[计数器列表],...>` | 指定要采集的 provider 与计数器子集 | 与 `monitor` 相同，不指定则只采 `System.Runtime` |
| `--refresh-interval <秒>` | 采样落盘间隔 | 默认 1 秒；与基线采集时使用的间隔必须一致，否则两次数据点数量不对齐，无法直接比较（见 `reference/eventpipe-and-diagnostic-port.md § 6. 基线采集：时间线判据的前置条件` 的对齐方式要求） |

### 输出逐列语义

CSV 文件每行是一个采样时间点，列依次为：时间戳、provider 名、计数器名、计数器类型（Metric/Rate/Gauge 等）、数值。JSON 格式按时间点分组嵌套，每个时间点下按 provider、计数器展开，字段语义与 CSV 一致。计数器名的版本差异（.NET 9+ Meter 名 vs .NET 8- EventCounter 名）与单位表示方式同 `§ 1. dotnet-counters monitor` 的说明，见 `reference/eventpipe-and-diagnostic-port.md § 4. EventCounter 与 Meter 两套计数器体系`。

### 判据：基线形态 / 异常形态 / 区分点

**基线形态**：把稳态期采集的文件按计数器列拆开画出时间序列，各计数器值应在中枢值上下小幅波动，无持续单向趋势。

**异常形态**：故障期文件中同一计数器的时间序列出现持续单向变化，且变化幅度与持续时长明显超出基线文件里观察到的波动范围。

**区分点**：`collect` 的核心价值就在于把基线文件与故障期文件按同一采样间隔逐点对齐比较——`monitor` 只能凭记忆粗略比对，`collect` 能拿两份文件做精确的逐点差值或画图叠加。判据成立的前提是两次采集的 provider 集合与 `--refresh-interval` 一致，否则时间轴上的点位无法对应，比较结果不可信。具体指标的判据表见 `§ 3. 内置计数器与判据对照`。

## 3. 内置计数器与判据对照

两套计数器体系的命名分水岭见 `reference/eventpipe-and-diagnostic-port.md § 4. EventCounter 与 Meter 两套计数器体系`，本节不重复其机制，只给出具体计数器的双版本名称与判据对照。「基线形态」「异常形态」均为形态描述，不写绝对阈值；「下一步」一律指向一期已建成的 SOS 命令。

| 指标 | .NET 9+ 名 | .NET 8- 名 | 基线形态 | 异常形态 | 下一步 |
|---|---|---|---|---|---|
| 堆大小 | `dotnet.gc.last_collection.heap.size (By)` | `GC Heap Size (MB)` | 随 GC 周期性回落，呈锯齿波形 | 包络线呈上升台阶，回收后不回落到原水位 | `reference/sos-heap-and-objects.md § 4. !gcroot` |
| 提交量 | `dotnet.gc.last_collection.memory.committed_size (By)` | `GC Committed Bytes (MB)` | 与堆大小同步小幅波动，可能高于堆大小（含预留） | 持续增长且增幅明显超出堆大小同期增幅 | `reference/sos-heap-and-objects.md § 5. !eeheap` |
| 碎片量 | `dotnet.gc.last_collection.heap.fragmentation.size (By)` | `GC Fragmentation (%)` | 占堆比例稳定在低位（.NET 9+ 须自行除以堆大小换算） | 占堆比例持续攀升 | `reference/sos-heap-and-objects.md § 5. !eeheap` |
| GC 次数（分代） | `dotnet.gc.collections ({collection})` | `# Gen 0/1/2 GCs` | gen0 频繁、gen2 稀少，符合正常晋升比例 | gen2 次数占比异常升高，指向大量对象晋升到高代 | `reference/sos-heap-and-objects.md § 1. !dumpheap` |
| GC 暂停时间 | `dotnet.gc.pause.time (s)` | `% Time in GC since last GC (%)` | 占比低且平稳（.NET 9+ 须取累计值的斜率） | 占比持续升高、单次暂停时长变长 | `reference/sos-heap-and-objects.md § 1. !dumpheap` |
| 累计分配量 | `dotnet.gc.heap.total_allocated (By)` | `Allocation Rate (B / 1 sec)` | 分配速率随业务吞吐同步变化，无脱钩增长（.NET 9+ 须取累计值的斜率） | 分配速率相对吞吐脱钩陡升（振幅增大而非堆占用抬高） | `reference/sos-heap-and-objects.md § 1. !dumpheap` |
| 线程池线程数 | `dotnet.thread_pool.thread.count ({thread})` | `ThreadPool Thread Count` | 随负载爬坡后企稳在某一水位 | 持续顶在上限附近且队列长度同时升高 | `reference/sos-locks-and-async.md § 3. !threadpool` |
| 线程池队列长度 | `dotnet.thread_pool.queue.length ({work_item})` | `ThreadPool Queue Length` | 短暂出现后迅速清零 | 持续 > 0 且线程数达上限、CPU 不高 | `reference/sos-locks-and-async.md § 3. !threadpool` |
| 工作项完成数 | `dotnet.thread_pool.work_item.count ({work_item})` | `ThreadPool Completed Work Item Count` | 完成速率与请求吞吐同步升降 | 完成速率骤降但队列长度同时升高 | `reference/sos-locks-and-async.md § 3. !threadpool` |
| 锁竞争次数 | `dotnet.monitor.lock_contentions ({contention})` | `Monitor Lock Contention Count` | 累计计数按低速率平稳增长 | 速率陡升伴随吞吐下降 | `reference/sos-locks-and-async.md § 1. !syncblk` |
| 异常数 | `dotnet.exceptions ({exception})` | `Exception Count` | 按应用自身基线平稳（first-chance 语义下未必接近 0） | 速率相对自身基线陡升 | `reference/sos-threads-and-stacks.md § 4. !pe` |
| 工作集 | `dotnet.process.memory.working_set (By)` | `Working Set (MB)` | 与托管堆、非托管内存总量同步，增长后进入平台期 | 持续增长但托管堆大小未同步增长 | `reference/sos-heap-and-objects.md § 6. !gchandles` |
| 计时器数 | `dotnet.timer.count ({timer})` | `Number of Active Timers` | 与已注册的定时任务数量匹配，保持稳定 | 持续增长且不随定时任务结束而回落 | `reference/sos-heap-and-objects.md § 4. !gcroot` |
| 程序集数 | `dotnet.assembly.count ({assembly})` | `Number of Assemblies Loaded` | 应用启动完成后趋于稳定，不再增长 | 持续增长（动态程序集反复加载未卸载） | `reference/sos-heap-and-objects.md § 5. !eeheap` |

**四条语义陷阱（直接影响上表判据的正确用法）**：

1. **双列并非处处语义等价，有三行需要换算后才可比**。`dotnet.gc.pause.time`、`dotnet.gc.heap.total_allocated` 在 .NET 9+ 侧是 **Counter（自进程启动的累计量，只增不减）**，而其 .NET 8- 对应项 `% Time in GC since last GC`、`Allocation Rate` 是**百分比与速率**；`fragmentation.size` 在 .NET 9+ 侧是**绝对字节数**，对应项 `GC Fragmentation` 是**百分比**。上表的形态判据按 .NET 8- 侧的语义书写，在 .NET 9+ 侧使用时：前两者须取累计值的**斜率**（单位时间增量），碎片量须**除以堆大小**换算为占比。直接照搬会得到一条永远上升的曲线，判据失效。
2. `dotnet.gc.heap.total_allocated` 是**自进程启动的累计量**，只增不减，不是当前堆占用——用它判断泄漏是错误用法，判泄漏须看「堆大小」行的 `dotnet.gc.last_collection.heap.size`。
3. `dotnet.gc.last_collection.memory.committed_size`（「提交量」行）**可能大于堆大小**，因为其中含为未来分配预留的部分，不能把两者的差值直接当作碎片量；碎片量有独立计数器，即上表「碎片量」行的 `dotnet.gc.last_collection.heap.fragmentation.size`。
4. `dotnet.exceptions`（「异常数」行）计的是 **first-chance** 异常，等价于 `AppDomain.FirstChanceException` 的触发次数，含已被 `catch` 捕获、未导致任何问题的异常，因此其基线**未必接近 0**——判据必须按应用自身的历史基线比较速率变化，而不是假设健康状态下该值应趋近于零。

