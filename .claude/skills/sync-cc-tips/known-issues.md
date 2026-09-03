# sync-cc-tips · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-03 | 第五步同步点清单声称「只有 2 处含条目总数」，实际有 4 处；漏掉的 `.kiro/steering/plugins.md` 数字长期停在 425，`.codex-plugin/plugin.json` 版本落后真源两个 Patch | `/sync-cc-tips`（v2.1.250→v2.1.259 同步） | 已修复 | 1.2.2 |
