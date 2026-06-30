# 插件详情

## unipus-frontend-plugin — 前端开发工具集

**Skills:**
- `unipus-fe-dev` — 前端全流程开发（唯一复合 Skill，5阶段：需求收集→分析规划→代码生成→交付物生成→验证完成）
- `unipus-design-ui` — UI 设计规范管理
- `wpf-xaml-performance` — WPF XAML 性能优化

**特色:** 复合 Skill 采用 Subagent 驱动并行生成，详见 ARCHITECTURE.md。

---

## unipus-backend-plugin — 后端开发工具集

**Skills:**
- `unipus-backend-dev` — 后端开发（架构设计、API开发）
- `unipus-backend-api-connect` — API 连接和文档生成
- `csharp-code-review` — C# 代码审查

**辅助脚本:** fetch_swagger.py、fetch_feishu_doc.py、fetch_webpage_api.py

---

## unipus-qa-plugin — 测试 QA 工具集

**Skills（7个，最多的插件）:**
- `unipus-qa-test-design` — 测试用例设计
- `unipus-qa-test-report` — 测试报告生成
- `unipus-qa-jmeter-scripts` — JMeter 性能测试脚本
- `unipus-qa-ui-scripts` — UI 自动化测试脚本
- `unipus-qa-ui-consistency-check` — UI 一致性检查
- `unipus-qa-feishu-project-sync` — 飞书测试项目同步
- `unipus-qa-feishu-project-xmind` — 飞书项目转 XMind（含 converter.py）

---

## unipus-prd-plugin — PRD 管理工具集

**Skills:**
- `unipus-prd-create` — PRD 文档创建
- `unipus-prd-optimize` — PRD 文档优化
- `unipus-prd-review` — PRD 文档审查

---

## unipus-feishu-plugin — 飞书集成工具集

**Skills:**
- `unipus-feishu-read-write` — 飞书文档读写
- `unipus-feishu-upload-doc` — 飞书文档上传
- `unipus-feishu-doc-load` — 飞书文档加载

---

## unipus-office-plugin — Office 文档处理工具集

**Skills（7个）:**
- `docx-writer` — Word 文档生成（含模板和脚本）
- `unipus-office-docx` — Office DOCX 处理
- `xlsx-editor` — Excel 编辑和报表
- `pptx-editor` — PowerPoint 演示文稿
- `pdf-creator` — PDF 文档生成
- `file-to-markdown` — 本地文件转 Markdown
- `web-to-markdown` — 网页内容抓取转 Markdown

---

## unipus-devops-plugin — DevOps 工具集

**Skills（5个）:**
- `jenkins-build` — Jenkins CI/CD 构建触发
- `weekly-report` — 工作周报转写（四段式标准格式）
- `sync-agent-skills` — Agent Skills 同步
- `unipus-project-analyze` — 项目结构分析
- `unipus-infra-init-app` — 应用初始化脚手架

**Hooks（内置自动加载）:**
- `SessionStart` — 会话启动展示技巧（425条智能轮播，带进度追踪）
- `Notification` — Windows 权限提示通知

**关键文件:**
- `hooks/hooks.json` — Hook 配置
- `hooks/sessionstart/tips.txt` — 425条技巧库
- `hooks/sessionstart/show-tip.sh` — 轮播脚本
- `hooks/notification/permission-notify.ps1` — 通知脚本

---

## unipus-mcp-servers — MCP 服务器集成

**无 Skills，仅 MCP 配置（.mcp.json）:**

| 服务名 | 连接方式 | 认证 |
|--------|----------|------|
| GitHub Copilot | HTTP (api.githubcopilot.com) | GITHUB_TOKEN |
| MasterGo Magic | stdio (npx @mastergo/magic-mcp) | MASTERGO_TOKEN |
| Feishu Project | stdio (npx @lark-project/mcp) | FEISHU_PROJECT_TOKEN |

---

## 项目级 Skills（.claude/skills/，不进 marketplace）

- `commit-cc-plugin` — 提交发布工作流（强制使用，替代手动 git）
- `sync-cc-tips` — tips.txt 自动同步（从 Claude Code changelog 同步技巧）
