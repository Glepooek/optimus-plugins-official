---
name: avalonia-wpf-migration
description: Use when migrating a WPF application to Avalonia, selecting Avalonia XPF versus native Avalonia, or producing a staged, validated migration plan. 触发词："WPF 迁移 Avalonia"、"WPF 跨平台"、"XPF 还是 Avalonia"、"评估 WPF 改造"。
license: MIT
compatibility: 需要安装 optimus-mcp-servers 中无需认证的 Avalonia Docs MCP；迁移目标项目须可由本地文件工具读取，实际构建与测试仍依赖目标项目所需的 .NET SDK。
metadata:
  version: "1.2.1"
  author: desktop client team
  category: workflow
allowed-tools: Read Glob Grep Write avalonia-docs
---

# WPF → Avalonia 企业迁移编排

本 skill 不维护静态 API 对照表。以 Avalonia Docs MCP 的官方迁移分析、映射和实现指南为准，将其组织成可审查、可分阶段验证的企业迁移交付；不在未分析项目的情况下猜测迁移路径或批量改写代码。

## 需求预告

开始前一次性确认以下用户可提供的信息：WPF 项目根目录、目标平台、是否要求短期保留现有 WPF 控件/商业控件，以及本次范围是评估、单个垂直切片还是全量迁移。缺少时统一询问；齐全时直接执行前置检查。

## Step 1：项目分析与路径建议

1. 调用 `analyze_wpf_project`，让 MCP 盘点目标框架、WPF 引用、第三方控件、MVVM 框架与 P/Invoke。
2. 输出事实清单：跨平台目标、阻塞项、风险最高的 UI/控件、可先迁移的垂直切片。
3. MCP 会给出 XPF 或原生 Avalonia 的建议；将建议、成本、许可证/第三方控件风险和未验证假设写成结论。

### 🔴 CHECKPOINT：确认迁移路线

展示 XPF 与原生 Avalonia 的选择及其影响后，等待用户明确确认。未确认前不得创建新项目、修改项目文件、批量改写 `.xaml`/`.axaml` 或安装包。

## Step 2：按确认路线加载官方流程

- **XPF 路线**：调用 `migrate_to_xpf`，按其 NuGet 源、SDK 切换、许可证、版本冲突和排障流程执行。
- **原生 Avalonia 路线**：调用 `migrate_to_avalonia`，从可运行基线和一个垂直切片开始；不得把迁移与架构重构混在同一批改动中。

对于原生迁移，仅在当前切片需要时调用 `lookup_wpf_to_avalonia_mapping`：`namespaces`、`controls`、`properties`、`styling`、`bindings`、`templates`、`events`、`resources`、`layout`、`threading`、`windows`、`animations`、`custom-controls`、`mvvm` 或 `gotchas`。不要把整套映射复制进项目文档。

## Step 3：迁移一个可验证垂直切片

1. 先建立可构建的目标工程和最小启动路径，再迁移一个 View、其 ViewModel、资源和必要服务。
2. 用映射工具核对高风险差异：样式/伪类、属性系统、绑定、模板、输入事件、资源 URI、线程与窗口行为。
3. 若目标已是 Avalonia 项目，调用 `migrate_diagnostics` 配置受支持的 Developer Tools；不得引入已弃用的 `Avalonia.Diagnostics`。
4. 每完成一个切片就构建、运行并记录平台差异；只在该切片通过后再扩大范围。

## Step 4：交付迁移决策与验证记录

交付内容必须区分已验证事实与待验证风险：

- 已确认的路线、目标平台和依赖；
- 按切片排列的迁移清单、阻塞项与回退方案；
- 每项使用的官方映射主题及需要人工验收的视觉/交互差异；
- 已运行的构建、单元测试、UI/手工验收及其结果。

## 失败处理

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| MCP 无法分析项目或缺少项目根目录 | 说明缺失项，停止在分析阶段 | 要求提供最小可读取项目副本或关键 `.csproj` / XAML 文件，不猜测引用关系 |
| XPF 路线因许可证、NuGet 源或版本冲突受阻 | 依 `migrate_to_xpf` 的排障步骤定位 | 回到 🔴 CHECKPOINT，重新评估原生路线；未经确认不切换 |
| 原生迁移遇到不确定 API/控件映射 | 调用对应主题的 `lookup_wpf_to_avalonia_mapping` 或 `lookup_avalonia_api` | 标为阻塞项，保留原实现或隔离适配层，禁止虚构等价 API |
| 构建成功但视觉/交互不一致 | 用最小复现与目标平台截图定位 | 将差异列为人工验收项，不宣称迁移完成 |

## 不要做什么

- 不把 WPF `DependencyProperty`、`Style.Triggers`、`pack://`、`Visibility` 或 `Dispatcher` 语义当作 Avalonia 的直接等价物。
- 不在未完成 `analyze_wpf_project` 和路线确认前批量修改用户项目。
- 不将“能编译”描述为跨平台迁移验收通过；必须记录实际平台验证范围。
- 不复制或维护容易过期的官方 API 映射，遇到具体问题必须查询 Avalonia Docs MCP。
