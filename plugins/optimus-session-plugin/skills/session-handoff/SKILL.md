---
name: session-handoff
description: 跨会话交接工作时使用。会话结束前保存交接物（进度与待办、关键决策、习得与踩坑三层），或新会话开始时恢复上次进度。触发场景：用户说"交接"、"保存进度"、"handoff"、"要下班了"、"继续上次的工作"、"接着干"、"上次做到哪了"、"恢复进度"。
metadata:
  version: "1.0.1"
  author: optimus
  category: workflow
compatibility: 需要 Git 仓库环境，以及 POSIX shell（Windows 下即 Git Bash，随 Git 一起安装）；无 MCP 或第三方 CLI 依赖。
allowed-tools: Bash Read Write Edit Glob Grep
---

# 跨会话交接

每个新会话对之前发生的一切一无所知。context 压缩能延续单次会话，但换一天、换一台机器、换 harness，上下文一律归零。本 skill 把「任务当前进行到哪一步」落成文件，让下一个会话读完就能接着干。

## 三层交接物

| 层 | 回答什么 | 恢复时 | 完整模板 |
|---|---|---|---|
| `progress.md` | 做了什么 + 接下来做什么（含待办队列） | **必读** | `references/progress-template.md` |
| `insights.md` | 已核验的事实 / 踩坑 / 习得 | **必读** | `references/insights-template.md` |
| `summaries.md` | 为什么这么选（决策、权衡、风险、假设） | **按需**——仅当要改动上轮决定时 | `references/summaries-template.md` |

每份模板自带该层的追加/覆写语义与是否创建的判据。**后两层允许不创建**——纯执行性会话（照既定计划做完、无决策无踩坑）只产 `progress.md` 是正常的，强制凑齐会让后两层充满空洞内容，降低下轮信噪比。

## 核心约束

> **不重复其他产物已记录的内容。** 代码改动看 `git diff`、变更历史看 CHANGELOG、已知缺陷看 known-issues、跨会话恒真事实看 memory。交接物只写这些地方**没有**的东西。

这是本 skill 最容易失守的地方——把 `git log` 抄一遍很容易且看起来充实，但对下一个会话零价值，它自己会跑 `git log`。唯一的 carve-out 是**纯执行性会话**：无自主决策时「已完成」允许指向计划文档的任务编号，见第 3 步。

## 模式判定与前置校验（HARD GATE）

被触发后先判定模式，**按用户意图判定，不按文件系统状态**——目录已存在但用户这次要保存新一轮时，用「目录是否存在」判定会误判为恢复：

| 用户意图 | 模式 |
|---|---|
| "交接"、"保存进度"、"handoff"、"要下班了" | **保存** |
| "继续上次的"、"接着干"、"上次做到哪了"、"恢复进度" | **恢复** |
| 无法判定 | 询问，二选一 |

两种模式都先过这四项校验：

| # | 检查 | 不通过时 |
|---|---|---|
| 1 | `git rev-parse --is-inside-work-tree` | 🔴 **STOP**，提示"请在 Git 仓库中使用本 skill" |
| 2 | `git rev-parse --abbrev-ref HEAD` | 返回 `HEAD` 说明处于 detached HEAD，🔴 **STOP**；命令**报错**说明是无提交的空仓库，此时用 `git branch --show-current` 取分支名继续，不终止 |
| 3 | 读对应层的 `references/*-template.md` | 找不到则用本文件的三层结构降级执行，**不终止**。仅保存模式需要 |
| 4 | `git status --short` | **不阻断**，但有未提交改动时须记入 `progress.md` 的「工作区状态」段——下个会话会看到一个脏工作区，需要知道那些改动是什么、为什么没提交。仅保存模式需要 |

## 交接物路径（每次运行实测，不缓存）

**一次跑完，把结果记在心里**——shell 变量不跨工具调用存活，后续步骤要用具体值而非 `$DEFAULT`：

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1     # 锚定仓库根，务必第一条
BRANCH=$(git rev-parse --abbrev-ref HEAD)
DEFAULT=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
[ -z "$DEFAULT" ] && DEFAULT=$(git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p')
DEFAULT=${DEFAULT:-$BRANCH}                          # 仍为空则视当前分支为默认
AUTHORS=$(git log --format=%an 2>/dev/null | sort -u | wc -l)
WHO=$(git config user.name | tr ' /' '--')           # 空格与斜杠净化，否则路径会裂
SLUG_BRANCH=$(echo "$BRANCH" | tr '/' '-')           # feat/coupon → feat-coupon
echo "BRANCH=$BRANCH DEFAULT=$DEFAULT AUTHORS=$AUTHORS WHO=$WHO SLUG_BRANCH=$SLUG_BRANCH"
```

🔴 **第 1 行不可省**。`--is-inside-work-tree` 在仓库的**任意子目录**都返回 true，不锚定根目录就会在 `plugins/foo/` 下建出一个平行的 `docs/sessions/`——写入成功、零报错，但恢复时永远找不到。

⚠️ **末行 echo 出的五个值后续都要用**：`SLUG_BRANCH` 与 `DEFAULT` 比较决定是否加分支段、`AUTHORS` 决定是否加 `.WHO` 后缀、`DEFAULT` 用于采集未推送提交。**在后续命令里写它们的字面值**，不要写 `$DEFAULT`——变量不跨工具调用存活，展开成空串后 `git log "origin/${DEFAULT}..HEAD"` 会变成 `origin/..HEAD` 并报错。

⚠️ **`git symbolic-ref` 那行常常取不到值，下一行的 fallback 是必要的**。`refs/remotes/origin/HEAD` 只有 `git clone` 会自动创建，`git init` + `git remote add` 建起来的仓库里根本不存在。缺 fallback 会让这类仓库**永远走单层路径**——即使在特性分支上交接也不分目录。`git remote show origin` 走网络，慢但准；两条都失败（离线、无 remote）才退到「当前分支即默认」。

推导规则 `docs/sessions/[<SLUG_BRANCH>/]<YYYY-MM-DD>-<slug>/<层>[.<WHO>].md`。两个可选段**各自独立**判定：

| 条件 | 路径 |
|---|---|
| `BRANCH`=`DEFAULT` 且 `AUTHORS`=1 | `docs/sessions/2026-09-10-handoff-impl/progress.md` |
| `BRANCH`≠`DEFAULT` 且 `AUTHORS`=1 | `docs/sessions/feat-coupon/2026-09-10-api-contract/progress.md` |
| `BRANCH`=`DEFAULT` 且 `AUTHORS`>1 | `docs/sessions/2026-09-10-api-contract/progress.anyu.md` |
| `BRANCH`≠`DEFAULT` 且 `AUTHORS`>1 | `docs/sessions/feat-coupon/2026-09-10-api-contract/progress.anyu.md` |

🔴 **分支段与用户段都用净化后的值**（`SLUG_BRANCH` / `WHO`）。`feat/coupon` 直接拼进路径会多出一层目录，落到 `docs/sessions/feat/coupon/...`——比恢复用的 glob 深一层，**写得进、读不出**。同理 `user.name` 常含空格（`Zhang San`）。

⚠️ **禁止硬编码 `master` / `main`**——两者在真实项目中都常见，写死会给另一半用户凭空多一层目录，或让多人仓库的交接物互相覆盖。**变量名避开 `USER`**——它是 shell 环境变量，覆盖有副作用。`AUTHORS` 数的是全部历史的作者，老仓库里离职多年的贡献者也计入，单人维护的仓库照样展开用户段——这是有意为之，宁可多个后缀也好过两人同时交接时互相覆盖。

**slug 取任务主题**，kebab-case，3-5 个词；不是日期的重复、不是 `session-1` 这类序号。**一任务一目录**——同一分支可有多个不相干任务，混进一个目录会让恢复时无法区分。

## 模式 A — 保存

### 第 1 步 · 定位目录（🔴 不可跳过）

**先查这个任务是否已有交接目录，再决定新建还是追加。**

```bash
ls -dt docs/sessions/*/ docs/sessions/*/*/ 2>/dev/null | grep -E '/[0-9]{4}-[0-9]{2}-[0-9]{2}-' | head -10
```
对照列出的目录名判断，**看的是做的是不是同一件事，不是 slug 字面像不像**（上轮叫 `coupon-api`、这轮在做同一个优惠券接口，就是同一任务）。目录名不足以判断时，**读候选目录 `progress.md` 的待办队列**——本轮做的事若正好是它列出的某一项，匹配就是确定的，这比目录名可靠：

| 情况 | 处理 |
|---|---|
| 有目录指向**同一任务** | 用它，走追加。**目录名不改**（含其中的旧日期——那记的是任务起始日，不是本轮日期） |
| 同一天但任务不同 / 无匹配 | 新建目录 |
| 读过待办队列仍拿不准 | 🔴 **STOP，问用户**。二选一：追加到 `<目录名>`，还是新建 |

🔴 **跳过这一步的代价是静默的**：同一任务凭记忆推 slug，第二次很可能推出个近义词（`handoff-impl` vs `session-handoff-impl`），于是任务裂成两个目录——两边各有半份待办队列，且不会有任何报错。**恢复时只会读到其中一个。**

### 第 2 步 · 采集（只读，不猜测）

```bash
git log --oneline -10          # 本次会话的落盘结果
git status --short             # 未完成的工作区状态
git log "origin/master..HEAD" --oneline   # 未推送的提交
```

⚠️ **末条里的 `master` 换成上一节 echo 出的 `DEFAULT` 实际值**，不要写 `$DEFAULT`——变量不跨工具调用存活，展开成空串后命令变为 `origin/..HEAD` 并报错。该分支不存在（无 remote）时此条会 fatal，跳过即可，不影响交接。

### 第 3 步 · 写入

**第 1 步判定为追加**（目录已存在）→ 先读现有 `progress.md`，再按下表分段处理（**完整规则与示意图在 `references/progress-template.md` 的「本层的追加与覆写语义」一节**，第一次遇到追加场景时去读它）：

| 内容 | 语义 |
|---|---|
| `## 会话 N` 块 | **插入到「🔧 工作区状态」前的 `---` 分隔线之前**，不是 append 到文件末尾（末尾是待办队列）。N = 已有最大编号 + 1；**不按日期推算**，同一天可能交接两次 |
| 🔧 工作区状态 | **整段覆写**——它描述当前工作区，旧快照即刻失效。**本轮 `git status` 干净则整段删除**，不留旧快照 |
| 📋 待办队列 | **整段覆写**，但**先读旧队列，未完成项要带进新队列** |
| 引用 | 覆写，与旧清单**去重合并**（不是丢弃旧的）。本轮无新增则保留旧清单原样 |
| frontmatter 的 `date` / `status` | 覆写为本轮值。`status` 仅在待办队列**清空**时才写 `已完成` |

⚠️ **`?? docs/sessions/` 自身不算工作区状态**——交接物目录是本 skill 的产物，把它记进去是自指的噪声。只记与任务相关的改动。

上轮的 ⏸️ 阻塞项在本轮**阻塞条件已解除**时：条件解除且本轮已做完 → 移入「已完成」并注明原阻塞已解除；条件解除但还没做 → 改标 🔴/🟡 留在队列。**不要原样留着 ⏸️**——下轮会以为还卡着。

`summaries.md` / `insights.md` 在追加模式下**只追加会话块**，frontmatter 的 `date` 同样覆写为本轮值，无其他覆写段。**本轮无内容则该文件保持原样不动**（连 `date` 也不动），不要因为它已存在就硬凑一个空会话块；反过来，上轮没建、本轮有内容则新建，**会话号与 `progress.md` 对齐**——即使是该文件的第一个会话块，编号也可能从 3 起，跳号本身说明了前两轮该层无产出。

**第 1 步判定为新建** → `mkdir -p` 后按模板创建，会话号从 1 起。三层各自判断是否创建：`progress.md` **总是**创建（必填三段写不出来说明本次无可交接内容，此时告知用户无需交接）；`summaries.md` / `insights.md` 在**至少一个维度有内容**时创建。

⚠️ **纯执行性会话的「已完成」允许指向计划文档的任务编号**（`plan 任务 1 完成`）+ 补计划里没有的实际差异。这不违反「不重复其他产物」——差异恰恰是计划里没有的。但不要因此把这一段写空。

### 第 4 步 · 待办队列写入检查清单

写待办前**逐项**核对，命中即入列——这把「有没有漏记待办」从凭感觉变成可核对：

| # | 检查 | 命中则 |
|---|---|---|
| 1 | 多步任务未做完？ | 剩余步骤入列 |
| 2 | 有分流的中/低优先级未执行？ | 入列 |
| 3 | 用户说"先不做"的？ | 入列 + **注明原因**（不写，下轮会重新提议一次） |
| 4 | 分析出问题但只修了部分？ | 未修的入列 |
| 5 | 本轮识别出可执行的遗留风险？ | 入列。**不依赖 `summaries.md` 是否存在**，纯执行会话同样要过 |
| 6 | 依赖外部未就绪？ | ⏸️ 入列 + **阻塞原因**（不写，下轮要重新排查才知道卡在哪） |
| 7 | 代码审查发现问题但未修？ | 入列 |

四档优先级：🔴 必须优先 / 🟡 应尽快 / 🔵 有空再做 / ⏸️ 阻塞。**⏸️ 与 🔴 的区别是能不能做，不是重不重要**——很重要但自己做不了的是 ⏸️。⚠️ 这里的 🔴 是**写进产物的优先级标记**，与本文件里表示「停下问用户」的 🔴 STOP 是两回事。

### 第 5 步 · 收尾输出

报告实际产出的文件，并附入库提示：

```
交接物已写入 docs/sessions/2026-09-11-coupon-api/：progress.md、insights.md
如不希望它进入版本库，可将 docs/sessions/ 加入 .gitignore。
```

⚠️ **列本次实际写了哪几个文件**（裸文件名，不带路径），不要固定写数量——那会与「后两层可不创建」冲突。**不自动提交**：是否入库、何时入库、用什么 message 由用户决定，很多仓库有专属提交流程或 message 规范，代为提交等于替用户做了一个未授权的决定。

## 模式 B — 恢复

### 第 1 步 · 定位

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
ls -dt docs/sessions/*/ docs/sessions/*/*/ 2>/dev/null | grep -E '/[0-9]{4}-[0-9]{2}-[0-9]{2}-' | head -5
```

`grep` 滤掉分支层目录——`docs/sessions/*/` 这个 glob 同时会命中 `docs/sessions/feat-coupon/` 这类中间层，不滤会让「多于一个」被永久误触发，用户还可能选中一个不含 md 的空壳。

| 结果 | 处理 |
|---|---|
| 恰好一个 | 直接读 |
| 多于一个 | 🔴 **STOP，让用户选**——同一天可能有多个不相干任务，猜错会让整个会话跑偏 |
| 零个 | 告知「未找到交接物」并列出实际查过的路径，**不要凭空开工**。可能是交接时写在了别的仓库/子目录 |

⚠️ **多人仓库里文件名带 `.<user>` 后缀**（`progress.anyu.md`）。目录里若有多个用户的同层文件，默认读**自己**的（`git config user.name` 净化后的值）；要接手他人的进度，须由用户明说。

### 第 2 步 · 分层读取

按序：① `progress.md`（必读）② `insights.md`（必读——已核验的事实避免重做、踩坑避免重踩）③ `summaries.md`（按需）④ `progress.md`「引用」段列出的路径 ⑤ `git log --oneline -10` 对照交接物写入后是否有新提交。

⑤ 发现有新提交 → 交接物已过时，**须提示用户**。

⚠️ **`summaries.md` 按需读是分层的意义所在**——每次都读全三层的话，拆分只是多了两次读取而无收益。判据：本次是「继续推进」（不读）还是「改动上轮的决定」（读）。

### 第 3 步 · 复述后停下（🔴 CHECKPOINT）

复述三件事——① 上次进行到哪一步 ② 下一步待办（按优先级）③ 有无阻塞项及其原因——然后 🔴 **STOP，等用户指令**。

⚠️ **不要读完就自动开工**。交接物里的"下一步"是上个会话的判断，两个会话之间可能需求变了、优先级调了、别人已经做了。自动开工省下一轮确认，代价是可能做完才发现不该做。

## Red Flags

| 错误做法 | 正确做法 |
|---|---|
| 在下一次工具调用里引用 `$DEFAULT` / `$WHO` 等变量 | shell 变量不跨调用存活。抄 echo 出来的**实际值**进命令 |
| 不 `cd` 到仓库根就开写 | 会在子目录建出平行的 `docs/sessions/`，写入成功但恢复找不到 |
| 分支名 / 用户名直接拼进路径 | `feat/coupon` 会多出一层目录，`Zhang San` 的空格会裂开路径。先 `tr` 净化 |
| 保存时凭记忆推 slug，不查已有目录 | 先 `ls -dt` 看有没有同一任务的目录。凭空推 slug 会让任务裂成两个目录，且**不报错** |
| 追加时把待办队列另起一段、保留旧队列 | 整段覆写，但**先读旧队列带上未完成项** |
| 「已完成」写成"做了一些工作" | 具体到文件名和功能点："给 check_plugin_versions.py 补了 symlink mode 的 12 个用例" |
| 把 `git log` 内容抄进「已完成」 | 下个会话自己会跑 `git log`。写 git 里看不到的：为什么这么改、试过什么没成 |
| 「待办」写成"继续完善 XXX" | 具体到可执行的动作："给 check_plugin_versions.py 补 symlink mode 的测试用例" |
| 空维度写"（无）"占位、或为凑齐三层而创建空洞的 `summaries` / `insights` | 空维度整段删除，该层全空则整个文件不创建。占位符比缺失更糟（下轮要花时间确认是真没有还是忘了写），**文件数量不是完整性的证据** |
| 把框架特性、API 行为写进 `summaries` | 那是长期有效的知识，该进知识库。写进交接物会随任务结束变成历史——归属错了等于丢了 |
| 上下文告急时还在写代码，留下半成品 | 主动**提议**交接（提议，不自动执行——保存须由用户显式触发） |
