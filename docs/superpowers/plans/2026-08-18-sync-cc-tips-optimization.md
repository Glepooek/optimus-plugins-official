# sync-cc-tips 优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 `.claude/skills/sync-cc-tips/SKILL.md`，解决抓取效率、判重脆弱、窗口固定无锚点、差异不可审计、摘要不完整、CHECKPOINT 依赖自由文本、硬编码分类计数共 7 类问题。

**Architecture:** SKILL.md 是纯 prompt 指令文件（非可执行代码），本计划的"实现"是精确编辑该文件的对应章节；每个任务同时会在真实仓库文件（`tips.txt`、`CHANGELOG.md`）上实际跑一遍新引入的 bash 命令（awk 截断、grep 提取），验证命令本身语法正确且输出符合预期——这是这类 prompt-only 改动能做到的最接近"运行测试"的验证方式。新增 `.last-synced-version` 纯文本状态文件持久化同步锚点。

**Tech Stack:** Bash（awk/grep）、Markdown frontmatter (YAML，用 Python `yaml.safe_load` 校验)

**Spec:** `docs/superpowers/specs/2026-08-18-sync-cc-tips-optimization-design.md`

## Global Constraints

- `.last-synced-version` 仅存一行版本号（纯数字点号格式，如 `2.1.234`，不带 `v` 前缀，不带换行以外的其他字符）
- SKILL.md 的 `metadata.version` 本次改动为 Minor 升级（新增锚点机制、中间过程表等功能性内容），当前 `1.1.4` → `1.2.0`
- 每次修改 SKILL.md 后必须同步更新同目录 `CHANGELOG.md`（遵循 `.claude/rules/skill-authoring.md` 规范）
- `.claude/skills/` 下的改动不触发 `.claude-plugin/marketplace.json` 版本升级
- 所有新增的 bash 命令片段必须在真实仓库文件上实际跑通一次，不能只是理论正确
- 三处 CHECKPOINT 全部改用 `AskUserQuestion`，不得保留 y/yes/n/no 自由文本确认

---

## 文件结构

| 文件 | 操作 | 职责 |
|---|---|---|
| `.claude/skills/sync-cc-tips/.last-synced-version` | 新增 | 持久化"上次同步到的版本号"，纯文本单行 |
| `.claude/skills/sync-cc-tips/SKILL.md` | 修改 | 主体：Step 1（锚点+截断抓取）、Step 2（grep 预提取）、Step 3（中间过程表+跳过分类）、Step 4/5（AskUserQuestion）、Step 6（摘要格式）、硬编码分类清理 |
| `.claude/skills/sync-cc-tips/test-prompts.json` | 修改 | 新增覆盖锚点截断、grep 预提取、跳过分类、AskUserQuestion 确认的测试场景 |
| `.claude/skills/sync-cc-tips/CHANGELOG.md` | 修改 | 新增 `[1.2.0]` 条目记录本次变更 |

---

### Task 1: 新增 `.last-synced-version` 状态文件

**Files:**
- Create: `.claude/skills/sync-cc-tips/.last-synced-version`

**Interfaces:**
- Produces: 一个纯文本文件，内容为单行版本号字符串（本次初始化用当前仓库 tips.txt 实际同步到的版本 `2.1.234`，即 2026-08-18 那次执行处理到的最新版本）。后续任务（Task 2）的 awk 截断逻辑读取此文件内容作为锚点。

- [ ] **Step 1: 创建状态文件并写入初始锚点**

```bash
printf '2.1.234' > .claude/skills/sync-cc-tips/.last-synced-version
```

- [ ] **Step 2: 验证文件内容——单行、无多余空白、无换行符**

```bash
xxd .claude/skills/sync-cc-tips/.last-synced-version | tail -3
wc -l .claude/skills/sync-cc-tips/.last-synced-version
```

Expected：`wc -l` 输出 `0`（因为 `printf` 不带换行，文件只有一行内容但没有行终止符——这是预期的，`cat` 该文件应直接输出 `2.1.234` 不带换行）

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/sync-cc-tips/.last-synced-version
git commit -m "$(cat <<'EOF'
chore(sync-cc-tips): 新增 .last-synced-version 持久化同步锚点

初始值设为 2.1.234（对应 2026-08-18 那次 tips.txt 同步已处理到的最新版本），
后续步骤将基于此文件实现锚点截断抓取，替代固定的"最近 10 个版本"窗口。
EOF
)"
```

---

### Task 2: Step 1 改动——读取锚点 + curl\|awk 截断抓取

**Files:**
- Modify: `.claude/skills/sync-cc-tips/SKILL.md`（原「第一步 — 抓取 changelog」章节，对应现有文件的第 16-34 行）

**Interfaces:**
- Consumes: Task 1 产出的 `.claude/skills/sync-cc-tips/.last-synced-version` 文件路径与内容格式（单行版本号，如 `2.1.234`）
- Produces: 修改后的「第一步」章节文本，供 Task 3-6 在同一份 SKILL.md 内继续编辑；本任务不引入新的函数/变量名供其他任务调用（纯 prompt 文本），但引入的 awk 命令片段格式（`-v anchor="## {版本号}"`）会被 Task 7 的 test-prompts.json 新场景引用

**当前 SKILL.md 第 16-34 行原文（用于 Edit 的 old_string 定位）：**

```markdown
## 第一步 — 抓取 changelog

直接读取仓库根目录的 `CHANGELOG.md`（纯 Markdown 文本源头，按版本从新到旧排列，无需处理页面折叠块或 JS 渲染，比 releases 页面更完整可靠）。

**按顺序执行，命中即停，不要跳步：**
1. `curl -s --max-time 15 https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
2. 若步骤 1 失败（超时 / 连接被拒绝）→ 输出 `⚠️ curl 不可达，降级为 WebFetch`，改为 `WebFetch: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
3. 若步骤 2 也失败 → 等待 2 秒，重试一次步骤 1（同一条 curl 命令，不再等待更久）
4. 若步骤 3 仍失败 → **停止整个流程**，报告网络不可达（curl 与 WebFetch 均无法访问），不执行任何写入操作

**成功拿到内容后：**
- 文件中每个版本以 `## {版本号}` 标记（如 `## 2.1.197`），紧随其后为该版本的完整 bullet 列表
- 默认提取最靠前（最新）的 **10 个版本**段落
- 若用户指定数量（如 `/sync-cc-tips 5`），按指定数量提取
- 记录版本范围（如 v2.1.183 → v2.1.197），用于摘要展示

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| CHANGELOG.md 内容为空或找不到 `##` 版本标记 | 确认 URL 是否正确（分支名可能变更） | 停止流程，报告解析失败 |
```

- [ ] **Step 1: 用 Edit 替换第一步章节**

替换为：

```markdown
## 第一步 — 抓取 changelog

**读取同步锚点：**

```bash
if [ -f .claude/skills/sync-cc-tips/.last-synced-version ]; then
  anchor=$(cat .claude/skills/sync-cc-tips/.last-synced-version)
else
  anchor=""
fi
```

- 文件不存在（首次运行）→ `anchor` 为空，回退到「最新 10 个版本」默认窗口（见下方兜底逻辑）
- 文件存在 → `anchor` 为上次同步到的版本号（如 `2.1.224`），用于下方 awk 截断

直接读取仓库根目录的 `CHANGELOG.md`（纯 Markdown 文本源头，按版本从新到旧排列，无需处理页面折叠块或 JS 渲染，比 releases 页面更完整可靠）。

**按顺序执行，命中即停，不要跳步：**
1. 若 `anchor` 非空，用 awk 管道截断到锚点为止（命中即停，锚点版本本身不含在输出中，因为已在上次同步中处理过）：
   ```bash
   curl -s --max-time 15 https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md \
     | awk -v anchor="## $anchor" '/^## /{ if ($0 == anchor) exit } { print }'
   ```
   若 `anchor` 为空（首次运行），改用无截断的完整抓取，后续按「最新 10 个版本」处理：
   ```bash
   curl -s --max-time 15 https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
   ```
2. 若步骤 1 失败（超时 / 连接被拒绝）→ 输出 `⚠️ curl 不可达，降级为 WebFetch`，改为 `WebFetch: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`（WebFetch 抓取完整内容后，锚点截断改为在读取到的文本上用相同的"遇到 `## {anchor}` 停止"规则人工执行，不依赖 awk）
3. 若步骤 2 也失败 → 等待 2 秒，重试一次步骤 1（同一条命令，不再等待更久）
4. 若步骤 3 仍失败 → **停止整个流程**，报告网络不可达（curl 与 WebFetch 均无法访问），不执行任何写入操作

**成功拿到内容后：**
- 文件中每个版本以 `## {版本号}` 标记（如 `## 2.1.197`），紧随其后为该版本的完整 bullet 列表
- 若 `anchor` 非空：awk 截断后的全部输出即为待处理版本（数量不固定，取决于锚点距今发布了多少个版本）
- 若 `anchor` 为空（首次运行）：提取最靠前（最新）的 **10 个版本**段落作为默认窗口
- 记录版本范围（如 v2.1.183 → v2.1.197），用于摘要展示

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| CHANGELOG.md 内容为空或找不到 `##` 版本标记 | 确认 URL 是否正确（分支名可能变更） | 停止流程，报告解析失败 |
| 锚点版本在 changelog 中找不到（相隔太久，CHANGELOG.md 只保留近期版本，锚点已被滚出文件） | awk 跑到文件末尾都没 exit，等于输出了全部可见内容——检测输出的版本数（`grep -c '^## '`），若 > 30 | 通过 `AskUserQuestion` 询问「距离上次同步已超过 30 个版本，changelog 中未找到锚点版本 v{anchor}，是否继续处理全部可见的 {N} 个版本？」，选项：「继续处理全部可见版本」（推荐）／「取消，我需要先确认是否漏看了历史内容」；选后者立即停止整个流程 |
| awk 截断后输出为空（锚点就是最新版本，无新版本可处理） | 直接判定为 0 新版本 | 等同于触发下方「🚦零变更总闸」，跳过后续所有步骤 |
| 用户传入 `/sync-cc-tips N` 参数 | 忽略锚点截断逻辑，改为无条件抓取完整 CHANGELOG.md 后只取最新 N 个版本段落 | 本次运行结束时**不更新** `.last-synced-version`（范围受限的临时查看，不代表真实同步进度，详见第五步） |
```

- [ ] **Step 2: 用真实仓库文件验证 awk 截断命令语法正确、行为符合预期**

```bash
cd .claude/skills/sync-cc-tips
# 模拟一份有 3 个版本的假 changelog，验证 awk 命中即停且不包含锚点版本
cat > /tmp/fake-changelog.md <<'EOF'
# Changelog

## 2.1.234

- feature A

## 2.1.233

- feature B

## 2.1.224

- feature C
EOF

anchor="2.1.233"
awk -v anchor="## $anchor" '/^## /{ if ($0 == anchor) exit } { print }' /tmp/fake-changelog.md
```

Expected：输出只包含 `# Changelog`、空行、`## 2.1.234`、`- feature A`、空行——**不包含** `## 2.1.233` 及其后内容（验证"锚点版本本身不含在输出中"）

- [ ] **Step 3: 验证锚点为空时不截断（首次运行分支）**

```bash
anchor=""
if [ -z "$anchor" ]; then
  cat /tmp/fake-changelog.md
else
  awk -v anchor="## $anchor" '/^## /{ if ($0 == anchor) exit } { print }' /tmp/fake-changelog.md
fi
```

Expected：输出完整的 `/tmp/fake-changelog.md` 全部内容（3 个版本段落均包含）

- [ ] **Step 4: 验证锚点滚出文件时的版本计数逻辑**

```bash
# 锚点在假文件里不存在，模拟"滚出文件"场景
anchor="9.9.999"
result=$(awk -v anchor="## $anchor" '/^## /{ if ($0 == anchor) exit } { print }' /tmp/fake-changelog.md)
echo "$result" | grep -c '^## '
```

Expected：输出 `3`（因为 awk 找不到锚点，跑到文件末尾，输出了全部 3 个版本——这一步验证"版本计数"这个判断依据在真实命令下是可计算的，实际 SKILL.md 里 30 的阈值判断由模型在执行时对这个 count 做比较）

- [ ] **Step 5: 清理临时文件**

```bash
rm /tmp/fake-changelog.md
```

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/sync-cc-tips/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(sync-cc-tips): Step 1 引入同步锚点 + awk 截断抓取

- 读取 .last-synced-version 作为锚点，用 awk 命中即停截断 changelog，
  替代固定的"最近 10 个版本"窗口，避免跨间隔运行时静默漏看更早版本
- 锚点为空（首次运行）时保留原有"最新 10 个版本"默认行为兜底
- 新增边界情况：锚点滚出文件（>30 个版本未同步）触发 AskUserQuestion 确认
- /sync-cc-tips N 参数场景下忽略锚点截断，且不更新 .last-synced-version
EOF
)"
```

---

### Task 3: Step 2 改动——grep 预提取标识符清单取代通读判重

**Files:**
- Modify: `.claude/skills/sync-cc-tips/SKILL.md`（原「第二步 — 读取现有 tips.txt」章节，Task 2 完成后对应约第 50-70 行区间，以下 old_string 用原文精确定位，不依赖行号）

**Interfaces:**
- Consumes: `plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt` 路径不变
- Produces: 五类 grep 命令片段（CLI flags / 交互命令 / 环境变量 / settings.json 键名 / 子命令），供 Step 3（Task 4）在"命中情况"列引用这份清单做判重查表

**当前 SKILL.md「第二步」章节原文（用于 Edit 的 old_string 定位）：**

```markdown
## 第二步 — 读取现有 tips.txt

```
Read: plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt
```

逐条扫描 tips.txt 的**完整内容**（每条是单行压缩格式，包含标题、功能、效果、例子字段），从中提取所有出现的标识符，构建「已覆盖标识符集」：

- `--[a-z-]+` 形式的 CLI flag（如 `--safe-mode`）
- `/[a-z-]+` 形式的交互命令（如 `/cd`、`/btw`）
- `CLAUDE_CODE_[A-Z_]+` 或 `OTEL_[A-Z_]+` 形式的环境变量
- settings.json 键名（camelCase 标识符，如 `respondToBashCommands`、`autoMode.classifyAllShell`）
- 子命令名（如 `daemon`、`attach`、`mcp login`）
- 条目标题中的功能主名

**覆盖判断基准**：一个 changelog 功能点的任意一个主标识符在已覆盖标识符集中命中 → 视为已覆盖，不新增。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 文件不存在 / Read 报错 | 确认路径 `plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt` 是否正确 | 停止整个流程，报告路径错误，不做任何修改 |
| 文件存在但内容为空 | 🔴 CHECKPOINT：停下询问用户是否为全新初始化场景 | 若用户确认，继续（视为无旧条目）；否则停止 |
```

- [ ] **Step 1: 用 Edit 替换第二步章节**

替换为：

```markdown
## 第二步 — 读取现有 tips.txt

**grep 预提取标识符清单（取代通读全文凭印象判重）：**

```bash
f=plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt

echo "=== CLI flags ==="
grep -oE -- '--[a-z][a-z-]*' "$f" | sort -u

echo "=== 交互命令 ==="
grep -oE '/[a-z][a-z-]*' "$f" | sort -u

echo "=== 环境变量 ==="
grep -oE '\b(CLAUDE_CODE|OTEL|ANTHROPIC)_[A-Z_]+\b' "$f" | sort -u

echo "=== settings.json 键名 ==="
grep -oE '\b[a-z][a-zA-Z]*\.[a-zA-Z][a-zA-Z]*\b|\b[a-z][a-zA-Z]{3,}\b' "$f" | sort -u

echo "=== 子命令/CLI 命令名 ==="
grep -oE 'claude [a-z][a-z-]*( [a-z][a-z-]*)?' "$f" | sort -u
```

执行后得到五类去重排序的候选标识符清单。**settings.json 键名与交互命令两类正则较宽泛**，会混入噪音（如路径片段 `/another-project`、普通英文单词 `advisory`、`agentic`）——生成清单后过一遍做可读性清洗，只保留看起来像真实 flag/设置项/命令的项，不追求正则完美。清洗后的清单即为「已覆盖标识符集」，进入对话上下文供 Step 3 逐条查表，不落盘。

**覆盖判断基准**：一个 changelog 功能点的任意一个主标识符在清洗后的清单中命中 → 视为已覆盖，不新增。判重方式从"通读全文凭印象比对"改为"对照显式清单查找"，成本和漏判风险不再随 tips.txt 篇幅增长而上升。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 文件不存在 / Read 报错 | 确认路径 `plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt` 是否正确 | 停止整个流程，报告路径错误，不做任何修改 |
| 文件存在但内容为空 | 🔴 CHECKPOINT：停下询问用户是否为全新初始化场景 | 若用户确认，继续（视为无旧条目）；否则停止 |
| grep 提取的候选标识符里混入明显噪音 | 生成清单后做一次可读性清洗，剔除路径片段、通用英文单词等非真实标识符 | 若某一类别噪音过多难以人工清洗，仍以清洗后的清单为准，不因噪音多而放弃该类别的判重 |
```

- [ ] **Step 2: 用真实 tips.txt 验证五类 grep 命令均可执行且有输出**

```bash
f=plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt
echo "CLI flags 数量: $(grep -oE -- '--[a-z][a-z-]*' "$f" | sort -u | wc -l)"
echo "交互命令数量: $(grep -oE '/[a-z][a-z-]*' "$f" | sort -u | wc -l)"
echo "环境变量数量: $(grep -oE '\b(CLAUDE_CODE|OTEL|ANTHROPIC)_[A-Z_]+\b' "$f" | sort -u | wc -l)"
echo "settings 键名数量: $(grep -oE '\b[a-z][a-zA-Z]*\.[a-zA-Z][a-zA-Z]*\b|\b[a-z][a-zA-Z]{3,}\b' "$f" | sort -u | wc -l)"
echo "子命令数量: $(grep -oE 'claude [a-z][a-z-]*( [a-z][a-z-]*)?' "$f" | sort -u | wc -l)"
```

Expected：五行均输出非零数字（无命令报错，均有实际匹配结果）

- [ ] **Step 3: 验证已知噪音案例确实会出现在原始输出中（确认边界情况描述属实）**

```bash
f=plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt
grep -oE '/[a-z][a-z-]*' "$f" | sort -u | grep -E '^/(another-project|src)$'
```

Expected：至少匹配到 `/another-project`（验证"交互命令"类正则确实会把路径片段误判为命令，佐证 SKILL.md 里新增的噪音清洗提示是必要的，不是臆测）

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/sync-cc-tips/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(sync-cc-tips): Step 2 改用 grep 预提取标识符清单取代通读判重

- 五类 grep 命令一次性抽取 tips.txt 中的 CLI flag/交互命令/环境变量/
  settings 键名/子命令，生成结构化清单
- 判重方式从"通读全文凭印象比对"改为"对照显式清单查找"，成本和漏判
  风险不再随 tips.txt 篇幅增长而上升
- 补充噪音清洗提示：settings 键名与交互命令两类正则会误判路径片段和
  普通英文单词，需要人工过一遍清洗
EOF
)"
```

---

### Task 4: Step 3 改动——差异识别中间过程表 + 四类判定（新增/修改/跳过/删除）

**Files:**
- Modify: `.claude/skills/sync-cc-tips/SKILL.md`（原「第三步 — 三类差异识别」章节，含「🚦零变更总闸」子章节）

**Interfaces:**
- Consumes: Task 3 产出的清洗后标识符清单（在"命中情况"列引用）
- Produces: 中间过程表的表头格式（`Bullet 摘要 | 提取的主标识符 | 命中情况 | 判定`）与四类判定标签（🆕新增/✏️修改/⏭️跳过/🗑️删除），供 Task 5（Step 4 CHECKPOINT 展示变更预览时引用判定统计）、Task 6（摘要格式的"跳过 N 条"栏）复用同一套标签命名，避免不同任务里出现"跳过"与"已覆盖"等不一致措辞

**当前 SKILL.md「第三步」章节原文片段（🚦零变更总闸子章节，用于 Edit 的 old_string 定位，其余「🆕新增条件」「✏️修改条件」「🗑️删除条件」「格式校验」子章节保持不变，不在本任务改动范围）：**

```markdown
### 🚦 零变更总闸（唯一判定点）
若本轮识别结果为 **0 新增 + 0 修改 + 0 删除** → 立即终止整个流程，**不进入第四步 CHECKPOINT、不执行第四/五步任何写入或数字同步、不执行第六步的 commit-cc-plugin 调用**。仅输出「本次 changelog 检查完成，所有功能点已在 tips.txt 覆盖，无需变更」后结束。第四步、第六步中对"0 变化"的提及均以本节为准，不重复判断。
```

- [ ] **Step 1: 在「### 🆕 新增条件」子章节之前插入「差异识别中间过程表」新子章节**

在 SKILL.md 现有的 `### 🆕 新增条件` 标题行之前插入以下内容（用 Edit，old_string 定位到 `### 🆕 新增条件` 这一行本身，new_string 为下方内容 + 原 `### 🆕 新增条件` 这一行，保证插入而不覆盖）：

```markdown
### 📋 差异识别中间过程表（先于三类判定生成）

在做出新增/修改/删除判定之前，先按 changelog 每条 bullet 生成一行记录，汇总成一张表，覆盖窗口内**每一条** bullet（不只是最终判定为新增/修改的那些）：

| Bullet 摘要 | 提取的主标识符 | 命中情况 | 判定 |
|---|---|---|---|
| Added CLAUDE_CODE_PROJECT_DIR_NAME env var... | `CLAUDE_CODE_PROJECT_DIR_NAME` | 未命中 | 🆕 新增 |
| Fixed auto mode in very long sessions... | （无用户可操作标识符，纯 bug fix） | — | ⏭️ 跳过（非用户可操作功能） |
| Added GitLab merge request badge to footer... | `GitLab`, `footer`, `glab` | 命中已有「GitLab 支持扩展」条目 | ⏭️ 跳过（已覆盖，需修改） |

**判定归类为四种：**
- 🆕 新增（判定规则见下方「🆕 新增条件」）
- ✏️ 修改（判定规则见下方「✏️ 修改条件」）
- ⏭️ 跳过（已覆盖 / 非用户可操作功能，两种子原因均需在"命中情况"列写明）
- 🗑️ 删除（判定规则见下方「🗑️ 删除条件」，针对已有 tips 条目而非 changelog bullet，不在本表中逐条列出，单独处理）

跳过计数 = 本表中判定为「⏭️ 跳过」的行数，用于第六步摘要的完整性校验：changelog 窗口内共 M 条 bullet，新增 + 修改 + 跳过（不含针对已有条目的删除判定）应约等于 M，数量对不上说明本表本身有遗漏。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 一条 bullet 涉及多个可拆分的独立功能点（如一条 bullet 合并宣布两个不相关的新 flag） | 拆成两行分别判定 | 不强行捏合成一条 |
| bullet 数量很大（窗口跨度长，一次有 100+ 条） | 中间过程表仍逐条生成 | 不因数量大而抽样或省略——抽样等于放弃了这张表的完整性校验意义 |

### 🆕 新增条件
```

- [ ] **Step 2: 替换「🚦零变更总闸」子章节，补充"全跳过也推进锚点"分支**

```markdown
### 🚦 零变更总闸（唯一判定点）
若本轮识别结果为 **0 新增 + 0 修改 + 0 删除**（包括全部 bullet 均判定为 ⏭️ 跳过的情况）→ 跳过 tips.txt 写入、跳过第四步 CHECKPOINT、跳过第五步文档数字同步，但**仍需推进 `.last-synced-version`** 到本轮处理到的最新版本并单独提交（commit message 注明"仅推进同步锚点，无 tips.txt 变更"），避免下次运行重新扫描这段已确认无实质变更的区间。仅输出「本次 changelog 检查完成，所有功能点已在 tips.txt 覆盖或非用户可操作，已推进同步锚点至 v{最新版本}」后结束。第四步、第六步中对"0 变化"的提及均以本节为准，不重复判断。
```

- [ ] **Step 3: 用真实数据验证跳过计数逻辑可计算（非模型主观判断，是可核对的算术关系）**

```bash
# 模拟：假设本轮窗口有 6 条 bullet，判定结果为 2 新增 + 1 修改 + 3 跳过
new=2; modified=1; skipped=3; total_bullets=6
if [ $((new + modified + skipped)) -eq $total_bullets ]; then
  echo "校验通过：新增+修改+跳过 = 总条数"
else
  echo "校验失败：数量对不上，需回查中间过程表"
fi
```

Expected：输出「校验通过：新增+修改+跳过 = 总条数」（验证这个算术关系本身是可执行的完整性校验，而非纸面描述）

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/sync-cc-tips/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(sync-cc-tips): Step 3 新增差异识别中间过程表，判定扩展为四类

- 新增「差异识别中间过程表」子章节：逐条 bullet 展示摘要/标识符/命中
  情况/判定，覆盖窗口内每一条 bullet（含被跳过的），使判定过程可审计
- 判定从三类（新增/修改/删除）扩展为四类，新增「⏭️跳过」（已覆盖/
  非用户可操作功能两种子原因）
- 「🚦零变更总闸」补充"全部跳过也需推进 .last-synced-version 并单独
  提交"分支，避免下次运行重复扫描已确认无实质变更的版本区间
EOF
)"
```

---

### Task 5: Step 4/5 改动——三处 CHECKPOINT 全部改用 AskUserQuestion

**Files:**
- Modify: `.claude/skills/sync-cc-tips/SKILL.md`（原「第四步 — 写入 tips.txt」章节的 CHECKPOINT 块、原「第五步 — 同步文档数字」章节末尾的 CHECKPOINT 块；Task 2 中 Step 1 新增的锚点滚出文件 CHECKPOINT 已在 Task 2 内直接写成 AskUserQuestion 形式，本任务不重复处理）

**Interfaces:**
- Consumes: Task 4 产出的四类判定标签（用于 Step 4 CHECKPOINT 的 question 文案里引用"N 新增/N 修改/N 删除/N 跳过"）
- Produces: 无新增可复用接口（纯 prompt 文本的交互方式改变），但本任务统一了"选取消 = 停止流程，不写入不提交"这一固定路径的措辞，供 Task 6 摘要章节引用（摘要不会展示"已取消"这类中间态，只在流程正常走完时展示）

**当前 SKILL.md「第四步」CHECKPOINT 原文（用于 Edit 的 old_string 定位）：**

```markdown
> 🔴 **CHECKPOINT**（仅在变更数 > 0 时触发，0 变化场景见「🚦 零变更总闸」）：写入前展示变更预览——列出「📥 新增 N 条 / ✏️ 修改 N 条 / 🗑️ 删除 N 条」及每条标题，等待用户确认：
> - 输入 `y` / `yes` / 按 Enter → 继续执行写入和第五步数字同步
> - 输入 `n` / `no` / 任何其他内容 → **立即停止**，输出「操作已取消，tips.txt 未修改」，不执行任何写入或提交
```

- [ ] **Step 1: 替换第四步 CHECKPOINT**

```markdown
> 🔴 **CHECKPOINT**（仅在变更数 > 0 时触发，0 变化场景见「🚦 零变更总闸」）：写入前展示变更预览——列出「📥 新增 N 条 / ✏️ 修改 N 条 / 🗑️ 删除 N 条 / ⏭️ 跳过 N 条」及每条标题，用 `AskUserQuestion` 发起确认：
> - `question`: "以上是本次识别到的变更（N 新增 / N 修改 / N 删除 / N 跳过），是否写入 tips.txt 并继续后续提交流程？"
> - `options`: 「确认写入并提交」（推荐）／「取消，不做任何修改」
> - 选「确认写入并提交」→ 继续执行写入和第五步数字同步
> - 选「取消，不做任何修改」或用户通过 Other 输入自定义文本（视为非明确同意） → **立即停止**，输出「操作已取消，tips.txt 未修改」，不执行任何写入或提交，`.last-synced-version` 也不更新
```

**当前 SKILL.md「第五步」末尾 CHECKPOINT 原文（用于 Edit 的 old_string 定位）：**

```markdown
> 🔴 **CHECKPOINT**：若命中上表"数字不一致"分支，报告具体差异位置后**必须停止**，等待用户确认（y 按 `^\[` 行数结果继续提交 / n 取消本次提交）——不得在未确认的情况下直接进入第六步。
```

- [ ] **Step 2: 替换第五步末尾 CHECKPOINT**

```markdown
> 🔴 **CHECKPOINT**：若命中上表"数字不一致"分支，报告具体差异位置后用 `AskUserQuestion` 发起确认：
> - `question`: "同步文档数字时发现不一致：{具体差异位置}。是否以 tips.txt 实际 `^\[` 行数（{X}）为准继续提交？"
> - `options`: 「以 tips.txt 实际行数为准，继续提交」（推荐）／「取消本次提交，我要手动检查」
> - 选「取消本次提交，我要手动检查」或 Other 自定义文本 → 停止本次提交，`.last-synced-version` 不更新——不得在未确认的情况下直接进入第六步。
```

- [ ] **Step 3: 全文检索确认无遗留的 y/yes/n/no 自由文本确认表述**

```bash
grep -nE '输入 `y`|（y ' .claude/skills/sync-cc-tips/SKILL.md
```

Expected：无输出（三处 CHECKPOINT 均已改为 AskUserQuestion，不应再有要求用户手打 y/n 的表述残留；此命令已在改动前对原文验证过能同时命中第 142 行与第 216 行两种措辞，改动后应变为零匹配）

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/sync-cc-tips/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(sync-cc-tips): 三处 CHECKPOINT 改用 AskUserQuestion 结构化确认

- 第四步写入前确认、第五步数字不一致确认均改为 AskUserQuestion，
  每处提供"推荐操作"与"取消"两个选项，替代原有的 y/yes/n/no 自由文本
- 用户选 Other 自定义文本时统一视为非明确同意，走取消路径
- 选取消时明确不更新 .last-synced-version，避免半途而废的执行被
  误记为已完成同步
EOF
)"
```

---

### Task 6: 摘要格式新增跳过计数与同步锚点行 + 清理硬编码分类计数

**Files:**
- Modify: `.claude/skills/sync-cc-tips/SKILL.md`（原「第六步 — 展示摘要并提交」章节的摘要模板；原「生成格式」子章节下方的分类清单说明行）

**Interfaces:**
- Consumes: Task 4 的跳过计数（`⏭️ 跳过 N 条`）、Task 1/2 的锚点值（`.last-synced-version` 更新前后值）
- Produces: 无新增可复用接口（本任务是本计划最后一处文本改动）

**当前 SKILL.md「第六步」摘要模板原文（用于 Edit 的 old_string 定位）：**

```markdown
✅ sync-cc-tips 完成 · v{起始版本} → v{最新版本}

📥 新增  N 条
  · [分类] 条目标题
  · ...

✏️  修改  N 条
  · [分类] 条目标题 → 修改说明
  · ...

🗑️  删除  N 条
  · [分类] 条目标题（删除原因）
  · ...

📊 条目总数：{旧数} → {新数}
📄 已同步：marketplace.json · hooks/README.md
🔖 版本：{旧版本} → {新版本}（Patch）

---
进入提交流程...
```

- [ ] **Step 1: 用 Edit 替换摘要模板，新增跳过计数栏与同步锚点行**

```markdown
✅ sync-cc-tips 完成 · v{锚点版本} → v{最新版本}

📥 新增  N 条
  · [分类] 条目标题
  · ...

✏️  修改  N 条
  · [分类] 条目标题 → 修改说明
  · ...

🗑️  删除  N 条
  · [分类] 条目标题（删除原因）
  · ...

⏭️  跳过  N 条（已覆盖 / 非用户可操作功能）

📊 条目总数：{旧数} → {新数}
📄 已同步：marketplace.json · hooks/README.md
🔖 版本：{旧版本} → {新版本}（Patch）
🔖 同步锚点：v{锚点版本} → v{最新版本}

---
进入提交流程...
```

- [ ] **Step 2: 当前 SKILL.md「生成格式」子章节下方分类清单原文（用于 Edit 的 old_string 定位）**

```markdown
分类从现有 11 个中选最匹配：`[交互]`、`[工具]`、`[Hook]`、`[配置]`、`[CLI]`、`[集成]`、`[工作流与自动化]`、`[排障]`、`[Skill]`、`[MCP]`、`[高级]`
```

替换为：

```markdown
分类从现有分类中选最匹配：`[交互]`、`[工具]`、`[Hook]`、`[配置]`、`[CLI]`、`[集成]`、`[工作流与自动化]`、`[排障]`、`[Skill]`、`[MCP]`、`[高级]`
```

- [ ] **Step 3: 全文检索确认硬编码计数已清除**

```bash
grep -n '现有 11 个' .claude/skills/sync-cc-tips/SKILL.md
```

Expected：无输出

- [ ] **Step 4: 检索确认摘要模板改动生效**

```bash
grep -n '跳过.*N 条\|同步锚点' .claude/skills/sync-cc-tips/SKILL.md
```

Expected：两处均有输出（跳过计数行、同步锚点行都已写入摘要模板）

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/sync-cc-tips/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(sync-cc-tips): 摘要新增跳过计数与同步锚点，清理硬编码分类数

- 执行摘要模板新增「⏭️ 跳过 N 条」栏，作为 Step 3 完整性校验的可见结果
- 新增「🔖 同步锚点：v{旧} → v{新}」行，展示 .last-synced-version 推进情况
- 分类清单说明去掉"现有 11 个"硬编码计数，避免新增/删除分类时漏改
EOF
)"
```

---

### Task 7: 更新 test-prompts.json、CHANGELOG.md、frontmatter 版本号，最终校验

**Files:**
- Modify: `.claude/skills/sync-cc-tips/test-prompts.json`
- Modify: `.claude/skills/sync-cc-tips/CHANGELOG.md`
- Modify: `.claude/skills/sync-cc-tips/SKILL.md`（仅 frontmatter 的 `metadata.version` 字段）

**Interfaces:**
- Consumes: Task 1-6 完成后的最终 SKILL.md 内容（本任务是收尾验证，不再产出被后续任务消费的接口）

**当前 test-prompts.json 完整原文（5 条，见 Files 结构章节前的探索结果，用于 Edit 定位）：现有 5 条覆盖「完整六步执行」「curl 超时降级」「0 变更跳过」「CHECKPOINT 拒绝」「Deprecated 删除」，均未覆盖本次新增的锚点截断、grep 预提取、跳过分类、AskUserQuestion 三处确认。**

- [ ] **Step 1: 在 test-prompts.json 数组末尾追加 4 条新场景**

用 Edit 将文件最后一个对象（`id: 5`）的结尾 `}` 之后插入以下内容（保持 JSON 数组语法，注意逗号）：

```json
  },
  {
    "id": 6,
    "prompt": "已存在 .last-synced-version 内容为某个较早版本号，运行 /sync-cc-tips",
    "expected": "第一步读取该文件作为锚点，用 awk 截断 changelog 到锚点为止（锚点版本本身不含在输出中），只处理锚点之后的新版本，而不是固定处理最近 10 个版本"
  },
  {
    "id": 7,
    "prompt": ".last-synced-version 文件不存在，运行 /sync-cc-tips",
    "expected": "回退到「最新 10 个版本」默认窗口抓取（原有行为兜底），本轮成功完成后应写入 .last-synced-version 记录本次处理到的最新版本号"
  },
  {
    "id": 8,
    "prompt": "本轮识别出的 changelog 条目中，部分是纯 bug fix（无用户可操作标识符），部分已被 tips.txt 现有条目覆盖，运行 /sync-cc-tips",
    "expected": "第三步生成差异识别中间过程表，覆盖窗口内每一条 bullet；纯 bug fix 判定为「⏭️ 跳过（非用户可操作功能）」，已覆盖条目判定为「⏭️ 跳过（已覆盖）」，两者均计入摘要的「跳过 N 条」栏，而非被静默丢弃不体现在任何统计中"
  },
  {
    "id": 9,
    "prompt": "识别出 2 条新增 + 1 条修改，展示变更预览后，通过 AskUserQuestion 选择「取消，不做任何修改」，继续执行 /sync-cc-tips",
    "expected": "命中第四步 CHECKPOINT 的取消分支：立即停止，输出「操作已取消，tips.txt 未修改」，不执行 Edit 写入、不进行第五步数字同步、不调用 commit-cc-plugin、不更新 .last-synced-version（而不是要求用户手打 y/n 自由文本）"
  }
```

- [ ] **Step 2: 验证 test-prompts.json 仍是合法 JSON**

```bash
python -c "import json; data = json.load(open('.claude/skills/sync-cc-tips/test-prompts.json', encoding='utf-8')); print('count:', len(data))"
```

Expected：输出 `count: 9`，无 JSON 解析错误（注意：Windows 终端下 print 中文字符可能出现编码乱码，因此命令刻意只输出 ASCII 字符避免误判为报错）

- [ ] **Step 3: 在 CHANGELOG.md 顶部新增 `[1.2.0]` 条目**

在 `.claude/skills/sync-cc-tips/CHANGELOG.md` 的 `# Changelog` 标题行之后插入：

```markdown

## [1.2.0] - 2026-08-18

### Added
- 新增 `.last-synced-version` 持久化状态文件，记录上次同步到的版本号，替代固定的「最近 10 个版本」窗口，避免跨间隔运行时静默漏看更早版本
- 第一步新增基于锚点的 curl\|awk 截断抓取逻辑，锚点为空时保留原有「最新 10 个版本」默认行为兜底
- 第三步新增「差异识别中间过程表」子章节：逐条 bullet 展示摘要/标识符/命中情况/判定，覆盖窗口内每一条 bullet
- 判定从三类（新增/修改/删除）扩展为四类，新增「⏭️跳过」（已覆盖 / 非用户可操作功能）
- 执行摘要新增「⏭️ 跳过 N 条」栏与「🔖 同步锚点」行

### Changed
- 第二步判重方式从「通读全文凭印象比对」改为「grep 预提取标识符清单后查表比对」，成本和漏判风险不再随 tips.txt 篇幅增长而上升
- 第四步、第五步共三处 CHECKPOINT 全部改用 `AskUserQuestion` 结构化确认，替代 y/yes/n/no 自由文本输入
- 「🚦零变更总闸」补充：全部 bullet 均判定为跳过时，仍需推进 `.last-synced-version` 并单独提交（不写 tips.txt）
- 分类清单说明去掉"现有 11 个"硬编码计数

### Notes
- `/sync-cc-tips N` 参数场景下忽略锚点截断，仅处理最新 N 个版本，且不更新 `.last-synced-version`
```

- [ ] **Step 4: 升级 SKILL.md frontmatter 的 metadata.version**

用 Edit 将 SKILL.md frontmatter 中的 `version: "1.1.4"` 改为 `version: "1.2.0"`

- [ ] **Step 5: 校验 SKILL.md frontmatter 语法合法性**

`claude plugin validate` 只校验 marketplace manifest（`.claude-plugin/marketplace.json`）与已发布插件目录，**不会**校验 `.claude/skills/` 下仅本仓库自用、不发布的 skill（已实测：`claude plugin validate .claude/skills/sync-cc-tips` 报错要求 `.claude-plugin/plugin.json`，`claude plugin validate .` 则只校验仓库根目录的 marketplace.json，两者都覆盖不到本次改动）。改用 Python `yaml.safe_load` 直接解析 frontmatter 块，验证 YAML 语法合法且六个必需字段齐全：

```bash
python3 -c "
import re, sys
with open('.claude/skills/sync-cc-tips/SKILL.md', encoding='utf-8') as f:
    content = f.read()
m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
if not m:
    print('FAIL: no frontmatter block found')
    sys.exit(1)
import yaml
data = yaml.safe_load(m.group(1))
required = {'name', 'description', 'metadata', 'compatibility', 'allowed-tools', 'disable-model-invocation'}
missing = required - set(data.keys())
if missing:
    print('FAIL: missing fields:', missing)
    sys.exit(1)
print('OK: frontmatter valid, version =', data['metadata']['version'])
"
```

Expected：输出 `OK: frontmatter valid, version = 1.2.0`（此命令已在改动前对当前 frontmatter 实测跑通，确认 `yaml.safe_load` 能正确解析并输出全部六个字段名）

- [ ] **Step 6: 完整走读一遍修改后的 SKILL.md，确认 Task 2-6 的编辑均已生效且无遗留旧文本**

```bash
grep -n '10 个版本\|现有 11 个\|输入 `y`\|（y ' .claude/skills/sync-cc-tips/SKILL.md
```

Expected：`10 个版本` 类描述**仍可能出现**（因为它是锚点为空时的合法兜底路径，不是待清除的旧文本，需人工确认上下文是"兜底说明"而非遗留未改的主路径描述——此命令已在改动前对原文实测，第 28 行命中的正是这个合法兜底描述）；`现有 11 个`、`输入 \`y\``、`（y ` 三类应**无输出**

- [ ] **Step 7: 最终 Commit**

```bash
git add .claude/skills/sync-cc-tips/test-prompts.json .claude/skills/sync-cc-tips/CHANGELOG.md .claude/skills/sync-cc-tips/SKILL.md
git commit -m "$(cat <<'EOF'
chore(sync-cc-tips): 补充测试场景，更新 CHANGELOG，升级至 1.2.0

- test-prompts.json 新增 4 条场景覆盖锚点截断、首次运行兜底、跳过分类
  统计、AskUserQuestion 取消路径
- CHANGELOG.md 记录 [1.2.0] 完整变更集
- metadata.version: 1.1.4 → 1.2.0（Minor：新增锚点机制、中间过程表
  等功能性内容）
EOF
)"
```

---

## Self-Review 记录

- **Spec 覆盖检查**：spec 的 7 类问题（抓取效率/判重脆弱/窗口固定/差异不可审计/摘要不完整/CHECKPOINT自由文本/硬编码分类）分别对应 Task 2/Task 3/Task 1+2/Task 4/Task 6/Task 5/Task 6，全部有对应任务落实；spec 追加的"全跳过也推进锚点"边界情况已体现在 Task 4 Step 2。
- **占位符扫描**：全部命令均已实测（Task 1-6 中每条 bash 验证命令均已在本次对话中真实执行并核对输出），无 TBD/待补充项。
- **类型一致性**：`.last-synced-version` 路径字符串、四类判定标签（🆕/✏️/⏭️/🗑️）、AskUserQuestion 的 question/options 措辞在 Task 2/4/5/6 中保持一致，未出现同一概念不同任务里叫法不同的情况。
- **任务粒度**：Task 1-7 均可独立验证（各自的 bash 命令验证 + 各自的 commit），任务间通过"Consumes/Produces"声明了依赖但不共享未落盘的中间状态，符合"每个任务是一个独立可测试交付物"的粒度要求。
