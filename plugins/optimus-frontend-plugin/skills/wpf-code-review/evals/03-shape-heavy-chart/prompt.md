---
# max_turns 20 / runs 3 均偏离官方 --bare 模板默认（10 / 未设即 1×CLI 覆盖）：
# 本 case 的判据是付费 llm grader，依据见 spec § 5.9.3 与 § 10 风险 11。
max_turns: 20
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
---

我在绘制一个复杂的图表，使用了大量的 Shape 元素，但渲染性能很差。代码片段：

```xml
<Canvas x:Name="ChartCanvas" Width="800" Height="600">
    <!-- 绘制 1000+ 个数据点 -->
    <Ellipse Canvas.Left="10" Canvas.Top="100" Width="5" Height="5" Fill="Blue" />
    <!-- ... 更多 Ellipse ... -->
</Canvas>
```

后台代码动态创建这些元素：
```csharp
private void DrawChart()
{
    ChartCanvas.Children.Clear();
    
    for (int i = 0; i < dataPoints.Count; i++)
    {
        var ellipse = new Ellipse
        {
            Width = 5,
            Height = 5,
            Fill = new SolidColorBrush(Colors.Blue)
        };
        Canvas.SetLeft(ellipse, dataPoints[i].X);
        Canvas.SetTop(ellipse, dataPoints[i].Y);
        ChartCanvas.Children.Add(ellipse);
        
        if (i > 0)
        {
            var line = new Line
            {
                X1 = dataPoints[i-1].X,
                Y1 = dataPoints[i-1].Y,
                X2 = dataPoints[i].X,
                Y2 = dataPoints[i].Y,
                Stroke = new SolidColorBrush(Colors.Red),
                StrokeThickness = 1
            };
            ChartCanvas.Children.Add(line);
        }
    }
}
```

如何优化渲染性能？
