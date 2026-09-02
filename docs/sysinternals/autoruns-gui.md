# Autoruns — 图形界面

**v14.3（2026-06-17）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns
**CLI 篇：** [autorunsc-cli.md](autorunsc-cli.md)（独立可执行文件 `autorunsc.exe`）

> **来源说明：** 菜单结构、对话框选项提取自 `Autoruns64.exe` **v14.3** 二进制资源。枚举范围与 VirusTotal 语义来自官方页面。ASCII 布局图为示意，非像素级还原。

## 定位与边界

枚举**所有自启动位置**并按类别分标签页展示。官方给出的覆盖范围基线：

登录项、Explorer 加载项、IE 加载项（含 BHO）、AppInit DLLs、映像劫持（image hijacks）、boot execute 映像、Winlogon 通知 DLL、Windows 服务与 Winsock 分层服务提供程序（LSP）、媒体编解码器等。

**v14.2（2026-05-07）新增对 Windows packaged apps（打包应用）的支持**，v14.3（2026-06-17）使命令行版 autorunsc 能力与 GUI 完全对齐 —— **早期文档中「autorunsc 功能少于 GUI」的说法在 v14.3 后已过时**。

| 需求 | Autoruns 是否合适 |
|---|---|
| 「开机启动了什么不该启动的东西」 | ✅ 正是设计目标，比 msconfig 全面得多 |
| 持久化排查（应急响应） | ✅ 覆盖面远超任务管理器的启动项标签 |
| 「这个启动项现在是否在运行」 | ⚠️ 需配合 [Process Explorer](process-explorer-gui.md)，见「联动」 |
| 离线系统 / 挂载的另一个 Windows | ✅ `Analyze Offline System` |
| 批量采集多机基线 | ❌ 用 [autorunsc](autorunsc-cli.md)，CSV/XML 输出 |
| 启动过程的时序与耗时 | ❌ 用 [Procmon](procmon-gui.md) 的 Boot logging |

## 主窗口布局

```
┌─ Autoruns ─────────────────────────────────────────────────────────────┐
│ File  Search  Entry  Options  User  Category  Help                     │ ← 菜单栏
├────────────────────────────────────────────────────────────────────────┤
│ 💾 🔄 ✖ │ 🔍 │ ⓘ 🗑 │ [Quick Find:            ] [Ctrl+Q]              │ ← 工具栏
├────────────────────────────────────────────────────────────────────────┤
│ Everything│Logon│Explorer│IE│Sched.Tasks│Services│Drivers│Codecs│…    │ ← 类别标签页
│  └─ 全部  └─ 最常用的两个 ─┘         └ 常见持久化位置 ─┘               │   （十余个）
├────────────────────────────────────────────────────────────────────────┤
│ ☑ │ Autorun Entry    │ Description   │ Publisher      │ Image Path     │
│ ☑ │ HKLM\...\Run                                                       │ ← 分组标题行
│ ☑ │  ├ YourApp       │ Your App      │ (Verified) …   │ c:\app\a.exe   │
│ ☐ │  ├ OldTool       │ Legacy Tool   │ (Not verified) │ c:\old\t.exe   │ ← 取消勾选=禁用
│ ☑ │  └ suspicious    │               │                │ c:\temp\x.exe  │ ← 空描述+temp 路径
│ ☑ │ HKCU\...\Run                                                       │   = 高度可疑
│ ☑ │  └ Updater       │ Updater       │ (Verified) …   │ c:\upd\u.exe   │
├────────────────────────────────────────────────────────────────────────┤
│ Path: c:\temp\x.exe                                                    │ ← 详情窗格
│ VirusTotal: 14/72   Timestamp: 2026-08-30 03:14   Size: 82 KB          │
└────────────────────────────────────────────────────────────────────────┘
```

**读表的三个可疑信号**（按优先级）：

1. **Publisher 为空或 `(Not verified)`** —— 合法软件基本都有签名
2. **Image Path 在 `%TEMP%` / `%APPDATA%` / 用户目录下** —— 正常启动项极少放这里
3. **Description 为空** —— 合法二进制通常填了版本资源

三者同时出现基本可以确定要追。开启 `Options → Verify Image Signatures` 让 Publisher 列显示验证结果。

## 菜单结构与快捷键

```
File                              Search                     Entry
├ Open...              Ctrl+O     ├ Quick Find      Ctrl+Q    ├ Delete            Ctrl+D
├ Save...              Ctrl+S     ├ Find...         Ctrl+F    ├ Copy              Ctrl+C
├ Analyze Offline System...       ├ Find Next                 ├ Jump to Entry...
│      ← 离线系统扫描             └ Find Previous   Shift+F3  │     ← 跳到注册表/文件位置
├ Compare...   ← 与基线对比                                   ├ Jump to Image...
├ Refresh                         Options                     ├ Verify Image
├ Cancel               ESC        ├ ☐ Hide Empty Locations    ├ Check VirusTotal
└ Exit                            ├ ☑ Hide Microsoft Entries  ├ Process Explorer...
                                  ├ ☐ Hide Windows Entries    │     ← 联动，见下
User      ← 切换要检查的用户      ├ ☐ Hide VirusTotal Clean   ├ Search Online...  Ctrl+M
Category  ← 类别快速跳转          │     Entries               ├ Find...           Ctrl+F
                                  ├ ☐ Always On Top           └ Properties...     Alt+Enter
Help                              ├ Scan Options...
├ Help...                         ├ Font...
└ About...                        └ Theme  ▸ Light/Dark/Use System Setting
```

## 禁用 vs 删除

**这是 Autoruns 最重要的操作语义差别。**

| 操作 | 方式 | 可逆性 |
|---|---|---|
| **禁用** | 取消该行的**勾选框** | ✅ 可逆。Autoruns 把原配置备份到专门位置，重新勾选即恢复 |
| **删除** | `Entry → Delete`（`Ctrl+D`） | ❌ **不可逆**。直接删除注册表值/文件系统条目 |

**排查时永远先禁用，确认无副作用后再考虑删除。** 禁用后重启验证问题是否消失，这是标准做法。误删一个系统组件的启动项可能导致无法登录。

`Entry → Jump to Entry` 直接打开注册表编辑器/资源管理器定位到该条目的实际位置 —— 想手工确认或备份时用它。

## 降噪：三个 Hide 选项

默认全表有数千条，必须降噪：

```
Options → ☑ Hide Microsoft Entries      ← 默认开启，隐藏微软签名的条目
Options → ☐ Hide Windows Entries        ← 更激进，隐藏 Windows 自带条目
Options → ☐ Hide Empty Locations        ← 隐藏没有条目的位置分组
Options → ☐ Hide VirusTotal Clean Entries  ← 只留 VT 检出非零的
```

**应急响应时的推荐组合：** 开启 `Hide Microsoft Entries` + `Hide Windows Entries` + `Hide Empty Locations`。剩下的基本就是第三方与可疑条目，通常从数千条降到几十条。

**但要注意：** 攻击者可以劫持微软签名的宿主程序（`rundll32.exe`、`regsvr32.exe`、`mshta.exe` 加载恶意 DLL/脚本）。这类条目的 Publisher 是微软签名，会被 `Hide Microsoft Entries` 隐藏 —— **确认没有可疑项后，应关掉该选项再扫一遍，重点看 Image Path 是微软程序但命令行参数指向异常路径的条目**。加 `Command Line` 列（如果可用）或看详情窗格。

## 与 Process Explorer 联动

官方明确的联动行为：**当 Process Explorer 正在运行且所选自启动映像有活动进程时，`Entry → Process Explorer` 菜单项会直接打开该进程的属性对话框。**

用途：确认某个启动项**当前是否真的在运行**。Autoruns 显示的是「配置了会启动」，不等于「现在正在运行」。

```
① 先启动 Process Explorer（保持运行）
② 在 Autoruns 选中可疑条目
③ Entry → Process Explorer
      有反应 → 该项当前有活动进程，可继续在 PE 里看句柄/DLL/网络
      无反应 → 配置存在但进程未运行
```

## VirusTotal 集成

**VirusTotal 集成不是 Process Explorer 独有** —— Autoruns 也有，且语义相同。

`Options → Scan Options` 打开扫描选项对话框，可启用签名验证与 VirusTotal 哈希/文件提交。

| 行为 | 隐私影响 |
|---|---|
| 按**哈希**查询 | 低。哈希不含文件内容 |
| **上传文件本体**（VT 未收录过的文件） | **高。文件会被上传到第三方并可能公开** |

官方警示：**扫描结果可能需要五分钟以上才可用**，且上传**可能泄露文件，生产环境需谨慎**。

`Options → Hide VirusTotal Clean Entries` 可只保留检出非零的条目。

**检出数非零 ≠ 恶意，为零 ≠ 安全。** 自研工具与打包器常被误报；新型样本 VT 可能尚未收录。

命令行侧的等价开关见 [autorunsc-cli.md](autorunsc-cli.md) —— 注意 autorunsc 用专用的 `-vt` 接受 VirusTotal 条款，**不是** `-accepteula`。

## 离线系统扫描

`File → Analyze Offline System` 指定另一个 Windows 安装的系统根目录与用户配置文件目录。

用途：

- 系统已无法启动，从 WinPE 或另一个系统挂载后排查持久化
- 分析取证镜像
- 检查其他用户配置（也可用 `User` 菜单切换）

> **对应 CLI：** `autorunsc -z` 扫描离线 Windows 系统。

## 基线对比

`File → Compare` 与之前保存的 `.arn` 文件对比，只显示差异。

**这是持久化排查最有效的方法：**

```
① 干净系统上 File → Save 存基线（.arn）
② 出问题后再次运行 Autoruns
③ File → Compare 选基线文件
④ 差异即新增/变更的启动项
```

批量采集多机基线更适合用 [autorunsc](autorunsc-cli.md) 的 CSV 输出配合脚本 diff。

## GUI 侧常见坑

1. **禁用（取消勾选）与删除（Ctrl+D）语义不同。** 前者可逆，后者不可逆。永远先禁用。
2. **默认隐藏微软条目。** 攻击者可劫持微软签名的宿主程序（rundll32/regsvr32/mshta），这类条目会被隐藏。确认无可疑项后关掉该选项再扫一遍。
3. **需管理员权限才能看到 HKLM 与服务/驱动类条目。** 非提权运行会静默少显示大量条目。
4. **VirusTotal 上传会泄露文件。** 只查哈希与上传本体是两个不同选项。
5. **扫描结果可能延迟 5 分钟以上。** 首次提交后立刻看可能是空的。
6. **Autoruns 显示的是配置，不是运行状态。** 用 Process Explorer 联动确认。
7. **v14.3 前 autorunsc 能力少于 GUI，v14.3 后已对齐。** 旧脚本可能基于过时假设。
8. **`Analyze Offline System` 需同时指定系统根与用户配置目录**，只给系统根会漏掉 HKCU 类条目。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns
- 工具自带：`Help → Help`

> **本篇事实边界：** 枚举范围、Process Explorer 联动、VirusTotal 语义与警示、v14.2/v14.3 变更来自官方页面与官方索引页 What's New。菜单结构、Options 各项、对话框选项提取自 `Autoruns64.exe` v14.3 二进制资源。读表可疑信号、降噪组合、基线对比流程、微软签名宿主劫持的注意事项为实践经验总结。
