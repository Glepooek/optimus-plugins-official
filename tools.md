## Skill

## MCP

### Playwright MCP

- **网址**：https://github.com/microsoft/playwright-mcp
- **简介**：Microsoft 官方推出的 Model Context Protocol (MCP) server，基于 Playwright 提供浏览器自动化能力；通过结构化的 accessibility snapshot 让 LLM 与网页交互，无需截图或视觉模型。
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
- **备注**：官方 README 明确区分了与 `playwright-cli`（本仓库已收录）的定位——coding agent 场景官方推荐优先用 CLI+SKILLS，因为 CLI 调用更省 token（不需要把大型 tool schema 和冗长 accessibility tree 塞进模型上下文）；MCP 更适合需要持久化状态、迭代式页面结构推理的探索式自动化/自愈测试等长程 agentic 场景。两者同属 Playwright 生态的互补方案，非替代关系。GitHub 35k star，Apache-2.0 许可，最新版本 v0.0.78（2026-07-09）。

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
- **更新方式**：`npm install apifox-cli@latest -g`（官方文档"更新 Apifox CLI"章节明确给出）
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
- **更新方式**：重新执行 `npm install -g @playwright/cli@latest`（README 未单独给出更新命令，安装命令本身用的是 `@latest` tag，重新执行即会覆盖为最新版本）
- **备注**：本仓库当前使用的 `playwright-cli` skill（用户级 `~/.claude/skills/playwright-cli`）正是基于这个工具；`record-tools` skill 本身抓取网页时也优先用它作为主要抓取方式。GitHub 11.9k star，Apache-2.0 许可，最新版本 v0.1.17（2026-07-09）。

### lark-cli (Lark/Feishu CLI)

- **网址**：https://github.com/larksuite/cli
- **简介**：Lark/Feishu 官方命令行工具，由 larksuite 团队维护，专为人类与 AI Agent 设计，覆盖日历、IM消息、文档、云盘、多维表格、电子表格、幻灯片、任务、知识库、通讯录、邮件、会议纪要、审批、OKR 等 18 个业务域，200+ 精选命令。
- **核心能力**：
  - Agent-Native 设计：24 个开箱即用的结构化 Skills，兼容主流 AI 工具，Agent 零配置即可操作 Lark/Feishu
  - 三层命令体系：Shortcuts（`+`前缀，人类和AI友好，含 dry-run 预览）→ API Commands（自动生成，1:1 映射平台端点，100+ 命令）→ Raw API（直调任意端点，覆盖 2500+ API）
  - JSON 输出契约明确：success/error 信封区分（用 `ok` 字段判定成功与否，而非 `code==0`），支持 json/pretty/table/ndjson/csv 多种输出格式
  - 安全可控：输入注入防护、终端输出脱敏、OS 原生 keychain 凭证存储
  - 支持身份切换（`--as user/bot`）、自动分页（`--page-all`）、schema 自省（`lark-cli schema`）等高级用法
- **安装方式**：
  - 推荐（npm）：`npx @larksuite/cli@latest install`
  - 从源码构建：需要 Go v1.23+ 和 Python 3，`git clone` 后 `make install`
  - 配置与登录：`lark-cli config init` → `lark-cli auth login --recommend`
- **更新方式**：重新执行 `npx @larksuite/cli@latest install`（README 未单独给出更新命令，安装命令本身用的是 `@latest` tag，重新执行即会覆盖为最新版本）
- **备注**：⚠️ 官方 README 专设"Security & Risk Warnings"章节明确提示：该工具可被 AI Agent 调用以自动化操作 Lark/Feishu 开放平台，存在模型幻觉、不可预测执行、prompt injection 等固有风险；授权后 Agent 将以用户身份在授权范围内操作，可能导致敏感数据泄露或未授权操作，官方建议不要主动放宽默认安全设置。与本仓库 `optimus-feishu-plugin`（飞书文档读写、上传、自动化）属相关领域，是潜在的补充/替代方案，尚未集成。MIT 许可，GitHub 15.5k star，最新版本 v1.0.68（2026-07-09）。

## Agent

## Plugin
