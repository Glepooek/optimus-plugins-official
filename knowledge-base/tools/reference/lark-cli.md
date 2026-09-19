# lark-cli (Lark/Feishu CLI)

- **网址**：https://github.com/larksuite/cli
- **简介**：Lark/Feishu 官方命令行工具，由 larksuite 团队维护，专为人类与 AI Agent 设计，覆盖日历、IM消息、文档、云盘、多维表格、电子表格、幻灯片、任务、知识库、通讯录、邮件、会议纪要、审批、OKR 等 18 个业务域，200+ 精选命令。
- **开发语言**：Go
- **核心能力**：
  - Agent-Native 设计：24 个开箱即用的结构化 Skills，兼容主流 AI 工具，Agent 零配置即可操作 Lark/Feishu
  - 三层命令体系：Shortcuts（`+`前缀，人类和AI友好，含 dry-run 预览）→ API Commands（自动生成，1:1 映射平台端点，100+ 命令）→ Raw API（直调任意端点，覆盖 2500+ API）
  - JSON 输出契约明确：success/error 信封区分（用 `ok` 字段判定成功与否，而非 `code==0`），支持 json/pretty/table/ndjson/csv 多种输出格式
  - 安全可控：输入注入防护、终端输出脱敏、OS 原生 keychain 凭证存储
  - 支持身份切换（`--as user/bot`）、自动分页（`--page-all`）、schema 自省（`lark-cli schema`）等高级用法
- **安装方式**：
  - 推荐（npm）：`npx @larksuite/cli@latest install`
  - 从源码构建：需要 Go v1.23+ 和 Python 3，`git clone` 后 `make install`
  - 配置与登录：`lark-cli config init` → `lark-cli auth login --recommend`
- **更新方式**：重新执行 `npx @larksuite/cli@latest install`（README 未单独给出更新命令，安装命令本身用的是 `@latest` tag，重新执行即会覆盖为最新版本）
- **备注**：⚠️ 官方 README 专设"Security & Risk Warnings"章节明确提示：该工具可被 AI Agent 调用以自动化操作 Lark/Feishu 开放平台，存在模型幻觉、不可预测执行、prompt injection 等固有风险；授权后 Agent 将以用户身份在授权范围内操作，可能导致敏感数据泄露或未授权操作，官方建议不要主动放宽默认安全设置。与本仓库 `optimus-feishu-plugin`（飞书文档读写、上传、自动化）属相关领域，是潜在的补充/替代方案，尚未集成。MIT 许可，GitHub 15.5k star，最新版本 v1.0.68（2026-07-09）。
