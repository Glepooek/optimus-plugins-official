# 16 · 版本控制与协作

> 更新历史：2026-08-21 创建；2026-08-23 分支/提交/PR/发布/所有权条款迁移至 `knowledge-base/git/`，本篇仅保留与 C# 语言相关的 CHANGELOG 条款。

分支策略、提交信息、PR 规范、版本发布、代码所有权等通用 Git 协作规范见 `knowledge-base/git/`。本篇仅保留 CHANGELOG 条款——契约变更联动 `13` 章。

## 1. CHANGELOG

- **必须**：用户可见变更记录到 CHANGELOG（按版本分组，契约变更联动 `13` 章）
- **应该**：CHANGELOG 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式
- **禁止**：把内部重构当用户可见变更写入 CHANGELOG（除非影响行为）
