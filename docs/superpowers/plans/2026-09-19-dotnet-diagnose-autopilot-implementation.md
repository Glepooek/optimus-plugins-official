# dotnet-diagnose-autopilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建 `dotnet-diagnose-autopilot` skill，作为编排层调度既有 `dotnet-diagnose` agent，实现自动识别诊断素材类型、按需触发盲态双活二次分析、产出结构化报告并标记分歧交人工复核。

**Architecture:** 纯 Markdown 编排型 skill（无脚本）。Step 1 判定素材证据类型；Step 2 用 `Task` 工具派发一次全新的 `optimus-devops-plugin:dotnet-diagnose` agent 调用并要求逐字转发结果；若首次结论强度为"推测"则 Step 4 派发第二次同样全新、零上下文的调用；Step 5 比对两次结论，一致则合并标注交叉确认，不一致则并列展示标 🔴 人工复核；Step 6 用 `Write` 工具把结构化报告落盘到仓库外 `$HOME/dd-autopilot/`。

**Tech Stack:** Claude Code Skill（插件生态）；`Task` 工具（agent 派发）；`Write`/`Read` 工具（报告落盘/素材读取）；无第三方库、无脚本。

**Spec:** `docs/superpowers/specs/2026-09-19-dotnet-diagnose-autopilot-design.md`

## Global Constraints

- 新 skill 目录：`plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/`
- SKILL.md frontmatter 六字段合规（`.claude/rules/skill-conventions.md`），起始 `metadata.version: "1.0.0"`，`metadata.category: workflow`
- `allowed-tools: Task Write Read`（`Task` 派发 agent；`Write` 落盘报告；`Read` 读取素材以文件路径给出时的内容）
- 插件两份 `plugin.json`（`.claude-plugin/` 与 `.codex-plugin/`）版本同步升 **Minor**：`1.2.4` → `1.3.0`
- 不修改 `dotnet-diagnose` agent 与 `dotnet-diagnose-triage` skill 的任何既有文件——本次是纯新增
- 不重新判定"征象"、不新增置信度数值体系、两次调用之间零信息传递、不一致结论不自动裁决（spec § 8 反例清单，贯穿全部任务的硬约束）
- 落盘路径固定为 `$HOME/dd-autopilot/report-<timestamp>.md`（仓库外，按 `knowledge-base/dotnet-debugging/rules/01-dump-handling.md § 2` 版本库隔离要求）
- 新增 skill 必须带 `evals/<case>/prompt.md`（CI `new-skill-eval-case` 门禁强制）
- 提交流程走 `commit-cc-plugin` skill，禁止手动 git 工作流；主干受保护，须走特性分支 → PR → 六项必需检查全绿 → squash merge

---

### Task 1: 创建 SKILL.md 骨架、frontmatter、Step 1 素材类型识别

**Files:**
- Create: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md`

**Interfaces:**
- Consumes: 无（本任务是全新文件的起点）
- Produces: SKILL.md 的 frontmatter 六字段（`name: dotnet-diagnose-autopilot`）；正文"概述"节（做什么/不做什么）；"Step 1 素材类型识别"节，产出证据类型判定表——后续任务（Task 2 起）依赖这份 frontmatter 与 Step 1 表格作为衔接点

- [ ] **Step 0: 建特性分支（若当前在 master 上）**

```bash
git status
git branch --show-current
```

若当前分支是 `master`，先建特性分支：

```bash
git switch -c feat/dotnet-diagnose-autopilot
```

若已在特性分支上（说明是接续中断的会话），沿用该分支，不新建。本计划后续 Task 2-11 的所有 `git commit` 均在此特性分支上进行，直到 Task 12 才推送、开 PR、合并。

- [ ] **Step 1: 创建目录并写入 SKILL.md 骨架**

先确认父目录存在：

```bash
ls plugins/optimus-devops-plugin/skills/ | grep dotnet-diagnose
```

Expected: 只列出 `dotnet-diagnose-triage`，`dotnet-diagnose-autopilot` 尚不存在。

写入 SKILL.md（frontmatter + 概述 + Step 1）：

```markdown
---
name: dotnet-diagnose-autopilot
description: 给定一份原始 .NET 诊断素材（崩溃日志、内存转储 SOS 输出、!syncblk 输出、dotnet-counters 时间序列），自动识别素材类型、调度 dotnet-diagnose agent 完成分析；若首次结论强度为"推测"，用完全独立的第二次盲态调用做交叉验证；产出含首次/复核/一致性判定/最终建议的结构化报告并落盘。两次结论不一致时并列展示，标记需人工复核，不擅自取舍。触发词：自主分诊、自动分析这份 dump、帮我判断这个根因靠不靠谱、交叉验证一下这个诊断结论、autopilot triage、autonomous .NET diagnosis。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: workflow
compatibility: 需要同一工作树内已安装 optimus-devops-plugin 的 dotnet-diagnose agent 与 dotnet-diagnose-triage skill（本 skill 经 Task 工具调度前者，不直接读取判据）。
allowed-tools: Task Write Read
---

# .NET 自主分诊工作流（盲态双活编排层）

## 概述

**做什么**：给定一份原始诊断素材，自动识别其证据类型，经 `Task` 工具调度 `optimus-devops-plugin:dotnet-diagnose` agent 完成首次分析；若首次结论强度为"推测"，追加一次完全独立、零上下文的第二次分析做交叉验证；把两次结论比对合并，产出结构化报告并落盘。

**不做什么**：不重新判定"征象"（挂起/内存增长/崩溃等症状分类）——那是 `dotnet-diagnose` agent 内部路由的职责；不重新定义结论强度——直接复用 `dotnet-diagnose-triage` 已有的三档（已确认/推测/超出覆盖）；不做知识库判据裁剪——那是 agent 加载 triage 后的职责；不抓取 dump 或采集 trace——素材由用户已经提供。完整职责边界见 `docs/superpowers/specs/2026-09-19-dotnet-diagnose-autopilot-design.md` § 2。

## 主干六步

```
Step 1  素材类型识别，不可用则短路结束
Step 2  首次分析：Task 派发全新、无历史上下文的子任务
Step 3  解析首次结论强度（已确认 / 推测 / 超出覆盖 / 候选集穷尽）
Step 4  置信度分档：仅"推测"触发第二次
Step 5  第二次分析（仅 Step 4 判定触发时执行）：另起一个全新、无上下文的 Task
Step 6  比对两次结论，合成报告并落盘
```

## Step 1：素材类型识别

判定用户给出的原始素材属于哪类证据，不判定"征象"（症状分类留给 agent 内部路由）：

| 素材特征 | 归入证据类型 | 后续路由（由 agent 内部完成） |
|---|---|---|
| 含 `Index`/`SyncBlock`/`MonitorHeld`/`MT`/`Count`/`TotalSize` 等 SOS 命令列名 | 单时点证据（dump/SOS 输出） | agent 加载 triage 后走 `debugging-decision-tree.md` |
| 含托管异常类型 + 堆栈帧（`System.XXXException` + `at ...` 或 `InnerException`） | 崩溃日志 | 走 `evidence-precheck.md`「崩溃日志的定位」一节 |
| 含 counters/trace 时间序列表头（多行采样、时间戳列） | 时间序列证据 | 走 `live-monitoring-decision.md` |
| 三者均不含（纯业务日志、空文本、无异常语义的纯文字） | 不可用 | **不派发**，直接短路报错（见"失败处理"） |

若用户在触发语句中一并给出了症状描述（如"界面卡死"），原样随素材转发；若没给，不替用户猜——交给 `dotnet-diagnose` agent 自行按证据推断征象。

若素材以文件路径给出而非直接粘贴在对话中，用 `Read` 工具读取文件内容后再执行上表判定。
```

- [ ] **Step 2: 校验 frontmatter 可被 skills-ref 解析（若本机有该工具）**

```bash
skills-ref validate plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/ 2>&1 || echo "skills-ref 未安装，跳过（非本仓强制门禁，仅供人工抽查）"
```

Expected: 若工具存在，六字段全部通过校验（本 skill 只用六字段，不含任何 Claude 原生字段，不应出现 `Unexpected key(s)` 报错）；若命令不存在，按提示跳过，不影响后续任务。

- [ ] **Step 3: 提交**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
git commit -m "$(cat <<'EOF'
feat(devops-skills): 新建 dotnet-diagnose-autopilot 骨架与素材识别

- frontmatter 六字段 + 概述 + Step 1 素材类型识别
- 后续任务补全 Step 2-6 主干与配套文档

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

⚠️ 本任务产出尚不完整（Step 2-6 未写），此提交仅为阶段性检查点，不代表 skill 可用；`pre-commit` 门禁此时不会报错，因为它不校验 SKILL.md 正文完整性，只校验版本号与镜像等结构项——但**插件版本升级留到 Task 9 统一处理**，此处提交前无需改动 `plugin.json`（提交历史上先有 skill 内容变化、后有版本号变化是正常顺序，pre-commit 不会因此拦截，因为它只比对当前工作树状态而非提交粒度）。

### Task 2: Step 2-3——首次分析派发与结论强度解析

**Files:**
- Modify: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md`（在 Task 1 写入的 Step 1 之后追加）

**Interfaces:**
- Consumes: Task 1 产出的证据类型判定结果（Step 1 表格的右列）
- Produces: "Step 2：首次分析"节固定的 dispatch prompt 模板（后续 Task 3 的 Step 5 第二次调用复用同一模板，仅替换素材来源说明）；"Step 3：解析结论强度"节的三档/四态判定规则——Task 3 的触发判定依赖这里定义的"推测"关键字匹配规则

- [ ] **Step 1: 追加 Step 2、Step 3 正文**

在 SKILL.md 末尾追加：

```markdown
## Step 2：首次分析（Task 派发）

用 `Task` 工具派发一个全新的子任务，prompt 固定为以下模板（`{素材}` 替换为 Step 1 判定过的原始素材原文，`{症状描述}` 替换为用户提供的症状描述，若用户未提供则整段省略）：

```
把下面的内容原样作为输入转发给 @optimus-devops-plugin:dotnet-diagnose，然后把该 agent 的回答逐字原样输出。禁止总结、禁止改写、禁止补充你自己的分析或评论、禁止加任何前言后语。你的整个回复必须只包含 agent 返回的原文。

{症状描述}

{素材}
```

⚠️ **这条约束不是本次新加的保险，是复用已验证过的调用范式**——早期测试中若 dispatch prompt 只是笼统地说"帮我看看"，外层会转述总结 agent 的回答而非原样返回，导致后续的结论强度解析建立在被转述过的文本上而失真。

调用产生的完整回复原样保留，作为"首次分析"的最终内容，不在本 skill 内做任何二次处理。

## Step 3：解析首次结论强度

从 Step 2 的原样回复中定位"结论"段落（`dotnet-diagnose` agent 固定输出格式的第 1 段），按以下关键字匹配判定强度：

| 匹配到的关键字 | 判定强度 |
|---|---|
| "已确认" | 已确认 |
| "推测" | 推测 |
| "超出覆盖" | 超出覆盖 |
| "候选集已穷尽" / "候选集穷尽" | 候选集穷尽 |

四态严格互斥，取回复中实际出现的那一个。若回复中同时含多个关键字（理论上不应发生，因为 agent 输出格式固定为单一强度），以结论段落**首次出现**的关键字为准，并在报告的"一致性判定"段落注明"检测到多重强度标记，已取首个"。
```

- [ ] **Step 2: 干跑验证 Step 2/3 文字描述的自洽性**

这一步没有可执行代码，采用"角色扮演读稿"验证：通读刚写入的 Step 2、Step 3 正文，确认满足两点——① dispatch prompt 模板中的 `{素材}`/`{症状描述}` 占位符命名与 Step 1 表格描述的变量一致；② Step 3 的四态判定关键字与 `dotnet-diagnose-triage/SKILL.md` 中"三种结论强度"章节（已确认/推测/超出覆盖）及"出口条件"（候选集已穷尽）逐字对照无出入：

```bash
grep -n "已确认\|推测\|超出覆盖\|候选集已穷尽\|候选集穷尽" plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md
```

Expected: 输出中能找到与本任务 Step 3 表格四个关键字逐字匹配的行（"已确认"、"推测"、"超出覆盖"来自"三种结论强度"表；"候选集已穷尽"来自"出口条件"表的"宣告「本征象候选集已穷尽」"一行）。

- [ ] **Step 3: 提交**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
git commit -m "$(cat <<'EOF'
feat(devops-skills): dotnet-diagnose-autopilot 补全首次分析与强度解析

- Step 2：固定 dispatch prompt 模板，强制逐字原样转发
- Step 3：四态结论强度关键字匹配规则

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 3: Step 4-5——触发判定与盲态双活第二次调用

**Files:**
- Modify: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md`

**Interfaces:**
- Consumes: Task 2 产出的四态强度判定结果、Step 2 的 dispatch prompt 模板
- Produces: "Step 4"触发表；"Step 5"第二次调用规则（**只传入原始素材，不传第一次结论**）——Task 4 的比对逻辑依赖这里产出的"首次分析"与"复核分析"两段文本

- [ ] **Step 1: 追加 Step 4、Step 5 正文**

```markdown
## Step 4：触发判定——仅"推测"触发第二次

| Step 3 判定的强度 | 是否触发第二次调用 | 理由 |
|---|---|---|
| 已确认 | 否 | 已命中 triage 判据的证实条件，重验是浪费一次几百秒的调用 |
| 推测 | **是** | 唯一映射到"置信度较低或证据不足"的信号；证据方向一致但判据未完整命中，值得独立路径复核 |
| 超出覆盖 | 否 | 知识缺口，不是置信度问题，重跑大概率原地打转 |
| 候选集穷尽 | 否 | 假设已穷尽，同上 |

不新增任何置信度数值或阈值概念，直接复用 `dotnet-diagnose-triage` SKILL.md 已有的三档定义。

## Step 5：第二次分析（仅 Step 4 判定为"是"时执行）

用 `Task` 工具**另起一个全新的子任务**（与 Step 2 的调用互不知情、互不共享上下文），prompt 使用与 Step 2 完全相同的模板，`{素材}` 与 `{症状描述}` 取值与 Step 2 相同的原始输入——**不追加、不提及首次分析的任何内容**：

```
把下面的内容原样作为输入转发给 @optimus-devops-plugin:dotnet-diagnose，然后把该 agent 的回答逐字原样输出。禁止总结、禁止改写、禁止补充你自己的分析或评论、禁止加任何前言后语。你的整个回复必须只包含 agent 返回的原文。

{症状描述}

{素材}
```

⚠️ **这是"盲态双活"的核心实现**：第二次调用是一个全新的 Task，不知道自己是"第二次"，不知道第一次说了什么。这不是"对抗式复核"（让第二次去挑战第一次的结论）——那样第二次的判断会被第一次结论锚定，偏离"独立观察"的字面含义。两次调用产生的结论完全独立，只在 Step 6 做事后比对。

调用产生的完整回复原样保留，作为"复核分析"的最终内容。
```

- [ ] **Step 2: 干跑验证——确认两次调用的 prompt 模板逐字一致**

```bash
grep -A6 "把下面的内容原样作为输入转发给" plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
```

Expected: 输出两处代码块，Step 2 与 Step 5 各一处，除模板本身逐字相同外无其他差异（不应出现"这是复核"、"第一次说了"等字样——出现即说明违反了盲态约束）。

- [ ] **Step 3: 提交**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
git commit -m "$(cat <<'EOF'
feat(devops-skills): dotnet-diagnose-autopilot 补全触发判定与盲态第二次调用

- Step 4：仅"推测"强度触发第二次分析
- Step 5：第二次调用与首次零信息传递，prompt 模板逐字一致

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 4: Step 6——结论比对、报告合成与落盘

**Files:**
- Modify: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md`

**Interfaces:**
- Consumes: Task 2 的"首次分析"文本、Task 3 的"复核分析"文本（或"未触发"占位说明）
- Produces: 完整报告 Markdown 模板（五段：素材摘要/首次分析/复核分析/一致性判定/最终建议）；`Write` 落盘路径规则——Task 5（评估门失败处理）与 Task 8（evals）都依赖这份报告骨架

- [ ] **Step 1: 追加 Step 6 正文**

```markdown
## Step 6：结论比对、报告合成与落盘

### 比对规则

| 两次结论关系 | 处理 |
|---|---|
| 强度一致 + 假设台账指向同一根因 | 合并为一条结论，标注"两次独立盲态分析交叉确认"，置信度可视为高于单次 |
| 强度不同，或指向不同根因 | **不擅自取舍、不加权投票、不选"更详细的那份"**。两份结论并列展示，标记 🔴 需人工复核 |

判断"是否指向同一根因"看两次回复"结论"段落中引用的 `file § anchor` 是否一致——一致视为同一根因，不一致视为不同根因。

### 报告骨架

```markdown
# .NET 自主分诊报告

## 素材摘要
- 类型：{单时点证据/崩溃日志/时间序列证据}
- 判定依据：{命中的特征，如 "含 MonitorHeld 列"}

## 首次分析
{Step 2 的原样输出}

## 复核分析
{未触发时：「未触发：首次已确认/超出覆盖/候选集穷尽，复核条件未命中」}
{触发时：Step 5 的原样输出}

## 一致性判定
- 结论：{一致 / 不一致 / 未触发复核}
- {一致时：合并陈述，标注"两次独立盲态分析交叉确认"}
- {不一致时：并列列出两份结论，🔴 标记"需人工复核"，不擅自取舍}

## 最终建议
{仅当"一致"或"仅首次触发"时给出；"不一致"时写"见上方两份结论，需人工裁决后再确定修复方向"}
```

### 落盘

用 `Write` 工具把上述报告写入：

```
$HOME/dd-autopilot/report-<timestamp>.md
```

`<timestamp>` 格式为 `YYYYMMDD-HHMMSS`（本机当前时间）。落盘前确认该目录存在（若不存在，`Write` 工具会自动创建父目录，无需额外的 `mkdir` 步骤）。诊断素材可能含敏感数据，该路径固定在仓库外，按 `knowledge-base/dotnet-debugging/rules/01-dump-handling.md § 2. 版本库隔离` 不得落进 git 工作树。

报告内容同时在对话中完整输出一份，不仅依赖落盘文件——落盘失败不应挡住结论交付（见"失败处理"）。
```

- [ ] **Step 2: 干跑验证——报告模板五段落与 spec 逐字对照**

```bash
grep -n "^## " docs/superpowers/specs/2026-09-19-dotnet-diagnose-autopilot-design.md | sed -n '/5\. 结构化报告与落盘/,/6\. 目录结构/p'
```

Expected: 能看到 spec § 5.1 报告骨架的五段标题（素材摘要/首次分析/复核分析/一致性判定/最终建议），与本任务写入 SKILL.md 的模板逐一对应，无缺漏或改名。

- [ ] **Step 3: 提交**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
git commit -m "$(cat <<'EOF'
feat(devops-skills): dotnet-diagnose-autopilot 补全报告合成与落盘

- Step 6：一致/不一致比对规则、五段报告骨架、$HOME/dd-autopilot/ 落盘路径

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 5: 执行前置校验与失败处理

**Files:**
- Modify: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md`

**Interfaces:**
- Consumes: Task 1 的 Step 1（素材类型识别，用于判断"输入参数检查"是否通过）、Task 4 的落盘路径（用于"输出参数检查"）
- Produces: "执行前置校验"独立 Step（置于 Step 1 之前，编号调整）；"失败处理"表——这是本 skill 最终交付的完整正文，之后任务不再修改主干逻辑

⚠️ `.claude/rules/skill-conventions.md` 规定"前置校验作为独立 Step 呈现……不要混入 SKILL.md 的失败处理章节"。本任务把两者分别写成两个独立小节，即使都在本任务内完成。

- [ ] **Step 1: 在 Step 1 之前插入"执行前置校验"小节（不占用 Step 编号，Step 1-6 原编号不变）**

先读取当前文件确认现有编号：

```bash
grep -n "^## Step" plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
```

Expected: 列出 `## Step 1：素材类型识别` 至 `## Step 6：结论比对、报告合成与落盘` 共 6 处，本任务不改动这些标题文字，只在 `## Step 1：素材类型识别` 之前插入一个新的、独立的 `## 执行前置校验` 小节：

```markdown
## 执行前置校验

进入 Step 1 之前，先做以下检查：

| # | 类别 | 检查内容 | 不满足时 |
|---|---|---|---|
| 1 | 依赖检查 | `dotnet-diagnose` agent 是否可用（`compatibility` 字段声明的依赖） | 硬约束，报错终止："未检测到 optimus-devops-plugin:dotnet-diagnose agent，请确认插件已安装" |
| 2 | 输入参数检查 | 用户是否提供了素材（对话内容或文件路径） | 硬约束，报错终止："未收到诊断素材，无法开始分诊" |
| 3 | 输出参数检查 | `$HOME/dd-autopilot/` 的父目录（`$HOME`）是否存在且可写 | 可协商风险 → 若不可写，仍继续执行分析，落盘环节按"失败处理"表处置，不阻断整个流程 |

类别 1、2 不满足属硬约束（无法绕过、继续执行没有意义），类别 3 不满足属可协商风险（报告仍可在对话中完整输出，只是落盘这一步失败）。
```

- [ ] **Step 2: 在文件末尾追加"失败处理"节**

```markdown
## 失败处理

| 触发条件 | 处置 | 理由 |
|---|---|---|
| Step 3/6 的 `Task` 调用超时或无响应 | 不设短超时熔断；`dotnet-diagnose` 单次正常耗时可达 300 秒以上，先等待。若最终仍失败（工具报错、非超时类失败），如实转发失败原因，标注"首次分析未能完成"，**不重试、不静默跳过** | 特意不引入新的超时数值，避免与 agent 自身已经隐含的耐心假设打架 |
| Step 2 素材类型识别判定为"不可用" | 短路结束，不派发任何 Task，报错提示"未识别出可用的取证输出类型" | 不可用的素材派发下去只会让 agent 在其 Step 1（证据清点）重新判一次同样的失败 |
| 首次分析返回的内容**仅是症状描述、无任何取证结论**（agent 判定证据不足以进入分析，直接反问用户要更多信息） | 不进入结论强度判定、不触发第二次调用；原样转发 agent 的反问内容；报告"复核分析"段落写"未触发：首次分析要求补充证据，未产生可比对的结论" | 双活机制比对的是两份**结论**；连一份结论都没有，比对无从谈起 |
| 第二次分析同样超时或失败 | 报告"复核分析"段落写明失败原因，"一致性判定"写"复核未完成"，不当作"一致"或"不一致"处理，仍标 🔴 交人工复核 | 复核失败本身就是一种需要人工介入的情形 |
| `Write` 落盘失败（如 `$HOME/dd-autopilot/` 不可写） | 报告内容仍在对话中完整输出，附加提示"落盘失败：{原因}，请手动保存以下内容" | 落盘是交付形式的加分项，不是报告本身能否产出的前提条件 |
```

- [ ] **Step 3: 通读全文核对 Step 编号连续且无重复**

```bash
grep -n "^## Step\|^## 执行前置校验\|^## 失败处理" plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
```

Expected: 依次为"执行前置校验"、"Step 1：素材类型识别"、"Step 2：首次分析（Task 派发）"、"Step 3：解析首次结论强度"、"Step 4：触发判定"、"Step 5：第二次分析"、"Step 6：结论比对、报告合成与落盘"、"失败处理"，**Step 编号与 Task 1-4 写入时完全一致，未发生顺延**。

⚠️ 本任务刻意让"执行前置校验"不占用 Step 序号（不叫"Step 0"或"Step 1"），避免与 Task 1-4 已经写死在正文各处的"Step 2"、"Step 5"等交叉引用（如 Step 6 中"仅 Step 4 判定为'是'时执行"）全部跟着错位——这类文字引用是逐字比对，重新编号意味着要逐处重写，风险远高于让前置校验单独成节。

- [ ] **Step 4: 提交**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
git commit -m "$(cat <<'EOF'
feat(devops-skills): dotnet-diagnose-autopilot 补全前置校验与失败处理

- 新增执行前置校验独立小节（三类检查），不占用 Step 编号，原 Step 1-6 保持不变
- 新增失败处理表，覆盖 Task 超时、素材不可用、症状无结论、复核失败、落盘失败五种情形

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 6: 目录结构补全——README.md

**Files:**
- Create: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/README.md`

**Interfaces:**
- Consumes: Task 1 的 `metadata.version`/`metadata.category`（README 头部须与 SKILL.md 一致）、Task 5 完成后的 Step 1-6 主干（业务逻辑流程图内容来源）
- Produces: 完整 README.md（六章节：标题元信息/所处层级/触发词/业务逻辑流程图/产出物数据流/依赖关系图）——`.claude/rules/doc-conventions.md` 强制要求

- [ ] **Step 1: 核对 SKILL.md 当前 version/category 取值**

```bash
grep -A3 "^metadata:" plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
```

Expected: `version: "1.0.0"`、`category: workflow`（Task 1 写入的值）。

- [ ] **Step 2: 写入 README.md**

```markdown
# dotnet-diagnose-autopilot

> 版本：1.0.0 | 分类：workflow

给定一份原始 .NET 诊断素材，自动识别类型、调度 dotnet-diagnose agent 完成分析，必要时用完全独立的第二次盲态调用交叉验证，产出结构化报告并标记分歧交人工复核。

## 所处层级

```
┌─────────────────────────────────────────────────────────────┐
│                          workflow                           │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │   ★ dotnet-diagnose-autopilot（编排层：多次调度）   │   │
│   └──────────────────────────┬──────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │ 经 Task 工具调度（非直接 Skill 加载）
                               │
                          ┌───────────────────┐
                          │ dotnet-diagnose   │
                          │ agent（编排层）   │
                          └─────────┬─────────┘
                                    │ 加载（承载层）
                                    ▼
                          ┌───────────────────────┐
                          │ dotnet-diagnose-triage │
                          │ skill（quality）       │
                          └───────────────────────┘
```

本 skill 与 `dotnet-diagnose` agent 同为编排层，区别是**调度次数**——`dotnet-diagnose-autopilot` 决定调用几次、给谁看什么、怎么合并结论；`dotnet-diagnose` 只负责单次调用内的证据解读。本 skill 不直接读取 `dotnet-diagnose-triage` 的判据，只经由 agent 间接消费。

## 触发词 / 调用方式

自主分诊、自动分析这份 dump、帮我判断这个根因靠不靠谱、交叉验证一下这个诊断结论、autopilot triage、autonomous .NET diagnosis。

## 业务逻辑流程图

```
┌─────────────────────────────────────────┐
│ 执行前置校验                            │
│ agent 可用性 / 素材是否提供 / 落盘目录  │
└────────────────────┬────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│ Step 1: 素材类型识别                    │
│ 单时点 / 崩溃日志 / 时间序列 / 不可用   │
└────────────────────┬────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│ Step 2: 首次分析（Task 派发）           │
│ 强制逐字原样转发 dotnet-diagnose 回复   │
└────────────────────┬────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│ Step 3: 解析首次结论强度                │
│ 已确认 / 推测 / 超出覆盖 / 候选集穷尽   │
└────────────────────┬────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│ Step 4: 触发判定——仅"推测"触发第二次  │
└────────────────────┬────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│ Step 5: 第二次分析（盲态，仅触发时执行）│
│ 全新 Task，零信息传递                   │
└────────────────────┬────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│ Step 6: 结论比对、报告合成与落盘        │
│ 一致→合并交叉确认；不一致→并列标🔴复核  │
└─────────────────────────────────────────┘
```

## 产出物数据流

原始诊断素材（用户提供）
  → dotnet-diagnose-autopilot（素材识别 + 一次或两次调度 + 结论比对）
  → 结构化报告（Markdown，五段：素材摘要/首次分析/复核分析/一致性判定/最终建议）
  → 同时落盘至 `$HOME/dd-autopilot/report-<timestamp>.md`（仓库外）
  → 人工接手（一致时直接参考最终建议；不一致时人工裁决两份结论）

## 依赖关系图

```
用户
 │ 提供原始诊断素材
 ▼
★ dotnet-diagnose-autopilot
 │ 经 Task 工具调度（一次或两次，互相独立）
 ▼
optimus-devops-plugin:dotnet-diagnose（agent）
 │ 加载（承载层，agent 内部完成，本 skill 不感知）
 ▼
optimus-devops-plugin:dotnet-diagnose-triage（skill）
 │ 读取（判据来源）
 ▼
knowledge-base/dotnet-debugging/
```

本 skill 不加载任何 skill（`allowed-tools` 不含 `Skill`），只经 `Task` 工具调度 agent；与 `dotnet-diagnose-triage` 之间无直接依赖，全部间接经由 agent。
```

- [ ] **Step 3: 提交**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/README.md
git commit -m "$(cat <<'EOF'
docs(devops-skills): dotnet-diagnose-autopilot 补全 README.md

- 六章节齐备：所处层级、触发词、业务流程图、数据流、依赖关系图

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 7: 目录结构补全——CHANGELOG.md 与 known-issues.md

**Files:**
- Create: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/CHANGELOG.md`
- Create: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/known-issues.md`

**Interfaces:**
- Consumes: Task 1-6 完成的全部正文变更内容（用于撰写 CHANGELOG 的 Added 条目）
- Produces: `CHANGELOG.md`（`.claude/rules/doc-conventions.md` 强制要求，新建 skill 起始版本 `[1.0.0]`）；`known-issues.md`（本仓 skill 持续优化约定要求，本次先建空表 + darwin-skill 基线待办说明，实际基线评估在 Task 10 执行）

- [ ] **Step 1: 写入 CHANGELOG.md**

```markdown
## [1.0.0] - 2026-09-19

### Added
- 新建 skill：`dotnet-diagnose` agent 的自主分诊编排层，实现盲态双活二次分析机制
- 主干六步：素材类型识别、首次分析（Task 派发）、结论强度解析、触发判定（仅"推测"触发复核）、第二次盲态分析、结论比对与报告落盘
- 执行前置校验（agent 可用性 / 素材是否提供 / 落盘目录可写）与失败处理表（五种失败情形）
- 报告固定落盘至 `$HOME/dd-autopilot/report-<timestamp>.md`（仓库外，按 dump 处置合规版本库隔离要求）
```

- [ ] **Step 2: 写入 known-issues.md**

```markdown
# dotnet-diagnose-autopilot · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

## darwin-skill 基线评估

待补——按本仓约定，新 skill 交付后必须跑一次基线评估建立初始分数记录（见本计划 Task 10）。

## 待处理问题

（暂无）
```

- [ ] **Step 3: 提交**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/CHANGELOG.md plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/known-issues.md
git commit -m "$(cat <<'EOF'
docs(devops-skills): dotnet-diagnose-autopilot 补全 CHANGELOG 与 known-issues

- CHANGELOG.md 起始 1.0.0，记录本次新建的全部能力
- known-issues.md 建立空表，darwin-skill 基线评估留待 Task 10

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 8: 新增 eval case（CI `new-skill-eval-case` 门禁强制要求）

**Files:**
- Create: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/evals/01-memory-growth-single-sample/prompt.md`
- Create: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/evals/01-memory-growth-single-sample/graders/criteria.md`

**Interfaces:**
- Consumes: `dotnet-diagnose-triage/test-cases/golden.md` 测例 2（单份 dumpheap 不足以判"持续增长"，预期强度"推测"）作为素材来源——选它是因为"推测"恰好是触发本 skill 第二次调用的唯一条件，能考到 Step 4/5 的分支
- Produces: 一个可被 `.githooks/check_new_skill_eval_case.py` 识别为合法 case 的目录（含 `prompt.md`），供 CI 门禁通过；不要求在本地真实跑通（同仓库既有 `wpf-code-review` 六个 case 同样因缺 `ANTHROPIC_API_KEY` 在 CI 里跑不了，仅形态合规）

- [ ] **Step 1: 确认门禁脚本对 case 目录的识别条件**

```bash
grep -n "CASE_MARKERS\|EVAL_DIR" .githooks/check_new_skill_eval_case.py
```

Expected: `EVAL_DIR = "evals"`，`CASE_MARKERS = ("case.yaml", "prompt.md")`——只需 `evals/<any-name>/prompt.md` 存在即满足。

- [ ] **Step 2: 写入 prompt.md**

```markdown
---
max_turns: 20
runs: 1
allowed_tools: [Task, Write, Read]
---

我这边一个 WPF 应用内存一直在涨，抓了一次 !dumpheap -stat（进程已经退出，没法再抓第二次了）：

```
              MT    Count    TotalSize Class Name
00007ffa1c3d4210  1847293    206896816 MyApp.Models.OrderItem
00007ffa1b9a1188   412887      3303100 System.String
00007ffa1b9c2340    98211      1257008 System.Object[]
00007ffa1c3d5998     8291       663280 System.Collections.Generic.List`1[[MyApp.Models.OrderItem, MyApp]]
00007ffa1b9a0d10     2104        10192 Free
Total 2368986 objects
```

帮我自动分诊一下，判断根因，如果把握不大就交叉验证一下再告诉我结论。
```

- [ ] **Step 3: 写入 graders/criteria.md**

```markdown
---
type: llm
weight: 1
---

应体现以下要点：1) 识别出这是单时点 dump/SOS 证据（含 MT/Count/TotalSize 列）；2) 首次分析结论强度应为"推测"而非"已确认"（单份 dumpheap 不足以证明"持续增长"，只能说明某类型实例多）；3) 因强度为"推测"而触发了第二次独立分析（复核分析段落不应是"未触发"）；4) 最终报告含素材摘要/首次分析/复核分析/一致性判定/最终建议五段结构；5) 若两次分析结论不一致，应并列展示并标记需人工复核，不擅自取舍。
```

- [ ] **Step 4: 校验门禁能正确识别新增 case（本地模拟增量 diff）**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/evals/
git status --short plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/evals/
```

Expected: 两个文件均显示为 `A`（新增，已暂存）。CI 侧的实际判定依赖 PR 的 base/head diff，本地无法完全模拟，留待 Task 12 的 PR 流程中由 `new-skill-eval-case` job 实跑验证。

- [ ] **Step 5: 提交**

```bash
git commit -m "$(cat <<'EOF'
test(devops-skills): dotnet-diagnose-autopilot 新增 eval case

- 01-memory-growth-single-sample：单份 dumpheap 场景，考触发第二次分析的"推测"强度分支
- CI new-skill-eval-case 门禁强制要求新增 skill 必须带 eval case

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 9: 插件版本升级——两份 plugin.json 同步升 Minor

**Files:**
- Modify: `plugins/optimus-devops-plugin/.claude-plugin/plugin.json`
- Modify: `plugins/optimus-devops-plugin/.codex-plugin/plugin.json`

**Interfaces:**
- Consumes: 无（版本号是独立于 skill 正文内容的元数据）
- Produces: 两份 `plugin.json` 的 `version` 字段从 `1.2.4` 升到 `1.3.0`——Task 12 的 PR 流程中 `.githooks/pre-commit` 依赖两份文件同值这一状态才能通过

⚠️ 按 `AGENTS.md` 触发矩阵："新增 skill" → 插件两份 `plugin.json` 同步升 **Minor**。当前 `1.2.4` 的 Minor 升级是 `1.3.0`（Patch 位归零，见 `AGENTS.md` "升 Minor 时 PATCH 归零"）。

- [ ] **Step 1: 读取当前版本号确认起点**

```bash
grep '"version"' plugins/optimus-devops-plugin/.claude-plugin/plugin.json plugins/optimus-devops-plugin/.codex-plugin/plugin.json
```

Expected: 两处均为 `"version": "1.2.4"`。

- [ ] **Step 2: 修改 `.claude-plugin/plugin.json`**

把 `"version": "1.2.4"` 改为 `"version": "1.3.0"`，其余字段不动（包括已有的 `"agents": ["./agents/dotnet-diagnose.md"]`——本次新增的是 skill 不是 agent，不需要改动这个数组）。

- [ ] **Step 3: 修改 `.codex-plugin/plugin.json`**

把 `"version": "1.2.4"` 改为 `"version": "1.3.0"`，其余字段不动。

- [ ] **Step 4: 校验两份文件版本同值**

```bash
python .githooks/check_plugin_versions.py .
```

Expected: 脚本正常退出（退出码 0），不报 `optimus-devops-plugin` 相关的不一致问题。

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-devops-plugin/.claude-plugin/plugin.json plugins/optimus-devops-plugin/.codex-plugin/plugin.json
git commit -m "$(cat <<'EOF'
feat(devops-plugin): 版本升级 1.2.4 → 1.3.0

- 新增 dotnet-diagnose-autopilot skill，两份 plugin.json 同步升 Minor

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 10: darwin-skill 基线评估

**Files:**
- Modify: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/known-issues.md`
- Modify: `.claude/skills/darwin-skill/results.tsv`（仓库根的门禁产物账本，九列 TSV）

**Interfaces:**
- Consumes: Task 1-9 完成后的完整 SKILL.md 正文（darwin-skill 9 维 rubric 的评分对象）
- Produces: `known-issues.md` 的"darwin-skill 基线评估"节填入实际分数；`results.tsv` 追加一行 `status=baseline` 记录

⚠️ 本仓 `AGENTS.md` 规定"Minor/Major 升级前必须用 darwin-skill 给改动的 skill 评分：新分 ≥ 改动前分数才可提交"，但这是**新建** skill，无"改动前分数"可比——本任务对应 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md` § 1"创建后强制基线评估"，只建基线，不做棘轮比较。

- [ ] **Step 1: 用 darwin-skill 评估新建的 SKILL.md**

按 darwin-skill 本体（全局安装于 `~/.claude/skills/darwin-skill/`，非本仓副本）的 9 维 rubric 逐项评分。以下是评分执行方式的说明，具体分值取决于本 skill 落地后的真实 SKILL.md 内容（Task 1-5 已写定的正文），须在执行本任务时实际读取该文件评出：

```bash
wc -l plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/SKILL.md
```

参照 `dotnet-diagnose-triage` 首次基线评估的模式（`known-issues.md` 已有先例：`full_test (partial)` 模式，dim7/dim8 用真实调用证据但缺 without-skill 对照）——本次同样按 `full_test (partial)` 模式评估，因为 Task 8 的 eval case 因缺 `ANTHROPIC_API_KEY` 在 CI 里跑不了（与 `wpf-code-review` 六个 case 同样的已知限制），dim8"实测表现"须靠人工干跑（读完 skill 模拟一次典型 prompt 的执行思路）而非真实 API 调用验证，按 darwin-skill 本体规则须在 `results.tsv` 标注 `dry_run` 而非 `full_test`。

九维评分要点（对照 `~/.claude/skills/darwin-skill/SKILL.md` 的 rubric 定义）：

| # | 维度 | 权重 | 本 skill 预期落点 |
|---|---|---:|---|
| 1 | frontmatter 质量 | 7 | description 含时机边界（"给定原始素材"）+ 多个触发词 + 转出去向说明，预期中高分 |
| 2 | 工作流清晰度 | 12 | 六步编号清晰，每步输入输出明确，预期高分 |
| 3 | 失败模式编码 | 12 | 失败处理表五种情形全为"若 X 则 Y"形态，预期高分 |
| 4 | 检查点设计 | 6 | ⚠️ 与 `dotnet-diagnose-triage` 基线同样的短板——本 skill 全程无 `🔴 CHECKPOINT` 显式标记（素材不可用/agent 不可用均为自动短路而非询问用户），预期中低分，**是首选优化靶点** |
| 5 | 可执行具体性 | 17 | dispatch prompt 模板逐字给出、四态判定关键字明确、落盘路径固定，预期高分 |
| 6 | 资源整合度 | 4 | 无 `references/` 子目录（本 skill 全部规则内联在 SKILL.md，未下钻），预期中等 |
| 7 | 整体架构 | 12 | 与 agent/triage 边界清晰、六步无冗余，预期高分 |
| 8 | 实测表现 | 23 | `dry_run` 模式（无 API key），按 darwin-skill 规则该维度分数上限受限，须在 `results.tsv` 显式标注 |
| 9 | 反例与黑名单 | 6 | 概述节已有"不做什么"，但**未设独立的反例章节**——不同于 spec 文档的 § 8，SKILL.md 正文本身没有把 spec 的反例清单迁移进来，预期中低分，**是第二个潜在优化靶点** |

- [ ] **Step 2: 记录评分到 `known-issues.md`**

把 `known-issues.md` 中"darwin-skill 基线评估"节的"待补"替换为实际评出的总分与九维明细表（格式参照 `dotnet-diagnose-triage/known-issues.md` 的"darwin-skill 基线评估"节：总分表 + 逐维度表 + "下一轮优化的首选靶点"一句）。

- [ ] **Step 3: 追加 `results.tsv` 一行**

```bash
echo -e "$(date +%Y-%m-%dT%H:%M)\tbaseline\tdotnet-diagnose-autopilot\t-\t<实评总分>\tbaseline\t-\t新建 skill 基线：编排层调度既有 agent，dim4（检查点设计）与 dim9（反例章节缺失）为首选优化靶点\tdry_run" >> .claude/skills/darwin-skill/results.tsv
```

⚠️ `results.tsv` 被 `.gitignore` 排除，暂存时**必须带 `-f`**（见 `AGENTS.md` "darwin-skill 评分门禁"节），否则 `git add` 报错退出码 1。

- [ ] **Step 4: 提交（结果文件需 `-f`）**

```bash
git add plugins/optimus-devops-plugin/skills/dotnet-diagnose-autopilot/known-issues.md
git add -f .claude/skills/darwin-skill/results.tsv
git commit -m "$(cat <<'EOF'
docs(devops-skills): dotnet-diagnose-autopilot darwin-skill 基线评估

- 新建 skill 基线记录，dry_run 模式（无 ANTHROPIC_API_KEY，与既有 wpf-code-review 六个 case 同样限制）
- 首选优化靶点：dim4 检查点设计、dim9 反例章节缺失

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

### Task 11: 本地功能验证

**Files:**
- 不新增/修改文件；本任务只做交互验证，若验证中发现 Task 1-10 已写入内容有缺陷，返回对应 Task 所在文件用 `Edit` 修正后重新验证

**Interfaces:**
- Consumes: Task 1-10 完成后的完整 skill 目录（`SKILL.md`/`README.md`/`CHANGELOG.md`/`known-issues.md`/`evals/`）与已升级的插件版本
- Produces: 一次真实的 `--plugin-dir` 无头验证记录（人工确认，无持久化产物）——Task 12 的 PR 描述里"测试计划"一节引用本任务的验证结论

按 `.claude/skills/test-locally/SKILL.md` 的方法：本次改动只涉及 `optimus-devops-plugin` 一个插件，用单插件加载（更快、避免其它插件干扰）。

- [ ] **Step 1: 确认当前在仓库根目录**

```bash
pwd
git rev-parse --show-toplevel
```

Expected: 两者输出的路径指向同一仓库根（`--plugin-dir .` 依赖相对路径，若不在根目录执行会报错找不到插件）。

- [ ] **Step 2: 无头模式验证 skill 能否被正确触发并调度到 agent**

```bash
claude --plugin-dir ./plugins/optimus-devops-plugin -p "自主分诊：帮我分析下面这份 dump

              MT    Count    TotalSize Class Name
00007ffa1c3d4210  1847293    206896816 MyApp.Models.OrderItem
00007ffa1b9a1188   412887      3303100 System.String
Total 2368986 objects"
```

Expected：输出中能观察到以下三点，缺一即为验证未通过：
1. 报告含"素材摘要"段落，判定为"单时点证据"（命中 `MT`/`Count`/`TotalSize` 列）——验证 Step 1 的证据类型识别表生效
2. 报告含"首次分析"段落，内容是 `dotnet-diagnose` agent 的输出格式（结论/修复方向/台账交接块/免责声明四段），而非外层会话自己的转述总结——验证 Task 2 的"逐字原样转发"约束在真实调用中真的生效，这是本任务**最容易暴露问题的一环**：如果 dispatch prompt 措辞不够强硬，外层仍可能忍不住加一句总结
3. 若"结论"段落命中"推测"关键字，报告应能看到"复核分析"段落含第二次独立调用的痕迹（而非"未触发"占位文字）——验证 Step 4 的触发判定与 Step 5 的盲态第二次调用真实发生

- [ ] **Step 3: 核对落盘文件确实写到仓库外**

```bash
ls -la "$HOME/dd-autopilot/" 2>&1 | tail -5
```

Expected: 存在一个新的 `report-<timestamp>.md` 文件，内容与 Step 2 对话中输出的报告一致；确认该目录不在本仓库工作树内（`git status` 不会显示它，因为它本就在 `$HOME` 而非仓库路径下）。

- [ ] **Step 4: 若 Step 2 未按预期触发，定位问题并修正**

| 观察到的现象 | 可能原因 | 修正位置 |
|---|---|---|
| 报告缺失"复核分析"实际内容（应触发但没触发） | dispatch prompt 转发保真度不够，外层总结掩盖了"推测"关键字 | 回到 Task 2 写入的 Step 2 dispatch prompt，检查措辞是否足够强硬 |
| Step 1 素材类型判定错误 | 判定表的特征列缺失该类素材的常见列名变体 | 回到 Task 1 的 Step 1 判定表补充特征 |
| `Task` 工具报错找不到 `optimus-devops-plugin:dotnet-diagnose` | 单插件加载模式下 agent 声明路径与实际文件不符 | 检查 `.claude-plugin/plugin.json` 的 `agents` 数组路径（本次未改动该字段，若报错说明该字段本身早已存在问题，需另行报告，不在本计划修复范围） |

若发生修正，修正后重新执行 Step 2-3 直到验证通过；每次修正后按其所属 Task 的提交规范单独 `git commit`（修正 Task 1 的内容用 Task 1 风格的 commit message，以此类推），不在本任务内合并提交。

- [ ] **Step 5: 记录验证结论（不提交文件，仅供 Task 12 引用）**

本步骤无需 `git commit`——本任务不产出新文件，验证结论以对话形式呈现，供撰写 Task 12 的 PR 描述时引用："已用 `--plugin-dir` 单插件加载模式实跑验证：素材类型识别、逐字转发、触发判定与落盘路径均按预期工作"。

### Task 12: PR 流程——推分支、开 PR、等 CI、合并、清理

**Files:**
- 不涉及仓库文件改动；本任务操作 git/GitHub 状态（分支、PR、合并）

**Interfaces:**
- Consumes: Task 1-11 在特性分支 `feat/dotnet-diagnose-autopilot` 上积累的全部提交
- Produces: `master` 分支上的一个 squash commit，包含本计划全部改动；无后续任务依赖本任务的产出（这是最后一个任务）

本任务严格按 `commit-cc-plugin` skill 的"第五步 — 推分支、开 PR、等 CI、合并"执行，不重复该 skill 已详细规定的内容，只列出本次改动的具体取值。

- [ ] **Step 1: 确认 `gh` 可用性（CHECKPOINT）**

```bash
gh auth status
```

Expected: 输出含 `✓ Logged in to github.com`。若未登录或未安装，按 `commit-cc-plugin` skill 前置检查表处置（`winget install GitHub.cli` 或 `gh auth login`），不在本计划内代为安装。

- [ ] **Step 2: 确认特性分支状态与提交历史完整**

```bash
git branch --show-current
git log --oneline master..HEAD
```

Expected: 当前分支为 `feat/dotnet-diagnose-autopilot`；提交历史包含 Task 1-10（及 Task 11 若有修正提交）产生的全部 commit，数量与内容不缺不重复。

- [ ] **Step 3: 推送特性分支**

```bash
git push -u origin feat/dotnet-diagnose-autopilot
```

- [ ] **Step 4: 生成 PR body 并开 PR**

```bash
cat > /tmp/pr-body.md <<'EOF'
新建 `dotnet-diagnose-autopilot` skill，作为编排层调度既有 `dotnet-diagnose` agent：自动识别诊断素材类型（单时点/崩溃日志/时间序列/不可用），首次分析结论强度为"推测"时用完全独立、零信息传递的第二次盲态调用做交叉验证，两次结论一致则合并标注交叉确认、不一致则并列展示并标记需人工复核，产出结构化报告落盘至 `$HOME/dd-autopilot/`（仓库外，遵循 dump 处置合规）。

- SKILL.md：六步主干（素材识别 → 首次分析 → 强度解析 → 触发判定 → 盲态第二次分析 → 报告合成落盘）+ 执行前置校验 + 失败处理
- README.md：六章节规范；CHANGELOG.md：起始 1.0.0；known-issues.md：darwin-skill 基线评估
- evals/01-memory-growth-single-sample：新增 skill 的 CI 门禁强制要求
- 插件版本 1.2.4 → 1.3.0（两份 plugin.json 同步升 Minor）
- 已用 `--plugin-dir` 单插件加载模式实跑验证：素材类型识别、逐字转发、触发判定与落盘路径均按预期工作

不修改 `dotnet-diagnose` agent 与 `dotnet-diagnose-triage` skill 的任何既有文件——本次是纯新增，零重叠边界见 `docs/superpowers/specs/2026-09-19-dotnet-diagnose-autopilot-design.md` § 2。

测试计划：
- [x] `.githooks/pre-commit` 七项提交门禁本地跑通
- [x] `--plugin-dir` 单插件加载模式无头验证素材识别、转发保真、触发判定
- [ ] CI `new-skill-eval-case` job 确认识别到 `evals/01-memory-growth-single-sample/`
- [ ] CI `plugin-validate` 确认命中 `optimus-devops-plugin` 目录

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
gh pr create --base master --head feat/dotnet-diagnose-autopilot \
  --title "feat(devops-skills): 新增 dotnet-diagnose-autopilot 自主分诊工作流" \
  --body-file /tmp/pr-body.md
```

- [ ] **Step 5: 等待六项必需检查全绿**

```bash
gh pr checks feat/dotnet-diagnose-autopilot --required --watch --fail-fast
```

Expected: 退出码 0。六项必需检查逐字为 `gates-hooks`、`gates-tests`、`gates-data`、`plugin-validate`、`new-skill-eval-case`、`actionlint`（清单真源是服务端 ruleset，此处只是复述预期）。

⚠️ 本次改动落在 `plugins/` 下，`plugin-validate` job 的日志中应能看到命中 `optimus-devops-plugin` 目录名；`new-skill-eval-case` job 应能识别到 Task 8 新增的 `evals/01-memory-growth-single-sample/prompt.md`。若任一必需检查失败，退出码为 1：

```bash
gh pr checks feat/dotnet-diagnose-autopilot --required --json name,bucket,link
gh run view <run-id> --log-failed
```

⛔ 出现失败检查时停下报告，不自动重试、不自动改代码、不使用 `--no-verify` 或强推绕过；按报错内容定位到本计划对应 Task 的产出修正，修正后创建新的提交（不 amend 已推送的提交），重新触发本 Step。

- [ ] **Step 6: 合并**

```bash
git show -s --format=%b HEAD > /tmp/squash-body.md
PR_NUMBER=$(gh pr view feat/dotnet-diagnose-autopilot --json number --jq .number)
gh pr merge feat/dotnet-diagnose-autopilot --squash \
  --subject "feat(devops-skills): 新增 dotnet-diagnose-autopilot 自主分诊工作流 (#${PR_NUMBER})" \
  --body-file /tmp/squash-body.md
```

⛔ 必须显式传 `--subject`（含 `(#N)`）与 `--body-file`（取最后一次 commit 的正文，保留 `Co-Authored-By` 尾注），理由见 `commit-cc-plugin` skill 动作 4 的两处静默失效说明。

- [ ] **Step 7: 回主干并自检 `Co-Authored-By` 未被转义**

```bash
git switch master && git pull --rebase origin master
git log -1 --format=%B | git interpret-trailers --parse
```

Expected: 输出 `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`，尖括号为真尖括号（非 `&lt;`/`&gt;` HTML 实体）。

- [ ] **Step 8: 清理特性分支（先本地、后远端）**

```bash
git branch -d feat/dotnet-diagnose-autopilot
git push origin --delete feat/dotnet-diagnose-autopilot
```

Expected: 本地删除成功（squash 后 `-d` 只给 warning 不报错，因为 `origin/feat/dotnet-diagnose-autopilot` 此时仍存在、判定走远端追踪引用）；随后远端删除成功。若本地 `-d` 被拒（顺序颠倒或其他原因），先用 `git rev-parse feat/dotnet-diagnose-autopilot^{tree}` 与 `git rev-parse master^{tree}` 比对树对象是否相等，相等再改用 `-D`，不确认相等不得强删。

至此本计划全部任务完成：`dotnet-diagnose-autopilot` skill 已合入 `master`，与 `dotnet-diagnose` agent、`dotnet-diagnose-triage` skill 构成完整的自主分诊工作流。