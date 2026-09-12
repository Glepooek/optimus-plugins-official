#!/usr/bin/env python3
"""校验 hooks.json 的配置与 Claude Code hook 契约是否相符。

只做**机械可判定**的检查——判据全部来自 knowledge-base/claude-code-hooks/，
每条报错都指向对应的索引条目，便于查完整判据。需要判断意图的事项
（事件选型是否恰当、additionalContext 措辞是否像系统指令）不在这里，
按 knowledge-base 的 enforcement=review 走人工评审。

挂在 .githooks/ 而非 skill 里，与 check_plugin_versions.py 同理：
Codex 侧走标准 git 流程读不到 skill 正文，写在那里的检查在 Codex 下不生效。
"""
import json
import pathlib
import re
import sys

# --- 事实表：全部来自官方 Hooks reference，核对日期 2026-09-12 ---
# 真源是 knowledge-base/claude-code-hooks/reference/event-capability-matrix.md，
# 这里是它的机器可读投影。官方增删事件时两处一起改。

KNOWN_EVENTS = {
    "SessionStart", "Setup", "SessionEnd", "UserPromptSubmit", "UserPromptExpansion",
    "Stop", "StopFailure", "PostToolBatch", "PreToolUse", "PostToolUse",
    "PostToolUseFailure", "PermissionRequest", "PermissionDenied", "Notification",
    "MessageDisplay", "SubagentStart", "SubagentStop", "TaskCreated", "TaskCompleted",
    "TeammateIdle", "InstructionsLoaded", "ConfigChange", "CwdChanged", "DirectoryAdded",
    "FileChanged", "WorktreeCreate", "WorktreeRemove", "PreCompact", "PostCompact",
    "PreModelSwitch", "PostModelSwitch", "Elicitation", "ElicitationResult",
}

# 不支持 matcher 的事件：写了会被静默忽略（claude-code-hooks.01.matcher-support）
NO_MATCHER = {
    "UserPromptSubmit", "PostToolBatch", "Stop", "TeammateIdle", "TaskCreated",
    "TaskCompleted", "WorktreeCreate", "WorktreeRemove", "MessageDisplay", "CwdChanged",
}

# 唯一会求值 `if` 的五个工具事件；其他事件上设了 if 的 hook 永不运行
# （claude-code-hooks.02.if-field）
TOOL_EVENTS = {
    "PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest",
    "PermissionDenied",
}

ALL_TYPES = {"command", "http", "mcp_tool", "prompt", "agent"}
THREE_TYPES = {"command", "http", "mcp_tool"}
TWO_TYPES = {"command", "mcp_tool"}

# handler 类型支持（claude-code-hooks.01.handler-support）
_FIVE_TYPE_EVENTS = {
    "PreToolUse", "PostToolUse", "PostToolUseFailure", "PostToolBatch",
    "PermissionRequest", "PermissionDenied", "Stop", "SubagentStop", "TaskCreated",
    "TaskCompleted", "TeammateIdle", "UserPromptSubmit", "UserPromptExpansion",
}
HANDLER_SUPPORT = {e: ALL_TYPES for e in _FIVE_TYPE_EVENTS}
HANDLER_SUPPORT.update({e: TWO_TYPES for e in ("SessionStart", "Setup")})
HANDLER_SUPPORT.update({
    e: THREE_TYPES for e in KNOWN_EVENTS
    if e not in _FIVE_TYPE_EVENTS and e not in ("SessionStart", "Setup")
})

# 这些事件本就丢弃/改道 systemMessage，故「async 让它不可见」在这里不是新增缺陷
# （claude-code-hooks.03.system-message-delivery）
DISCARDS_SYSTEM_MESSAGE = {
    "Setup", "InstructionsLoaded", "MessageDisplay", "Notification", "ConfigChange",
    "WorktreeCreate", "WorktreeRemove", "StopFailure", "CwdChanged", "FileChanged",
    "DirectoryAdded",
}

# 精确匹配字符集：只含这些字符的 matcher 按精确串比较，不走正则
EXACT_ONLY = re.compile(r"^[A-Za-z0-9_\-, |]*$")


def _resolve_script(command, hooks_json_path, repo_root):
    """把 command 里的路径占位符解析成实际文件路径；解析不出则返回 None。

    ${CLAUDE_PLUGIN_ROOT} 指向含该 hooks.json 的插件根（hooks/ 的上一级）。
    """
    m = re.search(r'\$\{?(CLAUDE_PLUGIN_ROOT|CLAUDE_PROJECT_DIR)\}?([^\s"\']*)', command)
    if not m:
        return None
    base = hooks_json_path.parent.parent if m.group(1) == "CLAUDE_PLUGIN_ROOT" else repo_root
    rel = m.group(2).lstrip("/\\")
    if not rel:
        return None
    target = base / rel
    return target if target.is_file() else None


def check_handler(event, handler, hooks_json_path, repo_root, matcher):
    """校验单个 hook handler，返回问题描述列表。"""
    problems = []
    where = f"{hooks_json_path.name} {event}"
    htype = handler.get("type")

    if htype not in ALL_TYPES:
        problems.append(
            f"[{where}] type 取值 {htype!r} 非法，应为 {sorted(ALL_TYPES)}")
        return problems

    allowed = HANDLER_SUPPORT.get(event, ALL_TYPES)
    if htype not in allowed:
        problems.append(
            f"[{where}] 该事件不支持 type={htype!r}，只支持 {sorted(allowed)}；"
            f"配了不支持的类型不报错，只是不生效"
            f"（判据 claude-code-hooks.01.handler-support）")

    if "if" in handler and event not in TOOL_EVENTS:
        problems.append(
            f"[{where}] 在非工具事件上设了 if，该 handler 永不运行"
            f"（判据 claude-code-hooks.02.if-field）")

    for field in ("async", "asyncRewake"):
        if handler.get(field) is not None and htype != "command":
            problems.append(
                f"[{where}] {field} 是 command handler 专有字段，"
                f"在 type={htype!r} 上不生效"
                f"（判据 claude-code-hooks.05.command-only）")

    if handler.get("async") is True and htype == "command":
        problems.extend(_check_async_visibility(event, handler, hooks_json_path,
                                                repo_root, where))

    if handler.get("shell") == "powershell":
        cmd = handler.get("command") or ""
        if re.search(r"\$CLAUDE_(PROJECT_DIR|PLUGIN_ROOT|PLUGIN_DATA)\b", cmd):
            problems.append(
                f"[{where}] PowerShell hook 里写了裸 $CLAUDE_* 占位符，"
                f"PowerShell 会解析成未定义局部变量并得 $null；"
                f"改用 $env:CLAUDE_* 或 ${{CLAUDE_*}}"
                f"（判据 claude-code-hooks.06.powershell-placeholder）")

    return problems


def _check_async_visibility(event, handler, hooks_json_path, repo_root, where):
    """async 的 hook 若产出 systemMessage，该输出只会给 Claude 而非用户。

    仅在能定位到脚本文件、且该事件在同步下本会展示 systemMessage 时才报——
    对本就丢弃 systemMessage 的事件（如 Notification），async 不改变可见性。
    """
    if event in DISCARDS_SYSTEM_MESSAGE:
        return []
    script = _resolve_script(handler.get("command") or "", hooks_json_path, repo_root)
    if script is None:
        return []
    try:
        body = script.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if "systemMessage" not in body:
        return []
    return [
        f"[{where}] async:true 但 {script.name} 输出 systemMessage——"
        f"异步 hook 的 systemMessage 只交付给 Claude，不展示给用户，"
        f"展示类输出会静默失效。改为 async:false，或把交付物改成副作用"
        f"（判据 claude-code-hooks.05.output-redirection）"
    ]


def check_matcher(event, matcher, hooks_json_path):
    """校验 matcher 取值，返回问题描述列表。"""
    problems = []
    where = f"{hooks_json_path.name} {event}"

    if matcher is None:
        return problems
    if not isinstance(matcher, str):
        return [f"[{where}] matcher 必须是字符串，实际是 {type(matcher).__name__}"]

    # 空串与 "*" 都是「匹配全部」的合法写法，等价于省略，不算误配
    if matcher not in ("", "*") and event in NO_MATCHER:
        problems.append(
            f"[{where}] 该事件不支持 matcher，{matcher!r} 会被静默忽略"
            f"（判据 claude-code-hooks.01.matcher-support）")

    # mcp__<server> 形态：只含精确字符集故按精确串比较，而真实工具名是
    # mcp__<server>__<tool>，因此永不匹配任何工具
    if matcher.startswith("mcp__") and EXACT_ONLY.match(matcher):
        if len(matcher.split("__")) == 2:
            problems.append(
                f"[{where}] matcher {matcher!r} 只含精确匹配字符，按精确串比较，"
                f"而工具名形如 mcp__<server>__<tool>，故永不匹配；"
                f"要匹配该 server 全部工具须写 {matcher}__.*"
                f"（判据 claude-code-hooks.02.matcher-evaluation）")

    return problems


def check_hooks_file(path, repo_root):
    """校验一个 hooks.json，返回问题描述列表。"""
    path = pathlib.Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"[{path}] 无法解析 JSON：{e}"]
    except OSError as e:
        return [f"[{path}] 无法读取：{e}"]

    events = data.get("hooks")
    if not isinstance(events, dict):
        return [f"[{path}] 缺顶层 hooks 对象"]

    problems = []
    for event, groups in events.items():
        if event not in KNOWN_EVENTS:
            problems.append(
                f"[{path.name}] 未知事件名 {event!r}——"
                f"事件名拼错时该 hook 永不触发且不报错")
            continue
        if not isinstance(groups, list):
            problems.append(f"[{path.name} {event}] 值必须是 matcher group 数组")
            continue
        for group in groups:
            if not isinstance(group, dict):
                problems.append(f"[{path.name} {event}] matcher group 必须是对象")
                continue
            matcher = group.get("matcher")
            problems.extend(check_matcher(event, matcher, path))
            handlers = group.get("hooks")
            if not isinstance(handlers, list):
                problems.append(
                    f"[{path.name} {event}] matcher group 缺 hooks 数组")
                continue
            for handler in handlers:
                if not isinstance(handler, dict):
                    problems.append(
                        f"[{path.name} {event}] handler 必须是对象")
                    continue
                problems.extend(
                    check_handler(event, handler, path, repo_root, matcher))
    return problems


def check_all(repo_root):
    """扫描 plugins/*/hooks/hooks.json 与 .claude/settings*.json，返回全部问题。"""
    repo_root = pathlib.Path(repo_root)
    targets = sorted(repo_root.glob("plugins/*/hooks/hooks.json"))
    for name in ("settings.json", "settings.local.json"):
        p = repo_root / ".claude" / name
        if p.is_file():
            targets.append(p)

    problems = []
    for t in targets:
        problems.extend(check_hooks_file(t, repo_root))
    return problems, len(targets)


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    problems, scanned = check_all(root)
    if problems:
        print("hook 配置校验未通过：")
        for p in problems:
            print(f"  - {p}")
        print("  完整判据见 knowledge-base/claude-code-hooks/")
        return 1
    print(f"hook 配置校验通过：已检查 {scanned} 个配置文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
