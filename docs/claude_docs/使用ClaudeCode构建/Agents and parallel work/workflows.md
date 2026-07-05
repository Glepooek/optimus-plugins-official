---
source: https://code.claude.com/docs/en/workflows
---

# 使用动态工作流编排大规模子智能体

> 动态工作流通过 Claude 编写的脚本来编排多个子智能体，脚本可反复执行。适用于代码库审计、大规模迁移和交叉验证研究。

<!-- plan-availability: feature=workflows plans=pro,max,team,enterprise providers=all -->

> **注意：** 动态工作流需要 Claude Code v2.1.154 或更高版本，适用于所有付费套餐、Anthropic API 用户，以及 Amazon Bedrock、Google Cloud Vertex AI 和 Microsoft Foundry 用户。Pro 套餐用户可在 `/config` 的"动态工作流"行中开启。

动态工作流是一个 JavaScript 脚本，可大规模编排[子智能体](https://code.claude.com/docs/en/sub-agents)。Claude 根据你描述的任务编写脚本，运行时在后台执行脚本，同时保持会话响应。

当一个任务所需的智能体数量超出单次对话的协调能力，或你希望将编排逻辑固化为可读取和反复执行的脚本时，工作流是理想选择。典型场景包括：全代码库 bug 扫描、500 个文件的迁移、需要对信息来源进行交叉核验的研究问题，以及在确定方案前值得从多个独立视角起草并权衡的复杂计划。

本页内容：

* 判断[何时使用工作流](#when-to-use-a-workflow)而非子智能体或 skill
* 使用 `/deep-research` [运行内置工作流](#run-a-bundled-workflow)
* [让 Claude 为你的任务编写工作流](#have-claude-write-a-workflow)并保存
* 了解[工作流的运行机制](#how-a-workflow-runs)和[管理运行](#manage-runs)

## 何时使用工作流

[子智能体](https://code.claude.com/docs/en/sub-agents)、[skill](https://code.claude.com/docs/en/skills)、[智能体团队](https://code.claude.com/docs/en/agent-teams)和工作流都能执行多步骤任务，区别在于由谁持有计划：

| | 子智能体 | Skill | 智能体团队 | 工作流 |
| :--- | :--- | :--- | :--- | :--- |
| 是什么 | Claude 派发的工作者 | Claude 遵循的指令 | 监督同级会话的主智能体 | 运行时执行的脚本 |
| 由谁决定下一步 | Claude，逐轮决策 | Claude，按提示词决策 | 主智能体，逐轮决策 | 脚本 |
| 中间结果存在哪 | Claude 的上下文窗口 | Claude 的上下文窗口 | 共享任务列表 | 脚本变量 |
| 可重复的内容 | 工作者定义 | 指令内容 | 团队定义 | 编排逻辑本身 |
| 规模 | 每轮少量委派任务 | 与子智能体相同 | 少量长期运行的同级 | 每次运行数十至数百个智能体 |
| 中断处理 | 重新开始该轮 | 重新开始该轮 | 队友继续运行 | 可在同一会话中恢复 |

工作流将计划转移到代码中。使用子智能体、skill 和智能体团队时，Claude 是编排者：它逐轮决定下一步派发或分配什么，每个结果都落入上下文窗口。工作流脚本自身持有循环、分支和中间结果，因此 Claude 的上下文只需保存最终答案。

将计划放入代码还让工作流能够应用可重复的质量模式，而不仅仅是运行更多智能体：它可以让独立智能体对彼此的发现进行对抗性审查，或从多个角度起草计划并相互权衡，从而获得比单次处理更可靠的结果。

## 运行内置工作流

体验工作流最快的方式是运行 `/deep-research`——Claude Code 内置的工作流，用于跨多个来源调查问题。你会看到智能体在后台按阶段工作，同时你的会话保持自由状态，最终获得一份报告而非逐轮对话记录。

**步骤 1：运行工作流**

用你想要调查的问题运行 `/deep-research`。它会从多个角度展开网络搜索，抓取并交叉核验找到的来源，并生成一份带引用的报告。

```text theme={null}
/deep-research What changed in the Node.js permission model between v20 and v22?
```

**步骤 2：允许工作流**

Claude Code 会询问是否允许运行工作流。选择**是**继续。具体提示取决于你的权限模式，详见[在运行前审批计划](#approve-the-plan-before-it-runs)。

**步骤 3：查看进度**

运行在后台启动。随时运行 `/workflows`，用方向键选择运行，按 Enter 打开进度视图：

```text theme={null}
/workflows
```

视图显示每个阶段的智能体数量、token 总数和耗时。深入任意阶段可查看其智能体及每个智能体的发现。完整操作说明见[查看运行](#watch-the-run)。

你也可以在输入框下方的任务面板中查看进度：运行期间会显示一行进度摘要，按向下箭头聚焦后按 Enter 展开。

**步骤 4：阅读报告**

运行结束后，报告出现在会话中。报告注明每项结论的来源，未通过交叉核验的结论已被过滤。

要为自己的任务运行工作流，请[让 Claude 编写一个](#have-claude-write-a-workflow)，当运行结果符合预期后，你可以[将其保存](#save-the-workflow-for-reuse)为自己的命令。

### 内置工作流

Claude Code 内置了 `/deep-research` 工作流：

| 命令 | 功能 |
| :--- | :--- |
| `/deep-research <question>` | 从多个角度对问题展开网络搜索，抓取并交叉核验找到的来源，对每项结论进行投票，返回带引用的报告，不通过交叉核验的结论将被过滤。需要 [WebSearch 工具](https://code.claude.com/docs/en/tools-reference#websearch-tool-behavior)可用 |

你[保存的工作流](#save-the-workflow-for-reuse)同样成为命令，与内置命令一起出现在 `/` 自动补全中。

### 查看运行

工作流在后台运行，智能体工作期间会话保持响应。随时运行 `/workflows` 列出正在运行和已完成的工作流，选择一个打开进度视图。

```text theme={null}
/workflows
```

进度视图显示每个阶段的智能体数量、token 总数和耗时。页脚列出各操作的快捷键：

| 快捷键 | 操作 |
| :--- | :--- |
| `↑` / `↓` | 选择阶段或智能体 |
| `Enter` 或 `→` | 深入选中的阶段，再深入智能体可查看其提示词、近期工具调用和结果 |
| `Esc` | 返回上一级 |
| `j` / `k` | 智能体详情溢出时在其中滚动 |
| `p` | 暂停或恢复运行 |
| `x` | 停止选中的智能体，焦点在运行上时停止整个工作流 |
| `r` | 重启选中的正在运行的智能体 |
| `s` | 将运行的脚本[保存](#save-the-workflow-for-reuse)为命令 |

## 让 Claude 编写工作流

有两种方式让 Claude 为你的任务编写工作流：

* 在提示词中[请求工作流](#ask-for-a-workflow-in-your-prompt)，用自己的话说或加入关键词 `ultracode`，Claude 就会为该任务编写工作流。
* [让 Claude 通过 ultracode 自主决策](#let-claude-decide-with-ultracode)：设置 `/effort ultracode`，Claude 会为会话中每个实质性任务规划工作流。

你也可以直接运行已有的工作流命令：[内置工作流](#bundled-workflows)如 `/deep-research`，或你[保存的工作流](#save-the-workflow-for-reuse)。

### 在提示词中请求工作流

要在不改变会话算力等级的情况下将单个任务作为工作流运行，在提示词中加入关键词 `ultracode`。用自己的话请求，例如"使用工作流"或"运行一个工作流"同样有效：Claude 将直接请求视为等同的确认。v2.1.160 之前的版本触发词是 `workflow`；自然语言请求在两个版本中均有效。

```text theme={null}
ultracode: audit every API endpoint under src/routes/ for missing auth checks
```

Claude Code 会在输入中高亮该关键词，Claude 将为任务编写工作流脚本而非逐轮处理。如果你并不想启动工作流，在 macOS 上按 `Option+W`，在 Windows 和 Linux 上按 `Alt+W` 可取消本次提示词的高亮，或在光标紧接高亮关键词之后时按退格键。要完全阻止关键词触发，可在 `/config` 中关闭"Ultracode 关键词触发"。

运行结果符合预期后，你可以[将其保存为命令](#save-the-workflow-for-reuse)。

如果你已用其他方式构建了编排器，例如一组子智能体提示词文件夹或一个分发工作的 skill，可以让 Claude 参考它，要求编写实现相同功能的工作流。

### 让 Claude 通过 ultracode 自主决策

Ultracode 是 Claude Code 的一项设置，将 `xhigh` [推理算力](https://code.claude.com/docs/en/model-config#adjust-effort-level)与自动工作流编排相结合。开启后，Claude 会为每个实质性任务规划工作流，而无需你每次请求。

```text theme={null}
/effort ultracode
```

开启 ultracode 后，Claude 自主判断任务是否需要工作流。单个请求可能触发连续多个工作流：一个用于理解代码，一个用于执行更改，一个用于验证结果。由于适用于会话中的每个任务，每次请求消耗的 token 更多、耗时更长。

Ultracode 仅在当前会话有效，新会话启动时重置。回到日常工作时用 `/effort high` 降档。它适用于支持 `xhigh` [算力](https://code.claude.com/docs/en/model-config#adjust-effort-level)的模型；其他模型的 `/effort` 菜单不提供此选项。

### 在运行前审批计划

在 CLI 中，每次运行的提示会显示规划的阶段及以下选项：

* **是，运行**：启动运行
* **是，且以后不再询问此项目中的 `<名称>`**：启动，并从此跳过该项目中此工作流的提示
* **查看原始脚本**：决定前阅读脚本
* **否**：取消

`Ctrl+G` 在编辑器中打开脚本。`Tab` 允许在运行开始前调整提示词。

是否显示此提示取决于你的[权限模式](https://code.claude.com/docs/en/permission-modes)：

| 权限模式 | 何时提示 |
| :--- | :--- |
| 默认、接受编辑 | 每次运行，除非已对该项目中的该工作流选择**是，且以后不再询问** |
| 自动 | 仅首次启动。任何**是**会将同意记录至用户设置，后续启动无需提示。开启 ultracode 时完全跳过 |
| 绕过权限、`claude -p`、Agent SDK | 从不提示，运行立即启动 |

在桌面应用中，审批卡片显示工作流名称、阶段列表和 token 用量提示，操作选项为**一次**、**始终**和**拒绝**。进度视图出现在"后台任务"侧边栏。

你的权限模式只控制上述启动提示。工作流派发的子智能体始终以 `acceptEdits` 模式运行，并继承你的[工具允许列表](https://code.claude.com/docs/en/settings#permission-settings)，与会话模式无关。文件编辑自动通过审批。

不在允许列表中的 shell 命令、网络请求和 MCP 工具仍可能在运行中途提示你。若要避免在长时间运行中被打断，请在启动前将智能体所需的命令添加到允许列表。

在 `claude -p` 和 Agent SDK 中没有可交互的对象，因此工具调用遵循你配置的权限规则，无需交互确认。

### 保存工作流以便复用

当 Claude 为你会重复执行的任务编写了工作流时，你可以将该次运行的脚本保存为命令。这样，每次在每个分支上运行的审查流程都会执行相同的编排逻辑。

运行 `/workflows`，选择要保留的运行，按 `s`。在保存对话框中，Tab 在两个保存位置之间切换：

* 项目中的 `.claude/workflows/`：与所有克隆该仓库的人共享
* 主目录中的 `~/.claude/workflows/`：在所有项目中可用，仅对你可见

按 Enter 保存。工作流在后续会话中以 `/<名称>` 运行，两个位置均适用。

在包含多个 `.claude/` 目录的 monorepo 中，你可以将工作流与其适用的包放在一起。从 v2.1.178 起，保存到项目位置时会写入工作目录到仓库根目录之间距离最近的已有 `.claude/workflows/` 目录；若不存在则写入仓库根目录。项目工作流也从该路径上的每个 `.claude/workflows/` 加载，同名时 Claude Code 运行距离工作目录最近的那个。

若项目工作流与个人工作流同名，运行项目工作流。

### 向已保存的工作流传入参数

已保存的工作流可以通过 `args` 参数接受输入。脚本将其作为名为 `args` 的全局变量读取。在调用时传入研究问题、目标路径列表或配置对象，无需每次运行都修改脚本。

以下提示词用一组 issue 编号运行已保存的工作流：

```text theme={null}
> Run /triage-issues on issues 1024, 1025, and 1030
```

Claude 将列表作为结构化数据传入，因此脚本可以直接对 `args` 调用数组和对象方法，无需手动解析。若省略 `args`，脚本内该全局变量为 `undefined`。

## 工作流的运行机制

工作流运行时在隔离环境中执行脚本，与你的对话分离。中间结果保存在脚本变量中，不会落入 Claude 的上下文。

每次运行都会将脚本写入 `~/.claude/projects/` 下会话目录中的文件。运行启动时 Claude 会收到路径，你可以随时查看。你可以打开该文件阅读 Claude 编写的编排逻辑，将其与上次运行的脚本对比，或编辑后让 Claude 基于修改版本重新启动。

运行时随运行进展追踪每个智能体的结果，这正是运行可[在同一会话中恢复](#resume-after-a-pause)的原因。

### 行为与限制

运行时执行以下约束：

| 约束 | 原因 |
| :--- | :--- |
| 运行中无法接收用户输入 | 只有智能体权限提示可以暂停运行。若需在阶段间审批，请将每个阶段作为独立工作流运行 |
| 工作流本身不能直接访问文件系统或 shell | 智能体负责读写和执行命令，脚本只负责协调智能体 |
| 最多 16 个并发智能体，CPU 核心有限的机器上更少 | 限制本地资源使用 |
| 每次运行最多 1,000 个智能体 | 防止失控循环 |

## 管理运行

运行启动后，可通过 `/workflows` 视图或展开输入框下方任务面板中的进度行进行管理。

### 暂停后恢复

停止运行后可以恢复：已完成的智能体直接返回缓存结果，其余智能体继续实时运行。在 `/workflows` 中选择已暂停的运行并按 `p` 恢复，或让 Claude 以相同脚本重新启动工作流。

恢复功能仅在同一个 Claude Code 会话内有效。若在工作流运行期间退出 Claude Code，下一个会话将重新启动该工作流。

### 成本

工作流会派发大量智能体，因此单次运行消耗的 token 可能明显多于对话方式处理同一任务。运行的计费和速率限制与其他会话一样计入你的套餐用量。

在投入大型任务之前，可先用小规模测试评估花销：选一个目录而非整个仓库，或提一个具体问题而非宽泛问题。`/workflows` 视图在运行过程中显示每个智能体的 token 用量，你可以随时在此停止运行而不丢失已完成的工作。运行时的[智能体上限](#behavior-and-limits)限制了单次运行可派发的智能体数量，从而控制失控脚本的成本。

工作流中的每个智能体都使用你会话的模型，除非脚本将某个阶段路由到其他模型。控制模型成本的方法：

* 在大型运行前检查 `/model`，如果你平时会切换到更小的模型处理日常工作
* 描述任务时让 Claude 对不需要最强模型的阶段使用更小的模型

### 关闭工作流

工作流适用于 CLI、桌面应用、IDE 扩展、使用 `claude -p` 的[非交互模式](https://code.claude.com/docs/en/headless)以及 [Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview)。关闭设置在所有界面上通用。

为自己关闭工作流：

* 在 `/config` 中关闭"动态工作流"，跨会话持久生效。
* 在 `~/.claude/settings.json` 中设置 `"disableWorkflows": true`，跨会话持久生效。
* 设置 `CLAUDE_CODE_DISABLE_WORKFLOWS=1`，在启动时读取，在设置处即可生效。

为整个组织关闭工作流，可在[托管设置](https://code.claude.com/docs/en/server-managed-settings)中设置 `"disableWorkflows": true`，或在 [Claude Code 管理员设置](https://claude.ai/admin-settings/claude-code)页面使用开关。

关闭工作流后，内置工作流命令不可用，`ultracode` 关键词不再触发运行，`ultracode` 从 `/effort` 菜单中移除。

## 相关资源

* [并行运行智能体](https://code.claude.com/docs/en/agents)：对比子智能体、智能体视图、智能体团队和工作流
* [创建自定义子智能体](https://code.claude.com/docs/en/sub-agents)：工作流编排的工作者原语
* [管理成本](https://code.claude.com/docs/en/costs)：多智能体运行如何计入用量限制
