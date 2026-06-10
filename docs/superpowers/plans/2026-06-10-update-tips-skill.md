# update-tips Skill 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `.claude/skills/update-tips/SKILL.md` 创建并验证一个专属 skill，让用户执行 `/update-tips` 后全自动完成 tips.txt 的增删改、文档数字同步和提交。

**Architecture:** 单文件平铺 skill，Claude 读取 SKILL.md 后按 6 步流程执行：抓取 changelog → 语义分析差异 → 写入 tips.txt → 同步文档数字 → 展示摘要 → 调用 unipus-commit。无独立脚本，所有判断逻辑由 Claude 语义理解完成。

**Tech Stack:** Claude Code skill 系统（`.claude/skills/` 自动加载，无需 marketplace）、WebFetch、文件读写工具、unipus-commit skill 链式调用。

---

## 文件结构

| 操作 | 路径 | 说明 |
|---|---|---|
| 已创建 ✅ | `.claude/skills/update-tips/SKILL.md` | skill 主体，6步流程全部写入 |
| 已创建 ✅ | `docs/superpowers/specs/2026-06-10-update-tips-skill-design.md` | 设计文档 |
| 本计划 | `docs/superpowers/plans/2026-06-10-update-tips-skill.md` | 实施计划 |

---

## Task 1：验证 SKILL.md 格式与内容完整性

**Files:**
- Check: `.claude/skills/update-tips/SKILL.md`

- [ ] **Step 1：检查 frontmatter 格式**

```bash
head -6 .claude/skills/update-tips/SKILL.md
```

期望输出（frontmatter 必须被 `---` 包裹，含 name 和 description）：
```
---
name: update-tips
description: 从 Claude Code 最新 changelog 自动更新 tips.txt...
---
```

- [ ] **Step 2：确认 6 个步骤标题全部存在**

```bash
grep "^## 第" .claude/skills/update-tips/SKILL.md
```

期望输出（顺序一致）：
```
## 第一步 — 抓取 changelog
## 第二步 — 读取现有 tips.txt
## 第三步 — 三类差异识别
## 第四步 — 写入 tips.txt
## 第五步 — 同步文档数字
## 第六步 — 展示摘要并提交
```

- [ ] **Step 3：确认三类差异识别规则标题存在**

```bash
grep "^### " .claude/skills/update-tips/SKILL.md
```

期望输出含：
```
### 🆕 新增条件
### ✏️ 修改条件
### 🗑️ 删除条件
### 格式校验（每条写入前执行）
```

- [ ] **Step 4：确认文档数字同步覆盖全部 5 处**

```bash
grep -A 10 "批量更新以下" .claude/skills/update-tips/SKILL.md
```

期望看到 marketplace.json（2处）、README.md（2处）、hooks/README.md（1处）均被列出。

---

## Task 2：验证 skill 在 Claude Code 中可加载

**Files:**
- Check: `.claude/skills/update-tips/SKILL.md`

- [ ] **Step 1：确认 `.claude/skills/` 目录结构正确**

```bash
ls -la .claude/skills/update-tips/
```

期望输出：
```
SKILL.md
```

只需一个文件，无多余文件。

- [ ] **Step 2：在 Claude Code 中验证 skill 已加载**

在 Claude Code 会话中执行：
```
/reload-skills
```

然后执行：
```
/skills
```

在输出列表中确认 `update-tips` 出现，description 为：
```
从 Claude Code 最新 changelog 自动更新 tips.txt...
```

- [ ] **Step 3：验证 description 触发词覆盖**

在 Claude Code 中分别输入以下内容，确认每次都触发 update-tips skill：
```
/update-tips
更新tips
同步tips
```

若 skill 正确加载，Claude 应开始执行第一步（WebFetch changelog）。

---

## Task 3：验证 unipus-commit 链式调用路径

**Files:**
- Check: `.claude/skills/update-tips/SKILL.md`
- Check: `.claude/skills/unipus-commit/SKILL.md`

- [ ] **Step 1：确认 SKILL.md 中包含 unipus-commit 调用指令**

```bash
grep "unipus-commit" .claude/skills/update-tips/SKILL.md
```

期望输出（必须在第六步中出现）：
```
调用 `unipus-commit` skill 完成提交推送
```

- [ ] **Step 2：确认无变更时退出逻辑存在**

```bash
grep "0新增/0修改/0删除\|无任何变化" .claude/skills/update-tips/SKILL.md
```

期望看到：
```
若本次 changelog 范围内无任何变化（0新增/0修改/0删除），输出提示并退出，不提交
```

- [ ] **Step 3：确认 changelog 抓取失败时的防护逻辑存在**

```bash
grep "抓取失败\|停止" .claude/skills/update-tips/SKILL.md
```

期望看到：
```
若 changelog 抓取失败，报告错误并停止，不对 tips.txt 做任何修改
```

---

## Task 4：提交全部文件

**Files:**
- Commit: `.claude/skills/update-tips/SKILL.md`
- Commit: `docs/superpowers/specs/2026-06-10-update-tips-skill-design.md`
- Commit: `docs/superpowers/plans/2026-06-10-update-tips-skill.md`

- [ ] **Step 1：确认暂存文件范围正确**

```bash
git status --short
```

期望只看到这三个 untracked 文件，无其他修改：
```
?? .claude/skills/update-tips/
?? docs/superpowers/plans/2026-06-10-update-tips-skill.md
?? docs/superpowers/specs/2026-06-10-update-tips-skill-design.md
```

- [ ] **Step 2：调用 unipus-commit skill 完成提交**

> ⚠️ 本步骤**必须通过 `unipus-commit` skill 执行**，禁止手动 git add/commit。

触发方式：在 Claude Code 中说"提交"或"推上去"。

skill 将：
1. 判断变更路径：`.claude/` 和 `docs/` 均不触发版本号升级
2. 选择性暂存三个文件
3. 生成提交消息，类型为 `feat`，scope 为 `devops-hooks`
4. pull --rebase 后 push 到 master

期望提交消息格式：
```
feat(devops-hooks): 新增 update-tips 专属 skill

- 创建 .claude/skills/update-tips/SKILL.md
- 6步全自动流程：changelog 抓取 → 差异识别 → 写入 → 文档同步 → 提交
- 新增设计文档和实施计划

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
```

---

## 自查结果

**Spec 覆盖：**
| Spec 要求 | 对应 Task |
|---|---|
| 触发方式：`/update-tips` | Task 2 Step 2-3 验证 |
| 6步全自动流程 | Task 1 Step 2 验证 |
| 三类差异识别规则 | Task 1 Step 3 验证 |
| 文档数字同步 5 处 | Task 1 Step 4 验证 |
| unipus-commit 链式调用 | Task 3 Step 1 验证 |
| 无变更时退出 | Task 3 Step 2 验证 |
| 抓取失败防护 | Task 3 Step 3 验证 |
| 提交入库 | Task 4 全部步骤 |

**Placeholder 扫描：** 无 TBD/TODO/占位符，所有步骤含完整命令和期望输出。

**类型一致性：** 纯 SKILL.md 文件，无代码类型，不适用。
