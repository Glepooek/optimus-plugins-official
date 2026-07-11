# CLAUDE.md

本文件为 Claude Code 在此仓库中工作时提供指导。

## 仓库概览

自定义的 Claude Code 插件仓库，8 个领域插件提供企业级开发工具链。

### 插件职责速查

| 插件 | 职责 |
|---|---|
| `optimus-frontend-plugin` | React/Vue/WPF 前端开发、UI 设计规范 |
| `optimus-backend-plugin` | API 开发、后端架构、数据库设计 |
| `optimus-qa-plugin` | 测试用例、JMeter、UI 自动化 |
| `optimus-prd-plugin` | PRD 文档创建、审查、需求管理 |
| `optimus-feishu-plugin` | 飞书文档读写、上传、自动化 |
| `optimus-office-plugin` | Word/Excel/PPT/PDF 生成与处理 |
| `optimus-devops-plugin` | Jenkins CI/CD、项目分析；内置 SessionStart + Notification hooks |
| `optimus-mcp-servers` | GitHub Copilot MCP、MasterGo、飞书项目等 MCP 集成 |

### 目录结构

```
plugins/{plugin-name}/
├── skills/{skill-name}/SKILL.md    # Skill 定义
├── commands/{cmd}/COMMAND.md       # Commands（如有）
├── subagents/{name}/AGENT.md       # Subagents（如有）
├── mcp/{name}/                     # MCP 服务器配置（如有）
└── hooks/hooks.json                # Hooks 配置（可选）

.claude/skills/{skill-name}/SKILL.md  # 项目级 skill（本仓库工作流专用，不进 marketplace）
```

---

## 重要约束

- **跨插件无重复 skills**：每个插件专注特定领域，新功能前先确认无跨插件重叠
- **Skills 可相互引用**：子 skill 用相对路径，跨插件用绝对命名空间
- **复合 skills 很少见**：仅在 3 个以上阶段且每阶段 >200 行时使用

---

## 开发规范

### Skill 调用规则

- 简单 skill：`/plugin-name:skill-name`
- 复合 skill：`/plugin-name:skill-name:substep`
- `optimus-fe-dev` 是唯一的复合 skill（5 阶段工作流），触发词：`/optimus-frontend-plugin:optimus-fe-dev`，详见 `plugins/optimus-frontend-plugin/skills/optimus-fe-dev/ARCHITECTURE.md`

### Hooks

Hooks 自动加载自 `plugins/{plugin-name}/hooks/hooks.json`，当前配置见 `plugins/optimus-devops-plugin/hooks/hooks.json`。

---

## 本地测试

修改任何 skill / hook / command 后，用 `--plugin-dir` 加载本仓库进行测试：

```bash
# 加载本仓库所有插件（推荐用于完整测试）
claude --plugin-dir "E:\ProjectxPlex\optimus-plugins-official"

# 也可以只加载单个插件目录
claude --plugin-dir "E:\ProjectxPlex\optimus-plugins-official\plugins\optimus-devops-plugin"
```

启动新会话后，直接输入触发词验证行为（无需重启、无需重新安装）。文件改动立即生效。

---

## 版本管理规则

| 变更路径 | 操作类型 | 版本升级 |
|---|---|---|
| `.claude/` 下任何文件 | 任意 | **不升级** |
| `plugins/` 下新增 skill/hook/command | 新增 | **Minor** `x.X.x` |
| `plugins/` 下更新/修复已有内容 | 更新 | **Patch** `x.x.X` |
| `plugins/` 下删除/重命名用户可见功能 | 删除 | **Major** `X.x.x` |

升级时编辑 `.claude-plugin/marketplace.json` 的 `version` 字段，随本次提交一并推送。

---

## Skill 级版本管理

每个 skill 维护**独立的语义版本**，与仓库 marketplace 版本号分开管理。

### SKILL.md frontmatter 版本号

新增或修改 skill 时，必须同步更新 SKILL.md frontmatter 中的 `version` 字段：

| 变更类型 | Skill 版本升级 |
|---|---|
| 新增功能、新增章节、新增参数 | **Minor** `x.X.x` |
| 修改/修复已有内容、文档优化、重构 | **Patch** `x.x.X` |
| 破坏性变更（接口不兼容、删除用户可见功能） | **Major** `X.x.x` |

```yaml
---
name: my-skill
version: 1.2.0
description: ...
---
```

### CHANGELOG.md

每个 skill 目录**必须**有 `CHANGELOG.md`，提交前必须更新，格式：

```markdown
## [版本号] - YYYY-MM-DD

### Added
- 新增的功能或章节

### Changed
- 修改的内容

### Removed
- 删除的内容

### Fixed
- 修复的问题
```

规则：
- 只写实际发生的类别，无变更的类别可省略
- 新建 skill 时同步创建 CHANGELOG.md，初始版本为 `[1.0.0]`
- agent（AGENT.md）遵循相同规范

---

## 提交与推送（强制）

**必须**使用 `commit-cc-plugin` skill，禁止手动执行 git 工作流。说"提交"或"推上去"即可触发。

---

## 关键文件

| 文件 | 用途 |
|---|---|
| `.claude-plugin/marketplace.json` | 插件仓库元数据和版本号 |
| `.claude/skills/commit-cc-plugin/SKILL.md` | 提交发布 skill（含版本决策规则） |
| `.claude/skills/sync-cc-tips/SKILL.md` | tips.txt 自动同步 skill（从 CC changelog 同步） |
| `plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt` | 235 条 Claude Code 使用技巧 |
| `plugins/optimus-frontend-plugin/skills/optimus-fe-dev/ARCHITECTURE.md` | 复合 skill 模式参考实现 |
