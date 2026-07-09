# Unipus 官方 Claude Code 插件仓库

[![Version](https://img.shields.io/badge/version-4.1.12-blue.svg)](https://github.com/Glepooek/unipus-plugins-official)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📦 插件列表

| 插件 | 职责 |
|---|---|
| [unipus-frontend-plugin](plugins/unipus-frontend-plugin) | React/Vue/WPF 前端开发、UI 设计规范；内置唯一的复合 skill `unipus-fe-dev`（5 阶段前端开发工作流） |
| [unipus-backend-plugin](plugins/unipus-backend-plugin) | API 开发、后端架构、数据库设计 |
| [unipus-qa-plugin](plugins/unipus-qa-plugin) | 测试用例、JMeter、UI 自动化、飞书测试项目集成 |
| [unipus-prd-plugin](plugins/unipus-prd-plugin) | PRD 文档创建、审查、需求管理 |
| [unipus-feishu-plugin](plugins/unipus-feishu-plugin) | 飞书文档读写、上传、自动化 |
| [unipus-office-plugin](plugins/unipus-office-plugin) | Word/Excel/PPT/PDF 生成与处理 |
| [unipus-devops-plugin](plugins/unipus-devops-plugin) | Jenkins CI/CD、项目分析、工作周报转写；内置 SessionStart（技巧轮播）+ Notification hooks |
| [unipus-mcp-servers](plugins/unipus-mcp-servers) | GitHub Copilot MCP、MasterGo、飞书项目等 MCP 集成 |

## 🔧 外部依赖

各插件除 Claude Code 内置能力外，还依赖以下外部工具/服务：

| 插件 | 关键依赖 |
|---|---|
| unipus-frontend-plugin | Figma MCP / Sketch MCP（设计稿读取）、lark-cli（飞书文档拉取） |
| unipus-backend-plugin | Python `requests`、`beautifulsoup4`（接口文档/网页抓取） |
| unipus-qa-plugin | JMeter（性能测试执行）、Playwright + Midscene（UI 自动化）、MasterGo MCP、飞书项目 MCP |
| unipus-prd-plugin | 无 |
| unipus-feishu-plugin | lark-cli（飞书开放平台 API） |
| unipus-office-plugin | markitdown、Playwright CLI（网页转 Markdown）、PptxGenJS（PPT 生成）、reportlab + pypdf（PDF 生成）、pandas + openpyxl（Excel 处理）、LibreOffice（文档转换/重算）、.NET SDK + OpenXML SDK（docx-writer） |
| unipus-devops-plugin | Jenkins（需账号/API Token）、Python `requests` + `pyyaml` |
| unipus-mcp-servers | GitHub Copilot MCP（`GITHUB_TOKEN`）、MasterGo Magic MCP（`MASTERGO_TOKEN`）、飞书项目 MCP（`FEISHU_PROJECT_TOKEN`）、Playwright CLI |

## 🚀 快速开始

### 安装方式

**方式 1：通过 Claude Code 会话安装（推荐）**

在 Claude Code 会话中执行：

```bash
/plugin marketplace add Glepooek/unipus-plugins-official
```

**方式 2：手动克隆安装**

```bash
# 克隆仓库到 Claude Code marketplace 插件目录
git clone https://github.com/Glepooek/unipus-plugins-official ~/.claude/plugins/marketplace/unipus-plugins-official
```

### 使用插件

在 Claude Code 中调用插件的 skills：

```bash
# 调用前端开发工作流
/unipus-frontend-plugin:unipus-fe-dev

# 调用 WPF 性能优化
/unipus-frontend-plugin:wpf-xaml-performance

# 调用其他 skills
/unipus-frontend-plugin:unipus-design-ui
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
