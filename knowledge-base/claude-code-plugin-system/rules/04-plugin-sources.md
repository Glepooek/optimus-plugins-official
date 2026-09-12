# 04 插件源

> 七种 `source` 形态的字段与固定方式、相对路径的解析基准与 `pluginRoot`、git 源的 `ref`/`sha` 取舍、`archive` 的完整性与鉴权、`command` 源的 copy/link 模式与用户接受语义。

`enforcement`：§ 2 的 `./` 前缀与禁 `../`、§ 3 的 40 位 `sha`、§ 5 的 `sha256` 长度与 HTTPS、§ 6 的命令文本 500 字符可打印 ASCII 均可由 `claude plugin validate` 或本仓 `.githooks/check_external_entries.py` 机械判定，标 `ci`；「该选哪种源」属选型判断，标 `review`。

七种源的完整对照表（字段 / 固定方式 / 版本解析 / 组织设置可用性 / 最低版本要求）在 [`reference/plugin-source-matrix.md`](../reference/plugin-source-matrix.md)，本篇只写构成判断依据的语义。

## 1. marketplace 源与 plugin 源是两件事

这两个概念常被混作一谈，混淆的后果是把固定写错位置：

| | 决定什么 | 在哪设 | 支持的固定 |
|---|---|---|---|
| **marketplace 源** | 从哪取 `marketplace.json` 目录本身 | 用户跑 `/plugin marketplace add`，或托管设置的 `extraKnownMarketplaces` | 基于 git 的支持 `ref`（分支/标签），**不支持 `sha`** |
| **plugin 源** | 从哪取 marketplace 中列出的单个插件 | `marketplace.json` 内每个条目的 `source` | 基于 git 的支持 `ref` **和** `sha`（精确提交） |

两者指向不同仓库、各自独立固定。托管在 `acme-corp/plugin-catalog` 的 marketplace 完全可以列出取自 `acme-corp/code-formatter` 的插件。

## 2. 相对路径与 pluginRoot

同仓库内的插件用以 `./` 开头的路径：

```json
{ "name": "my-plugin", "source": "./plugins/my-plugin" }
```

⚠️ **路径相对 marketplace 根解析，不是相对 `.claude-plugin/`。** 上例指向 `<repo>/plugins/my-plugin`，即使 `marketplace.json` 位于 `<repo>/.claude-plugin/marketplace.json`。

两条硬约束：

- **禁止**用 `../` 引用 marketplace 根之外的路径。`validate` 报 `plugins[0].source: Path contains ".."`
- **macOS 与 Linux 拒绝前导 `./` 之后任何位置含反斜杠的条目路径**，因此分隔符**必须**在每个平台都写 `/`

**裸名**是不含 `/` 的单个目录名（如 `"formatter"`）。要用裸名而非 `./` 路径，**必须**设 `metadata.pluginRoot` 指向它们解析到的目录——`"pluginRoot": "./plugins"` 让 `"source": "formatter"` 解析为 `./plugins/formatter`。需 v2.1.239+。

`metadata.pluginRoot` 本身**必须**是 marketplace 内的相对路径。它对已以 `./` 开头的源**不生效**；含 `/` 的源（如 `team-a/formatter`）**不是**裸名，即使设了 `pluginRoot` 仍需 `./` 前缀。

⚠️ **相对路径在基于 URL 的 marketplace 中一律失效。** 用户若以直接 URL 添加 marketplace（`https://example.com/marketplace.json`），Claude Code **只下载那一个文件**，不会按相对路径去该服务器取插件文件。安装时报 `its marketplace entry path does not stay inside the marketplace directory`，已安装的插件加载时报 `Plugin source path refused`。面向 URL 分发**必须**改用其他任一源类型，或把 marketplace 托管在 git 仓库里（git 形态会克隆整个仓库，相对路径才有效）。

## 3. 三种 git 源：sha 与 ref 同时设置时 sha 生效

`github`、`url`、`git-subdir` 三种源都支持 `ref`（分支或标签，默认为仓库默认分支）与 `sha`（完整 **40 字符** git 提交 SHA）。

| 源 | 必填 | 可选 | 特点 |
|---|---|---|---|
| `github` | `repo`（`owner/repo`） | `ref`、`sha` | 裸 `owner/repo` **默认经 SSH 克隆**，见 `rules/08-enterprise-governance.md § 7. 私有仓库凭证与后台更新` |
| `url` | `url`（`https://` 或 `git@`，`.git` 后缀可省，故 Azure DevOps / AWS CodeCommit 的无后缀 URL 也可用） | `ref`、`sha` | 任意 git 主机 |
| `git-subdir` | `url`、`path` | `ref`、`sha` | **稀疏部分克隆**，只取子目录，为大型 monorepo 省带宽。`url` 也接受 `owner/repo` 简写与 SSH URL |

⚠️ **`ref` 与 `sha` 同时设置时，`sha` 是生效的固定**，Claude Code 直接获取并检出该提交。

由此有一条通常成立、但有例外的推论：**在多数 git 主机上（GitHub、GitLab、Bitbucket），即使上游那个 `ref` 命名的分支或标签已被删除，只要提交仍可从仓库到达，安装依然成功。** 例外是**不支持按 SHA 获取提交的服务器（如 AWS CodeCommit）**——那里 `ref` 必须仍然存在，且固定的提交必须可从它到达。

## 4. npm 源

| 字段 | 必填 | 说明 |
|---|---|---|
| `package` | 是 | 包名或作用域包（`@org/plugin`） |
| `version` | 否 | 版本或版本范围（`2.1.0`、`^2.0.0`、`~1.5.0`） |
| `registry` | 否 | 自定义 registry URL，默认系统 npm registry |

⚠️ **`npm` 源没有可解析的版本来源。** 它不在 git 仓库内，版本解析回退链走到最后一级 `unknown`（见 `rules/05-versioning-and-updates.md § 1. 版本解析的五级回退`）。要让用户收到更新，`plugin.json` 里**必须**声明并逐版本提升 `version`。

⚠️ 取 `npm` 源插件本身时会跑**启用生命周期脚本**的 `npm install`——这与随后对插件自己依赖的受限安装（`--ignore-scripts`）不同，见 `rules/05-versioning-and-updates.md § 6. Node.js 包依赖的自动安装`。

## 5. archive 源：布局、体积与完整性

`archive` 把插件作为 zip 经 HTTPS 分发，用户机器上**无需 git 或 npm**。托管在任意静态文件服务器或工件仓库（S3、Artifactory、nginx）。需 v2.1.224+。

| 字段 | 必填 | 约束 |
|---|---|---|
| `url` | 是 | **必须**是 HTTPS。Claude Code 拒绝 `http://`，以及**环回、链接本地、云元数据主机**。**每个重定向跳转都必须满足同样的规则**，否则拒绝下载 |
| `sha256` | 否 | 存档的 SHA-256 摘要，**64 个十六进制字符**，大小写均可。每次下载都验证，不匹配则拒绝安装并报 `Plugin archive integrity check failed` |

**两种 zip 布局都可安装**：Claude Code 先在存档顶层找 `.claude-plugin/`，再到**单个**顶级文件夹内找。

```text
my-plugin.zip                  my-plugin.zip
├── .claude-plugin/            └── my-plugin/
│   └── plugin.json                ├── .claude-plugin/
└── commands/                      │   └── plugin.json
                                   └── commands/
```

⚠️ **不会再往深一层找**，嵌套更深的插件装不上。**存档大于 256 MiB 被拒绝。**

⚠️ **`sha256` 兼作版本，但只在两侧都没声明 `version` 时。** 若你声明了 `version`，那个字符串才是更新信号——**换了 zip 与摘要之后必须同时提升 `version`，否则用户保留缓存副本**。

版本兼容：v2.1.120–v2.1.223 上安装该插件失败并报 `This plugin uses a source type your Claude Code version does not support.`；**更早的版本上，含 `archive` 条目的整个 marketplace 无法加载**——一个条目就能拖垮整份清单。

## 6. archive 下载的鉴权：headers 与 headersHelper

从私有 registry 下载存档时，用 `headers` 发送固定 HTTP 头；值是短期凭证（registry 按需签发的令牌）时用 `headersHelper` 命令。需 v2.1.238+。

**放在哪个位置，决定哪些下载带头、以及命令何时运行**——这是选型的核心判据：

| 位置 | 哪些下载带头 | 何时运行该位置的 `headersHelper` |
|---|---|---|
| marketplace `url` 源 | 与 marketplace URL **同源**（同方案、主机、端口）的存档下载 | 每次获取 `marketplace.json` 之前、以及该源上每次存档下载之前。**一次运行的输出复用最多 60 秒** |
| plugin 条目 | 仅该条目的下载 | **仅当用户自己安装或更新那一个插件时**，且用户接受了命令 |

两个位置设了同名头时发送条目的值；同一位置内，命令打印的头覆盖同名的列出头。

设 `headersHelper` 的条目**必须**同时设 `"strict": false`（见 `rules/03-marketplace-manifest.md § 5. strict 模式决定谁是组件定义的权威`）。

**命令本身的四条硬要求**：

- **命令文本**：最多 500 个可打印 ASCII 字符，**不得有四个及以上连续空格**（防止把内容藏在空白后面）
- **输出**：stdout 打印一个「头名 → 字符串值」的 JSON 对象，**10 秒内以 0 退出**
- **shell 与工作目录**：经 `sh`（Windows 上 `cmd.exe`）从配置目录 `~/.claude` 或 `CLAUDE_CONFIG_DIR` 运行。**必须**给绝对路径或 `PATH` 上的命令——相对路径是相对该目录解析的，不是用户项目
- **不得引用 `${user_config.*}`**，见 `rules/01-plugin-manifest.md § 6.1 走 shell 的字段拒绝 ${user_config.*}`

**环境变量按声明来源分档处理**：来自 `marketplace.json` 条目、或项目 `.claude/settings.json` / `.claude/settings.local.json` 的命令，其环境中**每个名字含 `TOKEN`、`SECRET`、`KEY`、`AUTH` 的变量都被移除**（含 `ANTHROPIC_API_KEY`）；来自用户设置、`--settings` 文件、托管设置的命令**不做这个移除**。Claude Code 设置的变量：`url` 源命令得到 `CLAUDE_CODE_MARKETPLACE_URL` 与 `CLAUDE_CODE_MARKETPLACE_NAME`，条目命令得到 `CLAUDE_CODE_PLUGIN_NAME` 与 `CLAUDE_CODE_PLUGIN_ARCHIVE_URL`。

⚠️ **六种情况下命令不运行、或其输出被丢弃**——写鉴权方案前必须逐条排除：

| 情况 | 后果 |
|---|---|
| 命令非零退出、超 10 秒、或打印了非「JSON 字符串值对象」的任何内容 | 不进行那次获取或下载 |
| marketplace URL 不以 `https://` 开头 | 不运行该 `url` 源的命令，只发 `headers` 列出的头 |
| 下载被重定向**离开存档 URL 的源** | marketplace `url` 源与条目两侧的 `headers` 值与命令输出**全部丢弃** |
| 条目设了路由或身份类头 | 从条目的 `headers` 与命令输出中丢弃 `Host`、`Cookie`、`X-Forwarded-*` 等，**保留** `Authorization` 这类鉴权头 |
| 命令设在 `--add-dir` 目录的设置里 | 忽略该命令，只发该文件的 `headers` |
| 托管设置 `disableCommandPluginSources: true`，或 `allowManagedHooksOnly`（除非 `disableCommandPluginSources` 显式为 `false`） | 阻止命令。**但托管设置自身声明的 marketplace 仍然运行命令** |

**用户接受的绑定粒度**：条目的命令，用户**每次**自己安装或更新那个插件时都要接受（非交互 shell 传 `--yes`）。Claude Code **只运行它展示过的命令、只用于它展示过的存档 URL**；期间命令或 URL 变了就拒绝安装或更新（**仅查询字符串变化不算**）。

⚠️ **除「单个插件的安装或更新」以外的每条路径，都既不运行命令也不下载存档**：批量安装、来自插件建议的安装、作为另一个插件的依赖被拉入——该插件被拒绝并把用户指向 `/plugin` 里它自己的视图（批量中的其他插件照常安装；**依赖它的插件装不上，直到用户自己先装它**）；后台自动更新与会话启动（对从未下载过存档的插件）——列在 `/plugin` 错误选项卡里。

marketplace `url` 源的 `headersHelper` 声明在设置文件里而非 marketplace 发布的目录里，所以不按每次安装询问，改由**声明它的设置文件**决定：

| 设置文件 | 何时运行 |
|---|---|
| 用户设置、`--settings` 文件、机器上的托管设置文件 | 无需询问，**含后台 marketplace 刷新期间** |
| 项目 `.claude/settings.json` 或 `.claude/settings.local.json` | 仅在用户接受**该文件夹自身**的工作区信任对话框后。`-p` 与 SDK 会话不算接受，父文件夹的信任也不算 |
| 服务器托管设置 | 仅在用户于安全批准对话框中批准交付的设置后 |

⚠️ `-p` 与 SDK 会话无法显示安全批准对话框：其他交付的设置会应用，但 **marketplace 获取与任何需要该命令的存档下载会一直失败**，直到用户在交互式会话里批准。

v2.1.238 之前，Claude Code 下载条目存档时**不带**其 `headers` 或 `headersHelper`，依赖它们的安装失败并报 `HTTP 401 while downloading plugin archive from <url>`（状态码随 registry 而变）。

## 7. command 源：插件目录由本地工具现场生成

`command` 用于插件目录由本地安装的工具生成的场景（例如 IDE 按当前选定的工具链渲染出它的插件）。Claude Code 在用户安装时运行命令，并**每个会话在后台重跑一次**，所以用户无需重装即可拿到工具输出的变化。需 v2.1.229+。

| 字段 | 必填 | 约束 |
|---|---|---|
| `command` | 是 | shell 命令，在 stdout 打印插件目录的绝对路径作为**单行**并以 0 退出。**必须**是可打印 ASCII、最多 500 字符、无四个及以上连续空格——目的是让用户能看清他被要求接受的整条命令 |
| `timeout` | 否 | 等待秒数，**默认 60，最大 600** |
| `mode` | 否 | `"copy"`（默认）或 `"link"`，见 § 8 |

命令经平台 shell（`sh` / Windows 上 `cmd.exe`）**从用户主目录**运行。打印的那一行是含完整插件的目录绝对路径，**该路径可以在两次运行之间变化**。

⚠️ **四种情况下打印的路径被拒绝，安装或更新失败**：

- 目录顶层没有插件内容（既无 `.claude-plugin/`，也无 `skills/`、`commands/`、`agents/`、`hooks/`）
- 目录是 **Claude Code 启动的目录，或其某个父目录**
- Windows 上路径是 **UNC 路径**
- 命令运行超过 `timeout` 秒

**用户接受的绑定**：

- 用户从 `/plugin` 的插件详情屏安装、或在交互式终端用 `claude plugin install` / `claude plugin update` 时，Claude Code **先展示确切的命令字符串**，并为该次安装记录已接受的命令。已记录接受、命令又未变的 `update` 不再展示。非交互 shell 传 `--yes`
- **其他每条路径只运行用户已接受过的命令。** 未接受过任何内容时拒绝运行并告知用户如何查看
- ⚠️ **Claude Code 从不把 `command` 源插件作为另一个插件的依赖安装**——用户必须自己先装它
- ⚠️ **改了条目的 `command` 或切换了 `mode`，用户保留手上那一版，Claude Code 停止重跑命令。** 交互式会话的 `/plugin` 错误选项卡显示新命令，直到用户跑 `claude plugin update <plugin>@<marketplace>` 查看并接受

**重跑时机**（三种，其中两种是后台）：

1. 每次用户安装或更新插件
2. **每个会话一次**，对每个已启用的 `command` 源插件，会话启动后不久在后台跑。**这次运行不走 marketplace 自动更新**，故不受 marketplace 的自动更新设置影响
3. 启动或 `/reload-plugins` 时，已启用插件的已装版本从缓存中丢失时

⚠️ 用户设了 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 时，**两个后台运行被跳过**；显式安装与更新仍然运行命令。

命令的哈希输出变了时，Claude Code 把结果装成新版本并在运行中的交互式会话里重载它（切换范围同 `/reload-plugins`，见 `rules/02-directory-and-components.md § 6. 占位符的逐组件替换范围`）。若就地重载会让会话的提示缓存失效，改为提示用户自己跑 `/reload-plugins`。

管理员可用托管设置 `disableCommandPluginSources` 在全组织阻止 `command` 源；组织若设了 `allowManagedHooksOnly`，**默认即阻止** `command` 源（见 `rules/08-enterprise-governance.md § 4. disableCommandPluginSources 与 allowManagedHooksOnly 的联动`）。

版本兼容：v2.1.120–v2.1.228 上安装失败并报不支持该源类型；更早版本上**整个 marketplace 无法加载**。

## 8. copy 模式与 link 模式

| | copy（默认） | link |
|---|---|---|
| 插件文件 | 复制进版本化插件缓存 | **就地使用**，缓存条目里只放指向打印目录每个顶级条目的链接 |
| 版本来源 | 目录**内容的哈希** | 打印目录的**真实路径及其顶级条目**，不哈希文件内部 |
| 体积限制 | 拒绝 >256 MiB 或 >20,000 条目的目录 | 不适用 |
| Node.js 包依赖自动安装 | 会跑 | **跳过** |
| Windows | 支持 | **不支持，在那里安装 link 模式插件会被拒绝** |

选型判据：**大到不该被复制的插件目录用 `link`**（例如渲染出的 SDK 导出）。

用 copy 模式时，工具可以在命令退出后删除或重写目录，**内容相同的重跑算作最新**。

用 link 模式时有三条额外约束：

- **顶级条目若是指向打印目录之外的符号链接，安装失败**
- 打印的目录**必须在插件保持安装期间一直就位**——Claude Code 每次启动都经这些链接加载插件
- ⚠️ **版本由路径而非内容决定**，所以要表示新内容**必须打印不同的路径**；且**在打印目录内或其下方启动的会话中，插件根本不加载**
- link 模式跳过 Node.js 包依赖安装，因此打印的目录**必须**已包含插件需要的 `node_modules`
