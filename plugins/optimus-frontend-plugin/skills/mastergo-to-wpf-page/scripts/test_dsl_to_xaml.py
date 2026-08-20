"""Black-box CLI contract tests for dsl_to_xaml.py."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("dsl_to_xaml.py")
ASSETS = Path(__file__).with_name("assets")


class CliTestCase(unittest.TestCase):
    """Shared helper for driving the converter as the skill actually invokes it."""

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def convert(
        self,
        asset_name: str,
        *,
        indices: list[int] | None = None,
        mapping: dict | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        """Run the converter over one bundled asset and return the result and out dir.

        `indices` names the section-{N}.json numbers to write, so a test can reproduce a
        partial selection; `mapping` supplies a strict project mapping file.
        """
        with tempfile.TemporaryDirectory() as temporary:
            input_dir = Path(temporary) / "dsl"
            input_dir.mkdir()
            payload = json.loads((ASSETS / asset_name).read_text(encoding="utf-8"))
            (input_dir / "sections-list.json").write_text(
                json.dumps(payload["list"], ensure_ascii=False), encoding="utf-8"
            )
            numbers = indices if indices is not None else range(len(payload["sections"]))
            for number, section in zip(numbers, payload["sections"]):
                (input_dir / f"section-{number}.json").write_text(
                    json.dumps(section, ensure_ascii=False), encoding="utf-8"
                )
            out_dir = Path(temporary) / "out"
            arguments = ["--input", str(input_dir), "--out", str(out_dir)]
            if mapping is not None:
                mapping_path = Path(temporary) / "mapping.json"
                mapping_path.write_text(json.dumps(mapping, ensure_ascii=False), encoding="utf-8")
                arguments += ["--mapping", str(mapping_path)]
            result = self.run_cli(*arguments)
            if out_dir.exists():
                kept = Path(tempfile.mkdtemp())
                for item in out_dir.iterdir():
                    (kept / item.name).write_text(
                        item.read_text(encoding="utf-8"), encoding="utf-8"
                    )
                return result, kept
            return result, out_dir


class SkeletonTests(CliTestCase):
    def test_missing_input_directory_fails_without_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "nope"
            result = self.run_cli("--input", str(missing), "--out", temporary)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("error:", result.stderr.lower())
        self.assertEqual(result.stdout, "")

    def test_directory_without_sections_list_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cli("--input", temporary, "--out", temporary)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("sections-list.json", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_malformed_json_reports_the_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / "sections-list.json").write_text("{not json", encoding="utf-8")
            result = self.run_cli("--input", temporary, "--out", temporary)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("sections-list.json", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_non_utf8_json_reports_the_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / "sections-list.json").write_bytes(b"\xff\xfe\x00bad")
            result = self.run_cli("--input", temporary, "--out", temporary)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("sections-list.json", result.stderr)
        self.assertEqual(result.stdout, "")


class FlexLayoutTests(CliTestCase):
    """flexContainerInfo present means flow layout, never absolute positioning."""

    def test_flex_row_becomes_a_horizontal_stackpanel(self) -> None:
        result, out_dir = self.convert("flex-row.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<StackPanel Orientation="Horizontal"', xaml)
        self.assertIn("确定", xaml)
        self.assertIn("取消", xaml)

    def test_flex_children_never_get_canvas_coordinates(self) -> None:
        result, out_dir = self.convert("flex-row.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        body = xaml.split("<StackPanel", 1)[1]
        self.assertNotIn("Canvas.Left", body)
        self.assertNotIn("Canvas.Top", body)

    def test_flex_gap_becomes_margin_on_all_but_the_last_child(self) -> None:
        result, out_dir = self.convert("flex-row.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertEqual(xaml.count('Margin="0,0,8,0"'), 1)

    def test_the_last_child_gets_no_margin_at_all(self) -> None:
        result, out_dir = self.convert("flex-row.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        last_child = xaml.rsplit("<TextBlock", 1)[1]
        self.assertNotIn("Margin", last_child)

    def test_flex_grow_children_become_a_grid_with_star_columns(self) -> None:
        result, out_dir = self.convert("flex-grow.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("<Grid", xaml)
        self.assertEqual(xaml.count('<ColumnDefinition Width="*" />'), 2)
        self.assertIn('Grid.Column="0"', xaml)
        self.assertIn('Grid.Column="1"', xaml)

    def test_flex_grow_column_becomes_a_grid_with_star_rows(self) -> None:
        result, out_dir = self.convert("flex-grow-column.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("<Grid.RowDefinitions>", xaml)
        self.assertEqual(xaml.count('<RowDefinition Height="*" />'), 2)
        self.assertIn('Grid.Row="0"', xaml)
        self.assertIn('Grid.Row="1"', xaml)
        self.assertNotIn("ColumnDefinition", xaml)

    def test_flex_grow_column_gap_becomes_margin_on_all_but_the_last_child(self) -> None:
        result, out_dir = self.convert("flex-grow-column.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('Margin="0,0,0,8"', xaml)


class AbsoluteLayoutTests(CliTestCase):
    """A node without flexContainerInfo positions its children absolutely."""

    def test_absolute_container_becomes_a_canvas(self) -> None:
        result, out_dir = self.convert("absolute.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('Canvas.Left="32"', xaml)
        self.assertIn('Canvas.Top="16"', xaml)

    def test_section_shell_uses_the_splitcontainer_page_coordinates(self) -> None:
        result, out_dir = self.convert("absolute.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<Canvas Canvas.Left="10" Canvas.Top="20">', xaml)

    def test_nesting_is_preserved_rather_than_flattened(self) -> None:
        result, out_dir = self.convert("nested-mixed.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<StackPanel Orientation="Vertical">', xaml)
        stack_body = xaml.split('<StackPanel Orientation="Vertical">', 1)[1]
        self.assertIn("<Canvas", stack_body)
        self.assertIn('Canvas.Left="12"', stack_body)


class TokenTests(CliTestCase):
    """_token becomes a StaticResource; a dangling style reference is fatal."""

    def test_tokens_become_resource_dictionary_brushes(self) -> None:
        result, out_dir = self.convert("tokens.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        colors = (out_dir / "Colors.xaml").read_text(encoding="utf-8")
        self.assertIn('<SolidColorBrush x:Key="FillFill2" Color="#F2F3F5" />', colors)
        self.assertIn('<SolidColorBrush x:Key="TextText4" Color="#4E5969" />', colors)

    def test_the_original_token_name_is_kept_as_a_comment(self) -> None:
        result, out_dir = self.convert("tokens.json")

        colors = (out_dir / "Colors.xaml").read_text(encoding="utf-8")
        self.assertIn("Fill/Fill-2", colors)
        self.assertIn("Text/Text-4", colors)

    def test_the_page_references_brushes_rather_than_literal_colours(self) -> None:
        result, out_dir = self.convert("tokens.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("{StaticResource FillFill2}", xaml)
        self.assertIn("{StaticResource TextText4}", xaml)
        self.assertNotIn("#F2F3F5", xaml)

    def test_a_dangling_style_reference_is_fatal(self) -> None:
        result, _ = self.convert("broken-ref.json")

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("paint_9:9999", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_color_wins_over_a_fill_style_reference(self) -> None:
        result, out_dir = self.convert("tokens.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("#112233", xaml)
        self.assertNotIn("#FFFFFF", xaml)

    def test_resource_key_capitalises_each_segment(self) -> None:
        result, out_dir = self.convert("lowercase-token.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        colors = (out_dir / "Colors.xaml").read_text(encoding="utf-8")
        self.assertIn('x:Key="BrandBrandPrimary"', colors)


class ResourceWiringTests(CliTestCase):
    """The page must merge in Colors.xaml itself; nothing else wires it up."""

    def test_the_page_merges_in_colors_xaml_when_brushes_exist(self) -> None:
        result, out_dir = self.convert("tokens.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<ResourceDictionary Source="Colors.xaml" />', xaml)

    def test_a_token_free_design_does_not_reference_colors_xaml(self) -> None:
        result, out_dir = self.convert("absolute.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertNotIn("Colors.xaml", xaml)


class MultiRootLayoutTests(CliTestCase):
    """A section's node array can hold more than one top-level layer."""

    def test_each_root_node_keeps_its_own_canvas_coordinates(self) -> None:
        result, out_dir = self.convert("multi-root.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('Canvas.Left="0" Canvas.Top="0"', xaml)
        self.assertIn('Canvas.Left="300" Canvas.Top="400"', xaml)


class OpacityTests(CliTestCase):
    """A FRAME's opacity tints only its own background, never its children."""

    def test_frame_opacity_is_baked_into_the_background_alpha(self) -> None:
        result, out_dir = self.convert("opacity-frame.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("#804E5969", xaml)

    def test_no_opacity_property_is_emitted(self) -> None:
        result, out_dir = self.convert("opacity-frame.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertNotIn("Opacity=", xaml)

    def test_the_child_is_not_made_translucent(self) -> None:
        result, out_dir = self.convert("opacity-frame.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        child = xaml.split("子元素", 1)[0].rsplit("<TextBlock", 1)[1]
        self.assertNotIn("Opacity", child)

    def test_opacity_wins_over_a_token_even_when_both_are_present(self) -> None:
        result, out_dir = self.convert("token-with-opacity.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("#804E5969", xaml)
        self.assertNotIn("{StaticResource FillFill2}", xaml)


class TextTests(CliTestCase):
    """Text comes from the DSL's closed set — never invented, never dropped."""

    LONG = "这是一段超过五十个字符的很长的说明文字用于验证占位符能够被正确回填到生成的界面里"

    def test_a_long_text_placeholder_is_filled_from_rowtexts(self) -> None:
        result, out_dir = self.convert("long-text.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn(self.LONG, xaml)
        self.assertNotIn("T0|1:1234", xaml)

    def test_placeholder_boilerplate_is_skipped(self) -> None:
        result, out_dir = self.convert("placeholder-text.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertNotIn("Hillstone Design", xaml)
        self.assertIn("真实文案", xaml)

    def test_text_outside_the_alltexts_closed_set_is_fatal(self) -> None:
        result, _ = self.convert("hallucinated-text.json")

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("不在闭集里的文案", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_ampersand_and_angle_brackets_are_escaped(self) -> None:
        result, out_dir = self.convert("escaped-text.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("A &amp; B &lt;tag&gt;", xaml)
        self.assertNotIn("A & B <tag>", xaml)

    def test_a_node_with_no_position_and_no_flex_parent_is_fatal(self) -> None:
        result, _ = self.convert("missing-position.json")

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("relativeX", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_a_placeholder_with_no_matching_parentname_falls_back_to_order(self) -> None:
        result, out_dir = self.convert("long-text-order-fallback.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn(
            "这是通过顺序回退才能取到的很长的说明文字用于验证占位符没有命中parentName时仍可回填",
            xaml,
        )
        self.assertNotIn("T0|1:5678", xaml)


class IconTests(CliTestCase):
    """PATH nodes become placeholders plus a work list for extractSvg."""

    def test_path_nodes_become_icon_placeholders(self) -> None:
        result, out_dir = self.convert("icons.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("<!-- ICON:S0#0 -->", xaml)
        self.assertIn("<!-- ICON:S0#1 -->", xaml)

    def test_an_icon_manifest_is_written(self) -> None:
        result, out_dir = self.convert("icons.json")

        manifest = json.loads((out_dir / "icons.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 2)
        self.assertEqual(manifest[0]["svgShortKey"], "S0#0")
        self.assertEqual(manifest[0]["name"], "SearchIcon")
        self.assertEqual(manifest[1]["svgShortKey"], "S0#1")

    def test_icon_placeholders_keep_their_canvas_position(self) -> None:
        result, out_dir = self.convert("icons.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('Canvas.Left="4"', xaml)
        self.assertIn('Canvas.Left="28"', xaml)

    def test_a_path_without_a_shortkey_is_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_dir = Path(temporary) / "dsl"
            input_dir.mkdir()
            (input_dir / "sections-list.json").write_text(
                json.dumps({"rootMetadata": {"allTexts": []}, "splitContainers": [{}]}),
                encoding="utf-8",
            )
            (input_dir / "section-0.json").write_text(
                json.dumps(
                    {
                        "nodes": [
                            {
                                "type": "PATH",
                                "id": "11:1",
                                "name": "NoKey",
                                "layoutStyle": {"relativeX": 0, "relativeY": 0},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "--input", str(input_dir), "--out", str(Path(temporary) / "out")
            )

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("svgShortKey", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
