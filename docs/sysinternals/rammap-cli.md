# RAMMap — 命令行

**v1.63（2026-03-26）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/rammap
**GUI 篇：** [rammap-gui.md](rammap-gui.md)

> **官方页面对命令行参数完全无记载。** 下表提取自 `RAMMap64.exe` v1.63 二进制内嵌的 usage 资源（工具内 `Help → Usage` 弹出同一份）。
>
> **`-E` 系列是本目录中最有实用价值的「官方无文档」发现** —— 基准测试脚本可直接调用它重置内存状态。

## 语法

两套独立语法：

```
Usage: Rammap [[outputfile] | [[-run32] -o <inputfile.rmp>]]

Command line mode: Rammap -E[wsmt0]
```

## 参数表

### 采集/载入

| 参数 | 官方描述（原文译） | 说明 |
|---|---|---|
| `<outputfile>` | Has RAMMap dump scan output to a file and exit. | **位置参数**，采集后立即退出 |
| `-o <inputfile.rmp>` | Has RAMMap open the specified log file. | 载入已有快照 |
| `-run32` | Launch the 32-bit RAMMap on 64-bit Windows. | 与 `-o` 配合 |
| `-accepteula` | — | 二进制内有，抑制 EULA 弹窗 |

### Empty 系列（`-E` 命令行模式）

| 参数 | 官方描述（原文） | 作用 |
|---|---|---|
| `-Ew` | Empty Working Sets | 清空所有进程的工作集 |
| `-Es` | Empty System Working Sets | 清空系统（内核）工作集 |
| `-Em` | Empty Modified Page List | 把已修改页写回并释放 |
| `-Et` | Empty Standby List | **清空待命列表（即清空文件缓存）** |
| `-E0` | Empty Priority 0 standby List | 只清优先级 0 的待命页（较温和） |

`-E[wsmt0]` 的写法表示这些字母可组合，例如 `-Ewt`（同时清工作集与待命列表）。

## 唯一的合法用途：基准测试前重置

> **⚠ 这五项都是破坏性操作。** `-Et` 会清空文件缓存，导致后续文件访问全部落盘，产生持续的 I/O 峰值 —— **在生产环境执行可能引发服务超时**。

**正当场景只有一个：让每一轮基准测试从相同的冷缓存状态开始。**

不清空的话，第一轮把文件读进缓存，第二轮直接命中，结果快得离谱且不可比。

```powershell
# 基准测试脚本模板
1..5 | ForEach-Object {
  # 每轮前重置为冷缓存
  RAMMap64.exe -accepteula -Et
  Start-Sleep -Seconds 3        # 等 I/O 平息

  # 跑被测程序并计时
  $sw = [Diagnostics.Stopwatch]::StartNew()
  & "C:\app\benchmark.exe"
  $sw.Stop()

  [PSCustomObject]@{ Run = $_; Seconds = $sw.Elapsed.TotalSeconds }
} | Format-Table
```

**更彻底的重置**（工作集 + 待命列表 + 已修改页）：

```powershell
RAMMap64.exe -accepteula -Ewt
RAMMap64.exe -accepteula -Em
```

**用 `-E` 系列来「优化内存占用」是自欺欺人** —— 页会很快回来，而且中间付出了大量磁盘 I/O。Standby 列表本来就是随时可释放的，清空它只会让系统重新读盘。任何声称「清内存加速系统」的脚本都建立在错误前提上。

## 采集与快照对比

```powershell
# 采一次快照，落盘后退出
RAMMap64.exe -accepteula C:\trace\mem1.rmp

# 载入快照到 GUI
RAMMap64.exe -o C:\trace\mem1.rmp
```

### 定时采样追踪缓慢泄漏

排查几小时/几天的缓慢内存泄漏时，定时采集比盯实时视图有效：

```powershell
# 每 30 分钟采一次，共 48 次（24 小时）
1..48 | ForEach-Object {
  $ts = Get-Date -Format 'yyyyMMdd-HHmmss'
  RAMMap64.exe -accepteula "C:\trace\mem-$ts.rmp"
  Start-Sleep -Seconds 1800
}
```

**`.rmp` 是原生格式，只能用 RAMMap 本身打开** —— 官方 usage 未提供 CSV/XML 导出选项，所以无法直接脚本化 diff，必须逐个载入 GUI 对比。

如果需要可脚本化的内存趋势数据，用 PowerShell 原生计数器更实际：

```powershell
# 追踪非分页池（驱动泄漏的关键指标）
Get-Counter '\Memory\Pool Nonpaged Bytes','\Memory\Pool Paged Bytes',
            '\Memory\Standby Cache Normal Priority Bytes' `
  -SampleInterval 60 -MaxSamples 1440 |
  Export-Csv C:\trace\mem-trend.csv -NoTypeInformation
```

用 RAMMap 定性（哪一类内存/哪个文件在涨），用性能计数器定量（涨多快）。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 参数 |
|---|---|
| `File → Save`（`.rmp`） | `<outputfile>` 位置参数 |
| `File → Open` | `-o <inputfile.rmp>` |
| 在 64 位系统上跑 32 位版 | `-run32` |
| `Empty → Empty Working Sets` | `-Ew` |
| `Empty → Empty System Working Set` | `-Es` |
| `Empty → Empty Modified Page List` | `-Em` |
| `Empty → Empty Standby List` | `-Et` |
| `Empty → Empty Priority 0 Standby List` | `-E0` |
| 首次运行 EULA 弹窗 | `-accepteula` |
| 七个选项卡的交互浏览 | **无** |
| `File → Find`（`Ctrl+F`） | **无** |
| `F5` 刷新 | **无** → 重复调用 |
| CSV / XML 导出 | **无**（只有原生 `.rmp`） |

**五个 Empty 操作全都有 CLI 等价物** —— 这是 RAMMap 与 [VMMap](vmmap-cli.md) 的重要差别（VMMap 的 `Empty Working Set` 没有 CLI 开关）。

## 常见坑

1. **`<outputfile>` 是位置参数，不是 `-o`。** `-o` 是**载入**，位置参数是**输出** —— 写反会变成尝试打开不存在的文件。
2. **`-Et` 在生产环境可能引发服务超时。** 清空文件缓存后 I/O 峰值持续较长时间。
3. **`-E` 系列不能优化内存。** 页会很快回来。唯一正当用途是基准测试前重置。
4. **`.rmp` 只能用 RAMMap 打开。** 没有 CSV/XML 导出，无法脚本化 diff。需要可解析的趋势数据用性能计数器。
5. **需管理员权限。** 读物理内存信息与执行 Empty 都要提权，非提权运行会失败。
6. **`-E` 与采集是两套独立语法**，不要混写（`-Et` 不接受 outputfile 参数）。
7. **官方页面对 CLI 一字未提。** 参数只在 `Help → Usage` 里，升级后建议重新核对。
8. **架构后缀。** 用 `RAMMap64.exe`。`-run32` 只在需要用 32 位版载入旧快照时用。

## 分发

```
RAMMap.exe    743,488   x86      RAMMap64.exe   397,848   x64
```

`RAMMap.zip` 约 719 KB。Sysinternals Live：`https://live.sysinternals.com/RAMMap.exe`
winget 包名 `Microsoft.Sysinternals.RAMMap`。
支持范围：客户端 Windows Vista+，服务器 Windows Server 2008+。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/rammap（325 词，**对 CLI 与 Empty 完全无记载**）
- **工具自带：`Help → Usage`** —— 参数表的唯一权威来源

> **本篇事实边界：** 官方页面**不含任何命令行参数或 Empty 操作的说明**。两套语法、`-o` / `-run32` / `<outputfile>` 与五个 `-E` 开关及其官方英文描述均提取自 `RAMMap64.exe` v1.63 二进制 usage 资源。`-accepteula` 来自二进制字符串。基准测试模板、定时采样配方、性能计数器替代方案、`-E` 系列不能优化内存的判断为实践经验与内存管理原理总结。`-E[wsmt0]` 可组合的推断依据是官方 usage 的方括号写法，未逐一实测每种组合。
