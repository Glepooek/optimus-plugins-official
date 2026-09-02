# ProcDump

**v12.01（2026-07-09）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/procdump

> **纯 CLI 工具，无 GUI。** [Process Explorer](process-explorer-gui.md) 的 `Process → Create Dump` 可交互式抓 dump，但没有阈值触发与无人值守能力。
>
> **来源说明：** 官方页面覆盖了转储类型与主要触发条件。**`-mac`（压缩）、`-cp`（压缩线程数）、`-a`/`-at`（避免中断）、`-f`/`-fx`（内容过滤）、`-dc`（注释）、`-wer`、`-x`、`-k`、`-b`、`-o`、`-l`、`-m`/`-ml` 等开关来自 `procdump64.exe` v12.01 二进制内嵌 usage**，部分官方页面未记载。

## 定位与边界

命令行 dump 捕获工具。官方定位：监控应用的 CPU 峰值并在峰值期间生成崩溃转储；同时支持挂起窗口监控、未处理异常监控、基于系统性能计数器阈值触发，也可作为通用 dump 工具嵌入脚本。

**核心价值是「无人值守 + 条件触发」** —— 问题几小时才复现一次、复现时你不在场，这是唯一可行的抓现场手段。

| 需求 | ProcDump 是否合适 |
|---|---|
| CPU 峰值瞬时出现、抓不到现场 | ✅ `-c` 阈值 + `-s` 持续秒数 |
| 内存增长到某阈值时抓 dump | ✅ `-m` |
| 程序崩溃时自动抓 | ✅ `-e`，或 `-i` 注册为系统事后调试器 |
| 程序卡死（窗口无响应） | ✅ `-h` |
| 交互式抓一次 dump | ⚠️ [Process Explorer](process-explorer-gui.md) 更快 |
| 分析 dump 内容 | ❌ 用 WinDbg / Visual Studio |
| 持续监控（不抓 dump） | ❌ 用 [Sysmon](sysmon.md) 或性能计数器 |

运行环境：客户端 Windows 11+，服务器 Windows Server 2016+（**是本目录中要求最高的工具**）。

## 语法

官方 usage 三套独立语法：

```
Capture Usage:
   procdump.exe [-mm] [-ma] [-mt] [-mp] [-mc <Mask>] [-md <Callback_DLL>] [-mk]
                [-n <Count>] [-s <Seconds>]
                [-c|-cl <CPU_Usage> [-u]] [-cp <Workers>]
                [-m|-ml <Commit_Usage>]
                [-p|-pl <Counter> <Threshold>]
                [-h]
                [-e [1] [-g] [-b] [-ld] [-ud] [-ct] [-et]]
                [-l] [-t]
                [-f <Include_Filter>, ...] [-fx <Exclude_Filter>, ...]
                [-dc <Comment>] [-o]
                [-r [1..5] [-a]] [-at <Timeout>]
                [-pt] [-wer] [-64]
                {
                 {{[-w] <Process_Name> | <Service_Name> | <PID>} [<Dump_File> | <Dump_Folder>]}
                | {-x <Dump_Folder> <Image_File> [Argument, ...]}
                }

Install Usage:
   procdump.exe -i [Dump_Folder] [-mm] [-ma] [-mac] [-mt] [-mp]
                [-mc <Mask>] [-md <Callback_DLL>] [-mk] [-r] [-k]

Uninstall Usage:
   procdump.exe -u
```

**目标可以是进程名、服务名或 PID** —— 支持服务名是容易被忽略的便利特性。

## 转储类型

| 开关 | 类型 | 说明 |
|---|---|---|
| `-mm` | **Mini（默认）** | 最小 |
| `-ma` | **Full** | 含全部内存。**分析内存问题必须用这个** |
| `-mac` | Full + 压缩 | 官方网页未记载。含内存压缩，体积小但 CPU 开销高 |
| `-mt` | Triage | 仅直接引用内存与有限元数据。**尝试但不保证移除敏感信息** |
| `-mp` | MiniPlus | 排除最大的超过 512MB 私有内存区，体积为 Full 的 10%-75%。**CLR 进程因调试限制仍按 `-ma` 转储** |
| `-mc <Mask>` | Custom | 自定义 `MINIDUMP_TYPE` 掩码 |
| `-md <DLL>` | Callback | 回调 DLL |
| `-mk` | 额外写内核转储 | 含线程内核栈。**使用克隆（`-r`）时操作系统不支持 `-mk`** |
| `-pt` | 追加进程树流 | v12.0（2026-05-07）新增 |

**`-mt` 的「尝试但不保证移除敏感信息」是官方原话** —— 不要把它当作脱敏手段。给第三方 dump 前仍需自行评估。

`-cp <Workers>` 控制压缩线程数（1..核数），官方 usage 说明 OS 默认/推荐值为 4。

## 触发条件

| 开关 | 触发时机 |
|---|---|
| `-c <CPU%>` | CPU **超过**阈值 |
| `-cl <CPU%>` | CPU **低于**阈值 |
| `-u` | 使 CPU 使用率**按单核相对计算**（配合 `-c`） |
| `-s <秒>` | **触发前连续满足条件的秒数（默认 10 秒）** |
| `-m <MB>` | 内存提交量**达到**阈值 |
| `-ml <MB>` | 内存提交量**低于**阈值 |
| `-h` | 进程窗口**至少 5 秒**不响应窗口消息（与任务管理器相同的挂起判定） |
| `-t` | 进程**终止**时 |
| `-e` | **未处理异常**时 |
| `-e 1` | **首次异常**（first chance）时 |
| `-p <Counter> <Threshold>` | 性能计数器**达到或超过**阈值 |
| `-pl <Counter> <Threshold>` | 性能计数器**低于**阈值 |
| `-ld` / `-ud` | DLL **加载 / 卸载**时（配合 `-e`） |
| `-ct` / `-et` | 线程**创建 / 退出**时（配合 `-e`） |
| `-b` | 把调试断点当作异常处理（否则忽略） |
| `-n <Count>` | 退出前写多少个 dump |

**`-s` 默认 10 秒是关键默认值** —— CPU 必须**连续** 10 秒超阈值才触发。抓瞬时尖峰要显式调小（如 `-s 2`），否则永远触发不了。

**`-u` 的语义容易混淆：** 不加时 `-c 50` 指「总 CPU 的 50%」（8 核机器上单线程满载只有 12.5%）；加 `-u` 后按单核相对计算，单线程满载就是 100%。**抓单线程死循环必须加 `-u`。**

## 内容过滤（官方网页未记载）

| 开关 | 说明 |
|---|---|
| `-f <Include_Filter>` | 按内容**包含**过滤：异常内容、调试日志、DLL 加载/卸载的文件名 |
| `-fx <Exclude_Filter>` | 按内容**排除**过滤（同上维度） |
| `-l` | 显示进程的调试日志输出 |
| `-dc <Comment>` | 把指定字符串加入生成的 Dump Comment |

**`-f` 是抓特定异常的关键** —— 程序不停抛无害异常时，`-e` 会抓出一堆无用 dump，用 `-f` 只保留你关心的那类。

```powershell
# 只在抛出包含 "OutOfMemory" 的异常时抓 dump
procdump64.exe -accepteula -e -f OutOfMemory -ma YourApp.exe C:\dumps\

# 排除已知无害的异常
procdump64.exe -accepteula -e -fx "COMException" -ma YourApp.exe C:\dumps\
```

`-dc` 在批量抓取时很有用 —— 把触发原因写进 dump，事后在 WinDbg 里能看到。

## 克隆与避免中断（官方网页未记载）

| 开关 | 说明 |
|---|---|
| `-r [1..5]` | **用克隆（clone）方式转储。** 并发上限可选（默认 1，最大 5） |
| `-a` | **避免中断（Avoid outage）。需要 `-r`。** 若触发会导致目标挂起时间过长则取消 |
| `-at <Timeout>` | 在 N 秒时取消触发的收集 |
| `-k` | 克隆后（`-r`）或 dump 收集结束时**终止进程** |

**`-r` 是生产环境抓大 dump 的正确做法。** 常规 `-ma` 会挂起目标进程直到内存写完 —— 8GB 进程可能挂起十几秒，足以让服务超时。克隆方式先快速复制进程状态再从副本写 dump，大幅缩短挂起时间。

**`-a` 是进一步的保险**：预判挂起时间过长就直接放弃这次触发，宁可不抓也不影响服务。

> **注意：** 使用克隆（`-r`）时操作系统不支持 `-mk`（内核转储）。

## 注册为事后调试器（AeDebug）

```powershell
# 注册：任何进程崩溃都自动抓 Full dump 到 c:\dumps
procdump64.exe -ma -i c:\dumps

# 卸载
procdump64.exe -u
```

官方给出的示例即 `procdump -ma -i c:\dumps`。

**这是「崩溃了但没人在场」的标准解法**，比让用户手工操作可靠。注意：

- 会影响**全系统**所有崩溃进程，不只你关心的那个
- `-ma` 全内存 dump 在大进程崩溃时可能写出几 GB
- Install 模式额外支持 `-mac`（压缩）、`-r`（克隆）、`-k`（结束后终止）
- `-wer` 可把（最大的）dump 排入 Windows Error Reporting 队列

## 启动并监控（`-x`）

```
procdump.exe -x <Dump_Folder> <Image_File> [Argument, ...]
```

**用于监控「启动即崩溃」的程序** —— 常规用法需要进程已在运行，`-x` 由 ProcDump 启动它，从第一条指令就开始监控。

`-w` 则是「等待指定进程启动」（进程尚未运行时）：

```powershell
# 等 YourApp 启动，然后监控 CPU
procdump64.exe -accepteula -w YourApp.exe -c 80 -u -s 3 -ma C:\dumps\
```

## 实用配方

```powershell
# CPU 持续 3 秒超单核 90% → 抓 Full dump（抓单线程死循环）
procdump64.exe -accepteula -c 90 -u -s 3 -ma YourApp.exe C:\dumps\

# 内存提交超 2GB → 抓 dump（内存泄漏取证）
procdump64.exe -accepteula -m 2048 -ma YourApp.exe C:\dumps\

# 窗口卡死 → 抓 dump（UI 无响应）
procdump64.exe -accepteula -h -ma YourApp.exe C:\dumps\

# 未处理异常 → 抓 3 个 dump 后退出
procdump64.exe -accepteula -e -n 3 -ma YourApp.exe C:\dumps\

# 进程退出时抓 dump（排查非预期退出）
procdump64.exe -accepteula -t -ma YourApp.exe C:\dumps\

# 生产环境：克隆方式抓大 dump，挂起时间过长则放弃
procdump64.exe -accepteula -c 90 -u -s 5 -ma -r 2 -a YourApp.exe C:\dumps\

# 按服务名抓（不必先查 PID）
procdump64.exe -accepteula -ma "W32Time" C:\dumps\

# 性能计数器触发
procdump64.exe -accepteula -p "\Process(YourApp)\Handle Count" 5000 -ma YourApp.exe C:\dumps\

# 立即抓一个（通用 dump 工具用法）
procdump64.exe -accepteula -ma 4728 C:\dumps\snap.dmp
```

## 64 位差异

**在 64 位 Windows 上 ProcDump 默认对 32 位进程生成 32 位转储**，`-64` 可强制生成 64 位转储。官方明确该选项**仅应用于 WOW64 子系统调试**。

分析 32 位进程的 dump 时，调试器位数要与 dump 位数匹配 —— 位数不匹配是「dump 打开后栈全是乱码」的常见原因。

## 常见坑

1. **`-s` 默认 10 秒。** CPU 必须连续 10 秒超阈值才触发，抓瞬时尖峰要显式调小。
2. **`-c` 不加 `-u` 时按总 CPU 计算。** 8 核机器上单线程满载只有 12.5%，`-c 50` 永远不触发。抓单线程死循环必须加 `-u`。
3. **`-ma` 会挂起目标进程直到写完。** 大进程可能挂起十几秒导致服务超时。生产环境用 `-r`（克隆）+ `-a`（避免中断）。
4. **`-r` 与 `-mk` 不兼容。** 用克隆时操作系统不支持内核转储。
5. **`-mt` 的脱敏不保证。** 官方原话是「尝试但不保证移除敏感信息」，不要当作脱敏手段。
6. **`-mp` 对 CLR 进程无效。** 因调试限制仍按 `-ma` 全内存转储。
7. **`-i` 影响全系统。** 注册为 AeDebug 后所有崩溃进程都会被抓，配 `-ma` 可能写出大量数据。用完记得 `-u` 卸载。
8. **dump 含敏感信息。** 官方 EULA 明确警示可能包含用户名、密码、文件与注册表路径。外发前评估。
9. **`-e` 不加 `-f` 可能抓出一堆无用 dump。** 程序不停抛无害异常时用 `-f` 过滤。
10. **运行环境要求高（Windows 11+ / Server 2016+）。** 老系统上用旧版 ProcDump。
11. **`-x` 与 `-w` 语义不同。** `-x` 由 ProcDump 启动程序，`-w` 等待程序自行启动。
12. **无独立 winget 包。** `procdump.exe` 只作为 Suite zip 内的嵌套文件分发 —— **不能写 `winget install Microsoft.Sysinternals.ProcDump`**。

## 分发

**没有独立的 winget 包。** procdump 只在 Sysinternals Suite 内分发。

```
procdump.exe   1,370,432   x86      procdump64.exe   741,216   x64
（ARM64 为 procdump64a.exe）
```

独立下载包 1.2 MB。另有 ProcDump for Linux 与 ProcDump for Mac 的 GitHub 版本（参数不完全通用）。
运行环境：客户端 Windows 11+，服务器 Windows Server 2016+。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/procdump（Published 2026-07-09）
- **工具自带：`procdump.exe /?`** 输出完整三套语法
- ProcDump for Linux：https://github.com/microsoft/ProcDump-for-Linux

> **本篇事实边界：** 七种转储类型（`-mm`/`-ma`/`-mt`/`-mp`/`-mc`/`-md`/`-mk`）及其体积/限制说明、主要触发条件（`-c`/`-u`/`-s`/`-h`/`-t`/`-e`/`-p`/`-pl`/`-n`/`-ld`/`-ud`/`-ct`/`-et`）、`-i` AeDebug 注册、`-64` 与 WOW64 限制、无独立 winget 包均来自官方页面与调研素材。**`-mac`、`-cp`、`-a`、`-at`、`-f`、`-fx`、`-dc`、`-o`、`-l`、`-b`、`-k`、`-r`、`-w`、`-x`、`-wer`、`-m`/`-ml`、`-pt` 提取自 `procdump64.exe` v12.01 二进制内嵌 usage**，官方页面未完整记载（`-pt` 的 v12.0 新增时间来自官方索引页 What's New）。`-u` 的单核语义解释、`-r` 缩短挂起时间的机理、位数匹配的调试建议、各配方为实践经验总结。
