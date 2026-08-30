# MCP Client 概念：Elicitation 与已废弃原语

MCP Client 由 Host 应用实例化，用于和某个特定的 MCP Server 通信。Host（如 Claude.ai 或某个 IDE）管理整体用户体验并协调多个 Client；每个 Client 只负责与一个 Server 的直接通信——理解"Host 是用户交互的应用，Client 是使能 server 连接的协议层组件"这一区分很重要。

除了使用 server 提供的上下文外，client 也可以向 server 反向提供若干特性，让 server 作者能构建更丰富的交互：

| 特性 | 说明 | 状态 |
|---|---|---|
| **Elicitation** | server 在交互过程中向用户请求特定信息 | 当前有效 |
| **Roots** | client 向 server 声明应聚焦的目录范围 | 已废弃（`2026-07-28`） |
| **Sampling** | server 通过 client 请求 LLM 补全 | 已废弃（`2026-07-28`） |

## 1. Elicitation

Elicitation 让 server 能在交互过程中向用户请求特定信息，提供了一种按需收集必要信息的结构化方式：server 不必要求一次性提供全部信息，也不必在信息缺失时直接失败,而是可以暂停操作、请求特定输入。

### 两种模式

- **Form 模式**：server 要求 client 从用户处收集结构化数据。请求携带一个 schema，client 据此构建输入表单并校验响应
- **URL 模式**：server 提供一个 URL 供用户打开，交互在协议之外进行，数据不经过 client。适用于敏感流程（如凭据输入、第三方 OAuth 授权）

### 交互流程

Elicitation 遵循 **Multi Round-Trip Requests（MRTR）**模式：当 server 处理某个请求（如 `tools/call`）过程中需要用户输入时，它返回一个 `InputRequiredResult`，其 `inputRequests` 字段携带一个或多个 `elicitation/create` 请求；client 收集输入后携带 `inputResponses` 重试原请求，并回传 server 提供的 `requestState`。

### 用户交互模型

- **请求展示**：client 清晰展示是哪个 server 在请求、为何需要、如何使用该信息
- **响应选项**：用户可通过合适的 UI 控件提供信息、拒绝提供（可附带说明）或取消整个操作；client 在返回给 server 前按 schema 校验响应
- **URL 处理**：URL 模式下 client 展示完整 URL 并征得用户明确同意后才打开，**绝不**自动抓取该 URL；client 只知道用户是否同意，交互本身留在用户与目标站点之间
- **隐私考量**：server **不得**用 form 模式请求密码、API key、access token、支付凭据等敏感信息——这类交互应走 URL 模式，让数据留在协议之外，永远不经过 client 或 LLM 上下文

## 2. 已废弃：Roots

> Roots 已在协议版本 `2026-07-28` 中废弃并计划移除。新实现应通过工具参数、resource URI 或 server 配置传递目录/文件信息。

Roots 曾用于定义 server 操作的文件系统边界，让 client 告知 server 应聚焦哪些目录。它们始终使用 `file://` URI scheme，本质是**协调机制而非安全边界**——规范要求 server "应该（SHOULD）尊重"根边界，而非"必须（MUST）强制"，因为 server 运行的代码 client 无法控制；真正的安全约束必须在操作系统层面（文件权限、沙箱）落地。

## 3. 已废弃：Sampling

> Sampling 已在协议版本 `2026-07-28` 中废弃并计划移除。新实现应直接对接 LLM 提供商 API。

Sampling 曾允许 server 通过 client 请求语言模型补全，让 server 无需自行集成或付费使用 AI 模型，同时把用户权限与安全措施的控制权完全留在 client 侧。其流程与 Elicitation 相同的 MRTR 模式，`InputRequiredResult` 携带 `sampling/createMessage` 请求，并可选携带 `tools` 数组让 server 在采样过程中请求工具调用。

设计上强调 human-in-the-loop：用户可在请求发出前审批/修改，在响应返回前再次审批/修改——两轮人工检查点确保 server 请求的 AI 交互不能绕过用户同意访问敏感数据。

## 4. 已废弃：Logging（client 侧）

Logging 曾用于 server 向 client 发送日志消息以便调试和监控。新实现应改为写 `stderr`（stdio 传输场景）或使用 OpenTelemetry，不再依赖协议内的日志原语。

## 权威参考

- MCP 官方文档 [Understanding MCP clients](https://modelcontextprotocol.io/docs/2026-07-28/learn/client-concepts)
