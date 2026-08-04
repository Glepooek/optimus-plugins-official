"""Black-box contracts for MasterGo-to-WPF optimization features."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from test_dsl_to_xaml import ASSETS, CliTestCase


class OptimizationTests(CliTestCase):
    def test_numeric_section_indices_render_in_numeric_order(self) -> None:
        payload = json.loads((ASSETS / "numeric-section-order.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            source, out = Path(temporary) / "dsl", Path(temporary) / "out"
            source.mkdir()
            (source / "sections-list.json").write_text(json.dumps(payload["list"], ensure_ascii=False), encoding="utf-8")
            (source / "section-10.json").write_text(json.dumps(payload["sections"][1], ensure_ascii=False), encoding="utf-8")
            (source / "section-2.json").write_text(json.dumps(payload["sections"][0], ensure_ascii=False), encoding="utf-8")
            result = self.run_cli("--input", str(source), "--out", str(out))
            xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertLess(xaml.index("第二"), xaml.index("第十"))

    def test_reliable_geometry_and_text_style_use_native_wpf_properties(self) -> None:
        result, out = self.convert("sized-border.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        for expected in ('<Border Width="200" Height="80" Background="#112233" Padding="4,8" BorderBrush="#445566" BorderThickness="1" CornerRadius="6">', 'Width="100" Height="24"', 'FontFamily="Inter"', 'FontSize="14"', 'FontWeight="SemiBold"', 'LineHeight="20"', 'TextAlignment="Center"', 'TextWrapping="Wrap"'):
            self.assertIn(expected, xaml)
        self.assertNotIn("Opacity=", xaml)

    def test_rich_text_generates_escaped_runs(self) -> None:
        result, out = self.convert("rich-text.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<Run Text="粗" FontWeight="Bold" Foreground="#111111" />', xaml)
        self.assertIn('<Run Text="细" FontSize="12" Foreground="#222222" />', xaml)

    def test_image_and_instance_handoffs_are_visible_in_xaml_and_sidecars(self) -> None:
        image_result, image_out = self.convert("images.json")
        instance_result, instance_out = self.convert("instance-variants.json")
        self.assertEqual(image_result.returncode, 0, image_result.stderr)
        self.assertEqual(instance_result.returncode, 0, instance_result.stderr)
        image_xaml = (image_out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        images = json.loads((image_out / "images.json").read_text(encoding="utf-8"))
        instance_xaml = (instance_out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        report = json.loads((instance_out / "conversion-report.json").read_text(encoding="utf-8"))
        self.assertIn("TODO IMAGE:i:1", image_xaml)
        self.assertIn("<Image", image_xaml)
        self.assertEqual(images[0]["status"], "unrecoverable")
        self.assertIn("TODO INSTANCE_VARIANTS", instance_xaml)
        self.assertTrue(report["manualHandoffs"])

    def test_report_and_mapping_only_emit_registered_anchor_controls(self) -> None:
        payload = {"list": {"rootMetadata": {"allTexts": []}, "splitContainers": [{}]}, "sections": [{"nodes": [{"type": "FRAME", "id": "a:1", "name": "Save <--@ActionButton.Primary-->", "_token": "Fill/Primary", "_color": "#123456", "layoutStyle": {"width": 80, "height": 32, "relativeX": 0, "relativeY": 0}}]}]}
        mapping = {"resources": {"Fill/Primary": "BrandPrimaryBrush"}, "xmlns": {"controls": "clr-namespace:App.Controls"}, "components": {"ActionButton": {"xmlns": "controls", "type": "PrimaryButton", "allowedProperties": {"Variant": ["Primary"]}, "variants": {}}}}
        with tempfile.TemporaryDirectory() as temporary:
            root, out = Path(temporary), Path(temporary) / "out"
            source = root / "dsl"
            source.mkdir()
            (source / "sections-list.json").write_text(json.dumps(payload["list"]), encoding="utf-8")
            (source / "section-0.json").write_text(json.dumps(payload["sections"][0]), encoding="utf-8")
            mapping_path = root / "mapping.json"
            mapping_path.write_text(json.dumps(mapping), encoding="utf-8")
            result = self.run_cli("--input", str(source), "--out", str(out), "--mapping", str(mapping_path))
            xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
            report = json.loads((out / "conversion-report.json").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn('<controls:PrimaryButton Width="80" Height="32" Variant="Primary" />', xaml)
        self.assertIn('xmlns:controls="clr-namespace:App.Controls"', xaml)
        self.assertEqual(report["tokenCoverage"]["mapped"], 1)
        self.assertEqual(report["componentMapping"][0]["source"], "anchor")


class SectionPlacementTests(CliTestCase):
    """A partial selection must keep each section's own page-level offset."""

    def test_partial_selection_uses_the_matching_splitcontainer(self) -> None:
        result, out = self.convert("partial-selection.json", indices=[2, 3])
        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<Canvas Canvas.Left="2000" Canvas.Top="0">', xaml)
        self.assertIn('<Canvas Canvas.Left="3000" Canvas.Top="0">', xaml)
        self.assertNotIn('<Canvas Canvas.Left="0" Canvas.Top="0">', xaml)

    def test_the_report_names_the_real_section_index(self) -> None:
        result, out = self.convert("partial-selection.json", indices=[2, 3])
        report = json.loads((out / "conversion-report.json").read_text(encoding="utf-8"))
        self.assertEqual([entry["index"] for entry in report["sections"]], [2, 3])


class ValueSafetyTests(CliTestCase):
    """A value that cannot be proven safe never reaches the XAML."""

    def test_object_stroke_is_rejected_rather_than_stringified(self) -> None:
        result, out = self.convert("invalid-values.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertNotIn("BorderBrush", xaml)
        self.assertNotIn("'r':", xaml)

    def test_unparsable_text_styles_are_dropped_but_valid_ones_survive(self) -> None:
        result, out = self.convert("invalid-values.json")
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertNotIn("FontWeight=", xaml)
        self.assertNotIn("justified", xaml)
        self.assertIn('FontFamily="Inter"', xaml)

    def test_no_attribute_value_opens_a_markup_extension(self) -> None:
        result, out = self.convert("invalid-values.json")
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        for value in re.findall(r'="([^"]*)"', xaml):
            if value.startswith("{"):
                self.assertTrue(value.startswith("{StaticResource "), value)

    def test_every_rejected_value_is_recorded_as_a_fallback(self) -> None:
        result, out = self.convert("invalid-values.json")
        report = json.loads((out / "conversion-report.json").read_text(encoding="utf-8"))
        reasons = {(entry["nodeId"], entry["reason"]) for entry in report["fallbacks"]}
        self.assertIn("v:1", {node for node, _ in reasons})
        self.assertIn("v:2", {node for node, _ in reasons})

    def test_opacity_with_no_paint_to_bake_into_is_reported(self) -> None:
        result, out = self.convert("invalid-values.json")
        report = json.loads((out / "conversion-report.json").read_text(encoding="utf-8"))
        ghosts = [entry for entry in report["fallbacks"] if entry["nodeId"] == "v:3"]
        self.assertTrue(ghosts, report["fallbacks"])
        self.assertIn("opacity", ghosts[0]["reason"])


class AnchorSafetyTests(CliTestCase):
    """A registered anchor may replace a node only when nothing would be lost."""

    MAPPING = {
        "resources": {},
        "xmlns": {"controls": "clr-namespace:App.Controls"},
        "components": {
            "ActionButton": {
                "xmlns": "controls",
                "type": "PrimaryButton",
                "allowedProperties": {"Variant": ["Primary"]},
                "variants": {},
            }
        },
    }

    def test_a_leaf_anchor_still_becomes_the_registered_control(self) -> None:
        result, out = self.convert("anchor-with-children.json", mapping=self.MAPPING)
        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<controls:PrimaryButton', xaml)

    def test_an_anchor_never_swallows_its_child_content(self) -> None:
        result, out = self.convert("anchor-with-children.json", mapping=self.MAPPING)
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("保存", xaml)
        self.assertIn("行内", xaml)

    def test_an_anchor_on_a_flex_container_is_arbitrated_not_ignored(self) -> None:
        result, out = self.convert("anchor-with-children.json", mapping=self.MAPPING)
        report = json.loads((out / "conversion-report.json").read_text(encoding="utf-8"))
        recorded = {entry["nodeId"] for entry in report["fallbacks"]}
        self.assertIn("c:3", recorded)

    def test_a_rejected_anchor_explains_itself_in_the_report(self) -> None:
        result, out = self.convert("anchor-with-children.json", mapping=self.MAPPING)
        report = json.loads((out / "conversion-report.json").read_text(encoding="utf-8"))
        reasons = {entry["nodeId"]: entry["reason"] for entry in report["fallbacks"]}
        self.assertIn("c:1", reasons)
        self.assertIn("child", reasons["c:1"])


class GridSizingTests(CliTestCase):
    """Only a child that actually grows may claim star sizing."""

    def test_non_growing_children_keep_auto_columns(self) -> None:
        result, out = self.convert("mixed-grow.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertEqual(xaml.count('<ColumnDefinition Width="Auto" />'), 2)
        self.assertEqual(xaml.count('<ColumnDefinition Width="*" />'), 1)


if __name__ == "__main__":
    import unittest

    unittest.main()
