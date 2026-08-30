# 2026 年提示词工程最佳实践

面向 2026 年 Claude 模型的提示词工程指南：核心技巧、高级技巧、常见误区，以及如何在提示词工程与上下文工程之间做选择。

> **来源：** [Claude Blog - Best practices for prompt engineering for 2026](https://claude.com/blog/best-practices-for-prompt-engineering)
> **发布日期：** 2025 年 11 月 10 日
> **分类：** Agents | 产品：Claude apps | 阅读时长：5 分钟

---

## 一、什么是提示词工程？

提示词工程是指通过组织指令的结构，让 AI 模型产出更好结果的实践，文章将其称为"上下文工程的基础构件"。对于更新的 Claude 模型而言，提示词工程正日益向上下文工程靠拢——趋势是"更少的脚手架，更多的信息筛选（curation）"。

## 二、核心技巧

- **明确清晰**：直接说出你想要什么，不要指望模型去推断
- **提供背景与动机**：解释某个要求背后的"为什么"（例如格式偏好的原因）
- **保持具体**：包含约束条件、目标受众、结构要求与具体规范
- **使用示例**：即 one-shot / few-shot 提示；文章特别指出"Claude 4.x 及同类先进模型会非常仔细地关注示例中的细节"
- **允许模型表达不确定性**：降低模型产生幻觉的风险

## 三、高级技巧

- **预填充模型回复**：例如以 `{` 开头强制输出 JSON 格式
- **思维链提示**（基础版、引导版、结构化版三种变体）：文中提到，在可用的情况下，"扩展思考（extended thinking）通常优于手动构造思维链提示"
- **控制输出格式**：明确告诉模型"应该做什么"，让提示词风格与期望输出匹配，制定明确的格式规则
- **提示词链（Prompt chaining）**：将复杂任务拆解为一系列顺序执行的提示词

## 四、较旧或不太必要的技巧

- **用 XML 标签组织结构**：偶尔仍有用，但重要性下降
- **角色提示（Role prompting）**：需警惕过度限定角色人设带来的副作用

## 五、综合运用示例

文章给出了一个综合示例：在一个 JSON 提取任务的提示词中，同时组合了明确指令、背景说明、示例结构、允许表达不确定性、以及输出格式控制。

## 六、如何选择技巧

文章提供了一套决策框架，以及一张"技巧选择指南"表格，把不同需求（格式控制、推理能力、复杂度、防止幻觉）与对应技巧匹配起来。

## 七、排查问题与常见错误

列出了典型问题（输出笼统、答非所问、格式不一致）及对应修复方法，也列出了常见误区，如过度工程化提示词、依赖过时的技巧。

## 八、其他考量

文章讨论了 token/上下文开销的问题，指出 Claude 4.x 系列在"上下文感知能力"上的提升，并说明即便上下文窗口越来越大，任务拆分仍然有其价值。

## 九、结语建议

从核心技巧入手，仅在必要时叠加高级技巧；把跨会话通用的指令迁移到 CLAUDE.md 文件、Skill 或其他"引导（steering）方法"中管理，而不是每次都塞进单次提示词。

## 相关链接

- [提示词工程文档](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [上下文工程指南](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude 5 系列模型的上下文工程新规则](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models)
- [扩展思考（extended thinking）](https://www.anthropic.com/news/visible-extended-thinking)
- [用 CLAUDE.md 文件、Skill 与其他引导方法管理跨会话指令](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [提示词工程文档总览](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview)
- [交互式提示词工程教程](https://github.com/anthropics/prompt-eng-interactive-tutorial)
- [提示词工程课程](https://anthropic.skilljar.com/claude-with-the-anthropic-api)

---

## 致谢

本文由 Anthropic 团队撰写。
