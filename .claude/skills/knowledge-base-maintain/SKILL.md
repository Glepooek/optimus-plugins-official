---
name: knowledge-base-maintain
description: 新增、修改、迁移 knowledge-base/ 下的规范条目或 reference 条目时使用；同步更新 index.jsonl 索引、CHANGELOG.md 与版本号，并跑一致性校验。触发词："新增规范条目"、"知识库加一条"、"迁移知识库条目"、"校验知识库索引"。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要本机 Python 3（跑 knowledge-base/check_index.py 做一致性校验），无 MCP 或第三方 CLI 依赖。
allowed-tools: Read Write Edit Bash Grep Glob
---

# 知识库维护

维护 `knowledge-base/` 下的内容与索引一致性：新增条目、修改/迁移条目、仅校验三种场景。

## Step 1：确认场景与依赖

先确认 Python 3 可用：

```bash
python --version
```

不可用则提示用户安装 Python 3 后重试，终止本次操作（依赖检查失败，硬性阻断）。

确认场景：
- **新增条目**：新增一条 `rule` 或 `reference`
- **修改/迁移条目**：修改已有条目内容，或把内容从规范文件移到 `reference/`（或反之）
- **仅校验**：不新增/修改内容，只想看当前 `knowledge-base/` 一致性状态

## Step 2（新增条目）：收集条目信息

依次询问用户（已在触发语句中提供的不重复问）：

1. **`domain`**：目标领域（`csharp`/`wpf`/其他）。若目标领域目录不存在（`knowledge-base/<domain>/` 不存在），确认是新建领域——新建领域时先创建 `knowledge-base/<domain>/README.md`（参照 `knowledge-base/csharp/README.md` 的章节结构：文档目的、适用范围与读者、规范级别、阅读路径、文件地图）与空的 `knowledge-base/<domain>/index.jsonl`。
2. **`kind`**：`rule` 或 `reference`。
3. 若 `kind=rule`：追问 **`level`**（`MUST`/`SHOULD`/`MAY`）。
4. **正文归属**：`rule` 写入哪个规范文件的哪个章节（已有文件追加小节，或指出需要新建文件）；`reference` 写入 `reference/<主题slug>.md`（新文件，不编号）。
5. **`tags`**、**`summary`**、**`title`**：与用户共同确定，`summary` 一句话，不超过一行。

## Step 3（新增条目）：写入正文与索引

1. 用 Edit/Write 把正文内容写入 Step 2 确定的文件位置。
2. 生成 `id`：`<domain>.<文件编号或ref>.<slug>`（如 `csharp.02.xxx` 或 `csharp.ref.xxx`），确认在该领域 `index.jsonl` 中未出现过。
3. 用 Edit 在对应 `knowledge-base/<domain>/index.jsonl` **末尾追加一行**（不重排已有行），字段：`id`、`kind`、`level`（仅 rule）、`file`、`anchor`（标题文本，非 slug；`reference` 条目留空字符串）、`title`、`tags`、`summary`。

## Step 4（修改/迁移条目）：定位与同步

1. 用 Grep 在目标领域 `index.jsonl` 中按 `id` 或关键词定位现有记录行。
2. 修改正文内容（若涉及跨文件迁移，如从规范文件移到 `reference/`：先在新位置写入正文，再删除旧位置正文，最后更新索引行的 `file`/`anchor`/`kind` 字段——不得只改索引不改正文，也不得只改正文不改索引）。
3. 用 Edit 更新 `index.jsonl` 中对应行的变化字段。

## Step 5：运行一致性校验

```bash
cd knowledge-base && python check_index.py <domain>
```

- 输出 `OK: 共检查 N 条记录，未发现问题` → 继续 Step 6。
- 输出非零退出码 + 问题列表 → 逐条修复（常见问题：`anchor` 文本与实际标题不完全匹配、`file` 路径写错、`id` 重复），修复后重新运行本命令，直到 `OK`。

## Step 6：同步版本号与 CHANGELOG（新增/修改/迁移场景，仅校验场景跳过）

判断本次变更的版本升级级别：

| 变更类型 | 版本升级 |
|---|---|
| 新增领域、新增规范条目、新增 reference 条目 | Minor `x.X.x` |
| 修改已有规范/reference 内容、修正索引、文档优化 | Patch `x.x.X` |
| 删除领域、删除规范条目、规范措辞产生不兼容语义变化（如 SHOULD 改 MUST） | Major `X.x.x` |

用 Edit 更新 `knowledge-base/README.md` 顶部 `> 版本：x.x.x`，并在 `knowledge-base/CHANGELOG.md` 顶部追加对应版本条目（格式同 skill CHANGELOG：`## [版本号] - YYYY-MM-DD` + `### Added`/`Changed`/`Removed`/`Fixed`，只写实际发生的类别）。

## Step 7：提交

`knowledge-base/` 属于文档资产，不受 `commit-cc-plugin` 关于 `plugins/` 下 skill 改动的强制流程约束，但仍需遵循仓库通用 git 纪律（逐文件暂存、写清楚的提交信息）。若同一次改动还涉及 `plugins/` 下 skill（如某 skill 引用了新增条目），该部分改动必须走 `commit-cc-plugin`。

## 失败处理

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| `check_index.py` 报 `id` 重复 | 检查是否误用了已存在的 id 命名规则，改用更具体的 slug | 若确认是历史遗留重复，两条记录都需人工核对哪条是权威版本，不能随意删一条了事 |
| `check_index.py` 报 anchor 不匹配 | 打开目标文件确认标题文字的准确文本（含大小写、标点），更新索引 `anchor` 字段 | 若目标章节确实还不存在，先在正文补齐该章节标题，再回填索引 |
| 新建领域但用户未提供该领域的规范级别定义 | 参照 `knowledge-base/csharp/README.md` 的"规范级别"章节直接复用同一套 MUST/SHOULD/MAY 定义，无需重新设计 | 若用户希望该领域有不同的级别体系，先与用户确认具体差异再落地 |
