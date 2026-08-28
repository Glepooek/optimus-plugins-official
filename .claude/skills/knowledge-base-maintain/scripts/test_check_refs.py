import tempfile
import unittest
from pathlib import Path

from check_refs import (
    check_consumer,
    collect_consumers,
    extract_refs,
    normalize,
    parse_headings,
)


SPEC = """# 03 · MVVM 架构

## 1. MVVM 框架选型

## 2. ViewModel 基类与可绑定属性

### 2.1 属性变更通知

## 7. 事件与订阅
"""


class Fixture:
    """构造 <root>/knowledge-base/<domain>/rules|reference/ 与 <root>/plugins/... 的最小仓库结构。"""

    def __init__(self, tmp):
        self.root = Path(tmp)
        self.spec_dir = self.root / "knowledge-base" / "wpf" / "rules"
        self.spec_dir.mkdir(parents=True)
        (self.spec_dir / "03-mvvm.md").write_text(SPEC, encoding="utf-8")
        self.consumer_dir = self.root / "plugins" / "p" / "skills" / "s"
        self.consumer_dir.mkdir(parents=True)

    def consumer(self, body, name="SKILL.md"):
        path = self.consumer_dir / name
        path.write_text(body, encoding="utf-8")
        return path


class TestNormalize(unittest.TestCase):
    def test_strips_backticks_and_bold(self):
        self.assertEqual(normalize("**`var` 与对象创建**"), "var 与对象创建")

    def test_collapses_whitespace(self):
        self.assertEqual(normalize("  类型   与运算符 "), "类型 与运算符")


class TestParseHeadings(unittest.TestCase):
    def test_maps_number_to_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            headings = parse_headings(f.spec_dir / "03-mvvm.md")
            self.assertEqual(headings["1"], "MVVM 框架选型")
            self.assertEqual(headings["2"], "ViewModel 基类与可绑定属性")
            self.assertEqual(headings["2.1"], "属性变更通知")
            self.assertEqual(headings["7"], "事件与订阅")

    def test_ignores_h1_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            headings = parse_headings(f.spec_dir / "03-mvvm.md")
            self.assertNotIn("03", headings)


class TestExtractRefs(unittest.TestCase):
    def test_resolves_relative_path_via_file_level_domain(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("规范见 knowledge-base/wpf/00-README.md\n\n| `rules/03-mvvm.md` §2 |\n")
            refs = extract_refs(c, f.root)
            self.assertEqual(refs, [(3, "wpf", "rules/03-mvvm.md", "2", None)])

    def test_splits_multiple_files_on_one_line(self):
        """一行引用两个文件时，每个 § 必须归属到它前面的那个文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            (f.spec_dir / "04-xaml.md").write_text("# 04\n\n## 9. 事件与命令\n", encoding="utf-8")
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` §2；`rules/04-xaml.md` §9\n")
            refs = extract_refs(c, f.root)
            self.assertEqual([(r[2], r[3]) for r in refs],
                             [("rules/03-mvvm.md", "2"), ("rules/04-xaml.md", "9")])

    def test_captures_quoted_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` §7「事件与订阅」\n")
            self.assertEqual(extract_refs(c, f.root)[0][4], "事件与订阅")

    def test_captures_plain_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` § 7. 事件与订阅\n")
            self.assertEqual(extract_refs(c, f.root)[0][4], "事件与订阅")

    def test_range_form_yields_no_bogus_title(self):
        """§1-§5 的连字符不得被当成标题文本。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` §1-§2\n")
            self.assertEqual([r[4] for r in extract_refs(c, f.root)], [None, None])

    def test_bare_filename_uses_prior_file_dir_on_same_line(self):
        """同一行先出现完整路径、后用裸文件名省略写法时，裸名须归到前者所在目录。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            (f.spec_dir / "04-xaml.md").write_text("# 04\n\n## 9. 事件与命令\n", encoding="utf-8")
            c = f.consumer(
                "见 knowledge-base/wpf/rules/03-mvvm.md §2. ViewModel 基类；另见 `04-xaml.md` §9. 事件与命令\n")
            refs = extract_refs(c, f.root)
            self.assertEqual([r[2] for r in refs], ["rules/03-mvvm.md", "rules/04-xaml.md"])
            self.assertEqual(check_consumer(c, f.root)[0], [])

    def test_ambiguous_domain_skips_relative_refs(self):
        """一个文件引用了两个领域时，相对路径无法定基准，不猜。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md knowledge-base/csharp/00-README.md\n\n`rules/03-mvvm.md` §2\n")
            self.assertEqual(extract_refs(c, f.root), [])


class TestCheckConsumer(unittest.TestCase):
    def test_passes_when_number_and_title_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` § 7. 事件与订阅\n")
            problems, fragile = check_consumer(c, f.root)
            self.assertEqual((problems, fragile), ([], []))

    def test_detects_renumbered_section_via_title_mismatch(self):
        """核心场景：章节重编号后号仍存在，但标题对不上——必须报错。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` § 1. 事件与订阅\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(len(problems), 1)
            self.assertIn("标题不符", problems[0])
            self.assertIn("MVVM 框架选型", problems[0])

    def test_detects_missing_section_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` § 99. 不存在的章节\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(len(problems), 1)
            self.assertIn("无 § 99 章节", problems[0])

    def test_lists_existing_numbers_in_error(self):
        """报错须列出现有章节号，便于直接修复。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` § 99. x\n")
            problems, _ = check_consumer(c, f.root)
            self.assertIn("1, 2, 2.1, 7", problems[0])

    def test_detects_missing_target_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/99-gone.md` § 1. x\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(len(problems), 1)
            self.assertIn("引用的文件不存在", problems[0])

    def test_bare_number_reported_as_fragile_not_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` §2、§7\n")
            problems, fragile = check_consumer(c, f.root)
            self.assertEqual(problems, [])
            self.assertEqual(len(fragile), 2)
            self.assertIn("ViewModel 基类与可绑定属性", fragile[0])

    def test_title_prefix_match_accepted(self):
        """引用只写标题前半段（如省略括注）时视为匹配，避免逼迫逐字复制。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            (f.spec_dir / "06-controls.md").write_text(
                "# 06\n\n## 8. 绘制与图形（联动 08 章）\n", encoding="utf-8")
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/06-controls.md` § 8. 绘制与图形\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(problems, [])

    def test_subsection_number_checked_independently(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/00-README.md\n\n`rules/03-mvvm.md` § 2.1 属性变更通知\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(problems, [])


class TestCollectConsumers(unittest.TestCase):
    def test_finds_skill_and_reference_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            f.consumer("x")
            f.consumer("y", name="CLI-REFERENCE.md")
            names = {p.name for p in collect_consumers(f.root)}
            self.assertEqual(names, {"SKILL.md", "CLI-REFERENCE.md"})

    def test_ignores_changelog(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            f.consumer("x")
            f.consumer("历史记录里的 `rules/99-gone.md` § 1 不该被校验", name="CHANGELOG.md")
            names = {p.name for p in collect_consumers(f.root)}
            self.assertNotIn("CHANGELOG.md", names)


if __name__ == "__main__":
    unittest.main()
