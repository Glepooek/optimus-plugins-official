# Changelog — .NET 高级调试

## [1.0.0] - 2026-09-05

### Added
- 新建 `dotnet-debugging` 领域：8 篇 reference（调试决策树、CLR 运行时结构、dump 类型与能力、dump 抓取、符号与工具匹配、SOS 线程与栈、SOS 堆与对象、SOS 锁与异步）+ 1 篇规范文件（dump 处置）
- 覆盖 .NET Framework 4.x、.NET 6/8+、Linux 容器三种运行时的共性层
- 索引按命令/征象分片登记，支撑 skill 精确检索

已知未覆盖：`AssemblyLoadContext` 与可收集程序集卸载（原规约 `clr-runtime-anatomy.md` 设计范围内），一期未交付，留待后续期次。
