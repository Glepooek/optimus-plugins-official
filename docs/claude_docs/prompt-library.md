# 提示词库

> 可直接复制粘贴到 Claude Code 的提示词集合，按任务和角色分类标记。

来源：[code.claude.com/docs/en/prompt-library](https://code.claude.com/docs/en/prompt-library)

---

这是一个提示词库，供你复制到 Claude Code 中使用。用它来探索你尚未尝试过的工作方式，或在不知道从哪里开始时作为起点。

这些提示词汇集自 Anthropic 的各类指南，包括[常见工作流](https://code.claude.com/docs/en/common-workflows)、[最佳实践](https://code.claude.com/docs/en/best-practices)和[Anthropic 团队如何使用 Claude Code](https://claude.com/blog/how-anthropic-teams-use-claude-code)。它们是起点，而非脚本。展开任意提示词下的**为什么有效**，可了解其背后的模式，从而写出自己的版本。

---

## 阶段：探索（Discover）

### 入门（Onboard）

**熟悉新代码库**
```
give me an overview of this codebase: architecture, key directories, and how the pieces connect
```
> 描述你想了解什么，而非读哪些文件。Claude 自行探索项目并返回整体结构摘要。
> 💡 运行 `/init` 配置 `CLAUDE.md`，让 Claude 在每次会话都记住这些内容

---

### 理解（Understand）

**解释陌生代码**
```
explain what {path} does and how data flows through it. write it up as {format}
```
示例：`path` = `src/scheduler/queue.ts`，`format` = `an HTML page with a diagram, then open it in my browser`
> 指定文件并说明你想要什么格式的答案。可将 HTML 页面换成图表、要点或适合你学习方式的任何形式。

**找到某个行为发生的地方**
```
where do we {behavior}?
```
示例：`behavior` = `validate uploaded file types`
> 按行为搜索，而非文件名。即使你不知道文件叫什么或在哪个目录，也能找到。

**删除前检查依赖**
```
what would break if I deleted {target}?
```
示例：`target` = `the retryWithBackoff helper`
> 删除前先问一下。调用者和下游影响的列表告诉你这是一行代码的清理，还是需要协调的变更。

**追溯代码演变历史**
```
look through the commit history of {path} and summarize how it evolved and why
```
示例：`path` = `internal/auth/session.go`
> 当问题是"为什么"而非"是什么"时，指向提交历史。Claude 阅读日志和 blame，解释当前实现背后的决策。

**在动手前评估变更范围**（适合产品/设计）
```
which files would I need to touch to {change}?
```
示例：`change` = `add a dark mode toggle to settings`
> 在提交到路线图之前先评估工作量。文件列表告诉你是在改一个组件还是一个横切变更。

**向代码库提产品问题**（适合产品经理）
```
I am a {role}. walk me through what happens when a user {action}, from the UI down to the result
```
示例：`role` = `PM`，`action` = `clicks Export to PDF`
> 说明你的角色，让回答的深度更合适。Claude 直接从源代码解释产品实际做了什么，无需你去读代码。

---

## 阶段：设计（Design）

### 规划（Plan）

**动手前规划多文件变更**（适合产品/设计）
```
plan how to refactor the {target} to {goal}. list the files you would change, but don't edit anything yet
```
示例：`target` = `payment module`，`goal` = `support multiple currencies`
> 加上"先别编辑"将探索和变更分开，让你在任何代码移动前就能看到方案。

**通过访谈起草规格文档**（适合产品经理）
```
I want to build {feature}. interview me about implementation, UX, edge cases, and tradeoffs until we have covered everything, then write the spec to SPEC.md
```
示例：`feature` = `per-workspace rate limits`
> 让 Claude 来访谈你，而不是自己写规格。Claude 会提问直到需求完整，然后将结果写入文件。
> 💡 将访谈问题保存为 `/spec` skill，让每份规格都以同样的方式开始

**将会议记录转化为工单**（适合产品经理）
```
read {input} and write up the action items, then create a {tracker} ticket for each with acceptance criteria
```
示例：`input` = `@meeting-notes.md`，`tracker` = `Linear`
> 跳过转录步骤。Claude 从非结构化输入中提取行动项，通过 MCP 直接写入你的追踪器，让你审查工单而非会议记录。
> 💡 将此保存为 `/tickets` skill

**动手前梳理边缘情况**（适合设计/产品）
```
list the error states, empty states, and edge cases for {feature} that the design needs to cover
```
示例：`feature` = `the file upload flow`
> 问什么缺失，而非什么存在。Claude 列出快乐路径设计往往遗漏的错误状态、空状态和边缘情况。

---

### 原型（Prototype）

**将原型图转化为可交互原型**（适合设计/产品/营销）
```
here is a mockup. build a working prototype I can click through, matching the layout and states shown
```
*将原型图粘贴/拖入提示词，或用 @-mention 引用，然后发送*
> 可点击的原型能回答静态原型图无法回答的问题。将可运行的代码交给工程师，而不是在文档中解释交互。

**从截图实现并自我检查**（适合设计）
```
implement this design, then take a screenshot of the result, compare it to the original, and fix any differences
```
*将设计图粘贴/拖入提示词，或用 @-mention 引用*
> 这给了 Claude 一个验证循环：它渲染、与源图对比，并迭代，无需你逐一指出差距。
> 💡 使用 `/goal` 让 Claude 持续迭代直到截图匹配

---

## 阶段：构建（Build）

### 实现（Implement）

**遵循已有模式**
```
look at how {example} is implemented to understand the pattern, then build {new} the same way
```
示例：`example` = `the GitHub webhook handler`，`new` = `a Stripe webhook handler`
> 指向你已经喜欢的代码。没有参考时，Claude 默认通用最佳实践；有了参考，它会匹配代码库实际使用的约定。

**为未文档化的代码生成文档**（适合文档）
```
find {scope} without {format} comments and add them, matching the style already used in the file
```
示例：`scope` = `the public functions in src/auth/`，`format` = `JSDoc`
> 指定范围和格式。Claude 找到缺失的内容并匹配文件中已有的注释风格，让新文档读起来像原有内容。

**添加一个小的、明确定义的功能**
```
add a {endpoint} endpoint that returns {payload}
```
示例：`endpoint` = `/health`，`payload` = `the app version and uptime`
> 说明输入和输出，而非如何构建。Claude 找到类似代码所在的位置，并将你的代码添加在旁边。

**从头构建一个小型内部工具**（适合产品/设计/营销/文档）
```
create a {tool} using HTML, CSS, and vanilla JavaScript, then open it in my browser
```
示例：`tool` = `drag-and-drop Kanban board with three columns`
> 不需要项目、框架或构建步骤。描述工具并让 Claude 打开它，这样你立即就能看到它运行。

**从头到尾处理一个 Issue**
```
read issue #{issue}, implement the fix, and run the tests
```
示例：`issue` = `312`（需要 `gh` CLI 或 GitHub MCP）
> 给出 issue 编号，而非摘要。Claude 自己阅读完整工单，确保你可能忘记提到的需求都被涵盖，并在汇报前验证变更。

**在整个代码库中查找和更新文案**（适合设计/文档/营销）
```
find every place we say "{copy}" or a close variant, show me each one in context, then update them all to "{new}". leave tests and the changelog alone
```
示例：`copy` = `Sign up free`，`new` = `Start free trial`
> 要求查找变体并说明跳过什么。Claude 找到字面搜索会遗漏的措辞，并保留测试固件和历史记录不动。

**从历史样例起草文档**（适合文档/营销/产品）
```
read the {examples} in {folder} to learn the structure and voice, then draft a new one for {topic}
```
示例：`examples` = `privacy impact assessments`，`folder` = `legal/pia/`，`topic` = `the new analytics integration`
> 指向一个完成品文件夹，而非描述你的风格。Claude 从你已发布的内容中学习结构和语气，让初稿读起来像你写的。

---

### 测试（Test）

**编写测试、运行测试、修复失败**
```
write tests for {path}, run them, and fix any failures
```
示例：`path` = `app/parsers/feed.py`
> 把写、运行和修复放在一个请求里，让 Claude 无需停下来等待指令就能迭代。
> 💡 运行 `/init` 让 Claude 自动学习你的测试命令

**从测试驱动实现**
```
write tests for {feature} first, then implement it until they pass
```
示例：`feature` = `the password reset flow`
> 测试驱动开发：测试定义了工作何时完成，Claude 迭代实现直到通过。

**从覆盖率报告填补空白**
```
read {report} and add tests for the lowest-covered files until each is above {target}%
```
示例：`report` = `coverage/coverage-summary.json`，`target` = `80`
> 指向覆盖率报告，而非猜测什么没有测试。Claude 读取实际数字，为最需要的文件编写测试。
> 💡 将此设为 `/goal`，让 Claude 持续写测试直到覆盖率达到目标

---

### 重构（Refactor）

**在整个代码库中迁移一个模式**
```
migrate everything from {from} to {to}: identify every place that needs to change, then make the changes
```
示例：`from` = `the old logging API`，`to` = `the structured logger`
> 描述旧模式和新模式。先让 Claude 找出所有位置，意味着响应中会列出调用点，这样你可以检查没有遗漏。

**将代码移植到另一种语言**（适合团队）
```
port {source} to {target}, keeping the same {keep}
```
示例：`source` = `this Python module`，`target` = `Rust`，`keep` = `public API and test behavior`
> 说明要保留什么，而不只是目标语言。命名必须保持不变的 API 或行为，给 Claude 一个可以对照检查移植的契约。

**针对可衡量目标进行优化**（适合数据）
```
optimize {target} to bring {metric} from {current} down to under {goal}
```
示例：`target` = `the search query`，`metric` = `p95 latency`，`current` = `2s`，`goal` = `500ms`
> 给出指标和目标，Claude 就有了明确的完成定义。
> 💡 将此设为 `/goal`，让 Claude 持续测量和迭代直到达到数字

**修复精确的视觉 bug**（适合设计）
```
the {element} extends {amount} beyond the {container} on {viewport}. fix it.
```
示例：`element` = `login button`，`amount` = `20px`，`container` = `card border`，`viewport` = `mobile`
> 精确的视觉反馈得到精确的修复。说明确切的元素、尺寸和视口。
> 💡 添加预览工具让 Claude 自己截图验证修复效果

---

### 审查（Review）

**提交前审查你的变更**
```
review my uncommitted changes and flag anything that looks risky before I commit
```
> 在问题还容易修复时发现它们。Claude 完整阅读变更文件，而非只看 diff 行，所以能发现快速自我审查遗漏的问题。
> 💡 运行 `/review` 一键完成同样的检查

**审查一个 Pull Request**
```
review PR #{pr} and summarize what changed, then list any concerns
```
示例：`pr` = `247`（需要 `gh` CLI 或 GitHub MCP）
> Claude 在整个代码库上下文中进行审查，而非只看 diff。它阅读变更的代码及其调用的内容，捕获仅看 diff 会遗漏的问题。
> 💡 通过 Code Review 为每个 PR 开启此检查

**在应用前审查基础设施变更**（适合安全/运维）
```
here is my Terraform plan output. what is this going to do, and is anything here going to cause problems?
```
*将 plan 输出粘贴到提示词中，然后发送*
> Plan 输出密集且难以扫描。粘贴它可以让你在应用前得到一个通俗易懂的变更摘要。

**通过子智能体运行安全审查**（适合安全）
```
use a subagent to review {path} for security issues and report what it finds
```
示例：`path` = `src/api/`
> 子智能体在自己的上下文窗口中运行审计并汇报摘要，这样一次长时间的安全审查不会占满你的主会话。内置的通用子智能体无需额外配置即可处理此任务。

**发送前捕获问题**（适合营销/文档）
```
review {file} for {concerns} and list anything I should fix before it goes to {reviewer}
```
示例：`file` = `launch-post.md`，`concerns` = `unsupported claims, missing attributions, and brand-guideline issues`，`reviewer` = `legal`
> 在人工花费时间审阅之前先过一遍。说明你想检查的关注点，让审查有针对性，然后修复发现的内容，发送一个更干净的草稿。

---

### 引导（Steer）

**纠正错误方向**
```
that is not right: {feedback}. try a different approach
```
示例：`feedback` = `the function signature needs to stay backward-compatible`
> 说明 Claude 遗漏的约束，而非只是说它错了。具体的原因给 Claude 一个具体的约束来满足，而不是再次猜测。
> 💡 按 `Esc` 两次打开 rewind 菜单，恢复代码和对话，让重试从干净的状态开始

**缩小变更范围**
```
that is too much. keep only the changes to {scope} and undo your other edits
```
示例：`scope` = `the validation logic in src/forms/`
> 当方向正确但变更太宽泛时，让 Claude 保留其中一部分，而非撤销所有。明确的边界防止一个小修复变成大重构。

**将纠正转化为规则**
```
you keep {mistake}. add a rule to CLAUDE.md so this stops happening
```
示例：`mistake` = `using default exports when this project uses named exports`
> 聊天中的纠正不会与团队共享。项目 CLAUDE.md 中的规则在你提交后就共享了，Claude 在每次会话开始时都会读取它。
> 💡 打开 `/memory` 查看 Claude 写了什么

---

## 阶段：发布（Ship）

### Git

**解决合并冲突**
```
resolve the merge conflicts in this branch and explain what you kept from each side
```
> 说明你想要的状态，而非保留哪些标记。要求解释使合并可审查，而非黑盒。

**生成提交消息**
```
commit these changes with a message that summarizes what I did
```
> 让 Claude 从 diff 推导消息。它会匹配你仓库现有的提交风格。

**从工单开一个 Pull Request**
```
find the {tracker} ticket about {topic} and open a PR that implements it
```
示例：`tracker` = `Linear`，`topic` = `the login timeout`（需要 issue 追踪器 MCP）
> 跳过追踪器、编辑器和 GitHub 之间的上下文切换。一条提示词读取规格、进行变更并打开 PR。

---

### 发布（Release）

**从 git 历史起草发布说明**（适合产品/文档/营销）
```
compare {from} to {to} and draft release notes grouped by feature, fix, and breaking change
```
示例：`from` = `v2.3.0`，`to` = `v2.4.0`
> 给出两个参考点和你想要的结构。Claude 读取之间的提交日志，起草一份你可以编辑的 changelog。
> 💡 将此保存为 `/changelog` skill

**编写 CI 工作流**（适合运维）
```
write a GitHub Actions workflow that {steps} on every push to {branch}
```
示例：`steps` = `runs the tests and deploys to staging`，`branch` = `main`
> 描述何时运行以及做什么；YAML 会为你生成，并匹配你项目的构建和测试命令。

---

## 阶段：运营（Operate）

### 调试（Debug）

**找到并修复一个失败的测试**
```
the {test} test is failing, find out why and fix it
```
示例：`test` = `UserAuth`
> 描述症状；不需要知道哪个文件坏了。Claude 运行测试查看失败，追溯到源码并修复。

**调查已报告的错误**（适合运维）
```
users are seeing {symptom} on {where}. investigate and tell me what is going on
```
示例：`symptom` = `500 errors`，`where` = `/api/settings`
> 描述症状和位置；Claude 读取相关代码路径并追踪可能的原因。如果有的话，粘贴堆栈跟踪或日志。

**从根本修复构建错误**（适合运维）
```
here is a build error. fix the root cause and verify the build succeeds
```
*将错误输出粘贴到提示词中，然后发送*
> 要求根本原因和验证，防止只是压制错误而非修复的表面补丁。

---

### 事故处理（Incident）

**调查生产事故**（适合运维/安全）
```
{symptom}. check the logs, recent deploys, and config changes, then tell me the most likely cause
```
示例：`symptom` = `the checkout endpoint started returning 500s an hour ago`
> 列出要关联的证据来源，而非要采取的步骤。Claude 综合读取日志、git 历史和配置，缩小原因范围。
> 💡 通过 MCP 连接 Sentry 或你的日志存储

**从控制台截图诊断**（适合运维/数据）
```
here is a screenshot of {console}. walk me through why {resource} is failing and give me the exact commands to fix it
```
示例：`console` = `the GCP Kubernetes dashboard`，`resource` = `this pod`
*将截图粘贴/拖入提示词，或用 @-mention 引用*
> 云控制台告诉你问题所在，但不告诉你修复命令。Claude 读取截图，将仪表板翻译成要运行的 kubectl、gcloud 或 aws 命令。

**用自然语言查询日志**（适合安全/运维/数据）
```
show me all {events} for {scope} over {timeframe}. write the query, run it, and tell me what stands out
```
示例：`events` = `failed logins`，`scope` = `the auth service`，`timeframe` = `the past 24 hours`（需要数据仓库或日志存储 MCP）
> 提问而非写 SQL。Claude 构建查询，对你连接的日志运行它，并同时显示查询和结果，这样你可以检查运行了什么。

---

### 数据（Data）

**分析数据文件**（适合数据/产品/营销）
```
read {file}, summarize the key patterns, and write the results to {output}
```
示例：`file` = `@reports/q1-signups.csv`，`output` = `an HTML page with charts, then open it in my browser`
> 一次性问题不需要一次性脚本。指向项目文件夹中的文件，Claude 直接读取它，找出模式，并将输出写到你指定的地方。
> 💡 通过 MCP 连接数据源，而非导出文件

**从性能数据生成变体**（适合营销/数据）
```
read {file}, find the underperforming {items}, and generate {n} new variations that stay under {limit} characters
```
示例：`file` = `@ads-performance.csv`，`items` = `headlines`，`n` = `20`，`limit` = `90`
> 在开始时说明约束，让生成保持在限制范围内。Claude 读取指标，选择要替换的内容，并产生符合要求的备选方案。
> 💡 通过 MCP 连接广告平台，而非导出文件

---

### 自动化（Automate）

**将重复任务变成 skill**
```
create a /{name} skill for this project that {steps}
```
示例：`name` = `ship`，`steps` = `runs the linter and tests, then drafts a commit message`
> 说明一次步骤；作为命令复用。Claude 编写一个你团队中任何人都可以运行的 skill。

**为重复行为添加 hook**
```
write a hook that {action} after every {event}
```
示例：`action` = `runs prettier`，`event` = `edit to a .ts or .tsx file`
> Hook 使行为自动化，而不是每次都需要记得请求。描述触发器和动作，Claude 编写 hook 配置。

**用 MCP 连接工具**
```
set up the {server} MCP server so you can read my {data} directly
```
示例：`server` = `Sentry`，`data` = `error reports`
> 一次性连接数据源，而非每次会话都粘贴数据。MCP 设置后，当你询问时，Claude 直接从工具中读取。

**记录本次会话学到的内容**（适合产品/文档）
```
summarize what we did this session and suggest what to add to CLAUDE.md
```
> 在忘记前问一下。Claude 知道这次会话必须搞清楚什么，并提议 CLAUDE.md 条目，让下次会话以这些上下文开始。

---

## 这些提示词为什么有效

以上提示词共享几个模式。了解它们有助于你将这里的任何提示词适配到自己的任务。

**描述结果，而非步骤。** 说你想要什么，让 Claude 找文件。以下提示词无需命名任何文件路径就能生效：

```text
add rate limiting to the public API and make sure existing tests still pass
```

**给它一种自我检查的方式。** 在同一条提示词中要求运行、测试、对比或验证，这样 Claude 会迭代，而不是在一次尝试后就停下：

```text
write the migration, run it against the dev database, and confirm the schema matches
```

**指向参考资料。** 命名一个要匹配的已有文件、测试或模式，这样新代码与你已有的内容保持一致：

```text
add a settings page that follows the same layout as the profile page
```

**说明可量化的目标。** 当目标是性能或覆盖率时，给出指标和阈值，让完成标准清晰无歧义：

```text
get the bundle size under 200KB and show me what you removed
```

**提供原始材料。** 直接在提示词中粘贴错误、日志、截图和 plan 输出，或输入 `@` 引用文件。Claude 读取原始材料，而不是你对它的描述：

```text
why is the build failing? @build.log
```

**说明你想要什么格式的答案。** 命名格式、长度或受众，让解释适合你的使用方式。要将某种格式设为每次响应的默认值，设置[输出风格](https://code.claude.com/docs/en/output-styles)：

```text
explain how the payment retry logic works as an HTML page with a diagram, then open it in my browser
```

更多关于每个模式的内容，参见[最佳实践](https://code.claude.com/docs/en/best-practices)。

---

## 这些提示词的来源

这些提示词基于 Anthropic 已发布资源中的模式。每张卡片都链接到其来源：

- [常见工作流](https://code.claude.com/docs/en/common-workflows)：核心任务的分步指南
- [最佳实践](https://code.claude.com/docs/en/best-practices)：提示词模式和项目配置
- [Anthropic 团队如何使用 Claude Code](https://claude.com/blog/how-anthropic-teams-use-claude-code)：工程、产品、设计和数据团队的真实工作流，以及[法务](https://claude.com/blog/how-anthropic-uses-claude-legal)、[营销](https://claude.com/blog/how-anthropic-uses-claude-marketing)和[网络安全](https://claude.com/blog/how-anthropic-uses-claude-cybersecurity)的深度介绍
- [扩展智能体编程指南](https://resources.anthropic.com/hubfs/Scaling%20agentic%20coding%20across%20your%20organization.pdf)：企业采用指南

如需这些模式的视频演示，参见 Anthropic Academy 上的免费 [Claude Code in Action](https://anthropic.skilljar.com/claude-code-in-action) 课程。

---

## 相关资源

本页的提示词是起点。一旦某个提示词适用于你的项目，下一步就是让它可重复：将其保存为 [skill](https://code.claude.com/docs/en/skills)，让你团队中的任何人都可以将其作为 `/command` 运行；并将 Claude 学到的约定记录在 [CLAUDE.md](https://code.claude.com/docs/en/memory) 中，这样每次会话都以这些上下文开始，而不是让 Claude 重新学习。对于更大或更有风险的变更，[计划模式](https://code.claude.com/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)会在任何编辑发生前向你展示文件列表。

如果你在团队中引入 Claude Code，参见[管理](https://code.claude.com/docs/en/admin-setup)了解托管设置和策略，参见[成本与用量](https://code.claude.com/docs/en/costs)了解这些工作如何在你的计划中计费。
