# 04 · 异步编程

> 更新历史：2026-08-21 创建。

异步是 C# 并发模型的主干。本篇约束覆盖全链路、阻塞反模式、取消传播与资源释放。异常语义与取消协作见 `05` 章。

## 1. 全链路异步

- **必须**：I/O 绑定操作（文件、网络、数据库、HTTP）使用 `async`/`await`，禁止阻塞等待
- **必须**：异步方法内不调用阻塞 API（`.Result`、`.Wait()`、`.GetAwaiter().GetResult()`、`Task.WaitAll`）——见第 2 节反模式表
- **必须**：`async` 一路传播到入口（调用链全程 async，不在中途 `.Result` 截断）
- **应该**：UI 上下文中才用 `Task.Run` 卸载 CPU 绑定工作；服务端 I/O 已异步时 `Task.Run` 是浪费

## 2. 反模式表

| 反模式 | 问题 | 修复 |
|---|---|---|
| `.Result` / `.Wait()` | 同步上下文死锁、线程池饥饿 | `await` |
| `.GetAwaiter().GetResult()` | 同上 | `await` |
| `Task.Run(...).Result` | 无意义线程跳转 + 死锁风险 | `await` |
| `async void` | 异常逃逸、进程崩溃 | `async Task`；事件处理器例外（见第 8 节） |
| `async` 但无 `await` | 编译器警告 + 误导调用方 | 删 `async`，返回 `Task.FromResult` 或改同步 |
| 循环内串行 `await` 独立请求 | 慢、串行化 | 评估 `Task.WhenAll`（注意并发上限） |

```csharp
// ❌ .Result / .Wait()：阻塞 UI/请求线程，同步上下文被占死锁
public string Load()
{
    var html = httpClient.GetStringAsync(url).Result;   // UI 线程：GetResult 等 I/O，I/O 完成想回 UI 线程却回不来 → 死锁
    return html;
}

// ✅ 全链路 await：线程释放给调用方，I/O 完成再续跑
public async Task<string> LoadAsync()
{
    var html = await httpClient.GetStringAsync(url);
    return html;
}
```

## 3. ConfigureAwait 策略

- **必须**：类库 / 库代码使用 `Task.ConfigureAwait(false)`，避免捕获同步上下文，防死锁、提性能
- **应该**：需要回到特定线程上下文的代码（UI）不使用 `ConfigureAwait(false)`
- **必须**：团队统一策略——类库一律 `false`，入口层不设；**禁止**在同一代码库内混用导致行为不一致

```csharp
// ❌ 类库代码不 ConfigureAwait：捕获调用方同步上下文，死锁风险 + 无谓开销
public async Task<Order> GetAsync(int id)
{
    return await _repo.FindAsync(id);          // 类库不应关心 UI/请求上下文
}

// ✅ 类库一律 ConfigureAwait(false)：不捕获上下文，防死锁、提性能
public async Task<Order> GetAsync(int id)
{
    return await _repo.FindAsync(id).ConfigureAwait(false);
}
```

## 4. Task vs ValueTask

| 场景 | 选择 |
|---|---|
| 一般异步、公共 API | `Task` / `Task<T>` |
| 高性能热点路径，结果常同步完成或立即可用 | `ValueTask` / `ValueTask<T>` |
| 同一异步方法会被 `await` 多次 | `Task`（`ValueTask` 不可多次 await） |

- **必须**：公共 API 默认 `Task`；`ValueTask` 仅在有明确性能依据时使用并注释原因
- **禁止**：`ValueTask` 被缓存、被并发 `await`、或保存为字段后多次使用

## 5. 组合与并行

- **必须**：独立异步操作用 `Task.WhenAll` 并行等待；只需其一完成用 `Task.WhenAny`
- **禁止**：为"省事"对上千个任务 `Task.WhenAll`——用分区 / `SemaphoreSlim` 限制并发度
- **必须**：`SemaphoreSlim` 等可异步等待的原语配套 `await using` 或 `finally` 释放
- **禁止**：同步 `lock` 内 `await`（死锁）；需要异步互斥用 `SemaphoreSlim` 或 `Channel<T>`

```csharp
// ❌ 循环内串行 await 独立请求：一个接一个，N 个请求 N 倍延迟
foreach (var userId in userIds)
{
    var user = await api.GetUserAsync(userId);   // 每个都等上一个完成
    users.Add(user);
}

// ✅ 独立请求并行：Task.WhenAll 同时发起，总耗时 ≈ 最慢单个
var tasks = userIds.Select(api.GetUserAsync);
var users = await Task.WhenAll(tasks);           // 注意并发上限，超大列表用分区/SemaphoreSlim
```

## 6. CancellationToken 传播

- **必须**：所有 I/O 绑定异步方法接受 `CancellationToken cancellationToken = default` 并向下传递（公共 API 尤其，见 `13` 章）
- **必须**：把外部取消令牌透传到底层 I/O（EF 查询、`HttpClient`、文件流）
- **必须**：捕获 `OperationCanceledException` 时区分"取消"与"失败"——取消沿调用链传递，不吞不掉
- **禁止**：签名有 `CancellationToken` 却不检查、不传递（纯摆设 = 误导调用方）
- **应该**：超时控制用 `CancellationTokenSource.CancelAfter(...)`，替代手写超时轮询

## 7. 异步流

- **必须**：分批 / 流式返回数据用 `IAsyncEnumerable<T>`，替代"整批 `List<T>` 一次返回"
- **必须**：消费 `IAsyncEnumerable<T>` 用 `await foreach`，并继续传播取消令牌
- **禁止**：为返回一个完整小集合而用 `IAsyncEnumerable<T>`（直接 `Task<List<T>>` 即可）

## 8. async void 例外规则

- **必须**：`async void` 仅允许用于事件处理器，且处理器内用 `try/catch` 包裹全部逻辑，防止未观察异常
- **禁止**：`async void` 用于公共方法、库 API、构造函数

```csharp
// ❌ async void 公共方法：异常逃逸到调用方之外，无人能捕获，直接崩进程
public async void Save(Order order)
{
    await _repo.Add(order);       // 抛异常 → 未观察异常 → 进程崩溃
}

// ✅ 公共方法返回 Task：异常进入 Task，由 await 的调用方捕获
public async Task Save(Order order)
{
    await _repo.Add(order);
}

// ✅ 事件处理器是唯一例外：必须 try/catch 兜底，防止异常逃逸
public async void OnSaveClick(object? sender, RoutedEventArgs e)
{
    try
    {
        await Save(CurrentOrder);
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "保存订单失败");
    }
}
```

## 9. 资源与泄漏

- **必须**：`SemaphoreSlim`、`Channel<T>`、`CancellationTokenSource` 等可释放的异步原语用 `using` / `await using` 释放
- **应该**：长生命周期对象持有的 `CancellationTokenSource` 用后释放，防句柄 / 内存泄漏
- **禁止**：fire-and-forget 的裸 `Task`（不 await 不观察）——后台任务必须登记到生命周期管理并记录异常
