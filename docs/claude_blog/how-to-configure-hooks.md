# Claude Code 高级用户定制：如何配置 Hook

学习如何配置 Claude Code Hook，以自动化重复任务、强制执行项目规则，并向编程会话注入动态上下文。

> **来源：** [Claude Blog - Claude Code power user customization: How to configure hooks](https://claude.com/blog/how-to-configure-hooks)
> **发布日期：** 2025 年 12 月 11 日
> **分类：** Claude Code | 产品：Claude Code | 阅读时长：5 分钟

---

即便是流畅的 Claude Code 工作流，随着时间推移也会积累摩擦点。每次 Claude 写入文件后，Prettier 需要手动运行。每次运行 `npm test`，都会弹出同一个权限确认框。每次会话开始，都要把同样的项目样板上下文粘贴到第一条消息里。

好消息是？Hook 能消除这些摩擦点。Hook 是你可以配置的触发器，在特定动作的前后触发，让你能够将自定义逻辑、脚本和命令直接注入 Claude 的操作流程。

本文面向已熟悉 Claude Code 基础知识的开发者，介绍高级配置方法。读完本文，你将理解八种 Hook 类型、各自的适用场景、配置方式，以及出错时的调试方法。让我们开始吧。

---

## 一、什么是 Hook？

Hook 是一种自定义 Shell 命令，当 Claude Code 会话中的目标事件触发时（例如 Claude 即将写入文件，或你提交了一条提示词），它就会自动执行。

你可以为各种场景配置 Hook：拦截动作使其在执行前接受检查、注入智能体上下文、自动化审批，或在操作发生前将其阻止。

Hook 通过 JSON 结构配置在你的设置文件中，包含事件名称、匹配器（用于过滤哪些工具触发该 Hook）以及要运行的命令。Hook 在你的本地环境中以你的用户权限执行，通过 stdin 接收触发事件的信息，并通过退出码和 stdout 进行反馈通信。这让你无需修改工具本身，就能对 Claude Code 的行为进行精确控制。

---

## 二、为什么在 Claude Code 中使用 Hook？

Hook 解决三类问题：

**第一，消除重复的手动步骤。** 无需每次文件变更后手动运行格式化工具，PostToolUse Hook 会自动处理。无需第一百次审批 `npm test`，PermissionRequest Hook 会自动通过。

**第二，自动强制执行项目特定规则。** 你可以在危险命令执行前将其阻止，在写入前验证文件路径，或确保命名规范得到遵守。这些保护措施每次都会执行，而不是仅在你记得检查时才生效。

**第三，无需手动操作即可注入动态上下文。** SessionStart Hook 可以将当前 git 状态和 TODO 列表提供给 Claude。UserPromptSubmit Hook 可以将你的 Sprint 优先级附加到每条请求中。Claude 始终掌握最新信息，无需你重复说明。

---

## 三、Claude Code Hook 类型及适用场景

Claude Code 提供八种 Hook 事件，覆盖会话的完整生命周期——从启动到工具执行再到完成。每种 Hook 在特定时刻触发，让你对自动化运行时机有精确控制。选择合适的 Hook 取决于你想完成的目标。

### Hook 速览

| Hook | 触发时机 | 常见用途 |
|------|---------|---------|
| PreToolUse | 工具执行前 | 阻止危险命令、验证文件路径、自动审批安全操作 |
| PermissionRequest | 权限对话框弹出前 | 自动审批测试命令、阻止访问敏感文件 |
| PostToolUse | 工具完成后 | 运行格式化工具、触发 Lint 检查、记录文件变更 |
| PreCompact | 上下文压缩前 | 备份会话记录、保留重要决策 |
| SessionStart | 会话开始或恢复时 | 注入 git 状态、加载 TODO 列表、设置环境上下文 |
| Stop | Claude 完成响应时 | 验证任务完成情况、运行测试、生成摘要 |
| SubagentStop | 子智能体完成时 | 验证子智能体输出、触发后续动作 |
| UserPromptSubmit | 你提交提示词时 | 注入 Sprint 上下文、验证请求、添加动态上下文 |

---

### PreToolUse

这是最常用的 Hook，在 Claude 选择要使用的工具之后、工具实际执行之前触发。你的脚本可以检查计划中的操作，并使用匹配器过滤哪些工具触发此 Hook，然后批准、阻止、请求用户确认，或修改参数。

这个 PreToolUse Hook 示例在文件写入执行之前进行评估。Claude 根据指定标准审查计划中的操作，并可以根据提示词逻辑批准、阻止或标记问题：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/validate-file-path.sh"
          }
        ]
      }
    ]
  }
}
```

**PreToolUse 适用场景：**
- 阻止危险的 Bash 命令，如 `rm -rf` 或强制推送
- 自动审批安全的重复操作，减少权限确认疲劳
- 在写入前验证文件路径，防止意外覆盖
- 修改工具输入，注入项目特定的默认值

---

### PermissionRequest

当 Claude 通常会显示权限对话框时触发。此 Hook 拦截你本会看到确认提示的时刻，让你的脚本决定是允许、拒绝还是继续询问用户：

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "Bash(npm test*)",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/validate-test-command.sh"
          }
        ]
      }
    ]
  }
}
```

这个示例自动审批任何以 `npm test` 开头的 Bash 命令。匹配器模式可以包含参数以实现更精细的控制。

**PermissionRequest 适用场景：**
- 自动审批每次会话运行数十次的测试命令
- 阻止对生产配置文件的写入访问
- 允许对特定目录的读操作无需提示
- 拒绝匹配危险模式的任何命令

---

### PostToolUse

在工具成功完成后立即触发。你的脚本接收已发生事件的信息（包括工具输出），使用匹配器过滤哪些工具触发它。

这个 PostToolUse 示例对 Claude 写入或编辑的任何文件运行 Prettier。匹配器中的管道符表示对 Write 和 Edit 工具都触发：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write \"$CLAUDE_TOOL_INPUT_FILE_PATH\""
          }
        ]
      }
    ]
  }
}
```

**PostToolUse 适用场景：**
- 每次文件写入后运行 Prettier、Black 或 gofmt，强制执行格式化
- 将所有文件修改记录到审计追踪
- 代码变更后触发 Lint 检查并显示警告
- 当特定操作完成时发送通知

---

### PreCompact

在 Claude 压缩对话上下文以释放空间之前触发。压缩操作会汇总对话的较早部分，这意味着某些细节会丢失。此 Hook 让你有机会在压缩发生前保留信息。

这个 PreCompact 示例在自动压缩前备份会话记录。匹配器可以是 `"auto"` 或 `"manual"`，以便区分自动压缩和用户触发的压缩事件：

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/backup-transcript.sh"
          }
        ]
      }
    ]
  }
}
```

**PreCompact 适用场景：**
- 在汇总前将完整会话记录备份到文件
- 提取并保存重要决策或代码片段
- 记录会话里程碑供后续审查

---

### SessionStart

在 Claude Code 启动新会话或恢复已有会话时触发。脚本输出的任何内容都会被添加到对话上下文中，因此 Claude 从一开始就已加载这些信息：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "git status --short && echo '---' && cat TODO.md"
          }
        ]
      }
    ]
  }
}
```

每次会话开始时，Claude 就已了解当前的 git 状态和 TODO 列表。stdout 会自动成为上下文。

**SessionStart 适用场景：**
- 向 Claude 提供当前 git 分支和最近提交
- 加载 TODO 列表或 Sprint 待办事项的内容
- 注入环境特定的配置详情

---

### Stop

在 Claude 完成响应、通常会等待你下一次输入时触发。你的脚本可以检查 Claude 生成的内容，并判断任务是否真正完成。脚本可以返回带有 `"continue": true` 的 JSON 以让 Claude 继续工作，这对多步骤工作流很有用：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review whether the task is complete. If all requirements are met, respond with 'complete'. If work remains, respond with 'continue' and specify what still needs to be done."
          }
        ]
      }
    ]
  }
}
```

**Stop 适用场景：**
- 强制 Claude 持续工作直到清单上的所有项目完成
- 在认为任务完成前验证测试是否通过
- 在会话结束时触发摘要生成
- 在停止前检查生成的代码是否能编译

---

### SubagentStop

此 Hook 在通过 Task 工具创建的子智能体完成时触发。工作方式与 Stop 相同，但专门在子智能体完成动作时触发（而非主智能体）。SubagentStop 的配置结构与 Stop Hook 一致：

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate the subagent's output. Verify the task was completed correctly and the results meet quality standards. If the output is satisfactory, respond with 'accept'. If issues exist, respond with 'reject' and explain what needs to be fixed."
          }
        ]
      }
    ]
  }
}
```

**SubagentStop 适用场景：**
- 验证子智能体输出是否满足质量标准
- 根据子智能体结果触发后续动作
- 记录子智能体活动以用于调试或审计

---

### UserPromptSubmit

在你提交提示词、Claude 处理之前触发。脚本通过 stdout 输出的任何内容都会与你的提示词一起添加到 Claude 的上下文中，这使得 UserPromptSubmit 非常适合动态注入 Claude 应该考虑的信息。

在这个示例中，每次你提交提示词时，Claude 都会收到你的 Sprint 上下文文件的内容。这让 Claude 始终了解当前优先事项，而无需你重复说明：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cat ./current-sprint-context.md"
          }
        ]
      }
    ]
  }
}
```

**UserPromptSubmit 适用场景：**
- 随每条提示词注入当前 Sprint 上下文或项目优先级
- 在提示词到达 Claude 前进行验证
- 根据内容阻止某些类型的请求
- 添加动态上下文，如最近的错误日志或测试结果

---

## 四、配置与文件位置

Hook 存储在三个层级的 JSON 设置文件中：

- **项目级 Hook**：存放在仓库内的 `.claude/settings.json`，可与团队共享
- **用户级 Hook**：存放在 `~/.claude/settings.json`，适用于你的所有项目
- **本地项目 Hook**：存放在 `.claude/settings.local.json`，用于不想提交的个人配置

项目级设置优先于用户级设置。此外还有面向组织控制的企业管理策略设置。完整详情请参阅 [Claude Code 设置文档](https://code.claude.com/docs/en/settings)。

> **小提示：** 这与你可以为 Claude 操作设置精细权限的文件相同，可在项目、用户或本地层级设置。例如，你可以明确允许 Claude 读取某个目录中的所有文件，这样就不必每次审批；或者阻止对敏感文件的任何修改。

---

## 五、匹配器语法

匹配器用于过滤哪些工具可以触发你的 Hook，**仅适用于 PreToolUse、PostToolUse 和 PermissionRequest Hook**。

**简单字符串匹配**按预期工作：`"Write"` 仅匹配 Write 工具：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```

**管道符语法**让你匹配多个工具：`"Write|Edit"` 对两者都触发；**通配符**匹配所有工具：`"*"` 或空字符串匹配所有工具。

> **注意：** 匹配器区分大小写，`"bash"` 不会匹配 Bash 工具。

**参数模式**如 `"Bash(npm test*)"` 可匹配特定命令参数。**MCP 工具模式**遵循 `"mcp__memory__.*"` 格式用于模型上下文协议工具。

---

## 六、输入、输出与结构化响应

### Hook 接收什么

所有 Hook 通过 stdin 接收包含会话信息和事件特定数据的 JSON。通用字段包括：`session_id`、`transcript_path`、`cwd`、`permission_mode` 和 `hook_event_name`。此外，工具相关的 Hook 还会接收 `tool_name` 和 `tool_input`。这些数据让你的脚本能够做出有依据的响应决策。

### Hook 如何响应

**退出码**决定基本结果：
- 退出码 `0`：成功，stdout 要么被处理为 JSON，要么被添加到上下文
- 退出码 `2`：阻断性错误，stderr 成为错误消息，操作被阻止
- 其他退出码：非阻断性错误，stderr 在详细模式下显示

**结构化 JSON 响应**可实现更精细的控制，字段包括：
- `decision`：`approve`、`block`、`allow` 或 `deny`
- `reason`：展示给 Claude 的说明
- `continue`：用于 Stop Hook，强制继续执行
- `updatedInput`：在执行前修改工具参数

---

## 七、环境与执行

Hook 可以访问环境变量，包括：
- `CLAUDE_PROJECT_DIR`：项目根目录路径
- `CLAUDE_CODE_REMOTE`：在 Web 环境中为 `true`
- `CLAUDE_ENV_FILE`：用于 SessionStart Hook 持久化变量

Shell 中的标准环境变量也可访问。

其他注意事项：
- Hook 默认超时为 **60 秒**，可按 Hook 单独配置
- 当多个 Hook 匹配一个事件时，它们**并行运行**
- 相同的命令会被**自动去重**

---

## 八、安全注意事项

Hook 以你的用户权限执行任意 Shell 命令。Claude Code 包含一项保护措施：直接编辑 Hook 配置文件需要在 `/hooks` 菜单中审查后才生效，防止恶意代码在你不知情的情况下向配置中添加 Hook。

> **小提示：** 在任何环境中运行命令前，请评估风险。配置 Hook 时，建议遵循以下良好实践：验证并清理来自 stdin 的输入；为 Shell 变量加引号以防注入；使用脚本的绝对路径；避免处理 `.env` 或凭证等敏感文件。

---

## 九、调试与测试

Claude Code 将所有内容记录到会话记录文件中，提供对工具调用和响应的可见性，无需任何额外设置。每个 Hook 都会接收一个 `transcript_path` 字段，指向包含完整会话历史的 JSONL 文件。

你可以使用 SessionStart Hook 记录每个会话记录的位置：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"Session: \" + .transcript_path' >> ~/.claude/sessions.log"
          }
        ]
      }
    ]
  }
}
```

然后实时追踪该会话记录，观察 Claude 的工作过程：

```bash
tail -f /path/to/transcript.jsonl | jq .
```

### Hook 专项调试

对于 Hook 专项调试，在你的 Hook 脚本中添加日志。会话记录文件会显示 Claude 做了什么，但不会显示你的 Hook 为何采取批准或阻止操作。你可以用一个小型 Bash 脚本来包装工具并记录额外信息：

**`log-wrapper.sh`：**

```bash
#!/bin/bash
LOG=~/.claude/hooks.log
INPUT=$(cat)

TOOL=$(echo "$INPUT" | jq -r '.tool_name // "n/a"')
EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // "n/a"')

echo "=== $(date) | $EVENT | $TOOL ===" >> "$LOG"

echo "$INPUT" | "$1"
CODE=$?

echo "Exit: $CODE" >> "$LOG"
exit $CODE
```

这个小型包装脚本将 stdin 捕获到变量中，记录时间戳和工具名称，然后将输入管道传输到你的实际工具。写好 `log-wrapper.sh` 后，在 Hook 中将其添加到工具调用之前：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "log-wrapper.sh your-tool-command.py"
          }
        ]
      }
    ]
  }
}
```

> **小提示：** 更多调试技巧，请查看 [Claude Code 调试文档](https://code.claude.com/docs/en/debugging)。

---

## 十、构建你自己的 Hook

从一个能解决工作流中实际摩擦点的简单 Hook 开始。PostToolUse 格式化 Hook 是一个不错的起点，因为反馈直接且可见。成功之后，根据学到的经验逐步扩展。

完整的参考文档（包括所有可用字段和高级模式），请参阅[官方 Hooks 文档](https://code.claude.com/docs/en/hooks)。

Hook 让你能够将 Claude Code 塑造成符合你工作流的形态，而不是让你的工作流去适应工具。投入时间配置 Hook，每次会话都会有所回报。
