import json
import tempfile
import unittest
from pathlib import Path

from check_index import (
    check_anchor_exists,
    check_duplicate_ids,
    check_file_exists,
    find_headings,
    normalize_heading,
    parse_index_file,
    run_checks,
)


class TestNormalizeHeading(unittest.TestCase):
    def test_strips_hash_and_spaces(self):
        self.assertEqual(normalize_heading("## 1. 命名规范"), "1. 命名规范")

    def test_strips_backticks(self):
        self.assertEqual(normalize_heading("### 2.4 `var` 与对象创建"), "2.4 var 与对象创建")

    def test_collapses_extra_spaces(self):
        self.assertEqual(normalize_heading("#   1.  命名规范  "), "1. 命名规范")


class TestFindHeadings(unittest.TestCase):
    def test_finds_all_heading_levels(self):
        text = "# 标题\n正文\n## 二级\n### 三级\n非标题行 # 不是标题"
        self.assertEqual(find_headings(text), ["标题", "二级", "三级"])

    def test_empty_text_returns_empty_list(self):
        self.assertEqual(find_headings(""), [])


class TestParseIndexFile(unittest.TestCase):
    def test_parses_valid_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "index.jsonl"
            p.write_text(
                '{"id": "a.1", "kind": "rule"}\n{"id": "a.2", "kind": "reference"}\n',
                encoding="utf-8",
            )
            entries = parse_index_file(p)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["id"], "a.1")

    def test_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "index.jsonl"
            p.write_text('{"id": "a.1"}\n\n{"id": "a.2"}\n', encoding="utf-8")
            entries = parse_index_file(p)
            self.assertEqual(len(entries), 2)

    def test_raises_with_line_number_on_bad_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "index.jsonl"
            p.write_text('{"id": "a.1"}\n{not valid json}\n', encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_index_file(p)
            self.assertIn(":2:", str(ctx.exception))


class TestCheckFileExists(unittest.TestCase):
    def test_none_when_file_present(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "01-x.md").write_text("# 标题\n", encoding="utf-8")
            entry = {"id": "a.1", "file": "01-x.md"}
            self.assertIsNone(check_file_exists(domain_dir, entry))

    def test_message_when_file_missing(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            entry = {"id": "a.1", "file": "missing.md"}
            result = check_file_exists(domain_dir, entry)
            self.assertIsNotNone(result)
            self.assertIn("a.1", result)
            self.assertIn("missing.md", result)


class TestCheckAnchorExists(unittest.TestCase):
    def test_none_when_anchor_empty(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "01-x.md").write_text("# 标题\n", encoding="utf-8")
            entry = {"id": "a.1", "file": "01-x.md", "anchor": ""}
            self.assertIsNone(check_anchor_exists(domain_dir, entry))

    def test_none_when_anchor_matches_heading(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "01-x.md").write_text("# 标题\n## 1. 命名规范\n", encoding="utf-8")
            entry = {"id": "a.1", "file": "01-x.md", "anchor": "命名规范"}
            self.assertIsNone(check_anchor_exists(domain_dir, entry))

    def test_message_when_anchor_not_found(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "01-x.md").write_text("# 标题\n## 别的章节\n", encoding="utf-8")
            entry = {"id": "a.1", "file": "01-x.md", "anchor": "不存在的锚点"}
            result = check_anchor_exists(domain_dir, entry)
            self.assertIsNotNone(result)
            self.assertIn("a.1", result)


class TestCheckDuplicateIds(unittest.TestCase):
    def test_empty_when_all_unique(self):
        domain_entries = {"csharp": [{"id": "a.1"}, {"id": "a.2"}]}
        self.assertEqual(check_duplicate_ids(domain_entries), [])

    def test_detects_duplicate_within_domain(self):
        domain_entries = {"csharp": [{"id": "a.1"}, {"id": "a.1"}]}
        result = check_duplicate_ids(domain_entries)
        self.assertEqual(len(result), 1)
        self.assertIn("a.1", result[0])

    def test_detects_duplicate_across_domains(self):
        domain_entries = {"csharp": [{"id": "x.1"}], "wpf": [{"id": "x.1"}]}
        result = check_duplicate_ids(domain_entries)
        self.assertEqual(len(result), 1)


class TestRunChecks(unittest.TestCase):
    def test_no_problems_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            domain_dir = base / "csharp"
            domain_dir.mkdir()
            (domain_dir / "01-x.md").write_text("## 命名规范\n", encoding="utf-8")
            (domain_dir / "index.jsonl").write_text(
                json.dumps({"id": "csharp.1", "kind": "rule", "level": "MUST",
                            "file": "01-x.md", "anchor": "命名规范",
                            "title": "t", "tags": [], "summary": "s"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(run_checks(base, ["csharp"]), [])

    def test_collects_problems_from_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            domain_dir = base / "csharp"
            domain_dir.mkdir()
            (domain_dir / "index.jsonl").write_text(
                json.dumps({"id": "csharp.1", "kind": "rule", "file": "missing.md",
                            "anchor": "", "title": "t", "tags": [], "summary": "s"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            problems = run_checks(base, ["csharp"])
            self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main()
