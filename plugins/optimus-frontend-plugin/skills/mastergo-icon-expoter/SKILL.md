---
name: mastergo-icon-expoter
description: 当用户要求从 MasterGo 设计稿导出图标、背景等视觉资产用于 WPF XAML 项目时使用此 Skill；产出 Geometry/DrawingImage 资源字典、位图与决策清单，不生成页面代码。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: generator
compatibility: Python 3 标准库；可选 Pillow（为未来 .ico 合成功能预留，本版本尚未接入任何调用路径）；需 mastergo-magic-mcp（本仓库 plugins/optimus-mcp-servers/.mcp.json 内置）与 MASTERGO_TOKEN；委派 optimus-frontend-plugin:svg-to-xaml-path 完成 SVG→Path.Data 转换。
allowed-tools: Read Write Bash PowerShell Task mastergo-magic-mcp
---

# MasterGo 设计稿转 WPF 图标资产

从 MasterGo 设计稿导出图标、背景等视觉资产，产出 WPF 可直接引用的 `Icons.xaml`（`Geometry`/`DrawingImage` 资源）、`Images/*.png` 位图与 `icons-manifest.json` 决策清单。**不生成页面代码**——用户在自己的 XAML 里引用 `{StaticResource IconSearchGeometry}`。

格式决策、命名约定、静默陷阱清单见 [`references/wpf-xaml-icon-sepc.md`](references/wpf-xaml-icon-sepc.md)；本文件只讲编排步骤。

## Step 0：前置检查

以下任一条件不满足，停止且不要读取设计：`MASTERGO_TOKEN` 已配置；文件属于 MasterGo Team 版或以上且不是草稿箱；分享链接可解析出 `fileId`/`layerId`。

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

## Step 3：逐图标委派转换，组装 `input.json`

对每个矢量候选节点：

1. 调用 `mcp__extractSvg(svgShortKey=...)` 取得 SVG 标记。
2. 委派 `optimus-frontend-plugin:svg-to-xaml-path`（`--format data`），获得 `Data` 字符串（含 `F0`/`F1` 前缀）与其 stderr 告警。**多路径异色**的情形会返回多个 `Path`，按顺序填入同一个 icon 条目的 `paths` 数组，不需要为此额外询问用户——格式决策已经完全由 `paths` 数组长度决定。

对每个位图候选节点：调用 `mcp__getD2c` 落盘，记录相对路径为 `bitmapPath`。`bitmapPath` 必须写成相对于项目根目录的路径（与 Step 4 中 `--source-root .` 所解析的根一致），匹配 `mcp__getD2c` 典型输出约定（如 `.mastergo-icons/raw/avatar.png`）。

🔴 **红线：** `svg-to-xaml-path` 返回的 `Data` 字符串必须逐字写入 `input.json`，包括 `F0`/`F1` 前缀，不得删改、补全或重排。这条由 `icon_exporter.py` 的 `validate_contract` 强制校验——缺前缀会导致 exit 2。

单个图标的 SVG 取值失败或 `svg-to-xaml-path` 报错（如 `currentColor`、渐变 URL）不中断整批：将该图标的 `sourceKind` 标记为待定，在 `input.json` 中省略该条目，并在后续报告中列为 `unresolved`，附上兄弟 Skill 的错误原文。

组装完整的 `input.json`（结构见 `references/wpf-xaml-icon-sepc.md` 第十一节），写入 `.mastergo-icons/input.json`。

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
