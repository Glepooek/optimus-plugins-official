# SOS 命令：线程与栈

> 本篇覆盖「谁在跑、卡在哪、崩在哪」三类问题的取证命令。命令在三种运行时下同名同语义，差异只在 SOS 的加载方式——见 `reference/symbols-and-tool-matching.md § 3. SOS 与运行时版本匹配`。

命令名前的 `!` 是 WinDbg 的扩展命令前缀。在 `dotnet-dump analyze` 中可省略。

## 1. !threads

### 用途与前置条件
列出全部托管线程。进程挂起、无响应、CPU 打满时的**第一条命令**——它给出线程全景，后续用 `!clrstack` 深入某条可疑线程。任何类型的 dump 都支持（Mini/Triage 亦可）。

### 语法与关键开关
```
!threads
!threads -live      # 只列活动线程，过滤已终止的
!threads -special   # 含运行时内部线程（GC、终结器、调试器）
```

`-special` 在排查终结器卡死时必用——终结器线程不在默认输出里。

### 输出逐列语义

| 列 | 含义 | 异常信号 |
|---|---|---|
| `ID` | CLR 内部线程序号 | —— |
| `OSID` | 操作系统线程 ID（十六进制） | 用于 `~~[OSID]s` 切换线程 |
| `ThreadOBJ` | Thread 对象地址 | 可用 `!dumpobj` 展开 |
| `State` | 线程状态位掩码 | —— |
| `GC Mode` | `Preemptive` / `Cooperative` | 大量 Cooperative 且 GC 进行中 = 线程在等 GC |
| `Lock Count` | 持有的锁数量 | **非零表示持锁，死锁排查的起点** |
| `APT` | COM 单元模型（STA/MTA） | WPF UI 线程应为 STA |
| `Exception` | 该线程上的待处理异常 | **非空即为崩溃第一现场候选** |

### 判据：能证实 / 排除什么
- `Lock Count` 全为 0 → **排除** Monitor 死锁，转查异步死锁，见 `reference/sos-locks-and-async.md § 2. !dumpasync`。
- 线程数远超预期（数百）且多数栈相同 → **证实**线程池饥饿，转查 `reference/sos-locks-and-async.md § 3. !threadpool`。
- `Exception` 列非空 → **证实**该线程有待处理异常，转 `§ 4. !pe` 展开

## 2. !clrstack

### 用途与前置条件
显示当前线程（或指定线程，需先 `setthread`/`~~[OSID]s` 切换）的托管调用栈。定位到可疑线程之后的**第二步**——`!threads` 给出全景，`!clrstack` 深入某条线程看它具体卡在哪个方法。任何类型的 dump 都支持。

### 语法与关键开关
```
!clrstack
!clrstack -a      # 等价于 -l 与 -p 组合：同时显示局部变量与参数
!clrstack -l      # 显示帧内局部变量（无法取到变量名，只能显示地址=值）
!clrstack -p      # 显示传入方法的参数值
!clrstack -all    # 输出全部托管线程的栈，等价于对每条线程分别执行
!clrstack -n      # 禁止查找并显示源码文件名与行号
```

`-a` 是 `-l -p` 的简写，三者叠加使用是冗余的。`-all` 在批量扫描线程池饥饿或大范围死锁时比逐条 `setthread` 效率高。

### 输出逐列语义

| 列 | 含义 | 异常信号 |
|---|---|---|
| `Child SP` | 该栈帧的栈指针地址 | 用于区分递归调用的不同层 |
| `IP` | 该帧的指令指针（返回地址） | —— |
| `Call Site` | 解析出的方法名，或特殊帧标记（如 `[GCFrame]`、`[HelperMethodFrame_1OBJ]`） | 特殊帧标记本身即信息：`[HelperMethodFrame_1OBJ] System.Threading.Monitor.Enter` 表示该线程正在等待或进入一把 Monitor 锁 |

### 判据：能证实 / 排除什么
- 大量线程的 `Call Site` 停在同一个 `System.Threading.Monitor.ReliableEnter`/`Monitor.Enter` 帧 → **证实**这些线程在等待同一把锁，转 `reference/sos-locks-and-async.md § 1. !syncblk` 找出持锁线程后对其执行 `setthread` + `!clrstack` 确认它是否也在等别的锁（循环等待即死锁）。
- 缺符号时 `Call Site` 仍能显示完整类名与方法名（原因见 `reference/symbols-and-tool-matching.md § 4. 缺符号时的降级读法`）→ 只需确认调用链经过了哪些方法时，**排除**补符号的必要性；一旦要看源码行号或非托管帧，判据不成立

## 3. !dumpstack

### 用途与前置条件
显示当前线程的原生（非托管）与托管栈交错视图。`!clrstack` 只显示托管帧，遇到 P/Invoke、COM 互操作或卡在运行时内部帮助函数时看不到非托管侧的调用链——`!dumpstack` 补这个缺口。需要非托管符号（系统 DLL 的公共符号）才能解析出函数名，否则退化为裸地址。

### 语法与关键开关
```
!dumpstack
!dumpstack -EE          # 只显示托管帧（等价于 !clrstack 的精简版）
!dumpstack -n            # 禁止显示源码文件名与行号
!dumpstack <top> <bottom>   # 限定栈帧范围（仅 x86 平台支持起止参数）
```

`-EE` 在只想快速核对托管侧、不想被大量非托管帧噪声干扰时使用。

### 输出逐列语义

`!dumpstack` 的每一帧要么是一条原生栈帧（模块名 + 函数名或裸地址），要么是一个特殊的托管/非托管转换标记：

| 标记 | 含义 | 异常信号 |
|---|---|---|
| `[InlinedCallFrame]` | P/Invoke 调用被内联进调用方，标记跳转到非托管代码的位置 | 栈卡在此处附近 → 怀疑卡在非托管侧的 P/Invoke 调用 |
| `[HelperMethodFrame]` 及其变体（如 `[HelperMethodFrame_1OBJ]`） | 运行时内部帮助函数/FCall 的栈标记，用于在这些函数内部仍可回溯栈 | 常见于 `Monitor.Enter`/`Monitor.ReliableEnter` 附近，是锁等待的信号 |
| `[GCFrame]` | 该帧内有对象引用需要在 GC 时被保护 | 大量出现属正常运行时行为，不单独构成异常信号 |
| 裸地址 + 模块名（如 `ntdll!Unknown+0x1234`） | 无对应符号的非托管帧，无法解析出具体函数名 | 需要补齐系统符号才能继续解析，见 `reference/symbols-and-tool-matching.md § 4. 缺符号时的降级读法` |

### 判据：能证实 / 排除什么
- 托管帧下方紧跟 `[InlinedCallFrame]` 且长时间未返回 → **证实**该线程卡在某个 P/Invoke 调用的非托管侧，需要非托管符号或 Windows 事件日志进一步定位具体系统调用
- 栈顶是纯托管帧、没有转换标记 → **排除**非托管代码路径是卡顿原因，问题定位可完全依赖 `!clrstack`，无需切换到 `!dumpstack`

## 4. !pe

### 用途与前置条件
打印异常对象的字段：类型、消息、HRESULT、栈轨迹与 InnerException 链。不指定地址时默认打印当前线程上最后抛出的异常。崩溃 dump 定位第一现场的核心命令——先用 `!threads` 找到 `Exception` 列非空的线程，`setthread` 切过去后执行 `!pe`。

### 语法与关键开关
```
!pe
!pe <异常对象地址>
!pe -nested       # 展开嵌套/链式异常对象的详情
!pe -lines        # 附加源码文件名与行号（需要符号）
```

`-nested` 是遍历 InnerException 链的关键开关：不加时只显示最外层异常，`InnerException` 字段若非 `<none>` 会提示"使用 `!PrintException <地址>` 查看更多"，需要手动跟进；加 `-nested` 后一次性展开整条链，逐层显示每个异常对象的类型、消息与 HRESULT。

### 输出逐列语义

| 字段 | 含义 | 异常信号 |
|---|---|---|
| `Exception object` | 异常实例的堆地址 | 可用 `!dumpobj` 进一步展开字段 |
| `Exception type` | 异常的 .NET 类型全名 | —— |
| `Message` | 异常消息文本 | `<none>` 表示构造时未提供消息 |
| `InnerException` | 内部异常，`<none>` 或指向另一异常对象的地址 | 非 `<none>` 且未加 `-nested` 时需手动跟进 |
| `StackTrace (generated)` | 抛出时刻的托管栈（SP/IP/Function 三列） | 结合 `!clrstack` 交叉验证抛出位置 |
| `HResult` | 异常的 HRESULT 十六进制码 | 可用于区分同类型异常的不同错误原因（如 COM 互操作场景） |

### 判据：能证实 / 排除什么
- `InnerException` 非 `<none>` → **证实**存在链式异常，须加 `-nested` 完整展开才能看到根因异常，只看最外层会误判根因
- 该线程是 UI 线程（`!threads` 中 `APT` 为 STA 且为消息循环线程）且 `Exception` 列非空 → 转查 `knowledge-base/wpf/rules/12-exceptions-crash.md § 1. UI 线程异常`，核对是否违反了「`async void` 事件处理器异常必须兜底」等约束——这类违反在 dump 里的表现就是 `!pe` 能打出异常对象，但应用进程已经崩溃退出
- `Exception object` 地址与 `!threads` 的 `Exception` 列地址一致 → **证实**两条命令定位的是同一个异常，可交叉验证未看错线程

## 5. !dso

### 用途与前置条件
枚举当前线程栈上找到的所有托管对象引用（地址 + 类型名）。`!clrstack -a` 显示局部变量时只能给出"地址=值"、取不到变量名——当需要按类型反查栈上还有哪些对象时，`!dso` 是替代手段。

### 语法与关键开关
```
!dso
!dso -verify              # 额外校验每个对象非静态 CLASS 字段的合法性
!dso <top> <bottom>        # 限定栈范围
```

`-verify` 用于怀疑栈上对象已损坏（如错误的 P/Invoke 调用破坏了栈）时的完整性检查。

### 输出逐列语义

| 列 | 含义 | 异常信号 |
|---|---|---|
| `ESP/REG` | 栈上持有该引用的地址（或寄存器） | —— |
| `Object` | 引用指向的堆对象地址 | 可用 `!dumpobj` 展开该对象的字段 |
| `Name` | 对象的 .NET 类型全名（`System.String` 会附带字符串内容） | —— |

### 判据：能证实 / 排除什么
- 目标类型在 `!dso` 输出中出现 → **证实**该类型的实例当前被栈上某个引用持有，可取 `Object` 地址喂给 `!dumpheap -mt <该类型的 MT 地址>` 或 `!dumpobj` 继续深入
- `!clrstack -a` 无法解析出某个局部变量的类型名（只显示地址=值）而怀疑其类型 → 转 `!dso` 按类型名反查，**排除**"必须补符号才能确认局部变量类型"这一假设——`!dso` 不依赖 PDB，只依赖托管堆元数据

