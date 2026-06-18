# Superpowers Skills 使用场景指南

本文档覆盖 `superpowers` 插件中全部 14 个 skill 的触发时机、核心规则和典型场景。

**调用格式：** `/superpowers:<skill-name>`

---

## 目录

- [技能全景图](#技能全景图)
- [阶段一：设计](#阶段一设计)
  - [brainstorming](#brainstorming)
  - [writing-plans](#writing-plans)
- [阶段二：工作区准备](#阶段二工作区准备)
  - [using-git-worktrees](#using-git-worktrees)
- [阶段三：执行](#阶段三执行)
  - [subagent-driven-development](#subagent-driven-development)
  - [executing-plans](#executing-plans)
  - [dispatching-parallel-agents](#dispatching-parallel-agents)
- [阶段四：质量保障](#阶段四质量保障)
  - [test-driven-development](#test-driven-development)
  - [systematic-debugging](#systematic-debugging)
  - [requesting-code-review](#requesting-code-review)
  - [receiving-code-review](#receiving-code-review)
  - [verification-before-completion](#verification-before-completion)
- [阶段五：收尾](#阶段五收尾)
  - [finishing-a-development-branch](#finishing-a-development-branch)
- [元技能](#元技能)
  - [using-superpowers](#using-superpowers)
  - [writing-skills](#writing-skills)
- [标准工作流链路](#标准工作流链路)

---

## 技能全景图

```
需求 ──► 设计 ──► 工作区 ──► 执行 ──► 验证 ──► 收尾
          │                   │        │
       brainstorm          TDD/debug  code-review
       writing-plans       subagent   verification
                           parallel   receiving-review
```

每个阶段都有专属 skill。**不能跳过**——跳过设计直接写代码，跳过验证直接合并，都是 superpowers 明确禁止的。

---

## 阶段一：设计

### brainstorming

**触发时机：** 一切创造性工作开始之前——写新功能、改行为、做架构决策。

**核心规则（硬门控）：** 在设计被用户批准之前，**不得写任何代码、不得调用任何实现 skill**。

**流程：**
1. 探索项目上下文（文件、最近提交）
2. 一次只问一个澄清问题
3. 提出 2-3 个方案并附权衡分析
4. 逐节展示设计，获得用户确认
5. 将设计文档写入 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` 并提交
6. 调用 `writing-plans` 进入实现阶段

**典型场景：**

```
用户：给订单系统加一个退款功能

正确流程：
  /superpowers:brainstorming
  → 探索现有订单代码
  → 问：退款是全额还是部分？
  → 问：需要审批流吗？
  → 提出三个方案（同步/异步/第三方代扣）
  → 写设计文档
  → 调用 writing-plans
```

**陷阱：** "这个功能很简单，不需要 brainstorming"——这是最常见的理由，也是 skill 明确点名的反模式。简单功能的设计文档可以很短，但必须写。

---

### writing-plans

**触发时机：** 有了经过批准的设计文档（来自 brainstorming）或明确的需求规格，准备开始实现。

**核心规则：** 计划要细到"每步 2-5 分钟"粒度，让零上下文的工程师也能逐步执行。

**计划文档头部（必须包含）：**

```markdown
# [功能名称] 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** [一句话描述目标]
**Architecture:** [2-3 句描述方案]
**Tech Stack:** [关键技术栈]
```

**粒度示例（正确）：**

```markdown
- [ ] 写失败的单元测试：RefundService.ProcessRefund 返回错误当金额超限
- [ ] 运行测试，确认它失败
- [ ] 实现 ProcessRefund 的最小代码让测试通过
- [ ] 运行测试，确认通过
- [ ] 提交：feat(refund): add amount limit validation
```

**保存路径：** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`

**典型场景：** brainstorming 结束后自动跳转到此 skill；或接收到 PRD/需求文档后直接使用。

---

## 阶段二：工作区准备

### using-git-worktrees

**触发时机：** 开始功能开发之前，或执行实现计划之前。

**核心规则：** 先检测是否已在隔离工作区，再决定是否新建。优先使用平台原生工具（如 `EnterWorktree`），没有原生工具才用 `git worktree add`。

**检测逻辑：**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
# GIT_DIR != GIT_COMMON → 已在 worktree 中，跳过创建
```

**典型场景：**

```
场景 A：需要同时处理 hotfix 和新功能
  → 为新功能创建 worktree，不影响 hotfix 分支

场景 B：实验性重构，不确定方向
  → 在 worktree 中探索，随时可丢弃

场景 C：执行多任务并行计划
  → 每个独立 agent 在独立 worktree 中操作，避免冲突
```

---

## 阶段三：执行

### subagent-driven-development

**触发时机：** 有实现计划、任务基本独立、且在当前会话中执行。

**核心规则：** 每个任务分配一个全新的 subagent（无上下文污染），任务完成后做**两阶段 review**：先检查是否符合规格（spec compliance），再检查代码质量（code quality）。

**对比 executing-plans：**

| | subagent-driven-development | executing-plans |
|---|---|---|
| 执行位置 | 当前会话 | 独立会话 |
| 上下文管理 | 每任务隔离 | 线性累积 |
| 中间 review | 两阶段（规格+质量）| 无自动 review |
| 推荐场景 | 任务独立，追求质量 | 简单线性计划 |

**关键纪律：** 任务间**不暂停等待确认**。只有以下情况才停下来：BLOCKED 状态无法自行解决、真正无法继续的歧义、或全部任务已完成。

**典型场景：**

```
计划有 5 个任务：
  Task 1 → Implementer subagent 实现 → Spec reviewer → Quality reviewer → 标记完成
  Task 2 → 新 subagent（无 Task 1 上下文）→ 两阶段 review → 标记完成
  ...（无停顿，直到全部完成）
```

---

### executing-plans

**触发时机：** 有写好的实现计划，但在**独立会话**中执行（非 subagent 模式）。

**核心规则：**
1. 加载计划后先批判性审查，有疑问先问清楚再动手
2. 按计划步骤逐步执行，不跳步，不跳验证
3. 遇到 blocker 立即停下，不要猜测硬撑
4. 全部任务完成后调用 `finishing-a-development-branch`

**什么时候停下来：**
- 缺少依赖或配置
- 测试反复失败
- 指令不清楚
- 计划有根本性漏洞

---

### dispatching-parallel-agents

**触发时机：** 面对 2 个以上**真正独立**的任务（不同子系统、不同 bug、无共享状态）。

**核心规则：** 一个问题域对应一个 agent，精确构建每个 agent 的上下文（不继承主会话历史）。

**判断是否适合并行：**

```
多个失败？
  ├─ 是 → 它们互相独立？
  │         ├─ 是 → 可以并行运行？
  │         │         ├─ 是 → 并行派发 ✓
  │         │         └─ 否 → 顺序 agent
  │         └─ 否 → 单 agent 处理全部
  └─ 否 → 不需要并行
```

**典型场景：**

```
场景 A：3 个测试文件失败，根因各不相同
  → 3 个 agent 并行调查，互不干扰

场景 B：前端组件和后端 API 独立开发
  → 2 个 agent 并行，完成后汇总集成

场景 C：多个独立模块的文档更新
  → N 个 agent 并行写文档
```

**不适用场景：** 失败可能有共同根因（修一个可能修全部）；agents 会修改同一批文件（产生冲突）。

---

## 阶段四：质量保障

### test-driven-development

**触发时机：** 实现任何功能或 bug 修复之前。

**铁律（无例外）：**

```
不写失败的测试，就不写生产代码
```

如果先写了代码：删掉，从测试开始重新来。不能"留着参考"，不能"边看边写测试"。

**Red-Green-Refactor 循环：**

```
RED   → 写测试，确认它失败（失败原因要正确）
GREEN → 写最少代码让测试通过（不追求完美）
REFACTOR → 测试保持绿灯的前提下改进设计
```

**三种状态的关键问题：**

- RED 阶段：测试为什么失败？是预期的原因吗？
- GREEN 阶段：代码最简单是什么？
- REFACTOR 阶段：有重复吗？命名清晰吗？

**什么时候可以不用（需要询问）：** 纯探索原型、生成代码、配置文件。其他情况一律使用。

---

### systematic-debugging

**触发时机：** 遇到任何 bug、测试失败、意外行为，**在提出修复方案之前**。

**铁律：**

```
不找到根因，不提任何修复方案
```

**四个阶段（必须按序完成）：**

1. **根因调查**：仔细读错误信息（不要跳过 stack trace），稳定复现问题，二分法定位
2. **假设验证**：提出假设，设计最小实验验证，不要同时改多处
3. **修复**：针对根因的最小改动，不是症状的补丁
4. **回归验证**：写回归测试，确认原始场景通过，确认无副作用

**使用"尤其是"的场景：**
- 时间压力大时（紧急更让人想猜）
- 已经试了多个"修复"没效果
- "这个问题很简单，一眼就看出来了"——这时候最容易猜错

**常见反模式（skill 明确禁止）：**
- 随机改代码看看会不会好
- 还没复现就开始修
- 一次改多个地方
- 不写回归测试

---

### requesting-code-review

**触发时机：** 完成任务/功能后，合并前。在 `subagent-driven-development` 中每个任务完成后强制执行。

**核心规则：** 派发一个独立的 reviewer subagent，给它精确构建的上下文（不是主会话历史）。

**必须提供给 reviewer 的信息：**

```bash
BASE_SHA=$(git rev-parse HEAD~1)  # 或 origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

- 构建了什么（简短描述）
- 应该做什么（计划/需求文档）
- 从哪个 commit 到哪个 commit

**何时必须请求审查：**
- `subagent-driven-development` 中每个任务完成后
- 完成主要功能后
- 合并到主分支前

**何时可选（但有价值）：**
- 卡住时（获得新视角）
- 重构前（建立基线）
- 修复复杂 bug 后

---

### receiving-code-review

**触发时机：** 收到代码审查反馈后，在实现任何建议之前。

**核心规则：** 技术评估，不是表演性同意。

**禁止的回应：**
- "你说得对！" / "好建议！"（表演性）
- "我马上改"（没有先验证就承诺）

**正确的流程：**

```
1. 完整读完所有反馈
2. 用自己的话重述技术要求（或提问澄清）
3. 对照代码库验证建议是否正确
4. 技术上正确 → 实现；技术上有问题 → 有理由地反驳
5. 一次实现一个，每个都测试
```

**有不清楚的反馈时：** 先停下，全部问清楚再动手。部分理解 = 错误实现。

**分类处理：**

| 类型 | 处理方式 |
|------|---------|
| 明确 bug / 安全问题 | 立即修复 |
| 设计争议 / 性能权衡 | 技术讨论后决定 |
| 技术债 | 创建 issue 跟踪 |

---

### verification-before-completion

**触发时机：** 准备声称"完成了"、"修好了"、"测试通过了"之前。

**铁律：**

```
没有运行验证命令，就不能声称任何完成状态
```

**验证门控（每步都要做）：**

```
1. 确定：什么命令能证明这个声称？
2. 运行：完整执行（当前这条消息里，不是之前运行的）
3. 读完：完整输出，检查 exit code，数失败数量
4. 确认：输出是否支持声称？
   - 不支持 → 陈述实际状态
   - 支持 → 带证据声称
```

**常见"谎称完成"的红旗（遇到立刻停）：**

| 声称 | 需要的证据 | 不够的证据 |
|------|-----------|-----------|
| 测试通过 | 测试命令输出：0 failures | 之前跑过，"应该能过" |
| 构建成功 | 构建命令 exit 0 | lint 没报错 |
| Bug 已修复 | 原始症状的测试通过 | 代码改了 |
| Agent 完成 | VCS diff 显示有改动 | Agent 报告"成功" |

---

## 阶段五：收尾

### finishing-a-development-branch

**触发时机：** 实现完成、所有测试通过，需要决定如何集成（合并/PR/清理）。由 `executing-plans` 和 `subagent-driven-development` 在末尾自动调用。

**流程：**

```
Step 1: 验证测试通过
  → 失败 → 必须先修复，不能进行下一步

Step 2: 检测工作区状态
  GIT_DIR == GIT_COMMON → 普通仓库
  GIT_DIR != GIT_COMMON → 在 worktree 中

Step 3: 确定 base branch（main / master / develop）

Step 4: 展示选项（用户选择）
  - 合并到 main
  - 创建 PR
  - 仅推送
  - 保留分支

Step 5: 执行选择

Step 6: 清理（如果在 worktree 中）
```

**注意：** 这个 skill 不自己决定如何集成——它展示选项，让用户决定。

---

## 元技能

### using-superpowers

**触发时机：** 每次会话开始时（SessionStart hook 自动触发）。

**作用：** 建立整个会话的"skill 使用纪律"——规定在任何响应或行动之前，只要有 1% 可能某个 skill 适用，就必须先调用它。

**最重要的红旗（这些想法出现时说明你在合理化跳过 skill）：**

| 危险想法 | 现实 |
|---------|------|
| "这只是个简单问题" | 问题也是任务，要检查 skills |
| "我先了解一下代码库" | Skills 告诉你**怎么**了解 |
| "这个 skill 我记得" | Skills 会更新，每次必须重新调用 |
| "先做这一件事" | 在做任何事之前检查 |

**优先级：** Process skills（brainstorming、systematic-debugging）先于 Implementation skills。

---

### writing-skills

**触发时机：** 创建新 skill、编辑已有 skill、验证 skill 效果时。

**核心理念：** TDD 应用于流程文档。

| TDD 概念 | Skill 创建 |
|----------|-----------|
| 测试用例 | 压力场景（subagent） |
| 生产代码 | Skill 文档（SKILL.md） |
| RED | Agent 在没有 skill 时违反规则（基线） |
| GREEN | Agent 在有 skill 时遵守规则 |
| REFACTOR | 堵住新的漏洞，保持合规 |

**什么时候创建 skill：** 方法不是直觉上显而易见的；你会在跨项目中反复用到；对他人有价值。

**什么时候不创建：** 一次性解决方案；项目特定约定（放 CLAUDE.md）；标准做法文档已经很完善。

**Personal skills 路径：** `~/.claude/skills/` (Claude Code)

---

## 标准工作流链路

### 功能开发全流程

```
/superpowers:brainstorming
  → 探索上下文 → 澄清问题 → 提出方案 → 写设计文档
    ↓
/superpowers:writing-plans
  → 细粒度任务计划 → 保存到 docs/superpowers/plans/
    ↓
/superpowers:using-git-worktrees      ← 可选，推荐
  → 创建隔离工作区
    ↓
/superpowers:subagent-driven-development
  → 每任务独立 subagent → 两阶段 review（规格+质量）
    ↓
/superpowers:verification-before-completion
  → 运行测试 → 带证据确认完成
    ↓
/superpowers:finishing-a-development-branch
  → 选择集成方式 → 执行 → 清理
```

### Bug 修复流程

```
/superpowers:systematic-debugging
  → 根因调查（不猜测）→ 假设验证
    ↓
/superpowers:test-driven-development
  → 写回归测试（先让它失败）→ 修复 → 测试通过
    ↓
/superpowers:verification-before-completion
  → 确认原始症状消失
    ↓
/superpowers:requesting-code-review
  → dispatcher reviewer subagent
```

### 收到代码审查反馈

```
/superpowers:receiving-code-review
  → 完整读完 → 逐条技术验证
  → 正确的 → 实现
  → 有问题的 → 有理由反驳（不是情绪化拒绝）
  → 全部处理完
    ↓
/superpowers:verification-before-completion
  → 重新验证全部
```

### 独立任务并行处理

```
识别独立任务域（3 个测试文件各有不同根因）
  ↓
/superpowers:dispatching-parallel-agents
  → 每个域一个 agent → 精确构建上下文（不继承主会话）
  → 并行执行 → 汇总结果
```

---

**最后更新：** 2026/06/01
**适用范围：** 所有使用 superpowers 插件的 Claude Code 会话
