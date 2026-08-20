---
name: mastergo-to-wpf-components
description: 当用户提供 MasterGo 设计稿链接并要求抽取可复用视觉组件、生成组件库、沉淀样式/DataTemplate/自定义控件时使用此 Skill；产出组件索引、颜色资源与 DataTemplate 资源，并可按严格映射登记控件。Not for page generation (use mastergo-to-wpf-page) or icon export (use mastergo-icon-expoter).
metadata:
  version: "1.0.0"
  author: desktop client team
  category: generator
compatibility: Python 3；需 mastergo-magic-mcp（本仓库 plugins/optimus-mcp-servers/.mcp.json 内置）与 MASTERGO_TOKEN；需 MasterGo Team 版及以上，草稿箱文件不可用；首次使用前须填写 plugins/optimus-frontend-plugin/skills/wpf-project-conventions/CONVENTIONS.md。
allowed-tools: Read Write Bash PowerShell mastergo-magic-mcp
---

# MasterGo 设计稿抽取 WPF 组件库

从分区 DSL 离线抽取重复视觉模式，生成可审查的组件索引、颜色资源和 DataTemplate 资源。组件正文、交互和动画只能在已验证的设计信息与项目约定范围内生成。

## Step 0：需求预告

一次性比对设计稿链接、组件抽取范围和输出目录的缺失项，不逐 Step 追问。`MASTERGO_TOKEN` 属系统状态，不作为缺失项询问。

## Step 1：前置检查

1. 检查 `MASTERGO_TOKEN`、链接的 `fileId`/`layerId`、Team 版及非草稿箱条件；任一不满足即停止。
2. 读取 `wpf-project-conventions/CONVENTIONS.md`；文件缺失或 MVVM、解决方案、目录、资源字典、命名或编译关键项为空时停止，请项目负责人先填写。
3. 检查输出目录父目录存在且可写；已有 `components-index.json` 时说明将进行增量合并。

## Step 2：拉取目录与确认门

调用不带 `sectionIndex` 的 `mcp__getDesignSections`，原样写入 `.mastergo-dsl/sections-list.json`。区块数超过 8 时停止并请用户指定范围。

### 🔴 CHECKPOINT：范围与输出

展示待处理 `sectionIndex`、由约定确定的输出目录，以及是否携带 `--mapping`。等待用户明确确认后，才读取分区 DSL。

## Step 3：逐区读取 DSL

按确认范围调用 `mcp__getDesignSections(sectionIndex=N)`，每批 3–5 个，保存为 `.mastergo-dsl/section-{N}.json`。禁止使用 `getDsl` 绕过分区流程。

## Step 4：运行确定性抽取器

`$SkillDir` 必须是 Skill 加载时提供的绝对 base directory，不能取用户项目 cwd：

```powershell
python "$SkillDir\scripts\extract_components.py" --input .mastergo-dsl --out <约定输出目录>
# 仅携带用户确认的严格映射时追加：--mapping .mastergo-dsl\wpf-project-mapping.json
```

exit `0` 时据实报告抽取数量；exit `2` 时原样转达 stderr 单行 `error: ...`，不得包装为成功。

## Step 5：增量合并与冲突确认

逐条展示 `components-index.json` 中 `status=new` 的设计稿来源和资源 key。资源 key 冲突时展示新旧 diff，### 🔴 CHECKPOINT：等待用户选择覆盖或保留；不得自动覆盖。

`status=mapped` 的组件仅按严格映射白名单生成控件引用。`Background`、`BorderBrush`、`CornerRadius` 等正文仅从首个出现节点依 DSL 映射规则提取，不猜测。

## Step 6：人工接管点标注

需要 code-behind、事件或 `Storyboard` 的组件一律不自动生成；在索引项写入 `manual=true`，并在交付摘要逐条列出。

## Step 7：编译验证

从仓库根按约定的编译命令执行 `dotnet build`。失败按输出最多修复两轮；仍失败时输出 diff 交人工，不能宣称成功。

## Step 8：交付

交付新增、冲突和人工接管组件；列出 `components-index.json`、`Colors.generated.xaml`、`DataTemplates.generated.xaml`，并摘要 `fallbacks`、`manualHandoffs` 与 `unverified`。

## 不要做什么

- 不越过前置检查或确认门，不绕过分区读取。
- 不在确认前读取分区、运行 CLI 或写入组件库。
- 不猜测控件正文、业务交互、code-behind 或动画。
- 不静默覆盖冲突 resource key，不把 exit 2 包装为成功。
- 不把未经严格映射验证的名称、XAML 或属性直接写入产物。
