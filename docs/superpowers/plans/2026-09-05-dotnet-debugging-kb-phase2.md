# dotnet-debugging 知识库（二期）：活体监控工具链实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `knowledge-base/dotnet-debugging/` 领域新增活体监控工具链（4 篇 reference、约 20 条索引），并回填一期在三处正文留下的「留待后续期次」欠条。

**Architecture:** 沿用一期的领域结构与四段命令结构（用途与前置条件 / 语法与关键开关 / 输出逐列语义 / 判据）。与一期唯一的结构性差异在判据段：一期是单时点布尔判定，本期改为「基线形态 / 异常形态 / 区分点」三元组——时间序列的信息在趋势里而非数值里。计数器命名在 .NET 9 前后分叉，用双列对照表隔离，判据文字只写一次。

**Tech Stack:** Markdown + JSONL 索引；校验工具为仓库自带 Python 脚本（`check_index.py` / `find_duplicates.py` / `check_refs.py`，本机只有 `unittest`，无 `pytest`）。

**Spec:** `docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-phase2-design.md`

## Global Constraints

以下约束适用于**每一个** Task，不再逐条重复。多数继承自一期，标注「本期新增」的是二期特有。

- **域名与 id 前缀**：域名 `dotnet-debugging`；本期全部为 reference 条目，id 形式 `dotnet-debugging.ref.<slug>`。`ID_RE = ^[a-z0-9-]+\.(?:\d{2}|ref)\.[a-z0-9-]+$`，**slug 只能含小写字母、数字、连字符**。
- **正文语言中文，`tags` 全英文**：严格遵守，tag 用小写字母加连字符。
- **`anchor` 填中文标题文本**（非 slug），`check_index.py` 按 `anchor in heading` 子串匹配。标题含斜杠或括号时，`anchor` 取不含歧义字符的前缀子串即可。
- **索引 `source` 字段只用于领域内引用**，形式 `reference/<file>.md#<标题文本>`。**跨领域引用一律写在正文里**，形式 `knowledge-base/<domain>/rules/NN-x.md § 章节`。跨领域路径写进 `source` 会被路径越界检查拦截。
- **两种引用符号服务于两个校验器，不得混用**：

  | 位置 | 符号 | 形式 | 校验者 |
  |---|---|---|---|
  | 索引 `source` 字段 | `#` | `reference/eventpipe-and-diagnostic-port.md#2. 诊断端口与连接建立` | `check_index.py` 的 `check_source_refs` |
  | **正文**交叉引用（含领域内与跨领域） | ` § ` | `reference/dotnet-counters.md § 3. 内置计数器与判据对照` | `check_refs.py` |

  正文里写 `#` 不会报错，但 `check_refs.py` 检不到——引用会静默失效。**正文一律用 ` § `。**

- **`applies_to` 对 reference 条目必填**（一期约定）。**本期新增约束：全部条目不含 `.NET Framework 4.x`**——EventPipe 是 .NET Core+ 的运行时特性，Framework 完全不可用。取值按下表：

  | 条目类型 | `applies_to` |
  |---|---|
  | `dotnet-counters` / `dotnet-trace collect` / EventPipe 机制 | `[".NET 5+", "Windows", "Linux"]` |
  | `collect-linux` 相关 | `[".NET 10+", "Linux"]` |
  | 涉及 .NET 9+ Meter 命名的条目 | `[".NET 5+", "Windows", "Linux"]`（正文内区分版本，不在 `applies_to` 拆分） |

  一期曾因 `applies_to` 平台标注错误单独提交修正（commit `c8603f8`），这是已知易错点。

- **判据段标题固定**（本期新增）：`### 判据：基线形态 / 异常形态 / 区分点`。三段缺一不可。
- **不写绝对数值阈值**（本期新增）：不写「gen2 GC 超过 N 次/分钟即异常」这类阈值。官方文档或运行时默认值本身给出的硬数字（如 `--buffersize` 默认 256 MB）属事实而非阈值，照实写并标注出处。
- **每条判据须接回一期命令**（本期新增）：「区分点」段落须给出下一步动作，指向一期的具体 SOS 命令。活体监控定位方向，SOS 定位根因。
- **分段写入**：单篇 reference 预计数百行，必须先 `Write` 骨架再多次 `Edit` 逐段填充，禁止单次输出整篇。
- **事实以 spec 第 8 节为准**：spec 已核验 .NET 9+ 全部 18 个运行时计数器、EventPipe 六个环境变量、EventPipe 与 ETW 的能力对照表。**实施时直接引用，不重新查证**；spec 8.4 列出的两项未核验事实，写到对应小节时才查。
- **版本号**：领域 `README.md` 顶部版本行改为 `> 版本：1.1.0`，须与 `CHANGELOG.md` 最新条目一致。**不升 `.claude-plugin/marketplace.json`**——本期不动 `plugins/` 与 `.claude/`。
- **提交**：每个 Task 末尾提交。本仓库禁止手动 git 工作流，但**执行本计划期间的逐 Task 提交例外**——逐 Task 用直接 git 命令，最终推送前再走一次 `commit-cc-plugin`。提交类型统一 `docs(kb)`，`Co-Authored-By` 填当前会话实际模型名。

---

## File Structure

| 文件 | 责任 | 产出 Task |
|---|---|---|
| `reference/eventpipe-and-diagnostic-port.md` | 机制基础：EventPipe/诊断端口/Provider 模型/两套计数器体系/缓冲区/基线采集。后续三篇的术语基础 | Task 1 |
| `reference/dotnet-counters.md` | `monitor` / `collect` 两个子命令 + 内置计数器判据对照表 | Task 2 |
| `reference/dotnet-trace.md` | `collect` / profile 选择 / `report topN` / 格式转换 | Task 3 |
| `reference/live-monitoring-decision.md` | 六类征象 → 采集方案查表 | Task 4 |
| `debugging-decision-tree.md`（改） | § 5 整节重写，结论从否定翻转为可操作路径 | Task 5 |
| `dump-types-and-capability.md`（改） | § 3 末段改为指向新篇 | Task 5 |
| `dump-capture.md`（改） | § 1 判据段补一句优先级说明 | Task 5 |
| `README.md` / `CHANGELOG.md` / `catalog.json` / 一期 spec（改） | 版本、文件地图、领域 notes、分期路标 | Task 6 |

**任务顺序依据**：机制篇最先（其定义的诊断端口、Provider 模型、两套计数器体系被后续全部引用）；`dotnet-counters` 与 `dotnet-trace` 可互换顺序但都依赖机制篇；决策篇倒数第三（要指向前三篇的全部 anchor）；回填倒数第二（要指向决策篇的新 anchor）；收尾最后。

**TDD 在本计划中的形态**：知识库无单元测试，`check_index.py` 就是测试运行器。每个 Task 遵循「先写索引条目跑校验看它报错 → 补正文 → 再跑校验看它通过」的循环，与代码 TDD 同构。

---

## Task 索引

| Task | 交付物 | 索引增量 |
|---|---|---|
| 1 | `eventpipe-and-diagnostic-port.md`（6 节） | +6 |
| 2 | `dotnet-counters.md`（3 节） | +4 |
| 3 | `dotnet-trace.md`（4 节） | +5 |
| 4 | `live-monitoring-decision.md`（6 节） | +6 |
| 5 | 回填一期三处 | 0（改 1 条 summary） |
| 6 | 版本、文件地图、catalog、spec 路标、终检 | 0 |

**索引总增量 21 条**，全局记录数 544 → **565**。领域内 42 → 63（reference 37 → 58，rule 仍 5）。

> **实施后修订**：最终审查发现 `trace-cpu-sampling-removed` 一条同时承载 `collect` 与 `collect-linux` 两种适用范围，`applies_to` 无论取哪个都不准确，故拆出独立条目 `trace-collect-linux`（`[".NET 10+", "Linux"]`）。实际增量 **22 条**，全局 **566**，领域 **64**（reference 59）。

上述基数已于 2026-09-05 实测确认（`check_index.py` 全局 544 条；`dotnet-debugging` 42 条，其中 reference 37、rule 5）。验收按这些数字硬核对，不接受「约」。

---

### Task 1: EventPipe 与诊断端口机制篇

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/eventpipe-and-diagnostic-port.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 6 行）

**Interfaces:**
- Consumes: 无（本期第一个 Task）
- Produces: 六个 anchor，供 Task 2/3/4 在正文中以 ` § ` 引用，且**逐字不可改**：
  - `1. EventPipe 与 ETW 的关系`
  - `2. 诊断端口与连接建立`
  - `3. Provider / Keyword / Level 三级过滤`
  - `4. EventCounter 与 Meter 两套计数器体系`
  - `5. 采集开销与缓冲区`
  - `6. 基线采集：时间线判据的前置条件`
- Produces: 六条索引 id，供后续 Task 的 `source` 字段引用：`dotnet-debugging.ref.eventpipe-vs-etw` / `.diagnostic-port` / `.provider-keyword-level` / `.eventcounter-vs-meter` / `.eventpipe-buffer` / `.baseline-capture`

- [ ] **Step 1: 先追加 6 条索引，让校验失败**

追加到 `knowledge-base/dotnet-debugging/index.jsonl` 末尾（每条一行，JSON 不换行）：

```jsonl
{"id": "dotnet-debugging.ref.eventpipe-vs-etw", "kind": "reference", "file": "reference/eventpipe-and-diagnostic-port.md", "anchor": "1. EventPipe 与 ETW 的关系", "title": "EventPipe 与 ETW：采集通道的能力边界", "tags": ["eventpipe", "etw", "perf-events", "tracing", "capability-boundary"], "summary": "EventPipe 为运行时内置、跨平台、无需 admin/root，但作用域限于托管代码——不含内核事件、不能解析原生调用栈；需要原生栈或内核事件时必须转向 ETW 或 perf_events。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.diagnostic-port", "kind": "reference", "file": "reference/eventpipe-and-diagnostic-port.md", "anchor": "2. 诊断端口与连接建立", "title": "诊断端口：IPC 通道与容器跨 namespace 约束", "tags": ["diagnostic-port", "ipc", "named-pipe", "unix-socket", "tmpdir", "container"], "summary": "诊断端口的传输形式（Windows 命名管道 / Linux-macOS Unix domain socket）、DOTNET_DiagnosticPorts 的 listen 与 connect 两个方向，以及容器跨 PID namespace、TMPDIR 不共享时命令超时的成因。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.provider-keyword-level", "kind": "reference", "file": "reference/eventpipe-and-diagnostic-port.md", "anchor": "3. Provider", "title": "Provider / Keyword / Level：三级事件过滤语法", "tags": ["provider", "keyword", "verbosity-level", "clr-events", "event-filtering"], "summary": "KnownProviderName[:Flags[:Level[:KeyValueArgs]]] 语法、CLR provider 的 keyword 十六进制位掩码与字符串别名映射，以及 Level 六档取值——过滤写错会静默少采事件而非报错。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.eventcounter-vs-meter", "kind": "reference", "file": "reference/eventpipe-and-diagnostic-port.md", "anchor": "4. EventCounter 与 Meter 两套计数器体系", "title": "EventCounter 与 Meter：.NET 9 的计数器命名分水岭", "tags": ["eventcounter", "meter", "system-runtime", "counter-naming", "version-fork"], "summary": "System.Runtime Meter 自 .NET 9 起提供，.NET 8 及更低版本不存在该 Meter，工具会自动回退到旧 EventCounters；同一指标在两套体系下名称与单位表示均不同，判据引用计数器名时必须区分运行时版本。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.eventpipe-buffer", "kind": "reference", "file": "reference/eventpipe-and-diagnostic-port.md", "anchor": "5. 采集开销与缓冲区", "title": "采集缓冲区：溢出丢事件是静默失败", "tags": ["buffersize", "circular-buffer", "event-loss", "silent-failure", "collection-overhead"], "summary": "工具侧 --buffersize 与运行时侧 DOTNET_EventPipeCircularMB 是两个不同层级的缓冲区；事件产生快于落盘时缓冲区溢出会丢事件且不报错，采集结果看似正常却已残缺。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.baseline-capture", "kind": "reference", "file": "reference/eventpipe-and-diagnostic-port.md", "anchor": "6. 基线采集", "title": "基线采集：时间线判据的前置条件", "tags": ["baseline", "timeline", "comparison", "sampling-window", "prerequisite"], "summary": "无基线的时间线数据不可判读——同一数值可能是正常水位、泄漏中途或回收前峰值；基线的采集时机、时长与对齐方式，是本领域全部时间线判据的共用前提。", "applies_to": [".NET 5+", "Windows", "Linux"]}
```

- [ ] **Step 2: 运行校验，确认它因文件缺失而失败**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

预期：FAIL，6 条报错指向 `reference/eventpipe-and-diagnostic-port.md` 不存在。**看到这个失败才说明索引确实被校验器读到了**——直接写正文再补索引会跳过这层验证。

- [ ] **Step 3: 写文件骨架（只有标题，不填正文）**

创建 `reference/eventpipe-and-diagnostic-port.md`，内容为文件头 + 6 个 `##` 标题（逐字照抄上方 Interfaces 段）。文件头：

```markdown
# EventPipe 与诊断端口

> **运行时要求**：EventPipe 是 .NET Core+ 的运行时内置特性，**.NET Framework 4.x 完全不可用**。Framework 的活体诊断依赖 ETW / PerfView，不在本领域当前范围内。

本篇只讲机制不讲命令，是 `reference/dotnet-counters.md` 与 `reference/dotnet-trace.md` 的术语基础。两篇中每条命令的「用途与前置条件」段都会指回本篇。
```

- [ ] **Step 4: 再跑校验，确认 6 条 anchor 全部命中**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

预期：PASS。此时正文还是空的，但索引契约已经锁死——后续填正文不会再改动标题。

- [ ] **Step 5: 填 § 1（EventPipe 与 ETW 的关系）**

核心是 spec 8.7 的能力对照表，原样搬入（EventPipe / EventPipe(user_events) / ETW / perf_events 四列 × 跨平台、需 admin-root、可获取内核事件、可解析原生调用栈四行）。表后须写明两条结论：

1. 「无需 admin/root」是 EventPipe 相对 ETW 的关键实用优势——只要采集工具与目标进程以同一用户运行即可
2. EventPipe 的作用域**限于托管代码与运行时自身**，栈信息只含托管帧。这解释了本领域为何暂不含 PerfView/ETW，也划出了转向 OS 级工具的时机

- [ ] **Step 6: 填 § 2（诊断端口与连接建立）**

要点：

- 传输形式：Windows 为命名管道；Linux / macOS 为 Unix domain socket（落在 `TMPDIR`）；移动端为 IP:port
- `DOTNET_DiagnosticPorts` 的两个方向：默认由运行时 listen、工具 connect；反向（`,connect` 后缀）用于工具先起、进程后启，是 § 6 启动阶段采集的基础
- **容器踩坑（spec 8.3 已核验）**：Linux/macOS 上 `-p` / `-n` 要求工具与目标进程共享同一 `TMPDIR`，否则命令**超时**而非报「找不到进程」。跨 PID namespace 时须显式指定端口
- 权限：工具须与目标进程同用户或 root
- 位数必须匹配，否则报 `System.ComponentModel.Win32Exception (299)`。正文此处以 ` § ` 交叉引用 `reference/dump-types-and-capability.md § 2. 位数必须匹配`

- [ ] **Step 7: 填 § 3、§ 4、§ 5、§ 6（分四次 Edit，不要一次写完）**

- **§ 3**：`KnownProviderName[:Flags[:Level[:KeyValueArgs]]]` 语法；`Flags` 为十六进制位掩码；Level 六档 `logalways`(0) → `critical` → `error` → `warning` → `informational` → `verbose`(5)。写明过滤写窄了是**静默少采**而非报错，这与 § 5 的缓冲区溢出同属静默失败类风险
- **§ 4**：照 spec 8.2 的六行对照示例写。**须写明的两点**：（a）.NET 8 及更低版本无 `System.Runtime` Meter，工具自动 fallback 到旧 EventCounters；（b）新命名的单位随名称独立显示（`(By)` 字节、`(s)` 秒），旧命名的单位内嵌在名称里（`(MB)`、`(%)`）——判据涉及单位换算时必须注意。本节末尾以 ` § ` 指向 `reference/dotnet-counters.md § 3. 内置计数器与判据对照`
- **§ 5**：**必须区分两个层级的缓冲区**（spec 8.3）：工具侧 `dotnet-trace --buffersize` 默认 **256 MB**；运行时侧 `DOTNET_EventPipeCircularMB` 默认 **`400`（十六进制，即 1024 MB）**，仅在以 `DOTNET_EnableEventPipe` 启动会话时生效。混为一谈会写出自相矛盾的默认值。附 spec 8.6 的完整环境变量表。溢出丢事件不报错这一条要写成显式风险提示
- **§ 6**：基线为何不可省（同一个「堆 800 MB」可能是正常水位 / 泄漏中途 / 回收前峰值）；基线应在业务稳态期采、覆盖至少一个完整业务周期、与故障期采集用同一组 provider 和同一采样率，否则两次数据不可比

- [ ] **Step 8: 跑三个校验器**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
```

预期：前两个 PASS；`find_duplicates.py` 中本 Task 的 6 条与 `csharp.11.*` 相似度低于 0.5。

- [ ] **Step 9: 提交**

### Task 2: dotnet-counters 篇

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/dotnet-counters.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 4 行）

**Interfaces:**
- Consumes: Task 1 的 anchor `2. 诊断端口与连接建立`、`4. EventCounter 与 Meter 两套计数器体系`、`6. 基线采集：时间线判据的前置条件`
- Produces: anchor `1. dotnet-counters monitor`、`2. dotnet-counters collect`、`3. 内置计数器与判据对照`（Task 4 与 Task 5 引用）

- [ ] **Step 1: 先追加 4 条索引**

`## 3` 一节拆成 3 条索引（GC / 线程池 / 锁与异常），因为它们分别对应 Task 4 中三类不同征象，合成一条会让检索命中后仍需人工翻找：

```jsonl
{"id": "dotnet-debugging.ref.counters-monitor", "kind": "reference", "file": "reference/dotnet-counters.md", "anchor": "1. dotnet-counters monitor", "title": "dotnet-counters monitor：实时刷新的计数器面板", "tags": ["dotnet-counters", "monitor", "live-metrics", "refresh-interval", "counter-selection"], "summary": "monitor 子命令的进程定位（-p/-n/--diagnostic-port）、--counters 指定 provider 与计数器、--refresh-interval 采样间隔；无历史留存，只适合现场观察趋势。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.counters-collect", "kind": "reference", "file": "reference/dotnet-counters.md", "anchor": "2. dotnet-counters collect", "title": "dotnet-counters collect：计数器落盘与事后比对", "tags": ["dotnet-counters", "collect", "csv", "json", "timeline", "offline-analysis"], "summary": "collect 子命令的 --format（csv/json）、-o 输出路径与 --refresh-interval；落盘后可与基线数据对齐比对，是间歇性问题唯一可复盘的采集方式。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.counters-gc-metrics", "kind": "reference", "file": "reference/dotnet-counters.md", "anchor": "3. 内置计数器与判据对照", "title": "GC 与内存计数器：堆增长与 GC 压力的形态判据", "tags": ["gc-counters", "heap-size", "gc-pause", "allocation-rate", "memory-growth", "leak-detection"], "summary": "堆大小、提交量、碎片、暂停时间、分配速率五组计数器在 .NET 9+ 与 .NET 8- 下的名称对照，及其基线形态与异常形态——包络线上升判为泄漏、振幅增大判为分配压力，二者在单时点 dump 中无法区分。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/eventpipe-and-diagnostic-port.md#4. EventCounter 与 Meter 两套计数器体系"]}
{"id": "dotnet-debugging.ref.counters-threadpool-metrics", "kind": "reference", "file": "reference/dotnet-counters.md", "anchor": "3. 内置计数器与判据对照", "title": "线程池、锁与异常计数器：饥饿与竞争的形态判据", "tags": ["threadpool-counters", "queue-length", "lock-contention", "exception-rate", "starvation", "first-chance"], "summary": "线程池队列长度与线程数、锁竞争次数、异常速率三组计数器的双版本名称与形态判据；异常计数为 first-chance 语义，基线未必接近 0，须按应用自身基线判读。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/eventpipe-and-diagnostic-port.md#4. EventCounter 与 Meter 两套计数器体系"]}
```

两条 `counters-*-metrics` 共用同一 `anchor` 是**有意为之**——`check_index.py` 按 `anchor in heading` 子串匹配，不要求 anchor 唯一；一期 `dump-capture.md` 已有多条索引指向同一文件的先例。

- [ ] **Step 2: 跑校验确认失败**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

预期：FAIL，4 条报错指向文件不存在。

- [ ] **Step 3: 写骨架并复跑校验**

创建文件，写文件头 + 三个 `##` 标题（逐字：`## 1. dotnet-counters monitor` / `## 2. dotnet-counters collect` / `## 3. 内置计数器与判据对照`），跑 `check_index.py dotnet-debugging` 预期 PASS。

- [ ] **Step 4: 填 § 1 与 § 2（四段结构，分两次 Edit）**

两节均按一期四段结构写：`### 用途与前置条件` / `### 语法与关键开关` / `### 输出逐列语义` / `### 判据：基线形态 / 异常形态 / 区分点`。

「用途与前置条件」段两节都要指回 Task 1：

```markdown
前置条件见 `reference/eventpipe-and-diagnostic-port.md § 2. 诊断端口与连接建立`（进程定位与权限）与 `§ 6. 基线采集：时间线判据的前置条件`（没有基线时本命令的输出不可判读）。
```

`monitor` 与 `collect` 的分工要写清：`monitor` 无历史留存、关掉即丢，只适合现场观察；`collect` 落盘，是间歇性问题唯一可复盘的方式。间歇性问题**必须**用 `collect`——这是回填 Task 5 § 5 的依据。

- [ ] **Step 5: 填 § 3（双列对照表）**

表头六列：`指标` / `.NET 9+ 名` / `.NET 8- 名` / `基线形态` / `异常形态` / `下一步`。行取自 spec 8.5 已核验的清单，至少覆盖：堆大小、提交量、碎片量、GC 次数（分代）、GC 暂停时间、累计分配量、线程池线程数、线程池队列长度、工作项完成数、锁竞争次数、异常数、工作集、计时器数、程序集数。

**三条必写的语义陷阱**（spec 8.5，直接影响判据正确性）：

1. `dotnet.gc.heap.total_allocated` 是**自进程启动的累计量**，不是当前堆占用——判泄漏须看 `dotnet.gc.last_collection.heap.size`
2. `dotnet.gc.last_collection.memory.committed_size` **可大于堆大小**（含为未来分配预留的部分），不可将二者差值直接判为碎片；碎片有独立计数器 `dotnet.gc.last_collection.heap.fragmentation.size`
3. `dotnet.exceptions` 计的是 **first-chance** 异常（等价 `AppDomain.FirstChanceException` 触发次数），含已被 catch 的，故其基线**未必接近 0**

「下一步」列一律指向一期 SOS 命令，例如：

| 指标 | 异常形态 | 下一步 |
|---|---|---|
| 堆大小 | 包络线呈上升台阶 | `reference/sos-heap-and-objects.md § 4. !gcroot` |
| 线程池队列长度 | 持续 > 0 且线程数达上限、CPU 不高 | `reference/sos-locks-and-async.md § 3. !threadpool` |
| 锁竞争次数 | 速率陡升伴随吞吐下降 | `reference/sos-locks-and-async.md § 1. !syncblk` |
| 异常数 | 速率相对自身基线陡升 | `reference/sos-threads-and-stacks.md § 4. !pe` |

**不写绝对阈值**——「持续 > 0」是形态描述，「超过 100」是阈值，后者禁止。

- [ ] **Step 6: 跑三个校验器**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
```

`check_refs.py` 是本 Task 最易出错处——§ 3 的「下一步」列有大量 ` § ` 引用，写成 `#` 不报错但会静默失效。

- [ ] **Step 7: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/dotnet-counters.md
git add knowledge-base/dotnet-debugging/index.jsonl
git commit -m "docs(kb): dotnet-debugging 新增 dotnet-counters 篇与内置计数器判据对照"
```

---

### Task 3: dotnet-trace 篇

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/dotnet-trace.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 5 行）

**Interfaces:**
- Consumes: Task 1 的 anchor `2. 诊断端口与连接建立`、`3. Provider / Keyword / Level 三级过滤`、`5. 采集开销与缓冲区`
- Produces: anchor `1. dotnet-trace collect`、`2. profile 选择`、`3. dotnet-trace report topN`、`4. 格式转换与查看`

- [ ] **Step 1: 先追加 5 条索引**

`## 2. profile 选择` 拆成两条——`cpu-sampling` 的同名不同义陷阱单独成条，它是本期最高频的踩坑点，必须能被独立检索命中：

```jsonl
{"id": "dotnet-debugging.ref.trace-collect", "kind": "reference", "file": "reference/dotnet-trace.md", "anchor": "1. dotnet-trace collect", "title": "dotnet-trace collect：事件流采集与停止条件", "tags": ["dotnet-trace", "collect", "providers", "clrevents", "duration", "stopping-event"], "summary": "collect 的进程定位、--providers 与 --clrevents 两种过滤写法、--duration 定时停止与 --stopping-event-* 按事件停止；--buffersize 溢出丢事件是静默失败。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/eventpipe-and-diagnostic-port.md#3. Provider"]}
{"id": "dotnet-debugging.ref.trace-profiles", "kind": "reference", "file": "reference/dotnet-trace.md", "anchor": "2. profile 选择", "title": "内置 profile 的取值与展开语义", "tags": ["trace-profile", "dotnet-common", "sampled-thread-time", "gc-verbose", "provider-expansion"], "summary": "各内置 profile 的适用场景与展开后的 provider 组合；profile 与 --providers 同时指定时的叠加语义，以及 list-profiles 查实际取值的方法。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.trace-cpu-sampling-removed", "kind": "reference", "file": "reference/dotnet-trace.md", "anchor": "2. profile 选择", "title": "cpu-sampling profile 已从 collect 移除：同名不同义陷阱", "tags": ["cpu-sampling", "removed-profile", "collect-linux", "migration", "outdated-tutorial"], "summary": "collect 下的 cpu-sampling 已被移除（原名称误导：它采样所有线程而非仅高 CPU 线程），官方给出的替代写法；同名 profile 在 collect-linux 下仍存在但语义不同，照抄旧教程会直接报错或采到非预期数据。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.trace-report-topn", "kind": "reference", "file": "reference/dotnet-trace.md", "anchor": "3. dotnet-trace report topN", "title": "dotnet-trace report topN：无需外部工具读出热点方法", "tags": ["report-topn", "hotspot", "inclusive", "exclusive", "call-tree", "cpu-attribution"], "summary": "report topN 直接从 nettrace 读出栈上耗时最长的 N 个方法；默认按 exclusive 排序，--inclusive 切换为含被调用方耗时——两者结论可能完全相反。", "applies_to": [".NET 5+", "Windows", "Linux"]}
{"id": "dotnet-debugging.ref.trace-format-conversion", "kind": "reference", "file": "reference/dotnet-trace.md", "anchor": "4. 格式转换与查看", "title": "trace 格式转换：NetTrace / Speedscope / Chromium", "tags": ["nettrace", "speedscope", "chromium", "format-conversion", "irreversible", "trace-viewer"], "summary": "--format 三种取值及各自的查看器；转换不可逆，原 .nettrace 必须保留——转换产物丢失原始事件细节，无法回推。", "applies_to": [".NET 5+", "Windows", "Linux"]}
```

- [ ] **Step 2: 跑校验确认失败，写骨架，再跑校验确认 PASS**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
```

骨架为文件头 + 四个 `##` 标题（逐字见 Interfaces）。

- [ ] **Step 3: 实施前补核验两项事实**

spec 8.4 列出两项未核验事实，本 Task 的 § 2 依赖其一。执行：

```bash
dotnet-trace list-profiles
```

取实际输出中各 profile 展开后的 provider 与 keyword 组合。**若本机未安装 `dotnet-trace`**，改以 `learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace` 的 profile 小节为准，并在正文标注「以官方文档为准，实际取值可用 `dotnet-trace list-profiles` 核对」——不要凭印象编造 keyword 数值。

- [ ] **Step 4: 填 § 1（四段结构）**

`--buffersize` 一条要以 ` § ` 指回 `reference/eventpipe-and-diagnostic-port.md § 5. 采集开销与缓冲区`，不在本篇重复默认值的两层区分。

`--stopping-event-*` 是本命令相对 `dotnet-counters` 的独有能力：可在特定事件出现时自动停止采集，解决「问题偶发、人守不住」——这与一期 `procdump -p`/`-m` 阈值触发同构，正文应点明这层对应关系。

- [ ] **Step 5: 填 § 2（profile 选择）**

**本节最高优先级内容**（spec 8.1，官方原文已核验）：

- `collect` 下的 `cpu-sampling` **已被移除**，原因是名称误导——它采样所有线程而非仅高 CPU 线程
- 当前 `collect` 默认启用 `dotnet-common` + `dotnet-sampled-thread-time`
- 官方近似等价写法：`--profile dotnet-sampled-thread-time,dotnet-common`
- 精确复刻旧行为：`--profile dotnet-sampled-thread-time --providers "Microsoft-Windows-DotNETRuntime:0x14C14FCCBD:4"`
- **同名陷阱**：`cpu-sampling` 在 `collect-linux` 子命令下**仍然存在**，但语义不同（基于 perf 的内核 CPU 采样，发射为 `Universal.Events/cpu`）

`collect-linux` 的可用性约束一并写明：需 .NET 10+、内核 6.4+、root、glibc 2.27+，且为**预览特性**。

写不到这一节，读者照抄网上旧教程会直接报错——这是本期与现存网络资料偏离最大处。

- [ ] **Step 6: 填 § 3 与 § 4（分两次 Edit）**

- **§ 3**：默认 **exclusive**（仅方法自身耗时），`--inclusive` 切为含被调用方耗时。两者结论可能相反：一个薄封装方法在 inclusive 下排第一、exclusive 下排不进前 20。判据段须说清何时看哪个——找热点代码看 exclusive，找耗时调用路径看 inclusive
- **§ 4**：`--format` 默认 `NetTrace`，可选 `Speedscope` / `Chromium`，各自的查看器。**转换不可逆**，原 `.nettrace` 必须保留

- [ ] **Step 7: 跑三个校验器并提交**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
git add knowledge-base/dotnet-debugging/reference/dotnet-trace.md
git add knowledge-base/dotnet-debugging/index.jsonl
git commit -m "docs(kb): dotnet-debugging 新增 dotnet-trace 篇"
```

---

### Task 4: 活体监控决策查表篇

**Files:**
- Create: `knowledge-base/dotnet-debugging/reference/live-monitoring-decision.md`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（追加 6 行）

**Interfaces:**
- Consumes: Task 1/2/3 的全部 anchor
- Produces: anchor `1. 延迟尖峰`（Task 5 回填决策树时引用）、`2. 内存持续增长`、`3. CPU 打满`、`4. 异常风暴`、`5. 线程池饥饿`、`6. 启动阶段问题`

- [ ] **Step 1: 先追加 6 条索引**

```jsonl
{"id": "dotnet-debugging.ref.live-latency-spike", "kind": "reference", "file": "reference/live-monitoring-decision.md", "anchor": "1. 延迟尖峰", "title": "活体征象：间歇性延迟尖峰的采集方案", "tags": ["latency-spike", "intermittent", "timeline", "gc-pause", "jit", "live-monitoring"], "summary": "延迟尖峰的候选根因（GC 暂停、线程池注入延迟、锁竞争、外部 I/O 抖动、JIT 首次编译）与用 dotnet-counters collect 落盘后对齐时间轴的区分方法——这是单时点 dump 无法回答的问题类别。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/dotnet-counters.md#2. dotnet-counters collect"]}
{"id": "dotnet-debugging.ref.live-memory-growth", "kind": "reference", "file": "reference/live-monitoring-decision.md", "anchor": "2. 内存持续增长", "title": "活体征象：内存增长的趋势判据与转 dump 时机", "tags": ["memory-growth", "leak", "envelope-trend", "allocation-pressure", "live-monitoring"], "summary": "用堆大小包络线区分泄漏与分配压力——包络线上升为泄漏、水平但振幅增大为压力，二者在单时点 dump 中不可区分；确认为泄漏后转 SOS 定位持有者的时机判断。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/dotnet-counters.md#3. 内置计数器与判据对照"]}
{"id": "dotnet-debugging.ref.live-high-cpu", "kind": "reference", "file": "reference/live-monitoring-decision.md", "anchor": "3. CPU 打满", "title": "活体征象：CPU 打满的热点归因路径", "tags": ["high-cpu", "hotspot", "sampling", "gc-pressure", "spin-wait", "live-monitoring"], "summary": "用 dotnet-trace 采样加 report topN 直接读出热点方法，区分业务热点、自旋等待与 GC 压力；相比一期连抓 dump 对比栈，采样给出的是统计分布而非单次快照。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/dotnet-trace.md#3. dotnet-trace report topN"]}
{"id": "dotnet-debugging.ref.live-exception-storm", "kind": "reference", "file": "reference/live-monitoring-decision.md", "anchor": "4. 异常风暴", "title": "活体征象：异常风暴——时间线特有的观测量", "tags": ["exception-storm", "first-chance", "exception-rate", "swallowed-exception", "live-monitoring"], "summary": "异常速率只有时间线能观测，dump 只能看到当前未处理的异常；first-chance 语义下被 catch 的异常同样计入，故判据是相对自身基线的速率陡升而非绝对值。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/dotnet-counters.md#3. 内置计数器与判据对照"]}
{"id": "dotnet-debugging.ref.live-threadpool-starvation", "kind": "reference", "file": "reference/live-monitoring-decision.md", "anchor": "5. 线程池饥饿", "title": "活体征象：线程池饥饿——注入速率只有活体可见", "tags": ["threadpool-starvation", "injection-rate", "queue-length", "hill-climbing", "live-monitoring"], "summary": "队列长度与线程数随时间的联合形态可识别爬坡算法的注入滞后，这一速率信息在 dump 中不存在；与 CPU 打满的区分点是 CPU 利用率不高而队列持续积压。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/dotnet-counters.md#3. 内置计数器与判据对照"]}
{"id": "dotnet-debugging.ref.live-startup-issue", "kind": "reference", "file": "reference/live-monitoring-decision.md", "anchor": "6. 启动阶段问题", "title": "活体征象：启动阶段采集——dump 完全做不到的能力", "tags": ["startup", "diagnostic-port", "suspend-on-start", "jit-warmup", "assembly-loading", "live-monitoring"], "summary": "用 -- <command> 或 --diagnostic-port 反向连接可在进程启动前建立采集会话，覆盖 JIT 预热与程序集加载阶段；dump 在此场景下不可用，因为问题发生时进程尚未存在或已退出。", "applies_to": [".NET 5+", "Windows", "Linux"], "source": ["reference/eventpipe-and-diagnostic-port.md#2. 诊断端口与连接建立"]}
```

- [ ] **Step 2: 跑校验确认失败，写骨架，再跑校验确认 PASS**

骨架为文件头 + 六个 `##` 标题。**文件头必须含运行时边界声明**（spec 7.3——读者按征象查表时须第一时间知道自己的运行时是否适用，而不是读到命令处才发现用不了）：

```markdown
# 活体监控决策查表

> **运行时要求**：本篇全部方案基于 EventPipe，要求目标应用运行 **.NET 5 或更高**版本。**.NET Framework 4.x 不适用**——该运行时请走 `reference/debugging-decision-tree.md` 的 dump 路径。

按征象查「该采什么」。定位方向后转 SOS 命令定位根因——`reference/debugging-decision-tree.md` 回答「该抓哪种 dump」，本篇回答「该采什么时间线数据」，两篇互补而非替代。
```

- [ ] **Step 3: 逐节填写（六节分至少三次 Edit）**

每节沿用一期决策树的三段结构：`### 候选根因` / `### 采集方案与判据` / `### 常见误判`。

各节要点：

| 节 | 候选根因 | 采集方案 | 与一期的关系 |
|---|---|---|---|
| 1. 延迟尖峰 | GC 暂停、线程池注入延迟、锁竞争、外部 I/O 抖动、JIT 首次编译 | `dotnet-counters collect` 落盘后与业务日志时间轴对齐 | **回填**一期 § 5 的空洞 |
| 2. 内存持续增长 | 托管泄漏、分配压力、非托管增长 | 计数器看包络线趋势 → 确认泄漏后转 SOS | 与一期同名征象互补 |
| 3. CPU 打满 | 业务热点、自旋等待、GC 压力 | `dotnet-trace` 采样 + `report topN` | 一期是连抓 dump 对比栈 |
| 4. 异常风暴 | 吞异常的重试循环、依赖不可用、参数校验失败风暴 | 异常速率计数器 | 一期无对应节 |
| 5. 线程池饥饿 | 同步阻塞异步、长任务占用工作线程 | 队列长度与线程数的联合形态 | 一期在「进程挂起」下作候选根因之一 |
| 6. 启动阶段问题 | JIT 预热、程序集加载、静态构造函数 | `-- <command>` 启动即采、`--diagnostic-port` 反向连接 | **一期完全没有的能力** |

**每节的「采集方案与判据」段必须写明两件事**：

1. 该判据**为什么必须用时间线工具而非 dump**（spec 4.3——这是本期的存在理由）。例：包络线上升 vs 振幅增大这两种形态，在单时点 dump 中都只表现为「堆里有 N 个对象」，无法得知 N 处于回落前还是回落后
2. 「区分点」后的下一步动作，以 ` § ` 指向一期具体 SOS 命令

`## 6. 启动阶段问题` 单独说明：dump 在此场景下**不可用**，因为问题发生时进程尚未存在（启动前）或已退出（启动失败）。这是本期唯一一个一期完全无法覆盖的征象。

- [ ] **Step 4: 跑三个校验器**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
```

本 Task 是全期 ` § ` 引用最密集处（每节至少 2 条），`check_refs.py` 必须 PASS。

- [ ] **Step 5: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/live-monitoring-decision.md
git add knowledge-base/dotnet-debugging/index.jsonl
git commit -m "docs(kb): dotnet-debugging 新增活体监控决策查表篇"
```

---

### Task 5: 回填一期三处欠条

**Files:**
- Modify: `knowledge-base/dotnet-debugging/reference/debugging-decision-tree.md:78-92`
- Modify: `knowledge-base/dotnet-debugging/reference/dump-types-and-capability.md:36`
- Modify: `knowledge-base/dotnet-debugging/reference/dump-capture.md:64`
- Modify: `knowledge-base/dotnet-debugging/index.jsonl`（改 1 条，不增不删）

**Interfaces:**
- Consumes: Task 4 的 anchor `1. 延迟尖峰`；Task 2/3 的文件路径

**本 Task 的硬约束：不得删除任何既有做法。** 一期的连抓 dump 路径在 .NET Framework 4.x 下仍是唯一可用手段（spec 6.3），删除会让 Framework 读者失去出路。全部改动都是**追加分支**，不是替换。

- [ ] **Step 1: 重写 `debugging-decision-tree.md § 5. 间歇性抖动`**

现状（第 80–89 行）：`### 候选根因` 段写「不适用——本节不给出候选根因列表，见下方局限说明。」，正文以「完整的时间线采样方案……留待后续期次收录。」结尾。

三处改动：

1. `### 候选根因` 段的「不适用」整句替换为实际列表：GC 暂停、线程池注入延迟、锁竞争、外部 I/O 抖动、JIT 首次编译。**注意后半句「见下方局限说明」也要一并去掉**——局限已不再是本节结论
2. 第 89 行「完整的时间线采样方案（持续指标采集、火焰图、按时间轴定位延迟尖峰对应的调用）留待后续期次收录。」替换为指向 `reference/live-monitoring-decision.md § 1. 延迟尖峰` 的可操作路径，并说明适用运行时为 .NET 5+
3. **保留**第 87 行整段连抓 dump 的近似手段，但在其后补一句适用条件：目标为 .NET 5+ 且可安装诊断工具时应优先走时间线路径；.NET Framework 4.x 或无法安装工具的环境，本段仍是唯一可用手段

小节标题 `### 取证命令与判据：当前范围内的已知局限与近似替代` **可以改**（它不是任何索引条目的 anchor——索引 anchor 为 `5. 间歇性抖动`），建议改为 `### 取证命令与判据`，因为「当前范围内的已知局限」已不成立。改前用 `check_refs.py` 确认无其他文件以 ` § ` 引用该子标题。

- [ ] **Step 2: 更新该征象的索引条目**

`dotnet-debugging.ref.symptom-intermittent` 的 `id`、`anchor`、`file` **不动**（改动会破坏既有引用），只改 `title`、`summary`、`tags`：

```jsonl
{"id": "dotnet-debugging.ref.symptom-intermittent", "kind": "reference", "file": "reference/debugging-decision-tree.md", "anchor": "5. 间歇性抖动", "title": "征象：间歇性抖动的取证路径", "tags": ["intermittent", "latency-spike", "timeline", "sampling", "symptom", "triage"], "summary": "间歇性延迟抖动需要时间线采样而非单时点快照；.NET 5+ 走 live-monitoring-decision 的活体采集路径，.NET Framework 4.x 仍只能用连抓多个 dump 对比的近似手段。", "applies_to": [".NET Framework 4.x", ".NET 6+"]}
```

`applies_to` **保持不变**——该条目讲的是征象本身，两种运行时都会遇到；不含 Framework 的约束只适用于本期新增的活体条目。

- [ ] **Step 3: 改 `dump-types-and-capability.md` 第 36 行**

现状：「一期知识库不含专门的时间线采样工具链（如 `dotnet-trace` 的计数器持续采集），仅在 `reference/dump-capture.md § 1. procdump（Windows，全运行时）` 中以连续抓取多份 dump 作为一期内可行的替代手段；完整的时间线分析方法留待二期路标。」

改为指向 `reference/dotnet-counters.md` 与 `reference/dotnet-trace.md`，说明该能力仅覆盖 .NET 5+，并保留连抓 dump 作为 Framework 与受限环境的替代手段。**保留原句中 `§ 1. procdump（Windows，全运行时）` 的完整括号后缀**——那是实际标题文本，截短会让 `check_refs.py` 失配。

- [ ] **Step 4: 改 `dump-capture.md` 第 64 行判据段**

现状开头：「`-n 3` 连抓多个 dump 后对比各自的 `!dumpheap -stat` 输出，是**在没有时间线采样工具时**判断"哪类对象在涨"的替代手段——这是一期能给出的最接近趋势分析的做法」

改动**只补一句，不删原文**：把「这是一期能给出的最接近趋势分析的做法」之后接上——目标为 .NET 5+ 且可安装诊断工具时，应优先用 `reference/dotnet-counters.md § 2. dotnet-counters collect` 采集时间线，连抓 dump 退化为受限环境下的备选。

- [ ] **Step 5: 验收——全库检索残留措辞**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
```

```powershell
Select-String -Path knowledge-base\dotnet-debugging\**\*.md -Pattern '留待后续期次|二期路标|一期知识库不含|一期能给出|没有时间线采样工具'
```

预期：**只剩 `CHANGELOG.md:19` 一处**（`AssemblyLoadContext`，一期已登记的已知缺口，不属本期范围）。若 `dump-capture.md` 的「一期能给出」仍在，属正常——该句被保留在补充句之前；但须确认其后确实接上了新路径，否则读者读到该句就停了。

- [ ] **Step 6: 提交**

```bash
git add knowledge-base/dotnet-debugging/reference/debugging-decision-tree.md
git add knowledge-base/dotnet-debugging/reference/dump-types-and-capability.md
git add knowledge-base/dotnet-debugging/reference/dump-capture.md
git add knowledge-base/dotnet-debugging/index.jsonl
git commit -m "docs(kb): dotnet-debugging 回填一期三处时间线工具链欠条"
```

---

### Task 6: 版本、元数据与终检

**Files:**
- Modify: `knowledge-base/dotnet-debugging/README.md:3`（版本行）、文件地图与阅读路径两节
- Modify: `knowledge-base/dotnet-debugging/CHANGELOG.md`（顶部插入 1.1.0）
- Modify: `knowledge-base/catalog.json:121`（`notes` 字段）
- Modify: `docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md:243-257`（分期路标表）

**Interfaces:**
- Consumes: Task 1–5 的全部产出

- [ ] **Step 1: 改领域 README 三处**

1. 第 3 行 `> 版本：1.0.1` → `> 版本：1.1.0`
2. 「阅读路径」表**追加两行**（放在 `rules/01-dump-handling.md` 行之前，保持「先诊断后合规」的既有顺序）：

```markdown
| 间歇性问题 / 需要时间线数据 | `reference/live-monitoring-decision.md` |
| 采集机制与基线概念 | `reference/eventpipe-and-diagnostic-port.md` |
```

3. 「文件地图」表**追加四行**（放在 `debugging-decision-tree.md` 行之后、`rules/` 行之前）：

```markdown
| `reference/eventpipe-and-diagnostic-port.md` | EventPipe 与 ETW 的能力边界、诊断端口、Provider 三级过滤、两套计数器体系、缓冲区、基线采集 |
| `reference/dotnet-counters.md` | dotnet-counters monitor / collect 的开关与输出，内置计数器双版本命名与形态判据对照 |
| `reference/dotnet-trace.md` | dotnet-trace collect / profile 选择 / report topN / 格式转换，含 cpu-sampling 移除的迁移写法 |
| `reference/live-monitoring-decision.md` | 六类征象（延迟尖峰 / 内存增长 / CPU 打满 / 异常风暴 / 线程池饥饿 / 启动阶段）→ 采集方案查表 |
```

改完文件地图应为 **13 行**（一期 9 + 本期 4）。

- [ ] **Step 2: 加 CHANGELOG 1.1.0 条目**

插在 `## [1.0.1] - 2026-09-05` **之上**（本仓库 CHANGELOG 为倒序）：

```markdown
## [1.1.0] - 2026-09-05

### Added
- 新增 4 篇 reference：EventPipe 与诊断端口机制、dotnet-counters、dotnet-trace、活体监控决策查表，索引新增 22 条（42 → 64）
- 判据新增「基线形态 / 异常形态 / 区分点」三元组范式，用于时间序列数据——一期的单时点布尔判据不适用于趋势判读
- 内置计数器给出 .NET 9+ Meter 与 .NET 8- EventCounter 双版本命名对照

### Changed
- `debugging-decision-tree.md § 5. 间歇性抖动`：候选根因由「不适用」补齐为实际列表，结论由「留待后续期次」改为指向活体采集路径；连抓 dump 的做法保留为 .NET Framework 4.x 与受限环境下的可用手段
- `dump-types-and-capability.md § 3`、`dump-capture.md § 1` 判据段：时间线能力的说明由「一期不含」改为指向新篇
```

**不要写 `### Removed`**——本期无删除，这正是定为 Minor 而非 Major 的依据（spec 1.3）。

- [ ] **Step 3: 改 `catalog.json` 的 notes**

现状末句：「一期不含活体监控工具（PerfView/ETW/dotnet-counters）与 WPF 专属归因」。

改为：「含活体监控工具链（EventPipe / dotnet-counters / dotnet-trace，仅 .NET 5+）；暂不含 PerfView/ETW 与 WPF 专属归因」。

只改这一句，`domain` / `categories` / `consumers` 等字段不动（`consumers` 仍为空——本期无 skill 消费者）。改后确认 JSON 仍可解析：

```bash
python -c "import json;json.load(open('knowledge-base/catalog.json',encoding='utf-8'));print('OK')"
```

- [ ] **Step 4: 改一期 spec 的分期路标表**

`docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md` 第 243–257 行。改动：

1. 路标表中「二期 = WPF 桌面 dump 归因」与「三期 = 活体诊断与工具链分叉」**互换期次编号**
2. 活体诊断行的范围收窄为本期实际交付：`dotnet-counters` / `dotnet-trace` / EventPipe 机制；`dotnet-gcdump`、PerfView / ETW / WPR、三运行时工具选择矩阵**移出**，标注为后续期次
3. 第 257 行「卡顿归因随活体诊断进三期，那里才有帧时间线数据」中的「三期」改为「二期」，并相应调整「二期因此完全建立在一期已交付的 SOS 命令之上」一句的期次称谓
4. 表下补一句变更说明：期次顺序于 2026-09-05 调换，理由见 `docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-phase2-design.md § 1.2`

**保留**第 259 行「后续期次在本 spec 只登记路标与范围，不写实现细节」——它正是本次调整的授权依据。

- [ ] **Step 5: 全量终检**

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging --audit
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py"
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py"
```

逐条核对 spec 第 9 节的完成判定：

| 检查项 | 预期 |
|---|---|
| 全局记录数 | **566**（= 544 + 22，含最终审查拆出的 `trace-collect-linux`） |
| 领域记录数 | **64**（reference **59**、rule **5**） |
| `--audit` 孤儿文件 | 无 |
| `check_refs.py` | PASS |
| `find_duplicates.py` | 本期条目与 `csharp.11.*` 相似度 < 0.5 |
| 本期新增条目的 `applies_to` | 均不含 `.NET Framework 4.x`（`trace-collect-linux` 为 `[".NET 10+", "Linux"]`） |
| README 文件地图 | 13 行 |
| 版本一致性 | README `1.1.0` == CHANGELOG 最新条目 |
| 残留措辞 | 「留待后续期次」类仅剩 CHANGELOG 中 `AssemblyLoadContext` 一处 |

`applies_to` 这一条单独验：

```powershell
Get-Content knowledge-base/dotnet-debugging/index.jsonl | Select-String 'eventpipe|diagnostic-port|provider-keyword|eventcounter-vs-meter|baseline-capture|counters-|trace-|live-' | Select-String 'NET Framework'
```

预期：**无输出**。有输出说明某条误标了 Framework（spec 7.2 指出这是一期已发生过的错误，commit `c8603f8`）。

若 `find_duplicates.py` 报本期条目与 `csharp.11.*` 相似度 ≥ 0.5，说明判据被写成了埋点规范的复述——须改写为「从外部读取运行时已内置的计数器」视角，而非「应用该埋什么指标」。

- [ ] **Step 6: 提交并推送**

```bash
git add knowledge-base/dotnet-debugging/README.md
git add knowledge-base/dotnet-debugging/CHANGELOG.md
git add knowledge-base/catalog.json
git add docs/superpowers/specs/2026-09-05-dotnet-debugging-kb-design.md
git commit -m "docs(kb): dotnet-debugging 升版 1.1.0，更新文件地图、catalog 与分期路标"
```

推送走 `commit-cc-plugin` skill（本仓库禁止手动推送）。**不升 `.claude-plugin/marketplace.json`**——本期未动 `plugins/` 与 `.claude/`。

---

## 自查记录

写完后对照 spec 逐节核查的结果：

| spec 节 | 落位 |
|---|---|
| 1. 背景与期次顺序变更 | Task 5（回填）+ Task 6 Step 4（路标） |
| 2. 范围 | File Structure（4 篇）；排除项体现为「不在本期范围」，无对应 Task |
| 3. 篇目结构与接口契约 | Task 1–4 的 Interfaces 段逐字锁定全部 anchor |
| 4. 判据范式：时间线三元组 | Global Constraints（标题固定、禁绝对阈值、须接回一期）+ Task 2 Step 5 / Task 4 Step 3 |
| 5. 版本分叉 | Task 2 Step 5 双列对照表 |
| 6. 回填一期三处 | Task 5 Step 1/3/4，逐处给出现状原文与改法 |
| 7. 能力边界与 applies_to | Global Constraints 取值表 + Task 4 Step 2 文件头 + Task 6 Step 5 验证命令 |
| 8. 事实核验记录 | 8.1 → Task 3 Step 5；8.2 → Task 1 Step 7；8.3 → Task 1 Step 7；8.5 → Task 2 Step 5；8.6/8.7 → Task 1 Step 5/7；**8.4 未核验项 → Task 3 Step 3 显式安排补核验** |
| 9. 完成判定 | Task 6 Step 5 逐条对应，「约 57」已定死为 59 |
| 10. 不在本期范围 | 无 Task（有意不做） |

三处与 spec 的偏差，均为写计划时收紧：

1. spec 说「约 20 条索引」，本计划定死 **21 条**并逐条给出完整 JSON
2. spec § 3.2 把 `dotnet-counters.md § 3` 当作一条，本计划拆为 **2 条索引**（GC 与内存 / 线程池与锁异常）——该节承载 14 个计数器，单条 summary 无法覆盖，检索命中后仍需人工翻找
3. spec § 3.3 把 `profile 选择` 当作一条，本计划拆为 **2 条**——`cpu-sampling` 移除是最高频踩坑点，须能被独立检索命中

