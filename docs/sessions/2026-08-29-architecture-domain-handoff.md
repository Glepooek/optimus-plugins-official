# 会话交接：knowledge-base 三领域扩建（architecture / design-patterns / algorithms）

**日期：** 2026-08-29
**分支：** `master`（已推送，工作区干净）
**下一步：** 阶段 B —— `csharp` 五条架构条款迁移改造

---

## 已落地产物（内容不在此重复，按路径查阅）

| 产物 | 路径 | 提交 |
|---|---|---|
| architecture 领域正文与索引 | `knowledge-base/architecture/` | `254a469` |
| architecture / algorithms 设计文档 | `docs/superpowers/specs/2026-08-29-architecture-algorithms-domains.md` | `254a469` |
| architecture / algorithms 实施计划 | `docs/superpowers/plans/2026-08-29-architecture-algorithms-domains.md` | `254a469` |
| design-patterns 设计文档 | `docs/superpowers/specs/2026-08-29-design-patterns-domain.md` | `ed58af3` |
| design-patterns 实施计划 | `docs/superpowers/plans/2026-08-29-design-patterns-domain.md` | `ed58af3` |
| 版本与变更记录 | `knowledge-base/CHANGELOG.md` 的 `[5.1.0]` 条目 | `254a469` |

**当前版本：** `knowledge-base` 5.1.0。`.claude-plugin/marketplace.json` 未动（本轮不涉及 `plugins/`）。

**全局执行顺序：** A（已完成）→ **B** → P（design-patterns 四阶段）→ C（hello-algo 提取）→ D（algorithms rules）。

---

## 阶段 B 的入口

计划正文见 plan 的「阶段 B」一节，迁移清单见 spec 第四节（**8 项，含 5 条待迁移条款**）。以下是执行时需要的运行时状态，plan 里没有：

**查重基线（B 阶段的硬性消除目标）** —— 跑 `find_duplicates.py --top 20` 得到，B 做完后这六对必须全部降到 0.6 以下：

| 分数 | 候选对 |
|---|---|
| 0.917 | `architecture.02.composition-over-inheritance` ↔ `csharp.03.composition-over-inheritance` |
| 0.691 | `architecture.03.aggregate` ↔ `csharp.03.domain-modeling-ddd` |
| 0.613 | `architecture.02.solid-checkpoints` ↔ `csharp.03.solid-principles` |
| 0.556 | `architecture.01.dependency-direction` ↔ `csharp.01.layering-direction` |
| 0.537 | `architecture.09.composition-root-uniqueness` ↔ `csharp.03.dependency-injection` |
| 0.511 | `architecture.01.layering-model-choice` ↔ `csharp.01.layering-direction` |

**校验基线：** `check_index.py` 409 条 OK、`check_refs.py --strict` 113 文件 OK、`unittest` 133 全绿。B 阶段只收窄正文与改 `summary`，条目数不应变化——若 409 变了，说明误删或误增了索引行。

**B 阶段的版本影响：** 5.1.0 → **6.0.0**（Major）。理由是五条 `csharp` 条目的正文范围与 `summary` 收窄属不兼容语义变化——按 `id` 检索的消费者拿到的内容变了。`id`/`file`/`anchor` 全部不动。

---

## 会话中习得的教训（不在任何产物里）

**1. 一句里只能放一个 `§` 引用。** 写 `§ 4. 解决方案布局 与 § 7. 项目类型约定` 时，`check_refs.py --strict` 报「引用写『解决方案布局 与』，实际为『解决方案布局』」——连接词「与」被解析进标题。需要引用多个章节时分句写。B 阶段要写 5 处引用，是这个坑的高发区（已作为 CHECKPOINT 写入 plan 的 B1）。

**2. 按关键词反查迁移源会漏。** 调研阶段按「架构」「分层」「SOLID」「DDD」反查 `csharp`，只找到 3 条待迁移；A 落地后跑查重才发现另外 2 条（0.917 与 0.537），因为它们的条款措辞里不含这些词。**下次做跨领域去重，先建完新领域跑 `find_duplicates.py`，再定迁移清单**，不要反过来。这与 v1.5.0 的「按文件迁移会漏」是同一类教训的变体，已记入项目记忆 `kb_cross_domain_dedup_lesson.md`。

**3. `level` 要按小节实测措辞，不能默认填。** A 阶段 62 条全 MUST 是写脚本逐节统计「必须/禁止/应该/可以」出现次数后的结果，不是省事填的。B 阶段收窄 `csharp` 正文后，若某节的「必须」条款被摘走只剩「应该」，`level` 需要跟着降级——这点 plan 里没写，容易漏。

**4. 判 `ci` 前做外壳检验。** 「工具判的是该小节的实质，还是只是它的外壳？」A 阶段 8 条 `ci` 全部过了这道检验。B 阶段若某条 `csharp` 条目收窄后剩下的是纯落地约束，`enforcement` 可能需要从 `review` 改 `ci`（如「值对象用 `record`」分析器可判）。

**5. Bash heredoc 写文件会被权限系统拒绝。** `cat > /tmp/x.py <<'PY'` 整条被 deny。改用 Write 工具写脚本到 `C:\Users\Administrator\AppData\Local\Temp\`，再 `python` 执行。A 阶段生成索引的一次性脚本就在 `gen_arch_index.py`（不入库），其中的「正文实际章节 vs 索引登记章节」双向断言值得在 B/P/D 阶段复用。

---

## 硬约束（必须逐字遵守）

- **所有 git 提交/推送走 `commit-cc-plugin` skill**，禁止手动执行 git 工作流。`knowledge-base/` 的文档属性不构成例外。
- 禁止 `git commit --no-verify`、`git push --force`/`-f`、`git add -A`（逐文件暂存）。
- `.claude/` 下的改动**不触发** marketplace 版本升级。
- 编辑 `SKILL.md` / `CHANGELOG.md` / `AGENT.md` / `README.md` 时只改语义相关内容——不增删空行、不调整缩进、不做表格对齐。
- 历史文本（CHANGELOG 已发布条目、正文「更新历史」头、`docs/superpowers/` 下的历史计划）记录当时事实，**不改写**。
- 本机无 `pytest`，只能 `python -m unittest discover -s <dir> -p "test_*.py"`。
- `.claude/skills/darwin-skill/`、`.remember/`、`.codegraph/` 为有意 gitignore，不是缺失。

---

## 已定决策（不再询问）

| 项 | 结论 |
|---|---|
| hello-algo 许可证（CC BY-NC-SA 4.0） | **C-甲**：逐字提取 + `algorithms/reference/LICENSE` + 每篇署名 krahets + `00-README.md` 声明该目录授权独立于仓库其余部分。BY 是强制条款，不可省略 |
| 图解处理 | 改为指针（`见原书图 N-M / www.hello-algo.com`），不导出二进制入库 |
| architecture 范围 | 不限于 DDD/六边形/整洁三种，已扩至 .NET/C# 最常用架构决策（10 篇 rules） |
| design-patterns 独立成域 | 是。通用立场「模式成本与复杂度匹配」权威在 `architecture.06.style-selection § 1`，design-patterns 只留引用，不重写 |
| 消费者 skill | 本轮只建知识库，`architecture-review` / `algorithm-review` 类 skill 是后续独立决策 |
| 上轮遗留的 19 对 ≥0.4 查重候选 | 暂不处理（用户已明确） |

---

## Suggested skills

| Skill | 用途 |
|---|---|
| `knowledge-base-maintain` | 阶段 B 的主流程。Step 4（修改/迁移条目）与 Step 4.5（废弃条目）是本阶段的核心分支——某节摘除通用部分后无 C# 特有内容剩余时走废弃流程，不留空壳引用条目 |
| `commit-cc-plugin` | 所有提交推送。B 阶段是 Major 升版，提交消息须写明五条 `id` 与消费者影响 |
| `darwin-skill` | 若 B/P 阶段改动到 `plugins/` 下的 skill（如给 `csharp-code-review` 加 architecture 引用），Minor/Major 升级前先评分，新分数不得低于改动前 |
