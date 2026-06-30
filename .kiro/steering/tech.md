# 技术栈

## 插件开发规范

本仓库是 Claude Code 插件仓库，不使用传统编程语言构建。核心交付物为 Markdown 格式的 SKILL.md 文件和配置文件。

### 文件类型

| 类型 | 格式 | 用途 |
|------|------|------|
| Skills | Markdown (SKILL.md) | 定义 AI 能力和工作流 |
| Hooks | JSON (hooks.json) + Shell/PowerShell | 会话事件自动化 |
| MCP 配置 | JSON (.mcp.json) | 外部 MCP 服务器声明 |
| 辅助脚本 | Python / Bash / PowerShell | Skills 和 Hooks 的实现脚本 |

### 运行环境

- **主要平台**：Windows（PowerShell / Git Bash）
- **Shell 脚本**：Bash（通过 Git Bash 运行）
- **Python 脚本**：Python 3.x（部分 QA 和后端 Skills 依赖）
- **Node.js**：npx（MCP 服务器启动依赖）

### MCP 服务器

| 服务 | 类型 | 用途 |
|------|------|------|
| GitHub Copilot | HTTP | 代码生成增强 |
| MasterGo Magic | stdio (npx) | 设计稿协作转换 |
| Feishu Project | stdio (npx) | 飞书项目管理同步 |

### Hooks 机制

| Hook 类型 | 触发时机 | 实现 |
|-----------|----------|------|
| SessionStart | 会话启动 | Bash 脚本展示技巧轮播 |
| Notification | 权限提示 | PowerShell 脚本 Windows 通知 |

### 依赖工具

- **Git** — 版本控制，提交遵循 Conventional Commits
- **Claude Code** — 插件宿主环境
- **npx** — MCP 服务器按需启动
- **PowerShell** — Windows 平台 Hooks 执行
- **Git Bash** — 跨平台 Shell 脚本执行
