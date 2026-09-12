# C# 代码审查门禁 Hook

## 规范依据

⚠️ **改动本目录任何脚本或配置前，先读这一节。**

本 hook 的开发与修改遵从 **`knowledge-base/claude-code-hooks/`**（对 Claude Code 官方 hooks reference 的全量规范化，43 条索引条目）。与本门禁直接相关的条款：

| 条款 | 约束了什么 |
|---|---|
| `rules/01-event-selection.md § 3` | `PreToolUse` 可拦截，拦截以 `exit 2` 的效果为准 |
| `rules/03-output-contract.md § 1` | **策略型 hook 必须 `exit 2`**；`exit 1` 及其他非零码被当成非阻断错误直接放行 |
| `rules/03-output-contract.md § 1 超时` | `PreToolUse` 超时**不阻断**，工具调用继续——卡住的 hook 不能当闸门 |
| `rules/04-decision-control.md § 4` | hook 不是安全边界，故本门禁定位为"诚实门禁"（见下文局限性） |
| `rules/06-security-and-cost.md § 3` | 耗时按进程数估算（本机 Git Bash 单次 fork+exec 约 78ms），本 hook 触发频率为每次 Bash 调用 |
| `rules/06-security-and-cost.md § 5` | Claude 侧 hook 在 Codex 不生效，仓库级门禁应落 `.githooks/` |

排查「hook 没报错但没效果」查 `rules/03 § 8 静默失效清单`。

改动 hook 配置或脚本后，提交前跑 `python .githooks/check_hook_configs.py .`（`pre-commit` 已含该检查），并按 `AGENTS.md` 触发矩阵升本插件两份 `plugin.json`。仓库内的完整约定见 `.claude/rules/hook-conventions.md`（编辑 `plugins/*/hooks/**` 时自动载入）。

## 功能说明

拦截 `git commit`（含 `--amend`），当 staged 改动包含 `.cs` 文件且尚未经过 `csharp-code-review` skill 审查时阻止提交，提示先调用该 skill 完成审查。

## 工作原理

- 门禁基于 **staged `.cs` 内容的哈希**判定是否"已审查"，不是基于文件名——只要内容变化，哈希变化，标记失效，必须重新走审查
- 标记文件存放在 `.git/optimus-review-marks/csharp.hash`（仓库本地，不会被提交，多仓库互不干扰）
- 若 staged 区没有 `.cs` 改动，或当前 Bash 命令不含 `git commit`，直接放行，不产生任何感知

## 使用方式

1. 正常修改 `.cs` 文件、`git add` 后尝试提交
2. 若命中门禁，Claude 会看到阻塞提示，按提示调用 `csharp-code-review` 完成审查、修复问题
3. 审查通过后执行：
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/hooks/pretooluse/review-gate.sh" mark
   ```
4. 重新提交即可放行

## 局限性

这是**诚实门禁**，不是**强制门禁**——它防止的是"无意中漏掉审查步骤"，依赖 Claude 按提示真实调用审查 skill 后才执行 `mark`。它不能防止刻意跳过审查直接执行 `mark` 命令。若需要不可绕过的强制校验，需要走原生 Git `pre-commit` hook（本仓库当前未采用此方案，仅在 Claude Code 会话内生效）。

同理，本门禁只在 Claude Code 会话内通过 Bash 工具执行 `git commit` 时生效；用户在终端直接手动提交、或通过 IDE/CI 提交，不受此门禁约束。

## 依赖

- Git（`git diff --cached`）
- `sha256sum`（Git for Windows 自带的 Git Bash 环境已包含）

判断当前命令是否为 `git commit` 用纯 bash 正则在 hook 输入上匹配，**不起解释器**——Git Bash 自带环境没有 `python3`，解析失败会让门禁静默放行；且这里每次 Bash 调用都要付一次进程开销。

Codex CLI 无 `PreToolUse` 机制，本门禁仅对 Claude Code 生效。
