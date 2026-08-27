# Eval 工作区结构详解

> 讲解性内容，无规范语气。支撑 `rules/03-skill-evaluation.md`（质量评估）。描述"跑 eval 迭代"的完整工作区组织方式与各文件形态。

## 为什么需要规范的工作区

eval 迭代会产生大量产物（每次运行的输出、评分、统计）。松散的组织会让跨轮对比无从下手——规范的工作区结构让每一轮迭代自成目录、可独立对比，也便于脚本聚合。

## 完整目录结构

skill 目录旁放一个 workspace 目录，每轮迭代一个 `iteration-N/`，每个用例一个 eval 目录，内含 with/without 两组子目录：

```
csv-analyzer/
├── SKILL.md
└── evals/
    └── evals.json
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

人工手写的只有 `evals/evals.json`；`grading.json`、`timing.json`、`benchmark.json` 由 eval 过程（agent/脚本/人工）产出。

## 各文件形态

### evals.json（人工手写，唯一手写文件）

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV of monthly sales data in data/sales_2025.csv. Can you find the top 3 months by revenue and make a bar chart?",
      "expected_output": "A bar chart image showing the top 3 months by revenue, with labeled axes and values.",
      "files": ["evals/files/sales_2025.csv"],
      "assertions": [
        "The output includes a bar chart image file",
        "The chart shows exactly 3 months",
        "Both axes are labeled"
      ]
    }
  ]
}
```

`assertions` 是首轮输出后再补的（首轮前常不知道"好"长什么样）。

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
