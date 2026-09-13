---
# max_turns 20 / runs 3 均偏离官方 --bare 模板默认（10 / 未设即 1×CLI 覆盖）：
# 本 case 的判据是付费 llm grader，依据见 spec § 5.9.3 与 § 10 风险 11。
max_turns: 20
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
---

我的 WPF 应用点击按钮加载数据时 UI 完全冻结 5-10 秒，同时另一处后台线程更新状态时使用了同步 Invoke：

```csharp
private void LoadDataButton_Click(object sender, RoutedEventArgs e)
{
    // 在 UI 线程同步执行耗时操作
    var data = DataService.LoadLargeDataset(); // 耗时 5-8 秒
    ProcessData(data);                          // 耗时 1-2 秒
    DataGrid.ItemsSource = data;
    StatusLabel.Content = "加载完成";
}

private void UpdateStatusFromBackground(string message)
{
    // 后台线程调用同步 Invoke（有死锁风险）
    Application.Current.Dispatcher.Invoke(() =>
    {
        StatusLabel.Content = message;
    });
}
```

如何让 UI 保持响应？
