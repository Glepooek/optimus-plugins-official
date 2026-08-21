# 09 · 线程与调度

> 更新历史：2026-08-21 创建。

WPF 是线程亲和模型——UI 只能由 UI 线程操作。本篇约束 Dispatcher 使用、后台任务与 UI 编组、死锁防护。

## 1. UI 线程访问铁律

- **必须**：所有 UI 元素（`DependencyObject`）只能由创建它的 UI 线程操作（`GetValue` / `SetValue` / 属性赋值）
- **必须**：后台线程需要更新 UI 时，经 `Dispatcher` 编组到 UI 线程执行
- **禁止**：后台线程直接改 `TextBlock.Text`、`ObservableCollection`、`ProgressBar.Value` 等 UI 状态（抛 `InvalidOperationException` 或静默损坏状态）
- **应该**：识别后台线程是否持有 UI 引用，封装"UI 更新"逻辑统一走调度，不散布 `Dispatcher` 调用

```csharp
// ❌ 后台线程直接改 UI：跨线程访问 DependencyObject，抛 InvalidOperationException
var result = await Task.Run(() => DoWork());
StatusText.Text = result;       // 后台上下文？在 Task.Run 回调内 = 违规

// ✅ Dispatcher 编组：把 UI 更新调度回 UI 线程
var result = await Task.Run(() => DoWork());
await Application.Current.Dispatcher.InvokeAsync(() =>
    StatusText.Text = result);
```

```csharp
// ✅ IProgress<T> 自动回 UI 线程：无需手动 Dispatcher 编组
private async Task RunAsync()
{
    var progress = new Progress<string>(s => StatusText.Text = s);   // 自动在 UI 线程回调
    await Task.Run(() => DoWork(progress));
}
```

## 2. Dispatcher 使用规范

- **必须**：UI 线程调度用 `Dispatcher`（`Application.Current.Dispatcher`），**禁止**跨线程同步访问
- **必须**：异步调度用 `InvokeAsync`（`await dispatcher.InvokeAsync(...)`），**禁止**同步 `Invoke` 做 UI 更新（同步 Invoke 在 UI 线程等待自身会死锁）
- **必须**：事件处理器 / 命令内耗时操作异步化（`async/await` + 后台任务），**禁止**同步阻塞 UI 线程（界面冻结）
- **应该**：`DispatcherPriority` 按需设置（`Background` 低优先级批量更新、`Input` 响应输入），**禁止**一律 `Normal` 排队导致输入卡顿
- **禁止**：在 UI 线程 `Dispatcher.Invoke` 等待后台线程结果（经典死锁来源，见第 5 节）

## 3. 后台任务与 UI 更新模式

- **必须**：耗时操作（IO、计算、网络）在后台执行，结果回到 UI 线程更新界面
- **必须**：进度上报用 `IProgress<T>`（自动调度到 UI 线程），**禁止**后台线程手动 `Dispatcher.Invoke` 更新进度
- **必须**：长时间操作带 `CancellationToken`，可取消且取消后清理（联动 `12` 章异常处理）
- **应该**：后台任务统一 `Task.Run` / `Task.WhenAll`，**禁止** `Thread.Sleep` 模拟等待（用 `Task.Delay`）
- **禁止**：后台任务更新 UI 后再拿 UI 元素做进一步计算（线程亲和违反）

```csharp
// ✅ 后台取数 + IProgress 进度 + 回 UI 线程
private async void LoadData_Click(object sender, RoutedEventArgs e)
{
    LoadButton.IsEnabled = false;
    var progress = new Progress<int>(p => StatusText.Text = $"加载 {p}%");
    try
    {
        var data = await Task.Run(() => _repo.FetchAll(progress, _cts.Token), _cts.Token);
        DataGrid.ItemsSource = data; // 已回到 UI 线程
    }
    catch (OperationCanceledException) { StatusText.Text = "已取消"; }
    finally { LoadButton.IsEnabled = true; }
}
```

## 4. async/await 与 WPF 上下文

- **必须**：`async void` 仅用于事件处理器（`Click` 等 UI 事件签名），其余一律 `async Task`（联动 `12` 章）
- **必须**：`await` 后代码默认回到 UI 上下文（`SynchronizationContext`），无需手动 `Dispatcher.Invoke`
- **应该**：库 / 非 UI 代码用 `ConfigureAwait(false)` 避免捕获上下文；UI 代码保持默认（回 UI 线程），**禁止** UI 代码乱加 `ConfigureAwait(false)` 导致无法更新界面
- **禁止**：UI 线程 `await` 时用 `.Result` / `.Wait()` 同步等待（死锁风险，联动第 5 节）

## 5. 死锁防护

WPF 死锁典型来源：UI 线程同步等待后台任务，而后台任务又需要回 UI 线程。

- **必须**：UI 线程不 `Wait()` / `.Result` 等待异步任务（阻塞 UI → 后台回不来 → 死锁）
- **必须**：共享资源（集合、缓存）跨线程访问加锁，**禁止** UI 线程持锁等待后台线程（锁反转死锁）
- **应该**：用 `SemaphoreSlim` / `ConcurrentDictionary` 等并发原语替代裸 `lock` 于异步上下文（`lock` 不能跨 `await`）
- **禁止**：`Dispatcher.Invoke` 与后台线程互等（回调链检查：后台需要 UI、UI 等后台 = 环形死锁）

```csharp
// ❌ 经典死锁：UI 线程 Wait() 等待后台，后台又要回 UI 线程 → 互相等待
var task = Task.Run(() => LoadDataAsync());
task.Wait();                       // 阻塞 UI 线程
// LoadDataAsync 内部 await Dispatcher 或需要回 UI 上下文 → 死锁

// ✅ async/await：UI 线程让出控制权，后台完成后回 UI 线程
private async void LoadData_Click(object sender, RoutedEventArgs e)
{
    var data = await Task.Run(() => FetchData());   // UI 线程不阻塞
    DataGrid.ItemsSource = data;                    // 回到 UI 线程，安全
}
```

```csharp
// ❌ 同步 Invoke 在 UI 线程等自身：调度自己执行的代码块，潜在死锁
Application.Current.Dispatcher.Invoke(() => UpdateUI(result));

// ✅ InvokeAsync：非阻塞排队，避免同步等待自身
await Application.Current.Dispatcher.InvokeAsync(() => UpdateUI(result));
```

## 6. 集合跨线程更新

- **必须**：后台修改绑定集合时经 UI 线程调度（`await dispatcher.InvokeAsync(() => Collection.Add(...))`），**禁止**后台线程直接 `ObservableCollection.Add`
- **必须**：高频批量更新用 `BindingOperations.EnableCollectionSynchronization` 或批量调度（一次调度多变更），**禁止**逐项跨线程调度（性能差 + 竞态）
- **应该**：只读展示的集合用不可变集合快照（`ToImmutableList`），避免跨线程访问

## 7. 定时器与调度

- **必须**：UI 周期任务用 `DispatcherTimer`（UI 线程执行、可更新 UI），**禁止** `System.Timers.Timer` / `System.Threading.Timer` 回调直接碰 UI（回调在后台线程）
- **必须**：用后台 `Timer` 时回调内经 Dispatcher 编组，**禁止**后台回调直接更新 UI
- **应该**：非 UI 周期任务（后台轮询）用 `PeriodicTimer` / `System.Threading.Timer`，结果经 `IProgress<T>` 回 UI

## 8. 线程与测试（联动 `11` 章）

- **必须**：ViewModel 的异步逻辑不依赖具体 UI 线程（经抽象接口测试），UI 线程调度逻辑单独测
- **必须**：测试中 `Dispatcher` 行为用测试框架提供的调度上下文（或注入），**禁止**测试直接依赖 `Application.Current.Dispatcher`
- **应该**：UI 自动化测试在真实 UI 线程运行，后台任务用可控的取消 / 等待机制保证确定性
