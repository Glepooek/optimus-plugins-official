# MasterGo 转 WPF XAML Skill 优化完善 — 实施计划

> **关联规格**：[2026-08-03-mastergo-to-wpf-optimization-design.md](../specs/2026-08-03-mastergo-to-wpf-optimization-design.md)
>
> **初版基线（只读）**：[初版设计](../specs/2026-08-02-mastergo-to-wpf-design.md) · [初版实施计划](2026-08-02-mastergo-to-wpf.md)
>
> **目标**：在不破坏现有确定性 DSL→XAML 转换器及其“静默成功、原子失败、离线测试”契约的前提下，提高 WPF 视觉还原、项目资产复用能力和可验证性。

## 实施总则

- 不修改或重写初版设计/计划文档；本计划只作用于 `mastergo-to-wpf` 的后续优化实现。
- 保持 Python 标准库 + `unittest`，不为解析规则或报告引入第三方依赖。
- 保持 `dsl_to_xaml.py` 不联网、不读取环境变量、不调用 MCP；MCP 只在 `SKILL.md` 编排层使用。
- 现有成功契约不可破坏：exit 0 时 stdout/stderr 为空；`conversion-report.json` 等信息写入文件，不在 stderr 写“成功告警”。
- 每个阶段先新增失败的黑盒契约测试和 DSL fixture，再实现最小功能，最后全量回归。
- 涉及用户可见能力时升级 `SKILL.md` 的 Minor 版本并更新 `CHANGELOG.md`；最终发布时将 `.claude-plugin/marketplace.json` 升 Patch。提交时使用项目规定的 `commit-cc-plugin`，不在本计划执行阶段手工提交。

## 基线与共用验证命令

**基线文件：**

```text
plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/
├── SKILL.md
├── CHANGELOG.md
├── test-prompts.json
├── references/dsl-mapping.md
└── scripts/
    ├── dsl_to_xaml.py
    ├── test_dsl_to_xaml.py
    └── assets/
```

每个阶段完成后执行：

```powershell
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"
```

当前基线为 37 条测试通过。每次扩展测试数量后，文档中应以实际输出更新该数字，不能硬编码预期总数。

---

## Phase 0：契约对齐与排序正确性

**目的**：先消除已知的无声顺序错误和文档/测试期望漂移，为后续改造建立可信基线。

### 修改范围

- Modify: `scripts/dsl_to_xaml.py`
- Modify: `scripts/test_dsl_to_xaml.py`
- Create: `scripts/assets/numeric-section-order.json`
- Modify: `SKILL.md`
- Modify: `references/dsl-mapping.md`
- Modify: `test-prompts.json`
- Modify: `CHANGELOG.md`

### 任务

1. 为 `load_sections()` 新增数值 sectionIndex 排序：从 `section-{N}.json` 提取 `N` 并按整数排序；无法解析的文件名不应进入输入集合或应产生可诊断错误。
2. 用 section `2` 与 `10` fixture 断言页面外层区块与文本的真实数值顺序，防止再次退化为字符串排序。
3. 复核所有文档的“硬停止/静默行为”描述，使其与实现一致；不把人工检查当作已修复行为。
4. 修订 `test-prompts.json` 的首条案例：section 目录返回后必须先展示范围、输出目录与页面名，等待用户确认，才能拉取任一 section DSL 或运行 CLI。
5. 在 CHANGELOG 记录排序修复和评测预期同步。

### 验收

- `section-2.json` 在 `section-10.json` 前渲染；
- 全量 CLI 测试通过；
- 测试 prompt 与 SKILL.md 的确认门一致；
- 除计划中的目标文件外，无无关改动。

---

## Phase 1：几何、盒模型与基础文本样式

**目的**：将当前“坐标骨架”升级为具有可靠尺寸、边框、圆角和文本排版的 WPF 骨架，同时不虚构缺失设计字段。

### 修改范围

- Modify: `scripts/dsl_to_xaml.py`
- Modify: `scripts/test_dsl_to_xaml.py`
- Create: `scripts/assets/sized-border.json`
- Create: `scripts/assets/flex-padding.json`
- Create: `scripts/assets/text-style.json`
- Create: `scripts/assets/invalid-dimensions.json`
- Modify: `references/dsl-mapping.md`
- Modify: `SKILL.md`
- Modify: `CHANGELOG.md`

### 任务

1. 提取并统一校验宽、高、Padding、描边颜色/宽度、圆角、字体、字号、字重、行高、对齐和换行字段；数值必须是有限且非负的可用值。
2. 为带 fill/stroke/padding/radius 的节点选择 `Border` 容器，并在其内部维持既有 `Canvas`/`StackPanel`/`Grid` 布局；没有视觉盒模型需求时保留最简元素。
3. 为可靠尺寸生成 `Width`/`Height`；缺字段时不补默认值，写入报告候选数据（Phase 3 接入正式报告）。
4. 将 flex 容器的 Padding 映射到可承载 Padding 的外层 `Border`，并继续保证其直接子节点不出现 `Canvas.Left`/`Canvas.Top`。
5. 扩展 `TextBlock` 输出基础文字样式；设计字体在 Windows 不存在时只能交付提示，不能静默替换。
6. 保持 FRAME 的 opacity 只融合到自身 `Background` alpha，新增“有边框/子节点时仍无父级 Opacity”回归测试。

### 验收

- fixture 验证 Border、BorderBrush、BorderThickness、CornerRadius、Width、Height、Padding 与 TextBlock 样式；
- flex 子节点坐标禁止规则仍通过；
- 非法/缺失尺寸不会生成无效 XAML，也不会被编造；
- 现有颜色、长文本、图标、opacity 测试全量通过。

---

## Phase 2：富文本、实例状态与图片资源契约

**目的**：消除文本格式、组件状态和光栅图片的静默丢失，使人工接管需求可发现、可追溯。

### 修改范围

- Modify: `scripts/dsl_to_xaml.py`
- Modify: `scripts/test_dsl_to_xaml.py`
- Create: `scripts/assets/rich-text.json`
- Create: `scripts/assets/instance-variants.json`
- Create: `scripts/assets/images.json`
- Create: `scripts/assets/unrecoverable-image.json`
- Modify: `references/dsl-mapping.md`
- Modify: `SKILL.md`
- Modify: `CHANGELOG.md`

### 任务

1. 将 TEXT 的每个可解析 rich-text run 生成独立 `<Run>`，并确保拼接的实际文本仍通过 `rootMetadata.allTexts` 闭集校验。
2. 保留 INSTANCE `_variantProps`：能映射的当前状态写入 XAML；不能映射的状态以统一格式 XAML 注释和结构化条目保留。
3. 为 IMAGE 节点生成具名 `<Image>` 占位或等价的 WPF 资源接管标记，输出 `images.json`，包含 node ID、名称、尺寸、来源线索、状态和不可恢复原因。
4. 明确区分“图片资源未导出”和“上游 `url([object Object])` 不可恢复”；两者不得被描述为已转换。
5. 扩展 `icons.json` 的可选字段（位置、尺寸、可解析颜色），但保留现有必填字段以避免破坏 Step 4 图标回填流程。

### 验收

- 富文本生成多个 Run 且 XML 转义正确；
- IMAGE 不再退化为无痕 Canvas；`images.json` 无图片时为 `[]`；
- 实例状态在产物或清单中可检索；
- 图标契约和原有 37 条基线测试均未退化。

---

## Phase 3：结构化报告与项目资源映射基础

**目的**：将“有哪些内容被精确转换、回退、待人工处理”变为机器可读信息，并为项目级 Token/控件复用建立安全输入边界。

### 修改范围

- Modify: `scripts/dsl_to_xaml.py`
- Modify: `scripts/test_dsl_to_xaml.py`
- Create: `scripts/assets/report-fallbacks.json`
- Create: `references/wpf-project-mapping.md`
- Modify: `SKILL.md`
- Modify: `references/dsl-mapping.md`
- Modify: `CHANGELOG.md`

### 任务

1. 定义并输出 `conversion-report.json`：section 渲染模式、Token 统计、组件映射、资源清单、回退项、人工接管项、未验证项。
2. 报告只在完整验证成功后与 XAML/Colors/icons/images 一并写入，任何硬错误都不产生新报告。
3. 设计 WPF 项目映射文件的严格 JSON 或受限 Markdown 契约：资源 key、`xmlns` 前缀、自定义控件名、允许属性和变体映射；禁止接收自由 XAML 片段。
4. 实现显式的项目映射输入（建议 CLI `--mapping PATH`）；映射文件缺失或错误时保持纯 DSL 模式并在报告说明，而不是阻断基础转换。
5. 对现有 `_token` 预扫描：优先将可验证的设计 Token 映射为项目资源 key，未命中仍生成当前 Colors.xaml 条目或字面值并报告。

### 验收

- 成功转换会产生合法、稳定、可 JSON 解析的报告；stdout/stderr 仍为空；
- 映射缺失、格式错误、未知资源 key、冲突 key 分别有 fixture；
- 未注册自定义控件绝不进入 XAML；
- 报告能定位每个回退/人工接管项的 node ID 和原因。

---

## Phase 4：Meta Rules、Layer Anchor 与受控语义化布局

**目的**：借助设计侧显式规则和项目白名单提高组件复用率；在证据充分时降低绝对布局比例，但始终保留 Canvas 安全回退。

### 修改范围

- Modify: `SKILL.md`
- Create: `references/mastergo-meta-rules.md`
- Create: `references/layer-anchor-spec.md`
- Modify: `references/wpf-project-mapping.md`
- Modify: `scripts/dsl_to_xaml.py`
- Modify: `scripts/test_dsl_to_xaml.py`
- Create: `scripts/assets/meta-tokens.json`
- Create: `scripts/assets/component-anchor.json`
- Create: `scripts/assets/unregistered-anchor.json`
- Create: `scripts/assets/semantic-layout.json`
- Modify: `test-prompts.json`
- Modify: `CHANGELOG.md`

### 任务

1. 在已有“section 范围确认”后提供可选增强模式：读取 `mcp__getMeta(fileId)` 的 rules，解析 `Design Tokens`、`Component Mapping`、`Layer Anchors`、`Constraints`。MCP 不可用或局部格式错误时必须安全降级。
2. 定义层锚点语法 `<--@Component.variant-->` 和白名单解析流程。锚点仅是映射 key，最终控件及允许属性必须来自 `--mapping` 或已验证 Meta 映射。
3. 形成并测试固定仲裁顺序：验证通过的 Anchor > Meta Component Mapping > 项目 mapping > 高置信 DSL 语义 > 原生 WPF 直译。
4. 在写文件前展示方案摘要：布局树、映射控件、Token 覆盖、缺失资产和低置信度候选。纯 DSL 模式或所有决定高置信时不额外阻塞用户。
5. 为无 flex 的节点实现受控语义候选：仅在明确阈值下建议 `StackPanel`、`Grid`、`ItemsControl`、`ScrollViewer`；低置信度、会改变区块坐标或缺少尺寸依据时必须输出 Canvas。
6. 对重复节点只输出可人工接管的 ItemsControl 模板与 TODO，绝不捏造数据源、绑定或业务模型。

### 验收

- Meta 缺失/空/错误、Anchor 未注册/冲突均可安全回退；
- 注册 Anchor 只生成允许的控件、属性和 xmlns 前缀；
- 每个映射决定在报告中带 source、confidence、fallbackReason；
- 语义化 fixture 覆盖水平、垂直、重叠、重复和低置信回退 Canvas；
- 未经初始范围确认，仍不能读取 section DSL 或创建任何产物。

---

## Phase 5：截图辅助与可选 UI 验证闭环

**目的**：将视觉对比作为增强校验，而非使基础转换依赖设备、截图或网络。

### 修改范围

- Modify: `SKILL.md`
- Create: `references/visual-validation.md`
- Modify: `test-prompts.json`
- Modify: `CHANGELOG.md`
- Create at runtime (project side only): `.mastergo-dsl/feedback/{page-name}/...`

### 任务

1. 在输入阶段接收整页截图及局部特写；局部图必须记录其对应页面区域。未提供截图时流程完全保持 DSL 路径。
2. 在生成后、重量级对比前进行轻量参考图校验：布局层次、元素完整性、组件选择、关键间距、颜色/字体、圆角/阴影和滚动边界。
3. 当项目可运行、用户明确启用时，对接 `optimus-qa-ui-consistency-check` 或已配置的等效检查；生成模块级差异报告。
4. 自动返工必须显式 opt-in，最多 3 轮，每轮只依据当前差异报告处理严重项及有限数量的中等项；达到上限后停止并交付差异清单。
5. 反馈记录写入项目 `.mastergo-dsl/feedback/`，不得自动追加插件 `references/`，也不得自动升级版本。

### 验收

- 无截图/无设备/不启用验证时，转换仍可成功并写明“未执行视觉验证”；
- 有条件时产生可定位的验证报告；
- 返工上限和用户中止均有测试 prompt 覆盖；
- 插件目录不因一次用户转换而发生隐式变更。

---

## Phase 6：发布前质量门与文档收尾

**目的**：保证功能、测试、使用说明和版本信息同步，避免出现描述已支持但实现或评测未覆盖的漂移。

### 修改范围

- Modify: `SKILL.md`
- Modify: `CHANGELOG.md`
- Modify: `test-prompts.json`
- Modify: `references/dsl-mapping.md`
- Modify: 新增的 `references/*.md`
- Modify: `.claude-plugin/marketplace.json`

### 任务

1. 全量复核 `SKILL.md`、映射参考、实施结果与真实 CLI 行为，重点核查：成功静默、硬错误、降级、确认门、图像、映射、视觉验证。
2. 为每个 Red Flag 和关键降级路径至少保留一条 test prompt；为每项转换器功能保留离线 fixture/CLI 黑盒测试。
3. 运行全量单元测试，手工执行一个最小 DSL 和一个包含图像/锚点/Token 的复杂 DSL 烟雾测试，检查 XAML、JSON 清单和报告均可解析。
4. 按实际变更升级 Skill Minor 版本、更新 CHANGELOG；按既有插件更新规则升级 marketplace Patch 版本。
5. 若用户要求提交，调用 `commit-cc-plugin`，逐文件暂存文档与 Skill 文件，不使用手工 Git 流程。

### 最终验收清单

- [ ] 初版 2026-08-02 设计与计划文档未被修改；
- [ ] 基线及新增 `unittest` 全部通过；
- [ ] 成功转换 stdout/stderr 为空，失败 exit 2 且无半成品；
- [ ] 全部资源缺口、回退与人工接管项在 XAML 或报告中可发现；
- [ ] Meta/Anchor/项目映射未引入自由 XAML 注入风险；
- [ ] 无增强输入时，Skill 仍可离线执行原有 DSL→XAML 路径；
- [ ] 截图/视觉验证/反馈均为可选且不会隐式改写插件内容；
- [ ] 文档、测试 prompt、CHANGELOG、版本号与实际功能一致。
