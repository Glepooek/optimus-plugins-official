# 06 插件间依赖

> `dependencies` 的声明形态与 semver 范围、捆绑包形态、跨 marketplace 依赖的允许列表、`{plugin-name}--v{version}` 标签约定、多约束交集与冲突、启用与禁用的链式传递、`prune`、本地联调、四类依赖错误。

`enforcement`：§ 1 的 semver 语法、§ 3 的允许列表缺失、§ 4 的标签命名可由 `claude plugin validate` / `claude plugin tag` / 安装时校验机械判定，标 `ci`；§ 1 的范围宽窄取舍、§ 4 的发版节奏需人工判断，标 `review`。

## 1. dependencies 的两种条目形态

⚠️ **默认（不写版本约束）时依赖跟踪最新可用版本**，因此上游发布可能在无警告的情况下改变你插件脚下的依赖。约束的作用是把依赖锁在测试过的范围内，直到你自己选择升级。

在 `.claude-plugin/plugin.json` 的 `dependencies` 数组里声明：

```json
{
  "name": "deploy-kit",
  "version": "3.1.0",
  "dependencies": [
    "audit-logger",
    { "name": "secrets-vault", "version": "~2.1.0" }
  ]
}
```

**裸字符串**只给插件名，依赖其 marketplace 提供的任意版本。要更多控制则用对象：

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 是 | 插件名。**默认在声明插件所属的同一 marketplace 中解析** |
| `version` | 否 | 一个 [semver 范围](https://github.com/npm/node-semver#ranges)（`~2.1.0`、`^2.0`、`>=1.4`、`=2.1.0`）。依赖取**满足该范围的最高标记版本** |
| `marketplace` | 否 | 换一个 marketplace 解析 `name`。**跨 marketplace 默认被阻止**，见 § 3 |

⚠️ **预发布版本（如 `2.0.0-beta.1`）被排除，除非范围用预发布后缀显式选择加入**（如 `^2.0.0-0`）。写 `^2.0.0` 拿不到该版本线的 beta。

**安装时机与自动解析范围**：安装声明了依赖的插件时，Claude Code 自动解析并安装依赖——**唯二例外**是 marketplace 条目带 `command` 源或 `headersHelper` 的依赖，**必须**由用户自己先装（见 § 4 末）。此后 `/reload-plugins`、依赖插件所属 marketplace 的自动更新、在依赖插件上重跑 `claude plugin install`、以及 `claude plugin marketplace add` 都会按同样规则补装尚未安装的声明依赖。

## 2. 只含 name 与 dependencies 的捆绑包形态

清单除必填 `name` 外**可以只有 `dependencies` 数组**。安装它即拉取每一个依赖——这就是「把一套精选插件集打包在一次安装后面」的做法。

```json
{
  "name": "backend-standard",
  "version": "1.0.0",
  "description": "Standard plugin set for backend engineers",
  "dependencies": ["secrets-vault", "deploy-kit", { "name": "db-migrate", "version": "^3.0" }, "oncall-runbook"]
}
```

⚠️ **往标准集里加工具，必须发布新的捆绑包版本。** 而且**非 Anthropic marketplace 的自动更新默认是关的**，所以用户拿到新版只有两条路：在 `/plugin` 里为该 marketplace 打开自动更新（下次自动更新会把捆绑包移到新版并装上新增依赖），或跑 `claude plugin update <bundle>` 再跑 `/reload-plugins`。

要在全组织推开捆绑包，**应该**把它加进托管设置的 `enabledPlugins`。

## 3. 跨 marketplace 依赖需要显式允许

⚠️ **Claude Code 默认拒绝自动安装位于「与声明它的插件不同的 marketplace」中的依赖**，防止一个 marketplace 静默从未经审查的来源拉入插件。

允许的方式是由**根 marketplace** 的维护者把目标 marketplace 名加进 `marketplace.json` 的 `allowCrossMarketplaceDependenciesOn`：

```json
{
  "name": "acme-tools",
  "owner": { "name": "Acme" },
  "allowCrossMarketplaceDependenciesOn": ["acme-shared"],
  "plugins": [
    {
      "name": "deploy-kit",
      "source": "./deploy-kit",
      "dependencies": [{ "name": "audit-logger", "marketplace": "acme-shared" }]
    }
  ]
}
```

⚠️ **根 marketplace 指托管着用户正在安装的那个插件的 marketplace，且只查询它的允许列表——信任不会经中间 marketplace 传递。** 这条决定了多级依赖链下该改哪一份清单：改中间那份没用。

字段缺失或不含目标 marketplace 时，安装失败并报 `cross-marketplace` 错误，错误里点名要设置的字段。**用户仍可手动先装那个依赖，这样约束即被满足，无需改允许列表**——这是绕过运营方允许列表的合法路径，做安全评估时要计入。

## 4. 发布必须打 `{plugin-name}--v{version}` 标签

Claude Code **按 git 标签解析版本约束**。标签所在的仓库分两种情形：`github` / `url` / `git-subdir` 源用插件自己的仓库；marketplace 经相对路径引用的插件用 **marketplace 仓库**。

因此上游插件的每次发布**必须**标记为 `{plugin-name}--v{version}`，其中 `{version}` 与该提交的 `plugin.json` 中 `version` 一致。从插件目录跑：

```bash
claude plugin tag --push
```

该命令从插件清单与外层 marketplace 条目派生标签名，并在创建标签前**验证插件内容、检查 `plugin.json` 与 marketplace 条目版本一致、要求插件目录下工作树干净、标签已存在则拒绝**。`--push` 推到 `origin`（可用 `--remote` 改），推送失败时标签仍在本地创建且命令以错误退出；`--dry-run` 只打印将标记什么。自己保持两侧同步的话，直接 `git tag secrets-vault--v2.1.0` 等价。

**插件名前缀让一个 marketplace 仓库能托管多条独立版本线**；`--v` 分隔符按完整插件名做前缀匹配，所以插件名里含连字符也能正确处理。

解析过程：安装声明 `{ "name": "secrets-vault", "version": "~2.1.0" }` 的插件时，Claude Code 列出托管 `secrets-vault` 的仓库上的标签，筛出以 `secrets-vault--v` 开头的，取满足 `~2.1.0` 的最高版本。**插件自己的仓库上无标签满足该范围时安装失败**并报 `Dependency "secrets-vault@acme-tools" has no git tag satisfying ~2.1.0`。**相对路径插件无匹配标签时不同**：Claude Code 改为安装 marketplace 的当前副本，把约束检查推到插件加载时。

本地文件夹 marketplace：文件夹是 git 仓库时按同样方式解析标签（需 v2.1.196+）。两种情形下改为从文件夹当前内容安装依赖——更早的版本不读本地文件夹 marketplace 的标签（受约束的依赖只在该副本恰好满足范围时才加载），以及文件夹不是 git 仓库时根本没有标签。

两条容易被忽略的记录语义：

- **已解析标签的 semver 与 `plugin.json` 的 `version` 分开记录**，所以约束检查用的是实际取到的标签，即使那个提交处的 `plugin.json` 值已过期
- **标签解析安装的缓存目录名带 12 字符提交 SHA 后缀**，所以维护者强推标签到另一个提交时，下次安装会拿到新缓存目录而不是复用过期内容

⚠️ **`npm`、`archive`、`command` 源的依赖，约束不控制取哪个版本**——基于标签的解析只适用于 git 支持的源。约束仍在**加载时**检查，已装版本不满足则依赖插件被禁用并报 `dependency-version-unsatisfied`。对 `command` 源，Claude Code 检查依赖 `plugin.json` 里的版本并**忽略内容哈希后缀**；⚠️ **其 `plugin.json` 未设版本的依赖不满足任何约束**，所以约束它之前必须先给它设一个。

⚠️ **Claude Code 从不自己安装 `command` 源的依赖，也从不在依赖的 marketplace 条目上运行 `headersHelper`**——这两类依赖一律要用户先自己装。

## 5. 多个约束取交集

多个已安装插件约束同一依赖时，Claude Code **交集它们的范围**，把依赖解析为满足所有范围的最高版本：

| 插件 A 需要 | 插件 B 需要 | 结果 |
|---|---|---|
| `^2.0` | `>=2.1` | 在最高的、且 ≥ `2.1.0` 的 `2.x` 标签处**装一份**。两个插件都加载 |
| `~2.1` | `~3.0` | **插件 B 的安装失败**并报 `range-conflict`。插件 A 与依赖保持原样 |
| `=2.1.0` | 无 | 依赖停在 `2.1.0`。**插件 A 装着的期间，自动更新跳过更新的版本** |

**自动更新取的是满足每个已安装插件范围的最高 git 标签，而不是 marketplace 的最新版本**，所以依赖在其允许范围内继续收到更新。⚠️ **没有标签满足所有范围时，自动更新跳过该依赖**，并在 `/plugin` 错误选项卡里列出跳过情况、点名是哪些插件的约束造成的。

卸载最后一个约束该依赖的插件后，依赖不再被保持，**下次更新时恢复跟踪其 marketplace 条目**。

## 6. 启用与禁用沿依赖链传递

本节只针对从 marketplace 安装的插件；`--plugin-dir` 加载的副本见 § 8。

**启用插件也会在同一作用域启用它依赖的插件**，依赖自己还有依赖时一并启用，成功消息列出连带启用了什么。依赖无法启用时命令拒绝并说明原因：

| 条件 | 结果 |
|---|---|
| 依赖未安装 | 启用失败，为每个缺失依赖打印 `claude plugin install` 命令 |
| 依赖被组织的插件策略阻止 | 启用失败并点名被阻止的依赖 |
| 依赖在**优先级高于目标作用域**的作用域里被设为 `false` | 启用失败。须在该作用域启用它，或传 `--scope` 往那里写 |
| 全部依赖已安装且被允许 | 成功，为插件与每个尚未在目标作用域启用的依赖写入 `true` |

⚠️ **依赖清单里的 `defaultEnabled: false` 会被绕过**——Claude Code 为它写显式 `true`。安装同理：为满足活跃插件而引入的依赖一律以 `true` 安装，不论其自身默认值（另见 `rules/01-plugin-manifest.md § 5. defaultEnabled 是兜底值，两件事优先于它`）。

**禁用方向是反的**：另一个已启用插件仍依赖它时，禁用被拒绝。错误点名依赖方，并给出一条按正确顺序禁用、以你要求的那个结尾的链式命令：

```text
secrets-vault is still required by deploy-kit. Disable that plugin first, or
disable everything together: claude plugin disable deploy-kit@acme-tools && claude plugin disable secrets-vault@acme-tools
```

## 7. prune 只删自动安装的依赖

自动安装的依赖在装它的插件被卸载后**仍留在磁盘上**（以防重装依赖方，或用户想直接继续用该依赖）。清理用 `claude plugin prune`：列出不再被任何已安装插件需要的自动安装依赖，确认后删除。

⚠️ **用户自己安装的插件永不被 prune，只有经另一个插件 `dependencies` 数组自动安装的才会。** 这条是 prune 可以放心跑的前提。

无内容符合条件时打印 `Nothing to prune` 并说明原因后退出——**全新安装时这是预期输出，不是错误**。

默认在用户作用域运行并要求确认。`--scope project` / `--scope local` 换作用域；`--dry-run` 只列不删；`-y` 跳过确认。⚠️ **stdin 或 stdout 不是终端时，prune 只列出孤立项就退出，除非传 `-y`**。

卸载时顺带清理：`claude plugin uninstall <plugin> --prune`。同样的确认行为适用——非终端时卸载仍完成，但 prune 步骤只列出孤立项，不传 `-y` 就什么都不删。

## 8. 本地用 --plugin-dir 联调依赖

同时开发一个插件与它依赖的插件时，用 `--plugin-dir` 加载两者：

```bash
claude --plugin-dir ./my-dependency --plugin-dir ./my-plugin
```

⚠️ **依赖的本地副本满足你插件的依赖条目，即使该条目命名了某个 marketplace**，所以不必从其 marketplace 安装依赖。**Claude Code 不对本地副本检查版本约束**，故本地 `plugin.json` 不需要 `version`——这也意味着**本地联调通过不代表约束正确**。v2.1.242 之前，命名了 marketplace 的依赖条目从不匹配本地副本，Claude Code 会在加载时禁用你的插件。

两个插件在同一父文件夹下时，可以只把该文件夹传给 `--plugin-dir` 一次：文件夹本身不是插件时，Claude Code 加载其下每个含 `.claude-plugin/plugin.json` 的子文件夹。需 v2.1.265+。

尚未从 marketplace 安装依赖时，本地副本一消失，你的插件就停止加载：

- **禁用了本地副本**：下次插件加载时你的插件被禁用。命名了 marketplace 的依赖条目报 `Dependency "<name>@inline" is disabled — enable it or remove the dependency`，裸名条目按其裸名报告。**`<name>@inline` 是 Claude Code 识别每个 `--plugin-dir` 与 `--plugin-url` 插件的方式**
- **启动会话时漏了依赖那个 `--plugin-dir` 标志**：报依赖未安装

## 9. 四类依赖错误

依赖问题在 `claude plugin list` 与 `/plugin` 界面显示为描述性消息而非下表的字面代码，**Claude Code 会禁用受影响的插件直到问题解决**：

| 错误 | 含义 | 解决 |
|---|---|---|
| `dependency-unsatisfied` | 声明的依赖未安装，或已安装但被禁用 | 跑错误消息里给出的 `claude plugin install`。依赖的 marketplace 尚未配置时先 `claude plugin marketplace add`，Claude Code 会自动解析依赖；依赖是被禁用的则启用它 |
| `range-conflict` | 版本要求无法组合。消息会点明原因：无版本满足所有范围、范围不是合法 semver、或组合范围**太复杂无法交集** | 卸载或更新其中一个冲突插件、修正非法 `version` 字符串、简化长 `\|\|` 链，或请上游放宽约束 |
| `dependency-version-unsatisfied` | 已安装的依赖版本落在本插件声明范围之外 | 跑 `claude plugin install <dependency>@<marketplace>` 按当前全部约束重新解析 |
| `no-matching-tag` | 依赖的仓库没有满足范围的 `{name}--v*` 标签 | 检查上游是否按 § 4 的约定打了标签，或放宽范围 |

要编程式检查，跑 `claude plugin list --json`——有问题的插件带 `errors` 字段，加载正常的插件省略该字段。
