#!/usr/bin/env python3
"""fetch_changelog.py 的单元测试。

本机无 pytest，用 unittest：
    python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py"

网络相关函数（fetch_one / probe）一律 mock——单测不依赖外网，也不该因
GitHub 抖动而变红。真实取数的验证由 SKILL.md 流程本身承担。
"""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetch_changelog as fc  # noqa: E402


SAMPLE = """# Changelog

## 2.1.270

- Added `--foo` flag for doing things
- Fixed a crash in bar

## 2.1.269

- Added GitLab support
  - nested line should not count as bullet
Some prose that is not a bullet.

## 2.1.268

- Removed the deprecated `--baz` flag
* Alternate bullet marker also counts

## 2.1.267

- Single item
"""


class TestParseVersions(unittest.TestCase):
    def test_extracts_all_versions_in_file_order(self):
        vs = fc.parse_versions(SAMPLE)
        self.assertEqual([v["v"] for v in vs], ["2.1.270", "2.1.269", "2.1.268", "2.1.267"])

    def test_collects_both_bullet_markers(self):
        vs = fc.parse_versions(SAMPLE)
        by = {v["v"]: v["bullets"] for v in vs}
        self.assertEqual(len(by["2.1.268"]), 2)
        self.assertIn("Alternate bullet marker also counts", by["2.1.268"])

    def test_ignores_prose_and_nested_lines(self):
        """散文不计入；缩进的嵌套行虽以 - 开头，仍属排版而非独立功能点。"""
        vs = fc.parse_versions(SAMPLE)
        by = {v["v"]: v["bullets"] for v in vs}
        self.assertEqual(by["2.1.269"], ["Added GitLab support", "nested line should not count as bullet"])
        self.assertNotIn("Some prose that is not a bullet.", by["2.1.269"])

    def test_bullets_before_first_version_are_dropped(self):
        vs = fc.parse_versions("- orphan bullet\n\n## 1.0.0\n\n- real\n")
        self.assertEqual(len(vs), 1)
        self.assertEqual(vs[0]["bullets"], ["real"])

    def test_no_version_marker_yields_empty(self):
        self.assertEqual(fc.parse_versions("<html>404</html>"), [])

    def test_rejects_non_semver_headings(self):
        """`## Unreleased` 之类不是版本，不能被当成版本段。"""
        vs = fc.parse_versions("## Unreleased\n\n- x\n\n## 2.0.0\n\n- y\n")
        self.assertEqual([v["v"] for v in vs], ["2.0.0"])


class TestTruncate(unittest.TestCase):
    def setUp(self):
        self.versions = fc.parse_versions(SAMPLE)

    def test_anchor_found_excludes_anchor_itself(self):
        """锚点版本上轮已处理，不能再出现在本轮结果里。"""
        sel, found = fc.truncate(self.versions, "2.1.268", None)
        self.assertTrue(found)
        self.assertEqual([v["v"] for v in sel], ["2.1.270", "2.1.269"])

    def test_anchor_is_latest_yields_empty(self):
        """锚点即最新版：0 个新版本，对应 SKILL.md 的「无新版本可处理」分支。"""
        sel, found = fc.truncate(self.versions, "2.1.270", None)
        self.assertTrue(found)
        self.assertEqual(sel, [])

    def test_anchor_not_found_returns_all_and_flags(self):
        sel, found = fc.truncate(self.versions, "9.9.9", None)
        self.assertFalse(found)
        self.assertEqual(len(sel), 4)

    def test_no_anchor_uses_default_window(self):
        with mock.patch.object(fc, "DEFAULT_WINDOW", 2):
            sel, found = fc.truncate(self.versions, None, None)
        self.assertIsNone(found)
        self.assertEqual([v["v"] for v in sel], ["2.1.270", "2.1.269"])

    def test_limit_overrides_anchor(self):
        """limit 模式忽略锚点，且不报告 anchor_found（本模式不查锚点）。"""
        sel, found = fc.truncate(self.versions, "2.1.268", 3)
        self.assertIsNone(found)
        self.assertEqual(len(sel), 3)

    def test_limit_larger_than_available_is_not_an_error(self):
        sel, _ = fc.truncate(self.versions, None, 999)
        self.assertEqual(len(sel), 4)


class TestReadAnchor(unittest.TestCase):
    def test_reads_and_strips(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("  2.1.268 \n")
            path = f.name
        try:
            self.assertEqual(fc.read_anchor(path), "2.1.268")
        finally:
            os.unlink(path)

    def test_missing_file_is_none_not_error(self):
        """首次运行时文件不存在是正常状态，不该报错。"""
        self.assertIsNone(fc.read_anchor("/nonexistent/path/anchor"))

    def test_empty_file_is_none(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("\n  \n")
            path = f.name
        try:
            self.assertIsNone(fc.read_anchor(path))
        finally:
            os.unlink(path)


class TestHopsAreIndependent(unittest.TestCase):
    """降级的全部意义在于换主机名。这组断言锁住该性质，防止再退回「换工具不换主机」。"""

    def test_all_hops_have_distinct_hosts(self):
        hosts = [h["host"] for h in fc.HOPS]
        self.assertEqual(len(hosts), len(set(hosts)), f"存在同主机跳: {hosts}")

    def test_no_hop_targets_a_redirecting_url(self):
        """`github.com/<repo>/raw/<file>` 返 302 回落 raw 域，不构成独立跳。"""
        for hop in fc.HOPS:
            self.assertNotIn("/raw/", hop["url"], f"{hop['name']} 指向会重定向的 raw 路径")

    def test_api_hop_carries_raw_accept_header(self):
        """少了这个头，contents API 返 JSON 包装而非文件正文，解析必然失败。"""
        api = next(h for h in fc.HOPS if h["name"] == "api")
        self.assertEqual(api["headers"].get("Accept"), "application/vnd.github.raw")

    def test_diagnosis_includes_a_control_host(self):
        """分诊必须有对照组，否则无法区分全局断网与单主机阻断。"""
        self.assertIn("example.com", fc.DIAG_HOSTS)


class TestRunDegradation(unittest.TestCase):
    def _anchor_file(self, content):
        f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_first_hop_success_does_not_try_second(self):
        with mock.patch.object(fc, "fetch_one", side_effect=[SAMPLE]) as m:
            payload, code = fc.run(anchor_file="/nonexistent", limit=None)
        self.assertEqual(code, 0)
        self.assertEqual(payload["hop"], "raw")
        self.assertEqual(payload["hops_failed"], [])
        self.assertEqual(m.call_count, 1)

    def test_falls_through_to_api_when_raw_fails(self):
        with mock.patch.object(fc, "fetch_one", side_effect=[None, SAMPLE]) as m:
            payload, code = fc.run(anchor_file="/nonexistent", limit=None)
        self.assertEqual(code, 0)
        self.assertEqual(payload["hop"], "api")
        self.assertEqual(payload["hops_failed"], ["raw"])
        self.assertEqual(m.call_count, 2)

    def test_both_hops_fail_single_host_blocked_routes_to_webfetch(self):
        diag = {"raw.githubusercontent.com": "000", "api.github.com": "200", "example.com": "200"}
        with mock.patch.object(fc, "fetch_one", return_value=None), \
             mock.patch.object(fc, "probe", side_effect=lambda h, **kw: diag[h]):
            payload, code = fc.run(anchor_file="/nonexistent", limit=None)
        self.assertEqual(code, 3)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["verdict"], "single_host_blocked")
        self.assertEqual(payload["next"], "webfetch")
        self.assertEqual(payload["hops_failed"], ["raw", "api"])

    def test_network_down_routes_to_stop_not_webfetch(self):
        """全局断网时 WebFetch 同样走网络，再试一次没有价值。"""
        with mock.patch.object(fc, "fetch_one", return_value=None), \
             mock.patch.object(fc, "probe", return_value="000"):
            payload, code = fc.run(anchor_file="/nonexistent", limit=None)
        self.assertEqual(code, 3)
        self.assertEqual(payload["verdict"], "network_down")
        self.assertEqual(payload["next"], "stop")

    def test_html_error_page_is_parse_failure_not_fetch_failure(self):
        """取到内容但无版本标记 → 解析失败（exit 4），与取数失败（exit 3）分开。"""
        with mock.patch.object(fc, "fetch_one", return_value="<html>404</html>"):
            payload, code = fc.run(anchor_file="/nonexistent", limit=None)
        self.assertEqual(code, 4)
        self.assertEqual(payload["verdict"], "parse_failed")
        self.assertEqual(payload["next"], "stop")
        self.assertIn("404", payload["head"])


class TestNeedsConfirm(unittest.TestCase):
    """needs_confirm 只看版本数，不看锚点是否命中。

    上一版把判据写成「锚点未找到 且 >30」，那是 awk 实现的视角残留（跑到文件末尾
    都没 exit 才输出全部）。实测证伪：锚点 1.0.0 在真实 CHANGELOG 里存在，截断后
    仍有 351 个版本待处理——范围过大本身就是确认的理由。
    """

    def _many(self, n):
        return "\n".join(f"## 2.1.{300 - i}\n\n- item {i}\n" for i in range(n))

    def test_over_threshold_confirms_even_when_anchor_found(self):
        text = self._many(40) + "\n## 1.0.0\n\n- old\n"
        with mock.patch.object(fc, "fetch_one", return_value=text), \
             mock.patch.object(fc, "read_anchor", return_value="1.0.0"):
            payload, _ = fc.run(limit=None)
        self.assertTrue(payload["anchor_found"], "前提：锚点确实找到了")
        self.assertEqual(payload["version_count"], 40)
        self.assertTrue(payload["needs_confirm"])

    def test_over_threshold_confirms_when_anchor_missing(self):
        with mock.patch.object(fc, "fetch_one", return_value=self._many(40)), \
             mock.patch.object(fc, "read_anchor", return_value="9.9.9"):
            payload, _ = fc.run(limit=None)
        self.assertFalse(payload["anchor_found"])
        self.assertTrue(payload["needs_confirm"])

    def test_under_threshold_does_not_confirm(self):
        with mock.patch.object(fc, "fetch_one", return_value=self._many(5)), \
             mock.patch.object(fc, "read_anchor", return_value="9.9.9"):
            payload, _ = fc.run(limit=None)
        self.assertFalse(payload["needs_confirm"])

    def test_limit_mode_never_confirms(self):
        """用户显式给了 N，那就是他要的范围，不必再问。"""
        with mock.patch.object(fc, "fetch_one", return_value=self._many(40)):
            payload, _ = fc.run(anchor_file="/nonexistent", limit=40)
        self.assertFalse(payload["needs_confirm"])


class TestAdvanceAnchor(unittest.TestCase):
    """limit 模式是范围受限的临时查看，不代表真实同步进度，不得推进锚点。"""

    def test_normal_mode_advances(self):
        with mock.patch.object(fc, "fetch_one", return_value=SAMPLE):
            payload, _ = fc.run(anchor_file="/nonexistent", limit=None)
        self.assertTrue(payload["advance_anchor"])

    def test_limit_mode_does_not_advance(self):
        with mock.patch.object(fc, "fetch_one", return_value=SAMPLE):
            payload, _ = fc.run(anchor_file="/nonexistent", limit=2)
        self.assertFalse(payload["advance_anchor"])

    def test_limit_mode_ignores_anchor_file_entirely(self):
        """limit 模式下不该去读锚点文件——读了就有按锚点截断的风险。"""
        with mock.patch.object(fc, "fetch_one", return_value=SAMPLE), \
             mock.patch.object(fc, "read_anchor") as m:
            payload, _ = fc.run(limit=2)
        m.assert_not_called()
        self.assertIsNone(payload["anchor"])


class TestPayloadShape(unittest.TestCase):
    def test_range_is_oldest_to_newest(self):
        """摘要要展示 v旧 → v新，顺序不能反。"""
        with mock.patch.object(fc, "fetch_one", return_value=SAMPLE):
            payload, _ = fc.run(anchor_file="/nonexistent", limit=None)
        self.assertEqual(payload["range"], ["2.1.267", "2.1.270"])

    def test_empty_selection_has_null_range(self):
        with mock.patch.object(fc, "fetch_one", return_value=SAMPLE), \
             mock.patch.object(fc, "read_anchor", return_value="2.1.270"):
            payload, code = fc.run(limit=None)
        self.assertEqual(code, 0)
        self.assertEqual(payload["version_count"], 0)
        self.assertIsNone(payload["range"])
        self.assertEqual(payload["latest_available"], "2.1.270")

    def test_bullet_count_sums_selected_only(self):
        with mock.patch.object(fc, "fetch_one", return_value=SAMPLE), \
             mock.patch.object(fc, "read_anchor", return_value="2.1.268"):
            payload, _ = fc.run(limit=None)
        self.assertEqual(payload["bullet_count"], 4)

    def test_output_is_valid_json(self):
        buf = io.StringIO()
        with mock.patch.object(fc, "fetch_one", return_value=SAMPLE), \
             mock.patch("sys.stdout", buf):
            code = fc.main(["fetch_changelog.py", "--anchor-file", "/nonexistent"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(buf.getvalue())["ok"])


class TestCli(unittest.TestCase):
    def test_limit_zero_is_rejected_with_code_2(self):
        buf = io.StringIO()
        with mock.patch("sys.stderr", buf):
            code = fc.main(["fetch_changelog.py", "--limit", "0"])
        self.assertEqual(code, 2)
        self.assertIn("≥ 1", buf.getvalue())

    def test_negative_limit_is_rejected(self):
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(fc.main(["fetch_changelog.py", "--limit", "-5"]), 2)


if __name__ == "__main__":
    unittest.main()
