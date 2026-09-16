---
name: avalonia
description: Use when building, reviewing, or troubleshooting an Avalonia UI application. Routes framework questions to the official Avalonia Docs MCP and routes WPF migrations to the enterprise migration workflow. 触发词："Avalonia 开发"、"Avalonia AXAML"、"Avalonia 报错"、"Avalonia 跨平台"。
license: MIT
compatibility: 需要安装 optimus-mcp-servers 中无需认证的 Avalonia Docs MCP；实际构建、运行和发布仍依赖目标项目所需的 .NET SDK。
metadata:
  version: "2.1.0"
  author: desktop client team
  category: workflow
allowed-tools: Read Glob Grep avalonia-docs
---

# Avalonia 企业开发入口

本 skill 不复制 Avalonia 通用参考资料。所有框架 API、版本差异和实现模式以 Avalonia Docs MCP 的当前官方文档为准；本插件仅提供开发问题路由，以及可审查的 WPF 迁移编排。

## 需求预告

开始前一次性确认用户已提供的项目路径、目标平台、任务类型（开发、审查、排错或 WPF 迁移）及错误信息/涉及文件。缺少时统一询问；仅咨询官方 API 时可直接查询，不要求项目路径。

## Step 1：选择执行路径

| 用户任务 | 执行方式 |
|---|---|
| WPF 项目迁移、XPF/原生 Avalonia 选型 | 交由 `avalonia-wpf-migration`；先分析项目再决定路线 |
| 指定范围的 Avalonia 代码或 PR 审查 | 交由 `avalonia-code-review`；不扩大用户确认的范围 |
| 当前 Avalonia 项目开发、排错 | 调用 `get_avalonia_expert_rules`，再按问题查询官方 MCP |
| 确切类型、属性、方法或事件 | 调用 `lookup_avalonia_api` |
| 概念、示例、版本差异、构建/部署问题 | 调用 `search_avalonia_docs` |
| 已明确的 WPF 概念映射 | 调用 `lookup_wpf_to_avalonia_mapping` 的单个主题 |

## Step 2：基于官方资料实施

1. 先从目标项目读取相关 `.axaml`、`.csproj`、C# 和错误输出；范围由用户指定或收敛到单一功能。
2. 为每个框架事实查询对应 MCP 文档或 API，避免依赖静态记忆。
3. 将官方结论应用到最小必要改动。

### 🔴 CHECKPOINT：确认高影响改动

涉及包、目标框架、平台特性或项目结构变更时，先说明影响并等待用户确认；确认前不得修改这些项目配置。

4. 对现有 Avalonia 项目，调用 `migrate_diagnostics` 配置受支持的 Developer Tools；不得使用已弃用的 `Avalonia.Diagnostics`。

## Step 3：验证与交付

交付时说明实际检查的文件、查询的官方资料、改动内容和已运行的构建/测试。若无法在本地运行，明确未验证的原因及用户可执行的最小验证命令。

## 失败处理

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| Avalonia Docs MCP 不可用 | 报告 MCP 不可用，检查 `optimus-mcp-servers` 是否已安装和配置 | 停止在框架事实确认阶段，不以记忆替代官方 API 结论 |
| API 查询没有匹配项或版本不明确 | 查询目标项目的 Avalonia 包版本并缩小检索词 | 标记为待确认，不生成或声称兼容的代码 |
| 本地构建/运行失败 | 收集最小错误输出并按涉及 API 继续查询 | 仅给出已证实的隔离修复，不扩大到无关文件 |

## 不要做什么

- 不把 WPF/UWP/WinUI 的 API、属性系统、样式触发器或资源 URI 当作 Avalonia 的直接等价物。
- 不维护或复制易过期的通用 API 对照表；必须通过 Avalonia Docs MCP 查询具体框架事实。
- 不在没有项目范围或用户确认的情况下全仓扫描、批量格式化或引入第三方包。
- 不把未运行的构建、测试或多平台验证描述为通过。
