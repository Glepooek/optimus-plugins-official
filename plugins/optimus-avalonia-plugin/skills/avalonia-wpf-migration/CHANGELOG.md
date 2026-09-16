## [1.2.1] - 2026-09-16

### Changed
- 改为以 Avalonia Docs MCP 为官方知识源：先分析 WPF 项目，再经确认选择 XPF 或原生 Avalonia。
- 将实现收敛到可验证垂直切片，并按需加载官方映射主题与 Diagnostics 迁移流程。

### Removed
- 移除插件内静态 API 映射表，避免与官方文档版本漂移。


## [1.2.0] - 2026-09-15

### Added
- 新增 `Bindings Compile by Default` 章节：Avalonia 12 起 compiled bindings 默认开启，每条绑定都需要一个「起始类型」——通常是作用域（`Window` / `UserControl` / `DataTemplate`）上的 `x:DataType`，少数模板场景由编译器推断（如 `ItemTemplate` 从其 items）。缺起始类型时 XAML 编译器抛 `Cannot parse a compiled binding without an explicit x:DataType directive...`，**构建失败**，不会静默回退反射。`{ReflectionBinding}` 是 WPF `{Binding}` 的逐绑定等价物
- `Common Mistakes` 补一条：误以为 `{Binding}` 仍按反射解析

### Fixed
- `What Works Without Changes` 中「Data binding patterns（仅需命名空间与 `RelativeSource` 语法调整）」在 v12 下已不成立——缺 `x:DataType` 的绑定是**构建失败**，不是语法调整。该行改为指向新增章节

### 依据
依据取 Avalonia 编译器源码（一手源最高档），非文档叙述：`AvaloniaXamlIlBindingPathTransformer.cs` 中 `startTypeResolver` 在找不到祖先 `AvaloniaXamlIlDataContextTypeMetadataNode` 时抛 `XamlBindingsTransformException`；`AvaloniaXamlIlDataContextTypeTransformer.cs` 中该 metadata 的来源除 `x:DataType` 外还有内联 `DataContext`、`[DataType]` 属性与 `[InheritDataTypeFromItems]` 推断。抛错路径的判据是节点类型等于 `CompiledBindingExtension`，故 `{ReflectionBinding}` 不受影响

## [1.1.1] - 2026-09-15

### Fixed
- 映射表三处 Notes 述而不准，逐条回一手源码核实后改写（三条的 Avalonia 侧目标写法本身正确，改的是差异描述）：
  - `ResourceDictionary` `Source=` → `ResourceInclude`：原注「URI scheme differs」把差异说成了表面问题。`ResourceDictionary` 根本没有 `Source` 属性，合并只能经 `MergedDictionaries`（`IList<IResourceProvider>`）——是结构差异，不是 URI 写法差异
  - `BindingOperations.ClearBinding()` → `ClearValue`：原注「Slightly different」过低描述了差异。Avalonia 的 `BindingOperations` 只有 `DoNothing` 字段、两个已废弃的 `Apply` 重载和 `GetBindingExpressionBase`，**没有 `ClearBinding`**
  - `CollectionViewSource` → `DataGridCollectionView`：原注「Different class」遗漏了两个决定性限制——它只服务 `DataGrid`（`Avalonia.Collections` 命名空间，随 `Avalonia.Controls.DataGrid` 独立包分发），Avalonia 没有 WPF `ICollectionView` 的通用等价物
- `Common Mistakes` 补一条：沿用 `CollectionViewSource` / `ICollectionView` 做筛选排序分组——需改为在 view model 中处理，而非换个类名了事

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
