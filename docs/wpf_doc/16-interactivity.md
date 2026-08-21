# 16 · XAML Behaviors 与 Interactivity

> 更新历史：2026-08-22 创建。

XAML Behaviors 是 WPF 交互层的可复用逻辑载体——把"控件上的交互行为"（拖拽、验证、点击外部关闭、命令触发）封装为可复用组件，替代 code-behind 里散落的处理器。本篇约束 Behavior / Trigger / Action 的使用边界、编写规范与生命周期。

## 1. 库选型

- **必须**：统一使用 **Microsoft.Xaml.Behaviors.Wpf**（NuGet 包，Blend SDK 后继，社区维护），**禁止**多套 behaviors 库混用
- **禁止**：继续用已停更的 `System.Windows.Interactivity`（旧 Blend SDK，不再维护）
- **应该**：版本随依赖统一管理（联动 `01` 章第 6 节）；升级时核对 API 变更

```xml
<!-- Microsoft.Xaml.Behaviors.Wpf 命名空间声明，Behavior 类名与旧 Blend SDK 不同 -->
xmlns:behaviors="http://schemas.microsoft.com/xaml/behaviors"
```

```csharp
// ✅ 用新库：Behavior<T> 基类在 Microsoft.Xaml.Behaviors 命名空间
using Microsoft.Xaml.Behaviors;
public class ClickToExecuteBehavior : Behavior<Button> { }

// ❌ 旧库：System.Windows.Interactivity.Behavior<T>，已停更，不应再引入
using System.Windows.Interactivity;   // 弃用
```

## 2. 分工：Behavior / 命令 / 附加属性 / code-behind

| 机制 | 适用 |
|---|---|
| **Behavior** | 可复用的交互逻辑（拖拽、点击外部关闭、文本验证提示） |
| **命令绑定** | 有 ViewModel 关联的业务操作（联动 `03` 章） |
| **附加属性** | 给控件附加一个属性 / 轻量状态（联动 `06` 章第 4 节） |
| **code-behind** | 一次性、页面专属的 UI 逻辑（聚焦、窗口行为） |

- **必须**：可复用的交互逻辑封装为 Behavior，**禁止**在多个页面重复粘贴相同事件处理器
- **必须**：涉及业务数据 / 业务操作的交互走命令绑定，**禁止**用 Behavior 触碰 ViewModel 业务逻辑
- **应该**：Behavior 负责"UI 行为"（如何表现），ViewModel 负责"业务逻辑"（做什么）
- **禁止**：用 Behavior 取代命令做业务触发（命令是 ViewModel 的边界）

```csharp
// ❌ 交互逻辑散落各页面：每个窗口重复粘贴拖拽代码，一处改动处处同步
private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    => (sender as Window)?.DragMove();

// ✅ 封装为 Behavior：一处定义，处处复用
public class WindowDragBehavior : Behavior<Window>
{
    protected override void OnAttached()
        => AssociatedObject.MouseLeftButtonDown += OnMouseDown;
    protected override void OnDetaching()
        => AssociatedObject.MouseLeftButtonDown -= OnMouseDown;
    private void OnMouseDown(object sender, MouseButtonEventArgs e)
        => AssociatedObject.DragMove();
}
```

```xml
<Window xmlns:behaviors="http://schemas.microsoft.com/xaml/behaviors">
  <behaviors:Interaction.Behaviors>
    <local:WindowDragBehavior />
  </behaviors:Interaction.Behaviors>
</Window>
```

## 3. Behavior 生命周期

- **必须**：`OnAttached` 中订阅事件 / 初始化，`OnDetaching` 中取消订阅 / 清理——**配对编写**
- **必须**：Behavior 取消订阅的时机覆盖元素卸载（`OnDetaching` 在元素从树移除时触发），**禁止**只订阅不取消（泄漏，联动 `10` 章）
- **禁止**：在 `OnAttached` 中做耗时初始化（阻塞 UI，联动 `09` 章）

```csharp
public class HoverChangeBehavior : Behavior<Border>
{
    protected override void OnAttached()
    {
        base.OnAttached();
        AssociatedObject.MouseEnter += OnEnter;   // 订阅
        AssociatedObject.MouseLeave += OnLeave;
    }
    protected override void OnDetaching()
    {
        AssociatedObject.MouseEnter -= OnEnter;   // 配对取消
        AssociatedObject.MouseLeave -= OnLeave;
        base.OnDetaching();
    }
}
```

## 4. Trigger 与 Action 层级

- **必须**：简单事件响应用 `EventTrigger` + `Action`；复杂交互封装为 Behavior
- **应该**：`InvokeCommandAction` 是命令绑定的补强——控件没有 Command 属性（如 `DragEnter`）时用它转调 ViewModel 命令

```xml
<!-- EventTrigger + InvokeCommandAction：把没有 Command 的事件转调 ViewModel 命令 -->
<behaviors:Interaction.Triggers>
  <behaviors:EventTrigger EventName="DragEnter">
    <behaviors:InvokeCommandAction Command="{Binding DragEnterCommand}" />
  </behaviors:EventTrigger>
</behaviors:Interaction.Triggers>
```

```csharp
// ✅ InvokeCommandAction 让"无命令控件"也能绑定命令，保持 ViewModel 边界
public ICommand DragEnterCommand { get; }
DragEnterCommand = new RelayCommand<DragEventArgs>(OnDragEnter);  // 参数可为事件参数或 CommandParameter
```

- **禁止**：用 `EventTrigger` 做业务事件转发绕过命令（事件名硬编码 + 业务逻辑进 XAML，可维护性差）
- **禁止**：自定义 Trigger 承载业务逻辑（Trigger 只做事件/状态检测，Action 才做事）

## 5. 自定义 Action

- **必须**：需要参数 / 可复用的"动作"（弹提示、改状态）封装为 `Action`，**禁止**在 XAML 触发器内写复杂逻辑
- **必须**：自定义 Action 用 `Execute` 方法承载逻辑，属性声明为依赖属性（支持绑定）
- **禁止**：Action 内执行耗时操作（UI 线程阻塞）；异步动作返回 `Task` 或经 Dispatcher 调度

```csharp
public class ShowMessageAction : TriggerAction<FrameworkElement>
{
    public string Message
    {
        get => (string)GetValue(MessageProperty);
        set => SetValue(MessageProperty, value);
    }
    public static readonly DependencyProperty MessageProperty =
        DependencyProperty.Register(nameof(Message), typeof(string), typeof(ShowMessageAction), null);

    protected override void Invoke(object parameter)
        => MessageBox.Show(Message);   // 轻量动作
}
```

## 6. Behavior 与绑定

- **必须**：Behavior 需要接收外部值时用依赖属性（支持 `{Binding}`），**禁止**普通 CLR 属性
- **必须**：Behavior 内访问 ViewModel 数据经 `AssociatedObject.DataContext` 或依赖属性绑定，**禁止**强类型依赖具体 ViewModel（耦合 + 不可复用）
- **应该**：Behavior 保持与具体类型解耦——操作 `DataContext` 的抽象（接口 / 基类），提升复用

```csharp
// ❌ 强类型依赖具体 ViewModel：Behavior 绑死一个 VM，无法复用
public class SaveOnEnterBehavior : Behavior<TextBox>
{
    protected override void OnAttached()
        => AssociatedObject.KeyDown += (s, e) =>
        {
            if (e.Key == Key.Enter)
                (AssociatedObject.DataContext as LoginViewModel)?.SaveCommand.Execute(null);
        };
}

// ✅ 面向抽象：经接口触发，任何实现接口的 VM 都能用
public interface ISaveCapable { ICommand SaveCommand { get; } }
public class SaveOnEnterBehavior : Behavior<TextBox>
{
    protected override void OnAttached()
        => AssociatedObject.KeyDown += (s, e) =>
        {
            if (e.Key == Key.Enter && AssociatedObject.DataContext is ISaveCapable saveable)
                saveable.SaveCommand.Execute(null);
        };
}
```

## 7. Behavior 与可访问性（联动 `14` 章）

- **必须**：Behavior 改变的交互（拖拽、悬停）提供键盘 / 自动化等价路径，**禁止**仅鼠标手势可操作
- **应该**：Behavior 引发的视觉状态变化配合 `AutomationProperties`，读屏可感知
- **禁止**：Behavior 拦截输入导致键盘用户无法操作（Tab、Enter）

## 8. Behavior 测试（联动 `11` 章）

- **必须**：Behavior 逻辑与 UI 解耦——把行为逻辑抽到可测方法，**禁止**逻辑全部内联在事件处理器
- **必须**：测试注入假控件 / 模拟 `AssociatedObject`，验证 `OnAttached` / `OnDetaching` 的订阅配对
- **应该**：复杂 Behavior 配 UI 自动化测试（FlaUI / White）验证真实交互

```csharp
[Fact]
public void DragBehavior_OnAttached_SubscribesEvent()
{
    var behavior = new WindowDragBehavior();
    var window = new Window();               // 测试用真实 Window 实例
    var attached = behavior.AttachTo(window); // 或经 Interaction.GetBehaviors().Add
    // 验证 OnAttached 订阅了 MouseLeftButtonDown（事件处理非空）

    behavior.Detach();
    // 验证 OnDetaching 取消了订阅（不泄漏）
}
```
