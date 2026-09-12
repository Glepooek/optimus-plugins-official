---
paths:
  - "plugins/*/hooks/**"
---

> **本仓库全部 Claude Code hook 的开发、修改、评审，一律以 `knowledge-base/claude-code-hooks/` 为规范依据。** 该领域已对官方 hooks reference 做全量规范化（43 条索引条目），不要凭记忆或类比推导 hook 行为——先按下表定位到对应规则文件，用 `index.jsonl` 的 `file` + `anchor` 读原文。本篇只承载**本仓库专属约定**。

## 规范依据映射

| 你要做的事 | 查哪一份 |
|---|---|
| 选哪个事件、能不能拦截、cadence 多高 | `rules/01-event-selection.md` |
| 写在哪个文件、matcher 怎么求值、`if` / exec form / 路径占位符 | `rules/02-configuration.md` |
| exit code、stdout JSON、`systemMessage` 交付去向、超时 | `rules/03-output-contract.md` |
| 拦截 / 改写 / 放行的决策字段 | `rules/04-decision-control.md` |
| `async` / `asyncRewake` | `rules/05-async-execution.md` |
| workspace trust、编写实践、进程成本、PowerShell 占位符 | `rules/06-security-and-cost.md` |
| 34 个事件 × 6 个维度的能力对照 | `reference/event-capability-matrix.md` |

**排查「hook 没报错但没效果」直接查 `rules/03 § 8 静默失效清单`**——15 种形态按排查顺序列全，每行给出判据出处。

## 本仓专属约定

**改 `plugins/*/hooks/` 内任何脚本或配置，必须同步升该插件的两份 `plugin.json`**（`.claude-plugin/` 与 `.codex-plugin/` 同值），幅度判定见 `AGENTS.md` 的触发矩阵。`hooks/README.md` 也在此目录内，改它一样要升版。

**提交前必须跑机械自检**，它是 `.githooks/pre-commit` 的第 2 项检查，也可单独执行：

```bash
python .githooks/check_hook_configs.py .
python -m unittest discover -s .githooks -p "test_*.py"   # 18 个自检用例
```

⚠️ **该脚本只覆盖 7 项可机械判定的约束**（未知事件名、不支持 matcher 的事件却配了 matcher、`async` 配在需要用户可见输出的事件上、handler 类型与事件不匹配、mcp 工具名缺 `.*` 等），**不能替代按上表逐条人工核对**。它对定位不到引用脚本的情况刻意不报——宁可漏报也不误报。

**Claude 侧 hook 在 Codex 中完全不生效**（`rules/06 § 5`）。由此两条：

- 面向本仓库自身的一致性门禁**禁止**只写在 `plugins/*/hooks/` 里，必须落在 `.githooks/`（git 原生钩子，两个 harness 同等生效）。
- 插件对外发布的 hook 若承载功能承诺，`hooks/README.md` 必须写明它仅在 Claude Code 下生效。

## 本仓已登记的 hook 配置

| 位置 | 事件 | 用途 |
|---|---|---|
| `plugins/optimus-backend-plugin/hooks/hooks.json` | `PreToolUse`（matcher `Bash`） | staged `.cs` 未经 `csharp-code-review` 时拦 `git commit` |
| `plugins/optimus-frontend-plugin/hooks/hooks.json` | `PreToolUse`（matcher `Bash`） | staged `.xaml` 未经 `wpf-code-review` 时拦 `git commit` |
| `plugins/optimus-devops-plugin/hooks/hooks.json` | `SessionStart` | 技巧轮播（**必须同步**，`async` 会让 `systemMessage` 只交付给 Claude） |
| `plugins/optimus-devops-plugin/hooks/hooks.json` | `Notification`（matcher `permission_prompt`） | Windows toast 通知（`async: true` 刻意保留，纯副作用且该事件本就丢弃 `systemMessage`） |

新增 hook 配置后，`check_hook_configs.py` 会自动扫到（它 glob `plugins/*/hooks/hooks.json` 与 `.claude/settings*.json`），无需注册；但上表要手工补一行。
