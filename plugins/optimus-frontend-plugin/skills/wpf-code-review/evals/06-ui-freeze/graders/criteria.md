---
type: llm
weight: 1
---

应建议：1) 使用 async/await + Task.Run 将耗时操作移到后台线程；2) 用 Dispatcher.InvokeAsync 替代 Dispatcher.Invoke 避免死锁；3) 使用 IProgress<T> 报告后台进度；4) 添加 CancellationToken 支持取消操作
