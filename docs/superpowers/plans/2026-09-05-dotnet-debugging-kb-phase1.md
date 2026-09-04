# dotnet-debugging 知识库领域（一期）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建 `knowledge-base/dotnet-debugging/` 领域，交付共性层的 .NET 调试取证知识（8 篇 reference + 1 篇 rules + 42 条索引），填补知识库「事后诊断与定位」空白。

**Architecture:** 沿用仓库既有领域结构（领域根放 `README.md` / `index.jsonl` / `CHANGELOG.md`，内容按 `rules/` 与 `reference/` 分目录）。内容组织的核心决策是**按命令/征象分片登记索引**而非整篇登记——调试知识天然按这两个维度被检索。每篇 reference 的每条命令遵循固定四段结构（用途与前置条件 / 语法与开关 / 输出逐列语义 / 判据），其中第四段是未来 skill 编排的接口。

**Tech Stack:** Markdown + JSONL 索引；校验工具为仓库自带 Python 脚本（`check_index.py` / `find_duplicates.py` / `check_refs.py`，本机只有 `unittest`，无 `pytest`）。

**Spec:** `docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md`

## Global Constraints

以下约束适用于**每一个** Task，不再逐条重复：

- **域名与 id 前缀**：域名 `dotnet-debugging`；reference 条目 id 为 `dotnet-debugging.ref.<slug>`，rule 条目为 `dotnet-debugging.01.<slug>`。`ID_RE = ^[a-z0-9-]+\.(?:\d{2}|ref)\.[a-z0-9-]+$`，**slug 只能含小写字母、数字、连字符**——`!` 与下划线非法。
- **正文语言中文，`tags` 全英文**：全库 305 个 tag 零中文，严格遵守；tag 用小写字母加连字符。
- **`anchor` 填中文标题文本**（非 slug），`check_index.py` 按 `anchor in heading` 子串匹配。
- **索引 `source` 字段只用于领域内引用**，形式 `reference/<file>.md#<中文标题文本>`。**跨领域引用一律写在正文里**，形式 `knowledge-base/<domain>/rules/NN-x.md § 章节`（`architecture` 领域有 10 处先例）。跨领域路径写进 `source` 会被路径越界检查拦截。
- **两种引用符号服务于两个校验器，不得混用**：
  | 位置 | 符号 | 形式 | 校验者 |
  |---|---|---|---|
  | 索引 `source` 字段 | `#` | `reference/clr-runtime-anatomy.md#3. 同步块表` | `check_index.py` 的 `check_source_refs`（靠 `partition("#")` 切分） |
  | **正文**交叉引用（含领域内与跨领域） | ` § ` | `reference/sos-locks-and-async.md § 1. !syncblk` | `check_refs.py` |

  正文里写 `#` 不会报错，但 `check_refs.py` 检不到——引用会静默失效。**正文一律用 ` § `。**

- **治理字段必填**：每条 `rule` 必须有 `enforcement`、`status`、`applies_to`、`reviewed_at`、`owner`。`owner` 统一填 `desktop client team`，`status` 填 `active`，`reviewed_at` 填实际撰写日期（ISO `YYYY-MM-DD`）。
- **`applies_to` 对 reference 条目同样必填**（本领域额外约定）：每条命令的运行时可用性不同，取值示例 `[".NET Framework 4.x", ".NET 6+", "Windows"]`。
- **`level: MAY` 不得配 `enforcement: ci`**，该组合由校验器报错。
- **分段写入**：单篇 reference 预计数百行，必须先 `Write` 骨架再多次 `Edit` 逐段填充，禁止单次输出整篇。
- **版本号**：领域 `README.md` 顶部写 `> 版本：1.0.0`，须与 `CHANGELOG.md` 最新条目版本号一致（校验器检查）。**不升 `.claude-plugin/marketplace.json`**——本次不动 `plugins/` 与 `.claude/`。
- **内容来源标注**：出自《Advanced .NET Debugging》等书籍、无官方文档佐证的内容，正文须标注为经验性知识，不与官方文档事实混排。
- **提交**：每个 Task 末尾提交。本仓库禁止手动 git 工作流，但**执行本计划期间的逐 Task 提交例外**——`commit-cc-plugin` 面向一次完整发布，逐 Task 用直接 git 命令，最终推送前再走一次该 skill。提交类型统一 `docs(kb)`，Co-Authored-By 填当前会话实际模型名。

---

## File Structure

| 文件 | 责任 | 产出 Task |
|---|---|---|
| `knowledge-base/dotnet-debugging/README.md` | 领域边界、收录判据、阅读路径、文件地图 | Task 1 |
| `knowledge-base/dotnet-debugging/CHANGELOG.md` | 版本历史，`[1.0.0]` 建域 | Task 1 |
| `knowledge-base/dotnet-debugging/index.jsonl` | 42 条索引，随各 Task 增量追加 | Task 1 起，每 Task 追加 |
| `knowledge-base/catalog.json` | 登记新领域（校验器双向一致性检查） | Task 1 |
| `knowledge-base/README.md` | 首段领域列表 + 领域职责边界长句 | Task 1 |
| `reference/clr-runtime-anatomy.md` | 运行时可观测结构，其余篇目的术语基础 | Task 2 |
| `reference/dump-types-and-capability.md` | 四种 dump 类型的取证能力边界 | Task 3 |
| `reference/dump-capture.md` | 三运行时 × 抓取工具的完整命令 | Task 3 |
| `reference/symbols-and-tool-matching.md` | 符号与 SOS 版本匹配（所有命令的前置条件） | Task 4 |
| `reference/sos-threads-and-stacks.md` | 线程与栈类 SOS 命令 | Task 5 |
| `reference/sos-heap-and-objects.md` | 堆与对象类 SOS 命令 | Task 6 |
| `reference/sos-locks-and-async.md` | 锁与异步类 SOS 命令 | Task 7 |
| `reference/debugging-decision-tree.md` | 六类征象 → 假设 → 取证命令的查表 | Task 8 |
| `rules/01-dump-handling.md` | dump 作为数据资产的 5 条处置条款 | Task 9 |

**任务顺序依据**：`clr-runtime-anatomy` 最先——它定义的术语（分代堆、同步块表、终结队列）被后续所有篇目引用。`debugging-decision-tree` 倒数第二——它要指向全部命令条目的 anchor，须在命令篇目落地后才能写准。`rules` 最后——它引用 `dump-types-and-capability` 的类型名。

**TDD 在本计划中的形态**：知识库无单元测试，`check_index.py` 就是测试运行器。每个 Task 遵循「先跑校验看它报错 → 补内容 → 再跑校验看它通过」的循环，与代码 TDD 同构。

---

### Task 1: 领域骨架与注册

**Files:**
- Create: `knowledge-base/dotnet-debugging/README.md`
- Create: `knowledge-base/dotnet-debugging/CHANGELOG.md`
- Create: `knowledge-base/dotnet-debugging/index.jsonl`（空文件）
- Create: `knowledge-base/dotnet-debugging/reference/.gitkeep`
- Create: `knowledge-base/dotnet-debugging/rules/.gitkeep`
- Modify: `knowledge-base/catalog.json`（`domains` 数组末尾追加）
- Modify: `knowledge-base/README.md`（第 3 行领域列表、第 29 行职责边界句）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`

**Interfaces:**
- Consumes: 无（首个 Task）
- Produces: 领域目录结构与 `index.jsonl` 文件路径，后续 Task 2–9 全部向该文件追加行；`README.md` 的「文件地图」表格由后续 Task 逐行补充

- [ ] **Step 1: 跑校验确认领域不存在（失败用例）**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，报领域目录不存在或 `catalog.json` 缺失该领域。记下确切错误文本，Step 5 用它对比。

- [ ] **Step 2: 建目录与空索引**

```bash
cd "E:\ProjectxPlex\WPFCodePlex\optimus-plugins-official"
mkdir -p knowledge-base/dotnet-debugging/reference knowledge-base/dotnet-debugging/rules
touch knowledge-base/dotnet-debugging/index.jsonl
touch knowledge-base/dotnet-debugging/reference/.gitkeep
touch knowledge-base/dotnet-debugging/rules/.gitkeep
```

- [ ] **Step 3: 写 `README.md`**

分段写入：先 `Write` 到「规范级别」章节，再 `Edit` 追加其余章节。完整内容：

```markdown
# .NET 高级调试知识库

> 版本：1.0.0

> 面向 **.NET 应用事后诊断与定位**的知识库。覆盖 .NET Framework 4.x、.NET 6/8+ 与 Linux 容器三种运行时，收录从运行中进程或 dump 中取证的命令、输出解读与判据。

本领域负责「程序已经出问题之后，如何取证并定位根因」。预防性的编码规范不在本领域——那属于 `knowledge-base/csharp/` 与 `knowledge-base/wpf/`。

## 文档目的

让排查者能按「征象 → 候选根因 → 取证命令 → 输出解读 → 判据」这条链路自助定位问题，而不必每次依赖个人经验重新摸索。目标读者读完 `reference/debugging-decision-tree.md` 即可确定该用哪条命令，再按命令条目读懂输出含义。

## 适用范围与读者

- **适用范围**：生产或测试环境出现内存持续增长、进程挂起、CPU 打满、崩溃退出、句柄耗尽等问题时的诊断取证
- **读者**：需要定位 .NET 应用运行期问题的开发与运维人员；本领域一期无固定 skill 消费者

## 收录判据

**单命令粒度进知识库，多命令编排进 skill。**

检验标准：这条内容能独立成为一个「查一下就照着用」的条目吗？能 → 本领域。它是否必须知道「上一步做了什么」才有意义？是 → 属 skill，不收。

据此，抓取 dump 的完整命令行（`procdump`、`dotnet-dump collect`、`createdump` 等）**收录**——单条可查；而「先判断征象 → 决定抓哪种 dump → 引导装工具 → 抓 → 分析 → 回报」这条编排**不收**。

## 与既有领域的边界

| 已有资产 | 它负责 | 本领域负责 | 切线 |
|---|---|---|---|
| `knowledge-base/csharp/rules/06-memory-resource.md` § 4 / § 6 / § 9 | 怎么写才不泄漏 | 已经泄漏了，如何在托管堆里认出它 | 写代码时 vs 读现场时 |
| `knowledge-base/csharp/rules/11-observability.md` § 7 | 应用内部该埋什么指标 | 从外部读取运行中进程的计数器与事件流 | 埋点 vs 采集 |
| `knowledge-base/wpf/rules/12-exceptions-crash.md` § 1–3 | 怎么捕获并优雅退出 | 崩溃 dump 里如何找到抛出点与第一现场 | 兜住 vs 验尸 |
| `knowledge-base/dotnet/` | 目标框架能跑在哪 | 目标框架决定用哪套工具链 | 能不能跑 vs 用什么诊断 |

引用单向：本领域正文可指向上述领域，被指向方不反向声明。

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义，与 `knowledge-base/csharp/README.md` 同一套定义。

| 级别 | 措辞 | 含义 |
|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 |
| **建议 MAY** | "可以"、"建议" | 可选做法，不强制 |

本领域仅 `rules/01-dump-handling.md` 一篇规范文件，其余为 `reference/` 描述性内容。调试知识绝大多数是判据而非规范——"内存涨了应该先看 `!dumpheap -stat`" 是判据不是规则，写成 rule 即是假规范。

## 阅读路径

| 场景 | 参考文档 |
|---|---|
| 不知道从哪下手，先定位问题类别 | `reference/debugging-decision-tree.md` |
| 读懂命令输出前的术语基础 | `reference/clr-runtime-anatomy.md` |
| 决定抓哪种 dump | `reference/dump-types-and-capability.md` |
| 实际抓取 dump | `reference/dump-capture.md` |
| 命令报错、符号加载不出来 | `reference/symbols-and-tool-matching.md` |
| 进程挂起 / 查线程在等什么 | `reference/sos-threads-and-stacks.md` |
| 内存持续增长 / 找泄漏持有者 | `reference/sos-heap-and-objects.md` |
| 死锁 / 异步卡住 / 线程池饥饿 | `reference/sos-locks-and-async.md` |
| 处理生产 dump 文件（合规） | `rules/01-dump-handling.md` |

## 文件地图

| 文件 | 主题 |
|---|---|

## 内容来源

- **主干**：微软官方诊断文档（learn.microsoft.com 的 .NET diagnostics 专区）与 `dotnet/diagnostics` 仓库
- **深度补充**：《Advanced .NET Debugging》等书籍知识体系（CLR 内部、GC 堆结构、同步块表）。凡出自该来源且无官方文档佐证的内容，正文中标注为经验性知识

## 索引与机器消费

本领域 `index.jsonl` **按命令/征象分片登记**，而非按整篇文档登记——调试知识天然按这两个维度被检索。字段说明与维护约定见 `knowledge-base/README.md`。

`applies_to` 在本领域对 `reference` 条目**同样必填**：同一条命令在不同运行时的可用性不同（`!dumpasync` 需较新 SOS、`procdump` 仅 Windows、`createdump` 仅 .NET Core+），不标运行时等于没给出可用信息。

## 更新与维护

- 新增/修改内容时，同一次提交里同步更新 `index.jsonl`
- 改动后运行 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
- 每条命令条目遵循四段固定结构：用途与前置条件 / 语法与关键开关 / 输出逐列语义 / 判据（能证实或排除什么假设）
```

注意「文件地图」表格此时只有表头，后续 Task 各自补自己那行。

- [ ] **Step 4: 写 `CHANGELOG.md`**

```markdown
# Changelog — .NET 高级调试

## [1.0.0] - 2026-09-05

### Added
- 新建 `dotnet-debugging` 领域：8 篇 reference（调试决策树、CLR 运行时结构、dump 类型与能力、dump 抓取、符号与工具匹配、SOS 线程与栈、SOS 堆与对象、SOS 锁与异步）+ 1 篇规范文件（dump 处置）
- 覆盖 .NET Framework 4.x、.NET 6/8+、Linux 容器三种运行时的共性层
- 索引按命令/征象分片登记，支撑 skill 精确检索
```

- [ ] **Step 5: 注册到 `catalog.json`**

在 `domains` 数组**末尾**（`mcp` 条目之后）追加，注意前一条要补逗号：

```json
    {
      "domain": "dotnet-debugging",
      "title": ".NET 高级调试与诊断",
      "categories": ["rules", "reference"],
      "owner": "desktop client team",
      "status": "active",
      "consumers": [],
      "reviewed_at": "2026-09-05",
      "notes": "事后诊断与定位：征象判据、CLR 可观测结构、dump 抓取与分析命令、SOS 输出解读。覆盖 .NET Framework 4.x / .NET 6+ / Linux 容器三运行时的共性层；预防性编码规范归 csharp 与 wpf，平台生命周期归 dotnet。一期不含活体监控工具（PerfView/ETW/dotnet-counters）与 WPF 专属归因"
    }
```

- [ ] **Step 6: 更新知识库根 `README.md`**

改两处。第 3 行领域列表，把 `、\`mcp\`` 之后补上新域（保持原句其余部分不变）：

```
当前收纳领域：`dotnet`、`csharp`、`wpf`、`git`、`media`、`skill-authoring`、`architecture`、`design-patterns`、`data-structures-algorithms`、`mcp`、`dotnet-debugging`。
```

第 29 行「领域职责边界」长句末尾，在 `data-structures-algorithms 负责...` 之后追加一句：

```
`dotnet-debugging` 负责程序出问题后的取证与定位（征象判据、CLR 可观测结构、dump 与 SOS 命令解读），与 `csharp`/`wpf` 的预防性规范互补而不重叠。
```

- [ ] **Step 7: 跑校验确认通过**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS。若报「孤儿文件」指向 `.gitkeep`，改为删除 `.gitkeep` 并接受空目录不入 git（后续 Task 会填入真实文件）。

同时跑全局校验确认没破坏既有领域：

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"`
Expected: PASS，记录数仍为 502（本 Task 未加索引条目）。

- [ ] **Step 8: 提交**

```bash
git add knowledge-base/dotnet-debugging knowledge-base/catalog.json knowledge-base/README.md
git commit -m "$(cat <<'EOF'
docs(kb): 新建 dotnet-debugging 领域骨架

- 建领域目录、README（含边界表与收录判据）、CHANGELOG 1.0.0
- 注册到 catalog.json，同步知识库根 README 领域列表与职责边界

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: CLR 运行时可观测结构

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/clr-runtime-anatomy.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 7 条）
- Modify: `knowledge-base/dotnet-debugging/README.md`（「文件地图」表格加 1 行）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging --audit`

**Interfaces:**
- Consumes: Task 1 产出的领域目录与空 `index.jsonl`
- Produces: 七个中文小节标题，后续 Task 5–7 的命令条目用 `source` 指向它们。**标题文本必须逐字为**：
  - `## 1. 托管堆分代结构`
  - `## 2. 大对象堆（LOH）与固定对象堆（POH）`
  - `## 3. 同步块表`
  - `## 4. 终结队列`
  - `## 5. 线程池内部结构`
  - `## 6. GC 模式`
  - `## 7. 句柄表`

后续 Task 写 `source` 时形式为 `reference/clr-runtime-anatomy.md#3. 同步块表`（`check_index.py` 做子串匹配，写 `#3. 同步块表` 即可命中）。

- [ ] **Step 1: 先写索引条目，跑校验看它失败**

把 7 条追加到 `index.jsonl`（此时正文尚未创建，校验应报文件不存在）：

```jsonl
{"id": "dotnet-debugging.ref.managed-heap-generations", "kind": "reference", "file": "reference/clr-runtime-anatomy.md", "anchor": "1. 托管堆分代结构", "title": "托管堆分代结构：gen0/gen1/gen2 与晋升", "tags": ["gc", "managed-heap", "generation", "promotion", "segment"], "summary": "托管堆三代结构、对象晋升条件、段与区域（segment/region）布局，以及各代回收触发时机。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.loh-poh", "kind": "reference", "file": "reference/clr-runtime-anatomy.md", "anchor": "2. 大对象堆（LOH）与固定对象堆（POH）", "title": "大对象堆与固定对象堆：85000 字节阈值与碎片形态", "tags": ["loh", "poh", "large-object", "fragmentation", "pinning"], "summary": "LOH 的 85000 字节阈值、默认不压缩导致的碎片形态，以及 POH 承载固定对象的用途。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.sync-block-table", "kind": "reference", "file": "reference/clr-runtime-anatomy.md", "anchor": "3. 同步块表", "title": "同步块表：对象头、瘦锁膨胀与 Monitor 归属", "tags": ["syncblock", "monitor", "lock", "object-header", "thin-lock"], "summary": "对象头指向同步块的机制、瘦锁膨胀为同步块的条件，以及同步块记录的持有线程与等待队列——死锁判定的数据来源。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.finalization-queue", "kind": "reference", "file": "reference/clr-runtime-anatomy.md", "anchor": "4. 终结队列", "title": "终结队列与 F-Reachable 队列：两阶段回收", "tags": ["finalizer", "freachable", "gc", "dispose", "queue-backlog"], "summary": "终结队列与 F-Reachable 队列的分工、终结器线程单线程串行执行的后果，以及队列积压如何表现为内存无法回收。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.threadpool-internals", "kind": "reference", "file": "reference/clr-runtime-anatomy.md", "anchor": "5. 线程池内部结构", "title": "线程池内部结构：工作队列、爬坡算法与注入速率", "tags": ["threadpool", "work-queue", "hill-climbing", "starvation", "thread-injection"], "summary": "全局队列与本地队列的分工、爬坡算法的线程注入速率上限，以及饥饿为何表现为延迟阶梯式上升而非线性劣化。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.gc-modes", "kind": "reference", "file": "reference/clr-runtime-anatomy.md", "anchor": "6. GC 模式", "title": "GC 模式：工作站/服务器 × 并发/后台", "tags": ["gc-mode", "workstation-gc", "server-gc", "background-gc", "gc-pause"], "summary": "工作站与服务器 GC 的堆数量与线程差异、后台 GC 对暂停时间的影响，以及如何从 dump 判断当前进程用的哪种模式。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.handle-table", "kind": "reference", "file": "reference/clr-runtime-anatomy.md", "anchor": "7. 句柄表", "title": "句柄表：强/弱/固定句柄与非托管泄漏线索", "tags": ["gc-handle", "strong-handle", "weak-handle", "pinned-handle", "handle-leak"], "summary": "四类 GC 句柄的语义与生命周期影响，句柄数持续增长如何指向 COM 互操作或固定缓冲区泄漏。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
```

- [ ] **Step 2: 跑校验验证失败**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，7 条均报 `file` 引用的文件不存在（`reference/clr-runtime-anatomy.md`）。这确认索引已被读取且路径校验生效。

- [ ] **Step 3: 分段写正文**

先 `Write` 文件头与第 1–2 节，再 `Edit` 逐节追加 3–7 节。禁止单次写完整篇。

文件头固定为：

```markdown
# CLR 运行时可观测结构

> 本篇解释在 dump 或运行中进程里**能观察到什么**，以及各结构的语义。它是读懂 `sos-*` 系列命令输出的术语基础——命令输出的每一列都对应本篇的某个结构。

本篇不含命令，只含结构。命令见 `reference/sos-threads-and-stacks.md`、`reference/sos-heap-and-objects.md`、`reference/sos-locks-and-async.md`。

预防侧的编码规范（如何避免泄漏、如何正确实现 IDisposable）见 `knowledge-base/csharp/rules/06-memory-resource.md`。
```

每节须包含：结构的用途、在 dump 中的可观测形态、以及**该结构异常时对应什么征象**（最后一点是 `debugging-decision-tree.md` 的输入）。

第 3 节「同步块表」正文中须写明：对象头 4/8 字节中的同步块索引、瘦锁（thin lock）在无竞争时直接存 ThreadId、发生竞争或调用 `GetHashCode`/`Wait` 时膨胀为同步块。这是 `!syncblk` 输出的直接依据。

第 5 节「线程池内部结构」正文须交叉引用 `knowledge-base/csharp/rules/04-async-programming.md`（异步编码规范），说明"饥饿的成因在那边，饥饿的识别在本篇"。

- [ ] **Step 4: 跑校验确认通过**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS。若报 anchor 未匹配，核对正文标题文本与索引 `anchor` 是否逐字一致（含全角括号与空格）。

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging --audit`
Expected: 输出 `kind` 分布含 7 条 reference，无孤儿文件。

- [ ] **Step 5: 补 README 文件地图**

在 Task 1 建好的空表格里加第一行：

```markdown
| `reference/clr-runtime-anatomy.md` | 托管堆分代、LOH/POH、同步块表、终结队列、线程池结构、GC 模式、句柄表 |
```

- [ ] **Step 6: 跑跨领域查重**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"`
Expected: 输出中**不应**出现 `dotnet-debugging.ref.*` 与 `csharp.06.*` 的高相似度对（≥ 0.5）。若出现，说明本篇写成了预防规范而非结构描述，须改写正文——本篇只描述结构是什么，不写"应该怎么做"。

- [ ] **Step 7: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/clr-runtime-anatomy.md knowledge-base/dotnet-debugging/index.jsonl knowledge-base/dotnet-debugging/README.md
git commit -m "$(cat <<'EOF'
docs(kb): dotnet-debugging 新增 CLR 运行时可观测结构

- 7 个结构小节：分代堆、LOH/POH、同步块表、终结队列、线程池、GC 模式、句柄表
- 索引 7 条，为后续 SOS 命令篇目提供 source 锚点

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: dump 类型与抓取

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/dump-types-and-capability.md`
- Create: `knowledge-base/dotnet-debugging/reference/dump-capture.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 6 条：1 + 5）
- Modify: `knowledge-base/dotnet-debugging/README.md`（文件地图加 2 行）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`

**Interfaces:**
- Consumes: Task 2 的 `reference/clr-runtime-anatomy.md#1. 托管堆分代结构`（heap-only dump 保留什么、triage 剥离什么，须用分代堆术语说明）
- Produces:
  - `dump-types-and-capability.md` 整篇作为一个条目，无小节 anchor（`anchor` 填空字符串）。Task 9 的 rules 正文引用四个类型名，**类型名逐字固定为**：`Mini`、`Heap`、`Triage`、`Full`（与 `dotnet-dump collect --type` 取值一致）
  - `dump-capture.md` 五个小节标题，Task 8 决策树指向它们。**标题文本逐字为**：
    - `## 1. procdump（Windows，全运行时）`
    - `## 2. dotnet-dump collect（.NET Core 3.0+，跨平台）`
    - `## 3. createdump（.NET Core 3.0+，Linux 优先）`
    - `## 4. WER LocalDumps（Windows，崩溃自动抓取）`
    - `## 5. DOTNET_DbgEnableMiniDump（.NET Core 3.0+，崩溃自动抓取）`

- [ ] **Step 1: 先写索引，跑校验看失败**

追加 6 条到 `index.jsonl`：

```jsonl
{"id": "dotnet-debugging.ref.dump-types-capability", "kind": "reference", "file": "reference/dump-types-and-capability.md", "anchor": "", "title": "dump 类型与取证能力：Mini/Heap/Triage/Full 各能答什么", "tags": ["dump-type", "minidump", "full-dump", "triage-dump", "heap-dump", "bitness", "snapshot"], "summary": "四种 dump 类型各自保留与剥离的数据、能回答与不能回答的问题、位数匹配约束，以及 dump 作为单时点快照的固有局限。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.procdump", "kind": "reference", "file": "reference/dump-capture.md", "anchor": "1. procdump", "title": "procdump：Windows 全运行时通用抓取工具", "tags": ["procdump", "capture", "sysinternals", "crash-trigger", "hang-trigger", "cpu-trigger"], "summary": "procdump 的完整命令与关键开关（-ma 全内存、-e 首次异常、-h 挂起、-c CPU 阈值、-n 连抓次数），及各触发条件的适用场景。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"]}
{"id": "dotnet-debugging.ref.dotnet-dump-collect", "kind": "reference", "file": "reference/dump-capture.md", "anchor": "2. dotnet-dump collect", "title": "dotnet-dump collect：跨平台抓取与类型选择", "tags": ["dotnet-dump", "capture", "cross-platform", "dump-type", "diagnostic-port"], "summary": "dotnet-dump collect 的安装、进程定位与 --type 取值语义；与 analyze 子命令的关系及其相对 WinDbg 的能力边界。", "applies_to": [".NET 6+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.createdump", "kind": "reference", "file": "reference/dump-capture.md", "anchor": "3. createdump", "title": "createdump：容器内抓取与 PID namespace 约束", "tags": ["createdump", "capture", "container", "pid-namespace", "linux", "ptrace"], "summary": "运行时自带 createdump 的路径定位与开关；容器场景下 PID namespace 与 ptrace 权限（SYS_PTRACE）的前置约束。", "applies_to": [".NET 6+", "Linux"]}
{"id": "dotnet-debugging.ref.wer-localdumps", "kind": "reference", "file": "reference/dump-capture.md", "anchor": "4. WER LocalDumps", "title": "WER LocalDumps：Windows 崩溃自动抓取的注册表配置", "tags": ["wer", "localdumps", "registry", "crash-dump", "auto-capture", "unattended"], "summary": "WER LocalDumps 注册表键路径与 DumpType/DumpFolder/DumpCount 取值；进程退出即消失、无法手动介入场景下的唯一取证手段。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"]}
{"id": "dotnet-debugging.ref.dbgenableminidump", "kind": "reference", "file": "reference/dump-capture.md", "anchor": "5. DOTNET_DbgEnableMiniDump", "title": "DOTNET_DbgEnableMiniDump：运行时级崩溃自动抓取", "tags": ["dbgenableminidump", "environment-variable", "crash-dump", "auto-capture", "container", "unhandled-exception"], "summary": "DOTNET_DbgEnableMiniDump 及配套变量（DbgMiniDumpType/DbgMiniDumpName）的取值；容器内崩溃取证的首选，与 WER 的适用差异。", "applies_to": [".NET 6+", "Windows", "Linux"]}
```

- [ ] **Step 2: 跑校验验证失败**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，6 条报文件不存在。

- [ ] **Step 3: 分段写 `dump-types-and-capability.md`**

文件头 + 一张主表 + 位数与时点性两节。核心是那张能力表，须逐类型写明**不能答什么**（这是选型的真正依据）：

```markdown
# dump 类型与取证能力

> 选错 dump 类型是排查中最贵的返工——拿到一个 Triage dump 却要查内存泄漏，只能重抓，而故障现场可能已经消失。本篇给出四种类型的取证能力边界。

抓取命令见 `reference/dump-capture.md`；dump 文件的合规处置见 `rules/01-dump-handling.md`。

## 1. 四种类型的能力对照

| 类型 | 保留 | 剥离 | 能答 | 不能答 | 体积量级 |
|---|---|---|---|---|---|
| `Mini` | 线程栈、模块列表、寄存器 | 堆对象数据 | 崩溃在哪行、线程在等什么 | 任何涉及对象内容的问题 | MB |
| `Heap` | 上述 + 托管堆对象 | 部分非托管内存 | 内存泄漏、对象数量异常 | 非托管内存泄漏 | 数百 MB |
| `Triage` | 线程栈 + 已脱敏的有限信息 | 堆对象数据、字符串内容 | 崩溃位置、线程状态 | 对象内容、泄漏归属 | MB |
| `Full` | 整个进程地址空间 | 无 | 全部 | —— | 等同进程内存占用 |
```

后续小节须包含：`## 2. 位数必须匹配`（32 位进程的 dump 必须用 32 位调试器加载，WOW64 下抓错位数会得到无法解析的托管栈）、`## 3. dump 是单时点快照`（不能答"何时开始涨""涨速多快"，那类问题需要时间线采样——一期不含，见二期路标）。

第 3 节须明确指向 `reference/debugging-decision-tree.md` 的「间歇抖动」分支，说明该类问题 dump 答不了。

- [ ] **Step 4: 分段写 `dump-capture.md`**

五节，每节四段结构（用途与前置条件 / 语法与关键开关 / 输出与产物位置 / 判据）。**必须写出完整可执行命令**，这是本领域相对 `media` 领域的关键差异。第 1 节示范：

````markdown
## 1. procdump（Windows，全运行时）

### 用途与前置条件
Sysinternals 工具，需单独下载。对 .NET Framework 4.x 与 .NET 6+ 同等适用，是 Windows 上唯一覆盖全部运行时的抓取工具。首次运行需接受 EULA（`-accepteula`），自动化场景必带。

### 语法与关键开关

抓挂起进程（进程无响应，手动介入）：
```
procdump -accepteula -ma <PID>
```

崩溃时自动抓（等待首次机会异常）：
```
procdump -accepteula -ma -e 1 -f "" -w <进程名>
```

CPU 打满时抓（超过 80% 持续 5 秒，连抓 3 个）：
```
procdump -accepteula -ma -c 80 -s 5 -n 3 <PID>
```

| 开关 | 含义 | 不加的后果 |
|---|---|---|
| `-ma` | 全内存 dump | 默认只抓 mini，无堆数据，查不了泄漏 |
| `-e 1` | 首次机会异常即抓 | 只抓未处理异常，被 catch 吞掉的问题抓不到 |
| `-w` | 等待进程出现 | 只能抓已运行进程，启动即崩的场景抓不到 |
| `-n <次数>` | 连抓 N 个 | 只抓 1 个，无法对比不同时刻的堆增长 |

### 输出与产物位置
默认落在当前工作目录，文件名形如 `<进程名>_<日期>_<时间>.dmp`。`-n` 连抓时自动编号。

### 判据
`-n 3` 连抓多个 dump 后对比 `!dumpheap -stat` 输出，是**在没有时间线采样工具时**判断"哪类对象在涨"的替代手段——这是一期能给出的最接近趋势分析的做法。
````

其余四节同构。第 3 节 `createdump` 必须写明容器内两个前置条件：目标进程与调试器在同一 PID namespace、容器需 `SYS_PTRACE` capability。第 4/5 节须说明**二者的选择依据**：WER 是 Windows 系统级、对所有进程生效；`DOTNET_DbgEnableMiniDump` 是运行时级、只对 .NET Core+ 且可按进程配置，容器内首选后者。

- [ ] **Step 5: 跑校验确认通过**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS。

注意：`dump-types-and-capability.md` 的 `anchor` 为空字符串，校验器跳过锚点检查——这是整篇登记的正常形态（`mcp` 领域全部 reference 如此）。

- [ ] **Step 6: 补 README 文件地图两行**

```markdown
| `reference/dump-types-and-capability.md` | 四种 dump 类型的取证能力边界、位数匹配、快照时点性 |
| `reference/dump-capture.md` | procdump / dotnet-dump collect / createdump / WER LocalDumps / DOTNET_DbgEnableMiniDump 的完整命令与开关 |
```

- [ ] **Step 7: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/dump-types-and-capability.md knowledge-base/dotnet-debugging/reference/dump-capture.md knowledge-base/dotnet-debugging/index.jsonl knowledge-base/dotnet-debugging/README.md
git commit -m "$(cat <<'EOF'
docs(kb): dotnet-debugging 新增 dump 类型与抓取

- dump 类型能力对照表，逐类型写明不能回答什么
- 五种抓取工具的完整命令与开关语义，覆盖三运行时
- 索引 6 条

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: 符号与工具匹配

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/symbols-and-tool-matching.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 4 条）
- Modify: `knowledge-base/dotnet-debugging/README.md`（文件地图加 1 行）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`

**Interfaces:**
- Consumes: Task 3 的 `reference/dump-types-and-capability.md`（位数匹配一节，本篇的 SOS 版本匹配与之互补）
- Produces: 四个小节标题，Task 5–7 的每条命令在「用途与前置条件」段落统一指向本篇。**标题文本逐字为**：
  - `## 1. PDB 类型：portable 与 Windows PDB`
  - `## 2. 符号服务器与符号缓存`
  - `## 3. SOS 与运行时版本匹配`
  - `## 4. 缺符号时的降级读法`

- [ ] **Step 1: 先写索引，跑校验看失败**

```jsonl
{"id": "dotnet-debugging.ref.pdb-types", "kind": "reference", "file": "reference/symbols-and-tool-matching.md", "anchor": "1. PDB 类型", "title": "PDB 类型：portable PDB 与 Windows PDB 的差异", "tags": ["pdb", "portable-pdb", "symbols", "deterministic-build", "sourcelink"], "summary": "portable PDB 与 Windows PDB 的格式差异与调试器支持情况、嵌入式 PDB 的取舍，以及 SourceLink 如何让 dump 分析定位到源码行。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.symbol-server", "kind": "reference", "file": "reference/symbols-and-tool-matching.md", "anchor": "2. 符号服务器与符号缓存", "title": "符号服务器与符号缓存：_NT_SYMBOL_PATH 配置", "tags": ["symbol-server", "symbol-cache", "msdl", "nt-symbol-path", "dotnet-symbol"], "summary": "微软公共符号服务器地址、_NT_SYMBOL_PATH 的取值语法与本地缓存目录，以及 dotnet-symbol 为 Linux dump 补齐符号的用法。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.sos-version-matching", "kind": "reference", "file": "reference/symbols-and-tool-matching.md", "anchor": "3. SOS 与运行时版本匹配", "title": "SOS 与运行时版本匹配：加载方式与版本错配征象", "tags": ["sos", "loadby", "dotnet-sos", "version-mismatch", "dac", "setclrpath"], "summary": "三运行时下 SOS 的加载方式（.loadby sos clr / dotnet-sos install / dotnet-dump analyze 内置）、DAC 与运行时版本必须匹配的原因，以及版本错配的典型报错。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.missing-symbols-fallback", "kind": "reference", "file": "reference/symbols-and-tool-matching.md", "anchor": "4. 缺符号时的降级读法", "title": "缺符号时的降级读法：托管栈仍可读、非托管栈退化", "tags": ["missing-symbols", "fallback", "managed-stack", "unmanaged-stack", "method-table"], "summary": "缺符号时哪些信息仍然可靠（托管方法名来自元数据而非 PDB）、哪些退化为地址（非托管帧、行号），以及据此判断值不值得补符号重新分析。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
```

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，4 条报文件不存在。

- [ ] **Step 2: 分段写正文**

文件头须点明本篇的定位——它是**前置条件篇**，命令报错先查这里：

```markdown
# 符号与工具匹配

> SOS 命令报错、方法名显示为地址、`!clrstack` 输出空栈——这类问题九成不是分析思路错了，而是符号或 SOS 版本没配对。本篇是全部 `sos-*` 命令的前置条件。

dump 位数匹配见 `reference/dump-types-and-capability.md § 2. 位数必须匹配`，本篇只讲符号与 SOS 版本。
```

第 3 节是本篇重点，须给出三运行时的完整加载命令：

````markdown
## 3. SOS 与运行时版本匹配

### .NET Framework 4.x（WinDbg）
```
.loadby sos clr
```
`clr` 是 4.x 的运行时模块名（2.0 时代是 `mscorwks`）。`.loadby` 从已加载的运行时模块所在目录取同版本 SOS，这正是它比手动 `.load` 可靠的原因。

### .NET 6/8+（WinDbg 或 lldb）
```
dotnet-sos install
```
一次安装写入调试器配置，后续自动加载。

### .NET 6/8+（dotnet-dump，推荐）
```
dotnet-dump analyze <dump 文件>
```
内置 SOS，无需单独加载；命令前缀可省略 `!`（`dumpheap -stat` 与 `!dumpheap -stat` 等价）。
````

同节须写明 DAC（`mscordacwks.dll` / `libmscordaccore.so`）必须与产生 dump 的运行时**完全同版本**，以及版本错配的确切报错文本形态与 `!setclrpath` 的补救用法。

第 4 节须给出可操作的判断：托管方法名来自**元数据**不依赖 PDB，所以缺符号时 `!clrstack` 仍能显示方法名，只是没有行号；而非托管帧会退化为纯地址。据此判断"当前问题需不需要补符号"——若结论只依赖托管栈，不必补。

- [ ] **Step 3: 跑校验确认通过**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS，累计 17 条记录（7 + 6 + 4）。

- [ ] **Step 4: 补 README 文件地图**

```markdown
| `reference/symbols-and-tool-matching.md` | PDB 类型、符号服务器配置、SOS 与运行时版本匹配、缺符号降级读法 |
```

- [ ] **Step 5: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/symbols-and-tool-matching.md knowledge-base/dotnet-debugging/index.jsonl knowledge-base/dotnet-debugging/README.md
git commit -m "$(cat <<'EOF'
docs(kb): dotnet-debugging 新增符号与工具匹配

- PDB 类型、符号服务器、SOS 三运行时加载方式、缺符号降级读法
- 作为全部 SOS 命令篇目的前置条件篇
- 索引 4 条

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: SOS 线程与栈命令

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/sos-threads-and-stacks.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 5 条）
- Modify: `knowledge-base/dotnet-debugging/README.md`（文件地图加 1 行）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`

**Interfaces:**
- Consumes: `reference/clr-runtime-anatomy.md#5. 线程池内部结构`（Task 2）、`reference/symbols-and-tool-matching.md#3. SOS 与运行时版本匹配`（Task 4）
- Produces: **四段结构范式**，Task 6 与 Task 7 逐字复用。每条命令的小节结构固定为：

```
## N. !命令名
### 用途与前置条件
### 语法与关键开关
### 输出逐列语义
### 判据：能证实 / 排除什么
```

本篇五个小节标题**逐字为**：`## 1. !threads`、`## 2. !clrstack`、`## 3. !dumpstack`、`## 4. !pe`、`## 5. !dso`。Task 8 决策树按这些 anchor 指向。

- [ ] **Step 1: 先写索引，跑校验看失败**

```jsonl
{"id": "dotnet-debugging.ref.threads", "kind": "reference", "file": "reference/sos-threads-and-stacks.md", "anchor": "1. !threads", "title": "!threads：托管线程全景与异常标记", "tags": ["threads", "thread-list", "hang", "apartment", "gc-mode", "pending-exception"], "summary": "!threads 输出的线程 ID、锁计数、APT 模型、GC 模式与 Exception 列语义；进程挂起时定位可疑线程的第一条命令。", "applies_to": [".NET Framework 4.x", ".NET 6+"], "source": ["reference/clr-runtime-anatomy.md#5. 线程池内部结构"]}
{"id": "dotnet-debugging.ref.clrstack", "kind": "reference", "file": "reference/sos-threads-and-stacks.md", "anchor": "2. !clrstack", "title": "!clrstack：托管调用栈与局部变量", "tags": ["clrstack", "call-stack", "managed-stack", "locals", "parameters", "hang"], "summary": "!clrstack 的 -a/-l/-p 开关语义、托管栈帧读法，以及缺符号时仍能显示方法名的原因。", "applies_to": [".NET Framework 4.x", ".NET 6+"], "source": ["reference/symbols-and-tool-matching.md#4. 缺符号时的降级读法"]}
{"id": "dotnet-debugging.ref.dumpstack", "kind": "reference", "file": "reference/sos-threads-and-stacks.md", "anchor": "3. !dumpstack", "title": "!dumpstack：托管与非托管栈交错读法", "tags": ["dumpstack", "unmanaged-stack", "interop", "pinvoke", "transition-frame"], "summary": "!dumpstack 同时显示托管与非托管帧的用途；托管/非托管转换帧的识别，以及 P/Invoke 卡在原生调用时的定位方式。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.printexception", "kind": "reference", "file": "reference/sos-threads-and-stacks.md", "anchor": "4. !pe", "title": "!pe：异常对象与内部异常链", "tags": ["printexception", "exception", "inner-exception", "crash", "stack-trace", "hresult"], "summary": "!pe 打印异常对象的消息、HRESULT、栈轨迹与 InnerException 链；-nested 遍历嵌套异常，崩溃 dump 定位第一现场的核心命令。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.dso", "kind": "reference", "file": "reference/sos-threads-and-stacks.md", "anchor": "5. !dso", "title": "!dso：栈上对象枚举", "tags": ["dso", "dumpstackobjects", "stack-objects", "local-variable", "object-address"], "summary": "!dso 枚举当前线程栈上的所有托管对象引用；在 !clrstack -a 无法解析局部变量时的替代取证手段。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
```

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，5 条报文件不存在。**同时确认 `source` 字段的领域内引用被校验**——若 Task 2/Task 4 的锚点写错，这里会一并报出。

- [ ] **Step 2: 分段写正文，第 1 节确立范式**

文件头：

```markdown
# SOS 命令：线程与栈

> 本篇覆盖「谁在跑、卡在哪、崩在哪」三类问题的取证命令。命令在三种运行时下同名同语义，差异只在 SOS 的加载方式——见 `reference/symbols-and-tool-matching.md § 3. SOS 与运行时版本匹配`。

命令名前的 `!` 是 WinDbg 的扩展命令前缀。在 `dotnet-dump analyze` 中可省略。
```

第 1 节完整范式（后续所有命令小节照此写）：

````markdown
## 1. !threads

### 用途与前置条件
列出全部托管线程。进程挂起、无响应、CPU 打满时的**第一条命令**——它给出线程全景，后续用 `!clrstack` 深入某条可疑线程。任何类型的 dump 都支持（Mini/Triage 亦可）。

### 语法与关键开关
```
!threads
!threads -live      # 只列活动线程，过滤已终止的
!threads -special   # 含运行时内部线程（GC、终结器、调试器）
```

`-special` 在排查终结器卡死时必用——终结器线程不在默认输出里。

### 输出逐列语义

| 列 | 含义 | 异常信号 |
|---|---|---|
| `ID` | CLR 内部线程序号 | —— |
| `OSID` | 操作系统线程 ID（十六进制） | 用于 `~~[OSID]s` 切换线程 |
| `ThreadOBJ` | Thread 对象地址 | 可用 `!dumpobj` 展开 |
| `State` | 线程状态位掩码 | —— |
| `GC Mode` | `Preemptive` / `Cooperative` | 大量 Cooperative 且 GC 进行中 = 线程在等 GC |
| `Lock Count` | 持有的锁数量 | **非零表示持锁，死锁排查的起点** |
| `APT` | COM 单元模型（STA/MTA） | WPF UI 线程应为 STA |
| `Exception` | 该线程上的待处理异常 | **非空即为崩溃第一现场候选** |

### 判据：能证实 / 排除什么
- `Lock Count` 全为 0 → **排除** Monitor 死锁，转查异步死锁（`!dumpasync`，见 `reference/sos-locks-and-async.md § 2. !dumpasync`）
- 线程数远超预期（数百）且多数栈相同 → **证实**线程池饥饿，转查 `reference/sos-locks-and-async.md § 3. !threadpool`
- `Exception` 列非空 → **证实**该线程有待处理异常，转 `§ 4. !pe` 展开
````

其余四节同构。第 4 节 `!pe` 须写明 `-nested` 开关与 InnerException 链的遍历方式，判据段落须指向 `knowledge-base/wpf/rules/12-exceptions-crash.md § 1. UI 线程异常`（说明"这条规范被违反时在 dump 里长什么样"）。

- [ ] **Step 3: 跑校验确认通过**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS，累计 22 条。

- [ ] **Step 4: 跑正文交叉引用校验**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"`
Expected: PASS。本篇正文引用了 `wpf/rules/12-exceptions-crash.md § 1. UI 线程异常`，该脚本校验章节号引用有效性。

- [ ] **Step 5: 补 README 文件地图**

```markdown
| `reference/sos-threads-and-stacks.md` | !threads / !clrstack / !dumpstack / !pe / !dso 的开关、输出逐列语义与判据 |
```

- [ ] **Step 6: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/sos-threads-and-stacks.md knowledge-base/dotnet-debugging/index.jsonl knowledge-base/dotnet-debugging/README.md
git commit -m "$(cat <<'EOF'
docs(kb): dotnet-debugging 新增 SOS 线程与栈命令

- 五条命令：!threads / !clrstack / !dumpstack / !pe / !dso
- 确立四段结构范式：用途与前置条件 / 语法与开关 / 输出逐列语义 / 判据
- 索引 5 条

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: SOS 堆与对象命令

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/sos-heap-and-objects.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 6 条）
- Modify: `knowledge-base/dotnet-debugging/README.md`（文件地图加 1 行）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`

**Interfaces:**
- Consumes: Task 5 确立的四段结构范式（逐字复用）；`reference/clr-runtime-anatomy.md` 的 `#1. 托管堆分代结构`、`#2. 大对象堆（LOH）与固定对象堆（POH）`、`#7. 句柄表`
- Produces: 六个小节标题，Task 8 决策树的「内存持续增长」分支指向它们。**逐字为**：`## 1. !dumpheap`、`## 2. !dumpobj`、`## 3. !objsize`、`## 4. !gcroot`、`## 5. !eeheap`、`## 6. !gchandles`

- [ ] **Step 1: 先写索引，跑校验看失败**

```jsonl
{"id": "dotnet-debugging.ref.dumpheap-stat", "kind": "reference", "file": "reference/sos-heap-and-objects.md", "anchor": "1. !dumpheap", "title": "!dumpheap：堆对象统计与类型筛选", "tags": ["dumpheap", "heap", "statistics", "memory-growth", "leak-triage", "type-filter"], "summary": "!dumpheap -stat 的三列输出（MT/Count/TotalSize）读法、-type/-mt/-min 筛选开关，以及多次抓取对比判断增长类型的方法。", "applies_to": [".NET Framework 4.x", ".NET 6+"], "source": ["reference/clr-runtime-anatomy.md#1. 托管堆分代结构"]}
{"id": "dotnet-debugging.ref.dumpobj", "kind": "reference", "file": "reference/sos-heap-and-objects.md", "anchor": "2. !dumpobj", "title": "!dumpobj：单对象字段展开", "tags": ["dumpobj", "object-fields", "method-table", "field-offset", "value-type"], "summary": "!dumpobj 展开对象各字段的偏移、类型与值；引用字段如何逐层下钻，以及值类型内联字段的读法。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.objsize", "kind": "reference", "file": "reference/sos-heap-and-objects.md", "anchor": "3. !objsize", "title": "!objsize：对象保留大小与引用图代价", "tags": ["objsize", "retained-size", "shallow-size", "object-graph", "memory-attribution"], "summary": "!objsize 计算对象及其可达引用图的总大小；与 !dumpheap 浅层大小的差异，以及在大对象图上的执行代价。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.gcroot", "kind": "reference", "file": "reference/sos-heap-and-objects.md", "anchor": "4. !gcroot", "title": "!gcroot：根路径追踪与泄漏持有者定位", "tags": ["gcroot", "root-path", "leak", "event-handler", "static-reference", "handle"], "summary": "!gcroot 输出的根路径读法（静态字段/栈/句柄三类根）、如何据此认出事件订阅未解绑与静态集合持有——内存泄漏定位的核心命令。", "applies_to": [".NET Framework 4.x", ".NET 6+"], "source": ["reference/clr-runtime-anatomy.md#7. 句柄表"]}
{"id": "dotnet-debugging.ref.eeheap", "kind": "reference", "file": "reference/sos-heap-and-objects.md", "anchor": "5. !eeheap", "title": "!eeheap：堆段布局与加载器堆", "tags": ["eeheap", "gc-segment", "loader-heap", "region", "committed-reserved", "assembly-leak"], "summary": "!eeheap -gc 显示各代段的提交与保留边界、-loader 显示加载器堆；程序集反复加载导致的加载器堆增长如何识别。", "applies_to": [".NET Framework 4.x", ".NET 6+"], "source": ["reference/clr-runtime-anatomy.md#1. 托管堆分代结构"]}
{"id": "dotnet-debugging.ref.gchandles", "kind": "reference", "file": "reference/sos-heap-and-objects.md", "anchor": "6. !gchandles", "title": "!gchandles：句柄统计与非托管泄漏线索", "tags": ["gchandles", "handle-statistics", "strong-handle", "pinned-handle", "com-interop", "handle-leak"], "summary": "!gchandles 按类型统计句柄数；固定句柄过多导致堆碎片、强句柄持续增长指向 COM 互操作未释放的判断依据。", "applies_to": [".NET Framework 4.x", ".NET 6+"], "source": ["reference/clr-runtime-anatomy.md#7. 句柄表"]}
```

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，6 条报文件不存在。

- [ ] **Step 2: 分段写正文**

文件头须点明本篇与 `csharp/06` 的分工（这是第 1 节边界表的落地）：

```markdown
# SOS 命令：堆与对象

> 本篇覆盖「内存为什么涨、涨的是什么、谁持有它」三类问题的取证命令。

预防侧的编码规范——如何正确实现 `IDisposable`、事件订阅为何要解绑、LOH 该如何规避——见 `knowledge-base/csharp/rules/06-memory-resource.md`。本篇讲的是**那些规范被违反之后，在堆里长什么样**。
```

六节全部遵循 Task 5 的四段结构。两处关键内容要求：

**第 1 节 `!dumpheap`** 的「输出逐列语义」须给出三列表（`MT` 方法表地址 / `Count` 实例数 / `TotalSize` 浅层总字节），并写明**按 TotalSize 排序看绝对量、按 Count 排序看泄漏**这条经验判据——数量异常比体积异常更能指向泄漏，因为泄漏的典型形态是同类对象无限累积。该判据出自书籍知识体系，须按 Global Constraints 标注为经验性知识。

**第 4 节 `!gcroot`** 是本篇最重要的一节，「判据」段落须逐条列出三类根对应的根因：

```markdown
### 判据：能证实 / 排除什么

| 根路径末端形态 | 指向的根因 | 对应规范 |
|---|---|---|
| 静态字段（`static var`） | 静态集合无限增长、静态缓存无淘汰 | `knowledge-base/csharp/rules/06-memory-resource.md § 5. 静态引用` |
| 事件的 `_invocationList` | 事件订阅未解绑，发布者存活导致订阅者无法回收 | `knowledge-base/csharp/rules/06-memory-resource.md § 4. 事件与委托泄漏` |
| `Pinned handle` | 固定对象未释放，常见于原生互操作缓冲区 | `reference/clr-runtime-anatomy.md § 7. 句柄表` |
| 无根路径（输出为空） | **排除**托管泄漏，转查非托管内存或句柄泄漏（`§ 6. !gchandles`） | —— |
```

注意末两行的引用符号——正文一律用 ` § `，只有索引 `source` 字段才用 `#`（见 Global Constraints 的对照表）。

- [ ] **Step 3: 跑校验确认通过**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS，累计 28 条。

- [ ] **Step 4: 跑查重确认未与 csharp/06 重复**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"`
Expected: `dotnet-debugging.ref.gcroot` 与 `csharp.06.*` 的相似度应低于 0.5。若超过，说明本篇写成了"应该解绑事件"的规范复述而非"未解绑在堆里的形态"，须改写——本篇不出现 MUST/SHOULD 措辞。

注意：`find_duplicates.py` 只比对 `rule` 条目（输出提示"共 N 条 rule 参与比对"），本篇全为 reference 可能不参与比对。若确认如此，改为人工核对：通读本篇，确认无一句是规范措辞。

- [ ] **Step 5: 补 README 文件地图**

```markdown
| `reference/sos-heap-and-objects.md` | !dumpheap / !dumpobj / !objsize / !gcroot / !eeheap / !gchandles 的开关、输出语义与泄漏判据 |
```

- [ ] **Step 6: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/sos-heap-and-objects.md knowledge-base/dotnet-debugging/index.jsonl knowledge-base/dotnet-debugging/README.md
git commit -m "$(cat <<'EOF'
docs(kb): dotnet-debugging 新增 SOS 堆与对象命令

- 六条命令：!dumpheap / !dumpobj / !objsize / !gcroot / !eeheap / !gchandles
- !gcroot 判据表把根路径形态映射到 csharp/06 的对应规范
- 索引 6 条

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: SOS 锁与异步命令

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/sos-locks-and-async.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 3 条）
- Modify: `knowledge-base/dotnet-debugging/README.md`（文件地图加 1 行）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`

**Interfaces:**
- Consumes: Task 5 的四段结构范式；`reference/clr-runtime-anatomy.md#3. 同步块表`、`#5. 线程池内部结构`
- Produces: 三个小节标题，**逐字为**：`## 1. !syncblk`、`## 2. !dumpasync`、`## 3. !threadpool`。二期的 WPF Dispatcher 死锁归因将直接引用这三节。

- [ ] **Step 1: 先写索引，跑校验看失败**

```jsonl
{"id": "dotnet-debugging.ref.syncblk", "kind": "reference", "file": "reference/sos-locks-and-async.md", "anchor": "1. !syncblk", "title": "!syncblk：Monitor 持有者与死锁判定", "tags": ["syncblk", "deadlock", "monitor", "lock-contention", "owning-thread", "waiting-threads"], "summary": "!syncblk 输出的 MonitorHeld、Owning Thread、Waiting Threads 列语义；据此构造等待图判定循环等待——Monitor 死锁的直接证据。", "applies_to": [".NET Framework 4.x", ".NET 6+"], "source": ["reference/clr-runtime-anatomy.md#3. 同步块表"]}
{"id": "dotnet-debugging.ref.dumpasync", "kind": "reference", "file": "reference/sos-locks-and-async.md", "anchor": "2. !dumpasync", "title": "!dumpasync：async 状态机还原与异步死锁", "tags": ["dumpasync", "async", "state-machine", "async-deadlock", "continuation", "task"], "summary": "!dumpasync 还原挂起的 async 状态机与延续链；异步死锁（同步等待异步）在栈上不可见、只能靠本命令定位的原因。", "applies_to": [".NET 6+"], "source": ["reference/clr-runtime-anatomy.md#5. 线程池内部结构"]}
{"id": "dotnet-debugging.ref.threadpool", "kind": "reference", "file": "reference/sos-locks-and-async.md", "anchor": "3. !threadpool", "title": "!threadpool：工作队列积压与饥饿判定", "tags": ["threadpool", "starvation", "work-queue", "cpu-utilization", "worker-thread", "completion-port"], "summary": "!threadpool 输出的 CPU 利用率、工作线程与完成端口线程数、队列长度；饥饿与 CPU 打满的区分判据。", "applies_to": [".NET Framework 4.x", ".NET 6+"], "source": ["reference/clr-runtime-anatomy.md#5. 线程池内部结构"]}
```

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，3 条报文件不存在。

- [ ] **Step 2: 分段写正文**

文件头：

```markdown
# SOS 命令：锁与异步

> 本篇覆盖「卡住了但 CPU 不高」这类问题的取证命令——死锁、异步挂起、线程池饥饿三种形态在表象上相似，判据不同。

异步编码规范（为何禁止 `.Result`、如何正确传播 `CancellationToken`）见 `knowledge-base/csharp/rules/04-async-programming.md`。本篇讲的是**违反之后在 dump 里的形态**。
```

三节遵循四段结构。两处关键要求：

**第 1 节 `!syncblk`** 的「判据」段须给出死锁判定的可操作步骤（这是判据不是编排，因为它在单条命令的输出内完成）：

```markdown
### 判据：能证实 / 排除什么

用输出构造等待图：每行给出「Owning Thread 持有该锁」与「Waiting Threads 在等该锁」。若存在线程 A 持锁 1 等锁 2、线程 B 持锁 2 等锁 1 的循环，**证实** Monitor 死锁。

- 输出为空或 `MonitorHeld` 全为 0 → **排除** Monitor 死锁，转 `§ 2. !dumpasync`（异步死锁不占用 Monitor）
- 单个锁的 Waiting Threads 极多但无循环 → **排除**死锁，**证实**锁竞争，属性能问题而非挂起
```

**第 2 节 `!dumpasync`** 必须写明其 `applies_to` 只含 `.NET 6+`——.NET Framework 的 SOS 无此命令，Framework 下排查异步死锁只能靠 `!dumpheap -type` 找 `Task` 与状态机对象手工还原。这条限制必须显式写出，否则 Framework 用户会以为命令不存在是环境问题。

- [ ] **Step 3: 跑校验确认通过**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS，累计 31 条。

- [ ] **Step 4: 补 README 文件地图**

```markdown
| `reference/sos-locks-and-async.md` | !syncblk / !dumpasync / !threadpool 的开关、输出语义与死锁/饥饿判据 |
```

- [ ] **Step 5: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/sos-locks-and-async.md knowledge-base/dotnet-debugging/index.jsonl knowledge-base/dotnet-debugging/README.md
git commit -m "$(cat <<'EOF'
docs(kb): dotnet-debugging 新增 SOS 锁与异步命令

- 三条命令：!syncblk / !dumpasync / !threadpool
- !syncblk 给出等待图死锁判定步骤，!dumpasync 标注 .NET 6+ 限制
- 索引 3 条

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: 调试决策树

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/debugging-decision-tree.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 6 条）
- Modify: `knowledge-base/dotnet-debugging/README.md`（文件地图加 1 行）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`

**Interfaces:**
- Consumes: **Task 2–7 的全部小节 anchor**。本篇是唯一指向全域的篇目，故排在命令篇之后——anchor 写错会在 Step 3 校验时暴露。
- Produces: 六个征象小节，未来 skill 的入口。**标题逐字为**：
  - `## 1. 进程挂起 / 无响应`
  - `## 2. 内存持续增长`
  - `## 3. CPU 打满`
  - `## 4. 崩溃退出`
  - `## 5. 间歇性抖动`
  - `## 6. 句柄 / 资源耗尽`

- [ ] **Step 1: 先写索引，跑校验看失败**

```jsonl
{"id": "dotnet-debugging.ref.symptom-hang", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "1. 进程挂起", "title": "征象：进程挂起 / 无响应的取证路径", "tags": ["hang", "unresponsive", "deadlock", "symptom", "triage"], "summary": "进程无响应时的候选根因（Monitor 死锁、异步死锁、线程池饥饿、长时间 GC）与各自的取证命令及区分判据。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.symptom-memory-growth", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "2. 内存持续增长", "title": "征象：内存持续增长的取证路径", "tags": ["memory-growth", "leak", "symptom", "triage", "loh", "unmanaged-memory"], "summary": "内存增长的候选根因（托管泄漏、LOH 碎片、非托管泄漏、加载器堆增长）与区分它们的命令序列入口。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.symptom-high-cpu", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "3. CPU 打满", "title": "征象：CPU 打满的取证路径", "tags": ["high-cpu", "spin", "gc-pressure", "symptom", "triage"], "summary": "CPU 打满的候选根因（业务热点、自旋等待、GC 压力、无限循环）与用连抓多个 dump 对比栈的区分方法。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.symptom-crash", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "4. 崩溃退出", "title": "征象：崩溃退出的取证路径", "tags": ["crash", "unhandled-exception", "stackoverflow", "oom", "symptom", "triage"], "summary": "崩溃退出的候选根因（未处理异常、栈溢出、OOM、原生崩溃）与自动抓取配置的选择依据。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.symptom-intermittent", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "5. 间歇性抖动", "title": "征象：间歇性抖动为何 dump 答不了", "tags": ["intermittent", "latency-spike", "timeline", "sampling", "symptom", "limitation"], "summary": "间歇性延迟抖动需要时间线采样而非单时点快照；一期可用的近似手段（连抓多个 dump 对比）及其局限，完整方案见后续期次。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.symptom-handle-exhaustion", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "6. 句柄", "title": "征象：句柄 / 资源耗尽的取证路径", "tags": ["handle-leak", "resource-exhaustion", "file-handle", "socket", "symptom", "triage"], "summary": "句柄耗尽的候选根因（GC 句柄泄漏、未释放的文件/套接字句柄、COM 互操作）与托管侧、非托管侧的区分判据。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
```

注意 `anchor` 用了标题的**前缀子串**（如 `1. 进程挂起`，正文标题是 `## 1. 进程挂起 / 无响应`）。`check_index.py` 做 `anchor in heading` 子串匹配，前缀合法且避免了斜杠带来的歧义。

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，6 条报文件不存在。

- [ ] **Step 2: 分段写正文**

文件头须声明本篇是查表不是流程（这是 Global Constraints 收录判据的直接体现）：

```markdown
# 调试决策树

> 本篇是本领域的入口：按**观察到的征象**查出候选根因与对应的取证命令。

**这是一张查找表，不是操作流程。** 它回答"这个征象该用哪条命令取证"，不规定"先做什么再做什么"——多命令的编排属于 skill 的职责，见 `README.md § 收录判据`。

抓 dump 之前先读 `reference/dump-types-and-capability.md` 确定该抓哪种类型；命令报错先查 `reference/symbols-and-tool-matching.md`。
```

六节结构统一为三段：`### 候选根因` / `### 取证命令与判据`（表格）/ `### 常见误判`。第 1 节示范：

```markdown
## 1. 进程挂起 / 无响应

### 候选根因
Monitor 死锁、异步死锁（同步等待异步）、线程池饥饿、长时间 GC 暂停、等待外部 I/O 无超时。

### 取证命令与判据

| 命令 | 看什么 | 结论 |
|---|---|---|
| `!threads`（`reference/sos-threads-and-stacks.md § 1. !threads`） | `Lock Count` 列 | 全 0 → 排除 Monitor 死锁 |
| `!syncblk`（`reference/sos-locks-and-async.md § 1. !syncblk`） | 等待图是否成环 | 成环 → 证实 Monitor 死锁，定位到具体两条线程 |
| `!dumpasync`（`reference/sos-locks-and-async.md § 2. !dumpasync`） | 挂起的状态机延续链 | 有挂起状态机且无线程在跑 → 证实异步死锁（.NET 6+ 限定） |
| `!threadpool`（`reference/sos-locks-and-async.md § 3. !threadpool`） | 队列长度与工作线程数 | 队列长、线程数已达上限、CPU 低 → 证实饥饿 |

### 常见误判
线程数多**不等于**饥饿——须同时看队列长度与 CPU 利用率。CPU 高而队列长是业务压力，CPU 低而队列长才是饥饿。
```

第 5 节「间歇性抖动」是本篇唯一给出**否定结论**的一节，须明确写出：这类问题 dump 答不了，需要时间线采样（`dotnet-counters` / `dotnet-trace` / PerfView）；一期不含这些工具，可用的近似手段是 `procdump -n` 连抓多个 dump 对比（正文引用写作 `reference/dump-capture.md § 1. procdump` 的判据段），完整方案在后续期次。**不留 TODO 措辞**——写成"当前范围内的已知局限与近似替代"。

- [ ] **Step 3: 跑校验确认全域 anchor 有效**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS，累计 37 条。

本篇正文引用了 Task 2–7 的十余个 anchor。**若某个 anchor 写错，`check_refs.py` 会报出**：

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"`
Expected: PASS。这是本计划中交叉引用最密集的一步，报错须逐个核对正文标题原文。

- [ ] **Step 4: 补 README 文件地图**

```markdown
| `reference/debugging-decision-tree.md` | 六类征象（挂起 / 内存增长 / CPU 打满 / 崩溃 / 间歇抖动 / 句柄耗尽）→ 候选根因 → 取证命令查表 |
```

- [ ] **Step 5: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/debugging-decision-tree.md knowledge-base/dotnet-debugging/index.jsonl knowledge-base/dotnet-debugging/README.md
git commit -m "$(cat <<'EOF'
docs(kb): dotnet-debugging 新增调试决策树

- 六类征象的候选根因、取证命令查表与常见误判
- 间歇抖动一节明确给出否定结论：dump 答不了，需时间线采样
- 索引 6 条

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: dump 处置规范与终检

**Files:**
- Create: `knowledge-base/dotnet-debugging/rules/01-dump-handling.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 5 条）
- Modify: `knowledge-base/dotnet-debugging/README.md`（文件地图加 1 行）
- Delete: `knowledge-base/dotnet-debugging/rules/.gitkeep`、`knowledge-base/dotnet-debugging/reference/.gitkeep`（若 Task 1 保留了）
- Test: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging --audit`

**Interfaces:**
- Consumes: Task 3 的 `reference/dump-types-and-capability.md`（引用 `Mini`/`Heap`/`Triage`/`Full` 四个类型名）、Task 3 的 `reference/dump-capture.md#4. WER LocalDumps` 与 `#5. DOTNET_DbgEnableMiniDump`
- Produces: 本领域唯一的 rule 文件，五个小节。**标题逐字为**：`## 1. 生产 dump 的密级`、`## 2. 版本库隔离`、`## 3. 对外交付的类型选择`、`## 4. 留存期限与销毁`、`## 5. 自动抓取的落盘位置`

- [ ] **Step 1: 先写索引，跑校验看失败**

五条 rule **必须填满全部治理字段**（见 Global Constraints）：

```jsonl
{"id": "dotnet-debugging.01.dump-classification", "kind": "rule", "level": "MUST", "file": "rules/01-dump-handling.md", "anchor": "1. 生产 dump 的密级", "title": "生产 full dump 视同最高密级数据", "tags": ["dump", "security", "classification", "pii", "credential", "data-handling"], "summary": "full dump 含整个进程内存，必然包含明文凭证、令牌与全量 PII，禁止提交仓库或作为 IM/邮件附件传递。", "enforcement": "review", "status": "active", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows", "Linux"], "reviewed_at": "2026-09-05", "owner": "desktop client team", "source": ["reference/dump-types-and-capability.md"]}
{"id": "dotnet-debugging.01.gitignore-dumps", "kind": "rule", "level": "MUST", "file": "rules/01-dump-handling.md", "anchor": "2. 版本库隔离", "title": "dump 文件必须进 .gitignore", "tags": ["dump", "gitignore", "version-control", "security", "ci-check"], "summary": "*.dmp 与 *.dump 必须列入 .gitignore，防止调试产物随提交进入版本库历史。", "enforcement": "ci", "status": "active", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows", "Linux"], "reviewed_at": "2026-09-05", "owner": "desktop client team"}
{"id": "dotnet-debugging.01.external-delivery-type", "kind": "rule", "level": "SHOULD", "file": "rules/01-dump-handling.md", "anchor": "3. 对外交付的类型选择", "title": "对外交付应优先选 Triage 或 Heap 而非 Full", "tags": ["dump", "triage-dump", "external-delivery", "data-minimization", "vendor-support"], "summary": "向外部厂商或工单系统提交 dump 时，应先评估 Triage 或 Heap 类型能否回答问题，避免默认交付 Full。", "enforcement": "review", "status": "active", "applies_to": [".NET 6+", "Windows", "Linux"], "reviewed_at": "2026-09-05", "owner": "desktop client team", "source": ["reference/dump-types-and-capability.md"]}
{"id": "dotnet-debugging.01.retention-and-disposal", "kind": "rule", "level": "MUST", "file": "rules/01-dump-handling.md", "anchor": "4. 留存期限与销毁", "title": "生产 dump 须有留存期限与销毁责任人", "tags": ["dump", "retention", "disposal", "data-lifecycle", "accountability"], "summary": "生产环境 dump 必须约定留存期限与销毁责任人，排查结束后按期销毁，不得无限期滞留在分析机或共享盘。", "enforcement": "review", "status": "active", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows", "Linux"], "reviewed_at": "2026-09-05", "owner": "desktop client team"}
{"id": "dotnet-debugging.01.auto-capture-location", "kind": "rule", "level": "SHOULD", "file": "rules/01-dump-handling.md", "anchor": "5. 自动抓取的落盘位置", "title": "自动抓取启用前应评估落盘位置的访问控制", "tags": ["dump", "auto-capture", "wer", "access-control", "disk-space", "production"], "summary": "WER LocalDumps 与 DOTNET_DbgEnableMiniDump 会静默堆积敏感文件，生产启用前应确认落盘目录的访问权限与容量上限。", "enforcement": "review", "status": "active", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows", "Linux"], "reviewed_at": "2026-09-05", "owner": "desktop client team", "source": ["reference/dump-capture.md#4. WER LocalDumps"]}
```

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: FAIL，5 条报文件不存在。

- [ ] **Step 2: 写正文**

本篇短，可一次 `Write`（约 60 行，不触发分段约束）。文件头须写明与 `csharp/14` 的关系——这是设计中识别出的真空：

```markdown
# 01 · dump 文件处置

> 本篇约束 dump 作为**数据资产**的处置，不约束调试技术本身。

`knowledge-base/csharp/rules/14-security.md § 8. 日志与脱敏` 约束的是**日志**——禁止记录密码、令牌与完整 PII。但 full dump 是整个进程内存的完整副本，其中必然含明文凭证与全量 PII，**任何脱敏中间件都无法作用于它**。§ 8 推荐的统一脱敏过滤器在 dump 面前完全失效，故需本篇单独约束。

各 dump 类型的数据含量差异见 `reference/dump-types-and-capability.md`。
```

五节按仓库 rules 惯例写，措辞用「必须/禁止/应该」（与 `level` 字段对应）。第 2 节须给出具体 `.gitignore` 条目：

```markdown
## 2. 版本库隔离

- **必须**：`.gitignore` 包含 dump 文件模式，防止调试产物进入版本库历史

​```gitignore
*.dmp
*.dump
core.*
​```

`core.*` 覆盖 Linux 下 `createdump` 与内核 core dump 的默认命名。一旦 dump 进入 git 历史，移除需要重写历史——这是该条标 `enforcement: ci` 的原因：外壳（文件是否被 ignore）可自动判定，且违反后的修复代价极高。
```

- [ ] **Step 3: 跑校验确认通过**

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
Expected: PASS，累计 42 条。

Run: `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging --audit`
Expected: `kind` 分布为 37 reference + 5 rule；`level` 分布为 3 MUST + 2 SHOULD；无孤儿文件。

- [ ] **Step 4: 全局终检**

四项全跑，这是一期完成判定：

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging --audit
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
```

Expected:
- 全局校验 PASS，记录数 502 + 42 = **544**
- `--audit` 无孤儿文件
- `find_duplicates.py` 中 `dotnet-debugging.01.*` 与 `csharp.14.*` 的相似度低于 0.6。**若 `dotnet-debugging.01.dump-classification` 与 `csharp.14.secret-management` 超过 0.6**，说明本篇写成了密钥管理的复述，须收窄措辞——本篇只讲 dump 这一载体，不讲密钥该怎么存
- `check_refs.py` PASS

- [ ] **Step 5: 清理 .gitkeep**

```bash
rm -f knowledge-base/dotnet-debugging/rules/.gitkeep knowledge-base/dotnet-debugging/reference/.gitkeep
```

两个目录此时均有真实文件，占位文件不再需要。

- [ ] **Step 6: 核对 README 文件地图完整性**

打开 `knowledge-base/dotnet-debugging/README.md`，确认「文件地图」表格有 **9 行**（8 reference + 1 rules），与实际文件一一对应。补最后一行：

```markdown
| `rules/01-dump-handling.md` | dump 作为数据资产的处置：密级、版本库隔离、对外交付类型、留存销毁、自动抓取落盘 |
```

- [ ] **Step 7: 提交**

```bash
git add knowledge-base/dotnet-debugging
git commit -m "$(cat <<'EOF'
docs(kb): dotnet-debugging 新增 dump 处置规范并完成一期

- 5 条 dump 处置条款，填补 csharp/14 § 8 对 dump 载体的覆盖真空
- 补齐 README 文件地图 9 行，清理占位文件
- 一期完成：8 篇 reference + 1 篇 rules，索引 42 条

Co-Authored-By: <当前会话实际模型名> <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 8: 走 commit-cc-plugin 推送**

一期全部 Task 提交完毕后，用 `/commit-cc-plugin` 完成最终推送（该 skill 会检测未推送提交并询问是否 amend，此处选 `new`，保留逐 Task 提交历史）。

---

## 完成判定

一期完成需同时满足：

- [ ] `check_index.py`（全局）PASS，记录数 544
- [ ] `check_index.py dotnet-debugging --audit` 无孤儿文件，分布为 37 reference + 5 rule
- [ ] `find_duplicates.py` 未报出 `dotnet-debugging.*` 与既有领域的高相似度对（≥ 0.6）
- [ ] `check_refs.py` PASS
- [ ] `knowledge-base/catalog.json` 含 `dotnet-debugging` 条目
- [ ] `knowledge-base/README.md` 领域列表与职责边界句均已更新
- [ ] 领域 README 文件地图 9 行齐全，版本行 `1.0.0` 与 CHANGELOG 一致
- [ ] 全部改动已推送 master







