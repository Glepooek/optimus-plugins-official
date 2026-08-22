import unittest
from check_index import normalize_heading, find_headings


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


if __name__ == "__main__":
    unittest.main()
