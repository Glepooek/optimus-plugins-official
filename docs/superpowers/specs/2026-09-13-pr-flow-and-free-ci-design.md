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

因此拆成两层，二者不是替代关系而是**同一传感器的静态层与行为层**：

| 层 | 手段 | 触发 | 成本 | 查什么 |
|---|---|---|---|---|
| 静态闸 | `claude plugin validate --strict` + 既有门禁与单测 | 每个 PR，必需检查 | **零 token** | schema 合法性、仓库一致性 |
| 行为闸 | `claude plugin eval` | `workflow_dispatch` 手动 | 按 case 计费 | skill 是否真能被正确触发 |

## 2. 非目标

- **不建 eval 套件本体**。本 spec 只铺好手动触发的 workflow 入口与目录约定；`evals/` 下的 case 与 grader 是独立工作项，不在本次交付内。理由：eval case 的质量取决于对每个 skill 触发语境的逐一设计，与 CI 管道是两件事，混在一起会让本次交付无法收敛。
- **不追溯存量 51 个 skill**。用户已拍板「新增必须带 case，存量不回溯」。
- **不改 `03-pull-requests.md:26`**（`release/*` 保护的 SHOULD 条款）——本仓无 release 分支，该条款空转但无害。
- **不引入 `gh` CLI**。日常 PR 流程用 GitHub MCP 已有工具即可闭环（见 § 3.2），装 `gh` 只为一次性配置不值得引入新依赖。
- **不改 `.githooks/pre-commit` 的检查内容**。它继续在本地拦截，CI 只是把同一批脚本在另一个环境再跑一次；两者共用脚本、不分叉。

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
- **第 5 条 ⇒ 这一项可以无条件作必需检查。** 不需要 secret，因此 fork PR 也能跑通（fork PR 拿不到仓库 secret，任何依赖凭据的检查都会在 fork 场景失败）。
- **第 7 条 ⇒ CI 需要两类调用**：每个插件根各一次（清单），每个 `plugins/*/skills` 各一次（组件）。只跑一类会漏掉另一类。
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
| **主干已存在一个 active ruleset**（名 `main`、id `23134670`、`2026-09-13T05:02:49Z` 创建） | § 4 从「新建保护」改为「修订现有 ruleset」；完整配置与冲突见 § 4.1 |
| 当前账号在该 ruleset 的 **bypass 名单内** | 直推 `master` 仍成功，服务端只回 `Bypassed rule violations`——规则存在但对唯一使用者无效 |
| 本机**零提交签名配置** | `user.signingkey`/`gpg.format`/`commit.gpgsign` 均未设，最近 5 个提交 `git log --format=%G?` 全为 `N` |

## 4. 主干保护配置规格（修订现有 ruleset，人工执行）

### 4.1 现状取证：ruleset 已存在，但当前形态不可满足

主干上已有一个 active ruleset，名 `main`、id `23134670`、创建于 `2026-09-13T05:02:49Z`。**本节的原始设计是「从零新建」，取证后改为「修订现有」**——两者的差别不只是措辞：现有配置里有三项若照原样移出 bypass 名单会立即锁死主干。

发现方式值得记录：一次常规的 `git push origin master` 成功了，但服务端回了

```
remote: Bypassed rule violations for refs/heads/master:
remote: - Changes must be made through a pull request.
remote: - Commits must have verified signatures.
remote:   Found 1 violation: efeb3b49...
```

`Bypassed` 不是错误而是通告：规则命中了，因当前账号在 bypass 名单内而放行。**没有这一行，这个 ruleset 会长期给人「主干已受保护」的错觉，而实际上唯一会推它的人恰好豁免——保护的有效范围与实际使用者的交集是空集。**

现有配置（读自 `GET /repos/{owner}/{repo}/rulesets/23134670`，公开仓库无需认证）与本 spec 规格的逐项对照：

| 规则 | 现状 | 目标 | 判定 |
|---|---|---|---|
| `conditions.ref_name.include` | `~DEFAULT_BRANCH` | 不变 | ✓ 等价于 `master` |
| `deletion` | 有 | 保留 | ✓ |
| `non_fast_forward` | 有 | 保留 | ✓ 即「禁 force push」 |
| `pull_request` | 有 | 保留 | ✓ 本次裁决的核心 |
| └ `required_approving_review_count` | **1** | **0** | 🔴 见 § 4.2 |
| └ `require_extra_approval_for_unattributed_changes` | **true** | **false** | 🔴 见 § 4.2 |
| └ `allowed_merge_methods` | `merge`/`squash`/`rebase` | **仅 `squash`** | ⚠️ 收窄以配合线性历史 |
| `required_signatures` | **已删除** ✅ | 删除 | ✓ 用户已按 § 4.3 裁决执行（`updated_at` 05:09:52） |
| `copilot_code_review` | 有（`review_on_push: true`） | 保留 | ✓ 免费的额外一层，**且不阻塞合并**——它不计入 approval，所以既帮不上 `count:1` 也拦不住合并 |
| `required_linear_history` | **缺** | **新增** | ⚠️ `03-pull-requests.md` §2 推荐 squash 保持线性 |
| `required_status_checks` | **缺** | **新增** | 🔴 需求 3 的落点整个缺失，CI 全绿无法强制 |
| bypass 名单 | **含当前账号** | **清空** | 🔴 见 § 4.2 |

### 4.2 三项致命冲突

**其一：合并条件当前不可满足。** `required_approving_review_count: 1` 叠加四个事实——GitHub 不允许 PR 作者批准自己的 PR、个人账号无 team reviewer、Copilot review 不计入 approval、`require_extra_approval_for_unattributed_changes: true` 还要再加一票。单人仓库里这组条件凑不出所需批准数。**一旦移出 bypass 名单，主干将既不能直推、也不能通过 PR 合并**——这不是配置得严，而是配置得不可满足。

处置：`required_approving_review_count` 改 **0**，`require_extra_approval_for_unattributed_changes` 改 **false**。规范侧的对应改动是 § 7.1 给 `03-pull-requests.md:25` 加作用域限定；两者必须成对做，只改一边会留下「配置与规范互相矛盾」的新版死结。

**其二：bypass 名单必须清空。** 名单里有唯一使用者时，保护的实际作用范围为空。清空后的逃生口改为「把 Enforcement status 临时改为 `Disabled`」——一次显式、留痕、需刻意为之的操作，而不是每次推送时静默绕过。这才满足 `03-pull-requests.md:24` 的「禁止直接推送」：直推必须**真的被拒绝**。

**其三：缺 `required_status_checks` 意味着需求 3 落不了地。** 没有这一项，CI 可以红着而 PR 照样能合。§ 5 设计的三个零 token 检查必须挂进这里才有约束力。

### 4.3 `required_signatures`：删除（用户裁决）

本机零签名配置（`user.signingkey`/`gpg.format`/`commit.gpgsign` 均未设，最近 5 个提交 `%G?` 全为 `N`）。移出 bypass 名单后，未签名提交会被服务端拒绝——**连特性分支的推送都会被拒**，因为该规则作用于向受保护分支推送的 commit 及其合并。

两条路各自的代价已提交用户裁决，**结论：从 ruleset 删除 `required_signatures`**。放弃这条安全边界，换取零配置成本。**该项已执行完毕**（`updated_at` 05:09:52 起该规则不再存在），是本 spec 中唯一已落地的改动。

⚠️ 该裁决同时意味着 spec 不引入任何签名相关约定；若日后要恢复该规则，需先完成 SSH signing 配置（`gpg.format=ssh` + `user.signingkey` + `commit.gpgsign=true` + 在 GitHub 账号加 Signing Key），再改 ruleset，顺序不能颠倒。

### 4.4 修订手段

GitHub MCP 无 ruleset 工具（§ 3.2），`gh` 未安装。两条路：

| 手段 | 说明 |
|---|---|
| **Web UI**（推荐） | 仓库 → Settings → Rules → Rulesets → `main` → 按 § 4.1 目标列逐项改 |
| `curl` + PAT | `PATCH /repos/{owner}/{repo}/rulesets/23134670`，需 PAT 具备仓库 admin 权限 |

建议顺带把 ruleset 改名为 `master-protection`——现名 `main` 会让人以为它作用于 `main` 分支，而本仓不存在该分支（实际 target 是 `~DEFAULT_BRANCH` 即 `master`）。这是可选的清理项，不影响功能。

### 4.5 ⚠️ 实施顺序的硬约束

**bypass 名单最后清空。** 清空后 `git push origin master` 立即被拒绝，而 `commit-cc-plugin` 第五步当前正是直推 master——若先清空，下一次提交就会卡死在一个还没改好的 skill 上。

正确顺序：

1. CI workflow 落地
2. 开一个真实 PR 触发 CI —— **必需检查项必须先在 GitHub 上跑过至少一次，名字才会出现在 ruleset 的可选列表里**
3. 改 `commit-cc-plugin` 与 `AGENTS.md`
4. 改知识库条款（§ 7.1 / § 7.2，走 `knowledge-base-maintain`）
5. 修订 ruleset：删 `required_signatures`、approval 数改 0、补 `required_status_checks` 与 `required_linear_history`、收窄 merge 方法
6. **最后**清空 bypass 名单

⚠️ 第 2 步与第 5 步之间有真实的依赖：没跑过的 job 名选不上。而第 1 步的 PR 本身要在 bypass 名单还在、或 approval 数已改 0 的前提下才能合并——**建议第 5 步的「approval 数改 0」提前到第 2 步之前单独做**，这样第 2 步的 PR 就能正常合并，不必依赖 bypass。


## 5. CI 设计

### 5.1 总体：三个零 token 的必需检查 + 一个手动的行为检查

新建 `.github/`（当前仓库**无此目录**，从零建立）：

| 文件 | job | 触发 | 成本 | 是否必需检查 |
|---|---|---|---|---|
| `.github/workflows/ci.yml` | `gates` | `pull_request` → `master` | 零 | ✅ |
| 同上 | `plugin-validate` | 同上 | 零 | ✅ |
| 同上 | `new-skill-eval-case` | 同上 | 零 | ✅ |
| `.github/workflows/skill-eval.yml` | `eval` | **仅 `workflow_dispatch`** | 按 case 计费 | ❌ |

### 5.2 job `gates` —— 逐字执行 `.githooks/pre-commit`，不复制逻辑

**关键取证：`.githooks/pre-commit` 全程未使用 `git diff --cached`**，它的六项检查全部基于工作树与 `git ls-files`，与暂存区无关。因此 CI 可以直接 `sh .githooks/pre-commit`，而不是在 workflow YAML 里重写一份门禁逻辑。

这一步同时补上了一个长期缺口：`pre-commit` 靠 `git config core.hooksPath .githooks` **本机启用、不随仓库分发**，因此它在任何未做该配置的环境中从未生效过。搬进 CI 后，这批门禁第一次有了不依赖本机配置的执行点。

⚠️ **由此产生一条新约定，必须写进 `.githooks/README.md`**：`pre-commit` 不得引入依赖暂存区的检查（`git diff --cached`、`git diff --name-only --staged` 等）。一旦引入，CI 的逐字复用即失效，门禁判据会在两个环境间分叉。

`gates` 的完整步骤：

| # | 步骤 | 命令 |
|---|---|---|
| 1 | checkout | `actions/checkout@v5` |
| 2 | Python | `actions/setup-python@v6`（`python-version: '3.x'`；提供 `python` 别名，ubuntu 默认只有 `python3`） |
| 3 | 仓库一致性门禁 | `sh .githooks/pre-commit` |
| 4 | 单元测试（**9 个目录各跑一次**） | 见 § 5.3 |
| 5 | 知识库一致性 | `python .claude/skills/knowledge-base-maintain/scripts/check_index.py`<br>`python .claude/skills/knowledge-base-maintain/scripts/check_refs.py` |
| 6 | tips 库一致性 | `python .claude/skills/sync-cc-tips/scripts/validate_tips.py` |

第 5、6 步的当前基线（实测）：索引 790 条无问题、284 个消费者文件章节号引用全部有效、tips 250 条九项检查全通过。**均无存量债务，可直接设为硬失败。**

### 5.3 9 个测试目录必须逐个调用

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

实现上用一个 shell 循环遍历该列表，任一失败即整步失败。**不把目录列表硬编码进 YAML 的九个 step**——那样新增测试目录时容易漏改，且失败时要翻九个折叠块。

### 5.4 job `plugin-validate` —— 官方静态校验

| # | 步骤 | 说明 |
|---|---|---|
| 1 | checkout | — |
| 2 | `actions/setup-node@v6` | Node 22 |
| 3 | `npm i -g @anthropic-ai/claude-code` | 安装 CLI |
| 4 | 全量 `claude plugin validate --strict` | 目标见下表 |

**必须加 `--strict`**（§ 3.1 第 3、4 条：默认档下缺 `description` 只报 warning 且退出 0）。

校验目标（§ 3.1 第 7 条：单个 skill 目录不是合法目标，必须分两类）：

| 目标 | 数量 | 校验什么 |
|---|---|---|
| `.claude-plugin/marketplace.json` | 1 | marketplace 清单 |
| `plugins/*/` | 10 | 每插件 `plugin.json` 清单 |
| `plugins/*/skills/` | 9 | 插件对外发布的 skill 组件 |
| `plugins/*/agents/` | 1 | agent 组件 |
| `.claude/skills/` | 1 | 本仓自用 skill（不发布，但 frontmatter 同样要合法） |

**不校验 `.kiro/skills/` 与 `.agents/skills/`**——它们是指向 `.claude/skills/` 的符号链接，校验等于重复；镜像完整性已由 `pre-commit` 第 4-6 项负责。

**无需任何 secret**（§ 3.1 第 5 条实测：空配置目录、清空 API key 环境变量仍正常退出 0）。这一点决定了它在 fork PR 场景也能跑——fork PR 拿不到仓库 secret，任何依赖凭据的必需检查都会在那里失败。

### 5.5 job `new-skill-eval-case` —— 需求 3 的零成本落地

这是**「新增 skill 必须带 eval case」与「不为 CI 付费」两个约束的交点**：强制 case **存在**（纯静态 diff 检查，零成本），但不在 CI 里**运行** case（避免 token）。

逻辑：

1. `git diff --name-only --diff-filter=A origin/master...HEAD` 取本 PR **新增**的文件
2. 从中筛出形如 `plugins/<plugin>/skills/<skill>/SKILL.md` 的路径
3. 对每个命中项，要求 `evals/<plugin>/<skill>/` 存在且含 `case.yaml` 或 `prompt.md`
4. 无命中项 → 直接通过（**存量不回溯**，用户已拍板）

`--diff-filter=A` 是这里的要点：只看**新增**的 SKILL.md，修改已有 skill 不触发。这正是「新增必须带 case，存量不回溯」的机械表达。

⚠️ 本 spec 不创建任何 eval case（§ 2 非目标）。该 job 上线后处于「无命中即通过」状态，直到下一次真的新增 skill 时才第一次生效——那时它会要求作者补 case。这是刻意的：门禁先于第一个用例存在，才能保证第一个用例不被漏掉。

### 5.6 workflow `skill-eval.yml` —— 手动的行为闸

- 触发：**仅 `workflow_dispatch`**，可选输入 `target`（插件名或 skill 名，留空为全部）
- 需要 `ANTHROPIC_API_KEY` secret
- 不进必需检查列表，不在 PR 上自动运行

保留它的理由：`validate` 查的是 schema 合法性，**查不了行为**——一个 frontmatter 完全合法的 skill 完全可能因 `description` 写得含糊而永不被触发。只有 eval 能发现这件事。把它做成手动入口，是在「这件事只有 eval 查得出」与「每个 PR 都付费不可接受」之间取的位置。

## 6. `commit-cc-plugin` 的改造

### 6.1 建分支必须发生在提交之前

当前流程在 `master` 上提交、然后直推。走 PR 后若沿用「先提交再想办法」，提交已经落在本地 `master` 上，要搬到特性分支就得动 `git reset --hard`——把一个破坏性命令放进日常提交路径是不可接受的。

因此建分支插在**第四步提交之前**，而非第五步。改动落点：

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
| 3 | 等 CI | MCP `pull_request_read`（`method: get_check_runs`） | 轮询至三个必需检查全部结束 |
| 4 | 合并 | MCP `merge_pull_request`（`merge_method: "squash"`） | 见 § 6.5 关于 message 的注意事项 |
| 5 | 回主干 | `git switch master && git pull --rebase origin master` | — |
| 6 | 清分支 | 删本地与远端特性分支 | — |

第 3 步出现失败检查时：**停下报告，不自动重试、不自动改代码**。CI 红说明门禁真的拦到了东西，与 `pre-commit` 阻断时「禁止绕过」的处置同构。

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
4. **新增 skill 必须带 eval case**（`evals/<plugin>/<skill>/`），由 `new-skill-eval-case` job 强制；存量不回溯。

### 7.4 `.githooks/README.md` —— 新增一条约定

CI 逐字执行 `sh .githooks/pre-commit`，因此该脚本**不得引入依赖暂存区的检查**（`git diff --cached` 等）。当前六项检查全部基于工作树与 `git ls-files`，该性质必须被显式记录并保持，否则两个执行点的判据会静默分叉。

同时把 CI 作为第二执行点写进「启用」一节——现在「未启用时 hook 静默不执行」这句话有了限定：本地未启用仍会被 PR 上的 CI 拦住。

## 8. 受影响文件与版本影响

### 8.1 新建

| 文件 | 说明 |
|---|---|
| `.github/workflows/ci.yml` | 三个零 token job（§ 5.2 / 5.4 / 5.5） |
| `.github/workflows/skill-eval.yml` | 手动 eval（§ 5.6） |
| `.githooks/check_new_skill_eval_case.py` | § 5.5 的 diff 检查实现 |
| `.githooks/test_check_new_skill_eval_case.py` | 配套单测 |

**为什么 diff 检查放 `.githooks/` 却不挂进 `pre-commit`：** `.claude/rules/hook-conventions.md` 约定「仓库级门禁必须放 `.githooks/`」，所以脚本位置遵守该约定；但它依赖两个 ref 之间的 diff，而 § 5.2 又要求 `pre-commit` 保持暂存区无关。两者的解法是——脚本接受 base/head 两个 ref 作参数、**只由 CI 调用**，不进 `pre-commit` 的检查序列。目录约定与暂存区无关性因此都不破。

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

### 8.3 版本影响：全部不升

按 `AGENTS.md` 触发矩阵逐项核对：

| 改动落点 | 是否升版本 | 依据 |
|---|---|---|
| `.claude/` 下（`commit-cc-plugin`） | ❌ | 矩阵明列「`.claude/` 下任何文件 → 不升」 |
| `AGENTS.md`、`docs/` | ❌ | 矩阵明列 |
| `.githooks/` | ❌ | 不随插件分发，harness 读不到 |
| `.github/` | ❌ | **矩阵未列此路径**，见下 |
| `knowledge-base/git/` | 领域版本升，插件版本 ❌ | 知识库有独立版本体系 |

⚠️ **矩阵里没有 `.github/` 这一行。** 按矩阵的核心规则「改动物理上落在哪个分发单元内，就升那个单元的版本号」，`.github/` 不在任何插件内、不随插件分发，因此不升任何版本号——但这是**推导结论而非明文**。建议在 § 7.3 改 `AGENTS.md` 时**顺带补上这一行**，把推导变成明文，避免下次重新推导。

**本次交付不改动任何 `plugins/` 下的文件，因此两份 `plugin.json` 均不动**，`pre-commit` 的版本同值检查不受影响。

## 9. 验收标准

每项都要跑到、并留下可核对的输出。**其中两项是阴性对照——只验证「绿」不能证明门禁有效**（§ 3.1 的 `contents: []` 就是这个教训：一个什么都不查的门禁与一个全部通过的门禁，输出无法区分）。

| # | 目标 | 验证 |
|---|---|---|
| 1 | 本地门禁在 Linux 上可跑 | CI 中 `sh .githooks/pre-commit` 退出 0 |
| 2 | 9 个测试目录全绿 | CI 中每个 `unittest discover` 退出 0，累计用例数与本地一致 |
| 3 | 官方静态校验全绿 | CI 中 22 个校验目标（1 marketplace + 10 插件 + 9 skills + 1 agents + 1 `.claude/skills`）`--strict` 全部退出 0 |
| 4 | 知识库与 tips 一致性 | `check_index.py` / `check_refs.py` / `validate_tips.py` 均退出 0 |
| 5 | **阴性对照**：eval case 门禁真的会拦 | 造一个「新增 SKILL.md 但无对应 `evals/` 目录」的 PR，`new-skill-eval-case` **必须红**；补上目录后转绿 |
| 6 | **阴性对照**：主干真的推不上去 | 清空 bypass 名单后 `git push origin master` **必须被服务端拒绝**。⚠️ 判据是「拒绝」而非「有提示」——当前状态下该命令会**成功**并回 `Bypassed rule violations`，把那行提示误当成保护生效正是本次要消除的错觉 |
| 7 | 全自动流程闭环 | 走一次完整 `commit-cc-plugin`：建分支 → push → PR → CI 绿 → squash merge → 回主干；主干 commit 含 `Co-Authored-By`（§ 6.5） |
| 8 | 知识库改动未破坏一致性 | `knowledge-base-maintain` 的一致性校验通过，领域版本与 CHANGELOG 已同步 |
| 9 | 新门禁有测试与文档 | `test_check_new_skill_eval_case.py` 通过；`.githooks/README.md` 已登记 |

## 10. 风险与未决

| # | 风险 | 处置 |
|---|---|---|
| 1 | **CLI 版本漂移**：`npm i -g @anthropic-ai/claude-code` 拉最新版，未来 `validate` 新增 warning 类型会让 `--strict` 突然变红，且与本次改动无关 | workflow 里**固定版本号**，升级作为显式动作。`sync-cc-tips` 每次同步 changelog 时本就在读 CLI 变更，可顺带评估是否升 CI 里的固定版本 |
| 2 | **改 job 名会静默失去保护**：ruleset 的必需检查按名字匹配，改名后 GitHub 不报错，只是那项检查不再被要求 | 属「不报错的失效形态」。job 名写进 `.github/workflows/ci.yml` 顶部注释并在 `AGENTS.md` 登记，改名必须同步改 ruleset |
| 3 | **eval case 格式未定**：`new-skill-eval-case` 只检查目录与文件存在，不校验 case 内容 | 刻意的。case 的 schema 属 eval 套件那次工作，本 spec 只锁目录约定 `evals/<plugin>/<skill>/`。当前门禁处于「无新增 skill 即通过」状态 |
| 4 | **会话中断导致 PR 悬挂** | § 6.4 已述，靠 § 6.2 的接续逻辑兜住 |
| 5 | **Windows 本地与 Linux CI 的行为差异未实测**：符号链接、路径大小写、`git ls-files -s` 的模式位 | `actions/checkout` 保留符号链接为已知行为，但**本仓未实测**。验收第 1 项即是这项的实测；若 `pre-commit` 在 CI 首跑失败，按失败内容判断是脚本假设了 Windows 还是 CI 环境缺配置 |
| 6 | **`.claude/settings.json` 是否纳入版本库** | 遗留未决项，与本 spec 解耦。它当前已被 `git add` 但未提交；本次交付**不处理**，需单独裁决 |
| 7 | 首个 PR 的鸡生蛋问题：必需检查名字要先跑过一次才能选 | § 4.5 已列入实施顺序，并把「approval 数改 0」提前，使首个 PR 不依赖 bypass 即可合并 |
| 8 | **现有 ruleset 由用户在本会话期间手动创建**，其意图未完整记录 | 本 spec § 4.1 已把它的完整配置固化为取证，§ 4.2 / § 4.3 逐项给出改动理由。`required_signatures` 一项已单独交用户裁决（结论：删除），不做替用户推断 |





