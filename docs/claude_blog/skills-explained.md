# Skills 详解：Skill 与提示词、Projects、MCP 和子智能体的对比

Skills 是创建自定义 AI 工作流和智能体的强大工具，但它在 Claude 技术栈中处于什么位置？本文将解释各工具的适用场景，以及它们如何协同工作。

> **来源：** [Claude Blog - Skills explained: How Skills compares to prompts, Projects, MCP, and subagents](https://claude.com/blog/skills-explained)
> **发布日期：** 2025 年 11 月 13 日
> **分类：** Agents | 产品：Claude apps、Claude Platform | 阅读时长：5 分钟

---

自从推出 Skills 以来，大家对 Claude 智能体生态系统中各组件如何协作产生了浓厚兴趣。无论你是在 Claude Code 中构建复杂工作流、通过 API 创建企业解决方案，还是在 Claude.ai 上最大化提升效率，了解应该使用哪个工具、以及何时使用，都能彻底改变你与 Claude 的协作方式。

本指南将逐一解析每个构建模块、说明各自的适用场景，并展示如何将它们组合成强大的智能体工作流。

---

## 一、智能体构建模块全览

### 什么是 Skill？

> 🎬 视频：[Agent Skills: Specialized capabilities you can customize](https://www.youtube.com/watch?v=IoqpBKrNaZI)

Skill 是包含指令、脚本和资源的文件夹，Claude 在任务相关时会动态发现并加载它们。可以把 Skill 理解为专业培训手册，让 Claude 在特定领域获得专业知识——从处理 Excel 表格到遵循组织的品牌规范。

**Skill 的工作方式：** 当 Claude 遇到任务时，会扫描可用的 Skill 以找到匹配项。Skill 采用渐进式披露机制：先加载元数据（约 100 个 token），提供足够的信息让 Claude 判断 Skill 是否相关；需要时再加载完整指令（不超过 5k token）；附带的文件或脚本仅在需要时加载。

**适用场景：** 当你需要 Claude 一致且高效地执行专业任务时，选择 Skill。特别适合：

- **组织工作流**：品牌规范、合规流程、文档模板
- **领域专业知识**：Excel 公式、PDF 处理、数据分析
- **个人偏好**：笔记系统、编码风格、研究方法

**示例：** 创建一个包含公司配色方案、字体规则和排版规范的品牌规范 Skill。当 Claude 创建演示文稿或文档时，会自动应用这些标准，无需每次重新说明。

了解更多关于 [Skills](https://support.claude.com/en/articles/12512176-what-are-skills) 的信息，并查看我们不断增长的 [Skills 库](https://github.com/anthropics/skills)。

---

### 什么是提示词（Prompts）？

> 🎬 视频：[https://www.youtube.com/watch?v=ysPbXH0LpIE](https://www.youtube.com/watch?v=ysPbXH0LpIE)

提示词是你在对话中以自然语言向 Claude 提供的指令。它们是临时性的、对话式的、即时响应的——你在当下提供上下文和方向。

**适用场景：** 以下情况使用提示词：

- **一次性请求**：「总结这篇文章」
- **对话式优化**：「把语气改得更专业一些」
- **即时上下文**：「分析这份数据并找出趋势」
- **临时指令**：「把这个格式化为项目列表」

**示例：**

```
请对这段代码进行全面的安全审查。我希望了解：

1. 常见漏洞，包括：
   - 注入类缺陷（SQL、命令注入、XSS 等）
   - 认证和授权问题
   - 敏感数据暴露
   - 安全配置错误
   - 访问控制失效
   - 加密失败
   - 输入验证问题
   - 错误处理和日志记录问题

2. 对于发现的每个问题，请提供：
   - 严重级别（Critical/High/Medium/Low）
   - 代码位置（行号或函数名）
   - 说明为何存在安全风险及可能的利用方式
   - 具体的修复建议（尽量附上代码示例）
   - 防止类似问题的最佳实践

3. 代码上下文：
   [描述代码的功能、语言/框架及运行环境，
    例如：「这是一个处理用户认证和支付数据的 Node.js REST API」]

4. 其他注意事项：
   - 是否存在 OWASP Top 10 漏洞？
   - 代码是否遵循了 [特定框架/语言] 的安全最佳实践？
   - 是否存在已知漏洞的依赖项？

请按严重程度和潜在影响对发现进行优先级排序。
```

> **小提示：** 提示词是与 Claude 交互的主要方式，但不会跨对话持久化。对于重复性工作流或专业知识，可以考虑将提示词保存为 Skill 或项目指令。

**何时改用 Skill：** 如果你发现自己在多次对话中重复输入同一段提示词，就应该创建一个 Skill 了。将「按 OWASP 标准审查代码安全漏洞」或「用执行摘要、关键发现和建议格式化分析报告」这类反复使用的指令转化为 Skill，可以避免每次重新解释流程，并确保执行一致性。

查看我们的[提示词库](https://claude.com/en/prompt-library/library)、[提示词工程最佳实践](http://claude.com/blog/prompt-engineering-best-practices)，或使用[智能提示词生成器](https://claude.ai/public/artifacts/3796db7e-4ef1-4cab-b70c-d045778f23ec)开始上手。

---

### 什么是 Projects？

> 🎬 视频：[Shareable Projects in Claude](https://www.youtube.com/watch?v=nbG2DO6Xsek)

Projects 是所有付费 Claude 计划均可使用的功能，提供独立的工作空间，拥有各自的聊天历史和知识库。每个项目包含一个 200K 上下文窗口，你可以在其中上传文档、提供上下文，并设置适用于该项目所有对话的自定义指令。

**Projects 的工作方式：** 上传到项目知识库的所有内容，在该项目的所有对话中均可访问。Claude 会自动利用这些上下文提供更准确、更相关的响应。当项目知识接近上下文限制时，Claude 会无缝启用 RAG 模式，将容量扩展至最多 10 倍。

**适用场景：** 以下情况选择 Projects：

- **持久化上下文**：应影响所有对话的背景知识
- **工作空间组织**：为不同项目维护独立的上下文
- **团队协作**：共享知识和对话历史（Team 和 Enterprise 计划）
- **自定义指令**：特定于项目的语气、视角或方法

**示例：** 创建一个「Q4 产品发布」项目，上传市场调研、竞品分析和产品规格文档。该项目中的每次对话都能访问这些知识，无需重复上传或重新解释背景。

**何时改用 Skill：** Projects 为特定工作提供持久的上下文背景——你公司的代码库、一项研究计划、一个持续进行的客户项目。Skill 则教会 Claude **如何做某件事**。项目可以包含产品发布的所有背景信息，而 Skill 则可以教 Claude 你团队的写作标准或代码审查流程。如果你发现自己在多个项目中复制相同的指令，那就是该创建 Skill 的信号。

了解更多关于 [Projects](https://support.claude.com/en/articles/9517075-what-are-projects) 的信息。

---

### 什么是子智能体（Subagents）？

子智能体是专门的 AI 助手，拥有独立的上下文窗口、自定义系统提示词和特定的工具权限。子智能体在 Claude Code 和 Claude Agent SDK 中可用，能独立处理离散任务并将结果返回给主智能体。

**子智能体的工作方式：** 每个子智能体都有自己的配置——你定义它做什么、如何解决问题，以及它可以访问哪些工具。Claude 根据子智能体的描述自动将任务委派给合适的子智能体，你也可以明确指定某个子智能体。

**适用场景：** 以下情况使用子智能体：

- **任务专业化**：代码审查、测试生成、安全审计
- **上下文管理**：将主对话保持聚焦，同时将专业工作卸载出去
- **并行处理**：多个子智能体可以同时处理不同方面的任务
- **工具限制**：将特定子智能体限制在安全操作范围内（例如只读访问）

**示例：** 创建一个只能访问 Read、Grep 和 Glob 工具、但不能使用 Write 或 Edit 工具的代码审查子智能体。修改代码时，Claude 自动将工作委派给该子智能体进行质量和安全审查，不会有意外修改代码的风险。

**何时改用 Skill：** 如果多个智能体或对话需要相同的专业知识——如安全审查流程或数据分析方法——应创建 Skill 而非将这些知识内嵌到各个子智能体中。Skill 是可移植、可复用的，而子智能体是为特定工作流专门构建的。用 Skill 传授任何智能体都能应用的专业知识，用子智能体执行需要特定工具权限和上下文隔离的独立任务。

了解更多关于[子智能体](https://code.claude.com/docs/en/sub-agents)的信息。

---

### 什么是 MCP？

![MCP 连接层示意图](../assets/skills-explained-cover.png)

*MCP 在 AI 应用程序与现有工具和数据源之间建立了通用连接层。*

MCP 在 AI 应用程序与你现有的工具和数据源之间建立了一个通用连接层。模型上下文协议（MCP）是连接 AI 助手与外部系统的开放标准——内容库、业务工具、数据库和开发环境都可以通过它接入。

**MCP 的工作方式：** MCP 提供了一种将 Claude 连接到工具和数据源的标准化方式。无需为每个数据源构建自定义集成，只需对接单一协议。MCP 服务器暴露数据和能力，MCP 客户端（如 Claude）连接到这些服务器。

**适用场景：** 以下情况选择 MCP，让 Claude 能够：

- **访问外部数据**：Google Drive、Slack、GitHub、数据库
- **使用业务工具**：CRM 系统、项目管理平台
- **连接开发环境**：本地文件、IDE、版本控制
- **与自定义系统集成**：你的专有工具和数据源

**示例：** 通过 MCP 将 Claude 连接到公司的 Google Drive。这样 Claude 就能搜索文档、读取文件并引用内部知识，无需手动上传——连接持久有效，自动保持最新。

**何时改用 Skill：** MCP 负责将 Claude 连接到数据，Skill 则负责教 Claude 如何处理这些数据。如果你需要解释如何使用某个工具或遵循某个流程——比如「查询我们的数据库时，始终先按日期范围过滤」或「用这些特定公式格式化 Excel 报表」——那是 Skill 的职责。如果你需要 Claude 首先能够访问数据库或 Excel 文件，那才是 MCP 的职责。两者配合使用：MCP 负责连接，Skill 负责流程知识。

了解更多关于 [MCP](https://claude.com/blog/model-context-protocol) 的信息，并查看[如何构建 MCP Server](https://modelcontextprotocol.io/docs/develop/build-server) 的文档。

---

## 二、协同工作的力量

各构建模块各司其职，组合使用时能创造出强大的智能体工作流。

### 对比：如何选择合适的工具

| 特性 | Skill | 提示词 | Projects | 子智能体 | MCP |
|------|-------|--------|----------|---------|-----|
| 提供什么 | 流程知识 | 即时指令 | 背景知识 | 任务委派 | 工具连接 |
| 持久性 | 跨对话 | 单次对话 | 项目内 | 跨会话 | 持续连接 |
| 包含内容 | 指令 + 代码 + 资产 | 自然语言 | 文档 + 上下文 | 完整智能体逻辑 | 工具定义 |
| 加载时机 | 动态按需加载 | 每轮对话 | 项目内始终加载 | 调用时 | 始终可用 |
| 可包含代码 | 是 | 否 | 否 | 是 | 是 |
| 最适合 | 专业知识 | 快速请求 | 集中化上下文 | 专业任务 | 数据访问 |

---

## 三、智能体工作流示例：研究智能体

下面通过一个综合示例，展示如何将多个构建模块组合使用。这个例子演示了如何为竞品分析组建并启动一个智能体。

### 第一步：创建 Project

新建「竞品情报」项目并上传：
- 行业报告和市场分析
- 竞品产品文档
- 来自 CRM 的客户反馈
- 以往研究摘要

添加项目指令：
> 从我们的产品战略视角分析竞争对手。聚焦于差异化机会和新兴市场趋势。用具体证据和可落地的建议呈现发现。

### 第二步：通过 MCP 连接数据源

启用以下 MCP Server：
- Google Drive（访问共享研究文档）
- GitHub（查看竞品开源仓库）
- 网络搜索（获取实时市场信息）

### 第三步：创建专业 Skill

创建「competitive-analysis」Skill：

```markdown
# 公司云盘导航 Skill

## 概览
针对 Meridian Tech Google Drive 结构的优化搜索和检索策略。
使用此 Skill 高效定位内部文档、研究资料和战略材料。

## 云盘组织结构

**顶层结构：**
- `/Strategy & Planning/` - OKR、季度计划、董事会材料
- `/Product/` - PRD、路线图、技术规格
- `/Research/` - 市场调研、竞品情报、用户研究
- `/Sales & Marketing/` - 案例研究、演示材料、活动素材
- `/Customer Success/` - 实施指南、成功指标
- `/Company Ops/` - 政策、组织架构、团队目录

**命名规范：**
- 格式：`YYYY-MM-DD_文档名_vX`
- 最终版标注 `_FINAL`
- 草稿包含 `_DRAFT` 或 `_WIP`

## 搜索最佳实践

1. **从宽到窄** - 先用文件夹上下文 + 关键词
2. **定向文档责任人** - 销售材料找 Sales/，不找根目录
3. **关注时效性** - 优先查看近 6 个月的文档
4. **寻找「权威来源」** - 带 `_FINAL`、`_APPROVED` 或位于 `/Archives/Official/` 的文件

## 研究智能体工作流

1. 确定主题类别（产品、市场、客户）
2. 用精准关键词搜索相关文件夹
3. 检索 3-5 篇最新/最相关的文档
4. 与 `/Strategy & Planning/` 交叉参考获取背景
5. 引用来源时注明文件名和日期
```

### 第四步：配置子智能体（仅限 Claude Code/SDK）

创建专业化子智能体：

**market-researcher 子智能体：**

```yaml
name: market-researcher
description: 研究市场趋势、行业报告和竞争格局数据。主动用于竞品分析。
tools: Read, Grep, Web-search
---
你是专注于竞品情报的市场研究分析师。

研究时：
1. 识别权威来源（Gartner、Forrester、行业报告）
2. 收集量化数据（市占率、增长率、融资情况）
3. 分析定性洞察（分析师观点、客户评价）
4. 综合趋势和规律

用引用和置信度等级呈现发现。
```

**technical-analyst 子智能体：**

```yaml
name: technical-analyst
description: 分析技术架构、实现方案和工程决策。用于技术竞品分析。
tools: Read, Bash, Grep
---
你是分析竞品技术选型的技术架构师。

分析时：
1. 查看公开仓库和技术文档
2. 评估架构模式和技术栈
3. 评价可扩展性和性能方案
4. 识别技术优势和局限

聚焦于能指导我们产品决策的可落地技术洞察。
```

### 第五步：激活研究智能体

现在当你向 Claude 提问：

> 「分析我们的三大竞争对手如何定位其新 AI 功能，并找出我们可以利用的差距」

以下是执行过程：

1. **项目上下文加载**：Claude 访问已上传的研究文档，遵循项目指令
2. **MCP 连接激活**：Claude 在 Google Drive 中搜索最新竞品简报，拉取 GitHub 数据
3. **Skill 介入**：competitive-analysis Skill 提供分析框架
4. **子智能体执行**（Claude Code 中）：market-researcher 收集行业数据，technical-analyst 同时审查技术实现
5. **提示词精炼**：你提供对话式指导：「重点关注医疗行业的企业客户」

**结果**：一份综合竞品分析报告，来自多个数据源，遵循你的分析框架，发挥了专业知识优势，并在整个研究项目中保持了上下文连贯性。

---

## 四、常见问题

### Skill 是如何工作的？

Skill 通过渐进式披露让 Claude 保持高效。处理任务时，Claude 首先扫描 Skill 元数据（描述和摘要）以找到相关匹配；如果某个 Skill 匹配，Claude 加载完整指令；最后，如果 Skill 包含可执行代码或参考文件，这些内容仅在需要时才加载。

这一架构意味着你可以拥有大量可用 Skill，而不会压垮 Claude 的上下文窗口——Claude 在需要时才精确访问所需内容。

### Skill vs. 子智能体：如何选择？

**使用 Skill 当：** 你希望任何 Claude 实例都能加载和使用某项能力。Skill 就像培训材料——让 Claude 在所有对话中更擅长特定任务。

**使用子智能体当：** 你需要完整的、为特定目的构建的自包含智能体，能独立处理工作流。子智能体就像拥有独立上下文和工具权限的专业员工。

**组合使用当：** 你希望子智能体拥有专业知识。例如，代码审查子智能体可以使用语言特定最佳实践的 Skill，将子智能体的独立性与 Skill 的可移植专业知识结合起来。

### Skill vs. 提示词：如何选择？

**使用提示词当：** 你在给出一次性指令、提供即时上下文，或进行对话式来回交流。提示词是即时响应的、临时性的。

**使用 Skill 当：** 你有需要反复使用的流程或专业知识。Skill 是主动的——Claude 知道何时应用它们——并且跨对话持久存在。

**组合使用：** 提示词和 Skill 天然互补。用 Skill 提供基础专业知识，再用提示词为每项任务提供具体上下文和精炼指导。

### Skill vs. Projects：如何选择？

**使用 Projects 当：** 你需要应影响某项具体计划所有对话的背景知识。Projects 提供始终加载的静态参考资料。

**使用 Skill 当：** 你需要仅在相关时才激活的流程知识和可执行代码。Skill 提供按需加载的动态专业知识，节省上下文窗口。

**组合使用当：** 你既需要持久化上下文，又需要专业能力。例如，包含产品规格和用户研究的「产品开发」项目，结合用于创建技术文档和分析用户反馈数据的 Skill。

**关键区别：** Projects 说的是「这是你需要了解的」，Skill 说的是「这是如何做事的」。Projects 提供你在其中工作的知识库，Skill 提供在任何地方都能工作的能力——任何对话，任何项目。

### 子智能体可以使用 Skill 吗？

可以。在 Claude Code 和 Agent SDK 中，子智能体可以像主智能体一样访问和使用 Skill，这创造了强大的组合。

例如，你的 python-developer 子智能体可以使用 pandas-analysis Skill 按照团队规范执行数据转换，而你的 documentation-writer 子智能体则使用 technical-writing Skill 一致地格式化 API 文档。

---

## 五、开始使用

准备好开始使用 Skill 构建了吗？以下是入门方式：

**Claude.ai 用户：**
- 在「设置 → 功能」中启用 Skills
- 在 claude.ai/projects 创建你的第一个项目
- 尝试将项目知识与 Skill 结合用于下一项分析任务

**API 开发者：**
- 在[文档](https://docs.anthropic.com)中探索 Skills 端点
- 参阅我们的 [skills cookbook](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)

**Claude Code 用户：**
- 通过 [Plugin 市场](https://code.claude.com/docs/en/plugin-marketplaces)安装 Skills
- 参阅我们的 [skills cookbook](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)

---

## 致谢

本文由 Anthropic 团队撰写。
