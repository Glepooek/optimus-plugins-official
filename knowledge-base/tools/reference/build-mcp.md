# Build MCP

- **网址**：https://docs.avaloniaui.net/tools/ai-tools/build-mcp
- **简介**：Avalonia 官方推出的远程 MCP server，让 AI coding assistant 直接访问 Avalonia 官方文档与专家级开发指导；免费使用，无需 license key 或本地安装，任何兼容 MCP 的编辑器/CLI 只需几秒即可接入。
- **核心能力**：
  - `search_avalonia_docs`：全文搜索 Avalonia 文档，涵盖 API 参考、教程、指南
  - `lookup_avalonia_api`：查询指定的 Avalonia 类/属性/方法/事件
  - `get_avalonia_expert_rules`：返回一套完整的 Avalonia 开发规则，覆盖 AXAML 语法等
  - `migrate_diagnostics`：分步指导安装或升级到当前的 Avalonia Developer Tools 包
  - `analyze_wpf_project`：WPF 迁移 Avalonia 的入口，扫描项目的目标框架等信息
  - `migrate_to_xpf`：指导用 XPF（drop-in 跨平台方案）迁移 WPF 应用
  - `migrate_to_avalonia`：完整原生 Avalonia 迁移的分阶段 playbook
  - `lookup_wpf_to_avalonia_mapping`：针对单个主题返回聚焦的 WPF→Avalonia 映射
  - 内置 Prompts：`init`（加载开发规则、设置简洁响应行为）、`new`（引导新建项目、选择模板）、`recreate-ui`（依据截图重建 UI，需 Avalonia license 配合 DevTools MCP）
- **安装方式**：
  各编辑器均指向同一远程端点 `https://docs-mcp.avaloniaui.net/mcp`，配置示例（Claude Code）：
  ```
  claude mcp add --transport http avalonia-docs https://docs-mcp.avaloniaui.net/mcp
  ```
  VS Code / Cursor / Windsurf / Gemini CLI / Rider / Visual Studio 均为在各自 MCP 配置文件中写入同一 URL；Claude Desktop 通过 "Customize → Connectors" 界面手动添加自定义连接器。
- **备注**：`analyze_wpf_project`、`migrate_to_xpf`、`migrate_to_avalonia`、`lookup_wpf_to_avalonia_mapping` 四个工具与本仓库 `optimus-avalonia-plugin`（WPF→Avalonia 迁移场景）直接相关，是潜在的补充方案，尚未集成。官方文档未给出更新或卸载命令——远程托管无需本地更新，卸载即在对应编辑器的 MCP 配置文件中删除 `avalonia-docs` 条目。
