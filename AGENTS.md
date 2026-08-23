# AGENTS.md

本文件为 AI 编码 agent（Claude Code / OpenAI Codex）在此仓库中工作时提供指导。

## 仓库概览

自定义的 Claude Code 插件仓库，8 个领域插件提供企业级开发工具链。

各插件职责见 `.claude-plugin/marketplace.json` 的 `description` 字段。

**两层 skill，不要混淆：**

| 位置 | 性质 | 调用方式 |
|---|---|---|
| `plugins/*/skills/` | 对外发布的插件产物 | `/plugin-name:skill-name` |
| `.claude/skills/` | 仅本仓库维护自用，不发布 | `/skill-name`（无前缀） |

`.claude/skills/` 的 skill 需在 `.kiro/skills/` 保持同名符号链接镜像（`commit-cc-plugin` 会自动补齐）。

---

## 重要约束

- **跨插件无重复 skills**：每个插件专注特定领域，新功能前先确认无跨插件重叠
- **Skills 可相互引用**：子 skill 用相对路径，跨插件用绝对命名空间
- **复合 skills 很少见**：仅在 3 个以上阶段且每阶段 >200 行时使用
- **新 skill 上线前自检**：这个 skill 是「引导器」（指导用户/agent 完成某件事）还是「传感器」（校验/检测已有产物是否合规）？有没有配对的另一半（例如有生成类 skill 却没有对应的校验类 skill）？避免只造轮子不造刹车

---

## 开发规范

### Skill 调用规则

- 简单 skill：`/plugin-name:skill-name`
- 复合 skill：`/plugin-name:skill-name:substep`

---

## 本地测试

见 `test-locally` skill（`/test-locally` 触发）。

Python 脚本单元测试（**本机无 `pytest`，只能用 `unittest`**）：

```bash
python -m unittest discover -s .claude/skills/sync-cc-docs-to-youdaonote/scripts -p "test_*.py"
```

---

## 版本管理规则

| 变更路径 | 操作类型 | 版本升级 |
|---|---|---|
| `.claude/` 下任何文件 | 任意 | **不升级** |
| `plugins/` 下新增 skill/hook/command | 新增 | **Minor** `x.X.x` |
| `plugins/` 下更新/修复已有内容 | 更新 | **Patch** `x.x.X` |
| `plugins/` 下删除/重命名用户可见功能 | 删除 | **Major** `X.x.x` |

升级时编辑 `.claude-plugin/marketplace.json` 的 `version` 字段，随本次提交一并推送。**功能变了版本号不变 = 不完整交付**——必须主动检查并升版，不等用户提醒。

Minor/Major 升级建议先用 `darwin-skill` 对改动的 skill 评分，新分数不得低于改动前（不允许倒退），否则先修正再提交。

---

## Skill frontmatter 规范

Skill frontmatter / CHANGELOG 规范见 `.claude/rules/skill-conventions.md`（编辑 SKILL.md / CHANGELOG.md / AGENT.md 时自动加载）。

---

## 提交与推送（强制）

**必须**使用 `commit-cc-plugin` skill，禁止手动执行 git 工作流。说"提交"或"推上去"即可触发。

---

## 关键文件

| 文件 | 用途 |
|---|---|
| `.claude-plugin/marketplace.json` | 插件仓库元数据和版本号 |
| `.claude/rules/skill-conventions.md` | SKILL.md frontmatter / CHANGELOG 规范（按路径自动加载） |

**已被 gitignore 的目录（有意排除，非缺失）：** `.claude/skills/darwin-skill/`（评估产物）、`.remember/`、`.codegraph/`

---

## docs/ 与 knowledge-base/ 的定位划分

两者都是 Markdown 文档集合，但性质不同，新增文档前先判断该落在哪一侧：

| 维度 | `knowledge-base/` | `docs/` |
|---|---|---|
| 内容性质 | **规范条款**（MUST/SHOULD/MAY 语气），可执行的判断依据 | **叙述性资料**：使用指南、历史决策记录、外部资料备份 |
| 消费方式 | 被 skill **编程式检索**（`index.jsonl` + `file`+`anchor` 定位单条） | 人类完整阅读，无检索单条的场景 |
| 版本化 | 有独立版本号 + CHANGELOG，条目级别管理，见 `knowledge-base/README.md` | 无版本号，靠文件名日期或 git history 追溯 |

**判断标准**：这份内容是否需要被某个 skill 按条检索引用作为判断依据？是 → `knowledge-base/`；仅供人类阅读理解（工具怎么用、当时为什么这么设计、外部资料备份）→ `docs/`。

`docs/` 内部已有的分类，供参照：

- `superpowers/specs/`、`superpowers/plans/`：brainstorming→writing-plans 工作流产生的**历史决策记录**，记录某功能当时为什么这么设计，不是可复用规范，不进 knowledge-base
- `claude_blog/`、`claude_docs/`、`url_list.txt`：外部资料备份/追踪表，与本仓库规范无关
- `SUPERPOWERS_GUIDE.md`、`claude-code-config.md`：操作使用指南（怎么用某个工具/插件），非"代码该怎么写"的规范条款，即使内容详尽也不归入 knowledge-base——这类流程性叙述天然依赖线性阅读顺序，拆成索引条目会破坏可读性

---

## Codex CLI 兼容说明

本仓库同时支持 Claude Code 与 OpenAI Codex 双 harness。Codex 侧通过 `.agents/plugins/marketplace.json` 安装插件：

```bash
codex plugin marketplace add Glepooek/optimus-plugins-official
codex plugin add optimus-frontend-plugin@optimus-plugins-official   # 逐个按需安装
```

Codex 与 Claude 在本仓库的约定差异：

- **提交**：Claude Code 用 `/commit-cc-plugin` skill；Codex 无此 skill，改用标准 git 工作流 + Conventional Commits（`type(scope): subject`），禁止 `--no-verify` 绕过 hook。
- **Hooks**：Claude 侧有 SessionStart（技巧轮播）/Notification；Codex 无对应 hooks 机制，这些在 Codex 侧不生效。
- **MCP**：各插件通过 `.codex-plugin/plugin.json` 的 `mcpServers` 字段暴露（见 `plugins/optimus-mcp-servers/.mcp.json`）。
- **两层 skill**：`plugins/*/skills/` 为对外发布产物；`.claude/skills/` 为本仓库维护自用，经 `.agents/skills/` 符号链接暴露给 Codex。
