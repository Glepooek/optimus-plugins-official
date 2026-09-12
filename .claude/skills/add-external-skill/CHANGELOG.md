# Changelog

## [1.0.1] - 2026-09-12

### Changed
- 「Codex 兼容性」一节由文档调研推断改为**实测结论**：codex-cli 0.154.0 下用 `codex debug prompt-input`（隔离 `CODEX_HOME`，不发起 API 调用）确认 Codex 忽略 `disable-model-invocation` 这一未知顶层键、skill 仍正常列入模型可见清单，无告警。该字段与 Codex 镜像可以兼得，无需重新裁决。残留的非对称已写明，并**分层标注证据强度**：「该字段在 Codex 侧不生效」由「字段未进入模型可见上下文」直接推出；「Codex 会按 `description` 自主拉起本 skill」则标注为推断、本次未实测——避免推论与实测结论被当作同等确凿读走。取证证据见 `known-issues.md` 第 2 条

### Fixed
- 正文四处裸文件名引用改为路径限定形式（`.githooks/check_external_entries.py`、`external_plugins/<name>/UPSTREAM.md`）。这两个文件都不在本 skill 目录内，裸名会被 `selfcheck.py` 解析为同目录引用并报悬空
- Step 4 标题改为 `🔴 CHECKPOINT：写入前的人工确认`，并在开篇补「含 2 个阻塞式人工确认点」声明句。此前该确认点不被 `selfcheck.py` 的落地点判据识别（要求 🔴 后 30 字符内出现 `**CHECKPOINT**` 或 `CHECKPOINT：`），声明句亦缺失，`checkpoint_count` 一项恒失败

## [1.0.0] - 2026-09-12

### Added
- 首个版本：把「引入外部 skill」固化为可反复执行的 skill，取代此前散落在提交信息里的一次性判断（先例 `4d741b8` 引入 `cangjie-skill`）
- 接入与更新两个模式；接入含需求预告、四类执行前置校验、五分支形态判定、`git ls-remote` 取 40 位 sha、人在回路 CHECKPOINT、写入、安装验证、台账登记
- 形态判定表覆盖五种上游形态，含「根目录是 marketplace.json 而非 plugin.json」与「靠 CLI 安装、判定不适用」两个易错分支
- 更新模式 U0–U8，含 `ref` 变更处置、变更摘要的三种取法与取不到时的如实声明、以及对 auto-update 实际状态的核实（不只依赖默认值）
- 失败处理四格：探测阶段失败即终止不留残留；接入写入后验证失败回滚本次写入；**更新写入前失败旧 sha 原样保留**；**更新写入后验证失败必须把 sha 回滚到旧值并记「已回滚」**。三条共同硬规则：不重试、不排定时任务、不自动改 sha
- 更新失败分四类（临时不可达 / 上游仓库已消失 / ref 已消失 / 安装验证失败），「上游失联」落成台账状态标记而非仅历史记录——否则每次更新都会把同一个已死的仓库重试一遍
- `disable-model-invocation: true`：本 skill 只能由人显式调用，模型不按 description 自主拉起，`/loop` 等调度亦不执行
- 拷贝模式的两条正当理由与落位规范（含 version 取值的两情形规则）
- 配套台账 `registry.md`（已接入 / 已排除 / 更新历史三张表，已接入表带 `<!-- registry:active -->` 锚点与 `状态` 列）与传感器 `.githooks/check_external_entries.py`（检查项见 `.githooks/README.md`）
