# 01 事件选型

> 决定用哪个 hook 事件。选错事件的代价不是报错，而是 hook 安静地不产生预期效果。

`enforcement`：本篇条款以 `review` 为主——事件是否选得恰当依赖意图判断，脚本无法代劳。§ 3、§ 5 中「该事件不支持某能力」的部分可机械校验，标 `ci`。

## 1. 先按 cadence 判断触发频率

事件按触发频率分三类，**频率直接决定该事件能承担多重的工作**：

| cadence | 事件 | 一次会话触发次数 |
|---|---|---|
| 每会话一次 | `SessionStart`、`Setup`、`SessionEnd` | 1-2 次（`/clear`、compact 会再触发 `SessionStart`） |
| 每轮一次 | `UserPromptSubmit`、`Stop`、`StopFailure`、`PostToolBatch` | 数十次 |
| 每次工具调用 | `PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PermissionRequest` | 数百次 |

规则：

- 每次工具调用触发的事件上**禁止**放入耗时超过百毫秒级的同步工作。数百次 × 单次耗时是会话总延迟，不是单点延迟。
- `SessionStart` 必须快。官方明示「SessionStart runs on every session, so keep these hooks fast」。它的耗时直接体现为启动等待。
- `SessionEnd` 的全部 hook **共享 1.5 秒预算**；若设置了更长的 per-hook `timeout`，预算会提升到匹配值，上限 60 秒。不要指望在 `SessionEnd` 完成长任务。
- `EndConversation` 工具调用**不触发** `PreToolUse` 与 `PostToolUse`，不要依赖这两个事件做「每个工具都会经过」的全量审计。

具体耗时成本见 `rules/06-security-and-cost.md § 进程成本`。

## 2. 选型的三个问题

按顺序回答，前一个问题为否才看下一个：

1. **要阻止某件事发生吗？** → 只能选**可拦截**事件（§ 3）。事后事件（`PostToolUse`、`Notification`、`SessionEnd`）无论 exit code 与 JSON 都拦不住已发生的动作。
2. **要改写内容吗？** → 只有五个事件具备改写能力，见 `rules/04-decision-control.md § 改写类能力`。
3. **只是观测/记录/通知吗？** → 选无决策控制的事件，配 `async` 卸掉同步开销（判据见 `rules/05-async-execution.md`）。

**禁止**为了「顺便拦一下」而把观测逻辑挂到可拦截事件上：可拦截事件的超时与异常处理语义更严（如 `PreModelSwitch` 超时即阻断切换），观测逻辑一旦出错会连带阻断正常流程。

## 3. 能否拦截：以 exit 2 的效果为准

**可拦截**（exit 2 生效）：

| 事件 | exit 2 的效果 |
|---|---|
| `PreToolUse` | 阻断工具调用 |
| `UserPromptSubmit` | 阻断处理并**抹除**该 prompt |
| `UserPromptExpansion` | 阻断展开 |
| `Stop` / `SubagentStop` | 阻止停止，对话继续 |
| `TeammateIdle` | 阻止 teammate 进入 idle |
| `TaskCreated` | 回滚任务创建 |
| `TaskCompleted` | 阻止标记完成 |
| `ConfigChange` | 阻断配置变更生效（`policy_settings` 除外） |
| `PostToolBatch` | 在下次模型调用前中断 agentic loop |
| `PreCompact` | 阻断压缩 |
| `PreModelSwitch` | 阻断模型切换 |
| `Elicitation` | 拒绝 elicitation |
| `ElicitationResult` | 阻断响应（动作变为 decline） |
| `WorktreeCreate` / `WorktreeRemove` | **任何非零** exit code 即失败，不限于 2 |

**不可拦截**：`PermissionRequest`、`PostToolUse`、`PostToolUseFailure`、`PermissionDenied`、`Notification`、`SessionStart`、`Setup`、`SessionEnd`、`SubagentStart`、`StopFailure`、`CwdChanged`、`DirectoryAdded`、`FileChanged`、`PostCompact`、`PostModelSwitch`、`InstructionsLoaded`、`MessageDisplay`。

三个必须记住的例外：

- **`PermissionRequest` 不认 exit 2**，权限流程照常走。要拒绝必须用 `decision.behavior: "deny"`（见 `rules/04`）。这是最容易误判的一个——事件名看起来像个闸门，但 exit code 这条路是堵死的。
- **worktree 两个事件用「任何非零」而非「等于 2」**判断失败。在这两个事件上 `exit 1` 会阻断，与其余事件相反。
- **`PostToolUse` / `PostToolUseFailure` 的 exit 2 不拦截，但会把 stderr 展示给 Claude**。这是这两个事件上向模型传递告警的唯一途径——exit 0 的 stderr 只进 debug log，Claude 看不到。

完整逐事件对照见 `reference/event-capability-matrix.md`。

## 4. matcher 支持情况

不是所有事件都支持 `matcher`。**在不支持的事件上写 `matcher` 会被静默忽略**——不报错，所以不要用「配置没报错」推断过滤生效了。

无 matcher 支持（永远全量触发）：`UserPromptSubmit`、`PostToolBatch`、`Stop`、`TeammateIdle`、`TaskCreated`、`TaskCompleted`、`WorktreeCreate`、`WorktreeRemove`、`MessageDisplay`、`CwdChanged`。

其余事件各自匹配不同字段（工具名、会话来源、通知类型、agent 类型……），求值规则与逐事件匹配字段见 `rules/02-configuration.md § matcher 求值`。

## 5. handler 类型支持

五类 handler（`command` / `http` / `mcp_tool` / `prompt` / `agent`）**不是所有事件都支持**。写了不支持的类型不会有配置错误，只是不生效。

| 支持范围 | 事件 |
|---|---|
| 全部五类 | `PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PostToolBatch`、`PermissionRequest`、`PermissionDenied`、`Stop`、`SubagentStop`、`TaskCreated`、`TaskCompleted`、`TeammateIdle`、`UserPromptSubmit`、`UserPromptExpansion` |
| 仅 `command` / `http` / `mcp_tool` | `ConfigChange`、`CwdChanged`、`DirectoryAdded`、`Elicitation`、`ElicitationResult`、`FileChanged`、`InstructionsLoaded`、`MessageDisplay`、`Notification`、`PostCompact`、`PreCompact`、`PostModelSwitch`、`PreModelSwitch`、`SessionEnd`、`StopFailure`、`SubagentStart`、`WorktreeCreate`、`WorktreeRemove` |
| 仅 `command` / `mcp_tool` | `SessionStart`、`Setup` |

由此得出两条硬约束：

- **`SessionStart` 与 `Setup` 上禁止使用 `http`、`prompt`、`agent` handler**，不支持。
- **`SessionStart` 与 `Setup` 上的 `mcp_tool` handler 在启动时必然被跳过**：MCP server 此刻尚未对 hook 可用，debug log 记 `no MCP client context`。`Setup` 每次都跳过；`SessionStart` 只在 `/clear` 或 compact 后重新触发时才真正执行。**会话从第一轮就需要的东西，必须用 `command` handler**。

`agent` 类型官方标注为 experimental，生产用途应优先 `command`。

## 6. 选型误用的四种形态

| 形态 | 症状 | 正确做法 |
|---|---|---|
| **拿事后事件当闸门** | 挂 `PostToolUse` 想阻止写入，工具早已执行 | 改 `PreToolUse`；已发生的动作只能补救不能阻止 |
| **拿 `PermissionRequest` 的 exit code 当拒绝** | 脚本 `exit 2` 但权限照样弹给用户 | 用 `hookSpecificOutput.decision.behavior: "deny"` |
| **在 `SessionStart` 上用 `mcp_tool` 加载上下文** | 启动时静默跳过，只有 `/clear` 后才生效 | 改 `command` handler |
| **靠 hook 做硬性安全保证** | `if` 是 best-effort，Bash 命令展开不确定时 hook 照跑但判断可能错 | 用 permission 系统做 allow/deny 硬保证，hook 只做补充（见 `rules/04 § 硬保证的边界`） |

## 7. 不要用 hook 承载静态约定

需要 Claude 始终知道的**静态**项目约定（编码规范、目录结构、命令惯例）**应该**写进 `CLAUDE.md`，不要用 `SessionStart` hook 注入。官方明示「For static context that doesn't require a script, use CLAUDE.md instead」——CLAUDE.md 无需起进程即加载，而 hook 每次会话都付一次进程成本。

hook 注入上下文只在内容**动态**时才有正当性：当前分支、部署目标、CI 结果、刚编辑文件对应的测试命令。判据是「这个值会不会在两次会话之间变化」。
