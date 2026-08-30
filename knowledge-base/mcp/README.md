# MCP（Model Context Protocol）知识库

> 版本：1.0.0

> 面向**开发者使用视角**的 MCP 协议知识库。内容取自 MCP 官方文档站 [modelcontextprotocol.io](https://modelcontextprotocol.io/) 的 `2026-07-28` 版本，覆盖架构概念、server/client 开发、接入方式与授权安全，不收录协议规范的完整技术细节（Schema Reference、SEP 提案、社区治理文档等）。

本领域负责 MCP 协议本身的概念与开发实践；具体 MCP server 的接入配置（如本仓库 `optimus-mcp-servers` 插件已接入的 GitHub/MasterGo/飞书项目）不在本领域范围内，那是各插件自己的配置说明。

## 文档目的

帮助开发者理解"MCP 是什么、由哪些概念构成、如何接入现有 server、如何自建 server/client"，建立对协议的正确心智模型，避免把 MCP 想象成某个具体产品的专属能力。

## 适用范围与读者

- **适用范围**：评估是否接入某个 MCP server、自建 MCP server/client、审查 MCP 相关安全实践
- **读者**：需要理解或使用 MCP 协议的开发者；本仓库尚无固定 skill 消费者，供未来相关工作按需查阅

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义，与 `knowledge-base/csharp/README.md` 的定义一致：

| 级别 | 措辞 | 含义 |
|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 |
| **建议 MAY** | "可以"、"建议" | 可选做法，不强制 |

本领域仅 `rules/01-authorization-and-security.md` 一篇规范文件，其余为 `reference/` 描述性内容，不带规范语气。

## 阅读路径

| 场景 | 参考文档 |
|---|---|
| 第一次了解 MCP 是什么 | `reference/architecture-overview.md` |
| 开发/使用 MCP server 端能力 | `reference/server-concepts.md` |
| 开发/使用 MCP client 端能力 | `reference/client-concepts.md` |
| 接入一个已有的 MCP server | `reference/connecting-to-servers.md` |
| 从零构建一个 MCP server | `reference/building-servers.md` |
| 从零构建一个 MCP client | `reference/building-clients.md` |
| 理解协议版本与规范文档结构 | `reference/protocol-basics.md` |
| 评审授权/安全实现是否合规 | `rules/01-authorization-and-security.md` |

## 文件地图

| 文件 | 主题 |
|---|---|
| `reference/architecture-overview.md` | Host/Client/Server 三方参与者、数据层与传输层、JSON-RPC 基础、发现机制、通知机制 |
| `reference/server-concepts.md` | Tools/Resources/Prompts 三种服务器原语的用途、协议方法与控制权归属 |
| `reference/client-concepts.md` | Elicitation 机制；已废弃的 Roots/Sampling/Logging 及其替代方案 |
| `reference/connecting-to-servers.md` | 本地（stdio）与远程（Streamable HTTP）两种接入方式的配置与鉴权概览 |
| `reference/building-servers.md` | 自建 MCP server 的典型步骤、SDK 选择与常见实践 |
| `reference/building-clients.md` | 自建 MCP client 的典型步骤、SDK 选择与常见实践 |
| `reference/protocol-basics.md` | 协议版本协商、无状态设计、规范文档的分层结构 |
| `rules/01-authorization-and-security.md` | 授权与安全的强制/推荐条款（token passthrough、SSRF、状态劫持等） |

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。`reference/` 按整篇文档登记；`rules/` 按可独立判断的条款逐条登记。

## 更新与维护

- 新增/修改内容时，同一次提交里同步更新对应 `index.jsonl`
- 改动后运行 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" mcp` 做一致性自检
- 内容以 MCP 官方文档 `2026-07-28` 版本为准；官方文档改版后需要更新时，按差异增量修订，不做整站重新蒸馏
- 本领域内容取自公开文档的转写与提炼，不构成对原文的逐句翻译

## 与仓库已有资产的关系

- `plugins/optimus-mcp-servers/`：本仓库实际接入的 MCP server 配置（GitHub/MasterGo/飞书项目），其 `README.md` 是配置操作指南，与本领域的协议概念知识互补但不重复
