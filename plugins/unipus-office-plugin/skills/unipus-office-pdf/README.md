# u-pdf

用于创建和编辑精美 PDF 文档的 Claude Skill。
三条路由。一套设计系统。设计 token 从内容分析流经每个渲染器。

## 快速开始

```bash
bash scripts/make.sh check   # 检验依赖
bash scripts/make.sh fix     # 自动安装缺失依赖
bash scripts/make.sh demo    # 生成 → demo.pdf
```

---

## 路由 A：CREATE — 生成新 PDF

```bash
bash scripts/make.sh run \
  --title   "Q3 战略回顾" \
  --type    "proposal" \
  --author  "战略团队" \
  --date    "2025年10月" \
  --content content.json \
  --out     report.pdf
```

**`--type` 选项：**

| 类型 | 调色板 | 封面样式 | Google Fonts（封面） |
|---|---|---|---|
| `report` | 深墨色，青色强调 | `fullbleed` | Playfair Display / IBM Plex Sans |
| `proposal` | 近黑色，琥珀色强调 | `split` | Syne / Nunito Sans |
| `resume` | 白色，海军蓝强调 | `typographic` | DM Serif Display / DM Sans |
| `portfolio` | 深紫色，珊瑚色强调 | `atmospheric` | Fraunces / Inter |
| `academic` | 暖白色，海军蓝强调 | `typographic` | EB Garamond / Source Sans 3 |
| `general` | 深灰蓝，蓝色强调 | `fullbleed` | Outfit / Outfit |
| `minimal` | 近白色，红色强调 | `minimal` | Cormorant Garamond / Jost |
| `stripe` | 深海军蓝，琥珀色强调 | `stripe` | Barlow Condensed / Barlow |
| `diagonal` | 深蓝色，青色强调 | `diagonal` | Montserrat / Montserrat |
| `frame` | 暖米色，棕色强调 | `frame` | Cormorant / Crimson Pro |
| `editorial` | 白色，红色强调 | `editorial` | Bebas Neue / Libre Franklin |
| `magazine` | 暖亚麻色，深海军蓝强调 | `magazine` | Playfair Display / EB Garamond |
| `darkroom` | 深海军蓝，钢蓝色强调 | `darkroom` | Playfair Display / EB Garamond |
| `terminal` | 近黑色，霓虹绿强调 | `terminal` | Space Mono |
| `poster` | 白色，近黑色强调 | `poster` | Barlow Condensed / Courier Prime |

**content.json 内容块类型：**

```json
[
  {"type": "h1",      "text": "章节标题"},
  {"type": "h2",      "text": "小节标题"},
  {"type": "h3",      "text": "子小节标题"},
  {"type": "body",    "text": "段落文字。支持 <b>粗体</b> 和 <i>斜体</i>。"},
  {"type": "bullet",  "text": "无序列表项"},
  {"type": "numbered","text": "有序列表项——列表间计数器自动重置"},
  {"type": "callout", "text": "关键洞察或高亮发现"},
  {"type": "table",
    "headers": ["列 A", "列 B"],
    "rows":    [["a", "b"], ["c", "d"]]
  },
  {"type": "image",   "path": "chart.png", "caption": "图 1：可选说明文字"},
  {"type": "code",    "text": "def hello():\n    print('world')"},
  {"type": "math",    "text": "\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}", "label": "(1)"},
  {"type": "divider"},
  {"type": "caption", "text": "表 1：独立说明标签"},
  {"type": "pagebreak"},
  {"type": "spacer",  "pt": 16}
]
```

---

## 路由 B：FILL — 填写已有 PDF 的表单字段

```bash
# 查看 PDF 有哪些字段
bash scripts/make.sh fill --input form.pdf --inspect

# 填写字段
bash scripts/make.sh fill \
  --input  form.pdf \
  --out    filled.pdf \
  --values '{"FirstName": "张三", "Agree": "true", "Country": "CN"}'

# 或从 JSON 文件读取
bash scripts/make.sh fill --input form.pdf --out filled.pdf --data values.json
```

字段值规则：
- `text` → 任意字符串
- `checkbox` → `"true"` 或 `"false"`
- `dropdown` → 必须与 `--inspect` 显示的选项值完全匹配
- `radio` → 必须与 `--inspect` 显示的 radio 值完全匹配

---

## 路由 C：REFORMAT — 对已有文档应用设计

```bash
bash scripts/make.sh reformat \
  --input  source.md \
  --title  "年度报告" \
  --type   "report" \
  --author "研究团队" \
  --out    output.pdf
```

支持输入格式：`.md` `.txt` `.pdf` `.json`

---

## 架构

```
SKILL.md                      ← Claude 入口，路由表
design/design.md              ← 美学系统（CREATE/REFORMAT 前必读）
scripts/
  make.sh                     ← 统一 CLI
  palette.py                  ← 元数据 → tokens.json       [CREATE, REFORMAT]
  cover.py                    ← tokens.json → cover.html   [CREATE, REFORMAT]
  render_cover.js             ← cover.html → cover.pdf     [CREATE, REFORMAT]
  render_body.py              ← tokens + content → body.pdf [CREATE, REFORMAT]
  merge.py                    ← cover + body → final.pdf   [CREATE, REFORMAT]
  fill_inspect.py             ← PDF → 字段列表             [FILL]
  fill_write.py               ← PDF + 值 → 已填写 PDF      [FILL]
  reformat_parse.py           ← 文档 → content.json        [REFORMAT]
```

设计 token（`tokens.json`）从 `palette.py` 流向每个渲染器——封面和正文始终视觉一致。

## 依赖

| 工具 | 用途 | 安装方式 |
|---|---|---|
| Python 3.9+ | 所有 `.py` 脚本 | 系统自带 |
| `reportlab` | `render_body.py` 正文渲染 | `pip install reportlab` |
| `pypdf` | 填表、合并、重排 | `pip install pypdf` |
| Node.js 18+ | `render_cover.js` 封面渲染 | 系统自带 |
| `playwright` + Microsoft Edge | `render_cover.js` 封面渲染 | `npm install -g playwright && npx playwright install msedge` |

## 许可证

MIT
