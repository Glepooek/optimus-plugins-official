"""Merge SVG path data into WPF XAML Path elements."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable


class ConversionError(Exception):
    """An input or SVG conversion error that should be shown to the user."""


@dataclass(frozen=True)
class SvgPath:
    """A usable SVG path and its effective inherited paint attributes."""

    data: str
    fill: str | None
    stroke: str | None


def local_name(tag: object) -> str:
    """Return an XML element's local name, including for namespaced tags."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def effective_paint(value: str | None) -> str | None:
    """Translate SVG's `none` paint value to the absence of a WPF property."""
    if value is None:
        return None
    value = value.strip()
    return None if value.lower() == "none" else value


def collect_paths(root: ElementTree.Element) -> tuple[list[SvgPath], list[str]]:
    """Collect usable paths in document order and conversion warnings."""
    paths: list[SvgPath] = []
    warnings: list[str] = []
    saw_style_or_class = False
    stack = [(root, "#000000", "none", [])]

    while stack:
        element, inherited_fill, inherited_stroke, transform_sources = stack.pop()

        if "style" in element.attrib or "class" in element.attrib:
            saw_style_or_class = True

        fill = element.attrib.get("fill", inherited_fill)
        stroke = element.attrib.get("stroke", inherited_stroke)
        element_name = local_name(element.tag)
        transform = element.attrib.get("transform", "").strip()
        if transform:
            source = (
                f"path transform {transform!r}"
                if element_name == "path"
                else f"ancestor <{element_name}> transform {transform!r}"
            )
            transform_sources = [*transform_sources, source]

        if element_name == "path":
            data = element.attrib.get("d", "").strip()
            if data:
                path_index = len(paths) + 1
                if transform_sources:
                    raise ConversionError(
                        f"SVG transform attributes are not supported for path {path_index}: "
                        + "; ".join(transform_sources)
                    )
                paths.append(
                    SvgPath(
                        data=data,
                        fill=effective_paint(fill),
                        stroke=effective_paint(stroke),
                    )
                )

        for child in reversed(list(element)):
            stack.append((child, fill, stroke, transform_sources))

    if saw_style_or_class:
        warnings.append(
            "warning: style or class attributes were encountered; they were not converted."
        )
    if not paths:
        raise ConversionError("No <path> elements with nonempty d attributes found")

    return paths, warnings


def attribute(name: str, value: str) -> str:
    """Render an XML attribute using double quotes and XML escaping."""
    return f'{name}="{escape(value, quote=True)}"'


def render_path(path: SvgPath) -> str:
    """Render one WPF Path element with the required attribute order."""
    attributes: list[str] = []
    if path.fill is not None:
        attributes.append(attribute("Fill", path.fill))
    if path.stroke is not None:
        attributes.append(attribute("Stroke", path.stroke))
    attributes.append(attribute("Data", path.data))
    return f"<Path {' '.join(attributes)} />"


def render_xaml(paths: Iterable[SvgPath]) -> tuple[str, list[str]]:
    """Render one merged Path when paint matches, otherwise render every path."""
    path_list = list(paths)
    styles = {(path.fill, path.stroke) for path in path_list}
    if len(styles) == 1:
        first = path_list[0]
        merged = SvgPath(" ".join(path.data for path in path_list), first.fill, first.stroke)
        return render_path(merged) + "\n", []

    return (
        "\n".join(render_path(path) for path in path_list) + "\n",
        ["warning: multiple fill/stroke styles found; emitting separate Path elements."],
    )


def read_source(arguments: argparse.Namespace) -> str:
    """Read the mutually exclusive selected source using the specified encoding."""
    if arguments.file is not None:
        try:
            return Path(arguments.file).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError, ValueError) as error:
            raise ConversionError(f"could not read input file: {error}") from error
    if arguments.svg is not None:
        return arguments.svg
    try:
        return sys.stdin.read()
    except (OSError, UnicodeError, ValueError) as error:
        raise ConversionError(f"could not read standard input: {error}") from error


def parse_svg(source: str) -> ElementTree.Element:
    """Parse SVG XML and normalize parser errors for the command-line interface."""
    try:
        return ElementTree.fromstring(source)
    except ElementTree.ParseError as error:
        raise ConversionError(f"invalid XML: {error}") from error


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Merge SVG paths into WPF XAML paths.")
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--file", metavar="PATH", help="read SVG XML from a UTF-8 file")
    sources.add_argument("--svg", metavar="TEXT", help="SVG XML text")
    sources.add_argument("--stdin", action="store_true", help="read SVG XML from standard input")
    parser.add_argument("--format", choices=("data", "xaml"), default="xaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the SVG conversion CLI."""
    arguments = build_parser().parse_args(argv)
    try:
        root = parse_svg(read_source(arguments))
        paths, warnings = collect_paths(root)
        if arguments.format == "data":
            output = " ".join(path.data for path in paths) + "\n"
        else:
            output, style_warnings = render_xaml(paths)
            warnings.extend(style_warnings)
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(warning, file=sys.stderr)
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
