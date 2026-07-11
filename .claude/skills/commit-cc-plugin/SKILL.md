---
name: commit-cc-plugin
description: 在 optimus-plugins-official 插件仓库中提交并推送改动时使用。任何涉及此仓库 git 提交/推送的操作，都必须使用此 skill，绝不能用普通 git 工作流替代。触发场景：用户明确表达提交或推送意图，如说"提交"、"推上去"、"push"、"commit"、"保存改动"、"同步到远端"、"帮我提交"、"推到 master"、"推一下"、"存一下"。
metadata:
  version: "3.1.4"
  author: desktop client team
compatibility: 需要 Git 仓库环境及远程推送权限；无 MCP 或第三方 CLI 依赖。
allowed-tools: Bash Edit
---

# /commit-cc-plugin

本仓库专用发布工作流，完成版本决策、选择性暂存、提交和推送到 master。

## 第一步 — 状态检查

```bash
git status
git diff HEAD --stat
git log --oneline -5
```

🔴 **CHECKPOINT — 遗留暂存文件处理（继续前必须完成）：**

若 `git status` 存在 `Changes to be committed`，对每个文件做显式决策：

| 判断 | 操作 |
|---|---|
| 与本次改动属于**同一逻辑任务** | 一并提交，提交消息中说明 |
| 与本次改动**无关** | `git restore --staged <file>` 取消暂存，单独处理 |

## 第二步 — 版本号决策

**变更路径决定是否升级：**

- **`.claude/` 下的文件** → 跳过，不升级
- **`plugins/` 下的文件** → 按下表判断：

| 变更类型 | 升级 |
|---|---|
| 新增 skill / command / hook / subagent / mcp / lsp，或新增插件目录 | **Minor** `x.X.x` |
| 更新/修复已有内容（改进、修复、文档） | **Patch** `x.x.X` |
| 删除或重命名用户可见功能；破坏性架构变更 | **Major** `X.x.x` |
| 删除内部实现（hook 脚本调整、辅助文件）；配置微调 | **Patch** `x.x.X` |

如需升级，编辑 `.claude-plugin/marketplace.json` 的 `"version"` 字段，随本次一并暂存。

## 第三步 — 暂存与原子性核查

**禁止 `git add -A`**，逐文件暂存：

```bash
git add .claude-plugin/marketplace.json
git add plugins/<插件名>/skills/<skill名>/SKILL.md
# ... 只添加本次任务的文件

git diff --staged --stat   # 确认暂存内容
```

暂存后 🔴 **CHECKPOINT — 原子性自查三问**（任何一问答"否"先修正暂存区再继续）：

1. staged 内容是否都属于**同一逻辑任务**？
2. 同目录是否有同任务的关联文件**未暂存**（untracked 或 modified）？
3. 是否混入了**无关**变更？

## 第四步 — 提交

分析 `git diff --staged`，按 Conventional Commits 规范写消息：

```
<类型>(<scope>): <简明摘要>

- <具体变更>
- <具体变更>

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
```

**Co-Authored-By 的模型名不得硬编码**——必须填写当前会话实际使用的模型（如 Claude Sonnet 5、Claude Opus 4.6 等），不得照抄下方示例或任何历史提交里的旧模型名。

**类型：** `feat`（新增）/ `fix`（修复）/ `docs`（文档）/ `refactor`（重构）/ `chore`（版本/依赖）/ `perf`（性能）

**scope 示例：** `devops-hooks`、`office-plugin`、`marketplace`、`sync-cc-tips`

用 heredoc 避免引号转义：

```bash
git commit -m "$(cat <<'EOF'
feat(devops-hooks): 新增 weekly-report 工作周报转写技能

- 新增 /weekly-report skill，从对话和 git 记录提取工作内容
- 支持四段式标准周报格式输出
- 版本升级：2.0.0 → 2.1.0（Minor）

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

## 第五步 — 同步推送

提交后先 rebase 同步远端，再推送：

```bash
git pull --rebase origin master
git push origin master
```

- rebase 冲突：解决后 `git rebase --continue`；放弃用 `git rebase --abort` 并告知用户
- push 失败：重试一次；仍失败则报告错误，**禁止** force push 或 `--no-verify`

## 常见错误

| 错误 | 正确做法 |
|---|---|
| `git add -A` | 逐文件暂存，避免混入敏感文件 |
| `.claude/` 下改动也升级版本 | 仅 `plugins/` 下变更才判断版本 |
| 新增 skill 忘记升级版本 | 新增内容 → Minor |
| 提交消息过于模糊（"update files"） | 描述具体变更内容 |
| skill 内容改进就升级 Major | Major 仅用于破坏性变更 |
| `git push --force` 或 `git push -f` | 禁止 force push；push 失败先排查原因，最多重试一次 |
| `git commit --no-verify` 绕过 hook | 禁止跳过 hook；hook 报错必须修复后重试 |
