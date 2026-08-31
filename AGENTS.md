# AGENTS.md

本文件为 AI 编码 agent（Claude Code / OpenAI Codex）在此仓库中工作时提供指导。

## 仓库定位

自定义插件仓库，提供企业级开发工具链，**同时支持 Claude Code 与 OpenAI Codex 双 harness**。

各插件职责见 `.claude-plugin/marketplace.json` 的 `description` 字段。

**核心原则：单一真源，两个 harness 共用。** 所有 skill 内容只在 `plugins/*/skills/*/SKILL.md` 维护一份（开放 Agent Skills 规范，agentskills.io 六字段 frontmatter），两个 harness 各自的清单文件（`.claude-plugin/marketplace.json` / `.agents/plugins/marketplace.json` + 每插件 `.codex-plugin/plugin.json`）只是指向同一份内容的安装入口，不重复维护技能正文。下文规则默认对两个 harness 同时生效；仅在**必要差异**一节列出的地方才有分叉。

---

## Skill 分层与调用

**两层 skill，不要混淆：**

| 位置 | 性质 | Claude 调用 | Codex 调用 |
|---|---|---|---|
| `plugins/*/skills/` | 对外发布的插件产物 | `/plugin-name:skill-name` | 自然语言触发（按 description 匹配）或 `@plugin-name:skill-name` |
| `.claude/skills/` | 仅本仓库维护自用，不发布 | `/skill-name`（无前缀，经 `.kiro/skills/` 镜像） | 同名触发（经 `.agents/skills/` 镜像） |

`.claude/skills/` 下的 skill 需在 `.kiro/skills/`（Claude/Kiro 生态）与 `.agents/skills/`（Codex）**两处**保持同名符号链接镜像，`commit-cc-plugin` 会自动检测并补齐两处。

复合 skill 调用：`/plugin-name:skill-name:substep`（两个 harness 语法一致，仅前缀符号不同）。

---

## 重要约束（两个 harness 通用）

- **跨插件无重复 skills**：每个插件专注特定领域，新功能前先确认无跨插件重叠
- **Skills 可相互引用**：子 skill 用相对路径，跨插件用绝对命名空间
- **复合 skills 很少见**：仅在 3 个以上阶段且每阶段 >200 行时使用
- **新 skill 上线前自检**：这个 skill 是「引导器」（指导用户/agent 完成某件事）还是「传感器」（校验/检测已有产物是否合规）？有没有配对的另一半（例如有生成类 skill 却没有对应的校验类 skill）？避免只造轮子不造刹车
- **SKILL.md 是唯一真源**：修改技能行为只改 `plugins/*/skills/*/SKILL.md`，不要为 Codex 单独维护副本或调整 frontmatter——两个 harness 读的是同一份文件

---

## 本地测试

见 `test-locally` skill（`/test-locally` 触发）。

Python 脚本单元测试（**本机无 `pytest`，只能用 `unittest`**）：

```bash
# 维护型 skill（各自独立跑，unittest discover 不递归跨目录）
python -m unittest discover -s .claude/skills/sync-cc-docs-to-youdaonote/scripts -p "test_*.py"  # 77 tests
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"     # 139 tests
```

---

## 版本管理规则

| 变更路径 | 操作类型 | 版本升级 |
|---|---|---|
| `.claude/` 下任何文件 | 任意 | **不升级** |
| `plugins/` 下新增 skill/hook/command | 新增 | **Minor** `x.X.x` |
| `plugins/` 下更新/修复已有内容 | 更新 | **Patch** `x.x.X` |
| `plugins/` 下删除/重命名用户可见功能 | 删除 | **Major** `X.x.x` |

升级时编辑 `.claude-plugin/marketplace.json` 的 `version` 字段（两个 harness 共用的版本号真源），随本次提交一并推送。**功能变了版本号不变 = 不完整交付**——必须主动检查并升版，不等用户提醒。

若变更涉及 `plugins/` 下某插件，其 `.codex-plugin/plugin.json` 的 `version` 字段须同步改为相同值（该文件的 `version` 从 `.claude-plugin/marketplace.json` 抄录，不是独立真源）。

Minor/Major 升级前必须用 `darwin-skill` 对改动的 skill 评分：新分数 ≥ 改动前分数才可提交，倒退则先修正。（评分产物落在 gitignore 的 `.claude/skills/darwin-skill/results.tsv`，不进版本库。）

---

## Skill frontmatter 规范

Skill frontmatter / CHANGELOG 规范见 `.claude/rules/skill-conventions.md`（编辑 SKILL.md / CHANGELOG.md 或 `plugins/*/skills/` 下的 README.md 时自动加载）。该规范同时约束两个 harness——frontmatter 字段是 Codex 也会原样读取缓存的内容，不存在"仅 Claude 遵守"的特例。

---

## 提交与推送

**必须**使用 `commit-cc-plugin` skill，禁止手动执行 git 工作流。说"提交"或"推上去"即可触发。

---

## docs/ 与 knowledge-base/ 的定位划分

两者都是 Markdown 文档集合，但性质不同，新增文档前先判断该落在哪一侧（该判断与 harness 无关）：

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

## 关键文件

| 文件 | 用途 | harness |
|---|---|---|
| `.claude-plugin/marketplace.json` | 插件仓库元数据和版本号真源 | 两者共用（Codex 侧 `.codex-plugin/plugin.json` 的 version 从此抄录） |
| `.agents/plugins/marketplace.json` | Codex plugin marketplace 安装入口 | Codex 专属 |
| `plugins/*/.codex-plugin/plugin.json` | 每插件的 Codex 标识清单 | Codex 专属 |
| `.claude/rules/skill-conventions.md` | SKILL.md frontmatter / CHANGELOG 规范（按路径自动加载） | 两者共用 |

**已被 gitignore 的目录（有意排除，非缺失）：** `.claude/skills/darwin-skill/`（评估产物）、`.remember/`、`.codegraph/`

---

## 两个 harness 的必要差异（仅此一处，其余规则均通用）

| 方面 | Claude Code | Codex |
|---|---|---|
| 安装入口 | `/plugin marketplace add` 或手动 clone 到 `~/.claude/plugins/marketplace/` | `codex plugin marketplace add <repo>` → `codex plugin add <plugin>@optimus-plugins-official`，读取 `.agents/plugins/marketplace.json` |
| 提交流程 | 强制 `/commit-cc-plugin` skill | 标准 git + Conventional Commits，禁止 `--no-verify` |
| Hooks | SessionStart（技巧轮播）、Notification（权限通知）生效 | 无对应机制，Claude 侧 hooks 在 Codex 中不生效 |
| 维护型 skill 镜像目录 | `.kiro/skills/<name>` | `.agents/skills/<name>` |
| 插件标识文件 | `.claude-plugin/marketplace.json`（含全部插件） | 额外的 `.agents/plugins/marketplace.json` + 每插件 `.codex-plugin/plugin.json` |

除以上五项，其余所有规则（约束、frontmatter、版本管理、docs/knowledge-base 划分、本地测试）对两个 harness 一视同仁，不需要也不应该分叉处理。
