---
name: unipus-commit
description: 在 unipus-plugins-official 插件仓库中需要提交并推送改动时使用 — 触发词包括 "commit"、"push"、"提交"、"推上去"、"推到 master"，或完成任意插件、skill 文件、hook 脚本、marketplace.json 的编辑后需要保存时。在本仓库中请始终使用此 skill 代替普通 git 工作流。
---

# /unipus-commit

本仓库专用提交工作流，一次完成版本号判断、选择性暂存和推送到 master。

## 第一步 — 查看变更

```bash
git status
git diff HEAD --stat
git log --oneline -5
```

## 第二步 — 决定版本号升级

检查 `.claude-plugin/marketplace.json` 是否需要升级版本：

| 变更类型 | 升级类型 |
|---|---|
| 新增插件目录或新增 skill | **Minor** `x.X.x` |
| 改进已有 skill、修复 hook、更新文档 | **Patch** `x.x.X` |
| 架构变更、破坏性 API、重命名 skill | **Major** `X.x.x` |
| 配置微调、注释修改、纯内部重构 | **不升级** |

如需升级，编辑 `.claude-plugin/marketplace.json` → 递增 `"version"` 字段，然后将其与其他文件一起暂存。

## 第三步 — 选择性暂存文件

**禁止使用 `git add -A`** — 可能意外暂存 `.env`、锁文件或二进制文件。

```bash
# 逐个文件暂存
git add .claude-plugin/marketplace.json
git add plugins/<插件名>/skills/<skill名>/SKILL.md
# ... 只添加属于本次提交的文件

# 提交前验证
git diff --staged --stat
```

## 第四步 — 生成提交消息

分析 `git diff --staged`，编写 conventional commit 规范消息，从插件/skill 名称推断 scope。

**格式：**
```
<类型>(<scope>): <简明摘要（中英文均可）>

- <具体变更说明>
- <具体变更说明>

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
```

**类型参考：**
- `feat` — 新 skill、新插件、新 hook
- `fix` — hook 脚本 bug 修复、配置错误
- `docs` — README、CLAUDE.md、tips.txt 更新
- `chore` — 仅升级版本号、依赖更新
- `refactor` — 重构 skill 结构但不改变行为
- `perf` — skill token 数量优化

**scope 示例：** `wpf-skill`、`devops-hooks`、`marketplace`、`office-plugin`

使用 heredoc 传递多行消息，避免引号转义问题：
```bash
git commit -m "$(cat <<'EOF'
feat(wpf-skill): add event leak and async patterns

- 新增检查点 9: 事件处理器内存泄漏（WeakEventManager）
- 新增检查点 10: 数据绑定性能优化（OneTime/OneWay）
- 新增检查点 11: UI线程与Dispatcher优化

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

## 第五步 — 推送到 master

```bash
git push origin master
```

若因代理或网络重置导致推送失败，重试一次。若仍失败，向用户报告错误——**禁止** force push 或 `--no-verify`。

## 常见错误

- 使用 `git add -A` — 可能包含敏感文件
- 新增 skill 时忘记升级版本号（应为 minor）
- 使用 "update files" 等模糊消息 — 始终描述具体变更
- 因 skill 内容改进就升级 major — major 仅用于破坏性或架构级变更
