# dotnet-diagnose-autopilot · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

## darwin-skill 基线评估（2026-09-19）

Task 1-9 完成后完整 SKILL.md（170 行）的首次基线评估，无历史分可比，只建基线不做棘轮比较。

| 项 | 值 |
|---|---|
| 总分 | **74.3** |
| 评估模式 | `dry_run` — Task 8 的 eval case 因缺 `ANTHROPIC_API_KEY` 在 CI 里跑不了（与 `wpf-code-review` 六个 case 同样的已知限制），dim8 靠人工干跑（读完 skill 模拟一次典型 prompt 的执行思路）而非真实调用验证 |
| 结构组（dim1-6） | 48.4 |
| 效果组（dim7-8） | 22.3 |
| 元技能（dim9） | 3.6 |
| 判读 | 新建 skill 基线，无历史分可比。后续 Minor/Major 升级须 **≥ 74.3**，倒退则先修正 |

| # | 维度 | 权重 | 分 | 折算 | 评分依据 |
|---|---|---:|---:|---:|---|
| 1 | frontmatter 质量 | 7 | 9 | 6.3 | 五字段合规；description 285 字，含时机边界（"若首次结论强度为推测"）+ 6 个触发词 + compatibility 说明依赖 agent；无结尾空话尾巴 |
| 2 | 工作流清晰度 | 12 | 9 | 10.8 | "主干六步"编号清晰、每步输入输出明确；执行前置校验独立成节。扣分：Step2 与 Step5 的 dispatch prompt 模板完全重复（有意为之，但仍占篇幅） |
| 3 | 失败模式编码 | 12 | 9 | 10.8 | 失败处理表五种情形全为"若 X 则 Y"形态，含"仅症状描述无结论"等细腻边缘情形；前置校验类别 1/2 另有硬约束终止 |
| 4 | 检查点设计 | 6 | **4** | 2.4 | ★**唯一明显短板**：全篇三处 🔴 标记全部用于**标记结果**（"需人工复核"），不是执行流程**中途**暂停询问用户——素材不可用/agent 不可用均为自动短路而非询问，比 `dotnet-diagnose-triage` 基线（dim4=5，至少有自检四项等天然人审关口）更彻底地缺失检查点 |
| 5 | 可执行具体性 | 17 | 9 | 15.3 | dispatch prompt 模板逐字给出；四态判定关键字明确；落盘路径与 timestamp 格式固定；报告骨架具体。软化措辞扫描 0 处真实命中 |
| 6 | 资源整合度 | 4 | 7 | 2.8 | 无 `references/` 子目录（规则全部内联，规模合理故未下钻）；compatibility 字段依赖关系清楚；已引用的两处外部路径（`docs/superpowers/specs/...design.md`、`knowledge-base/dotnet-debugging/rules/01-dump-handling.md`）经核验均可达 |
| 7 | 整体架构 | 12 | 9 | 10.8 | 与 agent/triage 边界清晰（"不做什么"一节明确列出四类不做的事）；结构层次分明、无 AI 腔废话词汇；Step2/Step5 模板重复已用 ⚠️ 说明是盲态设计的有意为之，不计冗余 |
| 8 | 实测表现 | 23 | 5 | 11.5 | `dry_run`：人工干跑模拟"给一份含 `MonitorHeld` 列的 `!syncblk` 输出"典型 prompt，六步流程走通、无逻辑漏洞，但**无任何真实 Task 调用证据**——比 `dotnet-diagnose-triage` 基线的 `full_test (partial)`（好歹有七例真实调用）更弱，故明显低于其 dim8=9 |
| 9 | 反例与黑名单 | 6 | 6 | 3.6 | 概述节"不做什么"四条 + Step6 比对规则"不擅自取舍、不加权投票、不选更详细的那份"，但**未设独立的反例/黑名单章节**，反例散落在概述与业务规则中而非单列 |

权重合计 99（darwin 自身缺陷，非本仓评分误差，本仓 `results.tsv` 历史记录已多次复现）。

**下一轮优化的首选靶点**：dim4（权重 6，现 4 分，九维最低）。给 Step1"素材不可用短路"、Step2/5"Task 调用失败"、Step6"结论不一致"三处补显性 `🔴 CHECKPOINT` 标记（HL-1 手法），预期 dim4 4→8、总分 74.3→**76.7**。次选靶点 dim9（权重 6，现 6 分）：将概述节"不做什么"与 Step6 禁止句合并为独立的"反例与边界"章节。

⚠️ `dry_run` 模式的分数**上限受限**（按 darwin-skill 本体规则），尤其 dim8——一旦具备 `ANTHROPIC_API_KEY` 补跑 Task 8 的 eval case 做 full_test，本次基线分不可直接沿用，须重记评估模式。

## 待处理问题

（暂无）
