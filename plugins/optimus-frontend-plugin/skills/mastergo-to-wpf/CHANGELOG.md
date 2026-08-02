# Changelog

## [1.0.0] - 2026-08-02

### Added
- 新增 MasterGo 设计稿转 WPF XAML Skill。
- 新增 `dsl_to_xaml.py`：flex 容器转 StackPanel/Grid、绝对定位转 Canvas、设计令牌转 ResourceDictionary、PATH 转图标占位。
- 生成的页面在 `UserControl.Resources` 中自动引用 `Colors.xaml`（存在颜色令牌时），使 `{StaticResource …}` 可被 WPF 解析。
- 新增 `references/dsl-mapping.md` 完整映射表与静默行为清单。
- 新增 37 条 CLI 契约测试。

### Known Limitations
- **不输出任何 `Width`/`Height`/`Padding`/`BorderThickness`**：产物是一张正确的坐标骨架（层级、位置、颜色、文本、图标锚点均正确），但每个元素的尺寸需自行补齐。
- `FRAME`/`GROUP`/`INSTANCE` 统一渲染为 `Canvas`，不生成 `Border`，也不保留 `INSTANCE` 的 `_variantProps`。
- 详见 SKILL.md 的静默行为清单与已知限制。
