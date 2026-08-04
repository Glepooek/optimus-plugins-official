# mastergo-icon-expoter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `mastergo-icon-expoter` frontend Skill: a dependency-light Python CLI (`icon_exporter.py`) plus `SKILL.md` that turns a MasterGo design's icon/background nodes into WPF-ready `Icons.xaml` (Geometry/DrawingImage resources), PNG bitmaps, and an `icons-manifest.json`, without touching any user page code.

**Architecture:** Thick script, thin orchestration. The agent side (`SKILL.md`) owns MCP calls, the CHECKPOINT gate, and delegating SVG→`Path.Data` conversion to the sibling `svg-to-xaml-path` Skill; it transcribes results verbatim into a JSON contract file (`input.json`). The CLI (`icon_exporter.py`) owns everything deterministic: format decision, name derivation, XAML assembly, manifest generation, and a pre-write self-check — all pure functions over the contract, with zero MCP/network access. This mirrors `dsl_to_xaml.py`'s `ConversionError` + atomic-write pattern from the sibling `mastergo-to-wpf` Skill.

**Tech Stack:** Python 3 standard library (`argparse`, `dataclasses`, `json`, `pathlib`, `re`, `unittest`), optional `Pillow` for `.ico` synthesis (feature-detected, never a hard dependency), Markdown, WPF XAML, marketplace JSON.

## Global Constraints

- Design spec is `docs/superpowers/specs/2026-08-04-mastergo-icon-exporter-design.md` — every requirement in it must map to a task below.
- The script never calls MCP, reads a token, or touches the network — same discipline as `dsl_to_xaml.py` and `merge_svg_paths.py`.
- `svg-to-xaml-path`'s returned `Data` string (including its `F0`/`F1` prefix) must be transcribed into `input.json` verbatim by the agent; the CLI's `validate` layer hard-fails if the prefix is missing — this is the enforcement point for that rule, not documentation alone.
- Failure contract: on any hard error the CLI prints exactly one line `error: ...` to stderr, produces empty stdout, and writes zero files (this applies to `validate` failures and `selfcheck` failures alike — both must leave the output directory untouched).
- Per-icon failures (unresolved SVG fetch, `svg-to-xaml-path` exit 2 on `currentColor`/gradients) degrade that one icon to `sourceKind: "unresolved"` in the manifest and do not abort the batch; only contract violations and self-check failures abort the whole run.
- `needs-manual` manifest entries must always carry a non-empty `reason` and must never be reported as `exported`.
- Naming derivation is lexical only (no semantic guessing) — see the design doc's derivation table; this exact table becomes the test fixture in Task 3.
- New skill under `plugins/` → marketplace version is a **Minor** bump.
- Repository test runner is `python -m unittest discover ... -p "test_*.py"` (no `pytest` available locally).

---

## File Structure

| File | Responsibility |
|---|---|
| `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py` | Public CLI: contract validation, format decision, naming, XAML/manifest rendering, self-check, atomic write, optional `.ico` synthesis. |
| `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py` | Black-box CLI tests (subprocess-driven, matching `test_dsl_to_xaml.py`/`test_merge_svg_paths.py` style). |
| `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/SKILL.md` | Agent-facing orchestration: Step 0–5, CHECKPOINT structure, red lines, delivery discipline. |
| `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/CHANGELOG.md` | Initial `[1.0.0]` entry. |
| `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/README.md` | Five-section README per `.claude/rules/skill-authoring.md`. |
| `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/references/wpf-xaml-icon-sepc.md` | Already complete (prior session) — referenced, not modified. |
| `.claude-plugin/marketplace.json` | Minor version bump; frontend plugin description gains icon-export capability. |
| `README.md` (repo root) | New slash-command example under the frontend plugin section. |

---

## Task 1: Contract validation (`validate`) with failing tests

**Files:**
- Create: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py`
- Create later: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py`

**Interfaces:**
- Produces: `ConversionError(Exception)`; `load_input(path: Path) -> dict[str, Any]` (reads and JSON-parses, wraps I/O and JSON errors as `ConversionError` naming the file — mirrors `read_json` in `dsl_to_xaml.py`); `validate_contract(payload: dict[str, Any]) -> list[dict[str, Any]]` (returns the validated `icons` list or raises `ConversionError` naming the offending `nodeId`/`svgShortKey`).

- [ ] **Step 1: Write the failing black-box tests**

```python
"""Black-box CLI contract tests for icon_exporter.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and record the expected RED result**

Run:

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: all eight tests fail because `scripts/icon_exporter.py` does not exist; failures must be due to the missing CLI (import/collection error), not assertion mismatches.

- [ ] **Step 3: Implement `ConversionError`, `load_input`, and `validate_contract`**

```python
"""Convert MasterGo icon export contract JSON into WPF-ready icon assets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class ConversionError(Exception):
    """An input or conversion error that should be shown to the user."""


FILL_RULE_PREFIX = re.compile(r"\A(F0|F1)\s")
VALID_SOURCE_KINDS = {"vector", "bitmap"}


def load_input(path: Path) -> dict[str, Any]:
    """Read and parse the agent-produced contract file, naming it in any error."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise ConversionError(f"could not read {path.name}: {error}") from error
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ConversionError(f"{path.name} is not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ConversionError(f"{path.name} must contain a JSON object")
    return payload


def _icon_label(icon: dict[str, Any]) -> str:
    node_id = icon.get("nodeId", "?")
    name = icon.get("dslName", "unnamed")
    return f"nodeId={node_id} ({name})"


def validate_contract(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the icons list; raise ConversionError naming the first violation found."""
    icons = payload.get("icons")
    if not isinstance(icons, list):
        raise ConversionError("input.json must contain an 'icons' array")
    validated: list[dict[str, Any]] = []
    for icon in icons:
        if not isinstance(icon, dict):
            raise ConversionError("each entry in 'icons' must be a JSON object")
        source_kind = icon.get("sourceKind")
        if source_kind not in VALID_SOURCE_KINDS:
            raise ConversionError(
                f"{_icon_label(icon)}: sourceKind must be 'vector' or 'bitmap', got {source_kind!r}"
            )
        if "nodeId" not in icon or not icon.get("nodeId"):
            raise ConversionError(f"icon entry {icon.get('dslName', 'unnamed')!r} is missing nodeId")
        paths = icon.get("paths")
        if not isinstance(paths, list):
            raise ConversionError(f"{_icon_label(icon)}: paths must be an array")
        if source_kind == "vector":
            if not icon.get("svgShortKey"):
                raise ConversionError(f"{_icon_label(icon)}: vector icon is missing svgShortKey")
            if not paths:
                raise ConversionError(f"{_icon_label(icon)}: vector icon has empty paths")
            for path_entry in paths:
                data = path_entry.get("data") if isinstance(path_entry, dict) else None
                if not isinstance(data, str) or not FILL_RULE_PREFIX.match(data):
                    raise ConversionError(
                        f"{_icon_label(icon)}: path Data is missing a literal 'F0 ' or 'F1 ' "
                        "fill-rule prefix (case-sensitive; WPF's mini-language does not "
                        "tolerate lowercase or a missing prefix)"
                    )
        elif source_kind == "bitmap":
            if paths:
                raise ConversionError(f"{_icon_label(icon)}: sourceKind is 'bitmap' but paths is non-empty")
        validated.append(icon)
    return validated


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert MasterGo icon export contract JSON into WPF icon assets.")
    parser.add_argument("--input", required=True, metavar="PATH", help="path to input.json")
    parser.add_argument("--out", required=True, metavar="PATH", help="output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        payload = load_input(Path(arguments.input))
        validate_contract(payload)
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests and verify they pass**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: all eight tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py
git commit -m "feat(mastergo-icon-expoter): add contract validation layer"
```

---

## Task 2: Format decision (`decide`)

**Files:**
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py`
- Test: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py`

**Interfaces:**
- Consumes: the validated `icons: list[dict[str, Any]]` from Task 1's `validate_contract`.
- Produces: `decide_format(icon: dict[str, Any]) -> tuple[str, str]` returning `(format, decision)` where `format` is one of `"path"`, `"drawing-image"`, `"png"` and `decision` is a short human-readable justification string (e.g. `"single fill, no gradient"`). This function is pure — no file I/O.

- [ ] **Step 1: Add failing tests for the decision matrix**

Add to `test_icon_exporter.py` (new test class, same file):

```python
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
```

Add `sys.path.insert(0, str(Path(__file__).parent))` near the top of the test file (after the existing imports, before the test classes) so the in-process `from icon_exporter import ...` used by this class resolves; the black-box tests in Task 1 continue to use `run_cli` via subprocess and are unaffected.

- [ ] **Step 2: Run and verify RED**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: the four new tests fail with `ImportError: cannot import name 'decide_format'`; Task 1's eight tests still pass.

- [ ] **Step 3: Implement `decide_format`**

Insert into `icon_exporter.py`, after `validate_contract`:

```python
def decide_format(icon: dict[str, Any]) -> tuple[str, str]:
    """Map one validated icon to a WPF asset format and a human-readable justification.

    Decision is by paths length alone — svg-to-xaml-path already applied the
    Fill+Stroke+fill-rule+transform merge key, so this function does not
    re-inspect colours to avoid second-guessing an already-tested decision.
    """
    if icon.get("sourceKind") == "bitmap":
        return "png", "bitmap source; no vector geometry available"
    paths = icon.get("paths") or []
    if len(paths) == 1:
        return "path", "single fill, no gradient"
    return "drawing-image", f"{len(paths)} paths after svg-to-xaml-path merge; multi-colour vector"
```

- [ ] **Step 4: Run and verify GREEN**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: all twelve tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py
git commit -m "feat(mastergo-icon-expoter): add format decision layer"
```

---

## Task 3: Name derivation (`name`)

**Files:**
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py`
- Test: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py`

**Interfaces:**
- Consumes: `icon["dslName"]: str`, `icon["userName"]: str | None`.
- Produces: `derive_file_name(dsl_name: str) -> str | None` (returns a `snake_case` name with `icon_`/`bg_`/`logo_` prefix, or `None` on lexical-derivation failure — never raises); `resource_key(file_name: str, suffix: str) -> str` (e.g. `resource_key("icon_search", "Geometry") -> "IconSearchGeometry"`); `assign_names(icons: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` returning `(named, unnamed)` where `named` entries gain a `fileName` key and `unnamed` entries are those needing a CHECKPOINT prompt (both `userName` absent and derivation failed); raises `ConversionError` on a `fileName` collision between two different `dslName`/`userName` values.

- [ ] **Step 1: Add failing tests for the full derivation table**

Add to `test_icon_exporter.py`:

```python
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
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: the twelve new tests fail with `ImportError`; all twelve prior tests (from Tasks 1–2) still pass.

- [ ] **Step 3: Implement `derive_file_name`, `resource_key`, `assign_names`**

Insert into `icon_exporter.py`, after `decide_format`:

```python
_NOISE_WORDS = re.compile(r"\b(Frame|Group|Vector|Rectangle|Ellipse)\b", re.IGNORECASE)
_WORD_SPLIT = re.compile(r"[/_\-\s]+|(?<=[a-z0-9])(?=[A-Z])")
_ASCII_ALNUM = re.compile(r"\A[A-Za-z0-9_]+\Z")
_CATEGORY_KEYWORDS: dict[str, str] = {
    "icon": "icon", "图标": "icon",
    "bg": "bg", "background": "bg", "背景": "bg",
    "logo": "logo",
}


def _snake_words(name: str) -> list[str]:
    stripped = _NOISE_WORDS.sub(" ", name).strip()
    return [word.lower() for word in _WORD_SPLIT.split(stripped) if word]


def derive_file_name(dsl_name: str) -> str | None:
    """Lexically derive a snake_case, category-prefixed file name — never guesses semantics."""
    words = _snake_words(dsl_name)
    if not words:
        return None
    prefix = None
    remaining: list[str] = []
    for word in words:
        category = _CATEGORY_KEYWORDS.get(word)
        if category and prefix is None:
            prefix = category
        else:
            remaining.append(word)
    if prefix is None:
        return None
    if not remaining:
        return None
    candidate = "_".join([prefix, *remaining])
    if not _ASCII_ALNUM.match(candidate):
        return None
    return candidate


def resource_key(file_name: str, suffix: str) -> str:
    """Turn a snake_case file name into a PascalCase WPF resource key with a type suffix."""
    parts = [part for part in file_name.split("_") if part]
    pascal = "".join(part[:1].upper() + part[1:] for part in parts)
    return f"{pascal}{suffix}"


def assign_names(icons: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Assign fileName to each icon; split into named and needs-CHECKPOINT-naming groups."""
    named: list[dict[str, Any]] = []
    unnamed: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for icon in icons:
        user_name = icon.get("userName")
        file_name = user_name if user_name else derive_file_name(str(icon.get("dslName", "")))
        if not file_name:
            unnamed.append(icon)
            continue
        if file_name in seen and seen[file_name] != icon.get("dslName"):
            raise ConversionError(
                f"file name collision: {file_name!r} would be used for both "
                f"{seen[file_name]!r} and {icon.get('dslName')!r}; rename one via userName"
            )
        seen[file_name] = icon.get("dslName", "")
        icon_with_name = dict(icon)
        icon_with_name["fileName"] = file_name
        named.append(icon_with_name)
    return named, unnamed
```

- [ ] **Step 4: Run and verify GREEN**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: all twenty-four tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py
git commit -m "feat(mastergo-icon-expoter): add name derivation layer"
```

---

## Task 4: Rendering (`render`) — Icons.xaml and manifest assembly

**Files:**
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py`
- Test: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py`

**Interfaces:**
- Consumes: named icons from Task 3's `assign_names` (each carrying `fileName`), each icon's `(format, decision)` from Task 2's `decide_format`.
- Produces: `render_icons_xaml(entries: list[dict[str, Any]]) -> str` (full `Icons.xaml` text: one `<Geometry x:Key="...">` per `"path"`-format entry, one `<DrawingImage x:Key="..."><DrawingImage.Drawing><DrawingGroup>...` per `"drawing-image"`-format entry); `render_manifest(entries: list[dict[str, Any]], unnamed: list[dict[str, Any]]) -> dict[str, Any]` (the `icons-manifest.json` structure: a list of records each with `svgShortKey`/`nodeId`/`name`/`fileName`/`resourceKey`/`format`/`decision`/`width`/`height`/`color`/`status`, plus unnamed entries recorded with `status: "needs-manual"` and `reason: "could not derive a file name; needs a userName"`).

- [ ] **Step 1: Add failing tests for XAML and manifest structure**

Add to `test_icon_exporter.py`:

```python
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
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: the seven new tests fail with `ImportError`; all twenty-four prior tests still pass.

- [ ] **Step 3: Implement `render_icons_xaml` and `render_manifest`**

Insert into `icon_exporter.py`, after `assign_names`:

```python
def _escape_xml(value: str) -> str:
    return (
        str(value).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def render_icons_xaml(entries: list[dict[str, Any]]) -> str:
    """Assemble Icons.xaml: one Geometry per single-path entry, one DrawingImage per multi-path entry.

    PNG-format entries have no vector representation and are intentionally
    absent from this resource dictionary — they ship as loose files instead.
    """
    lines = [
        '<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">',
    ]
    for entry in entries:
        file_name = entry["fileName"]
        fmt = entry["format"]
        paths = entry.get("paths") or []
        if fmt == "path":
            key = resource_key(file_name, "Geometry")
            lines.append(f'  <Geometry x:Key="{key}">{_escape_xml(paths[0]["data"])}</Geometry>')
        elif fmt == "drawing-image":
            key = resource_key(file_name, "Image")
            lines.append(f'  <DrawingImage x:Key="{key}">')
            lines.append('    <DrawingImage.Drawing>')
            lines.append('      <DrawingGroup>')
            for path_entry in paths:
                fill = _escape_xml(path_entry.get("fill") or "#000000")
                data = _escape_xml(path_entry["data"])
                lines.append(f'        <GeometryDrawing Brush="{fill}" Geometry="{data}" />')
            lines.append('      </DrawingGroup>')
            lines.append('    </DrawingImage.Drawing>')
            lines.append('  </DrawingImage>')
        # "png" entries carry no vector representation and are skipped here by design.
    lines.append("</ResourceDictionary>")
    return "\n".join(lines) + "\n"


def render_manifest(entries: list[dict[str, Any]], unnamed: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the icons-manifest.json structure from named and needs-naming entries."""
    records: list[dict[str, Any]] = []
    for entry in entries:
        fmt = entry["format"]
        suffix = {"path": "Geometry", "drawing-image": "Image", "png": "Png"}[fmt]
        colour = None
        paths = entry.get("paths") or []
        if len(paths) == 1:
            colour = paths[0].get("fill")
        records.append({
            "svgShortKey": entry.get("svgShortKey"),
            "nodeId": entry.get("nodeId"),
            "name": entry.get("dslName"),
            "fileName": entry["fileName"],
            "resourceKey": resource_key(entry["fileName"], suffix) if fmt != "png" else None,
            "format": fmt,
            "decision": entry.get("decision", ""),
            "width": entry.get("width"),
            "height": entry.get("height"),
            "color": colour,
            "status": "exported",
            "reason": None,
        })
    for icon in unnamed:
        records.append({
            "svgShortKey": icon.get("svgShortKey"),
            "nodeId": icon.get("nodeId"),
            "name": icon.get("dslName"),
            "fileName": None,
            "resourceKey": None,
            "format": "unresolved",
            "decision": None,
            "width": icon.get("width"),
            "height": icon.get("height"),
            "color": None,
            "status": "needs-manual",
            "reason": "could not derive a file name; needs a userName",
        })
    return {"icons": records}
```

- [ ] **Step 4: Run and verify GREEN**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: all thirty-one tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py
git commit -m "feat(mastergo-icon-expoter): add Icons.xaml and manifest rendering"
```

---

## Task 5: Self-check (`selfcheck`) — the pre-write consistency gate

**Files:**
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py`
- Test: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py`

**Interfaces:**
- Consumes: `icons_xaml: str` (from Task 4's `render_icons_xaml`), `manifest: dict[str, Any]` (from Task 4's `render_manifest`), `png_files: dict[str, bytes]` (planned PNG outputs, filename → bytes; empty in tests that don't cover bitmaps), `existing_xaml: str | None` (contents of an already-existing `Icons.xaml` when `mergeMode == "merge"`, else `None`).
- Produces: `self_check(icons_xaml: str, manifest: dict[str, Any], png_files: dict[str, bytes], existing_xaml: str | None) -> list[str]` returning a list of violation strings (empty list means pass — this function never raises; the caller in Task 6 turns a non-empty list into a `ConversionError`).

- [ ] **Step 1: Add failing tests, one per design-doc rule**

Add to `test_icon_exporter.py`:

```python
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
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: the ten new tests fail with `ImportError`; all thirty-one prior tests still pass.

- [ ] **Step 3: Implement `self_check`**

Insert into `icon_exporter.py`, after `render_manifest`:

```python
_X_KEY = re.compile(r'x:Key="([^"]+)"')
_GEOMETRY_DATA = re.compile(r'<Geometry x:Key="([^"]+)">([^<]*)</Geometry>')
_GEOMETRY_DRAWING_DATA = re.compile(r'<GeometryDrawing[^>]* Geometry="([^"]*)"')


def self_check(
    icons_xaml: str,
    manifest: dict[str, Any],
    png_files: dict[str, bytes],
    existing_xaml: str | None,
) -> list[str]:
    """Check the about-to-be-written content for internal consistency.

    Every rule here maps to a named silent trap in the design doc; this
    function inspects in-memory content only and never touches disk.
    """
    violations: list[str] = []

    # Rule 1: every Geometry/GeometryDrawing Data must carry a literal F0/F1 prefix.
    for key, data in _GEOMETRY_DATA.findall(icons_xaml):
        if not FILL_RULE_PREFIX.match(data):
            violations.append(f"{key}: Data missing F0/F1 prefix")
    for data in _GEOMETRY_DRAWING_DATA.findall(icons_xaml):
        if not FILL_RULE_PREFIX.match(data):
            violations.append(f"GeometryDrawing Data missing F0/F1 prefix: {data[:40]!r}")

    # Rule 3: x:Key must be unique within the new file, and against an existing
    # file when mergeMode is "merge" (existing_xaml is only passed in that case).
    new_keys = _X_KEY.findall(icons_xaml)
    seen: set[str] = set()
    for key in new_keys:
        if key in seen:
            violations.append(f'duplicate x:Key "{key}" within the generated Icons.xaml')
        seen.add(key)
    if existing_xaml is not None:
        existing_keys = set(_X_KEY.findall(existing_xaml))
        for key in seen:
            if key in existing_keys:
                violations.append(f'duplicate x:Key "{key}" already present in the existing Icons.xaml')

    # Rule 4: every manifest resourceKey must correspond to a key actually in the XAML.
    xaml_keys = set(new_keys)
    for record in manifest.get("icons", []):
        resource_key_value = record.get("resourceKey")
        if resource_key_value and resource_key_value not in xaml_keys:
            violations.append(f"manifest references resourceKey {resource_key_value!r} not found in Icons.xaml")

    # Rule 5: needs-manual records must always carry a non-empty reason.
    for record in manifest.get("icons", []):
        if record.get("status") == "needs-manual" and not record.get("reason"):
            violations.append(f"{record.get('fileName') or record.get('nodeId')}: needs-manual record has no reason")

    # Rule 6: planned PNGs must have a determinate, positive width and height.
    for record in manifest.get("icons", []):
        if record.get("format") in {"png", "ico-fallback-png"} and record.get("fileName"):
            width, height = record.get("width"), record.get("height")
            if not isinstance(width, (int, float)) or width <= 0 or not isinstance(height, (int, float)) or height <= 0:
                violations.append(f"{record.get('fileName')}: width/height must be positive, got {width}x{height}")

    # Rule 7: an .ico that was downgraded to PNG fallback must never be reported as exported.
    for record in manifest.get("icons", []):
        if record.get("format") == "ico-fallback-png" and record.get("status") == "exported":
            violations.append(f"{record.get('fileName')}: ico fallback to PNG must be status=needs-manual, not exported")

    return violations
```

- [ ] **Step 4: Run and verify GREEN**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: all forty-one tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py
git commit -m "feat(mastergo-icon-expoter): add pre-write self-check gate"
```

---

## Task 6: Atomic write, optional `.ico` synthesis, and CLI wiring

**Files:**
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py`
- Test: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py`

**Interfaces:**
- Consumes: all prior layers (`load_input`, `validate_contract`, `decide_format`, `assign_names`, `render_icons_xaml`, `render_manifest`, `self_check`).
- Produces: `synthesize_ico(png_frames: dict[int, bytes]) -> bytes | None` (returns combined `.ico` bytes if `PIL` is importable, else `None` — never raises `ImportError` to the caller); `atomic_write_outputs(out_dir: Path, files: dict[str, bytes | str]) -> None` (stage-then-replace, matching `dsl_to_xaml.py`'s `atomic_write_outputs`; text values are UTF-8 encoded, bytes values are written as-is); `main(argv: list[str] | None = None) -> int` wired end-to-end.

- [ ] **Step 1: Add failing tests for the ico fallback and full pipeline**

Add to `test_icon_exporter.py`:

```python
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
            result = run_cli("--input", str(input_path), "--out", str(out_dir), "--source-root", directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((out_dir / "Images" / "avatar_default.png").exists())
```

Note: the last test passes `directory` (a `Path`) positionally to `run_cli`, which expects `str` — fix by wrapping it as `str(directory)` before running. Correct the call to:

```python
            result = run_cli("--input", str(input_path), "--out", str(out_dir), "--source-root", str(directory))
```

- [ ] **Step 2: Run and verify RED**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: the four new tests fail — `IcoSynthesisTests` with `AttributeError: module 'icon_exporter' has no attribute 'synthesize_ico'`, `FullPipelineTests` with non-zero/unexpected exit codes since `main` does not yet wire the pipeline together (bitmap copy, `--source-root` flag, and full assembly do not exist yet). All forty-one prior tests still pass.

- [ ] **Step 3: Implement `synthesize_ico`, `atomic_write_outputs`, bitmap copy, and wire `main`**

Insert into `icon_exporter.py`, after `self_check`, and replace the existing `build_parser`/`main`:

```python
import os
import shutil
import tempfile


def synthesize_ico(png_frames: dict[int, bytes]) -> bytes | None:
    """Combine same-icon PNG frames into one .ico if Pillow is available, else None.

    Import is local and lazy: a user who never asks for .ico output must not
    need Pillow installed for the rest of the CLI to work.
    """
    try:
        import PIL  # noqa: F401
        from PIL import Image
        import io
    except ImportError:
        return None
    images = []
    for size in sorted(png_frames):
        images.append(Image.open(io.BytesIO(png_frames[size])))
    buffer = io.BytesIO()
    images[0].save(buffer, format="ICO", sizes=[(size, size) for size in sorted(png_frames)])
    return buffer.getvalue()


def atomic_write_outputs(out_dir: Path, files: dict[str, bytes | str]) -> None:
    """Write a fully rendered output set only after all validation succeeds."""
    parent = out_dir.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.", dir=parent))
    try:
        for name, content in files.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content, encoding="utf-8")
        if not out_dir.exists():
            os.replace(stage, out_dir)
            return
        for name in files:
            destination = out_dir / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage / name, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert MasterGo icon export contract JSON into WPF icon assets.")
    parser.add_argument("--input", required=True, metavar="PATH", help="path to input.json")
    parser.add_argument("--out", required=True, metavar="PATH", help="output directory")
    parser.add_argument("--source-root", metavar="PATH", help="base directory bitmapPath entries are relative to")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        payload = load_input(Path(arguments.input))
        icons = validate_contract(payload)
        meta = payload.get("meta") or {}
        merge_mode = meta.get("mergeMode", "separate")
        out_dir = Path(arguments.out)

        decided = []
        for icon in icons:
            fmt, decision = decide_format(icon)
            entry = dict(icon)
            entry["format"] = fmt
            entry["decision"] = decision
            decided.append(entry)

        named, unnamed = assign_names(decided)

        icons_xaml = render_icons_xaml(named)
        manifest = render_manifest(named, unnamed)

        png_files: dict[str, bytes] = {}
        source_root = Path(arguments.source_root) if arguments.source_root else None
        for entry in named:
            if entry["format"] != "png":
                continue
            bitmap_path = entry.get("bitmapPath")
            if not bitmap_path or source_root is None:
                continue
            source_file = source_root / bitmap_path
            if not source_file.is_file():
                raise ConversionError(f"{entry['fileName']}: bitmapPath {bitmap_path!r} does not exist under --source-root")
            png_files[f"Images/{entry['fileName']}.png"] = source_file.read_bytes()

        existing_xaml_path = out_dir / "Icons.xaml"
        existing_xaml = (
            existing_xaml_path.read_text(encoding="utf-8")
            if merge_mode == "merge" and existing_xaml_path.is_file()
            else None
        )

        violations = self_check(icons_xaml, manifest, png_files, existing_xaml)
        if violations:
            raise ConversionError("self-check failed:\n  - " + "\n  - ".join(violations))

        files: dict[str, bytes | str] = {
            "Icons.xaml": icons_xaml,
            "icons-manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        }
        files.update(png_files)
        atomic_write_outputs(out_dir, files)
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Remove the old `build_parser`/`main` definitions from Task 1 (this replaces them) and move the `import argparse`, `import json`, `import re`, `import sys` block at the top of the file to also include `os`, `shutil`, `tempfile` instead of importing them inline — consolidate all imports at the top of `icon_exporter.py` in one block, matching `dsl_to_xaml.py`'s layout.

- [ ] **Step 4: Run and verify GREEN**

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py -v
```

Expected: all forty-five tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/test_icon_exporter.py
git commit -m "feat(mastergo-icon-expoter): wire full pipeline with atomic write and optional ico synthesis"
```

---

## Task 7: Skill documentation — SKILL.md, CHANGELOG.md, README.md

**Files:**
- Create: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/SKILL.md`
- Create: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/CHANGELOG.md`
- Create: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/README.md`
- Verify (no changes): `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/references/wpf-xaml-icon-sepc.md`

**Interfaces:**
- Consumes: `icon_exporter.py`'s CLI contract (`--input`, `--out`, `--source-root`) from Task 6; the design doc's CHECKPOINT structure and delivery-discipline rules.
- Produces: the discoverable Skill entry point — no code interfaces, this task's deliverable is documentation content that an agent follows verbatim.

This is a documentation-only task; there is no test-first cycle. Steps below produce the finished file content directly, then a validation step checks required substrings are present (matching how Task 4 of the `svg-to-xaml-path` plan validates its README update).

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: mastergo-icon-expoter
description: 当用户要求从 MasterGo 设计稿导出图标、背景等视觉资产用于 WPF XAML 项目时使用此 Skill；产出 Geometry/DrawingImage 资源字典、位图与决策清单，不生成页面代码。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: generator
compatibility: Python 3 标准库；可选 Pillow（用于 .ico 合成，未安装时降级为多张 png）；需 mastergo-magic-mcp（本仓库 plugins/optimus-mcp-servers/.mcp.json 内置）与 MASTERGO_TOKEN；委派 optimus-frontend-plugin:svg-to-xaml-path 完成 SVG→Path.Data 转换。
allowed-tools: Read Write Bash PowerShell Skill mastergo-magic-mcp
---

# MasterGo 设计稿转 WPF 图标资产

从 MasterGo 设计稿导出图标、背景等视觉资产，产出 WPF 可直接引用的 `Icons.xaml`（`Geometry`/`DrawingImage` 资源）、`Images/*.png` 位图与 `icons-manifest.json` 决策清单。**不生成页面代码**——用户在自己的 XAML 里引用 `{StaticResource IconSearchGeometry}`。

格式决策、命名约定、静默陷阱清单见 [`references/wpf-xaml-icon-sepc.md`](references/wpf-xaml-icon-sepc.md)；本文件只讲编排步骤。

## Step 0：前置检查

以下任一条件不满足，停止且不要读取设计：`MASTERGO_TOKEN` 已配置；文件属于 MasterGo Team 版或以上且不是草稿箱；分享链接可解析出 `fileId`/`layerId`。

## Step 1：拉取目录，扫描图标节点

调用不带 `sectionIndex` 的 `mcp__getDesignSections`。遍历返回的节点树，收集所有 `PATH`（矢量图标候选）与 `IMAGE`（位图候选）节点。区块数超过 8 个时停止，请用户指定范围。

未识别类型的节点（如 `INSTANCE` 图标组件）列入下一步 CHECKPOINT 的"未识别节点"清单，不猜测其类型，不产出。

## Step 2：🔴 CHECKPOINT

一次性展示，等待用户确认或修正后才能进入 Step 3：

```
1. 待处理范围：N 个图标节点（矢量 M 个 / 位图 K 个 / 未识别 J 个）
2. 待人工命名：<列出无法自动推导文件名的节点，格式见下方"命名规则">
3. 输出目录：<--out 路径>（若已存在 Icons.xaml，请选择：merge / overwrite / separate）
4. 是否需要 .ico：否 / 是（涉及哪些图标）
```

**命名规则**（详见 `references/wpf-xaml-icon-sepc.md` 第八节）：脚本会尝试从 DSL 图层名机械推导 `snake_case` 文件名（如 `SearchIcon` → `icon_search`），失败时（非 ASCII、无法判定 `icon_`/`bg_`/`logo_` 分类等）必须由用户补充完整文件名，不得猜测语义分类。

## Step 3：逐图标委派转换，组装 `input.json`

对每个矢量候选节点：

1. 调用 `mcp__extractSvg(svgShortKey=...)` 取得 SVG 标记。
2. 委派 `optimus-frontend-plugin:svg-to-xaml-path`（`--format data`），获得 `Data` 字符串（含 `F0`/`F1` 前缀）与其 stderr 告警。**多路径异色**的情形会返回多个 `Path`，按顺序填入同一个 icon 条目的 `paths` 数组，不需要为此额外询问用户——格式决策已经完全由 `paths` 数组长度决定。

对每个位图候选节点：调用 `mcp__getD2c` 落盘，记录相对路径为 `bitmapPath`。

🔴 **红线：** `svg-to-xaml-path` 返回的 `Data` 字符串必须逐字写入 `input.json`，包括 `F0`/`F1` 前缀，不得删改、补全或重排。这条由 `icon_exporter.py` 的 `validate_contract` 强制校验——缺前缀会导致 exit 2。

单个图标的 SVG 取值失败或 `svg-to-xaml-path` 报错（如 `currentColor`、渐变 URL）不中断整批：将该图标的 `sourceKind` 标记为待定，在 `input.json` 中省略该条目，并在后续报告中列为 `unresolved`，附上兄弟 Skill 的错误原文。

组装完整的 `input.json`（结构见 `references/wpf-xaml-icon-sepc.md` 第十一节），写入 `.mastergo-icons/input.json`。

## Step 4：运行转换器

`$SkillDir` 必须是本 Skill 加载时提供的绝对 base directory。

```powershell
$SkillDir = "<本 skill 的 base directory>"
python "$SkillDir\scripts\icon_exporter.py" --input .mastergo-icons\input.json --out <用户确认的输出目录> --source-root .mastergo-icons
```

成功时 exit `0`，stdout 为空；契约违规或自检失败时 exit `2`，stdout 为空，stderr 为 `error: ...`（自检失败会在同一条消息里列出全部违规项）。硬失败时不会创建或修改输出目录中的任何文件。

## Step 5：交付纪律

- 逐条转达 `icons-manifest.json` 中 `status: needs-manual` 的记录及其 `reason`，不得声称已导出。
- **矢量图标在使用处必须显式 `Stretch="Uniform"`。** 本 Skill 只产出资源字典，不产出消费该资源的 `<Path>`/`<Image>` 元素，因此这条规则无法由脚本自动校验——必须在每次交付时向用户逐字提醒：不写 `Stretch` 时 WPF 默认 `None`，图标只会显示左上角一小块，且不报任何错。
- 若涉及 `.ico` 且 Pillow 未安装，如实告知已降级为多张 PNG（`needs-manual`），需用户自行用外部工具合成。
- 不检查用户项目中已有的 XAML 是否正确使用了这些资源；不做视觉还原度校验。均为本 Skill 明确排除的范围。

## 本地测试

```powershell
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts -p "test_*.py"
```
```

- [ ] **Step 2: Write `CHANGELOG.md`**

```markdown
# Changelog

## [1.0.0] - 2026-08-04

### Added
- 新增 `mastergo-icon-expoter` Skill：从 MasterGo 设计稿导出图标、背景等视觉资产，产出 WPF `Icons.xaml`（`Geometry`/`DrawingImage` 资源字典）、`Images/*.png` 位图与 `icons-manifest.json` 决策清单。
- 新增 `scripts/icon_exporter.py`：契约校验、格式决策、命名推导、XAML/清单渲染、写盘前自检五层确定性实现，零 MCP、零网络依赖。
- 委派 `svg-to-xaml-path` 完成 SVG→`Path.Data` 转换，复用其合并键决策与 74 条测试覆盖的静默陷阱防护。
- 可选 Pillow 依赖用于 `.ico` 合成；未安装时降级为多张 PNG 并在清单中如实标记 `needs-manual`。
```

- [ ] **Step 3: Write `README.md`**

```markdown
# mastergo-icon-expoter

> 版本：1.0.0 | 分类：generator

从 MasterGo 设计稿导出图标、背景等视觉资产，产出 WPF 可直接引用的资源字典、位图和决策清单。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│  tool        │  svg-to-xaml-path（被委派，完成 SVG→Path.Data）
├─────────────┤
│  quality     │
├─────────────┤
│★ generator   │  mastergo-icon-expoter（本 skill）
├─────────────┤
│  workflow    │  mastergo-to-wpf（整页转换，独立流程，不消费本 skill 产物）
└─────────────┘
```

## 触发词

从 MasterGo 设计稿导出图标、导出 WPF 图标资产、导出图标资源字典、生成 Icons.xaml。

## 业务逻辑流程图

```
Step 0  前置检查（token / 文件版本 / 链接可解析）
   ↓
Step 1  拉取目录，扫描 PATH/IMAGE 节点
   ↓
Step 2  🔴 CHECKPOINT：范围 + 待命名项 + 输出目录 + 是否需要 ico
   ↓
Step 3  逐图标委派 svg-to-xaml-path，组装 input.json
   ↓
Step 4  运行 icon_exporter.py（契约校验 → 格式决策 → 命名 → 渲染 → 自检 → 原子写入）
   ↓
Step 5  交付纪律（needs-manual 转达、Stretch 提醒、ico 降级如实说明）
```

## 产出物数据流

MasterGo 设计稿链接 → 本 skill → `Icons.xaml` + `Images/*.png` + `icons-manifest.json` → 人工接手（用户在自己的 XAML 里引用 `{StaticResource IconXxxGeometry}`）。

## Skill 依赖关系图

```
用户 ──触发──▶ mastergo-icon-expoter ──委派──▶ svg-to-xaml-path
                       │
                       └──调用──▶ mastergo-magic-mcp（getDesignSections / extractSvg / getD2c）
```

不被其他 skill 调度；不消费也不产出 `mastergo-to-wpf` 的 `icons.json`（两者是不同的产物形态，互不依赖）。
```

- [ ] **Step 4: Verify required content is present**

```powershell
python -c "from pathlib import Path; text = Path('plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/SKILL.md').read_text(encoding='utf-8'); assert 'name: mastergo-icon-expoter' in text; assert 'svg-to-xaml-path' in text; assert 'Stretch=\"Uniform\"' in text; print('SKILL.md valid')"
python -c "from pathlib import Path; text = Path('plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/CHANGELOG.md').read_text(encoding='utf-8'); assert '[1.0.0]' in text; print('CHANGELOG.md valid')"
python -c "from pathlib import Path; text = Path('plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/README.md').read_text(encoding='utf-8'); assert '版本：1.0.0' in text; assert '分类：generator' in text; print('README.md valid')"
```

Expected: all three print their `valid` line.

- [ ] **Step 5: Commit**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/SKILL.md plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/CHANGELOG.md plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/README.md
git commit -m "docs(mastergo-icon-expoter): add SKILL.md, CHANGELOG.md, README.md"
```

---

## Task 8: Publish the new capability in repository metadata and docs

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md` (repo root)

**Interfaces:**
- Consumes: nothing from prior tasks' code; only the Skill's existence and slash-command name (`optimus-frontend-plugin:mastergo-icon-expoter`).
- Produces: nothing consumed by later tasks; this is a metadata leaf.

- [ ] **Step 1: Bump the marketplace version and expand the frontend description**

Read the current `"version"` field of `.claude-plugin/marketplace.json` first (do not assume it is still `8.5.3` — the design doc's estimate may be stale by the time this task runs; the design doc itself is frozen at the time it was written, so re-read the file's actual current value). Increment its **minor** segment by exactly 1 (patch reset to 0), per the Global Constraints rule. Expand only the existing `optimus-frontend-plugin` plugin's `description` field to mention icon/background asset export for WPF XAML alongside its existing capabilities. Do not alter plugin names, sources, owners, repository URL, or any other plugin's entry.

- [ ] **Step 2: Add the new frontend feature to the repository README**

Update the frontend plugin's capability row/section so it includes exporting MasterGo icon/background assets as WPF `Icons.xaml` resources. Add the following adjacent to the existing MasterGo/WPF command examples:

```bash
# 从 MasterGo 设计稿导出图标/背景资产为 WPF Icons.xaml
/optimus-frontend-plugin:mastergo-icon-expoter
```

- [ ] **Step 3: Validate JSON and documentation references**

```powershell
python -c "import json; data=json.load(open('.claude-plugin/marketplace.json', encoding='utf-8')); parts=[int(p) for p in data['version'].split('.')]; assert parts[1] >= 6, data['version']; assert any(p['name'] == 'optimus-frontend-plugin' for p in data['plugins']); print('marketplace valid')"
python -c "from pathlib import Path; text=Path('README.md').read_text(encoding='utf-8'); assert '/optimus-frontend-plugin:mastergo-icon-expoter' in text; print('README command documented')"
```

Expected: `marketplace valid` and `README command documented`.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json README.md
git commit -m "chore(marketplace): publish mastergo-icon-expoter skill"
```

---

## Task 9: Full repository-level validation

**Files:**
- Verify: `plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/**`
- Verify: `.claude-plugin/marketplace.json`
- Verify: `README.md`

- [ ] **Step 1: Run the full test suite for the new skill**

```powershell
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts -p "test_*.py" -v
```

Expected: all tests pass (forty-five from Tasks 1–6; no tests were added in Tasks 7–8).

- [ ] **Step 2: Run an end-to-end manual smoke test with a realistic multi-icon input**

Create a temporary `input.json` covering one single-colour icon, one multi-colour icon (2 paths), and one icon needing manual naming, then run:

```powershell
python plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py --input <path-to-temp-input.json> --out <temp-out-dir>
```

Expected: exit code `0`; `Icons.xaml` contains both a `<Geometry>` and a `<DrawingImage><DrawingGroup>` entry; `icons-manifest.json` marks the unnamed icon `needs-manual` with a non-empty `reason`.

- [ ] **Step 3: Verify a deliberately broken input is rejected without touching disk**

```powershell
python plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts/icon_exporter.py --input <path-to-input-with-missing-F1-prefix.json> --out <temp-out-dir-2>
```

Expected: exit code `2`; stdout empty; stderr starts with `error: `; `<temp-out-dir-2>` does not exist afterward.

- [ ] **Step 4: Test-load the repository plugin locally if the Claude CLI is installed**

```powershell
claude --plugin-dir "F:\optimus-plugins-official"
```

Expected: the CLI accepts the plugin directory and exposes `mastergo-icon-expoter`; if the executable is unavailable or requires interactive sign-in, record that limitation and retain the static and script validation evidence from Steps 1–3.

- [ ] **Step 5: Inspect the final diff against the approved scope**

```powershell
git diff --check
git diff -- .claude-plugin/marketplace.json README.md docs/superpowers/specs/2026-08-04-mastergo-icon-exporter-design.md docs/superpowers/plans/2026-08-04-mastergo-icon-exporter.md plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter
```

Expected: no whitespace errors; changed files exactly correspond to the design, plan, Skill (`SKILL.md`, `CHANGELOG.md`, `README.md`, `scripts/icon_exporter.py`, `scripts/test_icon_exporter.py`, unchanged `references/wpf-xaml-icon-sepc.md`), marketplace metadata, and repository README. Do not create a commit for this task unless the user explicitly requests one — this task only verifies prior commits.

---

## Self-Review

**Spec coverage:**
- Architecture (thick script / thin orchestration, four-layer boundary table) → Task 6's `main()` wiring plus Tasks 1–5's layer implementations; the "禁止 agent 做"/"禁止脚本做" boundary is enforced by the CLI having no MCP/network imports anywhere and by SKILL.md's explicit red line in Task 7.
- `input.json` contract (all fields, `paths` length as decision basis, `userName`/`dslName` split, `warnings` passthrough, `sourceKind`, `meta.mergeMode`) → Task 1 (`validate_contract`) covers required fields and the `F0`/`F1` check; Task 2 (`decide_format`) implements the length-based rule; Task 6's `main()` reads `meta.mergeMode` and threads it into `self_check`.
- Contract violations → hard fail, zero output → Task 1's tests assert `out_dir` does not exist after a validation failure; Task 6's `test_self_check_failure_leaves_output_directory_untouched` extends this to the self-check path specifically.
- Five-layer script pipeline (`validate` → `decide` → `name` → `render` → `selfcheck`) → Tasks 1–5 implement each layer with its own failing-test-first cycle; Task 6 composes them in `main()`.
- ico Pillow-optional fallback → Task 6's `synthesize_ico` (lazy `import PIL`, returns `None` on failure) and its test; Task 5's self-check rule 7 (`test_ico_fallback_reported_as_exported_is_caught`) guards against mislabeling the fallback.
- Naming derivation table (all seven examples from the design doc) → Task 3's `NameDerivationTests` reproduces every row verbatim.
- Seven self-check rules → Task 5's `SelfCheckTests` has one test per rule, matching the design doc's table order.
- Error handling / edge scenarios table (unresolved SVG, `currentColor` errors, existing `Icons.xaml`, single-icon-failure-does-not-abort-batch) → Task 6's `FullPipelineTests` covers the multi-icon batch continuing past one needs-manual icon; the CHECKPOINT and per-icon `unresolved` handling is agent-side and documented in Task 7's SKILL.md Step 3, since it depends on live MCP/Skill delegation that cannot be unit-tested (consistent with the design doc's explicit "MCP calls are not unit-tested" decision).
- Testing strategy (unittest, black-box CLI, layer-by-layer, regression cases for prefix case-sensitivity, ico downgrade, no-partial-write) → Tasks 1–6 each include the corresponding test; the three "key regression cases" from the design doc's Testing Strategy section appear as `test_lowercase_fill_rule_prefix_is_fatal` (Task 1), `test_synthesize_ico_returns_none_when_pillow_unavailable` + `test_ico_fallback_reported_as_exported_is_caught` (Tasks 5–6), and `test_self_check_failure_leaves_output_directory_untouched` (Task 6).
- File structure, SKILL.md frontmatter, SKILL.md body outline, marketplace/README publication → Tasks 7–8 verbatim.

**Placeholder scan:** No `TODO`/`TBD` remain. Every code step shows the actual function body, not a description of one. The one deliberately-documentation-only task (Task 7) is explicitly marked as such rather than silently omitting a test cycle.

**Type/name consistency:** `ConversionError`, `load_input`, `validate_contract`, `decide_format`, `derive_file_name`, `resource_key`, `assign_names`, `render_icons_xaml`, `render_manifest`, `self_check`, `synthesize_ico`, `atomic_write_outputs`, and `main` are each defined exactly once (in the task that introduces them) and referenced by the same name and signature in every later task that consumes them. The `--source-root` CLI flag introduced in Task 6 is the only argument not present in the design doc's CLI sketch — added because the design doc's `bitmapPath` field needs a base directory to resolve against, and leaving that ambiguous would have made Task 6 a placeholder.

**Deviation from the design doc, recorded here rather than silently fixed:** the design doc's self-check rule 2 ("every vector icon at its point of use must have `Stretch=\"Uniform\"`") has no in-scope target once the product boundary (Q1 of the brainstorming session) confirmed this Skill never emits `<Path>`/`<Image>` consumer elements — only the resource dictionary. Task 5 implements rules 1, 3, 4, 5, 6, 7 as automatic checks; rule 2 is instead promoted to a mandatory verbal reminder in Task 7's SKILL.md Step 5, called out explicitly rather than dropped.

