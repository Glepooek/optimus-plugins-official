# add-external-skill · 外部 skill 接入台账

记录本仓库引入过的外部 skill。`.githooks/check_external_entries.py` 会校验
`marketplace.json` 里每条外部引用条目都在「已接入」表有记录，且**该行的 sha 与
条目的 `source.sha` 逐字一致**。

## 已接入

下面这行 HTML 注释是传感器的定位锚点，**不要删**——删掉会让台账与条目的 sha
一致性检查整体失效，门禁会直接报错。

<!-- registry:active -->
| 条目名 | 方式 | 上游 | ref | sha | 接入日期 | 形态分支 | 状态 |
|---|---|---|---|---|---|---|---|
| `cangjie-skill` | 链接 | https://github.com/kangarooking/cangjie-skill | main | b633a4fad5a02f0fc6b2524d1ddf3ed50c753a40 | 2026-08-29 | 根目录裸 SKILL.md | 正常 |

**`状态` 列取三值**，缺省 `正常`：

| 状态 | 含义 | 对下次更新的影响 |
|---|---|---|
| `正常` | 已验证可用 | 照常更新 |
| `上游失联` | 仓库 404 / 已删除 / 转为私有 | **U1 即报告并停**，不再去试。要恢复须人工重新确认上游 |
| `ref 待选定` | 仓库可达但目标 ref 认不出对应物 | 同上，须人工先定新 `ref` |

后两个状态的存在理由：没有状态列，「不重试」只能靠人记得哪个上游已经死了——
那不是不重试，只是把轮询周期换成了人的记忆。

## 已排除

两个子类的**复议条件不同**：形态不适用是技术判定，要等上游改变形态；决策暂缓是人的决定，改主意即可复议。

| 候选 | 子类 | 原因 | 复议条件 |
|---|---|---|---|
| `graphify` | 形态不适用 | Python CLI 项目（`pyproject.toml` + 51 个 .py）。skill 正文是 `graphify/skill.md`（小写）+ 15 个按 harness 分版，靠 `graphify install` 写入 harness 目录，仓库内无 `SKILL.md` 也无 `plugin.json` | 上游提供 `SKILL.md` 或 `.claude-plugin/plugin.json` 后可复议 |
| `darwin-skill` | 决策暂缓 | 2026-09-12 决定暂不引入。形态本身适用（`alchaincyf/darwin-skill` 根目录有 `SKILL.md`，无 `plugin.json`，ref 为 `master`） | 决定改变即可复议，无需等上游 |

## 更新历史

**失败与回滚的那次也必须留行**——否则「失败即停」会退化为「失败即忘」，下次仍从头试一遍同样的失败。

`结果` 取四值：`成功` / `失败（写入前）` / `已回滚（写入后验证失败）` / `已是最新`。
`已回滚` 行必须写明回滚到的 sha——它是「当前生效的 sha 为什么不是最新」的唯一答案来源。

| 日期 | 条目名 | 旧 sha | 新 sha | 结果 |
|---|---|---|---|---|
| — | 暂无记录 | — | — | — |
