# Layer Anchor 规范

设计层名称可附显式组件意图：`保存按钮 <--@ActionButton.Primary-->`。语法为 `<--@Component.variant-->`，其中 `Component` 是字母/下划线开头的标识符，`variant` 可选。

Anchor 只作为查找 key，绝不是可执行 XAML。转换器只在 `--mapping` 的 `components[Component]` 已注册且其 `Variant` 白名单包含该值时生成自定义控件。否则输出原生 WPF 回退，并在报告写明原因。

仲裁顺序：已验证 Anchor（confidence `1.0`）> 用户确认的 Meta/项目映射 > 明确的 DSL flex 语义 > 原生 WPF。不得通过图层名称猜测业务控件、数据源、绑定、事件或任意属性。