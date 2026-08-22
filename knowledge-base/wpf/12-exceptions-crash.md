# 12 · 异常与崩溃

> 更新历史：2026-08-21 创建。

WPF 应用的异常发生在 UI 线程会冻结界面或直接崩溃。本篇约束异常边界、全局兜底、崩溃恢复与日志。异常设计通用原则团队另有约定，本篇聚焦 WPF 应用形态。

## 1. UI 线程异常

- **必须**：事件处理器 / 命令中不吞异常——让异常按既定路径上报（全局兜底或命令错误处理）
- **必须**：`async void` 事件处理器异常**必**进 `TaskScheduler.UnobservedTaskException` 或应用级兜底，**禁止**裸 `async void` 不设兜底（异常导致进程崩溃）
- **应该**：命令执行包一层错误处理（catch 后转用户可读提示 + 日志），**禁止**命令内裸抛让 UI 冻结
- **禁止**：`catch (Exception) { }` 空吞异常（联不动手排查，问题掩盖）

```csharp
// ❌ 空吞异常：错误被静默吞掉，用户与日志都看不到，问题掩盖
try
{
    await _service.SaveAsync(order);
}
catch (Exception) { }   // 空吞——等于"出错也没人知道"

// ✅ 记录 + 转用户可读提示：至少有一条出路
try
{
    await _service.SaveAsync(order);
}
catch (Exception ex)
{
    _logger.Error(ex, "保存订单失败");
    StatusText.Text = "保存失败，请稍后重试";
}
```

```csharp
// ❌ 裸 async void 不设兜底：按钮点击里的异常无路可走，进程可能崩溃
private async void SaveButton_Click(object sender, RoutedEventArgs e)
    => await _service.SaveAsync(order);    // 异常直接抛到消息循环

// ✅ async void 事件处理器内部包错误处理（async void 是 UI 事件签名，但内部要兜底）
private async void SaveButton_Click(object sender, RoutedEventArgs e)
{
    try
    {
        await _service.SaveAsync(order);
    }
    catch (Exception ex)
    {
        _logger.Error(ex, "保存失败");
        MessageBox.Show("保存失败", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
    }
}
```

## 2. 全局兜底（App 级）

- **必须**：`App.xaml.cs` 订阅 `DispatcherUnhandledException`，统一记录未处理异常（日志 + 用户友好提示 + 是否终止决策）
- **必须**：`TaskScheduler.UnobservedTaskException` 订阅，观测后台任务未处理异常（记录 + 遏制）
- **应该**：`AppDomain.CurrentDomain.UnhandledException` 兜底非 UI 线程崩溃（记录 + 崩溃转储）
- **禁止**：全局兜底吞掉致命异常静默继续（数据损坏风险）——记录后按策略终止或恢复

```csharp
protected override void OnStartup(StartupEventArgs e)
{
    base.OnStartup(e);
    DispatcherUnhandledException += (s, args) =>
    {
        _logger.Error(args.Exception, "未处理 UI 异常");
        MessageBox.Show("发生错误，已记录。", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
        args.Handled = true; // 记录后决定是否继续
    };
    TaskScheduler.UnobservedTaskException += (s, args) =>
    {
        _logger.Error(args.Exception, "未处理后台任务异常");
        args.SetObserved();
    };
}
```

## 3. 崩溃恢复

- **必须**：关键状态（未保存文档、操作进度）崩溃前有持久化或恢复机制，**禁止**依赖用户重做
- **应该**：崩溃后重启提供恢复路径（会话恢复、日志上报）
- **必须**：崩溃诊断信息（异常堆栈、版本、环境）记录并上报，**禁止**静默崩溃无痕
- **应该**：发布版开启崩溃转储采集（`dotnet-dump` / WER 配置），便于离线分析

## 4. 异常与错误设计

- **必须**：异常只用于真正异常路径（不可恢复的错误），**禁止**用异常控制流（`try/catch` 做分支判断）
- **必须**：业务校验错误用返回值 / 结果对象表达（ViewModel 展示错误信息），**禁止**用抛异常表达预期失败（表单校验）
- **应该**：抛异常时附上下文（参数、原因），**禁止** `throw new Exception("failed")` 无信息
- **必须**：异常传播时 `throw;` 保留堆栈，**禁止** `throw ex;`（丢失原始堆栈）

## 5. 取消与资源释放

- **必须**：`CancellationToken` 取消后抛 `OperationCanceledException`，调用方协作响应（联动 `09` 章）
- **必须**：`IDisposable` 资源用 `using` / `await using` 释放（对话框、流、定时器）
- **禁止**：取消 / 关闭窗口时泄漏后台任务（不等待、不取消就退出，任务残留）

## 6. 异常日志

- **必须**：异常记录含堆栈、消息、时间戳、用户上下文（窗口 / 操作），**禁止**只记 "Exception: xxx"
- **必须**：日志不记录敏感信息（密码、令牌，联动 `13` 章）
- **应该**：结构化日志（关键字段可查询），错误级别清晰（`Error` 为未处理 / `Warning` 为可恢复）
- **禁止**：日志影响用户界面（UI 线程日志阻塞），异步记录

## 7. 测试与异常（联动 `11` 章）

- **必须**：命令 / 服务异常路径配测试（模拟服务抛异常，断言错误处理逻辑）
- **必须**：`DispatcherUnhandledException` 逻辑可测（注入 logger + 提示策略）
- **应该**：UI 自动化测试覆盖关键崩溃路径（异常时应用不白屏、提示合理）
