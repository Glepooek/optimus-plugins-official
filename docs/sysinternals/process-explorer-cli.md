# Process Explorer — 命令行

**v17.13（2026-08-12）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer
**GUI 篇：** [process-explorer-gui.md](process-explorer-gui.md)（主体在此，本篇很短）

> **本篇很薄是符合事实的。** Process Explorer 的能力几乎全在 GUI，命令行**只管启动姿态**（以什么权限、什么窗口状态启动），没有任何「命令行查询/输出」能力。需要脚本化查句柄用 [Handle](handle.md)，脚本化抓 dump 用 [ProcDump](procdump.md)。
>
> 官方页面**不含任何命令行参数说明**。下表来自 `procexp64.exe` v17.13 二进制资源与官方 Defrag Tools 节目。

## 开关表

| 开关 | 说明 | 来源 |
|---|---|---|
| `/accepteula` | 自动接受 Sysinternals EULA，不弹对话框。脚本化必用 | 二进制资源（`-accepteula` 亦可） |
| `/e` | 以提升权限（elevated）启动 | 官方节目 |
| `/t` | 最小化到通知区托盘启动 | 官方节目 |
| `/rt` | 二进制内嵌，官方无说明 | 二进制资源 |

**开关总量就这些。** 没有指定进程、导出列表、查询句柄的命令行能力。

## `/t /e` 顺序敏感

官方节目给出的「让 Process Explorer 常驻运行」推荐做法：

```powershell
procexp.exe /t /e
```

**这两个开关顺序敏感（order sensitive）—— `/t /e` 与 `/e /t` 行为不等价。** 官方节目明确点出这一点但未解释原因。按推荐顺序写即可：

```powershell
# 正确
procexp64.exe /accepteula /t /e

# 不等价，避免
procexp64.exe /accepteula /e /t
```

配合 GUI 侧的 `Options → Hide When Minimized` 时，**必须至少保留一个托盘图标**（`Options → Tray Icons` 勾选任一项），否则最小化后无法唤回。详见 [GUI 篇](process-explorer-gui.md#替换任务管理器)。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 开关 |
|---|---|
| 首次运行的 EULA 对话框 | `/accepteula` |
| 右键「以管理员身份运行」 | `/e` |
| 最小化到托盘 | `/t` |
| `Options → Replace Task Manager` | **无**（只能 GUI 勾选，需管理员权限） |
| `Options → VirusTotal.com` 两项 | **无** |
| `Find → Find Handle or DLL` | **无** → 用 [Handle](handle.md) |
| `Process → Create Dump` | **无** → 用 [ProcDump](procdump.md) |
| 下窗格 DLLs / Handles / Threads | **无** |
| `View → Save Column Set` | **无** |
| 一切进程操作（Kill/Suspend/Set Priority） | **无** |

**「无」占绝大多数** —— 这就是 PE 的设计取向：交互式分析工具，不是自动化组件。

## 架构与分发

官方下载 `ProcessExplorer.zip`（3.4 MB），**无安装程序，直接运行 `procexp.exe`**。
Sysinternals Live：`https://live.sysinternals.com/procexp.exe`

Suite 内的文件：

```
procexp.exe      4,604,704   x86
procexp64.exe    2,411,824   x64
（ARM64 为 procexp64a.exe）
```

**单文件多架构自解压：** 在 x64 系统上运行 32 位 `procexp.exe` 时，它会**自行释放并创建 64 位的 `procexp64.exe`**。因此无需单独下载 64 位版本，但会在磁盘/临时目录看到额外的 `procexp64.exe` —— 这不是异常。

winget 安装后通过 PortableCommandAlias 统一映射为无后缀的 `procexp` 命令。包名为 `Microsoft.Sysinternals.ProcessExplorer`。

## 常见坑

1. **不要指望用命令行查询。** PE 没有输出能力，需要脚本化就换 [Handle](handle.md) / [ProcDump](procdump.md) / [Autoruns](autorunsc-cli.md)。
2. **`/t /e` 顺序敏感。** 按官方推荐顺序写。
3. **`/e` 之外的提权方式同样有效**（右键以管理员身份运行、从提权终端启动），`/e` 只是省一步。
4. **非提权运行时功能不全且不报错。** 看不到其他用户的进程、句柄列为空 —— PE 需加载内核驱动才能拿到完整数据。
5. **`/rt` 用途不明。** 二进制里存在但官方与随包 help 均无说明，不建议在生产脚本中使用。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer
- 工具自带：`Help → Help`（官方页面把操作用法明确下放给随包 help 文件）

> **本篇事实边界：** 官方页面**不含任何命令行参数说明**。`/accepteula` 与 `/rt` 来自 `procexp64.exe` v17.13 二进制资源；`/e` `/t` 及其顺序敏感性、单文件多架构自解压来自官方 Defrag Tools 节目（约 2012 年录制）。`/rt` 的语义未知，本篇未作推测。
