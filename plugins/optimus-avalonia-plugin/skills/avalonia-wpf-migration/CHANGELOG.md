## [1.1.0] - 2026-09-15

### Added
- 事件迁移章节：`Preview*` 事件替代（`AddHandler` + `RoutingStrategies.Tunnel`）、指针事件命名映射表
- 属性系统章节：三种属性类型对应表、`Register` 泛型写法、无 `PropertyMetadata` 类的两种替代（`OnPropertyChanged` override / `AddClassHandler`）、值优先级
- 布局章节：`StackPanel.Spacing`、Grid 行列简写、`Panel` 替代空 Grid 做层叠、`DockPanel.LastChildFill` 默认值
- 控件章节：无对应控件（`StatusBar` / `RichTextBox`）及替代方案、需额外配置的控件（`DataGrid` 独立包与主题注册）、`Items` 只读须用 `ItemsSource`、`ListView` → `ListBox`
- 命令章节：`RoutedCommand` / `CommandBinding` 无内置等价物的处置
- 窗口与图形章节：窗口属性映射、图形与变换映射、`RenderTransformOrigin` 默认值差异
- 平台服务章节：`SystemParameters` / `Screen` → `TopLevel` 服务映射
- `references/custom-control-authoring.md`：自定义属性与路由事件注册、强制值、`AddOwner` / `OverrideDefaultValue`
- `test-prompts.json`：darwin-skill 评测用测试 prompt 三条（开放式迁移咨询 / 具体 XAML 迁移 / 已正确迁移的反例校准）

### Fixed
- `TemplateBinding` 原标注为「Same」有误：Avalonia 仅支持 OneWay（WPF 默认 TwoWay），补充模板内双向绑定的正确写法
- `Style with TargetType` → `ControlTheme` 过度简化：改为按用途判定的三分规则（`ControlTheme` / `Style` + `Selector` / 样式类）
- 映射表补 `Visibility` → `IsVisible`（WPF 的 `Hidden` 语义需改用 `Opacity="0"`）
- 映射表补 `RenderTransformOrigin` 默认值差异（Avalonia `Center`、WPF `TopLeft`）
- `Common Mistakes` 按「静默失效优先」重排，并补充 `Items` 赋值、`DataGrid` 主题、`StyledProperty` 支持字段、`DirectProperty` 的 `SetValue` 等条目
- `DataGrid` 主题注册路径写错为 `Themes/Fluent.axaml`，正确为 `Themes/Fluent.xaml`（经 darwin-skill 评审 S1 项核实官方文档后更正）——该错误不影响编译，但会导致网格渲染无样式
- `Common Mistakes` 前四条的 `(E1)`–`(E4)` 编号在正文中无图例可查（且顺序为 E1/E2/E4/E3），属悬空引用，随评审 D2 项一并删除

## [1.0.0] - 2026-09-15

### Added
- 从上游 linuxdevel/Avalonia-skills 原样引入（自建插件 optimus-avalonia-plugin，MIT License）
