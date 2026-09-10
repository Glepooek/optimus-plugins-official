---
task: session-handoff skill 实现
date: 2026-09-10
---

# session-handoff skill 实现 · 习得与核验

## 会话 1 — 2026-09-10

### ✅ 已核验通过的事实（下轮不必重做）

- **两处 marketplace 的插件数本就不等**：Claude 11 / Codex 10，差的是外部 url 源 `cangjie-skill`（不在 `plugins/` 下，Codex 无对等能力）。校验脚本必须断言 `a - b == {'cangjie-skill'}` 而非 `a == b`。已写进 plan 0.2 且实跑通过
- **`sh .githooks/pre-commit` 通过**：输出「插件版本号校验通过：所有插件的两份 plugin.json 同值」。新插件的两份 `1.0.0` 已被该门禁确认
- **`claude plugin validate plugins/optimus-session-plugin` 通过**：输出 `✔ Validation passed`，无 warning。说明 `.claude-plugin/plugin.json` 的字段全在白名单内
- **Codex `category` 受控词表实测 9 个取值**：`Backend`/`Decision`/`DevOps`/`Frontend`/`MCP`/`Media`/`Product`/`Productivity`/`QA`。本插件取 `Productivity`，未新造词
- **SKILL.md 178 行 ≤ 180 上限**，`templates.md` 279 行，`test-prompts.json` 5 条经 `python -m json.tool` 校验合法
- **三处版本号一致 `1.0.0`**：SKILL.md 的 `metadata.version`、README 的「版本：」行、CHANGELOG 的最新条目

### 🕳️ 踩坑记录

- **现象**：`.agents/plugins/marketplace.json` 用紧凑单行格式（`"source": { "source": "local", "path": "..." }` 写在一行），而 `.claude-plugin/marketplace.json` 是常规展开缩进
  **根因**：两份文件的书写风格历史上就不同，没有统一
  **绕过/修复**：改动时用 Edit 精确插入而非 `json.load` + `json.dump` 重写——后者会把整个文件重新格式化，产生大量无关 diff，违反「外科手术式改动」
  **归属判定**：仅本任务相关（但凡改这两份文件都适用，可考虑记入仓库约定）

- **现象**：写 SKILL.md 时一次 Edit 误删了「模式 B — 恢复」的定位小节——`old_string` 覆盖范围超出了打算改的部分
  **根因**：为了压行数做连续编辑时，`old_string` 取了过长的上下文，把相邻小节一起吞掉了
  **绕过/修复**：立刻用 `grep -n "^##"` 核对章节完整性并补回。**压缩类编辑后必须查一次章节结构**，因为压缩的目的就是删内容，误删不会有任何报错
  **归属判定**：仅本任务相关，但「压缩后查结构」是通用做法

### 💡 本轮习得

- **行数上限倒逼出的删减，价值高于事先规划的删减**：219 → 178 行的过程中，砍掉的 Red Flags 有 7 条是正文已强调过的重复项。如果不是被上限逼着逐条审视，这些重复会一直留着——它们看起来都"没错"，只是没必要
- **参照实现的「已删除功能」是最省事的情报**：fltrp 的 CHANGELOG v2.0.0 记录了它自己删掉 `feature_list.json` 的理由（"对单人 main 分支场景无用"）。直接采纳这个结论，省下了自己走一遍弯路。**读参照实现时，它删过什么和它有什么同样重要**
- **「三层结构 + 仅显式触发」两个选择之间存在隐藏耦合**：用户分别回答了两个问题，但第二个答案让第一个方案里的某一层（逐轮对话记录）失去成立基础。**独立提问不等于选项独立**——组合后要重新检查每个部分是否还站得住

## 会话 2 — 2026-09-10

### ✅ 已核验通过的事实（下轮不必重做）

- **三处版本号已升至 1.0.1 且同值**：`python` 断言 `.claude-plugin` 与 `.codex-plugin` 的 `version` 相等，输出 `claude: 1.0.1  codex: 1.0.1  同值: True`
- **marketplace 差集断言仍成立**：`a - b == {'cangjie-skill'}` 且 `b - a == set()`，拆分模板与升版本未影响两处清单
- **`references/templates.md` 已删且无残留引用**：`grep -rn "templates\.md"` 在 `plugins/optimus-session-plugin/` 下无输出
- **SKILL.md 章节结构 16 个 `#` 级标题完整**，多轮压缩编辑后无误删

### 🕳️ 踩坑记录

- **现象**：SKILL.md 里写 `DEFAULT=$(git symbolic-ref ...)` 赋值，后续步骤的另一个代码块里用 `git log "origin/${DEFAULT}..HEAD"`
  **根因**：把「读起来像一个连续脚本」误当成「跑起来是一个连续 shell 会话」。这个环境每次 Bash 调用起一个新 shell，只有工作目录持久，变量不持久
  **绕过/修复**：改为 `echo` 出实际值、后续命令写字面量，并在正文写明原因
  **归属判定**：**建议沉淀到知识库**——凡是给 agent 写的、跨多次工具调用的 shell 指令都适用，不限于本 skill

- **现象**：前置校验只有 `git rev-parse --is-inside-work-tree`，没有 `cd` 到仓库根
  **根因**：该命令在仓库的**任意子目录**都返回 true。我把它当成了「在仓库根」的校验，实际它只校验「在仓库内」
  **绕过/修复**：补 `cd "$(git rev-parse --show-toplevel)"`。不补的后果是在 `plugins/foo/` 下交接会建出平行的 `docs/sessions/`——写入成功、零报错、恢复永远找不到
  **归属判定**：**建议沉淀到知识库**，同上

- **现象**：上一轮 darwin 的 baseline 组子 agent 给出的结果与 with_skill 组高度相似，对照实验失效
  **根因**：它在仓库里自主探索时读到了 SKILL.md 本身并照着执行
  **绕过/修复**：本轮改为虚构场景 + 只读 `/tmp` 副本，把所有 git 命令输出预先喂给它，agent 无从探索也就无从污染
  **归属判定**：**建议记入 darwin-skill 的方法说明**——凡是评估「仓库内已存在的 skill」都会撞上这个污染

### 💡 本轮习得

- **自评和执行模拟是两把尺子，对 skill 而言后者才对**。我自评 68.4 时读的是「这份文档写得清不清楚」，两个独立评审做的是「照这份文档逐行执行会发生什么」。五条静默出错路径我一条都没发现，因为我读的时候在脑内补全了一个连续 shell 会话，而真正执行的 agent 不会
- **静默失败比崩溃更该扣分**——用户不会知道要去修。本轮修的 9 条里有 6 条属于「写入成功、零报错、但产物是错的」，这类缺陷不会有人来报 bug
- **示意图能看懂 ≠ 指令说清了**。模板里画了 `progress.md` 的追加位置示意图，SKILL.md 的分段表只写了「追加」二字。执行者靠对照图才推出「插入到 `---` 之前而非 append 到末尾」——这属于运气，不是设计
- **「整段覆写」在真实数据上会把仍然有效的意图连同过期快照一起丢掉**。旧段落里两者混着：「12 个文件未提交」是过期事实，「等自举验证通过后一次性提交」是仍成立的意图。这个区分只有在真实数据上执行才看得见，读模板时看不出来
