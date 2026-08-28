# Changelog

## [5.0.0] - 2026-08-28

治理元数据从 `git` 试点推广到全部规范领域：`enforcement` 填写率 3.7%（12/326）→ **100%（326/326）**。此前该字段只在 12 条 `git` 规则上有值，等于一套定义完整、有校验器保护、但实际只覆盖 3.7% 内容的元数据——消费者无法用它做任何全库判断。

按 Major 升版的原因是 `skill-authoring` 三条 `level` 由 `SHOULD` 改为 `MUST`（见下方 Changed），这是不兼容语义变化。治理字段本身的补齐是纯增量。

### Changed

- **`skill-authoring` 三条 `level` 由 `SHOULD` 修正为 `MUST`**——正文含「必须/禁止」措辞，索引却标 `SHOULD`，违反根 README 已写明的「`level` 取该小节最强条款的级别」。逐条读正文判 `enforcement` 时暴露：
  - `skill-authoring.04.self-contained`（§3 自包含脚本）：正文含「**禁止**：依赖 `node_modules`/`Gemfile` 等外部安装步骤才可运行的脚本」
  - `skill-authoring.05.gotchas`（§5.1 Gotchas 章节）：正文含两条「**必须**」（Gotchas 须放 `SKILL.md` 内；纠正后须回填）
  - `skill-authoring.05.plan-validate-execute`（§5.5 Plan-Validate-Execute）：正文含「**必须**：关键在中间的校验脚本」

  对消费者的影响：按 `level: MUST` 过滤硬性要求的消费者此前会漏掉这三条；按 `SHOULD` 检索推荐做法的消费者会少三条命中。三条的 `id`/`file`/`anchor` 均未变更，无需改引用。
- 根 README 的「可选字段是渐进引入的治理元数据」改为反映现状：`enforcement`/`status`/`applies_to`/`reviewed_at`/`owner` 已在全部 `rule` 条目填满，schema 层仍可选（漏填不报错），实际是新增条目时的约定。漏填不会被校验拦住，只会在治理数据里留空洞。
- 根 README 的 `enforcement` 判定表例子由清一色 git 场景扩为覆盖三个领域，并补入判 `ci` 的操作性检验：**工具判的是该小节的实质，还是只是它的外壳？只判外壳的填 `review`。** 原型是 `git.02.commit-hooks`——"hook 是否存在"可自动判定（外壳），但该节实质要求是"不得绕过"，只能人判。同时明确该字段的语义归属：本仓库无 CI 也无 hook，`enforcement` 对自身是声明性元数据，标 `ci` 的 130 条指的是被这些规范约束的**项目**的 CI 该拦什么。

### Added

- `csharp`（142 条）、`wpf`（132 条）、`skill-authoring`（40 条）全部 `rule` 条目补齐五个治理字段：`enforcement`、`status: active`、`applies_to`、`reviewed_at: 2026-08-28`、`owner: desktop client team`。全库 `enforcement` 分布 `ci` 130 / `review` 183 / `advisory` 13。
  - `csharp` 58 `ci`：集中在 01 章工程配置（csproj/global.json/.editorconfig/CI 顺序）、02 章命名与布局（10 条，分析器 + `.editorconfig` 主场）、04 章异步反模式（`.Result`/`.Wait()`/`async void`/`ConfigureAwait` 是 Roslyn 强项）、06 章 Dispose 模式与终结器（成套 CA 规则）、10 章依赖清单（CPM/浮动版本/包源/漏洞/许可证）、12 章测试工程形态（框架统一、命名布局、断言库、覆盖率门禁）、14 章注入与弱算法（扫描器专长）、11/17 章的日志库统一与 XML 注释完整性
  - `wpf` 51 `ci`：01/02 章工程与命名（`-windows` 后缀、Desktop workload、生成文件标记、`x:Name` 形态）、04 章 XAML 结构（命名空间、`x:Name`/`x:Key` 分工、BAML 编译）、09 章线程（Timer 类型选择、`.Result`、`async void`、`ConfigureAwait`）、13 章安全（硬编码密钥、拼接 SQL、明文 HTTP、弱哈希、签名）、14 章可访问性与本地化（`AutomationProperties` 缺失、硬编码字号与字符串、硬编码日期格式）、15 章打包（Release/版本一致/pdb/签名）、以及 06/16 章的依赖属性与 Behavior 生命周期（`DependencyProperty` 声明形态、`OnAttached`/`OnDetaching` 配对可静态检出）
  - `skill-authoring` 13 `ci`：一半是 `skills-ref validate` 直接判定的（frontmatter 六字段、目录结构、正文行数上限、相对路径引用、`uv run` 自包含脚本、禁止交互提示），另一半是 eval 流程里有明确数值门槛的（触发率阈值、train/validation 切分比例、带/不带 skill 双跑基线、benchmark delta 记录）——这类的判定标准写在规则里，脚本能核对
  - `advisory` 13 条为横向对比表与优先级排序类内容（测试框架对比、Mock 框架对比、推荐语言特性、性能优先级、弱引用适用场景等），它们不表达可拦截的约束
  - `csharp.13.repo-asset-contract` 补 `source` 指向 `reference/refit.md`。其余条目按"规则自解释时不填"的既定判据留空，`source` 不追求覆盖率
- 根 README 新增「reviewed_at：读过才填」章节：该字段语义是"正文最近一次被人实际读过并确认仍成立的日期"，不是"索引行最近编辑日期"。批量刷新而不读正文会让它变成看起来在治理、实际零保证的数字，比留空更糟。因此批量填元数据须按领域逐文件读正文，不按 `id` 列表批处理——本次即按此执行，也正是这一约束让上述三条 `level` 不符被发现。

## [4.2.0] - 2026-08-28

`csharp` 领域索引覆盖率补齐（81.8% → 96.2%，超过 `wpf` 的 94.3%）。补之前先修了覆盖率算法本身——旧算法用 `min(条目数, 二级章节数)` 封顶，只比数量不看落点，会让条目集中的文件掩盖真实空缺。

### Added

- `csharp/index.jsonl` 新增 19 条 rule 条目（124 → 143）：`05-error-handling.md` 日志与异常，`06-memory-resource.md` 弱引用/终结器，`07-performance.md` 热点路径识别/字符串/异步性能/基准测试，`08-concurrency.md` 锁选择矩阵/静态可变状态，`09-data-access.md` 数据访问基础/模型验证/数据访问测试，`10-dependency-management.md` 中央包管理（CPM），`11-observability.md` 指标与追踪/配置，`13-api-design.md` 客户端契约同步/与仓库资产，`14-security.md` 日志与脱敏，`17-comments-docs.md` 文档质量。
- 根 README 索引粒度规范新增「覆盖率不追求 100%」章节：明确覆盖率是**诊断指标而非达标指标**，列出三类有意不登记的小节（落地模板与快速上手、通篇跨章导航的小节、约束已由其他章节承载），并记录「联动 X 章」措辞是重复的可靠信号。此前该数字缺少"什么算满"的定义——把它追平会逼出两类坏条目：给操作指南强造 rule 条目，以及给已有真源的约束造第二个检索入口。

### Changed

- **`csharp/rules/13-api-design.md` §6「契约测试」去重**：该节与 `csharp.12.contract-test`（`12-testing.md` §10）互写「联动」，实则「公共契约变更配契约测试」与 12 章的「变更须跑回归」「禁止无测试保护上线」是同一约束的两次表述——两边互认权威、实则无单一真源，与 3.0.0 处理的 `git` ↔ `csharp` 语义环同型。通用条改为引用 `rules/12-testing.md` § 10. 契约测试，本节只留 API 设计侧特有的「后端契约变更须同步回归客户端契约」。`anchor` 未变更，无消费者需同步。
- 根 README 覆盖率说明补充：`anchor` 指向三级标题时其父二级章节记为已覆盖。

### Fixed

- 覆盖率统计从「条目数与章节数取小」改为按 `anchor` 落点计算。旧算法让 `csharp/rules/12-testing.md` 的 17 条记为 14/14 满分，真实只覆盖 13 个二级章节——多出的条目把另一个小节的真实空缺掩盖成了满分。修正后 `csharp` 由虚高的 82.6% 回到真实的 81.8%，差距确认为真实存在后才开始补条目。

## [4.1.0] - 2026-08-28

### Added

- 根 README 新增「status：废弃条目的过渡期」章节。此前 `status` 只在字段表里列了 `active`/`deprecated`/`experimental` 三个枚举值，没有任何关于"怎么废弃一条规则"的规定——结果全库 326 条无一使用 `deprecated`，3.0.0 废弃 `csharp.15.quality-gate-overview` 时只能直接删索引行，按旧 `id` 检索的消费者只得到「查不到」而非「已废弃，改用 `git.03.pr-conventions`」。
- 废弃机制定为**保留正文 + 标题加「已废弃」标记 + `anchor` 不变**，配三条强制要求（正文标题带标记、`summary` 含替代去向、不得保留 `enforcement: ci`），并禁止其他条目的 `source` 指向已废弃小节。四项均由 `check_index.py` 校验。`anchor` 保持不变是关键取舍——改 `anchor` 会让按 `file`+`anchor` 固定映射的消费者立刻失效，等于用破坏性变更实现一个本意是给过渡期的机制。
- 明确废弃属不兼容语义变化按 Major 升版本，废弃条目在下一个 Major 移除正文与索引行；并给出例外：从未被引用且刚建立不久的条目（当次提交内的笔误、重复登记）直接删除即可。

### Changed

- 字段表 `status` 行补充指引，指向新增章节的三条要求。

## [4.0.1] - 2026-08-28

`check_refs.py` 扫描范围扩到知识库正文后的首轮修复（此前该校验器只看 `plugins/*/skills/`，正文内的 `§` 引用无人看守）。

### Fixed

- `git/reference/commit-message-tooling.md` §3.1 末段声称 `rules/02-commit-messages.md` §2 有「CI 侧二次校验」这一说法——**该措辞在规范中不存在**，§2 只约束本地 pre-commit / commit-msg hook，并明确把耗时检查「交给 CI」而未规定 CI 侧二次校验。真正对应的是 §3 的「CI 集成 secret scanning，在 PR 阶段拦截」。已改为引用 §3。

### Changed

- 补齐知识库正文内 11 处只写章节号、未写标题的 `§` 引用（`git/rules/02-commit-messages.md` 1 处、`git/reference/branching-workflows.md` 3 处、`git/reference/commit-message-tooling.md` 7 处）。裸章节号引用无法与标题交叉校验，章节重编号后会静默指向别的内容。全库 `check_refs.py --strict` 由 12 处问题降为 0。

## [4.0.0] - 2026-08-28

用 `knowledge-base-maintain` 1.4.0 新增的 `find_duplicates.py` 做全库跨领域查重，处理评分最高的 4 对 C# ↔ WPF 重复。这批重复是自动查重的首次实战产出——3.0.0 那次 `git` ↔ `csharp` 语义环靠人工通读才发现，本次 4 对中的 3 对排在候选前三名。

### Changed

- **破坏性：`wpf.11.integration-test` 的 `level` 由 `MUST` 降为 `SHOULD`**。通用条款（验证真实协作、可控环境、禁止连生产资源、禁止写成慢速 E2E）迁出后，该小节只剩一条 `应该` 级的 WPF 特有条款，原 `MUST` 已不反映正文实际措辞。按 `level` 取小节内最强条款级别的既定规则，此处只能是 `SHOULD`。按 `level` 做拦截强度分档的消费者需重新评估该条目。
- **`wpf/rules/11-testing.md` §1「测试分层」去重**：通用分层原则改为引用 `csharp/rules/12-testing.md` § 1. 测试策略与金字塔，本篇只保留 WPF 侧的术语对应（通用规范的 E2E 层在 WPF 即 UI 自动化测试）与「禁止只有 UI 自动化没有单元测试」。
- **`wpf/rules/11-testing.md` §7「集成测试」去重**：验证对象、可控环境与两条禁止项改为引用 `csharp/rules/12-testing.md` § 7. 集成测试，本篇只补 WPF 特有的一条（重点验证 ViewModel ↔ 服务 ↔ 持久化链路）。
- **`wpf/rules/01-environment.md` §1「目标框架策略」去重**：统一 `TargetFramework`、优先 LTS、用 `global.json` / `Directory.Build.props` 固化等通用约束改为引用 `csharp/rules/01-project-structure.md` § 1. 目标框架策略，本篇只保留 `-windows` 后缀必需性与 LTS 支持期语义两条 WPF 特有约束。
- **`wpf/rules/01-environment.md` §7「构建与 CI」去重**：CI 步骤顺序、SDK 与 `global.json` 一致、NuGet 缓存、构建可复现、产物不入库等通用约束改为引用 `csharp/rules/01-project-structure.md` § 8. 构建与 CI，本篇只保留 Desktop workload 安装、workload 缓存、禁止依赖本地设计器三条。
- 上述 4 个条目的 `title`/`summary` 同步收窄为其正文实际保留的 WPF 特有内容，并注明通用约束所在的 csharp 章节——去重后仍按旧 summary 检索会误以为 wpf 侧承载完整规则。
- 两个 wpf 规范文件的 `anchor` **未变更**，按 `file` + `anchor` 定位的消费者不受影响；本仓库两个 review skill（`wpf-code-review` / `csharp-code-review`）均未引用这两个文件，无消费者需同步。

### Fixed

- `wpf/rules/11-testing.md` 篇首原已声明「通用测试策略沿用团队约定，本篇聚焦 WPF 特有测试问题」，但 §1 与 §7 的正文把通用条款完整重述了一遍，与自身声明矛盾。本次去重使正文与该声明一致。

## [3.0.0] - 2026-08-27

按 `docs/superpowers/plans/2026-08-27-knowledge-base-optimization.md` 执行 Phase 2（规则内容质量治理），以 `git` 领域为试点，并处理试点中发现的 `git` ↔ `csharp` 跨领域重复。

### Removed

- **破坏性：删除索引条目 `csharp.15.quality-gate-overview`**——其承载的「CI 全绿才可合并」「禁止红灯合并」「门禁配置随仓库提交、禁止 `--no-verify`」属通用协作约束，已由 `git.03.branch-protection`、`git.03.pr-conventions`、`git.02.commit-hooks` 承载。按旧 ID 做固定映射的外部消费者需改引用 `git` 领域对应条目；本仓库内无消费者引用该条目（`csharp-code-review` 审查清单 10 类均为编码层面，不涉及 15 章）。
- `csharp/rules/15-quality-review.md` 删除原 §1「质量门禁总览」整节与 §4 中「所有变更走 PR + review」「PR 描述说明变更意图、测试情况、验证方式」两条，改为在篇首与节首引用 `knowledge-base/git/`。

### Changed

- **破坏性：`csharp.15.*` 其余 4 条条目的 `anchor` 随章节重编号变更**（`3.→2.` 复杂度与代码度量、`4. Code Review 流程→3. Code Review 内容重点`、`5.→4.` review 标准、`6.→5.` 技术债务管理）。
- `csharp.15.code-review-process` 的 `title`/`summary` 收窄为「C# code review 的内容重点与结论要求」——PR 流程条款迁出后，原措辞已不覆盖该条目实际内容。
- **解开 `git` ↔ `csharp` 语义环**：`git/rules/03-pull-requests.md` §1 原写「CI 通过 + review 批准才可合并（联动 `csharp/rules/15-quality-review.md`）」，而 csharp 又独立重述同一条 git 规则，形成两边互认权威、实则无单一真源的环。现按领域职责（README 载明 `git` 负责版本控制协作）归入 git，并把「禁止红灯合并」并入该条，`git.03.pr-conventions` 的 `summary` 同步补录。
- `csharp/00-README.md` 落地手段第 3 条与文件地图第 15 行同步更新，标明 CI 门禁与 PR 流程见 `knowledge-base/git/`。
- 根 README 记录实测结论：**76% 的索引条目所在小节混有不同级别条款，`level` 取该小节最强条款的级别**。这是对消费者安全的默认（不会把强制条款误判为推荐），但命中 `MUST` 条目不代表该小节每句话都是硬性要求，消费者仍需按 `file` + `anchor` 读正文。该结论修正了优化计划中"WPF 132 条全 MUST 说明规则被过度强化"的原始判断——真实原因是索引粒度与条款级别的粒度不匹配，而非规则本身被写强。
- 根 README 索引字段表中 `source` 的说明由"内部 ADR / issue / PR 路径"改为明确的 `<file>#<标题文本>` 形式，与校验器实际解析规则一致。
- 迁移/重命名文件时需同步的引用由四处增加为五处，新增"索引 `source` 字段中的内部引用"。

### Added

- `git` 领域 12 条 rule 补齐治理元数据：`enforcement`（`ci` 8 / `review` 3 / `advisory` 1）、`status`、`applies_to`、`reviewed_at`、`owner`，该领域治理字段覆盖率 100%。
- `git` 领域 8 条 rule 补齐 `source`，指向承载其理由的 `reference/` 小节或权威外部规范（如 `git.02.commit-hooks` → `reference/commit-message-tooling.md#2.3 为什么不能靠"团队自觉"代替 hook`）。理由不复制进规范正文——规范给约束、reference 给理由是既定分层，复制会产生两份需同步的同一事实。
- 根 README 新增"level 与 enforcement 的分工"章节：`level` 表达违反的严重程度（由正文措辞决定），`enforcement` 表达靠什么拦住（由能否被工具无歧义判定决定），附三档判定标准与例子。
- 根 README 新增"source：规则到理由的连接"章节：内部引用形式 `<file>#<标题文本>`、外部 URL、校验范围与不追求全覆盖的取值约定。

### Fixed

- 补上 2026-08-23（v1.5.0）那次迁移的漏项：当时按 `csharp/16-collaboration.md` 这一个文件迁移协作条款，但同类条款还散落在 `15-quality-review.md` 的「质量门禁」「Code Review 流程」标题下未被扫到——重复按语义分布，按文件迁移会漏。

## [2.0.0] - 2026-08-27

按 `docs/superpowers/plans/2026-08-27-knowledge-base-optimization.md` 执行 Phase 0（基线与保护网）+ Phase 1（索引粒度与目录册）。

### Changed

- **破坏性：领域目录结构调整为"元数据在根、内容按类型分组"**——各领域下的编号规范文件迁移到 `<domain>/rules/`，`00-README.md` 与 `index.jsonl` 保留在领域根目录，`reference/` 与 `rules/` 同级并列。涉及 `csharp`（17 篇）、`wpf`（17 篇）、`git`（5 篇）、`skill-authoring`（5 篇），共 44 个文件（`git mv` 迁移，保留历史）。
- **破坏性：索引 `file` 字段路径变更**——266 条记录的 `file` 从 `NN-*.md` 改为 `rules/NN-*.md`（仅此一字段变动，其余字段逐字未改）。按旧路径做固定映射引用的外部消费者需同步更新；本仓库内引用已全部同步。
- 同步更新全部内部与消费者引用（共 4 类）：各领域 `00-README.md` 文件地图、`reference/` 与 `rules/` 正文交叉引用（74 处）、`csharp-code-review` / `wpf-code-review` SKILL.md 的审查清单定位表（23 处）、`.claude/rules/skill-conventions.md`（2 处）、`.claude/skills/commit-cc-plugin/SKILL.md`（含 10 处 Markdown 链接目标）。正文头部"更新历史"与本 CHANGELOG 中记录当时事实的路径不改写。
- 领域 README"索引与机器消费"章节措辞更新：`reference/` 的并列对象由"本篇编号规范文件"改为"`rules/` 下的规范文件"。

### Added

- 根级 `catalog.json` 领域目录册：登记 6 个领域的内容分类、维护者、状态、主要消费者与最近审阅日期，纳入一致性校验（与实际领域目录双向一致，登记缺失或多余均报错）。
- 根 README 新增"索引粒度规范"章节：可独立判断的规则单独登记、导航标题不登记、`reference` 默认按整篇登记、文件级汇总条目与节级条目可并存。
- 根 README 索引字段表扩展为必填/可选两栏，新增可选治理字段 `enforcement`（`ci`/`review`/`advisory`）、`status`（`active`/`deprecated`/`experimental`）、`source`、`applies_to`、`reviewed_at`、`owner`——渐进引入，未填不报错，填了必须合法。
- 补齐 `csharp/rules/12-testing.md` 细粒度索引 7 条：测试项目布局、断言风格、覆盖率目标、测试数据自包含、契约测试、慢测试过滤、CI 覆盖率采集（覆盖率 79.7% → 82.7%）。
- 补齐 `skill-authoring` 节级索引 35 条：格式规约 6 条、描述优化 6 条、质量评估 8 条、脚本使用 7 条、最佳实践 8 条（覆盖率 14.7% → 100%）。原 5 条文件级汇总条目保留为文件入口，ID 不变。
- 根 README 维护约定补充：校验的单领域/全局作用域划分、`--audit` 报告用法、迁移文件时须同步的四处引用。

索引记录总数 285 → 327（rule 266 → 308，reference 19 条不变）。

## [1.11.0] - 2026-08-27

### Added
- 新增 `dotnet` 领域：收纳 .NET Framework、现代 .NET、Windows 兼容性与生命周期的描述性知识
- 新增 `dotnet/reference/windows-dotnet-support-matrix.md`：Windows 与 .NET Framework / .NET 5+ 支持矩阵整理稿
- 根知识库领域说明补充 `dotnet`、`csharp`、`wpf` 三者的职责边界

## [1.10.4] - 2026-08-26

### Changed
- `media/reference/media-parameters.md` 扩展：§2 帧率新增「提高帧率的两种方式」（复制帧 vs 运动插帧）与「降低帧率=丢帧」；§4 新增「由目标体积反推目标码率」（two-pass 场景的 `目标大小×8192÷时长−音频码率` 公式及 8192 的进制来源）
- `media/reference/video-codecs.md` §1 新增「关键帧（I/P/B 帧）与 GOP」小节：帧间预测、关键帧间隔与 seek/截取精度的权衡、`-c copy` 对齐关键帧的实际影响
- `media/index.jsonl` 同步更新 `media.ref.media-parameters`、`media.ref.video-codecs` 的 `summary`/`tags`

## [1.10.3] - 2026-08-26

### Changed
- `media/reference/streaming-protocols.md` 第 8 节扩展为「与 ffprobe / ffplay 的关系」：新增 ffplay 能直接播放 HLS/RTSP/RTMP 网络流的说明与命令示例，及 RTSP TCP 传输、RTMP 构建依赖、直播不可回拖、DRM 不可解密等注意点
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `tags`/`summary`（新增 `ffplay` 标签）

## [1.10.2] - 2026-08-26

### Changed
- `media/reference/streaming-protocols.md` 重构为面向零基础读者的通俗版：新增"为什么切分片"问题引入、播放器播放 HLS 的 4 步流程、各协议 URL 实例与一句话人话总结、CDN 说明、文末术语速查表，并在常见误区补充"扩展名非铁律"条目
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `summary`

## [1.10.1] - 2026-08-26

### Changed
- `media/reference/streaming-protocols.md`：标题改为"流媒体传输与分发协议：HLS、RTMP、RTSP、DASH 与 WebRTC"（去除 M3U8 平列与赘余的"与相关协议"）；将 M3U8 并入 HLS 章节作为其播放清单组件介绍，并展开 HLS 完整组成——分片、两级清单（Media/Master Playlist）、码率自适应、加密与 DRM、直播/点播差异
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `title`/`summary`

## [1.10.0] - 2026-08-26

### Added
- `media` 领域新增 `reference/streaming-protocols.md`：流媒体传输与分发协议讲解——M3U8 播放清单、HLS/DASH HTTP 分片分发、RTMP 推流、RTSP 会话控制协议、WebRTC 实时互动，及直播生态推流/分发/互动分工
- `media/index.jsonl` 登记 1 条 reference 索引记录 `media.ref.streaming-protocols`
- `media/00-README.md` 阅读路径与文件地图同步补充 streaming-protocols 条目

## [1.9.1] - 2026-08-26

### Changed
- `media/reference/media-parameters.md` 扩展：新增常用视频比例表（16:9/4:3/21:9/9:16/1:1）与横屏/竖屏判定方法、码率单位进制换算（码率 1000 进制 vs 存储 1024 进制、bit 与 Byte 换算）
- `media/reference/video-quality.md` 扩展：新增第 6 节 LUT（Look-Up Table）——1D/3D LUT 机制、常见文件格式、与 HDR/SDR 色调映射的关系、常见注意点
- `media/index.jsonl` 同步更新 `media.ref.media-parameters`、`media.ref.video-quality` 的 `summary`/`tags`/`title`

## [1.9.0] - 2026-08-26

### Added
- 新增 `media` 领域：纯描述性知识库（无规范条款，全部为 reference），含 10 篇参考文档——媒体流结构基础、视频/音频封装格式、视频/音频编解码器、媒体参数（分辨率/帧率/码率）、音频参数（采样率/位深/声道）、视频质量（有损无损/CRF/HDR/色度采样）、字幕格式、ffprobe 字段映射
- `media/index.jsonl` 登记 10 条 reference 索引记录

## [1.8.0] - 2026-08-23

### Added
- `git` 领域新增 `reference/pull-request-concepts.md`：Pull Request 概念讲解——PR 不是 GitHub 特有（GitLab 叫 Merge Request）、PR 的代码评审/CI 门禁/合并关卡三大作用、何时该用 PR，是 `03-pull-requests.md` 的配套参考
- `git/index.jsonl` 新增 1 条 reference 索引记录 `git.ref.pull-request-concepts`

### Changed
- `03-pull-requests.md` 正文头部补充指向配套 reference 的引用说明

## [1.7.0] - 2026-08-23

### Added
- `git/02-commit-messages.md` §1 新增规范条：提交中若有 AI 协作者，须用 `Co-Authored-By` footer 明确标注，禁止隐去 AI 参与事实
- `git/reference/commit-message-tooling.md` 新增第 4 节「AI 协作者标注」：Co-Authored-By 格式讲解、为何用结构化 footer 而非自由文本、常见误区
- `git/index.jsonl` 新增 1 条规范索引记录 `git.02.ai-coauthor`，`git.ref.commit-message-tooling` 的 `tags`/`summary` 同步补充 AI 协作相关关键词

## [1.6.0] - 2026-08-23

### Added
- `git` 领域新增 `reference/branching-workflows.md`：GitHub Flow/Git Flow/Trunk-Based 工作流对比、分支命名示例大全、分支生命周期管理（创建/同步/清理），是 `01-branching.md` 的配套参考
- `git` 领域新增 `reference/commit-message-tooling.md`：Conventional Commits 完整规范（type 清单、BREAKING CHANGE、多行 body）、commit-msg hook 实现（commitlint/husky、纯 Shell）、敏感信息扫描工具对比（gitleaks/git-secrets/truffleHog），是 `02-commit-messages.md` 的配套参考
- `git/index.jsonl` 补充对应 2 条 reference 索引记录

### Changed
- `01-branching.md`、`02-commit-messages.md` 正文头部补充指向配套 reference 的引用说明
- `git/00-README.md`「索引与机器消费」补充 `reference/` 目录说明

## [1.5.0] - 2026-08-23

### Added
- 新增 `git` 领域：Git 协作规范总纲（00-README + 01-05 五篇规范文件），覆盖分支策略与命名、提交信息与敏感信息防护、PR 与合并策略、版本与发布、代码所有权
- `git/index.jsonl` 首批 11 条索引记录

### Changed
- `csharp/16-collaboration.md` 的分支策略、提交信息、PR 规范、版本与发布、代码所有权五节迁移至 `git/` 领域对应文件，本篇仅保留与语言相关的 CHANGELOG 条款并重新编号为 §1
- `csharp/index.jsonl` 移除已迁移的 4 条记录（`branch-strategy`/`commit-message`/`pr-conventions`/`release-versioning`），`changelog` 记录 anchor 同步更新
- `csharp/00-README.md` 文件地图第 16 行主题说明同步更新，指向 `knowledge-base/git/`

## [1.4.0] - 2026-08-23

### Added
- `csharp/index.jsonl` 补齐至全量覆盖 01-17 全部规范文件：9 → 122 条（新增 113 条，`02-coding-style.md`/`12-testing.md` 按三级子节粒度，其余按二级章节粒度）
- `wpf/index.jsonl` 补齐至全量覆盖 01-17 全部规范文件：6 → 132 条（新增 126 条，全部按二级章节粒度，wpf 规范文件基本无三级子节）
- 两领域索引一致性校验通过：`check_index.py csharp wpf` → 共检查 254 条记录，未发现问题

## [1.3.3] - 2026-08-23

### Changed
- README「消费方式」补充"动态检索 vs 固定映射"两种消费模式说明，明确 `csharp-code-review`/`wpf-code-review` 直接引用 `file`+`anchor` 属于被认可的固定映射模式
- README「维护约定」补充索引覆盖是渐进式的，新增/优化 skill 引用到未登记规则时随手补录即可，不必专项排期回填

## [1.3.2] - 2026-08-22

### Changed
- wpf 规范引用 skill 改名同步：`wpf-xaml-performance` → `wpf-code-review`（wpf/00-README、10/08/07 篇头部与联动措辞更新，性能操作层改为指向 skill 的「性能专项诊断速查」章节）

## [1.3.1] - 2026-08-22

### Changed
- `.claude/rules/skill-authoring.md` 重命名为 `skill-conventions.md`（规则文件覆盖 skill 全生命周期约定，`authoring` 名偏窄），README 与 `skill-authoring/00-README.md`、`01-skill-format.md` 引用同步更新

## [1.3.0] - 2026-08-22

### Added
- 新增 `skill-authoring` 领域（Skill 创建规范）：00-README + 01-05 规范篇 + 3 个 reference 讲解篇
- `01-skill-format.md`：SKILL.md 格式规约（目录结构/frontmatter/正文/progressive disclosure/文件引用）
- `02-description-optimization.md`：描述优化（触发机制/写作原则/trigger eval/train-validation 切分）
- `03-skill-evaluation.md`：质量评估（evals/assertions/grading/benchmark/迭代循环）
- `04-script-usage.md`：脚本使用（one-off 命令/自包含脚本/agentic 设计）
- `05-best-practices.md`：最佳实践（真实经验/上下文预算/控制校准/指令模式）
- `reference/`：trigger-eval-workflow、eval-workspace-structure、self-contained-scripts 三篇讲解
- `.claude/rules/skill-authoring.md` frontmatter 节改为引用知识库 `skill-authoring/`（通用规范归知识库，仓库专属约定留规则文件）

## [1.2.1] - 2026-08-22

### Changed
- `csharp/README.md`、`wpf/README.md` 重命名为 `00-README.md`（纳入编号体系，文件地图同步更新）

## [1.2.0] - 2026-08-22

### Added
- 首个 reference 条目 `csharp.ref.refit`：`refit.md` 迁入 `csharp/reference/`，登记索引
- 相关引用路径更新（`13-api-design.md`、`csharp/README.md` 中 `refit.md` → `reference/refit.md`）

## [1.1.1] - 2026-08-22

### Changed
- 校验脚本 `check_index.py`、`test_check_index.py` 迁至 `knowledge-base-maintain` skill 的 `scripts/` 子目录，随 skill 分发；`base_dir` 定位逻辑相应调整（`parents[4]` 定位仓库根再进 `knowledge-base/`）；运行命令更新为 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>`

## [1.1.0] - 2026-08-22

### Added
- `02-coding-style.md` 新增 2.5 节：委托选择规则（优先 Func/Action），原 2.5 注释风格顺移为 2.6
- `13-api-design.md` 补充隐式依赖契约需显式说明的规则
- 对应索引记录 `csharp.02.delegate-func-action`、`csharp.13.implicit-dependency-contract`

## [1.0.0] - 2026-08-22

### Added
- 迁移 `docs/csharp_doc` → `knowledge-base/csharp`，`docs/wpf_doc` → `knowledge-base/wpf`
- 建立 JSON Lines 索引机制（`index.jsonl`）与一致性校验脚本 `check_index.py`
- csharp、wpf 两领域首批索引条目（各 6 条）
