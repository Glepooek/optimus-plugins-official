---
name: wpf-xaml-performance
description: 审查和优化 WPF XAML 代码性能。当用户提到"WPF 性能优化"、"XAML 优化"、"界面卡顿"、"ListView/ListBox 滚动慢"、"WPF 内存占用高"、"启动慢"、"渲染慢"或请求审查 WPF/XAML 代码性能时使用此 skill。适用于审查现有代码和编写新代码时的性能指导。
---

# WPF XAML 性能优化 Skill

本 skill 基于 Microsoft 官方 WPF 性能优化最佳实践，帮助你识别和修复 WPF 应用程序中的性能问题。

## 使用场景

使用此 skill 当：
- 审查现有 WPF/XAML 代码的性能问题
- 编写新的 WPF 代码时需要性能指导
- 遇到界面卡顿、滚动不流畅、内存占用高等问题
- 需要优化应用启动时间或渲染性能

## 工作流程

按照以下步骤进行性能审查和优化：

### 1. 收集信息

首先确定审查范围：
- 询问用户具体的性能问题（如启动慢、滚动卡顿、内存占用高）
- 识别需要审查的文件（如果用户未指定，使用 Glob 查找 *.xaml 和 *.xaml.cs 文件）
- 了解应用的使用场景和性能目标

### 2. 执行性能扫描

按以下优先级依次检查各个性能领域，使用 Grep 和 Read 工具查找代码模式。

#### 2.1 硬件渲染优化（高优先级）

**检查点：**
- 检查是否禁用了硬件加速
- 查找过度使用 BitmapEffect（已过时，性能极差）
- 检查不必要的视觉效果叠加

**反模式示例：**
```xml
<!-- ❌ 差：BitmapEffect 性能极差 -->
<Button>
  <Button.BitmapEffect>
    <DropShadowBitmapEffect />
  </Button.BitmapEffect>
</Button>

<!-- ✅ 好：使用 Effect 替代 -->
<Button>
  <Button.Effect>
    <DropShadowEffect />
  </Button.Effect>
</Button>
```

#### 2.2 布局和设计优化（高优先级）

**检查点：**
- 检查是否使用了性能较差的面板（如过度嵌套的 Grid）
- 查找 UpdateLayout() 的不当调用
- 检查是否自下而上构建可视化树

**关键原则：**
- 面板性能排序：Canvas > StackPanel > DockPanel > Grid
- 始终自上而下构建可视化树（先添加父级，再添加子级）
- 避免不必要的 UpdateLayout() 调用

**反模式示例：**
```xml
<!-- ❌ 差：过度使用 Grid，布局计算复杂 -->
<Grid>
  <Grid.RowDefinitions>
    <RowDefinition />
    <RowDefinition />
  </Grid.RowDefinitions>
  <TextBlock Grid.Row="0" Text="Name:" />
  <TextBox Grid.Row="1" />
</Grid>

<!-- ✅ 好：简单布局用 StackPanel -->
<StackPanel>
  <TextBlock Text="Name:" />
  <TextBox />
</StackPanel>
```

```csharp
// ❌ 差：自下而上构建树
for (int i = 0; i < 150; i++)
{
    var childPanel = new DockPanel();
    parentPanel.Children.Add(childPanel);
    parentPanel = childPanel;
}
myCanvas.Children.Add(parentPanel); // 最后添加到父级

// ✅ 好：自上而下构建树
myCanvas.Children.Add(parentPanel); // 先添加父级
for (int i = 0; i < 150; i++)
{
    var childPanel = new DockPanel();
    parentPanel.Children.Add(childPanel);
    parentPanel = childPanel;
}
```

#### 2.3 图形和图像优化（高优先级）

**检查点：**
- 查找使用 Shape 而非 Drawing 的场景
- 检查是否使用了 StreamGeometry 优化复杂几何图形
- 查找未设置 BitmapScalingMode 的动画图像
- 检查 TileBrush 是否使用了 CachingHint

**关键原则：**
- Drawing 比 Shape 性能更好（不派生自 FrameworkElement）
- 复杂几何图形使用 StreamGeometry 而非 PathGeometry
- 图像缩放动画使用 BitmapScalingMode.LowQuality
- 静态内容的 TileBrush 设置 CachingHint.Cache

**反模式示例：**
```xml
<!-- ❌ 差：使用 Shape（继承自 FrameworkElement，开销大） -->
<Canvas>
  <Ellipse Fill="Blue" Width="100" Height="100" />
  <Rectangle Fill="Red" Width="50" Height="50" />
</Canvas>

<!-- ✅ 好：使用 DrawingBrush -->
<Canvas>
  <Canvas.Background>
    <DrawingBrush>
      <DrawingBrush.Drawing>
        <DrawingGroup>
          <GeometryDrawing Brush="Blue">
            <GeometryDrawing.Geometry>
              <EllipseGeometry Center="50,50" RadiusX="50" RadiusY="50" />
            </GeometryDrawing.Geometry>
          </GeometryDrawing>
          <GeometryDrawing Brush="Red">
            <GeometryDrawing.Geometry>
              <RectangleGeometry Rect="0,0,50,50" />
            </GeometryDrawing.Geometry>
          </GeometryDrawing>
        </DrawingGroup>
      </DrawingBrush.Drawing>
    </DrawingBrush>
  </Canvas.Background>
</Canvas>
```

```xml
<!-- ❌ 差：PathGeometry 用于复杂几何图形 -->
<Path Fill="Black">
  <Path.Data>
    <PathGeometry>
      <PathFigure StartPoint="10,100">
        <LineSegment Point="100,100" />
        <LineSegment Point="100,50" />
      </PathFigure>
    </PathGeometry>
  </Path.Data>
</Path>

<!-- ✅ 好：StreamGeometry 更高效 -->
<Path Data="F0 M10,100 L100,100 100,50Z" Fill="Black" />
```

```csharp
// ❌ 差：图像缩放动画未设置 BitmapScalingMode
// 默认使用高质量算法，性能差

// ✅ 好：动画时使用低质量模式
RenderOptions.SetBitmapScalingMode(MyImage, BitmapScalingMode.LowQuality);
```

```csharp
// ❌ 差：TileBrush 未启用缓存
var brush = new DrawingBrush();
// 每帧都重新渲染

// ✅ 好：启用缓存
var brush = new DrawingBrush();
RenderOptions.SetCachingHint(brush, CachingHint.Cache);
RenderOptions.SetCacheInvalidationThresholdMinimum(brush, 0.5);
RenderOptions.SetCacheInvalidationThresholdMaximum(brush, 2.0);
```

#### 2.4 对象行为优化（中优先级）

**检查点：**
- 查找未清理的事件处理器（导致内存泄漏）
- 检查是否应该使用 Freezable.Freeze()
- 查找不必要的依赖属性使用
- 检查是否启用了 UI 虚拟化

**关键原则：**
- 及时移除不再需要的事件处理器
- 不可变对象调用 Freeze() 提升性能
- 大数据集使用 VirtualizingStackPanel 和虚拟化

**反模式示例：**
```csharp
// ❌ 差：事件处理器未清理，导致内存泄漏
public class MyControl : UserControl
{
    public MyControl()
    {
        SomeObject.SomeEvent += OnSomeEvent;
    }
    // 析构时未移除事件处理器
}

// ✅ 好：实现 IDisposable 并清理事件
public class MyControl : UserControl, IDisposable
{
    public MyControl()
    {
        SomeObject.SomeEvent += OnSomeEvent;
    }
    
    public void Dispose()
    {
        SomeObject.SomeEvent -= OnSomeEvent;
    }
}
```

```csharp
// ❌ 差：未冻结不可变的 Brush
var brush = new SolidColorBrush(Colors.Blue);
for (int i = 0; i < 10; i++)
{
    rectangles[i].Fill = brush;
}
// 每个 Rectangle 都监听 brush 的 Changed 事件

// ✅ 好：冻结 Brush，避免事件开销
var brush = new SolidColorBrush(Colors.Blue);
brush.Freeze(); // 冻结后无法修改，性能提升 4-5 倍
for (int i = 0; i < 10; i++)
{
    rectangles[i].Fill = brush;
}
```

```xml
<!-- ❌ 差：大数据集未启用虚拟化 -->
<ListBox ItemsSource="{Binding LargeCollection}">
  <ListBox.ItemsPanel>
    <ItemsPanelTemplate>
      <StackPanel /> <!-- 会为所有项创建容器 -->
    </ItemsPanelTemplate>
  </ListBox.ItemsPanel>
</ListBox>

<!-- ✅ 好：启用虚拟化 -->
<ListBox ItemsSource="{Binding LargeCollection}">
  <!-- ListBox 默认使用 VirtualizingStackPanel -->
  <!-- 或显式启用： -->
  <ListBox.ItemsPanel>
    <ItemsPanelTemplate>
      <VirtualizingStackPanel VirtualizingPanel.VirtualizationMode="Recycling" />
    </ItemsPanelTemplate>
  </ListBox.ItemsPanel>
</ListBox>
```

#### 2.5 应用程序资源优化（中优先级）

**检查点：**
- 查找 DynamicResource 的不当使用（应使用 StaticResource）
- 检查是否共享可复用的资源（如 Brush、Style）
- 查找重复定义的资源

**关键原则：**
- 优先使用 StaticResource（编译时查找）
- 仅在需要运行时更新时使用 DynamicResource
- 共享 Brush 而非为每个元素创建新实例

**反模式示例：**
```xml
<!-- ❌ 差：内联定义，无法共享 -->
<StackPanel>
  <Button>
    <Button.Background>
      <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
        <GradientStop Color="Blue" Offset="0" />
        <GradientStop Color="White" Offset="1" />
      </LinearGradientBrush>
    </Button.Background>
  </Button>
  <Button>
    <Button.Background>
      <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
        <GradientStop Color="Blue" Offset="0" />
        <GradientStop Color="White" Offset="1" />
      </LinearGradientBrush>
    </Button.Background>
  </Button>
</StackPanel>

<!-- ✅ 好：定义为资源并共享 -->
<StackPanel>
  <StackPanel.Resources>
    <LinearGradientBrush x:Key="MyBrush" StartPoint="0,0" EndPoint="1,1">
      <GradientStop Color="Blue" Offset="0" />
      <GradientStop Color="White" Offset="1" />
    </LinearGradientBrush>
  </StackPanel.Resources>
  
  <Button Background="{StaticResource MyBrush}" />
  <Button Background="{StaticResource MyBrush}" />
</StackPanel>
```

```xml
<!-- ❌ 差：使用 DynamicResource（运行时开销） -->
<Label Foreground="{DynamicResource {x:Static SystemColors.ControlBrushKey}}" />

<!-- ✅ 好：使用 StaticResource -->
<Label Foreground="{StaticResource MyBrush}" />
```

#### 2.6 文本优化（中优先级）

**检查点：**
- 查找 FlowDocument 的不当使用（应使用 TextBlock）
- 检查是否在 FlowDocument 中使用了 TextBlock（应使用 Run）
- 查找启用了断字的场景（IsHyphenationEnabled）
- 检查是否启用了最佳段落（IsOptimalParagraphEnabled）

**关键原则：**
- TextBlock < Label < FlowDocument（性能由高到低）
- FlowDocument 中使用 Run 而非 TextBlock
- 避免不必要的断字和最佳段落功能

**反模式示例：**
```xml
<!-- ❌ 差：简单文本使用 FlowDocument -->
<FlowDocumentScrollViewer>
  <FlowDocument>
    <Paragraph>
      <Run Text="Hello World" />
    </Paragraph>
  </FlowDocument>
</FlowDocumentScrollViewer>

<!-- ✅ 好：简单文本使用 TextBlock -->
<TextBlock Text="Hello World" />
```

```xml
<!-- ❌ 差：FlowDocument 中使用 TextBlock -->
<FlowDocument>
  <Paragraph>
    <TextBlock Text="Line one" />
  </Paragraph>
</FlowDocument>

<!-- ✅ 好：FlowDocument 中使用 Run -->
<FlowDocument>
  <Paragraph>
    <Run Text="Line one" />
  </Paragraph>
</FlowDocument>
```

```xml
<!-- ❌ 差：不必要的断字 -->
<TextBlock TextWrapping="Wrap" IsHyphenationEnabled="True">
  <!-- 启动 COM 互操作，性能开销 -->
</TextBlock>

<!-- ✅ 好：仅在必要时启用 -->
<TextBlock TextWrapping="Wrap">
  <!-- 默认 IsHyphenationEnabled="False" -->
</TextBlock>
```

#### 2.7 数据绑定优化（高优先级）

**检查点：**
- 查找绑定到 IEnumerable 而非 IList 的场景
- 检查是否使用了 ObservableCollection（而非 List）
- 查找不必要的双向绑定（应使用 OneWay）
- 检查 UpdateSourceTrigger 设置是否合理

**关键原则：**
- 绑定到 DependencyProperty 性能最佳
- 动态集合使用 ObservableCollection 而非 List
- 优先绑定到 IList 而非 IEnumerable
- 默认使用 OneWay 绑定，仅在必要时使用 TwoWay

**反模式示例：**
```csharp
// ❌ 差：使用 List，不会自动通知变化
public List<Employee> Employees { get; set; }
// 添加/删除员工时，ListBox 不会更新

// ✅ 好：使用 ObservableCollection
public ObservableCollection<Employee> Employees { get; set; }
// 自动通知 UI 更新，性能提升 80 倍
```

```xml
<!-- ❌ 差：绑定到 IEnumerable -->
<ListBox ItemsSource="{Binding EmployeesEnumerable}" />
<!-- WPF 会创建包装器 IList，额外开销 -->

<!-- ✅ 好：绑定到 IList -->
<ListBox ItemsSource="{Binding EmployeesList}" />
```

```xml
<!-- ❌ 差：不必要的 TwoWay 绑定 -->
<TextBlock Text="{Binding Name, Mode=TwoWay}" />
<!-- TextBlock 只读，不需要 TwoWay -->

<!-- ✅ 好：使用 OneWay -->
<TextBlock Text="{Binding Name}" />
<!-- 默认 Mode=OneWay -->
```

#### 2.8 控件优化（高优先级）

**检查点：**
- 检查 ListBox/ListView 是否启用了虚拟化
- 查找禁用虚拟化的场景（ScrollViewer.CanContentScroll="False"）
- 检查是否使用了容器回收（VirtualizationMode.Recycling）
- 查找 ComboBox 和 TreeView 的虚拟化设置

**关键原则：**
- ListBox/ListView 默认启用虚拟化，不要禁用
- 使用 Recycling 模式提升滚动性能
- TreeView 需要显式启用虚拟化

**反模式示例：**
```xml
<!-- ❌ 差：禁用了虚拟化 -->
<ListBox ItemsSource="{Binding LargeCollection}"
         ScrollViewer.CanContentScroll="False">
  <!-- 会为所有项创建容器，性能极差 -->
</ListBox>

<!-- ✅ 好：保持虚拟化启用 -->
<ListBox ItemsSource="{Binding LargeCollection}">
  <!-- 默认启用虚拟化 -->
</ListBox>
```

```xml
<!-- ❌ 差：未启用容器回收 -->
<ListBox ItemsSource="{Binding LargeCollection}">
  <!-- 默认 VirtualizationMode.Standard -->
</ListBox>

<!-- ✅ 好：启用容器回收 -->
<ListBox ItemsSource="{Binding LargeCollection}"
         VirtualizingPanel.VirtualizationMode="Recycling">
  <!-- 滚动性能提升显著 -->
</ListBox>
```

```xml
<!-- ❌ 差：TreeView 未启用虚拟化 -->
<TreeView ItemsSource="{Binding TreeData}">
  <!-- 默认未启用虚拟化 -->
</TreeView>

<!-- ✅ 好：启用虚拟化 -->
<TreeView ItemsSource="{Binding TreeData}"
          VirtualizingPanel.IsVirtualizing="True"
          VirtualizingPanel.VirtualizationMode="Recycling">
</TreeView>
```

#### 2.9 其他优化建议（低优先级）

**检查点：**
- 查找 Opacity < 1 的场景（应在 Brush 上设置）
- 检查 CompositionTarget.Rendering 事件的使用
- 查找 ScrollBarVisibility="Auto" 的使用
- 检查导航场景是否使用了对象导航（应使用 URI）

**反模式示例：**
```xml
<!-- ❌ 差：在元素上设置 Opacity -->
<Border Opacity="0.5">
  <Rectangle Fill="Blue" />
</Border>
<!-- 需要创建临时表面，性能开销 -->

<!-- ✅ 好：在 Brush 上设置 Opacity -->
<Border>
  <Rectangle>
    <Rectangle.Fill>
      <SolidColorBrush Color="Blue" Opacity="0.5" />
    </Rectangle.Fill>
  </Rectangle>
</Border>
```

```xml
<!-- ❌ 差：使用 ScrollBarVisibility.Auto -->
<ScrollViewer VerticalScrollBarVisibility="Auto">
  <!-- 每次布局都需要计算是否显示滚动条 -->
</ScrollViewer>

<!-- ✅ 好：明确指定 -->
<ScrollViewer VerticalScrollBarVisibility="Visible">
  <!-- 或 Hidden、Disabled -->
</ScrollViewer>
```

#### 2.10 启动时间优化（中优先级）

**检查点：**
- 检查是否有启动画面（SplashScreen）
- 查找启动时的重量级初始化
- 检查是否使用了 Ngen.exe
- 查找模块加载和程序集引用

**优化建议：**
- 添加启动画面改善感知启动时间
- 延迟非关键初始化到启动后
- 对大型程序集使用 Ngen.exe 预编译
- 减少不必要的程序集引用

### 3. 生成性能报告

按以下格式输出性能分析报告：

```markdown
# WPF XAML 性能分析报告

## 概述
- 扫描文件数：[数量]
- 发现问题数：[数量]
- 严重性分布：[高/中/低优先级数量]

## 问题详情

### [严重程度] [问题类别]：[问题描述]

**位置：** [文件路径:行号]

**问题说明：**
[详细说明性能影响和原因]

**当前代码：**
```xaml/csharp
[有问题的代码]
```

**优化建议：**
```xaml/csharp
[优化后的代码]
```

**性能影响：**
- [具体性能指标，如"渲染时间减少 XX%"、"内存占用降低 XX%"]

**参考资料：**
- [Microsoft 官方文档链接]

---

[重复以上格式列出所有问题]

## 优化优先级建议

### 高优先级（立即修复）
1. [问题描述]
2. ...

### 中优先级（计划修复）
1. [问题描述]
2. ...

### 低优先级（可选优化）
1. [问题描述]
2. ...

## 最佳实践总结

[基于发现的问题，总结适用于该项目的最佳实践]
```

## 输出格式

根据用户需求调整输出格式：

**审查现有代码时：**
- 生成详细的性能分析报告
- 包含问题位置、严重程度、优化建议
- 提供代码前后对比
- 给出优化优先级建议

**编写新代码时：**
- 提供性能最佳实践指导
- 展示推荐的代码模式
- 说明各种选择的性能权衡
- 给出具体的实现建议

## 性能指标参考

以下是常见优化的性能提升参考（来自 Microsoft 官方文档）：

| 优化项 | 性能提升 |
|--------|---------|
| List → ObservableCollection | ~80x（1656ms → 20ms） |
| Shape → Drawing | ~50%内存占用降低 |
| 启用虚拟化 | ~70x（3210ms → 46ms） |
| 冻结 Brush | ~4-5x（972字节 → 212字节） |
| StaticResource vs DynamicResource | ~3-5% |
| 自上而下构建树 | ~30x（366ms → 11ms） |
| StreamGeometry vs PathGeometry | ~20-30% |
| BitmapScalingMode.LowQuality | ~2-3x |

## 注意事项

1. **平衡性能和功能**：不是所有优化都适用于所有场景，需要根据实际需求权衡
2. **测量优先**：建议在优化前后使用性能分析工具（如 WPF Performance Profiling Tools）测量实际效果
3. **避免过早优化**：专注于解决实际性能瓶颈，而非盲目优化
4. **考虑可维护性**：某些优化会增加代码复杂度，需要权衡利弊

## 工具推荐

- **WPF Performance Suite**：分析渲染性能
- **Visual Studio Profiler**：分析 CPU 和内存使用
- **PerfView**：分析启动时间和内存分配
- **Snoop**：实时检查可视化树和属性

## 参考资源

- [优化 WPF 应用程序性能 - Microsoft Learn](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/advanced/optimizing-wpf-application-performance)
- [规划应用程序性能](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/advanced/planning-for-application-performance)
- [布局和设计优化](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/advanced/optimizing-performance-layout-and-design)
- [数据绑定优化](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/advanced/optimizing-performance-data-binding)
- [控件性能优化](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/advanced/optimizing-performance-controls)
