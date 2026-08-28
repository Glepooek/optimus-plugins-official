# Changelog

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
