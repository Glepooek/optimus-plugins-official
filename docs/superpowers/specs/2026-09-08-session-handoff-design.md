# session-handoff Skill 设计文档

**日期：** 2026-09-08
**作者：** anyu
**版本：** 1.0.0
**状态：** 待批准

---

## 背景

Claude Code / Codex 的每个新会话对之前发生的一切一无所知。context 压缩能延续单次会话的连贯性，但**关不掉的窗口边界依然存在**：换一天、换一台机器、换 harness，上下文一律归零。

任务跨多个会话时（本仓的知识库三领域扩建跨五个阶段、门禁迁移跨两个会话，都是实例），现有载体各有缺口：

| 现有载体 | 记录什么 | 缺什么 |
|---|---|---|
| `git log` | 做了什么（已落盘的结果） | 为什么这么选、放弃过什么、下一步打算做什么 |
| 待办清单（如 `docs/todo-list/`） | 待办条目 | 无上下文，"session-handoff" 五个字看不出要做成什么样 |
| harness 的 memory 机制 | 跨会话恒真的事实 | 单条一事，不承载「某个任务当前进行到哪一步」 |
| CHANGELOG / known-issues | 已完成的变更、已发现的缺陷 | 只覆盖产物自身，不覆盖会话级的进行状态 |

本 skill 补的正是中间那层：**任务级的会话交接**——下一个会话（或下一个人、下一个 harness）读完就能接着干。

这是跨领域的通用需求，与具体技术栈无关，因此作为独立插件对外发布。

---

## 参照实现

两份参照，同名不同物，分歧点是「交接给谁」：

| | `mattpocock/claude-handoff` | `fltrp-session-handoff` |
|---|---|---|
| 体量 | SKILL.md 1.3 KB | SKILL.md 17 KB + templates 8 KB |
| 交接物 | **进程**——摘要直接作为 `claude --bg` 的 prompt | **文档**——五件套落盘 `docs/sessions/` |
| 交接给谁 | 几秒后启动的另一个 agent | 明天的自己、同分支的同事 |
| 隔离维度 | 无 | git 分支 × `git config user.name` |
| 写入时机 | 用户显式调用 | 显式调用 + 每轮静默追写 + 上下文告急自动保存 |
| 核心约束 | 不重复已有产物（spec/plan/commit），引用路径即可 | 分层沉淀：progress（做了什么）/ summaries（为什么）/ conversations（聊了什么） |
| 附加机制 | 无 | stop hook 提醒、artifacts.json 产物注册、pitfalls.md 踩坑沉淀 |

**本 skill 取舍**：形态取 fltrp（落盘文档，跨天/跨机器/跨 harness 都能读），**约束取 claude-handoff**（不重复 git/CHANGELOG/known-issues 已记录的内容，引用路径）。写入时机两者都不取，只保留显式触发。

---

## 设计决策

### 决策 1：落盘文档，不拉起后台 agent

`claude --bg` 是 Claude Code 专有能力，Codex 侧无对等机制。本仓 `AGENTS.md` 的核心原则是「单一真源，两个 harness 共用」，交接物必须是两边都能读的文件。且后台 agent 的交接物随进程消失，跨天场景直接失效。

### 决策 2：仅手动触发，不做静默追写

fltrp 的「每轮有实质产出就静默追加 conversations」有两个问题：

1. **判定不可靠**——「有实质产出」由 LLM 自评，标准漂移；
2. **产生碎改动**——每轮写盘会让 `git status` 长期不干净，与本仓 `commit-cc-plugin` 的原子性自查直接冲突。

本仓的一贯风格是显式触发（提交必须说"提交"），交接同理。

### 决策 3：分支 × 用户名维度做成运行时**推导规则**，而非固定目录层级

采用「分支 × 用户名」隔离，但**每次运行实测、按需退化**，不写死目录层级。

理由是本 skill 对外发布，落地环境差异极大：

| 环境 | 分支 | 协作者 | 合适的路径 |
|---|---|---|---|
| 业务仓库（fltrp 的原生场景） | 多 feature 分支 | 多人 | `docs/sessions/feat-x/2026-09-08-xxx.anyu.md` |
| 本仓这类单人插件仓 | 长期 master | 1 人 | `docs/sessions/2026-09-08-xxx.md` |

固定写死 `{branch}/{user}` 会让后者得到 `docs/sessions/master/xxx.anyu.md`——两段各只有一个取值，纯噪音。反过来只按日期又会让前者的多人交接物互相覆盖。

**规则表达维度，运行时决定是否展开**。详见「三、交接物路径」。

### 决策 4：不做 artifacts.json / pitfalls.md / stop hook

三者都是 fltrp 为其业务工具链设计的联动机制，本仓无对应消费方：

- `artifacts.json` 的消费方是 `tech-spec-generator` / `client-dev-pipeline` 等，本仓没有这条流水线
- `pitfalls.md` → `code-linter` 的闭环，本仓的对等物是 `knowledge-base/` 与各 skill 的 `known-issues.md`，已有归属
- stop hook 在本仓的对等位置是 `.githooks/pre-commit`，而交接物是否更新**不适合做阻断**（不是仓库一致性问题）

---

## 一、定位与产物形态

**层级**：`plugins/optimus-session-plugin/skills/session-handoff/`——**对外发布的插件产物**，不是本仓自用 skill。

### 为什么新建独立插件而非并入 optimus-devops-plugin

`optimus-devops-plugin` 装的是 Jenkins 构建、项目分析、周报、符号链接同步、.NET 取证——都绑定「某条具体的运维/交付动作」。会话交接是**跨领域的基础能力**：写 WPF 的人要交接，写 PRD 的人也要交接。挂在 DevOps 下会让另外八个领域的用户找不到它。

代价明确并接受：marketplace 顶层版本需升 Minor（`14.0.0` → `14.1.0`），且要独立维护两份 `plugin.json`。

### 无本仓自用副本

本仓开发时直接用发布版 `/optimus-session-plugin:session-handoff` 调用，**不在 `.claude/skills/` 另存副本**。两份内容必然逐渐分叉，违反 `AGENTS.md`「单一真源」原则。

因此**不需要** `.kiro/skills/` 与 `.agents/skills/` 符号链接——那两处只镜像 `.claude/skills/` 下的自用 skill，`plugins/` 下的产物由各 harness 的插件安装机制分发。

### 文件构成

```
plugins/optimus-session-plugin/
├── .claude-plugin/plugin.json     # Claude 侧清单
├── .codex-plugin/plugin.json      # Codex 侧清单（含 interface 段）
├── README.md                      # 插件根 README，六章节
└── skills/session-handoff/
    ├── SKILL.md                   # 主流程，目标 ≤ 150 行
    ├── CHANGELOG.md
    └── test-prompts.json          # 触发与边界测试用例
```

不设 `references/`——本 skill 的模板只有两个（交接物、恢复检查清单），直接内联 SKILL.md。参照的 fltrp 拆 references 是因为它有 8 KB 模板，本 skill 达不到那个体量，拆分只会增加一次文件读取。

不设 `known-issues.md`——那是本仓自用 skill 的惯例（`.claude/skills/*/`），发布产物用 CHANGELOG 记录演进。

### 版本号

按 `AGENTS.md` 触发矩阵，本次改动同时落在三层：

| 层级 | 动作 |
|---|---|
| `plugins/optimus-session-plugin/.claude-plugin/plugin.json` | 新插件起 `1.0.0` |
| `plugins/optimus-session-plugin/.codex-plugin/plugin.json` | 同上，同值 |
| `SKILL.md` 的 `metadata.version` | 起 `1.0.0` |
| `.claude-plugin/marketplace.json` 顶层 | `14.0.0` → `14.1.0`（新增插件 = Minor） |

⚠️ marketplace 的**插件条目内不写 `version`**——会被 `plugin.json` 静默覆盖，且本仓条目 `source` 为本地路径时官方还会报不一致警告。

---

## 二、Frontmatter

遵循 `.claude/rules/skill-conventions.md` 的六字段规范：

```yaml
---
name: session-handoff
description: 跨会话交接工作时使用。会话结束前保存交接物（当前进度、下一步、关键决策），或新会话开始时恢复上次进度。触发场景：用户说"交接"、"保存进度"、"handoff"、"继续上次的工作"、"接着干"、"上次做到哪了"、"恢复进度"。
metadata:
  version: "1.0.0"
  author: optimus
  category: workflow
compatibility: 需要 Git 仓库环境；无 MCP 或第三方 CLI 依赖。
allowed-tools: Bash Read Write Edit Glob Grep
---
```

**调用方式**：Claude 侧 `/optimus-session-plugin:session-handoff`，Codex 侧按 description 自然语言匹配或 `@optimus-session-plugin:session-handoff`。`name` 字段本身不带插件前缀——前缀由 harness 按所属插件自动加。

**`allowed-tools` 说明**：需要 `Write`/`Edit` 写交接物，`Read`/`Glob`/`Grep` 读回历史交接物与相关代码，`Bash` 取 git 状态。**不含** `Task`/`Agent`——本 skill 不拉起子 agent（决策 1）。

---

## 三、交接物路径

### 推导规则

```
docs/sessions/[<branch>/]<YYYY-MM-DD>-<slug>[.<user>].md
```

两个可选段按实际情况退化：

| 段 | 何时出现 | 何时省略 |
|---|---|---|
| `<branch>/` | 当前分支 ≠ 仓库默认分支 | 在默认分支上工作时 |
| `.<user>` | `git log --format=%an` 去重后 > 1 人 | 单人仓库 |

**默认分支的判定**：`git symbolic-ref refs/remotes/origin/HEAD` 取远端默认分支，取不到（如无 origin）则回退为「当前分支就是默认分支」，即省略该段。不要硬编码 `master` 或 `main`——两者在真实项目中都常见。

多人业务仓库上的典型形态：

```
docs/sessions/feat-coupon-stacking/2026-09-08-api-contract.anyu.md
```

单人插件仓（如本仓）退化为：

```
docs/sessions/2026-09-08-session-handoff-spec.md
```

⚠️ **判定必须每次实测，不得缓存或写死**：分支用 `git rev-parse --abbrev-ref HEAD`，协作者数用 `git log --format=%an | sort -u | wc -l`。假定"这个仓库是单人的"会在有人加入的当天静默产生文件覆盖。

### slug 命名

取本次会话的**任务主题**，kebab-case，3-5 个词。不是日期的重复、不是"session-1"这类序号——序号无信息量，恢复时看不出该读哪个。

### 为什么按「日期 + 主题」而非「按人滚动追加」

fltrp 的 `progress/{user}.txt` 是单文件无限追加、恢复时读末尾 30 行，这隐含假设「一个分支 = 一个任务」。该假设在两种常见情形下不成立：

- **同一分支跨多个不相干任务**——尤其长期停留在主干的仓库，所有内容会挤进一个越来越长的文件
- **同一天并行推进两件事**——混进一个文件后恢复时要人工筛

一任务一文件、文件名带主题 slug，恢复时按文件名直接选。代价是文件数量增长，靠日期前缀自然排序、`ls -t` 取最近即可。

---

## 四、两种模式

skill 被触发后先判定模式，不询问用户：

| 用户意图 | 模式 |
|---|---|
| "交接"、"保存进度"、"handoff"、"要下班了" | **保存** |
| "继续上次的"、"接着干"、"上次做到哪了"、"恢复进度" | **恢复** |
| 无法判定 | 询问，二选一 |

### 模式 A：保存

#### 前置校验（HARD GATE）

1. `git rev-parse --is-inside-work-tree` — 非 git 仓库则终止
2. `git status --short` — 有未提交改动时**不阻断**，但交接物中必须记录这些文件的当前状态（下一个会话会看到一个脏工作区，需要知道为什么）

#### 采集（全部只读，不猜测）

```bash
git rev-parse --abbrev-ref HEAD          # 分支
git log --oneline -10                    # 本次会话的落盘结果
git status --short                       # 未完成的工作区状态
git log origin/master..HEAD --oneline    # 未推送的提交
```

#### 交接物内容

见「五、交接物模板」。核心约束（承自 claude-handoff）：

> **不重复其他产物已记录的内容。** 代码改动看 `git diff`、决策记录看 CHANGELOG、已知缺陷看 known-issues.md、跨会话事实看 `memory/`。交接物只写这些地方**没有**的东西——正在进行中的判断、下一步的具体动作、以及为什么。

⚠️ 这条是本 skill 最容易失守的地方。把 `git log` 抄一遍很容易，且看起来很充实，但对下一个会话零价值——它自己会跑 `git log`。

#### 收尾

写完后向用户报告文件路径，**不自动提交**。交接物是否入库、何时入库由用户决定；有些仓库还有专属提交流程（如本仓的 `commit-cc-plugin`），代为提交会绕过它。

### 模式 B：恢复

#### 定位交接物

```bash
ls -t docs/sessions/**/*.md | head -5
```

按修改时间倒序列出最近 5 个。**多于一个时必须让用户选**，不要默认取最新——同一天可能有多个任务，猜错会让整个会话跑偏。仅一个时直接读。

#### 读取顺序

1. 交接物本身
2. 交接物中「引用」段列出的路径（spec、CHANGELOG、known-issues 等）
3. `git log --oneline -10` 对照交接物写入后是否有新提交（有 → 说明交接物已过时，需提示用户）

#### 恢复后动作

向用户复述三件事，然后**停下等指令**：

- 上次进行到哪一步
- 下一步待办（按交接物中的优先级）
- 有无阻塞项

⚠️ **不要读完就自动开工**。交接物里的"下一步"是上个会话的判断，用户的实际意图可能已经变了。

---

## 五、交接物模板

```markdown
---
task: <任务主题>
date: <YYYY-MM-DD>
branch: <分支名>
status: 进行中 | 已完成 | 已搁置
---

# <任务主题>

## 当前状态

<2-4 句。这个任务要达成什么、现在到了哪一步。让人读完知道自己接手的是什么。>

## 已完成

- <具体到文件名和产物，不是"做了一些改动">

## 下一步

- 🔴 <必须优先做的>
- 🟡 <应该尽快做的>
- 🔵 <有空再做的>
- ⏸️ <阻塞项> — 阻塞原因：<原因>

## 关键决策

- **<决策>**：<为什么这么选，以及放弃了什么>

## 待验证的假设

- <当前基于什么假设在推进，这个假设怎么验证>

## 引用

- <路径或 URL> — <这里面有什么>
```

### 各段的取舍规则

| 段 | 必填 | 空了怎么办 |
|---|---|---|
| 当前状态 | ✅ | 不能空。写不出来说明这次会话没有可交接的东西，应告知用户无需交接 |
| 已完成 | ✅ | 同上 |
| 下一步 | ✅ | 若确实全部做完，写「已完成，无后续」并把 `status` 标为 `已完成` |
| 关键决策 | ❌ | 没做决策就删掉整段，不要写"无" |
| 待验证的假设 | ❌ | 同上 |
| 引用 | ❌ | 同上 |

⚠️ **维度可以为空，但不要凑数**。写"（无）"占位比删掉更糟——下一个会话要花时间确认这个"无"是真没有还是忘了写。

### 优先级标识

沿用 fltrp 的四档（🔴高 / 🟡中 / 🔵低 / ⏸️阻塞）。理由是这套符号在终端里视觉区分度高，且阻塞项单列一档能避免下个会话反复尝试一件根本做不了的事。

**⏸️ 必须附阻塞原因**——不写原因的阻塞项等于没写，下个会话还是要重新排查一遍才知道为什么卡住。

---

## 六、Red Flags

| 错误做法 | 正确做法 |
|---|---|
| 把 `git log` 内容抄进「已完成」 | 下个会话自己会跑 `git log`。写 git 里看不到的：为什么这么改、试过什么没成 |
| 「下一步」写成"继续完善 XXX" | 具体到可执行的动作："给 check_plugin_versions.py 补 symlink mode 的测试用例" |
| 交接物写完顺手 `git commit` | 只写文件，报告路径。入不入库由用户定，有些仓库还有专属提交流程 |
| 恢复模式读完交接物直接开工 | 复述三件事后停下等指令，用户意图可能已变 |
| 多个交接物时默认取最新 | 让用户选。同一天可能有多个不相干的任务 |
| 阻塞项不写原因 | ⏸️ 必须附「阻塞原因」，否则下次要重新排查 |
| 为了让文档"完整"给空维度写"（无）" | 删掉整段。空维度的存在本身就是噪音 |
| 单人仓库硬编码不带 `.user` 后缀 | 每次实测 `git log --format=%an \| sort -u \| wc -l`，有人加入时自动生效 |

---

## 七、与其他 skill / 机制的边界

### 跨插件无重复（AGENTS.md 硬约束）

发布前须确认无跨插件重叠。逐个核对现有 48 个 skill 后，唯一需要辨析的是 `optimus-devops-plugin:weekly-report`：

| | weekly-report | session-handoff |
|---|---|---|
| 输出面向 | **人**（主管读的周报） | **下一个 agent**（会话恢复用） |
| 时间范围 | 一周 | 单次会话 |
| 内容取向 | 已完成的成果，总结性 | 未完成的下一步，前瞻性 |
| 数据来源 | git log + 对话 | 会话内的判断与决策（git 里看不到的） |

两者都读 git log，但产出的信息类型正交——周报不写"下一步待办的优先级"，交接物不写"本周工时分布"。**判定：不重叠**。

### 与本仓其他机制的关系（用户侧同理）

| 对象 | 关系 |
|---|---|
| 提交类 skill（本仓为 `commit-cc-plugin`） | **不重叠**。本 skill 写交接物文件但不提交；提交仍须显式触发提交流程 |
| harness 的 memory 机制 | **互补**。memory 存「跨会话恒真的事实」（用户偏好、项目约束），交接物存「某个任务当前的进行状态」。任务完成后交接物成为历史，memory 条目继续有效 |
| 待办清单（如 `docs/todo-list/`） | **互补**。待办清单是跨任务的条目列表（"要建 session-handoff skill"），交接物是单任务的进行状态（"这个 skill 的 spec 写到第五节"） |
| 规范知识库（如本仓 `knowledge-base/`） | **不重叠**。交接物是叙述性的进行状态，不是可检索的规范条款 |
| 提交门禁（如本仓 `.githooks/pre-commit`） | **无关**。交接物是否更新不做阻断——它不是仓库一致性问题，漏写只影响下次接手效率 |

---

## 八、验收标准

实现完成后逐条验证：

### 插件脚手架

| # | 验收项 | 验证方式 |
|---|---|---|
| 1 | 两份 `plugin.json` 同值 `1.0.0` | `sh .githooks/pre-commit` 通过 |
| 2 | marketplace 顶层升至 `14.1.0`，新增插件条目且**条目内无 `version`** | 读 `.claude-plugin/marketplace.json` |
| 3 | Codex 侧 `.agents/plugins/marketplace.json` 同步新增条目 | 对照两份 marketplace |
| 4 | `.codex-plugin/plugin.json` 含 `interface` 段与 `skills: "./skills/"` | 对照 `optimus-prd-plugin` 格式 |
| 5 | 插件根 README 六章节齐全 | 按 `.claude/rules/doc-conventions.md` |
| 6 | `claude plugin validate` 无 warning | 命令行执行 |

### skill 行为

| # | 验收项 | 验证方式 |
|---|---|---|
| 7 | 保存模式产出符合模板的交接物 | 触发"交接"，检查段落齐全、无"（无）"占位 |
| 8 | 路径推导在单人默认分支下不产生空嵌套 | 本仓触发，路径应为 `docs/sessions/YYYY-MM-DD-<slug>.md` |
| 9 | 路径推导在多分支/多人下正确展开 | 建临时分支 + 模拟多作者，路径应变为 `docs/sessions/<branch>/<date>-<slug>.<user>.md` |
| 10 | 默认分支判定不硬编码 master/main | 在 `main` 为默认分支的仓库验证同样省略分支段 |
| 11 | 恢复模式在多个交接物时让用户选 | 造两个交接物，触发"继续上次的"，确认列出选项而非默认取最新 |
| 12 | 恢复后不自动开工 | 确认复述三件事后停下 |
| 13 | 不自动提交 | 触发保存后 `git status` 显示交接物为 untracked，未生成 commit |
| 14 | 交接物不重复 git log 内容 | 人工核对「已完成」段，不应是 commit message 的复述 |
| 15 | SKILL.md ≤ 150 行 | `wc -l` |
| 16 | 恢复真的可用（端到端） | 见下方「最小可行测试」 |

### darwin-skill 评分门禁

按 `AGENTS.md`，新插件属 Minor 升级，**提交前须用 `darwin-skill` 对 session-handoff 评分**。新 skill 无「改动前分数」可比，以评分不低于同类 workflow skill（如 `weekly-report`）为准，倒退项先修正。

### test-prompts.json

参照 `optimus-prd-plugin` 惯例（31/48 个 skill 已有），至少覆盖三类：

| # | 场景 | 考察点 |
|---|---|---|
| 1 | "交接一下" + 会话有实质产出 | 正常保存路径，段落取舍正确 |
| 2 | "继续上次的工作" + 存在多个交接物 | 是否让用户选，而非默认取最新 |
| 3 | **指令冲突**："快速交接，别问了" + 会话内容极少 | 用户要求从简，但可交接内容不足。应告知"本次无实质可交接内容"，而不是（a）无视指令追问，也不是（b）生成大量空洞占位符 |

第 3 条是关键——它测的是本 skill 最容易失守的地方：为了显得"完整"而输出无价值内容。

### 最小可行测试

前面都是结构性检查，这条才是真正的成败判定——**交接物能不能让一个无上下文的会话接着干**。

- **单一变量**：下一个会话除交接物外不给任何提示
- **执行**：会话结束前保存交接物 → 开新会话，只说"继续上次的工作" → 观察它能否正确说出任务是什么、下一步做什么
- **成功判定**：新会话复述的「下一步」与上个会话的实际意图一致，且无需用户补充背景
- **失败判定**：新会话问出"这个任务是要做什么"这类本该在交接物里的问题
- **失败后收集**：新会话具体缺了哪条信息 → 反推模板缺哪一段 → 补进模板并记 CHANGELOG

---

## 九、实现步骤

```
1. 建插件脚手架
   plugins/optimus-session-plugin/{.claude-plugin,.codex-plugin}/plugin.json + README.md
   → 验证：验收项 1、4、5

2. 两处 marketplace 新增条目 + 顶层升 14.1.0
   .claude-plugin/marketplace.json 与 .agents/plugins/marketplace.json
   → 验证：验收项 2、3、6

3. 写 SKILL.md（分段写入，勿单次输出全文）
   → 验证：验收项 15，frontmatter 六字段符合 skill-conventions.md

4. 写 CHANGELOG.md + test-prompts.json
   → 验证：test-prompts 三类场景齐全

5. 用本 skill 保存本次会话的交接物（自举）
   → 验证：验收项 7、8、13、14

6. 开新会话触发恢复
   → 验证：验收项 11、12、16（最小可行测试）

7. darwin-skill 评分
   → 验证：不低于同类 workflow skill，倒退项先修正

8. 按测试结果修正模板
   → 验证：重跑第 6 步
```

⚠️ 第 5-6 步是**自举验证**：用这个 skill 交接「这个 skill 的实现」本身。它同时检验保存与恢复两条路径，且失败反馈直接——新会话答不上来就是模板有缺口。

⚠️ 第 9、10 项（多分支/多人、非 master 默认分支）本仓无法自然验证，需建临时分支或找一个 `main` 为默认分支的仓库实测。**不要因为"本仓用不上"就跳过**——这是对外发布的产物，用户环境恰恰以那种形态为主。

---

## 待确认

以下三点在实现前需要拍板，不影响 spec 主体：

1. **插件命名**——本 spec 暂用 `optimus-session-plugin`。现有九个插件均为 `optimus-<领域>-plugin` 格式，`session` 符合该模式。若你倾向别的名字（如 `optimus-handoff-plugin`），实现前告知
2. **`docs/sessions/` 是否入版本库**——入库则交接物可跨机器同步、可回溯；不入库（gitignore）则纯本地。**倾向入库**，跨机器场景正是落盘方案相对后台 agent 的主要优势。注意这条决定要写进 skill 的输出提示里，让用户自行决定是否 gitignore
3. **是否需要配对的「校验」skill**——`AGENTS.md` 的新 skill 自检要求判断「引导器 vs 传感器」。本 skill 是引导器，其传感器形态（检查交接物是否过期/格式合规）**倾向不做**：为低频场景造刹车本身就是另一种过度设计
