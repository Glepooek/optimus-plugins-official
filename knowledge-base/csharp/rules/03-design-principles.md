# 03 · 面向对象与设计原则

> 更新历史：2026-08-21 创建。

分层模型沿用 `01` 章第 6 节（团队统一的一种），本篇给出与代码直接挂钩的可执行设计约束。

## 1. SOLID 原则落地

| 原则 | 可执行检查项 |
|---|---|
| 单一职责 SRP | 一个类一个变更理由；类名能概括全部职责，概括不了就拆 |
| 开闭 OCP | 扩展开放、修改关闭：新行为优先走派生 / 组合 / 策略，不修改既有稳定代码 |
| 里氏替换 LSP | 派生类可替换基类而不改变调用方预期；覆盖方法不弱化前置、不强化后置 |
| 接口隔离 ISP | 接口小而内聚；调用方只依赖所需成员，不用胖接口 |
| 依赖倒置 DIP | 高层模块不依赖低层实现，依赖抽象；依赖由组合根注入 |

- **必须**：类存在两个以上明显无关的职责时拆分
- **必须**：公共接口不暴露调用方不需要的成员
- **应该**：跨层依赖一律面向接口 / 抽象（见 `01` 章第 6 节）
- **禁止**：上帝类（单类数百行、混杂数据 + 行为 + 基础设施访问）通过 review

## 2. 组合优于继承

- **必须**：复用优先考虑组合与委托，而非继承
- **禁止**：为"复用几个方法"而继承不相关的基类
- **禁止**：深度继承链（超过两层需 review）
- **应该**：用 `sealed` 标记不打算被继承的类，向读者明示设计意图

## 3. 接口 vs 抽象类

| 维度 | 接口 | 抽象类 |
|---|---|---|
| 成员 | 契约（无状态） | 可含共享实现与字段 |
| 多重继承 | 支持 | 不支持 |
| 演进成本 | 新增成员破坏所有实现者 | 可加默认实现，破坏面小 |
| 场景 | 能力契约、跨层边界 | 共享基类逻辑 |

- **必须**：契约（服务、策略、跨层边界）用接口；共享实现用抽象类
- **禁止**：抽象类仅因"看起来像基类"而存在；只有一个实现时优先接口或具体类

## 4. class / record / struct 选择矩阵

| 特征 | `class` | `record` | `record struct` / `struct` |
|---|---|---|---|
| 引用 vs 值 | 引用 | 引用 | 值 |
| 值相等 | 需重写 | 默认 | 默认 |
| 可变性 | 可 | 默认不可变（`init`） | 可（应保持不可变） |
| 复制 | 引用共享 | 克隆（`with`） | 拷贝 |
| 场景 | 实体、服务、容器 | DTO、不可变模型 | 小型值对象、性能热点 |

- **必须**：有可变状态和身份标识的领域实体用 `class`；DTO 与不可变模型优先 `record`
- **禁止**：为"少写代码"把大型可变类改成 `record`（值相等语义被滥用）
- **应该**：结构体保持不可变，字段只读；可变 `struct` 是反模式
- **禁止**：结构体过大或含托管引用导致隐式拷贝陷阱——超过 16~24 字节或语义上更像引用时，改用 `class`/`record`

```csharp
// ❌ 可变实体误用 record：用户改个状态就得重建，相等语义还被滥用
public record User
{
    public string Name { get; set; }        // 可变 record：改 set 就违背值语义
    public void ChangeEmail(string email) => Email = email;
}
var a = user with { Name = "bob" };         // 每次变更新建实例，代价高、易错

// ✅ 有身份的领域实体用 class：就地变更，身份（引用）不变
public class User
{
    public string Name { get; private set; }
    public void ChangeEmail(string email) => Email = email;
}
```

```csharp
// ❌ 可变 struct：一次隐式拷贝就能"改了副本原值没变"，防不胜防
public struct Point
{
    public int X; public int Y;             // 公开可变字段
}
var a = points[0]; a.X = 5;                 // 改的是副本，points[0] 没变

// ✅ 不可变 struct：字段只读，构造即定，拷贝也不会出"改了没生效"
public readonly struct Point
{
    public Point(int x, int y) { X = x; Y = y; }
    public int X { get; }
    public int Y { get; }
}
```

## 5. 不可变性

- **必须**：不可变模型用 `init` 或构造函数一次性设置，暴露属性只读
- **应该**：需要变更时返回新实例（`with` 表达式 / 拷贝），而非内部就地修改
- **禁止**：公共可写集合属性直接暴露内部 `List<T>`——用 `IReadOnlyCollection<T>`、`ImmutableArray<T>` 暴露只读视图，或返回副本

```csharp
// ❌ 直接暴露内部 List<T>：调用方可 Add/Remove，绕过所有校验，内部状态被外部改写
public class Order
{
    public List<OrderItem> Items { get; } = new();   // 外部直接 items.Add(...)
}

// ✅ 只读视图：外部只能读，修改必须走领域方法（可校验、可通知）
public class Order
{
    private readonly List<OrderItem> _items = new();
    public IReadOnlyCollection<OrderItem> Items => _items;   // 只读视图
    public void AddItem(OrderItem item) { /* 校验 + 添加 */ }
}
```

## 6. 依赖注入

- **必须**：通过构造函数注入依赖；禁止 `ServiceLocator`、静态服务、业务代码内 `new` 关键服务
- **必须**：依赖关系显式——构造函数签名即依赖清单，不隐藏全局状态
- **应该**：生命周期贴近真实用途：短命状态用 `Transient`，复用连接 / 客户端用 `Singleton`，请求级上下文用 `Scoped`；不确定时选最短合理生命周期
- **必须**：`HttpClient` 等设计为复用的客户端注册为 `Singleton`（类型化 / 命名客户端），禁止逐次 `new`
- **禁止**：在构造函数内做耗时 / 阻塞工作；依赖应立即可用，昂贵代价用 `Lazy<T>` 惰性推迟

```csharp
// ❌ ServiceLocator / 静态服务：依赖藏在代码里，测试无法替换，谁改了服务全乱
public class OrderService
{
    public async Task Create(Order order)
    {
        var repo = ServiceLocator.Get<IOrderRepository>();   // 全局取，隐式依赖
        var mailer = Mailer.Instance;                         // 静态服务，不可替
        await repo.Add(order);
        await mailer.Send(order);
    }
}

// ✅ 构造函数注入：签名即依赖清单，测试可换实现，显式无隐藏
public class OrderService
{
    private readonly IOrderRepository _repo;
    private readonly INotifier _notifier;
    public OrderService(IOrderRepository repo, INotifier notifier)
    {
        _repo = repo;
        _notifier = notifier;
    }
    public async Task Create(Order order)
    {
        await _repo.Add(order);
        await _notifier.Send(order);
    }
}
```

```csharp
// ❌ 逐次 new HttpClient：每个实例独立连接池，高并发下 socket 耗尽
public class WeatherClient
{
    public async Task<string> Get() {
        using var http = new HttpClient();   // 每次调用新建，连接不复用
        return await http.GetStringAsync("https://api.example.com/now");
    }
}

// ✅ 注册为 Singleton / 类型化客户端：连接池复用，由 DI 管理生命周期
services.AddHttpClient<WeatherClient>()
        .ConfigureHttpClient(c => c.BaseAddress = new Uri("https://api.example.com"));
```

## 7. 设计模式适度使用

- **必须**：模式服务目标，不为模式而模式；优先语言原生表达力（`switch 表达式`、委托参数）替代模板类模式
- **应该**：常见模式按需采用：策略（算法族）、观察者（事件 / `IObservable`）、仓储（持久化抽象）、工厂（复杂创建）
- **禁止**：为单例而单例——实例由 DI 容器管理，类内静态 `Instance` 属性反模式禁止
- **禁止**：照搬 GoF 模板而不评估是否真正解决当前问题；解决不了问题就写简单代码

## 8. 领域建模（若采用 DDD）

- **必须**：聚合根是聚合的唯一对外入口；实体变更经由聚合根方法，不绕过它直接改子对象集合
- **必须**：跨聚合一致性用领域事件 / 最终一致，不用跨聚合事务
- **应该**：值对象用 `record` / 不可变实现；实体用 `class` + 身份标识
- **禁止**：领域层引用基础设施（EF、`HttpClient`）；领域接口由基础设施层实现（DIP）
- **应该**：复杂领域规则放领域层（富领域模型），简单的 CRUD 场景不必强上 DDD
