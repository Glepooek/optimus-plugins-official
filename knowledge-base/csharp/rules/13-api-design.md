# 13 · API 设计与版本化

> 更新历史：2026-08-21 创建。

"公共 API" 涵盖：库的公共类型与成员、Web 端点、服务契约、数据库 Schema——凡变更会波及消费者的都是契约。异常与取消语义联动 `04`/`05` 章；契约测试联动 `12` 章；仓库 `reference/refit.md` 为 REST 客户端契约参考。

## 1. 公共 API 的契约属性

- **必须**：公共 API 是团队契约，新增、变更、删除均需评审
- **禁止**：公共 API 暴露实现细节（内部类型、可变集合、实现命名）
- **必须**：公共 API 变更记录到 CHANGELOG（联动 `16` 章）

## 2. 设计原则

- **必须**：公共成员命名表达意图，参数与返回类型明确（联动 `02` 章命名规则）
- **必须**：公共入口先做参数校验（`ArgumentNullException`、`ArgumentOutOfRangeException`，语义见 `05` 章）
- **必须**：I/O 绑定公共 API 接受并传播 `CancellationToken`（联动 `04` 章第 6 节）
- **必须**：公共 API 配 XML 文档注释（联动 `17` 章）
- **应该**：返回只读 / 不可变视图，不暴露可写集合（联动 `03` 章第 5 节）
- **应该**：方法依赖调用方预先配置好的外部状态时（如注入的 `HttpClient` 必须已设置 `BaseAddress`），通过构造函数校验或 XML 注释明确该前提

```csharp
// ❌ 隐式依赖调用方配置：BaseAddress 未设置时运行期才报错，且报错信息与"配置遗漏"无关
public class WeatherClient(HttpClient http)
{
    public Task<string> GetAsync() => http.GetStringAsync("current");   // 依赖 http.BaseAddress 已设置
}

// ✅ 构造函数显式校验前提：配置遗漏在启动期就能定位
public class WeatherClient
{
    public WeatherClient(HttpClient http)
    {
        if (http.BaseAddress is null)
            throw new ArgumentException("HttpClient.BaseAddress 必须预先配置", nameof(http));
        _http = http;
    }
    private readonly HttpClient _http;
}
```

## 3. DTO 与模型分离

- **必须**：API 边界用 DTO，不直接暴露领域实体（防过度暴露、解耦演进）
- **必须**：DTO ↔ 领域映射显式（手写映射，或配置统一的映射方案如 AutoMapper）
- **禁止**：公共 API 直接返回 EF 实体（懒加载序列化异常、字段泄漏）
- **应该**：DTO 设边界职责，不承载业务逻辑

```csharp
// ❌ 公共 API 返回 EF 实体：懒加载代理出序列化异常，导航属性把内部结构全暴露
public Order GetOrder(int id)
{
    return _ctx.Orders.Include(o => o.Items).First(o => o.Id == id);  // 直接甩实体出去
}

// ✅ 边界用 DTO：只暴露该传的字段，序列化稳定，实体演进不波及契约
public record OrderDto(int Id, decimal Amount, IReadOnlyList<OrderItemDto> Items);
public OrderDto GetOrder(int id)
{
    var order = _ctx.Orders.Include(o => o.Items).First(o => o.Id == id);
    return new OrderDto(order.Id, order.Amount,
        order.Items.Select(i => new OrderItemDto(i.Id, i.Name)).ToArray());
}
```

## 4. 版本化与兼容

遵循语义化版本（semver）：`major` 破坏性、`minor` 新特性、`patch` 修复。

- **必须**：破坏性变更升 `major`，并附迁移指南
- **必须**：新增可选参数 / 成员须向后兼容（不改变既有签名语义）
- **禁止**：静默改变既有 API 语义（相同签名、不同行为）
- **应该**：Web API 显式版本化（URL / Header / 版本策略，团队统一一种）
- **应该**：接口演进优先加新方法，而非修改既有契约（接口默认实现是演进手段之一）

## 5. 弃用与移除

- **必须**：移除公共成员先标 `[Obsolete]`，给过渡期再移除
- **禁止**：直接删除被使用的公共成员（`[Obsolete]` 不是立即移除的许可）
- **应该**：`[Obsolete]` 消息说明替代方案

```csharp
// ❌ 直接删除：所有消费者编译失败，库升级即破坏，无过渡期
public Task<Order> GetOrderByNumber(string orderNo) { /* ... */ }   // 下一版本直接删掉

// ✅ 先标 Obsolete 给过渡期：消费者有编译告警指引替代，下个大版本再移除
[Obsolete("请使用 GetOrderAsync(int id) 替代", false)]
public Task<Order> GetOrderByNumber(string orderNo) { /* ... */ }
```

## 6. 契约测试

- **必须**：公共契约变更配契约测试（联动 `12` 章第 10 节）
- **必须**：后端契约变更同步回归客户端契约

## 7. 与仓库资产

- **必须**：Refit 接口即 REST 客户端契约，与后端契约保持同步（见 `reference/refit.md`）
- **应该**：REST 端点遵循统一资源与错误体格式，错误响应携带可解析的错误码与详情
