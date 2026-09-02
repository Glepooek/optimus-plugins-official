# VMMap — 图形界面

**v3.4（2023-10-18，维护停滞）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/vmmap
**CLI 篇：** [vmmap-cli.md](vmmap-cli.md)

> **维护状态：** v3.4 发布于 2023-10-18，官方索引页 What's New 时间线（2026-03 至 2026-08）中无 VMMap 更新条目。
>
> **官方页面信息极少（277 词）：** 只给了定位、「支持多种格式导出含可重载的原生格式」、「提供命令行选项以支持脚本化场景」（**不列出参数名**）、运行环境与下载体积。**不含版本号、命令行参数、内存类型枚举、快照对比或调用栈追踪的具体说明。** 本篇菜单结构、内存类型定义、CLI 参数均提取自 `vmmap64.exe` v3.4 二进制资源。

## 定位与边界

分析**单个进程**的虚拟内存与物理内存（工作集）使用：按已提交虚拟内存类型分解，并显示操作系统分配给各类型的物理内存量。

**VMMap 是进程视角，RAMMap 是系统视角** —— 这是两者最重要的分工：

| 问题 | 用哪个 |
|---|---|
| 「这个进程的内存都用在哪了」 | **VMMap** |
| 「进程内存持续增长，泄漏在哪类内存」 | **VMMap** 快照对比 |
| 「系统整体内存吃紧，谁占的」 | [RAMMap](rammap-gui.md) |
| 「多少内存被文件缓存占了」 | [RAMMap](rammap-gui.md) |
| 「句柄泄漏」（不是内存） | [Process Explorer](process-explorer-gui.md) |
| 「抓内存快照做事后分析」 | [ProcDump](procdump.md) |

## 内存类型（官方 Quick Help 原文）

VMMap 把内存分为若干类型，二进制内嵌的 Quick Help 给出了定义 —— **这是官方网页上完全没有的内容**：

| 类型 | 官方定义（译） |
|---|---|
| **Image** | 该内存代表一个可执行文件，Details 列显示文件路径 |
| **Mapped File** | 该内存代表磁盘上的一个文件，Details 列显示文件路径。映射文件通常包含应用数据 |
| **Shareable** | 可与其他进程共享，计入系统提交限制，通常包含不同进程间 DLL 共享的数据或进程间通信消息 |
| **Heap** | 由用户态堆管理器管理的内存，与 Private 一样计入系统提交限制，包含应用数据 |
| **Stack** | 存放函数参数、局部变量与函数调用记录，按线程分配。计入提交限制，通常按需增长 |
| **Private** | 进程私有，计入提交限制 |
| **Free** / **Unusable** | 未提交 / 因对齐无法使用（默认隐藏，见下） |

**排查内存泄漏时看哪一类，直接决定后续方向：**

- **Heap 增长** → 应用 `malloc`/`new` 未释放，或托管堆未回收
- **Private 增长** → 直接 `VirtualAlloc` 未释放
- **Stack 增长** → 线程数暴涨（每线程一个栈），查线程泄漏
- **Mapped File 增长** → 文件映射未关闭
- **Image 增长** → DLL 反复加载未卸载

## 主窗口布局

```
┌─ VMMap - YourApp.exe (4728) ───────────────────────────────────────────┐
│ File  Edit  View  Tools  Options  Help                                 │
├────────────────────────────────────────────────────────────────────────┤
│ Committed  Private Bytes  Working Set                                  │ ← 摘要条
│  842,120 K     512,400 K     380,220 K                                 │
├────────────────────────────────────────────────────────────────────────┤
│ Type          Size      Committed  Private  Total WS  Private WS  …    │ ← 上窗格
│ Total       2,097,152     842,120  512,400   380,220     301,10…       │   按类型汇总
│ Image          48,220      48,220    2,104    31,208       2,104       │
│ Mapped File    12,400      12,400        0     8,120           0       │
│ Shareable      88,100      88,100        0    41,220           0       │
│ Heap          420,800     420,800  420,800   248,600     248,600  ←─── │ 泄漏嫌疑
│ Managed Heap   62,400      62,400   62,400    38,100      38,100       │
│ Stack          16,384       8,200    8,200     4,100       4,100       │
│ Private Data  204,800     202,000  19,896     8,872       6,296        │
│ Free        1,255,048           0        0         0           0       │
├────────────────────────────────────────────────────────────────────────┤
│ Address        Type    Size    Committed  Protection      Details      │ ← 下窗格
│ 0x00007FF6…    Image     420        420   Execute/Read    C:\app\a.exe │   选中类型的
│ 0x0000021C…    Heap    1,024      1,024   Read/Write                  │   明细区域
│ 0x0000021D…    Heap    2,048      2,048   Read/Write                  │
└────────────────────────────────────────────────────────────────────────┘
```

## 菜单结构

```
File                        Edit                    View
├ Select Process... Ctrl+P  ├ Copy Address  Ctrl+C  ├ Expand All
├ Open...          Ctrl+O   ├ Copy All      Ctrl+A  ├ Collapse All
├ Save            Ctrl+S    └ Find          Ctrl+F  ├ Strings          Ctrl+T
├ Save As...                                        ├ Fragmentation View  ← 见下
└ Exit                      Tools                   └ Refresh
                            └ Empty Working Set Ctrl+E
Options                          ← 见下警告        Help
├ ☐ Show Free and Unusable Regions                 ├ Help
├ Trace Snapshot Interval  ▸                        ├ Quick Help  ← 内存类型定义在这
│ ├ 1 second / 2 / 5 / 10 seconds                   ├ Command-line Options  ← CLI 表在这
│ └ Paused                 Ctrl+Space               └ About
├ Font...
├ Colors
└ Configure Symbols...
```

## 选择进程

`File → Select Process`（`Ctrl+P`）打开进程选择对话框。两种模式：

**① 附加到已运行的进程** —— 常规用法，取当前快照。

**② 从 VMMap 启动应用（instrumented 模式）** —— 官方 Quick Help 原文：

> When you launch an application from Vmmap the application is instrumented to track individual memory allocations (HeapAlloc, VirtualAlloc, etc) along with the associated call stack.

**这是 VMMap 最强但最少人知道的能力，官方网页完全没提。** 从 VMMap 启动应用后，它会插桩跟踪**每一次内存分配及其调用栈** —— 这意味着你能直接看到「是哪行代码分配了这块没释放的内存」，而不只是「Heap 涨了 200MB」。

代价：插桩有性能开销，且必须由 VMMap 启动（不能附加到已运行的进程）。排查内存泄漏时，**如果能重启目标应用，优先用这个模式**。

`Options → Trace Snapshot Interval` 控制插桩模式下的快照间隔（1/2/5/10 秒或暂停）。

## 快照对比：定位泄漏

VMMap 支持保存与加载快照，这是泄漏归因的基础手段：

```
① 应用刚启动、稳定后 → File → Save（存为 .mmp 原生格式）
② 执行怀疑泄漏的操作 N 次（比如打开关闭某窗口 100 次）
③ View → Refresh
④ 对比当前值与快照：哪个 Type 行的 Committed/Private 明显增长
⑤ 该类型下窗格找出新增的地址区域
⑥ 若用 instrumented 模式启动，可直接看该区域的分配调用栈
```

**「某个应用功能的内存开销」也用同样方法** —— 官方页面提到 VMMap 的内置过滤与刷新能力正是为此设计。

## 碎片视图

`View → Fragmentation View` 以图形方式展示地址空间布局。

**用途：诊断「内存够但分配失败」** —— 32 位进程（或 WOW64 下的 32 位进程）地址空间只有 2-4 GB，长期运行后即使总空闲量充足，也可能因碎片化而无法满足一次大块连续分配。碎片视图能直观看出空闲块是否被切碎。

64 位进程的地址空间极大，碎片通常不是问题。

## Strings 视图

`View → Strings`（`Ctrl+T`）提取选中内存区域中的字符串。

用途：确认某块匿名内存到底装的是什么（配置数据？缓存的响应？泄漏的日志？）。这是 [Strings](strings-sigcheck.md) 工具的进程内存版本。

> **⚠** 进程内存中的字符串可能包含密码、令牌、个人信息。导出或外发前必须脱敏（官方 EULA 明确警示 Sysinternals 工具保存的文件可能包含敏感信息）。

## Empty Working Set

`Tools → Empty Working Set`（`Ctrl+E`）清空目标进程的工作集，把物理页推回待命列表。

> **⚠ 这是破坏性操作，不要在生产环境随手用。** 清空后进程需要重新从磁盘/页面文件读回数据，会造成明显的卡顿与磁盘 I/O 峰值。
>
> **合法用途只有一个：** 测量「进程真正需要常驻多少内存」—— 清空后观察工作集回升到多少并稳定，那个值才是真实需求。用它来「优化内存占用」是自欺欺人，页很快会回来。

## 显示空闲区域

`Options → Show Free and Unusable Regions` 默认关闭。

打开后能看到 `Free`（未提交）与 `Unusable`（因对齐无法使用）区域 —— 做碎片分析时需要打开，日常看内存占用时关掉更清爽。

## 符号配置

`Options → Configure Symbols` —— instrumented 模式下解析分配调用栈需要符号，否则栈帧只有模块名+偏移。

符号路径语法见 [00-suite-setup.md](00-suite-setup.md#符号配置)。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 参数 |
|---|---|
| `File → Select Process` 附加到进程 | `-p <pid 或进程名>` |
| `File → Save`（`.mmp`） | `-p <目标> <outputfile>` |
| `File → Save As` 选 XML / CSV | 输出文件扩展名写 `.xml` / `.csv` |
| `File → Open` 载入快照 | `-o <inputfile>` |
| 在 64 位系统上分析 32 位进程 | `-64` |
| 首次运行 EULA 弹窗 | `-accepteula` |
| instrumented 启动模式 | **无** |
| `View → Fragmentation View` | **无** |
| `View → Strings` | **无** |
| `Tools → Empty Working Set` | **无** |
| `Options → Trace Snapshot Interval` | **无** |
| `Options → Configure Symbols` | **无** |

完整 CLI 说明见 [vmmap-cli.md](vmmap-cli.md)。

## GUI 侧常见坑

1. **官方页面几乎什么都没说（277 词）。** 内存类型定义在 `Help → Quick Help`，CLI 参数在 `Help → Command-line Options` —— 都在工具里，不在网上。
2. **instrumented 模式必须由 VMMap 启动应用**，不能附加到已运行的进程。排查泄漏前先想清楚能否重启目标。
3. **`Empty Working Set` 是破坏性操作。** 会造成卡顿与 I/O 峰值，只用于测量真实内存需求。
4. **`Show Free and Unusable Regions` 默认关闭。** 做碎片分析必须打开。
5. **VMMap 是进程视角。** 「系统整体内存去哪了」要用 [RAMMap](rammap-gui.md)。
6. **需管理员权限才能分析其他用户/系统进程。**
7. **32 位/64 位要匹配。** 在 64 位系统上分析 32 位进程用 `-64`（CLI）或对应版本。
8. **Strings 视图可能含密码令牌。** 外发前脱敏。
9. **维护停滞（2023-10-18）。**

## 分发

`vmmap.zip`（约 7.6 MB）。Sysinternals Live：`https://live.sysinternals.com/vmmap.exe`
运行环境：客户端 Windows 10+，服务器 Windows Server 2016+。

```
vmmap.exe      5,193,152   x86      vmmap64.exe   2,758,064   x64
```

winget 包名 `Microsoft.Sysinternals.VMMap`。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/vmmap（277 词，仅概览）
- **工具自带：`Help → Quick Help`**（内存类型定义）、**`Help → Command-line Options`**（CLI 参数表）
- 更深入的内容：《Windows Sysinternals Administrator's Reference》

> **本篇事实边界：** 官方页面只有定位、「支持多格式导出含可重载原生格式」、「提供命令行选项」（不列参数）、运行环境与体积。**内存类型定义（Image/Shareable/Mapped File/Heap/Stack）、instrumented 分配跟踪说明、菜单结构、CLI 参数均提取自 `vmmap64.exe` v3.4 二进制资源**，官方网页无记载。泄漏归因流程、类型增长的诊断映射、`Empty Working Set` 的用途取舍、碎片视图的适用场景为实践经验总结。
