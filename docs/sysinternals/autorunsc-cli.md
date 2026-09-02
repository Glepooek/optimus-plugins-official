# autorunsc — 命令行

**Autoruns v14.3（2026-06-17）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns
**GUI 篇：** [autoruns-gui.md](autoruns-gui.md)

> `autorunsc.exe` 是**独立的可执行文件**，不是 `Autoruns.exe` 的命令行开关 —— Suite 内两者并存（`autorunsc.exe` / `autorunsc64.exe`）。
>
> **v14.3（2026-06-17）使 autorunsc 能力与 GUI 完全对齐**（包括 packaged apps 支持）。早期文档中「autorunsc 功能少于 GUI」的说法已过时。

## 语法

官方给出的完整语法：

```
autorunsc [-a <*|bdeghiklmoprsw>] [-c|-ct] [-h] [-m] [-s] [-u] [-vt] [[-z] | [user]]
```

## 参数表

| 参数 | 说明 |
|---|---|
| `-a <类别>` | 选择枚举类别，见下表。`*` 为全部 |
| `-c` | 输出 CSV |
| `-ct` | 输出制表符分隔 |
| `-x` | 输出 XML |
| `-h` | 显示文件哈希 |
| `-s` | 验证数字签名 |
| `-m` | 隐藏 Microsoft 条目 |
| `-t` | 以规范化 UTC 显示时间戳（`YYYYMMDD-hhmmss`） |
| `-u` | 仅显示未签名或 VT 检出非零的条目 |
| `-v` | VirusTotal 按**哈希**查询 |
| `-vr` | 对检出非零的条目自动打开在线报告页 |
| `-vs` | **上传** VT 未收录过的文件本体 |
| `-vt` | **接受 VirusTotal 服务条款**（必需，见下） |
| `-z <目录>` | 扫描离线 Windows 系统 |
| `user` | 指定用户配置（`*` 为全部用户） |
| `-nobanner` | 抑制启动横幅 |

### `-a` 的类别字母

| 字母 | 类别 |
|---|---|
| `*` | 全部 |
| `b` | Boot execute |
| `d` | AppInit DLLs |
| `e` | Explorer 加载项 |
| `g` | Sidebar gadgets |
| `h` | Image hijacks（映像劫持） |
| `i` | Internet Explorer 加载项 |
| `k` | Known DLLs |
| `l` | **登录启动项（默认）** |
| `m` | WMI |
| `o` | Codecs |
| `p` | Printer monitor DLLs |
| `r` | LSA providers |
| `s` | **服务与驱动** |
| `t` | **计划任务** |
| `w` | Winlogon |

**`-a l` 是默认值**（只查登录启动项）。持久化排查要用 `-a *`。

## 关键坑：`-vt` 不是 `-accepteula`

**autorunsc 用专用开关 `-vt` 接受 VirusTotal 服务条款，本页全文未出现 `-accepteula`。**

省略 `-vt` 会**交互式提示**，在无人值守脚本中直接阻塞。这与其他 Sysinternals 工具通用的 `-accepteula`（接受 Sysinternals 自身 EULA）是两个独立的东西 —— [Sigcheck](strings-sigcheck.md) 则**两个都有**。

```powershell
# ❌ 会阻塞：启用了 VT 但没接受条款
autorunsc64.exe -a * -v -c

# ✅ 正确
autorunsc64.exe -a * -v -vt -c
```

## VirusTotal 三个开关的分界

| 开关 | 行为 | 隐私影响 |
|---|---|---|
| `-v` | 按**哈希**查询 | 低。哈希不含文件内容 |
| `-vr` | 对检出非零的条目打开报告页 | 低（只是打开浏览器） |
| `-vs` | **上传** VT 未收录过的文件本体 | **高。文件被上传到第三方并可能公开** |

官方警示：扫描结果**可能需要五分钟以上才可用**；上传**可能泄露文件，生产环境需谨慎**。

**生产环境只用 `-v`，绝不用 `-vs`** —— 内部自研的可执行文件一旦上传即等同于向第三方公开该二进制。

## 实用配方

```powershell
# 全类别 + 签名验证 + 哈希 + 隐藏微软条目 → CSV
autorunsc64.exe -accepteula -nobanner -a * -s -h -m -c > baseline.csv

# 只看可疑项：未签名或 VT 检出非零
autorunsc64.exe -nobanner -a * -s -v -vt -u -c > suspicious.csv

# 全部用户配置 + UTC 时间戳（多机基线对齐用）
autorunsc64.exe -nobanner -a * -s -h -t -c "*" > all-users.csv

# 只查服务与驱动、计划任务（最常见的持久化位置）
autorunsc64.exe -nobanner -a st -s -h -c > persistence.csv

# 离线系统扫描（从 WinPE 或挂载的另一个系统）
autorunsc64.exe -nobanner -z D:\Windows -a * -s -h -c > offline.csv

# XML 输出（需保留结构化嵌套时）
autorunsc64.exe -nobanner -a * -s -h -x > report.xml
```

### 多机基线 diff

CSV 输出配合脚本 diff 是**批量持久化排查的正确做法**，比逐台开 GUI 快得多：

```powershell
# 采集
autorunsc64.exe -nobanner -a * -s -h -m -t -c > "host-$env:COMPUTERNAME.csv"

# 与黄金基线对比（只看新增行）
$base = Get-Content golden.csv
$now  = Get-Content "host-$env:COMPUTERNAME.csv"
Compare-Object $base $now | Where-Object SideIndicator -eq '=>'
```

**加 `-t` 让时间戳规范化为 UTC** —— 不加则各机时区不同，diff 会产生大量假差异。

## GUI ↔ CLI 对照

| GUI 操作 | CLI 参数 |
|---|---|
| 类别标签页 | `-a <字母>`（`*` 全部，默认 `l`） |
| `Options → Hide Microsoft Entries` | `-m` |
| `Options → Scan Options`，签名验证 | `-s` |
| `Options → Scan Options`，VT 哈希查询 | `-v` + `-vt` |
| `Options → Scan Options`，VT 提交文件 | `-vs` + `-vt` |
| `Options → Hide VirusTotal Clean Entries` | `-u`（含未签名） |
| `File → Save`（`.arn`） | `-c` / `-ct` / `-x`（格式不同，非 `.arn`） |
| `File → Analyze Offline System` | `-z <目录>` |
| `User` 菜单切换用户 | `user` 位置参数（`*` 全部） |
| 详情窗格的哈希 | `-h` |
| `File → Compare` | **无** → 用 CSV + 脚本 diff |
| 取消勾选禁用条目 | **无** → autorunsc 只读，不能禁用/删除 |
| `Entry → Jump to Entry` | **无** |
| `Entry → Process Explorer` 联动 | **无** |

**autorunsc 是只读工具** —— 能枚举与导出，不能禁用或删除条目。处置必须回 GUI 或手工改注册表。

## 常见坑

1. **`-vt` 不是 `-accepteula`。** 前者接受 VirusTotal 条款，后者接受 Sysinternals EULA。启用 VT 功能时缺 `-vt` 会阻塞脚本。
2. **`-a` 默认只查登录项（`l`）。** 持久化排查必须显式写 `-a *`，否则漏掉服务、驱动、计划任务、WMI 等。
3. **`-vs` 会上传文件本体。** 生产环境只用 `-v`。
4. **需管理员权限才能枚举 HKLM 与服务/驱动类条目。** 非提权运行会静默少输出。
5. **不加 `-t` 时时间戳带本地时区**，多机 diff 会产生假差异。
6. **autorunsc 只读。** 不能禁用/删除。
7. **VT 结果可能延迟 5 分钟以上。** 首次提交后立刻查可能为空。
8. **`-u` 的语义随 VT 是否启用而变**：未启用 VT 时列未签名文件；启用后列 VT 未知或检出非零的文件。
9. **架构后缀。** 64 位系统用 `autorunsc64.exe`，否则可能漏掉 64 位专有位置。

## 分发

Autoruns 包内含 GUI 与 CLI 两套、各三个架构：

```
Autoruns.exe     1,809,728   x86 GUI      autorunsc.exe    1,317,184   x86 CLI
Autoruns64.exe   1,931,616   x64 GUI      autorunsc64.exe  1,460,024   x64 CLI
（ARM64 为 *64a.exe）
```

winget 包名 `Microsoft.Sysinternals.Autoruns`。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns

> **本篇事实边界：** 语法、`-a` 类别字母、各参数语义、VirusTotal 三开关分界与警示、`-vt` 非 `-accepteula`、`-z` 离线扫描、`user` 参数均来自官方页面。v14.2/v14.3 变更来自官方索引页 What's New。多机 diff 配方、`-t` 对齐时区的必要性、只读性质的处置建议为实践经验总结。
