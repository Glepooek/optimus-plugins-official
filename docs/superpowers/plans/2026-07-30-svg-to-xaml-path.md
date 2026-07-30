# SVG to XAML Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `svg-to-xaml-path` frontend Skill and a dependency-free Python CLI that turns SVG `<path>` data into WPF `Path.Data` or XAML.

**Architecture:** The CLI owns parsing, ordered path extraction, effective inherited `fill`/`stroke` selection, rendering, and explicit diagnostics. `SKILL.md` directs agents to the CLI or a manual equivalent, explains that concatenating SVG `d` values creates one WPF geometry with multiple figures rather than performing a boolean union, and specifies all unsupported cases. The Skill is independently testable with `unittest`; repository metadata advertises it as a new frontend capability.

**Tech Stack:** Python 3 standard library (`argparse`, `dataclasses`, `pathlib`, `subprocess`, `unittest`, `xml.etree.ElementTree`), Markdown, JSON, WPF XAML, marketplace JSON.

---

## File structure

| File | Responsibility |
|---|---|
| `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py` | Public CLI, SVG parsing, style inheritance, data/XAML rendering and diagnostics. |
| `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/test_merge_svg_paths.py` | Black-box CLI tests using only the standard library. |
| `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/SKILL.md` | User-facing invocation, process, conversion rules and limits. |
| `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/CHANGELOG.md` | Initial `1.0.0` release record. |
| `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/test-prompts.json` | Manual/evaluation prompts that exercise normal and unsupported workflows. |
| `.claude-plugin/marketplace.json` | Minor repository-version bump to `8.1.0` and frontend plugin description update. |
| `README.md` | Frontend plugin capability and slash-command documentation. |

## Task 1: Define the CLI contract with failing tests

**Files:**
- Create: `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/test_merge_svg_paths.py`
- Create later: `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py`

- [ ] **Step 1: Write the failing black-box tests**

```python
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("merge_svg_paths.py")
SAME_STYLE_SVG = '''<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 0 Z" fill="#B8C6E0"/><path d="M2 0 L3 0 Z" fill="#B8C6E0"/></svg>'''
MIXED_STYLE_SVG = '''<svg><path d="M0 0 L1 0 Z" fill="#112233"/><path d="M2 0 L3 0 Z" fill="#445566"/></svg>'''


def run_cli(*arguments: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )


class MergeSvgPathsTests(unittest.TestCase):
    def test_inline_svg_merges_ordered_paths_into_data(self) -> None:
        result = run_cli("--svg", SAME_STYLE_SVG, "--format", "data")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "M0 0 L1 0 Z M2 0 L3 0 Z")

    def test_matching_paints_render_as_one_wpf_path(self) -> None:
        result = run_cli("--svg", SAME_STYLE_SVG, "--format", "xaml")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            '<Path Fill="#B8C6E0" Data="M0 0 L1 0 Z M2 0 L3 0 Z" />',
        )

    def test_file_and_standard_input_are_both_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg_file = Path(directory) / "icon.svg"
            svg_file.write_text(SAME_STYLE_SVG, encoding="utf-8")
            from_file = run_cli("--file", str(svg_file), "--format", "data")
        from_stdin = run_cli("--stdin", "--format", "data", stdin=SAME_STYLE_SVG)
        self.assertEqual(from_file.returncode, 0, from_file.stderr)
        self.assertEqual(from_stdin.returncode, 0, from_stdin.stderr)
        self.assertEqual(from_file.stdout, from_stdin.stdout)

    def test_missing_path_is_a_clear_error(self) -> None:
        result = run_cli("--svg", "<svg><rect width=\"10\" height=\"10\"/></svg>")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No <path>", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_different_fills_emit_multiple_paths_and_warning(self) -> None:
        result = run_cli("--svg", MIXED_STYLE_SVG, "--format", "xaml")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("multiple fill/stroke styles", result.stderr)
        self.assertEqual(result.stdout.count("<Path "), 2)
        self.assertIn('Fill="#112233" Data="M0 0 L1 0 Z"', result.stdout)
        self.assertIn('Fill="#445566" Data="M2 0 L3 0 Z"', result.stdout)

    def test_transform_fails_without_geometry_output(self) -> None:
        result = run_cli("--svg", '<svg><g transform="translate(2 0)"><path d="M0 0 Z"/></g></svg>')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("transform", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and record the expected RED result**

Run:

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/test_merge_svg_paths.py -v
```

Expected: all six tests fail because `scripts/merge_svg_paths.py` does not exist; failures must be due to the missing CLI, not assertion or test-discovery errors.

## Task 2: Implement the minimal SVG-to-WPF CLI

**Files:**
- Create: `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py`
- Test: `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/test_merge_svg_paths.py`

- [ ] **Step 1: Add the parser model and extraction functions**

```python
from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET

DEFAULT_FILL = "#000000"


class ConversionError(ValueError):
    pass


@dataclass(frozen=True)
class PathRecord:
    data: str
    fill: str | None
    stroke: str | None
    index: int


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def paint(value: str | None, default: str | None) -> str | None:
    if value is None:
        return default
    return None if value.strip().lower() == "none" else value.strip()


def extract_paths(svg_text: str) -> tuple[list[PathRecord], list[str]]:
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as error:
        raise ConversionError(f"Invalid SVG XML: {error}") from error

    records: list[PathRecord] = []
    warnings: list[str] = []

    def visit(element: ET.Element, fill: str | None, stroke: str | None, transforms: list[str]) -> None:
        if "style" in element.attrib or "class" in element.attrib:
            warnings.append("SVG style/class attributes are not converted; inline fill/stroke attributes are required.")
        current_fill = paint(element.get("fill"), fill)
        current_stroke = paint(element.get("stroke"), stroke)
        current_transforms = transforms + ([element.get("transform")] if element.get("transform") else [])
        if local_name(element.tag) == "path":
            data = (element.get("d") or "").strip()
            if data:
                if current_transforms:
                    raise ConversionError(f"Unsupported transform on path {len(records) + 1}: {'; '.join(current_transforms)}")
                records.append(PathRecord(data, current_fill, current_stroke, len(records) + 1))
        for child in element:
            visit(child, current_fill, current_stroke, current_transforms)

    visit(root, DEFAULT_FILL, None, [])
    if not records:
        raise ConversionError("No <path> elements with a non-empty d attribute were found.")
    return records, list(dict.fromkeys(warnings))
```

- [ ] **Step 2: Add renderers and the CLI entry point**

```python
import argparse
import sys
from pathlib import Path


def xaml_path(record: PathRecord, data: str | None = None) -> str:
    attributes: list[tuple[str, str]] = []
    if record.fill is not None:
        attributes.append(("Fill", record.fill))
    if record.stroke is not None:
        attributes.append(("Stroke", record.stroke))
    attributes.append(("Data", data if data is not None else record.data))
    rendered = " ".join(f'{name}="{value}"' for name, value in attributes)
    return f"<Path {rendered} />"


def render(records: list[PathRecord], output_format: str) -> tuple[str, list[str]]:
    merged_data = " ".join(record.data for record in records)
    if output_format == "data":
        return merged_data, []
    styles = {(record.fill, record.stroke) for record in records}
    if len(styles) == 1:
        return xaml_path(records[0], merged_data), []
    warning = "SVG contains multiple fill/stroke styles; emitting one WPF Path per SVG path to preserve styles and drawing order."
    return "\n".join(xaml_path(record) for record in records), [warning]


def read_source(arguments: argparse.Namespace) -> str:
    if arguments.svg is not None:
        return arguments.svg
    if arguments.stdin:
        return sys.stdin.read()
    try:
        return Path(arguments.file).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise ConversionError(f"Cannot read SVG file '{arguments.file}': {error}") from error


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract SVG path data for WPF XAML.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Path to an SVG file.")
    source.add_argument("--svg", help="Inline SVG text.")
    source.add_argument("--stdin", action="store_true", help="Read SVG text from standard input.")
    parser.add_argument("--format", choices=("data", "xaml"), default="xaml")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        records, extraction_warnings = extract_paths(read_source(arguments))
        output, render_warnings = render(records, arguments.format)
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for warning in extraction_warnings + render_warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run the tests and verify GREEN**

Run:

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/test_merge_svg_paths.py -v
```

Expected: six passing tests, no tracebacks or warnings other than the intentionally asserted CLI diagnostics.

- [ ] **Step 4: Run the real supplied SVG as a smoke test**

Run:

```powershell
python plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py --file 'C:\Users\Administrator\Downloads\AI问答.svg' --format xaml
```

Expected: exit code `0`; one `<Path>` line with `Fill="#B8C6E0"` and a `Data` attribute containing both sample path figures.

## Task 3: Add the discoverable Skill documentation and evaluations

**Files:**
- Create: `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/SKILL.md`
- Create: `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/CHANGELOG.md`
- Create: `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/test-prompts.json`
- Reference: `plugins/optimus-frontend-plugin/skills/wpf-xaml-performance/SKILL.md`

- [ ] **Step 1: Add frontmatter and concise trigger coverage**

```yaml
---
name: svg-to-xaml-path
version: 1.0.0
description: Use when converting an SVG file or SVG markup into WPF XAML Path.Data, extracting SVG path d attributes, or combining multiple SVG paths for a WPF icon.
metadata:
  version: "1.0.0"
  author: desktop client team
compatibility: Requires Python 3 for the bundled helper script; accepts local SVG files or pasted SVG markup and produces WPF Path.Data or XAML.
allowed-tools: Read Write Glob Grep Shell
---
```

- [ ] **Step 2: Document the operational workflow and limitations**

Include exact calls:

```powershell
python "plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py" --file "C:\path\icon.svg" --format xaml
python "plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py" --svg '<svg>...</svg>' --format data
Get-Content "C:\path\icon.svg" | python "plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py" --stdin --format data
```

Document that the default result concatenates ordered `d` values into one WPF Geometry with multiple figures; it is not boolean union. State that `Path.Data` output omits visual style, matching `fill`/`stroke` produces one XAML `Path`, and different paint styles produce multiple XAML `Path` elements. State unsupported `transform`, non-`path` SVG elements, CSS/style attributes, SVG `viewBox` conversion, and boolean merge explicitly, with the correct fallback for each.

- [ ] **Step 3: Add initial changelog and eval prompts**

```markdown
# Changelog

## [1.0.0] - 2026-07-30

### Added
- SVG `<path>` extraction and ordered multi-figure `Path.Data` merging for WPF XAML.
- Dependency-free Python CLI for SVG files, inline SVG markup and standard input.
- Diagnostics for unsupported transforms and mismatched SVG paint styles.
```

Create `test-prompts.json` with four named valid JSON cases: supplied SVG file conversion, inline SVG data-only conversion, a different-fill SVG that must produce multiple paths, and a transformed SVG that must explain its unsupported status rather than invent geometry.

- [ ] **Step 4: Validate the Skill’s static artifacts**

Run:

```powershell
python -c "import json, pathlib; json.load(open('plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/test-prompts.json', encoding='utf-8')); text=pathlib.Path('plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/SKILL.md').read_text(encoding='utf-8'); assert text.startswith('---\n') and '\nname: svg-to-xaml-path\n' in text and '\nversion: 1.0.0\n' in text; print('Skill artifacts valid')"
```

Expected: `Skill artifacts valid`.

## Task 4: Publish the new capability in repository metadata and docs

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`

- [ ] **Step 1: Bump the marketplace version and improve the frontend description**

Change the marketplace version exactly from `8.0.6` to `8.1.0`. Expand only the existing `optimus-frontend-plugin` description to mention SVG Path extraction/merging for WPF XAML alongside its existing capabilities. Do not alter plugin names, sources, owners, repository URL, or other plugin entries.

- [ ] **Step 2: Add the new frontend feature to the README**

Update the frontend plugin row so its responsibility includes converting SVG `<path>` data to WPF XAML. Add the following adjacent to the existing WPF command example:

```bash
# 从 SVG 提取并合并路径，转换为 WPF Path.Data
/optimus-frontend-plugin:svg-to-xaml-path
```

- [ ] **Step 3: Validate JSON and documentation references**

Run:

```powershell
python -c "import json; data=json.load(open('.claude-plugin/marketplace.json', encoding='utf-8')); assert data['version'] == '8.1.0'; assert any(p['name'] == 'optimus-frontend-plugin' for p in data['plugins']); print('marketplace valid')"
python -c "from pathlib import Path; text=Path('README.md').read_text(encoding='utf-8'); assert '/optimus-frontend-plugin:svg-to-xaml-path' in text; print('README command documented')"
```

Expected: `marketplace valid` and `README command documented`.

## Task 5: Perform final repository-level validation

**Files:**
- Verify: `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/**`
- Verify: `.claude-plugin/marketplace.json`
- Verify: `README.md`

- [ ] **Step 1: Run the full helper-script test suite**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/test_merge_svg_paths.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Verify the supplied SVG has one generated WPF Path**

```powershell
python plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py --file 'C:\Users\Administrator\Downloads\AI问答.svg' --format xaml
```

Expected: exit code `0`, one `<Path>` output, `Fill="#B8C6E0"`, and both original SVG `d` sequences in `Data`.

- [ ] **Step 3: Test-load the repository plugin locally if the Claude CLI is installed**

```powershell
claude --plugin-dir "E:\ProjectxPlex\WPFCodePlex\optimus-plugins-official"
```

Expected: the CLI accepts the plugin directory and exposes `svg-to-xaml-path`; if the executable is unavailable or requires interactive sign-in, record that limitation and retain the static and script validation evidence.

- [ ] **Step 4: Inspect the final diff against the approved scope**

Run:

```powershell
git diff --check
git diff -- .claude-plugin/marketplace.json README.md docs/superpowers/specs/2026-07-30-svg-to-xaml-path-design.md docs/superpowers/plans/2026-07-30-svg-to-xaml-path.md plugins/optimus-frontend-plugin/skills/svg-to-xaml-path
```

Expected: no whitespace errors; changed files exactly correspond to the design, plan, Skill, script/tests, marketplace metadata, and README. Do not create a commit unless the user explicitly requests one.

## Self-review

- **Spec coverage:** Task 1 establishes failing tests; Task 2 supplies all three inputs, both output modes, ordered concatenation, inherited `fill`/`stroke`, errors and transform detection. Task 3 provides Skill, changelog and eval prompts. Task 4 updates the required marketplace version and documentation. Task 5 validates tests, the supplied SVG and plugin loading.
- **No placeholders:** No `TODO`, `TBD`, vague error-handling instructions, or undefined interfaces remain. The public CLI functions and exact expected behavior are defined in Task 2 before later documentation references them.
- **Type consistency:** `PathRecord`, `ConversionError`, `extract_paths`, `render`, `main`, CLI arguments and both output formats use the same names throughout. The plan intentionally excludes JSON and all `viewBox`/`Viewbox` handling.
