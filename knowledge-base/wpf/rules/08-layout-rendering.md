# 08 · 布局与渲染

> 更新历史：2026-08-21 创建。2026-08-22 引用 skill 改名（`wpf-xaml-performance` → `wpf-code-review`）。性能相关约束与 `wpf-code-review` skill 的性能专项诊断速查互为印证。

布局决定元素位置与尺寸，渲染决定显示质量与性能。本篇约束面板选型、布局系统理解、DPI 感知与绘制方式。

## 1. 布局系统认知（Measure / Arrange）

- **必须**：理解两遍布局（`Measure` 定期望尺寸 → `Arrange` 定最终位置），避免在自定义控件中误用
- **必须**：自定义控件布局重写 `MeasureOverride` / `ArrangeOverride` 时遵循契约（`MeasureOverride` 返回期望尺寸，`ArrangeOverride` 返回实际尺寸）
- **禁止**：在 `MeasureOverride` / `ArrangeOverride` 中做耗时计算或 IO（每次布局触发，联动 `10` 章）
- **应该**：布局变更用属性回调声明（`FrameworkPropertyMetadataOptions.AffectsMeasure` / `AffectsArrange` / `AffectsRender`）精准触发，避免整棵布局树重排

## 2. 面板选型矩阵

| 面板 | 特征 | 适用 |
|---|---|---|
| `Grid` | 行列网格，最灵活 | 复杂表单、布局骨架 |
| `StackPanel` | 单一方向堆叠 | 简单垂直/水平排列、ItemTemplate |
| `DockPanel` | 停靠布局 | 窗口骨架（顶/底/左/右/填充） |
| `WrapPanel` | 自动换行 | 标签云、图标流 |
| `Canvas` | 绝对定位 | 绘图、坐标精确场景 |
| `UniformGrid` | 等分网格 | 键盘/等宽网格 |

- **必须**：默认用 `Grid` 构建布局骨架，简单方向排列用 `StackPanel`，**禁止**全用 `Canvas` 绝对定位（不可自适应）
- **必须**：列表项 ItemTemplate 内优先 `StackPanel`（轻量，配合虚拟化，联动 `10` 章）
- **禁止**：`Grid` 嵌套过深（>8 层）——布局计算指数级增长，用相对布局 / 合并行减层
- **应该**：布局性能优先级 `Canvas > StackPanel > DockPanel > Grid`，简单场景用更轻面板（联动 `wpf-code-review` 性能专项诊断速查之布局性能）

## 3. 可视化树 vs 逻辑树

- **必须**：区分可视化树（`Visual` 层次，影响渲染 / 命中测试）与逻辑树（`Logical` 层次，影响数据上下文继承）
- **必须**：`DataContext` 沿逻辑树继承，自定义控件数据上下文处理要留意逻辑树连接（`AddLogicalChild`）
- **禁止**：在可视化树遍历中做高频操作（命中测试、`VisualTreeHelper` 遍历开销大）
- **应该**：高频命中测试 / 区域查询用 `HitTestResult` 优化，避免逐元素 `VisualTreeHelper` 遍历

## 4. RenderTransform vs LayoutTransform

| 变换 | 阶段 | 是否影响布局 |
|---|---|---|
| `RenderTransform` | 渲染时应用 | 不影响布局（元素占位不变） |
| `LayoutTransform` | 布局时应用 | 影响布局（周围元素重排） |

- **必须**：动画 / 平移 / 缩放优先 `RenderTransform`（不触发重排，性能好）
- **必须**：需元素尺寸变化带动周围重排（旋转后文字换行）时才用 `LayoutTransform`
- **禁止**：动画场景用 `LayoutTransform`（每次布局重排，卡顿）
- **应该**：`RenderTransformOrigin` 明确旋转 / 缩放中心

```xml
<!-- ❌ 动画用 LayoutTransform：每帧触发布局重排，周围元素跟着抖动，卡顿 -->
<Button>
  <Button.LayoutTransform>
    <ScaleTransform ScaleX="1.2" ScaleY="1.2" />
  </Button.LayoutTransform>
</Button>

<!-- ✅ 动画用 RenderTransform：只在渲染层变换，不影响布局，周围元素不动 -->
<Button>
  <Button.RenderTransform>
    <ScaleTransform ScaleX="1.2" ScaleY="1.2" />
  </Button.RenderTransform>
  <Button.RenderTransformOrigin>0.5, 0.5</Button.RenderTransformOrigin>
</Button>
```

```xml
<!-- ✅ 唯一适合 LayoutTransform 的场景：旋转后文字换行，需要布局真实重算 -->
<TextBlock>
  <TextBlock.LayoutTransform>
    <RotateTransform Angle="90" />
  </TextBlock.LayoutTransform>
</TextBlock>
```

## 5. DPI 感知

- **必须**：WPF 应用声明 `PerMonitorV2` DPI 感知（`app.manifest` 的 `dpiAwareness`），避免跨显示器缩放模糊
- **必须**：布局用相对单位（`*` 比例、`Auto`、控件系统度量），**禁止**硬编码像素尺寸做自适应
- **必须**：图形坐标随 DPI 缩放——`DeviceDpi` 变化时重算布局，避免文字/图形模糊
- **禁止**：用 DIP（设备无关像素）硬编码窗口最小尺寸而不考虑高 DPI 缩放（字体可读性问题，联动 `14` 章）
- **应该**：多显示器高 DPI 场景用系统 DPI 感知 API 监听 `WM_DPICHANGED` 或 WPF `DpiChanged` 事件刷新

## 6. 文本渲染

- **必须**：文本用 `TextBlock`（轻量），**禁止**简单文本用 `FlowDocumentScrollViewer`（重，联动 `10` 章）
- **必须**：文本重排频繁场景用 `TextBlock` + `TextWrapping` 合理配置，**禁止**每帧重建 `FormattedText`（后台高开销）
- **应该**：文字清晰度受 `TextOptions.TextFormattingMode`（`Ideal` / `Display`）与 `TextRenderingMode` 影响，按清晰度与性能取舍
- **禁止**：`TextBox` 大量纯展示文本（编辑控件开销大，展示用 `TextBlock`）

## 7. Shape 与 Drawing

- **必须**：静态图形用 `Path` + `StreamGeometry`（只读快），**禁止**大量 `Ellipse` / `Rectangle` 堆叠（每个都是 UI 元素，联动 `wpf-code-review` 性能专项诊断速查之图形渲染）
- **必须**：动态高频图形（图表、动画数据）用 `DrawingVisual` + `VisualCollection` 或 `DrawingGroup`（非 UI 元素，批量绘制）
- **必须**：`Brush` / `Pen` 在循环外创建并 `Freeze()` 后共享（联动 `07` 章第 5 节）
- **禁止**：循环中 `new SolidColorBrush` / `new Pen`（每个实例都有事件监听，性能差）
- **应该**：图标 Path 数据资源化（联动 `07` 章第 7 节），支持主题换色

## 8. 渲染性能（联动 `10` 章）

- **必须**：图层合成用 `Opacity` / 平移 / 缩放等 GPU 友好属性，**禁止**逐帧改布局（`LayoutTransform` / 重排）
- **必须**：元素 `Opacity` 替代透明画刷的场景正确选择（元素级透明度需临时表面，`Brush` 的 Alpha 更高效，联动 `wpf-code-review` 性能专项诊断速查之资源）
- **禁止**：`BitmapEffect`（已过时，性能差），用 `Effect`（`DropShadowEffect` 等）

```xml
<!-- ❌ 元素级 Opacity：为半透明临时渲染到离屏表面，开销大 -->
<Border Opacity="0.5">
  <Rectangle Fill="Blue" />
</Border>

<!-- ✅ 画刷 Alpha：直接在画刷上控制透明度，无需临时表面 -->
<Border>
  <Rectangle Fill="#80000000" />   <!-- Alpha=0x80，约 50% 透明 -->
</Border>
```

```xml
<!-- ❌ BitmapEffect：已过时，CPU 软件渲染，性能极差 -->
<Button>
  <Button.BitmapEffect><DropShadowBitmapEffect /></Button.BitmapEffect>
</Button>

<!-- ✅ Effect：硬件加速，效果丰富 -->
<Button>
  <Button.Effect><DropShadowEffect BlurRadius="8" /></Button.Effect>
</Button>
```
- **应该**：重绘频繁的区域启用 `CacheMode`（`BitmapCache`）减少重绘，但注意缓存命中率权衡
- **禁止**：不经测量断言渲染问题（先 Profiler 定位再优化，联动 `10` 章第 1 节）
