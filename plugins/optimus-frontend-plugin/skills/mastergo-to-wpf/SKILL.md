---
name: mastergo-to-wpf
description: 当用户提供 MasterGo 设计稿链接并要求生成 WPF 界面、XAML 页面或把设计稿转成 WPF 代码时使用此 Skill；组件优先组装可验证的 XAML、资源清单与转换报告，并可选复用经白名单验证的项目资源和控件。
metadata:
  version: "1.2.0"
  author: desktop client team
  category: generator
compatibility: Python 3；需 mastergo-magic-mcp（本仓库 plugins/optimus-mcp-servers/.mcp.json 内置）与 MASTERGO_TOKEN；需 MasterGo Team 版及以上，草稿箱文件不可用。
allowed-tools: Read Write Bash PowerShell mastergo-magic-mcp
---

# MasterGo 设计稿转 WPF XAML

将 MasterGo 分区 DSL 组装为可手工接管的 WPF 页面：优先复用已匹配的组件库、可靠尺寸、盒模型、基础文字样式、富文本、颜色资源、图标/图片清单和 `conversion-report.json`。默认生成原生 WPF；**只有经过项目映射白名单验证的锚点才会生成自定义控件**。仅当项目约定声明 MVVM 框架时生成标注 TODO 的 ViewModel 骨架；不生成绑定、命令体或业务逻辑；设计改动应生成新文件，不做增量同步。

## Step 0：前置检查

以下任一条件不满足，停止且不要读取设计：`MASTERGO_TOKEN` 已配置；文件属于 MasterGo Team 版或以上且不是草稿箱；分享链接可解析出 `fileId`/`layerId`。

## Step 1：拉取目录与确认门

调用不带 `sectionIndex` 的 `mcp__getDesignSections`，原样写入 `.mastergo-dsl/sections-list.json`。区块数超过 8 时停止并请用户指定范围。

### 🔴 CHECKPOINT：确认范围、输出和模式

在读取任一分区 DSL 前，展示：待处理 `sectionIndex`、拟用 `--out`、`--page-name`，以及是否启用增强映射/视觉验证。**等待用户明确确认或修正。**确认前不得调用带 `sectionIndex` 的接口、运行转换器或创建产物。

## Step 2：逐区读取 DSL

确认后，按用户选择调用 `mcp__getDesignSections(sectionIndex=N)`（每批 3–5 个），保存为 `.mastergo-dsl/section-{N}.json`。禁止用 `mcp__getDsl` 绕过分区流程。转换器会按文件名中的**数值** `N` 排序。

## Step 3（可选）：预分析与项目资产映射

仅在用户选择增强模式时执行：

1. 可调用 `mcp__getMeta(fileId)`，读取 `Design Tokens`、`Component Mapping`、`Layer Anchors`、`Constraints`。Meta 缺失、为空或格式错误时，记录降级原因并继续纯 DSL 模式。
2. 扫描目标 WPF 项目的 `ResourceDictionary` 和现有控件；让用户确认映射，按 [`references/wpf-project-mapping.md`](references/wpf-project-mapping.md) 创建**严格 JSON**映射。不得接收或拼接自由 XAML。
3. 层名锚点采用 `<--@Component.variant-->`；它只是查询 key。仲裁顺序是：已验证 Anchor > 已验证 Meta/项目映射 > 可靠 DSL flex 语义 > 原生 WPF 回退。未注册或冲突的锚点必须回退，不生成自定义控件。
4. 在写文件前展示方案摘要：区块与 flex 布局、命中 Token/控件、待导出图标/图片及低置信度候选；用户可改映射或切回纯 DSL。低置信度的无 flex 节点保持 `Canvas`，不虚构 `ItemsControl` 数据源或绑定。

详情见 [`references/mastergo-meta-rules.md`](references/mastergo-meta-rules.md) 与 [`references/layer-anchor-spec.md`](references/layer-anchor-spec.md)。

## Step 4：组件匹配

1. 读取 `wpf-project-conventions/CONVENTIONS.md`；缺失或关键项为空时停止，并请用户先填写。
2. 读取组件库 `components-index.json`；不存在时说明并进入原生回退分支，沿用既有纯 DSL 模式。
3. 存在索引时运行匹配器：

```powershell
python "$SkillDir\scripts\match_components.py" --input .mastergo-dsl --index <约定输出目录>\components-index.json --out .mastergo-dsl
```

### 🔴 CHECKPOINT：展示 `component-match-report.json` 的缺失清单。
   - 用户选择“先补组件库”时结束本 Skill，转 `mastergo-to-wpf-components`。
   - 用户明确选择“原生回退”时，仅缺失项按既有纯 DSL 规则生成，并在报告标注 `fallbacks`。
   - 未确认前不得生成页面。

## Step 5：运行确定性转换器

`$SkillDir` 必须是 Skill 加载时提供的绝对 base directory（不要使用用户项目 cwd）。转换器不联网、不读 token、不调 MCP。

```powershell
$SkillDir = "<本 skill 的 base directory>"
python "$SkillDir\scripts\dsl_to_xaml.py" --input .mastergo-dsl --out src\Views --page-name LoginPage
# 仅在用户确认了严格映射后追加：
# --mapping .mastergo-dsl\wpf-project-mapping.json
```

成功时 exit `0`，stdout/stderr 均为空；关键 DSL 缺失时 exit `2`，stdout 为空，stderr 为单行 `error: ...`。所有输出先完整渲染和校验，再共同写入；硬错误不会创建新的输出目录或半成品。

| 文件 | 内容 |
|---|---|
| `{page-name}.xaml` | 原生 WPF 页面；可靠字段会生成 `Width`/`Height`、`Border`、`Padding`、边框、圆角和基础文字属性 |
| `Colors.xaml` | 未映射设计 Token 的 `SolidColorBrush`；页面仅在需要时引用它 |
| `icons.json` | `PATH` 的 `svgShortKey`、节点、位置、尺寸和颜色上下文 |
| `images.json` | 所有 `IMAGE` 节点的资源线索、状态及不可恢复原因 |
| `conversion-report.json` | section、Token 覆盖、控件决策、资产、回退、人工接管和未验证项 |

`FRAME opacity` 只合并进自身背景 alpha，绝不输出会影响子节点的父级 `Opacity`。富文本将输出多个 `Run`；INSTANCE 不能映射的 `_variantProps` 会同时出现在 XAML 注释与报告。`IMAGE` 生成具名占位；`url([object Object])` 视为上游不可恢复，不得声称已下载或转换。

当项目约定声明 MVVM 框架时，ViewModel 仅生成骨架：与设计稿文本对应的属性占位及约定基类/命令类型；数据源、命令体和业务逻辑一律标注 TODO，不猜测。约定未声明 MVVM 框架时不生成 ViewModel，保持既有纪律。

## Step 6：图标回填

逐条读取 `icons.json`：用 `mcp__extractSvg(svgShortKey=...)` 获取 SVG，交给 `optimus-frontend-plugin:svg-to-xaml-path` 的 `merge_svg_paths.py --format data`，将 `Data` 回填对应 `<!-- ICON:{svgShortKey} --> <Path .../>`，保留位置和尺寸。缺 `svgShortKey` 会使 CLI exit 2，须据实转达。

## Step 7（可选）：视觉验证

仅当用户提供设计截图、项目可运行且明确选择验证时，按 [`references/visual-validation.md`](references/visual-validation.md) 使用 `optimus-qa-ui-consistency-check` 或已配置等效能力：先轻量审阅，再比较运行截图，输出模块级差异。自动修正必须单独 opt-in，最多 3 轮；反馈只能写目标项目 `.mastergo-dsl/feedback/{page-name}/`，不得改写本插件的 `references/`、版本或规则文件。

## 交付纪律与红线

- 交付实际生成的 XAML、全部清单与报告；不得将 exit 2、未导出的图片或未注册映射包装成成功。
- 将报告中的 `fallbacks`、`manualHandoffs`、`missingDimensions` 和 `unverified` 摘要告知用户。字体不会被自动替换；提示用户确认 Windows 字体可用性。
- 不猜测 Button 等业务控件、图片 URL、图标 Path.Data、绑定、数据源或业务模型。
- 不在确认门前读取分区、生成文件或调用转换器；不全量转换超过 8 个分区；不绕过分区调用 `getDsl`。
- 不将 Anchor、Meta 或映射中的字符串直接拼进 XAML。仅允许严格映射中的资源 key、已声明 xmlns、控件类型、属性和值。

## 本地测试

```powershell
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"
```

映射字段、精确转换规则和错误契约见 [`references/dsl-mapping.md`](references/dsl-mapping.md)。