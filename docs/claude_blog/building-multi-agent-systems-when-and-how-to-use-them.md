# 构建多智能体系统：何时以及如何使用

虽然单智能体系统能够有效处理大多数企业工作流，但多智能体架构可以为你的组织解锁额外价值。本文介绍何时以及如何使用多智能体系统。

> **来源：** [Claude Blog - Building multi-agent systems: When and how to use them](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)
> **作者：** Cara Phillips（贡献者：Paul Chen、Andy Schumeister、Brad Abrams、Theo Chu）
> **发布日期：** 2026 年 1 月 23 日
> **分类：** Agents | 产品：Claude Platform、Claude Code | 阅读时长：5 分钟

---

多智能体系统是一种架构，其中多个 LLM 实例以各自独立的对话上下文运行，通过代码进行协调。多种协调模式均有其价值（Agent 群集、基于能力的系统、消息总线架构），但本文聚焦于**编排者-子智能体模式**：一种层级模型，由主智能体（Lead Agent）生成并管理专门用于特定子任务的子智能体（Subagent）。这一模式提供了清晰的协调模型，是多智能体系统新手团队的良好起点。我们将在下一篇文章中详细探讨其他模式。

如今，多智能体系统往往被用于单智能体能表现更佳的场景，尽管随着模型的持续改进，这一判断正在不断演变。在 Anthropic，我们见过不少团队耗费数月构建精密的多智能体架构，最终发现对单智能体进行更好的提示词工程就能达到同等效果。在构建多智能体系统并与生产部署团队合作之后，我们总结出多智能体系统**持续优于单智能体**的三种情形：上下文污染影响性能时、任务可并行执行时、以及专业化能改善工具选择或任务聚焦时。在这三种情形之外，协调成本通常会超过收益。

本文将分享：如何识别单智能体的局限，找出多智能体系统表现出色的三种场景，以及如何避免常见的实现错误。

---

## 一、优先从单智能体开始

一个设计良好、配备了合适工具的单智能体，能够完成远超许多开发者预期的工作。多智能体系统引入了额外开销——每增加一个智能体，就意味着多一个潜在故障点、多一套需要维护的提示词、以及多一个意外行为的来源。

我们观察到，一些团队构建了包含规划、执行、审查和迭代等独立智能体的精密多智能体系统，结果却发现每次交接都造成上下文丢失，花在协调上的 token 比实际执行还多。在我们的测试中，对于等效任务，多智能体实现的 token 消耗通常是单智能体方案的 **3 到 10 倍**。这一开销来自：在各智能体间复制上下文、智能体间的协调消息，以及交接时的结果汇总。

---

## 二、多智能体系统的决策框架

多智能体架构在能解决单智能体无法克服的特定约束时才有价值。因此，多智能体架构应保留给能提供明确收益、足以证明额外成本合理的场景。

以下模式代表了我们持续观察到正向回报的情形。

### 上下文保护（Context Protection）

大语言模型的上下文窗口是有限的，随着上下文增长，响应质量可能下降。当一个智能体的上下文积累了某个子任务的信息，而这些信息与后续子任务无关时，就会发生**上下文污染**。子智能体提供了隔离能力——每个子智能体在专注于其特定任务的干净上下文中运行。

设想一个客户支持智能体，需要在诊断技术问题的同时检索订单历史。如果每次订单查询都向上下文添加数千个 token，智能体对技术问题的推理能力就会下降。

**单智能体方式（上下文不断积累）：**

```python
# 单智能体将所有内容积累进上下文
conversation_history = [
    {"role": "user", "content": "My order #12345 isn't working"},
    {"role": "assistant", "content": "Let me check your order..."},
    # 工具调用结果添加 2000+ token 的订单历史
    {"role": "user", "content": "... (order details, past purchases, shipping info) ..."},
    {"role": "assistant", "content": "Now let me diagnose the technical issue..."},
    # 上下文现在被智能体不需要的订单细节所污染
]
```

智能体必须在维护 2000+ token 无关订单历史的情况下推理技术问题，分散了注意力，降低了响应质量。

**多智能体方式（上下文保持干净）：**

```python
from anthropic import Anthropic

client = Anthropic()

class OrderLookupAgent:
    def lookup_order(self, order_id: str) -> dict:
        # 拥有独立上下文的子智能体
        messages = [
            {"role": "user", "content": f"Get essential details for order {order_id}"}
        ]
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=messages,
            tools=[get_order_details_tool]
        )
        # 只返回关键信息
        return extract_summary(response)

class SupportAgent:
    def handle_issue(self, user_message: str):
        if needs_order_info(user_message):
            order_id = extract_order_id(user_message)
            # 只获取所需内容，而非完整历史
            order_summary = OrderLookupAgent().lookup_order(order_id)
            # 注入紧凑摘要，而非完整上下文
            context = f"Order {order_id}: {order_summary['status']}, purchased {order_summary['date']}"

        # 主智能体上下文保持干净
        messages = [
            {"role": "user", "content": f"{context}\n\nUser issue: {user_message}"}
        ]
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            messages=messages
        )
        return response
```

订单查询智能体处理完完整订单历史后提取摘要。主智能体只接收实际所需的 50-100 个 token，使上下文保持聚焦。

**上下文隔离在以下情形最有效：**
- 子任务产生大量上下文（超过 1000 token），但大部分与主任务无关
- 子任务定义明确，有清晰的信息提取标准
- 需要在使用前进行过滤的查询或检索操作

---

### 并行化（Parallelization）

并行运行多个智能体，可以探索单个智能体无法覆盖的更大搜索空间。这一模式在搜索和研究任务中特别有价值。我们的 Research 功能就采用了这种方式：主智能体分析查询并并行生成多个子智能体，分别调查不同维度，每个子智能体独立搜索后返回提炼后的发现。与单智能体方式相比，多智能体搜索通过探索更大的信息空间，在准确率上取得了显著提升。

核心实现是将问题分解为独立的研究维度，并发运行子智能体，再合成结果：

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def research_topic(query: str) -> dict:
    # 主智能体将查询分解为研究维度
    facets = await lead_agent.decompose_query(query)

    # 并行生成子智能体研究每个维度
    tasks = [
        research_subagent(facet)
        for facet in facets
    ]
    results = await asyncio.gather(*tasks)

    # 主智能体合成发现
    return await lead_agent.synthesize(results)

async def research_subagent(facet: str) -> dict:
    """每个子智能体拥有独立的上下文窗口"""
    messages = [
        {"role": "user", "content": f"Research: {facet}"}
    ]
    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=messages,
        tools=[web_search, read_document]
    )
    return extract_findings(response)
```

覆盖面的提升是有代价的。多智能体系统对等效任务的 token 消耗通常是单智能体的 3 到 10 倍——每个智能体需要独立上下文、智能体间需要交换协调消息、结果在传递时需要汇总。虽然并行执行有助于减少总执行时间，但由于总计算量的大幅增加，多智能体系统的整体耗时往往比单智能体更长。

**并行化的主要收益是全面性，而非速度。** 当你需要在大规模信息空间中搜索，或调查复杂问题的多个维度时，并行智能体能比单智能体在上下文限制内覆盖更广的范围。代价是更高的 token 消耗和通常更长的总执行时间，换来的是更全面的结果。

---

### 专业化（Specialization）

不同任务有时受益于不同的工具集、系统提示或专业领域知识。与其为单个智能体提供数十种工具，不如让专业化智能体持有与其职责匹配的聚焦工具集，以提升可靠性。

#### 工具集专业化

当一个智能体拥有过多工具时，性能会下降。以下三个信号表明工具专业化有帮助：

- **数量过多**：工具超过 20 个时，智能体难以选择合适的工具
- **领域混淆**：当工具跨越多个不相关领域（数据库操作、API 调用、文件系统操作），智能体会混淆应该使用哪个领域的工具
- **性能退化**：添加新工具会导致现有任务性能下降，说明智能体已达到工具管理能力上限

#### 系统提示专业化

不同任务有时需要相互冲突的角色设定、约束或指令。客户支持智能体需要共情和耐心；代码审查智能体需要精确和批判性；合规检查智能体需要严格遵守规则；头脑风暴智能体需要创意灵活性。当单个智能体必须在相互冲突的行为模式间切换时，拆分为具有定制系统提示的专业化智能体能产生更一致的结果。

#### 领域专业知识专业化

某些任务受益于深度领域上下文，这些上下文会压垮通用智能体。法律分析智能体可能需要关于判例法和法规框架的大量上下文；医学研究智能体可能需要关于临床试验方法的专业知识。与其将所有领域上下文加载到单个智能体，不如让专业化智能体携带与其职责相关的聚焦专业知识。

**示例：多平台集成**

考虑一个需要跨 CRM、营销自动化和消息平台工作的集成系统。每个平台有 10-15 个相关 API 端点。拥有 40 多个工具的单智能体往往难以正确选择，在不同平台的相似操作间产生混淆。将其拆分为具有聚焦工具集和定制提示词的专业化智能体，可以解决选择错误问题：

```python
from anthropic import Anthropic

client = Anthropic()

# 具有聚焦工具集和定制提示词的专业化智能体
class CRMAgent:
    """处理客户关系管理操作"""
    system_prompt = """You are a CRM specialist. You manage contacts,
    opportunities, and account records. Always verify record ownership
    before updates and maintain data integrity across related records."""
    tools = [
        crm_get_contacts,
        crm_create_opportunity,
        # 8-10 个 CRM 专用工具
    ]

class MarketingAgent:
    """处理营销自动化操作"""
    system_prompt = """You are a marketing automation specialist. You
    manage campaigns, lead scoring, and email sequences. Prioritize
    data hygiene and respect contact preferences."""
    tools = [
        marketing_get_campaigns,
        marketing_create_lead,
        # 8-10 个营销专用工具
    ]

class OrchestratorAgent:
    """将请求路由到专业化智能体"""
    def execute(self, user_request: str):
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system="""You coordinate platform integrations. Route requests to the appropriate specialist:
            - CRM: Contact records, opportunities, accounts, sales pipeline
            - Marketing: Campaigns, lead nurturing, email sequences, scoring
            - Messaging: Notifications, alerts, team communication""",
            messages=[
                {"role": "user", "content": user_request}
            ],
            tools=[delegate_to_crm, delegate_to_marketing, delegate_to_messaging]
        )
        return response
```

这一模式反映了有效的专业协作——工具与职责匹配的专家，比试图在所有领域保持专业知识的通才合作更有效。但专业化引入了路由复杂性：编排者必须正确分类请求并委托给正确的智能体，错误路由会导致糟糕的结果。维护多个专业化智能体也增加了提示词维护开销。专业化在领域可清晰分离、路由决策明确时效果最佳。

---

## 三、超越单智能体架构的信号

除了上述通用框架，某些具体信号表明单智能体模式已经不够用：

- **接近上下文限制**：如果智能体经常使用大量上下文且性能在下降，上下文压力可能是瓶颈。注意，上下文管理的近期进展（如 Compaction）正在减少这一限制，让单智能体能够跨更长时间跨度保持有效记忆。
- **管理大量工具**：当智能体有 15-20 个以上工具时，模型会花费大量上下文和注意力理解可用选项。在采用多智能体架构之前，考虑使用 **Tool Search Tool**，它让 Claude 能够按需动态发现工具，而非预先加载所有定义。这可以将 token 使用降低高达 85%，同时提升工具选择准确率。
- **可并行的子任务**：当任务自然分解为独立的部分（跨多个来源的研究、多个组件的测试），并行子智能体可以带来实质性的加速。

这些阈值会随模型改进而变化。当前的限制代表实践指南，而非根本性约束。

---

## 四、以上下文为中心的任务分解

采用多智能体架构时，最重要的设计决策是如何在智能体间分配工作。我们观察到，团队经常在这一选择上出错，导致协调开销抵消了多智能体设计的收益。

**关键洞察是：分解工作时采用以上下文为中心的视角，而非以问题为中心的视角。**

**以问题为中心的分解（通常适得其反）**：按工作类型划分（一个智能体写功能，另一个写测试，第三个负责审查）会造成持续的协调开销。每次交接都丢失上下文——测试智能体不了解为何做出某些实现决策，代码审查智能体缺乏探索和迭代的背景。

**以上下文为中心的分解（通常有效）**：按上下文边界划分意味着处理某功能的智能体也应处理其测试，因为它已经拥有必要的上下文。工作只有在上下文能够真正隔离时才应拆分。

这一原则来自对多智能体系统失败模式的观察。当智能体按问题类型拆分时，它们陷入"电话游戏"，每次交接都在降低信息保真度。在一个按软件开发角色（规划者、实现者、测试者、审查者）专业化的智能体实验中，子智能体花在协调上的 token 比实际工作还多。

**有效的分解边界包括：**
- **独立的研究路径**：调查"亚洲市场趋势"和"欧洲市场趋势"可以并行进行，无共享上下文
- **具有清晰接口的独立组件**：有明确 API 契约时，前端和后端工作可以并行进行
- **黑盒验证**：只需运行测试并报告结果的验证者不需要实现上下文

**有问题的分解边界包括：**
- **同一工作的顺序阶段**：同一功能的规划、实现和测试共享太多上下文
- **紧密耦合的组件**：需要持续来回交互的组件应放在同一智能体中
- **需要共享状态的工作**：需要频繁同步理解的智能体应保持在一起

---

## 五、验证子智能体模式

在各领域中持续表现良好的一种多智能体模式是**验证子智能体**——一个专门负责测试或验证主智能体工作的独立智能体。

值得注意的是，更强大的编排者模型（如 Claude Opus 4.5）越来越能够直接评估子智能体的工作，而无需独立的验证步骤。但在以下情况下，验证子智能体仍然有价值：使用能力较弱的编排者时、验证需要专用工具时、或者你想在工作流中强制设置明确的验证检查点时。

验证子智能体成功的原因在于，它绕开了"电话游戏"问题。验证本质上只需要最少的上下文传递——验证者可以对系统进行黑盒测试，无需了解它是如何构建的完整历史，只需判断产物是否满足指定标准。

### 实现

主智能体完成一个工作单元后，在继续之前生成一个验证子智能体，并提供：要验证的产物、清晰的成功标准，以及执行验证的工具。

```python
from anthropic import Anthropic

client = Anthropic()

class CodingAgent:
    def implement_feature(self, requirements: str) -> dict:
        """主智能体实现功能"""
        messages = [
            {"role": "user", "content": f"Implement: {requirements}"}
        ]
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=messages,
            tools=[read_file, write_file, list_directory]
        )
        return {
            "code": response.content,
            "files_changed": extract_files(response)
        }

class VerificationAgent:
    def verify_implementation(self, requirements: str, files_changed: list) -> dict:
        """独立智能体验证工作"""
        messages = [
            {"role": "user", "content": f"""
Requirements: {requirements}
Files changed: {files_changed}

Run the test suite and verify:
1. All existing tests pass
2. New functionality works as specified
3. No obvious errors or security issues

You MUST run the complete test suite before marking as passed.
Do not mark as passing after only running a few tests.
Run: pytest --verbose
Only mark as PASSED if ALL tests pass with no failures.
"""}
        ]
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=messages,
            tools=[run_tests, execute_code, read_file]
        )
        return {
            "passed": extract_pass_fail(response),
            "issues": extract_issues(response)
        }

def implement_with_verification(requirements: str, max_attempts: int = 3):
    for attempt in range(max_attempts):
        result = CodingAgent().implement_feature(requirements)
        verification = VerificationAgent().verify_implementation(
            requirements,
            result['files_changed']
        )

        if verification['passed']:
            return result

        requirements += f"\n\nPrevious attempt failed: {verification['issues']}"

    raise Exception(f"Failed verification after {max_attempts} attempts")
```

### 适用场景

验证子智能体在以下场景有效：
- **质量保障**：运行测试套件、代码检查、根据 Schema 验证输出
- **合规检查**：验证文档是否符合策略要求、根据规则检查输出
- **输出验证**：在交付前确认生成内容满足规格
- **事实核查**：让独立智能体核查生成内容中的声明或引用

### 早期胜利问题

验证子智能体最重要的失败模式是在未经充分测试的情况下就将输出标记为通过。验证者运行一两个测试，观察到通过，便宣告成功。

**缓解策略：**
- **具体标准**：指定"运行完整测试套件并报告所有失败"，而非"确保它能运行"
- **全面检查**：要求验证者测试多个场景和边界情况
- **负向测试**：指示验证者尝试应该失败的输入，并确认它们确实失败
- **明确指令**：指令"You MUST run the complete test suite before marking as passed"至关重要——没有对全面验证的明确要求，验证智能体会走捷径

---

## 六、总结

多智能体系统很强大，但并非普遍适用。在增加多个协调智能体的复杂性之前，请确认：

1. **存在多智能体能解决的真实约束**，例如上下文限制、并行化机会，或对专业化的需求
2. **分解遵循上下文，而非问题类型**——按工作所需的上下文分组，而非按工作类型
3. **存在清晰的验证点**，子智能体可以在不需要完整上下文的情况下验证工作

我们的建议：从能奏效的最简单方法开始，只有在证据支持时才增加复杂性。

---

本文是多智能体系统系列的第一篇。更多相关阅读：
- 单智能体模式：[Building effective agents](https://anthropic.com/research/building-effective-agents)
- 上下文管理策略：[Effective context engineering for AI agents](https://claude.com/blog/context-engineering-for-agents)
- 多智能体研究系统构建实践：[How we built our multi-agent research system](https://claude.com/blog/how-we-built-our-multi-agent-research-system)

---

## 致谢

本文由 Cara Phillips 撰写，感谢 Paul Chen、Andy Schumeister、Brad Abrams 和 Theo Chu 的贡献。
