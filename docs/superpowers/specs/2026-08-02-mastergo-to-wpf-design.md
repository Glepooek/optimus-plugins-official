# MasterGo 设计稿转 WPF XAML — 设计文档

- **日期**：2026-08-02
- **Skill 名**：`mastergo-to-wpf`
- **归属插件**：`optimus-frontend-plugin`
- **状态**：设计已确认，待实现

## 1. 目标与非目标

### 目标

从 MasterGo 设计稿链接生成 WPF XAML 页面脚手架：布局结构、几何、颜色令牌、图标。开发者拿到后手工接管，替换成真控件、接数据绑定。

### 非目标

- **不做可重复同步**。设计稿改了就重新生成到新文件，不处理与已修改代码的合并。
- **不猜控件语义**。圆角矩形 + 居中文字生成 `Border` + `TextBlock`，不生成 `Button`。
- **不生成 ViewModel、不接数据绑定、不写 code-behind**。
- **不碰 `optimus-fe-dev`**。该 skill 保持现状。

### 与同插件既有 skill 的边界

| Skill | 职责 |
|---|---|
| `svg-to-xaml-path` | 单个图标 SVG → `Path.Data`（本 skill **复用**它） |
| `wpf-xaml-performance` | 已有 XAML 的性能审查 |
| `optimus-qa-ui-consistency-check` | 设计稿 vs 线上页面的**校验**（只读对比） |
| **`mastergo-to-wpf`（本设计）** | 设计稿 → **整页 XAML 结构**（生成） |

QA 那个 skill 同样调 `getDsl`，但方向相反：它比对已有实现，本 skill 产出实现。不构成重复。

## 2. 关键调研结论

以下均从 `@mastergo/magic-mcp@0.2.6` 的发布包源码（`dist/index.js`，797 KB）核实，非文档转述。

### 2.1 工具清单（10 个）

`mcp__getDesignSections`、`mcp__getDsl`、`mcp__extractSvg`、`mcp__applyDesign`、`mcp__getMeta`、`mcp__getD2c`、`mcp__C2d`、`mcp__getComponentLink`、`mcp__getComponentGenerator`、`mcp__getFlutterGenerator`。

本 skill 只用前三个。

### 2.2 矢量数据不在 DSL 里（决定架构）

包内原文：

> PATH nodes carry a `svgShortKey`… **The SVG markup is NOT in the DSL.** Place `@@SVG:{svgShortKey}@@` where each icon goes, then call `mcp__applyDesign` to inject…

而 `applyDesign` 的 `targetLang` 只有 `html` 和 `dart`，**无 XAML 模式**，且它会把手写的 `<path d="…">` 判定为 `FABRICATED` 并报错。官方图标管道对 XAML 不通。

**出路**：`mcp__extractSvg` 打独立端点 `/mcp/extract-svg`，直接返回真实 SVG 标记，绕开占位符管道。

### 2.3 布局语义是显式的，不需要推断

| 判据 | 含义 | WPF 映射 |
|---|---|---|
| 节点有 `flexContainerInfo` | flex 容器，带 `flexDirection`/`gap`/`padding` | `StackPanel` / `Grid` |
| 节点无 `flexContainerInfo` | 绝对定位，用 `layoutStyle.relativeX/relativeY` | `Canvas` |
| `splitContainers` | 页面级区块，带画布绝对坐标 | 外层 `Canvas` |

包内明确禁止：不要给 flex 容器及其直接子节点加绝对定位；不要把区块用 flex 竖排堆叠。

**没有** `constraints` 字段，也没有 Figma 式的 resize 约束——要么有 flex 语义，要么什么都没有。

### 2.4 文本是闭集，不会丢失

- `rootMetadata.allTexts`（在 section LIST 响应里）：设计稿全部真实文本的**完整闭集**。
- `dsl.rowTexts`：`{text, parentType?, parentName?, _placeholder?}` 数组，按树序排列。
- `T{sectionIndex}|{nodeId}`：节点树里长文本（>50 字符）的占位，**但文本内容在上述两处都有**，无需 `applyDesign` 还原。

`allTexts` 同时是防幻觉的校验器：包内要求任何输出文本必须能在其中溯源。

### 2.5 其他硬约束

| 约束 | 出处 |
|---|---|
| 分区流程启动后 `getDsl` 被运行时封锁 | 错误信息提到「195KB+ 完整 DSL」 |
| 区块须逐个拉取，每批 3-5 个 | 包内 rules |
| FRAME 的 `opacity` 只作用于自身背景，不影响子节点 | 包内 rules（见 §5.3） |
| 图片 URL 存在上游 bug `url([object Object])` | 包内注释：「LOST by the MasterGo upstream… cannot be recovered」 |
| 需 MasterGo Team 版及以上，文件须在团队项目内 | 官方文档；草稿箱不可用 |

## 3. 目录结构

```
plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/
├── SKILL.md                     编排流程、前置检查、交付纪律
├── CHANGELOG.md
├── test-prompts.json
├── references/
│   └── dsl-mapping.md           DSL 字段 → XAML 完整映射表
└── scripts/
    ├── dsl_to_xaml.py           DSL JSON → XAML + ResourceDictionary + 图标清单
    ├── test_dsl_to_xaml.py      契约测试
    └── fixtures/                测试与示例共用的 DSL 样本
```

### 职责切分

| 组件 | 职责 |
|---|---|
| SKILL.md | 调哪些 MCP 工具、什么顺序、结果如何判断、向用户交代什么 |
| `dsl_to_xaml.py` | **纯函数**：DSL JSON 进，XAML 出。不联网、不调 MCP、不读环境变量 |
| `svg-to-xaml-path`（已有） | 图标 SVG → `Path.Data` |

脚本刻意不碰 MCP，只吃落盘的 JSON。这样测试无需 token、无需网络，`python -m unittest` 全量离线可跑。代价是多一步「MCP 结果存 JSON 再喂脚本」，该步骤顺带留下可复查的中间产物。

## 4. 数据流

```
Step 0  前置检查
        解析链接 → fileId + layerId（或 shortLink）
        🔴 MASTERGO_TOKEN 未配置 / 非 Team 版 / 文件在草稿箱 → 停止并说明

Step 1  mcp__getDesignSections（不带 sectionIndex）
        → 区块目录、splitContainers（页面绝对坐标）、rootMetadata.allTexts
        → 存 .mastergo-dsl/sections-list.json
        🔴 区块数 > 8 → 停止，请用户指定要转换的区块

Step 2  mcp__getDesignSections(sectionIndex=N)  逐区，3-5 个一批
        → 每区存 .mastergo-dsl/section-{N}.json
        ⚠️ 禁止改用 getDsl —— 分区流程启动后它被运行时封锁

Step 3  python dsl_to_xaml.py --input .mastergo-dsl/ --out src/Views/
        → {PageName}.xaml        带 <!-- ICON:S0#0 --> 占位
        → Colors.xaml            _token → SolidColorBrush
        → icons.json             待转图标清单

Step 4  对 icons.json 中每个 svgShortKey：
        mcp__extractSvg → SVG 标记
        → svg-to-xaml-path 的 merge_svg_paths.py --svg '…' --format data
        → 回填 XAML 中的占位

Step 5  交付并说明：未转换项、需人工替换为真控件处、字体可用性
```

`.mastergo-dsl/` 需加入 `.gitignore`（与仓库既有的 `.remember/`、`.codegraph/` 同类）。

## 5. 映射规则

### 5.1 布局

```
节点有 flexContainerInfo ?
├── 是 → flexDirection == "row"    → <StackPanel Orientation="Horizontal">
│        flexDirection == "column" → <StackPanel Orientation="Vertical">
│        子节点带 flexGrow          → 改用 <Grid> + ColumnDefinition="*"
│        gap                        → 子元素 Margin（末元素不加）
│        padding                    → 容器 Padding（由 Border 承载）
│        ⚠️ 绝不给它或其直接子节点加 Canvas.Left/Top
└── 否 → <Canvas> + 子元素 Canvas.Left/Top = layoutStyle.relativeX/relativeY
```

页面外壳固定为 `Canvas`，各区块按 `splitContainers` 绝对坐标定位。嵌套层级必须保留，不得把两层 flex 压平成一层。

### 5.2 节点类型

| DSL type | XAML | 说明 |
|---|---|---|
| `FRAME` / `GROUP` | `Border` 或 `Grid` | 有 fill/stroke/padding 时用 Border |
| `TEXT` | `TextBlock` | `text` 为富文本段数组，多段 → 多个 `<Run>` |
| `PATH` | `Path` | 先写 `<!-- ICON:{svgShortKey} -->`，Step 4 回填 |
| `INSTANCE` | 按几何展开 | `_variantProps` 保留为注释，不猜控件类型 |

### 5.3 样式

| DSL 字段 | XAML | 优先级 |
|---|---|---|
| `_token`（如 `Text/Text-4`） | `{StaticResource TextText4}` | 最高 |
| `_color`（如 `#4E5969`） | 字面值 / 资源字典中的值 | `_token` 缺失时 |
| `fill`（如 `paint_1:7200`） | 查 `dsl.styles` 表 | 前两者均缺时 |
| `strokeColor` + `strokeWidth` | `BorderBrush` + `BorderThickness` | — |

令牌名转 XAML key：`Text/Text-4` → `TextText4`。资源字典中保留原名为注释。

### 5.4 两处必须特殊处理

**FRAME 的 `opacity`**：只作用于自身背景，不影响子节点。**不得**翻译为 WPF 的 `Opacity`（那会连子元素一起透明），必须烧进背景色 alpha 通道——`opacity: 0.5` + `#4E5969` → `Background="#804E5969"`。

**光栅图片的上游 bug**：`cssCode` 中可能出现 `url([object Object])`。包内承认无法恢复。遇到须输出占位并具名告警，不得静默跳过。

### 5.5 文本

- 短文本取 `node.text`，长文本按 `T{si}|{nodeId}` 从 `dsl.rowTexts` / `allTexts` 回填。
- `_placeholder: true` 的条目是设计师留的样板文字，跳过。
- 用 `parentType`/`parentName` 判断归属，避免语义错配（例：`{text:"8", parentType:"INSTANCE", parentName:"删除"}` 是按钮角标，不是独立元素）。
- **闭集校验**：输出的每个文本串必须能在 `allTexts` 中找到，否则 exit 2。

## 6. 错误处理

### 6.1 硬停止（exit 2，无 stdout）

| 情形 | 理由 |
|---|---|
| DSL JSON 解析失败 / 缺 `nodes` | 输入非有效 DSL |
| 节点缺 `layoutStyle` 且非 flex 子节点 | 无法定位，不猜坐标 |
| `_token` 引用了 `styles` 中不存在的键 | 断链，不静默降级为字面色 |
| 输出文本不在 `allTexts` 闭集内 | 说明生成了幻觉文本 |
| 图片 URL 为 `url([object Object])` | 上游 bug，无法恢复 |

### 6.2 具名告警（exit 0，须转达）

- 某节点被跳过（不支持的 type）——列出 type 与节点名
- 富文本段数超阈值，可能有格式丢失
- 字体名在 Windows 上不存在（`Inter`、`Roboto` 等，设计稿常见）

### 6.3 静默行为清单（转换前须人工检查）

脚本无法自动发现，须写入 SKILL.md 并在交付时说明：

| 情形 | 后果 | 严重度 |
|---|---|---|
| 设计稿完全未用 autolayout | 全页退化为 Canvas 绝对定位，不可响应式 | **结构错误** |
| `INSTANCE` 的 `_variantProps` 表示选中态 | 只转了当前变体的几何，其他状态缺失 | **状态缺失** |
| `_placeholder: true` 样板文字 | 误当真实内容渲染 | **内容错误** |
| 幽灵图层（设计师留的空 GROUP） | 生成多余嵌套容器 | 冗余 |
| 字体回退 | 视觉与设计稿不一致 | 视觉偏差 |

## 7. 测试策略

`subprocess` 跑 CLI 比对 stdout，沿用 `test_merge_svg_paths.py` 的 `CliTestCase` 基类模式。

| Fixture | 断言 |
|---|---|
| `flex-row.json` | 输出 `StackPanel Orientation="Horizontal"` |
| `flex-grow.json` | 带 `flexGrow` 的子节点 → `Grid` + `ColumnDefinition="*"` |
| `absolute.json` | 输出 `Canvas` + `Canvas.Left`/`Canvas.Top` |
| `nested-mixed.json` | flex 内嵌 canvas，嵌套层级保持不压平 |
| `opacity-frame.json` | alpha 烧进背景色，**不生成** `Opacity` 属性 |
| `tokens.json` | `_token` → `StaticResource` + 资源字典条目 |
| `long-text.json` | `T{si}\|{nodeId}` 从 `rowTexts` 正确回填 |
| `placeholder-text.json` | `_placeholder: true` 条目被跳过 |
| `broken-ref.json` | 断链 `_token` → exit 2 |
| `hallucinated-text.json` | 文本不在 `allTexts` → exit 2 |

## 8. 版本与规范

- 新增 skill → marketplace **Minor** 升版
- SKILL.md frontmatter 遵循 `.claude/rules/skill-authoring.md`：六字段限制、`metadata.version: "1.0.0"`、`metadata.author: desktop client team`
- `compatibility` 须注明：Python 3；需 `mastergo-magic-mcp`（本仓库 `plugins/optimus-mcp-servers/.mcp.json` 内置）及 `MASTERGO_TOKEN`；需 MasterGo Team 版及以上
- `allowed-tools`：`Read Write Bash PowerShell mastergo-magic-mcp`
- 同步创建 CHANGELOG.md，初始 `[1.0.0]`

## 9. 已知限制（写入 SKILL.md）

1. 需 MasterGo Team 版及以上，草稿箱文件不可用。
2. 未用 autolayout 的设计稿会退化为全 Canvas 绝对定位。
3. 不识别项目现有组件库，产出的是原生 WPF 元素。
4. 组件多状态（hover/disabled 等）不转换，只出当前变体。
5. 光栅图片需另行下载，且存在上游 URL 丢失的可能。
