# MCP 架构总览

MCP（Model Context Protocol）是一个开源标准，用于把 AI 应用连接到外部系统——数据源（本地文件、数据库）、工具（搜索引擎、计算器）和工作流（专用提示词模板）。可以把 MCP 类比为 AI 应用的"USB-C 接口"：像 USB-C 提供了连接电子设备的标准化方式一样，MCP 提供了连接 AI 应用与外部系统的标准化方式。

MCP 只关注"上下文交换"这一层协议本身，不规定 AI 应用如何使用 LLM 或如何管理已获取的上下文。

## 1. 参与者：Host / Client / Server

MCP 遵循客户端-服务器架构：

- **MCP Host**：协调管理一个或多个 MCP Client 的 AI 应用（如 Claude Code、Claude Desktop）
- **MCP Client**：与某个 MCP Server 维持连接、从其获取上下文供 Host 使用的组件
- **MCP Server**：向 MCP Client 提供上下文的程序

Host 为每个连接的 Server 创建一个专属的 Client 对象，每个 Client 与其对应 Server 维持独立连接。例如 VS Code（Host）连接 Sentry MCP server 时会实例化一个 Client 对象维护该连接；再连接本地文件系统 server 时会实例化另一个 Client 对象。

**Server 的运行位置与本地/远程之分**：Server 本身指"提供上下文数据的程序"，可以本地运行也可以远程运行——这与它使用的传输方式对应：

- 使用 STDIO 传输的 Server 通常在本机运行（"本地 server"），典型场景是单个 Client 独占服务
- 使用 Streamable HTTP 传输的 Server 通常部署在远端（"远程 server"），典型场景是同时服务多个 Client

## 2. 两层架构：数据层与传输层

MCP 由两层构成，数据层是内层，传输层是外层：

- **数据层（Data Layer）**：定义基于 JSON-RPC 的客户端-服务器通信协议，包括能力/版本发现，以及 tools、resources、prompts、notifications 等核心原语
- **传输层（Transport Layer）**：定义实现数据交换的通信机制和信道，包括连接建立、消息分帧和鉴权

### 传输层的两种机制

- **Stdio 传输**：使用标准输入/输出流，用于同一台机器上进程间的直接通信，无网络开销，性能最优，典型用于本地 server
- **Streamable HTTP 传输**：使用 HTTP POST 传递 client→server 消息，可选用 Server-Sent Events 做流式响应；支持远程通信，兼容标准 HTTP 鉴权方式（Bearer token、API key、自定义 header）。MCP 推荐用 OAuth 获取鉴权 token

传输层向协议层屏蔽了通信细节，使同一套 JSON-RPC 2.0 消息格式能在所有传输机制上通用。

## 3. 数据层协议：JSON-RPC 与原语

MCP 使用 [JSON-RPC 2.0](https://www.jsonrpc.org/) 作为底层 RPC 协议：client 与 server 互相发送请求并响应；不需要响应时可用通知（notification）。

### 无状态与发现（Statelessness and discovery）

MCP 是**无状态协议**：每个请求都携带处理该请求所需的全部信息（协议版本、能力），server 不依赖之前的请求做推断。请求的 `_meta` 字段携带协议版本与相关能力；client 通常也应在其中标识自身身份（除非配置为不标识）。

Server 通过强制实现的 `server/discover` 请求对外声明其支持的版本与能力，client 可以在发出其他任何请求之前先调用它。调用 `server/discover` 是可选的——因为每个请求都携带同样的 `_meta` 字段，client 完全可以直接发出业务请求，遇到版本不匹配再重试；`server/discover` 只是把身份、能力、支持版本一次性拿到手的便捷方式，其响应通常可缓存。

### 原语（Primitives）：MCP 最核心的概念

原语定义了 client 与 server 之间"能互相提供什么"。

**Server 可暴露的三种核心原语**（详见 `server-concepts.md`）：

- **Tools**：AI 应用可调用的可执行函数（执行文件操作、调用 API、查询数据库等）
- **Resources**：为 AI 应用提供上下文信息的数据源（文件内容、数据库记录、API 响应等）
- **Prompts**：帮助结构化与语言模型交互的可复用模板

每种原语类型都有对应的发现方法（`*/list`）、获取方法（`*/get`），部分还有执行方法（`tools/call`）。

**Client 可暴露的原语**（详见 `client-concepts.md`）：

- **Elicitation**：允许 server 在交互过程中向用户请求补充信息或确认操作

以下两个客户端原语已在协议版本 `2026-07-28` 中**废弃**：

- **Sampling**：曾用于让 server 通过 client 请求语言模型补全；新实现应直接对接 LLM 提供商的 API
- **Logging**：曾用于 server 向 client 发送日志消息；新实现应改为写 `stderr`（stdio 传输）或使用 OpenTelemetry

除核心原语外，协议还支持基于核心协议构建的可选**扩展（extensions）**，例如 Tasks 扩展让 server 为长时间运行的请求返回一个可持久保存的句柄，client 可据此轮询状态并稍后取回结果。

### 通知（Notifications）

协议支持实时通知，让 server 主动告知 client 状态变化（如可用工具列表变化），无需 client 轮询。通知以不期望响应的 JSON-RPC 2.0 通知消息发送。变更通知是**opt-in（按需订阅）**的：client 打开一个长连接的 `subscriptions/listen` 流，声明想接收的通知类型，server 在该流上推送匹配的通知。

## 4. 一次交互的完整示例

一次典型的数据层交互按以下顺序展开：

1. **Discovery**：client 发送 `server/discover`，获知 server 支持的协议版本、能力（如 `tools`/`resources`）
2. **Tool Discovery**：client 发送 `tools/list` 发现可用工具及其 `inputSchema`
3. **Tool Execution**：client 发送 `tools/call` 携带工具名与参数，server 返回结构化的 `content` 数组（支持文本、图片、resource 等多种内容类型）
4. **Real-time Updates**：client 通过 `subscriptions/listen` 订阅变更通知，server 在工具列表变化时推送 `notifications/tools/list_changed`，client 据此刷新工具注册表

这套发现→执行→订阅的模式，让 AI 应用能够动态地了解 server 能力、按需调用，并在能力变化时及时响应，而不需要在编译期硬编码每个 server 提供什么。

## 权威参考

- MCP 官方文档 [Architecture overview](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)
