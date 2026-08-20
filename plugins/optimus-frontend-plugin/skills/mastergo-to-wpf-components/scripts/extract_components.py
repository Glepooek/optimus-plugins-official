"""Extract reusable WPF visual components from MasterGo DSL JSON.

Pure function: no network, no MCP, no environment access beyond CLI args.
Reads section-*.json plus sections-list.json from --input, writes
components-index.json, Colors.generated.xaml and DataTemplates.generated.xaml
to --out.

Exit contract:
- 0: success; JSON report printed to stdout
- 2: hard error; single-line message on stderr, no stdout
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HEX_COLOUR = re.compile(r"^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
KEY_SUFFIX = re.compile(r"[/ -]+")


class ExtractionError(Exception):
    """Hard error that terminates with exit 2."""


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"cannot read {path}: {exc}") from exc


def numeric_section_paths(directory: Path) -> list[Path]:
    numbered_paths: list[tuple[int, Path]] = []
    for path in directory.glob("section-*.json"):
        match = re.fullmatch(r"section-(\d+)\.json", path.name)
        if not match:
            raise ExtractionError(f"invalid section file name: {path.name}")
        numbered_paths.append((int(match.group(1)), path))
    return [path for _, path in sorted(numbered_paths)]


def load_sections(directory: Path) -> list[dict]:
    listing_path = directory / "sections-list.json"
    if not listing_path.exists():
        raise ExtractionError("sections-list.json not found")
    listing = read_json(listing_path)
    if not isinstance(listing, dict):
        raise ExtractionError("sections-list.json must be a JSON object")
    if not isinstance(listing.get("rootMetadata"), dict):
        raise ExtractionError("sections-list.json missing rootMetadata")

    sections: list[dict] = []
    for path in numeric_section_paths(directory):
        payload = read_json(path)
        if not isinstance(payload, dict):
            raise ExtractionError(f"{path.name} must be a JSON object")
        if not isinstance(payload.get("nodes"), list):
            raise ExtractionError(f"{path.name} missing nodes array")
        sections.append(payload)
    if not sections:
        raise ExtractionError("no section-*.json files found")
    return sections


def walk(nodes: list) -> list[dict]:
    result: list[dict] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        result.append(node)
        children = node.get("children")
        if isinstance(children, list):
            result.extend(walk(children))
    return result


def resource_key(token: str) -> str:
    """Convert `Text/Text-4` to `TextText4`, matching dsl_to_xaml.py."""
    return KEY_SUFFIX.sub("", token)


def node_colour(node: dict, styles: dict) -> str | None:
    reference = node.get("fill")
    if isinstance(reference, str) and reference:
        entry = styles.get(reference)
        if not isinstance(entry, dict):
            raise ExtractionError(f"fill {reference!r} not in dsl.styles")
        values = entry.get("value")
        if isinstance(values, list) and values and isinstance(values[0], dict):
            value = values[0].get("color")
            if isinstance(value, str) and HEX_COLOUR.match(value.strip()):
                return value.strip()

    token = node.get("_token")
    if isinstance(token, str) and token:
        return None
    colour = node.get("_color")
    if isinstance(colour, str) and HEX_COLOUR.match(colour.strip()):
        return colour.strip()
    return None


def frame_signature(node: dict) -> tuple:
    return (
        node.get("type"),
        node.get("name"),
        node.get("_token"),
        node.get("_color"),
        len(node.get("children") or []),
    )


def load_mapping(path_value: str | None) -> dict:
    if not path_value:
        return {}
    mapping = read_json(Path(path_value))
    if not isinstance(mapping, dict):
        raise ExtractionError("mapping must be a JSON object")
    components = mapping.get("components")
    return components if isinstance(components, dict) else {}


def nodes_with_styles(sections: list[dict]) -> list[tuple[dict, dict]]:
    result: list[tuple[dict, dict]] = []
    for section in sections:
        styles = section.get("styles")
        if not isinstance(styles, dict):
            styles = {}
        for node in walk(section.get("nodes") or []):
            node_colour(node, styles)
            result.append((node, styles))
    return result


def build_component_index(sections: list[dict], mapping: dict) -> list[dict]:
    source_nodes = nodes_with_styles(sections)
    instance_names = Counter(
        node.get("name") for node, _ in source_nodes if node.get("type") == "INSTANCE"
    )
    frame_sigs = Counter(
        frame_signature(node)
        for node, _ in source_nodes
        if node.get("type") in ("FRAME", "GROUP")
    )

    index: list[dict] = []
    seen: set[str] = set()
    for node, styles in source_nodes:
        if node.get("type") == "INSTANCE":
            name = node.get("name")
            if not isinstance(name, str) or not name or name in seen:
                continue
            seen.add(name)
            if name in mapping:
                definition = mapping[name]
                index.append({
                    "key": name,
                    "kind": "control" if isinstance(definition, dict) and definition.get("control") else "style",
                    "source": [name],
                    "occurrences": instance_names[name],
                    "status": "mapped",
                    "resourceKey": name,
                })
                node_colour(node, styles)
            elif instance_names[name] >= 2:
                index.append({
                    "key": name,
                    "kind": "style",
                    "source": [name],
                    "occurrences": instance_names[name],
                    "status": "new",
                    "resourceKey": name,
                })
                node_colour(node, styles)
        elif node.get("type") in ("FRAME", "GROUP"):
            signature = frame_signature(node)
            if frame_sigs[signature] < 2:
                continue
            key = f"{node.get('type')}.{node.get('name')}"
            if key in seen:
                continue
            seen.add(key)
            index.append({
                "key": key,
                "kind": "datatemplate",
                "source": [node.get("name")],
                "occurrences": frame_sigs[signature],
                "status": "new",
                "resourceKey": key,
            })
            node_colour(node, styles)
    return index


def collect_tokens(sections: list[dict], index: list[dict]) -> dict[str, str]:
    keys = {item["resourceKey"] for item in index}
    tokens: dict[str, str] = {}
    for node, styles in nodes_with_styles(sections):
        node_key = (
            node.get("name")
            if node.get("type") == "INSTANCE"
            else f"{node.get('type')}.{node.get('name')}"
        )
        if node_key not in keys:
            continue
        token = node.get("_token")
        if isinstance(token, str) and token:
            tokens.setdefault(resource_key(token), node_colour(node, styles) or "#000000")
    return tokens


def xaml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_colors_xaml(tokens: dict[str, str]) -> str:
    lines = [
        '<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">',
    ]
    for key, colour in sorted(tokens.items()):
        lines.append(f'    <SolidColorBrush x:Key="{key}" Color="{colour}"/>')
    lines.append("</ResourceDictionary>")
    return "\n".join(lines) + "\n"


def render_data_templates_xaml(sections: list[dict], index: list[dict]) -> str:
    templates = {item["resourceKey"] for item in index if item["kind"] == "datatemplate"}
    lines = [
        '<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">',
    ]
    emitted: set[str] = set()
    for section in sections:
        for node in walk(section.get("nodes") or []):
            key = f"{node.get('type')}.{node.get('name')}"
            if key not in templates or key in emitted:
                continue
            emitted.add(key)
            labels = [
                child.get("name")
                for child in (node.get("children") or [])
                if isinstance(child, dict) and child.get("type") == "TEXT"
            ]
            lines.append(f'    <DataTemplate x:Key="{key}">')
            lines.append("        <Grid>")
            for label in labels[:6]:
                lines.append(f'            <TextBlock Text="{xaml_escape(str(label))}"/>')
            lines.append("        </Grid>")
            lines.append("    </DataTemplate>")
    lines.append("</ResourceDictionary>")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="directory with sections-list.json + section-*.json")
    parser.add_argument("--out", required=True, help="output directory for generated component library")
    parser.add_argument("--mapping", help="optional strict wpf-project-mapping.json path")
    args = parser.parse_args(argv)
    try:
        input_directory = Path(args.input)
        output_directory = Path(args.out)
        if not input_directory.is_dir():
            raise ExtractionError(f"input directory not found: {input_directory}")
        sections = load_sections(input_directory)
        mapping = load_mapping(args.mapping)
        index = build_component_index(sections, mapping)
        tokens = collect_tokens(sections, index)
        output_directory.mkdir(parents=True, exist_ok=True)
        (output_directory / "components-index.json").write_text(
            json.dumps({"version": 1, "components": index}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_directory / "Colors.generated.xaml").write_text(
            render_colors_xaml(tokens), encoding="utf-8"
        )
        (output_directory / "DataTemplates.generated.xaml").write_text(
            render_data_templates_xaml(sections, index), encoding="utf-8"
        )
        print(json.dumps({"extracted": len(index), "tokens": len(tokens)}, ensure_ascii=False))
        return 0
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
