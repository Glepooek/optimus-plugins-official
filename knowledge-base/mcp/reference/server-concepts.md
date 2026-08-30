# MCP Server 概念：Tools / Resources / Prompts

MCP Server 是向 AI 应用暴露特定能力的程序，常见例子包括文件系统 server（文档访问）、数据库 server（数据查询）、GitHub server（代码管理）、Slack server（团队通信）、日历 server（日程安排）。

Server 通过三种构建块提供功能，三者的控制权归属不同：

| 原语 | 说明 | 典型例子 | 控制权归属 |
|---|---|---|---|
| **Tools** | 模型可主动调用的函数，模型根据用户请求自行决定何时使用；可写数据库、调外部 API、改文件、触发其他逻辑 | 搜索航班、发消息、创建日历事件 | 模型 |
| **Resources** | 被动的数据源，为上下文提供只读信息访问，如文件内容、数据库 schema、API 文档 | 检索文档、访问知识库、读取日历 | 应用 |
| **Prompts** | 预置的指令模板，引导模型如何配合特定工具和资源工作 | 规划一次旅行、总结会议、起草邮件 | 用户 |

## 1. Tools

Tools 让 AI 模型能够执行动作。每个 tool 定义一个具有类型化输入输出的具体操作，模型根据上下文自行请求执行。

**工作方式**：Tools 是 LLM 可调用的、按 schema 定义的接口，MCP 用 JSON Schema 做参数校验。每个 tool 只执行一个明确定义的操作。Tool 的执行可能需要用户同意，以确保用户始终掌控模型可执行的动作。

**协议方法**：

| 方法 | 用途 | 返回 |
|---|---|---|
| `tools/list` | 发现可用工具 | 带 schema 的工具定义数组 |
| `tools/call` | 执行指定工具 | 工具执行结果 |

**用户交互模型**：Tools 由模型控制（model-controlled），意味着模型可自动发现并调用。为保障信任与安全，应用可实现多种用户控制机制：在 UI 中展示可用工具供用户决定是否在特定交互中启用、为单次工具执行设审批对话框、为安全操作设预批权限、用活动日志展示全部工具执行记录及结果。

## 2. Resources

Resources 提供对信息的结构化访问，供 AI 应用检索后作为上下文提供给模型。

**工作方式**：Resources 暴露来自文件、API、数据库或任何其他来源的数据。应用可以直接访问这些信息，并自行决定如何使用——选取相关片段、用 embedding 搜索，或整体传给模型。每个 resource 有唯一的 URI（如 `file:///path/to/document.md`），并声明其 MIME 类型。

Resources 支持两种发现模式：

- **Direct Resources**：固定 URI 指向特定数据，如 `calendar://events/2024`
- **Resource Templates**：带参数的动态 URI，支持灵活查询，如 `travel://activities/{city}/{category}`；模板携带 title、description、预期 MIME 类型等元数据，具备自描述能力，并支持参数补全（如输入 "Par" 提示 "Paris"）

**协议方法**：

| 方法 | 用途 | 返回 |
|---|---|---|
| `resources/list` | 列出可用的 direct resources | resource 描述符数组 |
| `resources/templates/list` | 发现 resource templates | resource template 定义数组 |
| `resources/read` | 获取 resource 内容 | 带元数据的 resource 数据 |
| `subscriptions/listen` | 监听 resource 变更 | 更新通知流 |

监听某个 resource 的变化时，client 发送带 `resourceSubscriptions` 过滤条件的 `subscriptions/listen` 请求；server 在被监听资源变化时通过该流推送 `notifications/resources/updated`。

**用户交互模型**：Resources 由应用驱动（application-driven），应用在检索、处理、展示上下文时拥有灵活性。常见交互模式：类文件夹的树/列表视图浏览、搜索过滤界面、基于启发式或 AI 选择的自动上下文包含、单选或批量选择界面。协议本身不强制特定 UI 模式。

## 3. Prompts

Prompts 提供可复用模板，让 server 作者能为某个领域提供参数化提示词，或演示如何最佳使用该 server。

**工作方式**：Prompts 是定义了预期输入与交互模式的结构化模板，由**用户控制**（user-controlled），需要显式调用而非自动触发。Prompts 可以是上下文感知的——引用可用的 resources 和 tools 构成完整工作流；与 resources 类似，prompts 也支持参数补全以帮助用户发现有效的参数值。

**协议方法**：

| 方法 | 用途 | 返回 |
|---|---|---|
| `prompts/list` | 发现可用 prompts | prompt 描述符数组 |
| `prompts/get` | 获取 prompt 详情 | 带参数的完整 prompt 定义 |

**用户交互模型**：Prompts 需要显式调用，协议给实现者留出设计自由。关键原则：易于发现可用 prompts、清晰描述每个 prompt 的作用、支持带校验的自然参数输入、透明展示 prompt 的底层模板。常见 UI 模式：斜杠命令（输入 "/" 查看可用 prompts）、可搜索的命令面板、专用 UI 按钮、建议相关 prompts 的上下文菜单。

## 4. 多 Server 协同：原语如何组合工作

MCP 的真正威力体现在多个 server 协同工作、通过统一接口组合各自专长能力时。典型流程：

1. 用户调用一个带参数的 prompt（如 "plan-vacation"）
2. 用户从多个已连接的 server 中选择要包含的 resources（如日历、旅行偏好、历史行程）
3. AI 先读取所有选中的 resources 获取上下文，再依据上下文调用一系列 tools（搜索航班、查天气、订酒店、创建日历事件、发送邮件），必要时在关键步骤请求用户批准

这一流程展示了 Prompts（引导流程）、Resources（提供上下文）、Tools（执行动作）三种原语如何跨多个 server 组合，把原本需要数小时的任务在数分钟内完成。

## 权威参考

- MCP 官方文档 [Understanding MCP servers](https://modelcontextprotocol.io/docs/2026-07-28/learn/server-concepts)
