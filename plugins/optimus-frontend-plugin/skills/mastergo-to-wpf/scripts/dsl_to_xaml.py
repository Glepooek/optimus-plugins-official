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


def number(value: float) -> str:
    """Format a coordinate without a trailing fraction, so output stays readable."""
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-", "-0") else text


def escaped(value: str) -> str:
    """Escape text for an XML attribute or element body."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def node_text(node: dict) -> str:
    """Join a TEXT node's rich-text runs into one string."""
    runs = node.get("text") or []
    return "".join(str(run.get("text", "")) for run in runs if isinstance(run, dict))


def render_text(node: dict, indent: str, extra: str = "") -> list[str]:
    """Render a TEXT node as a TextBlock."""
    content = escaped(node_text(node))
    return [f'{indent}<TextBlock{extra} Text="{content}" />']


def render_flex(node: dict, depth: int) -> list[str]:
    """Render a flex container as a StackPanel, or a Grid when children grow."""
    indent = "  " * depth
    info = node.get("flexContainerInfo") or {}
    children = node.get("children") or []
    grows = [child for child in children if child.get("flexGrow")]

    if grows:
        lines = [f"{indent}<Grid>", f"{indent}  <Grid.ColumnDefinitions>"]
        lines += [f'{indent}    <ColumnDefinition Width="*" />' for _ in children]
        lines.append(f"{indent}  </Grid.ColumnDefinitions>")
        for column, child in enumerate(children):
            lines += render_node(child, depth + 1, extra=f' Grid.Column="{column}"')
        lines.append(f"{indent}</Grid>")
        return lines

    horizontal = str(info.get("flexDirection", "row")).lower() == "row"
    orientation = "Horizontal" if horizontal else "Vertical"
    gap = float(info.get("gap") or 0)
    lines = [f'{indent}<StackPanel Orientation="{orientation}">']
    for position, child in enumerate(children):
        extra = ""
        if gap and position < len(children) - 1:
            margin = f"0,0,{number(gap)},0" if horizontal else f"0,0,0,{number(gap)}"
            extra = f' Margin="{margin}"'
        lines += render_node(child, depth + 1, extra=extra)
    lines.append(f"{indent}</StackPanel>")
    return lines


def render_node(node: dict, depth: int, extra: str = "") -> list[str]:
    """Render one DSL node and its subtree."""
    indent = "  " * depth
    kind = node.get("type")
    if kind == "TEXT":
        return render_text(node, indent, extra)
    if node.get("flexContainerInfo"):
        return render_flex(node, depth)
    lines = [f"{indent}<Grid{extra}>"]
    for child in node.get("children") or []:
        lines += render_node(child, depth + 1)
    lines.append(f"{indent}</Grid>")
    return lines


def render_page(listing: dict, sections: list[dict], page_name: str) -> str:
    """Render the whole page: a Canvas shell holding every section."""
    lines = [
        '<UserControl xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"',
        f'             x:Class="{page_name}">',
        "  <Canvas>",
    ]
    containers = listing.get("splitContainers") or []
    for index, section in enumerate(sections):
        box = containers[index] if index < len(containers) else {}
        left, top = number(box.get("x", 0)), number(box.get("y", 0))
        lines.append(f'    <Canvas Canvas.Left="{left}" Canvas.Top="{top}">')
        for node in section.get("nodes") or []:
            lines += render_node(node, 3)
        lines.append("    </Canvas>")
    lines += ["  </Canvas>", "</UserControl>", ""]
    return "\n".join(lines)


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
        listing, sections = load_sections(Path(arguments.input))
        xaml = render_page(listing, sections, arguments.page_name)
        out_dir = Path(arguments.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{arguments.page_name}.xaml").write_text(xaml, encoding="utf-8")
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
