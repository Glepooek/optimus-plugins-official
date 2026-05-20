# Unipus 官方插件仓库

Unipus 公司官方 Claude Code 插件集合，提供前端/后端开发、测试 QA、文档处理、CI/CD、会话增强（278条技巧智能轮播）、权限通知等企业级开发工具链。

## 🌟 功能特性

本插件市场包含 8 个企业级开发插件，覆盖完整的软件开发生命周期：

- **🎨 前端开发**：React/Vue 开发、WPF XAML 性能优化、UI 设计规范
- **⚙️ 后端开发**：API 开发、C# 代码审查、后端架构设计
- **🧪 测试 QA**：测试用例设计、JMeter 脚本、UI 自动化、飞书测试项目管理
- **📋 PRD 管理**：PRD 文档创建、优化、审查
- **💼 飞书集成**：飞书文档读写、文档上传、文档加载
- **📄 Office 处理**：Word、Excel、PowerPoint、PDF 文档生成和处理
- **🚀 DevOps**：Jenkins CI/CD、API 变更通知、项目分析、278条技巧智能轮播
- **🔌 MCP 服务**：GitHub Copilot MCP、MasterGo 设计协作、飞书项目集成

## 📦 安装方法

### 方法一：从 Marketplace 安装（推荐）

1. 在 Claude Code 中打开命令面板
2. 输入 `/marketplace` 命令
3. 搜索 `unipus-plugins-official`
4. 点击安装按钮

### 方法二：通过 Git URL 安装

1. 在 Claude Code 中运行：
   ```bash
   /marketplace add https://github.com/Glepooek/unipus-plugins-official
   ```

2. 重新加载插件：
   ```bash
   /reload-plugins
   ```

### 方法三：手动克隆安装

1. 克隆仓库到本地：
   ```bash
   git clone https://github.com/Glepooek/unipus-plugins-official.git
   ```

2. 在 Claude Code 中添加本地 marketplace：
   ```bash
   /marketplace add file:///path/to/unipus-plugins-official
   ```
   
   例如（Windows）：
   ```bash
   /marketplace add file:///E:/ProjectxPlex/WPFCodePlex/unipus-plugins-official
   ```

3. 重新加载插件：
   ```bash
   /reload-plugins
   ```

### 方法四：通过配置文件安装

1. 编辑 Claude Code 配置文件（通常位于 `~/.claude/settings.json`）

2. 在 `marketplaces` 数组中添加：
   ```json
   {
     "marketplaces": [
       {
         "type": "git",
         "url": "https://github.com/Glepooek/unipus-plugins-official"
       }
     ]
   }
   ```

3. 重启 Claude Code 或运行 `/reload-plugins`

## 📚 插件列表

### 1. unipus-frontend-plugin
前端开发工具集
- React/Vue 组件开发
- WPF XAML 性能优化
- UI 设计规范
- 组件库集成
- 前端架构文档

### 2. unipus-backend-plugin
后端开发工具集
- API 开发与对接
- C# 代码审查（Microsoft 编码规范）
- 后端架构设计
- 数据库设计
- API 文档生成

### 3. unipus-qa-plugin
测试 QA 工具集
- 测试用例设计
- 测试报告生成
- JMeter 脚本生成
- UI 自动化测试
- 飞书测试项目管理

### 4. unipus-prd-plugin
PRD 管理工具集
- PRD 文档创建
- PRD 优化与审查
- 产品需求全流程管理

### 5. unipus-feishu-plugin
飞书集成工具集
- 飞书文档读写
- 文档上传
- 文档加载
- 飞书自动化操作

### 6. unipus-office-plugin
Office 文档处理工具集
- Word 文档生成和处理
- Excel 文档生成和处理
- PowerPoint 文档生成和处理
- PDF 文档生成和处理

### 7. unipus-devops-plugin
DevOps 工具集
- Jenkins CI/CD 集成
- API 变更通知
- 应用初始化
- 项目分析
- **SessionStart Hook**：278条开发技巧智能轮播
- **Notification Hook**：Windows 权限通知

### 8. unipus-mcp-servers
MCP 服务器集成
- GitHub Copilot MCP
- MasterGo 设计协作 MCP
- 飞书项目 MCP
- 企业级 MCP 服务

## 🚀 快速开始

安装完成后，你可以通过以下方式使用插件功能：

1. **使用 Skills**：
   ```bash
   /help skills
   ```
   查看所有可用的技能列表

2. **代码审查**：
   在 C# 项目中，Claude Code 会自动触发 `csharp-code-review` skill

3. **前端开发**：
   使用 `frontend-design` skill 创建高质量的前端界面

4. **Jenkins 构建**：
   使用 `unipus-ci-jenkins-build` skill 触发 CI 构建

5. **会话启动提示**：
   每次启动会话时，会自动显示一条开发技巧（来自 278 条技巧库）

## ⚙️ 配置说明

### DevOps 插件 Hooks

安装后，以下 Hooks 会自动启用：

- **SessionStart Hook**：会话启动时展示随机开发技巧
- **Notification Hook**：Windows 系统权限请求通知

如需禁用，可以编辑 `~/.claude/settings.json`：

```json
{
  "hooks": {
    "SessionStart": {
      "enabled": false
    }
  }
}
```

### MCP 服务器配置

部分 MCP 服务需要配置认证信息，请参考各插件的文档：

- MasterGo MCP：需要配置 API Token
- 飞书项目 MCP：需要配置飞书应用凭证

## 🔄 更新插件

```bash
# 更新所有 marketplace 插件
/marketplace update

# 重新加载插件
/reload-plugins
```

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📊 版本历史

- **1.0.4** (当前版本)
  - 完整的企业级开发工具链
  - 8 个核心插件
  - 278 条开发技巧智能轮播
  - MCP 服务集成

---

**Made with ❤️ by Unipus**
