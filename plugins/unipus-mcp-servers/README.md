# Unipus MCP Servers 插件

此插件为 Unipus 开发环境提供 MCP（Model Context Protocol）服务器集成。

## 包含的 MCP 服务器

### 1. Playwright MCP
- **类型**: stdio
- **功能**: 基于 Microsoft Playwright 的浏览器自动化，让 Claude 可直接操控浏览器
- **浏览器**: Microsoft Edge（`msedge`）
- **前置要求**: 已安装 Node.js（`npx` 可用）；首次运行自动下载 `@playwright/mcp`
- **主要能力**:
  - 🌐 **页面导航**: `browser_navigate`、`browser_navigate_back`
  - 📸 **内容抓取**: `browser_snapshot`（accessibility tree）、`browser_take_screenshot`
  - 🖱️ **交互操作**: `browser_click`、`browser_type`、`browser_fill_form`、`browser_select_option`
  - ⌨️ **键盘/等待**: `browser_press_key`、`browser_wait_for`
  - 🗂️ **标签页管理**: `browser_tabs`（list/new/close/select）
  - 🔍 **网络监控**: `browser_network_requests`、`browser_network_request`
  - 📊 **JavaScript**: `browser_evaluate`、`browser_run_code_unsafe`
  - 🗃️ **文件操作**: `browser_file_upload`、`browser_drop`
  - 📋 **控制台日志**: `browser_console_messages`
- **典型用途**: 抓取 SPA 动态页面（Vue/React/Next.js 渲染后内容）、自动化表单填写、端到端测试

### 2. GitHub MCP Server
- **类型**: HTTP
- **功能**: 提供 GitHub Copilot MCP API 访问
- **环境变量**: `GITHUB_TOKEN`

### 3. MasterGo Magic MCP
- **类型**: stdio
- **功能**: MasterGo 设计协作工具集成
- **环境变量**: `MASTERGO_TOKEN`

### 4. 飞书项目 MCP
- **类型**: stdio
- **功能**: 飞书项目（Feishu Project）全功能集成
- **环境变量**: `MCP_USER_TOKEN`
- **主要能力**:
  - 📋 **工作项管理**: 创建、查询、更新各类工作项（需求、缺陷、任务等）
  - 🎯 **待办任务**: 查询我的待办、已办、逾期、本周待办
  - 📊 **视图看板**: 创建/查询固定视图、度量图表、全景视图
  - 📝 **计划表 (WBS)**: 创建、编辑、发布计划表草稿，管理排期和估分
  - 🔄 **流程管理**: 节点流转、状态流转、评审管理
  - 🗂️ **资源库**: 创建资源实例、从资源创建工作项
  - 💬 **协作**: 添加评论（支持富文本、@人、附件）
  - 🔍 **元数据**: 查询空间、字段配置、工作项类型、团队信息
  - 📈 **高级查询**: 支持 MQL 查询语言进行复杂条件筛选

## 配置说明

### 前置要求

**Playwright MCP** 无需配置 Token，但需要：
- 已安装 Node.js（确保 `npx` 命令可用）
- 已安装 Microsoft Edge 浏览器

其余服务器在全局配置文件 `~/.claude/settings.json` 中设置环境变量：

```json
{
  "env": {
    "GITHUB_TOKEN": "your_github_token_here",
    "MASTERGO_TOKEN": "your_mastergo_token_here",
    "MCP_USER_TOKEN": "your_feishu_project_token_here"
  }
}
```

### 使用方式

1. **安装插件**
   ```bash
   # 通过 marketplace 安装
   claude plugins install unipus-mcp-servers@unipus-plugins-official
   ```

2. **启用插件**
   - 插件安装后会提示是否启用 MCP 服务器
   - 批准后即可在 Claude Code 中使用

3. **手动启用（可选）**
   如果需要手动管理，在项目 `.claude/settings.json` 中添加：
   ```json
   {
     "enabledMcpjsonServers": ["playwright", "github", "mastergo-magic-mcp", "FeishuProjectMcp"]
   }
   ```

## Token 获取

### GitHub Token
1. 访问 https://github.com/settings/tokens
2. 生成 Personal Access Token (Classic)
3. 需要的权限：`repo`, `read:user`

### MasterGo Token
1. 登录 MasterGo (https://mastergo.com)
2. 进入用户设置 → 开发者设置
3. 创建 API Token

### 飞书项目 Token
1. 登录飞书项目 (https://project.feishu.cn)
2. 进入浏览器开发者工具（F12）→ Application/存储 → Cookies
3. 复制 `user_token` 的值（注意：可能需要定期更新）

> **提示**: 飞书项目 Token 使用 user_token，建议定期检查是否过期。

## 许可证

MIT
