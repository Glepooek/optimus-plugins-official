import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from resolve_category import parse_catalog, find_tab, find_group, suggest_names, tab_candidate_names

SAMPLE_CATALOG = """\
## Tab 1 — Getting started（入口：`/overview`）

### Getting started
- [ ] Overview — `/overview`
- [ ] Quickstart — `/quickstart`

## Tab 2 — Build with Claude Code（对应有道笔记"使用ClaudeCode构建"，入口：`/agents`）

### Automation
- [x] Goals — `/goal`
- [ ] Launch sessions from links — `/deep-links`

### Guides
- [x] Monorepos and large repos — `/large-codebases`

### Plugin distribution（当前处理中，对应有道笔记"管理 / 插件分发"）
- [ ] Create and distribute a plugin marketplace — `/plugin-marketplaces`
"""


class TestParseCatalog(unittest.TestCase):
    def test_parses_all_tabs(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        self.assertEqual(len(tabs), 2)

    def test_tab_without_zh_annotation(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        self.assertEqual(tabs[0]["en"], "Getting started")
        self.assertIsNone(tabs[0]["zh"])

    def test_tab_with_zh_annotation(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        self.assertEqual(tabs[1]["en"], "Build with Claude Code")
        self.assertEqual(tabs[1]["zh"], "使用ClaudeCode构建")

    def test_group_with_trailing_annotation_still_parses_name(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        group_names = [g["en"] for g in tabs[1]["groups"]]
        self.assertIn("Plugin distribution", group_names)

    def test_parses_pages_under_group(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        guides = next(g for g in tabs[1]["groups"] if g["en"] == "Guides")
        self.assertEqual(
            guides["pages"],
            [{"title": "Monorepos and large repos", "url": "/large-codebases"}],
        )

    def test_parses_multiple_pages(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        automation = next(g for g in tabs[1]["groups"] if g["en"] == "Automation")
        self.assertEqual(len(automation["pages"]), 2)
        self.assertEqual(automation["pages"][0]["url"], "/goal")
        self.assertEqual(automation["pages"][1]["url"], "/deep-links")


class TestFindTab(unittest.TestCase):
    def test_find_by_english_name(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        tab = find_tab(tabs, {}, "Build with Claude Code")
        self.assertIsNotNone(tab)
        self.assertEqual(tab["en"], "Build with Claude Code")

    def test_find_by_chinese_name_from_catalog_annotation(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        tab = find_tab(tabs, {}, "使用ClaudeCode构建")
        self.assertIsNotNone(tab)
        self.assertEqual(tab["en"], "Build with Claude Code")

    def test_find_by_chinese_name_from_folder_map_alias(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        folder_map = {"tabs": {"入门": {"en": "Getting started"}}}
        tab = find_tab(tabs, folder_map, "入门")
        self.assertIsNotNone(tab)
        self.assertEqual(tab["en"], "Getting started")

    def test_not_found_returns_none(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        self.assertIsNone(find_tab(tabs, {}, "Nonexistent Tab"))


class TestFindGroup(unittest.TestCase):
    def test_find_existing_group(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        tab = find_tab(tabs, {}, "使用ClaudeCode构建")
        group = find_group(tab, "Guides")
        self.assertIsNotNone(group)
        self.assertEqual(len(group["pages"]), 1)

    def test_group_not_found_returns_none(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        tab = find_tab(tabs, {}, "使用ClaudeCode构建")
        self.assertIsNone(find_group(tab, "Nonexistent Group"))


from resolve_category import ensure_folder, load_folder_map, save_folder_map


class TestEnsureFolder(unittest.TestCase):
    @patch("resolve_category.youdaonote_mkdir")
    @patch("resolve_category.youdaonote_list")
    def test_reuses_existing_folder_without_creating(self, mock_list, mock_mkdir):
        mock_list.return_value = [("folder", "WEB123", "指南")]
        folder_id = ensure_folder("指南", "WEBparent")
        self.assertEqual(folder_id, "WEB123")
        mock_mkdir.assert_not_called()

    @patch("resolve_category.youdaonote_mkdir")
    @patch("resolve_category.youdaonote_list")
    def test_creates_when_missing_then_relists(self, mock_list, mock_mkdir):
        mock_list.side_effect = [[], [("folder", "WEB999", "指南")]]
        folder_id = ensure_folder("指南", "WEBparent")
        self.assertEqual(folder_id, "WEB999")
        mock_mkdir.assert_called_once_with("指南", "WEBparent")

    @patch("resolve_category.youdaonote_mkdir")
    @patch("resolve_category.youdaonote_list")
    def test_raises_if_still_missing_after_create(self, mock_list, mock_mkdir):
        mock_list.side_effect = [[], []]
        with self.assertRaises(RuntimeError):
            ensure_folder("指南", "WEBparent")


class TestFolderMapIO(unittest.TestCase):
    def test_load_missing_file_returns_empty_structure(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "nonexistent.json"
            result = load_folder_map(path)
            self.assertEqual(result, {"tabs": {}})

    def test_save_then_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "map.json"
            data = {"tabs": {"测试": {"id": "WEBabc"}}}
            save_folder_map(path, data)
            loaded = load_folder_map(path)
            self.assertEqual(loaded, data)

    def test_load_invalid_json_exits(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "broken.json"
            path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(SystemExit):
                load_folder_map(path)


class TestSuggestNames(unittest.TestCase):
    def test_suggests_close_match_for_typo(self):
        result = suggest_names("Guids", ["Guides", "Automation", "Plugins"])
        self.assertIn("Guides", result)

    def test_no_suggestion_when_nothing_close(self):
        result = suggest_names("完全不相关的名字", ["Guides", "Automation"])
        self.assertEqual(result, [])

    def test_limits_to_n_results(self):
        result = suggest_names("Guide", ["Guides", "Guidee", "Guided", "Guidex"], n=2)
        self.assertLessEqual(len(result), 2)


class TestTabCandidateNames(unittest.TestCase):
    def test_includes_english_and_chinese_annotation(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        names = tab_candidate_names(tabs, {})
        self.assertIn("Build with Claude Code", names)
        self.assertIn("使用ClaudeCode构建", names)

    def test_includes_folder_map_alias(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        folder_map = {"tabs": {"入门": {"en": "Getting started"}}}
        names = tab_candidate_names(tabs, folder_map)
        self.assertIn("入门", names)

    def test_dedupes_when_catalog_annotation_matches_folder_map_alias(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        folder_map = {"tabs": {"使用ClaudeCode构建": {"en": "Build with Claude Code"}}}
        names = tab_candidate_names(tabs, folder_map)
        self.assertEqual(names.count("使用ClaudeCode构建"), 1)


if __name__ == "__main__":
    unittest.main()
