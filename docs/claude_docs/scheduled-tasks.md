# 按计划运行提示词

> 使用 `/loop` 和 cron 调度工具重复运行提示词、轮询状态，或在 Claude Code 会话内设置一次性提醒。

来源：[code.claude.com/docs/en/scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks)

---

> **注意：**
> 计划任务需要 Claude Code v2.1.72 或更高版本。用 `claude --version` 检查你的版本。

计划任务（Scheduled tasks）让 Claude 按固定间隔自动重新运行一个提示词。可以用它来轮询某次部署、盯着一个 PR、检查一个长时间运行的构建，或者提醒自己在会话稍后的时间做某件事。如果你想在事件发生时立即响应，而不是轮询，参见 [Channels](https://code.claude.com/docs/en/channels)：你的 CI 可以把失败结果直接推送到会话中。如果你想让会话一轮接一轮持续工作直到某个条件满足，而不是按固定间隔运行，参见 [`/goal`](https://code.claude.com/docs/en/goal)。

任务是会话范围的（session-scoped）：它们存在于当前对话中，当你开启新对话时就会停止。用 `--resume` 或 `--continue` 恢复会话会带回任何尚未[过期](#seven-day-expiry)的任务：创建于最近 7 天内的循环任务，或者计划触发时间尚未到达的一次性任务。如果需要独立于任何会话持续存在的调度，可以使用 [Routines](https://code.claude.com/docs/en/routines) 在 Anthropic 托管的基础设施上创建例行任务，设置[桌面端计划任务](https://code.claude.com/docs/en/desktop-scheduled-tasks)，或使用 [GitHub Actions](https://code.claude.com/docs/en/github-actions)。

## 对比调度方式

Claude Code 提供三种方式来调度重复性或一次性的工作：

|                            | [云端](https://code.claude.com/docs/en/routines)          | [桌面端](https://code.claude.com/docs/en/desktop-scheduled-tasks) | [`/loop`](https://code.claude.com/docs/en/scheduled-tasks)      |
| :--- | :--- | :--- | :--- |
| 运行位置                    | Anthropic 云端                | 你的本机                           | 你的本机                        |
| 需要机器开机                | 否                             | 是                                       | 是                                 |
| 需要打开会话                | 否                             | 否                                       | 是                                 |
| 重启后是否持久              | 是                             | 是                                       | 未过期时通过 `--resume` 恢复 |
| 访问本地文件                | 否（全新克隆）               | 是                                       | 是                                 |
| MCP servers                | 按任务配置连接方              | [配置文件](https://code.claude.com/docs/en/mcp) 和连接方 | 继承自会话               |
| 权限确认                    | 否（自主运行）         | 按任务可配置                   | 继承自会话               |
| 可自定义调度                | 通过 CLI 中的 `/schedule`     | 是                                       | 是                                 |
| 最小间隔                    | 1 小时                          | 1 分钟                              | 1 分钟                              |

> **提示：**
> 对于需要在没有你的机器时也可靠运行的工作，使用**云端任务**。当你需要访问本地文件和工具时，使用**桌面端任务**。会话期间的快速轮询，使用 **`/loop`**。

## 用 /loop 重复运行提示词

`/loop` [内置 skill](https://code.claude.com/docs/en/commands) 是在会话保持打开期间重复运行一个提示词最快的方式。间隔和提示词都是可选的，你提供的内容决定了循环的行为。

| 你提供的内容                | 示例                     | 会发生什么                                                                                                  |
| :--- | :--- | :--- |
| 间隔和提示词       | `/loop 5m check the deploy` | 你的提示词按[固定计划](#run-on-a-fixed-interval)运行                                                              |
| 仅提示词               | `/loop check the deploy`    | 你的提示词每次迭代都按 [Claude 选择的间隔](#let-claude-choose-the-interval)运行              |
| 仅间隔，或什么都不提供 | `/loop`                     | 运行[内置的维护提示词](#run-the-built-in-maintenance-prompt)，或者如果存在你自己的 `loop.md` 则运行它 |

你也可以把一个 skill 作为提示词传入，例如 `/loop 20m /review-pr 1234`，让该 skill 每次迭代都重新运行一次。{/* min-version: 2.1.196 */}从 v2.1.196 开始，计划触发只会运行 Claude [被允许自主调用](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill)的 skill。以下几类会作为纯文本发送给 Claude，而不会被执行：

* 内置命令，例如 `/permissions`、`/model` 或 `/clear`
* 标记为 [`disable-model-invocation: true`](https://code.claude.com/docs/en/skills#frontmatter-reference) 的 skill
* 被 [`skillOverrides`](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings) 设置或 `Skill` [拒绝规则](https://code.claude.com/docs/en/skills#restrict-claude’s-skill-access)对 Claude 隐藏的 skill
* [MCP prompts](https://code.claude.com/docs/en/mcp#use-mcp-prompts-as-commands)，例如 `/mcp__github__list_prs`；MCP server 暴露的 skill 仍会正常运行

### 按固定间隔运行

当你提供一个间隔时，Claude 会把它转换成一个 cron 表达式，安排任务，并确认运行节奏和任务 ID。

```text theme={null}
/loop 5m check if the deployment finished and tell me what happened
```

间隔可以作为一个裸词放在提示词前面，比如 `30m`，也可以作为从句跟在后面，比如 `every 2 hours`。支持的单位有：`s` 表示秒、`m` 表示分钟、`h` 表示小时、`d` 表示天。

由于 cron 的最小粒度是一分钟，秒会被向上取整到最近的分钟。像 `7m` 或 `90m` 这类无法对应到一个规整 cron 步长的间隔，会被四舍五入到最近的可用间隔，Claude 会告诉你它选择了哪个值。

### 让 Claude 自行选择间隔

当你省略间隔时，Claude 不会按固定 cron 计划运行，而是动态选择一个间隔。每次迭代结束后，它会根据观察到的情况，在一分钟到一小时之间选择一个延迟：构建即将完成或 PR 处于活跃状态时等待更短，没有待处理事项时等待更长。每次迭代结束时都会打印出所选的延迟以及选择理由。

下面的例子会检查 CI 和评审意见，一旦 PR 安静下来，Claude 会在两次迭代之间等待更长时间：

```text theme={null}
/loop check whether CI passed and address any review comments
```

当你要求一个动态调度的 `/loop` 时，Claude 可能会直接使用 [Monitor 工具](https://code.claude.com/docs/en/tools-reference#monitor-tool)。Monitor 会在后台运行一个脚本，并把每一行输出实时传回，这完全避免了轮询，通常比按间隔重复运行一个提示词更省 token、响应也更及时。

一个动态调度的循环会像其他任务一样出现在你的[计划任务列表](#manage-scheduled-tasks)中，因此你可以用同样的方式列出或取消它。[抖动规则](#jitter)不适用于它，但[七天过期规则](#seven-day-expiry)适用：这个循环会在你启动它七天后自动结束。

> **注意：**
> 在 Amazon Bedrock、Google Cloud 的 Agent Platform 以及 Microsoft Foundry 上，没有指定间隔的提示词会改为按固定的 10 分钟计划运行。

### 运行内置的维护提示词

当你省略提示词时，Claude 会使用一个内置的维护提示词，而不是你提供的提示词。每次迭代它都会按顺序处理以下内容：

* 继续对话中任何未完成的工作
* 处理当前分支的 pull request：评审意见、失败的 CI 运行、合并冲突
* 当没有其他待处理事项时，运行清理性的检查，比如查找 bug 或简化代码

Claude 不会在这个范围之外发起新的工作，而像推送或删除这样不可逆的操作，只有在对话记录已经明确授权的延续动作中才会执行。

```text theme={null}
/loop
```

一个裸 `/loop` 会以[动态选择的间隔](#let-claude-choose-the-interval)运行这个提示词。加上一个间隔，比如 `/loop 15m`，则会改为按固定计划运行。要用你自己的默认提示词替换内置提示词，参见[用 loop.md 自定义默认提示词](#customize-the-default-prompt-with-loop-md)。

> **注意：**
> 在 Amazon Bedrock、Google Cloud 的 Agent Platform 以及 Microsoft Foundry 上，不带提示词的 `/loop` 会打印用法说明，而不会运行维护提示词。

### 用 loop.md 自定义默认提示词

`loop.md` 文件会用你自己的指令替换内置的维护提示词。它为裸 `/loop` 定义了单一的默认提示词，而不是一份独立计划任务的列表，并且只要你在命令行中提供了提示词，它就会被忽略。要在它之外调度更多提示词，使用 `/loop <prompt>` 或[直接让 Claude 处理](#manage-scheduled-tasks)。

Claude 会在两个位置查找该文件，并使用第一个找到的位置。

| 路径                | 作用范围                                                            |
| :--- | :--- |
| `.claude/loop.md`   | 项目级。两个文件都存在时优先生效。           |
| `~/.claude/loop.md` | 用户级。适用于没有定义自己文件的任何项目。 |

这个文件是纯 Markdown，没有必须遵循的结构。把它写得就像你在直接输入 `/loop` 的提示词一样。下面的例子用来保持一个发布分支的健康状态：

```markdown title=".claude/loop.md" theme={null}
Check the `release/next` PR. If CI is red, pull the failing job log,
diagnose, and push a minimal fix. If new review comments have arrived,
address each one and resolve the thread. If everything is green and
quiet, say so in one line.
```

对 `loop.md` 的修改会在下一次迭代时生效，因此你可以在循环运行期间调整指令。当两个位置都不存在 `loop.md` 时，循环会回退到内置的维护提示词。保持文件精简：超过 25,000 字节的内容会被截断。

> **注意：**
> 在 Amazon Bedrock、Google Cloud 的 Agent Platform 以及 Microsoft Foundry 上，`loop.md` 不会被读取，不带提示词的 `/loop` 会打印用法说明。

### 停止一个循环

要在 `/loop` 等待下一次迭代期间停止它，按 `Esc`。这会清除待触发的下一次唤醒，循环就不会再次触发。通过[直接让 Claude 处理](#manage-scheduled-tasks)方式调度的任务不受 `Esc` 影响，会一直保留，直到你删除它们。

在[自主节奏模式](#let-claude-choose-the-interval)下，一旦任务已被证实完成，Claude 也可以通过不再调度下一次唤醒来自行结束循环。按固定间隔运行的循环会一直运行，直到你停止它，或者[七天过后](#seven-day-expiry)。

## 设置一次性提醒

对于一次性提醒，用自然语言描述你想要的内容，而不是使用 `/loop`。Claude 会调度一个单次触发的任务，运行后自行删除。

```text theme={null}
remind me at 3pm to push the release branch
```

```text theme={null}
in 45 minutes, check whether the integration tests passed
```

Claude 会用一个 cron 表达式把触发时间固定到具体的分钟和小时，并确认它将在何时触发。

## 管理计划任务

用自然语言让 Claude 列出或取消任务，或者直接引用底层工具。

```text theme={null}
what scheduled tasks do I have?
```

```text theme={null}
cancel the deploy check job
```

在底层，Claude 使用以下工具：

| 工具         | 用途                                                                                                         |
| :--- | :--- |
| `CronCreate` | 调度一个新任务。接受一个 5 字段 cron 表达式、要运行的提示词，以及它是重复运行还是只运行一次。 |
| `CronList`   | 列出所有计划任务，包括它们的 ID、调度计划和提示词。                                                                  |
| `CronDelete` | 按 ID 取消一个任务。                                                                                            |

每个计划任务都有一个 8 个字符的 ID，可以传给 `CronDelete`。一个会话最多可以同时持有 50 个计划任务。

## 计划任务如何运行

调度器每秒检查一次到期的任务，并将其以低优先级入队。计划中的提示词会在你的两轮对话之间触发，而不是在 Claude 正在响应的过程中。如果任务到期时 Claude 正忙，提示词会等到当前这一轮结束后再触发。

所有时间都按你的本地时区解释。像 `0 9 * * *` 这样的 cron 表达式，表示的是运行 Claude Code 所在地的上午 9 点，而不是 UTC 时间。

### 抖动（Jitter）

为了避免每个会话在同一个时钟时刻同时命中 API，调度器会为触发时间添加一个确定性的偏移量：

* 循环任务最多会在计划时间之后 30 分钟内触发（对于运行频率高于每小时一次的任务，则最多是间隔的一半）。一个计划在 `:00` 触发的每小时任务，可能会在 `:30` 之前的任意时刻触发。
* 计划在整点或半点触发的一次性任务，会提前最多 90 秒触发。

这个偏移量是根据任务 ID 推算出来的，所以同一个任务总会得到相同的偏移量。如果精确的时间点很重要，选一个不是 `:00` 或 `:30` 的分钟，比如用 `3 9 * * *` 代替 `0 9 * * *`，这样一次性任务的抖动就不会生效。

### 七天过期

循环任务会在创建 7 天后自动过期。任务会最后触发一次，然后自行删除。这限制了一个被遗忘的循环最长能运行多久。如果你需要一个循环任务持续更久，请在它过期之前取消并重新创建它，或者使用 [Routines](https://code.claude.com/docs/en/routines) 或[桌面端计划任务](https://code.claude.com/docs/en/desktop-scheduled-tasks)来实现持久化调度。

## Cron 表达式参考

`CronCreate` 接受标准的 5 字段 cron 表达式：`分钟 小时 日 月 星期`。所有字段都支持通配符（`*`）、单个值（`5`）、步长（`*/15`）、范围（`1-5`）以及逗号分隔的列表（`1,15,30`）。

| 示例        | 含义                      |
| :--- | :--- |
| `*/5 * * * *`  | 每 5 分钟一次              |
| `0 * * * *`    | 每小时整点一次       |
| `7 * * * *`    | 每小时第 7 分钟一次 |
| `0 9 * * *`    | 每天本地时间上午 9 点     |
| `0 9 * * 1-5`  | 工作日本地时间上午 9 点        |
| `30 14 15 3 *` | 3 月 15 日本地时间下午 2:30     |

星期字段用 `0` 或 `7` 表示周日，`6` 表示周六。不支持扩展语法，比如 `L`、`W`、`?`，以及像 `MON` 或 `JAN` 这样的名称别名。

当日和星期字段同时被约束时，只要其中一个字段匹配，日期就算匹配。这遵循标准的 vixie-cron 语义。

## 禁用计划任务

在环境变量中设置 `CLAUDE_CODE_DISABLE_CRON=1` 可以完全禁用调度器。cron 工具和 `/loop` 将变得不可用，任何已经计划好的任务都会停止触发。完整的禁用标志列表参见[环境变量](https://code.claude.com/docs/en/env-vars)。

## 限制

会话范围的调度存在一些固有的限制：

* 任务只有在 Claude Code 运行且处于空闲状态时才会触发。关闭终端或让会话退出会导致任务不再触发。[将会话转入后台](https://code.claude.com/docs/en/agent-view#from-inside-a-session)会把 `/loop` 任务带入一个后台会话，这个会话即使没有终端也会持续运行。
* 不会补跑错过的触发。如果一个任务的计划时间在 Claude 正忙于处理一个长时间请求时过去了，它只会在 Claude 空闲下来时触发一次，而不是每错过一个间隔就补触发一次。
* 开启一个新对话会清除所有会话范围的任务。用 `claude --resume` 或 `claude --continue` 恢复会话，会恢复那些尚未过期的任务：创建于七天内的循环任务，以及计划时间尚未到达的一次性任务。后台 Bash 任务和 monitor 任务在恢复时永远不会被恢复。

对于需要无人值守运行的 cron 驱动自动化：

* [Routines](https://code.claude.com/docs/en/routines)：在 Anthropic 托管的基础设施上，按计划、通过 API 调用或响应 GitHub 事件运行
* [GitHub Actions](https://code.claude.com/docs/en/github-actions)：在 CI 中使用 `schedule` 触发器
* [桌面端计划任务](https://code.claude.com/docs/en/desktop-scheduled-tasks)：在你的本机上本地运行
