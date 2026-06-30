# Unipus 官方 Claude Code 插件仓库

[![Version](https://img.shields.io/badge/version-1.0.7-blue.svg)](https://github.com/Glepooek/unipus-plugins-official)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Unipus 公司官方 Claude Code 插件集合,提供前端/后端开发、测试 QA、文档处理、CI/CD、会话增强（232条技巧智能轮播）、权限通知等企业级开发工具链。

## 📦 插件列表

### 1. [unipus-frontend-plugin](plugins/unipus-frontend-plugin) - 前端开发工具集

**功能：** React/Vue 开发、WPF XAML 性能优化、UI 设计规范、组件库、前端架构文档

**核心 Skills：**
- `unipus:fe-dev` - 前端全流程开发（复合 skill，5 阶段工作流）
- `unipus:design-ui` - UI 设计规范管理
- `wpf-xaml-performance` - WPF XAML 性能优化

**特色：** 唯一的复合 skill 实现，包含完整的前端开发工作流（从 PRD 到交付）。

### 2. [unipus-backend-plugin](plugins/unipus-backend-plugin) - 后端开发工具集

**功能：** API 开发、后端架构设计、数据库设计、API 文档生成

**核心 Skills：**
- 后端架构设计
- API 开发和文档生成
- 数据库设计和优化

### 3. [unipus-qa-plugin](plugins/unipus-qa-plugin) - 测试 QA 工具集

**功能：** 测试用例设计、测试报告、JMeter 脚本、UI 自动化、飞书测试项目管理

**核心 Skills：**
- 测试用例设计和管理
- JMeter 性能测试脚本生成
- UI 自动化测试
- 飞书测试项目集成

### 4. [unipus-prd-plugin](plugins/unipus-prd-plugin) - PRD 管理工具集

**功能：** PRD 文档创建、优化、审查，产品需求全流程管理

**核心 Skills：**
- PRD 文档创建和模板化
- PRD 审查和优化
- 需求管理流程

### 5. [unipus-feishu-plugin](plugins/unipus-feishu-plugin) - 飞书集成工具集

**功能：** 飞书文档读写、文档上传、文档加载等自动化操作

**核心 Skills：**
- 飞书文档自动化读写
- 文档批量处理
- 飞书 API 集成

### 6. [unipus-office-plugin](plugins/unipus-office-plugin) - Office 文档处理工具集

**功能：** Word、Excel、PowerPoint、PDF 文档的生成和处理

**核心 Skills：**
- Word 文档生成和模板
- Excel 数据处理和报表
- PowerPoint 演示文稿生成
- PDF 文档处理

### 7. [unipus-devops-plugin](plugins/unipus-devops-plugin) - DevOps 工具集

**功能：** Jenkins CI/CD、API 变更通知、应用初始化、项目分析、工作周报转写

**核心 Skills：**
- Jenkins 流水线配置
- CI/CD 自动化
- 应用初始化脚手架
- 项目结构分析
- **工作周报转写** - 从对话、日志、git 提交中自动提取工作内容，生成标准四段式周报

**内置 Hooks（自动加载）：**
- **SessionStart Hook** - 会话启动时展示技巧（232条技巧智能轮播，带进度追踪）
- **Notification Hook** - Windows 权限通知

### 8. [unipus-mcp-servers](plugins/unipus-mcp-servers) - MCP 服务器集成

**功能：** GitHub Copilot MCP、MasterGo 设计协作、飞书项目等企业级 MCP 服务

**集成服务：**
- GitHub Copilot MCP 服务
- MasterGo 设计协作 MCP
- 飞书项目管理 MCP

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
/unipus:fe-dev

# 调用 WPF 性能优化
/wpf-xaml-performance

# 调用其他 skills
/unipus:design-ui
```

## 🏗️ 核心特性

### 工作流驱动开发

**unipus:fe-dev** - 唯一的复合 skill，提供完整的前端开发工作流：
- 5 阶段自动化：需求收集 → 分析规划 → 代码生成 → 交付物生成 → 验证完成
- Subagent 驱动并行生成，显著提升开发效率
- 详见 [ARCHITECTURE.md](plugins/unipus-frontend-plugin/skills/unipus-fe-dev/ARCHITECTURE.md)

### 智能会话增强

**SessionStart Hook** - 每次启动自动展示技巧：
- 230 条 Claude Code 使用技巧智能轮播
- 自动追踪展示进度，确保不重复
- 涵盖开发、测试、文档、CI/CD 等全方位实践

### 企业级集成

**MCP 服务器支持**：
- GitHub Copilot MCP - 代码生成增强
- MasterGo 设计协作 - 设计稿自动转换
- 飞书项目管理 - 项目数据同步

## 📚 文档

- **[CLAUDE.md](CLAUDE.md)** - Claude Code 项目指导文档（中文）
- **[CLAUDE_WORKFLOW.md](CLAUDE_WORKFLOW.md)** - Claude Code Skill 工作流最佳实践（通用）
- **[ARCHITECTURE.md](plugins/unipus-frontend-plugin/skills/unipus-fe-dev/ARCHITECTURE.md)** - 复合 Skill 架构设计文档

## 🛠️ 开发指南

### 创建新插件

1. 在 `plugins/` 下创建新目录
2. 添加 `skills/{skill-name}/SKILL.md`
3. （可选）添加 `hooks/hooks.json` 配置
4. 在 `.claude-plugin/marketplace.json` 中注册插件

### 测试插件

```bash
# 测试 skill 加载
/your-plugin:skill-name

# 检查 skill 文件语法
head -20 plugins/{plugin-name}/skills/{skill-name}/SKILL.md

# 验证 hooks 配置
cat plugins/{plugin-name}/hooks/hooks.json
```

### 版本管理

遵循语义化版本控制：

- **Patch (x.x.X)**: Bug 修复、文档更新
- **Minor (x.X.x)**: 新增插件、新增 skill
- **Major (X.x.x)**: 架构变更、破坏性更新

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- **官网**: [https://www.unipus.cn](https://www.unipus.cn)
- **GitHub**: [https://github.com/Glepooek/unipus-plugins-official](https://github.com/Glepooek/unipus-plugins-official)
- **Claude Code 文档**: [https://docs.anthropic.com/claude/docs/claude-code](https://docs.anthropic.com/claude/docs/claude-code)

## 💡 技巧

- **会话技巧轮播**: 每次启动会话时，SessionStart Hook 会自动展示 2 条随机技巧（共 230 条），智能追踪展示进度
- **快捷键**: 在 Claude Code 会话中按 `#` 键可以快速将学习内容写入 CLAUDE.md
- **Hooks 调试**: 使用 `echo $CLAUDE_PLUGIN_ROOT` 查看插件根目录环境变量

## ⚠️ 故障排查

遇到问题？查看 [CLAUDE.md](CLAUDE.md) 中的**故障排查**章节，包含：
- SessionStart Hook 失败诊断
- Hooks 未加载的解决方法
- Skill 加载失败的常见原因
- Windows 编码问题解决方案

---

**维护者**: Unipus 团队
**问题反馈**: [GitHub Issues](https://github.com/Glepooek/unipus-plugins-official/issues)
