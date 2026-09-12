# 03 输出契约

> exit code 与 stdout 怎么被解读、各字段最终交付到哪里。**本篇是 hook「跑了但没效果」的第一排查位置。**

`enforcement`：§ 1 的 exit code 选择、§ 2 的 stdout 纯净性、§ 4 的字段与事件配对可机械校验，标 `ci`；§ 5 的措辞要求需人工判断，标 `review`。

## 1. exit code 语义

**exit code 不单独决定结果。** Claude Code 在**任何** exit code 下都会读 stdout 的 JSON，通过 schema 校验的对象与 exit code 共同生效。exit 2 的阻断是 JSON 唯一覆盖不了的结果。

### exit 0

成功，也是打印 JSON 做结构化控制时的**应该**取值。

- 多数事件下 stdout 只进 debug log，不进 transcript。**四个例外**：`UserPromptSubmit`、`UserPromptExpansion`、`SessionStart`、`PostModelSwitch`——这些事件会把纯文本 stdout 作为上下文加给 Claude。
- **exit 0 的 stderr 只进 debug log，Claude 永远看不到，transcript 也不显示。** 要从 `PostToolUse` / `PostToolUseFailure` 向 Claude 传告警，**必须** exit 2（这两个事件的 exit 2 不拦截，只把 stderr 给 Claude）。

### exit 2

阻断错误。在可拦截事件上，**打不打印 JSON 都阻断**——即使 JSON 里写了 `permissionDecision: "allow"` 也覆盖不了。

- 阻断消息取自 JSON 的阻断决策 `reason`，没有则取 stderr 文本。
- JSON schema 校验失败但 exit 2 时**仍然阻断**，用 stderr 当理由，校验失败记 debug log。
- `Elicitation` / `ElicitationResult` 上，exit 2 的 hook 其 `hookSpecificOutput` 被忽略。

### 其他 exit code

**这是最危险的一档。** 对多数事件，非 0 非 2 的 exit code **本身不阻断**：

- stdout 有通过校验的 JSON → exit code 被忽略，JSON 单独决定结果，且不报错。
- stdout 有解析失败或校验失败的 JSON → 非阻断错误，动作照常进行，transcript 显示 `<hook name> hook error`。
- stdout 是纯文本或为空 → 非阻断错误，动作照常进行，transcript 显示 notice + stderr 首行，前缀 `Failed with non-blocking status code:`。

由此得出一条硬规则：

> **要执行策略的 hook 必须用 `exit 2`。** `exit 1` 是 Unix 惯例的失败码，但在多数 hook 事件上被当成非阻塞错误直接放行。

两个反向例外：`WorktreeCreate` 的**任何**非零 exit 阻断创建；`WorktreeRemove` 的任何非零 exit 使移除失败（若目录事后仍存在）。

### hook 起不来也落在非阻断档

脚本路径不存在或不可执行时，shell 退出码是 127 之类，走的是**非阻断错误**路径——动作照常进行。**部署策略型 hook 后必须看它第一次运行的 transcript notice**：`settings.json` 里一个拼错的路径会让闸门静默失效，且此后每次都静默。

### 超时

除 `async: true` 的 command hook 外，达到 `timeout` 的 `command` / `http` / `mcp_tool` hook 会被取消并**丢弃输出**，多数事件上等于没做决策。两个例外：

- `PreModelSwitch`：超时被取消的 hook **阻断**模型切换。
- `PreToolUse`：超时的 command/http/mcp_tool hook **不阻断**，工具调用继续走正常权限流程。**不要指望一个卡住的 hook 充当闸门。**（Agent SDK callback hook 与此相反，超时会阻断。）

`timeout` 默认值：`command`/`http`/`mcp_tool` 600 秒；`prompt` 30 秒；`agent` 60 秒。`UserPromptSubmit`、`PreModelSwitch`、`PostModelSwitch` 上前三类降到 30 秒，`MessageDisplay` 降到 10 秒。

## 2. stdout 被读成 JSON 还是纯文本，由首尾字符决定

忽略首尾空白后：

| stdout 形态 | 解读 |
|---|---|
| 以 `{` 开头且以 `}` 结尾 | 按 JSON 解析 |
| 以 `{` 开头但不以 `}` 结尾 | 纯文本 |
| 以其他任何字符开头 | 纯文本，**JSON 数组与带引号的 JSON 字符串也算纯文本** |

多行情形：每行各自都是合法 JSON、且没有任何一行是设了字段的输出对象时，整体当纯文本；有一行设了字段时，整体算解析失败。

因此：

- **stdout 必须只含那一个 JSON 对象。** shell profile 启动时打印任何文字都会破坏解析。
- **禁止输出 JSON 数组或 JSON 字符串**作为结构化结果，它们会被当纯文本。

## 3. 通用 JSON 输出字段

| 字段 | 作用 |
|---|---|
| `continue` | `false` 时 hook 跑完 Claude 完全停止处理，**优先于任何事件特定决策字段** |
| `stopReason` | `continue: false` 时展示给用户的消息，留在对话里，对话继续时 Claude 能看到 |
| `systemMessage` | 展示给用户的警告消息，**交付去向逐事件不同，见 § 4** |
| `terminalSequence` | 让 Claude Code 代发的终端转义序列，见 § 6 |
| `suppressOutput` | **无效字段**，接受但不生效。成功 hook 的 stdout 本就不进 transcript |

`hookSpecificOutput` 是需要更丰富控制的事件用的嵌套对象，**必须**含 `hookEventName` 且值等于事件名。

**输出字符串上限 10000 字符**，含 `additionalContext`、`systemMessage` 与纯文本 stdout。超限的内容被存成文件，替换为预览 + 文件路径。

## 4. `systemMessage` 的交付去向：这是最容易判错的一项

`systemMessage` 名义上是「展示给用户」，但**十余个事件会丢弃它或改道**。写 hook 前必须确认目标事件属于哪一类：

| 类别 | 事件 | `systemMessage` 的实际去向 |
|---|---|---|
| 正常展示给用户 | 多数事件 | transcript |
| **完全丢弃** | `Setup`、`InstructionsLoaded`、`MessageDisplay`、`Notification`、`ConfigChange`、`WorktreeCreate`、`WorktreeRemove`、`StopFailure` | 无 |
| **改道给 Claude 而非用户** | `DirectoryAdded` 的 `slash_command` 来源 | Claude 的下一轮上下文 |
| **只进 debug log** | `DirectoryAdded` 的 `register_repo_root` 来源 | debug log |
| **降级为短暂终端提示** | `CwdChanged`、`FileChanged` | 终端一闪而过的提示，**不进 SDK 消息流** |
| **改道给 Claude，用户看不见** | 任何 `async: true` 的 command hook | Claude 的下一轮上下文，见 `rules/05-async-execution.md` |

**规则：面向人类展示的输出，禁止挂在会丢弃或改道 `systemMessage` 的事件/配置上。** 这类事件只适合承载副作用（写日志、发通知、调外部服务）。

`Notification` 事件是这条规则的典型正例——它丢弃 `systemMessage`，但 `terminalSequence` 仍然生效，所以桌面通知类 hook 挂在它上面是正确的；把展示文本挂上去则不是。

## 5. `additionalContext`：给 Claude 的上下文

放在 `hookSpecificOutput` 里，与 `hookEventName` 并列。Claude Code 把它包成 system reminder 插入对话，**不作为聊天消息显示**。

插入位置逐事件不同：

| 事件 | 插入位置 |
|---|---|
| `SessionStart`、`SubagentStart` | 对话开头，第一个 prompt 之前 |
| `UserPromptSubmit`、`UserPromptExpansion` | 与提交的 prompt 并列 |
| `PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PostToolBatch` | 工具结果旁 |
| `Stop`、`SubagentStop` | 轮次末尾，对话继续以便 Claude 据此行动 |
| `PostModelSwitch` | 切换后的下一个请求 |

多个 hook 同一事件都返回时，Claude 收到全部值。

三条写法规则：

- **必须写成事实陈述，不要写成祈使式系统指令。** 「部署目标是 production」「本仓用 `bun test`」读起来是项目信息；写成带外系统命令的措辞会触发 Claude 的 prompt-injection 防御，导致它把文本转呈给用户而不是当上下文用。
- **静态约定不用 `additionalContext`**，用 `CLAUDE.md`（见 `rules/01-event-selection.md § 不要用 hook 承载静态约定`）。
- **注意 resume 时的过期风险**：注入的文本存进 transcript，`--continue` / `--resume` 时对过去的轮次**重放存档文本而不重跑 hook**，所以时间戳、commit SHA 这类值会变成陈旧值。`SessionStart` hook 会在 resume 时重跑（`source` 为 `"resume"` 或 `"fork"`），可借此刷新。

## 6. `terminalSequence`：hook 唯一的终端输出通道

hook 没有控制终端，直接写 `/dev/tty` 会失败。桌面通知、窗口标题、响铃**必须**通过 `terminalSequence` 由 Claude Code 代发。

白名单（超出即整个字段被忽略）：

- OSC `0`、`1`、`2`：窗口与图标标题
- OSC `9`：iTerm2 / ConEmu / Windows Terminal / WezTerm 通知，含 `9;4` 任务栏进度
- OSC `99`：Kitty 通知
- OSC `777`：urxvt / Ghostty / Warp 通知
- 裸 BEL

**被拒绝的**：CSI 光标与颜色序列、OSC 调色板、OSC 8 超链接、OSC 52 剪贴板写入、OSC 1337。

两个限制：

- 只在**交互式会话且界面在屏幕上**时才写出。`-p` 非交互模式与 Agent SDK 下该字段被忽略。
- `WorktreeCreate` 的 command hook 返回不了 JSON（stdout 被当作 worktree 路径读），因此用不上该字段；HTTP 形式的 `WorktreeCreate` 可以。

它的适用面比 `systemMessage` 宽——**在丢弃 `systemMessage` 与 `continue` 的事件上（如 `Notification`、`StopFailure`）`terminalSequence` 仍然生效**。

## 7. HTTP hook 的响应映射

HTTP hook 用状态码与响应体代替 exit code 与 stdout：

| 响应 | 结果 |
|---|---|
| 2xx + 空 body | 成功，等价 exit 0 无输出 |
| 2xx + JSON 对象 body | 按与 command hook 相同的 schema 解析；校验失败为非阻断错误 |
| 2xx + 其他 body（如纯文本） | 非阻断错误，**文本不会加进 Claude 的上下文** |
| 非 2xx | 非阻断错误，继续执行 |
| 连接失败 | 非阻断错误，继续执行 |
| 超时 | 按 § 1 的超时规则取消 |

**HTTP hook 无法只靠状态码表达阻断。** 要拦截工具调用或拒绝权限，**必须**返回 2xx 且 body 含对应决策字段。

`mcp_tool` hook 的文本输出按 command hook 的 stdout 规则解读（§ 2）。server 未连接或工具返回 `isError: true` 时是非阻断错误。

## 8. 静默失效清单

按排查顺序汇总本领域全部「不报错但无效果」的形态：

| 现象 | 根因 | 判据出处 |
|---|---|---|
| hook 完全没跑 | 路径拼错 → 非阻断错误放行 | § 1 hook 起不来 |
| hook 完全没跑 | 在非工具事件上设了 `if` | `rules/02 § if` |
| hook 完全没跑 | workspace trust 未接受 | `rules/06 § workspace trust` |
| hook 跑了但没拦住 | 用了 `exit 1` 而非 `exit 2` | § 1 其他 exit code |
| hook 跑了但没拦住 | 事件本身不可拦截 | `rules/01 § 能否拦截` |
| hook 跑了但没拦住 | `PermissionRequest` 不认 exit 2 | `rules/01 § 三个例外` |
| 输出没显示给用户 | 该事件丢弃或改道 `systemMessage` | § 4 |
| 输出没显示给用户 | 配了 `async: true` | `rules/05` |
| JSON 没生效 | stdout 混入了其他文本 | § 2 |
| JSON 没生效 | 输出的是数组或字符串而非对象 | § 2 |
| matcher 没过滤 | 该事件不支持 matcher，被静默忽略 | `rules/01 § matcher 支持情况` |
| matcher 匹配不到 | `mcp__server` 缺 `.*`，走了精确串路径 | `rules/02 § matcher 求值` |
| `SessionStart` 加载上下文没生效 | 用了 `mcp_tool` handler，启动时被跳过 | `rules/01 § handler 类型支持` |
| `once: true` 没注销 | 写在设置文件或 agent frontmatter 里 | `rules/02 § 定义位置` |
| 插件状态每次升级都丢 | 存在 `${CLAUDE_PLUGIN_ROOT}` 下 | `rules/02 § 路径占位符` |

排查手段：`claude --debug-file <path>`，或 `claude --debug` 后读 `~/.claude/debug/<session-id>.txt`（`--debug` **不**打印到终端）。要看 matcher 匹配细节设 `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose`。`/hooks` 菜单可只读查看全部已配置 hook 及其来源文件。
