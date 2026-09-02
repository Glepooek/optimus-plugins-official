# Handle

**v5.0（2022-10-26，维护停滞）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/handle

> **纯 CLI 工具，无 GUI。** 图形化对等物是 [Process Explorer](process-explorer-gui.md) 的 Find Handle（`Ctrl+Shift+F`）。
>
> **维护状态：** v5.0 发布于 2022-10-26，是本目录中停滞最久的工具之一。官方索引页 What's New 时间线（2026-03 至 2026-08）中无 Handle 更新条目。

## 定位与边界

查看进程打开的句柄，以及**哪个进程持有某个文件/对象的句柄**。

| 需求 | Handle 是否合适 |
|---|---|
| 「文件被谁锁定了」（脚本化/批量） | ✅ 正是设计目标 |
| 「文件被谁锁定了」（交互式一次性） | ⚠️ [Process Explorer](process-explorer-gui.md) 的 Find Handle 更直观 |
| 句柄泄漏的时序对比 | ✅ `-s` + CSV 导出，比肉眼盯 GUI 可靠 |
| 强制关闭某个句柄 | ✅ `-c`，但有风险（见下） |
| 看句柄的对象类型分布 | ✅ `-s` |
| 交互式浏览某进程的全部句柄 | ❌ 用 Process Explorer 下窗格 |

## 前提：必须管理员权限

**官方文档明确把管理员权限列为运行前提。** 非提权运行时症状通常是输出为空或只看到自己的进程，而非明确报错。

## 语法

官方 usage 原文：

```
handle [[-a [-l]] [-v|-vt] [-u] | [-c <handle> [-y]] | [-s]]
       [-p <process>|<pid>] [name] [-nobanner]
```

## 参数表（官方 usage 原文译）

| 参数 | 官方描述（译） |
|---|---|
| `-a` | 转储**所有**句柄信息 |
| `-l` | 只显示由页面文件支持的 section 句柄 |
| `-c <handle>` | 关闭指定句柄（**按十六进制解析**） |
| `-y` | 关闭句柄时不提示确认 |
| `-g` | 打印已授予的访问权限（granted access） |
| `-s` | 打印**每种类型**已打开句柄的计数 |
| `-u` | 搜索句柄时显示所属用户名 |
| `-v` | CSV 输出（逗号分隔） |
| `-vt` | CSV 输出（制表符分隔） |
| `-p <process 或 pid>` | 只转储属于该进程的句柄（**接受部分名称**） |
| `name` | 位置参数，按名称片段搜索 |
| `-nobanner` | 不显示启动横幅与版权信息 |
| `-accepteula` | 抑制 EULA 弹窗 |

## 关键坑：默认只列出文件句柄

**Handle 默认只列出指向「打开文件」的句柄。** 要覆盖端口、注册表键、同步原语（Mutant/Event/Semaphore）、线程、进程等其他对象类型，**必须显式加 `-a`**。

```powershell
# ❌ 查互斥体，什么都看不到（默认只看文件）
handle64.exe YourAppMutex

# ✅ 正确
handle64.exe -a YourAppMutex
```

排查「程序说已有实例在运行」这类问题时（通常是命名互斥体），不加 `-a` 会白忙。

## 路径匹配语义

把名字片段作为**位置参数**传入。官方明确匹配规则为：

- **大小写不敏感**
- **路径子串匹配**
- **可出现在路径的任意位置**

```powershell
# 全都有效
handle64.exe locked.db
handle64.exe "windows\system"
handle64.exe C:\data\
```

不必写完整路径。这是 Process Explorer 图形化句柄搜索的命令行对等物（PE 对话框标签原文也是 `Handle or DLL substring:`）。

## 定位「文件被谁锁定」

```powershell
# 基础用法
handle64.exe -accepteula -nobanner locked.db

# 输出形态：
# YourApp.exe        pid: 4728   type: File          2A4: C:\data\locked.db
# backup.exe         pid: 5512   type: File          1B0: C:\data\locked.db
#                                                    ↑ 句柄值（十六进制）

# 带用户名（多用户/服务场景需要）
handle64.exe -a -u locked.db

# 带授予的访问权限（判断是读锁还是写锁）
handle64.exe -a -g locked.db
```

**`-g` 是判断锁类型的关键** —— 持有者只请求了读权限，和请求了 `Delete`/`Write` 是不同的问题。

## 强制关闭句柄

```powershell
# 必须同时指定 PID 与句柄值（十六进制）
handle64.exe -c 2A4 -p 4728

# 跳过确认（脚本化）
handle64.exe -c 2A4 -p 4728 -y
```

**`-c` 必须配合 `-p` 指定进程** —— 句柄值只在其所属进程内有意义。

> **⚠ 官方明确警告关闭句柄可能导致应用或系统不稳定。**
>
> 程序不知道自己的句柄被强夺，后续对该句柄的操作会遇到无效句柄错误，可能导致崩溃或数据损坏。**优先重启持有进程，而非强关句柄。** 只在无法重启（如关键服务）且已评估风险时使用。

## 句柄泄漏排查

`-s` 按对象类型输出计数，这是泄漏归因的入口：

```powershell
# 看某进程各类型句柄的数量
handle64.exe -accepteula -nobanner -p 4728 -s

# 输出形态：
#   File         : 142
#   Event        : 8931      ← 异常，泄漏嫌疑
#   Key          : 23
#   Mutant       : 4
#   Thread       : 12
```

### 时序对比（推荐做法）

**脚本化对比比肉眼盯 GUI 可靠得多：**

```powershell
# 每分钟采一次，共 30 次
1..30 | ForEach-Object {
  $ts = Get-Date -Format 'HH:mm:ss'
  $out = handle64.exe -accepteula -nobanner -p 4728 -s
  "$ts`n$out" | Add-Content C:\trace\handle-trend.txt
  Start-Sleep 60
}
```

CSV 形式更适合解析：

```powershell
# 采全量句柄明细（CSV），对比两个时间点
handle64.exe -accepteula -nobanner -a -p 4728 -v > before.csv
# ……触发怀疑泄漏的操作……
handle64.exe -accepteula -nobanner -a -p 4728 -v > after.csv

Compare-Object (Get-Content before.csv) (Get-Content after.csv) |
  Where-Object SideIndicator -eq '=>'
```

**泄漏的往往是无名对象**（未命名的 Event、Semaphore）。Handle 的 `-a` 会包含它们；Process Explorer 侧则需要额外打开 `View → Show Unnamed Handles and Mappings`（默认关闭）。

### 按进程名前缀过滤

`-p` 接受部分名称：

```powershell
handle64.exe -a -p exp      # 命中 Explorer
handle64.exe -a -p chrome   # 命中所有 chrome 进程
```

多个同名实例时会全部列出，需要精确定位用 PID。

## 与替代方案的取舍

| 工具 | 优势 | 劣势 |
|---|---|---|
| **Handle** | 脚本化友好；CSV 输出；`-s` 类型计数；能强制关句柄 | 需单独部署；**维护停滞 4 年**；需管理员权限 |
| **Process Explorer** Find Handle | 交互直观；双击跳转；能看更多上下文 | 无法脚本化 |
| `openfiles /query` | 系统自带 | 需先启用（`openfiles /local on` 且要重启）；只覆盖文件；输出难解析 |
| `Get-SmbOpenFile` | 原生，对象输出 | **只覆盖 SMB 共享打开的文件**，不含本地句柄 |

**Handle 的能力在本机场景可被 Process Explorer 覆盖**（交互式）或 `openfiles`（受限）。它的不可替代价值在于**脚本化 + 全对象类型 + 类型计数**这个组合。

## 常见坑

1. **默认只列文件句柄。** 查互斥体/注册表键/事件必须加 `-a`。
2. **必须管理员权限。** 非提权运行输出为空或不全，且不明确报错。
3. **`-c` 必须配合 `-p`。** 句柄值只在所属进程内有意义。
4. **`-c` 的句柄值按十六进制解析。** 不要写十进制。
5. **关闭句柄有风险。** 官方明确警告可能导致应用或系统不稳定。优先重启持有进程。
6. **`-p` 接受部分名称**，可能意外命中多个进程。精确定位用 PID。
7. **架构后缀。** 用 `handle64.exe`，32 位版在 64 位系统上可能漏项。
8. **维护停滞（2022-10-26）。** 遇到缺陷不会修复。
9. **输出可能含敏感路径。** 官方 EULA 警示 Sysinternals 工具保存的文件可能包含用户名、密码、访问过的文件与注册表路径。外发前脱敏。

## 分发

```
handle.exe    761,240   x86      handle64.exe   416,144   x64
（ARM64 为 handle64a.exe）
```

winget 包名 `Microsoft.Sysinternals.Handle`。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/handle（Published 2022-10-26，`ms.date` / `updated_at` 均为 2022-10-26T19:28Z）

> **本篇事实边界：** 完整语法与全部参数描述提取自 `handle64.exe` v5.0 二进制内嵌 usage（与官方页面重叠部分已交叉核对）。管理员权限前提、默认只列文件句柄需 `-a`、路径子串大小写不敏感匹配、`-c` 需配合 PID 且关闭句柄可能导致不稳定的警告、`-s`/`-u`/`-v`/`-vt`/`-p` 语义均来自官方页面。`-g`（打印授予访问权限）来自二进制 usage。时序对比配方、替代方案取舍、`-g` 判断锁类型的用法为实践经验总结。
