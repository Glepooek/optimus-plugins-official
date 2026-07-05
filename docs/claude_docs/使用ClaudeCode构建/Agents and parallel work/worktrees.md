---
source: https://code.claude.com/docs/en/worktrees
---

# 使用工作树运行并行会话

> 将并行 Claude Code 会话隔离在独立的 git 工作树中，避免变更冲突。涵盖 `--worktree` 标志、子智能体隔离、`.worktreeinclude`、清理方式及非 git VCS hook。

[git 工作树](https://git-scm.com/docs/git-worktree)是一个独立的工作目录，拥有自己的文件和分支，与主检出共享同一仓库历史和远端。将每个 Claude Code 会话运行在各自的工作树中，意味着一个会话中的编辑不会影响另一个会话的文件，因此你可以在一个终端让 Claude 开发功能，同时在另一个终端修复 bug。

本页介绍 CLI 中的工作树隔离。以下内容均假设使用 git 仓库。对于其他版本控制系统，参见[非 git 版本控制](#non-git-version-control)。[桌面应用](https://code.claude.com/docs/en/desktop#work-in-parallel-with-sessions)会自动为每个新会话创建工作树。

工作树是并行运行 Claude 的多种方式之一。它们隔离文件编辑，而[子智能体](https://code.claude.com/docs/en/sub-agents)和[智能体团队](https://code.claude.com/docs/en/agent-teams)负责协调工作本身。参见[并行运行智能体](https://code.claude.com/docs/en/agents)来对比各种方式，或直接跳转至[使用工作树隔离子智能体](#isolate-subagents-with-worktrees)了解如何将工作树与子智能体结合使用。

## 在工作树中启动 Claude

传入 `--worktree` 或 `-w` 可创建一个隔离的工作树并在其中启动 Claude。默认情况下，工作树创建在仓库根目录的 `.claude/worktrees/<值>/` 下，对应的新分支名为 `worktree-<值>`：

```bash theme={null}
claude --worktree feature-auth
```

要将工作树放在其他位置，可配置 [`WorktreeCreate` hook](#non-git-version-control)。在另一个终端中以不同名称再次运行该命令，即可启动第二个隔离会话：

```bash theme={null}
claude --worktree bugfix-123
```

省略名称时，Claude 会自动生成一个，例如 `bright-running-fox`：

```bash theme={null}
claude --worktree
```

你也可以在会话中让 Claude "在工作树中工作"，它会通过 [`EnterWorktree`](https://code.claude.com/docs/en/tools-reference) 工具创建一个工作树。进入工作树后，Claude 可以调用 `EnterWorktree` 并传入目标路径，直接切换到 `.claude/worktrees/` 下的另一个工作树，之前的工作树会原样保留在磁盘上。

在某个目录首次交互式使用 `--worktree` 之前，需要先在该目录运行 `claude` 一次来接受工作区信任对话框。若尚未接受信任，`--worktree` 会报错并提示你先在该目录运行 `claude`。使用 `-p` 的非交互式运行会跳过[信任检查](https://code.claude.com/docs/en/security)，因此 `claude -p --worktree` 无需该步骤即可执行。

> **提示：** 将 `.claude/worktrees/` 添加到 `.gitignore`，这样工作树内容就不会在主检出中显示为未追踪文件。

### 选择基础分支

工作树从仓库的默认分支 `origin/HEAD` 创建分支，因此初始状态与远端保持一致。若未配置远端或抓取失败，工作树会回退至本地当前的 `HEAD`。若要始终从本地 `HEAD` 创建分支，可在[设置](https://code.claude.com/docs/en/settings#worktree-settings)中将 `worktree.baseRef` 设为 `"head"`。将 `baseRef` 设为 `"head"` 会使新工作树携带你未推送的提交和功能分支状态，适用于需要基于进行中工作运行的子智能体隔离场景。该设置仅接受 `"fresh"` 或 `"head"`，不支持任意 git 引用：

```json theme={null}
{
  "worktree": {
    "baseRef": "head"
  }
}
```

要从特定 Pull Request 创建分支，可传入以 `#` 开头的 PR 编号，或完整的 GitHub Pull Request URL。Claude Code 会从 `origin` 拉取 `pull/<编号>/head` 并在 `.claude/worktrees/pr-<编号>` 处创建工作树：

```bash theme={null}
claude --worktree "#1234"
```

若需完全控制工作树的创建方式，可配置 [`WorktreeCreate` hook](https://code.claude.com/docs/en/hooks#worktreecreate)，该 hook 会完全替换默认的 `git worktree` 逻辑。

## 将 gitignore 的文件复制到工作树

工作树是全新的检出，因此主仓库中 `.env` 或 `.env.local` 等未追踪文件不会存在于工作树中。要在 Claude 创建工作树时自动复制这些文件，可在项目根目录添加 `.worktreeinclude` 文件。

该文件使用 `.gitignore` 语法。只有匹配某个模式且同时被 gitignore 的文件才会被复制，因此已追踪的文件不会重复。

以下 `.worktreeinclude` 示例会将两个 env 文件和一个 secrets 配置文件复制到每个新工作树中：

```text .worktreeinclude theme={null}
.env
.env.local
config/secrets.json
```

此规则适用于通过 `--worktree` 创建的工作树、[子智能体工作树](#isolate-subagents-with-worktrees)以及[桌面应用](https://code.claude.com/docs/en/desktop#work-in-parallel-with-sessions)中的并行会话。

## 使用工作树隔离子智能体

子智能体可以在各自的工作树中运行，从而避免并行编辑冲突。让 Claude "为你的智能体使用工作树"，或在[自定义子智能体](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields)的 frontmatter 中添加 `isolation: worktree` 来永久设置。每个子智能体会获得一个临时工作树，子智能体完成且无变更时自动删除。

子智能体工作树与 `--worktree` 使用相同的[基础分支](#choose-the-base-branch)，因此除非将 `worktree.baseRef` 设为 `"head"`，否则它们均从仓库的默认分支创建分支。

## 清理工作树

退出工作树会话时，清理行为取决于是否有变更：

* **无未提交变更、无未追踪文件、无新提交**：工作树及其分支自动删除。若会话有[名称](https://code.claude.com/docs/en/sessions#name-your-sessions)，Claude 会改为提示以便你保留工作树供后续使用
* **存在未提交变更、未追踪文件或新提交**：Claude 会提示你选择保留或删除工作树。保留会保存目录和分支以便日后回访；删除会清除工作树目录及其分支，丢弃所有未提交变更、未追踪文件和提交
* **非交互式运行**：与 `-p` 一同使用 `--worktree` 创建的工作树不会自动清理，因为没有退出提示。可通过 `git worktree remove` 手动删除

Claude 为子智能体和[后台会话](https://code.claude.com/docs/en/agent-view#how-file-edits-are-isolated)创建的工作树，在超过 [`cleanupPeriodDays`](https://code.claude.com/docs/en/settings#available-settings) 设置的天数后，若无未提交变更、未追踪文件和未推送提交，则自动删除。通过 `--worktree` 创建的工作树不受此清理机制影响。

智能体运行期间，Claude 会对其工作树执行 `git worktree lock`，防止并发清理将其删除。智能体完成后锁定解除。若清理机制持续跳过某个工作树，可运行 `git worktree remove` 手动删除，若工作树存在未提交变更或未追踪文件则加上 `--force`。

## 手动管理工作树

若需完全控制工作树位置和分支配置，可直接用 Git 创建工作树。适用于需要检出特定已有分支或将工作树放在仓库外部的场景。

在新分支上创建工作树：

```bash theme={null}
git worktree add ../project-feature-a -b feature-a
```

从已有分支创建工作树：

```bash theme={null}
git worktree add ../project-bugfix bugfix-123
```

在工作树中启动 Claude：

```bash theme={null}
cd ../project-feature-a && claude
```

列出所有工作树：

```bash theme={null}
git worktree list
```

完成后删除某个工作树：

```bash theme={null}
git worktree remove ../project-feature-a
```

完整命令参考见 [Git 工作树文档](https://git-scm.com/docs/git-worktree)。记得在每个新工作树中初始化开发环境：安装依赖、设置虚拟环境，或执行项目所需的任何初始化步骤。

## 非 git 版本控制

工作树隔离默认使用 git。对于 SVN、Perforce、Mercurial 或其他系统，可配置 [`WorktreeCreate` 和 `WorktreeRemove` hook](https://code.claude.com/docs/en/hooks#worktreecreate) 来提供自定义的创建和清理逻辑。由于该 hook 会替换默认 git 行为，使用 `--worktree` 时不会处理 [`.worktreeinclude`](#copy-gitignored-files-into-worktrees)，请在 hook 脚本中自行复制所需的本地配置文件。

以下 `WorktreeCreate` hook 从 stdin 读取工作树名称，检出一个新的 SVN 工作副本，并打印目录路径以便 Claude Code 将其作为会话的工作目录：

```json theme={null}
{
  "hooks": {
    "WorktreeCreate": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'NAME=$(jq -r .name); DIR=\"$HOME/.claude/worktrees/$NAME\"; svn checkout https://svn.example.com/repo/trunk \"$DIR\" >&2 && echo \"$DIR\"'"
          }
        ]
      }
    ]
  }
}
```

配合 `WorktreeRemove` hook 在会话结束时执行清理。输入 schema 和删除示例参见 [hook 参考文档](https://code.claude.com/docs/en/hooks#worktreecreate)。

## 另见

工作树负责文件隔离。以下相关页面介绍如何将工作委派到这些隔离的检出中，以及如何在创建的会话间切换：

* [子智能体](https://code.claude.com/docs/en/sub-agents)：在会话内将工作委派给隔离的智能体
* [智能体团队](https://code.claude.com/docs/en/agent-teams)：自动协调多个 Claude 会话
* [管理会话](https://code.claude.com/docs/en/sessions)：命名、恢复和切换对话
* [桌面应用并行会话](https://code.claude.com/docs/en/desktop#work-in-parallel-with-sessions)：桌面应用中基于工作树的并行会话
