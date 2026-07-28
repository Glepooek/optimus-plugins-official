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
compatibility: 需要 Node.js 环境及已配置的 XXX MCP server。
allowed-tools: Read Write Bash Task
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
