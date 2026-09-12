---
name: add-external-skill
description: 把外部仓库的 Agent Skill 接入本仓库，或更新已接入条目的版本锁定。探测上游仓库形态、判定落位方式（默认链接：marketplace 条目锁 40 位 sha；例外才拷贝到 external_plugins/）、取 sha、人在回路确认、写入并验证、记台账。更新失败一次即停，不重试、不轮询。只能由人显式调用 /add-external-skill 触发。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要 git（用 git ls-remote 取上游 sha）与可达上游仓库的网络；写入后的验证步骤需要 claude CLI 的 plugin 子命令；传感器 .githooks/check_external_entries.py 需要 Python 3 标准库。
allowed-tools: Read Write Edit Bash Grep WebFetch
disable-model-invocation: true
---

# add-external-skill

把「引入外部 skill」固化为可反复执行的判断流程，取代此前散落在提交信息里的一次性推导（先例：`4d741b8` 引入 `cangjie-skill`）。设计依据：`docs/superpowers/specs/2026-09-12-add-external-skill-design.md`。

## 适用范围与边界

三条不做：

1. **不做 Codex 侧的远程引用覆盖。** `.codex-plugin/plugin.json` 是强制项且 `skills` 只接受单一路径字符串，没有 Claude 侧 `strict:false` 那样的豁免机制——这是结构性差异，不是本 skill 遗漏。`cangjie-skill` 已确立「接受非对称」的先例：链接模式只在 Claude 侧生效，Codex 侧不装该外部 skill。
2. **不修改上游内容。** 走链接或拷贝都是接受上游内容原样进来；需要改内容的场景，由人显式决定 fork 后再走「必须改内容」的拷贝正当理由，不由本 skill 自动完成任何改写。
3. **不建 `external_plugins/`，除非命中拷贝判据**（见「拷贝模式」一节的两条正当理由）。默认路径永远是链接；「拷贝更省事」「不想每次装的时候联网」都不构成理由。

## 触发方式

**本 skill 只能由人显式 `/add-external-skill` 触发。** 不支持模型按 `description` 自主拉起，也不支持 `/loop` 等无人值守调度自动执行——这是 frontmatter 里 `disable-model-invocation: true` 的官方行为（v2.1.196 起）。

为什么要收紧到这一条路径：本 skill 会把**能在用户权限下执行任意代码的第三方插件**写进 marketplace，官方对插件的原话是「can execute arbitrary code on your machine with your user privileges」。即便 Step 4 的 CHECKPOINT 仍会在写入前拦住确认，「是否现在讨论引入某个外部插件」这件事本身也应当由人发起，而不是模型看到某句话像是在提外部仓库就顺手拉起判断流程。

三点连带影响，如实记在这里，不留给后人自己踩：

1. **`/loop` 等计划触发会把本 skill 当作纯文本而不执行。** 这正是要的——更新必须由人显式发起（见「更新模式」U0），不得被任何调度器代为拉起。
2. **`skills-ref validate` 必然报 `Unexpected key(s): disable-model-invocation`，这是预期结果，不是要修的规范偏差。** 该字段是 Claude Code 原生合法字段，在 `.claude/skills/` 这一层允许使用（`.claude/rules/skill-conventions.md`），不需要登记豁免（口径同 `sync-cc-tips`；`bb6867a` 撤销的是「具名例外」这一定性，不是字段本身）。**不要因为想让校验变绿就删掉这个字段。**
3. **Codex 侧对该字段的行为见下方「Codex 兼容性」。**

### Codex 兼容性

Codex 没有与 `disable-model-invocation` 等价的 SKILL.md frontmatter 字段；Codex 用一份独立的 `agents/openai.yaml` 承载同类策略（`policy.allow_implicit_invocation: false`）。**该结论目前只经文档调研得出，未在真实 Codex 会话中实测**——第三方使用者的报告一致描述的现象是「该字段不生效、skill 仍正常加载进上下文」，即降级为静默忽略而非硬报错，未见任何关于 Codex 严格校验 frontmatter 并拒绝未知顶层键的记载。据此**推断**本 skill 在 Codex 侧仍可被同名触发，只是「禁止模型自主拉起」这条约束在 Codex 侧不生效。这是推断而非确认结论，完整取证来源与状态见 `known-issues.md` 第 2 条（状态：待验证（非实测））。

## 两个模式

| 模式 | 触发 | 干什么 |
|---|---|---|
| **接入** | 人显式 `/add-external-skill` | 探测形态 → 定落位 → 锁 sha → 写条目 → 验证 → 记台账 |
| **更新** | 人显式调用并指明「更新 X」 | 取新 sha → 展示变更 → 确认 → 改 sha → 验证；失败即停并回滚 |

两个模式**都没有**「自然语言触发」这一行——`disable-model-invocation: true` 已从机制上取消该路径，本 skill 正文不出现暗示模型可自主判断「该不该拉起本 skill」的措辞。

**更新为什么必须与接入同处一个 skill，不拆成两个：** 「更新失败不重试」是接入方式的直接后果——只有接入时锁死了 40 位 `sha` 且条目内永不写 `version`，`/plugin update` 才会在 sha 相同时直接 skip（省去了任何重试机制的必要性）。这个结论建立在接入阶段的写入规则之上；如果把更新拆成独立 skill，两边各自维护一套「该不该重试」的判断，口径迟早漂移。同一个 skill 里两个模式共享同一份写入规则，是保持口径一致的手段，不是偷懒少建一个 skill。

## Step 0：需求预告

第一步先比对「接入需要哪些信息」与「用户已在触发语句或上下文中提供了哪些」，缺失项一次性问齐，不逐个 Step 卡顿式追问：

- **上游仓库地址**（URL）——必须，否则连形态探测都无法开始。
- **条目名**——若用户未指定，可从仓库名推导并在确认时展示，不强制用户单独提供；但若推导结果可能与 `marketplace.json` 已有条目冲突，需要在预告里一并提出。

**依赖状态不计入本环节的比对**：git 是否可用、上游网络是否可达，属于系统状态而非用户能在触发语句里主动提供的信息，不作为「缺失项」询问，也不参与「信息是否齐全」的判定——这些留给 Step 1 的实际检测。

若上游 URL 与条目名（或可推导的条目名）已经齐全，跳过本预告，直接进入 Step 1。方式默认链接，不必用户指定，也不在预告里问。本步不做任何系统调用——不检测 URL 是否可达、不检测条目名是否冲突，这些是 Step 1 的事。

更新模式的预告：需要「更新哪个条目」，即条目名必须已在 `registry.md` 「已接入」表中存在；未指明则询问，不得默认更新任意条目。

## Step 1：执行前置校验

四类检查，按 `.claude/rules/skill-conventions.md` 的口径：

| 类别 | 检查什么 | 性质 |
|---|---|---|
| 依赖 | `git ls-remote <url>` 能否访问该 URL（同时验证 git 命令可用与网络可达） | 硬约束，失败终止 |
| 输入 | 上游 URL 形态合法（可被 git 识别）；条目名尚未被 `marketplace.json` 的 `plugins` 数组占用 | 硬约束，失败终止 |
| 输出 | `.claude-plugin/marketplace.json` 可写；若走拷贝模式，`external_plugins/` 的父目录（仓库根）可写 | 硬约束，失败终止 |
| 运行条件 | **License 可确认**；**上游存在可识别的 skill 载体**（`SKILL.md` 或 `.claude-plugin/plugin.json`，见 Step 2 判定表） | 硬约束，失败终止 |

**这两项运行条件都是硬约束，不是可协商风险**，理由：

- **License 不明** 时引入即构成法律风险，即便用户明确表示「不管什么协议都要接」也不能消除风险本身，用户确认无法把不明确的授权变成明确的授权——这与「画质损失、用户知情后可接受」那类可协商风险不同，属于「用户确认也无法绕过」的硬约束定义。
- **上游没有可识别的 skill 载体**（形态判定表第五行）时，接入的产出物本身无意义——不存在一个「效果打折但仍能用」的降级版本可供用户知情后接受。

类别 1–3（依赖/输入/输出）与上述运行条件检查失败时一律终止，不留任何写入残留。

## Step 2：形态判定

这是本 skill 的核心资产。「看着能接其实不能」只有这一道防线，没有判定表就只能试错——五分支，穷举：

| 探到什么 | 落位 | 已知实例 |
|---|---|---|
| 有 `.claude-plugin/plugin.json`（根或子目录） | `git-subdir` + `path`，**不写** `strict` / `skills` | ppt-master（在 `skills/`） |
| 根有 `SKILL.md`、全仓无 `plugin.json` | `url` + `strict:false` + `skills:["./"]` | cangjie-skill（存量）、darwin-skill（未引入） |
| skill 在子目录、无 `plugin.json` | `url`（整仓）+ `strict:false` + `skills:["./<子目录>"]` | archify（`archify/`）；官方 `amd-skills`、`learn-with-coursera` |
| 根是 `.claude-plugin/`**`marketplace.json`**（而非 `plugin.json`） | **不要把 marketplace 当 plugin 引**——读它自己的条目，照抄其中的 source 形态 | ppt-master 根目录即此形态 |
| 无 `SKILL.md`、靠 CLI 安装（`pip`/`uv`/自带 installer 生成 skill 文件） | **判定不适用**，终止接入，写入 `registry.md` 的「已排除」表（子类：形态不适用） | graphify |

**第四行是易错点**：`hugohe3/ppt-master` 根目录的 `.claude-plugin/` 里是 `marketplace.json` 而不是 `plugin.json`——它本身是一个 marketplace，不是一个插件。把它当 plugin 直接引用，会得到一个没有 skill 内容的空插件。正确做法是打开它自己的 marketplace 条目，读出其中声明的 source 形态再照做——该条目实际用 `git-subdir` + `path: "skills"`，与本表第一行一致。

**第三行为什么选 `url` + `skills:["./<子目录>"]`，而不是语义等价的 `git-subdir` + `path` + `skills:["./"]`**：两者效果相同，但前者的两个半边都有官方先例——`url` 源见本仓 `cangjie-skill`，`skills` 指向子目录见官方 `amd-skills`（`["./local-ai-use", …]`）与 `learn-with-coursera`（`["./learn-with-coursera"]`）。`skills:["./"]` 只在本仓 `cangjie-skill` 里与 `url` 源搭配出现过；与 `git-subdir` 组合在官方 295 条条目中零先例，未经验证。代价是 `url` 会取整仓（例如 archify 仓根还带着 `archify.zip`、`benchmarks/`、`experiments/` 等无关内容），比只取子目录更重——**这是刻意用体积换确定性**。若实施时实测确认 `git-subdir` + `skills:["./"]` 可行，可作为后续优化项替换，但不在本次判定范围内自行切换。

命中「判定不适用」分支时，终止接入流程，不继续尝试拷贝模式——「仓库形态无法被远程引用表达」明确**不构成**转拷贝的理由（见「拷贝模式」一节）。

## Step 3：取 sha

命令：`git ls-remote <url> <ref>`。

**为什么不用 GitHub API**：`ls-remote` 对任意 git 主机都成立，不绑定 GitHub，不需要处理 API 速率限制与鉴权问题——本仓上游不保证都在 GitHub 上。

**`ref` 不得假定为 `main`**，必须实测取值。已知反例：`alchaincyf/darwin-skill` 默认分支是 `master`，`Graphify-Labs/graphify` 是 `v8`。取到的 `sha` 必须是 40 位全长十六进制，缩写形式不满足传感器 `check_external_entries.py` 的校验，也会退回「跟随分支最新」的风险。

## Step 4：🔴 CHECKPOINT

写入前必须向用户展示以下五项，等待确认后才能进入 Step 5：

1. **探测结论与所选落位形态**——命中 Step 2 判定表的哪一行、为什么。
2. **锁定的 40 位 sha**（与 `ref`）。
3. **License**（License 不明时不应该走到这一步——Step 1 已把它列为硬约束）。
4. **该 skill 会带进来什么**：是否含 `scripts/`、`hooks/`、`.mcp.json`；是否需要用户额外安装依赖（如 Python 包、CLI 工具）。
5. **Codex 侧是否覆盖**——链接模式默认不覆盖 Codex（见「适用范围与边界」第 1 条），拷贝模式才会。

这个确认点不可省：官方对插件的原话是「can execute arbitrary code on your machine with your user privileges」——写入 marketplace 条目等于给了这段代码在用户机器上以用户权限执行的资格，必须让人在看清这五项之后再点头。

## Step 5：写入

四条硬规则，全部来自官方 243 条远程引用条目的实测口径（`docs/superpowers/specs/2026-09-12-add-external-skill-design.md` § 2.1）：

| # | 规则 | 违反的后果 |
|---|---|---|
| 1 | 必锁 `sha`，40 位全长 | 退回「跟随分支最新」，「更新失败不重试」的第一层保障当场失效 |
| 2 | 条目内**永不写** `version` | 覆盖 sha 的更新信号；且与本仓既有铁律（marketplace 条目不填 version）同向 |
| 3 | `ref` 与 `sha` 并写，`ref` 只作人类可读的分支记录 | 不致命，但丢掉「这个 sha 来自哪个分支」的线索 |
| 4 | 展示字段补齐 `description` / `homepage` / `author`；`category` 建议填但不强制 | 官方 243/243 都有 `homepage`，缺失则来源不可追；`category` 官方覆盖率 94%，未到全量，不设为硬要求 |

**`url` + `strict:false` 型条目模板**（形态判定表第二、三行）：

```jsonc
{
  "name": "<条目名>",
  "description": "…（注明外部引入 + 上游 + License）",
  "source": {
    "source": "url",
    "url": "<上游 git 地址>",
    "ref": "<实测得到的默认分支/tag>",
    "sha": "<git ls-remote 取到的 40 位值>"
  },
  "strict": false,
  "skills": ["./<子目录，根目录用 \".\">"],
  "author": { "name": "<上游作者>" },
  "homepage": "<上游仓库主页>",
  "category": "<可选>"
}
```

**`git-subdir` 型条目模板**（形态判定表第一行）：

```jsonc
{
  "name": "<条目名>",
  "description": "…（注明外部引入 + 上游 + License）",
  "source": {
    "source": "git-subdir",
    "url": "<上游 git 地址>",
    "path": "<plugin.json 所在子目录>",
    "ref": "<实测得到的默认分支/tag>",
    "sha": "<git ls-remote 取到的 40 位值>"
  },
  "author": { "name": "<上游作者>" },
  "homepage": "<上游仓库主页>",
  "category": "<可选>"
}
```

写入拷贝模式时不使用上述条目模板，改按「拷贝模式」一节的目录结构落位。

## Step 6：验证

顺序执行：

1. `claude plugin marketplace update optimus-plugins-official`
2. `claude plugin install <name>@optimus-plugins-official`
3. 确认新接入的 skill 能在 skill 列表中列出。
4. `python .githooks/check_external_entries.py .`，确认退出码为 0。

第 4 步不是可选项——它是本 skill 与 `.githooks/check_external_entries.py` 之间的唯一接口：条目写歪（漏 sha、误写 version、`strict:false` 却没有 `skills` 数组等）本 skill 不会自己发现，必须靠传感器机械校验。

任一步失败按「失败处理」一节的对应格处置，不在这里临场发挥。

## Step 7：收尾

1. **记台账**：在 `registry.md` 的「已接入」表新增一行，行必须落在 `<!-- registry:active -->` 锚点之后，含 `状态` 列（缺省 `正常`）。
2. **marketplace 顶层版本升 Minor**（先例 `4d741b8`）——按 `AGENTS.md` 的触发矩阵，新增插件条目属于「集合里的插件数变了」。
3. **调用 `/commit-cc-plugin` 提交**。本仓提交铁律禁止手动执行 git 工作流，本 skill 不例外。

## 更新模式

更新不是「重新走一遍接入」，它有自己的一套 Step，因为「严格把关更新，尤其是更新失败」是本 skill 存在的主要理由之一。

| Step | 内容 | 性质 |
|---|---|---|
| U0 | **确认本次是人显式发起的。** 本 skill 不提供任何「顺便检查有没有新版」的入口：不扫描台账全表、不批量更新、不因为这次在接入别的条目就连带检查已有条目是否有新版 | 前置 |
| U1 | 从 `registry.md` 读该条目当前 `sha` 与 `ref`，并与 `marketplace.json` 里该条目**逐字比对**。**不一致则立即终止**——这是上一次更新只做了一半的证据（改了条目没记台账，或回滚了条目没回滚台账），须先人工判明哪一个对应实际验证过的状态，再改另一个，**不要为了继续往下走而随手对齐两边** | 前置校验 |
| U2 | `git ls-remote <url>` 一次调用取回全部 ref。**sha 与台账记录相同则报告「已是最新」并结束，不做任何写入。** 取值失败则按「失败处理」分类处置，不重试 | 取值 |
| U3 | **确认 `ref` 本身仍存在。** 上游删除或重命名分支时 sha 无从取起，这不是网络故障，处置见下方「`ref` 变更的处置」 | 判定 |
| U4 | **取上游变更摘要**（取法见下）。取不到时不跳过，改为在 U5 的 CHECKPOINT 里如实声明「无法取得变更摘要，本次确认是在看不到改了什么的前提下做的」 | 取值 |
| U5 | 🔴 **CHECKPOINT**：旧 sha → 新 sha、变更摘要（或其缺失声明）、上游是否新增了 `scripts` / `hooks` / `.mcp.json` / 依赖、License 是否变化 | 人在回路 |
| U6 | **写入**：改 `sha`（必要时同改 `ref`）；拷贝模式则重新拷贝内容 + 更新 `UPSTREAM.md` + 按「拷贝模式」一节的 version 规则调整版本号。**写入前先记下旧值**——回滚要用 | 产出 |
| U7 | **验证**（同 Step 6 的四步）。不通过则按「失败处理」的「更新写入后失败」一格**回滚到旧 sha** | 验收 |
| U8 | 记台账更新历史（`成功` / `失败（写入前）` / `已回滚` 三种结果都必须留行，`已是最新` 按需留）；同步「已接入」行的 sha（不同步会被传感器第 7 项拦住）；核实自动更新实际状态仍是关闭的（见下）；调用 `/commit-cc-plugin` 提交 | 收尾 |

⚠️ **U6 在 U7 之前，这个顺序无法调换**——安装验证需要条目已经存在才能进行。因此「验证失败」必然发生在已经改了 sha 之后，**回滚是必经动作，不是异常分支**。这一点是理解「失败处理」第四格的前提：那一格里「旧 sha 原样保留」这句话在这条路径上是不成立的，必须显式改回去。

### `ref` 变更的处置

更新模式不只处理 sha。上游改默认分支、把分支换成 tag、或删掉旧分支时，`ref` 必须跟着改——**非 `main` 的 `ref` 是常态**，不是异常（graphify 用 `v8`，darwin-skill 用 `master`）。

| 探到什么 | 处置 |
|---|---|
| `ref` 仍在，sha 变了 | 常规路径，U4 起照走 |
| `ref` 不在了，但能在 `ls-remote` 输出里认出改名后的对应 ref | 在 CHECKPOINT 里**把 `ref` 变更单独列为一项待确认**，不与 sha 更新混为一谈；确认后同改两个字段 |
| `ref` 不在了，且认不出对应物 | **不猜。** 终止，在台账把该条目状态记为「ref 待选定」，待人工重新选定 |

`ref` 变更必须走完整 CHECKPOINT：从 `main` 换到某个 tag 可能意味着上游改了发布策略，也可能意味着我们锁到了一条不再维护的线，两种情况人需要分别判断。

### 变更摘要怎么取

链接模式在本仓**没有上游的本地 clone**，`git ls-remote` 只返回 ref 与 sha、不返回提交日志，所以「展示上游变更摘要」需要显式给出取法，否则这一步在实操上是空话：

| 手段 | 适用 | 代价 |
|---|---|---|
| GitHub compare API（`/repos/{owner}/{repo}/compare/{old}...{new}`） | 上游在 GitHub | 绑定 GitHub、需联网、有速率限制 |
| 临时浅克隆后 `git log --oneline old..new` | 任意 git 主机 | 要落盘 |
| 无 | 非 GitHub 主机且不便克隆 | 摘要缺失 |

**首选 GitHub compare API**，不落盘。退到临时浅克隆时：**克隆到系统临时目录、用 `--filter=blob:none` 做浅克隆、用完即删**，禁止落在仓库工作区内——落在工作区会污染 `git status`，甚至可能被误提交进正式仓库。

**取不到摘要不是终止条件，但也绝不能静默跳过。** U5 的 CHECKPOINT 必须显式声明「无法取得变更摘要，本次确认是在看不到改了什么的前提下做的」，让人知道自己正在盲签，而不是把「取不到就跳过确认」当成流程里的默认分支——那等于在最需要人看的那一次把人绕开了。

### 「不重试」不能只靠默认值

官方文档描述的默认状态：第三方与本地开发 marketplace 的 auto-update 默认关闭。但这是**默认值，不是不可变事实**：

- 用户可能在 `/plugin` → Marketplaces 里手动为本 marketplace 开过自动更新；
- `FORCE_AUTOUPDATE_PLUGINS=1` 会强制插件自动更新，且**它不受 `DISABLE_AUTOUPDATER` 约束**（后者管的是 Claude Code 自身的更新器，不是插件更新）。

因此 U8 要**核实一次实际状态**，而不是断言默认值成立；发现自动更新被开启时**向人报告**，不擅自改用户的全局设置——这不是本 skill 的权限范围。

相关环境变量：`CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` 可让后台 pull 失败时保留既有 clone 而不是删库重克隆，避免一次网络抖动把已装好的插件弄没。本仓因为锁 sha 已使后台 pull 基本不会发生，**不需要主动设置它**；这里记录只是说明该变量与本机制的关系，不构成本 skill 的待办项。

## 失败处理

「更新失败」不能当成一格来处理——写入前失败与写入后失败的处置方向相反：一个是什么都别动，一个是必须动手撤回。按失败发生的位置分四格：

| 失败位置 | 处置 | 台账 |
|---|---|---|
| 接入的探测 / 取 sha 阶段 | 终止，不留任何残留写入 | 记入「已排除」或不记（未接入过） |
| 接入的写入后验证不通过 | 回滚本次写入（条目、目录、版本号一并撤销） | 不留「已接入」行 |
| **更新的写入前失败**（U1–U5 任一步） | **一次失败即停。** 旧 sha 与 `ref` 原样保留——什么都还没改，不需要撤销动作 | 更新历史留一行「失败（写入前）」，含原因与时间 |
| **更新的写入后失败**（U7 验证不通过） | **把 `sha`（及 `ref`）回滚到 U6 记下的旧值**；拷贝模式一并撤回目录与 version。回滚后**再跑一次验证**确认已恢复到可用状态 | 更新历史留一行「已回滚」，写明失败原因与回滚到的 sha |

三条共同的硬规则：**不重试、不排定时任务、不自动改 sha**。用户要求「设个定时任务重试」时应当明确拒绝，并说明理由（见 `test-prompts.json` id 5）。

### 更新失败要分类

「更新失败」不是一种情况。分类的目的不是分类学，而是**避免对一个已经永久失效的上游一次又一次地重来**：

| 类别 | 判据 | 处置 |
|---|---|---|
| **临时不可达** | `ls-remote` 网络层报错、超时、鉴权临时失败 | 停。旧 sha 仍可用，不影响任何已安装的人。台账记「临时失败」，下次人想更新时正常重试——这不违反「不重试」，因为重试是人下次主动发起的，不是本 skill 自己排的 |
| **上游仓库已消失** | 仓库返回 404 / 已删除 / 已转为私有 | 停，并在台账「已接入」行**把状态标记为「上游失联」**。这是链接模式最严重的失效形态：条目还在、装不上新的、也拉不到旧的（但已装好的插件不受影响，因为它已经缓存在本地） |
| **`ref` 已消失** | 仓库可达但目标 ref 不在（见「`ref` 变更的处置」第三行） | 停，台账记「ref 待选定」 |
| **安装验证失败** | 新 sha 拉下来了，但 skill 装不上 / 列不出 | 按上表第四格回滚，台账记「已回滚」并写明现象 |

**「上游失联」必须落成状态标记，不能只是一行历史记录。** 区别在于：历史记录只有翻台账的人才会看到；状态标记会让下一次更新在 U1 就直接知道「这个条目已经不用再试了」。没有这个标记，每次更新都会把同一个已死的仓库重新试一遍——这就是「持续重试」，只不过轮询周期从定时器变成了人的记忆。

⚠️ **「临时不可达」与「上游失联」不可合并处理。** 前者下次照常重试是对的，后者下次照常重试是纯粹的浪费；但两者的表层现象（拉不到）完全相同，只能靠判据区分，不能靠现象区分。

### 失败记进哪一份文件

| 现象 | 落点 |
|---|---|
| 上游侧的事（不可达、仓库消失、ref 消失、上游内容变了导致装不上） | `registry.md` 的更新历史 / 状态标记 |
| 本 skill 自己的表现缺陷（探测判错形态、回滚没撤干净、CHECKPOINT 少展示一项） | `known-issues.md` |

划界的判据是**谁该被改**：上游的事改不了，只能记录并决定是否继续引用；本 skill 的缺陷是要修的东西。两者混在一份文件里，会让真正待修的项被一堆「上游那天挂了」淹没。

## 拷贝模式

默认路径是链接（见「适用范围与边界」）。拷贝只在命中以下两条正当理由之一时才启用：

| 理由 | 为什么它够硬 |
|---|---|
| ① **需要 Codex 侧也生效** | 远程引用在 Codex 无对等能力（见「适用范围与边界」第 1 条），拷贝是唯一出路 |
| ② **必须改内容才能在本仓用，且明确不走 fork** | 上游地址不可改；fork 是首选，用户拒绝 fork 时拷贝是兜底 |

**明确不构成理由的两种**，写在这里防止被当成理由援引：

- **仓库形态无法被远程引用表达**——正确处置是判定不适用并记入排除台账（Step 2 判定表第五行），不是转拷贝。graphify 即此例：它是 Python CLI 项目，skill 正文是 `graphify/skill.md`（小写）+ 15 个按 harness 分版的文件，靠 `graphify install` 写入 harness 目录。拷进来意味着自己维护一份 41KB 正文与一个 CHANGELOG 已达 428KB 的上游的同步，成本远超收益。
- **离线可用**——本仓没有这个约束，不要为不存在的需求开例外。

### 落位

```
external_plugins/<name>/
├── .claude-plugin/plugin.json      version：与下一份同值
├── .codex-plugin/plugin.json       version：与上一份同值
├── skills/<skill-name>/SKILL.md    上游正文，原样拷入
├── UPSTREAM.md                     防漂移记账
└── LICENSE                         上游 License 原样带入
```

`UPSTREAM.md` 是拷贝模式**唯一**的防漂移手段，四项必填：上游 repo URL、拷贝自的 40 位 commit SHA、拷贝日期、**本地改动逐条清单**（无改动则写「无」）。缺了它就等于「仓内一份、上游一份，谁都不知道差多少」——`.githooks/check_external_entries.py` 第 8 项会校验它存在且含一枚 40 位 SHA。

### version 规则

**与官方刻意分叉**：官方 14 个 vendored 插件里 10 个不写 `version`。本仓**必须写，且两份 `plugin.json` 同值**——因为它是本仓自己维护的双 harness 分发单元，要落进 `.githooks/check_plugin_versions.py` 的管辖范围才自洽。取值分两种情形：

| 情形 | version 取值 |
|---|---|
| 未做本地改动 | **逐字等于上游版本**（上游 `2.0` → `2.0.0`） |
| 有本地改动 | 上游版本 + `-optimus.N` 后缀（如 `2.0.0-optimus.1`），N 递增 |

上游版本非 semver 时回落 `1.0.0`。⚠️ 起始值取上游版本，与 `AGENTS.md`「新插件起 `1.0.0`」的一般规则冲突——这是刻意例外：上游版本号是读者判断「这份副本是哪一代上游内容」的唯一线索，归零会把这条线索丢掉。

**为什么必须有后缀这一档：** 插件缓存按 version 分目录，若解析出的版本与用户已安装的版本相同，`/plugin update` 与 auto-update 会直接跳过该插件。改了 `external_plugins/<name>/` 的内容但 version 逐字不变，已安装过的人拿到的仍是旧缓存——**改动装不上**，这是功能缺陷，不是记账偏好。而拷贝模式的理由②本来就是「必须改内容」，所以这不是边缘情形，是拷贝模式一半的用途。后缀同时兼作「这不是纯上游内容」的显式标记，比只在 `UPSTREAM.md` 里埋一行更难被忽略。

⚠️ **该分支截至 1.0.0 未被任何真实用例验证。** 首批两个目标（archify、ppt-master）都命中形态判定表的链接分支，`external_plugins/` 不会被创建。首次真正使用拷贝模式时，须按本节展开实际步骤，并在该次提交内补齐 `test-prompts.json` 对应用例——不要假装这个分支已经跑通过。

## 参考

- 设计 spec：`docs/superpowers/specs/2026-09-12-add-external-skill-design.md`
- 配对传感器：`.githooks/check_external_entries.py`（机械检查项见 `.githooks/README.md`，`pre-commit` 第 3 项）
- 台账：`.claude/skills/add-external-skill/registry.md`