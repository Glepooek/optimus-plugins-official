# Optimus MCP Servers 插件

此插件为 Optimus 开发环境提供 MCP（Model Context Protocol）服务器集成。

## 包含的 MCP 服务器

### 1. GitHub MCP Server
- **类型**: HTTP
- **功能**: 提供 GitHub Copilot MCP API 访问
- **环境变量**: `GITHUB_TOKEN`

### 2. MasterGo Magic MCP
- **类型**: stdio
- **功能**: MasterGo 设计协作工具集成
- **环境变量**: `MG_MCP_TOKEN`

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

> **单一真源**：三台服务器的通用定义在插件根目录 `mcp.config.json`。运行
> `python scripts/gen_mcp_config.py` 会按各 harness 原生字段生成两套配置：
> `.mcp.json`（Claude Code，用 `headers`/`env` + `${VAR}` 插值）与
> `config.toml.example`（Codex，用 `bearer_token_env_var`/`env_vars`，不做 `${VAR}`
> 插值）。**请勿手改生成产物**，改 `mcp.config.json` 后重新生成并跑
> `python scripts/test_gen_mcp_config.py` 校验。之所以分成两套，是因为 Claude Code
> 与 Codex 的鉴权字段和 `${VAR}` 插值规则不同——没有一份 `.mcp.json` 能同时让两侧正确带入令牌。

### Claude Code 使用方式

0. 前置要求

在全局配置文件 `~/.claude/settings.json` 中设置环境变量：

```json
{
  "env": {
    "GITHUB_TOKEN": "your_github_token_here",
    "MG_MCP_TOKEN": "your_mastergo_token_here",
    "MCP_USER_TOKEN": "your_feishu_project_token_here"
  }
}
```

1. **安装插件**
   ```bash
   # 通过 marketplace 安装
   claude plugins install optimus-mcp-servers@optimus-plugins-official
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

### Codex 使用方式

Codex 有两种方式加载这些 MCP 服务器，可按需选择。

**方式 A：通过 marketplace 安装插件**——Codex 读取插件内的 `.mcp.json` 自动加载，marketplace 清单见 `.agents/plugins/marketplace.json`：

```bash
codex plugin marketplace add https://github.com/Glepooek/optimus-plugins-official
codex plugin add optimus-mcp-servers@optimus-plugins-official
```

**方式 B：手动写入 `~/.codex/config.toml`**——需要在 Codex 侧精细管理鉴权时推荐，Codex 原生字段更可靠。复制插件根目录的 `config.toml.example` 到 `~/.codex/config.toml`：

```toml
# ~/.codex/config.toml
[mcp_servers.github]
url = "https://api.githubcopilot.com/mcp/"
bearer_token_env_var = "GITHUB_TOKEN"

[mcp_servers.mastergo-magic-mcp]
command = "npx"
args = ["-y", "@mastergo/magic-mcp", "--url=https://mastergo.com"]
env_vars = ["MG_MCP_TOKEN"]

[mcp_servers.FeishuProjectMcp]
command = "npx"
args = ["-y", "@lark-project/mcp", "--domain", "https://project.feishu.cn"]
env_vars = ["MCP_USER_TOKEN"]
```

**环境变量**：两种方式都依赖以下环境变量，需在运行 Codex 的 shell 环境中设置（或写入 `~/.codex/config.toml` 的 `[shell_environment_policy.set]`）：

| 变量 | 用途 |
|---|---|
| `GITHUB_TOKEN` | GitHub Copilot MCP 鉴权（Bearer token） |
| `MG_MCP_TOKEN` | MasterGo 设计协作 token（服务原生环境变量） |
| `MCP_USER_TOKEN` | 飞书项目 user_token |

> **注意**：Codex 不会展开 `.mcp.json` 里的 `${VAR}`，也不会把 shell 环境变量自动传给 MCP
> 子进程。因此 Codex 侧**可靠**的鉴权方式是写 `~/.codex/config.toml`（上面的方式 B），
> 用 `bearer_token_env_var`（HTTP）和 `env_vars`（stdio）按名称转发环境变量。
> `config.toml.example` 已按此生成。插件内的 `.mcp.json` 是 Claude Code 原生写法，Codex
> 通过 marketplace 加载到的是服务器定义，鉴权请走方式 B。

**生效时机**：安装或修改配置后需新开一个 Codex 会话，MCP 工具才会被加载。

## Token 获取

### GitHub Token
1. 访问 https://github.com/settings/tokens
2. 生成 Personal Access Token (Classic)
3. 需要的权限：`repo`, `read:user`

### MasterGo Token
1. 登录 MasterGo (https://mastergo.com)
2. 进入用户设置 → 开发者设置
3. 创建 API Token

> 将生成的 token 导出为环境变量 `MG_MCP_TOKEN`（两侧都使用该变量名）。

### 飞书项目 Token
1. 登录飞书项目 (https://project.feishu.cn)
2. 进入浏览器开发者工具（F12）→ Application/存储 → Cookies
3. 复制 `user_token` 的值（注意：可能需要定期更新）

> 将 `user_token` 导出为环境变量 `MCP_USER_TOKEN`。该 token 建议定期检查是否过期。
