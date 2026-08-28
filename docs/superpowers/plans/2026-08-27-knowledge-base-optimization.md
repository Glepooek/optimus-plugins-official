# knowledge-base 优化计划

> **状态：已部分实施，本文已于 2026-08-28 复核并标注现状。**
>
> 本文是**历史决策记录**，不再是待执行的任务清单。2026-08-27 提出时的 baseline 与部分诊断已经失效，照原文继续执行会基于错误前提工作。当前真实状态以 `knowledge-base/README.md`、`knowledge-base/CHANGELOG.md` 与 `check_index.py` 为准。
>
> **复核结论摘要（2026-08-28）：**
>
> | Phase | 判定 | 说明 |
> |---|---|---|
> | Phase 0 | ✅ 已交付 | 66 个单测覆盖全部验收项，`check_index.py` 326 条通过 |
> | Phase 1 | ✅ 已交付 | `rules/`+`reference/` 分目录、`catalog.json`、粒度规范均已落地；粒度不均已解决 |
> | Phase 2 | ⚠️ 部分交付，部分废弃 | git 领域治理元数据试点已完成；**「MUST 过高」诊断已被实测证伪**，**内容模板已废弃** |
> | Phase 3 | ⚠️ 8 项中 2 项值得做 | `audit`/`coverage`/提交流程已交付；`deprecate`、`find-duplicates` 值得做；其余不必要 |
> | Phase 4 | ❌ 大部分为伪需求 | 无失效引用；消费者不按 ID 引用，反查清单无收益。**但发现文档未提及的真实风险，见该节** |
> | Phase 5 | ❌ 不属本计划范围 | 仓库无任何 CI 基础设施，「接入 CI」是全仓库级决策，量级不同 |
>
> **baseline 失效对照：** 原文称「284 + 1 = 285 条索引」，2026-08-28 实测为 **326 条**（rule 307 / reference 19）。

**Goal:** 在保留当前"领域文档 + JSONL 索引 + 维护 skill"总体架构的前提下，提升知识库的规则可信度、检索一致性、自动校验能力和持续维护能力。

**Current baseline（提出时，已失效）:** 当前包含 `dotnet`、`csharp`、`wpf`、`git`、`media`、`skill-authoring` 六个领域；新增 `dotnet` 领域后，原有 284 条索引记录之外新增 1 条 reference 索引，现有一致性校验通过。当前主要问题不是目录无法使用，而是治理深度不足：规则强度偏高、索引粒度不均、校验覆盖面较窄、语义质量缺少可持续度量。

> 复核批注：「规则强度偏高」与「索引粒度不均」两项判断均已失效，见「已确认的问题」节的批注。「校验覆盖面较窄」已通过 Phase 0 解决。

**Scope:** 本计划覆盖知识库目录与元数据、各领域规范内容、索引校验脚本、`knowledge-base-maintain` skill、CI 接入和消费者影响分析。不在本计划中重做知识库目录，不立即批量改写所有历史条目，也不把描述性 reference 强行改成规范条款。

**Architecture decision:** 采纳“领域下按内容类型分目录”的方向。每个领域的规范、reference 和后续新增内容分类均作为同级目录管理；领域说明文件和索引仍保留在领域根目录，避免把导航元数据混入某一类内容。新增 `dotnet` 领域，负责 Runtime、.NET Framework、SDK、目标框架、操作系统兼容性与生命周期；`csharp` 负责语言和通用工程实践；`wpf` 负责 WPF/XAML 桌面 UI 技术栈。该调整需要在实施前先完成路径与引用影响分析，再一次性迁移，不能只移动正文而遗漏索引、skill 引用和文档链接。

## 已确认的问题

### P0：规则语义与治理

> **复核批注（2026-08-28）：下方第 1、2 条已被实测证伪，保留原文仅作历史记录，不得作为行动依据。**
>
> 原文由「WPF 132 条全 MUST」推断出「规则被过度强化」。CHANGELOG 3.0.0 记录的实测结论是：**76% 的索引条目所在小节混有不同级别条款，`level` 取该小节最强条款的级别**——这是索引粒度与条款级别粒度不匹配，不是规则本身被写强，也是"索引只做定位、不复制正文"原则的直接后果。
>
> 2026-08-28 抽样 8 条 WPF `MUST` 复验：全部为真实硬约束（UI 线程访问铁律、禁止 `.Result` 同步等待致死锁、长列表必须虚拟化、`TargetFramework` 必含 `-windows` 后缀），无一条属于风格偏好。

1. ~~`MUST` 使用比例过高：C# 记录中 107 条为 `MUST`、10 条为 `SHOULD`；WPF 132 条全部为 `MUST`；Git 11 条为 `MUST`、1 条为 `SHOULD`。~~（已证伪：级别取值正确，是索引粒度问题）
2. ~~`MUST` 在领域 README 中被定义为 CI / review 拦截，但部分条目更像推荐实践或需要场景判断的设计偏好。~~（已证伪：抽样未发现此类条目）
3. 索引只有 `level`，没有表达规则如何执行，无法区分 CI、review 和 advisory。 → ✅ **已解决**：`enforcement` 字段已加入 schema 与校验器，git 领域 12 条覆盖率 100%；其余 295 条待推广（见 Phase 2 批注）。
4. 部分规则包含具体性能数字、框架行为或工具结论，但缺少统一的测量条件、适用版本和来源元数据。 → ⚠️ **部分解决**：`source`、`applies_to`、`reviewed_at` 字段已就位并被校验，git 领域 8 条已填；其余领域待推广。

### P1：索引与检索

> **复核批注（2026-08-28）：第 1、2、3 条均已解决。**

1. ~~现有脚本主要验证 `file`、`anchor` 和 ID 唯一性，无法发现 schema 错误、孤儿文件、无效 domain、空摘要、非法 level 等问题。~~ → ✅ **已解决**：`check_index.py` 443 行，含 schema/枚举/ID 格式/路径越界/孤儿文件/catalog 一致性/`source` 内部引用校验，66 个单测全绿。
2. ~~单领域运行脚本时不会发现跨领域重复 ID~~ → ✅ **已解决**：全局 ID 池排除目标领域自身，单领域模式下也能检出跨领域冲突（`test_detects_cross_domain_duplicate_when_checking_one_domain`）。
3. ~~索引粒度不一致：C# `12-testing.md` 约有 30 个标题但仅登记 10 条；Skill Authoring 多数规范文件仅登记 1 条~~ → ✅ **已解决**：`12-testing.md` 现为 17 条（121%），`skill-authoring` 5 个 rules 文件全部 100%。当前覆盖率 git 100% / skill-authoring 100% / wpf 94.3% / csharp 82.6%。**csharp 12 个文件未满仍是真实缺口**（最低 `07-performance.md` 55%）。
4. 当前"校验通过"只能证明索引指向存在，不能证明动态检索能召回所有需要独立判断的规则。 → ⚠️ **仍然成立**：`--audit` 已能输出覆盖率作为代理指标，但召回质量本身仍无自动度量手段。

### P2：内容结构与维护流程

1. ~~规范条目没有统一要求"适用范围、例外、理由、验证方式、正反例"等字段或章节。~~ → ❌ **已废弃该方向**，见 Phase 2 的内容模板批注。
2. reference 有较好的文档化实践，但来源、审阅日期、适用版本、事实验证方式未形成统一元数据约定。 → ⚠️ **部分解决**：字段约定已在 README 落地，实际填写仅覆盖 git 领域。
3. 维护 skill 已覆盖新增、修改、迁移、校验，但缺少 audit、coverage、impact、deprecate、dry-run 等维护型能力。 → ⚠️ **部分解决**：`audit`、`coverage` 已实现；`deprecate`、`find-duplicates` 仍缺且值得补；`impact`、`link-check`、`dry-run` 经评估不必要（见 Phase 3 批注）。
4. ~~维护 skill 的提交说明与仓库要求的 `commit-cc-plugin` 流程需要统一~~ → ✅ **已解决**：SKILL.md Step 7 已明确一律走 `commit-cc-plugin`。

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

### Phase 0：建立基线与保护网（P0）— ✅ 已交付

> **复核（2026-08-28）：全部验收项已达成。** `check_index.py` 443 行，66 个单测全绿，326 条记录校验通过。单测覆盖 schema、枚举、ID 格式、跨领域重复（含单领域模式）、路径越界、孤儿文件、覆盖率、`catalog.json` 一致性、`source` 内部引用解析。`--audit` 已实现全领域健康报告。

**目标：** 在任何大规模内容调整前，建立可重复的健康检查和现状快照。

**任务：**

- [x] 增加统一的知识库审计命令入口，默认扫描所有含 `index.jsonl` 的领域。
- [x] 为现有 284 条记录生成基线报告：记录数、规则级别分布、reference 比例、每个文件的索引覆盖率、孤儿文件和校验问题。
- [x] 将现有索引校验测试扩展为 schema、枚举、ID 格式、跨领域 ID 唯一性、文件路径越界和空值检查。
- [x] 明确单领域检查与全局检查的区别：全局检查负责 ID、领域归属和目录清单；单领域检查负责该领域文件与锚点。

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

### Phase 1：统一索引粒度与根目录目录册（P1）— ✅ 已交付（剩 csharp 覆盖率一项）

> **复核（2026-08-28）：架构调整与粒度治理均已落地，实际结果优于原文预期。**
>
> - `rules/` + `reference/` 分目录已完成（CHANGELOG 2.0.0，44 文件 `git mv`，266 条 `file` 字段更新）
> - `catalog.json` 已建，且含原文未要求的 `consumers` 字段，为影响分析预留了基础
> - 索引粒度规范已写入 `knowledge-base/README.md`（`## 索引粒度规范` 章节，4 条判断标准）
> - 原文担心的粒度不均已解决：`csharp/rules/12-testing.md` 从「30 标题仅 10 条」变为 **17 条 / 121%**；`skill-authoring` 从「多数文件仅 1 条」变为 **5 个 rules 文件全部 100%**
>
> **唯一剩余缺口：csharp 覆盖率 82.6%**，12 个文件未满（`07-performance.md` 55%、`09-data-access.md` 67%、`13-api-design.md` 71% 等）。属日常补条目工作，不需要「Phase」规格。

**目标：** 让动态检索在不同领域具有可比较的召回能力。

**任务：**

- [x] 先盘点每个领域的内容类型与现有引用，确认 `rules/`、`reference/` 及未来分类的迁移边界。
- [x] 将当前各领域根目录下的规范文件迁移到 `<domain>/rules/`；保留 `README.md` 与 `index.jsonl` 在领域根目录。
- [x] 保持 `reference/` 与 `rules/` 同级；已有 reference 不改变内容，只更新相对路径。
- [x] 更新所有 `file` 字段、领域 README 文件地图、规范正文交叉引用、插件 skill 引用和历史计划中的当前状态说明。
- [x] 在 `knowledge-base/README.md` 增加索引粒度规范：可独立判断的规则原则上单独登记；README 的导航标题不作为规则；reference 可按文档或独立主题登记。
- [x] 新增根级 `knowledge-base/catalog.json`，登记 domain、内容类型、维护者、状态、版本、主要消费者和最近审阅日期。
- [x] 补齐 C# `12-testing.md` 的细粒度条目，优先覆盖测试隔离、集成测试、测试框架、mock 边界和命令等独立判断项。
- [x] 补齐 `skill-authoring` 的细粒度条目，至少将格式、描述、评估、脚本和最佳实践章节拆成可独立检索的规则。
- [x] 复核 Git、WPF 与 C# 中同主题条目的重复索引和跨领域边界，保留通用规则在通用领域，技术特有规则留在技术领域。（CHANGELOG 3.0.0 完成 git ↔ csharp 去重，解开语义环）
- [ ] **（剩余）** 补齐 csharp 12 个未满文件的细粒度条目，把领域覆盖率从 82.6% 提升到与 wpf（94.3%）可比的水平。

**验收：**

- 每个领域输出 `indexed_headings / eligible_headings` 覆盖率。
- 每个领域根目录只保留领域说明与索引；所有规范正文位于 `rules/`，`reference/` 与 `rules/` 同级。
- 全仓库不再存在指向旧规范路径的失效链接，且索引校验能正确解析 `rules/` 和 `reference/` 下的文件。
- 对 C# 测试和 Skill Authoring 的典型关键词进行检索，能够命中对应独立条目。
- `catalog.json` 中每个实际领域都有一条记录，且目录中的领域都能被审计命令发现。

### Phase 2：规则内容质量治理（P0/P1）— ⚠️ 部分交付，部分废弃

> **复核（2026-08-28）：**
>
> **已交付**（CHANGELOG 3.0.0，git 领域试点）：12 条 rule 治理元数据覆盖率 100%（`enforcement` `ci`8/`review`3/`advisory`1、`status`、`applies_to`、`reviewed_at`、`owner`）；8 条补 `source`；README 新增「level 与 enforcement 的分工」「source：规则到理由的连接」两章。
>
> **已废弃 1——MUST 级别复核**：原文的「逐领域复核 MUST」「优先审查 WPF 全部 MUST」建立在已被证伪的诊断上（见「已确认的问题」P0 批注），不执行。
>
> **已废弃 2——内容模板**：原文要求每条规则正文补「适用范围/例外/理由/验证方式/正反例」六小节，全库 0 处落地，且不应落地。理由：307 条 rule、正文共 4765 行，按模板扩写将膨胀至约 2 万行；更关键的是「理由」会与 `reference/` 重复成两份需同步的同一事实——正是 3.0.0 刚花力气解开的语义环。**实际采用的替代方案**是既有分层：规范给约束、`reference/` 给理由、索引 `source` 字段做连接（形式 `<file>#<标题文本>`，由校验器验证真实存在）。
>
> **仍待执行**：把治理元数据从 git 推广到其余 295 条 rule（当前全库 `enforcement` 覆盖率 3.9%）。
>
> **推广决策与已知权衡（2026-08-28 确认推广）**：本仓库无任何 CI，也未启用 git hook，因此 `enforcement` 对**本仓库自身**不产生实际拦截，是声明性元数据。推广的价值在于**外部消费者**——知识库面向的是照此规范开发的项目，那些项目有 CI，`enforcement` 为它们提供「哪些规则该进 CI、哪些只需 review」的分档依据。需注意 git 领域已标的 8 条 `ci` 指的是被审查项目的 CI，不是本仓库的。

**目标：** 让规则的强度、适用边界和执行方式可解释。

**任务：**

- [x] ~~逐领域复核 `MUST` 条目，建立调整清单~~ →（已废弃，诊断被证伪）
- [x] ~~优先审查 WPF 全部 `MUST` 条目，以及 C# / Git 中明显属于风格偏好的条目~~ →（已废弃，抽样未发现此类条目）
- [x] 为规则索引增加 `enforcement`，区分 `ci`、`review`、`advisory`。（字段与校验已就位；git 领域已填）
- [x] ~~为高风险或有争议的规则补充"适用范围、例外、理由、验证方式"~~ →（内容模板方向已废弃，改由 `source` 指向 `reference/` 承载理由）
- [x] 为包含性能数字、框架版本行为和工具能力判断的条目补充来源、测量条件或适用版本。（git 领域 8 条已填 `source`、12 条已填 `applies_to`）
- [x] 对同主题重复规则建立人工审查表，特别关注 C# / WPF 的 async、异常、测试、依赖管理和安全条款。（3.0.0 已完成 git ↔ csharp；C# ↔ WPF 尚未做，见下方剩余项）
- [ ] **（剩余，已确认执行）** 将治理元数据推广到其余 295 条 rule：`enforcement`、`status`、`applies_to`、`reviewed_at`、`owner`；`source` 按「规则不自解释时才填」的既定约定补，不追求 100%。
- [ ] **（剩余）** 复核 C# ↔ WPF 跨领域重复：两领域在 async、异常、测试、依赖管理、安全上均有条款，需按语义反查而非按文件比对（v1.5.0 的教训：按文件迁移会漏）。

**内容模板：**

> ⛔ **已废弃（2026-08-28）**：下方模板保留仅作历史记录，不要按它改写规范正文。原因见本节复核批注。

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

- ~~每个领域完成一轮级别复核并有变更记录。~~（已废弃）
- 新增的 `enforcement`、`source`、`applies_to` 等字段通过 schema 校验。→ ✅ 已达成
- 任意一条被降级或升级的规则，都能在 CHANGELOG 中说明语义变化和影响范围。→ ✅ 3.0.0 已按此执行

### Phase 3：增强 knowledge-base-maintain skill（P1）— ⚠️ 8 项中 2 项值得做

> **复核（2026-08-28）：** SKILL.md（v1.2.0）当前支持 3 个场景（新增 / 修改·迁移 / 仅校验）+ `--audit`。8 个提议场景逐项判定见下方任务列表。核心结论：`audit`/`coverage`/`schema-check`/提交流程已交付；`deprecate` 与 `find-duplicates` 值得补；`impact`/`link-check`/`dry-run` 经评估**不必要**，不是欠账。

**目标：** 将 skill 从"条目写入向导"升级为"知识库生命周期维护工具"。

**新增场景：**

- [x] `audit`：全领域健康报告。→ ✅ 已实现（`check_index.py --audit`，输出记录数、kind/level 分布、覆盖率、`enforcement` 分布、未满文件清单）
- [x] `coverage`：索引粒度和文件覆盖率统计。→ ✅ 已含在 `--audit` 输出中，无需独立子命令
- [x] `schema-check`：仅执行结构校验。→ ✅ 已含在默认校验（不带 `--audit` 即为纯校验）
- [ ] ~~`link-check`：检查 Markdown 本地链接、索引引用和 skill 引用。~~ → ❌ **不必要**：索引与 `source` 内部引用已被校验器覆盖；外部 URL 按 README 既定约定不做离线校验（网络依赖会让校验变成不稳定操作）
- [ ] ~~`impact`：按文件、条目 ID、tag 反查消费者 skill 和受影响文档。~~ → ⏸️ **暂不需要**：当前消费者仅 3 个 skill，Step 4 的人工 Grep 五处已够；`catalog.json` 的 `consumers` 字段已为将来工具化预留。消费者显著变多后再评估
- [ ] **（值得做）** `deprecate`：标记条目废弃，要求填写替代条目和迁移说明，不直接删除历史。→ **理由**：`status` 枚举已在校验器中（`active`/`deprecated`/`experimental`），但没有任何操作步骤会写入 `deprecated`，字段目前等于摆设
- [ ] ~~`dry-run`：展示正文、索引、版本号和 CHANGELOG 的预期变化，不写文件。~~ → ❌ **不必要**：所有改动都在 git 工作区内，`git diff` 即预览、`git restore` 即回滚，另造一套预演机制是重复建设
- [ ] **（值得做）** `find-duplicates`：报告疑似重复或冲突条目，结果交由人工确认。→ **理由**：现有 `check_duplicate_ids` 只查 `id` 字符串重复；3.0.0 的 git ↔ csharp **语义**去重全靠人工，且 v1.5.0 已留下教训「重复按语义分布，按文件迁移会漏」。这是唯一被实际踩过的痛点

**流程增强：**

- [ ] **（值得做）** 新增条目时先检查近似标题、tag 和 summary，降低重复建设。→ 与 `find-duplicates` 同源，建议一并实现
- [ ] ~~修改条目时自动列出引用该文件或 ID 的 skill。~~ → ⏸️ 同 `impact`，消费者少时人工 Grep 即可
- [x] 版本升级前要求明确变更类型：新增、兼容修改、破坏性修改、废弃。→ ✅ Step 6 已有版本表
- [x] 仅校验场景默认执行全局检查，而不是只检查用户偶然指定的单个领域。→ ✅ 不传 domain 即全局
- [x] 统一提交规则，明确涉及仓库提交或推送时遵循仓库要求的 `commit-cc-plugin` 流程。→ ✅ Step 7 已明确

**验收：**

- ~~新增、修改、迁移、废弃、审计、预演六类场景均有明确输入、输出和失败处理。~~ → 修正为：新增、修改/迁移、校验、审计、**废弃**五类（预演已废弃）
- `.claude/skills/` 是唯一正文来源，`.kiro/skills/` 与 `.agents/skills/` 镜像内容一致。→ ✅ 已达成
- 使用不存在的 domain、重复 ID、无替代条目的废弃操作时能阻断并给出修复提示。→ 前两项 ✅ 已达成；废弃阻断待 `deprecate` 实现

### Phase 4：消费者接入与影响分析（P1/P2）— ❌ 列出的任务大部分为伪需求，但漏掉了一个真实风险

> **复核（2026-08-28）：**
>
> **前提事实：** 全仓库对 `knowledge-base/` 的引用共 3 个消费者 —— `csharp-code-review`、`wpf-code-review`、`media` 插件族。逐条核对后**无任何失效路径或锚点**（2.0.0 迁移时已同步更新）。
>
> **关键发现使多数任务失效：** 两个 review skill **完全不使用条目 ID，也不读 `index.jsonl`**，它们引用的是「文件路径 + `§ 章节号`」。因此原文核心任务「建立规则 ID → skill 反向清单」缺少消费方——建了也没人查。
>
> **⚠️ 但文档漏掉了一个真实风险（比它列出的所有任务都值得做）：** review skill 引用的 `§ 章节号`**不受任何校验保护**——`check_index.py` 校验的是索引 `anchor` 的标题文本，管不到 SKILL.md 正文里的章节号引用。3.0.0 对 csharp 15 个章节重新编号时，若 skill 里的 `§ 7` 变成了别的内容，引用会**静默失效**、无任何报错。这是唯一被验证存在的真实缺口。

**目标：** 让知识库的规则真的约束和改善下游 skill，而不是只作为文档存储。

**任务：**

- [x] 审查所有 `plugins/*/skills/` 对知识库的引用，确认路径、锚点和规则范围准确。→ ✅ 已复核，3 个消费者引用全部有效
- [ ] ~~为主要消费者建立"规则 ID → skill"反向清单~~ → ❌ **伪需求**：消费者不按 ID 引用，反查清单无消费方
- [ ] ~~对 C# / WPF review skill 的 checklist 做引用覆盖测试，确认每个审查类别至少关联一个有效规则。~~ → ⏸️ **收益有限**：两个 skill 引用的是整章而非单条，"每类别至少一条规则"天然成立
- [x] 对 media skill 现有引用继续保持"知识库负责概念，skill 负责操作"的分层。→ ✅ 已保持，未出现命令模板回流
- [ ] ~~规则变更时在审计结果中报告受影响的 skill、README 和交叉引用。~~ → ⏸️ 同 Phase 3 的 `impact`，消费者仅 3 个时人工 Grep 即可
- [ ] **（新增，文档原本未列，最值得做）** 保护 review skill 中的 `§ 章节号` 引用：让 `check_index.py` 或独立脚本校验 `csharp-code-review` / `wpf-code-review` SKILL.md 里的 `§ N` 能对应到规范文件的真实章节，避免章节重编号时静默失效。

**验收：**

- ~~任意索引条目都能反查引用它的消费者~~（已废弃，无消费方）；没有失效的知识库路径或锚点 → ✅ 已达成
- ~~关键消费者的最小触发/引用测试通过~~ → 修正为：**章节号引用在规范文件重编号后能被自动检出失效**（即上方新增任务）

### Phase 5：CI 与持续运营（P2/P3）— ❌ 不属本计划范围

> **复核（2026-08-28）：**
>
> **整个仓库无任何 CI 基础设施** —— 无 `.github/workflows/`、无 `.gitlab-ci.yml`、无任何 CI 配置，也未启用 git hook。因此「把校验接入 CI」不是"优化知识库"，而是要先从零为整个仓库搭建 CI 体系，属于仓库级基础设施决策，与本计划量级不同，不应挂在知识库优化计划下执行。
>
> **需澄清一处语义混淆：** `enforcement: ci` 指的是**被审查项目的 CI**（知识库面向的下游项目），不是本仓库的 CI。git 领域已标的 8 条 `ci` 属前者。两者不要混为一谈。
>
> **当前实际做法：** 校验通过 `commit-cc-plugin` 流程中人工执行 `check_index.py` 保证，66 个单测可随时运行。在无 CI 的前提下这已是可行的最强保障。

**目标：** 将一致性检查变成合并前的稳定门禁，将语义质量变成可跟踪指标。

**任务：**

- [ ] ~~将全领域 schema、索引、链接、孤儿文件检查接入 CI。~~ → ❌ **前置条件不存在**：仓库无 CI，需先做全仓库级 CI 决策
- [x] 在 CI 中保留 `unittest`，不引入仓库当前不存在的 pytest 依赖。→ ✅ 约束已遵守（66 个单测均为 `unittest`）
- [ ] ~~生成机器可读 JSON 审计报告，供后续 dashboard 或 PR 评论使用。~~ → ⏸️ 无 CI 也无 dashboard 消费方，`--audit` 的人读输出已够
- [ ] ~~每月或每个版本周期复核过期条目、外部来源、技术版本和高风险 MUST 规则。~~ → ⏸️ `reviewed_at` 字段已就位，可支撑将来复核；定期复核制度本身需人力承诺，不宜写成技术任务
- [ ] ~~每季度统计知识库指标~~ → ⏸️ `--audit` 已能一次性输出覆盖率、`enforcement` 分布等指标，按需运行即可，不需要季度制度

**验收：**

- ~~修改正文但未同步索引、破坏本地链接、引入非法元数据时 CI 失败。~~ → 无 CI，改由 `commit-cc-plugin` 流程中人工执行校验保证
- ~~CI 失败输出包含文件、条目 ID、问题类型和修复建议。~~ → `check_index.py` 的报错输出已满足此格式要求（仅缺 CI 载体）
- ~~审计报告可用于比较两个版本之间的条目新增、修改、废弃和覆盖率变化。~~ → 版本间差异由 `knowledge-base/CHANGELOG.md` 承载

---

## 复核后的实际待办清单（2026-08-28）

上文各 Phase 的批注已把原文任务逐条判定。汇总实际仍值得做的项，按优先级排列：

| 优先级 | 事项 | 出处 |
|---|---|---|
| P0 | 治理元数据推广到其余 295 条 rule（`enforcement`/`status`/`applies_to`/`reviewed_at`/`owner`） | Phase 2 |
| P1 | 保护 review skill 的 `§ 章节号` 引用不被章节重编号静默破坏 | Phase 4（文档原未列） |
| P1 | `find-duplicates`：语义重复检测（唯一被实际踩过的痛点） | Phase 3 |
| P2 | `deprecate` 操作步骤（让 `status` 字段不再是摆设） | Phase 3 |
| P2 | csharp 覆盖率 82.6% → 与 wpf（94.3%）可比 | Phase 1 |
| P2 | C# ↔ WPF 跨领域语义去重 | Phase 2 |

原文的 `link-check`、`dry-run`、规则 ID 反查清单、CI 接入、季度指标统计均已判定为不必要或前置条件不存在，**不列入待办**。

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
