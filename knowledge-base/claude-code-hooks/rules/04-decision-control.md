# 04 决策控制

> 各事件用什么字段表达决策、哪些事件能改写内容、hook 的保证强度到哪里为止。

`enforcement`：§ 1 的字段与事件配对、§ 2 的 `decision` 取值可机械校验，标 `ci`；§ 4 的硬保证边界、§ 5 的 prompt/agent hook 选用需人工判断，标 `review`。

## 1. 五种决策模式

**不同事件用不同字段表达决策，写错字段不会报错，只是不生效。**

| 决策模式 | 事件 | 关键字段 |
|---|---|---|
| 顶层 `decision` | `UserPromptSubmit`、`UserPromptExpansion`、`PostToolUse`、`PostToolUseFailure`、`PostToolBatch`、`Stop`、`SubagentStop`、`ConfigChange`、`PreCompact` | `decision: "block"` + `reason` |
| exit code 或 `continue: false` | `TeammateIdle`、`TaskCompleted` | exit 2 带 stderr 反馈；`{"continue": false, "stopReason": "..."}` |
| exit code 或顶层 `decision` | `TaskCreated` | exit 2 或 `decision: "block"` 取消任务；**`continue: false` 被忽略** |
| `hookSpecificOutput` | `PreToolUse` | `permissionDecision`（allow/deny/ask/defer）+ `permissionDecisionReason` |
| `hookSpecificOutput` | `PermissionRequest` | `decision.behavior`（allow/deny） |
| `hookSpecificOutput` | `PermissionDenied` | `retry: true` |
| `hookSpecificOutput` | `Elicitation` / `ElicitationResult` | `action`（accept/decline/cancel）+ `content` |
| `hookSpecificOutput` | `MessageDisplay` | `displayContent` |
| `hookSpecificOutput` 或顶层 `decision` | `PreModelSwitch` | `permissionDecision`（allow/deny/ask）；`decision: "block"` 亦可取消切换 |
| 路径返回 | `WorktreeCreate` | command hook 在 stdout 打印路径；HTTP hook 返回 `hookSpecificOutput.worktreePath` |
| 仅 exit code | `WorktreeRemove` | 任何非零 exit 使移除失败；**JSON 输出被丢弃** |
| 仅上下文 | `SessionStart`、`SubagentStart`、`PostModelSwitch` | `hookSpecificOutput.additionalContext`；无阻断能力 |
| **无决策控制** | `Setup`、`Notification`、`SessionEnd`、`PostCompact`、`InstructionsLoaded`、`StopFailure`、`CwdChanged`、`DirectoryAdded`、`FileChanged` | 只用于副作用 |

`SessionStart` 除 `additionalContext` 外还接受 `initialUserMessage`、`watchPaths`、`sessionTitle`、`reloadSkills`。

## 2. 顶层 `decision` 的唯一合法值是 `"block"`

**要放行就省略 `decision` 字段，或直接 exit 0 不输出 JSON。** 不存在 `decision: "allow"`。

```json
{ "decision": "block", "reason": "Test suite must pass before proceeding" }
```

`Stop` 与 `SubagentStop` 另接受 `hookSpecificOutput.additionalContext`，用于**非错误性反馈**——对话继续，Claude 据此调整，而不是当成阻断错误。要给出建设性反馈应优先用它而非 `decision: "block"`。

## 3. 改写类能力：只有五处

| 事件 | 改写什么 | 字段位置 |
|---|---|---|
| `PreToolUse` | 工具参数（执行前） | `hookSpecificOutput.updatedInput` |
| `PermissionRequest` | 工具参数 | `decision` 对象内的 `updatedInput` |
| `PostToolUse` | 工具结果 | `updatedToolOutput` |
| `MessageDisplay` | 屏幕显示的文本 | `hookSpecificOutput.displayContent` |
| `UserPromptSubmit` | **改写不了 prompt**，只能并列注入 `additionalContext` | — |

两条约束：

- **`updatedInput` 是整体替换**，不是合并。未改动的字段也必须一并带上，漏了就是删掉。
- **`MessageDisplay` 的 `displayContent` 只改屏幕**。transcript 与 Claude 看到的内容仍是原文。用它做脱敏展示不构成脱敏——数据仍进了 transcript 与模型上下文。

做脱敏或转换时的拦截位：出站工具输入拦 `PreToolUse`，入站工具结果拦 `PostToolUse`。

`PreToolUse` 的 `updatedInput` 有一处连带效应：Claude Code 用**你返回的输入**而非 Claude 原本发的输入去评估权限规则与 Bash 命令的自动后台化资格。

## 4. 硬保证的边界

**hook 不是安全边界。** 三条理由：

1. **`if` 是 best-effort**：Claude Code 判断不出 Bash 会执行什么时，无论模式匹配与否都运行你的 hook（见 `rules/02 § if`）。
2. **超时不阻断**：`PreToolUse` 上超时的 hook 不拦截，工具调用继续走正常权限流程。
3. **起不来即放行**：路径写错、脚本不可执行都落在非阻断档，动作照常进行（见 `rules/03 § 1`）。

因此：

> **需要硬性 allow/deny 的场景必须用 permission 系统，hook 只作补充。** 用 hook 实现「禁止删除生产数据」这类不可失效的约束，等于把安全性押在配置无笔误上。

`continue: false` 是最强的通用停止手段——**优先于任何事件特定决策字段**。`PreToolUse` 与 `PostToolUse` 上，即使工具调用失败或 Claude 仍在流式输出，停止也生效。但它同样受上述三条限制，不构成硬保证。

## 5. `prompt` 与 `agent` handler 的决策语义

`prompt` hook 让模型返回 `{"ok": bool, "reason": str, "impossible": bool}`；`agent` hook 返回 `{"ok": bool, "reason": str}`（无 `impossible`、无 `continueOnBlock`）。

`ok: false` 的效果逐事件不同，**默认多数是「结束本轮 + 聊天里出一行警告」，而不是把理由反馈给 Claude 让它继续**：

| 事件 | `ok: false` 的默认行为 |
|---|---|
| `Stop` / `SubagentStop` | 理由作为 Claude 的下一条指令反馈，轮次继续；除非同时 `impossible: true`，此时允许停止 |
| `PreToolUse` | 拒绝调用，**默认结束本轮**；设 `continueOnBlock: true` 才把理由作为工具错误返给 Claude 让它调整 |
| `PostToolUse` | 默认结束本轮；`continueOnBlock: true` 才反馈并继续 |
| `PostToolBatch`、`UserPromptSubmit`、`UserPromptExpansion` | 结束本轮并出警告行，**无论 `continue` 取值** |
| `PostToolUseFailure`、`TaskCreated` | 理由作为工具错误返给 Claude，轮次继续，**与 `continueOnBlock` 无关** |
| `TeammateIdle` | 默认 teammate 停止；`continueOnBlock: true` 才反馈并继续工作 |
| `PermissionRequest` | **无效**。要从 hook 拒绝审批必须用 command hook 返 `decision.behavior: "deny"` |
| `PermissionDenied` | **无效**，拒绝已发生。该事件只读 `hookSpecificOutput.retry`，而 prompt/agent hook 设不了该字段——它们会运行，但输出被丢弃 |

两条选用规则：

- **想让 Claude 收到理由后自行调整而非中断轮次，`PreToolUse` / `PostToolUse` / `TeammateIdle` 上必须显式设 `continueOnBlock: true`。**
- **`PermissionRequest` 与 `PermissionDenied` 上禁止用 prompt/agent hook 做决策**，它们在这两个事件上没有可写的决策字段。

`agent` hook 至多 50 轮，可用 Read / Grep / Glob 等工具做验证，适合「判断依赖实际文件或测试输出」的场景。官方标注 experimental，生产优先 `command`。
