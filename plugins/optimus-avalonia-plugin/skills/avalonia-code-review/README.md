# avalonia-code-review

> 版本：1.0.0 | 分类：quality

在用户指定范围内审查 Avalonia AXAML 与 C# UI 代码，并以官方 Avalonia Docs MCP 查询作为每项框架结论的依据。

## 所处层级

```
┌─────────────┐
│ workflow    │  avalonia（开发入口）
├─────────────┤
│★ quality    │  avalonia-code-review（本 skill）
├─────────────┤
│ platform    │  Avalonia Docs MCP（官方依据）
└─────────────┘
```

本 skill 负责已有限范围的质量审查；`avalonia` 负责一般开发问题路由，`avalonia-wpf-migration` 负责迁移编排。

## 触发词 / 调用方式

审查 Avalonia 代码、Avalonia review、AXAML 检查、Avalonia PR 审查、检查 Avalonia 绑定/样式/跨平台问题。

## 业务逻辑流程图

```
Step 1  收敛审查范围与深度
   ↓
Step 2  读取代码并查询 Avalonia Docs MCP
   ↓
Step 3  分级报告已确认问题与待确认项
   ↓
Step 4  提供最小修正与验证状态
```

## 产出物数据流

输入（指定代码范围、项目配置、错误输出）→ 本 skill（官方资料核验）→ 严重度报告、最小修正、待确认项 → 人工修复或复审。

## 依赖关系图

```
avalonia ──路由──▶ ★ avalonia-code-review ──查询──▶ Avalonia Docs MCP
```
