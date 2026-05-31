---
name: unipus:office:pdf
description: >
  当视觉质量和设计感很重要时使用此 Skill，输出达到印刷品质的 PDF。
  CREATE（从零生成）——触发词：生成PDF、生成报告、写提案、制作简历、
  make a PDF、generate a report、write a proposal、create a resume、
  精美PDF、专业文档、封面页、客户级文档、polished PDF、cover page。
  FILL（填写表单）——触发词：填写表单、填PDF字段、完成表单、
  fill in the form、fill out this PDF、what fields does this PDF have。
  REFORMAT（转换/美化已有文档）——触发词：重新排版、转换为PDF、把这个文档变好看、
  convert to PDF、reformat this document、re-style this PDF、apply our style、
  convert Markdown to PDF、Markdown转PDF。
  MERGE（多文件合并）——触发词：把多个文件合并成PDF、把这些文档合成一份报告、
  合并这些Markdown、combine these files into a PDF、merge multiple docs into one PDF。
  只要用户在意外观质量，即使只说"导出PDF"或"export to PDF"也应触发本 Skill。
license: MIT
metadata:
  version: "1.1"
  category: document-generation
---

# unipus-office-pdf

三种任务。一个 Skill。

## 开始任何 CREATE 或 REFORMAT 工作之前，先读取 `design/design.md`。

按需读取对应章节——不必全量阅读：
- 选配色 → 「调色板逻辑」
- 选封面样式 → 「封面设计」
- 处理内容块渲染细节 → 「内容块类型参考」

---

## 路由表

| 用户意图 | 路由 | 使用的脚本 |
|---|---|---|
| 从零生成新 PDF | **CREATE** | `palette.py` → `cover.py` → `render_cover.js` → `render_body.py` → `merge.py` |
| 填写/补全已有 PDF 的表单字段 | **FILL** | `fill_inspect.py` → `fill_write.py` |
| 对单个已有文档重新排版/美化 | **REFORMAT** | `reformat_parse.py` → 然后走完整 CREATE 流程 |
| 将多个文档合并为一份 PDF | **MERGE→CREATE** | 逐个解析 → 合并 content.json → 走完整 CREATE 流程 |

**规则：** 当 CREATE 和 REFORMAT 之间难以判断时，询问用户是否有已有文档作为起点。有 → REFORMAT。没有 → CREATE。用户提供多个文件 → MERGE→CREATE。

---

## 路由 A：CREATE（从零生成）

完整流程 — 内容 → 设计 token → 封面 → 正文 → 合并 PDF。

```bash
bash scripts/make.sh run \
  --title "Q3 战略回顾" --type proposal \
  --author "战略团队" --date "2025年10月" \
  --accent "#2D5F8A" \
  --content content.json --out report.pdf
```

**文档类型：** `report`（报告）· `proposal`（提案）· `resume`（简历）· `portfolio`（作品集）· `academic`（学术）· `general`（通用）· `minimal`（极简）· `stripe`（条纹）· `diagonal`（斜切）· `frame`（边框）· `editorial`（编辑风）· `magazine`（杂志风）· `darkroom`（暗房风）· `terminal`（终端风）· `poster`（海报风）

| 类型 | 封面样式 | 视觉特征 |
|---|---|---|
| `report` | `fullbleed`（全出血） | 深色背景、点阵纹理、Playfair Display 字体 |
| `proposal` | `split`（左右分割） | 左面板 + 右侧几何图形、Syne 字体 |
| `resume` | `typographic`（字体主导） | 超大首字、DM Serif Display 字体 |
| `portfolio` | `atmospheric`（氛围感） | 近黑色背景、径向光晕、Fraunces 字体 |
| `academic` | `typographic`（字体主导） | 浅色背景、古典衬线、EB Garamond 字体 |
| `general` | `fullbleed`（全出血） | 深灰蓝色、Outfit 字体 |
| `minimal` | `minimal`（极简） | 白色 + 单条 8px 强调色带、Cormorant Garamond 字体 |
| `stripe` | `stripe`（条纹） | 3 条粗彩色横条、Barlow Condensed 字体 |
| `diagonal` | `diagonal`（斜切） | SVG 斜切封面、深/浅两半、Montserrat 字体 |
| `frame` | `frame`（边框） | 内嵌边框 + 角落装饰、Cormorant 字体 |
| `editorial` | `editorial`（编辑风） | 幽灵大字母、全大写标题、Bebas Neue 字体 |
| `magazine` | `magazine`（杂志风） | 暖米色背景、居中排版、主图、Playfair Display 字体 |
| `darkroom` | `darkroom`（暗房风） | 深蓝背景、居中排版、灰度主图、Playfair Display 字体 |
| `terminal` | `terminal`（终端风） | 近黑背景、网格线、等宽字体、霓虹绿 |
| `poster` | `poster`（海报风） | 白色背景、厚左侧边栏、超大标题、Barlow Condensed 字体 |

封面附加选项（通过 `--abstract`、`--cover-image` 注入 token）：
- `--abstract "文字"` — 封面上的摘要文本块（magazine/darkroom 类型）
- `--cover-image "url"` — 主图 URL 或本地路径（magazine、darkroom、poster 类型）

**颜色覆盖 — 始终根据文档内容来选择：**
- `--accent "#HEX"` — 覆盖强调色；`accent_lt` 会自动向白色方向变浅派生
- `--cover-bg "#HEX"` — 覆盖封面背景色

**强调色选择指导：**

你对强调色有创作自主权。从文档的语义上下文中选取——标题、行业、用途、受众——而不是选"安全的通用色"。强调色出现在章节分割线、引用框、表格表头和封面上，承载文档的视觉标识。

| 场景 | 建议强调色范围 |
|---|---|
| 法律/合规/金融 | 深海军蓝 `#1C3A5E`、炭灰 `#2E3440`、石板灰 `#3D4C5E` |
| 医疗/健康 | 蓝绿 `#2A6B5A`、冷绿 `#3A7D6A` |
| 科技/工程 | 钢蓝 `#2D5F8A`、靛蓝 `#3D4F8A` |
| 环境/可持续 | 森林绿 `#2E5E3A`、橄榄绿 `#4A5E2A` |
| 创意/艺术/文化 | 酒红 `#6B2A35`、深紫 `#5A2A6B`、赤陶 `#8A3A2A` |
| 学术/研究 | 深蓝绿 `#2A5A6B`、图书馆蓝 `#2A4A6B` |
| 企业/中性 | 石板蓝 `#3D4A5A`、石墨灰 `#444C56` |
| 奢华/高端 | 暖黑 `#1A1208`、深铜色 `#4A3820` |

**规则：** 选择一个有思想的设计师会为该特定文档选择的颜色——而不是该类型的默认色。柔和、去饱和的色调效果最佳；避免鲜艳的原色。拿不准时，选更深、更中性的颜色。

**content.json 内容块类型：**

| 块类型 | 用途 | 关键字段 |
|---|---|---|
| `h1` | 章节标题 + 强调色分割线 | `text` |
| `h2` | 小节标题 | `text` |
| `h3` | 子小节（加粗） | `text` |
| `body` | 两端对齐段落；支持 `<b>` `<i>` 标记 | `text` |
| `bullet` | 无序列表项（• 前缀） | `text` |
| `numbered` | 有序列表项——计数器在非编号块处自动重置 | `text` |
| `callout` | 带强调色左竖条的高亮提示框 | `text` |
| `table` | 数据表格——强调色表头、隔行着色 | `headers`、`rows`、`col_widths`?、`caption`? |
| `image` | 嵌入图片，缩放至栏宽 | `path`/`src`、`caption`? |
| `figure` | 图片 + 自动编号"图 N："说明文字 | `path`/`src`、`caption`? |
| `code` | 等宽代码块，带强调色左竖条 | `text`、`language`? |
| `math` | 展示型数学公式——通过 matplotlib mathtext 解析 LaTeX | `text`、`label`?、`caption`? |
| `chart` | 柱状图/折线图/饼图，用 matplotlib 渲染 | `chart_type`、`labels`、`datasets`、`title`?、`x_label`?、`y_label`?、`caption`?、`figure`? |
| `flowchart` | 流程图，节点 + 连线，用 matplotlib 渲染 | `nodes`、`edges`、`caption`?、`figure`? |
| `bibliography` | 带悬挂缩进的编号参考文献列表 | `items` [{id, text}]、`title`? |
| `divider` | 全宽强调色分割线 | — |
| `caption` | 小号柔和标注文字 | `text` |
| `pagebreak` | 强制换页 | — |
| `spacer` | 垂直空白 | `pt`（默认 12） |

**chart / flowchart 结构示例：**
```json
{"type":"chart","chart_type":"bar","labels":["Q1","Q2","Q3","Q4"],
 "datasets":[{"label":"收入","values":[120,145,132,178]}],"caption":"季度数据"}

{"type":"flowchart",
 "nodes":[{"id":"s","label":"开始","shape":"oval"},
          {"id":"p","label":"处理","shape":"rect"},
          {"id":"d","label":"有效？","shape":"diamond"},
          {"id":"e","label":"结束","shape":"oval"}],
 "edges":[{"from":"s","to":"p"},{"from":"p","to":"d"},
          {"from":"d","to":"e","label":"是"},{"from":"d","to":"p","label":"否"}]}

{"type":"bibliography","items":[
  {"id":"1","text":"作者（年份）. 标题. 出版社."}]}
```

---

## 路由 B：FILL（填写表单）

在不改变版式和设计的情况下填写已有 PDF 的表单字段。

```bash
# 第一步：检查字段
python3 scripts/fill_inspect.py --input form.pdf

# 第二步：填写
python3 scripts/fill_write.py --input form.pdf --out filled.pdf \
  --values '{"FirstName": "张三", "Agree": "true", "Country": "CN"}'
```

| 字段类型 | 值格式 |
|---|---|
| `text`（文本） | 任意字符串 |
| `checkbox`（复选框） | `"true"` 或 `"false"` |
| `dropdown`（下拉框） | 必须与 inspect 输出中的选项值完全匹配 |
| `radio`（单选框） | 必须与 radio 值匹配（通常以 `/` 开头） |

始终先运行 `fill_inspect.py` 以获取准确的字段名称。

---

## 路由 C：REFORMAT（重新排版单文件）

解析已有单个文档 → content.json → 走 CREATE 流程。

```bash
bash scripts/make.sh reformat \
  --input source.md --title "我的报告" --type report --out output.pdf
```

**支持的输入格式：** `.md` `.txt` `.pdf` `.json`

**Markdown 解析映射规则：**

`reformat_parse.py` 在解析 `.md` 时按以下规则将 Markdown 语法映射为 content.json 块：

| Markdown 语法 | 映射为 content.json 块 | 说明 |
|---|---|---|
| `# 标题` | `h1` | ATX 一级标题 |
| `## 标题` | `h2` | ATX 二级标题 |
| `### 标题` | `h3` | ATX 三级标题（四级及以下合并为 h3） |
| 普通段落 | `body` | 保留 `**粗**`→`<b>`、`*斜*`→`<i>` |
| `- 列表项` / `* 列表项` | `bullet` | 每行一个 bullet 块 |
| `1. 列表项` | `numbered` | 有序列表，序号自动管理 |
| ` ```代码块``` ` | `code` | 保留语言标注（如 ` ```python` → `"language":"python"`） |
| `> 引用` | `callout` | blockquote 映射为高亮提示框 |
| `---` / `***` | `divider` | 水平分割线 |
| Markdown 表格 | `table` | 首行作 headers，其余作 rows |
| `![alt](path)` | `figure` | alt 文字作 caption |

**注意事项：**
- 原文中 `####` 及更深层级标题统一折叠为 `h3`
- 行内 HTML 标签（`<br>`、`<span>` 等）会被剥离，仅保留 `<b>` `<i>`
- 代码块中的内容原样保留，不做任何转义

---

## 路由 D：MERGE→CREATE（多文件合并）

当用户提供多个文件（`.md`、`.txt`、`.pdf` 等）并希望合并为一份完整 PDF 时，不依赖 `reformat` 命令，而是由 Claude 负责整合内容：

**流程：**

1. **逐个解析每个文件** — 对每个输入文件运行 `reformat_parse.py`，得到各自的 content.json 片段
2. **询问用户章节顺序**（如未指定）— 确认各文件在最终文档中的排列顺序和章节标题
3. **合并为统一 content.json** — 按顺序拼接各片段，在文件边界处插入 `pagebreak` 块（可选）或 `h1` 作为章节分隔
4. **走完整 CREATE 流程** — 封面、正文、页码全部统一，整份文档共享同一套设计 token

```bash
# 示例：解析每个文件
python3 scripts/reformat_parse.py --input chapter1.md --out /tmp/ch1.json
python3 scripts/reformat_parse.py --input chapter2.md --out /tmp/ch2.json

# 由 Claude 合并（伪代码，实际由 Claude 直接操作 JSON）
# merged = ch1_blocks + [pagebreak] + ch2_blocks
# 写入 content.json，然后：

bash scripts/make.sh run \
  --title "完整报告" --type report \
  --author "作者" --date "2025年" \
  --content content.json --out merged_report.pdf
```

**合并时的设计决策：**
- 若各文件逻辑上是同一文档的不同章节 → 用 `h1` 分隔，不插 `pagebreak`（保持阅读连续性）
- 若各文件是相对独立的子报告 → 在边界处插 `pagebreak`，让每个子报告从新页开始
- 封面只生成一次，反映整份合并文档的主题，而不是某个子文件

---

## 环境检查

```bash
bash scripts/make.sh check   # 检验所有依赖
bash scripts/make.sh fix     # 自动安装缺失依赖
bash scripts/make.sh demo    # 生成示例 PDF
```

| 工具 | 用途 | 安装方式 |
|---|---|---|
| Python 3.9+ | 所有 `.py` 脚本 | 系统自带 |
| `reportlab` | `render_body.py` 正文渲染 | `pip install reportlab` |
| `pypdf` | 填表、合并、重排 | `pip install pypdf` |
| Node.js 18+ | `render_cover.js` 封面渲染 | 系统自带 |
| `playwright` + Microsoft Edge | `render_cover.js` 封面渲染（HTML → PDF） | `npm install -g playwright && npx playwright install msedge` |
