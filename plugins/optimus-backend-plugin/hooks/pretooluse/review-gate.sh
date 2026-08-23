#!/usr/bin/env bash
# PreToolUse 门禁：拦截 git commit，要求 staged 的 .cs 改动先经 csharp-code-review 审查。
# 用法：
#   review-gate.sh        默认检测模式，作为 PreToolUse hook 被调用（stdin 传入 hook JSON）
#   review-gate.sh mark   审查通过后，标记当前 staged .cs 内容为已审查

set -euo pipefail

MARK_DIR="$(git rev-parse --git-dir 2>/dev/null)/optimus-review-marks"
MARK_FILE="$MARK_DIR/csharp.hash"
SKILL_NAME="csharp-code-review"
PATTERN='*.cs'

current_hash() {
    git diff --cached -- "$PATTERN" | sha256sum | cut -d' ' -f1
}

if [[ "${1:-}" == "mark" ]]; then
    mkdir -p "$MARK_DIR"
    current_hash > "$MARK_FILE"
    echo "已标记当前 staged .cs 改动为审查通过。"
    exit 0
fi

# 检测模式：无 staged 的 .cs 改动，直接放行，不必关心当前命令是不是 git commit
staged_files="$(git diff --cached --name-only -- "$PATTERN")"
if [[ -z "$staged_files" ]]; then
    exit 0
fi

input="$(cat)"
command_text="$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))' 2>/dev/null || true)"
if [[ "$command_text" != *"git commit"* ]]; then
    exit 0
fi

hash_now="$(current_hash)"
hash_marked="$(cat "$MARK_FILE" 2>/dev/null || true)"

if [[ -n "$hash_marked" && "$hash_now" == "$hash_marked" ]]; then
    exit 0
fi

cat >&2 <<EOF
检测到 staged 的 C#/.cs 改动尚未经 ${SKILL_NAME} 审查（或审查后内容又发生了变化）：
${staged_files}

请先调用 ${SKILL_NAME} 完成审查并修复问题，再执行：
  bash "${BASH_SOURCE[0]}" mark
标记通过后重新提交。
EOF
exit 2
