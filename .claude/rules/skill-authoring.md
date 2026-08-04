---
paths:
  - "**/SKILL.md"
  - "**/CHANGELOG.md"
  - "**/AGENT.md"
---

## Skill frontmatter 规范

每个 skill 维护**独立的语义版本**，与仓库 marketplace 版本号分开管理，并遵循开放 Agent Skills 规范（agentskills.io）——该规范只允许 `name`/`description`/`license`/`allowed-tools`/`metadata`/`compatibility` 六个顶层字段，出现其他顶层字段会导致跨 runtime 严格校验器报"Unexpected fields in frontmatter"错误。

### SKILL.md frontmatter 版本号

新增或修改 skill 时，必须同步更新 SKILL.md frontmatter 中 `metadata.version` 字段：

| 变更类型 | Skill 版本升级 |
|---|---|
| 新增功能、新增章节、新增参数 | **Minor** `x.X.x` |
| 修改/修复已有内容、文档优化、重构 | **Patch** `x.x.X` |
| 破坏性变更（接口不兼容、删除用户可见功能） | **Major** `X.x.x` |

版本号放在 `metadata` 下而非顶层，是为了兼容上述开放规范。

### metadata.author

所有 skill 统一署名：

```yaml
metadata:
  author: desktop client team
```

### metadata.category

标注该 skill 的工作形态，用于跨插件横向检索（与插件归属的领域分类正交，插件回答"属于哪个业务领域"，category 回答"是什么形状的工作"）。可选字段，取值：

| 取值 | 适用场景 |
|---|---|
| workflow | 流程编排类（多阶段、pipeline、交接式工作流） |
| quality | 质量保障类（review、评分、一致性校验、性能诊断） |
| generator | 代码/文档生成类（创建 PRD、代码、测试用例、报告等产物） |
| tool | 工具类（格式转换、数据同步、CI 触发、脚本初始化等） |
| platform | 平台专项类（如未来出现 android/ios/harmony 专属 skill） |

### compatibility

一句话描述运行环境依赖（≤500字符），必须基于该 skill 实际用到的工具/依赖据实填写，不得凭空编造。常见依赖类型：语言运行时（Python/Node.js/.NET SDK）、第三方 CLI（lark-cli、JMeter）、MCP server——引用 MCP server 时须注明是本仓库 `plugins/optimus-mcp-servers/.mcp.json` 内置（如 `mastergo-magic-mcp`、`FeishuProjectMcp`）还是需要用户自行配置（如 Figma/Sketch/Chrome DevTools MCP）。

### allowed-tools

空格分隔的预授权工具列表，必须基于该 skill 实际调用的工具据实填写：
- Claude Code 内置工具写原名（如 `Read Write Bash Grep Glob WebFetch TodoWrite Task`）
- MCP 工具只写 server 命名空间，不精确到具体工具全名，避免 MCP server 改名/升级后 allowed-tools 跟着失效
- 会派发子代理或调用其他 skill 的技能必须包含 `Task`

```yaml
---
name: my-skill
description: ...
metadata:
  version: "1.2.0"
  author: desktop client team
  category: workflow
compatibility: 需要 Node.js 环境及已配置的 XXX MCP server。
allowed-tools: Read Write Bash Task
---
```

### 编辑铁律：禁止无关格式化

编辑 SKILL.md / CHANGELOG.md / AGENT.md 时，只改动语义相关的内容，不增删空行、不调整缩进、不做表格对齐等纯格式化改动。仓库已配置 `.prettierignore`（排除 `*.md`）和 `.vscode/settings.json`（禁用 markdown 自动格式化）作为防护，但仍需自查：提交前看 `git diff`，若出现大片纯空白/缩进变化而无实际内容变化，说明格式化工具介入了，应撤销重做。

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
