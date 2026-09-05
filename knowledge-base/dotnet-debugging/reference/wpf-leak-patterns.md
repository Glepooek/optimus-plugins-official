# WPF 泄漏形态图鉴

> **适用范围**：WPF 桌面应用，**仅 Windows**。覆盖 .NET Framework 4.x 与 .NET 6+ 两条 WPF 技术栈。非 WPF 应用的内存增长排查见 `reference/debugging-decision-tree.md § 2. 内存持续增长`。

本篇不引入新命令，全部复用一期已交付的 SOS 命令，增量是「同一条 !gcroot 输出在 WPF 场景下意味着什么」。预防性的编码规范属另一领域，见 `knowledge-base/wpf/rules/10-performance.md § 7. 内存与泄漏（联动 12 章）`。那里讲怎么不写出泄漏，本篇讲已经泄漏了怎么认出是哪一类。

§ 2–5 四节结构固定为：`### 堆上的可见特征` / `### 根链形态` / `### 判据与下一步`。已知泄漏类型时读对应节；只拿到一条 `!gcroot` 输出、不知属于哪类时，按 `§ 6. 根链形态图鉴速查表` 的内部类型名反查。

## 1. WPF 泄漏的共同取证起点

### 该盯哪些类型

用 `reference/sos-heap-and-objects.md § 1. !dumpheap` 的 `-stat -type <名>` 逐个筛查以下类型，四类泄漏形态的第一现场都反映在这几个类型的实例数上：

| 类型名 | 预期活动实例数的判断依据 |
|---|---|
| `System.Windows.Window` 及其派生 | 应用当前打开的窗口数；已关闭的窗口应为 0 |
| `System.Windows.Controls.UserControl` 派生 | 当前显示的控件实例数 |
| `System.Windows.Data.BindingExpression` | 无固定预期值，看是否与已销毁的界面数量同比增长 |
| `System.Windows.Threading.DispatcherTimer` | 应用当前活动定时器数 |
| 应用自身的 ViewModel 类型 | 按导航层级推算 |

### 预期实例数这个前提

这是 WPF 泄漏排查与通用泄漏排查最大的差异。通用做法（`reference/debugging-decision-tree.md § 2. 内存持续增长`）是间隔采样两次 dump，看 `!dumpheap -stat` 的 Count 列是否持续上涨——单份 dump 无法区分「实例数高但稳定」与「实例数持续增长」。

WPF 场景下，单份 dump 也能判定，因为存在先验知识：「已关闭的 `Window` 实例数应为 0」「当前显示的 `UserControl` 实例数等于界面上可见的控件数」这类预期值不依赖第二次采样就能确定。

**该前提不成立时——即分析者并不清楚这个应用预期应有多少活动实例——整条推理链失效**，不能把「数量看起来有点多」当作泄漏证据，须退回一期的间隔采样做法逐一确认。

### 判据与下一步

- **证实**：某 WPF 类型的实例数超出该应用预期的活动实例数 → 用 `§ 1. !dumpheap` 定位到具体实例，转 `reference/sos-heap-and-objects.md § 4. !gcroot` 追踪持有链，按本篇 § 2–5 对号入座分类；
- **排除**：全部 WPF 类型实例数均在预期范围内 → 排除本篇覆盖的四类泄漏，转 `reference/debugging-decision-tree.md § 2. 内存持续增长` 排查非托管泄漏、LOH 碎片等通用成因。

## 2. Binding 泄漏

### 堆上的可见特征

`System.Windows.Data.BindingExpression` 实例数随已销毁界面的数量同比增长，且对应的绑定源对象（通常是 ViewModel 或数据实体）实例数不回落——界面关了，绑定表达式和它绑定的源都还活着。

### 根链形态

WPF 处理绑定源变更通知的方式取决于源类型是否实现 `INotifyPropertyChanged`：

- 绑定源实现了 `INotifyPropertyChanged` 时，WPF 通过弱引用订阅其 `PropertyChanged` 事件，源对象与订阅者之间不构成强引用，源对象可正常回收；
- 未实现时，WPF 退化为基于 `PropertyDescriptor` 的订阅路径：源对象的 `PropertyDescriptor.AddValueChanged` 被调用后，管理该订阅的内部对象会记录一条持有源对象**强引用**的登记项，这条登记项的生命周期设计为与 `AddValueChanged`/`RemoveValueChanged` 这对调用的作用域一致——也就是说，只有显式调用配对的 `RemoveValueChanged`（或等效的解绑操作），这条强引用才会被清空；
- 后果：如果绑定目标（界面元素）被丢弃时没有人显式触发这次解绑，登记项会一直持有源对象，即便绑定目标本身已经从可视化树移除、甚至已被回收，源对象依然存活；若源对象反过来又持有界面元素（例如 ViewModel 持有 View 的引用），整条链会一起留在堆上。

登记项挂在哪个对象上、根链末端具体呈现什么形态，见下方「判据与下一步」。

### 判据与下一步

- **证实**：`reference/sos-heap-and-objects.md § 4. !gcroot` 显示该绑定源对象的根链末端落在 WPF 内部命名空间 `MS.Internal.Data` 下的一个事件管理器类型上（**一级事实**，来源：dotnet/wpf 源码 `PresentationFramework/MS/Internal/Data/ValueChangedEventManager.cs`——该类型派生自 `WeakEventManager`，经基类的 `CurrentManager` 机制按线程存取单例，内部按源对象建表，表项 `ValueChangedRecord` 对源对象持有的是强引用，注释明确说明"其作用域刻意与 `AddValueChanged`…`RemoveValueChanged` 的调用范围一致"）→ 该绑定源未实现 `INotifyPropertyChanged` 且没有人显式解绑这次订阅。修复方向（跨领域引用）见 `knowledge-base/wpf/rules/05-data-binding.md § 2. 变更通知：INotifyPropertyChanged / ObservableCollection`；
- **排除**：根链末端是应用自身的静态字段或事件（而非 `MS.Internal.Data` 命名空间下的类型）→ 不是本节描述的 Binding 泄漏，转 § 3 或 § 4 按根链末端形态重新比对。

## 3. 可视化树泄漏

### 堆上的可见特征

`Window` / `UserControl` 派生类型的实例数超出该应用预期的活动实例数（判断依据见 § 1）；用 `reference/sos-heap-and-objects.md § 2. !dumpobj` 展开这些实例的字段，其 `DataContext` 字段指向的 ViewModel 实例数同步不回落——界面元素和它绑定的视图模型是一起留下来的。

### 根链形态

元素从可视化树移除不等于可以被回收。三类常见持有方式各自在根链末端呈现不同形态：

| 持有方式 | 根链末端 |
|---|---|
| 静态资源字典持有 | 静态字段 → `ResourceDictionary` → 元素 |
| 逻辑父级残留 | 父元素（自身仍有根）→ 子元素集合 → 元素 |
| 未退订的事件 | 事件源对象 → 委托 `_invocationList` → 元素（作为 `Target`） |

第三行的根链形态与 `reference/debugging-decision-tree.md § 2. 内存持续增长` 中给出的通用事件泄漏形态一致，此处不重复其判据，只强调 WPF 场景下这条链末端的 `Target` 通常是已从可视化树移除的界面元素这一点。

### 判据与下一步

- **证实**：`reference/sos-heap-and-objects.md § 4. !gcroot` 输出的根链末端匹配上表任一行 → 确认为可视化树泄漏，按对应持有方式定位具体代码位置；
- **排除**：`!gcroot` 报告该对象无根路径（找不到任何存活根）→ 该元素实际已经可以被回收，只是本次抓取时 GC 尚未运行到它，**不是泄漏**——这是本节最容易出现的误判，须显式排除后再下结论。

下一步：预防侧规范见 `knowledge-base/wpf/rules/10-performance.md § 7. 内存与泄漏（联动 12 章）`；事件退订规范见 `knowledge-base/wpf/rules/03-mvvm.md § 7. 事件与订阅`。两处均为跨领域引用。

## 4. 弱事件泄漏

## 5. DispatcherTimer 泄漏

## 6. 根链形态图鉴速查表
