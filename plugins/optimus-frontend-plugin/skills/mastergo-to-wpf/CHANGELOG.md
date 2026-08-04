# Changelog

## [1.1.0] - 2026-08-04

### Added
- 数值 sectionIndex 排序、可靠尺寸/盒模型/文字样式、富文本 Run、IMAGE 占位与 `images.json`、INSTANCE 变体接管信息。
- `conversion-report.json`、严格 JSON 项目资源/控件映射、白名单 Layer Anchor 和关联 Meta/视觉验证参考文档。
- 5 条优化黑盒契约测试；当前转换器全量离线测试为 42 条。

### Changed
- 成功产物扩展为 XAML、Colors、icons、images 和报告的验证后共同写入；维持 exit 0 静默、关键错误 exit 2 的 CLI 契约。
- Skill 工作流增加增强映射方案确认、资产/回退报告交付和可选的最多三轮视觉验证闭环。

### Fixed
- `section-10.json` 被字符串排序到 `section-2.json` 前的顺序错误。
- 文档与 test prompts 已同步确认门、图片/实例限制和实际转换能力。

## [1.0.2] - 2026-08-03

### Added
- 增加独立“红线：不要做什么”清单，集中禁止越过前置条件、绕过分区、未确认即生成、虚报成功和猜测设计资源。

## [1.0.1] - 2026-08-03

### Changed
- 在获取不超过 8 个区块的目录后、拉取任一区块 DSL 前增加显性确认门：展示转换范围、输出目录与页面名，等待用户确认后才创建产物。

## [1.0.0] - 2026-08-02

### Added
- 新增 MasterGo 设计稿转 WPF XAML Skill 与确定性 DSL 转换器。