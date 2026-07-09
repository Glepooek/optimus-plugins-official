---
name: unipus-frontend-wpf-xaml-performance
version: 1.1.0
description: 识别并修复 WPF/XAML 性能问题的专家级 skill。当用户提到 WPF、XAML、Prism、MVVM、界面卡顿、ListView/ListBox 滚动慢、内存占用高、启动慢、渲染慢、Shape 元素多、数据绑定性能、虚拟化、ObservableCollection，或请求审查/优化 WPF 代码时立即使用此 skill。涵盖从硬件加速到数据绑定的全方位性能优化，特别擅长诊断虚拟化、Freezable、图形渲染和启动时间问题。无论是审查现有代码还是编写新代码都应该使用此 skill。
---

# WPF XAML 性能优化 Skill

本 skill 基于 Microsoft 官方 WPF 性能优化最佳实践，帮助快速识别和修复性能问题。

## 工作流程

### 1. 快速定位问题

首先确定问题范围和优先级：
- 询问具体症状（启动慢/滚动卡顿/内存高/渲染慢）
- 如果用户未指定文件，使用 `Glob "**/*.xaml"` 和 `Grep` 查找问题模式
- 按优先级扫描：数据绑定 > 控件虚拟化 > 图形渲染 > 启动优化 > 其他

### 2. 执行性能扫描

按以下检查点依次扫描代码，找到问题立即报告。

#### 检查点 1：数据绑定优化（最高优先级）

**为什么重要：** 使用 List 而非 ObservableCollection 会导致 UI 无法自动更新，强制刷新会带来巨大性能开销。正确使用可提升 **80 倍**性能（1656ms → 20ms）。

**扫描模式：**
```bash
Grep "List<.*> .*{ get" --type cs
Grep "IEnumerable<.*> .*{ get" --type cs
Grep "Mode=OneWay\|Mode=TwoWay" --glob "*.xaml" -C 1
Grep 'Binding.*Path=[A-Za-z]+\.[A-Za-z]+\.[A-Za-z]+\.' --glob "*.xaml"
Grep "Converter=" --glob "*.xaml"
```

**集合绑定：**
```csharp
// ❌ List 不会通知 UI 更新
public List<Employee> Employees { get; set; }
// ✅ ObservableCollection 自动通知
public ObservableCollection<Employee> Employees { get; set; }
```

```xml
<!-- ❌ 不必要的 TwoWay（TextBlock 只读）-->
<TextBlock Text="{Binding Name, Mode=TwoWay}" />
<!-- ✅ OneWay 即可 -->
<TextBlock Text="{Binding Name}" />
```

**OneTime 绑定（常量/不变属性）：** 常量属性若用 OneWay/TwoWay 会订阅 PropertyChanged 事件，浪费内存。
```xml
<!-- ❌ 版本号不变，却订阅了 PropertyChanged -->
<TextBlock Text="{Binding AppVersion}" />
<!-- ✅ OneTime 绑定只读取一次，不订阅任何事件 -->
<TextBlock Text="{Binding AppVersion, Mode=OneTime}" />
```

**深层属性访问链：** 超过 3 层的路径（如 `User.Department.Manager.Name`）每层都要建立监听，并且中间对象为 null 时会静默失败。在 ViewModel 暴露扁平属性。
```csharp
// ❌ XAML 中 Binding Path=User.Department.Manager.Name — 三层监听
// ✅ ViewModel 暴露扁平属性
public string ManagerName => User?.Department?.Manager?.Name ?? string.Empty;
```

**昂贵转换器缓存：** IValueConverter 每次绑定刷新都会调用，计算密集型转换器必须缓存结果。
```csharp
// ✅ 字典缓存转换结果
private readonly Dictionary<object, object> _cache = new();
public object Convert(object value, ...) {
    if (_cache.TryGetValue(value, out var cached)) return cached;
    return _cache[value] = DoExpensiveComputation(value);
}
```

#### 检查点 2：控件虚拟化（最高优先级）

**为什么重要：** 未启用虚拟化会导致为所有项创建 UI 容器，造成严重卡顿和内存占用。启用虚拟化可将性能提升 **70 倍**（3210ms → 46ms）。

**扫描模式：**
```bash
Grep "ScrollViewer.CanContentScroll=\"False\"" --glob "*.xaml"
Grep "<StackPanel" --glob "*.xaml" -A 2
Grep "<TreeView" --glob "*.xaml" -A 3
Grep "<ListBox\|<ListView" --glob "*.xaml" -A 5
Grep "VirtualizationMode" --glob "*.xaml"  # 未出现则缺失 Recycling 模式
```

**独立问题：未启用容器回收（VirtualizationMode=Recycling）**

默认虚拟化模式 `Standard` 在滚动时销毁/重建容器，`Recycling` 模式复用容器对象，避免 GC 压力，滚动更流畅。若扫描发现 ListBox/ListView 中无 `VirtualizationMode=Recycling`，应主动添加。

**虚拟化与 ItemTemplate 布局：**
```xml
<!-- ❌ 禁用虚拟化 -->
<ListBox ScrollViewer.CanContentScroll="False" ItemsSource="{Binding Items}" />

<!-- ❌ 缺少 VirtualizationMode=Recycling，默认 Standard 模式销毁/重建容器 -->
<ListBox VirtualizingPanel.IsVirtualizing="True" ItemsSource="{Binding Items}" />

<!-- ✅ 启用容器回收 + 单行 ItemTemplate 用 StackPanel -->
<ListBox VirtualizingPanel.VirtualizationMode="Recycling" ItemsSource="{Binding Items}">
  <ListBox.ItemTemplate>
    <DataTemplate>
      <StackPanel Orientation="Horizontal">
        <TextBlock Text="{Binding Name}" Width="120" />
        <TextBlock Text="{Binding Age}" />
      </StackPanel>
    </DataTemplate>
  </ListBox.ItemTemplate>
</ListBox>

<!-- ✅ TreeView 需要显式启用 -->
<TreeView VirtualizingPanel.IsVirtualizing="True"
          VirtualizingPanel.VirtualizationMode="Recycling" />
```

#### 检查点 3：图形渲染优化（高优先级）

**为什么重要：** Shape 元素（Ellipse/Rectangle）继承自 FrameworkElement，每个都是独立 UI 元素，参与完整布局/命中测试。动态图表在循环中创建大量 Shape 会造成内存暴涨和渲染阻塞。改用 Drawing 层次结构可减少 **50% 内存**并提升渲染速度 **50-100 倍**。

**扫描模式：**
```bash
Grep "<Ellipse\|<Rectangle\|<Path" --glob "*.xaml" -C 2
Grep "new Ellipse\|new Rectangle\|new Path" --type cs
Grep "PathGeometry\|new SolidColorBrush" --type cs
```

**反模式：循环中创建 Shape 和 Brush**
```csharp
// ❌ 每次循环创建新 Shape 和新 Brush — 大量 UI 元素 + 大量 Brush 实例
for (int i = 0; i < dataPoints.Count; i++)
{
    var dot = new Ellipse
    {
        Fill = new SolidColorBrush(Colors.Blue), // ❌ 每次 new，不共享
        Width = 6, Height = 6
    };
    canvas.Children.Add(dot);
}
```

**方案 A：DrawingVisual + VisualCollection（最佳，适合动态图表）**

DrawingVisual 不是 UIElement，无布局/事件开销，直接通过 DrawingContext 批量绘制，性能最佳。
```csharp
// ✅ 自定义 Visual Host + DrawingVisual
public class ChartVisualHost : FrameworkElement
{
    private readonly VisualCollection _visuals;
    public ChartVisualHost() => _visuals = new VisualCollection(this);
    protected override int VisualChildrenCount => _visuals.Count;
    protected override Visual GetVisualChild(int index) => _visuals[index];

    // 共享 Brush — 在循环外创建并冻结，所有点复用同一实例
    private static readonly Brush _dotBrush = Brushes.Blue; // 系统 Brush 已冻结

    public void RenderDataPoints(IEnumerable<Point> points)
    {
        _visuals.Clear();
        var dv = new DrawingVisual();
        using (DrawingContext dc = dv.RenderOpen()) // 单次 DrawingContext，批量绘制
        {
            foreach (var pt in points)
                dc.DrawEllipse(_dotBrush, null, pt, 3, 3);
        }
        _visuals.Add(dv);
    }
}
```

**方案 B：DrawingGroup + GeometryDrawing（适合静态/XAML 组合图形）**

DrawingGroup 将多个 Drawing 对象组合为一个绘图树，适合在 XAML 中声明或在代码中组合点集与连线集。
```csharp
// ✅ DrawingGroup 组合点集和连线集
var group = new DrawingGroup();
var linePen = new Pen(Brushes.Gray, 1); linePen.Freeze();
var dotBrush = new SolidColorBrush(Colors.Blue); dotBrush.Freeze(); // 循环外创建并冻结

using (var dc = group.Open())
{
    foreach (var seg in lineSegments)
        dc.DrawLine(linePen, seg.Start, seg.End);
    foreach (var pt in dataPoints)
        dc.DrawEllipse(dotBrush, null, pt, 3, 3);
}
var drawing = new DrawingImage(group);
```

```xml
<!-- ✅ XAML 中 DrawingGroup 组合多个 GeometryDrawing -->
<DrawingBrush>
  <DrawingBrush.Drawing>
    <DrawingGroup>
      <GeometryDrawing Brush="Blue">
        <GeometryDrawing.Geometry><EllipseGeometry Center="50,50" RadiusX="50" RadiusY="50" /></GeometryDrawing.Geometry>
      </GeometryDrawing>
      <GeometryDrawing Brush="Red">
        <GeometryDrawing.Geometry><RectangleGeometry Rect="10,10,30,20" /></GeometryDrawing.Geometry>
      </GeometryDrawing>
    </DrawingGroup>
  </DrawingBrush.Drawing>
</DrawingBrush>
```

**StreamGeometry 替代 PathGeometry：**
```csharp
// ❌ PathGeometry - 可修改但慢
var geometry = new PathGeometry();

// ✅ StreamGeometry - 只读但快 20-30%，冻结后更快
var geometry = new StreamGeometry();
using (var ctx = geometry.Open())
{
    ctx.BeginFigure(new Point(10, 100), true, true);
    ctx.LineTo(new Point(100, 100), true, false);
}
geometry.Freeze();
```

#### 检查点 4：冻结 Freezable 对象（关键）

**为什么重要：** 未冻结的 Brush/Pen 等对象会为每个使用者维护 Changed 事件监听。冻结可提升 **4-5 倍**性能。同时，在循环中 `new SolidColorBrush(...)` 应移到循环外并冻结，所有元素共享同一实例。

**扫描模式：** `Grep "new SolidColorBrush\|new LinearGradientBrush\|new Pen" --type cs`

```csharp
// ❌ 循环内每次 new SolidColorBrush — 大量实例，每个都有事件监听
for (int i = 0; i < 1000; i++)
    rectangles[i].Fill = new SolidColorBrush(Colors.Blue);

// ✅ 循环外创建一次，冻结后共享 — 无事件监听，性能提升 4-5 倍
var brush = new SolidColorBrush(Colors.Blue);
brush.Freeze();
for (int i = 0; i < 1000; i++)
    rectangles[i].Fill = brush;
```

#### 检查点 5：启动时间优化（高优先级）

**为什么重要：** 同步加载大量资源会阻塞主线程，用户只能盯着空白窗口等待。可将启动时间从 8-10 秒优化到 0.5-1 秒（**90% 改善**）。

**扫描模式：**
```bash
Grep "SplashScreen" --type cs
Grep "Application_Startup\|OnStartup" --type cs -A 20
Grep "MergedDictionaries" --glob "*.xaml"
```

**1. 添加启动画面**
```csharp
var splash = new SplashScreen("SplashScreen.png");
splash.Show(true, true);
```

**2. 延迟非关键初始化**
```csharp
// ❌ 构造函数中同步初始化，阻塞 2-4 秒
public MainWindow() { InitializeComponent(); LoadAllResourceDictionaries(); InitializeDatabase(); }

// ✅ Loaded 事件中异步初始化
public MainWindow()
{
    InitializeComponent();
    this.Loaded += async (s, e) => { await Task.Run(() => InitializeDatabase()); await LoadModulesAsync(); };
}
```

**3. 按需加载资源字典**
```csharp
// ❌ App.xaml 一次性加载 50 个资源字典 — 延长启动时间
// ✅ 模块初始化时动态加载
var uri = new Uri($"Styles/{moduleName}.xaml", UriKind.Relative);
Application.Current.Resources.MergedDictionaries.Add(new ResourceDictionary { Source = uri });
```

**4. Ngen.exe / ReadyToRun（改善冷启动）**

```bash
ngen install YourApp.exe  # 安装时运行（需管理员）；.NET 6+ 用 <PublishReadyToRun>true</PublishReadyToRun>
```

#### 检查点 6：布局优化（中优先级）

**为什么重要：** Grid 布局计算比 Canvas/StackPanel 复杂，自下而上构建树导致大量重复布局计算。正确构建可提升 **30 倍**性能（366ms → 11ms）。

**关键原则：** 面板性能 Canvas > StackPanel > DockPanel > Grid；始终自上而下构建可视化树；ItemTemplate 简单布局优先 StackPanel。

```csharp
// ❌ 自下而上构建 - 大量重复布局
for (int i = 0; i < 150; i++) { var child = new DockPanel(); parentPanel.Children.Add(child); parentPanel = child; }
myCanvas.Children.Add(parentPanel);

// ✅ 自上而下构建 - 布局只算一次
myCanvas.Children.Add(parentPanel);
for (int i = 0; i < 150; i++) { var child = new DockPanel(); parentPanel.Children.Add(child); parentPanel = child; }
```

#### 检查点 7：资源优化（中优先级）

**扫描模式：** `Grep "DynamicResource" --glob "*.xaml"`

```xml
<!-- ❌ 内联定义无法共享 -->
<Button><Button.Background><LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
  <GradientStop Color="Blue" Offset="0" /><GradientStop Color="White" Offset="1" />
</LinearGradientBrush></Button.Background></Button>

<!-- ✅ 定义为资源并用 StaticResource 引用 -->
<Window.Resources>
  <LinearGradientBrush x:Key="MyBrush" StartPoint="0,0" EndPoint="1,1">
    <GradientStop Color="Blue" Offset="0" /><GradientStop Color="White" Offset="1" />
  </LinearGradientBrush>
</Window.Resources>
<Button Background="{StaticResource MyBrush}" />
```

#### 检查点 8：其他常见问题

```xml
<!-- ❌ BitmapEffect 已过时，性能极差 -->
<Button><Button.BitmapEffect><DropShadowBitmapEffect /></Button.BitmapEffect></Button>
<!-- ✅ 使用 Effect 替代 -->
<Button><Button.Effect><DropShadowEffect /></Button.Effect></Button>

<!-- ❌ 在元素上设置 Opacity - 需要创建临时表面 -->
<Border Opacity="0.5"><Rectangle Fill="Blue" /></Border>
<!-- ✅ 在 Brush 上设置 Alpha -->
<Border><Rectangle Fill="#80000000" /></Border>

<!-- ❌ 简单文本使用 FlowDocument -->
<FlowDocumentScrollViewer><FlowDocument><Paragraph><Run Text="Hello" /></Paragraph></FlowDocument></FlowDocumentScrollViewer>
<!-- ✅ 简单文本用 TextBlock -->
<TextBlock Text="Hello" />
```

#### 检查点 9：事件处理器内存泄漏（高优先级）

**为什么重要：** 订阅事件会建立从发布者到订阅者的强引用。若控件卸载后未取消订阅，发布者（尤其是静态对象）会阻止 GC 回收订阅者，造成内存泄漏。

**扫描模式：**
```bash
Grep "+= " --type cs -C 2
Grep "Application\.Current\.\|CommandManager\.\|SystemEvents\." --type cs
```

**在 Unloaded 中取消订阅：**
```csharp
// ❌ 只订阅不取消 — Application.Current 等静态对象永远不会被 GC，整个订阅者对象图泄漏
public MyControl() { someService.DataChanged += OnDataChanged; Application.Current.Activated += OnAppActivated; }

// ✅ 在 Unloaded 中取消订阅
public MyControl()
{
    someService.DataChanged += OnDataChanged;
    Application.Current.Activated += OnAppActivated;
    this.Unloaded += (s, e) => { someService.DataChanged -= OnDataChanged; Application.Current.Activated -= OnAppActivated; };
}
```

**WeakEventManager（推荐替代方案）：**
```csharp
// ✅ 弱引用，订阅者可被 GC 正常回收，无需手动取消订阅
WeakEventManager<SomeService, EventArgs>.AddHandler(someService, nameof(someService.DataChanged), OnDataChanged);
WeakEventManager<Application, EventArgs>.AddHandler(Application.Current, nameof(Application.Activated), OnAppActivated);
```

**IDisposable 模式（ViewModel/Service 场景）：**
```csharp
public class MyViewModel : IDisposable
{
    public MyViewModel() => _service.DataChanged += OnDataChanged;
    public void Dispose() => _service.DataChanged -= OnDataChanged;
}
// View 的 Unloaded 调用 (DataContext as IDisposable)?.Dispose()
```

#### 检查点 10：UI 线程阻塞与 Dispatcher 优化（高优先级）

**为什么重要：** 在 UI 线程（事件处理器、按钮点击）中执行耗时操作会冻结整个界面。同步 `Dispatcher.Invoke` 可能在某些场景导致死锁。

**扫描模式：**
```bash
Grep "private void.*_Click\|private void.*Handler" --type cs -A 15
Grep "Dispatcher\.Invoke(" --type cs
```

**async/await + Task.Run（UI 线程解放）：**
```csharp
// ❌ 同步阻塞 UI，界面冻结
private void LoadData_Click(object sender, RoutedEventArgs e) { DataGrid.ItemsSource = _repository.GetAllData(); }

// ✅ async void 在事件处理器中是唯一合法用法
private async void LoadData_Click(object sender, RoutedEventArgs e)
{
    LoadButton.IsEnabled = false;
    DataGrid.ItemsSource = await Task.Run(() => _repository.GetAllData());
    LoadButton.IsEnabled = true;
}
```

**Dispatcher.InvokeAsync 替代同步 Invoke：**
```csharp
// ❌ 同步 Invoke — 可能在某些场景死锁（UI 线程等待自身）
Application.Current.Dispatcher.Invoke(() => UpdateUI(result));

// ✅ InvokeAsync — 非阻塞，避免潜在死锁
await Application.Current.Dispatcher.InvokeAsync(() => UpdateUI(result));
```

**IProgress<T> 报告后台进度 + CancellationToken：**
```csharp
// ✅ IProgress<T> 自动在 UI 线程回调；CancellationToken 支持取消
private async void Process_Click(object sender, RoutedEventArgs e)
{
    var progress = new Progress<int>(pct => ProgressBar.Value = pct);
    var cts = new CancellationTokenSource();
    CancelButton.Click += (_, _) => cts.Cancel();
    try { await Task.Run(() => DoLongWork(progress, cts.Token), cts.Token); }
    catch (OperationCanceledException) { StatusText.Text = "已取消"; }
}
private void DoLongWork(IProgress<int> progress, CancellationToken ct)
{
    for (int i = 0; i < 100; i++)
    { ct.ThrowIfCancellationRequested(); Thread.Sleep(50); progress.Report(i + 1); }
}
```

### 3. 边界场景处理

扫描过程中遇到以下场景时，按对应分支处理，不要静默跳过或凭空判断：

| 场景 | 触发条件 | 处理方式 |
|------|---------|---------|
| 未发现任何问题 | 10 个检查点全部扫描完毕，代码已正确使用 ObservableCollection、虚拟化、冻结 Brush 等最佳实践 | **如实报告"未发现重大性能问题"**，可指出 1-2 个低优先级的可选权衡项（并标注"可选优化"而非"问题"），禁止为凑数硬扣分或编造问题 |
| 找不到目标文件 | `Glob "**/*.xaml"` 或用户指定路径无匹配结果 | 明确告知用户未找到 XAML 文件，询问具体文件路径或代码片段，不要臆测代码内容 |
| 代码片段信息不全 | 用户只提供 XAML 或只提供 C#，缺少绑定源（ViewModel）无法确认属性类型/绑定模式是否合理 | 基于现有片段指出可见的问题（如虚拟化、Shape 用量），同时说明"绑定源类型未知，以下判断基于假设"，列出需要确认的假设 |
| 反模式疑似有业务权衡 | 识别到的写法（如 TwoWay、频繁刷新）可能是刻意的业务需求而非疏忽 | 先说明"通常应为 X，但如果业务需要 Y（如可编辑控件、频繁变化数据），当前写法合理"，不要武断判定为错误 |

### 4. 生成性能报告

扫描完成后输出报告，包含：
- 扫描文件数量、问题汇总（高危/中危/低危）
- 每个问题：**位置**（文件:行号）、**影响**（具体指标）、**修复前后代码**、**预期提升**

🔴 **CHECKPOINT · 应用修复前的确认**：默认只在报告中给出修复前后代码供用户参考，不直接编辑文件。若用户要求直接修改代码：
- **局部修改**（单个方法/单个类内部即可完成，不涉及新增类型、不影响多文件协调、不改变现有行为契约）→ 可直接应用，无需额外确认。包括但不限于：补 `Freeze()`、改 `Binding Mode`、加 `VirtualizationMode`、调整 `x:Key`、构造函数同步初始化迁移到 `Loaded` 异步初始化（检查点5）、手动订阅+`Unloaded` 取消订阅改造为 `WeakEventManager`（检查点9）、事件处理器同步改 `async`/`await` + `Task.Run`（检查点10）
- **架构级改动**（Shape 迁移到 DrawingVisual/DrawingGroup、重写虚拟化容器、拆分 ViewModel 职责等涉及多文件或改变现有行为契约（如命中测试、可视化树结构）的重构）→ 先在报告中列出改动范围和风险，**🛑 STOP 等用户明确确认后再应用**，不要在报告之外直接静默重写

性能指标参考：

| 优化项 | 提升幅度 |
|--------|---------|
| List → ObservableCollection | ~80x |
| 启用虚拟化 + Recycling | ~70x |
| Shape → DrawingVisual/DrawingGroup | ~50-100x |
| 冻结 Brush + 循环外共享 | ~4-5x |
| 自上而下构建树 | ~30x |
| SplashScreen + 延迟初始化 | ~90% 启动时间 |

## 输出原则

1. **审查现有代码**：生成详细分析报告，按优先级排序问题
2. **编写新代码**：提供最佳实践指导，预防性能问题
3. **平衡权衡**：不是所有优化都适用所有场景，需说明适用条件
4. **可测量**：提供具体的性能指标和改善预期
5. **可操作**：给出可直接使用的优化代码

## ⛔ 不要做什么

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|---|---|---|
| 1 | 无脑把所有绑定都加 `Mode=OneTime` | 若该属性其实会通过事件（如 `XxxChanged`）驱动更新，`OneTime` 会导致 UI 静默不刷新——这是功能性 bug，不是性能优化 | 先确认属性是否有对应的变更通知路径（`INotifyPropertyChanged` 实现、订阅的 `Changed` 事件），只对确认不变的属性建议 `OneTime` |
| 2 | 未确认数据总量是否超出可视区域，就纠结"有没有开虚拟化" | 虚拟化的收益只在"数据总量远超一屏可见范围"时才体现；数据量本身很小、全部在一屏内时，是否开启虚拟化不影响实际渲染的元素数量，讨论这个是伪命题 | 先确认真实数据规模（当前量级 + 可能增长到的量级），只对确实会超出可视区域的列表建议虚拟化 |
| 3 | 未经实测，直接把文档里的 `~80x`/`~70x`/`~50-100x` 等参考倍数当作本次修复的确定收益汇报给用户 | 这些倍数来自 Microsoft 官方基准测试的特定场景，不代表用户当前代码库的真实提升幅度；把参考值包装成确定承诺是过度承诺 | 明确标注"官方基准测试参考值，实际提升取决于数据规模和场景，建议修复后用 Profiler 实测" |
| 4 | 对可能动态变化的 `Freezable` 对象（如颜色随主题切换的 Brush）调用 `.Freeze()` | 冻结后的对象只读，之后任何修改尝试都会抛 `InvalidOperationException`；只有确认对象生命周期内不再变化才能冻结 | 先确认该 Brush/Pen 之后是否需要修改（如主题切换、状态变色），仅对确认不变的对象建议冻结 |
| 5 | 只给出片段级代码就断言"已修复"，不提示该修复依赖的外部前提 | 例如 `IDisposable.Dispose()` 写得再对，若调用方从未在 `Unloaded` 中触发它，泄漏依然存在；口径上宣称"已解决"会误导用户 | 明确指出修复生效所依赖的调用方/宿主代码是否已确认存在，不确认时列为「需要确认的假设」而非既成事实 |

## 工具推荐

- **WPF Performance Suite**：渲染性能分析
- **Visual Studio Profiler**：CPU/内存分析
- **Snoop**：可视化树实时检查

## 参考资源

- [优化 WPF 应用程序性能 - Microsoft Learn](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/advanced/optimizing-wpf-application-performance)
- [数据绑定优化](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/advanced/optimizing-performance-data-binding)
