# PsExec

**v2.43（2023-04-11，维护停滞）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/psexec

> **纯 CLI 工具，无 GUI。**
>
> **⚠ 在企业环境使用前先读「安全影响」一节。** PsExec 被 MITRE ATT&CK 登记为工具 S0029，30 余个 APT/勒索团伙在实战中使用它 —— **在受控环境运行极可能触发安全告警或被列入黑名单**。

## 定位与边界

在远程系统上执行进程，无需预先安装客户端软件。

| 需求 | PsExec 是否合适 |
|---|---|
| 临时在远程机跑个命令 | ✅ 但注意告警风险 |
| 以 SYSTEM 身份在本机跑（看 SAM/SECURITY 注册表） | ✅ `-i -d -s` |
| 生产环境的常规远程管理 | ❌ 用 PowerShell Remoting / WinRM，不触发 EDR 告警 |
| 批量部署 | ❌ 用 SCCM / Intune / Ansible |
| 需要审计留痕的操作 | ⚠️ PsExec 会留痕，但是「可疑活动」形态的留痕 |

**现代替代方案更可取：**

```powershell
# PowerShell Remoting —— 加密、有审计、不触发 EDR
Invoke-Command -ComputerName SERVER01 -ScriptBlock { Get-Service W32Time }
Enter-PSSession -ComputerName SERVER01
```

PsExec 的不可替代场景只剩：目标机没开 WinRM、需要 `-s` 提到 SYSTEM、需要 `-x` 在 Winlogon 安全桌面显示 UI。

## 语法

官方 usage 原文：

```
psexec [\\computer[,computer2[,...] | @file]][-u user [-p psswd]][-n s]
       [-r servicename][-h][-l][-s|-e][-x][-i [session]][-c [-f|-v]]
       [-w directory][-d][-<priority>][-g n][-a n,n,...][-verbose]
       cmd [arguments]
```

## 参数表（官方 usage 原文译）

### 目标指定

| 参数 | 说明 |
|---|---|
| `\\computer` | 在指定远程机执行。**省略则在本机执行** |
| `\\computer1,computer2` | 多台 |
| `@file` | 从文件读取计算机列表 |
| `\\*` | **在当前域的所有计算机上执行**（极危险，见常见坑） |

### 身份与权限

| 参数 | 官方描述（译） |
|---|---|
| `-u <user>` | 登录远程计算机的用户名 |
| `-p <psswd>` | 用户名对应的密码。**省略则会提示输入隐藏密码** |
| `-s` | 在 System 账户上下文运行远程进程 |
| `-e` | 不加载指定账户的配置文件 |
| `-h` | 目标为 Vista 或更高时，用账户的**提升令牌**运行（若可用） |
| `-l` | 以受限用户运行（**剥离 Administrators 组**，只保留 Users 组权限）。Vista 上以低完整性运行 |

`-s` 与 `-e` 互斥。

### 执行控制

| 参数 | 官方描述（译） |
|---|---|
| `-i [session]` | 让程序与指定会话的桌面交互。**不指定 session 则在控制台会话运行** |
| `-d` | 不等待进程结束（非交互） |
| `-c` | 把指定程序复制到远程系统后执行。**省略则程序必须已在远程系统的 PATH 中** |
| `-f` | 即使远程已存在该文件也强制复制（配合 `-c`） |
| `-v` | 仅当版本号更高或更新时才复制（配合 `-c`） |
| `-w <directory>` | 设置进程工作目录（相对于远程计算机） |
| `-n <s>` | 连接远程计算机的超时秒数 |
| `-r <servicename>` | 指定要创建或交互的远程服务名 |
| `-x` | 在 **Winlogon 安全桌面**显示 UI（仅本机） |

### 处理器与优先级

| 参数 | 官方描述（译） |
|---|---|
| `-a n,n,...` | 限定可运行的 CPU（逗号分隔，1 为最小编号）。例：`-a 2,4` |
| `-g n` | 设置主线程的处理器组（仅用于超过 64 个处理器的系统） |
| `-low` `-belownormal` `-abovenormal` `-high` `-realtime` | 以不同优先级运行 |
| `-background` | 在 Vista 上以低内存与 I/O 优先级运行 |

### 其他

| 参数 | 说明 |
|---|---|
| `-arm` | **指定远程计算机为 ARM 架构**（官方网页未记载，来自二进制 usage） |
| `-verbose` | 详细输出（官方网页未记载） |
| `-accepteula` | 抑制许可协议对话框的显示 |
| `-nobanner` | 抑制启动横幅与版权信息 |

**`-accepteula` 与 `-nobanner` 是不同开关，不可互相替代**（官方明确）。脚本化时通常两个都要加。

## 关键坑：模拟（impersonation）与双跳

**若省略 `-u`，远程进程以调用者账户上下文运行，但因为是「模拟（impersonating）」而无法访问网络资源。**

这就是经典的双跳（double-hop）问题：

```
你的机器 ──① PsExec──> 远程机A ──② 访问 \\fileserver\share ──✗ 失败
                                    （凭据无法再传递一跳）
```

**解法：用 `Domain\User` 形式显式指定用户名。**

```powershell
# ❌ 远程进程访问网络共享会失败
psexec \\SERVER01 cmd /c "dir \\fileserver\share"

# ✅ 显式指定域用户，凭据可传递
psexec \\SERVER01 -u CONTOSO\admin -p <password> cmd /c "dir \\fileserver\share"
```

官方声明口令与命令在传输到远端时是**加密的**。但 `-p` 出现在命令行意味着**密码会进入命令行历史、进程列表与审计日志** —— 生产环境应省略 `-p` 让它交互式提示。

## 实用配方

```powershell
# 以 SYSTEM 身份打开本机注册表编辑器（看 SAM/SECURITY 键）
# 官方给出的示例
psexec -i -d -s c:\windows\regedit.exe

# 以 SYSTEM 身份开一个本机命令行
psexec -i -d -s cmd.exe

# 远程执行（程序已在远程 PATH 中）
psexec \\SERVER01 -accepteula -nobanner ipconfig /all

# 远程执行并把程序复制过去
psexec \\SERVER01 -accepteula -c C:\tools\collect.exe

# 多台机器（从文件读列表）
psexec @servers.txt -accepteula -nobanner hostname

# 用提升令牌运行（UAC 环境）
psexec \\SERVER01 -h -accepteula cmd /c "net localgroup administrators"

# 以受限权限运行不受信任的程序（剥离 Administrators 组）
psexec -l -accepteula C:\untrusted\sample.exe

# 低优先级运行，避免影响业务
psexec \\SERVER01 -accepteula -background -d C:\tools\scan.exe
```

## 安全影响（重要）

### 技术机理

| 机理 | 后果 |
|---|---|
| **向目标机的 `ADMIN$` 管理共享写入程序文件** | 这是它被 EDR/安全策略拦截的技术根因。禁用管理共享即 PsExec 失效 |
| **在目标机创建临时 Windows 服务来执行二进制** | 会在目标机留下**服务创建痕迹**（对应 ATT&CK T1543.003 / T1569.002 Service Execution）。排查时可据此在系统日志中定位 PsExec 活动 |
| **`-s` 把权限从 Administrator 提到 SYSTEM** | 官方支持的参数行为，也是它被归类为提权手段的原因 |

### 告警与黑名单

**官方明确承认部分杀毒软件会把 PsTools 报为「remote admin」病毒**，并说明这是因为该工具曾被病毒利用，而非工具本身含毒。

MITRE ATT&CK 将 PsExec 登记为工具 **S0029**，列出 30 余个 APT/勒索团伙在实战中使用它，包括 **Volt Typhoon（G1017）、APT29（G0016）、Wizard Spider（G0102）、Akira（G1024）**。

**在企业环境运行 PsExec 极可能：**

- 触发 EDR/AV 告警，惊动安全团队
- 被应用控制策略（AppLocker / WDAC）阻止
- 在 SIEM 中生成「疑似横向移动」事件

**如果你的操作是合法授权的，事前通知安全团队** —— 否则可能触发事件响应流程。

### 能力面远超「远程跑个命令」

PsExec 还具备：

- **跨网络共享上传/下载文件**（ATT&CK T1570 Lateral Tool Transfer）
- **在目标系统远程创建账户**（T1136.002）

运维使用时需明确最小权限边界 —— 不要因为「只是跑个命令」而低估授权范围。

## 常见坑

1. **`\\*` 会在当前域的所有计算机上执行。** 极其危险，一条命令可影响整个域。**不要在生产环境使用。**
2. **省略 `-u` 时远程进程无法访问网络资源**（模拟限制/双跳）。需要访问网络共享必须用 `Domain\User` 显式指定。
3. **`-p` 会让密码进入命令行历史与进程列表。** 省略 `-p` 让它交互式提示。
4. **`-accepteula` 与 `-nobanner` 是不同开关。** 脚本化时两个都加。
5. **企业环境极可能触发安全告警。** 事前通知安全团队。
6. **会在目标机留下服务创建痕迹。** 这既是排查线索，也意味着你的操作会被记录。
7. **依赖 `ADMIN$` 管理共享。** 该共享被禁用则 PsExec 失效。
8. **`-i` 不指定 session 时在控制台会话运行** —— 远程桌面用户可能看不到 UI。
9. **`-s` 与 `-e` 互斥。**
10. **无独立安装包。** 官方安装说明只是「把 PsExec 拷到可执行路径下」，下载入口是 `PsTools.zip`（约 5 MB）套件，**页面未提供单独版本号**。
11. **维护停滞（2023-04-11）。** 优先考虑 PowerShell Remoting。
12. **`-arm` 与 `-verbose` 官方网页未记载**，仅在二进制 usage 中，行为未经本篇实测。

## 分发

**没有独立的 winget 包** —— PsExec 归入 `Microsoft.Sysinternals.PsTools`。

```
PsExec.exe     716,176   x86      PsExec64.exe   833,472   x64
（ARM64 为 PsExec64a.exe）
```

`PsTools.zip` 约 5 MB。支持范围：客户端 Windows 8.1+，服务器 Windows Server 2012+。

**文档中给安装命令时不能写 `winget install Microsoft.Sysinternals.PsExec`** —— 该包不存在。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/psexec
- MITRE ATT&CK S0029：https://attack.mitre.org/software/S0029/

> **本篇事实边界：** 完整语法与绝大部分参数描述提取自 `PsExec64.exe` v2.43 二进制内嵌 usage（与官方页面一致的部分已交叉核对）。`-arm`、`-verbose`、`-g` 官方网页未记载。`-accepteula` / `-nobanner` 的定义、模拟与网络资源限制、口令加密传输、杀软误报说明、无独立安装包均来自官方页面（`ms.date` 2023-03-30，Published 2023-04-11，页面更新 2023-10-18）。ADMIN$ 依赖、临时服务创建、ATT&CK 归类与团伙列表来自 MITRE ATT&CK S0029（Created 2017-05-31，last modified 2026-05-12，page version 1.7，ATT&CK v19）。PowerShell Remoting 替代建议、`-p` 泄露风险为实践经验总结。
