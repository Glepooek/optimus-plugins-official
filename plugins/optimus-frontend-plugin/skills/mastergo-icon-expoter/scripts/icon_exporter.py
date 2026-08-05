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
