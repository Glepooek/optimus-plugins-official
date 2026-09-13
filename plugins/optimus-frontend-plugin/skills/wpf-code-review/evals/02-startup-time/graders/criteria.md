---
type: llm
weight: 1
---

应建议：1) 添加启动画面改善感知时间；2) 延迟非关键初始化（ModuleLoader, LogManager）到窗口显示后；3) 按需加载资源字典而非全部加载；4) 考虑使用 Ngen.exe；5) 异步初始化数据库连接
