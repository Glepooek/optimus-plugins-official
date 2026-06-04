---
name: unipus:office:file-to-markdown
license: MIT
metadata:
  version: "1.0.0"
  category: document-processing
  author: Glepooek
description: >
  将本地文件转换为 Markdown 并保存到 docs/ 目录，支持 Word、PDF、PPT、CSV、JSON、XML、TXT 格式。
  自动检测语言，英文内容翻译为中文，中文内容直接输出。
  MUST use this skill whenever the user provides a local file path and wants to convert it to Markdown —
  including "把这个文件转成 Markdown"、"file to markdown"、"转换文档"、"本地文件转 Markdown"。
triggers:
  - 文件转Markdown
  - 本地文件转换
  - 转换文档
  - file to markdown
  - convert file
  - docx转markdown
  - pdf转markdown
  - pptx转markdown
dependencies:
  - name: markitdown
    description: 文件格式转 Markdown 核心工具（硬依赖，缺失时立即中断）
    required: true
    check_command: python -m markitdown --version
    install_command: pip install markitdown
    install_url: https://github.com/microsoft/markitdown
  - name: markitdown[docx]
    description: Word 文档支持
    required: false
    check_command: python -c "import mammoth"
    install_command: pip install 'markitdown[docx]'
  - name: markitdown[pdf]
    description: PDF 文档支持
    required: false
    check_command: python -c "import pdfminer"
    install_command: pip install 'markitdown[pdf]'
  - name: markitdown[pptx]
    description: PowerPoint 文档支持
    required: false
    check_command: python -c "import pptx"
    install_command: pip install 'markitdown[pptx]'
---

# unipus-office-file-to-markdown

将单个本地文件转换为 Markdown，保存到 `docs/` 目录，自动翻译英文内容为中文。

---

## 一、支持格式

| 格式 | 扩展名 | 所需子依赖 |
|------|--------|-----------|
| Word | `.docx` | `markitdown[docx]` |
| PDF | `.pdf` | `markitdown[pdf]` |
| PowerPoint | `.pptx` | `markitdown[pptx]` |
| CSV | `.csv` | 核心包即可 |
| JSON | `.json` | 核心包即可 |
| XML | `.xml` | 核心包即可 |
| 纯文本 | `.txt` | 核心包即可 |

---

## 二、依赖检查

执行前必须完成依赖检查。

**第一步：检查 markitdown 核心包**

```bash
python -m markitdown --version
```

失败则立即中断，输出：

```
✗ 缺少依赖：markitdown
  请先安装：pip install markitdown
  安装完成后重新运行此 skill
```

**第二步：按文件格式检查子依赖**

| 输入扩展名 | 检查命令 | 缺失时提示 |
|-----------|----------|-----------|
| `.docx` | `python -c "import mammoth"` | `pip install 'markitdown[docx]'` |
| `.pdf` | `python -c "import pdfminer"` | `pip install 'markitdown[pdf]'` |
| `.pptx` | `python -c "import pptx"` | `pip install 'markitdown[pptx]'` |
| `.csv` `.json` `.xml` `.txt` | 无需额外检查 | — |

子依赖缺失时同样立即中断，不尝试继续。

---

## 三、执行流程

```
1. 依赖检查（见第二节）
2. 解析输入文件路径，确认文件存在
3. 推断输出路径（见第四节）
4. 检查目标文件是否已存在：
   ├─ 否 → 新建流程
   └─ 是 → 存量核对流程
```

### 新建流程

```
1. python -m markitdown "<文件路径>" → Markdown 文本
2. 语言检测 → 必要时翻译（见第五节）
3. 写入目标路径（目录不存在则自动创建）
4. 输出确认行
```

**执行命令：**
```bash
python -m markitdown "/path/to/file.docx"
```

### 存量核对流程（文件已存在）

```
1. python -m markitdown "<文件路径>" → 新 Markdown 文本
2. 读取本地已有文件
3. 逐段对照差异 → 补全 → 确认无遗漏
4. 输出确认行
```

---

## 四、输出路径规则

**默认路径：** 文件名转 kebab-case → `docs/<文件名>.md`

```
report-Q1.docx     → docs/report-q1.md
API Reference.pdf  → docs/api-reference.md
data.csv           → docs/data.md
meeting notes.txt  → docs/meeting-notes.md
```

**用户可覆盖目标路径：**
```
"把 report.docx 存到 docs/archive/q1.md"
→ 保存到 docs/archive/q1.md
```

**路径推断规则：**
1. 用户明确指定路径 → 直接使用
2. 未指定 → 文件名去扩展名，转 kebab-case，保存到 `docs/`

---

## 五、语言检测与翻译

**检测方式：**

取转换后 Markdown 文本的前 500 字符，跳过代码块（``` 包裹）、行内代码（` 包裹）和 URL，统计 CJK 字符（`一-鿿`）占比：

- **占比 ≥ 15%** → 判定为中文，直接输出，不翻译
- **占比 < 15%** → 判定为非中文，翻译为中文后输出

**翻译保护规则（以下内容保持原文不变）：**

- 代码块与行内代码
- URL 和文件路径
- 专有名词、产品名、API 名称
- CSV / JSON / XML 的键名（key 不翻译，value 中的自然语言内容按语言判断）

---

## 六、输出格式

```
✓ docs/report-q1.md（已转换，中文原文）
✓ docs/api-reference.md（已转换，已翻译为中文）
✓ docs/data.md（已存在，已补全 2 处）
✗ docs/report.md — 缺少依赖 markitdown[pdf]，请运行：pip install 'markitdown[pdf]'
✗ docs/unknown.xyz — 不支持的文件格式（.xyz）
```

---

## 七、错误处理

| 情况 | 处理方式 |
|------|---------|
| markitdown 核心包未安装 | 立即中断，输出安装指引 |
| 格式对应子依赖未安装 | 立即中断，输出对应 pip 安装命令 |
| 文件路径不存在 | 报错并中断：`✗ 文件不存在：<路径>` |
| 不支持的文件格式 | 报错并中断：`✗ 不支持的文件格式（.<ext>）` |
| 转换结果为空 | 警告并跳过，不写入空文件：`✗ 转换结果为空，跳过` |
| 目标目录无写权限 | 报告错误并中断 |
| 文件已存在 | 不覆盖，执行存量核对流程 |
