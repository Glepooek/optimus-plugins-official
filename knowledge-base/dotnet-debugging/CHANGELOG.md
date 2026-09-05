# Changelog — .NET 高级调试

## [1.0.1] - 2026-09-05

### Fixed
- `dump-capture.md § 1. procdump`：CPU 触发示例补 `-u` 开关。`-c` 的阈值默认按全核总量计算，单线程满载在 8 核机上仅占 12.5%，原示例 `-c 80` 在多核机上抓单线程死循环永不触发且无任何报错提示
- `dump-types-and-capability.md § 1`：补 `MiniPlus`（`procdump -mp`）对 CLR 进程无效的限制——官方明确 CLR 进程因调试限制一律按 `-ma` 转储，选 `-mp` 不会带来体积收益

### Added
- `dump-capture.md § 1. procdump`：新增 `-p`（性能计数器阈值触发）与 `-m`（提交内存阈值触发）两个开关及示例，分别对接「句柄耗尽」与「内存持续增长」两条征象路径；判据段补充阈值触发对「抓取时刻与问题窗口不重合」这一困难的作用

## [1.0.0] - 2026-09-05

### Added
- 新建 `dotnet-debugging` 领域：8 篇 reference（调试决策树、CLR 运行时结构、dump 类型与能力、dump 抓取、符号与工具匹配、SOS 线程与栈、SOS 堆与对象、SOS 锁与异步）+ 1 篇规范文件（dump 处置）
- 覆盖 .NET Framework 4.x、.NET 6/8+、Linux 容器三种运行时的共性层
- 索引按命令/征象分片登记，支撑 skill 精确检索

已知未覆盖：`AssemblyLoadContext` 与可收集程序集卸载（原规约 `clr-runtime-anatomy.md` 设计范围内），一期未交付，留待后续期次。
