---
name: unipus:office:web-to-markdown
license: MIT
metadata:
  version: "1.1.1"
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

每条 URL 均先判断目标文件是否已存在，走不同分支：

```
判断目标文件是否存在？
  ├─ 不存在 → 【新建流程】
  └─ 已存在 → 【存量核对流程】
```

### 抓取策略

三级降级，按顺序执行，前一级内容有效（不触发任何动态页面判定规则）则不进入下一级：

**一级：curl（静态 / SSR 页面，默认路径）**

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
... | python3 -c "...; print(text[:8000])"      # 第一段
... | python3 -c "...; print(text[8000:16000])"  # 第二段
# 继续直到内容结束
```

**curl 完成后执行动态页面判定**（满足规则 1-4 任一 → 内容无效，进入二级；规则 5 例外，直接失败）：

| # | 规则 | 说明 |
|---|------|------|
| 1 | 正文字符数 < 200 | 基本空壳 |
| 2 | 含 SPA 框架标记且正文 < 500 字符 | `id="root"` / `id="app"` / `id="__nuxt"` / `id="__layout"` / `data-reactroot` |
| 3 | 含 JS 数据注入标记（无论正文长短） | `__NEXT_DATA__` / `__NUXT__` / `__REDUX_STATE__` / `window.__INITIAL_STATE__` |
| 4 | 含骨架屏 / 加载占位符特征词 | `class="skeleton"` / `loading-placeholder` / `shimmer` / `aria-busy="true"` |
| 5 | HTTP 非 200 且非 4xx 认证错误 | 网络错误（例外：不进入二级，直接标记失败） |

**二级：Playwright MCP（curl 内容无效时）**

```
1. browser_navigate(url=<URL>)

2. 等待策略（三层兜底）：
   a. browser_wait_for_load_state(state="networkidle", timeout=8000)
      超时 → 进入 b
   b. browser_wait_for_selector(
        selector="main, article, [role='main'], #main-content, .content",
        timeout=5000
      )
      超时 → 进入 c
   c. browser_wait(milliseconds=2000)

3. browser_snapshot()
   → 返回 accessibility tree（渲染后语义文本，无 JS/CSS 噪音）

4. 内容有效性二次校验（同判定规则 1-4）
   无效 → 进入三级，结果标注「Playwright 抓取内容仍为空，降级 WebFetch」
   有效 → 进入清理 / 转换 / 翻译流程（与静态路径相同）
   结果标注「动态抓取」

5. browser_close()
```

**三级：WebFetch（Playwright MCP 不可用，或抓取内容二次校验仍无效时）**

在 prompt 中明确要求：「返回页面完整原始文本，不要省略、不要总结、不要截断任何部分」。长页面仍可能被截断，需多次调用补全。结果标注「WebFetch，内容可能不完整」。

**内容完整性验证：** 抓取后检查是否包含文章结语/底部内容，若缺失则继续分段抓取。

### 新建流程

```
1. 按路径推断规则确定保存路径
2. 抓取网页原始内容（见上方「抓取策略」）
3. 清理无关元素（导航栏、页脚、侧边栏、Cookie 提示、广告）
4. 按「媒体处理规则」提取图片/视频（含 figcaption）
5. 转换为 Markdown，翻译为中文（见「翻译规则」）
6. 文档结构：副标题（subtitle）紧跟主标题之后，元信息（来源/日期/分类）在副标题之后
7. 写入文件（目录不存在则自动创建）
8. 【第一轮核对】逐段对照原始抓取内容与已写入文件，列出所有差异；若无差异则注明"未发现遗漏"
9. 【第二轮核对】逐一补全差异，再次扫描确认无遗漏，输出核对结论
10. 输出单行确认
```

### 存量核对流程（文件已存在时）

**不重新写入，直接核对已存文件与原始网页的差异：**

```
1. 抓取网页原始内容（见「抓取策略」）
2. 读取已存在的本地文件
3. 【第一轮核对】逐段对照原文与已存文件，检查段落、代码块、表格、列表、图片、视频链接是否有遗漏；列出所有差异
4. 【第二轮核对】针对差异逐一补全，补全后再次扫描全文确认无遗漏，输出核对结论
5. 输出单行确认
```

### 输出格式

```
✓ docs/blog/guide.md（新建，核对完整）
✓ docs/blog/guide.md（新建，已补全 2 处）
✓ docs/blog/guide.md（已存在，核对完整）
✓ docs/blog/guide.md（已存在，已补全 3 处）
✗ docs/blog/guide.md — 抓取失败 (403)
```

### 单 URL：零交互直接执行

按上述流程（新建或存量核对）处理，完成后输出单行确认。

### 批量（≥2 URL 或 `.txt` 文件）：先计划，再执行

**第一步：输出执行计划表，等待用户确认**

计划表中标注每条 URL 的预期状态（新建 / 已存在）：

```
准备处理以下 4 个页面：

  docs/kiro/guide.md    [新建]   ← https://kiro.dev/docs/cli/guide/
  docs/kiro/context.md  [已存在] ← https://kiro.dev/docs/cli/context/
  docs/api/reference.md [新建]   ← https://kiro.dev/docs/api/reference/
  docs/kiro/<从页面标题推断> [新建] ← https://kiro.dev/docs/

确认执行？
```

**第二步：用户确认后逐条处理，每条完成后立即输出进度**

```
[1/4] ✓ docs/kiro/guide.md（新建，核对完整）
[2/4] ✓ docs/kiro/context.md（已存在，已补全 1 处表格）
[3/4] ✗ docs/api/reference.md — 抓取失败 (403)
[4/4] ✓ docs/kiro/cli.md（新建，核对完整）

完成：3 成功，1 失败
失败项：
  docs/api/reference.md — 403 Forbidden（可能需要登录）
```

---

## 四、媒体处理规则

### 图片

1. 从原始 HTML 提取所有 `<img>` 标签的 `src` 和 `alt`，以及 `<figcaption>` 说明文字
2. **区分内容图片与装饰图标**：
   - **内容图片**：文件名含语义词（如 `browsecomp.png`、`diagram.png`）→ 下载到 `docs/assets/`，文档中插入 `![alt](../assets/文件名)`
   - **装饰图标**：纯哈希文件名、含 `placeholder`/`icon`/`logo` 或 `.svg` 扩展名 → 跳过
3. `<figcaption>` 存在时，在图片引用下方插入斜体说明：`*figcaption 内容（翻译为中文）*`
4. 文件名取 URL 最后一段，去掉哈希前缀（如 `69937fbb_Dynamic-filtering.png` → `dynamic-filtering.png`）
5. `alt` 为空时，根据图片在文章中的位置拟写中文 alt 文本

### 视频

1. 从原始 HTML 提取所有 `<iframe>` 和 `<video>` 标签
2. 仅保存视频链接，不嵌入、不下载：
   - YouTube embed（`/embed/ID`）→ 转换为 `https://www.youtube.com/watch?v=ID`
   - 其他视频 URL → 直接保留原始链接
3. 在文档对应位置插入：`> 🎬 视频：[视频标题](视频URL)`
4. 视频标题取 `<iframe title="">` 属性；若为空则用链接本身

---

## 五、翻译规则

以下内容**保持原文不变**：
- 代码块（` ``` ` 包裹）和行内代码（`` ` `` 包裹）
- URL 和文件路径
- 专有名词、产品名称、API 名称

**术语统一对照表**（遇到下列术语时，统一使用右侧译法，不可自行变体）：

| 原文 | 统一译法 |
|------|---------|
| harness / agent harness | 工具链 |
| agent / Agent | 智能体 |
| multi-agent / multi-agent system | 多智能体 / 多智能体系统 |
| subagent / sub-agent | 子智能体 |
| orchestrator / lead agent | 编排者 / 主智能体 |
| context window | 上下文窗口 |
| context pollution | 上下文污染 |
| prompt | 提示词 |
| system prompt | 系统提示词 |
| token | token（保留原文） |
| tool call | 工具调用 |
| tool use | 工具使用 |
| skill | Skill（产品功能名保留原文） |
| hook | Hook（产品功能名保留原文） |
| plugin | Plugin（产品功能名保留原文） |
| MCP server | MCP Server（保留原文） |
| hallucination | 幻觉 |
| fine-tuning | 微调 |
| inference | 推理 |
| embedding | 嵌入 |
| RAG | RAG（保留原文） |

---

## 六、错误处理

| 情况 | 处理方式 |
|------|---------|
| URL 无法访问（4xx/5xx） | 记录失败原因，继续下一条 |
| 网页内容为空 | 警告并跳过，不写入空文件 |
| curl 不可用 | 降级使用 WebFetch，告知用户内容可能不完整 |
| 内容疑似截断（缺少结语/底部） | 继续分段抓取直至完整 |
| 目标目录无写权限 | 报告错误，跳过该条 |
| `.txt` 文件不存在 | 立即中止，提示用户确认路径 |
| URL 重复（同一批次） | 跳过后续重复项，结果标注"已跳过（重复）" |
| 文件已存在 | 不覆盖，执行存量核对流程，结果标注"已存在，核对完整/已补全 N 处" |
