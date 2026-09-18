# Changelog

## [6.0.1] - 2026-09-18

darwin baseline 评估（79.4）后针对 d7/d4 的第一轮优化，外加一处在核对数字时撞见的事实性修正（必需检查项数）。**未改动任何命令、参数或判据**——`gh pr checks --required --watch` 等动作逐字不变，改的是可读性、标记语义与被写错的清单。

按 `skill-conventions.md` §7 跑了 `selfcheck.py --skill-dir .claude/skills/commit-cc-plugin`，得 `failed: [checkpoint_count, dangling_refs]`，逐项核对后确认**三处均为检查器的可移植性缺陷、本 skill 正文无需改动**（正则只认 `**CHECKPOINT**` 紧闭形态、标记定义表行被算作落地点、悬空判定不试仓库根 `.githooks/`）。已记入 `known-issues.md`，归 `sync-cc-tips` 自己的优化轮处理——**没有为让校验变绿而改正文**。

### Added
- 新增「三种标记的含义」小节，定义 🔴/⛔/⚠️ 三级：🔴 = 必须停下等用户回答或退出；⛔ = 硬性禁令但**无需问人**；⚠️ = 提示。判据是「**有没有人需要回答问题**」而非重要程度——⛔ 标的往往是不可逆的静默失效，只是正确做法唯一
- 第五步拆出 8 个小标题（前置 / 六个动作 / 动作 2、4 / 动作 3 / 动作 4 / 动作 6 / 不用 --auto / 工作区不干净），最长连续无标题段落从 109 行降到约 25 行
- 动作 2、4 新增「两处文件来源不同」对照表：**squash body 不要手写**，用 `git show -s --format=%b HEAD` 直接从 commit 取，连「会不会手滑转义」的可能性都消除；PR body 因需另加 `🤖 Generated with` 尾注、与 commit 正文不同，仍用 heredoc 手写。该做法源自 6.0.0 首次实战（PR #52）

### Changed
- **第五步内部编号由「第 N 步」改为「动作 N」**，并在节首写明该约定。原先「第 3 步」（第五步内部）与「第四步」（顶层）在同一行内出现，指代无从判断——两判官独立指出该缺陷
- **8 处**非确认型 🔴 降级为 ⛔（多行文本传参、CI 失败停下、合并传参两条、尖括号转义、无法修复、-d 改 -D、清分支顺序）。改前 🔴 出现 16 次、改后 8 次（另 2 次属新增的标记定义表本身），即**改前 16 处里真正需要用户回答的仅 8 处**——符号被复用后真闸口与强调在视觉上无法区分。留下的 8 处是 6 个 CHECKPOINT（L51/60/82/107/218/235）+ 2 个 STOP（L246/247）
- 第一步 CHECKPOINT 删去对主干保护的整段复述（开篇已讲），GH013 由三处降为两处：L16 定义 + 速查表回指
- 「绿灯不等于查过了」补一句实测观察：改动落在 `plugins/` 时 `plugin-validate` 耗时明显更长（PR #52 实测 24s vs skipping）

### Fixed
- **dim8 有效重测完成**（第一轮对照组污染作废后重做）。新设计让**两臂都不读任何文件**、with_skill 由 prompt 内嵌 SKILL.md 摘录，堵住上轮 arm-B 从 `.githooks/README.md` + `ci.yml` + `git log` 重建仓库语境的漏洞。4 份产物交 2 名盲判官按 `test-prompts.json` 的 `expected` 打分，臂别映射由实验者持有。结果：id2 baseline 43.5 vs with_skill 84.5（**Δ+41.0**）、id3 with_skill 84.5 vs baseline 74.0（**Δ+10.5**），dim8 子分 **8.5/10**，`eval_mode: full_test`。⚠️ **本轮未重算 all9 总分**——d7/d4 的结构改动理应影响总分，但那需要完整九维重评，本行只记 dim8
- **必需检查项数由「五项」修正为「六项」**：服务端 ruleset `master-protection` 实测要求 6 个 context（`gh api repos/:owner/:repo/rulesets/23134670`），`actionlint` 已被勾选进去，而文档侧 5 处仍写「五项」。同批修正 `AGENTS.md` 两处、`tools.md` 一处、`.github/workflows/actionlint.yml` 的注释（后者最严重——它**主动断言**「服务端 ruleset 当前也没有它」，该句已成假）。⚠️ **修法不止于把数字改对**：三处都加了「此处是副本、真源是那条 `gh api`」的标注，否则下次勾选新检查时同样漂移。`CHANGELOG`/`known-issues` 里的「五项」属当时事实，按「跟改即伪造记录」保留不动
- `results.tsv` 中 commit-cc-plugin 那行的 `commit` 列由 `pending` 回填为真实 sha `085669a`
- 本轮 Changed 段初稿把降级数写成「12 处」、剩余确认点写成「4 处」，实测为 8 与 8（🔴 出现次数 16 → 10，其中 2 次属新增的标记定义表本身）。数字类声明在写入后逐条复算过

## [6.0.0] - 2026-09-18

### Changed
- **第五步的第 2/3/4 步由 GitHub MCP 全面改为 `gh` CLI**：`create_pull_request` → `gh pr create`、`pull_request_read`（`get_check_runs`）→ `gh pr checks --required --watch --fail-fast`、`merge_pull_request` → `gh pr merge --squash`。第一步 CHECKPOINT 查已有 PR 由 `list_pull_requests` 改为 `gh pr list --head <branch> --state open`
- `compatibility` 由「需 github MCP server（本仓库 `plugins/optimus-mcp-servers/.mcp.json` 内置）」改为「需 GitHub CLI（`gh`，已通过 `gh auth status` 认证）；不依赖任何 MCP server」；`allowed-tools` 由 `Bash github` 收回为 `Bash`。这是 Major 的依据——运行依赖变了，装了本 skill 但没装 `gh` 的环境会直接卡在第五步
- 「这是 auto-merge 的等效实现」节改写为「不用 `gh pr merge --auto`」：`gh` 本身支持原生 auto-merge，旧节「MCP 未提供对应工具」的前提已不成立。**新的不采用理由是本仓库 `allow_auto_merge: false`**（2026-09-18 `gh api repos/... --jq .allow_auto_merge` 实测），传 `--auto` 会被服务端拒绝。同时写明打开该开关属仓库配置变更、不在本 skill 职责内
- 三个静默失效形态的载体随之改写：`commit_message` → `--body-file`、`commit_title` → `--subject`；尖括号那条的成因从「传 JSON 参数时转义」改为「手工拼串或从网页复制时转义」——走 `<<'EOF'` heredoc 写文件不会产生该转义

### Added
- 第五步开头新增 🔴 **CHECKPOINT「`gh` 可用性」**：跑 `gh auth status`，未安装与未登录分列两种 STOP 处置（均不代为安装或代跑交互式登录）。**刻意排在第 1 步 `git push` 之后**——git 凭据与 `gh` 认证是两套，前者能成功不代表后者可用
- 第 2/4 步新增 🔴「多行文本一律走 `--body-file`，不用 `--body`」，配 `<<'EOF'` heredoc 示例并说明引号必须有（否则 `$`、反引号、`<` `>` 会被 shell 解释）。这是 CLI 路径**新引入**的失效面，MCP 传 JSON 参数时不存在
- 第 3 步新增 `gh pr checks` 的退出码判据表（0 全绿 / 8 pending / 4 需认证 / 1 有失败），并写明「判据是退出码，不要读人类可读输出」。8 来自 `gh pr checks --help` 的 Additional exit codes，4 来自 `gh help exit-codes`（2026-09-18 实测 gh 2.101.0）
- 第 3 步新增 ⚠️ **必须带 `--required`**：不加会把非必需检查一并计入，可选 job 变红即误判为 CI 失败
- 失败时的取证路径：`gh pr checks --required --json name,bucket,link` 定位失败项 + `gh run view <run-id> --log-failed` 读日志。用 `bucket` 而非裸 `state`——它把各种 state 归并成 pass/fail/pending/skipping/cancel 五类，少一层映射
- 常见错误表新增 2 条（`gh pr checks` 漏 `--required`、读人类可读输出而非退出码），另 4 条随手段变更改写

### Removed
- 常见错误表删除「用 `get_status` 轮询 CI」一条：`get_status` / `get_check_runs` 是 MCP `pull_request_read` 的 `method` 取值，`gh pr checks` 无对应参数，该误用形态在 CLI 路径下不存在。原始案例仍保留在 `known-issues.md`

## [5.0.0] - 2026-09-13

### Removed
- **第五步「同步推送」整节移除**（含 `git pull --rebase origin master` + `git push origin master`、三种失败处置表）：主干已由服务端 ruleset 强制只能经 PR 合入，直推被 `GH013` 拒绝，该节描述的动作**物理上已不可执行**。这是 Major 的依据——skill 的终点动作变了，用户说「提交」不再得到「已推上 master」而是「PR 已 squash merge」

### Added
- **第五步重写为六个动作**：推特性分支 → MCP `create_pull_request` → MCP `pull_request_read`（`get_check_runs`）轮询五项必需检查 → MCP `merge_pull_request`（squash）→ 回主干 → 清分支
- 第一步新增 CHECKPOINT「当前分支判定」：在 `master` 上则第四步前建分支；已在特性分支上则说明上一轮未走完，沿用该分支并查是否已有开着的 PR。该支是「轮询 + 显式 merge」这一 auto-merge 等效实现的必要配套，不是防御性设计
- 新增「第三步之后 — 建特性分支」小节，含忘记建分支时的无损补救（`git switch -c` + `git branch -f master origin/master`，只移动引用不触碰工作树，用不上 `--hard`）
- 新增「这是 auto-merge 的等效实现」小节：GitHub 原生 auto-merge 是 GraphQL mutation，MCP 未提供对应工具，故用轮询替代；差异只在会话中断时 PR 会悬挂。明确不为此引入 `gh` CLI
- 第五步记入三个**静默失效形态**：漏传 `commit_message` 会丢 `Co-Authored-By`；`commit_title` 需自带 `(#N)`；🔴 **`commit_message` 里的尖括号写成 HTML 实体 `&lt;`/`&gt;` 时尾注看着还在但 GitHub 不识别为 co-author，且合并后无法修复**（改 master 的 message 需 force push，被 `non_fast_forward` 硬拒）。配 `git interpret-trailers --parse` 自检
- 第五步记入清分支的顺序硬约束（先本地后远端）与 `-d` 被拒时的树对象判据（`<branch>^{tree}` 与 `master^{tree}` 相等才 `-D`）
- 第五步提示 `plugin-validate` 是增量检查：只改 `docs/` 的 PR 上 30/40/41 三步全 `skipping`，绿灯此时几乎不携带插件相关信息
- 常见错误表新增 7 条（直推主干、漏传 `commit_message`、尖括号转义、`commit_title` 漏 `(#N)`、用 `get_status` 轮询、清分支顺序反了、`-d` 被拒改用 `-D`、忘建分支就推翻重做）

### Changed
- **第三步的比较基准从 `origin/master` 改为 `@{upstream}`**：在特性分支上 `origin/master..HEAD` 会把本分支全部提交都算成未推送，每次误触发 §A 的 amend 询问。`@{upstream}` 不存在（首次 `push -u` 之前）是正常状态而非错误
- 删掉第三步「第五步的同步推送复用其结果，不重复 fetch」一句：新第五步的 `git pull --rebase` 发生在 squash merge **之后**，那时 master 已前进，复用旧 fetch 结果会拿到过期状态
- 「工作区不干净」小节的命令块改为 `stash push <文件>` → `git switch master && git pull --rebase` → `stash pop`（原为 pull + push origin master）
- 开篇一句从「推送到 master」改为「经特性分支与 PR 合入 master」，并说明这是服务端强制
- `compatibility` 从「无 MCP 或第三方 CLI 依赖」改为声明需 `github` MCP server（本仓库 `plugins/optimus-mcp-servers/.mcp.json` 内置）；`allowed-tools` 由 `Bash` 改为 `Bash github`

### Fixed
- 常见错误表补入「用 `get_status` 轮询 CI」：`get_status` 查的是 legacy commit status，本仓五项是 check run，会返回 `total_count: 0` 的空结果并被误读成「CI 还没开始」。该误读在手工演练 PR #10 时真实发生过一次

## [4.0.0] - 2026-09-08

### Removed
- **第二步「版本号决策」整节移出**（含落点判断、两份同步、阻断式校验、「白名单冲突」元流程共 48 行）：版本一致性失效损害的是仓库长期状态而非本次提交，且原实现要求 LLM 逐行读并自觉执行——Codex 侧走标准 git 时完全不生效。校验脚本迁至 `.githooks/`，由 `pre-commit` 强制执行
- **§A「补齐符号链接」条件小节移出**（36 行）：同上，改由 `pre-commit` 检测。原实现的 GATE 使其仅在新增/删除 skill 时触发，执行频率极低，其中「未排除 gitignore 目录」的缺陷（会误报 `darwin-skill` 缺失）因此长期未暴露，迁移时一并修正
- `allowed-tools` 去掉 `Edit`：不再需要在提交流程内改写 `plugin.json` 与校验脚本

### Added
- 开篇新增「职责边界」表，明确本 skill 与 `.githooks/pre-commit` 的分工判据：失效后坏的是「这一次提交」还是「仓库长期状态」
- 第四步新增 CHECKPOINT：`pre-commit` 阻断时按报错分类处置，四类各有对应动作，明令禁止 `--no-verify`
- 第五步补齐 rebase 撞上未暂存改动的处置（`git stash push <文件>` → push → `git stash pop`），解决 known-issues 2026-09-07 条：该失败与第一步「排除无关改动」的规范互为因果，越守规范越必然撞上
- `metadata.category: workflow`（此前缺失）

### Changed
- 流程由「6 步 + 2 条件小节」收敛为「5 步 + 1 条件小节」，🔴 CHECKPOINT 由 4 个减至 3 个，SKILL.md 由 278 行降至 216 行
- 常见错误表重写：删除 6 条版本号/符号链接相关（已随门禁移出），新增 3 条（禁止 `--no-verify` 的理由、rebase 阻塞的正确解法、版本决策发生在改动时而非提交时）
- 正文不写职责边界说明：`description` 与 `allowed-tools: Bash`（无 `Edit`）已界定范围，散文式的分工表在流程正常时也要读、读完却不产生任何动作。设计决策的记录归 `.githooks/README.md` 与本文件

## [3.7.0] - 2026-09-08

### Added
- 第二步 CHECKPOINT 新增失败模式分流表：`check_plugin_versions.py` 的四种失败模式此前只有「版本号写错」一类有处置指引，撞上「有多余字段」（白名单校验）时无章可循
- 新增「白名单冲突」小节：以「该字段在 Claude 侧有无独立消费方」为可观测判据二选一——无消费方则删字段，有消费方则放宽门禁白名单，并明确放宽必须同时完成改脚本、改测试、记 `known-issues.md` 三件事
- 常见错误表增两行：报「有多余字段」直接删字段、放宽白名单只改脚本

### Changed
- `known-issues.md` 的 2026-09-08 条目标记为「已优化」，解决版本 3.7.0

## [3.6.1] - 2026-09-06

### Fixed
- `test_check_plugin_versions.py` 的 `test_agents_field_is_allowed` 固件路径由 `./agents/x.agent.md` 改为 `./agents/x.md`——避免测试固件成为 `.agent.md` 命名的残留示范，断言本身不受影响

## [3.6.0] - 2026-09-06

### Added
- 第二步新增阻断式校验：`scripts/check_plugin_versions.py` 比对每插件两份 `plugin.json` 的 `version`，不一致则禁止提交（配 11 个 unittest 用例，含「报错措辞不得写以某一份为准」一条）

### Changed
- 第二步「版本号决策」整节重写：版本落点从 `.claude-plugin/marketplace.json` 顶层下移至每插件的两份 `plugin.json`；升级幅度表删除，统一以 `AGENTS.md` 版本管理规则为唯一依据（原表与 AGENTS.md 有两行差异）
- 第三步暂存示例改为两份 `plugin.json`，不再示范 `git add .claude-plugin/marketplace.json`
- 常见错误表增两行：只升一份 `plugin.json`、改插件内容却升 marketplace 顶层

## [3.5.0] - 2026-09-04

### Changed
- 流程重组为「5 步主路径 + 2 条件小节」：将原第二步（.kiro/.agents/skills 符号链接）收敛为 §A 条件小节、原第五步 amend 合并收敛为 §B 条件小节，仅在该场景触发，主路径更短
- 去重：第四步 `git fetch` 一次，第六步 `git pull --rebase` 复用其结果，消除重复 fetch；第一步去掉与 `git status` 内容重复的 `git diff HEAD --stat`
- 修正「常见错误」表中「未提交 → 未推送」表述错误，步骤编号随重组同步更新

## [3.4.4] - 2026-08-30

### Added
- 新增 `known-issues.md` 使用期反馈记录机制（空模板），配套仓库新增的 skill 持续优化硬性约定，见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`

## [3.4.3] - 2026-08-29

### Changed
- Git 知识库入口链接随知识库领域元数据文件改名同步：`knowledge-base/git/00-README.md` → `README.md`

## [3.4.2] - 2026-08-27

### Changed
- Git 提交、分支、PR 与发布规则改为引用 `knowledge-base/git/`，skill 仅保留本仓库专用的发布编排与 checkpoint

## [3.4.1] - 2026-08-27

### Fixed
- 增加 PowerShell 提交信息的正确写法与提交后真实换行校验，明确禁止使用字面量 `\n` 拼接 message

## [3.4.0] - 2026-08-23

### Added
- 第二步扩展到同时维护 `.agents/skills/` 符号链接镜像：检查缺失、自动补齐、清理及暂存均覆盖
  `.kiro/skills/` 与 `.agents/skills/` 两个镜像（本仓库支持 Codex CLI，需在 `.agents/skills/`
  暴露与 kiro 一致的镜像）

## [3.3.0] - 2026-08-04

### Added
- 新增"第五步 — Unpushed 提交检测与 Amend 合并"：写 commit message 前检测当前分支相对
  `origin/master` 是否已有未推送的提交，若有则询问用户是否 amend 合并而非直接新建 commit，
  避免同一逻辑任务被拆成多个碎片提交（借鉴 appskills 仓库 fltrp-git-commit-helper 的
  unpushed 检测设计）
- "常见错误"表补充对应反例行
- 原"第五/六步"顺移为"第六/七步"

## [3.2.0] - 2026-07-11

### Added
- 新增"第二步 — 补齐 .kiro/skills 符号链接"：仅当本次改动包含 `.claude/skills/`
  下 SKILL.md 的新增或删除时触发（GATE门禁，避免每次提交都做无谓检查），
  自动检测缺失的符号链接并补齐（新增skill）或清理（删除skill），纳入本次提交
- "常见错误"表补充对应反例行

## [3.1.4] - 2026-07-11

### Fixed
- Co-Authored-By 原硬编码"Claude Sonnet 4.6 (1M context)"，与实际使用的模型不符；改为要求填写当前会话实际使用的模型名

## [3.1.3] - 2026-07-11

### Changed
- 随全仓库 unipus 前缀重命名为 optimus 同步更新（机械性文本替换，无行为变更）

## [3.1.2] - 2026-06-30

### Removed
- 移除 disable-model-invocation 限制

## [3.1.1] - 2026-06-26

### Changed
- "常见错误"表补充 force push 和 --no-verify 反例

## [3.1.0] - 2026-06-26

### Added
- 第一步"遗留暂存文件处理"检查点
- 第三步"原子性自查三问"加 🔴 CHECKPOINT 显性标记

## [3.0.1] - 2026-06-23

### Fixed
- 修复 disable-model-invocation 的 YAML 格式错误

## [3.0.0] - 2026-06-19

### Changed
- Skill 重命名：`publish-cc-plugin` → `commit-cc-plugin`（破坏性变更，需使用新名称调用）

## [2.0.0] - 2026-06-19

### Changed
- Skill 重命名：`unipus-commit` → `publish-cc-plugin`（破坏性变更，需使用新名称调用），精简步骤结构

## [1.0.0] - 2026-05-29

### Added
- 初始创建（原名 `unipus-commit`），本仓库专用发布工作流：版本决策、选择性暂存、提交、推送
