import json
import pathlib
import shutil
import tempfile
import unittest

from check_hook_configs import check_all, check_hooks_file


def make_hooks(root, plugin, events, script_body=None, script_rel="hooks/s.sh"):
    """在临时仓库里造一个插件的 hooks.json，可选一并造出被引用的脚本。"""
    base = root / "plugins" / plugin / "hooks"
    base.mkdir(parents=True, exist_ok=True)
    path = base / "hooks.json"
    path.write_text(json.dumps({"hooks": events}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    if script_body is not None:
        target = root / "plugins" / plugin / script_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(script_body, encoding="utf-8")
    return path


def cmd(rel="hooks/s.sh"):
    return 'bash "${CLAUDE_PLUGIN_ROOT}/' + rel + '"'


class TestHookConfigChecks(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        (self.root / "plugins").mkdir()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # --- 应通过侧 ---

    def test_valid_config_passes(self):
        make_hooks(self.root, "p", {
            "PostToolUse": [{"matcher": "Edit|Write",
                             "hooks": [{"type": "command", "command": "echo ok"}]}],
        })
        self.assertEqual(check_all(self.root)[0], [])

    def test_sync_hook_emitting_system_message_passes(self):
        """同步 hook 输出 systemMessage 是正常用法，不该被拦。"""
        make_hooks(self.root, "p", {
            "SessionStart": [{"matcher": "", "hooks": [
                {"type": "command", "command": cmd(), "async": False}]}],
        }, script_body='echo \'{"systemMessage":"hi"}\'')
        self.assertEqual(check_all(self.root)[0], [])

    def test_async_on_event_that_discards_system_message_passes(self):
        """Notification 本就丢弃 systemMessage，async 不改变可见性，不该报。"""
        make_hooks(self.root, "p", {
            "Notification": [{"matcher": "permission_prompt", "hooks": [
                {"type": "command", "command": cmd(), "async": True}]}],
        }, script_body='echo \'{"systemMessage":"x"}\'')
        self.assertEqual(check_all(self.root)[0], [])

    def test_async_without_system_message_passes(self):
        """副作用型异步 hook 是 async 的正当用法。"""
        make_hooks(self.root, "p", {
            "PostToolUse": [{"matcher": "Write", "hooks": [
                {"type": "command", "command": cmd(), "async": True}]}],
        }, script_body="npm test >> /tmp/log")
        self.assertEqual(check_all(self.root)[0], [])

    def test_full_mcp_tool_name_as_exact_matcher_passes(self):
        """mcp__server__tool 是合法的精确工具名，不缺 .*。"""
        make_hooks(self.root, "p", {
            "PreToolUse": [{"matcher": "mcp__memory__create_entities",
                            "hooks": [{"type": "command", "command": "echo ok"}]}],
        })
        self.assertEqual(check_all(self.root)[0], [])

    def test_matcher_star_on_unsupported_event_passes(self):
        """"*" 与 "" 等价于省略，不算误配。"""
        make_hooks(self.root, "p", {
            "Stop": [{"matcher": "*",
                      "hooks": [{"type": "command", "command": "echo ok"}]}],
        })
        self.assertEqual(check_all(self.root)[0], [])

    # --- 应拦截侧 ---

    def test_async_with_system_message_is_reported(self):
        """本次事故的形态：SessionStart + async + systemMessage。"""
        make_hooks(self.root, "p", {
            "SessionStart": [{"matcher": "", "hooks": [
                {"type": "command", "command": cmd(), "async": True}]}],
        }, script_body='echo \'{"systemMessage":"tip"}\'')
        problems = check_all(self.root)[0]
        self.assertEqual(len(problems), 1)
        self.assertIn("async:true", problems[0])
        self.assertIn("claude-code-hooks.05.output-redirection", problems[0])

    def test_async_on_non_command_handler_is_reported(self):
        make_hooks(self.root, "p", {
            "PostToolUse": [{"matcher": "Write", "hooks": [
                {"type": "http", "url": "https://example.com/h", "async": True}]}],
        })
        problems = check_all(self.root)[0]
        self.assertTrue(any("command handler 专有字段" in p for p in problems))

    def test_unsupported_handler_type_is_reported(self):
        """SessionStart 不支持 http/prompt/agent。"""
        make_hooks(self.root, "p", {
            "SessionStart": [{"matcher": "", "hooks": [
                {"type": "http", "url": "https://example.com/h"}]}],
        })
        problems = check_all(self.root)[0]
        self.assertTrue(any("该事件不支持 type" in p for p in problems))

    def test_if_on_non_tool_event_is_reported(self):
        make_hooks(self.root, "p", {
            "SessionStart": [{"matcher": "", "hooks": [
                {"type": "command", "command": "echo x", "if": "Bash(git *)"}]}],
        })
        problems = check_all(self.root)[0]
        self.assertTrue(any("永不运行" in p for p in problems))

    def test_matcher_on_unsupported_event_is_reported(self):
        make_hooks(self.root, "p", {
            "Stop": [{"matcher": "Bash",
                      "hooks": [{"type": "command", "command": "echo x"}]}],
        })
        problems = check_all(self.root)[0]
        self.assertTrue(any("不支持 matcher" in p for p in problems))

    def test_mcp_server_matcher_missing_wildcard_is_reported(self):
        make_hooks(self.root, "p", {
            "PreToolUse": [{"matcher": "mcp__memory",
                            "hooks": [{"type": "command", "command": "echo x"}]}],
        })
        problems = check_all(self.root)[0]
        self.assertEqual(len(problems), 1)
        self.assertIn("mcp__memory__.*", problems[0])

    def test_unknown_event_name_is_reported(self):
        make_hooks(self.root, "p", {
            "SesionStart": [{"matcher": "",
                             "hooks": [{"type": "command", "command": "echo x"}]}],
        })
        problems = check_all(self.root)[0]
        self.assertTrue(any("未知事件名" in p for p in problems))

    def test_bare_placeholder_in_powershell_is_reported(self):
        make_hooks(self.root, "p", {
            "Notification": [{"matcher": "permission_prompt", "hooks": [
                {"type": "command", "shell": "powershell",
                 "command": "& $CLAUDE_PROJECT_DIR\\x.ps1"}]}],
        })
        problems = check_all(self.root)[0]
        self.assertTrue(any("裸 $CLAUDE_" in p for p in problems))

    def test_env_form_placeholder_in_powershell_passes(self):
        make_hooks(self.root, "p", {
            "Notification": [{"matcher": "permission_prompt", "hooks": [
                {"type": "command", "shell": "powershell",
                 "command": '& "$env:CLAUDE_PROJECT_DIR\\x.ps1"'}]}],
        })
        self.assertEqual(check_all(self.root)[0], [])

    # --- 作用域与健壮性 ---

    def test_scan_covers_all_plugins(self):
        make_hooks(self.root, "a", {
            "Stop": [{"matcher": "X", "hooks": [
                {"type": "command", "command": "echo x"}]}]})
        make_hooks(self.root, "b", {
            "Stop": [{"matcher": "Y", "hooks": [
                {"type": "command", "command": "echo y"}]}]})
        problems, scanned = check_all(self.root)
        self.assertEqual(scanned, 2)
        self.assertEqual(len(problems), 2)

    def test_malformed_json_is_reported_not_raised(self):
        base = self.root / "plugins" / "p" / "hooks"
        base.mkdir(parents=True)
        path = base / "hooks.json"
        path.write_text("{ not json", encoding="utf-8")
        problems = check_hooks_file(path, self.root)
        self.assertTrue(any("无法解析 JSON" in p for p in problems))

    def test_unresolvable_script_path_does_not_report_async(self):
        """脚本定位不到时不猜——宁可漏报也不误报。"""
        make_hooks(self.root, "p", {
            "SessionStart": [{"matcher": "", "hooks": [
                {"type": "command", "command": cmd("hooks/missing.sh"),
                 "async": True}]}],
        })
        self.assertEqual(check_all(self.root)[0], [])


if __name__ == "__main__":
    unittest.main()
