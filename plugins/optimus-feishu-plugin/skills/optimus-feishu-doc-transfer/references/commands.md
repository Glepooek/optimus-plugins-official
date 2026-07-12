# lark-cli 常用命令速查

## 环境检查

```bash
# 检查版本
npx @larksuite/cli --version

# 检查认证状态
npx @larksuite/cli doctor

# 登录（首次或 token 过期时）
npx @larksuite/cli login
```

## 读取文档（docx / doc / wiki）

```bash
npx @larksuite/cli docs +fetch --doc "<URL>" --format json
```

- `--doc`：完整飞书 URL 或 doc token
- `--format`：`json`（结构化）或 `markdown`（纯文本）

## 读取表格（sheets）

```bash
npx @larksuite/cli sheets +read --url "<URL>" --range "<sheetId>!A1:Z1000"
```

- `--range`：格式为 `<sheetId>!<起始格>:<结束格>`，如 `0b4f3b!A1:Z100`
- 不确定 sheetId 时可先不指定 range，系统会列出可用 sheet

## 上传文件到云空间

```bash
# 普通上传（保留原始文件格式）
npx @larksuite/cli drive +upload --file "<本地路径>" --name "<显示名称>"

# 上传到指定文件夹
npx @larksuite/cli drive +upload --file "<本地路径>" --name "<显示名称>" --folder-token "<folder_token>"
```

## 导入为飞书文档（Markdown → docx）

```bash
npx @larksuite/cli drive +import --file "<本地.md路径>" --type docx
```

- `--type`：目标文档类型，通常为 `docx`

## 导出飞书文档到本地

```bash
npx @larksuite/cli drive +export \
  --token "<doc_token>" \
  --doc-type docx \
  --file-extension markdown \
  --output-dir "<本地目录>"
```

- `--doc-type`：源文档类型（`docx` / `doc` / `sheet`）
- `--file-extension`：导出格式（`markdown` / `pdf` / `docx` / `xlsx`）
- `--output-dir`：输出目录（自动创建）

## 搜索文档

```bash
npx @larksuite/cli docs +search --query "<关键词>" --page-size 10 --format json
```
