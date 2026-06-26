---
name: sync-cc-tips
description: 从 Claude Code 最新 changelog 自动同步 tips.txt：新增未覆盖条目、修正过时内容、删除已废弃功能，同步所有文档数字，最后调用 commit-cc-plugin 提交。触发场景：用户说 "/sync-cc-tips"、"更新tips"、"同步tips"、"tips需要更新"、"从changelog更新tips"、"sync tips"。可附带版本数量参数，如 "/sync-cc-tips 5" 表示只看最近5个版本。
disable-model-invocation: true
---

# /sync-cc-tips

从 Claude Code 最新 changelog 全自动同步 tips.txt，无需人工干预，完成后展示摘要并提交。

## 第一步 — 抓取 changelog

**优先使用 Playwright CLI**（JS 渲染，内容更完整）：

调用 `playwright-cli` skill，执行以下步骤：
1. 导航至 `https://github.com/anthropics/claude-code/releases`
2. 等待页面加载完成（等待 `.release-entry` 或 `[data-hpc]` 元素出现）
3. 提取每个 release 的版本号和正文内容（展开所有折叠块）

**降级条件**：若 playwright-cli skill 不可用、浏览器启动失败或抓取结果为空，则：
> ⚠️ Playwright CLI 不可用，降级为 WebFetch（静态 HTML，部分版本 body 可能不完整）

改用：
```
WebFetch: https://github.com/anthropics/claude-code/releases
```

**无论使用哪种方式：**
- 默认提取最近 **10 个版本**的更新内容
- 若用户指定数量（如 `/sync-cc-tips 5`），按指定数量提取
- 记录版本范围（如 v2.1.160 → v2.1.170），用于摘要展示

## 第二步 — 读取现有 tips.txt

```
Read: plugins/unipus-devops-plugin/hooks/sessionstart/tips.txt
```

逐条扫描 tips.txt，提取每条涉及的功能名称、CLI flag、子命令、settings.json 键名，构建「已覆盖功能集」，用于第三步的差异识别。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 文件不存在 / Read 报错 | 确认路径 `plugins/unipus-devops-plugin/hooks/sessionstart/tips.txt` 是否正确 | 停止整个流程，报告路径错误，不做任何修改 |
| 文件存在但内容为空 | 提示用户确认是否为全新初始化场景 | 若用户确认，继续（视为无旧条目）；否则停止 |

## 第三步 — 三类差异识别

依次对 changelog 中每个功能点做判断：

### 🆕 新增条件
以下情况生成新条目：
- 新 CLI flag（如 `--safe-mode`、`--advisor`）
- 新子命令（如 `claude daemon`、`claude attach`）
- 新 Hook 事件（如 `MessageDisplay`、`PreCompact`）
- 新 settings.json 设置项（如 `fallbackModel`、`disableBundledSkills`）
- 新交互命令（如 `/cd`、`/plugin list`）
- tips.txt 中**无任何条目**覆盖该功能

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

## 第四步 — 写入 tips.txt

> 🔴 **CHECKPOINT**：写入前展示变更预览——列出「📥 新增 N 条 / ✏️ 修改 N 条 / 🗑️ 删除 N 条」及每条标题，等待用户确认（输入 y/yes 或按 Enter）后再执行写入和第五步数字同步。若变更数为 0，跳过此检查点直接退出。

```
Edit: plugins/unipus-devops-plugin/hooks/sessionstart/tips.txt
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

统计写入后 tips.txt 的实际条目总数：计算文件中独立 `---` 分隔符的数量加 1，即为条目总数（也可直接数非空内容块的数量交叉验证）。

批量更新以下 5 处数字，将旧数字替换为新总数：

| 文件 | 位置 |
|---|---|
| `.claude-plugin/marketplace.json` | 顶层 `description` 中的 `N条技巧智能轮播` |
| `.claude-plugin/marketplace.json` | `unipus-devops-plugin` 的 `description` |
| `README.md` | 第 6 行简介 |
| `README.md` | SessionStart Hook 说明行 |
| `plugins/unipus-devops-plugin/hooks/README.md` | `tips.txt 包含 N 条技巧` |

同时将 `.claude-plugin/marketplace.json` 的 `version` 做 **Patch 升级**（`x.x.X`），因为这是已有内容的更新/修复，符合版本管理规范。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 某处文件不存在（如 README.md 路径错误） | 跳过该处，继续更新其余文件 | 在摘要中列出"未同步"文件，不阻断提交 |
| 数字 pattern 在文件中找不到 | 搜索邻近上下文确认格式是否变更 | 跳过并在摘要注明，不修改该文件 |
| 更新后数字不一致（多处数字不同） | 以 tips.txt 实际 `---` 计数为准 | 报告具体不一致位置，等用户确认后提交 |

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
| 0变化时仍然提交 | 产生无意义 commit，污染 git 历史 | 检测到 0新增/0修改/0删除 → 输出提示并退出，不调用 commit-cc-plugin |
| 修改 show-tip.sh 脚本逻辑 | 脚本逻辑不在本 skill 职责范围内 | 只修改 tips.txt 数据文件 |
| 删除旧功能条目，但该功能仍可用（只是有了替代方案） | 用户可能仍在用旧方式 | 仅在 changelog 明确标注 Removed/Deprecated 时删除 |
| 用估算数字代替实际计数更新文档 | 估算不准会导致文档与实际不符 | 必须先 Read tips.txt 计算实际 `---` 数量再更新 |
| 抓取失败后继续执行后续步骤 | 基于空数据的操作可能误删现有条目 | 第一步失败 → 立即停止，不执行任何写入操作 |

> `.claude/` 下的 skill 文件本身不触发版本号升级（遵循 CLAUDE.md 规范）
