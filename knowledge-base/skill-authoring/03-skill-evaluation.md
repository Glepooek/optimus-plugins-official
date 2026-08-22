# 03 · skill 质量评估

> 更新历史：2026-08-22 创建。
>
> 来源：[评估 skill 输出质量](https://agentskills.io/skill-creation/evaluating-skills)。评估回答"skill 是否可靠地产出好结果"——用 eval 驱动迭代，让改进有据可依。

## 1. 测试用例设计

一个测试用例含三部分：**prompt**（真实用户消息）、**expected output**（成功长什么样的描述）、**files**（可选输入文件）。

- **必须**：测试用例存到 `evals/evals.json`（skill 目录内）
- **必须**：先只写 prompt + expected output，**不做**具体 pass/fail 检查——看过首轮结果后再加 assertions
- **应该**：先做 2-3 个用例，不过度投入；首轮结果后再扩
- **必须**：prompt 多样化——不同措辞、细节量、正式度；含边界条件用例（畸形输入、异常请求、指令可能歧义的场景）
- **必须**：prompt 用真实上下文（文件路径、列名、个人背景），不用"process this data"这类无法测试任何东西的空泛请求

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV of monthly sales data in data/sales_2025.csv. Can you find the top 3 months by revenue and make a bar chart?",
      "expected_output": "A bar chart image showing the top 3 months by revenue, with labeled axes and values.",
      "files": ["evals/files/sales_2025.csv"]
    }
  ]
}
```

## 2. 运行方式：with-skill vs without-skill 基线

- **必须**：每个用例跑两次——**带 skill** 与**不带 skill**（或上一版本），获得基线对比
- **必须**：每次运行从干净上下文开始（无上次运行/开发过程残留）；有子代理环境（如 Claude Code）用子代理隔离，否则用独立会话
- **必须**：改进既有 skill 时，用**上一版本快照**作为基线（`cp -r` 快照后指向快照跑），而非裸 without-skill
- **应该**：每次运行记录 token 数与耗时（`timing.json`），量化 skill 的成本收益
- **应该**：工作区按 `iteration-N/eval-*/{with_skill,without_skill}/{outputs,timing,grading}.json` 组织

## 3. Assertions（断言）

- **必须**：assertions 是**可验证**的陈述——"输出是合法 JSON"、"图表有标注坐标轴"、"报告含至少 3 条建议"
- **禁止**：用"输出是好的"这类太模糊的断言
- **禁止**：用过于脆弱的断言（"输出恰好包含短语 'Total Revenue: $X'"）——正确输出换措辞就失败
- **必须**：看过首轮输出后再加 assertions（首轮前常不知道"好"长什么样）
- **应该**：机械可判的断言（合法 JSON、行数、文件存在）用校验脚本，比 LLM 判断可靠且可复用；无法分解为 pass/fail 的质量（文风、视觉设计、整体感）留给人工 review

## 4. Grading（评分）

- **必须**：每条 assertion 记 **PASS/FAIL** 并附**具体 evidence**（引用/指向输出，不只给观点）
- **必须**：PASS 要具体证据——"有个叫 Summary 的标题但只有一句含糊句子"是 FAIL，光有标签没有实质
- **应该**：评分时也审视 assertions 本身——太易（无论如何都过）、太难（好输出也失败）、不可验证的，下一轮修正
- **应该**：比较两个 skill 版本时用**盲评**——不告诉 LLM 裁判哪个版本，按自有标准打分，避免"哪个该更好"的偏见

```json
{
  "assertion_results": [
    { "text": "The chart shows exactly 3 months", "passed": true, "evidence": "Chart displays bars for March, July, and November" },
    { "text": "Both axes are labeled", "passed": false, "evidence": "Y-axis is labeled 'Revenue ($)' but X-axis has no label" }
  ],
  "summary": { "passed": 3, "failed": 1, "total": 4, "pass_rate": 0.75 }
}
```

## 5. Benchmark 聚合

- **必须**：每轮迭代完成后，按配置聚合统计存入 `benchmark.json`
- **必须**：记录 `delta`——with-skill 相对 without-skill 的 pass_rate / time / tokens 差
- **必须**：用 delta 判断 skill 值不值——加 13 秒换 pass_rate 提高 50 个百分点大概率值得；token 翻倍只换 2 个百分点可能不值
- **认知**：多轮运行时 stddev 才有意义；早期单轮聚焦原始 pass 数和 delta

## 6. 模式分析

- **必须**：移除/替换**两边都过**的 assertion——测不出 skill 价值，还虚增 with-skill pass_rate
- **必须**：调查**两边都失败**的 assertion——断言坏了 / 用例太难 / 查错了东西，下一轮修
- **必须**：重点研究**带 skill 过、不带不过**的 assertion——这是 skill 真正增值的地方，理解为什么（哪条指令/脚本起了作用）
- **必须**：结果跨运行不一致（stddev 高）时——eval 可能 flaky，或 skill 指令歧义到模型每次理解不同；加示例或更具体指引
- **应该**：查时间/token 异常——某个 eval 用时 3 倍，读它的执行记录找瓶颈

## 7. 人工 review

- **必须**：每个用例人工看实际输出 + 评分，补 assertions 没覆盖的问题
- **必须**：反馈**具体可执行**（"图表缺坐标轴标注，月份按字母序而非时间序"），不用"看起来不好"
- **应该**：反馈存 `feedback.json`，迭代时聚焦有具体投诉的用例

## 8. 迭代循环

1. 收集三类信号：**失败 assertions**（具体缺口）、**人工反馈**（整体质量问题）、**执行记录**（为何出错——忽略指令 = 指令歧义；浪费步骤 = 指令过泛/过多选项）
2. 把三类信号 + 当前 `SKILL.md` 交给 LLM 提议改进，遵循：从反馈泛化（修底层问题，不针对具体例子打补丁）、保持精简（更少更好的指令常优于穷举规则）、解释 why（"做 X 因为 Y 会导致 Z"比"ALWAYS X"更可靠）、捆绑重复工作（每次运行都重写的助手脚本 → 进 `scripts/`）
3. 应用改动，在新 `iteration-N+1/` 重跑全部用例
4. 评分聚合 → 人工 review → 重复

- **必须**：满足以下任一即停：结果满意、反馈持续为空、不再有实质改进

## 权威参考

- [评估 skill 输出质量 — 完整版](https://agentskills.io/skill-creation/evaluating-skills)
- [在 skill 中使用脚本](https://agentskills.io/skill-creation/using-scripts)（捆绑重复工作的脚本设计）
