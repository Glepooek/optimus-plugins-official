# Tcpvcon — 命令行

**TCPView v4.19（2023-04-11，维护停滞）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/tcpview
**GUI 篇：** [tcpview-gui.md](tcpview-gui.md)

> `tcpvcon.exe` 是**独立的可执行文件**，随 `TCPView.zip` 一同分发。官方原文：「The TCPView download includes Tcpvcon, a command-line version with the same functionality.」
>
> **「same functionality」需要打个折扣** —— Tcpvcon 只有 3 个开关，GUI 的协议过滤、连接状态筛选、Whois、关闭连接、终止进程都没有对应能力。它是「同样的数据源」，不是「同样的功能集」。

## 语法

官方给出的完整语法（原文：`Tcpvcon usage is similar to that of the built-in Windows netstat utility`）：

```
tcpvcon [-a] [-c] [-n] [process name or PID]
```

## 参数表

| 参数 | 官方描述（原文） | 说明 |
|---|---|---|
| `-a` | Show all endpoints (default is to show established TCP connections). | **默认只显示已建立的 TCP 连接**，要看 LISTENING/UDP 必须加 `-a` |
| `-c` | Print output as CSV. | 脚本化处理用 |
| `-n` | Don't resolve addresses. | 不做 DNS 反解，**排查时通常应该加** |
| `<进程名或 PID>` | — | 位置参数，按进程筛选 |
| `-accepteula` | — | 二进制内有，抑制 EULA 弹窗 |

**开关总量就这些。** 没有按端口、按状态、按协议筛选的能力 —— 这些只能靠 `findstr` / PowerShell 后置过滤。

## 关键坑：默认不显示监听端口

**`tcpvcon` 不加参数时只列出 `ESTABLISHED` 的 TCP 连接**（官方原文明确：`default is to show established TCP connections`）。

这意味着「查端口被谁占了」这个最常见需求，**不加 `-a` 会什么都查不到** —— 因为监听端口的状态是 `LISTENING`，不是 `ESTABLISHED`。

```powershell
# ❌ 查监听端口，但什么都看不到
tcpvcon64.exe | findstr 8080

# ✅ 正确
tcpvcon64.exe -a -n | findstr 8080
```

## 实用配方

```powershell
# 全部端点，不解析地址（最常用的基础形式）
tcpvcon64.exe -accepteula -a -n

# 查某端口被谁占用
tcpvcon64.exe -a -n | Select-String ":8080"

# 只看某进程的连接
tcpvcon64.exe -a -n chrome.exe
tcpvcon64.exe -a -n 4728            # 按 PID

# CSV 导出供脚本分析
tcpvcon64.exe -a -n -c > endpoints.csv

# 只看监听端口（后置过滤，Tcpvcon 无状态筛选开关）
tcpvcon64.exe -a -n | Select-String "LISTENING"

# 只看外连（排除本地回环与内网）
tcpvcon64.exe -a -n -c | ConvertFrom-Csv |
  Where-Object { $_.State -eq 'ESTABLISHED' -and
                 $_.'Remote Address' -notmatch '^(127\.|192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)' }
```

### 时序对比：找出新增连接

Tcpvcon 是快照工具，没有 GUI 的颜色高亮变化。要观察变化只能自己做 diff：

```powershell
# 采基线
tcpvcon64.exe -a -n -c > before.csv
# ……触发可疑行为……
tcpvcon64.exe -a -n -c > after.csv

# 只看新增
Compare-Object (Get-Content before.csv) (Get-Content after.csv) |
  Where-Object SideIndicator -eq '=>'
```

### 排查 CLOSE_WAIT 泄漏

```powershell
# 统计各状态数量，定位堆积
tcpvcon64.exe -a -n -c | ConvertFrom-Csv |
  Group-Object State | Sort-Object Count -Descending |
  Select-Object Count, Name
```

**`CLOSE_WAIT` 大量堆积几乎总是应用 bug** —— 对端已关闭，本端没调 `close()`，且不会自动消失。`TIME_WAIT` 堆积通常正常（约 4 分钟自动消失），但数万条并伴随端口耗尽错误则说明短连接建太快，应改用连接池。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 参数 |
|---|---|
| 默认视图 | `tcpvcon`（无参数，仅 ESTABLISHED TCP） |
| `View → Connection States` 全选 | `-a` |
| `Options → Resolve Addresses` 取消勾选 | `-n` |
| `File → Save` | `-c` |
| `Ctrl+F` 按进程查找 | `tcpvcon <进程名或 PID>` |
| 首次运行 EULA 弹窗 | `-accepteula` |
| `View → Protocols`（TCPv4/v6、UDPv4/v6 过滤） | **无** → 后置 `findstr` |
| `View → Connection States` 逐状态筛选 | **无** → 后置过滤 |
| `View → Update Speed` / 刷新 | **无**（快照工具，无刷新概念） |
| 颜色高亮变化（绿/黄/红） | **无** → 自己做 CSV diff |
| `Connection → Whois` | **无** |
| `Connection → Close` | **无** |
| `Process → Kill` | **无** |
| `Process → Properties` | **无** |

## 与 netstat / PowerShell 的取舍

| 工具 | 优势 | 劣势 |
|---|---|---|
| **Tcpvcon** | 直接给进程名与服务名；CSV 输出干净 | 只 3 个开关；需单独部署；维护停滞 |
| `netstat -ano` | 系统自带，无需部署 | 只给 PID，要再查进程名；输出难解析 |
| `Get-NetTCPConnection` | 原生对象输出，可直接管道过滤；有 `-State` `-LocalPort` 等参数 | 不含 UDP（需 `Get-NetUDPEndpoint`）；无服务名 |

**建议：** 交互排查用 GUI 版 TCPView；脚本化在 Windows 8+ 上优先 `Get-NetTCPConnection`（原生、有结构化筛选参数、无需部署第三方工具）；需要「进程名 + 服务名」且要跨老系统时才用 Tcpvcon。

```powershell
# PowerShell 原生等价物（通常更好用）
Get-NetTCPConnection -State Listen | Select-Object LocalPort,OwningProcess,
  @{n='Process';e={(Get-Process -Id $_.OwningProcess -EA 0).ProcessName}}
```

## 常见坑

1. **默认不显示监听端口。** 不加 `-a` 只有 `ESTABLISHED`，查端口占用会一无所获。
2. **默认做 DNS 反解。** 大量端点时很慢，且会产生额外 DNS 查询干扰网络排查。基本上应该总是加 `-n`。
3. **「same functionality」是官方措辞的夸大。** 只有 3 个开关，GUI 的筛选/处置能力全无。
4. **没有状态/协议筛选开关。** 只能靠后置 `findstr` / PowerShell 过滤。
5. **需管理员权限才能看到全部进程的端点。** 非提权运行会漏掉其他用户/系统进程的连接。
6. **架构后缀。** 用 `tcpvcon64.exe`，32 位版在 64 位系统上可能漏项。
7. **维护停滞（2023-04-11）。** 遇到缺陷不会修复，考虑用 `Get-NetTCPConnection` 替代。

## 分发

随 `TCPView.zip`（1.5 MB）一同分发：

```
tcpvcon.exe     202,632   x86      tcpvcon64.exe   250,816   x64
（ARM64 为 tcpvcon64a.exe）
```

运行环境：客户端 Windows 8.1+，服务器 Windows Server 2012+。
winget 包名 `Microsoft.Sysinternals.TCPView`（含 GUI 与 CLI）。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/tcpview（含 `Using Tcpvcon` 一节）

> **本篇事实边界：** 语法、`-a` / `-c` / `-n` 三个参数的官方描述、「默认只显示已建立的 TCP 连接」、Tcpvcon 随包分发均来自官方页面原文（`ms.date` 2023-03-30，`updated_at` 2024-02-06）。`-accepteula` 来自二进制。配方、CLOSE_WAIT/TIME_WAIT 判据、与 netstat/PowerShell 的取舍为实践经验总结。
