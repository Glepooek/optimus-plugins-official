# 03 · 面向对象与设计原则

> 更新历史：2026-08-21 创建；2026-08-29 第 1、2、6、8 节的通用条款去重，改为引用 `knowledge-base/architecture/`；同日第 7 节的模式选用判据去重，改为引用 `knowledge-base/design-patterns/`，本篇仅保留 C# 特有增量。

分层模型沿用 `01` 章第 6 节（团队统一的一种），本篇给出与代码直接挂钩的可执行设计约束。

## 1. SOLID 原则落地

五原则的可执行检查项、SRP 的常见误读等**通用**内容见 `knowledge-base/architecture/rules/02-design-principles.md` § 1. SOLID 原则的可执行检查项。C# 侧的附加要求：

- **必须**：`public` 接口不暴露调用方不需要的成员——C# 接口新增成员会破坏所有实现者，胖接口的演进成本在这里被放大
- **应该**：DIP 的抽象归属内层项目，由组合根注入（见 `01` 章第 6 节）
- **禁止**：上帝类（单类数百行、混杂数据 + 行为 + 基础设施访问）通过 review

## 2. 组合优于继承

复用优先组合与委托、禁止为复用方法而继承不相关基类、深继承链须 review 等**通用**约束见 `knowledge-base/architecture/rules/02-design-principles.md` § 2. 组合优于继承。C# 侧的附加要求：

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

组合根的唯一性、禁止服务定位器与静态服务等**通用**约束见 `knowledge-base/architecture/rules/09-composition-root.md` § 1. 组合根的唯一性。生命周期选择的架构含义见同文件 § 3. 生命周期选择的架构含义。构造期不得阻塞见同文件 § 4. 构造期的约束。C# 侧的附加要求：

- **必须**：依赖通过构造函数注入；禁止属性注入与 `IServiceProvider` 直接注入——构造函数签名即依赖清单
- **必须**：三种生命周期的对应关系是 `Transient`（短命状态）/ `Scoped`（请求级上下文）/ `Singleton`（复用连接与客户端）
- **必须**：`HttpClient` 等设计为复用的客户端注册为 `Singleton`（类型化 / 命名客户端），禁止逐次 `new`
- **应该**：昂贵依赖用 `Lazy<T>` 惰性推迟，而非在构造函数内提前构造

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

模式的引入门槛、单个模式的引入与误用信号等**通用**判据见 `knowledge-base/design-patterns/rules/01-pattern-selection.md` § 1. 引入门槛。语言特性对模式的替代关系见 `knowledge-base/design-patterns/rules/06-modern-alternatives.md` § 1. 替代关系总览。反模式识别见 `knowledge-base/design-patterns/rules/05-antipatterns.md` § 1. 过度模式化。C# 侧的附加要求：

- **禁止**：为单例而单例——实例由 DI 容器管理，类内静态 `Instance` 属性反模式禁止（生命周期注册见本篇第 6 节）
- **应该**：替代模板类模式的 C# 语言构件按场景选择：算法族用委托参数、类型分派用 `switch` 表达式与模式匹配、通知用事件或 `IObservable<T>`、迭代用 `IEnumerable<T>` + `yield`
- **禁止**：为 .NET 已提供实现的模式手写类结构——`IDisposable` 的 Dispose 模式（见 `06` 章）、`IEnumerable<T>` 的迭代器均属此类

## 8. 领域建模（若采用 DDD）

聚合根作为唯一入口、一次事务只改一个聚合等**通用**约束见 `knowledge-base/architecture/rules/03-ddd.md` § 4. 聚合。领域事件的语义与约束见同文件 § 6. 领域事件。领域层不依赖基础设施见同文件 § 7. 领域层的纯净性。DDD 的引入门槛见 `knowledge-base/architecture/rules/06-style-selection.md` § 3. 引入 DDD 的门槛。C# 侧的附加要求：

- **应该**：值对象用 `record` / 不可变实现；实体用 `class` + 身份标识（选型依据见本篇第 4 节）
- **禁止**：领域层项目引用 EF Core、`HttpClient` 等基础设施类型；领域接口由基础设施层项目实现
- **禁止**：领域类型带 `[Table]`、`[JsonPropertyName]` 等持久化 / 序列化标注
