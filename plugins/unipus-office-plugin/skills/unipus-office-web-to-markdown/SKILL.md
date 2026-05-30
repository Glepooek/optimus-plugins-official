---
name: unipus:office:web-to-markdown
license: MIT
metadata:
  version: "1.0.1"
  category: document-processing
  author: Glepooek
description: >
  将网页内容抓取并以 Markdown 格式保存到 docs/ 目录，自动翻译为中文。
  支持单个 URL、对话内多 URL、或 .txt 列表文件三种输入方式。
  MUST use this skill whenever the user provides a URL and wants to save,
  fetch, download, or convert web content into a document — including
  "保存网页"、"抓取这个页面"、"把这个 URL 存下来"、"批量保存文档"。
triggers:
  - 保存网页
  - 抓取网页
  - 下载网页
  - 网页转文档
  - 网页转Markdown
  - 爬取
  - URL转文档
  - save webpage
  - fetch URL
  - download page
  - web to markdown
  - scrape
  - crawl
---

# unipus-office-web-to-markdown

给定一个或多个 URL，将网页内容以 Markdown 格式保存到 `docs/` 目录，自动翻译为中文。

---

## 一、输入格式与子目录语法

三种输入方式，**格式规则完全统一**：

### 单个 URL
```
https://kiro.dev/docs/cli/guide/
把 https://kiro.dev/docs/cli/guide/ 存到 docs/kiro/
```

### 对话内多 URL（内联批量）
```
# docs/kiro
https://kiro.dev/docs/cli/guide/
https://kiro.dev/docs/cli/context/

# docs/api
https://kiro.dev/docs/api/reference/
```

### `.txt` 列表文件

文件格式与对话内联完全一致，文件名列可省略：
```
# docs/kiro
https://kiro.dev/docs/cli/guide/  guide.md
https://kiro.dev/docs/cli/context/

# docs/api
https://kiro.dev/docs/api/reference/  reference.md
```

**`.txt` 文件解析流程：**

1. 运行 `python scripts/batch_fetch.py <file.txt>` 解析文件，得到 JSON 任务列表
2. 脚本逐行处理规则：

| 行类型 | 识别规则 | 处理方式 |
|--------|---------|---------|
| 空行 | 空白行 | 忽略 |
| 目录声明 | 以 `#` 开头 | 更新 `current_dir`，对后续条目生效 |
| URL 条目（带文件名） | `URL 文件名.md` 两段 | 记录 url、filename、dir |
| URL 条目（仅 URL） | 单段，以 `http` 开头 | 记录 url、dir，filename 为 null |
| 格式错误行 | 无法解析为上述类型 | 打印警告到 stderr，跳过 |

3. 重复 URL 在解析阶段去重（后出现的跳过，stderr 警告）
4. 文件名未带 `.md` 后缀时自动补全
5. 脚本输出 JSON 后，进入批量执行流程（先展示计划表，等确认后执行）

脚本输出格式：
```json
[
  {"url": "https://kiro.dev/docs/cli/guide/",    "filename": "guide.md", "dir": "docs/kiro"},
  {"url": "https://kiro.dev/docs/cli/context/",  "filename": null,       "dir": "docs/kiro"},
  {"url": "https://kiro.dev/docs/api/reference/","filename": "reference.md","dir": "docs/api"}
]
```

**子目录语法规则：**
- `# 路径` 声明后续 URL 的完整保存目录（含 `docs/` 前缀），如 `# docs/kiro` → 存到 `docs/kiro/`
- 遇到新 `# 路径` 则切换目录
- 无 `#` 声明时，按第二节路径推断规则自动确定目录

---

## 二、路径推断规则

保存路径由**目录**和**文件名**两部分组合：`<目录>/<文件名>.md`

### 目录来源（二选一）

1. **有 `#` 声明** → `#` 后的值即为完整保存目录
   - `# docs/kiro` → 存到 `docs/kiro/`
2. **无 `#` 声明** → 从 URL 路径自动映射，根目录为 `docs/`
   - 取 URL 路径（去掉 host），去掉开头通用前缀（`/docs/`、`/help/`），其余层级作为 `docs/` 下子目录
   - `https://kiro.dev/docs/cli/guide/` → 目录 `docs/cli/`
   - 无可用路径层级时（如 `https://kiro.dev/`）→ 直接存到 `docs/`

### 文件名推断优先级

1. **用户明确指定文件名** → 直接使用
2. **URL 末段非空且非通用词** → 取末段作为文件名
3. **URL 末段为通用词或空** → 抓取页面后取 `<title>` 转 kebab-case

通用词列表：`index`、`docs`、`page`、`home`、`overview`、`default`、`main`

### 示例对照

| 用户输入 | 保存路径 |
|---------|---------|
| `https://kiro.dev/docs/cli/guide/` | `docs/cli/guide.md` |
| `https://kiro.dev/docs/cli/guide/` + `# docs/kiro` | `docs/kiro/guide.md` |
| `https://kiro.dev/docs/cli/guide/` 存为 `my-guide.md` | `docs/my-guide.md` |
| `https://kiro.dev/docs/`（末段为通用词） | `docs/<title-kebab>.md` |

---

## 三、执行流程

### 单 URL：零交互直接执行

```
1. 按路径推断规则确定保存路径
2. 抓取网页原始内容（见下方「抓取策略」）
3. 清理无关元素（导航栏、页脚、侧边栏、Cookie 提示、广告）
4. 转换为 Markdown
5. 翻译为中文（代码块、URL、专有名词、API 名称保持原文）
6. 写入文件（目录不存在则自动创建）
7. 输出单行确认
```

输出示例：
```
✓ docs/cli/guide.md（新建）
```

### 抓取策略

**WebFetch 会对长页面做摘要压缩，导致内容不完整。** 必须按以下优先级执行：

**首选：curl + Python 提取（完整原文）**

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

若页面内容较长，分段抓取（每次偏移 8000 字符）直到内容完整：

```bash
# 第一段
... | python3 -c "...; print(text[:8000])"
# 第二段
... | python3 -c "...; print(text[8000:16000])"
# 继续直到内容结束
```

**备用：WebFetch**（仅当 Bash 工具不可用时使用）

使用 `WebFetch` 时需在 prompt 中明确要求：
> "返回页面完整原始文本，不要省略、不要总结、不要截断任何部分"

即使如此，长页面仍可能被截断，需多次调用补全剩余内容。

**内容完整性验证：** 抓取后检查是否包含文章结语/底部内容，若缺失则继续分段抓取。

### 批量（≥2 URL 或 `.txt` 文件）：先计划，再执行

**第一步：输出执行计划表，等待用户确认**

展示计划表前先按路径推断规则解析所有路径。若某条 URL 末段为通用词（需抓取页面才能确定文件名），在计划表中显示占位符，执行时实际替换：

```
准备保存以下 4 个页面（翻译为中文）：

  docs/kiro/guide.md          ← https://kiro.dev/docs/cli/guide/
  docs/kiro/context.md        ← https://kiro.dev/docs/cli/context/
  docs/api/reference.md       ← https://kiro.dev/docs/api/reference/
  docs/kiro/<从页面标题推断>  ← https://kiro.dev/docs/

确认执行？
```

**第二步：用户确认后逐条处理，实时输出进度**

```
[1/4] ✓ docs/kiro/guide.md
[2/4] ✓ docs/kiro/context.md
[3/4] ✗ docs/api/reference.md — 抓取失败 (403)
[4/4] ✓ docs/api/examples.md

完成：3 成功，1 失败
失败项：
  docs/api/reference.md — 403 Forbidden（可能需要登录）
```

### Markdown 转换规则

- 标题层级保持原始层级（`h1`→`#`，`h2`→`##`，以此类推）
- 代码块标注语言标识符
- 表格使用标准 Markdown 语法
- 列表使用 `-`（无序）或数字（有序）
- 链接格式：`[文本](URL)`
- 图片保留原始链接：`![alt](原始URL)`，不下载到本地

### 翻译规则

以下内容**保持原文不变**：
- 代码块（` ``` ` 包裹）和行内代码（`` ` `` 包裹）
- URL 和文件路径
- 专有名词、产品名称、API 名称

---

## 四、错误处理

| 情况 | 处理方式 |
|------|---------|
| URL 无法访问（4xx/5xx） | 记录失败原因，继续下一条 |
| 网页内容为空 | 警告并跳过，不写入空文件 |
| curl 不可用 | 降级使用 WebFetch，告知用户内容可能不完整 |
| 内容疑似截断（缺少结语/底部） | 继续分段抓取直至完整 |
| 目标目录无写权限 | 报告错误，跳过该条 |
| `.txt` 文件不存在 | 立即中止，提示用户确认路径 |
| URL 重复（同一批次） | 跳过后续重复项，结果标注"已跳过（重复）" |
| 文件已存在 | 直接覆盖，结果标注"已覆盖" |
