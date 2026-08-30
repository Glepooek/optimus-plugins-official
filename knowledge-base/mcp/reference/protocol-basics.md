# 协议基础：版本、无状态设计与规范文档结构

## 1. 协议版本

MCP 协议按日期命名版本号（如 `2026-07-28`、`2025-11-25`），每个版本对应一套完整的文档站点与规范文档。协议持续演进，新版本可能废弃旧原语（如 `2026-07-28` 废弃了 Roots、Sampling、Logging 客户端原语）、新增原语（如 Discovery、Tasks 扩展），或调整既有机制的细节。

版本协商发生在每次请求的 `_meta` 字段中：

- Client 在 `io.modelcontextprotocol/protocolVersion` 字段声明自己在用的版本
- Server 若不支持该版本，会以 `UnsupportedProtocolVersionError` 拒绝请求，并在错误中列出自己支持的版本列表
- Client 收到该错误后，用双方都支持的版本重试

`server/discover` 响应中的 `supportedVersions` 字段也会列出该 server 支持的全部版本，供 client 在首次连接时确认兼容性。

## 2. 无状态设计（Statelessness）

MCP 是无状态协议：每个请求都携带处理它所需的全部信息，server 不会从之前的请求中推断状态。这意味着：

- 请求的 `_meta` 字段必须携带协议版本与调用方能力，server 才能独立处理每个请求
- 需要跨请求维持的状态（如购物车 ID、工作流 ID）由 server 主动生成一个显式的"状态句柄"，作为普通的工具参数在后续请求中传回——协议本身不提供 session 机制
- 这一设计选择直接影响安全实践：既然没有协议层的 session，server 必须自己确保"谁拿到了这个句柄"不等于"这个人有权使用它"（详见 `rules/01-authorization-and-security.md` 的状态句柄劫持章节）

## 3. 规范文档的分层结构

MCP 官方站点内容分为多个大类，本领域仅取"开发文档 + Specification 概念页"两类，其余类别（供参考）：

| 分类 | 内容 | 本领域是否收录 |
|---|---|---|
| **Docs（文档）** | 入门、学习、开发教程、工具使用指南 | 部分收录（本领域其余 reference 文件即取自此类） |
| **Specification（规范）** | 协议的正式技术规范，分 Basic/Client/Server/Schema Reference 四大块 | 仅收录概念性内容，不收录完整 Schema Reference |
| **Extensions（扩展）** | MCP Apps、Tasks 等构建在核心协议之上的可选扩展 | 不收录 |
| **Registry（注册表）** | MCP Server 注册与发布相关文档 | 不收录 |
| **SEPs（规范增强提案）** | 协议演进的正式提案记录（编号 SEP-414 至 SEP-2663） | 不收录 |
| **Community（社区）** | 治理、工作组章程等社区流程文档 | 不收录 |

Specification 内部按参与方分层：

- **Basic**：架构、生命周期/版本协商、传输、鉴权等基础协议机制
- **Client**：Roots、Sampling、Elicitation 等客户端原语的完整技术规范
- **Server**：Prompts、Resources、Tools 等服务端原语的完整技术规范，以及 Discovery、Caching、Completion、Logging、Pagination 等工具能力
- **Schema Reference**：完整的协议 JSON Schema 定义

日常开发中，`learn/architecture`、`learn/server-concepts`、`learn/client-concepts` 等 Docs 页面已经覆盖了绝大多数实操所需的概念；只有在需要精确核对某个字段的协议级约束时才需要下钻到 Specification 的对应章节。

## 权威参考

- MCP 官方文档 [Architecture overview](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)
- MCP 官方文档索引 [llms.txt](https://modelcontextprotocol.io/llms.txt)
