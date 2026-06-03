# Unipus MCP Servers 插件

此插件为 Unipus 开发环境提供 MCP（Model Context Protocol）服务器集成。

## 包含的 MCP 服务器

### 1. GitHub MCP Server
- **类型**: HTTP
- **功能**: 提供 GitHub Copilot MCP API 访问
- **环境变量**: `GITHUB_TOKEN`

### 2. MasterGo Magic MCP
- **类型**: stdio
- **功能**: MasterGo 设计协作工具集成
- **环境变量**: `MASTERGO_TOKEN`

### 3. 飞书项目 MCP
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

在全局配置文件 `~/.claude/settings.json` 中设置环境变量：

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
     "enabledMcpjsonServers": ["github", "mastergo-magic-mcp", "FeishuProjectMcp"]
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


## 浏览器自动化推荐：Playwright CLI

本插件不再包含 Playwright MCP 配置。对于浏览器自动化需求（如抓取 SPA 动态页面、自动化测试），推荐使用 **Playwright CLI**。

### 为什么推荐 Playwright CLI

| 对比项 | Playwright CLI | Playwright MCP |
|--------|----------------|----------------|
| **安装方式** | `npx @playwright/cli` 即开即用，包和浏览器均自动缓存 | 需要配置 MCP 服务器 |
| **使用门槛** | 低，直接在终端执行命令 | 中，需要理解 MCP 协议 |
| **交互性** | 高，支持实时查看浏览器状态 | 低，通过 Claude 间接调用 |
| **调试体验** | 可视化浏览器窗口，方便调试 | 无头模式，调试困难 |
| **功能灵活性** | 支持截图、PDF、点击、输入、滚动等完整操作 | 仅支持预设的工具调用 |
| **会话管理** | 支持持久化会话（cookies、localStorage） | 每次调用独立 |
| **Token消耗** | 较低 | 较高 |

### 快速上手

```bash
# 打开网页（优先用系统 Edge，零下载；也可改 chrome；省略则自动下载 Chromium）
npx @playwright/cli -s=demo open --browser=msedge "https://example.com"

# 提取页面文本（eval 接受函数形式）
npx @playwright/cli -s=demo eval "() => document.body.innerText"

# 截图（接受可选元素 ref）
npx @playwright/cli -s=demo screenshot

# 保存快照到文件（--filename 是 snapshot 的参数）
npx @playwright/cli -s=demo snapshot --filename=page.yaml

# 关闭浏览器
npx @playwright/cli -s=demo close
```

### 典型用例

- **抓取 SPA 动态页面**：Vue/React/Next.js 渲染后的完整内容
- **自动化表单填写**：点击、输入、选择、提交
- **端到端测试**：模拟用户操作流程
- **页面截图/PDF**：生成报告或存档

## 许可证

MIT
