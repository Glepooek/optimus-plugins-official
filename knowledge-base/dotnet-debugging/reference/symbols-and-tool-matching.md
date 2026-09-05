# 符号与工具匹配

> SOS 命令报错、方法名显示为地址、`!clrstack` 输出空栈——这类问题九成不是分析思路错了，而是符号或 SOS 版本没配对。本篇是全部 `sos-*` 命令的前置条件。

dump 位数匹配见 `reference/dump-types-and-capability.md § 2. 位数必须匹配`，本篇只讲符号与 SOS 版本。

## 1. PDB 类型：portable 与 Windows PDB

PDB（Program Database）保存源码行号、局部变量名等调试信息，与二进制程序集分离存放。存在两种格式：

- **Windows PDB**：随 .NET Framework 第一版一同出现，格式复杂且长期未公开文档化，仅能在 Windows 上生成与读取。
- **Portable PDB**：跨平台格式，可在 Windows/Linux/macOS 上生成与读取，体积通常小于同等内容的 Windows PDB，是 .NET Core 及以后版本的默认输出格式。

两者的调试器支持面不同：`dotnet-dump analyze` 与 lldb+SOS 组合只认 Portable PDB；WinDbg 对两种格式均能读取。用 .NET Framework 项目产出的 dump 配 Windows PDB，用 .NET 6+ 项目产出的 dump 配 Portable PDB，是默认场景下的对应关系——项目显式配置 `<DebugType>` 时才会偏离这一默认。

**嵌入式 PDB**（`<DebugType>embedded</DebugType>`）把调试信息直接打进程序集文件内部，不再产生独立的 `.pdb` 文件。取舍在于：省去了单独分发/上传符号文件的步骤，但程序集体积随之增大，且无法单独更新符号（改符号必须重新编译整个程序集）。

**SourceLink** 让调试器在有符号但没有本地源码副本的情况下（例如引用了某个 NuGet 包的源码）仍能定位到源码行：Portable PDB 内嵌一段 JSON，把编译时的本地路径映射到源码托管平台（如 GitHub）上的原始文件 URL，调试器据此按需下载对应版本的源码内容用于展示。这一机制依赖符号文件本身携带该映射信息——如果符号缺失或版本不匹配，SourceLink 同样不可用。

## 2. 符号服务器与符号缓存

**Windows（WinDbg）**：微软公共符号服务器地址为 `https://msdl.microsoft.com/download/symbols`，通过环境变量 `_NT_SYMBOL_PATH` 配置：

```
set _NT_SYMBOL_PATH=srv*C:\Symbols*https://msdl.microsoft.com/download/symbols
```

语法为 `srv*<本地缓存目录>*<符号服务器地址>`，中间用 `*` 分隔。首次加载某个符号文件时从服务器下载并缓存到本地目录，后续加载同一文件直接读本地缓存，不重复下载。WinDbg 内也可用快捷命令 `.symfix c:\MyCache` 等效设置该路径。多个符号源可用 `;` 串联（如 `.sympath C:\MyRegularSymbols;srv*C:\MyServerSymbols*https://msdl.microsoft.com/download/symbols`）；缓存目录是 `srv*` 元素自身携带的参数，需要缓存的每个 `srv*` 元素各自在其内部指定，并非在整条路径最左侧统一写一次——那是 `cache*` 前缀的语义（`cache*` 出现时，其右侧全部元素下载的符号统一存入该目录），与 `srv*` 内嵌缓存目录是两种不同写法，不要混用。

**Linux/macOS（dotnet-dump / lldb）**：没有 `_NT_SYMBOL_PATH` 这一机制，改用 `dotnet-symbol` 工具为 dump 补齐符号、DAC/DBI 与模块文件：

```
dotnet tool install --global dotnet-symbol
dotnet-symbol /tmp/dump/coredump.32232
```

不带任何开关时，`dotnet-symbol` 会为目标 dump 下载全部所需内容（符号、模块、DAC/DBI）。仅需 lldb 加载 dump 本身（不深入分析符号内容）时可用 `--host-only --debugging` 缩小下载范围：

```
dotnet-symbol --host-only --debugging /tmp/dump/coredump.32232
```

`dotnet-symbol` 默认从微软公共符号服务器下载，仅覆盖官方渠道发布的 .NET Core 运行时版本——用本地构建或 Linux 发行版自带的运行时产生的 dump，下载会返回 404，此时需要从产生 dump 的原始环境里手动拷贝 `dotnet`、`libcoreclr.so`、`libmscordaccore.so` 等文件。

## 3. SOS 与运行时版本匹配

SOS（Son of Strike）是读取 CLR 内部数据结构（托管堆、线程、方法表等）的调试器扩展，本身不含运行时数据的解析逻辑——真正解析工作由 **DAC**（Data Access Component）完成，SOS 只是调用 DAC 提供的接口后格式化输出。三种运行时下 SOS 的加载方式不同：

### .NET Framework 4.x（WinDbg）
```
.loadby sos clr
```
`clr` 是 4.x 的运行时模块名（2.0 时代是 `mscorwks`）。`.loadby` 从已加载的运行时模块所在目录取同版本的 `sos.dll`，这正是它比手动 `.load <路径>` 可靠的原因——手动指定路径容易加载到与当前进程运行时版本不匹配的 SOS。

### .NET 6/8+（WinDbg 或 lldb）
```
dotnet-sos install
```
一次安装将 SOS 写入调试器配置（Linux/macOS 下写入 `.lldbinit`），后续每次启动调试器自动加载。WinDbg 10.0.18317.1001 及以上版本会从微软扩展库自动加载 SOS，无需手动安装；`dotnet-sos install` 主要用于 Linux/macOS 或较旧版本的 WinDbg。

### .NET 6/8+（dotnet-dump，推荐）
```
dotnet-dump analyze <dump 文件>
```
内置 SOS，无需单独加载；进入交互式会话后命令前缀可省略 `!`（`dumpheap -stat` 与 `!dumpheap -stat` 等价，两种写法都被接受）。

### DAC 必须与运行时版本完全匹配

DAC 文件名随运行时不同：.NET Framework 是 `mscordacwks.dll`，.NET Core/5+ 是 `mscordaccore.dll`（Linux 下为 `libmscordaccore.so`）。DAC 与产生 dump 的运行时版本只要存在差异（即使只是补丁号不同），就无法正确解析托管堆结构。版本错配的典型报错形态：

```
The version of SOS does not match the version of CLR you are debugging.
Please load the matching version of SOS for the version of CLR you are debugging.
```

或加载 DAC 本身失败：

```
Failed to load data access DLL, 0x80004005
```

**补救**：先用 `.cordll -ve -u -l` 强制重新加载并查看 DAC 的搜索路径与期望版本，再用 `!setclrpath <目录>` 手动指定包含匹配版本 DAC 的目录（该目录通常是目标机器上对应版本的运行时安装目录，或用 `dotnet-symbol`/符号服务器下载到的缓存目录）：

```
!setclrpath "C:\Program Files\dotnet\shared\Microsoft.NETCore.App\8.0.10"
```

`dotnet-dump analyze` 环境下等价命令是 `setclrpath <path>`（无需 `!` 前缀），常见触发场景是分析一份在其他机器上生成的 dump，本机没有对应版本的运行时安装。

## 4. 缺符号时的降级读法

托管方法名来自 CLR 的**元数据**（程序集内嵌的类型与方法签名表），不依赖 PDB——因此即使完全没有符号文件，`!clrstack` 仍能显示完整的类名与方法名，只是缺少源码行号（显示为纯地址偏移而非 `文件名 @ 行号`）。这是判断"当前问题需不需要补符号"的依据：如果排查目标只是确认调用链经过了哪些方法（例如判断某个业务方法是否在栈上、区分是哪个重载被调用），托管栈本身已经足够，不必额外花时间补符号。

非托管帧的退化程度更彻底：没有对应的 PDB 或系统符号时，非托管调用栈只能显示为裸地址加模块名（如 `ntdll!Unknown+0x1234` 或纯十六进制地址），无法解析出具体函数名。这类信息缺失只能靠补齐系统符号（Windows 系统 DLL 走 `_NT_SYMBOL_PATH` 指向的公共符号服务器即可覆盖大多数情况）解决。

据此，判据可以简化为：**问题结论如果只依赖托管栈（方法名、参数类型、异常类型），符号缺失不影响分析，不必补符号重新分析；一旦涉及非托管代码路径（如 P/Invoke 调用卡在哪个系统函数、非托管死锁），补齐符号才能继续解析非托管帧**。
