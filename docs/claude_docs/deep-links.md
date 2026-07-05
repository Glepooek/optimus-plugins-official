# 从链接启动会话

> 从一个 URL 打开一个 Claude Code 终端会话。在运行手册、告警和看板中嵌入 `claude-cli://` 链接，点击即可在正确的仓库中打开 Claude Code 并带上正确的提示词。

来源：[code.claude.com/docs/en/deep-links](https://code.claude.com/docs/en/deep-links)

---

深度链接（deep link）是一个 `claude-cli://` URL，点击后会在一个新的终端窗口中打开 Claude Code。这个 URL 可以携带一个工作目录，以及一段要预先填入的提示词。

这让你可以为一项任务分享一个一键起点：任何安装了 Claude Code 的人点击这个链接，都会看到一个会话打开，提示词已经填好。提示词只是被填入，直到你按下 Enter 才会发送。

因为深度链接是一个 URL，你可以把它放在任何能放链接的地方：

* 一个事故运行手册步骤，打开受影响服务的仓库并带上一段诊断提示词
* 一个监控告警或看板，链接到针对某个特定指标的排查提示词
* 一个 README 或 wiki 页面，打开项目并带上一段上手引导提示词
* 一个 CI 失败通知，预先填入失败任务的名称

本页介绍如何[构建一个链接](#build-a-link)、[在运行手册中嵌入它或从 shell 中触发它](#examples)，以及在每个平台上[管理或禁用处理程序注册](#registration-and-supported-platforms)。

> **注意：**
> 深度链接需要 Claude Code v2.1.91 或更高版本。

## 工作原理

`claude-cli://` 前缀是一个自定义 URL scheme，Claude Code 会将其注册到你的操作系统，类似于 `mailto:` 链接打开你的邮件客户端的方式。这个链接可以放在网页、wiki、Slack 消息，或任何能渲染链接的应用中。当你点击一个链接时：

1. 浏览器或应用把这个 URL 交给你的操作系统。
2. 操作系统识别出 `claude-cli://` 前缀，并在你的机器上启动 Claude Code。
3. 一个新的终端窗口打开，Claude Code 在链接指定的目录中运行，输入框中已经填好了链接的提示词文本。
4. 你阅读这段提示词，如果需要可以编辑它，然后按 Enter 发送。

链接本身可以托管在任何地方，但会话总是在你点击的这台电脑上本地打开。参见[注册与支持的平台](#registration-and-supported-platforms)了解每个操作系统上会打开哪个终端模拟器。

> **注意：**
> 显示该链接的平台必须允许自定义 URL scheme。GitHub 渲染的 Markdown 允许 `http` 和 `https`，但会在 README、issue、pull request 和 wiki 中剥离像 `claude-cli://` 这样的 scheme。只会显示链接文本，背后没有链接，URL 也被隐藏。解决办法参见[故障排查](#the-link-renders-as-plain-text-instead-of-being-clickable)。

### 一个已启动的会话会展示什么

深度链接本身从不执行任何操作。这个链接只是选择一个目录并填充提示词框。如果你点击了一个来自不受信任页面的链接，提示词依然是惰性的：在你阅读填入的内容并按下 Enter 之前，任何内容都不会到达模型。

会话打开时，输入框下方会出现一行警告，写着"Prompt from an external link"（提示词来自外部链接），并一直保持可见，直到你发送或清除该提示词。对于超过 1,000 字符的提示词，警告中会包含字符数，并提示你在按 Enter 之前滚动查看完整文本，因为长提示词可能会把部分指令挤出屏幕之外。所选目录的权限规则、`CLAUDE.md` 和信任提示，会像任何其他会话一样照常生效。

## 构建一个链接

每个深度链接都以 `claude-cli://open` 开头，这是处理程序唯一接受的路径，后面跟着可选的查询参数。最简形式会在你的主目录中打开一个空提示词的 Claude Code：

```text theme={null}
claude-cli://open
```

添加参数来控制会话从哪里启动，以及提示词框里有什么内容：

| 参数 | 说明                                                                                                                                                                                                                                                 |
| :--- | :--- |
| `q`       | 要预先填入提示词框的文本。请对该值进行 [URL 编码](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/encodeURIComponent)。多行提示词中的换行请用 `%0A`。最多 5,000 个字符。 |
| `cwd`     | 用作工作目录的绝对路径。网络路径和 UNC 路径会被拒绝，包含不可见字符或双向控制字符的路径也会被拒绝。                                                                             |
| `repo`    | 一个 GitHub 的 `owner/name` 标识。Claude Code 会把它解析为一个它此前见过的本地克隆，并从那里启动。如果没有匹配的克隆，会话会改为在你的主目录中打开。                                                  |

`cwd` 和 `repo` 是[设置工作目录的两种方式](#choose-between-cwd-and-repo)。如果你同时传入两者，`cwd` 优先，`repo` 会被忽略，即使 `cwd` 指定的路径并不存在。

下面这个链接指向一个名为 `acme/payments` 的仓库，带有一段两行的诊断提示词。构建你自己的链接时，请把 `acme/payments` 替换为你仓库的 `owner/name` 标识：

```text theme={null}
claude-cli://open?repo=acme/payments&q=Investigate%20the%20failed%20deploy%20of%20payments-api.%0ACheck%20recent%20commits%20to%20main%20and%20the%20last%20successful%20build.
```

点击它会打开一个新的终端窗口，在你本地 `acme/payments` 的克隆中启动 Claude Code，并用解码后的文本填充提示词框：

```text theme={null}
Investigate the failed deploy of payments-api.
Check recent commits to main and the last successful build.
```

在按 Enter 发送之前，你可以编辑这段提示词。如果你没有该仓库的本地克隆，会话会改为在你的主目录中打开。当你有多个克隆或 worktree 时，本地路径是如何被选中的，参见[在 `cwd` 和 `repo` 之间选择](#choose-between-cwd-and-repo)。

### 在 `cwd` 和 `repo` 之间选择

当点击链接的每个人都把项目放在同一个绝对路径下时，例如一个标准化的 devcontainer 或 VM 镜像，使用 `cwd`。

当链接被共享、每个人克隆到不同位置时，使用 `repo`。Claude Code 按以下方式把这个标识解析为一个本地路径：

* 每次你在一个 Git 仓库中运行 `claude`，该目录的文件系统路径都会被记录，并关联到该仓库的 GitHub `owner/name` 标识。
* 当一个深度链接到达时，`repo` 会打开你最近使用过的那个匹配路径。多个克隆和 worktree 会分别被追踪，因此它会选择你最后一次工作过的那一个。
* 这个查找只会找到你已经至少运行过一次 Claude Code 的路径。
* 这个链接不会改变检出的分支。会话会以该目录当前所处的状态打开。

欢迎信息会显示它选中的是哪个路径，方便你确认打开的是不是正确的克隆。

## 示例

以下小节展示了使用深度链接的两种常见方式：作为文档中的一个 Markdown 链接，以及作为脚本或 shell 别名中的一条命令。

### 在运行手册中嵌入一个链接

运行手册中的一个深度链接，能让排查问题的人一键开始在正确的仓库中调查，并带上一段准备好的提示词。渲染该运行手册的平台必须允许自定义 URL scheme。GitHub 渲染的 Markdown 不允许 `claude-cli://`，因此 GitHub README、issue 或 wiki 中的深度链接只会显示其文字标签，没有可点击的链接。解决办法参见[故障排查说明](#the-link-renders-as-plain-text-instead-of-being-clickable)。

提示词是 URL 的一部分，必须进行 URL 编码。要生成编码后的值，可以在浏览器控制台或任意 URL 编码工具中把你的提示词文本传给 `encodeURIComponent`。

下面的例子为一个叫 `web-gateway` 的服务的事故运行手册添加了一个调查入口：

```markdown theme={null}
## High 5xx rate on web-gateway

1. Acknowledge the page in PagerDuty.
2. [Open Claude Code in the gateway repo](claude-cli://open?repo=acme/web-gateway&q=5xx%20rate%20is%20elevated%20on%20web-gateway.%20Check%20recent%20deploys%2C%20error%20logs%20from%20the%20last%2030%20minutes%2C%20and%20open%20incidents%20in%20Linear.)
3. Post initial findings in #incident.
```

要在你自己的运行手册中使用，把 `acme/web-gateway` 替换为你服务的仓库标识。这样，安装了 Claude Code 并有该仓库本地克隆的工程师，就能点击第 2 步，用已经准备好的提示词开始调查。

### 从 shell 中打开一个链接

你也可以从一个 shell 脚本、别名或自动化流程中打开一个深度链接，而不是靠点击。用你操作系统的 URL 打开命令，把这个链接作为参数传入即可。

**macOS：**

内置的 `open` 命令会把这个 URL 传给已注册的 `claude-cli://` 处理程序：

```bash theme={null}
open "claude-cli://open?repo=acme/payments&q=review%20open%20PRs"
```

**Linux：**

大多数桌面环境都提供 `xdg-open`，它会把这个 URL 传给已注册的处理程序：

```bash theme={null}
xdg-open "claude-cli://open?repo=acme/payments&q=review%20open%20PRs"
```

**Windows：**

在 PowerShell 中，`Start-Process` 会把这个 URL 传给已注册的处理程序：

```powershell theme={null}
Start-Process "claude-cli://open?repo=acme/payments&q=review%20open%20PRs"
```

在 `cmd.exe` 中，`start` 会把它的第一个带引号的参数当作窗口标题，所以要在 URL 前面传一个空标题：

```cmd theme={null}
start "" "claude-cli://open?repo=acme/payments&q=review%20open%20PRs"
```

## 注册与支持的平台

Claude Code 会在你第一次在 macOS、Linux 和 Windows 上启动一个交互式会话时，把 `claude-cli://` 处理程序注册到你的操作系统。你不需要运行单独的安装命令。注册只会写入用户级别的位置：

| 平台 | 处理程序位置                                                                                                   |
| :--- | :--- |
| macOS    | `~/Applications/Claude Code URL Handler.app`                                                                       |
| Linux    | `$XDG_DATA_HOME/applications` 下的 `claude-code-url-handler.desktop`，默认为 `~/.local/share/applications` |
| Windows  | `HKEY_CURRENT_USER\Software\Classes\claude-cli`                                                                    |

处理程序会在一个检测到的终端模拟器中启动 Claude Code。在 macOS 上，Claude Code 会记住你最近一次交互式会话所用的终端并复用它，支持 iTerm2、Ghostty、kitty、Alacritty、WezTerm 和 Terminal.app。在 Linux 上，它遵循 `$TERMINAL` 环境变量，然后是 `x-terminal-emulator`，再然后是一份常见模拟器列表。在 Windows 上，它优先选择 Windows Terminal，然后是 PowerShell，再然后是 `cmd.exe`。

要完全阻止注册，在 `settings.json` 中把 [`disableDeepLinkRegistration`](https://code.claude.com/docs/en/settings) 设为 `"disable"`。要在整个组织中强制执行这一点，让用户无法重新启用它，请改在[受管理设置](https://code.claude.com/docs/en/server-managed-settings)中设置它。

## 打开一个 VS Code 标签页而不是终端

VS Code 插件会注册自己的处理程序，地址是 `vscode://anthropic.claude-code/open`，它打开的是一个 Claude Code 编辑器标签页，而不是一个终端窗口。关于该 URL 的参数，参见[从其他工具启动一个 VS Code 标签页](https://code.claude.com/docs/en/vs-code#launch-a-vs-code-tab-from-other-tools)。

## 故障排查

### 点击链接没有任何反应

处理程序可能还没有注册。在那台机器上启动一次交互式 `claude` 会话，退出，再试一次这个链接。如果你在没有桌面环境的 Linux 上，`xdg-open` 可能找不到可分发的目标。

### 链接渲染为纯文本，而不是可点击的

一些 Markdown 渲染器只允许 `http` 和 `https` 链接，会剥离其他 URL scheme。GitHub 在 README、issue、pull request 和 wiki 中就是这样做的：`[label](claude-cli://...)` 只会渲染成 `label`，没有链接，URL 也被移除。在这些平台上，把深度链接放进一个代码块中，这样读者就能看到这个 URL，并把它粘贴到浏览器地址栏中。

### 会话在我的主目录中打开，而不是在仓库中

`repo` 参数只能解析到 Claude Code 已经见过的克隆。在该克隆中运行一次 `claude`，让它的路径被记录下来，或者把链接改为使用带绝对路径的 `cwd`。

### 链接打开了错误的终端

在 macOS 上，在你偏好的终端中启动一次 `claude`，下一个深度链接就会使用它。在 Linux 上，把 `$TERMINAL` 环境变量设为你偏好的模拟器的命令名。在 Windows 上，顺序是固定的：如果你想让链接改在 Windows Terminal 而不是 PowerShell 或 `cmd.exe` 窗口中打开，请安装 Windows Terminal。

## 延伸阅读

以下页面涵盖了启动或扩展 Claude Code 会话的相关方式：

* [Skills](https://code.claude.com/docs/en/skills)：把一段长的运行手册提示词存成仓库中的一个 `/skill`，这样深度链接的 `q` 参数只需要指名它即可
* [非交互模式](https://code.claude.com/docs/en/headless)：从一个脚本中运行 Claude，无需打开终端即可获取输出
