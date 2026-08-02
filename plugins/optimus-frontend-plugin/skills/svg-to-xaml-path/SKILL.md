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

## 运行脚本

命令中的 `$SkillDir` 必须替换为**本 skill 加载时给出的 base directory**。**始终用该绝对路径**——本 skill 通常从插件缓存加载，cwd 是用户的项目目录，与 skill 目录无关。

```powershell
$SkillDir = "<本 skill 的 base directory>"

# 本地 .svg 文件路径
python "$SkillDir\scripts\merge_svg_paths.py" --file "C:\icons\icon.svg" --format xaml

# 用户粘贴的完整标记；不要把片段补成臆测的图形
python "$SkillDir\scripts\merge_svg_paths.py" --svg '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 0 Z" /></svg>' --format data

# 已在管道中
Get-Content -Raw "C:\icons\icon.svg" | python "$SkillDir\scripts\merge_svg_paths.py" --stdin --format data
```

## 输出格式与合并规则

**stdout 是产物，stderr 是告警。** 告警行绝不能混进 `.xaml` 或交付的 `Data`。若工具会交错两流，用 `2>$null` 只取产物。

| 格式 | 结果 | 丢失什么 |
|---|---|---|
| `data` | 单个几何字符串，带 fill rule 前缀。含 transform 时报错。 | **`Fill`/`Stroke` 全部丢弃**；多路径异色时静默熔为一条 |
| `xaml` | WPF `Path` 元素，必要时附 `MatrixTransform`。缺省值。 | 仅丢弃对照表中标注「不转换」的属性 |

**合并键（仅 `xaml` 适用）：** `Fill` + `Stroke` + `fill-rule` + `transform` 四项全同才输出一个 `Path`；任一不同则输出多个，**不得伪造为单一 `Path`**。基本图元转换后与 `<path>` 同等参与合并。

**🔴 静默陷阱一：`data` 不适用合并键。** `data` 只输出几何，颜色无处安放——`#B8C6E0` 与 `#FF0000` 两条路径会被拼成一条串，exit 0 且**零告警**。用户要求「合并成一个」但颜色不同时，**不得改用 `data` 迂回**；正确应对是说明无法合并并输出多个 `Path`。仅在确认全部同色（或用户只要几何）时才用 `data`。

`fill-rule` 是 `data` 唯一会告警的差异项：混用时报 `multiple fill rules found`，并按**首条路径**的规则定前缀。

**🔴 静默陷阱二：颜色由 CSS 提供时输出纯黑且零告警。** 脚本只认前两种着色方式：

| 着色方式 | 脚本行为 |
|---|---|
| `fill="#B8C6E0"` | 正常转换 |
| `style="fill:#B8C6E0"` | 正常转换 |
| `<style>.icon{…}</style>` + `class="icon"` | 默认黑，**但有 class 告警** |
| `<style>path{…}</style>`（标签选择器）、外部样式表 | 默认黑，**exit 0 且零告警** |

SVG 的 `fill` 默认值就是黑，脚本自认正常。**转换前必须打开源 SVG 确认着色方式**：若 `<path>` 上既无 `fill` 也无 `style="fill:…"`，而文件含 `<style>` 元素或依赖外部 CSS，则产出的黑色是错的，须让用户提供实际颜色。iconfont、Illustrator、Figma 的部分导出配置都会产生这种 SVG。

**fill rule 前缀必须保留：** `Data` 以 `F1`（nonzero，SVG 默认）或 `F0`（evenodd）开头。WPF 迷你语言无前缀时按 EvenOdd 解析，与 SVG 默认值不一致，**删除前缀会改变自相交路径和孔洞的渲染结果**。串接后的 `Data` 是含多个 figure 的单一 Geometry，各 figure 按 fill rule 共同决定填充，**不是布尔并集**。

## 交付给 WPF 时的三个约束

脚本的输出不是「贴进去就完事」，以下三点必须随产物一并告知用户：

- **产物没有固有尺寸。** `viewBox`、`width`、`height` 全部不转换，坐标按原样返回（一个 `viewBox="0 0 1024 1024"` 的图标就是 1024 单位跨度）。用户须自行设定 `Width`/`Height`，或包一层 `Viewbox` + `Canvas`。**不要**代替用户臆造尺寸。
- **`MatrixTransform` 挂在 `RenderTransform` 上，不参与布局测量。** WPF 的 `RenderTransform` 在 measure/arrange 之后生效，父容器仍按变换前的尺寸给位置。图标放在 `StackPanel`/`Grid` 等布局敏感容器里时，偏移可能不是用户预期的效果。改用 `LayoutTransform` 只对缩放/旋转有效——**纯平移在 `LayoutTransform` 下不影响 `DesiredSize`，这条退路是空的**，此时只能在源 SVG 中展平变换，或改用 `Canvas.Left`/`Canvas.Top`。
- **多个 `Path` 是无根元素的裸序列。** 脚本不生成包裹容器，调用方须自行放进 `Canvas`（保持绝对坐标）或 `Grid`（各 Path 重叠）。

## 示例

`assets/sample-icon.svg` 有两个同色路径并含 `class="icon"`：

```powershell
python "$SkillDir\scripts\merge_svg_paths.py" --file "$SkillDir\assets\sample-icon.svg" --format xaml
```

stderr：

```
warning: class attributes were encountered; CSS classes were not converted.
```

stdout（这一行才是产物）：

```xml
<Path Fill="#B8C6E0" Data="F1 M3 3h18v18H3V3zm2 2v14h14V5H5z M7 11h10v2H7v-2z" />
```

含 transform 时的形态（`<g transform="translate(4 4) rotate(45)">` + `<rect rx="1">`），注意坐标**未被烘焙**：

```xml
<Path Fill="#B8C6E0" Data="F1 M1,0 H7 A1,1 0 0 1 8,1 V7 A1,1 0 0 1 7,8 H1 A1,1 0 0 1 0,7 V1 A1,1 0 0 1 1,0 Z">
  <Path.RenderTransform>
    <MatrixTransform Matrix="0.707107,0.707107,-0.707107,0.707107,4,4" />
  </Path.RenderTransform>
</Path>
```

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
| `class`（告警）、`<style>` 元素 / 外部样式表（无告警） | 均不解析——靠它们上色即落入静默陷阱二 |
| `<defs>`/`<clipPath>`/`<mask>`/`<symbol>`/`<marker>`/`<pattern>` 子树、`display:none` 子树、`visibility:hidden` 的路径 | 跳过（前者 SVG 本身也不直接渲染） |
| `text`/`tspan`/`textPath`/`image`/`use`/`foreignObject` | 跳过，并**按名称告警** |
| `viewBox`、stroke width、opacity、clip/mask/filter | **不转换，无告警** |

**全部告警与错误的原文见 [`references/messages.md`](references/messages.md)。** 转述给用户时必须完整照抄，**不得截断结尾的处置建议**——那部分正是用户需要的行动指引。该文件同时列出了「既不告警也不报错」的静默行为清单。

## 错误与告警

脚本失败时 exit 2 且**不产生任何 stdout**，必须如实转达，不得声称转换成功：

| 情形 | 原因与处置 |
|---|---|
| `currentColor` | WPF 无此概念。在 WPF 侧绑定画刷（`{TemplateBinding Foreground}`、`DynamicResource`）——其语义正是「跟随前景色」 |
| `url(#grad)` | **被引用的渐变在此硬失败，不是静默丢弃**（未被引用的 `<defs>` 渐变才随 `<defs>` 静默跳过）。展平为纯色，或照 SVG 的 stop 手工建 `LinearGradientBrush` |
| `hsl()` / 其他非 hex 非关键字 | 改用 hex。注意关键字**不做校验**，SVG 独有的关键字会透传并在 XAML 解析时才失败 |
| `--format data` 遇到 transform | 路径数据无法承载变换；改用 `--format xaml`，或先在源 SVG 展平 |
| 长度写作百分比（如 `width="50%"`） | 百分比需要 viewport，本脚本不读取 viewBox；改用用户单位 |
| transform 语法错误或参数个数不对 | 不做猜测性修复；须修正源 SVG |
| 内部 DTD 子集（`<!DOCTYPE ... [ ... ]>`） | 实体不会展开；移除 `[...]` 块后重试。仅有外部 DTD 引用（iconfont/Illustrator 的标准前言）不受影响 |
| XML 格式错误 / `--file` 路径不可读 | 原样转达解析器或系统的报错原文，让用户修源文件或路径 |
| 无任何可转换几何 | 需先在源 SVG 中把图形转为 path |

## 输出纪律

1. 返回完整、未截断的 `data` 或 XAML，保留 SVG 文档顺序、fill rule 前缀与 `MatrixTransform`。
2. 只交付 stdout 的内容；stderr 的告警单独转述，不得混入产物。
3. 不发明、补全或近似任何几何数据；不手工把变换烘焙进坐标。
4. 各路径颜色不同时不得改用 `--format data` 迂回满足「合并成一个」的要求——那会静默丢色。
5. 输出 `Fill="#000000"` 时必须回查源 SVG：若着色实际来自 `<style>` 元素或外部 CSS，这个黑色是错的，须向用户确认真实颜色而非照发。
6. 将脚本的警告和错误如实、明确地报告；错误时不要声称已转换成功。
7. 交付时必须提示「对照表中标注不转换的属性会造成差异，不保证视觉保真」，不得因 `Fill` 匹配就宣称与原图一致。

## 本地测试

```bash
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts -p "test_*.py"
```
