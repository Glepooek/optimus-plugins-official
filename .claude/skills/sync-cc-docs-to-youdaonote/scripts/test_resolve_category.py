import unittest
from resolve_category import parse_catalog, find_tab, find_group

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


if __name__ == "__main__":
    unittest.main()
