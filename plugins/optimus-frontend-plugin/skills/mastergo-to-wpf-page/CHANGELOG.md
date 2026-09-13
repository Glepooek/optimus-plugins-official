## [2.0.2] - 2026-09-13

### Removed
- `scripts/test_optimization.py` 的 9 个存量失败测试：`ValueSafetyTests` 整类（5 条）、`GridSizingTests` 整类（1 条）、`AnchorSafetyTests` 的 3 条（叶子锚点那条通过，已保留）。按用户裁决删除（`docs/todo-list/2026-09-12-todo.md` 的 A3）。删除后该目录 47 个测试全绿
- 随之不再被引用的 `import re`

### Added
- `known-issues.md`：承接那 9 条测试所盯的三个缺陷（对象类型 `stroke`/`fontWeight` 被 `str()` 进属性值导致 WPF 按 markup extension 解析并抛异常、锚点吞掉子内容、Grid 把不增长的子元素判为 star），状态一律「待处理」

### Changed
- `.github/workflows/ci.yml` 的 `gates-tests` 把本 skill 的 `scripts` 目录加回列表（8 → 9 个目录）。此前排除是因为那 9 个失败会让必需检查常红、主干每个 PR 都合不了（`bypass_actors` 为空，无人能绕过）
- 🔴 **这次动的是测试不是实现，三个缺陷一个都没修。** `ci.yml` 里承载根因分析的注释随排除一并撤销，`known-issues.md` 因此是它们在版本库里的唯一记录；被删测试的原文可用 `git show f149819:<本 skill>/scripts/test_optimization.py` 取回，fixture 全部原地保留

## [2.0.1] - 2026-08-20

### Added
- 补充中英文触发词示例到 frontmatter description："转 WPF 页面"、"MasterGo 转 WPF"、"设计稿转 WPF"、"这个设计稿转成 WPF"、"MasterGo 页面转换"、"WPF 页面生成"。

## [2.0.0] - 2026-08-20

### Changed
- **Breaking:** Renamed the Skill and slash command from /optimus-frontend-plugin:mastergo-to-wpf to /optimus-frontend-plugin:mastergo-to-wpf-page for MasterGo WPF pages.

# Changelog

## [1.2.0] - 2026-08-19

### Added
- 组件优先组装：读取 wpf-project-conventions 与组件库索引，新增 match_components.py 命中/缺失报告。
- 缺失组件确认门：默认返回缺失清单并建议先跑 mastergo-to-wpf-components；用户显式选择时才原生回退。
- ViewModel 骨架生成（仅当约定声明 MVVM 框架；数据源/命令标注 TODO）。

### Changed
- 生成流程插入组件匹配 Step；原 Step 4-6 顺延。

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