# Playwright MCP

- **网址**：https://github.com/microsoft/playwright-mcp
- **简介**：Microsoft 官方推出的 Model Context Protocol (MCP) server，基于 Playwright 提供浏览器自动化能力；通过结构化的 accessibility snapshot 让 LLM 与网页交互，无需截图或视觉模型。
- **开发语言**：TypeScript
- **核心能力**：
  - 基于 accessibility tree 而非像素/截图的浏览器自动化，快速轻量、LLM 友好
  - 确定性工具调用，避免截图方案常见的歧义
  - 标准 MCP config 一键接入 20+ 主流客户端（VS Code、Cursor、Claude Code、Claude Desktop、Windsurf、Copilot、Cline 等）
  - 60+ 命令行参数细粒度配置：host/origin 白名单、代理、超时、viewport、设备模拟、CDP 连接等
  - 两种浏览态：Persistent Profile（持久化登录态）/ Isolated（每次会话隔离）
  - 可选能力模块（`--caps`）：config / network / storage / devtools / vision（坐标点击）/ pdf / testing（断言）
  - 支持浏览器扩展模式连接已有标签页复用登录态；支持 Docker 部署、编程式（Programmatic）调用
- **安装方式**：
  标准 config（写入 MCP client 配置）：
  ```json
  {
    "mcpServers": {
      "playwright": {
        "command": "npx",
        "args": ["@playwright/mcp@latest"]
      }
    }
  }
  ```
  也支持 VS Code 一键安装链接、Docker 部署。
- **更新方式**：`args` 固定使用 `@playwright/mcp@latest`，MCP client 每次启动都会拉取最新版本，无需手动更新；如需锁定版本可将 `@latest` 替换为具体版本号（如 `@playwright/mcp@0.0.78`）
- **移除方式**：从 MCP client 配置文件的 `mcpServers` 中删除 `"playwright"` 对应条目即可（通过 npx 按需运行，未做全局安装，无需额外卸载操作）
- **备注**：官方 README 明确区分了与 `playwright-cli`（本仓库已收录，见 `tools.ref.playwright-cli`）的定位——coding agent 场景官方推荐优先用 CLI+SKILLS，因为 CLI 调用更省 token（不需要把大型 tool schema 和冗长 accessibility tree 塞进模型上下文）；MCP 更适合需要持久化状态、迭代式页面结构推理的探索式自动化/自愈测试等长程 agentic 场景。两者同属 Playwright 生态的互补方案，非替代关系。GitHub 35k star，Apache-2.0 许可，最新版本 v0.0.78（2026-07-09）。
