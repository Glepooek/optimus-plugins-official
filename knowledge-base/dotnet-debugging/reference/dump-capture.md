# dump 抓取命令

> 本篇给出五种抓取工具的完整可执行命令。选哪种类型（`Mini`/`Heap`/`Triage`/`Full`）见 `reference/dump-types-and-capability.md`；dump 文件抓到之后的合规处置见 `rules/01-dump-handling.md`。

每节固定四段结构：用途与前置条件 / 语法与关键开关 / 输出与产物位置 / 判据。

## 1. procdump（Windows，全运行时）

### 用途与前置条件
Sysinternals 出品的命令行工具，需单独下载（`https://download.sysinternals.com/files/Procdump.zip`），不随 Windows 或 .NET 运行时预装。对 .NET Framework 4.x 与 .NET 6+ 同等适用，是 Windows 上唯一覆盖全部 .NET 运行时的抓取工具。首次运行需接受 Sysinternals 许可协议，命令行加 `-accepteula` 可跳过交互式确认，自动化场景必带。

### 语法与关键开关

抓挂起进程的 Full dump（进程窗口无响应超过 5 秒，手动介入）：
```
procdump -accepteula -ma -h <PID>
```

崩溃时自动抓（等到未处理异常即 2nd chance；含 1st chance 用 `-e 1`）：
```
procdump -accepteula -ma -e <进程名>
```

CPU 打满时抓（单核相对占用超过 80%、持续 5 秒，连抓 3 个，每次间隔按下次触发计算）：
```
procdump -accepteula -ma -c 80 -s 5 -n 3 -u <PID>
```

**`-c` 的阈值默认按全核总量计算**，`-u` 才改为按单核相对计算。这个差异决定命令会不会触发：单线程死循环在 8 核机上只占总 CPU 的 12.5%、在 16 核机上只占 6.25%，不加 `-u` 时 `-c 80` 永远等不到触发，且 procdump 不会报错，只是一直等待。查单线程热点（死循环、自旋等待）必带 `-u`；查进程整体 CPU 压力（多线程并行打满）则不加 `-u`，此时阈值针对全核总量才有意义。

按性能计数器阈值抓（句柄数超过 10000 时抓，对应「句柄耗尽」征象）：
```
procdump -accepteula -ma <PID> -p "\Process(<进程名>)\Handle Count" 10000
```

按提交内存阈值抓（提交量超过 4096 MB 时抓，对应「内存持续增长」征象）：
```
procdump -accepteula -ma -m 4096 <PID>
```

等待进程启动后再监控异常（进程尚未运行、需要覆盖启动阶段崩溃）：
```
procdump -accepteula -e -w <进程名>
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `-ma` | 写 Full dump（含全部内存：镜像/映射/私有） | 默认写 `-mm` Mini dump，无堆对象数据，查不了泄漏 |
| `-mt` | 写 Triage dump（模块/线程/异常信息与全部栈，尝试脱敏但不保证完全，见 `reference/dump-types-and-capability.md § 1. 四种类型的能力对照`） | procdump 是 Windows 上唯一覆盖 .NET Framework 4.x 的抓取工具，该运行时下 `-mt` 是产出 Triage dump 的唯一途径 |
| `-e [1]` | 未处理异常即抓（2nd chance）；加 `1` 则含已处理的 1st chance 异常 | 不设 `-e` 则不监控异常，仅覆盖 CPU/挂起/手动等其他触发条件 |
| `-h` | 进程出现挂起窗口（无响应超 5 秒）时抓 | 挂起类问题（UI 卡死、非托管死锁）不会自动触发抓取 |
| `-c <阈值> -s <秒数>` | CPU 使用率超过阈值且持续指定秒数才抓 | 不设 `-s` 时默认 10 秒；不设 `-c` 则不按 CPU 触发 |
| `-u` | 与 `-c` 连用，把 CPU 阈值改为按单核相对计算 | `-c` 按全核总量计算，单线程满载在 8 核机上仅 12.5%，`-c 80` 永不触发且无任何报错提示 |
| `-p <计数器> <阈值>` | 指定性能计数器达到或超过阈值时抓（计数器名与实例名可能区分大小写） | 只能按 CPU/内存/异常等内置条件触发，无法针对句柄数、线程数等其他计数器 |
| `-m <MB>` | 提交内存（commit）达到指定 MB 时抓 | 内存增长类问题只能靠人守着手动抓，错过增长拐点 |
| `-n <次数>` | 连抓 N 个后退出 | 默认只抓 1 个，无法对比不同时刻的堆增长 |
| `-w` | 等待指定进程名启动 | 只能抓已运行进程，启动即崩的场景抓不到 |
| `-64` | 64 位 Windows 上强制对 32 位目标抓 64 位 dump（仅用于 WOW64 子系统调试） | 默认按目标进程实际位数抓，与目标位数不一致会导致后续分析用错位数的调试器 |

### 输出与产物位置
默认落在当前工作目录，文件名形如 `<进程名>_<年月日>_<时分秒>.dmp`；异常触发时文件名会带上 `EXCEPTIONCODE` 替换符。`-n` 连抓时依时间戳自动区分，不覆盖前一个文件。

### 判据
`-n 3` 连抓多个 dump 后对比各自的 `!dumpheap -stat` 输出，是**在没有时间线采样工具时**判断"哪类对象在涨"的替代手段——这是一期能给出的最接近趋势分析的做法（见 `reference/dump-types-and-capability.md § 3. dump 是单时点快照`）。目标为 .NET 5+ 且可安装诊断工具时，应优先用 `reference/dotnet-counters.md § 2. dotnet-counters collect` 采集时间线，连抓 dump 退化为受限环境下的备选。若三次抓取中同一类型对象计数持续上升且不回落，指向该类型对象存在泄漏或持有链异常，需转 `reference/sos-heap-and-objects.md` 定位持有者。

`-p` 与 `-m` 把抓取时机绑定到征象本身的阈值上，解决的是**抓取时刻与问题窗口不重合**这一困难：定时抓或手动抓都可能落在进程状态正常的时段，而阈值触发保证 dump 一定抓在指标越界的那一刻。句柄耗尽用 `-p "\Process(<进程名>)\Handle Count" <阈值>`，内存增长用 `-m <MB>`，两者都能无人值守长时间挂起等待。阈值应取"明显高于正常基线但尚未到故障"的值——取太高会抓在进程已经不可用之后，取太低会在正常波动时误抓。

## 2. dotnet-dump collect（.NET Core 3.0+，跨平台）

### 用途与前置条件
微软官方 .NET 全局工具，跨 Windows/Linux/macOS，仅支持 .NET Core 3.0+（不覆盖 .NET Framework）。安装：
```
dotnet tool install --global dotnet-dump
```
安装后需以与目标进程相同的用户身份运行（或 root/管理员），否则无法与目标进程建立诊断连接。抓取前用 `dotnet-dump ps` 列出可抓取的 .NET 进程及其 PID。

### 语法与关键开关

用 PID 抓取（默认 `Full` 类型）：
```
dotnet-dump collect -p <PID>
```

指定输出路径与 Heap 类型（不含模块镜像，体积远小于 Full，覆盖绝大多数泄漏排查场景）：
```
dotnet-dump collect -p <PID> --type Heap -o /data/dump/heap.dmp
```

按进程名抓取：
```
dotnet-dump collect -n <进程名>
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `--type <Full\|Heap\|Mini\|Triage>` | 指定 dump 类型 | 不指定时默认 `Full`，体积最大；若目标运行在有内存上限的容器中，`Full`/`Heap` 抓取期间的内存翻页可能触发容器 OOM Kill——需评估容器内存上限是否留有余量 |
| `-o <路径>` | 指定输出文件完整路径 | 不指定时 Windows 落 `.\dump_YYYYMMDD_HHMMSS.dmp`，Linux/macOS 落 `./core_YYYYMMDD_HHMMSS` |
| `--diag` | 开启抓取过程诊断日志 | 抓取失败（如连接超时）时缺少诊断信息，难以定位是权限问题还是 `TMPDIR` 不一致 |

`dotnet-dump collect --type Triage` 可产出 `Triage` dump——官方文档在 `--type` 选项签名处只写 `<Full|Heap|Mini>`、概述句也称"共三种类型"，但紧随其后的取值列表实际列出了第四项 `Triage`，这是文档自身签名与取值列表不一致导致的常见误读（详见 `reference/dump-types-and-capability.md § 1. 四种类型的能力对照`）。跨平台场景下需要脱敏对外交付时：
```
dotnet-dump collect -p <PID> --type Triage -o /data/dump/triage.dmp
```
与 `DOTNET_DbgMiniDumpType` 环境变量（见 `§ 5. DOTNET_DbgEnableMiniDump（.NET Core 3.0+，崩溃自动抓取）`）、`createdump` 的 `-t` 开关（见 `§ 3. createdump（.NET Core 3.0+，Linux 优先）`）是同一枚举语义在不同接口下的暴露方式。

Linux/macOS 上，`dotnet-dump` 与目标进程必须共享同一个 `TMPDIR` 环境变量，否则连接会超时；容器内跨容器抓取需要 `--cap-add=SYS_PTRACE`（见 `§ 3. createdump（.NET Core 3.0+，Linux 优先）` 的容器约束，二者共用同一套 ptrace 权限要求）。

### 输出与产物位置
`-o` 未指定时，Windows 默认 `.\dump_YYYYMMDD_HHMMSS.dmp`；Linux/macOS 默认 `./core_YYYYMMDD_HHMMSS`。容器场景下注意输出路径是相对**目标进程的文件系统视角**解释的，不是发起抓取命令的 sidecar 容器视角——跨容器抓取时建议用共享卷并写绝对路径，避免文件写到了目标容器内部而外部访问不到。

### 判据
`dotnet-dump collect` 只负责抓取，不含分析能力之外的判据——抓完后用 `dotnet-dump analyze <dump_path>` 进入交互式 SOS 命令环境（`dumpheap`、`clrstack`、`syncblk` 等），具体命令与输出解读见 `reference/sos-threads-and-stacks.md`、`reference/sos-heap-and-objects.md`、`reference/sos-locks-and-async.md`。相对 WinDbg，`dotnet-dump analyze` 不是原生调试器，不支持显示原生栈帧，仅覆盖托管侧分析——涉及非托管代码调用栈的问题仍需 WinDbg 或 `lldb` 配合 SOS 插件。

## 3. createdump（.NET Core 3.0+，Linux 优先）

### 用途与前置条件
`createdump` 随 .NET Core 3.0+ 运行时一同安装，无需单独下载，路径位于运行时安装目录下（`dotnet --list-runtimes` 可定位版本目录）：
- Linux：`/usr/share/dotnet/shared/Microsoft.NETCore.App/<版本号>/createdump`
- Windows：`C:\Program Files\dotnet\shared\Microsoft.NETCore.App\<版本号>\createdump.exe`

它既是运行时崩溃时自动调用的内部工具（见 `§ 5. DOTNET_DbgEnableMiniDump（.NET Core 3.0+，崩溃自动抓取）`），也可手动对任意运行中的 .NET Core 进程调用。手动调用需要 `ptrace`（`CAP_SYS_PTRACE`）权限，普通用户需以 `sudo`/`su` 运行；容器场景见下方约束。

**容器内两个前置条件**：
1. `createdump` 进程与目标进程必须处于同一 PID namespace——跨 PID namespace 无法通过 `/proc/<pid>/` 解析到目标进程，抓取会直接失败或抓到错误进程。
2. 容器需具备 `SYS_PTRACE` capability，即启动容器时带 `--cap-add=SYS_PTRACE`（或 `--privileged`），否则内核层面直接拒绝 ptrace 调用，与文件权限无关。

### 语法与关键开关

手动对运行中进程抓 Heap dump（默认类型）：
```
sudo /usr/share/dotnet/shared/Microsoft.NETCore.App/8.0.10/createdump -f ~/dumps/coredump.%p <PID>
```

抓 Full dump（含全部内存）：
```
sudo /usr/share/dotnet/shared/Microsoft.NETCore.App/8.0.10/createdump -u -f /tmp/coredump.%p <PID>
```

抓 Triage dump（脱敏，供外发）：
```
sudo /usr/share/dotnet/shared/Microsoft.NETCore.App/8.0.10/createdump -t -f /tmp/coredump.triage.%p <PID>
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `-n, --normal` | 写 Mini dump | — |
| `-h, --withheap` | 写 Heap dump（**默认行为**，不加任何类型开关时即此类型） | 若误以为默认是 Mini，会拿到比预期大得多的 dump |
| `-t, --triage` | 写 Triage dump | 不脱敏，外发前需人工处理敏感信息 |
| `-u, --full` | 写 Full dump | 默认（Heap）不含模块镜像，某些反汇编场景数据不全 |
| `-f, --name <路径模板>` | 指定输出路径，支持 `%p`（PID）、`%e`（可执行文件名）、`%h`（主机名）、`%t`（Epoch 秒数）占位符 | 默认 Linux 落 `/tmp/coredump.%p`，Windows 落 `%TEMP%\dump.%p.dmp` |
| `-d, --diag` | 开启诊断日志 | 抓取失败时无诊断输出 |

PID 是位置参数，直接跟在命令末尾，无需专门开关。

### 输出与产物位置
未指定 `-f` 时，Linux 落 `/tmp/coredump.<PID>`，Windows 落 `%TEMP%\dump.<PID>.dmp`。容器场景下该路径是容器内部路径，需配合共享卷挂载才能在容器外访问到产物。

### 判据
`createdump` 手动调用的价值在于：运行时自动触发的自动抓取（WER 或 `DOTNET_DbgEnableMiniDump`）只在崩溃时生效，若需要在进程**仍存活但状态异常**（如已观察到内存持续增长但尚未崩溃）时立即取证，只能用 `createdump` 或 `dotnet-dump collect` 手动介入；`createdump` 相对 `dotnet-dump collect` 的优势是不需要额外安装全局工具，运行时自带即可用，适合镜像精简、不便安装额外工具的容器场景。

## 4. WER LocalDumps（Windows，崩溃自动抓取）

### 用途与前置条件
Windows Error Reporting（WER）的本地转储功能，系统级、对进程模型不做区分——.NET Framework 4.x、.NET 6+、乃至任意 Win32 进程崩溃时均可触发，无需目标进程做任何配置。默认不启用，需管理员权限修改注册表启用。这是进程崩溃退出、事后才发现需要 dump 时**唯一能补救的手段**——前提是启用发生在崩溃之前；崩溃已经发生且未启用 LocalDumps 的场景，dump 已永久丢失。

### 语法与关键开关

全局启用（对所有进程生效），注册表键路径：
```
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps
```

用 PowerShell 创建键并设置全局配置：
```powershell
New-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps" -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps" -Name "DumpFolder" -Value "C:\Dumps" -Type ExpandString
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps" -Name "DumpCount" -Value 10 -Type DWord
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps" -Name "DumpType" -Value 2 -Type DWord
```

只对某个进程生效（在 `LocalDumps` 下新建以进程文件名命名的子键，值覆盖全局设置）：
```powershell
New-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\MyApp.exe" -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\MyApp.exe" -Name "DumpType" -Value 2 -Type DWord
```

| 值 | 类型 | 含义 | 不设的后果 |
|---|---|---|---|
| `DumpFolder` | `REG_EXPAND_SZ` | dump 文件存放目录，需确保目录 ACL 允许崩溃进程写入 | 默认 `%LOCALAPPDATA%\CrashDumps`；服务崩溃则写入服务专属 profile 目录（`%WINDIR%\ServiceProfiles` 或 `%WINDIR%\System32\Config\SystemProfile`） |
| `DumpCount` | `REG_DWORD` | 目录内保留的最大 dump 文件数，超出后最旧的被新的替换 | 默认 10 |
| `DumpType` | `REG_DWORD` | `0`=Custom（配合 `CustomDumpFlags` 位掩码自定义）；`1`=Mini dump；`2`=Full dump | 默认 `1`（Mini），排查内存问题时会发现拿到的 dump 没有堆数据 |
| `CustomDumpFlags` | `REG_DWORD` | `DumpType=0` 时生效的自定义位掩码（`MINIDUMP_TYPE` 枚举值的按位组合） | `DumpType` 非 0 时此值被忽略 |

注意 WER LocalDumps 的 `DumpType` 只有 `Mini`/`Full` 两档（外加 `Custom`），**没有** `Heap`/`Triage` 选项——这与 `DOTNET_DbgMiniDumpType` 的四档枚举（`§ 5. DOTNET_DbgEnableMiniDump（.NET Core 3.0+，崩溃自动抓取）`）不是同一套取值空间，WER 场景下想要接近 `Heap` 的效果只能选 `2`（Full）。

### 输出与产物位置
落在 `DumpFolder` 指定目录（默认 `%LOCALAPPDATA%\CrashDumps`），文件名由系统自动生成，包含进程名与时间戳。`DumpCount` 超限后自动轮转，最旧文件被静默删除——需要长期保留的 dump 应在轮转前转移出该目录。

### 判据
WER 是系统级机制，对所有进程无差别生效，无法像 `DOTNET_DbgEnableMiniDump` 那样按单个 .NET 进程精细配置类型；且它依赖注册表全局状态，在容器场景中因容器通常是无状态且短生命周期的，注册表配置很难持久化到每次容器启动前——这正是 `§ 5. DOTNET_DbgEnableMiniDump（.NET Core 3.0+，崩溃自动抓取）` 在容器场景中被优先选用的原因（详见该节判据）。WER 的价值在于它是 Windows 桌面/服务器长期运行进程（非容器）崩溃场景下，**无需预先知道会崩溃、也无需针对该进程做任何提前配置**（只需全局启用一次）即可捕获的兜底手段。

## 5. DOTNET_DbgEnableMiniDump（.NET Core 3.0+，崩溃自动抓取）

### 用途与前置条件
运行时级的崩溃自动抓取机制，仅覆盖 .NET Core 3.0+（不含 .NET Framework），通过环境变量配置，对单个进程按需启用——只需在该进程的环境中设置变量即可，无需系统级注册表改动。崩溃发生时运行时内部调用 `createdump`（见 `§ 3. createdump（.NET Core 3.0+，Linux 优先）`）完成实际抓取。

### 语法与关键开关

Linux 下启用（对该进程生效，Heap 类型，写入指定目录）：
```bash
export DOTNET_DbgEnableMiniDump=1
export DOTNET_DbgMiniDumpType=2
export DOTNET_DbgMiniDumpName=/dumps/coredump.%p
dotnet MyApp.dll
```

Windows 下启用（PowerShell，Full 类型）：
```powershell
$env:DOTNET_DbgEnableMiniDump = "1"
$env:DOTNET_DbgMiniDumpType = "4"
$env:DOTNET_DbgMiniDumpName = "C:\dumps\dump.%p.dmp"
dotnet MyApp.dll
```

容器场景（Dockerfile 中固化，随镜像启动即生效）：
```dockerfile
ENV DOTNET_DbgEnableMiniDump=1
ENV DOTNET_DbgMiniDumpType=2
ENV DOTNET_DbgMiniDumpName=/dumps/coredump.%p
```

| 变量 | 含义 | 取值 | 不设的后果 |
|---|---|---|---|
| `DOTNET_DbgEnableMiniDump` | 总开关，是否在崩溃时生成 dump | `1` 启用 | 默认 `0`，崩溃不产出任何 dump |
| `DOTNET_DbgMiniDumpType` | dump 类型 | `1`=Mini，`2`=Heap（默认），`3`=Triage，`4`=Full | 未设置时按默认值 `2`（Heap）生成 |
| `DOTNET_DbgMiniDumpName` | 输出路径模板，支持 `%p`（PID）、`%e`（可执行文件名）、`%h`（主机名）、`%t`（Epoch 秒数） | 路径字符串 | 默认 `/tmp/coredump.<pid>`（Linux；Windows 侧默认路径需显式设置，不设置时依赖运行时内部默认行为） |
| `DOTNET_CreateDumpDiagnostics` | 开启抓取过程诊断日志 | `1` 启用 | 默认 `0`，抓取失败时缺少诊断输出 |

单文件发布与 Native AOT 应用模型下，**仅支持 Full 类型**——设置其他 `DOTNET_DbgMiniDumpType` 值在这两种模型下不生效。

### 输出与产物位置
按 `DOTNET_DbgMiniDumpName` 模板生成，未设置时 Linux 默认 `/tmp/coredump.<pid>`。容器内需将该路径挂载到共享卷才能在容器生命周期结束（崩溃通常导致容器退出）后仍能取到文件。

### 判据
`DOTNET_DbgEnableMiniDump` 与 WER LocalDumps（`§ 4. WER LocalDumps（Windows，崩溃自动抓取）`）的选择依据：WER 是 Windows 系统级机制、依赖注册表全局状态、对所有进程无差别生效；`DOTNET_DbgEnableMiniDump` 是 .NET 运行时级机制、通过环境变量配置、可按进程精细控制类型与输出路径，且跨 Windows/Linux 均可用。容器场景中镜像通常是无状态、一次性启动的，无法依赖预先手工配置的系统注册表状态（WER 的注册表配置不会随容器镜像分发），因此容器内崩溃取证**首选** `DOTNET_DbgEnableMiniDump`——把配置固化进 Dockerfile 或编排清单的环境变量声明中，随容器每次启动自动生效，不依赖宿主机状态。
