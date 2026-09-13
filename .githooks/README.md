# .githooks

仓库一致性门禁。检查的是**失效后会损害仓库长期状态**的东西，与某一次提交的内容无关——只是借提交这个必经关口拦截。

提交行为本身的规范（暂存原子性、commit message 格式、推送流程）不在这里，由 `commit-cc-plugin` skill 承担。

## 启用

配置在本机 `.git/config` 里，**不随仓库分发**，新克隆后需执行一次：

```bash
git config core.hooksPath .githooks
```

未启用时 hook 静默不执行，不会有任何提示——**但改动仍会被 PR 上的 CI 拦住**（`gates-hooks` job 跑的是同一个脚本，见「与 CI 的关系」）。这批门禁此前只在配置过 `core.hooksPath` 的机器上生效过，搬进 CI 后第一次有了不依赖本机配置的执行点。

## 检查项

| # | 检查 | 失效后果 |
|---|---|---|
| 1 | 每插件两份 `plugin.json` 的 `version` 同值 | 两个 harness 读到不同版本号 |
| 2 | hook 配置与 Claude Code 契约相符 | hook 静默失效——不报错、不中断、无痕迹 |
| 3 | marketplace 条目合规与 `.claude-plugin/` 目录内容 | 条目写歪多数不报错，只是静默退回「跟随分支最新」、整条加载失败，或插件正常加载而组件全部不出现 |
| 4 | `.claude/skills/` 每个 skill 在 `.kiro`/`.agents` 都有符号链接 | Kiro 或 Codex 侧看不到该 skill |
| 5 | 镜像不指向已删除的 skill | 悬空链接 |
| 6 | 镜像以 `120000` 模式入库 | `core.symlinks=false` 时会存成普通文件，克隆到别的机器就不是链接 |
| 7 | `evals/` 下每个子目录都含 `case.yaml` 或 `prompt.md` | 缺 marker 的目录被 `claude plugin eval` 静默忽略——少跑一个 case，而总数只在 verbose 输出里 |

第 1 项由 `check_plugin_versions.py` 实现（18 个单元测试）。

第 2 项由 `check_hook_configs.py` 实现（21 个单元测试），扫 `plugins/*/hooks/hooks.json` 与 `.claude/settings*.json`，查七项机械可判定的错配：`async` 与展示类输出的错配、`async`/`asyncRewake` 用在非 command handler、handler 类型与事件不符、非工具事件上的 `if`、不支持 matcher 的事件上写了 matcher、永不匹配的 `mcp__<server>` matcher、PowerShell 裸占位符，另加拼错的事件名。判据真源是 `knowledge-base/claude-code-hooks/`，每条报错都带对应索引条目 ID。脚本定位不到被引用的脚本文件时不报——宁可漏报也不误报。两类文件的 `hooks` 键要求不同：`hooks.json` 缺顶层 `hooks` 对象是错配；`settings*.json` 是通用设置文件（`enabledPlugins`、`permissions`、`env` 等），完全不配 `hooks` 属常态，只在该键存在而类型不对时才报。

第 3 项由 `check_external_entries.py` 实现（49 个单元测试），分两组判据。

**外部引用条目**（`source` 为对象，非本地相对路径）：`sha` 是否 40 位全长、是否误写 `version`、`strict:false` 是否配了非空 `skills` 数组、`source.source` 类型与 `git-subdir` 的 `path`、展示元数据（`description`/`homepage`/`author`）是否齐备，以及是否登记进 `.claude/skills/add-external-skill/registry.md` 的「已接入」表且台账 sha 与条目 sha 一致；另外还会检查拷贝模式落位的 `external_plugins/*/UPSTREAM.md` 是否存在且含 40 位 SHA。这些写歪的形态多数不报错——漏 `sha` 只是静默退回「跟随分支最新」，缺 `skills` 数组则整条加载失败，都是需要借提交关口拦的形态。刻意不联网：条目结构完美但上游仓库已被删除或转私有，这一项抓不到，只能靠实际安装时暴露。

**全部条目与插件目录**（判据真源是 `knowledge-base/claude-code-plugin-system/`，每条报错都带对应索引条目 ID）：marketplace 名是否撞上 17 个 Anthropic 保留名或 Claude Desktop 的三个保留名、marketplace 与条目名是否满足 kebab-case 与 Claude Desktop 托管同步的字符集、本地路径源的 `./` 前缀 / `..` / 反斜杠 / 目标目录存在性、`relevance` 的 `topic` 长度与五种信号的条数与长度上限（含 `hosts` 的裸小写主机名形态与 `manifestDeps` 的 `file` 末尾锚定）、以及 `.claude-plugin/` 目录内除清单外是否混进了组件目录。这一组针对的同样是「不报错」的形态：保留名会在某个版本起让整个 marketplace 停止加载、条目名不合规会被 Claude Desktop 静默删除、拼错的信号名只会静默不匹配、组件放进 `.claude-plugin/` 后插件仍显示为启用而组件一个都调不出来。

### `check_skill_mirrors.py`：第 4–6 项，判据是「这个 skill 由本仓分发吗」

第 4–6 项由 `check_skill_mirrors.py` 实现（10 个单元测试）。⚠️ **它 2026-09-14 前是内联在 `pre-commit` 里的 sh，是七项中唯一没有单测的一项**；抽成脚本不是为了整齐，而是因为它的判据被撞出了一个错，而当时没有任何测试宿主能承接对这个判据的断言。

🔴 **「由本仓分发」有两条正交的排除理由，缺任一条都误判：**

| # | 排除理由 | 为什么 | 活体 |
|---|---|---|---|
| 一 | 目录里没有 `SKILL.md` | 镜像的目的是让 skill 被两个 harness **发现**，一个没有 `SKILL.md` 的目录镜像过去对两侧都无意义 | `.claude/skills/darwin-skill/` 是评分的**工作目录**，skill 正文装在全局 `~/.claude/skills/darwin-skill/` |
| 二 | 被 gitignore 排除 | 是 skill，但本仓刻意不分发 | 同上（当下恰好同时满足两条） |

⚠️ **两条只是在当下这一个目录上重合，并不等价**——有 `SKILL.md` 却被忽略的目录属理由二，没有 `SKILL.md` 也未被忽略的目录属理由一。单测 `test_two_exclusion_reasons_are_independent` 用三个目录把这件事钉住，正是因为「从单一样本推出两个条件等价」在本项上已经发生过一次。

🔴 **理由二的实现必须带 `--no-index`，这是本项被撞出的那个错：** `git check-ignore` **默认也查 index**，子树内任一文件经 `git add -f` 进入 index 后，该目录就不再被报告为已忽略。于是「把 `results.tsv` 判据入库」这个动作会反过来触发本检查、要求给 `darwin-skill` 补两处镜像并阻断提交。git 自己的文档正为此列出该开关：「when developing patterns including negation to match a path previously added with `git add -f`」。

⚠️ **由此得到的教训比那一行开关更重要**：`git add -f` 并没有绕开 gitignore 那条边界，它只是把同一次撞击**推迟**到文件真正进入 index 的那一刻。此前 `.gitignore`、`AGENTS.md`、todo B8 三处都写着「`git add -f` 不碰 gitignore 的判定，是一条不移动边界的落地路径」——那个判断是在 `results.tsv` **尚未** `add -f` 的中间态下测出来的，测的状态里不含本次的关键动作。三处已随本项一并更正。

单测 `test_add_f_does_not_make_an_ignored_skill_distributed` 是该事故的活体复现，在临时目录里跑**真 git**（不 mock `check-ignore`）——把 git 换成替身的测试恰好绕过出错的那一环，永远抓不到它。已做阴性对照：临时把实现换成漏掉 `--no-index` 的版本，该目录立刻被判为分发并报出 2 条缺镜像。

### `check_new_skill_eval_case.py`：一个脚本，两个模式，一个挂得上一个挂不上

该脚本（31 个单元测试）有两个互不重叠的模式，**分界线正是「要不要 diff」**：

| 模式 | 判据 | 挂在 `pre-commit`？ | 由谁调用 |
|---|---|---|---|
| `--all`（上表第 7 项） | `plugins/*/skills/*/evals/` 下**每个**子目录都含 `case.yaml` 或 `prompt.md` | ✅ 挂了 | `pre-commit` 第 5 项检查 + `gates-hooks`（逐字复用） |
| `<base-ref> <head-ref>` | 本次改动新增的 `plugins/<plugin>/skills/<skill>/SKILL.md` 必须配 `evals/<case>/`（缺失即失败并给出应建路径） | ❌ 挂不上 | 只由 `ci.yml` 的 `new-skill-eval-case` job 调用 |

增量模式挂不上的原因是它需要两个 ref 之间的 diff，而 `pre-commit` 必须保持暂存区无关（见下节「与 CI 的关系」）；`--all` 只读工作树，因此不受该约定限制。位置都在 `.githooks/` 是遵守 `.claude/rules/hook-conventions.md` 的「仓库级门禁必须放 `.githooks/`」。

🔴 **两个模式查的不是同一件事，缺一不可。** 增量模式只在**新增 SKILL.md** 时触发，所以「给存量 skill 补 case 但补错形态」完全落在它的射程外——单测 `test_adding_eval_case_to_existing_skill_is_not_a_new_skill` 明确锁定了这条放行。`--all` 补的正是这个缺口。

⚠️ **两个模式的量词刻意相反**：增量模式问「这个 skill 有没有 case」（任一子目录合格即可），`--all` 问「有没有哪个 case 只建了一半」（每个子目录都要合格）。**后者不被前者覆盖**——3 个子目录里 2 个合格 1 个缺 marker 时，前者判通过，而 `claude plugin eval` 会静默少跑那一个。

🔴 **`--all` 跳过名为 `results/` 的子目录，这不是可选的宽松而是必需的。** `claude plugin eval` 把 `aggregate-result.json` 写进 `<eval 目录>/results/<ISO 时间戳>/`，而 eval 目录默认就叫 `evals/`——**产物与人工维护的 case 目录同级，且天然缺 marker**。不跳过的后果实测过：在 skill 目录内跑一次 eval，下一次提交就被 `pre-commit` 阻断，**门禁反过来惩罚使用被它保护的东西**。第二道防线是 `.gitignore` 的 `evals/results/`（不入库）。两道都要：只忽略不跳过仍会阻断提交，只跳过不忽略则产物会被误提交。代价是一个真名叫 `results` 的 case 会被静默跳过，可接受——该名字已被 CLI 占用。

⚠️ **`--all` 仍不判定「有 `evals/` 却一个合格子目录都没有」，但理由已经换了。** 原理由是「那是另一套规范的合规产物」——`knowledge-base/skill-authoring/rules/03-skill-evaluation.md` 曾有一条 MUST「测试用例存到 `evals/evals.json`」，而 `wpf-code-review/evals/` 正是它的产物，两套规范谁服从谁需要人裁决。**该裁决已于 2026-09-13 作出：官方格式为唯一规范**，那 6 条素材已迁成 `evals/<case>/prompt.md` + `graders/criteria.md`，本仓再无此形态的实例。现在的理由是一条纯粹的判据边界：**「一个 case 都没有」与「这个 skill 不需要 case」在文件系统上不可区分**，而「新增必须带 case、存量不回溯」的存量豁免恰恰意味着后者合法存在——要收紧成失败，就得先有一份「哪些 skill 必须有 case」的名单，而那正是增量模式已经用 diff 回答的问题，不该在全量模式里再造一份会过期的名单。

⚠️ 文件名全程在 Python 内解析，**不经 shell、不用 `xargs`**：本仓的必需检查不跳过 fork PR，而 fork 的文件名不可信。

```bash
python -m unittest discover -s .githooks -p "test_*.py"
```

## 与 CI 的关系

`.github/workflows/ci.yml` 的 `gates-hooks` job **逐字执行 `sh .githooks/pre-commit`**，不在 workflow YAML 里重写一份门禁逻辑。这是本目录唯一的第二执行点。

🔴 **由此产生一条硬约定：`pre-commit` 不得引入依赖暂存区的检查**（`git diff --cached`、`git diff --name-only --staged` 等）。当前七项检查全部基于工作树与 `git ls-files`，**这条性质必须保持**——一旦引入，CI 的逐字复用即失效，门禁判据会在两个环境间静默分叉：本地拦得住的 CI 拦不住，反之亦然。

需要 diff 的门禁改为「接受 base/head 两个 ref 作参数、只由 CI 调用、不进 `pre-commit` 序列」。⚠️ **这条约定约束的是检查，不是文件**：`check_new_skill_eval_case.py` 的两个模式分别落在约定的两侧——增量模式走上面那条路，`--all` 模式因为只读工作树而挂进了 `pre-commit`（见上一节）。**判断该不该挂，看的是这个检查要不要 diff，而不是它所在的脚本以前挂没挂。**

⚠️ **「暂存区无关」不等于「不许碰 index」，这个区别在第 4–6 项上有实际后果。** 约定的实质是「判据不得随**这次暂存了什么**而变」，因此禁的是 `git diff --cached` 这类「本次要提交什么」的查询；而 `git ls-files -s`（第 6 项读模式位）把 index 当作「仓库已跟踪什么」的视图，在干净工作树下等于 HEAD，CI checkout 后结论一致。**`git check-ignore` 的默认行为恰好踩在两者之间**——它读 index，却让判据随「这个子树里有没有文件被 `add -f` 过」而翻转，这已经不是稳定的仓库状态视图了。`--no-index` 把它拉回纯 `.gitignore` 判定，也就把这一项拉回约定之内。**同一句「读 index」，一处安全一处不安全，分界线是「读到的东西会不会随一次 `git add` 改变判据」。**

## 为什么挂在 hook 而不是 skill 里

这些检查曾写在 `commit-cc-plugin` 的 SKILL.md 中，靠 LLM 逐行读并自觉执行。两个问题：

- **Codex 侧走标准 git 流程，读不到 skill 正文**——门禁在那一侧从来没生效过
- **写在条件小节里的检查执行频率极低**，其自身的缺陷长期得不到反馈（符号链接检查原先漏了排除 gitignore 目录，会误报 `darwin-skill`，因为 GATE 保护极少触发而一直没被发现）

## 不要用 --no-verify

阻断说明仓库一致性真的坏了。报错文本里带了修复命令，按它改；若判定是 hook 自身误报，就修 hook 并补测试。`--no-verify` 只是把问题推给下一个人。
