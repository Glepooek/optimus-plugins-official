# dynamic-programming-problem-solving

> 版本：1.1.0 | 分类：decision

用户面对可分解为子问题的优化/计数问题，纠结"能不能用DP解、状态该怎么定义"时，给出基于《Hello 算法》的三大特性判据与三步解题法。

## 所处层级

```
┌───────────────────────────────────────────────────┐
│               optimus-decision-plugin                │
│                                                       │
│   ┌───────────────────────────────────┐             │
│   │  complexity-analysis (地基)        │             │
│   └──────────────┬──────────────────────┘             │
│                  │ depends-on                        │
│                  ▼                                   │
│   ┌───────────────────────────────────────┐         │
│   │ ★ dynamic-programming-problem-solving  │         │
│   └──────┬───────────────────┬──────────────┘         │
│          │ contrasts-with    │ contrasts-with         │
│          ▼                   ▼                       │
│   ┌──────────────┐   ┌────────────────────┐          │
│   │ divide-and-   │   │ greedy-algorithm-   │          │
│   │ conquer-      │   │ applicability /     │          │
│   │ problem-check │   │ backtracking-       │          │
│   │               │   │ algorithm-template  │          │
│   └──────────────┘   └────────────────────┘          │
└───────────────────────────────────────────────────┘
```

## 触发词 / 内部触发条件

这个问题能用动态规划解吗、怎么定义dp状态、我的DP转移方程结果不对、dynamic programming for this problem、how to define dp state、空间优化该正序还是倒序遍历

## 业务逻辑流程图

```
┌─────────────────────────────┐
│ Step 1: 加分项/减分项快速初筛 │
└────────────┬──────────────────┘
             ▼
┌─────────────────────────────┐
│ Step 2: 核对三大特性          │
│ 重叠子问题/最优子结构/无后效性 │
└────────────┬──────────────────┘
             ▼
┌─────────────────────────────┐
│ Step 3: 按三步法定义状态转移   │
│ 定义状态→转移方程→边界与顺序   │
└────────────┬──────────────────┘
             ▼
┌─────────────────────────────┐
│ Step 4: 判断空间优化遍历方向   │
│ 依赖方向决定正序/倒序/暂存变量 │
└────────────┬──────────────────┘
             ▼
┌─────────────────────────────┐
│ Step 5: 输出结构化建议        │
└──────────────────────────────┘
```

## 产出物数据流

用户的问题描述（最优化目标/状态特征/约束条件） → dynamic-programming-problem-solving → 结构化设计建议
（适用性结论 + 状态定义与转移方程 + 遍历方向依据） → 人工接手，写入实际代码

## Skill 依赖关系图

```
complexity-analysis ──depends-on──▶ dynamic-programming-problem-solving
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼ contrasts-with                             ▼ contrasts-with
          divide-and-conquer-problem-check          greedy-algorithm-applicability
                                                      backtracking-algorithm-template
```
