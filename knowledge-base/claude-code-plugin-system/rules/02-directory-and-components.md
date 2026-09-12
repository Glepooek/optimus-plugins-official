# 02 目录结构与组件装配

> 目录布局的硬约束、九类组件的默认位置、清单路径字段的替换 vs 追加语义、路径遍历限制与符号链接处置、占位符的逐组件替换范围、各组件自身的装配约束。

`enforcement`：§ 1 的目录位置、§ 3 的 `./` 前缀、§ 4 的路径越界与反斜杠均可由 `claude plugin validate` 机械判定，标 `ci`；§ 3 的「该替换还是该追加」、§ 5 的符号链接布局需人工判断意图，标 `review`。

## 1. 只有 plugin.json 放 `.claude-plugin/`，其余一律插件根

**禁止**把 `commands/`、`agents/`、`skills/`、`hooks/`、`workflows/`、`output-styles/`、`themes/`、`monitors/` 放进 `.claude-plugin/` 目录内。`.claude-plugin/` 里**只有** `plugin.json`。

这是官方点名的最常见错误，症状具有欺骗性：**插件正常加载，只是组件全部不出现**。没有报错，`/plugin` 里插件是启用状态，skill 却一个都调不出来。

⚠️ **「插件根」指单个插件自己的目录，永远不是 `~/.claude/`。** 例如放在 `~/.claude/.mcp.json` 的 MCP 配置不会被读取。

正确布局：

```text
my-plugin/                    ← 插件根
├── .claude-plugin/
│   └── plugin.json           ← 只有这一个文件在这里
├── skills/
│   └── code-reviewer/SKILL.md
├── agents/
├── hooks/hooks.json
├── .mcp.json
└── scripts/
```

## 2. 组件默认位置

无清单或清单未声明路径时，Claude Code 扫描这些位置：

| 组件 | 默认位置 | 备注 |
|---|---|---|
| 清单 | `.claude-plugin/plugin.json` | 可选 |
| Skills | `skills/`（`<name>/SKILL.md` 结构） | 新插件用这个 |
| Commands | `commands/`（平铺 `.md`） | 旧形态，新插件**应该**改用 `skills/` |
| Agents | `agents/` | |
| Workflows | `workflows/` | |
| 输出样式 | `output-styles/` | |
| 主题 | `themes/` | 实验性组件 |
| Hooks | `hooks/hooks.json` | |
| MCP servers | `.mcp.json` | |
| LSP servers | `.lsp.json` | |
| Monitors | `monitors/monitors.json` | 实验性组件 |
| 可执行文件 | `bin/` | 插件启用时加入 Bash tool 的 `PATH`，可作裸命令调用 |
| 默认设置 | `settings.json` | 仅支持 `agent` 与 `subagentStatusLine` 两个键 |

⚠️ **插件根的 `CLAUDE.md` 不会作为项目上下文加载。** 插件通过 skill / agent / hook 贡献上下文，不通过 CLAUDE.md。要提供进入 Claude 上下文的说明，**必须**写在 skill 里。`claude plugin validate` 会对插件根的 `CLAUDE.md` 给警告。

`experimental` 键下的 `themes` 与 `monitors` 的 schema 在稳定前可能变化。声明位置正在迁移：顶层仍然有效，但 `validate` 会给警告，未来版本将**要求** `experimental.*`。

## 3. 路径字段：三种合并语义，记错就少加载组件

清单里的自定义路径**是替换默认目录还是追加到默认目录，逐字段不同**。这是本篇最容易出错的地方——判断错的后果是默认目录被静默停扫。

| 语义 | 字段 |
|---|---|
| **替换默认值** | `commands`、`agents`、`workflows`、`outputStyles`、`experimental.themes`、`experimental.monitors` |
| **追加到默认值** | `skills`（默认 `skills/` 始终被扫描） |
| **自有合并规则** | `hooks`、`mcpServers`、`lspServers`，见各自小节与 `knowledge-base/claude-code-hooks/rules/02-configuration.md § 1. 定义位置决定作用域` |

因此声明了 `commands` 就**不再**扫描默认 `commands/`。要保留默认值并追加，**必须**显式列出两者：

```json
"commands": ["./commands/", "./extras/"]
```

`skills` 有一个例外：**源解析为 marketplace 根（`"source": "./"`）的条目**，声明特定子目录会**替换**默认 `skills/` 扫描。这是为了让多个条目共享一个 `skills/` 文件夹时各自只加载自己那部分：

```json
"source": "./",
"skills": ["./skills/code-review", "./skills/docs"]
```

此形态下列出的路径就是该条目的完整集合，共享文件夹里的其他目录不会加载。列 `./skills/` 本身或插件根则保持完整扫描；列出的路径**全都不存在**时，退回默认扫描。

**当插件同时有默认文件夹和匹配的清单键时**，Claude Code 在 `claude plugin list` 与 `/plugin` 详情里警告哪个文件夹被忽略了，插件仍按清单路径加载。清单键指向的正是默认文件夹时不警告（如 `"commands": ["./commands/deploy.md"]`）。

全部路径字段的共同约束：

- 路径**必须**相对插件根并以 `./` 开头。唯一例外是 `skills` 也接受 `"."`
  - `"."` 与 `"./"` 都表示插件根本身
  - v2.1.221 之前 `"."` 通不过清单校验、插件无法加载，需兼容旧版时用 `"./"`
- 可以用数组指定多个路径
- 来自自定义路径的组件遵循相同的命名与命名空间规则

## 4. 路径不得越出插件目录，越界只丢一个组件

**禁止**引用插件目录之外的文件。Claude Code 拒绝解析到插件根之外的组件路径，**不论该路径写在 `plugin.json` 还是 marketplace 条目里**。这覆盖两种形态：指向外部的路径（如 `../shared-utils`），以及导向外部的符号链接（§ 5 的 marketplace 内例外除外）。

⚠️ **被拒绝时报 [`path escapes plugin directory`](https://code.claude.com/docs/zh-CN/errors)，然后插件在缺少该组件的情况下继续加载。** 这是本领域最典型的静默失效：没有加载失败，只是那一个组件从此不存在。

还有两条容易踩的细节：

- **macOS 与 Linux 拒绝含反斜杠的组件路径**，即使该路径并未越界。用反斜杠写的组件因此只在 Windows 上加载。路径**必须**用正斜杠，如 `./commands/deploy.md`。
- **安装时也不会把插件目录外的文件复制进缓存**，所以复制后的插件内脚本读取插件根之上的路径同样找不到文件——写脚本时不能依赖「构建机上那个相对路径存在」。

## 5. 符号链接按目标解析位置分三档

需要与同一 marketplace 的其他部分共享文件时，可以在插件目录内建符号链接。插件被复制进缓存时的处置**取决于链接目标解析到哪里**：

| 目标解析位置 | 处置 |
|---|---|
| 插件自己的目录内 | 在缓存中**保留为相对符号链接**，运行时继续解析到复制后的目标 |
| 同一 marketplace 内的其他位置 | **解引用**，把目标内容复制进缓存代替链接。这使元插件的 `skills/` 可以链接到 marketplace 中其他插件定义的 skill |
| marketplace 之外 | **跳过**（安全考虑），防止插件把任意主机文件拉进缓存 |

⚠️ **三档只适用于 marketplace 复制安装。** 对 `--plugin-dir` 安装的插件、来自本地路径的插件、以及 copy 模式的 `command` 源插件，**只保留解析到插件自己目录内的链接，其他一律跳过**——即中间那一档（跨插件共享）在这些形态下不成立。为本地开发写的跨插件链接，装到用户机器上可能就没了。

```bash
ln -s ../../shared-plugin/skills/foo ./skills/foo
```

Windows 上需从提升权限的命令提示符使用 `mklink /D`，或启用开发者模式。

## 6. 占位符的逐组件替换范围

三个路径变量的**语义**（各自解析成什么、为什么持久状态不能写在 `${CLAUDE_PLUGIN_ROOT}` 下）见 `knowledge-base/claude-code-hooks/rules/02-configuration.md § 5. 路径占位符`。本节只给组件装配契约缺的那一半：**哪些组件的哪些字段会内联替换它们**。

| 插件组件 | 会做占位符替换的字段 |
|---|---|
| Skill 与 agent 正文 | 占位符出现的任何地方 |
| Hook 与 monitor 命令 | 占位符出现的任何地方 |
| MCP `stdio` server | `command`、`args`、`env` |
| MCP `http` / `sse` / `ws` server | `url`、`headers`、`headersHelper` |
| LSP server | `command`、`args`、`env`、`workspaceFolder` |

**不在表内的字段不做替换**——写了占位符就是字面量。三个变量同时也作为环境变量导出给 hook 进程以及 MCP、LSP server 子进程，所以表外字段的替代方案是让脚本自己读环境变量。

引号规则：hook 命令**应该**用带 `args` 的 exec form，路径逐个作为参数传递，无需引号；shell form 的 hook 与 monitor 命令**必须**用双引号包住变量，如 `"${CLAUDE_PROJECT_DIR}/scripts/server.sh"`。

⚠️ **会话中途更新插件后，旧路径继续被使用。** hook 命令、monitor、MCP server 与 LSP server 都还指向前一个版本的目录。`/reload-plugins` 会把 hook、MCP、LSP 切到新路径，**monitor 需要重启会话**；无交互终端的会话中，reload 会让插件 MCP server 留在旧路径直到下一个会话。

## 7. skill 与 agent 的命名空间与缺名回退

插件名给全部组件加命名空间（见 `rules/01-plugin-manifest.md § 2. name 的命名约束与命名空间作用`）：skill 是 `/<plugin>:<skill>`，agent 在 @-mention 提示中显示为 `<plugin>:<agent>`。

**skill 的调用名来自 `SKILL.md` frontmatter 的 `name`**，因此不随安装目录名变化。未设 `name` 时回退到目录基名——对 marketplace 安装的插件，这个基名是解析出的版本串，每次更新都变（后果见 `rules/01-plugin-manifest.md § 1. 清单可省略，但省略后插件名来自目录名`）。

**根 `SKILL.md` 单 skill 装配**：插件根有 `SKILL.md`、没有 `skills/` 子目录、也没有 `skills` 清单字段时，自动作为单 skill 插件加载。这种布局**不需要**在 `plugin.json` 里写 `"skills": ["./"]`。

agent 的容错比其他来源宽：

| 情形 | 插件 agent | 项目 / 用户 / 托管 agent |
|---|---|---|
| frontmatter 无 `name` | 按文件名命名（`agents/reviewer.md` → `my-plugin:reviewer`） | **跳过该文件** |
| frontmatter 无法解析 | 按文件名命名，描述用 `Agent from <plugin> plugin`，**文件内每个字段都被忽略** | **跳过该文件** |

⚠️ 「无法解析就忽略全部字段」意味着 frontmatter 写坏时 `model`、`tools`、`disallowedTools` 全部失效，agent 仍然可调用——**这是最危险的一档静默降级**。要找出默认 `agents/` 目录里 frontmatter 无法解析的文件，**必须**跑 `claude plugin validate`；插件无清单时传的是 `agents` 子目录路径（`claude plugin validate ./my-plugin/agents`，需 v2.1.233+）。

出于安全原因，**插件提供的 agent 不支持 `hooks`、`mcpServers`、`permissionMode`** 三个 frontmatter 字段。`isolation` 的唯一合法值是 `"worktree"`。

## 8. 针对捆绑 MCP server 的 hook 必须用作用域名

插件可以在 `.mcp.json` 或 `plugin.json` 内联捆绑 MCP server。插件启用时自动启动，在 Claude 工具集里表现为标准 MCP 工具。

⚠️ **针对插件自己捆绑的 server 写 hook 时，必须用作用域名，写裸 server 键的匹配器永远不会触发。** 两种字段的形式不同：

| 位置 | 形式 |
|---|---|
| 工具匹配器与 `if` 字段 | `mcp__plugin_<plugin-name>_<server-name>__<tool>` |
| `mcp_tool` hook 的 `server` 字段 | `plugin:<plugin-name>:<server-name>` |

hook 事件选型、handler 类型、matcher 求值与输出契约一律见 `knowledge-base/claude-code-hooks/`，本领域不重复。

会话中途运行 `/reload-plugins` 时，Claude Code **保持配置未变的 server 的活动连接**，只重连配置变了的。

## 9. LSP server：三条硬约束

LSP 配置的完整字段表是查阅型资料（见官方 [Plugins reference](https://code.claude.com/docs/zh-CN/plugins-reference)），本节只收构成判断依据的三条。

**① 同一扩展名先注册者胜。** 多个已启用的 LSP server 在 `extensionToLanguage` 里声明同一扩展名时——不论来自一个插件还是不同插件——**第一个注册的处理该扩展名的文件，其余永不启动**。`/plugin` 界面显示警告并指名哪个插件的 server 处于活动状态。

**② 日志必须走 stderr，不得走 stdout。** Claude Code 只把 server 的 stdout 当协议消息读，且接受最大 64 KiB 的消息头与最大 32 MiB 的消息体。超出任一限制、或向 stdout 写非协议输出的 server 会被**断开，并计为一次崩溃**（计入 `restartOnCrash` 与 `maxRestarts`）。`transport` 写 `socket` 也一样——Claude Code 接受该值但仍在 stdio 上运行每个 server，故 stdout 规则对全部 server 生效。

**③ 配置无效的 server 被跳过，其他照常启动。** 缺 `command` 或 `extensionToLanguage` 即被跳过，原因**只在 `claude --debug` 输出里可见**。被跳过的 server 不声明其扩展名，所以声明同一扩展名的另一个有效 server 仍会接手这些文件——即约束 ① 的「第一个」指第一个成功注册的。

⚠️ `restartOnCrash` 与 `shutdownTimeout` 需要 v2.1.205+。**v2.1.205 之前 schema 接受这两个选项，但设置任何一个都会导致该 LSP server 在启动时被完全跳过**，原因仅在 `claude --debug` 里可见。

⚠️ **语言服务器二进制必须单独安装。** LSP 插件只配置连接方式，不包含 server 本身；`/plugin` Errors 选项卡出现 `Executable not found in $PATH` 即为此因。

## 10. Monitor：三条约束

monitor 是插件活跃时自动启动的后台进程，每行 stdout 作为通知传给 Claude。它与 Monitor tool 共享可用性约束：**仅在交互式 CLI 会话中运行**，以与 hook 相同的信任级别在非沙箱环境运行，在 Monitor tool 不可用的主机上被跳过。

**① `name` 必须在插件内唯一**——它正是防止「插件重载或 skill 再次被调用时起重复进程」的键。

**② `command` 不得引用 `${user_config.*}`**。命令经 shell 运行，Claude Code 拒绝该 monitor 并报 `plugin command references user config`，而不是做替换。**monitor 进程也不接收 `CLAUDE_PLUGIN_OPTION_<KEY>` 环境变量**，所以传值只剩「让脚本从它自己拥有的配置文件读」一条路（详见 `rules/01-plugin-manifest.md § 6.1 走 shell 的字段拒绝 ${user_config.*}`）。

**③ 会话中途禁用插件不会停止已在运行的 monitor**，它们在会话结束时才停止。

`when` 控制启动时机：`"always"`（默认）在会话启动与插件重载时启动；`"on-skill-invoke:<skill-name>"` 在本插件的该 skill 首次被调度时启动。命令的工作目录是**会话工作目录**，脚本需要在插件自己的目录下运行时**必须**前置 `cd "${CLAUDE_PLUGIN_ROOT}" && `。

## 11. `bin/` 与 `settings.json` 各有一条硬限制

**`bin/`**：插件启用时其中的可执行文件加入 Bash tool 的 `PATH`，可作裸命令调用。

⚠️ **通过 claude.ai 组织设置分发插件时，禁止存在顶层 `bin/` 目录**——两条分发路径都会拒绝。替代方案与错误文本见 `rules/08-enterprise-governance.md § 5. 组织设置分发的源限制与顶层 bin/ 禁令`。

**`settings.json`**（插件根，非 `.claude-plugin/` 内）：插件启用时应用的默认设置，**只支持 `agent` 与 `subagentStatusLine` 两个键**。写其他键不生效。

## 12. skills 目录插件：无 marketplace、无安装步骤

任何 skills 目录下含 `.claude-plugin/plugin.json` 的文件夹，会在下一个会话作为 `<name>@skills-dir` 插件加载——**原地发现，不复制进缓存**，与 marketplace 安装的复制语义相反。`claude plugin init <name>` 用于搭建。

同一棵 skills 目录树里三种东西并存，靠有无清单区分：

| 磁盘上是什么 | 它是什么 |
|---|---|
| `<skills-dir>/foo/SKILL.md`，无清单 | 一个普通 skill `foo` |
| `<skills-dir>/foo/.claude-plugin/plugin.json` | 一个插件 `foo@skills-dir`，可捆绑自己的 skill / agent / hook |
| `<plugin>/skills/bar/SKILL.md` | 插件内部打包的一个 skill `bar` |

放置位置决定作用域，而**项目作用域另有三条组件收窄**：

| skills 目录 | 作用域 | 加载条件与限制 |
|---|---|---|
| `~/.claude/skills/` | personal | 每个项目都加载，无额外限制 |
| `<cwd>/.claude/skills/` | project | 仅在接受该文件夹的工作区信任对话框后加载；其声明的 MCP server 走与项目 `.mcp.json` 相同的逐 server 审批；LSP server 仅在信任工作区后启动；**后台 monitor 一律不加载** |

⚠️ **项目作用域的 `@skills-dir` 插件只从会话主工作目录的 `.claude/skills/` 加载，不会像普通 skill 那样向上走到仓库根。** 从子目录启动会漏掉位于仓库根的插件——**必须**从仓库根启动，或用 `/cd` 把会话移过去（v2.1.246+）。

**改动的生效范围不一致**：改 `SKILL.md` 立即在当前会话生效；改 `hooks/`、`.mcp.json`、`agents/`、`output-styles/` **不生效**，需 `/reload-plugins` 或重启。停止加载的方式是删除文件夹或 `claude plugin disable <name>@skills-dir`——没有 `uninstall`，因为没有从 marketplace 装过任何东西。

**同名冲突的胜者**：任何其他来源的已启用插件（marketplace 安装、`@skills-dir`、`--plugin-dir`）与 claude.ai 同步插件（`<name>@synced`，仅在 Cowork 与云会话中存在）同名时，**Claude Code 加载前者并报告同步副本未加载**。v2.1.239 之前是反的（加载同步副本），且同步插件当时用的是 `@inline` 身份——与 `--plugin-dir` 插件相同，两者无法区分。
