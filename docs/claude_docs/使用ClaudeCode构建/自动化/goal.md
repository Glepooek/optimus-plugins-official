# 让 Claude 持续朝目标推进

> 通过 `/goal` 设置一个完成条件，Claude 会在多个回合中持续工作，直到该条件被满足。

来源：[code.claude.com/docs/en/goal](https://code.claude.com/docs/en/goal)

---

> **注意：**
> `/goal` 需要 Claude Code v2.1.139 或更高版本。

`/goal` 命令设置一个完成条件，Claude 会朝着这个条件持续工作，而不需要你每一步都手动提示。每个回合结束后，一个小型快速模型会检查该条件是否已经满足。如果尚未满足，Claude 会开始新的一轮，而不是把控制权交还给你。一旦条件满足，goal 会自动清除。

在以下场景中使用 goal，适用于有可验证终态的大量工作：

* 将一个模块迁移到新 API，直到所有调用点都能编译通过且测试通过
* 按照设计文档实现功能，直到所有验收标准都满足
* 将一个大文件拆分为多个聚焦的模块，直到每个模块都在大小预算之内
* 处理一个带标签的 issue 积压队列，直到队列清空

## 对比让会话持续运行的几种方式

三种方法都能让当前会话在多次提示之间持续运行。根据"下一轮应该由什么触发"来选择：

| 方式 | 下一轮何时开始 | 何时停止 |
| :--- | :--- | :--- |
| `/goal` | 上一轮结束后 | 模型确认条件已满足 |
| [`/loop`](https://code.claude.com/docs/en/scheduled-tasks#run-a-prompt-repeatedly-with-%2Floop) | 时间间隔到达后 | 你停止它，或 Claude 判断工作已完成 |
| [Stop hook](https://code.claude.com/docs/en/hooks-guide#prompt-based-hooks) | 上一轮结束后 | 你自己的脚本或提示词来判断 |

`/goal` 和 Stop hook 都会在每一轮结束后触发。`/goal` 是一个会话范围的快捷方式：你输入一个条件，它仅在当前会话内生效。Stop hook 存在于你的设置文件中，适用于其作用范围内的每一个会话，既可以运行脚本做确定性检查，也可以用提示词做模型评估的检查。

[自动模式](https://code.claude.com/docs/en/auto-mode-config)本身只会在单个回合内自动批准工具调用，但不会开启新的一轮。Claude 会在它判断工作已完成时停止。`/goal` 增加了一个独立的评估器，在每一轮结束后检查你设定的条件，因此完成与否由一个全新的模型来决定，而不是执行工作的那个模型。两者是互补的：自动模式去除了每次工具调用的确认，而 `/goal` 去除了每一轮结束时的确认。

> **提示：**
> 上述方式都是让当前会话持续运行。你也可以调度独立于任何已打开会话的工作，比如夜间测试或早晨的例行检查。参见[调度选项](https://code.claude.com/docs/en/scheduled-tasks#compare-scheduling-options)了解云端例行任务和桌面端定时任务。

## 使用 `/goal`

每个会话同一时间只能有一个 goal 处于激活状态。同一个命令根据参数的不同，分别承担设置、检查、清除三种功能。

### 设置一个 goal

运行 `/goal` 并在后面跟上你希望满足的条件。如果已经有一个 goal 处于激活状态，新的 goal 会替换它。

```text theme={null}
/goal all tests in test/auth pass and the lint step is clean
```

设置 goal 会立即开始一轮，并把条件本身当作指令。你不需要再单独发送一条提示词。goal 激活期间，状态栏会显示一个 `◎ /goal active` 指示器，展示 goal 已经运行了多久。

每一轮结束后，评估器会返回一个简短的理由，说明条件是否满足。最近一次的理由会显示在状态视图和对话记录中，让你了解 Claude 接下来要朝哪个方向努力。

> **注意：**
> goal 会持续运行，直到条件满足或你运行 `/goal clear`。不带参数运行 `/goal` 可以查看目前已经花费的轮次和 token 数。

### 写出有效的条件

[评估器](#how-evaluation-works)会根据 Claude 在对话中已经展现出的内容来判断你的条件。它不会自己运行命令或读取文件，所以要把条件写成 Claude 自身的输出就能证明的东西。"`test/auth` 中的所有测试都通过"之所以有效，是因为 Claude 会运行测试，而结果会出现在对话记录中供评估器读取。

一个能在多轮之间站得住脚的条件通常具备：

* **一个可衡量的终态**：一个测试结果、一个构建退出码、一个文件数量、一个空队列
* **一个明确的检查方式**：Claude 应该如何证明，比如"`npm test` 退出码为 0"或"`git status` 是干净的"
* **重要的约束**：任何在达成目标过程中不应改变的东西，比如"没有其他测试文件被修改"

条件最长可以有 4,000 个字符。

要限制 goal 运行多久，可以在条件中加入轮次或时间的从句，比如 `or stop after 20 turns`。Claude 每一轮都会汇报相对于这个从句的进度，评估器会根据对话记录来判断。

### 查看状态

不带参数运行 `/goal` 可以查看当前状态。

```text theme={null}
/goal
```

如果有一个 goal 处于激活状态，状态会显示：

* 条件内容
* 已经运行了多久
* 已经评估了多少轮
* 当前的 token 花费
* 评估器最近一次给出的理由

如果当前没有激活的 goal，但会话中此前已经达成过一个，状态会显示已达成的条件，以及它的持续时间、轮次数和 token 花费。

### 清除一个 goal

运行 `/goal clear` 可以在条件满足之前移除一个激活中的 goal。

```text theme={null}
/goal clear
```

`stop`、`off`、`reset`、`none`、`cancel` 都可以作为 `clear` 的别名。运行 `/clear` 开启新对话也会一并移除任何激活中的 goal。

### 恢复会话时保留激活中的 goal

如果一个会话结束时仍有 goal 处于激活状态，当你用 `--resume` 或 `--continue` 恢复该会话时，这个 goal 会被恢复。条件会被保留，但轮次计数、计时器和 token 花费基准都会在恢复时重置。已经达成或已被清除的 goal 不会被恢复。

### 非交互式运行

`/goal` 可以在[非交互模式](https://code.claude.com/docs/en/headless)、[桌面应用](https://code.claude.com/docs/en/desktop)以及通过[远程控制](https://code.claude.com/docs/en/remote-control)中使用。用 `-p` 设置 goal 会在单次调用中把整个循环运行至完成：

```bash theme={null}
claude -p "/goal CHANGELOG.md has an entry for every PR merged this week"
```

用 Ctrl+C 中断进程可以在条件满足之前停止一个非交互式的 goal。

## 评估工作原理

`/goal` 是对一个会话范围的[提示词式 Stop hook](https://code.claude.com/docs/en/hooks#prompt-based-hooks)的封装。每次 Claude 结束一轮，条件和目前为止的对话内容都会被发送给你配置的[小型快速模型](https://code.claude.com/docs/en/model-config)（默认是 Haiku）。该模型会返回一个是/否的判断和一个简短的理由。"否"会告诉 Claude 继续工作，并把这个理由作为下一轮的指导。"是"会清除 goal，并在对话记录中记下一条已达成的记录。

评估器运行在你的会话所配置的提供方上。它不会调用工具，所以只能根据 Claude 已经在对话中展现出的内容来判断。

> **注意：**
> 评估所消耗的 token 会计入你的提供方所配置的小型快速模型，相比主回合的花费通常可以忽略不计。

## 使用条件

`/goal` 只能在你已经接受信任对话框的工作区中运行，因为评估器是 hooks 系统的一部分。当[`disableAllHooks`](https://code.claude.com/docs/en/hooks#disable-or-remove-hooks)在任何设置层级被设置，或者[`allowManagedHooksOnly`](https://code.claude.com/docs/en/settings#hook-configuration)在托管设置中被设置时，`/goal` 也同样不可用。这两种情况下，命令都会告诉你原因，而不是悄无声息地什么都不做。

## 参见

* [用 `/loop` 重复运行一条提示词](https://code.claude.com/docs/en/scheduled-tasks#run-a-prompt-repeatedly-with-%2Floop)：按时间间隔重复运行，而不是运行到条件满足为止
* [提示词式 hooks](https://code.claude.com/docs/en/hooks-guide#prompt-based-hooks)：当你需要自定义评估逻辑时，编写自己的 Stop hook
* [自动模式](https://code.claude.com/docs/en/auto-mode-config)：自动批准工具调用，让每一轮 goal 都能无人值守运行
* [调度对比](https://code.claude.com/docs/en/scheduled-tasks#compare-scheduling-options)：独立于任何已打开会话来调度工作
