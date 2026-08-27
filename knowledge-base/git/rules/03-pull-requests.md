# 03 · PR 规范与合并策略

> 更新历史：2026-08-23 创建，迁移自 `csharp/16-collaboration.md` §3 并新增合并策略与保护分支约定。

PR 概念讲解（PR 是什么、平台名称差异、何时使用）见 `reference/pull-request-concepts.md`。

## 1. PR 规范

- **必须**：PR 标题表达变更意图；描述含：背景、改动、测试、验证方式
- **必须**：PR 关联 issue / 需求编号
- **必须**：CI 通过 + review 批准才可合并（联动 `knowledge-base/csharp/rules/15-quality-review.md`）
- **应该**：PR 小而聚焦（大 PR 拆分，减少 review 摩擦）
- **禁止**：把无关改动混进一个 PR

## 2. 合并策略

- **必须**：团队统一一种合并策略（squash / rebase / merge commit），不逐 PR 各自决定
- **推荐**：特性分支合入主干用 squash merge，保持主干历史线性、一 PR 一提交，便于回滚
- **应该**：涉及多个逻辑独立变更且需要保留提交粒度时，例外使用 rebase merge，需在 PR 描述中说明理由
- **禁止**：用 merge commit 制造大量交织的合并记录（除非团队明确选择该策略并全仓一致）

## 3. 保护分支设置

- **必须**：主干分支开启保护规则——禁止直接推送，禁止强制推送（force push），只能通过 PR 合入
- **必须**：主干分支要求至少一名 reviewer 批准且 CI 全绿才允许合并
- **应该**：保护规则覆盖发布分支（`release/*`），防止发布收尾期被意外改动绕过 review
