---
name: sync-cc-tips
description: 从 Claude Code 最新 changelog 自动同步 tips.jsonl：按环境可用性与可感知性双重门禁新增条目、修正过时内容、删除已废弃功能，写入后做九项完整性校验并推进同步锚点，最后调用 commit-cc-plugin 提交。触发场景：用户说 "/sync-cc-tips"、"更新tips"、"同步tips"、"tips需要更新"、"从changelog更新tips"、"sync tips"。可附带版本数量参数，如 "/sync-cc-tips 5" 表示只看最近5个版本。
metadata:
  version: "2.3.2"
  author: desktop client team
compatibility: 需要 Python 3（标准库，无第三方依赖）——第一步取 changelog 走 urllib 两跳（raw.githubusercontent.com → api.github.com），两跳均失败时降级为 WebFetch；第三步斜杠名取证需本机 claude 二进制（默认 npm 全局安装路径，可用 --binary 指定）。脚本经 Bash 调用 Windows 原生 Python，二者文件系统视图不同，临时文件一律用仓库内相对路径。流程末尾调用 commit-cc-plugin skill 完成提交推送。
allowed-tools: Bash WebFetch Read Write Edit Grep AskUserQuestion Skill
disable-model-invocation: true
---

# /sync-cc-tips

从 Claude Code 最新 changelog 同步 tips.jsonl：**抓取、判定、写入、校验全自动，但写入前必须经一次人工确认**，确认后展示摘要并提交。

⚠️ **本流程含 5 个阻塞式人工确认点，不得跳过：**

| 位置 | 触发条件 | 跳过的后果 |
|---|---|---|
| 执行前置校验 | tips.jsonl 有未提交改动 | 回滚基线被污染，出错时 `git restore` 会连带丢弃用户的那些改动 |
| 第一步 | 待处理版本 > 30 个（无论锚点是否命中） | 可能误处理过大范围 |
| 第二步 | tips.jsonl 为空 | 把异常空文件当作全新初始化，静默丢失全库 |
| 第二步 | `validate_tips.py` 报出存量 `failed` 项 | 把改动前就有的缺陷算成本轮写入错误，或反过来静默继续 |
| 第四步 | 变更数 > 0，写入前 | 未经确认改写唯一真源 |

📌 `disable-model-invocation: true` **有意保留，不要顺手删掉它来「修规范」**——它是 Claude Code 原生字段（合法可用，判据见 `.claude/rules/skill-conventions.md`），作用是本 skill **只能由人显式触发、不支持无人值守调度**：模型不自主拉起，`/loop` 等计划触发也只当纯文本，故五个确认点始终有人应答，不存在「无人应答怎么办」的分支。Codex 侧该字段不生效，那一侧仍可能被自主拉起。


## 执行前置校验（进入第一步前必过）

四类检查一次跑完，**不要边执行边发现**。用户可提供的信息只有可选的版本数量参数 `N`，不存在"信息不全需先追问"的情形——缺 `N` 就是默认全量，不问。

```bash
git rev-parse --show-toplevel >/dev/null 2>&1 && test -z "$(git rev-parse --show-prefix)" && test -f AGENTS.md  # 4 运行条件：**先跑这条**，cwd 错会让下面各条给出错误诊断
python -V || python3 -V                              # 1 依赖：两者皆无才算缺失
python .claude/skills/sync-cc-tips/scripts/check_slash_name.py init   # 1 依赖：verdict 非 binary_missing 即可
python .claude/skills/sync-cc-tips/scripts/validate_tips.py           # 2 输入：只读 checks.json_valid
test -w plugins/optimus-devops-plugin/hooks/sessionstart && test -w .claude/skills/sync-cc-tips  # 3 输出：两个输出文件分属不同目录
ls .claude/skills/sync-cc-tips/.last-synced-version  # 2 输入：锚点文件
git status --short plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl  # 4 运行条件：回滚基线是否干净
```

| # | 类别 | 检查项 | 不满足时 |
|---|---|---|---|
| 1 | 依赖 | Python 解释器可用 | ❌ 仅当 `python` **与** `python3` 都不可用才报错终止。只是缺 `python` 别名（常见于 Linux/WSL）不终止——各步失败表已写明改用 `python3` 重试，那是既有降级路径 |
| 1 | 依赖 | `claude` 二进制存在 | ⚠️ **不终止**，标记降级：本轮新增条目一律省略斜杠形式，摘要注明「取证不可用」（等同第三步 `binary_missing`）。**探测方式是跑脚本本身读 `verdict`，不要在正文抄写二进制路径**——路径是 `check_slash_name.py` 的常量，抄一份必然分叉；非默认路径用 `--binary` 指定 |
| 2 | 输入 | tips.jsonl 可解析 —— **判据只有 `checks.json_valid.ok`** | ❌ 该项为 false 才报错终止（在损坏文件上做增删会把损坏固化进 git）。⚠️ **不要拿整体 `ok` 或退出码当判据**：`ok` 聚合九项，库里任一存量 `schema`/`field_dup`/`body_shape` 缺陷都会让它为 false，据此终止就抢走了第二步「存量问题交用户裁决」那一支 |
| 2 | 输入 | `.last-synced-version` 存在且为纯版本号（无 `v` 前缀） | ⚠️ 缺失按首次初始化处理，只在摘要说明；扫描范围过大由第一步「待处理版本 > 30」CHECKPOINT 兜住，此处不重复设卡 |
| 2 | 输入 | 用户给了 `N` 时须为正整数 | ❌ 报错终止——不猜用户意图，不静默退回全量。这项是静态判断，无对应探测命令 |
| 3 | 输出 | 两个输出文件所在目录**各自**可写 | ❌ 报错终止。⚠️ 二者**不同目录**：tips.jsonl 在 `plugins/optimus-devops-plugin/hooks/sessionstart/`，`.last-synced-version` 在 `.claude/skills/sync-cc-tips/`。漏查后者的后果是写完 tips.jsonl 才在第五步锚点写入时炸，落进人工善后分支 |
| 4 | 运行条件 | **cwd 必须等于仓库根**，不是"在仓库内" | ❌ **硬约束**，报错终止。⚠️ 两个坑：`git rev-parse --show-toplevel` 成功**不**构成通过（它在任意子目录都退出 0，而本 skill 的脚本路径全是**相对仓库根**的）；而拿 `--show-toplevel` 与 `pwd` 直接比字符串在本机**必然假阴性**——前者给 `E:/...`、后者给 `/e/...`。故判据用 `--show-prefix` 为空（与路径形式无关），加一条 `--show-toplevel` 成功以排除非仓库目录，再加一条 `test -f AGENTS.md` 以排除**别的**仓库的根目录（前两条对任何 git 仓库根都通过）。三条缺一不可。Bash 工具的 cwd 跨调用保持，上一条命令 `cd` 过就会踩到 |
| 4 | 运行条件 | tips.jsonl 在 git 中无未提交改动 | 🔴 **可协商风险 → CHECKPOINT**，见下 |

**为什么 git 干净度是可协商风险而非硬约束**：技术上完全可以在有改动的文件上继续写，用户也可能正清楚自己为什么改了它。真实代价是**回滚基线被污染**——出错时 `git restore` 会连带丢弃那些改动。用 `AskUserQuestion` 发起，不要用自由文本问 y/n：

- `question`：「tips.jsonl 已有未提交改动（贴出 `git status --short` 输出）。继续同步会让本轮改动与这些混在一起，出错时 `git restore` 会把它们一并丢弃。是否继续？」
- options：①「先 stash 这一个文件的改动，再继续同步」（推荐——**消除**风险且不放弃本轮）②「保留改动继续同步，我清楚它们」③「取消本轮，我自己处理」
- 选①→ 执行 `git stash push -- plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl` 后按干净基线执行。⚠️ **必须带 pathspec**：裸 `git stash` 是仓库级操作，会把工作区全部在途改动一起收走，而本 skill 的问题域只有这一个文件。⚠️ stash 了就**必须归还**——记下本轮曾 stash，第六步摘要按模板提示用户 `git stash pop`，否则用户的改动停在 stash 里无人告知；选②即继续且**不算任务失败**，同时**记下「脏基线已获同意」**——第四步写入前的复检见到同样的非空输出据此直接放行，**不得二次询问**（那等于作废刚给出的同意），只有输出与此刻所见**不同**（中途又被改过）才重新确认；选③或用户走 **Other 输入自由文本（视为非明确同意）→ 立即停止**

⚠️ 前置校验只做**执行前的主动探测**。执行中才暴露的报错（抓取失败、Edit 报错、脚本崩溃）归各步自己的失败处理表，两者不合并——把执行中错误塞进本节会让它变成一份永远不完整的错误清单。

## 第一步 — 抓取 changelog

```bash
python .claude/skills/sync-cc-tips/scripts/fetch_changelog.py
# 用户传了 /sync-cc-tips N 时：加 --limit N
```

脚本内部完成读锚点、两跳取数（换主机名而非换工具）、按锚点截断、失败时连通性分诊。**降级链的正确写法已固化在脚本里并被单测锁住，不要在此重写命令。**

**读输出的这几个字段决定下一步：**

| 字段 | 含义 | 处置 |
|---|---|---|
| `ok` | 取数与解析是否成功 | `false` 看 `verdict` 与 `next` |
| `versions` | `[{v, bullets}]`，新→旧 | 第三步逐条判定的输入 |
| `version_count` | 待处理版本数 | 0 → 无新版本，跳过 Step 3-6 且**无需推进锚点**（锚点已等于最新版，区别于「🚦零变更总闸」） |
| `range` | `[最旧, 最新]` | 摘要展示用 |
| `needs_confirm` | 范围是否过大（> 30 个版本） | `true` → 🔴 见下方 CHECKPOINT |
| `advance_anchor` | 本轮是否该推进锚点 | `false`（`--limit` 模式）→ 第五步不写 `.last-synced-version` |
| `anchor_found` | 锚点是否在 changelog 中命中，**三态** | `true` 正常；`false` 锚点已被滚出文件，仅作摘要说明；`null` 表示本轮压根没查锚点，此时不要把它当成 `false` 去报「锚点丢失」 |
| `limit` | 用户传入的 `N`（`--limit`），未传为 `null` | 与 `anchor_found` 组合判出三种取数模式，见下表 |

**三种取数模式由 `anchor_found` + `limit` 组合判定**（脚本内部优先级 `limit` > 锚点 > 默认窗口）：

| `anchor_found` | `limit` | 模式 | 摘要该怎么写 |
|---|---|---|---|
| `true` / `false` | `null` | 锚点截断（常规） | 「自 v{anchor} 起」；`false` 时补「锚点已滚出文件，取全部可见版本」 |
| `null` | `null` | **首次运行**，取最近 **10** 个版本 | 「首次运行，取最近 10 个版本」——不要写成锚点丢失 |
| `null` | 有值 | `--limit N` 临时查看 | 「按 --limit 取最近 N 个」；此模式 `advance_anchor` 恒为 `false` |

> 🔴 **CHECKPOINT**（`needs_confirm: true` 时触发）：用 `AskUserQuestion` 询问「本轮待处理 {version_count} 个版本（超过 30 个）{锚点未找到时补一句：且 changelog 中未找到锚点版本 v{anchor}}，是否继续？」，选项：「继续处理全部版本」（推荐）／「取消，我需要先确认是否漏看了历史内容」。选后者立即停止整个流程。

**取数失败时按 `next` 走，不要自行改写 URL：**

| `verdict` | `next` | 处置 |
|---|---|---|
| `single_host_blocked` | `webfetch` | 两跳主机均不可达但网络正常 → `WebFetch: https://api.github.com/repos/anthropics/claude-code/contents/CHANGELOG.md`，锚点截断在读到的文本上按同规则人工执行。**URL 用 api 域**：raw 域已被证实不可达，指回去等于把这一跳的独立性押在网络栈上 |
| `network_down` | `stop` | 全部探测主机均为 `000`，确属断网 → 停止流程，不执行任何写入。**不要再试 WebFetch**（同样走网络） |
| `parse_failed` | `stop` | 取到内容但无 `## ` 版本标记（`head` 字段给出前 200 字符，多为 HTML 错误页）→ 这是**解析失败**而非取数失败，停止流程并报告 |

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 脚本非零退出但输出不是合法 JSON | 跑 `python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_fetch*.py"` 判断是脚本坏了还是环境问题 | 停止流程，报告解释器或脚本异常，不做任何写入 |
| WebFetch 第三跳也失败 | 报告「两条 curl 路径与 WebFetch 均已失败」，在 `known-issues.md` 记一行（说明 api 通道也失效，需要新的取数通道） | 停止流程，不执行任何写入 |
| `python` 命令不存在 | 改用 `python3` 重试一次 | 停止流程，报告解释器不可用 |

## 第二步 — 读取现有 tips.jsonl

> **黄金真源 = `tips.jsonl`**（单一真源：`show-tip.sh` 展示与 `sync-cc-tips` 同步均读写它）。每行一个 JSON 对象，字段 `{id, category, title, body}`。`id` 是稳定主键（命令名/flag/功能名），`body` 含真实换行的 `功能/效果/例子`。

**三个脚本一次跑完**（互不依赖，可并行调用）：

```bash
S=.claude/skills/sync-cc-tips/scripts
python $S/build_alias_index.py    # 判重集：{ids, aliases, stats}
python $S/detect_residue.py       # 残影候选：{candidates, shared_main, stats}
python $S/validate_tips.py        # 基线体检：{ok, entries, failed, checks}
```

| 脚本 | 产出用于 | 失败处置 |
|---|---|---|
| `build_alias_index.py` | 第三步逐条查表判重 | **停止整个流程** |
| `detect_residue.py` | 第四步残影栏与同主标识符聚集栏 | 不中止，残影栏改写为「⚠️ 残影检测未运行（原因）」 |
| `validate_tips.py` | 记下 `entries` 作为改动前基线 | 报告后由用户裁决是否先修复 |

⚠️ **三者的失败处置刻意不同，不要照搬。** `build_alias_index.py` 失败必须停——判重集不全会让已覆盖的功能点被判为新增，静默产出重复条目，这比不同步更糟；`detect_residue.py` 失败只损失一次可选的清理机会，停掉整轮反而是过度反应；`validate_tips.py` 报的是**改动前就存在**的问题，不是本轮造成的。

**判重基准**：一个 changelog 功能点的**任意一个主标识符**在 `ids`/`aliases` 中命中 → 视为已覆盖，不新增。

`build_alias_index.py` 只收录**带语法标记**的标识符（斜杠命令含 `/plugin:skill` 命名空间、长短 flag、大写环境变量），并做斜杠/双横前缀剥离、连字符与下划线互换、小写三类归一化；此外 `SEMANTIC_ALIASES` 显式登记字面无关的等价组（`/cost`≡`/usage`≡`/stats`、`/review`≡`/code-review`、`/plugin`≡`/plugins`、`/undo`≡`/rewind`）——字面归一化对语义等价名无效，只能显式登记。

> ⚠️ **不要改回收录裸英文词**（失效原理见文末黑名单）。`test_build_alias_index.py::TestExtractRejectsNoise` 已锁住该行为。

`detect_residue.py` 补齐判重的盲区：判重是单向的（changelog → 已有条目），不检查**已有条目之间互相覆盖**。召回需同时满足主标识符相同 + `功能：` 段落 bigram 达到阈值包含关系。

> ⚠️ **输出是待裁决候选，不是判定结果。** 真残影与非残影的重叠度在数值上交叠，纯词频区分不了，阈值因此按**召回**定，宁可多召回几个让人看。残影候选在第四步预览中单独列出交用户裁决，**不要让脚本或模型自行删除**。（阈值取 0.25 的实测依据见 `references/measurements.md`，改阈值前先读。）

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 文件不存在 / 脚本报路径错 | 确认路径 `plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl` 是否正确 | 停止整个流程，报告路径错误，不做任何修改 |
| `validate_tips.py` 报 `entries: 0` | 🔴 CHECKPOINT：停下询问用户是否为全新初始化场景 | 若用户确认，继续（视为无旧条目）；否则停止 |
| `validate_tips.py` 有 `failed` 项 | 🔴 **CHECKPOINT**：用 `AskUserQuestion` 报告失败项，问「先修复存量问题再同步」还是「记下基线继续」 | 用户选择继续则**原样留存这份基线 JSON**，第五步按「基线豁免」判读（见第五步） |
| 任一脚本非零退出 / traceback / 输出非 JSON | 跑 `python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py"` 定位是脚本坏了还是数据触发边界；单测过说明问题在数据 | 按上表「失败处置」列分别处理，不要一律停或一律继续 |
| `python` 命令不存在或版本过低 | 改用 `python3` 重试一次 | 停止流程，报告解释器不可用；**不要退回手工 grep 判重**（失效原理见文末黑名单） |

## 第三步 — 三类差异识别

依次对 changelog 中每个功能点做判断：

### 📋 差异识别中间过程表（先于三类判定生成）

在做出新增/修改/删除判定之前，先按 changelog 每条 bullet 生成一行记录，汇总成一张表，覆盖窗口内**每一条** bullet（不只是最终判定为新增/修改的那些）：

| Bullet 摘要 | 提取的主标识符 | 命中情况 | 判定 |
|---|---|---|---|
| Added CLAUDE_CODE_PROJECT_DIR_NAME env var... | `CLAUDE_CODE_PROJECT_DIR_NAME` | 未命中 | 🆕 新增 |
| Fixed auto mode in very long sessions... | （无用户可操作标识符，纯 bug fix） | — | ⏭️ 跳过（非用户可操作功能） |
| Changed /doctor to also report plugin health... | `/doctor` | 命中 `ids`，对应「/doctor-配置体检」 | ✏️ 修改 |
| Added a badge showing the current permission mode in the footer... | （无带语法标记的标识符——`badge`/`footer` 是裸英文词，索引有意不收） | 索引查不到，按语义人工核对已有「权限模式-footer-徽章」条目 | ⏭️ 跳过（已覆盖） |

⚠️ **末行演示的是索引的能力边界，不是可自动化的命中。** `build_alias_index.py` 只收带语法标记的标识符，纯功能描述型 bullet（无斜杠命令、无 flag、无环境变量、无 settings 键）在索引里必然查不到——此时**不要**因为「未命中」就判新增，改为按语义人工核对。收裸英文词是已被证伪的方案（见文末黑名单），不能为了让这类 bullet 自动命中而放宽索引。

**判定归类为四种：**
- 🆕 新增（判定规则见下方「🆕 新增条件」）
- ✏️ 修改（判定规则见下方「✏️ 修改条件」）
- ⏭️ 跳过（四种子原因：**已覆盖** / **非用户可操作功能** / **本机不可用** / **不可感知**，均需在"命中情况"列写明具体是哪一种）
- 🗑️ 删除（判定规则见下方「🗑️ 删除条件」，针对已有 tips 条目而非 changelog bullet，不在本表中逐条列出，单独处理）

跳过计数 = 本表中判定为「⏭️ 跳过」的行数，用于第六步摘要的完整性校验：changelog 窗口内共 M 条 bullet，新增 + 修改 + 跳过（不含针对已有条目的删除判定）应约等于 M，数量对不上说明本表本身有遗漏。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 一条 bullet 涉及多个可拆分的独立功能点（如一条 bullet 合并宣布两个不相关的新 flag） | 拆成两行分别判定 | 不强行捏合成一条 |
| bullet 数量很大（窗口跨度长，一次有 100+ 条） | 中间过程表仍逐条生成 | 不因数量大而抽样或省略——抽样等于放弃了这张表的完整性校验意义 |

### 🆕 新增条件
满足以下**全部条件**才生成新条目：
- 属于对用户操作有实质影响的功能（新 CLI flag、新子命令、新 Hook 事件、新 settings.json 设置项、新交互命令）
- **判重**：提取该功能点的所有主标识符（flag 名、设置项名、命令名、环境变量名，如 `respondToBashCommands`、`!命令`），在 `build_alias_index.py` 产出的 `ids`/`aliases` 中逐一查找——**任一命中 → 跳过，不新增**；全部未命中才算新增
- **环境可用性门**：该功能在本机 harness 下确实能跑。mac/Linux-only、Enterprise 席位或组织席位、**企业 managed 配置**、**自建网关**、cloud-SDK、claude.ai 账号、**VS Code / JetBrains 扩展专属**（本机只在终端使用 Claude Code）等本机用不了的 → 标记 `⏭️ 跳过（本机不可用）`，不占坑。⚠️ 判据是「有无硬性阻断」：条目**主体**是扩展专属功能才跳过；主体本机可用而只在某句提到扩展（如 `/plugin` 安装即时生效顺带提 VS Code 对话框），是**删掉那半句、保留条目**。反向同样成立——本机确实自建了网关，网关类条目就没有阻断，照常新增
- **可感知性门**：用户能亲眼看到该功能生效或未生效（判据与豁免见下节），否则 → 标记 `⏭️ 跳过（不可感知）`。⚠️ **四条件按上列顺序判定，先失败的那道门即定子原因**：已被环境可用性门判「本机不可用」的功能点**不再过本门**，因此也用不到本门的两条豁免——环境门是无豁免的硬闸，可用性问题一律在那里终结

#### 👁️ 可感知性门（新增前必过）

tips 的载体是 SessionStart 单条轮播——**读者读完既无法追问也无法查证**。因此条目描述的机制必须存在**用户侧可观测的验证闭环**，否则读者既确认不了它生效、也判断不了要不要配它，条目沦为纯知识陈列。

对每个待新增功能点回答一个问题：**「用户改了这个配置/用了这个功能，怎么知道它起作用了？」**

| 若答案是 | 判定 | 举例 |
|---|---|---|
| 界面/终端有可见变化（提示、徽章、面板、菜单、报错） | ✅ 通过 | 权限模式 footer 徽章、MCP 认证启动通知 |
| 有专门命令能查（`/usage`、`/permissions`、`/doctor`、`claude xxx list`） | ✅ 通过 | 缓存命中率经 `/usage` 可见 |
| 会改变用户日常会撞到的行为（原来能用现在报错、原来要确认现在不用） | ✅ 通过 | 项目级 env 收紧、权限规则语义变更 |
| 只能在 OTel 后端 / 网关日志 / stream-json 里看到 | ❌ 跳过 | 遥测类环境变量、headless 专属输出字段 |
| 是上限、超时或配额阈值（**不看默认值有多大**） | ✅ 通过 | 并发子代理上限 20、单会话搜索上限 200、WebFetch 缓存 15 分钟 |
| 静默生效，开关前后用户观察不到差别 | ❌ 跳过 | 内存压力回收、空闲看门狗、沙箱静默阻断 |
| 描述的是「兼容多种写法」或「某限制已移除」，无行为差异 | ❌ 跳过 | frontmatter 命名/布尔值兼容、硬上限移除 |
| 明确已失效的死配置 | ❌ 跳过 | changelog 自陈「不再有任何作用」的设置项 |

**两条豁免**（命中即视为通过，不受上表 ❌ 约束）：

1. **现象解释豁免** — 该条目解释的是用户会亲眼撞到的困惑现象，即使机制本身不可见。判据：能写出「你会遇到 X，原因是 Y」的句式。例：`CLAUDE_CODE_ENABLE_TODO_TOOLS` 机制不可见，但解释了「升级模型后任务清单消失」这个真实困惑。
2. **安全收紧豁免** — 该条目描述的是权限或安全边界收紧，用户会以「原来能用现在被拦」的形式撞上。例：项目级 settings.json 的 env 收紧。

> ⚠️ **不要用「高级/小众」当判据**，判据只有一条——**有没有验证闭环**。`--restricted` 很小众但一眼可见，该留；`CLAUDE_ENABLE_STREAM_WATCHDOG` 人人可设但完全静默，该跳。误按「高级」筛会连带删掉 `--restricted`、`/batch` 这类小众但真实可用的能力。

> 📌 **上限类是本节的显式例外，不要按「碰不到就跳过」处理。** 上限、超时、配额阈值**一律通过**，不看默认值有多大——这类条目的价值不在「看到它生效」而在**知道天花板存在、撞上时知道去哪调**，属速查表属性，与需要验证闭环的机制类条目不同。**残留风险已知**：它确实不满足本节的通用判据，是显式例外而非判据的自然推论，因此**不要拿它去类推其他 ❌ 档**（遥测、静默看门狗、无行为差异仍照跳）。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 功能点部分可感知、部分不可感知（如一个设置项既改界面又调遥测上限） | 只写可感知的那部分，不可感知的部分从 `body` 中略去 | 若两部分无法拆分，按可感知处理并保留条目 |
| 拿不准是否命中豁免 | 尝试写出「你会遇到 X，原因是 Y」句式——写得出即豁免 | 写不出则判 ❌ 跳过，宁缺毋滥（tips 是轮播位，占坑的成本是挤掉一条有用的） |

#### 📝 条目生成（两道门都过后执行）

**信息补全与条目信息完整性清单**：changelog 的单行描述往往只覆盖核心功能，直接照抄会产出信息不全的条目。**判定有新增条目后、生成 `body` 前，加载 `references/entry-authoring.md`** 执行其中的生成前补全（交叉关联已有 tips、提取完整参数集、补全用法示例）与生成后的**条目信息完整性清单**（键名/环境变量/版本号/多种用法/关联功能/限制说明六项）。**改已有条目而要重写 `body` 时同样加载**——六项清单里的「限制说明」等项对改写后的 body 一样适用；只做判重、或只改标题/分类不必加载。⚠️ 该清单与第五步的「完整性校验」是两回事：前者查一条条目的信息齐不齐，后者查整个文件的格式与账目，不要混称。

生成格式（每条一行 JSON，写入 tips.jsonl）：
```json
{"id":"/xxx","category":"分类","title":"🔰 标题","body":"功能：一句话说明\n效果：使用场景和收益\n例子：claude --完整命令 具体说明"}
```
- `id` 取主标识符（命令名 / flag / 功能名），无主标识符用标题 slug，全库唯一
- `body` 内用真实换行（JSON 里为 `\n`）而非字面 `\n`
- 分类从现有分类中选最匹配：`交互`、`工具`、`Hook`、`配置`、`CLI`、`集成`、`工作流与自动化`、`排障`、`Skill`、`MCP`、`高级`、`Skill·superpowers`。⚠️ **`category` 字段值不带方括号**——方括号是 `show-tip.sh` 展示时拼上的（`head = f"[{tip['category']}] …"`），写进数据会展示成 `[[交互]]`，而 `validate_tips.py` 只查四字段存在性、不校验取值，**没有任何机制拦得住**

#### 🏷️ 斜杠名存在性校验（写入前必过）

**危害不在分类标签错，在斜杠名不存在。** tips 的载体是 SessionStart 单条轮播，读者照着敲一个不存在的 `/xxx` 时既无法追问也无法查证。真实误标形态只有一种：把**内置 subagent** 写成可斜杠调用——`statusline-setup` 即此例（`agentType` 命中、`name` 不命中，只能由 Claude 以 `subagent_type` 派生，没有斜杠命令）。⚠️ 曾与它并列记载的 `init`、`security-review` **均已实测为活注册体**，那两条记载是错的，不要照抄。

⚠️ **不要试图用二进制判定「是 skill 还是命令」——该区分在 v2.1.266 已不存在**（`--help` 明写 "Skills still resolve via `/skill-name`"、`--disable-slash-commands` 的说明是 "Disable all skills"，二者是同一套注册）。为此迭代四轮判据全部被推翻，记录见 `known-issues.md`。**已有 `Skill` / `交互` 分类的历史划分不要回溯改动**，新条目按功能性质选分类。

要校验的只有一件事：**这个斜杠名在本机二进制里真实存在吗。**

```bash
python .claude/skills/sync-cc-tips/scripts/check_slash_name.py <斜杠名>
```

| `verdict` | 处置 |
|---|---|
| `command` | 斜杠名存在，按功能性质选分类。**但须看 `evidence[].context` 确认是注册体**——`registry_markers` 为空时脚本会给 `warning`，那种命中可能是 JS 解析器的无关字符串 |
| `subagent` | **不写斜杠形式**，改述为「内置 subagent」 |
| `not_found` + changelog 明确提到它 | 可能来自插件（如 `code-review`/`commit`）——确认插件名后斜杠形式**须带命名空间前缀** |
| `not_found` 且非插件 | **无结论，不等于「不存在」**：随附 skill 是惰性解包的内嵌资源，名字不以字面量存在于二进制。新增条目时不写斜杠形式；**已有条目一律不动**，列入摘要交用户实跑确认 |
| `binary_missing` | 按 `hint` 用 `(Get-Command claude).Source` 定位后传 `--binary` 重试 |

⚠️ **一手证据源是本机原生二进制，不是官方文档**（文档滞后于发布）。**脚本只取证不下结论**——`verdict` 是模式匹配结果，是否为注册体须由你看 `evidence` 判断。脚本另输出的 `action` 只是上表首列的中文回显，**不是独立信号**，以本表为准。四条取证教训（不按调用形态提取清单、不写死混淆名、常量表不算证据、正则写窄会把「存在」误判成「不存在」）已固化在 `check_slash_name.py` 的 docstring 与单测中，完整推翻记录见 `known-issues.md`「取证方法备注」。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 已知存在的名字（如 `doctor`）返 `not_found` | 混淆结构变了，用 `grep -ao '.\{60\}doctor.\{60\}' <二进制>` 宽窗口反查实际形态 | 宽窗口也查不到**不代表不存在**（随附 skill 惰性解包，见下方⚠️）——交用户实跑确认，并在 `known-issues.md` 记一行说明模式失效 |
| `verdict: command` 但带 `warning` | 加长窗口复查完整对象 | 列入摘要交用户裁决 |
| **脚本自身崩溃 / traceback / 输出非 JSON** | 跑一次 `python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_check_slash_name.py"` 区分是脚本坏了还是该名字触发了边界 | **不要因此停掉整轮**（取证失败只损失一次确认机会，与判重集不全不同）：该条按「存在性无法确认」处理——只描述功能、不写斜杠形式，并在摘要里注明「取证脚本不可用，斜杠形式已省略」交用户补确认 |

⚠️ **保守侧随改动方向而变，不是恒定的「不写斜杠形式」。** 新增条目时存在性无法确认 → 只描述功能、不写斜杠形式。**已有条目则相反**：`not_found` 是无结论而非否证，把它当否证会去删一个真实可用的功能。根因是**随附 skill 为惰性解包的内嵌资源**，名字不以 `name:"x"` 字面量存在于可执行段——`/simplify`、`/dataviz`、`/deep-research` 均实测可用而脚本一律报 `not_found`（三次误判经过见 `known-issues.md`）。**未命中既不构成删除依据，也不构成写入任何否定陈述的依据**，只能列入摘要交用户确认。

### ✏️ 修改条件
以下情况原地更新已有条目（不改变条目位置）：
- 已有条目的命令语法与 changelog 不符（如 flag 名称变更）
- 已有条目描述的行为已被新版本改变
- 已有条目的例子中使用了已不存在的 flag 或子命令
- **不修改**：仅措辞差异、风格调整、无实质差异的改动

**修改即覆盖旧语义，不追加版本沿革**：同一条目只保留最新语义，不在 `body` 里逐版本累积"v2.1.196 新增…v2.1.220 改为…"这类历史。

**长度自检**：修改后条目长度不超过全库 `body` 长度中位数的 2 倍（超出通常说明在堆历史，应压缩为当前语义）。**中位数与阈值不用手算**——`validate_tips.py` 的 `checks.length` 直接给 `median`/`threshold`/`over_count`/`over[]`。

⚠️ **这条只约束改动增量，不是全库门禁。** 判定看的是「本轮把它推超了没有」，不是「它现在超没超」：

| 改动前 | 改动后 | 处理 |
|---|---|---|
| 阈值内 | 超阈值 | **本轮推超的，必须压回阈值内** |
| 已超阈值 | 更长了 | 只压缩本轮新加的部分，原有内容不动（外科手术式改动） |
| 已超阈值 | 未再变长 | 不处理——存量长条目不是本轮的责任 |
| 未被本轮触及 | — | 完全不看，哪怕它超了 3 倍 |

按全库状态执行会每轮被无关存量卡住——库里长期存在一批未触及的超阈值存量（实测比例见 `references/measurements.md`）。合并残影产生的长条目同理豁免——两条并一条本就该更长。

### 🗑️ 删除条件
以下情况将在第四步变更预览时列出待删条目：
- changelog 明确标注 `Removed`、`Deprecated`、`no longer available`
- 功能已被完全移除（不是"有了更好的替代"，而是彻底消失）
- **可感知性回溯**：changelog 表明某已有条目描述的机制已退化为不可感知（如原本会弹提示的行为改为静默生效），按「👁️ 可感知性门」重判，判 ❌ 则列为待删
- **不删除**：changelog 只是新增了替代功能，旧功能仍可用

> 存量库中**未被本轮 changelog 触及**的不可感知条目不在本 skill 的自动删除范围内——本 skill 只处理 changelog 驱动的差异。批量清理属于人工发起的一次性维护（用户主动发起的全量复审），走「⏭️ 跳过」判据人工复核后由用户拍板，不由本 skill 自行扫库删除。

### 格式校验（每条写入前执行）

生成的条目须满足：

- 合法 JSON 单行，含 `id`/`category`/`title`/`body` 四字段，`id` 全库唯一
- `body` 含「功能」「效果」「例子」三段，**「功能」「效果」各恰好 1 次**（> 1 说明同一条内语义重复，需合并）
- 「例子」不受次数限制——允许分平台拆成多行「例子（Windows）：」「例子（Linux/Mac）：」。⚠️ **这是预留写法，不依赖任何活体用例**（原先援引的 `--add-dir` 已改写为单行分号并列，勿再据此查证）。保留理由是分平台命令差异确实存在，届时不该被校验挡住
- 例子中的可执行形式必须是**三种形态之一**，禁止裸缩写：① CLI 完整命令 `claude --xxx`；② 斜杠命令 `/xxx`；③ skill 完整触发形式 `/xxx:yyy` 或注明注册来源

前三项由脚本校验（第五步统一执行，也可在写入前先跑一次自查）：

```bash
python .claude/skills/sync-cc-tips/scripts/validate_tips.py
```

> ⚠️ **不要用「字段段数 > 4 即报错」替代 `field_dup` 检查**——那会误伤合法的多段例子写法。脚本已按行首匹配实现该区分，`test_validate_tips.py::TestFieldDup` 锁住了它。

- **如果校验不通过** → 修正后再写入，不跳过也不写入不合格条目；若无法修正则跳过该条并在摘要中注明

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 「条目信息完整性清单」（见 `references/entry-authoring.md`）某项在 changelog 原文中确实找不到对应信息（如未提供 settings.json 键名） | 交叉检索该功能关联的已有 tips 条目或同版本其他条目上下文推断 | 若仍无法确认，跳过该项校验并在摘要中注明"信息不全，需人工补充"，不编造数值 |
| 同一功能点同时命中🆕新增与✏️修改条件（如新 flag 替换了旧 flag 的部分行为） | 优先按✏️修改处理，原地更新旧条目，不重复新增 | 若归属仍有歧义，在变更预览中单独列出并说明歧义原因，交由用户在 CHECKPOINT 处裁决 |

### 🚦 零变更总闸（唯一判定点）
若本轮识别结果为 **0 新增 + 0 修改 + 0 删除**（包括全部 bullet 均判定为 ⏭️ 跳过的情况）→ 跳过 tips.jsonl 写入、跳过第四步 CHECKPOINT、跳过第五步的完整性校验（无写入则无可校验），**但仍须执行第五步的「推进同步锚点」小节**，把 `.last-synced-version` 推进到本轮处理到的最新版本并单独提交（commit message 注明"仅推进同步锚点，无 tips.jsonl 变更"），避免下次运行重新扫描这段已确认无实质变更的区间。仅输出「本次 changelog 检查完成，所有功能点已在 tips.jsonl 覆盖或非用户可操作，已推进同步锚点至 v{最新版本}」后结束。第四步、第六步中对"0 变化"的提及均以本节为准，不重复判断。

## 第四步 — 写入 tips.jsonl

> 🔴 **CHECKPOINT**（仅在变更数 > 0 时触发，0 变化场景见「🚦 零变更总闸」）：写入前展示变更预览——列出「📥 新增 N 条 / ✏️ 修改 N 条 / 🗑️ 删除 N 条 / ⏭️ 跳过 N 条」及每条标题；**第二步检出的残影候选在此单独列一栏**（每条给出 `覆盖方 ⊇ 被覆盖方` 与重叠度），其后再列 📚 同主标识符聚集栏，然后用 `AskUserQuestion` 发起确认：
> - `question`: "以上是本次识别到的变更（N 新增 / N 修改 / N 删除 / N 跳过），是否写入 tips.jsonl 并继续后续提交流程？"
> - `options`（**`stats.pending_review > 0` 时必须给出合并选项**，否则该裁决点无处落地）：
>   - 「确认写入并提交」（推荐）
>   - 「写入并同时合并残影」——**仅在 `stats.pending_review > 0` 时出现**（即存在未登记豁免的待裁决候选），选项描述里写明会删哪条、并入哪条
>   - 「取消，不做任何修改」
> - 选「确认写入并提交」→ 继续执行写入，残影保持原样，随后进入第五步完整性校验与锚点推进
> - 选「写入并同时合并残影」→ 写入时一并执行合并（**被删条目独有的信息必须并入保留方**，不可直接丢弃），第五步调用 `validate_tips.py` 时须把被合并掉的 id 一并传入 `--removed-ids=`，以触发 `orphan_ref` 反查
> - 选「取消，不做任何修改」或用户通过 Other 输入自定义文本（视为非明确同意） → **立即停止**，输出「操作已取消，tips.jsonl 未修改」，不执行任何写入或提交，`.last-synced-version` 也不更新

**两栏的完整格式示例、末列标注映射与召回边界见 `references/preview-format.md`——`candidates > 0` 或 `shared_main_groups > 0` 时加载。** ⚠️ 触发条件是 `candidates` 而非 `pending_review`：候选全部已登记豁免时 `pending_review` 为 0，但残影栏**仍须照常列出**（见下条），而末列那两种标注的映射只在该文件里。⚠️ 反过来，两者**都为 0** 时该栏**整栏略去，不写「无」占位**——这条规则本身留在此处常驻，因为那种情形恰好落在上述加载条件之外，写进该 reference 就等于永不生效。三条不可违反的约束在此重述：

- **末列标注绑死 `detect_residue.py` 字段，模型不参与判断**——不要凭判断写「← 建议合并」。合并与否是用户在 CHECKPOINT 的决定，预先宣告结论会诱导确认，与检查点存在的意义相抵触
- **已登记豁免的组合仍照常列出**，静默隐藏会让人误以为库里没有残影，裁决权始终在用户
- **残影栏与聚集栏不合并**——前者是过阈值的可执行裁决项，后者只是主题聚集视野，无对应自动化动作，不进 `AskUserQuestion` 的 options

### 写入机制（回滚基线 + 批量写法 + 写入失败处理）

**CHECKPOINT 已确认、即将实际写入时加载 `references/write-mechanics.md`**——它含三块内容：回滚基线的复检命令与三条分支处置（**含「脏基线已在前置校验获同意」时直接放行、不得二次询问**）、条目多于两三条时改用一次性 Python 脚本按 `id` 增删改（JSONL 转义会让字面 `Edit` 失效）、以及 Edit 报错与 `/tmp` 不可见两类写入失败的处理。🚦 零变更总闸触发时第四步整体跳过，不必加载。

⚠️ 回滚基线的 git 干净度探测在「执行前置校验」已做过一次，写入前**仍须复检**——两次之间隔着抓取、判定、生成三个阶段，工作区状态可能已被别的操作改变。

## 第五步 — 写入后完整性校验

```bash
python .claude/skills/sync-cc-tips/scripts/validate_tips.py \
  --expect-entries {旧条目数 + 新增 − 删除} \
  --removed-ids={本轮删除的 id 逗号分隔}     # 本轮无删除时整个 flag 省略
```

⚠️ **`--removed-ids` 的值以 `-` 开头时（flag 类 id）必须用等号形式**，空格分隔会被 argparse 当成 flag。

⚠️ **值以 `/` 开头时（斜杠命令类 id）在 Git Bash / MSYS 下必须前置 `MSYS_NO_PATHCONV=1`**，否则 shell 会把 `/design-界面设计草图` 重写成 `C:/Program Files/Git/design-界面设计草图`，反查的是不存在的 id。脚本已能识破（`orphan_ref` 判失败并在 `mangled` 里回报改写前后的形态），但**别指望靠它兜底**——正确写法是：

```bash
MSYS_NO_PATHCONV=1 python .claude/skills/sync-cc-tips/scripts/validate_tips.py \
  --expect-entries <改动后应有的条数> --removed-ids=/design-界面设计草图,/dataviz-图表与可视化设计
```

两个坑同时踩到时（既有 `-` 开头又有 `/` 开头的 id）等号形式与 `MSYS_NO_PATHCONV=1` 都要加，它们互不替代。

**`ok: true` 才可进入第六步。** `ok: false` → 看 `failed` 数组定位，按下表修复并重跑；修复无效或原因不明 → 停止流程，不进入第六步，**不推进锚点**。

> **基线豁免（仅当第二步基线体检就已 `ok: false` 且用户选了继续）**：脚本**没有**忽略项参数，`ok` 必定仍为 `false`，此时不能按上句停流程——那会让每一轮都卡死。改为**逐项与第二步留存的基线 JSON 对比**：
>
> | 对比结果 | 判读 |
> |---|---|
> | 该项在基线中已存在，且 `errors` 条目集合未扩大 | 存量问题，本轮不负责，放行 |
> | 该项在基线中已存在，但本轮多出了新的 `errors` 条目 | **本轮引入的**，按下表修复 |
> | 该项基线中为 `ok`、本轮变 `failed` | **本轮引入的**，按下表修复 |
>
> 逐项对比而非整体放行——基线里 `schema` 挂着不代表本轮新写的条目可以缺字段。`count_match` 与 `orphan_ref` **永不适用豁免**：前者算的是本轮增删账，后者查的是本轮删除引发的悬挂引用，两者都与存量无关。

| `failed` 中的项 | 含义 | 处置 |
|---|---|---|
| `line_count` | 有空行或有行不以 `{` 开头 | 定位并删除该行 |
| `json_valid` | 某行 JSON 语法错误（常见于手工编辑引号/逗号） | 按 `errors[].line` 修正；无法修正则回退该行到改前内容并在摘要注明 |
| `schema` | 四字段缺失或为空 | 按 `errors[].missing` 补齐 |
| `id_unique` | id 重复 | 按 `errors[].lines` 合并或改名——id 重复会让按 id 操作的写入脚本改错条目 |
| `field_dup` | 「功能」或「效果」出现次数 ≠ 1 | 合并重复段落 |
| `body_shape` | 三段不全 | 补齐缺失段 |
| `orphan_ref` | 被删条目的标识符仍被其他条目引用 | 按 `hits[].referrer` 修正引用方措辞，去掉对已删条目的指向 |
| `count_match` | 增删账不平（`delta` 给出差值） | 以实测 `actual` 为准，回查第四步哪一条漏改或多改 |

> 本表行序与脚本 `checks` 的键序一致，只略去恒为 `ok` 的 `length`（说明见下）。

> `length` 项**恒为 `ok`**，不会进 `failed`——它只报告超阈值清单（`over`），因为长度自检约束的是改动增量而非全库状态（判据见第三步「长度自检」）。本轮把某条推超阈值时，按那一节的矩阵压回。

> 📌 **本步骤不含「同步文档数字」，该机制已废除，不要重新加回。** 展示性文件里的 tips 条目总数曾靠每轮 sync 手工追平，结果是长期失准且无人察觉。**根治办法是移除派生值而非加固同步流程**：数字已全部删除，同步点归零（事故规模见 `references/measurements.md`）。**凡能从脚本输出即时读出的数值，正文一律不复述**——包括命令示例里的 `--expect-entries`，写占位符而非具体条数。

**⛔ 不要重新往任何文件添加条目总数。** 读者从分类列表已能感知规模，具体数字对任何决策都无影响，而每多一处就多一个失准点。需要当前条目数时读脚本输出的 `entries`——**即时可算的值不该被写死在文档里**。

### 推进同步锚点

校验通过后，把本轮处理到的**最新版本号**写入 `.last-synced-version`（不含 `v` 前缀）：

```bash
echo "{最新版本}" > .claude/skills/sync-cc-tips/.last-synced-version
```

⚠️ **写入时机必须在校验通过之后、提交之前**——提前写会导致校验失败中止时锚点已前移，下次运行跳过这段未处理区间，造成永久漏同步。

| 场景 | 是否写入 | 说明 |
|---|---|---|
| 正常完成（有变更，校验 `ok: true`） | ✅ 写入本轮最新版本 | 主路径 |
| 零变更总闸触发 | ✅ 写入本轮最新版本 | 见第三步该节，单独提交并注明「仅推进同步锚点」 |
| 用户在第四步 CHECKPOINT 取消 | ❌ 不写入 | 未做任何改动，锚点保持原值 |
| 第一步输出 `advance_anchor: false`（`--limit` 模式） | ❌ 不写入 | 范围受限的临时查看，不代表真实同步进度 |
| **写入命令失败**（磁盘只读、路径不存在、重定向报错） | ❌ 视为未写入 | **不要继续提交**——tips.jsonl 已改而锚点没动，下轮会重扫同一区间并把本轮条目全部判为已覆盖，表面无害但掩盖了锚点损坏。立即报告「锚点写入失败，本轮改动未提交」，`cat` 该文件确认实际内容后由用户决定是手工写入还是回滚本轮改动 |
| 校验 `ok: false` 而中止 | ❌ 不写入 | 数据未落定，下次需重新处理该区间 |

**版本号升级不在本 skill 定义**——由 `commit-cc-plugin` 第二步按 AGENTS.md 触发矩阵统一处理，本 skill 只交接事实：本次改动落在 `plugins/optimus-devops-plugin/hooks/` 内，届时应升该插件的两份 `plugin.json`（Patch）。

## 第六步 — 展示摘要并提交

按以下格式输出执行摘要：

```
✅ sync-cc-tips 完成 · v{锚点版本} → v{最新版本}
   本轮扫描 {version_count} 个版本 / {bullet_count} 条 bullet

📥 新增  N 条
  · [分类] 条目标题
  · ...

✏️  修改  N 条
  · [分类] 条目标题 → 修改说明
  · ...

🗑️  删除  N 条
  · [分类] 条目标题（删除原因）
  · ...

⏭️  跳过  N 条（已覆盖 / 非用户可操作 / 本机不可用 / 不可感知，按子原因分列条数）

📊 条目总数：{旧数} → {新数}（即时统计，不写入任何文档）
✅ 完整性校验：validate_tips.py {九项全过／除已获用户裁决放行的存量项 `<项名>` 外全过}（含增删账平、孤儿引用{无命中／本轮无删除不适用}）
🔖 版本：待 commit-cc-plugin 按 AGENTS.md 触发矩阵判定（改动落在 hooks/ 内，预期 Patch）
🔖 同步锚点：v{锚点版本} → v{最新版本}
🧺 stash 归还：本轮曾 stash tips.jsonl 改动，请执行 `git stash pop` 取回（**前置校验未 stash 时整行略去，不写「无」占位**）

---
进入提交流程...
```

**「最新版本」一律取 `fetch_changelog.py` 的 `latest_available`（changelog 里存在的最新版），不是 `range[1]`。** `--limit N` 模式下两者不同——`range[1]` 只是本轮取到的最新一个，用它会让摘要看起来「已同步到最新」而实际没有。同理，`bullet_count` 与本表的「新增 + 修改 + 跳过」应约等（差值说明中间过程表有遗漏，见第三步）。

摘要展示完毕后，立即调用 `commit-cc-plugin` skill 完成提交推送。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| `commit-cc-plugin` skill 不可用 | 提示用户手动执行：`git add` → `git commit` → `git push` | 输出待提交的完整 diff 供用户参考 |
| 提交被 hook 拦截（pre-commit 失败） | 报告 hook 输出，不强制绕过 | 停止，提示用户修复后手动重试提交 |

## ⛔ 不要做什么（反例黑名单）

| 反模式 | 原因 | 替代做法 |
|---|---|---|
| 把 changelog 里所有更新项都加入 tips.jsonl | tips 面向用户实用技巧，不是版本记录——内部重构、bug fix、依赖升级不应出现 | 只加对用户操作有实质影响的功能（新 flag、新命令、新设置项） |
| 只要是新 flag / 新设置项就加进来 | 存在大量用户永远观察不到效果的开关（遥测、静默看门狗），以及本机根本没有对象的开关（企业席位、managed 配置、自建网关），加进来只是占轮播位 | 按顺序过「环境可用性门」再过「👁️ 可感知性门」：本机没有对象的归前者，答不出「用户怎么知道它起作用了」的归后者。**唯一例外是上限/超时/配额阈值**，该档一律新增 |
| 用「高级 / 小众」筛掉条目 | 会误伤 `--restricted`、`/batch` 这类小众但一眼可见的真实能力 | 唯一判据是有无验证闭环，与功能是否高级无关 |
| 只用条目标题判断是否已覆盖 | tips.jsonl 每条含完整正文，次级功能点只出现在功能/效果/例子字段而非标题 | 必须扫描 tips.jsonl **全文**，用主标识符（flag 名/设置项名/命令名）做精确匹配 |
| 0 变化时提交 tips.jsonl 改动 | 无实质变更却产生 commit，污染 git 历史 | 触发「🚦 零变更总闸」跳过 Step 4 与完整性校验；**但仍须推进 `.last-synced-version` 并为该锚点单独提交**——这不是"无意义 commit"，不推进会导致下次重复扫描同一区间 |
| 修改 show-tip.sh 脚本逻辑 | 脚本逻辑不在本 skill 职责范围内 | 只修改 tips.jsonl 数据文件 |
| 删除旧功能条目，但该功能仍可用（只是有了替代方案） | 用户可能仍在用旧方式 | 仅在 changelog 明确标注 Removed/Deprecated 时删除 |
| 往任何文档写入 tips 条目总数 | 派生值写死在展示文案里必然失准，且失准是静默的——没有任何机制会告诉你某处数字已经过期（历史事故规模见 `references/measurements.md`）。读者从分类列表已能感知规模，具体数字不影响任何决策 | 一律用不含数字的表述（「技巧智能轮播」）；需要数字时读 `validate_tips.py` 输出的 `entries` |
| 抓取失败后继续执行后续步骤 | 基于空数据的操作可能误删现有条目 | 第一步 `ok: false` → 按 `next` 走，`stop` 则立即停止，不执行任何写入 |
| 在本 skill 内自行决定版本号怎么升 | 规则的唯一依据是 AGENTS.md 触发矩阵，写第二份必然与之分叉——曾长期误写为升 marketplace 顶层 version 且漏升 `.claude-plugin/plugin.json` | 交给 `commit-cc-plugin` 第二步统一处理，本 skill 只交接「改动落在 `plugins/optimus-devops-plugin/hooks/` 内」这一事实 |
| `cp tips.jsonl /tmp/xxx.bak` 做备份 | Bash 工具是 Git Bash、Python 是 Windows 原生解释器，`/tmp` 对后者不可见——`cp` 报成功而实际读不到，备份形同虚设且无任何警示 | tips.jsonl 已入库，git 本身就是回滚基线：`git status --short` 确认干净、出错时 `git restore`、对比用 `git show HEAD:<path>` |
| 在 SKILL.md 里重写取数命令，或按上述思路改 `fetch_changelog.py` 的降级链 | 三类写法都已实测证伪（管道吞退出码、302 回落同域当第二跳、等 N 秒重试同一命令），共同病根是**故障域与首跳重合**。逐条实测见 `references/measurements.md` | 调用 `fetch_changelog.py`，正确写法已被 `test_fetch_changelog.py::TestHopsAreIndependent` 锁住。**新增跳必须换主机名**，不是换工具、不是换 URL 字符串 |
| 判重时退回手工 grep 扫全文 | 收录裸英文词会让别名集合膨胀到通用词量级，任何功能点都能「命中」→ 判重恒为已覆盖、新增恒为 0，属不报错的静默失效（实测见 `references/measurements.md`） | 只用 `build_alias_index.py`；脚本不可用时停止流程，不要用手工方案顶替 |
| 把规则写成「某日确认」「某日反转」 | 规则的效力来自它是规则，不来自决策日期。给判据盖上日期会让它读起来像一次临时决定，且日期逐轮累积就成了版本考古——正文该讲「现在按什么办」，不该讲「哪天决定的」 | 判据、约束、警示一律写成**无日期的规范条款**。**实测数值、实跑快照、某次清理的规模一律不进正文**——它们回答「结论怎么来的」，执行时用不到，落 `references/measurements.md` 并在那里标注观测日期与当时样本量；正文只留判据本身加一句指针。缺陷时间线归 `known-issues.md`（逐轮叙事进 `known-issues-archive.md`），版本时间线归 `CHANGELOG.md` |
| 让 `check_slash_name.py` 直接下结论、或据 `verdict` 就写斜杠形式而不看 `evidence` | `name:"init"` 这类短名会命中 JS 解析器的无关字符串。脚本给 `warning` 时尤须复查——**「命令跑通且数字属实」≠「输出能支撑那个判断」** | `verdict` 只是模式匹配结果，看 `evidence[].context` 与 `registry_markers` 自行确认是注册体 |

> `.claude/` 下的 skill 文件本身不触发版本号升级（遵循 CLAUDE.md 规范）

## 📁 配套文件

| 文件 | 用途 | 何时读写 |
|---|---|---|
| `scripts/fetch_changelog.py` | 取 changelog + 两跳降级 + 锚点截断 + 连通性分诊 | 第一步调用 |
| `scripts/build_alias_index.py` | 构建 `{ids, aliases}` 判重集 | 第二步调用 |
| `scripts/detect_residue.py` | 库内残影候选召回 | 第二步调用 |
| `scripts/validate_tips.py` | 九项格式与完整性校验 | 第二步（取基线）、第五步（验写入） |
| `scripts/check_slash_name.py` | 斜杠名存在性取证 | 第三步按需调用（每个待写入的斜杠名一次） |
| `scripts/test_*.py` | 上述脚本的单测（本机无 pytest，用 `python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py"`） | 改动脚本后必跑 |
| `.last-synced-version` | 同步锚点（纯版本号，无 `v` 前缀） | 第一步读、第五步写 |
| `references/entry-authoring.md` | 新增条目的信息补全与「条目信息完整性清单」 | 第三步判定有新增、生成 `body` 前加载 |
| `references/preview-format.md` | CHECKPOINT 残影栏与聚集栏的格式示例、标注映射、召回边界 | 第四步 `candidates > 0` 或 `shared_main_groups > 0` 时加载 |
| `references/write-mechanics.md` | 回滚基线、批量写法、写入失败处理 | 第四步 CHECKPOINT 已确认、即将写入时加载；零变更总闸触发时不加载 |
| `references/measurements.md` | 各判据与阈值背后的实测数值、实跑快照、清理规模、证伪实验 | **正常执行不加载**；质疑或改动某个阈值/禁令时加载 |
| `known-issues.md` | 待处理项 + 反复发作的教训 + 取证方法备注（封顶 150 行） | **本 skill 执行中发现自身缺陷时追加一行**；满 3 条「待处理」在**下一次真实同步之后**触发优化循环 |
| `known-issues-archive.md` | 已解决条目的逐轮叙事与历史修复记要 | **正常执行与派发评审时均不加载**；查某条历史缺陷的来龙去脉时才打开 |
| `test-prompts.json` | 验证 prompt 与期望行为 | darwin-skill 优化循环的验证素材；**改动 SKILL.md 流程后须复查相关 `expected` 是否失效** |

⚠️ **临时脚本不进本表。** 第四步的 `_apply_sync.py` 是一次性产物，用后即删（下划线前缀即为此标记）。本表只列长期存在的正式脚本。

⚠️ **本表不写条目数与测试数。** 它们是可即时统计的派生值，写死必然失准——第五步整套「同步文档数字」机制正因此被废除，同一原则适用于本表自身。需要数字时即时跑命令。

⚠️ **改流程时不要只改 SKILL.md**：删除或重命名某个步骤后，`test-prompts.json` 中指向该步骤的 `expected` 会变成恒定失败的失效断言；把内嵌命令抽成脚本时，断言了具体命令写法的 `expected` 同样失效。历次流程改动牵连到的具体断言 id 见 `references/measurements.md`。

