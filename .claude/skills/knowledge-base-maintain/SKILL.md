---
name: knowledge-base-maintain
description: 新增、修改、迁移 knowledge-base/ 下的规范条目或 reference 条目时使用；同步更新 index.jsonl 索引、CHANGELOG.md 与版本号，并跑一致性校验。触发词："新增规范条目"、"知识库加一条"、"迁移知识库条目"、"校验知识库索引"。
metadata:
  version: "1.1.0"
  author: desktop client team
  category: tool
compatibility: 需要本机 Python 3（跑本 skill scripts/check_index.py 做一致性校验），无 MCP 或第三方 CLI 依赖。
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

1. **`domain`**：目标领域（`csharp`/`wpf`/其他）。若目标领域目录不存在（`knowledge-base/<domain>/` 不存在），确认是新建领域——新建领域时先创建 `knowledge-base/<domain>/00-README.md`（参照 `knowledge-base/csharp/00-README.md` 的章节结构：文档目的、适用范围与读者、规范级别、阅读路径、文件地图）与空的 `knowledge-base/<domain>/index.jsonl`，并在 `knowledge-base/catalog.json` 的 `domains` 数组追加一条记录（`domain`/`title`/`categories`/`owner`/`status`/`consumers`/`reviewed_at`）——未登记会导致校验失败。
2. **`kind`**：`rule` 或 `reference`。
3. 若 `kind=rule`：追问 **`level`**（`MUST`/`SHOULD`/`MAY`）。
4. **正文归属**：`rule` 写入 `rules/` 下哪个规范文件的哪个章节（已有文件追加小节，或指出需要新建文件）；`reference` 写入 `reference/<主题slug>.md`（新文件，不编号）。
5. **`tags`**、**`summary`**、**`title`**：与用户共同确定，`summary` 一句话，不超过一行。

判断索引粒度：可独立用于合规判断的规则单独登记一条（锚点指向其小节）；导航性标题（阅读路径、文件地图、"权威参考"）不登记；`reference` 默认按整篇文档登记，仅当内部存在多个会被独立检索的主题时才拆条。完整规范见 `knowledge-base/README.md` 的"索引粒度规范"。

## Step 3（新增条目）：写入正文与索引

1. 用 Edit/Write 把正文内容写入 Step 2 确定的文件位置（`rule` → `<domain>/rules/`，`reference` → `<domain>/reference/`）。
2. 生成 `id`：`<domain>.<两位文件编号或 ref>.<slug>`（如 `csharp.02.xxx` 或 `csharp.ref.xxx`），slug 只用小写字母/数字/连字符，确认在该领域 `index.jsonl` 中未出现过。
3. 用 Edit 在对应 `knowledge-base/<domain>/index.jsonl` **末尾追加一行**（不重排已有行），必填字段：`id`、`kind`、`level`（仅 rule）、`file`（相对领域根，如 `rules/02-coding-style.md`）、`anchor`（标题文本，非 slug；`reference` 条目留空字符串）、`title`、`tags`、`summary`。可选治理字段（`enforcement`/`status`/`source`/`applies_to`/`reviewed_at`/`owner`）按需填写，取值约束见 `knowledge-base/README.md` 字段表。

## Step 4（修改/迁移条目）：定位与同步

1. 用 Grep 在目标领域 `index.jsonl` 中按 `id` 或关键词定位现有记录行。
2. 修改正文内容（若涉及跨目录迁移，如从 `rules/` 移到 `reference/`：先在新位置写入正文，再删除旧位置正文，最后更新索引行的 `file`/`anchor`/`kind` 字段——不得只改索引不改正文，也不得只改正文不改索引）。
3. 用 Edit 更新 `index.jsonl` 中对应行的变化字段。
4. **迁移或重命名文件时**，用 Grep 在全仓库反查引用该路径的位置并同步更新四处：索引 `file` 字段、领域 `00-README.md` 的文件地图、其他正文的交叉引用、消费者 skill 的引用（含 Markdown 链接目标 `](...)`，不只是反引号提及）。历史记录类文本（CHANGELOG、正文头部"更新历史"、`docs/superpowers/` 下的历史计划）记录的是当时事实，不改写。

## Step 5：运行一致性校验

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>
```

**仅校验场景不传 domain 参数**，默认扫描全部领域。传 domain 只缩小"文件与锚点"的检查范围；`id` 全局唯一、`id` 前缀与领域归属一致、`catalog.json` 与实际领域双向一致这三项**始终按全局判定**。

需要健康报告（记录数、`kind`/`level` 分布、规范文件标题索引覆盖率、孤儿文件）时加 `--audit`：

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" --audit
```

- 输出 `OK: 共检查 N 条记录，未发现问题` → 继续 Step 6。
- 输出非零退出码 + 问题列表 → 逐条修复，修复后重新运行本命令，直到 `OK`。常见问题：

| 问题类型 | 典型原因 |
|---|---|
| `anchor 未在 ... 中找到匹配标题` | 锚点文本与实际标题不完全一致（大小写、标点、编号） |
| `file 不存在` / `file 越出领域目录` | 路径漏了 `rules/` / `reference/` 前缀，或用了 `../` 跨领域 |
| `重复 id` | 与其他领域的条目冲突（全局唯一） |
| `id 不符合 ... 格式` | 中段不是两位数字或 `ref`，或 slug 含大写/下划线 |
| `缺少必填字段` / `非法 level` | 索引行漏字段或枚举拼错 |
| `孤儿文件未被索引引用` | 新建了 Markdown 但未登记索引 |
| `领域未登记到 catalog.json` | 新建领域后忘记同步 `catalog.json` |

## Step 6：同步版本号与 CHANGELOG（新增/修改/迁移场景，仅校验场景跳过）

判断本次变更的版本升级级别：

| 变更类型 | 版本升级 |
|---|---|
| 新增领域、新增规范条目、新增 reference 条目 | Minor `x.X.x` |
| 修改已有规范/reference 内容、修正索引、文档优化 | Patch `x.x.X` |
| 删除领域、删除规范条目、规范措辞产生不兼容语义变化（如 SHOULD 改 MUST） | Major `X.x.x` |

用 Edit 更新 `knowledge-base/README.md` 顶部 `> 版本：x.x.x`，并在 `knowledge-base/CHANGELOG.md` 顶部追加对应版本条目（格式同 skill CHANGELOG：`## [版本号] - YYYY-MM-DD` + `### Added`/`Changed`/`Removed`/`Fixed`，只写实际发生的类别）。

## Step 7：提交

涉及本仓库任何 git 提交或推送时，一律走 `commit-cc-plugin` skill，不自行执行 git 工作流——这与仓库根 `AGENTS.md` 的强制要求一致，`knowledge-base/` 的文档属性不构成例外。本 skill 只负责把正文、索引、版本号与 CHANGELOG 改到位，改完把提交交给 `commit-cc-plugin`。

## 失败处理

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| `check_index.py` 报 `id` 重复 | 检查是否误用了已存在的 id 命名规则，改用更具体的 slug | 若确认是历史遗留重复，两条记录都需人工核对哪条是权威版本，不能随意删一条了事 |
| `check_index.py` 报 anchor 不匹配 | 打开目标文件确认标题文字的准确文本（含大小写、标点），更新索引 `anchor` 字段 | 若目标章节确实还不存在，先在正文补齐该章节标题，再回填索引 |
| `check_index.py` 报孤儿文件 | 判断该文件是新建待登记（补索引行）还是应删除的残留（确认后删） | 若该文件有意不登记索引，说明它不属于 `rules/`/`reference/` 分类，与用户确认其归属 |
| `check_index.py` 报领域未登记到 `catalog.json` | 在 `catalog.json` 的 `domains` 追加该领域记录，`categories` 只填实际存在的分类目录 | 若该目录不应作为知识库领域（如误建），删除其 `index.jsonl` 或整个目录 |
| 新建领域但用户未提供该领域的规范级别定义 | 参照 `knowledge-base/csharp/00-README.md` 的"规范级别"章节直接复用同一套 MUST/SHOULD/MAY 定义，无需重新设计 | 若用户希望该领域有不同的级别体系，先与用户确认具体差异再落地 |
