# Trigger Eval 工作流详解

> 讲解性内容，无规范语气。支撑 `02-description-optimization.md`（触发率测试）。描述"如何搭建并跑触发率测试"的完整可操作流程。

## 为什么需要触发率测试

`description` 是 skill 能否被 agent 想起的唯一机制。写完后不能只靠"感觉应该能触发"——要定量测：给一组标注了应/不应触发的用户 prompt，跑多次，统计实际触发率。低于阈值的查询暴露 description 的盲区。

## 完整工作流

```
1. 设计查询集（约 20 条：应触发 8-10 + 不应触发 8-10）
2. 切分 train / validation（60% / 40%，固定随机种子）
3. 对每条查询跑 N 次（N=3 起步），记录触发次数
4. 算触发率 = 触发次数 / 运行次数
5. 应触发 > 0.5 通过；不应触发 < 0.5 通过
6. train 失败引导改 description → 重测 → 用 validation 验证泛化
```

## 查询集设计要点

**应触发查询**沿四个维度变化，避免全是"点名领域"的简单正例：

| 维度 | 变化方式 |
|---|---|
| 措辞 | 正式 / 随意 / 带错别字 / 缩写 |
| 显式度 | 直接点名（"analyze this CSV"）/ 只描述需求（"my boss wants a chart from this data"）|
| 细节量 | 一句话 / 含文件路径、列名、背景的长消息 |
| 复杂度 | 单步 / 多步工作流（skill 的任务埋在长链条里）|

**最有用**的应触发查询是"skill 有帮助但连接不明显"的——这正是 description 措辞决定成败的分水岭。**不应触发**查询重点用 near-miss（共享关键词但需要别的能力），测的是精确性而非宽泛性。

## 触发率测试脚本

用 Bash + `jq` 脚本化。以 Claude Code 为例（用 `--output-format json` 检测 Skill 工具调用），其他 agent 客户端换掉 `check_triggered` 即可：

```bash
#!/bin/bash
QUERIES_FILE="${1:?Usage: $0 <queries.json>}"
SKILL_NAME="my-skill"
RUNS=3

# 应返回 0（skill 被调用）或 1
check_triggered() {
  local query="$1"
  claude -p "$query" --output-format json 2>/dev/null \
    | jq -e --arg skill "$SKILL_NAME" \
      'any(.messages[].content[]; .type == "tool_use" and .name == "Skill" and .input.skill == $skill)' \
      > /dev/null 2>&1
}

count=$(jq length "$QUERIES_FILE")
for i in $(seq 0 $((count - 1))); do
  query=$(jq -r ".[$i].query" "$QUERIES_FILE")
  should_trigger=$(jq -r ".[$i].should_trigger" "$QUERIES_FILE")
  triggers=0

  for run in $(seq 1 $RUNS); do
    check_triggered "$query" && triggers=$((triggers + 1))
  done

  jq -n \
    --arg query "$query" \
    --argjson should_trigger "$should_trigger" \
    --argjson triggers "$triggers" \
    --argjson runs "$RUNS" \
    '{query: $query, should_trigger: $should_trigger, triggers: $triggers, runs: $runs, trigger_rate: ($triggers / $runs)}'
done | jq -s '.'
```

**省时技巧**：结果一旦明确（skill 被调用了或已开始不带它干活）即可提前终止本轮，不必等完整输出——能显著降低全量 eval 的时间和成本。

## Train/Validation 切分

防过拟合：用 train 集失败引导修改，validation 集只用于验证泛化。

- 60% / 40% 切分，两个集合都含成比例的正/负例（别把正例全放一个集合）
- 随机洗牌后固定切分，跨迭代可比
- 只用 train 失败引导修改；validation 结果不进优化过程
- 用脚本把查询拆成 `train_queries.json` / `validation_queries.json` 分别跑

## 常见失败模式与修订方向

| train 失败表现 | 诊断 | 修订方向 |
|---|---|---|
| 应触发的没触发 | description 太窄 | 扩大 scope，加"何时有用"的上下文 |
| 不应触发的却触发 | description 太宽 | 加"不做什么"的边界，澄清与相邻能力的界限 |
| 反复卡住 | 查询集本身有问题（太易/太难/标签错） | 修查询集，而非继续调 description |

**禁止**：从失败查询抄具体关键词到 description——那是过拟合；要找失败背后的通用类别去解决。卡住几轮后，尝试**结构性不同**的写法（换框架/换句子结构），比渐进微调更可能突破。

## 适用性

- 面向**对外发布**或**会被 agent 自动触发**的 skill，建议完整跑触发率测试
- 纯内部、用户手动点名调用的 skill，可只做少量手动 sanity check

## 权威参考

- [优化 skill 描述 — 完整版](https://agentskills.io/skill-creation/optimizing-descriptions)
