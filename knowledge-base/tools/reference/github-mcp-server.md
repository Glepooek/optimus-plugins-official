# GitHub MCP Server

- **网址**：https://github.com/github/github-mcp-server
- **简介**：GitHub 官方 MCP server，把 AI 工具直接接到 GitHub 平台上——用自然语言读仓库与代码、处理 issue 与 PR、分析代码、自动化工作流。
- **开发语言**：Go
- **核心能力**：
  - Repository Management：浏览/查询代码、搜索文件、分析提交
  - Issue & PR Automation：创建与更新 issue / PR、分流、看板维护
  - CI/CD & Workflow Intelligence：监控 Actions 运行、构建失败、发布
  - Code Analysis：安全告警、Dependabot alert、代码模式
  - Team Collaboration：discussion、通知、团队活动
  - 工具集按需装载：`--toolsets` / `GITHUB_TOOLSETS` 选 toolset（`context`/`actions`/`issues`/`pull_requests`/`repos`/`code_security` 等 20+ 项，默认集为 context+repos+issues+pull_requests+users），`--tools` / `GITHUB_TOOLS` 精确到单个工具；另有只读模式 `--read-only` 与 insiders 抢先模式
- **安装方式**：
  远程托管（官方称"最简单的上手方式"），端点 `https://api.githubcopilot.com/mcp/`，支持 OAuth 或 PAT：
  ```json
  {
    "servers": {
      "github": {
        "type": "http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": { "Authorization": "Bearer ${input:github_mcp_pat}" }
      }
    }
  }
  ```
  本地 Docker（镜像 `ghcr.io/github/github-mcp-server`）：
  ```
  docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=<token> ghcr.io/github/github-mcp-server
  ```
  也可 `go build` 从源码构建后跑 `github-mcp-server stdio`。GitHub Enterprise Server 不支持远程托管，须本地部署并用 `--gh-host` / `GITHUB_HOST` 指向自建实例。
- **备注**：⚠️ **本仓库曾接入远程端点，2026-09-18 已移除**，`commit-cc-plugin` 的 PR 流程改用 GitHub CLI（本仓库已收录，见 `tools.ref.github-cli`）。两者能力高度重叠，取舍理由与 Playwright MCP vs CLI 那条同构——coding agent 场景下 CLI 更省 token（不必把大型 tool schema 塞进上下文），且 `gh` 覆盖了本仓需要的开 PR / 轮询必需检查 / squash merge 三个动作。MCP 的优势在需要持久化状态与迭代式探索的长程 agentic 场景，以及 toolset 粒度的能力裁剪。MIT 许可，GitHub 33k star，最新版本 v1.12.2（2026-09-16）。
