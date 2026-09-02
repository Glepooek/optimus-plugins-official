# Process Monitor — 命令行

**v4.1（2026-08-19）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/procmon
**GUI 篇：** [procmon-gui.md](procmon-gui.md) · **工具定位与事件类别：** 见 GUI 篇「定位与边界」

> **来源说明：** 官方页面 `learn.microsoft.com/en-us/sysinternals/downloads/procmon` 全文仅 396 词，**不包含任何命令行开关文档**。本篇开关表提取自 `Procmon64.exe` v4.1 二进制内嵌的 Usage 对话框资源（`Process Monitor Usage` / `Command line arguments:`），描述为原文英文的中文对译，保留原始开关拼写与参数占位符。工具内 `Help → Command Line Options` 可弹出同一份表。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 开关 |
|---|---|
| `File → Capture Events` 取消勾选 | `/NoConnect` |
| `File → Open` | `/OpenLog <PML>` |
| `File → Backing Files`，文件模式 | `/BackingFile <PML>` |
| `File → Backing Files`，虚拟内存模式 | `/PagingFile` |
| `Filter → Reset Filter`（`Ctrl+R`）| `/NoFilter`（语义不同，见下注） |
| `Filter → Load Filter`（`.pmc`）| `/LoadConfig <file>` |
| `File → Save`，`All events` | `/SaveAs <path>` |
| `File → Save`，勾 `Include stack traces` | `/SaveAs1 <path>`（仅 XML） |
| `File → Save`，勾 `Resolve stack symbols` | `/SaveAs2 <path>`（仅 XML） |
| `File → Save`，`Events displayed using current filter` | `/SaveApplyFilter` |
| `Options → Enable Boot Logging` | `/EnableBootLogging` |
| （重启后 Procmon 自动提示转换）| `/ConvertBootLog <PML>` |
| `Options → Profiling Events` | `/Profiling` |
| **无 GUI 等价物** | `/RingBuffer` `/RingBufferSize` `/RingBufferLen` `/Runtime` `/Terminate` `/WaitForIdle` `/Quiet` `/Minimized` `/AcceptEula` `/Run32` `/Altitude` |

**`/NoFilter` 与 `Ctrl+R` 语义不同：** `/NoFilter` 清空过滤器（`Clear the filter at start up`），`Ctrl+R` 是恢复**默认**过滤器（保留系统降噪规则）。要真正全清，GUI 侧只能在过滤器对话框逐条 Remove。

**Ring buffer 与定时采集没有 GUI 入口** —— 这是 CLI 独有能力，也是本篇最值得看的部分。

## 完整开关表

| 开关 | 参数 | 官方描述（原文） | 说明 |
|---|---|---|---|
| `/OpenLog` | `<PML file>` | Open a previously saved event file | 载入已有 PML 分析，不启动新采集 |
| `/BackingFile` | `<PML file>` | Save events in the specified backing file | **长时间采集必用** |
| `/PagingFile` | — | Save events in the virtual memory | 默认行为，受系统提交限制约束 |
| `/NoConnect` | — | Don't automatically begin collecting events at start up | 启动但不采集，用于先配过滤器 |
| `/NoFilter` | — | Clear the filter at start up | 清空上次退出时保留的过滤器 |
| `/AcceptEula` | — | Accept the EULA automatically (don't show a dialog) | 脚本化必用 |
| `/Quiet` | — | Don't confirm filter settings during start up | 抑制「上次的过滤器仍生效」确认框 |
| `/Minimized` | — | Start the application minimized | |
| `/Terminate` | — | Terminate all instances of ProcMon and exit | 停止采集的标准手段 |
| `/Runtime` | `<秒>` | Run for the specified number of seconds and terminate | 定时采集，自动退出 |
| `/WaitForIdle` | — | Wait for an instance of ProcMon to become ready | 脚本中等待前一实例就绪，避免竞态 |
| `/Profiling` | — | Enable the thread profiling feature | 线程采样，间隔在 GUI 的 Profiling Events 中设定（1 秒 / 100 毫秒） |
| `/Run32` | — | Run the 32-bit version to load 32-bit log files (x64 only) | 加载 32 位机采集的 PML |
| `/SaveAs` | `<path>` | Export to an XML, CSV or PML file | 格式由扩展名决定，**不含堆栈** |
| `/SaveAs1` | `<path>` | Export including stack traces (**XML only**) | 含堆栈，仅 XML |
| `/SaveAs2` | `<path>` | Export including stack traces with symbols (**XML only**) | 含堆栈**与符号**，仅 XML，很慢 |
| `/SaveApplyFilter` | — | Apply current filter before exporting | 不加则导出全量 |
| `/LoadConfig` | `<file>` | Load a previously saved configuration file | 载入 PMC（过滤器 + 列 + 高亮） |
| `/EnableBootLogging` | — | Configures logging of next boot | **只生效一次**，需重启 |
| `/ConvertBootLog` | `<PML file>` | Automatically processes a boot log after reboot | 重启后自动转换 boot 日志 |
| `/RingBuffer` | — | Enable flight recorder mode | **官方网页完全未记载** |
| `/RingBufferSize` | `<MB>` | Ring buffer size in MB | |
| `/RingBufferLen` | `<分钟>` | Ring buffer length in minutes | |
| `/HookRegistry` | — | Hook Registry for Softgrid troubleshooting (**x86 Vista only**) | 已无实际用途 |
| `/Altitude` | `<altitude>` | Driver numeric altitude | 与其他过滤驱动冲突时调整 |

## Ring buffer（flight recorder 模式）

`/RingBuffer` 让 Procmon 只保留最近一段时间/一定体积的事件，滚动覆盖旧数据。这是**捕获间歇性问题的正确姿势**：问题几小时才复现一次，全量采集会写出几十 GB，而 ring buffer 恒定占用。

```powershell
# 常驻后台，只保留最近 512 MB
procmon64.exe /AcceptEula /Quiet /Minimized /RingBuffer /RingBufferSize 512 /BackingFile C:\trace\ring.pml

# 只保留最近 30 分钟
procmon64.exe /AcceptEula /Quiet /Minimized /RingBuffer /RingBufferLen 30 /BackingFile C:\trace\ring.pml

# 问题复现后立刻停止
procmon64.exe /Terminate
```

`/RingBufferSize` 与 `/RingBufferLen` 同时给出时哪个优先，官方无文档、二进制帮助也未说明——建议只用其中一个。

## 无人值守采集配方

```powershell
# 定时 5 分钟采集，落盘后自动退出并导出 CSV
procmon64.exe /AcceptEula /Quiet /Minimized `
  /BackingFile C:\trace\cap.pml /Runtime 300
procmon64.exe /OpenLog C:\trace\cap.pml /SaveAs C:\trace\cap.csv /SaveApplyFilter

# 用预置配置采集（过滤器已在 PMC 中定义，避免采集全量）
procmon64.exe /AcceptEula /Quiet /Minimized `
  /LoadConfig C:\trace\myfilter.pmc /BackingFile C:\trace\cap.pml

# 脚本中串联多个实例时避免竞态
procmon64.exe /Terminate
procmon64.exe /AcceptEula /WaitForIdle /BackingFile C:\trace\next.pml

# 导出带符号的堆栈（仅 XML，很慢）
procmon64.exe /OpenLog C:\trace\cap.pml /SaveAs2 C:\trace\stacks.xml
```

**`/BackingFile` 不给则事件存在虚拟内存中**，长时间采集会耗尽内存后崩溃。任何超过几分钟的采集都应显式指定后备文件。

**PMC 是无人值守采集的正确做法。** 在 GUI 里配好过滤器 → `Filter → Save Filter` 存为 `.pmc` → 脚本中用 `/LoadConfig` 载入。这比在命令行拼过滤条件可靠（Procmon 没有命令行设过滤器的开关）。

## Boot logging

**抓取与分析不在同一次会话内完成。**

```powershell
# 1. 配置下次启动记录（需管理员权限）
procmon64.exe /AcceptEula /EnableBootLogging

# 2. 重启
Restart-Computer

# 3. 重启后转换 boot 日志
procmon64.exe /AcceptEula /ConvertBootLog C:\trace\boot.pml
```

- **`/EnableBootLogging` 只生效一次**，不是持久设置。
- 启动期事件量极大，务必预置窄过滤器（`/LoadConfig`）或在 GUI 启用 Drop Filtered Events。
- Boot 日志的中间文件由驱动写在系统盘上（官方未记载确切路径与文件名）。不去转换会一直占磁盘。
- Boot logging 期间系统启动明显变慢。

## 架构与分发

官方包 `ProcessMonitor.zip`（2.9 MB）解压后：

```
Eula.txt
Procmon.exe      4,247,832   x86
Procmon64.exe    2,232,136   x64
Procmon64a.exe   2,316,576   ARM64
```

Sysinternals Live：`https://live.sysinternals.com/Procmon.exe`
运行环境：客户端 Windows 10+，服务器 Windows Server 2012+。

winget 安装后通过 PortableCommandAlias 统一映射为无后缀的 `procmon` 命令，掩盖了架构差异；手工解压使用时要自己选对。加载 32 位机采集的 PML 需 `/Run32`。

## CLI 侧常见坑

1. **`/BackingFile` 不给会耗尽内存。** 默认走虚拟内存，受系统提交限制约束。
2. **`/SaveAs` 默认导出全量**，要应用过滤器必须显式加 `/SaveApplyFilter`。
3. **带符号的堆栈只能导出 XML。** CSV/PML 导出不含堆栈——自动化管道若按惯性选 CSV，会静默丢掉最有价值的根因信息且不报错。
4. **没有命令行设过滤器的开关。** 只能通过 `/LoadConfig` 载入预先在 GUI 里存好的 PMC。
5. **`/Quiet` 抑制的是确认框，不是过滤器本身。** 上次退出时的过滤器仍然生效，要清空得加 `/NoFilter`。
6. **`/EnableBootLogging` 只生效一次。**
7. **PML 含敏感信息。** 官方 EULA 明确警示可能包含用户名、密码、访问过的文件与注册表路径。外发前脱敏。
8. **与其他过滤驱动冲突时用 `/Altitude`。** Procmon 是文件系统 minifilter，和 AV/EDR 抢同一条驱动栈。症状通常是启动失败或某类事件完全捕获不到（被更高 altitude 的安全驱动挡在下游）——这个诊断方向官方文档没有任何提示。

## 日志体积控制

官方声明日志架构可扩展到「数千万条事件与数 GB 日志数据」——这是能力上限，不是建议值。

| 手段 | 效果 | 代价 |
|---|---|---|
| `/BackingFile` | 落盘而非占内存 | 磁盘 I/O，需预留空间 |
| `/RingBuffer` + Size/Len | 恒定占用，滚动覆盖 | 只保留最近窗口 |
| `/Runtime <秒>` | 限定采集时长 | 需预判问题复现时间 |
| `/LoadConfig` 预置窄过滤器 + GUI 侧 Drop Filtered Events | 真正减少采集量 | 不可逆，丢弃的事件无法恢复 |

**经验量级：** 一台空闲的桌面系统，不设过滤器全类别采集，PML 增长约每分钟数十至上百 MB；有活跃编译或大量文件 I/O 时可达每分钟 GB 级。做长时间采集前先跑 1 分钟测增速。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/procmon
- Linux 版（参数不通用）：https://github.com/microsoft/ProcMon-for-Linux
- 文档源文件：https://github.com/MicrosoftDocs/sysinternals/blob/live/sysinternals/downloads/procmon.md
- **工具自带：`Help → Command Line Options`**

> **本篇事实边界：** 开关表提取自 `Procmon64.exe` v4.1 二进制资源，官方网页无记载（`/RingBuffer` 系列在任何官方网页上都查不到）。日志增速量级、采集配方为实践经验总结。
