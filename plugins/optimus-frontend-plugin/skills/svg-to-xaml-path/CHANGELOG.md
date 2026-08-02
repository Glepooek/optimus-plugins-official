# Changelog

## [1.1.0] - 2026-08-02

### Added
- 新增解析 `style` 内联声明的能力：`fill`/`stroke`/`fill-rule`/`display`/`visibility`/`transform` 六个属性按 CSS 优先级覆盖同名 presentation attribute。
- 新增 `Data` 的 fill rule 前缀（`F1` nonzero / `F0` evenodd），对齐 SVG 的 nonzero 默认值与 WPF 迷你语言的 EvenOdd 默认值差异。
- 新增 `assets/sample-icon.svg` 示例文件，替代原先指向个人下载目录的示例路径。
- 新增「已转换 / 未转换」对照表，并明确点名 `currentColor`、`url(#gradient)`、`rgb()` 等 WPF 无法解析的 paint 值。
- 新增 14 条 CLI 契约测试，覆盖非渲染子树、隐藏元素、`style` 解析与 fill rule。

### Changed
- 脚本调用路径改为基于本 skill 的 base directory；原先的仓库相对路径在插件缓存加载时会失败。
- fill-rule 纳入 `xaml` 的合并判据：`Fill`/`Stroke`/`fill-rule` 三者全同才合并为一个 `Path`。
- 拆分原先的 `style or class` 合并警告：`class` 单独告警，`style` 中未识别的声明按名称告警。

### Fixed
- 修复 `<defs>`/`<clipPath>`/`<mask>`/`<symbol>`/`<marker>`/`<pattern>` 内的路径被当作可见图形串入几何的问题。
- 修复 `display:none` 子树与 `visibility:hidden` 路径被输出的问题。
- 修复填充写在 `style` 中时静默退化为 `#000000` 的问题。
- 移除违反开放 Agent Skills 规范六字段限制的顶层 `version` 字段。

## [1.0.0] - 2026-07-30

### Added
- 新增 SVG 转 WPF XAML Path Skill。
- 新增无需第三方依赖、兼容 Python 3 的命令行工具说明。
- 新增 `data` 和 `xaml` 输出格式说明。
- 新增转换警告与错误诊断说明。
