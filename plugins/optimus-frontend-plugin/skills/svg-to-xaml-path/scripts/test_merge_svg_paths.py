"""Black-box CLI contract tests for merge_svg_paths.py."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree


SCRIPT = Path(__file__).with_name("merge_svg_paths.py")
SAME_STYLE_SVG = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z" fill="#B8C6E0" />
  <path d="M2 0 L3 0 Z" fill="#B8C6E0" />
</svg>"""
MERGED_DATA = "M0 0 L1 0 Z M2 0 L3 0 Z"
MERGED_XAML = '<Path Fill="#B8C6E0" Data="M0 0 L1 0 Z M2 0 L3 0 Z" />'


class MergeSvgPathsCliTests(unittest.TestCase):
    def run_cli(self, *arguments: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

    def test_same_style_namespaced_svg_merges_paths_to_data(self) -> None:
        result = self.run_cli("--stdin", "--format", "data", stdin=SAME_STYLE_SVG)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), MERGED_DATA)

    def test_same_style_namespaced_svg_merges_paths_to_xaml(self) -> None:
        result = self.run_cli("--stdin", "--format", "xaml", stdin=SAME_STYLE_SVG)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), MERGED_XAML)

    def test_file_and_stdin_data_outputs_are_successful_and_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            svg_file = Path(temporary_directory) / "icon.svg"
            svg_file.write_text(SAME_STYLE_SVG, encoding="utf-8")

            file_result = self.run_cli("--file", str(svg_file), "--format", "data")
        stdin_result = self.run_cli("--stdin", "--format", "data", stdin=SAME_STYLE_SVG)

        self.assertEqual(file_result.returncode, 0, file_result.stderr)
        self.assertEqual(stdin_result.returncode, 0, stdin_result.stderr)
        self.assertEqual(file_result.stdout, stdin_result.stdout)
        self.assertEqual(file_result.stdout.strip(), MERGED_DATA)

    def test_svg_without_paths_fails_without_stdout(self) -> None:
        result = self.run_cli(
            "--stdin",
            "--format",
            "data",
            stdin='<svg xmlns="http://www.w3.org/2000/svg"></svg>',
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No <path>", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_distinct_fills_emit_multiple_xaml_paths_and_warning(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z" fill="#B8C6E0" />
  <path d="M2 0 L3 0 Z" fill="#FF0000" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("multiple fill/stroke styles", result.stderr.lower())
        self.assertEqual(result.stdout.count("<Path "), 2)
        self.assertIn('Data="M0 0 L1 0 Z"', result.stdout)
        self.assertIn('Data="M2 0 L3 0 Z"', result.stdout)

    def test_transformed_group_fails_without_stdout(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <g transform="translate(2 0)">
    <path d="M0 0 L1 0 Z" fill="#B8C6E0" />
  </g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("transform", result.stderr.lower())
        self.assertIn("path 1", result.stderr.lower())
        self.assertIn("translate(2 0)", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_malformed_xml_returns_error_without_stdout(self) -> None:
        result = self.run_cli(
            "--stdin",
            "--format",
            "data",
            stdin='<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0">',
        )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("error:", result.stderr.lower())
        self.assertEqual(result.stdout, "")

    def test_missing_or_unreadable_file_returns_error_without_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_file = Path(temporary_directory) / "missing.svg"
            missing_result = self.run_cli("--file", str(missing_file), "--format", "data")
            unreadable_result = self.run_cli(
                "--file", temporary_directory, "--format", "data"
            )

        for result in (missing_result, unreadable_result):
            with self.subTest(stderr=result.stderr):
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("error:", result.stderr.lower())
                self.assertEqual(result.stdout, "")

    def test_inherited_fill_and_none_stroke_emit_fill_without_stroke(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <g fill="#B8C6E0" stroke="none">
    <path d="M0 0 L1 0 Z" />
  </g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Fill="#B8C6E0"', result.stdout)
        self.assertNotIn("Stroke=", result.stdout)

    def test_repeated_style_or_class_attributes_emit_one_warning(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg" class="icon">
  <g style="fill: #B8C6E0">
    <path d="M0 0 L1 0 Z" class="primary" />
    <path d="M2 0 L3 0 Z" style="stroke: none" />
  </g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.count("style or class attributes"), 1)

    def test_xml_decoded_quote_fill_remains_escaped_and_parseable_xaml(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z" fill="&quot;" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Fill="&quot;"', result.stdout)
        path = ElementTree.fromstring(result.stdout)
        self.assertEqual(path.attrib["Fill"], '"')

    def test_deeply_nested_groups_convert_without_traceback(self) -> None:
        nesting = 1_100
        svg = "<svg>" + "<g>" * nesting + '<path d="M0 0 L1 0 Z" />' + "</g>" * nesting + "</svg>"
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "M0 0 L1 0 Z")
        self.assertNotIn("traceback", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
