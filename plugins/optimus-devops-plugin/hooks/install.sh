#!/usr/bin/env bash
# Optimus DevOps Plugin - Hooks 安装脚本
# 自动安装 SessionStart 和 Notification hooks 到 Claude Code

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Optimus DevOps Plugin - Hooks 安装程序${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Claude 配置目录
if [[ ! -d "$CLAUDE_DIR" ]]; then
    echo -e "${YELLOW}⚠️  Claude 配置目录不存在，正在创建...${NC}"
    mkdir -p "$CLAUDE_DIR"
fi

# 创建 hooks 目录
echo -e "${BLUE}📁 创建 hooks 目录...${NC}"
mkdir -p "$HOOKS_DIR/sessionstart"
mkdir -p "$HOOKS_DIR/notification"

# 复制 SessionStart hook
echo -e "${BLUE}📋 安装 SessionStart hook...${NC}"
cp -f "$SCRIPT_DIR/sessionstart/show-tip.sh" "$HOOKS_DIR/sessionstart/"
cp -f "$SCRIPT_DIR/sessionstart/tips.txt" "$HOOKS_DIR/sessionstart/"
chmod +x "$HOOKS_DIR/sessionstart/show-tip.sh"
echo -e "${GREEN}✅ SessionStart hook 已安装${NC}"

# 复制 Notification hook
echo -e "${BLUE}🔔 安装 Notification hook...${NC}"
cp -f "$SCRIPT_DIR/notification/permission-notify.ps1" "$HOOKS_DIR/notification/"
echo -e "${GREEN}✅ Notification hook 已安装${NC}"

# 备份现有的 settings.json
if [[ -f "$SETTINGS_FILE" ]]; then
    backup_file="${SETTINGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}💾 备份现有配置到: $backup_file${NC}"
    cp "$SETTINGS_FILE" "$backup_file"
fi

# 配置 settings.json
echo ""
echo -e "${BLUE}⚙️  配置 settings.json...${NC}"
echo -e "${YELLOW}提示: 建议使用 Claude Code 的 update-config skill 来配置 hooks${NC}"
echo -e "${YELLOW}      或者手动编辑 ~/.claude/settings.json 添加以下配置：${NC}"
echo ""
cat << 'EOF'
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
EOF
echo ""

# 检查 Windows 环境下的 BurntToast 模块
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo -e "${BLUE}🔍 检查 BurntToast 模块（Notification hook 依赖）...${NC}"
    if powershell.exe -Command "Get-Module -ListAvailable BurntToast" &>/dev/null; then
        echo -e "${GREEN}✅ BurntToast 模块已安装${NC}"
    else
        echo -e "${YELLOW}⚠️  BurntToast 模块未安装${NC}"
        echo -e "${YELLOW}   Notification hook 需要此模块才能工作${NC}"
        echo -e "${YELLOW}   请以管理员身份运行 PowerShell 并执行：${NC}"
        echo -e "${YELLOW}   Install-Module -Name BurntToast -Scope CurrentUser${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Hooks 文件安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}下一步：${NC}"
echo -e "1. 使用 Claude Code 的 ${YELLOW}update-config skill${NC} 配置 hooks"
echo -e "2. 或手动编辑 ${YELLOW}~/.claude/settings.json${NC} 添加上面显示的配置"
echo -e "3. 重启 Claude Code 使配置生效"
echo ""
echo -e "${BLUE}文档：${NC}"
echo -e "查看 ${YELLOW}$SCRIPT_DIR/README.md${NC} 了解更多配置选项"
echo ""
