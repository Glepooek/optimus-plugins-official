# web-to-markdown Skill 设计文档

**日期：** 2026-05-30
**作者：** Glepooek
**版本：** 1.0.0
**状态：** 已批准

---

## 背景

`unipus:office:web-to-markdown` 的核心功能：给定一个或多个 URL，将网页内容以 Markdown 格式保存到 `docs/` 目录，并自动翻译为中文。

本次重构目标：提升易用性（用户少做决策）+ 提升执行确定性（模型按清晰规则执行，不猜测不反复确认）。

---

## 一、Frontmatter

```yaml
name: unipus:office:web-to-markdown
license: MIT
metadata:
  version: "1.0.0"
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
```

**设计决策：**
- `name` 采用 `unipus:office:*` 冒号格式，与同插件其他 skills 对齐
- triggers 中英双语，覆盖"保存/抓取/下载/爬取/转换"全部意图词
- description 保留英文 MUST 句式，与 docx/pdf 风格一致

---

## 二、输入格式与子目录语法

三种输入方式，**格式规则完全统一**：

### 单个 URL
```
https://kiro.dev/docs/cli/guide/
```
```
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
文件格式与对话内联完全一致：
```
# docs/kiro
https://kiro.dev/docs/cli/guide/  guide.md
https://kiro.dev/docs/cli/context/

# docs/api
https://kiro.dev/docs/api/reference/  reference.md
```

**`.txt` 文件解析流程：**

1. 用 `scripts/batch_fetch.py <file.txt>` 解析文件，输出 JSON 任务列表
2. 脚本逐行处理，规则如下：

| 行类型 | 识别规则 | 处理方式 |
|--------|---------|---------|
| 空行 | 空白行 | 忽略 |
| 目录声明 | 以 `#` 开头 | 更新 `current_dir`，对后续条目生效 |
| URL 条目（带文件名） | `URL 文件名.md` 两段 | 记录 url、filename、dir |
| URL 条目（仅 URL） | 单段，以 `http` 开头 | 记录 url、dir，filename 为 null（由模型推断） |
| 格式错误行 | 无法解析为上述任何类型 | 打印警告到 stderr，跳过 |

3. 重复 URL 在解析阶段去重（后出现的跳过，stderr 警告）
4. 文件名未带 `.md` 后缀时自动补全
5. 脚本输出标准 JSON，模型读取后进入**批量执行流程**（先展示计划表，等确认后执行）

**脚本输出格式：**
```json
[
  {"url": "https://kiro.dev/docs/cli/guide/", "filename": "guide.md", "dir": "docs/kiro"},
  {"url": "https://kiro.dev/docs/cli/context/", "filename": null, "dir": "docs/kiro"},
  {"url": "https://kiro.dev/docs/api/reference/", "filename": "reference.md", "dir": "docs/api"}
]
```
`filename` 为 null 时，模型按路径推断规则（第三节）自动生成文件名。

**子目录语法规则：**
- `# 子目录` 声明后续 URL 的保存目录（相对于 `docs/`）
- 遇到新 `# 子目录` 则切换
- 无 `# 子目录` 声明时，按路径推断规则自动确定目录（见下节）
- `.txt` 文件中文件名列**可省略**，省略时按路径推断规则自动生成

---

## 三、路径推断规则

保存路径由**目录**和**文件名**两部分组合：`<目录>/<文件名>.md`

### 目录来源（二选一）

1. **有 `#` 声明** → `#` 后的值即为完整保存目录（含 `docs/` 前缀）
   - `# docs/kiro` → 保存到 `docs/kiro/`
2. **无 `#` 声明** → 从 URL 路径自动映射，默认根目录为 `docs/`
   - `https://kiro.dev/docs/cli/guide/` → 目录为 `docs/cli/`
   - 规则：取 URL 路径（去掉 host），去掉开头通用前缀（`/docs/`、`/help/`），其余层级作为 `docs/` 下的子目录
   - 无可用路径层级时（如 `https://kiro.dev/`）→ 直接存到 `docs/`

### 文件名推断优先级

1. **用户明确指定文件名** → 直接使用
2. **URL 末段路径非空且非通用词** → 取末段作为文件名
3. **URL 末段为通用词或空** → 抓取页面后取 `<title>` 转 kebab-case

通用词列表：`index`、`docs`、`page`、`home`、`overview`、`default`、`main`

### 示例对照

| 用户输入 | 保存路径 |
|---------|---------|
| `https://kiro.dev/docs/cli/guide/` | `docs/cli/guide.md` |
| `https://kiro.dev/docs/cli/guide/` + `# docs/kiro` | `docs/kiro/guide.md` |
| `https://kiro.dev/docs/cli/guide/` 存为 `my-guide.md` | `docs/my-guide.md` |
| `https://kiro.dev/docs/` （末段为通用词）| `docs/<title-kebab>.md` |

---

## 四、执行流程

### 单 URL：零交互直接执行

```
1. 解析路径（按路径推断规则）
2. WebFetch 抓取网页
3. 清理无关元素（导航栏、页脚、侧边栏、Cookie 提示、广告）
4. 转换为 Markdown
5. 翻译为中文（代码块、URL、专有名词、API 名称保持原文）
6. 写入文件（目录不存在则自动创建）
7. 输出单行确认
```

输出示例：
```
✓ docs/kiro/guide.md（新建）
```

### 批量（≥2 URL 或 `.txt` 文件）：先计划，再执行

**第一步：输出执行计划表，等待用户确认**

```
准备保存以下 4 个页面（翻译为中文）：

  docs/kiro/guide.md     ← https://kiro.dev/docs/cli/guide/
  docs/kiro/context.md   ← https://kiro.dev/docs/cli/context/
  docs/api/reference.md  ← https://kiro.dev/docs/api/reference/
  docs/api/examples.md   ← https://kiro.dev/docs/api/examples/

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

## 五、错误处理

| 情况 | 处理方式 |
|------|---------|
| URL 无法访问（4xx/5xx） | 记录失败原因，继续下一条 |
| 网页内容为空 | 警告并跳过，不写入空文件 |
| 目标目录无写权限 | 报告错误，跳过该条 |
| `.txt` 文件不存在 | 立即中止，提示用户确认路径 |
| URL 重复（同一批次） | 跳过后续重复项，结果标注"已跳过（重复）" |
| 文件已存在 | 直接覆盖，结果标注"已覆盖" |

---

## 六、辅助脚本更新点

`scripts/batch_fetch.py` 需同步更新：
- 捕获 `# 子目录` 行，将 `dir` 字段加入 JSON 输出
- 文件名列可省略（省略时输出 `"filename": null`，由模型执行推断）
- URL 去重逻辑保留
- 自动补 `.md` 扩展名保留

输出 JSON 格式：
```json
[
  {"url": "https://kiro.dev/docs/cli/guide/", "filename": null, "dir": "docs/kiro"},
  {"url": "https://kiro.dev/docs/api/reference/", "filename": "reference.md", "dir": "docs/api"}
]
```
