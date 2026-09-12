# Claude Code Hook 机制规范

> 版本：1.0.0

> 面向 **Claude Code hook 的编写与审查**。收录事件选型判据、配置与作用域语义、输入输出契约、决策控制能力、异步执行边界、安全与成本约束，覆盖官方 [Hooks reference](https://code.claude.com/docs/en/hooks) 记载的 34 个 hook 事件。

本领域只负责 **Claude Code 的 hook 机制**，与两类同名概念严格区分：

| 同名概念 | 归属领域 | 区别 |
|---|---|---|
| Git 的 `pre-commit` / `pre-push` 等 VCS 钩子 | `git`（见 `git.02.commit-hooks`） | 由 git 调用，与 Claude Code 会话无关 |
| Windows API Hook / ShellExecute Hooks（注入手法） | `host-diagnostics` | 进程注入技术，是被诊断的对象而非工具 |

**Codex 侧不适用。** 本仓为双 harness，但 Claude 侧 hooks 在 Codex 中不生效（见仓库 `AGENTS.md`「两个 harness 的必要差异」）。本领域全部条款仅约束 Claude Code。

## 文档目的

让 hook 的编写者在落笔前就能判断：**该选哪个事件、输出会去哪里、什么情况下它根本不会生效**。

hook 的失效模式有一个共同特征——**静默**。路径写错只在 transcript 留一行 notice，exit 1 被当成非阻塞错误放行，`async` 把面向用户的输出改道给模型，`matcher` 写成 `mcp__memory` 则永不匹配。这些都不报错、不中断、不留痕，靠试出来的成本远高于查一条判据。

## 适用范围与读者

- **适用范围**：`~/.claude/settings.json`、项目 `.claude/settings.json`、插件 `hooks/hooks.json`、skill / subagent frontmatter 中定义的全部 hook；本仓 `plugins/*/hooks/` 下的既有 hook 亦适用
- **平台**：全平台，Windows 专有约束在条款内显式标注
- **harness**：仅 Claude Code
- **读者**：编写或审查 hook 的开发者，以及需要判断「某 hook 为什么没生效」的排查者

## 收录判据

**判据进知识库，操作步骤进 skill。**

检验标准：这条内容能独立成为「查一下就照着判断」的依据吗？能 → 本领域。它是否必须知道「上一步做了什么」才有意义？是 → 属 skill，不收。

据此：

- 「`async: true` 的 `systemMessage` 不展示给用户」**收录**——单条可判，且判错的代价是功能静默失效
- 「`matcher: "mcp__memory"` 不含正则字符，按精确串比较，匹配不到任何工具」**收录**——单条可判
- 「怎么一步步调试一个不触发的 hook」**不收录**——是排查流程，依赖上一步结论，属 skill

官方文档中**纯描述性的 input 字段表**（各事件收到哪些 JSON 字段）不逐一抄录：它是查阅型资料而非判断依据，且随版本增删频繁，抄录即制造过期风险。本领域只收录**契约与判据**，字段明细指向官方原文。

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义。

| 级别 | 措辞 | 含义 | 违反处置 |
|---|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，违反会导致 hook 静默失效或产生安全风险 | 视为缺陷，review / 脚本拦截 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 | review 说明理由后可豁免 |
| **建议 MAY** | "可以"、"建议" | 可选做法，不强制 | 无 |

## enforcement 取值说明

| 取值 | 本领域含义 |
|---|---|
| `ci` | 可由 `.githooks/check_hook_configs.py` 机械判定，提交前拦截 |
| `review` | 需人工判断意图（如事件选型是否恰当），脚本无法代劳 |
| `advisory` | 提示性，不构成拦截理由 |

⚠️ 标 `ci` 不等于**已经**被脚本覆盖。当前脚本落地了七项检查：`async` 与展示类输出的错配、`async`/`asyncRewake` 用在非 command handler、handler 类型与事件不符、非工具事件上的 `if`、不支持 matcher 的事件上写了 matcher、永不匹配的 `mcp__<server>` matcher、PowerShell 裸占位符，另加拼错的事件名。其余 `ci` 条目是「原理上可机械判定」，尚未落地脚本。

## 文件地图

| 文件 | 承载什么 | 什么时候读 |
|---|---|---|
| `rules/01-event-selection.md` | 事件选型：三类 cadence、能否拦截、matcher 支持、handler 类型支持 | 决定「用哪个事件」时 |
| `rules/02-configuration.md` | 配置与作用域：定义位置、合并语义、matcher 求值、`if` 边界、exec/shell form、路径占位符 | 写配置 JSON 时 |
| `rules/03-output-contract.md` | 输出契约：exit code 语义、stdout 的 JSON/纯文本判定、字段交付去向与逐事件例外 | 决定「怎么把结果传出去」时 |
| `rules/04-decision-control.md` | 决策控制：各事件的决策模式与字段、改写类能力、硬保证的边界 | 要拦截或改写行为时 |
| `rules/05-async-execution.md` | 异步执行：`async` / `asyncRewake` 的适用判据与输出改道 | 考虑「让 hook 不阻塞」时 |
| `rules/06-security-and-cost.md` | 安全与成本：workspace trust、注入面、Windows 进程成本、PowerShell 占位符 | 审查 hook 安全性与启动开销时 |
| `reference/event-capability-matrix.md` | 34 个事件 × 六个能力维度的完整对照表 | 需要逐事件查证时，作为 rules 的取证出处 |

## 阅读路径

- **第一次写 hook**：`01` 选事件 → `02` 写配置 → `03` 定输出方式
- **要拦截某个行为**：`04` 决策控制 → `03` § exit code 语义 → `01` 确认该事件能否拦截
- **hook 没生效**：`03` § 静默失效清单 → `02` § matcher 求值 → `06` § workspace trust
- **担心启动变慢**：`06` § 进程成本 → `05` 判断能否异步

## 索引与机器消费

条目索引在 `index.jsonl`，检索方式见 `knowledge-base/README.md` § 消费方式。机械可判定的条款落地为 `.githooks/check_hook_configs.py`，挂在 `.githooks/pre-commit` 上提交前拦截；覆盖范围见上文 § enforcement 取值说明。

## 权威参考

- [Hooks reference](https://code.claude.com/docs/en/hooks) —— 本领域全部条款的一手依据
- [Hooks guide](https://code.claude.com/docs/en/hooks-guide) —— 教学与排查向，非规范
- [Settings](https://code.claude.com/docs/en/settings) —— 设置文件优先级
- [Permissions](https://code.claude.com/docs/en/permissions) —— `if` 字段与 workspace trust 的语法出处
