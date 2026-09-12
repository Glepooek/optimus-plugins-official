# 05 异步执行

> `async` 不是「同样的 hook 只是不阻塞」。它换掉了输出的交付对象、取消了超时约束、放弃了全部决策能力。

`enforcement`：§ 1 的 handler 类型限制、§ 2 的输出去向与交付物类型配对可机械校验，标 `ci`；§ 4 的适用判据需人工判断，标 `review`。

## 1. `async` 只在 `type: "command"` 上可用

`async` 与 `asyncRewake` 是 **command hook 专有字段**。`http`、`mcp_tool`、`prompt`、`agent` 的字段表里没有它们。写上去不生效。

不限制事件——任何支持 command handler 的事件都可以异步。但**能异步不等于该异步**，判据见 § 4。

## 2. 输出的交付对象变了：从用户变成 Claude

这是 `async` 最容易判错的一项，官方原文：

> After the background process exits, Claude Code delivers the `additionalContext` and `systemMessage` fields from the hook's JSON response to Claude on the next conversation turn. **Unlike a synchronous hook's `systemMessage`, neither field is shown to you.**

拆成三条：

- **`systemMessage` 与 `additionalContext` 都只交付给 Claude 的下一轮上下文，两者都不展示给用户。** 同步 hook 的 `systemMessage` 是给人看的，异步之后它变成给模型看的。
- **禁止把面向人类展示的 hook 配成 `async`。** 判据：这个 hook 的交付物是**副作用**（写日志、发通知、调外部服务、跑测试），还是**给人看的文本**？后者一律同步。
- **不存在「既异步又对用户可见」的替代方案。** `terminalSequence` 不在异步交付的字段列表内，且其白名单只有窗口标题、通知、响铃（见 `rules/03 § terminalSequence`），承载不了多行展示文本。后台进程直接写 TTY 会与 Claude Code 的界面绘制冲突，且 hook 本就没有控制终端。

**异步完成通知默认被抑制。** 要看到它须开 verbose（`Ctrl+O` 或启动时 `--verbose`）。所以「hook 好像没跑」在异步下缺乏可观测信号——状态文件的 mtime 往往是唯一证据。

## 3. 其余四项语义变化

- **失去全部决策能力**：`decision`、`permissionDecision`、`continue` 一概无效，因为它们本该控制的动作已经完成。
- **`timeout` 不再强制**：一旦后台进程起来，Claude Code 不再对它计时。`asyncRewake` 的 hook 仍然受 `timeout` 约束。
- **输出等到下一轮才交付**：会话空闲时会一直等到下一次用户交互。唯一例外是 `asyncRewake` 且 exit 2，能在空闲时立刻唤醒 Claude。
- **无去重**：每次触发都新起一个后台进程，同一个异步 hook 多次触发不会合并。

生命周期限制：`-p` 非交互模式下，teardown 时仍在跑的异步 hook 会被杀掉并标记为 `cancelled`。工作必须活过 `claude -p` 会话的，须从 hook 里再起一个完全脱离的进程。

**JSON 校验仍然执行**：异步输出走与同步相同的 schema 校验，类型不对的字段（如非字符串的 `systemMessage`）会被丢弃而非交付，`--debug` 可看到被丢字段的警告。v2.1.202 之前，异步 hook 输出畸形 JSON 会崩会话，且每次 resume 复现。

## 4. 适用判据

| 该异步 | 不该异步 |
|---|---|
| 交付物是副作用：部署、跑测试套件、调外部 API、发桌面通知 | 交付物是给人看的文本 |
| 耗时长且结果不需要在本轮生效 | 结果需要影响本轮的决策或展示 |
| 需要向 Claude 回报长任务失败 → 用 `asyncRewake` + exit 2 | 需要阻断某个动作 |

**同一个配置文件里另一个 hook 用了 `async` 不构成类比依据。** 判据是那个 hook 的交付物性质，不是它的写法。典型对照：

- `Notification` + `async: true` **正确**——它的实质工作是弹窗这个副作用，而且 `Notification` 事件本身就丢弃 `systemMessage`（见 `rules/03 § 4`），异步与否都不改变可见性。
- `SessionStart` 的技巧展示 + `async: true` **错误**——它的全部产出就是那个 `systemMessage`，异步等于把唯一交付物扔进模型上下文。

## 5. 同步的固有成本不能靠 `async` 掩盖

把一个必须同步的 hook 改成异步来「优化启动速度」，是用功能失效换延迟数字。同步 hook 的耗时只能靠减少它的实际工作量来降低（进程数、解释器启动、I/O），成本模型见 `rules/06-security-and-cost.md § 进程成本`。

另需注意 `/clear` 场景：**Claude Code 本身已经把 `SessionStart` hook 放后台跑**，输入框立刻可用，Claude 的首次响应才等 hook 完成以便上下文送达。所以「`/clear` 卡住」这半边症状本就不需要靠改 `async` 解决。若在这些 hook 仍在运行时再次 `/clear` 或用 `/resume` 切换对话，Claude Code 会取消它们并丢弃输出。

## 6. `asyncRewake`

`async` 的变体：后台运行，**exit code 2 时唤醒 Claude**。hook 的 stderr（stderr 为空则取 stdout）作为 system reminder 展示给 Claude，使它能对长时后台失败作出反应。

与 `async` 的三处差异：

- 仍受 `timeout` 约束。
- exit 2 能在会话空闲时立刻唤醒，不必等下一次用户交互。
- 回报通道是 stderr/stdout，**不是** `systemMessage`。

适用场景：后台跑的长任务需要在失败时让 Claude 知道并处理。仅需记录不需要 Claude 反应的，用 `async` 即可。
