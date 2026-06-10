# Unipus DevOps 插件 - Hooks 集合

这个目录包含了用于增强 Claude Code 工作流程的各种 hooks。这些 hooks 可以在特定事件发生时自动执行，提升开发效率和用户体验。

## 📋 目录

- [SessionStart Hook - 会话启动技巧展示](#sessionstart-hook---会话启动技巧展示)
- [Notification Hook - 智能权限通知](#notification-hook---智能权限通知)
- [安装指南](#安装指南)
- [自定义配置](#自定义配置)

---

## SessionStart Hook - 会话启动技巧展示

### 功能说明

在每次 Claude Code 会话启动时，智能地展示使用技巧，帮助用户更好地使用 Claude Code 的各种功能。

### 特性

- **智能轮播**: 确保所有技巧都展示完毕后才开始下一轮
- **随机顺序**: 每轮技巧按随机顺序展示，避免单调
- **可配置数量**: 默认每次显示 2 条技巧，可通过环境变量调整（1-3 条）
- **进度追踪**: 显示当前轮次和展示进度（如：📚 第 1 轮 · 1-2/334）
- **状态持久化**: 使用 JSON 文件记录展示状态，跨会话保持
- **智能检测**: 自动检测技巧数量变化，变化时重置展示状态

### 文件结构

```
sessionstart/
├── show-tip.sh          # 主脚本
├── tips.txt             # 技巧内容文件
└── .tip-state.json      # 状态文件（自动生成于 ~/.claude/.tip-state.json）
```

### 技巧分类

tips.txt 包含 201 条技巧，涵盖以下分类：

- **[交互]** - 基本交互命令和快捷键
- **[工具]** - Claude Code 内置工具使用
- **[Hook]** - Hooks 机制和配置
- **[配置]** - settings.json 配置项
- **[CLI]** - 命令行参数和子命令
- **[集成]** - Skills、Plugins、MCP 集成
- **[工作流与自动化]** - 高级工作流程
- **[排障]** - 问题诊断和排查
- **[Skill]** - 预定义工作流技能
- **[MCP]** - Model Context Protocol 服务器
- **[高级]** - 高级特性和用法

### 环境变量配置

```bash
# 设置每次显示的技巧数量（1-3，默认 2）
export CLAUDE_TIPS_COUNT=2
```

---

## Notification Hook - 智能权限通知

### 功能说明

当 Claude Code 请求用户权限时，如果 Claude Code 窗口不在焦点，则发送 Windows 系统通知提醒用户。

### 特性

- **智能判断**: 仅在 Claude Code 窗口不在焦点时通知
- **避免干扰**: 如果用户正在查看 Claude 窗口，不会发送通知
- **声音提示**: 通知带有系统默认声音
- **自定义消息**: 可通过环境变量自定义通知文本
- **自定义图标**: 支持自定义通知图标

### 依赖要求

- **Windows 系统**
- **PowerShell**
- **BurntToast 模块**: 用于发送 Windows 通知

#### 安装 BurntToast 模块

```powershell
# 以管理员身份运行 PowerShell
Install-Module -Name BurntToast -Scope CurrentUser
```

### 环境变量配置

```bash
# 自定义通知消息（默认："Master，Claude 等你发令！"）
export CLAUDE_NOTIFICATION="Claude 需要你的批准"
```

### 通知图标

默认图标路径：`~/.claude/icon.png`

如果需要自定义图标，请将图片文件放置在该位置。

---

## 安装指南

### 方法 1: 通过插件自动使用（✨ 强烈推荐）

**这是最简单的方式！** 当你安装 `unipus-devops-plugin` 插件后，这些 hooks 会**自动注册**到 Claude Code，无需任何手动配置。

#### 步骤：

1. **安装或更新插件**

   如果你是通过 Claude Code 插件市场安装的 `unipus-plugins-official`，插件更新后会自动包含这些 hooks。

   ```bash
   # 或者手动从 Git 仓库安装/更新
   cd ~/.claude/plugins/marketplaces/
   git clone https://github.com/Glepooek/unipus-plugins-official.git
   # 或更新现有仓库
   cd unipus-plugins-official && git pull
   ```

2. **在 settings.json 中启用插件**

   确保 `~/.claude/settings.json` 中启用了该插件：

   ```json
   {
     "enabledPlugins": {
       "unipus-devops-plugin@unipus-plugins-official": true
     },
     "extraKnownMarketplaces": {
       "unipus-plugins-official": {
         "source": {
           "source": "github",
           "repo": "Glepooek/unipus-plugins-official"
         }
       }
     }
   }
   ```

3. **重启 Claude Code**

   重启后，hooks 会自动生效！你会在每次启动时看到使用技巧，权限提示时收到通知。

#### 优势：
- ✅ **零手动配置** - 无需复制文件或编辑 hooks 配置
- ✅ **自动更新** - 插件更新时 hooks 也会更新
- ✅ **团队共享** - 团队成员安装插件即可使用相同配置
- ✅ **易于管理** - 通过插件系统统一管理

---

### 方法 2: 手动独立安装（仅需要独立使用时）

如果你不想使用完整的 `unipus-devops-plugin` 插件，只想单独使用这些 hooks，可以手动安装到 `~/.claude/hooks` 目录。

#### 使用安装脚本：

**Unix/Linux/Git Bash:**

```bash
cd /path/to/unipus-plugins-official
./plugins/unipus-devops-plugin/hooks/install.sh
```

**Windows PowerShell:**

```powershell
cd C:\path\to\unipus-plugins-official
.\plugins\unipus-devops-plugin\hooks\install.ps1
```

安装脚本会自动完成所有配置。

#### 手动安装：

1. **复制 hooks 到 Claude 配置目录**

```bash
# Unix/Linux/Git Bash
cp -r ./plugins/unipus-devops-plugin/hooks/sessionstart ~/.claude/hooks/
cp -r ./plugins/unipus-devops-plugin/hooks/notification ~/.claude/hooks/

# 或使用 PowerShell
Copy-Item -Recurse -Force .\plugins\unipus-devops-plugin\hooks\sessionstart $env:USERPROFILE\.claude\hooks\
Copy-Item -Recurse -Force .\plugins\unipus-devops-plugin\hooks\notification $env:USERPROFILE\.claude\hooks\
```

2. **编辑 settings.json**

打开 `~/.claude/settings.json`（如果没有该文件，可以先运行 `/config` 创建），添加以下配置：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/sessionstart/show-tip.sh"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File ~/.claude/hooks/notification/permission-notify.ps1",
            "async": true
          }
        ]
      }
    ]
  }
}
```

3. **重启 Claude Code**

重新启动 Claude Code 使配置生效。

---

## 自定义配置

### 自定义技巧内容

编辑 `~/.claude/hooks/sessionstart/tips.txt` 文件：

- 每条技巧使用 `---` 分隔
- 支持 `\n` 表示换行（会在显示时转换为真实换行）
- 格式建议：`[分类] 🔰 标题\n功能：...\n效果：...\n例子：...`

示例：

```
[自定义] 🎯 我的技巧\n功能：这是一个自定义技巧\n效果：帮助你更好地使用 Claude\n例子：在需要时使用这个功能
---
[自定义] 🚀 另一个技巧\n功能：另一个有用的提示\n效果：提升工作效率\n例子：日常开发中的实用技巧
```

### 调整技巧显示数量

在 `~/.claude/settings.json` 中添加环境变量：

```json
{
  "env": {
    "CLAUDE_TIPS_COUNT": "3"
  }
}
```

### 禁用特定 Hook

如果要临时禁用某个 hook，可以在 settings.json 中注释掉相应的配置，或者删除该 hook 的配置块。

---

## 常见问题

### Q: SessionStart hook 显示错误 "提示文件不存在"

**A**: 确保 `tips.txt` 文件在正确的位置：`~/.claude/hooks/sessionstart/tips.txt`

### Q: Notification hook 不工作

**A**: 检查以下几点：
1. 确保已安装 BurntToast 模块：`Get-Module -ListAvailable BurntToast`
2. 检查 PowerShell 执行策略：`Get-ExecutionPolicy`
3. 如果提示权限问题，尝试以管理员身份安装 BurntToast

### Q: 如何查看当前 hook 状态

**A**: 使用 `/hooks` 命令查看当前配置的所有 hooks。

### Q: 技巧展示顺序可以固定吗？

**A**: 当前设计是随机展示以保持新鲜感。如果需要固定顺序，可以修改 `show-tip.sh` 中的 Python 代码，移除 `random.shuffle(remaining)` 这行。

---

## 贡献

如果你有更好的技巧或改进建议，欢迎：

1. 编辑 `tips.txt` 添加新技巧
2. 改进 hook 脚本逻辑
3. 提交 Pull Request

---

## 许可证

MIT License - 详见项目根目录 LICENSE 文件
