# WPF 代码审查门禁 Hook

## 功能说明

拦截 `git commit`（含 `--amend`），当 staged 改动包含 `.xaml` 文件且尚未经过 `wpf-code-review` skill 审查时阻止提交，提示先调用该 skill 完成审查。

## 工作原理

- 门禁基于 **staged `.xaml` 内容的哈希**判定是否"已审查"，不是基于文件名——只要内容变化，哈希变化，标记失效，必须重新走审查
- 标记文件存放在 `.git/optimus-review-marks/wpf.hash`（仓库本地，不会被提交，多仓库互不干扰）
- 若 staged 区没有 `.xaml` 改动，或当前 Bash 命令不含 `git commit`，直接放行，不产生任何感知

## 使用方式

1. 正常修改 `.xaml` 文件、`git add` 后尝试提交
2. 若命中门禁，Claude 会看到阻塞提示，按提示调用 `wpf-code-review` 完成审查、修复问题
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
- Python 3（解析 hook stdin 的 JSON，仅用于判断当前命令是否为 `git commit`）

Codex CLI 无 `PreToolUse` 机制，本门禁仅对 Claude Code 生效。
