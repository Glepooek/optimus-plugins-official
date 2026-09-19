# Playwright CLI

- **网址**：https://github.com/microsoft/playwright-cli
- **简介**：Microsoft 官方推出的 Playwright 命令行工具，用命令行方式执行浏览器自动化操作（打开页面、点击、填表、截图、生成PDF等），相比 MCP 方式更省 token——不会把整页数据强塞进 LLM 上下文。
- **开发语言**：TypeScript
- **核心能力**：
  - 完整浏览器操作命令集：导航、点击、填表、拖拽、截图、生成 PDF 等
  - 多会话管理，可同时管理多个浏览器实例（`-s=<session>`）
  - 可视化监控面板（`playwright-cli show`），可实时查看/接管正在运行的浏览器会话
  - 网络请求拦截/模拟（route）、Cookie/LocalStorage/SessionStorage 管理
  - 追踪记录（tracing）、视频录制、生成 Playwright 定位器（locator）等开发调试能力
  - 支持 JSON 配置文件或环境变量做细粒度配置（浏览器类型、超时、代理、权限等）
- **安装方式**：
  ```
  npm install -g @playwright/cli@latest
  playwright-cli --help
  playwright-cli install --skills   # 安装配套 skills
  ```
- **更新方式**：重新执行 `npm install -g @playwright/cli@latest`（README 未单独给出更新命令，安装命令本身用的是 `@latest` tag，重新执行即会覆盖为最新版本）
- **备注**：本仓库当前使用的 `playwright-cli` skill（用户级 `~/.claude/skills/playwright-cli`）正是基于这个工具；`record-tools` skill 本身抓取网页时也优先用它作为主要抓取方式。GitHub 11.9k star，Apache-2.0 许可，最新版本 v0.1.17（2026-07-09）。
