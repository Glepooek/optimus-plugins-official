# DSL → XAML 完整映射表

本文件是按需查阅的参考数据，不是决策依据。判据速查、静默行为清单见 [`SKILL.md`](../SKILL.md)。

以下所有行为均对照 `scripts/dsl_to_xaml.py` 源码逐条核实，并用 `scripts/assets/` 的 fixture 实跑验证（验证记录见仓库 `.superpowers/sdd/2026-08-02-mastergo-to-wpf/task-8-9-report.md`）。

## 1. 布局判据

```
节点有 flexContainerInfo ?
├── 是 → flexDirection == "row"（默认，缺省即视为 row） → <StackPanel Orientation="Horizontal">
│        flexDirection == "column"                       → <StackPanel Orientation="Vertical">
│        任一子节点带 flexGrow（真值）                     → 改用 <Grid>：
│            row    → Grid.ColumnDefinitions，每列 Width="*"，子节点标 Grid.Column
│            column → Grid.RowDefinitions，每行 Height="*"，子节点标 Grid.Row
│        gap（非零）→ 除最后一个子节点外，其余追加 Margin
│            row    → Margin="0,0,{gap},0"
│            column → Margin="0,0,0,{gap}"
│        ⚠️ 绝不给它或其直接子节点加 Canvas.Left/Top（flex 容器自身若处于绝对定位父级下，
│           容器本身仍可带 Canvas.Left/Top；约束只针对其直接子节点）
└── 否 → 通用 <Canvas>，子元素 Canvas.Left/Top = layoutStyle.relativeX/relativeY
         子节点缺 layoutStyle.relativeX 且 relativeY 时 exit 2（见 §4 硬停止）
```

**实测：混合 flexGrow 未特殊处理。** 同一行内部分子节点带 `flexGrow`、部分不带时，只要有一个子节点带，全部子节点都会等分为 `Width="*"`/`Height="*"` 列/行——不带 `flexGrow` 的子节点原本期望保留固定尺寸的意图会丢失。这是已知简化，未在需求范围内修复。

**padding 字段：脚本完全不读取。** `flexContainerInfo.padding` 无论是否存在，都不影响输出——不生成 `Padding`，也不生成 `Margin` 补偿。

**页面外壳：** 固定为最外层 `<Canvas>`，每个区块用 `splitContainers[i].x`/`y`（缺省 `0`）定位为一个子 `<Canvas Canvas.Left="..." Canvas.Top="...">`，区块内的节点树在其中递归渲染。区块与 `splitContainers` 按数组下标一一对应；`splitContainers` 数组比区块数短时，缺失项按 `{}` 处理，`x`/`y` 静默取 `0`。

## 2. 节点类型表

| DSL `type` | 实际输出 | 说明 |
|---|---|---|
| `TEXT` | `<TextBlock Text="..." />` | 见 §5 文本规则 |
| `PATH` | `<!-- ICON:{svgShortKey} -->` 注释 + `<Path />` 占位 | 缺 `svgShortKey` 时 exit 2 |
| 带 `flexContainerInfo` 的任意类型 | `<StackPanel>` 或 `<Grid>` | 见 §1 |
| **其余全部**（`FRAME`、`GROUP`、`INSTANCE`、`IMAGE`、任何未识别的 `type`，含无 `type` 字段） | 通用 `<Canvas>`，子节点递归、各自 `Canvas.Left`/`Top` | **无区分**——脚本不按 `type` 字符串分支，只按「有没有 `flexContainerInfo`」和「是不是 `TEXT`/`PATH`」三路判断。`INSTANCE` 的 `_variantProps` **不会**被保留为注释或以任何形式输出；`IMAGE` 节点**没有**占位符或告警，与普通 `FRAME` 完全一样处理 |

> 设计文档 §5.2 曾设想 `INSTANCE` 的 `_variantProps` 保留为注释、`FRAME`/`GROUP` 依 fill/stroke/padding 选择 `Border` 还是 `Grid`——实测均**未实现**：脚本没有 `Border` 输出路径，`strokeColor`/`strokeWidth` 字段也从未被读取。当前版本只有一种通用容器 `<Canvas>`。

## 3. 样式（颜色解析优先级）

`node_colour(node, styles)` 的实际解析顺序：

1. `node._token` **与** `node._color` 都读取；若 `_color` 非空，直接用它作为颜色。
2. 若 `_color` 为空/缺失，退回读取 `node.fill`（字符串，样式表键名），查 `section.styles[fill].value[0].color`；查不到时 exit 2（`references style '...', which is not in dsl.styles`）。
3. 上述两条都拿不到颜色 → 该节点**不输出**任何 `Background=`/`Foreground=` 属性（不是空字符串占位，是属性完全不出现）。

`_token` 只影响 **key**，不影响颜色来源——`_token` 存在时输出 `{StaticResource <key>}` 并在 `Colors.xaml` 登记一条 `SolidColorBrush`；`_token` 缺失但颜色能解析出来时，直接写字面 hex 值，`Colors.xaml` 中**不会**有对应条目。

令牌名转 XAML key（`resource_key`）：按非字母数字字符切分，每段首字母大写后拼接。`Fill/Fill-2` → `FillFill2`；`Text/Text-4` → `TextText4`。`Colors.xaml` 中每条 `SolidColorBrush` 前保留一行注释 `<!-- 原始令牌名 -->`。

`strokeColor`/`strokeWidth`/`padding` 字段**从未被读取**，无论出现与否都不影响输出（不生成 `BorderBrush`/`BorderThickness`/`Padding`）。

## 4. 两处特殊处理（已实现，已验证）

**FRAME 的 `opacity`：** 只作用于自身背景色，绝不翻译为 WPF 的 `Opacity=` 属性（那会连子元素一起透明）。`opacity < 1.0` 时，`with_alpha()` 把颜色烧进 alpha 通道：`opacity=0.5` + `#4E5969` → `#804E5969`（先取 3 位/6 位 hex 规范化为 6 位，再前置两位十六进制 alpha）。**此分支下 `_token` 完全被绕过**——即使节点有 `_token`，`opacity < 1.0` 时也无条件写字面色，不查/不生成 `StaticResource`（因为资源字典里的画刷本身不透明，不能表达每节点各异的透明度）。`opacity >= 1.0` 或未设置时不受影响，按 §3 的正常优先级解析。

实测验证（`opacity-frame.json`）：
```xml
<Canvas Background="#804E5969">
  <TextBlock Canvas.Left="8" Canvas.Top="20" Text="子元素" />
</Canvas>
```
子元素的 `TextBlock` 没有任何 `Opacity`/透明度相关属性——不透明，未受父级 `opacity` 影响。

**光栅图片的上游 bug（`url([object Object])`）：** **脚本层完全不处理**，因为脚本根本不识别 `IMAGE` 类型（见 §2），更不读取 `cssCode` 字段。设计文档 §5.4 要求「遇到须输出占位并具名告警」——这一要求**未在脚本中实现**；`IMAGE` 节点走通用 `<Canvas>` 分支，零占位符、零告警。图片需求超出本 skill 范围：图片需要另行下载，本转换器不做资源下载。

## 5. 文本回填规则

- 短文本（≤ 50 字符）直接取 `node.text` 数组，逐段 `run.get("text", "")` 拼接（`node_text`）——**多段富文本被拼接成一整个纯文本字符串**，各段各自的格式（加粗/颜色/字号）不保留，也不产生多个 `<Run>`。
- 长文本（> 50 字符）在节点树中以占位符 `T{sectionIndex}|{nodeId}` 出现，正则 `\AT\d+\|[^\s|]+\Z` 识别。真实文本从 `section.dsl.rowTexts`（顶层字段名是 `rowTexts`，不带 `dsl.` 前缀）按以下顺序取：
  1. 优先找 `rowTexts` 中 `parentName == node.name` 且未被标记 `_placeholder` 的条目；
  2. 找不到则按当前 section 内「已消费的非占位符 `rowTexts` 计数」顺序取下一条；
  3. 两者都取不到 → exit 2（`holds placeholder ... but no matching entry exists in dsl.rowTexts`）。
- `_placeholder: true` 的 `TEXT` 节点（设计师留的样板文字，如水印图层名）**整体跳过**，不输出 `TextBlock`，不计入 `EMITTED_TEXTS`。
- **闭集校验**：转换过程中每一段实际写入页面的文本都记入 `EMITTED_TEXTS`；写文件之前，逐条核对是否存在于 `sections-list.json` 的 `rootMetadata.allTexts` 数组中，不在其中即 exit 2（`is not in rootMetadata.allTexts; the design's text is a closed set, so this string would be fabricated`）。**该校验依赖 `rootMetadata.allTexts` 是一个数组**——若该字段缺失或类型不是数组，`verify_texts` 直接返回，闭集校验被整体跳过，不报错也不告警（见 SKILL.md 静默行为清单第 5 条）。

## 6. 错误信息原文

以下为对 `dsl_to_xaml.py` 实跑捕获的 stderr 原文（exit code 均为 2，stdout 均为空字符串）：

| 情形 | stderr 原文 |
|---|---|
| `--input` 目录不存在 | `error: input directory not found: {path}` |
| 目录存在但无 `sections-list.json` | `error: sections-list.json not found in {directory}; run mcp__getDesignSections without a sectionIndex first and save its response there` |
| JSON 语法错误 | `error: {文件名} is not valid JSON: {json 解析器原始报错}` |
| 文件非 UTF-8 编码 | `error: could not read {文件名}: 'utf-8' codec can't decode byte ...` |
| `_token`/`fill` 引用的样式键不存在 | `error: node {id} references style '{fill值}', which is not in dsl.styles; re-fetch this section's DSL` |
| 绝对定位节点缺 `layoutStyle.relativeX`/`relativeY`（且不在 flex 容器内） | `error: node {id} ({name}) has no layoutStyle.relativeX/relativeY and is not inside a flex container; its position cannot be determined` |
| `PATH` 节点缺 `svgShortKey` | `error: PATH node {id} ({name}) has no svgShortKey; its vector cannot be fetched — re-fetch this section's DSL` |
| 长文本占位符在 `rowTexts` 中找不到匹配 | `error: node {id} holds placeholder '{占位符}' but no matching entry exists in dsl.rowTexts; re-fetch this section's DSL` |
| 输出文本不在 `allTexts` 闭集内 | `error: generated text '{文本}' is not in rootMetadata.allTexts; the design's text is a closed set, so this string would be fabricated` |

以上错误在 exit 2 时，`--out` 目录**不会被创建**——`main()` 里 `load_sections`/`render_page`/`verify_texts` 全部在 `out_dir.mkdir()` 与三个写文件动作之前完成，任何一步抛 `ConversionError` 都不会留下半成品文件。
