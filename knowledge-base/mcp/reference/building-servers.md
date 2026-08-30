# 构建 MCP Server

自建 MCP server 是把已有能力（查询数据库、调用外部 API、读写文件等）按 MCP 协议暴露给任意兼容 client 使用的方式，一次实现即可被所有支持 MCP 的 Host 复用，无需为每个 AI 应用单独适配。

## 1. Server 可提供的三种能力

参照 `server-concepts.md` 的定义，构建 server 时需要决定该能力应建模为哪种原语：

1. **Resources**：客户端可读取的类文件数据（如 API 响应、文件内容）——被动提供上下文
2. **Tools**：可被 LLM 调用的函数（需用户批准）——主动执行动作
3. **Prompts**：帮助用户完成特定任务的预写模板

多数开发工作聚焦在 Tools 上，因为它是模型主动决策调用、直接产生行为效果的原语。

## 2. 典型开发步骤（以官方 Python SDK 示例为参照）

1. **选择 SDK**：MCP 提供多语言官方 SDK（Python、TypeScript、Java、C# 等），优先选择目标语言的官方 SDK 而非手搓 JSON-RPC 处理逻辑
2. **定义 Server 实例**：初始化一个 server 对象，声明名称与支持的能力
3. **注册 Tools**：为每个 tool 定义唯一名称、描述、输入 schema（JSON Schema），并实现对应的执行逻辑；工具命名应清晰具体（如 `get_alerts`、`get_forecast`），避免笼统命名
4. **实现工具逻辑**：工具内部调用真实的外部依赖（API、数据库等），返回结构化的 `content`（文本、图片、resource 引用等）
5. **选择传输方式**：本地场景用 stdio 传输；需要被多 client 远程访问时用 Streamable HTTP 传输
6. **连接到 Host 验证**：将 server 接入某个支持 MCP 的 Host（如 Claude Desktop）进行端到端验证，观察工具是否被正确发现、调用、返回预期结果

## 3. 日志与调试

- **stdio 传输下不要用 stdout 输出日志**——stdout 通道被协议消息占用，混入日志会破坏 JSON-RPC 消息帧；日志应写入 `stderr`
- 开发阶段可结合 MCP Inspector 工具直接调用 server 的 `tools/list`、`tools/call` 等方法，脱离 Host 单独验证 server 行为
- Host（如 Claude Desktop）通常会记录 MCP 连接日志与各 server 的 stderr 输出到本地日志文件，排查连接失败或工具调用异常时应先查看这些日志

## 4. 常见注意事项

- Tool 的 `inputSchema` 应尽量精确（标注必填字段、枚举取值范围），这直接影响模型能否正确构造调用参数
- Tool 的 `description` 应说明"做什么"与"何时用"，这是模型决定是否调用该工具的主要依据
- 涉及写操作（改文件、发消息、下单等）的 tool，应设计为需要用户批准才能执行，而非静默执行
- Server 只应声明自己真正实现的能力（`capabilities`），未实现的能力不应在 `server/discover` 响应中声明，否则 client 会尝试调用不存在的方法

## 权威参考

- MCP 官方文档 [Build an MCP server](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server)
- MCP 官方 SDK 列表 [SDKs](https://modelcontextprotocol.io/docs/2026-07-28/sdk)
