# 套件获取、EULA 与符号配置

非工具篇。覆盖所有工具共用的前置事项：分发渠道、架构差异、EULA 开关、符号路径、合规边界。

## 分发渠道

**官方下载索引页提供的整体分发渠道只有四条**（`learn.microsoft.com/en-us/sysinternals/downloads/`，`ms.date` 2026-08-12 / `updated_at` 2026-08-19）：

| 渠道 | 内容 | 体积 |
|---|---|---|
| `SysinternalsSuite.zip` | 完整版（x86 + x64 + ARM64 混装） | **192.3 MB** |
| `SysinternalsSuite-ARM64.zip` | ARM64 版 | 21.3 MB |
| `SysinternalsSuite-Nano.zip` | Nano Server 版 | 9.9 MB |
| Microsoft Store | ProductId `9p7knl5rwt25`，可自动更新 | — |

**体积差异说明覆盖范围不同：** ARM64 版仅 21.3 MB、Nano Server 版仅 9.9 MB，相对完整版 192.3 MB —— **后两者只包含工具子集**。需要完整工具集就用完整版。

**官方下载页正文未出现 winget 安装命令，也未列出 Sysinternals Live** —— 这两种方式来自其他官方页面。

### Sysinternals Live

来自官方索引页（`learn.microsoft.com/en-us/sysinternals/`）的独立小节，无需下载直接运行：

```
资源管理器：  live.sysinternals.com/<toolname>
             \\live.sysinternals.com\tools\<toolname>
命令提示符：  \\live.sysinternals.com\tools\<toolname>    ← 必须用 UNC 形式
完整目录：    https://live.sysinternals.com/
```

**命令行中必须用 UNC 形式**，`live.sysinternals.com/procmon.exe` 这种写法只在资源管理器地址栏有效。

适用场景：应急响应时目标机没装工具且不便下载。但依赖网络与 SMB 出网，很多企业环境会阻断。

### winget

**winget 官方清单库下只有 25 个 Sysinternals 包**（`manifests/m/Microsoft/Sysinternals`，数据抓取于 2026-09-02）：

```
Autologon  Autoruns  BGInfo  Ctrl2Cap  DebugView  Desktops  FindLinks
Handle  MoveFile  PendMoves  ProcessExplorer  ProcessMonitor  PsTools
RAMMap  RDCMan  RegJump  SDelete  Sigcheck  Strings  Suite  Sysmon
TCPView  VMMap  Whois  ZoomIt
```

即 `Microsoft.Sysinternals.<名称>` 只有这 25 个 ID，**并非全部 70+ 工具都有独立包**。

**两个重要缺口：**

| 工具 | winget 情况 |
|---|---|
| **ProcDump** | **没有独立包。** 只作为 Suite zip 内的嵌套文件分发 —— **不能写 `winget install Microsoft.Sysinternals.ProcDump`** |
| **PsExec** | **没有独立包。** 归入 `Microsoft.Sysinternals.PsTools` |

```powershell
# 常用安装命令
winget install Microsoft.Sysinternals.Suite            # 整套（推荐）
winget install Microsoft.Sysinternals.ProcessMonitor
winget install Microsoft.Sysinternals.ProcessExplorer
winget install Microsoft.Sysinternals.PsTools          # 含 PsExec
winget install Microsoft.Sysinternals.Sysmon
```

**winget 的 Suite 包不是 MSIX/Store 应用。** 清单为 `InstallerType: zip` + `NestedInstallerType: portable`，直接从 `download.sysinternals.com` 拉官方 zip。因此 **winget 安装等价于「解压便携版并注册命令别名」**，不产生传统安装程序，也不等同于 Microsoft Store 的 MSIX 版本。

x86/x64 共用 `SysinternalsSuite.zip`，ARM64 使用独立的 `SysinternalsSuite-ARM64.zip`（不同 SHA256）。

### 渠道选择建议

| 场景 | 推荐 |
|---|---|
| 个人工作机，要自动更新 | Microsoft Store 版 |
| 开发机，习惯包管理器 | `winget install Microsoft.Sysinternals.Suite` |
| 服务器 / 批量部署 | 手工下载 zip 解压到固定路径，纳入配置管理 |
| 应急响应，目标机没装 | Sysinternals Live（若网络允许） |
| 离线 / 隔离环境 | 手工下载 zip，随介质带入 |

## 架构后缀

**这是最容易踩的坑。** Sysinternals 的三套可执行文件命名规则（winget 清单显式记录）：

| 架构 | 命名 | 示例 |
|---|---|---|
| x86 | 无后缀 | `Procmon.exe` `procexp.exe` `handle.exe` |
| x64 | `64` 后缀 | `Procmon64.exe` `procexp64.exe` `handle64.exe` |
| ARM64 | `64a` 后缀 | `Procmon64a.exe` `procexp64a.exe` `handle64a.exe` |

**winget 安装后通过 `PortableCommandAlias` 统一映射为无后缀命令**（`procmon` / `procexp` / `handle`），**掩盖了这一差异** —— 手工解压使用时必须自己选对。

**在 64 位系统上用 32 位版本的后果因工具而异：**

| 工具 | 后果 |
|---|---|
| [Handle](handle.md) | 可能漏掉 64 位专有对象 |
| [Autoruns](autoruns-gui.md) | 可能漏掉 64 位专有的启动位置 |
| [Procmon](procmon-cli.md) | 能工作；加载 32 位机采集的 PML 需 `/Run32` |
| [Process Explorer](process-explorer-cli.md) | **自行释放并创建 `procexp64.exe`** —— 无需手工选，但磁盘会多出一个文件 |
| [VMMap](vmmap-cli.md) | 分析 32 位进程需 `-64` |
| [RAMMap](rammap-cli.md) | 用 32 位版载入旧快照需 `-run32` |
| [ProcDump](procdump.md) | 默认对 32 位进程生成 32 位 dump，`-64` 强制 64 位 |

**默认规则：在 64 位系统上一律用 `*64.exe`。**

## Suite 包含哪些工具

**Suite 是「选定工具的打包」而非全集。** 官方称它包含各故障排查工具及帮助文件，但明确排除非排查类工具（如 BSOD 屏保）。

**但官方文档在同一页自相矛盾** —— 打包清单中仍列出 `BlueScreen`（即 BSOD 屏保）、`NotMyFault`、`ZoomIt` 等非排查用途工具。**「排除非排查工具」这一表述不能按字面采信。**

本目录涉及的全部工具（Process Monitor、Process Explorer、Autoruns、TCPView、Handle、PsExec、RAMMap、VMMap、Sysmon、Strings、Sigcheck、ProcDump）**都在官方 Suite 打包清单内**（清单共列出 74 个工具条目）。**装一份 Suite 即可覆盖，不必单独下载各工具。**

Suite 只是可执行文件与帮助文件的压缩包，**没有安装程序概念**，解压即用、便携运行是官方设计的分发形态。Suite 页面不给统一的语义化版本号，只用「更新日期 + 压缩包体积」标识版本（winget 清单则用日期式版本号，如 `2026-07-09`）。

## EULA 与 `-accepteula`

### 法律基础

Sysinternals 工具的 EULA 采取**「使用即接受」**模式（官方 EULA 页，原始发布 2009-09-28，最后更新 2023-05-24）：

> BY USING THE SOFTWARE, YOU ACCEPT THESE TERMS. IF YOU DO NOT ACCEPT THEM, DO NOT USE THE SOFTWARE.

只要运行工具即视为接受许可条款。**这正是 `-accepteula` 开关在自动化/远程场景中合法可用的法律基础** —— 它跳过的是首次运行的 EULA 弹窗，不是跳过许可本身。

**EULA 页面本身未提及 `-accepteula` 参数。**

### 开关形式差异

| 工具 | 开关形式 |
|---|---|
| 大部分 CLI 工具 | `-accepteula` |
| [Procmon](procmon-cli.md) | `/AcceptEula`（斜杠 + 驼峰） |
| [Process Explorer](process-explorer-cli.md) | `/accepteula` 或 `-accepteula` 皆可 |
| [autorunsc](autorunsc-cli.md) | **本页全文未出现 `-accepteula`**，只有 `-vt` |

**首次运行不加 `-accepteula` 会弹对话框并阻塞** —— 无人值守脚本必踩。

### `-accepteula` 与 `-vt` 是两件事

**这是最容易混淆的一对：**

| 开关 | 接受什么 |
|---|---|
| `-accepteula` | **Sysinternals 自身**的 EULA |
| `-vt` | **VirusTotal** 的服务条款 |

| 工具 | 有哪个 |
|---|---|
| [Sigcheck](strings-sigcheck.md) | **两个都有**，都要加 |
| [autorunsc](autorunsc-cli.md) | **只有 `-vt`** |

省略 `-vt` 时工具会交互式提示，同样阻塞脚本。

### `-nobanner`

抑制启动横幅与版权信息，与 `-accepteula` 是**不同开关，不可互相替代**（PsExec 官方明确）。脚本化时通常两个都加：

```powershell
handle64.exe -accepteula -nobanner -a locked.db
```

## 符号配置

用于 [Procmon](procmon-gui.md#配置符号) 的堆栈跟踪、[Process Explorer](process-explorer-gui.md#符号配置) 的线程栈、[VMMap](vmmap-gui.md) 的分配调用栈。

### 路径语法

符号路径是**分号分隔**的多个目录路径组成的字符串。该语法同时适用于 `.sympath` 命令与 `_NT_SYMBOL_PATH` 环境变量。

**官方推荐的「符号服务器 + 本地缓存」写法：**

```
srv*<本地缓存目录>*<符号库地址>
```

微软公共符号服务器地址：`https://msdl.microsoft.com/download/symbols`

完整示例：

```
srv*C:\MyServerSymbols*https://msdl.microsoft.com/download/symbols
```

官方给出的环境变量设置命令：

```cmd
set _NT_SYMBOL_PATH=srv*DownstreamStore*https://msdl.microsoft.com/download/symbols
```

**`cache*` 的语法与 `srv*` 不同** —— `cache*` 后接**分号**，`srv*` 用星号分隔：

```
cache*C:\MySymbols;srv*https://msdl.microsoft.com/download/symbols
```

### PowerShell 设置

```powershell
# 当前会话
$env:_NT_SYMBOL_PATH = 'srv*C:\Symbols*https://msdl.microsoft.com/download/symbols'

# 永久（用户级）
[Environment]::SetEnvironmentVariable('_NT_SYMBOL_PATH',
  'srv*C:\Symbols*https://msdl.microsoft.com/download/symbols', 'User')
```

**`_NT_SYMBOL_PATH` 必须在启动工具之前设置。** 已运行的工具不会感知变更。

### 六个坑

1. **环境变量中的无效目录会被静默忽略。** 这是排查符号加载失败时的关键坑 —— 路径写错不报错，只是没符号。
2. **最终路径由 `_NT_ALT_SYMBOL_PATH` 后追加 `_NT_SYMBOL_PATH` 拼成。** 两个变量都设了会叠加。
3. **DBGHELP.DLL 所在目录必须同时包含匹配的 SYMSRV.DLL**（官方 Process Explorer 页面明示），否则符号服务器解析不可用。官方将细节指向 Windows 驱动文档的 SymSrv 页面。
4. **DbgHelp.dll 版本要够新。** Procmon 会报 `The version of Dbghelp.dll configured does not support the Microsoft Symbol Server.` —— 需装 Debugging Tools for Windows 取得较新的 DbgHelp（Procmon 要求 6.0 或更高）。
5. **公共符号服务器仅支持 TLS 1.2 及以上。** 符号加载失败时应先核查网络是否支持 TLS 1.2+ 及防火墙设置 —— 这是官方首选检查项。
6. **手工存放符号的目录不得兼作符号服务器下载缓存目录。** 必须用两个独立目录。缓存过大可用 AgeStore 清理。

### 离线环境

**微软已停止发布 Windows 的离线符号包（offline symbol packages）** —— 原因是 Windows 更新频繁、打包发布的符号很快过时。公共符号服务器基于 Azure 符号存储，覆盖所有 Windows 版本与更新的符号。

**因此堆栈解析不能再依赖下载符号包安装文件。** 对无法联网的机器，官方路径是**使用 SymChk 配合 manifest 文件**，而不是安装离线符号包。

### 缓存行为

符号路径中的 DownstreamStore 必须是本机或网络上的一个目录，作为符号缓存。**未被访问过的符号仍留在微软服务器上，每个文件只下载一次** —— 因此本地缓存体积保持较小。

### 许可限制

符号服务器上的符号、二进制代码与可执行文件受《Microsoft license terms - Microsoft symbol server》约束，**仅授权用于调试和测试与微软软件相关的自有软件**，未经授权不得使用。

## 合规边界

### 敏感信息（重要）

**Microsoft 官方警示：** Sysinternals 工具保存的文件（如 Procmon 的 PML 日志、Procdump 的 dump）**可能包含个人可识别信息或敏感信息，包括用户名、密码、被访问的文件路径与注册表路径**。用户对外发这些日志所泄露的信息承担全部责任。

**这是排查日志外发/上传给第三方前必须脱敏的合规依据。** 涉及的产物：

- Procmon 的 `.pml` / 导出的 CSV/XML
- ProcDump 的 `.dmp`（`-mt` Triage 类型「尝试但不保证」移除敏感信息）
- Handle / Sigcheck / autorunsc 的 CSV 输出（含完整路径）
- VMMap 的 Strings 视图导出（进程内存中可能有明文密码/令牌）

### 许可禁止事项

- **禁止发布软件供他人复制**
- **禁止出租/出借/转让**
- **禁止用于商业软件托管服务**
- 禁止绕过技术限制与逆向工程（除法律明确允许的范围）

**企业不能把 Sysinternals 工具打包进自己的内部分发镜像对外发布，或随产品转交第三方。**

### 安装数量不受限

**许可允许在你自己的设备上安装和使用任意数量的副本**（不限台数、无需按座席授权）。运维在整个机群铺开 Sysinternals Suite 不存在数量许可障碍 —— **限制点在于「不得再发布给他人」而非「安装数量」**。

### 无遥测、无 SLA

- **工具本身不收集任何数据**（无遥测）
- 软件按「as is」授权，Microsoft 可能不提供支持服务
- **责任上限仅为 5 美元直接损失**

意味着生产环境使用（如 [Sysmon](sysmon.md) 长期驻留、[Procmon](procmon-cli.md) Boot logging）出问题**无官方 SLA 兜底**。

## 文档时效性基线

Sysinternals 文档由 **Mark Russinovich** 署名维护，源文件托管在 GitHub `MicrosoftDocs/sysinternals` 仓库（`live` 分支）。

**核对某个事实是否过时的方法：**

1. 打开工具页对应的 `original_content_git_url`（形如 `github.com/MicrosoftDocs/sysinternals/blob/live/sysinternals/downloads/<tool>.md`）
2. 看 `ms.date` 与 `updated_at`
3. 用 git history 查具体改动

本目录各篇的 `事实边界` 小节均标注了采集时间与来源层级（官方页面 / 二进制资源 / 实践经验）。

**官方页面信息量差异极大，这直接影响可信度：**

| 工具页 | 词数 | 覆盖情况 |
|---|---|---|
| [ProcDump](procdump.md) | 较全 | 转储类型与触发条件都有 |
| [Sysmon](sysmon.md) | 较全 | 开关、事件、规则语义都有 |
| [Procmon](procmon-cli.md) | **396** | **无任何命令行开关** |
| [RAMMap](rammap-cli.md) | **325** | **无 CLI、无 Empty 操作** |
| [VMMap](vmmap-cli.md) | **277** | 只说「提供命令行选项」不列参数 |
| [Strings](strings-sigcheck.md) | **228** | 参数表完整（工具本身简单） |
| [Process Explorer](process-explorer-gui.md) | 中等 | **无版本号、无 CLI、无 VirusTotal、无替换任务管理器** |

**遇到官方页面查不到的参数，先试工具自带的帮助入口：**

```
Procmon     Help → Command Line Options
VMMap       Help → Command-line Options
RAMMap      Help → Usage
Sysmon      Sysmon64.exe -? / -? config
其他 CLI    <tool>.exe -? 或 /?
```

## 官方文档

- 索引页（版本与 What's New）：https://learn.microsoft.com/en-us/sysinternals/
- 下载索引：https://learn.microsoft.com/en-us/sysinternals/downloads/
- Suite 页：https://learn.microsoft.com/en-us/sysinternals/downloads/sysinternals-suite
- EULA：https://learn.microsoft.com/en-us/sysinternals/license
- 符号语法：https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/symbol-path
- 文档源仓库：https://github.com/MicrosoftDocs/sysinternals

> **本篇事实边界：** 四条分发渠道与体积、Suite 是选定工具打包及其自相矛盾之处、74 个工具条目、Sysinternals Live 路径语法、EULA「使用即接受」与四项禁止事项与安装数量不限与无遥测与 5 美元责任上限与敏感信息警示、符号路径语法（`srv*` / `cache*` / 分号分隔）、`_NT_SYMBOL_PATH` 须在启动前设置、无效目录静默忽略、`_NT_ALT_SYMBOL_PATH` 拼接顺序、SYMSRV.DLL 与 DBGHELP.DLL 同目录要求、TLS 1.2+ 要求、手工目录不得兼作缓存、离线符号包已停止发布与 SymChk 替代、符号服务器许可限制均来自官方页面。winget 25 个包清单、`InstallerType: zip` + `NestedInstallerType: portable`、ProcDump/PsExec 无独立包、三套架构命名规则与 PortableCommandAlias 来自 winget 官方清单库（`microsoft/winget-pkgs` master 分支，数据抓取于 2026-09-02，清单由 komac v2.16.0 生成，schema 1.12.0）。各工具页词数与「工具自带帮助入口」为本目录实际核对结果。渠道选择建议、32 位版后果对照表为实践经验总结。
