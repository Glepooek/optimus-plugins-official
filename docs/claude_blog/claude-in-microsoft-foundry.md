# Claude 在 Microsoft Foundry 中正式全面发布

> 原文：https://claude.com/blog/claude-in-microsoft-foundry<br/>
> 分类：Product announcements | 产品：Claude Platform | 日期：2026年6月29日 | 阅读时长：5分钟

---

从今天起，Claude 模型已在托管于 Azure 的 Microsoft Foundry 中正式全面发布。Claude 运行在你的 Azure 环境中，使用你的团队已经在使用的身份认证、计费和治理控制。你可以选择推理处理的位置，包括面向有数据驻留要求的团队提供的美国数据区域。Anthropic 负责运营推理服务，并作为数据处理方。

> **NVIDIA**
>
> "在 NVIDIA，我们每天都在使用自主 AI 智能体，帮助团队更快行动、思考更宏大的问题。Claude 模型带来了强大的推理、编码和企业级能力，这些能力对复杂技术工作非常有价值。如今 Claude 已在运行于 NVIDIA GB300 GPU 的 Microsoft Foundry 中可用，更多组织能够以生产环境所需的性能、规模和安全性，运行先进的专业化 AI 智能体。"
>
> —— Justin Boitano，企业计算业务副总裁兼总经理

> **Bolt**
>
> "在 Azure 上运行 Claude 模型，为我们带来了企业客户所期望的持续吞吐量和可靠性。前沿模型质量与企业级基础设施的结合，正是让 Bolt 能够服务财富 500 强企业的关键所在。"
>
> —— Gary Ballabio，合作伙伴业务副总裁

> **Everstar**
>
> "借助 Anthropic 与 Azure 的组合，我们获得了业界最强的能力，也获得了业界最高的安全性。而这正是核能行业所需要的。正因如此，我们把原本需要 200 个人日才能完成的安全分析，压缩到了一天之内。"
>
> —— Matt Huang，创始产品负责人

> **Momentic**
>
> "我们的客户用简单的英语描述测试用例，Momentic 会在界面中实际运行这些用例，在发布前验证一切正常运作。我们发现 Claude Opus 特别适合这项任务，在 Azure Foundry 上运行后，我们如今能够以客户所依赖的可靠性，每分钟处理数百万 token。"
>
> —— Jeff An，联合创始人兼首席技术官

### 通过 Azure 账户构建 Claude 应用

目前，Claude Opus 4.8 和 Claude Haiku 4.5 已在 Messages API 中可用，并支持提示缓存（prompt caching）和扩展思维（extended thinking）等核心能力，适用于从编码、智能体任务到复杂推理等多种场景。我们将持续扩展 Foundry 中可用的功能。

Claude in Microsoft Foundry 原生集成于 Azure，兼容你现有的 Azure 身份认证、网络和治理控制。你将收到统一的合并账单；对于符合条件、持有 Microsoft 企业协议（Enterprise Agreement）的客户，Claude 的使用量可用于抵扣 Microsoft Azure 承诺消费额度。

### 在 Azure 中运行 Claude，由 Anthropic 运营

在 Microsoft Foundry 中运行 Claude 有两种方式。当你需要在自己的 Azure 环境中运行，并使用 Azure 身份认证、计费、治理以及美国数据区域时，选择 *hosted on Azure*（托管于 Azure）。当你需要完整的 API 功能集，或需要使用尚未在 Azure 上线的模型时，选择 *hosted on Anthropic*（托管于 Anthropic，原 Foundry Preview）。长期来看，我们的目标是让"托管于 Azure"与"托管于 Anthropic"两种方案在功能和模型上实现对等。

### 开始使用

Claude in Microsoft Foundry 现已正式全面发布。要开始使用，请打开 [Claude in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude?tabs=python)，或查阅[相关文档](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)。
