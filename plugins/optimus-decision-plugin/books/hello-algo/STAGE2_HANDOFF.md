# Hello 算法蒸馏 · 阶段 2 交接文档

## 目的
本文档供**下一次对话 / 下一个执行者**在无需重新阅读本次对话全部历史的情况下，继续完成阶段 2（剩余 7 个 skill）及后续阶段。

## 已完成（第 1 个 skill，作为范本）

`plugins/optimus-decision-plugin/skills/data-structure-selection/` 已完整产出四个文件：
- `SKILL.md`（六字段 frontmatter + 完整 R/I/A1/A2/E/B 六段）
- `CHANGELOG.md`（`[1.0.0]`）
- `README.md`（固定 ASCII 图结构五章节）
- `test-prompts.json`（8 条，含应调用/面试诱饵/跨 skill 诱饵/无关诱饵/边界场景）

**这是唯一的参考范本**——后续 7 个 skill 严格照此结构和字段规格撰写，不要重新发明格式。

## 关键前提决策（已与用户确认，不要重新询问）

1. **`metadata.category` 全部留空**——这 8 个 skill 是决策指导型，不精确匹配 workflow/quality/generator/tool/platform 任一枚举，省略该字段。
2. **`allowed-tools` 统一为 `Read Grep Glob`**——本质是对话式指导，但允许看一眼用户当前代码/数据规模以给出更精准建议。
3. **`metadata.author` 固定 `desktop client team`**，**`metadata.version` 初始 `"1.0.0"`**。
4. **frontmatter 只允许六个顶层字段**（`name`/`description`/`license`/`compatibility`/`metadata`/`allowed-tools`），cangjie-skill 模板要求的 `source_book`/`source_chapter`/`tags`/`related_skills` **一律不进 frontmatter**，改为：
   - 书名/章节：正文标题下用 HTML 注释一行标注来源（如 `<!-- 蒸馏来源：《Hello 算法》(Hello Algo) krahets，第 4-9 章。verified.md skill-01。 -->`）
   - tags：不需要单独字段，`description` 已含关键词
   - related_skills：体现在正文末尾"相关 skills"章节（depends-on / contrasts-with / composes-with）
5. **`compatibility` 字段统一写法**："纯知识决策类 skill，无外部 CLI/MCP 依赖；可选用 Read/Grep/Glob 查看用户当前代码库以判断已有数据规模、访问模式，辅助给出更精准建议。"（8 个 skill 可完全复用此句）
6. **长内容分段输出**：每个 SKILL.md 必须用 Write 建骨架 + 多次 Edit 补段落，禁止一次性长文本输出（用户全局硬性规则）。

## 待完成的 7 个 skill（严格按此顺序，来自阶段 0 已确认的工程优先级）

按 `plugins/optimus-decision-plugin/books/hello-algo/verified.md` 里的 merged_from 字段取原文引用/案例/反例素材，全部素材已在阶段 1 candidates 和阶段 1.5 verified.md 中就位，**无需重新读原书**：

### 2. complexity-analysis（复杂度分析方法）
- merged_from: frameworks[f01], principles[p01-p04]
- 无 case/counter-example（本簇是方法论地基，其他 skill 会 depends-on 它）
- related: 被其余 7 个 skill 依赖

### 3. sorting-algorithm-selection（排序算法选型）
- merged_from: frameworks[f05], principles[p21-p28], cases[c15,c16], counter_examples[c10-c16]（counter-examples.md 的 id）

### 4. search-algorithm-selection（搜索算法选型）
- merged_from: frameworks[f04], principles[p18-p20], cases[c14], counter_examples[c01]

### 5. dynamic-programming-problem-solving（动态规划解题三步法）
- merged_from: frameworks[f07-f11], principles[p32-p34], cases[c01-c07,c12]（cases.md 的 id）, counter_examples[c22,c23]（counter-examples.md 的 id）

### 6. greedy-algorithm-applicability（贪心算法适用性判断）
- merged_from: frameworks[f13-f16], principles[p35,p36], cases[c08-c11], counter_examples[c17,c18,c19]

### 7. divide-and-conquer-problem-check（分治问题判断）
- merged_from: frameworks[f03], principles[p29], cases[c17,c18,c22]（cases.md 的 c22）, counter_examples[c22]（counter-examples.md 的 c22——与 cases.md 的 c22 是不同内容，注意区分来源文件）

### 8. backtracking-algorithm-template（回溯算法框架模板）
- merged_from: frameworks[f12], principles[p30,p31], cases[c19,c20,c21], counter_examples[c20,c21]

## 每个 skill 的产出清单（4 文件，缺一不可）
1. `plugins/optimus-decision-plugin/skills/<slug>/SKILL.md`
2. `plugins/optimus-decision-plugin/skills/<slug>/CHANGELOG.md`
3. `plugins/optimus-decision-plugin/skills/<slug>/README.md`
4. `plugins/optimus-decision-plugin/skills/<slug>/test-prompts.json`（5-10 条，含应调用/诱饵/边界三类，诱饵至少 1 条是同书兄弟 skill 场景）

## 阶段 2 之后仍需做的事（勿遗漏）

- **阶段 3 Zettelkasten 链接**：每个 skill 的"相关 skills"章节目前只是初稿（依据 verified.md 的簇映射推测），需要在全部 8 个 SKILL.md 写完后回填定稿；生成 `books/hello-algo/INDEX.md`（含 mermaid 引用图）+ `books/hello-algo/GLOSSARY.md`（整理自 `candidates/glossary.md` 20 条术语）
- **阶段 4 压力测试**：可用独立 sub-agent 盲测每个 skill 的 test-prompts.json，未过的回炉阶段 2
- **阶段 5 交付**：生成 `books/hello-algo/DIGEST.md`，询问用户安装位置
- **插件基础设施**（贯穿性，尚未开始）：
  - `plugins/optimus-decision-plugin/.codex-plugin/plugin.json`（参考 `plugins/optimus-media-plugin/.codex-plugin/plugin.json` 模板）
  - 注册到 `.claude-plugin/marketplace.json`（Minor 版本升级）和 `.agents/plugins/marketplace.json`
  - `plugins/optimus-decision-plugin/` 顶层可能需要一个说明性 README（参考其他插件顶层结构，本次未确认，需要时再问用户）
- **跨插件重复性自检**（按 AGENTS.md 约束，大概率无重叠但流程要求）
- **提交推送**：必须用 `commit-cc-plugin` skill，禁止手动 git 操作；提交前需按仓库规则用 `darwin-skill` 给新 skill 评分（Minor/Major 升级前置要求）

## 断点续跑指引
`plugins/optimus-decision-plugin/books/hello-algo/PIPELINE_STATE.md` 需要在每完成一个 skill 后更新勾选项，当前该文件仍停留在"阶段 1.5 已完成"的旧状态，需要同步更新为"阶段 2 进行中（1/8 完成）"。
