# sync-skill-symlinks 改名与 Codex 集成设计

> 日期：2026-08-30
> 范围：`plugins/optimus-devops-plugin/skills/sync-agent-skills/` 改名为 `sync-skill-symlinks`，补充 Codex CLI 全局 skills 目录支持
> 决策：改名（用户确认）｜保留在 optimus-devops-plugin 下（用户确认）｜Codex target 采用 `~/.codex/skills/`（用户机器实测目录结构确认）｜版本 Major 13.0.0（用户确认）
>
> **修订记录**：本文档曾在草拟阶段误判 Codex target 应为 `~/.agents/skills/`（依据仓库内一份隔离 `CODEX_HOME` pilot 环境下的历史记录），并因此设计了一套"target 与 source 同路径"的自环防护逻辑。用户直接在其真实机器上核实 `~/.codex/skills/` 确实存在且已有实质内容（Codex 内置 `.system/` 系统 skill 集 + 用户手动创建的指向 `~/.agents/skills/` 的符号链接），纠正了这一误判。现依此修订：Codex target 为 `~/.codex/skills/`，自环防护逻辑作废（该 target 与默认 source `~/.agents/skills/` 是两个不同路径，不存在自环）。

---

## 1. 背景

### 1.1 命名歧义

`sync-agent-skills` 的名字容易与仓库中随处出现的「Agent Skills 规范」（agentskills.io，SKILL.md 六字段 frontmatter 的官方名称）混淆——读者第一反应可能理解为"同步 Agent Skills 规范内容"，但实际语义是"把一个 skill 源目录以符号链接分发到多个 AI 工具的全局 skills 目录"，纯文件系统操作，与规范本身无关。用户确认改名为 `sync-skill-symlinks`。

### 1.2 分类归属

该 skill 操作对象是用户 home 目录下的 AI 工具全局配置，语义上更接近"AI 工具个人环境搭建"而非传统 DevOps（CI/CD/部署）。但当前 8 个领域插件中没有更贴切的归类，且 `optimus-devops-plugin` 的 marketplace description 已显式列出"skill 链接同步"这一职责（说明当初是刻意放置）。用户确认**保留**在 `optimus-devops-plugin` 下，不新建插件、不迁移。

### 1.3 Codex 集成依据

用户在其真实机器上直接核实：`~/.codex/skills/` 目录真实存在且已有实质内容——
- `~/.codex/skills/.system/` 下有 Codex 内置的系统 skill 集（`imagegen`、`openai-docs`、`plugin-creator`、`review-agent`、`skill-creator`、`skill-installer`），带 `.codex-system-skills.marker` 标记文件；
- 用户此前已手动创建三个符号链接（`darwin-skill`、`youdaonote-llm-wiki`、`youdaonote-skill`），均指向 `~/.agents/skills/<name>`——即用户已经在手工做"从 Codex 全局目录桥接到 `.agents/skills/` 源"的事，这正是本 skill 应该自动化的场景。

这证实 **`~/.codex/skills/` 是 Codex CLI 真实读取的全局 skills 目录**，而非仓库内 `docs/superpowers/specs/2026-08-23-codex-agent-compat-design.md` 第33行记录的 `~/.agents/skills/`（该记录来自一次隔离 `CODEX_HOME` 环境下的 pilot，可能与真实机器上 Codex 固定使用 `~/.codex/` 作为自身数据目录的行为不一致——真实机器上的直接观测优先于隔离 pilot 记录）。

**设计结论**：把 `~/.codex/skills/` 补进默认 **targets** 数组，与 `~/.claude/skills/`、`~/.kiro/skills/` 并列，作为普通新增 target 处理——它与默认 source `~/.agents/skills/` 是两个不同路径，不需要任何自环防护或特殊拓扑。

---

## 2. 设计

### 2.1 新增默认 target

默认 `targets` 数组从两项扩展为三项：`~/.claude/skills/`、`~/.kiro/skills/`、`~/.codex/skills/`（新增，覆盖 Codex 场景）。三者与默认 source `~/.agents/skills/` 均为不同路径，按现有 Step 3 逻辑（新建/更新/跳过/警告）直接处理即可，无需额外分支。

### 2.2 改名影响面

`sync-agent-skills` → `sync-skill-symlinks`，涉及：
- 目录名（`git mv`）
- SKILL.md frontmatter `name` 字段
- SKILL.md description 中的触发词列表（含旧名 `sync-agent-skills` 作为触发词之一——不保留兼容别名，用户已确认按仓库规则走 Major）
- SKILL.md 正文中所有提及技能名的地方（标题、全局使用说明章节）
- CHANGELOG.md
- `.kiro/steering/plugins.md` 中该 skill 的清单条目

**不改动**范围：历史 spec/plan 文档（`docs/superpowers/specs/2026-06-28-*`、`2026-06-30-*` 及对应 plans）——按 AGENTS.md 的 docs 定位划分，这些是"记录当时为什么这么设计"的历史决策记录，不回填新决策，避免破坏历史可追溯性。

### 2.3 版本影响

按 `AGENTS.md` 版本管理规则与 `.claude/rules/skill-conventions.md` 的 metadata.version 规则：
- 改名 = 重命名用户可见功能 = **Major**；新增 Codex target = 新增功能 = Minor。两者取最强 → Major。
- 仓库整体版本（`.claude-plugin/marketplace.json`）：`12.3.3` → `13.0.0`（用户已确认）。
- `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` 的 version 同步为 `13.0.0`。
- Skill 自身 `metadata.version`（与仓库版本号分开管理）：`1.2.0` → `2.0.0`。

---

## 3. 不在范围内

- 不支持保留旧名 `sync-agent-skills` 作为别名或兼容触发词。
- 不迁移插件归属，不新建插件。
- 不回填历史 spec/plan 文档。
- 不强制运行 darwin-skill 自动优化（`AGENTS.md` 原文为"建议"而非强制；是否运行留给实施阶段征询用户）。
