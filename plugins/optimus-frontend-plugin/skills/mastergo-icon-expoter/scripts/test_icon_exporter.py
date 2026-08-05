"""Black-box CLI contract tests for icon_exporter.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

SCRIPT = Path(__file__).with_name("icon_exporter.py")


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def write_input(directory: Path, payload: dict) -> Path:
    path = directory / "input.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def single_vector_icon(**overrides) -> dict:
    icon = {
        "svgShortKey": "S0#0",
        "nodeId": "10:2",
        "dslName": "SearchIcon",
        "userName": None,
        "width": 16,
        "height": 16,
        "paths": [{"data": "F1 M3,3 H21 V21 H3 Z", "fill": "#4E5969", "stroke": None}],
        "warnings": [],
        "sourceKind": "vector",
    }
    icon.update(overrides)
    return icon


def base_payload(*icons: dict) -> dict:
    return {
        "meta": {"fileId": "1", "layerId": "2:3", "outDir": "Assets", "mergeMode": "separate"},
        "icons": list(icons),
    }


class ContractValidationTests(unittest.TestCase):
    def test_missing_input_file_fails_without_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_cli("--input", str(Path(directory) / "missing.json"), "--out", str(Path(directory) / "out"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("error: "))

    def test_malformed_json_reports_the_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            input_path.write_text("{not valid json", encoding="utf-8")
            result = run_cli("--input", str(input_path), "--out", str(Path(directory) / "out"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("input.json", result.stderr)

    def test_vector_icon_missing_svg_short_key_is_fatal(self) -> None:
        icon = single_vector_icon()
        del icon["svgShortKey"]
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("svgShortKey", result.stderr)
        self.assertIn("10:2", result.stderr)
        self.assertFalse(out_dir.exists())

    def test_vector_icon_missing_node_id_is_fatal(self) -> None:
        icon = single_vector_icon()
        del icon["nodeId"]
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertIn("nodeId", result.stderr)
        self.assertFalse(out_dir.exists())

    def test_vector_icon_with_empty_paths_is_fatal(self) -> None:
        icon = single_vector_icon(paths=[])
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertIn("paths", result.stderr)
        self.assertFalse(out_dir.exists())

    def test_path_data_missing_fill_rule_prefix_is_fatal(self) -> None:
        icon = single_vector_icon(paths=[{"data": "M3,3 H21 V21 H3 Z", "fill": "#4E5969", "stroke": None}])
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertIn("F0", result.stderr)
        self.assertIn("F1", result.stderr)
        self.assertFalse(out_dir.exists())

    def test_lowercase_fill_rule_prefix_is_fatal(self) -> None:
        # WPF's mini-language is case-sensitive; tolerating "f1" would be a new silent trap.
        icon = single_vector_icon(paths=[{"data": "f1 M3,3 H21 V21 H3 Z", "fill": "#4E5969", "stroke": None}])
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertFalse(out_dir.exists())

    def test_bitmap_icon_with_nonempty_paths_is_fatal(self) -> None:
        icon = {
            "nodeId": "i:1", "dslName": "Avatar", "userName": None,
            "width": 40, "height": 40,
            "paths": [{"data": "F1 M0,0 Z", "fill": "#000000", "stroke": None}],
            "warnings": [], "sourceKind": "bitmap", "bitmapPath": "raw/avatar.png",
        }
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertIn("sourceKind", result.stderr)
        self.assertFalse(out_dir.exists())


class FormatDecisionTests(unittest.TestCase):
    def test_bitmap_becomes_png(self) -> None:
        from icon_exporter import decide_format
        icon = {"sourceKind": "bitmap", "paths": []}
        fmt, decision = decide_format(icon)
        self.assertEqual(fmt, "png")
        self.assertTrue(decision)

    def test_single_path_vector_becomes_path(self) -> None:
        from icon_exporter import decide_format
        icon = {"sourceKind": "vector", "paths": [{"data": "F1 M0,0 Z", "fill": "#000", "stroke": None}]}
        fmt, decision = decide_format(icon)
        self.assertEqual(fmt, "path")

    def test_multi_path_vector_becomes_drawing_image(self) -> None:
        from icon_exporter import decide_format
        icon = {
            "sourceKind": "vector",
            "paths": [
                {"data": "F1 M0,0 Z", "fill": "#FFB800", "stroke": None},
                {"data": "F1 M1,1 Z", "fill": "#FFD666", "stroke": None},
            ],
        }
        fmt, decision = decide_format(icon)
        self.assertEqual(fmt, "drawing-image")

    def test_two_same_color_paths_still_become_drawing_image(self) -> None:
        # Decision is by paths length alone; svg-to-xaml-path already made the merge
        # call, and decide_format must not re-litigate it by inspecting fill values.
        from icon_exporter import decide_format
        icon = {
            "sourceKind": "vector",
            "paths": [
                {"data": "F1 M0,0 Z", "fill": "#000", "stroke": None},
                {"data": "F1 M1,1 Z", "fill": "#000", "stroke": None},
            ],
        }
        fmt, _ = decide_format(icon)
        self.assertEqual(fmt, "drawing-image")


class NameDerivationTests(unittest.TestCase):
    def test_camel_case_search_icon_gets_icon_prefix(self) -> None:
        from icon_exporter import derive_file_name
        self.assertEqual(derive_file_name("SearchIcon"), "icon_search")

    def test_kebab_case_search_icon_gets_icon_prefix(self) -> None:
        from icon_exporter import derive_file_name
        self.assertEqual(derive_file_name("search-icon"), "icon_search")

    def test_slash_separated_icon_search_normalizes(self) -> None:
        from icon_exporter import derive_file_name
        self.assertEqual(derive_file_name("Icon/Search"), "icon_search")

    def test_existing_bg_prefix_is_not_doubled(self) -> None:
        from icon_exporter import derive_file_name
        self.assertEqual(derive_file_name("bg-header-gradient"), "bg_header_gradient")

    def test_non_ascii_name_fails_derivation(self) -> None:
        from icon_exporter import derive_file_name
        self.assertIsNone(derive_file_name("搜索图标"))

    def test_frame_number_fails_derivation(self) -> None:
        from icon_exporter import derive_file_name
        self.assertIsNone(derive_file_name("Frame 427"))

    def test_name_without_category_keyword_fails_derivation(self) -> None:
        # Lexical match only — CloseButton is "obviously" an icon but the rule
        # must not guess semantics; it should fail and be routed to CHECKPOINT.
        from icon_exporter import derive_file_name
        self.assertIsNone(derive_file_name("CloseButton"))

    def test_resource_key_from_file_name(self) -> None:
        from icon_exporter import resource_key
        self.assertEqual(resource_key("icon_search", "Geometry"), "IconSearchGeometry")
        self.assertEqual(resource_key("icon_folder_color", "Image"), "IconFolderColorImage")
        self.assertEqual(resource_key("bg_grid", "Brush"), "BgGridBrush")


class AssignNamesTests(unittest.TestCase):
    def test_user_name_wins_over_derivation(self) -> None:
        from icon_exporter import assign_names
        icons = [{"dslName": "Frame 427", "userName": "icon_close_alt", "nodeId": "1"}]
        named, unnamed = assign_names(icons)
        self.assertEqual(unnamed, [])
        self.assertEqual(named[0]["fileName"], "icon_close_alt")

    def test_derivation_success_needs_no_user_name(self) -> None:
        from icon_exporter import assign_names
        icons = [{"dslName": "SearchIcon", "userName": None, "nodeId": "1"}]
        named, unnamed = assign_names(icons)
        self.assertEqual(unnamed, [])
        self.assertEqual(named[0]["fileName"], "icon_search")

    def test_failed_derivation_without_user_name_is_routed_to_checkpoint(self) -> None:
        from icon_exporter import assign_names
        icons = [{"dslName": "搜索图标", "userName": None, "nodeId": "1"}]
        named, unnamed = assign_names(icons)
        self.assertEqual(named, [])
        self.assertEqual(len(unnamed), 1)
        self.assertEqual(unnamed[0]["nodeId"], "1")

    def test_colliding_file_names_from_different_sources_are_fatal(self) -> None:
        from icon_exporter import assign_names, ConversionError
        icons = [
            {"dslName": "SearchIcon", "userName": None, "nodeId": "1"},
            {"dslName": "search-icon", "userName": None, "nodeId": "2"},
        ]
        with self.assertRaises(ConversionError) as context:
            assign_names(icons)
        self.assertIn("icon_search", str(context.exception))


class RenderIconsXamlTests(unittest.TestCase):
    def test_single_path_entry_becomes_a_geometry_resource_with_stretch_note(self) -> None:
        from icon_exporter import render_icons_xaml
        entries = [{
            "fileName": "icon_search", "format": "path",
            "paths": [{"data": "F1 M3,3 H21 V21 H3 Z", "fill": "#4E5969", "stroke": None}],
        }]
        xaml = render_icons_xaml(entries)
        self.assertIn('<Geometry x:Key="IconSearchGeometry">F1 M3,3 H21 V21 H3 Z</Geometry>', xaml)

    def test_multi_path_entry_becomes_a_drawing_image_with_drawing_group(self) -> None:
        from icon_exporter import render_icons_xaml
        entries = [{
            "fileName": "icon_folder_color", "format": "drawing-image",
            "paths": [
                {"data": "F1 M2,4 H10 L12,7 H22 V20 H2 Z", "fill": "#FFB800", "stroke": None},
                {"data": "F1 M2,9 H22 V20 H2 Z", "fill": "#FFD666", "stroke": None},
            ],
        }]
        xaml = render_icons_xaml(entries)
        self.assertIn('<DrawingImage x:Key="IconFolderColorImage">', xaml)
        self.assertIn('<DrawingGroup>', xaml)
        self.assertIn('<GeometryDrawing Brush="#FFB800" Geometry="F1 M2,4 H10 L12,7 H22 V20 H2 Z" />', xaml)
        self.assertIn('<GeometryDrawing Brush="#FFD666" Geometry="F1 M2,9 H22 V20 H2 Z" />', xaml)

    def test_xaml_is_a_well_formed_resource_dictionary(self) -> None:
        from icon_exporter import render_icons_xaml
        entries = [{
            "fileName": "icon_search", "format": "path",
            "paths": [{"data": "F1 M0,0 Z", "fill": "#000", "stroke": None}],
        }]
        xaml = render_icons_xaml(entries)
        self.assertTrue(xaml.startswith("<ResourceDictionary"))
        self.assertTrue(xaml.rstrip().endswith("</ResourceDictionary>"))

    def test_png_format_entries_are_not_written_into_icons_xaml(self) -> None:
        from icon_exporter import render_icons_xaml
        entries = [{"fileName": "bg_photo", "format": "png", "paths": []}]
        xaml = render_icons_xaml(entries)
        self.assertNotIn("bg_photo", xaml)


class RenderManifestTests(unittest.TestCase):
    def test_named_entry_becomes_an_exported_record(self) -> None:
        from icon_exporter import render_manifest
        entries = [{
            "svgShortKey": "S0#0", "nodeId": "10:2", "dslName": "SearchIcon",
            "fileName": "icon_search", "format": "path", "decision": "single fill, no gradient",
            "width": 16, "height": 16,
            "paths": [{"data": "F1 M0,0 Z", "fill": "#4E5969", "stroke": None}],
        }]
        manifest = render_manifest(entries, [])
        record = manifest["icons"][0]
        self.assertEqual(record["resourceKey"], "IconSearchGeometry")
        self.assertEqual(record["status"], "exported")
        self.assertEqual(record["color"], "#4E5969")

    def test_unnamed_entry_becomes_needs_manual_with_reason(self) -> None:
        from icon_exporter import render_manifest
        unnamed = [{"nodeId": "1", "dslName": "搜索图标", "svgShortKey": "S0#3"}]
        manifest = render_manifest([], unnamed)
        record = manifest["icons"][0]
        self.assertEqual(record["status"], "needs-manual")
        self.assertTrue(record["reason"])

    def test_png_entry_records_png_format(self) -> None:
        from icon_exporter import render_manifest
        entries = [{
            "nodeId": "i:1", "dslName": "Avatar", "fileName": "avatar_default",
            "format": "png", "decision": "bitmap source; no vector geometry available",
            "width": 40, "height": 40, "paths": [],
        }]
        manifest = render_manifest(entries, [])
        self.assertEqual(manifest["icons"][0]["format"], "png")


def _manifest_with(records: list[dict]) -> dict:
    return {"icons": records}


class SelfCheckTests(unittest.TestCase):
    def test_missing_fill_rule_prefix_is_caught(self) -> None:
        from icon_exporter import self_check
        xaml = '<ResourceDictionary xmlns="a" xmlns:x="b">\n  <Geometry x:Key="IconSearchGeometry">M0,0 Z</Geometry>\n</ResourceDictionary>\n'
        manifest = _manifest_with([{"resourceKey": "IconSearchGeometry", "fileName": "icon_search", "format": "path", "status": "exported", "reason": None}])
        violations = self_check(xaml, manifest, {}, None)
        self.assertTrue(any("F0" in v or "F1" in v for v in violations))

    def test_valid_geometry_passes_rule_one(self) -> None:
        from icon_exporter import self_check
        xaml = '<ResourceDictionary xmlns="a" xmlns:x="b">\n  <Geometry x:Key="IconSearchGeometry">F1 M0,0 Z</Geometry>\n</ResourceDictionary>\n'
        manifest = _manifest_with([{"resourceKey": "IconSearchGeometry", "fileName": "icon_search", "format": "path", "status": "exported", "reason": None}])
        violations = self_check(xaml, manifest, {}, None)
        self.assertEqual(violations, [])

    def test_duplicate_x_key_within_new_xaml_is_caught(self) -> None:
        from icon_exporter import self_check
        xaml = (
            '<ResourceDictionary xmlns="a" xmlns:x="b">\n'
            '  <Geometry x:Key="IconCloseGeometry">F1 M0,0 Z</Geometry>\n'
            '  <Geometry x:Key="IconCloseGeometry">F1 M1,1 Z</Geometry>\n'
            '</ResourceDictionary>\n'
        )
        manifest = _manifest_with([
            {"resourceKey": "IconCloseGeometry", "fileName": "icon_close", "format": "path", "status": "exported", "reason": None},
            {"resourceKey": "IconCloseGeometry", "fileName": "icon_close_alt", "format": "path", "status": "exported", "reason": None},
        ])
        violations = self_check(xaml, manifest, {}, None)
        self.assertTrue(any("IconCloseGeometry" in v for v in violations))

    def test_duplicate_key_against_existing_xaml_is_caught_when_merging(self) -> None:
        from icon_exporter import self_check
        new_xaml = '<ResourceDictionary xmlns="a" xmlns:x="b">\n  <Geometry x:Key="IconSearchGeometry">F1 M0,0 Z</Geometry>\n</ResourceDictionary>\n'
        existing_xaml = '<ResourceDictionary xmlns="a" xmlns:x="b">\n  <Geometry x:Key="IconSearchGeometry">F1 M9,9 Z</Geometry>\n</ResourceDictionary>\n'
        manifest = _manifest_with([{"resourceKey": "IconSearchGeometry", "fileName": "icon_search", "format": "path", "status": "exported", "reason": None}])
        violations = self_check(new_xaml, manifest, {}, existing_xaml)
        self.assertTrue(any("IconSearchGeometry" in v for v in violations))

    def test_same_key_is_fine_when_not_merging(self) -> None:
        from icon_exporter import self_check
        new_xaml = '<ResourceDictionary xmlns="a" xmlns:x="b">\n  <Geometry x:Key="IconSearchGeometry">F1 M0,0 Z</Geometry>\n</ResourceDictionary>\n'
        manifest = _manifest_with([{"resourceKey": "IconSearchGeometry", "fileName": "icon_search", "format": "path", "status": "exported", "reason": None}])
        violations = self_check(new_xaml, manifest, {}, existing_xaml=None)
        self.assertEqual(violations, [])

    def test_manifest_resource_key_absent_from_xaml_is_caught(self) -> None:
        from icon_exporter import self_check
        xaml = '<ResourceDictionary xmlns="a" xmlns:x="b">\n</ResourceDictionary>\n'
        manifest = _manifest_with([{"resourceKey": "IconGhostGeometry", "fileName": "icon_ghost", "format": "path", "status": "exported", "reason": None}])
        violations = self_check(xaml, manifest, {}, None)
        self.assertTrue(any("IconGhostGeometry" in v for v in violations))

    def test_needs_manual_without_reason_is_caught(self) -> None:
        from icon_exporter import self_check
        manifest = _manifest_with([{"resourceKey": None, "fileName": None, "format": "unresolved", "status": "needs-manual", "reason": None}])
        violations = self_check("<ResourceDictionary xmlns=\"a\" xmlns:x=\"b\"></ResourceDictionary>\n", manifest, {}, None)
        self.assertTrue(any("reason" in v for v in violations))

    def test_needs_manual_with_reason_passes(self) -> None:
        from icon_exporter import self_check
        manifest = _manifest_with([{"resourceKey": None, "fileName": None, "format": "unresolved", "status": "needs-manual", "reason": "could not derive a file name; needs a userName"}])
        violations = self_check("<ResourceDictionary xmlns=\"a\" xmlns:x=\"b\"></ResourceDictionary>\n", manifest, {}, None)
        self.assertEqual(violations, [])

    def test_zero_dimension_png_is_caught(self) -> None:
        from icon_exporter import self_check
        manifest = _manifest_with([{"resourceKey": None, "fileName": "bg_photo", "format": "png", "width": 0, "height": 40, "status": "exported", "reason": None}])
        violations = self_check("<ResourceDictionary xmlns=\"a\" xmlns:x=\"b\"></ResourceDictionary>\n", manifest, {"bg_photo.png": b"\x89PNG"}, None)
        self.assertTrue(any("width" in v or "height" in v for v in violations))

    def test_ico_fallback_reported_as_exported_is_caught(self) -> None:
        from icon_exporter import self_check
        manifest = _manifest_with([{
            "resourceKey": None, "fileName": "app_icon", "format": "ico-fallback-png",
            "status": "exported", "reason": "Pillow not installed", "width": 16, "height": 16,
        }])
        violations = self_check("<ResourceDictionary xmlns=\"a\" xmlns:x=\"b\"></ResourceDictionary>\n", manifest, {}, None)
        self.assertTrue(any("ico-fallback-png" in v or "exported" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
