# 03 · MVVM 架构

> 更新历史：2026-08-21 创建。

MVVM 是 WPF 的默认架构形态。本篇约束框架选型、View/ViewModel 边界、命令与导航。MVVM 框架选型与 `wpf-project-conventions` skill 第 1 节互为事实来源。

## 1. MVVM 框架选型

| 框架 | 基类 / 命令 | 特点 | 适用 |
|---|---|---|---|
| **Prism** | `BindableBase` / `DelegateCommand` | 模块化、导航、区域（Region）、DI 深度集成 | 大型多模块应用 |
| **CommunityToolkit.Mvvm** | `ObservableObject` / `RelayCommand`（源生成器） | 轻量、无强约束、源生成器减少样板 | 中小型、追求简洁 |
| **原生 MVVM** | 自写 `INotifyPropertyChanged` + `ICommand` | 零依赖、完全可控 | 极简应用 / 教学 |
| 其他（MVVMLight 等） | — | 社区库，注意维护状态 | 存量项目 |

- **必须**：全仓库统一一种 MVVM 框架，**禁止**混用（Prism + Toolkit 混用会导致基类与命令混乱）
- **推荐**：新项目默认 **Prism**（若需模块化 / 导航）或 **CommunityToolkit.Mvvm**（若需求简洁）；存量项目已统一框架的不强制迁移
- **应该**：框架版本随依赖统一管理，升级框架时同步核对基类与命令 API 变更

## 2. ViewModel 基类与可绑定属性

- **必须**：ViewModel 继承团队选定的基类（`BindableBase` / `ObservableObject`），实现 `INotifyPropertyChanged`
- **必须**：可绑定属性用属性设置器触发变更通知，**禁止**直接操作公共字段
- **必须**：属性变更通知写法统一（`SetProperty` / `SetObservableProperty`），不手写样板 `if (field != value)` 重复块
- **禁止**：在 ViewModel 中声明 UI 类型（`Brush`、`Visibility` 用 `bool` 或枚举表达，由 Converter 转换，联动 `05` 章）

```csharp
// ❌ 手写样板：每个属性重复 if-赋值-通知，易漏、难维护
public class LoginViewModel
{
    private string _userName;
    public string UserName
    {
        get => _userName;
        set { if (_userName != value) { _userName = value; OnPropertyChanged(); } }
    }
}

// ✅ SetProperty 统一模板：一行搞定"比较+赋值+通知"
public class LoginViewModel : ObservableObject
{
    private string _userName;
    public string UserName { get => _userName; set => SetProperty(ref _userName, value); }
}
```

```csharp
// ❌ ViewModel 声明 UI 类型：View 耦合 VM，VM 无法脱离 UI 测试
public class LoginViewModel
{
    public Brush StatusColor { get; set; }          // UI 类型泄漏进 VM
    public Visibility ErrorVisibility { get; set; }
}

// ✅ 用数据表达状态，由 View 层 Converter 转 UI 类型
public class LoginViewModel
{
    public bool HasError { get; set; }              // 纯数据，可测试
}
<!-- View 侧：bool → Visibility 由 Converter 完成 -->
<TextBlock Visibility="{Binding HasError, Converter={StaticResource BoolToVisibilityConverter}}" />
```
- **应该**：ViewModel 无参构造友好——依赖经构造函数注入，便于测试与设计期数据（联动 `11` 章）

## 3. 命令（ICommand）

- **必须**：操作一律走 `ICommand`（`DelegateCommand` / `RelayCommand`），**禁止**在 code-behind 里直接实现业务操作
- **必须**：命令定义携带 `CanExecute`，执行状态随属性变更自动刷新（`RaiseCanExecuteChanged`）
- **应该**：命令构造用框架提供的强类型命令，减少自写 `ICommand`
- **禁止**：命令体内吞异常（联动 `12` 章）；长时间操作命令内做异步并禁用期间交互

```csharp
// ❌ 无 CanExecute：按钮永远可点，空提交 / 重复提交
public ICommand SaveCommand { get; }
public LoginViewModel() => SaveCommand = new RelayCommand(_ => Save(), _ => true);

// ✅ CanExecute 联动：输入为空时按钮禁用，输入变化时刷新状态
public ICommand SaveCommand { get; }
public LoginViewModel()
{
    SaveCommand = new RelayCommand(Save, CanSave);
}
private bool CanSave(object _) => !string.IsNullOrWhiteSpace(UserName) && !IsSaving;
private void Save() { IsSaving = true; /* ... */ }
// 在 UserName / IsSaving 的 setter 中调用 (SaveCommand as RelayCommand)?.RaiseCanExecuteChanged();
```

## 4. View 与 ViewModel 配对

- **必须**：View 与 ViewModel 一一对应，`DataContext` 赋值统一路径（构造注入、`DataContext` 定位器、`ViewModelLocator`）
- **必须**：View 通过 `{Binding}` 消费 ViewModel 公开属性，**禁止** View 直接访问 ViewModel 私有状态
- **禁止**：ViewModel 反向持有 View 引用（破坏可测性与解耦）
- **应该**：用视图定位器（如 `prism:ViewModelLocator`）按约定自动绑定 `DataContext`，减少手工 `new VM()` 样板
- **禁止**：在 `View` 的 XAML 中 `new` ViewModel（`<DataContext><local:VM/></DataContext>` 例外场景需 review）

## 5. 依赖注入与组合根

- **必须**：服务 / 仓储 / ViewModel 经 DI 容器解析，`App.xaml.cs` 的 `OnStartup`（或 Prism 容器）是组合根
- **必须**：ViewModel 依赖通过构造函数注入接口，**禁止** ServiceLocator 反模式（到处 `container.Resolve<T>()`）
- **应该**：生命周期管理——单例服务（全局状态）/ Transient（每请求）按职责选择
- **禁止**：静态服务（静态 `Current` 单例）承载可变业务状态（联动 `13` 章相关约束）

## 6. 导航与页面管理

- **必须**：多页面应用导航统一走框架导航（Prism `INavigationService` / 自建导航服务），**禁止**每个页面各自 `new Window()` 打开并自行管理
- **应该**：导航参数用框架导航参数机制传递，ViewModel 通过 `INavigationAware` / `OnNavigatedTo` 接收

```csharp
// ❌ 各自 new Window：窗口生命周期失控，无法导航回退、参数传递散乱
private void OpenDetail_Click(object sender, RoutedEventArgs e)
{
    var win = new DetailWindow();      // code-behind 直接建窗口
    win.Owner = Application.Current.MainWindow;
    win.Show();
}

// ✅ 框架导航：导航服务统一管理，参数强类型传递
private void OpenDetail(Order order)
{
    var navParams = new NavigationParameters { { "orderId", order.Id } };
    _navigationService.RequestNavigate("DetailPage", navParams);   // Prism
}
// DetailViewModel 接收参数
public void OnNavigatedTo(NavigationContext ctx)
    => _orderId = ctx.Parameters.GetValue<int>("orderId");
```
- **应该**：页面生命周期（进入 / 退出、数据加载 / 释放）统一在导航钩子中处理，不散落 code-behind
- **禁止**：导航到已销毁页面持有悬挂引用（联动 `10` 章内存泄漏）

## 7. 事件与订阅

- **必须**：跨 ViewModel / 服务通信用框架事件聚合器（Prism `IEventAggregator`）或弱事件机制
- **必须**：订阅事件必须配对取消订阅（View 卸载 / ViewModel 销毁时），**禁止**泄漏订阅（联动 `10` 章）
- **禁止**：用静态事件 / 全局事件中转业务数据（难追踪、易泄漏）

## 8. 可测性（联动 `11` 章）

- **必须**：ViewModel 依赖均为接口（可 mock），业务逻辑不在 code-behind
- **必须**：命令与属性行为可独立测试（`CanExecute` → `Execute` 状态机）
- **应该**：导航、消息、日志等框架依赖抽象成接口，测试注入假实现
