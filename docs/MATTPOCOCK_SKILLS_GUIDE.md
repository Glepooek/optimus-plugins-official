# Mattpocock Skills 使用场景指南

本文档覆盖 `mattpocock-skills` 插件（作者 [Matt Pocock](https://www.aihero.dev)，Claude Code 官方 marketplace 收录，版本 1.2.3）中 Engineering + Productivity 两大域共 24 个 skill 的触发时机、核心规则和典型场景。Misc / In-progress / Deprecated 三个非主线分类只做简要说明。

**调用格式：** 该插件内部 SKILL.md 相互引用时均使用无前缀形式，例如 `/grill-me`、`/to-spec`、`/ask-matt`。若命名与其他已安装插件冲突，可用完整命名空间 `/mattpocock-skills:<skill-name>`。

**这份插件与 superpowers 的关键差异：** superpowers 把流程刻成一条主链路（brainstorming → writing-plans → executing-plans → ...），几乎所有 skill 都是这条链上的一站；mattpocock-skills 是一张**路由图**——`ask-matt` 是路口，`CONTEXT.md`/ADR 是贯穿全程的共享语言层，`grilling`（相当于一个"访谈原语"）被 5 个不同 skill 复用。理解这张图，比记住 24 个 skill 各自的用法更重要。

---

## 目录

- [调用轴线：user-invoked 与 model-invoked](#调用轴线user-invoked-与-model-invoked)
- [技能全景图](#技能全景图)
- [前置条件](#前置条件)
  - [setup-matt-pocock-skills](#setup-matt-pocock-skills)
  - [ask-matt](#ask-matt)
- [一、Engineering 域：主流程](#一engineering-域主流程)
  - [grill-with-docs / grilling](#grill-with-docs--grilling)
  - [to-spec](#to-spec)
  - [to-tickets](#to-tickets)
  - [implement](#implement)
  - [tdd](#tdd)
  - [code-review](#code-review)
- [二、Engineering 域：On-ramp（问题接入口）](#二engineering-域on-ramp问题接入口)
  - [triage](#triage)
  - [diagnosing-bugs](#diagnosing-bugs)
  - [wayfinder](#wayfinder)
- [三、Engineering 域：代码库健康与词汇层](#三engineering-域代码库健康与词汇层)
  - [improve-codebase-architecture](#improve-codebase-architecture)
  - [domain-modeling](#domain-modeling)
  - [codebase-design](#codebase-design)
- [四、Engineering 域：独立工具](#四engineering-域独立工具)
  - [prototype](#prototype)
  - [research](#research)
  - [resolving-merge-conflicts](#resolving-merge-conflicts)
  - [wizard](#wizard)
- [五、Productivity 域](#五productivity-域)
  - [grill-me](#grill-me)
  - [handoff](#handoff)
  - [teach](#teach)
  - [to-questionnaire](#to-questionnaire)
  - [wait-what](#wait-what)
  - [writing-for-agents](#writing-for-agents)
- [六、Misc / In-progress / Deprecated](#六misc--in-progress--deprecated)
- [标准工作流链路](#标准工作流链路)

---

## 调用轴线：user-invoked 与 model-invoked

这是理解本插件的第一个关键概念，也是它与 superpowers 最大的结构差异。每个 skill 的 frontmatter 里都标了 `disable-model-invocation: true`（Codex 对应 `policy.allow_implicit_invocation: false`），据此分成两类：

| 轴线 | 谁能触发 | 职责 | 举例 |
| :--- | :--- | :--- | :--- |
| **User-invoked** | 只有你主动输入 `/skill-name` 才会触发 | **编排**——组织流程，调用其他 skill | `ask-matt`、`grill-with-docs`、`to-spec`、`triage`、`wayfinder` |
| **Model-invoked** | 你输入，或模型在任务匹配时自动调用 | **持有可复用的纪律**——具体怎么做 | `tdd`、`diagnosing-bugs`、`domain-modeling`、`codebase-design`、`prototype`、`research` |

一条硬规则：**user-invoked skill 可以调用 model-invoked skill，但绝不会调用另一个 user-invoked skill。** 例如 `triage` 内部会跑 `/grilling` 和 `/domain-modeling`（两个都是 model-invoked），但它不会去调用 `/to-spec`（user-invoked）——那种跨主线跳转必须由你手动决定。

★ Insight ─────────────────────────────────────
这个设计解决的问题是"模型该不该自己决定切换大流程"。像 `implement`、`tdd` 这类只管"怎么把一件已经定义清楚的事做对"的技巧，交给模型自动触发很安全——它们不会改变你的项目走向。但像 `to-spec`、`triage`、`wayfinder` 这类会创建工单、切分任务、改变你接下来要做什么的编排型 skill，一旦允许模型自动触发，就可能在你没意识到的情况下把对话岔到另一条主线上。所以插件作者用 frontmatter 的 `disable-model-invocation` 把"决定权"和"执行力"分开授权。
─────────────────────────────────────────────────

## 技能全景图

```
                          ┌─────────────┐
                          │  ask-matt   │  ← 路由：不确定用哪个 skill 时先问它
                          └──────┬──────┘
                                 │
   ┌─────────────────────────── main flow: idea → ship ───────────────────────────┐
   │                                                                              │
   │  grill-with-docs ──► [需要跑得起来的答案?] ──► handoff → prototype → handoff  │
   │       │                                                                     │
   │       ▼                                                                     │
   │  [多会话构建?] ──yes──► to-spec → to-tickets(阻塞边) → implement(每票 /clear) │
   │       │                                                     │               │
   │       no                                              内部驱动 tdd          │
   │       │                                                     │               │
   │       └──────────────────────► implement ◄──────────────────┘               │
   │                                     │                                       │
   │                                     ▼                                       │
   │                              code-review → commit                           │
   └──────────────────────────────────────────────────────────────────────────────┘
                                 ▲
        on-ramps（问题接入口，最终汇入 main flow）
                                 │
   ┌─────────────┬──────────────┼──────────────┬──────────────┐
   │  triage     │ diagnosing-bugs │  wayfinder（雾太大才用）    │
   │ (issue 堆积) │  (线上/线下 bug) │ (greenfield/超大功能)      │
   └─────────────┴──────────────┴──────────────┴──────────────┘

        贯穿全程的词汇层（model-invoked，被上面所有 skill 引用）
   ┌─────────────────────┬─────────────────────────────────────┐
   │  domain-modeling     │  codebase-design                    │
   │  CONTEXT.md / ADR     │  module/interface/depth/seam/adapter │
   └─────────────────────┴─────────────────────────────────────┘

        代码库健康（不是功能开发，是维护）
                    improve-codebase-architecture
                         （产出 idea → 回到 grill-with-docs）
```

**每个阶段都有专属 skill，但边界比 superpowers 更松**——`ask-matt` 明确说"这是一张路由图，不是一条流水线"：小任务可以跳过 `to-spec`/`to-tickets` 直接 `implement`；不在工作目录里就用 `grill-me` 代替 `grill-with-docs`；已经在冲突中间才会碰到 `resolving-merge-conflicts`。判断走哪条路，是 `ask-matt` 存在的意义。

---

## 前置条件

### setup-matt-pocock-skills

**触发时机：** 每个仓库第一次使用本插件任何 engineering skill 之前，只跑一次。

**核心规则：** 这是一个**提示驱动型 skill，不是确定性脚本**——先探索仓库现状，展示发现，与用户确认，再写入。它配置三件事，供其余 engineering skill 读取：

| 配置项 | 写入位置 | 决定了什么 |
| :--- | :--- | :--- |
| Issue tracker | `docs/agents/issue-tracker.md` | `to-tickets`/`triage`/`to-spec` 用 `gh issue create` 还是写本地 `.scratch/` 文件 |
| Triage 标签 | `docs/agents/triage-labels.md` | `triage` 用什么标签字符串对应五个规范角色（仅当 `triage` skill 已安装才问） |
| 域文档布局 | `docs/agents/domain.md` | 单一上下文（根目录一份 `CONTEXT.md`）还是多上下文（`CONTEXT-MAP.md` + 每上下文一份） |

**探索清单：** `git remote -v`、`AGENTS.md`/`CLAUDE.md` 是否已有 `## Agent skills` 块、`CONTEXT.md`/`CONTEXT-MAP.md`、`docs/adr/`、`.scratch/`、`triage` skill 是否安装、monorepo 信号（`pnpm-workspace.yaml` 等）。

**写入规则：** 若 `CLAUDE.md` 已存在就编辑它，否则编辑 `AGENTS.md`；两者都没有则询问用户创建哪个——绝不会同时创建两个文件。已有 `## Agent skills` 块时原地更新，不追加重复块。

**典型场景：**

```
用户：/setup-matt-pocock-skills

流程：
  → 探索：发现 git remote 指向 GitHub，没有 CONTEXT.md，没装 triage skill
  → Section A：推荐 GitHub issue tracker，用户确认
  → Section B：跳过（triage 未安装）
  → Section C：单一上下文，无需询问，直接采用
  → 展示 CLAUDE.md 的 ## Agent skills 草稿 + docs/agents/issue-tracker.md 草稿
  → 用户确认后写入
```

### ask-matt

**触发时机：** 不确定该用哪个 skill、或想知道当前情况该走哪条流程时。

**核心规则：** `ask-matt` 是**路由器**，不做任何实质工作——它只回答"接下来该跑哪个 skill"。它把整套 skill 组织成一条主流程（idea → ship）+ 若干 on-ramp（问题接入口）+ 代码库健康维护 + 词汇层 + 完全独立的工具。

**判断你在主流程还是该走 on-ramp 的三个问题：**

1. **有没有工作目录？** 没有 → `grill-me`（无状态）；有 → `grill-with-docs`（有状态，写 `CONTEXT.md`/ADR）。
2. **这是多会话构建吗？** 是 → `to-spec` → `to-tickets` → 逐票 `implement`；不是 → 直接 `implement`。
3. **这是接入口还是从零开始？** issue/PR 堆积 → `triage`；有 bug/性能问题 → `diagnosing-bugs`；一个大到装不进一次会话的模糊想法 → `wayfinder`。

**上下文卫生（Context hygiene）：** 步骤 1–3（grilling → spec → tickets）要留在**同一个未间断的上下文窗口**里——不要在 `to-tickets` 完成前 `/compact` 或 `/clear`，让访谈、spec、票据的思考建立在同一条推理链上。限制是**智能区（smart zone）**：前沿模型上大约 150k token，超出这个窗口模型推理会开始变钝。接近这个阈值时不要硬撑，在最近的阶段边界 `/compact` 再继续。

**阶段边界的五个选项（哪个都不是默认"继续"）：**

| 选项 | 何时用 | 代价 |
| :--- | :--- | :--- |
| **Continue** | 下一步仍需要这里的一切 | 零成本，零损失 |
| **`/clear`** | 接下来的工作跟这里无关 | 清空窗口 |
| **`/handoff`** | 换 harness / 换目录 / 交给同事 / 中途分叉出一个旁支任务 | 写一份可移植的 Markdown |
| **子智能体** | 一个范围明确的任务，只要结果不要过程 | 拿到一份报告 |
| **`/compact`** | 默认选项——压缩当前上下文，接着干 | 压缩成本，但保留连续性 |

**典型场景：**

```
用户：/ask-matt 我想给订单系统加退款功能，这个仓库我从没碰过

ask-matt 判断：
  → 有工作目录 → 用 grill-with-docs（不是 grill-me）
  → 退款涉及模块设计、审批流，值得先跑一轮域建模 → grill-with-docs 内部会带 domain-modeling
  → 如果访谈发现这是个跨多会话的大功能 → 建议 to-spec → to-tickets
  → 如果访谈后发现范围很小 → 建议直接 implement
```

---

## 一、Engineering 域：主流程

### grill-with-docs / grilling

**触发时机：** 有工作目录、想推进一个新想法/功能，且值得把结论沉淀成文档（而不是随对话消失）时。`grill-with-docs` 是 user-invoked 编排层，`grilling` 是它内部驱动的 model-invoked 访谈原语——同一个 `grilling` 原语还被 `improve-codebase-architecture`、`triage`、`wayfinder`、`to-questionnaire` 复用，是全插件里复用率最高的一块。

**核心规则（grilling 访谈原语）：** 把访谈看成一棵**design tree**（设计树）——每个未决问题是一个节点，**frontier（前沿）** 是"当前可以被回答的问题集合"。每轮（round）只问 frontier 上的问题，回答会让树往下长出新的子问题，形成新的 frontier。**session 结束的判定标准是 frontier 为空**，不是问够了几轮。

**寻找事实是你的工作，永远不是用户的：** 需要知道某个环境事实（这个函数现在怎么实现的、这个依赖版本号是多少）时，dispatch 一个子智能体去查，而不是把这类问题抛给用户。用户只回答只存在于他们脑子里的判断和偏好。

**问题输出格式（固定模板）：**
```
❓ **Q1** - **<question title>**: <question body>

➡️ <your recommended answer>
```
每个问题都要带一个你的推荐答案——不是让用户凭空作答，而是让他们「确认或纠正」。

**grill-with-docs 的编排流程：**
```
1. 启动 /grilling（驱动上述访谈循环，直到 frontier 清空）
2. 访谈过程中调用 /domain-modeling：
   - 挑战词汇是否与 CONTEXT.md 一致
   - 把模糊语言磨尖
   - 讨论具体场景
   - 与现有代码交叉验证
   - 内联更新 CONTEXT.md
3. 访谈结束后，把决策沉淀为 CONTEXT.md 更新 + 可能的 ADR
```

**典型场景：**

```
用户：/grill-with-docs 我想给购物车加「稍后购买」功能

第一轮 frontier：
  ❓ Q1 - 存储位置：这个状态存在服务端还是本地？
    ➡️ 服务端，因为要跨设备同步
  ❓ Q2 - 与现有 wishlist 功能的关系：是同一个实体还是独立概念？
    ➡️ 独立概念，wishlist 是收藏，save-for-later 是购物车临时移出

用户确认后，树往下长：
  ❓ Q3 - 移入 save-for-later 时，原购物车行的优惠券/折扣是否保留？
    ...

frontier 清空后 → domain-modeling 更新 CONTEXT.md，记录「SavedItem」实体定义
```

★ Insight ─────────────────────────────────────
`grilling` 之所以被 5 个 skill 复用而不是各自写一套问答逻辑，本质是把"如何问出高质量问题"这件事和"问完之后往哪个流程走"解耦。design tree + frontier 这套心智模型的价值在于：它给了"什么时候该停止提问"一个客观判据（树没有新叶子了），避免了 LLM 常见的两种失败模式——问不完（对每个回答都追加子问题，永无止境）或问太浅（一轮问完就武断收尾）。
─────────────────────────────────────────────────

### to-spec

**触发时机：** 一个功能大到需要跨多个会话构建、需要先固化下"到底要做什么"再切工单时。

**核心规则：** `to-spec` **不做新的访谈**，它综合已经发生的对话（通常紧跟在 `grill-with-docs` 之后，在同一个未 `/clear` 的上下文里）产出一份结构化 spec 文档。

**Spec 固定模板：**

| 章节 | 内容 |
| :--- | :--- |
| Problem Statement | 要解决的问题，不涉及方案 |
| Solution | 方案概述 |
| User Stories | 用户视角的场景 |
| Implementation Decisions | 技术选型与理由 |
| Testing Decisions | 测试策略 |
| Out of Scope | 明确排除的部分 |
| Further Notes | 边角信息 |

**典型场景：**

```
（承接上文 grill-with-docs 的访谈，同一上下文内）
用户：/to-spec

→ 综合刚才关于「稍后购买」功能的全部问答
→ 产出 docs/specs/save-for-later.md，含七个固定章节
→ 不重新提问，除非发现访谈中遗留了未决问题
```

### to-tickets

**触发时机：** spec 已经写好，需要切成可独立执行、可在不同会话/不同 agent 之间分发的工单。

**核心规则：** **竖切（tracer-bullet）原则**——每个 ticket 应该是一条端到端可验证的功能切片，而不是"先写后端 ticket 再写前端 ticket"的横切。工单之间标注**阻塞边（blocking edge）**，明确依赖顺序。

**Wide refactor 的例外处理——expand-contract 三段式：** 当变更本质是"改一个被广泛引用的接口"而不是"加一个新功能"时，竖切会制造大量脆弱的中间状态。这时改用：
1. **Expand**：新增新接口/新字段，与旧接口并存
2. **Migrate**：按 blast radius（影响范围）分批把调用点迁移到新接口
3. **Contract**：确认全部迁移完成后，删除旧接口

**Ticket 存储：** 按 `setup-matt-pocock-skills` 配置的 issue tracker 写入——GitHub/GitLab 用 `gh issue create` 等命令；本地模式写到 `.scratch/<feature>/issues/<NN>-<slug>.md`。

**典型场景：**

```
用户：/to-tickets
（基于 save-for-later.md spec）

→ 识别这是新功能，非 wide refactor → 竖切
→ Ticket 01：后端 SavedItem 模型 + API（无依赖）
→ Ticket 02：前端「移入稍后购买」按钮（阻塞于 01）
→ Ticket 03：稍后购买列表页（阻塞于 01）
→ 写入 .scratch/save-for-later/issues/01-*.md 等三个文件，标注阻塞关系
```

### implement

**触发时机：** 一个范围已经清楚的 ticket/任务，要真正开始写代码。这是 main flow 最终落地的一步，也是唯一一个"不管走哪条路径，最终都会汇入"的 skill。

**核心规则：** 全文极简——**驱动 `/tdd`** 在预先约定的 seam（测试所在的公开边界）上工作；开发过程中**定期跑 typecheck/单测/全量测试**（不要攒到最后一次性验证）；完成后**跑 `/code-review`**；最后提交到当前分支。**每个 ticket 建议一个独立会话（`/clear` 后开始）**，避免上一个 ticket 的上下文污染下一个。

**典型场景：**

```
用户：/implement（针对 Ticket 01：后端 SavedItem 模型 + API）

→ 驱动 tdd：先写失败测试（SavedItem 的 CRUD 行为）
→ Green：实现最小代码
→ Refactor
→ 全量测试 + typecheck
→ /code-review 走一轮
→ git commit
```

### tdd

**触发时机：** `implement` 内部驱动，也可被模型在任意"写一段新逻辑"的场景中自动触发。

**核心规则：Red-Green-Refactor** 循环，但插件对"在哪测"给出了明确纪律：

**Seams（测试所在的公开边界）：** 只在预先约定的 seam 上写测试，不测试实现细节。这与 `codebase-design` 里"interface is the test surface"的原则是同一件事的两种表述。

**三种反模式（禁止）：**

| 反模式 | 表现 |
| :--- | :--- |
| Implementation-coupled | 测试断言内部实现细节，重构就会测试失败 |
| Tautological | 测试逻辑和实现逻辑抄一遍，等于没测 |
| Horizontal slicing | 按"层"切测试（先测所有 model，再测所有 controller），而不是按"功能"切 |

**循环的三条规则：**
1. 先写一个失败的测试，确认它真的失败（不是配置错误导致的假失败）
2. 只写让测试通过所需的最少代码
3. 通过后再重构，重构过程中测试必须一直保持绿色

**典型场景：**

```
用户：/tdd（要实现「移入稍后购买时保留折扣」这条逻辑）

Red：写测试 —— 购物车行有优惠券时，移入 saved items 后优惠券字段应保留
     跑测试，确认失败（且是因为逻辑未实现，不是测试本身写错）
Green：最小实现 —— 在 moveToSaved() 里带上 discountId 字段
Refactor：抽取字段映射逻辑，测试全程保持绿色
```

### code-review

**触发时机：** `implement` 收尾时自动触发，或代码写完想过一遍。

**核心规则：双轴并行 review**——把"这段代码是否符合规范（Standards）"和"这段代码是否满足需求（Spec）"分成两条独立的检查线，分别派发给**两个并行子代理**，避免两条检查线互相污染彼此的上下文与结论。

**五步流程：**
1. **Pin fixed point**：确定这次 review 的代码范围（通常是相对某个 commit/分支的 diff）
2. **Identify spec source**：找到这段代码对应的 spec/ticket/需求描述
3. **Identify standards sources**：以 **12 条 Fowler code smell** 作为基线（见下表），加上仓库自身的 lint/风格规则
4. **Spawn 两个并行子代理**：Standards 子代理只看代码坏味道，Spec 子代理只看是否满足需求，互不知晓对方存在（两个子代理 prompt 均限定 400 字以内）
5. **Aggregate**：把两份报告原样并列展示，**不合并、不重排**——避免"综合结论"抹掉某一轴上的具体问题

**12 条 Fowler code smell 基线：**

| # | Smell | # | Smell |
| :-: | :--- | :-: | :--- |
| 1 | Mysterious Name | 7 | Repeated Switches |
| 2 | Duplicated Code | 8 | Shotgun Surgery |
| 3 | Feature Envy | 9 | Divergent Change |
| 4 | Data Clumps | 10 | Speculative Generality |
| 5 | Primitive Obsession | 11 | Message Chains |
| 6 | (保留位) | 12 | Middle Man / Refused Bequest |

**典型场景：**

```
用户：/code-review（针对 save-for-later 的 PR diff）

→ Pin：对比 main 分支的 diff
→ Spec source：Ticket 01 的验收标准
→ Standards子代理：发现 SavedItemService 有 Feature Envy（频繁调用 Cart 的内部字段）
→ Spec子代理：发现「保留折扣」这条验收标准未被测试覆盖
→ 输出：两份报告并列展示，不合并结论
```

---

## 二、Engineering 域：On-ramp（问题接入口）

这三个 skill 不是 idea → ship 主流程的一站，而是**从别处进入这条主流程的入口**——它们各自处理一种"事情已经发生了，现在需要决定怎么办"的场景，处理完之后再把结论汇入主流程（比如 triage 判定某个 issue 值得做，就交给 grill-with-docs/to-spec 继续）。

### triage

**触发时机：** issue/PR 堆积，需要系统性过一遍分类、判断优先级、回复处理意见。

**核心规则：** 两个 category 角色（bug / enhancement）+ 五个 state 角色（`needs-triage`/`needs-info`/`ready-for-agent`/`ready-for-human`/`wontfix`，具体标签字符串由 `setup-matt-pocock-skills` 配置）。**PR 被当成"附带代码的 issue"处理**，走同一套分类逻辑。**每条 AI 生成的评论必须带免责声明**：`> *This was generated by AI during triage.*`——这是插件里少数几处强制免责声明的地方，因为 triage 的输出会直接出现在公开 issue tracker 上，影响真实协作者的判断。

**五步流程：**
1. **Gather context**：读 issue 描述、关联代码、历史评论
2. **Recommend**：给出分类 + 状态标签的建议
3. **Verify the claim**：如果是 bug report，验证复现步骤是否成立（不能直接采信报告者的描述）
4. **Grill（如需要）**：信息不足时调用 `/grilling` 向 issue 作者或维护者补问
5. **Apply the outcome**：打标签、回复评论（带免责声明）

**典型场景：**

```
用户：/triage（面对仓库里 40 个未分类 issue）

Issue #102「点击保存按钮没反应」：
  → Gather：读复现步骤，发现只在 Safari 提及
  → Verify：尝试在代码里定位对应的保存逻辑，发现确实有个 Safari-only 的 event listener 问题
  → Recommend：bug + ready-for-agent
  → 评论："已确认为 Safari 特定问题，定位到 xxx.ts 第 42 行事件绑定缺失。
          > *This was generated by AI during triage.*"
```

### diagnosing-bugs

**触发时机：** 遇到一个具体的、可复现或半可复现的 bug，需要系统化排查（而不是盲改代码试出来）。

**核心规则：六阶段调试法**，Phase 1 是全流程里投入最大、最核心的一步：

**Phase 1 — Build feedback loop（构建反馈循环）**，按优先级排序的十种方法：

| 优先级 | 方法 |
| :-: | :--- |
| 1 | Failing test（能写成自动化测试就直接写） |
| 2 | Curl 脚本（API 类问题） |
| 3 | CLI 比对（对比预期输出与实际输出） |
| 4 | Headless browser（前端类问题） |
| 5 | Replay trace |
| 6 | Throwaway harness（临时脚本） |
| 7 | Property/fuzz loop |
| 8 | Bisection harness（二分定位引入 bug 的 commit） |
| 9 | Differential loop（新旧版本对比跑） |
| 10 | HITL bash script（人类在环，最后手段） |

**后续阶段：**
- **Phase 2 Reproduce + minimise**：把复现步骤缩到最小
- **Phase 3 Hypothesise**：列出 3–5 个**可证伪**的假设（不是"可能是缓存问题"这种笼统说法，而是能直接验证/推翻的具体陈述）
- **Phase 4 Instrument**：打点排查，日志统一标记 `[DEBUG-xxxx]` 便于最后清理
- **Phase 5 Fix + regression test**：修复后补一个回归测试，防止复发
- **Phase 6 Cleanup + post-mortem**：清理 Phase 4 遗留的调试日志，写复盘

每个阶段都有明确的"完成标准清单"，不满足就不能进入下一阶段。

**典型场景：**

```
用户：/diagnosing-bugs（用户报告「导出 PDF 后中文乱码」）

Phase 1：写一个能复现的最小脚本——固定输入内容，跑导出，检查输出字节
Phase 2：缩小到「只要包含中文字符就乱码，英文正常」
Phase 3：假设 A（字体未嵌入中文字符集）/ 假设 B（编码声明错误）/ 假设 C（PDF 库版本 bug）
Phase 4：打点 [DEBUG-pdf01] 输出实际使用的字体资源路径 → 定位到假设 A 成立
Phase 5：嵌入中文字体，写回归测试
Phase 6：清理 [DEBUG-pdf01] 日志，记录「后续换 PDF 库前需重新验证中文字体嵌入」
```

### wayfinder

**触发时机：** 一个想法/功能大到装不进一次会话，甚至大到装不进一次访谈——典型是 greenfield 项目或超大功能，**雾气（fog of war）太浓**，连"要问什么问题"本身都不清楚。这是插件里最复杂的 skill，`ask-matt` 明确说"雾太大才用，不要滥用"。

**核心哲学："Plan, don't do"**——wayfinder 本身不写代码，它只负责把模糊的大问题拆解成一张可以被后续 session/agent 认领执行的地图。

**核心概念：**

| 术语 | 含义 |
| :--- | :--- |
| Map | 单个 issue，打 `wayfinder:map` 标签 |
| Destination | 这张地图最终要到达的目标状态 |
| Fog of war | 尚未能精确表述的问题区域 |
| Frontier | 已经解锁但还没被认领的子 ticket |
| Ticket Type | Research / Prototype / Grilling / Task 四种 |

**HITL vs AFK：** 部分子 ticket 需要 Human-in-the-loop（比如需要用户做产品判断），部分可以 AFK（Away From Keyboard，agent 自主执行）——地图上会标注每张子 ticket 属于哪一类。

**Map body 固定模板：** Destination / Notes / Decisions so far / Not yet specified / Out of scope 五节。

**两种 invocation 模式：**

- **Chart the map（画地图，六步）**：从一个模糊想法出发，逐步展开 Destination、识别 fog of war、拆出第一批 frontier ticket
- **Work through the map（走地图，五步）**：认领 frontier 上的一张 ticket 并执行，执行完后地图更新，解锁新的 frontier

**硬规则：每个 session 最多解决一张 ticket**（research 类 ticket 例外，可以并行多张）——这是为了防止一个 session 里同时推进多条线导致互相污染上下文，与 `ask-matt` 的"上下文卫生"原则呼应。

**典型场景：**

```
用户：/wayfinder 我想做一个类似 Notion 的多人协作文档编辑器，从零开始

Chart the map：
  → Destination：支持多人实时编辑、块级结构化内容、权限管理
  → Fog of war：「实时同步用什么算法（OT vs CRDT）」「块结构怎么落数据库」两处完全不清楚
  → 拆出 frontier：
      Ticket A（Research，AFK）：调研 OT vs CRDT 在本项目场景下的取舍
      Ticket B（Grilling，HITL）：访谈用户明确「块级内容」的具体形态需求
      Ticket C（Prototype，AFK）：搭一个最小的实时同步 demo 验证可行性

（下一个 session）
      Ticket A（Research，AFK）：调研 OT vs CRDT 在本项目场景下的取舍
      Ticket B（Grilling，HITL）：访谈用户明确「块级内容」的具体形态需求
      Ticket C（Prototype，AFK）：搭一个最小的实时同步 demo 验证可行性

（下一个 session）
Work through the map：
  → 认领 Ticket A，产出调研结论 → 解锁新的 frontier ticket「基于 CRDT 设计数据模型」
```

---

## 三、Engineering 域：代码库健康与词汇层

这一组 skill 不对应"做一件具体的事"，而是维护贯穿全流程的**共享语言层**和**代码库整体质量**。`domain-modeling`/`codebase-design` 是 model-invoked 的词汇标准，被前面几乎所有编排型 skill 内部调用；`improve-codebase-architecture` 是维护性的入口，产出的结论会反过来汇入 `grill-with-docs` 主流程。

### improve-codebase-architecture

**触发时机：** 不是在开发新功能，而是定期/主动检视代码库整体架构健康度，找出值得重构的候选区域。

**核心规则：** 从 commit history 找"热点"入手——频繁变更、频繁一起改动的文件往往是架构痛点的信号。产出一份**自包含 HTML 报告**（写到操作系统临时目录，不是仓库内，因为它是一次性分析产物而非项目文档）：用 Tailwind CDN + Mermaid CDN 渲染，包含 Before/After 架构对比图和"Recommendation strength"（推荐强度）徽章。

**三步流程：**
1. **Explore**：先看 git log 找变更热点，再结合当前代码结构定位候选问题区域
2. **生成 HTML 报告**：每个候选问题配一张 Before/After 对比图 + 强度徽章（如「强烈建议」/「值得考虑」）
3. **Grilling loop**：用户从报告里选中感兴趣的候选项后，调用 `/grilling` + `/domain-modeling` 深入讨论，最终结论汇入正常的 `grill-with-docs` 流程去实际执行

**典型场景：**

```
用户：/improve-codebase-architecture

→ Explore：发现 UserService.ts 和 OrderService.ts 在过去 3 个月里几乎每次一起改动
→ 报告候选项：「UserService 与 OrderService 耦合过深，建议引入 UserOrderFacade」
   （强度：强烈建议，附 Before/After Mermaid 架构图）
→ 用户在报告里选中该项 → 触发 grilling 讨论具体怎么拆
→ 讨论结论 → 走 to-spec → to-tickets → implement 正常落地
```

### domain-modeling

**触发时机：** model-invoked，几乎在任何涉及"给一个概念下定义/讨论业务规则"的对话里都可能被触发；显式驱动方是 `grill-with-docs` 内部调用。

**核心规则：** 文档布局分两种（由 `setup-matt-pocock-skills` 决定）：

| 布局 | 结构 |
| :--- | :--- |
| Single-context | 根目录一份 `CONTEXT.md` |
| Multi-context | `CONTEXT-MAP.md`（索引）+ 每个上下文各自一份 `CONTEXT.md` |

**五种交互模式：**
1. **Challenge against glossary**：新提到的术语是否与 `CONTEXT.md` 已有词汇冲突
2. **Sharpen fuzzy language**：把"用户"这种模糊词逼问成"注册用户"还是"访客"
3. **Discuss concrete scenarios**：用具体场景校验定义是否成立
4. **Cross-reference with code**：定义是否与代码里实际的类型/命名一致
5. **Update CONTEXT.md inline**：讨论过程中直接更新文档，不攒到最后

**ADR 触发条件（三条必须同时满足才写 ADR，缺一不可）：**
- Hard to reverse（决策难以撤回）
- Surprising without context（不解释理由，旁观者会觉得意外）
- 存在真实的 trade-off（不是唯一显然的方案）

**典型场景：**

```
（grill-with-docs 访谈中途触发）
用户提到「稍后购买的商品30天后自动清理」

domain-modeling 介入：
  → Challenge：CONTEXT.md 里「购物车行」的定义是否涵盖 SavedItem？→ 不涵盖，需新增术语
  → Sharpen：「30天」是从加入时算，还是从最后一次查看时算？
  → Cross-reference：代码里是否已有类似的 TTL 清理逻辑可复用？
  → Inline update：CONTEXT.md 新增「SavedItem」定义 + TTL 规则
  → 判断是否需要 ADR：TTL 策略选择存在真实 trade-off（成本 vs 用户体验）且难以撤回
    → 是 → 写 docs/adr/00xx-saved-item-ttl.md
```

### codebase-design

**触发时机：** model-invoked，讨论"这段代码该怎么组织"（新建模块、拆分职责、定义接口边界）时自动介入；也是 `code-review`、`tdd` 里"seam"概念的定义来源。

**核心规则：八个术语的精确定义**，是全插件里唯一一处系统性地为架构讨论提供共享词汇的地方：

| 术语 | 定义 |
| :--- | :--- |
| Module | 一个有边界的实现单元 |
| Interface | Module 对外暴露的契约——**也是测试应该覆盖的表面**（"interface is the test surface"） |
| Implementation | Interface 背后的具体代码，可以自由重写而不影响调用方 |
| Depth | Interface 简单、Implementation 复杂 = deep；反之 = shallow |
| Seam | 测试/替换实现的接缝，通常等于 Interface |
| Adapter | 为适配某个外部系统写的转换层 |
| Leverage | 一个 Module 被复用的程度 |
| Locality | 修改一处需求时，改动是否能局部化在少数 Module 内 |

**Deep vs Shallow（ASCII 对比）：**
```
Deep module（好）：          Shallow module（差）：
  简单接口                     复杂接口
  ┌────┐                      ┌──────────┐
  │ if │                      │ getX()   │
  └─┬──┘                      │ setY()   │
    │ 复杂实现                 │ getZ()   │
  ┌─┴──────┐                  │ doA()    │
  │ ...    │                  │ doB()    │
  │ ...    │                  └────┬─────┘
  └────────┘                       │ 简单实现
                                  ┌─┴──┐
                                  │ .. │
                                  └────┘
```

**四条设计原则：**
1. 优先做 deep module（简单接口封住复杂实现），而非 shallow module（接口本身就很复杂，等于没封装）
2. **Deletion test**：如果删掉这个 module，调用方需要改多少行？改得越多，说明这个 module 的边界切得越合理（意味着它真的封装了东西，而不是薄薄一层转发）
3. **"一个 adapter 是假设的 seam，两个才是真实的 seam"**——只有一个外部系统在用某个适配层时，那个"接口"可能只是臆想出来的抽象；有两个实现在用，才说明这条边界是真实存在的
4. Interface 就是测试面——测试应该打在 Interface 上，不应该穿透到 Implementation 内部

**三条明确拒绝的框架（Rejected framings）：**
- 不采用 Ousterhout《A Philosophy of Software Design》里"depth = functionality / interface complexity"的比率定义——本 skill 认为 depth 是相对判断，不是可计算比率
- 不采用 TypeScript `interface` 关键字的狭义含义——这里的 Interface 是设计概念，不等于语言语法
- 不使用"boundary"这个词——因为容易与 DDD 的 bounded context 混淆，本 skill 统一用 module/seam 表述边界

**典型场景：**

```
（implement 阶段，讨论 SavedItemService 该怎么设计）

codebase-design 介入：
  → 建议：SavedItemService 对外只暴露 moveToSaved(cartItemId) / moveBackToCart(savedItemId) 两个方法
     （deep：接口简单）
  → 内部处理折扣保留、TTL 计算等复杂逻辑（implementation 复杂，但外部不需要知道）
  → Deletion test：如果删掉 SavedItemService，调用方（前端按钮 handler）只需改一行 API 调用
     → 说明封装合理
  → 测试打在 moveToSaved/moveBackToCart 这两个 seam 上，不测试内部折扣计算细节
```

---

## 四、Engineering 域：独立工具

这四个 skill 彼此独立，不依赖主流程的上下游，可以在任何时候单独调用。

### prototype

**触发时机：** 需要快速验证一个想法是否可行，还不打算走完整的 spec/ticket 流程。

**核心规则：** 根据要验证的对象分两条分支：

| 分支 | 产出 | 适用场景 |
| :--- | :--- | :--- |
| LOGIC.md 路径 | 状态机 HTML | 验证一套业务逻辑/状态转换是否合理 |
| UI.md 路径 | 多变体 UI 路由页面 | 验证多个视觉/交互方案哪个更好 |

**六条通用规则**，第 6 条最关键——**"完成后要捕获它（Capture it when done）"**：验证完成后必须把 prototype 提交到 `prototype/<name>` 分支，作为**主要来源（primary source）**永久保留，不能验证完就随手丢弃。这是因为 prototype 过程中做的取舍决定本身就是有价值的设计记录。

**典型场景：**

```
用户：/prototype 想看看「拖拽排序」和「上下箭头按钮」两种交互哪个更顺手

→ 判断为 UI 验证 → 走 UI.md 路径
→ 搭建一个路由页面，/variant-a 是拖拽排序，/variant-b 是箭头按钮
→ 用户试用后选定拖拽排序
→ 提交到 prototype/reorder-interaction 分支保留
→ 结论带入正式 implement 阶段
```

### research

**触发时机：** 需要基于一手资料（primary sources）做研究调研，且不希望研究过程占用主对话的上下文。

**核心规则：** 全文极简——**委托给 background agent**，要求引用一手资料，产出**带引用的 Markdown 文件**落盘。这是插件里最短的 skill 之一，因为它本质是"调用子智能体做研究"这个模式的一层薄封装。

**典型场景：**

```
用户：/research CRDT 与 OT 在多人编辑场景下的性能对比

→ 派发 background agent
→ agent 检索一手资料（论文、官方文档、benchmark 数据）
→ 产出 docs/research/crdt-vs-ot.md，每条结论标注引用来源
→ 主对话上下文不被检索过程污染，只拿到最终文件
```

### resolving-merge-conflicts

**触发时机：** 已经处于 merge conflict 状态中，需要系统性解决。

**核心规则：** 全文仅五步，核心原则是**"始终解决冲突，永不 `--abort`"**——`resolving-merge-conflicts` 假设"放弃这次合并"不是一个可接受的退路，冲突必须被理解并解决，而不是绕开。

**典型场景：**

```
用户：/resolving-merge-conflicts

→ 定位冲突文件与冲突块
→ 结合两侧的 commit 意图理解冲突本质（不是机械选 ours/theirs）
→ 逐一解决，运行测试验证
→ 完成合并（不使用 git merge --abort 退出）
```

### wizard

**触发时机：** 需要构建一个多步骤引导流程（wizard），本身是一个"生成引导式流程"的元工具。

**核心规则：** 基于 `template.sh` 模板生成。**明确的适用边界**——"不要为 agent 自己就能完成的步骤调用这个 skill"，也就是说 wizard 是为**需要人类逐步确认/输入**的多阶段流程设计的，如果 agent 能一次性自主跑完，就不需要包装成 wizard。

**四步流程：**
1. **Scope procedure**：明确这个 wizard 要覆盖哪些步骤
2. **Map each stage's journey**：每一步用户会看到什么、输入什么
3. **Author the wizard**：基于模板实际生成
4. **Verify and hand off**：验证流程走得通，交付

**典型场景：**

```
用户：/wizard 我想为新贡献者做一个「如何配置本地开发环境」的引导流程

→ Scope：clone → 安装依赖 → 配置环境变量 → 起数据库 → 跑测试确认环境 OK 五步
→ Map：每步需要用户输入什么（比如环境变量的具体值）
→ Author：基于 template.sh 生成对应的引导脚本/文档
→ Verify：新贡献者视角走一遍，确认每步指引清晰
```

---

## 五、Productivity 域

Engineering 域解决"怎么把代码写对"，Productivity 域解决"怎么和 AI 高效协作本身"——访谈、交接、教学、写文档这类跨领域通用能力。

### grill-me

**触发时机：** 想推进一个想法，但**不在工作目录里**（没有代码库、纯讨论场景），或者不需要把结论写成 `CONTEXT.md`/ADR 这类持久化文档。

**核心规则：** 全文仅一句——"Run a `/grilling` session."。它是 `grill-with-docs` 的**无状态版本**：同样驱动 design tree + frontier 循环访谈，但访谈结束后不落盘任何文档，结论只存在于对话历史里。

**典型场景：**

```
用户：/grill-me 帮我想清楚要不要从 REST 换成 GraphQL

→ 纯讨论场景，不针对某个具体代码库
→ 驱动 grilling 循环，逐轮问清楚团队规模、现有客户端数量、性能诉求等
→ frontier 清空后给出结论，不写入任何 CONTEXT.md（因为没有工作目录语境）
```

### handoff

**触发时机：** `disable-model-invocation: true`，`argument-hint` 提示为"下一个会话将被用来做什么？"——典型场景是换 harness、换目录、交给同事、或从当前任务中分叉出一个旁支任务。这是 `ask-matt` 阶段边界五选项之一。

**核心规则：** 产出的交接文档写到**操作系统临时目录**（不是当前 workspace），因为它是一次性的、跨会话传递用的产物，不是项目文档。文档含一个**"suggested skills"**章节，提示下一个会话该用哪些 skill 继续。**不重复其他 artifact 已有的内容**——如果结论已经写在某个 spec/ticket 文件里，交接文档只引用路径/URL，不整段抄录。**须对敏感信息做 redact（脱敏）处理**。

**典型场景：**

```
用户：/handoff 接下来要在另一台机器上用 Codex 继续

→ 产出交接文档（写到 OS temp 目录）：
   - 当前进度：Ticket 01 已完成，Ticket 02 进行中
   - 引用：.scratch/save-for-later/issues/02-*.md（不整段复制内容）
   - Suggested skills: /implement（继续 Ticket 02）
   - 脱敏：移除对话中出现的测试环境数据库密码
```

### teach

**触发时机：** 需要系统性地教用户学习某个主题/技能，而不是单次问答式讲解。

**核心规则：** 教学工作区由七类文件构成：

| 文件/目录 | 用途 |
| :--- | :--- |
| `MISSION.md` | 本次教学的整体目标 |
| `reference/*.html` | 参考资料 |
| `RESOURCES.md` | 外部资源索引 |
| `learning-records/*.md` | 学习进度记录 |
| `lessons/*.html` | 具体课程内容（要求 **Tufte 风格**排版，即注重数据/图表清晰呈现的极简学术风格） |
| `assets/*` | 配图等素材 |
| `NOTES.md` | 教学过程中的零散笔记 |

**两个核心区分概念：**
- **Fluency strength vs Storage strength**：前者是"现在能不能流畅使用"，后者是"记忆是否牢固不会遗忘"——两者独立，教学设计要同时兼顾（不能只练熟练度不管长期记忆，也不能只做记忆强化不给流畅练习）
- **Zone of Proximal Development（最近发展区）**：教学内容应该落在"用户现有能力刚好够不上，但通过引导能达到"的区间，太易或太难都无效

**典型场景：**

```
用户：/teach 教我理解 CRDT 的核心原理

→ 建立 MISSION.md：目标是让用户能独立判断某场景是否适合用 CRDT
→ 评估用户现有基础（分布式系统经验）→ 定位 Zone of Proximal Development
→ lessons/01-intro.html：Tufte 风格排版，图解 CRDT 合并规则
→ 学习后记录到 learning-records/2026-08-30.md
→ 后续复习时同时检查 Fluency（能否现场解释）和 Storage（一周后是否还记得）
```

### to-questionnaire

**触发时机：** `disable-model-invocation: true`，需要给某个外部对象（用户、客户、团队）发一份问卷收集信息。

**核心规则：**"**Grill the send, not the subject（访谈'怎么发'，不要访谈'问什么'）**"——`to-questionnaire` 只向你提问关于「发送对象是谁」「需要拿回什么样的信息」这两类元问题，绝不直接问你问卷的主题内容本身（那应该是问卷面向的对象来回答的）。产出文件名固定为 `to-questionnaire-<slug>.md`。

**典型场景：**

```
用户：/to-questionnaire 想了解现有用户对「稍后购买」功能的期待

to-questionnaire 只问你：
  ❓ 发送对象是谁？付费用户还是全部用户？
  ❓ 需要拿回什么？是「要不要做」的验证，还是「怎么设计」的细节？

（不会问你「用户对稍后购买有什么期待」这种主题本身的问题——那是问卷该问受访者的）

→ 产出 to-questionnaire-save-for-later-survey.md
```

### wait-what

**触发时机：** `disable-model-invocation: true`，当前解释太难懂、术语太密集，需要重新用简单语言解释一遍。

**核心规则：** 全文仅一段话——要求用 **ASD-STE100 Simplified Technical English**（航空工业维护文档常用的受控自然语言标准，核心是短句、限定词汇表、无歧义结构）重新解释，并且要使用项目 `CONTEXT.md` 里已经定义好的词汇（不引入新术语）。

**典型场景：**

```
（前面模型解释了一段涉及 CRDT/vector clock/causal consistency 的内容）
用户：/wait-what

→ 用 ASD-STE100 风格重新说一遍：短句、限定动词、避免被动语态
→ 替换生僻术语为 CONTEXT.md 已定义的项目内词汇
→ 例如把「causal consistency」换成项目里已经用惯的「操作先后顺序保证」
```

### writing-for-agents

**触发时机：** model-invoked，撰写供 agent 读取的文档（SKILL.md、CLAUDE.md、AGENTS.md 等）时自动介入，判断怎么写更容易被模型正确理解和执行。

**核心规则——一套完整的文档写作理论：**

| 概念 | 含义 |
| :--- | :--- |
| Context pointer（上下文指针） | 文档里用引用/路径代替整段复制，降低维护成本 |
| Context load vs cognitive load | 二元代价模型——塞进上下文本身有成本（context load），理解消化也有成本（cognitive load），两者要分别优化，不能只看其一 |
| Information hierarchy 三层 | in-file step（步骤直接写在文件里）/ in-file reference（文件内引用别处）/ disclosed reference（跳转到外部文件）——按信息的使用频率和体量决定放哪一层 |
| Leading words（引导词） | 借用模型预训练阶段已经见过的成熟概念词汇，比生造新词更容易被正确理解 |
| Negation 失效模式 | "不要做 X"这种否定式指令效果差（类比"不要想象大象"效应，否定反而会激活被否定的概念），应该正面表述该做什么 |

**Pruning（精简）四原则：**
1. Single source of truth——同一信息只在一处维护，其余地方引用
2. 环境本身作为真源——如果代码/配置已经能回答这个问题，文档不需要重复说明
3. Relevance 检验——每一段内容问自己"这跟当前任务相关吗"
4. No-op 检验——删掉这段话，行为会变吗？不变就删

**子文件：** 详见 `SKILL-MECHANICS.md`（该子文件覆盖 skill 专属的 frontmatter 规则、invocation 方式选择、router skill 应遵循的额外约束）。

**典型场景：**

```
（撰写一份新 SKILL.md 时）

writing-for-agents 介入：
  → 检查是否有大段重复内容可以换成 context pointer（引用而非复制）
  → 检查指令是否用了"不要做 X"式否定表述 → 改写为正面指令"应该做 Y"
  → 检查术语是否用了生造词 → 换成模型预训练阶段更熟悉的 leading word
  → 用 no-op 检验逐段检查：删掉这段，agent 行为会变吗？不变则删
```

---

## 六、Misc / In-progress / Deprecated

这三类**不包含在插件默认安装范围内**（`.claude-plugin/plugin.json` 的 `skills` 数组只列出了前面 24 个 engineering + productivity skill），因此下面只做简要引用，不展开触发时机/核心规则/典型场景四要素。

### Misc（4 个，"很少用"，未被插件打包推广）

| Skill | 一句话说明 |
| :--- | :--- |
| `git-guardrails-claude-code` | 配置 hooks 拦截危险 git 命令（如误 push 到主分支） |
| `migrate-to-shoehorn` | 把代码里的 `as` 类型断言迁移到 shoehorn 库的安全转换方式 |
| `scaffold-exercises` | 生成练习题目录结构 |
| `setup-pre-commit` | 配置 Husky pre-commit + lint-staged + Prettier |

### In-progress（6 个，beta 阶段，需单独安装）

不随插件安装，需要额外执行 `npx skills@latest add mattpocock/skills --skill=<name>` 才能使用：

| Skill | 一句话说明 |
| :--- | :--- |
| `loop-me` | 多 session 的 workflow spec 访谈流程 |
| `writing-beats` | 按"beat"（叙事节拍）组织的文章写作方法 |
| `writing-fragments` | 碎片化素材采集 |
| `writing-shape` | 逐段成文的写作辅助 |
| `claude-handoff` | 后台 agent 之间的任务交接 |
| `setup-ts-deep-modules` | 配置 dependency-cruiser 检查 TypeScript 模块深度 |

### Deprecated（当前为空）

退役的 skill 会被直接删除，替代方案记录在插件的 changeset 里，不保留占位文档。

---

## 标准工作流链路

### 场景一：功能开发全流程（多会话大功能）

```
/ask-matt（判断走 main flow）
  → /grill-with-docs（访谈 + domain-modeling 沉淀 CONTEXT.md）
  → /to-spec（综合访谈产出 spec）
  → /to-tickets（竖切成可独立执行的工单，标注阻塞边）
  → 逐票 /clear 后 /implement（内部驱动 /tdd）
      → /code-review（双轴并行）
      → commit
```

### 场景二：Bug 修复流程

```
用户报告 bug
  → /diagnosing-bugs
      Phase 1 Build feedback loop（优先写 failing test）
      → Phase 2 Reproduce + minimise
      → Phase 3 Hypothesise（3-5 个可证伪假设）
      → Phase 4 Instrument（[DEBUG-xxxx] 标记）
      → Phase 5 Fix + regression test
      → Phase 6 Cleanup + post-mortem
  → commit（regression test 随修复一起提交）
```

### 场景三：Issue 堆积的批量处理

```
/triage（面对一批未分类 issue/PR）
  → 逐条 Gather context → Recommend → Verify claim
  → 信息不足时 /grilling 补问
  → Apply outcome（打标签 + 带免责声明的评论）
  → 判定为「值得做」的 issue 汇入场景一的 main flow
```

### 场景四：想法太模糊，先探路

```
/wayfinder（雾气浓到连问题都问不清楚时才用，不要滥用）
  → Chart the map：定义 Destination，识别 fog of war，拆出首批 frontier ticket
  → 每个 session 认领一张 ticket（research 类可并行）
  → Work through the map：执行、更新地图、解锁新 frontier
  → 单张 ticket 明确后，汇入场景一的 main flow 继续
```

### 场景五：代码库维护（非功能开发）

```
/improve-codebase-architecture
  → Explore（commit history 找热点）
  → 生成 HTML 报告（Before/After 对比图 + 推荐强度徽章）
  → 用户选中候选项 → /grilling + /domain-modeling 深入讨论
  → 结论汇入场景一的 main flow（grill-with-docs 之后正常走 spec/tickets/implement）
```

### 场景六：跨会话/跨 harness 交接

```
当前会话接近 smart zone 上限（约 150k token）或需要换环境
  → /handoff（生成交接文档到 OS 临时目录，含 suggested skills，脱敏）
  → 新会话/新 harness 读取交接文档
  → 按 suggested skills 提示继续（通常是 /implement 或 /wayfinder 的 work through the map）
```

---

**最后更新：** 2026/08/30
**适用范围：** 所有使用 mattpocock-skills 插件的 Claude Code 会话

