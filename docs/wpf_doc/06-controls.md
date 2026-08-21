# 06 · 控件体系

> 更新历史：2026-08-21 创建。

控件是 UI 的积木。本篇约束内置控件使用、UserControl / 自定义控件选型、依赖属性与模板部件。

## 1. 控件选型：内置 / UserControl / 自定义控件

| 形态 | 特征 | 适用 |
|---|---|---|
| **内置控件** | WPF 自带，模板可换 | 通用交互（Button、TextBox、ListBox、DataGrid） |
| **UserControl** | 组合控件 + code-behind，无独立模板 | 页面局部复用的组合件（`SearchBar`、`Card`） |
| **自定义控件** | 继承 `Control`，默认样式 + 模板（`Themes/Generic.xaml`） | 需跨主题 / 跨皮肤复用、外观完全可控 |
| **附加行为/附加属性** | 给已有控件附加能力 | 轻量扩展（验证、拖拽），不新建类型 |

- **必须**：优先内置控件——内置能实现就不自造，避免不必要的自定义控件
- **必须**：多页面复用的 UI 组合抽成 UserControl；需主题化 / 模板重写能力时用自定义控件
- **禁止**：把业务逻辑塞进 UserControl / 自定义控件（联动 `03` 章——逻辑在 ViewModel）
- **应该**：轻量扩展用附加属性 / 行为（`AttachedProperty` / `Behavior`），不无脑新建控件类型

## 2. 自定义控件约定

- **必须**：自定义控件继承 `Control`（或 `ContentControl` / 更具体基类），控件逻辑与外观分离——**逻辑在控件类，外观在模板**
- **必须**：默认样式放在 `Themes/Generic.xaml`（`ThemeInfo` 指向该字典），控件自带默认模板
- **必须**：模板部件用 `TemplatePart` 特性声明（`[TemplatePart(Name="PART_X", Type=typeof(...))]`），`OnApplyTemplate` 中获取
- **必须**：控件暴露的配置走依赖属性（`DependencyProperty`），支持绑定、动画与样式化
- **禁止**：自定义控件内做业务操作 / 直接访问 ViewModel 业务服务

## 3. 依赖属性（DependencyProperty）

- **必须**：自定义控件可绑定、可样式化的属性用依赖属性声明，**禁止**普通 CLR 属性（无法绑定 / 动画）
- **必须**：依赖属性命名 `OwnerType.PropertyNameProperty`（静态字段），属性名 PascalCase，包装器 `Get/SetValue`
- **必须**：依赖属性设置 `DefaultValue`，需要时给回调（`PropertyChangedCallback`）做联动更新
- **应该**：读多写少的依赖属性用 `FrameworkPropertyMetadataOptions` 配置优化（`AffectsArrange`、`AffectsRender` 等）
- **禁止**：在 `PropertyChangedCallback` 内做重操作（会高频触发，联动 `10` 章）

```csharp
// ❌ 普通 CLR 属性：无法 {Binding}、无法样式化、无法动画——控件属性失去 WPF 能力
public string Title { get; set; }

// ✅ 依赖属性：绑定/样式/动画全支持
public static readonly DependencyProperty TitleProperty =
    DependencyProperty.Register(
        nameof(Title), typeof(string), typeof(MyControl),
        new PropertyMetadata("默认标题"));

public string Title
{
    get => (string)GetValue(TitleProperty);
    set => SetValue(TitleProperty, value);
}
```

```csharp
// ❌ 属性回调里做重操作：每次值变化都执行，UI 线程卡顿（联动 10 章）
private static void OnTitleChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
{
    var ctl = (MyControl)d;
    var data = File.ReadAllText($"templates/{e.NewValue}.xaml");  // IO 在回调里
    ctl.ApplyTemplate(data);
}

// ✅ 回调只做轻量联动：重操作延迟/异步到不阻塞 UI 的地方
private static void OnTitleChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
{
    var ctl = (MyControl)d;
    ctl.RefreshPreview((string)e.NewValue);   // 内部异步加载，不阻塞布局线程
}
```

## 4. 附加属性（Attached Property）

- **必须**：扩展已有控件能力且需 XAML 赋值时用附加属性（如 `Grid.Row`、`DockPanel.Dock` 模式）
- **必须**：附加属性命名 `OwnerType.PropertyNameProperty`，提供静态 `Get/Set` 方法
- **禁止**：滥用附加属性做全局状态（可读性差），能用继承 / 依赖属性表达就优先原生方式
- **应该**：附加属性带 `PropertyChangedCallback` 时注意元素生命周期（卸载时清理，联动 `10` 章）

## 5. 模板与样式

- **必须**：控件模板（`ControlTemplate`）在资源中定义，**禁止**内联在控件上（不可复用 + 难维护）
- **必须**：模板用 `{TemplateBinding}` 绑定控件属性（模板与控件耦合的最小通道），复杂场景用 `{RelativeSource TemplatedParent}`
- **必须**：模板内命名部件用 `PART_` 前缀，与 `TemplatePart` 声明一致（见第 2 节）
- **应该**：模板编写用 `Setter` + `Trigger` + `VisualState` 实现视觉反馈，**禁止**在模板里写业务逻辑
- **禁止**：控件外部修改模板部件依赖的实现细节（只依赖 `TemplatePart` 契约）

## 6. 控件分组与集合

- **必须**：列表展示用带虚拟化的集合控件（`ListBox`/`ListView`/`DataGrid`），长列表**禁止** `ItemsControl` 堆全部元素（联动 `10` 章）
- **必须**：`DataGrid` 列绑定明确（`Binding` 属性路径），复杂列用 `DataGridTemplateColumn` + `DataTemplate`
- **应该**：集合项模板复用 `DataTemplate`（联动 `04` 章第 5 节），不每项内联
- **禁止**：`ItemsSource` 绑定到 `List<T>` 后依赖手动刷新（联动 `05` 章第 2 节）

## 7. 输入与命令

- **必须**：控件交互优先绑定命令（`Command` / `CommandParameter`），**禁止**code-behind 处理业务交互
- **必须**：`CommandParameter` 传需要的数据（项、ID），命令 `CanExecute` 联动（联动 `03` 章第 3 节）
- **应该**：键盘交互用 `InputBindings` / `KeyBinding` 声明，提升可访问性（联动 `14` 章）
- **禁止**：`CommandParameter` 传 UI 元素本身（`Button` 等）——ViewModel 不应感知 UI 类型

```xml
<!-- ❌ 传 UI 元素：ViewModel 收到 Button，被迫感知 UI 类型 -->
<Button Command="{Binding DeleteCommand}"
        CommandParameter="{Binding RelativeSource={RelativeSource Self}}" />

<!-- ✅ 传数据：ViewModel 只处理业务数据 -->
<Button Command="{Binding DeleteCommand}"
        CommandParameter="{Binding}">   <!-- 传当前数据项本身 -->
```

```csharp
// ViewModel 侧：
public ICommand DeleteCommand { get; }
DeleteCommand = new RelayCommand<Order>(DeleteOrder);   // 参数类型 Order，非 UI 元素
private void DeleteOrder(Order order) => _repo.Remove(order.Id);
```

## 8. 绘制与图形（联动 `08` 章）

- **必须**：静态图形优先 `Path` + `Geometry`（`StreamGeometry`），**禁止**用 `Ellipse`/`Rectangle`/`Line` 堆大量 `Shape`（每个都是独立 UI 元素，联动 `10` 章）
- **必须**：动态高频图形用 `DrawingVisual` / `DrawingGroup`（非 UI 元素、批量绘制）
- **应该**：图标用 Path 数据（`svg-to-xaml-path` 产物）而非图片，支持主题换色（`Fill="{DynamicResource ...}"`）
- **禁止**：循环中 `new` 图形对象与 `Brush`（联动 `10` 章 Freeze 与共享）

## 9. 控件测试（联动 `11` 章）

- **必须**：自定义控件可脱离业务数据测试（依赖属性 + 模板为纯 UI 契约）
- **应该**：复杂控件行为配 UI 自动化测试（FlaUI / White），保证模板部件与交互回归
- **禁止**：控件内部依赖外部单例 / 静态服务（不可测 + 难维护，联动 `03` 章）
