# Process Monitor — 图形界面

**v4.1（2026-08-19）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/procmon
**CLI 篇：** [procmon-cli.md](procmon-cli.md)

> **来源说明：** 本篇菜单结构、快捷键、对话框选项文本均提取自 `Procmon64.exe` **v4.1** 二进制资源，与实际界面一致。官方网页（396 词）不含这些内容。ASCII 布局图为按资源结构绘制的示意，标注面板划分与控件位置，非像素级还原。

## 定位与边界

实时捕获文件系统、注册表、进程/线程、网络与 Profiling 活动。前身是 Filemon + Regmon 的合并。

**v4.1 新增 IPC 事件类**，覆盖命名管道（named pipes）与邮件槽（mailslots）——官方索引页 What's New 记载的变更，旧文档中「Procmon 有五类事件」的说法已过时。

| 需求 | Procmon 是否合适 |
|---|---|
| 「现在正在发生什么」，秒级高频 | ✅ 正是设计目标 |
| 「昨天发生过什么」，长期审计 | ❌ 用 [Sysmon](sysmon.md)。Procmon 是交互式采样，不是常驻服务 |
| 某进程当前持有哪些句柄（静态快照） | ❌ 用 [Process Explorer](process-explorer-gui.md)。Procmon 捕获操作事件流，不是句柄表 |
| DLL 加载失败的完整探测序列 | ✅ Procmon 给出按序的 `NAME NOT FOUND` 链，Process Explorer 只给最终结果 |
| 开机早期、登录前 | ✅ Boot logging |
| 无人值守 / 间歇性问题守候 | ❌ 用 [CLI 篇](procmon-cli.md)的 `/RingBuffer` `/Runtime`，无 GUI 入口 |

## 主窗口布局

```
┌─ Process Monitor ──────────────────────────────────────────────────┐
│ File  Edit  Event  Filter  Tools  Options  Help                    │ ← 菜单栏
├────────────────────────────────────────────────────────────────────┤
│ 🖉 💾 │ 🔍 ⊘ │ ▦ 🔧 │ 🗔 📊 │ 🗂 📁 ⚙ 🌐 📈                        │ ← 工具栏
│ └┬┘└┬┘  └┬┘└┬┘  └┬┘└┬┘  └┬┘└┬┘  └──────┬───────┘                  │
│  │  │    │  │    │  │    │  │          └ 五个事件类别开关          │
│  │  │    │  │    │  │    │  │            Registry / File System /  │
│  │  │    │  │    │  │    │  │            Network / Process&Thread /│
│  │  │    │  │    │  │    │  │            Profiling                 │
│  │  │    │  │    │  │    │  └ Process Tree (Ctrl+T)                │
│  │  │    │  │    │  │    └ Find (Ctrl+F)                           │
│  │  │    │  │    │  └ Highlight (Ctrl+H)                           │
│  │  │    │  │    └ Filter (Ctrl+L)                                 │
│  │  │    │  └ Clear Display (Ctrl+X)                               │
│  │  │    └ Capture Events (Ctrl+E) ← 启动后第一件事：关掉它         │
│  │  └ Save (Ctrl+S)                                                │
│  └ Auto Scroll (Ctrl+A) ← 分析时关掉                               │
├────────────────────────────────────────────────────────────────────┤
│ Time  │ Process Name │ PID  │ Operation  │ Path      │ Result      │ ← 列（可增删）
│ 08:31 │ yourapp.exe  │ 4728 │ CreateFile │ C:\a.cfg  │ NAME NOT F… │
│ 08:31 │ yourapp.exe  │ 4728 │ CreateFile │ D:\a.cfg  │ SUCCESS     │ ← 双击看属性
│ …     │ …            │ …    │ …          │ …         │ …           │
├────────────────────────────────────────────────────────────────────┤
│ Showing 1,204 of 87,331 events (1.3%)          Backed by C:\…pml   │ ← 状态栏
└────────────────────────────────────────────────────────────────────┘
                  └─ 过滤后/总数比例，判断过滤器是否过窄的第一眼依据
```

**状态栏的 `Showing X of Y events` 是最被忽视的信息。** 过滤器写窄了、看不到预期事件时，先看这里：`Showing 0 of 87,331` 说明事件采到了但被过滤器挡住；`Showing 0 of 0` 说明根本没采集（Capture Events 关着或类别开关全关）。

## 菜单结构与快捷键

v4.1 完整菜单项：

```
File                          Edit                      Event
├ Open...                     ├ Copy          Ctrl+C    ├ Properties...      Ctrl+P
├ Save...                     ├ Find...       Ctrl+F    ├ Stack...           Ctrl+K
├ ☑ Capture Events            ├ Find Highlight          ├ Toggle Bookmark    Ctrl+B
└ Exit                        ├ Find Bookmark           ├ Jump To...         Ctrl+J
                              ├ ☑ Auto Scroll Ctrl+A    ├ Count Occurrences...
                              └ Clear Display Ctrl+X    └ Search Online

Filter                            Tools                          Options
├ ☐ Enable Advanced Output        ├ System Details...             ├ ☐ Always on Top
├ Filter...           Ctrl+L      ├ Process Tree...     Ctrl+T    ├ Font...
├ Reset Filter        Ctrl+R      ├ Process Activity Summary...   ├ Highlight Colors...
├ Load Filter         ▸           ├ File Summary...               ├ Theme            ▸
├ Save Filter...                  ├ Registry Summary...           │ ├ ○ Light
├ Organize Filters...             ├ Stack Summary...              │ ├ ○ Dark
├ ☐ Drop Filtered Events          ├ Network Summary...            │ └ ○ Use System Theme
└ Highlight...        Ctrl+H      ├ Cross Reference Summary...    ├ Configure Symbols...
                                  └ Count Occurrences...          ├ Select Columns...
Help                                                              ├ History Depth...
├ Help...                                                         ├ Profiling Events...
├ Command Line Options...  ← 官方网页查不到的开关表在这里          ├ ☐ Enable Boot Logging
└ About...                                                        ├ ☐ Show Resolved
                                                                  │   Network Addresses Ctrl+N
                                                                  ├ ☐ Hex File Offsets…
                                                                  └ ☐ Hex Process and Thread IDs
```

三处与网上流传的旧版信息不同，已按 v4.1 核对：

- **`Highlight` 在 Filter 菜单**（`Ctrl+H`），不在 Edit 菜单
- **`Drop Filtered Events` 在 Filter 菜单**，不在 Options 菜单
- **`Theme`（Light/Dark/Use System Theme）是较新加入的**，切换后需重启生效，对话框原文：`Selected theme will take effect the next time you restart Process Monitor`

## 启动后的第一件事：停止采集

Procmon 启动即开始全量采集，几秒内堆积数万条事件。

```
① File → Capture Events 取消勾选     （工具栏放大镜带红叉 = 已停止）
② Ctrl+X 清空已有事件
③ 配置过滤器（见下）
④ 重新勾选 Capture Events 开始采集
⑤ 复现问题
⑥ 再次取消 Capture Events 停止
```

> **对应 CLI：** `/NoConnect`（启动但不采集）。见 [CLI 篇](procmon-cli.md#完整开关表)。

## 筛选进程

### 方法一：从事件行右键（最快）

```
┌─ 右键菜单（点在 Process Name 列上）────────┐
│ Properties...                    Ctrl+P    │
│ Stack...                         Ctrl+K    │
│ Jump To...                       Ctrl+J    │
│ Search Online                              │
│ ─────────────────────────────────────────  │
│ Include 'yourapp.exe'      ← 只看该进程    │
│ Exclude 'yourapp.exe'      ← 排除该进程    │
│ Highlight 'yourapp.exe'    ← 高亮不过滤    │
│ ─────────────────────────────────────────  │
│ Copy 'yourapp.exe'               Ctrl+C    │
│ Edit Filter 'yourapp.exe'                  │
└────────────────────────────────────────────┘
```

**右键菜单按你点击的那一列给出对应过滤项**：点 Process Name 列给进程过滤，点 Path 列给路径过滤，点 Result 列给结果过滤。看到一堆无关的 `svchost.exe` 噪音就右键 Exclude——这是最省事的降噪方式。

### 方法二：Process Tree（`Ctrl+T`）

```
┌─ Process Tree ─────────────────────────────────────────────────┐
│ Process                    PID   Description      Owner        │
│ ├ services.exe             892   Services…        SYSTEM       │
│ │ ├ svchost.exe            1204  Host Process…    SYSTEM       │
│ │ └ YourService.exe        3312  Your Service     SYSTEM       │
│ │   └ worker.exe           4728  Worker           SYSTEM   ←── │ 选中它
│ └ explorer.exe             2156  Windows Explorer USER         │
├────────────────────────────────────────────────────────────────┤
│ [Include Process] [Include Subtree] [Go To Event] [Close]      │
│  └┬───────────┘   └┬────────────┘                              │
│   │                └ 含全部子进程 ← 排查启动链必用             │
│   └ 仅该进程                                                   │
└────────────────────────────────────────────────────────────────┘
```

右键菜单项为 `Add process to Include filter` 与 `Add process and children to Include filter`。

**排查启动链时必用 Include Subtree**：某服务拉起了子进程，只过滤父进程会漏掉真正干活的子进程。Process Tree 同时也是「这个进程是谁启动的」的答案来源。

### 方法三：过滤器对话框（`Ctrl+L`）

```
┌─ Process Monitor Filter ───────────────────────────────────────────┐
│ Display entries matching these conditions:                         │
│ ┌──────────────┬──────────┬──────────────────┬──────────┐          │
│ │ Process Name▼│ is     ▼ │ yourapp.exe      │ Include▼ │          │
│ └──────────────┴──────────┴──────────────────┴──────────┘          │
│   ①字段          ②关系      ③值                ④动作               │
│                                    [Add]  [Remove]                 │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ ☑ Process Name  is        yourapp.exe            Include       │ │
│ │ ☑ Result        is        NAME NOT FOUND         Include       │ │
│ │ ☑ Process Name  is        Procmon64.exe          Exclude       │ │
│ │ ☑ Operation     begins w… FASTIO                 Exclude       │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                          [OK] [Cancel] [Apply]     │
└────────────────────────────────────────────────────────────────────┘
```

**规则语义：同字段多条 Include 是 OR，不同字段之间是 AND，Exclude 优先于 Include。**

关系下拉常用项：`is` / `is not` / `begins with` / `ends with` / `contains` / `excludes` / `less than` / `more than`。

### 方法四：按 PID 而非进程名

同名多实例时（多个 `svchost.exe`、多个 `python.exe`）必须按 PID：

```
PID  is  4728  Include
```

PID 从 Process Tree 或事件行的 PID 列读取。也可加 `Command Line` 列来区分实例，比 PID 直观。

### 方法五：工具栏类别开关

```
工具栏右侧五个切换按钮：
┌───┬───┬───┬───┬───┐
│🗂 │📁 │🌐 │⚙ │📈 │
└─┬─┴─┬─┴─┬─┴─┬─┴─┬─┘
  │   │   │   │   └ Profiling Events
  │   │   │   └ Process and Thread Activity
  │   │   └ Network Activity
  │   └ File System Activity
  └ Registry Activity
```

**这是降量最快的手段** —— 只排查文件问题就把其余四类关掉，事件量往往降一个数量级。v4.1 新增的 IPC 事件类是否有独立按钮以实际界面为准。

### 重置过滤器

`Ctrl+R`（`Filter → Reset Filter`）恢复**默认**过滤器（保留 Procmon 自身等系统降噪规则），**不是清空所有规则**。真要全清只能在过滤器对话框逐条 Remove。

> **对应 CLI：** `/NoFilter` 是真正的清空（`Clear the filter at start up`），语义与 `Ctrl+R` 不同。

**看不到任何事件时的检查顺序：**

```
① 状态栏 Showing 0 of 0        → 没采集：Capture Events 关着或类别开关全关
② 状态栏 Showing 0 of 87,331   → 采到了但被挡：Ctrl+L 看过滤器
③ 状态栏有数但看不到           → Auto Scroll 把视图冲走了，或滚动位置不对
```

## 过滤器的「非破坏性」真实含义

官方对过滤器的定性是「非破坏性」（non-destructive filters allow you to set filters without losing data），以及「过滤器可作用于任意数据字段，包括未被配置为列显示的字段」。

**这句话常被误读。** 非破坏性意味着：

- 设置/修改/移除过滤器**不影响已捕获的数据**，随时可反复调整视图；
- 但事件**仍然全量写入后备存储**——过滤器只作用于显示层。

所以只设过滤器**不能**减小 PML 体积或降低采集开销。要真正不采集，必须勾选 `Filter → Drop Filtered Events`。

代价是**不可逆**：被丢弃的事件永久丢失，事后发现过滤条件写窄了只能重新采集。

| 场景 | 是否勾选 Drop Filtered Events |
|---|---|
| 短时采集（< 1 分钟）、目标不明确 | ❌ 保留全量，事后反复调过滤器 |
| 长时间采集、目标进程明确 | ✅ 必须勾选，否则日志失控 |
| Boot logging | ✅ 勾选，启动期事件量极大 |
| 间歇性问题守候 | 用 [CLI 篇](procmon-cli.md#ring-bufferflight-recorder-模式)的 `/RingBuffer` 替代，无需丢弃 |

## 过滤条件实用配方

可存为 PMC 复用（见下节）。

**定位配置文件/DLL 探测失败：**
```
Operation      is           CreateFile        Include
Result         is           NAME NOT FOUND    Include
Process Name   is           yourapp.exe       Include
```

**定位权限问题：**
```
Result         is           ACCESS DENIED     Include
```
命中后必看 Detail 列的 `Desired Access`——请求 `Generic Write` 被拒和请求 `Read Attributes` 被拒是完全不同的问题。

**定位注册表配置项归因**（某 GUI 开关写到哪个键）：
```
Operation      begins with  RegSet            Include
Process Name   is           explorer.exe      Include
```
只过滤 `RegSetValue` 会漏掉 `RegSetInfoKey` 等，用 `begins with RegSet` 覆盖整族。这是官方节目演示的经典场景（以资源管理器「文件夹选项」对话框为例）。

**降噪：排除系统常态噪音**
```
Process Name   is           Procmon64.exe     Exclude
Process Name   is           System            Exclude
Operation      begins with  FASTIO            Exclude
Path           ends with    pagefile.sys      Exclude
```

**只看写操作**（排查「谁改了/删了我的文件」）：
```
Operation      is           WriteFile                      Include
Operation      is           SetRenameInformationFile       Include
Operation      is           SetDispositionInformationFile  Include
```

**删除文件在 Procmon 里叫 `SetDispositionInformationFile`，改名叫 `SetRenameInformationFile`** —— 没有叫 DeleteFile/RenameFile 的操作。写错过滤器会一条都匹配不到，且因为是「没有结果」而非报错，极易被误判成「不是文件被删的问题」。

## PMC 配置文件

过滤器 + 列布局 + 高亮规则可整体存为 `.pmc`（默认文件名 `ProcmonConfiguration.pmc`）。

```
Filter → Save Filter...        存为 .pmc
Filter → Load Filter    ▸      从子菜单选已存的
Filter → Organize Filters...   管理/重命名/删除
```

**团队协作与无人值守采集都应固化为 PMC**，而不是口头传递过滤条件。PMC 保存的是**完整配置快照**（含列顺序与高亮色），载入会整体覆盖当前设置。

> **对应 CLI：** `/LoadConfig <file>`。Procmon **没有**命令行设过滤器的开关，脚本化采集只能靠预先存好的 PMC。

## 保存 PML 文件

`File → Save`（`Ctrl+S`）弹出 **Save To File** 对话框：

```
┌─ Save To File ─────────────────────────────────────────────────┐
│ Events to save:                                                │
│   ○ All events                          → CLI: /SaveAs         │
│   ● Events displayed using current filter                      │
│                                         → CLI: /SaveApplyFilter│
│   ○ Highlighted events                  → 无 CLI 等价物        │
│                                                                │
│ Format:                                                        │
│   ● Native Process Monitor Format (PML)   ← 默认首选，无损     │
│   ○ Comma-Separated Values (CSV)          ← 给 Excel/脚本      │
│   ○ Extensible Markup Language (XML)      ← 唯一支持堆栈       │
│                                                                │
│   ☐ Include stack traces (will increase file size)             │
│                                         → CLI: /SaveAs1 (XML)  │
│   ☐ Resolve stack symbols (will be slow)                       │
│                                         → CLI: /SaveAs2 (XML)  │
│   ☐ Also include profiling events                              │
│                                                                │
│ Path: [C:\trace\cap.pml                          ] [...]       │
│                                              [OK] [Cancel]     │
└────────────────────────────────────────────────────────────────┘
```

括注 `(will increase file size)` 与 `(will be slow)` 是微软自己写在 UI 里的原文警告，不是第三方经验。

**格式选择：**

| 格式 | 用途 | 含堆栈 |
|---|---|---|
| **PML** | **给他人分析必须选这个。** 保留全部数据，可被另一个 Procmon 实例完整加载 | ✅ |
| CSV | Excel / 脚本分析 | ❌ |
| XML | 唯一支持导出堆栈的文本格式，体积膨胀数倍 | ✅（需勾选） |

PML 含敏感信息，外发前先脱敏（见「常见坑」）。

## 后备文件（Backing Files）

`File → Backing Files` 打开对话框，原文说明了两种存储的取舍：

```
┌─ Process Monitor Backing Files ────────────────────────────────┐
│ Process Monitor can store events in virtual memory (limited by │
│ the system commit limit), or in a file you specify (limited by  │
│ free disk space). Which do you prefer?                         │
│                                                                │
│   ● Use virtual memory        → CLI: /PagingFile               │
│   ○ Use file named:           → CLI: /BackingFile <path>       │
│     [C:\trace\cap.pml                            ] [...]       │
│                                                                │
│ These backing file objects are being used to store event data: │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ （当前使用的后备文件列表）                                 │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                      [OK]      │
└────────────────────────────────────────────────────────────────┘
```

**任何超过几分钟的采集都应切到文件模式** —— 虚拟内存模式受系统提交限制约束，会耗尽内存。

## 加列

`Options → Select Columns` 打开列选择器，v4.1 完整清单（分三组）：

```
┌─ Process Monitor Column Selection ─────────────────────────────┐
│ Select columns to appear in the Process Monitor window:        │
│                                                                │
│ Application Details          Event Details                     │
│  ☑ Process Name               ☐ Sequence Number                │
│  ☐ Image Path                 ☐ Event Class                    │
│  ☐ Command Line   ← 建议加    ☑ Operation                      │
│  ☐ Company Name               ☐ Date & Time                    │
│  ☐ Description                ☑ Time of Day                    │
│  ☐ Version                    ☐ Category                       │
│  ☐ Architecture  ← WOW64 排查 ☑ Path                           │
│                               ☑ Detail                         │
│ Process Management            ☑ Result                         │
│  ☐ User Name    ← 服务账户    ☐ Relative Time ← 对齐时间线     │
│  ☐ Session ID                 ☐ Duration      ← 耗时分析必加   │
│  ☐ Authentication ID                                           │
│  ☐ Integrity    ← UAC 排查                                     │
│  ☑ Process ID                                                  │
│  ☐ Thread ID                                                   │
│  ☐ Parent PID                                                  │
│  ☐ Virtualized                                                 │
│  ☐ Completion Time                                             │
│  ☐ Process Start                                               │
│                                          [OK] [Cancel]         │
└────────────────────────────────────────────────────────────────┘
```

值得加的六列及理由：

| 列 | 用途 |
|---|---|
| **Duration** | 耗时分析必须，默认不显示 |
| **Relative Time** | 对齐外部时间线（「用户点击按钮的那一刻」） |
| **Command Line** | 同名多实例时区分实例，比 PID 直观 |
| **Integrity** | 排查 UAC / 完整性级别导致的拒绝访问 |
| **User Name** | 排查服务账户权限问题 |
| **Architecture** | 排查 WOW64 重定向问题 |

## 事件属性与堆栈

双击任意事件打开 **Event Properties**，三个页签：

```
┌─ Event Properties ─────────────────────────────────────────────┐
│ ┌────────┬─────────┬───────┐                                   │
│ │ Event  │ Process │ Stack │  ← Ctrl+K 直达 Stack              │
│ └────────┴─────────┴───────┘                                   │
│                                                                │
│ [Event]   该操作的完整参数（Detail 列放不下的内容在这里）      │
│                                                                │
│ [Process] Name / Version / Path / Command Line / PID /         │
│           Parent PID / Session ID / User / Auth ID / Started / │
│           Architecture / Virtualized / Integrity / Ended /     │
│           Modules（已加载模块列表）                            │
│                                                                │
│ [Stack]   Frame  Module        Location            Address     │
│           0      ntoskrnl.exe  NtCreateFile+0x1a   0xfff…      │
│           …                                                    │
│           12     yourapp.exe   LoadConfig+0x3c     0x7ff…  ←── │ 业务代码
│                                                                │
│        [Next Highlighted] [Copy All] [Source...] [Close]       │
└────────────────────────────────────────────────────────────────┘
```

**读栈的实用判据：** 从栈底往上找**第一个属于被排查程序自身模块**的帧（而不是从栈顶看内核帧），那里通常才是发起该操作的业务代码位置。

未配符号时 Stack 页签会弹警告，原文：

> Symbols are not currently configured. You must configure symbols in order to view thread stack information.

另一条更隐蔽的：

> The version of Dbghelp.dll configured does not support the Microsoft Symbol Server.

第二条意味着 DbgHelp.dll 版本不够 —— 需装 Debugging Tools for Windows 取得较新的 DbgHelp。

## 配置符号

`Options → Configure Symbols`：

```
┌─ Configure Symbols ────────────────────────────────────────────┐
│ Process Monitor uses symbols to resolve function names when    │
│ displaying thread stack locations on the Stack page of an      │
│ event's properties dialog. If you do not require that          │
│ information you do not need to configure symbols.              │
│                                                                │
│ DbgHelp.dll path (version 6.0 or later):                       │
│ [C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\dbghelp… ] [...]│
│                                                                │
│ Symbol paths:                                                  │
│ [srv*C:\Symbols*https://msdl.microsoft.com/download/symbols  ] [...]│
│                                                                │
│ Source code paths:                                             │
│ [                                                            ] [...]│
│                     When displaying stack traces for modules   │
│                     for which you have both symbols and source │
│                     code available Process Monitor can let you │
│                     view the source associated with a stack    │
│                     frame.                                     │
│                                              [OK] [Cancel]     │
└────────────────────────────────────────────────────────────────┘
```

符号路径语法见 [00-suite-setup.md](00-suite-setup.md#符号配置)。

**关键坑（官方 Process Explorer 页面明示，Procmon 同理）：** 配置的 DBGHELP.DLL 所在目录必须同时包含支持所用服务器路径的 SYMSRV.DLL，否则符号解析不可用。

> **对应 CLI：** 无。符号只能在 GUI 配置（写入注册表后 CLI 导出的 `/SaveAs2` 才能解析符号）。

## Result 值的误诊陷阱

这是 Procmon 排查中错误率最高的环节。以下判据直接决定你追的是根因还是噪音。

### `NAME NOT FOUND` — 默认是噪音

程序按固定顺序在多个候选路径探测配置文件/DLL，找不到就换下一个，这是**设计如此**的探测链。一次成功的加载往往伴随十几条 `NAME NOT FOUND`。

**判断它是否是根因，看后续序列：**

| 序列形态 | 结论 |
|---|---|
| 多条 `NAME NOT FOUND` 后出现同名文件的 `SUCCESS` | 噪音。探测链正常收敛，程序找到了 |
| 多条 `NAME NOT FOUND` 后**没有**任何 `SUCCESS`，紧接着进程报错或退出 | **根因**。探测链耗尽 |
| 单条 `NAME NOT FOUND`，路径明显拼错/带异常前缀 | 可疑，值得追 |

实操方法：在命中行右键 → `Include` 该 Path 的文件名（去掉目录），把过滤器改为只看这一个文件名的全部操作，即可一眼看出探测链是否收敛。

### `BUFFER OVERFLOW` / `BUFFER TOO SMALL` — 几乎总是噪音

Windows API 的标准两次调用模式：第一次传 NULL 或小缓冲区询问「需要多大空间」，内核返回 `BUFFER OVERFLOW` 并告知所需长度，第二次分配足够空间再调。**成对出现且第二次 `SUCCESS` 就是正常的。**

只有当同一请求反复 `BUFFER OVERFLOW` 且始终没有成功的后续调用时，才可能是程序缓冲区管理有问题。

### `ACCESS DENIED` — 通常是根因，但要看清请求的是什么

必须结合 Detail 列的 `Desired Access` 判断：

- 请求 `Generic Write` / `Delete` 被拒 → 权限或 ACL 问题，正常方向
- 请求 `Read Attributes` 被拒 → 更可能是路径在受保护位置，或有 EDR/AV 拦截
- 对同一路径先 `ACCESS DENIED`、随后换路径 `SUCCESS` → 程序有降级逻辑，不是故障

### `SHARING VIOLATION` — 指向文件锁定

有别的进程以不兼容的共享模式打开了该文件。Procmon 只告诉你被拒，**不告诉你是谁持有** —— 切到 [Process Explorer](process-explorer-gui.md) 的 Find Handle 或 [Handle](handle.md) 定位持有者。

### `FAST IO DISALLOWED` — 纯噪音

内核尝试快速 I/O 路径失败，自动回退到常规 IRP 路径。用 `Operation begins with FASTIO → Exclude` 过滤掉。

### `REPARSE` — 不是错误

遇到符号链接/联接点/挂载点，I/O 被重新解析到目标路径。后面紧跟着对真实路径的操作。

## 耗时分析

- **Relative Time** — 相对采集起点的偏移，对齐外部时间线
- **Duration** — 单个操作耗时，**默认不显示**，需在 `Options → Select Columns` 加

标准路径：加 Duration 列 → 按 Duration 降序排序 → 看排在最前的操作类型与路径。常见结论是某个网络路径或被 AV 扫描拦截的文件访问吃掉了几百毫秒。

`Tools → File Summary` 直接按路径给出汇总耗时，比手工排序更快定位热点文件。

## 定位与导航

| 操作 | 快捷键 | 用途 |
|---|---|---|
| Find | `Ctrl+F` | 全文搜索，官方特性列表提到搜索可取消（cancellable search） |
| Toggle Bookmark | `Ctrl+B` | 标记关键事件，配合 `Find Bookmark` 在长 trace 中往返 |
| **Jump To** | `Ctrl+J` | **从事件跳到对应的注册表键或文件系统位置**（直接打开注册表编辑器/资源管理器定位），排查「这个键到底在哪」时极省事 |
| Search Online | — | 用该事件的路径/操作去搜索引擎查 |
| Auto Scroll | `Ctrl+A` | 采集中自动滚到最新；**分析时务必关掉** |
| Count Occurrences | — | 按指定列统计各值出现次数，快速看分布 |

`Jump To` 对某些事件类不可用，会提示 `Jump not implemented for this event class`。

## Tools 菜单的汇总报告

| 报告 | 快捷键 | 用途 |
|---|---|---|
| `System Details` | — | 系统信息概览 |
| `Process Tree` | `Ctrl+T` | 进程父子关系，筛选进程的入口 |
| `Process Activity Summary` | — | 各进程操作量对比，找「谁在狂读盘」 |
| `File Summary` | — | 按文件路径汇总，含耗时——**定位热点文件的首选** |
| `Registry Summary` | — | 按注册表路径汇总 |
| `Stack Summary` | — | 按调用栈汇总，找重复触发的代码路径 |
| `Network Summary` | — | 按网络端点汇总 |
| `Cross Reference Summary` | — | 找**多个进程共同访问**的路径，排查资源争用 |
| `Count Occurrences` | — | 按列统计值分布 |

**所有 Summary 的作用域都是「当前过滤器命中的事件」**，不是全量。过滤器设窄了汇总数据随之失真 —— 看汇总前先确认过滤器状态与状态栏的 `Showing X of Y`。

## Boot logging

`Options → Enable Boot Logging` 勾选 → 重启 → 重启后启动 Procmon，会提示发现 boot 日志并询问保存位置。

**抓取与分析不在同一次会话内完成。**

- **只生效一次**，不是持久设置。每次要抓都得重新勾选。
- 启动期事件量极大，务必配合 Drop Filtered Events 或预置窄过滤器。
- Boot 日志中间文件由驱动写在系统盘上（官方未记载确切路径）。不去转换会一直占磁盘。
- Boot logging 期间系统启动明显变慢。

> **对应 CLI：** `/EnableBootLogging` 配置，`/ConvertBootLog <PML>` 重启后转换。见 [CLI 篇](procmon-cli.md#boot-logging)。

## 典型 GUI 排查流程

以「程序启动报找不到配置文件」为例：

```
① 启动 Procmon，File → Capture Events 取消勾选
② Ctrl+X 清屏
③ Ctrl+L 加 Process Name is yourapp.exe → Include，Apply
④ 工具栏只留 File System 类别（关掉其余四个）
⑤ 勾选 Capture Events 开始采集
⑥ 启动被排查的程序，等它报错
⑦ 取消 Capture Events 停止采集
⑧ Ctrl+L 追加 Result is NAME NOT FOUND → Include
⑨ 看路径序列：探测链是否收敛到 SUCCESS？
      未收敛 → 最后几条即根因
      已收敛 → 是噪音，回到 ⑧ 换 ACCESS DENIED 或 SHARING VIOLATION
⑩ 双击关键事件 → Stack 页签（Ctrl+K）看发起该操作的代码位置
⑪ File → Save 存 PML 留档（格式选 PML，脱敏后再外发）
```

## GUI 侧常见坑

1. **启动即全量采集。** 几秒堆积数万条。先停采集、清屏、配过滤器再开。
2. **过滤器 ≠ 不采集。** 见「非破坏性的真实含义」。这是最高频的误解。
3. **上次的过滤器会被保留。** Procmon 退出时保存过滤器，下次启动仍生效并弹确认框。
4. **`Ctrl+R` Reset Filter 不是清空。** 它恢复默认过滤器（含系统降噪规则）。
5. **删除操作不叫 DeleteFile。** 是 `SetDispositionInformationFile`，改名是 `SetRenameInformationFile`。写错过滤器一条都匹配不到，且不报错。
6. **Duration 列默认不显示。** 耗时分析必须先加列。
7. **Summary 报告受过滤器影响。** 所有 Tools 下的汇总都只统计过滤器命中的事件。
8. **CSV 导出不含堆栈。** 需要堆栈只能选 XML 并勾选相应选项。
9. **默认用虚拟内存做后备存储**，长时间采集会耗尽内存。切到 `File → Backing Files` 文件模式。
10. **Theme 切换需重启 Procmon 生效。**
11. **符号配置有两个独立失败点：** 符号路径写错，或 DbgHelp.dll 版本过旧。另外 DBGHELP.DLL 所在目录必须同时含匹配的 SYMSRV.DLL。
12. **`Auto Scroll` 分析时要关掉**，否则视图被不停冲走。
13. **PML 含敏感信息。** 官方 EULA 明确警示可能包含用户名、密码、访问过的文件与注册表路径。外发前脱敏。
14. **Bookmark 对只读文件不可用**，提示 `Bookmarks are not enabled because the file is read-only.`

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/procmon
- 文档源文件：https://github.com/MicrosoftDocs/sysinternals/blob/live/sysinternals/downloads/procmon.md
- **工具自带：`Help → Help`** 打开随包帮助文件 —— 官方页面把详细用法明确下放给这里
- 更深入的实战案例：《Windows Sysinternals Administrator's Reference》（Mark Russinovich & Aaron Margosis）

> **本篇事实边界：** 官方页面（396 词）只覆盖定位、能力清单、下载与运行环境。**菜单结构、快捷键、对话框选项与原文提示均提取自 `Procmon64.exe` v4.1 二进制资源**，与实际界面一致但官方网页无记载。ASCII 布局图为按资源结构绘制的示意，标注面板划分与控件位置，非像素级还原。Result 值判据、读栈方法、排查流程为实践经验总结。菜单项已按 v4.1 核对，不采用网上流传的旧版菜单位置。


