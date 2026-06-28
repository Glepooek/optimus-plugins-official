# sync-agent-skills Skill 设计文档

**日期：** 2026-06-28  
**状态：** 已批准

---

## 概述

设计一个 Claude Code skill，将 `~/.agents/skills/` 中的所有 skill 目录以符号链接的方式同步到 `~/.claude/skills/` 和 `~/.kiro/skills/`，使用户只需维护一个 source of truth，而无需在多处手动创建链接。

---

## 定位

**存放位置：** `plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md`

分类依据：`unipus-devops-plugin` 负责开发基础设施（CI/CD、项目分析、hooks）。本 skill 管理本地开发工具链环境，属同类职责。

**全局使用说明：** 如需在所有项目的 Claude Code 会话中使用，将 `plugins/unipus-devops-plugin/skills/sync-agent-skills/` 整个目录复制到 `~/.agents/skills/sync-agent-skills/`，再运行一次本 skill 自动链接即可全局生效。

**版本规则：** 新增 skill → Minor 升级（`x.X.x`）

**触发词：** "同步 skills"、"sync agent skills"、"链接 skills"、"更新 skill 链接"、"sync-agent-skills"

---

## 执行流程

### Step 1 — 扫描源目录

列出 `~/.agents/skills/` 下所有子目录名，作为待同步的 skill 列表。

### Step 2 — 检测并创建缺失链接

对每个 source_skill，分别检查 `~/.claude/skills/<skill>` 和 `~/.kiro/skills/<skill>`：
- 不存在 → 创建符号链接
- 已存在且是符号链接 → 记录"跳过"
- 已存在但非符号链接（普通目录）→ 打印警告，跳过（不覆盖）

### Step 3 — 检测失效链接

扫描两个目标目录中的所有符号链接，找出指向路径不存在的失效链接（dangling symlinks），收集到 `dangling_list`。

### Step 4 — 处理失效链接（仅当 dangling_list 非空）

打印失效链接列表后进入 CHECKPOINT：

> 🔴 CHECKPOINT：以上 X 条失效链接指向已不存在的源，是否删除？[y/n]

- `y` → 逐条删除
- `n` → 跳过，提示用户稍后手动处理

### 输出格式示例

```
✅ 新建链接: youdaonote-skill → ~/.claude/skills/
✅ 新建链接: youdaonote-skill → ~/.kiro/skills/
⚠️  已存在，跳过: darwin-skill（~/.claude 和 ~/.kiro）
──────────────────────────────────────────
汇总: 新建 2 条，跳过 4 条，失效 0 条
```

---

## 边界情况与错误处理

| 情况 | 处理方式 |
|---|---|
| 目标目录（`~/.claude/skills/` 或 `~/.kiro/skills/`）不存在 | 自动创建目录，不终止 |
| 目标路径已存在且为普通目录（非符号链接） | 打印警告跳过，不覆盖 |
| `~/.kiro/` 整体不存在 | 跳过 kiro 同步，打印 `ℹ️  ~/.kiro/skills/ 不存在，已跳过 kiro 同步` |
| Windows 下符号链接权限不足 | 开头检测权限，不足则打印提示并终止，不静默失败 |

---

## 平台兼容性

- **Windows：** 使用 `New-Item -ItemType SymbolicLink`，需要开发者模式或管理员权限
- **macOS/Linux：** 使用 `ln -s`

Skill 在执行前检测当前平台并选择对应命令。

---

## 不在范围内

- 不支持自动触发（SessionStart hook）——设计为纯手动触发
- 不支持自定义目标目录（固定为 `~/.claude/skills/` 和 `~/.kiro/skills/`）
- 不同步非目录文件（仅处理 `~/.agents/skills/` 下的子目录）
