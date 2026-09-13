---
type: llm
weight: 1
---

应建议：1) 在 Unloaded 事件中取消订阅所有事件；2) 使用 WeakEventManager 避免强引用；3) 避免订阅 Application.Current 等静态对象的事件（阻止 GC）；4) 实现 IDisposable 模式清理资源
