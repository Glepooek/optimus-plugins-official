---
name: avalonia-code-review-compiled-binding-and-styles
description: Review a narrow Avalonia AXAML sample for framework-specific correctness.
plugins:
  - optimus-avalonia-plugin
runs: 1
max_turns: 12
allowed_tools: [Read, Glob, Grep, avalonia-docs]
---

请审查以下 `Views/SearchView.axaml`。只审查这段代码，不要扩大到整个项目；对每项发现通过 Avalonia Docs MCP 核验，并给出严重度、官方依据、修正代码和未验证项。

```xml
<UserControl xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             x:Class="Sample.Views.SearchView">
  <UserControl.Styles>
    <Style TargetType="Button">
      <Style.Triggers>
        <Trigger Property="IsMouseOver" Value="True">
          <Setter Property="Background" Value="LightBlue" />
        </Trigger>
      </Style.Triggers>
    </Style>
  </UserControl.Styles>
  <StackPanel>
    <TextBox Text="{Binding Query}" />
    <TextBlock Text="{Binding ResultCount}" />
  </StackPanel>
</UserControl>
```
