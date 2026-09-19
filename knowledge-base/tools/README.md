# 工具与资源目录

> 版本：1.0.0

> 记录团队已调研或已使用的外部工具/资源（CLI、MCP server、Skill、Agent、Plugin 等）——是什么、能做什么、怎么安装/更新/移除，以及与本仓库现有资产的关系与取舍理由。**纯描述性领域，不定义 MUST/SHOULD/MAY 规范条款**。

本领域负责记录"调研过、评估过、或正在用的具体产品"，与 `knowledge-base/mcp/` 不同——`mcp` 讲 MCP 协议本身的架构与机制，本领域记录某个具体 MCP server/CLI 产品的能力、安装方式与取舍结论。

## 文档目的

避免同一个工具被反复调研：新增依赖、接入新 MCP server、引入新 CLI 或评估新工具前，先查本领域有没有现成记录；也沉淀"为什么选 A 不选 B"的取舍理由（如 GitHub CLI 替代 GitHub MCP Server 的理由），供后续同类决策参考。

## 适用范围与读者

- **适用范围**：CLI、MCP server、Skill、Agent、Plugin 等外部工具/资源的调研记录
- **读者**：需要引入新工具或评估技术选型的开发者与 agent

## 规范级别

本领域**暂无规范条款**，不定义 MUST/SHOULD/MAY 级别体系。`reference/` 下的文档全部为描述性知识——某工具的能力、安装方式、与本仓库现有资产的关系，不表达"必须怎样做"的判定。是否引入某个工具仍由使用者判断，本领域只提供决策依据。

## 阅读路径

| 场景 | 参考文档 |
|---|---|
| 评估 GitHub 相关自动化方案 | `reference/github-cli.md`、`reference/github-mcp-server.md`（两者取舍见后者备注） |
| 评估浏览器自动化方案 | `reference/playwright-cli.md`、`reference/playwright-mcp.md`（两者互补关系见后者备注） |
| 评估 WPF→Avalonia 迁移辅助工具 | `reference/build-mcp.md` |
| 评估 API 测试/管理工具 | `reference/apifox-cli.md` |
| 评估飞书/Lark 自动化工具 | `reference/lark-cli.md` |
| 评估文件转 Markdown 工具 | `reference/markitdown.md` |

## 文件地图

| 文件 | 工具 | 分类标签 |
|---|---|---|
| `reference/github-mcp-server.md` | GitHub MCP Server（本仓已移除） | mcp, github |
| `reference/playwright-mcp.md` | Playwright MCP | mcp, playwright |
| `reference/build-mcp.md` | Build MCP（Avalonia） | mcp, avalonia |
| `reference/github-cli.md` | GitHub CLI (gh) | cli, github |
| `reference/apifox-cli.md` | Apifox CLI | cli, api-testing |
| `reference/playwright-cli.md` | Playwright CLI | cli, playwright |
| `reference/lark-cli.md` | lark-cli (Lark/Feishu) | cli, feishu |
| `reference/markitdown.md` | MarkItDown | cli, markdown-conversion |

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。每个工具一条独立 `reference` 条目，`anchor` 留空整篇登记；`tags` 承载分类信息（如 `mcp`/`cli`/`skill`/`agent`/`plugin` 及技术栈标签），不要求互斥，一个工具可同时打多个标签。新增/修改内容需同步 `index.jsonl`，建议通过 `/knowledge-base-maintain` skill 完成。

## 与仓库已有资产的关系

- `.claude/skills/record-tools`：本领域内容的唯一写入方，负责抓取、去重、归档新工具条目
- `AGENTS.md`：新增依赖/MCP/CLI 前先查本领域、MCP 与 CLI 同时存在优先选 CLI 的仓库级约定见该文件"重要约束"一节
- `knowledge-base/mcp/`：讲 MCP 协议本身的架构与机制，本领域记录具体 MCP server 产品的评估结论，两者不重叠
