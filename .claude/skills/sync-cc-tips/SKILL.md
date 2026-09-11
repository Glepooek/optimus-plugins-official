---
name: sync-cc-tips
description: 从 Claude Code 最新 changelog 自动同步 tips.jsonl：按环境可用性与可感知性双重门禁新增条目、修正过时内容、删除已废弃功能，写入后做四重完整性校验并推进同步锚点，最后调用 commit-cc-plugin 提交。触发场景：用户说 "/sync-cc-tips"、"更新tips"、"同步tips"、"tips需要更新"、"从changelog更新tips"、"sync tips"。可附带版本数量参数，如 "/sync-cc-tips 5" 表示只看最近5个版本。
metadata:
  version: "2.2.1"
  author: desktop client team
compatibility: 需要 Python 3（标准库，无第三方依赖）——第一步取 changelog 走 urllib 两跳（raw.githubusercontent.com → api.github.com），两跳均失败时降级为 WebFetch；第三步斜杠名取证需本机 claude 二进制（默认 npm 全局安装路径，可用 --binary 指定）。脚本经 Bash 调用 Windows 原生 Python，二者文件系统视图不同，临时文件一律用仓库内相对路径。流程末尾调用 commit-cc-plugin skill 完成提交推送。
allowed-tools: Bash WebFetch Read Write Edit Grep AskUserQuestion Skill
disable-model-invocation: true
---

# /sync-cc-tips

从 Claude Code 最新 changelog 同步 tips.jsonl：**抓取、判定、写入、校验全自动，但写入前必须经一次人工确认**，确认后展示摘要并提交。

⚠️ **本流程含 3 个阻塞式人工确认点，不得跳过：**

| 位置 | 触发条件 | 跳过的后果 |
|---|---|---|
| 第一步 | 待处理版本 > 30 个（无论锚点是否命中） | 可能误处理过大范围 |
| 第二步 | tips.jsonl 为空 | 把异常空文件当作全新初始化，静默丢失全库 |
| 第四步 | 变更数 > 0，写入前 | 未经确认改写唯一真源 |

📌 **本 skill 只能由人显式触发，不支持无人值守调度**——frontmatter 的 `disable-model-invocation: true` 是有意为之：它既阻止模型自主调用，也意味着 `/loop` 等计划触发会把本 skill 当作纯文本而不执行（官方行为，v2.1.196 起）。三个确认点因此始终有人应答，不存在「无人响应该怎么办」的分支。

⚠️ 该字段是本仓**唯一**超出六字段规范的顶层字段（见 `.claude/rules/skill-conventions.md`），已知偏离、有意保留，Codex 侧严格校验器可能报 `Unexpected fields in frontmatter`。**不要顺手删掉它来"修规范"**——删了本 skill 就会变成可被模型自主拉起。


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

`build_alias_index.py` 只收录**带语法标记**的标识符（斜杠命令含 `/plugin:skill` 命名空间、长短 flag、大写环境变量），并做斜杠/双横前缀剥离、连字符与下划线互换、小写三类归一化；此外 `SEMANTIC_ALIASES` 显式登记字面无关的等价组（`/cost`≡`/usage`≡`/stats`、`/review`≡`/code-review`、`/plugin`≡`/plugins`、`/undo`≡`/rewind`）——这 4 组历史重复正是因归一化覆盖不到别名而产生。

> ⚠️ **不要改回收录裸英文词**（失效原理见文末黑名单）。`test_build_alias_index.py::TestExtractRejectsNoise` 已锁住该行为。

`detect_residue.py` 补齐判重的盲区：判重是单向的（changelog → 已有条目），不检查**已有条目之间互相覆盖**。召回需同时满足主标识符相同 + `功能：` 段落 bigram 达到阈值包含关系。

> ⚠️ **输出是待裁决候选，不是判定结果。** 2026-09-04 在当时 276 条库上实测：人工确认的真残影（`/doctor` 那两条互为详略版本）只有 **0.263**，而非残影的 `MCP-资源列出 ⊇ MCP-服务器` 却有 **0.333**——两类在数值上交叠，纯词频无法可靠区分。阈值按召回定为 0.25，宁可多召回几个让人看。（276 是当次实测样本量，属历史取证，**不随库存变化更新**。）残影候选在第四步预览中单独列出交用户裁决，**不要让脚本或模型自行删除**。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 文件不存在 / 脚本报路径错 | 确认路径 `plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl` 是否正确 | 停止整个流程，报告路径错误，不做任何修改 |
| `validate_tips.py` 报 `entries: 0` | 🔴 CHECKPOINT：停下询问用户是否为全新初始化场景 | 若用户确认，继续（视为无旧条目）；否则停止 |
| `validate_tips.py` 有 `failed` 项 | 报告失败项，询问是否先修复存量问题再同步 | 用户选择继续则**原样留存这份基线 JSON**，第五步按「基线豁免」判读（见第五步） |
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
| Added GitLab merge request badge to footer... | （无带语法标记的标识符——`GitLab`/`footer` 是裸英文词，索引有意不收） | 索引查不到，按语义人工核对已有「GitLab 支持扩展」条目 | ⏭️ 跳过（已覆盖） |

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
- 在 tips.jsonl **全文**中，该功能点的所有主标识符（flag 名、设置项名、命令名、环境变量名）在 `ids`/`aliases` 中均未命中
- **环境可用性门**：该功能在本机 harness 下确实能跑。mac/Linux-only、Enterprise 席位、cloud-SDK、claude.ai 账号等本机用不了的 → 标记 `⏭️ 跳过（本机不可用）`，不占坑
- **可感知性门**：用户能亲眼看到该功能生效或未生效（判据与豁免见下节），否则 → 标记 `⏭️ 跳过（不可感知）`

#### 👁️ 可感知性门（新增前必过）

tips 的载体是 SessionStart 单条轮播——**读者读完既无法追问也无法查证**。因此条目描述的机制必须存在**用户侧可观测的验证闭环**，否则读者既确认不了它生效、也判断不了要不要配它，条目沦为纯知识陈列。

对每个待新增功能点回答一个问题：**「用户改了这个配置/用了这个功能，怎么知道它起作用了？」**

| 若答案是 | 判定 | 举例 |
|---|---|---|
| 界面/终端有可见变化（提示、徽章、面板、菜单、报错） | ✅ 通过 | 权限模式 footer 徽章、MCP 认证启动通知 |
| 有专门命令能查（`/usage`、`/permissions`、`/doctor`、`claude xxx list`） | ✅ 通过 | 缓存命中率经 `/usage` 可见 |
| 会改变用户日常会撞到的行为（原来能用现在报错、原来要确认现在不用） | ✅ 通过 | 项目级 env 收紧、权限规则语义变更 |
| 只能在 OTel 后端 / 网关日志 / stream-json 里看到 | ❌ 跳过 | 遥测类环境变量、headless 专属输出字段 |
| 默认值远超正常使用量，永远碰不到 | ❌ 跳过 | 上限类阈值（默认 200 次搜索、20 并发） |
| 静默生效，开关前后用户观察不到差别 | ❌ 跳过 | 内存压力回收、空闲看门狗、沙箱静默阻断 |
| 需要企业 managed 配置 / 自建网关 / 组织席位才有对象 | ❌ 跳过 | 组织白名单、企业 tips 投放 |
| 描述的是「兼容多种写法」或「某限制已移除」，无行为差异 | ❌ 跳过 | frontmatter 命名/布尔值兼容、硬上限移除 |
| 明确已失效的死配置 | ❌ 跳过 | changelog 自陈「不再有任何作用」的设置项 |

**两条豁免**（命中即视为通过，不受上表 ❌ 约束）：

1. **现象解释豁免** — 该条目解释的是用户会亲眼撞到的困惑现象，即使机制本身不可见。判据：能写出「你会遇到 X，原因是 Y」的句式。例：`CLAUDE_CODE_ENABLE_TODO_TOOLS` 机制不可见，但解释了「升级模型后任务清单消失」这个真实困惑。
2. **安全收紧豁免** — 该条目描述的是权限或安全边界收紧，用户会以「原来能用现在被拦」的形式撞上。例：项目级 settings.json 的 env 收紧。

> ⚠️ **不要用「高级/小众」当判据**，判据只有一条——**有没有验证闭环**。`--restricted` 很小众但一眼可见，该留；`CLAUDE_ENABLE_STREAM_WATCHDOG` 人人可设但完全静默，该跳。2026-09-07 清理 17 条即按此标准，误按「高级」筛会连带删掉 `--restricted`、`/batch`。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 功能点部分可感知、部分不可感知（如一个设置项既改界面又调遥测上限） | 只写可感知的那部分，不可感知的部分从 `body` 中略去 | 若两部分无法拆分，按可感知处理并保留条目 |
| 拿不准是否命中豁免 | 尝试写出「你会遇到 X，原因是 Y」句式——写得出即豁免 | 写不出则判 ❌ 跳过，宁缺毋滥（tips 是轮播位，占坑的成本是挤掉一条有用的） |

**识别流程**：
1. 提取该功能点的主标识符列表（如 `respondToBashCommands`、`!命令`）
2. 在 `ids`/`aliases` 中逐一查找
3. **任一命中 → 跳过，不新增**；全部未命中 → 标记为新增

**信息补全（生成前必须执行）**：
changelog 的单行描述往往只覆盖核心功能，生成前需补充完整信息：

1. **交叉关联已有 tips** — 在 tips.jsonl 全文中搜索与新功能相关的已有条目，提取可关联的信息：
   - 新功能是否与已有功能形成工作流？（如「可点击附件」与「@ 引用」配合）
   - 新功能是否涉及已有命令/flag？（如「可读会话名」涉及 `-n`、`/rename`、`--resume`）
   - 新功能是否属于已有配置项的子集或扩展？

2. **提取完整参数集** — 从 changelog 原文中提取：
   - settings.json 键名（camelCase 形式）
   - 环境变量名（全大写下划线形式）
   - 支持的值/选项（如 small/medium/large、true/false）
   - 是否为建议性指引（advisory）vs 硬性限制（enforced cap）
   - 相关 CLI flag 或交互命令

3. **补全用法示例** — 为每个功能点提供完整的使用方式：
   - CLI 命令必须是完整可执行形式：`claude --xxx`
   - 配置项需给出 settings.json 键名和示例值
   - 交互命令需给出触发方式和预期结果（`/xxx:yyy` 或注册来源）
   - 若有多种使用方式（CLI + 交互 + 配置），全部列出
   - **不写裸缩写 / 不可执行简称**：`/tdd`、`debugging`、`parallel-agents` 这类敲不出来、无处注册的标识符一律不得作为例子

**完整性校验（生成后必须执行）**：
生成条目后，对照检查以下清单，任一项缺失则补充：

| 检查项 | 要求 |
|--------|------|
| settings.json 键名 | 配置类功能必须包含 camelCase 键名 |
| 环境变量名 | 有环境变量的功能必须包含全大写形式 |
| 版本号 | 标注引入版本（如 v2.1.196） |
| 多种用法 | 有 CLI + 交互两种方式的，全部列出 |
| 关联功能 | 与已有 tips 有配合关系的，互相引用 |
| 限制说明 | advisory vs enforced、仅 -p 模式、仅特定平台等 |

生成格式（每条一行 JSON，写入 tips.jsonl）：
```json
{"id":"/xxx","category":"[分类]","title":"🔰 标题","body":"功能：一句话说明\n效果：使用场景和收益\n例子：claude --完整命令 具体说明"}
```
- `id` 取主标识符（命令名 / flag / 功能名），无主标识符用标题 slug，全库唯一
- `body` 内用真实换行（JSON 里为 `\n`）而非字面 `\n`
- 分类从现有分类中选最匹配：`[交互]`、`[工具]`、`[Hook]`、`[配置]`、`[CLI]`、`[集成]`、`[工作流与自动化]`、`[排障]`、`[Skill]`、`[MCP]`、`[高级]`、`[Skill·superpowers]`

#### 🏷️ 斜杠名存在性校验（写入前必过）

**危害不在分类标签错，在斜杠名不存在。** tips 的载体是 SessionStart 单条轮播，读者照着敲一个不存在的 `/xxx` 时既无法追问也无法查证。2026-09-04 全量核对查出 3 条问题：`statusline-setup`（内置 subagent，**没有斜杠命令**）、`init`、`security-review`。

⚠️ **不要试图用二进制判定「是 skill 还是命令」——该区分在 v2.1.266 已不存在**（`--help` 明写 "Skills still resolve via `/skill-name`"、`--disable-slash-commands` 的说明是 "Disable all skills"，二者是同一套注册）。为此迭代四轮判据全部被推翻，记录见 `known-issues.md`。**已有 `[Skill]` / `[交互]` 标签的历史划分不要回溯改动**，新条目按功能性质选分类。

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

⚠️ **保守侧随改动方向而变，不是恒定的「不写斜杠形式」。** 新增条目时存在性无法确认 → 只描述功能、不写斜杠形式。**已有条目则相反**：`not_found` 是无结论而非否证，把它当否证会去删一个真实可用的功能——2026-09-11 就据此错误提请删除 `/simplify` 与 `/dataviz`，被用户实跑推翻（详见 `known-issues.md`）。**未命中不构成删除依据**，只能列入摘要交用户确认。

### ✏️ 修改条件
以下情况原地更新已有条目（不改变条目位置）：
- 已有条目的命令语法与 changelog 不符（如 flag 名称变更）
- 已有条目描述的行为已被新版本改变
- 已有条目的例子中使用了已不存在的 flag 或子命令
- **不修改**：仅措辞差异、风格调整、无实质差异的改动

**修改即覆盖旧语义，不追加版本沿革**：同一条目只保留最新语义，不在 `body` 里逐版本累积"v2.1.196 新增…v2.1.220 改为…"这类历史。

**长度自检**：修改后条目长度不超过全库 `body` 长度中位数的 2 倍（超出通常说明在堆历史，应压缩为当前语义）。**中位数与阈值不用手算**——`validate_tips.py` 的 `checks.length` 直接给 `median`/`threshold`/`over_count`/`over[]`（2026-09-09 实测 194.0 / 388.0 / 20）。

⚠️ **这条只约束改动增量，不是全库门禁。** 判定看的是「本轮把它推超了没有」，不是「它现在超没超」：

| 改动前 | 改动后 | 处理 |
|---|---|---|
| 阈值内 | 超阈值 | **本轮推超的，必须压回阈值内** |
| 已超阈值 | 更长了 | 只压缩本轮新加的部分，原有内容不动（外科手术式改动） |
| 已超阈值 | 未再变长 | 不处理——存量长条目不是本轮的责任 |
| 未被本轮触及 | — | 完全不看，哪怕它超了 3 倍 |

按全库状态执行会每轮被无关存量卡住：2026-09-09 实测 268 条中 20 条超阈值（7.5%），其中 18 条属未触及的存量。合并残影产生的长条目同理豁免——两条并一条本就该更长。

### 🗑️ 删除条件
以下情况将在第四步变更预览时列出待删条目：
- changelog 明确标注 `Removed`、`Deprecated`、`no longer available`
- 功能已被完全移除（不是"有了更好的替代"，而是彻底消失）
- **可感知性回溯**：changelog 表明某已有条目描述的机制已退化为不可感知（如原本会弹提示的行为改为静默生效），按「👁️ 可感知性门」重判，判 ❌ 则列为待删
- **不删除**：changelog 只是新增了替代功能，旧功能仍可用

> 存量库中**未被本轮 changelog 触及**的不可感知条目不在本 skill 的自动删除范围内——本 skill 只处理 changelog 驱动的差异。批量清理属于人工发起的一次性维护（如 2026-09-07 那次 280→263），走「⏭️ 跳过」判据人工复核后由用户拍板，不由本 skill 自行扫库删除。

### 格式校验（每条写入前执行）

生成的条目须满足：

- 合法 JSON 单行，含 `id`/`category`/`title`/`body` 四字段，`id` 全库唯一
- `body` 含「功能」「效果」「例子」三段，**「功能」「效果」各恰好 1 次**（> 1 说明同一条内语义重复，需合并）
- 「例子」不受次数限制——允许分平台拆成多行「例子（Windows）：」「例子（Linux/Mac）：」。⚠️ **这是预留写法，截至 2026-09-09 全库 0 条在用**（原先援引的 `--add-dir` 已改写为单行分号并列，援引已失效，勿再据此查证）。保留理由是分平台命令差异确实存在，届时不该被校验挡住
- 例子中的可执行形式必须是**三种形态之一**，禁止裸缩写：① CLI 完整命令 `claude --xxx`；② 斜杠命令 `/xxx`；③ skill 完整触发形式 `/xxx:yyy` 或注明注册来源

前三项由脚本校验（第五步统一执行，也可在写入前先跑一次自查）：

```bash
python .claude/skills/sync-cc-tips/scripts/validate_tips.py
```

> ⚠️ **不要用「字段段数 > 4 即报错」替代 `field_dup` 检查**——那会误伤合法的多段例子写法。脚本已按行首匹配实现该区分，`test_validate_tips.py::TestFieldDup` 锁住了它。

- **如果校验不通过** → 修正后再写入，不跳过也不写入不合格条目；若无法修正则跳过该条并在摘要中注明

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| "完整性校验"清单某项在 changelog 原文中确实找不到对应信息（如未提供 settings.json 键名） | 交叉检索该功能关联的已有 tips 条目或同版本其他条目上下文推断 | 若仍无法确认，跳过该项校验并在摘要中注明"信息不全，需人工补充"，不编造数值 |
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

**残影栏示例**（无候选时整栏略去，不要写「无」占位）。下例前两行是 2026-09-09 现网实跑结果，第三行为示意——用于展示 `← 待裁决` 的写法，当前库中并不存在该组合：

```
🔗 残影候选 3 条（脚本召回，需你裁决；非本轮 changelog 引入）
  · 0.333  MCP-资源的列出与读取 ⊇ MCP-服务器        ← 已知误报，建议保留
  · 0.250  MCP-认证启动通知 ⊇ MCP-服务器            ← 已知误报，建议保留
  · 0.263  〈覆盖方〉 ⊇ 〈被覆盖方〉                 ← 待裁决
```

**末列标注绑死脚本字段，模型不参与判断**——只有两种取值，按 `detect_residue.py` 输出直接映射：

| 脚本输出 | 标注 |
|---|---|
| `known_non_residue: true` | `← 已知误报，建议保留`（并在其后附 `exempt_reason`） |
| 无该字段 | `← 待裁决` |

⚠️ **不要自行改写这一列**（如凭判断写「← 建议合并」）。合并与否是用户在 CHECKPOINT 的决定，预先宣告结论会诱导确认，与检查点存在的意义相抵触。**已登记豁免的组合仍照常列出**——静默隐藏会让人误以为库里没有残影，裁决权始终在用户。

**同主标识符聚集栏**（消费 `detect_residue.py` 的 `shared_main` 字段，`shared_main_groups > 0` 时列出，否则整栏略去）：

```
📚 同主标识符聚集 4 组（仅供参考，本轮不要求处置）
  · @       ── @-符号快速引用 / @-提及其他会话
  · agent   ── agent-配置 / agent-指定代理 / Agent-派生工作流
  · memory  ── Memory-自动记忆 / Memory-工作流
  · vscode  ── VSCode-会话分组 / VSCode-不活跃会话归档
```

**它与残影栏是两个不同的信号，不要合并成一栏**：残影栏是「功能描述重叠已过阈值」的**可执行**裁决项；聚集栏只说明「这几条讲的是同一个主标识符」，重叠度未达阈值，多数是正常的分主题拆分（如上表四组皆是）。**已在残影栏出现的组整组跳过**——上例即 2026-09-09 现网实跑结果：`shared_main_groups: 5`，其中 `mcp` 组已被残影栏覆盖，故此处只余 4 组。避免同一批 id 在预览里出现两次。

聚集栏不进 `AskUserQuestion` 的 options——它没有对应的自动化动作，只是给用户一个「库里哪些主题在长期累积」的视野。冗余是历次 sync 逐次累积的，每次单看都不重复，只有整库分组扫描才看得见。

⚠️ **聚集栏的召回有已知边界，不要当成穷举。** `main_identifier()` 取 id 的 **ASCII 前缀**分组，共同概念出现在后缀时聚不到一起——库里三条 code-review 条目（`/code-review-审查当前改动`、`requesting-code-review-…`、`receiving-code-review-…`）分属三个不同的 main，不会同组。这是分组方式的取舍（前缀分组无歧义、零误报），不是缺陷；**看到聚集栏为空不等于库里没有主题冗余**。

### 回滚基线（写入前确认，不额外备份）

tips.jsonl 是已入库文件，**git 本身就是回滚基线**，无需另存副本：

```bash
git status --short plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl   # 应为空（干净）
```

- 输出为空 → 直接改，出错时 `git restore <path>` 即可回到本轮起点
- 输出非空 → 该文件已有未提交改动，先弄清来源再动手；此时 `git restore` 会连带丢弃那些改动
- 需要与改动前对比时用 `git show HEAD:plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl`

⚠️ **不要 `cp` 到 `/tmp` 做备份**——`cp` 会报成功而 Python 读不到，备份形同虚设且无任何警示（失效原理见文末黑名单）。凡需跨 Bash 与 Python 传递的临时文件，一律放仓库内相对路径。

### 写入方式

条目多于两三条时，不要逐条 `Edit` 字面匹配——JSONL 单行内含大量转义（`\n`、中文引号、`\"`），字面匹配极易失败。改为写一个一次性 Python 脚本按 `id` 增删改：

```
Write: .claude/skills/sync-cc-tips/scripts/_apply_sync.py   （下划线前缀标记临时脚本）
```

脚本要点：`json.loads` 逐行读入 → 按 `id` 匹配处理 → `json.dumps(ensure_ascii=False)` 写回，`io.open(..., newline="\n")` 固定换行符；结尾自校验「旧数 − 删除 + 新增 == 实得」并在不符时 `sys.exit` 报错。**用后必须删除该脚本**，不要留在 `scripts/` 里污染正式脚本目录。

```
Edit: plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl   （改动 ≤ 2 条时直接用）
```

- **新增**：追加到文件末尾，每条为一行合法 JSON 对象
- **修改**：原地替换对应条目所在行，保持位置不变
- **删除**：移除对应条目所在行

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| Edit 工具报错（文件锁 / 权限不足） | 等待 2 秒后重试一次 | 停止流程，报告错误路径，不继续第五步 |
| Edit 报 `String to replace not found`，但内容肉眼看着一致 | JSONL 行内转义（`\n`、`\"`）导致字面匹配失效，改用上方「写入方式」的 Python 脚本按 `id` 操作 | 停止流程，报告哪几条无法定位 |
| 写入后读回内容与预期不符 | 重新执行 Edit | 停止流程，提示用户手动检查文件状态 |
| 删除条目后空行残留 | 再次定位并删除残留在行 | 在摘要中标注"空行可能残留，请人工确认" |
| Python 报 `FileNotFoundError` 读某个 Bash 刚创建的文件 | 该文件在 `/tmp` 等 Git Bash 专有路径下，Windows 原生 Python 看不到；改用仓库内相对路径重新生成 | 用 `git show HEAD:<path>` 取基线替代临时文件 |

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
  --expect-entries 247 --removed-ids=/design-界面设计草图,/dataviz-图表与可视化设计
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

> 📌 **本步骤原含「同步文档数字」，2026-09-07 起废除。** 曾有 6 个展示性文件把 tips 条目总数冗余写进文案，每轮 sync 手工追平，导致两次失准事故（其中两处数字从未被任何一轮 sync 更新过，长期停在 425 而真实值为 276）。**根治办法是移除派生值而非加固同步流程**：6 处数字已全部删除，同步点归零。

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
✅ 完整性校验：validate_tips.py 九项全过（含增删账平、孤儿引用{无命中／本轮无删除不适用}）
🔖 版本：待 commit-cc-plugin 按 AGENTS.md 触发矩阵判定（改动落在 hooks/ 内，预期 Patch）
🔖 同步锚点：v{锚点版本} → v{最新版本}

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
| 只要是新 flag / 新设置项就加进来 | 存在大量用户永远观察不到效果的开关（遥测、静默看门狗、企业专属、默认值碰不到的上限），加进来只是占轮播位——2026-09-07 因此一次性清掉 17 条 | 过「👁️ 可感知性门」：答不出「用户怎么知道它起作用了」就跳过 |
| 用「高级 / 小众」筛掉条目 | 会误伤 `--restricted`、`/batch` 这类小众但一眼可见的真实能力 | 唯一判据是有无验证闭环，与功能是否高级无关 |
| 只用条目标题判断是否已覆盖 | tips.jsonl 每条含完整正文，次级功能点只出现在功能/效果/例子字段而非标题 | 必须扫描 tips.jsonl **全文**，用主标识符（flag 名/设置项名/命令名）做精确匹配 |
| 0 变化时提交 tips.jsonl 改动 | 无实质变更却产生 commit，污染 git 历史 | 触发「🚦 零变更总闸」跳过 Step 4 与完整性校验；**但仍须推进 `.last-synced-version` 并为该锚点单独提交**——这不是"无意义 commit"，不推进会导致下次重复扫描同一区间 |
| 修改 show-tip.sh 脚本逻辑 | 脚本逻辑不在本 skill 职责范围内 | 只修改 tips.jsonl 数据文件 |
| 删除旧功能条目，但该功能仍可用（只是有了替代方案） | 用户可能仍在用旧方式 | 仅在 changelog 明确标注 Removed/Deprecated 时删除 |
| 往任何文档写入 tips 条目总数 | 派生值写死在展示文案里必然失准——历史上 6 处同步点漏了两轮，两处长期停在 425（真实 276）。读者从分类列表已能感知规模，具体数字不影响任何决策 | 一律用不含数字的表述（「技巧智能轮播」）；需要数字时读 `validate_tips.py` 输出的 `entries` |
| 抓取失败后继续执行后续步骤 | 基于空数据的操作可能误删现有条目 | 第一步 `ok: false` → 按 `next` 走，`stop` 则立即停止，不执行任何写入 |
| 在本 skill 内自行决定版本号怎么升 | 规则的唯一依据是 AGENTS.md 触发矩阵，写第二份必然与之分叉——曾长期误写为升 marketplace 顶层 version 且漏升 `.claude-plugin/plugin.json` | 交给 `commit-cc-plugin` 第二步统一处理，本 skill 只交接「改动落在 `plugins/optimus-devops-plugin/hooks/` 内」这一事实 |
| `cp tips.jsonl /tmp/xxx.bak` 做备份 | Bash 工具是 Git Bash、Python 是 Windows 原生解释器，`/tmp` 对后者不可见——`cp` 报成功而实际读不到，备份形同虚设且无任何警示 | tips.jsonl 已入库，git 本身就是回滚基线：`git status --short` 确认干净、出错时 `git restore`、对比用 `git show HEAD:<path>` |
| 在 SKILL.md 里重写取数命令，或按上述思路改 `fetch_changelog.py` 的降级链 | 三个已证伪的写法：`curl … \| awk …`（管道吞掉 curl 退出码，降级链永不启动）；`github.com/<repo>/raw/…` 当第二跳（302 回落 raw 域，字节等价对**内容**成立、对**可达性**不成立，`--max-redirs 0`/`-f` 对 302 仍返 `exit 0`）；「等 N 秒重试同一条命令」（同主机同工具，故障域与首跳完全重合）。实测数据见 `known-issues.md` | 调用 `fetch_changelog.py`，正确写法已被 `test_fetch_changelog.py::TestHopsAreIndependent` 锁住。**新增跳必须换主机名**，不是换工具、不是换 URL 字符串 |
| 判重时退回手工 grep 扫全文 | 2026-09-04 用 `\b[a-z][a-zA-Z]{3,}\b` 收录裸英文词，集合膨胀到数千个通用词，任何功能点都能「命中」→ 判重恒为已覆盖、新增恒为 0，属不报错的静默失效 | 只用 `build_alias_index.py`；脚本不可用时停止流程，不要用手工方案顶替 |
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
| `known-issues.md` | 真实使用中暴露的问题台账 | **本 skill 执行中发现自身缺陷时追加一行**；累积满 3 条「待处理」触发 darwin-skill 优化循环 |
| `test-prompts.json` | 验证 prompt 与期望行为 | darwin-skill 优化循环的验证素材；**改动 SKILL.md 流程后须复查相关 `expected` 是否失效** |

⚠️ **临时脚本不进本表。** 第四步的 `_apply_sync.py` 是一次性产物，用后即删（下划线前缀即为此标记）。本表只列长期存在的正式脚本。

⚠️ **本表不写条目数与测试数。** 它们是可即时统计的派生值，写死必然失准——2.0.0 版为此废除了第五步整套「同步文档数字」机制（6 处同步点归零），同一原则适用于本表自身。需要数字时即时跑命令。

⚠️ **改流程时不要只改 SKILL.md**：删除或重命名某个步骤后，`test-prompts.json` 中指向该步骤的 `expected` 会变成恒定失败的失效断言；把内嵌命令抽成脚本时，断言了具体命令写法的 `expected` 同样失效。2026-09-07 废除「同步文档数字」时 id 1/3/4 需同步更新，2.2.0 抽三个脚本时 id 2/6/7/10/12 需同步更新。

