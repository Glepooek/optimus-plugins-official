# 组件抽取规则（component-extraction-rules）

## 可复用判定

| 判据 | 结论 |
|---|---|
| 节点为 INSTANCE 且命中严格映射 | `status=mapped`，`kind=control/style` |
| INSTANCE 未映射但出现 >=2 次 | `status=new`，`kind=style` |
| FRAME/GROUP 同签名出现 >=2 次 | `status=new`，`kind=datatemplate` |
| 单次出现 | 不抽取，留在页面内联 |

签名定义：type + name + `_token` + `_color` + 子节点数。

## 资源生成

- token 仅收集被抽取组件引用的 `_token`；`_color` 字面量保留内联不生成资源。
- 颜色 key 用 `resource_key`（`Text/Text-4` → `TextText4`），保留原名注释。
- DataTemplate 只从首个匹配节点生成，子 TEXT 节点名作为占位标签（上限 6 个）。

## 人工接管

- code-behind / 动画 / 事件：一律不自动生成，index 中 `manual=true`。
- 正文提取上限：几何与填充来自首个出现节点，变体差异写入报告。
