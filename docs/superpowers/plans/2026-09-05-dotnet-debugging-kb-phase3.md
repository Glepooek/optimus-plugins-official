# dotnet-debugging 知识库（三期）：WPF 桌面 dump 归因实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `knowledge-base/dotnet-debugging/` 领域新增 WPF 桌面应用的 dump 归因内容（2 篇 reference、10 条索引），并在一期决策树中接入 WPF 分支。

**Architecture:** 沿用一期的领域结构。本期**不新增任何命令**——两篇正文全部复用一期已交付的 SOS 命令（`!threads` / `!clrstack` / `!dumpstack` / `!dso` / `!syncblk` / `!dumpheap` / `!gcroot`），增量是「WPF 特有的读法」：同一条 `!gcroot` 输出，通用读法给出一条类型链，WPF 读法能指出这条链意味着「XAML 里某个绑定没解开」。因此本期条目是**征象归因条目**而非命令条目，与一期 `debugging-decision-tree.md` 同类，结构上用三段而非一期命令篇的四段。

**Tech Stack:** Markdown + JSONL 索引；校验工具为仓库自带 Python 脚本（`check_index.py` / `find_duplicates.py` / `check_refs.py`，本机只有 `unittest`，无 `pytest`）。

**Spec:** `docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-phase3-design.md`

## Global Constraints

以下约束适用于**每一个** Task，不再逐条重复。

- **域名与 id 前缀**：域名 `dotnet-debugging`；本期全部为 reference 条目，id 形式 `dotnet-debugging.ref.<slug>`。`ID_RE = ^[a-z0-9-]+\.(?:\d{2}|ref)\.[a-z0-9-]+$`，**slug 只能含小写字母、数字、连字符**。
- **正文语言中文，`tags` 全英文**：严格遵守，tag 用小写字母加连字符。
- **`anchor` 填中文标题文本**（非 slug），`check_index.py` 按 `anchor in heading` 子串匹配。标题含斜杠、括号或感叹号时，`anchor` 取不含歧义字符的前缀子串即可（一期先例：`## 1. 进程挂起 / 无响应` 的 anchor 为 `1. 进程挂起`）。
- **索引 `source` 字段只用于领域内引用**，形式 `reference/<file>.md#<标题文本>`。**跨领域引用一律写在正文里**，形式 `knowledge-base/wpf/rules/NN-x.md § 章节`。跨领域路径写进 `source` 会被路径越界检查拦截。
- **两种引用符号服务于两个校验器，不得混用**：

  | 位置 | 符号 | 形式 | 校验者 |
  |---|---|---|---|
  | 索引 `source` 字段 | `#` | `reference/sos-heap-and-objects.md#4. !gcroot` | `check_index.py` 的 `check_source_refs` |
  | **正文**交叉引用（含领域内与跨领域） | ` § ` | `reference/sos-heap-and-objects.md § 4. !gcroot` | `check_refs.py` |

  正文里写 `#` 不会报错，但 `check_refs.py` 检不到——引用会静默失效。**正文一律用 ` § `。**

- **`applies_to` 本期全部条目取值固定**（spec § 6）：

  ```json
  "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"]
  ```

  **不含 `Linux`**——WPF 不跨平台。**含 `.NET Framework 4.x`**——与二期相反，二期不含 Framework 是因 EventPipe 为 .NET Core+ 特性，三期复用的是 SOS 命令，Framework 完全适用。`applies_to` 平台标注是本领域已知易错点（一期为此单独提交过修正 commit `c8603f8`）。

- **判据段标题固定为 `### 判据与下一步`**：本期沿用一期布尔判据，**不用**二期的「基线形态 / 异常形态 / 区分点」三元组（spec § 4.1——dump 是单时点快照，不需要「和之前比」）。
- **每条判据须同时写证实与排除两个方向**（spec § 4.2）：只写证实方向的判据在排查中价值减半。
- **不写绝对阈值**（spec § 4.3）：「堆上超过 100 个 Window 实例即异常」这类禁止；预期实例数由应用自身决定，表述为「超出该应用预期的活动实例数」这一相对形态。
- **事实分级标注**（spec § 7.2）：一级（源码/文档可核实）照实写并注明出处；二级（可从一级事实与 CLR/GC 语义逻辑推导）照实写并写明推导依据；三级（典型输出排版、常见现场形态）**显式标注为经验性知识**。**硬约束：查不到源码佐证的内部字段名，宁可写「根链上会出现 WPF 内部类型」的模糊表述，也不编造一个看似精确的字段名**——读者会拿着不存在的类型名去 grep 输出。
- **分段写入**：单篇 reference 预计数百行，必须先 `Write` 骨架再多次 `Edit` 逐段填充，禁止单次输出整篇。
- **版本号**：领域 `README.md` 顶部版本行改为 `> 版本：1.2.0`，须与 `CHANGELOG.md` 最新条目一致。**不升 `.claude-plugin/marketplace.json`**——本期不动 `plugins/` 与 `.claude/`。
- **提交**：每个 Task 末尾提交。本仓库禁止手动 git 工作流，但**执行本计划期间的逐 Task 提交例外**——逐 Task 用直接 git 命令，最终推送前再走一次 `commit-cc-plugin`。提交类型统一 `docs(kb)`，`Co-Authored-By` 填当前会话实际模型名。

---

## File Structure

| 文件 | 责任 | 产出 Task |
|---|---|---|
| `reference/wpf-dispatcher-deadlock.md` | UI 线程卡死的取证：认出 UI 线程、三类等待形态、队列积压 vs 真死锁、定位持锁方 | Task 1 |
| `reference/wpf-leak-patterns.md` | 四类 WPF 泄漏在托管堆里的形态图鉴：共同起点 + Binding / 可视化树 / 弱事件 / DispatcherTimer 四节 + 反查速查表 | Task 2、Task 3 |
| `debugging-decision-tree.md`（改） | § 1 与 § 2 各增补一处 WPF 分支入口，不改结论、不删原文 | Task 4 |
| `index.jsonl`（改 2 条 summary） | `symptom-hang` / `symptom-memory-growth` 的 summary 微调，id/anchor/file 不动 | Task 4 |
| `README.md` / `CHANGELOG.md` / `catalog.json` / 一期 spec（改） | 定位段、版本、文件地图、阅读路径、领域 notes、分期路标 | Task 5 |

**任务顺序依据**：两篇 reference 之间**无依赖**（不像一期术语篇、二期机制篇被后续引用），Task 1 与 Task 2/3 可互换顺序。泄漏篇拆成两个 Task 是因为它有 6 节、含全期最难的待核验事实，一个 Task 过大；决策树增补须待两篇落地（要指向其 anchor），收尾最后。

**TDD 在本计划中的形态**：知识库无单元测试，`check_index.py` 就是测试运行器。每个 Task 遵循「先写索引条目跑校验看它报错 → 补正文 → 再跑校验看它通过」的循环，与代码 TDD 同构。

---

## Task 索引

| Task | 交付物 | 索引增量 |
|---|---|---|
| 1 | `wpf-dispatcher-deadlock.md`（4 节） | +4 |
| 2 | `wpf-leak-patterns.md` § 1–3（起点 + Binding + 可视化树） | +3 |
| 3 | `wpf-leak-patterns.md` § 4–6（弱事件 + DispatcherTimer + 反查表） | +3 |
| 4 | 决策树两处增补 | 0（改 2 条 summary） |
| 5 | 版本、定位段、文件地图、catalog、spec 路标、终检 | 0 |

**索引总增量 10 条**，全局记录数 566 → **576**。领域内 64 → **74**（reference 59 → 69，rule 仍 5）。

上述基数已于 2026-09-05 实测确认（`check_index.py` 全局 566 条；`dotnet-debugging` 64 条，其中 reference 59、rule 5）。验收按这些数字硬核对，不接受「约」。

---

## 待核验事实的处理位置

spec § 7.3 列出 6 条待核验事实。本计划把它们**绑定到具体 Step**，不允许「写到哪儿想起来再查」：

| # | 待核验事实 | 落在 |
|---|---|---|
| 1 | `PropertyDescriptor` 订阅路径上实际出现在根链里的类型名 | Task 2 Step 6 |
| 2 | `WeakEventManager` 内部表的类型名与清理时机 | Task 3 Step 3 |
| 3 | `DispatcherTimer` 到 `Dispatcher` 的实际引用字段与方向 | Task 3 Step 4 |
| 4 | `Dispatcher` 自身的生命周期锚点 | Task 1 Step 4（与 Task 3 Step 4 共用结论） |
| 5 | UI 线程栈底出现的实际方法名层次 | Task 1 Step 4 |
| 6 | `!syncblk` 的 owner 线程 ID 与 `!threads` 哪一列对应 | Task 1 Step 7——**读一期正文核对，不重新查证** |

第 6 条特别说明：它是一期已交付内容。若发现一期写错，属一期缺陷，**单独修正并升 patch 版本，不混进三期**。

---

### Task 1: Dispatcher 死锁归因篇

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/wpf-dispatcher-deadlock.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 4 行）

**Interfaces:**
- Consumes: 一期 anchor `1. !threads`、`2. !clrstack`、`3. !dumpstack`、`5. !dso`（`sos-threads-and-stacks.md`）与 `1. !syncblk`（`sos-locks-and-async.md`）
- Produces: 四个 anchor，供 Task 4 在正文中以 ` § ` 引用，且**逐字不可改**：
  - `1. 从 !threads 认出 UI 线程`
  - `2. UI 线程栈的三类等待形态`
  - `3. Dispatcher 队列积压 vs 真死锁`
  - `4. 定位持锁方与互等闭环`
- Produces: 四条索引 id：`dotnet-debugging.ref.wpf-identify-ui-thread` / `.wpf-ui-wait-forms` / `.wpf-queue-vs-deadlock` / `.wpf-lock-owner-loop`

- [ ] **Step 1: 先追加 4 条索引，让校验失败**

追加到 `knowledge-base/dotnet-debugging/index.jsonl` 末尾（每条一行，JSON 不换行）：

```jsonl
{"id": "dotnet-debugging.ref.wpf-identify-ui-thread", "kind": "reference", "file": "reference/wpf-dispatcher-deadlock.md", "anchor": "1. 从 !threads 认出 UI 线程", "title": "认出 UI 线程：Dispatcher 归属而非线程编号", "tags": ["ui-thread", "dispatcher", "sta", "thread-identification", "wpf"], "summary": "UI 线程的判定依据是栈底出现 Dispatcher 消息循环帧且 Apartment 为 STA，而非线程编号——按编号猜测在多 UI 线程应用与托管宿主场景下会认错线程，导致后续全部分析基于错误的栈。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-threads-and-stacks.md#1. !threads"]}
{"id": "dotnet-debugging.ref.wpf-ui-wait-forms", "kind": "reference", "file": "reference/wpf-dispatcher-deadlock.md", "anchor": "2. UI 线程栈的三类等待形态", "title": "UI 线程的三类等待形态：等锁 / 等异步 / 等 COM", "tags": ["ui-thread", "blocking", "monitor-enter", "task-wait", "com-marshaling", "wpf"], "summary": "UI 线程被阻塞时栈顶呈三类形态——Monitor 等锁、同步等待异步结果、COM 编组等待，三者的下一步取证命令与修复方向完全不同，混为一谈会查错方向。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-threads-and-stacks.md#2. !clrstack"]}
{"id": "dotnet-debugging.ref.wpf-queue-vs-deadlock", "kind": "reference", "file": "reference/wpf-dispatcher-deadlock.md", "anchor": "3. Dispatcher 队列积压 vs 真死锁", "title": "队列积压与真死锁的区分：同一征象两种处置方向", "tags": ["dispatcher-queue", "deadlock", "long-running-task", "unresponsive", "differentiation", "wpf"], "summary": "界面无响应有两种成因——UI 线程在跑长任务（栈上有业务帧、队列积压）与 UI 线程被阻塞（栈顶是等待原语），二者外在表现相同但处置方向相反，区分依据是栈顶形态而非无响应时长。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-threads-and-stacks.md#2. !clrstack"]}
{"id": "dotnet-debugging.ref.wpf-lock-owner-loop", "kind": "reference", "file": "reference/wpf-dispatcher-deadlock.md", "anchor": "4. 定位持锁方与互等闭环", "title": "定位持锁方：从 !syncblk 到互等闭环的完整读法", "tags": ["syncblk", "lock-owner", "circular-wait", "thread-mapping", "deadlock-evidence", "wpf"], "summary": "由 !syncblk 的 owner 线程 ID 回到 !threads 映射托管线程、再以 !clrstack 看其在等什么，构成 UI 线程与后台线程互等的证据闭环；单看任一侧都只能得出「在等」而无法证实成环。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-locks-and-async.md#1. !syncblk"]}
```

- [ ] **Step 2: 运行校验，确认它因文件缺失而失败**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

预期：FAIL，4 条报错指向 `reference/wpf-dispatcher-deadlock.md` 不存在。**看到这个失败才说明索引确实被校验器读到了**——直接写正文再补索引会跳过这层验证。

- [ ] **Step 3: 写文件骨架（只有标题，不填正文）**

创建 `reference/wpf-dispatcher-deadlock.md`，内容为文件头 + 4 个 `##` 标题（逐字照抄上方 Interfaces 段）。文件头：

```markdown
# WPF Dispatcher 死锁归因

> **适用范围**：WPF 桌面应用，**仅 Windows**。覆盖 .NET Framework 4.x 与 .NET 6+ 两条 WPF 技术栈。非 WPF 应用的挂起排查见 `reference/debugging-decision-tree.md § 1. 进程挂起`。

本篇不引入新命令，全部复用一期已交付的 SOS 命令，增量是「同一份输出在 WPF 场景下怎么读」。预防性的线程与 Dispatcher 编码规范属另一领域，见 `knowledge-base/wpf/rules/09-threading.md § 5. 死锁防护`——那里讲怎么不写出死锁，本篇讲已经死锁了怎么认出来。
```

跑校验确认 4 条 anchor 全部命中：

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

预期：PASS。此时正文还是空的，但索引契约已锁死。

- [ ] **Step 4: 补核验待查事实 #4 与 #5**

本 Step 不写正文，只查证。两项：

1. **UI 线程栈底的实际方法名层次**（spec § 7.3 第 5 条）：查 `dotnet/wpf` 中 `Dispatcher.Run` / `Dispatcher.PushFrame` / `Dispatcher.PushFrameImpl` 的调用关系，确认 dump 栈上实际会出现哪几帧、顺序如何
2. **`Dispatcher` 自身的生命周期锚点**（第 4 条）：`Dispatcher` 与线程的关联方式（是否有静态表持有各线程的 Dispatcher 实例）。此结论 Task 3 Step 4 的 `DispatcherTimer` 泄漏链会复用

查证来源：`dotnet/wpf` 仓库源码，或 `learn.microsoft.com` 的 `System.Windows.Threading.Dispatcher` API 文档。

**查不到时的降级写法**：不编造方法名。写「栈底可见 Dispatcher 的消息循环帧」并标注为经验性知识，而非写一个具体但未经核实的 `Dispatcher.PushFrameImpl`。按 Global Constraints 的事实分级硬约束执行。

- [ ] **Step 5: 填 § 1（从 !threads 认出 UI 线程）**

三段结构：`### 识别依据` / `### 操作步骤` / `### 判据与下一步`。

要点：

- **识别依据不是线程编号**。0 号线程通常是主线程，但主线程未必是 UI 线程（托管宿主、`Main` 另起 STA 线程创建窗口的场景）；多 UI 线程应用中每个线程各有独立 `Dispatcher`
- 两个判定条件须同时成立：`!threads` 输出中 Apartment 为 **STA**；`!clrstack` 栈底可见 Dispatcher 消息循环帧（具体帧名按 Step 4 查证结果写）
- 操作步骤：`!threads` 列出全部托管线程 → 对 STA 线程逐个 `!clrstack` → 栈底有消息循环帧者即 UI 线程
- 判据须写双向：**证实**——STA 且栈底有消息循环帧 → 该线程是 UI 线程；**排除**——全部线程均无消息循环帧 → 该 dump 抓取时 UI 线程已退出，或这不是 WPF 应用，转 `reference/debugging-decision-tree.md § 1. 进程挂起` 走通用路径

正文以 ` § ` 引用 `reference/sos-threads-and-stacks.md § 1. !threads` 与 `§ 2. !clrstack`。

- [ ] **Step 6: 填 § 2 与 § 3（分两次 Edit）**

**§ 2（三类等待形态）**，三段结构同上。核心是一张形态对照表：

| 栈顶形态 | 含义 | 下一步 |
|---|---|---|
| `Monitor.Enter` / `Monitor.ReliableEnter` | 等 Monitor 锁 | `§ 4. 定位持锁方与互等闭环` |
| `Task.Wait` / `Task.Result` / `WaitHandle.WaitOne` | 同步等待异步结果 | `reference/sos-locks-and-async.md § 2. !dumpasync`（.NET 6+ 限定） |
| `CoWaitForMultipleHandles` 等 COM 编组帧 | 等 COM 调用返回 | 超出 SOS 托管取证范围，转原生栈分析 |

第三行的「超出范围」须写明——这是本篇能力边界，不写会让读者在 SOS 里空转。第二行以 ` § ` 引用 wpf 领域的预防规范 `knowledge-base/wpf/rules/09-threading.md § 5. 死锁防护`。

**§ 3（队列积压 vs 真死锁）**，本篇核心区分点：

- 两种成因外在表现相同（界面无响应），处置方向相反：长任务要挪到后台线程，死锁要打破等待环
- 区分依据是**栈顶形态**，不是无响应时长——「卡了 30 秒以上就是死锁」是错误判据，长任务同样能卡任意久
- 长任务形态：栈上有业务方法帧，栈顶不是等待原语；配合 `!dso` 看栈上对象判断在处理什么
- 死锁形态：栈顶是 § 2 表中的等待原语
- 判据双向写：**证实**长任务 → 栈顶为业务帧；**证实**阻塞 → 栈顶为等待原语；**排除**——UI 线程栈正常且无等待帧，则无响应另有成因（如渲染线程问题、消息泵被非托管代码占用），超出本篇范围

- [ ] **Step 7: 填 § 4（定位持锁方与互等闭环）**

**先读一期正文核对待查事实 #6**（`!syncblk` 的 owner 线程 ID 与 `!threads` 哪一列对应）：

```bash
python -c "print(open('knowledge-base/dotnet-debugging/reference/sos-locks-and-async.md',encoding='utf-8').read()[:4000])"
```

按一期实际写法对齐列名，**不重新查证**。若发现一期写错，属一期缺陷，单独修正并升 patch，不混进三期。

正文要点：

- 完整闭环四步：`!syncblk` 拿到 owner 线程 ID → 回 `!threads` 映射到托管线程 → 对该线程 `!clrstack` 看它在等什么 → 若它等的锁 owner 又是 UI 线程，环闭合
- **单看任一侧不足以证实死锁**：只看 UI 线程只能得出「它在等」，必须看到环才是死锁证据
- `!syncblk` 默认输出是 `-all` 的子集，排查同步块表膨胀须加 `-all`（一期 `sos-locks-and-async.md § 1` 已述，此处以 ` § ` 引用而非重复）
- 判据双向：**证实**——等待关系成环；**排除**——owner 线程栈顶不是等待原语（它在干活，只是慢），则不是死锁而是锁竞争，转 § 3 的长任务分支

- [ ] **Step 8: 跑三个校验器**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
```

预期：前两个 PASS；`find_duplicates.py` 中本 Task 的 4 条与 `wpf.09.no-sync-wait-deadlock`、`wpf.09.dispatcher-usage` 相似度低于 0.5。若超过，说明判据写成了预防规范的复述，须改写为「从 dump 里认出它」的视角。

- [ ] **Step 9: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/wpf-dispatcher-deadlock.md
git add knowledge-base/dotnet-debugging/index.jsonl
git commit -m "docs(kb): dotnet-debugging 新增 WPF Dispatcher 死锁归因篇"
```

---

### Task 2: 泄漏形态图鉴 § 1–3（起点 + Binding + 可视化树）

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/wpf-leak-patterns.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 3 行）

**Interfaces:**
- Consumes: 一期 anchor `1. !dumpheap`、`2. !dumpobj`、`4. !gcroot`（`sos-heap-and-objects.md`）
- Produces: 三个 anchor，供 Task 3 与 Task 4 引用，**逐字不可改**：
  - `1. WPF 泄漏的共同取证起点`
  - `2. Binding 泄漏`
  - `3. 可视化树泄漏`
- Produces: 三条索引 id：`dotnet-debugging.ref.wpf-leak-entry` / `.wpf-leak-binding` / `.wpf-leak-visual-tree`
- Produces: 文件骨架含全部 **6** 个 `##` 标题（Task 3 的三节标题一并建好，避免 Task 3 再动文件头）

- [ ] **Step 1: 先追加 3 条索引，让校验失败**

```jsonl
{"id": "dotnet-debugging.ref.wpf-leak-entry", "kind": "reference", "file": "reference/wpf-leak-patterns.md", "anchor": "1. WPF 泄漏的共同取证起点", "title": "WPF 泄漏取证起点：该盯哪些类型与预期实例数", "tags": ["dumpheap", "wpf-types", "expected-instance-count", "leak-triage", "window", "usercontrol"], "summary": "WPF 泄漏排查先用 !dumpheap -stat 筛查 Window/UserControl/BindingExpression/DispatcherTimer 等类型；判定「该被回收却还在」的前提是知道该应用的预期活动实例数，这个前提不成立时整条推理链失效。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-heap-and-objects.md#1. !dumpheap"]}
{"id": "dotnet-debugging.ref.wpf-leak-binding", "kind": "reference", "file": "reference/wpf-leak-patterns.md", "anchor": "2. Binding 泄漏", "title": "Binding 泄漏：绑定源未实现 INotifyPropertyChanged 的代价", "tags": ["binding-leak", "inotifypropertychanged", "propertydescriptor", "static-table", "gcroot", "wpf"], "summary": "绑定源未实现 INotifyPropertyChanged 时 WPF 退化为 PropertyDescriptor 订阅，由静态表持有源对象，绑定目标即使已从可视化树移除源仍不可回收；根链止于 WPF 内部订阅结构而非应用代码，是最易被误判为「无根」的一类。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-heap-and-objects.md#4. !gcroot"]}
{"id": "dotnet-debugging.ref.wpf-leak-visual-tree", "kind": "reference", "file": "reference/wpf-leak-patterns.md", "anchor": "3. 可视化树泄漏", "title": "可视化树泄漏：元素已移除但仍被持有", "tags": ["visual-tree", "static-resource", "logical-parent", "event-subscription", "gcroot", "wpf"], "summary": "元素从可视化树移除不等于可回收——静态资源字典、逻辑父级残留、未退订的事件三类持有方式会让整棵子树连同其 DataContext 一起留在堆上，根链末端的形态决定了是哪一类。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-heap-and-objects.md#4. !gcroot"]}
```

- [ ] **Step 2: 跑校验确认失败**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

预期：FAIL，3 条报错指向 `reference/wpf-leak-patterns.md` 不存在。

- [ ] **Step 3: 写骨架（含 Task 3 的三个标题）并复跑校验**

创建文件，文件头 + **6** 个 `##` 标题，逐字：

```
## 1. WPF 泄漏的共同取证起点
## 2. Binding 泄漏
## 3. 可视化树泄漏
## 4. 弱事件泄漏
## 5. DispatcherTimer 泄漏
## 6. 根链形态图鉴速查表
```

文件头：

```markdown
# WPF 泄漏形态图鉴

> **适用范围**：WPF 桌面应用，**仅 Windows**。覆盖 .NET Framework 4.x 与 .NET 6+ 两条 WPF 技术栈。非 WPF 应用的内存增长排查见 `reference/debugging-decision-tree.md § 2. 内存持续增长`。

本篇不引入新命令，全部复用一期已交付的 SOS 命令，增量是「同一条 !gcroot 输出在 WPF 场景下意味着什么」。预防性的编码规范属另一领域，见 `knowledge-base/wpf/rules/10-performance.md § 7. 内存与泄漏`——那里讲怎么不写出泄漏，本篇讲已经泄漏了怎么认出是哪一类。

§ 2–5 四节结构固定为：`### 堆上的可见特征` / `### 根链形态` / `### 判据与下一步`。已知泄漏类型时读对应节；只拿到一条 `!gcroot` 输出、不知属于哪类时，按 `§ 6. 根链形态图鉴速查表` 的内部类型名反查。
```

跑校验：

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

预期：PASS。§ 4–6 三个标题此时无索引指向，**这是正常的**——`--audit` 检的是「有文件无索引」的孤儿文件，不是孤儿小节；Task 3 会补上它们的索引。

- [ ] **Step 4: 填 § 1（共同取证起点）**

三段结构：`### 该盯哪些类型` / `### 预期实例数这个前提` / `### 判据与下一步`。

**类型清单表**（`!dumpheap -stat -type <名>` 的筛查对象）：

| 类型名 | 预期活动实例数的判断依据 |
|---|---|
| `System.Windows.Window` 及其派生 | 应用当前打开的窗口数；已关闭的窗口应为 0 |
| `System.Windows.Controls.UserControl` 派生 | 当前显示的控件实例数 |
| `System.Windows.Data.BindingExpression` | 无固定预期值，看是否与已销毁的界面数量同比增长 |
| `System.Windows.Threading.DispatcherTimer` | 应用当前活动定时器数 |
| 应用自身的 ViewModel 类型 | 按导航层级推算 |

**「预期实例数」这个前提必须单独成段**，理由：这是与通用泄漏排查最大的差异。通用做法是「间隔采样两次看 Count 是否上涨」（一期 `debugging-decision-tree.md § 2` 的做法），但 WPF 场景下单份 dump 也能判定——因为「已关闭的 Window 实例数应为 0」是先验知识。**该前提不成立时（不知道应用预期实例数），整条推理链失效**，须退回一期的间隔采样做法。

判据双向：**证实**——某 WPF 类型实例数超出应用预期活动数 → 转 `!gcroot` 定位持有链，按 § 2–5 分类；**排除**——全部 WPF 类型实例数均在预期内 → 排除本篇四类泄漏，转 `reference/debugging-decision-tree.md § 2. 内存持续增长` 查非托管泄漏、LOH 碎片等通用成因。

正文以 ` § ` 引用 `reference/sos-heap-and-objects.md § 1. !dumpheap` 与 `§ 4. !gcroot`。

- [ ] **Step 5: 填 § 2 的前两段（堆上的可见特征 / 根链形态骨架）**

`### 堆上的可见特征`：`BindingExpression` 实例数与已销毁界面同比增长；对应的绑定源对象（通常是 ViewModel 或数据实体）实例数不回落。

`### 根链形态` 段先写机制推导（二级事实，可写）：

- 绑定源实现了 `INotifyPropertyChanged` 时，WPF 用弱引用订阅其 `PropertyChanged`，源对象可正常回收
- 未实现时退化为 `PropertyDescriptor` 订阅路径，由**静态表**持有源对象——静态表是 GC 根，源对象因此不可回收
- 后果：绑定目标（界面元素）即使已从可视化树移除，源对象仍活着；若源对象反向持有界面元素，整条链一起留下

具体类型名留到 Step 6 填。

- [ ] **Step 6: 补核验待查事实 #1，填 § 2 的根链类型名与判据段**

查证 `PropertyDescriptor` 订阅路径上实际出现在根链里的类型名。来源：`dotnet/wpf` 中 `PropertyPathWorker` / `DependencySource` / `ValueTable` 相关实现，或官方 data binding 文档。

**这是全期最重要的一条待核验事实**——它是 § 6 反查表里 Binding 泄漏的标志物。

按 Global Constraints 的事实分级处理：

- 查到确切类型名 → 一级事实，照实写并注明出处（源码路径或文档 URL）
- 查不到 → **写「根链末端为 WPF 内部的 PropertyDescriptor 订阅结构（静态表持有）」这一模糊但正确的表述，并标注为经验性知识**。不编造具体类型名

`### 判据与下一步` 双向写：**证实**——`!gcroot` 根链末端为 PropertyDescriptor 订阅相关的静态表结构 → 该绑定源未实现 `INotifyPropertyChanged`，下一步以 ` § ` 指向 `knowledge-base/wpf/rules/05-data-binding.md`（修复方向，跨领域引用写正文不写 source）；**排除**——根链末端是应用自身的静态字段或事件 → 不是 Binding 泄漏，转 § 3。

- [ ] **Step 7: 填 § 3（可视化树泄漏）**

`### 堆上的可见特征`：`Window` / `UserControl` 派生类型实例数超出预期；其 `DataContext` 指向的 ViewModel 同步不回落（用 `!dumpobj` 看元素对象的 `DataContext` 字段）。

`### 根链形态`：三类持有方式各自的根链末端形态——

| 持有方式 | 根链末端 |
|---|---|
| 静态资源字典持有 | 静态字段 → `ResourceDictionary` → 元素 |
| 逻辑父级残留 | 父元素（自身仍有根）→ 子元素集合 → 元素 |
| 未退订的事件 | 事件源对象 → 委托 `_invocationList` → 元素（作为 `Target`） |

第三行的 `_invocationList` 是一期 `debugging-decision-tree.md § 2` 已给出的形态（原文：「事件 `_invocationList`」），此处对齐一期措辞，不另造说法。

`### 判据与下一步` 双向写：**证实**——根链末端匹配上表任一行；**排除**——`!gcroot` 报无根路径 → 该元素实际已可回收，只是 GC 尚未运行，不是泄漏（这是本节最常见的误判，须显式写出）。

下一步以 ` § ` 指向 `knowledge-base/wpf/rules/10-performance.md § 7. 内存与泄漏`（预防侧）与 `knowledge-base/wpf/rules/03-mvvm.md § 7. 事件与订阅`（事件退订规范）。

- [ ] **Step 8: 跑三个校验器**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
```

`find_duplicates.py` 重点看本 Task 3 条与 `wpf.10.memory-leak`、`wpf.03.event-subscription`、`wpf.05.binding-threading` 的相似度，须 < 0.5。

- [ ] **Step 9: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/wpf-leak-patterns.md
git add knowledge-base/dotnet-debugging/index.jsonl
git commit -m "docs(kb): dotnet-debugging 新增 WPF 泄漏形态图鉴（取证起点、Binding、可视化树）"
```

---

### Task 3: 泄漏形态图鉴 § 4–6（弱事件 + DispatcherTimer + 反查表）

**Files:**
- Modify: `knowledge-base/dotnet-debugging/reference/wpf-leak-patterns.md`（填 § 4–6，标题已由 Task 2 建好）
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 3 行）

**Interfaces:**
- Consumes: Task 2 的 anchor `1. WPF 泄漏的共同取证起点`、`2. Binding 泄漏`、`3. 可视化树泄漏`；Task 1 Step 4 关于 `Dispatcher` 生命周期锚点的查证结论
- Produces: 三个 anchor：`4. 弱事件泄漏`、`5. DispatcherTimer 泄漏`、`6. 根链形态图鉴速查表`
- Produces: 三条索引 id：`dotnet-debugging.ref.wpf-leak-weak-event` / `.wpf-leak-dispatcher-timer` / `.wpf-leak-rootchain-lookup`

- [ ] **Step 1: 先追加 3 条索引，跑校验确认 PASS**

```jsonl
{"id": "dotnet-debugging.ref.wpf-leak-weak-event", "kind": "reference", "file": "reference/wpf-leak-patterns.md", "anchor": "4. 弱事件泄漏", "title": "弱事件泄漏：用了 WeakEventManager 不等于不泄漏", "tags": ["weak-event", "weakeventmanager", "amortized-cleanup", "listener-table", "gcroot", "wpf"], "summary": "WeakEventManager 弱的是监听者一侧，其内部监听表的清理是摊销式的——表项在下次相关操作触发前不会被移除，短周期内大量订阅退订会让表项堆积；这类堆积在 dump 中表现为管理器内部结构体积增长而非应用对象泄漏。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-heap-and-objects.md#4. !gcroot"]}
{"id": "dotnet-debugging.ref.wpf-leak-dispatcher-timer", "kind": "reference", "file": "reference/wpf-leak-patterns.md", "anchor": "5. DispatcherTimer 泄漏", "title": "DispatcherTimer 泄漏：被应用级生命周期钉住的对象图", "tags": ["dispatchertimer", "tick-handler", "dispatcher-lifetime", "strong-reference", "gcroot", "wpf"], "summary": "Dispatcher 强引用未 Stop 的 timer、timer 强引用 Tick 处理器、处理器的 Target 是界面元素或 ViewModel，整条对象图被应用级生命周期的 Dispatcher 钉住；根链止于 Dispatcher 而非应用代码，是四类中最易定位也最易被忽略的一类。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"], "source": ["reference/sos-heap-and-objects.md#4. !gcroot"]}
{"id": "dotnet-debugging.ref.wpf-leak-rootchain-lookup", "kind": "reference", "file": "reference/wpf-leak-patterns.md", "anchor": "6. 根链形态图鉴速查表", "title": "根链反查表：从内部类型名倒推泄漏类型", "tags": ["root-chain", "reverse-lookup", "leak-classification", "internal-types", "quick-reference", "wpf"], "summary": "按 !gcroot 输出中出现的 WPF 内部类型名反查属于哪类泄漏——排查现场更常见的方向是拿到一条链却不知它属于哪类，正查（已知类型读对应节）与反查（已知链倒推类型）是两个入口。", "applies_to": [".NET Framework 4.x", ".NET 6+", "Windows"]}
```

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

预期：**PASS**（不是 FAIL）——Task 2 Step 3 已把 6 个标题全部建好，本 Task 的 3 条 anchor 直接命中空标题。这是本 Task 与 Task 1/2 的差异：契约在上个 Task 就锁死了。

- [ ] **Step 2: 核对领域记录数**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging --audit
```

预期：领域 **74** 条（reference **69**、rule **5**）= 64 + 4（Task 1）+ 3（Task 2）+ 3（Task 3）。Task 4 与 Task 5 均不增条目，故此处已是终值。

数字对不上时先查两件事：是否有 Task 漏提交；`index.jsonl` 是否有重复行（追加式写入的常见故障）。

- [ ] **Step 3: 补核验待查事实 #2，填 § 4（弱事件泄漏）**

查证 `WeakEventManager` 内部表的类型名与清理时机。来源：`dotnet/wpf` 中 `WeakEventManager` / `WeakEventTable` 实现。

关注三点：（a）内部表的实际类型名；（b）清理是否为摊销式、由什么操作触发；（c）表项在监听者被回收后是否立即移除。

三段结构填写：

`### 堆上的可见特征`：`WeakEventManager` 派生类型或其内部表结构的实例数/体积增长，而应用自身对象数正常。**这是与其余三类的关键差异**——泄漏体现在 WPF 内部结构上，不在应用对象上，用 `!dumpheap -stat` 按应用类型名筛查**看不到**它。

`### 根链形态`：按查证结果写。查不到确切类型名时，按 Global Constraints 降级：写「根链指向 WeakEventManager 的内部监听表」并标注经验性，不编造 `WeakEventTable` 的具体字段名。

`### 判据与下一步` 双向：**证实**——管理器内部表体积随订阅/退订周期单调增长且不回落；**排除**——内部表体积稳定 → 弱事件机制工作正常，泄漏另有成因，转 § 5。

**必写的反直觉点**：「用了弱事件所以不会泄漏」是错误推论。弱的是监听者一侧（监听者可被回收），管理器内部的表项本身仍占内存，清理是摊销式的而非即时的。

- [ ] **Step 4: 填 § 5（DispatcherTimer 泄漏）**

复用 Task 1 Step 4 关于 `Dispatcher` 生命周期锚点的查证结论，并补查待查事实 #3（`DispatcherTimer` 到 `Dispatcher` 的实际引用字段与方向）。来源：`dotnet/wpf` 中 `DispatcherTimer` 实现。

`### 堆上的可见特征`：`DispatcherTimer` 实例数超出应用预期活动定时器数；其 `Tick` 委托的 `Target` 指向本应已销毁的界面元素或 ViewModel。

`### 根链形态`（机制链，二级事实可推导）：

```
Dispatcher（应用级生命周期，GC 根可达）
  → 未 Stop 的 DispatcherTimer
    → Tick 委托
      → 委托 Target（界面元素 / ViewModel）
        → 其整个对象图
```

链的具体字段名按查证结果写；查不到则写方向性描述并标注经验性。

`### 判据与下一步` 双向：**证实**——`!gcroot` 根链起点为 `Dispatcher`、中途经过 `DispatcherTimer`；**排除**——`DispatcherTimer` 实例数在预期内 → 转 § 6 反查表按实际根链形态重新分类。

下一步以 ` § ` 指向 `knowledge-base/wpf/rules/09-threading.md § 7. 定时器与调度`（预防侧）。

- [ ] **Step 5: 填 § 6（根链形态图鉴速查表）**

本节是**反查入口**，不重复 § 2–5 的内容，只做映射。表结构：

| `!gcroot` 输出中出现的标志物 | 泄漏类型 | 详见 |
|---|---|---|
| PropertyDescriptor 订阅相关静态表 | Binding 泄漏 | `§ 2. Binding 泄漏` |
| `ResourceDictionary` / 应用静态字段 → 元素 | 可视化树泄漏（静态资源） | `§ 3. 可视化树泄漏` |
| 父元素 → 子元素集合 → 元素 | 可视化树泄漏（逻辑父级） | `§ 3. 可视化树泄漏` |
| 委托 `_invocationList` → 元素 | 可视化树泄漏（未退订事件） | `§ 3. 可视化树泄漏` |
| `WeakEventManager` 内部监听表 | 弱事件泄漏 | `§ 4. 弱事件泄漏` |
| `Dispatcher` → `DispatcherTimer` → 委托 | DispatcherTimer 泄漏 | `§ 5. DispatcherTimer 泄漏` |

**标志物列的写法须与 § 2–5 各节 `### 根链形态` 段一致**——反查表是索引不是新事实，两处写法分叉会让读者反查到一个查不到的说法。若某节按事实分级降级成了模糊表述，本表对应行同步降级。

表后补一段**反查失败时的出路**：根链末端不匹配上表任何一行 → 不是本篇四类泄漏，可能是应用自身的静态集合持有（通用形态，见 `reference/debugging-decision-tree.md § 2. 内存持续增长`）或非托管泄漏（见同节 `!eeheap` 判据）。不给出路的速查表会让读者卡在「查不到」。

- [ ] **Step 6: 跑三个校验器**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
```

本 Task 的 ` § ` 引用密集（§ 6 一节就有 6 处指向本篇其余小节），`check_refs.py` 必须 PASS。

- [ ] **Step 7: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/wpf-leak-patterns.md
git add knowledge-base/dotnet-debugging/index.jsonl
git commit -m "docs(kb): dotnet-debugging 补齐 WPF 泄漏形态图鉴（弱事件、DispatcherTimer、反查表）"
```

---

### Task 4: 决策树接入 WPF 分支

**Files:**
- Modify: `knowledge-base/dotnet-debugging/reference/debugging-decision-tree.md`（§ 1 与 § 2 各加一处）
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（改 2 条 summary，不增不删）

**Interfaces:**
- Consumes: Task 1 的 anchor `3. Dispatcher 队列积压 vs 真死锁`；Task 2 的 anchor `1. WPF 泄漏的共同取证起点`

**本 Task 的硬约束：不删除、不改写任何既有内容。** 两处均为**追加**——决策树服务全部 .NET 应用，WPF 只是其中一类；改动既有行会让非 WPF 读者的路径变窄。

- [ ] **Step 1: 在 § 1 追加 WPF 分支**

现状：`## 1. 进程挂起 / 无响应` 的 `### 候选根因` 段为一行文字（「Monitor 死锁、异步死锁（同步等待异步）、线程池饥饿、长时间 GC 暂停、等待外部 I/O 无超时。」），`### 取证命令与判据` 段为 4 行表格。

两处改动：

1. `### 候选根因` 一行文字末尾**追加**一项：「；WPF 应用另有 UI 线程被阻塞与 Dispatcher 队列积压两类，见下表末行」
2. `### 取证命令与判据` 表格**末尾追加一行**：

```markdown
| `!clrstack`（WPF 应用，`reference/wpf-dispatcher-deadlock.md § 3. Dispatcher 队列积压 vs 真死锁`） | UI 线程栈顶形态 | 栈顶为等待原语 → 证实 UI 线程被阻塞；栈顶为业务帧 → 证实队列积压而非死锁 |
```

该行的「看什么/结论」两列须与既有 4 行的写法一致（既有行结论列均为「X → 排除/证实 Y」的形态）。

- [ ] **Step 2: 在 § 2 追加 WPF 分支**

现状：`## 2. 内存持续增长` 的 `### 取证命令与判据` 段为 4 行表格，首行是 `!dumpheap -stat`。

`### 取证命令与判据` 表格**末尾追加一行**：

```markdown
| `!dumpheap -stat -type <WPF 类型>`（WPF 应用，`reference/wpf-leak-patterns.md § 1. WPF 泄漏的共同取证起点`） | Window/UserControl/BindingExpression/DispatcherTimer 实例数是否超出应用预期活动数 | 超出 → 证实 WPF 特有泄漏，按根链形态分类；均在预期内 → 排除 WPF 四类泄漏，回到本表前四行查通用成因 |
```

`### 候选根因` 段**不改**——该段列的是通用成因（托管对象泄漏、LOH 碎片化、非托管泄漏、加载器堆增长），WPF 四类泄漏是「托管对象泄漏」的细分，不是并列项。

- [ ] **Step 3: 更新两条索引的 summary**

`id` / `anchor` / `file` / `applies_to` **全部不动**（改动会破坏既有引用；`applies_to` 保持 `[".NET Framework 4.x", ".NET 6+"]`——决策树条目讲的是通用征象，不是 WPF 专属）。只在 `summary` 末尾追加一句：

```jsonl
{"id": "dotnet-debugging.ref.symptom-hang", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "1. 进程挂起", "title": "征象：进程挂起 / 无响应的取证路径", "tags": ["hang", "unresponsive", "deadlock", "symptom", "triage"], "summary": "进程无响应时的候选根因（Monitor 死锁、异步死锁、线程池饥饿、长时间 GC）与各自的取证命令及区分判据；WPF 应用另有 UI 线程阻塞与 Dispatcher 队列积压两类，转 wpf-dispatcher-deadlock 篇。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
{"id": "dotnet-debugging.ref.symptom-memory-growth", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "2. 内存持续增长", "title": "征象：内存持续增长的取证路径", "tags": ["memory-growth", "leak", "symptom", "triage", "loh", "unmanaged-memory"], "summary": "内存增长的候选根因（托管泄漏、LOH 碎片、非托管泄漏、加载器堆增长）与区分它们的命令序列入口；其中 !gchandles 仅 Windows 平台支持；WPF 应用的托管泄漏可按四类特有形态细分，转 wpf-leak-patterns 篇。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
```

替换 `index.jsonl` 中对应两行（**整行替换，不是追加**——追加会产生重复 id，`check_index.py` 会报错）。

- [ ] **Step 4: 校验并核对条目数未变**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
```

预期：领域仍为 **74** 条（本 Task 改 summary 不增删）。若变成 76，说明 Step 3 误用了追加而非替换。

- [ ] **Step 5: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/debugging-decision-tree.md
git add knowledge-base/dotnet-debugging/index.jsonl
git commit -m "docs(kb): dotnet-debugging 决策树接入 WPF 归因分支"
```

---

### Task 5: 版本、元数据与终检

**Files:**
- Modify: `knowledge-base/dotnet-debugging/README.md`（版本行、定位段、阅读路径表、文件地图表）
- Modify: `knowledge-base/dotnet-debugging/CHANGELOG.md`（顶部插入 1.2.0）
- Modify: `knowledge-base/catalog.json`（`dotnet-debugging` 条目的 `notes`）
- Modify: `docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md`（分期路标表三期行）

**Interfaces:**
- Consumes: Task 1–4 的全部产出

- [ ] **Step 1: 改领域 README 四处**

1. 第 3 行 `> 版本：1.1.0` → `> 版本：1.2.0`

2. **定位段补 WPF 分支说明**（spec § 1.2）。现状第 5 行为「覆盖 .NET Framework 4.x、.NET 6/8+ 与 Linux 容器三种运行时」。在该段之后**追加一句**：

```markdown
本领域以三运行时共性层为主干，**WPF 专属归因作为独立分支收录**（`reference/wpf-*.md` 两篇，仅 Windows）——WPF 是本仓库核心技术栈，其 Dispatcher 死锁与四类泄漏的根链形态无法由通用 SOS 读法直接得出。
```

3. 「阅读路径」表**追加两行**（放在 `rules/01-dump-handling.md` 行之前，保持「先诊断后合规」的既有顺序）：

```markdown
| WPF 界面无响应 / UI 线程卡死 | `reference/wpf-dispatcher-deadlock.md` |
| WPF 内存泄漏 / 窗口关不掉还在堆上 | `reference/wpf-leak-patterns.md` |
```

4. 「文件地图」表**追加两行**（放在 `live-monitoring-decision.md` 行之后、`rules/` 行之前）：

```markdown
| `reference/wpf-dispatcher-deadlock.md` | 认出 UI 线程、三类等待形态、队列积压与真死锁的区分、持锁方定位闭环（仅 WPF/Windows） |
| `reference/wpf-leak-patterns.md` | 四类 WPF 泄漏（Binding / 可视化树 / 弱事件 / DispatcherTimer）的堆上特征、根链形态与反查速查表（仅 WPF/Windows） |
```

改完文件地图应为 **15 行**（一期 9 + 二期 4 + 本期 2）。

- [ ] **Step 2: 加 CHANGELOG 1.2.0 条目**

插在 `## [1.1.0] - 2026-09-05` **之上**（本仓库 CHANGELOG 为倒序）：

```markdown
## [1.2.0] - 2026-09-05

### Added
- 新增 2 篇 reference：WPF Dispatcher 死锁归因、WPF 泄漏形态图鉴，索引新增 10 条（64 → 74）
- 领域定位调整：以三运行时共性层为主干，WPF 专属归因作为独立分支收录（仅 Windows）
- 泄漏篇含根链反查表，支持「拿到一条 !gcroot 输出倒推属于哪类泄漏」这一排查现场更常见的方向

### Changed
- `debugging-decision-tree.md § 1. 进程挂起` 与 `§ 2. 内存持续增长`：各追加一行 WPF 分支入口，既有内容与结论不变
```

**不要写 `### Removed`**——本期无删除，这正是定为 Minor 而非 Major 的依据（spec § 1.3）。

- [ ] **Step 3: 改 `catalog.json` 的 notes**

现状末句：「含活体监控工具链（EventPipe / dotnet-counters / dotnet-trace，仅 .NET 5+）；暂不含 PerfView/ETW 与 WPF 专属归因」。

改为：「含活体监控工具链（EventPipe / dotnet-counters / dotnet-trace，仅 .NET 5+）与 WPF 专属归因分支（Dispatcher 死锁、四类泄漏形态，仅 Windows）；暂不含 PerfView/ETW」。

只改这一句，`domain` / `categories` / `consumers` 等字段不动（`consumers` 仍为空——本期无 skill 消费者）。`reviewed_at` 保持 `2026-09-05`（同日）。改后确认 JSON 仍可解析：

```bash
python -c "import json;json.load(open('knowledge-base/catalog.json',encoding='utf-8'));print('OK')"
```

- [ ] **Step 4: 标注一期 spec 的三期行为已交付**

`docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md` 的分期路标表，三期行「WPF 桌面 dump 归因」的范围列**末尾追加**：

```
（已于 2026-09-05 交付，实施 spec 见 docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-phase3-design.md）
```

二期行同理若尚未标注，一并补上指向二期 spec 的说明。**不改期次编号**（二期/三期顺序已在上一期调换完成，本次不再动）。

- [ ] **Step 5: 全量终检**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging --audit
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
```

逐条核对 spec 第 8 节的完成判定：

| 检查项 | 预期 |
|---|---|
| 全局记录数 | **576**（= 566 + 10） |
| 领域记录数 | **74**（reference **69**、rule **5**） |
| `--audit` 孤儿文件 | 无 |
| `check_refs.py` | PASS |
| `find_duplicates.py` | 本期条目与 spec § 5.1 所列五条 wpf 条目相似度 < 0.5 |
| 本期新增条目 `applies_to` | 均为 `[".NET Framework 4.x", ".NET 6+", "Windows"]`，**无 Linux** |
| 两篇文件头 | 均含 WPF 专属 + 仅 Windows 声明 |
| README 文件地图 | 15 行 |
| README 定位段 | 已含 WPF 分支说明 |
| 版本一致性 | README `1.2.0` == CHANGELOG 最新条目 |
| 决策树 | 两处已增补，既有内容零删除 |
| 待核验清单 | spec § 7.3 六条全部处理（查到的写实注明出处，查不到的标注经验性） |

`applies_to` 单独验：

```powershell
Get-Content knowledge-base/dotnet-debugging/index.jsonl | Select-String 'wpf-identify-ui-thread|wpf-ui-wait-forms|wpf-queue-vs-deadlock|wpf-lock-owner-loop|wpf-leak-' | Select-String 'Linux'
```

预期：**无输出**。有输出说明某条误标了 Linux——WPF 不跨平台（spec § 6 指出平台标注是本领域已知易错点，一期为此提交过修正 commit `c8603f8`）。

决策树零删除单独验：

```bash
git diff HEAD~4 -- knowledge-base/dotnet-debugging/reference/debugging-decision-tree.md | grep '^-' | grep -v '^---'
```

预期：**无输出**（纯追加，无删除行）。有输出说明 Task 4 违反了「不删除、不改写」的硬约束。

- [ ] **Step 6: 提交并推送**

```bash
git add knowledge-base/dotnet-debugging/README.md
git add knowledge-base/dotnet-debugging/CHANGELOG.md
git add knowledge-base/catalog.json
git add docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md
git commit -m "docs(kb): dotnet-debugging 升版 1.2.0，更新定位、文件地图、catalog 与分期路标"
```

推送走 `commit-cc-plugin` skill（本仓库禁止手动推送）。**不升 `.claude-plugin/marketplace.json`**——本期未动 `plugins/` 与 `.claude/`。

---

## 自查记录

写完后对照 spec 逐节核查的结果：

| spec 节 | 落位 |
|---|---|
| 1. 背景与定位调整 | Task 5 Step 1（README 定位段）+ Step 4（一期 spec 路标标注） |
| 2. 范围 | File Structure（2 篇）；2.2 排除项无对应 Task（有意不做） |
| 3. 篇目结构与接口契约 | Task 1–3 的 Interfaces 段逐字锁定全部 10 个 anchor；3.3 两处增补 → Task 4；3.4 实施顺序 → Task 索引的顺序依据 |
| 4. 判据范式 | Global Constraints（判据段标题固定、须双向写、禁绝对阈值）+ 各 Task 的判据 Step |
| 5. 与 wpf 领域的边界 | Global Constraints（跨领域引用写正文）+ Task 1 Step 8 / Task 2 Step 8 的查重比对对象 + Task 5 Step 5 终检 |
| 6. applies_to 约定 | Global Constraints 取值固定 + 各 Task 索引 JSON 已写死 + Task 5 Step 5 的 PowerShell 验证命令 |
| 7. 事实核验与待核验清单 | Global Constraints 事实分级 + 「待核验事实的处理位置」表把 6 条绑定到具体 Step（#1→T2S6、#2→T3S3、#3→T3S4、#4→T1S4、#5→T1S4、#6→T1S7） |
| 8. 完成判定 | Task 5 Step 5 逐条对应，「约 10 条」已定死为 10 条 |
| 9. 不在本期范围 | 无 Task（有意不做） |

三处与 spec 的偏差，均为写计划时收紧：

1. spec § 3.2 把泄漏篇当作一个交付单元，本计划**拆为 Task 2 与 Task 3** ——该篇 6 节且含全期最难的 3 条待核验事实，单 Task 过大，一个 reviewer 无法有效 gate
2. spec § 7.3 只列出 6 条待核验事实，本计划**把每条绑定到具体 Step**并写明查不到时的降级写法——不绑定则会变成「写到哪儿想起来再查」
3. spec § 8 的完成判定为文字清单，本计划**补了两条可执行的验证命令**（`applies_to` 无 Linux 的 PowerShell 检索、决策树零删除的 `git diff` 检索）——文字判定无法自动核对

一处需要执行者注意的结构安排：**Task 2 Step 3 建骨架时一次建齐 6 个 `##` 标题**（含 Task 3 的三节），因此 Task 3 Step 1 追加索引后校验预期是 PASS 而非 FAIL——这与 Task 1/2 的 TDD 循环形态不同，是有意为之，避免 Task 3 再次改动文件头。
