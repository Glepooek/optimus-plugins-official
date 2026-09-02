# VMMap — 命令行

**v3.4（2023-10-18，维护停滞）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/vmmap
**GUI 篇：** [vmmap-gui.md](vmmap-gui.md)（主体在此）

> **官方页面只说「提供命令行选项以支持脚本化场景」，不列出任何参数名。** 下表提取自 `vmmap64.exe` v3.4 二进制内嵌的 usage 资源（工具内 `Help → Command-line Options` 弹出同一份）。

## 语法

```
vmmap [-64] [-p <pid or process name> [outputfile]] | [-o <inputfile>]
```

## 参数表

| 参数 | 官方描述（原文译） | 说明 |
|---|---|---|
| `-p <pid 或进程名>` | Specifies process VMMap will scan on startup | 可用 PID 或进程名 |
| `<outputfile>` | Has VMMap dump scan output to file and exit | **位置参数**，跟在 `-p` 目标之后 |
| `-o <inputfile>` | Has VMMap load the specified file on startup | 载入已有快照 |
| `-64` | Run the 64-bit version to analyze a 32-bit process | 在 64 位系统上分析 32 位进程 |
| `-accepteula` | — | 二进制内有，抑制 EULA 弹窗 |

## 输出格式由扩展名决定

官方 usage 原文：

> The output file will be created as a native VMMap .mmp file unless you specify .xml or .csv as the file extension, which will save as XML or CSV respectively.

| 扩展名 | 格式 | 用途 |
|---|---|---|
| `.mmp`（或其他） | **原生格式（默认）** | 可用 `-o` 重新载入 VMMap 完整分析 |
| `.xml` | XML | 结构化解析 |
| `.csv` | CSV | Excel / 脚本对比 |

**做时序对比时存 `.csv`，做完整留档存 `.mmp`。**

## 实用配方

```powershell
# 采一次快照，落盘后自动退出（原生格式）
vmmap64.exe -accepteula -p YourApp.exe C:\trace\snap1.mmp

# 按 PID
vmmap64.exe -accepteula -p 4728 C:\trace\snap1.mmp

# 存 CSV 供脚本分析
vmmap64.exe -accepteula -p YourApp.exe C:\trace\snap1.csv

# 载入已有快照到 GUI
vmmap64.exe -o C:\trace\snap1.mmp

# 在 64 位系统上分析 32 位进程
vmmap64.exe -accepteula -64 -p Legacy32.exe C:\trace\snap32.mmp
```

### 定时采样做泄漏趋势

VMMap 没有内建的定时采集开关（`-p <目标> <文件>` 是采一次就退出），需要外层循环：

```powershell
# 每 5 分钟采一次，共 12 次（1 小时）
1..12 | ForEach-Object {
  $ts = Get-Date -Format 'yyyyMMdd-HHmmss'
  vmmap64.exe -accepteula -p YourApp.exe "C:\trace\vm-$ts.csv"
  Start-Sleep -Seconds 300
}
```

然后提取各快照的类型汇总行做趋势对比：

```powershell
# 抽取每个快照的 Heap 行，看是否单调增长
Get-ChildItem C:\trace\vm-*.csv | ForEach-Object {
  $heap = Import-Csv $_ | Where-Object { $_.Type -eq 'Heap' }
  [PSCustomObject]@{
    File      = $_.Name
    Committed = $heap.Committed
    Private   = $heap.Private
  }
} | Format-Table
```

**CSV 的实际列名需以你这台机器上 v3.4 的输出为准** —— 官方未记载 CSV 列结构，先跑一次看表头再写解析脚本。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 参数 |
|---|---|
| `File → Select Process` 附加到进程 | `-p <pid 或进程名>` |
| `File → Save`（原生 `.mmp`） | `-p <目标> <file.mmp>` |
| `File → Save As` 选 XML | `-p <目标> <file.xml>` |
| `File → Save As` 选 CSV | `-p <目标> <file.csv>` |
| `File → Open` 载入快照 | `-o <inputfile>` |
| 分析 32 位进程 | `-64` |
| 首次运行 EULA 弹窗 | `-accepteula` |
| **instrumented 启动模式**（跟踪每次分配及调用栈） | **无** |
| `View → Fragmentation View` | **无** |
| `View → Strings` | **无** |
| `Tools → Empty Working Set` | **无** |
| `Options → Trace Snapshot Interval` | **无** |
| `Options → Configure Symbols` | **无** |
| `View → Refresh` 反复刷新 | **无** → 外层循环重复调用 |

**CLI 是「采快照并退出」的一次性工具**，没有交互分析能力。VMMap 最强的 instrumented 分配跟踪（能看到分配调用栈）**只有 GUI 有** —— 需要它就必须从 GUI 启动应用，见 [GUI 篇](vmmap-gui.md#选择进程)。

## 常见坑

1. **`<outputfile>` 是位置参数，不是 `-o`。** `-o` 是**载入**，位置参数是**输出** —— 写反会变成尝试打开一个不存在的文件。
2. **给了输出文件就会立刻退出。** 想留在 GUI 里分析就不要给输出文件参数。
3. **输出格式靠扩展名推断。** 想要 CSV 就得把文件名写成 `.csv`，没有单独的格式开关。
4. **没有定时采集开关。** 趋势采样要靠外层脚本循环。
5. **CSV 列结构官方无记载。** 写解析脚本前先跑一次看表头。
6. **`-p` 用进程名时若有多个同名实例**，行为未文档化（可能取第一个）。多实例场景用 PID。
7. **需管理员权限才能分析其他用户/系统进程。**
8. **instrumented 模式无 CLI 等价物。** 脚本化只能拿到快照，拿不到分配调用栈。
9. **维护停滞（2023-10-18）。**

## 分发

```
vmmap.exe      5,193,152   x86      vmmap64.exe   2,758,064   x64
```

winget 包名 `Microsoft.Sysinternals.VMMap`。
运行环境：客户端 Windows 10+，服务器 Windows Server 2016+。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/vmmap（只说「提供命令行选项」，不列参数）
- **工具自带：`Help → Command-line Options`** —— 参数表的唯一权威来源

> **本篇事实边界：** 官方页面**不列出任何参数名**。语法、`-p` / `-o` / `-64` 的描述、输出格式由扩展名决定的规则均提取自 `vmmap64.exe` v3.4 二进制 usage 资源。`-accepteula` 来自二进制字符串。定时采样配方、CSV 解析注意事项为实践经验总结（CSV 列结构官方无记载，本篇未编造列名）。
