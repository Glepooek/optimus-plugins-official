# dotnet-trace

> 前置概念（诊断端口连接方式、provider/keyword/level 过滤语法、采集缓冲区）见 `reference/eventpipe-and-diagnostic-port.md`，本篇只讲 `dotnet-trace` 这一具体工具的命令与判据。

## 1. dotnet-trace collect

### 用途与前置条件

`dotnet-trace collect` 对目标 .NET 进程发起 EventPipe 采集，把指定 provider/keyword/level 过滤下的事件流写入 `.nettrace` 文件，用于 CPU 热点、GC 行为、异步状态机等需要**时间线级**事件而非计数器快照的排查场景。前置条件（进程定位方式、诊断端口传输形式、容器跨 `TMPDIR`/PID namespace 约束）见 `reference/eventpipe-and-diagnostic-port.md § 2. 诊断端口与连接建立`；过滤语法（Provider/Keyword/Level 三段式）见 `reference/eventpipe-and-diagnostic-port.md § 3. Provider / Keyword / Level 三级过滤`，本篇不重复。

安装：
```
dotnet tool install --global dotnet-trace
```

### 语法与关键开关

用 PID 采集，按内置 profile（默认行为，见 `§ 2. profile 选择`）：
```
dotnet-trace collect -p <PID>
```

用 `--providers` 显式指定 provider/keyword/level，覆盖默认 profile：
```
dotnet-trace collect -p <PID> --providers Microsoft-Windows-DotNETRuntime:0x1:5
```

用 `--clrevents` 简写常见 CLR 事件类别（等价于对 `Microsoft-Windows-DotNETRuntime` 指定对应 keyword，写法更短但可选类别有限）：
```
dotnet-trace collect -p <PID> --clrevents gc+exception
```

采集 30 秒后自动停止：
```
dotnet-trace collect -p <PID> --duration 00:00:30
```

按事件出现自动停止（间歇性问题复现时刻不可预知，需要无人值守守到事件本身触发）：
```
dotnet-trace collect -p <PID> --stopping-event-provider-name Microsoft-Windows-DotNETRuntime --stopping-event-event-name Exception
```

由工具直接拉起目标进程并从第一行代码开始采集（覆盖启动阶段，此时进程尚不存在，无法用 `-p` 定位）：
```
dotnet-trace collect -- <可执行文件路径> <应用自身的参数>
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `-p, --process-id <PID>` / `-n, --name <进程名>` / `--diagnostic-port <路径>` | 进程定位方式，语义与 `dotnet-counters` 一致 | 三选一缺失则命令无法确定目标进程 |
| `-- <command>` | 由工具启动目标进程，采集覆盖进程整个生命周期（含启动阶段） | 只能在进程已运行后附加，JIT 预热、程序集加载、静态构造函数等启动期事件全部错过，且这些问题无法靠重连补采 |
| `--profile <名称>` | 使用内置 profile 展开为对应的 provider 组合 | 不指定时按官方默认 profile 采集，具体展开见 `§ 2. profile 选择` |
| `--providers <过滤串>` | 显式指定 provider/keyword/level，可与 `--profile` 叠加 | 不指定则仅按 `--profile` 展开的 provider 采集，捕获不到应用自定义 `EventSource` 的事件 |
| `--clrevents <类别>` | 按预定义类别名（`gc`、`exception` 等）简写常见 CLR keyword | 需要手写完整的十六进制 keyword，容易写窄导致静默少采（见 `reference/eventpipe-and-diagnostic-port.md § 3. Provider / Keyword / Level 三级过滤`的风险提示） |
| `--duration <hh:mm:ss>` | 采集指定时长后自动停止 | 需人工按 <kbd>Enter</kbd> 或 <kbd>Ctrl+C</kbd> 手动停止，无人值守场景无法收尾 |
| `--stopping-event-provider-name` / `--stopping-event-event-name` | 指定某 provider 的某个事件出现时自动停止采集 | 只能靠 `--duration` 定时或人工停止，赶不上事件出现的精确时刻，事后回看采到的窗口可能偏早或偏晚 |
| `--buffersize <MB>` | 工具侧缓冲区大小 | 默认值、溢出行为与运行时侧缓冲区的区分见 `reference/eventpipe-and-diagnostic-port.md § 5. 采集开销与缓冲区`，本篇不重复 |
| `-o, --output <路径>` | 指定输出文件路径 | 不指定时落在当前目录，文件名含进程名与时间戳 |

**`--stopping-event-*` 与 procdump 阈值触发同构**：`--stopping-event-provider-name`/`--stopping-event-event-name` 让采集在特定事件出现时自动停止，解决的是「问题偶发、人守不住」——这与一期 `procdump -c`/`-p`/`-m` 按 CPU/性能计数器/内存阈值触发抓取是同一类设计：都是把「何时该固定证据」的判断从人工值守转移到工具对征象本身的监视上。区别在于 `procdump` 触发的是单时点快照，`dotnet-trace` 触发的是一段时间线的收尾。

### 输出与产物位置

默认落在当前工作目录，文件名形如 `<进程名>_<年月日>_<时分秒>.nettrace`。`-o` 可指定完整路径与文件名。

### 判据

采集是否覆盖到问题窗口，取决于停止条件与征象出现时刻是否吻合：`--duration` 定时停止适合已知问题会在固定时间窗口内复现的场景；`--stopping-event-*` 适合问题以特定事件为标志但出现时刻不可预知的场景。两者都不解决「采集期间事件速度超过缓冲区消费能力」的溢出问题，该风险的识别与规避见 `reference/eventpipe-and-diagnostic-port.md § 5. 采集开销与缓冲区`。

## 2. profile 选择

### 用途与前置条件

内置 profile 是对常用 provider/keyword/level 组合的命名封装，避免每次手写完整的过滤串。`--profile` 与 `--providers` 可同时指定，此时两者展开的 provider 集合取并集叠加，而非互斥覆盖。实际取值以官方文档为准，可用 `dotnet-trace list-profiles` 核对（本机未安装 `dotnet-trace`，本节数值未能现场核验，均取自官方文档已核验事实）。

### 语法与关键开关

查看当前版本下各 profile 展开后的实际 provider/keyword 组合：
```
dotnet-trace list-profiles
```

按 profile 采集（`collect` 默认即启用 `dotnet-common` + `dotnet-sampled-thread-time`，无需显式指定）：
```
dotnet-trace collect -p <PID> --profile dotnet-sampled-thread-time,dotnet-common
```

**✗ 不要写 `--profile cpu-sampling`**——该取值已从 `collect` 移除，照抄旧教程会直接报错，原因与替代写法见下。

`collect` 下的 `cpu-sampling` **已被移除**——名称本身具有误导性：它实际采样的是**所有线程**，而非仅高 CPU 占用的线程，与名称暗示的语义不符，这是官方移除它的原因。当前 `collect` 默认启用的是 `dotnet-common` + `dotnet-sampled-thread-time` 两个 profile 的组合。

官方给出的近似等价替代写法：
```
dotnet-trace collect -p <PID> --profile dotnet-sampled-thread-time,dotnet-common
```

需要精确复刻旧版 `cpu-sampling` 行为时，改用显式 provider 写法：
```
dotnet-trace collect -p <PID> --profile dotnet-sampled-thread-time --providers "Microsoft-Windows-DotNETRuntime:0x14C14FCCBD:4"
```

| profile / 开关 | 含义 | 不加的后果 |
|---|---|---|
| `--profile <名称>` | 使用内置 profile 展开为对应的 provider 组合 | 不指定时按官方默认 profile（`dotnet-common` + `dotnet-sampled-thread-time`）采集 |
| `dotnet-common` | 默认基线 profile，覆盖常规运行时诊断事件 | 单独使用时不含采样式调用栈信息 |
| `dotnet-sampled-thread-time` | 按固定频率采样各线程调用栈，用于 CPU 热点分析 | 不启用则 `§ 3. dotnet-trace report topN` 无采样数据可供聚合 |
| `--providers`（与 `--profile` 同时指定） | 在 profile 展开的基础上叠加额外 provider | 两者取并集，不是互斥覆盖——遗漏这一点会误以为 `--providers` 会覆盖 profile 默认值 |

### 输出与产物位置

同 `§ 1. dotnet-trace collect`，profile 的选择只影响采集期间实际生效的 provider/keyword 组合，不影响输出文件的位置与命名规则。

### 判据

**同名不同义陷阱**：`cpu-sampling` 这个 profile 名称在 `collect-linux` 子命令下**仍然存在**，但语义与 `collect` 下曾经的同名 profile完全不同——`collect-linux` 的 `cpu-sampling` 基于 Linux `perf` 做**内核态** CPU 采样，发射为 `Universal.Events/cpu` 事件，而非 `collect` 下基于 EventPipe 的托管线程采样。照抄网上仍在流传的旧教程（写 `dotnet-trace collect --profile cpu-sampling`）会直接报错，因为该取值在 `collect` 下已不存在；即便误套到 `collect-linux` 下跑通，采到的也是内核态数据而非预期的托管调用栈——这是本期与现存网络资料偏离最大之处。

`collect-linux` 子命令本身有额外可用性约束：需 .NET 10+、Linux 内核 6.4+、以 root 运行、glibc 2.27+，且目前仍是**预览特性**，行为可能随版本变化。判断该走 `collect` 的 `dotnet-sampled-thread-time` 替代写法、还是走 `collect-linux` 的 `cpu-sampling`，取决于是否需要内核态视角与上述环境约束是否满足。

## 3. dotnet-trace report topN

### 用途与前置条件

`dotnet-trace report topN` 直接从已采集的 `.nettrace` 文件读出栈上耗时最长的 N 个方法，无需借助外部可视化工具即可快速定位热点。依赖 `§ 2. profile 选择` 中启用采样式调用栈信息的 profile（如 `dotnet-sampled-thread-time`）采到的数据；若采集时未启用采样式 provider，本命令无数据可聚合。

### 语法与关键开关

列出耗时最长的 20 个方法（默认按 exclusive 排序）：
```
dotnet-trace report trace.nettrace topN
```

指定数量并切换为 inclusive 排序：
```
dotnet-trace report trace.nettrace topN -n 10 --inclusive
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `-n <数量>` | 指定输出的方法条数 | 默认输出条数由工具内置，未显式指定时可能遗漏排名靠后但仍值得关注的方法 |
| `--inclusive` | 切换为 inclusive 排序（含被调用方法耗时） | 不加则按默认的 **exclusive** 排序（仅方法自身耗时，不含被调用方法） |

### 输出与产物位置

命令直接在终端输出排序后的方法列表，不产出额外文件。

### 判据

默认 **exclusive** 排序只统计方法自身的耗时，不含它调用的其他方法；`--inclusive` 切换为统计该方法及其调用链下游的总耗时。两种排序在同一份数据上可能得出**完全相反**的结论——一个只做转发调用的薄封装方法，在 inclusive 排序下可能排到第一（因为它间接触发了大量下游耗时），而在 exclusive 排序下可能排不进前 20（因为它自身几乎不做计算）。判据取决于排查目标：**找热点代码本身**（哪个方法自己在烧 CPU）看 exclusive；**找耗时的调用路径**（从入口到问题代码经过了哪些层）看 inclusive。两者应配合使用而非二选一，单看一种排序可能误判问题所在层级。

## 4. 格式转换与查看

### 用途与前置条件

`.nettrace` 是 `dotnet-trace collect` 的原始输出格式，仅少数工具（如 PerfView、Visual Studio）能直接打开。`convert` 子命令把 `.nettrace` 转换为其他通用格式，供更广泛的可视化工具查看。

### 语法与关键开关

转换为 Speedscope 格式（浏览器端查看，适合快速查看火焰图）：
```
dotnet-trace convert trace.nettrace --format Speedscope
```

转换为 Chromium 格式（Chrome/Edge 的 `chrome://tracing` 或 Perfetto 查看）：
```
dotnet-trace convert trace.nettrace --format Chromium
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `--format <NetTrace\|Speedscope\|Chromium>` | 指定转换目标格式 | 默认 `NetTrace`（即不转换，等同于跳过本步骤） |

`Speedscope` 转换产物用浏览器打开 [speedscope.app](https://www.speedscope.app/) 并加载生成的 `.speedscope.json` 文件查看；`Chromium` 转换产物用 Chrome/Edge 的 `chrome://tracing` 或 [Perfetto UI](https://ui.perfetto.dev/) 加载生成的 `.chromium.json` 文件查看。

### 输出与产物位置

转换产物落在与源 `.nettrace` 相同目录，文件名在原名基础上追加对应格式后缀（如 `trace.speedscope.json`、`trace.chromium.json`）。

### 判据

**转换不可逆**：`Speedscope`、`Chromium` 两种目标格式为了适配各自查看器的数据模型，会丢失部分原始事件细节（如原始 provider/keyword 元数据），转换产物无法回推出完整的原始事件流。原始 `.nettrace` 文件**必须保留**，不能在转换后删除——一旦后续需要用不同的过滤条件或工具重新解读原始事件，只有 `.nettrace` 能提供完整数据，转换产物做不到。
