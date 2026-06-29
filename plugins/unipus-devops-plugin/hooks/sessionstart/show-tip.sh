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
# 固定路径，避免随 plugin cache 版本哈希变化导致状态丢失
STATE_FILE="$HOME/.claude/.tip-state.json"

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
import io
import time

# 修复 Windows GBK 编码问题：强制 stdout 使用 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 在非 Windows 平台导入 fcntl
if sys.platform != 'win32':
    import fcntl

TIPS_FILE = os.environ['TIPS_FILE']
STATE_FILE = os.environ['STATE_FILE']
LOCK_FILE = STATE_FILE + '.lock'
TIPS_COUNT = int(os.environ.get('TIPS_COUNT', 2))

# 限制显示数量在 1-3 之间
TIPS_COUNT = max(1, min(3, TIPS_COUNT))

def acquire_lock(lock_file, timeout=2):
    """获取文件锁，支持超时和跨平台"""
    start_time = time.time()
    lock_fd = None

    while time.time() - start_time < timeout:
        try:
            # Windows 不支持 fcntl，使用独占打开模式
            if sys.platform == 'win32':
                # 尝试独占创建锁文件
                lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return lock_fd
            else:
                # Unix/Linux 使用 fcntl 文件锁
                lock_fd = open(lock_file, 'w')
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_fd
        except (OSError, IOError):
            # 锁已被占用，短暂等待后重试
            time.sleep(0.1)

    # 超时：强制获取锁（清理僵尸锁）
    if sys.platform == 'win32':
        try:
            os.remove(lock_file)
        except:
            pass
        lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    else:
        lock_fd = open(lock_file, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)

    return lock_fd

def release_lock(lock_fd, lock_file):
    """释放文件锁"""
    try:
        if sys.platform == 'win32':
            os.close(lock_fd)
            os.remove(lock_file)
        else:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
            try:
                os.remove(lock_file)
            except:
                pass
    except:
        pass

try:
    # 获取锁（防止并发冲突）
    lock_fd = acquire_lock(LOCK_FILE)

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
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                round_num = state.get('round', 1)
                remaining = state.get('remaining', [])
                saved_count = state.get('count', count)

                # 检测技巧数量是否变化
                if saved_count != count:
                    need_reset = True
            except (json.JSONDecodeError, ValueError):
                # 状态文件损坏（空文件或无效 JSON），重新初始化
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

    finally:
        # 释放锁
        release_lock(lock_fd, LOCK_FILE)

except Exception as e:
    print(json.dumps({"systemMessage": f"错误: {str(e)}"}), file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT
