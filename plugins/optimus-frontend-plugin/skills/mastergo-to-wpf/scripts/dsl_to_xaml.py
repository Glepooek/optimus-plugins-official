"""Convert MasterGo section DSL into a WPF XAML page scaffold."""

from __future__ import annotations

import argparse
import json
import re
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


#: A long-text placeholder MasterGo substitutes for text over 50 characters.
TEXT_PLACEHOLDER = re.compile(r"\AT\d+\|[^\s|]+\Z")

#: Every string actually emitted into the page, collected for the allTexts check.
EMITTED_TEXTS: list[str] = []


def resolve_text(node: dict, section: dict, order: list[int]) -> str:
    """Return a TEXT node's real content, filling long-text placeholders.

    Long text (>50 chars) reaches the node tree as `T{sectionIndex}|{nodeId}`; the
    real string lives in `dsl.rowTexts`, in tree order. `order` tracks how many
    non-placeholder rowTexts have been consumed so far in this section.
    """
    raw = node_text(node)
    if not TEXT_PLACEHOLDER.match(raw.strip()):
        return raw
    rows = [row for row in (section.get("rowTexts") or []) if not row.get("_placeholder")]
    for row in rows:
        if row.get("parentName") == node.get("name"):
            return str(row.get("text", ""))
    if order[0] < len(rows):
        text = str(rows[order[0]].get("text", ""))
        order[0] += 1
        return text
    raise ConversionError(
        f"node {node.get('id', '?')} holds placeholder {raw!r} but no matching entry "
        "exists in dsl.rowTexts; re-fetch this section's DSL"
    )


def verify_texts(emitted: list[str], listing: dict) -> None:
    """Fail if any emitted string is outside the design's closed text set."""
    metadata = listing.get("rootMetadata") or {}
    allowed = metadata.get("allTexts")
    if not isinstance(allowed, list):
        return
    permitted = {str(item) for item in allowed}
    for text in emitted:
        if text and text not in permitted:
            raise ConversionError(
                f"generated text {text!r} is not in rootMetadata.allTexts; the design's "
                "text is a closed set, so this string would be fabricated"
            )


def resource_key(token: str) -> str:
    """Turn a design token name like `Text/Text-4` into the XAML key `TextText4`."""
    parts = re.split(r"[^0-9A-Za-z]+", token)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def node_colour(node: dict, styles: dict) -> tuple[str | None, str | None]:
    """Resolve a node's paint to (resource key or None, literal colour or None)."""
    token = node.get("_token")
    colour = node.get("_color")
    if colour is None:
        reference = node.get("fill")
        if isinstance(reference, str) and reference:
            entry = styles.get(reference)
            if entry is None:
                raise ConversionError(
                    f"node {node.get('id', '?')} references style {reference!r}, which is "
                    "not in dsl.styles; re-fetch the section DSL"
                )
            values = entry.get("value") or [{}]
            colour = values[0].get("color")
    if colour is None:
        return None, None
    return (resource_key(token) if token else None), colour


def walk(nodes: list[dict]):
    """Yield every node in the tree, depth first, in document order."""
    for node in nodes:
        yield node
        yield from walk(node.get("children") or [])


def collect_brushes(sections: list[dict]) -> dict[str, tuple[str, str]]:
    """Collect {resource key: (colour, original token name)} across all sections."""
    brushes: dict[str, tuple[str, str]] = {}
    for section in sections:
        styles = section.get("styles") or {}
        for node in walk(section.get("nodes") or []):
            key, colour = node_colour(node, styles)
            if key and colour:
                brushes.setdefault(key, (colour, str(node.get("_token"))))
    return brushes


def icon_key(node: dict) -> str:
    """Return a PATH node's svgShortKey, which is the only handle on its vector."""
    key = node.get("svgShortKey")
    if not key:
        raise ConversionError(
            f"PATH node {node.get('id', '?')} ({node.get('name', 'unnamed')}) has no "
            "svgShortKey; its vector cannot be fetched — re-fetch this section's DSL"
        )
    return str(key)


def collect_icons(sections: list[dict]) -> list[dict]:
    """List every PATH node so the caller can fetch its SVG with mcp__extractSvg."""
    icons: list[dict] = []
    for section in sections:
        for node in walk(section.get("nodes") or []):
            if node.get("type") == "PATH":
                icons.append(
                    {
                        "svgShortKey": icon_key(node),
                        "nodeId": str(node.get("id", "")),
                        "name": str(node.get("name", "")),
                    }
                )
    return icons


def render_resources(brushes: dict[str, tuple[str, str]]) -> str:
    """Render the colour ResourceDictionary."""
    lines = [
        '<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">',
    ]
    for key in sorted(brushes):
        colour, token = brushes[key]
        lines.append(f"  <!-- {token} -->")
        lines.append(f'  <SolidColorBrush x:Key="{key}" Color="{colour}" />')
    lines += ["</ResourceDictionary>", ""]
    return "\n".join(lines)


def with_alpha(colour: str, opacity: float) -> str:
    """Bake an opacity into a hex colour's alpha channel.

    A FRAME's opacity in MasterGo tints only its own background, so it must not
    become a WPF `Opacity` — that would make every child translucent too.
    """
    if not colour.startswith("#") or opacity >= 1.0:
        return colour
    digits = colour[1:]
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    if len(digits) != 6:
        return colour
    return f"#{round(max(0.0, min(1.0, opacity)) * 255):02X}{digits.upper()}"


def paint_attribute(node: dict, styles: dict, attr: str) -> str:
    """Render a node's resolved paint as a `Background=`/`Foreground=` attribute."""
    key, colour = node_colour(node, styles)
    if colour is None:
        return ""
    opacity = float(node.get("opacity", 1))
    if opacity < 1.0:
        return f' {attr}="{with_alpha(colour, opacity)}"'
    if key:
        return f' {attr}="{{StaticResource {key}}}"'
    return f' {attr}="{colour}"'


def render_text(
    node: dict,
    indent: str,
    extra: str = "",
    styles: dict | None = None,
    section: dict | None = None,
    order: list[int] | None = None,
) -> list[str]:
    """Render a TEXT node as a TextBlock, or skip it if it is placeholder boilerplate."""
    if node.get("_placeholder"):
        return []
    text = resolve_text(node, section or {}, order if order is not None else [0])
    EMITTED_TEXTS.append(text)
    content = escaped(text)
    paint = paint_attribute(node, styles or {}, "Foreground")
    return [f'{indent}<TextBlock{extra}{paint} Text="{content}" />']


def render_flex(
    node: dict,
    depth: int,
    extra: str = "",
    styles: dict | None = None,
    section: dict | None = None,
    order: list[int] | None = None,
) -> list[str]:
    """Render a flex container as a StackPanel, or a Grid when children grow."""
    styles = styles or {}
    indent = "  " * depth
    info = node.get("flexContainerInfo") or {}
    children = node.get("children") or []
    grows = [child for child in children if child.get("flexGrow")]
    paint = paint_attribute(node, styles, "Background")

    if grows:
        horizontal = str(info.get("flexDirection", "row")).lower() == "row"
        gap = float(info.get("gap") or 0)
        axis, definition = ("Column", "ColumnDefinition Width") if horizontal else ("Row", "RowDefinition Height")
        lines = [f"{indent}<Grid{extra}{paint}>", f"{indent}  <Grid.{axis}Definitions>"]
        lines += [f'{indent}    <{definition}="*" />' for _ in children]
        lines.append(f"{indent}  </Grid.{axis}Definitions>")
        for position, child in enumerate(children):
            child_extra = f' Grid.{axis}="{position}"'
            if gap and position < len(children) - 1:
                margin = f"0,0,{number(gap)},0" if horizontal else f"0,0,0,{number(gap)}"
                child_extra += f' Margin="{margin}"'
            lines += render_node(
                child, depth + 1, extra=child_extra, absolute=False, styles=styles,
                section=section, order=order,
            )
        lines.append(f"{indent}</Grid>")
        return lines

    horizontal = str(info.get("flexDirection", "row")).lower() == "row"
    orientation = "Horizontal" if horizontal else "Vertical"
    gap = float(info.get("gap") or 0)
    lines = [f'{indent}<StackPanel Orientation="{orientation}"{extra}{paint}>']
    for position, child in enumerate(children):
        child_extra = ""
        if gap and position < len(children) - 1:
            margin = f"0,0,{number(gap)},0" if horizontal else f"0,0,0,{number(gap)}"
            child_extra = f' Margin="{margin}"'
        lines += render_node(
            child, depth + 1, extra=child_extra, absolute=False, styles=styles,
            section=section, order=order,
        )
    lines.append(f"{indent}</StackPanel>")
    return lines


def canvas_position(node: dict) -> str:
    """Return the Canvas attached properties for an absolutely positioned node."""
    layout = node.get("layoutStyle") or {}
    if "relativeX" not in layout and "relativeY" not in layout:
        raise ConversionError(
            f"node {node.get('id', '?')} ({node.get('name', 'unnamed')}) has no "
            "layoutStyle.relativeX/relativeY and is not inside a flex container; "
            "its position cannot be determined"
        )
    left = number(layout.get("relativeX", 0))
    top = number(layout.get("relativeY", 0))
    return f' Canvas.Left="{left}" Canvas.Top="{top}"'


def render_node(
    node: dict,
    depth: int,
    extra: str = "",
    absolute: bool = False,
    styles: dict | None = None,
    section: dict | None = None,
    order: list[int] | None = None,
) -> list[str]:
    """Render one DSL node and its subtree.

    `absolute` says the parent positions its children with Canvas coordinates; flex
    parents pass False so their children never receive Canvas.Left/Top.
    """
    styles = styles or {}
    indent = "  " * depth
    placement = canvas_position(node) if absolute else ""
    if node.get("type") == "PATH":
        return [f"{indent}<!-- ICON:{icon_key(node)} -->",
                f'{indent}<Path{extra}{placement} />']
    if node.get("type") == "TEXT":
        return render_text(node, indent, extra + placement, styles=styles, section=section, order=order)
    if node.get("flexContainerInfo"):
        return render_flex(node, depth, extra + placement, styles=styles, section=section, order=order)
    paint = paint_attribute(node, styles, "Background")
    lines = [f"{indent}<Canvas{extra}{placement}{paint}>"]
    for child in node.get("children") or []:
        lines += render_node(child, depth + 1, absolute=True, styles=styles, section=section, order=order)
    lines.append(f"{indent}</Canvas>")
    return lines


def render_page(
    listing: dict, sections: list[dict], page_name: str, has_brushes: bool = False
) -> str:
    """Render the whole page: a Canvas shell holding every section.

    `has_brushes` says whether `collect_brushes` produced any entries; only then
    does the page wire up Colors.xaml, so a token-free design never references an
    empty dictionary.
    """
    EMITTED_TEXTS.clear()
    lines = [
        '<UserControl xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"',
        f'             x:Class="{page_name}">',
    ]
    if has_brushes:
        lines += [
            "  <UserControl.Resources>",
            '    <ResourceDictionary Source="Colors.xaml" />',
            "  </UserControl.Resources>",
        ]
    lines.append("  <Canvas>")
    containers = listing.get("splitContainers") or []
    for index, section in enumerate(sections):
        box = containers[index] if index < len(containers) else {}
        left, top = number(box.get("x", 0)), number(box.get("y", 0))
        lines.append(f'    <Canvas Canvas.Left="{left}" Canvas.Top="{top}">')
        styles = section.get("styles") or {}
        order = [0]
        nodes = section.get("nodes") or []
        roots_absolute = len(nodes) > 1
        for node in nodes:
            lines += render_node(
                node, 3, absolute=roots_absolute, styles=styles, section=section, order=order,
            )
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
        brushes = collect_brushes(sections)
        xaml = render_page(listing, sections, arguments.page_name, has_brushes=bool(brushes))
        verify_texts(EMITTED_TEXTS, listing)
        icons = collect_icons(sections)
        out_dir = Path(arguments.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{arguments.page_name}.xaml").write_text(xaml, encoding="utf-8")
        (out_dir / "Colors.xaml").write_text(render_resources(brushes), encoding="utf-8")
        (out_dir / "icons.json").write_text(
            json.dumps(icons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
