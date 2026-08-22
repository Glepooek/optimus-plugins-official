# Codex CLI 兼容适配 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 OpenAI Codex CLI（0.149.0）通过 plugin marketplace 安装并消费本仓库 8 个插件技能，同时不破坏 Claude 侧现状。

**Architecture:** 方案 A（同目录增补）。SKILL.md 一字不改（Claude 单一 source of truth），Codex 端全部用新增适配文件表达：`AGENTS.md` 做真源（CLAUDE.md 全文迁入 + codex 对照段）、`CLAUDE.md` 改 `@AGENTS.md` 引用层、`.agents/plugins/marketplace.json`（安装入口）、8× `.codex-plugin/plugin.json`（插件标识）、`.agents/skills/*`（维护型 skill 符号链接镜像）、README 双向 harness 完善。版本同步升 Major 12.0.0。

**Tech Stack:** 无新增运行时依赖。文件为 JSON/YAML/Markdown + 符号链接。验证用 `codex` CLI（本机 0.149.0）+ git。

**Spec:** `docs/superpowers/specs/2026-08-23-codex-agent-compat-design.md`

## Global Constraints

- **提交必须用 `commit-cc-plugin` skill**（仓库强制，禁止手动 git / `--no-verify` / force push）。
- **SKILL.md 一个字节都不改**——任何任务不得触碰 `plugins/*/skills/*/SKILL.md`。
- 版本升级：`.claude-plugin/marketplace.json` `11.1.1` → **`12.0.0`**；8 个 `.codex-plugin/plugin.json` 的 `version` 同步为 `12.0.0`。（首个含 `plugins/` 变更的提交必须带上版本升级，不得延后。）
- 符号链接目标用仓库内相对路径（与 `.kiro/skills/` 一致）；`git config core.symlinks` 已为 `true`。
- `marketplace.json` 的 `policy`：`installation`=`AVAILABLE`、`authentication`=`ON_USE`（codex 0.149.0 实测合法枚举）。
- 文件内凡复制 `marketplace.json` 的 description，以 `plugins/optimus-*` 各自 description 为准，不得增删内容。
- 所有新增文件使用 UTF-8、不引入 BOM；Markdown 不做格式化对齐改动（仓库 `.prettierignore` 排除 `*.md`）。

---

## 文件结构总览

| 文件 | 动作 | 职责 |
|---|---|---|
| `AGENTS.md` | Create | Codex 真源：CLAUDE.md 全文 + Codex 兼容说明段 |
| `CLAUDE.md` | Modify | 改为 `@AGENTS.md` 引用层，去重 |
| `.agents/plugins/marketplace.json` | Create | 8 插件安装入口 |
| `plugins/optimus-*/.codex-plugin/plugin.json` | Create ×8 | 每插件 Codex 标识（mcp-servers 特判） |
| `.agents/skills/<name>` | Create ×6 | 维护型 skill 符号链接镜像 |
| `.claude/skills/commit-cc-plugin/SKILL.md` | Modify | 扩展补齐逻辑到 `.agents/skills/` |
| `README.md` | Modify | 双 harness 门面 |
| `.claude-plugin/marketplace.json` | Modify | 版本升 12.0.0 |

---

### Task 1: 创建 AGENTS.md（真源）

**Files:**
- Create: `AGENTS.md`

**Interfaces:**
- Consumes: `CLAUDE.md`（现有全文）
- Produces: `AGENTS.md`（Codex 真源，Task 2 的 `CLAUDE.md` 引用它）

- [ ] **Step 1: 复制 CLAUDE.md 全文为 AGENTS.md**

把现有 `CLAUDE.md` 的全部内容逐字复制到 `AGENTS.md`（标题从 `# CLAUDE.md` 改为 `# AGENTS.md`），包括：仓库概览（两层 skill 表）、重要约束、开发规范、本地测试、版本管理规则表、Skill frontmatter 规范、提交与推送、关键文件。**一字不删，只改标题。**

- [ ] **Step 2: 在 AGENTS.md 末尾追加"Codex CLI 兼容说明"段**

在文档末尾新增（`## 提交与推送（强制）` 一节之后）粘贴以下完整段落：

```markdown
## Codex CLI 兼容说明

本仓库同时支持 Claude Code 与 OpenAI Codex 双 harness。Codex 侧通过 `.agents/plugins/marketplace.json` 安装插件：

```bash
codex plugin marketplace add Glepooek/optimus-plugins-official
codex plugin add optimus-frontend-plugin@optimus-plugins-official   # 逐个按需安装
```

Codex 与 Claude 在本仓库的约定差异：

- **提交**：Claude Code 用 `/commit-cc-plugin` skill；Codex 无此 skill，改用标准 git 工作流 + Conventional Commits（`type(scope): subject`），禁止 `--no-verify` 绕过 hook。
- **Hooks**：Claude 侧有 SessionStart（技巧轮播）/Notification；Codex 无对应 hooks 机制，这些在 Codex 侧不生效。
- **MCP**：各插件通过 `.codex-plugin/plugin.json` 的 `mcpServers` 字段暴露（见 `plugins/optimus-mcp-servers/.mcp.json`）。
- **两层 skill**：`plugins/*/skills/` 为对外发布产物；`.claude/skills/` 为本仓库维护自用，经 `.agents/skills/` 符号链接暴露给 Codex。
```

- [ ] **Step 3: 验证结构**

Run: `grep -c "Codex CLI 兼容说明" AGENTS.md && head -1 AGENTS.md`
Expected: `1`（codex 段存在）且首行为 `# AGENTS.md`

- [ ] **Step 4: 提交（用 commit-cc-plugin）**

`git add AGENTS.md`，调用 commit-cc-plugin 提交，commit `docs(codex-compat): 迁移 CLAUDE.md 为 AGENTS.md 真源`。

---

### Task 2: CLAUDE.md 改为引用层

**Files:**
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: `AGENTS.md`（Task 1）
- Produces: 引用层 CLAUDE.md

> ⚠️ 本任务改为引用后，Claude Code 需依赖 `@` import 支持（预期内建）。执行时先确认 Claude Code 版本支持，若拒绝引用则回退为"CLAUDE.md 保留全文 + AGENTS.md 冗余"方案并上报。

- [ ] **Step 1: 替换 CLAUDE.md 正文为引用**

将 `CLAUDE.md` 的全部正文替换为仅一行引用：

```markdown
@AGENTS.md
```

（`@AGENTS.md` 为相对引用，Claude Code 读取时内联拉取仓库根 `AGENTS.md` 全文。若需保留 Claude 侧专属附加内容，可在该行之后追加，但不得重复正文。）

- [ ] **Step 2: 验证**

Run: `cat CLAUDE.md`
Expected: 内容仅 `@AGENTS.md` 一行（及可选追加行）

- [ ] **Step 3: 提交（用 commit-cc-plugin）**

`git add CLAUDE.md`，调用 commit-cc-plugin 提交，commit `docs(codex-compat): CLAUDE.md 改为引用 AGENTS.md 去重`。

---

### Task 3: 创建 .agents/plugins/marketplace.json

**Files:**
- Create: `.agents/plugins/marketplace.json`

**Interfaces:**
- Consumes: `plugins/optimus-*/`（路径）
- Produces: marketplace.json（Task 4 依赖其 `source.path` 语义）

- [ ] **Step 1: 写入完整 marketplace.json**

创建 `.agents/plugins/marketplace.json`，粘贴以下内容（8 插件，`AVAILABLE`/`ON_USE`）：

```json
{
  "name": "optimus-plugins-official",
  "interface": { "displayName": "Optimus 官方插件" },
  "plugins": [
    {
      "name": "optimus-frontend-plugin",
      "source": { "source": "local", "path": "./plugins/optimus-frontend-plugin" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "Frontend"
    },
    {
      "name": "optimus-backend-plugin",
      "source": { "source": "local", "path": "./plugins/optimus-backend-plugin" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "Backend"
    },
    {
      "name": "optimus-qa-plugin",
      "source": { "source": "local", "path": "./plugins/optimus-qa-plugin" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "QA"
    },
    {
      "name": "optimus-prd-plugin",
      "source": { "source": "local", "path": "./plugins/optimus-prd-plugin" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "Product"
    },
    {
      "name": "optimus-office-plugin",
      "source": { "source": "local", "path": "./plugins/optimus-office-plugin" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "Productivity"
    },
    {
      "name": "optimus-devops-plugin",
      "source": { "source": "local", "path": "./plugins/optimus-devops-plugin" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "DevOps"
    },
    {
      "name": "optimus-mcp-servers",
      "source": { "source": "local", "path": "./plugins/optimus-mcp-servers" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "MCP"
    },
    {
      "name": "optimus-media-plugin",
      "source": { "source": "local", "path": "./plugins/optimus-media-plugin" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "Media"
    }
  ]
}
```

- [ ] **Step 2: 用 codex 验证 marketplace 能被识别**

Run（隔离 CODEX_HOME 到临时目录，避免污染 `~/.codex/`）:
```
codex plugin marketplace add "$PWD" --json
```
Expected: 输出 `"marketplaceName": "optimus-plugins-official"`，无报错。

- [ ] **Step 3: 提交（用 commit-cc-plugin）**

`git add .agents/plugins/marketplace.json`，调用 commit-cc-plugin 提交，commit `feat(codex-compat): 新增 Codex marketplace 安装入口`。

---

### Task 4: 创建 8× .codex-plugin/plugin.json 并升版本

**Files:**
- Create ×8: `plugins/optimus-*/.codex-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`（version `11.1.1` → `12.0.0`）

**Interfaces:**
- Consumes: 各插件 `plugins/optimus-*/skills/`（skills 路径）
- Produces: 各插件 plugin.json（Task 8 冒烟依赖）

> ⚠️ 首次触及 `plugins/` 下新增能力，必须在此提交同步升 `marketplace.json` 版本到 `12.0.0`（不延后）。

- [ ] **Step 1: 建 7 个有 skills 的插件 plugin.json**

对以下插件各创建 `plugins/<domain>/.codex-plugin/plugin.json`，`description` 从 `.claude-plugin/marketplace.json` 对应插件 description 逐字复制：

- `optimus-frontend-plugin`（7 skills）
- `optimus-backend-plugin`（3 skills）
- `optimus-qa-plugin`（7 skills）
- `optimus-prd-plugin`（3 skills）
- `optimus-office-plugin`（6 skills）
- `optimus-devops-plugin`（4 skills）
- `optimus-media-plugin`（9 skills）

模板（`<description>` 换成该插件 description）：

```json
{
  "name": "optimus-<domain>",
  "version": "12.0.0",
  "description": "<markeplace.json 对应插件 description>",
  "skills": "./skills/",
  "author": "optimus",
  "repository": "https://github.com/Glepooek/optimus-plugins-official"
}
```

- [ ] **Step 2: 建 optimus-mcp-servers 的 plugin.json（特判：无 skills）**

`plugins/optimus-mcp-servers/.codex-plugin/plugin.json`，省略 `skills`，改用 `mcpServers`：

```json
{
  "name": "optimus-mcp-servers",
  "version": "12.0.0",
  "description": "MCP 服务器集成：GitHub Copilot MCP、MasterGo 设计协作、飞书项目等企业级 MCP 服务",
  "mcpServers": "./.mcp.json",
  "author": "optimus"
}
```

- [ ] **Step 3: 升 marketplace.json 版本**

在 `.claude-plugin/marketplace.json` 修改 `"version": "11.1.1"` → `"version": "12.0.0"`。

- [ ] **Step 4: 用 codex 验证 8 插件被列出**

Run（隔离 CODEX_HOME）:
```
codex plugin marketplace add "$PWD" --json
codex plugin list --available --json
```
Expected: `available` 数组含全部 8 个 `pluginId`（`optimus-*@optimus-plugins-official`），每个 `installPolicy` 为 `AVAILABLE`。

- [ ] **Step 5: 提交（用 commit-cc-plugin）**

`git add plugins/*/.codex-plugin/plugin.json .claude-plugin/marketplace.json`，调用 commit-cc-plugin 提交，commit `feat(codex-compat): 为 8 插件添加 Codex plugin 清单并升版本至 12.0.0`。

---

### Task 5: .agents/skills 符号链接 + commit-cc-plugin 扩展

**Files:**
- Create ×6: `.agents/skills/<name>`（符号链接）
- Modify: `.claude/skills/commit-cc-plugin/SKILL.md`（扩展补齐逻辑 + CHANGELOG.md + metadata.version）

**Interfaces:**
- Consumes: `.claude/skills/<name>`（源目录）
- Produces: `.agents/skills/<name>` 符号链接（codex 侧暴露维护型 skill）

- [ ] **Step 1: 建 6 个符号链接**

对下列 skill 建立 `.agents/skills/<name>` → `../../.claude/skills/<name>`（仓库内相对路径，与 `.kiro/skills/` 一致）：

`commit-cc-plugin`, `knowledge-base-maintain`, `record-tools`, `sync-cc-docs-to-youdaonote`, `sync-cc-tips`, `test-locally`（不含被 gitignore 的 `darwin-skill`）

```bash
# Windows（PowerShell）
New-Item -ItemType SymbolicLink -Path ".agents/skills/<name>" -Target "..\..\.claude\skills\<name>"
```

- [ ] **Step 2: 确认符号链接以 symlink blob 入库**

Run: `git ls-files -s .agents/skills/<name>`
Expected: mode 为 `120000`（不是 `100644`）。

- [ ] **Step 3: 扩展 commit-cc-plugin 的补齐逻辑**

在 `.claude/skills/commit-cc-plugin/SKILL.md` 的"第二步 — 补齐 .kiro/skills 符号链接"中：对照 `.claude/skills/` 检查缺失时，**同时**维护 `.agents/skills/<name>`（目标 `..\..\.claude\skills\<name>`），逻辑与 `.kiro/skills/` 相同。更新 CHANGELOG.md（Patch）与 `metadata.version`（x.x.X +1）。修改 commit-cc-plugin 的 `description` 触发词不必要。

- [ ] **Step 4: 验证**

Run: `git ls-files -s .agents/skills/ | grep -c 120000`
Expected: `6`（6 个 symlink）。

- [ ] **Step 5: 提交（用 commit-cc-plugin）**

`git add .agents/skills/<name> .claude/skills/commit-cc-plugin/SKILL.md .claude/skills/commit-cc-plugin/CHANGELOG.md`，调用 commit-cc-plugin 提交，commit `feat(codex-compat): 新增维护型 skill 的 codex 符号链接镜像并扩展补齐逻辑`。

---

### Task 6: README.md 双 harness

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 标题与简介改双 harness**

`READMEmd` 首行 `# Claude Code 插件仓库` → `# Claude Code + Codex 插件仓库`，简介补充"同时支持 Claude Code 与 OpenAI Codex 双 harness"。

- [ ] **Step 2: 新增 Codex 安装章节**

在"🚀 快速开始"的 Claude 安装方式之后，追加：

```markdown
### Codex 安装

前提：已安装 [OpenAI Codex CLI](https://github.com/openai/codex)。

```bash
# 添加本仓库为 marketplace
codex plugin marketplace add Glepooek/optimus-plugins-official

# 安装所需插件（逐个）
codex plugin add optimus-frontend-plugin@optimus-plugins-official
codex plugin add optimus-devops-plugin@optimus-plugins-official
```

### Codex 使用

在 Codex 会话中用自然语言描述任务，Codex 依技能 description 自动触发；或显式 `@plugin:skill` 调用（如 `@optimus-frontend-plugin:wpf-code-review`）。注意：Claude 侧 hooks（SessionStart 技巧轮播、Notification）在 Codex 中不生效。
```

- [ ] **Step 3: 验证**

Run: `grep -c "Codex 安装" README.md`
Expected: `1`。

- [ ] **Step 4: 提交（用 commit-cc-plugin）**

`git add README.md`，调用 commit-cc-plugin 提交，commit `docs(codex-compat): README 完善为双 harness 门面`。

---

### Task 7: 全量 Codex 冒烟

**Files:**
- （无源码改动，仅验证）

- [ ] **Step 1: 隔离环境逐个安装并验证 inventory**

Run（隔离 CODEX_HOME）:
```bash
for p in optimus-frontend-plugin optimus-backend-plugin optimus-qa-plugin optimus-prd-plugin optimus-office-plugin optimus-devops-plugin optimus-media-plugin; do
  codex plugin add "$p@optimus-plugins-official" --json
done
codex debug prompt-input "请用 mastergo-to-wpf-page 和 csharp-code-review 分析" 2>&1 | grep -E "optimus-[a-z-]+:[a-z-]+"
```
Expected: 各插件代表性 skill 以 `plugin:skill` 形式出现于 Available skills，无 frontmatter 报错（如 `optimus-frontend-plugin:mastergo-to-wpf-page`、`optimus-backend-plugin:csharp-code-review`）。

- [ ] **Step 2: 确认 SKILL.md 零改动**

Run: `git status --porcelain plugins/*/skills/`
Expected: 无输出（所有 SKILL.md 未被修改）。

- [ ] **Step 3: 汇总报告**

向用户报告：8 插件可装入、代表 skill 可被 codex 识别、SKILL.md 零改动、frontmatter 无报错。

---

## 附：执行顺序与验收

1. Task 1-2（AGENTS.md 真源 + CLAUDE.md 引用）→ 交付规则层
2. Task 3-4（marketplace + 8 plugin.json + 版本 12.0.0）→ 交付安装层
3. Task 5（.agents/skills + 补齐逻辑）→ 交付维护型暴露
4. Task 6（README）→ 交付文档门面
5. Task 7（全量冒烟）→ 验收

每个任务末尾均用 `commit-cc-plugin` 提交（仓库强制）。全部完成后整体 `git pull --rebase && git push origin master`。
