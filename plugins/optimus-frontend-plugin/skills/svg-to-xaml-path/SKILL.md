---
name: svg-to-xaml-path
description: 当用户提供本地 SVG 文件路径或完整 SVG 标记，并要求提取 path 的 d、合并多路径、生成 WPF XAML 或 Path.Data 时使用此 Skill；适用于 SVG 图标转 WPF Path 的场景。
metadata:
  version: "1.2.0"
  author: desktop client team
compatibility: Python 3；可在 Windows PowerShell 中运行随附的无第三方依赖 CLI。
allowed-tools: Read Bash PowerShell
---

# SVG 转 WPF Path

将 SVG 的路径与基本图元转换为 WPF `Path.Data` 或 XAML `Path`。无需 Inkscape。

## 识别输入

- 用户给出本地 `.svg` 文件路径时，使用 `--file`。
- 用户粘贴完整的 `<svg>...</svg>` 标记时，使用 `--svg`；不要把片段补成臆测的图形。
- 已从管道或标准输入获得完整 SVG 标记时，使用 `--stdin`。

## 运行脚本

下列命令中的 `$SkillDir` 必须替换为**本 skill 加载时给出的 base directory**（形如 `…/plugins/cache/optimus-plugins-official/optimus-frontend-plugin/<hash>/skills/svg-to-xaml-path`）。**始终使用该绝对路径**——本 skill 通常从插件缓存加载，而当前工作目录是用户的项目目录，与 skill 目录无关；仓库相对路径只在 cwd 恰好是本仓库时才碰巧可用。

```powershell
$SkillDir = "<本 skill 的 base directory>"

# 本地 SVG 文件
python "$SkillDir\scripts\merge_svg_paths.py" --file "C:\icons\icon.svg" --format xaml

# 粘贴的完整 SVG 标记
python "$SkillDir\scripts\merge_svg_paths.py" --svg '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 0 Z" /></svg>' --format data

# 管道中的完整 SVG 标记
Get-Content -Raw "C:\icons\icon.svg" | python "$SkillDir\scripts\merge_svg_paths.py" --stdin --format data
```

## 输出格式与合并规则

**stdout 是产物，stderr 是告警——两者必须分开。** 告警行绝不能混进 `.xaml` 文件或交付的 `Data` 字符串。若所用工具会交错两个流，请重定向后再取值：

```powershell
python "$SkillDir\scripts\merge_svg_paths.py" --file "C:\icons\icon.svg" --format xaml 2>$null   # 仅取产物
```

| 格式 | 结果 | 丢失什么 |
|---|---|---|
| `data` | 单个几何字符串，带 fill rule 前缀。**含 transform 时报错**——纯几何无法承载变换。 | **`Fill`/`Stroke` 全部丢弃**，需自行补回；多路径异色时会被静默熔为一条（见下） |
| `xaml` | 可直接使用的 WPF `Path` 元素，必要时附 `MatrixTransform`。 | 仅丢弃对照表中标注「不转换」的属性 |

`--format` 缺省值为 `xaml`。

**合并键（仅适用于 `xaml`）：** `Fill` + `Stroke` + `fill-rule` + `transform` 四项全部相同才输出一个 `Path`；任一项不同则输出多个 `Path`，**不得伪造为单一 `Path`**。基本图元转换后与 `<path>` 同等参与合并。

**🔴 `data` 格式不适用合并键——异色路径会被静默熔合。** `data` 只输出几何，颜色无处安放：两条 `#B8C6E0` 和 `#FF0000` 的路径会被拼成一条字符串，exit 0 且**零告警**。因此：

- 用户要求「合并成一个 Path」但各路径颜色不同时，**不得改用 `--format data` 迂回**——那会静默丢掉一种颜色。正确应对是说明无法合并，输出多个 `Path`。
- 仅在已确认所有路径同色（或用户只要几何、颜色另行设置）时才使用 `data`。

`fill-rule` 是 `data` 唯一会告警的差异项：混用时报 `warning: multiple fill rules found; data output uses the first path's rule.`，并按**首条路径**的规则决定前缀。

**fill rule 前缀必须保留：** 输出的 `Data` 以 `F1`（nonzero，SVG 的默认值）或 `F0`（evenodd）开头。WPF 路径迷你语言在无前缀时按 EvenOdd 解析，与 SVG 默认值不一致，**删除该前缀会改变自相交路径和孔洞的渲染结果**。

**多段几何不是布尔并集：** 串接后的 `Data` 是一个含多个 figure 的 WPF Geometry，各 figure 按 fill rule 共同决定填充，而非求并。

## 交付给 WPF 时的两个约束

脚本的输出不是「贴进去就完事」，以下两点必须随产物一并告知用户：

- **`MatrixTransform` 挂在 `RenderTransform` 上，不参与布局测量。** WPF 的 `RenderTransform` 在 measure/arrange 之后生效，父容器仍按变换前的尺寸给位置。图标放在 `StackPanel`/`Grid` 等布局敏感容器里时，偏移可能不是用户预期的效果。若需要参与布局，用户须自行改用 `LayoutTransform`（仅适用于无平移的情形）或在源 SVG 中展平变换。
- **多个 `Path` 是无根元素的裸序列。** 脚本不生成包裹容器，调用方须自行放进 `Canvas`（保持绝对坐标）或 `Grid`（各 Path 重叠）。不要臆造 `Viewbox` 或尺寸——见「支持边界」。

## 示例

### 同色多路径合并为一个 Path

`assets/sample-icon.svg` 有两个同色路径并含 `class="icon"`：

```powershell
python "$SkillDir\scripts\merge_svg_paths.py" --file "$SkillDir\assets\sample-icon.svg" --format xaml
```

```
warning: class attributes were encountered; CSS classes were not converted.
```
```xml
<Path Fill="#B8C6E0" Data="F1 M3 3h18v18H3V3zm2 2v14h14V5H5z M7 11h10v2H7v-2z" />
```

### 带 transform 的圆角矩形

```xml
<!-- 输入：<g transform="translate(4 4) rotate(45)"><rect width="8" height="8" rx="1" fill="#B8C6E0"/></g> -->
<Path Fill="#B8C6E0" Data="F1 M1,0 H7 A1,1 0 0 1 8,1 V7 A1,1 0 0 1 7,8 H1 A1,1 0 0 1 0,7 V1 A1,1 0 0 1 1,0 Z">
  <Path.RenderTransform>
    <MatrixTransform Matrix="0.707107,0.707107,-0.707107,0.707107,4,4" />
  </Path.RenderTransform>
</Path>
```

坐标**未被烘焙**——原始几何保持不变，变换以 WPF 等价形式承载。

## 已转换 / 未转换

| 输入 | 处理方式 |
|---|---|
| 非空 `d` 的 `<path>` | 转换 |
| `rect`（含 `rx`/`ry` 圆角）、`circle`、`ellipse`、`line`、`polyline`、`polygon` | 按 SVG 2 规范的等价路径**精确**转换，无近似 |
| `fill` / `stroke`（含继承、`none`） | 转换为 `Fill` / `Stroke` |
| `rgb()` / `rgba()` | 换算为 WPF hex（`rgba` → `#AARRGGBB`） |
| `fill-rule`（含继承） | 转换为 `Data` 的 `F0`/`F1` 前缀 |
| `transform`：`translate`/`scale`/`rotate`/`skewX`/`skewY`/`matrix`（含继承与函数列表） | 合成为单一仿射矩阵，输出 `MatrixTransform` |
| `style` 中的 `fill`/`stroke`/`fill-rule`/`display`/`visibility`/`transform` | 转换，且优先级高于同名 presentation attribute |
| `style` 中的其余声明 | 忽略，并按名称告警 |
| `class` | 不解析（需 CSS 引擎），出现即告警 |
| `<defs>`/`<clipPath>`/`<mask>`/`<symbol>`/`<marker>`/`<pattern>` 子树 | 整棵跳过（SVG 本身也不直接渲染） |
| `display:none` 子树、有效 `visibility:hidden` 的路径 | 跳过 |
| `text`/`tspan`/`textPath`/`image`/`use`/`foreignObject` | 跳过，并**按名称告警** |
| `viewBox`、stroke width、opacity、渐变、clip/mask/filter | **不转换，无告警** |

## 错误与告警

脚本失败时 exit 2 且**不产生任何 stdout**，必须如实转达，不得声称转换成功：

| 情形 | 原因 |
|---|---|
| `currentColor` / `url(#grad)` / `hsl()` 作为 `fill`/`stroke` | WPF 无法解析。改用具体 hex/颜色关键字，或在 WPF 侧绑定画刷（`{TemplateBinding Foreground}`、`DynamicResource` 等）——`currentColor` 的语义正是「跟随前景色」 |
| `--format data` 遇到 transform | 路径数据无法承载变换；改用 `--format xaml`，或先在源 SVG 展平 |
| 长度写作百分比（如 `width="50%"`） | 百分比需要 viewport，本脚本不读取 viewBox；改用用户单位 |
| transform 语法错误或参数个数不对 | 不做猜测性修复；须修正源 SVG |
| SVG 声明了内部 DTD 子集（`<!DOCTYPE ... [ ... ]>`） | 其中的实体不会展开；移除 `[...]` 块后重试。仅有外部 DTD 引用（iconfont/Illustrator 的标准前言）不受影响 |
| 无任何可转换几何 | 需先在源 SVG 中把图形转为 path |

## 支持边界

- 不读取、转换或输出 SVG `viewBox` 的布局；路径坐标始终按原样返回，且永不生成 WPF `Viewbox`。调用方自行选择 WPF 的布局缩放和定位。
- 不解析 CSS（`class`、`<style>` 元素）。只有内联 `style` 属性会被解析。
- stroke width、opacity、渐变、clip/mask/filter 及其他作为 presentation attribute 书写的展示属性不会被转换，也不会因其存在而告警（仅当写在 `style` 中时才具名告警）。用户必须检查源 SVG 并自行预处理。
- **即使 `Fill`、`Stroke` 与 transform 都匹配，也不保证视觉保真**——上述未转换的属性会造成差异。

## 输出纪律

1. 返回完整、未截断的 `data` 或 XAML，保留 SVG 文档顺序、fill rule 前缀与 `MatrixTransform`。
2. 只交付 stdout 的内容；stderr 的告警单独转述，不得混入产物。
3. 不发明、补全或近似任何几何数据；不手工把变换烘焙进坐标。
4. 各路径颜色不同时不得改用 `--format data` 迂回满足「合并成一个」的要求——那会静默丢色。
5. 将脚本的警告和错误如实、明确地报告；错误时不要声称已转换成功。
6. 交付时必须提示「未转换的展示属性不保证视觉保真」，不得因 `Fill` 匹配就宣称与原图一致。

## 本地测试

```bash
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts -p "test_*.py"
```
