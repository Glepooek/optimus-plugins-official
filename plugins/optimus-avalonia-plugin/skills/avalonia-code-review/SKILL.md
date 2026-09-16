---
name: avalonia-code-review
description: Use when reviewing Avalonia AXAML or C# UI code for framework correctness, binding and styling defects, cross-platform risks, accessibility, performance concerns, or before merging an Avalonia UI change. 触发词："审查 Avalonia 代码"、"Avalonia review"、"AXAML 检查"、"Avalonia PR 审查"。
license: MIT
compatibility: 需要安装 optimus-mcp-servers 中无需认证的 Avalonia Docs MCP；支持审查用户粘贴的代码或本地 Avalonia 项目中的已限定文件范围。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: quality
allowed-tools: Read Glob Grep avalonia-docs
---

# Avalonia 代码审查

以 Avalonia Docs MCP 的当前官方文档和 API 为唯一框架判据，审查用户指定范围内的 AXAML、C# UI 代码和项目配置。此 skill 不复制静态框架规则，也不把 WPF/UWP/WinUI 的习惯当作 Avalonia 结论。

## 需求预告

先对照用户已提供的信息，一次性列出缺失项：审查范围（文件、目录、代码片段或本次改动）、审查深度（快速或完整）、目标 Avalonia/.NET 版本、以及可用的构建或错误输出。用户只给出代码片段时，按可见代码审查并注明上下文限制；信息齐全时直接开始。

## Step 1：锁定范围与审查深度

按以下优先级收敛，除非用户明确要求，不得扩大范围：指定文件/片段 → 指定功能模块 → 本次 `git diff` 涉及的 Avalonia 文件 → 单一最相关文件。扫描前先确定目录边界；约 20 个以上相关文件时请求用户缩小范围。

### 🔴 CHECKPOINT：全项目审查

只有用户明确同意后，才能扫描整个项目或执行无边界的 `**/*.axaml`、`**/*.cs` 搜索。默认不越过已确认范围。

- **快速初审**：AXAML 命名空间与资源、样式/主题、绑定与数据模板、UI 线程、明显跨平台或可访问性问题。
- **完整审查**：在快速初审基础上，逐项覆盖属性系统与自定义控件、MVVM、事件/输入、布局与性能、资源/资产、AOT/裁剪与部署风险。

## Step 2：用官方 MCP 核验判据

1. 对每次 Avalonia 审查会话调用 `get_avalonia_expert_rules`。
2. 读取范围内的 `.axaml`、相关 C#、`.csproj` 和用户提供的错误输出；不要检查范围外文件来补猜上下文。
3. 对每个疑点按需调用官方资料：确切类型/成员用 `lookup_avalonia_api`；概念和示例用 `search_avalonia_docs`。仅当审查 WPF 遗留代码时，调用 `lookup_wpf_to_avalonia_mapping` 的单个主题。
4. 在完整审查中，按当前范围核对以下主题：

| 主题 | 核验重点 |
|---|---|
| AXAML、资源与资产 | `.axaml`、Avalonia 命名空间、`using:`、`avares://`、资源生成方式 |
| 样式、主题与模板 | selector、style class、pseudo-class、`ControlTheme`、模板绑定方向 |
| 绑定与模板 | `x:DataType`、编译绑定、DataTemplate、null/fallback、绑定模式 |
| 属性、控件与 MVVM | `StyledProperty`/`DirectProperty`、控件基类、命令、ViewModel 边界 |
| 线程、事件与输入 | `Dispatcher.UIThread`、指针/键盘路由事件、异步 UI 更新 |
| 布局、性能与跨平台 | 响应式布局、虚拟化、平台 API 隔离、AOT/裁剪风险 |
| 可访问性 | 键盘可达性、语义/自动化信息、缩放与主题可读性 |

## Step 3：判定、修复与严重度

每个问题必须同时包含：位置、可观察风险、已查询的官方依据、严重度、最小修正和验证状态。

- **🔴 严重**：已确认会导致构建失败、运行时异常、数据/交互故障、跨平台崩溃或阻断可访问性的缺陷。
- **🟡 重要**：已确认违反 Avalonia 模型，或存在明确的性能、可维护性、跨平台或可访问性风险，但需要特定输入/配置才会失效。
- **🟢 建议**：不改变正确性、仅提升可读性、一致性或未来维护性的优化。
- 无法从可见代码和 MCP 资料确认的事项，列入“待确认项”，不得作为缺陷计数。

只在代码片段和版本信息足够时提供最小修正片段；没有完整上下文时不生成声称可直接替换整个文件的代码。审查默认只读；用户明确要求修复时，先确认拟修改的文件和范围，并在修改后重新审查该范围。

## 报告格式

```markdown
# Avalonia 代码审查报告

## 审查摘要
- 审查范围：[文件 / 代码片段 / diff]
- 审查深度：[快速初审 / 完整审查]
- 已核验的官方依据：[MCP 查询主题或 API]
- 未验证项：[构建、平台、配置或缺失上下文]
- 发现问题：[总数] 个；🔴 [X] / 🟡 [Y] / 🟢 [Z]

## 问题清单
### 🔴 严重问题
- `[文件:行]` [风险]；官方依据：[资料]；修正：[最小改动]；验证：[已验证/未验证]

### 🟡 重要问题
...

### 🟢 建议
...

## 待确认项
- [依赖的项目配置、运行平台或不可见代码]

## 修正后代码
[仅提供有充分上下文的最小片段；否则说明为什么不能安全生成]
```

## 失败处理

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| Avalonia Docs MCP 不可用 | 报告 MCP 不可用并检查 `optimus-mcp-servers` 安装/配置 | 停止框架合规判定，不以记忆替代官方依据 |
| 代码不属于 Avalonia 或缺少必要上下文 | 明确说明可见范围和不适用部分 | 只给通用说明或请求最小可复现代码，不编造问题 |
| 官方资料与目标包版本不匹配 | 从 `.csproj` 确认版本并重新查询 | 标为待确认项，不给确定性修复指令 |
| 构建/多平台行为无法运行 | 审查静态代码并列出未验证项 | 不将静态审查描述为已通过构建或平台验收 |

## 不要做什么

- 不扫描范围外文件、编造问题，或为了让报告“有产出”而把正确实现标为缺陷。
- 不把 WPF `Style.Triggers`、`DependencyProperty`、`pack://`、`Visibility` 或 `Dispatcher` 语义直接套到 Avalonia。
- 不在没有 MCP 官方依据时给出确定性的 Avalonia API、版本或兼容性结论。
- 不把配置依赖的推断、未运行的构建或未测试的平台行为标记为已验证。
