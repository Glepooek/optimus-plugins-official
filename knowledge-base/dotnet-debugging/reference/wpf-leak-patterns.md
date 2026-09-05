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

### 堆上的可见特征

`WeakEventManager` 派生类型（如处理绑定通知的那一类管理器）自身实例数正常，应用自身对象的实例数也正常——用 `!dumpheap -stat` 按应用类型名逐个筛查看不到任何异常。这是本节与其余三类的关键差异：泄漏体现在 `WeakEventManager` 内部的监听表结构上，不体现在应用对象上。能看到的征象是该管理器关联的内部结构（监听表）体积随应用运行时间增长，而非某个应用类型的实例数增长。

### 根链形态

**一级事实**，来源：dotnet/wpf 源码 `WindowsBase/System/Windows/WeakEventManager.cs`：`WeakEventManager` 自身不直接持有监听表，而是通过字段 `_table`（取自单例 `WeakEventTable.CurrentWeakEventTable`）按「管理器 + 源对象」为键做索引；每个源对象对应一个内部 `ListenerList`，其中的监听项是 `Listener` 结构体，对监听目标与处理器分别持有的是 `WeakReference`——弱的正是这一侧，监听者本身可以被正常回收。

但 `Listener` 结构体不会在监听者被回收的瞬间从 `ListenerList` 中消失：清理动作由 `ScheduleCleanup` 触发一次 `Purge`，触发时机是「下一次有新监听者加入」或「一次事件分发过程中恰好发现了失效项」，源码注释明确说明这是有意为之的摊销策略——清理要足够频繁以避免大量堆积，但不能频繁到每次操作都扫描一遍付出明显的性能代价。因此根链末端会落在 `WeakEventManager`/`WeakEventTable` 内部的监听表结构上，而不是指向应用代码；短周期内大量订阅退订会让尚未被 `Purge` 扫到的失效项暂时堆积，这段堆积在 dump 中就体现为管理器内部结构的体积增长。

### 判据与下一步

- **证实**：连续两次采样间隔，`WeakEventManager` 及其内部监听表关联的内部结构体积单调增长且不回落 → 说明堆积速度超过了摊销清理的触发频率，需检查是否存在短周期内大量订阅又退订、或长期持有大量已失效监听项的代码路径；
- **排除**：内部结构体积在两次采样间稳定或有涨有落 → 弱事件机制的摊销清理在正常工作，当前的实例数波动是正常现象，泄漏另有成因，转 § 5。

**易被误判的反直觉点**：「用了 `WeakEventManager` 所以不会泄漏」是错误推论。`WeakEventManager` 弱的只是监听者一侧的引用，管理器内部监听表里的登记项本身仍然占用内存，且它的清理是摊销式的、不是即时的——短周期高频订阅退订依然可能造成可观测的堆积，只是形态与应用对象泄漏不同，落在 WPF 内部结构而非应用类型上。

## 5. DispatcherTimer 泄漏

### 堆上的可见特征

`System.Windows.Threading.DispatcherTimer` 实例数超出该应用预期的活动定时器数（判断依据见 § 1）；展开这些实例，其 `Tick` 事件委托的 `Target` 指向已经从可视化树移除、本应已销毁的界面元素或 ViewModel。

### 根链形态

**一级事实**，来源：dotnet/wpf 源码 `WindowsBase/System/Windows/Threading/DispatcherTimer.cs`：`DispatcherTimer` 持有一个私有字段 `_dispatcher`，是对所属 `Dispatcher` 的**普通强引用**（未包裹 `WeakReference`）；定时器启动时调用 `_dispatcher.AddTimer(this)` 把自身注册进 Dispatcher，`Stop()` 时调用 `_dispatcher.RemoveTimer(this)` 注销——但两者不对称：某些零间隔、同线程的重启路径会跳过 `AddTimer` 直接提升执行，只有 `Stop()` 才总是配对调用 `RemoveTimer`，也就是说只要不调用 `Stop()`，这次注册就不会被撤销。`Tick` 是字段式事件（`public event EventHandler Tick`），其编译器生成的委托字段由 `DispatcherTimer` 实例自身持有，因此任何订阅了 `Tick` 的处理器及其 `Target`（界面元素或 ViewModel）都被这个委托字段直接强引用。

`Dispatcher` 一侧是否用强引用集合持有已注册的定时器，源码未能在时间盒内查证到具体字段声明与类型（`AddTimer`/`RemoveTimer`/`_timers` 字段的实现体在可获取的源码片段之外）；但从行为层面看——`Dispatcher` 需要在每次消息循环轮转时能提升到期的定时器执行 `Tick`，注册期间必须能随时枚举到该定时器，这一行为要求它对已注册且未 `Stop` 的定时器保持可达（**经验性知识**，标注为行为层面的推断，不假设具体字段名）。可查询的行为锚点与 Task 1 一致：定时器创建时关联的 `Dispatcher` 可通过 `CurrentDispatcher`/`FromThread` 查询到线程归属，不依赖某个具体命名的静态字典字段。

按以上事实，机制链呈现为：

```
Dispatcher（应用级生命周期，GC 根可达）
  → 未 Stop 的 DispatcherTimer（注册期间对 Dispatcher 保持可达，具体持有集合未查证，经验性推断）
    → Tick 委托（字段式事件，由 DispatcherTimer 实例强引用）
      → 委托 Target（界面元素 / ViewModel）
        → 其整个对象图
```

链的前两段（`DispatcherTimer` → `_dispatcher` 强引用、`Tick` 委托字段）为一级事实；`Dispatcher` → `DispatcherTimer` 一段为经验性行为推断，未在源码中确认具体字段名。

### 判据与下一步

- **证实**：`reference/sos-heap-and-objects.md § 4. !gcroot` 显示根链起点落在 `Dispatcher`、中途经过一个未 `Stop` 的 `DispatcherTimer` 实例、末端是 `Tick` 委托的 `Target` → 确认为本节描述的 DispatcherTimer 泄漏，检查对应代码路径是否在界面卸载时遗漏了 `Stop()` 调用；
- **排除**：`DispatcherTimer` 实例数在预期范围内、或 `!gcroot` 根链未经过 `Dispatcher`/`DispatcherTimer` → 不是本节描述的泄漏，转 § 6 反查表按实际根链形态重新分类。

下一步（跨领域引用）：预防侧规范见 `knowledge-base/wpf/rules/09-threading.md § 7. 定时器与调度`。

## 6. 根链形态图鉴速查表

本节是反查入口，不重复 § 2–5 的内容，只做映射：已经拿到一条 `!gcroot` 输出、但不确定属于哪一类泄漏时，按下表左列的标志物定位到对应小节。

| `!gcroot` 输出中出现的标志物 | 泄漏类型 | 详见 |
|---|---|---|
| 根链末端为 `MS.Internal.Data` 命名空间下的事件管理器类型（`PropertyDescriptor` 订阅登记项） | Binding 泄漏 | `§ 2. Binding 泄漏` |
| 静态字段 → `ResourceDictionary` → 元素 | 可视化树泄漏（静态资源） | `§ 3. 可视化树泄漏` |
| 父元素（自身仍有根）→ 子元素集合 → 元素 | 可视化树泄漏（逻辑父级） | `§ 3. 可视化树泄漏` |
| 事件源对象 → 委托 `_invocationList` → 元素（作为 `Target`） | 可视化树泄漏（未退订事件） | `§ 3. 可视化树泄漏` |
| 根链末端落在 `WeakEventManager`/`WeakEventTable` 内部监听表结构上 | 弱事件泄漏 | `§ 4. 弱事件泄漏` |
| `Dispatcher` → 未 `Stop` 的 `DispatcherTimer` → `Tick` 委托 → 委托 `Target` | DispatcherTimer 泄漏 | `§ 5. DispatcherTimer 泄漏` |

根链末端不匹配上表任何一行时，不属于本篇覆盖的四类泄漏。可能是应用自身的静态集合持有，这是通用形态，见 `reference/debugging-decision-tree.md § 2. 内存持续增长`；也可能是非托管泄漏，判据见同节的 `!eeheap` 用法。
