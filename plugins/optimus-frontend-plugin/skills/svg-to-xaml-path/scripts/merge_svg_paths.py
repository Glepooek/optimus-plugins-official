"""Merge SVG path data into WPF XAML Path elements."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, replace
from html import escape
from pathlib import Path
from typing import Iterable


#: Container elements whose descendants are never rendered directly.
NON_RENDERED_TAGS = frozenset({"defs", "clipPath", "mask", "symbol", "marker", "pattern"})
#: Presentation properties read out of inline `style` declarations.
CONVERTED_STYLE_PROPERTIES = frozenset(
    {"fill", "stroke", "fill-rule", "display", "visibility", "transform"}
)
#: WPF fill rule prefixes; SVG defaults to nonzero while WPF defaults to EvenOdd.
FILL_RULE_PREFIXES = {"nonzero": "F1", "evenodd": "F0"}


class ConversionError(Exception):
    """An input or SVG conversion error that should be shown to the user."""


@dataclass(frozen=True)
class SvgPath:
    """A usable SVG path and its effective inherited presentation attributes."""

    data: str
    fill: str | None
    stroke: str | None
    fill_rule: str


@dataclass(frozen=True)
class Inherited:
    """Presentation state an element inherits from its ancestors."""

    fill: str = "#000000"
    stroke: str = "none"
    fill_rule: str = "nonzero"
    visibility: str = "visible"
    transforms: tuple[str, ...] = ()


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


def parse_style(value: str) -> dict[str, str]:
    """Parse an inline `style` attribute into lowercase property declarations."""
    declarations: dict[str, str] = {}
    for declaration in value.split(";"):
        name, separator, raw_value = declaration.partition(":")
        if separator:
            declarations[name.strip().lower()] = raw_value.strip()
    return declarations


def presentation(
    element: ElementTree.Element, declarations: dict[str, str], name: str, fallback: str
) -> str:
    """Resolve a presentation property; an inline `style` outranks the plain attribute."""
    return declarations.get(name, element.attrib.get(name, fallback))


def normalized_fill_rule(value: str) -> str:
    """Normalize an SVG fill-rule, defaulting anything unrecognized to nonzero."""
    return "evenodd" if value.strip().lower() == "evenodd" else "nonzero"


def collect_paths(root: ElementTree.Element) -> tuple[list[SvgPath], list[str]]:
    """Collect rendered paths in document order and conversion warnings."""
    paths: list[SvgPath] = []
    warnings: list[str] = []
    saw_class = False
    ignored_properties: set[str] = set()
    stack = [(root, Inherited())]

    while stack:
        element, inherited = stack.pop()
        element_name = local_name(element.tag)
        if element_name in NON_RENDERED_TAGS:
            continue

        saw_class = saw_class or "class" in element.attrib
        declarations = parse_style(element.attrib.get("style", ""))
        ignored_properties.update(set(declarations) - CONVERTED_STYLE_PROPERTIES)
        if presentation(element, declarations, "display", "").strip().lower() == "none":
            continue

        current = Inherited(
            fill=presentation(element, declarations, "fill", inherited.fill),
            stroke=presentation(element, declarations, "stroke", inherited.stroke),
            fill_rule=presentation(element, declarations, "fill-rule", inherited.fill_rule),
            visibility=presentation(element, declarations, "visibility", inherited.visibility),
            transforms=inherited.transforms,
        )
        transform = presentation(element, declarations, "transform", "").strip()
        if transform:
            source = (
                f"path transform {transform!r}"
                if element_name == "path"
                else f"ancestor <{element_name}> transform {transform!r}"
            )
            current = replace(current, transforms=(*current.transforms, source))

        if element_name == "path":
            data = element.attrib.get("d", "").strip()
            if data and current.visibility.strip().lower() != "hidden":
                path_index = len(paths) + 1
                if current.transforms:
                    raise ConversionError(
                        f"SVG transform attributes are not supported for path {path_index}: "
                        + "; ".join(current.transforms)
                    )
                paths.append(
                    SvgPath(
                        data=data,
                        fill=effective_paint(current.fill),
                        stroke=effective_paint(current.stroke),
                        fill_rule=normalized_fill_rule(current.fill_rule),
                    )
                )

        for child in reversed(list(element)):
            stack.append((child, current))

    if saw_class:
        warnings.append(
            "warning: class attributes were encountered; CSS classes were not converted."
        )
    if ignored_properties:
        warnings.append(
            "warning: unconverted style declarations were ignored: "
            + ", ".join(sorted(ignored_properties))
            + "."
        )
    if not paths:
        raise ConversionError("No <path> elements with nonempty d attributes found")

    return paths, warnings


def attribute(name: str, value: str) -> str:
    """Render an XML attribute using double quotes and XML escaping."""
    return f'{name}="{escape(value, quote=True)}"'


def geometry(fill_rule: str, data: str) -> str:
    """Prefix path data with the WPF fill rule matching SVG's nonzero default."""
    return f"{FILL_RULE_PREFIXES[fill_rule]} {data}"


def render_path(path: SvgPath) -> str:
    """Render one WPF Path element with the required attribute order."""
    attributes: list[str] = []
    if path.fill is not None:
        attributes.append(attribute("Fill", path.fill))
    if path.stroke is not None:
        attributes.append(attribute("Stroke", path.stroke))
    attributes.append(attribute("Data", geometry(path.fill_rule, path.data)))
    return f"<Path {' '.join(attributes)} />"


def render_xaml(paths: Iterable[SvgPath]) -> tuple[str, list[str]]:
    """Render one merged Path when presentation matches, otherwise render every path."""
    path_list = list(paths)
    styles = {(path.fill, path.stroke, path.fill_rule) for path in path_list}
    if len(styles) == 1:
        first = path_list[0]
        merged = SvgPath(
            " ".join(path.data for path in path_list),
            first.fill,
            first.stroke,
            first.fill_rule,
        )
        return render_path(merged) + "\n", []

    return (
        "\n".join(render_path(path) for path in path_list) + "\n",
        [
            "warning: multiple fill/stroke/fill-rule styles found; "
            "emitting separate Path elements."
        ],
    )


def render_data(paths: list[SvgPath]) -> tuple[str, list[str]]:
    """Render every path's data as one geometry, which carries a single fill rule."""
    warnings: list[str] = []
    if len({path.fill_rule for path in paths}) > 1:
        warnings.append(
            "warning: multiple fill rules found; data output uses the first path's rule."
        )
    return geometry(paths[0].fill_rule, " ".join(path.data for path in paths)) + "\n", warnings


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
            output, format_warnings = render_data(paths)
        else:
            output, format_warnings = render_xaml(paths)
        warnings.extend(format_warnings)
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(warning, file=sys.stderr)
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
