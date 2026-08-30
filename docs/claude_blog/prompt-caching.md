# Prompt Caching：让 Claude 的提示词缓存更快更便宜

Prompt Caching（提示词缓存）允许开发者在多次 API 调用之间缓存频繁使用的上下文，大幅降低长提示词场景下的成本与延迟。

> **来源：** [Claude Blog - Prompt caching with Claude](https://claude.com/blog/prompt-caching)
> **发布日期：** 2025 年 8 月 14 日
> **分类：** Product announcements | 产品：Claude Platform | 阅读时长：5 分钟

---

Prompt Caching 现已在 Anthropic API 上正式发布（此前曾在 Amazon Bedrock 与 Google Cloud Vertex AI 上提供预览），并在 Claude 3.5 Sonnet、Claude 3 Opus、Claude 3 Haiku 上开放公开测试。这项能力让开发者可以缓存对话之间反复使用的上下文，官方数据显示：对于长提示词场景，缓存最多可将**成本降低 90%**、将**延迟降低 85%**。

## 一、适合使用 Prompt Caching 的场景

- **对话式智能体**：降低长对话的成本与延迟
- **编程助手**：把代码库摘要长期保留在提示词中
- **长文档处理**：在提示词中纳入长篇资料与图片
- **详细指令集**：共享大量示例与操作流程
- **智能体式搜索与工具调用**：改善多步骤工具调用工作流的表现
- **与书籍/论文/文档/播客转录稿对话**：把完整文档嵌入提示词用于问答

## 二、性能对比

官方给出的延迟与成本对比数据：

| 使用场景 | 无缓存延迟 | 有缓存延迟 | 成本降低 |
|---|---|---|---|
| 与一本书对话（缓存 10 万 token 提示词） | 11.5s | 2.4s（-79%） | -90% |
| 多样本提示（1 万 token 提示词） | 1.6s | 1.1s（-31%） | -86% |
| 多轮对话（10 轮对话，长系统提示词） | ~10s | ~2.5s（-75%） | -53% |

## 三、缓存提示词的计价方式

缓存提示词的价格取决于你缓存的输入 token 数量，以及使用该内容的频率：

- **写入缓存**：比基础输入价格贵 25%
- **读取缓存**：仅为基础输入 token 价格的 10%

各模型的具体价格（200K 上下文窗口）：

| 模型 | 输入 | 缓存写入 | 缓存读取 | 输出 |
|---|---|---|---|---|
| Claude 3.5 Sonnet | $3/MTok | $3.75/MTok | $0.30/MTok | $15/MTok |
| Claude 3 Opus | $15/MTok | $18.75/MTok | $1.50/MTok | $75/MTok |
| Claude 3 Haiku | $0.25/MTok | $0.30/MTok | $0.03/MTok | $1.25/MTok |

## 四、客户案例：Notion

Notion 将 Prompt Caching 集成进 Notion AI，目标是降低成本并提升响应速度。Notion 联合创始人 Simon Last 表示，团队很期待用 Prompt Caching 让 Notion AI 变得更快、更便宜。

## 五、开始使用

前往 [Anthropic 文档](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)与[定价页面](https://www.anthropic.com/pricing#anthropic-api)了解如何在公开测试阶段使用这一功能。

---

## 致谢

本文由 Anthropic 团队撰写。
