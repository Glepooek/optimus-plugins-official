# markitdown 集成设计

**日期：** 2026-06-04  
**范围：** `unipus-office-plugin` 内两个 skill 的改造与新建  
**状态：** 待实现

---

## 背景

现有 `web-to-markdown` skill 使用 regex 脚本清理 HTML 再交由 Claude 组织成 Markdown，转换质量在表格、嵌套列表等复杂结构上有限。[markitdown](https://github.com/microsoft/markitdown) 是微软开源的文档转 Markdown 工具库，底层使用经过大量文档打磨的 `markdownify`，并原生支持 PDF/Word/PPT 等格式。

本设计方案 A+C：优化现有 `web-to-markdown`，同时新建 `file-to-markdown` skill。

---

## 一、整体架构

```
输入
 ├─ URL          → web-to-markdown（保持现有名，优化 HTML 转换层）
 └─ 本地文件路径  → file-to-markdown（新建，单文件）

共享约定：
 ├─ 输出目录：docs/
 ├─ 文件名转 kebab-case
 ├─ 语言检测：CJK 占比 < 15% → 翻译为中文
 └─ 依赖缺失：给出安装提示，有确定降级路径才回退，否则中断
```

---

## 二、web-to-markdown 改动

### 改动范围（最小化）

只改三级降级策略中的 **HTML 清理步骤**，其余逻辑不变。

**原流程：**
```
curl 抓取 → regex 手工清理 → 纯文本 → Claude 组织成 Markdown
```

**新流程（静态页面）：**
```
markitdown convert_uri(url) → 直接输出 Markdown
（markitdown 自行发起 HTTP 请求，curl 步骤合并进去，不再单独调用）
```

**新流程（动态页面，Playwright 降级路径）：**
```
Playwright 拿到 HTML 字符串 → 写入临时文件 → markitdown convert(tmp.html) → Markdown
```

### 新增零级路径

特殊 URL 类型直接交给 markitdown，跳过 curl 步骤：

| URL 特征 | markitdown 转换器 | 优势 |
|----------|------------------|------|
| `youtube.com` / `youtu.be` | YouTube 转换器 | 提取字幕而非页面文本 |
| `wikipedia.org` | Wikipedia 转换器 | 提取干净正文，去除模板噪音 |
| RSS/Atom feed | RSS 转换器 | 结构化条目提取 |

匹配到零级路径时直接执行，不进入原有三级降级流程。

### markitdown 依赖策略

```
检测命令：python -m markitdown --version
缺失时：回退到原有 regex 清理路径（原路径确定可用）
```

markitdown 缺失时 skill 仍可工作（regex 路径有效），因此回退合理。

---

## 三、file-to-markdown 新建

### 支持格式

| 格式 | 扩展名 | 所需依赖 |
|------|--------|---------|
| Word | `.docx` | `markitdown[docx]` |
| PDF | `.pdf` | `markitdown[pdf]` |
| PowerPoint | `.pptx` | `markitdown[pptx]` |
| CSV | `.csv` | `markitdown`（核心包）|
| JSON | `.json` | `markitdown`（核心包）|
| XML | `.xml` | `markitdown`（核心包）|
| 纯文本 | `.txt` | `markitdown`（核心包）|

文档类子依赖**按需检测**：用户传入 PDF 只检查 `markitdown[pdf]`，无需安装全部。

### 核心流程

```
1. 接收单个文件路径
2. 依赖检查（markitdown 核心包 + 对应格式子依赖）
   └─ 任一缺失 → 立即中断，输出安装指引
3. markitdown.convert(path) → Markdown 文本
4. 语言检测 → 必要时翻译
5. 路径推断 → 写入 docs/
6. 文件已存在 → 执行存量核对流程（同 web-to-markdown）
7. 输出确认行
```

### 依赖缺失提示模板

```
✗ 缺少依赖：markitdown[pdf]
  请先安装：pip install 'markitdown[pdf]'
  安装完成后重新运行此 skill
```

### 输出路径规则

```
文件名转 kebab-case → docs/<文件名>.md

示例：
  report-Q1.docx     → docs/report-q1.md
  API Reference.pdf  → docs/api-reference.md
  data.csv           → docs/data.md

用户可覆盖：
  "把 report.docx 存到 docs/archive/q1.md" → docs/archive/q1.md
```

### 输出确认行格式

```
✓ docs/report-q1.md（已转换，中文原文）
✓ docs/api-reference.md（已转换，已翻译为中文）
✗ docs/data.md — 缺少依赖 markitdown[pdf]，请运行：pip install 'markitdown[pdf]'
```

---

## 四、语言检测规则（两个 skill 共享）

```
取转换后 Markdown 文本的前 500 字符
跳过：代码块、行内代码、URL
统计 CJK 字符（一-鿿）占比
  ≥ 15% → 中文原文，直接输出
  < 15% → 非中文，翻译为中文
```

**翻译保护规则（不翻译以下内容）：**

- 代码块与行内代码
- URL 和文件路径
- 专有名词、产品名、API 名称
- CSV/JSON/XML 的键名（key 不翻译，value 中的自然语言内容按语言判断）

---

## 五、不在本次范围内

- 批量文件处理（file-to-markdown 只支持单文件）
- 图片 OCR / LLM 图像描述
- 音频转录
- Excel 格式（已有 `unipus-office-xlsx` skill 专门处理）
- Azure Document Intelligence 集成

---

## 六、实现顺序建议

1. 优先实现 `web-to-markdown` 改造（改动小，风险低，可立即验证 markitdown 集成效果）
2. 再新建 `file-to-markdown` skill
