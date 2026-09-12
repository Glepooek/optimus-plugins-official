#!/usr/bin/env bash
# PreToolUse 门禁：拦截 git commit，要求 staged 的 .xaml 改动先经 wpf-code-review 审查。
# 用法：
#   review-gate.sh        默认检测模式，作为 PreToolUse hook 被调用（stdin 传入 hook JSON）
#   review-gate.sh mark   审查通过后，标记当前 staged .xaml 内容为已审查

set -euo pipefail

GIT_DIR="$(git rev-parse --git-dir 2>/dev/null || true)"
if [[ -z "$GIT_DIR" ]]; then
    # 不在 git 仓库内：没有可门禁的对象。必须干净 exit 0——`set -e` 下让
    # git rev-parse 失败会以 128 退出，被当成非阻断 hook 错误，虽然同样放行，
    # 但每次 Bash 调用都在 transcript 留一条错误通知。
    if [[ "${1:-}" == "mark" ]]; then
        echo "当前目录不在 git 仓库内，无法标记。" >&2
        exit 1
    fi
    exit 0
fi

MARK_DIR="$GIT_DIR/optimus-review-marks"
MARK_FILE="$MARK_DIR/wpf.hash"
SKILL_NAME="wpf-code-review"
PATTERN='*.xaml'

current_hash() {
    git diff --cached -- "$PATTERN" | sha256sum | cut -d' ' -f1
}

if [[ "${1:-}" == "mark" ]]; then
    mkdir -p "$MARK_DIR"
    current_hash > "$MARK_FILE"
    echo "已标记当前 staged .xaml 改动为审查通过。"
    exit 0
fi

# 检测模式：无 staged 的 .xaml 改动，直接放行，不必关心当前命令是不是 git commit
staged_files="$(git diff --cached --name-only -- "$PATTERN")"
if [[ -z "$staged_files" ]]; then
    exit 0
fi

input="$(cat)"
# 只在 tool_input.command 的值内匹配，避免命中 description 等其他字段。
# 刻意不起解释器解析 JSON：Git Bash 自带环境没有 python3，解析失败会让门禁
# 静默放行；且每次 Bash 调用都要多付一个解释器的启动开销。
GIT_COMMIT_RE='"command"[[:space:]]*:[[:space:]]*"[^"]*git[[:space:]]+commit'
if [[ ! "$input" =~ $GIT_COMMIT_RE ]]; then
    exit 0
fi

hash_now="$(current_hash)"
hash_marked="$(cat "$MARK_FILE" 2>/dev/null || true)"

if [[ -n "$hash_marked" && "$hash_now" == "$hash_marked" ]]; then
    exit 0
fi

cat >&2 <<EOF
检测到 staged 的 WPF/.xaml 改动尚未经 ${SKILL_NAME} 审查（或审查后内容又发生了变化）：
${staged_files}

请先调用 ${SKILL_NAME} 完成审查并修复问题，再执行：
  bash "${BASH_SOURCE[0]}" mark
标记通过后重新提交。
EOF
exit 2
