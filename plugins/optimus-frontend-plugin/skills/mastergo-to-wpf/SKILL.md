---
name: mastergo-to-wpf
description: 当用户提供 MasterGo 设计稿链接并要求生成 WPF 界面、XAML 页面或把设计稿转成 WPF 代码时使用此 Skill；产出 XAML 页面脚手架、颜色资源字典与图标，供开发者手工接管。
metadata:
  version: "1.0.2"
  author: desktop client team
compatibility: Python 3；需 mastergo-magic-mcp（本仓库 plugins/optimus-mcp-servers/.mcp.json 内置）与 MASTERGO_TOKEN；需 MasterGo Team 版及以上，草稿箱文件不可用。
allowed-tools: Read Write Bash PowerShell mastergo-magic-mcp
---

# MasterGo 设计稿转 WPF XAML

从 MasterGo 设计稿链接生成 WPF XAML 页面脚手架：布局结构、几何坐标、颜色令牌、图标占位。产物需开发者手工接管——替换成真控件、接数据绑定、补尺寸。**不做可重复同步**：设计稿改了就重新生成到新文件。

## Step 0：前置检查

🔴 以下任一条件不满足，停止并向用户说明，不要继续：

- `MASTERGO_TOKEN` 未配置。
- 文件不在 MasterGo Team 版（或以上）的团队项目内——**草稿箱文件不可用**。
- 用户给的是分享链接但解析不出 `fileId`/`layerId`。

## Step 1：拉取区块目录

调用 `mcp__getDesignSections`（**不带** `sectionIndex`），把返回的 JSON 原样存为 `.mastergo-dsl/sections-list.json`。

🔴 返回的区块数 > 8 时停止，请用户指定要转换的具体区块，不要一次性全部转换。

## 🔴 CHECKPOINT · 确认转换范围与输出名称

当区块数 ≤ 8 时，在拉取任一 `section-{N}.json` 前，向用户展示将要转换的 `sectionIndex` 列表，以及拟使用的 `--out` 目录和 `--page-name`；等待用户明确确认或修正。

🛑 收到确认前，**不得**调用带 `sectionIndex` 的 `mcp__getDesignSections`，不得运行转换器，也不得创建 XAML、颜色或图标产物。用户缩小范围、改输出目录或改页面名后，按其最新选择执行。

## Step 2：逐区拉取 DSL

对每个要转换的区块调用 `mcp__getDesignSections(sectionIndex=N)`，每批 3-5 个，每区结果存为 `.mastergo-dsl/section-{N}.json`（`{N}` 用该区块的 `sectionIndex`，不是流水号）。

⚠️ 分区流程一旦启动，`mcp__getDsl` 会被运行时封锁（报错提及「195KB+ 完整 DSL」）。**禁止**改用 `getDsl` 绕过。

🔴 **`section-{N}.json` 文件按文件名字符串排序处理，不是按数值排序。** 双位数区块索引会插到个位数之前（`section-10.json` 排在 `section-2.json` 之前），页面里各区块的先后顺序会因此错乱。转换前核对 `.mastergo-dsl/` 目录里实际有哪些 `section-*.json`，索引跨个位数/两位数时尤其要检查生成结果的区块顺序是否符合预期。

## Step 3：运行转换器

`$SkillDir` 必须替换为**本 skill 加载时给出的 base directory**。**始终用该绝对路径**——本 skill 通常从插件缓存加载，cwd 是用户的项目目录，与 skill 目录无关。

```powershell
$SkillDir = "<本 skill 的 base directory>"

python "$SkillDir\scripts\dsl_to_xaml.py" --input .mastergo-dsl --out src\Views --page-name LoginPage
```

`--page-name` 缺省为 `GeneratedPage`。成功时 **exit 0，stdout 和 stderr 均为空**，在 `--out` 目录写入三个文件：

| 文件 | 内容 |
|---|---|
| `{page-name}.xaml` | 页面：外层 `<Canvas>` 逐区放置，内部按 flex/绝对定位递归渲染。有颜色令牌时，`UserControl.Resources` 自动引用同目录下的 `Colors.xaml`（`<ResourceDictionary Source="Colors.xaml" />`），无需手工接线 |
| `Colors.xaml` | `_token`/`fill` 解出的颜色汇总为 `SolidColorBrush`，原始令牌名保留为注释 |
| `icons.json` | 待转图标清单：`[{"svgShortKey","nodeId","name"}, ...]`，无图标时为 `[]` |

失败时 **exit 2，stdout 为空**，`--out` 目录**不会被创建**（校验发生在写文件之前，不产生半成品）。stderr 是 `error: ...` 单行，须原样转达。真实错误原文见 [`references/dsl-mapping.md`](references/dsl-mapping.md#错误信息原文)。

**本脚本从不产生「exit 0 + stderr 告警」——只有「exit 0 静默成功」或「exit 2 硬停止」两种结果。** 不要向用户描述某种情况会「报警告」，除非已在 `references/dsl-mapping.md` 的静默行为清单里核实过。

## Step 4：图标回填

对 `icons.json` 中每一项：

1. 调 `mcp__extractSvg(svgShortKey=...)` 取回真实 SVG 标记。
2. 交给 `optimus-frontend-plugin:svg-to-xaml-path` 转成 `Path.Data`（`merge_svg_paths.py --svg '<svg>…</svg>' --format data`）。
3. 用返回的 `Data` 回填 XAML 中对应的 `<!-- ICON:{svgShortKey} --> <Path .../>` 占位——把空的 `<Path />` 换成 `<Path Data="..." .../>`，保留其 `Canvas.Left`/`Canvas.Top`。

## Step 5：交付纪律

1. 只交付 `--out` 目录里的实际文件内容；不得声称转换成功却隐瞒 exit 2 的错误。
2. 明确告知用户哪些节点需要人工换成真控件——本转换器**不猜控件语义**：圆角矩形 + 居中文字仍然是 `Canvas` + `TextBlock`，不是 `Button`。
3. 明确告知**所有元素都没有 `Width`/`Height`/`Padding`/`BorderThickness`/`BorderBrush`**（见下方静默行为清单第 1 条）——这是本转换器最容易被忽视的缺口，必须每次主动提醒。
4. 设计稿常用的 `Inter`/`Roboto` 等字体在 Windows 上通常不存在；转换器不检测、不替换，须提醒用户自行确认字体可用性或改用系统字体。

## 红线：不要做什么

- **不要**在 `MASTERGO_TOKEN`、Team 项目/非草稿箱或链接标识任一前置条件未通过时调用设计读取工具，或猜测设计稿内容。
- **不要**在区块数 > 8 时擅自全量转换、只转换前 8 个，或把分区流程改回 `mcp__getDsl`。
- **不要**在用户确认 `sectionIndex` 范围、输出目录和页面名之前读取分区 DSL、运行转换器或创建产物。
- **不要**把转换器的 exit 2、缺失 `svgShortKey` 或未处理的 `IMAGE` 节点包装成“转换成功”；只交付实际生成的文件。
- **不要**猜测控件语义、图标 `Path.Data`、尺寸/边框/圆角或缺失的图片 URL；这些必须明确交由人工补齐或基于实际 DSL/SVG 回填。

## 静默行为清单（转换前须人工检查）

以下情形 **exit 0、无 stdout、无 stderr，产物合法但不完整或不对**，脚本无法自动发现：

| # | 情形 | 后果 | 严重度 |
|---|---|---|---|
| 1 | 任何节点都不产出 `Width`/`Height`/`Padding`/`BorderThickness`/`BorderBrush`/圆角 | 所有容器按内容自然定尺寸；绝对定位元素的可视范围与设计稿不符，需要手工逐个补尺寸 | **结构缺失** |
| 2 | `FRAME`/`GROUP`/`INSTANCE`（及任何未识别的 `type`）统一落到通用 `<Canvas>` 分支 | `INSTANCE` 的 `_variantProps`（如选中态）**完全丢弃**，连注释都没有；只转出当前变体的几何，其他状态无痕迹 | **状态缺失** |
| 3 | `IMAGE` 类型节点没有专门分支 | 与 FRAME 走同一条通用 `<Canvas>` 逻辑，**没有任何占位符或注释**标记「这里本应是一张图」——不像 `PATH` 节点会留下 `<!-- ICON:... -->` | **内容缺失** |
| 4 | 富文本多段 `text` 数组被直接拼接成一个字符串 | 各段落各自的加粗/颜色/字号等差异全部丢失，`TextBlock` 只有一段纯文本 | **格式丢失** |
| 5 | `sections-list.json` 缺失 `rootMetadata.allTexts` 或该字段不是数组 | 防幻觉的闭集校验被**整体跳过**，任何文本都会通过，不会报错 | **校验失效** |
| 6 | 混合 `flexGrow`（同一行/列里部分子节点带 `flexGrow`、部分不带） | 全部子节点等分为 `*` 宽/高列，不带 `flexGrow` 的子节点应有的固定尺寸意图丢失 | 布局偏差 |
| 7 | `splitContainers` 数组比区块数量短 | 缺失的区块外层 `Canvas.Left`/`Canvas.Top` 静默取 `0`，位置可能与设计稿画布坐标不符 | 布局偏差 |
| 8 | `section-*.json` 按文件名字符串排序（非数值） | 双位数区块索引排到个位数之前，页面区块顺序错乱（见 Step 2 🔴） | 结构错误 |

完整映射表、颜色解析优先级的真实实现细节、`opacity`/图片 bug 的处理，见 [`references/dsl-mapping.md`](references/dsl-mapping.md)。

## 已知限制

1. 需 MasterGo Team 版及以上，草稿箱文件不可用。
2. 未用 autolayout 的设计稿会退化为全 `Canvas` 绝对定位，不可响应式。
3. 不识别项目现有组件库，产出的是原生 WPF 元素（`Canvas`/`StackPanel`/`Grid`/`TextBlock`/`Path`）。
4. 组件多状态（hover/disabled/selected 等）不转换，只出当前变体，且不留痕迹（见静默行为清单第 2 条）。
5. 光栅图片没有专门处理：既不下载，也不留占位符或告警；且存在上游 `url([object Object])` 丢失 URL 的已知 bug，脚本无法恢复。

## 本地测试

```bash
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"
```
