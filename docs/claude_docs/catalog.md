# Claude Code 官方文档站点结构（code.claude.com/docs/en）

> 通过 Playwright 实测抓取站点侧边栏得到的真实层级（而非 `llms.txt` 的扁平列表）。站点采用 **8 个顶级 Tab**，每个 Tab 下再分若干分组（H3），分组内是具体页面。用于指导有道云笔记的文件夹分类与翻译进度追踪。

抓取方式：逐个导航到每个 Tab 的入口 URL，从 `#sidebar` 提取 `h3` 分组标题及其下 `<a>` 链接；手风琴式折叠的子分组（图标为按钮而非直接链接）需先点击展开才会渲染到 DOM。

标记说明：`[x]` 已翻译并保存到有道云笔记；`[ ]` 未处理；`⚠️` 表示该分组仅部分展开验证，可能有遗漏子项。

---

## Tab 1 — Getting started（入口：`/overview`）

### Getting started
- [ ] Overview — `/overview`
- [ ] Quickstart — `/quickstart`
- [ ] Changelog — `/changelog`

### Core concepts
- [ ] How Claude Code works — `/how-claude-code-works`
- [ ] Extend Claude Code — `/features-overview`
- [ ] Explore the .claude directory — `/claude-directory`
- [ ] Explore the context window — `/context-window`
- [ ] Prompt caching — `/prompt-caching`

### Use Claude Code
- [ ] Store instructions and memories — `/memory`
- [ ] Permission modes — `/permission-modes`
- [ ] Manage sessions — `/sessions`
- [ ] Common workflows — `/common-workflows`
- [ ] Prompt library — `/prompt-library`
- [ ] Best practices — `/best-practices`

### Platforms and integrations
- [ ] Overview — `/platforms`
- [ ] Remote Control — `/remote-control`
- [ ] Claude Code on the web ⚠️ — Get started(`/web-quickstart`)，另有 Configuration(`/claude-code-on-the-web`) 等页面推测同属此子分组
- [ ] Claude Code on desktop ⚠️ — Get started(`/desktop-quickstart`)，另有 Desktop application(`/desktop`)、Claude Desktop on Linux(`/desktop-linux`) 等页面推测同属此子分组
- [ ] Chrome extension — `/chrome`
- [ ] Computer use (preview) — `/computer-use`
- [ ] Visual Studio Code — `/vs-code`
- [ ] JetBrains IDEs — `/jetbrains`
- [ ] Code review & CI/CD ⚠️ — Security guidance plugin(`/security-guidance`)，另有 Code Review(`/code-review`)、GitHub Actions(`/github-actions`)、GitHub Enterprise Server(`/github-enterprise-server`)、GitLab CI/CD(`/gitlab-ci-cd`) 推测同属此子分组
- [ ] Claude Code in Slack — `/slack`

---

## Tab 2 — Build with Claude Code（对应有道笔记"使用ClaudeCode构建"，入口：`/agents`）

### Agents and parallel work
- [ ] Overview — `/agents`
- [ ] Create custom subagents — `/sub-agents`
- [ ] Agent view — `/agent-view`
- [ ] Run agent teams — `/agent-teams`
- [ ] Dynamic workflows — `/workflows`
- [ ] Isolate sessions with worktrees — `/worktrees`

### MCP
- [ ] Quickstart — `/mcp-quickstart`
- [ ] Reference — `/mcp`

### Skills
- [ ] Extend Claude with skills — `/skills`

### Plugins
- [ ] Discover and install prebuilt plugins — `/discover-plugins`
- [ ] Create plugins — `/plugins`

### Artifacts
- [ ] Share session output as artifacts — `/artifacts`

### Automation
- [x] Automate with hooks — `/hooks-guide`
- [ ] Push external events to Claude — `/channels`
- [x] Run prompts on a schedule — `/scheduled-tasks`（已存：scheduled-tasks.md）
- [x] Goals — `/goal`（已存：goal.md）
- [x] Programmatic usage — `/headless`（已存：run-claude-code-programmatically.md）
- [x] Launch sessions from links — `/deep-links`（已存：deep-links.md）

### Guides
- [x] Monorepos and large repos — `/large-codebases`（已存：large-codebases.md）

### Troubleshooting
- [ ] Troubleshoot installation and login — `/troubleshoot-install`
- [ ] Troubleshoot performance and stability — `/troubleshooting`
- [ ] Debug configuration — `/debug-your-config`
- [ ] Error reference — `/errors`

---

## Tab 3 — Administration（对应有道笔记"管理"，入口：`/admin-setup`）

### Setup and access
- [ ] Administration overview — `/admin-setup`
- [ ] Advanced setup — `/setup`
- [ ] Authentication — `/authentication`
- [ ] Server-managed settings — `/server-managed-settings`
- [ ] Managed MCP configuration — `/managed-mcp`
- [ ] Auto mode — `/auto-mode-config`

### Deployment
- [ ] Overview — `/third-party-integrations`
- [ ] Feature availability — `/feature-availability`
- [ ] Amazon Bedrock — `/amazon-bedrock`
- [ ] Claude Platform on AWS — `/claude-platform-on-aws`
- [ ] Google Cloud's Agent Platform — `/google-vertex-ai`
- [ ] Microsoft Foundry — `/microsoft-foundry`
- [ ] Network configuration — `/network-config`
- [ ] Development containers — `/devcontainer`

### Gateways
- [ ] Overview — `/gateways`
- [ ] Claude apps gateway（子分组）
  - [ ] Configuration — `/claude-apps-gateway-config`
  - [ ] Spend limits — `/claude-apps-gateway-spend-limits`
  - [ ] Deployment — `/claude-apps-gateway-deploy`
  - [ ] Deployment example — `/claude-apps-gateway-on-gcp`
  - [ ] （概览页推测）`/claude-apps-gateway`
- [ ] Other gateways（子分组）
  - [ ] Connect to a gateway — `/llm-gateway-connect`
  - [ ] Organization rollout — `/llm-gateway-rollout`
  - [ ] Protocol reference — `/llm-gateway-protocol`
  - [ ] （概览页推测）`/llm-gateway`

### Usage and costs
- [ ] Monitoring — `/monitoring-usage`
- [ ] Costs — `/costs`
- [ ] Track team usage with analytics — `/analytics`

### Plugin distribution（当前处理中，对应有道笔记"管理 / 插件分发"）
- [ ] Create and distribute a plugin marketplace — `/plugin-marketplaces`
- [ ] Plugin dependency versions — `/plugin-dependencies`
- [ ] Recommend your plugin from your CLI — `/plugin-hints`
- [ ] Recommend plugins for your org — `/plugin-relevance`

### Security and data
- [ ] Security — `/security`
- [ ] Data usage — `/data-usage`
- [ ] Zero data retention — `/zero-data-retention`

### Adoption
- [ ] Communications kit — `/communications-kit`
- [ ] Champion kit — `/champion-kit`

---

## Tab 4 — Configuration（入口：`/settings`）

### Settings and permissions
- [ ] Settings — `/settings`
- [ ] Permissions — `/permissions`
- [ ] Sandbox environments — `/sandbox-environments`
- [ ] Bash sandbox — `/sandboxing`

### Model and responses
- [ ] Model configuration — `/model-config`
- [ ] Speed up responses with fast mode — `/fast-mode`
- [ ] Escalate hard decisions with the advisor tool — `/advisor`
- [ ] Output styles — `/output-styles`

### Interface
- [ ] Terminal configuration — `/terminal-config`
- [ ] Fullscreen rendering — `/fullscreen`
- [ ] Voice dictation — `/voice-dictation`
- [ ] Customize status line — `/statusline`
- [ ] Customize keyboard shortcuts — `/keybindings`

---

## Tab 5 — Reference（入口：`/cli-reference`）

### Reference
- [ ] CLI reference — `/cli-reference`
- [ ] Commands — `/commands`
- [ ] Environment variables — `/env-vars`
- [ ] Tools reference — `/tools-reference`
- [ ] Interactive mode — `/interactive-mode`
- [ ] Checkpointing — `/checkpointing`
- [ ] Hooks reference — `/hooks`
- [ ] Plugins reference — `/plugins-reference`
- [ ] Channels reference — `/channels-reference`

### Glossary
- [ ] Glossary — `/glossary`

---

## Tab 6 — Agent SDK（入口：`/agent-sdk/overview`）

### Agent SDK
- [ ] Overview — `/agent-sdk/overview`
- [ ] Quickstart — `/agent-sdk/quickstart`

### Core concepts
- [ ] How the agent loop works — `/agent-sdk/agent-loop`
- [ ] Use Claude Code features — `/agent-sdk/claude-code-features`
- [ ] Work with sessions — `/agent-sdk/sessions`
- [ ] Persist sessions to external storage — `/agent-sdk/session-storage`

### Input and output
- [ ] Streaming Input — `/agent-sdk/streaming-vs-single-mode`
- [ ] Handle approvals and user input — `/agent-sdk/user-input`
- [ ] Stream responses in real-time — `/agent-sdk/streaming-output`
- [ ] Get structured output from agents — `/agent-sdk/structured-outputs`

### Extend with tools
- [ ] Give Claude custom tools — `/agent-sdk/custom-tools`
- [ ] Connect to external tools with MCP — `/agent-sdk/mcp`
- [ ] Scale to many tools with tool search — `/agent-sdk/tool-search`
- [ ] Subagents in the SDK — `/agent-sdk/subagents`

### Customize behavior
- [ ] Modifying system prompts — `/agent-sdk/modifying-system-prompts`
- [ ] Slash Commands in the SDK — `/agent-sdk/slash-commands`
- [ ] Agent Skills in the SDK — `/agent-sdk/skills`
- [ ] Plugins in the SDK — `/agent-sdk/plugins`

### Control and observability
- [ ] Configure permissions — `/agent-sdk/permissions`
- [ ] Intercept and control agent behavior with hooks — `/agent-sdk/hooks`
- [ ] Rewind file changes with checkpointing — `/agent-sdk/file-checkpointing`
- [ ] Track cost and usage — `/agent-sdk/cost-tracking`
- [ ] Observability with OpenTelemetry — `/agent-sdk/observability`
- [ ] Todo Lists — `/agent-sdk/todo-tracking`

### Deployment
- [ ] Hosting the Agent SDK — `/agent-sdk/hosting`
- [ ] Securely deploying AI agents — `/agent-sdk/secure-deployment`

### SDK references
- [ ] TypeScript SDK — `/agent-sdk/typescript`
- [ ] TypeScript V2 (removed) — `/agent-sdk/typescript-v2-preview`
- [ ] Python SDK — `/agent-sdk/python`
- [ ] Migration Guide — `/agent-sdk/migration-guide`

---

## Tab 7 — What's New（入口：`/whats-new`）

### What's New
- [ ] What's new（索引页）— `/whats-new`
- [ ] Week 26 · June 22–26 — `/whats-new/2026-w26`
- [ ] Week 25 · June 15–19 — `/whats-new/2026-w25`
- [ ] Week 24 · June 8–12 — `/whats-new/2026-w24`
- [ ] Week 23 · June 1–5 — `/whats-new/2026-w23`
- [ ] Week 22 · May 25–29 — `/whats-new/2026-w22`
- [ ] Week 21 · May 18–22 — `/whats-new/2026-w21`
- [ ] Week 20 · May 11–15 — `/whats-new/2026-w20`
- [ ] Week 19 · May 4–8 — `/whats-new/2026-w19`
- [ ] Week 18 · Apr 27 – May 1 — `/whats-new/2026-w18`
- [ ] Week 17 · Apr 20–24 — `/whats-new/2026-w17`
- [ ] Week 16 · Apr 13–17 — `/whats-new/2026-w16`
- [ ] Week 15 · Apr 6–10 — `/whats-new/2026-w15`
- [ ] Week 14 · Mar 30 – Apr 3 — `/whats-new/2026-w14`
- [ ] Week 13 · Mar 23–27 — `/whats-new/2026-w13`

---

## Tab 8 — Resources（入口：`/legal-and-compliance`）

### Resources
- [ ] Legal and compliance — `/legal-and-compliance`

> ⚠️ 该 Tab 侧边栏只抓到 1 个链接，明显少于预期（`llms.txt` 中同类页面如 `glossary.md` 已归入 Reference Tab）。可能此 Tab 确实只有这一篇，也可能有未展开的折叠分组，未来处理到这里时建议重新用 Playwright 核实。

---

## 已知缺口 / 待核实项

1. **三个手风琴子分组仅部分展开验证**（标记 ⚠️）：Tab1 的"Claude Code on the web"、"Claude Code on desktop"、"Code review & CI/CD"；Tab3 的"Claude apps gateway"、"Other gateways"。原因：折叠分组用 React 状态渲染，子项在点击展开前不存在于 DOM 中；点击展开后，提取脚本用 `li.querySelector('a')` 只拿到了子列表中的第一个链接，未能正确取出该 `<li>` 下的完整子链接集合。后续如需精确核对，应改用 `li.querySelectorAll('ul a')` 取全部子项。
2. **总数核对**：本次共提取约 150 个页面链接，`llms.txt` 列出 163 个页面（外加 Documentation Index 本身不计入）。差值可能来自：(a) 上述未完全展开的子分组遗漏的页面；(b) Resources Tab 可能存在未发现的折叠分组；(c) 少数页面在多个 Tab/分组间重复出现（如各 Tab 入口的 "Overview" 页面）被去重统计。
3. **抓取方法**：直接 `curl` 探测 `docs.json`/`mint.json` 等 Mintlify 常见配置文件返回 302（重定向到首页，非真实命中），页面也未内嵌 `__NEXT_DATA__`，因此该表格是通过 Playwright 实际点击 8 个 Tab 入口 URL + 展开可见折叠按钮后提取得到，不是从静态配置文件解析。
