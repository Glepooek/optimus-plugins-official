# 04 · XAML 编写规范

> 更新历史：2026-08-21 创建。

XAML 是 WPF 的声明式 UI 语言。本篇约束命名空间、资源引用、模板组织与代码可读性。生成工具（mastergo 系列）产出的 XAML 须符合本约定。

## 1. 命名空间与根元素

- **必须**：XAML 根元素统一 `x:Class`（页面 / 窗口）或用 `x:ClassModifier` 控制可访问性（自定义控件）
- **必须**：根元素声明默认命名空间（`xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"`）与 `x` 命名空间（`xmlns:x="..."`）
- **应该**：自定义命名空间前缀语义化（`xmlns:controls="clr-namespace:App.Controls"`），**禁止**无意义前缀（`xmlns:foo`）
- **禁止**：未使用的命名空间声明（编译告警 + 噪音）
- **应该**：页面根元素用 `Window` / `UserControl` / `Page`，不随意用 `ContentControl` 当根

## 2. 资源引用：StaticResource vs DynamicResource

| 类型 | 时机 | 特点 |
|---|---|---|
| `StaticResource` | 值**编译后不再变** | 构建期解析一次，快；找不到资源编译报错 |
| `DynamicResource` | 值**运行期可变**（主题切换、动态加载） | 运行期解析，跟随资源变更；略慢，找不到时静默 |

- **必须**：默认用 `StaticResource`，仅当需要响应资源运行时变化（主题切换、皮肤）才用 `DynamicResource`（联动 `07` 章）
- **禁止**：无理由用 `DynamicResource`（运行期查找开销 + 找不到静默吞掉，问题难排查）
- **必须**：资源引用尽量就近（页面局部 → 应用级），跨层级引用维护成本高

```xml
<!-- ❌ 无理由 DynamicResource：运行期查找慢，key 拼错静默不显示 -->
<Button Background="{DynamicResource ButtonBrush}" />

<!-- ✅ 编译期资源用 StaticResource：key 找不到构建即报错，性能好 -->
<Button Background="{StaticResource ButtonBrush}" />
```

```xml
<!-- ✅ 主题切换 / 皮肤场景才用 DynamicResource：资源变更时 UI 实时跟随 -->
<Button Background="{DynamicResource ThemeAccentBrush}" />
```

```xml
<!-- 两者关键差异：DynamicResource 运行时依赖资源存在且可替换，StaticResource 一次解析后固定 -->
<!-- 主题不切换就用 StaticResource；会切换的主题资源（颜色、画刷）才用 DynamicResource -->
```

## 3. 布局与可读性

- **必须**：XAML 缩进与嵌套清晰（子元素缩进 4 空格），长属性换行对齐
- **必须**：同一页面嵌套层级控制合理，深度过大（>8 层）应拆分 UserControl / DataTemplate
- **应该**：属性值用 Markup Extension 简写（`{Binding X}`、`{StaticResource Y}`），不写冗余的完整形式
- **禁止**：XAML 中出现魔法数字 / 硬编码颜色散布（集中到资源，联动 `07` 章）
- **禁止**：把业务逻辑写进 XAML（`x:Code`、触发器里做复杂计算）

## 4. x:Name 与 x:Key

- **必须**：`x:Name` 用于需代码引用的元素（事件订阅、动画目标、程序化访问），`x:Key` 用于资源键
- **必须**：只有代码需要访问的元素才设 `x:Name`（多余的 `x:Name` 产生字段 + 编译成本）
- **禁止**：`x:Name` 与 `x:Key` 混用（`x:Name` 用于资源时产生字段但无法作为资源键引用——用 `x:Key` 定义资源）
- **应该**：`x:Name` 命名见 `02` 章第 5 节，资源键见 `07` 章

```xml
<!-- ❌ 资源用 x:Name：产生无用的字段，且无法通过 {StaticResource} 引用 -->
<LinearGradientBrush x:Name="MyBrush">
  <GradientStop Color="Blue" Offset="0"/>
</LinearGradientBrush>
<Button Background="{StaticResource MyBrush}"/>   <!-- 编译错：x:Name 不是资源键 -->

<!-- ✅ 资源用 x:Key：可被 StaticResource 正确引用，无多余字段 -->
<LinearGradientBrush x:Key="MyBrush">
  <GradientStop Color="Blue" Offset="0"/>
</LinearGradientBrush>
<Button Background="{StaticResource MyBrush}"/>
```

## 5. DataTemplate 组织

- **必须**：DataTemplate 定义在资源字典（`Themes/DataTemplates.xaml` 或所属 View 资源），**禁止**在列表项内联定义重复模板（无法复用 + 性能差）
- **必须**：DataTemplate 内绑定用 `{Binding Property}`（相对 `DataContext`），层级复杂时用 `{RelativeSource}` / `{ElementName}` 定位，**禁止**硬编码路径
- **应该**：同类型数据的模板统一放置，命名 `{DataType}Template`
- **禁止**：DataTemplate 内承载业务操作（命令绑定在 ViewModel，联动 `03` 章）

## 6. 样式与触发器

- **必须**：样式定义在资源字典集中管理，`Style` 显式设置 `TargetType`（不靠 `x:Key` 猜类型）
- **必须**：隐式样式（无 `x:Key`，按类型自动应用）限定使用范围——明确所有该类型元素都需同样式时用，否则用显式 `x:Key`

```xml
<!-- ❌ 内联样式：每次使用都定义一份，无法复用、主题无法覆盖 -->
<Button>
  <Button.Style>
    <Style TargetType="Button">
      <Setter Property="Background" Value="#FF3377CC"/>
      <Setter Property="Foreground" Value="White"/>
    </Style>
  </Button.Style>
  保存
</Button>

<!-- ✅ 集中资源：定义一次，多处引用，主题可整体替换 -->
<Style x:Key="ButtonPrimaryStyle" TargetType="Button">
  <Setter Property="Background" Value="#FF3377CC"/>
  <Setter Property="Foreground" Value="White"/>
</Style>
<Button Style="{StaticResource ButtonPrimaryStyle}">保存</Button>
```
- **应该**：样式间用 `BasedOn` 继承组织层次，不复制粘贴整段样式
- **禁止**：在样式内写业务逻辑（Trigger 只做视觉状态切换，不改数据）
- **禁止**：`Style` 内内联定义不可共享的资源（Brush、Geometry 等在 `Style.Resources` 内嵌，联动的资源应提为独立字典）

## 7. 触发器与视觉状态

- **必须**：视觉状态优先用 `VisualStateManager`（`VisualState` / `VisualStateGroup`），可维护性优于属性触发器堆叠
- **应该**：简单状态（悬停、按下）用 `Trigger` / `Setter` 足够；复杂动画状态用 `VisualStateManager` 管理
- **禁止**：用 `EventTrigger` 做非动画业务行为（命令该走绑定）

## 8. 事件与命令

- **必须**：交互行为优先绑定命令（`{Binding Command}`），**禁止**code-behind 写业务事件处理器
- **必须**：无命令的事件（窗口关闭、拖拽、焦点）在 code-behind 处理并转调 ViewModel 方法，保持 handler 极薄（联动 `02` 章第 4 节）
- **应该**：常见交互（点击、选择变化）优先命令绑定，必要时用 `InputBindings` / `CommandBindings` 声明按键与手势

## 9. XAML 编译与设计期

- **必须**：XAML 编译（BAML）开启，编译期错误（缺 `x:Class`、命名空间错）在构建期暴露
- **必须**：绑定路径错误用设计期诊断 / `PresentationTraceSources` 跟踪，**禁止**运行期靠肉眼发现绑定静默失败（联动 `05` 章）
- **应该**：启用设计期数据（`d:` 命名空间）辅助设计器预览，避免设计器报绑定缺失
- **禁止**：设计期数据写进生产逻辑（`d:DataContext` 仅在编辑器加载，不参与运行期）

## 10. 可访问性（联动 `14` 章）

- **必须**：关键交互元素配 `AutomationProperties.Name` / `HelpText`
- **必须**：纯装饰元素设 `AutomationProperties.AutomationId` 且不参与 Tab 焦点（`Focusable="False"`）
- **应该**：图标按钮等无文本元素必须有可读的自动化名称
