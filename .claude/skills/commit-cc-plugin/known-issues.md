# commit-cc-plugin · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-08 | 第二步 CHECKPOINT 只覆盖「版本号写错」一类失败，但 `check_plugin_versions.py` 实际有四种失败模式，其中「有多余字段」（白名单校验）撞上时 CHECKPOINT 的处置指引（"回头判断该升什么号"）完全不适用。根因与 2026-09-07 那条同类——**流程内两处规定的前提互相矛盾**：门禁白名单 `{name,version,agents}` 建立在「description 等已在 marketplace 条目声明」这一前提上，而该前提经实测被推翻（已安装插件的描述渲染只读 `manifest.description`，不回退 marketplace 条目），于是「遵守门禁」与「修好 bug」不可兼得。危险的绕开方式是删掉字段让门禁通过（等于放弃修复）或只改脚本不改测试（等于让门禁失效）；正确做法是判断字段有无独立消费方，有则连同测试一起放宽白名单并记录 | 修复 /plugin 界面插件描述空白（commit 3f98739）时，给 9 份 `.claude-plugin/plugin.json` 补 description 等字段，第二步门禁以「有多余字段」阻断 | 已优化 | 3.7.0 |
| 2026-09-07 | 第六步 `git pull --rebase origin master` 在工作区存在未暂存改动时直接失败（exit 128，`cannot pull with rebase: You have unstaged changes`），第六步的兜底只列了「rebase 冲突」与「push 失败」两种，未覆盖此场景。根因是流程隐含假设「提交后工作区即干净」，但第一步 CHECKPOINT 明确允许把无关改动排除在本次提交外——**两步的前提互相矛盾**：越是按第一步规范排除了无关文件，越必然在第六步撞上这个失败。绕开它的错误做法是把无关文件一并提交（破坏第三步刚校验过的原子性）；正确做法是 `git stash push <file>` 只挪走无关文件，push 后 `git stash pop` 原样恢复 | 提交 sync-cc-tips 2.0.0 时按要求排除会话前遗留的 `docs/claude_blog/*.md`，第六步 rebase 被该文件挡住 | 已优化 | 4.0.0 |
| 2026-09-08 | skill 职责不单一：除「提交」本身外，还承担了插件版本一致性校验与 `.kiro`/`.agents` 符号链接镜像维护两项**仓库长期一致性**门禁，SKILL.md 达 278 行、4 个 CHECKPOINT，其中第二步甚至内含「门禁白名单过时了怎么改门禁自身」的元流程。根因是拦截点便利性驱动的耦合——提交是每次改动的必经关口，什么检查都想挂上去。真正的代价有二：① 门禁靠 LLM 读 SKILL.md 自觉执行，而 AGENTS.md 明写 Codex 侧走标准 git，**这两个门禁在 Codex 下从来没生效过**；② §A 有 GATE 保护、执行频率极低，其内部「未排除 gitignore 目录」的缺陷（误报 `darwin-skill` 缺失）长期无人发现——低频执行的检查等于未经测试的检查 | 用户指出「该 skill 职责不单一，它就是单纯提交修改内容」 | 已优化 | 4.0.0 |
