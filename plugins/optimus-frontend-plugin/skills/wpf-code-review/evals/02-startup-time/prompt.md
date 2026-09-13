---
# max_turns 20 / runs 3 均偏离官方 --bare 模板默认（10 / 未设即 1×CLI 覆盖）：
# 本 case 的判据是付费 llm grader，依据见 spec § 5.9.3 与 § 10 风险 11。
max_turns: 20
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
---

我的 WPF 应用启动很慢，大约需要 8-10 秒才能显示主窗口。App.xaml.cs 的启动代码如下：

```csharp
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        
        // 加载所有资源字典
        LoadAllResourceDictionaries();
        
        // 初始化数据库连接
        DatabaseManager.Initialize();
        
        // 加载用户配置
        ConfigManager.LoadConfiguration();
        
        // 预加载所有模块
        ModuleLoader.LoadAllModules();
        
        // 初始化日志系统
        LogManager.Initialize();
        
        // 显示主窗口
        MainWindow mainWindow = new MainWindow();
        mainWindow.Show();
    }
    
    private void LoadAllResourceDictionaries()
    {
        // 加载 50+ 个资源字典
        for (int i = 0; i < 50; i++)
        {
            var dict = new ResourceDictionary();
            dict.Source = new Uri($"Resources/Theme{i}.xaml", UriKind.Relative);
            Resources.MergedDictionaries.Add(dict);
        }
    }
}
```

如何优化启动时间？
