# 08 · 并发与线程安全

> 更新历史：2026-08-21 创建。

本篇约束线程级并发。异步并发的组合、取消与传播见 `04` 章；锁与性能的交叉约束见 `07` 章。

## 1. 共享状态原则

- **必须**：多线程访问的可变共享状态必须同步（锁 / 原子操作 / 并发集合 / 不可变）
- **必须**：优先不可变与无共享——状态封装进实例，尽量用函数式转换
- **禁止**：暴露可变公共字段让外部随意写入（线程安全隐患且无门禁）
- **应该**：默认不可变，确需共享时显式设计同步策略

## 2. lock 使用规范

- **必须**：互斥用 `lock` 语句（`Monitor`）
- **必须**：锁对象为私有只读字段：`private readonly object _lock = new();`
- **禁止**：锁 `this`、锁 `typeof(...)`、锁字符串字面量（公共对象易被外部意外锁住，导致死锁 / 误锁）
- **必须**：锁内只做最小临界区工作；禁止锁内 I/O、慢操作、嵌套锁
- **禁止**：锁内 `await`（`Monitor` 不支持异步重入，必死锁；需要异步互斥用 `SemaphoreSlim`）
- **必须**：涉及多个锁时，全仓库统一获取顺序（防死锁，见第 8 节）

```csharp
// ❌ lock 内 await：Monitor 是线程持锁，await 释放线程后锁无人持、也无人可再进 → 死锁
lock (_lock)
{
    var data = await _repo.GetAsync();   // 持锁线程被 await 放走，锁永远释放不了
}

// ✅ 异步互斥用 SemaphoreSlim：可 await 等待，不绑定线程
private readonly SemaphoreSlim _gate = new(1, 1);
await _gate.WaitAsync();
try
{
    var data = await _repo.GetAsync();
}
finally
{
    _gate.Release();
}
```

```csharp
// ❌ 锁 this / typeof：锁的是可被外部接触的公共对象，别人也能 lock 同一个 → 误锁、死锁
public class Counter
{
    public void Increment() { lock (this) { /* ... */ } }        // 实例可能被外部传出去锁
    public static void Reset() { lock (typeof(Counter)) { /* ... */ } }  // 类型对象全局唯一，处处可锁
}

// ✅ 私有锁对象：只有本类能拿到引用，杜绝外部误锁
public class Counter
{
    private readonly object _lock = new();
    public void Increment() { lock (_lock) { /* ... */ } }
}
```

## 3. 原子操作

- **必须**：简单计数 / 标志用 `Interlocked`（`Increment`、`Decrement`、`CompareExchange`、`Exchange`）
- **禁止**：多线程裸 `count++` / `count--`（非原子）
- **应该**：复杂状态用锁或并发集合，不强行原子化

```csharp
// ❌ 裸 count++：读→加→写三步非原子，两个线程同时走会丢更新（竞态）
public class Metrics
{
    private int _total;
    public void Record() => _total++;        // 两线程各 Record 一次，结果可能只 +1
}

// ✅ Interlocked.Increment：单指令原子完成，无锁无竞态
public class Metrics
{
    private int _total;
    public void Record() => Interlocked.Increment(ref _total);
}
```

## 4. 并发集合选择

| 集合 | 特性 | 场景 |
|---|---|---|
| `ConcurrentDictionary<TKey,TValue>` | 并发字典，复合方法原子 | 全局字典、缓存 |
| `ConcurrentQueue<T>` | FIFO | 生产者-消费者 |
| `ConcurrentStack<T>` | LIFO | 工作栈 |
| `ConcurrentBag<T>` | 无序、局部线程优先 | 同线程生产者消费者 |
| `Channel<T>` | 异步生产消费、背压 | 异步管道（配合 `04` 章） |

- **必须**：需要"读-改-写"原子时用并发集合提供的方法（`GetOrAdd`、`AddOrUpdate`），禁止先 `TryGetValue` 再 `Add`（非原子）
- **禁止**：迭代并发集合时并发修改——需快照时先 `ToList()` / `ToArray()`

```csharp
// ❌ TryGetValue 再 Add：两步之间另一个线程已插入，重复键、覆盖、异常都有可能
if (!_cache.TryGetValue(key, out var value))
{
    value = Load(key);
    _cache.Add(key, value);      // 并发下可能已存在 → 抛异常或覆盖
}

// ✅ GetOrAdd：查+插在一个原子操作内完成，由并发字典保证
var value = _cache.GetOrAdd(key, k => Load(k));
```

## 5. 可见性

- **认知**：多线程共享变量的修改默认不保证对其他线程可见，需要内存屏障（`lock` / `Interlocked` / `volatile`）
- **禁止**：用裸 `volatile` 实现复杂内存序（极难正确）；需要强语义时用 `Interlocked` / `lock`
- **必须**：跨线程共享的简单标志用 `volatile` 或 `Interlocked`，或由 `lock` 保护

## 6. 任务级并行

- **应该**：CPU 绑定的大数据集并行用 `Parallel.ForEach`（内部分区与调度）
- **禁止**：`Parallel` 循环内做 I/O（应改异步 / 管道）
- **禁止**：`Parallel` 内访问非线程安全共享状态
- **必须**：`Parallel` 内累加用 `Interlocked` 或局部初始化重载，避免共享累加变量竞争

## 7. 锁选择矩阵

| 同步原语 | 适用 | 备注 |
|---|---|---|
| `lock` / `Monitor` | 通用互斥 | 首选 |
| `SemaphoreSlim` | 计数信号量 | 异步可用，可限并发 |
| `ReaderWriterLockSlim` | 读多写少 | 读并发、写独占 |
| `SpinLock` | 极短临界区、无阻塞 | 慎用，热路径专家场景 |

- **必须**：能并发集合 / 原子解决就不上锁；必须上锁则临界区最小
- **禁止**：无脑 `lock` 包裹整方法——同步应在最小边界

## 8. 死锁防护

- **必须**：多锁时全局统一获取顺序
- **必须**：锁粒度小（临界区最小化，缩短持锁时间）
- **禁止**：锁内调用外部回调 / 事件 / 虚方法（可能反向加锁或重入）
- **应该**：高风险锁用 `Monitor.TryEnter` 带超时检测，或改用无锁 / 并发集合方案

## 9. 静态可变状态

- **禁止**：静态可变集合 / 单例状态无同步（全局共享是数据竞争重灾区）
- **必须**：静态状态要么不可变（`readonly` / `Immutable*`），要么并发安全（并发集合 + 原子操作）
