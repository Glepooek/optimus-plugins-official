---
name: unipus-office-web-to-markdown
license: MIT
metadata:
  version: "1.9.0"
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
  - name: markitdown
    description: HTML/URL 转 Markdown
    required: false
    check_command: python -m markitdown --version
    install_command: pip install markitdown
  - name: curl
    description: markitdown 不可用时的回退抓取工具
    required: false
    check_command: curl --version
---

# unipus-office-web-to-markdown

给定一个或多个 URL，将网页内容以 Markdown 格式保存到 `docs/` 目录，自动翻译为中文。

---

## 一、输入格式

**单个 URL：** 直接粘贴，或附带目录说明。

**内联批量：** 用 `# 目录` 分组，每行一个 URL：
```
# docs/kiro
https://kiro.dev/docs/cli/guide/
https://kiro.dev/docs/cli/context/
```

**`.txt` 列表文件：** 格式同内联批量，支持 `URL 文件名.md` 两段格式（文件名可省略）。
运行 `python scripts/batch_fetch.py <file.txt>` 解析后进入批量执行流程。

---

## 二、路径推断

保存路径 = `<目录>/<文件名>.md`

**目录：** 有 `#` 声明则直接使用；否则取 URL 路径去掉 host 和开头通用前缀（`/docs/`、`/help/`），映射到 `docs/` 下。

**文件名：** 用户指定 > URL 末段（非通用词）> 抓取后取 `<title>` 转 kebab-case。
通用词：`index` `docs` `page` `home` `overview` `default` `main`

| 示例输入 | 保存路径 |
| :--- | :--- |
| `https://kiro.dev/docs/cli/guide/` | `docs/cli/guide.md` |
| 同上 + `# docs/kiro` | `docs/kiro/guide.md` |
| `https://kiro.dev/docs/` | `docs/<title-kebab>.md` |

---

## 三、执行流程

```
目标文件存在？
  ├─ 否 → 新建流程
  └─ 是 → 存量核对流程
```

### 新建流程

```
1. 确定保存路径
2. 抓取原文，落盘为 docs/.raw-<filename>.md，记录行数
3. 扫描原文图片 URL，下载内容图片到 docs/assets/
4. 翻译并写入目标文件（行数 ≤ 300 → 直接翻译；> 300 → Workflow 分段翻译）
5. 运行后处理：python scripts/post_process.py <out> [--base-url <BASE_URL>]
6. 运行核对：python scripts/verify.py docs/.raw-<filename>.md <out>
7. 差值非零则补全，重跑步骤 6 直至归零；通过后删除临时文件
8. 输出单行确认
```

### 存量核对流程

```
1. 抓取最新原文，落盘为 docs/.raw-<filename>.md
2. 运行核对：python scripts/verify.py docs/.raw-<filename>.md <out>
3. 差值非零则补全，重跑步骤 2 直至归零；通过后删除临时文件
4. 输出单行确认
```

---

## 四、抓取策略（三级降级）

**原则：抓取结果必须落盘，不直接读进对话上下文。**

### 一级：markitdown（默认）

```bash
python -m markitdown "<URL>" > docs/.raw-<filename>.md
wc -l docs/.raw-<filename>.md
```

markitdown 自动识别 YouTube、Wikipedia、RSS 等特殊类型。
输出 < 200 字符 → 进入二级。

### 二级：Playwright CLI（一级失败时）

```bash
npx @playwright/cli -s=fetch open --browser=msedge "<URL>"
# msedge 不可用改 chrome；两者都没有则省略 --browser（触发 Chromium 下载）
npx @playwright/cli -s=fetch eval "() => document.documentElement.outerHTML" > /tmp/page.html
npx @playwright/cli -s=fetch close
python -m markitdown /tmp/page.html > docs/.raw-<filename>.md && rm /tmp/page.html
# markitdown 不可用时改用：eval "() => document.body.innerText" > docs/.raw-<filename>.md
```

以下任一条件成立 → 内容无效，进入三级（HTTP 非 200 且非 4xx 则直接失败）：

| 规则 | 判定 |
| :--- | :--- |
| 正文字符数 < 200 | 无效 |
| 含 SPA 框架标记（`id="root"` / `id="__nuxt"` / `data-reactroot`）且正文 < 500 字符 | 无效 |
| 含 JS 注入标记（`__NEXT_DATA__` / `__NUXT__` / `window.__INITIAL_STATE__`） | 无效 |
| 含骨架屏特征词（`class="skeleton"` / `loading-placeholder` / `shimmer`） | 无效 |

### 三级：WebFetch（二级失败时）

调用 WebFetch 时要求：「返回完整原始文本，不要省略、不要总结、不要截断」。
结果写入 `docs/.raw-<filename>.md`，标注「WebFetch，内容可能不完整」。

---

## 五、翻译

### 直接翻译（≤ 300 行）

用 Read 工具读取临时文件，翻译后用 Write 工具写入目标文件，不在响应中回显内容。

### Workflow 分段翻译（> 300 行）

> 单次响应输出 > 300 行必然截断，Workflow + 文件落盘是唯一可靠方案。

见 [`scripts/translate_workflow.js`](scripts/translate_workflow.js)，调用方式：

```javascript
Workflow({
  scriptPath: "plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/scripts/translate_workflow.js",
  args: {
    raw:    "<绝对路径>/docs/.raw-<filename>.md",
    out:    "<绝对路径>/docs/<path>/<filename>.md",
    tmp:    "<绝对路径>/docs/.tmp-seg",
    source: "<原始 URL>",
    segSize: 90,   // 可选，默认 90 行/段
    terms:  "",    // 可选，追加术语对照
  }
})
```

断点续跑：`resumeFromRunId` 让已完成的翻译段从缓存取回，只重跑失败的阶段。

---

## 六、翻译规则

**不翻译：** 代码块、行内代码、URL、文件路径、专有名词、产品名称、API 名称。

**HTML 组件转换：**
- `<Note>...</Note>` → `> **注意：** ...` 引用块
- `<Step title="X">` → `**步骤 N：X**` 加粗标题
- `<img ...>` → 标准 Markdown 图片，路径替换为本地 `../assets/` 路径

**术语对照：**

| 原文 | 译法 |
| :--- | :--- |
| agent / Agent | 智能体 |
| subagent / sub-agent | 子智能体 |
| multi-agent | 多智能体 |
| orchestrator / lead agent | 编排者 / 主智能体 |
| harness / agent harness | 工具链 |
| context window | 上下文窗口 |
| context pollution | 上下文污染 |
| prompt | 提示词 |
| system prompt | 系统提示词 |
| tool call / tool use | 工具调用 |
| hallucination | 幻觉 |
| fine-tuning | 微调 |
| inference | 推理 |
| embedding | 嵌入 |
| token / RAG / skill / hook / plugin / MCP server | 保留原文 |

---

## 七、媒体处理

**图片：**
- 内容图片（文件名含语义词）→ 下载到 `docs/assets/`，插入 `![中文 alt](../assets/文件名)`
- 装饰图标（纯哈希名、含 `icon`/`logo`、`.svg`）→ 跳过
- `<figcaption>` 存在时图片下方插入 `*说明文字（中文）*`
- 文件名去掉哈希前缀（`69937fbb_diagram.png` → `diagram.png`）

**视频：** 仅保存链接，格式：`> 🎬 视频：[标题](URL)`，YouTube embed 转为 `watch?v=ID`。

---

## 八、输出与错误

**输出格式：**
```
✓ docs/cli/guide.md（新建，核对完整）
✓ docs/cli/guide.md（新建，Workflow 翻译，核对完整）
✓ docs/cli/guide.md（新建，已补全 2 处）
✓ docs/cli/guide.md（已存在，核对完整）
✗ docs/api/ref.md — 抓取失败 (403)
```

**执行模式：** 单 URL 零交互直接执行；批量（≥2 URL 或 `.txt`）先展示计划表等待确认再逐条处理。

**错误处理：**

| 情况 | 处理 |
| :--- | :--- |
| URL 无法访问（4xx/5xx） | 记录原因，继续下一条 |
| 三级均无效 | 标记失败，跳过 |
| 目标目录无写权限 | 报告错误，跳过 |
| `.txt` 文件不存在 | 立即中止，提示确认路径 |
| URL 重复（同批次） | 跳过，标注「已跳过（重复）」 |
| 文件已存在 | 不覆盖，执行存量核对流程 |
| Workflow 翻译中断 | resumeFromRunId 断点续跑 |
