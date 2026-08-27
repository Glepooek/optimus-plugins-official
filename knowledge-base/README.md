# 知识库（knowledge-base）

> 版本：3.0.0

跨插件共享的规范知识库，供人类阅读也供 skill 编程式查询。当前收纳领域：`dotnet`、`csharp`、`wpf`、`git`、`media`、`skill-authoring`。其中 `dotnet`、`media` 为纯描述性参考领域（无规范条款），其余领域为规范条款 + 参考混合。

## 目录结构

每个领域目录遵循统一模式——**元数据在领域根目录，内容按类型分目录**：

```
<domain>/
├── 00-README.md         # 领域说明、阅读路径、分类说明
├── index.jsonl          # 索引：rule + reference 统一编目
├── rules/               # 规范条款（MUST/SHOULD/MAY 语气）
│   ├── 01-*.md ... 17-*.md
└── reference/           # 描述性知识（无规范语气），首篇内容产生时才建
    └── *.md
```

目录约束：

- `00-README.md`、`index.jsonl` 是领域导航元数据，始终位于领域根目录，不下沉到分类目录。
- `rules/` 只放可用于合规判断的规范正文；文件编号在 `rules/` 内保持既有顺序。
- `reference/` 与 `rules/` 是**同级并列**关系，不是从属关系；reference 只解释概念、机制、工具和用法。
- 索引的 `file` 始终是相对领域根目录的路径（`rules/05-error-handling.md`、`reference/video-codecs.md`）；正文内交叉引用同样采用该形式，与索引保持一致。
- 后续新增分类（如 `examples/`、`decisions/`、`playbooks/`）必须先定义用途、内容语气、索引 `kind` 与生命周期规则，再建目录，并登记到 `catalog.json`；不预建空目录，也不设"其他"这类无语义收容目录。

根目录另有 `catalog.json` 领域目录册，登记每个领域的内容分类、维护者、状态、主要消费者与最近审阅日期。新增或删除领域时必须同步维护——`check_index.py` 会校验 `catalog.json` 与实际领域目录双向一致（登记了不存在的领域、或存在未登记的领域都会报错）。

领域职责边界：`dotnet` 负责 Runtime、.NET Framework、SDK、目标框架、操作系统兼容性与生命周期；`csharp` 负责 C# 语言和通用工程实践；`wpf` 负责 WPF/XAML 桌面 UI 技术栈；`git` 负责版本控制协作；`media` 负责媒体处理概念；`skill-authoring` 负责 Skill 创建与维护规范。领域可以相互引用，但不得复制同一事实或规则。

## 消费方式

skill 需要引用某条规范/知识时，先用 Grep 在对应领域的 `index.jsonl` 中按 `tags`/`title`/`summary` 检索，定位到 `id` 后按 `file` + `anchor` 打开原文件读取具体条款——索引不复制正文，原始 Markdown 文件始终是唯一真相源。

两种消费模式，按场景选择，不互斥：

- **动态检索**：consumer 事先不知道规则具体在哪，先按关键词在 `index.jsonl` 查，再按 `file`+`anchor` 定位原文，适合临时性、探索式引用。
- **固定映射**：consumer 自身已有稳定的分类体系（如代码审查的审查大类），可以直接在自己的文档里写死 `file` § `章节` 引用，不必先过一遍 `index.jsonl`——`csharp-code-review`、`wpf-code-review` 的"审查清单"表格属于此类，是被认可的消费方式，不代表未遵循规范。

索引记录字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 必填 | `<domain>.<两位文件编号或 ref>.<slug>`，全局唯一，人工手写；slug 用小写字母/数字/连字符 |
| `kind` | 必填 | `"rule"` \| `"reference"` |
| `level` | rule 必填 | 仅 `rule` 有，`MUST`/`SHOULD`/`MAY`；`reference` 不得有 |
| `file` | 必填 | 相对领域根目录的路径（`rules/*.md` 或 `reference/*.md`） |
| `anchor` | 必填 | 文件内标题文本（非 slug），无锚点留空字符串 |
| `title` | 必填 | 条目标题 |
| `tags` | 必填 | 自由关键词数组 |
| `summary` | 必填 | 一句话摘要 |
| `enforcement` | 可选 | `ci` \| `review` \| `advisory`，表达规则如何执行 |
| `status` | 可选 | `active` \| `deprecated` \| `experimental`，缺省视为 `active` |
| `source` | 可选 | 依据数组，两种形式：外部 URL，或领域内相对路径 `<file>#<标题文本>` |
| `applies_to` | 可选 | 技术栈、版本或场景边界数组 |
| `reviewed_at` | 可选 | 最近审阅日期，ISO 格式 `YYYY-MM-DD` |
| `owner` | 可选 | 维护责任主体（团队而非个人） |

可选字段是渐进引入的治理元数据：未填不报错，填了必须合法。`check_index.py` 校验全部字段的类型与枚举取值。

### level 与 enforcement 的分工

两个字段回答不同问题，不可互相替代：

- **`level` 回答"违反有多严重"**——由正文措辞决定：「必须/禁止」→ `MUST`，「应该/不应」→ `SHOULD`，「可以/建议」→ `MAY`。
- **`enforcement` 回答"靠什么拦住"**——由该规则能否被工具无歧义判定决定。

| `enforcement` | 判定标准 | 典型例子 |
|---|---|---|
| `ci` | 存在可自动执行的检查机制（正则校验、静态分析规则、平台保护规则、扫描器），工具能无歧义判定通过与否 | 分支名格式、Conventional Commits 格式、tag 命名、secret scanning |
| `review` | 需人工判断内容质量或变更意图，工具无法可靠判定 | PR 描述是否讲清背景与验证方式、版本号语义是否判断正确、是否绕过了 hook |
| `advisory` | 建议性做法，不作为拦截依据 | CODEOWNERS 配置、onboarding 阅读顺序 |

**一个小节内混有不同级别的条款时，`level` 取该小节最强条款的级别**（实测 76% 的条目属此情形）。这是对消费者安全的默认——不会把强制条款误判为推荐；但反过来，命中一条 `MUST` 条目不代表该小节每句话都是硬性要求，消费者仍需按 `file` + `anchor` 打开正文读具体措辞。这也是"索引只做定位、不复制正文"原则的直接后果。

约束：`level: MAY` 的条目不得标 `enforcement: ci`——可选做法不应作为 CI 拦截依据，该组合由校验器报错。

### source：规则到理由的连接

规范条款只写"要做什么、不能做什么"，**理由、选型对比、例外场景由 `reference/` 承载**——这是 `rules/` 与 `reference/` 分层的目的。`source` 把这层关系登记成可检索的数据，让消费者能从一条规则反查到它的依据，而不必靠人工在两个目录间猜对应关系。

- 内部依据写 `<file>#<标题文本>`（如 `reference/commit-message-tooling.md#2.3 为什么不能靠"团队自觉"代替 hook`），路径相对领域根目录，与 `file` 字段同一形式。
- 外部依据写完整 URL（如 `https://www.conventionalcommits.org/`）。
- `check_index.py` 校验内部引用的文件与锚点真实存在；URL 不做离线校验。因此**迁移 `reference/` 文件或改其标题时，`source` 也是需要同步的引用之一**。
- 规则本身自解释、无独立理由文档时不填——`source` 未填不代表缺失，不追求 100% 覆盖。

## 索引粒度规范

粒度不均会让动态检索在不同领域的召回能力不可比较，因此统一如下判断标准：

- **可独立判断的规则原则上单独登记一条**：一条规则若能脱离上下文单独用于合规判断（"断言库须团队统一"、"脚本禁止交互提示"），就应有自己的索引条目，锚点指向其所在小节。
- **导航性标题不作为规则登记**：领域 README 的阅读路径、文件地图、"权威参考"等章节是导航，不承载判断依据，不登记。
- **reference 可按文档或按独立主题登记**：描述性文档以整篇为单位登记是被认可的做法（media、dotnet 领域即如此）；仅当一篇 reference 内部存在多个会被独立检索的主题时，才拆成多条。因此审计报告的覆盖率**只统计 `rule` 类文件**，不对 reference 计算标题覆盖率。
- **文件级汇总条目与节级条目可以并存**：早期以整篇为单位登记的 `rule` 条目（如 `skill-authoring.01.format`）已被消费者按文件引用，补充节级条目时保留它作为文件入口，不改 ID——改 ID 属破坏性变更。
- 覆盖率用 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" --audit` 查看，输出每个规范文件的 `indexed / eligible_headings`。

## 维护约定

- 新增/修改一条规范/reference 时，同一次提交里必须同步更新对应 `index.jsonl`。
- 改动后运行 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>` 做一致性自检（脚本随 `knowledge-base-maintain` skill 分发）。校验分两类作用域：
  - **单领域检查**（传参）：该领域的 schema、字段枚举、`id` 格式、`file` 存在与路径越界、`anchor` 匹配、孤儿文件。
  - **全局检查**（始终执行，即使只传一个领域）：`id` 全局唯一、`id` 前缀与领域归属一致、`catalog.json` 与实际领域双向一致。
- 加 `--audit` 输出健康报告（记录数、`kind`/`level` 分布、规范文件的标题索引覆盖率、孤儿文件）。
- 规范条款可选择性引用 `reference/*.md` 加强依据；引用单向，reference 不反向声明被谁引用。
- 版本号见本文件顶部，变更规则与 CHANGELOG 格式见 `CHANGELOG.md`；日常新增/修改建议通过 `/knowledge-base-maintain` skill 完成，会自动同步索引与版本号。
- 不做自动生成索引的脚本——`tags`/`summary`/`level` 需要语义判断，机械提取质量不可靠。
- 索引覆盖是渐进式的，不要求一次性覆盖全部规范文件——新增/优化 skill 引用到某条规则时，若该规则尚未登记索引，随手补一行即可，不必专项排期回填。
- 迁移或重命名规范/reference 文件时，必须同步更新五处：索引 `file` 字段、索引 `source` 字段中的内部引用、领域 README 文件地图、正文交叉引用、消费者 skill 的引用路径（含 Markdown 链接目标）。

## 与仓库已有资产的关系

- `plugins/optimus-backend-plugin/skills/csharp-code-review`：审查规则以 `knowledge-base/csharp/` 为准，见该 skill 的"权威参考"章节。
- `plugins/optimus-frontend-plugin/skills/wpf-code-review`、`wpf-project-conventions`：代码审查与项目结构判断依据见 `knowledge-base/wpf/`。
- `.claude/rules/skill-conventions.md`：skill 的仓库专属约定（版本号、author、category、前置校验、需求预告、CHANGELOG、README）；通用规范引用 `knowledge-base/skill-authoring/`。
