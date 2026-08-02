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


if __name__ == "__main__":
    unittest.main()
