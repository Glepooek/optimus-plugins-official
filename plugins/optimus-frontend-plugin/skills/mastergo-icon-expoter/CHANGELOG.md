# Changelog

## [1.1.1] - 2026-08-06

### Fixed
- `references/wpf-xaml-icon-sepc.md`：修正 `F0`/`F1` FillRule 前缀的适用范围——该前缀只属于 `Path.Data`/`Geometry` 资源使用的 `StreamGeometry` 迷你语言；若改写为 `<PathGeometry><PathGeometry.Figures>` 冗长形式，`Figures` 属性用的是不支持该前缀的 `PathFigureCollection` 迷你语言，需改用 `PathGeometry.FillRule` 属性显式指定。

## [1.1.0] - 2026-08-05

### Added
- 支持 `drawingXaml` 输入契约：将 sibling Skill 生成的 `DrawingGroup` 原样写入 `DrawingImage`，保留 `LinearGradientBrush` 和父级坐标变换。
- 新增 `fallback-png` 输入类型：矢量转换失败后可复制 MasterGo D2C 产出的完整图标 PNG 到 `Images/`。
- 清单新增 `fallbackFrom`、`fallbackReason`，区分原生位图和矢量 PNG 降级。
- 新增 DrawingGroup、PNG 降级复制、降级失败不影响同批资源的回归测试。

### Changed
- Step 3 改为以完整图标父节点为单位转换；不再把局部 PATH 当作可交付图标。
- 明确 SVG 不支持项、D2C 无权限和 PNG 缺失时为 `needs-manual`，不允许假报导出成功。

## [1.0.0] - 2026-08-04

### Added
- 新增 `mastergo-icon-expoter` Skill：从 MasterGo 设计稿导出图标、背景等视觉资产，产出 WPF `Icons.xaml`（`Geometry`/`DrawingImage` 资源字典）、`Images/*.png` 位图与 `icons-manifest.json` 决策清单。
- 新增 `scripts/icon_exporter.py`：契约校验、格式决策、命名推导、XAML/清单渲染、写盘前自检五层确定性实现，零 MCP、零网络依赖。
- 委派 `svg-to-xaml-path` 完成 SVG→`Path.Data` 转换，复用其合并键决策与 74 条测试覆盖的静默陷阱防护。
