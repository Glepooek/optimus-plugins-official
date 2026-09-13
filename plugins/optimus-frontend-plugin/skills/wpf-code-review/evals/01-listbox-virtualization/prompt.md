---
# max_turns 20 / runs 3 均偏离官方 --bare 模板默认（10 / 未设即 1×CLI 覆盖）：
# 本 case 的判据是付费 llm grader，依据见 spec § 5.9.3 与 § 10 风险 11。
max_turns: 20
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
---

我有一个 WPF 应用，MainWindow.xaml 中有一个显示 5000 条员工记录的 ListBox，滚动时非常卡顿。代码如下：

```xml
<Window x:Class="EmployeeApp.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Employee List" Height="600" Width="800">
    <Grid>
        <ListBox x:Name="EmployeeListBox" 
                 ItemsSource="{Binding Employees}"
                 ScrollViewer.CanContentScroll="False">
            <ListBox.ItemsPanel>
                <ItemsPanelTemplate>
                    <StackPanel />
                </ItemsPanelTemplate>
            </ListBox.ItemsPanel>
            <ListBox.ItemTemplate>
                <DataTemplate>
                    <Grid>
                        <Grid.RowDefinitions>
                            <RowDefinition />
                            <RowDefinition />
                        </Grid.RowDefinitions>
                        <TextBlock Grid.Row="0" Text="{Binding Name}" />
                        <TextBlock Grid.Row="1" Text="{Binding Department}" />
                    </Grid>
                </DataTemplate>
            </ListBox.ItemTemplate>
        </ListBox>
    </Grid>
</Window>
```

ViewModel 代码：
```csharp
public class MainViewModel
{
    public List<Employee> Employees { get; set; }
    
    public MainViewModel()
    {
        Employees = LoadEmployees(); // 加载 5000 条记录
    }
}
```

请帮我分析性能问题并提供优化建议。
