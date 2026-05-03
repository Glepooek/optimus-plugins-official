#!/bin/bash
# Jenkins 构建触发脚本
# 用法：
#   ./run.sh                    # 触发默认 job
#   ./run.sh zk-api             # 触发指定 job
#   ./run.sh zk-api BRANCH=main # 触发带参数的 job

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 检查配置文件
if [ ! -f "$SKILL_DIR/jenkins_build/config.yaml" ]; then
    echo "[✗] 未找到配置文件 $SKILL_DIR/jenkins_build/config.yaml"
    echo "    请参考 jenkins_build/config.yaml.example 创建配置文件"
    exit 1
fi

VENV_DIR="$SKILL_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"

# 创建虚拟环境并安装依赖
if [ ! -f "$PYTHON" ]; then
    echo "[~] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

if ! "$PYTHON" -c "import requests, yaml" 2>/dev/null; then
    echo "[~] 安装依赖..."
    "$VENV_DIR/bin/pip" install requests pyyaml -q
fi

# 执行构建
cd "$SKILL_DIR/jenkins_build"
"$PYTHON" main.py "$@"
