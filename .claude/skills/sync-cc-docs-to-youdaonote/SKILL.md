---
name: sync-cc-docs-to-youdaonote
description: >
  按分类路径（如"使用ClaudeCode构建 / Guides"）核对 docs/claude_docs/catalog.md，
  抓取翻译该分类下的 Claude Code 官方文档页面，幂等同步到有道云笔记，文件夹层级
  与站点导航一致。触发词："保存 <分类路径> 文档"、"同步 <分类路径> 到有道笔记"。
metadata:
  version: "1.0.2"
---

# sync-cc-docs-to-youdaonote

将 Claude Code 官方文档站点（code.claude.com/docs/en）按 Tab/分组分类，抓取翻译
后同步到有道云笔记，文件夹层级与站点导航一致。

## 前置条件

- `docs/claude_docs/catalog.md` 必须已存在（通过 Playwright 抓取站点导航得到，
  本 skill 只读取，不负责生成或更新）
- 依赖 `youdaonote-skill`（用户级全局 skill）提供的 `youdaonote` CLI

## 使用方式

用户说"保存 <Tab 名> / <分组名> 文档"，分类路径中英文均可，如：
- "保存 使用ClaudeCode构建 / Guides 文档"
- "保存 Build with Claude Code / Guides 文档"

只支持"Tab / 单个分组"这一级粒度，不支持一次处理整个 Tab。

## 执行流程

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

用 Read 工具读取 `.claude/skills/sync-cc-docs-to-youdaonote/folder-map.json`，定位
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
2. 未同步的页面，完整走一遍 `optimus-office-plugin:web-to-markdown` skill 已有的抓取
   /翻译/校验流程：
   - 创建本地目录：`mkdir -p docs/claude_docs/<Tab中文名>/<group_zh>`
   - `python -m markitdown "https://code.claude.com/docs/en<url>" > docs/claude_docs/<Tab中文名>/<group_zh>/.raw-<slug>.md`（三级降级见 web-to-markdown SKILL.md）
   - Read 原文 → 翻译（剥离站点通用 Documentation Index 横幅、`<Note>`/`<Tip>` 转引用块）→ Write 到 `docs/claude_docs/<Tab中文名>/<group_zh>/<slug>.md`
   - `python plugins/optimus-office-plugin/skills/web-to-markdown/scripts/post_process.py "docs/claude_docs/<Tab中文名>/<group_zh>/<slug>.md" --base-url "https://code.claude.com/docs"`
   - `python plugins/optimus-office-plugin/skills/web-to-markdown/scripts/verify.py "docs/claude_docs/<Tab中文名>/<group_zh>/.raw-<slug>.md" "docs/claude_docs/<Tab中文名>/<group_zh>/<slug>.md"`
   - `python plugins/optimus-office-plugin/skills/web-to-markdown/scripts/verify_quality.py "docs/claude_docs/<Tab中文名>/<group_zh>/.raw-<slug>.md" "docs/claude_docs/<Tab中文名>/<group_zh>/<slug>.md" --base-url "https://code.claude.com/docs"`
   - 两轮核对通过后：`youdaonote -s ydn save` 上传，参数说明：
     - `contentFile`：`docs/claude_docs/<Tab中文名>/<group_zh>/<slug>.md`
     - `type`：`"md"`
     - `parentId`：`"<GROUP_ID>"`
     - `title`：译文 markdown 的第一个 `#` 标题（用 Read 工具读取译文，提取首行 `# ` 后的内容）
   - 清理 `docs/claude_docs/<Tab中文名>/<group_zh>/.raw-<slug>.md` 临时文件
3. 上传成功 → 用 Edit 工具把 `{"title": "<文档标题>", "fileId": "<返回的fileId>"}` 写入
   `folder-map.json` 的 `pages[<url>]`（覆盖过期记录）
4. 任一环节失败（抓取/翻译/校验/上传）→ 记录该篇失败原因，**继续处理下一篇**，不阻断
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
| 分类不存在于 catalog.md | 检查拼写和大小写 | 🔴 **立即停止**，不创建任何文件夹 |
| 有道文件夹创建失败 | 重试一次（等待 1 秒） | 🔴 **整个分组判定失败**，停止并告知用户 |
| 单篇抓取失败 | 检查 URL 是否有效 | 记录失败原因，继续下一篇 |
| 单篇翻译失败 | 检查原文是否为空 | 记录失败原因，继续下一篇 |
| 单篇上传失败 | 检查网络连接 | 记录失败原因，继续下一篇 |
| 本地记录 fileId 但远端已被手动删除 | 判定过期，按未同步处理 | 重新同步并覆盖记录 |
| folder-map.json 不存在 | 首次运行自动初始化为 `{"tabs": {}}` | - |
| folder-map.json 解析失败 | 检查文件是否损坏 | 🔴 **报错停止**，不静默覆盖 |

## 不在范围内

- 不支持一次处理整个 Tab
- 不负责迁移历史遗留文件
- 不负责维护/更新 catalog.md
- 不做 marketplace 分发

## 反模式与危险操作（不要做什么）

| # | 反模式 | 为什么不要做 | 正确做法 |
|---|--------|-------------|----------|
| 1 | **跳过 Step 3 直接上传** | 无法检测远端已存在的文件，导致重复 | 必须先拉取远端列表进行交叉验证 |
| 2 | **静默覆盖 folder-map.json** | 丢失历史同步记录，破坏幂等性 | 只在上传成功后更新 `pages[<url>]` |
| 3 | **单篇失败时中断整个分组** | 一篇失败导致其他页面无法同步 | 记录失败原因，继续下一篇 |
| 4 | **不检查 catalog.md 就创建文件夹** | 可能创建不存在的分类结构 | 先 resolve 确认分类存在 |
| 5 | **忽略 folder-map.json 解析错误** | 静默覆盖会丢失所有历史记录 | 🔴 报错停止，不自动修复 |
| 6 | **重试时不等待** | 网络瞬时错误可能未恢复 | 重试前短暂等待（如 1 秒） |
