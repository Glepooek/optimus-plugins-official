# known-issues

真实使用中暴露的问题记录。发现当下一行带过即可，不必整理成完整 bug report。"待处理"条目累积满 3 条时，发起一次 darwin-skill 优化循环（须人工在对话中显式发起）。已解决的条目改状态为"已优化"并标注版本号，**不删除**——保留可追溯的问题史。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-13 | **`dsl_to_xaml.py` 把对象类型的 `stroke` / `fontWeight` 直接 `str()` 进 XAML 属性值**，产出形如 `BorderBrush="{'r': 1, 'g': 0.2, ...}"`。以 `{` 开头的属性值会被 WPF 当作 markup extension，**运行时抛解析异常**——产出的页面打不开。原由 `scripts/test_optimization.py` 的 `ValueSafetyTests` 5 条捕获 | 节点带对象类型的 `stroke` 或 `fontWeight`；复现输入 `scripts/assets/invalid-values.json`（已保留） | 待处理 | — |
| 2026-09-13 | **锚点会吞掉子内容**：用注册锚点替换节点时未校验「是否有内容会随之丢失」，带子节点的锚点被整体替换为注册控件，子文本不出现在产出中，且 fallback 报告未记录该节点。原由 `AnchorSafetyTests` 的 3 条捕获（第 4 条叶子锚点用例通过，已保留） | 锚点标记打在有子节点的容器上；复现输入 `scripts/assets/anchor-with-children.json`（已保留，仍被保留的那条测试使用） | 待处理 | — |
| 2026-09-13 | **Grid 定尺把不增长的子元素也判为 star**：期望 2 个 `<ColumnDefinition Width="Auto" />` + 1 个 `Width="*"`，实测 `Auto` 为 **0** 个。原由 `GridSizingTests` 捕获 | 同一 Grid 内混合增长与不增长的子元素；复现输入 `scripts/assets/mixed-grow.json`（已保留） | 待处理 | — |

> 🔴 **三条的共同来路与本文件存在的理由。** 它们随 `de88b9d`（重命名该 skill）入库时即为红，`.github/workflows/ci.yml` 的 `gates-tests` 曾因此**显式排除本目录**——排除而非留红，是因为 `gates-tests` 是必需检查且 ruleset 的 `bypass_actors` 为空，留红会让主干每个 PR 都无法合并。2026-09-13 按用户裁决删除那 9 条测试，目录随之加回 `gates-tests`（裁决记录见 `docs/todo-list/2026-09-12-todo.md` 的 A3）。
>
> ⚠️ **删除测试的同时也删掉了 `ci.yml` 里承载根因分析的那段注释，因此本文件是这三个缺陷在版本库里的唯一记录。** 三条测试的原文可用下面这条命令取回，作为修复后重建行为规格的输入——fixture 都还在原地，重建只需把断言写回来：
>
> ```bash
> git show f149819:plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/scripts/test_optimization.py
> ```
>
> ⚠️ 状态一栏是「待处理」而不是「已优化」：**这次动的是测试，不是实现**。三个缺陷一个都没修。
