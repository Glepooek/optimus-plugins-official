# tips 存储改 JSONL + show-tip/sync-cc-tips 优化设计

- 日期：2026-09-04
- 状态：已批准（经 brainstorming 确认）
- 范围：`plugins/optimus-devops-plugin` 的 SessionStart 技巧展示链路 + 维护型 skill `sync-cc-tips`

## 背景与动机

`tips.txt` 现存 **129 KB / 552 物理行 / 276 条**，每条 = **1 个物理行**，正文用**字面 `\n` 转义**拼装，条目间以 `---` 分隔。消费者只有两个：

1. `plugins/optimus-devops-plugin/hooks/sessionstart/show-tip.sh`（每会话启动读来展示）
2. `.claude/skills/sync-cc-tips/SKILL.md`（同步 changelog 时读来计数 + 判重）

`install.sh`/`install.ps1` 只 `cp` 复制，不解析——改格式不碰坏安装。

**当前存储/读取方式的低效点：**

| 问题 | 现状 |
|---|---|
| 人不可读 | 正文靠字面 `\n` 转义，人眼只能看转义序列，无法直接阅读 |
| 机要拆解 | 读取 = `content.split('---\n')` 全文拆 + 每条 `tip.replace('\\n','\n')`，无索引、无元数据 |
| 判重靠猜 | sync-cc-tips 用 grep 正则提取全文命令名/标识符，别名字面不同判不出来（`/cost`≡`/usage`、`/review`≡`/code-review` 等 4 组重复） |
| 无稳定主键 | 每条无 `id`，轮播状态 `round/remaining/count`，count 一变就**整体重建** |

## 目标

1. **存储格式**改为 JSONL（每行一个 JSON 对象），结构化 + 人可读 + 可索引
2. **show-tip 读取**改按结构化字段读取，显示 **每次 6 条**（默认 + 上限 6），轮播状态按 `id` 走
3. **sync-cc-tips 匹配/判重**改按 `id` + 别名归一化，并加固 6 条检测规则

## 设计

### 1. 存储格式：`tips.jsonl`

每条 = 一行 JSON：

```json
{"id":"/fast","category":"交互","title":"🚀 /fast 快速模式","body":"功能：…\n效果：…\n例子：…"}
```

- `id`：稳定主键，供判重与轮播记忆。**生成规则**：迁移时自动取标题主标识符（命令名 / flag / 功能名），无主标识符时用标题 slug。最终的归属真源 = 本机 Claude 二进制 `no({name:"…"` 注册表（谁运行响应归谁），迁移后人工校正一次。
- `category`：原 `[分类]` 标签（含 `[Skill·superpowers]` 这类带 `·` 的）。
- `title`：`[分类] ` 之后、首个 `\n` 之前。
- `body`：`功能/效果/例子` 三段，`\n` 转真实换行。

### 2. 迁移：`tips.txt` → `tips.jsonl`

- 脚本切分：`---` 为条目边界 + `[分类]` 前缀剥离 + 字面 `\n` 转真实换行
- **保留语义、不改内容**——只改封装
- 旧 `tips.txt` 生成后重命名保留为 `tips.txt.bak`，删除契约，避免读者混淆

### 3. `show-tip.sh`

- 读取 `tips.jsonl`（`json.loads` 逐行），不再 `split('---\n')` + `replace`
- `TIPS_COUNT=${CLAUDE_TIPS_COUNT:-6}`；上限由 `min(3,…)` 改为 `max(1, min(6, TIPS_COUNT))`
- 状态文件升级为**按 `id` 记忆**：已展示 `id` 集合 + 轮次 + 游标；count 变化增量更新而非整体重建
- 显示条数固定 6 / 上限 6

### 4. `sync-cc-tips` SKILL.md

- 第二步判重：从「grep 全文正则」改为**读 JSONL 的 `id` 集合**（按 `category`/`id` 索引）
- 规则加固 6 条：
  1. **别名归一化判重**：`/cost`≡`/usage`、`/review`≡`/code-review`、`/plugins`≡`/plugin`、`/undo`≡`/rewind`
  2. **库内残影检测**：已有条目两两比对，A⊇B 完全覆盖 → 标合并/删除
  3. **完整性校验补斜杠命令 + skill 名**：禁止裸缩写（`/tdd`、`debugging`、`parallel-agents`）
  4. **新增环境可用性门**：本机跑不了（mac/Linux-only、Enterprise 席位、cloud-SDK、claude.ai 账号）→ `⏭️ 跳过（本机不可用）`
  5. **「修改」不追加版本沿革**：覆盖旧语义，条目长度不超中位数 2×
  6. **同步点处数统一为 4 处**：marketplace.json description、hooks/README.md、.codex-plugin/plugin.json longDescription、.kiro/steering/plugins.md

### 5. 周边契约

- `install.sh` / `install.ps1`：`cp tips.txt` → `cp tips.jsonl`
- `hooks/README.md`：格式说明改 JSONL；「1-3 条」→「1-6 条」
- `.claude-plugin/marketplace.json` + `.codex-plugin/plugin.json`：Patch `13.1.8 → 13.1.9`（两处同值）

## 测试

- 迁移后校验 276 条 JSONL 全部可解析
- `show-tip.sh` 实跑输出 6 条 + 分隔线正常
- sync-cc-tips 计数从 JSONL 读取一致

## 版本与提交

- 涉及 `plugins/` 下 hook 变更 → Patch `13.1.8 → 13.1.9`
- 走 `commit-cc-plugin` skill，不手动 git
