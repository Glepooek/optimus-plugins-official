# 构建 MCP Client

自建 MCP client 通常是为了让某个 AI 应用（如自研聊天机器人）具备连接任意 MCP server 的能力，而不是只能对接单一固定的工具集。

## 1. Client 的核心职责

一个 MCP client 需要完成：

1. **连接 server**：按 server 声明的传输方式（stdio 或 Streamable HTTP）建立连接
2. **发现能力**：调用 `server/discover`（可选）与各原语的 `*/list` 方法，获知该 server 提供哪些 tools/resources/prompts
3. **桥接 LLM 与 server**：把发现到的 tools 转换为 LLM 能理解的工具定义格式，注入到与 LLM 的对话中
4. **执行调用**：当 LLM 决定调用某个工具时，client 负责路由该调用到正确的 server、执行、并把结果返回给对话上下文
5. **处理原语支持**：若 client 声明支持 Elicitation 等能力，需要实现对应的用户交互 UI

## 2. 典型开发步骤（以官方 Python SDK 示例为参照）

1. **选择 SDK**：与构建 server 一样，优先用目标语言的官方 MCP SDK 处理协议细节，而非自行实现 JSON-RPC 消息处理
2. **建立连接**：用 SDK 提供的 client 类连接到目标 server（stdio 场景通常是启动子进程并通过管道通信；HTTP 场景是发起网络连接）
3. **完成 LLM 集成**：把 MCP client 与某个 LLM API（如 Anthropic API）串联起来，形成"用户提问 → LLM 决定调用工具 → MCP client 执行 → 结果回传 LLM → 生成回复"的完整闭环
4. **发现并注册工具**：连接建立后调用 `tools/list`，将返回的工具定义注册进对话的可用工具列表
5. **处理工具调用循环**：当 LLM 响应中包含工具调用请求时，client 提取工具名与参数，调用 `tools/call`，把结果重新提交给 LLM 继续生成

## 3. 联邦多个 Server 时的注意事项

当 client 需要同时连接多个 server 时：

- **工具命名冲突**：不同 server 可能注册同名工具，client 需要按 server 来源做命名空间隔离，避免调用路由错误
- **渐进式工具发现**：连接的 server 数量增多时，一次性把所有工具塞进 LLM 上下文会占用大量 token 且降低模型选择准确率；可采用渐进式发现——仅在需要时才拉取某个 server 的详细工具列表，而不是无差别加载全部
- **能力差异处理**：不同 server 支持的能力集合不同（有的支持 `tools`，有的还支持 `resources`），client 应按 `server/discover` 返回的 `capabilities` 判断可用哪些操作，不要假设所有 server 能力一致

## 4. 常见注意事项

- Client 应对工具调用结果做校验和错误处理，不能假设 server 总是返回预期格式的结果
- 涉及敏感操作的工具调用前，client 应给用户可见的确认机制，而不是让 LLM 完全自主决定
- Client 若要支持远程 server 的 OAuth 鉴权流程，需要正确处理鉴权回调、token 刷新与过期重鉴权

## 权威参考

- MCP 官方文档 [Build an MCP client](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-client)
- MCP 官方 SDK 列表 [SDKs](https://modelcontextprotocol.io/docs/2026-07-28/sdk)
