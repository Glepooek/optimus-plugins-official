# 06 安全与成本

> hook 以完整用户权限执行任意命令，且每次触发都是一次真实的进程开销。两者都需要在配置前而非事后评估。

`enforcement`：§ 2 的五条编写实践、§ 4 的 PowerShell 占位符写法可机械校验或 review 拦截，标 `ci` / `review`；§ 3 的成本估算是判断依据，标 `advisory`。

## 1. workspace trust：两种会话的规则不同

Claude Code 在运行任何设置文件里的 hook 前检查 workspace trust，**但两种会话类型的结果相反**：

| 会话类型 | 行为 |
|---|---|
| 交互式 | 扣住**全部**设置文件的 hook（含你自己的 `~/.claude/settings.json`），直到你接受该目录或其父目录的 workspace trust 对话框 |
| `-p` 或 SDK | **从不显示对话框，直接视该目录为可信**——仓库 `.claude/settings.json` 里提交的 hook 会在你从未信任过的目录下运行 |

由此得出一条硬规则：

> **对不是自己写的仓库跑 `claude -p` 之前，必须先审查它的 `.claude/` 设置文件**；或用 `--bare` 启动，或用 `--settings '{"disableAllHooks": true}'` 关掉这一次运行的全部 hook。

两类 frontmatter hook 的规则不同，不要混淆：

- **project skill 的 frontmatter hook** 跟设置文件同规则——`-p` 运行时在未信任目录下也会注册。
- **project subagent 的 frontmatter hook** 更严：只有接受了该 agent 文件所在目录的 workspace trust 才运行，`-p` 会话不算接受。

企业侧另有 `allowManagedHooksOnly`：开启后你的 user / project / local / 插件 hook 全部被阻止（managed settings `enabledPlugins` 里强制启用的插件除外）。

## 2. 编写实践

- **必须校验与净化输入**：hook 输入来自会话，不要无条件信任。
- **必须给 shell 变量加引号**：用 `"$VAR"` 而非 `$VAR`。
- **必须阻断路径穿越**：检查文件路径中的 `..`。
- **必须用绝对路径**：exec form 下用 `${CLAUDE_PROJECT_DIR}` 且无需引号；shell form 下必须包双引号。
- **应该跳过敏感文件**：`.env`、`.git/`、密钥等。

`additionalContext` 有一个额外的注入面：**写成带外系统指令措辞的文本会触发 Claude 的 prompt-injection 防御**，结果是它把文本转呈给用户而不是当上下文使用——功能上等于失效。必须写成事实陈述，见 `rules/03 § additionalContext`。

## 3. 进程成本

hook 的耗时按**它启动多少个进程**估算，不按脚本行数。

本机实测基线（Windows + Git Bash，`optimus-plugins-official` 仓）：

- **Git Bash 单次 fork+exec 约 78ms。** POSIX 风格脚本在 Windows 上被这个常数放大数十倍——一个「只有几十行」的 bash 脚本若内部调用十几次外部命令，实际耗时是秒级。
- 一个 `bash` 包一个 `python` 的两进程脚本约 0.44s，其中 python 解释器启动占大头。
- 四个同步 `SessionStart` hook 串行曾实测阻塞约 13s。

由此三条：

- **`SessionStart` 与每次工具调用触发的事件上，优化方向是减少进程数**，不是精简脚本行数。合并多次外部命令调用、用单个解释器进程完成全部逻辑，比删代码有效。
- **Windows 上应该避免 POSIX 风格的多进程管道**（`cat | grep | awk` 之类）。同样逻辑用一次 python / PowerShell 调用完成。
- **禁止用改 `async` 来掩盖同步成本**——见 `rules/05 § 5`。对必须同步的 hook，成本只能靠减少工作量降低。

各事件的触发频率见 `rules/01 § cadence`。`SessionEnd` 的 1.5 秒共享预算是硬上限，不要在那里放任何需要起解释器的工作。

## 4. PowerShell 占位符

Windows 上给 command hook 设 `"shell": "powershell"` 可用 PowerShell 运行（自动探测 `pwsh.exe`，回退 `powershell.exe`）。占位符有三种写法，**其中一种是错的**：

| 写法 | 结果 |
|---|---|
| `${CLAUDE_PROJECT_DIR}` | ✅ v2.1.198+ 会被重写为 PowerShell 的 `${env:NAME}` 形式 |
| `$env:CLAUDE_PROJECT_DIR` | ✅ 全版本可用 |
| `$CLAUDE_PROJECT_DIR` | ❌ **PowerShell 解析成未定义局部变量并解析为 `$null`**，脚本路径丢掉项目根前缀。Claude Code 不重写这种形式，只在 debug log 记警告 |

两条附加约束：

- 占位符重写后由 PowerShell 在解析后从导出环境取值，因此**在双引号字符串内有效，在单引号字符串内无效**——单引号里 PowerShell 从不展开变量。
- v2.1.198 之前该重写只对插件 hook 生效。要兼容旧版本，用 `$env:` 形式或 exec form。

跨版本最稳的写法是 `$env:` 形式：

```json
{
  "type": "command",
  "shell": "powershell",
  "command": "& \"$env:CLAUDE_PROJECT_DIR\\.claude\\hooks\\check.ps1\""
}
```

## 5. 双 harness 下的定位

**本领域全部条款不适用于 Codex。** 本仓为双 harness，但 Claude 侧 hooks 在 Codex 中不生效。因此：

- **禁止把仓库级一致性门禁只写在 hook 里**。Codex 侧走标准 git 流程读不到 Claude 的 hook 配置，写在那里的检查在 Codex 下完全不生效。仓库级门禁应落在 `.githooks/`（git 原生钩子，两侧同等生效）。
- 这条区分与 `git` 领域的边界一致：`git.02.commit-hooks`「提交前 hook 不得绕过」讲的是 git 原生钩子，与本领域无重叠。
