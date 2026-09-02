# Sysinternals 工具集实战参考

面向已熟悉 Windows 系统机制的开发与运维工程师。本目录按工具拆分，每篇给出精确参数、排查配方与官方文档中缺失或易误读的部分。

## 事实基准与时效性

所有事实以 `learn.microsoft.com/sysinternals` 官方页面为准，**采集时间 2026-09-02**。凡官方页面未记载而由二进制内嵌帮助或第三方来源补充的内容，正文均显式标注来源，不与官方事实混排。

各工具官方页面标注的版本与发布日期（来自官方索引页 `learn.microsoft.com/en-us/sysinternals/`，`ms.date` 2026-08-12 / `updated_at` 2026-08-19）：

| 工具 | 版本 | 发布日期 | 维护状态 |
|---|---|---|---|
| Process Monitor | v4.1 | 2026-08-19 | 活跃 |
| Process Explorer | v17.13 | 2026-08-12 | 活跃 |
| Autoruns | v14.3 | 2026-06-17 | 活跃 |
| Sysmon | v15.21 | 2026-06-17 | 活跃 |
| ProcDump | v12.01 | 2026-07-09 | 活跃 |
| RAMMap | v1.63 | 2026-03-26 | 活跃 |
| Sigcheck | v2.91 | 2026-02-04 | 活跃 |
| VMMap | v3.4 | 2023-10-18 | 停滞 |
| TCPView | v4.19 | 2023-04-11 | 停滞 |
| PsExec | v2.43 | 2023-04-11 | 停滞 |
| Handle | v5.0 | 2022-10-26 | 停滞 |
| Strings | v2.54 | 2021-06-22 | 停滞 |

**维护状态的实际含义：** 官方索引页的 What's New 时间线（2026-03 至 2026-08）中，Process Explorer、TCPView、Handle、PsExec、RAMMap、VMMap、Strings、Sigcheck 均无更新条目。对标注「停滞」的工具，遇到缺陷不要指望修复——本目录在对应篇章直接给替代路径。

## 按症状选工具

工具名不是入口，症状才是。下表给出首选工具与判据。

| 症状 | 首选 | 判据 / 次选 |
|---|---|---|
| 文件删不掉、目录改不了名 | [Process Explorer](process-explorer-gui.md) 的 Find Handle | 需脚本化或批量则用 [Handle](handle.md)；Handle 已停滞 4 年 |
| 程序报「找不到文件/配置」但路径看着没错 | [Procmon GUI](procmon-gui.md) | 过滤 `Result is NAME NOT FOUND`，但先读该篇「Result 值的误诊陷阱」 |
| 程序报权限错误 | [Procmon GUI](procmon-gui.md) | 过滤 `Result is ACCESS DENIED`，配合 Detail 列看请求的访问掩码 |
| DLL 加载了错误版本 / 加载失败 | [Process Explorer](process-explorer-gui.md) DLL 模式 | 需捕获加载过程时序则用 [Procmon](procmon-gui.md) 的 `Process and Thread` + `Image/DLL` 事件 |
| CPU 占用高但任务管理器看不出归属 | [Process Explorer](process-explorer-gui.md) | 任务管理器把 Interrupts 计入 Idle，Process Explorer 单列显示——驱动吃 CPU 只能这样定位 |
| CPU 峰值瞬时出现、抓不到现场 | [ProcDump](procdump.md) | `-c` 阈值触发 + `-s` 持续秒数，无人值守抓 dump |
| 进程内存持续增长 | [VMMap GUI](vmmap-gui.md) | 按提交类型分解 + 快照对比；定时采样用 [vmmap-cli](vmmap-cli.md) |
| 系统整体内存吃紧、缓存异常 | [RAMMap GUI](rammap-gui.md) | 物理内存视角，7 个固定选项卡；基准测试前清缓存见 [rammap-cli](rammap-cli.md) |
| 句柄数持续增长 | [Handle](handle.md) `-s` | 按对象类型计数，CSV 导出做时序对比 |
| 不明网络连接、端口被占 | [TCPView GUI](tcpview-gui.md) | 脚本化用同包的 [Tcpvcon](tcpvcon-cli.md) |
| 开机自启动了不该启动的东西 | [Autoruns GUI](autoruns-gui.md) | 批量/离线扫描用 [autorunsc](autorunsc-cli.md) |
| 需要长期留存审计日志（事后追溯） | [Sysmon](sysmon.md) | Procmon 是交互式短时采样，Sysmon 才是常驻记录 |
| 开机早期、登录前的行为 | [Procmon](procmon-cli.md) Boot logging | 抓取与分析不在同一会话，见该篇 |
| 可疑二进制来源核查 | [Sigcheck](strings-sigcheck.md) | `-u -e` 列未签名文件；VirusTotal 集成注意上传语义 |
| 二进制里有什么字符串/硬编码 | [Strings](strings-sigcheck.md) | 全文件扫描，不解析 PE 结构 |
| 远程机器上执行命令 | [PsExec](psexec.md) | 企业环境极可能触发 EDR 告警，见该篇安全影响一节 |

## 篇章

**同时提供 GUI 与 CLI 的工具拆成两篇**，两篇顶部各有一张双向对照表，逐节交叉链接。CLI 篇按**程序名**命名（`autorunsc-cli.md` / `tcpvcon-cli.md`），因为 Autoruns 与 TCPView 的命令行版本是**独立可执行文件**，不是同一程序的开关。

| 文件 | 内容 |
|---|---|
| [00-suite-setup.md](00-suite-setup.md) | 分发渠道对比（ZIP / Store / winget / Sysinternals Live）、架构后缀差异、`-accepteula` 与 `-vt` 语义、[`_NT_SYMBOL_PATH` 配置](00-suite-setup.md#符号配置)、EULA 合规边界 |

### Process Monitor

| 文件 | 内容 |
|---|---|
| [procmon-gui.md](procmon-gui.md) | 主窗口与菜单 ASCII 布局、过滤器四元组、Result 值误诊陷阱、堆栈跟踪与符号、保存 PML、11 步排查流程 |
| [procmon-cli.md](procmon-cli.md) | 25 个开关完整表（官方页面零记载）、Ring buffer 飞行记录、无人值守配方、Boot logging、日志体积控制 |

### Process Explorer

| 文件 | 内容 |
|---|---|
| [process-explorer-gui.md](process-explorer-gui.md) | 主窗口（含 Interrupts 行）、下窗格三模式（DLL/句柄/线程）、Find Handle、VirusTotal 隐私边界、替换任务管理器 |
| [process-explorer-cli.md](process-explorer-cli.md) | 仅 4 个开关，`/t /e` 顺序敏感；绝大多数功能无 CLI 对等物 |

### Autoruns

| 文件 | 内容 |
|---|---|
| [autoruns-gui.md](autoruns-gui.md) | 可疑条目三信号判据、禁用（可逆）vs 删除（不可逆）、三个 Hide 选项与微软签名宿主劫持、基线对比 |
| [autorunsc-cli.md](autorunsc-cli.md) | `-a` 类别字母表、`-vt` ≠ `-accepteula` 陷阱、多机基线 diff 配方 |

### TCPView

| 文件 | 内容 |
|---|---|
| [tcpview-gui.md](tcpview-gui.md) | 颜色语义（绿新增/黄变更/红删除）、连接状态筛选与 TIME_WAIT vs CLOSE_WAIT 判读、端口占用定位 |
| [tcpvcon-cli.md](tcpvcon-cli.md) | 默认不显示 LISTENING 的陷阱、与 netstat / `Get-NetTCPConnection` 取舍 |

### VMMap / RAMMap

| 文件 | 内容 |
|---|---|
| [vmmap-gui.md](vmmap-gui.md) | 内存类型定义、泄漏类型→观察方向映射、instrumented 启动模式（GUI 独有）、快照对比、碎片视图 |
| [vmmap-cli.md](vmmap-cli.md) | 官方页面否认存在的 CLI；按扩展名决定输出格式、定时采样循环 |
| [rammap-gui.md](rammap-gui.md) | 7 个选项卡语义、Use Counts 列判读（Standby 大 ≠ 内存不足；Nonpaged Pool 增长 = 驱动泄漏） |
| [rammap-cli.md](rammap-cli.md) | 两套语法与 `-E[wsmt0]` 五个清空操作；唯一正当用途是基准测试前重置冷缓存 |

### 纯 CLI 工具

| 文件 | 内容 |
|---|---|
| [handle.md](handle.md) | 默认只列文件句柄需 `-a`、路径子串匹配语义、强制关闭句柄的风险、句柄泄漏时序对比 |
| [psexec.md](psexec.md) | 参数表、模拟与双跳限制、ADMIN$ 依赖与临时服务、ATT&CK S0029 归类、`\\*` 全域执行警告 |
| [procdump.md](procdump.md) | 七种转储类型、触发条件（`-s` 默认 10 秒 / `-u` 单核语义）、克隆抓取避免服务超时、AeDebug 注册 |
| [sysmon.md](sysmon.md) | 与 Procmon 的时间尺度分工、5 个核心开关、默认关闭的高价值事件（3/7/10/23）、配置 XML 规则语义 |
| [strings-sigcheck.md](strings-sigcheck.md) | Strings 全文件扫描与降噪；Sigcheck 四套语法、VT 三开关隐私边界、离线两阶段取证 |

## 通用注意事项

以下三条对多数工具生效，各篇不重复展开：

1. **管理员权限。** Handle 官方明确要求管理员权限。Process Explorer 完整功能需加载内核驱动，首次需提权。Procmon 需加载过滤驱动。非提权运行时症状通常是「看不到别的用户的进程」或「句柄列为空」，而非明确报错。
2. **敏感信息。** 官方 EULA 页面（`ms.date` 2023-05-24）明确警示：工具保存的文件可能包含用户名、密码、被访问的文件路径与注册表路径，外发泄露由使用者承担全部责任。PML 日志与 dump 在提交给第三方前必须脱敏。
3. **无 SLA。** 软件按 as-is 授权，责任上限 5 美元直接损失。Sysmon 长期驻留、Procmon Boot logging 这类生产环境用法出问题无官方兜底。
