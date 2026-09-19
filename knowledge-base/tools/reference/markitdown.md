# MarkItDown

- **网址**：https://github.com/microsoft/markitdown
- **简介**：Microsoft 官方推出的轻量级 Python 工具，将各类文件转换为 Markdown，供 LLM 及文本分析流水线使用；定位类似 textract，但更注重保留标题、列表、表格、链接等重要文档结构。
- **开发语言**：Python
- **核心能力**：
  - 支持多种文件格式转换为 Markdown（含 Office 文档、PDF、图片、音频、YouTube 等，具体依赖安装的 extras）
  - LLM 图片描述：可配置 `mlm_client`/`mlm_model`（如 OpenAI GPT-4o），为文档中嵌入的图片生成描述
  - OCR 插件（`markitdown-ocr`）：为 PDF/DOCX/PPTX/XLSX 转换器新增 OCR 能力，复用已有的 `llm_client`/`llm_model` 模式提取图片中的文字
  - Azure Content Understanding 集成：支持结构化字段提取（YAML front matter）、多模态（文档/图片/音频/视频）及可按文件类型自动选择或自定义分析器
  - 提供 Python 包与命令行两种使用方式
- **安装方式**：
  - `pip install 'markitdown[all]'`
  - 源码安装：`git clone git@github.com:microsoft/markitdown.git`，`cd markitdown`，`pip install -e 'packages/markitdown[all]'`
- **备注**：需要 Python 3.10 及以上版本，官方建议在虚拟环境中安装以避免依赖冲突；官方安全提示 MarkItDown 以当前进程权限执行 I/O（如 `open()`、`requests.get()`），在不可信环境中使用需自行做输入校验，并按需调用最窄的 `convert_*` 方法（如 `convert_stream()`、`convert_local()`）。本仓库 `optimus-office-plugin` 的 `web-to-markdown` skill 已将其列为一级抓取依赖（`python -m markitdown`），抓取失败时才降级到 Playwright CLI 或 WebFetch。本次归档因本机网络无法直连 GitHub，playwright-cli 与 WebFetch 均连接失败，内容改由 WebSearch 检索到的官方信息整理，License 类型、更新/移除方式未能从可靠来源确认，故未填写对应字段。
