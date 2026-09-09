#!/usr/bin/env python3
"""validate_tips.py 的单元测试。

    python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py"
"""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validate_tips as vt  # noqa: E402


def entry(id_="/x", category="[CLI]", title="标题", body="功能：做事\n效果：有用\n例子：claude --x"):
    return {"id": id_, "category": category, "title": title, "body": body}


def write_jsonl(rows):
    """把若干 dict（或裸字符串行）写成临时 jsonl，返回路径。"""
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8", newline="\n")
    for r in rows:
        f.write(r if isinstance(r, str) else json.dumps(r, ensure_ascii=False))
        f.write("\n")
    f.close()
    return f.name


class JsonlCase(unittest.TestCase):
    def make(self, rows):
        path = write_jsonl(rows)
        self.addCleanup(os.unlink, path)
        return path


class TestLoadAndLineCount(JsonlCase):
    def test_clean_file_passes(self):
        entries, lc, jv = vt.load(self.make([entry("/a"), entry("/b")]))
        self.assertEqual(len(entries), 2)
        self.assertTrue(lc["ok"])
        self.assertTrue(jv["ok"])

    def test_blank_lines_are_skipped_not_counted(self):
        """空行不计入总数——文件末尾换行是正常的，不该判成格式破损。"""
        path = self.make([entry("/a"), "", entry("/b")])
        entries, lc, _ = vt.load(path)
        self.assertEqual(len(entries), 2)
        self.assertTrue(lc["ok"])

    def test_non_brace_line_fails_line_count(self):
        path = self.make([entry("/a"), "not json at all"])
        _, lc, _ = vt.load(path)
        self.assertFalse(lc["ok"])
        self.assertEqual(lc["json_lines"], 1)
        self.assertEqual(lc["total_lines"], 2)
        self.assertIn("hint", lc)

    def test_malformed_json_reported_not_raised(self):
        """JSON 非法是要报告的检查结果，抛异常会让调用方拿不到其余结论。"""
        path = self.make([entry("/a"), '{"id":"/b","broken":}'])
        entries, _, jv = vt.load(path)
        self.assertFalse(jv["ok"])
        self.assertEqual(jv["errors"][0]["line"], 2)
        self.assertEqual(len(entries), 1, "合法行仍应被解析出来")


class TestFieldDup(JsonlCase):
    """「功能」「效果」各恰好 1 次；「例子」不参与计数。

    后半条是 1.4.0 为修 --add-dir 被误判所加的有意例外。用「字段段数 > 4 即报错」
    替代本检查会误伤分平台多行写法——这组断言就是防止那次回退。
    """

    def _run(self, body):
        payload, _ = vt.validate(self.make([entry(body=body)]))
        return payload["checks"]["field_dup"]

    def test_normal_body_passes(self):
        self.assertTrue(self._run("功能：做事\n效果：有用\n例子：claude --x")["ok"])

    def test_duplicate_gongneng_fails(self):
        r = self._run("功能：一\n功能：二\n效果：有用\n例子：claude --x")
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["field"], "功能")
        self.assertEqual(r["errors"][0]["n"], 2)

    def test_duplicate_xiaoguo_fails(self):
        r = self._run("功能：做事\n效果：一\n效果：二\n例子：claude --x")
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["field"], "效果")

    def test_missing_gongneng_fails_with_zero(self):
        r = self._run("效果：有用\n例子：claude --x")
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["n"], 0)

    def test_multiple_liji_lines_are_allowed(self):
        """分平台多行例子是有意保留的合法写法，不得报错。"""
        r = self._run(
            "功能：做事\n效果：有用\n"
            "例子（Windows）：claude --w\n例子（Linux/Mac）：claude --l"
        )
        self.assertTrue(r["ok"], "多行例子被误判为字段重复")

    def test_three_liji_lines_still_allowed(self):
        r = self._run("功能：做事\n效果：有用\n例子（A）：a\n例子（B）：b\n例子（C）：c")
        self.assertTrue(r["ok"])

    def test_section_word_inside_line_is_not_counted(self):
        """按行首匹配：正文中间提到「效果：」不算一个段落。"""
        r = self._run("功能：做事\n效果：见下文的效果：说明\n例子：claude --x")
        self.assertTrue(r["ok"])


class TestBodyShape(JsonlCase):
    def _run(self, body):
        payload, _ = vt.validate(self.make([entry(body=body)]))
        return payload["checks"]["body_shape"]

    def test_all_three_sections_pass(self):
        self.assertTrue(self._run("功能：做事\n效果：有用\n例子：claude --x")["ok"])

    def test_missing_liji_fails(self):
        r = self._run("功能：做事\n效果：有用")
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["missing"], ["例子"])

    def test_liji_with_platform_suffix_counts_as_present(self):
        """「例子」按行首匹配，不要求与「：」紧邻——否则分平台写法会被判缺字段。"""
        self.assertTrue(self._run("功能：做事\n效果：有用\n例子（Windows）：claude --w")["ok"])

    def test_reports_all_missing_sections(self):
        r = self._run("只有一句话，没有任何段落")
        self.assertEqual(r["errors"][0]["missing"], ["功能", "效果", "例子"])


class TestSchemaAndIdUnique(JsonlCase):
    def test_missing_field_fails(self):
        row = entry("/a")
        del row["category"]
        payload, _ = vt.validate(self.make([row]))
        r = payload["checks"]["schema"]
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["missing"], ["category"])

    def test_blank_field_counts_as_missing(self):
        payload, _ = vt.validate(self.make([entry(title="   ")]))
        self.assertFalse(payload["checks"]["schema"]["ok"])

    def test_duplicate_id_fails_with_both_lines(self):
        payload, _ = vt.validate(self.make([entry("/dup"), entry("/other"), entry("/dup")]))
        r = payload["checks"]["id_unique"]
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["id"], "/dup")
        self.assertEqual(r["errors"][0]["lines"], [1, 3])

    def test_unique_ids_pass(self):
        payload, _ = vt.validate(self.make([entry("/a"), entry("/b")]))
        self.assertTrue(payload["checks"]["id_unique"]["ok"])


class TestLength(JsonlCase):
    """length 恒为 ok——超阈值是待判断信息，不是缺陷。

    长度自检约束改动增量（本轮有没有把某条推超），不是全库门禁。按全库状态阻断
    会让每轮同步被无关存量卡住：2026-09-09 实测 268 条中 20 条超阈值，18 条属存量。
    """

    def test_over_threshold_does_not_fail(self):
        rows = [entry(f"/s{i}", body="功能：短\n效果：短\n例子：a") for i in range(5)]
        rows.append(entry("/long", body="功能：" + "长" * 500 + "\n效果：有用\n例子：a"))
        payload, ok = vt.validate(self.make(rows))
        self.assertTrue(payload["checks"]["length"]["ok"], "length 不该判失败")
        self.assertNotIn("length", payload["failed"])
        self.assertTrue(ok, "仅长度超标不应让总判定失败")

    def test_reports_over_entries_sorted_desc(self):
        rows = [entry(f"/s{i}", body="功能：短\n效果：短\n例子：a") for i in range(5)]
        rows.append(entry("/mid", body="功能：" + "长" * 200 + "\n效果：a\n例子：a"))
        rows.append(entry("/max", body="功能：" + "长" * 500 + "\n效果：a\n例子：a"))
        payload, _ = vt.validate(self.make(rows))
        r = payload["checks"]["length"]
        self.assertEqual(r["over_count"], 2)
        self.assertEqual([x["id"] for x in r["over"]], ["/max", "/mid"], "应按长度降序")

    def test_threshold_is_median_times_multiplier(self):
        rows = [entry(f"/s{i}", body="x" * 100) for i in range(3)]
        payload, _ = vt.validate(self.make(rows))
        r = payload["checks"]["length"]
        self.assertEqual(r["median"], 100.0)
        self.assertEqual(r["threshold"], 100.0 * vt.LENGTH_MULTIPLIER)

    def test_empty_file_skips_gracefully(self):
        payload, _ = vt.validate(self.make([]))
        self.assertTrue(payload["checks"]["length"]["ok"])
        self.assertIn("skipped", payload["checks"]["length"])


class TestOrphanRef(JsonlCase):
    def test_skipped_when_no_removed_ids(self):
        payload, _ = vt.validate(self.make([entry("/a")]))
        r = payload["checks"]["orphan_ref"]
        self.assertTrue(r["ok"])
        self.assertEqual(r["skipped"], "本轮无删除")

    def test_detects_reference_in_body(self):
        rows = [
            entry("/keep", body="功能：做事\n效果：配合 --gone 使用\n例子：a"),
            entry("--gone", body="功能：旧\n效果：旧\n例子：a"),
        ]
        payload, ok = vt.validate(self.make(rows), removed_ids=["--gone"])
        r = payload["checks"]["orphan_ref"]
        self.assertFalse(r["ok"])
        self.assertFalse(ok)
        self.assertEqual(r["hits"][0]["referrer"], "/keep")
        self.assertEqual(r["hits"][0]["removed_id"], "--gone")

    def test_detects_reference_in_title(self):
        rows = [entry("/keep", title="替代 --gone 的新写法"), entry("--gone")]
        payload, _ = vt.validate(self.make(rows), removed_ids=["--gone"])
        self.assertFalse(payload["checks"]["orphan_ref"]["ok"])

    def test_self_mention_is_not_an_orphan_ref(self):
        """被删条目自身提到自己的标识符，不算悬空引用。"""
        rows = [entry("--gone", body="功能：旧\n效果：用 --gone\n例子：claude --gone")]
        payload, _ = vt.validate(self.make(rows), removed_ids=["--gone"])
        self.assertTrue(payload["checks"]["orphan_ref"]["ok"])

    def test_no_reference_passes(self):
        rows = [entry("/clean"), entry("--gone")]
        payload, _ = vt.validate(self.make(rows), removed_ids=["--gone"])
        self.assertTrue(payload["checks"]["orphan_ref"]["ok"])


class TestCountMatch(JsonlCase):
    def test_skipped_when_not_provided(self):
        payload, _ = vt.validate(self.make([entry("/a")]))
        self.assertIn("skipped", payload["checks"]["count_match"])

    def test_match_passes(self):
        payload, ok = vt.validate(self.make([entry("/a"), entry("/b")]), expect_entries=2)
        self.assertTrue(payload["checks"]["count_match"]["ok"])
        self.assertTrue(ok)

    def test_mismatch_reports_delta(self):
        payload, ok = vt.validate(self.make([entry("/a")]), expect_entries=3)
        r = payload["checks"]["count_match"]
        self.assertFalse(r["ok"])
        self.assertFalse(ok)
        self.assertEqual(r["delta"], -2)


class TestCli(unittest.TestCase):
    def test_missing_file_returns_2(self):
        with mock.patch("sys.stderr", io.StringIO()) as err:
            code = vt.main(["validate_tips.py", "/nonexistent/tips.jsonl"])
        self.assertEqual(code, 2)
        self.assertIn("无法读取", err.getvalue())

    def test_clean_file_returns_0(self):
        path = write_jsonl([entry("/a")])
        self.addCleanup(os.unlink, path)
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            code = vt.main(["validate_tips.py", path])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(buf.getvalue())["ok"])

    def test_failing_file_returns_1(self):
        path = write_jsonl([entry("/a", body="功能：一\n功能：二\n效果：a\n例子：a")])
        self.addCleanup(os.unlink, path)
        with mock.patch("sys.stdout", io.StringIO()) as buf:
            code = vt.main(["validate_tips.py", path])
        self.assertEqual(code, 1)
        self.assertIn("field_dup", json.loads(buf.getvalue())["failed"])

    def test_removed_ids_parsed_from_comma_list(self):
        path = write_jsonl([entry("/keep", body="功能：a\n效果：用 /old 和 /gone\n例子：a")])
        self.addCleanup(os.unlink, path)
        with mock.patch("sys.stdout", io.StringIO()) as buf:
            code = vt.main(["validate_tips.py", path, "--removed-ids", "/old,/gone"])
        self.assertEqual(code, 1)
        hits = json.loads(buf.getvalue())["checks"]["orphan_ref"]["hits"]
        self.assertEqual(len(hits), 2)

    def test_blank_entries_in_removed_ids_are_ignored(self):
        """`--removed-ids "/a,,"` 里的空段不该变成匹配任何东西的空串。"""
        path = write_jsonl([entry("/keep")])
        self.addCleanup(os.unlink, path)
        with mock.patch("sys.stdout", io.StringIO()) as buf:
            code = vt.main(["validate_tips.py", path, "--removed-ids", "/nothere,,"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue())["checks"]["orphan_ref"]["checked"], ["/nothere"])


if __name__ == "__main__":
    unittest.main()
