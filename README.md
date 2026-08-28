# Optimus 插件库（Claude Code / Codex CLI）

[![Version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FGlepooek%2Foptimus-plugins-official%2Fmaster%2F.claude-plugin%2Fmarketplace.json&query=%24.version&label=version&color=blue)](https://github.com/Glepooek/optimus-plugins-official)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

企业级开发工具链插件仓库，同时支持 **Claude Code** 与 **OpenAI Codex CLI** 两个 harness。
两套 harness 共用同一份 SKILL.md 真源（`.claude/skills/`），通过符号链接镜像（`.kiro/skills/`、`.agents/skills/`）分发，无需双份维护。

## 📦 插件列表

| 插件 | 职责 |
|---|---|
| [optimus-frontend-plugin](plugins/optimus-frontend-plugin) | WPF 前端开发：MasterGo 设计稿转页面与组件库、SVG 转 XAML、XAML 代码审查 |
| [optimus-backend-plugin](plugins/optimus-backend-plugin) | 后端开发：需求到实现全流程、公司服务 API 对接、C# 代码审查 |
| [optimus-qa-plugin](plugins/optimus-qa-plugin) | 测试 QA：用例设计与报告、JMeter 与 UI 自动化、设计稿一致性校验、飞书项目同步 |
| [optimus-prd-plugin](plugins/optimus-prd-plugin) | PRD 全流程：需求文档创建、优化与审查 |
| [optimus-office-plugin](plugins/optimus-office-plugin) | 文档处理：Word/Excel/PPT/PDF 生成，网页与本地文件转 Markdown |
| [optimus-devops-plugin](plugins/optimus-devops-plugin) | DevOps：Jenkins 构建、项目分析、周报转写、skill 链接同步；内置 SessionStart（技巧轮播）+ Notification hooks |
| [optimus-mcp-servers](plugins/optimus-mcp-servers) | MCP 服务集成：GitHub、MasterGo 设计协作、飞书项目 |
| [optimus-media-plugin](plugins/optimus-media-plugin) | 音视频处理：分析、转码压缩、裁剪缩放、在线下载与播放预览 |

## 🔧 外部依赖

各插件除 Claude Code 内置能力外，还依赖以下外部工具/服务：

| 插件 | 关键依赖 |
|---|---|
| optimus-frontend-plugin | MasterGo MCP（设计稿读取）、Python 3 |
| optimus-backend-plugin | superpowers 插件（后端开发流程硬性依赖）、服务注册表 `api-doc-test.optimus.cn`（有本地缓存降级）、Python `requests` + `beautifulsoup4`（接口文档/网页抓取） |
| optimus-qa-plugin | JMeter（性能测试执行）、Playwright + Midscene（UI 自动化）、MasterGo MCP、飞书项目 MCP、Figma MCP + Chrome DevTools MCP（UI 一致性校验，需自行配置）、Python（XMind 生成） |
| optimus-prd-plugin | 无 |
| optimus-office-plugin | markitdown、Playwright CLI（网页转 Markdown）、PptxGenJS（PPT 生成）、reportlab + pypdf（PDF 生成）、pandas + openpyxl（Excel 处理）、LibreOffice（文档转换/重算）、.NET SDK + OpenXML SDK（docx-writer） |
| optimus-devops-plugin | Jenkins（需账号/API Token）、Python `requests` + `pyyaml`、Git（项目分析与周报提取提交记录） |
| optimus-mcp-servers | GitHub Copilot MCP（`GITHUB_TOKEN`）、MasterGo Magic MCP（`MG_MCP_TOKEN`）、飞书项目 MCP（`MCP_USER_TOKEN`） |
| optimus-media-plugin | ffmpeg/ffprobe（编解码分析与处理）、ffplay（播放预览，需图形显示环境）、yt-dlp（在线视频/音频下载） |

## 🚀 快速开始

### Claude Code 安装与使用

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

在 Claude Code 中调用插件的 skills：

```bash
# MasterGo 设计稿转 WPF 页面
/optimus-frontend-plugin:mastergo-to-wpf-page

# 音视频压缩、分辨率转换、片段截取
/optimus-media-plugin:media-compress
/optimus-media-plugin:media-resize
/optimus-media-plugin:media-trim
```

### Codex CLI 安装与使用

仓库在 `.agents/plugins/marketplace.json` 定义了 Codex marketplace（8 个插件），支持 Codex CLI 安装。

**方式 1：远程添加（推荐）**

```bash
# 添加 GitHub 仓库为 marketplace（owner/repo 或 HTTPS/SSH 均可）
codex plugin marketplace add Glepooek/optimus-plugins-official

# 手动安装单个插件（AVAILABLE）
codex plugin add optimus-frontend-plugin@optimus-plugins-official

# 查看可用插件与已安装状态
codex plugin list --available --json
```

**方式 2：本地路径添加（开发调试用）**

```bash
# 从仓库根目录添加本地 marketplace
codex plugin marketplace add ./
codex plugin add optimus-frontend-plugin@optimus-plugins-official
```

**更新已安装的插件：**

```bash
# 刷新指定市场（远程添加的市场才有快照可刷；add 后需 upgrade 才拉到新插件）
codex plugin marketplace upgrade optimus-plugins-official
```

```bash
# 省略市场名 → 刷新所有已配置的 Git 市场
codex plugin marketplace upgrade
```

注意：`upgrade` 只对 Git 市场生效（远程添加的）；「方式 2」本地路径添加的市场没有可刷新的快照，无需 upgrade。

Codex 中调用插件 skill（自动带 `plugin:` 前缀）：

```bash
# MasterGo 设计稿转 WPF 页面
/optimus-frontend-plugin:mastergo-to-wpf-page

# 分析音视频编码/分辨率/码率/时长
/optimus-media-plugin:media-analyze
```

此外，本仓库维护流程类 skill（如 `commit-cc-plugin`、`test-locally`）也会通过 `.agents/skills/` 镜像暴露给 Codex。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
