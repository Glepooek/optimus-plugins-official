---
name: sync-cc-docs-to-youdaonote
description: >
  按分类路径（如"使用ClaudeCode构建 / Guides"）核对 docs/claude_docs/catalog.md，
  抓取翻译该分类下的 Claude Code 官方文档页面，幂等同步到有道云笔记，文件夹层级
  与站点导航一致。触发词："保存 <分类路径> 文档"、"同步 <分类路径> 到有道笔记"。
metadata:
  version: "1.2.0"
  author: desktop client team
compatibility: 需要 Python 运行时（含 markitdown 包）；需要已配置账号的 youdaonote CLI；依赖同仓库 optimus-office-plugin:web-to-markdown skill 完成抓取翻译流程。
allowed-tools: Bash Read Edit Write Task
---

# sync-cc-docs-to-youdaonote

将 Claude Code 官方文档站点（code.claude.com/docs/en）按 Tab/分组分类，抓取翻译
后同步到有道云笔记，文件夹层级与站点导航一致。

## 前置条件

- **外部依赖**：`docs/claude_docs/catalog.md`（站点导航快照）必须已存在（首次通过
  Playwright 抓取站点导航得到）。它不属于本 skill 的私有数据——与它索引的实际文档树
  `docs/claude_docs/<Tab中文名>/<group_zh>/` 同级存放，供人浏览时目录和内容一目了然。
  本 skill 平时只读取；仅当 Step 0 检测到已超过 14 天未核对、且用户明确同意时，才会
  重新核对并在用户确认 diff 后更新它——不做无提示的自动抓取或自动覆写。本 skill 自身
  的私有状态（有道文件夹映射、核对时间戳）统一存放在 `.claude/skills/sync-cc-docs-to-youdaonote/data/`
- 依赖 `youdaonote-skill`（用户级全局 skill）提供的 `youdaonote` CLI

## 使用方式

用户说"保存 <Tab 名> / <分组名> 文档"，分类路径中英文均可，如：
- "保存 使用ClaudeCode构建 / Guides 文档"
- "保存 Build with Claude Code / Guides 文档"

只支持"Tab / 单个分组"这一级粒度，不支持一次处理整个 Tab。

## 执行流程

### Step 0 — 核对 catalog.md 是否过期

0. 防御性清理：若 `data/.catalog-staging.md` 存在（上次异常中断残留），直接删除，不读取内容。

1. 运行：

   ```bash
   python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/catalog_freshness.py" check-freshness --threshold-days 14
   ```

   - exit 0（`fresh` 或 `recently_prompted`）→ 跳过本 Step，直接进入 Step 1
   - exit 1（`stale` 或 `never_checked`）→ 读 stdout JSON，向用户提问：
     > "距离上次核对 Claude Code 文档站点导航结构已经 `<days_since_verified>` 天（阈值 14
     > 天）。是否要花几分钟重新核对站点导航结构？（预计 5–15 分钟，需逐个访问 8 个 Tab
     > 并展开手风琴子菜单）"
   - exit 2 → 🔴 **报错停止**，`catalog-check-meta.json` 损坏，告知用户手动检查该文件

2. **用户回答"否"**：

   ```bash
   python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/catalog_freshness.py" record-check --result declined
   ```

   继续 Step 1（本次仍用现有 catalog.md）。

3. **用户回答"是"**：进入抓取流程。

   a. 用 playwright-cli，对 catalog.md 当前记录的 8 个 Tab 逐一导航到入口 URL，从
      `#sidebar` 提取 `h3` 分组标题及 `<a>` 链接（手风琴折叠子菜单需先点击展开，参照
      catalog.md 顶部"抓取方式"说明）。

      - 单个 Tab 核实失败（超时/DOM 结构异常）→ 重试一次；仍失败 → 该 Tab **不阻断其余
        Tab**，把 catalog.md 中该 Tab 原有区块原样搬到候选新文本里，并在其 `## Tab` 行
        后插入 `<!-- unverified: <失败原因> -->` 标记行
      - **8 个 Tab 全部核实失败**（网络/浏览器不可用等更高层故障）→ 不写 staging 文件、
        不做 diff，运行：
        ```bash
        python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/catalog_freshness.py" record-check --result failed
        ```
        告知用户"本次核对失败，沿用现有 catalog.md"，继续 Step 1。

   b. 将完整候选新文本写入 `.claude/skills/sync-cc-docs-to-youdaonote/data/.catalog-staging.md`。

   c. 运行：

      ```bash
      python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/catalog_freshness.py" diff-catalog --new ".claude/skills/sync-cc-docs-to-youdaonote/data/.catalog-staging.md"
      ```

      - exit 2 → 🔴 停止，删除 staging 文件，告知用户
      - exit 0（无差异）：
        ```bash
        python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/catalog_freshness.py" record-check --result verified --unverified-tabs "<本轮标记为 unverified 的 Tab，逗号分隔，可为空>"
        ```
        删除 staging 文件，告知用户"核对完成，导航结构无变化"，继续 Step 1。
      - exit 1（有差异）：将 diff JSON 转述为易读报告（新增/删除/移动/改名的 Tab/分组/
        页面）。若 `pages_removed` 中有 `had_synced_record: true` 的条目，需在报告里
        提示"该页面在 folder-map.json 中仍有有道笔记同步记录（fileId=...），本功能不会
        自动处理有道笔记侧，如需一并清理请手动处理"。若 `tabs_added`/`tabs_removed`
        非空，需额外提醒这是"顶级 Tab 结构变化"，比普通页面级改动更重大，请用户格外
        确认。然后询问用户是否应用这份 diff：
        - **拒绝**：
          ```bash
          python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/catalog_freshness.py" record-check --result declined --unverified-tabs "<...>"
          ```
          不覆写 catalog.md，删除 staging 文件，继续 Step 1（仍用旧 catalog.md）。
        - **同意**：
          ```bash
          python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/catalog_freshness.py" apply-diff --new ".claude/skills/sync-cc-docs-to-youdaonote/data/.catalog-staging.md" --write
          ```
          成功后运行：
          ```bash
          python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/catalog_freshness.py" record-check --result verified --unverified-tabs "<...>"
          ```
          删除 staging 文件，把 apply-diff 返回的摘要（新增/删除/未核实的 Tab 列表）
          告知用户，并提示"如需回滚可用 `git diff` / `git checkout` 查看改动"。继续
          Step 1——注意：由于分类结构可能已变化（尤其是本次要同步的 Tab/分组本身可能
          被改名/移动），Step 1 的 `resolve` 仍按用户原话执行；如果因改名而找不到，按
          Step 1 现有的"分类不存在"报错路径处理，提示用户按报错信息里的新名字重新说
          一次。

### Step 1 — 解析分类

```bash
python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" resolve "<Tab名>" "<分组名>"
```

- 非零退出 → 🔴 **立即停止**，将 stderr 的错误信息转告用户，不做任何后续操作
- 成功 → 得到 JSON：`{"tab_en", "tab_zh", "group_en", "pages": [{"title", "url"}]}`

### Step 2 — 定位/创建有道文件夹

若 `tab_zh` 为 `null`（catalog.md 未标注该 Tab 的中文名），使用用户输入的中文 Tab 名作为 `<Tab中文名>`；否则直接用 `tab_zh`。

```bash
python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" get-folder "<Tab中文名>" "<group_en>"
```

- 若报错"尚无中文名记录，必须提供 --group-zh"：将 `group_en`（英文分组名）翻译为
  中文（简短、贴合含义，如 "Guides" → "指南"），加上 `--group-zh "<译名>"` 重跑：

  ```bash
  python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" get-folder "<Tab中文名>" "<group_en>" --group-zh "<译名>"
  ```

- 命令因网络等瞬时错误失败 → 重试一次，仍失败则 🔴 **整个分组判定失败**，停止，告知用户
- 成功 → 得到分组文件夹 ID（记为 `<GROUP_ID>`）

### Step 3 — 拉取远端实际列表（每分组一次，供幂等交叉验证）

```bash
youdaonote -s ydn list -f <GROUP_ID>
```

记录输出中每一行 `📄 <fileId>\t<title>` 的 `fileId` 集合，供 Step 4 交叉验证。

### Step 4 — 逐篇处理

用 Read 工具读取 `.claude/skills/sync-cc-docs-to-youdaonote/data/folder-map.json`，定位
`tabs[<Tab中文名>].groups[<group_en>].pages` 这个字典。

**本地存储路径**：`docs/claude_docs/<Tab中文名>/<group_zh>/`
- `<Tab中文名>`：来自 Step 1 的 `tab_zh`
- `<group_zh>`：优先使用 folder-map.json 中记录的中文名；若无则翻译 `group_en`（如 "Guides" → "指南"）
- 目录不存在时自动创建

对 Step 1 返回的每一篇页面（`title` + `url`）：

1. 查 `pages[<url>]` 是否有记录的 `fileId`：
   - **有记录，且该 `fileId` 出现在 Step 3 拉取的远端列表中** → 已同步，跳过，计入"已跳过"
   - **有记录，但不在远端列表中**（用户手动删除过）→ 记录已过期，按未同步处理
   - **无记录** → 按未同步处理
2. 未同步的页面，先完成"抓取 + 翻译"（这部分需要 LLM 判断，走
   `optimus-office-plugin:web-to-markdown` skill 已有约定，不可脚本化）：
   - 创建本地目录：`mkdir -p docs/claude_docs/<Tab中文名>/<group_zh>`
   - `python -m markitdown "https://code.claude.com/docs/en<url>" > docs/claude_docs/<Tab中文名>/<group_zh>/.raw-<slug>.md`（三级降级见 web-to-markdown SKILL.md）
   - Read 原文 → 翻译（剥离站点通用 Documentation Index 横幅、`<Note>`/`<Tip>` 转引用块）→ Write 到 `docs/claude_docs/<Tab中文名>/<group_zh>/<slug>.md`

   译文产出后，剩下全是确定性步骤，**一律调用 `finalize_page.py` 一次性完成**，不要手动
   逐条执行 post_process/verify/verify_quality/上传/更新 folder-map.json/清理临时文件——
   手动执行时最容易漏掉的正是"清理临时文件"和"更新 folder-map.json"这两步：

   ```bash
   python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/finalize_page.py" \
     --raw "docs/claude_docs/<Tab中文名>/<group_zh>/.raw-<slug>.md" \
     --translated "docs/claude_docs/<Tab中文名>/<group_zh>/<slug>.md" \
     --group-id "<GROUP_ID>" \
     --tab-zh "<Tab中文名>" \
     --group-en "<group_en>" \
     --url "<url>" \
     --base-url "https://code.claude.com/docs"
   ```

   脚本内部依次执行：post_process.py 后处理 → verify.py 结构核对 → verify_quality.py
   内容质量核对 → `youdaonote save` 上传 → 更新 `folder-map.json` 的 `pages[<url>]` →
   删除 `.raw-<slug>.md`。任一环节失败会原样退出非零码并打印失败原因，**且不会**清理
   raw 文件或更新 folder-map.json（保留现场供排查、避免下次误判为"已同步"）。

   - exit 0 → stdout 是 JSON（含 `fileId`/`title`），该篇视为同步成功
   - 非零退出 → 该篇视为失败，转到下面第 3 点处理；**不要**手动重跑脚本内部的某一个
     子步骤，脚本已经在失败点原地停止，直接看报错信息定位问题、修正后整个脚本重跑一遍
3. 任一环节失败（抓取/翻译，或 `finalize_page.py` 非零退出）→ 记录该篇失败原因，
   **继续处理下一篇**，不阻断
   - ⚠️ **注意**：单篇失败不阻断，但需记录失败原因供汇总报告

### Step 5 — 汇总报告

```
✓ 已同步 N 篇
⏭ 已跳过 N 篇（本地+远端均确认存在）
↻ 重新同步 N 篇（本地记录已失效）
✗ 失败 N 篇（附原因）
```

## 边界情况

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 分类不存在于 catalog.md | 报错信息附模糊匹配候选名（`resolve_category.py` 内置 `difflib` 提示），按提示核对 | 🔴 **立即停止**，不创建任何文件夹 |
| 有道文件夹创建失败 | 重试一次（等待 1 秒） | 🔴 **整个分组判定失败**，停止并告知用户 |
| 单篇抓取失败 | 检查 URL 是否有效 | 记录失败原因，继续下一篇 |
| 单篇翻译失败 | 检查原文是否为空 | 记录失败原因，继续下一篇 |
| `finalize_page.py` 内某一步失败（post_process/verify/verify_quality/上传） | 看脚本打印的失败原因定位问题，修正后整个脚本重跑一遍 | 记录失败原因，继续下一篇；不清理 raw 文件、不更新 folder-map.json |
| `finalize_page.py` 上传后未在目标目录发现新增笔记 | 检查网络/账号权限，`youdaonote list` 手动核实 | 报错退出，不更新 folder-map.json，不清理 raw 文件 |
| `finalize_page.py` 上传后目标目录同时新增了多篇笔记（无法唯一确定 fileId） | 检查是否有并发写入/其他进程也在同一目录上传 | 报错退出并列出所有新增 fileId，需人工核实后手动处理 |
| 本地记录 fileId 但远端已被手动删除 | 判定过期，按未同步处理 | 重新同步并覆盖记录 |
| folder-map.json 不存在 | 首次运行自动初始化为 `{"tabs": {}}` | - |
| folder-map.json 解析失败 | 检查文件是否损坏 | 🔴 **报错停止**，不静默覆盖 |
| catalog-check-meta.json 解析失败 | 检查文件是否被手动改坏 | 🔴 **报错停止**，不静默重置 |
| 单 Tab 核实失败（超时/DOM 结构异常） | 重试一次 | 标记 `unverified`，原样保留旧内容，不阻断其余 Tab |
| 8 个 Tab 全部核实失败 | 检查 playwright-cli/网络 | 🔴 放弃本轮核对，`record-check --result failed`，沿用旧 catalog.md |
| 抓取到的 Tab 数量与 catalog.md 记录的对不上 | 按抓取结果生成候选区块 | diff 报告显式标注"顶级 Tab 结构变化"，需用户格外确认 |
| staging 文件解析出 0 个 Tab | 检查抓取内容是否完整 | 🔴 `diff-catalog`/`apply-diff` exit 2，不进入询问用户的分支 |
| 被删除页面在 folder-map.json 有同步记录 | diff 报告提示对应 fileId | 仅提示，不自动处理有道笔记侧 |
| `apply-diff` 写入中途失败 | temp 文件 + `os.replace` 原子写入，catalog.md 本体不会损坏 | 🔴 报错停止，清理残留 `.tmp` 文件 |
| `data/.catalog-staging.md` 因上次异常中断残留 | Step 0 开始时无条件删除，不读取内容 | - |

## 不在范围内

- 不支持一次处理整个 Tab
- 不负责迁移历史遗留文件
- 不做 marketplace 分发
- catalog.md 的重新核对**只在 Step 0 阈值到期且用户明确同意时触发**，不做定时任务/
  后台自动刷新；已核实 Tab 内部的多条差异只能整份 diff 一起接受或拒绝，不支持逐条目
  筛选

## 反模式与危险操作（不要做什么）

| # | 反模式 | 为什么不要做 | 正确做法 |
|---|--------|-------------|----------|
| 1 | **跳过 Step 3 直接上传** | 无法检测远端已存在的文件，导致重复 | 必须先拉取远端列表进行交叉验证 |
| 2 | **静默覆盖 folder-map.json** | 丢失历史同步记录，破坏幂等性 | 只在上传成功后更新 `pages[<url>]` |
| 3 | **单篇失败时中断整个分组** | 一篇失败导致其他页面无法同步 | 记录失败原因，继续下一篇 |
| 4 | **不检查 catalog.md 就创建文件夹** | 可能创建不存在的分类结构 | 先 resolve 确认分类存在 |
| 5 | **忽略 folder-map.json 解析错误** | 静默覆盖会丢失所有历史记录 | 🔴 报错停止，不自动修复 |
| 6 | **重试时不等待** | 网络瞬时错误可能未恢复 | 重试前短暂等待（如 1 秒） |
| 7 | **未经用户确认直接抓取/覆写 catalog.md** | 违反"不做无提示自动抓取"的决策，抓取耗时较长会打断用户 | Step 0 先问是否愿意花时间核对，用户明确同意后才抓取 |
| 8 | **diff 有变化时自动合并覆写** | 违反"不自动合并覆写"的决策，静默改动人工维护的分类结构风险高 | 生成 diff 报告，等待用户确认后才调用 `apply-diff --write` |
| 9 | **用"parse → 重新序列化"方式重建 catalog.md** | 会丢失 `[x]`/`[ ]` 之外的行尾批注、Tab/分组标题的备注文字等未被正则捕获的细节 | `apply-diff` 以 `(tab_en, url)` 为 key 复用旧文件原始整行文本，仅新增页面时才生成全新文本 |
| 10 | **某个 Tab 抓取失败就放弃整轮核对** | 一个 Tab 失败不该阻断其余 7 个 Tab 的核对结果 | 该 Tab 标记 `unverified` 并原样保留，其余 Tab 正常参与 diff |
| 11 | **`finalize_page.py` 失败后手动重跑内部某一个子步骤（如只重跑 verify.py）** | 绕开脚本的失败即停止语义，容易在 folder-map.json/清理文件状态上留下不一致 | 修正问题后把整个 `finalize_page.py` 命令重跑一遍，脚本内部会从 post_process 开始完整重来 |
