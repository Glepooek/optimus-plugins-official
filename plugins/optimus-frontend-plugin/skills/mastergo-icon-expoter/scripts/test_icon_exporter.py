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


def assert_hard_failure(test_case: unittest.TestCase, result: subprocess.CompletedProcess[str], out_dir: Path) -> None:
    test_case.assertEqual(result.returncode, 2)
    test_case.assertEqual(result.stdout, "")
    test_case.assertTrue(result.stderr.startswith("error: "), result.stderr)
    test_case.assertFalse(out_dir.exists())


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

    def test_boolean_width_is_not_accepted_as_a_number(self) -> None:
        # bool is an int subclass; isinstance(True, int) is True, so a naive
        # numeric check would silently accept width: True as if it were 1.
        from icon_exporter import self_check
        manifest = _manifest_with([{"resourceKey": None, "fileName": "bg_photo", "format": "png", "width": True, "height": 40, "status": "exported", "reason": None}])
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

    def test_degraded_bitmap_with_no_dimensions_does_not_trigger_rule_six(self) -> None:
        # Regression guard: a degraded (needs-manual) bitmap still carries
        # format "png" and a fileName, but width/height are legitimately
        # unknown (unresolved source). Rule 6 must skip needs-manual records
        # entirely instead of aborting the whole batch over them.
        from icon_exporter import self_check
        manifest = _manifest_with([{
            "resourceKey": None, "fileName": "avatar_default", "format": "png",
            "width": None, "height": None, "status": "needs-manual",
            "reason": "bitmapPath is missing",
        }])
        violations = self_check("<ResourceDictionary xmlns=\"a\" xmlns:x=\"b\"></ResourceDictionary>\n", manifest, {}, None)
        self.assertEqual(violations, [])


class IcoSynthesisTests(unittest.TestCase):
    def test_synthesize_ico_returns_none_when_pillow_unavailable(self) -> None:
        import icon_exporter
        original = icon_exporter.sys.modules.get("PIL")
        icon_exporter.sys.modules["PIL"] = None  # forces ImportError on `import PIL`
        try:
            result = icon_exporter.synthesize_ico({16: b"\x89PNG16", 32: b"\x89PNG32"})
        finally:
            if original is not None:
                icon_exporter.sys.modules["PIL"] = original
            else:
                icon_exporter.sys.modules.pop("PIL", None)
        self.assertIsNone(result)


class FullPipelineTests(unittest.TestCase):
    def test_single_color_icon_and_multi_color_icon_and_unnamed_icon_all_land_correctly(self) -> None:
        icons = [
            single_vector_icon(),
            single_vector_icon(
                svgShortKey="S0#3", nodeId="10:9", dslName="搜索图标", userName="icon_search_alt",
                width=24, height=24,
                paths=[
                    {"data": "F1 M2,4 H10 L12,7 H22 V20 H2 Z", "fill": "#FFB800", "stroke": None},
                    {"data": "F1 M2,9 H22 V20 H2 Z", "fill": "#FFD666", "stroke": None},
                ],
                warnings=["class attributes were encountered; CSS classes were not converted."],
            ),
            single_vector_icon(svgShortKey="S0#7", nodeId="10:20", dslName="CloseButton", userName=None),
        ]
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(*icons))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            icons_xaml = (out_dir / "Icons.xaml").read_text(encoding="utf-8")
            self.assertIn("IconSearchGeometry", icons_xaml)
            self.assertIn("IconSearchAltImage", icons_xaml)
            manifest = json.loads((out_dir / "icons-manifest.json").read_text(encoding="utf-8"))
            statuses = {record["fileName"] or record["name"]: record["status"] for record in manifest["icons"]}
            self.assertEqual(statuses["icon_search"], "exported")
            self.assertEqual(statuses["icon_search_alt"], "exported")
            self.assertEqual(statuses["CloseButton"], "needs-manual")

    def test_self_check_failure_leaves_output_directory_untouched(self) -> None:
        # Regression guard: a bad path.data (missing F0/F1) must be caught by
        # validate_contract before render even runs, so nothing is ever written.
        icon = single_vector_icon(paths=[{"data": "M0,0 Z", "fill": "#000", "stroke": None}])
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertFalse(out_dir.exists())

    def test_bitmap_only_icon_produces_a_needs_manual_manifest_entry_without_pillow_target(self) -> None:
        icon = {
            "nodeId": "i:1", "dslName": "Avatar", "userName": "avatar_default",
            "width": 40, "height": 40, "paths": [], "warnings": [],
            "sourceKind": "bitmap", "bitmapPath": "raw/avatar.png",
        }
        with tempfile.TemporaryDirectory() as directory:
            raw_dir = Path(directory) / "raw"
            raw_dir.mkdir()
            (raw_dir / "avatar.png").write_bytes(b"\x89PNGDATA")
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir), "--source-root", str(directory))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out_dir / "Images" / "avatar_default.png").exists())


def _payload_with_merge_mode(icon: dict, merge_mode: str | None) -> dict:
    meta = {"fileId": "1", "layerId": "2:3", "outDir": "Assets"}
    if merge_mode is not None:
        meta["mergeMode"] = merge_mode
    return {"meta": meta, "icons": [icon]}


class MergeModeTests(unittest.TestCase):
    def test_merge_mode_combines_new_and_existing_non_colliding_resources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory) / "out"
            first_icon = single_vector_icon()
            first_input = write_input(Path(directory), _payload_with_merge_mode(first_icon, "separate"))
            first_result = run_cli("--input", str(first_input), "--out", str(out_dir))
            self.assertEqual(first_result.returncode, 0, first_result.stderr)

            second_icon = single_vector_icon(
                svgShortKey="S0#9", nodeId="20:2", dslName="CloseButton", userName="icon_close",
            )
            second_input = write_input(Path(directory), _payload_with_merge_mode(second_icon, "merge"))
            second_result = run_cli("--input", str(second_input), "--out", str(out_dir))
            self.assertEqual(second_result.returncode, 0, second_result.stderr)

            icons_xaml = (out_dir / "Icons.xaml").read_text(encoding="utf-8")
            self.assertIn("IconSearchGeometry", icons_xaml)
            self.assertIn("IconCloseGeometry", icons_xaml)

    def test_merge_mode_with_colliding_key_aborts_and_leaves_existing_file_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory) / "out"
            first_icon = single_vector_icon()
            first_input = write_input(Path(directory), _payload_with_merge_mode(first_icon, "separate"))
            first_result = run_cli("--input", str(first_input), "--out", str(out_dir))
            self.assertEqual(first_result.returncode, 0, first_result.stderr)
            before = (out_dir / "Icons.xaml").read_bytes()

            colliding_icon = single_vector_icon()  # same dslName -> same fileName -> same x:Key
            second_input = write_input(Path(directory), _payload_with_merge_mode(colliding_icon, "merge"))
            second_result = run_cli("--input", str(second_input), "--out", str(out_dir))

            self.assertEqual(second_result.returncode, 2)
            self.assertEqual(second_result.stdout, "")
            after = (out_dir / "Icons.xaml").read_bytes()
            self.assertEqual(before, after)

    def test_existing_icons_xaml_with_default_merge_mode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory) / "out"
            first_icon = single_vector_icon()
            first_input = write_input(Path(directory), _payload_with_merge_mode(first_icon, "separate"))
            first_result = run_cli("--input", str(first_input), "--out", str(out_dir))
            self.assertEqual(first_result.returncode, 0, first_result.stderr)
            before = (out_dir / "Icons.xaml").read_bytes()

            second_icon = single_vector_icon(
                svgShortKey="S0#9", nodeId="20:2", dslName="CloseButton", userName="icon_close",
            )
            second_input = write_input(Path(directory), _payload_with_merge_mode(second_icon, None))
            second_result = run_cli("--input", str(second_input), "--out", str(out_dir))

            self.assertEqual(second_result.returncode, 2)
            self.assertEqual(second_result.stdout, "")
            self.assertTrue(second_result.stderr.startswith("error: "), second_result.stderr)
            after = (out_dir / "Icons.xaml").read_bytes()
            self.assertEqual(before, after)

    def test_existing_icons_xaml_with_explicit_separate_mode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory) / "out"
            first_icon = single_vector_icon()
            first_input = write_input(Path(directory), _payload_with_merge_mode(first_icon, "separate"))
            first_result = run_cli("--input", str(first_input), "--out", str(out_dir))
            self.assertEqual(first_result.returncode, 0, first_result.stderr)

            second_icon = single_vector_icon(
                svgShortKey="S0#9", nodeId="20:2", dslName="CloseButton", userName="icon_close",
            )
            second_input = write_input(Path(directory), _payload_with_merge_mode(second_icon, "separate"))
            second_result = run_cli("--input", str(second_input), "--out", str(out_dir))

            self.assertEqual(second_result.returncode, 2)
            self.assertEqual(second_result.stdout, "")

    def test_merge_mode_with_self_closing_existing_xaml_fails_hard_not_with_a_crash(self) -> None:
        # Regression guard: a self-closing <ResourceDictionary ... /> is valid XAML
        # that _inner's index()/rindex() calls cannot locate a closing tag for;
        # this must surface as a clean error:/exit 2, not an uncaught ValueError.
        # (An existing Icons.xaml is a precondition for the merge code path to run
        # at all, so --out must already exist here; assert_hard_failure's "does not
        # exist" check does not apply — instead we assert nothing new was written.)
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory) / "out"
            out_dir.mkdir()
            existing_xaml = (
                '<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" '
                'xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />\n'
            )
            (out_dir / "Icons.xaml").write_text(existing_xaml, encoding="utf-8")
            icon = single_vector_icon()
            input_path = write_input(Path(directory), _payload_with_merge_mode(icon, "merge"))
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertTrue(result.stderr.startswith("error: "), result.stderr)
            self.assertEqual((out_dir / "Icons.xaml").read_text(encoding="utf-8"), existing_xaml)
            self.assertFalse((out_dir / "icons-manifest.json").exists())

    def test_overwrite_mode_replaces_existing_icons_xaml_entirely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out_dir = Path(directory) / "out"
            first_icon = single_vector_icon()
            first_input = write_input(Path(directory), _payload_with_merge_mode(first_icon, "separate"))
            first_result = run_cli("--input", str(first_input), "--out", str(out_dir))
            self.assertEqual(first_result.returncode, 0, first_result.stderr)

            second_icon = single_vector_icon(
                svgShortKey="S0#9", nodeId="20:2", dslName="CloseButton", userName="icon_close",
            )
            second_input = write_input(Path(directory), _payload_with_merge_mode(second_icon, "overwrite"))
            second_result = run_cli("--input", str(second_input), "--out", str(out_dir))
            self.assertEqual(second_result.returncode, 0, second_result.stderr)

            icons_xaml = (out_dir / "Icons.xaml").read_text(encoding="utf-8")
            self.assertNotIn("IconSearchGeometry", icons_xaml)
            self.assertIn("IconCloseGeometry", icons_xaml)


class BitmapDegradationTests(unittest.TestCase):
    def test_bitmap_icon_with_no_source_root_degrades_without_aborting_batch(self) -> None:
        bitmap_icon = {
            "nodeId": "i:1", "dslName": "Avatar", "userName": "avatar_default",
            "width": 40, "height": 40, "paths": [], "warnings": [],
            "sourceKind": "bitmap", "bitmapPath": "raw/avatar.png",
        }
        vector_icon = single_vector_icon()
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(vector_icon, bitmap_icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((out_dir / "Images" / "avatar_default.png").exists())
            manifest = json.loads((out_dir / "icons-manifest.json").read_text(encoding="utf-8"))
            records = {record["fileName"] or record["name"]: record for record in manifest["icons"]}
            self.assertEqual(records["icon_search"]["status"], "exported")
            degraded_record = records["avatar_default"]
            self.assertEqual(degraded_record["status"], "needs-manual")
            self.assertTrue(degraded_record["reason"])
            self.assertIn("--source-root", degraded_record["reason"])

    def test_bitmap_icon_with_missing_source_file_degrades_without_aborting_batch(self) -> None:
        bitmap_icon = {
            "nodeId": "i:1", "dslName": "Avatar", "userName": "avatar_default",
            "width": 40, "height": 40, "paths": [], "warnings": [],
            "sourceKind": "bitmap", "bitmapPath": "raw/missing.png",
        }
        vector_icon = single_vector_icon()
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(vector_icon, bitmap_icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir), "--source-root", str(directory))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((out_dir / "Images" / "avatar_default.png").exists())
            manifest = json.loads((out_dir / "icons-manifest.json").read_text(encoding="utf-8"))
            records = {record["fileName"] or record["name"]: record for record in manifest["icons"]}
            self.assertEqual(records["icon_search"]["status"], "exported")
            degraded_record = records["avatar_default"]
            self.assertEqual(degraded_record["status"], "needs-manual")
            self.assertIn("raw/missing.png", degraded_record["reason"])

    def test_degraded_bitmap_with_no_width_height_does_not_abort_batch(self) -> None:
        # Regression guard: self_check rule 6 used to fire on a degraded bitmap's
        # planned-but-never-written PNG record regardless of status, aborting the
        # whole batch (self-check failed: ... width/height must be positive, got
        # NonexNone) even though nothing was ever planned for it. width/height are
        # absent here (unresolved bitmap, no dimensions known) — the same shape a
        # real degraded record has.
        bitmap_icon = {
            "nodeId": "i:1", "dslName": "Avatar", "userName": "avatar_default",
            "paths": [], "warnings": [],
            "sourceKind": "bitmap", "bitmapPath": "raw/missing.png",
        }
        vector_icon = single_vector_icon()
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(vector_icon, bitmap_icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir), "--source-root", str(directory))
            self.assertEqual(result.returncode, 0, result.stderr)
            icons_xaml = (out_dir / "Icons.xaml").read_text(encoding="utf-8")
            self.assertIn("IconSearchGeometry", icons_xaml)
            manifest = json.loads((out_dir / "icons-manifest.json").read_text(encoding="utf-8"))
            records = {record["fileName"] or record["name"]: record for record in manifest["icons"]}
            self.assertEqual(records["icon_search"]["status"], "exported")
            degraded_record = records["avatar_default"]
            self.assertEqual(degraded_record["status"], "needs-manual")
            self.assertIsNone(degraded_record["width"])
            self.assertIsNone(degraded_record["height"])


class ExceptionContractTests(unittest.TestCase):
    def test_non_utf8_input_json_fails_hard_not_with_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            input_path.write_text(json.dumps(base_payload(single_vector_icon())), encoding="utf-16")
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        assert_hard_failure(self, result, out_dir)

    def test_out_path_that_is_an_existing_file_fails_hard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(single_vector_icon()))
            out_dir = Path(directory) / "out"
            out_dir.write_text("not a directory", encoding="utf-8")
            result = run_cli("--input", str(input_path), "--out", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("error: "), result.stderr)


class VectorPngFallbackTests(unittest.TestCase):
    """A failed vector conversion can ship the exact MasterGo PNG without aborting peers."""

    def fallback_icon(self, **overrides: object) -> dict:
        icon = {
            "nodeId": "v:1", "dslName": "GradientIcon", "userName": "icon_gradient",
            "width": 92, "height": 92, "paths": [], "warnings": [],
            "sourceKind": "fallback-png", "fallbackPngPath": "raw/gradient.png",
            "fallbackReason": "svg-to-xaml-path could not preserve a referenced linear gradient",
        }
        icon.update(overrides)
        return icon

    def test_vector_png_fallback_copies_png_and_records_its_vector_origin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            raw.mkdir()
            source_png = b"\x89PNG\r\n\x1a\nmastergo"
            (raw / "gradient.png").write_bytes(source_png)
            input_path = write_input(root, base_payload(self.fallback_icon()))
            out_dir = root / "out"

            result = run_cli("--input", str(input_path), "--out", str(out_dir), "--source-root", str(root))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((out_dir / "Images" / "icon_gradient.png").read_bytes(), source_png)
            manifest = json.loads((out_dir / "icons-manifest.json").read_text(encoding="utf-8"))
            record = manifest["icons"][0]
            self.assertEqual(record["format"], "png")
            self.assertEqual(record["status"], "exported")
            self.assertEqual(record["fallbackFrom"], "vector")
            self.assertIn("linear gradient", record["fallbackReason"])

    def test_missing_vector_fallback_png_degrades_without_aborting_a_vector_peer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = write_input(root, base_payload(single_vector_icon(), self.fallback_icon()))
            out_dir = root / "out"

            result = run_cli("--input", str(input_path), "--out", str(out_dir), "--source-root", str(root))

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((out_dir / "icons-manifest.json").read_text(encoding="utf-8"))
            records = {record["fileName"] or record["name"]: record for record in manifest["icons"]}
            self.assertEqual(records["icon_search"]["status"], "exported")
            fallback = records["icon_gradient"]
            self.assertEqual(fallback["status"], "needs-manual")
            self.assertEqual(fallback["fallbackFrom"], "vector")
            self.assertIn("fallbackPngPath", fallback["reason"])

    def test_vector_fallback_without_a_reason_is_rejected_before_output(self) -> None:
        icon = self.fallback_icon()
        del icon["fallbackReason"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = write_input(root, base_payload(icon))
            out_dir = root / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir), "--source-root", str(root))

        self.assertEqual(result.returncode, 2)
        self.assertIn("fallbackReason", result.stderr)
        self.assertFalse(out_dir.exists())


class DrawingGroupInputTests(unittest.TestCase):
    """svg-to-xaml-path drawing output is embeddable without dropping gradients or offsets."""

    DRAWING = """<DrawingGroup>
  <DrawingGroup.Transform>
    <MatrixTransform Matrix="1,0,0,1,12,8" />
  </DrawingGroup.Transform>
  <GeometryDrawing Geometry="F1 M0,0 H10 V10 H0 Z">
    <GeometryDrawing.Brush>
      <LinearGradientBrush StartPoint="0,0" EndPoint="1,1" MappingMode="RelativeToBoundingBox">
        <GradientStop Color="#FF0000" Offset="0" />
        <GradientStop Color="#800000FF" Offset="1" />
      </LinearGradientBrush>
    </GeometryDrawing.Brush>
  </GeometryDrawing>
</DrawingGroup>"""

    def test_drawing_group_is_written_as_a_gradient_drawing_image(self) -> None:
        icon = {
            "svgShortKey": "S0#0", "nodeId": "10:2", "dslName": "GradientIcon",
            "userName": "icon_gradient", "width": 24, "height": 24,
            "paths": [], "sourceKind": "vector", "drawingXaml": self.DRAWING,
        }
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))

            self.assertEqual(result.returncode, 0, result.stderr)
            xaml = (out_dir / "Icons.xaml").read_text(encoding="utf-8")
            self.assertIn('x:Key="IconGradientImage"', xaml)
            self.assertIn('<LinearGradientBrush StartPoint="0,0" EndPoint="1,1"', xaml)
            self.assertIn('<MatrixTransform Matrix="1,0,0,1,12,8" />', xaml)
            manifest = json.loads((out_dir / "icons-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["icons"][0]["format"], "drawing-image")

    def test_non_drawing_group_fragment_is_rejected_before_output(self) -> None:
        icon = single_vector_icon(paths=[], drawingXaml='<GeometryDrawing Geometry="F1 M0,0 Z" />')
        with tempfile.TemporaryDirectory() as directory:
            input_path = write_input(Path(directory), base_payload(icon))
            out_dir = Path(directory) / "out"
            result = run_cli("--input", str(input_path), "--out", str(out_dir))

        self.assertEqual(result.returncode, 2)
        self.assertIn("DrawingGroup", result.stderr)
        self.assertFalse(out_dir.exists())


if __name__ == "__main__":
    unittest.main()
