# 设计 Spec：add-external-skill —— 把「引入外部 skill」固化为 skill

**日期：** 2026-09-12
**状态：** 待评审
**触发：** `docs/todo-list/2026-09-08-todo.md` 的「将外部skill加入本库」条目

## 1. 背景与目标

### 1.1 要解决什么

本仓库已有一次外部 skill 引入的实践：`cangjie-skill`（提交 `4d741b8`，2026-08-29）。那次的判断过程——外部仓库是什么形态、该用哪种 source、要不要 `strict:false`、Codex 侧做不做、版本号升哪一层——全部留在提交信息里，**没有留在任何可复用的产物中**。下一次引入只能重新推导一遍，且推导质量取决于当次是否想起去翻那条提交。

本次的交付物**不是**把某几个外部 skill 加进来，而是**把这套判断固化成一个可反复执行的 skill**。具体的引入目标是它的首次运行素材与验证用例。

三件必须被固化的事：

1. **形态判定**——外部仓库的形态差异极大，「看着能接其实不能」是真实存在的坑（见 § 4.3 的 graphify）。没有判定表就只能试错。
2. **更新策略**——`cangjie-skill` 那次的结论「不跟随上游自动更新，升级需手动更新 sha」是对的，但它是当次结论，不是仓库约定。下一次可能换个做法。
3. **刹车**——`AGENTS.md` 要求「有生成类 skill 就要有对应的校验类 skill」。条目写歪（漏 `sha`、误写 `version`、`strict:false` 却没有 `skills` 数组）全都不报错、只是静默失效或整条加载失败，正是需要机械检查的形态。

### 1.2 非目标

- **不做 Codex 侧的远程引用覆盖**。`.codex-plugin/plugin.json` 是强制项且 `skills` 只接受单一路径字符串，无 `strict:false` 那样的豁免机制。这是结构性差异，`cangjie-skill` 已确立「接受非对称」的先例，本次沿用并把它写成 skill 内的结论，避免每次引入重新纠结。
- **不修改上游内容**。走上游地址即接受不可改。需要改内容的场景由人显式决定 fork，不由 skill 自动化。
- **不引入 darwin-skill**（本次决策暂缓）与 **graphify**（形态不适用），两者均只登记进台账。
- **不改 `AGENTS.md` 的 darwin-skill 评分门禁一节**——darwin 未引入，该节「darwin-skill 是全局 skill、不在本仓」的表述仍然成立。本 spec 与 `2026-09-12-darwin-artifacts-per-skill-design.md` 完全解耦。
- **不追求拷贝模式在本次被验证**——首批两个目标都走链接，拷贝分支零用例，处置见 § 9 第 10 项。

## 2. 官方做法取证

对 `anthropics/claude-plugins-official` 逐条核查（本机 clone：`~/.claude/plugins/marketplaces/claude-plugins-official`，共 295 条插件条目）。本 spec 后续所有形态规则都以这份取证为依据，不凭记忆或类比推导。

### 2.1 远程引用：243 条

| 核查项 | 结果 |
|---|---|
| source 类型分布 | `url` 154 条 + `git-subdir` 89 条 |
| **锁 `sha`** | **243 / 243 = 100%** |
| 带 `ref` | 88 条（36%，可选） |
| **条目内写 `version`** | **0 条** |
| `strict:false` + 显式 `skills` 数组 | 仅 2 条（`amd-skills`、`learn-with-coursera`）——外部仓无 `plugin.json` 时才用 |
| 每条都有的字段 | `name` `description` `source` `homepage`（243/243）；`category` 229 条、`author` 173 条 |
| `git-subdir` 的子目录字段名 | **`path`**（不是 `subdir`） |

### 2.2 「100% 锁 sha + 0% 写 version」即「更新失败不重试」的官方答案

todo 里那条「更新时若不成功不要持续、定时重试」的需求，官方的解法不是配置某个重试开关，而是**让更新根本不发起**：

省略 `version` 时，插件版本 = 该 source 解析出的 commit SHA（官方原文：「if you omit `version`, Claude Code uses the source's resolved commit SHA」）。`sha` 被钉死 → 每次解析结果与已安装版本相同 → 官方原文：「if the resolved version matches what a user already has, `/plugin update` and auto-update **skip** the plugin」。

三层叠加，构成完整的「不重试」：

| 层 | 机制 | 依据 |
|---|---|---|
| 1 | 锁 `sha` + 不写 `version` → update 直接 skip，不发起拉取 | `/docs/en/plugins-reference#version-management` |
| 2 | 第三方与本地开发 marketplace 的 auto-update **默认关闭** | 官方原文「Third-party and local development marketplaces have auto-update disabled by default」 |
| 3 | 真失败时落 `/plugin` 的 **Errors tab** 由人处理，不静默循环 | `/docs/en/discover-plugins#configure-auto-updates` |

另有 `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1`，用于后台 pull 失败时保留既有 clone 而不是删库重克隆。**本仓不需要设置它**——第 2 层已使后台 pull 不会发生；记录在此仅为说明该变量与本机制的关系，避免后人误以为漏了配置。

### 2.3 `external_plugins/` 在官方仓库里不是「外部仓库的副本」

官方 `external_plugins/` 下 14 个目录（`asana` `context7` `discord` `fakechat` `firebase` `github` `gitlab` `imessage` `laravel-boost` `linear` `playwright` `serena` `telegram` `terraform`），每个只有 `.claude-plugin/plugin.json` + `.mcp.json`（少数带 README/skills/commands）。**它们是 Anthropic 自己为第三方服务写的薄包装插件**，marketplace 条目的 source 是本地相对路径字符串，条目内不写 `version`，14 份 `plugin.json` 里 10 份也不写 `version`。

**官方 295 条里没有任何一例把外部 skill 的原文件拷进仓库。** 本仓保留拷贝模式是本仓自己的决定（判据见 § 3.2），不是对官方做法的照搬，因此其规范（尤其 version 规则）也不照搬官方，见 § 3.4。

## 3. 两种接入方式

### 3.1 默认链接

**链接是默认方式**：不把任何外部内容 vendor 进本仓，只在 `.claude-plugin/marketplace.json` 的 `plugins` 数组加一条 object source 条目。四条硬规则，全部来自 § 2.1 的实测口径：

| # | 规则 | 违反的后果 |
|---|---|---|
| 1 | 必锁 `sha`，40 位全长 | 退回「跟随分支最新」，§ 2.2 的第 1 层当场失效 |
| 2 | 条目内**永不写** `version` | 覆盖 SHA 的更新信号；且与本仓既有铁律（marketplace 条目不填 version）同向 |
| 3 | `ref` 与 `sha` 并写，`ref` 只作人类可读的分支记录 | 不致命，但丢掉「这个 sha 来自哪个分支」的线索 |
| 4 | 展示字段补齐 `description` / `homepage` / `author`；`category` 建议填但不强制 | 官方 243/243 都有 `homepage`；缺失则来源不可追。`category` 官方为 229/243（94%），不到全量，故不设为硬要求 |

⚠️ 规则 3 的实际陷阱：**默认分支不一定是 `main`**。已确认的反例——`alchaincyf/darwin-skill` 是 `master`，`Graphify-Labs/graphify` 是 `v8`。`ref` 必须实测取值，不得假定。

### 3.2 什么时候才可以选拷贝

默认值只有配上**穷举的例外判据**才有约束力，否则会被随手绕过。正当理由只有两条：

| 理由 | 为什么它够硬 |
|---|---|
| ① **需要 Codex 侧也生效** | 远程引用在 Codex 无对等能力（§ 1.2），拷贝是唯一出路 |
| ② **必须改内容才能在本仓用，且明确不走 fork** | 上游地址不可改；fork 是首选，拒绝 fork 时拷贝是兜底 |

**明确不构成理由的两种**（写进 skill 正文，防止被当成理由援引）：

- **仓库形态无法被远程引用表达**——正确处置是判定不适用并记排除台账，不是转拷贝。graphify 即此例：它是 Python CLI 项目，skill 正文是 `graphify/skill.md`（小写）+ 15 个按 harness 分版，靠 `graphify install` 写入 harness 目录。拷进来意味着自己维护 41KB 正文与一个 CHANGELOG 已达 428KB 的上游的同步。
- **离线可用**——本仓无此约束，不要为不存在的需求开例外。

### 3.3 拷贝模式的落位

```
external_plugins/<name>/
├── .claude-plugin/plugin.json      version：与下一份同值
├── .codex-plugin/plugin.json       version：与上一份同值
├── skills/<skill-name>/SKILL.md    上游正文，原样拷入
├── UPSTREAM.md                     防漂移记账
└── LICENSE                         上游 License 原样带入
```

`UPSTREAM.md` 是拷贝模式**唯一**的防漂移手段，四项必填：上游 repo URL、拷贝自的 40 位 commit SHA、拷贝日期、**本地改动逐条清单**（无改动则写「无」）。缺了它就等于「仓内一份、上游一份，谁都不知道差多少」。

### 3.4 拷贝模式的 version 规则

**与官方刻意分叉**：官方 14 个 vendored 插件里 10 个不写 `version`（§ 2.3）。本仓**必须写，且两份同值**——因为它是本仓自己维护的双 harness 分发单元，落进 `.githooks/check_plugin_versions.py` 的管辖范围才自洽。官方省略是因为他们的本地路径插件靠 marketplace 仓库 commit 当版本；本仓有显式 semver 门禁，跟着省略会让 `external_plugins/` 成为门禁盲区。

取值分两种情形：

| 情形 | version 取值 |
|---|---|
| 未做本地改动 | **逐字等于上游版本**（上游 2.0 → `2.0.0`） |
| 有本地改动 | 上游版本 + `-optimus.N` 后缀（`2.0.0-optimus.1`），N 递增 |

上游版本非 semver 时回落 `1.0.0`。

**为什么必须有后缀这一档**：插件缓存按 version 分目录，官方原文「if the resolved version matches what a user already has, `/plugin update` and auto-update skip the plugin」。改了 `external_plugins/<name>/` 的内容但 version 逐字不变，已安装过的人拿到的仍是旧缓存——**改动装不上**。这是功能缺陷，不是记账偏好。而拷贝模式的理由②本来就是「必须改内容」，所以这不是边缘情形，而是拷贝模式一半的用途。

后缀同时兼作「这不是纯上游内容」的显式标记，比只在 `UPSTREAM.md` 里埋一行更难被忽略。

⚠️ 起始值取上游版本与 `AGENTS.md`「新插件起 `1.0.0`」冲突，需在触发矩阵补一行例外（见 § 7）。理由：上游版本号是读者判断「这份副本是哪一代内容」的唯一线索，归零会把它丢掉。

## 4. skill 设计

### 4.1 落位与命名

`.claude/skills/add-external-skill/`——**仅本仓维护自用，不发布**。Claude 侧 `/add-external-skill`，Codex 侧同名触发（经 `.agents/skills/` 镜像）。命名与 `sync-cc-tips`、`commit-cc-plugin`、`record-tools` 一致：动词 + 对象。

按 `.claude/rules/skill-conventions.md`：该层允许使用 Claude Code 原生字段（用了则必须在正文写明该字段解决什么问题）；`metadata.version` 起 `1.0.0`；`metadata.category` 取 `tool`；需配 `known-issues.md`、`CHANGELOG.md`、`test-prompts.json`（2026-08-30 后新建的 skill 自动适用持续优化约定，无需加入「试点范围」清单）。

**必须带 `disable-model-invocation: true`。** 这是本 skill 唯一使用的 Claude Code 原生字段，正文须写明它解决什么问题：本 skill 会把**能在用户权限下执行任意代码的第三方插件**写进 marketplace，官方对插件的原话是「can execute arbitrary code on your machine with your user privileges」。模型按 description 自主拉起意味着这个决定可能在用户没有明确要求的时刻发生——即便 Step 4 的 CHECKPOINT 仍会拦住写入，「是否现在讨论引入某个外部插件」本身也应当由人发起。该字段把入口收敛为**人显式 `/add-external-skill`** 一条。

三点连带影响必须在 SKILL.md 里如实写明，不得留给后人自己踩：

1. 它同时使 `/loop` 等计划触发把本 skill 当作纯文本而不执行（官方行为，v2.1.196 起）。**这正是要的**——见 § 4.4 U0 与 § 4.5：更新必须由人发起，不得被任何调度器拉起。
2. `skills-ref validate` 必然报 `Unexpected key(s)`，那是预期结果，**不是要修的规范偏差**。该字段合法可用，不需登记豁免（口径同 `sync-cc-tips`，`bb6867a` 撤销的是「具名例外」这一定性，不是字段本身）。
3. **Codex 侧对未知顶层字段是忽略还是硬报错未实测。** 风险不是告警而是该 skill 在 Codex 侧整体加载失败。实施时必须在 Codex 侧实测一次并把结论写进 `known-issues.md`；若确认硬报错，则该字段与 Codex 镜像不可兼得，须回来重新裁决（列入 § 10 遗留）。

**它管两件事**，不是一件：

| 模式 | 触发 | 干什么 |
|---|---|---|
| **接入** | 人显式 `/add-external-skill`（Codex 侧同名显式调用） | 探测形态 → 定落位 → 锁 sha → 写条目 → 验证 → 记台账 |
| **更新** | 同上，人显式调用并指明「更新 X」 | 取新 sha → 展示变更 → 确认 → 改 sha → 验证；失败即停并回滚 |

⚠️ 两个模式都**没有**「自然语言触发」这一行——`disable-model-invocation: true` 已从机制上取消该路径。SKILL.md 不得出现暗示模型可自主判断该不该拉起本 skill 的措辞。

更新必须与接入同处一个 skill：「更新失败不重试」是**接入方式的直接后果**（锁 sha 才能让 update 跳过），拆开会让两半的口径漂移。

### 4.2 接入模式的 Step

| Step | 内容 | 性质 |
|---|---|---|
| 0 | **需求预告**：比对「需要什么」与「已提供什么」，缺失项一次性问齐——上游 URL、条目名。方式默认链接，不问 | 静态比对，不做系统调用 |
| 1 | **执行前置校验**（四类，见下） | 前置校验 |
| 2 | **形态探测** → § 4.3 判定表 | 判定 |
| 3 | **取 sha**：`git ls-remote <url> <ref>` 取 40 位 | 取值 |
| 4 | 🔴 **CHECKPOINT**（见下） | 人在回路 |
| 5 | **写入**：链接 → 一条 marketplace 条目；拷贝 → § 3.3 的目录结构 + 条目 | 产出 |
| 6 | **验证**：`claude plugin marketplace update` → `install` → 确认 skill 可列出；跑 `python .githooks/check_external_entries.py .` | 验收 |
| 7 | 记台账、升 marketplace 顶层 Minor、交 `commit-cc-plugin` 提交 | 收尾 |

**Step 1 的四类检查**（口径见 `skill-conventions.md`「执行前置校验」）：

| 类别 | 检查什么 | 性质 |
|---|---|---|
| 依赖 | `git ls-remote` 能否访问该 URL（同时验证 git 可用与网络可达） | 硬约束 |
| 输入 | URL 形态合法；条目名未被 `marketplace.json` 占用 | 硬约束 |
| 输出 | `.claude-plugin/marketplace.json` 可写；拷贝模式时 `external_plugins/` 父目录可写 | 硬约束 |
| 运行条件 | **License 可确认**；**上游存在可识别的 skill 载体** | 两项均为硬约束 |

两项运行条件都是硬约束而非可协商风险：License 不明时引入即法律风险，用户确认也不能消除；没有 skill 载体则产物无意义。

**Step 3 用 `git ls-remote` 而不是 GitHub API**：`ls-remote` 对任意 git 主机都成立，不绑定 GitHub，也不需要处理 API 速率限制与鉴权。

**Step 4 的 CHECKPOINT 必须展示五项**：探测结论与所选落位形态、锁定的 sha、License、**该 skill 会带进来什么**（`scripts/` / `hooks/` / `.mcp.json` / 需安装的依赖）、Codex 侧是否覆盖。官方对插件的原话是「can execute arbitrary code on your machine with your user privileges」，这个确认点不可省。

### 4.3 形态判定表（五分支，穷举）

这是本 skill 的核心资产。「看着能接其实不能」只有这一道防线。

| 探到什么 | 落位 | 已知实例 |
|---|---|---|
| 有 `.claude-plugin/plugin.json`（根或子目录） | `git-subdir` + `path`，**不写** `strict` / `skills` | ppt-master（在 `skills/`） |
| 根有 `SKILL.md`、全仓无 `plugin.json` | `url` + `strict:false` + `skills:["./"]` | cangjie-skill（存量）、darwin-skill（未引入） |
| skill 在子目录、无 `plugin.json` | `url`（整仓）+ `strict:false` + `skills:["./<子目录>"]` | archify（`archify/`）；官方 amd-skills、learn-with-coursera |
| 根是 `.claude-plugin/`**`marketplace.json`** | **不要把 marketplace 当 plugin 引**——读它的条目，照抄其中的 source 形态 | ppt-master 根目录即此形态 |
| 无 `SKILL.md`、靠 CLI 安装（`pip`/`uv`/自带 installer 生成 skill 文件） | **判定不适用**，终止并写排除台账 | graphify |

第四行是易错点：`hugohe3/ppt-master` 根目录的 `.claude-plugin/` 里是 `marketplace.json` 而非 `plugin.json`，它本身是个 marketplace。把它当 plugin 引用会得到一个没有 skill 的空插件。正确做法是读它的条目——该条目用 `git-subdir` + `path: "skills"`，与本表第一行一致。

**第三行为什么选 `url` + `skills:["./<子目录>"]` 而不是 `git-subdir` + `path` + `skills:["./"]`**：两者语义等价，但前者的**两个半边都有官方先例**——`url` 源见本仓 `cangjie-skill`，`skills` 指向子目录见官方 `amd-skills`（`["./local-ai-use", …]`）与 `learn-with-coursera`（`["./learn-with-coursera"]`）。而 `skills: ["./"]` 只在本仓 `cangjie-skill` 里与 `url` 源搭配出现过，与 `git-subdir` 的组合**官方 295 条中零先例**，未经验证。

代价是 `url` 会取整仓（archify 仓根还有 `archify.zip`、`benchmarks/`、`experiments/`、`generated/`、`viewer/`），比只取 `archify/` 重。**这是刻意用体积换确定性**。若实施时实测确认 `git-subdir` + `skills:["./"]` 可用，可作为后续优化换过去，但不在本次范围。

### 4.4 更新模式的 Step

| Step | 内容 | 性质 |
|---|---|---|
| U0 | **确认本次是人显式发起的**。本 skill 不提供任何「顺便检查有没有新版」的入口：不扫全表、不批量更新、不因为接入了别的条目就连带检查已有条目 | 前置 |
| U1 | 从台账读该条目当前 sha 与 `ref`，并与 `marketplace.json` 条目**逐字比对**。不一致 → **立即终止**，这是上一次更新做了一半的证据，须先人工判明哪一个对应实际验证过的状态（见 § 5.1 第 7 项），再改另一个——不要为了继续往下走而随手对齐 | 前置校验 |
| U2 | `git ls-remote <url>` 一次调用取回全部 ref。**相同则报告「已是最新」并结束**，不做任何写入。失败 → 按 § 4.5 分类，**不重试** | 取值 |
| U3 | **确认 `ref` 本身仍存在**。上游删除或重命名分支时 sha 无从取起，这不是网络故障（见 § 4.4.1） | 判定 |
| U4 | **取上游变更摘要**（见 § 4.4.2）。取不到时**不跳过**，改为在 CHECKPOINT 如实声明「无法取得变更摘要，本次确认是在看不到改了什么的前提下做的」 | 取值 |
| U5 | 🔴 **CHECKPOINT**：旧 sha → 新 sha、变更摘要（或其缺失声明）、上游是否新增了 `scripts` / `hooks` / `.mcp.json` / 依赖、License 是否变化 | 人在回路 |
| U6 | **写入**：改 `sha`（必要时同改 `ref`）；拷贝模式则重新拷贝 + 更新 `UPSTREAM.md` + 按 § 3.4 调整 version。**写入前记下旧值**，回滚要用 | 产出 |
| U7 | **验证**（同 Step 6）。不通过 → 按 § 4.5「写入后失败」**回滚到旧 sha** | 验收 |
| U8 | 记台账更新历史（`成功` / `失败（写入前）` / `已回滚` 三种结果都必须留行，`已是最新` 按需）；同步「已接入」行的 sha（不同步就会被第 7 项拦住）；核实自动更新仍关闭（见 § 4.4.3）；交 `commit-cc-plugin` 提交 | 收尾 |

⚠️ **U6 在 U7 之前，这个顺序无法调换**——安装验证需要条目已经存在才能进行。因此「验证失败」必然发生在已经改了 sha 之后，**回滚是必经动作而不是异常分支**。§ 4.5 把这一点单列成格，就是因为「旧 sha 原样保留」在这条路径上是假的。

#### 4.4.1 `ref` 变更的处置

更新模式不只处理 sha。上游改默认分支、把分支换成 tag、或删掉旧分支时，`ref` 必须跟着改，而**非 `main` 的 `ref` 是常态**（graphify 用 `v8`，darwin-skill 用 `master`）。

| 探到什么 | 处置 |
|---|---|
| `ref` 仍在，sha 变了 | 常规路径，U4 起照走 |
| `ref` 不在了，但能在 `ls-remote` 输出里认出改名后的对应 ref | 在 CHECKPOINT 里**把 `ref` 变更单独列为一项待确认**，不与 sha 更新混为一谈。确认后同改两个字段 |
| `ref` 不在了，且认不出对应物 | **不猜**。终止，台账记「上游 ref 已消失，待人工重新选定」 |

`ref` 变更必须走完整 CHECKPOINT：从 `main` 换到某个 tag 可能意味着上游改了发布策略，也可能意味着我们锁到了一条不再维护的线。

#### 4.4.2 变更摘要怎么取——以及取不到时怎么办

链接模式在本仓**没有上游的本地 clone**，`git ls-remote` 只返回 ref 与 sha、不返回 log。所以「展示上游变更摘要」需要显式给出取法，否则这一步在实操上是空的：

| 手段 | 适用 | 代价 |
|---|---|---|
| GitHub compare API（`/repos/{o}/{r}/compare/{old}...{new}`） | 上游在 GitHub | 绑定 GitHub、需联网、有速率限制 |
| 临时浅克隆后 `git log --oneline old..new` | 任意 git 主机 | 要落盘，须按 `skill-conventions.md` § 6 写明作用域与归还路径 |
| 无 | 非 GitHub 主机且不便克隆 | 摘要缺失 |

首选 compare API（本仓两个首批条目都在 GitHub，且不落盘）。退到临时克隆时：**克隆到系统临时目录、只做 `--filter=blob:none` 浅克隆、用完即删**，禁止落在仓库工作区内（会污染 `git status` 并可能被误提交）。

**取不到摘要不是终止条件，但也绝不是静默跳过。** CHECKPOINT 必须显式声明缺失，让人知道自己正在盲签。把「取不到就跳过确认」写进流程，等于在最需要人看的那一次把人绕开了。

#### 4.4.3 「不重试」不能只靠默认值

§ 2.2 的三层里，第 2 层（第三方与本地 marketplace 默认关闭 auto-update）是**默认值，不是不可变事实**：

- 用户可能在 `/plugin` → Marketplaces 里手动开过该 marketplace 的自动更新；
- `FORCE_AUTOUPDATE_PLUGINS=1` 会强制插件自动更新，且**它不受 `DISABLE_AUTOUPDATER` 约束**（后者管的是 Claude Code 自身的更新器）。

因此 U8 要**核实一次实际状态**而不是断言默认值成立，并在发现被开启时报告给人（不擅自改用户的全局设置）。相关排查项一并写进 `known-issues.md`：`CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` 可让后台 pull 失败时保留既有 clone，避免一次网络抖动把已装好的插件弄没。

### 4.5 失败处理

原先的「三分」不成立：它把「更新失败」当成一格，而写入前失败与写入后失败的处置**方向相反**（一个是什么都别动，一个是必须动手撤回）。改为四格：

| 失败位置 | 处置 | 台账 |
|---|---|---|
| 接入的探测 / 取 sha 阶段 | 终止，不留任何残留写入 | 排除或不记（未接入过） |
| 接入的写入后验证不通过 | 回滚本次写入（条目、目录、版本号一并撤） | 不留已接入行 |
| **更新的写入前失败**（U1–U5） | **一次失败即停**。旧 sha 与 `ref` 原样保留——什么都还没改 | 更新历史留一行「失败」，含原因与时间 |
| **更新的写入后失败**（U7 验证不通过） | **把 `sha`（及 `ref`）回滚到 U6 记下的旧值**；拷贝模式一并撤回目录与 version。回滚后**再跑一次验证**确认已恢复到可用状态 | 更新历史留一行「已回滚」，写明失败原因与回滚到的 sha |

三条共同的硬规则：**不重试、不排定时任务、不自动改 sha**。

#### 4.5.1 更新失败要分类，否则「不重试」会被人的记忆变成轮询

「更新失败」不是一种情况。分类的目的不是分类学，而是**避免对已经永久失效的上游一次又一次地重来**：

| 类别 | 判据 | 处置 |
|---|---|---|
| **临时不可达** | `ls-remote` 网络层报错、超时、鉴权临时失败 | 停。旧 sha 可用，不影响任何人。台账记「临时失败」，下次人想更新时正常重试 |
| **上游仓库已消失** | 仓库 404 / 已删除 / 已转为私有 | 停，并在台账「已接入」行**标记状态为「上游失联」**。这是链接模式最严重的失效形态：条目还在、装不上新的、也拉不到旧的 |
| **`ref` 已消失** | 仓库可达但目标 ref 不在（§ 4.4.1 第三行） | 停，台账记「ref 已消失，待重新选定」 |
| **安装验证失败** | 新 sha 拉下来了但 skill 装不上 / 列不出 | 按上表第四格回滚，台账记「已回滚」并写明现象 |

「上游失联」必须落成**状态标记**而不是一行历史记录。区别在于：历史记录只有翻台账的人会看到，状态标记会让下一次更新在 U1 就知道「这个条目已经不用再试了」。**没有这个标记，每次更新都会把同一个已死的仓库重新试一遍——这就是「持续重试」，只不过轮询周期从定时器变成了人的记忆。**

⚠️ 「临时不可达」与「上游失联」不可合并：前者下次照常重试是对的，后者下次照常重试是纯粹的浪费。而两者的表层现象（拉不到）完全相同，只能靠判据区分。

#### 4.5.2 失败记进哪一份文件

| 现象 | 落点 |
|---|---|
| 上游侧的事（不可达、仓库消失、ref 消失、上游内容变了导致装不上） | `registry.md` 的更新历史 / 状态标记 |
| 本 skill 自己的表现缺陷（探测判错形态、回滚没撤干净、CHECKPOINT 少展示一项） | `known-issues.md` |

划界的判据是**谁该被改**：上游的事改不了，只能记录并决定是否继续引用；本 skill 的缺陷是要修的。两者混在一份文件里，会让真正待修的项被一堆「上游那天挂了」淹没。

§ 2.2 的三层让 harness 根本不发起拉取，§ 4.5 则规定**人工触发的那一次失败也不升级为循环**。两者缺一不可——只有前者时，人可能自己写个循环重试；只有后者时，后台仍在拉。

## 5. 配对传感器：`check_external_entries.py`

引导器写完条目就退场，条目写歪只能靠人发现。落在 `.githooks/`，挂 `pre-commit` 作为第 3 项，现有第 3 项（`.claude/skills` 符号链接镜像）顺延为第 4 项；配套 `.githooks/test_check_external_entries.py` 单元测试。

放 `.githooks/` 而非 skill 内，理由与既有 hook 门禁一致：**Codex 侧走标准 git 读不到 skill 正文**，写在 skill 里的检查在 Codex 下完全不生效。

### 5.1 检查项

扫描范围：`.claude-plugin/marketplace.json` 的 `plugins` 数组中**所有 source 为对象的条目**（本地相对路径字符串的条目不适用本检查）。

| # | 检查 | 为什么它是刹车而不是装饰 |
|---|---|---|
| 1 | 必有 `source.sha`，且为 40 位十六进制 | 漏 sha = 退回「跟随分支最新」，§ 2.2 第 1 层当场失效 |
| 2 | 条目内**不得**出现 `version` | 写了就覆盖 SHA 的更新信号；官方明确会静默忽略 marketplace 条目的 version |
| 3 | `strict: false` 时必须有非空 `skills` 数组 | 缺数组时外部仓无 `plugin.json` → 整条加载失败 |
| 4 | `source.source` ∈ `url` / `github` / `git-subdir`；`git-subdir` 必须带 `path` | 字段名写成 `subdir` 是已知易错（上游 ppt-master 的文档即如此表述） |
| 5 | `description` / `homepage` / `author` 齐备 | 官方 243/243 都有 `homepage`；缺失则来源不可追 |
| 6 | 每条外部条目在 `.claude/skills/add-external-skill/registry.md` 有对应记录 | 只做名称的存在性匹配，防「接进来但没人知道为什么」 |
| 7 | 台账「已接入」行的 sha 与该条目的 `source.sha` **逐字一致** | 抓「更新做了一半」：条目改了台账没改、或回滚了台账没回滚。见下 |

**第 7 项是要求「严格把关更新失败」在传感器侧的落点。** 第 6 项只匹配名称，于是最危险的中间状态完全无人发现：

- U6 改了条目但 U8 没记台账 → 台账里的 sha 是旧的，下次更新的 U1 会从错误的起点算变更；
- U7 失败后回滚了条目但台账已经记了新 sha → 台账在撒谎，且撒的是「我们已经在新版上了」这种谎。

两种都**可机械判定**（两个字符串比对，不需联网），因此没有理由留给人去发现。这一项也是 § 4.4 U1「不一致就立即终止」的前置保障——U1 是运行时检查，第 7 项是提交时检查，同一条不变式的两道关。

另加一项（第 8 项）针对拷贝模式：**`external_plugins/*/` 必须有 `UPSTREAM.md` 且含一行 40 位 SHA**。该目录不存在时视为通过（保持幂等）。

### 5.2 刻意不检查什么

沿用 `check_hook_configs.py` 已确立的原则：**宁可漏报也不误报**。

| 不检查 | 原因 |
|---|---|
| `sha` 是否真实存在于上游 | 需联网。提交门禁联网会让离线提交失败，代价大于收益 |
| 上游是否已有新 commit | 需联网，且这正是 § 2.2 要避免的「主动去查」 |
| `skills` 数组里的路径是否真实存在 | 需联网 |
| `category` 是否在某个枚举内 | 官方未定义封闭枚举，校验会误报 |
| 条目描述是否准确反映上游内容 | 语义判断，机械不可判定 |
| 「上游失联」状态标记是否与上游真实状态相符 | 需联网。该标记由 § 4.5.1 在更新时写入，传感器只保证格式不保证时效 |

**能力边界**：本传感器保证条目的**结构合规与来源可追**，不保证条目指向的内容真的存在、真的是 skill、或真的还在维护。后者仍依赖 Step 6 的实际安装验证与人。

## 6. 台账：`registry.md`

落在 `.claude/skills/add-external-skill/registry.md`，与该 skill 的 `known-issues.md` 同处一地。三类行：

**① 已接入**——条目名、方式（链接/拷贝）、上游 URL、`ref`、当前 `sha`、接入日期、命中的形态分支、**状态**。

「状态」列取三值，缺省为 `正常`：

| 状态 | 含义 | 对下次更新的影响 |
|---|---|---|
| `正常` | 已验证可用 | 照常更新 |
| `上游失联` | § 4.5.1 第二类，仓库 404 / 已删 / 转私有 | **U1 即报告并停**，不再去试。要恢复须人工重新确认上游 |
| `ref 待选定` | § 4.4.1 第三行，仓库在但目标 ref 认不出对应物 | 同上，须人工先定新 `ref` |

后两个状态的存在理由见 § 4.5.1：**没有状态列，「不重试」只能靠人记得哪个已经死了。**

⚠️ 这一列的 sha 与 `marketplace.json` 条目的 `source.sha` 必须逐字一致，由传感器第 7 项在提交时强制。

⚠️ **「已接入」表前必须有机器可读锚点 `<!-- registry:active -->`。** 传感器只解析锚点到下一个 Markdown 标题之间的行——「更新历史」行的首列同样是条目名、且一行里有旧新两个 sha，不隔开会让 sha 比对失效。用锚点而不是章节标题的措辞定位，是因为措辞会被改。**锚点缺失本身要报错，不得静默跳过**：静默跳过会让第 7 项整体失效而没人知道。

**② 已排除**——必须区分两个子类，因为**复议条件不同**：

| 子类 | 含义 | 复议条件 |
|---|---|---|
| **形态不适用** | 技术判定，命中 § 4.3 第五行 | 上游改变形态（提供 `SKILL.md` 或 `plugin.json`）后可复议 |
| **决策暂缓** | 人的决定，与技术形态无关 | 决定改变即可复议，无需等上游 |

首批两条记录：graphify → 形态不适用；darwin-skill → 决策暂缓。

**③ 更新历史**——条目名、旧 sha → 新 sha、日期、结果。**结果取四值**：`成功` / `失败（写入前）` / `已回滚（写入后验证失败）` / `已是最新`。

**失败与回滚的那次也必须留行**（§ 4.5），否则「失败即停」会退化为「失败即忘」，下次仍从头试一遍同样的失败。`已回滚` 行要写明回滚到的 sha——它是「当前生效的 sha 为什么不是最新」这个问题的唯一答案来源。

`已是最新`（U2 判定相同 sha）是否留行按需，不强制：它不改变任何状态，留行的价值只在于记录「我们那天确实查过」。

台账放 skill 内而非 `docs/`：它是这个 skill 自己的维护台账，与 `known-issues.md` 同族；且被传感器第 6、7 项按名称与 sha 双向匹配，与 skill 强绑定。

## 7. 本仓改动清单

| 目标 | 改什么 |
|---|---|
| `AGENTS.md` 触发矩阵 | 补两行：`external_plugins/*/` 内任一文件 → 两份 `plugin.json` ✅、顶层 ❌；新增拷贝插件 → 顶层 Minor 且**起始 version = 上游版本**（§ 3.4 的例外）。并说明「新插件起 `1.0.0`」对链接模式不适用（它没有 `plugin.json`） |
| `AGENTS.md` 关键文件表 | 登记 `.githooks/check_external_entries.py` |
| `AGENTS.md` 提交与推送一节 | pre-commit 的检查项描述加第 3 项 |
| `.githooks/check_external_entries.py` | 新建，§ 5.1 的 7 项 + `UPSTREAM.md` 一项，共 8 项 |
| `.githooks/test_check_external_entries.py` | 新建，双向覆盖 |
| `.githooks/pre-commit` | 插入第 3 项，原第 3 项（符号链接镜像）顺延为第 4 项 |
| `.githooks/check_plugin_versions.py` | `check_all()`（`:91`）扩到 `external_plugins/`；该目录不存在时视为通过 |
| `.githooks/README.md` | 记一条新检查的由来 |
| 镜像 | `.kiro/skills/add-external-skill`、`.agents/skills/add-external-skill` 两个符号链接（不补会被 pre-commit 拦） |
| `.claude-plugin/marketplace.json` | 补齐 `cangjie-skill` 缺失的 `homepage` / `author` / `category`（见下）；新增 archify、ppt-master 两条；顶层 version 升 Minor |
| `docs/todo-list/2026-09-08-todo.md` | 勾掉「将外部skill加入本库」 |

**不改** `.claude/rules/skill-conventions.md`：新建 skill 自动适用持续优化约定，「当前试点范围」那份清单是给存量回填用的。

**不改** `AGENTS.md` 的 darwin-skill 评分门禁一节：darwin 未引入，该节表述仍然成立。

**为什么补 `cangjie-skill` 的三个字段不算「顺手改进」**：传感器第 5 项机械上无法区分新旧条目，上线即会拦住存量条目。补齐是传感器上线的**必要代价**，不是范围外的顺手整理。提交信息里须写明这一归因。

## 8. 首批落地

两个目标，均走链接。它们分别命中 § 4.3 的两个不同分支，覆盖优于三个同型目标。

**archify** —— 命中「skill 在子目录、无 `plugin.json`」：

```jsonc
{
  "name": "archify",
  "description": "…（注明外部引入 + 上游 + License）",
  "source": { "source": "url", "url": "https://github.com/tt-a1i/archify.git",
              "ref": "main", "sha": "<实施时用 git ls-remote 取>" },
  "strict": false,
  "skills": ["./archify"],
  "author": { "name": "tt-a1i" },
  "homepage": "https://github.com/tt-a1i/archify",
  "category": "development"
}
```

**ppt-master** —— 命中「有 `.claude-plugin/plugin.json`」：

```jsonc
{
  "name": "ppt-master",
  "source": { "source": "git-subdir", "url": "https://github.com/hugohe3/ppt-master.git",
              "path": "skills", "ref": "main", "sha": "<实施时用 git ls-remote 取>" },
  "author": { "name": "hugohe3" },
  "homepage": "https://github.com/hugohe3/ppt-master",
  "category": "productivity"
}
```

**实施时必须先确认的两件事**（本 spec 阶段未取证到位，不得假定）：

1. **`hugohe3/ppt-master` 的 `skills/.claude-plugin/` 里确实是 `plugin.json`**。已确认该目录存在，也已确认上游自己的 marketplace 条目用 `git-subdir` + `path: skills` 且**未**写 `strict:false`——这强烈暗示 `plugin.json` 存在，但未直接列出该文件。若实际不存在，该条目要退回「无 `plugin.json`」分支，补 `strict:false` + `skills:["./ppt-master"]`。
2. **ppt-master 需要安装 `requirements.txt` 才能跑后处理脚本**（上游 marketplace 条目的 setup 说明）。这属于 Step 4 CHECKPOINT「会带进来什么」必须展示的内容。

**交付顺序（这是硬约束，见 § 9 第 11 项）**：先写完 skill 与传感器 → 用 skill 自己接入 archify → 再用它接入 ppt-master。手工写完条目再补一份 SKILL.md，等于这个 skill 从未被验证过。

## 9. 验收标准

| # | 标准 | 怎么验 |
|---|---|---|
| 1 | frontmatter 合规，`metadata.version` = `1.0.0`；`known-issues.md` / `CHANGELOG.md` / `test-prompts.json` 齐备 | 读文件 |
| 2 | 两处镜像以 `120000` 模式入库 | `git ls-files -s .kiro/skills .agents/skills` |
| 3 | 传感器对当前仓库通过（含补齐后的 cangjie 条目与两条新条目） | `python .githooks/check_external_entries.py .` 退出 0 |
| 4 | 传感器能抓到全部 8 类问题 | 单测双向覆盖：应通过 + 应阻断两侧 |
| 5 | `check_plugin_versions.py` 扩范围后对当前仓库仍通过，`external_plugins/` 不存在时视为通过 | 跑它 + 补一例单测 |
| 6 | `pre-commit` 四项全过 | `bash .githooks/pre-commit` 退出 0 |
| 7 | 两个链接条目可装、skill 可列出 | `claude plugin marketplace update` + `install` |
| 8 | 两条 sha 均 40 位且与 `git ls-remote` 结果逐字一致 | 逐条比对 |
| 9 | 台账三类行齐备：**3 条已接入**（存量 `cangjie-skill` + archify + ppt-master，均带 `状态` 列）+ 2 条已排除（graphify 形态不适用、darwin-skill 决策暂缓）+ 更新历史表头 | 读 `registry.md` |
| 10 | 拷贝分支的未验证状态写在明面上 | SKILL.md 内有该声明，且 `known-issues.md` 有对应条目 |
| **11** | **至少一个接入是用 skill 自己跑出来的** | 提交历史能体现：skill 先落地，条目后落地 |
| **12** | **`disable-model-invocation: true` 已带，且正文写明该字段解决什么问题 + 三点连带影响**（§ 4.1） | 读 SKILL.md frontmatter 与正文 |
| **13** | **Codex 侧对该字段的实际行为已实测并记入 `known-issues.md`**（忽略 / 硬报错） | 在 Codex 中触发一次同名 skill |
| **14** | **SKILL.md 的更新一节完整落 § 4.4 的 U0–U8、§ 4.4.1–4.4.3、§ 4.5 四格与 § 4.5.1 四类**，且写入后失败明确要求回滚 sha | 逐条比对 spec |
| **15** | **`test-prompts.json` 覆盖更新失败的两种形态**：写入后验证失败要回滚、上游仓库消失要标状态且不再试 | 读用例 |

**版本号裁决**：本次改动落在 `.claude/`（新 skill）、`.githooks/`、`docs/` 与 `.claude-plugin/marketplace.json`。按 `AGENTS.md` 矩阵——`.claude/` 与 `docs/` 一律不升任何版本号；**唯一要升的是 marketplace 顶层 Minor**（新增 2 条插件条目，先例 `4d741b8`）。没有任何插件的 `plugin.json` 被触及，故两份同值规则本次不涉及。

⚠️ **矩阵里没有 `.githooks/` 这一行**。本 spec 判定它不升任何版本号，依据是矩阵自己的核心规则「改动物理上落在哪个分发单元内，就升那个单元的版本号」——`.githooks/` 不属于任何分发单元，harness 读不到。

**这是推导，没有先例支撑**：已核查 `f994c09` 虽改了 `.githooks/` 且升了 4 份 `plugin.json`，但它同时改了 `plugins/*/hooks/` 下的脚本与配置，升版可完整归因于后者，无法作为 `.githooks/` 单独触发升版的证据；仓库历史中**不存在只改 `.githooks/` 的提交**。plan 阶段可考虑顺便给矩阵补这一行以消除歧义，但不是本次的必要项。

**darwin-skill 评分门禁不适用于本次**：门禁只在 Minor/Major 升级前要求对**改动的 skill** 评分。本次是**新建** skill，无「改动前分数」可比。按 `skill-conventions.md` 的持续优化约定，新建后应做一次基线评估——该评估不构成本次提交的阻塞项。

## 10. 已知遗留

1. **拷贝分支零用例**。首批两个目标都走链接，`external_plugins/` 目录不会被创建。该分支只写判据与落位规范，实际步骤标注为「首次使用时按 § 3.3/§ 3.4 展开，并在该次提交内补齐 `test-prompts.json` 用例」。这是**已知的未验证状态**，不假装已完成。
2. **`check_plugin_versions.py` 扩范围后暂无真实被测对象**。`external_plugins/` 不存在时视为通过，所以这次扩范围只有单测能覆盖。先就位是为了让第一次拷贝不落进盲区。
3. **darwin-skill 与 graphify 的复议未排期**。两者的复议条件已写入台账（§ 6），但没有触发机制——需要人主动想起。刻意不加提醒机制：为两个已明确暂缓的候选建轮询是过度设计。
4. **传感器不校验上游可达性与时效性**（§ 5.2）。「条目结构完美但上游仓库已删除」这一形态本传感器抓不到，只能由 Step 6 的实际安装暴露。
5. **`cangjie-skill` 的 `description` 未复核**。本次只补三个缺失字段，不重写既有 description。
6. **`disable-model-invocation` 在 Codex 侧的行为未实测**（§ 4.1 第 3 点）。风险是该 skill 在 Codex 侧整体加载失败而非降级告警。验收第 13 项要求实测，但**若实测结果是硬报错，本次设计需要重新裁决**（保字段舍 Codex 镜像，或保镜像改用别的方式约束触发）——该分支的处置不在本 spec 范围内。
7. **变更摘要在非 GitHub 主机上无成熟取法**（§ 4.4.2 第三行）。首批两个目标都在 GitHub，所以这条不影响本次；第一次引入非 GitHub 上游时，要么实现临时浅克隆分支，要么接受盲签并让 CHECKPOINT 如实声明。
8. **「上游失联」状态需人工解除**。§ 4.5.1 刻意不提供自动复检——自动复检就是轮询。代价是上游恢复后我们不会知道，须人主动重试。
