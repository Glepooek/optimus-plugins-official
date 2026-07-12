## Skill

## MCP

## CLI

### Apifox CLI

- **网址**：https://apifox.com/apifox-cli/
- **简介**：Apifox（API 全生命周期管理工具）官方推出的命令行工具，主打"一行命令让 Apifox 与 AI Agent 形影不离"——可在本地终端或 CI/CD 流水线中直接自动化完整 API 工作流，免去频繁切换窗口。
- **支持的 AI Agent / IDE**：Claude Code、Codex、Cursor、Antigravity、OpenClaw、Trae、Windsurf、GitHub Copilot、Cline、Hermes Agent
- **核心能力**：
  - 接口资源管理、测试用例 / 测试场景 / 测试套件管理
  - 数据模型管理、写入前 JSON 校验（提前发现缺失字段、类型错误、结构不匹配）
  - 自动化测试运行 + 多格式报告（CLI / HTML / JSON / JUnit）
  - 数据导入导出支持 30+ 格式，包括 OpenAPI、Postman、HAR、JMeter、WSDL、Markdown
  - AI 分支安全写入（在独立分支创建/修改资源，避免直接污染主分支数据，确认无误再合并）
  - 分支与资源协作（lock/merge 流程，避免多人协作和版本化接口管理冲突）
- **安装方式**：
  - AI Agent 自动安装（推荐）：对 Agent 说"阅读说明并帮我安装 Apifox CLI：https://apifox.com/apifox-cli-installation-guide.md"，由其自主完成安装、登录、配置
  - 手动安装：参考帮助文档 https://docs.apifox.com/cli-command-options
- **备注**：与本仓库 `optimus-qa-plugin` 下 `optimus-qa-jmeter-scripts`、`optimus-qa-test-design` 两个 skill 当前依赖的 `apifox-mcp-server`（MCP方式）同属 Apifox 生态，是获取 OpenAPI 规范/生成 JMeter 脚本的潜在替代或补充方案，尚未集成。

### Playwright CLI

- **网址**：https://github.com/microsoft/playwright-cli
- **简介**：Microsoft 官方推出的 Playwright 命令行工具，用命令行方式执行浏览器自动化操作（打开页面、点击、填表、截图、生成PDF等），相比 MCP 方式更省 token——不会把整页数据强塞进 LLM 上下文。
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
- **备注**：本仓库当前使用的 `playwright-cli` skill（用户级 `~/.claude/skills/playwright-cli`）正是基于这个工具；`record-tools` skill 本身抓取网页时也优先用它作为主要抓取方式。GitHub 11.9k star，Apache-2.0 许可，最新版本 v0.1.17（2026-07-09）。

## Agent

## Plugin
