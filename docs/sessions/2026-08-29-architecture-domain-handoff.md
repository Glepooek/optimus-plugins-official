# 会话交接：knowledge-base 三领域扩建（architecture / design-patterns / algorithms）

**日期：** 2026-08-29（本文件已于同日更新——原版本停在阶段 A 末，下一步写的是「阶段 B」）
**分支：** `master`（已推送，工作区干净）
**下一步：** 本轮五阶段**全部完成**，无待续阶段。后续可选方向见文末「后续可选方向」一节

---

## 执行结果总览

**全局执行顺序 A → B → P → C → D，五阶段全部完成并推送 `master`。**

| 阶段 | 内容 | 提交 | 版本 | 改动规模 |
|---|---|---|---|---|
| A | architecture 领域（62 rule + 2 reference） | `254a469` | 5.0.0 → 5.1.0 | — |
| B | csharp 五条架构条款迁移收窄 | `b300838` | 5.1.0 → **6.0.0** Major | 7 文件 +76 −40 |
| P | design-patterns 领域（33 rule + 2 reference） | `b491446` | 6.0.0 → **7.0.0** Major | 16 文件 +1010 −10 |
| C | algorithms reference 侧（15 章 + LICENSE） | `80ddfdc` | 7.0.0 → **7.1.0** Minor | 21 文件 +10132 −3 |
| D | algorithms rules 侧（4 篇 / 24 rule） | `a974b5d` | 7.1.0 → **7.2.0** Minor | 9 文件 +446 −5 |

**当前版本：** `knowledge-base` **7.2.0**，9 领域 / **483 条**索引。`.claude-plugin/marketplace.json` 全程未动（五阶段改动均在 `knowledge-base/` 下，不涉及 `plugins/`）。

三个新领域的实测指标：

| 领域 | 条目 | 覆盖率 | `enforcement` 分布 |
|---|---|---|---|
| architecture | 62 rule + 2 ref | 100.0% | review 50 / ci 8 / advisory 4 |
| design-patterns | 33 rule + 2 ref | 100.0% | review 27 / ci 3 / advisory 3 |
| algorithms | 24 rule + 15 ref | 92.3% | review 24 |

algorithms 的 92.3% 是**正确状态**，非缺口：`02 § 8. 选型对照` 与 `04 § 8. 策略对照` 两张速查表有意不登记（措辞统计「必须/禁止/应该/可以」各 0 次，每行的适用前提都写在对应小节内，登记会给同一约束造第二个检索入口）。

产物内容不在此重复，见 `knowledge-base/CHANGELOG.md` 的 `[5.1.0]`–`[7.2.0]` 五个条目。

---

## 原定阶段 B 的硬性目标：六对基线全部消除（已重跑实测）

原版本列出的六对查重基线是 B 阶段的硬性消除目标。逐对重跑 `find_duplicates.py --top 400 --threshold 0.1` 确认（非引用当时结论）：

| 原基线 | 现状 |
|---|---|
| 0.917 `architecture.02.composition-over-inheritance` ↔ `csharp.03.composition-over-inheritance` | 已消除；该 `id` 最高残留 **0.182**，对手换成 `csharp.05.exception-type-selection` |
| 0.691 `architecture.03.aggregate` ↔ `csharp.03.domain-modeling-ddd` | 已消除；该 `id` 最高 **0.200**（`wpf.03.view-viewmodel-pairing`） |
| 0.613 `architecture.02.solid-checkpoints` ↔ `csharp.03.solid-principles` | **0.147** |
| 0.556 `architecture.01.dependency-direction` ↔ `csharp.01.layering-direction` | **0.147** |
| 0.537 `architecture.09.composition-root-uniqueness` ↔ `csharp.03.dependency-injection` | 已消除；该 `id` 最高 **0.306**（`design-patterns.05.service-locator`） |
| 0.511 `architecture.01.layering-model-choice` ↔ `csharp.01.layering-direction` | 已消除 |

原版本要求的「B 阶段条目数不应变化（409 条）」也守住了——收窄只改正文与 `summary`，`id`/`file`/`anchor` 全部未动。

---

## 未按交接文档 / spec / plan 执行的部分

三处偏离，均已落地并通过验收。原因与新做法如下。

### 偏离 1：C 阶段的数据来源由 PDF 改为上游 markdown 源

**原定做法**（spec 第 151 行、plan C1）：用 `pdfplumber` 从 `hello-algo_1.3.0_zh_csharp.pdf`（356 页）提取，脚本含「字符修复层」（`^/`→`//`、`^^=`→`===`、`^^.`→`...`）。

**实际做法**：改从上游 GitHub 仓库 `krahets/hello-algo` 的 **tag `1.3.0`** 拉取 markdown 源（`docs/**/*.md` 107 篇 + `mkdocs.yml`），代码从同 tag 的 `codes/csharp/**/*.cs`（86 篇）按花括号配平提取，回填 ```` ```src ```` 占位符（133 处，全部成功）。

**改的原因——PDF 路线不可完备逆向，且这一点只能靠实测发现：**

字符修复表本身是对的，但**不完备且不可能完备**。逐个排查全部 18 处 `^.` 后确认：p42 的 `1 + 2 + 4 + 8 + ^. + 2^(n-1)` 还原为 `...`（省略号），而 p101 的 `front^.next` 还原为 `->`（C++ 箭头）——**同一输出对应两个不同输入**。交叉验证（`!=`/`<=`/`>=` 字面出现不连字，而 `==`/`..`/`&&`/`::`/`??`/`=>`/`*/`/`//` 从不字面出现）证实这是连字符号表的固有歧义，非个例。

后果的性质决定了必须换路线：任何单一替换规则都会在一边**静默写错**，且写错后语法仍然合法、`grep` 检不出。plan C2 的门禁判据（`grep -c '\^/\|\^\^'` 为 0）**通不过这类缺陷**——它检的是残留标记，而歧义还原产生的是「看起来正常的错代码」。

同类问题还有一层：`^/` 有两个来源（903 处行注释 `//` 与 342 处块注释闭合 `*/`），靠「是否以 `/*` 开头」分类才区分开。这类修复能做，但每修一个都要重新证明完备性。

**改后额外拿回三样 PDF 路线必然丢失的东西**：代码缩进、行内代码标记（`` ` ``）、真实图片路径。

**可复用结论（已写入 `knowledge-base/CHANGELOG.md` [7.1.0]「提取路线的两处实测结论」）**：

1. **有上游 markdown 源时不要从 PDF 提取。** PDF 是渲染产物，正确的问题是「这份数据是不是某个东西的渲染结果」——是，就去找那个东西。
2. **按 tag 抓取而非默认分支。** 来源声明写「版本 1.3.0」就必须取 `1.3.0` tag；`main` 已漂移（实测多出 13 个 `exercises.md`），抓 `main` 会让声明变成不可复现的假声明。

**门禁做法也相应改了**：plan C2 的 5 项 PDF 判据不再适用，改为独立写一个 7 项机械门禁脚本（章号↔标题↔节号一致、来源声明完整、无 MkDocs 残留、栅栏配平且无非 C# 语言泄漏、无标题跳级、无 PDF 连字哨兵、小节覆盖计数）。**该门禁与提取器分开写**，首轮报出 28 项失败、含 3 个真缺陷，其中一个（代码栅栏内 Python 的 `#` 注释被当成 Markdown 标题）是提取器与我最初的门禁**共有的盲区**——若门禁复用提取器的解析逻辑，这个缺陷会一起漏过。

### 偏离 2：`applies_to` 由 `["数据结构与算法", "C#"]` 改为 `["算法与数据结构", "语言无关"]`

**原定做法**（spec 第 203 行）：algorithms 领域填 `["数据结构与算法", "C#"]`，理由写的是「PDF 是 C# 版，代码示例为 C#」。

**实际做法**：39 条（24 rule + 15 reference）统一填 `["算法与数据结构", "语言无关"]`。

**改的原因**：spec 那条理由只对 `reference/` 成立，却被写成了对**整个领域**的约定。C 阶段确定 `rules/` 必须语言无关（领域 `00-README.md` 声明「不回答在 C# 里用哪个类型怎么写」，正文禁止出现语言专有类型名，实测 4 篇对 `Dictionary`/`List<`/`record`/`HttpClient` **0 命中**）。若给 rules 标 `applies_to: ["C#"]`，按技术栈过滤的消费者会认为这些复杂度与选型判据不适用于非 C# 代码——而它们恰恰适用，这是本领域的核心定位。

改后取值与同为语言无关的 `architecture`（`["软件架构", "语言无关"]`）形成一致模式；`design-patterns` 则是混合（29 条语言无关 + 6 条 `["设计模式","C#",".NET"]`，后者是 `06-modern-alternatives.md` 那篇被允许点名语言特性的）。

**未一并改 spec**：`docs/superpowers/specs/` 属历史决策记录，按硬约束不改写。该偏离在此处与 CHANGELOG [7.1.0] 均有记录。

### 偏离 3：D 阶段一条计划断言未获证实，条款措辞相应收紧

**原定做法**（spec 第 125 行）：`03-recursion-iteration.md` 写「尾递归在 **.NET** 的实际状况」。我原本要写的条款是「C# 编译器不发出 `tail.` 前缀，所以尾递归不能作为深度保证」。

**实际做法**：条款写成「**尾递归的深度安全性不可验证**，因此不能作为设计依据」。

**改的原因**：查 `OpCodes.Tailcall` 的官方文档后确认，该页**不涉及 C# 编译器是否发出该前缀**——它只说明 `tail.` 前缀的语义，以及运行时在若干情形下会**忽略**它（跨信任边界须做安全检查时、退出 `synchronized` 区域时）。也就是说「编译器不发出」这一步**我没有核实到依据**。

改后的措辞由两条已核实事实直接支撑，绕开了未证实的那一步：

- `tail.` 即使存在于 IL 中也可能被运行时忽略（`OpCodes.Tailcall`）
- `StackOverflowException` **不可被 `try`/`catch` 捕获**，进程默认终止，`HandleProcessCorruptedStateExceptions` 对它无效（`System.StackOverflowException`）

**结论强度未降低**（仍是「禁止以『这是尾递归』作为不设深度上限的理由」），依据换成了站得住的那条。索引 `source` 相应填这两个 Microsoft Learn URL——这是 algorithms 24 条中唯一两条外部 `source`，因为书中通篇未点名任何运行时。

---

## 原版本五条教训的应用情况

| 教训 | 结果 |
|---|---|
| **1. 一句里只能放一个 `§` 引用** | B/P 阶段守住，**D 阶段仍踩到 4 处**（`check_refs.py --strict` 报「引用写『集合预分配 与同文件』」等）。已修正为分句。附带发现：我最初填的三个章节编号（热点路径、基准测试、静态引用）**全部是错的**，正是「号与标题必须同时对得上」的一致性检查把它们逼出来的——若按惯性只写 `§ 1` 不带标题，三处会静默指向别的章节且永不可查。**这条防线的价值被实测确认，不是形式要求** |
| **2. 先建域再定迁移清单** | 已照办。B 阶段迁移清单从 spec 原定 3 条修正为**实际 5 条**，多出的两条正是关键词反查漏掉的（0.917 与 0.537） |
| **3. `level` 按小节实测措辞** | 已照办，**触发两次降级**：`csharp.03.composition-over-inheritance` MUST → SHOULD（摘除三条「必须/禁止」后只剩「应该：用 `sealed` 标记」）。D 阶段 24 条全 MUST 亦为逐节统计结果 |
| **4. 判 `ci` 前做外壳检验** | 已照办，方向与预判一致——**三条 `enforcement` 从 `review` 升为 `ci`**（B 两条、P 一条）。原因是摘走「判意图」的通用部分后，留下的恰是「判形态」的落地约束，形态是工具的强项 |
| **5. heredoc 被 deny，改 Write + python** | 全程照办。D 阶段追加 24 条索引时 `cat >>` 仍被拒，改为 Write 临时脚本 + `python` 执行 |

---

## 本轮新习得的教训（不在任何产物里）

以下六条是 B–D 阶段新增，与原版本五条并列，下轮仍适用。

**1. PDF 是渲染产物，有源就去找源。** 见「偏离 1」。更一般的形态：遇到需要「修复」的数据，先问它是不是某个东西的渲染结果。所有连字表工作执行本身没错，但方向错了。

**2. 歧义是墙，不是谜题。** 发现 `^.` 同时来自两个输入时，正确反应是「这条路线关闭」，不是「再想想怎么消歧」。同一输出对应多个输入 → 不可还原，任何规则都会在一边写错。

**3. 校验器必须与被校验的代码分开写。** 「133/133 提取成功」只代表没抛异常。独立写的 C2 门禁抓出 3 个真缺陷，其中 1 个是提取器与我最初门禁**共有的盲区**（代码栅栏内的 `#` 被当成标题）。复用解析逻辑 = 共享盲区。

**4. 语义防撞在措辞阶段完成，不靠事后查重。** D 阶段 algorithms 与全库最高候选仅 **0.238**，0.4–0.6 区间**无一对候选**。这不是运气：写正文时先做了「本篇的策略不是策略模式」「本篇的复杂度不是圈复杂度」的区分，才据此把 `title`/`summary` 写成「算法策略的前提条件」而非泛泛的「策略选择」（该对实测 0.139）。**若先按泛化措辞写完再查重，改措辞已要连带改 `id` 与 `anchor`。**

**5. 真正的风险是同词不同义，查重脚本抓不到。** 三处词面相同、语义无关，分数都低（0.14–0.24）但人会拿错条目，已在 algorithms 正文显式挡掉：**复杂度**（本领域是渐近复杂度；`csharp.15.complexity-metrics` 是圈复杂度；`architecture.06.cost-complexity-match` 是问题域复杂度）、**策略**（本领域是算法策略；`design-patterns.04.strategy` 是策略模式）、**集合预分配**（`csharp.07` 讲怎么写；本领域讲扩容为何有摊还代价）。

**6. 判断要不要配套收窄，看「这块内容此前有没有寄生处」，不看领域名是否接近。** A 阶段要 Major 收窄，因为 architecture 的内容原本寄生在 `csharp` 里；D 阶段零重叠，因为建域前按 13 个关键词反查全库，确认 `csharp.07.*`/`csharp.08.*` 全 19 条都是「怎么用不踩坑」，而递归深度、栈溢出、复杂度量级、策略前提这个语义面**此前零条款**。领域名听起来接近不构成收窄理由。

**7. `source` 锚点是子串匹配，写太短会误命中。** `check_index.py` 用 `anchor in heading` 判定。只写 `AVL 树` 会同时匹配 `AVL 树旋转`/`AVL 树常用操作` 等五个标题；带章节号（`7.5 AVL 树`）是必要的精度保障。副作用是好的：末尾的原书选读标记（`7.5 AVL 树 *`）不影响匹配。

---

## 硬约束（必须逐字遵守，本轮已全部核查通过）

- **所有 git 提交/推送走 `commit-cc-plugin` skill**，禁止手动执行 git 工作流。`knowledge-base/` 的文档属性不构成例外。
- 禁止 `git commit --no-verify`、`git push --force`/`-f`、`git add -A`（逐文件暂存）。本轮五个提交均已核查：`reflog` 无 force 记录，全部逐文件暂存。
- `.claude/` 下的改动**不触发** marketplace 版本升级。
- 编辑 `SKILL.md` / `CHANGELOG.md` / `AGENT.md` / `README.md` 时只改语义相关内容——不增删空行、不调整缩进、不做表格对齐。
- 历史文本（CHANGELOG 已发布条目、正文「更新历史」头、`docs/superpowers/` 下的历史计划与 spec）记录当时事实，**不改写**。本轮已核查：`git diff` 显示 CHANGELOG 历史条目零删除行，只有新增。
- 本机无 `pytest`，只能 `python -m unittest discover -s <dir> -p "test_*.py"`。
- `.claude/skills/darwin-skill/`、`.remember/`、`.codegraph/` 为有意 gitignore，不是缺失。
- **`algorithms/reference/` 的许可证独立于本仓库**（CC BY-NC-SA 4.0）。SA 在**目录级别**隔离：不得把自撰内容混入该目录，也不得整段复制其正文到 `rules/`——`rules/` 只能通过 `source` 引用。该目录不接受本地编辑，更新时重新从上游 tag 提取。

---

## 已定决策（不再询问，本轮已全部落实）

| 项 | 结论 | 落实情况 |
|---|---|---|
| hello-algo 许可证（CC BY-NC-SA 4.0） | **C-甲**：逐字提取 + `reference/LICENSE` + 每篇署名 krahets + `00-README.md` 声明目录授权独立 | 已落实。**实测确认 `LICENSE` 不被报为孤儿**——`check_index.py` 只扫 `.md`（原版本要求实测的 CHECKPOINT，结论：预期正确）。SA 隔离写死在四处：领域 README、根 README 维护约定、`catalog.json` 的 `notes`、CHANGELOG |
| 图解处理 | 改为指针，不导出二进制入库 | 已落实，15 章零二进制 |
| architecture 范围 | 扩至 .NET/C# 最常用架构决策（10 篇 rules） | 已落实，62 rule |
| design-patterns 独立成域 | 是。通用立场「模式成本与复杂度匹配」权威在 `architecture.06.style-selection § 1`，design-patterns 只留引用 | 已落实。实测该措施有效：两条同名条目查重仅 **0.203** |
| 消费者 skill | 本轮只建知识库，`architecture-review` / `algorithm-review` 类 skill 是后续独立决策 | 未做（按决策）。三个新领域的 `catalog.json` `consumers` 均为空数组 |
| 上轮遗留的 19 对 ≥0.4 查重候选 | 暂不处理（用户已明确） | 未动。当前全库 ≥0.4 候选仍在，最高 **0.823**（`csharp.12.test-pyramid` ↔ `wpf.11.test-layering`） |
| C 阶段 reference 的代码语言 | **仅保留 C#**（原书含 12 种，用户在会话中选定） | 已落实，164 个 C# 代码块 |

---

## 后续可选方向（均未获批准，需用户决策）

本轮范围已闭合，以下为可能的下一步，按依赖顺序列出：

1. **消费者 skill 建设**：三个新领域（architecture / design-patterns / algorithms）目前 `consumers` 全为空——规范已建但无 skill 消费。既有形态可参照 `csharp-code-review` / `wpf-code-review` 的「审查清单固定映射」模式。**这是本轮明确推迟的决策**
2. **19 对 ≥0.4 遗留查重候选**：最高 0.823（`csharp.12` ↔ `wpf.11` 测试分层一族，4 对集中在测试主题）。若处理，按 4.0.0 那次 C# ↔ WPF 去重的模式做
3. **algorithms 的 `enforcement` 是否有可升 `ci` 的**：当前 24 条全 `review`。最接近的是 `03.recursion-depth-limit`（捕获栈溢出的代码形态可静态检出），但该节实质是「深度必须事前受控」，只判外壳故仍取 `review`。若将来引入分析器规则，可重新评估

---

## Suggested skills

| Skill | 用途 |
|---|---|
| `knowledge-base-maintain` | 任何 `knowledge-base/` 改动的主流程。本轮用到 Step 2（查重）、Step 3（新增）、Step 4（修改/迁移）、Step 5（校验）、Step 6（版本与 CHANGELOG） |
| `commit-cc-plugin` | 所有提交推送。本轮四次提交均经此 skill |
| `darwin-skill` | 若后续改动 `plugins/` 下的 skill（如给 `csharp-code-review` 加 architecture 引用），Minor/Major 升级前先评分，新分数不得低于改动前 |

---

## 验收命令（下轮回归基线）

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"            # 期望 483 条 OK
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" --audit    # catalog.json 9 领域双向一致、无孤儿文件
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict    # 期望 140 文件 OK
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py" --top 20
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"   # 期望 133 全绿
```

本轮末实测：`check_index.py` **483 条 OK**、`check_refs.py --strict` **140 文件 OK**、`unittest` **133 全绿**、`git diff --check` 无空白污染。
