---
name: feishu-doc
description: 飞书文档读写工具。通过 lark-cli 读取、上传、下载、搜索飞书文档（Doc/Docx、Wiki、云文档附件、Sheets）。独立工具 skill，也可在主流程中替代 WebFetch 获取飞书链接内容。
metadata:
  version: "1.0.0"
  author: desktop client team
compatibility: 强依赖 Node.js/npx 环境执行 @larksuite/cli，需提前 npx @larksuite/cli auth login 完成认证；支持飞书(feishu.cn)与Lark国际版(larksuite.com)。
allowed-tools: Bash Read
triggers:
  - 飞书
  - feishu
  - lark
  - 飞书文档
  - 飞书知识库
  - wiki
  - 读取飞书
  - 上传飞书
  - 下载飞书
  - 飞书表格
---

# 飞书文档读写工具

通过 `lark-cli` 读取、上传、下载、搜索飞书文档。

**宣告：** "我正在使用 fe-dev:feishu-doc 操作飞书文档。"

**定位：** 独立工具 skill。也可在主流程 `fe-dev` 中替代 `WebFetch`，当用户提供的 PRD / API 文档链接是飞书 URL 时自动调用。

## 前置条件

<HARD-GATE>
执行任何飞书操作前，必须先检查环境：

1. **lark-cli 已安装** — `npx @larksuite/cli --version`
2. **认证已完成** — `npx @larksuite/cli doctor`

如果 doctor 报错，提示用户先运行 `! npx @larksuite/cli auth login` 完成认证。
</HARD-GATE>

## 支持的文档类型

| 类型 | URL 特征 | 读取命令 | 上传/导入 | 导出/下载 |
|------|---------|---------|----------|----------|
| 飞书文档 | `feishu.cn/docx/` 或 `feishu.cn/doc/` | `docs +fetch` | `drive +import --type docx` | `drive +export --doc-type docx` |
| 飞书知识库 | `feishu.cn/wiki/` | `docs +fetch` | `wiki nodes create` | 同文档导出 |
| 云文档附件 | `feishu.cn/file/` 或 file_token | `drive +download` | `drive +upload` | `drive +download` |
| 飞书表格 | `feishu.cn/sheets/` | `sheets +read` | `drive +import --type sheet` | `drive +export --doc-type sheet` |

> **国际版 URL** 使用 `larksuite.com` 代替 `feishu.cn`，处理逻辑相同。

## URL 解析规则

从飞书 URL 中提取 token 和类型：

```
https://xxx.feishu.cn/docx/Abc123Def456      → 类型: docx,  token: Abc123Def456
https://xxx.feishu.cn/doc/Abc123Def456        → 类型: doc,   token: Abc123Def456
https://xxx.feishu.cn/wiki/Abc123Def456       → 类型: wiki,  token: Abc123Def456
https://xxx.feishu.cn/sheets/Abc123Def456     → 类型: sheet, token: Abc123Def456
https://xxx.feishu.cn/file/Abc123Def456       → 类型: file,  token: Abc123Def456
https://xxx.feishu.cn/drive/folder/Abc123     → 类型: folder
```

**提取规则：** URL 路径中 `/docx/`、`/doc/`、`/wiki/`、`/sheets/`、`/file/` 后的第一段即为 token。忽略 URL query 参数和 hash。

---

## 功能 1：读取飞书文档

用户提供飞书 URL，返回文档内容。

### Step 1：判断 URL 类型

按 URL 解析规则识别文档类型。

### Step 2：调用 lark-cli

**飞书文档 / 知识库：**

```bash
npx @larksuite/cli docs +fetch --doc "<飞书URL>" --format json
```

返回文档的 block 结构化内容（标题、段落、列表、表格、代码块等）。

**飞书表格：**

```bash
# 先获取表格信息（sheet ID 列表）
npx @larksuite/cli sheets +info --url "<飞书URL>"

# 读取指定 sheet 内容
npx @larksuite/cli sheets +read --url "<飞书URL>" --range "<sheetId>!A1:Z1000"
```

**云文档附件：**

```bash
# 下载到临时目录后读取
npx @larksuite/cli drive +download --file-token "<token>" --output "/tmp/feishu-download/<filename>"
```

然后用 `Read` 工具读取下载的文件内容。

### Step 3：输出结构化内容

将 lark-cli 返回的 JSON 转为可读的 Markdown 格式输出。对于文档，提取：
- 标题层级
- 段落文本
- 列表项
- 表格（转 Markdown 表格）
- 代码块
- 图片（记录 token，需要时用 `docs +media-download` 下载）

---

## 功能 2：上传文档到飞书

用户提供本地文件，上传到飞书云文档。

### Step 1：判断文件类型和上传方式

| 场景 | 命令 | 说明 |
|------|------|------|
| 保持原格式（PDF/图片等） | `drive +upload` | 上传为云盘文件 |
| 转为飞书文档 | `drive +import --type docx` | .docx / .md → 飞书文档 |
| 转为飞书表格 | `drive +import --type sheet` | .xlsx / .csv → 飞书表格 |

**如用户未指定，默认行为：**
- `.docx` / `.md` → `drive +import --type docx`（转为可在线编辑的飞书文档）
- `.xlsx` / `.csv` → `drive +import --type sheet`
- 其他格式 → `drive +upload`（保持原格式）

### Step 2：执行上传

**转为云文档：**

```bash
npx @larksuite/cli drive +import --file "<本地路径>" --type docx --name "<文档名>"
```

**原格式上传：**

```bash
npx @larksuite/cli drive +upload --file "<本地路径>" --name "<文件名>"
```

**上传到指定文件夹：**

```bash
npx @larksuite/cli drive +upload --file "<本地路径>" --folder-token "<folder_token>"
npx @larksuite/cli drive +import --file "<本地路径>" --type docx --folder-token "<folder_token>"
```

### Step 3：返回结果

输出飞书文档链接或 file_token，便于用户访问。

---

## 功能 3：下载/导出飞书文档

将飞书文档导出为本地文件。

### Step 1：确定导出格式

| 文档类型 | 可导出格式 |
|---------|-----------|
| 飞书文档 | markdown, docx, pdf |
| 飞书表格 | xlsx, csv |
| 云文档附件 | 原格式下载 |

**默认导出格式：** 文档 → markdown，表格 → xlsx。

### Step 2：执行导出

**飞书文档导出：**

```bash
npx @larksuite/cli drive +export \
  --token "<document_token>" \
  --doc-type docx \
  --file-extension markdown \
  --output-dir "<输出目录>" \
  --overwrite
```

**飞书表格导出：**

```bash
npx @larksuite/cli drive +export \
  --token "<spreadsheet_token>" \
  --doc-type sheet \
  --file-extension xlsx \
  --output-dir "<输出目录>" \
  --overwrite
```

**云文档附件下载：**

```bash
npx @larksuite/cli drive +download \
  --file-token "<file_token>" \
  --output "<本地路径>" \
  --overwrite
```

### Step 3：确认下载

用 `Read` 或 `ls` 确认文件已成功下载，输出文件路径和大小。

---

## 功能 4：搜索飞书文档

按关键词搜索飞书文档。

```bash
npx @larksuite/cli docs +search --query "<关键词>" --page-size 10 --format json
```

输出搜索结果列表：标题、类型、URL、更新时间。

如需按类型筛选：

```bash
npx @larksuite/cli docs +search --query "<关键词>" --filter '{"search_obj_type":"docx"}'
```

支持的 `search_obj_type`：`doc`、`docx`、`sheet`、`wiki`。

---

## 与主流程的集成

当 `fe-dev` 主流程或 `fe-dev:collect-inputs` 中用户提供的文档链接是飞书 URL 时：

1. 识别 URL 包含 `feishu.cn` 或 `larksuite.com`
2. 自动调用本 skill 的读取功能，替代 `WebFetch`
3. 将获取到的内容按原流程继续处理

**无需用户手动指定**，链接识别是自动的。

---

## Red Flags

| 想法 | 现实 |
|------|------|
| "直接用 WebFetch 打开飞书链接" | 飞书文档需要认证，WebFetch 拿不到内容。必须用 lark-cli。 |
| "lark-cli 报权限错误，跳过吧" | 提示用户检查文档分享权限或重新认证。 |
| "表格太大，全部读取" | 先用 `sheets +info` 查看 sheet 列表和行数，再按需读取范围。 |
| "上传完就行了" | 必须返回飞书链接或 token 给用户确认。 |

## 常见错误排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `unauthorized` | 未认证或 token 过期 | `! npx @larksuite/cli auth login` |
| `permission denied` | 无文档访问权限 | 请文档所有者授权或分享 |
| `not found` | token 错误或文档已删除 | 确认 URL 正确 |
| `rate limit` | API 请求过于频繁 | 等待后重试，或加 `--page-delay` |
| `file too large` | 上传文件超过 20MB | 拆分文件或使用其他方式 |
