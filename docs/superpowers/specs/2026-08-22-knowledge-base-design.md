# 知识库（knowledge-base）设计

> 状态：已批准，待转 writing-plans 生成实施计划

## 背景与动机

仓库目前有两类知识载体：

1. **规范文档集**（`docs/csharp_doc/`、`docs/wpf_doc/`）：面向人类阅读的 Markdown 规范，有阅读路径、RFC 2119 措辞（MUST/SHOULD/MAY）。
2. **Skill 内嵌知识**：如 `mastergo-to-wpf-components`/`mastergo-to-wpf-page` 中的"项目知识库匹配"，是运行时生成的项目级映射数据，不是仓库维护的通用知识。

驱动本次设计的具体痛点：

- 长篇规范文档不便被 skill 精准引用到某条具体规则。
- 多个插件各自维护相似的判断规则或参考资料，容易口径不一致。
- 新 skill（如未来改造 `csharp-code-review`）缺少可编程消费的结构化知识源。

目标：建设一个跨插件共享、可被 skill 编程式查询的规范知识库，同时保留人类可读性。不与"人类阅读 vs 机器消费"做割裂设计，而是让同一套内容同时服务两者。

仓库根目录已存在一个空的 `./knowledge-base` 目录（未提交、未在 gitignore 中排除），本设计直接复用该目录作为知识库根。

## 范围声明

- 本次搭建知识库的目录结构、索引机制、维护 skill；**同时处理** `plugins/optimus-backend-plugin/skills/csharp-code-review` 中与规范文档重复的内嵌知识（见 Section 5）——该 skill 是当前仓库里唯一已发现的、内嵌完整规范内容且与知识库直接冲突的案例，纳入本次一并解决，避免同一套规则存在两份独立维护的拷贝。
- 其余 skill 中若发现类似的纯文档知识内嵌（非本次排查范围内的），后续按 Section 5 同样的原则处理，不在本次强制排查全仓库。
- 知识库当前只收纳 `csharp`、`wpf` 两个领域（迁移自现有文档），新领域按同一模式随时追加。

## Section 1：目录结构与迁移

统一的领域目录模式（对 `csharp`、`wpf` 及未来任何新领域一致）：

```
knowledge-base/
├── README.md                      # 知识库总说明：领域列表、consume 约定
├── csharp/
│   ├── README.md                  # 沿用 docs/csharp_doc 现有阅读路径说明
│   ├── 01-project-structure.md    # 规范条款（MUST/SHOULD/MAY，判断合规性）
│   ├── ...
│   ├── 17-comments-docs.md
│   ├── index.jsonl                # 索引：rule + reference 统一编目
│   └── reference/                 # 描述性知识，无规范语气，按主题命名不编号
│       ├── linq-deferred-execution.md
│       └── pattern-matching-syntax.md
└── wpf/
    ├── README.md
    ├── 01-...17-*.md
    ├── index.jsonl
    └── reference/
```

规则：

- **规范文件（01-17 系列）**：只回答"该不该这么写"，延续现有 MUST/SHOULD/MAY 语气。
- **`reference/` 目录**：只回答"这是什么/怎么用"，纯描述性讲解，无合规判断语气。文件按主题命名，不编号（数量和主题会持续增长，编号会导致后续插入困难）。
- **规范条款可选择引用 reference**：当某条规范的判断依据需要更深的语法讲解支撑时，规范正文里用相对链接指向对应 `reference/*.md`；reference 内容本身不重复抄写进规范文件，保持单一来源。引用是单向的——reference 不反向声明"被哪条规范引用"，避免规范措辞变动时需要同步维护 reference。
- **规范条款与 reference 是并列关系，不是从属关系**：某个领域可以只有 reference、没有规范条款（例如未来新增 `sql` 领域，初期只沉淀"窗口函数用法"等参考知识，尚未形成规范判断）；也可以先有 reference 后补规范，顺序不做强制。

迁移动作：

1. `git mv docs/csharp_doc knowledge-base/csharp`，`git mv docs/wpf_doc knowledge-base/wpf`（内容不变，只搬位置）。
2. 每个领域目录下新增 `index.jsonl`（见 Section 2）和 `reference/` 空目录。
3. 新增 `knowledge-base/README.md`，列出当前领域、consume 约定（指向 Section 3）。
4. 修正 `docs/csharp_doc/17-comments-docs.md:68` 中唯一的内部自引用路径（`docs/csharp_doc/` → `knowledge-base/csharp/`）。
5. 复用已存在的空 `./knowledge-base` 目录，不新建。

## Section 2：索引文件格式

每个领域目录下一个 `index.jsonl`（JSON Lines，每行一条独立记录）。选择 JSONL 而非单个 JSON 数组，是因为 skill 主要靠 Grep 按关键词/标签/级别检索——JSONL 每行自成一条完整记录，Grep 命中一行即可直接使用；美化格式的 JSON 数组每条记录跨多行，Grep 命中后还需靠上下文行猜边界，不利于 agent 消费。

`rule` 与 `reference` 共用同一 schema，靠 `kind` 区分，无关字段省略：

```json
{"id": "csharp.01.editorconfig", "kind": "rule", "level": "MUST", "file": "01-project-structure.md", "anchor": "editorconfig", "title": ".editorconfig 强制生效", "tags": ["project-structure", "tooling"], "summary": "所有项目根目录必须包含 .editorconfig，且 CI 按 warnings-as-errors 校验。"}
{"id": "csharp.ref.linq-deferred-execution", "kind": "reference", "file": "reference/linq-deferred-execution.md", "anchor": "", "title": "LINQ 延迟执行", "tags": ["linq", "execution-model"], "summary": "解释 IEnumerable 查询在枚举时才真正求值，及其对多次枚举/异常时机的影响。"}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `id` | `<domain>.<file编号或ref>.<slug>`，全局唯一，人工手写，不自动生成 |
| `kind` | `"rule"` \| `"reference"` |
| `level` | 仅 `rule` 有，取值 `MUST`/`SHOULD`/`MAY`；`reference` 省略此字段 |
| `file` | 相对领域目录的文件路径，定位原文 |
| `anchor` | 文件内标题锚点，无锚点可留空字符串 |
| `title` | 条目标题 |
| `tags` | 自由关键词数组，供按主题 grep |
| `summary` | 一句话摘要，供 skill 不打开原文件即可判断相关性 |

索引不复制正文，原始 Markdown 文件始终是唯一真相源。

## Section 3：维护约定与一致性校验

- **同步纪律**：新增或修改一条规范/reference 时，同一次提交里必须同步更新对应 `index.jsonl`（新增 append 一行；修改标题/级别/位置时同步改字段）。写入 `knowledge-base/README.md` 作为约定说明。
- **一致性自检脚本**：`knowledge-base/check_index.py`（`unittest` 风格，符合仓库"本机无 pytest"约束），校验：
  1. 每条记录的 `file` 指向的文件确实存在；
  2. 有 `anchor` 的记录，对应文件中确实存在该标题；
  3. `id` 全局不重复。
  供人工/agent 改动后手动运行，不接入 CI 或 hook。
- **维护责任**：不新增专职角色，谁改动 `knowledge-base/` 内容，谁负责同步索引与自检，与现有 `docs/csharp_doc` 维护方式一致。
- **明确不做**：不做自动生成索引的脚本（`tags`/`summary`/`level` 需要语义判断，机械提取质量不可靠）；`knowledge-base/` 内容变更不触发 `marketplace.json` 版本升级（内容资产，非 CLAUDE.md 定义的插件功能），除非某插件 skill 因此改变行为，则该 skill 按现有版本规则处理。

## Section 4：`knowledge-base-maintain` skill

- **位置**：`.claude/skills/knowledge-base-maintain/`（仓库自用，无插件前缀，调用 `/knowledge-base-maintain`），需在 `.kiro/skills/` 补同名符号链接镜像（`commit-cc-plugin` 自动补齐）。
- **frontmatter**：`category: tool`；`allowed-tools: Read Write Edit Bash Grep Glob`；`compatibility` 声明依赖 Python（跑 `check_index.py`，`unittest`，非 `pytest`）。
- **核心流程**（引导器角色，指导"如何正确新增/修改一条知识"，并调用脚本做后置校验）：
  1. **新增条目**：确认 `domain`（新领域则同步建 `knowledge-base/<domain>/README.md` + `reference/` 骨架）、`kind`（rule/reference）、`kind=rule` 时追问 `level`；引导正文写入位置；追加一行到 `index.jsonl`；跑 `check_index.py`。
  2. **修改/迁移条目**：定位现有 `index.jsonl` 行 → 同步改内容与索引 → 校验。典型场景：把内容从规范文件挪到 `reference/`。
  3. **仅校验**：不新增内容，只运行 `check_index.py` 查看当前一致性状态。
- **前置校验**（按 `.claude/rules/skill-authoring.md` 四类检查）：依赖检查（Python 可用）；输入参数检查（若指定 `domain` 且非新建，目录须存在）；输出参数检查（写入路径父目录存在）；无强"运行条件"硬约束，`id` 重复等问题走脚本校验后置报告。
- **不做的事**：不做语义内容生成，`summary`/`tags` 由人/agent 判断填写，skill 只负责流程引导与格式/一致性校验。

## Section 5：`csharp-code-review` 内嵌知识去重

排查发现：`plugins/optimus-backend-plugin/skills/csharp-code-review/SKILL.md` 的"审查清单"章节内嵌了 12 个类别的完整规则（命名约定、类型使用、字符串处理、逻辑运算符、代码结构、`var` 使用、集合与 LINQ、对象创建、委托与事件、异常处理、异步模式、API 设计与健壮性），与迁移后的 `knowledge-base/csharp/` 规范条款存在大面积重复：

| csharp-code-review 类别 | 对应 knowledge-base 篇章 | 处理方式 |
|---|---|---|
| 1. 命名约定 | `02-coding-style.md` §1 | 删除 skill 内嵌表格，改引用 |
| 2-6. 类型/字符串/运算符/结构/`var` | `02-coding-style.md` §2 | 删除，改引用 |
| 7. 集合与 LINQ | `07-performance.md` §3 | 删除，改引用 |
| 8. 对象创建 | `02-coding-style.md` §2.4 | 删除，改引用 |
| 10. 异常处理 | `05-error-handling.md` | 删除，改引用 |
| 11. 异步模式 | `04-async-programming.md` §6、`13-api-design.md` | 删除，改引用 |
| 12. API 设计与健壮性（异常语义统一、取消令牌传播） | `05`/`13`/`04` 已覆盖 | 删除，改引用 |
| 9. 委托与事件（优先 `Func<>`/`Action<>`） | 现有规范文档**未覆盖** | 新增为 `knowledge-base/csharp/` 规范条目（归入 `02-coding-style.md` 或 `03-design-principles.md`，由执行阶段判断） |
| 12. "隐式依赖契约需要显式说明" | 现有规范文档**未覆盖**（仅 `03-design-principles.md` 反例代码注释提及，非正式条款） | 新增为 `knowledge-base/csharp/` 规范条目（归入 `13-api-design.md` 或 `03-design-principles.md`） |

处理原则：

- **逐条删重，不整体保留**：已被规范文档覆盖的内容从 SKILL.md 删除，不作为并行拷贝保留——同一规则存在两份独立文字表述，长期必然漂移不一致。
- **skill 改为引用规范**：SKILL.md 的"审查清单"章节改写为指向 `knowledge-base/csharp/` 对应文件/条目 `id` 的引用列表（审查时按引用去读原文规则），不再自建规则文本。速查表、"为什么重要"讲解等 skill 特有的呈现形式（checkbox、severity 分级提示）可以保留，但规则内容本身以引用为准。
- **两条真缺口内容新增后先入库**：先按 Section 1-2 流程把这两条写入 `knowledge-base/csharp/` 并登记索引，再让 SKILL.md 引用，不倒着来（不能让 skill 继续维护一份规范文档里没有的规则文本）。
- **权威参考章节调整**：SKILL.md 末尾的"权威参考"从 Microsoft 官方文档链接，改为同时说明"团队规范以 `knowledge-base/csharp/` 为准，语言层通用惯例参考 Microsoft 官方文档"，避免误导——团队内部规则的权威来源应是仓库自己的规范，而非外部文档。
- **版本处理**：这是对 `plugins/` 下已有内容的修改（非破坏性，行为不变只是知识来源变化），按 `CLAUDE.md` 版本规则计 **Patch**，随 `commit-cc-plugin` 一并升级 `csharp-code-review` 的 `metadata.version` 与仓库 `marketplace.json`。

## Section 6：knowledge-base 自身版本号与 CHANGELOG

`knowledge-base/` 作为一个整体维护**独立于 `marketplace.json` 的单一版本号**（不按领域拆分——csharp、wpf 及未来新领域共用一个版本号，任一领域的变更都升级同一个号）。

- **版本号位置**：`knowledge-base/README.md` 顶部加一行 `> 版本：x.x.x`，格式比照 `plugins/*/skills/*/README.md` 现有的 `> 版本：1.0.0 | 分类：generator` 写法（去掉不适用的"分类"字段）。
- **CHANGELOG.md**：新增 `knowledge-base/CHANGELOG.md`，格式与 skill 的 `CHANGELOG.md` 完全一致（见 `.claude/rules/skill-authoring.md` CHANGELOG 规范）：

```markdown
## [版本号] - YYYY-MM-DD

### Added
- 新增的领域/规范条目/reference 条目

### Changed
- 修改的内容

### Removed
- 删除的内容

### Fixed
- 修复的问题
```

只写实际发生的类别，无变更的类别省略。

- **版本升级规则**（比照 skill 版本规则，换算到知识库内容语义）：

| 变更类型 | 版本升级 |
|---|---|
| 新增领域、新增规范条目、新增 reference 条目 | **Minor** `x.X.x` |
| 修改已有规范/reference 内容、修正索引、文档优化 | **Patch** `x.x.X` |
| 删除领域、删除规范条目、规范措辞产生不兼容语义变化（如 SHOULD 改 MUST） | **Major** `X.x.x` |

- **初始版本**：本次迁移与建设（Section 1-5 全部内容）视为创世提交，初始版本 `1.0.0`；CHANGELOG 第一条记录本次全部变更（迁移 csharp/wpf 两个领域、建立索引机制、新增两条缺口规范、`csharp-code-review` 去重改造）。
- **与仓库整体版本的关系**：独立于 `marketplace.json`，两者不联动，与 Section 3 已确定的"knowledge-base 内容变更不触发 marketplace.json 升级"一致。
- **维护责任并入 `knowledge-base-maintain` skill**：该 skill 引导新增/修改条目时，同步判断本次变更的版本升级级别，追加 CHANGELOG 条目并更新 `README.md` 版本号，与索引一致性校验一起完成，不依赖人工事后补记。

## 待实施清单（转 writing-plans）

1. 迁移 `docs/csharp_doc` → `knowledge-base/csharp`，`docs/wpf_doc` → `knowledge-base/wpf`。
2. 为两个领域生成 `index.jsonl`（回填现有 01-17 规范条目的索引记录）、`reference/` 空目录、领域 `README.md` 补充说明。
3. 新增 `knowledge-base/README.md`（含版本号）、`knowledge-base/CHANGELOG.md`（初始 `1.0.0`）、`knowledge-base/check_index.py`。
4. 修正 `knowledge-base/csharp/17-comments-docs.md` 内部自引用路径。
5. 新建 `.claude/skills/knowledge-base-maintain/`（SKILL.md + CHANGELOG.md），并在 `.kiro/skills/` 建同名符号链接；职责中包含引导版本号/CHANGELOG 同步。
6. 全仓搜索 `docs/csharp_doc`、`docs/wpf_doc` 残留引用并更新（当前已知：`.remember/` 下的历史记忆文件不必更新，属于历史快照）。
7. 补齐 `knowledge-base/csharp/` 两条缺口规范条目（委托与事件选择、隐式依赖契约显式说明），登记索引。
8. 改写 `csharp-code-review/SKILL.md` 审查清单章节为引用形式，删除已重复的规则文本；更新"权威参考"章节；`CHANGELOG.md` 记录本次调整；升级 `metadata.version`（Patch）与 `marketplace.json`。
