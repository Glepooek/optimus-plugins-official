---
name: unipus-office-web-to-markdown
license: MIT
metadata:
  version: "1.5.0"
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
---

# unipus-office-web-to-markdown

给定一个或多个 URL，将网页内容以 Markdown 格式保存到 `docs/` 目录，自动翻译为中文。

---

## 一、输入格式

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

格式与内联批量一致，支持 `URL 文件名.md` 两段格式，文件名可省略。
运行 `python scripts/batch_fetch.py <file.txt>` 解析，得到任务列表后进入批量执行流程。

**子目录语法：**
- `# 路径` 声明后续 URL 的完整保存目录，如 `# docs/kiro` → 存到 `docs/kiro/`
- 无 `#` 声明时，按下节路径推断规则自动确定目录

---

## 二、路径推断规则

保存路径 = `<目录>/<文件名>.md`

**目录（二选一）：**
1. 有 `#` 声明 → 直接使用声明值
2. 无声明 → 取 URL 路径去掉 host 和开头通用前缀（`/docs/`、`/help/`），其余层级映射到 `docs/` 下

**文件名优先级：**
1. 用户明确指定 → 直接使用
2. URL 末段非通用词 → 取末段
3. URL 末段为通用词或空 → 抓取后取 `<title>` 转 kebab-case

通用词：`index`、`docs`、`page`、`home`、`overview`、`default`、`main`

**示例：**

| 用户输入 | 保存路径 |
|---------|---------|
| `https://kiro.dev/docs/cli/guide/` | `docs/cli/guide.md` |
| 同上 + `# docs/kiro` | `docs/kiro/guide.md` |
| 同上，存为 `my-guide.md` | `docs/my-guide.md` |
| `https://kiro.dev/docs/`（通用词末段） | `docs/<title-kebab>.md` |

---

## 三、执行流程

每条 URL 先判断目标文件是否存在，走不同分支：

```
目标文件存在？
  ├─ 否 → 新建流程
  └─ 是 → 存量核对流程
```

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

### 抓取策略（三级降级）

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

内容较长时分段抓取（每次偏移 8000 字符）直到完整。

> 注：使用 markitdown 时，若返回内容 < 200 字符仍视为无效，进入二级。

**curl 后执行动态页面判定**（满足任一 → 内容无效，进入二级；规则 5 直接失败）：

| # | 规则 | 说明 |
|---|------|------|
| 1 | 正文字符数 < 200 | 基本空壳 |
| 2 | 含 SPA 框架标记且正文 < 500 字符 | `id="root"` / `id="app"` / `id="__nuxt"` / `data-reactroot` |
| 3 | 含 JS 数据注入标记（无论正文长短） | `__NEXT_DATA__` / `__NUXT__` / `window.__INITIAL_STATE__` |
| 4 | 含骨架屏特征词 | `class="skeleton"` / `loading-placeholder` / `shimmer` |
| 5 | HTTP 非 200 且非 4xx | 网络错误，直接标记失败 |

**二级：Playwright CLI**（curl 内容无效时）

通过 `npx @playwright/cli` 启动无头浏览器抓取动态页面。用 `-s=fetch` 绑定会话名，确保多次调用共享同一浏览器进程。

默认使用 `--browser=msedge`（调用系统已安装的 Edge，零下载）；若系统无 Edge 则改用 `--browser=chrome`；两者均不可用时省略 `--browser` 参数（会触发 Chromium 自动下载并缓存）：

```bash
npx @playwright/cli -s=fetch open --browser=msedge "<URL>"
npx @playwright/cli -s=fetch eval "() => document.body.innerText"
npx @playwright/cli -s=fetch close
```

需要交互（如点击加载更多）时：
```bash
npx @playwright/cli -s=fetch click "button.load-more"
npx @playwright/cli -s=fetch eval "() => document.body.innerText"
```

调试时加 `--headed` 可见浏览器窗口；`snapshot --filename=snap.yaml` 可将页面结构写入文件辅助定位元素。

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

抓取后同样执行动态页面判定（规则 1-4）：有效 → 继续处理，标注「动态抓取」；无效 → 进入三级。

**三级：WebFetch**（Playwright CLI 不可用或内容仍无效）

调用时明确要求：「返回页面完整原始文本，不要省略、不要总结、不要截断任何部分」。长页面需多次调用补全，结果标注「WebFetch，内容可能不完整」。

### 新建流程

```
1. 按路径推断规则确定保存路径
2. 抓取网页原始内容（见抓取策略）
3. 清理无关元素（导航栏、页脚、侧边栏、Cookie 提示、广告）
4. 按媒体处理规则提取图片/视频
5. 转换为 Markdown，翻译为中文（见翻译规则）
6. 文档结构：副标题紧跟主标题，元信息（来源/日期/分类）在副标题之后
7. 写入文件（目录不存在则自动创建）
8. 【两轮核对】逐段对照原文与已写文件，列出差异 → 补全 → 再次扫描确认无遗漏
9. 输出单行确认
```

### 存量核对流程（文件已存在）

```
1. 抓取网页原始内容
2. 读取本地文件
3. 【两轮核对】逐段对照，检查段落/代码块/表格/图片/视频是否遗漏 → 补全 → 确认
4. 输出单行确认
```

### 输出格式

```
✓ docs/cli/guide.md（新建，核对完整）
✓ docs/cli/guide.md（新建，已补全 2 处）
✓ docs/cli/guide.md（新建，动态抓取，核对完整）
✓ docs/cli/guide.md（已存在，已补全 3 处）
✓ docs/cli/guide.md（新建，WebFetch，内容可能不完整）
✗ docs/api/ref.md — 抓取失败 (403)
```

### 执行模式

**单 URL**：零交互直接执行，完成后输出单行确认。

**批量（≥2 URL 或 `.txt` 文件）**：先展示计划表等待确认，再逐条处理并实时输出进度：

```
准备处理以下 3 个页面：
  docs/kiro/guide.md    [新建]   ← https://kiro.dev/docs/cli/guide/
  docs/kiro/context.md  [已存在] ← https://kiro.dev/docs/cli/context/
  docs/api/reference.md [新建]   ← https://kiro.dev/docs/api/reference/
确认执行？

[1/3] ✓ docs/kiro/guide.md（新建，核对完整）
[2/3] ✓ docs/kiro/context.md（已存在，已补全 1 处）
[3/3] ✗ docs/api/reference.md — 抓取失败 (403)
完成：2 成功，1 失败
```

---

## 四、媒体处理规则

**图片：**
- 内容图片（文件名含语义词）→ 下载到 `docs/assets/`，插入 `![alt](../assets/文件名)`
- 装饰图标（纯哈希文件名、含 `icon`/`logo` 或 `.svg`）→ 跳过
- `<figcaption>` 存在时，图片下方插入：`*说明文字（中文）*`
- 文件名去掉哈希前缀（`69937fbb_diagram.png` → `diagram.png`）
- `alt` 为空时根据上下文拟写中文 alt

**视频：**
- 仅保存链接，不嵌入不下载
- YouTube embed `/embed/ID` → `https://www.youtube.com/watch?v=ID`
- 插入格式：`> 🎬 视频：[标题](URL)`，标题取 `<iframe title="">`，为空则用 URL

---

## 五、翻译规则

**保持原文不变：** 代码块、行内代码、URL、文件路径、专有名词、产品名称、API 名称。

**术语统一对照表：**

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
| token | token（保留） |
| tool call / tool use | 工具调用 / 工具使用 |
| skill / hook / plugin / MCP server | 保留原文 |
| hallucination | 幻觉 |
| fine-tuning | 微调 |
| inference | 推理 |
| embedding | 嵌入 |
| RAG | RAG（保留） |

---

## 六、错误处理

| 情况 | 处理方式 |
|------|---------|
| URL 无法访问（4xx/5xx） | 记录失败原因，继续下一条 |
| 网页内容为空 | 警告并跳过，不写入空文件 |
| curl 不可用 | 直接尝试 Playwright CLI；仍不可用则降级 WebFetch |
| Playwright CLI 不可用或内容仍无效 | 降级 WebFetch，标注「内容可能不完整」 |
| 内容疑似截断 | 继续分段抓取直至完整 |
| 目标目录无写权限 | 报告错误，跳过该条 |
| `.txt` 文件不存在 | 立即中止，提示用户确认路径 |
| URL 重复（同一批次） | 跳过后续重复项，标注「已跳过（重复）」 |
| 文件已存在 | 不覆盖，执行存量核对流程 |
