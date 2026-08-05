# Claude Code 插件仓库

[![Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FGlepooek%2Foptimus-plugins-official%2Fmaster%2F.claude-plugin%2Fmarketplace.json&query=%24.version&label=version&color=blue)](https://github.com/Glepooek/optimus-plugins-official)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📦 插件列表

| 插件 | 职责 |
|---|---|
| [optimus-frontend-plugin](plugins/optimus-frontend-plugin) | React/Vue/WPF 前端开发、UI 设计规范、SVG `<path d>` 提取并生成 WPF `Path.Data`/XAML；有效样式不同时输出多个 WPF `Path` 元素，以保留支持的 Fill/Stroke 区分；内置唯一的复合 skill `optimus-fe-dev`（5 阶段前端开发工作流） |
| [optimus-backend-plugin](plugins/optimus-backend-plugin) | API 开发、后端架构、数据库设计 |
| [optimus-qa-plugin](plugins/optimus-qa-plugin) | 测试用例、JMeter、UI 自动化、飞书测试项目集成 |
| [optimus-prd-plugin](plugins/optimus-prd-plugin) | PRD 文档创建、审查、需求管理 |
| [optimus-feishu-plugin](plugins/optimus-feishu-plugin) | 飞书文档读写、上传、自动化 |
| [optimus-office-plugin](plugins/optimus-office-plugin) | Word/Excel/PPT/PDF 生成与处理 |
| [optimus-devops-plugin](plugins/optimus-devops-plugin) | Jenkins CI/CD、项目分析、工作周报转写；内置 SessionStart（技巧轮播）+ Notification hooks |
| [optimus-mcp-servers](plugins/optimus-mcp-servers) | GitHub Copilot MCP、MasterGo、飞书项目等 MCP 集成 |

## 🔧 外部依赖

各插件除 Claude Code 内置能力外，还依赖以下外部工具/服务：

| 插件 | 关键依赖 |
|---|---|
| optimus-frontend-plugin | Figma MCP / Sketch MCP / MasterGo MCP（设计稿读取）、lark-cli（飞书文档拉取） |
| optimus-backend-plugin | Python `requests`、`beautifulsoup4`（接口文档/网页抓取） |
| optimus-qa-plugin | JMeter（性能测试执行）、Playwright + Midscene（UI 自动化）、MasterGo MCP、飞书项目 MCP |
| optimus-prd-plugin | 无 |
| optimus-feishu-plugin | lark-cli（飞书开放平台 API） |
| optimus-office-plugin | markitdown、Playwright CLI（网页转 Markdown）、PptxGenJS（PPT 生成）、reportlab + pypdf（PDF 生成）、pandas + openpyxl（Excel 处理）、LibreOffice（文档转换/重算）、.NET SDK + OpenXML SDK（docx-writer） |
| optimus-devops-plugin | Jenkins（需账号/API Token）、Python `requests` + `pyyaml` |
| optimus-mcp-servers | GitHub Copilot MCP（`GITHUB_TOKEN`）、MasterGo Magic MCP（`MASTERGO_TOKEN`）、飞书项目 MCP（`FEISHU_PROJECT_TOKEN`）、Playwright CLI |

## 🚀 快速开始

### 安装方式

**方式 1：通过 Claude Code 会话安装（推荐）**

在 Claude Code 会话中执行：

```bash
/plugin marketplace add Glepooek/optimus-plugins-official
```

**方式 2：手动克隆安装**

```bash
# 克隆仓库到 Claude Code marketplace 插件目录
git clone https://github.com/Glepooek/optimus-plugins-official ~/.claude/plugins/marketplace/optimus-plugins-official
```

### 使用插件

在 Claude Code 中调用插件的 skills：

```bash
# 调用前端开发工作流
/optimus-frontend-plugin:optimus-fe-dev

# 调用 WPF 性能优化
/optimus-frontend-plugin:wpf-xaml-performance

# 从 SVG 提取并合并路径，转换为 WPF Path.Data
/optimus-frontend-plugin:svg-to-xaml-path

# 调用其他 skills
/optimus-frontend-plugin:optimus-design-ui

# 从 MasterGo 设计稿导出图标/背景资产为 WPF Icons.xaml
/optimus-frontend-plugin:mastergo-icon-expoter
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
