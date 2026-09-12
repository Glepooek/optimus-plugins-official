# add-external-skill · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-12 | 拷贝模式分支自 1.0.0 起从未被真实用例执行过——首批两个目标（archify、ppt-master）都走链接，`external_plugins/` 不会被创建 | — | 待处理 | — |
| 2026-09-12 | `disable-model-invocation: true` 在 Codex 侧的行为**只经文档调研得出，未在真实 Codex 会话中实测**：多个第三方来源（`blog.sandipb.net` 2026-07-15 一文、`mattpocock/skills` 仓库的 `.agents/invocation.md`、`openai/codex` issue #29989 及其评论）一致描述现象为「该字段不生效，skill 仍正常加载进上下文」——即 Codex 忽略该未知顶层键而非硬报错拒绝加载；Codex 用独立的 `agents/openai.yaml`（`policy.allow_implicit_invocation: false`）承载同类策略。未找到任何关于 Codex 严格校验 SKILL.md frontmatter 并拒绝未知顶层键的记载。**这是文档调研结论，不是在本环境或任何真实 Codex CLI 会话里触发本 skill 观察到的实测结果**，风险仍然是：若实际行为与调研结论不符（即真实硬报错），本 skill 会在 Codex 侧整体加载失败，而镜像正是为 Codex 建的。**⚠️ 若日后一次真实 Codex 会话触发本 skill 并观察到硬报错/拒绝加载，不要自行删掉该字段或改用别的约束方式——停下来报告，该字段与 Codex 镜像不可兼得需要重新裁决（保字段舍 Codex 镜像，或保镜像改用别的方式约束触发）** | 在 Codex 中触发同名 skill | 待验证（非实测） | — |
| 2026-09-12 | 变更摘要在非 GitHub 上游上无成熟取法（compare API 绑定 GitHub，临时浅克隆要落盘）。首批目标都在 GitHub，首次引入非 GitHub 上游时须补 | 更新一个非 GitHub 上游的条目 | 待处理 | — |
| 2026-09-12 | 接入 `archify` 时，Step 6（安装验证：`claude plugin marketplace update` + `claude plugin install`）按控制器/用户决策未在本次自动化执行中运行——理由是该操作会向用户全局 Claude Code 环境安装一个具备任意代码执行能力的第三方插件，不应由自动化派发代为决定。已用 `python .githooks/check_external_entries.py .`（仅结构校验，不联网、不安装）替代，并独立复核了 sha。**需人工手动执行 `claude plugin marketplace update optimus-plugins-official && claude plugin install archify@optimus-plugins-official`，确认 archify 的 skill 能在列表中列出后，才能视本条目为完全验证** | 首次接入 archify | 待处理 | — |
