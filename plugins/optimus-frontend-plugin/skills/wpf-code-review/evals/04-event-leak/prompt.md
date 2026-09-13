---
# max_turns 20 / runs 3 均偏离官方 --bare 模板默认（10 / 未设即 1×CLI 覆盖）：
# 本 case 的判据是付费 llm grader，依据见 spec § 5.9.3 与 § 10 风险 11。
max_turns: 20
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
---

我的 WPF 应用随时间推移内存持续增长，导航页面后旧页面无法被 GC 回收。代码片段：

```csharp
public partial class EmployeePage : UserControl
{
    public EmployeePage()
    {
        InitializeComponent();
        // 订阅 ViewModel 的 CollectionChanged
        ViewModel.Employees.CollectionChanged += OnCollectionChanged;
        // 订阅主窗口的 SizeChanged
        Application.Current.MainWindow.SizeChanged += OnWindowSizeChanged;
    }
    
    private void OnCollectionChanged(object sender, NotifyCollectionChangedEventArgs e)
    {
        UpdateChart();
    }
    
    private void OnWindowSizeChanged(object sender, SizeChangedEventArgs e)
    {
        ResizeContent();
    }
    // 没有任何取消订阅的代码
}
```

如何修复内存泄漏？
