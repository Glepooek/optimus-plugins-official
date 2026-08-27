# knowledge-base 优化计划

> 状态：已提出，待按优先级实施。本文记录 2026-08-27 对当前知识库的评估结论与详细优化方案；实施后的实际状态以 `knowledge-base/README.md`、`knowledge-base/CHANGELOG.md` 与代码为准。

**Goal:** 在保留当前“领域文档 + JSONL 索引 + 维护 skill”总体架构的前提下，提升知识库的规则可信度、检索一致性、自动校验能力和持续维护能力。

**Current baseline:** 当前包含 `dotnet`、`csharp`、`wpf`、`git`、`media`、`skill-authoring` 六个领域；新增 `dotnet` 领域后，原有 284 条索引记录之外新增 1 条 reference 索引，现有一致性校验通过。当前主要问题不是目录无法使用，而是治理深度不足：规则强度偏高、索引粒度不均、校验覆盖面较窄、语义质量缺少可持续度量。

**Scope:** 本计划覆盖知识库目录与元数据、各领域规范内容、索引校验脚本、`knowledge-base-maintain` skill、CI 接入和消费者影响分析。不在本计划中重做知识库目录，不立即批量改写所有历史条目，也不把描述性 reference 强行改成规范条款。

**Architecture decision:** 采纳“领域下按内容类型分目录”的方向。每个领域的规范、reference 和后续新增内容分类均作为同级目录管理；领域说明文件和索引仍保留在领域根目录，避免把导航元数据混入某一类内容。新增 `dotnet` 领域，负责 Runtime、.NET Framework、SDK、目标框架、操作系统兼容性与生命周期；`csharp` 负责语言和通用工程实践；`wpf` 负责 WPF/XAML 桌面 UI 技术栈。该调整需要在实施前先完成路径与引用影响分析，再一次性迁移，不能只移动正文而遗漏索引、skill 引用和文档链接。

## 已确认的问题

### P0：规则语义与治理

1. `MUST` 使用比例过高：C# 记录中 107 条为 `MUST`、10 条为 `SHOULD`；WPF 132 条全部为 `MUST`；Git 11 条为 `MUST`、1 条为 `SHOULD`。
2. `MUST` 在领域 README 中被定义为 CI / review 拦截，但部分条目更像推荐实践或需要场景判断的设计偏好。
3. 索引只有 `level`，没有表达规则如何执行，无法区分 CI、review 和 advisory。
4. 部分规则包含具体性能数字、框架行为或工具结论，但缺少统一的测量条件、适用版本和来源元数据。

### P1：索引与检索

1. 现有脚本主要验证 `file`、`anchor` 和 ID 唯一性，无法发现 schema 错误、孤儿文件、无效 domain、空摘要、非法 level 等问题。
2. 单领域运行脚本时不会发现跨领域重复 ID；README 又规定 ID 全局唯一，实际约束不完整。
3. 索引粒度不一致：C# `12-testing.md` 约有 30 个标题但仅登记 10 条；Skill Authoring 多数规范文件仅登记 1 条；WPF 相对细粒度；Media 主要采用文档级 reference 索引。
4. 当前“校验通过”只能证明索引指向存在，不能证明动态检索能召回所有需要独立判断的规则。

### P2：内容结构与维护流程

1. 规范条目没有统一要求“适用范围、例外、理由、验证方式、正反例”等字段或章节。
2. reference 有较好的文档化实践，但来源、审阅日期、适用版本、事实验证方式未形成统一元数据约定。
3. 维护 skill 已覆盖新增、修改、迁移、校验，但缺少 audit、coverage、impact、deprecate、dry-run 等维护型能力。
4. 维护 skill 的提交说明与仓库要求的 `commit-cc-plugin` 流程需要统一，避免提交路径判断不一致。

## 设计原则

- 保留领域目录和 JSONL 的核心架构，不为解决索引问题引入数据库。
- 原始 Markdown 继续作为正文唯一真相源，索引只承载检索和治理元数据。
- 自动化负责结构、一致性和可追溯性；规则级别、语义重复和规范冲突保留人工判断。
- 先建立校验与度量，再批量调整规则级别，避免在不可观测的情况下大规模改写。
- 规则优先服务实际消费者 skill，所有影响消费者的修改必须做影响分析。
- 每一阶段都必须有可执行验收命令，不能只以“文档看起来更完整”为完成标准。

## 目标目录结构

领域目录采用“元数据在根、内容按类型分组”的结构：

```text
knowledge-base/
├── README.md
├── CHANGELOG.md
└── <domain>/
  ├── README.md             # 领域说明、阅读路径、分类说明
  ├── index.jsonl            # 领域统一索引
  ├── rules/                 # MUST / SHOULD / MAY 规范文件
  │   ├── 01-*.md
  │   └── ...
  ├── reference/             # 描述性引用文档
  │   └── *.md
  └── <future-category>/     # 后续新增分类，按用途建立同级目录
    └── *.md
```

目录约束：

- `README.md`、`index.jsonl` 是领域元数据，始终位于领域根目录。
- `rules/` 只放可用于合规判断的规范正文；文件编号在 `rules/` 内继续保持现有顺序。
- `reference/` 只放解释概念、机制、工具和用法的描述性文档，不因移动目录改变其内容性质。
- 后续分类必须先定义用途、内容语气、索引 `kind` 和生命周期规则，再建立目录；不能把“其他”作为长期无语义的收容目录。
- 索引的 `file` 始终是相对领域根目录的路径，例如 `rules/05-error-handling.md` 或 `reference/video-codecs.md`。
- 分类目录迁移必须同步更新 Markdown 内部链接、插件 skill 引用、领域 README 文件地图、索引记录和 CHANGELOG。

分类命名建议使用稳定的内容语义：`rules`、`reference`、`examples`、`decisions`、`playbooks` 等；只有在出现真实内容和明确消费场景后才新增分类，避免预建空目录。

## 目标数据模型

在现有字段基础上保留兼容性，并增加可选治理字段：

```json
{
  "id": "csharp.05.no-silent-catch",
  "kind": "rule",
  "level": "MUST",
  "enforcement": "review",
  "file": "05-error-handling.md",
  "anchor": "4. 捕获边界与过滤",
  "title": "禁止静默吞异常",
  "tags": ["exception", "logging"],
  "summary": "catch 块内必须有实质处理。",
  "status": "active",
  "applies_to": [".NET"],
  "source": [],
  "reviewed_at": "2026-08-27",
  "owner": "desktop client team"
}
```

字段约定：

- 必填字段继续为 `id`、`kind`、`file`、`anchor`、`title`、`tags`、`summary`；`rule` 必须有 `level`。
- `enforcement` 取 `ci`、`review`、`advisory`，未迁移的旧记录可暂时省略。
- `status` 取 `active`、`deprecated`、`experimental`。
- `source` 为公开来源 URL 数组；内部经验允许填写 ADR、issue 或 PR 路径。
- `applies_to` 表达技术栈、版本或场景边界；`reviewed_at` 用 ISO 日期。
- `owner` 表达维护责任主体，不要求绑定个人。

## 实施阶段

### Phase 0：建立基线与保护网（P0）

**目标：** 在任何大规模内容调整前，建立可重复的健康检查和现状快照。

**任务：**

- [ ] 增加统一的知识库审计命令入口，默认扫描所有含 `index.jsonl` 的领域。
- [ ] 为现有 284 条记录生成基线报告：记录数、规则级别分布、reference 比例、每个文件的索引覆盖率、孤儿文件和校验问题。
- [ ] 将现有索引校验测试扩展为 schema、枚举、ID 格式、跨领域 ID 唯一性、文件路径越界和空值检查。
- [ ] 明确单领域检查与全局检查的区别：全局检查负责 ID、领域归属和目录清单；单领域检查负责该领域文件与锚点。

**涉及文件：**

- `.claude/skills/knowledge-base-maintain/scripts/check_index.py`
- `.claude/skills/knowledge-base-maintain/scripts/test_check_index.py`
- `.claude/skills/knowledge-base-maintain/SKILL.md`
- `.kiro/skills/knowledge-base-maintain/`、`.agents/skills/knowledge-base-maintain/`（镜像验证）

**验收：**

```text
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
```

检查器应能对故意构造的非法 JSON、缺字段、非法枚举、重复 ID、越界路径、孤儿文件返回非零退出码，并对当前仓库返回成功。

### Phase 1：统一索引粒度与根目录目录册（P1）

**目标：** 让动态检索在不同领域具有可比较的召回能力。

**任务：**

- [ ] 先盘点每个领域的内容类型与现有引用，确认 `rules/`、`reference/` 及未来分类的迁移边界。
- [ ] 将当前各领域根目录下的规范文件迁移到 `<domain>/rules/`；保留 `README.md` 与 `index.jsonl` 在领域根目录。
- [ ] 保持 `reference/` 与 `rules/` 同级；已有 reference 不改变内容，只更新相对路径。
- [ ] 更新所有 `file` 字段、领域 README 文件地图、规范正文交叉引用、插件 skill 引用和历史计划中的当前状态说明。
- [ ] 在 `knowledge-base/README.md` 增加索引粒度规范：可独立判断的规则原则上单独登记；README 的导航标题不作为规则；reference 可按文档或独立主题登记。
- [ ] 新增根级 `knowledge-base/catalog.json`，登记 domain、内容类型、维护者、状态、版本、主要消费者和最近审阅日期。
- [ ] 补齐 C# `12-testing.md` 的细粒度条目，优先覆盖测试隔离、集成测试、测试框架、mock 边界和命令等独立判断项。
- [ ] 补齐 `skill-authoring` 的细粒度条目，至少将格式、描述、评估、脚本和最佳实践章节拆成可独立检索的规则。
- [ ] 复核 Git、WPF 与 C# 中同主题条目的重复索引和跨领域边界，保留通用规则在通用领域，技术特有规则留在技术领域。

**验收：**

- 每个领域输出 `indexed_headings / eligible_headings` 覆盖率。
- 每个领域根目录只保留领域说明与索引；所有规范正文位于 `rules/`，`reference/` 与 `rules/` 同级。
- 全仓库不再存在指向旧规范路径的失效链接，且索引校验能正确解析 `rules/` 和 `reference/` 下的文件。
- 对 C# 测试和 Skill Authoring 的典型关键词进行检索，能够命中对应独立条目。
- `catalog.json` 中每个实际领域都有一条记录，且目录中的领域都能被审计命令发现。

### Phase 2：规则内容质量治理（P0/P1）

**目标：** 让规则的强度、适用边界和执行方式可解释。

**任务：**

- [ ] 逐领域复核 `MUST` 条目，建立调整清单：保留硬性约束、降为 `SHOULD`、改为 `MAY`，或拆分为“硬约束 + 推荐实践”。
- [ ] 优先审查 WPF 全部 `MUST` 条目，以及 C# / Git 中明显属于风格偏好的条目。
- [ ] 为规则索引增加 `enforcement`，区分 `ci`、`review`、`advisory`。
- [ ] 为高风险或有争议的规则补充“适用范围、例外、理由、验证方式”。
- [ ] 为包含性能数字、框架版本行为和工具能力判断的条目补充来源、测量条件或适用版本。
- [ ] 对同主题重复规则建立人工审查表，特别关注 C# / WPF 的 async、异常、测试、依赖管理和安全条款。

**内容模板：**

```markdown
## 条目标题

### 规则
必须 / 应该 / 可以……

### 适用范围
适用于……；不适用于……

### 例外
以下情况可例外，例外需要记录……

### 理由
……

### 验证方式
通过 CI、review 或专项测试验证……

### 正例 / 反例
……
```

**验收：**

- 每个领域完成一轮级别复核并有变更记录。
- 新增的 `enforcement`、`source`、`applies_to` 等字段通过 schema 校验。
- 任意一条被降级或升级的规则，都能在 CHANGELOG 中说明语义变化和影响范围。

### Phase 3：增强 knowledge-base-maintain skill（P1）

**目标：** 将 skill 从“条目写入向导”升级为“知识库生命周期维护工具”。

**新增场景：**

- [ ] `audit`：全领域健康报告。
- [ ] `coverage`：索引粒度和文件覆盖率统计。
- [ ] `schema-check`：仅执行结构校验。
- [ ] `link-check`：检查 Markdown 本地链接、索引引用和 skill 引用。
- [ ] `impact`：按文件、条目 ID、tag 反查消费者 skill 和受影响文档。
- [ ] `deprecate`：标记条目废弃，要求填写替代条目和迁移说明，不直接删除历史。
- [ ] `dry-run`：展示正文、索引、版本号和 CHANGELOG 的预期变化，不写文件。
- [ ] `find-duplicates`：报告疑似重复或冲突条目，结果交由人工确认。

**流程增强：**

- [ ] 新增条目时先检查近似标题、tag 和 summary，降低重复建设。
- [ ] 修改条目时自动列出引用该文件或 ID 的 skill。
- [ ] 版本升级前要求明确变更类型：新增、兼容修改、破坏性修改、废弃。
- [ ] 仅校验场景默认执行全局检查，而不是只检查用户偶然指定的单个领域。
- [ ] 统一提交规则，明确涉及仓库提交或推送时遵循仓库要求的 `commit-cc-plugin` 流程。

**验收：**

- 新增、修改、迁移、废弃、审计、预演六类场景均有明确输入、输出和失败处理。
- `.claude/skills/` 是唯一正文来源，`.kiro/skills/` 与 `.agents/skills/` 镜像内容一致。
- 使用不存在的 domain、重复 ID、无替代条目的废弃操作时能阻断并给出修复提示。

### Phase 4：消费者接入与影响分析（P1/P2）

**目标：** 让知识库的规则真的约束和改善下游 skill，而不是只作为文档存储。

**任务：**

- [ ] 审查所有 `plugins/*/skills/` 对知识库的引用，确认路径、锚点和规则范围准确。
- [ ] 为主要消费者建立“规则 ID → skill”反向清单，至少覆盖 `csharp-code-review`、`wpf-code-review` 和 media 插件族。
- [ ] 对 C# / WPF review skill 的 checklist 做引用覆盖测试，确认每个审查类别至少关联一个有效规则。
- [ ] 对 media skill 现有引用继续保持“知识库负责概念，skill 负责操作”的分层，避免将命令模板重新复制回 reference。
- [ ] 规则变更时在审计结果中报告受影响的 skill、README 和交叉引用。

**验收：**

- 任意索引条目都能反查引用它的消费者；没有失效的知识库路径或锚点。
- 关键消费者的最小触发/引用测试通过，且不会因知识库文档重排而静默失效。

### Phase 5：CI 与持续运营（P2/P3）

**目标：** 将一致性检查变成合并前的稳定门禁，将语义质量变成可跟踪指标。

**任务：**

- [ ] 将全领域 schema、索引、链接、孤儿文件检查接入 CI。
- [ ] 在 CI 中保留 `unittest`，不引入仓库当前不存在的 pytest 依赖。
- [ ] 生成机器可读 JSON 审计报告，供后续 dashboard 或 PR 评论使用。
- [ ] 每月或每个版本周期复核过期条目、外部来源、技术版本和高风险 MUST 规则。
- [ ] 每季度统计知识库指标：索引覆盖率、无 owner 条目数、过期条目数、重复候选数、被消费者引用的条目比例。

**验收：**

- 修改正文但未同步索引、破坏本地链接、引入非法元数据时 CI 失败。
- CI 失败输出包含文件、条目 ID、问题类型和修复建议。
- 审计报告可用于比较两个版本之间的条目新增、修改、废弃和覆盖率变化。
