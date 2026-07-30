---
name: svg-to-xaml-path
version: 1.0.0
description: 当用户提供本地 SVG 文件路径或完整 SVG 标记，并要求提取 path 的 d、合并多路径、生成 WPF XAML 或 Path.Data 时使用此 Skill；适用于 SVG 图标转 WPF Path 的场景。
metadata:
  version: "1.0.0"
  author: desktop client team
compatibility: Python 3；可在 Windows PowerShell 中运行随附的无第三方依赖 CLI。
allowed-tools: Read Bash
---

# SVG 转 WPF Path

将仅包含可用 `<path d>` 的 SVG 路径数据转换为 WPF `Path.Data` 或 XAML `Path`。普通的仅路径 SVG 不需要 Inkscape。

## 识别输入

- 用户给出本地 `.svg` 文件路径时，使用 `--file`。
- 用户粘贴完整的 `<svg>...</svg>` 标记时，使用 `--svg`；不要把片段补成臆测的图形。
- 已从管道或标准输入获得完整 SVG 标记时，使用 `--stdin`。

在仓库根目录运行以下命令：

```powershell
# 本地 SVG 文件
python "plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py" --file "C:\icons\icon.svg" --format xaml

# 粘贴的完整 SVG 标记
python "plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py" --svg '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 0 Z" /></svg>' --format data

# 管道中的完整 SVG 标记
Get-Content -Raw "C:\icons\icon.svg" | python "plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py" --stdin --format data
```

## 输出格式与合并规则

仅使用以下格式：

| 格式 | 结果 |
|---|---|
| `data` | 按 SVG 文档顺序连接的完整 `d` 数据。 |
| `xaml` | 可直接使用的 WPF `Path` 元素。 |

**核心规则：** 多个 `d` 值按 SVG 文档顺序串接，会形成一个包含多个 figure 的 WPF Geometry，**不是**布尔并集。有效 `Fill` 和 `Stroke` 相同时，CLI 输出一个合并的 WPF `Path`；有效 `Fill` 或 `Stroke` 不同时，`data` 仍可提供完整路径数据，而 `xaml` 必须输出多个 `Path`，不能伪造为一个颜色的单一 `Path`。

生成的 XAML **只**传递 `Fill` 和 `Stroke`。CLI 只会自动检测并警告 SVG 中出现的 `style` 或 `class` 属性；它们不会被转换。该警告不改变按有效 `Fill`/`Stroke` 合并的规则。除此以外，stroke width、opacity、gradients、fill rule、clip/mask/filter 及其他任意 SVG 展示属性都既不会被转换，也不会被 CLI 自动验证或警告。用户必须自行检查并在转换前预处理这些属性；即使生成的 `Fill` 和 `Stroke` 匹配，也**不能保证视觉保真**。

## 示例：两个同色路径

`C:\Users\Administrator\Downloads\AI问答.svg` 有两个相同填充色的路径，并含有 `class="icon"`。以 `--file` 和 `--format xaml` 转换时，CLI 应在标准错误输出实际警告 `warning: style or class attributes were encountered; they were not converted.`，但因忽略该 class 后两个路径的有效 `Fill` 和 `Stroke` 仍相同，仍应得到**一个** XAML `Path`，其 `Fill="#B8C6E0"`，并在 `Data` 中按原始顺序包含两个路径的完整数据。该结果不保证原 SVG 的视觉保真：CLI 只输出 `Fill` 和 `Stroke`，且不会自动验证其他展示属性：

```powershell
python "plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py" --file "C:\Users\Administrator\Downloads\AI问答.svg" --format xaml
```

## 支持边界与回退

- 仅处理具有非空 `d` 的 `<path>`；不会转换 `rect`、`circle`、`text` 或 `use`。
- 不读取、转换或输出 SVG `viewBox` 的布局；路径坐标始终按原样返回，且永不生成 WPF `Viewbox`。调用方自行选择 WPF 的布局缩放和定位；若需要精确的 SVG 视口变换，必须先在源 SVG 中预展平或规范化，再进行转换。
- CLI 自动检测的展示属性只有 `style` 和 `class`：遇到任一属性时，原样报告 `warning: style or class attributes were encountered; they were not converted.`；不会转换这些属性中的绘制规则。该警告不表示脚本检查了任何其他展示属性。
- stroke width、opacity、gradients、fill rule、clip/mask/filter 和其他任意 SVG 展示属性不会被转换，也不会被 CLI 自动验证或因其存在而自动警告。用户必须检查源 SVG 并自行预处理；即使 `Fill` 和 `Stroke` 匹配，也不得承诺视觉保真。
- 不会展平变换。任一待转换路径或其祖先有 `transform` 时，脚本会硬停止并报告错误；**不得**手工估算或把组变换烘焙进坐标。应先在源 SVG 中应用或展平变换，再重新转换。
- 当路径有效绘制样式不同，单一 XAML `Path` 无法保持原视觉；保留 `data` 结果，并接受 `xaml` 的多个 `Path` 输出。

## 输出纪律

1. 返回完整、未截断的 `data` 或 XAML，保留 SVG 文档顺序。
2. 不发明、补全或近似任何几何数据。
3. 将脚本的警告和错误如实、明确地报告；错误时不要声称已转换成功。
4. 若输入不含可用的 `<path d>`，明确报告脚本错误并请求用户先将源图形转换为路径后再试。
