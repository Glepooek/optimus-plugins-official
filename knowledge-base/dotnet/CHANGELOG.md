# Changelog — .NET 平台与运行时

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [7.3.0] - 2026-09-03

### Added
- 新增 `dotnet/reference/wpf-cpu-architecture-support.md`：WPF 与 .NET 的 CPU 架构（x86/x64/ARM32/ARM64）支持矩阵整理稿，覆盖 .NET Framework 4.8.1 与 .NET 5.0.8 两个 ARM64 支持起点、ARM32 从未支持的事实、ARM64 上 x86/x64 模拟运行的适用条件
- 索引新增条目 `dotnet.ref.wpf-cpu-architecture-support`

### Changed
- `reference/windows-dotnet-support-matrix.md` 头部补充与新 reference 的交叉引用，说明两份矩阵分别为 Windows 版本轴与 CPU 架构轴，维度互补
- 领域 `README.md` 阅读路径表新增「判断 WPF 能否在 ARM64 / x86 / x64 上原生运行」一行

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 1.11.0 - 2026-08-27

- 新增 `dotnet` 领域：收纳 .NET Framework、现代 .NET、Windows 兼容性与生命周期的描述性知识
- 新增 `dotnet/reference/windows-dotnet-support-matrix.md`：Windows 与 .NET Framework / .NET 5+ 支持矩阵整理稿
- 根知识库领域说明补充 `dotnet`、`csharp`、`wpf` 三者的职责边界
