# 07 两套安装推荐协议

> CLI 侧的 `<claude-code-hint />` 标记协议与 marketplace 侧的 `relevance` 信号：各自的生效前提、频率上限、以及永远不会触发的场景。

`enforcement`：§ 1 的标记三个必填属性与「独占一行」、§ 2 的 `topic` 长度与 `hosts` 形态可由格式检查或 `claude plugin validate` 机械判定，标 `ci`；「在哪些代码路径发标记」「选哪些信号」属选型判断，标 `review`。

两套协议的适用者不同，不要混用：**CLI hint 面向「维护 CLI/SDK 且在官方 marketplace 有插件」的一方**；**`relevance` 面向「为组织运营 marketplace」的一方**。两者的共同点只有一条：**Claude Code 永不自动安装插件，始终需要用户确认。**

## 1. CLI hint：一行标记换一次安装提示

CLI 检测到自己运行在 Claude Code 内时，向 stderr 写一行自闭合标记；Claude Code 读到后**把它从输出中删掉**，并向用户显示一次性安装提示。该协议不需要额外命令，也不改变 CLI 对 Claude Code 之外用户打印的内容。

```text
<claude-code-hint v="1" type="plugin" value="example-cli@claude-plugins-official" />
```

三个属性**全部必填**：

| 属性 | 说明 |
|---|---|
| `v` | 协议版本，**`1` 是唯一支持的值** |
| `type` | 提示类型，**`plugin` 是唯一支持的值** |
| `value` | `name@marketplace` 形式的插件标识符 |

属性值可加双引号也可不加；**不加引号的值不得含空格**；**不支持转义序列**。

**Claude Code 强制的两个条件，任一不过即丢弃该标记**：

1. **标记必须独占一行。** 嵌在行中间的（例如塞在日志语句里）被忽略。行前后可以有空白
2. ⚠️ **`value` 必须指向 Anthropic 控制的官方 marketplace 中的插件**（如 `claude-plugins-official`）。**指向其他 marketplace 的提示被静默丢弃**

⚠️ **提示行总是在到达模型之前被删除**，即使版本或类型无法识别——所以标记**永远不计入 token 消耗**，也因此在每次调用都发标记没有坏处。

**门控与写入流是推荐而非强制**（Claude Code 无法观察 CLI 是否遵循）：

- **应该**写 stderr——能让标记留在 shell 管道之外（如 `example-cli deploy | jq`）。Claude Code 两个流都扫，stdout 也能工作
- **应该**在环境变量上门控。两个变量的取舍是本节唯一真正的选型判断：

| 变量 | 覆盖面 | 泄漏到人类终端的风险 |
|---|---|---|
| `CLAUDECODE` | 每个 Claude Code 版本都设，触达最多会话 | **较高**：tmux 会话、Claude Code 启动的 stdio MCP server 子进程中也设置，IDE 扩展在其集成终端中设置它——人类可能在那里直接跑你的 CLI |
| `CLAUDE_CODE_CHILD_SESSION` | 仅 Claude Code 自己生成的子进程（工具调用、hook 命令、状态行命令）。需 v2.1.172+ | **较低**，但不为零：会话内启动的长期进程（如 tmux server）会捕获该变量，从它启动的后续 shell 仍会看到原始标记 |

**只有 Bash 与 PowerShell 工具的输出会触发安装提示**；**hook 命令里的提示标记会被剥离并忽略**。

好的发出时机：`--help` 输出（Claude 探索不熟悉的 CLI 时经常跑它）、未知子命令错误（Claude 对你的界面感到困惑的时刻）、登录或鉴权成功、首次运行欢迎消息。

⚠️ **频率上限与永不显示的场景**——设计集成时必须计入，否则会误判「协议没生效」：

| 限制 | 语义 |
|---|---|
| **每个插件一次** | 提示显示过后就记录该插件，**不论用户答什么**，永不再提示该插件 |
| **每个会话一次** | 机器上所有 CLI 加起来，每个 Claude Code 会话最多出现一个提示 |
| **仅主交互会话** | **subagent 运行的命令永不提示**；`-p` 非交互模式与 Agent SDK 下也不提示。这些情况下提示行**仍然**被删除 |
| **遥测选择退出** | 禁用分析的会话永不显示。含设了 `DISABLE_TELEMETRY` 或 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 的会话，以及 Amazon Bedrock、Google Cloud Agent Platform 等自动遥测退出生效的第三方提供商 |
| **30 秒无响应** | 按**否**关闭 |

用户选**是**把插件装进用户作用域；选**「否，不再显示插件安装提示」**则关闭该用户未来的全部提示。

⚠️ **应用内提交表单只会把插件加进社区 marketplace，而提示协议不检查那个 marketplace。** 官方 marketplace 由 Anthropic 自行策划——想进去须经 Anthropic 合作伙伴联系人协调，提交社区 marketplace 不是路径。

## 2. relevance：本地匹配 + 管理员开关

marketplace 条目里的 `relevance` 对象声明「什么时候该向用户建议这个插件」。

⚠️ **只在 `marketplace.json` 里声明 `relevance` 是不够的——管理员必须在托管设置里把该 marketplace 加入允许列表，建议才会显示。在管理员把任何 marketplace 加进允许列表之前，没有任何 marketplace 的 `relevance` 声明会产生建议，包括官方 Anthropic marketplace。** 这是本节最容易被误判为「配置没生效」的地方。

**匹配在用户机器上本地进行**：不增加网络流量，**也不向 Anthropic 或 marketplace 运营方报告哪些信号匹配或其值**。

### 2.1 字段与三个展示面

| 字段 | 必填 | 说明 |
|---|---|---|
| `topic` | 否 | 填充 spinner 提示里「Working with *topic*?」的短语，通常是产品名（`Stripe`）；插件名读起来不自然时用域名词（`design`）。**默认为插件名，每个连字符段首字母大写。最多 64 字符。会话启动通知不使用这个值** |
| `signals` | 是 | 匹配器对象。**至少需要一个信号，插件才可被建议** |

信号命中且插件尚未安装时，插件出现在三个位置：

| 展示面 | 触发条件 |
|---|---|
| **Spinner 提示** | Claude 正在响应时，spinner 下方显示「Working with *topic*? Install the *plugin* plugin」附 `/plugin install` 命令 |
| **会话启动通知** | **仅 `cwd` 信号**与工作目录匹配时，第一轮之前显示一行 `plugin suggestion: <name>@<marketplace> · /plugin` |
| **`/plugin` Discover 标签页** | 插件被固定在 Discover 列表顶部，带「suggested for this directory」这类注释 |

⚠️ **关闭开关只影响前两个。** spinner 提示与会话启动通知属于 spinner 提示系统：设置里 `spinnerTipsEnabled` 解析为 `false` 时两者都被禁用；或用户 / `--settings` / 托管设置的 `spinnerTipsOverride` 键中 `excludeDefault` 解析为 `true`（且这些键配置了至少一个提示或 `tipsFile`）时同样禁用。**Discover 标签页的固定独立于提示设置，关不掉。**

有 `relevance` 块但无信号命中的插件，行为与任何其他 marketplace 条目一致：在 Discover 列表里以正常位置出现，永不作为 spinner 提示显示。

### 2.2 五种信号与它们的匹配时机

完整对照表（数量与长度上限、路径规范化、大小写敏感性、正则锚定要求）在 [`reference/relevance-signals.md`](../reference/relevance-signals.md)。本节只给三条构成判断依据的语义：

**① 只有 `cwd` 能在会话启动时（第一轮之前）匹配。** `cli`、`hosts`、`filesRead`、`manifestDeps` 都需要会话历史，因此只能在 spinner 提示与 Discover 标签页上命中。

**② `cli` 只记录复合命令的前导命令。** Claude Code 每次 shell 工具调用记录**一个**命令名——去掉前导环境变量赋值与 `sudo` 后的第一个 token。所以 `cd infra && terraform plan` 记录的是 `cd`，**不是 `terraform`**。想匹配 `terraform` 的信号会在这种最常见的调用形态下失效，须改配 `filesRead`。

**③ `filesRead` 测的是会话记录的文件状态，范围比「读过」更宽**——还包括 Claude 写过或编辑过的文件，以及自动加载的 `CLAUDE.md` 记忆文件。`manifestDeps` 同理。

```json
{
  "name": "terraform-helpers",
  "source": "./plugins/terraform-helpers",
  "relevance": {
    "topic": "Terraform",
    "signals": { "cli": ["terraform"], "filesRead": ["**/*.tf"] }
  }
}
```

⚠️ **`relevance` 与 `relevance.signals` 下的未知字段在加载时被忽略**，所以老客户端能继续加载你的 marketplace——代价是拼错的信号名不会报错，只会静默不匹配。`claude plugin validate` 是唯一的检出手段：它把未知键报为警告、标记非对象的 `relevance` 值、并**拒绝含方案、端口或路径的 `signals.hosts` 条目**。

### 2.3 托管设置里的两个条件

把 marketplace 名加进 `pluginSuggestionMarketplaces`。⚠️ **官方 Anthropic marketplace 之外的任何 marketplace，还必须在同一份托管设置里声明其源**——作为该名字在 `extraKnownMarketplaces` 中的条目，或作为 `strictKnownMarketplaces` 中的条目。

```json
{
  "extraKnownMarketplaces": {
    "acme-corp-plugins": {
      "source": { "source": "github", "repo": "acme-corp/claude-plugins" }
    }
  },
  "pluginSuggestionMarketplaces": ["acme-corp-plugins"]
}
```

⚠️ **机器上以该名字注册的 marketplace 若来自不同的源，允许列表里的这个名字被忽略。** 这条防的是「无关的源用允许列表里的名字注册，从而让自己的插件在组织内被建议」。

官方 marketplace 豁免源声明要求——它的名字只能从官方 Anthropic 源注册，所以只写允许列表就够：

```json
{ "pluginSuggestionMarketplaces": ["claude-plugins-official"] }
```

### 2.4 频率上限

| 限制 | 语义 |
|---|---|
| **每三个会话最多一次** | 对给定插件，spinner 提示与会话启动通知**合计**最多每三个会话出现一次 |
| **装了就不再出现** | 插件一旦安装，两者都不再重复 |
| **会话启动通知显示两次后停止** | 即使还没装，它也不会显示第三次 |
| **Discover 固定只一次** | 固定给定插件一次，后续访问以正常顺序列出它 |
