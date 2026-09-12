# 01 插件清单

> `plugin.json` 的可选性、`name` 的唯一必填地位与命名约束、元数据字段在清单与 marketplace 条目两侧的优先级、未识别字段与类型错误的处置分档、`defaultEnabled` 的优先级链、`userConfig` 与 `channels`。

`enforcement`：§ 1 的必填字段、§ 2 的命名字符集、§ 4 的类型错误、§ 6 的 `userConfig` 字段完整性均可由 `claude plugin validate` 机械判定，标 `ci`；§ 3 的两侧写哪一侧、§ 5 的默认启用取舍需人工判断意图，标 `review`。

## 1. 清单可省略，但省略后插件名来自目录名

`.claude-plugin/plugin.json` **不是必需文件**。省略时 Claude Code 在默认位置自动发现组件（见 `rules/02-directory-and-components.md § 2. 组件默认位置`），并从目录名派生插件名。

需要以下任一情形时**必须**提供清单：

- 要声明元数据（`description`、`author`、`version` 等）
- 组件不在默认位置，需要自定义路径
- 要声明 `dependencies`、`userConfig`、`channels`、`defaultEnabled`

**提供清单时，`name` 是唯一必填字段。** 其余全部可选。

⚠️ **省略清单对 marketplace 安装的插件有一个隐蔽后果**：插件安装目录名是解析出的版本串，每次更新都变。若插件是「根 `SKILL.md` 单 skill」形态且该 `SKILL.md` 的 frontmatter 未设 `name`，skill 的调用名会回退到目录名，于是**每次插件更新，用户的调用名都变**。这类插件必须在 `SKILL.md` 里显式设 `name`（SKILL.md 字段规范见 `knowledge-base/skill-authoring/rules/01-skill-format.md`）。

## 2. `name` 的命名约束与命名空间作用

`name` **必须**采用 kebab-case，**禁止**包含空格、控制字符与双向格式化字符（Unicode BiDi）。

该名字有两个不可替代的作用，都不能用 `displayName` 代替：

| 作用 | 表现 |
|---|---|
| 组件命名空间 | 插件 `plugin-dev` 的 agent `agent-creator` 显示并调用为 `plugin-dev:agent-creator`；skill 为 `/plugin-dev:skill-name` |
| 稳定标识符 | 用户在 `enabledPlugins`、`pluginConfigs`、`/plugin install` 中引用它 |

由此两条硬约束：

- **改 `name` 会破坏每一个既有安装。** 只想改 UI 上的显示文本时**必须**改 `displayName` 并保持 `name` 不变。
- 确实必须改名或下架插件时，**必须**在 marketplace 侧登记迁移映射，否则老用户只会收到 `plugin-not-found`——见 `rules/03-marketplace-manifest.md § 6. renames 是只追加的迁移史`。

⚠️ **marketplace 条目名优先于清单名。** 当 marketplace 条目以不同名字列出该插件时，`enabledPlugins` 键与 `/plugin` 使用的是**条目名**，不是 `plugin.json` 的 `name`。两侧不一致会让作者按清单名给出的安装指令失效。

其他两处对 `name` 的额外收窄（比 Claude Code 自身更严）：

- **claude.ai marketplace 同步拒绝非 kebab-case**。Claude Code 接受其他形式，只在 `claude plugin validate` 给警告，但同步会拒。
- **Claude Desktop 的托管同步**只接受最多 128 字符、由字母数字与 `.` `_` `-` 组成、以字母或数字开头的名字。不合规的插件条目会被**静默删除**（不是报错），marketplace 名不合规则整个 marketplace 被拒。

## 3. 元数据字段在两侧同名，优先级不统一

七个展示字段可以同时出现在 `plugin.json` 与 marketplace 条目：`displayName`、`description`、`author`、`homepage`、`repository`、`license`、`keywords`。

**这七个字段一律条目优先**：条目设了就用条目的值，即使 `plugin.json` 设了不同值；条目没设才回落到 `plugin.json`。

⚠️ **不要把这条规律外推到全部同名字段。** 三个字段的优先级方向各不相同，记混任何一个都会导致自己设的值被静默忽略：

| 字段 | 哪一侧胜 | 记错的后果 |
|---|---|---|
| 七个展示字段 | **marketplace 条目** | 改了 `plugin.json` 的 `description` 但条目也设了，用户看不到改动 |
| `version` | **`plugin.json`**，且不给任何警告 | 在条目里设版本以为能覆盖，实际被静默忽略——详见 `rules/05-versioning-and-updates.md § 3. 两侧都写 version 是静默取舍` |
| `defaultEnabled` | **marketplace 条目** | 见 § 5 |

**安装前的可见性另有限制**：只有[相对路径源](../reference/plugin-source-matrix.md)的条目，Claude Code 才能在安装前读到插件自己的 `plugin.json`。其他源类型下，用户在安装前**只能看到条目自己的字段**。因此面向 marketplace 分发的插件，`description` 应该写在条目上，否则用户在选择安装时看不到它。

## 4. 未识别字段被忽略，类型错误则分档处置

Claude Code **忽略**它不认识的顶层字段。这是刻意设计，使一份清单可以同时充当 VS Code / Cursor 扩展清单、npm `package.json` 或 MCPB/DXT bundle 清单。

`claude plugin validate` 把未识别字段报为**警告而非错误**；若某字段与已知字段仅差一两个字符，警告会提示可能的正确名。仅有未识别字段警告的插件**仍然通过验证并在运行时加载**。

已识别字段的**值类型错误**则分两档，这个分档决定了故障是显性还是隐性：

| 字段 | 类型错时的行为 |
|---|---|
| 绝大多数字段 | **插件无法加载**，`validate` 报 error。例：`keywords` 写成字符串而非数组 |
| `experimental`、`metadata` | 非对象值被**忽略**，插件照常加载，`validate` 只报 warning |

**CI 中应该加 `--strict`**，把警告一并当作错误：

```bash
claude plugin validate ./my-plugin --strict
```

这是唯一能在发布前抓住「字段名拼错」与「从别的工具清单里带过来的残留字段」的手段——不加 `--strict` 时它们在运行时被静默吞掉，插件照常加载，声明的行为却不生效。

## 5. defaultEnabled 是兜底值，两件事优先于它

`defaultEnabled: false` 让插件安装后处于禁用态，用户需显式 `claude plugin enable` 才生效。**应该**给两类插件设它：会带来额外成本的（如每会话常驻的 MCP server），以及用户理应主动选择加入的（如连接外部服务的）。

它只是「没有其他因素决定状态时」的兜底。两件事优先：

| 优先项 | 语义 |
|---|---|
| 用户设置中的 `enabledPlugins` 条目（任意作用域） | 一旦写入，就跨插件更新与重装持续存在 |
| 依赖要求 | 插件被另一个活跃插件依赖时，Claude Code 在安装或启用时为它写入显式 `true` |

由此两条实际后果：

- **在后续版本改 `defaultEnabled` 不会翻转既有用户。** 他们的 `enabledPlugins` 已有显式值，改清单只影响新装用户。
- **被依赖的插件的 `defaultEnabled: false` 会被绕过。** 为满足活跃插件而引入的依赖一律以 `true` 安装，不论其自身默认值——见 `rules/06-dependencies.md § 6. 启用与禁用沿依赖链传递`。

marketplace 条目上的同名字段**优先于**清单里的值。

## 6. userConfig 声明启用时向用户索取的值

`userConfig` 让插件在启用时弹出配置对话框索取值，替代「让用户自己去改 `settings.json`」。键**必须**是合法标识符。每个选项的字段：

| 字段 | 必需 | 说明 |
|---|---|---|
| `type` | 是 | `string` / `number` / `boolean` / `directory` / `file` |
| `title` | 是 | 对话框中的标签 |
| `description` | 是 | 字段下方的帮助文本 |
| `sensitive` | 否 | `true` 时掩码输入，并存入安全存储而非 `settings.json` |
| `required` | 否 | `true` 时空值导致校验失败 |
| `default` | 否 | 用户未填时采用的值 |
| `multiple` | 否 | 仅 `string` 类型，允许字符串数组 |
| `min` / `max` | 否 | 仅 `number` 类型的边界 |

值的两种取用方式：

- **占位符替换** `${user_config.KEY}`：可用于 MCP 与 LSP server 配置、hook 命令。**非敏感值**还可用于 skill 与 agent 正文。
- **环境变量** `CLAUDE_PLUGIN_OPTION_<KEY>`（键名大写）：全部值都导出给 hook 进程。

### 6.1 走 shell 的字段拒绝 `${user_config.*}`

把用户配置的值替换进 shell 命令，等于让 shell 执行该值里的任意内容。因此三类字段**拒绝**该占位符，组件直接失败并报 `plugin command references user config`：

| 被拒绝的字段 | 改用什么传值 |
|---|---|
| shell form 的 hook 命令 | 改用带 `args` 的 exec form，见 `knowledge-base/claude-code-hooks/rules/02-configuration.md § 4. exec form 与 shell form`；或在脚本里读 `CLAUDE_PLUGIN_OPTION_<KEY>` |
| monitor 命令 | 从脚本自己拥有的配置文件读 |
| MCP 的 `headersHelper` | 从脚本自己拥有的配置文件读 |

⚠️ **monitor 进程不接收 `CLAUDE_PLUGIN_OPTION_<KEY>` 环境变量**，所以对 monitor 而言「读环境变量」这条退路也不存在，只剩配置文件一条路。

v2.1.207 之前这些字段会做替换，依赖该行为的插件**必须**更新。

### 6.2 值的存储位置与可读设置源

| 值类型 | 存储位置 |
|---|---|
| 非敏感 | 用户 `settings.json` 的 `pluginConfigs[<plugin-id>].options` |
| 敏感（macOS） | macOS Keychain，写入被拒时回落 `~/.claude/.credentials.json` |
| 敏感（无 keychain 平台） | `~/.claude/.credentials.json` |

⚠️ **Keychain 存储与 OAuth 令牌共享约 2 KB 总额度**，因此敏感值**必须**保持短小。

Claude Code 只从三个设置源读 `pluginConfigs`，优先级由高到低：**托管设置 → `--settings` → 用户设置**。

**项目的 `.claude/settings.json` 与 `.claude/settings.local.json` 中的 `pluginConfigs` 条目被忽略**——两个文件都在工作区内，克隆来的仓库可以借它们把值注入插件的 hook 命令、MCP 配置、LSP 命令与 monitor 命令。这条限制只针对 `pluginConfigs`；`enabledPlugins` 仍然遵守项目与本地设置。v2.1.207 之前这些条目会被读取。

三个源中只有用户设置可以移除：传不含 `user` 的 `--setting-sources` 即跳过。托管设置与 `--settings` 始终生效。

## 7. channels 必须绑定到本插件的 MCP server

`channels` 让插件声明一到多个消息频道，把外部消息注入对话（Telegram / Slack / Discord 形态）。

`server` 字段**必需**，且**必须**与本插件 `mcpServers` 中的某个键匹配——频道不能绑定到插件之外的 server。每个频道可带自己的 `userConfig`，schema 与 § 6 的顶层字段相同，用于在启用时索取 bot token、owner ID 这类值。
