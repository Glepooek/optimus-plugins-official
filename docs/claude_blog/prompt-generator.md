# 在开发者控制台中生成更好的提示词

Anthropic Console 新增提示词生成器：只需描述任务，Claude 就会运用思维链等提示词工程技巧，自动生成生产级提示词模板。

> **来源：** [Claude Blog - Generate better prompts in the developer console](https://claude.com/blog/prompt-generator)
> **发布日期：** 2024 年 5 月 20 日
> **分类：** Product announcements | 产品：Claude Platform | 阅读时长：5 分钟

---

现在，用户可以在 Anthropic Console 中生成生产级的提示词模板——只需描述任务，Claude 就会运用思维链推理等提示词工程技巧来构建有效的提示词。这既有助于刚接触提示词工程的新手，也能为经验丰富的从业者提供帮助；任务描述越详细，生成结果越好。生成的提示词往往优于提示词工程新手手写的提示词，同时用户仍可自行编辑微调。

## 一、内置的提示词最佳实践

该功能内部沿用了以下几种技巧：

- **角色设定**：引导 Claude 采用专家人设。例如内容审核场景的示例提示词写道："你将扮演内容审核员，根据给定的内容审核政策，将聊天记录分类为通过或拒绝。"
- **思维链推理**：在给出回答前留出思考空间。例如产品推荐场景的示例，要求 Claude 先在草稿区里带着理由头脑风暴出三条推荐。
- **用 XML 标签包裹变量**：较长或含义模糊的变量（如一段代码）用 `<code>` 等标签包裹；较短的变量（如语言名称）则直接内联出现。示例为一个 Python 翻译提示词。
- **输入输出示例**：Claude 有时会写出示例答案以明确期望的格式，用户可对其编辑。

## 二、幕后原理

提示词生成器本身由一段较长的内部提示词驱动，采用了同样的技巧：其中包含大量"任务→模板"的示例对，引导 Claude 在正式撰写模板前先规划其结构，并用 XML 标签作为结构上的"脊梁"。完整的内部提示词可在[这份 Colab notebook](https://colab.research.google.com/drive/1SoAajN8CBYTl79VyTwxtxncfCWlHlyy9#scrollTo=NTOiFKNxqoq2) 中查看。

## 三、提示词模板也是一种评估工具

生成的变量采用 [Handlebars](https://handlebarsjs.com/) 语法。文章建议上传多样化的输入（例如一份内容政策加多段聊天记录）来测试 Claude 在不同场景下的表现，从而支持应用可靠性测试。

## 四、客户案例：ZoomInfo

作为一家营销获客平台，ZoomInfo 使用提示词生成器加速构建了一个 RAG 应用的 MVP。该公司首席数据科学家 Spencer Fox 表示，这一功能"揭示了一些我此前没有用到、能提升效果的技巧"，并显著缩短了提示词调优的时间。

## 五、开始使用

前往 [Anthropic Console](https://console.anthropic.com/) 即可开始构建提示词。

---

## 致谢

本文由 Anthropic 团队撰写。
