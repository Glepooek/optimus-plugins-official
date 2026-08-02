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
        self.assertIn("No convertible geometry", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_distinct_fills_emit_multiple_xaml_paths_and_warning(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z" fill="#B8C6E0" />
  <path d="M2 0 L3 0 Z" fill="#FF0000" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("multiple fill/stroke/fill-rule/transform", result.stderr.lower())
        self.assertEqual(result.stdout.count("<Path "), 2)
        self.assertIn('Data="F1 M0 0 L1 0 Z"', result.stdout)
        self.assertIn('Data="F1 M2 0 L3 0 Z"', result.stdout)

    def test_transformed_group_converts_to_a_render_transform(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <g transform="translate(2 0)">
    <path d="M0 0 L1 0 Z" fill="#B8C6E0" />
  </g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('<MatrixTransform Matrix="1,0,0,1,2,0" />', result.stdout)
        self.assertIn('Data="F1 M0 0 L1 0 Z"', result.stdout)

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

    def test_xml_decoded_quote_in_data_remains_escaped_and_parseable_xaml(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <path d="M0 0 L1 0 Z&quot;" fill="#B8C6E0" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("&quot;", result.stdout)
        path = ElementTree.fromstring(result.stdout)
        self.assertEqual(path.attrib["Data"], 'F1 M0 0 L1 0 Z"')

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
        self.assertIn("No convertible geometry", result.stderr)
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

    def test_style_transform_is_converted_like_the_attribute(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <g style="transform: translate(2 3)"><path d="M0 0 L1 0 Z" /></g>
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('<MatrixTransform Matrix="1,0,0,1,2,3" />', result.stdout)

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
        self.assertIn("multiple fill/stroke/fill-rule/transform", result.stderr.lower())
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


class PaintValidationTests(CliTestCase):
    """Paint WPF cannot parse must fail here, not at XAML load time."""

    def test_hex_and_keyword_colours_pass_through_unchanged(self) -> None:
        for colour in ("#ABC", "#ABCD", "#B8C6E0", "#80B8C6E0", "SteelBlue", "transparent"):
            svg = f'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 Z" fill="{colour}"/></svg>'
            with self.subTest(colour=colour):
                result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f'Fill="{colour}"', result.stdout)

    def test_rgb_notation_is_rewritten_to_wpf_hex(self) -> None:
        cases = {
            "rgb(184, 198, 224)": "#B8C6E0",
            "rgb(184 198 224)": "#B8C6E0",
            "rgb(100%, 0%, 0%)": "#FF0000",
            "rgba(184, 198, 224, 0.5)": "#80B8C6E0",
            "rgba(184, 198, 224, 100%)": "#FFB8C6E0",
        }
        for notation, expected in cases.items():
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg">'
                f'<path d="M0 0 Z" fill="{notation}"/></svg>'
            )
            with self.subTest(notation=notation):
                result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f'Fill="{expected}"', result.stdout)

    def test_unparseable_paint_fails_with_an_actionable_hint(self) -> None:
        cases = {
            "currentColor": "bind the WPF brush",
            "url(#gradient)": "flatten the gradient",
            "hsl(210, 40%, 80%)": "use a hex colour",
            "rgb(300, 0, 0)": "out-of-range channel",
        }
        for paint, hint in cases.items():
            svg = f'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 Z" fill="{paint}"/></svg>'
            with self.subTest(paint=paint):
                result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn(hint, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_the_failing_role_is_named_in_the_error(self) -> None:
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<path d="M0 0 Z" fill="#B8C6E0" stroke="currentColor"/></svg>'
        )
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("stroke value", result.stderr)

    def test_unused_inherited_paint_never_blocks_the_conversion(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg" fill="url(#grad)">
  <path d="M0 0 Z" fill="#B8C6E0" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Fill="#B8C6E0"', result.stdout)

    def test_data_format_validates_paint_too(self) -> None:
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 Z" fill="currentColor"/></svg>'
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(result.stdout, "")


class InputHardeningTests(CliTestCase):
    """Encoding and DTD handling, verified rather than assumed."""

    def test_non_ascii_markup_survives_a_utf8_pipe(self) -> None:
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><title>问答</title><path d="M0 0 Z"/></svg>'
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdin", "--format", "data"],
            input=svg.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(result.stdout.decode("utf-8").strip(), "F1 M0 0 Z")

    def test_utf8_bom_is_stripped_from_both_file_and_stdin(self) -> None:
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 Z"/></svg>'
        stdin_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdin", "--format", "data"],
            input=svg.encode("utf-8-sig"),
            capture_output=True,
            check=False,
            timeout=10,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            svg_file = Path(temporary_directory) / "bom.svg"
            svg_file.write_bytes(svg.encode("utf-8-sig"))
            file_result = self.run_cli("--file", str(svg_file), "--format", "data")

        self.assertEqual(stdin_result.returncode, 0, stdin_result.stderr.decode("utf-8", "replace"))
        self.assertEqual(stdin_result.stdout.decode("utf-8").strip(), "F1 M0 0 Z")
        self.assertEqual(file_result.returncode, 0, file_result.stderr)
        self.assertEqual(file_result.stdout.strip(), "F1 M0 0 Z")

    def test_internal_dtd_subset_is_rejected_instead_of_expanding_entities(self) -> None:
        svg = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE svg [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;">]>'
            '<svg xmlns="http://www.w3.org/2000/svg"><path d="&b;"/></svg>'
        )
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("internal DTD subset", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_the_standard_iconfont_doctype_preamble_still_converts(self) -> None:
        svg = (
            '<?xml version="1.0" standalone="no"?>'
            '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
            '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'
            '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 Z"/></svg>'
        )
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "F1 M0 0 Z")

    def test_an_external_entity_reference_never_reaches_the_output(self) -> None:
        svg = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">]>'
            '<svg xmlns="http://www.w3.org/2000/svg"><path d="&xxe;"/></svg>'
        )
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(result.stdout, "")


class BasicShapeTests(CliTestCase):
    """Basic shapes convert algebraically, so no geometry is invented or approximated."""

    def convert(self, markup: str) -> subprocess.CompletedProcess[str]:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg">{markup}</svg>'
        return self.run_cli("--stdin", "--format", "data", stdin=svg)

    def test_each_basic_shape_yields_its_spec_equivalent_path(self) -> None:
        cases = {
            '<rect x="1" y="2" width="10" height="5"/>': "M1,2 H11 V7 H1 Z",
            '<rect width="10" height="6" rx="2"/>': (
                "M2,0 H8 A2,2 0 0 1 10,2 V4 A2,2 0 0 1 8,6 "
                "H2 A2,2 0 0 1 0,4 V2 A2,2 0 0 1 2,0 Z"
            ),
            '<circle cx="5" cy="5" r="4"/>': (
                "M9,5 A4,4 0 0 1 5,9 A4,4 0 0 1 1,5 A4,4 0 0 1 5,1 A4,4 0 0 1 9,5 Z"
            ),
            '<ellipse cx="5" cy="5" rx="4" ry="2"/>': (
                "M9,5 A4,2 0 0 1 5,7 A4,2 0 0 1 1,5 A4,2 0 0 1 5,3 A4,2 0 0 1 9,5 Z"
            ),
            '<line x1="0" y1="0" x2="3" y2="4"/>': "M0,0 L3,4",
            '<polygon points="0,0 3,0 3,4"/>': "M0,0 L3,0 L3,4 Z",
            '<polyline points="0 0 3 0 3 4"/>': "M0,0 L3,0 L3,4",
        }
        for markup, expected in cases.items():
            with self.subTest(markup=markup):
                result = self.convert(markup)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), f"F1 {expected}")

    def test_a_single_rect_radius_mirrors_onto_the_other_axis(self) -> None:
        rx_only = self.convert('<rect width="10" height="6" rx="2"/>')
        ry_only = self.convert('<rect width="10" height="6" ry="2"/>')

        self.assertEqual(rx_only.returncode, 0, rx_only.stderr)
        self.assertEqual(rx_only.stdout, ry_only.stdout)

    def test_oversized_rect_radii_are_clamped_to_half_the_side(self) -> None:
        result = self.convert('<rect width="10" height="6" rx="99" ry="99"/>')

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("A5,3 0 0 1", result.stdout)
        self.assertNotIn("99", result.stdout)

    def test_shapes_that_never_paint_are_dropped(self) -> None:
        for markup in (
            '<rect width="0" height="6"/>',
            '<rect width="10" height="-1"/>',
            '<circle cx="5" cy="5" r="0"/>',
            '<ellipse cx="5" cy="5" rx="4"/>',
            '<polygon points="0,0"/>',
        ):
            with self.subTest(markup=markup):
                result = self.convert(f'{markup}<path d="M0 0 Z"/>')

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "F1 M0 0 Z")

    def test_shapes_inherit_paint_and_merge_with_paths(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg" fill="#B8C6E0">
  <path d="M0 0 Z" />
  <rect width="2" height="2" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("<Path "), 1)
        self.assertIn('Data="F1 M0 0 Z M0,0 H2 V2 H0 Z"', result.stdout)

    def test_shapes_honour_document_order_against_paths(self) -> None:
        result = self.convert('<rect width="2" height="2"/><path d="M9 9 Z"/>')

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "F1 M0,0 H2 V2 H0 Z M9 9 Z")

    def test_shapes_inside_defs_are_still_skipped(self) -> None:
        result = self.convert('<defs><rect width="9" height="9"/></defs><path d="M0 0 Z"/>')

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "F1 M0 0 Z")

    def test_transformed_shape_carries_its_matrix_like_a_path(self) -> None:
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g transform="translate(2 0)"><rect width="2" height="2"/></g></svg>'
        )
        result = self.run_cli("--stdin", "--format", "xaml", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Data="F1 M0,0 H2 V2 H0 Z"', result.stdout)
        self.assertIn('<MatrixTransform Matrix="1,0,0,1,2,0" />', result.stdout)

    def test_percentage_length_fails_because_no_viewport_is_read(self) -> None:
        result = self.convert('<rect width="50%" height="6"/>')

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("percentages need a viewport", result.stderr)

    def test_unreadable_points_fail_instead_of_dropping_the_shape(self) -> None:
        result = self.convert('<polygon points="0,0 3,x"/>')

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("unreadable points", result.stderr)


class UnconvertibleElementTests(CliTestCase):
    """Elements no path can reproduce must be named, never silently dropped."""

    def test_skipped_elements_are_named_in_one_warning(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <text x="0" y="0">hi</text>
  <image href="a.png" width="1" height="1" />
  <path d="M0 0 Z" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<image>, <text>", result.stderr)
        self.assertEqual(result.stdout.strip(), "F1 M0 0 Z")

    def test_text_children_do_not_warn_twice(self) -> None:
        svg = """<svg xmlns="http://www.w3.org/2000/svg">
  <text x="0" y="0"><tspan>a</tspan><tspan>b</tspan></text>
  <path d="M0 0 Z" />
</svg>"""
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.count("no exact path equivalent"), 1)
        self.assertNotIn("tspan", result.stderr)

    def test_an_svg_of_only_unconvertible_elements_fails_with_the_warning(self) -> None:
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><text x="0" y="0">hi</text></svg>'
        result = self.run_cli("--stdin", "--format", "data", stdin=svg)

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("No convertible geometry", result.stderr)
        self.assertEqual(result.stdout, "")


class TransformTests(CliTestCase):
    """SVG transforms map onto WPF MatrixTransform exactly, with no baked coordinates."""

    def convert(self, markup: str, output: str = "xaml") -> subprocess.CompletedProcess[str]:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg">{markup}</svg>'
        return self.run_cli("--stdin", "--format", output, stdin=svg)

    def matrix_of(self, result: subprocess.CompletedProcess[str]) -> list[float]:
        root = ElementTree.fromstring(result.stdout)
        transform = root.find("./Path.RenderTransform/MatrixTransform")
        self.assertIsNotNone(transform, result.stdout)
        return [float(value) for value in transform.attrib["Matrix"].split(",")]

    def test_each_transform_function_maps_to_its_matrix(self) -> None:
        cases = {
            "translate(2 3)": [1, 0, 0, 1, 2, 3],
            "translate(2)": [1, 0, 0, 1, 2, 0],
            "scale(2)": [2, 0, 0, 2, 0, 0],
            "scale(2 3)": [2, 0, 0, 3, 0, 0],
            "rotate(90)": [0, 1, -1, 0, 0, 0],
            "matrix(1 2 3 4 5 6)": [1, 2, 3, 4, 5, 6],
            "skewX(45)": [1, 0, 1, 1, 0, 0],
            "skewY(45)": [1, 1, 0, 1, 0, 0],
        }
        for source, expected in cases.items():
            with self.subTest(transform=source):
                result = self.convert(f'<path d="M0 0 Z" transform="{source}"/>')

                self.assertEqual(result.returncode, 0, result.stderr)
                for actual, want in zip(self.matrix_of(result), expected):
                    self.assertAlmostEqual(actual, want, places=6)

    def test_rotate_about_a_centre_keeps_that_centre_fixed(self) -> None:
        result = self.convert('<path d="M0 0 Z" transform="rotate(90 1 1)"/>')
        a, b, c, d, e, f = self.matrix_of(result)

        self.assertAlmostEqual(a * 1 + c * 1 + e, 1.0, places=6)
        self.assertAlmostEqual(b * 1 + d * 1 + f, 1.0, places=6)

    def test_transform_lists_compose_left_to_right(self) -> None:
        outer_first = self.convert('<path d="M0 0 Z" transform="translate(10 0) scale(2)"/>')
        inner_first = self.convert('<path d="M0 0 Z" transform="scale(2) translate(10 0)"/>')

        self.assertEqual(self.matrix_of(outer_first), [2, 0, 0, 2, 10, 0])
        self.assertEqual(self.matrix_of(inner_first), [2, 0, 0, 2, 20, 0])

    def test_ancestor_and_element_transforms_compose(self) -> None:
        result = self.convert(
            '<g transform="translate(10 0)"><path d="M0 0 Z" transform="scale(2)"/></g>'
        )

        self.assertEqual(self.matrix_of(result), [2, 0, 0, 2, 10, 0])

    def test_a_transform_in_style_is_honoured(self) -> None:
        result = self.convert('<path d="M0 0 Z" style="transform: translate(2 3)"/>')

        self.assertEqual(self.matrix_of(result), [1, 0, 0, 1, 2, 3])

    def test_untransformed_paths_stay_self_closing(self) -> None:
        result = self.convert('<path d="M0 0 Z" fill="#B8C6E0"/>')

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("RenderTransform", result.stdout)
        self.assertTrue(result.stdout.strip().endswith("/>"), result.stdout)

    def test_identity_transforms_do_not_emit_a_render_transform(self) -> None:
        for source in ("translate(0 0)", "scale(1)", "matrix(1 0 0 1 0 0)", "rotate(0)"):
            with self.subTest(transform=source):
                result = self.convert(f'<path d="M0 0 Z" transform="{source}"/>')

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("RenderTransform", result.stdout)

    def test_transforms_are_applied_to_converted_basic_shapes(self) -> None:
        result = self.convert('<rect width="2" height="2" transform="translate(5 5)"/>')

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Data="F1 M0,0 H2 V2 H0 Z"', result.stdout)
        self.assertEqual(self.matrix_of(result), [1, 0, 0, 1, 5, 5])

    def test_differing_transforms_split_otherwise_identical_paths(self) -> None:
        result = self.convert(
            '<path d="M0 0 Z" fill="#B8C6E0"/>'
            '<path d="M1 1 Z" fill="#B8C6E0" transform="translate(2 0)"/>'
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("transform combinations", result.stderr)
        self.assertEqual(result.stdout.count("<Path "), 2)

    def test_a_shared_transform_still_merges_into_one_path(self) -> None:
        result = self.convert(
            '<g transform="translate(2 0)" fill="#B8C6E0">'
            '<path d="M0 0 Z"/><path d="M1 1 Z"/></g>'
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("<Path "), 1)
        self.assertIn('Data="F1 M0 0 Z M1 1 Z"', result.stdout)
        self.assertEqual(self.matrix_of(result), [1, 0, 0, 1, 2, 0])

    def test_data_format_refuses_transformed_paths(self) -> None:
        result = self.convert('<path d="M0 0 Z" transform="translate(2 0)"/>', output="data")

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("--format xaml", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_data_format_still_works_without_transforms(self) -> None:
        result = self.convert('<path d="M0 0 Z" transform="translate(0 0)"/>', output="data")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "F1 M0 0 Z")

    def test_unparseable_transforms_stop_the_conversion(self) -> None:
        for source in ("translate(1 2 3)", "scale()", "foo(1)", "rotate(a)", "translate(1) junk"):
            with self.subTest(transform=source):
                result = self.convert(f'<path d="M0 0 Z" transform="{source}"/>')

                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("transform", result.stderr.lower())
                self.assertEqual(result.stdout, "")

    def test_the_emitted_xaml_is_well_formed(self) -> None:
        result = self.convert('<path d="M0 0 Z" fill="#B8C6E0" transform="rotate(45)"/>')

        root = ElementTree.fromstring(result.stdout)
        self.assertEqual(root.tag, "Path")
        self.assertEqual(root.attrib["Fill"], "#B8C6E0")


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
