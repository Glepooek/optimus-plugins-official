# Eval 工作区结构详解

> 讲解性内容，无规范语气。支撑 `rules/03-skill-evaluation.md`（质量评估）。描述"跑 eval 迭代"的完整工作区组织方式与各文件形态。
>
> 更新历史：2026-09-13 case 形态由 `evals/evals.json` 改为官方 `claude plugin eval` 格式（`<case>/prompt.md` + `graders/*.md`），新增 `evals/results/` 产物落点与 `aggregate-result.json`。

⚠️ **本篇同时描述两条路径，读时先分清在哪一条**：用官方 `claude plugin eval` 跑（case 形态、`aggregate-result.json`），与手工跑迭代循环（`iteration-N/` 工作区、`timing.json`/`grading.json`/`benchmark.json`/`feedback.json`）。**case 形态只有官方一种，工作区形态只在手工路径下需要**；官方 CLI 不产出后面那四个文件，而它们承载的方法论（delta 判断、模式分析、人工 review）官方也没有对等物。

## 为什么需要规范的工作区

eval 迭代会产生大量产物（每次运行的输出、评分、统计）。松散的组织会让跨轮对比无从下手——规范的工作区结构让每一轮迭代自成目录、可独立对比，也便于脚本聚合。

## 完整目录结构

skill 目录旁放一个 workspace 目录，每轮迭代一个 `iteration-N/`，每个用例一个 eval 目录，内含 with/without 两组子目录：

```
csv-analyzer/
├── SKILL.md
└── evals/
    ├── top-months-chart/          # 一个 case 一个目录
    │   ├── prompt.md              # frontmatter 是 case 字段，正文是用户提问
    │   └── graders/
    │       └── criteria.md        # frontmatter 是 type/weight，正文是判据
    ├── clean-missing-emails/
    │   ├── prompt.md
    │   └── graders/
    │       └── criteria.md
    └── results/                   # ⚠️ CLI 的运行产物，必须 gitignore（见下）
        └── 2026-09-13T14-22-21-053Z/
            └── aggregate-result.json
csv-analyzer-workspace/
└── iteration-1/
    ├── eval-top-months-chart/
    │   ├── with_skill/
    │   │   ├── outputs/       # 本次运行产出的文件
    │   │   ├── timing.json    # token 数与耗时
    │   │   └── grading.json   # assertion 结果
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    ├── eval-clean-missing-emails/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── timing.json
    │   │   └── grading.json
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    └── benchmark.json         # 聚合统计
```

🔴 **`evals/results/` 必须 gitignore，理由有两层，第二层比第一层要紧。** `claude plugin eval` 把 `aggregate-result.json` 写进 `<eval 目录>/results/<ISO 时间戳>/`，而 eval 目录默认就叫 `evals/`——**工具的输出目录与它的输入目录同名同级**。实测两个落点：在插件根运行落 `plugins/<插件>/evals/results/`，在 skill 目录内运行落该 skill 自己的 `evals/results/`。

- 第一层：产物不该入库
- 🔴 第二层：`results/` 是一个**没有 `case.yaml`/`prompt.md` 的子目录**，落在 `evals/` 下时会被「每个 case 目录都要含 marker」这类校验判成「建了一半的 case」——**跑一次 eval 就让下一次提交失败**，门禁反过来惩罚使用被它保护的东西。因此校验器侧也要按名字跳过 `results/`。两道都要：只忽略仍会阻断提交，只跳过则产物会被误提交

（本仓已加 `.gitignore` 的 `evals/results/`，校验器侧见 `.githooks/check_new_skill_eval_case.py`。）

人工手写的只有 `prompt.md` 与 `graders/*.md`；`aggregate-result.json` 由 CLI 产出，`grading.json`、`timing.json`、`benchmark.json` 由手工跑的 eval 过程（agent/脚本/人工）产出。

## 各文件形态

### prompt.md + graders/*.md（人工手写，唯一手写的两类文件）

```markdown
<!-- evals/top-months-chart/prompt.md -->
---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

I have a CSV of monthly sales data in data/sales_2025.csv. Can you find the
top 3 months by revenue and make a bar chart?
```

```markdown
<!-- evals/top-months-chart/graders/criteria.md -->
---
type: llm
weight: 1
---

A bar chart image showing the top 3 months by revenue, with labeled axes and values.
```

**拆成两个文件而非一个 `case.yaml`（官方等价写法），是为了让「改提问」与「改判据」变成两次互不牵连的改动**——提问措辞会随 skill 的 `description` 调整反复微调，而判据一旦定下通常不动。

`graders/` 下可以放多个文件，每个是一条 assertion，各带自己的 `weight`。**assertion 是首轮输出后再补的**（首轮前常不知道"好"长什么样）——在这个格式下，「首轮只写 prompt + 判据」落地为：先只建 `prompt.md` 与一个描述性的 `llm` grader，看过首轮输出后再补机械可判的 `regex`/`tool_used`/`file_exists` grader。

⚠️ `allowed_tools` 若要让被测 skill 能被触发，**必须含 `Skill`**——漏了它会让全部正例失败，而失败表象与「`description` 匹配不上」完全相同、无法区分。

### aggregate-result.json（官方 CLI 产出，一份承担 timing + grading + benchmark 三类）

落在 `evals/results/<ISO 时间戳>/`。关键字段：

```json
{
  "schemaVersion": 1,
  "claudeVersion": "2.1.270",
  "durationSeconds": 207,
  "costUsd": 2.66,
  "judgeCostUsd": 0,
  "partial": false,
  "casesTotal": 20,
  "casesPassed": 19,
  "overallScore": 0.95
}
```

⚠️ **`casesTotal` 是唯一能直接读到「发现了几个 case」的地方**——命令行摘要只打印**跑过的**数量。少发现一个 case 与全部通过，在退出码上不可区分。

⚠️ 每个 run 另有 `stopReason`：值为 `max_turns` 说明回答**被硬截断**。这对 `tool_used` 无害（只数调用次数），但 `llm` grader 读的正是最终回答文本，截断会让评委把「答案没写完」判成「答得不对」，产出**稳定复现的假失败**——稳定的错误比抖动的错误更难被识别为错误。因此引入 `llm` grader 时要同时看 `max_turns` 够不够，不只是调 `--runs`。

⚠️ `judgeCostUsd` 为 0 说明**评委一次都没被调用过**（套件里没有付费 grader）。此时「评委的判据稳定性」这件事是零观测状态，不要把它读成「评委表现良好」。

### timing.json（每次运行记录）

```json
{ "total_tokens": 84852, "duration_ms": 23332 }
```

Claude Code 中，子代理任务完成通知会带 `total_tokens` 和 `duration_ms`——**立即保存**，别处不持久化。

### grading.json（每条 assertion 一个结果 + evidence）

```json
{
  "assertion_results": [
    { "text": "The chart shows exactly 3 months", "passed": true, "evidence": "Chart displays bars for March, July, and November" },
    { "text": "Both axes are labeled", "passed": false, "evidence": "Y-axis is labeled 'Revenue ($)' but X-axis has no label" }
  ],
  "summary": { "passed": 3, "failed": 1, "total": 4, "pass_rate": 0.75 }
}
```

机械可判的 assertion（合法 JSON、行数、文件存在）用校验脚本，比 LLM 判断可靠且可复用。

### benchmark.json（每轮聚合）

```json
{
  "run_summary": {
    "with_skill": {
      "pass_rate": { "mean": 0.83, "stddev": 0.06 },
      "time_seconds": { "mean": 45.0, "stddev": 12.0 },
      "tokens": { "mean": 3800, "stddev": 400 }
    },
    "without_skill": {
      "pass_rate": { "mean": 0.33, "stddev": 0.10 },
      "time_seconds": { "mean": 32.0, "stddev": 8.0 },
      "tokens": { "mean": 2100, "stddev": 300 }
    },
    "delta": { "pass_rate": 0.50, "time_seconds": 13.0, "tokens": 1700 }
  }
}
```

`delta` 告诉决策：skill 加了 13 秒但 pass_rate 提 50 个百分点 → 大概率值；token 翻倍只换 2 个百分点 → 可能不值。

### feedback.json（人工 review 记录，每个用例一条）

```json
{
  "eval-top-months-chart": "The chart is missing axis labels and the months are in alphabetical order instead of chronological.",
  "eval-clean-missing-emails": ""
}
```

空字符串 = 该用例通过 review。反馈要具体可执行（"缺坐标轴标注"）而非"看起来不好"。

⚠️ **`feedback.json` 是本篇唯一没有官方对等物的文件。** `aggregate-result.json` 承担了 timing/grading/benchmark 三类数据，但人工 review 的记录官方不产出、也无处存放——用官方 CLI 跑时这一份仍须自己维护，否则 `rules/03-skill-evaluation.md` § 7「人工 review」与 § 8「迭代循环」所需的三类信号里就少了一类。

## 运行隔离

- 每次运行从**干净上下文**开始——无上次运行/开发过程残留
- 有子代理环境（Claude Code）：每个子任务天然隔离
- 无子代理：用独立会话
- 每次运行提供：skill 路径（基线则不给）、测试 prompt、输入文件、输出目录

## 改进既有 skill 时的基线

用**上一版本快照**作基线，而非裸 without-skill：

```bash
cp -r <skill-path> <workspace>/skill-snapshot/
```

基线运行指向快照，输出存 `old_skill/outputs/`。这样对比的是"新旧版本"而非"有 skill vs 无 skill"。

## 适用性

- **新 skill**：with-skill vs without-skill 验证是否增值
- **既有 skill**：新版本 vs 旧版本快照验证是否改善

## 权威参考

- [评估 skill 输出质量 — 完整版](https://agentskills.io/skill-creation/evaluating-skills)
