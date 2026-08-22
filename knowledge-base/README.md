# 知识库（knowledge-base）

> 版本：1.2.1

跨插件共享的规范知识库，供人类阅读也供 skill 编程式查询。当前收纳领域：`csharp`、`wpf`。

## 目录结构

每个领域目录遵循统一模式：

```
<domain>/
├── 00-README.md         # 领域说明、阅读路径
├── 01-*.md ... 17-*.md  # 规范条款（MUST/SHOULD/MAY 语气）
├── index.jsonl          # 索引：rule + reference 统一编目
└── reference/           # 描述性知识（无规范语气），首篇内容产生时才建
```

## 消费方式

skill 需要引用某条规范/知识时，先用 Grep 在对应领域的 `index.jsonl` 中按 `tags`/`title`/`summary` 检索，定位到 `id` 后按 `file` + `anchor` 打开原文件读取具体条款——索引不复制正文，原始 Markdown 文件始终是唯一真相源。

索引记录字段：

| 字段 | 说明 |
|---|---|
| `id` | `<domain>.<文件编号或ref>.<slug>`，全局唯一，人工手写 |
| `kind` | `"rule"` \| `"reference"` |
| `level` | 仅 `rule` 有，`MUST`/`SHOULD`/`MAY` |
| `file` | 相对领域目录的文件路径 |
| `anchor` | 文件内标题文本（非 slug），无锚点留空字符串 |
| `title` | 条目标题 |
| `tags` | 自由关键词数组 |
| `summary` | 一句话摘要 |

## 维护约定

- 新增/修改一条规范/reference 时，同一次提交里必须同步更新对应 `index.jsonl`。
- 改动后运行 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>` 做一致性自检（file 存在、anchor 存在、id 不重复；脚本随 `knowledge-base-maintain` skill 分发）。
- 规范条款可选择性引用 `reference/*.md` 加强依据；引用单向，reference 不反向声明被谁引用。
- 版本号见本文件顶部，变更规则与 CHANGELOG 格式见 `CHANGELOG.md`；日常新增/修改建议通过 `/knowledge-base-maintain` skill 完成，会自动同步索引与版本号。
- 不做自动生成索引的脚本——`tags`/`summary`/`level` 需要语义判断，机械提取质量不可靠。

## 与仓库已有资产的关系

- `plugins/optimus-backend-plugin/skills/csharp-code-review`：审查规则以 `knowledge-base/csharp/` 为准，见该 skill 的"权威参考"章节。
- `plugins/optimus-frontend-plugin/skills/wpf-xaml-performance`、`wpf-project-conventions`：性能与项目结构判断依据见 `knowledge-base/wpf/`。
