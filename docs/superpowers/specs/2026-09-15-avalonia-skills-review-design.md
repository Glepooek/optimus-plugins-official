# Avalonia 技能集引入与优化 spec

> 日期：2026-09-15
> 状态：**已引入（原样）**，优化待实施
> 上游：github.com/linuxdevel/Avalonia-skills（MIT License），拷贝自 2026-09-15 的 main 分支快照

## 1. 背景与目标

用户是 WPF 开发，项目要从 WPF 迁移到 Avalonia。本 spec 记录 Avalonia 技能集（1 个 master 路由 + 17 个顶层 skill + controls/pro-max 嵌套子 skill，共 33 个 SKILL.md）**原样引入**本仓库后的审查结论与优化计划。

三步要求与落地：

1. **原样搬进** —— 已完成为自建插件 `plugins/optimus-avalonia-plugin/`（本 spec §2）。
2. **对照 welcome 文档审查覆盖面** —— 结论见 §5。
3. **重点深审 wpf-migration skill**（对照 7 个 migration 文档）—— 结论见 §4。

## 2. 引入现状（已完成）

- 33 个 skill 拷入 `plugins/optimus-avalonia-plugin/skills/`，正文**未改一字**（name/description/正文原样）。
- 每 skill 补齐本仓规范：frontmatter `metadata.version/author/category`（均 `1.0.0`/`desktop client team`/`platform`）+ `CHANGELOG.md` + `README.md` + `evals/01-basic/prompt.md`。
- 双 harness 清单：`.claude-plugin/plugin.json` 与 `.codex-plugin/plugin.json`（version `1.0.0`）。
- marketplace 两条目（`.claude-plugin/marketplace.json` 顶层版本 `14.3.0 → 14.4.0`；`.agents/plugins/marketplace.json` 无顶层版本）。
- 七项 pre-commit 门禁已跑绿（exit 0）。

## 3. 结构性问题（P0，需优先处理）

「原样搬进」暴露了两处**上游结构与本仓约定的冲突**，属于不修就会影响 skill 发现/门禁的结构性问题。

### 3.1 嵌套 skill 与本仓扁平约定冲突

- `avalonia-controls/`（5 子：input/data-display/layout/media/navigation）与 `avalonia-pro-max/`（9 子）是**嵌套目录**，路径为 6 段 `skills/<name>/<sub>/SKILL.md`。
- 本仓工具链只认**扁平 5 段** `skills/<name>/SKILL.md`：`.githooks/check_new_skill_eval_case.py::new_skill_dirs()` 以 `len(parts) == 5` 判新增 skill，嵌套 skill（6 段）对增量门禁**不可见**——实测 pre-commit 全量模式「已检查 25 个」只数到 19 个顶层 skill + 6 个 wpf-code-review 存量 case，14 个嵌套 skill 的 eval 目录未纳入。
- 待确认风险：若 Claude Code 的插件 skill 发现**不递归**扫描子目录，则这 14 个嵌套 skill 不可被调用。

### 3.2 `name` 字段命名不一致

- `avalonia-controls/*` 子 skill 的 frontmatter `name` 用**连字符**（`avalonia-controls-input`），而 `avalonia-pro-max/*` 用**斜杠**（`avalonia-pro-max/themes`）。
- master 路由表（`skills/avalonia/SKILL.md`）与上游 README 用**斜杠**引用（`avalonia-controls/input`）。
- 后果：`name` 与目录路径/路由引用三者不一致，可能破坏 skill 发现与路由解析。

### 3.3 处置建议（写入优化计划，非本次改动）

见 §6 P0：优先确认 harness 是否支持嵌套；若否，则扁平化 14 个嵌套 skill 并统一 `name`（连字符），同步改 master 路由表。

## 4. wpf-migration skill 深审（任务 3）

判据来源：`migration/wpf/` 下 7 个文档（cheat-sheet / controls / data-templates / events / layout / properties / styling）。`skills/avalonia-wpf-migration/SKILL.md` 共 145 行，含 Quick Mapping Table（27 行）+ 6 个代码示例 + "What Works Without Changes" + "Common Mistakes"。

### 4.1 事实性错误 / 过度简化（高置信）

| # | 位置 | skill 现写 | 文档实际 | 影响 |
|---|---|---|---|---|
| E1 | 映射表 `TemplateBinding` | `TemplateBinding → TemplateBinding (Same)` | styling 文档：Avalonia `TemplateBinding` **仅 OneWay**，WPF 默认 TwoWay；模板内需双向时须改 `{Binding X, RelativeSource={RelativeSource TemplatedParent}, Mode=TwoWay}` | 迁移者在模板里要双向绑定会静默失败 |
| E2 | 映射表 `Style with TargetType` | `→ ControlTheme with TargetType` | styling 文档：仅「无 `x:Key` 的**隐式** Style 且含 ControlTemplate」才对应 `ControlTheme`；普通 `Style TargetType`（非定义默认外观）对应 `Style Selector` | 误导迁移者把普通样式也写成 ControlTheme |
| E3 | 缺失 `Visibility` | （无） | cheat-sheet：`Visibility` → `IsVisible`（布尔）；`Hidden`（仍占位）→ `Opacity=0` | 迁移者沿用 WPF 三态 Visibility 直接编译失败 |
| E4 | 缺失 `RenderTransformOrigin` | （无） | controls 文档：Avalonia 默认 `Center`，WPF 默认 `TopLeft`；`Viewbox` 等场景渲染结果不同 | 相同代码渲染结果不一致的隐性 bug |

### 4.2 需核实（置信中等，待查一手）

| # | skill 现写 | 疑点 |
|---|---|---|
| V1 | `CollectionViewSource → DataGridCollectionView` | Avalonia 集合视图的真实类名需核实，`DataGridCollectionView` 疑似仅覆盖 DataGrid 场景 |
| V2 | `BindingOperations.ClearBinding() → control.ClearValue(prop)` | Avalonia 是否仍有 `BindingOperations.ClearBinding`（而非只能 `ClearValue`）需核实 |
| V3 | `ResourceDictionary Source= → ResourceInclude Source="avares://..."` | cheat-sheet 称 `ResourceDictionary`/`MergedDictionaries` 与 WPF「一致」，此映射与官方口径的差异需核实 |

### 4.3 整块缺失（对照 7 文档逐项）

| 缺口 | 文档来源 | 缺失内容要点 |
|---|---|---|
| G1 事件迁移（**整块**） | events | `EventManager.RegisterRoutedEvent → RoutedEvent.Register<T>`；无独立 `Preview*` 事件、须 `AddHandler` + `RoutingStrategies.Tunnel`；`MouseLeftButtonDown → PointerPressed` 等指针命名；`AddClassHandler` 非静态 |
| G2 属性系统（过简） | properties | 仅一行 `DependencyProperty→StyledProperty/DirectProperty`；缺三类型区分、泛型 `Register<TOwner,TValue>`、`RegisterDirect`+`SetAndRaise`、`OnPropertyChanged` override、`AddOwner` vs `OverrideMetadata`、「无 `PropertyMetadata` 类」 |
| G3 布局差异 | layout | `StackPanel.Spacing` 替代逐子 Margin；`Grid` 简写 `ColumnDefinitions="Auto,*"`；层叠用 `Panel` 替代空 Grid |
| G4 控件缺失/改名 | controls | `StatusBar`/`RichTextBox` 无对应；`DataGrid` 需独立包 + `App.axaml` 主题注册；`ListView → ListBox`+ItemTemplate；`ItemsControl.Items` 只读改 `ItemsSource` |
| G5 命令体系 | cheat-sheet | `RoutedCommand`/`CommandBinding` 无内置等价物，改 `ICommand`（推荐 CommunityToolkit.Mvvm） |
| G6 窗口/图形 | cheat-sheet | `AllowsTransparency→TransparencyLevelHint`；`WindowStyle→WindowDecorations`；`ResizeMode→CanResize`；`DrawingBrush` 不可用；`LayoutTransform→LayoutTransformControl` |
| G7 平台服务 | cheat-sheet | `SystemParameters.PrimaryScreenWidth → TopLevel.GetTopLevel(this).Screens...` |

### 4.4 判定为正确、应保留的内容（正面清单）

命名空间、`.xaml→.axaml`、`DependencyProperty→StyledProperty/DirectProperty`（方向）、`FrameworkElement/Control→Control/TemplatedControl`、Dispatcher（`InvokeAsync`/`Post`）、Asset URI `avares://`、RelativeSource 语法（`$self`/`$parent[Type]`）、ControlTemplate→ControlTheme 示例、`MessageBox.Show` 移除、Common Mistakes 六条——大体正确。

## 5. 全技能集覆盖面审查（任务 2）

判据来源：`docs/welcome` 的文档目录树 + 上游 README 的技能清单。

### 5.1 覆盖良好（正面）

33 个 skill 与官方文档结构**高度对应**：XAML / layout / styling / data-binding / data-templates / controls（5 子）/ custom-controls / graphics-animation / input-interaction / property-system / events / services / app-development / testing / deployment / migration 全部有对应 skill。pro-max 系列（design-system/themes/components/motion/accessibility/layout-patterns/icons-imagery/review-checklist/preview-server）是文档之上的**增值**层，非缺口。

### 5.2 覆盖缺口（文档有、skill 无）

| # | 缺口 | 官方文档章节 | 说明 |
|---|---|---|---|
| C1 | Getting Started / 项目引导 | `Getting Started`（Install / IDE / 首个项目 / 温度转换器教程） | 无 skill 覆盖「从零建 Avalonia 项目」，参考 skill 假设项目已存在 |
| C2 | Platform Integration (Windows) | `Platform Integration` | 无专属 skill；Windows 专属能力（托盘、通知等）散落在 services/deployment，未成体系 |
| C3 | Breaking changes / 11→12 升级 | `Breaking changes (Avalonia 12)` | 无 skill 覆盖升级路径；而 master skill 却声称覆盖「Avalonia 12」 |

### 5.3 版本/事实声明需核实（中置信）

- master `skills/avalonia/SKILL.md` Overview 称「**Avalonia 12 is the current stable version; compiled bindings are enabled by default**」。
- welcome 文档确认「docs target version 12」；但 `migration/wpf/data-templates` 文档提到需在 `.csproj` 显式加 `<AvaloniaUseCompiledBindingsByDefault>true</...>` 才「全局启用」——**与「默认启用」矛盾**。需查 Avalonia 12 发行说明核实 compiled bindings 是否已默认开启；若未默认，则 master 的表述是错误的事实声明。

## 6. 优化计划（分优先级）

| 优先级 | 项 | 动作 | 依赖 |
|---|---|---|---|
| **P0** | 结构（§3） | 确认 harness 是否递归发现嵌套 skill；若否 → 扁平化 14 个嵌套 skill、`name` 统一连字符、同步 master 路由表 | 先做一次真实 `--plugin-dir` 加载验证 |
| **P1** | wpf-migration 修复 | 修 E1–E4；补 G1–G7 七个缺失章节；更正 E2 的 Style/ControlTheme 措辞 | §4 结论 |
| **P2** | 需核实项 | 核实 V1–V3（查一手 API 文档）后更正或删除 | — |
| **P3** | 覆盖缺口 | 评估 C1/C2/C3 是否值得新建 skill（C1 或并入 app-development；C3 依赖版本事实） | §5.2 |
| **P4** | 版本声明 | 核实 compiled bindings 默认值，修正 master Overview | §5.3 |

**升级幅度预估**（按 AGENTS.md 触发矩阵）：P1 属「修改已有内容」→ 各 skill Patch；若 P0 需扁平化（重命名用户可见 skill）→ 插件 Minor 起；master 路由表改动 → `avalonia` skill Patch/Minor 视是否新增路由行。

> **附：上游脚本安全审查（后台自动审查，2026-09-15）**
> `skills/avalonia-pro-max/preview-server/scripts/serve_gallery.py` 被标 MEDIUM「DOM-based stored XSS」：`header.innerHTML = \`<h2 id="title-${vid}">...\`` 内插值未转义。属上游原样带入的代码；`vid` 为脚本内部生成的变体 ID，非用户可控输入，当前无可利用的数据流，但仍是防御性整改点。记入优化项：改用 `textContent`/`createElement`，或对 `vid` 做 HTML 转义。

## 7. 判据来源

- https://docs.avaloniaui.net/docs/welcome
- https://docs.avaloniaui.net/docs/migration/wpf/cheat-sheet
- https://docs.avaloniaui.net/docs/migration/wpf/controls
- https://docs.avaloniaui.net/docs/migration/wpf/data-templates
- https://docs.avaloniaui.net/docs/migration/wpf/events
- https://docs.avaloniaui.net/docs/migration/wpf/layout
- https://docs.avaloniaui.net/docs/migration/wpf/properties
- https://docs.avaloniaui.net/docs/migration/wpf/styling
