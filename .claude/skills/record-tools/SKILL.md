---
name: record-tools
description: 将工具/资源（CLI、MCP、Agent、Skill、Plugin等）的信息抓取整理并归档到 knowledge-base/tools 领域，自动生成分类标签、检测重复。触发词："记录这个工具"、"归档到知识库"、"归档这个CLI/MCP"、"catalog this tool"、"把这个加到工具清单"。
metadata:
  version: "1.2.0"
  author: desktop client team
compatibility: 优先使用 playwright-cli（通过 npx 调用，需 Node.js 环境）抓取网页；不可用时降级为 WebFetch。写入目标为 knowledge-base/tools 领域（reference 条目），依赖 knowledge-base-maintain skill 的索引与版本同步机制，需本机 Python 3。
allowed-tools: Bash WebFetch Read Edit Write Grep Skill
---

# record-tools

将工具/资源的信息抓取、整理并归档到 `knowledge-base/tools` 领域，每个工具登记为一条独立的 reference 条目，用 `tags` 标注其类别（如 mcp/cli/skill/agent/plugin，不互斥），写入前检测重复。

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
输入：Step2 抓到的页面内容（若有）+ Step1 用户提供的文字描述（若有）
输出：结构化字段——名称 / 网址 / 简介 / 核心能力（bullet列表）/ 安装方式（如适用，不适用则省略该项）/ 更新方式（如适用）/ 移除方式（如适用）/ 备注（可选，若与本仓库现有 skill/MCP 有直接关联需指出）/ `tags`（该工具的类别标签，如 `mcp`/`cli`/`skill`/`agent`/`plugin`，可叠加技术栈标签如 `github`/`avalonia`，不要求互斥，一个工具可以同时打多个标签）

更新方式、移除方式与安装方式同等对待：抓取内容中若无对应说明，不得凭包管理器通用惯例（如"npm 全局包一律 npm uninstall -g"）推断填写，必须找到该工具官方文档/README 中明确写出的具体命令或步骤才可填入；找不到时该字段整项省略，不得留空占位或标注"未知"。

若用户同时提供了文字描述、且成功抓取到页面内容，两者存在实质性出入（如核心能力条数、版本定位有明显差异）时，以抓取内容为准；仅当抓取失败或降级失败（见异常处理表）时才使用用户描述兜底。以抓取内容为准不等于丢弃用户描述——若用户描述中有抓取内容未覆盖的信息（如内部使用经验、与本仓库其他工具的关联），仍需保留进"备注"字段。

**Step 4 — 读取 knowledge-base/tools，检查重复**
输入：Step3 提取的名称/网址 + `knowledge-base/tools/index.jsonl` 现有内容
输出：是否存在重复条目的判定

用 Grep 在 `knowledge-base/tools/index.jsonl` 中按名称（`title`）或网址关键词搜索——该领域全部为 `kind: reference` 条目，`knowledge-base-maintain` 的 `find_duplicates.py` 只处理 `kind: rule`，查不到这里的重复，不能依赖它。

🔴 **CHECKPOINT**：按名称或网址匹配到已有条目时，必须停下询问用户：
> "knowledge-base/tools 中已存在「{名称}」的条目（`{id}`），是要更新为最新信息、跳过本次归档，还是仍要新增（可能造成重复）？"

未收到用户明确选择前，不得写入。

**Step 5 — 确定分类标签**
输入：Step3 提取的信息
输出：该工具的 `tags` 数组

`tags` 至少包含一个类别标签（`mcp`/`cli`/`skill`/`agent`/`plugin`，或用户明确认可的新类别），可叠加技术栈/生态标签（如 `github`、`avalonia`、`playwright`）。标签不互斥、可叠加，不必强行归入单一分类。

🔴 **CHECKPOINT**：完全无法归纳出合理类别标签时，必须停下询问用户：
> "这个工具不确定归入哪个类别标签，你希望打上什么标签？"

不得凭猜测编造类别标签。

**Step 6 — 写入 knowledge-base/tools**
输入：Step3 结构化信息 + Step5 确定的 tags
输出：新增一条 reference 条目

调用 `knowledge-base-maintain` skill 完成落地，不手动操作 `index.jsonl`/`README.md`/`CHANGELOG.md`——条目落地的字段规则、版本号同步、一致性校验均由该 skill 维护，本 skill 只负责决定"写什么"（领域固定为 `tools`，`kind` 固定为 `reference`），不重复实现"怎么安全写进知识库"。调用时提供：

- 场景：新增 reference 条目
- 领域：`tools`
- 正文：Step3 提取的全部字段（简介、核心能力、安装/更新/移除方式、备注）
- `title`/`tags`/`summary`：Step3/Step5 结果

`knowledge-base-maintain` skill 不可用时，🔴 **STOP**——不得手动模拟该 skill 的写入步骤，这类内联复制会在其字段规则或校验脚本变化时静默过期。

**Step 7 — 展示改动，不自动提交**
输入：Step6 写入后的完整条目
输出：向用户展示本次新增/更新的条目内容

只展示改动内容供确认；是否提交推送需用户显式要求（说"提交"触发 `commit-cc-plugin`），不得在本 skill 内擅自调用提交流程。

## 异常处理

| 触发条件 | 处理方式 |
|---------|---------|
| URL 不可达/404 | 🔴 **STOP**——报告具体错误信息，请用户确认链接是否正确，或改为直接粘贴介绍内容 |
| playwright-cli 和 WebFetch 都抓不到有效内容（页面为空/内容明显不完整） | 🔴 **STOP**——请用户手动粘贴关键信息，不得凭训练知识/常识杜撰简介或核心能力 |
| `knowledge-base/tools/index.jsonl` 中已存在同名/同网址条目 | 🔴 **STOP**——见 Step 4 |
| 完全无法归纳出合理类别标签 | 🔴 **STOP**——见 Step 5 |
| `knowledge-base/tools/` 领域不存在 | 调用 `knowledge-base-maintain` skill 走"新建领域"流程创建骨架，再写入新条目 |
| `knowledge-base-maintain` skill 不可用 | 🔴 **STOP**——见 Step 6，不得手动模拟其写入步骤 |
| 抓取"成功"但内容明显与目标工具不符（页面标题/主体产品名与用户提供的工具名不一致，很可能是链接跳转到了错误页面、或该产品已改名/下线跳转到了别的站点） | 🔴 **STOP**——不得按抓错的内容继续填写字段。向用户说明实际抓到的页面标题/关键信息与预期不符，请用户确认链接是否正确 |

## Red Flags

| 错误做法 | 正确做法 |
|---------|---------|
| 抓不到页面内容时凭常识/训练知识编造简介或核心能力 | 抓取失败必须 STOP 并如实告知，不得杜撰 |
| 不检查重复直接追加，导致 `knowledge-base/tools` 出现同一工具的多条记录 | 写入前必须用 Grep 检查 `index.jsonl` 是否重复（Step 4） |
| 类别标签判断不确定时随意编造标签 | 拿不准就停下问用户，不得凭猜测编造标签 |
| 写完直接调用 commit-cc-plugin 自动提交 | 只展示改动，提交与否由用户明确决定（Step 7） |
| 直接手动编辑 `index.jsonl`/`README.md`/`CHANGELOG.md` 而不调用 `knowledge-base-maintain` | 落地一律通过 `knowledge-base-maintain` skill（Step 6），手动内联复制其写入步骤会在该 skill 的字段规则或校验脚本变化时静默过期 |
