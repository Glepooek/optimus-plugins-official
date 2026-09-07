# commit-cc-plugin · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-07 | 第六步 `git pull --rebase origin master` 在工作区存在未暂存改动时直接失败（exit 128，`cannot pull with rebase: You have unstaged changes`），第六步的兜底只列了「rebase 冲突」与「push 失败」两种，未覆盖此场景。根因是流程隐含假设「提交后工作区即干净」，但第一步 CHECKPOINT 明确允许把无关改动排除在本次提交外——**两步的前提互相矛盾**：越是按第一步规范排除了无关文件，越必然在第六步撞上这个失败。绕开它的错误做法是把无关文件一并提交（破坏第三步刚校验过的原子性）；正确做法是 `git stash push <file>` 只挪走无关文件，push 后 `git stash pop` 原样恢复 | 提交 sync-cc-tips 2.0.0 时按要求排除会话前遗留的 `docs/claude_blog/*.md`，第六步 rebase 被该文件挡住 | 待处理 | - |
