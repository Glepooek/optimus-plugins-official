---
name: dotnet-diagnose-autopilot
description: 给定一份原始 .NET 诊断素材（崩溃日志、内存转储 SOS 输出、!syncblk 输出、dotnet-counters 时间序列），自动识别素材类型、调度 dotnet-diagnose agent 完成分析；若首次结论强度为"推测"，用完全独立的第二次盲态调用做交叉验证；产出含首次/复核/一致性判定/最终建议的结构化报告并落盘。两次结论不一致时并列展示，标记需人工复核，不擅自取舍。触发词：自主分诊、自动分析这份 dump、帮我判断这个根因靠不靠谱、交叉验证一下这个诊断结论、autopilot triage、autonomous .NET diagnosis。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: workflow
compatibility: 需要同一工作树内已安装 optimus-devops-plugin 的 dotnet-diagnose agent 与 dotnet-diagnose-triage skill（本 skill 经 Task 工具调度前者，不直接读取判据）。
allowed-tools: Task Write Read
---

# .NET 自主分诊工作流（盲态双活编排层）

## 概述

**做什么**：给定一份原始诊断素材，自动识别其证据类型，经 `Task` 工具调度 `optimus-devops-plugin:dotnet-diagnose` agent 完成首次分析；若首次结论强度为"推测"，追加一次完全独立、零上下文的第二次分析做交叉验证；把两次结论比对合并，产出结构化报告并落盘。

**不做什么**：不重新判定"征象"（挂起/内存增长/崩溃等症状分类）——那是 `dotnet-diagnose` agent 内部路由的职责；不重新定义结论强度——直接复用 `dotnet-diagnose-triage` 已有的三档（已确认/推测/超出覆盖）；不做知识库判据裁剪——那是 agent 加载 triage 后的职责；不抓取 dump 或采集 trace——素材由用户已经提供。完整职责边界见 `docs/superpowers/specs/2026-09-19-dotnet-diagnose-autopilot-design.md` § 2。

## 主干六步

```
Step 1  素材类型识别，不可用则短路结束
Step 2  首次分析：Task 派发全新、无历史上下文的子任务
Step 3  解析首次结论强度（已确认 / 推测 / 超出覆盖 / 候选集穷尽）
Step 4  置信度分档：仅"推测"触发第二次
Step 5  第二次分析（仅 Step 4 判定触发时执行）：另起一个全新、无上下文的 Task
Step 6  比对两次结论，合成报告并落盘
```

## Step 1：素材类型识别

判定用户给出的原始素材属于哪类证据，不判定"征象"（症状分类留给 agent 内部路由）：

| 素材特征 | 归入证据类型 | 后续路由（由 agent 内部完成） |
|---|---|---|
| 含 `Index`/`SyncBlock`/`MonitorHeld`/`MT`/`Count`/`TotalSize` 等 SOS 命令列名 | 单时点证据（dump/SOS 输出） | agent 加载 triage 后走 `debugging-decision-tree.md` |
| 含托管异常类型 + 堆栈帧（`System.XXXException` + `at ...` 或 `InnerException`） | 崩溃日志 | 走 `evidence-precheck.md`「崩溃日志的定位」一节 |
| 含 counters/trace 时间序列表头（多行采样、时间戳列） | 时间序列证据 | 走 `live-monitoring-decision.md` |
| 三者均不含（纯业务日志、空文本、无异常语义的纯文字） | 不可用 | **不派发**，直接短路报错（见"失败处理"） |

若用户在触发语句中一并给出了症状描述（如"界面卡死"），原样随素材转发；若没给，不替用户猜——交给 `dotnet-diagnose` agent 自行按证据推断征象。

若素材以文件路径给出而非直接粘贴在对话中，用 `Read` 工具读取文件内容后再执行上表判定。
