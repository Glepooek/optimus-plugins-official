---
name: commit-cc-plugin
description: 在 optimus-plugins-official 插件仓库中提交并推送改动时使用。任何涉及此仓库 git 提交/推送的操作，都必须使用此 skill，绝不能用普通 git 工作流替代。触发场景：用户明确表达提交或推送意图，如说"提交"、"推上去"、"push"、"commit"、"保存改动"、"同步到远端"、"帮我提交"、"推到 master"、"推一下"、"存一下"。
metadata:
  version: "4.0.0"
  author: desktop client team
  category: workflow
compatibility: 需要 Git 仓库环境及远程推送权限；无 MCP 或第三方 CLI 依赖。
allowed-tools: Bash
---

# /commit-cc-plugin

本仓库的提交工作流：把改动干净地暂存、写成一条规范的 commit message、推送到 master。

版本号该不该升、升多少，依据是 `AGENTS.md` 的「版本管理规则」节，在改动插件内容时就该判断完；漏升由 `.githooks/pre-commit` 拦截。

## Git 规范依据

本 skill 不重复维护 Git 协作规范，统一以 `knowledge-base/git/` 为依据：

- 分支策略、主干保护和同步方式：[`knowledge-base/git/rules/01-branching.md`](../../../knowledge-base/git/rules/01-branching.md)
- Conventional Commits、AI 协作者标注、hook 和敏感信息防护：[`knowledge-base/git/rules/02-commit-messages.md`](../../../knowledge-base/git/rules/02-commit-messages.md)
- PR、review、合并策略和强制推送限制：[`knowledge-base/git/rules/03-pull-requests.md`](../../../knowledge-base/git/rules/03-pull-requests.md)
- 版本号、tag 和发布流程：[`knowledge-base/git/rules/04-versioning-release.md`](../../../knowledge-base/git/rules/04-versioning-release.md)
- 完整规则入口：[`knowledge-base/git/README.md`](../../../knowledge-base/git/README.md)

本 skill 只补充本仓库特有的暂存编排与 checkpoint；若本文件与 Git 知识库的通用规范冲突，以知识库为准。

## 第一步 — 状态检查

```bash
git status
git log --oneline -5
```

🔴 **CHECKPOINT — 遗留暂存文件处理（继续前必须完成）：**

若 `git status` 存在 `Changes to be committed`，对每个文件做显式决策：

| 判断 | 操作 |
|---|---|
| 与本次改动属于**同一逻辑任务** | 一并提交，提交消息中说明 |
| 与本次改动**无关** | `git restore --staged <file>` 取消暂存，单独处理 |

## 第二步 — 暂存与原子性核查

**禁止 `git add -A`**，逐文件暂存：

```bash
git add plugins/<插件名>/.claude-plugin/plugin.json
git add plugins/<插件名>/.codex-plugin/plugin.json
git add plugins/<插件名>/skills/<skill名>/SKILL.md
# ... 只添加本次任务的文件

git diff --staged --stat   # 确认暂存内容
```

暂存后 🔴 **CHECKPOINT — 原子性自查三问**（任何一问答"否"先修正暂存区再继续）：

1. staged 内容是否都属于**同一逻辑任务**？
2. 同目录是否有同任务的关联文件**未暂存**（untracked 或 modified）？
3. 是否混入了**无关**变更？

## 第三步 — Unpushed 提交检测与 Amend 合并

在写 commit message 前，按 [`knowledge-base/git/rules/01-branching.md`](../../../knowledge-base/git/rules/01-branching.md) 的分支同步约定，检测当前分支相对 `origin/master` 是否已有未推送的提交。**本步 fetch 一次，第五步的同步推送复用其结果，不重复 fetch**：

```bash
git fetch origin master --quiet 2>/dev/null || true
git log origin/master..HEAD --oneline
```

🔴 **CHECKPOINT**：

| 检测结果 | 处理 |
|---|---|
| 无未推送提交 | 跳过 §A，第四步正常新建 commit |
| 有未推送提交 | 展示列表，询问用户是否将本次改动 amend 合并到最近一次提交 |

### §A 条件小节 — 合并到最近一次未推送提交（仅当第三步检测到未推送提交时执行）

询问示例：

```
📌 检测到未推送的提交：
{hash1} {message1}

是否将本次改动合并到这次提交？(amend/new，默认 new)
```

选择 amend 时：

1. `git diff HEAD~1 --name-status` 读取上一个提交的改动范围，与本次暂存内容合并分析
2. 生成一条覆盖两次改动的汇总 commit message，不得遗漏任一次的变更点
3. 第四步改用 `git commit --amend -m "{汇总 message}"` 而非新建 commit

仅 amend 最近一个未推送提交，不做多提交 squash。

## 第四步 — 提交

若 §A 选择了 amend，用 `git commit --amend` 替代下方的 `git commit`，其余流程不变。

分析 `git diff --staged`（amend 时改为分析合并后的完整改动范围），按 [`knowledge-base/git/rules/02-commit-messages.md`](../../../knowledge-base/git/rules/02-commit-messages.md) 写 Conventional Commits message，并按其中要求标注 AI 协作者：

```
<类型>(<scope>): <简明摘要>

- <具体变更>
- <具体变更>

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
```

`Co-Authored-By` 的格式、提交类型和 scope 规则以 Git 知识库为准；模型名必须填写当前会话实际使用的模型，不得照抄历史提交。

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

PowerShell 不支持 Bash 的 `$(cat <<'EOF'...)` 写法，也不会把 `\n` 转换为真实换行。Windows 下使用 here-string，或传入多个 `-m` 参数。提交格式仍以 [`knowledge-base/git/rules/02-commit-messages.md`](../../../knowledge-base/git/rules/02-commit-messages.md) 为准：

```powershell
$message = @"
docs(scope): 简明摘要

- 具体变更
- 具体变更

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
"@
git commit -m $message
```

禁止在提交 message 字符串中使用字面量 `\n` 拼接换行。提交后必须验证 message：

```powershell
# PowerShell
git show -s --format=%B HEAD
git show -s --format=%B HEAD | Select-String -SimpleMatch '\n'
```

```bash
# Bash：必须用 -F 固定字符串匹配
git show -s --format=%B HEAD
git show -s --format=%B HEAD | grep -F '\n'
```

⚠️ **两处都要关闭正则解释**（PowerShell 用 `-SimpleMatch`，Bash 用 `-F`），这样匹配的就是「反斜杠 + 字母 n」这两个字符本身。

不要把 PowerShell 的 `Select-String '\\n'` 照搬到 Bash：该写法在 .NET 正则下恰好等价于字面反斜杠加 n，结果正确；但 `grep '\\n'` 在 BRE 下会被解释成「反斜杠**或**字母 n」，凡含 `n` 的行全部命中，正确的 message 也会被误判为格式错误。

第二条命令必须无输出；若出现 `\n`，说明提交信息格式错误。可再用 `git show -s --format=%B HEAD | wc -l`（PowerShell 用 `(git show -s --format=%B HEAD).Count`）确认行数与预期一致，佐证换行是真实的。提交已推送后遵循 [`knowledge-base/git/rules/03-pull-requests.md`](../../../knowledge-base/git/rules/03-pull-requests.md) 的强制推送限制，不要擅自 amend 或 force push，应先报告并确认处理方式。

🔴 **CHECKPOINT — `pre-commit` 阻断时禁止绕过**。`git commit` 输出 `[pre-commit] 未通过` 说明仓库一致性检查失败，commit **没有生成**。修正需要编辑文件，超出本 skill 的 `allowed-tools`——**退出本流程**，按下表修好后重新触发提交，**禁止** `--no-verify`：

| 报错 | 处置 |
|---|---|
| `版本不一致` / `缺 version 字段` / `缺 .claude-plugin` / `缺 .codex-plugin` | 按 `AGENTS.md` 版本管理规则判断本次改动该升到哪个版本号，把**两份** `plugin.json` 都改成该值。**不要**拿一份覆盖另一份——错的可能恰好是"另一份"（该升 Minor 却升了 Patch） |
| `缺符号链接` / `指向已不存在的` | 按报错括号里给出的命令补齐或清理，产生的文件纳入本次暂存后重新提交 |
| `有多余字段` | 门禁白名单与本次改动冲突，见 `.githooks/pre-commit` 与 `check_plugin_versions.py` 的注释；放宽白名单需同时改脚本、改测试、记 `known-issues.md`，三件事缺一不可 |
| 检查本身的 bug（如误报） | 修 `.githooks/` 下的脚本并跑通 `python -m unittest discover -s .githooks -p "test_*.py"`，不要改用 `--no-verify` 跳过 |
| `不是 40 位小写十六进制` / `条目内不得写 version` / `未登记在 … 的「已接入」表` / `缺锚点 <!-- registry:active -->` | marketplace 外部引用条目写歪，触发 `check_external_entries.py`。按 `/add-external-skill` 的写入规则修正条目或台账 |
| `台账 sha … 不一致` | 先判明哪一个对应实际验证过的状态，不要随手对齐——先看是条目还是台账反映的是「更新做了一半」，修那个偏离实际状态的一边 |

## 第五步 — 同步推送

按 [`knowledge-base/git/rules/01-branching.md`](../../../knowledge-base/git/rules/01-branching.md) 和 [`knowledge-base/git/rules/03-pull-requests.md`](../../../knowledge-base/git/rules/03-pull-requests.md) 的主干保护与同步约定，提交后先 rebase 同步远端，再推送。**复用第三步已完成的 fetch**（若第三步已 fetch 且本地未落后，`git pull --rebase` 会静默返回）：

```bash
git pull --rebase origin master
git push origin master
```

三种失败的处置：

| 失败 | 处置 |
|---|---|
| `cannot pull with rebase: You have unstaged changes`（exit 128） | 见下方「工作区不干净」 |
| rebase 冲突 | 解决后 `git rebase --continue`；放弃用 `git rebase --abort` 并告知用户 |
| push 失败 | 重试一次；仍失败则报告错误，**禁止** force push 或 `--no-verify` |

**工作区不干净**——第一步 CHECKPOINT 明确允许把无关改动排除在本次提交外，被排除的文件就留在工作区，rebase 会被它们挡住。**越是按第一步规范排除了无关文件，越必然撞上这个失败**。

不要为了让 rebase 通过就把无关文件一并提交——那会破坏第二步刚校验过的原子性。正确做法是只把它们临时挪走：

```bash
git stash push -m "commit-cc-plugin: 临时挪走无关改动" <排除的文件路径...>
git pull --rebase origin master
git push origin master
git stash pop
```

⚠️ `git stash push` 必须**列出具体文件路径**，不加路径的裸 `git stash` 会把工作区全部改动一起挪走，`pop` 时若遇冲突更难还原。推送完成后必须 `git stash pop` 原样恢复，不要留在 stash 里——用户会以为改动丢了。

## 常见错误

| 错误 | 正确做法 |
|---|---|
| `git add -A` | 逐文件暂存，避免混入敏感文件 |
| 提交消息过于模糊（"update files"） | 按 `knowledge-base/git/rules/02-commit-messages.md` 写明变更意图 |
| `git push --force` 或 `git push -f` | 遵循 `knowledge-base/git/rules/03-pull-requests.md` 的强制推送限制；push 失败先排查原因，最多重试一次 |
| `git commit --no-verify` 绕过 hook | 禁止跳过。`pre-commit` 报错说明仓库一致性真的坏了，按第四步 CHECKPOINT 的分类处置；`--no-verify` 只是把问题推给下一个人 |
| 有未推送提交不检测直接新建 commit | 第三步已内置检测，发现未推送提交时应询问用户是否 amend 合并 |
| rebase 被未暂存改动挡住，就把无关文件一并提交 | 破坏了刚校验过的原子性。用 `git stash push <文件>` 只挪走它们，push 后 `git stash pop` 恢复（第五步「工作区不干净」） |
| 在本 skill 内逐步核对版本号该升多少 | 版本决策的依据是 `AGENTS.md` 版本管理规则，发生在**改动插件内容时**，不是提交时。本 skill 不重复该判断，漏升由 `pre-commit` 拦截 |
| hook 报「缺符号链接」就手动建完了事、不看是不是自己删错了 | 先确认该 skill 是新增（应补链接）还是被删（应连同镜像一起 `git rm`），别把删除操作补成半成品 |
