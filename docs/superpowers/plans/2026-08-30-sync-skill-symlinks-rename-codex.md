# sync-skill-symlinks 改名与 Codex 集成 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `sync-agent-skills` skill 改名为 `sync-skill-symlinks`（消除与 Agent Skills 规范的命名歧义），并补充对 Codex CLI 全局 skills 目录（`~/.codex/skills/`）的支持，同时同步升级仓库版本号。

**Architecture:** 目录级 `git mv` + SKILL.md 内容改写（frontmatter name/description/正文）+ CHANGELOG 追加 + `.kiro/steering/plugins.md` 索引更新 + 版本号三处同步升级（marketplace.json、devops-plugin 的 .codex-plugin/plugin.json、skill 自身 metadata.version）。核心改动是 Step 0/Step 3 的默认 targets 数组新增 `~/.codex/skills/`，与其他 target 同等对待，无需特殊逻辑。

**Tech Stack:** Markdown（SKILL.md/CHANGELOG.md）、JSON（marketplace.json/plugin.json）、PowerShell + Bash（脚本内容改动）

**Spec:** `docs/superpowers/specs/2026-08-30-sync-skill-symlinks-rename-codex-design.md`

## Global Constraints

- 改名不保留旧名 `sync-agent-skills` 作为兼容别名或触发词（用户已确认，按仓库规则走 Major）。
- 不新增未经实测/官方确认的路径——Codex target 固定为 `~/.codex/skills/`（用户机器直接实测确认：该目录下已有 Codex 内置 `.system/` 系统 skill 集与用户手动创建的指向 `~/.agents/skills/` 的符号链接）。
- 不迁移插件归属，skill 保留在 `plugins/optimus-devops-plugin/skills/` 下。
- 不回填历史 spec/plan 文档（`docs/superpowers/specs/2026-06-28-*`、`2026-06-30-*` 及对应 plans）。
- 版本号：仓库整体 `.claude-plugin/marketplace.json` `12.3.3` → `13.0.0`；`plugins/optimus-devops-plugin/.codex-plugin/plugin.json` 同步为 `13.0.0`；skill 自身 `metadata.version` `1.2.0` → `2.0.0`。
- 提交与推送必须使用 `commit-cc-plugin` skill，禁止手动 git 工作流（`AGENTS.md` 强制要求）。

---

### Task 1: 目录改名 + SKILL.md 全文重写

**Files:**
- Rename (via `git mv`): `plugins/optimus-devops-plugin/skills/sync-agent-skills/` → `plugins/optimus-devops-plugin/skills/sync-skill-symlinks/`
- Modify: `plugins/optimus-devops-plugin/skills/sync-skill-symlinks/SKILL.md`（原 `sync-agent-skills/SKILL.md` 全文，395行）

**Interfaces:**
- Consumes: 无上游任务
- Produces: 供 Task 2（CHANGELOG）、Task 3（索引更新）、Task 4（版本号）引用的新技能名 `sync-skill-symlinks`

**改动点清单（对照当前 `SKILL.md` 395 行内容逐项定位）：**

1. **Frontmatter（第1-10行）**：
   - `name: sync-agent-skills` → `name: sync-skill-symlinks`
   - `description` 字段：把开头的功能描述保持不变，触发词列表里的 `sync-agent-skills` 替换为 `sync-skill-symlinks`；同时在触发词列表追加 `link skill symlinks`（保持中英文触发词各一个新增，不用编造更多）。**不保留 `sync-agent-skills` 作为触发词**（按 Global Constraints）。
   - `metadata.version: "1.2.0"` → `"2.0.0"`

2. **标题（第12行）**：`# sync-agent-skills` → `# sync-skill-symlinks`

3. **Step 0 默认值（第27-29行 PowerShell / 第59-61行 Bash）**：
   ```powershell
   # 默认值
   $source    = "$env:USERPROFILE\.agents\skills"
   $targets   = @("$env:USERPROFILE\.claude\skills", "$env:USERPROFILE\.kiro\skills", "$env:USERPROFILE\.codex\skills")
   $useCustom = $false
   ```
   ```bash
   # 默认值
   source_dir="$HOME/.agents/skills"
   targets=("$HOME/.claude/skills" "$HOME/.kiro/skills" "$HOME/.codex/skills")
   use_custom=false
   ```

4. **Step 0 参数用法说明文本（第50-53行 / 第82-84行）**：不变（source=/target= 语法本身不受影响）。

5. **Step 3 标题下方说明文字（第208行）**：
   > 原文：`$targets` 由 Step 0 赋值（默认：\`~/.claude/skills/\` 和 \`~/.kiro/skills/\`）。对每个目标目录逐一处理：父目录不存在则静默跳过（默认 targets）；自动创建目标目录本身；链接不存在则新建，已存在但目标路径不符则自动更新，目标路径一致则跳过，非符号链接则警告。

   改为：
   > `$targets` 由 Step 0 赋值（默认：`~/.claude/skills/`、`~/.kiro/skills/`、`~/.codex/skills/`）。对每个目标目录逐一处理：父目录不存在则静默跳过（默认 targets）；自动创建目标目录本身；链接不存在则新建，已存在但目标路径不符则自动更新，目标路径一致则跳过，非符号链接则警告。

6. **Step 3 兜底赋值（第214-216行 PowerShell / 第260-262行 Bash）**：
   ```powershell
   if (-not $targets) {
       $targets = @("$env:USERPROFILE\.claude\skills", "$env:USERPROFILE\.kiro\skills", "$env:USERPROFILE\.codex\skills")
   }
   ```
   ```bash
   if [ ${#targets[@]} -eq 0 ]; then
       targets=("$HOME/.claude/skills" "$HOME/.kiro/skills" "$HOME/.codex/skills")
   fi
   ```

7. **Step 3 主循环**：无需改动——新增的 `~/.codex/skills/` target 与默认 source `~/.agents/skills/` 是不同路径，现有的新建/更新/跳过/警告分支已足够覆盖，不需要自环防护或任何额外逻辑。

8. **Step 5 汇总说明（第341-348行）**：不改动。

9. **⛔ 反例与黑名单表（第363-373行）**：本次改动不新增反例条目——Codex target 与其他 target 处理逻辑一致，没有引入新的误用场景。

10. **全局使用说明章节（第376-383行）**：把 `sync-agent-skills` 文字替换为 `sync-skill-symlinks`（含路径 `~/.agents/skills/sync-agent-skills/` → `~/.agents/skills/sync-skill-symlinks/`，以及"输入「同步 skills」"触发语句不变）。

- [ ] **Step 1: 执行目录改名**

```bash
git mv plugins/optimus-devops-plugin/skills/sync-agent-skills plugins/optimus-devops-plugin/skills/sync-skill-symlinks
```

- [ ] **Step 2: 按上述改动点清单 1-10，用 Edit 逐项修改 `plugins/optimus-devops-plugin/skills/sync-skill-symlinks/SKILL.md`**

逐条对照当前文件行号定位后编辑（改名后文件内容不变，仅路径变了，行号仍适用于改名前读到的内容）。

- [ ] **Step 3: 校验改动**

```bash
grep -n "sync-agent-skills" plugins/optimus-devops-plugin/skills/sync-skill-symlinks/SKILL.md
```
Expected: 无输出（全部替换完毕，除非刻意保留了指向历史 docs 的引用——本 skill 无此类引用，应为空结果）。

```bash
grep -n "codex.skills\|\.codex/skills" plugins/optimus-devops-plugin/skills/sync-skill-symlinks/SKILL.md
```
Expected: 命中 Step 0 默认 targets（2处 win/bash）、Step 3 默认 targets 数组（2处，含兜底）、Step 3 说明文字——确认 `~/.codex/skills/` 作为第三个 target 与 `~/.claude/skills/`、`~/.kiro/skills/` 并列出现。

- [ ] **Step 4: Commit（暂不推送，等所有 Task 完成后统一提交）**

本任务不单独提交，改动累积到 Task 5 统一走 `commit-cc-plugin`。

---

### Task 2: CHANGELOG.md 追加条目

**Files:**
- Modify: `plugins/optimus-devops-plugin/skills/sync-skill-symlinks/CHANGELOG.md`（Task 1 改名后路径）

**Interfaces:**
- Consumes: Task 1 产出的新目录路径
- Produces: 无（终端产物）

- [ ] **Step 1: 在文件顶部插入新版本条目**

在现有 `## [1.2.0] - 2026-06-30` 之前插入：

```markdown
## [2.0.0] - 2026-08-30

### Changed
- **Breaking**: skill 重命名 `sync-agent-skills` → `sync-skill-symlinks`，消除与 Agent Skills 规范（agentskills.io）的命名歧义；不保留旧名作为兼容触发词
- 默认 targets 新增 `~/.codex/skills/`（Codex CLI 数据目录下的全局 skills 目录，与 `~/.claude/skills/`、`~/.kiro/skills/` 并列；用户机器实测确认：`~/.codex/skills/` 下已存在 Codex 内置的 `.system/` 系统 skill 集，以及用户手动创建的指向 `~/.agents/skills/` 的符号链接，证实该路径是 Codex 真实读取的全局位置）

```

- [ ] **Step 2: 校验格式**

```bash
head -20 plugins/optimus-devops-plugin/skills/sync-skill-symlinks/CHANGELOG.md
```
Expected: 新条目位于最上方，格式与既有条目一致（`## [版本号] - YYYY-MM-DD` + `### Changed` 小节）。

---

### Task 3: `.kiro/steering/plugins.md` 索引更新

**Files:**
- Modify: `.kiro/steering/plugins.md:74`

**Interfaces:**
- Consumes: Task 1 产出的新技能名
- Produces: 无（终端产物）

- [ ] **Step 1: 替换索引条目**

当前第74行：
```
- `sync-agent-skills` — Agent Skills 同步
```

改为：
```
- `sync-skill-symlinks` — skill 目录符号链接同步（Claude/Kiro/Codex）
```

- [ ] **Step 2: 校验**

```bash
grep -n "sync-agent-skills\|sync-skill-symlinks" .kiro/steering/plugins.md
```
Expected: 只命中新名 `sync-skill-symlinks` 一处。

---

### Task 4: 版本号三处同步升级

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `plugins/optimus-devops-plugin/.codex-plugin/plugin.json`

**Interfaces:**
- Consumes: 无
- Produces: 无（终端产物，供提交时一并校验）

- [ ] **Step 1: 升级仓库整体版本号**

`.claude-plugin/marketplace.json` 第5行：`"version": "12.3.3"` → `"version": "13.0.0"`

- [ ] **Step 2: 同步 devops-plugin 的 Codex 清单版本号**

`plugins/optimus-devops-plugin/.codex-plugin/plugin.json` 第3行：`"version": "12.3.3"` → `"version": "13.0.0"`

同时该文件的 `description`（第4行）与 `interface.longDescription`（约第14行）已经是"skill 链接同步"的泛化措辞，未点名旧技能名，**无需改动**——用 Grep 确认一下：

```bash
grep -n "sync-agent-skills\|sync-skill-symlinks" plugins/optimus-devops-plugin/.codex-plugin/plugin.json
```
Expected: 无输出（该文件本就不点名具体 skill 名）。

- [ ] **Step 3: 校验两处版本号一致**

```bash
grep -n '"version"' .claude-plugin/marketplace.json plugins/optimus-devops-plugin/.codex-plugin/plugin.json
```
Expected: 两处均为 `13.0.0`。

---

### Task 5: 整体校验 + 提交推送

**Files:**
- 无新增/修改，仅校验 + 提交

**Interfaces:**
- Consumes: Task 1-4 全部产出
- Produces: 无

- [ ] **Step 1: 全仓搜索确认无遗留旧名引用（历史 docs 除外）**

```bash
grep -rln "sync-agent-skills" . --include="*.md" --include="*.json" 2>/dev/null | grep -v node_modules
```
Expected: 仅命中 `docs/superpowers/plans/2026-06-28-sync-agent-skills.md`、`docs/superpowers/plans/2026-06-30-sync-agent-skills-custom-paths.md`、`docs/superpowers/specs/2026-06-28-sync-agent-skills-design.md`、`docs/superpowers/specs/2026-06-30-sync-agent-skills-custom-paths-design.md` 这4份历史决策记录（按 Global Constraints 不回填）。若命中其他文件，回到对应 Task 补漏。

- [ ] **Step 2: 校验 SKILL.md frontmatter 合法性**

```bash
head -10 plugins/optimus-devops-plugin/skills/sync-skill-symlinks/SKILL.md
```
Expected: `name: sync-skill-symlinks`，`metadata.version: "2.0.0"`，其余字段（`author`/`category`/`compatibility`/`allowed-tools`）保持不变。

- [ ] **Step 3: git status 确认改动范围符合预期**

```bash
git status --short
```
Expected: 涉及文件仅为——`plugins/optimus-devops-plugin/skills/sync-agent-skills/` → `sync-skill-symlinks/`（rename）、`.kiro/steering/plugins.md`、`.claude-plugin/marketplace.json`、`plugins/optimus-devops-plugin/.codex-plugin/plugin.json`，以及本次新增的 `docs/superpowers/specs/2026-08-30-sync-skill-symlinks-rename-codex-design.md` 和本计划文件本身。

- [ ] **Step 4: 调用 commit-cc-plugin skill 提交并推送**

不手动执行 git 工作流。触发语句："提交"。commit message 建议方向（由 commit-cc-plugin 内部规范最终决定格式）：说明 skill 改名 + Codex 集成 + Major 版本升级的原因。

- [ ] **Step 5: 提交后人工确认**

提交完成后，告知用户改动已推送，并提醒：若用户本机 home 目录下已存在旧的 `~/.claude/skills/sync-agent-skills`、`~/.kiro/skills/sync-agent-skills` 符号链接（早期全局部署遗留），本次改名不会自动清理它们——因为这些链接存在于用户 home 目录而非本仓库，本计划范围不包含清理个人机器上的历史链接。若用户需要，可在改名后手动运行新版 `sync-skill-symlinks`，其 Step 4/5（失效链接检测 + CHECKPOINT）会捕获这些指向旧路径的失效链接并询问是否删除。
