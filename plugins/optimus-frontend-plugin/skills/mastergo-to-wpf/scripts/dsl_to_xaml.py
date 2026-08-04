"""Convert MasterGo section DSL into a deterministic WPF XAML page scaffold."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


class ConversionError(Exception):
    """An input or conversion error that should be shown to the user."""


TEXT_PLACEHOLDER = re.compile(r"\AT\d+\|[^\s|]+\Z")
SECTION_FILE = re.compile(r"\Asection-(\d+)\.json\Z")
ANCHOR = re.compile(r"<--@([A-Za-z_]\w*)(?:\.([A-Za-z_][\w.-]*))?-->")
XML_NAME = re.compile(r"\A[A-Za-z_][\w.-]*\Z")
HEX_COLOUR = re.compile(r"\A#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\Z")
# WPF only accepts these enum values; anything else makes the page fail to load.
FONT_WEIGHTS = {"Thin", "ExtraLight", "UltraLight", "Light", "Normal", "Regular", "Medium",
                "DemiBold", "SemiBold", "Bold", "ExtraBold", "UltraBold", "Black", "Heavy"}
TEXT_ENUMS = {
    "FontWeight": FONT_WEIGHTS,
    "FontStyle": {"Normal", "Italic", "Oblique"},
    "TextAlignment": {"Left", "Right", "Center", "Justify"},
    "TextWrapping": {"Wrap", "NoWrap", "WrapWithOverflow"},
}
EMITTED_TEXTS: list[str] = []


def read_json(path: Path) -> object:
    """Read one JSON file, naming it in any error so the user can find it."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError) as error:
        raise ConversionError(f"could not read {path.name}: {error}") from error
    except json.JSONDecodeError as error:
        raise ConversionError(f"{path.name} is not valid JSON: {error}") from error


def load_sections(directory: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load section DSL files in numeric sectionIndex order."""
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

    indexed_paths: list[tuple[int, Path]] = []
    for path in directory.glob("section-*.json"):
        match = SECTION_FILE.match(path.name)
        if match:
            indexed_paths.append((int(match.group(1)), path))
    sections: list[dict[str, Any]] = []
    for index, path in sorted(indexed_paths, key=lambda item: item[0]):
        section = read_json(path)
        if not isinstance(section, dict):
            raise ConversionError(f"{path.name} must contain a JSON object")
        section = dict(section)
        section["_sectionIndex"] = index
        sections.append(section)
    return listing, sections


def finite_nonnegative(value: object) -> float | None:
    """Return a finite, non-negative number or None for missing/invalid inputs."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) and result >= 0 else None


def number(value: object) -> str:
    """Format a known valid coordinate or dimension without a trailing fraction."""
    result = finite_nonnegative(value)
    if result is None:
        return "0"
    text = f"{result:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def escaped(value: object) -> str:
    """Escape an XML attribute or element value."""
    return (
        str(value).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def hex_colour(value: object) -> str | None:
    """Return a literal colour only when it is a hex form WPF can actually parse."""
    if isinstance(value, str) and HEX_COLOUR.match(value.strip()):
        return value.strip()
    return None


def note_fallback(report: dict[str, Any], node: dict[str, Any], reason: str) -> None:
    """Record a degraded conversion so exit 0 never means silent data loss."""
    report["fallbacks"].append({"nodeId": str(node.get("id", "")), "reason": reason})


def node_text(node: dict[str, Any]) -> str:
    """Join a TEXT node's rich-text runs into one string."""
    runs = node.get("text") or []
    return "".join(str(run.get("text", "")) for run in runs if isinstance(run, dict))


def resolve_text(node: dict[str, Any], section: dict[str, Any], order: list[int]) -> str:
    """Return a TEXT node's real content, filling long-text placeholders."""
    raw = node_text(node)
    if not TEXT_PLACEHOLDER.match(raw.strip()):
        return raw
    rows = [row for row in (section.get("rowTexts") or []) if isinstance(row, dict) and not row.get("_placeholder")]
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


def verify_texts(emitted: list[str], listing: dict[str, Any]) -> None:
    """Fail if an emitted string falls outside the design's closed text set."""
    metadata = listing.get("rootMetadata") or {}
    allowed = metadata.get("allTexts") if isinstance(metadata, dict) else None
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
    """Turn a design token name such as `Text/Text-4` into a WPF resource key."""
    parts = re.split(r"[^0-9A-Za-z]+", token)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def load_mapping(path_value: str | None) -> tuple[dict[str, Any], str | None]:
    """Load a strict, data-only project mapping; errors degrade to native WPF output."""
    if not path_value:
        return {}, None
    path = Path(path_value)
    try:
        payload = read_json(path)
    except ConversionError as error:
        return {}, str(error)
    if not isinstance(payload, dict):
        return {}, "mapping must contain a JSON object"
    resources = payload.get("resources", {})
    xmlns = payload.get("xmlns", {})
    components = payload.get("components", {})
    if not all(isinstance(item, dict) for item in (resources, xmlns, components)):
        return {}, "mapping resources, xmlns, and components must be JSON objects"
    if any(not isinstance(key, str) or not isinstance(value, str) or not XML_NAME.match(value) for key, value in resources.items()):
        return {}, "mapping resources must map design token strings to valid resource keys"
    if any(not isinstance(key, str) or not XML_NAME.match(key) or not isinstance(value, str) or any(c in value for c in '<>\"') for key, value in xmlns.items()):
        return {}, "mapping xmlns entries must use safe prefix and namespace strings"
    safe_components: dict[str, dict[str, Any]] = {}
    for name, definition in components.items():
        if not isinstance(name, str) or not isinstance(definition, dict):
            return {}, "mapping components must map names to objects"
        prefix, control = definition.get("xmlns"), definition.get("type")
        allowed = definition.get("allowedProperties", {})
        variants = definition.get("variants", {})
        if (not isinstance(prefix, str) or prefix not in xmlns or not isinstance(control, str)
                or not XML_NAME.match(control) or not isinstance(allowed, dict) or not isinstance(variants, dict)):
            return {}, f"mapping component {name!r} is invalid or refers to an undeclared xmlns prefix"
        if any(not isinstance(key, str) or not XML_NAME.match(key) or not isinstance(value, list) or not all(isinstance(v, str) for v in value) for key, value in allowed.items()):
            return {}, f"mapping component {name!r} has invalid allowedProperties"
        safe_components[name] = definition
    return {"resources": resources, "xmlns": xmlns, "components": safe_components}, None


def node_colour(node: dict[str, Any], styles: dict[str, Any], mapping: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Resolve paint to (resource key, literal colour, token), preferring project mapping."""
    token = node.get("_token")
    token = str(token) if token else None
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
            colour = values[0].get("color") if isinstance(values[0], dict) else None
    if colour is None:
        return None, None, token
    colour = str(colour)
    project_key = (mapping.get("resources", {}) or {}).get(token) if token else None
    return project_key or (resource_key(token) if token else None), colour, token


def walk(nodes: list[dict[str, Any]]):
    """Yield every node in depth-first document order."""
    for node in nodes:
        if isinstance(node, dict):
            yield node
            yield from walk(node.get("children") or [])


def collect_brushes(sections: list[dict[str, Any]], mapping: dict[str, Any], report: dict[str, Any]) -> dict[str, tuple[str, str]]:
    """Collect local token brushes while recording project-resource coverage."""
    brushes: dict[str, tuple[str, str]] = {}
    coverage = report["tokenCoverage"]
    seen: set[str] = set()
    for section in sections:
        styles = section.get("styles") or {}
        for node in walk(section.get("nodes") or []):
            key, colour, token = node_colour(node, styles, mapping)
            if not colour:
                continue
            if token and token not in seen:
                seen.add(token)
                if token in (mapping.get("resources", {}) or {}):
                    coverage["mapped"] += 1
                else:
                    coverage["literal"] += 1
            if key and token and token not in (mapping.get("resources", {}) or {}):
                brushes.setdefault(key, (colour, token))
    return brushes


def icon_key(node: dict[str, Any]) -> str:
    key = node.get("svgShortKey")
    if not key:
        raise ConversionError(
            f"PATH node {node.get('id', '?')} ({node.get('name', 'unnamed')}) has no "
            "svgShortKey; its vector cannot be fetched — re-fetch this section's DSL"
        )
    return str(key)


def size_attributes(node: dict[str, Any], report: dict[str, Any]) -> str:
    layout = node.get("layoutStyle") or {}
    values: list[str] = []
    missing: list[str] = []
    for dsl_name, xaml_name in (("width", "Width"), ("height", "Height")):
        value = finite_nonnegative(layout.get(dsl_name, node.get(dsl_name)))
        if value is None:
            if dsl_name in layout or dsl_name in node:
                report["fallbacks"].append({"nodeId": str(node.get("id", "")), "reason": f"invalid {dsl_name} ignored"})
            else:
                missing.append(dsl_name)
        else:
            values.append(f' {xaml_name}="{number(value)}"')
    if missing:
        report["missingDimensions"].append({"nodeId": str(node.get("id", "")), "fields": missing})
    return "".join(values)


def parse_thickness(value: object) -> str | None:
    if isinstance(value, str):
        parts = re.split(r"[\s,]+", value.strip())
    elif isinstance(value, (list, tuple)):
        parts = list(value)
    elif isinstance(value, dict):
        parts = [value.get(key) for key in ("left", "top", "right", "bottom")]
    else:
        parts = [value]
    if not 1 <= len(parts) <= 4:
        return None
    parsed = [finite_nonnegative(part) for part in parts]
    if any(part is None for part in parsed):
        return None
    return ",".join(number(part) for part in parsed)


def paint_attribute(node: dict[str, Any], styles: dict[str, Any], attr: str, mapping: dict[str, Any]) -> str:
    """Render a resolved paint as an attribute, keeping FRAME opacity local to paint."""
    key, colour, _ = node_colour(node, styles, mapping)
    if colour is None:
        return ""
    opacity = finite_nonnegative(node.get("opacity", 1))
    if opacity is not None and opacity < 1.0:
        return f' {attr}="{with_alpha(colour, opacity)}"'
    if key:
        return f' {attr}="{{StaticResource {key}}}"'
    return f' {attr}="{escaped(colour)}"'


def with_alpha(colour: str, opacity: float) -> str:
    """Bake background opacity into a hex paint, never into parent Opacity."""
    if not colour.startswith("#") or opacity >= 1.0:
        return colour
    digits = colour[1:]
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    if len(digits) != 6:
        return colour
    return f"#{round(max(0.0, min(1.0, opacity)) * 255):02X}{digits.upper()}"


def padding_attribute(node: dict[str, Any]) -> str:
    value = node.get("padding")
    if value is None:
        info = node.get("flexContainerInfo") or {}
        value = info.get("padding") if isinstance(info, dict) else None
    thickness = parse_thickness(value) if value is not None else None
    return f' Padding="{thickness}"' if thickness is not None else ""


def border_attributes(node: dict[str, Any], styles: dict[str, Any], mapping: dict[str, Any], report: dict[str, Any]) -> str:
    stroke = node.get("strokeColor", node.get("stroke"))
    width = node.get("strokeWidth", node.get("strokeThickness"))
    radius = node.get("cornerRadius", node.get("radius"))
    attrs = ""
    if stroke is not None or width is not None:
        width_text = parse_thickness(width)
        if stroke is not None and width_text is not None:
            if isinstance(stroke, str) and stroke.startswith("#"):
                brush = stroke
            else:
                brush = str(stroke)
            attrs += f' BorderBrush="{escaped(brush)}" BorderThickness="{width_text}"'
        else:
            report["fallbacks"].append({"nodeId": str(node.get("id", "")), "reason": "stroke color/width could not be parsed as a pair"})
    radius_text = parse_thickness(radius) if radius is not None else None
    if radius is not None and radius_text is None:
        report["fallbacks"].append({"nodeId": str(node.get("id", "")), "reason": "corner radius could not be parsed"})
    if radius_text is not None:
        attrs += f' CornerRadius="{radius_text}"'
    return attrs


def text_attributes(source: dict[str, Any], styles: dict[str, Any], mapping: dict[str, Any]) -> str:
    """Map reliable common text fields without inventing a fallback font."""
    attrs = ""
    value_map = (("fontFamily", "FontFamily"), ("fontSize", "FontSize"), ("fontWeight", "FontWeight"),
                 ("fontStyle", "FontStyle"), ("lineHeight", "LineHeight"), ("textAlignment", "TextAlignment"),
                 ("textAlign", "TextAlignment"), ("textWrapping", "TextWrapping"), ("wrap", "TextWrapping"))
    for dsl_name, xaml_name in value_map:
        value = source.get(dsl_name)
        if value is not None and value != "":
            if dsl_name in {"fontSize", "lineHeight"} and finite_nonnegative(value) is None:
                continue
            if dsl_name == "wrap" and isinstance(value, bool):
                value = "Wrap" if value else "NoWrap"
            attrs += f' {xaml_name}="{escaped(value)}"'
    attrs += paint_attribute(source, styles, "Foreground", mapping)
    return attrs


def has_visual_box(node: dict[str, Any], styles: dict[str, Any], mapping: dict[str, Any]) -> bool:
    return bool(paint_attribute(node, styles, "Background", mapping) or padding_attribute(node)
                or border_attributes(node, styles, mapping, {"fallbacks": []}))


def render_text(node: dict[str, Any], indent: str, extra: str, styles: dict[str, Any], section: dict[str, Any], order: list[int], mapping: dict[str, Any], report: dict[str, Any]) -> list[str]:
    if node.get("_placeholder"):
        return []
    resolved = resolve_text(node, section, order)
    EMITTED_TEXTS.append(resolved)
    runs = [run for run in (node.get("text") or []) if isinstance(run, dict)]
    is_placeholder = bool(runs) and TEXT_PLACEHOLDER.match(node_text(node).strip())
    attrs = extra + size_attributes(node, report) + text_attributes(node, styles, mapping)
    if len(runs) <= 1 or is_placeholder:
        return [f'{indent}<TextBlock{attrs} Text="{escaped(resolved)}" />']
    lines = [f"{indent}<TextBlock{attrs}>"]
    for run in runs:
        run_text = str(run.get("text", ""))
        # The node-level resolved text is authoritative for placeholders; normal rich text keeps each run.
        lines.append(f'{indent}  <Run Text="{escaped(run_text)}"{text_attributes(run, styles, mapping)} />')
    lines.append(f"{indent}</TextBlock>")
    return lines


def render_image(node: dict[str, Any], indent: str, extra: str, report: dict[str, Any]) -> list[str]:
    source = node.get("url", node.get("src", node.get("cssCode")))
    source_text = str(source) if source else ""
    if "url([object Object])" in source_text:
        status, reason = "unrecoverable", "upstream url([object Object]) cannot be recovered"
    elif source_text:
        status, reason = "not-exported", "image resource must be exported and assigned manually"
    else:
        status, reason = "missing", "no recoverable image resource reference in DSL"
    entry = {"nodeId": str(node.get("id", "")), "name": str(node.get("name", "")), "width": (node.get("layoutStyle") or {}).get("width"), "height": (node.get("layoutStyle") or {}).get("height"), "sourceHint": source_text or None, "status": status, "reason": reason}
    report["assets"]["images"].append(entry)
    report["manualHandoffs"].append({"nodeId": entry["nodeId"], "reason": reason})
    return [f'{indent}<!-- TODO IMAGE:{entry["nodeId"]} {escaped(reason)} -->', f'{indent}<Image{extra}{size_attributes(node, report)} Stretch="Fill" />']


def render_flex(node: dict[str, Any], depth: int, extra: str, styles: dict[str, Any], section: dict[str, Any], order: list[int], mapping: dict[str, Any], report: dict[str, Any]) -> list[str]:
    indent = "  " * depth
    info = node.get("flexContainerInfo") or {}
    children = node.get("children") or []
    grows = [child for child in children if isinstance(child, dict) and child.get("flexGrow")]
    horizontal = str(info.get("flexDirection", "row")).lower() == "row"
    gap_value = finite_nonnegative(info.get("gap"))
    gap = gap_value or 0
    outer_attrs = extra + size_attributes(node, report)
    visual_attrs = paint_attribute(node, styles, "Background", mapping) + padding_attribute(node) + border_attributes(node, styles, mapping, report)
    wrapper = bool(visual_attrs)
    if wrapper:
        lines = [f"{indent}<Border{outer_attrs}{visual_attrs}>"]
        content_depth = depth + 1
    else:
        lines = []
        content_depth = depth
    content_indent = "  " * content_depth
    if grows:
        axis, definition = ("Column", "ColumnDefinition Width") if horizontal else ("Row", "RowDefinition Height")
        lines.extend([f"{content_indent}<Grid>", f"{content_indent}  <Grid.{axis}Definitions>"])
        lines.extend(f'{content_indent}    <{definition}="*" />' for _ in children)
        lines.append(f"{content_indent}  </Grid.{axis}Definitions>")
        for position, child in enumerate(children):
            child_extra = f' Grid.{axis}="{position}"'
            if gap and position < len(children) - 1:
                margin = f"0,0,{number(gap)},0" if horizontal else f"0,0,0,{number(gap)}"
                child_extra += f' Margin="{margin}"'
            lines.extend(render_node(child, content_depth + 1, child_extra, False, styles, section, order, mapping, report))
        lines.append(f"{content_indent}</Grid>")
        mode = "flex-grid"
    else:
        orientation = "Horizontal" if horizontal else "Vertical"
        lines.append(f'{content_indent}<StackPanel Orientation="{orientation}">')
        for position, child in enumerate(children):
            child_extra = ""
            if gap and position < len(children) - 1:
                margin = f"0,0,{number(gap)},0" if horizontal else f"0,0,0,{number(gap)}"
                child_extra = f' Margin="{margin}"'
            lines.extend(render_node(child, content_depth + 1, child_extra, False, styles, section, order, mapping, report))
        lines.append(f"{content_indent}</StackPanel>")
        mode = "flex"
    if wrapper:
        lines.append(f"{indent}</Border>")
    report["sectionsByNode"].append({"nodeId": str(node.get("id", "")), "renderMode": mode})
    return lines


def canvas_position(node: dict[str, Any]) -> str:
    layout = node.get("layoutStyle") or {}
    if "relativeX" not in layout and "relativeY" not in layout:
        raise ConversionError(
            f"node {node.get('id', '?')} ({node.get('name', 'unnamed')}) has no "
            "layoutStyle.relativeX/relativeY and is not inside a flex container; its position cannot be determined"
        )
    return f' Canvas.Left="{number(layout.get("relativeX", 0))}" Canvas.Top="{number(layout.get("relativeY", 0))}"'


def component_for(node: dict[str, Any], mapping: dict[str, Any], report: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve only registered Layer Anchors; all other component intent safely falls back."""
    match = ANCHOR.search(str(node.get("name", "")))
    if not match:
        return None, None
    component, variant = match.groups()
    definition = (mapping.get("components", {}) or {}).get(component)
    if definition is None:
        report["fallbacks"].append({"nodeId": str(node.get("id", "")), "reason": f"unregistered layer anchor {component}"})
        return None, variant
    report["componentMapping"].append({"nodeId": str(node.get("id", "")), "component": component, "source": "anchor", "confidence": 1.0, "fallbackReason": None})
    return definition, variant


def render_node(node: dict[str, Any], depth: int, extra: str, absolute: bool, styles: dict[str, Any], section: dict[str, Any], order: list[int], mapping: dict[str, Any], report: dict[str, Any]) -> list[str]:
    """Render a node with conservative native-WPF fallback semantics."""
    indent = "  " * depth
    placement = canvas_position(node) if absolute else ""
    attrs = extra + placement
    node_type = node.get("type")
    if node_type == "PATH":
        key = icon_key(node)
        report["assets"]["icons"].append({"svgShortKey": key, "nodeId": str(node.get("id", "")), "name": str(node.get("name", "")), "x": (node.get("layoutStyle") or {}).get("relativeX"), "y": (node.get("layoutStyle") or {}).get("relativeY"), "width": (node.get("layoutStyle") or {}).get("width"), "height": (node.get("layoutStyle") or {}).get("height"), "color": node.get("_color")})
        return [f"{indent}<!-- ICON:{key} -->", f'{indent}<Path{attrs}{size_attributes(node, report)}{paint_attribute(node, styles, "Fill", mapping)} />']
    if node_type == "TEXT":
        return render_text(node, indent, attrs, styles, section, order, mapping, report)
    if node_type == "IMAGE":
        return render_image(node, indent, attrs, report)
    if node.get("flexContainerInfo"):
        return render_flex(node, depth, attrs, styles, section, order, mapping, report)

    component, variant = component_for(node, mapping, report)
    if component:
        prefix, control = component["xmlns"], component["type"]
        allowed = component.get("allowedProperties", {})
        properties = ""
        if variant and "Variant" in allowed and variant in allowed["Variant"]:
            properties = f' Variant="{escaped(variant)}"'
        return [f'{indent}<{prefix}:{control}{attrs}{size_attributes(node, report)}{properties} />']

    visual_attrs = paint_attribute(node, styles, "Background", mapping) + padding_attribute(node) + border_attributes(node, styles, mapping, report)
    variant_comment: list[str] = []
    if node_type == "INSTANCE" and node.get("_variantProps"):
        value = json.dumps(node.get("_variantProps"), ensure_ascii=False, sort_keys=True)
        variant_comment = [f"{indent}<!-- TODO INSTANCE_VARIANTS:{escaped(value)} -->"]
        report["manualHandoffs"].append({"nodeId": str(node.get("id", "")), "reason": "instance variant props require a registered mapping", "variantProps": node.get("_variantProps")})
    if visual_attrs:
        lines = variant_comment + [f'{indent}<Border{attrs}{size_attributes(node, report)}{visual_attrs}>', f"{indent}  <Canvas>"]
        for child in node.get("children") or []:
            lines.extend(render_node(child, depth + 2, "", True, styles, section, order, mapping, report))
        lines.extend([f"{indent}  </Canvas>", f"{indent}</Border>"])
        return lines
    lines = variant_comment + [f"{indent}<Canvas{attrs}{size_attributes(node, report)}>"]
    for child in node.get("children") or []:
        lines.extend(render_node(child, depth + 1, "", True, styles, section, order, mapping, report))
    lines.append(f"{indent}</Canvas>")
    return lines


def render_resources(brushes: dict[str, tuple[str, str]]) -> str:
    lines = ['<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"', '                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">']
    for key in sorted(brushes):
        colour, token = brushes[key]
        lines.extend([f"  <!-- {escaped(token)} -->", f'  <SolidColorBrush x:Key="{key}" Color="{escaped(colour)}" />'])
    return "\n".join(lines + ["</ResourceDictionary>", ""])


def render_page(listing: dict[str, Any], sections: list[dict[str, Any]], page_name: str, brushes: dict[str, tuple[str, str]], mapping: dict[str, Any], report: dict[str, Any]) -> str:
    EMITTED_TEXTS.clear()
    lines = ['<UserControl xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"', '             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"']
    for prefix, uri in sorted((mapping.get("xmlns", {}) or {}).items()):
        lines.append(f'             xmlns:{prefix}="{escaped(uri)}"')
    lines.append(f'             x:Class="{escaped(page_name)}">')
    if brushes:
        lines.extend(["  <UserControl.Resources>", '    <ResourceDictionary Source="Colors.xaml" />', "  </UserControl.Resources>"])
    lines.append("  <Canvas>")
    containers = listing.get("splitContainers") or []
    for ordinal, section in enumerate(sections):
        # Index by the section's real number: a partial selection (say sections 2 and 3)
        # must still take its own page offsets, not the first boxes in the list.
        index = section.get("_sectionIndex", ordinal)
        box = containers[index] if index < len(containers) and isinstance(containers[index], dict) else {}
        lines.append(f'    <Canvas Canvas.Left="{number(box.get("x", 0))}" Canvas.Top="{number(box.get("y", 0))}">')
        styles = section.get("styles") or {}
        order = [0]
        nodes = section.get("nodes") or []
        report["sections"].append({"index": index, "renderMode": "absolute"})
        for node in nodes:
            lines.extend(render_node(node, 3, "", len(nodes) > 1, styles, section, order, mapping, report))
        lines.append("    </Canvas>")
    lines.extend(["  </Canvas>", "</UserControl>", ""])
    return "\n".join(lines)


def build_report(mapping_error: str | None) -> dict[str, Any]:
    report: dict[str, Any] = {"sections": [], "tokenCoverage": {"mapped": 0, "literal": 0, "missing": []}, "componentMapping": [], "assets": {"icons": [], "images": []}, "fallbacks": [], "manualHandoffs": [], "unverified": ["visual validation was not executed"], "missingDimensions": [], "sectionsByNode": []}
    if mapping_error:
        report["fallbacks"].append({"nodeId": None, "reason": f"mapping disabled: {mapping_error}"})
    return report


def atomic_write_outputs(out_dir: Path, files: dict[str, str]) -> None:
    """Write a fully rendered output set only after all conversion validation succeeds."""
    parent = out_dir.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.", dir=parent))
    try:
        for name, content in files.items():
            (stage / name).write_text(content, encoding="utf-8")
        if not out_dir.exists():
            os.replace(stage, out_dir)
            return
        for name in files:
            os.replace(stage / name, out_dir / name)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert MasterGo section DSL into a WPF XAML page scaffold.")
    parser.add_argument("--input", required=True, metavar="PATH", help="directory of DSL JSON")
    parser.add_argument("--out", required=True, metavar="PATH", help="output directory")
    parser.add_argument("--page-name", default="GeneratedPage", help="generated page file name")
    parser.add_argument("--mapping", metavar="PATH", help="optional strict JSON project resource/component mapping")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        listing, sections = load_sections(Path(arguments.input))
        mapping, mapping_error = load_mapping(arguments.mapping)
        report = build_report(mapping_error)
        brushes = collect_brushes(sections, mapping, report)
        xaml = render_page(listing, sections, arguments.page_name, brushes, mapping, report)
        verify_texts(EMITTED_TEXTS, listing)
        # Icons and images are collected during rendering; files are prepared before any output directory is created.
        files = {f"{arguments.page_name}.xaml": xaml, "Colors.xaml": render_resources(brushes), "icons.json": json.dumps(report["assets"]["icons"], ensure_ascii=False, indent=2) + "\n", "images.json": json.dumps(report["assets"]["images"], ensure_ascii=False, indent=2) + "\n", "conversion-report.json": json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"}
        atomic_write_outputs(Path(arguments.out), files)
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
