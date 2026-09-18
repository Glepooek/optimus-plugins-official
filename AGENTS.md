# AGENTS.md

本文件为 AI 编码 agent（Claude Code / OpenAI Codex）在此仓库中工作时提供指导。

## 仓库定位

自定义插件仓库，提供企业级开发工具链，**同时支持 Claude Code 与 OpenAI Codex 双 harness**。各插件职责见 `.claude-plugin/marketplace.json` 的 `description`。

**核心原则：单一真源，两个 harness 共用。** skill 正文只在 `plugins/*/skills/*/SKILL.md` 维护一份（Agent Skills 规范 `agentskills.io`，六字段 frontmatter）；两 harness 的清单文件（`.claude-plugin/marketplace.json`、`.agents/plugins/marketplace.json` + 每插件 `.codex-plugin/plugin.json`）只是指向同一份内容的安装入口，不复制正文。

### 必要差异（唯一的分叉点）

**全文只有这张表存在分叉**，其余规则对两个 harness 一视同仁。

| 方面 | Claude Code | Codex |
|---|---|---|
| 安装入口 | `/plugin marketplace add` 或手动 clone 到 `~/.claude/plugins/marketplace/` | `codex plugin marketplace add <repo>` → `codex plugin add <plugin>@optimus-plugins-official`，读取 `.agents/plugins/marketplace.json` |
| 提交流程 | 强制 `/commit-cc-plugin` skill | 标准 git + Conventional Commits，禁止 `--no-verify`；`.githooks/pre-commit` 的一致性门禁两侧同等生效 |
| Hooks | SessionStart（技巧轮播）、Notification（权限通知）生效 | 无对应机制，Claude 侧 hooks 在 Codex 中不生效 |
| 维护型 skill 镜像目录 | `.kiro/skills/<name>` | `.agents/skills/<name>` |
| 插件标识文件 | `.claude-plugin/marketplace.json`（含全部插件） | 额外的 `.agents/plugins/marketplace.json` + 每插件 `.codex-plugin/plugin.json` |

### 重要约束

- **SKILL.md 是唯一真源**：只改 `plugins/*/skills/*/SKILL.md`，不为 Codex 维护副本或改 frontmatter——两 harness 读的是同一份文件
- **跨插件无重复 skills**：新功能前先确认无跨插件重叠
- **Skills 可相互引用**：子 skill 用相对路径，跨插件用绝对命名空间
- **复合 skills 很少见**：仅在 3 个以上阶段且每阶段 >200 行时使用
- **上线前自检是否配对**：这个 skill 是指导用户完成某事的「引导器」，还是校验已有产物的「传感器」？有没有配对的另一半？避免只造轮子不造刹车

---

## Skill 分层与调用

**两层 skill，不要混淆：**

| 位置 | 性质 | Claude 调用 | Codex 调用 |
|---|---|---|---|
| `plugins/*/skills/` | 对外发布的插件产物 | `/plugin-name:skill-name` | 自然语言触发（按 description 匹配）或 `@plugin-name:skill-name` |
| `.claude/skills/` | 仅本仓库维护自用，不发布 | `/skill-name`（无前缀） | 同名触发 |

`.claude/skills/` 下的 skill 必须在 `.kiro/skills/`（Claude/Kiro 生态）与 `.agents/skills/`（Codex）**两处**保持同名符号链接镜像，`.githooks/pre-commit` 会检测缺失或悬空并阻断，报错中给出补齐命令。复合 skill 调用：`/plugin-name:skill-name:substep`（两 harness 语法一致，仅前缀符号不同）。

**第三种产物形态：agent**（`plugins/*/agents/<name>.md`）。与 skill 的区别是**上下文隔离**——skill 注入当前对话，agent 独立上下文只收一个 prompt，适合单次可闭环、需与主对话隔离的判定类任务。**必须在每插件 `.claude-plugin/plugin.json` 显式声明 `agents` 路径数组**（该字段是 replaces 语义，声明后默认目录扫描被取代，杜绝把配套文档误加载成假 agent）；Claude 侧 `plugin-name:agent-name` @-mention 调用，Codex 侧同名触发。配套文档放 `plugins/*/agent-docs/<name>/`（**不放 `agents/`**），独立版本化与门禁豁免细则见 `.claude/rules/agent-conventions.md`。

---

## 产物规范（四份规则文件，按编辑路径自动加载）

| 规则文件 | 承载什么 | 编辑什么时自动加载 |
|---|---|---|
| `.claude/rules/skill-conventions.md` | SKILL.md 六字段 frontmatter、执行前置校验、需求预告、持续优化约定 | `**/SKILL.md` |
| `.claude/rules/doc-conventions.md` | 编辑铁律、CHANGELOG 格式、README 六章节（skill/agent 两栏差异） | `**/CHANGELOG.md`、`plugins/*/skills/**/README.md`、`plugins/*/agent-docs/**/*.md` |
| `.claude/rules/agent-conventions.md` | agent 选型判据、`agents/` 目录硬约束、四字段 frontmatter、配套文档与独立版本化 | `plugins/*/agents/*.md`、`plugins/*/agents/**/*.md` |
| `.claude/rules/hook-conventions.md` | hook 规范依据映射、机械自检、双 harness 定位、已登记配置清单 | `plugins/*/hooks/**` |

**两处规范依据，禁止凭记忆或类比推导**：hook 的行为语义（事件选型、exit code、`async`、静默失效排查）以 `knowledge-base/claude-code-hooks/` 为准；插件与 marketplace 本身的字段语义、目录约束、七种插件源、版本解析与缓存以 `knowledge-base/claude-code-plugin-system/` 为准。本文件的「版本管理规则」是后者之上的**本仓落地约定**（如「条目内永不写 `version`」），两者是约定与判据的分层关系——改动约定前先读判据；可机械判定的部分已接进 `.githooks/check_external_entries.py`。

前三份规范**同时约束两个 harness**——frontmatter 是 Codex 也会原样读取缓存的内容，不存在「仅 Claude 遵守」的特例。第四份不同：**Claude 侧 hook 在 Codex 中不生效**，但其中的版本升级、门禁落位（仓库级门禁必须放 `.githooks/`）两条约定对两侧编辑者同等有效。

---

## docs/ 与 knowledge-base/ 的定位划分

两者都是 Markdown 文档集合，性质不同，新增文档前先判断该落在哪一侧（该判断与 harness 无关）：

| 维度 | `knowledge-base/` | `docs/` |
|---|---|---|
| 内容性质 | **规范条款**（MUST/SHOULD/MAY 语气），可执行的判断依据 | **叙述性资料**：使用指南、历史决策记录、外部资料备份 |
| 消费方式 | 被 skill **编程式检索**（`index.jsonl` + `file`+`anchor` 定位单条） | 人类完整阅读，无检索单条的场景 |
| 版本化 | 有独立版本号 + CHANGELOG，条目级别管理，见 `knowledge-base/README.md` | 无版本号，靠文件名日期或 git history 追溯 |

**判断标准**：这份内容是否需要被某个 skill 按条检索引用作为判断依据？是 → `knowledge-base/`；仅供人类阅读理解 → `docs/`。

`docs/` 内部已有的分类，供参照：`superpowers/specs/`、`superpowers/plans/` 是 brainstorming→writing-plans 工作流产生的**历史决策记录**（记录当时为什么这么设计，非可复用规范）；`todo-list/` 按日期分文件记待办与裁决，编号形如 `A3`、`B1`——本文件与 `ci.yml` 等处的注释会以「按 A3 裁决」引用，**裁决的完整经过只记在那里**，正文只留结论；`claude_blog/`、`claude_docs/`、`url_list.txt` 是外部资料备份/追踪表，与本仓规范无关；`SUPERPOWERS_GUIDE.md`、`claude-code-config.md` 是操作使用指南——这类流程性叙述天然依赖线性阅读顺序，即使内容详尽也不拆进 knowledge-base。

---

## 版本管理规则

### 两类版本号

**功能性**——harness 据此决定要不要拉新版本，改了才生效：

- `plugins/<plugin>/.claude-plugin/plugin.json` 的 `version`（Claude 侧读）
- `plugins/<plugin>/.codex-plugin/plugin.json` 的 `version`（Codex 侧读）

这两份是**同一个事实的两个 harness 视图**，无抄录关系也无主从关系：改动插件内容后，两份在同一次改动内一起升到同一个新值，新值由本次改动的性质决定。

**描述性**——无 harness 读取，纯供人判断该产物演进到哪一步：`SKILL.md` 的 `metadata.version`（每 skill 一个）、`agent-docs/<name>/CHANGELOG.md` 的最新 `## [x.y.z]`（每 agent 一个）。

⚠️ 两类版本号**不换算、不同步、不要求任何对应关系**。一个插件有多个 skill、节奏各异，试图让它们与插件号对应是无解的。

### 三处容易写错的 `version`

⚠️ **marketplace 顶层**（`.claude-plugin/marketplace.json`）的 `version` 只记录「集合里有哪些插件」，**仅在增删插件时升**。它不在官方版本解析回退链里，harness 不用它判断插件版本——**它不是任何插件的版本来源**。

⚠️ **marketplace 的插件条目内永不写 `version`**。① 官方明确：同时写 `plugin.json` 与条目时，Claude Code **总是用 `plugin.json` 的值且不给警告**，条目里的值只会被静默忽略；② 本仓条目 `source` 均为本地相对路径，官方对这类条目会额外校验、不一致时报警告。不填则无从冲突。

⚠️ **外部引用条目**（`source` 为 `url`/`github`/`git-subdir`，如 `cangjie-skill`/`archify`/`ppt-master`）**不参与本机制**——它不在 `plugins/` 下，我们无处写、也不该代写它的 `plugin.json`；其版本按官方回退链落到已固定的 `source.sha`，精确且无需维护。

### 触发矩阵：什么改动升哪一层

核心规则：**改动物理上落在哪个分发单元内，就升那个单元的版本号；产物级版本号只在改动落在该产物内部时才升。**

| 改动的文件 | 插件 `plugin.json`（两份同步） | `SKILL.md` `metadata.version` | agent CHANGELOG | marketplace 顶层 |
|---|---|---|---|---|
| `plugins/<p>/` 内任一文件（默认行：hooks、scripts、`.mcp.json`、插件根 README 等） | ✅ | — | — | ❌ |
| ↳ 其中 `skills/<name>/` 内（**含 `evals/`**） | ✅ | ✅ | — | ❌ |
| ↳ 其中 `agents/<name>.md` 或 `agent-docs/<name>/` 内 | ✅ | — | ✅ | ❌ |
| `external_plugins/*/` 内任一文件（拷贝模式引入的外部 skill） | ✅ | — | — | ❌ |
| **新增或删除整个插件** | ✅ 新插件起 `1.0.0` | — | — | ✅ |
| **新增链接模式的外部引用条目**（source 为 url/github/git-subdir） | — 无该文件 | — | — | ✅ |
| **新增拷贝模式引入的外部插件**（`external_plugins/<name>/`） | ✅ 起始值取**上游版本号**，非 `1.0.0` | — | — | ✅ |
| marketplace 的插件 `description` / `displayName` 等展示元数据 | ❌ | — | — | ❌ |
| **只改 `plugin.json` 自身的 `version`** | ❌ | — | — | ❌ |
| 外部引用条目的 `sha` / `ref` | — 无该文件 | — | — | ❌ |
| `.claude/`、`.github/`、`docs/`、`knowledge-base/`、`AGENTS.md`、`CLAUDE.md` | ❌ | — | — | ❌ |

**三条反直觉之处：**

⚠️ **「只改 `version` 本身」不构成再升一次**——补某一侧的漏升、新建 `plugin.json` 时写起始号，都属版本号自身的维护。否则陷入递归：升版本要改 `plugin.json`，改 `plugin.json` 又要升版本。

⚠️ **「新插件起 `1.0.0`」只适用于本仓自建插件**——链接模式的外部条目没有 `plugin.json`，无从起（顶层仍升 Minor）；拷贝模式起始值取上游版本号，因为它是读者判断「这份副本是哪一代内容」的唯一线索，归零会丢掉。拷贝模式有本地改动时 version 为**上游版本 + `-optimus.N`**：插件缓存按 version 分目录，内容改了 version 不变，已安装的人拿到的仍是旧缓存。**`external_plugins/` 目录当前无任何实例**，本条与矩阵里那两行是前瞻性约定。

⚠️ **「只改 `evals/` 也要升该 skill 的 `metadata.version`」反直觉但成立**——`metadata.version` 本就该反映「这个 skill 演进到哪一步」，**有行为测试的 skill 与没有的确实不是同一步**。

### 升级幅度

各层独立判定，同一次改动在不同层的幅度**可以不同**（如给某 skill 新增一节 → 该 skill Minor，但插件只是「修改已有内容」→ 插件 Patch）：

| 层级 | Major | Minor | Patch |
|---|---|---|---|
| 插件 `plugin.json`（两份同步） | 删除/重命名用户可见功能 | 新增 skill / agent / hook / command；**标记废弃但未删除** | 修改或修复已有内容 |
| `SKILL.md` `metadata.version` | 接口不兼容、删除用户可见功能 | 新增功能 / 章节 / 参数；**标记废弃但未删除** | 修改、修复、文档优化、重构 |
| agent CHANGELOG | 删除或重命名 agent、破坏调用契约 | 新增能力 / 章节 / 扩大适用范围；**标记废弃但未删除** | 修改已有行为、修复措辞 |
| marketplace 顶层 | 删除插件 | 新增插件 | **无对应场景** |

⚠️ **「标记废弃」升 Minor，「实际删除」才升 Major**（[semver 第 7 条](https://semver.org/lang/zh-CN/)：「在任何公共 API 的功能被标记为弃用时」必须升 Minor）。两步通常跨多次发布：先 Minor 标废弃留过渡期，待真正移除再 Major。**别把标废弃当成 Major**，那会让使用者以为功能已经没了。

⚠️ **升 Major 时 MINOR 与 PATCH 归零，升 Minor 时 PATCH 归零**（semver 第 7、8 条）——`2.4.7` 的下一个 Major 是 `3.0.0` 不是 `3.4.7`。手写时最容易漏这一步，而 `pre-commit` 只校验两份 `plugin.json` **是否同值**，两份一起写错它拦不住。

⚠️ **两份 `plugin.json` 的幅度必然一致**——幅度由改动的性质决定，两份记录的是同一次改动。**marketplace 顶层的 Patch 位永久停在 `0`**：它只有「新增插件 → Minor」「删除插件 → Major」两种触发，这是刻意收窄的结果，**不要为了填满三档而编造 Patch 场景**。

**功能变了版本号不变 = 不完整交付**——必须主动检查并升版，不等用户提醒。`.githooks/pre-commit` 会在提交前校验两份 `plugin.json` 是否同值，不一致则阻断（该门禁对两 harness 同等生效，Codex 走标准 git 时一样拦截）。

### darwin-skill 评分门禁

Minor/Major 升级前必须用 `darwin-skill` 给改动的 skill 评分：新分 ≥ 改动前分数才可提交，倒退则先修正。

🔴 **本体用全局安装的那份，不在本库找**——`~/.claude/skills/darwin-skill/`。本仓 `.claude/skills/darwin-skill/` 没有 `SKILL.md`，只是承接产物的目录。

产物只落 `results.tsv`（九列 TSV，列义见 `darwin-skill/SKILL.md`，**每仓一份**），**已入库**：它是棘轮机制「上次分数」的唯一载体，从源码生成不出来；`.gitattributes` 给了它 `merge=union`（纯追加型单文件，避免多分支尾部冲突）。🔴 **本仓不生成 `cards/` 成果卡片**——`darwin-skill` 默认在优化完成后自动出卡片，此处刻意覆盖：本仓只看 `results.tsv`，卡片是纯装饰、不随仓库分发，生成它只是白跑一次截图（该目录与 CLI 的 `results/` 均已 gitignore）。

⚠️ **暂存 `results.tsv` 必须带 `-f`**，否则 `git add` 报「paths are ignored」并**退出码 1**，放进 `&&` 链里会中断后续命令。**完整机制（三种命令口径、镜像门禁的两条正交排除理由、`--no-index` 的必要性）在 `.gitignore` 该行注释、`.githooks/README.md`、`.githooks/check_skill_mirrors.py` 的 docstring 各有一份**，改机制时以那三处为准。⚠️ 由此的通用教训：**验证必须覆盖本次的关键动作**（那次判据判错，根因是测了不含 `add -f` 的中间态）。

**只约束 skill**——rubric 针对 SKILL.md 结构，对 agent 无对应维度，agent 改动按其 spec 的验收清单人工核验。

🔴 **只改 `evals/` 时本门禁空转**：触发矩阵的 `evals/` 特例会把它判成 Minor 从而触发本门禁，而九维 rubric **全部针对 `SKILL.md`、不读 `evals/`**——SKILL.md 一字未改时除 dim8（重新采样的噪声）外必然不变。此时记 `baseline`（首评，`old_score` 记 `-`），不要声称「新分 ≥ 旧分、门禁通过」：**跑它只为留一条基线，不是为了拿一个有信息量的比较。**

---

## 提交与推送

**必须**用 `commit-cc-plugin` skill，禁止手动跑 git 工作流（说「提交」或「推上去」即触发）。它只负责这一次提交本身——暂存范围、原子性、message 格式、推送。

**主干 `master` 已开启保护规则，直推会被服务端以 `GH013` 拒绝。** 路径是「特性分支 → PR → CI 全绿 → squash merge」，`commit-cc-plugin` 第五步已按此改造。**Codex 侧走标准 git 时同样必须建分支走 PR**——ruleset 是服务端强制，不依赖任何 harness 的自觉。分支名按 `knowledge-base/git/rules/01-branching.md` 的 `<type>/<简短描述>`，`type` 与本次 commit 的 Conventional Commits type 逐字对齐。

**门禁有两个执行点**：`.githooks/pre-commit` 在本地（需 `git config core.hooksPath .githooks`），`.github/workflows/ci.yml` 在每个 PR 上跑**同一批脚本**——后者不依赖本机配置，补齐了 pre-commit 长期「本地未启用就形同虚设」的缺口。禁止 `--no-verify` 绕过。门禁挂在 hook 而非 skill 正文，是因为 Codex 侧走标准 git 流程读不到 skill，写在 skill 里的检查在 Codex 下完全不生效。

**六个必需检查的 job 名**——`ci.yml` 的五项（`gates-hooks`、`gates-tests`、`gates-data`、`plugin-validate`、`new-skill-eval-case`）加 `actionlint.yml` 的 `actionlint`——**由服务端 ruleset `master-protection` 要求，而它不在版本库里、改动不留 diff**。🔴 **改 job 名必须同步改 ruleset**，否则那项检查会静默不再被要求——属「不报错的失效形态」。⚠️ **反方向同样会漂移**：`actionlint` 被勾选为第六项后，本文件与 `commit-cc-plugin/SKILL.md`、`actionlint.yml` 三处都还写着「五项」，直到 2026-09-18 用 `gh api repos/:owner/:repo/rulesets/23134670` 对账才发现。**项数声明处处是副本，真源只有那条 API。**

**新增 skill 必须带 eval case**：`plugins/<plugin>/skills/<skill>/evals/<case>/` 下需有 `prompt.md`（或 `case.yaml`），由 `new-skill-eval-case` job 强制，**存量不回溯**。**活体样本是 `plugins/optimus-frontend-plugin/skills/wpf-code-review/evals/` 的 6 个 case**（`01-listbox-virtualization` 等），照它写即可；规范条款见 `knowledge-base/skill-authoring/rules/03-skill-evaluation.md` § 1。⚠️ 门禁只查 case **存在**，不查内容有没有意义——质量属人工评审。⚠️ 那 6 条的判据是付费 `llm` grader，而 `skill-eval.yml` 缺 `ANTHROPIC_API_KEY`，因此**形态合规但在 CI 里一次都跑不了**——别把它当作「eval 已在 CI 里生效」的证据。

**pre-commit 具体拦什么**（与 skill 分工明确）：每插件两份 `plugin.json` 版本同值、`plugins/*/hooks/hooks.json` 与 Claude Code 契约相符、marketplace 外部引用条目锁 40 位 `sha` 且不写 `version`、台账「已接入」表与条目 sha 一致、`.kiro`/`.agents` 符号链接镜像完整且以 `120000` 模式入库。**新克隆的仓库需执行一次 `git config core.hooksPath .githooks`**（该配置是本机的，不随仓库分发）。

---

## 本地测试

改动 skill / hook / command 后用 `--plugin-dir` 加载本仓做交互验证，见 `test-locally` skill（`/test-locally` 触发）。以下清单本地复现「提交与推送」那六个必需检查中的**三个**——`gates-hooks`、`gates-tests`、`gates-data`；余下 `plugin-validate`（上游 action）、`new-skill-eval-case`（依赖 PR diff）与 `actionlint`（本机未装该二进制）**无本地等价命令，只能在 PR 上验证**，别把本节跑绿当成 CI 会绿。

**七项提交门禁**（对应 `gates-hooks`，CI 逐字复用同一个文件）：

```bash
sh .githooks/pre-commit
```

⚠️ 这一条覆盖全部七项，**跑它不需要先 `git config core.hooksPath .githooks`**——那条配置只决定提交时会不会自动触发，直接调文件路径始终可用。

**Python 单元测试**（**本机无 `pytest`，只能用 `unittest`**）：全仓共 **9 个**测试目录，`unittest discover` 不递归跨目录，必须逐个跑。该清单的真源是 `ci.yml` 的 `gates-tests` job——**本地漏跑不会报错，只会在 PR 上撞红**，而 `gates-tests` 是必需检查、`bypass_actors` 为 null，无人可绕过。**新增测试目录时两处都要改。**

```bash
# 维护型 skill
python -m unittest discover -s .claude/skills/sync-cc-docs-to-youdaonote/scripts -p "test_*.py"
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py"

# 提交门禁脚本
python -m unittest discover -s .githooks -p "test_*.py"

# 插件内脚本
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts -p "test_*.py"
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/scripts -p "test_*.py"
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/scripts -p "test_*.py"
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts -p "test_*.py"
python -m unittest discover -s plugins/optimus-mcp-servers/scripts -p "test_*.py"
```

**数据文件一致性**（对应 `gates-data`，三项均从仓库根不带参数运行）：

```bash
python .claude/skills/knowledge-base-maintain/scripts/check_index.py
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
python .claude/skills/sync-cc-tips/scripts/validate_tips.py
```

---

## 关键文件

| 文件 | 用途 | harness |
|---|---|---|
| `plugins/*/.claude-plugin/plugin.json` | **每插件版本真源**（与 `.codex-plugin/plugin.json` 同步同值）+ `agents` 声明 | Claude 侧读，两者共同维护 |
| `plugins/*/.codex-plugin/plugin.json` | 每插件的 Codex 标识清单 + 版本号（与 `.claude-plugin/plugin.json` 同步同值） | Codex 侧读，两者共同维护 |
| `.claude-plugin/marketplace.json` | 插件清单与展示元数据；顶层 `version` 仅记录集合构成，**不是插件版本来源** | 两者共用 |
| `.agents/plugins/marketplace.json` | Codex plugin marketplace 安装入口 | Codex 专属 |
| `.claude/rules/`（四份，按编辑路径自动加载） | 各自承载什么见「产物规范」节 | 两者共用 |
| `.githooks/`（`pre-commit` + 五个自检脚本） | 七项提交门禁，检查项与判据见 `.githooks/README.md`；需 `git config core.hooksPath .githooks` 启用 | 两者共用 |

**已被 gitignore 的目录（有意排除，非缺失）：** `.claude/skills/darwin-skill/`（⚠️ 其中 `results.tsv` 已 `git add -f` 入库，**不受该行影响**，见「darwin-skill 评分门禁」节）、`.remember/`、`.codegraph/`、`.superpowers/`、`.playwright-cli/`、`.playwright-mcp/`
