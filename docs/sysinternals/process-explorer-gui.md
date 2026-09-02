# Process Explorer — 图形界面

**v17.13（2026-08-12）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer
**CLI 篇：** [process-explorer-cli.md](process-explorer-cli.md)

> **来源说明：** 官方页面只描述了双窗格结构与三类适用场景，**不含版本号、命令行参数、VirusTotal 集成或「替换任务管理器」的任何说明**（官方明确把操作用法下放给随包 help 文件，问题排查引导至 Microsoft Q&A 的 procexp 板块）。本篇菜单结构、对话框选项与原文提示提取自 `procexp64.exe` **v17.13** 二进制资源。ASCII 布局图为按资源结构绘制的示意，非像素级还原。

## 定位与边界

官方对界面结构的权威描述：界面由两个子窗格组成，**上窗格始终列出当前活动进程及其所属账户名**，下窗格内容取决于当前模式 —— 句柄模式显示所选进程已打开的句柄，DLL 模式显示该进程加载的 DLL 与内存映射文件。

官方定位的三个强项场景：

1. **查找哪个程序打开了某个文件或目录**（搜索持有特定句柄或加载特定 DLL 的进程）
2. **排查 DLL 版本问题**
3. **排查句柄泄漏**

| 需求 | Process Explorer 是否合适 |
|---|---|
| 「谁锁定了这个文件」 | ✅ Find Handle，最快路径 |
| 「这个进程现在持有什么」静态快照 | ✅ 正是设计目标 |
| 「加载 DLL 时探测了哪些路径」时序 | ❌ 用 [Procmon](procmon-gui.md)，PE 只给最终结果 |
| CPU 被驱动/中断吃掉 | ✅ 任务管理器把 Interrupts 计入 Idle，PE 单列显示 |
| 批量/脚本化查句柄 | ❌ 用 [Handle](handle.md)，PE 的 CLI 只管启动姿态 |
| 长期监控 | ❌ 用 [Sysmon](sysmon.md) |

**数据来源不只是公开 API：** PE 通过自带的内核设备驱动获取进程/系统数据 —— 这解释了为何完整功能需要管理员权限（首次加载驱动）。非提权运行时症状通常是「看不到别的用户的进程」或「句柄列为空」，而非明确报错。

## 主窗口布局

```
┌─ Process Explorer ─────────────────────────────────────────────────────┐
│ File  Options  View  Process  Find  Users  Help                        │ ← 菜单栏
├────────────────────────────────────────────────────────────────────────┤
│ 💾 🔄 ⏸ │ ▦ 📊 │ ✖ 🌲 │ ⓘ 🔍 🎯 │  ╱╲╱╲  ╱╲__  ▁▃▅  ▂▄▆         │ ← 工具栏+微图
│ └┬┘└┬┘└┬┘ └┬┘└┬┘ └┬┘└┬┘ └┬┘└┬┘└┬┘   └──┬──┘ └─┬─┘ └┬┘  └┬┘          │
│  │  │  │   │  │   │  │   │  │  └ 目标准星（拖到窗口上定位其进程）      │
│  │  │  │   │  │   │  │   │  └ Find Handle or DLL (Ctrl+Shift+F)       │
│  │  │  │   │  │   │  │   └ Properties                                  │
│  │  │  │   │  │   │  └ Show Process Tree (Ctrl+T)                      │
│  │  │  │   │  │   └ Kill Process (Del)                                 │
│  │  │  │   │  └ System Information（点微图打开）                       │
│  │  │  │   └ Show Lower Pane (Ctrl+L)                                  │
│  │  │  └ Paused (Space) ← 分析时按空格冻结                             │
│  │  └ Refresh Now (F5)                                                 │
│  └ Save (Ctrl+S) / Save As (Ctrl+A)                                    │
├────────────────────────────────────────────────────────────────────────┤
│ Process            PID   CPU  Private Bytes  Description   User Name   │
│ ├ System Idle Pro… 0     94.2                                          │ ← 上窗格
│ ├ Interrupts       n/a   1.8  ← 任务管理器不单列，PE 单列               │   始终是进程
│ ├ System           4                                                   │
│ │ └ smss.exe       412                                                 │
│ ├ services.exe     892        4,120 K       Services…     SYSTEM       │
│ │ └ YourApp.exe    4728  2.1  128,400 K     Your App      DOMAIN\user  │ ← 选中它
│ └ explorer.exe     2156  0.4   88,200 K     Windows Expl… DOMAIN\user  │
├────────────────────────────────────────────────────────────────────────┤
│ Type      Name                                          Handle         │ ← 下窗格
│ File      C:\data\locked.db                             0x2A4          │   模式三选一：
│ File      C:\logs\app.log                               0x310          │   DLLs  Ctrl+D
│ Key       HKLM\SOFTWARE\YourApp                         0x1F8          │   Handles Ctrl+H
│ Mutant    \Sessions\1\BaseNamedObjects\YourAppMutex     0x0C4          │   Threads Ctrl+Y
├────────────────────────────────────────────────────────────────────────┤
│ CPU Usage: 5.8%  Commit Charge: 42.1%  Processes: 187  Physical: 61%   │ ← 状态栏
└────────────────────────────────────────────────────────────────────────┘
```

**`Interrupts` 单列显示是 PE 替代任务管理器的核心理由。** 任务管理器把中断的 CPU 占用计入 Idle，导致「CPU 明明很忙但看不到是谁」。PE 把 Interrupts 作为独立条目列出，驱动吃 CPU 只能这样定位。

## 菜单结构与快捷键

v17.13 完整菜单：

```
File                     Options                              View
├ Run...        Ctrl+R   ├ ☐ Run At Logon                     ├ ☑ Show Process Tree    Ctrl+T
├ Save          Ctrl+S   ├ ☐ Verify Image Signatures           ├ ☐ Show Column Heatmaps
├ Save As...    Ctrl+A   ├ VirusTotal.com          ▸           ├ ☐ Scroll to New Processes
├ Shutdown      ▸        │ ├ ☐ Check VirusTotal.com            ├ ☐ Show Unnamed Handles
│ ├ Logoff               │ └ ☐ Submit Unknown Executables      │     and Mappings
│ ├ Shutdown             ├ ☐ Always On Top                     ├ ☐ Show Processes From
│ └ Restart              ├ ☐ Hide When Minimized               │     All Users
└ Exit                   ├ ☐ Allow Only One Instance           ├ ☑ Show Lower Pane Ctrl+L
                         ├ ☑ Confirm Kill                      ├ Lower Pane View        ▸
Process                  ├ ☐ Highlight Relocated DLLs          │ ├ ○ DLLs           Ctrl+D
├ Window          ▸      ├ Tray Icons              ▸           │ ├ ● Handles        Ctrl+H
│ ├ Bring to Front       │ ├ ☐ CPU History                     │ └ ○ Threads        Ctrl+Y
│ ├ Restore              │ ├ ☐ I/O History                     ├ Refresh Now            F5
│ ├ Minimize             │ ├ ☐ Commit History                  ├ Update Speed           ▸
│ ├ Maximize             │ └ ☐ Physical Memory History         │ ├ ○ .5 seconds
│ └ Close                ├ Difference Highlight Duration...    │ ├ ● 1 second
├ Set Priority    ▸      ├ Font...                             │ ├ ○ 2 seconds
│ ├ Realtime: 24         ├ Theme                   ▸           │ ├ ○ 5 seconds
│ ├ High: 13             │ ├ ○ Light                           │ ├ ○ 10 seconds
│ ├ Normal: 8            │ ├ ○ Dark                            │ └ ○ Paused        Space
│ └ Idle: 4              │ └ ○ Use System Setting              ├ Organize Column Sets...
├ Kill Process    Del    └ Replace Task Manager  ← 见下        ├ Save Column Set...
├ Kill Process Tree      （官方页面对此无任何说明）            ├ Load Column Set        ▸
│              Shift+Del                                       └ Select Columns...
├ Restart                Find
├ Suspend                ├ Filter Processes...      Ctrl+F     Help
├ Create Dump     ▸      └ Find Handle or DLL... Ctrl+Shift+F  ├ Help...
│ ├ Create Minidump...                                          └ About Process Explorer...
│ └ Create Full Dump...
├ Check VirusTotal.com
├ Properties...
└ Search Online...  Ctrl+M
```

`Theme`（Light / Dark / Use System Setting）与 Procmon 同样是较新加入的。

## 定位「谁锁定了这个文件」

**这是 PE 最高频的用途。** `Find → Find Handle or DLL`（`Ctrl+Shift+F`）：

```
┌─ Process Explorer Search ──────────────────────────────────────┐
│ Handle or DLL substring:                                       │
│ [locked.db                                    ] [Search] [Cancel]│
│                                                                │
│ Process              PID    Type   Handle  Name                │
│ YourApp.exe          4728   File   0x2A4   C:\data\locked.db   │
│ backup.exe           5512   File   0x1B0   C:\data\locked.db   │
│                              ↑ 双击跳到上窗格对应进程          │
└────────────────────────────────────────────────────────────────┘
```

对话框标签原文为 `Handle or DLL substring:` —— **是子串匹配，不是完整路径匹配**。输入 `locked.db` 即可，不必写全路径。

**完整处置流程：**

```
① Ctrl+Shift+F 输入文件名片段 → Search
② 双击结果行 → 跳到上窗格该进程
③ 判断该进程是否可安全终止
④ 若可：确认下窗格 Handles 模式，找到该句柄 → 右键 Close Handle
   若不可：Process → Kill Process（Del）终止整个进程
```

> **⚠ 关闭句柄的风险：** Handle 官方文档明确警告关闭句柄可能导致应用或系统不稳定。程序不知道自己的句柄被强夺，后续操作会遇到无效句柄。**优先重启持有进程，而非强关句柄。**

对应命令行工具是 [Handle](handle.md)（`handle locked.db`），适合脚本化与批量场景。

## 下窗格三种模式

`View → Lower Pane View`，或直接用快捷键切换：

| 模式 | 快捷键 | 显示内容 | 排查用途 |
|---|---|---|---|
| **DLLs** | `Ctrl+D` | 该进程加载的 DLL 与内存映射文件 | DLL 版本问题、加载了错误副本 |
| **Handles** | `Ctrl+H` | 该进程已打开的句柄 | 文件锁定、句柄泄漏 |
| **Threads** | `Ctrl+Y` | 该进程的线程 | 哪个线程在烧 CPU |

`Ctrl+L`（`Show Lower Pane`）整体显隐下窗格。

**`View → Show Unnamed Handles and Mappings` 默认关闭。** 排查句柄泄漏时**必须打开** —— 泄漏的往往正是无名对象（未命名的事件、信号量），关着这个开关会看不到它们。

### DLL 版本排查

切到 DLLs 模式后，加 `Version`、`Path`、`Company Name` 列（右键列头 → Select Columns）。典型判据：

- 同一 DLL 在多个进程里版本不同 → DLL 地狱，检查各自的加载路径
- DLL 路径不在预期目录 → 被同目录的旧副本抢先加载
- `Options → Highlight Relocated DLLs` 打开后，被重定位的 DLL 会高亮 —— 重定位意味着基址冲突，可能有性能影响

### 句柄泄漏排查

```
① View → Show Unnamed Handles and Mappings 打开
② 选中目标进程，下窗格切 Handles（Ctrl+H）
③ 上窗格加 Handles 列（右键列头 → Select Columns → Process Performance → Handles）
④ 观察 Handles 列是否单调增长
⑤ 增长则在下窗格找出增长的对象类型
```

对应命令行做法见 [Handle](handle.md) 的 `-s`（按对象类型输出句柄计数）+ CSV 导出做时序对比 —— **脚本化对比比肉眼盯 GUI 可靠**。

## CPU 归因

```
① 上窗格按 CPU 列降序排序
② 看 Interrupts 条目：占比高 → 驱动/硬件中断问题，不是应用问题
③ 定位到具体进程后，下窗格切 Threads（Ctrl+Y）
④ Threads 列表按 CPU 排序，找出烧 CPU 的线程
⑤ 双击该线程 → Stack 看它在执行什么（需配符号）
```

**`Options → Difference Highlight Duration` 控制新增/退出进程的高亮时长**（默认 1 秒）。排查「有进程一闪而过」时把它调长到 3-5 秒，配合 `View → Scroll to New Processes` 就能看清瞬时进程。

工具栏的微型图表（CPU / I/O / Commit / Physical Memory）点击可打开 **System Information** 窗口，展示系统级趋势图。`Options → Tray Icons` 可把这些图表放到通知区常驻。

## VirusTotal 集成

`Options → VirusTotal.com` 子菜单两项：

```
├ ☐ Check VirusTotal.com        ← 提交哈希，查询已知结果
└ ☐ Submit Unknown Executables  ← 上传文件本体
```

首次启用弹出条款同意框，原文：

> You must agree to VirusTotal's terms of service to use VirusTotal features.
> https://www.virustotal.com/about/terms-of-service

以及功能说明原文：

> You can enable lookup of VirusTotal results for all files displayed in the process and DLL views by selecting the Check VirusTotal entry in the Options menu or check individual files on-demand using the process and DLL properties dialogs.

> When you do, Process Explorer will submit hashes for files listed in the process and DLL view to VirusTotal.com. You can submit a file's contents by using the Submit button on the process and DLL properties dialog boxes.

**两个选项的隐私边界完全不同，务必分清：**

| 选项 | 行为 | 隐私影响 |
|---|---|---|
| `Check VirusTotal.com` | 只提交**文件哈希** | 低。哈希不含文件内容 |
| `Submit Unknown Executables` | VirusTotal 未收录时**上传文件本体** | **高。文件会被上传到第三方并可能公开** |

**生产环境慎用 `Submit Unknown Executables`** —— 内部自研的可执行文件一旦上传，即等同于向第三方公开该二进制。这与 [Sigcheck](strings-sigcheck.md) 和 autorunsc 的 `-v` / `-vs` 分界是同一套语义。

结果列显示为「检出数/引擎总数」（如 `0/72`）。**检出数非零不等于恶意** —— 自研工具、打包器、脚本宿主常被误报；检出数为零也不等于安全。

## 替换任务管理器

`Options → Replace Task Manager` —— **官方页面对此功能无任何说明**，本条来自二进制资源与实测菜单项。

勾选后 `Ctrl+Shift+Esc` 与任务栏右键的「任务管理器」都会启动 PE。取消勾选恢复。

失败时的错误提示原文为 `Error replacing Task Manager` / `Error restoring Task Manager` —— 该操作需修改 `HKLM` 下的 Image File Execution Options，**必须以管理员权限运行 PE**，否则必然失败。

**常驻运行的官方推荐做法**（来自官方节目）：

```powershell
procexp.exe /t /e
```

`/t` 最小化到托盘、`/e` 提升权限，**且这两个开关顺序敏感** —— `/t /e` 与 `/e /t` 行为不等价。详见 [CLI 篇](process-explorer-cli.md)。

配合 `Options → Hide When Minimized` 使用时注意提示原文：

> Because the Hide When Minimized option is selected, you must maintain at least one tray icon so that you can activate Process Explorer when it is minimized.

即启用 Hide When Minimized 后**必须至少保留一个托盘图标**（`Options → Tray Icons` 里勾选任一项），否则最小化后无法唤回。

## 进程操作

`Process` 菜单提供的处置手段：

| 操作 | 快捷键 | 注意 |
|---|---|---|
| `Kill Process` | `Del` | 受 `Options → Confirm Kill` 保护（默认开启） |
| `Kill Process Tree` | `Shift+Del` | 连带全部子进程，破坏性更大 |
| `Suspend` | — | 冻结而非终止，用于「先保住现场再分析」 |
| `Restart` | — | 终止后按原命令行重启 |
| `Set Priority` | — | Realtime: 24 / High: 13 / Normal: 8 / Idle: 4 |
| `Create Minidump` | — | 小转储 |
| `Create Full Dump` | — | 含全部内存 |

> **对应 CLI：** 无。PE 的命令行只管启动姿态，进程操作全在 GUI。批量/脚本化抓 dump 用 [ProcDump](procdump.md)，它支持阈值触发与无人值守。

**`Suspend` 是被低估的操作。** 遇到「进程正在疯狂写日志/占满 CPU，但我需要先保留现场」时，Suspend 比 Kill 好 —— 冻结后可从容看句柄、DLL、线程栈，分析完再恢复或终止。

## 列与列集

右键列头或 `View → Select Columns` 配置列。PE 的列极多，分组包括 Process Image / Process Performance / Process Memory / Process I/O / Process GPU / Handle / DLL / .NET 等。

**列集（Column Set）是 PE 独有的效率特性：**

```
View → Save Column Set...       存当前列布局
View → Load Column Set    ▸     从子菜单切换
View → Organize Column Sets...  管理
```

建议按排查场景各存一套：「CPU 排查」（CPU、CPU History、Threads）、「内存排查」（Private Bytes、Working Set、Virtual Size）、「句柄排查」（Handles、Unnamed Handles）、「安全排查」（Verified Signer、VirusTotal、Command Line、Integrity）。切换列集比每次重配列快得多。

`View → Show Column Heatmaps` 打开后数值列按大小着色，扫视时更快发现异常值。

## 符号配置

`Options → Configure Symbols`（用于线程栈的函数名解析）。

**官方页面明示的坑：** 当把符号路径指向符号服务器时，**配置的 DBGHELP.DLL 所在目录必须同时包含支持所用服务器路径的 SYMSRV.DLL**，否则符号解析不可用。官方将细节指向 Windows 驱动文档的 SymSrv 页面。

符号路径语法见 [00-suite-setup.md](00-suite-setup.md#符号配置)。

## GUI 侧常见坑

1. **非提权运行时功能不全且不报错。** 症状是看不到其他用户的进程、句柄列为空。PE 需要加载内核驱动才能拿到完整数据。配 `View → Show Processes From All Users` 或直接用 `/e` 启动。
2. **`Show Unnamed Handles and Mappings` 默认关闭。** 排查句柄泄漏必须打开，否则看不到泄漏的无名对象。
3. **`Submit Unknown Executables` 会上传文件本体到第三方。** 与只提交哈希的 `Check VirusTotal.com` 是完全不同的隐私边界。生产环境慎用。
4. **VirusTotal 检出数非零 ≠ 恶意，为零 ≠ 安全。** 自研工具与打包器常被误报。
5. **`Replace Task Manager` 需管理员权限**，否则报 `Error replacing Task Manager`。
6. **`Hide When Minimized` 必须搭配至少一个托盘图标**，否则最小化后无法唤回。
7. **`/t /e` 顺序敏感。** 见 CLI 篇。
8. **关闭句柄有风险。** 优先重启持有进程。
9. **符号需要匹配的 SYMSRV.DLL** 与 DBGHELP.DLL 同目录。
10. **单文件多架构自解压：** 在 x64 上运行 32 位 `procexp.exe` 时它会自行释放并创建 `procexp64.exe`，磁盘/临时目录会多出一个文件 —— 不是异常。
11. **`Paused`（空格）容易误触。** 分析时按空格冻结很方便，但忘了恢复会以为「数据不刷新」。状态栏与标题栏无明显提示。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer
- **工具自带：`Help → Help`** —— 官方页面把操作用法明确下放给随包 help 文件
- 问题排查：Microsoft Q&A 的 procexp 板块（官方指定入口）
- 符号服务器细节：Windows 驱动文档的 SymSrv 页面

> **本篇事实边界：** 官方页面只描述双窗格结构、三类适用场景、内核驱动数据来源与 SYMSRV.DLL 的坑，**不含版本号、CLI 参数、VirusTotal 集成、替换任务管理器的任何说明**。菜单结构、对话框原文提取自 `procexp64.exe` v17.13 二进制资源；`/t /e` 顺序敏感性与单文件多架构自解压来自官方 Defrag Tools 节目（约 2012 年录制，该节目未提及 VirusTotal，因其为后续版本新增）。排查流程、列集建议、Suspend 用法为实践经验总结。
