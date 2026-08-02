# Changelog

## [1.0.1] - 2026-08-03

### Fixed
- 生成的页面在 `UserControl.Resources` 里自动引用 `Colors.xaml`（有颜色令牌时），解决 `{StaticResource ...}` 在 WPF 加载时因资源字典未接线而报错的问题。
- 区块含多个根节点时，不再统一按 `absolute=False` 渲染——根节点数 > 1 时每个根节点都带自己的 `Canvas.Left`/`Canvas.Top`，避免坐标被静默丢弃导致多个顶层图层重叠堆在原点。
- 补齐 4 条回归测试：`gap` 末元素不加 Margin、XML 转义（`&`/`<`）、`canvas_position` 缺坐标校验、`resource_key` 首字母大写。

## [1.0.0] - 2026-08-02

### Added
- 新增 MasterGo 设计稿转 WPF XAML Skill。
- 新增 `dsl_to_xaml.py`：flex 容器转 StackPanel/Grid、绝对定位转 Canvas、设计令牌转 ResourceDictionary、PATH 转图标占位。
- 新增 `references/dsl-mapping.md` 完整映射表与静默行为清单。
- 新增 30 条 CLI 契约测试。
