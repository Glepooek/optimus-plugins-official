# Changelog

本文件记录 `claude-code-plugin-system` 领域的版本变更。版本号按领域独立管理，与其他领域互不关联。

## [1.0.0] - 2026-09-13

### Added

- 新建 `claude-code-plugin-system` 领域，收录 Claude Code 插件系统的创作、分发与治理规范，共 **68 条**索引条目（66 条 rule + 2 条 reference）
- `rules/01-plugin-manifest.md`：`plugin.json` 的可选性与 `name` 的唯一必填地位、清单与 marketplace 条目同名字段的三种优先级方向、未识别字段与类型错误的处置分档、`defaultEnabled` 的优先级链、`userConfig`（含走 shell 的字段拒绝 `${user_config.*}`、值的存储位置与可读设置源）、`channels`
- `rules/02-directory-and-components.md`：`.claude-plugin/` 只放 `plugin.json` 的硬约束、十三类组件的默认位置、路径字段的替换 vs 追加语义、路径越界与符号链接三档处置、占位符的逐组件替换范围、skill/agent 命名空间与缺名回退、捆绑 MCP server 的作用域名、LSP 与 monitor 的硬约束、`bin/` 与 `settings.json`、`@skills-dir` 插件
- `rules/03-marketplace-manifest.md`：`marketplace.json` 的必填三字段与「一名一 marketplace」、17 个保留名称与追溯生效、条目侧独有字段、`strict` 模式、`renames` 只追加迁移史、下游同步渠道的名字收窄、`validate` 指向 marketplace 目录时的覆盖边界
- `rules/04-plugin-sources.md`：marketplace 源与 plugin 源的区分、相对路径与 `pluginRoot`、git 源的 `sha` 优先、`npm` / `archive` / `command` 三种源的约束、`archive` 下载鉴权的 `headers` 与 `headersHelper`、copy 与 link 模式
- `rules/05-versioning-and-updates.md`：版本解析的五级回退、三种版本化方法与显式版本的固定陷阱、两侧都写 `version` 的静默取舍、发布渠道必须解析为不同版本、插件缓存与孤立目录、Node.js 包依赖的受限自动安装、持久数据目录
- `rules/06-dependencies.md`：`dependencies` 的两种条目形态与 semver 范围、捆绑包形态、跨 marketplace 依赖的允许列表、`{plugin-name}--v{version}` 标签约定、多约束交集与冲突、启用与禁用的链式传递、`prune` 范围、`--plugin-dir` 本地联调、四类依赖错误
- `rules/07-suggestion-protocols.md`：`<claude-code-hint />` CLI 标记协议（属性、两个强制条件、五条频率上限）与 marketplace `relevance`（允许列表前提、字段与三个展示面、五种信号的匹配时机、托管设置的两个条件、频率上限）
- `rules/08-enterprise-governance.md`：`strictKnownMarketplaces` 三值行为、允许列表匹配规则、`blockedMarketplaces` 与 `disableSideloadFlags`、`disableCommandPluginSources` 与 `allowManagedHooksOnly` 的联动、组织设置分发的源限制与顶层 `bin/` 禁令、团队自动添加与容器种子目录、私有仓库凭证与后台更新、发布前门禁
- `reference/plugin-source-matrix.md`：七种源 × 字段 / 固定方式 / 版本解析落点 / 依赖约束适用性 / 组织设置可用性与最低版本 / 缓存语义的完整对照表
- `reference/relevance-signals.md`：五种 `relevance` 信号 × 数量与长度上限 / 路径规范化 / 大小写敏感性 / 匹配方式的完整对照表，含 `manifestDeps` 的末尾锚定要求与四种静默失效成因汇总

内容取自官方 [Plugins](https://code.claude.com/docs/zh-CN/plugins)、[Plugins reference](https://code.claude.com/docs/zh-CN/plugins-reference)、[Plugin marketplaces](https://code.claude.com/docs/zh-CN/plugin-marketplaces)、[Plugin dependencies](https://code.claude.com/docs/zh-CN/plugin-dependencies)、[Plugin hints](https://code.claude.com/docs/zh-CN/plugin-hints)、[Plugin relevance](https://code.claude.com/docs/zh-CN/plugin-relevance) 六篇 2026-09-12 版本。

有意不收录：`claude plugin *` 子命令的完整选项表、LSP 配置的全部字段明细、各事件的 hook input 字段表——查阅型资料，只收其中构成判断依据的语义。
