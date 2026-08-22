# 02 · 描述优化

> 更新历史：2026-08-22 创建。
>
> 来源：[优化 skill 描述](https://agentskills.io/skill-creation/optimizing-descriptions)。`description` 承载 skill 的**全部触发负担**——description 写不好，skill 功能再强也不会被 agent 调用。

## 1. 触发机制

- **认知**：agent 启动时只加载所有 skill 的 `name` + `description`，靠它判断任务何时需要这个 skill；description 不传达"何时有用"，agent 就不会想起它
- **认知**：agent 通常只在任务需要**专门知识**（陌生 API、领域工作流、不常见格式）时才会考虑 skill；一步简单的请求（如"读这个 PDF"）即使 description 完全匹配也可能不触发
- **必须**：description 精准描述"何时用"，否则 skill 不会被触发

## 2. 写作原则

- **必须**：用**祈使语气**——"Use this skill when..."，而非"This skill does..."；agent 在决定是否行动，要告诉它何时行动
- **必须**：聚焦**用户意图**而非实现机制——描述用户想达成什么，agent 拿用户请求来匹配
- **必须**：宁可**pushy**——显式列出适用场景，包括用户未直接点名领域的情况（"即使未明确提 CSV 或 analysis"）
- **应该**：保持**简洁**——几句话到一小段，足以覆盖 scope 即可；硬上限 1024 字符
- **禁止**：描述实现细节（"调用 X API 做 Y"）而非用户目标

```yaml
# ❌ 空泛：无法触发
description: Process CSV files.

# ✅ 具体做什么 + 广泛何时用
description: >
  Analyze CSV and tabular data files — compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use this
  skill when the user has a CSV, TSV, or Excel file and wants to
  explore, transform, or visualize the data, even if they don't
  explicitly mention "CSV" or "analysis."
```

## 3. Trigger eval 查询设计

为验证 description 能否正确触发，需要一组 **eval 查询**——标注了应不应触发的真实用户 prompt。

- **应该**：约 20 条查询——8-10 条应触发 + 8-10 条不应触发
- **必须**：应触发的查询沿多维度变化：措辞（正式/随意/带错别字）、显式度（直接点名领域 vs 只描述需求）、细节量（一句话 vs 含文件路径和背景）、复杂度（单步 vs 多步工作流）
- **必须**：最值得测的应触发查询是"skill 有帮助但连接不明显"的——此时 description 措辞决定成败
- **必须**：不应触发的查询重点用 **near-miss**（共享关键词但实际需要别的能力）——测 description 是否精确而非宽泛
- **应该**：查询贴近真实：含文件路径、个人背景、列名、公司名、随意缩写

示例（CSV 分析 skill）：

```json
[
  { "query": "I've got a spreadsheet in ~/data/q4_results.xlsx with revenue in col C — can you add a profit margin column?", "should_trigger": true },
  { "query": "whats the quickest way to convert this json file to yaml", "should_trigger": false },
  { "query": "can you write a python script that reads a csv and uploads each row to our postgres database", "should_trigger": false }
]
```

## 4. 触发率测试

- **必须**：每条查询多次运行（3 次是合理起点），计算**触发率** = 触发次数 / 运行次数
- **必须**：应触发查询的触发率高于阈值（0.5 为合理默认）才算通过；不应触发的低于阈值才算通过
- **应该**：用 agent 的可观测性（执行日志 / 工具调用历史）判断 skill 是否被加载
- **应该**：脚本化整个测试（20 查询 × 3 次 = 60 次调用），可复用
- **应该**：若客户端支持，一旦结果明确即可提前终止运行，节省成本

## 5. Train/Validation 切分防过拟合

- **必须**：把查询集切分为 train（约 60%）与 validation（约 40%）
- **必须**：两个集合都含比例的应触发/不应触发查询（不得把正例全放一个集合）
- **必须**：随机洗牌并保持切分固定，跨迭代可比
- **必须**：**只用 train 集失败引导修改**；validation 集结果不得参与优化过程，只用于验证改进是否泛化

## 6. 优化循环

1. 用当前 description 在 train + validation 集评估；train 结果引导修改，validation 结果验证泛化
2. 识别 train 集失败：应触发没触发 → description 太窄，扩大 scope；不应触发却触发 → 太宽，加"不做什么"的边界
3. 修订 description 时聚焦泛化，**禁止**从失败查询里抄具体关键词（那是过拟合）；找失败背后的通用类别去解决
4. 卡住时尝试结构性不同的写法，而非渐进微调
5. 反复至 train 集全过或不再有实质改进；用 validation 通过率选最优迭代（最优可能不是最后一版）
6. 每次修订后检查 ≤1024 字符限制

- **认知**：5 轮迭代通常足够；不再改进时问题可能在查询集本身（太易/太难/标签错），而非 description
- **应该**：可用 [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) skill 自动化此循环

## 权威参考

- [优化 skill 描述 — 完整版](https://agentskills.io/skill-creation/optimizing-descriptions)
