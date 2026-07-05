# 以编程方式运行 Claude Code

> 使用 Agent SDK 从 CLI、Python 或 TypeScript 以编程方式运行 Claude Code。

来源：[code.claude.com/docs/en/headless](https://code.claude.com/docs/en/headless)

---

[Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) 为你提供了驱动 Claude Code 的同一套工具、智能体循环和上下文管理能力。它既可以作为面向脚本和 CI/CD 的 CLI 使用，也可以作为 [Python](https://code.claude.com/docs/en/agent-sdk/python) 和 [TypeScript](https://code.claude.com/docs/en/agent-sdk/typescript) 包使用，以获得完整的编程控制能力。

要以非交互模式运行 Claude Code，传入 `-p` 和你的提示词以及任意 [CLI 选项](https://code.claude.com/docs/en/cli-reference)：

```bash theme={null}
claude -p "Find and fix the bug in auth.py" --allowedTools "Read,Edit,Bash"
```

本页介绍如何通过 CLI（`claude -p`）使用 Agent SDK。关于带结构化输出、工具批准回调和原生消息对象的 Python 及 TypeScript SDK 包，参见[完整的 Agent SDK 文档](https://code.claude.com/docs/en/agent-sdk/overview)。

## 基本用法

给任意 `claude` 命令加上 `-p`（或 `--print`）标志，即可非交互式运行。所有 [CLI 选项](https://code.claude.com/docs/en/cli-reference)都能配合 `-p` 使用，包括：

* `--continue` 用于[继续对话](#continue-conversations)
* `--allowedTools` 用于[自动批准工具](#auto-approve-tools)
* `--output-format` 用于[结构化输出](#get-structured-output)

下面这个例子向 Claude 询问关于你代码库的一个问题，并打印出回答：

```bash theme={null}
claude -p "What does the auth module do?"
```

### 用 bare 模式启动更快

加上 `--bare` 可以跳过对 hooks、skill、plugin、MCP server、自动记忆和 CLAUDE.md 的自动发现，从而缩短启动时间。不加这个标志时，`claude -p` 会加载和交互式会话一样的[上下文](https://code.claude.com/docs/en/how-claude-code-works#the-context-window)，包括工作目录或 `~/.claude` 中配置的任何内容。

bare 模式适用于 CI 和脚本场景，因为你需要在每台机器上都得到相同的结果。队友 `~/.claude` 中的一个 hook，或者项目 `.mcp.json` 中的一个 MCP server 都不会运行，因为 bare 模式根本不会读取它们。只有你显式传入的标志才会生效。

下面的例子在 bare 模式下运行一次性的摘要任务，并预先批准了 Read 工具，这样调用就不会因为权限确认而卡住：

```bash theme={null}
claude --bare -p "Summarize this file" --allowedTools "Read"
```

在 bare 模式下，Claude 可以使用 Bash、文件读取和文件编辑工具。用标志传入你需要的任何上下文：

| 想加载什么                 | 使用什么标志                                                     |
| :--- | :--- |
| 系统提示词追加内容 | `--append-system-prompt`、`--append-system-prompt-file` |
| 设置                | `--settings <file-or-json>`                             |
| MCP servers             | `--mcp-config <file-or-json>`                           |
| 自定义 agent           | `--agents <json>`                                       |
| 一个 plugin                | `--plugin-dir <path>`、`--plugin-url <url>`             |

bare 模式会跳过 OAuth 和系统密钥链读取。Anthropic 的身份验证必须来自 `ANTHROPIC_API_KEY`，或者传给 `--settings` 的 JSON 中的一个 `apiKeyHelper`。Amazon Bedrock、Google Cloud 的 Agent Platform 以及 Microsoft Foundry 则使用它们各自惯常的提供方凭证。

> **注意：**
> `--bare` 是脚本化和 SDK 调用推荐使用的模式，未来版本中会成为 `-p` 的默认模式。

### 退出时的后台任务

如果 Claude 在一次 `claude -p` 运行中启动了[后台 Bash 任务](https://code.claude.com/docs/en/tools-reference#bash-tool-behavior)（比如一个开发服务器或一个 watch 构建），这个 shell 会在 Claude 返回最终结果、且标准输入关闭大约五秒后被终止。这个宽限期让一个恰好在结果返回后才完成的任务仍有机会交付输出。在 v2.1.163 之前，一个永不退出的后台进程会让 `claude -p` 的调用无限期挂起。

后台[子智能体](https://code.claude.com/docs/en/sub-agents)和工作流不受这五秒宽限期约束，因为它们的结果是最终输出的一部分，所以 `claude -p` 会等待它们完成。从 v2.1.182 开始，这个等待默认上限为十分钟，这样一个卡住的后台 agent 就不会让进程无限期挂起。可以用 [`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`](https://code.claude.com/docs/en/env-vars) 调整这个上限，或将其设为 `0` 以无限期等待。

## 示例

以下示例展示了常见的 CLI 使用模式。对于 CI 和其他脚本化调用，加上 [`--bare`](#start-faster-with-bare-mode)，这样它们就不会意外读取本地恰好配置的内容。

### 把数据通过管道传给 Claude

非交互模式会读取标准输入，因此你可以像使用任何其他命令行工具一样，把数据用管道传进去，并把响应重定向出来。

下面的例子把一份构建日志通过管道传给 Claude，并把解释写入一个文件：

```bash theme={null}
cat build-error.txt | claude -p 'concisely explain the root cause of this build error' > output.txt
```

使用 `--output-format json` 时，响应负载中会包含 `total_cost_usd` 以及按模型划分的成本明细，这样脚本化的调用方无需查阅[用量看板](https://code.claude.com/docs/en/costs)就能追踪每次调用的花费。

> **注意：**
> 从 Claude Code v2.1.128 开始，通过管道传入的标准输入上限为 10MB。超过这个上限时，Claude Code 会退出并给出明确的错误和非零状态码。要处理更大的输入，把内容写入一个文件，并在提示词中引用该文件路径，而不是用管道传入。

### 把 Claude 加入构建脚本

你可以把一次非交互调用封装进一个脚本，把 Claude 当作项目专属的 linter 或评审者来使用。

下面这个 `package.json` 脚本把针对 `main` 的 diff 通过管道传给 Claude，并让它报告拼写错误。用管道传入 diff 意味着 Claude 不需要 Bash 权限来读取它，转义的双引号也保证了这个脚本在 Windows 上同样可移植：

```json theme={null}
{
  "scripts": {
    "lint:claude": "git diff main | claude -p \"you are a typo linter. for each typo in this diff, report filename:line on one line and the issue on the next. return nothing else.\""
  }
}
```

### 获取结构化输出

用 `--output-format` 控制响应的返回方式：

* `text`（默认）：纯文本输出
* `json`：带 result、session ID 和元数据的结构化 JSON
* `stream-json`：用于实时流式传输的按行分隔 JSON

下面的例子把一份项目摘要以 JSON 形式返回，附带 session 元数据，文本结果位于 `result` 字段中：

```bash theme={null}
claude -p "Summarize this project" --output-format json
```

要获得符合特定 schema 的输出，把 `--output-format json` 和 `--json-schema` 以及一份 [JSON Schema](https://json-schema.org/) 定义配合使用。响应中会包含关于这次请求的元数据（session ID、用量等），结构化输出则位于 `structured_output` 字段中。

下面的例子提取函数名，并将其作为字符串数组返回：

```bash theme={null}
claude -p "Extract the main function names from auth.py" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}},"required":["functions"]}'
```

> **提示：**
> 用像 [jq](https://jqlang.github.io/jq/) 这样的工具来解析响应并提取特定字段：

```bash theme={null}
# Extract the text result
claude -p "Summarize this project" --output-format json | jq -r '.result'

# Extract structured output
claude -p "Extract function names from auth.py" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}},"required":["functions"]}' \
  | jq '.structured_output'
```

### 流式响应

用 `--output-format stream-json` 配合 `--verbose` 和 `--include-partial-messages`，在 token 生成的同时接收它们。每一行都是代表一个事件的 JSON 对象：

```bash theme={null}
claude -p "Explain recursion" --output-format stream-json --verbose --include-partial-messages
```

下面的例子用 [jq](https://jqlang.github.io/jq/) 过滤出文本增量并只显示流式文本。`-r` 标志输出不带引号的原始字符串，`-j` 在拼接时不换行，让 token 能够连续流出：

```bash theme={null}
claude -p "Write a poem" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

当一次 API 请求因可重试的错误而失败时，Claude Code 会在重试之前发出一个 `system/api_retry` 事件。你可以用它来展示重试进度，或实现自定义的退避逻辑。

| 字段            | 类型            | 说明                                                                                                                                                                                            |
| :--- | :--- | :--- |
| `type`           | `"system"`      | 消息类型                                                                                                                                                                                           |
| `subtype`        | `"api_retry"`   | 标识这是一个重试事件                                                                                                                                                                       |
| `attempt`        | integer         | 当前尝试次数，从 1 开始                                                                                                                                                                  |
| `max_retries`    | integer         | 允许的总重试次数                                                                                                                                                                                |
| `retry_delay_ms` | integer         | 距下一次尝试的毫秒数                                                                                                                                                                    |
| `error_status`   | integer or null | HTTP 状态码，对于没有 HTTP 响应的连接错误则为 `null`                                                                                                                               |
| `error`          | string          | 错误类别：`authentication_failed`、`oauth_org_not_allowed`、`billing_error`、`rate_limit`、`overloaded`、`invalid_request`、`model_not_found`、`server_error`、`max_output_tokens` 或 `unknown` |
| `uuid`           | string          | 唯一的事件标识符                                                                                                                                                                                   |
| `session_id`     | string          | 该事件所属的 session                                                                                                                                                                           |

`system/init` 事件报告 session 的元数据，包括模型、工具、MCP servers 和已加载的 plugin。除非设置了 [`CLAUDE_CODE_SYNC_PLUGIN_INSTALL`](https://code.claude.com/docs/en/env-vars)（此时 `plugin_install` 事件会先于它出现），否则它是流中的第一个事件。用 plugin 相关字段可以让 CI 在某个 plugin 未能加载时判定失败：

| 字段           | 类型  | 说明                                                                                                                                                                                                                                                                                  |
| :--- | :--- | :--- |
| `plugins`       | array | 成功加载的 plugin，每个都带有 `name` 和 `path`                                                                                                                                                                                                                                |
| `plugin_errors` | array | plugin 加载期间的错误，每个都带有 `plugin`、`type` 和 `message`。包括未满足的依赖版本，以及 `--plugin-dir` 加载失败（比如路径缺失或归档无效）。受影响的 plugin 会被降级，且不出现在 `plugins` 中。没有错误时会省略该字段 |

设置了 [`CLAUDE_CODE_SYNC_PLUGIN_INSTALL`](https://code.claude.com/docs/en/env-vars) 时，Claude Code 会在第一轮之前、marketplace 中的 plugin 安装期间发出 `system/plugin_install` 事件。可以用它们在你自己的界面中展示安装进度。

| 字段        | 类型                                                     | 说明                                                                                                                    |
| :--- | :--- | :--- |
| `type`       | `"system"`                                               | 消息类型                                                                                                   |
| `subtype`    | `"plugin_install"`                                       | 标识这是一个 plugin 安装事件                                                                      |
| `status`     | `"started"`、`"installed"`、`"failed"` 或 `"completed"` | `started` 和 `completed` 标记整个安装过程的起止；`installed` 和 `failed` 报告各个 marketplace 的结果 |
| `name`       | string, optional                                         | marketplace 名称，出现在 `installed` 和 `failed` 中                                                          |
| `error`      | string, optional                                         | 失败信息，出现在 `failed` 中                                                                           |
| `uuid`       | string                                                   | 唯一的事件标识符                                                                                                   |
| `session_id` | string                                                   | 该事件所属的 session                                                                                   |

关于带回调和消息对象的编程式流式传输，参见 Agent SDK 文档中的[实时流式响应](https://code.claude.com/docs/en/agent-sdk/streaming-output)。

### 自动批准工具

用 `--allowedTools` 让 Claude 使用某些工具而无需确认。下面的例子运行一个测试套件并修复失败项，允许 Claude 执行 Bash 命令、读取和编辑文件而无需请求权限：

```bash theme={null}
claude -p "Run the test suite and fix any failures" \
  --allowedTools "Bash,Read,Edit"
```

要为整个 session 设定一个基线，而不是逐个列出工具，传入一个[权限模式](https://code.claude.com/docs/en/permission-modes)。`dontAsk` 会拒绝任何不在你的 `permissions.allow` 规则或[只读命令集合](https://code.claude.com/docs/en/permissions#read-only-commands)中的操作，这对锁定的 CI 运行很有用。`acceptEdits` 让 Claude 无需确认就能写入文件，并且会自动批准常见的文件系统命令，比如 `mkdir`、`touch`、`mv` 和 `cp`。其他 shell 命令和网络请求仍然需要一条 `--allowedTools` 条目或一条 `permissions.allow` 规则，否则一旦尝试执行，运行就会中止：

```bash theme={null}
claude -p "Apply the lint fixes" --permission-mode acceptEdits
```

### 创建一次提交

下面的例子评审已暂存的改动，并创建一条合适的提交信息：

```bash theme={null}
claude -p "Look at my staged changes and create an appropriate commit" \
  --allowedTools "Bash(git diff *),Bash(git log *),Bash(git status *),Bash(git commit *)"
```

`--allowedTools` 标志使用[权限规则语法](https://code.claude.com/docs/en/settings#permission-rule-syntax)。结尾的 ` *` 启用前缀匹配，因此 `Bash(git diff *)` 允许任何以 `git diff` 开头的命令。`*` 前面的空格很重要：如果没有它，`Bash(git diff*)` 会同时匹配到 `git diff-index`。

> **注意：**
> 用户主动调用的 [skill](https://code.claude.com/docs/en/skills) 和自定义命令在 `-p` 模式下也能正常工作：在提示词字符串中包含 `/skill-name`，Claude Code 会在运行前将其展开。会打开交互式对话框的内置命令，比如 `/login`，在 `-p` 模式下不可用。{/* min-version: 2.1.181 */}要从一次 `-p` 调用中修改某项设置，把 `key=value` 传给 `/config`，例如 `/config thinking=false`。

### 自定义系统提示词

用 `--append-system-prompt` 在保留 Claude Code 默认行为的同时追加指令。下面的例子把一份 PR diff 通过管道传给 Claude，并指示它评审安全漏洞：

```bash theme={null}
gh pr diff "$1" | claude -p \
  --append-system-prompt "You are a security engineer. Review for vulnerabilities." \
  --output-format json
```

关于更多选项，包括用 `--system-prompt` 完全替换默认提示词，参见[系统提示词标志](https://code.claude.com/docs/en/cli-reference#system-prompt-flags)。

### 继续对话

用 `--continue` 继续最近的一次对话，或用带 session ID 的 `--resume` 继续某个特定对话。下面的例子先运行一次评审，然后发送后续提示词：

```bash theme={null}
# First request
claude -p "Review this codebase for performance issues"

# Continue the most recent conversation
claude -p "Now focus on the database queries" --continue
claude -p "Generate a summary of all issues found" --continue
```

如果你在运行多个对话，记录下 session ID 以便恢复某个特定对话：

```bash theme={null}
session_id=$(claude -p "Start a review" --output-format json | jq -r '.session_id')
claude -p "Continue that review" --resume "$session_id"
```

在同一个目录下运行这两条命令：session ID 的查找范围限定在当前项目目录及其 git worktree 内。完整的范围规则参见[恢复一个会话](https://code.claude.com/docs/en/sessions#resume-a-session)。

## 后续步骤

* [Agent SDK 快速入门](https://code.claude.com/docs/en/agent-sdk/quickstart)：用 Python 或 TypeScript 构建你的第一个 agent
* [CLI 参考](https://code.claude.com/docs/en/cli-reference)：所有 CLI 标志和选项
* [GitHub Actions](https://code.claude.com/docs/en/github-actions)：在 GitHub workflow 中使用 Agent SDK
* [GitLab CI/CD](https://code.claude.com/docs/en/gitlab-ci-cd)：在 GitLab pipeline 中使用 Agent SDK
