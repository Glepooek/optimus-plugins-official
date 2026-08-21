# 05 · 异常处理与错误设计

> 更新历史：2026-08-21 创建。

本篇与 `04` 章（取消传播）协作，决定"失败如何表达、如何传播、如何恢复"。与 `csharp-code-review` skill 第 12 类（API 设计与健壮性）直接对应。

## 1. 失败表达：抛异常 vs 返回结果

| 维度 | 抛异常 | Result / 返回值 |
|---|---|---|
| 适用 | 程序缺陷、前置条件失败、无法继续执行 | 预期的业务失败、可恢复的验证失败 |
| 调用方 | 上层决定如何恢复 | 显式分支处理 |
| 性能 | 有开销（不该用于常规路径） | 无异常开销 |

- **必须**：一个方法内"失败"的表达方式统一——要么统一抛异常，要么统一返回 Result / 默认值，**不得混用**
- **应该**：业务规则失败（校验不过、资源不存在）用显式返回 / Result；程序错误（参数非法、状态错乱）抛异常
- **禁止**：用异常做常规控制流（如用 `try/catch` 判断文件是否存在——用 `File.Exists`）

```csharp
// ❌ 用异常做常规控制流：预期"文件不存在"是正常分支，却走异常路径（性能 + 语义错）
try
{
    File.ReadAllText(path);      // 每次探测都抛/接异常
    return true;
}
catch (FileNotFoundException) { return false; }

// ✅ 常规分支用返回判断，异常留给真正的意外
if (File.Exists(path))
{
    return File.ReadAllText(path);
}
return null;
```

## 2. 异常类型选择

- **必须**：优先内置异常，语义对得上就用：`ArgumentException`（含 `ArgumentNullException`、`ArgumentOutOfRangeException`）、`InvalidOperationException`、`NotSupportedException`、`TimeoutException`
- **应该**：仅当内置类型无法表达语义时才定义自定义异常
- **必须**：自定义异常提供默认 / 带消息 / 带消息+内部异常三种构造函数
- **禁止**：直接抛 `Exception` 基类型；禁止 `ApplicationException`（历史遗留，不应用）
- **必须**：`throw new Exception("...")` 一律替换为具体类型

```csharp
// ❌ 裸 Exception / ApplicationException：调用方无法按类型区分，只能 catch(Exception)
throw new Exception("用户不存在");          // 用户不存在 vs 参数非法，catch 无从分辨

// ✅ 语义具体的内置异常：调用方可精确捕获
throw new ArgumentException("用户 id 不能为空", nameof(userId));
throw new InvalidOperationException("订单已支付，不能重复支付");
throw new TimeoutException("调用支付网关超时");
```

## 3. 异常消息

- **必须**：异常消息写给人读：发生了什么、为何发生、可选的补救
- **禁止**：消息中拼接未经验证的动态内容导致敏感信息泄露（见 `14` 章）
- **应该**：公共 API 抛出的异常消息属于契约，修改属破坏性变更

## 4. 捕获边界与过滤

- **必须**：只捕获能处理的异常类型；禁止裸 `catch (Exception)` 或空 `catch`
- **必须**：`catch` 块内必须有实质处理（记录日志、包装向上抛、重试）；只打印不处理视同吞异常
- **禁止**：静默吞异常——空 catch、只 `Console.WriteLine` 后继续 = 让调用方误以为成功
- **应该**：条件性处理用异常过滤器 `catch (XException ex) when (condition)`
- **必须**：`catch` 后原样上抛用 `throw;` 保留堆栈；**禁止** `throw ex;`（重置堆栈）

```csharp
// ❌ 空 catch：失败被吞掉，调用方以为成功，故障无从定位
try
{
    await _payment.ChargeAsync(order);
}
catch (Exception) { }               // 支付失败无声，用户看到"已支付"

// ✅ 有实质处理：记录后重抛，或包装后上抛，绝不静默
try
{
    await _payment.ChargeAsync(order);
}
catch (PaymentException ex)
{
    _logger.LogError(ex, "支付失败，订单 {OrderId}", order.Id);
    throw;                          // 保留原始堆栈，让上层决定恢复
}
```

```csharp
// ❌ throw ex：堆栈从这一行重新开始，原始抛出点丢失，排查无从下手
catch (Exception ex)
{
    Log(ex);
    throw ex;      // 堆栈变成这里，看不到真实的失败位置
}

// ✅ throw：原样重抛，堆栈完整保留
catch (Exception ex)
{
    Log(ex);
    throw;         // 保留原始调用链
}
```

## 5. 包装与保留上下文

- **必须**：跨层抛出需要补充上下文时用内部异常链：`throw new XException("...", ex);`
- **禁止**：层层捕获又原样重抛（不添加任何信息）——每一层 catch 要么增值，要么直接放行
- **必须**：并行任务失败会聚合为 `AggregateException`；需要恢复时正确展开处理，**禁止**丢弃未观察的兄弟任务异常

## 6. 失败原子性

- **必须**：方法抛异常时，对外状态保持一致（不处于半修改状态）——先校验、后修改，或变更前复制
- **必须**：多步操作要么全部成功要么全部失败，需要时用事务 / 补偿
- **禁止**：先改数据再发现错误返回，让调用方看到部分生效的状态

## 7. 与异步 / 取消协作（联动 04 章）

- **必须**：`OperationCanceledException` 与业务异常分离——取消沿调用链传递，捕获后要么放行、要么转为 `TaskCanceledException`
- **禁止**：把取消当失败吞掉（用户主动取消不是 bug）
- **必须**：`async void` 事件处理器内捕获全部异常（见 `04` 章第 8 节），未观察异常会直接崩溃进程

## 8. 日志与异常

- **必须**：记录异常时包含异常对象本身（`Log.Error(ex, "...")`），保留堆栈与内部异常链
- **禁止**：只记录 `ex.Message` 而丢弃堆栈（排查无从下手）
- **应该**：异常日志携带上下文关联信息（请求 ID、业务 ID），由 `11` 章统一；日志不落敏感数据（见 `14` 章）
