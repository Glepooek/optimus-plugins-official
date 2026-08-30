# 接入 MCP Server：本地（stdio）与远程（Streamable HTTP）

接入一个已有的 MCP server 分两种形态：本地 server（安装运行在本机）与远程 server（部署在互联网上）。两者接入方式、鉴权方式与适用场景不同。

## 1. 本地 MCP Server（stdio 传输）

本地 server 是运行在与 client 同一台机器上的程序，通过 stdio 传输与 client 通信——无网络开销，通常由单个 client 独占服务。

### 典型接入方式

以 Claude Desktop 接入官方 Filesystem Server 为例，接入的核心是一份 JSON 配置文件（`claude_desktop_config.json`），告诉 Host 启动哪个命令、传什么参数：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/Desktop",
        "/Users/username/Downloads"
      ]
    }
  }
}
```

- `"filesystem"`：该 server 在 Host 界面中显示的名字
- `"command"`：启动该 server 进程的可执行程序（此处用 `npx`）
- `"args"`：传给该命令的参数，包含 server 允许访问的目录列表

配置生效后需要完全重启 Host 应用以加载新配置。

### 安全考量

本地 server 以用户账户权限运行，能执行用户手动可执行的任何文件操作——因此：

- 只授予自己确定放心让 server 读写的目录
- 每次文件系统操作执行前，规范良好的 Host 会请求用户批准，用户应逐条审查后再批准
- Server 作者应通过 stdio 传输本身限制访问范围（仅限当前 client），或在使用 HTTP 传输时要求鉴权 token / 使用带访问限制的 IPC 机制

## 2. 远程 MCP Server（Streamable HTTP 传输）

远程 server 部署在互联网上而非本机，功能上与本地 server 类似（同样暴露 tools/resources/prompts），但**任何联网的 MCP client 都能访问**，不需要在每台设备上单独安装配置——这使其更适合 Web 应用、强调易用性的集成，以及需要服务端处理或鉴权的服务。

### 典型接入方式

以 Claude 接入 Custom Connector 为例，接入流程为：

1. 在 Connector 设置中添加自定义连接器，填入远程 server 的 URL（如 `https://example-server.modelcontextprotocol.io/mcp`）
2. 完成鉴权——多数远程 server 要求鉴权以确保安全访问，常见方式包括 OAuth、API key 或用户名/密码，具体流程由 server 实现决定
3. 鉴权完成后，该 server 的 resources 和 prompts 在对话中可用
4. 可在连接器设置中配置工具权限，控制允许使用哪些工具、设置用量限制等安全参数

### 使用建议

- **验证可信度**：连接前核实远程 server 的真实性，只连接来自可信来源的 server，审查鉴权过程中请求的权限范围，对授予敏感数据/系统访问权限保持谨慎
- **管理多个连接器**：可同时连接多个远程 server；按用途/项目组织连接器；定期审查并移除不再使用的连接器

## 3. 本地 vs 远程的选择依据

| 维度 | 本地（stdio） | 远程（Streamable HTTP） |
|---|---|---|
| 部署 | 每台设备单独安装配置 | 一次部署，任意联网 client 可用 |
| 性能 | 无网络开销 | 受网络延迟影响 |
| 典型场景 | 文件系统、本地数据库等需要直接系统访问的能力 | 云端服务集成（项目管理、代码仓库、第三方 API） |
| 鉴权 | 通常无需鉴权（进程隔离本身即边界） | 通常需要 OAuth/API key/Bearer token |
| 服务对象 | 通常单 client 独占 | 通常多 client 共享 |

## 权威参考

- MCP 官方文档 [Connect to local MCP servers](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers)
- MCP 官方文档 [Connect to remote MCP Servers](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-remote-servers)
