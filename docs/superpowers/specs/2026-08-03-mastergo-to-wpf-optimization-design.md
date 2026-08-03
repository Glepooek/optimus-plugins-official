# MasterGo 转 WPF XAML Skill 优化完善 — 设计规格

- **日期**：2026-08-03
- **Skill 名**：`mastergo-to-wpf`
- **归属插件**：`optimus-frontend-plugin`
- **状态**：待实现
- **基线实现**：`1.0.2`（`dsl_to_xaml.py`，37 条离线 CLI 契约测试）
- **关联初版文档**：[初版设计](2026-08-02-mastergo-to-wpf-design.md) · [初版实施计划](../plans/2026-08-02-mastergo-to-wpf.md)

> 本文档仅定义对已存在 Skill 的优化完善；**不修改、不替代** 2026-08-02 的初版设计与实施计划。初版仍是当前确定性 DSL→XAML 转换器的实现基线。

## 1. 背景与问题

当前 Skill 已实现可靠的基础链路：分区 DSL 落盘、纯 Python CLI 转换、颜色资源字典、文本闭集校验、SVG 图标清单与回填流程。它的优势是离线可测、失败原子化（exit 2 且不产生半成品）、不猜测设计稿内容。

但当前输出仍是“可供人工接管的坐标骨架”，而非高保真、可复用的 WPF 页面：

1. 节点不输出 `Width`、`Height`、`Padding`、描边、圆角及大部分排版属性；
2. `FRAME`、`GROUP`、`INSTANCE`、`IMAGE` 大多退化为 `Canvas`，图片无占位，组件变体丢失；
3. 仅生成设计稿颜色资源，不能优先复用项目既有 WPF 控件、主题资源和 Design Token；
4. 无截图辅助分析、生成方案摘要、结构化转换报告或可选视觉验证闭环；
5. `section-*.json` 按文件名字典序读取，双位数 sectionIndex 会发生顺序错误；
6. `test-prompts.json` 的首条期望未覆盖现已存在的“区块选择/输出名称确认”门禁。

本优化借鉴 `fltrp-mastergo-to-code` 的 Meta Rules、层锚点、Token 预扫描、方案确认、截图辅助和有界验证思想，但保留本 Skill 的 WPF 专用性与确定性 CLI 核心。

## 2. 目标与非目标

### 2.1 目标

1. **提高直接还原度**：可从可用 DSL 生成尺寸、盒模型、基础边框/圆角、文本排版和富文本 Run，显式处理图片与实例状态。
2. **优先复用项目资产**：可选读取 MasterGo Meta Rules 和目标 WPF 项目映射，将设计 Token 映射到现有 ResourceDictionary，将明确组件意图映射到已注册 WPF 控件。
3. **保持可信与可控**：保留“缺少关键坐标/资源即硬失败”“成功 stdout/stderr 为空”“写入前完整校验”的 CLI 契约；所有启发式映射均带置信度、可追溯来源和回退路径。
4. **建立可验证闭环**：生成结构化报告；在用户提供截图且项目具备运行条件时，可选执行 UI 一致性检查并限制返工次数。
5. **强化可维护性**：修复排序与测试期望漂移，为新映射建立离线 fixture 和黑盒契约测试。

### 2.2 非目标

- 不做设计稿与已手改 XAML 的双向或增量同步。
- 不生成 ViewModel、数据绑定、命令、code-behind 或业务逻辑。
- 不在低置信度条件下将几何节点强行猜成业务控件；保留 `Canvas` 作为安全回退。
- 不绕开分区流程调用 `mcp__getDsl`，不下载不可恢复的图片 URL，也不伪造资源。
- 不默认修改 Skill 自身的 `references/` 来记录运行反馈；反馈记录写到目标项目侧，且由用户控制。
- 不将视觉得分阈值当作发布承诺；基础骨架和有外部资源缺口的页面可只产生差异报告。

## 3. 设计原则

1. **确定性核心，增强可选**：`dsl_to_xaml.py` 始终可只依赖本地 JSON 运行；MCP、项目扫描、截图和 UI 自动化只能增强结果，不能破坏离线转换能力。
2. **显式优先于推断**：Meta Rules 与层锚点优先于项目知识库匹配；知识库匹配优先于几何/名称推断；无法证明时原样直译或留具名 TODO。
3. **先验证再写入**：收集与验证全部页面、资源、报告数据成功后，才创建/替换输出文件。
4. **回退可见**：每个降级项必须写入 `conversion-report.json` 或 XAML 注释，不能“exit 0 但静默丢内容”。
5. **WPF 原生优先**：优先输出合法、可编译的 `Border`、`Grid`、`StackPanel`、`Canvas`、`TextBlock`、`Image`、`Path`；项目自定义控件必须来自显式映射白名单。

## 4. 目标架构

```text
MasterGo section DSL ─┐
MasterGo Meta Rules ──┼─> Skill 编排层（前置检查、确认门、MCP、交付）
项目映射/资源字典 ────┘                 │
                                      ▼
                      语义与资产预分析层（可选）
                      - Token / 组件 / 层锚点 / 布局置信度
                                      │
                                      ▼
                      确定性转换器 dsl_to_xaml.py
                      - JSON → XAML / Colors / icons / images / report
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                 SVG → Path.Data 回填        可选截图/UI 一致性检查
```

### 4.1 职责边界

| 层级 | 职责 | 禁止事项 |
|---|---|---|
| `SKILL.md` 编排层 | 前置检查、拉取 sections/Meta、确认范围、调用 CLI、报告交付 | 不能跳过确认门或绕过分区读取完整 DSL |
| 预分析层 | 解析规则、Token 预扫描、映射决策、置信度和方案摘要 | 不能直接写入 XAML 或把未注册锚点当作可执行 XAML |
| `dsl_to_xaml.py` | 基于落盘 JSON 和显式映射生成确定性文件 | 不联网、不读取 token、不调用 MCP |
| `svg-to-xaml-path` | SVG 到 `Path.Data` | 不承担布局或组件映射 |
| QA 一致性检查 | 比对设计与运行截图、输出差异 | 不直接篡改生成的 XAML |

## 5. 功能规格

### 5.1 基础正确性与输出契约

- section 文件必须按其文件名中的**数值** `sectionIndex` 升序读取，而非字符串字典序。
- 保持现有成功/失败 CLI 契约：成功 exit 0 且 stdout/stderr 为空；可恢复信息写入 sidecar 报告；关键缺失仍 exit 2 且 stdout 为空。
- 所有页面、颜色、图标、图片、报告均在完整渲染和验证后再落盘；失败不得留下新增的半成品。
- `test-prompts.json` 必须反映：取得 section 列表后，用户尚未确认 section 范围、输出目录和页面名时，不得读取分区 DSL 或创建产物。

### 5.2 尺寸、盒模型与基础样式

转换器在 DSL 具有相应字段时输出以下属性；字段缺失时不编造默认值，并在报告中登记：

| DSL 信息 | WPF 输出 | 约束 |
|---|---|---|
| `layoutStyle.width/height` 或等价可靠尺寸 | `Width` / `Height` | 仅写入可解析的非负数 |
| `padding` | `Border.Padding` 或布局容器的等效边距 | 需保持 flex 子节点不带 Canvas 坐标 |
| fill / `_token` / `_color` | `Background` 或 `Foreground` | 沿用现有颜色优先级与 opacity 规则 |
| `strokeColor` / `strokeWidth` | `BorderBrush` / `BorderThickness` | 无法成对解析时登记缺失项 |
| 圆角字段 | `CornerRadius` | 只作用于可承载视觉盒模型的节点 |
| 字体、字号、字重、行高、对齐、换行 | `TextBlock` 对应属性 | 缺字体仅告知，不替换为虚构字体 |

有可见 fill/stroke/padding/radius 的容器优先产出 `Border`，其内部根据布局语义放置 `Grid`、`StackPanel` 或 `Canvas`；无视觉盒模型需求的容器保留最简合法元素。FRAME `opacity` 继续只烧进自身背景 alpha，绝不输出会影响子节点的父级 `Opacity`。

### 5.3 文本、实例、图标与图片

- 多段富文本输出一个 `TextBlock` 和多个 `<Run>`，各段能解析的样式分别保留；长文本仍从 `rowTexts` 回填并受 `allTexts` 闭集校验。
- `INSTANCE` 当前变体可正常渲染；无法转换的 `_variantProps` 须在 XAML 注释和报告中保留，不得静默丢弃。
- `PATH` 继续通过 `icons.json` → `mcp__extractSvg` → `svg-to-xaml-path` 回填。图标清单应包含节点、位置、目标尺寸及可解析的颜色上下文。
- `IMAGE` 节点生成 `<Image>` 占位和 `images.json` 清单（节点 ID、名称、尺寸、可用资源线索、不可恢复原因）。对于 `url([object Object])` 等上游不可恢复 URL，保留具名 TODO，不把空 Canvas 当作图片已转换。

### 5.4 可选项目资产映射

#### Meta Rules

在初始区块目录成功且用户选择启用增强映射时，编排层可调用 `mcp__getMeta(fileId)`。其 `rules` 是增强输入而非硬依赖：MCP 不可用、规则为空或格式异常时，记录降级原因后走现有 DSL 路径。

可消费的语义段落：

| 段落 | 用途 | WPF 结果 |
|---|---|---|
| `## Design Tokens` | 颜色、字体、间距、圆角映射 | 优先引用已验证的 WPF 资源 key；未映射时保留设计令牌/字面值和 TODO |
| `## Component Mapping` | 层名前缀到项目控件的映射 | 将明确匹配的节点渲染为注册的自定义控件 |
| `## Layer Anchors` | 层名中的显式组件意图 | 优先级最高的组件选择来源 |
| `## Constraints` | 禁止硬编码、必须复用等项目规则 | 转换后审计项，失败或告警写入报告 |

#### Layer Anchor

层名可使用 `<--@Component.variant-->` 标记设计师的显式意图。锚点只作为**查询 key**；转换器只接受在 Meta Rules 或项目映射白名单中解析过的组件及属性，禁止把锚点字符串直接拼入 XAML。仲裁顺序如下：

```text
已验证 Layer Anchor
  > Meta Component Mapping
    > 目标项目资源/控件映射
      > 可靠的 DSL 语义判断
        > 原生 WPF 直译（Canvas/Border/Grid/...）
```

每个决策记录 `source`、`confidence`、`fallbackReason`，供报告与用户确认使用。

### 5.5 布局语义化与安全回退

现有 `flexContainerInfo` 是最高可信的布局来源，仍直接映射为 `StackPanel`/`Grid`。对于未使用 flex 的节点，可选预分析层仅在满足明确阈值时提出候选：同轴对齐可建议 `StackPanel`，高重叠可建议 `Grid`/覆盖容器，连续同结构节点可建议 `ItemsControl`，溢出可建议 `ScrollViewer`。

- 候选必须携带证据和置信度；低置信度或可能改变视觉坐标的候选一律回退为 `Canvas`。
- 识别为重复列表只生成可接管的 `ItemsControl` 模板/注释，不虚构数据源、绑定路径或业务模型。
- 任何语义化转换不得破坏原有区块 `splitContainers` 的页面级绝对坐标。

### 5.6 确认门与报告

保留现有首个确认门：在拉取 section 目录后，明确 section 范围、输出目录、页面名，未经确认不读取 section DSL。

启用项目映射或存在低置信度方案时，在写文件前展示可选的“生成方案摘要”：布局树、命中组件、Token 覆盖率、待导出图像/图标和回退节点。用户可接受、修改映射或选择纯 DSL 模式。

成功时在输出目录写 `conversion-report.json`，至少包含：

```json
{
  "sections": [{"index": 0, "renderMode": "flex"}],
  "tokenCoverage": {"mapped": 0, "literal": 0, "missing": []},
  "componentMapping": [{"nodeId": "", "source": "anchor", "confidence": 1.0}],
  "assets": {"icons": [], "images": []},
  "fallbacks": [],
  "manualHandoffs": []
}
```

报告不能取代 XAML 注释中的关键资源缺口，也不能改变 CLI 静默成功契约。

### 5.7 可选视觉验证与反馈

当用户提供设计截图、目标 WPF 项目可运行且明确选择验证时，Skill 可调用 `optimus-qa-ui-consistency-check` 或等效已配置能力：

1. 先做轻量参考图审阅，检查元素完整性、布局、关键间距、颜色、圆角、阴影和滚动边界；
2. 再进行实际页面截图与设计对比，输出模块级差异；
3. 只有用户同意自动修正时，才最多进行 3 轮、每轮基于差异报告的受控修复；
4. 达不到目标时停止，交付当前结果、差异清单与人工介入建议。

反馈默认写入项目 `.mastergo-dsl/feedback/`，包含输入版本、差异和修正记录；不得自动修改插件的 `references/`、版本或规则文件。

## 6. 错误、降级与安全策略

| 场景 | 行为 |
|---|---|
| DSL 关键坐标、文本闭集、PATH `svgShortKey`、断链样式缺失 | 延续 exit 2 硬停止 |
| Meta Rules 不可用/为空/局部格式错误 | 正常转换，报告写明规则降级 |
| 未注册 Layer Anchor 或组件映射冲突 | 不生成任意自定义控件；报告并回退原生 WPF |
| 图像 URL 丢失/不可恢复 | 生成具名图片 TODO 与 `images.json`，不声称资源可用 |
| 不支持的样式、状态或富文本属性 | 尽量保留可用部分，剩余项写报告和 XAML 注释 |
| 截图或运行环境不可用 | 跳过视觉验证，不阻断转换，报告标注未验证 |

## 7. 验收标准

### 7.1 离线转换器

- 数值排序 fixture 覆盖 `section-2.json` 与 `section-10.json`，输出顺序正确。
- 带可靠字段的 fixture 可生成尺寸、Padding、边框、圆角、文本基础样式，且 opacity 不影响子节点。
- 富文本 fixture 输出多个 `Run`；IMAGE fixture 同时生成 XAML 占位与 `images.json`；INSTANCE fixture 保留变体接管信息。
- 所有新资源和报告在验证成功后共同写入；故意触发硬错误时无新增输出目录/文件。
- 全量 `unittest` 通过，且成功 CLI stdout/stderr 均为空。

### 7.2 增强映射

- Meta Token、组件映射、Layer Anchor 分别有正常、缺失、格式错误、冲突和未注册 fixture。
- 锚点映射只生成白名单内控件；未注册锚点安全回退。
- `conversion-report.json` 能追溯每个 Token/组件/回退决定的来源。

### 7.3 视觉验证

- 无截图、无项目运行条件时可完整降级且不影响离线转换。
- 有截图与运行条件时产出差异报告；自动返工最多 3 轮并可中止。
- 反馈只写项目侧路径，插件目录内容不被自动改写。

## 8. 版本与交付规范

每个具有用户可见新能力的阶段按 Skill 级语义版本作 Minor 升级，更新 `CHANGELOG.md`；对既有插件内容的发布同步升级 `.claude-plugin/marketplace.json` Patch 版本。所有实现提交遵循仓库 `commit-cc-plugin` 流程；本设计文档本身不包含提交操作。
