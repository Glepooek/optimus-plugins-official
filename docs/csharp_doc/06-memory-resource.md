# 06 · 内存与资源管理

> 更新历史：2026-08-21 创建。

托管内存由 GC 管理，本篇的"管理"聚焦两件事：**系统/非托管资源的释放**，以及**防泄漏模式**（事件、静态引用、池、LOH）。

## 1. 基本认知

- 托管内存由 GC 回收，**不需要**手动释放；需要手动释放的是**非托管 / 系统资源**：文件句柄、网络 / 数据库连接、`CancellationTokenSource`、GDI、注册表等
- **必须**：实现 `IDisposable` 的对象必须通过 `using` / `await using` 或显式 `Dispose` 释放
- **禁止**：手动调用 `GC.Collect()`（除性能分析场景外）

## 2. IDisposable 正确实现

- **必须**：实现 `IDisposable` 时同时实现 `Dispose(bool)`，并在 `Dispose()` 中调用 `Dispose(true)` + `GC.SuppressFinalize(this)`
- **必须**：`Dispose` 幂等（可安全多次调用）
- **必须**：释放后再调用实例方法应抛 `ObjectDisposedException`
- **禁止**：仅为"清理托管字段"实现 `IDisposable`——托管内存归 GC 管，画蛇添足
- **禁止**：泄漏非托管资源（未释放的句柄 / 连接 / 流）

## 3. using 用法

- **必须**：用 `using` 语句或 using 声明覆盖资源的生命周期
- **应该**：方法级生命周期优先 using 声明（`using var`），缩短作用域
- **必须**：异步资源（`IAsyncDisposable`）用 `await using`
- **禁止**：`using` 块内 return 资源对象，使其生命周期超出释放点（调用方拿到已释放对象）

```csharp
// ❌ using 块内 return 资源：流在 return 前已 Dispose，调用方拿到已关闭的流
public Stream GetDataStream()
{
    using var stream = File.OpenRead("data.bin");   // 返回前流被释放
    return stream;                                   // 调用方 Read 直接 ObjectDisposedException
}

// ✅ 生命周期由调用方管理：方法只创建并转移所有权，谁接收谁负责释放
public Stream OpenDataStream()
{
    return File.OpenRead("data.bin");   // 不 using，调用方负责 using
}
```

## 4. 事件与委托泄漏

- **必须**：短命对象订阅长命对象的事件后，不再使用时 `-=` 退订——否则长命对象通过事件引用保持短命对象不回收
- **应该**：优先弱事件模式，或一次性订阅（如 `CancellationToken.Register` 返回的 `IDisposable`）
- **禁止**：静态事件不加订阅管理（静态引用永存，最常见的泄漏源）

```csharp
// ❌ 只订阅不退订：长命的 domainService 持有短命 window 的引用，window 永不回收
public class MainWindow : Window
{
    public MainWindow()
    {
        _domainService.OrderChanged += OnOrderChanged;   // 一直加，从不减
    }
    private void OnOrderChanged(object? s, EventArgs e) { /* ... */ }
}
// 窗口关闭后 _domainService.OrderChanged 仍指向它 → 内存泄漏

// ✅ 配对退订：Dispose / Closed 时 -=，引用断开，对象可回收
public class MainWindow : Window
{
    public MainWindow()
    {
        _domainService.OrderChanged += OnOrderChanged;
        Closed += OnClosed;
    }
    private void OnClosed(object? s, EventArgs e)
        => _domainService.OrderChanged -= OnOrderChanged;   // 退订，断开引用
    private void OnOrderChanged(object? s, EventArgs e) { /* ... */ }
}
```

## 5. 静态引用

- **必须**：静态字段持有实例引用时，该实例成为 GC 根对象不被回收
- **必须**：静态集合（`List`、`ConcurrentDictionary` 缓存）设大小上限与过期策略
- **禁止**：无界增长的静态缓存（内存泄漏的经典来源）

```csharp
// ❌ 无界静态缓存：每次查询都往静态字典塞，只增不减，进程退出前不回收
private static readonly Dictionary<int, Report> _cache = new();
public Report GetReport(int id)
{
    if (!_cache.TryGetValue(id, out var r))
        _cache[id] = r = _repo.Load(id);     // 永不清理，内存持续增长
    return r;
}

// ✅ 有界 + 过期：MemoryCache 内置上限与过期，超限自动淘汰
private static readonly MemoryCache _cache =
    new(new MemoryCacheOptions { SizeLimit = 1000 });   // 上限 + 滑动过期
public Report GetReport(int id) => _cache.GetOrCreate(id, entry =>
{
    entry.SetSlidingExpiration(TimeSpan.FromMinutes(10));  // 过期策略
    return _repo.Load(id);
});
```

## 6. 大对象堆（LOH）

- **认知**：约 85KB 以上的对象进大对象堆，回收代价高、易碎片化
- **应该**：避免频繁分配超 85KB 的大数组 / 大字符串；需要缓冲时复用（`ArrayPool`）
- **禁止**：热路径频繁创建超 85KB 的临时缓冲

## 7. Span / Memory / ArrayPool

| 类型 | 特性 | 场景 |
|---|---|---|
| `Span<T>` | `ref struct`，仅栈上 / 同步，不可装箱、不可进异步状态机字段 | 高性能同步切片、解析 |
| `Memory<T>` | 可跨 `await` 边界，不可进 `class` 字段 | 异步场景的切片 |
| `ArrayPool<T>` | 租借数组缓冲，用后归还 | 高频缓冲复用 |

- **必须**：`ArrayPool` 租借的数组在 `finally` / `using` 中归还
- **禁止**：租借数组被长期持有或忘记归还——池耗尽时退化为新建数组，性能反噬
- **应该**：仅性能热点引入 `Span`/`ArrayPool`；普通业务代码不必（复杂度高、易错）

```csharp
// ❌ 租借不归还：池里数组被拿走不放回，池子耗尽后每次都是 new，性能反噬
public byte[] ReadBlock(Stream s, int size)
{
    var buffer = ArrayPool<byte>.Shared.Rent(size);
    s.Read(buffer, 0, size);
    return buffer;              // 忘记 Return，数组脱离池管理且长期占用
}

// ✅ finally 保证归还：异常路径也归还，池保持健康
public void ReadBlock(Stream s, int size)
{
    var buffer = ArrayPool<byte>.Shared.Rent(size);
    try
    {
        s.Read(buffer, 0, size);
        Process(buffer);
    }
    finally
    {
        ArrayPool<byte>.Shared.Return(buffer);   // 无论成败都归还
    }
}
```

## 8. 弱引用

- **认知**：`WeakReference` 不阻止回收，适合"可重建的昂贵对象"缓存兜底
- **应该**：需要缓存但重建代价可控的对象用弱引用 / 条件缓存
- **禁止**：把强引用对象塞进无过期策略的缓存（与第 5 节同源）

## 9. 终结器

- **认知**：终结器（`~Class()`）会推迟对象回收（先进终结队列，下一轮才真正回收），且运行时机不确定
- **禁止**：普通类写终结器
- **必须**：确实需要释放非托管资源时才用终结器，并配套 `GC.SuppressFinalize(this)` + `IDisposable`
