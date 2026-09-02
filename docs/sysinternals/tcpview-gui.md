# TCPView — 图形界面

**v4.19（2023-04-11，维护停滞）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/tcpview
**CLI 篇：** [tcpvcon-cli.md](tcpvcon-cli.md)（独立可执行文件 `tcpvcon.exe`，随同一个包分发）

> **维护状态：** v4.19 发布于 2023-04-11，官方索引页 What's New 时间线（2026-03 至 2026-08）中无 TCPView 更新条目。遇到缺陷不会修复。
>
> **来源说明：** 颜色语义、刷新率、关闭连接、Tcpvcon 参数来自官方页面。菜单结构（含官方页面未记载的协议过滤、连接状态筛选、Whois）提取自 `tcpview64.exe` v4.19 二进制资源。

## 定位与边界

显示所有 TCP 与 UDP 端点的详细列表，含本地/远端地址与 TCP 连接状态，**并报告持有该端点的进程名（含服务名）**。官方定位为「netstat 的一个更翔实、呈现更便利的子集」。

**「归因到进程」是它相对 netstat 的核心价值** —— `netstat -ano` 只给 PID，还要再查 PID 对应什么；TCPView 直接显示进程名与服务名。

| 需求 | TCPView 是否合适 |
|---|---|
| 「哪个程序在连这个 IP」 | ✅ 正是设计目标 |
| 「端口被谁占了」 | ✅ 比 `netstat -ano` + `tasklist` 两步快 |
| 实时观察连接建立/断开 | ✅ 颜色高亮变化 |
| 抓包看协议内容 | ❌ 用 Wireshark，TCPView 只看端点不看载荷 |
| 脚本化采集 | ❌ 用 [Tcpvcon](tcpvcon-cli.md) |
| 长期记录网络连接 | ❌ 用 [Sysmon](sysmon.md) 的 Event ID 3（注意默认禁用） |

## 主窗口布局

```
┌─ TCPView ──────────────────────────────────────────────────────────────┐
│ File  Edit  View  Process  Connection  Options  Help                   │ ← 菜单栏
├────────────────────────────────────────────────────────────────────────┤
│ 💾 🔄 ⏸ │ [Quick Find: Ctrl+F      ] │ ☑TCPv4 ☑TCPv6 ☑UDPv4 ☑UDPv6   │ ← 工具栏
│         └ Space 暂停/恢复             └─── View → Protocols ────┘      │
├────────────────────────────────────────────────────────────────────────┤
│ Process    PID  Proto  Local Addr    Local  Remote Addr   Remote State │
│                        ess           Port                 Port         │
│ chrome.exe 8124 TCP    192.168.1.10  52310  142.250.x.x   443 ESTABLI… │ ← 白：稳定
│ YourApp    4728 TCP    0.0.0.0       8080   *             *   LISTENING│
│ backup.exe 5512 TCP    192.168.1.10  52411  10.0.0.5      445 ESTABLI… │ ← 绿：新增
│ old.exe    3120 TCP    192.168.1.10  52099  203.0.113.9   80  TIME_WAIT│ ← 红：即将消失
│ svchost    1204 UDP    0.0.0.0       5353   *             *            │ ← 黄：状态变化
├────────────────────────────────────────────────────────────────────────┤
│ Endpoints: 187   Established: 42   Listening: 61                       │ ← 状态栏
└────────────────────────────────────────────────────────────────────────┘
```

### 颜色语义（官方定义）

| 颜色 | 含义 |
|---|---|
| **绿色** | 新出现的端点（new endpoints） |
| **黄色** | 从上次刷新到本次**状态发生变化**的端点 |
| **红色** | 已被删除的端点（deleted） |
| 无色 | 稳定未变 |

**颜色只在一个刷新周期内显示**，下次刷新就恢复。所以观察瞬时连接时要么放慢刷新率，要么按空格及时暂停。

## 菜单结构

```
File                    Edit                  View
├ Save...     Ctrl+S    ├ Copy      Ctrl+C    ├ Toggle Pause/Resume   Space
└ Exit                  └ Quick Find Ctrl+F   ├ Refresh Now
                                              ├ Update Speed          ▸
Process                 Connection            │ ├ 1 Second（默认）
├ Properties...         ├ Whois...            │ ├ 2 Seconds
└ Kill...               └ Close               │ ├ 5 Seconds
                                              │ └ Pause              Space
Options                 Help                  ├ Protocols            ▸
├ ☑ Resolve Addresses   ├ Help                │ ├ ☑ TCP v4
├ ☐ Always on Top       └ About TCPView...    │ ├ ☑ TCP v6
├ Theme  ▸ Default/Dark                       │ ├ ☑ UDP v4
├ Font...                                     │ └ ☑ UDP v6
└ Reset                                       ├ Connection States...  ← 见下
                                              ├ ☑ Toolbar
                                              └ ☑ Status Bar
```

**协议过滤（`View → Protocols`）与连接状态筛选（`View → Connection States`）官方页面未记载**，但都是实用的降噪手段。

## 连接状态筛选

`View → Connection States` 打开对话框，标签原文 `Choose which connection states to show:`，带 `All` / `None` 两个批量按钮。

**这是 TCPView 最有效的降噪功能。** 典型用法：

| 排查目标 | 只勾选 |
|---|---|
| 「谁在往外连」 | `ESTABLISHED` |
| 「哪些端口在监听」 | `LISTENING` |
| 「连接为何建不起来」 | `SYN_SENT`（卡在这里 = 对端不响应） |
| 「大量连接堆积」 | `TIME_WAIT` / `CLOSE_WAIT`（见下） |

**`TIME_WAIT` 与 `CLOSE_WAIT` 大量堆积的诊断意义不同：**

- **`TIME_WAIT` 多** —— 通常正常（主动关闭方的必经状态，约 4 分钟后自动消失）。但若数万条并伴随端口耗尽错误，说明短连接建太快，应改用连接池。
- **`CLOSE_WAIT` 多** —— **几乎总是应用 bug**：对端已关闭，本端却没调用 `close()`。这不会自动消失，是资源泄漏。

## 定位「端口被谁占了」

```
① Ctrl+F 输入端口号，或按 Local Port 列排序找到该端口
② 读 Process 列拿到进程名与 PID
③ 需要更多信息 → Process → Properties
④ 需要终止 → Process → Kill
```

比 `netstat -ano | findstr :8080` + `tasklist /fi "pid eq NNNN"` 两步快。

对应命令行：`tcpvcon -a -n` 输出全部端点后过滤。

## 关闭连接与终止进程

| 操作 | 菜单 | 说明 |
|---|---|---|
| 关闭连接 | `Connection → Close`，或右键 `Close Connection` | **仅对状态为 `ESTABLISHED` 的连接有效**（官方明确） |
| 终止进程 | `Process → Kill` | 破坏性，会终止整个进程 |

官方原文说明关闭连接的入口为 `File|Close Connections` 或右键菜单 —— v4.19 二进制中该项在 `Connection` 菜单下（`&Close`）。以实际菜单为准。

> **⚠** 强行关闭连接会让应用遇到意外的连接中断，可能导致数据丢失或状态不一致。优先重启应用。

## 地址解析

`Options → Resolve Addresses` 控制是否把 IP 解析为域名。

**排查时通常应该关掉：**

- 解析会产生额外的 DNS 查询（可能干扰你正在排查的网络问题）
- 大量端点时解析很慢，界面卡顿
- 恶意连接的 IP 往往没有有效反解，解析纯属浪费

> **对应 CLI：** `tcpvcon -n`（不解析地址）。

## Whois 查询

`Connection → Whois` 对选中连接的远端地址做 Whois 查询，弹出结果窗口。

**这是 TCPView 里少见的「往外发请求」功能** —— 会把你查询的 IP 发给 Whois 服务器。排查内网问题时无意义，排查可疑外连时有用（确认 IP 归属的 ASN/国家/注册组织）。

官方页面未记载此功能。

## 保存输出

`File → Save`（`Ctrl+S`）保存当前窗口内容到文件。

> **对应 CLI：** `tcpvcon -c` 输出 CSV，更适合脚本处理与时序对比。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 参数 |
|---|---|
| 默认视图（仅 ESTABLISHED） | `tcpvcon`（无参数，默认只显示已建立的 TCP 连接） |
| `View → Connection States` 全选 | `-a`（显示全部端点） |
| `Options → Resolve Addresses` 取消勾选 | `-n` |
| `File → Save` | `-c`（CSV） |
| 按进程名/PID 筛选 | `tcpvcon <进程名或 PID>` 位置参数 |
| `View → Protocols` 协议过滤 | **无** |
| `View → Connection States` 逐状态筛选 | **无** |
| `Connection → Whois` | **无** |
| `Connection → Close` | **无** |
| `Process → Kill` | **无** |
| 颜色高亮变化 | **无**（CLI 是快照，无变化概念） |

## GUI 侧常见坑

1. **颜色只在一个刷新周期内显示。** 观察瞬时连接要放慢刷新率或及时按空格暂停。
2. **`Resolve Addresses` 默认开启，会产生 DNS 查询。** 排查网络问题时先关掉，避免干扰与卡顿。
3. **`Close Connection` 只对 `ESTABLISHED` 有效。** 对 LISTENING / TIME_WAIT 无效。
4. **`CLOSE_WAIT` 堆积几乎总是应用 bug**，不会自动消失；`TIME_WAIT` 堆积通常正常。
5. **`Whois` 会向外发请求。** 排查敏感环境时注意。
6. **需管理员权限才能看到全部进程的端点。** 非提权运行会漏掉其他用户/系统进程的连接。
7. **只看端点不看载荷。** 需要看协议内容用 Wireshark。
8. **维护停滞（2023-04-11）。** 遇到缺陷不会修复。

## 分发

TCPView 包（`TCPView.zip`，1.5 MB）内含 GUI 与 CLI：

```
tcpview.exe      944,520   x86 GUI      tcpvcon.exe     202,632   x86 CLI
tcpview64.exe  1,087,368   x64 GUI      tcpvcon64.exe   250,816   x64 CLI
```

Sysinternals Live：`https://live.sysinternals.com/Tcpview.exe`
运行环境：客户端 Windows 8.1+，服务器 Windows Server 2012+。
winget 包名 `Microsoft.Sysinternals.TCPView`。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/tcpview

> **本篇事实边界：** 定位、颜色语义（绿/黄/红）、默认 1 秒刷新率、关闭 ESTABLISHED 连接、地址解析开关、Tcpvcon 参数、Tcpvcon 随包分发均来自官方页面（`ms.date` 2023-03-30，`updated_at` 2024-02-06）。菜单结构、协议过滤、连接状态筛选对话框、Whois、Theme 提取自 `tcpview64.exe` v4.19 二进制资源，官方页面未记载。TIME_WAIT/CLOSE_WAIT 诊断判据、关闭地址解析的理由、降噪组合为实践经验总结。
