# 评估用例：avalonia-wpf-migration

针对一个真实或最小 WPF 项目，验证本 skill 是否先调用 Avalonia Docs MCP 的 `analyze_wpf_project`，在 XPF / 原生 Avalonia 之间设置确认点，并只按需加载官方主题映射；检查它不会在分析前批量改写代码或以“可编译”代替跨平台验收。
