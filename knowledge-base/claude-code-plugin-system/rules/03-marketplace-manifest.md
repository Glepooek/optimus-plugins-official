# 03 Marketplace 清单

> `marketplace.json` 的三个必填字段、保留名称机制、可选字段、条目与 `plugin.json` 的分工、`strict` 模式、`renames` 迁移史，以及下游同步渠道对名字的额外收窄。

`enforcement`：§ 1 的必填字段、§ 2 的保留名称、§ 4 的条目必填项、§ 6 的 `renames` 链环检测均可由 `claude plugin validate` 机械判定，标 `ci`；§ 5 的 `strict` 取值选择需人工判断运营意图，标 `review`。

## 1. 必填三字段，且一个名字只能对应一个 marketplace

marketplace 清单位于仓库根的 `.claude-plugin/marketplace.json`，三个字段**必填**：

| 字段 | 类型 | 约束 |
|---|---|---|
| `name` | string | kebab-case，**禁止**空格、控制字符与双向格式化字符。面向公众——用户安装时会看到（`/plugin install my-tool@your-marketplace`） |
| `owner` | object | `name` 必填，`email` 与 `url` 可选 |
| `plugins` | array | 可用插件列表 |

⚠️ **每个用户对每个名字只能注册一个 marketplace：添加第二个同名 marketplace 会替换第一个。** 因此想在一个 marketplace 名下发布多个插件，**必须**把它们列在同一份 `marketplace.json` 里，不能靠多个同名 marketplace 拼凑。

## 2. 保留名称：每次加载都重新检查

以下 marketplace 名称由 Anthropic 官方保留，第三方**禁止**使用：

`claude-code-marketplace`、`claude-code-plugins`、`claude-plugins-official`、`claude-plugins-community`、`claude-community`、`anthropic-marketplace`、`anthropic-plugins`、`agent-skills`、`anthropic-agent-skills`、`knowledge-work-plugins`、`life-sciences`、`claude-for-legal`、`claude-for-financial-services`、`financial-services-plugins`、`first-party-plugins`、`claude-tag-plugins`、`healthcare`。

**冒充官方的名字也一并被阻止**（如 `official-claude-plugins`、`anthropic-plugins-v2`）——这条不是字面清单匹配，起新名时不能只对着上面 17 个规避。

⚠️ **保留名称在每次加载 marketplace 时重新检查，不只是添加时。** 后果是这份清单会追溯生效：在某个名字成为保留名之前用该名注册的 marketplace 会**停止加载**，并报告它是「从不受信任的来源注册的」。处置是移除该 marketplace，改名后重新添加即可立即恢复。

版本沿革（判断某台机器为何行为不同时要用）：v2.1.205 之前 `first-party-plugins` 与 `healthcare` 不是保留名，且**已注册的 marketplace 继续加载**；v2.1.265 之前 `claude-tag-plugins` 不是保留名。

## 3. 可选字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `$schema` | string | 供编辑器补全与校验，Claude Code 加载时**忽略** |
| `description` | string | marketplace 简述。`validate` 缺它会给警告 |
| `version` | string | 清单版本 |
| `metadata.pluginRoot` | string | 裸插件源名解析到的目录，见 `rules/04-plugin-sources.md § 2. 相对路径与 pluginRoot`。需 v2.1.239+ |
| `allowCrossMarketplaceDependenciesOn` | array | 本 marketplace 的插件可以依赖的其他 marketplace。未列出的来源在安装时被阻止，见 `rules/06-dependencies.md § 3. 跨 marketplace 依赖需要显式允许` |
| `renames` | object | 旧 `name` → 当前名的映射，或 `null` 表示已下架。见 § 6。需 v2.1.193+ |

`description` 与 `version` 也接受写在 `metadata` 下，属向后兼容形态。

## 4. 条目字段：条目侧独有的七个

`plugins` 数组的每个条目**必填** `name`（kebab-case，同 § 1 的字符约束）与 `source`（见 `rules/04-plugin-sources.md`）。

条目可以包含[插件清单 schema](https://code.claude.com/docs/zh-CN/plugins-reference) 中的任何字段，**加上七个条目侧独有的字段**：

| 字段 | 作用 |
|---|---|
| `source` | 从哪取这个插件（必填） |
| `category` | 分类 |
| `tags` | 可搜索标签 |
| `strict` | `plugin.json` 是否为组件定义的权威（默认 `true`），见 § 5 |
| `relevance` | 何时向用户建议此插件的信号。**仅对管理员在托管设置中允许列表的 marketplace 生效**，见 `rules/07-suggestion-protocols.md § 2. relevance：本地匹配 + 管理员开关` |
| `headers` / `headersHelper` | `archive` 源的下载鉴权，见 `rules/04-plugin-sources.md § 6. archive 下载的鉴权：headers 与 headersHelper` |

条目还可以声明组件路径（`skills`、`commands`、`agents`、`hooks`、`mcpServers`、`lspServers`），语义与清单侧同名字段一致——含替换 vs 追加的区别与路径越界拒绝，见 `rules/02-directory-and-components.md § 3. 路径字段：三种合并语义，记错就少加载组件`。

**两侧同名字段的优先级不统一**（七个展示字段条目优先、`version` 是 `plugin.json` 优先且不给警告、`defaultEnabled` 条目优先），完整判据在 `rules/01-plugin-manifest.md § 3. 元数据字段在两侧同名，优先级不统一`，本篇不重复。

⚠️ 面向 marketplace 分发的插件，`description` **应该**写在条目上：安装前 Claude Code 只能为[相对路径源](../reference/plugin-source-matrix.md)的条目读到 `plugin.json`，其他源类型下用户在安装前只看得到条目自己的字段。

## 5. strict 模式决定谁是组件定义的权威

`strict` 控制 `plugin.json` 是否为组件定义（skill、agent、hook、MCP server、输出样式）的权威：

| 值 | 行为 | 什么时候用 |
|---|---|---|
| `true`（默认） | `plugin.json` 是权威，marketplace 条目可以用额外组件**补充**它，两侧合并 | 插件自己管自己的组件。绝大多数插件用这个 |
| `false` | **marketplace 条目是完整定义。** 若插件的 `plugin.json` 也声明了组件，那是冲突，插件无法加载 | marketplace 运营方要完全控制：插件仓库只提供原始文件，由条目决定其中哪些暴露为组件 |

⚠️ **`strict: false` + 插件自带声明组件的 `plugin.json` = 插件加载失败**，报 `Plugin my-plugin has conflicting manifests: both plugin.json and marketplace entry specify components.`。处置是删掉重复的组件定义，或去掉条目的 `strict: false`。

设置了 `headersHelper` 的条目**必须**同时设 `"strict": false`——目的是让条目成为插件的完整定义，用户在接受那条命令之前能看清插件包含什么。

## 6. renames 是只追加的迁移史

插件的 `name` 是稳定标识符，改它会破坏每个既有安装（见 `rules/01-plugin-manifest.md § 2. name 的命名约束与命名空间作用`）。**确实必须改名，或从 `plugins` 数组中下架插件时，必须加顶层 `renames` 条目**，否则老用户只会收到 `plugin-not-found`。

```json
"renames": {
  "formatter": "code-formatter",
  "legacy-linter": null
}
```

旧名仍在用户设置里时，Claude Code 的处置分两种：

| 映射值 | 行为 |
|---|---|
| 新名字 | 以新名加载插件，显示一行通知；随后在用户 / 项目 / 本地三个作用域中把 `enabledPlugins` 与 `pluginConfigs` 的旧键**重写为新键**，所以通知只出现一次 |
| `null` | 删除旧键，通知报告插件已从 marketplace 移除 |

⚠️ **改名的插件用远程源（如 `github`、`npm`）时，改名后会报 `plugin-cache-miss`**，用户须跑一次 `/plugin install` 才能以新名取到它。

**`renames` 必须当作只追加的历史对待**——即使你认为所有用户都已迁移，旧条目也**不要**删。Claude Code 会跟随链：后来把 `code-formatter` 再改成 `formatter-pro` 时，**必须**追加第二条而不是编辑第一条，这样还停在原始 `formatter` 的用户能经两跳解析到 `formatter-pro`。

改完映射**应该**跑 `claude plugin validate .`——它拒绝任何成环的链，以及不终止于 `null` 或 `plugins` 中已列名字的链。

⚠️ **托管与策略设置对 Claude Code 是只读的**，那里启用的插件无法被自动重写。改名后的插件每个会话都能加载，但**改名通知会一直重复**，直到管理员更新托管设置文件里的 `enabledPlugins`。经其他只读源（如 `--add-dir`）启用的插件同理。

v2.1.193 之前的版本**忽略** `renames` 字段，对旧名一律报 `plugin-not-found`。

## 7. 下游同步渠道对名字的额外收窄

Claude Code 自己接受的名字形态比下游宽。以下三条只在 `claude plugin validate` 中表现为**警告**，但会让下游同步失败——面向这些渠道分发时**必须**满足：

| 收窄 | 不合规的后果 |
|---|---|
| **claude.ai marketplace 同步要求 kebab-case 插件名** | 同步拒绝。Claude Code 本身接受其他形式 |
| **Claude Desktop 托管同步的字符集**：最多 128 字符，由字母数字与 `.` `_` `-` 组成，以字母或数字开头 | marketplace 名不合规 → **整个 marketplace 被拒**；插件条目名不合规 → 该**条目被静默删除**（不是报错） |
| **Claude Desktop 另有三个保留 marketplace 名**：`org`、`org-provisioned`、`unknown`（任意大小写） | Claude Code 接受，Claude Desktop 拒绝整个 marketplace |

v2.1.221 之前 `claude plugin validate` 不跑后两项检查，故老版本上「验证通过」不代表下游能同步。

## 8. validate 指向 marketplace 目录时检查什么

`claude plugin validate .` 指向 marketplace 目录时的覆盖范围是固定的，**它不打开插件的 skill / agent / command / hook 文件**：

- `marketplace.json` 的 schema 错误、**重复插件名**、源路径遍历
- 对 `source` 为本地路径的每个条目：一并校验该插件自己的 `plugin.json`，并在**条目的 `version` 与 `plugin.json` 中的版本不一致时给警告**（这正是「两侧都写 version」的检出点，见 `rules/05-versioning-and-updates.md § 3. 两侧都写 version 是静默取舍`）
- `plugin.json` 内发现的问题以条目索引为前缀，形如 `plugins[2] plugin.json →`

v2.1.196 起逐条目检查还会：包含 `source` 为 `.` 的插件；在 `marketplace.json` 位于 `.claude-plugin` 之外时也运行（相对该文件自己的目录解析源）；即使文件别处有 schema 错误也照样报告每个条目的问题。更早的版本跳过 marketplace 根目录下的插件。

要查 skill / agent / command 的 frontmatter 错误与 `hooks/hooks.json` 的 JSON 错误，**必须**另跑一次并指向含这些文件的目录——目录选择规则见 `rules/02-directory-and-components.md § 7. skill 与 agent 的命名空间与缺名回退`。

⚠️ **`validate` 不跟随目录内的符号链接。** 链接的 `skills` / `agents` / `commands` 目录会警告「其中没有任何内容被读取」，目录内的链接条目被跳过并计数警告——但**会话运行时是会加载它们的**。这意味着 validate 通过不等于这些文件没问题；要检查它们，须再跑一次并指向真实文件所在的目录。
