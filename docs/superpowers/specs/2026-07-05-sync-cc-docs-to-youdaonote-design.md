# sync-cc-docs-to-youdaonote Skill 设计文档

**日期：** 2026-07-05
**状态：** 已批准

---

## 概述

设计一个 Claude Code skill，按用户指定的 Claude Code 官方文档分类路径（如"使用ClaudeCode构建 / Guides"），从站点导航目录 `docs/claude_docs/catalog.md` 中核实该分类是否存在；存在则抓取翻译该分类下的所有页面并保存到本地 `docs/claude_docs/`，再通过有道云笔记 CLI 同步上传，文件夹层级与网站的 Tab/分组结构保持一致，最内层为具体的中文 Markdown 笔记。

背景：`catalog.md` 已通过 Playwright 实测抓取站点侧边栏得到（8 个顶级 Tab、150+ 页面），记录在 `docs/claude_docs/catalog.md`。此前已手动完成 5 篇文档的抓取翻译与上传，本 skill 用于把这套流程固化成可重复执行的操作。

---

## 定位

**存放位置：** `.claude/skills/sync-cc-docs-to-youdaonote/SKILL.md`

分类依据：这是仅服务于本仓库、绑定特定有道云笔记账号（文件夹 ID 硬编码）的个人工作流，不具备跨账号可移植性，因此不作为 marketplace 插件分发，归入项目级 skill。

**版本管理：** 尽管落在 `.claude/` 下，仍强制遵循与 `plugins/` 下 skill 一致的独立语义版本规则——SKILL.md frontmatter 维护 `version` 字段，同步维护 `CHANGELOG.md`，新增功能 Minor、修复 Patch、破坏性变更 Major。初始版本 `1.0.0`。此规则不涉及 `.claude-plugin/marketplace.json` 的联动升级（该文件仅追踪 `plugins/` 下的变更）。

**触发词：** "保存 <分类路径> 文档"、"同步 <分类路径> 到有道笔记"，分类路径格式为 `<Tab 名> / <分组名>`（中英文均可，如"使用ClaudeCode构建 / Guides"或"Build with Claude Code / Guides"）。

**依赖：**
- `docs/claude_docs/catalog.md`（站点导航目录，本 skill 只读取，不负责生成/更新——若 catalog.md 本身过期需要重新抓取，需另外触发 Playwright 抓取流程）
- `unipus-office-plugin:web-to-markdown` skill 已有的抓取/翻译/校验约定（三级降级抓取、Read+Write 翻译、`post_process.py`、`verify.py`、`verify_quality.py`）——本 skill 直接复用这套流程逐篇执行，不重新实现
- `youdaonote-skill`（用户级全局 skill，提供 `youdaonote` CLI：`list`、`mkdir`、`save`）

---

## 组件

```
.claude/skills/sync-cc-docs-to-youdaonote/
├── SKILL.md                  # 编排指令
├── CHANGELOG.md
├── folder-map.json           # 持久化映射表（英文名 ↔ 中文名 ↔ 有道文件夹ID ↔ 已同步页面的 fileId）
└── scripts/
    └── resolve_category.py   # 子命令：resolve / get-folder
```

### `folder-map.json` 数据结构

```json
{
  "tabs": {
    "使用ClaudeCode构建": {
      "en": "Build with Claude Code",
      "id": "WEBb2aab5b9ec63445b0c0d299e3b36b96e",
      "groups": {
        "Guides": {
          "en": "Guides",
          "zh": "指南",
          "id": "WEB...",
          "pages": {
            "/large-codebases": {
              "title": "large-codebases.md",
              "fileId": "441DB6F8881F4B7FA5FFD70C73DE452D"
            }
          }
        }
      }
    }
  }
}
```

- 顶层以中文 Tab 名为 key，同时记录对应英文名（`en`），便于用户用中英文任一名称触发
- 分组（`groups`）同样中英文双记录，`id` 为空表示分组文件夹尚未创建
- `pages` 以页面的站点相对路径（如 `/large-codebases`）为 key，记录标题与上传后得到的 `fileId`，作为幂等判重的依据

### `resolve_category.py` 子命令

| 子命令 | 用途 |
|---|---|
| `resolve <tab> <group>` | 解析 `catalog.md`（支持中文名回查 `folder-map.json` 别名），返回该分组下的页面清单（标题 + 相对 URL）。未找到对应标题时非零退出并打印原因 |
| `get-folder <tab> <group> [--zh-name <中文名>]` | 查 `folder-map.json`；Tab/分组文件夹 ID 缺失则调用 `youdaonote mkdir` 创建并写回。若目标层级（Tab 或分组）尚无中文名记录，`--zh-name` 为必填——由我（Claude）先把英文名翻译好，作为参数传入；已有记录时忽略该参数直接复用。返回分组文件夹 ID |

不设 `check-exists` 子命令——幂等判重逻辑由 SKILL.md 编排（见执行流程 Step 4），因为需要交叉验证远端实际列表，属于一次性、按分组执行的逻辑，没必要固化成独立脚本子命令。

---

## 执行流程

以"使用ClaudeCode构建 / Guides"为例：

### Step 1 — 解析分类

调用 `resolve_category.py resolve "使用ClaudeCode构建" "Guides"`。

- 未在 `catalog.md` 中找到对应 Tab/分组标题 → 立即停止，告知用户"未找到该分类，请检查名称，或该分类可能需要重新抓取站点导航更新 catalog.md"，不做任何后续操作
- 找到 → 得到该分组下的页面清单（标题 + 相对 URL）

### Step 2 — 定位/创建有道文件夹

调用 `resolve_category.py get-folder "使用ClaudeCode构建" "Guides"`。

- Tab 级文件夹 ID 已记录 → 直接复用
- 分组级文件夹 ID 未记录 → 我先将英文分组名翻译为中文（如"Guides" → "指南"），作为 `--zh-name` 参数传给脚本；脚本据此调用 `youdaonote mkdir` 在 Tab 文件夹下创建，并把新 ID 与中文名写回 `folder-map.json`
- 文件夹创建失败（CLI 报错、网络问题等瞬时错误）→ 重试一次，仍失败则整个分组判定失败，不处理该分组下任何页面

### Step 3 — 拉取远端实际列表（交叉验证用）

用 `youdaonote list -f <分组文件夹ID>` 拉取该文件夹当前实际存在的笔记，得到一份 `fileId` 集合。每个分组只发一次此请求，不随页面数量线性增加请求次数。

### Step 4 — 逐篇处理（幂等 + 不阻断）

对 Step 1 得到的每一篇页面：

1. 查 `folder-map.json` 中该页面（按相对 URL）是否记录 `fileId`
   - **有记录，且该 `fileId` 出现在 Step 3 的远端列表中** → 确认已同步，跳过
   - **有记录，但该 `fileId` 不在远端列表中**（用户手动删除过）→ 判定记录过期，按未同步处理
   - **无记录** → 按未同步处理
2. 未同步的页面，走完整流程：抓取（markitdown 三级降级）→ 翻译落盘到 `docs/claude_docs/`（沿用现有平铺放置习惯）→ `post_process.py` 补链接修表格 → `verify.py` + `verify_quality.py` 两轮核对 → `youdaonote save --file` 上传到目标文件夹
3. 上传成功 → 把返回的 `fileId` 写回 `folder-map.json` 对应页面条目（覆盖过期记录）
4. 任一环节失败（抓取/翻译/校验/上传）→ 记录该篇失败原因，继续处理下一篇，不阻断整个分组

### Step 5 — 汇总报告

```
✓ 已同步 N 篇
⏭ 已跳过 N 篇（本地+远端均确认存在）
↻ 重新同步 N 篇（本地记录已失效）
✗ 失败 N 篇（附原因）
```

---

## 边界情况与错误处理

| 情况 | 处理方式 |
|---|---|
| 分类不存在于 `catalog.md` | 立即停止，不创建任何文件夹，提示用户核对名称或重新抓取导航 |
| 有道文件夹创建失败 | 重试一次，仍失败则整个分组判定失败，不处理任何页面 |
| 单篇抓取/翻译/上传失败 | 记录失败原因，继续处理下一篇，不阻断 |
| 本地记录 `fileId` 但远端已被手动删除 | 判定记录过期，按未同步重新处理，上传后覆盖旧记录 |
| `folder-map.json` 不存在 | 首次运行自动初始化空结构 |
| `folder-map.json` 存在但 JSON 解析失败 | 报错并停止，不静默用空结构覆盖（避免丢失历史映射） |

---

## 校验与测试

- 抓取/翻译环节复用 `web-to-markdown` 已有的两轮核对（`verify.py` 结构数量、`verify_quality.py` 段落/链接/图片），不新增校验逻辑
- `resolve_category.py` 冒烟测试：对现有 `catalog.md` 跑 `resolve "使用ClaudeCode构建" "Guides"`，确认能正确返回 `large-codebases` 这一篇，作为最基本的正确性验证

---

## 不在范围内

- **不支持一次处理整个 Tab**（如"使用ClaudeCode构建"下全部 8 个分组）——只支持"Tab / 单个分组"这一级粒度，需要多个分组时手动多次触发
- **不负责迁移历史遗留文件**——"使用ClaudeCode构建"文件夹下现存的 7 篇摊平文档（goal.md、scheduled-tasks.md 等）由用户手动归位到 Automation/Guides 子文件夹后再启用本 skill，不在本 skill 处理范围内
- **不负责维护/更新 `catalog.md`**——若站点导航发生变化需要重新抓取，属于另一个独立流程（此前通过 Playwright 手动完成），本 skill 只读取现有 catalog.md
- **不做 marketplace 分发**——文件夹 ID 等配置绑定特定个人账号，不具备跨用户可移植性
