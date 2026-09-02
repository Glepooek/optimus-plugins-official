# Strings 与 Sigcheck

两个二进制取证类小工具，均为**纯 CLI，无 GUI**。合并成篇因为各自开关不多且常配合使用。

- **Strings** v2.54（2021-06-22，**维护停滞 5 年**）· https://learn.microsoft.com/en-us/sysinternals/downloads/strings
- **Sigcheck** v2.91（2026-02-04，活跃）· https://learn.microsoft.com/en-us/sysinternals/downloads/sigcheck

---

# Strings

## 定位

在二进制文件中搜索 ANSI 与 UNICODE 字符串。官方原文说明了它存在的理由：

> executables and object files will many times have embedded UNICODE strings that you cannot easily see with a standard ASCII strings or grep programs

**关键特性：全文件扫描，不解析 PE 结构。** 它逐字节扫过整个文件找可打印字符序列，不理解节区、导入表、资源。这既是优点（能找到任何位置的字符串）也是局限（无法告诉你字符串在哪个节区、是否被引用）。

## 语法

```
strings [-a] [-f offset] [-b bytes] [-n length] [-o] [-q] [-s] [-u] <file or directory>
```

**支持文件名通配符。**

## 参数表（官方原文译）

| 参数 | 官方描述 |
|---|---|
| `-a` | 仅 ASCII 搜索（**默认是 Unicode + ASCII 都搜**） |
| `-u` | 仅 Unicode 搜索（默认两者都搜） |
| `-n <length>` | **最小字符串长度（默认 3）** |
| `-o` | 打印字符串在文件中的偏移 |
| `-f <offset>` | 从指定文件偏移开始扫描 |
| `-b <bytes>` | 扫描的字节数 |
| `-s` | 递归子目录 |
| `-q` | （语法中列出，官方参数表未描述） |
| `-nobanner` | 不显示启动横幅与版权信息 |
| `-accepteula` | 抑制 EULA 弹窗 |

**默认最小长度 3 会产生大量噪音** —— 三字符的偶然序列极多。实用起点是 `-n 8` 或更高。

## 实用配方

官方给出的基础用法：

```cmd
strings * | findstr /i TextToSearchFor
```

更实用的形式：

```powershell
# 找硬编码的 URL / IP（最小长度 8 降噪）
strings64.exe -accepteula -nobanner -n 8 suspicious.exe | Select-String -Pattern 'https?://|\d+\.\d+\.\d+\.\d+'

# 找可能的凭据关键字
strings64.exe -nobanner -n 6 app.exe | Select-String -Pattern 'password|passwd|secret|token|api[_-]?key' -CaseSensitive:$false

# 带偏移，便于后续用十六进制编辑器定位
strings64.exe -nobanner -o -n 10 app.exe

# 递归扫整个目录
strings64.exe -nobanner -s -n 10 C:\suspect\ | Out-File strings.txt

# 只扫文件头部（PE 头与导入表区域，速度快）
strings64.exe -nobanner -b 4096 app.exe

# 只看 Unicode（.NET 程序的字符串多为 Unicode）
strings64.exe -nobanner -u -n 8 managed.exe
```

## 与替代方案

| 工具 | 优势 | 劣势 |
|---|---|---|
| **Strings** | 同时搜 Unicode + ASCII；简单 | 不解析 PE 结构；**维护停滞 5 年** |
| `Select-String` on raw bytes | 原生 | 处理 Unicode 麻烦 |
| **VMMap** 的 `View → Strings` | 扫**进程内存**而非磁盘文件 | 只能对运行中的进程，见 [vmmap-gui.md](vmmap-gui.md#strings-视图) |
| Ghidra / IDA | 理解 PE 结构，能看交叉引用 | 重量级 |

**排查「这块内存里装的是什么」用 VMMap 的 Strings 视图；排查「这个文件里有什么」用 Strings 工具。**

## 常见坑

1. **默认最小长度 3，噪音极大。** 实用起点 `-n 8`。
2. **默认同时搜 Unicode 与 ASCII。** `-a` / `-u` 是**限制**为单一编码，不是启用。
3. **不解析 PE 结构。** 找到字符串不代表它被代码引用。
4. **维护停滞（2021-06-22）。** 本目录中最久未更新的工具。
5. **输出可能含敏感信息。** 扫描自己的程序时可能暴露内部路径、密钥。
6. 运行环境：客户端 Windows Vista+，服务器 Windows Server 2008+，Nano Server 2016+。下载包 534 KB。

---

# Sigcheck

## 定位

验证文件的数字签名、版本信息与哈希，并可集成 VirusTotal 查询。**排查可疑二进制来源的首选。**

v2.91（2026-02-04）**维护活跃**，与 Strings 形成对比。

## 四套语法

官方 usage 给出四套独立语法（**官方网页未完整记载后三套**）：

```
① 常规扫描
sigcheck [-a][-h][-i][-e][-l][-n][[-s]|[-c|-ct]|[-m]][-q][-p <policy GUID>]
         [-r][-u][-vt][-v[r][s]][-f catalog file] [-w file] <file or directory>

② 转储 catalog 文件内容
sigcheck -d [-c|-ct] [-w file] <file or directory>

③ 离线 VirusTotal 查询（对已采集的 CSV）
sigcheck -o [-vt][-v[r]] [-w file] <csv file>

④ 转储证书存储
sigcheck -t[u][v] [-i] [-c|-ct] [-w file] <certificate store name|*>
```

## 参数表（官方 usage 原文译）

### 扫描与输出

| 参数 | 说明 |
|---|---|
| `-e` | **只扫描可执行映像**（不管扩展名是什么） |
| `-s` | 递归子目录 |
| `-l` | 遍历符号链接与目录联接点 |
| `-h` | 显示文件哈希 |
| `-a` | 显示扩展版本信息（**含熵值 entropy 度量**） |
| `-n` | 只显示文件版本号 |
| `-c` | CSV 输出（逗号分隔） |
| `-ct` | CSV 输出（制表符分隔） |
| `-w <file>` | **把输出写入指定文件** |
| `-q` | 安静模式 |
| `-nobanner` | 抑制横幅 |
| `-accepteula` | 抑制 EULA 弹窗 |

### 签名验证

| 参数 | 说明 |
|---|---|
| `-i` | 显示 catalog 名称与签名链 |
| `-f <catalog file>` | 在指定 catalog 文件中查找签名 |
| `-p <policy GUID>` | 按指定策略验证签名 |
| `-r` | **禁用证书吊销检查** |
| `-m` | 转储 manifest |
| `-d` | 转储 catalog 文件内容 |
| `-t[u][v]` | 转储指定证书存储（`*` 为全部） |

**`-a` 的熵值度量是识别加壳/加密二进制的实用信号** —— 正常 PE 的熵约 6.x，加壳后接近 8.0（接近随机）。官方 usage 提到熵度量但未给判据。

**`-r` 在离线环境有用**（吊销检查需要联网，否则每个文件都要等超时），但会降低验证强度。

### VirusTotal

| 参数 | 说明 |
|---|---|
| `-v` | 按**哈希**查询 VirusTotal |
| `-vr` | 对检出非零的文件**自动打开在线报告页** |
| `-vs` | **上传** VirusTotal 未收录过的文件本体 |
| `-vt` | **接受 VirusTotal 服务条款**（必需） |
| `-u` | 未启用 VT 时：只列**未签名**文件；启用 VT 后：列 VT **未知或检出非零**的文件 |
| `-o` | 对已采集的 CSV 中的哈希批量做 VT 查询 |

## 关键坑：`-vt` 与 `-accepteula` 是两个独立开关

**Sigcheck 两个都有**（与 [autorunsc](autorunsc-cli.md) 只有 `-vt` 不同）：

| 开关 | 接受什么 |
|---|---|
| `-accepteula` | **Sysinternals 自身**的 EULA |
| `-vt` | **VirusTotal** 的服务条款 |

省略 `-vt` 时工具会**交互式弹出提示**，在脚本/自动化场景会阻塞。

```powershell
# ❌ 会阻塞
sigcheck64.exe -accepteula -v C:\suspect\

# ✅ 正确
sigcheck64.exe -accepteula -vt -v C:\suspect\
```

## VirusTotal 三个开关的分界（官方权威定义）

**这是 Sysinternals 工具族「哈希查询 vs 文件上传」分界的官方权威定义所在：**

| 开关 | 行为 | 隐私影响 |
|---|---|---|
| `-v` | **只按文件哈希比对** | 低 |
| `-vr` | 对检出非零的文件打开报告页 | 低 |
| `-vs` | **把 VT 未收录过的文件真正上传** | **高。文件被上传到第三方并可能公开** |

**官方明确：上传后扫描结果可能需要 5 分钟以上才可用。**

**生产环境只用 `-v`，绝不用 `-vs`。**

## 核心配方：找未签名的可执行文件

官方给出的典型排查用法：

```powershell
sigcheck -u -e c:\windows\system32
```

- `-e` 只扫可执行映像（不管扩展名）
- `-u` 未启用 VT 时仅列**未签名**文件

**官方建议对任何未签名文件都要追查其来源用途。**

```powershell
# 完整形式：递归 + 哈希 + CSV
sigcheck64.exe -accepteula -nobanner -u -e -s -h -c C:\Windows\System32 > unsigned.csv

# 加 VT 哈希查询（只列未签名或 VT 有检出的）
sigcheck64.exe -accepteula -nobanner -u -e -s -v -vt -c C:\suspect > suspicious.csv

# 加熵值（识别加壳）
sigcheck64.exe -accepteula -nobanner -a -e -s -c C:\suspect > with-entropy.csv

# 输出直接写文件（比重定向更可靠，避免编码问题）
sigcheck64.exe -accepteula -nobanner -u -e -s -h -c -w C:\out\scan.csv C:\suspect
```

## 离线系统两阶段取证（官方支持）

**这是 Sigcheck 最有价值的能力：避免把离线/隔离系统接入网络。**

```powershell
# 阶段一：在目标（离线）机采集哈希，导出 CSV
sigcheck64.exe -accepteula -nobanner -h -e -s -r -c -w E:\evidence\hashes.csv C:\

# 阶段二：把 CSV 拷到有网络的机器，批量做 VT 查询
sigcheck64.exe -accepteula -nobanner -o -v -vt E:\evidence\hashes.csv
```

`-o` 就是为此设计的（官方原文：`This usage is intended for scans of offline systems.`）。阶段一加 `-r` 禁用吊销检查，避免每个文件等联网超时。

## 证书存储与 catalog

```powershell
# 转储所有证书存储（排查被植入的根证书）
sigcheck64.exe -accepteula -nobanner -t * -c > certs.csv

# 转储 catalog 文件内容
sigcheck64.exe -accepteula -nobanner -d C:\Windows\System32\CatRoot\...\xxx.cat
```

**`-t *` 转储证书存储是排查「中间人证书被植入」的手段** —— 恶意软件或企业代理会向根存储添加自己的 CA。官方网页未记载此语法。

## 常见坑

1. **`-vt` 与 `-accepteula` 是两个独立开关，都要加。** 缺 `-vt` 会阻塞脚本。
2. **`-vs` 会上传文件本体。** 生产环境只用 `-v`。
3. **VT 结果可能延迟 5 分钟以上。**
4. **`-u` 的语义随 VT 是否启用而变。** 未启用时列未签名；启用后列 VT 未知或检出非零。
5. **检出数非零 ≠ 恶意，为零 ≠ 安全。** 自研工具与打包器常被误报。
6. **`-e` 才是「按内容判断是否可执行」。** 不加 `-e` 会按扩展名扫，漏掉伪装成 `.dat` 的 PE。
7. **`-r` 降低验证强度。** 只在离线环境为避免超时使用。
8. **熵值无官方判据。** 经验值：正常 PE 约 6.x，加壳接近 8.0。
9. **后三套语法官方网页未完整记载**（`-d` / `-o` / `-t`），来自二进制 usage。
10. 运行环境：客户端 Windows 8.1+，服务器 Windows Server 2012+，Nano Server 2016+。

---

## 分发

```
strings.exe    370,056   x86      strings64.exe    478,088   x64
sigcheck.exe   437,792   x86      sigcheck64.exe   527,944   x64
（ARM64 为 *64a.exe）
```

winget 包名 `Microsoft.Sysinternals.Strings` / `Microsoft.Sysinternals.Sigcheck`。

## 官方文档

- Strings：https://learn.microsoft.com/en-us/sysinternals/downloads/strings（228 词）
- Sigcheck：https://learn.microsoft.com/en-us/sysinternals/downloads/sigcheck
- **工具自带：`strings.exe -?` / `sigcheck.exe -?`**

> **本篇事实边界：**
> **Strings** —— 语法、全部参数描述、默认最小长度 3、默认搜 Unicode+ASCII、支持通配符、`strings * | findstr` 示例、运行环境与体积（534 KB）均来自官方页面原文（`ms.date` / `updated_at` 均为 2021-06-22）。`-q` 在官方语法行中出现但参数表未描述，本篇如实标注。`-n 8` 降噪起点为实践经验。
> **Sigcheck** —— `-v` / `-vr` / `-vs` 的分界与 5 分钟延迟、`-vt` 与 `-accepteula` 独立、`-u -e c:\windows\system32` 典型用法与「追查未签名文件来源」建议、`-h` + `-c`/`-ct` + `-o` 两阶段离线流程、运行环境均来自官方页面（发布 2026-02-04）。**四套语法全文与 `-a`（熵值）、`-l`、`-p`、`-r`、`-m`、`-d`、`-t[u][v]`、`-f`、`-w`、`-i`、`-q` 提取自 `sigcheck64.exe` v2.91 二进制内嵌 usage**，官方网页未完整记载。熵值判据（6.x vs 8.0）、`-t *` 排查植入根证书、`-r` 在离线场景的用途为实践经验总结。
