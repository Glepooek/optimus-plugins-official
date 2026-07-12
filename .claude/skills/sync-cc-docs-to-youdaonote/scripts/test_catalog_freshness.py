import unittest
from resolve_category import parse_catalog
from catalog_freshness import (
    apply_record_check,
    build_index,
    build_tab_patch,
    compute_apply,
    compute_diff,
    compute_freshness,
    find_unverified_tabs,
    flatten_synced_pages,
    locate_tab_blocks,
    reconstruct,
    scan_tab_block,
)

DAY = 86400
NOW_BASE = 1_752_300_000  # 一个真实量级的 epoch（2026 年前后），避免 Windows 下负数/过小 epoch 触发 OSError

SAMPLE_CATALOG = """\
# 示例站点导航

> 示例说明文字

## Tab 1 — Getting started（入口：`/overview`）

### Getting started
- [ ] Overview — `/overview`
- [x] Quickstart — `/quickstart`

### Core concepts
- [ ] Concept A — `/concept-a`
- [ ] Concept B — `/concept-b`

---

## Tab 2 — Build（对应有道笔记"构建"，入口：`/agents`）

### MCP
- [x] Reference — `/mcp`（已存：mcp.md）

---

## 已知缺口 / 待核实项

1. 一些说明文字，不属于任何 Tab。
"""


class TestComputeFreshness(unittest.TestCase):
    def test_never_checked_when_meta_empty(self):
        result = compute_freshness({}, now=NOW_BASE, threshold_days=14)
        self.assertEqual(result["status"], "never_checked")
        self.assertIsNone(result["days_since_verified"])

    def test_fresh_within_threshold(self):
        now = NOW_BASE
        meta = {"last_verified_epoch": now - 5 * DAY}
        result = compute_freshness(meta, now, threshold_days=14)
        self.assertEqual(result["status"], "fresh")
        self.assertEqual(result["days_since_verified"], 5)

    def test_stale_exactly_at_threshold(self):
        now = NOW_BASE
        meta = {"last_verified_epoch": now - 14 * DAY}
        result = compute_freshness(meta, now, threshold_days=14)
        self.assertEqual(result["status"], "stale")

    def test_stale_beyond_threshold(self):
        now = NOW_BASE
        meta = {"last_verified_epoch": now - 30 * DAY}
        result = compute_freshness(meta, now, threshold_days=14)
        self.assertEqual(result["status"], "stale")

    def test_recently_prompted_overrides_stale(self):
        """哪怕已经过期，24 小时内问过一次就不再重复打扰。"""
        now = NOW_BASE
        meta = {
            "last_verified_epoch": now - 30 * DAY,
            "last_prompted_epoch": now - 3600,
        }
        result = compute_freshness(meta, now, threshold_days=14)
        self.assertEqual(result["status"], "recently_prompted")

    def test_prompted_over_24h_ago_does_not_suppress(self):
        now = NOW_BASE
        meta = {
            "last_verified_epoch": now - 30 * DAY,
            "last_prompted_epoch": now - 2 * DAY,
        }
        result = compute_freshness(meta, now, threshold_days=14)
        self.assertEqual(result["status"], "stale")

    def test_unverified_tabs_passed_through(self):
        result = compute_freshness({"unverified_tabs": ["Resources"]}, now=0, threshold_days=14)
        self.assertEqual(result["unverified_tabs"], ["Resources"])

    def test_survives_unrepresentable_epoch_without_crashing(self):
        """meta 里的 epoch 若异常（如被手动改坏），耗时/展示字段换算失败也不该让整条命令崩溃。"""
        meta = {"last_verified_epoch": -99999999999}
        result = compute_freshness(meta, now=NOW_BASE, threshold_days=14)
        self.assertEqual(result["status"], "stale")
        self.assertIsNone(result["last_verified_at"])


class TestApplyRecordCheck(unittest.TestCase):
    def test_verified_advances_last_verified(self):
        meta = apply_record_check({}, "verified", None, now=NOW_BASE)
        self.assertEqual(meta["last_verified_epoch"], NOW_BASE)
        self.assertEqual(meta["last_prompted_epoch"], NOW_BASE)
        self.assertEqual(meta["last_prompt_response"], "verified")

    def test_declined_does_not_advance_last_verified(self):
        meta = {"last_verified_epoch": NOW_BASE - DAY}
        meta = apply_record_check(meta, "declined", None, now=NOW_BASE)
        self.assertEqual(meta["last_verified_epoch"], NOW_BASE - DAY)
        self.assertEqual(meta["last_prompted_epoch"], NOW_BASE)
        self.assertEqual(meta["last_prompt_response"], "declined")

    def test_failed_does_not_advance_last_verified(self):
        meta = {"last_verified_epoch": NOW_BASE - DAY}
        meta = apply_record_check(meta, "failed", None, now=NOW_BASE)
        self.assertEqual(meta["last_verified_epoch"], NOW_BASE - DAY)
        self.assertEqual(meta["last_prompt_response"], "failed")

    def test_unverified_tabs_updated_when_provided(self):
        meta = apply_record_check({}, "declined", ["Resources", "Reference"], now=NOW_BASE)
        self.assertEqual(meta["unverified_tabs"], ["Resources", "Reference"])

    def test_unverified_tabs_untouched_when_none(self):
        meta = {"unverified_tabs": ["Old"]}
        meta = apply_record_check(meta, "declined", None, now=NOW_BASE)
        self.assertEqual(meta["unverified_tabs"], ["Old"])

    def test_does_not_mutate_input_meta(self):
        original = {"last_verified_epoch": NOW_BASE - DAY}
        apply_record_check(original, "verified", None, now=NOW_BASE)
        self.assertEqual(original, {"last_verified_epoch": NOW_BASE - DAY})


class TestFindUnverifiedTabs(unittest.TestCase):
    def test_detects_marker_right_after_tab_header(self):
        text = SAMPLE_CATALOG.replace(
            "## Tab 2 — Build（对应有道笔记\"构建\"，入口：`/agents`）\n",
            "## Tab 2 — Build（对应有道笔记\"构建\"，入口：`/agents`）\n"
            "<!-- unverified: timeout -->\n",
        )
        result = find_unverified_tabs(text)
        self.assertEqual(result, {"Build": "timeout"})

    def test_no_marker_returns_empty(self):
        self.assertEqual(find_unverified_tabs(SAMPLE_CATALOG), {})


class TestLocateAndScan(unittest.TestCase):
    def test_leading_and_trailing_boundaries(self):
        lines = SAMPLE_CATALOG.splitlines()
        leading_end, blocks, trailing_start = locate_tab_blocks(lines)
        self.assertEqual(lines[leading_end], "## Tab 1 — Getting started（入口：`/overview`）")
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["tab_en"], "Getting started")
        self.assertEqual(blocks[1]["tab_en"], "Build")
        self.assertEqual(lines[trailing_start], "## 已知缺口 / 待核实项")

    def test_scan_tab_block_captures_pages_and_groups(self):
        lines = SAMPLE_CATALOG.splitlines()
        _, blocks, _ = locate_tab_blocks(lines)
        scan = scan_tab_block(lines, blocks[0]["start"], blocks[0]["end"])
        group_names = [g["group_en"] for g in scan["groups"]]
        self.assertEqual(group_names, ["Getting started", "Core concepts"])
        first_group = scan["groups"][0]
        self.assertEqual(set(first_group["page_idxs"].keys()), {"/overview", "/quickstart"})


class TestBuildIndex(unittest.TestCase):
    def test_index_keyed_by_tab_and_url(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        idx, tab_names, group_idx = build_index(tabs)
        self.assertIn(("Getting started", "/overview"), idx)
        self.assertEqual(tab_names, {"Getting started", "Build"})
        self.assertEqual(group_idx["Getting started"], {"Getting started", "Core concepts"})


class TestFlattenSyncedPages(unittest.TestCase):
    def test_flattens_nested_structure(self):
        folder_map = {
            "tabs": {
                "构建": {
                    "groups": {
                        "MCP": {"pages": {"/mcp": {"fileId": "ABC123"}, "/no-id": {}}}
                    }
                }
            }
        }
        result = flatten_synced_pages(folder_map)
        self.assertEqual(result, {"/mcp": "ABC123"})


class TestComputeDiff(unittest.TestCase):
    def test_no_changes_when_identical(self):
        result = compute_diff(SAMPLE_CATALOG, SAMPLE_CATALOG, {})
        self.assertFalse(result["has_changes"])

    def test_detects_added_page(self):
        new_text = SAMPLE_CATALOG.replace(
            "- [x] Quickstart — `/quickstart`\n",
            "- [x] Quickstart — `/quickstart`\n- [ ] New Page — `/new-page`\n",
        )
        result = compute_diff(SAMPLE_CATALOG, new_text, {})
        self.assertTrue(result["has_changes"])
        self.assertEqual(len(result["pages_added"]), 1)
        self.assertEqual(result["pages_added"][0]["url"], "/new-page")

    def test_detects_removed_page_and_synced_record(self):
        new_text = SAMPLE_CATALOG.replace("- [ ] Concept B — `/concept-b`\n", "")
        result = compute_diff(SAMPLE_CATALOG, new_text, {"/concept-b": "FILEID999"})
        removed = result["pages_removed"]
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["url"], "/concept-b")
        self.assertTrue(removed[0]["had_synced_record"])
        self.assertEqual(removed[0]["synced_file_id"], "FILEID999")

    def test_detects_retitled_page(self):
        new_text = SAMPLE_CATALOG.replace(
            "- [x] Quickstart — `/quickstart`",
            "- [x] Quick Start Guide — `/quickstart`",
        )
        result = compute_diff(SAMPLE_CATALOG, new_text, {})
        self.assertEqual(len(result["pages_retitled"]), 1)
        self.assertEqual(result["pages_retitled"][0]["new_title"], "Quick Start Guide")

    def test_detects_moved_page(self):
        new_text = SAMPLE_CATALOG.replace(
            "- [ ] Overview — `/overview`\n- [x] Quickstart — `/quickstart`\n\n### Core concepts\n",
            "- [x] Quickstart — `/quickstart`\n\n### Core concepts\n- [ ] Overview — `/overview`\n",
        )
        result = compute_diff(SAMPLE_CATALOG, new_text, {})
        moved = result["pages_moved"]
        self.assertEqual(len(moved), 1)
        self.assertEqual(moved[0]["url"], "/overview")
        self.assertEqual(moved[0]["from"]["group"], "Getting started")
        self.assertEqual(moved[0]["to"]["group"], "Core concepts")

    def test_unverified_tab_excluded_from_diff(self):
        """标记 unverified 的 Tab 即使内容整体消失也不该被当成'全部删除'。"""
        new_text = SAMPLE_CATALOG.replace(
            "## Tab 2 — Build（对应有道笔记\"构建\"，入口：`/agents`）\n\n### MCP\n"
            "- [x] Reference — `/mcp`（已存：mcp.md）\n",
            "## Tab 2 — Build（对应有道笔记\"构建\"，入口：`/agents`）\n"
            "<!-- unverified: timeout -->\n",
        )
        result = compute_diff(SAMPLE_CATALOG, new_text, {})
        self.assertFalse(result["has_changes"])
        self.assertEqual(result["tabs_skipped_unverified"], ["Build"])

    def test_raises_when_new_has_zero_tabs(self):
        with self.assertRaises(ValueError):
            compute_diff(SAMPLE_CATALOG, "# 空文件\n没有任何 Tab\n", {})


class TestComputeApply(unittest.TestCase):
    def test_roundtrip_identical_content_unchanged(self):
        merged, summary = compute_apply(SAMPLE_CATALOG, SAMPLE_CATALOG)
        self.assertEqual(merged.rstrip("\n"), SAMPLE_CATALOG.rstrip("\n"))

    def test_preserves_checkbox_and_trailing_annotation_on_retitle(self):
        new_text = SAMPLE_CATALOG.replace(
            "- [x] Reference — `/mcp`（已存：mcp.md）",
            "- [ ] API Reference — `/mcp`",  # 新抓取内容没有历史批注和 checkbox 状态
        )
        merged, _ = compute_apply(SAMPLE_CATALOG, new_text)
        # 应保留旧行的 [x] 和"（已存：mcp.md）"尾注，只替换标题文字
        self.assertIn("- [x] API Reference — `/mcp`（已存：mcp.md）", merged)

    def test_removed_page_disappears(self):
        new_text = SAMPLE_CATALOG.replace("- [ ] Concept B — `/concept-b`\n", "")
        merged, summary = compute_apply(SAMPLE_CATALOG, new_text)
        self.assertNotIn("/concept-b", merged)

    def test_added_page_appears_with_unchecked_box(self):
        new_text = SAMPLE_CATALOG.replace(
            "- [ ] Concept B — `/concept-b`\n",
            "- [ ] Concept B — `/concept-b`\n- [ ] Concept C — `/concept-c`\n",
        )
        merged, _ = compute_apply(SAMPLE_CATALOG, new_text)
        self.assertIn("- [ ] Concept C — `/concept-c`", merged)

    def test_new_group_inserted_before_trailing_separator(self):
        new_text = SAMPLE_CATALOG.replace(
            "---\n\n## Tab 2",
            "### Advanced\n- [ ] Advanced Topic — `/advanced`\n\n---\n\n## Tab 2",
        )
        merged, _ = compute_apply(SAMPLE_CATALOG, new_text)
        lines = merged.splitlines()
        adv_idx = lines.index("### Advanced")
        sep_idx = next(i for i, l in enumerate(lines) if l == "---")
        tab2_idx = next(i for i, l in enumerate(lines) if l.startswith("## Tab 2"))
        self.assertLess(adv_idx, sep_idx)
        self.assertLess(sep_idx, tab2_idx)

    def test_new_tab_inserted_before_known_gaps_section(self):
        new_text = SAMPLE_CATALOG.replace(
            "## 已知缺口",
            "## Tab 3 — Extra（入口：`/extra`）\n\n### Extra Group\n"
            "- [ ] Extra Page — `/extra-page`\n\n---\n\n## 已知缺口",
        )
        merged, summary = compute_apply(SAMPLE_CATALOG, new_text)
        self.assertIn("Extra", summary["tabs_added"])
        lines = merged.splitlines()
        tab3_idx = next(i for i, l in enumerate(lines) if l.startswith("## Tab 3"))
        gaps_idx = next(i for i, l in enumerate(lines) if l.startswith("## 已知缺口"))
        self.assertLess(tab3_idx, gaps_idx)

    def test_unverified_tab_copied_verbatim(self):
        new_text = SAMPLE_CATALOG.replace(
            "## Tab 2 — Build（对应有道笔记\"构建\"，入口：`/agents`）\n\n### MCP\n"
            "- [x] Reference — `/mcp`（已存：mcp.md）\n",
            "## Tab 2 — Build（对应有道笔记\"构建\"，入口：`/agents`）\n"
            "<!-- unverified: timeout -->\n",
        )
        merged, summary = compute_apply(SAMPLE_CATALOG, new_text)
        self.assertIn("- [x] Reference — `/mcp`（已存：mcp.md）", merged)
        self.assertNotIn("unverified", merged)
        self.assertEqual(summary["tabs_skipped_unverified"], ["Build"])

    def test_removed_tab_dropped_entirely(self):
        lines = SAMPLE_CATALOG.splitlines()
        _, blocks, _ = locate_tab_blocks(lines)
        tab2 = blocks[1]
        new_lines = lines[:tab2["start"]] + lines[tab2["end"]:]
        new_text = "\n".join(new_lines) + "\n"
        merged, summary = compute_apply(SAMPLE_CATALOG, new_text)
        self.assertNotIn("## Tab 2", merged)
        self.assertEqual(summary["tabs_removed"], ["Build"])

    def test_leading_and_trailing_free_text_preserved(self):
        merged, _ = compute_apply(SAMPLE_CATALOG, SAMPLE_CATALOG)
        self.assertIn("# 示例站点导航", merged)
        self.assertIn("一些说明文字，不属于任何 Tab", merged)

    def test_raises_when_new_has_zero_tabs(self):
        with self.assertRaises(ValueError):
            compute_apply(SAMPLE_CATALOG, "空内容，没有 Tab\n")


if __name__ == "__main__":
    unittest.main()
