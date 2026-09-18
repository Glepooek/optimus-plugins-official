---
name: commit-cc-plugin
description: 在 optimus-plugins-official 插件仓库中提交并推送改动时使用。任何涉及此仓库 git 提交/推送的操作，都必须使用此 skill，绝不能用普通 git 工作流替代。触发场景：用户明确表达提交或推送意图，如说"提交"、"推上去"、"push"、"commit"、"保存改动"、"同步到远端"、"帮我提交"、"推到 master"、"推一下"、"存一下"。
metadata:
  version: "6.0.0"
  author: desktop client team
  category: workflow
compatibility: 需要 Git 仓库环境及远程推送权限；需 GitHub CLI（`gh`，已通过 `gh auth status` 认证）用于开 PR、轮询必需检查、squash merge；不依赖任何 MCP server。
allowed-tools: Bash
---

# /commit-cc-plugin

本仓库的提交工作流：把改动干净地暂存、写成一条规范的 commit message、经特性分支与 PR 合入 master。

主干 `master` 已开启保护规则，**直推会被服务端拒绝**（`GH013`），这是服务端强制、不依赖任何 harness 的自觉。因此本 skill 的终点不是 `git push origin master`，而是「特性分支 → PR → 五项必需检查全绿 → squash merge」。

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

🔴 **CHECKPOINT — 当前分支判定（继续前必须完成）：**

主干 `master` 已开启保护规则，直推会被服务端以 `GH013` 拒绝。提交路径是「特性分支 → PR → CI 绿 → squash merge」。

| 当前分支 | 处置 |
|---|---|
| `master` | 正常流程，第四步前新建特性分支（见「第三步之后」） |
| 已在特性分支上 | **说明上一轮流程未走完**（CI 未过，或会话中断在轮询阶段）。沿用该分支，不新建；用 `gh pr list --head <branch> --state open` 查是否已有开着的 PR——有则本次提交推上去后**追加进同一个 PR** |

⚠️ 第二支不是防御性设计，而是必要配套：本仓库未开启 auto-merge（见第五步），会话在等 CI 期间中断时 PR 会停在未合并状态，**必须靠下一次触发接续**。CI 变红同样会让流程停在中途。

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

在写 commit message 前，按 [`knowledge-base/git/rules/01-branching.md`](../../../knowledge-base/git/rules/01-branching.md) 的分支同步约定，检测当前分支相对**当前分支的上游**（`@{upstream}`）是否已有未推送的提交：

```bash
# 特性分支上要相对**本分支的上游**判断，不是相对 origin/master
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)
if [ -n "$UPSTREAM" ]; then
  git fetch origin --quiet 2>/dev/null || true
  git log "$UPSTREAM"..HEAD --oneline
else
  echo "本分支尚无上游（首次推送），无未推送提交可合并"
fi
```

⚠️ **基准必须是 `@{upstream}` 而不是 `origin/master`。** 在特性分支上，`origin/master..HEAD` 会把本分支的全部提交都算成「未推送」，从而每次都误触发 §A 的 amend 询问——而那些提交往往已经推上去、甚至已经在一个开着的 PR 里。

⚠️ **`@{upstream}` 不存在是正常状态而非错误**——特性分支首次 `git push -u` 之前本就没有上游，此时「无未推送提交」是正确结论，走上表第一行。

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

## 第三步之后 — 建特性分支（仅当第一步判定为在 `master` 上时执行）

分支名按 [`knowledge-base/git/rules/01-branching.md`](../../../knowledge-base/git/rules/01-branching.md) 的 `<type>/<简短描述>`，**`type` 与本次 commit 的 Conventional Commits type 逐字对齐**：

```bash
git switch -c <type>/<简短描述>
```

示例：`fix/hook-configs-settings-json`、`feat/pr-flow-ci`、`docs/agents-commit-section`。

⚠️ **建分支排在提交之前，理由是「少一步、少一个可能记错的命令」**，不是「否则必须用破坏性命令」。**会话中途才发现忘了建分支时不必推翻重来**，两条命令即可无损补救：

```bash
git switch -c <type>/<描述>          # 新分支从当前 HEAD 拉出，已有 commit 自然归它
git branch -f master origin/master   # master 未被 checkout，-f 只改指针
```

第二条作用于一个**未被 checkout** 的分支，因此只移动引用、不触碰工作树，用不上 `--hard`。（`reset --hard` 之所以危险是它会同时重置工作树；分支指针的移动本身是无损的。）

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

## 第五步 — 推分支、开 PR、等 CI、合并

🔴 **CHECKPOINT — `gh` 可用性（进入第 2 步前必须确认）：**

```bash
gh auth status
```

Expected: 输出含 `✓ Logged in to github.com`。

| 结果 | 处置 |
|---|---|
| 已登录 | 继续 |
| `gh: command not found` | 🔴 **STOP**——报告 `gh` 未安装，请用户 `winget install GitHub.cli` 后重新触发。本 skill 不代为安装 |
| `You are not logged into any GitHub hosts` | 🔴 **STOP**——认证是交互式的，请用户自行 `gh auth login`（在会话中输 `! gh auth login`），完成后重新触发 |

⚠️ 这个检查放在第 1 步之后：`git push` 用的是 git 自己的凭据，与 `gh` 的认证是两套，前者能成功不代表后者可用。

主干只能经 PR 合入（服务端 ruleset 强制，不依赖任何 harness 的自觉）。六个动作，第 1 步和最后两步用 git，中间三步用 `gh` CLI：

| # | 动作 | 手段 |
|---|---|---|
| 1 | 推特性分支 | `git push -u origin <branch>` |
| 2 | 开 PR | `gh pr create --base master --head <branch> --title <标题> --body-file <文件>` |
| 3 | 等 CI | `gh pr checks <branch> --required --watch --fail-fast` |
| 4 | 合并 | `gh pr merge <branch> --squash --subject <标题> --body-file <文件>` |
| 5 | 回主干 | `git switch master && git pull --rebase origin master` |
| 6 | 清分支 | `git branch -d <branch>` **再** `git push origin --delete <branch>` |

⚠️ 第 1 步**必须用 `git push`，不用 `gh api` 之类的 API 写入**——那是通过 API 造新 commit，会与本地已有的 commit 分叉。ruleset 只作用于 `master`，特性分支可自由推。

🔴 **第 2、4 步的多行文本一律走 `--body-file` / `-F`，不用 `--body` 传字面串。** PR body 与 squash message 都含换行和尖括号，直接作为命令行参数传入要同时对付 shell 引号、反引号与 `$` 展开三层转义。写进临时文件再喂给 `gh` 可以整类绕开：

```bash
cat > /tmp/pr-body.md <<'EOF'
- 具体变更
- 具体变更

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
gh pr create --base master --head <branch> --title "<type>(<scope>): <摘要>" --body-file /tmp/pr-body.md
```

heredoc 用 `<<'EOF'`（**引号必须有**），这样 `$`、反引号、`<` `>` 全部按字面写入，不被 shell 解释。

**第 2 步的 PR 内容：** title 取 commit 摘要行，body 取 commit 正文，结尾加 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`。该尾注**只进 PR body，不进** squash 后的 commit message。

**第 3 步等的五个必需检查**（名字逐字，同时被 `.github/workflows/ci.yml` 与服务端 ruleset 引用）：`gates-hooks`、`gates-tests`、`gates-data`、`plugin-validate`、`new-skill-eval-case`。

`gh pr checks` 的**退出码就是判据**，不要去读它的人类可读输出：

| 退出码 | 含义 | 处置 |
|---|---|---|
| 0 | 全部通过 | 进第 4 步 |
| 8 | 仍有 pending | 加了 `--watch` 时不会返回 8（它会一直等到结束）；裸跑返回 8 说明还在跑 |
| 4 | 需要认证 | 本步之前的 CHECKPOINT 应已拦住；此处出现说明 token 中途失效，🔴 停下报告 |
| 1 | 有失败 | 🔴 停下报告，见下 |

⚠️ **必须带 `--required`**：不加它会把非必需的检查也算进去，某个可选 job 红了就误判为「CI 失败」。`--fail-fast` 让第一个检查失败时立刻退出，不必等完剩下四个。

🔴 **第 3 步出现失败检查时：停下报告，不自动重试、不自动改代码。** CI 红说明门禁真的拦到了东西，与第四步 `pre-commit` 阻断时「禁止绕过」的处置同构。取证路径：

```bash
gh pr checks <branch> --required --json name,bucket,link
gh run view <run-id> --log-failed    # run-id 取自上一条输出的 link 末段
```

`bucket` 字段把各种 `state` 归并成 `pass`/`fail`/`pending`/`skipping`/`cancel` 五类，比裸读 `state` 少一层映射。

⚠️ **绿灯本身不等于「查过了」。** 五项里 `plugin-validate` 是增量的：只改 `docs/` 的 PR 上它会打印 `Changed external entries: 0` 与 `Changed in-repo plugin folders: []`，然后 30/40/41 三步全部 `skipping`——绿灯此时几乎不携带关于插件的信息。改动落在 `plugins/` 时才是它发挥作用的时候，那时应能在日志里看到被命中的插件目录名。

🔴 **第 4 步必须显式传 `--subject` 与 `--body-file`**，两处各有一个静默失效形态：

| 漏传 | 后果 |
|---|---|
| `--body-file`（或 `-b`） | GitHub 用 PR body 生成 message，**特性分支 commit 里的 `Co-Authored-By` 尾注不会进入 squash 后的 commit**——主干上的 AI 协作者标注从此静默消失 |
| `--subject` 里的 `(#N)` | **显式传 `--subject` 时 GitHub 不再自动追加 `(#N)` 后缀**。漏了会让主干 log 分成「带 PR 号」与「不带」两种 |

因此 `--subject` 写成 `<type>(<scope>): <摘要> (#N)`，`--body-file` 指向的文件原样带上 commit 正文与 `Co-Authored-By` 尾注、**不带**那条 `🤖 Generated with` 尾注。PR 号从第 2 步 `gh pr create` 的输出 URL 末段取，或 `gh pr view <branch> --json number --jq .number`。

🔴 **`Co-Authored-By` 的尖括号必须是原始 `<` `>`，不得被转义成 HTML 实体 `&lt;` `&gt;`。** 这是最隐蔽的一类失效：尾注在文本上看着还在，但邮箱不是合法的 `<email>` 形态，**GitHub 不会把它识别为 co-author**，`gh pr merge` 也照样返回成功。用上面的 `<<'EOF'` heredoc 写文件不会产生这种转义，但**手工拼串或从网页复制时会**。合并后立刻自检：

```bash
git switch master && git pull --rebase origin master
git log -1 --format=%B | git interpret-trailers --parse
```

Expected: 输出 `Co-Authored-By: <模型名> <noreply@anthropic.com>`，尖括号是**真尖括号**。

🔴 **一旦写坏就无法修复**：改已在 `master` 上的 commit message 只能靠 force push，而 ruleset 的 `non_fast_forward` 会服务端硬拒。**所以这条自检必须在合并后立刻做，但它只能用于「知道自己写坏了」，不能用于「修好它」**——真正的防线是传参时就不转义。

⚠️ **第 6 步的顺序是硬约束：先删本地、后删远端。**

| 顺序 | `git branch -d` 的结果 |
|---|---|
| **先本地、后远端**（本 skill 采用） | ✅ 成功，只给一行 warning：`… has been merged to refs/remotes/origin/<branch>, but not yet merged to HEAD` |
| 先远端、后本地 | ❌ 拒绝，报 `not fully merged` |

机制是 **`-d` 的「已合并」判定不只看 HEAD，也看远端追踪引用**。顺序正确时 `origin/<branch>` 仍存在且与本地同 commit，判定通过；先删远端则该引用消失，判定只能对 HEAD 做，而 squash 产生的是一个**全新的 commit 对象**、特性分支的 commit 从未成为它的祖先，按可达性确实「未合并」。

🔴 **万一顺序反了、`-d` 已被拒，不能因此改用 `-D`**：`-D` 对「真的没合进去」和「合进去了但换了对象」一视同仁，用它等于放弃判断。正确判据是**比对树对象**：

```bash
git rev-parse <branch>^{tree}   # 与
git rev-parse master^{tree}     # 相等 ⇒ 内容已完整落地，再 -D
```

树对象相等意味着两边文件内容逐字节一致，这正是「已合并」在 squash 语境下的实质含义。

### 不用 `gh pr merge --auto`

`gh` 支持原生 auto-merge（`--auto`，走 `enablePullRequestAutoMerge` mutation），但**本仓库在 GitHub 上没有开启该功能**（`allow_auto_merge: false`，2026-09-18 实测），传 `--auto` 会被服务端拒绝。因此上表用「`--watch` 等待 + 显式 merge」达到同样的最终状态。实质差异只有一处：

| | 原生 auto-merge | 本流程 |
|---|---|---|
| 会话在等 CI 期间中断 | GitHub 在服务端继续等，CI 绿后自行合并 | PR 停在未合并状态，**需下次触发本 skill 时接续**（第一步 CHECKPOINT 的第二支） |

想消除这个差异需要先在仓库设置里打开 Allow auto-merge——那是一次性的仓库配置变更，**不在本 skill 的职责内，不要顺手去改**。接续逻辑本来就必须存在（CI 变红同样会让流程停在中途）。

### 工作区不干净

**工作区不干净**——第一步 CHECKPOINT 明确允许把无关改动排除在本次提交外，被排除的文件就留在工作区，第 5 步的 `git pull --rebase` 会被它们挡住。**越是按第一步规范排除了无关文件，越必然撞上这个失败**。

不要为了让 rebase 通过就把无关文件一并提交——那会破坏第二步刚校验过的原子性。正确做法是只把它们临时挪走：

```bash
git stash push -m "commit-cc-plugin: 临时挪走无关改动" <排除的文件路径...>
git switch master && git pull --rebase origin master
git stash pop
```

⚠️ `git stash push` 必须**列出具体文件路径**，不加路径的裸 `git stash` 会把工作区全部改动一起挪走，`pop` 时若遇冲突更难还原。必须 `git stash pop` 原样恢复，不要留在 stash 里——用户会以为改动丢了。

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
| `git push origin master` 直推主干 | 主干已开保护，直推被 `GH013` 拒绝。走第五步的「分支 → PR → CI → squash merge」 |
| `gh pr merge` 不传 `--body-file` | squash 会丢掉 `Co-Authored-By`，主干上的 AI 协作者标注静默消失（第五步第 4 步） |
| 用 `--body` 传含换行的多行文本 | 要同时对付 shell 的引号、反引号与 `$` 展开三层转义。用 `<<'EOF'` heredoc 写临时文件 + `--body-file` |
| `Co-Authored-By` 的 `<>` 变成 `&lt;` `&gt;` | 尾注看着还在，但不是合法 `<email>` 形态，GitHub 不识别为 co-author，且**合并后无法修复**（改 master 的 message 需 force push，被 ruleset 硬拒）。合并后立刻 `git interpret-trailers --parse` 自检 |
| `--subject` 不带 `(#N)` | 显式传 `--subject` 时 GitHub 不再自动追加 PR 号，主干 log 会分成两种风格 |
| `gh pr checks` 不带 `--required` | 会把非必需检查也算进来，某个可选 job 红了就误判为 CI 失败 |
| 读 `gh pr checks` 的人类可读输出判断状态 | 判据是**退出码**：0 全绿、8 pending、1 有失败 |
| 清分支时先删远端 | `git branch -d` 的已合并判定也看远端追踪引用，反了会报 `not fully merged`。顺序：先本地、后远端 |
| `-d` 被拒就改用 `-D` | `-D` 对「真没合」与「合了但换了对象」一视同仁。先比 `<branch>^{tree}` 与 `master^{tree}`，相等才 `-D` |
| 会话中途发现忘了建分支，就推翻重做 | `git switch -c <分支>` 后 `git branch -f master origin/master` 即可无损搬运（「第三步之后」小节） |
