# 如何在 Claude Code 中使用 Subagents

> 原文：https://claude.com/blog/subagents-in-claude-code
> 副标题：Claude Code subagents 实用指南：何时有效、如何指挥，以及判断委派是否值得的关键信号。
> 分类：Claude Code | 日期：2026年4月7日 | 阅读时间：5分钟

---

Claude Code 能很好地处理复杂的多步骤项目，但长时间的会话会积累大量负担。每次文件读取、每次旁枝探索、每个未完成的思路都停留在上下文窗口中，拖慢响应速度并推高 token 消耗。

试想在一个大型 TypeScript monorepo 中开发新功能。主要工作是实现本身，但旁枝任务不断涌现：追踪某个现有服务如何处理认证、找到日期格式化的共用工具函数、确认设计系统中是否已有接近需求的组件。这些任务都不需要完整的项目上下文，放在主会话里处理只会引入噪音。

如果能并行运行这些任务呢？这就是 **subagents** 的价值所在。

Subagent 是一个独立的 Claude 实例，拥有自己的上下文窗口。它接受任务，完成工作，只返回结果。可以把 subagents 理解为 Claude Code 会话中的"浏览器标签页"：一个可以追踪旁枝而不丢失主线的地方。

本文讨论何时使用 subagents、如何调用，以及何时不值得增加这层开销。

---

## 什么是 Subagent？

Subagents 是独立运行的自治 agent，拥有各自的上下文窗口。Claude 派生 subagent 时，该助手独立工作：读取文件、探索代码或进行修改。任务完成后，subagent 只将相关结果返回给主对话。

每个 subagent 全新启动，不携带对话历史或已调用 skills 的包袱。多个 subagents 可并行运行，各自可拥有不同权限：研究型 subagent 可能只有只读权限，而实现型 subagent 可获得完整编辑能力。

Claude Code 内置了几种 subagent 类型，包括：
- **通用 Agent** – 处理复杂的多步骤任务
- **Plan Agent** – 在提出实施策略前先研究代码库
- **Explore Agent** – 经过优化的快速只读代码搜索

Claude Code 通常会自动派生 subagents 来处理分配的任务。也可以明确指挥这种行为，并定义可复用的专家 agent，让 Claude 自动委派给它们。知道何时使用 subagents，才能让这个功能真正发挥价值。

---

## 何时应该使用 Subagents？

某些类别的工作明显受益于 subagent 委派。学会识别这些场景，能让功能效果大幅提升。

### 研究密集型任务

当理解某样东西的工作原理是修改它的前提时，subagent 可以探索代码库并返回摘要，而不是把数十个文件塞进对话。

- **信号：** 获取上下文需要读取数十个文件
- **收益：** 主对话保持干净，到来的是综合整理后的发现，而非原始内容

### 多个独立任务

修复多个文件中的错误、更新多个组件中的模式，或进行互不依赖的修改时，并行 subagents 能更快完成任务。

- **信号：** 子任务之间没有依赖关系
- **收益：** 三个 subagents 同时工作，通常完成时间不超过处理一个的时间

### 需要全新视角

需要对实现进行无偏见审查时，subagent 能提供一个干净的起点，因为它不继承主对话中的假设、上下文或思维盲区。

- **信号：** 需要在不受对话历史影响的情况下进行验证
- **收益：** 更干净、更客观的反馈

> **Pro-tip：** `/clear` 命令同样能重置上下文和对话历史，提供类似的无偏见视角，但代价是完全丢失那段历史。Subagent 能在保持主对话完整的同时实现同样的全新视角。

### 提交前验证

在最终确定改动之前，独立的 subagent 可以验证实现是否过拟合于测试或遗漏了边界情况。

- **信号：** 提交代码前需要第二意见
- **收益：** 捕获对代码的熟悉度可能掩盖的问题

### 流水线工作流

当任务有明确阶段（如设计、实现、测试）时，每个阶段都受益于专注的注意力。

- **信号：** 有明确交接点的顺序阶段
- **收益：** 每个 subagent 专注于自己的阶段，不受其他阶段上下文的干扰

> **Pro-tip：** 当任务需要探索 10 个以上文件，或涉及 3 个以上独立工作块时，这是强烈信号——应该引导 Claude 使用 subagents。

---

## 如何指挥 Subagent 的使用

调用 subagents 有多种方式，从简单对话到自动化工作流各有不同。正确的起点取决于工作流，复杂度可以随着模式的明确逐步叠加。

### 对话调用

最灵活的方式是直接在对话中要求 Claude 使用 subagents。适用于所有 Claude Code 界面：终端、VS Code、JetBrains、网页和桌面应用。

能可靠触发 subagents 的自然语言模式包括：
- "Use a subagent to explore how authentication works in this codebase"
- "Have a separate agent review this code for security issues"
- "Research this in parallel. Check the API routes, database models, and frontend components simultaneously"
- "Spin up subagents to fix these TypeScript errors across the different packages"

明确说明至关重要。指定范围、在任务独立时要求并行执行、描述期望的输出。以下是一个有效的提示结构：

```
Use subagents to explore this codebase in parallel:

1. Find all API endpoints and summarize their purposes
2. Identify the database schema and relationships
3. Map out the authentication flow

Return a summary of each, not the full file contents.
```

这个提示有效，因为它清晰定义了三个独立任务，明确要求并行执行，并指定了输出格式。Claude 能理解意图并派生相应的 subagents。

对话调用的有效技巧：
- **明确界定任务范围。** "探索支付系统如何工作"优于"探索一切"
- **明确要求并行化。** 说"这些可以并行运行"或"同时处理全部三个"
- **指定返回内容。** 摘要、具体发现或建议——命名输出格式有助于 Claude 准确交付
- **需要无偏见分析时要求全新上下文。** "Use a subagent that does not see our previous discussion" 能确保干净的评估

> **Pro-tip：** Subagent 运行时间较长时，**Ctrl+B** 可将其发送到后台。对话可以继续，结果完成后会自动浮现。**/tasks** 命令显示后台运行中的任务。

### 自定义 Subagents

当同类 subagent 被反复请求（安全审查者、测试编写者、文档校对者）时，可以将其定义为自定义 subagent。

Claude 会在任务与其 description 匹配时自动委派，无需提示。

自定义 subagents 以 Markdown 文件形式存放在：
- 项目级：`.claude/agents/`（与团队共享）
- 用户级：`~/.claude/agents/`（跨所有项目可用）

每个 subagent 有自己的系统提示、工具权限，还可以指定独立的模型。最简单的创建方式是 `/agents` 命令，它会交互式地引导完成设置，并能根据描述生成初稿。也可以手动编写文件，例如：

```yaml
---
name: security-reviewer
description: Reviews code changes for security vulnerabilities,
injection risks, auth issues, and sensitive data exposure.
Use proactively before commits touching auth, payments, or user data.
tools: Read, Grep, Glob
model: sonnet
---

You are a security-focused code reviewer. Analyze the provided
changes for:
- SQL injection, XSS, and command injection risks
- Authentication and authorization gaps
- Sensitive data in logs, errors, or responses
- Insecure dependencies or configurations

Return a prioritized list of findings with file:line references
and a recommended fix for each. Be critical. If you find nothing,
say so explicitly rather than inventing issues.
```

配置好后，Claude 会自动将匹配的工作路由到该 subagent。也可以按名称调用："Have the security-reviewer look at the staged changes."

自定义 subagents 适用于：
- 需要专家 agent 供 Claude 在任务匹配时自动委派
- 工作受益于严格限定范围的系统提示和受限工具集
- 配置需要在团队间共享或跨项目复用

> **Pro-tip：** `description` 字段是 Claude 决定何时委派的依据。要具体描述触发条件，而不仅仅是能力。"Reviews code for security issues before commits" 的路由效果优于 "security expert"。

完整的配置参考，包括权限模式以及项目级和用户级 subagents 的交互方式，请参阅 [Claude Code subagents 文档](https://docs.anthropic.com/en/docs/claude-code/sub-agents)。

### CLAUDE.md 指令

自定义 subagents 定义了"谁是专家"，CLAUDE.md 文件定义了"何时使用他们的规则"。

如果每次代码审查都应该通过只读 subagent 进行，或每个架构问题都应该先触发研究，CLAUDE.md 就是存放这些策略的地方。

Claude 在每次对话开始时都会读取它，因此行为在会话间和团队成员间保持一致，无需任何人记得提醒。

CLAUDE.md 适合存放 subagent 指令的场景：
- 代码审查始终应使用只读 subagents
- 项目有 Claude 应遵循的特定研究模式
- 需要跨团队成员和会话保持一致行为

以下是一个在特定条件下触发 subagent 的 CLAUDE.md 示例：

```markdown
## 代码审查标准

被要求审查代码时，始终使用只有 READ-ONLY 权限的 subagent
（仅限 Glob、Grep、Read）。审查内容必须包括：
- 安全漏洞
- 性能问题
- 与 /docs/architecture.md 中项目模式的一致性

以带有 file:line 引用的优先级排序列表形式返回发现。
```

有了上面的 CLAUDE.md，每次代码审查请求都会自动使用定义好的模式，无需每次指定。

关于 CLAUDE.md 文件的更多内容，请参阅[为代码库自定义 Claude Code：设置 CLAUDE.md 文件](https://docs.anthropic.com/en/docs/claude-code/memory)以及 [Claude Code CLAUDE.md 文件文档](https://docs.anthropic.com/en/docs/claude-code/memory)。

### Skills

对于反复运行的复杂多步骤工作流，skills 提供了可复用的接口。在 `.claude/skills/` 中定义一次，然后用 `/skill-name` 调用，或让 Claude 在任务与其 description 匹配时自动加载。

Skills 与 CLAUDE.md 文件的区别在于作用范围：CLAUDE.md 文件始终加载，影响每次交互；而 skill 按需加载——要么被明确调用，要么 Claude 将当前任务与 skill 的 `description` 字段匹配后加载。这使 skills 成为存放"随时可用但不需要应用于每个提示"的工作流的合适位置。

Skills 适用于：
- 某些操作需要定期运行
- 不同团队成员需要访问同一个复杂操作
- 在团队中标准化某些任务的执行方式

以下是一个用于全面代码审查的 deep-review skill 示例：

```markdown
# .claude/skills/deep-review/SKILL.md

---
name: deep-review
description: Comprehensive code review that checks security,
performance, and style in parallel. Use when reviewing staged
changes before a commit or PR.
---

Run three parallel subagent reviews on the staged changes:

1. Security review - check for vulnerabilities, injection risks,
   authentication issues, and sensitive data exposure
2. Performance review - check for N+1 queries, unnecessary iterations,
   memory leaks, and blocking operations
3. Style review - check for consistency with project patterns
   documented in /docs/style-guide.md

Synthesize findings into a single summary with priority-ranked issues.
Each issue should include the file, line number, and recommended fix.
```

`/deep-review` 按需触发三部分 subagent 分析。因为 description 提到了"在提交前审查暂存改动"，Claude 在相关上下文出现时也可以自动调用这个 skill。

Skill 是一个目录，不是单个文件。除了 SKILL.md，它还可以包含 Claude 填写的模板、展示预期格式的示例输出，或 Claude 作为工作流一部分执行的脚本。旧版 `.claude/commands/` 格式是单个平面文件，所有内容都必须写在提示词本身里。

关于在 Claude Code 中使用 skills 的更多内容，请参阅 [Claude Code skills 文档](https://docs.anthropic.com/en/docs/claude-code/skills-tutorial)。

### Hooks

Hooks 是用户定义的 Shell 命令、HTTP 端点或 LLM 提示，在 Claude Code 生命周期的特定节点自动执行。Hooks 可以基于事件自动化 subagent 工作流，无需手动调用。

Hooks 适用于：
- 每次提交前都应自动审查
- 安全检查应该自动运行，无需任何人记得提问
- CI 式质量门控应属于本地开发流程

以下是一个 Stop hook 示例，阻止 Claude 在测试通过前结束其轮次：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-tests.sh"
          }
        ]
      }
    ]
  }
}
```

`.claude/hooks/check-tests.sh` 脚本内容：

```bash
#!/bin/bash
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# 防止无限循环——如果本轮已经阻止过一次，放行
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

if ! npm test --silent > /dev/null 2>&1; then
  jq -n '{
    decision: "block",
    reason: "Tests are failing. Run `npm test` to see the failures and fix them before finishing."
  }'
  exit 0
fi

exit 0
```

Claude 结束轮次时，Stop 事件触发。脚本运行测试套件——如果测试失败，返回带有 `decision: "block"` 和 `reason` 的 JSON。Claude Code 读取后不允许 Claude 停止，并将原因作为指令反馈到对话中，要求继续工作。顶部的 `stop_hook_active` 守卫防止无限循环：如果 Claude 已经因为上一次 stop-hook 阻断而在继续运行，脚本会允许它退出。

Hooks 是 subagent 编排中最自动化的方式。对话调用或 CLAUDE.md 指令是更好的起点；随着工作流趋于成熟，再引入 hooks。

完整的 hooks 配置，请参阅 [Claude Code 高级用户自定义：如何配置 hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) 或 [Claude Code hooks 文档](https://docs.anthropic.com/en/docs/claude-code/hooks)。

---

## Subagents 的实践模式

以下模式展示了 subagent 指挥应用于常见场景的具体方式。

### 先研究，再实现

在不熟悉的代码中添加功能时，先将研究委派给 subagent，能让实现讨论有的放矢，而不是一边探索一边摸索：

```
Before I implement user notifications, use a subagent to research:
- How are emails currently sent in this codebase?
- What notification patterns already exist?
- Where should new notification logic live based on the current architecture?

Summarize findings, then we'll plan the implementation together.
```

到来的是综合整理后的摘要，而非二十个原始上下文文件，实现讨论从坚实的基础起步。

### 并行修改

当相同模式需要在多个文件中更新时，并行 subagents 完成更快且保持专注：

```
Use parallel subagents to update the error handling in these files:
- src/api/users.ts
- src/api/orders.ts
- src/api/products.ts

Each should follow the pattern established in src/api/auth.ts.
Work on all three simultaneously.
```

三个 subagents 并行工作，完成时间大约相当于处理一个文件的时间。每个专注于自己的文件，不受其他文件上下文的干扰或引发不一致。

### 独立审查

在实现了复杂的东西之后，来自未受实现过程影响的 subagent 的验证，能捕获熟悉度掩盖的问题：

```
Use a fresh subagent with read-only access to review my implementation
of the payment flow. It should not see our previous discussion.
I want an unbiased review.

Check for: security vulnerabilities, unhandled edge cases, and error
handling gaps. Be critical.
```

审查 subagent 在不了解权衡取舍、不了解被否决的方案、不了解既有假设的情况下评估代码。这种外部视角能发现主对话可能遗漏的问题。

### 流水线工作流

对于多阶段任务，将各阶段链接起来并在阶段间明确交接，能让每个阶段保持专注：

```
Let's build this feature as a pipeline:

1. First subagent: Design the API contract and write it to docs/api-spec.md
2. Second subagent: Implement the backend endpoints based on that spec
3. Third subagent: Write integration tests for the implementation

Each stage should complete before the next begins. Use the output
files as the handoff mechanism between stages.
```

使用流水线工作流，任务的每个阶段都获得专注的上下文。设计 subagent 不受实现细节干扰，实现 subagent 从干净的规格工作，测试 subagent 独立评估结果。

---

## 何时不应使用 Subagents？

尽管 subagents 是有用的功能，但它们带有开销。每个 subagent 启动自己的上下文、消耗 token，并在开发者和工作之间增加一层间接性。当上下文隔离、并行性或全新视角真正有帮助时，这些代价是值得的。

对于较小或高度顺序的任务，留在主对话中通常更简单：

- **顺序依赖的工作。** 当第二步需要第一步的完整输出，第三步需要前两步时，由单个会话处理这条链通常比让 subagents 通过文件传递状态更简洁
- **同文件编辑。** 两个 subagents 并行编辑同一个文件是制造冲突的良方。此类情况，将紧密耦合的修改保持在一个上下文窗口中
- **小型任务。** 对于快速修复或专注的问题，委派的开销超过了收益。直接在主对话中提问或操作即可
- **专家 agent 过多。** 为所有事情都定义一个自定义 subagent 很诱人，但用太多选项淹没 Claude 会让自动委派变得不可靠。大多数团队选择少数几个界定清晰的 agent，而非庞大的阵容
- **需要 agents 之间互相协调的工作。** Subagents 向主对话汇报，但无法互相通信。对于 subagents 需要通信的任务，使用 [Agent Teams](https://docs.anthropic.com/en/docs/claude-code/agent-teams)。Agent Teams 让 subagents 在独立会话间协调，这使其更重量级、更昂贵

关于何时使用 subagents 与 Agent Teams 的更多指引，请参阅 [Claude Code agent teams 文档](https://docs.anthropic.com/en/docs/claude-code/agent-teams)。

前文描述的信号（需要第二意见、子任务间缺乏依赖、需要大量研究）能清楚地表明何时委派给 subagent 是值得的。

---

## 先对话，后自动化

Subagents 在被刻意使用时才能充分发挥价值。Claude 提供的自动调用很有帮助，但知道何时委派研究、并行化工作、请求全新视角，能产生比随机应变更好的结果。

使用 subagents 时，从对话提示开始。注意哪些请求反复出现，随着这些模式逐渐清晰，再建立自动化。

目标是让 subagent 委派变得毫不费力，让你的注意力停留在真正重要的工作上。
