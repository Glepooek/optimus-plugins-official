---
type: llm
weight: 1
---

应建议：1) 用 OneTime 绑定替换永不变化的常量属性（AppVersion）；2) 只读显示属性使用 OneWay 而非 TwoWay；3) 避免超过 3 层深的属性访问链，在 ViewModel 中暴露扁平属性；4) 昂贵转换器使用缓存或 Memoization
