---
name: unipus:prd:review
description: 对已有 PRD 文档进行6维度质量诊断，输出评分报告和分优先级改进建议，不修改原文档。触发词：审查PRD、检查PRD、review PRD、诊断需求文档
---

使用 `unipus:prd:review` 对 PRD 文档进行全面质量诊断。

---

<HARD-GATE>
**开始任何评审工作前，必须先执行以下三步：**
1. Read `references/prd-template.md` — 获取标准7章结构作为对比基准
2. Read `references/prd-checklist.md` — 获取6维度评估标准和权重
3. Read `references/review-report-template.md` — 获取诊断报告输出格式

未读取以上文件不得开始评审。
</HARD-GATE>

---

## Workflow

**Step 1 — 宣告并读取参考文件**
告知用户："正在使用 unipus:prd:review"，然后读取3个 references/ 文件。

**Step 2 — 获取待审 PRD**
- 用户已提供文件路径 → 用 Read 工具读取文件内容
- 用户直接粘贴内容 → 直接使用粘贴内容
- 未提供任何输入 → 问用户：
  > "请提供 PRD 文档路径或直接粘贴文档内容。"

**Step 3 — 结构对比检查**
对照 `references/prd-template.md` 的7章结构，逐章检查：
- 该章是否存在
- 子节是否完整
- 章节内容是否实质性填写（非空占位符）

输出结构检查表：

```
结构检查
├── 第1章 文档信息：✅ / ⚠️ / ❌
├── 第2章 需求概述：✅ / ⚠️ / ❌
│   ├── 2.1 背景：✅ / ⚠️ / ❌
│   ├── 2.2 目标：...
│   └── ...
└── 第7章 其他：✅ / ⚠️ / ❌
```

**Step 4 — 6维度评分**
对照 `references/prd-checklist.md`，逐维度逐项打分（✅=100分 / ⚠️=60分 / ❌=0分），计算各维度得分。

**Step 5 — 按 review-report-template.md 格式输出诊断报告**
完整填写 `references/review-report-template.md` 模板中的所有字段，包括：
- 综合评分表（含加权分）
- 总体评价（1段话）
- 风险评估
- 各维度详细诊断
- 分P0/P1/P2/P3改进建议

**Step 6 — 末尾引导**
报告末尾固定输出：
> 综合得分：XX/100。如需优化，请使用 `unipus:prd:optimize` 自动修复问题。

---

## Red Flags

| 错误做法 | 正确做法 |
|---------|---------|
| 直接修改原 PRD 文档 | review 只输出诊断报告，不修改原文 |
| 只说"整体较好"等笼统评价 | 每个维度必须列出具体问题和改进建议 |
| 跳过某个维度的评分 | 6个维度全部必须评分，即使无问题也要说明 |
| 改进建议不区分优先级 | 必须按 P0/P1/P2/P3 分级输出建议 |
| 未使用 review-report-template.md 格式 | 输出格式必须严格遵循模板结构 |
| 评分缺乏依据 | 每个扣分项必须引用 prd-checklist.md 中的具体检查点 |
