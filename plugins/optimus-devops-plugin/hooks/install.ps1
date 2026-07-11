# Optimus DevOps Plugin - Hooks 安装脚本 (PowerShell)
# 自动安装 SessionStart 和 Notification hooks 到 Claude Code

$ErrorActionPreference = "Stop"

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir = "$env:USERPROFILE\.claude"
$HooksDir = "$ClaudeDir\hooks"
$SettingsFile = "$ClaudeDir\settings.json"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Optimus DevOps Plugin - Hooks 安装程序" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# 检查 Claude 配置目录
if (-not (Test-Path $ClaudeDir)) {
    Write-Host "⚠️  Claude 配置目录不存在，正在创建..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $ClaudeDir | Out-Null
}

# 创建 hooks 目录
Write-Host "📁 创建 hooks 目录..." -ForegroundColor Blue
New-Item -ItemType Directory -Path "$HooksDir\sessionstart" -Force | Out-Null
New-Item -ItemType Directory -Path "$HooksDir\notification" -Force | Out-Null

# 复制 SessionStart hook
Write-Host "📋 安装 SessionStart hook..." -ForegroundColor Blue
Copy-Item -Force "$ScriptDir\sessionstart\show-tip.sh" "$HooksDir\sessionstart\"
Copy-Item -Force "$ScriptDir\sessionstart\tips.txt" "$HooksDir\sessionstart\"
Write-Host "✅ SessionStart hook 已安装" -ForegroundColor Green

# 复制 Notification hook
Write-Host "🔔 安装 Notification hook..." -ForegroundColor Blue
Copy-Item -Force "$ScriptDir\notification\permission-notify.ps1" "$HooksDir\notification\"
Write-Host "✅ Notification hook 已安装" -ForegroundColor Green

# 备份现有的 settings.json
if (Test-Path $SettingsFile) {
    $BackupFile = "$SettingsFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "💾 备份现有配置到: $BackupFile" -ForegroundColor Yellow
    Copy-Item $SettingsFile $BackupFile
}

# 检查 BurntToast 模块
Write-Host ""
Write-Host "🔍 检查 BurntToast 模块（Notification hook 依赖）..." -ForegroundColor Blue
$BurntToastInstalled = Get-Module -ListAvailable BurntToast

if ($BurntToastInstalled) {
    Write-Host "✅ BurntToast 模块已安装" -ForegroundColor Green
} else {
    Write-Host "⚠️  BurntToast 模块未安装" -ForegroundColor Yellow
    Write-Host "   Notification hook 需要此模块才能工作" -ForegroundColor Yellow
    Write-Host ""

    $InstallChoice = Read-Host "是否现在安装 BurntToast 模块? (Y/N)"
    if ($InstallChoice -eq 'Y' -or $InstallChoice -eq 'y') {
        try {
            Write-Host "正在安装 BurntToast 模块..." -ForegroundColor Blue
            Install-Module -Name BurntToast -Scope CurrentUser -Force
            Write-Host "✅ BurntToast 模块安装成功" -ForegroundColor Green
        } catch {
            Write-Host "❌ 安装失败: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "   请以管理员身份运行 PowerShell 并手动安装：" -ForegroundColor Yellow
            Write-Host "   Install-Module -Name BurntToast -Scope CurrentUser" -ForegroundColor Yellow
        }
    }
}

# 配置说明
Write-Host ""
Write-Host "⚙️  配置 settings.json..." -ForegroundColor Blue
Write-Host "提示: 建议使用 Claude Code 的 update-config skill 来配置 hooks" -ForegroundColor Yellow
Write-Host "      或者手动编辑 ~/.claude/settings.json 添加以下配置：" -ForegroundColor Yellow
Write-Host ""

$ConfigExample = @'
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
'@

Write-Host $ConfigExample
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Hooks 文件安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：" -ForegroundColor Blue
Write-Host "1. 使用 Claude Code 的 " -NoNewline
Write-Host "update-config skill" -ForegroundColor Yellow -NoNewline
Write-Host " 配置 hooks"
Write-Host "2. 或手动编辑 " -NoNewline
Write-Host "~/.claude/settings.json" -ForegroundColor Yellow -NoNewline
Write-Host " 添加上面显示的配置"
Write-Host "3. 重启 Claude Code 使配置生效"
Write-Host ""
Write-Host "文档：" -ForegroundColor Blue
Write-Host "查看 " -NoNewline
Write-Host "$ScriptDir\README.md" -ForegroundColor Yellow -NoNewline
Write-Host " 了解更多配置选项"
Write-Host ""
