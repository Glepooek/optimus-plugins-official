# markitdown 集成实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 markitdown 替换 web-to-markdown 的 HTML 清理层，并新建 file-to-markdown skill 支持本地文档转 Markdown。

**Architecture:** 阶段一改造 `web-to-markdown`——新增零级特殊 URL 路径（YouTube/Wikipedia/RSS 直接交 markitdown），并将 curl 一级路径的 regex 清理替换为 `markitdown convert_uri()`，Playwright 降级路径改为抓 HTML 写临时文件后交 markitdown；阶段二新建 `file-to-markdown` skill，接收单个本地文件路径，调用 markitdown 按需转换，共享语言检测逻辑（CJK 占比阈值）。

**Tech Stack:** Python 3、markitdown（`pip install markitdown[docx,pdf,pptx]`）、现有 curl / Playwright CLI / WebFetch 工具链。

**Spec:** `docs/superpowers/specs/2026-06-04-markitdown-integration-design.md`

> **提交说明：** 本仓库统一使用 `unipus-commit` skill 完成提交与推送，各 Task 的"提交"步骤仅展示 commit message 格式供参考，实际执行时说"提交"触发 skill 即可，禁止手动 `git push`。

---

## 文件变更清单

| 操作 | 路径 | 说明 |
|------|------|------|
| Modify | `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md` | 新增零级路径、替换一级路径清理步骤、Playwright 降级更新、依赖声明补 markitdown |
| Create | `plugins/unipus-office-plugin/skills/unipus-office-file-to-markdown/SKILL.md` | 全新 skill |

---

## 阶段一：改造 web-to-markdown

### Task 1：新增 markitdown 依赖声明与零级路径

**Files:**
- Modify: `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md`

- [ ] **Step 1：读取现有 SKILL.md 顶部 frontmatter**

```bash
head -35 plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
```

确认当前 `dependencies` 块只有 `curl`。

- [ ] **Step 2：在 dependencies 块中追加 markitdown 依赖**

找到：
```yaml
dependencies:
  - name: curl
    description: 用于抓取静态网页内容
    required: true
    check_command: curl --version
    install_url: https://curl.se/download.html
```

替换为：
```yaml
dependencies:
  - name: curl
    description: 用于抓取静态网页内容
    required: true
    check_command: curl --version
    install_url: https://curl.se/download.html
  - name: markitdown
    description: HTML/URL 转 Markdown（缺失时回退到 regex 清理路径）
    required: false
    check_command: python -m markitdown --version
    install_url: https://github.com/microsoft/markitdown
    install_command: pip install markitdown
```

- [ ] **Step 3：在"三、执行流程"的"抓取策略（三级降级）"前插入零级路径说明**

在 `### 抓取策略（三级降级）` 标题上方插入：

```markdown
### 零级路径：特殊 URL（markitdown 直接处理）

在进入三级降级流程前，先检查 URL 是否属于以下特殊类型。若匹配且 markitdown 可用，直接调用 markitdown，跳过后续所有降级步骤：

| URL 特征 | markitdown 转换器 | 优势 |
|----------|------------------|------|
| `youtube.com` / `youtu.be` | YouTube 转换器 | 提取字幕而非页面文本 |
| `wikipedia.org` | Wikipedia 转换器 | 提取干净正文，去除模板噪音 |
| URL 以 `.rss` / `.atom` 结尾，或 Content-Type 含 `application/rss+xml` | RSS 转换器 | 结构化条目提取 |

**检测 markitdown 是否可用：**
```bash
python -m markitdown --version
```
不可用时跳过零级路径，直接进入三级降级流程。

**执行方式（命令行调用）：**
```bash
python -m markitdown "<URL>"
```
输出即为 Markdown 文本，直接进入翻译规则步骤，无需进一步清理。
```

- [ ] **Step 4：验证插入位置正确**

```bash
grep -n "零级路径\|三级降级\|抓取策略" plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
```

预期输出：零级路径出现在三级降级之前（行号更小）。

- [ ] **Step 5：提交**

```bash
git add plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
git commit -m "feat(web-to-markdown): 新增 markitdown 依赖声明与零级特殊 URL 路径"
```

---

### Task 2：替换一级路径（curl）的 HTML 清理步骤

**Files:**
- Modify: `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md`

- [ ] **Step 1：定位现有一级 curl 清理脚本**

```bash
grep -n "python3 -c\|regex\|re\.sub\|markitdown" plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
```

确认当前一级路径使用内联 Python regex 脚本清理 HTML。

- [ ] **Step 2：替换一级路径的清理逻辑**

找到 `**一级：curl**` 段落下的完整 bash 代码块（含 `python3 -c` 的那段），替换为：

```markdown
**一级：curl + markitdown**（静态 / SSR 页面，默认路径）

**若 markitdown 可用：**
```bash
python -m markitdown "<URL>"
```
直接输出 Markdown，无需额外清理步骤。

**若 markitdown 不可用（回退）：**
```bash
curl -s "<URL>" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
| python3 -c "
import sys, re
html = sys.stdin.read()
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'[ \t]+', ' ', text)
text = re.sub(r'\n{3,}', '\n\n', text)
print(text)
"
```
```

- [ ] **Step 3：在 curl 后的"动态页面判定"注释中补充说明**

找到 `**curl 后执行动态页面判定**` 这行，在其前加一行说明：

```markdown
> 注：使用 markitdown 时，若返回内容 < 200 字符仍视为无效，进入二级。
```

- [ ] **Step 4：验证文档结构完整**

```bash
grep -n "^###\|^####\|^---$" plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md | head -30
```

确认各节标题层级没有破坏。

- [ ] **Step 5：提交**

```bash
git add plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
git commit -m "feat(web-to-markdown): 用 markitdown 替换一级路径 regex 清理，保留回退"
```

---

### Task 3：更新 Playwright 降级路径（二级）

**Files:**
- Modify: `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md`

- [ ] **Step 1：定位二级 Playwright 路径的内容处理部分**

```bash
grep -n "Playwright\|innerText\|document.body" plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
```

- [ ] **Step 2：在二级路径"抓取后同样执行动态页面判定"前，补充 markitdown 处理说明**

找到二级路径中拿到 `innerText` 后的处理描述，在其后插入：

```markdown
**若 markitdown 可用，将 HTML 写入临时文件后转换（保留结构优于纯文本）：**
```bash
# 先获取完整 HTML（而非 innerText）
npx @playwright/cli -s=fetch eval "() => document.documentElement.outerHTML" > /tmp/page.html
python -m markitdown /tmp/page.html
rm /tmp/page.html
```

**若 markitdown 不可用，保持原有 innerText 方式：**
```bash
npx @playwright/cli -s=fetch eval "() => document.body.innerText"
```
```

- [ ] **Step 3：验证 Playwright 三步指令（open/eval/close）未被破坏**

```bash
grep -n "playwright\|s=fetch\|msedge" plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
```

确认 `open`、`eval`、`close` 三条指令仍完整存在。

- [ ] **Step 4：提交**

```bash
git add plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
git commit -m "feat(web-to-markdown): Playwright 降级路径改用 markitdown 处理 HTML"
```

---

## 阶段二：新建 file-to-markdown skill

### Task 4：创建 file-to-markdown SKILL.md（框架 + 依赖）

**Files:**
- Create: `plugins/unipus-office-plugin/skills/unipus-office-file-to-markdown/SKILL.md`

- [ ] **Step 1：确认目录不存在**

```bash
ls plugins/unipus-office-plugin/skills/ | grep file-to-markdown
```

预期：无输出。

- [ ] **Step 2：创建目录**

```bash
mkdir -p plugins/unipus-office-plugin/skills/unipus-office-file-to-markdown
```

- [ ] **Step 3：写入 SKILL.md 完整内容**

创建文件 `plugins/unipus-office-plugin/skills/unipus-office-file-to-markdown/SKILL.md`，内容如下：

```markdown
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
```

- [ ] **Step 4：验证文件已创建**

```bash
head -10 plugins/unipus-office-plugin/skills/unipus-office-file-to-markdown/SKILL.md
```

预期：看到 frontmatter `---` 开头。

- [ ] **Step 5：提交**

```bash
git add plugins/unipus-office-plugin/skills/unipus-office-file-to-markdown/SKILL.md
git commit -m "feat(file-to-markdown): 新建 skill 支持 docx/pdf/pptx/csv/json/xml/txt 转 Markdown"
```

---

### Task 5：更新 marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1：确认当前版本号**

```bash
grep '"version"' .claude-plugin/marketplace.json
```

预期：`"version": "1.2.9"`

- [ ] **Step 2：确认 unipus-office-plugin 的 description 是否需要更新**

```bash
grep -A2 "unipus-office-plugin" .claude-plugin/marketplace.json
```

当前描述：`"Office 文档处理工具集：Word、Excel、PowerPoint、PDF 文档的生成和处理，以及网页内容抓取转 Markdown"`

新描述需补充 file-to-markdown 能力：

找到：
```json
"description": "Office 文档处理工具集：Word、Excel、PowerPoint、PDF 文档的生成和处理，以及网页内容抓取转 Markdown"
```

替换为：
```json
"description": "Office 文档处理工具集：Word、Excel、PowerPoint、PDF 文档的生成和处理，网页内容抓取转 Markdown，本地文件（docx/pdf/pptx/csv/json/xml）转 Markdown"
```

- [ ] **Step 3：版本号升级（新增 skill → Minor）**

找到：
```json
"version": "1.2.9"
```

替换为：
```json
"version": "1.3.0"
```

- [ ] **Step 4：验证 JSON 格式**

```bash
python -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "JSON valid"
```

预期：`JSON valid`

- [ ] **Step 5：提交**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(marketplace): 新增 file-to-markdown skill 描述，版本升至 1.3.0"
```

---

### Task 6：推送并验证

- [ ] **Step 1：检查全部提交**

```bash
git log --oneline -6
```

预期看到 5 条新提交（Task 1-5 各一条）。

- [ ] **Step 2：pull --rebase 同步远端**

```bash
git pull --rebase origin master
```

- [ ] **Step 3：推送**

```bash
git push origin master
```

- [ ] **Step 4：验证两个 skill 文件均存在**

```bash
ls plugins/unipus-office-plugin/skills/
```

预期：`unipus-office-file-to-markdown` 出现在列表中。

```bash
grep "零级路径\|markitdown" plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md | head -5
```

预期：至少有 3 行匹配。

---

## 实现顺序

```
Task 1 → Task 2 → Task 3   （阶段一，顺序执行，每步改同一文件）
    ↓
Task 4                      （阶段二，新建 skill）
    ↓
Task 5 → Task 6             （更新 marketplace，推送）
```
