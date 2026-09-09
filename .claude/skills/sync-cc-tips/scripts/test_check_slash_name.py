#!/usr/bin/env python3
"""check_slash_name.py 的单元测试。

    python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py"

扫描逻辑用构造的假二进制验证——不依赖本机 claude.exe 的具体版本，否则每次
Claude Code 升级都可能让单测无故变红。真实二进制的查证由 SKILL.md 流程承担。
"""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_slash_name as cs  # noqa: E402


def fake_binary(content, filler=0):
    """写一个假二进制。filler 为前置填充字节数，用于制造跨块边界场景。

    content 只用 ASCII——scan() 以 latin-1 解码字节流（这是为了让任意字节都能
    解码而不报错，不是为了正确还原文本），非 ASCII 字面量在这里没有意义。
    """
    f = tempfile.NamedTemporaryFile("wb", suffix=".exe", delete=False)
    if filler:
        f.write(b"x" * filler)
    f.write(content.encode("latin-1"))
    f.close()
    return f.name


class BinaryCase(unittest.TestCase):
    def make(self, content, filler=0):
        path = fake_binary(content, filler)
        self.addCleanup(os.unlink, path)
        return path


class TestDecide(unittest.TestCase):
    def test_agent_type_wins_over_name(self):
        """同时命中时判 subagent——statusline-setup 就是这种情况，不该写成斜杠命令。"""
        self.assertEqual(
            cs.decide({"name": ["name:\"x\""], "agentType": ["agentType:\"x\""]}),
            "subagent",
        )

    def test_name_only_is_command(self):
        self.assertEqual(cs.decide({"name": ["hit"], "agentType": []}), "command")

    def test_agent_type_only_is_subagent(self):
        self.assertEqual(cs.decide({"name": [], "agentType": ["hit"]}), "subagent")

    def test_neither_is_not_found(self):
        self.assertEqual(cs.decide({"name": [], "agentType": []}), "not_found")


class TestPatternRobustness(BinaryCase):
    """正则写窄会把「存在」误判成「不存在」，方向恰好是最危险的一侧。

    这组断言锁住窗口宽度与「不要求伴随字段紧邻」两条性质——曾用
    `name:"x",menuDescription`（要求紧邻）漏掉 `name:"doctor",aliases:[…]`。
    """

    def test_fields_between_name_and_marker_still_match(self):
        path = self.make('name:"doctor",aliases:["checkup"],isEnabled:()=>!0,menuDescription:"checkup"')
        payload, code = cs.check("doctor", path)
        self.assertEqual(code, 0)
        self.assertEqual(payload["verdict"], "command")
        self.assertIn("aliases", payload["evidence"][0]["registry_markers"])

    def test_marker_beyond_80_chars_still_found(self):
        """窗口 80 会漏掉 requires:{workspace:!0} 挡在前面的情况，故取 200。"""
        padding = "a" * 120
        path = self.make(f'name:"fewer-permission-prompts",requires:{{workspace:!0}},{padding},description:"x"')
        payload, _ = cs.check("fewer-permission-prompts", path)
        self.assertEqual(payload["verdict"], "command")
        self.assertIn("requires", payload["evidence"][0]["registry_markers"])

    def test_window_is_at_least_200(self):
        self.assertGreaterEqual(cs.WINDOW, 200, "窗口收窄会重现漏判")

    def test_no_hardcoded_obfuscated_function_name(self):
        """混淆名每次构建都可能变（no( → po(），写死等于埋一个静默失效。"""
        pats = cs.build_patterns("doctor")
        for key, pat in pats.items():
            self.assertTrue(
                pat.pattern.startswith(f"{key}:"),
                f"{key} 模式应以语义字段名开头，实际: {pat.pattern[:40]}",
            )

    def test_name_is_regex_escaped(self):
        """含正则元字符的名字不该被当成模式——虽然 CLI 已过滤，脚本层也要稳。"""
        path = self.make('name:"a.b"')
        payload, _ = cs.check("axb", path)
        self.assertEqual(payload["verdict"], "not_found", "`.` 不应匹配任意字符")

    def test_exact_name_match_not_prefix(self):
        """`doctor` 不该命中 `doctorate`——引号闭合保证了全名匹配。"""
        path = self.make('name:"doctorate",description:"x"')
        payload, _ = cs.check("doctor", path)
        self.assertEqual(payload["verdict"], "not_found")


class TestChunkBoundary(BinaryCase):
    """块间重叠保证跨边界的匹配不丢。二进制约 200MB，必须分块读。"""

    def test_match_spanning_chunk_boundary_is_found(self):
        with mock.patch.object(cs, "CHUNK", 1024):
            # 让匹配正好落在第一块尾部
            path = self.make('name:"spanning",description:"found"', filler=1000)
            payload, _ = cs.check("spanning", path)
        self.assertEqual(payload["verdict"], "command")

    def test_overlap_does_not_duplicate_hits(self):
        """重叠区的同一命中不该被计两次。"""
        with mock.patch.object(cs, "CHUNK", 1024):
            path = self.make('name:"once",description:"x"', filler=1010)
            payload, _ = cs.check("once", path)
        self.assertEqual(payload["hit_counts"]["name"], 1)


class TestEvidenceAndWarning(BinaryCase):
    """脚本只取证不下结论——evidence 必须带上下文原文供调用方判断。"""

    def test_evidence_carries_raw_context(self):
        path = self.make('name:"doctor",aliases:["checkup"]')
        payload, _ = cs.check("doctor", path)
        self.assertIn('name:"doctor"', payload["evidence"][0]["context"])
        self.assertEqual(payload["evidence"][0]["anchor"], "name:")

    def test_warns_when_no_registry_marker(self):
        """`name:"init"` 会命中 JS 解析器的无关字符串，须提示复查而非默认可信。"""
        path = self.make('name:"init"}}};var x=1;')
        payload, _ = cs.check("init", path)
        self.assertEqual(payload["verdict"], "command")
        self.assertIn("warning", payload)

    def test_no_warning_when_markers_present(self):
        path = self.make('name:"doctor",description:"health check"')
        payload, _ = cs.check("doctor", path)
        self.assertNotIn("warning", payload)

    def test_subagent_evidence_uses_agent_type_anchor(self):
        path = self.make('{agentType:"statusline-setup",whenToUse:"configure status line"')
        payload, _ = cs.check("statusline-setup", path)
        self.assertEqual(payload["verdict"], "subagent")
        self.assertEqual(payload["evidence"][0]["anchor"], "agentType:")

    def test_every_verdict_has_an_action(self):
        """四种 verdict 与 SKILL.md 原表四行处置一一对应，不能缺。"""
        self.assertEqual(
            set(cs.ACTIONS),
            {"command", "subagent", "not_found", "binary_missing"},
        )
        for v, a in cs.ACTIONS.items():
            self.assertTrue(a.strip(), f"{v} 缺处置建议")


class TestNotFoundAndMissingBinary(BinaryCase):
    def test_not_found_is_a_completed_check_not_an_error(self):
        """查不到也是查证完成，退出码 0——调用方据 verdict 决定措辞。"""
        path = self.make('name:"other",description:"x"')
        payload, code = cs.check("absent", path)
        self.assertEqual(code, 0)
        self.assertEqual(payload["verdict"], "not_found")
        self.assertIn("插件", payload["action"])

    def test_missing_binary_returns_5_with_hint(self):
        payload, code = cs.check("doctor", "/nonexistent/claude.exe")
        self.assertEqual(code, 5)
        self.assertEqual(payload["verdict"], "binary_missing")
        self.assertIn("Get-Command", payload["hint"])


class TestCli(BinaryCase):
    def test_strips_leading_slash(self):
        path = self.make('name:"doctor",description:"x"')
        with mock.patch("sys.stdout", io.StringIO()) as buf:
            code = cs.main(["check_slash_name.py", "/doctor", "--binary", path])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue())["name"], "doctor")

    def test_accepts_namespaced_name(self):
        """插件 skill 形如 /superpowers:tdd，冒号是合法字符。"""
        path = self.make('name:"superpowers:tdd",description:"x"')
        with mock.patch("sys.stdout", io.StringIO()) as buf:
            code = cs.main(["check_slash_name.py", "superpowers:tdd", "--binary", path])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue())["verdict"], "command")

    def test_rejects_illegal_chars(self):
        with mock.patch("sys.stderr", io.StringIO()) as err:
            code = cs.main(["check_slash_name.py", "foo bar"])
        self.assertEqual(code, 2)
        self.assertIn("只能含", err.getvalue())

    def test_rejects_empty_after_stripping_slash(self):
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(cs.main(["check_slash_name.py", "/"]), 2)

    def test_missing_binary_exit_code_propagates(self):
        with mock.patch("sys.stdout", io.StringIO()):
            code = cs.main(["check_slash_name.py", "doctor", "--binary", "/nope.exe"])
        self.assertEqual(code, 5)


if __name__ == "__main__":
    unittest.main()
