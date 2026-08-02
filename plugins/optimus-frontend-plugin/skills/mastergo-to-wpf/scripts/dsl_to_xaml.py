"""Convert MasterGo section DSL into a WPF XAML page scaffold."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class ConversionError(Exception):
    """An input or conversion error that should be shown to the user."""


def read_json(path: Path) -> object:
    """Read one JSON file, naming it in any error so the user can find it."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError) as error:
        raise ConversionError(f"could not read {path.name}: {error}") from error
    except json.JSONDecodeError as error:
        raise ConversionError(f"{path.name} is not valid JSON: {error}") from error


def load_sections(directory: Path) -> tuple[dict, list[dict]]:
    """Load the section directory listing and every section DSL beside it."""
    if not directory.is_dir():
        raise ConversionError(f"input directory not found: {directory}")
    listing_path = directory / "sections-list.json"
    if not listing_path.is_file():
        raise ConversionError(
            f"sections-list.json not found in {directory}; run mcp__getDesignSections "
            "without a sectionIndex first and save its response there"
        )
    listing = read_json(listing_path)
    if not isinstance(listing, dict):
        raise ConversionError("sections-list.json must contain a JSON object")

    sections: list[dict] = []
    for path in sorted(directory.glob("section-*.json"), key=lambda p: p.name):
        section = read_json(path)
        if not isinstance(section, dict):
            raise ConversionError(f"{path.name} must contain a JSON object")
        sections.append(section)
    return listing, sections


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Convert MasterGo section DSL into a WPF XAML page scaffold."
    )
    parser.add_argument("--input", required=True, metavar="PATH", help="directory of DSL JSON")
    parser.add_argument("--out", required=True, metavar="PATH", help="output directory")
    parser.add_argument("--page-name", default="GeneratedPage", help="generated page file name")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the DSL conversion CLI."""
    arguments = build_parser().parse_args(argv)
    try:
        load_sections(Path(arguments.input))
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
