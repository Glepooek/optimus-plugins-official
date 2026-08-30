# 在开发者控制台中优化你的提示词

Anthropic Console 新增提示词优化器（Prompt Improver），能自动为已有提示词应用高级提示词工程技巧，并提供更结构化的多样本示例管理界面。

> **来源：** [Claude Blog - Improve your prompts in the developer console](https://claude.com/blog/prompt-improver)
> **发布日期：** 2024 年 10 月 14 日
> **分类：** Product announcements | 产品：Claude Platform | 阅读时长：5 分钟

---

Anthropic 在 [Anthropic Console](https://console.anthropic.com/) 中推出新能力，让开发者能自动优化提示词、更有效地管理示例，从而更好地落地提示词工程最佳实践。

## 一、Prompt Improver（提示词优化器）

提示词质量对模型输出质量有显著影响，但最佳实践的落地往往耗时，且在不同模型厂商之间存在差异。新的提示词优化器工具可以让 Claude 自动为已有提示词应用高级技巧——无论是迁移自其他 AI 系统的提示词，还是手写提示词的进一步打磨，都能受益。

优化器通过五种方法工作：

1. 添加思维链推理段落
2. 将示例统一格式化为 XML
3. 用推理过程丰富示例内容
4. 为清晰度与语法进行改写
5. 添加预填充文本以引导输出格式

优化完成后，开发者还可以给出反馈进一步迭代。根据内部基于 Claude 3 Haiku 的测试（以 Wikipedia 数据为基础），某个多标签分类任务的准确率提升了 30%，某个摘要任务的字数遵循度达到 100%。

## 二、管理多样本示例

Workbench 中新增的结构化界面让开发者可以直接添加或编辑输入/输出示例对，文章指出这能提升**准确性**、**一致性**与**性能**。若提示词缺少示例，Claude 还能自动生成合成示例。

## 三、提示词评估

[提示词评估器](https://www.anthropic.com/news/evaluate-prompts)在 Evaluations 标签页中新增了一个可选的"理想输出"列，支持按 5 分制进行一致的评分。开发者可以持续向优化器提供反馈，包括诸如"把输出格式从 JSON 切换为 XML"这类具体要求。

## 四、客户案例：Kapa.ai

[Kapa.ai](https://www.kapa.ai/) 致力于把技术知识库转化为 AI 助手，该公司使用这一工具将工作流迁移到了 Claude 上。联合创始人 Finn Bauer 表示，这帮助团队"更快地进入生产环境"。

## 五、可用性

以上功能已向所有 [Anthropic Console](https://console.anthropic.com/) 用户开放，更多细节参阅[提示词工程文档](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-improver)。

---

## 致谢

本文由 Anthropic 团队撰写。
