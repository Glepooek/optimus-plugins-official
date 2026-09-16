# avalonia

> 版本：2.1.0 | 分类：workflow

Avalonia 开发入口：调用官方 Avalonia Docs MCP 确认框架事实，并将代码审查和 WPF 迁移交由受控流程处理。

## 所处层级

```
┌─────────────┐
│★ workflow   │  avalonia（本 skill）
├─────────────┤
│ quality     │  avalonia-code-review（限定范围的代码审查）
│ workflow    │  avalonia-wpf-migration（WPF 迁移编排）
│ platform    │  Avalonia Docs MCP（官方 API / 文档 / 映射）
└─────────────┘
```

本 skill 负责路由和验证边界；官方框架知识由 MCP 提供，代码审查和 WPF 迁移由对应 skill 接手。

## 触发词 / 调用方式

Avalonia 开发、AXAML、样式、绑定、控件、跨平台报错、Avalonia API 查询；审查任务转入 `avalonia-code-review`，WPF 迁移任务转入 `avalonia-wpf-migration`。

## 业务逻辑流程图

```
Step 1  收敛项目范围与任务类型
   ↓
Step 2  查询 Avalonia Docs MCP 的当前官方资料
   ↓
Step 3  最小改动、代码审查、迁移编排或构建/测试验证
```

## 产出物数据流

输入（Avalonia 任务 / 项目代码 / 报错）→ 本 skill（官方资料路由）→ 开发建议、审查报告或迁移计划 → 构建/测试记录 → 人工接手。

## 依赖关系图

```
                 ┌──▶ avalonia-code-review
★ avalonia ──────┼──▶ avalonia-wpf-migration
     │           └──▶ Avalonia Docs MCP
     └──查询──────────────────▶ Avalonia Docs MCP
```
