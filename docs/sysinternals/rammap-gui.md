# RAMMap — 图形界面

**v1.63（2026-03-26）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/rammap
**CLI 篇：** [rammap-cli.md](rammap-cli.md)

> **官方页面信息很少（325 词）：** 给了定位、7 个选项卡的名称、刷新与快照保存/加载能力、支持范围与下载体积。**不含版本号、命令行参数或 Empty/purge 类清空操作的任何说明**，各标签含义与内存管理器算法被外链到《Windows Internals, 5th Edition》。本篇菜单结构与 CLI 参数提取自 `RAMMap64.exe` v1.63 二进制资源。

## 定位与边界

分析**系统整体**的物理内存使用：Windows 如何分配物理内存、多少文件数据被缓存在 RAM 中、内核与设备驱动占用多少 RAM。

**RAMMap 是系统视角，VMMap 是进程视角。**

| 问题 | 用哪个 |
|---|---|
| 「系统内存吃紧，到底谁占的」 | **RAMMap** |
| 「多少内存被文件缓存占了」 | **RAMMap** 的 File Summary |
| 「内核/驱动占了多少」 | **RAMMap** 的 Use Counts |
| 「这个进程的内存用在哪了」 | [VMMap](vmmap-gui.md) |
| 「进程内存泄漏在哪类内存」 | [VMMap](vmmap-gui.md) |
| 「基准测试前重置内存状态」 | **RAMMap** 的 Empty 系列（见 [CLI 篇](rammap-cli.md)） |

支持范围：客户端 Windows Vista 及更高，服务器 Windows Server 2008 及更高（是本目录中支持范围最宽的工具）。

## 七个选项卡（官方定义）

| 选项卡 | 官方说明（译） | 排查用途 |
|---|---|---|
| **Use Counts** | 按类型与分页列表汇总 | **首屏总览**，先看这里 |
| **Processes** | 各进程工作集大小 | 找出占用最多的进程 |
| **Priority Summary** | 按优先级的 standby 列表大小 | 待命内存的优先级分布 |
| **Physical Pages** | 每一页的用途 | 极细粒度，页级归因 |
| **Physical Ranges** | 物理内存地址区间 | 硬件保留区、内存空洞 |
| **File Summary** | 按文件统计 RAM 中的文件数据 | **「谁把内存吃在文件缓存上」** |
| **File Details** | 按文件列出各物理页 | File Summary 的下钻 |

## 主窗口布局

```
┌─ RAMMap ───────────────────────────────────────────────────────────────┐
│ File  Empty  Settings  Help                                            │ ← 菜单栏（只有4个）
├────────────────────────────────────────────────────────────────────────┤
│ Use Counts│Processes│Priority Summary│Physical Pages│Physical Ranges│…  │ ← 7 个选项卡
│ └─ 先看这个                                          File Summary ─┘   │
├────────────────────────────────────────────────────────────────────────┤
│                Total    Active   Standby  Modified  Modified  Transi…  │
│                                                     No Write           │
│ Total       16,384 MB  9,210 MB 5,880 MB   102 MB      0 MB    12 MB   │
│ Process Priv 4,120 MB  4,020 MB   100 MB     0 MB                      │
│ Mapped File  6,880 MB  1,210 MB 5,600 MB    70 MB              ←────── │ 文件缓存
│ Shareable      420 MB    380 MB    40 MB     0 MB                      │
│ Page Table     180 MB    180 MB     0 MB                               │
│ Paged Pool     620 MB    600 MB    20 MB                               │
│ Nonpaged Pool  480 MB    480 MB                        ←────────────── │ 不可换出
│ Driver Locked  210 MB    210 MB                                        │
│ Unused          … MB                                                   │
└────────────────────────────────────────────────────────────────────────┘
```

### 读 Use Counts 的关键判据

**列的含义（分页列表状态）：**

| 列 | 含义 |
|---|---|
| **Active** | 正在被某个工作集使用 |
| **Standby** | 待命 —— **已不在工作集，但内容仍有效，可直接复用**。这是「缓存」 |
| **Modified** | 已修改待写回页面文件/磁盘 |
| **Modified No Write** | 已修改但不写回 |
| **Transition** | 正在 I/O 中的过渡状态 |

**行的诊断意义：**

- **`Standby` 总量大 = 正常。** 这是 Windows 在用空闲内存做缓存，需要时会立刻释放。**「可用内存少」不等于内存不足** —— 这是最常见的误判。
- **`Nonpaged Pool` 异常大 → 驱动泄漏。** 非分页池不能换出，只能由内核/驱动分配。持续增长基本可确定是驱动 bug。
- **`Paged Pool` 异常大 → 内核对象泄漏**（句柄、注册表键等）。
- **`Driver Locked` 大 → 驱动锁定了物理页**，常见于显卡/虚拟化。
- **`Mapped File` 的 Standby 大 = 文件缓存**，正常。切到 File Summary 看是哪些文件。

### File Summary 的用途

**「内存都被某个大文件的缓存吃了」是很常见的场景** —— 备份程序、日志、数据库文件、虚拟机磁盘映像。

```
① 切到 File Summary 选项卡
② 按 Total 列降序排序
③ 看排最前的文件路径
④ 需要页级细节 → File Details
```

结论通常是「某个进程在顺序读一个巨大文件，把整个缓存冲掉了」（cache thrashing）。处置方向是让该程序用非缓冲 I/O（`FILE_FLAG_NO_BUFFERING`），而不是清空缓存。

## 菜单结构

```
File                    Empty                              Settings    Help
├ Open...               ├ Empty Working Sets               └ Colors    ├ Usage
├ Save...               ├ Empty System Working Set                     └ About
├ Find      Ctrl+F      ├ Empty Modified Page List                        ↑
├ Refresh   F5          ├ Empty Standby List                          CLI 参数表在这
└ Exit                  └ Empty Priority 0 Standby List
                            ↑ 五个破坏性操作，见下
```

菜单极简 —— RAMMap 的复杂度全在数据呈现，不在操作。

## Empty 系列：五个破坏性操作

> **⚠ 这五项都是破坏性操作，不要在生产环境随手用。** 官方页面对它们**没有任何说明**（本节来自二进制资源与内存管理原理）。

| 操作 | 作用 | 后果 |
|---|---|---|
| **Empty Working Sets** | 清空所有进程的工作集 | 全系统卡顿，所有进程需重新从磁盘/页面文件读回 |
| **Empty System Working Set** | 清空系统（内核）工作集 | 内核代码/数据需重新读回，卡顿更明显 |
| **Empty Modified Page List** | 把已修改页写回并释放 | 触发磁盘写入峰值 |
| **Empty Standby List** | 清空待命列表（**即清空文件缓存**） | **后续文件访问全部落盘**，I/O 峰值持续较长时间 |
| **Empty Priority 0 Standby List** | 只清优先级 0 的待命页 | 比上一项温和，只清最低优先级的缓存 |

### 唯一的合法用途：基准测试前重置

**这些操作的正当场景只有一个 —— 让每一轮基准测试从相同的冷缓存状态开始。**

不清空的话，第一轮测试把文件读进缓存，第二轮直接命中缓存，结果会快得离谱且不可比。

```
① Empty → Empty Standby List    （清掉文件缓存）
② 跑一轮基准测试，记录
③ 重复 ①②，取多轮均值
```

**用 Empty 系列来「优化内存占用」是自欺欺人** —— 页会很快回来，而且中间付出了大量磁盘 I/O。任何声称「清内存加速系统」的说法都是错的：Standby 列表本来就是随时可释放的，清空它只会让系统重新读盘。

命令行等价物是 `RAMMap -E[wsmt0]`，**这是本目录中最有实用价值的「官方无文档」发现** —— 基准测试脚本可以直接调用，见 [CLI 篇](rammap-cli.md)。

## 快照对比

`File → Save` / `File → Open` 保存与加载内存快照（`.rmp`），可对比两个时间点的物理内存分布。

```
① 系统内存正常时 File → Save 存基线
② 问题出现后 F5 刷新
③ File → Open 打开基线对比
④ 看哪一行（类型）或哪个文件的占用明显增长
```

排查缓慢的内存泄漏（几小时/几天）时，定时采集快照比盯实时视图有效 —— 见 [CLI 篇](rammap-cli.md) 的定时采样配方。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 参数 |
|---|---|
| `File → Save`（`.rmp`） | `<outputfile>` 位置参数（采集后退出） |
| `File → Open` | `-o <inputfile.rmp>` |
| 在 64 位系统上跑 32 位版 | `-run32` |
| `Empty → Empty Working Sets` | `-Ew` |
| `Empty → Empty System Working Set` | `-Es` |
| `Empty → Empty Modified Page List` | `-Em` |
| `Empty → Empty Standby List` | `-Et` |
| `Empty → Empty Priority 0 Standby List` | `-E0` |
| 首次运行 EULA 弹窗 | `-accepteula` |
| 七个选项卡的交互浏览 | **无**（CLI 只能整体导出） |
| `File → Find`（`Ctrl+F`） | **无** |
| `F5` 刷新 | **无** → 重复调用 |
| `Settings → Colors` | **无** |

**五个 Empty 操作全都有 CLI 等价物** —— 这是 RAMMap 与 VMMap 的重要差别（VMMap 的 `Empty Working Set` 没有 CLI 开关）。

## GUI 侧常见坑

1. **官方页面对 Empty 系列一字未提。** 五个破坏性操作没有任何官方警告，也没有 CLI 参数文档 —— 都在工具的 `Help → Usage` 里。
2. **`Standby` 大不等于内存不足。** 这是最常见的误判。Windows 用空闲内存做缓存是正确行为。
3. **Empty 系列不能「优化内存」。** 页会很快回来，中间付出大量 I/O。唯一正当用途是基准测试前重置。
4. **`Empty Standby List` 会造成持续的 I/O 峰值。** 在生产环境执行可能引发服务超时。
5. **`Nonpaged Pool` 持续增长基本可确定是驱动泄漏。** 这类问题应用层无法解决。
6. **需管理员权限。** 读取物理内存信息与执行 Empty 操作都需要提权。
7. **各标签含义官方未定义**，被外链到《Windows Internals, 5th Edition》—— 该书版本较旧（对应 Windows 7 时代），新版内存管理细节有变化。
8. **File Details 数据量极大**（按物理页列出），大内存机器上打开会很慢。

## 分发

`RAMMap.zip`（约 719 KB）。Sysinternals Live：`https://live.sysinternals.com/RAMMap.exe`

```
RAMMap.exe    743,488   x86      RAMMap64.exe   397,848   x64
```

winget 包名 `Microsoft.Sysinternals.RAMMap`。
支持范围：客户端 Windows Vista+，服务器 Windows Server 2008+。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/rammap（325 词，仅概览）
- **工具自带：`Help → Usage`** —— CLI 参数表的唯一权威来源
- 内存管理原理：《Windows Internals》（官方外链的是 5th Edition）

> **本篇事实边界：** 官方页面提供了定位、7 个选项卡名称与说明、刷新与快照保存/加载能力、支持范围（Vista+/Server 2008+）与体积（719 KB）。**菜单结构、五个 Empty 操作、CLI 参数均提取自 `RAMMap64.exe` v1.63 二进制资源，官方页面对 Empty 与 CLI 完全无记载。** 列含义（Active/Standby/Modified 等）、诊断判据（Nonpaged Pool 泄漏、Standby 误判、cache thrashing）、基准测试用法为实践经验与内存管理原理总结。
