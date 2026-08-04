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
