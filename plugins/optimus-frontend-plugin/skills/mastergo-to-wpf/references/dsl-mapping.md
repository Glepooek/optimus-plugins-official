# DSL → WPF XAML 映射

这是 `scripts/dsl_to_xaml.py` 的实际离线契约。成功为 exit 0 且 stdout/stderr 均为空；关键输入错误为 exit 2、stdout 为空、stderr 为单行 `error: ...`。所有 XAML、资源、清单和报告会在校验后共同写入。

## 布局与盒模型

- `section-{N}.json` 按数值 `N` 升序读取；不符合 `section-<整数>.json` 的文件忽略。
- 有 `flexContainerInfo` 的节点生成 `StackPanel`；子节点有 `flexGrow` 时生成 `Grid`。gap 生成除最后一项外的 Margin，直接 flex 子节点绝不带 `Canvas.Left`/`Canvas.Top`。
- 无 flex 节点生成 `Canvas`，子节点使用 `layoutStyle.relativeX/relativeY`；必要坐标缺失硬失败。
- 可靠、有限、非负的 `layoutStyle.width/height` 生成 `Width`/`Height`。缺失不编造，非法值忽略并写报告。
- 含 fill、stroke、padding 或 radius 的容器使用 `Border` 包裹内部布局；`padding` 支持数值、空格/逗号分隔、数组和 left/top/right/bottom 对象。
- `strokeColor`/`strokeWidth` 成对解析为 `BorderBrush`/`BorderThickness`；`cornerRadius` 或 `radius` 解析为 `CornerRadius`。无法解析会写 `fallbacks`。
- FRAME `opacity` 只烧入自身 Background 的 alpha；不会输出父级 `Opacity`。

## 文本、图标、图片与实例

- TEXT 生成 `TextBlock`，支持 `fontFamily`、`fontSize`、`fontWeight`、`fontStyle`、`lineHeight`、`textAlignment`/`textAlign`、`textWrapping`/`wrap`；不会替换设计字体。
- 多段 `text` 生成多个 `Run`，各 run 保留可解析文字样式。长文本仍从 `rowTexts` 回填，所有实际文字受 `rootMetadata.allTexts` 闭集校验。
- PATH 生成 `<!-- ICON:key -->` 和 `Path`，缺 `svgShortKey` 硬失败；`icons.json` 含位置、尺寸和颜色上下文。
- IMAGE 生成具名 TODO 注释和 `Image` 占位，同时写 `images.json`。`url([object Object])` 标为 `unrecoverable`，其他资源缺口标为 `missing` 或 `not-exported`。
- INSTANCE 的未映射 `_variantProps` 写为 `TODO INSTANCE_VARIANTS` 注释及 `manualHandoffs`；不静默丢弃。

## Token、映射与报告

颜色优先级为 `_color`、再 `fill` 引用 `styles`；断链 style 硬失败。Token 默认写进 `Colors.xaml` 并以 `{StaticResource}` 引用。`--mapping` 中已验证的 Token 优先引用项目 resource key，不重复生成局部画刷。

`conversion-report.json` 固定包含 `sections`、`tokenCoverage`、`componentMapping`、`assets`、`fallbacks`、`manualHandoffs`、`missingDimensions` 与 `unverified`。报告不替代 XAML 中图片、实例等关键 TODO。

严格项目映射见 [`wpf-project-mapping.md`](wpf-project-mapping.md)；Meta/Anchor 与视觉验证均为可选编排层能力。