---
name: mastergo-icon-expoter
description: 当用户要求从 MasterGo 设计稿导出图标、背景等视觉资产用于 WPF XAML 项目时使用此 Skill；产出 Geometry/DrawingImage 资源字典、位图与决策清单，不生成页面代码。
metadata:
  version: "1.1.1"
  author: desktop client team
  category: generator
compatibility: Python 3 标准库；可选 Pillow（为未来 .ico 合成功能预留，本版本尚未接入任何调用路径）；需 mastergo-magic-mcp（本仓库 plugins/optimus-mcp-servers/.mcp.json 内置）与 MASTERGO_TOKEN；委派 optimus-frontend-plugin:svg-to-xaml-path 完成 SVG→Path.Data 转换。
allowed-tools: Read Write Bash PowerShell Task mastergo-magic-mcp
---

# MasterGo 设计稿转 WPF 图标资产

从 MasterGo 设计稿导出图标、背景等视觉资产，产出 WPF 可直接引用的 `Icons.xaml`（`Geometry`/`DrawingImage` 资源）、`Images/*.png` 位图与 `icons-manifest.json` 决策清单。**不生成页面代码**——用户在自己的 XAML 里引用 `{StaticResource IconSearchGeometry}`。

格式决策、命名约定、静默陷阱清单见 [`references/wpf-xaml-icon-sepc.md`](references/wpf-xaml-icon-sepc.md)；本文件只讲编排步骤。

## Step 0：前置检查

以下任一条件不满足，停止且不要读取设计：
- `MASTERGO_TOKEN` 已配置；
- 文件属于 MasterGo Team 版或以上且不是草稿箱；
- 分享链接可解析出 `fileId`/`layerId`。

## Step 1：拉取目录，扫描图标节点

调用不带 `sectionIndex` 的 `mcp__getDesignSections`。遍历返回的节点树，收集所有 `PATH`（矢量图标候选）与 `IMAGE`（位图候选）节点。区块数超过 8 个时停止，请用户指定范围。

未识别类型的节点（如 `INSTANCE` 图标组件）列入下一步 CHECKPOINT 的"未识别节点"清单，不猜测其类型，不产出。

## Step 2：🔴 CHECKPOINT

一次性展示，等待用户确认或修正后才能进入 Step 3：

```
1. 待处理范围：N 个图标节点（矢量 M 个 / 位图 K 个 / 未识别 J 个）
2. 待人工命名：<列出无法自动推导文件名的节点，格式见下方"命名规则">
3. 输出目录：<--out 路径>（若已存在 Icons.xaml，请选择：merge / overwrite / separate）
```

**命名规则**（详见 `references/wpf-xaml-icon-sepc.md` 第八节）：脚本会尝试从 DSL 图层名机械推导 `snake_case` 文件名（如 `SearchIcon` → `icon_search`），失败时（非 ASCII、无法判定 `icon_`/`bg_`/`logo_` 分类等）必须由用户补充完整文件名，不得猜测语义分类。

## Step 3：按完整图标转换、组装 `input.json`

先按共同 FRAME/GROUP 父级归并路径、LAYER、IMAGE；**一个完整图标只能写入一个 input 条目**，禁止将局部 PATH 当作完整图标交付。调用 `mcp__extractSvg` 获取目标 layer 的 SVG 集合后，按 DSL `nodeId`/`svgShortKey` 对应源图元。

### 3.1 矢量优先路径

1. 纯色、无渐变且没有需要保留的父级偏移时，委派 `svg-to-xaml-path --format data`，将返回的 `F0`/`F1` Data 原样写入 `paths`。
2. 多色、线性渐变、SVG transform，或必须按 DSL `relativeX`/`relativeY` 拼装的图元，委派：

   ```powershell
   python "$SvgSkillDir\scripts\merge_svg_paths.py" --file <svg> `
     --format drawing --parent-transform "translate(<relativeX> <relativeY>)"
   ```

   将 stdout 的完整 `<DrawingGroup>...</DrawingGroup>` 原样写入该矢量条目的 `drawingXaml`，同时令 `paths: []`。`icon_exporter.py` 会生成含 `LinearGradientBrush` 和嵌套父级坐标 `DrawingGroup` 的 `DrawingImage`。

🔴 **红线：** `F0`/`F1` 前缀、`DrawingGroup` 的 Geometry 属性和转换器 stdout 都不得删改、补全或重排。

### 3.2 可恢复失败：PNG 降级

转换失败不再直接丢弃完整图标。每个图标按下表处理：

| 失败类型 | 降级动作 | 清单结果 |
|---|---|---|
| `svg-to-xaml-path` 不支持的 SVG（径向渐变、pattern、滤镜、不可转换元素） | 调用 `mcp__getD2c` 导出同一**完整图标父节点**的 PNG 到 `.mastergo-icons/raw/` | `png`、`exported`、`fallbackFrom: vector` |
| 线性渐变/父级坐标的 DrawingGroup 转换或写盘失败 | 对同一完整父节点执行 D2C PNG 导出 | `png`、`exported`、`fallbackFrom: vector` |
| 原始 `IMAGE` 节点 | 用 D2C PNG 直接落盘 | `png`、`exported` |
| D2C 无权限、未返回 PNG、PNG 路径不存在 | 不伪造图像；保留转换/D2C 错误原文 | `needs-manual` |
| 命名冲突、输出目录冲突、契约错误 | 硬失败；不写任何输出 | 无产物 |

有成功 PNG 时在 `input.json` 写入：

```json
{
  "sourceKind": "fallback-png",
  "nodeId": "10:2",
  "dslName": "GradientIcon",
  "userName": "icon_gradient",
  "width": 92, "height": 92,
  "paths": [],
  "fallbackPngPath": ".mastergo-icons/raw/icon_gradient.png",
  "fallbackReason": "svg-to-xaml-path failed: <完整 stderr>"
}
```

`fallback-png` 会复制为 `Images/icon_gradient.png`，并在 `icons-manifest.json` 写入 `fallbackFrom: "vector"` 和 `fallbackReason`。位图源使用 `sourceKind: "bitmap"` 与 `bitmapPath`。

## Step 4：运行转换器

`$SkillDir` 必须是本 Skill 加载时提供的绝对 base directory。

```powershell
$SkillDir = "<本 skill 的 base directory>"
python "$SkillDir\scripts\icon_exporter.py" --input .mastergo-icons\input.json --out <用户确认的输出目录> --source-root .
```

成功时 exit `0`，stdout 为空；契约违规或自检失败时 exit `2`，stdout 为空，stderr 为 `error: ...`（自检失败会在同一条消息里列出全部违规项）。硬失败时不会创建或修改输出目录中的任何文件。

## Step 5：交付纪律

- 逐条转达 `icons-manifest.json` 中 `status: needs-manual` 的记录及其 `reason`，不得声称已导出。
- **矢量图标在使用处必须显式 `Stretch="Uniform"`。** 本 Skill 只产出资源字典，不产出消费该资源的 `<Path>`/`<Image>` 元素，因此这条规则无法由脚本自动校验——必须在每次交付时向用户逐字提醒：不写 `Stretch` 时 WPF 默认 `None`，图标只会显示左上角一小块，且不报任何错。
- 本版本未实现 `.ico` 合成；若用户需要 `.ico`，需自行用外部工具对导出的 PNG 进行合成。
- 不检查用户项目中已有的 XAML 是否正确使用了这些资源；不做视觉还原度校验。均为本 Skill 明确排除的范围。

## 本地测试

```powershell
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts -p "test_*.py"
```
