# 11 · 测试

> 更新历史：2026-08-21 创建。

WPF 测试分三层：ViewModel 单元测试（多、快）、集成测试（真实协作）、UI 自动化测试（少、慢）。测试框架与断言库团队统一，通用测试策略沿用团队约定，本篇聚焦 WPF 特有测试问题。

## 1. 测试分层

- **必须**：测试分层——ViewModel/服务单元测试（多、快）→ 集成测试（真实协作）→ UI 自动化测试（少、慢）
- **必须**：新功能配测试；修复 bug 先写能复现的测试再修
- **禁止**：只有 UI 自动化测试没有单元测试（慢、脆、故障难以定位）
- **应该**：UI 自动化只覆盖关键用户路径，普通逻辑下沉到单元 / 集成

## 2. 测试结构

- **必须**：测试项目命名 `<被测>.Tests`，目录镜像源码结构
- **必须**：被测类 `UserManager` 对应测试类 `UserManagerTests`
- **禁止**：测试项目引用 UI 项目中的 `App.xaml` / 资源（测 ViewModel 不需要 UI 上下文）

## 3. ViewModel 单元测试

- **必须**：ViewModel 依赖为接口（DI 注入），mock 外部边界（I/O、服务、时间），**禁止** mock 被测单元自身逻辑
- **必须**：命令测试——`CanExecute` → `Execute` → 状态断言（属性、集合、导航调用）
- **必须**：异步命令测试 `await` 完成，**禁止** `.Result` / `.Wait()` 同步等待（死锁，联动 `09` 章）
- **应该**：`INotifyPropertyChanged` 变更断言（`PropertyChanged` 事件触发、触发属性名正确）
- **禁止**：ViewModel 依赖具体 UI 类型（`Brush`、`Dispatcher` 直接使用），否则不可测（联动 `03` 章第 2 节）

### 示例：属性变更与命令

```csharp
[Fact]
public async Task SaveCommand_WhenValid_InvokesRepositoryAndRaisesPropertyChanged()
{
    // Arrange
    var repo = Substitute.For<IOrderRepository>();
    var vm = new OrderViewModel(repo) { Amount = 42 };
    var raised = false;
    vm.PropertyChanged += (_, e) => { if (e.PropertyName == nameof(vm.IsSaving)) raised = true; };

    // Act
    await vm.SaveCommand.ExecuteAsync(null);

    // Assert
    await repo.Received(1).Save(Arg.Is<Order>(o => o.Amount == 42));
    Assert.True(raised);
}
```

## 4. 测试 UI 线程

- **必须**：ViewModel 单元测试不依赖真实 UI 线程（纯逻辑可测），涉及 `Dispatcher` 时注入调度接口
- **必须**：测试中创建 `Dispatcher` 上下文用测试框架支持（`[StaThread]` 测试线程 或 调度器封装），**禁止**测试依赖 `Application.Current.Dispatcher`（无 Application 时抛异常）
- **应该**：需要 UI 上下文的测试项目设置 `<UseWPF>true</UseWPF>` 并在 STA 线程运行（`[StaFact]` / `[Apartment(ApartmentState.STA)]`）
- **禁止**：单元测试中启动真实窗口（属 UI 自动化测试范畴）

```csharp
// ❌ 测试直接依赖 Application.Current.Dispatcher：测试进程无 WPF Application 实例，抛异常
[Fact]
public void Update_WithValidData_UpdatesStatus()
{
    var vm = new OrderViewModel();
    Application.Current.Dispatcher.Invoke(() => vm.Update());   // NullReferenceException

    Assert.Equal("已更新", vm.Status);
}

// ✅ 依赖注入调度接口：测试注入假调度器，生产注入真 Dispatcher
public interface IDispatcher { void Invoke(Action action); }

[Fact]
public void Update_WithValidData_UpdatesStatus()
{
    var vm = new OrderViewModel(new FakeDispatcher());   // 假调度：同步执行
    vm.Update();

    Assert.Equal("已更新", vm.Status);
}
```

## 5. UI 自动化测试

- **必须**：关键用户路径配 UI 自动化测试（登录、主流程、关键交互）
- **必须**：UI 测试框架团队统一（**FlaUI** / **White** 二选一），**禁止**混用
- **必须**：UI 测试元素定位用稳定标识（`AutomationId`，联动 `04` 章第 10 节、`14` 章），**禁止**按坐标 / 文本脆弱定位
- **应该**：UI 测试独立于单元测试运行（慢、脆），CI 单独阶段或独立任务
- **禁止**：UI 测试依赖真实网络 / 数据库（用桩 / 假服务，保持确定性）

```csharp
// FlaUI 示例：稳定定位 + 显式等待
using var app = Application.Launch("App.exe");
using var window = app.GetMainWindow(new UIA3Automation());
var loginBtn = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginButton")).AsButton();
var wait = new WaitHelpers(window);
Assert.True(wait.WaitUntil(() => loginBtn.IsEnabled));
loginBtn.Click();
```

## 6. XAML / 资源验证

- **必须**：XAML 编译（BAML）通过（构建期），**禁止**运行期才暴露 XAML 解析错误
- **必须**：资源字典合并验证——`App.xaml` 合并清单与资源键不冲突（联动 `02` 章第 2 节）
- **应该**：静态分析资源引用（`StaticResource` 找不到的 key 在构建期排查）
- **禁止**：测试依赖设计器生成代码（`InitializeComponent` 生成的字段仅由框架管理）

## 7. 集成测试

- **必须**：集成测试验证真实协作（DB、HTTP、消息中间件），运行在可控环境（Testcontainers、本地实例）
- **禁止**：集成测试连生产资源；**禁止**写成本地慢速 E2E
- **应该**：WPF 集成测试重点验证 ViewModel ↔ 服务 ↔ 持久化链路，UI 层由自动化测试覆盖

## 8. 覆盖率

- **应该**：覆盖率目标（行覆盖 ≥ 70%，关键路径 ≥ 80%），按模块而非总量考核
- **禁止**：把覆盖率当唯一标准——无断言覆盖是假质量
- **应该**：金额、安全、并发等高风险领域提高覆盖率要求
- **禁止**：为凑覆盖率写无效断言

## 9. 测试数据与确定性

- **必须**：测试数据自包含（工厂 / 构建器），**禁止**依赖生产数据
- **必须**：测试确定性——固定输入 / 注入时钟，**禁止**随机性 / 时间依赖
- **应该**：UI 测试截图 / 日志留存便于失败定位（WPF 渲染问题截图比日志直观）

## 10. 测试执行

- **必须**：测试框架与断言库团队统一（联动团队测试约定）
- **应该**：UI 测试在 CI 用独立任务（不拖慢单元测试主流程）
- **禁止**：测试对执行顺序有依赖（每个测试独立可重复）
