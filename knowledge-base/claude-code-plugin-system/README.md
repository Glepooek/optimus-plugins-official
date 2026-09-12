# Claude Code 插件系统规范

> 版本：1.0.0

> 面向 **Claude Code 插件的创作、分发与治理**。收录清单 schema 与组件装配契约、marketplace 目录与七种插件源、版本解析与缓存语义、插件间依赖的版本约束、两套安装推荐协议、企业托管与门禁设置。内容取自官方 [Plugins](https://code.claude.com/docs/zh-CN/plugins)、[Plugins reference](https://code.claude.com/docs/zh-CN/plugins-reference)、[Plugin marketplaces](https://code.claude.com/docs/zh-CN/plugin-marketplaces)、[Plugin dependencies](https://code.claude.com/docs/zh-CN/plugin-dependencies)、[Plugin hints](https://code.claude.com/docs/zh-CN/plugin-hints)、[Plugin relevance](https://code.claude.com/docs/zh-CN/plugin-relevance) 六篇 2026-09-12 版本。

本领域负责**插件这一产物形态本身的机制**，不负责插件内各组件的编写规范。四条边界：

| 内容 | 归属领域 | 本领域只收什么 |
|---|---|---|
| hook 事件选型、exit code、输出契约、`async` 语义 | `claude-code-hooks`（43 条） | 插件 hook 的**声明位置与合并规则**，以及插件捆绑 MCP server 的作用域工具名。事件表与契约一律引用，不重写 |
| `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` 的语义与「持久状态别放 ROOT 下」 | `claude-code-hooks/rules/02-configuration.md § 5. 路径占位符` | **哪些组件的哪些字段**会内联替换这些占位符——这是组件装配契约，hook 领域只讲 hook 自己那一栏 |
| SKILL.md 六字段 frontmatter、`disable-model-invocation`、原生字段取舍 | `skill-authoring`（55 条） | 插件内 skill 的**命名空间与发现规则**（`/plugin:skill`、根 `SKILL.md` 单 skill 装配、`name` 缺失时的回退后果） |
| MCP 协议、原语、授权与安全 | `mcp`（14 条） | 插件捆绑 MCP server 的**声明位置与作用域名形式** |

**Codex 侧不适用。** 本仓为双 harness，但本领域全部条款描述的是 Claude Code 的插件加载与分发实现。Codex 有自己的 `codex plugin` 体系与 `.codex-plugin/plugin.json` 清单，字段与语义均不同——不要把本领域条款套用到 Codex 侧（对照见仓库 `AGENTS.md`「两个 harness 的必要差异」）。

## 文档目的

让插件的作者与 marketplace 维护者在落笔前就能判断：**这个字段写在哪一侧才生效、用户什么时候才会收到更新、什么配置会让插件静默少加载一个组件**。

插件系统的失效模式集中在三类，都不报错：

1. **版本没变 = 更新装不上。** 版本是缓存键。改了内容却没动 `version`，已安装的用户拿到的仍是旧缓存，`/plugin update` 报「已是最新」。
2. **两侧都写 = 一侧被静默忽略。** `plugin.json` 与 marketplace 条目有大量同名字段，优先级各不相同——`version` 永远取 `plugin.json` 且不给警告，`displayName` / `defaultEnabled` 却是条目优先。
3. **路径越界 = 插件照样加载，只是少一个组件。** 组件路径解析到插件目录外时报 `path escapes plugin directory`，插件继续加载，缺的那个组件不会有人注意到。

## 适用范围与读者

- **适用范围**：`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、插件根下各组件目录、`managed-settings.json` 中的插件治理键
- **平台**：全平台，Windows 与 macOS/Linux 的差异在条款内显式标注（link 模式、反斜杠路径、UNC 路径）
- **harness**：仅 Claude Code
- **读者**：编写插件的作者、维护 marketplace 的运营方、需要判断「为什么用户没收到更新」的排查者、以及为组织配置插件策略的管理员

## 收录判据

**判据进知识库，操作步骤进 skill。**

检验标准：这条内容能独立成为「查一下就照着判断」的依据吗？能 → 本领域。它是否必须知道「上一步做了什么」才有意义？是 → 属 skill，不收。

据此：

- 「`version` 在 `plugin.json` 与 marketplace 条目都写时，Claude Code 总是静默取 `plugin.json`」**收录**——单条可判，判错的代价是自己设的版本被忽略
- 「`commands/` 放进 `.claude-plugin/` 内，插件加载但命令全部不出现」**收录**——单条可判，是官方点名的常见错误
- 「怎么一步步排查插件没加载」**不收录**——是排查流程，依赖上一步结论，属 skill

三类内容**有意不收录**：

| 不收 | 原因 |
|---|---|
| 34 个 hook 事件的触发时机表、hook 五种 handler 类型 | 真源在 `claude-code-hooks`，抄录即制造两份需同步的同一事实 |
| `claude plugin *` 各子命令的完整选项表 | 查阅型资料，`--help` 随时可得且随版本增删频繁；只收其中构成判断依据的语义（如 `-y` 在会话内无效、`--prune` 只删自动安装的依赖） |
| LSP server 的 16 个配置字段明细 | 描述性字段表，非判断依据；只收其中的硬约束（同扩展名先注册者胜、日志必须走 stderr） |

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义。

| 级别 | 措辞 | 含义 | 违反处置 |
|---|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，违反会导致插件不加载、组件静默缺失、或用户收不到更新 | 视为缺陷，review / 脚本拦截 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 | review 说明理由后可豁免 |
| **建议 MAY** | "可以"、"建议" | 可选做法，不强制 | 无 |

## enforcement 取值说明

| 取值 | 本领域含义 |
|---|---|
| `ci` | 可由 `claude plugin validate` 或 `.githooks/check_external_entries.py` 机械判定 |
| `review` | 需人工判断意图（如版本幅度是否判断正确、该用哪种源），脚本无法代劳 |
| `advisory` | 提示性，不构成拦截理由 |

⚠️ 标 `ci` 不等于**已经**被本仓脚本覆盖。本仓 `.githooks/check_external_entries.py` 只覆盖 marketplace 外部引用条目的若干项；官方 `claude plugin validate` 覆盖 schema、重复插件名、源路径遍历、`relevance` 未知键与 `hosts` 形态。其余 `ci` 条目是「原理上可机械判定」，尚未落地脚本。

## 文件地图

| 文件 | 承载什么 | 什么时候读 |
|---|---|---|
| `rules/01-plugin-manifest.md` | `plugin.json`：可选性与 `name` 唯一必填、命名约束、元数据字段、未识别字段与 `--strict`、`defaultEnabled` 优先级链、`userConfig` 与 shell 注入拒绝、`channels` | 写或审 `plugin.json` 时 |
| `rules/02-directory-and-components.md` | 目录结构硬约束、组件默认位置、组件路径字段的替换 vs 追加语义、路径遍历限制与符号链接、占位符的逐组件替换范围、各组件自身的装配约束（skill/agent 命名空间、捆绑 MCP 作用域名、LSP、monitor、`bin/`、skills 目录插件） | 决定「组件文件放哪、路径怎么写」时 |
| `rules/03-marketplace-manifest.md` | `marketplace.json`：必填与可选字段、保留名称、条目与 `plugin.json` 的字段优先级、`strict` 模式、`renames` 迁移 | 写或审 `marketplace.json` 时 |
| `rules/04-plugin-sources.md` | 七种插件源的选型与字段、相对路径与 `pluginRoot`、`ref`/`sha` 固定、`archive` 完整性与鉴权、`command` 源与 copy/link 模式 | 决定「插件从哪取」时 |
| `rules/05-versioning-and-updates.md` | 版本解析五级回退、显式版本的固定陷阱、双写静默取舍、发布渠道、缓存与孤立目录、Node.js 包依赖安装 | 发版前、或排查「用户收不到更新」时 |
| `rules/06-dependencies.md` | `dependencies` 声明与 semver 范围、跨 marketplace 允许列表、发布标签约定、约束交集与冲突、启用/禁用联动、`prune` | 插件依赖另一个插件时 |
| `rules/07-suggestion-protocols.md` | 两套推荐协议：CLI 侧 `<claude-code-hint />` 标记与 marketplace 侧 `relevance` 信号，及各自的生效前提 | 想让用户被主动推荐安装时 |
| `rules/08-enterprise-governance.md` | 托管设置族（允许列表、阻止列表、命令源禁用）、组织设置分发的源限制与 `bin/` 禁令、容器种子目录、私有仓库凭证与后台更新 | 为组织配置插件策略、或分发私有插件时 |
| `reference/plugin-source-matrix.md` | 七种源 × 字段 / 固定方式 / 版本解析 / 组织设置可用性 / 最低版本要求的完整对照表 | 需要逐源查证时，作为 `rules/04`、`rules/05` 的取证出处 |
| `reference/relevance-signals.md` | 五种 `relevance` 信号 × 匹配时机 / 数量与长度上限 / 路径规范化 / 大小写敏感性的完整对照表 | 写 `relevance` 块时，作为 `rules/07` 的取证出处 |

## 阅读路径

- **第一次做插件**：`01` 写清单 → `02` 摆目录 → `05` § 1 决定版本策略
- **要把插件分发出去**：`03` 写 marketplace → `04` 选源 → `05` 定版本与渠道
- **用户收不到更新**：`05` § 2 版本固定陷阱 → `05` § 3 双写静默 → `04` § 7 `command` 源的哈希版本
- **组件没加载**：`02` § 1 目录硬约束 → `02` § 3 替换 vs 追加 → `02` § 4 路径遍历限制
- **给组织上策略**：`08` 托管设置族 → `07` § 2 `relevance` 的允许列表前提 → `04` § 7 `command` 源的阻止方式

## 索引与机器消费

条目索引在 `index.jsonl`，检索方式见 `knowledge-base/README.md` § 消费方式。本领域的机械可判定条款部分落地在 `.githooks/check_external_entries.py`（本仓 `marketplace.json` 外部引用条目的提交门禁），挂在 `.githooks/pre-commit` 上；覆盖范围见 `.githooks/README.md`。

⚠️ 本仓 `plugins/*/` 下的八个插件与根 `.claude-plugin/marketplace.json` 是**被本领域约束的对象**，不是消费者——它们不检索本领域。本仓专属的版本管理约定（两份 `plugin.json` 同值、marketplace 顶层 version 的升级时机、条目内永不写 `version`）在 `AGENTS.md`，它建立在本领域的官方机制事实之上，两者是约定与判据的分层关系，不是重复。

## 权威参考

- [Plugins reference](https://code.claude.com/docs/zh-CN/plugins-reference) —— 清单 schema、组件契约、缓存与版本管理的一手依据
- [Plugin marketplaces](https://code.claude.com/docs/zh-CN/plugin-marketplaces) —— marketplace schema、插件源、托管限制的一手依据
- [Plugin dependencies](https://code.claude.com/docs/zh-CN/plugin-dependencies) —— 依赖版本约束的一手依据
- [Plugin hints](https://code.claude.com/docs/zh-CN/plugin-hints) —— CLI 侧推荐协议的一手依据
- [Plugin relevance](https://code.claude.com/docs/zh-CN/plugin-relevance) —— marketplace 侧建议信号的一手依据
- [Plugins](https://code.claude.com/docs/zh-CN/plugins) —— 教学与迁移向，非规范
- [Settings reference](https://code.claude.com/docs/zh-CN/settings-reference) —— 插件相关设置键的语法出处
