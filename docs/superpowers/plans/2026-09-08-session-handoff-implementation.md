# 实施计划：session-handoff skill

**日期：** 2026-09-08
**Spec：** [`docs/superpowers/specs/2026-09-08-session-handoff-design.md`](../specs/2026-09-08-session-handoff-design.md)
**状态：** 待执行

---

## 0. 全局约束

### 0.1 硬性规则

1. **单一真源**——SKILL.md 只在 `plugins/optimus-session-plugin/skills/session-handoff/` 维护一份，不在 `.claude/skills/` 另存副本
2. **不建符号链接**——`.kiro/skills/` 与 `.agents/skills/` 只镜像 `.claude/skills/` 下的自用 skill。`plugins/` 下的产物由 harness 插件机制分发，建了反而会被 pre-commit 的反向检查判为悬空
3. **两份 `plugin.json` 同值**——同一次改动内一起写入 `1.0.0`，不是一方抄另一方
4. **marketplace 条目内不写 `version`**——会被 `plugin.json` 静默覆盖，且本地 source 会触发官方不一致警告
5. **分段写入**——SKILL.md 预计 130-150 行，必须先 Write 骨架再多次 Edit 填充，禁止单次输出全文
6. **不写插件根 README**——9 个现有插件中 8 个没有（唯一的 `optimus-mcp-servers` 不含 skill）。`doc-conventions.md` 的六章节规范是对 skill 级 README 的要求，不约束插件根

### 0.2 校验命令

```bash
# 提交门禁（版本同值 + 镜像完整）
sh .githooks/pre-commit

# 官方插件校验
claude plugin validate plugins/optimus-session-plugin

# 两处 marketplace 是否同步
python -c "
import json
a={p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']}
b={p['name'] for p in json.load(open('.agents/plugins/marketplace.json'))['plugins']}
print('仅 Claude 有:', a-b); print('仅 Codex 有:', b-a)
"
```

### 0.3 版本规则

本次改动落在四处，按 `AGENTS.md` 触发矩阵：

| 对象 | 值 | 依据 |
|---|---|---|
| `.claude-plugin/plugin.json` | `1.0.0` | 新插件起始号 |
| `.codex-plugin/plugin.json` | `1.0.0` | 同上，同值 |
| `SKILL.md` 的 `metadata.version` | `1.0.0` | 新 skill 起始号 |
| `.claude-plugin/marketplace.json` 顶层 | `14.0.0` → `14.1.0` | 新增插件 = Minor |

⚠️ `.agents/plugins/marketplace.json` 若有独立顶层 `version`，同步升同值——执行时先读实际结构确认。

### 0.4 已批准的三项待确认

| 项 | 决定 |
|---|---|
| 插件命名 | `optimus-session-plugin` |
| `docs/sessions/` 入库 | **入库**。skill 在保存后的输出里提示「如不希望入库，可加入 .gitignore」，把选择权交给用户，但不代为决定 |
| 配对校验 skill | **不做**。为低频场景造刹车是另一种过度设计 |

---

## 1. 任务总览

| # | 任务 | 优先级 | 产出 | 阻塞关系 |
|---|---|---|---|---|
| 1 | 插件脚手架 + 两处 marketplace | P0 | 2 份 plugin.json、2 处条目、顶层升版 | 无 |
| 2 | SKILL.md 主体 | P0 | ≤150 行 | 依赖 1（目录须先存在） |
| 3 | CHANGELOG + test-prompts + skill README | P1 | 3 个文件 | 依赖 2 |
| 4 | 自举验证（保存路径） | P0 | 本会话交接物 | 依赖 2 |
| 5 | 恢复验证（新会话） | P0 | 测试结论 | 依赖 4，**需用户开新会话** |
| 6 | 多分支/多人路径验证 | P1 | 测试结论 | 依赖 2 |
| 7 | darwin-skill 评分 | P1 | 评分结果 | 依赖 2、3 |
| 8 | 按测试结果修正 | P0 | 修订版 | 依赖 5、6、7 |

**关键路径**：1 → 2 → 4 → 5 → 8。任务 5 需要你开新会话配合，是唯一无法单会话内完成的环节。

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

⚠️ **只有 Claude 侧有顶层 `version` 要升**（`14.0.0` → `14.1.0`）。Codex 侧没有该字段，不要凭空添加。

⚠️ Codex 的 `category` 是受控词表，现有取值：`Backend` / `Decision` / `DevOps` / `Frontend` / `MCP` / `Media` / `Product` / `Productivity` / `QA`。会话交接属工作流工具，**取 `Productivity`**（与现有 office 插件同类），不新造词。

### 步骤

**1.1** 建目录 `plugins/optimus-session-plugin/{.claude-plugin,.codex-plugin,skills/session-handoff}`

**1.2** 写 `.claude-plugin/plugin.json`（字段照 `optimus-prd-plugin`，白名单见 `.githooks/check_plugin_versions.py` 的 `CLAUDE_ALLOWED_KEYS`）：

```json
{
  "name": "optimus-session-plugin",
  "version": "1.0.0",
  "description": "跨会话交接：会话结束前保存进度与决策，新会话恢复上下文接着干",
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
  "description": "跨会话交接：会话结束前保存进度与决策，新会话恢复上下文接着干",
  "skills": "./skills/",
  "author": { "name": "optimus", "url": "https://www.optimus.cn" },
  "homepage": "https://github.com/Glepooek/optimus-plugins-official",
  "repository": "https://github.com/Glepooek/optimus-plugins-official",
  "license": "MIT",
  "interface": {
    "displayName": "Optimus Session",
    "shortDescription": "跨会话交接工具",
    "longDescription": "跨会话交接：会话结束前保存进度与决策，新会话恢复上下文接着干",
    "developerName": "Optimus",
    "category": "Productivity",
    "capabilities": ["Skills"],
    "defaultPrompt": ["交接一下当前工作", "继续上次的工作"]
  }
}
```

**1.4** `.claude-plugin/marketplace.json`：顶层 `version` 升 `14.1.0`，`plugins` 数组追加条目（**不含 `version`**）

**1.5** `.agents/plugins/marketplace.json`：`plugins` 数组追加条目，`source` 用对象形式，`category: "Productivity"`，顶层不动

### 验证

```bash
sh .githooks/pre-commit                                   # 两份 plugin.json 同值
claude plugin validate plugins/optimus-session-plugin     # 无 warning
python -c "
import json
a={p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']}
b={p['name'] for p in json.load(open('.agents/plugins/marketplace.json'))['plugins']}
assert a==b, f'不同步: {a^b}'
print('两处 marketplace 同步，共', len(a), '个插件')
"
```

对应 spec 验收项 1、2、3、4、6。

---

## 任务 2：SKILL.md 主体（P0）

### 目标

≤150 行，覆盖保存/恢复两模式，frontmatter 六字段合规。

### 分段写入顺序

⚠️ 全局规则要求分段，禁止单次输出全文。按此顺序，每段一次 Edit：

```
2.1 Write 骨架：frontmatter + 标题 + 模式判定表          (~25 行)
2.2 Edit 追加：模式 A 保存（前置校验 + 采集 + 收尾）      (~35 行)
2.3 Edit 追加：交接物模板 + 各段取舍规则                  (~45 行)
2.4 Edit 追加：模式 B 恢复（定位 + 读取顺序 + 复述）      (~25 行)
2.5 Edit 追加：Red Flags 表                              (~15 行)
```

### 路径推导必须写成可执行命令

spec 第三节的推导规则要落成 SKILL.md 里的实际命令，不能只写文字描述：

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
DEFAULT=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
DEFAULT=${DEFAULT:-$BRANCH}          # 无 origin 时视当前分支为默认
AUTHORS=$(git log --format=%an | sort -u | wc -l)
USER=$(git config user.name)
```

- `BRANCH` ≠ `DEFAULT` → 路径含 `<branch>/` 段
- `AUTHORS` > 1 → 文件名含 `.<user>` 后缀

⚠️ **禁止硬编码 `master` 或 `main`**——两者在真实项目中都常见，写死会给另一半用户凭空多一层目录。

### 入库提示（已批准决定）

保存完成后的输出须包含一行：

```
交接物已写入 <路径>。如不希望它进入版本库，可将 docs/sessions/ 加入 .gitignore。
```

不代为决定，也不代为提交。

### 必须落进正文的三条约束

来自 spec，且是本 skill 最容易失守的地方：

1. **不重复 git/CHANGELOG 已记录的内容**——「已完成」段写 git 里看不到的（为什么这么改、试过什么没成），不是 commit message 的复述
2. **空维度删掉整段，不写「（无）」**——占位符比缺失更糟，下个会话要花时间确认是真没有还是忘了写
3. **⏸️ 阻塞项必须附原因**——不写原因等于没写，下次还要重新排查

### 验证

```bash
wc -l plugins/optimus-session-plugin/skills/session-handoff/SKILL.md   # ≤150
```

frontmatter 六字段对照 `.claude/rules/skill-conventions.md`。对应 spec 验收项 15。

---

## 任务 3：CHANGELOG + test-prompts + skill README（P1）

### 3.1 CHANGELOG.md

```markdown
# Changelog

## [1.0.0] - 2026-09-08

### Added
- 跨会话交接 skill 首个版本，保存与恢复两种模式
- 交接物路径按「分支 × 协作者数」运行时推导，单分支单人时自动退化为扁平路径
- 交接物模板六段（当前状态/已完成/下一步/关键决策/待验证的假设/引用），后三段可为空
- 下一步支持四档优先级（🔴高 / 🟡中 / 🔵低 / ⏸️阻塞），阻塞项强制附原因
```

### 3.2 test-prompts.json

照 `optimus-prd-plugin/skills/prd-creator/test-prompts.json` 格式（`id` / `prompt` / `expected`）。三条对应 spec 第八节：

| id | prompt 要点 | expected 要点 |
|---|---|---|
| 1 | "交接一下"，会话有实质产出 | 正常保存，段落取舍正确，空维度整段删除而非写「（无）」，输出含 gitignore 提示，**不自动提交** |
| 2 | "继续上次的工作"，存在多个交接物 | 列出选项让用户选，不默认取最新；读完复述三件事后停下，不自动开工 |
| 3 | **指令冲突**："快速交接，别问了"，但会话内容极少 | 告知「本次无实质可交接内容」，既不无视指令追问，也不生成空洞占位符敷衍 |

第 3 条是关键——它测的正是本 skill 最容易失守的地方：为了显得「完整」而输出无价值内容。

### 3.3 skill README

24/48 的 skill 有 README，新产物向好的那半看齐。按 `.claude/rules/doc-conventions.md` 的六章节写。

⚠️ **不写插件根 README**——9 个插件中 8 个没有，那一层没有此惯例。

### 验证

```bash
python -m json.tool plugins/optimus-session-plugin/skills/session-handoff/test-prompts.json > /dev/null && echo "JSON 合法"
```

---

## 任务 4：自举验证 — 保存路径（P0）

### 目标

用这个 skill 交接「这个 skill 的实现」本身。同时检验保存路径的四个验收项。

### 步骤

在本仓触发一次保存，检查产出：

| 检查项 | 期望 | spec 验收项 |
|---|---|---|
| 路径 | `docs/sessions/2026-09-08-session-handoff-impl.md`，**无 `master/` 层、无 `.anyu` 后缀** | 8 |
| 段落 | 六段中必填三段齐全，空维度整段删除而非「（无）」 | 7 |
| 「已完成」内容 | 不是 commit message 的复述 | 14 |
| git 状态 | 交接物为 untracked，**未生成 commit** | 13 |

```bash
git status --short docs/sessions/     # 应为 ?? 而非已提交
```

### 为什么用自举而非造假数据

造一份人工交接物只能验证「格式对不对」，验证不了「skill 自己写出来的东西够不够用」。自举同时暴露两者，且失败反馈直接。

---

## 任务 5：恢复验证 — 新会话（P0，需你配合）

### 目标

最小可行测试：**交接物能不能让一个无上下文的会话接着干**。这是全部验收项里唯一能判定成败的一条，前面都是结构性检查。

### 测试设计

- **单一变量**：新会话除交接物外不给任何提示
- **执行**：任务 4 保存后，你开一个新会话，只说「继续上次的工作」
- **成功判定**：新会话能说出任务是什么、下一步做什么，与本会话实际意图一致，且无需你补充背景
- **失败判定**：新会话问出「这个任务是要做什么」这类本该在交接物里的问题

### 顺带验证

| 检查项 | 期望 | spec 验收项 |
|---|---|---|
| 多个交接物时 | 列出选项让你选，不默认取最新 | 11 |
| 读完后 | 复述三件事后停下等指令，不自动开工 | 12 |

验收项 11 需要 `docs/sessions/` 下有 ≥2 个文件。当前只会有任务 4 产出的一个，**执行时临时造第二个**（内容随意，测完删除）。

### 失败后怎么办

不是推倒重来，而是定位缺口：新会话具体缺了哪条信息 → 反推模板缺哪一段 → 补进模板 → 重跑。记入 CHANGELOG。

---

## 任务 6：多分支 / 多人路径验证（P1）

### 目标

验证 spec 验收项 9、10——本仓自然状态下**验证不到**的两条。

### 为什么不能跳过

本仓只有 `master` 一个分支、`anyu` 一个提交者。但这是**对外发布的产物**，用户仓库的主流形态恰恰是多分支多人、且默认分支常为 `main`。

「本仓用不上」不是跳过的理由——发布产物的主要运行环境，正是你在本仓验证不到的那些。

### 步骤

**6.1 分支段展开**

```bash
git checkout -b tmp-handoff-test
# 触发保存，期望路径含 tmp-handoff-test/ 层
git checkout master && git branch -D tmp-handoff-test
```

**6.2 用户名后缀展开**

无法真造第二个提交者，改为验证判定逻辑本身：

```bash
git log --format=%an | sort -u | wc -l     # 当前应为 1
```

确认 SKILL.md 里的条件是 `> 1` 而非硬编码。**代码审查方式验证**，不实跑。

**6.3 默认分支非 master**

```bash
git symbolic-ref refs/remotes/origin/HEAD    # 本仓返回 refs/remotes/origin/master
```

确认 SKILL.md 用的是这条命令的输出，而不是字面量 `master`。同样代码审查验证。

⚠️ 6.2 与 6.3 是**静态审查**，不是实跑。真实的多人 / main 分支环境需要另一个仓库，本次不做——但要在 CHANGELOG 里标注「多人场景未经实测」。

---

## 任务 7：darwin-skill 评分（P1）

### 目标

按 `AGENTS.md`，新插件属 Minor 升级，提交前须评分。

### 基线

新 skill 无「改动前分数」可比。以**不低于同类 workflow skill** 为准，取 `optimus-devops-plugin:weekly-report` 作对照（同为 workflow category、同样读 git log）。

倒退项先修正再提交。评分产物落在 gitignore 的 `.claude/skills/darwin-skill/results.tsv`，不进版本库。

---

## 任务 8：按测试结果修正（P0）

汇总任务 5、6、7 的结论，逐项修正后重跑对应验证。

修正若涉及 SKILL.md 行为变更 → 升 `metadata.version` 至 `1.0.1`（Patch，修复已有内容），**同时**升两份 `plugin.json` 至 `1.0.1`。若只是补 CHANGELOG 措辞，不升版本。

---

## 提交策略

按 `commit-cc-plugin` 的原子性要求，**分两次提交**：

| # | 范围 | 类型 | 时机 |
|---|---|---|---|
| 1 | 任务 1-3（插件脚手架 + skill 全部文件） | `feat(session-handoff)` | 任务 4 自举验证通过后 |
| 2 | 任务 8 的修正（若有） | `fix(session-handoff)` | 任务 5-7 全部完成后 |

⚠️ 不要在任务 4 之前提交——自举验证可能暴露模板缺口，改完再提交避免一次功能引入两个 commit。

⚠️ 任务 4 产出的交接物本身（`docs/sessions/2026-09-08-*.md`）与第 1 次提交**是同一逻辑任务**（它是验证产物），一并提交。

---

## 风险与应对

| 风险 | 概率 | 应对 |
|---|---|---|
| SKILL.md 超 150 行 | 中 | 优先砍交接物模板的说明性文字，模板本身保留。真放不下再考虑拆 `references/`，但那会增加一次文件读取 |
| 自举验证发现模板缺关键段 | 中 | 这正是自举的目的。补段后重跑，不算返工 |
| 新会话恢复时读不懂交接物 | 中 | 记录它具体缺什么，反推模板。这是最有价值的失败 |
| `claude plugin validate` 报未知 warning | 低 | 对照 `check_plugin_versions.py` 的 `CLAUDE_ALLOWED_KEYS` 注释——该白名单本身就是历次 validate warning 的沉淀 |
| 多人场景无法实测 | **确定发生** | 静态审查判定逻辑 + CHANGELOG 标注未实测。不假装验证过 |
