---
name: svg-to-xaml-path
description: 当用户提供本地 SVG 文件路径或完整 SVG 标记，并要求提取 path 的 d、合并多路径、生成 WPF XAML 或 Path.Data 时使用此 Skill；适用于 SVG 图标转 WPF Path 的场景。
metadata:
  version: "1.1.0"
  author: desktop client team
compatibility: Python 3；可在 Windows PowerShell 中运行随附的无第三方依赖 CLI。
allowed-tools: Read Bash PowerShell
---

# SVG 转 WPF Path

将仅包含可用 `<path d>` 的 SVG 路径数据转换为 WPF `Path.Data` 或 XAML `Path`。普通的仅路径 SVG 不需要 Inkscape。

## 识别输入

- 用户给出本地 `.svg` 文件路径时，使用 `--file`。
- 用户粘贴完整的 `<svg>...</svg>` 标记时，使用 `--svg`；不要把片段补成臆测的图形。
- 已从管道或标准输入获得完整 SVG 标记时，使用 `--stdin`。

## 运行脚本

下列命令中的 `$SkillDir` 必须替换为**本 skill 加载时给出的 base directory**（形如 `…/plugins/cache/optimus-plugins-official/optimus-frontend-plugin/<hash>/skills/svg-to-xaml-path`）。**不要使用仓库相对路径**——本 skill 通常从插件缓存加载，当前工作目录不一定是本仓库，相对路径会直接 `FileNotFoundError`。

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

仅使用以下格式：

| 格式 | 结果 |
|---|---|
| `data` | 按 SVG 文档顺序连接的完整 `d` 数据，带 fill rule 前缀。 |
| `xaml` | 可直接使用的 WPF `Path` 元素。 |

**核心规则：** 多个 `d` 值按 SVG 文档顺序串接，会形成一个包含多个 figure 的 WPF Geometry，**不是**布尔并集。有效 `Fill`、`Stroke`、`fill-rule` 三者全部相同时，CLI 输出一个合并的 WPF `Path`；任一项不同时，`data` 仍可提供完整路径数据，而 `xaml` 必须输出多个 `Path`，不能伪造为单一 `Path`。

**fill rule 前缀必须保留：** 输出的 `Data` 以 `F1`（nonzero，SVG 的默认值）或 `F0`（evenodd）开头。WPF 路径迷你语言在无前缀时按 EvenOdd 解析，与 SVG 默认值不一致，**删除该前缀会改变自相交路径和孔洞的渲染结果**。

生成的 XAML **只**传递 `Fill` 和 `Stroke`。除 `Fill`/`Stroke`/`fill-rule` 外的展示属性都不会被转换；即使生成的 `Fill` 和 `Stroke` 匹配，也**不能保证视觉保真**。

## 示例：两个同色路径

`assets/sample-icon.svg` 有两个相同填充色的路径，并含有 `class="icon"`。以 `--file` 和 `--format xaml` 转换时，CLI 应在标准错误输出实际警告 `warning: class attributes were encountered; CSS classes were not converted.`，但因忽略该 class 后两个路径的有效 `Fill`、`Stroke`、`fill-rule` 仍相同，得到**一个** XAML `Path`：

```powershell
python "$SkillDir\scripts\merge_svg_paths.py" --file "$SkillDir\assets\sample-icon.svg" --format xaml
```

```xml
<Path Fill="#B8C6E0" Data="F1 M3 3h18v18H3V3zm2 2v14h14V5H5z M7 11h10v2H7v-2z" />
```

## 已转换 / 未转换

| 输入 | 处理方式 |
|---|---|
| 非空 `d` 的 `<path>` | 转换 |
| `fill` / `stroke`（含继承、`none`） | 转换为 `Fill` / `Stroke` |
| `fill-rule`（含继承） | 转换为 `Data` 的 `F0`/`F1` 前缀 |
| `style` 中的 `fill`/`stroke`/`fill-rule`/`display`/`visibility`/`transform` | 转换，且优先级高于同名 presentation attribute |
| `style` 中的其余声明 | 忽略，并按名称告警 |
| `class` | 不解析（需 CSS 引擎），出现即告警 |
| `<defs>`/`<clipPath>`/`<mask>`/`<symbol>`/`<marker>`/`<pattern>` 子树 | 整棵跳过（这些内容 SVG 本身也不直接渲染） |
| `display:none` 子树、有效 `visibility:hidden` 的路径 | 跳过 |
| `transform`（路径自身或任一祖先） | **硬停止报错** |
| `rect`/`circle`/`ellipse`/`line`/`polyline`/`polygon`/`text`/`image`/`use` | **静默忽略，无告警** |
| `viewBox`、stroke width、opacity、渐变、clip/mask/filter | **不转换，无告警** |

## 支持边界与回退

- 范围外图元（`rect`、`circle`、`text`、`use` 等）被**静默丢弃且不告警**。转换前必须自行确认源 SVG 中的图形已全部转为 `<path>`，否则会得到残缺图形却看不到任何提示。
- 不读取、转换或输出 SVG `viewBox` 的布局；路径坐标始终按原样返回，且永不生成 WPF `Viewbox`。调用方自行选择 WPF 的布局缩放和定位；若需要精确的 SVG 视口变换，必须先在源 SVG 中预展平或规范化，再进行转换。
- **paint 值原样透传，不校验 WPF 可解析性。** `currentColor`、`url(#gradient)`、`rgb()`/`rgba()`/`hsl()` 都会被写进 `Fill`/`Stroke`，脚本返回成功，但 WPF 加载时会失败。遇到这些值必须先在源 SVG 中换成 hex 或颜色关键字。
- stroke width、opacity、渐变、clip/mask/filter 及其他作为 presentation attribute 书写的展示属性不会被转换，也不会因其存在而告警（仅当它们写在 `style` 中时才会被具名告警）。用户必须检查源 SVG 并自行预处理；即使 `Fill` 和 `Stroke` 匹配，也不得承诺视觉保真。
- 不会展平变换。任一待转换路径或其祖先有 `transform` 时，脚本会硬停止并报告错误；**不得**手工估算或把组变换烘焙进坐标。应先在源 SVG 中应用或展平变换，再重新转换。
- 当路径有效绘制样式不同，单一 XAML `Path` 无法保持原视觉；保留 `data` 结果，并接受 `xaml` 的多个 `Path` 输出。

## 输出纪律

1. 返回完整、未截断的 `data` 或 XAML，保留 SVG 文档顺序与 fill rule 前缀。
2. 不发明、补全或近似任何几何数据。
3. 将脚本的警告和错误如实、明确地报告；错误时不要声称已转换成功。
4. 若输入不含可用的 `<path d>`，明确报告脚本错误并请求用户先将源图形转换为路径后再试。
5. 交付时必须提示「未转换的展示属性不保证视觉保真」，不得因 `Fill` 匹配就宣称与原图一致。

## 本地测试

```bash
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts -p "test_*.py"
```
