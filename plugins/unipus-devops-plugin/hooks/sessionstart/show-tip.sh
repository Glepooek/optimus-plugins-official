#!/usr/bin/env bash
# 智能追踪展示：确保所有技巧都展示完毕后才开始下一轮

# 获取脚本所在目录
# 支持插件环境（CLAUDE_PLUGIN_ROOT）和独立安装（SCRIPT_DIR）
if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
    # 插件环境：使用 CLAUDE_PLUGIN_ROOT
    HOOKS_DIR="$CLAUDE_PLUGIN_ROOT/hooks/sessionstart"
else
    # 独立安装：使用脚本所在目录
    HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

TIPS_FILE="$HOOKS_DIR/tips.txt"
STATE_FILE="$HOOKS_DIR/.tip-state.json"

# 可配置：每次显示的技巧数量(默认2条,可通过环境变量修改)
TIPS_COUNT=${CLAUDE_TIPS_COUNT:-2}

if [[ ! -f "$TIPS_FILE" ]]; then
    echo '{"systemMessage":"提示文件不存在"}'
    exit 0
fi

# 使用 Python 处理所有逻辑，通过环境变量传递路径
export TIPS_FILE STATE_FILE TIPS_COUNT
python << 'PYTHON_SCRIPT'
import json
import os
import random
import sys

TIPS_FILE = os.environ['TIPS_FILE']
STATE_FILE = os.environ['STATE_FILE']
TIPS_COUNT = int(os.environ.get('TIPS_COUNT', 2))

# 限制显示数量在 1-3 之间
TIPS_COUNT = max(1, min(3, TIPS_COUNT))

try:
    # 读取所有技巧
    with open(TIPS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        tips = [tip.strip() for tip in content.split('---\n') if tip.strip()]

    count = len(tips)
    if count == 0:
        print(json.dumps({"systemMessage": "没有可用的技巧"}))
        sys.exit(0)

    # 读取或初始化状态
    need_reset = False
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        round_num = state.get('round', 1)
        remaining = state.get('remaining', [])
        saved_count = state.get('count', count)

        # 检测技巧数量是否变化
        if saved_count != count:
            need_reset = True
    else:
        need_reset = True

    if need_reset:
        round_num = 1
        remaining = list(range(count))
        random.shuffle(remaining)

    # 如果本轮已展示完，开始新一轮
    if not remaining:
        round_num += 1
        remaining = list(range(count))
        random.shuffle(remaining)

    # 每次选择 N 条技巧（如果剩余不足则全部选择）
    tips_to_show = min(TIPS_COUNT, len(remaining))
    selected_indices = [remaining.pop(0) for _ in range(tips_to_show)]
    selected_tips = [tips[i] for i in selected_indices]

    # 保存状态(包含技巧总数用于变化检测)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'round': round_num,
            'remaining': remaining,
            'count': count
        }, f)

    # 计算进度
    shown_start = count - len(remaining) - tips_to_show + 1
    shown_end = count - len(remaining)
    if tips_to_show == 1:
        progress = f"📚 第 {round_num} 轮 · {shown_end}/{count}"
    else:
        progress = f"📚 第 {round_num} 轮 · {shown_start}-{shown_end}/{count}"

    # 转换字面 \n 为真实换行符
    selected_tips = [tip.replace('\\n', '\n') for tip in selected_tips]

    # 合并多条技巧，用美化的分隔线隔开
    separator = "\n\n" + "━" * 50 + "\n\n"
    combined_tips = separator.join(selected_tips)

    # 输出（将进度信息添加到技巧前）
    tip_with_progress = f"{progress}\n\n{combined_tips}"
    print(json.dumps({"systemMessage": tip_with_progress}, ensure_ascii=False))

except Exception as e:
    print(json.dumps({"systemMessage": f"错误: {str(e)}"}), file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT
