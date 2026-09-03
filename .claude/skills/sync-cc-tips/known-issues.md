# sync-cc-tips · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-03 | 第五步同步点清单声称「只有 2 处含条目总数」，实际有 4 处；漏掉的 `.kiro/steering/plugins.md` 数字长期停在 425，`.codex-plugin/plugin.json` 版本落后真源两个 Patch | `/sync-cc-tips`（v2.1.250→v2.1.259 同步） | 已修复 | 1.2.2 |
| 2026-09-04 | 分类标签是事实断言而非排版分组：`[Skill]` 声称「可用 skill 方式调用」，但第三步只要求「从现有分类中选最匹配」，不验证该断言为真。statusline-setup（实为内置 subagent，无斜杠命令）、init、security-review（实为内置命令）三条均误标 | tips.txt 全量人工核对 | 待处理 | - |
| 2026-09-04 | 第三步完整性校验的「完整可执行形式」只覆盖 CLI 命令，未覆盖斜杠命令与 skill 名，导致例子字段出现照抄敲不出来的简称共 9 处（如 `/tdd`，真名 `test-driven-development`；`debugging`、`parallel-agents` 等 6 个 superpowers 简称） | 同上 | 待处理 | - |
| 2026-09-04 | 第五步格式校验只验前 4 字段的前缀依次正确，同一条内字段语义重复（`例子：` 写了两遍）能通过校验；且因 `--add-dir` 有意使用 5 段结构，「字段数 > 4 即报错」不能作为替代规则 | 同上 | 待处理 | - |
| 2026-09-04 | 第二步判重基准是主标识符字面匹配，别名字面不同故无法命中——`/cost` 与 `/usage`、`/review` 与 `/code-review`、`/plugins` 与 `/plugin`、`/undo` 与 `/rewind` 四组均因此产生了重复条目 | 同上 | 待处理 | - |
| 2026-09-04 | 判重方向是单向的（新条目 vs 已有条目），不检查库内已存在的多条之间是否互相覆盖。冗余由历次 sync 累积产生，每次单看都不重复：三条 `/code-review` 中一条纯泛述被另两条完全覆盖，另有三条概述 Skills 的条目讲同一件事 | 同上 | 待处理 | - |
| 2026-09-04 | 第四步「修改」的定义是原地替换，实际执行时易变成在原句后追加版本沿革从句，累积成版本考古——核对前最长条目 925 字符，而中位数仅 224，属少数条目失控 | 同上 | 待处理 | - |
| 2026-09-04 | 第三步新增条件只判断「是否对用户操作有实质影响」，未判断「本机环境能否使用」。changelog 面向全体用户，tips 面向一个具体的人：29 条 macOS/Linux 专属、Enterprise 席位、需组织管理员写 managed-settings、云厂商 SDK、claude.ai 账号会话类条目长期占位。反向注意：本机走自定义网关，网关类条目反而可用，判据是「有无硬性阻断」而非「听起来像不像企业向」 | 同上 | 待处理 | - |
| 2026-09-04 | 文档数字同步点的处数在三个位置说法不一：SKILL.md 第五步称「只有 2 处」，`test-prompts.json` 的 id 1 expected 写「同步 5 处文档数字」，实际为 4 处。按规范不重写既有测试条目，故此处仅记录，待优化循环时一并校正 | tips.txt 全量人工核对 | 待处理 | - |

## 取证方法备注

判定某个名字是 skill / command / agent 时，一手证据源是本机原生二进制而非官方文档（文档滞后于发布）：

```bash
B=~/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe
grep -ao 'no({name:"[a-z][a-z0-9-]*"' "$B" | sed 's/no({name:"//;s/"//' | sort -u   # 内置 skill（v2.1.259 共 16 项）
grep -ao '{agentType:"<名字>"[^}]\{0,80\}' "$B"                                      # 内置 subagent，无斜杠命令
grep -ao '{name:"<名字>",description:"[^"]\{0,60\}' "$B"                             # 内置命令
```

两个已踩过的坑：

1. **常量表不能作为内置证据。** 二进制里有形如 `fJe="simplify",pJe="commit",MM="code-review"` 的常量表，用途是「需特殊处理的名字」，内置项与官方插件项混在一起——`code-review` 已证实来自插件的 `commands/code-review.md`。
2. **正则写窄会把「存在」误判成「不存在」**，方向恰好是最危险的一侧。首次提取内置 skill 用了 `name:"x",menuDescription`（要求紧邻），漏掉中间插字段的 `name:"fewer-permission-prompts",requires:{workspace:!0},menuDescription:...`，该 skill 差点被当作不存在而删除。改用 `no({name:"` 才取全。

删除类改动收尾必查**悬挂引用**：被删标识符是否仍被其他条目正文提及。2026-09-04 删 29 条后，`/simplify`、`/code-review`、`/commit`、`Bedrock/Vertex/Foundry`、`Remote Control` 在 5 条保留条目里留下悬挂引用，其中包括那条专讲「skill 与命令区别」的条目——它举的两个例子恰好都被删掉了。
