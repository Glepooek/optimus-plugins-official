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

## 配置说明

### 前置要求

在全局配置文件 `~/.claude/settings.json` 中设置环境变量：

```json
{
  "env": {
    "GITHUB_TOKEN": "your_github_token_here",
    "MASTERGO_TOKEN": "your_mastergo_token_here"
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
     "enabledMcpjsonServers": ["github", "mastergo-magic-mcp"]
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

## 许可证

MIT
