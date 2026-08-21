# 07 · 资源、样式与主题

> 更新历史：2026-08-21 创建。资源字典合并清单与 `wpf-project-conventions` skill 第 4 节互为事实来源。

资源字典是 WPF 的可复用资产库。本篇约束资源组织、样式体系、主题切换与 Freezable 使用。

## 1. 资源字典组织

- **必须**：资源按职责拆分字典（`Colors.xaml` / `Styles.xaml` / `DataTemplates.xaml` / `Converters.xaml`），**禁止**一个巨型字典
- **必须**：资源字典在 `App.xaml` 合并清单中登记（联动 `02` 章第 2 节），新增字典必须同步登记
- **应该**：字典层级合理——应用级（通用样式）→ 模块级（页面共享）→ 页面局部（仅本页），资源就近放置
- **禁止**：同一 `x:Key` 在多级重复定义造成查找歧义（就近原则掩盖问题）

## 2. 资源键命名

- **必须**：`x:Key` 用 PascalCase，禁止空格与 `/`（与 `wpf-project-conventions` skill 第 5 节一致）
- **应该**：键名语义化并带类型提示（`ButtonPrimaryStyle`、`ErrorBrush`、`LoginDataTemplate`），**禁止**通用名（`Style1`、`Color1`）
- **必须**：资源键全局唯一（应用级），跨字典冲突在合并时报错 / 遮蔽——用前缀区分模块（`Login_ErrorBrush` 或命名空间级前缀）

## 3. 样式体系

- **必须**：样式在资源字典集中定义，显式 `TargetType`
- **必须**：通用样式（按钮、输入框、文本）定义为应用级默认样式（隐式 `Style` 或 `{x:Static}` 键引用），页面不重复定义
- **应该**：样式层次用 `BasedOn` 继承（基样式 → 变体），**禁止**复制粘贴整段样式
- **应该**：`x:Key` 样式与隐式样式分工——隐式只用于"所有该类型都用这个"，变体用显式键
- **禁止**：内联样式（`<Button><Button.Style>...`）散布页面，除非一次性覆盖

## 4. 主题与皮肤切换

- **必须**：主题相关资源（颜色、画刷、字体）用 `DynamicResource` 引用，保证切换时 UI 实时更新（联动 `04` 章第 2 节）
- **必须**：主题切换统一走"替换资源字典"机制（运行时 `MergedDictionaries` 增减），**禁止**逐控件手动改颜色
- **应该**：主题分暗/亮（或品牌色）由应用级配置控制，主题字典文件命名 `Theme.{Name}.xaml`，在 `App.xaml` 按当前配置合并
- **禁止**：主题切换时泄漏旧字典资源（卸载旧字典引用，联动 `10` 章内存）

## 5. Freezable 与资源共享

- **必须**：静态使用的 `Brush` / `Pen` / `Transform` / `Geometry` 等 `Freezable` 对象 `Freeze()`，多个元素共享同一实例（性能提升 4-5 倍，联动 `10` 章）
- **必须**：`Freeze()` 只在对象确认不再修改时调用（主题切换会变色的 Brush **禁止**冻结，联动 `wpf-xaml-performance` 边界场景第 4 条）
- **必须**：循环 / 动态场景中的 `SolidColorBrush` 等在循环外创建并冻结，**禁止**每次 `new`
- **禁止**：冻结后的对象再尝试修改（抛 `InvalidOperationException`）

```csharp
// ❌ 循环里每次 new Brush：每个元素一份实例 + 事件监听，1000 个元素就是 1000 个 Brush
for (int i = 0; i < 1000; i++)
    rects[i].Fill = new SolidColorBrush(Colors.Blue);

// ✅ 循环外创建一次、冻结后共享：无事件监听，性能提升 4-5 倍
var brush = new SolidColorBrush(Colors.Blue);
brush.Freeze();
for (int i = 0; i < 1000; i++)
    rects[i].Fill = brush;
```

```csharp
// ❌ 冻结后修改：抛 InvalidOperationException（Freeze 后对象只读）
var brush = new SolidColorBrush(Colors.Blue);
brush.Freeze();
brush.Color = Colors.Red;    // 运行期异常

// ✅ 只在确定不再变化时冻结；需要动态变化的 Brush 不冻结
var brush = new SolidColorBrush(Colors.Blue);
// ... 可能修改的阶段结束，确认不再变化后
if (brush.CanFreeze) brush.Freeze();
```

## 6. 资源可共享性检查

- **必须**：可共享资源（画刷、样式、模板、转换器）提到资源字典，**禁止**内联定义在控件上（无法复用 + 每元素一份实例）
- **禁止**：把带状态的资源对象（可变集合、缓存）放资源字典共享（多元素引用同一实例会互相干扰）

```xml
<!-- ❌ 内联定义：每个 Button 一份画刷实例，无法复用、主题无法整体替换 -->
<Button>
  <Button.Background>
    <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
      <GradientStop Color="Blue" Offset="0"/>
      <GradientStop Color="White" Offset="1"/>
    </LinearGradientBrush>
  </Button.Background>
</Button>

<!-- ✅ 提为资源：定义一次，多处引用，主题切换一处生效 -->
<Window.Resources>
  <LinearGradientBrush x:Key="HeaderBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="Blue" Offset="0"/>
    <GradientStop Color="White" Offset="1"/>
  </LinearGradientBrush>
</Window.Resources>
<Button Background="{StaticResource HeaderBrush}" />
```
- **应该**：资源中的代码（Converter、自定义控件）注册进字典时注意生命周期，避免长生命周期引用短生命周期对象（联动 `10` 章）

## 7. 图标与矢量资源

- **必须**：图标用 Path 数据（`svg-to-xaml-path` / `mastergo-icon-expoter` 产物）定义为资源，支持主题换色（`Fill="{DynamicResource IconBrush}"`）
- **必须**：图标资源集中管理（`Themes/Icons.xaml` 或图标字典目录），命名 `Icon{Name}`
- **禁止**：图标硬编码颜色（无法跟随主题切换）
- **禁止**：位图图标用于主题敏感场景（不支持换色，放大糊），矢量优先

## 8. 资源清理与内存（联动 `10` 章）

- **必须**：动态加载的字典在不再需要时移除引用，**禁止**持有全局 `Application.Current.Resources` 之外的强引用链
- **应该**：主题切换 / 模块卸载后核查资源引用（`DynamicResource` 订阅的清理）
- **禁止**：资源中放置长生命周期对象（Service、ViewModel 单例）——资源应只放声明式资产
