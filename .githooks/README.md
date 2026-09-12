# .githooks

仓库一致性门禁。检查的是**失效后会损害仓库长期状态**的东西，与某一次提交的内容无关——只是借提交这个必经关口拦截。

提交行为本身的规范（暂存原子性、commit message 格式、推送流程）不在这里，由 `commit-cc-plugin` skill 承担。

## 启用

配置在本机 `.git/config` 里，**不随仓库分发**，新克隆后需执行一次：

```bash
git config core.hooksPath .githooks
```

未启用时 hook 静默不执行，不会有任何提示。

## 检查项

| # | 检查 | 失效后果 |
|---|---|---|
| 1 | 每插件两份 `plugin.json` 的 `version` 同值 | 两个 harness 读到不同版本号 |
| 2 | hook 配置与 Claude Code 契约相符 | hook 静默失效——不报错、不中断、无痕迹 |
| 3 | marketplace 条目合规与 `.claude-plugin/` 目录内容 | 条目写歪多数不报错，只是静默退回「跟随分支最新」、整条加载失败，或插件正常加载而组件全部不出现 |
| 4 | `.claude/skills/` 每个 skill 在 `.kiro`/`.agents` 都有符号链接 | Kiro 或 Codex 侧看不到该 skill |
| 5 | 镜像不指向已删除的 skill | 悬空链接 |
| 6 | 镜像以 `120000` 模式入库 | `core.symlinks=false` 时会存成普通文件，克隆到别的机器就不是链接 |

第 1 项由 `check_plugin_versions.py` 实现（18 个单元测试）。

第 2 项由 `check_hook_configs.py` 实现（18 个单元测试），扫 `plugins/*/hooks/hooks.json` 与 `.claude/settings*.json`，查七项机械可判定的错配：`async` 与展示类输出的错配、`async`/`asyncRewake` 用在非 command handler、handler 类型与事件不符、非工具事件上的 `if`、不支持 matcher 的事件上写了 matcher、永不匹配的 `mcp__<server>` matcher、PowerShell 裸占位符，另加拼错的事件名。判据真源是 `knowledge-base/claude-code-hooks/`，每条报错都带对应索引条目 ID。脚本定位不到被引用的脚本文件时不报——宁可漏报也不误报。

第 3 项由 `check_external_entries.py` 实现（85 个单元测试），分两组判据。

**外部引用条目**（`source` 为对象，非本地相对路径）：`sha` 是否 40 位全长、是否误写 `version`、`strict:false` 是否配了非空 `skills` 数组、`source.source` 类型与 `git-subdir` 的 `path`、展示元数据（`description`/`homepage`/`author`）是否齐备，以及是否登记进 `.claude/skills/add-external-skill/registry.md` 的「已接入」表且台账 sha 与条目 sha 一致；另外还会检查拷贝模式落位的 `external_plugins/*/UPSTREAM.md` 是否存在且含 40 位 SHA。这些写歪的形态多数不报错——漏 `sha` 只是静默退回「跟随分支最新」，缺 `skills` 数组则整条加载失败，都是需要借提交关口拦的形态。刻意不联网：条目结构完美但上游仓库已被删除或转私有，这一项抓不到，只能靠实际安装时暴露。

**全部条目与插件目录**（判据真源是 `knowledge-base/claude-code-plugin-system/`，每条报错都带对应索引条目 ID）：marketplace 名是否撞上 17 个 Anthropic 保留名或 Claude Desktop 的三个保留名、marketplace 与条目名是否满足 kebab-case 与 Claude Desktop 托管同步的字符集、本地路径源的 `./` 前缀 / `..` / 反斜杠 / 目标目录存在性、`relevance` 的 `topic` 长度与五种信号的条数与长度上限（含 `hosts` 的裸小写主机名形态与 `manifestDeps` 的 `file` 末尾锚定）、以及 `.claude-plugin/` 目录内除清单外是否混进了组件目录。这一组针对的同样是「不报错」的形态：保留名会在某个版本起让整个 marketplace 停止加载、条目名不合规会被 Claude Desktop 静默删除、拼错的信号名只会静默不匹配、组件放进 `.claude-plugin/` 后插件仍显示为启用而组件一个都调不出来。

```bash
python -m unittest discover -s .githooks -p "test_*.py"
```

## 为什么挂在 hook 而不是 skill 里

这些检查曾写在 `commit-cc-plugin` 的 SKILL.md 中，靠 LLM 逐行读并自觉执行。两个问题：

- **Codex 侧走标准 git 流程，读不到 skill 正文**——门禁在那一侧从来没生效过
- **写在条件小节里的检查执行频率极低**，其自身的缺陷长期得不到反馈（符号链接检查原先漏了排除 gitignore 目录，会误报 `darwin-skill`，因为 GATE 保护极少触发而一直没被发现）

## 不要用 --no-verify

阻断说明仓库一致性真的坏了。报错文本里带了修复命令，按它改；若判定是 hook 自身误报，就修 hook 并补测试。`--no-verify` 只是把问题推给下一个人。
