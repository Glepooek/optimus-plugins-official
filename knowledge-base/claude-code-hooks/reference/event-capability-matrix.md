# 事件能力矩阵

> 34 个 hook 事件 × 六个能力维度的完整对照。本篇是 `rules/` 各篇结论的取证出处，不含规范语气。

依据：[Hooks reference](https://code.claude.com/docs/en/hooks)，核对日期 2026-09-12。官方文档随版本增删事件，使用前若发现与现状不符以官方为准。

## 维度说明

| 维度 | 含义 |
|---|---|
| cadence | 触发频率：会话级 / 轮级 / 工具级 / 事件驱动 |
| matcher | 匹配什么字段；`—` 表示不支持 matcher（写了被静默忽略） |
| 可拦截 | exit 2 是否阻断；worktree 两事件为「任何非零」 |
| handler | 支持的 handler 类型：`5` = 全部五类，`3` = command/http/mcp_tool，`2` = command/mcp_tool |
| 决策字段 | JSON 里表达决策的字段 |
| 输出去向 | `systemMessage` 的实际交付位置 |

## 完整矩阵

| 事件 | cadence | matcher | 可拦截 | handler | 决策字段 | 输出去向 |
|---|---|---|---|---|---|---|
| `SessionStart` | 会话 | 会话来源：`startup`/`resume`/`clear`/`compact`/`fork` | 否（stderr 只给用户） | 2 | 仅 `additionalContext`、`initialUserMessage`、`watchPaths`、`sessionTitle`、`reloadSkills` | 用户 |
| `Setup` | 会话 | `init`/`maintenance` | 否（全忽略） | 2 | 无 | **丢弃** |
| `SessionEnd` | 会话 | `clear`/`resume`/`logout`/`prompt_input_exit`/`other` | 否（stderr 只给用户） | 3 | 无 | 用户 |
| `UserPromptSubmit` | 轮 | — | **是**（抹除 prompt） | 5 | 顶层 `decision` | 用户 |
| `UserPromptExpansion` | 轮 | 命令名 | **是** | 5 | 顶层 `decision` | 用户 |
| `Stop` | 轮 | — | **是** | 5 | 顶层 `decision` + `additionalContext` | 用户 |
| `StopFailure` | 轮 | 错误类型（窄字符集） | 否（输出与 exit code 全忽略，`terminalSequence` 除外） | 3 | 无 | **丢弃** |
| `PostToolBatch` | 轮 | — | **是**（中断 agentic loop） | 5 | 顶层 `decision` | 用户 |
| `PreToolUse` | 工具 | 工具名 | **是** | 5 | `permissionDecision`（allow/deny/ask/defer）、`updatedInput` | 用户 |
| `PostToolUse` | 工具 | 工具名 | 否（stderr 给 Claude） | 5 | 顶层 `decision`、`updatedToolOutput` | 用户 |
| `PostToolUseFailure` | 工具 | 工具名 | 否（stderr 给 Claude） | 5 | 顶层 `decision` | 用户 |
| `PermissionRequest` | 工具 | 工具名 | **否，exit 2 不生效** | 5 | `decision.behavior`（allow/deny）、`decision.updatedInput` | 用户 |
| `PermissionDenied` | 工具 | 工具名 | 否（exit code 与 stderr 全忽略） | 5 | `retry: true` | 用户 |
| `Notification` | 事件 | 通知类型（12 种） | 否 | 3 | 无 | **丢弃**（`terminalSequence` 仍生效） |
| `MessageDisplay` | 事件 | — | 否（显示原文） | 3 | `displayContent` | **丢弃** |
| `SubagentStart` | 事件 | agent 类型 | 否（stderr 只给用户，在子 transcript） | 3 | 仅 `additionalContext` | 用户 |
| `SubagentStop` | 事件 | agent 类型 | **是** | 5 | 顶层 `decision` + `additionalContext` | 用户 |
| `TaskCreated` | 事件 | — | **是**（回滚创建） | 5 | exit 2 或顶层 `decision`；`continue:false` 被忽略 | 用户 |
| `TaskCompleted` | 事件 | — | **是** | 5 | exit 2 或 `continue:false` | 用户 |
| `TeammateIdle` | 事件 | — | **是** | 5 | exit 2 或 `continue:false` | 用户 |
| `InstructionsLoaded` | 事件 | 加载原因（5 种） | 否（exit code 忽略） | 3 | 无 | **丢弃** |
| `ConfigChange` | 事件 | 配置来源（5 种） | **是**（`policy_settings` 除外） | 3 | 顶层 `decision` | **丢弃** |
| `CwdChanged` | 事件 | — | 否（stderr 只给用户） | 3 | 无 | **降级为终端提示** |
| `DirectoryAdded` | 事件 | `slash_command`/`register_repo_root` | 否（stderr 进 debug log） | 3 | 无 | **改道**：`slash_command` → Claude；`register_repo_root` → debug log |
| `FileChanged` | 事件 | 文件名（窄字符集，见下） | 否（stderr 只给用户） | 3 | 无 | **降级为终端提示** |
| `WorktreeCreate` | 事件 | — | **是（任何非零）** | 3 | command 打印路径 / HTTP 返 `worktreePath` | **丢弃** |
| `WorktreeRemove` | 事件 | — | **是（任何非零）** | 3 | 仅 exit code，JSON 丢弃 | **丢弃** |
| `PreCompact` | 事件 | `manual`/`auto` | **是** | 3 | 顶层 `decision` | 用户 |
| `PostCompact` | 事件 | `manual`/`auto` | 否（stderr 只给用户） | 3 | 无 | 用户 |
| `PreModelSwitch` | 事件 | 目标模型规范名 | **是**（超时亦阻断） | 3 | `permissionDecision`（allow/deny/ask）或顶层 `decision` | 用户 |
| `PostModelSwitch` | 事件 | 目标模型规范名 | 否（stderr 只给用户） | 3 | 仅 `additionalContext` | 用户 |
| `Elicitation` | 事件 | MCP server 名 | **是**（拒绝） | 3 | `action`（accept/decline/cancel）+ `content` | 用户 |
| `ElicitationResult` | 事件 | MCP server 名 | **是**（变为 decline） | 3 | `action` + `content` | 用户 |

## 附注

**窄 matcher 字符集的两个事件**：`FileChanged` 与 `StopFailure` 的精确匹配集只含字母、数字、`_`、`|`。连字符、空格、逗号会让 matcher 落到正则路径，且只有 `|` 分隔备选项。`FileChanged` 构建 watch list 时另有自己的规则，见官方该节。

**`EndConversation` 工具跳过 `PreToolUse` 与 `PostToolUse`**，因此这两个事件不能用作「每个工具都会经过」的全量审计点。

**四个把纯文本 stdout 当上下文加给 Claude 的事件**：`UserPromptSubmit`、`UserPromptExpansion`、`SessionStart`、`PostModelSwitch`。其余事件的 stdout 只进 debug log。

**`SessionStart` 与 `Setup` 的 `mcp_tool` handler 时序**：`Setup` 每次都在 MCP server 可用前触发，其 `mcp_tool` hook 必然被跳过；`SessionStart` 在启动时（含 `--continue` / `--resume`）也在之前，只有 `/clear` 或 compact 后重新触发时才真正执行。debug log 记 `no MCP client context`。

**`additionalContext` 的插入位置**逐事件不同，见 `rules/03-output-contract.md § additionalContext`。

**异步维度未列入本表**：`async` / `asyncRewake` 是 command handler 的属性而非事件属性，任何支持 command handler 的事件都可用，但会改变输出去向——异步下 `systemMessage` 与 `additionalContext` 一律只交付给 Claude，本表「输出去向」列描述的是同步情形。见 `rules/05-async-execution.md`。
