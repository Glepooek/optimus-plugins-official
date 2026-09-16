# avalonia-wpf-migration

> 版本：1.2.1 | 分类：workflow

为 WPF→Avalonia 迁移提供项目分析、XPF/原生路线确认、垂直切片实施和验证记录；官方映射均按需从 Avalonia Docs MCP 查询。

## 所处层级

```
┌─────────────┐
│★ workflow   │  avalonia-wpf-migration（本 skill）
├─────────────┤
│ workflow    │  ↑ avalonia（入口路由）
│ platform    │  ↔ Avalonia Docs MCP（分析 / 映射 / 官方流程）
└─────────────┘
```

本 skill 是企业迁移编排器，不维护静态 API 对照表。

## 触发词 / 调用方式

WPF 迁移 Avalonia、WPF 跨平台、XPF 还是 Avalonia、评估 WPF 改造；也可由 `avalonia` 入口在识别到迁移任务时转入。

## 业务逻辑流程图

```
Step 1  MCP 分析 WPF 项目与依赖
   ↓
Step 2  🔴 确认 XPF 或原生 Avalonia 路线
   ↓
Step 3  迁移并验证一个垂直切片
   ↓
Step 4  交付风险、验收和后续切片清单
```

## 产出物数据流

输入（WPF 项目、目标平台、迁移范围）→ 本 skill（官方分析与路线编排）→ 迁移决策、切片计划、验证记录 → 人工接手或下一切片。

## 依赖关系图

```
avalonia ──路由──▶ ★ avalonia-wpf-migration ──调用──▶ Avalonia Docs MCP
```
