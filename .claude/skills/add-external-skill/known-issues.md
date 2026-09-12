# add-external-skill · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

> 注：下表 archify、ppt-master 两行记录的是**待人工完成的安装验证动作**，不是本 skill 的行为缺陷——按控制器/用户决策，写入 marketplace 会执行任意代码的插件安装步骤不由自动化代为决定。这两行计入「待处理」计数是如实反映当前状态，但复核 3 条阈值触发 darwin-skill 优化循环时，不应把它们误读为「skill 该改」的信号。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-12 | 拷贝模式分支自 1.0.0 起从未被真实用例执行过——首批两个目标（archify、ppt-master）都走链接，`external_plugins/` 不会被创建 | — | 待处理 | — |
| 2026-09-12 | `disable-model-invocation: true` 在 Codex 侧的行为**已实测确认为「忽略未知顶层键、skill 仍正常加载」，不是硬报错**。取证：codex-cli 0.154.0，`CODEX_HOME=<系统临时目录> codex debug prompt-input`（渲染模型可见 prompt，不发起 API 调用、不动用户全局配置）。观察到：退出码 0；本 skill 以 `add-external-skill: <description> (file: r3/add-external-skill/SKILL.md)` 形式出现在模型可见的 skill 清单里（`r3` = 本仓 `.agents/skills`，即为 Codex 建的镜像目录），与其他 skill 呈现方式无差别；模型可见文本中无 `Unexpected` / `unknown` / `invalid` / `warn` 任何字样，`disable-model-invocation` 本身出现 0 次（Codex 只取 `name` + `description`，不透传该字段）。**结论：该字段与 Codex 镜像可以兼得，无需重新裁决。** 残留的非对称：该字段在 Codex 侧不生效（字段未进入模型可见上下文，模型无从遵守）；⚠️ 至于 **Codex 是否会按 description 自主拉起本 skill，本次未实测**——那是依据 Codex 通用触发机制的推断，不在本次取证范围内。这一层在 Codex 侧只能靠 description 末句「只能由人显式调用 /add-external-skill 触发」作软约束；Codex 的硬约束路径是它自己的 `agents/openai.yaml`（`policy.allow_implicit_invocation: false`），本仓未采用、未实测 | `codex debug prompt-input`（隔离 CODEX_HOME） | 已确认（实测） | 1.0.1 |
| 2026-09-12 | 变更摘要在非 GitHub 上游上无成熟取法（compare API 绑定 GitHub，临时浅克隆要落盘）。首批目标都在 GitHub，首次引入非 GitHub 上游时须补 | 更新一个非 GitHub 上游的条目 | 待处理 | — |
| 2026-09-12 | 接入 `archify` 时，Step 6（安装验证：`claude plugin marketplace update` + `claude plugin install`）按控制器/用户决策未在本次自动化执行中运行——理由是该操作会向用户全局 Claude Code 环境安装一个具备任意代码执行能力的第三方插件，不应由自动化派发代为决定。已用 `python .githooks/check_external_entries.py .`（仅结构校验，不联网、不安装）替代，并独立复核了 sha。**需人工手动执行 `claude plugin marketplace update optimus-plugins-official && claude plugin install archify@optimus-plugins-official`，确认 archify 的 skill 能在列表中列出后，才能视本条目为完全验证** | 首次接入 archify | 待处理 | — |
| 2026-09-12 | 接入 `ppt-master` 时，同样按控制器/用户决策未运行 Step 6 的 `claude plugin marketplace update` + `claude plugin install`——理由与 archify 一致。已用 `python .githooks/check_external_entries.py .` 与 `bash .githooks/pre-commit` 替代，并独立复核了 sha（`git ls-remote https://github.com/hugohe3/ppt-master.git main`，结果与条目 `source.sha` 逐字一致）。**需人工手动执行 `claude plugin marketplace update optimus-plugins-official && claude plugin install ppt-master@optimus-plugins-official`，确认 ppt-master 的 skill 能在列表中列出、且按上游 setup 说明在安装后的插件目录内执行 `pip install -r requirements.txt`（Python 后处理脚本依赖）后，才能视本条目为完全验证** | 首次接入 ppt-master | 待处理 | — |
