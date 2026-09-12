# 插件源对照表

本文件是 `rules/04-plugin-sources.md` 与 `rules/05-versioning-and-updates.md` 的取证出处：七种 `source` 形态逐项对照字段、固定方式、版本解析落点、组织设置可用性与最低 Claude Code 版本。规范条款在 `rules/`，本文件只承载对照数据，不带规范语气。

数据取自官方 [Plugin marketplaces](https://code.claude.com/docs/zh-CN/plugin-marketplaces) 与 [Plugins reference](https://code.claude.com/docs/zh-CN/plugins-reference) 2026-09-12 版本。

## 1. 字段与形态

| 源 | `source` 写法 | 必填字段 | 可选字段 |
|---|---|---|---|
| 相对路径 | 字符串，如 `"./my-plugin"` | 无（路径本身） | 无 |
| `github` | 对象 | `repo`（`owner/repo`） | `ref`、`sha` |
| `url` | 对象 | `url`（`https://` 或 `git@`，`.git` 后缀可省） | `ref`、`sha` |
| `git-subdir` | 对象 | `url`、`path` | `ref`、`sha` |
| `npm` | 对象 | `package` | `version`、`registry` |
| `archive` | 对象 | `url`（必须 HTTPS） | `sha256` |
| `command` | 对象 | `command` | `timeout`、`mode` |

相对路径的两个约束：**相对 marketplace 根**解析（不是相对 `.claude-plugin/`），必须以 `./` 开头，除非在 `metadata.pluginRoot` 下写裸名。

## 2. 固定方式与版本解析落点

| 源 | 固定方式 | 未声明 `version` 时版本解析落到 |
|---|---|---|
| 相对路径 | 随 marketplace 仓库的检出 | git 提交 SHA（marketplace 在 git 仓库内时）；否则 `unknown` |
| `github` | `ref`（分支/标签）或 `sha`（40 字符，**与 `ref` 同时设置时 `sha` 生效**） | git 提交 SHA |
| `url` | 同上 | git 提交 SHA |
| `git-subdir` | 同上 | git 提交 SHA |
| `npm` | `version`（版本或范围） | **`unknown`** |
| `archive` | `sha256`（64 位十六进制） | SHA-256 摘要**前 12 字符**（有 `sha256` 用固定值，否则用下载文件的摘要） |
| `command` | **不被 `version` 固定** | 始终为内容哈希：12 字符哈希，或设了版本时 `<version>-<hash>` |

`command` 源的 marketplace 条目 `version` 字段被忽略。link 模式下哈希覆盖打印目录的真实路径及其顶级条目，而非文件内容。

完整回退链与「两侧都写 version」的取舍见 `rules/05-versioning-and-updates.md § 1. 版本解析的五级回退` 与 `§ 3. 两侧都写 version 是静默取舍`。

## 3. 依赖版本约束的适用性

| 源 | 约束能否控制取哪个版本 |
|---|---|
| `github` / `url` / `git-subdir` | **能**——按 `{plugin-name}--v{version}` git 标签解析 |
| 相对路径 | **能**（标签在 marketplace 仓库上）；无匹配标签时改装 marketplace 当前副本，约束推到加载时检查 |
| `npm` / `archive` / `command` | **不能**——约束只在加载时检查，不满足则依赖插件被禁用并报 `dependency-version-unsatisfied` |

`command` 源另有两条：约束检查读依赖 `plugin.json` 里的版本并忽略内容哈希后缀；其 `plugin.json` 未设版本的依赖不满足任何约束。Claude Code 从不自行安装 `command` 源依赖，也从不在依赖条目上运行 `headersHelper`。详见 `rules/06-dependencies.md § 4. 发布必须打 {plugin-name}--v{version} 标签`。

## 4. 组织设置分发可用性与最低版本

| 源 | 经组织设置 > Plugins 分发 | 最低 Claude Code 版本 |
|---|---|---|
| 相对路径（以 `./` 开头） | ✅ | — |
| `metadata.pluginRoot` 下的裸名 | ❌ 被组织同步拒绝为不支持的源 | v2.1.239（裸名本身） |
| `github` | ✅ | — |
| `url` | ✅ | — |
| `git-subdir` | ✅ | — |
| `npm` | ❌ | — |
| `archive` | ❌ | **v2.1.224**；v2.1.120–v2.1.223 安装失败，更早版本整个 marketplace 无法加载 |
| `command` | ❌ | **v2.1.229**；v2.1.120–v2.1.228 安装失败，更早版本整个 marketplace 无法加载 |

组织设置分发的其余源规则（marketplace 仓库须私有/内部、私有插件源的两种例外、顶层 `bin/` 禁令）见 `rules/08-enterprise-governance.md § 5. 组织设置分发的源限制与顶层 bin/ 禁令`。

## 5. 缓存与就地使用

| 源 | 安装后 |
|---|---|
| 除下一行外的全部 | **复制**进 `~/.claude/plugins/cache`，每个版本一个目录 |
| link 模式的 `command` | **就地使用**，缓存条目里只放指向打印目录顶级条目的链接 |

符号链接在复制时的三档处置（插件内保留 / 同 marketplace 内解引用 / marketplace 外跳过），以及 `--plugin-dir`、本地路径、copy 模式 `command` 源只保留插件内链接的收窄，见 `rules/02-directory-and-components.md § 5. 符号链接按目标解析位置分三档`。

## 6. 其他源特有事实

| 源 | 事实 |
|---|---|
| `git-subdir` | 用**稀疏部分克隆**只取子目录，为大型 monorepo 省带宽。`url` 也接受 `owner/repo` 简写与 SSH URL |
| `github` | 裸 `owner/repo` **默认经 SSH 克隆**，`CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` 改走 HTTPS |
| `url` / `github` / `git-subdir` | `sha` 生效时，多数 git 主机上即使 `ref` 命名的分支/标签已删除，只要提交可达安装仍成功；AWS CodeCommit 这类不支持按 SHA 获取的服务器不成立 |
| `npm` | 取插件本身跑的是**启用生命周期脚本**的 `npm install`；插件自己的包依赖另走 `--ignore-scripts` 的受限安装 |
| `archive` | 两种 zip 布局可装（顶层 `.claude-plugin/`，或单个顶级文件夹内）；不再往深一层找；>256 MiB 被拒；`url` 拒绝 `http://` 与环回、链接本地、云元数据主机，每个重定向跳转须满足同样规则 |
| `command` | 打印**恰好一行**绝对路径并以 0 退出；`timeout` 默认 60、最大 600；copy 模式拒绝 >256 MiB 或 >20,000 条目；**link 模式在 Windows 上不支持** |
