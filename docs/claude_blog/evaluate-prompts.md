# 在开发者控制台中评估提示词

Anthropic Console 新增自动化测试与评估工具，帮助开发者更轻松地生成、测试并对比提示词效果。

> **来源：** [Claude Blog - Evaluate prompts in the developer console](https://claude.com/blog/evaluate-prompts)
> **发布日期：** 2024 年 7 月 9 日
> **分类：** Product announcements | 产品：Claude Platform | 阅读时长：5 分钟

---

提示词的质量对结果影响很大。为此，Anthropic 在 Console 中新增了一系列工具，帮助开发者更轻松地生成、测试和评估提示词，包括自动生成测试用例与对比输出结果。

## 一、生成提示词

内置的提示词生成器由 Claude 3.5 Sonnet 驱动，用户描述一个任务（示例为"分类处理客户支持的来件请求"），即可获得一份草拟的提示词。之后用户可以自动生成测试输入变量，或手动输入，以预览 Claude 的响应结果。

## 二、生成测试套件

新的"Evaluate"功能让用户可以直接在 Console 中构建测试套件，而不必手动在电子表格或代码中维护测试用例。测试用例可以手动添加、通过 CSV 导入，或自动生成，并可调整 Claude 解读变量要求的方式。

## 三、评估模型响应并迭代

用户可以创建新的提示词版本，重新运行测试套件，并将多个提示词的输出并排对比。此外，领域专家可以用 5 分制对响应质量打分，以此追踪提示词的修改是否真正带来了改进。

## 四、开始使用

这些功能已向所有 Anthropic Console 用户开放，更多细节可参阅[提示词工程文档](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)。

---

## 致谢

本文由 Anthropic 团队撰写。
