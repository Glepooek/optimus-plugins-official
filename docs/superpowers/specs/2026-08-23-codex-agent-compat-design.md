# Codex CLI 兼容适配设计

> 日期：2026-08-23
> 范围：全仓库适配 OpenAI Codex CLI（0.149.0），含 Codex plugin marketplace 安装支持
> 决策：方案 A（同目录增补，SKILL.md 零改动）｜版本 Major 12.0.0

---

## 1. 背景与目标

本仓库是一个 Claude Code 插件仓库，8 个领域插件、36 个 skill，采用开放 Agent Skills 规范（agentskills.io 六字段 frontmatter）。现有 `.kiro/skills/` 符号链接镜像机制已把维护型 skill 暴露给 Kiro harness（一源多 harness）。

**目标**：让 OpenAI Codex CLI 能通过 plugin marketplace 安装并消费这些插件技能，同时**不破坏任何 Claude 侧现状**。

**核心不变式**：`SKILL.md` 一个字节都不改（Claude 的 source of truth）。Codex 端全部用**新增的适配文件**表达，与 `.kiro/` 镜像哲学一致。

---

## 2. 已实测确认的技术前提（pilot 结论）

用真实 `codex 0.149.0`（本机）在隔离 `CODEX_HOME` 下完成两轮 pilot，结论：

| # | 结论 | 证据 | 影响 |
|---|---|---|---|
| 1 | Codex 从 `<仓库根>/.agents/plugins/marketplace.json` 读取 marketplace | `codex plugin marketplace add <root>` 命中该文件 | 安装入口位置确定 |
| 2 | marketplace.json `source.path` 相对**仓库根**解析（`./plugins/optimus-*`），非 `.agents/plugins/` | 被解析为 `<root>/plugins/pilot-fe` 绝对路径 | 插件路径写法确定 |
| 3 | 安装策略枚举 `INSTALLED_BY_DEFAULT`/`AVAILABLE` 有效；`authentication` 枚举是 **`ON_INSTALL`/`ON_USE`**（文档写的 `ON_FIRST_USE` **报错**） | `unknown variant ON_FIRST_USE` 报错 → 改 `ON_USE` 成功 | 采用 `AVAILABLE`+`ON_USE` |
| 4 | 安装命令是 **`codex plugin add <plugin>@<marketplace>`**（文档写的 `plugin install` 是本版本不存在） | `plugin install` → `unrecognized subcommand` | 文档命令用对版本 |
| 5 | SKILL.md 顶层字段（`metadata`/`compatibility`/`allowed-tools`）被 codex **原样接受并缓存**，无 frontmatter 报错 | 缓存中 SKILL.md 完整保留 | 无需剥离字段（方案 A 成立） |
| 6 | `agents/openai.yaml` **非必需**——codex 仅凭 SKILL.md `name`+`description` 即可加载进 skill inventory | 无 `openai.yaml` 的 pilot-min 仍出现在 Available skills | **砍掉 36 个 yaml 生成** |
| 7 | skill 自动带插件前缀（`pilot-fe:pilot-analyzer`） | Available skills 列表 | 跨插件重名被前缀隔离，安全 |
| 8 | `AGENTS.md` 会被 codex 读取进模型输入 | `<AGENTS.md instructions for ...>` | 项目规则入口确定 |
| 9 | codex 也读 `~/.agents/skills/`（跨工具共享位置） | 列表出现用户 darwin-skill/find-skills | 维护型 skill 暴露路径可选 |

**清理**：两轮 pilot 临时目录（`optimus-codex-pilot*`、`.optimus-codex-pilot*-home`）均已删除，未污染用户 `~/.codex/`。

---

## 3. 设计

### 交付物全景

```
optimus-plugins-official/
├── README.md                                ← ⑤ 完善（codex 安装/使用）
├── AGENTS.md                                ← ① 真源（CLAUDE.md 全文迁入）
├── CLAUDE.md                                ← ①→改为 @AGENTS.md 引用层
├── .agents/
│   ├── plugins/marketplace.json             ← ②
│   └── skills/<name> -> ../../.claude/skills/<name>  ← ④ 符号链接
└── plugins/optimus-<domain>/
    └── .codex-plugin/plugin.json            ← ③ × 8
```

### 交付物 ① `AGENTS.md`（仓库根，真源）+ `CLAUDE.md`（引用层）

**原则：消除双份漂移，AGENTS.md 为唯一权威真源。** codex 原生读 `<git-root>/AGENTS.md` 全文；Claude Code 读 `CLAUDE.md`，经 `@AGENTS.md` 引用拉到同样内容。

**`AGENTS.md`**（承载原 `CLAUDE.md` 全部内容，全部原样迁入，逐条不省略）：
- 仓库概览、两层 skill 区分、重要约束、开发规范、本地测试、版本管理规则表、Skill frontmatter 规范、提交与推送、关键文件
- **追加 codex 适配对照说明**：
  - 提交补充：codex 无 `/commit-cc-plugin`，用标准 git 工作流 + Conventional Commits（`type(scope): subject`）提交，禁止 `--no-verify` 绕过 hook
  - hooks 说明：codex 侧无 SessionStart/Notification，MCP 经 `plugin.json` 的 `mcpServers` 暴露
  - Codex 侧安装入口指引（指向 `.agents/plugins/marketplace.json`）

**`CLAUDE.md`**（改为引用层，去重）：
- 正文替换为 `@AGENTS.md` 相对引用，Claude Code 读取时内联拉取 AGENTS.md 全文
- 除引用外尽量保持零内容（如需 Claude 侧专属增强，仅追加在引用之后，不复制正文）
- ⚠️ 实施时验证：确认 Claude Code 的 `@` import 生效（预期为内建支持）

### 交付物 ② `.agents/plugins/marketplace.json`（仓库根）

```json
{
  "name": "optimus-plugins-official",
  "interface": { "displayName": "Optimus 官方插件" },
  "plugins": [
    { "name": "optimus-frontend-plugin",
      "source": { "source": "local", "path": "./plugins/optimus-frontend-plugin" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "Frontend" },
    // ... 8 个，见 3.1 分类表
  ]
}
```
- `policy.installation` = `AVAILABLE`（用户 `codex plugin add` 手动装，不自动强装）
- `policy.authentication` = `ON_USE`（0.149.0 实测合法枚举）
- 安装：`codex plugin marketplace add Glepooek/optimus-plugins-official` → `codex plugin add optimus-<domain>@optimus-plugins-official`

### 交付物 ③ 每插件 `.codex-plugin/plugin.json`（8 份）

通用模板：
```json
{
  "name": "<plugin-name>",
  "version": "12.0.0",
  "description": "<抄 marketplace.json 对应 description>",
  "skills": "./skills/",
  "author": "optimus",
  "repository": "https://github.com/Glepooek/optimus-plugins-official"
}
```
**特判** `plugins/optimus-mcp-servers/`（无 `skills/`）：省略 `skills` 字段，改：
```json
{
  "name": "optimus-mcp-servers",
  "version": "12.0.0",
  "description": "MCP 服务器集成：GitHub Copilot、MasterGo、飞书项目",
  "mcpServers": "./.mcp.json",
  "author": "optimus"
}
```
> ⚠️ `mcpServers` 字段在 0.149.0 的生效行为实施时需实例验证（pilot 未覆盖）。

### 交付物 ④ `.agents/skills/` 维护型 skill 符号链接（对齐 kiro）

在仓库 `.agents/skills/` 建立指向 `.claude/skills/` 的符号链接，暴露维护型 skill 给 codex（codex 会读仓库级 `.agents/skills/`）。清单对齐现有 `.kiro/skills/`：
```
commit-cc-plugin
knowledge-base-maintain
record-tools
sync-cc-docs-to-youdaonote
sync-cc-tips
test-locally
```
> 不含 `darwin-skill`（被 `.gitignore` 排除，与 `.kiro/skills/` 一致）。
> 需扩展 `commit-cc-plugin` 的自动补齐逻辑，使其维护 `.agents/skills/` 镜像（当前仅维护 `.kiro/skills/`）。

### 交付物 ⑤ `README.md`（仓库根，完善）

从"Claude Code 单 harness"升级为"双 harness"文档门面：
- 标题/简介：Claude Code + Codex 双 harness 插件仓库
- **新增 Codex 安装章节**：
  ```bash
  codex plugin marketplace add Glepooek/optimus-plugins-official
  codex plugin add optimus-frontend-plugin@optimus-plugins-official
  ```
- **使用插件章节补充 Codex 调用方式**：自然语言触发 skill 描述，或 `@plugin:skill` 显式调用
- 保留插件列表、外部依赖、Claude 安装方式（`/plugin marketplace add`）

### 3.1 marketplace.json 插件 category 分类表

| 插件 | category | 说明 |
|---|---|---|
| optimus-frontend-plugin | Frontend | WPF 前端工具集 |
| optimus-backend-plugin | Backend | 后端开发工具集 |
| optimus-qa-plugin | QA | 测试 QA 工具集 |
| optimus-prd-plugin | Product | PRD 管理 |
| optimus-office-plugin | Productivity | Office 文档处理 |
| optimus-devops-plugin | DevOps | CI/CD、周报、agent skills |
| optimus-mcp-servers | MCP | 仅 MCP，无 skills |
| optimus-media-plugin | Media | 音视频处理 |

---

## 4. 版本管理

- `.claude-plugin/marketplace.json`：`11.1.1` → **`12.0.0`**（Major，全仓库适配里程碑）
- 8 个 `.codex-plugin/plugin.json` 的 `version` 同步为 `12.0.0`
- 仓库级 `AGENTS.md` 版本不上架，随仓库提交

---

## 5. 边界与错误处理

| 场景 | 处理 |
|---|---|
| `optimus-mcp-servers` 无 skills | plugin.json 省略 `skills`，用 `mcpServers` 指向 `.mcp.json` |
| 跨插件 skill 重名 | Codex 自动加 `plugin:` 前缀，天然隔离，无需处理 |
| Claude hooks（SessionStart/Notification） | Codex 无对应机制，不硬塞；AGENTS.md 注明 |
| 项目 `.agents/` 与用户 `~/.agents/` | 并存；项目级优先，互不干扰 |
| 重复添加 marketplace | `codex plugin marketplace add` 幂等（`alreadyAdded`），无需特判 |

---

## 6. 测试策略

### Codex 冒烟（主要验收）
1. `codex plugin marketplace add <本仓库路径>`（本地路径验证）
2. `codex plugin list --available --json` → 确认 8 插件齐全
3. 逐个 `codex plugin add optimus-<domain>@optimus-plugins-official` → `enabled: true`
4. `codex debug prompt-input "<触发语>"` → 确认各插件代表性 skill 出现在 Available skills 列表
5. 抽查 1-2 个含顶层字段的 skill（如 `wpf-code-review`）→ 无 frontmatter 报错

### Claude 侧回归
- `git diff` 确认 `plugins/*/skills/*/SKILL.md` 无改动
- 既有 skill 单元测试（`test-locally`）不受影响

### 校验 skill（可选）
一个轻量校验（纯脚本或 skill）：确认每插件有 `.codex-plugin/plugin.json`、marketplace `plugins[]` 引用与插件目录一致、无 skill 重名冲突。

---

## 7. 非目标（YAGNI）

- **不做** `agents/openai.yaml` 生成（已证实非必需，pilot 第 6 条）
- **不做** 36 个 skill 的元数据生成脚本（无生成需求）
- **不做** 剥离 SKILL.md 顶层字段（方案 B 已否）——保留 Claude 权限模型
- **不做** 独立的 skill 副本（方案 C 已否，违反单一 source）
- **不做** codex 侧提交 skill（用户定"仅文字约束"）
- **不做** hooks 的 codex 等价物（Codex 无此机制）
