# complexity-analysis

> 版本：1.1.0 | 分类：decision

用户在评估或对比方案效率时纠结"该按哪种复杂度视角判断"时，给出基于《Hello 算法》的最佳/最差/平均三视角选择框架。

## 所处层级

```
┌─────────────────────────────────────────────────┐
│              optimus-decision-plugin              │
│                                                     │
│   ┌───────────────────────────────────────┐       │
│   │ ★ complexity-analysis (全书方法论地基)  │       │
│   └──────────────────┬──────────────────────┘       │
│                       │ depends-on (被依赖)         │
│         ┌─────────────┼─────────────┬───────────┐  │
│         ▼             ▼             ▼           ▼  │
│  data-structure- sorting- search- (其余4个算法策略  │
│  selection        selection selection  选型 skill)  │
└─────────────────────────────────────────────────┘
```

## 触发词 / 内部触发条件

这个方案的时间复杂度该怎么评估、该用最差情况还是平均情况来判断、为什么空间复杂度只看最差情况、这两个方案哪个更适合有延迟要求的场景、how should I evaluate the time complexity、worst case vs average case

## 业务逻辑流程图

```
┌───────────────────────────┐
│ Step 1: 判断决策场景性质    │
│ 延迟/内存硬上限？吞吐/均摊？ │
└────────────┬───────────────┘
             ▼
┌───────────────────────────┐
│ Step 2: 选定复杂度评估视角  │
│ 时间：最差/平均/最佳        │
│ 空间：恒定用最差            │
└────────────┬───────────────┘
             ▼
┌───────────────────────────┐
│ Step 3: 交叉核对大O局限性   │
│ 常数项/缓存命中率等         │
└────────────┬───────────────┘
             ▼
┌───────────────────────────┐
│ Step 4: 输出结构化建议      │
│ 视角+依据+条件性说明        │
└────────────────────────────┘
```

## 产出物数据流

用户的方案对比诉求（延迟要求/内存约束/吞吐目标） → complexity-analysis → 结构化评估建议
（推荐视角 + 选择依据 + 条件性说明） → 人工接手，或作为下游选型 skill 的方法论输入

## Skill 依赖关系图

```
complexity-analysis ──depends-on──▶ data-structure-selection
        │                           search-algorithm-selection
        │                           sorting-algorithm-selection
        └─────depends-on──▶ dynamic-programming-problem-solving
                            greedy-algorithm-applicability
                            divide-and-conquer-problem-check
                            backtracking-algorithm-template
```
