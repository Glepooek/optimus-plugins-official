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

    def convert(self, asset_name: str) -> tuple[subprocess.CompletedProcess[str], Path]:
        """Run the converter over one bundled asset and return the result and out dir."""
        with tempfile.TemporaryDirectory() as temporary:
            input_dir = Path(temporary) / "dsl"
            input_dir.mkdir()
            payload = json.loads((ASSETS / asset_name).read_text(encoding="utf-8"))
            (input_dir / "sections-list.json").write_text(
                json.dumps(payload["list"], ensure_ascii=False), encoding="utf-8"
            )
            for index, section in enumerate(payload["sections"]):
                (input_dir / f"section-{index}.json").write_text(
                    json.dumps(section, ensure_ascii=False), encoding="utf-8"
                )
            out_dir = Path(temporary) / "out"
            result = self.run_cli("--input", str(input_dir), "--out", str(out_dir))
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
        self.assertIn("<Canvas>", stack_body)
        self.assertIn('Canvas.Left="12"', stack_body)


if __name__ == "__main__":
    unittest.main()
