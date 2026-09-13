---
# max_turns 20 / runs 3 均偏离官方 --bare 模板默认（10 / 未设即 1×CLI 覆盖）：
# 本 case 的判据是付费 llm grader，依据见 spec § 5.9.3 与 § 10 风险 11。
max_turns: 20
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
---

我的 WPF ViewModel 中有复杂的 IValueConverter，绑定链层级深，UI 更新时有明显卡顿：

```xml
<!-- 深层属性访问链 -->
<TextBlock Text="{Binding User.Department.Manager.Name, Converter={StaticResource NameFormatter}, Mode=TwoWay}" />

<!-- 绑定到常量属性却用 OneWay -->
<TextBlock Text="{Binding AppVersion}" /> <!-- AppVersion 永不变化 -->

<!-- 只读显示用了 TwoWay -->
<TextBlock Text="{Binding DisplayName, Mode=TwoWay}" />
```

```csharp
public class NameFormatterConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        // 每次绑定刷新都执行昂贵计算
        return FormatNameWithComplexRules(value?.ToString());
    }
}
```

如何优化数据绑定性能？
