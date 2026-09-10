# 实施计划：session-handoff skill

**日期：** 2026-09-10
**Spec：** [`docs/superpowers/specs/2026-09-10-session-handoff-design.md`](../specs/2026-09-10-session-handoff-design.md)
**参照实现：** `E:\Waiyan\appskills\fltrp-session-handoff` v2.1.0
**状态：** 待执行

---

## 0. 全局约束

### 0.1 硬性规则

1. **单一真源**——SKILL.md 只在 `plugins/optimus-session-plugin/skills/session-handoff/` 维护一份，不在 `.claude/skills/` 另存副本
2. **不建符号链接**——`.kiro/skills/` 与 `.agents/skills/` 只镜像 `.claude/skills/` 下的自用 skill。`plugins/` 下的产物由 harness 插件机制分发，建了反而会被 pre-commit 的反向检查判为悬空
3. **两份 `plugin.json` 同值**——同一次改动内一起写入 `1.0.0`，不是一方抄另一方
4. **marketplace 条目内不写 `version`**——会被 `plugin.json` 静默覆盖，且本地 source 会触发官方不一致警告
5. **分段写入**——SKILL.md 预计 160-180 行、`templates.md` 预计 200+ 行，两者都必须先 Write 骨架再多次 Edit 填充，禁止单次输出全文
6. **不写插件根 README**——10 个现有插件条目中仅 `optimus-mcp-servers` 有（且不含 skill）。`doc-conventions.md` 的六章节规范是对 skill 级 README 的要求
7. **不照抄参照实现的 frontmatter**——它是 `name`/`version`/`description`/`author`/`tags`/`category` 平铺结构，本仓要求 `metadata` 嵌套 + `compatibility` + `allowed-tools` 六字段

### 0.2 校验命令

```bash
# 提交门禁（版本同值 + 镜像完整）
sh .githooks/pre-commit

# 官方插件校验
claude plugin validate plugins/optimus-session-plugin

# 两处 marketplace 是否同步（注意已知差异，见 0.4）
python -c "
import json, io
a={p['name'] for p in json.load(io.open('.claude-plugin/marketplace.json',encoding='utf-8'))['plugins']}
b={p['name'] for p in json.load(io.open('.agents/plugins/marketplace.json',encoding='utf-8'))['plugins']}
only_claude = a - b
assert only_claude == {'cangjie-skill'}, f'Claude 侧多出非预期插件: {only_claude - {chr(99)+chr(97)+chr(110)+chr(103)+chr(106)+chr(105)+chr(101)+chr(45)+chr(115)+chr(107)+chr(105)+chr(108)+chr(108)}}'
assert b - a == set(), f'Codex 侧多出: {b - a}'
print(f'两处同步（Claude {len(a)} / Codex {len(b)}，差异仅外部源 cangjie-skill）')
"
```

⚠️ **不要用 `assert a == b`**——见 0.4。

### 0.3 版本规则

本次改动落在四处，按 `AGENTS.md` 触发矩阵：

| 对象 | 值 | 依据 |
|---|---|---|
| `.claude-plugin/plugin.json` | `1.0.0` | 新插件起始号 |
| `.codex-plugin/plugin.json` | `1.0.0` | 同上，同值 |
| `SKILL.md` 的 `metadata.version` | `1.0.0` | 新 skill 起始号 |
| `.claude-plugin/marketplace.json` 顶层 | `14.0.0` → `14.1.0` | 新增插件 = Minor |

⚠️ `.agents/plugins/marketplace.json` **无顶层 `version` 字段**（实测顶层键只有 `name`/`interface`/`plugins`），**不要凭空添加**。

### 0.4 实施前已实测的三处环境事实

**执行时不必重新确认，但也不要假设它们仍然成立——若与实际不符，以实际为准并在报告中说明。**

| # | 事实 | 对实施的影响 |
|---|---|---|
| 1 | 两处 marketplace 插件数**不等**：Claude 10 / Codex 9 | 差的是外部 url 源 `cangjie-skill`（不在 `plugins/` 下，Codex 无对等能力）。校验脚本**必须**按 0.2 的写法排除它，用 `assert a==b` 会被已知差异误报 |
| 2 | Codex `category` 受控词表现有 9 个取值：`Backend`/`Decision`/`DevOps`/`Frontend`/`MCP`/`Media`/`Product`/`Productivity`/`QA` | 会话交接取 **`Productivity`**，不新造词 |
| 3 | 两份 marketplace 格式不同 | 见任务 1 的对照表，**不要互抄** |

### 0.5 已批准的决定

| 项 | 决定 | 来源 |
|---|---|---|
| 插件命名 | `optimus-session-plugin` | 旧版已批准，本次不复议 |
| 交接物结构 | **三层分文件**（progress / summaries / insights） | 本次批准 |
| 写入时机 | **仅显式触发**，不做静默追写 | 本次批准 |
| 第三层定位 | 由 fltrp 的「逐轮对话」改为「习得与核验」 | 上两条的连带推论，见 spec 决策 2 |
| `docs/sessions/` 入库 | **入库**。skill 在输出里提示「如不希望入库，可加入 .gitignore」，不代为决定 | 旧版已批准 |
| 配对校验 skill | **不做**。为低频场景造刹车是另一种过度设计 | 旧版已批准 |

---

## 1. 任务总览

| # | 任务 | 优先级 | 产出 | 阻塞关系 |
|---|---|---|---|---|
| 1 | 插件脚手架 + 两处 marketplace | P0 | 2 份 plugin.json、2 处条目、顶层升 14.1.0 | 无 |
| 2 | `references/templates.md` 三层模板 | P0 | 1 个文件 | 依赖 1 |
| 3 | SKILL.md 主体 | P0 | ≤180 行 | 依赖 2（正文引用模板章节名） |
| 4 | CHANGELOG + test-prompts + skill README | P1 | 3 个文件 | 依赖 3 |
| 5 | 自举验证（保存路径） | P0 | 本会话交接物三层 | 依赖 3 |
| 6 | 恢复验证（新会话） | P0 | 测试结论 | 依赖 5，**需用户开新会话** |
| 7 | 多分支/多人路径验证 | P1 | 测试结论 | 依赖 3 |
| 8 | darwin-skill 评分 | P1 | 评分结果 | 依赖 3、4 |
| 9 | 按测试结果修正 | P0 | 修订版 | 依赖 6、7、8 |

**关键路径**：1 → 2 → 3 → 5 → 6 → 9。任务 6 需要你开新会话配合，是唯一无法单会话内完成的环节。

⚠️ **任务 2 先于任务 3**——与旧 plan 相反。理由：SKILL.md 正文要按章节名引用 `templates.md`（如"格式见 templates.md『progress.md 模板』章节"），模板先定稿才不会写出悬空引用。参照实现的 SKILL.md 正是靠这类引用把体量压下来的。

---

## 任务 1：插件脚手架 + 两处 marketplace（P0）

### 目标

新插件目录可被两个 harness 识别，`sh .githooks/pre-commit` 与 `claude plugin validate` 均通过。

### 两份 marketplace 格式不同，不要互抄

实测差异（执行前已核对）：

| | `.claude-plugin/marketplace.json` | `.agents/plugins/marketplace.json` |
|---|---|---|
| 顶层键 | `name` / `description` / **`version`** / `owner` / `plugins` | `name` / `interface` / `plugins`（**无 version**） |
| 条目 `source` | 字符串 `"./plugins/xxx"` | 对象 `{"source":"local","path":"./plugins/xxx"}` |
| 条目其他字段 | `description` | `policy`（installation/authentication）+ `category` |
| 插件数 | 10（含外部 url 源 `cangjie-skill`） | 9 |

⚠️ **只有 Claude 侧有顶层 `version` 要升**（`14.0.0` → `14.1.0`）。Codex 侧没有该字段，不要凭空添加。

⚠️ **`category` 取 `Productivity`**（受控词表，见 0.4 #2），不新造词。

### 步骤

**1.1** 建目录：

```bash
mkdir -p plugins/optimus-session-plugin/{.claude-plugin,.codex-plugin}
mkdir -p plugins/optimus-session-plugin/skills/session-handoff/references
```

**1.2** 写 `.claude-plugin/plugin.json`（字段照 `optimus-prd-plugin`，白名单见 `.githooks/check_plugin_versions.py` 的 `CLAUDE_ALLOWED_KEYS`）：

```json
{
  "name": "optimus-session-plugin",
  "version": "1.0.0",
  "description": "跨会话交接：会话结束前分三层保存进度与决策，新会话恢复上下文接着干",
  "author": { "name": "optimus", "url": "https://www.optimus.cn" },
  "homepage": "https://github.com/Glepooek/optimus-plugins-official",
  "repository": "https://github.com/Glepooek/optimus-plugins-official",
  "license": "MIT"
}
```

**1.3** 写 `.codex-plugin/plugin.json`（额外含 `skills` 与 `interface` 段）：

```json
{
  "name": "optimus-session-plugin",
  "version": "1.0.0",
  "description": "跨会话交接：会话结束前分三层保存进度与决策，新会话恢复上下文接着干",
  "skills": "./skills/",
  "author": { "name": "optimus", "url": "https://www.optimus.cn" },
  "homepage": "https://github.com/Glepooek/optimus-plugins-official",
  "repository": "https://github.com/Glepooek/optimus-plugins-official",
  "license": "MIT",
  "interface": {
    "displayName": "Optimus Session",
    "shortDescription": "跨会话交接工具",
    "longDescription": "跨会话交接：会话结束前分三层保存进度与决策（进度与待办 / 关键决策 / 习得与核验），新会话恢复上下文接着干",
    "developerName": "Optimus",
    "category": "Productivity",
    "capabilities": ["Skills"],
    "defaultPrompt": ["交接一下当前工作", "继续上次的工作"]
  }
}
```

⚠️ 两份的 `description` 必须一致——它们是同一事实的两个 harness 视图。

**1.4** `.claude-plugin/marketplace.json`：顶层 `version` 升 `14.1.0`，`plugins` 数组追加条目（**不含 `version`**）

**1.5** `.agents/plugins/marketplace.json`：`plugins` 数组追加条目，`source` 用对象形式，`category: "Productivity"`，**顶层不动**

### 验证

```bash
sh .githooks/pre-commit                                   # 两份 plugin.json 同值
claude plugin validate plugins/optimus-session-plugin     # 无 warning
# marketplace 同步检查用 0.2 的脚本（已排除 cangjie-skill）
```

对应 spec 验收项 1、2、3、4、6。

---

## 任务 2：`references/templates.md` 三层模板（P0）

### 目标

三层交接物的完整模板定稿，供 SKILL.md 按章节名引用。

### 为什么设 references（与旧 plan 的差异）

旧版设计是单文件六段，模板短，内联即可。改为三层后每层各有 frontmatter + 段落结构 + 示例，全部内联会把 SKILL.md 推到 300 行以上。参照实现在 v2.0.0 正因同样原因把模板外移（SKILL.md 662 → 342 行，降 48%）。

### 章节结构（SKILL.md 将按这些标题引用，定稿后不要改名）

```
# 交接物模板
## progress.md 模板          ← 含 frontmatter / 会话块 / 待办队列
### 待办队列写入检查清单       ← 7 项，完整采纳参照实现
## summaries.md 模板         ← 四维度：关键决策 / 方案权衡 / 遗留风险 / 待验证的假设
## insights.md 模板          ← 三维度：已核验的事实 / 踩坑记录 / 本轮习得
## 追加语义                   ← 同任务第二次交接：会话块追加、待办队列覆写
## 各层的取舍规则             ← 哪段可空、空了整段删、后两层可整个文件不建
```

⚠️ **不要照抄参照实现 `templates.md` 的章节**——它含 `init.sh 模板`、`feature_list.json 生成规则`、`artifacts.json 格式`、`踩坑沉淀` 四节，对应的机制本 skill 全不采纳（spec 对照表 #13/#14/#15/#16）。抄进来就是无消费方的死文档。

### 三个必须写进模板的硬约束

| # | 约束 | 为什么 |
|---|---|---|
| 1 | 待办队列**整段覆写**，其余段落追加 | 待办是当前状态而非历史。参照实现每个 Session 块各带一份队列、靠 `tail -30` 读末尾，本 skill 写明覆写以免读者误留历次快照 |
| 2 | 空维度**整段删除**，不写「（无）」 | 占位符比缺失更糟——下轮要花时间确认是真没有还是忘了写 |
| 3 | `summaries.md` / `insights.md` 全空则**整个文件不创建** | 纯执行性会话只产 progress 是正常的。强制凑齐会让后两层充满空洞内容，降低信噪比。**这条与参照实现相反**（它的 Red Flag 把"只更新 progress"列为错误），差异原因见 spec 第五节末 |

### 验证

- 章节标题与上方列表逐字一致（SKILL.md 的引用依赖它）
- 三个硬约束各有明确表述，不是暗示
- 无参照实现的四节死内容（`init.sh` / `feature_list` / `artifacts` / `pitfalls`）

对应 spec 第五节。

---

## 任务 3：SKILL.md 主体（P0）

### 目标

≤180 行，覆盖保存/恢复两模式与三层结构，frontmatter 六字段合规。

⚠️ **行数上限从旧 plan 的 150 放宽到 180**——三层结构比单文件六段多出「分层读取顺序」「三层各自的必填判定」两块内容，且待办队列 7 项检查清单要落进正文。150 行会逼出两种坏结果：砍掉检查清单，或把约束压缩成暗示。

### 分段写入顺序

⚠️ 全局规则要求分段，禁止单次输出全文。按此顺序，每段一次 Edit：

```
3.1 Write 骨架：frontmatter + 标题 + 三层职责表 + 模式判定表      (~35 行)
3.2 Edit 追加：HARD GATE 四项 + 路径推导命令                      (~30 行)
3.3 Edit 追加：模式 A 保存（采集 + 三层内容约束 + 收尾输出）        (~40 行)
3.4 Edit 追加：待办队列 7 项检查清单                              (~15 行)
3.5 Edit 追加：模式 B 恢复（定位 + 分层读取顺序 + 复述后停下）      (~30 行)
3.6 Edit 追加：Red Flags 表（12 条）                             (~20 行)
```

### 路径推导必须写成可执行命令

spec 第三节的推导规则要落成 SKILL.md 里的实际命令，不能只写文字描述：

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
DEFAULT=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
DEFAULT=${DEFAULT:-$BRANCH}          # 无 origin 时视当前分支为默认
AUTHORS=$(git log --format=%an | sort -u | wc -l)
WHO=$(git config user.name)
```

- `BRANCH` ≠ `DEFAULT` → 路径含 `<branch>/` 段
- `AUTHORS` > 1 → 文件名含 `.<user>` 后缀

⚠️ **禁止硬编码 `master` 或 `main`**——两者在真实项目中都常见，写死会给另一半用户凭空多一层目录。

⚠️ **变量名避开 `USER`**——参照实现用了 `USER=$(git config user.name)`，但 `USER` 是 shell 环境变量，覆盖它在某些环境下有副作用。用 `WHO` 或 `GIT_USER`。

### 模式判定不看文件系统

⚠️ 参照实现按 `docs/sessions/{分支}/` 是否存在决定进 Initializer 还是 Coder。**本 skill 必须按用户意图判定**——目录已存在但用户这次要保存新一轮的情况下，存在性判定会误判为恢复。

### 必须落进正文的五条约束

来自 spec，且是本 skill 最容易失守的地方：

| # | 约束 | 对应 spec |
|---|---|---|
| 1 | **不重复 git/CHANGELOG 已记录的内容**——「已完成」写 git 里看不到的 | 四节·三层内容的核心约束 |
| 2 | **空维度删掉整段，不写「（无）」；后两层全空则不建文件** | 五节·各段取舍规则 |
| 3 | **⏸️ 阻塞项必须附原因**，「先不做」项也须附原因 | 五节·检查清单第 3/6 项 |
| 4 | **恢复后复述三件事就停下**，不自动开工 | 决策 6 |
| 5 | **不自动提交**，输出含 gitignore 提示 | 决策 4 |

### 收尾输出的固定措辞

```
交接物已写入 docs/sessions/<任务目录>/（progress / summaries / insights 三份）。
如不希望它进入版本库，可将 docs/sessions/ 加入 .gitignore。
```

⚠️ 实际只产 1 或 2 个文件时，措辞须相应调整为实际产出的文件名——**不要固定写"三份"**，那会与「后两层可不创建」的规则冲突。

### 验证

```bash
wc -l plugins/optimus-session-plugin/skills/session-handoff/SKILL.md   # ≤180
grep -c "master\|main" plugins/optimus-session-plugin/skills/session-handoff/SKILL.md  # 只应出现在说明性文字里，不在命令中
```

frontmatter 六字段对照 `.claude/rules/skill-conventions.md`。对应 spec 验收项 11、12、19。

---

## 任务 4：CHANGELOG + test-prompts + skill README（P1）

### 4.1 CHANGELOG.md

```markdown
# Changelog

## [1.0.0] - 2026-09-10

### Added
- 跨会话交接 skill 首个版本，保存与恢复两种模式
- 三层交接物分职责：progress（做了什么 + 待办队列）/ summaries（为什么这么选）/ insights（习得、踩坑、已核验的事实）
- 交接物路径按「分支 × 协作者数」运行时推导，单分支单人时自动退化为扁平路径
- 待办队列四档优先级（🔴高 / 🟡中 / 🔵低 / ⏸️阻塞），阻塞项强制附原因
- 待办队列 7 项写入检查清单，把「有没有漏记待办」变成可逐项核对
- 恢复时分层读取：progress 与 insights 必读，summaries 仅在要改动上轮决定时读

### 设计说明
- 参照 fltrp-session-handoff v2.1.0，采纳其三层分职责结构、按人隔离与待办队列四档；不采纳静默追写、init.sh、feature_list.json、artifacts.json、pitfalls 闭环与 stop hook（理由见 spec 对照表）
- 第三层由参照实现的「逐轮对话记录」改为「习得与核验」——逐轮记录依赖静默追写才成立，仅显式触发时回溯补写既不可靠也无价值

### 已知限制
- **多人协作场景未经实测**——本仓只有单一提交者，`.{user}` 后缀展开逻辑仅经静态审查
- **非 master 默认分支未经实测**——本仓默认分支为 master，`git symbolic-ref` 回退逻辑仅经静态审查
```

⚠️ **「已知限制」两条必须写**——不假装验证过。这是 spec 风险表里标为「确定发生」的项。

### 4.2 test-prompts.json

照 `optimus-prd-plugin/skills/prd-creator/test-prompts.json` 格式（`id` / `prompt` / `expected`）。四条对应 spec 第八节：

| id | prompt 要点 | expected 要点 |
|---|---|---|
| 1 | "交接一下"，会话有决策有踩坑 | 三层齐全；空维度整段删除而非「（无）」；输出含 gitignore 提示；**不自动提交** |
| 2 | "交接一下"，纯执行性会话（照计划做完、无决策无踩坑） | **只产 `progress.md`**，不强行创建 summaries/insights |
| 3 | "继续上次的工作"，存在多个任务目录 | 列出选项让用户选，不默认取最新；`summaries` 不在「继续推进」场景下读；复述三件事后停下 |
| 4 | **指令冲突**："快速交接，别问了"，但会话内容极少 | 告知「本次无实质可交接内容」，既不无视指令追问，也不生成空洞占位符敷衍 |

第 2 与第 4 条是关键——测的正是本 skill 最容易失守的地方：为了显得「完整」而输出无价值内容。

### 4.3 skill README

按 `.claude/rules/doc-conventions.md` 的六章节写。

⚠️ **不写插件根 README**——那一层无此惯例（见 0.1 #6）。

### 验证

```bash
python -m json.tool plugins/optimus-session-plugin/skills/session-handoff/test-prompts.json > /dev/null && echo "JSON 合法"
```

---

## 任务 5：自举验证 — 保存路径（P0）

### 目标

用这个 skill 交接「这个 skill 的实现」本身，同时检验保存路径的五个验收项。

### 检查项

| 检查项 | 期望 | spec 验收项 |
|---|---|---|
| 路径 | `docs/sessions/2026-09-10-session-handoff-impl/`，**无 `master/` 层、无 `.anyu` 后缀** | 9 |
| 三层文件 | 本次会话有决策（三层结构、写入时机）也有踩坑 → 三个文件都应产出 | 7 |
| 段落 | 必填段齐全，空维度整段删除而非「（无）」 | 7 |
| 「已完成」内容 | 不是 commit message 的复述 | 18 |
| 待办队列 | 按 7 项清单逐条自查过，⏸️ 项附原因 | 12 |
| git 状态 | 交接物为 untracked，**未生成 commit** | 17 |

```bash
git status --short docs/sessions/     # 应为 ?? 而非已提交
```

### 补充：验收项 8 需另造场景

验收项 8（纯执行性会话只产 `progress.md`）**本次自举验证覆盖不到**——本次实现过程有大量决策与踩坑，必然产三层。需另造一个纯执行场景（如"照 plan 的任务 1 建好脚手架"这样一段无决策的执行）单独验证。

⚠️ 不要因为自举验证通过就认为验收项 8 也过了。两者测的是相反的路径：一个测「该产三层时产齐」，一个测「不该产时不硬凑」。

### 补充：验收项 13 需第二次交接

待办队列覆写语义（验收项 13）需要同一任务目录下的**第二次**交接才能验证。可在任务 9 修正后再交接一次，检查旧队列是否被覆写而非保留。

### 为什么用自举而非造假数据

造一份人工交接物只能验证「格式对不对」，验证不了「skill 自己写出来的东西够不够用」。自举同时暴露两者，且失败反馈直接。

---

## 任务 6：恢复验证 — 新会话（P0，需你配合）

### 目标

最小可行测试：**交接物能不能让一个无上下文的会话接着干**。这是全部验收项里唯一能判定成败的一条，前面都是结构性检查。

### 测试设计

- **单一变量**：新会话除交接物外不给任何提示
- **执行**：任务 5 保存后，你开一个新会话，只说「继续上次的工作」
- **成功判定**：新会话能说出任务是什么、下一步做什么，与本会话实际意图一致，且无需你补充背景
- **失败判定**：新会话问出「这个任务是要做什么」这类本该在交接物里的问题

### 顺带验证

| 检查项 | 期望 | spec 验收项 |
|---|---|---|
| 多个任务目录时 | 列出选项让你选，不默认取最新 | 14 |
| 分层读取 | 「继续推进」场景下**不读** `summaries.md` | 15 |
| 读完后 | 复述三件事后停下等指令，不自动开工 | 16 |

验收项 14 需要 `docs/sessions/` 下有 ≥2 个任务目录。当前只会有任务 5 产出的一个，**执行时临时造第二个**（内容随意，测完删除）。

### 三层结构下的失败定位多一步

失败时不是推倒重来，而是定位缺口：

```
新会话缺了哪条信息 → 该信息属于哪一层 → 补进那一层的模板 → 重跑
```

⚠️ **先判层再补段**。补错层会让下次恢复读不到——例如把「已核验的事实」写进 `summaries.md`，而恢复时 summaries 是按需读的，等于白写。记入 CHANGELOG。

---

## 任务 7：多分支 / 多人路径验证（P1）

### 目标

验证 spec 验收项 10、11——本仓自然状态下**验证不到**的两条。

### 为什么不能跳过

本仓只有 `master` 一个分支、`anyu` 一个提交者。但这是**对外发布的产物**，用户仓库的主流形态恰恰是多分支多人、且默认分支常为 `main`。

「本仓用不上」不是跳过的理由——发布产物的主要运行环境，正是你在本仓验证不到的那些。

### 步骤

**7.1 分支段展开（实跑）**

```bash
git checkout -b tmp-handoff-test
# 触发保存，期望路径含 tmp-handoff-test/ 层
git checkout master && git branch -D tmp-handoff-test
```

⚠️ 测完记得删掉临时分支产出的交接物目录。

**7.2 用户名后缀展开（静态审查）**

无法真造第二个提交者，改为验证判定逻辑本身：

```bash
git log --format=%an | sort -u | wc -l     # 当前应为 1
```

确认 SKILL.md 里的条件是 `> 1` 而非硬编码。

**7.3 默认分支非 master（静态审查）**

```bash
git symbolic-ref refs/remotes/origin/HEAD    # 本仓返回 refs/remotes/origin/master
```

确认 SKILL.md 用的是这条命令的输出，而不是字面量 `master`。

⚠️ 7.2 与 7.3 是**静态审查，不是实跑**。真实的多人 / main 分支环境需要另一个仓库，本次不做——但**必须在 CHANGELOG 的「已知限制」里标注未实测**（见任务 4.1）。

---

## 任务 8：darwin-skill 评分（P1）

### 目标

按 `AGENTS.md`，新插件属 Minor 升级，提交前须评分。

### 首评没有基线，也不需要造一个

AGENTS.md 的门禁原文是「新分数 ≥ 改动前分数」——它防的是**同一个 skill 在迭代中退步**。新 skill 没有「改动前分数」，这条规则字面上对首次发布不适用。

⚠️ **不要找一个同类 skill 当替代基线**（本 plan 初稿曾写「取 `weekly-report` 作对照」，是错的）。两个 skill 的分数不可比：darwin-skill 的 rubric 评的是各自 SKILL.md 的结构质量，不是同一把尺子上的刻度。对照 skill 分低时超过它不说明什么，分高时达不到也不代表不合格——那是把「防倒退」错译成了「排名」。

⚠️ 实测 `.claude/skills/darwin-skill/results.tsv` **只有表头无数据行**，`cards/` 下仅 `sync-cc-docs-to-youdaonote` 一个产物。本仓此前几乎没跑过评分，任何「现有基线」的假设都要先查再用。

### 做法

直接评 `session-handoff`，看**绝对分与各维度失分点**，按失分点改。改完的分数成为**将来迭代的基线**——那才是门禁真正需要的东西。

倒退项（若将来迭代出现）先修正再提交。评分产物落在 gitignore 的 `.claude/skills/darwin-skill/results.tsv`，不进版本库。

---

## 任务 9：按测试结果修正（P0）

汇总任务 6、7、8 的结论，逐项修正后重跑对应验证。

修正若涉及 SKILL.md 或 `templates.md` 的行为变更 → 升 `metadata.version` 至 `1.0.1`（Patch，修复已有内容），**同时**升两份 `plugin.json` 至 `1.0.1`。若只是补 CHANGELOG 措辞，不升版本。

⚠️ **`templates.md` 的改动同样触发升版**——它在 `plugins/*/skills/<name>/` 目录内，按 AGENTS.md 触发矩阵首行，该目录内任一文件改动都要升 skill 的 `metadata.version` 与插件两份 `plugin.json`。

---

## 提交策略

按 `commit-cc-plugin` 的原子性要求，**分两次提交**：

| # | 范围 | 类型 | 时机 |
|---|---|---|---|
| 1 | 任务 1-4（脚手架 + templates + SKILL + 配套文件）+ 任务 5 的交接物 | `feat(session-handoff)` | 任务 5 自举验证通过后 |
| 2 | 任务 9 的修正（若有） | `fix(session-handoff)` | 任务 6-8 全部完成后 |

⚠️ 不要在任务 5 之前提交——自举验证可能暴露模板缺口，改完再提交避免一次功能引入两个 commit。

⚠️ 任务 5 产出的交接物本身与第 1 次提交**是同一逻辑任务**（它是验证产物），一并提交。

⚠️ 本次删除旧 spec/plan（`2026-09-08-*`）与新增本 spec/plan 属**文档改动**，落在 `docs/` 下，**不升任何版本号**（AGENTS.md 触发矩阵末几行）。可与上述两次提交分开，单独作一次 `docs(session-handoff)` 提交。

---

## 风险与应对

| 风险 | 概率 | 应对 |
|---|---|---|
| SKILL.md 超 180 行 | 中 | 优先把三层模板的说明性文字移进 `templates.md`，SKILL.md 只留引用。**不要砍待办队列 7 项清单**——那是参照实现里最有价值的可核对约束 |
| 三层结构对单人小任务过重 | **中高** | 这是本次结构选择的主要代价。缓解手段是「后两层可不创建」（spec 五节末）。若实测发现绝大多数会话只产 progress，说明三层拆分对本仓收益为负，届时按数据回退为单文件——但**要等实测数据，不要现在预判** |
| 自举验证发现模板缺关键段 | 中 | 这正是自举的目的。补段后重跑，不算返工 |
| 新会话恢复时读不懂交接物 | 中 | 记录它具体缺什么，先判层再补段。这是最有价值的失败 |
| `claude plugin validate` 报未知 warning | 低 | 对照 `check_plugin_versions.py` 的 `CLAUDE_ALLOWED_KEYS` 注释——该白名单本身就是历次 validate warning 的沉淀 |
| 多人 / 非 master 默认分支无法实测 | **确定发生** | 静态审查判定逻辑 + CHANGELOG「已知限制」标注。不假装验证过 |

---

## 与参照实现的最终差异清单（实施时自查用）

实施完成后逐条确认，**每一条都应该是有意的偏离，不是遗漏**：

| # | 参照实现有 | 本 skill | 依据 |
|---|---|---|---|
| 1 | `conversations/` 逐轮对话 | `insights.md` 习得与核验 | 决策 2 |
| 2 | 每轮静默追写 | 仅显式触发 | 决策 2 |
| 3 | 上下文告急自动保存 | 提议交接，不自动执行 | 对照表 #11 |
| 4 | 交接物自动 commit | 只写文件报路径 | 决策 4 |
| 5 | `init.sh` 四平台环境脚本 | 无 | 对照表 #13 |
| 6 | `feature_list.json` | 无（参照实现自己已删） | 对照表 #14 |
| 7 | `artifacts.json` 产物注册 | 无 | 对照表 #15 |
| 8 | `pitfalls.md` → code-linter 闭环 | 踩坑留在 `insights.md`，带「归属判定」字段由人搬 | 对照表 #16 |
| 9 | stop hook（session-guard） | 无 | 决策 5 |
| 10 | 双 agent（Initializer / Coder） | 单 skill 两模式 | 对照表 #19 |
| 11 | 按目录存在性判定模式 | 按用户意图判定 | 四节开头 |
| 12 | 恢复后按队列直接开工 | 复述后停下 | 决策 6 |
| 13 | 固定 `{分支}/{层}/{user}` | 运行时推导，可退化 | 决策 3 |
| 14 | 一分支一目录，progress 无限追加 | 一任务一目录 | 三节·路径结构差异 |
| 15 | 「只更新 progress 不写 summary」是错误 | 后两层允许不创建 | 五节末 |
| 16 | 「技术洞察」维度 | 无，归 `knowledge-base/` | 五节·第二层 |
| 17 | 平铺 frontmatter | 六字段 + `metadata` 嵌套 | 0.1 #7 |
