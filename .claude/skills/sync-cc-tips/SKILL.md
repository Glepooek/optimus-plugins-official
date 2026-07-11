---
name: sync-cc-tips
description: 从 Claude Code 最新 changelog 自动同步 tips.txt：新增未覆盖条目、修正过时内容、删除已废弃功能，同步所有文档数字，最后调用 commit-cc-plugin 提交。触发场景：用户说 "/sync-cc-tips"、"更新tips"、"同步tips"、"tips需要更新"、"从changelog更新tips"、"sync tips"。可附带版本数量参数，如 "/sync-cc-tips 5" 表示只看最近5个版本。
metadata:
  version: "1.1.2"
  author: desktop client team
compatibility: 需要网络访问 raw.githubusercontent.com 拉取 changelog；流程末尾调用 commit-cc-plugin skill 完成提交推送。
allowed-tools: Bash WebFetch Read Edit Task
disable-model-invocation: true
---

# /sync-cc-tips

从 Claude Code 最新 changelog 全自动同步 tips.txt，无需人工干预，完成后展示摘要并提交。

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

## 第三步 — 三类差异识别

依次对 changelog 中每个功能点做判断：

### 🆕 新增条件
满足以下**全部条件**才生成新条目：
- 属于对用户操作有实质影响的功能（新 CLI flag、新子命令、新 Hook 事件、新 settings.json 设置项、新交互命令）
- 在 tips.txt **全文**中，该功能点的所有主标识符（flag 名、设置项名、命令名、环境变量名）均未命中

**识别流程**：
1. 提取该功能点的主标识符列表（如 `respondToBashCommands`、`!命令`）
2. 在已覆盖标识符集中逐一查找
3. **任一命中 → 跳过，不新增**；全部未命中 → 标记为新增

**信息补全（生成前必须执行）**：
changelog 的单行描述往往只覆盖核心功能，生成前需补充完整信息：

1. **交叉关联已有 tips** — 在 tips.txt 全文中搜索与新功能相关的已有条目，提取可关联的信息：
   - 新功能是否与已有功能形成工作流？（如「可点击附件」与「@ 引用」配合）
   - 新功能是否涉及已有命令/flag？（如「可读会话名」涉及 `-n`、`/rename`、`--resume`）
   - 新功能是否属于已有配置项的子集或扩展？

2. **提取完整参数集** — 从 changelog 原文中提取：
   - settings.json 键名（camelCase 形式）
   - 环境变量名（全大写下划线形式）
   - 支持的值/选项（如 small/medium/large、true/false）
   - 是否为建议性指引（advisory）vs 硬性限制（enforced cap）
   - 相关 CLI flag 或交互命令

3. **补全用法示例** — 为每个功能点提供完整的使用方式：
   - CLI 命令必须是完整可执行形式：`claude --xxx`
   - 配置项需给出 settings.json 键名和示例值
   - 交互命令需给出触发方式和预期结果
   - 若有多种使用方式（CLI + 交互 + 配置），全部列出

**完整性校验（生成后必须执行）**：
生成条目后，对照检查以下清单，任一项缺失则补充：

| 检查项 | 要求 |
|--------|------|
| settings.json 键名 | 配置类功能必须包含 camelCase 键名 |
| 环境变量名 | 有环境变量的功能必须包含全大写形式 |
| 版本号 | 标注引入版本（如 v2.1.196） |
| 多种用法 | 有 CLI + 交互两种方式的，全部列出 |
| 关联功能 | 与已有 tips 有配合关系的，互相引用 |
| 限制说明 | advisory vs enforced、仅 -p 模式、仅特定平台等 |

生成格式：
```
[分类] 🔰 标题\n功能：一句话说明\n效果：使用场景和收益\n例子：claude --完整命令 具体说明
```

分类从现有 11 个中选最匹配：`[交互]`、`[工具]`、`[Hook]`、`[配置]`、`[CLI]`、`[集成]`、`[工作流与自动化]`、`[排障]`、`[Skill]`、`[MCP]`、`[高级]`

### ✏️ 修改条件
以下情况原地更新已有条目（不改变条目位置）：
- 已有条目的命令语法与 changelog 不符（如 flag 名称变更）
- 已有条目描述的行为已被新版本改变
- 已有条目的例子中使用了已不存在的 flag 或子命令
- **不修改**：仅措辞差异、风格调整、无实质差异的改动

### 🗑️ 删除条件
以下情况将在第四步变更预览时列出待删条目：
- changelog 明确标注 `Removed`、`Deprecated`、`no longer available`
- 功能已被完全移除（不是"有了更好的替代"，而是彻底消失）
- **不删除**：changelog 只是新增了替代功能，旧功能仍可用

### 格式校验（每条写入前执行）
- 必须包含"功能："、"效果："、"例子："三个字段
- 例子中的命令必须是完整可执行形式：`claude --xxx`，不能只写 `--xxx`
- 每条末尾确保有 `---` 分隔符
- **如果校验不通过** → 修正后再写入，不跳过也不写入不合格条目；若无法修正则跳过该条并在摘要中注明

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| "完整性校验"清单某项在 changelog 原文中确实找不到对应信息（如未提供 settings.json 键名） | 交叉检索该功能关联的已有 tips 条目或同版本其他条目上下文推断 | 若仍无法确认，跳过该项校验并在摘要中注明"信息不全，需人工补充"，不编造数值 |
| 同一功能点同时命中🆕新增与✏️修改条件（如新 flag 替换了旧 flag 的部分行为） | 优先按✏️修改处理，原地更新旧条目，不重复新增 | 若归属仍有歧义，在变更预览中单独列出并说明歧义原因，交由用户在 CHECKPOINT 处裁决 |

### 🚦 零变更总闸（唯一判定点）
若本轮识别结果为 **0 新增 + 0 修改 + 0 删除** → 立即终止整个流程，**不进入第四步 CHECKPOINT、不执行第四/五步任何写入或数字同步、不执行第六步的 commit-cc-plugin 调用**。仅输出「本次 changelog 检查完成，所有功能点已在 tips.txt 覆盖，无需变更」后结束。第四步、第六步中对"0 变化"的提及均以本节为准，不重复判断。

## 第四步 — 写入 tips.txt

> 🔴 **CHECKPOINT**（仅在变更数 > 0 时触发，0 变化场景见「🚦 零变更总闸」）：写入前展示变更预览——列出「📥 新增 N 条 / ✏️ 修改 N 条 / 🗑️ 删除 N 条」及每条标题，等待用户确认：
> - 输入 `y` / `yes` / 按 Enter → 继续执行写入和第五步数字同步
> - 输入 `n` / `no` / 任何其他内容 → **立即停止**，输出「操作已取消，tips.txt 未修改」，不执行任何写入或提交

```
Edit: plugins/optimus-devops-plugin/hooks/sessionstart/tips.txt
```

- **新增**：追加到文件末尾，每条内容后跟一行 `---` 作为分隔符
- **修改**：原地替换对应条目内容，保持位置不变
- **删除**：移除条目及其后的 `---` 分隔符行

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| Edit 工具报错（文件锁 / 权限不足） | 等待 2 秒后重试一次 | 停止流程，报告错误路径，不继续第五步 |
| 写入后读回内容与预期不符 | 重新执行 Edit | 停止流程，提示用户手动检查文件状态 |
| 删除条目后 `---` 残留 | 再次定位并删除残留分隔符 | 在摘要中标注"分隔符可能残留，请人工确认" |

## 第五步 — 同步文档数字

统计写入后 tips.txt 的实际条目总数：**以独立 `---` 分隔符的数量加 1 为准**（主计数方式）；若结果与非空内容块数量不一致，以 `---` 计数为准，并在摘要中标注差异。

批量更新以下 5 处数字，将旧数字替换为新总数：

| 文件 | 位置 |
|---|---|
| `.claude-plugin/marketplace.json` | 顶层 `description` 中的 `N条技巧智能轮播` |
| `.claude-plugin/marketplace.json` | `optimus-devops-plugin` 的 `description` |
| `README.md` | 第 6 行简介 |
| `README.md` | SessionStart Hook 说明行 |
| `plugins/optimus-devops-plugin/hooks/README.md` | `tips.txt 包含 N 条技巧` |

同时将 `.claude-plugin/marketplace.json` 的 `version` 做 **Patch 升级**（`x.x.X`），因为这是已有内容的更新/修复，符合版本管理规范。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 某处文件不存在（如 README.md 路径错误） | 跳过该处，继续更新其余文件 | 在摘要中列出"未同步"文件，不阻断提交 |
| 数字 pattern 在文件中找不到 | 搜索邻近上下文确认格式是否变更 | 跳过并在摘要注明，不修改该文件 |
| 更新后数字不一致（多处数字不同） | 以 tips.txt 实际 `---` 计数为准 | 报告具体不一致位置 |

> 🔴 **CHECKPOINT**：若命中上表"数字不一致"分支，报告具体差异位置后**必须停止**，等待用户确认（y 按 `---` 计数结果继续提交 / n 取消本次提交）——不得在未确认的情况下直接进入第六步。

## 第六步 — 展示摘要并提交

按以下格式输出执行摘要：

```
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
📄 已同步：marketplace.json · README.md · hooks/README.md
🔖 版本：{旧版本} → {新版本}（Patch）

---
进入提交流程...
```

摘要展示完毕后，立即调用 `commit-cc-plugin` skill 完成提交推送。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| `commit-cc-plugin` skill 不可用 | 提示用户手动执行：`git add` → `git commit` → `git push` | 输出待提交的完整 diff 供用户参考 |
| 提交被 hook 拦截（pre-commit 失败） | 报告 hook 输出，不强制绕过 | 停止，提示用户修复后手动重试提交 |

## ⛔ 不要做什么（反例黑名单）

| 反模式 | 原因 | 替代做法 |
|---|---|---|
| 把 changelog 里所有更新项都加入 tips.txt | tips 面向用户实用技巧，不是版本记录——内部重构、bug fix、依赖升级不应出现 | 只加对用户操作有实质影响的功能（新 flag、新命令、新设置项） |
| 只用条目标题判断是否已覆盖 | tips.txt 每条包含完整正文，次级功能点只出现在功能/效果/例子字段而非标题 | 必须扫描 tips.txt **全文**，用主标识符（flag 名/设置项名/命令名）做精确匹配 |
| 0变化时仍然提交 | 产生无意义 commit，污染 git 历史 | 触发「🚦 零变更总闸」直接终止，不进入 Step 4-6，不调用 commit-cc-plugin |
| 修改 show-tip.sh 脚本逻辑 | 脚本逻辑不在本 skill 职责范围内 | 只修改 tips.txt 数据文件 |
| 删除旧功能条目，但该功能仍可用（只是有了替代方案） | 用户可能仍在用旧方式 | 仅在 changelog 明确标注 Removed/Deprecated 时删除 |
| 用估算数字代替实际计数更新文档 | 估算不准会导致文档与实际不符 | 必须先 Read tips.txt 计算实际 `---` 数量再更新 |
| 抓取失败后继续执行后续步骤 | 基于空数据的操作可能误删现有条目 | 第一步失败 → 立即停止，不执行任何写入操作 |

> `.claude/` 下的 skill 文件本身不触发版本号升级（遵循 CLAUDE.md 规范）
