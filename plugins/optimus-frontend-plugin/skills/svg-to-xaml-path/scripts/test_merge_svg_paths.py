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
MERGED_DATA = "F1 M0 0 L1 0 Z M2 0 L3 0 Z"
MERGED_XAML = '<Path Fill="#B8C6E0" Data="F1 M0 0 L1 0 Z M2 0 L3 0 Z" />'


class CliTestCase(unittest.TestCase):
    """Shared helper for driving the converter as the skill actually invokes it."""

    def run_cli(self, *arguments: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )


class MergeSvgPathsCliTests(CliTestCase):

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
        self.assertIn("multiple fill/stroke/fill-rule styles", result.stderr.lower())
        self.assertEqual(result.stdout.count("<Path "), 2)
        self.assertIn('Data="F1 M0 0 L1 0 Z"', result.stdout)
        self.assertIn('Data="F1 M2 0 L3 0 Z"', result.stdout)

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

    def test_repeated_class_attributes_emit_one_warning(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg" class="icon">
  <g style="fill: #B8C6E0">
    <path d="M0 0 L1 0 Z" class="primary" />
    <path d="M2 0 L3 0 Z" style="stroke: none" />
  </g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.count("class attributes were encountered"), 1)
        self.assertEqual(result.stdout.strip(), MERGED_XAML)

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
        self.assertEqual(result.stdout.strip(), "F1 M0 0 L1 0 Z")
        self.assertNotIn("traceback", result.stderr.lower())


class NonRenderedContentTests(CliTestCase):
    """Content SVG never paints must not reach the WPF geometry."""

    def test_paths_inside_non_rendered_containers_are_skipped(self) -> None:
        for container in ("defs", "clipPath", "mask", "symbol", "marker", "pattern"):
            svg = f"""<svg xmlns="http://www.w3.org/2000/svg">
  <{container}><path d="M9 9 L8 8 Z" fill="#B8C6E0" /></{container}>
  <path d="M0 0 L1 0 Z" fill="#B8C6E0" />
</svg>"""
            with self.subTest(container=container):
                result = self.run_cli("--stdin", "--format", "data", stdin=svg)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "F1 M0 0 L1 0 Z")

    def test_only_non_rendered_paths_fails_instead_of_emitting_geometry(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <defs><path d="M9 9 L8 8 Z" fill="#B8C6E0" /></defs>
</svg>"""
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("No <path>", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_display_none_prunes_the_whole_subtree(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <g display="none"><path d="M9 9 L8 8 Z" /></g>
  <g style="display: none"><path d="M7 7 L6 6 Z" /></g>
  <path d="M0 0 L1 0 Z" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "F1 M0 0 L1 0 Z")

    def test_hidden_visibility_skips_the_path_but_still_inherits(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <g visibility="hidden">
    <path d="M9 9 L8 8 Z" />
    <path d="M0 0 L1 0 Z" visibility="visible" />
  </g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "F1 M0 0 L1 0 Z")


class StyleDeclarationTests(CliTestCase):
    """Inline `style` paint must be honoured instead of silently falling back to black."""

    def test_style_fill_is_converted_instead_of_defaulting_to_black(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z" style="fill:#B8C6E0" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Fill="#B8C6E0"', result.stdout)
        self.assertNotIn("#000000", result.stdout)

    def test_style_outranks_the_presentation_attribute(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z" fill="#FF0000" style="fill: #B8C6E0" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Fill="#B8C6E0"', result.stdout)
        self.assertNotIn("#FF0000", result.stdout)

    def test_style_transform_still_stops_the_conversion(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <g style="transform: translate(2px, 0)"><path d="M0 0 L1 0 Z" /></g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("transform", result.stderr.lower())
        self.assertEqual(result.stdout, "")

    def test_unconverted_style_declarations_are_named_in_the_warning(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z" style="fill:#B8C6E0;opacity:0.5;stroke-width:2" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("opacity, stroke-width", result.stderr)
        self.assertNotIn("fill", result.stderr)


class FillRuleTests(CliTestCase):
    """SVG defaults to nonzero; WPF defaults to EvenOdd, so the prefix is mandatory."""

    def test_default_fill_rule_emits_the_nonzero_prefix(self) -> None:
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 0 Z" /></svg>'
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Data="F1 M0 0 L1 0 Z"', result.stdout)

    def test_evenodd_emits_the_evenodd_prefix_from_attribute_and_style(self) -> None:
        for markup in ('fill-rule="evenodd"', 'style="fill-rule: evenodd"'):
            svg = f'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 Z" {markup} /></svg>'
            with self.subTest(markup=markup):
                result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Data="F0 M0 0 Z"', result.stdout)

    def test_fill_rule_is_inherited_from_an_ancestor_group(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <g fill-rule="evenodd"><path d="M0 0 Z" /></g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Data="F0 M0 0 Z"', result.stdout)

    def test_mixed_fill_rules_split_same_coloured_paths(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg" fill="#B8C6E0">
  <path d="M0 0 L1 0 Z" />
  <path d="M2 0 L3 0 Z" fill-rule="evenodd" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("multiple fill/stroke/fill-rule styles", result.stderr.lower())
        self.assertEqual(result.stdout.count("<Path "), 2)
        self.assertIn('Data="F1 M0 0 L1 0 Z"', result.stdout)
        self.assertIn('Data="F0 M2 0 L3 0 Z"', result.stdout)

    def test_mixed_fill_rules_warn_that_data_output_uses_the_first_rule(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z" fill-rule="evenodd" />
  <path d="M2 0 L3 0 Z" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("multiple fill rules", result.stderr.lower())
        self.assertEqual(result.stdout.strip(), "F0 M0 0 L1 0 Z M2 0 L3 0 Z")


class SampleIconTests(CliTestCase):
    """The bundled fixture backs the worked example in SKILL.md."""

    def test_bundled_sample_icon_merges_to_one_path_with_a_class_warning(self) -> None:
        sample = SCRIPT.parent.parent / "assets" / "sample-icon.svg"
        result = self.run_cli("--file", str(sample), "--format", "xaml")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("class attributes were encountered", result.stderr)
        self.assertEqual(result.stdout.count("<Path "), 1)
        self.assertIn('Fill="#B8C6E0"', result.stdout)
        self.assertIn('Data="F1 M3 3h18v18H3V3zm2 2v14h14V5H5z M7 11h10v2H7v-2z"', result.stdout)


if __name__ == "__main__":
    unittest.main()
