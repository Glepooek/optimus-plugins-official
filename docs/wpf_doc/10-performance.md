# 10 · 性能优化

> 更新历史：2026-08-21 创建。本篇是性能**原则**层；诊断与修复操作以 `wpf-xaml-performance` skill 为准（检查点 1-10 对应本条款）。

性能优化分原则与操作两层：本篇约束"何时优化、优化的优先级、达标线"；具体扫描模式与修复代码见 `wpf-xaml-performance` skill。

## 1. 先测量再优化

- **必须**：先定位瓶颈再优化——用 Profiler（Visual Studio Profiler、WPF Performance Suite、Snoop）确认问题点，**禁止**凭猜测大改代码
- **必须**：优化有可测量目标（响应时间、内存、帧率），优化前后对比数据
- **禁止**：对非热点路径做微观优化（无谓复杂度）；先修热点
- **应该**：性能回归纳入 CI 或定期巡检（启动时间、长列表滚动、内存峰值）

## 2. 性能优先级排序

性能优化按影响面排序，从高到低：

1. **数据绑定**（最影响交互）——`List` → `ObservableCollection` 提升可达 ~80x
2. **虚拟化**——长列表未虚拟化提升可达 ~70x
3. **图形渲染**——`Shape` 堆叠 → `DrawingVisual`/`DrawingGroup` 提升可达 ~50-100x
4. **启动时间**——`SplashScreen` + 延迟初始化可改善 ~90% 启动时间
5. **布局 / 资源 / 事件泄漏**等次级项

- **必须**：按上述优先级扫描（联动 `wpf-xaml-performance` 检查点顺序），**禁止**跳过前三级直接优化低级项
- **应该**：优化按"先修影响面大的、后修小的"推进，报告注明预期收益与实测差异

## 3. 数据绑定性能

- **必须**：集合绑定用 `ObservableCollection<T>`（自动通知），**禁止** `List<T>` 绑定后手动 `Refresh()`
- **必须**：常量 / 只读属性用 `OneTime` 绑定，**禁止**为不变值订阅 `PropertyChanged`（联动 `05` 章第 1 节）
- **必须**：绑定路径 ≤3 层，深层路径在 ViewModel 扁平化（联动 `05` 章第 3 节）
- **必须**：计算密集型 `IValueConverter` 缓存结果（联动 `05` 章第 4 节）
- **禁止**：ItemTemplate 内每项执行昂贵 Converter / 多级绑定路径

```csharp
// ❌ 昂贵 Converter 每次刷新重算：长列表每项每个刷新周期都重算，UI 卡顿
public object Convert(object value, Type t, object p, CultureInfo c)
    => ExpensiveComputation(value);      // 无缓存

// ✅ 字典缓存结果：同一输入只算一次
private readonly Dictionary<object, object> _cache = new();
public object Convert(object value, Type t, object p, CultureInfo c)
{
    if (_cache.TryGetValue(value, out var cached)) return cached;
    return _cache[value] = ExpensiveComputation(value);
}
```

## 4. 虚拟化

- **必须**：长列表（`ListBox` / `ListView` / `DataGrid` / `TreeView`）开启虚拟化，并设 `VirtualizationMode="Recycling"`
- **必须**：确认列表数据量确实超出可视区域再讨论虚拟化（数据都在一屏内时虚拟化无收益，联动 `wpf-xaml-performance` 边界场景第 2 条）
- **必须**：虚拟化容器内 ItemTemplate 用轻量布局（`StackPanel`），**禁止** `ScrollViewer.CanContentScroll="False"` 禁用虚拟化
- **应该**：`TreeView` 显式开启虚拟化（`VirtualizingPanel.IsVirtualizing="True"`）
- **禁止**：列表项模板内嵌 `ItemsControl`（嵌套集合破坏虚拟化）

```xml
<!-- ❌ 禁用虚拟化：10 万项全部创建 UI 容器，内存暴涨、滚动卡死 -->
<ListBox ScrollViewer.CanContentScroll="False" ItemsSource="{Binding Items}" />

<!-- ✅ 启用虚拟化 + 容器回收：只渲染可见项，滚动复用容器 -->
<ListBox VirtualizingPanel.VirtualizationMode="Recycling"
         ItemsSource="{Binding Items}">
  <ListBox.ItemTemplate>
    <DataTemplate>
      <StackPanel Orientation="Horizontal">   <!-- 轻量布局 -->
        <TextBlock Text="{Binding Name}" />
      </StackPanel>
    </DataTemplate>
  </ListBox.ItemTemplate>
</ListBox>
```

```xml
<!-- ❌ 嵌套 ItemsControl 破坏虚拟化：每项又渲染一整套列表，虚拟化失效 -->
<DataTemplate>
  <StackPanel>
    <ItemsControl ItemsSource="{Binding Children}" />   <!-- 内嵌列表 -->
  </StackPanel>
</DataTemplate>
```

## 5. 图形与渲染

- **必须**：静态图形用 `Path` + `StreamGeometry`（只读快，联动 `08` 章第 7 节）
- **必须**：动态高频图形用 `DrawingVisual` / `DrawingGroup`（批量绘制、非 UI 元素）
- **必须**：`Brush` / `Pen` 循环外创建并 `Freeze()` 共享（联动 `07` 章第 5 节）
- **禁止**：`BitmapEffect`（过时）；`Opacity` 优先于透明画刷场景用 Brush Alpha（联动 `08` 章第 8 节）
- **应该**：重绘频繁区域用 `CacheMode="BitmapCache"`，注意缓存命中权衡

## 6. 启动时间

- **必须**：应用启动避免同步加载全部资源 / 初始化全部模块（联动 `02` 章 App.xaml 职责）
- **必须**：关键路径用 `SplashScreen` 与延迟初始化（`Loaded` 异步加载、按需加载资源字典）
- **禁止**：构造函数中同步 `InitializeComponent` + 全部初始化（阻塞 UI）
- **应该**：冷启动发布启用 `ReadyToRun`（`<PublishReadyToRun>true</PublishReadyToRun>`，联动 `15` 章）
- **禁止**：`App.xaml` 一次性合并数十个资源字典（按需动态加载，联动 `07` 章）

## 7. 内存与泄漏（联动 `12` 章）

- **必须**：事件订阅配对取消（`Unloaded` 取消订阅 / `WeakEventManager` / `IDisposable`），**禁止**静态对象长期持有订阅者
- **必须**：`Freezable` 资源共享并冻结，**禁止**循环内 `new Brush` / 新图形对象
- **必须**：动态加载的字典 / 控件移除后释放引用（主题切换、窗口关闭）
- **禁止**：静态字段持有 `Window` / `UserControl` 引用（永不回收）
- **应该**：大内存场景（图片、大集合）用 `WeakReference` / 池化（`ArrayPool`）管理，警惕 LOH 碎片

## 8. 布局性能

- **必须**：`Grid` 嵌套控制（≤8 层），简单排列用 `StackPanel` / `Canvas`
- **必须**：动画用 `RenderTransform`，**禁止**动画 `LayoutTransform`（每次重排，联动 `08` 章第 4 节）
- **应该**：自定义控件布局回调用 `AffectsMeasure` / `AffectsArrange` / `AffectsRender` 精准声明（联动 `08` 章第 1 节）
- **禁止**：`MeasureOverride` / `ArrangeOverride` 内做耗时计算

## 9. 静态资源与 DynamicResource 权衡

- **必须**：默认 `StaticResource`（构建期解析、快），**禁止**无理由 `DynamicResource`（运行期查找，联动 `04` 章第 2 节）
- **必须**：主题敏感资源才用 `DynamicResource`（联动 `07` 章第 4 节）
- **应该**：页面加载时的资源查找路径短（就近定义），避免长链查找

## 10. 工具推荐（联动 `wpf-xaml-performance`）

- **WPF Performance Suite**：渲染性能分析
- **Visual Studio Profiler**：CPU / 内存分析
- **Snoop**：可视化树实时检查、绑定诊断
- **PerfView**：深层次诊断（GC、线程）
- **dotnet-counters / dotnet-dump**：运行时指标与内存转储

## 11. 达标线

- **必须**：启动时间、滚动流畅度、内存占用有团队验收线（如：冷启动 ≤ 3s、长列表滚动不丢帧、无持续内存增长）
- **应该**：性能门禁随 CI 采集（启动、内存快照），回归自动告警
- **禁止**：性能问题以"用户没抱怨"为由搁置——纳入巡检与门禁
