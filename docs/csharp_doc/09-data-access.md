# 09 · 数据访问与数据库

> 更新历史：2026-08-21 创建。

默认技术栈为 EF Core + 关系数据库（团队统一实例）。本篇约束查询、事务、迁移与测试的数据访问行为。并发与取消协作见 `04`/`08` 章，安全（注入、敏感数据）见 `14` 章。

## 1. 数据访问基础

- **必须**：ORM 查询保持异步（`ToListAsync` 等），禁止同步数据访问（`.Result` / `.Wait()`，见 `04` 章）
- **必须**：连接字符串等敏感配置不入代码、不入日志（见 `14` 章）
- **禁止**：在领域层直接使用 ORM / 数据访问类型（分层约束见 `01` 章）

## 2. DbContext 生命周期

- **必须**：`DbContext` 按请求注册为 `Scoped`（短生命周期）
- **禁止**：`Singleton` / 静态 `DbContext`（状态泄漏、线程不安全）
- **必须**：通过 DI 获取 `DbContext`，禁止业务代码手动 `new`（明确理由除外）

## 3. 查询编写

- **必须**：查询用投影（`Select` 所需字段），禁止全实体拖出再取字段（Select * 反模式）
- **必须**：避免 N+1——需要导航数据时用 `Include` / `ThenInclude` 一次性加载，或用投影
- **必须**：`Where` 过滤在数据库端执行（EF 翻译为 SQL），禁止 `ToList()` 后内存过滤

```csharp
// ❌ N+1：先查 1 个订单，循环里再逐条查 100 个用户 → 101 次查询
var orders = await ctx.Orders.ToListAsync();
foreach (var o in orders)
{
    var user = await ctx.Users.FindAsync(o.UserId);   // 每订单一次查询，N 次往返
    Console.WriteLine($"{o.Id}:{user?.Name}");
}

// ✅ Include 一次性加载：1 次查询带出关联数据，无 N+1
var orders = await ctx.Orders.Include(o => o.User).ToListAsync();
foreach (var o in orders)
    Console.WriteLine($"{o.Id}:{o.User?.Name}");
```

```csharp
// ❌ ToList 后内存过滤：全表拖进内存再 Where，数据库索引失效、网络传一堆
var active = (await ctx.Users.ToListAsync()).Where(u => u.IsActive);

// ✅ Where 在数据库端执行：EF 翻译为 WHERE 子句，只回传需要的行
var active = await ctx.Users.Where(u => u.IsActive).ToListAsync();
```
- **必须**：列表查询分页（`Take` / `Skip`），禁止无界返回全表
- **禁止**：取全表到内存再聚合——复杂聚合（`GroupBy`、`Count`、`Sum`）在 SQL 端完成
- **应该**：投影返回 DTO / 视图模型，而非实体（防过度暴露与性能）

## 4. 索引与查询性能

- **必须**：高频查询 / 分页排序字段建索引
- **禁止**：无索引的 `LIKE '%...%'`（全表扫描）
- **禁止**：查询对索引列包裹函数（无法命中索引）：`WHERE YEAR(CreatedAt) = 2026`
- **应该**：通过执行计划 / EF 日志验证关键查询；必要时使用手动 SQL（经 review）

```csharp
// ❌ 对索引列包裹函数：YEAR() 使索引失效，每行都要算一次 → 全表扫描
var rows = await ctx.Orders
    .Where(o => o.CreatedAt.Year == 2026)      // 无法走 CreatedAt 索引
    .ToListAsync();

// ✅ 改为范围比较：区间查询命中索引，等价且快
var start = new DateTime(2026, 1, 1);
var end = start.AddYears(1);
var rows = await ctx.Orders
    .Where(o => o.CreatedAt >= start && o.CreatedAt < end)
    .ToListAsync();
```

## 5. 事务与一致性

- **必须**：多步写入用事务（`BeginTransaction`），保证原子性
- **禁止**：事务内执行耗时操作 / 外部调用（长事务持锁，引发阻塞与死锁）
- **必须**：并发更新用乐观并发（并发令牌 / `RowVersion` + 处理 `DbUpdateConcurrencyException`）
- **应该**：默认乐观锁；悲观锁仅在明确需求下使用并评估死锁风险

```csharp
// ❌ 事务内做外部调用：持锁等待第三方 HTTP，锁长时间不放，并发请求全被堵住
await using var tx = await ctx.Database.BeginTransactionAsync();
await ctx.Orders.AddAsync(order);
await _paymentGateway.ChargeAsync(order);      // 外部 HTTP，慢则数秒，全程持锁
await ctx.SaveChangesAsync();
await tx.CommitAsync();

// ✅ 事务只包数据库写入：外部调用在事务外，先收钱/记账再落库（或补偿）
await _paymentGateway.ChargeAsync(order);      // 外部调用先行，不持锁
await using var tx = await ctx.Database.BeginTransactionAsync();
await ctx.Orders.AddAsync(order);
await ctx.SaveChangesAsync();
await tx.CommitAsync();
```

## 6. 迁移管理

- **必须**：Schema 变更通过 EF Migrations 管理，随代码提交，禁止手动改库不同步
- **必须**：自动生成的迁移需 review（可能丢数据、加非空列报错、索引缺失）
- **应该**：破坏性 / 数据迁移与结构迁移分开；生产部署显式执行迁移脚本，**禁止**应用启动自动迁移（默认关闭）
- **应该**：迁移命名表达意图（`Add_Order_Number_Unique`）

## 7. 模型验证

- **必须**：实体边界校验（必填、长度、范围）用 DataAnnotations 或 FluentValidation（**团队统一一种**）
- **必须**：外部输入在应用层校验，不依赖数据库兜底（见 `14` 章）
- **应该**：数据库约束（非空、唯一、长度）与模型校验双保险，数据一致性最终由数据库保证

## 8. 数据类型

- **必须**：金额 / 货币用 `decimal`，禁止 `float` / `double`
- **必须**：日期时间统一 UTC 存储，展示层负责时区转换
- **禁止**：把可数值化数据存为字符串（除非有明确理由并注释）

## 9. 数据访问测试

- **应该**：数据访问集成测试用真实数据库（本地实例 / SQLite / Testcontainers）
- **禁止**：依赖 EF InMemory Provider 验证 SQL 行为（不走 SQL 翻译，行为差异大，会漏真实错误）
- **应该**：InMemory 仅用于无 SQL 语义的单元级测试
