# Claude Code 配置说明

> 记录于 2026-06-13，基于 `/config` 面板截图整理；最后更新 2026-06-13

---

## 第一页配置

| 选项 | 当前值 | 含义 | 建议 |
|---|---|---|---|
| Auto-compact | true | 对话接近上下文上限时自动压缩历史消息 | ✅ 保持 |
| Switch models when a message is flagged | true | 消息被安全过滤拦截时自动切换模型重试 | ✅ 保持 |
| Show tips | true | 显示使用技巧提示 | ✅ 保持 |
| Reduce motion | false | 减少界面动画效果（无障碍选项） | ✅ 保持 |
| Thinking mode | true | 启用扩展思考，模型回答前进行深度推理 | ⚠️ 可关闭，简单任务浪费 token；需要时在 prompt 中写 `think` 手动触发 |
| Session recap | false | 会话开始时显示上次对话摘要 | 💡 可开启，与 `.remember/` 记忆系统互补 |
| Rewind code (checkpoints) | true | 启用代码检查点，可回滚到之前的文件状态 | ✅ 保持，对多文件修改有价值 |
| Dynamic workflows | true | 允许工作流脚本在运行时动态调整 | ✅ 保持 |
| Ultracode keyword trigger | true | prompt 含 "ultracode" 关键字时触发多 agent 工作流 | ✅ 保持，但注意 token 消耗 |
| Verbose output | false | 显示详细的工具调用日志 | ✅ 保持，调试时再临时开启 |
| Terminal progress bar | false | 在终端底部显示进度条 | ✅ 已关闭 |
| Show turn duration | true | 显示每轮对话耗时 | ✅ 保持 |
| Default permission mode | acceptEdits | 工具调用默认授权模式（自动接受文件修改，bash 命令仍需确认） | ✅ 已优化 |
| Worktree base ref | fresh | 创建 git worktree 时的基准分支（从远端默认分支） | ✅ 保持 |
| Use auto mode during plan | true | 计划模式中自动批准低风险操作 | ✅ 保持 |
| Respect .gitignore in file picker | true | 文件选择器过滤 .gitignore 忽略的文件 | ✅ 保持 |
| Skip the /copy picker | false | 执行 `/copy` 命令时显示选择菜单 | ✅ 保持 |
| Copy on select | true | 选中文本后自动复制到剪贴板 | ✅ 保持 |

---

## 第二页配置

| 选项 | 当前值 | 含义 | 建议 |
|---|---|---|---|
| Auto-scroll | true | 输出时自动滚动到底部 | ✅ 保持 |
| Open agents view by default | true | 有 agent 任务时默认展开 agent 面板 | ✅ 保持 |
| ← opens agents | true | 按左箭头键打开 agent 视图 | ✅ 保持 |
| Auto-update channel | disabled (env) | 自动更新被环境变量禁用 | ⚠️ 需手动更新：`npm update -g @anthropic-ai/claude-code` |
| Theme | Dark mode (ANSI) | 深色主题，使用终端原生 ANSI 颜色 | ✅ 保持 |
| Local notifications | Auto | 根据焦点状态自动发送系统通知 | ✅ 保持 |
| Output style | Explanatory | 教学式输出风格 | ✅ 保持 |
| Language | 简体中文 | 界面和回复语言 | ✅ 保持 |
| Editor mode | normal | 输入框编辑模式（可选 vim） | 按个人习惯 |
| Show last response in external editor | false | 用外部编辑器查看上次回复 | ✅ 保持 |
| Show PR status footer | false | 底部显示当前 PR 状态 | ✅ 保持 |
| Model | sonnet[1m] | 当前主模型（1M token 上下文窗口） | ✅ 合适，大仓库受益于长上下文 |
| Auto-connect to IDE (external terminal) | true | 自动连接 VS Code 等 IDE 扩展 | ✅ 保持 |
| Claude in Chrome enabled by default | false | 浏览器扩展集成 | ✅ 保持 |
| Teammate mode | auto | 多 agent 协作中自动判断自身角色 | ✅ 保持 |
| Default teammate model | claude-sonnet-4-6 | 子 agent 默认使用的模型 | ✅ 已优化，从 opus-4-8 改为 sonnet 降低成本 |


## 补充说明

### Permission Mode 四档说明
- **Default** — 逐次询问
- **acceptEdits** — 自动接受文件修改，仍会询问 bash 命令
- **bypassPermissions** — 全自动，跳过所有确认（高风险）
- **plan** — 只规划不执行

### Ultracode + Teammate Model 的成本关系
启用 `Ultracode keyword trigger: true` 时，每次在 prompt 中写 "ultracode" 会触发多 agent workflow，所有子 agent 均使用 `Default teammate model` 运行，单次任务可能消耗数十万 token。已将 teammate model 从 `opus-4-8` 改为 `sonnet` 以降低成本；如需高质量输出，可在 workflow 脚本中为特定 agent 指定 `model: "opus"` 覆盖默认值。
