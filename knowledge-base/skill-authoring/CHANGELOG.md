# Changelog — Skill 创建与维护规范

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [8.0.0] - 2026-09-13

eval 用例的**存放位置与文件形态**改为官方 `claude plugin eval` 格式，原 `evals/evals.json` 不再是合规位置。这是 Major 而非 Patch：`skill-authoring.03.test-case-design` 的 MUST 换掉了它要求的产物本身，**按旧条款做出的合规产物在新条款下变为不合规**，外部消费者必须迁移，不是措辞优化。方法论未动——§2 的 with/without 基线、§3 的断言写法要求、§4 的 evidence 要求、§5 的 delta 判据、§6 模式分析、§7 人工 review、§8 迭代循环全部原样保留，本次只替换它们的载体。

### Changed
- `skill-authoring.03.test-case-design`（`rules/03-skill-evaluation.md` §1）：测试用例由 `evals/evals.json` 改存 `evals/<case-name>/prompt.md`（frontmatter 承载 case 字段、正文是用户提问）+ `evals/<case-name>/graders/*.md`（frontmatter 承载 `type`/`weight`、正文是判据）；单文件 `case.yaml` 为官方等价写法。🔴 **外部消费者需要做的事：把已有 `evals/evals.json` 拆成上述两类文件**——`prompt` 字段成为 `prompt.md` 正文，`expected_output` 字段原样成为 `llm` grader 的正文（两者本是同一件事的两种包装，不需要重新发明判据措辞）
- `skill-authoring.03.test-case-design`：新增两处结构差异警示——官方 case 顶层 15 个合法键（zod strict）中**没有 `files`**，输入文件不再是用例的字段而靠工作区预置；`expected_outcome` 不受枚举约束，任意字符串都能过校验，因此它不是可依赖的判据
- `skill-authoring.03.baseline-comparison`（§2）：补官方 `--ablation` 默认值即 `with-without`，故本节第一条 MUST 在用官方工具时是默认行为；并记入一个反直觉耦合——with-without 下 with-only 的 grader（**含 `tool_used: Skill`**）被当作 plugin-fired 指示器而**不计入分数**，判据全是 `tool_used: Skill` 的套件在该模式下会失去全部判据。另补三个执行时默认值：`--runs` 默认 `case.runs ?? 3`、`--judge-model` 默认 haiku、`--threshold` 默认 1.0
- `skill-authoring.03.assertions`（§3）：补 assertion 在官方格式下的落位即 grader 的 `type`，六种中 `regex`/`tool_order`/`tool_used`/`file_exists` 免费、`llm`/`baseline` 付费，并逐行对应到本节既有条款；`tool_used` 配 `max: 0` 使「不该触发的语境」也能零成本判定
- `skill-authoring.ref.eval-workspace`（`reference/eval-workspace-structure.md`）：目录图改为官方 case 形态，新增 CLI 产物落点 `evals/results/<ISO 时间戳>/aggregate-result.json` 与 `casesTotal`/`stopReason`/`judgeCostUsd` 三处读数陷阱；`### evals.json` 一节改为 `### prompt.md + graders/*.md`；`timing`/`grading`/`benchmark` 三节保留并注明官方由 `aggregate-result.json` 一份承担，`feedback.json` 注明**官方无对等物、须自行维护**
- `rules/06-continuous-improvement.md` §1 第三条对 03 篇的指向由 `evals.json` 驱动改为用例目录驱动（连带修正，避免留下悬空的旧形态提及）

### 依据
- 官方 `claude plugin eval` 的 case schema 与 grader 类型（`--bare` 脚手架实测 + zod strict 报错逐键取证）
- 用户 2026-09-13 裁决「官方格式为唯一规范」；本仓 `wpf-code-review` 的 6 条素材已按此迁移并合并（`ddd353bd`），是本次规范的活体样本
- 🔴 `evals/results/` 必须 gitignore 的第二层理由（它是天然缺 marker 的子目录，会被 case 校验门禁判成「建了一半的 case」，导致**跑一次 eval 就让下一次提交失败**）来自本仓实测，见 `.githooks/check_new_skill_eval_case.py`


## [7.5.0] - 2026-09-12

`rules/06-continuous-improvement.md` 新增 §5-§10，把持续优化从「有没有机制」推进到「机制怎么用才不会越优化越贵」。六条全部来自实际教训，不是推演：某 skill 连续 6 轮优化而其功能在这些提交期间一次未执行；台账（known-issues + CHANGELOG 共 918 行）已超过它所描述的正文（498 行）且每轮被完整重读；一轮新写的检查项贡献了该轮全部三条高危缺陷。

### Added
- `§5 优化轮的入场条件：必须真实运行过`——自上次改动以来至少真实执行过一次才可发起优化轮；禁止连续多轮只读不跑，症状是连续提交全为 fix/refactor 而功能一次未执行
- `§6 新增判据必须双向实跑`——必须同时实跑「应通过」与「应拦截」两侧（只验一侧分别漏掉恒通过与恒拒绝）；命令类动作须另验作用域；每个副作用配归还路径；禁止拿聚合字段代替单项字段作判据
- `§7 机械可判定的检查不进人工评审`——派生值不写死、必须写时落笔前重跑统计；五类机械项用脚本拦。判据是**人工评审成本 ∝ 语料总量，机械检查成本 ∝ 检查项数**
- `§8 评审范围与成本控制`——darwin-skill 是门禁不是缺陷猎场；禁止与评审 agent 就分数往复论证；缺陷发现只读 diff 及影响半径；一轮只改一个主题
- `§9 台账封顶与归档`——`known-issues.md` 正文只留待处理项、仍生效且被正文指向的判据、归档指针；逐轮叙事移入 `known-issues-archive.md`；封顶 150 行；评审时告知 agent 不读归档
- `§10 定性问题先查一手规范`——分清**运行时拒绝**（缺陷）与**移植时拒绝**（取舍），给取舍登记豁免会让规范自相矛盾
- `index.jsonl` 新增 6 条索引，对应 §5-§10

### Changed
- `§3` 的「已解决条目不删除」补注：台账超封顶时该可追溯性由归档文件承载，与 `§9` 不冲突
- `§4` 的 enforcement 声明由「§1-3」扩为「本篇各节」，并说明 §7 的机械项虽可脚本化、但脚本存在性因仓库而异，故规则本身仍标 `review`

### 依据
- 实际优化轮的成本取证（`optimus-plugins-official` 仓 `sync-cc-tips` 的 `fcb9483`..`bb6867a` 六次连续提交）


### Added
- `rules/01-skill-format.md` 新增 `2.1 runtime 原生扩展字段`：规范六字段是**可移植性全集**而非 Claude Code 的字段上限，Claude Code 另有约 20 个原生 frontmatter 字段在其内合法可用；需跨 runtime 分发的只用六字段，仅 Claude Code 内使用的可用原生字段但须在正文写明其用途；**禁止把使用原生字段记为「规范例外」逐个登记豁免**
- `rules/01-skill-format.md` 新增 `2.2 disable-model-invocation`：该字段对模型的五层作用（description 整体移出上下文、模型无法自主加载、越权尝试被硬拦截并被指示不要改用别的方式复现、不预载入子代理、v2.1.196 起计划任务当纯文本不执行）、取值范围与版本门槛、反向字段 `user-invocable` 与 `skillOverrides` 替代路径、适用与禁用场景
- `index.jsonl` 新增 2 条索引：`skill-authoring.01.runtime-native-fields`、`skill-authoring.01.disable-model-invocation`

### Changed
- `rules/01-skill-format.md` §2 导语由「只允许六个顶层字段」改为「规范定义的顶层字段共六个，这六个是可移植性的全集」——原表述把可移植性边界误读为合法性边界
- `rules/01-skill-format.md` §6 补充 `skills-ref` 判读方式：声明了原生字段时 `Unexpected key(s)` 报错是**预期结果**，须确认报错只涉及有意声明的字段、其余校验项仍全通过，禁止为让校验变绿而删字段
- `index.jsonl` 的 `skill-authoring.01.frontmatter-fields` summary 同步精化，并指向新增的 `01.runtime-native-fields`

### 依据
- 官方文档 <https://code.claude.com/docs/en/skills> 的 frontmatter 字段表与 Portability note；本机 Claude Code 2.1.268 已满足 v2.1.196 / v2.1.218 两处版本门槛

## [7.3.0] - 2026-08-30

### Added
- 新增 `rules/06-continuous-improvement.md`（持续优化）：创建后强制 darwin-skill 基线评估、`known-issues.md` 使用期反馈记录规范、"待处理"满3条强制触发优化循环、与 darwin-skill 的现实边界说明
- `index.jsonl` 新增 3 条 `skill-authoring.06.*` rule 索引；补登 `reference/darwin-skill-optimization.md` 的 reference 索引（修复此前的孤儿文件警告）
- README 文件地图新增 `06` 行，阅读路径表补入 `06`

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 1.3.1 - 2026-08-22

- `.claude/rules/skill-authoring.md` 重命名为 `skill-conventions.md`（规则文件覆盖 skill 全生命周期约定，`authoring` 名偏窄），README 与 `skill-authoring/00-README.md`、`01-skill-format.md` 引用同步更新

### 衍生自全局 1.3.0 - 2026-08-22

- 新增 `skill-authoring` 领域（Skill 创建规范）：00-README + 01-05 规范篇 + 3 个 reference 讲解篇
- `01-skill-format.md`：SKILL.md 格式规约（目录结构/frontmatter/正文/progressive disclosure/文件引用）
- `02-description-optimization.md`：描述优化（触发机制/写作原则/trigger eval/train-validation 切分）
- `03-skill-evaluation.md`：质量评估（evals/assertions/grading/benchmark/迭代循环）
- `04-script-usage.md`：脚本使用（one-off 命令/自包含脚本/agentic 设计）
- `05-best-practices.md`：最佳实践（真实经验/上下文预算/控制校准/指令模式）
- `reference/`：trigger-eval-workflow、eval-workspace-structure、self-contained-scripts 三篇讲解
- `.claude/rules/skill-authoring.md` frontmatter 节改为引用知识库 `skill-authoring/`（通用规范归知识库，仓库专属约定留规则文件）
