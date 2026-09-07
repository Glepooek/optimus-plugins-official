# AI 原生 SDLC 战术手册

> 原文：https://claude.com/blog/the-ai-native-sdlc-playbook

如何借助 AI 逐阶段改造你的软件开发生命周期。

- **分类**：[Enterprise AI](https://claude.com/blog/category/enterprise-ai)、[Claude Code](https://claude.com/blog/category/claude-code)
- **产品**：[Claude Enterprise](https://claude.com/solutions/enterprise)、[Claude Code](https://claude.com/product/claude-code)、[Claude Tag](https://claude.com/product/tag)
- **日期**：2026 年 8 月 21 日
- **阅读时长**：5 分钟
- **作者**：Louis Claxton

## 代码不再是瓶颈

各类组织已开始用 AI 以一年前无法想象的速度编写代码，然而围绕代码的流程却没有同步演进。

许多工程团队仍沿用原有的审批门禁、评审、交接与政策，拖慢了使用 [Claude Code](https://claude.com/product/claude-code) 这类智能体编码方案所带来的生产力增益。

软件开发生命周期（SDLC）是把软件从想法带到生产环境的流程。大多数组织都在运行同样六个阶段的某种变体，涵盖软件的规划、设计、构建、测试、部署与维护。传统上，每个阶段都是由不同角色负责的离散环节：产品经理编写需求，技术架构师将其转化为设计，工程师实现设计，受监管企业的 QA 团队负责验证，发布团队负责上线，运维团队监控运行状况。工作通过文档、工单与签核在各环节之间流转。

传统 SDLC 流程繁重，目的是确保每一步都有问责与管控。然而，传统 SDLC 的设计前提是：最耗时、最昂贵的阶段是编写与实现代码——而这一前提已不再成立。PRD、工作量估算仪式、产品安全评审，全都是为了在可能长达数周、数月乃至数个季度的开发工作中强行对齐认知。

传统 SDLC 的另一特征是：其管控机制假定每一步都由人来执行。而那些创造出最大价值的组织，已经围绕智能体 AI 当下的能力重建了流程，同时确保人始终留在闭环之中。在本指南中，我们将介绍 Applied AI 团队在内部把 Claude 集成进 SDLC 各阶段的若干最佳实践——这些实践源自我们与客户合作的经验——用以加速开发、让流程运转得更快。

当代码不再是瓶颈、构建阶段的速度超出传统 SDLC 的承载能力时，有三件事会随之成立：

* 瓶颈转移到构建阶段左右两侧的环节。主要是规划、评审/测试与部署，它们仍以人的速度运行。
* 管控机制与现实脱节，变得无法落地。当代码由人编写时，逐行人工评审是合理的；但一旦智能体写出了绝大部分 diff，人工评审就跟不上了。
* 治理成本上升，因为例外情况仍要走每周或每月才开一次的会议与委员会流程。

![构建不再是约束条件，人的速度才是](../assets/sdlc-44592f18.png)

构建已不再是约束条件——环绕它的那些以人的速度运行的环节才是。当构建被压缩到以小时计时，人力速度的阶段仍保持原有的时长。

以安全瓶颈为例。安全团队的人员规模是按人的产出量配置的，因此当智能体成倍放大代码产出时，要么评审队列不断积压，要么代码在评审不足的情况下上线。受监管的组织无法接受其中任何一种结果，所以它的安全与政策检查必须跟上智能体的节奏。

要更好地兑现智能体 AI 的生产力增益并保障其安全性，传统 SDLC 生命周期需要经历与实现阶段同等程度的转型。

目录

1. [代码不再是瓶颈](#sd-c1)
2. [战术集](#sd-c2)
3. [阶段 1 — 规划](#sd-s1)
4. [阶段 2 — 设计](#sd-s2)
5. [阶段 3 — 构建](#sd-s3)
6. [阶段 4 — 测试](#sd-s4)
7. [阶段 5 — 部署](#sd-s5)
8. [阶段 6 — 维护](#sd-s6)
9. [结语](#sd-c9)

## 什么是 AI 原生 SDLC？

AI 原生 SDLC 是一套重新构想的流程，它把原有的管控目标与全新的执行方式结合起来。流程不再是线性流转，而是变成一个闭环，AI 嵌入其中的每一个节点。AI 原生 SDLC 推动自动化的交接与后续战术的触发，有助于化解传统 SDLC 各阶段之间手工且笨拙的交接方式。

你也会听到这种转变被称作智能体 SDLC、AI SDLC，或干脆叫智能体软件开发——叫法不同，指的是同一件事。

![AI 原生 SDLC 的闭环示意](../assets/sdlc-53b010df.png)

### AI 原生 SDLC 六个阶段的转变

下表列出了传统 SDLC 与由 Claude 支撑的 AI 原生 SDLC 这两个极端之间的差异。大多数组织处于两栏之间的某个位置。

| 阶段 | 传统 SDLC | AI 原生 SDLC |
| :--- | :--- | :--- |
| 规划 | 由委员会收集需求，经研讨会与签核提炼，手工撰写成文 | Claude 直接从源头归纳痛点，并落成 `intent.md`——既可供人阅读，也可被机器执行 |
| 设计 | 由分析师撰写规格，由设计师解读 | 需求与设计压缩进与智能体的一次工作会话，以编码为 skill 的标准为指引，在 git 中版本化 |
| 构建 | 测试与代码手工编写，文档在主要开发完成之后才补写 | 测试与代码由 AI 生成，机构知识以版本化、机器可读的 `CLAUDE.md` 文件与 skill 形式维护 |
| 测试 | 在阶段边界设置 QA 门禁 | 持续评估贯穿实现全过程 |
| 部署 | 人工逐行评审代码，治理发生在评审周期中，且往往不一致 | 多层智能体评审，人工评审仅保留给受监管与关键代码。治理在 AI 行动的当下即被强制执行，以 hook 作为审批门禁 |
| 维护 | 人工盯着生产环境找 bug | 智能体监控线上部署。任何被突破的管控阈值带都会被诊断，并作为新的 `intent.md` 写回闭环 |

贯穿右栏的那条主线是「被提交的产物」。每个阶段以向版本控制写入一份产物作为结束（包括 `intent.md`、`spec.md`、`plan.md`、diff 及其测试、附带评审发现的 PR，以及事故记录），而下一阶段以读取它作为开始。对于前期阶段，.md 文件是主要产物形态，因为产品负责人与智能体都能读取并基于同一份文件行动。从构建阶段起，产物变为代码及其记录。这条提交链同时就是审计轨迹：谁提出了什么诉求、智能体产出了什么、谁批准了它。

对于每一项需要判断力的决策，人始终负有问责。在智能体 SDLC 的世界里，人的注意力随着必须被评审的产物一同转移。

每个阶段都提交一份下一阶段可读取的产物。意图、规格、计划、diff 与评审发现合在一起，就是审计轨迹。

## 战术集

战术（play）是本手册的核心，它们被归入六个非线性阶段（规划、设计、构建、测试、部署、维护），共同覆盖完整的生命周期。

每个战术包含：

* 什么发生了变化；
* 如何起步；
* 具体的实施步骤；
* 治理方面的考量；以及
* 如何衡量它是否奏效。

这些步骤是模块化的，组织可以根据自身独特需求，选择在不同时间优先改造不同阶段。每个战术都在「前置条件」下标明其依赖项，依赖关系图会进一步呈现这些依赖。

一个阶段以提交一份产物作为结束，该次提交则启动下一阶段。一份被接受的 `intent.md` 触发需求与设计流程，一份被批准的 `spec.md` 触发 plan mode，一个被合并的 PR 触发流水线，而生产环境中一条被突破的管控阈值带则写出下一份 `intent.md`——闭环由此延续。

起初，你手工提示每一个步骤；终态则是一个闭环，其中每一份被接受的产物都会触发下一道门禁。人的注意力集中在这些门禁上，评审智能体标记出的内容，而不是每个阶段都从零开始。

![战术依赖关系图](../assets/sdlc-5d5a3c05.png)

图中战术按阶段列出；箭头给出的是采纳它们的顺序。二者并不相同。可以从任意一个陶土色战术开始——没有箭头指向它，因此它无需任何前置。对于其他任何战术，指向它的箭头就是需要先行采纳的战术。

**01**

## 规划

想法不必再等着某个人把它写下来。意图被一次性捕获，用提出者自己的话，形成一份下一阶段可以据以行动的版本化产物。

### 以 intent.md 形式捕获

启动软件开发流程的 `intent.md` 可以通过不同途径进入：某人产生了一个想法、有人提交了一张工单，或者某次事故通过告警浮现出来（见阶段 6：维护）。

当某人产生想法时，他与 Claude 进行头脑风暴，产出一份 markdown 原型规格。在传统 SDLC 中，这个人接下来必须说服产品团队的某位成员与他一起、或代他把这个想法写成文档。

Claude 生成的原型规格可供人阅读、被版本控制，并可立即被下一阶段消费。这份原型规格被保存为 `intent.md`。

无论意图源自事件触发还是智能体，步骤都相同：产品负责人在提交前审阅并订正由智能体撰写的 `intent.md`。

**传统方式**：一个想法要先经过待办条目、用户故事、故事点与需求梳理会议，才有人能着手处理。所有权在每次交接时转移，因此到达工程团队的内容，与提出者原本的意思之间已隔了好几层。

**AI 原生方式**：提出者与 Claude 头脑风暴，并把结果写成 `intent.md`——一份用提出者自己的措辞写就的原型规格。这份产物包含想要什么、为什么要、以及在哪些约束之下。重复性流程通过 skill 编码固化。

如何起步

**前置条件**

无。

**基础设施**

为非工程人员提供 Claude 访问权限（claude.ai 或 [Cowork](https://claude.com/product/cowork)）；一份约定好的 `intent.md` 模板；一个由产品负责人关注的、共享且受版本控制的意图存放处。对于单个产品，最简单的存放处是产品仓库中的 `intent/` 目录。这样的设置让产物链条与由其派生出的代码放在一起。只有当意图跨越多个仓库时，专设一个意图仓库才值得这份额外开销；而在 monorepo 中，它就是一个目录。阶段 3：构建的补充说明中会讲到这个存放处与已经承载记录的 Jira 或需求管理工具之间的关系。

搭建这套机制对平台或工程团队来说是一次性任务。需要一位技术团队成员把意图存放处立起来，并决定谁有写入权限——因为贡献者会来自组织的各个角落。

仓库一旦建立，没有 git 经验的贡献者不需要直接使用 git。取而代之的是，一个连接到版本控制系统（例如 GitHub）的 connector 让 Claude 从 claude.ai 或 Cowork 代他们提交 markdown 文件。

#### 如何执行

1. 提出者用自己的话向 Claude 描述问题。提出者可以描述他今天做不到什么、这个想法会影响谁、更好的状态是什么样，或者哪些内容不在范围内。不需要使用任何正式措辞。
2. 头脑风暴直到想法变得具体。Claude 会问出分析师会问的那些问题：范围、用户、约束，以及成功的标准是什么。
3. 让 Claude 使用组织的模板把结果写成 `intent.md`——该模板可以由技术团队成员编码成一个 skill 并由负责人签核。模板可涵盖问题、期望结果、受影响的用户与系统、约束条件，以及开放性问题。
4. 提出者订正 Claude 理解有误的任何地方。
5. 把 `intent.md` 提交到共享存放处。作者与时间戳随之进入记录，产品负责人从这里接手这个想法。

```
# Intent: claims status self-service
Author: J. Ortiz (claims operations). Status: draft.

## Problem
Customers phone the contact center to ask where their claim is.
Handlers spend roughly a third of call time on status-only queries.

## Proposed outcome
Customers see claim status, next step and expected date in the portal.

## Affected users and systems
Claims handlers, portal team, claims-core API.

## Constraints
No new PII in the portal session. Existing authentication only.

## Open questions
Do third-party loss adjusters need access too?
```

#### 治理考量

证据就是那份已提交的 `intent.md`，其中列出了作者、时间戳与完整的修订历史。它被记录在意图存放处的 git 历史中。产品负责人做出批准，而把意图送入阶段 2：设计的接受或拒绝决策，则以合并动作或结案评审的形式被记录下来。

如何衡量

**先行指标**

从第一次对话到 `intent.md` 被提交所耗费的时间，从意图存放处的 git 历史中读取（其中记录了作者与时间戳）。预期是从长达数周的需求获取与梳理周期缩短到数小时。

**滞后指标**

存活率，即产品负责人接受并送入阶段 2：设计（而非关闭）的 `intent.md` 文件占比。接受或拒绝的决策以产物被合并或评审被关闭的形式记录。此外还包括：同一变更的第一份 `spec.md` 提交之后，`intent.md` 又被修改的次数。

**02**

## 设计

需求与设计坍缩进同一次会话。政策在规格被撰写的当下就得到应用，而不是几周后在评审中才被发现。

### 需求与设计

一旦获得产品负责人批准，Claude 就接过被接受的 `intent.md`，产出一份需求与设计规格。这个过程由组织在品牌、安全、合规与 UX 方面的 [skill](https://code.claude.com/docs/en/skills) 引导。

产品负责人评审这份规格，但不撰写它。这个流程的目标是产出一份工程团队可以据以做计划的规格，并标记出需要关注的领域。

前端工作是最清晰的例子。`intent.md` 一旦被接受，产品负责人就依据它在 [Claude Design](https://claude.com/product/design)（beta）中做出设计稿，对稿件进行迭代，然后将其导出到 Claude Code 去构建。

**传统方式**：需求与设计是由不同团队负责的两个独立阶段。分析师把想法形式化为需求，设计师再把这些需求反向解读成设计。这种分离是为了问责而存在的，但它既慢又有损耗。

**AI 原生方式**：两个阶段发生在一次被提示的会话中。Claude 接过 `intent.md`，在组织 skill 的约束下产出一份需求与设计规格，并标记出需要关注的领域。

如何起步

**前置条件**

先写好一份 `intent.md` 文件，并把品牌、安全、合规与 UX 政策写成 skill。

**基础设施**

一位拥有 Claude 访问权限的产品负责人。不需要任何工程技能。

#### 如何执行

1. 产品负责人开启一次会话，让组织的 skill 可用，并附上 `intent.md`。
2. 产品负责人的提示词指向 `intent.md`，点明各项约束，并要求标记出关注点。一开始手工运行，随后将其固化为组织级别的 slash command。再往后，把意图存放处中 `intent.md` 的被接受动作作为触发器，用一个在合并时触发的非交互式任务，在加载了组织 skill 的前提下运行该流程，并以 pull request 的形式提交 `spec.md`（阶段 5：部署中的 CI/CD 战术会讲到这套管道）。从此刻起，产品负责人第一次介入就是评审。
3. 同一位产品负责人对照最初的想法评审这份规格。规格是否解决了所陈述的问题？`intent.md` 中的开放性问题是否已被回答或被延续下来？
4. 优先处理被标记出的关注点，因为它们正是分析师本会升级上报的那些点。产品负责人在工程团队看到规格之前，与各自的政策负责人逐条解决这些关注点。
5. 把 `spec.md` 与 `intent.md` 一并提交。这一对文件记录了「当初要什么」与「最终定了什么」。
6. 产品负责人决定规格与意图是否推进到构建阶段，对于组织归类为较高风险的事项则咨询技术负责人。这个判断始终由人类队友做出，而接受规格正是启动阶段 3：构建中 plan mode 战术的动作。

#### 实际样例（提示词）

```
Read the attached intent.md and produce a requirements and design spec for integrating it into our existing codebase. Apply the skills available to you so the plan conforms to our brand guidelines, security policies and UX standards. Document the spec fully as spec.md, ready to hand to the engineering team. Describe clearly any areas of concern, especially where you cannot satisfy contradicting policies.
```

#### 治理考量

政策不再是几周后在评审中才被发现，而是在规格被撰写的当下就被读取并应用。组织的 skill 作为约束条件被施加到规格上。规格本身、产生它的提示词，以及当时生效的 skill 版本，全部记录在版本控制中。产品负责人签核规格，并把被标记的关注点路由给指定的政策负责人。

如何衡量

**先行指标**

同一变更的 `intent.md` 提交与 `spec.md` 提交之间的间隔时长（两个 git 时间戳），与旧有的「需求 + 设计」周期作对比。

**滞后指标**

构建开始之后的需求返工量。统计同一变更中，日期晚于第一份 `plan.md` 提交的 `spec.md` 提交数。git log 可以直接给出这个数字。

**03**

## 构建

没有被接受的计划，就不会有任何实现动作。机构知识变成智能体可读取的文件，护栏以代码形式运行，而不是靠习惯维系。

### 以 Claude Code plan mode 作为默认起点

工程师在 [plan mode](https://code.claude.com/docs/en/permission-modes) 下启动 Claude Code 会话，把阶段 2：设计中批准过的 `spec.md` 交给 Claude，让它反过来向自己提问，并不断迭代计划，直到工程师满意为止。

**传统方式**：工程师读完设计就开始写代码。这个变更将如何实现——具体到哪些文件、哪些测试——留在工程师的脑子里，最好的情况下也不过是一条工单评论。没有别人能评审它。评审者看到的第一样东西就是完成后的 diff，而到那时返工已经很慢了。

**AI 原生方式**：工作从一份书面计划开始，由 Claude 在 plan mode 下产出——在该模式下它可以读取代码库而不做任何改动。工程师在代码被写出之前订正计划，被批准的版本以 `plan.md` 形式提交，供后续阶段据以核对。

如何起步

**前置条件**

意图产物（`intent.md` 或 `spec.md`，若存在的话），另外有 `CLAUDE.md` 文件会有帮助。

**基础设施**

拥有仓库访问权限的 Claude Code。

#### 如何执行

1. 工程师在 plan mode 下与 Claude 开启会话。
2. 工程师把 `intent.md` 和 `spec.md` 交给 Claude，要求给出一份实现计划，其中点明哪些文件会变更、工作的先后顺序，以及用来证明其正确的测试。
3. 拷问这份计划：问它这个变更可能破坏什么、哪一步风险最高、Claude 主动放弃了哪些其他选项。
4. 反复迭代，直到一个从未看过这段对话的工程师，仅凭这份计划就能实现该变更。
5. 把被批准的计划提交为 `plan.md`。该计划加入审计轨迹，而 PR 评审战术（阶段 5：部署）会拿最终的 diff 与它核对。
6. 接受计划，让 Claude 去实现。有了一份扎实的计划，实现往往一次通过。
7. 当实现偏离了计划时，在同一次提交中更新 `plan.md`。可以考虑用 hook 来强制这两者保持同步。

#### 实际样例（plan.md）

```
# Plan: claims status self-service (from intent.md 2026-06-02)

## Files that change
portal/src/claims/StatusPanel.tsx (new), claims-api/routes/status.py,
claims-api/tests/test_status.py

## Order of work
1. Add the status endpoint behind existing auth.
2. Panel against the endpoint.
3. Wire into the portal nav.

## Risks
The claims-core API rate-limits at 50 rps; the panel must cache.

## Proof
test_status.py covers the four claim states; screenshot matches the
approved mock.
```

#### 治理考量

设计评审发生在任何代码被生成之前，此时改变方向还只是编辑一份文档的事。plan mode 本身就强制了这一点，因为在工程师接受计划之前，Claude 无法编辑文件。计划及其修订会连同「谁接受了它」一并被记录。常规变更由工程师批准，任何被组织归类为较高风险的事项则交由技术负责人或架构师处理。

如何衡量

**先行指标**

第一次实现流程就完成合并的变更占比，以及从计划批准到 PR 合并的时长——所需数据都在 PR 元数据中。

**滞后指标**

每个变更的返工轮次（同样取自 PR 元数据），以及合并后的 diff 与已提交的 `plan.md` 仍然吻合的频率。

### Claude Code 的 auto mode

Claude Code 也可以运行在 auto mode 下：工程师批准计划，在满意且经过迭代之后，Claude 逐项应用每处改动，不再逐次编辑请求确认。随着后续战术中的护栏逐渐成熟（一份调校过的 `CLAUDE.md`、把政策编码进去的 skill、拦截不安全动作的 hook，以及一套 Claude 可以运行的测试集），auto-accept 就成了常规工作的默认选项：一份严密的 `spec.md`、较小的影响半径，以及已被测试覆盖的代码。

现在的转变是：从用户盯着智能体做编辑、逐个审查动作，转向在更长的自主会话之后评审产物。auto-accept 模式在与 worktree 配合使用时，还能进一步实现个人内部与团队之间的并行，它也是自主运行 SDLC、闭合阶段 6：维护中所述闭环的基础。

补充说明

### 遗留系统与真源

*适用于该流程产出的每一份产物。*

现有的 SDLC 流程很可能已经在追踪各类产物，只是没有以 markdown 文件的形式。工作项可能在 Jira 里，需求在一个内建了监管可追溯性的工具里，设计在 Figma 里，变更审批在变更委员会那里。这些系统很难被取代，因为审计师与监管方已经认可它们，其他团队也依赖它们——所以 AI 原生 SDLC 必须围绕既有现实来适配。

在向 AI 原生 SDLC 过渡时，针对该流程产出的每一份产物，指定一个系统作为真源，其余所有系统只持有副本或指向原件的链接。以下几种配置都可以做到「只有一个真源」，而具体选哪种可以因产物而异：

**以仓库为真源。** markdown 产物是权威记录，遗留系统引用提交内的文件。对于工程主导的组织，这可能是最清爽的配置之一，因为所有记录都活在同一个工具里，只有一个时间戳权威。

**以遗留系统为真源。** Jira、ServiceNow 或需求管理工具持有权威记录，markdown 产物是工作副本。Claude 在会话开始时读取记录，并在产出规格或计划的同一次会话中，通过 [MCP](https://code.claude.com/docs/en/mcp) connector 把结果写回去。

**以互相关联作为最低标准。** 所有产物都标注记录 ID，所有遗留记录都包含对应 markdown 文件的提交 SHA。在向 AI 原生 SDLC 过渡时，互相关联是个不错的起点——代价是接受存在两个真源。

遗留系统与 markdown 优先的系统可以共存，只要两者之间有链接，或者其中之一被明确宣告为真源。

### CLAUDE.md

[`CLAUDE.md`](https://code.claude.com/docs/en/memory) 为 Claude 提供一位新人所需要的上下文，涵盖约定、命令、架构，以及团队最常遇到的那些错误。过去存在于人们脑中和 wiki 上的知识，变成了智能体在每次会话开始时都会读取的一份文件，由整个团队共同维护，并在每次犯错之后迭代。

如何起步

**前置条件**

无。

**基础设施**

一个仓库、已安装的 Claude Code，以及一位熟悉这套代码库的工程师。

#### 如何执行

1. 在仓库中运行 `/init`。Claude 会根据它发现的内容生成一份初始的 `CLAUDE.md`。
2. 把生成的文件精简到「新人第一天所需要的内容」。保留构建、测试与 lint 命令、真正重要的约定，以及 Claude 反复搞错的那些事。
3. 把 `CLAUDE.md` 提交到 git 仓库根目录，这样整个团队共享同一个版本，改动也像代码一样被评审。
4. 有一条实践准则很有用：当 Claude 第二次犯同一个错误时，就把对应的纠正写进 `CLAUDE.md`。
5. 把篇幅控制在一页以内，因为 Claude 在会话开始时会读完全文，任何过时的内容都在白白占用上下文。

#### 实际样例（CLAUDE.md）

```
# Payments service

## Commands
- Build: make build
- Test: make test (unit), make itest (integration, needs docker)
- Lint: make lint (runs in CI; fix before pushing)

## Conventions
- Java 21, Spring Boot 3. No new Lombok.
- Money is always BigDecimal, never double.
- Every endpoint needs an integration test in src/itest.

## Architecture
- api/ holds REST controllers, core/ holds domain logic,
  adapters/ talks to external systems.
- Kafka events are defined in schemas/; never edit generated classes.

## Things Claude gets wrong
- Do not bump dependency versions; the platform team owns them.
- The legacy v1/ package is frozen; changes go in v2/.
```

#### 治理考量

`CLAUDE.md` 受版本控制，因此智能体所依据的指令是可评审、可审计的。团队约定通过这份文件得到应用，对它的改动记录在 git 历史中，代码负责人在 PR 评审中批准这些改动。

如何衡量

**先行指标**

Claude 重犯本应被 `CLAUDE.md` 拦住的错误的频率。对 `CLAUDE.md` 的纠正或改动应当在 git 历史中被追踪。

**滞后指标**

从 PR 历史中读取的、团队新成员第一个 PR 被合并所需的时间。

### 把 skill 当作机构知识

skill 是组织让自身机构知识可操作化的方式。这些指令是显式的、受版本控制的、被广泛应用的，并在政策变更时集中更新。经验法则是：为那些必须被一致应用的机构知识写 skill；不要为本该属于 `CLAUDE.md` 或提示词的内容写 skill。

如何起步

**前置条件**

无硬性要求。有一份 `CLAUDE.md` 会有帮助，因为它把智能体的工作知识留在仓库里，但 skill 并不依赖它。

**基础设施**

一条有明确负责人、且有书面真源的政策。

#### 如何执行

1. 挑一条今天执行得不一致的知识。它可以是一项安全标准、一条 API 设计约定，或一条品牌规则。
2. 把它写成 skill——一个包含 `SKILL.md` 的目录，其 frontmatter 说明何时触发，正文说明该做什么。由工程师依据政策负责人的真源撰写，并借助 Claude 辅助。
3. 把 skill 放在仓库的 `.claude/skills/<name>/` 下，使其随代码一同分发；或者通过 [plugin](https://code.claude.com/docs/en/plugin-marketplaces) 在全组织范围内分发。
4. 测试 skill 是否会被触发。用不同的表述方式让 Claude 执行相关任务，确认 skill 每次都会加载。
5. 政策变更时，修改 skill 并让政策负责人签核该改动。
6. 工程师在下一次会话中自动获得新版本。

#### 实际样例（.claude/skills/secure-api-review/SKILL.md）

```
---
name: secure-api-review
description: Apply the API security standard. Use whenever creating or
  modifying an external-facing endpoint, reviewing API code, or
  generating an OpenAPI spec.
---
# Secure API review

When you create or change an API endpoint:
1. Authentication: every endpoint requires the gateway JWT;
   no anonymous routes outside /health.
2. Input validation: validate request bodies against the OpenAPI
   schema and reject unknown fields.
3. Audit: every state-changing endpoint emits an audit event with
   actor, action, entity and timestamp.
4. Data classification: fields tagged pii in the schema must never
   appear in logs or error messages.

Run scripts/check-endpoints.sh and include its output in your summary.
```

#### 治理考量

skill 是一种管控手段，尽管只是建议性的。它让 Claude 很可能在代码被写出的当下就应用该政策，但没有任何机制强制某次会话必须遵守它。一条必须永远成立的政策，需要在 skill 背后有确定性的东西托底，比如一个拦截该动作的 hook，或者一次在 PR 阶段重新核查该政策的评审流程。skill 让违规变得罕见，hook 则让违规近乎不可能。skill 的调用会被记录在会话轨迹中，政策负责人像评审代码一样评审 skill 的变更。

如何衡量

**先行指标**

从政策负责人批准一次政策变更，到更新后的 skill 被合并所耗费的时间，取自该 skill 目录上的 PR。

**滞后指标**

PR 评审中引用该政策的发现数量——一旦 skill 在代码被写出的当下就应用了政策，这个数字应当趋近于零。如果它没有趋近于零，那么要么 skill 没有被触发，要么它的文本已与官方政策发生漂移。

### 把 hook 当作构建期护栏

skill 是建议性的管控，而 [hook](https://code.claude.com/docs/en/hooks) 是它背后那层确定性机制。Claude 的大部分动作是实现过程中的文件编辑与 shell 命令，因此构建阶段往往是 hook 触发最频繁的地方。

构建阶段的 hook 可以：

* 拦截对受保护路径的编辑，例如生成的类文件或已冻结的包；
* 在文件编辑之后运行格式化工具与 linter，使漂移永远不会累积；
* 让凭据不进入 diff。

任何其政策必须无例外成立的 skill，都要有 hook 托底。hook 会在每个与之匹配的动作上运行，因此构建阶段的 hook 应当快速，且范围限定在发生变更的那个文件上。更重的检查（比如完整测试集）应放在提交或 PR 环节。

那种需要请求人工批准的 hook 属于阶段 5：部署中的门禁，因为在构建过程中弹出审批提示，等于把人重新放回所有并行会话的关键路径上。

### 并行会话与子智能体

一位工程师可以同时推进多条工作流。

并行会话是指另一个完整的 Claude Code 实例，在它自己的 [git worktree](https://code.claude.com/docs/en/worktrees) 中处理一项独立任务。每个独立会话对其他会话一无所知，驾驭它们的那位工程师是它们唯一的共同点。

[子智能体](https://code.claude.com/docs/en/sub-agents)运行在单个会话内部，是一个范围受限的助手，拥有自己的上下文窗口与工具权限限制，适合处理在多个任务中反复出现的工作，例如验证应用是否按预期运行。

并行会话提升了一位工程师能同时推进的任务数量，而子智能体让每个会话专注于自己的任务。工程师的职责是驾驭并评审它们全部。

**传统方式**：一位工程师一次做一项任务，一天或一周中相当一部分时间花在构建、测试与等待评审者上。等待期间切换到别的任务是可行的，但上下文切换足够累人，以至于很少有人愿意这么做。

**AI 原生方式**：一位工程师同时运行多个 Claude 会话，每个都在各自的 worktree 中处理各自的任务。重复性工作变成拥有独立上下文与工具限制的子智能体。工程师的职责转向编排，并最终转向构建与监控闭环。

如何起步

**前置条件**

`CLAUDE.md`，因为所有会话都会读取这份文件。反馈闭环（阶段 4：测试）在这里同样有帮助，因为当一个会话能够自行验证成果时，就不那么需要工程师的监督了。

**基础设施**

一个 git 仓库（隔离性来自 worktree），以及经过调校的权限设置——让会话不必为组织认定安全的命令停下来等待审批提示。

#### 如何执行

1. 工程师把工作拆分成触及不同文件的任务，借助 plan mode 战术（阶段 3：构建）产出的计划来判断哪些工作是彼此独立的。共享同一批文件的任务放在单个会话中依次执行。
2. 每个并行任务拥有自己的 worktree，例如在一个终端里运行 `claude --worktree feature-auth`，在另一个终端里运行 `claude --worktree fix-rate-limit`。worktree 是位于独立分支上的一份单独检出，可以避免会话之间在文件上发生冲突。
3. 两到三个会话是合理的起点。实际上限取决于一个人能认真评审多少条工作流，因此只在评审跟得上的前提下才增加会话数。
4. 把重复性工作转化为子智能体，以 markdown 文件形式定义在 `.claude/agents/` 中，每个都带有名称、何时使用的描述，以及它可以触及的工具。例子包括：在主智能体完成后剥除多余复杂度的代码简化器；运行应用并检查行为的验证器；探索代码库并汇报结果、且不会淹没主上下文的调研员。把这些定义提交进 git，让整个团队共享。

#### 实际样例（.claude/agents/verifier.md）

```
---
name: verifier
description: Runs the app and checks the change works before the session
  reports done
tools: Bash, Read
---
Start the app with make run. Exercise the changed behavior and the two
nearest neighboring flows. Report what you ran, what you saw, and any
behavior that does not match plan.md. Do not fix anything; report only.
```

#### 治理考量

会话越多，产出越多，因此管控必须来自仓库中的配置。放在那里的 hook 与权限设置对所有会话生效，而某个会话做了什么会被记录并归属到运行它的那位工程师名下。

如何衡量

**先行指标**

在评审质量不下滑的前提下，每位工程师的并发会话数（从 OpenTelemetry 导出数据中统计），以及一天中用于驾驭而非等待的时间占比。

**滞后指标**

每位工程师每周合并的变更数，结合从 PR 历史中确定的返工率一并解读。

**04**

## 测试

每个会话在人看到之前先自查成果，而那些驾驭智能体的配置，也像它所写的代码一样接受回归测试。

### 给 Claude 一个反馈闭环

始终给 Claude 一条自行验证成果的途径，无论是测试、构建，还是截图比对。会话在工程师看到之前先自查成果、自行修正错误。

不要把反馈闭环与验证器子智能体（阶段 3：构建）混为一谈。反馈闭环贯穿整个任务，工作需要跑多少次就跑多少次。而验证器子智能体是打包最终检查的一种方式：在会话认为工作已完成时，用一个全新的上下文窗口跑一次。这样一来，结论就不会被产出这些代码时的那些假设所染色。

**传统方式**：代码可用的信号来得很晚。CI 要等几分钟，测试人员要等几天，生产环境要等几周。当代码由智能体产出时，迟到的信号意味着必须由人来检查它的全部输出，而这个人就成了瓶颈。

**AI 原生方式**：会话被赋予一条在人看到之前自查成果的途径。跑测试、跑构建、截图。Claude 反复迭代直到检查通过，因此送到工程师面前的东西已经通过了检查。搭建这个闭环的责任落在运行该会话的工程师身上，下面的步骤就是写给他们的。

如何起步

**前置条件**

无。

**基础设施**

一套测试集与一套构建，各自都能用一条命令在本地运行。对于 UI 工作，让 Claude 能「看到」结果至关重要——可以是一个浏览器工具，或者通过 MCP 接入的截图工具。

#### 如何执行

1. 如果今天检查成果需要一串命令外加一些环境知识，就把它包装成单一目标，比如 "make test" 或 "npm test"，并让它在失败时返回非零退出码。
2. 在 `CLAUDE.md` 的 Commands 一节中，逐条列出命令，并附上一个正常输出的示例。
3. 陈述一个目标，并让它可量化，这样 Claude 无需询问你就能自查成果，例如：「test\_status.py 中所有测试通过」「截图与附上的设计稿一致」或「该端点返回 200 且包含新字段」。
4. 对于 bug 修复，先写失败的测试。让 Claude 把 bug 复现为一个测试、运行它，并确认它失败的原因与你预期的一致。提交这个测试。只有到那时，才让 Claude 在不修改测试的前提下让它通过——用最后一步中的测试文件 hook 来强制这项限制。一个在修复之前就已存在、且智能体无法改写的测试，是 bug 确已消失的证明。
5. 对于 UI 工作，用视觉检查闭合回路。给 Claude 一个浏览器或截图工具，给它设计稿，让它迭代：实现、截图、比对、调整。两三轮是正常的，且每一轮结果都应该有所改善。
6. 把验证纳入「完成」的定义。相关指令写在 `CLAUDE.md` 中：在报告任务完成之前先跑测试，并展示输出。
7. 最后，闭环本身也需要保护，因为一个正在修复代码的智能体，绝不能有能力削弱针对那段代码的检查。用一个在修复任务期间拦截测试文件编辑的 hook 就能做到这一点。替代方案是在评审中检查 diff，并拒绝任何触及测试的改动。

#### 实际样例（CLAUDE.md 中的验证块）

```
## Verifying your work

- Build: make build (must finish with "Build succeeded")
- Test: make test (all green; never skip or delete a failing test)
- Lint: make lint (zero warnings)

Run all three before reporting any task complete, and paste the output.
If a test fails, fix the code, not the test.
```

治理考量

**强制执行了什么**

在任务被报告完成之前必须验证，以及在修复任务期间禁止智能体编辑测试文件——在组织希望得到保证的场合，二者都以 hook 形式实现。

**证据是什么**

Claude 实际运行并粘贴出来的 "make test" 原始输出、构建日志，或截图比对结果——因此证据来自工具链本身。

**记录在哪里**

记录在会话轨迹中（由 OpenTelemetry 导出转发到组织的可观测性栈），以及 PR 的检查运行记录中——评审者与日后的任何审计人员都能在那里看到它。

**由谁批准**

评审该 PR 的代码负责人。由于机械性证据已经附上，他可以把注意力集中在意图与风险上。

如何衡量

**先行指标**

智能体所写变更的 CI 首次通过率——这是 CI 系统本来就支持的数据。

**滞后指标**

每个 PR 的评审耗时（取自 PR 元数据）——一旦测试能抓住过去靠评审者才能抓住的问题，这个数字就应当下降；以及来自事故追踪系统的变更失败率。

### CI 中的持续评估

评估（eval）是 QA 阶段门禁在 AI 原生世界中的对应物。落到实处，它意味着一套在智能体配置发生变化时就会运行的测试集。当换入一个新模型或重写一段提示词时，评估集会告诉你这个智能体是否仍以同样的标准完成工作。

评估集应当被视为一套活的测试集。随着模型能力提升，曾经具有区分度的用例会失去区分度，必须从持续监控中提炼出新的用例加进来。

视具体使用场景而定，有些团队可能更愿意按固定节奏离线运行这些评估，而非每次变更都跑。下面的步骤针对的是持续评估。

如何起步

**前置条件**

`CLAUDE.md` 与反馈闭环（阶段 4：测试）。

**基础设施**

能够非交互式运行 Claude Code 的 CI，以及一个有预算支撑评估运行的 API key。

#### 如何执行

1. 平台工程师从近期工作中收集 20 到 50 个真实任务，连同其预期/已接受的结果。
2. 把每个任务写成一条评估，即提示词加上定义「可接受」的各项检查（测试通过、lint 干净、行为未变、政策被遵守）。
3. 该测试集在 CI 中非交互式运行——按计划定时运行，以及在 `CLAUDE.md`、skill 或 hook 发生任何变更时运行，因为这些配置驾驭着智能体，理应享有代码所拥有的回归测试待遇。
4. 用评估结果为配置变更设门禁。一次导致通过率下降的 skill 变更，在合并前必须经过评审。
5. 每次生产事故都对应一条评估，由该事故的归属团队撰写，并作为回归测试长期留在测试集中。

#### 实际样例（.github/workflows/agent-evals.yml）

```
name: Agent evals
on:
  pull_request:
    paths: ['CLAUDE.md', '.claude/**']
  schedule:
    - cron: '0 2 * * *'
jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g @anthropic-ai/claude-code
      - name: Run eval suite
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          for eval in evals/*.json; do
            claude -p "$(jq -r '.prompt' $eval)" \
              --allowedTools "Read,Edit,Bash(make test)" \
              --output-format json > result.json
            ./evals/check.sh "$eval" result.json
          done
```

#### 治理考量

评估给了 QA 一道能跟上智能体产出速度的门禁。通过率阈值以合并检查的形式强制执行，每次运行都被记录以便跨时间对比结果，而配置变更由其归属团队批准。

如何衡量

**先行指标**

评估通过率随时间的变化（每次运行时由测试集报出），以及一次生产事故转化为常驻评估所需的时长。

**滞后指标**

在 CI 中被拦截的回归数量，与逃逸到生产环境的回归数量作对比——数据源自事故追踪系统。

**05**

## 部署

评审在两个方向上运行，治理在智能体行动的当下即被强制执行。智能体做完生产门禁之前的一切，绝不越过它一步。

### AI 进入 PR 评审闭环

Claude 既做评审，也接受评审。它依据组织的政策评审传入的 PR，也处理自己所提 PR 上的评审意见。这让工程师在 PR 评审中可以专注于行为本身，归根结底就是判断意图与风险。

**传统方式**：评审能力是按人的产出量规划的。一个 PR 要等评审者把它全部读完，评审质量随评审者的负载而波动，作者不断催促，而积压却越堆越多。

**AI 原生方式**：所有 PR 都经过完全一致的一组评审流程，发现项按严重程度排序。人的注意力上移一个层次——变更是否达成了计划所意图的目标，以及风险是否可以接受。

如何起步

**前置条件**

来自阶段 3：构建的最新 `CLAUDE.md` 文件；如果评审流程要强制执行成文政策，则还需要 skill，以及已定义的子智能体。

**基础设施**

一个安装了 Claude 集成的仓库——可以是由管理员启用的托管版 [Code Review](https://code.claude.com/docs/en/code-review)（研究预览）服务，也可以是运行在你自己 CI 中的 [claude-code-action](https://code.claude.com/docs/en/github-actions)，并在需要时通过 AWS Bedrock、Google Vertex 或 Microsoft Foundry 发起模型调用（CI/CD 战术会讲到部署选项）。要求代码负责人批准的分支保护策略同样值得配置。

#### 如何执行

1. 托管版 Code Review 服务是最快的起步方式。管理员启用它并选择仓库。当你需要掌控流水线，或希望 API 调用经由自己的云合约路由时，就用 claude-code-action 在自己的 CI 中运行评审（CI/CD 战术会讲到这套管道）。
2. 技术负责人把评审政策写成仓库根目录下的 `REVIEW.md`，按组织关心的几类流程划分：bug 与逻辑错误；安全与漏洞；对规格（需求战术产出的 `spec.md`）、实现计划（plan mode 战术产出的 `plan.md`）与设计原则的合规性。`REVIEW.md` 还要定义什么算「Important」而什么只是「Nit」，以及哪些内容应当跳过。
3. 技术负责人设定人工介入的阈值。发现项本身既不批准也不阻断 PR，分支保护仍然要求代码负责人的批准。想要以发现项为合并门禁的平台工程师，可以读取检查运行所发布的、机器可读的严重程度计数。
4. 当评审者或作者在某条评审意见中 @ 了 `@claude` 时，Claude 会处理这条意见并推送修复。PR 讨论串同时记录了请求与改动。这个修复闭环通过 claude-code-action 运行。在托管服务中，评论 `@claude review` 则是请求一次全新的评审。对于 Claude 自己开的 PR，还可以更进一步，让 Claude 一路盯着 PR 直到合并。有些团队把这个闭环包装成一个自定义 slash command：扫过 PR 上未解决的评审意见与失败的检查项，逐一处理并推送修复，直到 PR 全绿、只等代码负责人批准为止。
5. 评审发现会反馈回 `CLAUDE.md`。当一次评审第二次标记出同一个错误时，纠正内容就作为该次评审的一部分写进 `CLAUDE.md`；又因为评审本身会读取 `CLAUDE.md`，这个错误从下一个 PR 起就会被拦住。评审还会指出某次变更是否让 `CLAUDE.md` 变得过时。
6. 每月一次，技术负责人通过给发现项打分来调校这套机制，让评审者不断改进，并在 `REVIEW.md` 中限制 Nit 的数量上限。生成类路径以及 CI 已经强制执行的内容都被排除在外。

#### 实际样例（REVIEW.md）

```
# Review instructions

## Passes
Run three passes and tag each finding with its pass:
- Bugs: logic errors, broken edge cases, subtle regressions
- Security: injection risks, authentication gaps, PII in logs
- Compliance: the change matches spec.md, plan.md and our design principles

## What Important means here
Reserve Important for findings that would break behavior, leak data
or breach a policy. Style and naming are nits.

## Cap the nits
Report at most five nits per review; summarize the rest as a count.

## Do not report
Generated files under src/gen/ and anything CI already enforces.
```

#### 治理考量

职责分离得以保持，因为写出这段代码的智能体没有任何途径去批准它。`REVIEW.md` 中的评审政策被应用于所有 PR，而发现项、修复、评分与批准都记录在 PR 历史中——因此 PR 本身就是审计记录。批准来自人类，经由分支保护给出，并以那些发现项作为判断依据。

关于这些管控手段在生产规模下如何组合，参见[Anthropic 如何保障其 AI 原生软件开发生命周期的安全](https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle)。

如何衡量

**先行指标**

首次评审所需时间（应当下降到以分钟计），以及无需人类碰触分支即被解决的评审意见占比——数据直接存放在 Git 上。

**滞后指标**

合并前被抓住的缺陷与漏洞数量，与逃逸到生产环境的数量作对比，数据来自 PR 历史与事故追踪系统。

### 把 hook 当作审批门禁

构建阶段把 hook 用作护栏，在无人介入的情况下放行或拦截动作（阶段 3：构建）。hook 也可以「发问」——暂停动作直到某位特定人员批准，而这正是发布门禁所需要的。

这个战术被放在阶段 5：部署，是因为发布门禁是最清晰的用例，但 hook 并不专属于部署环节：Claude 在哪里行动，它就在哪里运行。举例来说，hook 可以在阶段 3：构建期间拦截没有变更工单支撑的迁移脚本与基础设施编辑，也可以在阶段 4：测试的修复任务中阻止智能体编辑测试文件。

如何起步

**前置条件**

无。

**基础设施**

一份成文清单，列出变更流程所要求的各项审批。

#### 如何执行

1. 工程领导层会同变更管理与合规部门，列出必须保留的人工审批门禁，例如变更管理签核、发布授权，以及对受保护路径的编辑。
2. 平台工程师把每道门禁表达为一个 hook——一个在 Claude 行动之前运行的脚本，可以放行（allow）、发问（ask）或拦截（block）。
3. 团队级 hook 放进 git 中的 `.claude/settings.json`，而不可协商的 hook 放进由平台或 IT 管理员掌管的 managed settings 中，个别工程师无法关闭它们。
4. 拦截应当自我解释：当某个 hook 阻止了一个动作时，原因与获取审批的途径都应出现在 Claude 的输出中。

#### 实际样例（.claude/settings.json）

```
{
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [
            { "type": "command",
              "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/production-gate.sh" }
          ]
        }
      ]
    }
}
```

#### 以及门禁本身（.claude/hooks/production-gate.sh）

```
#!/bin/bash
# Production deploys require a named release authorization
cmd=$(jq -r '.tool_input.command' < /dev/stdin)
if [[ "$cmd" == *"deploy"* && "$cmd" == *"production"* ]]; then
   if [ -z "$RELEASE_APPROVAL" ]; then
     echo "Production deploys need a release authorization." >&2
     exit 2 # exit 2 blocks the action; the message goes to Claude
   fi
fi
exit 0
```

#### 治理考量

hook 就是审批门禁。门禁条件每一次、对每一个人都被强制执行。放行与拦截的决策连同时间戳一并记录。门禁同时也定义了什么才算「批准」——无论那是一张已批准的变更工单，还是发布经理的签核。

实战范例

### 受监管企业的 managed settings

*由平台团队通过 MDM 或管理控制台下发；工程师无法编辑或覆盖其中任何一项。*

```json
{
  "permissions": {
    "deny": [
      "Read(.env*)", "Read(./secrets/**)",
      "WebFetch", "Bash(curl *)", "Bash(wget *)"
    ],
    "allow": [
      "Bash(git *)", "Bash(make build)",
      "Bash(make test)", "Bash(make lint)"
    ],
    "disableBypassPermissionsMode": "disable"
  },
  "allowManagedPermissionRulesOnly": true,
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "allowUnsandboxedCommands": false,
    "network": { "allowedDomains": ["git.internal.example.com",
      "registry.npmjs.org"] },
    "credentials": {
      "files": [
        { "path": "~/.ssh", "mode": "deny" },
        { "path": "~/.aws/credentials", "mode": "deny" }
      ],
      "envVars": [ { "name": "GITHUB_TOKEN", "mode": "deny" } ]
    }
  },
  "allowManagedHooksOnly": true,
  "disableSideloadFlags": true,
  "allowManagedMcpServersOnly": true,
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "example-corp/approved-plugins" }
  ],
  "requiredMinimumVersion": "2.1.193"
}
```

从管控角度看，每一行分别买到了什么

`permissions.deny` 让机密不进入智能体的上下文，并阻断通过工具发起的任意网络外联；`permissions.allow` 则预先批准安全的内层循环，使得拒绝列表不至于演变成审批疲劳。

`disableBypassPermissionsMode` 加上 `allowManagedPermissionRulesOnly`，意味着任何工程师、项目文件或命令行参数都无法放宽这些规则。

`sandbox` 补上了权限机制无法覆盖的缺口。在工具层面禁用 WebFetch，并不能阻止一条 shell 命令触达网络；而操作系统层面的域名白名单会直接阻断外联。

`failIfUnavailable` 与 `allowUnsandboxedCommands` 让沙箱成为一道门禁：当沙箱无法初始化时 Claude Code 拒绝启动，而在沙箱内失败的命令也无法拿到沙箱外重试。

`credentials` 补上了拒绝规则留下的缺口。`permissions.deny` 管的是 Claude 的文件工具，但一条沙箱化的 shell 命令在默认情况下仍能读取 `~/.ssh` 或 `~/.aws/credentials`；这个配置块拒绝了这些读取，并从每一条沙箱化命令的环境变量中剥离所列的机密。

`allowManagedHooksOnly` 意味着本战术中的审批门禁是唯一会运行的 hook；任何本地配置都无法追加或替换它们。

`disableSideloadFlags` 与 `strictKnownMarketplaces` 意味着工程师机器上的每一个 skill、agent、hook 与 MCP server，都来自组织批准的 plugin marketplace，绝不会来自某个家目录。

`allowManagedMcpServersOnly` 让智能体的工具面变成一份由平台团队掌管的白名单。

`requiredMinimumVersion` 会拒绝在低于批准下限的版本上启动，从而确保这些管控由一个组织确实评估过的构建版本来执行。

请把上述内容视为一个需要因地制宜调整的起点，而非照抄的建议。每一条拒绝规则都是以能力为代价换来的，而恰当的平衡点取决于该仓库的数据分级。settings 参考文档记录了每一个配置键，包括那些仅限 managed 使用的：[code.claude.com/docs/en/settings](https://code.claude.com/docs/en/settings)

如何衡量（针对 hook 本身）

**先行指标**

在每道审批门禁上等待所花费的时间。每一次 hook 决策都会连同时间戳与放行/拦截的结论写入 OpenTelemetry 导出数据，因此每道门禁的等待时长都是可见的。

**滞后指标**

引入 hook 前后，突破门禁并抵达生产环境的违规数量，数据来自事故追踪系统。

### CI/CD 集成与部署

在 CI/CD 流水线内部非交互式运行 Claude Code，对执行过程做沙箱化以保证长时间运行的智能体安全无虞，通过 MCP 集成暴露部署能力，并在智能体真正需要之前先演练好回滚路径。

**传统方式**：流水线运行确定性脚本，任何需要判断力的事情都要等人。比如给不稳定的测试定性、撰写变更日志，或者搞清楚构建为什么坏了。部署与回滚是人在压力之下照着执行的操作手册。

**AI 原生方式**：Claude 在流水线内部非交互式运行，负责那些需要判断力的步骤，运行在一个凭据范围受限的沙箱中。部署工具通过 MCP 暴露给智能体，因此那个写出并测试了变更的工作流，也能把它发布出去并回滚——全部发生在组织按环境定义的门禁之内。

如何起步

**前置条件**

Claude 已进入 PR 评审闭环，且 hook 已作为审批门禁就位——因为门禁必须先存在，自动化才能加速任何东西通过它们。

**基础设施**

一个安装了 claude-code-action 的 CI 平台，或任何能调用 `claude -p` 的 runner；通过 API 获得模型访问权限，或在流量必须留在组织云合约之内时，通过 Bedrock、Foundry 或 Vertex 获得；面向各部署目标的 MCP server；以及一份用于智能体任务的沙箱配置，其中不常驻任何生产凭据。

#### 如何执行

1. 平台工程师从只读的判断类步骤起步。在流水线任务中用 `claude -p` 给失败的构建定性、总结一个不稳定的测试，或起草变更日志。
2. 在已有门禁之后加入写入类步骤，用于修复 lint、更新生成的文档，或通过 `@claude` 提及来处理评审意见这类工作。智能体写出的任何东西都以 PR 形式经由分支保护进入，智能体没有任何途径直接推送到 main。
3. 执行过程是沙箱化的。智能体任务运行在受网络策略约束的容器中，使用短期的、范围受限的令牌，默认不持有任何生产凭据。
4. 通过 MCP 暴露部署能力。部署、状态查询与回滚都变成工具，按环境限定范围，因此智能体的部署权限是一份白名单，而不是一个带着凭据的 shell 脚本。
5. 按环境划分自主权层级。在开发环境中，智能体可以自由部署。在生产环境中，智能体准备好发布，由发布经理授权，并由一个 hook 强制执行生产门禁。预发布环境则处在两者之间。
6. 回滚应当是整条流水线中演练得最充分的路径——一条智能体可以运行的单一命令，并在预发布环境中定期被演练。闭合闭环战术（阶段 6：维护）会在某条管控阈值带被突破时调用这个回滚，因此它必须事先被证明是可靠的。

#### 实际样例（流水线步骤）

```
- name: Triage failed build
  if: failure()
  run: >
    claude -p "Read the build log at out/build.log. Identify the most
    likely cause, say whether the failure looks flaky or real, and write a
    three-line summary for the PR thread." >> triage.md
```

#### 治理考量

统领性原则是：智能体可以行动到生产门禁为止，且无法越过它。下面这些管控手段落实了这一原则。

* 分支保护把智能体写出的任何东西都变成 PR，没有直通 main 的路径。
* 生产部署 hook 会阻断发布，直到某位具名的发布经理授权为止。每次非交互式运行都以智能体自身的身份进行，因此流水线日志能把智能体做了什么与触发它的工程师做了什么区分开来。
* 按环境划分的权限层级，决定了智能体在通往门禁的路上被允许做多少事。

如何衡量

**先行指标**

无需呼叫人工即被定性的流水线失败占比，数据取自 CI/CD 流水线日志。

**滞后指标**

DevOps Research and Assessment（DORA）指标——CI 系统与部署工具本来就会产出这些数据。

**06**

## 维护

闭环就此闭合。一个触发器在调用路径上没有任何人的情况下唤起 Claude，而它的发现以 `intent.md` 的形式重新进入流水线。

### 维护与闭合闭环

到目前为止，我们讨论的是如何把 Claude 加入 SDLC 流程的各个阶段，而每个阶段都需要一个人来启动最初的步骤。然而本阶段把重心转向了让 Claude 自主运行，从而闭合闭环。

举例来说，一个持续运行的监控智能体可以在一张 bug 工单被提出之后，创建一份 `intent.md`，并一路流经需求、计划、构建、测试与评审各个阶段。阶段 6：维护以无头（headless）方式运行，各阶段之间设有独立的置信度门禁——可以是一项确定性检查，也可以是一个对抗性评审智能体——由它决定上一阶段的产出是继续推进，还是升级给人处理。

**传统方式**：维护是一个被动响应的阶段。所有工单或事故都在等某个人去处理它、重新启动流程。凌晨三点触发的告警可能被漏掉，一张工单可能一直躺在待办里直到有人捡起它，而如果另一场火先烧起来，事后复盘的行动项可能根本就没有落到代码库里。

**AI 原生方式**：诸如管控阈值带被突破、一张工单、一条频道消息或一个定时计划这样的触发器，在路径上没有任何人的情况下唤起 Claude。Claude 做出诊断，只通过受门禁约束的路径行动，并把它的发现写成 `intent.md`，随后走完上文描述的各个阶段。人负责分流与评审这些工作，而不再需要去启动它。

### 闭合闭环

一个确定性脚本盯着生产环境，在某条管控阈值带被突破时唤起 Claude。对阈值突破的监控是「闭环自主运行」这一模式的一个好例子，而本阶段末尾的 [Claude Tag](https://claude.com/product/tag)（公开 beta）一节则涵盖了工作通过不同渠道抵达的情形。

如何起步

**前置条件**

`Intent.md`——它为闭环提供了一个结构化产出以重新启动流程。以及由 Claude 加速的 PR 评审、作为动作边界的 hook，还有 CI/CD 的回滚路径（最高自主权层级会调用它）。

**基础设施**

一个检测脚本可以查询的指标存储（Prometheus、CI 系统的 API 或同类产品）、对仓库的读取权限、一种在 CI 中非交互式运行 Claude Code 的方式，或者用 [Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) 搭建一个接收 webhook 的服务。

#### 如何执行

1. 服务负责人或平台工程师挑选一个具有稳定滚动基线的指标，例如 CI 测试失败率、部署后 5xx 比率，或 PR 周期时长。
2. 他们编写检测脚本，通常是在滚动窗口上计算均值与标准差，并配合规则（Western Electric 或类似规则），让阈值带既能捕捉突刺，也能捕捉缓慢漂移。该脚本受版本控制并有单元测试，检测过程完全保持确定性，不涉及任何模型。
3. 响应层级定义在受版本控制的配置中（即下文的 `bands.yaml`）。在 1σ 时脚本仅记录日志，在 2σ 时它以只读方式唤起 Claude 做诊断，在 3σ 时 Claude 可以采取行动——但只能通过向评审门禁提交 PR，或触发一个预先批准的操作手册。
4. 触发层可以是 GitHub 或 GitLab 中的定时工作流、来自既有监控栈的 webhook，或网络内部的一个 Cron Job。Claude 无状态运行，既可以作为 CI runner 上的一个非交互式步骤，也可以作为沙箱容器中的一个 Agent SDK 服务，CI/CD 战术涵盖了部署与模型访问的各种选项。正因为这次运行是无状态且非交互式的，一个闭环可以在无人启动的情况下开始并结束。
5. 智能体把它的诊断以阶段 1：规划的格式写成 `intent.md`，涵盖该异常及其证据、一个期望结果、受影响的系统，以及任何开放性问题。从那里开始，这项发现就像其他任何事项一样走完整条流水线。
6. 服务负责人或值守工程师对队列做分流，把面向产品的发现路由给产品负责人。要么立刻修、要么排期、要么驳回。驳回会用来调校阈值带，有助于降低噪音。
7. 当修复上线时，为该事故补上一条评估（见持续评估战术），以确保此类问题在未来得到防护。

#### 实际样例（例如一份监控 CI 测试失败率的 bands.yaml）

```
metric: ci_test_failure_rate
baseline: rolling_30d
rules: western_electric
tiers:
  1sigma: { action: log }
  2sigma: { action: diagnose,
            tools: "Read,Grep,Bash(gh run view *)" }
  3sigma: { action: propose,
            routes: [pull_request, runbook:rollback-deploy] }
```

#### 治理考量

各层级的边界由受版本控制的配置强制执行，同时权限设置与 managed settings 拒绝生产环境访问。唤起、发现与分流决策都连同时间戳一并记录。由服务负责人分流并批准发现项，由此产生的变更走正常的 PR 评审门禁，而智能体可以触发的那些操作手册都是事先批准过的。

如何衡量

**先行指标**

从阈值带被突破，到一份 `intent.md` 出现在分流队列中所需的时间，与旧有的「从事故到复盘行动项」的时长作对比。检测脚本的日志中记录了突破的时间戳与事故层级。

**滞后指标**

最终变成已合并修复的发现项占比（分流队列对照实际 PR 历史），以及同一类别的重复事故数量——随着修复不断为评估集补充用例，这个数字应当下降。

#### 示例

* 当 CI 测试失败率突破 3σ 时，智能体隔离掉那个不稳定的测试或提交一个 revert PR，由评审门禁作出裁决。
* 当部署后 5xx 比率突破 3σ 且时间窗内存在一次部署时，智能体触发既有的回滚流水线。
* 当 PR 周期时长触发漂移规则时，智能体为工程领导层撰写一份报告——这说明这套工具链不仅适用于生产指标，也适用于流程指标。

检测始终保持确定性。Claude 只在某条阈值带被突破之后才被唤起，而层级决定了它可以做什么。

### 周期性代码库扫描

一次安全扫描，是在某个特定模型之下对某个代码库做出的一份时间点声明，而这两半都会过期：代码每周都在变，而每一代模型都会找出上一代漏掉的漏洞。AI 原生的答案是按计划运行扫描、调用路径上不设人，并让它的发现走与代码库其他任何变更相同的门禁。

[Claude Security](https://claude.com/product/claude-security) 是定时扫描的托管形态。连接一个 GitHub 仓库，扫描就会在 Anthropic 的基础设施上基于 Claude Mythos 5 运行，每一项发现在被报告之前都经过验证，并附带一个置信度评级。建议的补丁在 Claude Code on the web 中被评审并应用。组织无需拥有模型本身的访问权限即可获得这些发现。

**传统方式**：安全扫描是一个事件——在发布或审计之前发起一次扫描。报告进入追踪系统，积压项被人工逐条清理，直到下一次事件到来。期间写下的代码，能覆盖多少全看 PR 评审抓住了什么。

**AI 原生方式**：扫描按计划针对每个已连接的仓库运行，使用当前可用的最强模型，且发现项在任何人阅读之前就已通过验证。每一项发现的处理方式与被突破的管控阈值带相同：能装进一个 PR 的修复走评审门禁，更大的则变成一份 `intent.md`。覆盖度的时间基准是最近一次运行，而不是第一次运行。

如何起步

**前置条件**

PR 评审门禁与作为审批门禁的 hook（[阶段 5：部署](#sd-s5)），使发现项像其他任何变更一样走评审。对于单个 PR 装不下的发现，还需要[阶段 1：规划](#sd-s1)中的 `intent.md` 格式。

**基础设施**

Claude Security 以公开 beta 形式向 Claude Enterprise 组织开放。它需要在目标仓库（云托管的 github.com）上安装 Anthropic GitHub App、启用 Claude Code on the Web、开启 Extra Usage 并设定支出上限、为执行扫描的人员配备 premium 席位，以及由管理员在 `claude.ai/admin-settings/claude-code` 中打开该功能。扫描按 Mythos 5 费率按用量计费，因此支出上限应当与仓库的规模和数量相匹配。

#### 如何执行

1. 安全负责人连接各仓库，并按仓库、服务或团队把它们组织成项目，使发现项的归属从一开始就清晰。
2. 对最关键的仓库先跑一次完整扫描，包括那些曾被其他工具或更早的模型扫描过的仓库。把第一次扫描当作基线。第一次扫描很可能会在被认为干净的代码中翻出问题。
3. 为每个项目设定计划。对于活跃开发中的服务，每周一次是合理的默认值；当某个仓库很大或内容混杂时，把扫描范围限定到某个目录或分支。
4. 带着置信度评级去分流发现项。驳回时给出理由，这样驳回本身会被记录，同一项发现在下次运行时也不会作为新问题再度出现。
5. 对于范围明确的发现，在 Claude Code on the Web 中打开建议补丁，评审它，然后像其他任何变更一样送入 PR 评审门禁。提出该修复的智能体没有任何途径去批准它。
6. 对于超出单个补丁范围的任何问题——比如架构层面的弱点，或跨多个服务重复出现的模式——按阶段 1 的格式把它写成 `intent.md`，从规划阶段起步。
7. 当某个修复发布到生产环境时，为该漏洞类别向持续评估战术中的测试集补上一条评估，使得从此以后，驾驭智能体的那些配置都会针对该类别接受测试。
8. 把发现项导出为 CSV 或 Markdown，或者使用 webhook，让组织既有的追踪与审计系统继续充当记录系统——审计师本来就期望在那里找到它们。

#### 治理考量

扫描运行在组织的管理控制之下，也就是说：连接了哪些仓库、谁持有扫描席位、支出上限是多少，全都由中心统一设定。每一项发现都有验证结果与置信度评级，每一次驳回都有理由，因此扫描历史就是一份审计记录，记载了发现了什么、修复了什么，以及有意识地接受了什么。

修复通过 PR 评审门禁与分支保护抵达生产环境，而不是直接来自扫描本身。Claude Security 是对既有静态分析与依赖扫描的增强。确定性检查仍留在 CI 中，而模型驱动的扫描负责覆盖那些检查在设计上就找不到的、依赖上下文的漏洞。

如何衡量

**先行指标**

已纳入定时计划的已连接仓库占比，以及从一项发现被报告到其补丁进入 PR 评审门禁所需的时间——分别从扫描历史与 PR 元数据中读取。

**滞后指标**

定时扫描发现的漏洞数量，与在生产环境中发现或由外部报告的漏洞数量作对比（数据来自事故追踪系统）；以及在已经历多轮扫描的仓库上，每次扫描的发现数趋势——随着修复与评估不断累积，它应当下降。

### 用 Claude Tag 让 Claude 值守

事故也可能通过其他途径抵达，比如 Slack 或 Teams 这类办公沟通应用。事故可能表现为晚上十点在事故频道里发来的一条要求紧急修复的 Slack 消息，而现在它可以被立即着手处理。Claude Tag（公开 beta，目前在 Slack 中可用）让 Claude 以自身身份成为这些频道的一员，因此每起新事故都能得到一位第一响应者，而响应过程本身也成为闭环的一部分，以及未来事故可资参考的记忆。

对话与机构知识都留在频道里，频道中的任何人都可以引导并推动响应。任何团队成员都能实时验证假设、探索新方案、展开调查，而频道历史进一步增强了可审计性。通过 MCP 的访问能力，Claude 验证指标已回到基线并在讨论串中予以确认，还会把事后复盘写入一个受版本控制的经验教训文件，供未来的调查阅读。

事故并不是 Claude Tag 承接的唯一工作。无论是通过 MCP 在一张工单上被 @，还是在频道里被问到，Claude 都以同样的方式对工作做分流。一个小而边界清晰的修复以 PR 形式经由评审门禁抵达，而更大的事项则被写成 `intent.md` 送入阶段 1：规划——至此闭环开始自我喂养。参见：[Claude Tag 如何在 Anthropic 为 CI/CD 值守](https://claude.com/blog/ai-ci-cd-on-call)。

![Claude Tag 在事故频道中响应](../assets/sdlc-fe6d780d.png)

频道就是审计轨迹：请求、诊断、人工授权与修复，全都留在事故被处理的那个地方。

## 结语

模型与工具链都变得更先进了，这让各类组织不仅能改造自己生产代码的方式，还能改造整个软件开发生命周期。

这场转型让人的判断力始终居于流程的核心，并顾及了大型企业组织在治理与监管方面的要求。

本指南汇总了我们 Applied AI 团队日常为客户执行的诸多真实最佳实践，希望你觉得它是一份务实且可付诸行动的资料。

闭环持续运转。人的判断力始终在它之上。

### 资源与致谢

以下文档是平台团队搭建那些管控手段所需要的，大致按你会推行它们的顺序排列。

- [为你的组织配置 Claude Code —— 管理员决策地图，从这里开始](https://code.claude.com/docs/en/admin-setup)（code.claude.com/docs/en/admin-setup）
- [Settings 参考与优先级，含每一个仅限 managed 使用的配置键](https://code.claude.com/docs/en/settings)（code.claude.com/docs/en/settings）
- [来自 Claude 管理控制台的服务端托管设置](https://code.claude.com/docs/en/server-managed-settings)（code.claude.com/docs/en/server-managed-settings）
- [权限](https://code.claude.com/docs/en/permissions)（code.claude.com/docs/en/permissions）
- [沙箱化 —— 操作系统层面的文件系统与网络隔离](https://code.claude.com/docs/en/sandboxing)（code.claude.com/docs/en/sandboxing）
- [Hooks —— 指南](https://code.claude.com/docs/en/hooks-guide)（code.claude.com/docs/en/hooks-guide）
- [Hooks —— 参考](https://code.claude.com/docs/en/hooks)（code.claude.com/docs/en/hooks）
- [Skills](https://code.claude.com/docs/en/skills)（code.claude.com/docs/en/skills）
- [Plugin 与私有 marketplace —— skill 与 hook 如何在全组织范围内分发](https://code.claude.com/docs/en/plugin-marketplaces)（code.claude.com/docs/en/plugin-marketplaces）
- [Managed MCP —— 对智能体工具面的集中管控](https://code.claude.com/docs/en/managed-mcp)（code.claude.com/docs/en/managed-mcp）
- [企业部署概览 —— Bedrock、Vertex、Foundry](https://code.claude.com/docs/en/third-party-integrations)（code.claude.com/docs/en/third-party-integrations）
- [企业网络配置](https://code.claude.com/docs/en/network-config)（code.claude.com/docs/en/network-config）
- [监控（OpenTelemetry）](https://code.claude.com/docs/en/monitoring-usage)（code.claude.com/docs/en/monitoring-usage）
- [分析看板](https://code.claude.com/docs/en/analytics)（code.claude.com/docs/en/analytics）
- [Compliance API —— 企业版活动流、聊天检索与删除](https://platform.claude.com/docs/en/manage-claude/compliance-api)（platform.claude.com/docs/en/manage-claude/compliance-api）
- [安全模型](https://code.claude.com/docs/en/security)（code.claude.com/docs/en/security）

感谢 Jim Blackhurst、Will Steuk 与 Jamal Arif 对本指南的贡献，本文正是受他们此前诸多工作的启发并在其基础上写成。
