---
type: llm
weight: 1
---

应识别出：1) ScrollViewer.CanContentScroll="False" 禁用了虚拟化；2) 使用 List 而非 ObservableCollection；3) 未启用容器回收；4) ItemTemplate 中使用 Grid 可以简化为 StackPanel
