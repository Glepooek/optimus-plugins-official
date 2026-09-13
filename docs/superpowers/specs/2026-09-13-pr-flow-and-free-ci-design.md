# 设计 Spec：主干走 PR + 零成本 CI 门禁

**日期：** 2026-09-13
**状态：** 待评审
**触发：** `docs/todo-list/2026-09-12-todo.md` 的「主干推送方式的规范冲突（待裁决作用域）」

## 1. 背景与目标

### 1.1 要裁决的死结

`knowledge-base/git/` 与 `commit-cc-plugin` 对「怎么把改动合入主干」给出相反答案，三方并存：

- `knowledge-base/git/rules/03-pull-requests.md:24` —— **必须**：主干开启保护、禁止直推、禁止 force push，只能通过 PR 合入；`:25` —— **必须**：至少一名 reviewer 批准且 CI 全绿
- `commit-cc-plugin` 第五步 —— `git push origin master`，即直推主干；而 `AGENTS.md`「提交与推送」规定提交**必须**走这个 skill
- 实际历史 —— `origin/master` 零 PR 合入记录，全部直推

死结在于 `commit-cc-plugin` 自己声明「若本文件与 Git 知识库冲突，以知识库为准」：**一份规范把裁决权让给另一份，而另一份禁止它自己的核心动作。**

### 1.2 裁决结论

采用 todo 的**处置 2**：承认本仓也该走 PR。四项决定：

| # | 决定 | 依据 |
|---|---|---|
| 1 | `03-pull-requests.md:24`（禁止直推、只能 PR）**原样保留并开始遵守** | 该条款本身无缺陷，缺的是执行 |
| 2 | `:25` 的「至少一名 reviewer 批准」**加作用域限定** | GitHub 不允许 PR 作者批准自己的 PR，单人仓库该条款物理上无法满足；「CI 全绿」部分保留且强化 |
| 3 | 日常提交手感为**全自动**：建分支 → 推 → 开 PR → CI 绿 → 自动合并 | 用户拍板 |
| 4 | `01-branching.md:17` 的分支命名条款（`<type>/<简短描述>`）**随之生效** | 走 PR 必然要建分支，该条款不再是空转 |

### 1.3 CI 的目标与成本约束

需求原文是「用 `claude plugin eval` 对新增的 skill 进行检测」，随后追加约束：**若 eval 收费则换方案**。

取证结论：`claude plugin eval` 不是收费功能，但它的工作方式是为每个 case 启动真实 `claude` 子进程跑 agent，**token 消耗是机制内在的，无法归零**。放进 PR 的必需检查等于每个 PR 都付费。

⚠️ **该结论在 § 3.5 完成实测后仍然成立，且有了具体数字：**六种 grader 里四种（`regex`/`tool_order`/`tool_used`/`file_exists`）不计费，但**免费的只是评分那一层**——被评的那次 agent run 照样要跑。实测单价 ≈$0.15/run，默认配置下 ≈$0.90/case，按 § 5.8 收窄到 `--ablation none --runs 1` 后 ≈$0.15/case。**「有免费 grader」不等于「有免费 eval」，这是本次取证最容易搞错的一处。**

因此拆成两层，二者不是替代关系而是**同一传感器的静态层与行为层**：

| 层 | 手段 | 触发 | 成本 | 查什么 |
|---|---|---|---|---|
| 静态闸 | `claude plugin validate --strict` + 既有门禁与单测 | 每个 PR，必需检查 | **零 token** | schema 合法性、仓库一致性 |
| 行为闸 | `claude plugin eval` | `workflow_dispatch` 手动 | ≈$0.15/case（收窄后） | skill 是否真能被正确触发**、以及是否过度触发** |

⚠️ 行为闸那一格的「以及是否过度触发」是 § 3.5.2 才确立的能力（`tool_used` 支持 `max: 0`）。**它把行为闸的价值从「测能不能用」扩到「测会不会乱触发」**——后者在单人日常使用中反而是更常见的困扰。

## 2. 非目标

- **不追溯存量 51 个 skill 的 eval case**。用户已拍板「新增必须带 case，存量不回溯」。⚠️ **但已有的两份 eval 素材不属「存量回溯」**——它们已经入库、已有实质内容，只是格式不被官方识别（§ 3.5.4），把它们迁成官方格式是**修复已有产物**，见 § 5.9。
- **不在 CI 的必需检查里运行任何 eval case**。case 的运行成本是机制内在的（§ 3.5.3），行为闸只留 `workflow_dispatch` 入口。
- **不改 `03-pull-requests.md:26`**（`release/*` 保护的 SHOULD 条款）——本仓无 release 分支，该条款空转但无害。
- **不引入 `gh` CLI**。日常 PR 流程用 GitHub MCP 已有工具即可闭环（见 § 3.2），装 `gh` 只为一次性配置不值得引入新依赖。
- **不改 `.githooks/pre-commit` 的检查内容**。它继续在本地拦截，CI 只是把同一批脚本在另一个环境再跑一次；两者共用脚本、不分叉。

⚠️ **本节曾把「不建 eval 套件本体」列为非目标，该项已被用户明确撤销**（追加指示：「现在建」）。撤销的后果不只是多一个工作项——它把 § 5.7 的目录约定从「待定的占位」变成了必须实测确定的事实（于是暴露出原约定是错的，见 § 3.5.4），也把 § 8.3「版本影响：全部不升」推翻了（evals 落在 `plugins/*/skills/<name>/` 内，命中版本矩阵第一行）。**范围变更会向外传导到看似无关的结论上，这一处记录的就是那条传导链。**

## 3. 取证

本节全部为本机实测，不采信文档或记忆。后续设计的每个选择都指回这里。

### 3.1 `claude plugin validate` 的实测能力与边界

命令签名：`claude plugin validate [--json] [--strict] <path>`，官方描述为「Validate a plugin or marketplace manifest, or the skills, agents, and commands in a directory」。

| # | 实测结论 | 证据 |
|---|---|---|
| 1 | **真的解析 SKILL.md frontmatter** | 阴性对照：临时造一个缺 `description` 的 skill，命中 `description: No description in frontmatter` |
| 2 | `contents: []` 含义是「无发现」，**不是「未扫描」** | 同一命令在有问题的目录上 `contents` 立即填充条目 |
| 3 | **缺 `description` 只判 warning，默认档退出码 0** | 非 strict 时输出 `✔ Validation passed with warnings` 且 `RC=0` |
| 4 | `--strict` 把 warning 升为失败，退出码 1 | 同一阴性对照加 `--strict` 后 `RC=1` |
| 5 | **无凭据可运行、零 token** | 用空 `CLAUDE_CONFIG_DIR` 且清空 `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` 仍 `RC=0`，CLI 自建空配置且不要求登录 |
| 6 | 本仓当前**零存量债务** | 22 个校验目标（marketplace + 10 插件清单 + 9 个 `skills/` + 1 个 `agents/` + `.claude/skills/`）全量 `--strict` 全绿 |
| 7 | 单个 skill 目录**不是**合法目标 | 对 `skills/weekly-report` 报 `No manifest found in directory`，`RC=1`——必须传插件根（校验清单）或 `skills/` 父目录（校验组件） |
| 8 | 覆盖边界：只管官方 schema | `name` 与所在目录名不一致**未被拦**；本仓六字段约定（`metadata.version` 等）也不在其中 |

**四条对设计有决定性影响的结论：**

- **第 3 条 + 第 4 条 ⇒ CI 必须加 `--strict`。** 缺 `description` 的 skill 在 Claude 侧等于永不被自动触发，属功能性失效，却在默认档静默通过。不加 `--strict` 的 CI 是只会亮绿灯的刹车。
- **第 5 条 + 第 6 条 ⇒ 门禁可以在上线第一天就硬失败、且无条件作必需检查。** 零凭据意味着不需要 secret，fork PR 同样跑得通（fork PR 拿不到仓库 secret，任何依赖凭据的检查都会在 fork 场景失败）；零存量债务意味着不必先设「只对改动文件严格」的过渡档（`scope-errors-to-changed` 因此保持 `false`）。
- **第 7 条 ⇒ 校验目标必须分两类给**：插件根（校验清单）与 `skills/` 父目录（校验组件），传单个 skill 目录会直接报错。§ 5.6 采用的官方 composite action 内部已按这个形态调用（00 步定位插件根、40 步校验），**因此本仓不需要自己维护这份目标清单——但 `.claude/skills/` 不属任何插件，落在它的定位逻辑之外，须另加一步**。
- **第 8 条 ⇒ 它不能取代本仓自有门禁。** 官方校验与 `.githooks/` 的三个门禁是互补的两套判据，都要跑。

### 3.2 GitHub MCP 的能力边界

需求原文为「使用 github mcp 对本仓库的主程序设置保护」。**MCP 服务器未提供任何分支保护或 ruleset 工具**，`gh` CLI 本机也未安装（`gh api` 退出 127）。该句字面上不可实现。

但把它拆成一次性与持续性两部分后，缺口只剩一次性开关：

| 事项 | 频次 | MCP 能否承担 | 工具 |
|---|---|---|---|
| 打开「必须 PR」保护开关 | **一次性** | ❌ 无工具 | 需 Web UI 或 `curl` + PAT |
| 建分支 | 每次 | ✅ | `create_branch`（实际用本地 `git push` 更直接，见 § 6） |
| 开 PR | 每次 | ✅ | `create_pull_request` |
| 查 CI 状态 | 每次 | ✅ | `pull_request_read`（`get_status` / `get_check_runs`） |
| 合并 | 每次 | ✅ | `merge_pull_request`（支持 `merge_method: squash`） |

**结论：需求 2 的持续性部分完全由 GitHub MCP 承担，只有一次性开关需人工点一次。** 本 spec § 4 给出逐字段配置规格。

### 3.3 GitHub 账号与计费事实

| 事实 | 影响 |
|---|---|
| 仓库 `Glepooek/optimus-plugins-official` 为 **public** | 分支保护与 ruleset 对公开仓库免费，无需付费计划 |
| 账号类型为 **User**（个人账号，非组织） | 无法配置 team reviewer；CODEOWNERS 的团队语法不可用 |
| 默认分支 `master` | 保护规则的 target 写 `master`，非 `main` |
| PR 作者**不能**批准自己的 PR | § 1.2 决定 2 的直接依据 |
| Copilot review 与 `GITHUB_TOKEN` 发起的 review **不计入** approval | 「找个自动批准者」这条路不存在 |
| fork PR 拿不到仓库 secret | 必需检查必须全部零凭据（§ 3.1 第 5 条已满足） |
| GitHub Actions 对公开仓库免费、无分钟数上限 | CI 本身零成本 |
| **主干已存在一个 active ruleset**（名 `main`、id `23134670`、`2026-09-13T05:02:49Z` 创建） | § 4 从「新建保护」改为「修订现有 ruleset」；两次被现实推翻的经过见 § 4.1 |
| bypass 名单**已清空**（`updated_at` 05:44:26） | 直推 `master` 现被 `GH013` 硬拒绝。此前含当前账号时只回 `Bypassed rule violations`——规则存在但对唯一使用者无效 |
| 本机**零提交签名配置** | `user.signingkey`/`gpg.format`/`commit.gpgsign` 均未设，最近 5 个提交 `git log --format=%G?` 全为 `N` |

### 3.4 官方 marketplace 仓库的 CI 取证

对 `anthropics/claude-plugins-official`（经用户 fork `Glepooek/claude-plugins-official` 读取）的 `.github/` 逐个核查。它有 9 个 workflow，与本次需求相关的是 `validate-plugins.yml`、`validate-frontmatter.yml`，以及被前者引用的 composite action。

**两个仓库均为 public**（实测 `GET /repos/...` 的 `visibility: public`），因此 `uses: anthropics/claude-plugins-community/...` 可直接引用。

#### 3.4.1 🔴 必需检查绝对不能加 `paths:` 过滤器

`validate-plugins.yml` 的 `paths:` 长达 40 行，通篇是补漏历史，注释点名了 PR #5416。机制是：

> `validate` 是 required status check，一个 PR 若未命中 `paths:`，该检查就永远停在 **"Expected — Waiting for status to be reported"**，PR 永久无法合并。

他们为此逐条补了 `plugins/*/.claude-plugin/**`（`*` 不跨 `/`，一级模式匹配不到两级目录）、`.github/workflows/**`、`.github/policy/**`、`.github/bump-tracking.json`、`plugins/*/README.md`、`plugins/*/assets/**`、`plugins/*/.mcp.json`、`plugins/*/hooks/**`。注释还明确记载：**`workflow_dispatch` 的 check run 不关联 PR，所以手动跑一次也救不了**。

**本 spec 的约定：所有必需检查一律不设 `paths:`，每个 PR 全跑。** 代价是几分钟 runner 时间（公开仓库免费无上限），收益是彻底消除这一类死锁。这一条比任何 YAML 结构都重要。

#### 3.4.2 🔴 `claude` CLI 在 hosted runner 上的安装不可靠

action 内 `Install claude CLI` 一步有 40 行自愈逻辑，注释给出根因：

> claude-code 包把运行时作为**平台原生 optional dependency**、由 postinstall 脚本抓取。在 hosted runner 上该抓取会间歇性 stall 或被跳过（`npm --omit=optional`、某些 pnpm 配置），留下「added 1 package」但没有可用的 `claude` 二进制（`native binary not installed`）。

因此**裸 `npm i -g @anthropic-ai/claude-code && claude --version` 会非确定性失败，卡住恰好赶上的那个 PR**。官方的五层处置：`--include=optional` 强制装原生依赖、每个网络步骤加 `timeout -k 10 300`、3 次重试且**重试前删包目录 + 清 cache**（npm 对已在磁盘的 `@latest` 会 no-op 从而跳过 postinstall，否则重试是假重试）、兜底直接 `node install.cjs`、`rm -rf` 前加路径守卫。

**本 spec 的处置：不自己写这套，直接复用官方 composite action（§ 5.6）。** 一份手写的 `npm i -g` + 校验循环看起来更简单、也更好读，但它把一个已知的非确定性失败留在了每个 PR 的必经路径上——**这是本次取证否掉的最大一处「更简单方案」**。

#### 3.4.3 composite action 的能力与边界

`anthropics/claude-plugins-community/.github/actions/validate-plugins`（官方 fork 中锁的是 `426e469f322952061102b286b378c0c9733a0934`，本仓沿用同一 SHA），7 个实质步骤：

| 步骤 | 做什么 | 对本仓 |
|---|---|---|
| 00 detect-changes | 对每个变更文件**向上走目录树找最近含 `.claude-plugin/plugin.json` 的祖先** | ✅ 通用逻辑、不硬编码 `plugins/`，本仓 `plugins/<name>/` 与 `external_plugins/<name>/` 均命中，**无需任何路径配置** |
| 11 invariants I1–I11 | 自定义策略不变量，含 **I5 = `source.sha` 锁定** | ⚠️ 与 `.githooks/check_external_entries.py` 部分重叠，两者都留（见 § 5.6） |
| 20 CLI validate marketplace | `claude plugin validate` 校验 marketplace | ✅ |
| 30 CLI validate external | **clone 外部插件再校验**，`external-timeout-secs` 默认 120 | ✅ **纯增益**：补上 `check_external_entries.py` 自陈的盲区——「刻意不联网，上游仓库被删除或转私有抓不到」 |
| 40 CLI validate local folders | 校验**本 PR 改动的**插件目录 | ⚠️ 增量而非全量；且**抓不到 `.claude/skills/`**（不属任何插件，无 `.claude-plugin/plugin.json`） |
| 41 aux-file JSON parse | 解析插件的附属 JSON | ✅ |
| 90 report | 产出 markdown 报告 | ✅ |

四个要在 `with:` 里写明的输入。三个必须覆盖默认值（`base-ref`、`fail-on-warnings`、`claude-cli-version`）；`scope-errors-to-changed` 的默认值就是我们要的，**写出来是为了让「刻意选了严格档」留痕**——依赖一个不在眼前的默认值来维持严格性，等于把门禁强度交给上游的下一次改动：

| 输入 | 默认值 | 本仓要传 | 原因 |
|---|---|---|---|
| `base-ref` | `…\|\| 'origin/main'` | `${{ github.event.pull_request.base.sha }}` | **默认值里是 `origin/main`，本仓默认分支是 `master`** |
| `fail-on-warnings` | `false` | **`true`** | 等价于 § 3.1 第 3/4 条论证的 `--strict`；不开则缺 `description` 只是 warning |
| `scope-errors-to-changed` | `false` | 保持 `false` | 本仓零存量债务（§ 3.1 第 6 条），可承受全量严格 |
| `claude-cli-version` | **`latest`** | **`2.1.270`** | 见 § 10 风险 1。取 `2.1.270` 而非任意版本，是因为 § 3.1「零存量债务」这条基线正是用本机 `2.1.270` 量出来的——**CI 的判据版本与基线量测版本必须同一个，否则「零债务」这个前提在 CI 里不成立** |

另需 `actions/checkout` 配 `fetch-depth: 0`（diff 需要完整历史）。

#### 3.4.4 ⚠️ 不要照抄官方的 job 命名

`validate-plugins.yml` 与 `validate-frontmatter.yml` 的 job **都叫 `validate`**。两个同名 check run 会让 required status checks 的名字匹配含混——正是 § 10 风险 2 记的那个脆弱点。**本仓每个 job 用唯一且描述性的名字。**

#### 3.4.5 暂不借鉴的部分

| workflow | 为什么不用 |
|---|---|
| `scan-plugins.yml`（27 KB） | 第三方插件安全扫描，本仓插件全部自建或已人工审过，成本收益不成比例 |
| `validate-licenses.yml` | 面向 curated marketplace 的第三方 license 合规；本仓 `external_plugins/` 拷贝模式有一定相关性，**列为未来项** |
| `close-external-prs.yml`、`external-pr-scope-guard.yml` | 官方靠它自动关闭 fork PR。本仓是个人插件仓库，不采用「一律关闭外部 PR」策略，故 fork PR 照跑必需检查（全部零凭据，fork 也能跑通）。**代价见 § 5.7 关于文件名注入的处置** |
| `bump-plugin-shas.yml`、`revert-failed-bumps.yml` | 自动跟随上游升级 `source.sha`。本仓 3 个外部引用条目正是锁 sha 的形态，**高度相关但属新功能**，不在本次三项需求内，列为未来项 |
| `validate-frontmatter.yml` | 它校验的是官方六字段之外的自定义约定，用 bun + TypeScript。本仓的 frontmatter 约定在 `.claude/rules/skill-conventions.md`，与官方不同，直接抄会校验错的规则。**思路借鉴**（见 § 5.7 的 `--diff-filter` 与文件名处理），实现不抄 |

### 3.5 `claude plugin eval` 的实测契约

本节全部实测。**取证手法本身值得记录：让 case 在 load 阶段就非法（`weight` 传字符串），zod 解析即抛错，永远走不到启动 agent 那一步**——因此除下表第 6 条那一次，其余全部零成本。zod 是 strict 模式，会把未识别的键**逐个点名**，于是「批量投递候选键名、看谁被点名」就是一次性枚举整个字段表的办法。

#### 3.5.1 位置与发现规则

| # | 结论 | 证据 |
|---|---|---|
| 1 | 必须在**插件或 skill 文件夹**内运行，或显式传 `--eval-dir` | 在裸目录 `.eval-probe` 跑 `eval init --bare` 报 `is not a plugin or skill folder`；补上最小 `.claude-plugin/plugin.json`（只需 `name`/`version`/`description`）后即被识别为 `Plugin under test` |
| 2 | eval 目录默认 `evals/`，可由 `plugin.json` 的 `experimental.evals` 改 | 官方 help |
| 3 | 🔴 **在插件根运行会递归发现 `skills/*/evals/**`** | 造 `.eval-probe/skills/probe-skill/evals/nested-case/`（故意非法）后在**插件根**运行，报错路径逐字为 `…\skills\probe-skill\evals\nested-case` |
| 4 | 仓库根**不是**合法运行位置 | 本仓根只有 `.claude-plugin/marketplace.json`，无 `plugin.json`，命中第 1 条的报错 |

**第 3 条决定了目录约定与调用方式**（§ 5.7、§ 5.9）：case 放在 skill 自己的目录下，而运行以**插件**为单位，一条命令覆盖该插件全部 skill 的 case；不需要在仓库根维护一份集中的 eval 目录树，也不需要逐 skill 循环。

⚠️ **第 4 条意味着「全量跑」必须按插件循环**，没有一条覆盖全仓的命令。

#### 3.5.2 case 与 grader 的 schema

两种等价写法：`case.yaml`，或 `prompt.md` + `graders/*.md`（frontmatter 承载字段，正文承载 prompt / 判据描述）。官方 `--bare` 模板即后者。

case 顶层 15 个合法键（zod strict，未识别键报错）：`schema_version`、`name`、`description`、`tags`、`plugins`、`runs`、`expected_outcome`、`model`、`max_turns`、`timeout_seconds`、`allowed_tools`、`artifact_publish`、`growthbook_overrides`、`append_system_prompt`、`env`。

⚠️ **`expected_outcome` 不受枚举约束**，任意字符串都能通过校验——它不是可依赖的判据，真正的判据只在 grader 里。

六种 grader，**付费的只有后两种**：

| type | 计费 | 说明 |
|---|---|---|
| `regex` | 免费 | 正则匹配最终输出 |
| `tool_order` | 免费 | 工具调用顺序 |
| `tool_used` | 免费 | 某工具被调用的次数落在 `min..max` 内 |
| `file_exists` | 免费 | 文件产出 |
| `llm` | **付费** | LLM 评委按自然语言判据打分 |
| `baseline` | **付费** | 与基线对比 |

⚠️ **`--bare` 脚手架默认生成的是付费的 `llm`**，照抄模板就等于选了付费档。

`tool_used` 的完整字段（批量投递 16 个候选键探明）：`type`、`tool`、`weight`、`min`、`name`、`max`。被点名拒绝的有 `count`、`min_count`、`max_count`、`times`、`expected`、`negate`、`not`、`at_least`、`at_most`、`description`。

**两条由此得到的关键能力：**

- `tool_used` + `tool: Skill` 是「这个 skill 到底有没有被触发」的**直接传感器**。默认 `min: 1`、`max` 无穷，失败时渲染为 `Skill called 0x (expected 1..∞)`
- **`max: 0` 表达「不得调用」**，因此**负例（不该触发的语境）也能零成本判定**——这一条决定了 § 5.9 里 `jenkins-build` 那 20 条素材可以整体迁移，而不是只能迁一半

#### 3.5.3 成本与外发行为

| # | 事实 | 影响 |
|---|---|---|
| 5 | **一次 agent run ≈ $0.15**（本机实测单价） | 计量单位是 run，不是 case |
| 6 | 🔴 默认 `--runs` = `case.runs ?? 3`，`--ablation` 默认 `with-without`（2 臂）⇒ **6 runs/case ≈ $0.90** | 不显式收窄就是每个 case 近一美元 |
| 7 | 🔴 **`--max-cost-usd` 在每次 run 启动前检查，因此挡不住第一次 run** | **没有零成本的 dry-run**，成本下限是一次 run。第 5、6 条的数据正是这样测出来的——一次 `expected_outcome: bogus_value` 未被 schema 拦下，真启动了一次 run，花了 $0.15 |
| 8 | 🔴 **HTML 报告默认发布到 claude.ai**（`--publish-report` 的说明是「already the default when your account supports it」） | `--no-publish` 对本仓是**强制项**；case 级另有 `artifact_publish` 键，同样须保持关闭 |
| 9 | `--trust-plugin` 用于跳过首次运行的信任提示 | 非交互环境必需 |
| 10 | `--scaffold` 会执行 case 作者提供的 bash；`--allow-real-servers` 会在 OS 沙箱外启动真实 MCP 服务器 | 两者默认关闭，**保持关闭**；开启前须逐个 case 审过 |
| 11 | `--judge-model` 默认 haiku，`--threshold` 默认 1.0 | 只影响付费 grader |

⚠️ **grader 免费 ≠ eval 免费。** 免费只省掉评分那一层，被评的那次 agent run 照样要跑、照样计费。§ 1.3 的结论「token 消耗是机制内在的，无法归零」因此仍然成立，**这也是 `skill-eval` 不进必需检查的成本依据（§ 4.2 其四）**。

#### 3.5.4 本仓已有的两份 eval 素材：位置对，格式不对

⚠️ 本 spec 早期表述过「本仓没有任何 eval 套件」，**该表述不准确**。实际有两份已入库、有实质内容的文件，但都是**自定义格式**，`claude plugin eval` 在它们上面找到 0 个 case：

| 文件 | 格式 | 内容 | 可迁移性 |
|---|---|---|---|
| `plugins/optimus-devops-plugin/skills/jenkins-build/evals/trigger-eval.json` | 20 元素数组，每项 `{"query": …, "should_trigger": true\|false}`，10 正 10 负 | 触发判定语料 | ✅ **`should_trigger` 与 `tool_used` 同构**：`true` → `min: 1`；`false` → `max: 0`。迁移是机械的，不需要重新设计 prompt |
| `plugins/optimus-frontend-plugin/skills/wpf-code-review/evals/evals.json` | `{"skill_name", "evals": [{"id", "prompt", "expected_output", "files"}]}`，6 条 WPF 性能/泄漏场景 | 输出质量语料 | ⚠️ `expected_output` 是自然语言描述，**只能由付费 `llm` grader 判定**。见 § 5.9 的处置 |

**两份文件的目录位置（`plugins/*/skills/*/evals/`）恰好就是官方递归发现的形态**（3.5.1 第 3 条），因此迁移只需换内容、不需搬家。这同时推翻了本 spec 原先设计的仓库根 `evals/<plugin>/<skill>/`（原 § 5.7）。

## 4. 主干保护配置（ruleset 已修订完毕，本节转为记录与善后）

### 4.1 取证过程：从「以为要新建」到「已改完并锁死」

这一节被现实推翻过两次，两次都值得记录，因为两次的失效形态都不报错。

**第一次推翻——它已经存在。** 本节原始设计是「从零新建保护」。取证方式是一次常规的 `git push origin master`：它**成功了**，但服务端回了

```
remote: Bypassed rule violations for refs/heads/master:
remote: - Changes must be made through a pull request.
remote: - Commits must have verified signatures.
remote:   Found 1 violation: efeb3b49...
```

`Bypassed` 不是错误而是通告：规则命中了，因当前账号在 bypass 名单内而放行。**没有这一行，这个 ruleset 会长期给人「主干已受保护」的错觉，而实际上唯一会推它的人恰好豁免——保护的有效范围与实际使用者的交集是空集。**

**第二次推翻——它已经改完了，而且顺序反了。** 用户在本会话期间按 § 4.2 / § 4.3 把六项改动全部执行，**包括 § 4.5 明确要求放到最后的「清空 bypass 名单」**。下一次 `git push origin master` 就换成了硬拒绝：

```
remote: error: GH013: Repository rule violations found for refs/heads/master.
remote: - Changes must be made through a pull request.
remote: - 6 of 6 required status checks are expected.
```

⚠️ **这一次的输出恰好是验收第 6 项要的阴性对照**：直推必须**真的被拒绝**，而不是回一行提示。该项由此达成，证据即上面这段 `GH013`。

但第二行暴露了一个双向死锁：`required_status_checks` 先于 CI workflow 被配置，6 个 job 在 GitHub 上一个都不存在，于是**每个 PR 的 6 项检查全部永久停在 "Expected — Waiting for status to be reported"**——主干既不能直推、也不能通过 PR 合并。这与 § 3.4.1 记录的官方那个死锁是同一形态，只是成因从「`paths:` 未命中」换成了「workflow 不存在」。

现有配置（读自 `GET /repos/{owner}/{repo}/rulesets/23134670`，公开仓库无需认证，`updated_at` 05:44:26）与本 spec 规格的逐项对照：

| 规则 | 原始状态 | 目标 | 现状 |
|---|---|---|---|
| `conditions.ref_name.include` | `~DEFAULT_BRANCH` | 不变 | ⚠️ 现为 `~DEFAULT_BRANCH` + `refs/heads/main` + `refs/heads/master`。本仓无 `main` 分支，该条空转无害，但会让人以为有——可选清理项 |
| `deletion` | 有 | 保留 | ✓ |
| `non_fast_forward` | 有 | 保留 | ✓ 即「禁 force push」 |
| `pull_request` | 有 | 保留 | ✓ 本次裁决的核心 |
| └ `required_approving_review_count` | 1 | 0 | ✅ 已改 0 |
| └ `require_extra_approval_for_unattributed_changes` | true | false | ✅ 已改 false |
| └ `allowed_merge_methods` | `merge`/`squash`/`rebase` | 仅 `squash` | ✅ 已收窄 |
| `required_signatures` | 有 | 删除 | ✅ 已删（`updated_at` 05:09:52） |
| `copilot_code_review` | `review_on_push` | 保留 | ✓ 现另加 `review_draft_pull_requests: true`，无害。**它不阻塞合并**——不计入 approval，既帮不上批准数也拦不住合并 |
| `required_linear_history` | 缺 | 新增 | ✅ 已新增 |
| `required_status_checks` | 缺 | 5 项 | 🔴 **配成了 6 项，且早于 CI 存在**——多出的 `skill-eval` 见 § 4.2 其四；整条规则须先移除，见 § 4.5 |
| └ `strict_required_status_checks_policy` | — | spec 未设计 | ⚠️ 现为 `true`（= 合并前分支必须最新）。单人串行提交撞不上，但给 § 6.3 的「轮询 + 显式 merge」多一个失败模式：master 在轮询期间前进则 merge 被拒 |
| bypass 名单 | 含当前账号 | 清空 | ✅ 已清空（`bypass_actors: null`） |

### 4.2 四项冲突：前三项已解决，第四项是新出现的

**其一：合并条件当前不可满足（已解决）。** `required_approving_review_count: 1` 叠加四个事实——GitHub 不允许 PR 作者批准自己的 PR、个人账号无 team reviewer、Copilot review 不计入 approval、`require_extra_approval_for_unattributed_changes: true` 还要再加一票。单人仓库里这组条件凑不出所需批准数。**一旦移出 bypass 名单，主干将既不能直推、也不能通过 PR 合并**——这不是配置得严，而是配置得不可满足。

处置：`required_approving_review_count` 改 **0**，`require_extra_approval_for_unattributed_changes` 改 **false**，两项均已执行。规范侧的对应改动是 § 7.1 给 `03-pull-requests.md:25` 加作用域限定——⚠️ **配置侧已先行落地，规范侧尚未改，此刻正处在「配置与规范互相矛盾」的中间态**，§ 7.1 必须补上，否则就是把旧死结换了个方向。

**其二：bypass 名单必须清空（已执行）。** 名单里有唯一使用者时，保护的实际作用范围为空。清空后的逃生口改为「把 Enforcement status 临时改为 `Disabled`」——一次显式、留痕、需刻意为之的操作，而不是每次推送时静默绕过。这才满足 `03-pull-requests.md:24` 的「禁止直接推送」：直推必须**真的被拒绝**（证据见 § 4.1 的 `GH013`）。

**其三：缺 `required_status_checks` 意味着需求 3 落不了地（已配置，但配早了）。** 没有这一项，CI 可以红着而 PR 照样能合，§ 5 设计的五个零 token 检查必须挂进这里才有约束力。该项已配置——**但在 CI workflow 存在之前配置它，制造了 § 4.1 记的双向死锁**。这不是配置内容错，是配置**时机**错，处置见 § 4.5。

**其四（新出现）：`skill-eval` 不该在必需检查里。** 实际配置的 6 项里含 `skill-eval`，而 § 5.1 那张表把它明确标为 **❌ 不是必需检查**。两个独立的理由，各自都是充分的：

| 理由 | 后果 |
|---|---|
| 它只有 `workflow_dispatch` 触发 | 永远不会在 PR 上产生 check run，**这一项自身就是永久 Expected**——与 § 3.4.1 官方注释记的「`workflow_dispatch` 的 check run 不关联 PR」是同一条机制 |
| 它是唯一**收费**的 job（每个 case 起真实 `claude` 子进程） | 进必需检查等于每个 PR 都付费，直接违背 § 1.3 那条「若 eval 收费则换方案」的用户约束 |

处置：删掉该 context，必需检查最终为 5 项，与 § 5.1 逐字一致。

⚠️ **这个偏差的来源值得记一笔：** § 5.1 的表里六个 job 同列，「是否必需检查」是其中一列。照表配置时整列被一并勾上是很自然的读法——**把「不要做的事」和「要做的事」放进同一张表的同一列，就要承担被连带执行的风险**。表本身不改（六个 job 的成本对比正需要并列），但 § 5.1 正文已加了独立一句强调 `skill-eval` 不进必需检查。

### 4.3 `required_signatures`：删除（用户裁决）

本机零签名配置（`user.signingkey`/`gpg.format`/`commit.gpgsign` 均未设，最近 5 个提交 `%G?` 全为 `N`）。移出 bypass 名单后，未签名提交会被服务端拒绝——**连特性分支的推送都会被拒**，因为该规则作用于向受保护分支推送的 commit 及其合并。

两条路各自的代价已提交用户裁决，**结论：从 ruleset 删除 `required_signatures`**。放弃这条安全边界，换取零配置成本。**该项已执行完毕**（`updated_at` 05:09:52 起该规则不再存在），是本 spec 中唯一已落地的改动。

⚠️ 该裁决同时意味着 spec 不引入任何签名相关约定；若日后要恢复该规则，需先完成 SSH signing 配置（`gpg.format=ssh` + `user.signingkey` + `commit.gpgsign=true` + 在 GitHub 账号加 Signing Key），再改 ruleset，顺序不能颠倒。

### 4.4 修订手段

GitHub MCP 无 ruleset 工具（§ 3.2），`gh` 未安装。两条路：

| 手段 | 说明 |
|---|---|
| **Web UI**（实际采用） | 仓库 → Settings → Rules → Rulesets → `main` → 按 § 4.1 现状列逐项核对 |
| `curl` + PAT | `PATCH /repos/{owner}/{repo}/rulesets/23134670`，需 PAT 具备仓库 admin 权限 |

⚠️ **读取不需要认证，写入需要。** 本 spec 全部现状取证都走匿名 `GET /repos/{owner}/{repo}/rulesets/23134670`（公开仓库），因此「配置到底是什么」这个问题在任何时候都能零成本核实——**不要凭 UI 记忆或本节文字判断当前状态，直接读 API**。本节两次被推翻都是靠这条。

建议顺带把 ruleset 改名为 `master-protection`——现名 `main` 会让人以为它作用于 `main` 分支，而本仓不存在该分支（实际 target 是 `~DEFAULT_BRANCH` 即 `master`）。这是可选的清理项，不影响功能。

### 4.5 ⚠️ 实施顺序：原定顺序已被推翻，记录事故与实际解锁路径

**原定的硬约束是「bypass 名单最后清空」**，理由是 `commit-cc-plugin` 第五步当前正是直推 master，先清空会让下一次提交卡死在一个还没改好的 skill 上。原定顺序：

1. CI workflow 落地
2. 开一个真实 PR 触发 CI —— **必需检查项必须先在 GitHub 上跑过至少一次，名字才会出现在 ruleset 的可选列表里**
3. 改 `commit-cc-plugin` 与 `AGENTS.md`
4. 改知识库条款（§ 7.1 / § 7.2，走 `knowledge-base-maintain`）
5. 修订 ruleset
6. **最后**清空 bypass 名单

**实际发生的是：第 5、6 步先做了，第 1–4 步一步没做。** 后果精确地就是原定约束要防的那件事，且比预想更重——不只是 `commit-cc-plugin` 卡住，而是 § 4.1 记的双向死锁：直推被拒，PR 也因 6 项检查永久 Expected 而合不了。

⚠️ **值得记住的不是「顺序写得不够醒目」，而是这一类约束的性质：** 第 2 步与第 5 步之间的依赖（没跑过的 job 名在 UI 列表里选不上）会**倒逼**人手打 job 名，而手打就绕过了「先跑一次」这道天然校验——`skill-eval` 混进必需检查正是这条路径的产物。**顺序约束一旦被绕过，它原本顺带提供的校验也一起消失了。**

#### 实际解锁路径（用户已拍板）

不走 Enforcement `Disabled`，而是**只移除整条 `required_status_checks` 规则**，其余保护一项不动。理由：

| | Disabled 逃生口 | 只删 `required_status_checks`（采用） |
|---|---|---|
| 「禁止直推」是否仍生效 | ❌ 全部保护失效 | ✅ 始终生效 |
| spec 与 CI workflow 怎么合进 master | 直推 | **走第一个真实 PR** |
| 第一次 PR 流程演练 | 被跳过 | 就是它本身，顺带实测 § 6.3 的 MCP 工具链 |
| 与现实是否一致 | — | ✅ CI 还不存在，不声明它才是诚实的配置 |

顺序：

1. 移除 `required_status_checks` 整条规则（含 `skill-eval`，一次处理完 § 4.2 其四）
2. 走 PR 把本 spec 合进 master —— **第一次真实 PR，同时是 § 6.3 工具链的实测**
3. 写 plan，然后落地 CI workflow（同样走 PR）
4. 该 PR 跑完后，5 个 job 名进入 UI 可选列表
5. 按列表**勾选**加回 `required_status_checks`（5 项）——不手打，避免重演 § 4.2 其四
6. 改 `commit-cc-plugin`、`AGENTS.md`、知识库条款（§ 7.1 / § 7.2）

⚠️ 第 6 步排在最后不再有风险了：主干已经锁上，`commit-cc-plugin` 的直推第五步从现在起本就不可用，改它是补齐而非解锁。**但这意味着第 2、3 步的 PR 要手工走一遍 § 6.3 的动作**——skill 还没改，流程得由本次会话手动执行。这也正好是第一次演练。


## 5. CI 设计

### 5.1 总体：五个零 token 的必需检查 + 一个手动的行为检查

新建 `.github/`（当前仓库**无此目录**，从零建立）：

| 文件 | job | 触发 | 成本 | 是否必需检查 |
|---|---|---|---|---|
| `.github/workflows/ci.yml` | `gates-hooks` | `pull_request` → `master` | 零 | ✅ |
| 同上 | `gates-tests` | 同上 | 零 | ✅ |
| 同上 | `gates-data` | 同上 | 零 | ✅ |
| 同上 | `plugin-validate` | 同上 | 零 | ✅ |
| 同上 | `new-skill-eval-case` | 同上 | 零 | ✅ |
| `.github/workflows/skill-eval.yml` | `skill-eval` | **仅 `workflow_dispatch`** | 按 case 计费 | ❌ |

**五个必需检查而非一个聚合 job**，五个 job 并行、失败时一眼看出坏在哪类。代价是每个 job 各自 checkout + setup-python（约 10–15 秒 ×5），公开仓库 Actions 免费无上限，可接受。

⚠️ 五个 job 名同时被 `ci.yml` 与 GitHub 服务端的 ruleset 引用，**后者不在版本库里、改动不留 diff**。改名必须同步改 ruleset，否则那项检查静默不再被要求（§ 10 风险 2）。

🔴 **`skill-eval` 绝对不进必需检查列表。** 上表最后一行的「❌」是硬约束，不是建议：它只有 `workflow_dispatch` 触发，进了必需检查就是一项永久 Expected，会把主干锁死；它也是唯一收费的 job。**这件事已经真实发生过一次**，经过与代价见 § 4.2 其四。

### 5.2 三条适用于全部 job 的约定

**其一：一律不设 `paths:` 过滤器。** 判据见 § 3.4.1——必需检查加 `paths:` 会让未命中的 PR 永久停在 "Expected — Waiting for status to be reported"，且 `workflow_dispatch` 救不了。官方为此打了至少 5 次补丁。

**其二：`permissions: contents: read`。** 最小权限，与官方一致。`new-skill-eval-case` 若改用 `gh pr diff` 需额外 `pull-requests: read`，但本 spec 用 `git diff` 避开（见 § 5.7）。

**其三：第三方 action 一律 SHA-pin。** 官方对 `oven-sh/setup-bun` 与自家 composite action 都是 SHA-pin。`actions/*` 官方 action 用 major tag 即可。

不跳过 fork PR。官方用 `if: github.event.pull_request.head.repo.full_name == github.repository` 跳过，但那是因为它有 `close-external-prs.yml` 自动关闭 fork PR；本仓不采用该策略，若跳过则 fork PR 的必需检查永久 Expected、无法合并。五个检查全部零凭据（§ 3.1 第 5 条），fork 场景照样跑通。

### 5.3 job `gates-hooks` —— 逐字执行 `.githooks/pre-commit`，不复制逻辑

**关键取证：`.githooks/pre-commit` 全程未使用 `git diff --cached`**，它的六项检查全部基于工作树与 `git ls-files`，与暂存区无关。因此 CI 可以直接 `sh .githooks/pre-commit`，而不是在 workflow YAML 里重写一份门禁逻辑。

这一步同时补上了一个长期缺口：`pre-commit` 靠 `git config core.hooksPath .githooks` **本机启用、不随仓库分发**，因此它在任何未做该配置的环境中从未生效过。搬进 CI 后，这批门禁第一次有了不依赖本机配置的执行点。

⚠️ **由此产生一条新约定，必须写进 `.githooks/README.md`**：`pre-commit` 不得引入依赖暂存区的检查（`git diff --cached`、`git diff --name-only --staged` 等）。一旦引入，CI 的逐字复用即失效，门禁判据会在两个环境间分叉。

步骤：checkout → `actions/setup-python@v6`（`python-version: '3.x'`，提供 `python` 别名，ubuntu 默认只有 `python3`）→ `sh .githooks/pre-commit`。

### 5.4 job `gates-tests` —— 9 个测试目录必须逐个调用

`unittest discover` **不跨目录递归**（`AGENTS.md`「本地测试」已记载该事实），因此不能用一条命令覆盖全部。九个目录：

```
.githooks
.claude/skills/knowledge-base-maintain/scripts
.claude/skills/sync-cc-docs-to-youdaonote/scripts
.claude/skills/sync-cc-tips/scripts
plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts
plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/scripts
plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/scripts
plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts
plugins/optimus-mcp-servers/scripts
```

实现上用一个 shell 循环遍历该列表，任一失败即整 job 失败。**不把目录列表硬编码成九个 step**——那样新增测试目录时容易漏改，且失败时要翻九个折叠块。

### 5.5 job `gates-data` —— 数据文件一致性

| 检查 | 当前基线（实测） |
|---|---|
| `python .claude/skills/knowledge-base-maintain/scripts/check_index.py` | 790 条记录无问题 |
| `python .claude/skills/knowledge-base-maintain/scripts/check_refs.py` | 284 个消费者文件章节号引用全部有效 |
| `python .claude/skills/sync-cc-tips/scripts/validate_tips.py` | 250 条、九项检查全通过 |

**均无存量债务，可直接设为硬失败。**

### 5.6 job `plugin-validate` —— 复用官方 composite action

**不自己写 `npm i -g` + 校验循环。** 判据见 § 3.4.2：裸安装会非确定性失败并卡住 PR，官方 action 内已有 40 行自愈逻辑（强制 optional 依赖、每步超时、真重试、postinstall 兜底）。

```
- uses: actions/checkout@v5
  with:
    fetch-depth: 0          # detect-changes 需要完整历史
- uses: anthropics/claude-plugins-community/.github/actions/validate-plugins@426e469f322952061102b286b378c0c9733a0934
  with:
    marketplace-path: .claude-plugin/marketplace.json
    base-ref: ${{ github.event.pull_request.base.sha }}   # 默认值是 origin/main，本仓 master
    fail-on-warnings: "true"                              # 等价于 --strict
    scope-errors-to-changed: "false"                      # 本仓零债务，可全量严格
    claude-cli-version: "2.1.270"                         # 默认 latest 会漂移，见 § 10 风险 1
```

四个输入的取值理由见 § 3.4.3 的表。`warn-invariants` 暂不设——先跑一次看 I1–I11 在本仓的实际命中情况，再决定要不要降级某几项；**在没有实测前不预先豁免任何不变量**。

**补一步覆盖 action 的盲区。** action 按「含 `.claude-plugin/plugin.json` 的祖先目录」定位插件，因此 `.claude/skills/`（本仓自用维护型 skill，不属任何插件）完全不在其扫描范围内。在 action 之后追加一步：

```
- run: claude plugin validate .claude/skills --strict
```

`claude` 已由 action 装到 runner 全局，同 job 后续 step 可直接调用，无需重装。

⚠️ **与 `.githooks/check_external_entries.py` 的重叠是刻意保留的。** action 的 I5 查 `source.sha` 锁定，自家脚本也查——但两者不可互相取代：自家脚本额外校验 `add-external-skill` 台账与条目 sha 是否一致（官方没有这个概念），且必须能在 `pre-commit` 里本地跑；官方 action 则会 clone 上游、抓到「仓库已删除或转私有」这个自家脚本明确声明抓不到的形态。**互补，都留。**

### 5.7 job `new-skill-eval-case` —— 需求 3 的零成本落地

这是**「新增 skill 必须带 eval case」与「不为 CI 付费」两个约束的交点**：强制 case **存在**（纯静态 diff 检查，零成本），但不在 CI 里**运行** case（避免 token）。

逻辑：

1. `git diff --name-only --diff-filter=A <base-sha>...HEAD` 取本 PR **新增**的文件
2. 从中筛出形如 `plugins/<plugin>/skills/<skill>/SKILL.md` 的路径
3. 对每个命中项，要求**同目录下** `evals/` 存在、且其下至少有一个子目录含 `case.yaml` 或 `prompt.md`
4. 无命中项 → 直接通过（**存量不回溯**，用户已拍板）

⚠️ **第 3 步的路径是 `plugins/<plugin>/skills/<skill>/evals/<case>/`，不是仓库根的 `evals/<plugin>/<skill>/`。** 本 spec 原先设计的是后者，实测推翻：官方在插件根运行时会递归发现 `skills/*/evals/**`（§ 3.5.1 第 3 条），因此 case 属于 skill 自己的目录。**这个更正的价值不只是少写一层路径**——它让「找到 SKILL.md 就知道去哪找它的 case」成为纯字符串推导（`dirname(SKILL.md) + "/evals"`），门禁脚本不需要维护任何 plugin↔skill 的映射；而原设计要从 `plugins/<plugin>/skills/<skill>/SKILL.md` 反解出两段名字再去另一棵目录树拼路径，多一次可能对不上的转换。

`--diff-filter=A` 是这里的要点：只看**新增**的 SKILL.md，修改已有 skill 不触发。这正是「新增必须带 case，存量不回溯」的机械表达。官方 `validate-frontmatter.yml` 用 `--diff-filter=AMRC`（排除删除），因为它要校验改动过的文件；本 job 的语义不同，只要 `A`。

**⚠️ 文件名必须在 Python 里处理，不能进 shell。** 官方 `validate-frontmatter.yml` 的注释记载了这个考虑——它跳过 fork PR 的理由之一就是「防止来自 fork 的不可信文件名进入下游 shell 步骤」。本 spec 不跳过 fork（§ 5.2），因此该风险必须在实现层消除：`.githooks/check_new_skill_eval_case.py` 用 `subprocess` 取 diff、在 Python 内解析路径，**不经 `xargs`、不做 shell 插值**。

⚠️ 该 job 只查 case **存在**，不查内容是否有意义——一个 `prompt.md` 写着 `TODO` 也能过。这是刻意的边界：内容质量属人工评审，机械门禁只保证「没有悄悄漏掉」。**本次交付会同时建出第一批真 case**（§ 5.9），因此该 job 上线即有活体样本可参照，不再是「等下一次新增 skill 才第一次生效」的空转状态。

### 5.8 workflow `skill-eval.yml` —— 手动的行为闸

- 触发：**仅 `workflow_dispatch`**，输入 `plugin`（插件名，**必填**）
- 需要 `ANTHROPIC_API_KEY` secret
- 不进必需检查列表，不在 PR 上自动运行（🔴 硬约束，见 § 5.1 与 § 4.2 其四）
- CLI 安装复用官方 action 的自愈逻辑（§ 3.4.2），不自己写 `npm i -g`

**`plugin` 必填而非「留空跑全部」**：仓库根不是合法运行位置（§ 3.5.1 第 4 条），「全部」必须实现为按插件循环，而循环会把一次误触的成本乘以插件数。**必填一个插件名，是把成本上界写进接口本身**——比在文档里叮嘱「小心别跑全量」可靠。

命令形态（六个开关全部是有据可依的，不是保守起见）：

```
claude plugin eval "plugins/${{ inputs.plugin }}" \
  --trust-plugin \
  --no-publish \
  --ablation none \
  --runs 1 \
  --max-cost-usd 5
```

| 开关 | 取值 | 判据 |
|---|---|---|
| `--trust-plugin` | 恒开 | 非交互环境必需，否则卡在首次信任提示（§ 3.5.3 第 9 条） |
| `--no-publish` | **恒开** | 🔴 报告默认发布到 claude.ai（§ 3.5.3 第 8 条）。本仓 case 里含内部 Jenkins job 名等信息，**发布是外发行为，必须显式关闭** |
| `--ablation none` | 恒设 | 默认 `with-without` 是 2 臂，成本翻倍。消融对比在「插件装了 vs 没装」的效果研究里有意义，而本仓的问题是「这个 skill 触发得对不对」，单臂足够 |
| `--runs 1` | 恒设 | 默认 3；本仓 case 的判据全是 `tool_used` 这类确定性布尔判定，重复 3 次不增加信息量。⚠️ 若日后引入 `llm` grader，那类判据有抖动，**届时该调回 ≥3** |
| `--max-cost-usd 5` | 上限 | ⚠️ **它挡不住第一次 run**（§ 3.5.3 第 7 条），只是失控时的刹车，不是准入检查 |

不设 `--scaffold`、不设 `--allow-real-servers`（§ 3.5.3 第 10 条）：前者会执行 case 作者提供的 bash，后者会在 OS 沙箱外启动真实 MCP 服务器。本仓 case 都不需要，**保持关闭**。

⚠️ **`--ablation none --runs 1` 把单价从 ≈$0.90/case 压到 ≈$0.15/case（约 1/6）**，这是 § 5.9 的迁移规模能成立的前提。

保留它的理由：`validate` 查的是 schema 合法性，**查不了行为**——一个 frontmatter 完全合法的 skill 完全可能因 `description` 写得含糊而永不被触发。只有 eval 能发现这件事。把它做成手动入口，是在「这件事只有 eval 查得出」与「每个 PR 都付费不可接受」之间取的位置。

### 5.9 eval 套件本体：迁移两份已有素材

用户已明确要求本次就把套件建出来。范围**不是** 51 个 skill，而是把 § 3.5.4 那两份已入库素材迁成官方格式——它们已有实质内容，缺的只是官方包装。

#### 5.9.1 目录与文件形态

```
plugins/<plugin>/skills/<skill>/evals/
  <case-name>/
    prompt.md          # frontmatter: name/description/max_turns/allowed_tools；正文是用户提问
    graders/
      triggered.md     # frontmatter: type/tool/min/max/weight
```

采用 `prompt.md + graders/*.md` 而非单文件 `case.yaml`：**判据与提问分成两个文件，是为了让「改提问」与「改判据」变成两次互不牵连的改动**——本仓这批 case 的提问措辞会随 skill 的 `description` 调整而反复微调，而判据（该不该触发）一旦定下就不动。

#### 5.9.2 `jenkins-build`：20 条整体迁移

原素材 `{"query": …, "should_trigger": true|false}` 与 `tool_used` 逐字同构：

| `should_trigger` | grader |
|---|---|
| `true` | `type: tool_used` / `tool: Skill` / `min: 1` |
| `false` | `type: tool_used` / `tool: Skill` / `max: 0` |

**负例（`max: 0`）是这批素材真正的价值所在。** 只测正例只能证明 skill 能被触发，测不出**过度触发**——`jenkins-build` 的 10 条负例全是「提到 Jenkins 但不该跑构建」的语境（如「帮我写一个 Jenkinsfile，把编译和测试分两个 stage」），这类误触发在真实使用中比不触发更烦人，而且**只有负例查得出**。§ 3.5.2 探明 `max: 0` 可用，是这 10 条能迁的唯一原因。

成本：20 case × 1 run × $0.15 ≈ **$3**（按 § 5.8 的 `--ablation none --runs 1`；不收窄则 ≈$18）。

⚠️ **原文件 `trigger-eval.json` 迁移后删除**，不保留两份。理由：它是自定义格式、无任何工具消费，留着就是第二份真源，而两份判据迟早分叉。迁移时必须逐条核对 20 条 query 全部落地，**不能只迁一部分就删原文件**。

#### 5.9.3 `wpf-code-review`：本次不迁，记明原因

6 条素材的 `expected_output` 是自然语言描述的期望产出（「应指出虚拟化被关闭」之类），**四种免费 grader 都判不了**：`regex` 匹配不了语义、`tool_used` 与产出质量无关、`file_exists` 无文件产出、`tool_order` 不适用。唯一能判的是付费 `llm` grader。

处置：**本次不迁，原文件原样保留**，在 § 10 风险里记为未来项。理由不是省钱（6 条也就 ≈$0.90），而是 `llm` grader 有两个尚未取证的问题：判据措辞怎么写才稳定、`--threshold` 默认 1.0 对自然语言判据是否过严。**在没测过之前迁过去，等于把一批判据不可靠的 case 塞进套件，之后每次跑都要人工分辨「是 skill 退化了还是评委抖动」。**

⚠️ 这是刻意的不对称：`jenkins-build` 迁是因为判据确定、迁移机械；`wpf-code-review` 不迁是因为判据本身需要先做实验。**同一批「已有素材」按可判定性分了两类处理，不按文件数平均用力。**

## 6. `commit-cc-plugin` 的改造

### 6.1 建分支必须发生在提交之前

当前流程在 `master` 上提交、然后直推。走 PR 后若沿用「先提交再想办法」，提交已经落在本地 `master` 上，需要一次额外的搬运。

⚠️ **本节原先的论据是「搬运就得动 `git reset --hard`，把破坏性命令放进日常提交路径不可接受」。该论据已被实测推翻**——本会话手工走完第一个 PR 时验证了无损搬运：

```bash
git switch -c <type>/<描述>          # 新分支从当前 HEAD 拉出，已有 commit 自然归它
git branch -f master origin/master   # master 未被 checkout，-f 只改指针
```

关键在**第二条命令作用于一个未被 checkout 的分支**，因此只移动引用、不触碰工作树，也就不需要 `--hard`。`reset --hard` 之所以危险是它会同时重置工作树；分支指针的移动本身是无损的。

**结论不变，理由换了。** 建分支仍然排在提交之前，但现在的理由是「少一步、少一个可能记错的命令」，而不是「否则必须用破坏性命令」。⚠️ 这个区别有实际后果：既然搬运是安全的，**会话中途才发现忘了建分支时不必推翻重来**，按上面两条命令补救即可——这条补救路径要写进 SKILL.md 的常见错误表。

改动落点：

| 步骤 | 现状 | 改造后 |
|---|---|---|
| 第一步 状态检查 | 不变 | 增加「当前在哪个分支」的判定，见 § 6.2 |
| 第二步 暂存与原子性 | 不变 | 不变 |
| 第三步 unpushed 检测 + amend | 相对 `origin/master` 检测 | 相对**当前分支的上游**检测；§A amend 逻辑保留 |
| **第四步之前（新增）** | — | 若在 `master` 上 → `git switch -c <type>/<简短描述>` |
| 第四步 提交 | 不变 | 不变（`pre-commit` 照常在本地拦截） |
| 第五步 同步推送 | `git push origin master` | 整节重写为 PR 流程，见 § 6.3 |

### 6.2 分支名与「流程中断后接续」

分支名按 `knowledge-base/git/rules/01-branching.md:17` 的 `<type>/<简短描述>`，**`type` 与本次 commit 的 Conventional Commits type 逐字对齐**（该条款括号内枚举与 Conventional Commits 不一致，裁决见 § 7.2）。示例：`fix/hook-configs-settings-json`、`feat/pr-flow-ci`。

第一步的分支判定分两支：

| 当前分支 | 处置 |
|---|---|
| `master` | 正常新建特性分支 |
| 已在特性分支上 | **说明上一轮流程未走完**（如 CI 未过、或会话中断在轮询阶段）。沿用该分支；用 MCP `list_pull_requests`（按 `head` 过滤）查是否已有开着的 PR——有则本次提交推上去后**追加进同一个 PR**，不新建 |

这一支不是防御性设计，而是 § 6.4 已知取舍的必要配套。

### 6.3 第五步新流程

六个动作，前两个用 git，中间三个用 GitHub MCP，最后回到 git：

| # | 动作 | 手段 | 说明 |
|---|---|---|---|
| 1 | 推特性分支 | `git push -u origin <branch>` | ruleset 只作用于 `master`，特性分支可自由推。**不用 MCP 的 `push_files`**——那是通过 API 造新 commit，会与本地已有的 commit 分叉 |
| 2 | 开 PR | MCP `create_pull_request` | `base: master`、`head: <branch>`；title 取 commit 摘要行，body 取 commit 正文 + 归属尾注 |
| 3 | 等 CI | MCP `pull_request_read`（`method: get_check_runs`） | 轮询至五个必需检查全部结束 |
| 4 | 合并 | MCP `merge_pull_request`（`merge_method: "squash"`） | 见 § 6.5 关于 message 的注意事项 |
| 5 | 回主干 | `git switch master && git pull --rebase origin master` | — |
| 6 | 清分支 | 删本地与远端特性分支 | — |

第 3 步出现失败检查时：**停下报告，不自动重试、不自动改代码**。CI 红说明门禁真的拦到了东西，与 `pre-commit` 阻断时「禁止绕过」的处置同构。

⚠️ **第 6 步「清分支」有一个实测到的坑：squash merge 之后 `git branch -d` 会拒绝删除**，报 `not fully merged`。这不是 git 出错——squash 产生的是一个**全新的 commit 对象**，特性分支的那些 commit 从未成为它的祖先，按可达性判断确实「未合并」。

🔴 **不能因此就改用 `-D`**：`-D` 对「真的没合进去」和「合进去了但换了对象」这两种情形一视同仁，直接用等于放弃判断。正确判据是**比对树对象**：

```bash
git rev-parse <branch>^{tree}   # 与
git rev-parse master^{tree}     # 相等 ⇒ 内容已完整落地，再 -D
```

树对象相等意味着两边的文件内容逐字节一致，这正是「已合并」在 squash 语境下的实质含义。本会话执行第一个 PR 时两边均为 `945812d6345c0f30015bfc8fa43577b37bcf28d8`，据此才 `-D`。**这条判据必须写进 SKILL.md，否则要么日常撞上一个看起来像故障的拒绝、要么养成无脑 `-D` 的习惯。**

### 6.4 ⚠️ 这是 auto-merge 的等效实现，不是 GitHub 的 auto-merge

用户选择的是「全自动：建 PR + auto-merge」。需要如实说明：**GitHub 原生的 auto-merge 是一个 GraphQL mutation（`enablePullRequestAutoMerge`），MCP 服务器未提供对应工具**。§ 6.3 用「轮询 + 显式 merge」达到同样的最终状态。

两者的实质差异只有一处，但真实存在：

| | 原生 auto-merge | 本方案（轮询 + 显式 merge） |
|---|---|---|
| 会话在等 CI 期间中断 | GitHub 在服务端继续等，CI 绿后**自行合并** | PR 停在未合并状态，**需下次触发 skill 时接续** |

缓解措施即 § 6.2 的第二支：下次触发时检测到「当前已在特性分支且有开着的 PR」，直接跳到轮询与合并。**不为此引入 `gh` CLI**——它能做到原生 auto-merge，但为一个「会话中断时少一次接续」的收益引入新依赖不划算，而 § 6.2 的接续逻辑本来就必须存在（CI 变红同样会让流程停在中途）。

### 6.5 squash merge 会丢 `Co-Authored-By`

GitHub 做 squash merge 时默认用 PR 的 title/body 生成主干 commit message，**特性分支上 commit 里的 `Co-Authored-By` 尾注不会自动进入 squash 后的 commit**。而 `knowledge-base/git/rules/02-commit-messages.md` 要求标注 AI 协作者。

处置：第 4 步调用 `merge_pull_request` 时**显式传 `commit_title` 与 `commit_message`**，把原 commit 的正文与 `Co-Authored-By` 尾注原样带进去。这一条必须写进 SKILL.md 的第五步，否则主干上的 AI 协作者标注会从此静默消失——属于「不报错的失效形态」。

PR 描述另需按归属约定加 `🤖 Generated with [Claude Code](https://claude.com/claude-code)` 尾注；该尾注只进 PR body，**不进** squash 后的 commit message。

✅ **本节的推断已实测确认**（PR #1，squash 成 `50e6fb6`）：显式传 `commit_title` + `commit_message` 后，`Co-Authored-By` 尾注**确实原样进入了主干 commit**。

⚠️ 同时测出一个副作用：**显式传 `commit_title` 时 GitHub 不再自动追加 `(#N)` 后缀**。PR #1 的主干 commit 标题末尾那个 `(#1)` 是手工写进 `commit_title` 的。这条不写下来，日后主干 log 会分成「带 PR 号」和「不带」两种，而这种不一致既不报错也没人会立刻注意到——属和 `Co-Authored-By` 丢失同一类的静默失效。**`commit_title` 必须自己带上 `(#N)`。**

## 7. 规范条款改动

### 7.1 `knowledge-base/git/rules/03-pull-requests.md:25` —— 加作用域限定

⚠️ **必须走 `knowledge-base-maintain` skill**（同步 `index.jsonl`、CHANGELOG、领域版本号，跑一致性校验），禁止直接编辑条目正文。todo 第 18 行已明确这一点。

现状（单条同时管两件事）：

> - **必须**：主干分支要求至少一名 reviewer 批准且 CI 全绿才允许合并

改为拆成两条，一条无条件强化、一条加作用域：

> - **必须**：主干分支要求 CI 全绿才允许合并
> - **必须**：多人协作仓库要求至少一名 reviewer 批准才允许合并。**单人维护仓库不适用**——GitHub 不允许 PR 作者批准自己的 PR，要求 ≥1 批准会使主干永久不可合并；此类仓库以「CI 全绿 + 保护规则禁止直推」作为等效约束

拆条的理由：原条款把「CI 全绿」和「reviewer 批准」用「且」绑在一起，给单人仓库加作用域限定时会连带豁免掉 CI 要求，而 CI 要求恰恰是本次要**强化**的部分。**不拆条就无法只豁免其中一半。**

`:24`（禁止直推、禁止 force push、只能 PR）与 `:26`（`release/*`）**不动**。

### 7.2 `knowledge-base/git/rules/01-branching.md:17` —— 消解条款内的措辞矛盾

该条款正文要求「`type` 取值与提交信息 `type` 对齐」，但括号内枚举给的是 `feature`，而本仓提交用的 Conventional Commits 类型是 `feat`。**条款自己的两半互相矛盾**：逐字对齐的话该叫 `feat/`，照抄括号的话该叫 `feature/`。

本仓此前 trunk-based、几乎不建特性分支，所以该矛盾一直没被撞上。走 PR 后每次提交都要决定分支名，不消解就会每次重新纠结。

裁决：**以正文的「对齐」为准，括号内枚举改为 Conventional Commits 类型**（`feat`/`fix`/`docs`/`refactor`/`chore` 等），`:18` 的示例 `feature/123-add-login` 相应改为 `feat/123-add-login`。理由是 MUST 的正文才是规范意图，括号是示例；而「逐字相同」是最强、也是唯一不需要维护映射表的对齐方式。

同样走 `knowledge-base-maintain`。这一改动与 § 7.1 在同一领域、同一次维护内完成。

### 7.3 `AGENTS.md`「提交与推送」节 —— 重写

需要写进去的四件事：

1. **主干已开保护，直推会被拒绝**。提交路径是「特性分支 → PR → CI 绿 → squash merge」。
2. `commit-cc-plugin` 仍是**唯一**提交路径（该 skill 内部已改为 PR 流程），Codex 侧走标准 git 时同样必须建分支走 PR——ruleset 是服务端强制，不依赖任何 harness 的自觉。
3. **门禁现在有两个执行点**：`pre-commit` 在本地（需 `git config core.hooksPath .githooks`），CI 在 PR 上跑**同一批脚本**。后者不依赖本机配置，是 `pre-commit` 长期缺口的补齐。
4. **新增 skill 必须带 eval case**（`plugins/<plugin>/skills/<skill>/evals/<case>/`，与 SKILL.md 同目录下的 `evals/`），由 `new-skill-eval-case` job 强制；存量不回溯。可参照的活体样本是 `jenkins-build` 的 20 条（§ 5.9.2）。
5. **版本矩阵补两行**：`.github/` → 不升任何版本（§ 8.3）；`plugins/*/skills/<name>/evals/` 命中既有的第一行、**要升**插件两份 `plugin.json` 与该 skill 的 `metadata.version`——⚠️ 后者矩阵已隐含覆盖（「内任一文件」），但「改 eval 要升 skill 版本」反直觉到值得一条明文，否则每次都要重新推导一遍。

### 7.4 `.githooks/README.md` —— 新增一条约定

CI 逐字执行 `sh .githooks/pre-commit`，因此该脚本**不得引入依赖暂存区的检查**（`git diff --cached` 等）。当前六项检查全部基于工作树与 `git ls-files`，该性质必须被显式记录并保持，否则两个执行点的判据会静默分叉。

同时把 CI 作为第二执行点写进「启用」一节——现在「未启用时 hook 静默不执行」这句话有了限定：本地未启用仍会被 PR 上的 CI 拦住。

## 8. 受影响文件与版本影响

### 8.1 新建

| 文件 | 说明 |
|---|---|
| `.github/workflows/ci.yml` | 五个零 token job（§ 5.3 – § 5.7），无 `paths:` 过滤；官方 composite action 按 40 位 SHA 引用（`426e469f…`）、`claude-cli-version` 传 `2.1.270` |
| `.github/workflows/skill-eval.yml` | 手动 eval（§ 5.8），六个开关按该节表格逐项设定 |
| `.githooks/check_new_skill_eval_case.py` | § 5.7 的 diff 检查实现；文件名在 Python 内解析，不经 shell |
| `.githooks/test_check_new_skill_eval_case.py` | 配套单测 |
| `plugins/optimus-devops-plugin/skills/jenkins-build/evals/<case>/prompt.md` ×20 | § 5.9.2 迁移产物，每条 query 一个 case 目录 |
| `plugins/optimus-devops-plugin/skills/jenkins-build/evals/<case>/graders/triggered.md` ×20 | 同上，正例 `min: 1` / 负例 `max: 0` |

**为什么 diff 检查放 `.githooks/` 却不挂进 `pre-commit`：** `.claude/rules/hook-conventions.md` 约定「仓库级门禁必须放 `.githooks/`」，所以脚本位置遵守该约定；但它依赖两个 ref 之间的 diff，而 § 5.3 又要求 `pre-commit` 保持暂存区无关。两者的解法是——脚本接受 base/head 两个 ref 作参数、**只由 CI 调用**，不进 `pre-commit` 的检查序列。目录约定与暂存区无关性因此都不破。

按 `AGENTS.md` 的门禁改动要求，新增门禁必须**脚本 + 测试 + 文档**三件齐备，缺一不可。

### 8.2 修改

| 文件 | 改动 | 经由 |
|---|---|---|
| `.claude/skills/commit-cc-plugin/SKILL.md` | 第一步分支判定、第三步上游改判、第四步前建分支、第五步整节重写、常见错误表补条目 | 直接编辑 |
| `AGENTS.md` | 「提交与推送」节重写（§ 7.3）；版本触发矩阵补 `.github/` 一行 | 直接编辑 |
| `.githooks/README.md` | 暂存区无关性约定、CI 第二执行点、新门禁登记（§ 7.4） | 直接编辑 |
| `knowledge-base/git/rules/03-pull-requests.md` | `:25` 拆条 + 加作用域（§ 7.1） | **`knowledge-base-maintain`** |
| `knowledge-base/git/rules/01-branching.md` | `:17`/`:18` 消解措辞矛盾（§ 7.2） | **`knowledge-base-maintain`** |
| `knowledge-base/git/index.jsonl`、CHANGELOG、领域版本号 | 随上两项同步 | `knowledge-base-maintain` 自动 |
| `docs/todo-list/2026-09-12-todo.md` | 标记该条目已裁决，指向本 spec | 直接编辑 |
| `plugins/optimus-devops-plugin/skills/jenkins-build/SKILL.md` | `metadata.version` 升 Minor（新增 eval 套件） | 直接编辑 |
| `plugins/optimus-devops-plugin/.claude-plugin/plugin.json`、`.codex-plugin/plugin.json` | `version` 同步升 Minor（§ 8.3） | 直接编辑，**两份同值** |

### 8.2.1 删除

| 文件 | 理由 |
|---|---|
| `plugins/optimus-devops-plugin/skills/jenkins-build/evals/trigger-eval.json` | 已迁成官方格式（§ 5.9.2）。⚠️ **必须先逐条核对 20 条 query 全部落地再删**——删在前、漏在后就是静默丢素材 |

### 8.3 版本影响：`optimus-devops-plugin` 要升，其余不升

⚠️ **本节原先的结论是「全部不升」，已被 § 5.9 的范围扩张推翻。** 推翻的路径值得记一笔：eval case 的目录约定从仓库根 `evals/` 改成 `plugins/*/skills/<skill>/evals/`（§ 3.5.1 第 3 条实测），落点因此从「不随插件分发的仓库基建」变成了「插件分发单元内部」——**同一批文件，只因为存放位置变了就跨过了版本矩阵的边界**。

按 `AGENTS.md` 触发矩阵逐项核对：

| 改动落点 | 是否升版本 | 依据 |
|---|---|---|
| `plugins/optimus-devops-plugin/skills/jenkins-build/evals/` | ✅ **插件两份 `plugin.json` + 该 skill 的 `metadata.version`** | 矩阵第一行：「`plugins/*/skills/<name>/` 内任一文件」→ 插件 ✅、`SKILL.md` `metadata.version` ✅ |
| `.claude/` 下（`commit-cc-plugin`） | ❌ | 矩阵明列「`.claude/` 下任何文件 → 不升」 |
| `AGENTS.md`、`docs/` | ❌ | 矩阵明列 |
| `.githooks/` | ❌ | 不随插件分发，harness 读不到 |
| `.github/` | ❌ | **矩阵未列此路径**，见下 |
| `knowledge-base/git/` | 领域版本升，插件版本 ❌ | 知识库有独立版本体系 |

**幅度：两处都是 Minor。** 插件侧按矩阵的「新增 skill / agent / hook / command」类比——eval 套件是新增的用户可见产物；skill 侧按「新增功能 / 章节 / 参数」。⚠️ 两侧幅度一致在这里是巧合而非规则，矩阵明确允许同一次改动在不同层取不同幅度。

⚠️ **只改 evals/ 却要升 `SKILL.md` 的 `metadata.version`，读起来反直觉，但矩阵是明文**（「`plugins/*/skills/<name>/` 内**任一**文件」）。这不是矩阵写宽了：eval 套件是该 skill 的产物之一，`metadata.version` 作为描述性版本号，本就该反映「这个 skill 演进到哪一步」——有了行为测试的 skill 与没有的，确实不是同一步。

**考虑过并否掉的规避方案：** 用 `plugin.json` 的 `experimental.evals` 把 eval 目录指到插件外（如仓库根），落点就不在分发单元内、也就不升版本。否掉的理由不是配置麻烦，而是**它会让「找 skill 的 case」重新需要一层映射**（§ 5.7 已论证过这层映射的代价），且把 eval 与被测对象分置两处。**为了少升一次版本号去换一层间接性，是拿长期可读性换一次性的省事。**

⚠️ **矩阵里没有 `.github/` 这一行。** 按矩阵的核心规则「改动物理上落在哪个分发单元内，就升那个单元的版本号」，`.github/` 不在任何插件内、不随插件分发，因此不升任何版本号——但这是**推导结论而非明文**。建议在 § 7.3 改 `AGENTS.md` 时**顺带补上这一行**，把推导变成明文，避免下次重新推导。

🔴 **`pre-commit` 的版本同值检查这次会真的参与进来**（此前设计里 `plugins/` 无改动、该检查空转）：两份 `plugin.json` 必须在**同一次提交内**升到同一个值，漏一份就会被阻断。这是本次交付第一次触发该门禁，也正好是它的一次实测。

### 8.4 `darwin-skill` 评分门禁在本次的适用性

`AGENTS.md` 规定「Minor/Major 升级前必须用 `darwin-skill` 对改动的 skill 评分，新分数 ≥ 改动前分数才可提交」。§ 8.3 判定 `jenkins-build` 的 `metadata.version` 升 Minor，字面上命中该门禁。

**实际处置：跑一次评分留档，但预期分数不变。** 依据是 `AGENTS.md` 自己给出的门禁边界——「该门禁只约束 skill，因为 darwin-skill 的 rubric 针对 SKILL.md 结构」。本次改动**不触碰 `SKILL.md` 正文**，只改它的 `metadata.version` 一行，加上在 `evals/` 下新增文件；rubric 的输入没变，分数不该变。

⚠️ **仍然要跑，不能因「预期不变」就跳过。** 两个理由：① 「预期不变」是推断，而门禁存在的意义正是不依赖推断；② 若分数**真的变了**，说明 rubric 会读 skill 目录下的非 SKILL.md 内容，那是一个关于门禁本身的新事实，值得记下来——**一次预期无信息量的检查，恰好是发现判据边界的时机。**

## 9. 验收标准

每项都要跑到、并留下可核对的输出。**其中两项是阴性对照——只验证「绿」不能证明门禁有效**（§ 3.1 的 `contents: []` 就是这个教训：一个什么都不查的门禁与一个全部通过的门禁，输出无法区分）。

💰 **第 10、11 项是本 spec 唯一会产生费用的验收项**（合计 ≈$3.15），其余十项零成本。两项刻意排成先后：先花 $0.15 确认格式，再花 $3 跑全量——**反过来的话，一个写错的 frontmatter 会让那 $3 白花**。

| # | 目标 | 验证 |
|---|---|---|
| 1 | 本地门禁在 Linux 上可跑 | CI 中 `sh .githooks/pre-commit` 退出 0 |
| 2 | 9 个测试目录全绿 | CI 中每个 `unittest discover` 退出 0，累计用例数与本地一致 |
| 3 | 官方静态校验全绿 | `plugin-validate` job 退出 0，且其 90-report 报告须逐项核对：① marketplace 校验已执行；② 3 个外部条目**已被 clone 并校验**（这是本仓此前完全没有的判据）；③ 本 PR 改动的插件目录已被 40 步命中；④ 追加步骤 `claude plugin validate .claude/skills --strict` 退出 0。⚠️ **判据不是「22 个目标全绿」**——官方 action 的 40 步是**增量**校验（只看本 PR 改动的插件），22 个目标的全量结果只存在于 § 3.1 第 6 条的本机基线里，不是 CI 每次的产出 |
| 4 | 知识库与 tips 一致性 | `check_index.py` / `check_refs.py` / `validate_tips.py` 均退出 0 |
| 5 | **阴性对照**：eval case 门禁真的会拦 | 造一个「新增 SKILL.md 但无对应 `evals/` 目录」的 PR，`new-skill-eval-case` **必须红**；补上目录后转绿 |
| 6 | **阴性对照**：主干真的推不上去 | ✅ **已达成**：清空 bypass 名单后 `git push origin master` 被服务端以 `GH013 … push declined due to repository rule violations` 拒绝（原文见 § 4.1）。⚠️ 判据是「拒绝」而非「有提示」——此前同一命令会**成功**并回 `Bypassed rule violations`，把那行提示误当成保护生效正是本次要消除的错觉 |
| 7 | 全自动流程闭环 | 走一次完整 `commit-cc-plugin`：建分支 → push → PR → CI 绿 → squash merge → 回主干；主干 commit 含 `Co-Authored-By`（§ 6.5） |
| 8 | 知识库改动未破坏一致性 | `knowledge-base-maintain` 的一致性校验通过，领域版本与 CHANGELOG 已同步 |
| 9 | 新门禁有测试与文档 | `test_check_new_skill_eval_case.py` 通过；`.githooks/README.md` 已登记 |
| 10 | **eval 套件格式正确**（先做，≈$0.15） | 跑 `claude plugin eval plugins/optimus-devops-plugin --trust-plugin --no-publish --ablation none --runs 1 --max-cost-usd 0.01`，只读 **load 阶段**输出：须**无任何 `invalid case.yaml` 行**、且 case 计数为 **20**。⚠️ load 对全部 case 一次性完成、发生在第一次 run 之前，所以这一步能一次覆盖全部 20 个；⚠️ `--max-cost-usd` 挡不住第一次 run（§ 3.5.3 第 7 条），**这一步必然花掉约 $0.15**，第二次 run 才被挡下——**这是本仓能做到的最便宜的格式验收，不存在零成本版本** |
| 11 | **负例判据真的成立**（后做，≈$3） | 第 10 项通过后跑全量（去掉 `--max-cost-usd` 或放宽到 5）。判据不是「全绿」而是**分档核对**：10 条正例须以 `min: 1` 通过，10 条负例须以 `max: 0` 通过。⚠️ **10 条负例全过才算 § 5.9.2 的迁移决策被验证**——`max: 0` 能表达「不得调用」此前只有 schema 层证据（字段合法）与渲染文本的旁证，语义未经实跑确认。若负例出现假失败，说明 `max: 0` 的语义与推断不符，该批 case 需改判据形式而非改 skill |
| 12 | 报告未外发 | 上两项的命令输出中**不出现 claude.ai 报告链接**；`--no-publish` 生效（§ 3.5.3 第 8 条） |

## 10. 风险与未决

| # | 风险 | 处置 |
|---|---|---|
| 1 | **CLI 版本漂移**：未来 `validate` 新增一类 warning，叠加 `fail-on-warnings: true` 会让全部 PR 一夜变红，且与任何一次改动都无关 | 显式传 `claude-cli-version: "2.1.270"` 覆盖官方 action 的默认值 —— ⚠️ **该 input 默认是 `latest`，不覆盖就等于接受漂移**。加上 § 5.2 的 action SHA-pin，「校验逻辑」与「校验器版本」两个维度同时冻结，升级是一次显式的成对动作。`sync-cc-tips` 每次同步 changelog 时本就在读 CLI 变更，可顺带评估是否升这两个 pin |
| 2 | **改 job 名会静默失去保护**：ruleset 的必需检查按名字匹配，改名后 GitHub 不报错，只是那项检查不再被要求 | 属「不报错的失效形态」。job 名写进 `.github/workflows/ci.yml` 顶部注释并在 `AGENTS.md` 登记，改名必须同步改 ruleset |
| 3 | **`new-skill-eval-case` 只检查目录与文件存在，不校验 case 内容**——写着 `TODO` 的 `prompt.md` 也能过 | 刻意的边界：内容质量属人工评审。⚠️ 本项的**前提已变**：case 格式此前是「未定」，现已由 § 3.5.2 实测锁定，目录约定见 § 5.7。因此门禁不再是「对着一个还不存在的规范占位」，而是「对着一个已定规范只查其最外层」——**残留风险从「规范未定」缩小为「只查存在性」** |
| 4 | **会话中断导致 PR 悬挂** | § 6.4 已述，靠 § 6.2 的接续逻辑兜住 |
| 5 | **Windows 本地与 Linux CI 的行为差异未实测**：符号链接、路径大小写、`git ls-files -s` 的模式位 | `actions/checkout` 保留符号链接为已知行为，但**本仓未实测**。验收第 1 项即是这项的实测；若 `pre-commit` 在 CI 首跑失败，按失败内容判断是脚本假设了 Windows 还是 CI 环境缺配置 |
| 6 | **`.claude/settings.json` 是否纳入版本库** | 遗留未决项，与本 spec 解耦。它当前已被 `git add` 但未提交；本次交付**不处理**，需单独裁决 |
| 7 | **首个 PR 的鸡生蛋问题已真实爆发**：必需检查先于 CI 配好，6 项全部永久 Expected，主干双向锁死 | § 4.5「实际解锁路径」已给出处置：先移除整条 `required_status_checks`，走 PR 合入 CI，再按 UI 列表**勾选**加回 5 项。⚠️ 教训是那条依赖会倒逼人手打 job 名，而手打绕过了「先跑一次」这道天然校验——`skill-eval` 混入正是该路径的产物 |
| 8 | **现有 ruleset 由用户在本会话期间手动创建**，其意图未完整记录 | 本 spec § 4.1 已把它的完整配置固化为取证，§ 4.2 / § 4.3 逐项给出改动理由。`required_signatures` 一项已单独交用户裁决（结论：删除），不做替用户推断 |
| 9 | 🔴 **eval 报告默认外发到 claude.ai**，而本仓 case 含内部 Jenkins job 名等信息 | `--no-publish` 在 § 5.8 定为恒开、验收第 12 项专门核对。⚠️ **这是本 spec 唯一一个「默认行为即数据外发」的依赖**：其余工具的默认值出错只影响判据强度，这一项出错是信息泄漏。case 级另有 `artifact_publish` 键，新增 case 时须确认未开启——**门禁查不到它**（`new-skill-eval-case` 只查文件存在），只能靠评审 |
| 10 | **`wpf-code-review` 的 6 条素材仍是非官方格式**，`claude plugin eval` 在它上面找到 0 个 case | § 5.9.3 已记明：唯一可用的是付费 `llm` grader，而其判据措辞稳定性与 `--threshold` 默认 1.0 的适用性均未取证。列为未来项。⚠️ **风险不是「暂时没迁」而是「看起来已经有 eval 了」**——目录里躺着一个名为 `evals/` 的文件夹却一个 case 都不产出，与 § 3.1 第 2 条那个 `contents: []` 教训同形：**存在一个文件不等于存在一份判据** |
| 11 | **`--runs 1` 在引入 `llm` grader 后不再合适** | 当前全部判据是 `tool_used` 布尔判定，确定性的，重复不增信息。`llm` 评委有抖动，单次结果不可据以判定回归。§ 5.8 已就地记明「届时调回 ≥3」——⚠️ 但这条依赖人记得，**没有任何机制会在新增 `llm` grader 时提醒调 `--runs`** |
