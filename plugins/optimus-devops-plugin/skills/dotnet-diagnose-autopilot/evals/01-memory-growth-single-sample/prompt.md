---
max_turns: 20
runs: 1
allowed_tools: [Task, Write, Read]
---

我这边一个 WPF 应用内存一直在涨，抓了一次 !dumpheap -stat（进程已经退出，没法再抓第二次了）：

```
              MT    Count    TotalSize Class Name
00007ffa1c3d4210  1847293    206896816 MyApp.Models.OrderItem
00007ffa1b9a1188   412887      3303100 System.String
00007ffa1b9c2340    98211      1257008 System.Object[]
00007ffa1c3d5998     8291       663280 System.Collections.Generic.List`1[[MyApp.Models.OrderItem, MyApp]]
00007ffa1b9a0d10     2104        10192 Free
Total 2368986 objects
```

帮我自动分诊一下，判断根因，如果把握不大就交叉验证一下再告诉我结论。
