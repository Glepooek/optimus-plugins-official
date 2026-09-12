# 05 版本解析与更新

> 版本解析的五级回退、显式版本的固定语义、两侧都写 `version` 的静默取舍、发布渠道的版本区分要求、插件缓存与孤立目录清理、Node.js 包依赖的受限自动安装、持久数据目录。

`enforcement`：§ 3 的「条目内不写 `version`」可由本仓 `.githooks/check_external_entries.py` 与 `claude plugin validate`（本地路径源条目的版本不一致警告）机械判定，标 `ci`；§ 1 的源选型、§ 2 的三种版本化方法取舍、§ 4 的渠道设计需人工判断，标 `review`。

## 1. 版本解析的五级回退

**版本是缓存键。** `/plugin update` 与自动更新触发时，Claude Code 计算当前版本，若与已安装的版本相同就**跳过更新**。理解这条回退链是排查「用户收不到更新」的前提。

除 `command` 之外的每种源类型，版本取**第一个已设置**的项：

1. 插件 `plugin.json` 的 `version`
2. 插件在 `marketplace.json` 中条目的 `version`
3. **插件源的 git 提交 SHA**——适用于 git 托管 marketplace 中的 `github`、`url`、`git-subdir` 与相对路径源
4. **SHA-256 摘要**——适用于 `archive` 源：条目里的 `sha256` 固定值，或未固定时下载文件的摘要。Claude Code **截短为前 12 个字符**
5. **`unknown`**——适用于 `npm` 源，或不在 git 仓库内的本地目录

⚠️ **`command` 源不走这条链。** 它**始终**从命令生成的内容派生版本：单独的 12 字符内容哈希，或在设了版本时附加为 `<version>-<hash>`。**Claude Code 忽略 `command` 源条目里的 `version` 字段。** 后果是：命令的哈希输出一变就产生新版本，即使写死的版本字符串没动。link 模式下哈希覆盖的是打印目录的真实路径及其顶级条目，而非文件内容（见 `rules/04-plugin-sources.md § 8. copy 模式与 link 模式`）。

## 2. 三种版本化方法，和显式版本的固定陷阱

上述回退链给出三种可选方法：

| 方法 | 怎么做 | 更新行为 | 最适合 |
|---|---|---|---|
| **显式版本** | 在 `plugin.json` 设 `"version": "2.1.0"` | 用户**只在你改这个字段时**才收到更新 | 有稳定发布周期的已发布插件 |
| **提交 SHA 版本** | `plugin.json` 与条目**都省略** `version` | 源解析出的提交一变，用户就收到更新 | 正在积极开发的内部或团队插件 |
| **摘要版本** | 用 `archive` 源且两侧都省略 `version` | 有 `sha256` 固定时改固定值才更新；无固定时 zip 字节一变就更新 | 发布为 zip 的插件 |

⚠️ **显式版本的固定陷阱**：声明了 `"version": "1.0.0"` 却推了新提交而不改这个字符串，**既有用户保留缓存副本**，`/plugin update` 报「已是最新版本」。每次发布**必须**提升该字段，或干脆省略它以回退到解析出的版本。

`command` 源是唯一不被 `version` 固定的源类型——它的版本总含内容哈希。

用显式版本时**应该**遵循[语义化版本](https://semver.org)（`MAJOR.MINOR.PATCH`），并在 `CHANGELOG.md` 记录变更。

## 3. 两侧都写 version 是静默取舍

⚠️ **`plugin.json` 与 marketplace 条目都设了 `version` 时，Claude Code 总是取 `plugin.json` 的值，且不给任何警告。** 因此**不应该**两侧都写——一份过期的清单版本会静默盖掉你在 `marketplace.json` 里设的版本。

这条与 `rules/01-plugin-manifest.md § 3. 元数据字段在两侧同名，优先级不统一` 里的七个展示字段方向相反：那七个是条目优先，`version` 是清单优先。方向记反的代价是自己设的值被忽略。

唯一的检出手段：条目 `source` 是**本地路径**时，`claude plugin validate` 会在两值不一致时给警告（见 `rules/03-marketplace-manifest.md § 8. validate 指向 marketplace 目录时检查什么`）。其他源类型下**没有任何提示**。

**本仓的落地约定**：`.claude-plugin/marketplace.json` 的插件条目内一律不写 `version`，由 `.githooks/check_external_entries.py` 在提交时拦截。理由与操作见 `AGENTS.md`「版本管理规则」。

## 4. 发布渠道必须解析为不同版本

支持「稳定」与「最新」两条发布渠道的做法是：**建两个 marketplace，各自指向同一仓库的不同 `ref` 或 `sha`**，再通过托管设置把每个用户组分配到自己的 marketplace（按组端点管理设置，或按组的 Claude apps gateway 策略）。

⚠️ **每条渠道必须解析为不同的版本。** 用显式版本时，`plugin.json` **必须**在每个固定的 ref 上声明不同的 `version`；省略 `version` 时不同的提交 SHA 已天然区分。**两个 ref 解析出相同版本字符串时，Claude Code 视其为同一版本并跳过更新**——渠道就此失效且不报错。

两条组分配机制的注意点：

- 来自管理控制台的**服务器托管设置对组织内每个用户生效**，因此**无法**做按组分配
- 网关的**组策略的 `extraKnownMarketplaces` 是替换而非合并**全局策略的映射，所以组策略里**必须**列出该组需要的每一个 marketplace，不只是它的渠道 marketplace

## 5. 插件缓存与孤立目录

出于安全与验证目的，Claude Code 把 **marketplace 插件复制**到用户本地插件缓存 `~/.claude/plugins/cache`，而不是就地使用——唯一例外是 link 模式的 `command` 源。

复制形态下，**每个已安装版本是缓存中一个独立目录**，按 marketplace 与 plugin 分组、以解析出的版本命名，各自持有插件文件与 Node.js 包依赖的副本。从[发布标签](06-dependencies.md)解析出的依赖，目录名带 **commit-SHA 后缀**。

清理语义有三条容易误判的地方：

- 更新或卸载插件时，先前的版本目录被标记为**孤立**，在约 **14 天**后的后台扫描中删除。宽限期是为了让已加载旧版本的并发会话继续运行不出错
- ⚠️ **只在至少装有一个插件时才跑该扫描**——卸载最后一个插件后，孤立目录会一直留在磁盘上，直到你再装插件
- ⚠️ **符号链接进缓存的开发检出永不被视为孤立**，也永不被删除，其所在文件夹也不会被删；Claude Code 也不会在链接的检出里写版本跟踪文件。Claude Code 只在插件或 marketplace 文件夹不再含任何目录或符号链接时才把它从缓存移除

Claude 的 Glob 与 Grep 工具**在搜索时跳过孤立版本目录**，所以文件结果不会包含过期的插件代码。

## 6. Node.js 包依赖的自动安装

把插件复制进缓存时，Claude Code 也在那里安装插件**自己 `package.json` 里声明的** npm / Bun 包，使插件的 hook 与 MCP server 能加载它们。（依赖**其他插件**是另一回事，见 `rules/06-dependencies.md`。）

运行时机：每次创建复制的版本目录时——安装插件时、更新到新版本时、以及**会话启动时若已启用的插件尚未缓存**（例如换了新机器）。

**只在插件根目录同时有 `package.json` 与受支持的 lockfile 时才跑**：

| Lockfile | 命令 |
|---|---|
| `bun.lock` 或 `bun.lockb` | `bun install --frozen-lockfile --ignore-scripts` |
| `npm-shrinkwrap.json` 或 `package-lock.json` | `npm ci --ignore-scripts` |

有多个 lockfile 时按 `bun.lock` → `bun.lockb` → `npm-shrinkwrap.json` → `package-lock.json` 取**第一个命中**。

⚠️ **`yarn.lock` 与 `pnpm-lock.yaml` 被跳过**——因为 Yarn 与 pnpm 支持绕过 `--ignore-scripts` 的解析时配置钩子。

覆盖面最广的做法是**提供 npm lockfile**：Claude Code 从用户 PATH 运行匹配 lockfile 的包管理器，**缺失时不回退到另一种**。⚠️ **经 npm 源分发的插件必须用 `npm-shrinkwrap.json`**——npm 会从已发布的包里排除 `package-lock.json`。

三条安全与时限约束，**都无法关闭**（没有任何设置或环境变量能禁用这次自动安装）：

- **冻结解析**：`package.json` 与 lockfile 不一致时失败，而不是重新解析版本
- **无生命周期脚本**：`--ignore-scripts` 阻止 `preinstall` / `install` / `postinstall`，所以在这些脚本里构建原生模块的依赖会被下载但不编译
- **60 秒超时**：超时视为失败，且**可能在缓存副本里留下部分 `node_modules` 树**

⚠️ 取 `npm` 源插件**本身**时跑的是**启用生命周期脚本**的 `npm install`，发生在这次受限安装之前——两者约束不同，别混作一谈。

**失败或跳过永不阻止插件加载**：失败与「跳过 yarn/pnpm lockfile」会在 `claude --debug` 输出中记为警告；**有 `package.json` 但无 lockfile 的插件被跳过且不留任何日志**——这是最难发现的一档。

自动安装覆盖不了的依赖（需要生命周期脚本构建的包、Python 依赖、用 Yarn 或 pnpm 锁定的插件），**应该**从 hook 装进 § 7 的持久数据目录。

## 7. 持久数据目录

`${CLAUDE_PLUGIN_DATA}` 解析为 `~/.claude/plugins/data/{id}/`，其中 `{id}` 是插件标识符、且 `a-z`、`A-Z`、`0-9`、`_`、`-` 之外的字符被替换为 `-`。装为 `formatter@my-marketplace` 的插件对应 `~/.claude/plugins/data/formatter-my-marketplace/`。

用途是**一次安装语言依赖并跨会话与插件更新复用**：Python 依赖、用 Yarn 或 pnpm 锁定的依赖、以及必须运行生命周期脚本的包。marketplace 安装的插件可能根本不需要它——符合条件的 Node.js 包依赖已由 § 6 自动装好。

⚠️ **数据目录的生命周期长于任何单个插件版本，所以「只检查目录是否存在」检测不到更新是否改了插件的依赖清单。** 推荐模式是**把捆绑的清单与数据目录里的副本比对，不同就重装**：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "diff -q \"${CLAUDE_PLUGIN_ROOT}/package.json\" \"${CLAUDE_PLUGIN_DATA}/package.json\" >/dev/null 2>&1 || (cd \"${CLAUDE_PLUGIN_DATA}\" && cp \"${CLAUDE_PLUGIN_ROOT}/package.json\" . && npm install) || rm -f \"${CLAUDE_PLUGIN_DATA}/package.json\""
          }
        ]
      }
    ]
  }
}
```

存副本缺失或与捆绑副本不同时 `diff` 非零退出，同时覆盖首次运行与依赖变更；`npm install` 失败时尾部的 `rm` 删掉复制的清单，使下个会话重试。

**卸载时的删除语义**：从最后一个安装它的作用域卸载插件时，数据目录**自动删除**。`/plugin` 界面显示目录大小并在删除前提示；**CLI 默认删除**，传 `--keep-data` 才保留（例如测试新版本后要重装时）。
