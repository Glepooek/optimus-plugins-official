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
