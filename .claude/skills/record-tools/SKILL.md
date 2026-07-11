---
name: record-tools
description: 将工具/资源（CLI、MCP、Agent、Skill、Plugin等）的信息抓取整理并归档到仓库根目录 tools.md，自动判断分类、检测重复。触发词："记录这个工具"、"整理进tools.md"、"归档这个CLI/MCP"、"catalog this tool"、"把这个加到工具清单"。
metadata:
  version: "1.0.0"
  author: desktop client team
compatibility: 优先使用 playwright-cli（通过 npx 调用，需 Node.js 环境）抓取网页；不可用时降级为 WebFetch。写入目标固定为仓库根目录 tools.md。
allowed-tools: Bash WebFetch Read Edit Write
---

# record-tools

将工具/资源的信息抓取、整理并归档到仓库根目录 `tools.md`，按现有分类（Skill/MCP/CLI/Agent/Plugin）自动归入，写入前检测重复。

## Workflow

**Step 1 — 获取输入**
用户提供一个 URL，或直接粘贴/描述工具信息。若两者都没有，问用户：
> "请提供工具的官网/文档链接，或直接粘贴该工具的介绍内容。"

**Step 2 — 抓取内容**（仅当输入是 URL 时）
输入：Step1 获得的 URL
输出：页面原始内容（用于 Step3 提取）

1. 优先用 playwright-cli 抓取（能处理 JS 渲染的 SPA 页面）：
   ```bash
   npx playwright-cli open <url>
   ```
   打开后读取生成的 snapshot yml 文件提取内容，用完执行：
   ```bash
   npx playwright-cli close
   ```
2. 若 playwright-cli 不可用（如 `npx --no-install playwright-cli --version` 报错）或抓到的内容明显为空/异常，降级改用 WebFetch 抓取同一 URL。

**Step 3 — 提取结构化信息**
输入：Step2 抓到的页面内容
输出：结构化字段——名称 / 网址 / 简介 / 核心能力（bullet列表）/ 安装方式（如适用，不适用则省略该项）/ 备注（可选，若与本仓库现有 skill/MCP 有直接关联需指出）

**Step 4 — 读取 tools.md，检查重复**
输入：Step3 提取的名称/网址 + `tools.md` 现有内容
输出：是否存在重复条目的判定

🔴 **CHECKPOINT**：按名称或网址匹配到 `tools.md` 中已有条目时，必须停下询问用户：
> "tools.md 中已存在「{名称}」的条目，是要更新为最新信息、跳过本次归档，还是仍要新增（可能造成重复）？"

未收到用户明确选择前，不得写入。

**Step 5 — 判定分类**
输入：Step3 提取的信息 + `tools.md` 现有的 `## Skill`/`## MCP`/`## CLI`/`## Agent`/`## Plugin` 五个分类
输出：确定该工具应归入的分类

🔴 **CHECKPOINT**：判断不确定、或该工具明显不属于任何现有分类时，必须停下询问用户：
> "这个工具不确定归入哪个分类（Skill/MCP/CLI/Agent/Plugin），你希望归入哪一类，还是新建一个分类？"

不得凭猜测强行塞进某个分类。

**Step 6 — 格式化并写入**
输入：Step3 结构化信息 + Step5 确定的分类
输出：写入 `tools.md` 对应分类下的完整条目

格式模板（三级标题 + 加粗字段标签的 bullet 列表）：

```markdown
### {工具名}

- **网址**：{URL}
- **简介**：{一段话简介}
- **核心能力**：
  - {能力点1}
  - {能力点2}
- **安装方式**：{如适用}
- **备注**：{可选，如与本仓库现有 skill/MCP 的关联}
```

**Step 7 — 展示改动，不自动提交**
输入：Step6 写入后的完整条目
输出：向用户展示本次新增/更新的条目内容

只展示改动内容供确认；是否提交推送需用户显式要求（说"提交"触发 `commit-cc-plugin`），不得在本 skill 内擅自调用提交流程。

## 异常处理

| 触发条件 | 处理方式 |
|---------|---------|
| URL 不可达/404 | 🔴 **STOP**——报告具体错误信息，请用户确认链接是否正确，或改为直接粘贴介绍内容 |
| playwright-cli 和 WebFetch 都抓不到有效内容（页面为空/内容明显不完整） | 🔴 **STOP**——请用户手动粘贴关键信息，不得凭训练知识/常识杜撰简介或核心能力 |
| tools.md 中已存在同名/同网址条目 | 🔴 **STOP**——见 Step 4 |
| 新工具不属于现有5个分类 | 🔴 **STOP**——见 Step 5 |
| tools.md 文件不存在 | 创建文件并写入 `## Skill`/`## MCP`/`## CLI`/`## Agent`/`## Plugin` 五个分类骨架，再写入新条目 |

## Red Flags

| 错误做法 | 正确做法 |
|---------|---------|
| 抓不到页面内容时凭常识/训练知识编造简介或核心能力 | 抓取失败必须 STOP 并如实告知，不得杜撰 |
| 不检查重复直接追加，导致 tools.md 出现同一工具的多条记录 | 写入前必须检查重复（Step 4） |
| 分类判断不确定时随意塞进第一个看着还行的分类 | 拿不准就停下问用户，不得强行分类 |
| 写完直接调用 commit-cc-plugin 自动提交 | 只展示改动，提交与否由用户明确决定（Step 7） |
| 用 sed/正则等方式批量改写 tools.md 全文 | 只在目标分类下追加/更新单个条目，不触碰其他分类和条目 |
