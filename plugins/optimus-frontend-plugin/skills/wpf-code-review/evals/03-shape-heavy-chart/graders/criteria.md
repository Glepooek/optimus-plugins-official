---
type: llm
weight: 1
---

应建议：1) 使用 DrawingVisual 或 StreamGeometry 替代 Shape 元素；2) 共享 Brush 实例而非每次创建新的；3) 冻结不可变的 Brush；4) 考虑使用 GeometryDrawing 和 DrawingGroup；5) 使用 Path 和 StreamGeometry 绘制所有点和线
