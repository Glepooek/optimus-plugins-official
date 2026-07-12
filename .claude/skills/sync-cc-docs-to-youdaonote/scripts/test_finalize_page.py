import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from finalize_page import FinalizeError, extract_title, finalize


def fake_proc(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def make_fns(
    post_process_rc=0, verify_rc=0, verify_quality_rc=0,
    save_rc=0, before_ids=None, after_ids=None,
):
    before_ids = before_ids if before_ids is not None else {"OLD1"}
    after_ids = after_ids if after_ids is not None else before_ids | {"NEW1"}
    calls = {"list_call_count": 0}

    def list_fn(group_id):
        calls["list_call_count"] += 1
        ids = before_ids if calls["list_call_count"] == 1 else after_ids
        return [("note", i, f"title-{i}") for i in ids]

    saved_map = {}

    def load_map_fn(path):
        return saved_map.setdefault("data", {"tabs": {}})

    def save_map_fn(path, data):
        saved_map["data"] = data
        saved_map["saved"] = True

    fns = {
        "post_process_fn": lambda *a: fake_proc(post_process_rc, stderr="post_process failed" if post_process_rc else ""),
        "verify_fn": lambda *a: fake_proc(verify_rc, stderr="verify failed" if verify_rc else ""),
        "verify_quality_fn": lambda *a: fake_proc(verify_quality_rc, stderr="quality failed" if verify_quality_rc else ""),
        "list_fn": list_fn,
        "save_fn": lambda *a: fake_proc(save_rc, stderr="save failed" if save_rc else ""),
        "load_map_fn": load_map_fn,
        "save_map_fn": save_map_fn,
    }
    return fns, saved_map


class TestExtractTitle(unittest.TestCase):
    def test_extracts_first_heading(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "doc.md"
            p.write_text("intro line\n# Real Title\nmore text\n", encoding="utf-8")
            self.assertEqual(extract_title(p), "Real Title")

    def test_returns_none_when_no_heading(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "doc.md"
            p.write_text("no heading here\njust text\n", encoding="utf-8")
            self.assertIsNone(extract_title(p))

    def test_ignores_subheadings(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "doc.md"
            p.write_text("## Not this one\n# This one\n", encoding="utf-8")
            self.assertEqual(extract_title(p), "This one")


class TestFinalize(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.raw_path = Path(self.tmpdir.name) / "raw.md"
        self.translated_path = Path(self.tmpdir.name) / "translated.md"
        self.raw_path.write_text("原文内容\n", encoding="utf-8")
        self.translated_path.write_text("# 译文标题\n\n正文\n", encoding="utf-8")

    def test_happy_path_returns_summary_and_updates_map(self):
        fns, saved_map = make_fns()
        result = finalize(
            self.raw_path, self.translated_path, "GROUP1", "使用ClaudeCode构建", "Guides",
            "/some-page", **fns, map_path="fake-path", delete_raw=False,
        )
        self.assertEqual(result["fileId"], "NEW1")
        self.assertEqual(result["title"], "译文标题")
        self.assertTrue(saved_map["saved"])
        page = saved_map["data"]["tabs"]["使用ClaudeCode构建"]["groups"]["Guides"]["pages"]["/some-page"]
        self.assertEqual(page, {"title": "译文标题", "fileId": "NEW1"})

    def test_deletes_raw_file_on_success(self):
        fns, _ = make_fns()
        finalize(
            self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
            "/x", **fns, map_path="fake-path", delete_raw=True,
        )
        self.assertFalse(self.raw_path.exists())

    def test_post_process_failure_stops_before_verify(self):
        fns, saved_map = make_fns(post_process_rc=1)
        with self.assertRaises(FinalizeError):
            finalize(
                self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertNotIn("saved", saved_map)
        self.assertTrue(self.raw_path.exists())

    def test_verify_failure_stops_before_verify_quality(self):
        fns, saved_map = make_fns(verify_rc=1)
        with self.assertRaises(FinalizeError):
            finalize(
                self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertNotIn("saved", saved_map)

    def test_verify_quality_failure_stops_before_save(self):
        fns, saved_map = make_fns(verify_quality_rc=1)
        with self.assertRaises(FinalizeError):
            finalize(
                self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertNotIn("saved", saved_map)

    def test_missing_title_raises(self):
        self.translated_path.write_text("没有标题的正文\n", encoding="utf-8")
        fns, saved_map = make_fns()
        with self.assertRaises(FinalizeError):
            finalize(
                self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertNotIn("saved", saved_map)

    def test_explicit_title_overrides_extraction(self):
        fns, saved_map = make_fns()
        result = finalize(
            self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
            "/x", title="自定义标题", **fns, map_path="fake-path", delete_raw=False,
        )
        self.assertEqual(result["title"], "自定义标题")

    def test_save_command_failure_raises_and_does_not_update_map(self):
        fns, saved_map = make_fns(save_rc=1)
        with self.assertRaises(FinalizeError):
            finalize(
                self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertNotIn("saved", saved_map)
        self.assertTrue(self.raw_path.exists())

    def test_no_new_file_id_after_save_raises(self):
        fns, saved_map = make_fns(before_ids={"A"}, after_ids={"A"})
        with self.assertRaises(FinalizeError):
            finalize(
                self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertNotIn("saved", saved_map)

    def test_ambiguous_multiple_new_file_ids_raises(self):
        fns, saved_map = make_fns(before_ids={"A"}, after_ids={"A", "B", "C"})
        with self.assertRaises(FinalizeError):
            finalize(
                self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertNotIn("saved", saved_map)

    def test_missing_raw_file_raises_exit_code_2(self):
        fns, _ = make_fns()
        missing = Path(self.tmpdir.name) / "does-not-exist.md"
        with self.assertRaises(FinalizeError) as ctx:
            finalize(
                missing, self.translated_path, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertEqual(ctx.exception.exit_code, 2)

    def test_missing_translated_file_raises_exit_code_2(self):
        fns, _ = make_fns()
        missing = Path(self.tmpdir.name) / "does-not-exist.md"
        with self.assertRaises(FinalizeError) as ctx:
            finalize(
                self.raw_path, missing, "GROUP1", "Tab", "Group",
                "/x", **fns, map_path="fake-path", delete_raw=False,
            )
        self.assertEqual(ctx.exception.exit_code, 2)

    def test_preserves_existing_pages_in_same_group(self):
        fns, saved_map = make_fns()
        saved_map["data"] = {
            "tabs": {"Tab": {"groups": {"Group": {"pages": {"/existing": {"title": "T", "fileId": "OLD"}}}}}}
        }
        finalize(
            self.raw_path, self.translated_path, "GROUP1", "Tab", "Group",
            "/x", **fns, map_path="fake-path", delete_raw=False,
        )
        pages = saved_map["data"]["tabs"]["Tab"]["groups"]["Group"]["pages"]
        self.assertIn("/existing", pages)
        self.assertIn("/x", pages)


if __name__ == "__main__":
    unittest.main()
