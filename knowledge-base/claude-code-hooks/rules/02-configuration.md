# 02 配置与作用域

> 配置 JSON 的三层嵌套、定义位置的作用域、matcher 求值规则、命令的两种执行形态。本篇的错误几乎全是静默的。

`enforcement`：§ 2 的 matcher 字符集判定、§ 4 的 exec/shell form 配对、§ 5 的占位符引号规则均可机械校验，标 `ci`；§ 1 的作用域选择、§ 3 的 `if` 用法需人工判断，标 `review`。

## 1. 定义位置决定作用域

| 位置 | 作用域 | 可共享 |
|---|---|---|
| `~/.claude/settings.json` | 本机全部项目 | 否 |
| `.claude/settings.json` | 单个项目 | 是，可入库 |
| `.claude/settings.local.json` | 单个项目 | 否，gitignore |
| managed policy settings | 组织级 | 是，管理员控制 |
| 插件 `hooks/hooks.json` | 插件启用期间 | 是，随插件分发 |
| skill frontmatter | skill 被调用后的**整个会话余下部分** | 是 |
| subagent frontmatter | 该 subagent 运行期间 | 是 |

四条必须知道的语义：

- **各层是合并而非覆盖**：用户、项目、local 层各自追加自己的 hook，不会移除 managed 层的。同一个 handler 在多个设置文件中重复定义时只运行一次，但插件或 skill 里的同一份拷贝算独立的，会各跑一次。
- **skill frontmatter 的 hook 会活到会话结束**，不只在该 skill 那一轮。要让它跑完一次就注销，**必须**加 `once: true`——该字段**只在 skill frontmatter 生效**，写在设置文件或 agent frontmatter 里会被忽略。注意 `once` 只认「成功运行」：失败、exit 2 阻断、超时都不注销，下次匹配还会跑。
- **subagent 的 `Stop` hook 会被转换成 `SubagentStop`**。在 subagent frontmatter 里写 `Stop` 不会拦住主对话的停止。
- **`disableAllHooks` 关不掉 managed 层的 hook**。只有 managed 层自己设置的 `disableAllHooks` 才能。项目层的 `false` 会覆盖用户层的 `true`（按设置优先级取最终值）。

插件 hook 的写法约束见 § 5；本仓插件 hook 的版本管理见仓库 `AGENTS.md` § 版本管理规则。

## 2. matcher 求值：三条路径由字符集决定

`matcher` 怎么求值**不由你声明，由它包含哪些字符决定**：

| matcher 取值 | 求值方式 |
|---|---|
| `"*"`、`""`、或省略 | 匹配全部 |
| 只含字母、数字、`_`、`-`、空格、`,`、`\|` | **精确串**，或用 `\|` / `,` 分隔的精确串列表 |
| 含任何其他字符 | JavaScript 正则，**不锚定** |

由此产生的四个陷阱：

- **`mcp__memory` 匹配不到任何工具**。它只含精确字符集内的字符，因此按精确串比较，而实际工具名是 `mcp__memory__create_entities`。要匹配某 server 的全部工具**必须**写 `mcp__memory__.*`——`.*` 不是可选的美化，是让它走正则路径的开关。
- **正则不锚定**。`Edit.*` 会同时匹配 `Edit` 和 `NotebookEdit`。需要整串匹配**必须**写 `^Edit$`。
- **`FileChanged` 与 `StopFailure` 用更窄的精确字符集**：只有字母、数字、`_`、`|`。在这两个事件上写连字符、空格或逗号会让 matcher 落到正则路径，且只有 `|` 能分隔备选项。
- **插件自带的 MCP server 用带插件名的作用域段**：`mcp__plugin_<plugin-name>_<server-name>__<tool>`。按裸 server key 写的 matcher 对这些工具永不触发。

各事件的 matcher 匹配什么字段（工具名 / 会话来源 / 通知类型 / agent 类型 / 错误类型……）见 `reference/event-capability-matrix.md`；不支持 matcher 的事件清单见 `rules/01-event-selection.md § matcher 支持情况`。

## 3. `if` 是 best-effort，不是闸门

`if` 用 permission rule 语法在**工具名与参数上**做二次过滤，例如 `"Bash(git *)"`、`"Edit(*.ts)"`。四条约束：

- **只在五个工具事件上求值**：`PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PermissionRequest`、`PermissionDenied`。**在其他事件上设了 `if` 的 hook 永不运行**——这是静默失效，不是报错。
- **一个 `if` 只放一条规则**。没有 `&&`、`||` 或列表语法，多条件必须拆成多个 handler。
- **Claude Code 判断不出 Bash 会执行什么命令时，无论模式是否匹配都会运行你的 hook**。`$TOOL git push`、`echo $(date)` 配 `Bash(git push *)` 都会触发。
- 因此 **`if` 禁止用于硬性 allow/deny**。硬保证用 permission 系统，见 `rules/04-decision-control.md § 硬保证的边界`。

目录模式有个版本差异需注意：`"Edit(src/**)"` 只匹配工作目录下的 `src`；要匹配任意深度的 `src` 须写 `"Edit(**/src/**)"`。

## 4. exec form 与 shell form

由 `args` 字段是否存在决定，**不能同时享有两者的性质**：

| | exec form（有 `args`） | shell form（无 `args`） |
|---|---|---|
| 如何执行 | `command` 解析为可执行文件直接 spawn，**无 shell** | `command` 交给 shell（`sh -c` / Git Bash / PowerShell） |
| 参数 | 每个 `args` 元素原样作为一个参数，无需引号 | shell 做分词、变量展开、管道、重定向、glob |
| 特殊字符 | `'`、`$`、反引号原样传递 | 由 shell 解释 |

选用规则：

- **引用了路径占位符的 hook 应该用 exec form**。占位符会被替换成纯字符串，路径含空格时 exec form 无需任何引号处理。
- 需要管道、`&&`、重定向时才用 shell form，此时**必须**给每个占位符包双引号。
- **exec form 下 `command` 只放可执行文件名或路径**。含空格的裸名（如 `node script.js`）会 spawn 失败，Claude Code 会记警告；多余 token 应移入 `args`。含空格的绝对路径（`C:\Program Files\nodejs\node.exe`）是合法单值，不触发警告。

Windows 专有约束：**exec form 要求 `command` 解析到真实可执行文件**。npm / npx / eslint 在 `node_modules/.bin` 装的 `.cmd`、`.bat` shim 不是可执行文件，无 shell 无法 spawn。要在 exec form 下运行，直接调底层脚本：`"command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/node_modules/eslint/bin/eslint.js"]`。按名字跑 shim 只能用 shell form。

`shell` 字段（`"bash"` / `"powershell"`）在 `args` 存在时被忽略。PowerShell 的占位符写法另有陷阱，见 `rules/06-security-and-cost.md § PowerShell 占位符`。

## 5. 路径占位符

| 占位符 | 指向 |
|---|---|
| `${CLAUDE_PROJECT_DIR}` | 会话启动时的项目根 |
| `${CLAUDE_PLUGIN_ROOT}` | 插件安装目录，**每次插件更新都变** |
| `${CLAUDE_PLUGIN_DATA}` | 插件持久数据目录，跨更新存活 |

三条规则：

- **禁止把需要跨插件更新存活的状态写在 `${CLAUDE_PLUGIN_ROOT}` 下**。该路径含版本哈希，插件一升级状态即丢失。持久状态用 `${CLAUDE_PLUGIN_DATA}`，或固定的 `$HOME` 路径。
- **worktree 下 `${CLAUDE_PROJECT_DIR}` 不跟随**：它始终指向会话启动的项目根。要知道 Claude 当前实际在哪个目录，读输入 JSON 的 `cwd` 字段。
- 插件 hook 额外支持 `${user_config.*}` 替换，**仅在 exec form 下**。shell form 里引用 `${user_config.*}` 会直接报错而不执行；shell form 要取配置值须读 `$CLAUDE_PLUGIN_OPTION_<KEY>` 环境变量。

三个占位符同时也作为环境变量 `CLAUDE_PROJECT_DIR`、`CLAUDE_PLUGIN_ROOT`、`CLAUDE_PLUGIN_DATA` 导出给子进程，脚本内可直接读。

## 6. 运行环境

- handler 在**当前目录**下运行，继承 Claude Code 的环境。当前目录已不存在时（如被别的 shell 删掉的 worktree），依次回退到会话起始目录、项目根、home、系统 temp，并在 debug log 记警告。
- **macOS/Linux 上 command hook 运行在自己的 session 里，没有控制终端**。hook 进程及其子进程打不开 `/dev/tty`，无法直接向 Claude Code 界面写转义序列。要发桌面通知或设窗口标题**必须**用 `terminalSequence` 字段（见 `rules/03-output-contract.md § terminalSequence`）。Windows 本就没有 `/dev/tty`。
- 环境变量继承有两处剔除：`OTEL_*` 导出变量被移除；设了 `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` 时另有变量被剥离。
- **没有 `$CLAUDE_MODEL` 环境变量**。要跟踪会话模型变化用 `PostModelSwitch` hook 的 `to_model`；`$ANTHROPIC_MODEL` 不随 `/model` 切换而变。
