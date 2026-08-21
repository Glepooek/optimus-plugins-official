# 12 · 测试规范

> 更新历史：2026-08-21 创建；同日补充第 11–13 节（测试框架选型、Mock 实操、框架快速上手）及第 14 节（dotnet test 一键执行）。

测试是质量的刹车。本篇约束测试策略、结构、mock 边界与确定性。集成 / 契约测试与数据访问协作见 `09` 章；契约测试与 API 演进见 `13` 章。

## 1. 测试策略与金字塔

- **必须**：测试分层——单元（多、快）→ 集成（真实协作）→ E2E（少、慢）
- **必须**：新功能配测试；修复 bug 先写能复现的测试再修
- **禁止**：只有 E2E 没有单元测试（慢、脆、故障难以定位）
- **应该**：E2E 只覆盖关键用户路径，普通逻辑下沉到单元 / 集成

## 2. 测试结构

- **必须**：测试项目命名 `<被测>.Tests`，目录镜像源码结构
- **必须**：被测类 `UserManager` 对应测试类 `UserManagerTests`
- **禁止**：把测试散落在业务项目内（与 `01` 章 tests/ 布局一致）

## 3. 单元测试

- **必须**：AAA 三段式（Arrange-Act-Assert），段间空行分隔
- **必须**：测试命名表达行为：`Method_Scenario_Expected`（`Divide_ByZero_Throws`）或 Given_When_Then
- **必须**：一个测试聚焦一个行为；同一行为的多个断言可共存
- **禁止**：测试依赖执行顺序或共享可变状态——每个测试独立可重复
- **禁止**：测试内含随机性 / 时间依赖（固定输入，或注入时钟 / `Random`）

## 4. Mock 最小化

- **必须**：只 mock 被测单元的**外部边界**（I/O、时间、随机、外部服务）
- **禁止**：mock 被测单元自身的实现（把一切 mock 掉等于测 mock，无价值）
- **应该**：协作对象可真实使用时优先真实使用（优先真实小对象）
- **应该**：依赖注入 + 纯函数让被测单元更易测（联动 `03` 章）

## 5. 断言风格

- **必须**：断言库团队统一（xUnit 断言 或 FluentAssertions/Shouldly 二选一）
- **必须**：浮点断言用近似比较（`Assert.Equal(expected, actual, precision)`），禁止 `==`
- **禁止**：断言实现细节（测"怎么做的"而非"结果对不对"）

## 6. 测试隔离与确定性

- **必须**：测试独立——不依赖前序测试留下的状态、不依赖数据库残留数据
- **必须**：测试数据库隔离（每测试清理 / 事务回滚）
- **禁止**：跨测试共享静态可变状态（需要并行时必须是线程安全的）
- **应该**：并行测试保持确定性（不共享资源、不共享固定端口）

## 7. 集成测试

- **必须**：集成测试验证真实协作（数据库、HTTP、消息中间件）
- **必须**：集成测试运行在可控环境（Testcontainers、本地实例、契约测试桩），**禁止**连生产资源
- **禁止**：把集成测试写成慢速 E2E（每个测试走完整链路）
- **应该**：集成测试使用专用测试配置（测试数据库、测试队列），与开发 / 生产隔离

## 8. 覆盖率

- **应该**：设覆盖率目标（行覆盖 ≥ 70%，关键路径 ≥ 80%），按模块而非总量考核
- **禁止**：把覆盖率当唯一标准——无断言的覆盖是假质量
- **应该**：金额、安全、并发等高风险领域提高覆盖率要求
- **禁止**：为凑覆盖率写无效断言（永远为真的断言无意义）

## 9. 测试数据

- **必须**：测试数据自包含（工厂 / 构建器创建），**禁止**依赖生产数据
- **应该**：用测试数据工厂 / 构建器模式（TestDataBuilder）集中构造
- **禁止**：测试连接生产数据库（数据污染与泄露风险）

## 10. 契约测试

- **应该**：跨服务 / 外部 API 边界用契约测试锁定接口契约
- **必须**：公共契约变更跑契约测试回归（联动 `13` 章）
- **禁止**：契约变更无测试保护就上线

## 11. 测试框架

### 11.1 框架对比

| 框架 | 数据驱动 | 并行 | 初始化 | 生态 |
|---|---|---|---|---|
| **xUnit** | `[Theory]` / `[InlineData]` / `[MemberData]` | 内置并行（程序集级） | 无 `[SetUp]`，构造函数即初始化 | 最流行，.NET 生态事实标准 |
| **NUnit** | `[TestCase]` / `[TestCaseSource]` | 受限，需显式配置 | `[SetUp]` / `[TearDown]` | 老牌，特性丰富 |
| **MSTest** | `[DataTestMethod]` / `[DataRow]` | 手动控制 | `[TestInitialize]` / `[TestCleanup]` | Visual Studio 集成好 |

**主要差异**：xUnit 用构造函数做初始化、`IDisposable` 做清理，天然鼓励不可变、可复用的测试实例；NUnit/MSTest 用 `[SetUp]` 特性。并行方面 xUnit 默认并行各测试类，是团队默认推荐。

### 11.2 选型与统一

- **必须**：全仓库统一一种测试框架 + 一种 mock 框架 + 一种断言库，**禁止混用**（框架混用会让新成员无所适从）
- **推荐组合**（新项目默认）：**xUnit + NSubstitute（或 Moq）+ FluentAssertions（或 xUnit 原生断言）**
- **应该**：存量项目若已统一使用其他组合（如 NUnit），不强制迁移——一致性优先于"换新框架"
- **应该**：选定后把框架版本随依赖统一管理（CPM，见 `10` 章），分析器与项目模板一并绑定

## 12. Mock 测试

### 12.1 Mock 框架对比

| 框架 | 语法风格 | 特点 |
|---|---|---|
| **Moq** | `mock.Setup(...).Returns(...)` / `Verify(...)` | 最流行、功能最全；注意较新版本捆绑赞助商组件（有争议） |
| **NSubstitute** | `sub.Returns(...)` / `sub.Received(...)` | 语法简洁直观，无附加组件，社区推荐度上升 |
| **FakeItEasy** | `A.Fake<T>()` / `A.CallTo(...)` | 可读性好 |

三者的能力（设返回值、抛异常、验证调用、参数匹配）等价，选型以团队偏好与许可证考量为准。

### 12.2 通用 mock 规范（呼应第 4 节）

- **必须**：只 mock 被测单元的**外部边界**（I/O、时间、随机、外部服务），不 mock 被测单元自身逻辑
- **必须**：mock 只验证**契约行为**（方法被调用、关键参数、返回值），不验证内部实现细节
- **必须**：mock 的接口 / 抽象是被测单元的依赖，用 DI 注入（联动 `03` 章）
- **应该**：对关键交互用 `Verify` / `Received` 验证，**避免**对每个方法都做过度验证（过度 mock 验证使测试僵化）
- **禁止**：mock 具体类（仅 mock 接口 / 抽象，具体类 mock 行为不可控）

### 12.3 Moq 使用示例

```csharp
// 被测 OrderService 依赖 IOrderRepository 与 IDateTimeProvider（DI 注入）
var repo = new Mock<IOrderRepository>();
var clock = new Mock<IDateTimeProvider>();

// Arrange：设置返回值与参数匹配
clock.Setup(c => c.Now).Returns(new DateTime(2026, 8, 21));
repo.Setup(r => r.Find(It.IsAny<int>())).ReturnsAsync((Order?)null);

var service = new OrderService(repo.Object, clock.Object);

// Act
await service.CreateAsync(42);

// Assert：验证调用次数与关键参数
repo.Verify(r => r.Add(It.Is<Order>(o => o.Amount > 0)), Times.Once);
```

```csharp
// 模拟异常
repo.Setup(r => r.Save(It.IsAny<Order>()))
    .ThrowsAsync(new DbUpdateException("并发冲突"));
```

### 12.4 NSubstitute 使用示例

```csharp
var repo = Substitute.For<IOrderRepository>();
var clock = Substitute.For<IDateTimeProvider>();

// Arrange
clock.Now.Returns(new DateTime(2026, 8, 21));
repo.Find(Arg.Any<int>()).Returns((Order?)null);

var service = new OrderService(repo, clock);

// Act
await service.CreateAsync(42);

// Assert：验证调用次数与关键参数
repo.Received(1).Add(Arg.Is<Order>(o => o.Amount > 0));
```

```csharp
// 模拟异常
repo.Save(Arg.Any<Order>())
    .Returns(x => throw new DbUpdateException("并发冲突"));
```

## 13. 框架快速上手

### 13.1 xUnit

```csharp
public class CalculatorTests
{
    private readonly Calculator _calc = new(); // 构造函数即初始化，无需 SetUp

    [Fact]
    public void Add_TwoNumbers_ReturnsSum()
    {
        // Arrange / Act / Assert 三段式
        Assert.Equal(3, _calc.Add(1, 2));
    }

    [Theory]                       // 数据驱动：一个测试多组输入
    [InlineData(1, 2, 3)]
    [InlineData(-1, 1, 0)]
    public void Add_Parameters_ReturnsExpected(int a, int b, int expected)
        => Assert.Equal(expected, _calc.Add(a, b));

    [Fact]
    public async Task FetchAsync_ReturnsData()      // 异步测试直接 async Task
    {
        var data = await _service.FetchAsync();
        Assert.NotNull(data);
    }
}
```

### 13.2 NUnit

```csharp
[TestFixture]
public class CalculatorTests
{
    private Calculator _calc;

    [SetUp]
    public void SetUp() => _calc = new Calculator();  // 每个测试前执行

    [Test]
    public void Add_TwoNumbers_ReturnsSum()
        => Assert.That(_calc.Add(1, 2), Is.EqualTo(3));

    [TestCase(1, 2, 3)]             // 数据驱动
    [TestCase(-1, 1, 0)]
    public void Add_Parameters_ReturnsExpected(int a, int b, int expected)
        => Assert.That(_calc.Add(a, b), Is.EqualTo(expected));
}
```

### 13.3 MSTest

```csharp
[TestClass]
public class CalculatorTests
{
    [TestMethod]
    public void Add_TwoNumbers_ReturnsSum()
        => Assert.AreEqual(3, new Calculator().Add(1, 2));

    [DataTestMethod]                // 数据驱动
    [DataRow(1, 2, 3)]
    [DataRow(-1, 1, 0)]
    public void Add_Parameters_ReturnsExpected(int a, int b, int expected)
        => Assert.AreEqual(expected, new Calculator().Add(a, b));
}
```

### 13.4 断言库（FluentAssertions 示例）

```csharp
result.Should().Be(3);                                   // 值断言
list.Should().HaveCount(2).And.Contain(o => o.IsActive); // 集合断言
Func<Task> act = () => service.CreateAsync(-1);
await act.Should().ThrowAsync<ArgumentException>();      // 异步异常断言
```

**异步异常断言对照**（团队统一一种即可）：

```csharp
// FluentAssertions
await act.Should().ThrowAsync<ArgumentException>();
// xUnit 原生
await Assert.ThrowsAsync<ArgumentException>(() => service.CreateAsync(-1));
// NUnit
Assert.That(async () => await service.CreateAsync(-1),
            Throws.TypeOf<ArgumentException>());
```

## 14. dotnet test 一键执行

### 14.1 基础命令

| 命令 | 作用 |
|---|---|
| `dotnet test` | 从当前目录向上查找 `.sln`，构建并运行全部测试 |
| `dotnet test <path-to-sln>` | 指定解决方案运行 |
| `dotnet test --project <csproj>` | 只运行指定测试项目 |
| `dotnet test --no-build` | 复用上次构建产物快速重跑（改过被测代码须先 build） |
| `dotnet test -c Release` | 以 Release 配置构建并测试 |

- **必须**：本地开发默认 `dotnet test`（Debug 配置）；CI 用 `-c Release`（联动 `01` 章第 8 节）
- **应该**：未改动被测代码的重复运行加 `--no-build` 提速

### 14.2 过滤测试

- 按完全限定名（`~` 表示"包含"）：`dotnet test --filter "FullyQualifiedName~OrderService"`
- 按特性分类：`dotnet test --filter "Category=Unit"`、`dotnet test --filter "TestCategory!=Slow"`
- 组合过滤：`dotnet test --filter "(FullyQualifiedName~OrderService|Category=Unit)&TestCategory!=Slow"`
- **应该**：慢测试用 `[Trait("Category", "Slow")]`（xUnit）/ `[Category("Slow")]`（NUnit）标记，日常执行按需过滤跳过

### 14.3 覆盖率

```bash
dotnet test --collect:"XPlat Code Coverage"
```

- 生成 cobertura 格式覆盖率报告（输出于 `TestResults/`），需测试项目引用 `coverlet.collector` 包
- **应该**：CI 采集覆盖率并与门禁阈值比对（联动第 8 节覆盖率目标）

### 14.4 CI 一键执行（联动 01 章第 8 节）

```bash
dotnet restore
dotnet build -warnaserror
dotnet test -c Release --collect:"XPlat Code Coverage"
```

### 14.5 常用技巧

- 运行单个测试：`dotnet test --filter "FullyQualifiedName=Namespace.Tests.CalculatorTests.Add_TwoNumbers_ReturnsSum"`
- xUnit 限制并行线程：`dotnet test -- xUnit.MaxParallelThreads=4`（需要时用，配合 `[assembly: CollectionBehavior]` 细化）
- 失败快速回归：修完后 `dotnet test --no-build`，复用上一轮构建产物
```
