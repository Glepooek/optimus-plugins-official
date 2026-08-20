# mastergo-to-wpf-page 重命名 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将页面组装 Skill 的用户可见入口从 `mastergo-to-wpf` 重命名为 `mastergo-to-wpf-page`，并保留历史设计与计划文档不变。

**Architecture:** 这是纯命名迁移，不改变 DSL 转换器、组件匹配器或组件抽取器的实现和行为。移动页面 Skill 目录后，同步所有现行运行文档和相邻 Skill 的交叉引用；以 Skill `2.0.0` 与 marketplace `9.0.0` 明确表达旧调用入口不再可用。

**Tech Stack:** Markdown、JSON、Python 3 unittest、Git。

---

## 文件结构

| 路径 | 责任 |
|---|---|
| `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/` | 重命名后的页面组装 Skill；保留全部 Python 脚本、fixtures 与测试。 |
| `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/` | 将下游交叉引用改为新页面 Skill 名称。 |
| `plugins/optimus-frontend-plugin/skills/wpf-project-conventions/` | 将共享约定的消费者名称改为新名称。 |
| `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/` | 将现行 README 与参考文档中的页面 Skill 引用改为新名称。 |
| `.claude-plugin/marketplace.json` | 用新名称说明页面组装能力，并升级 marketplace Major 版本。 |

## Task 1: 重命名页面 Skill 目录与公开元数据

**Files:**
- Move: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/` → `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/`
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/SKILL.md`
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/CHANGELOG.md`

- [ ] **Step 1: 移动完整目录，保留脚本与 fixtures 内容**

```powershell
Move-Item `
  plugins/optimus-frontend-plugin/skills/mastergo-to-wpf `
  plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page
```

Expected: 新目录含 `SKILL.md`、`CHANGELOG.md`、`test-prompts.json`、`references/` 与 `scripts/`；旧目录不存在。

- [ ] **Step 2: 更新 SKILL.md frontmatter 与本地测试路径**

将前置元数据替换为：

```yaml
---
name: mastergo-to-wpf-page
description: 当用户提供 MasterGo 设计稿链接并要求生成 WPF 页面、WPF 界面或把设计稿转成 WPF 代码时使用此 Skill；组件优先组装可验证的 XAML、资源清单与转换报告，并可选复用经白名单验证的项目资源和控件。
metadata:
  version: "2.0.0"
  author: desktop client team
  category: generator
```

将末尾测试命令改为：

```powershell
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/scripts -p "test_*.py"
```

- [ ] **Step 3: 在 CHANGELOG 顶部记录破坏性入口变更**

在 `# Changelog` 后插入：

```markdown
## [2.0.0] - 2026-08-20

### Changed
- 破坏性重命名：页面组装 Skill 从 `mastergo-to-wpf` 更名为 `mastergo-to-wpf-page`。
- 新调用入口为 `/optimus-frontend-plugin:mastergo-to-wpf-page`；旧入口 `/optimus-frontend-plugin:mastergo-to-wpf` 不再保留别名。
- 页面生成、组件匹配、图标回填和离线脚本行为保持不变。
```

- [ ] **Step 4: 验证目录和 Skill 元数据**

```powershell
Test-Path plugins/optimus-frontend-plugin/skills/mastergo-to-wpf
Test-Path plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/SKILL.md
Select-String -Path plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/SKILL.md -Pattern '^name: mastergo-to-wpf-page$|version: "2.0.0"'
```

Expected: 第一个命令输出 `False`，第二个输出 `True`，最后命中两行。

## Task 2: 更新现行运行文档和跨 Skill 引用

**Files:**
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/SKILL.md`
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/README.md`
- Modify: `plugins/optimus-frontend-plugin/skills/wpf-project-conventions/CONVENTIONS.md`
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/README.md`
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/references/wpf-xaml-icon-sepc.md`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: 更正 components Skill 的页面入口引用**

在 `mastergo-to-wpf-components/SKILL.md` description 中替换：

```text
Not for page generation (use mastergo-to-wpf-page)
```

在 README 中将下游说明、产出物数据流和依赖图的 `mastergo-to-wpf` 全部替换为 `mastergo-to-wpf-page`；保留 `mastergo-to-wpf-components` 自身名称不变。

- [ ] **Step 2: 更正共享约定和图标 Skill 的现行引用**

在 `wpf-project-conventions/CONVENTIONS.md` 开头改为：

```markdown
本文件是 `mastergo-to-wpf-components` 与 `mastergo-to-wpf-page` 两个 skill 的共享事实来源。
```

在 `mastergo-icon-expoter/README.md` 和 `references/wpf-xaml-icon-sepc.md` 中，将“整页转换/页面生成”职责的 `mastergo-to-wpf` 引用替换成 `mastergo-to-wpf-page`，但不改动本 Skill、`mastergo-to-wpf-components` 或历史文档的名称。

- [ ] **Step 3: 更新 marketplace 名称说明和 Major 版本**

将 `.claude-plugin/marketplace.json` 顶层版本替换为：

```json
"version": "9.0.0"
```

在 `optimus-frontend-plugin` description 的页面能力描述中使用：

```text
MasterGo 设计稿转 WPF 页面组装（mastergo-to-wpf-page）
```

保留单独的 `mastergo-to-wpf-components` 组件库说明。

- [ ] **Step 4: 验证现行引用不遗留旧入口**

```powershell
$paths = @(
  '.claude-plugin/marketplace.json',
  'plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page',
  'plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components',
  'plugins/optimus-frontend-plugin/skills/wpf-project-conventions',
  'plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter'
)
git grep -n -- 'mastergo-to-wpf' -- $paths
```

Expected: 只允许 `mastergo-to-wpf-components` 自身名称命中；不得有独立 `mastergo-to-wpf` 入口、旧目录或旧调用名。

## Task 3: 离线回归、结构完整性与提交

**Files:**
- Verify: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/scripts/**`
- Verify: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/scripts/**`
- Verify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: 运行重命名后页面 Skill 的全量离线测试**

```powershell
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/scripts -p "test_*.py"
```

Expected: 新增的 `test_match_components.py` 两项通过；既有 `test_optimization.py` 的 9 项已知失败单独记录为重命名前基线，不作为此次目录迁移回归。

- [ ] **Step 2: 运行组件抽取器回归测试与 JSON 校验**

```powershell
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/scripts -p "test_*.py"
python -m json.tool .claude-plugin/marketplace.json > $null
python -m json.tool plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/test-prompts.json > $null
git diff --check
```

Expected: 抽取器测试全部通过；三个校验命令无输出且 exit 0。

- [ ] **Step 3: 确认历史文档未被修改**

```powershell
git diff --name-only | Select-String '^docs/superpowers/(plans|specs)/'
```

Expected: 仅允许本次新建的 `docs/superpowers/specs/2026-08-20-mastergo-to-wpf-page-rename-design.md` 与 `docs/superpowers/plans/2026-08-20-mastergo-to-wpf-page-rename.md`；既有历史 plans/specs 不在输出中.

- [ ] **Step 4: 提交重命名**

逐文件暂存，禁止 `git add -A`：

```powershell
git add .claude-plugin/marketplace.json
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/SKILL.md
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/README.md
git add plugins/optimus-frontend-plugin/skills/wpf-project-conventions/CONVENTIONS.md
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/README.md
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/references/wpf-xaml-icon-sepc.md
git add docs/superpowers/specs/2026-08-20-mastergo-to-wpf-page-rename-design.md
git add docs/superpowers/plans/2026-08-20-mastergo-to-wpf-page-rename.md
```

Commit message:

```text
feat(frontend-plugin)!: 重命名 MasterGo WPF 页面组装 skill

- mastergo-to-wpf 更名为 mastergo-to-wpf-page，旧调用入口不再保留
- 同步组件库、共享约定、图标 Skill 和 marketplace 的现行引用
- Skill 升级至 2.0.0，marketplace 升级至 9.0.0（Major）

Co-Authored-By: gpt-5.6-terra <noreply@anthropic.com>
```
