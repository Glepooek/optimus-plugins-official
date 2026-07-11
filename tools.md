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

## Agent

## Plugin
