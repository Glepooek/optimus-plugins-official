# relevance 信号对照表

本文件是 `rules/07-suggestion-protocols.md § 2. relevance：本地匹配 + 管理员开关` 的取证出处：五种 `signals` 逐项对照匹配对象、路径规范化、大小写敏感性、数量与长度上限。规范条款与判断依据在 `rules/07`，本文件只承载对照数据。

数据取自官方 [Plugin relevance](https://code.claude.com/docs/zh-CN/plugin-relevance) 2026-09-12 版本。

## 1. 五种信号总表

| 信号 | 类型 | 匹配对象 |
|---|---|---|
| `cwd` | 字符串数组 | 会话工作目录（glob 模式） |
| `cli` | 字符串数组 | 本会话 shell 命令中的命令名 |
| `hosts` | 字符串数组 | 本会话 Bash 命令中 `http://` / `https://` URL 里出现的主机名 |
| `filesRead` | 字符串数组 | 本会话记录的文件路径（glob 模式） |
| `manifestDeps` | 对象数组 | 本会话读过的包清单中声明的依赖 |

`signals` 必填，**至少一个信号插件才可被建议**。

## 2. 上限、规范化与大小写

| 信号 | 数量上限 | 每条长度 | 路径/分隔符规范化 | 大小写 | 匹配方式 |
|---|---|---|---|---|---|
| `cwd` | 10 个模式 | 256 字符 | **正斜杠规范化** | **不敏感** | glob |
| `cli` | 10 条 | 64 字符 | — | — | **精确匹配** |
| `hosts` | 20 条 | 128 字符 | — | **不敏感** | 精确匹配 |
| `filesRead` | 10 个模式 | 256 字符 | **正斜杠规范化** | **不敏感** | glob |
| `manifestDeps` | 10 条 | `file` 与 `pattern` 各 256 字符 | ⚠️ **不规范化**——Windows 路径用反斜杠 | `file` 不敏感、**`pattern` 敏感** | 两者均为 JavaScript `RegExp` 源字符串 |

## 3. 各信号的形态要求

**`cwd`**：作为**绝对路径**匹配；在 git 仓库内时**同时**作为相对仓库根的路径匹配。每个模式匹配目录本身及其下全部内容，所以 `infra`、`infra/`、`infra/**` 行为相同。**唯一能在会话启动（第一轮之前）匹配的信号。**

**`cli`**：跨平台一致——Windows 上经 PowerShell 或 Git Bash 运行的命令记录方式相同。Claude Code **每次 shell 工具调用只记录一个命令名**：去掉前导环境变量赋值与 `sudo` 后的第一个 token；复合命令只贡献前导命令（`cd infra && terraform plan` 记录 `cd`）。

**`hosts`**：⚠️ **只接受裸小写主机名——不含方案、端口或路径**。`claude plugin validate` 会拒绝含这三者的条目。

**`filesRead` 与 `manifestDeps`**：测的是**会话记录的文件状态**，比「读过」更宽——还包含 Claude 写过或编辑过的文件，以及自动加载的 `CLAUDE.md` 记忆文件。

## 4. manifestDeps 的两个字段与锚定陷阱

| 字段 | 匹配什么 |
|---|---|
| `file` | 清单文件路径的正则（按会话状态记录的形态，**通常是绝对路径**） |
| `pattern` | 该文件**内容**的正则 |

⚠️ **`file` 必须在末尾锚定。起始锚定的模式永不匹配绝对路径**——这是本信号最容易写错、且错了只表现为「静默不匹配」的一处。JSON 转义形态：

```json
{
  "manifestDeps": [
    { "file": "[/\\\\]package\\.json$", "pattern": "\"stripe\"\\s*:" }
  ]
}
```

三处写法要点：`[/\\\\]` 同时匹配正斜杠与反斜杠分隔符；`\\.` 让点成为字面量；**JSON 里正则的每个反斜杠都写两次**。

⚠️ **大于 512 KB 的清单文件被跳过**，所以 monorepo 根上的巨型 `package.json` 可能永远不触发匹配。

## 5. 静默失效的四种成因汇总

以下四条都表现为「配了却不出建议」，且都不报错：

| 成因 | 出处 |
|---|---|
| 管理员未把该 marketplace 加入 `pluginSuggestionMarketplaces` | `rules/07-suggestion-protocols.md § 2.3 托管设置里的两个条件` |
| 信号名拼错——`relevance` 与 `signals` 下的未知字段被忽略 | 同上 § 2.2；唯一检出手段是 `claude plugin validate` |
| `cli` 想匹配复合命令里的非前导命令 | 本文件 § 3 |
| `manifestDeps` 的 `file` 未在末尾锚定 | 本文件 § 4 |
