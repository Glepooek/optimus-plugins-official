# Changelog

## [1.0.0] - 2026-08-04

### Added
- 新增 `mastergo-icon-expoter` Skill：从 MasterGo 设计稿导出图标、背景等视觉资产，产出 WPF `Icons.xaml`（`Geometry`/`DrawingImage` 资源字典）、`Images/*.png` 位图与 `icons-manifest.json` 决策清单。
- 新增 `scripts/icon_exporter.py`：契约校验、格式决策、命名推导、XAML/清单渲染、写盘前自检五层确定性实现，零 MCP、零网络依赖。
- 委派 `svg-to-xaml-path` 完成 SVG→`Path.Data` 转换，复用其合并键决策与 74 条测试覆盖的静默陷阱防护。
- 可选 Pillow 依赖用于 `.ico` 合成；未安装时降级为多张 PNG 并在清单中如实标记 `needs-manual`。
