# CLAUDE.md

本文件为 Claude Code 在此仓库中工作时提供指导。

## 提问质量引导

当用户问题属于以下情况时，**回答前**先给出精准化版本并询问是否按此继续：

| 模糊信号 | 缺失维度 | 引导方向 |
|---|---|---|
| "看看"、"核对"、"检查" | 检查维度不明 | 补充：具体检查哪些方面 |
| "改改"、"优化"、"整理" | 优化目标不明 | 补充：改进方向 |
| "帮我弄一下"、"搞一下" | 操作范围不明 | 补充：操作对象和期望结果 |
| 问题少于 15 字且无具体对象 | 成功标准不明 | 补充：什么状态算完成 |

引导格式：`建议更精准的提问：「…」按此继续，还是你有其他侧重？`

**不触发**：已含明确对象和验收标准；上下文已足够清晰；用户说"你看着办"。

---

## 仓库概览

Unipus 官方 Claude Code 插件仓库，8 个领域插件提供企业级开发工具链。**这是插件集合仓库，没有构建/测试命令。**

### 插件职责速查

| 插件 | 职责 |
|---|---|
| `unipus-frontend-plugin` | React/Vue/WPF 前端开发、UI 设计规范 |
| `unipus-backend-plugin` | API 开发、后端架构、数据库设计 |
| `unipus-qa-plugin` | 测试用例、JMeter、UI 自动化 |
| `unipus-prd-plugin` | PRD 文档创建、审查、需求管理 |
| `unipus-feishu-plugin` | 飞书文档读写、上传、自动化 |
| `unipus-office-plugin` | Word/Excel/PPT/PDF 生成与处理 |
| `unipus-devops-plugin` | Jenkins CI/CD、项目分析；内置 SessionStart + Notification hooks |
| `unipus-mcp-servers` | GitHub Copilot MCP、MasterGo、飞书项目等 MCP 集成 |

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

## 工作流规则

### 提交与推送（强制）

**必须**使用 `unipus-commit` skill，禁止手动执行 git 工作流。说"提交"或"推上去"即可触发。

### 版本管理规则

| 变更路径 | 操作类型 | 版本升级 |
|---|---|---|
| `.claude/` 下任何文件 | 任意 | **不升级** |
| `plugins/` 下新增 skill/hook/command | 新增 | **Minor** `x.X.x` |
| `plugins/` 下更新/修复已有内容 | 更新 | **Patch** `x.x.X` |
| `plugins/` 下删除/重命名用户可见功能 | 删除 | **Major** `X.x.x` |

升级时编辑 `.claude-plugin/marketplace.json` 的 `version` 字段，随本次提交一并推送。

### Skill 调用规则

- 简单 skill：`/plugin-name:skill-name`
- 复合 skill：`/plugin-name:skill-name:substep`
- `unipus-fe-dev` 是唯一的复合 skill（5 阶段工作流），详见 `plugins/unipus-frontend-plugin/skills/unipus-fe-dev/ARCHITECTURE.md`

### Hooks

Hooks 自动加载自 `plugins/{plugin-name}/hooks/hooks.json`。当前启用：
- **SessionStart**：tips.txt 技巧轮播（unipus-devops-plugin）
- **Notification**：Windows 权限通知（unipus-devops-plugin）

> Windows 注意：show-tip.sh 若出现 GBK 编码错误，已在脚本第 34-36 行内置 UTF-8 包装器修复。

---

## 关键文件

| 文件 | 用途 |
|---|---|
| `.claude-plugin/marketplace.json` | 插件仓库元数据和版本号 |
| `.claude/skills/unipus-commit/SKILL.md` | 提交流程 skill（含详细版本规则） |
| `.claude/skills/update-tips/SKILL.md` | tips.txt 自动更新 skill |
| `plugins/unipus-devops-plugin/hooks/sessionstart/tips.txt` | 203 条 Claude Code 使用技巧 |
| `plugins/unipus-frontend-plugin/skills/unipus-fe-dev/ARCHITECTURE.md` | 复合 skill 模式参考实现 |

---

## 重要约束

- **跨插件无重复 skills**：每个插件专注特定领域，新功能前先确认无跨插件重叠
- **Skills 可相互引用**：子 skill 用相对路径，跨插件用绝对命名空间
- **复合 skills 很少见**：仅在 3 个以上阶段且每阶段 >200 行时使用
