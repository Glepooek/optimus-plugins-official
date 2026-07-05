# 并行运行智能体

> 对比 Claude Code 同时处理多个任务的几种方式：子智能体、智能体视图、智能体团队和动态工作流。

来源：[code.claude.com/docs/en/agents](https://code.claude.com/docs/en/agents)

---

[子智能体](https://code.claude.com/docs/en/sub-agents)、[智能体视图](https://code.claude.com/docs/en/agent-view)、[智能体团队](https://code.claude.com/docs/en/agent-teams)和[动态工作流](https://code.claude.com/docs/en/workflows)各自以不同的方式并行化工作。正确的选择取决于你是想亲自参与每次对话、将任务交出并稍后检查，还是让 Claude 为你协调一组工作者。

| 方式 | 提供什么 | 适用场景 |
|:-----|:---------|:---------|
| [子智能体](https://code.claude.com/docs/en/sub-agents) | 在一个会话内的委托工作者，在自己的上下文中执行辅助任务并返回摘要 | 辅助任务会用大量搜索结果、日志或文件内容淹没你的主对话，而你之后不会再引用这些内容 |
| [智能体视图](https://code.claude.com/docs/en/agent-view) | 一个用于分发和监控后台运行会话的界面，通过 `claude agents` 打开。研究预览版 | 你有多个独立任务，想将它们交出去、一目了然地检查状态，并只在某个任务需要你时才介入 |
| [智能体团队](https://code.claude.com/docs/en/agent-teams) | 多个协调会话，共享任务列表并支持智能体间消息传递，由主智能体管理。实验性功能，默认禁用 | 你希望 Claude 将项目拆分成多个部分、分配任务并保持工作者同步 |
| [动态工作流](https://code.claude.com/docs/en/workflows) | 运行大量子智能体并交叉验证结果的脚本，适用于规模太大无法逐轮协调或需要多轮处理的工作 | 任务超出了几个子智能体的处理能力，或者你希望发现的结果相互验证：全代码库审计、500 个文件的迁移、交叉验证的研究，或从多个角度起草的计划 |

在每种方式中，工作者都是 Claude 会话。如果需要接入其他工具，可以通过 [MCP server](https://code.claude.com/docs/en/mcp) 将其暴露给 Claude。

另有两个工具支持这类工作，但它们本身并不是运行智能体的方式：

- [Worktrees](https://code.claude.com/docs/en/worktrees) 为每个会话提供独立的 git checkout，使并行会话永远不会编辑相同的文件。可用于你自己手动运行的会话。智能体视图会自动将每个分发的会话放入独立的 worktree，你派生的子智能体也可以各自拥有一个。
- [`/batch`](https://code.claude.com/docs/en/commands) 是一个 [skill](https://code.claude.com/docs/en/skills)，让 Claude 将一次大型变更拆分为 5 到 30 个 worktree 隔离的子智能体，每个都会开一个 pull request。这是子智能体和 worktree 的打包使用方式，而非单独的协调风格。

另有几个功能可以让 Claude 在不需要你驱动每一步的情况下运行，但它们解决的是不同于跨智能体拆分工作的问题：

- [后台 bash 命令](https://code.claude.com/docs/en/interactive-mode#background-bash-commands)：在不阻塞对话的情况下运行一条 shell 命令，不会派生智能体。
- [分支子智能体](https://code.claude.com/docs/en/sub-agents#fork-the-current-conversation)：继承你的完整对话上下文而不是从头开始的子智能体。这是派生子智能体的一种方式，而非单独的界面。
- [例程（Routine）](https://code.claude.com/docs/en/routines)：在 Anthropic 的云端按计划运行一个会话，而非在你的本地机器上并行运行。

> 注意：同时运行多个会话或子智能体会成倍增加 token 用量。详见 [成本说明](https://code.claude.com/docs/en/costs)。

---

## 选择方式

正确的方式取决于谁来协调工作、工作者是否需要相互通信，以及他们是否编辑相同的文件：

- **谁来协调工作？**
  - Claude 在一次对话内委托并收集结果：[子智能体](https://code.claude.com/docs/en/sub-agents)
  - 你交出独立任务并稍后检查：[智能体视图](https://code.claude.com/docs/en/agent-view)
  - Claude 规划、分配并监督一组工作者：[智能体团队](https://code.claude.com/docs/en/agent-teams)，实验性功能，默认禁用
  - 由脚本而非 Claude 的逐轮判断来持有计划：[动态工作流](https://code.claude.com/docs/en/workflows)。参见[工作流与子智能体及 skill 的对比](https://code.claude.com/docs/en/workflows#when-to-use-a-workflow)

- **工作者需要相互通信吗？** 子智能体将结果汇报回派生它们的对话，智能体视图的会话只向你汇报。智能体团队中的队员共享任务列表并直接互发消息。

- **任务是否涉及相同文件？** 使用 [worktrees](https://code.claude.com/docs/en/worktrees) 隔离工作。子智能体和你自己手动运行的会话都可以各使用一个独立的 worktree。智能体团队不将队员隔离在各自的 worktree 中，因此需要[划分工作范围](https://code.claude.com/docs/en/agent-teams#avoid-file-conflicts)，让每个队员负责不同的文件集。

---

## 检查正在运行的工作

检查正在运行的工作所用的命令，取决于你使用的方式：

- 对于后台会话，`claude agents` 打开[智能体视图](https://code.claude.com/docs/en/agent-view)：一个显示所有会话、其状态以及哪些会话需要你输入的界面。
- 对于当前会话中的子智能体，`/agents` 打开一个面板，其中包含列出实时子智能体的 **Running** 标签，以及用于[创建和编辑自定义子智能体](https://code.claude.com/docs/en/sub-agents#use-the-%2Fagents-command)的 **Library** 标签。尽管名称相似，但这与 `claude agents` 是独立的。
- 对于在当前会话后台运行的任何内容，`/tasks` 列出每个项目，并允许你检查、附加或停止它。
- 对于动态工作流，`/workflows` 列出正在运行和已完成的任务、每个任务所处的阶段，以及已完成的智能体数量。

如需桌面端查看所有会话，参见[桌面应用中的并行会话](https://code.claude.com/docs/en/desktop#work-in-parallel-with-sessions)。

---

## 深入了解

以下每篇指南介绍一种方式的设置和配置：

- [创建自定义子智能体](https://code.claude.com/docs/en/sub-agents)：定义可复用的专家智能体，并控制它们可以使用哪些工具。
- [使用智能体视图管理智能体](https://code.claude.com/docs/en/agent-view)：分发会话、观察其状态，并在需要时接入。
- [编排智能体团队](https://code.claude.com/docs/en/agent-teams)：设置主智能体和队员，分配任务并审查他们的工作。
- [编排动态工作流](https://code.claude.com/docs/en/workflows)：运行打包好的工作流，或让 Claude 编写一个能运行大量子智能体并相互验证结果的工作流。
- [使用 worktrees 运行并行会话](https://code.claude.com/docs/en/worktrees)：在隔离的 checkout 中启动 Claude，控制哪些内容被复制进来，并在之后清理。
