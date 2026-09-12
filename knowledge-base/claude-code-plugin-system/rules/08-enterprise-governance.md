# 08 企业治理与托管设置

> 托管设置族（允许列表、阻止列表、sideload 与命令源禁用）的语义与匹配规则、组织设置分发的源限制与 `bin/` 禁令、团队自动添加与容器种子目录、私有仓库凭证与后台更新的差异、发布前门禁。

`enforcement`：§ 5 的源类型限制与 `bin/` 禁令由 claude.ai 组织同步在分发时强制拒绝，标 `ci`；托管设置的取值属策略决策，标 `review`。

本篇的读者是**为组织配置插件策略的管理员**与**面向组织分发插件的作者**。⚠️ 全篇设置一律在**托管设置**（`managed-settings.json`）中生效——**个别用户与项目配置无法覆盖它们**。

## 1. strictKnownMarketplaces 的三值行为

| 值 | 行为 |
|---|---|
| 未定义（默认） | 无限制，用户可添加任何 marketplace |
| **空数组 `[]`** | **完全锁定**，阻止每个 marketplace 源，**包括官方 Anthropic marketplace** |
| 源列表 | 允许列表强制执行，用户只能添加与条目匹配的 marketplace |

⚠️ **它限制的是「用户可以添加什么」，本身不注册任何 marketplace。** 要为用户自动注册某个允许的 marketplace，**必须**在同一份 `managed-settings.json` 里把它加进 `extraKnownMarketplaces`。

**官方 Anthropic marketplace 是唯一 Claude Code 会自行注册的**，且仅当允许列表允许时。⚠️ **自动注册覆盖不到每台机器**，最常漏掉两类：

- **在机器首次交互启动之前就运行的非交互环境**
- **Claude Code 曾在阻止该 marketplace 的策略下交互式运行过的机器**（例如空数组锁定期间）。Claude Code 记录了被阻止的尝试，**策略改了也不重试**

这两类机器上**必须**把官方 marketplace 也加进 `extraKnownMarketplaces`，或跑一次 `claude plugin marketplace add anthropics/claude-plugins-official`。

⚠️ **`strictKnownMarketplaces` 匹配插件来自的 marketplace，而不是其中的条目**——所以用户仍可从一个被允许的 marketplace 安装带 `command` 源的插件。要同时阻止 `command` 源，见 § 4。

## 2. 允许列表的匹配规则

**检查发生在任何网络或文件系统操作之前**，且在 marketplace 添加、插件安装、更新、刷新、自动更新时都运行。⚠️ **策略配置之前就添加过的 marketplace，若其源不再匹配允许列表，Claude Code 拒绝从它安装或更新插件**（已装的插件不会因此被删，但停止演进）。同样的强制也适用于 `blockedMarketplaces`。

除所有者通配符形式的 `github` 条目外，允许列表对大多数源类型用**精确匹配**——所有指定的字段都必须匹配：

| 源类型 | 匹配规则 |
|---|---|
| `github` | `repo` 必填，可以命名单个仓库，或用 `owner/*` 通配覆盖该所有者下每个仓库（需 v2.1.223+）。**单仓库条目的 `ref` 必须完全相同、或在 marketplace 源与允许列表条目中都不存在**，`path` 同理 |
| `url` | **完整 URL 必须完全一致** |
| `hostPattern` | marketplace 主机与正则匹配。GitHub Enterprise Server 或自托管 GitLab 的**推荐做法** |
| `pathPattern` | marketplace 的文件系统路径与正则匹配。用 `".*"` 允许任意文件系统路径，同时仍用 `hostPattern` 控制网络源 |

⚠️ **精确匹配把「仅尾斜杠不同」「`.git` 后缀不同」「`ssh://` 与 `https://` 方案不同」的 URL 视为不同值。** 组织的 marketplace 若能经多种 URL 形式克隆，**应该**优先用 `hostPattern` 条目而不是字面 URL，这样 `https://`、`ssh://`、`user@host:path` 三种形式都匹配。

## 3. blockedMarketplaces 与 disableSideloadFlags

阻止某个 GitHub 所有者下每个 marketplace 仓库，用所有者通配符形式：`{ "source": "github", "repo": "untrusted-org/*" }`（需 v2.1.223+）。⚠️ **通配符的匹配规则在阻止列表与允许列表之间不同**，配置前须查[所有者通配符](https://code.claude.com/docs/zh-CN/settings-reference)。

⚠️ **用户添加 Claude Code 会克隆（而非获取）的 `https://` 仓库 URL 时**（如裸 `github.com` / `gitlab.com` 仓库 URL），Claude Code 也会拿它去比对 `blockedMarketplaces` 里的 `url` 条目；条目命名同一 URL 即阻止添加。比对时**忽略 `.git` 后缀与用户在 `#` 后附加的任何 ref**。需 v2.1.232+；更早的版本只对「作为托管 `marketplace.json` 文件获取的 URL」匹配 `url` 条目——即那些版本上，克隆形态的仓库 URL 绕过了阻止列表。

要同时拒绝为单次运行 sideload 插件、agent 与 MCP server 的 CLI 标志，**应该**把 `disableSideloadFlags` 与 `strictKnownMarketplaces` 配对使用——只配后者时 `--plugin-dir` 一类标志仍然可用。

`claude plugin init` 搭建出的是 `@skills-dir` 源插件。要阻止这条路径，用 `strictKnownMarketplaces`，或在 `blockedMarketplaces` 里加 `{"source": "skills-dir"}`；**被阻止时 `plugin init` 在写入前就失败**。

## 4. disableCommandPluginSources 与 allowManagedHooksOnly 的联动

这两个设置的组合语义容易记反，而记反的后果是以为封住了 `command` 源、实际没封：

| 配置 | `command` 源与 `headersHelper` 命令 |
|---|---|
| `disableCommandPluginSources: true` | **阻止** |
| `allowManagedHooksOnly`（未显式设 `disableCommandPluginSources`） | **默认即阻止** |
| `allowManagedHooksOnly` + `disableCommandPluginSources: false` | **不阻止**——显式的 `false` 压过 `allowManagedHooksOnly` 的默认 |

⚠️ **两种阻止之下，托管设置自身声明的 marketplace 的命令仍然运行。** 这是刻意的例外（管理员自己交付的配置视为可信），但它意味着「阻止 command 源」不等于「机器上不会跑任何 marketplace 声明的命令」。

`command` 源与 `headersHelper` 的完整语义见 `rules/04-plugin-sources.md § 6. archive 下载的鉴权：headers 与 headersHelper` 与 `§ 7. command 源：插件目录由本地工具现场生成`。

## 5. 组织设置分发的源限制与顶层 bin/ 禁令

在 Team 或 Enterprise 计划上经 **组织设置 > Plugins** 分发插件时，四条源规则**必须**满足——组织同步不走用户的 git 凭证，而是通过 Claude GitHub App 或组织的 GitHub Enterprise App 读取：

- **marketplace 仓库必须是私有或内部的**
- **每个插件源必须是 `github`、`url`、`git-subdir`，或以 `./` 开头的相对路径。** ⚠️ **按 `metadata.pluginRoot` 下的裸名列出插件会被组织同步拒绝为不支持的源**——须写全路径（`./plugins/deploy-tools`）
- **插件源只在两种情况下可以是私有的**：与 marketplace 仓库同一所有者的 github.com 源；组织的 GitHub Enterprise 主机上装了 GHE App 的源
- ⚠️ **其他所有源都在无凭证的情况下获取**，所以不同所有者下的 github.com 仓库、以及其他主机（GitLab、Bitbucket）上的仓库**必须公开**

要包含私有插件，**应该**把插件文件夹放进 marketplace 仓库内并用相对路径引用——组织同步在分发期间打包每个插件，用户永不需要访问单独的源仓库。

⚠️ **禁止**在经组织设置分发的任何插件中包含**顶层 `bin/` 目录**。claude.ai 两条路径都拒绝：

| 路径 | 行为 |
|---|---|
| marketplace 同步 | 拒绝该插件并同步 marketplace 的其余部分。错误以 `Plugin contains a top-level bin/ directory` 开头 |
| 直接上传 | 以相同消息拒绝上传 |

替代做法：把可执行文件放在别的目录（如 `scripts/`），从 skill、hook 或 MCP server 配置中以 `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` 引用（`bin/` 的正常语义见 `rules/02-directory-and-components.md § 11. bin/ 与 settings.json 各有一条硬限制`）。

## 6. 为团队自动添加与容器种子目录

要让团队成员**信任项目文件夹时自动获得 marketplace**（不再单独提示），把它写进仓库的 `.claude/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": { "source": "github", "repo": "your-org/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "code-formatter@company-tools": true
  }
}
```

⚠️ **marketplace 状态每个用户只存一份，在 `~/.claude/plugins/known_marketplaces.json`，不是按项目存。** 用本地 `directory` / `file` 源加相对路径时，路径相对**仓库主检出**解析——**从 git worktree 运行 Claude Code 时路径仍指向主检出，所有 worktree 共享同一个 marketplace 位置**。

**容器镜像与 CI** 用 `CLAUDE_CODE_PLUGIN_SEED_DIR` 在构建时预填充，启动时无需克隆任何东西。目录结构镜像 `~/.claude/plugins`：

```text
$CLAUDE_CODE_PLUGIN_SEED_DIR/
  known_marketplaces.json
  marketplaces/<name>/...
  cache/<marketplace>/<plugin>/<version>/...
```

多个种子目录用 `:`（Unix）或 `;`（Windows）分层，按顺序搜索，**第一个含给定 marketplace 或插件缓存的种子胜出**。构建时可直接把 `CLAUDE_CODE_PLUGIN_CACHE_DIR` 设为目标种子路径，省掉复制步骤。

五条行为细节，其中三条会改变运维方式：

- **只读**：种子目录永不被写入。⚠️ **因为 git pull 在只读文件系统上会失败，种子 marketplace 的自动更新被禁用**
- ⚠️ **种子条目优先**：每次启动时，种子里声明的 marketplace **覆盖**用户配置中任何匹配条目。**要退出某个种子插件，用 `/plugin disable`，不要删 marketplace**
- **路径解析靠运行时探测** `$CLAUDE_CODE_PLUGIN_SEED_DIR/marketplaces/<name>/`，而不是信任种子 JSON 里存的路径——所以挂载到与构建时不同的路径也能工作
- ⚠️ **变更被阻止**：对种子管理的 marketplace 跑 `/plugin marketplace remove` 或 `update` 会失败，并提示要求管理员更新种子镜像。更新全部 marketplace 时，种子管理的条目被跳过、其他照常更新
- **与设置组合**：`extraKnownMarketplaces` 或 `enabledPlugins` 声明的 marketplace 已存在于种子中时，用种子副本而不克隆

## 7. 私有仓库凭证与后台更新

⚠️ **「用户自己跑的命令」与「后台自动更新」的凭证行为不同，这是私有 marketplace 间歇性失败的根因。**

**用户自己跑的命令**（`/plugin marketplace add`、`/plugin install`、`/plugin update`、`/plugin marketplace update`）使用现有 git 凭证助手，所以经 `gh auth login`、macOS Keychain、`git-credential-store` 的 HTTPS 访问与终端里一致。SSH 访问可用的前提是**主机已在 `known_hosts` 里、且密钥已加载到 `ssh-agent`**——Claude Code 抑制了 SSH 的交互式提示（主机指纹、密钥口令），所以缺任一条就是静默失败。⚠️ **GitHub `owner/repo` 简写源默认经 SSH 克隆**，要改走 HTTPS 须设 `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`。

**后台自动更新默认为其 `git pull` 禁用 git 凭证助手**，所以即使配了助手，pull 也无法对 HTTPS 上的私有仓库鉴权。SSH 远程不受影响。pull 失败时 Claude Code **回退到从头重新克隆**——重新克隆确实用存储的凭证，但**在大型仓库上可能超时**。

两个设置让私有 marketplace 行为可预测：

- **`CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1`**：后台 pull 失败时保留现有克隆，而不是删掉重新克隆。插件继续以最后同步的状态工作。**离线或隔离环境必须设它**——否则每个会话都会重复失败的重新克隆尝试，每个 git 操作可等 120 秒
- **配置 git 凭证助手**（如 `gh auth setup-git`），让重新克隆回退能无提示鉴权

⚠️ **仅在环境里设提供商令牌（如 `GITHUB_TOKEN`）本身不启用后台鉴权**——令牌只经配置好的凭证助手生效（例如 `gh` CLI 的助手会读 `GH_TOKEN` 与 `GITHUB_TOKEN`）。

要让后台 pull 本身经 HTTPS 鉴权，**应该**配全局 git URL 重写：它把令牌嵌进远程 URL，所以即使后台 pull 禁用了凭证助手也生效，且成功的 pull 会跳过重新克隆回退。

```bash
git config --global url."https://x-access-token:YOUR_TOKEN@github.com/acme-corp/plugins".insteadOf "https://github.com/acme-corp/plugins"
```

⚠️ **必须把重写范围限定到 marketplace 仓库或组织路径。仅以主机为基础的重写会作用于本机对该主机的每次 fetch 与 push，并覆盖你的正常凭证，包括对你自己仓库的 push。**

各提供商期望的用户名不同（自托管服务器把主机名替换为自己的）：

| 提供商 | 重写后的 URL 形式 |
|---|---|
| GitHub | `https://x-access-token:YOUR_TOKEN@github.com/acme-corp/plugins` |
| GitLab | `https://oauth2:YOUR_TOKEN@gitlab.com/acme-corp/plugins` |
| Bitbucket | `https://x-token-auth:YOUR_TOKEN@bitbucket.org/acme-corp/plugins` |

⚠️ **重写以纯文本形式把令牌存在 gitconfig 里，所以必须用对 marketplace 仓库只读的令牌。**

**git 超时默认 120 秒**（覆盖克隆插件仓库与拉取 marketplace 更新），大仓库或慢网络需调 `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS`（毫秒）。完全离线部署**应该**改用 § 6 的种子目录，而不是调超时。

## 8. 发布前门禁

两道门禁覆盖的是不同层面，**不能相互替代**：

- **`claude plugin validate`** 检查文件结构与 schema。CI 中**应该**加 `--strict` 把警告当错误（见 `rules/01-plugin-manifest.md § 4. 未识别字段被忽略，类型错误则分档处置`）。它的覆盖边界见 `rules/03-marketplace-manifest.md § 8. validate 指向 marketplace 目录时检查什么`
- **`claude plugin eval`** 检查插件是否真的改变了 Claude 在实际提示上的行为。发布新版本前**应该**跑插件的 eval 套件——`validate` 通过只说明结构没错，不说明插件有用
