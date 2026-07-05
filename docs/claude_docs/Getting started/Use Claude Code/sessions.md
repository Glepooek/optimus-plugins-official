# 管理会话

> 命名、恢复、分支，以及在 Claude Code 对话之间切换。涵盖 `--continue`、`--resume`、`--from-pr`、`/resume` 选择器、会话命名，以及对话记录的存储位置。

来源：[code.claude.com/docs/en/sessions](https://code.claude.com/docs/en/sessions)

---

会话是与某个项目目录绑定的已保存对话。Claude Code 在你工作时持续将其保存到本地，以便从上次离开的地方继续、分支出新路径尝试不同方案，或在任务之间切换。

[桌面应用](https://code.claude.com/docs/en/desktop#work-in-parallel-with-sessions)、[网页版 Claude Code](https://code.claude.com/docs/en/claude-code-on-the-web) 和 [VS Code 扩展](https://code.claude.com/docs/en/vs-code#resume-past-conversations)各自维护独立的会话历史。本页介绍 CLI 的用法：

- [恢复](#恢复会话)：通过标志、名称或 PR 恢复历史对话
- [命名](#命名会话)：给会话取名以便后续查找
- [浏览](#使用会话选择器)：通过 `/resume` 选择器浏览会话
- [分支](#分支会话)：复制当前对话以尝试不同方案
- [导出](#导出与定位会话数据)：导出对话记录并找到其在磁盘上的位置

---

## 恢复会话

会话在你工作时持续保存到[本地记录文件](#导出与定位会话数据)，因此在退出或运行 `/clear` 后可以随时回来继续。可使用以下入口：

| 命令 | 作用 |
|:-----|:-----|
| `claude --continue` | 恢复当前目录中最近的会话 |
| `claude --resume` | 打开[会话选择器](#使用会话选择器) |
| `claude --resume <name>` | 直接恢复指定名称的会话 |
| `claude --from-pr <number>` | 恢复与该 pull request 关联的会话 |
| `/resume` | 在活动会话内切换到另一个对话 |

通过 [`claude -p`](https://code.claude.com/docs/en/headless) 或 [Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) 创建的会话不会出现在会话选择器中，但你仍然可以将其 session ID 传给 `claude --resume <session-id>` 来恢复。请在创建该会话时所在的目录中运行此命令：session ID 查找的范围限定在当前项目目录及其 git worktree，因此在其他地方创建的会话会报告 `No conversation found with session ID: <session-id>`。

### 会话选择器的查找范围

会话按项目目录存储。默认情况下，会话选择器显示当前 worktree 中的交互式会话，以及在其他地方通过 `/add-dir` 添加了当前目录的会话。从 v2.1.169 起，通过 [`/cd`](https://code.claude.com/docs/en/commands) 移动会话会将其迁移到新目录的项目存储中，之后它会出现在该目录的选择器里。使用 `Ctrl+W` 可扩展到该仓库的所有 worktree，`Ctrl+A` 可扩展到本机上的每个项目。

从同一仓库的其他 worktree 选择会话时，会就地恢复。从不相关项目选择会话时，系统会将 `cd` 和恢复命令复制到剪贴板。

按名称恢复时，查找范围涵盖当前仓库及其所有 worktree。两种形式均会查找精确匹配，即使会话在不同 worktree 中也会直接恢复：

| 命令 | 精确匹配 | 名称歧义 |
|:-----|:---------|:---------|
| `claude --resume <name>` | 直接恢复 | 打开会话选择器，并将名称预填为搜索词 |
| `/resume <name>` | 直接恢复 | 报告错误；运行不带参数的 `/resume` 打开选择器 |

---

## 命名会话

给会话取描述性名称，以便在选择器中找到并通过名称恢复。这在并行处理多个任务时尤为重要。

| 时机 | 设置方式 |
|:-----|:---------|
| 启动时 | `claude -n auth-refactor` |
| 会话进行中 | `/rename auth-refactor`，名称也会显示在提示栏上 |
| 在会话选择器中 | 高亮选中会话后按 `Ctrl+R` |
| 接受计划时 | 在[计划模式](https://code.claude.com/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)中接受计划，会从计划内容自动命名会话（前提是尚未手动命名） |

会话命名后，可通过 `claude --resume <name>` 或 `/resume <name>` 返回。跨 worktree 的名称解析行为详见[恢复会话](#恢复会话)。

---

## 使用会话选择器

在会话内运行 `/resume`，或不带参数运行 `claude --resume`，即可打开交互式会话选择器。使用以下快捷键导航、搜索和扩展列表：

| 快捷键 | 操作 |
|:-------|:-----|
| `↑` / `↓` | 在会话之间导航 |
| `→` / `←` | 展开或折叠分组会话 |
| `Enter` | 恢复高亮的会话 |
| `Space` | 预览会话内容（在不拦截粘贴的终端上，`Ctrl+V` 也有效） |
| `Ctrl+R` | 重命名高亮的会话 |
| `/` 或任意可打印字符（除 `Space`） | 进入搜索模式并过滤会话；粘贴 GitHub、GitHub Enterprise、GitLab 或 Bitbucket 的 PR/MR URL 可找到创建该会话的记录 |
| `Ctrl+A` | 显示本机上所有项目的会话，再次按下返回当前仓库 |
| `Ctrl+W` | 显示当前仓库所有 worktree 的会话，再次按下返回当前 worktree（仅在多 worktree 仓库中显示） |
| `Ctrl+B` | 过滤为当前 git 分支的会话，再次按下显示所有分支 |
| `Esc` | 退出会话选择器或搜索模式 |

每一行显示会话名称（若已设置），否则显示对话摘要或第一条提示词，以及距最后活动时间、消息数量和 git 分支。使用 `Ctrl+A` 扩展到所有项目后，行中还会显示项目路径。

通过 `/branch`、`/rewind` 或 `--fork-session` 创建的分支会话会归组到其根会话下。按 `→` 展开分组。

---

## 分支会话

分支会复制目前为止的对话并切换进去，保持原始会话不变。当你想尝试不同方案而又不想丢失当前路径时使用。

在会话内运行 `/branch`，可附加可选的名称：

```text
/branch try-streaming-approach
```

从命令行，将 `--continue` 或 `--resume` 与 `--fork-session` 组合：

```bash
claude --continue --fork-session
```

原始会话不受影响，仍可在会话选择器中找到。`/branch` 确认信息会打印两个 session ID：你当前所在的新分支，以及原始会话。要返回原始会话，可将其 ID 传给 `/resume`，使用会话选择器，或运行 `/resume <original-name>`。在原始会话中以"本次会话允许"批准的权限不会延续到新分支。如果你在两个终端中不分支地恢复同一会话，两边的消息会交织进同一份记录。

关于单个会话内基于检查点的回退，参见[检查点](https://code.claude.com/docs/en/checkpointing)。

---

## 管理会话内的上下文

以下命令可在不离开会话的情况下控制上下文窗口中的内容：

- **`/clear`**：以空上下文重新开始，先前的对话已保存且可恢复
- **`/compact [instructions]`**：用摘要替换历史记录，可选择性地指定摘要重点
- **`/context`**：显示当前占用上下文的内容

关于压缩如何与 CLAUDE.md、skills 和规则交互，参见[上下文窗口指南](https://code.claude.com/docs/en/context-window)。关于何时清空与压缩的策略，参见[最佳实践](https://code.claude.com/docs/en/best-practices#manage-your-session)。

---

## 导出与定位会话数据

运行 `/export` 可将当前对话复制到剪贴板或保存为纯文本文件，消息和工具输出以可读文本格式呈现。传入文件名可直接写入该文件。

记录文件以 JSONL 格式存储在 `~/.claude/projects/<project>/<session-id>.jsonl`，其中 `<project>` 从你的工作目录路径派生。每行是一个 JSON 对象，代表一条消息、一次工具调用或一条元数据。要将会话存储在 `~/.claude` 以外的位置，设置 [`CLAUDE_CONFIG_DIR`](https://code.claude.com/docs/en/env-vars)。这些本地文件默认在 30 天后删除；通过 [`cleanupPeriodDays`](https://code.claude.com/docs/en/settings#available-settings) 可修改此设置。

要完全禁止写入记录文件，设置 [`CLAUDE_CODE_SKIP_PROMPT_HISTORY`](https://code.claude.com/docs/en/env-vars)；在非交互模式下则使用 `--no-session-persistence`。

---

## 另见

以下页面涵盖相关的会话与并行机制：

- [Worktrees](https://code.claude.com/docs/en/worktrees)：在独立分支上运行隔离的并行会话
- [检查点](https://code.claude.com/docs/en/checkpointing)：将代码和对话回退到更早的时间点
- [上下文窗口](https://code.claude.com/docs/en/context-window)：什么内容填充上下文，什么内容在压缩后保留
- [非交互模式](https://code.claude.com/docs/en/headless)：`claude -p` 下的会话行为
