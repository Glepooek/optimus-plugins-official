# MasterGo Meta Rules（可选增强输入）

在初始 section 目录和用户确认后，才可调用 `mcp__getMeta(fileId)`。Rules 是编排层增强输入，不是转换器依赖：MCP 不可用、返回为空、段落不完整或内容不能验证时，继续纯 DSL 路径，并在报告/交付说明记录降级。

可消费段落：

| Meta 段落 | 允许用途 | 禁止事项 |
|---|---|---|
| `## Design Tokens` | 用户确认后填入映射 `resources` | 不验证资源 key 就写 StaticResource |
| `## Component Mapping` | 提出已注册控件映射候选 | 不把控件字符串或 XAML 片段直写页面 |
| `## Layer Anchors` | 用作锚点名称/变体说明 | 未在 JSON 映射中登记时生成自定义控件 |
| `## Constraints` | 生成后审计与报告项 | 将规则缺失当作转换失败 |

安全流程：提取候选 → 扫描项目中的实际 ResourceDictionary/控件 → 向用户展示方案摘要 → 生成严格 JSON mapping → 调用 CLI。Meta 从不直接传入 XAML。