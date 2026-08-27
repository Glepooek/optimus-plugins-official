# 05 · 数据绑定

> 更新历史：2026-08-21 创建。

绑定是 WPF 的核心机制，也是静默失败的重灾区。本篇约束绑定模式、变更通知、转换器与失败排查。

## 1. Binding 模式选择

| 模式 | 时机 | 注意 |
|---|---|---|
| `OneWay`（默认） | 源 → 目标，只读展示 | 目标不可编辑，节省资源 |
| `TwoWay` | 用户输入 → 源（表单、编辑框） | 仅在需要回写时用 |
| `OneTime` | 值初始化后不再变 | 不订阅变更通知，性能最好（常量、静态元数据） |
| `OneWayToSource` | 目标 → 源 | 少用 |

- **必须**：只读展示用 `OneWay`（默认），**禁止**无谓 `TwoWay`（如 `TextBlock` 上写 `TwoWay` 是反模式）
- **必须**：明确不变的值用 `OneTime`（版本号、只读元数据），**禁止**为不变化的常量订阅 `PropertyChanged`
- **必须**：输入控件（`TextBox`、`ComboBox` 等）需要回写源时才用 `TwoWay`
- **禁止**：把不必要变更的属性设计成 `TwoWay` 并在无变更时也触发通知（性能噪音）

```xml
<!-- ❌ 只读展示却用 TwoWay：TextBlock 不可编辑，TwoWay 纯浪费，还订阅了写入路径 -->
<TextBlock Text="{Binding AppVersion, Mode=TwoWay}" />

<!-- ✅ 只读展示用默认 OneWay（省略 Mode） -->
<TextBlock Text="{Binding AppVersion}" />
```

```xml
<!-- ❌ 常量却用 OneWay/TwoWay：版本号不变，却每次初始化都订阅 PropertyChanged -->
<TextBlock Text="{Binding AppVersion}" />

<!-- ✅ 明确不变的值用 OneTime：只读一次，不订阅任何变更通知 -->
<TextBlock Text="{Binding AppVersion, Mode=OneTime}" />
```

## 2. 变更通知：INotifyPropertyChanged / ObservableCollection

- **必须**：可绑定集合用 `ObservableCollection<T>`（自动通知增删），**禁止** `List<T>` 直接绑定后手动强制刷新
- **必须**：`INotifyPropertyChanged` 属性用 `SetProperty` 模板集中实现（联动 `03` 章第 2 节）
- **必须**：集合元素内部属性变化时，集合本身要感知——元素实现 `INotifyPropertyChanged` 且通过属性访问
- **禁止**：用 `ListView.Items.Refresh()` 这类强制刷新掩盖集合设计问题（联动 `10` 章性能）

```csharp
// ❌ List<T> 绑定 + 手动强制刷新：List 不通知 UI，增删后 UI 不更新，只能靠 Refresh 硬刷
public List<Employee> Employees { get; set; }
// 新增后：
_employees.Add(new Employee(...));
EmployeesListView.Items.Refresh();   // 手动强刷，掩盖了集合设计错误

// ✅ ObservableCollection：增删自动通知，UI 实时更新，无需手动刷新
public ObservableCollection<Employee> Employees { get; set; }
Employees.Add(new Employee(...));    // UI 自动反映
```
- **应该**：大批量数据用 `ObservableCollection` 时注意每项通知的 UI 开销，批量变更用批量添加 / `SuppressNotification`

## 3. 绑定路径

- **必须**：绑定路径控制在合理深度（≤3 层，`User.Department.Manager.Name` 是反模式，联动 `10` 章）
- **必须**：深层路径在 ViewModel 暴露扁平属性（`ManagerName => User?.Department?.Manager?.Name ?? string.Empty`）
- **禁止**：绑定路径中混入可空链导致静默失败（中间对象为 `null` 时绑定静默不报错）
- **应该**：路径引用 ViewModel 公开属性，不访问私有 / 内部字段

```xml
<!-- ❌ 深层路径：每层都要建监听，中间对象为 null 时静默失败，UI 无值且无报错 -->
<TextBlock Text="{Binding User.Department.Manager.Name}" />

<!-- ✅ 扁平属性：ViewModel 暴露计算属性，绑定一层，null 安全 -->
<TextBlock Text="{Binding ManagerName}" />
```

```csharp
// ViewModel 中：
public string ManagerName => User?.Department?.Manager?.Name ?? string.Empty;
```

## 4. 数据转换器（IValueConverter / IMultiValueConverter）

- **必须**：显示格式与 UI 状态转换用 Converter（`bool → Visibility`、`enum → 文案`、`数值 → 格式化字符串`），**禁止**在 ViewModel 放 UI 类型（联动 `03` 章第 2 节）
- **必须**：Converter 无状态（不持有跨调用可变状态），同一实例可被多元素复用
- **必须**：Converter 处理 `null` 与异常输入（返回 `DependencyProperty.UnsetValue` 或安全默认值），**禁止**抛异常
- **应该**：Converter 集中在 `Themes/Converters.xaml` 注册（联动 `02` 章），单一职责一个 Converter 一类转换
- **禁止**：一个 Converter 内部做多类格式转换（`object` → 各种分支），拆分为独立 Converter
- **禁止**：计算密集型 Converter 每次刷新重算（缓存结果，联动 `10` 章）

## 5. 绑定静默失败排查

WPF 绑定失败**默认静默**（输出窗口有 `BindingExpression` 错误但 UI 不报错），必须主动防御：

- **必须**：开发期用 `PresentationTraceSources.TraceLevel="High"` 跟踪可疑绑定
- **必须**：`{Binding Path, FallbackValue=...}` 与 `{Binding Path, TargetNullValue=...}` 提供降级显示，**禁止**裸绑定可能为 null 的属性不做兜底

```xml
<!-- ❌ 裸绑定：Path 不存在或源为 null 时 UI 空白，且无任何提示 -->
<TextBlock Text="{Binding CreatedBy}" />

<!-- ✅ FallbackValue：源属性不存在 / 类型不匹配时显示降级文案 -->
<TextBlock Text="{Binding CreatedBy, FallbackValue='未知用户'}" />

<!-- ✅ TargetNullValue：源存在但值为 null 时显示占位 -->
<TextBlock Text="{Binding CreatedBy, TargetNullValue='（未署名）'}" />
```
- **应该**：启用 XAML 设计期绑定诊断（`d:DataContext` + 设计期数据），把绑定错误前移到设计器
- **必须**：绑定目标属性类型与源属性类型匹配（不匹配时静默失败），Converter 缺失时用 `StringFormat` 兜底格式
- **禁止**：依赖输出窗口里的 `BindingError` 事后排查而不做设计期防护

## 6. 绑定性能（联动 `10` 章）

- **必须**：静态/常量值用 `OneTime`，不订阅不必要的变更通知
- **必须**：长列表 ItemTemplate 内绑定保持轻量（简单属性 + 轻量 Converter），**禁止**复杂 Converter 每项重复计算
- **应该**：集合虚拟化开启（`VirtualizingPanel.IsVirtualizing` + `VirtualizationMode="Recycling"`），绑定项多时容器复用
- **禁止**：在 `Binding` 内做 `StringFormat` 的昂贵格式化或用多级路径绕弯

## 7. 绑定与线程

- **必须**：绑定源属性变更发生在 UI 线程（WPF 绑定默认调度到 UI 线程，但数据源跨线程变更需 `Dispatcher` 编组，联动 `09` 章）
- **必须**：后台线程更新集合时通过 UI 线程调度（`Dispatcher.InvokeAsync` / `BindingOperations.EnableCollectionSynchronization`），**禁止**跨线程直接改 `ObservableCollection`
- **禁止**：`INotifyPropertyChanged` 触发后在同一后台线程继续写目标控件（线程亲和性）

## 8. 绑定调试技巧

- **应该**：可疑绑定临时加 `PresentationTraceSources.TraceLevel="High"` 定位后移除，**禁止**遗留调试痕迹
- **应该**：绑定树用 Snoop 等工具检查（`DataContext` 链、绑定值），联动 `10` 章工具推荐
