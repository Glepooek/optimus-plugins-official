# WPF 项目映射契约

> 本映射与 `wpf-project-conventions/CONVENTIONS.md` 的关系：映射是“设计稿组件名 → 项目控件/资源”的严格白名单；约定是项目级基线（目录/命名/编译）。两者缺一不可：先读约定确定落盘位置与命名，再用映射决定控件语义。

`dsl_to_xaml.py --mapping PATH` 只接受 UTF-8 JSON 数据，不接受 Markdown、自由 XAML、任意属性或事件处理器。映射错误会降级为纯 DSL 转换，并在 `conversion-report.json` 的 `fallbacks` 中说明，不会阻断基础转换。

```json
{
  "resources": {
    "Fill/Primary": "BrandPrimaryBrush"
  },
  "xmlns": {
    "controls": "clr-namespace:Example.Client.Controls"
  },
  "components": {
    "ActionButton": {
      "xmlns": "controls",
      "type": "PrimaryButton",
      "allowedProperties": {
        "Variant": ["Primary", "Secondary"]
      },
      "variants": {}
    }
  }
}
```

- `resources`：设计 Token 到**已验证** WPF resource key；映射后输出 `{StaticResource key}`，不会重复写入 `Colors.xaml`。
- `xmlns`：前缀必须是合法 XML 名；命名空间不得包含 `<`、`>` 或引号。
- `components`：名称是 Anchor 的 `Component`；`xmlns` 必须引用同文件已声明的前缀，`type` 必须是合法控件名。
- `allowedProperties`：属性和值均为显式白名单。当前转换器仅将经允许的 Anchor `variant` 写为 `Variant`，其余值不会输出。
- `variants` 为保留的受限变体映射字段；不得放入 XAML 片段。

任何缺失资源、未知控件、无效前缀或未注册 Anchor 都必须回退为原生 `Canvas`/`Border`/`Grid`/`StackPanel`，并保留可追踪报告项。