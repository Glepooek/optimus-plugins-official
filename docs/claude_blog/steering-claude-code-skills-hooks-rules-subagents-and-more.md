# 驾驭 Claude Code：何时使用 CLAUDE.md、skills、hooks 与子智能体

> **分类：** [Claude Code](https://claude.com/blog/category/claude-code)
> **产品：** Claude Code
> **日期：** June 18, 2026
> **阅读时长：** 5 分钟
> **原文链接：** https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more

Claude 被设计为契合你的工作方式，而在 Claude Code 中，你可以对它进行定制。

有七种方法可以指导 Claude 的行为：CLAUDE.md 文件、rules、[**skills**](https://code.claude.com/docs/en/skills)、[**子智能体**](https://code.claude.com/docs/en/sub-agents)、[**hooks**](https://code.claude.com/docs/en/hooks-guide)、output styles，以及追加系统提示词。

每种方法都控制着：

* 指令何时载入上下文；
* 它是否能在长会话中持续存在（压缩行为）；以及
* 它具有多大的权限等级。

下表快速总结了各方法之间的关键差异，而本文将提供更多细节，以及一套决策框架，帮助你判断每一条 Claude 指令应当归属何处。

| 方法 | 何时载入 | 压缩行为 | 上下文成本 | 何时使用 |
| :--- | :--- | :--- | :--- | :--- |
| CLAUDE.md（根目录） | 会话开始时载入；在整个会话期间保留在上下文中 | 记忆化。读取一次并缓存至整个会话；压缩后清除缓存并重新读取 | 高。无论是否相关，每一行都消耗 token | 构建命令、目录布局、monorepo 结构、编码规范、团队约定 |
| CLAUDE.md（子目录） | 按需载入，当 Claude 读取该子目录下的文件时 | 在该子目录再次被触及之前一直丢失 | 低。仅在处理相关子目录时才消耗上下文 | 特定于某个子目录的约定 |
| Rules | 会话开始时载入（用户级 rules），或仅在匹配文件被触及时载入（路径限定） | 压缩时重新注入 | 中。除非路径限定，否则始终开启 | 特定约束或约定（例如，所有 API handler 必须用 Zod 校验输入） |
| Skills | 会话开始时载入名称与描述；完整正文在 skill 被调用时载入 | 已调用的 skill 在共享预算内重新注入；最旧的优先被丢弃 | 低。完整正文仅在调用时载入；受所有已调用 skill 之间的共享 token 预算约束 | 流程化工作流（部署或发布检查清单） |
| 子智能体 | 会话开始时载入名称、描述与工具列表；正文仅在通过 Agent 工具调用时载入 | 只有最终消息（摘要加元数据）返回主会话 | 低。被调用前在主上下文中零成本；运行于自己独立的上下文窗口中 | 并行运行工作，或应当隔离运行且只返回摘要的旁支任务（深度搜索、日志分析、依赖审计） |
| Hooks | 在生命周期事件上触发 | 完全绕过压缩 | 低。配置存在于主上下文之外；部分输出可能返回（例如阻断性错误） | 确定性自动化：运行 linter、完成时发送到 Slack、阻断命令、在 PreCompact 时备份聊天记录 |
| Output styles | 会话开始时载入；注入系统提示词 | 从不压缩 | 高。占用上下文窗口，但会覆盖默认系统提示词 | 重大角色转变（从代码助手转为通用助手） |
| 追加系统提示词 | 会话开始时载入；通过 CLI 标志传入 | 从不压缩；仅应用于该次调用 | 中等。会话中首次请求后被缓存 | 语气、回复长度、格式偏好 |

## 传递指令的七种方法

有七种方式可以定制 Claude Code 的行为：CLAUDE.md 文件用于始终开启的项目上下文，rules 用于硬性约束，skills 用于可复用的流程，子智能体用于委派工作，hooks 用于确定性自动化，output styles 或系统提示词追加用于全局性变更。每种方法都在上下文成本与权限等级之间做出权衡——选对方法本身就是工作的大部分。

### CLAUDE.md 文件

CLAUDE.md 是位于项目根目录的一个 markdown 文件。它在会话开始时载入上下文，并在整个会话期间保留在那里。

构建命令、目录布局、monorepo 结构、编码规范以及团队约定都天然适合放在这里。

它有两种类型，且载入方式不同：

* **始终载入**：第一种是根目录 CLAUDE.md 文件，可以位于共享仓库中，也可以本地保存以存放你针对某个项目的个人偏好。所有这些文件都在会话开始时载入，且不会在长会话中丢失或退化。当 Claude Code 压缩对话时，它会重新读取这些文件。
* **按需载入**：位于你初始化会话的文件夹下方的子目录中的 CLAUDE.md 文件。例如，`app/api/CLAUDE.md` 会在 Claude 读取 `app/api` 下某个文件时载入，而非会话开始时。它的压缩行为与路径限定 rules 相同：在该子目录再次被触及之前一直丢失。

![CLAUDE.md 子目录文件的加载方式](../assets/claude-md-subdirectory.png)

*cwd 下方的所有子目录 CLAUDE.md 文件，都会在 Claude 读取该目录内文件时载入。*

在共享仓库中，CLAUDE.md 会像任何无人负责的配置文件一样膨胀：每个团队都追加自己的指令，却没有任何内容被删除。这种成本会随规模复合增长。

每一行都会为仓库中每一位工程师的每一次会话载入，无论它是否与其任务相关。这会消耗 token，并稀释对那些真正重要的指令的遵循度。随着文件增长，应把团队特定的约定推入路径限定 rules，把流程推入 skills，让它们只在相关时才载入。

**提示：** 把 CLAUDE.md 保持在 200 行以内，为它指定一位负责人，并像审查代码一样审查对它的变更。内容本身应遵循与任何提示词相同的规则：[编写有效的提示词](https://claude.com/blog/best-practices-for-prompt-engineering)意味着做到明确、解释约束背后的原因、并给出示例。

可以把这个文件想象成为 Claude 提供你代码库的概览，或是一个指向其他文件的索引，让 Claude 在需要时找到更多信息。

在 monorepo 中，为每个团队的目录配备各自的子目录 CLAUDE.md，这样团队只会载入自己的约定，而开发者可以使用 claudeMdExcludes 设置跳过那些他们从不触碰的团队的文件。

对于必须应用于组织内每个仓库的标准——安全策略、合规要求——可以通过 MDM 或配置管理将一份集中管理的 CLAUDE.md 部署到开发者机器上，且它无法被个人设置排除。

关于设置 CLAUDE.md 的更多内容，见我们的博客文章 [CLAUDE.md 文件：为你的代码库定制 Claude Code](https://claude.com/blog/using-claude-md-files)。

### Rules

[**Rules**](https://code.claude.com/docs/en/memory#organize-rules-with-claude/rules/) 是位于 `.claude/rules/` 中的 markdown 文件，用于给 Claude 提供特定的约束或约定。

未限定范围的 rules 行为类似 CLAUDE.md，它们总是在会话开始时载入，并在压缩时重新注入。这可能会浪费 token，因为即便对当前任务并不相关，也会载入上下文。

路径限定 rules 允许你通过添加一个 `paths` 字段来控制它们何时载入，从而仅在相关时载入 rule 指令。

例如：一个限定到 `src/api/**` 的 rule 在纯文档会话中会保持在上下文之外。它只会在 Claude 读取 `src/api/` 目录内的文件时载入。

它看起来是这样的：

```
---
paths:
  - "src/api/**"
  - "**/*.handler.ts"
---
All API handlers must validate input with Zod before processing.
```

**提示**：一个文件特定的约束，比如"迁移文件只能追加（append-only）"，最适合作为一条 **rule** 放在你的 paths: frontmatter 中。当指令涉及一个横切关注点、或涉及在代码库多处（但并非全部）出现的文件时，应优先选择路径限定 rule 而非嵌套的 CLAUDE.md 文件。

### Skills

[**Skills**](https://code.claude.com/docs/en/skills) 以文件夹形式存在于 `.claude/skills/` 中，包含指令、脚本和资源，由 Claude 动态载入。每个 skill 都有一个 `SKILL.md` 文件，含名称、描述和正文。

只有名称和描述在会话开始时载入；完整正文在 Claude 调用该 skill 时载入，可以通过斜杠命令（/code-review）触发，也可以通过与任务自动匹配来触发。

![Skills 通过系统提示词触发](../assets/skills-trigger.png)

*Skills 通过你的系统提示词触发。*

例如，`/code-review` 是一个内置 skill，它会审查你当前的 diff 并报告发现，而不编辑文件。该 skill 定义了操作手册，因此每次你调用它时 Claude 都遵循相同的结构化方法。

在压缩时，Claude Code 会在所有已调用 skill 共享的总预算内重新注入已调用的 skill。如果你在一次会话中调用了许多 skill，最旧的会优先被丢弃。

**提示：** 流程化的指令，比如部署工作流、发布检查清单或审查流程，应归属于 skill，而非放在 CLAUDE.md 中。

Claude Code 自带若干 skill，但你也可以编写自己的自定义 skill。我们的[构建 Claude skill 完整指南](https://claude.com/blog/complete-guide-to-building-skills-for-claude)会告诉你如何做。

### 子智能体

[**子智能体**](https://code.claude.com/docs/en/sub-agents) 是位于 `.claude/agents/` 中的 markdown 文件，用于为特定的旁支任务定义隔离的助手。每个文件使用 YAML frontmatter（名称、描述，加上可选的模型和工具访问字段），后接一段正文，该正文将成为该子智能体的系统提示词。

子智能体与 skill 相似，其名称、描述和工具列表在会话开始时载入，但智能体正文中较大的上下文不会自动调用。Claude 通过 Agent 工具调用它们，并传入一个提示词字符串。

![子智能体在独立上下文窗口中运行](../assets/subagent-context.png)

*Claude Code 的上下文窗口容纳了 Claude 关于你会话所知的一切。[此处的交互式时间线](https://code.claude.com/docs/en/context-window)会逐步讲解何物在何时载入。*

子智能体正文中较大的指令性上下文不仅不会自动调用，它根本不会进入父对话。

随后子智能体在自己全新的上下文窗口中运行，唯一返回到你主会话的，是子智能体的最终消息（通常是众多子任务的汇总结果）加上元数据。

这种模式可以扩展：子智能体最多可嵌套五层，而[动态工作流](https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code)可以编排数十到数百个后台智能体，而无需你指定子智能体架构的每一个细节。编排计划和中间结果存在于脚本变量中，而非 Claude 的上下文窗口，这使得扩展规模的同时不损失指令保真度。

**提示：** 这种隔离性正是选择子智能体而非 skill 的主要原因之一。当一个旁支任务——比如深度搜索、一次日志分析或一次依赖审计——会用你不会再引用的中间结果扰乱你的主对话时，使用子智能体。当你希望流程在主线程内展开、以便你能看到并引导每一步时，使用 skill。

### Hooks

[**Hooks**](https://code.claude.com/docs/en/hooks-guide) 是用户定义的命令、HTTP 端点或 LLM 提示词，它们通过在 [Claude 生命周期中的特定事件](https://code.claude.com/docs/en/hooks#hook-lifecycle)（比如文件编辑、工具调用或会话开始）上触发，提供对 Claude 行为更具确定性的控制。

![Claude Code 会话中 hook 可触发的事件图](../assets/hooks-lifecycle.png)

*一张 Claude Code 会话中 hook 可触发事件的地图。*

你可以在 `settings.json`、受管策略设置，或 skill/agent 的 frontmatter 中注册 hooks。

hook 有若干类型：command、HTTP、mcp\_tool、prompt 和 agent。所有 hook 都是确定性触发的。前三种确定性执行，而后两种（prompt 和 agent）使用 Claude 的判断而非一套规则来决定输出。

hooks 的上下文成本很低，因为配置或指令存在于主上下文窗口之外。工具链会运行处理器（command、http、mcp\_tool），或根据 hook 类型用独立窗口进行模型调用（prompt、agent）。

某些 hook 可能会把输出保存到主上下文窗口。例如，一个阻断性 hook 的标准错误会被保存进上下文，以便 Claude 知道该调用为何被拒绝。

但大多数 hook 不会把输出保存到主窗口，除非配置显式返回它。如果你在压缩前使用 `PreCompact` 事件把聊天记录备份到另一个文件以供日后参考，Claude 并不会知道哪个文件保存了聊天记录。

这使得这些 hook 类型与 CLAUDE.md、rules 和 skills 有着根本性的不同。你可以在我们的文章[**如何配置 hooks**](https://claude.com/blog/how-to-configure-hooks)中了解更多。

**提示：** 对任何应当确定性发生的事情使用 hooks：编辑后运行 linter、完成时发送到 Slack，或在特定命令执行前阻断它们。一个 `PreToolUse` hook 可以检查任何工具调用，并以退出码 2 拒绝它。

它们的上下文成本很低，因为它们是由工具链运行的代码，而非载入上下文的、给 Claude 的指令。

### Output styles

[**Output styles**](https://code.claude.com/docs/en/output-styles) 是位于 `.claude/output-styles/` 中的文件，用于向系统提示词注入指令。它们从不被压缩，在每次会话开始时载入，并在会话内首次请求后被缓存，这意味着它们具有中等的上下文成本。

由于它们处于系统提示词中，output styles 在我们目前所涵盖的所有方法中携带着最高的指令遵循权重，应当审慎使用。

**对 output style 的更改会替换默认的 output style**（除非你在样式的 frontmatter 中设置 keep-coding-instructions: true）。

在 Claude Code 中，这将移除那些告诉 Claude 它正在帮助用户完成软件工程任务的指令，以及其他关键的默认指令，例如：

* 如何界定变更范围；
* 何时添加或省略代码注释；
* 对安全问题应如何处理；以及
* 在宣布工作完成前运行测试等验证习惯。

默认情况下，一个自定义 output style 会丢弃所有这些内容，Claude Code 便会从软件工程师助手更多地变成一个通用助手。

**提示**：在编写自定义 output style 之前，先查看内置样式。**Proactive**、**Explanatory** 和 **Learning** 涵盖了最常见的需求（自主性、教学模式、协作式编码），无需你维护一个样式文件。

### 追加系统提示词

修改 output styles 的一个替代方案是 `append-system-prompt` 标志。修改 output style 文件可能会对 Claude 的行为产生巨大的、意料之外的变化，而 append 标志仅对原始系统提示词做加法。它不修改 Claude 的角色；只是向其默认角色添加指令。

它同样在调用时传入，且仅应用于该次调用，而不会作为文件跨会话持久化。

与其他传递指令的方法相比，追加系统提示词可能会带来更高的上下文成本。它会增加输入 token，不过提示词缓存会在会话中首次请求后降低这一成本。指示 Claude 使用更冗长或更长的风格也会增加输出 token。

**提示：** 追加系统提示词最适合用于添加特定的编码标准、输出格式或领域特定知识。请记住，追加系统提示词在遵循度上具有边际递减效应。一般来说，你用此方法提供的指令越多，Claude 遵循得就越不严格，尤其是当其中有任何指令相互矛盾时。

## 何时使用每种方法

如果你发现自己在做以下某件事，你或许应当考虑为你的指令换一个位置：

**在 CLAUDE.md 中写"每次 X，总是做 Y"。** 如果某个行为应当可靠地发生，比如每次编辑后运行 prettier 或完成时发送到 Slack，那就改用 `settings.json` 中的 hook。模型选择运行格式化工具，与格式化工具自动运行，是两回事。

**在 CLAUDE.md 中写"永远不要这样做"。** 当有某件事绝对不能发生时，用指令是错误的工具。Claude 大多数时候会遵循该指令，但当处于压力之下、身处长会话或含糊情境中、或由于任务中访问的文件里存在提示词注入时，模型可能无法遵循一条被提示的规则。真正的护栏需要是确定性的，而其执行方法是 [hooks](https://code.claude.com/docs/en/hooks) 和[权限](https://code.claude.com/docs/en/permissions)。一个 `PreToolUse` hook 可以检查一次调用并以退出码 2 阻断它。[**受管设置**](https://code.claude.com/docs/en/settings#managed-settings)则更进一步：它们由管理员部署，无法被用户的本地配置覆盖，是强制实施确定性、组织级护栏的唯一途径。

**在 CLAUDE.md 中写一段 30 行的流程。** 流程应归属于 skills。CLAUDE.md 用于 Claude 应始终持有的事实：构建命令、monorepo 布局、团队约定。一份部署运行手册或一份安全审查检查清单应存在于 `.claude/skills/` 中，其正文只在被调用时才载入。

**一条没有 paths 的 API 特定 rule。** 如果一条 rule 只适用于 `src/api/**`，用 `paths:` 限定它可使其在无关工作期间保持在上下文之外。一条未限定的 rule 在机制上等同于把内容放进 CLAUDE.md：始终载入，始终消耗 token。

**把个人偏好写入项目级的 CLAUDE.md 文件。** 所有基于文件的方法都有一个用户级对应版本，无论你身处哪个仓库，它都会为每次 Claude Code 会话载入。用本地文件存放个人偏好（比如始终使用语义化的提交信息）。把项目级文件留给那些团队通用但特定于某个代码库的偏好。

## 开始定制 Claude Code

你可以在我们的 [Claude Code 最佳实践](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md)文档中，找到更多充分发挥 Claude Code 的技巧与模式，从配置你的环境到跨并行会话扩展。

一旦你让其中几项运转起来，就可以把它们中的许多（skills、子智能体、hooks、output styles）打包为一个 [plugin](https://code.claude.com/docs/en/plugins)，从而在队友或项目之间共享一套连贯的配置。

*本文由 Anthropic 员工 Michael Segner 撰写。*

## 相关文章

探索更多面向使用 Claude 进行构建的团队的产品资讯与最佳实践。

* **Jun 30, 2026** · Claude Code — [Getting started with loops](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more/blog/getting-started-with-loops)
* **Mar 19, 2026** · Claude Code — [Product management on the AI exponential](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more/blog/product-management-on-the-ai-exponential)
* **Jul 7, 2026** · Product announcements — [Bringing Claude Code and Claude Cowork to government](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more/blog/bringing-claude-code-and-claude-cowork-to-government)
* **Jun 2, 2026** · Claude Code — [A harness for every task: dynamic workflows in Claude Code](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code)
