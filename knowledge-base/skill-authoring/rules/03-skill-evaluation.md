# 03 · skill 质量评估

> 更新历史：2026-08-22 创建；2026-09-13 §1 的存放位置与用例结构改为官方 `claude plugin eval` 格式（原 `evals/evals.json` 已不再是合规位置），§2/§3 补官方工具的对应关系与默认值。
>
> 来源：[评估 skill 输出质量](https://agentskills.io/skill-creation/evaluating-skills)。评估回答"skill 是否可靠地产出好结果"——用 eval 驱动迭代，让改进有据可依。

## 1. 测试用例设计

一个测试用例含两部分：**prompt**（真实用户消息）与**判据**（成功长什么样的描述）。

⚠️ **本节 2026-09-13 由 `evals/evals.json` 改为官方 `claude plugin eval` 格式，两处结构差异容易踩空：**

- **没有 `files` 键。** 官方 case 顶层 15 个合法键（zod strict，未识别键逐个报错）是 `schema_version`/`name`/`description`/`tags`/`plugins`/`runs`/`expected_outcome`/`model`/`max_turns`/`timeout_seconds`/`allowed_tools`/`artifact_publish`/`growthbook_overrides`/`append_system_prompt`/`env`。输入文件不再是用例的一个字段，需要输入文件时靠工作区预置
- **「expected output」不是 case 的字段，它就是判据本身**——即 `llm` grader 文件的正文。两者过去被写成用例里的两个并列部分，实际是同一件事的两种包装；迁移已有素材时不需要重新发明判据措辞
- ⚠️ `expected_outcome` 这个键**不受枚举约束**，任意字符串都能通过校验，因此它不是可依赖的判据——真正的判据只在 grader 里

- **必须**：测试用例存到 `evals/<case-name>/prompt.md`（frontmatter 承载 case 字段，正文是用户提问）+ `evals/<case-name>/graders/*.md`（frontmatter 承载 `type`/`weight` 等，正文是判据描述）；单文件 `case.yaml` 是官方等价写法，二选一即可
- **必须**：先只写 prompt + 判据描述，**不做**具体 pass/fail 检查——看过首轮结果后再加 assertions（在官方格式下即「再加 grader 文件」）
- **应该**：先做 2-3 个用例，不过度投入；首轮结果后再扩
- **必须**：prompt 多样化——不同措辞、细节量、正式度；含边界条件用例（畸形输入、异常请求、指令可能歧义的场景）
- **必须**：prompt 用真实上下文（文件路径、列名、个人背景），不用"process this data"这类无法测试任何东西的空泛请求

**拆成两个文件而非一个 `case.yaml`，理由是让「改提问」与「改判据」变成两次互不牵连的改动**——提问措辞会随 skill 的 `description` 调整反复微调，而判据一旦定下通常不动。

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

## 2. 运行方式：with-skill vs without-skill 基线

- **必须**：每个用例跑两次——**带 skill** 与**不带 skill**（或上一版本），获得基线对比
- **必须**：每次运行从干净上下文开始（无上次运行/开发过程残留）；有子代理环境（如 Claude Code）用子代理隔离，否则用独立会话
- **必须**：改进既有 skill 时，用**上一版本快照**作为基线（`cp -r` 快照后指向快照跑），而非裸 without-skill
- **应该**：每次运行记录 token 数与耗时（`timing.json`），量化 skill 的成本收益
- **应该**：工作区按 `iteration-N/eval-*/{with_skill,without_skill}/{outputs,timing,grading}.json` 组织

**用官方 `claude plugin eval` 时，本节第一条 MUST 是默认行为**：`--ablation` 的默认值就是 `with-without`，两臂各跑一次；`--ablation none` 才是显式放弃基线（通常为省成本，2 臂即翻倍）。上面的工作区约定描述的是**手工跑迭代循环**时的组织方式。

🔴 **但基线与判据类型有耦合，这一点反直觉：** with-without 下「标记为 with-only 的 grader（**含 `tool_used: Skill`**）被当作 plugin-fired 指示器而不计入分数」。于是**判据全是 `tool_used: Skill` 的套件在 with-without 下会失去全部判据**——同一个开关，对语义判据（`llm`）是加了一层基线，对触发判据是抽走了判据本身。选 `--ablation` 前先看本套件的 grader 类型构成。

**三个执行时要知道的官方默认值：** `--runs` 默认 `case.runs ?? 3`（不是 1）；`--judge-model` 默认 haiku；`--threshold` 默认 **1.0**，即任何一个 case 分数低于 1.0 就整体 `exit 1`。⚠️ 1.0 对确定性判据（`tool_used` 这类布尔判定）是自然阈值，对 `llm` 评委的自然语言判据是否过严则须自己实测——评委有抖动，单次结果不足以判定回归。

## 3. Assertions（断言）

- **必须**：assertions 是**可验证**的陈述——"输出是合法 JSON"、"图表有标注坐标轴"、"报告含至少 3 条建议"
- **禁止**：用"输出是好的"这类太模糊的断言
- **禁止**：用过于脆弱的断言（"输出恰好包含短语 'Total Revenue: $X'"）——正确输出换措辞就失败
- **必须**：看过首轮输出后再加 assertions（首轮前常不知道"好"长什么样）
- **应该**：机械可判的断言（合法 JSON、行数、文件存在）用校验脚本，比 LLM 判断可靠且可复用；无法分解为 pass/fail 的质量（文风、视觉设计、整体感）留给人工 review

**官方格式下 assertion 的落位就是 grader 文件的 `type`**，六种，前四种不计费：

| type | 计费 | 判什么 | 对应本节哪一条 |
|---|---|---|---|
| `regex` | 免费 | 正则匹配最终输出 | 「机械可判的用校验脚本」 |
| `tool_order` | 免费 | 工具调用顺序 | 同上 |
| `tool_used` | 免费 | 某工具被调用次数落在 `min..max` 内 | 同上 |
| `file_exists` | 免费 | 文件产出 | 同上 |
| `llm` | **付费** | LLM 评委按自然语言判据打分 | 「留给人工 review 的质量」的自动化替身 |
| `baseline` | **付费** | 与基线对比 | § 2 的基线对比 |

⚠️ **免费 grader 不等于免费 eval**：免费只省掉评分那一层，被评的那次 agent run 照样要跑、照样计费。
⚠️ **官方 `--bare` 脚手架默认生成的是付费的 `llm`**，照抄模板等于选了付费档。
⚠️ `tool_used` 配 `tool: Skill` 是「这个 skill 到底有没有被触发」的直接传感器，而 **`max: 0` 表达「不得调用」**——因此「不该触发的语境」也能零成本判定。**只测正例查不出过度触发，而过度触发在日常使用中往往比不触发更烦人。**

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
