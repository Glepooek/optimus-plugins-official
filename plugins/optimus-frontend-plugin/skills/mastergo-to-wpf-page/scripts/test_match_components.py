"""Contract tests for match_components.py (offline, unittest only)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
SCRIPT = Path(__file__).parent / "match_components.py"
VALID_INDEX = {"version": 1, "components": [{"key": "ActionButton.Primary", "kind": "style", "source": ["ActionButton.Primary"], "occurrences": 2, "status": "new", "resourceKey": "ActionButton.Primary"}]}


def run_cli(test_case: unittest.TestCase, asset: str, index_payload: dict) -> tuple[subprocess.CompletedProcess, Path]:
    tmp = Path(tempfile.mkdtemp())
    test_case.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
    src, out = tmp / "input", tmp / "out"
    src.mkdir()
    payload = json.loads((ASSETS / asset).read_text(encoding="utf-8"))
    (src / "sections-list.json").write_text(json.dumps({"rootMetadata": payload["list"].get("rootMetadata", {})}, ensure_ascii=False), encoding="utf-8")
    for i, section in enumerate(payload["sections"]):
        (src / f"section-{i}.json").write_text(json.dumps(section, ensure_ascii=False), encoding="utf-8")
    index_path = tmp / "components-index.json"
    index_path.write_text(json.dumps(index_payload, ensure_ascii=False), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "--input", str(src), "--index", str(index_path), "--out", str(out)], capture_output=True, text=True), out


class MatchCliTestCase(unittest.TestCase):
    def test_matched_and_missing_reported(self):
        proc, out = run_cli(self, "matched-and-missing.json", VALID_INDEX)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads((out / "component-match-report.json").read_text(encoding="utf-8"))
        self.assertEqual(len(report["matches"]), 1)
        self.assertEqual(report["matches"][0]["resourceKey"], "ActionButton.Primary")
        self.assertEqual(len(report["missing"]), 1)
        self.assertEqual(report["missing"][0]["nodeName"], "MysteryWidget")

    def test_invalid_index_hard_stops(self):
        proc, _ = run_cli(self, "matched-and-missing.json", {"version": 1, "components": "bad"})
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(proc.stderr.startswith("error: "), proc.stderr)


if __name__ == "__main__":
    unittest.main()
