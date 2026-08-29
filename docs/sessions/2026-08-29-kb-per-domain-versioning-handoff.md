# 会话交接：知识库分领域版本化与结构优化（5 项需求 / 四组改动）

**日期：** 2026-08-29
**分支：** `master`（已推送，工作区干净）
**下一步：** 9 个 Task 全部实施完毕，**最终统一审查未执行**——审查包已生成待用；另有 2 处待处理问题，见「待处理事项」一节

---

## 执行结果总览

用户提出 5 项知识库优化需求，归为四组，**顺序固定 A → B → D → C，全部完成并推送**。顺序不可调换：B 改文件名、D 改正文，两者都产生须写入 CHANGELOG 的变更，故 C（拆 CHANGELOG + 定版本号）必须最后，否则要写两遍。

| 组 | 内容 | 提交 | 改动规模 |
|---|---|---|---|
| A | `algorithms` → `data-structures-algorithms` 彻底改名 | `0bd0536` | 21 文件（含 `git mv`） |
| B | 9 个领域 `00-README.md` → `README.md` | `b06c230` | 18 文件 |
| — | **补丁**：修 B 组遗漏的 `plugins/` 下 4 处坏链 | `9920004` | 5 文件 |
| D | 235 处图指针回填为本地图片引用 | `a5657fd` | 15 篇正文 + 488 张图 |
| C | 版本号与 CHANGELOG 改为按领域独立管理 | `db2e952` | 25 文件（1 删 / 15 改 / 9 增） |

**版本落点**（分叉点 7.2.0，此后各领域独立递增）：

| 领域 | 版本 | 依据 |
|---|---|---|
| `data-structures-algorithms` | **8.0.0** | A 组改名 Major + D 组图片 Minor + B 组 README 改名 Patch |
| 其余 8 个 | **7.2.1** | 仅 `00-README.md` → `README.md`（Patch） |

**skill 版本联动：** `knowledge-base-maintain` 1.8.0 → **1.9.0**、`commit-cc-plugin` 3.4.2 → **3.4.3**（这两个在 `.claude/` 下，不升 marketplace）；`csharp-code-review` 1.5.4 → **1.5.5**、`wpf-code-review` 2.0.4 → **2.0.5**、marketplace 12.1.8 → **12.1.9**（补丁触及 `plugins/`，按规则须升）。

产物内容不在此重复，见：

| 产物 | 路径 |
|---|---|
| 设计文档（权威规范） | `docs/superpowers/specs/2026-08-29-knowledge-base-per-domain-versioning-design.md` |
| 实施计划（9 Task / 72 Step，含全部精确值） | `docs/superpowers/plans/2026-08-29-knowledge-base-per-domain-versioning.md` |
| 决策 ledger（我裁定的全部偏差与理由） | `.superpowers/sdd/2026-08-29-knowledge-base-per-domain-versioning/progress.md` |
| 各组实施报告 | 同目录 `task-1-report.md`、`task-b-report.md`、`task-d-report.md`、`task-c-report.md` |
| **全分支审查包（795 KB / 5 commits，待用）** | 同目录 `review-c653490..db2e952.diff` |
| 各 Task 的 brief（拆分好的需求） | 同目录 `task-1..9-brief.md` |

`.superpowers/` 已被 gitignore，是本计划的专属工作区。

---

## 已机械核验通过的事实（下轮不必重做）

这些我用脚本逐项核过，结论可信：

- `check_index.py` → **483 条 OK**；`check_refs.py --strict` → **140 文件 OK**；`unittest` → **138 tests OK**（133 + 5 新增）
- 9 个领域 README 版本行与 CHANGELOG 首条目**两侧完全一致**；根 README 已无版本行
- 图片：**488 处引用 / 488 个唯一文件 / 断链 0**；`📊 原书图` 与「图解未导出」字样全清；`assets/` 无零字节、无多余文件
- 多图组分步顺序（抽查 `hello-algo-05-stack-queue.md` 全部 6 组）：`step1→step2→step3` 严格递增且语义与正文一致。**这验证了整套多图展开算法的核心假设**——算法只按上游文档出现顺序取图、不读文件名里的 step 号，两者吻合是独立证据
- 34 条 CHANGELOG 去向：8 条删除无残留、20 条单领域、6 条跨领域切分（`7.0.0`/`6.0.0`/`5.1.0`/`1.5.0`/`1.2.1` 双侧、`4.2.0` 按设计只归 csharp），**零遗漏零重复**
- `plugins/` 下 `00-README` 坏链已清零

核对 34 条去向能自动跑，靠的是拆分时每条都留了「衍生自全局 X.Y.Z」标注——为可读性加的标注同时成了可验证性的载体。

---

## 待处理事项

### 1. 两处已确认问题（建议合并为一个 Patch 提交）

**① `knowledge-base/data-structures-algorithms/README.md:48` 领域自称仍是旧标识符**（Important，已复核为真）

```
| **`algorithms`（本领域）** | **该用什么结构、复杂度是否可接受** | 「线性查找退化为 $O(n)$ 的热路径必须换为哈希或有序结构」 |
```

此处 `` `algorithms` `` 是**代码字面量的领域标识符**（不是普通名词「算法」），指代领域自身，与文件标题「数据结构与算法规范」及全库统一的 `data-structures-algorithms` 自相矛盾。改为 `` `data-structures-algorithms`（本领域） ``。

不是实施者偏离——计划 Task 1 Step 7 精确列出的三处（第 1/3/9 行）都逐字落实了，是**计划枚举「领域名措辞」时漏了这一处**。**同一目录 CHANGELOG.md 里的 `algorithms` 是历史文本，按约定正确保留，不要改。**

**② `DOMAIN_META_FILES` 被 C 组实施者扩为 `{"README.md", "CHANGELOG.md"}`**（需确认，未必是缺陷）

位置 `.claude/skills/knowledge-base-maintain/scripts/check_index.py:43`。原因是 Task 8 新建的 9 个领域 CHANGELOG 会被孤儿文件校验误判。逻辑上正确（CHANGELOG 确实是领域元数据、非 rules/reference 内容），但 spec 与计划都没预见它，需确认两点：

- `knowledge-base-maintain` 1.9.0 的 CHANGELOG 是否记了这一条
- 是否配了对应测试（B 组给 `README.md` 白名单配了 `test_readme_is_not_orphan`，`CHANGELOG.md` 是否也有）

### 2. 最终统一审查（主任务）

审查包已生成：`.superpowers/sdd/2026-08-29-knowledge-base-per-domain-versioning/review-c653490..db2e952.diff`（795 KB，**不要一次读完**；工作区 HEAD 即最终状态，可直接读文件或对 diff 用 Grep 定位）。

上一节列出的都已机械核验，审查应聚焦机械检查覆盖不到的地方：

| # | 聚焦点 | 具体核什么 |
|---|---|---|
| 1 | **9 份领域 CHANGELOG 的内容质量**（最重要） | 对照 `git show a5657fd:knowledge-base/CHANGELOG.md`（拆分前原文）：摘取到各领域的内容是否确实属于该领域？跨领域切分的 6 条两侧是否各自完整可读、没把同一句话重复写两边？历史正文是否被**改写/润色/压缩**（要求只做摘取 + 加标注，大幅重写是缺陷）？`data-structures-algorithms` 的 8.0.0 条目是否完整覆盖 A/B/D 三组？ |
| 2 | `check_domain_versions` 实现质量 | README 缺版本行时 `continue` 的位置、`readme_ver` 为 None 的分支是否有漏判；5 个测试是否真在断言行为而非空断言 |
| 3 | `knowledge-base-maintain` SKILL.md | Step 6 重写后是否还有「根 CHANGELOG」「根 README 顶部版本」旧表述残留；新增问题表 5 行的报错字样是否与 `check_domain_versions` 实际输出**逐字对得上**（对不上则排障指引失效） |
| 4 | 根 `knowledge-base/README.md` 自洽性 | 「目录结构」章节的 `00-README.md`（第 13、23 行附近）是否已改；是否还有指向全局版本号/根 CHANGELOG 的残留 |
| 5 | 15 篇 reference 的图片引用形态 | 抽查 2-3 篇：`![alt](assets/xxx.png)` 是否独立成行、原指针的 `> ` 引用标记有无残留、段落结构是否通顺 |
| 6 | 跨提交一致性 | 版本号有无漏升错升（见总览的版本联动一段） |

**审查时不要重复报告 ledger 里已裁定接受的偏差**（下一节列出）——理由都在 `progress.md`，重复报告只会消耗一轮修复循环。

---

## 未按 spec / plan 执行的部分

### 偏离 1：取消每 Task 审查，改为最后统一审查一次

**原定**：`subagent-driven-development` 流程每个 Task 完成后派发一次审查（spec 合规 + 质量两个结论），有 Critical/Important 则进修复循环。

**实际**：用户在 Task 1 审查进行中明确指示「快速执行，最后统一审查一次」，遂中止该审查并取消后续 Task 审查，改为批次派发（B 组 = Task 2+3、D 组 = Task 4+5+6、C 组 = Task 7+8+9）。

**代价与缓解**：缺陷推迟到最终审查才暴露，修复要跨多个提交。缓解是三项机械检查在每个 Task 末尾都跑，能挡住结构性错误（漏改 id、断链、孤儿文件、版本漂移）；审查独有的「措辞质量」判断推到最后。**被中止的 Task 1 审查实际已产出一条有效发现**（即待处理事项 ①），说明这个取舍确实有成本。

### 偏离 2：图片下载环节由我接手，改串行为并行

**原定**：计划 Task 5 Step 3 给的 PowerShell 脚本串行下载，`-TimeoutSec 40` + 4 次重试 + 每次失败 `Start-Sleep 2`。

**实际**：实测约 **3 张 / 5 分钟**，488 张需十几小时。原因是失败模式判断错了——实测是**随机网络抖动**而非持续不可达（同一批里 6 张能一次成功）。对随机抖动，正确策略是缩短超时 + 提高并发。我改用 `ForEach-Object -Parallel -ThrottleLimit 10` + 15 秒超时，两轮跑完 488/488。

**为什么不算越界**：只改「怎么下」不改「下什么」——清单 `tmp-wanted.json` 由实施者的 Task 5 Step 1-2 产出、我未改动，产物一致性由 488/488 逐项核验保证（缺失 0 / 零字节 0 / 多余 0）。并行脚本已自删，不进临时文件清单。

### 偏离 3：唯一图片数 488 而非 spec 估算的 480，体积 11 MB 而非 8-9 MB

**已裁定接受。** spec 5.2 的「≤485」是按上游 485 张全量图去重推算的**上界**，但实际清单含封面图等非正文图。488 与磁盘精确一致、与引用数 488 一致，说明映射与下载都没错。代价是仓库多 2-3 MB。

### 偏离 4：`plugins/` 补丁升了 marketplace 版本

**原定**：Global Constraints 写「不升级 marketplace 版本」。

**实际**：修 B 组遗漏的 4 处坏链触及 `plugins/`，按 `AGENTS.md` 必须升（Patch → 12.1.9）。

**不冲突的理由**：该约束的前提是「全部改动落在 `knowledge-base/` 与 `.claude/`」，此补丁已越出该前提。B 组实施者正确识别了这一冲突并选择上报而非自行处理。

### 偏离 5：`DOMAIN_META_FILES` 扩容（见待处理事项 ②）

C 组实施者执行中发现的必要连带修正，属同一脚本内的最小闭环，但未经 spec/plan 预见，待确认配套是否齐全。

---

## 本轮新习得的教训（不在任何产物里）

### 1. 改名类任务的清单必须在改名**后**用兜底 grep 复核，改名前的枚举必然不全

本轮暴露 4 处「计划本身的遗漏」，成因完全相同——spec 阶段的 grep 跑在改名之前：

| # | 遗漏 | 怎么被发现 | 状态 |
|---|---|---|---|
| 1 | spec 4.1 把 `commit-cc-plugin/SKILL.md:23` 判为「唯一插件侧消费者」，实际 `plugins/` 下另有 4 处链接目标 | B 组实施者的全库 grep 兜底 | 已修（`9920004`） |
| 2 | 计划 Task 3 Step 3 只列 2 个领域的文件地图，实际 5 个领域的文件地图有 `\| 00 \| \`00-README.md\` \|` **自引用**行 | Task 3 Step 4 的兜底 grep | 实施者自行按同形处理 |
| 3 | 计划 Task 1 Step 7 枚举领域名措辞时漏了 `README.md:48` 的领域自称 | Task 1 审查者 | **未修** |
| 4 | 未预见新建的 9 个领域 CHANGELOG 会被孤儿文件校验误判 | C 组实施者执行中 | 已扩白名单，**待确认** |

改名前，`00-README.md` 还存在，指向它的行看起来是「目录项」而非「引用」；`data-structures-algorithms` 还不存在，所以每一处 `` `algorithms` `` 都得靠人判断是标识符还是普通名词。**这是枚举时机的结构性局限，不是谁疏忽。** 计划里每个 Task 都留 grep 兜底步骤的价值正在此——它不是形式主义复查，而是承认清单可能不全。

### 2. 判断网络失败模式，再决定重试策略；串行 + 长超时是对随机抖动的最差组合

`raw.githubusercontent.com` 的失败是**随机抖动**（同批里部分请求一次成功），不是持续不可达。对随机抖动：**缩短超时 + 提高并发**（15 秒 / 10 路并行），抖动被并发摊平；而串行 + 40 秒超时 + 4 次重试 + sleep 2，单张最坏 168 秒，488 张要十几小时。上一轮交接文档记的教训是「须重试」，本轮补充：**重试策略要匹配失败模式，不是加了重试就完事**。

### 3. 为可读性加的标注可以顺带成为可验证性的载体

各领域 CHANGELOG 里「衍生自全局 X.Y.Z」这个标注，设计初衷是保留跨领域关联的可追溯性（人读得懂这条是从哪来的）。实际它让「34 条去向零遗漏零重复」这个核对**可以脚本化**——否则要人工通读 9 份 CHANGELOG。设计时不起眼的格式决定带来了意外的审计能力。

### 4. 机械校验挡结构、审查挡语义，取消审查时要认清丢的是哪一半

本轮取消每 Task 审查后，三项检查（`check_index` / `check_refs` / `unittest`）挡住了全部结构性错误：漏改 id、断链、孤儿文件、版本漂移。但被中止的 Task 1 审查产出的那条发现（`README.md:48` 领域自称）**机械检查永远查不出来**——它语法正确、链接有效、索引一致，只是语义上自相矛盾。**「引导器要配传感器」这条仓库原则，在这里的推论是：传感器只覆盖它能判定的那一层。**

---

## 硬约束（必须逐字遵守，本轮已全部核查通过）

- **提交与推送必须走 `commit-cc-plugin` skill**，禁止手动 git 工作流（`AGENTS.md` 强制）。禁止 `git add -A`、`git push --force`、`git commit --no-verify`
  - 例外已确认：`assets/` 这类含数百文件的新目录允许**目录级**精确暂存（`git add <dir>`），禁的是全库通配
- **两套版本号正交**：`.claude/` 下改动不升 marketplace；`plugins/` 下改动按新增 Minor / 更新 Patch / 删除重命名 Major 升 `.claude-plugin/marketplace.json`；skill 自身 `metadata.version` 是独立编号
- **编辑 Markdown 禁止无关格式化**（`.claude/rules/skill-conventions.md` 铁律）：不增删空行、不调缩进、不做表格对齐。提交前看 `git diff`，出现大片纯空白变化说明格式化工具介入了
- **历史记录类文本不改写**：`docs/`、`.remember/`、各 CHANGELOG 里的旧路径名记录当时事实，保持不动
- 本机**无 pytest**：`python -m unittest discover -s <dir> -p "test_*.py"`
- **网络**：`raw.githubusercontent.com` 对 curl 与 WebFetch **均超时**，只有 PowerShell `Invoke-WebRequest` 可达。大批量下载见教训 2
- **长内容分段写入**：用户明确要求过「响应内容太多时采用分批写入，不要一次性写入，导致响应数据过大」——这是 API 层面的实际约束，已多次复现。写长文档用 Write 建骨架 + 多次 Edit 追加
- 全程用**简体中文**回复

---

## 已定决策（不再询问）

这些都经用户明确拍板，下轮不要重新提出：

| 决策 | 内容 |
|---|---|
| 领域改名彻底做 | 目录名与 id 前缀一并改（用户原话「修改就彻底修改」），不只改中文 title |
| 中文展示名 | 「数据结构与算法」（不是「算法与数据结构」） |
| 图片处置 | 从上游 1.3.0 下载到本地 `reference/assets/`，改标准 `![]()` 引用；不用外链 |
| 根 CHANGELOG | **删除**，34 条按领域重写切分 |
| 8 条机制类历史 | **直接删除**不保留（1.0.0/1.1.1/1.3.3/2.0.0/3.0.0/4.0.0/4.1.0/5.0.0），已确认接受知识损失 |
| 根 README | 删版本行且**不放领域版本一览表** |
| 版本分叉点 | 7.2.0；新建领域从 1.0.0 起算，不套用分叉点 |
| 一次性脚本 | 跑完删除不留仓库（不属于 `knowledge-base-maintain` 常规能力，留下会成死代码） |
| 执行位置 | 在 `master` 上直接实施，不建 worktree |

---

## Suggested skills

| skill | 用途 | 时机 |
|---|---|---|
| `superpowers:requesting-code-review` | 最终统一审查（有现成 `code-reviewer.md` 模板） | **首先做** |
| `superpowers:receiving-code-review` | 处理审查结论、决定哪些修哪些驳回 | 审查报告返回后 |
| `commit-cc-plugin` | 提交待处理事项 1 的 Patch，及审查发现的任何修复 | 有改动要提交时 |
| `knowledge-base-maintain` | 若需改知识库条目内容（1.9.0 已支持领域独立版本模型，会自动同步索引与**领域**版本号） | 按需 |

**不建议**再用 `superpowers:subagent-driven-development`——9 个 Task 已全部完成，剩下的是审查与零星修复，不需要 Task 循环。

---

## 验收命令（下轮回归基线）

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
# → OK: 共检查 483 条记录，未发现问题

python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
# → OK: 检查 140 个消费者文件，章节号引用全部有效

python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
# → Ran 138 tests ... OK
```

领域版本号一致性（9 行全 OK，`data-structures-algorithms`=8.0.0，其余 7.2.1）：

```bash
for d in knowledge-base/*/; do
  n=$(basename "$d")
  v=$(grep -m1 '^> 版本：' "$d/README.md" | sed 's/^> 版本：//')
  c=$(grep -m1 '^## \[' "$d/CHANGELOG.md" | sed 's/^## \[//;s/\].*//')
  printf "%-28s README=%-8s CHANGELOG=%-8s %s\n" "$n" "$v" "$c" "$([ "$v" = "$c" ] && echo OK || echo 不一致)"
done
grep -n '^> 版本：' knowledge-base/README.md   # 根 README 应无版本行
```

图片完整性（488 处引用 / 488 唯一文件 / 断链 0）：

```bash
python - <<'PY'
import re, glob
from pathlib import Path
d = Path('knowledge-base/data-structures-algorithms/reference/assets')
refs = []
for f in glob.glob('knowledge-base/data-structures-algorithms/reference/hello-algo-*.md'):
    refs += re.findall(r'!\[[^\]]*\]\(assets/([^)]+)\)', Path(f).read_text(encoding='utf-8'))
broken = sorted({r for r in refs if not (d / r).exists()})
print(f"图片引用 {len(refs)} 处，唯一文件 {len(set(refs))}，断链 {len(broken)}")
PY
```


