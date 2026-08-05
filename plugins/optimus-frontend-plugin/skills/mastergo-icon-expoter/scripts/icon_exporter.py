"""Convert MasterGo icon export contract JSON into WPF-ready icon assets."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import Any


class ConversionError(Exception):
    """An input or conversion error that should be shown to the user."""


FILL_RULE_PREFIX = re.compile(r"\A(F0|F1)\s")
VALID_SOURCE_KINDS = {"vector", "bitmap", "fallback-png"}


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
            drawing_xaml = icon.get("drawingXaml")
            if drawing_xaml is not None:
                if paths:
                    raise ConversionError(f"{_icon_label(icon)}: drawingXaml and paths are mutually exclusive")
                if not isinstance(drawing_xaml, str) or not drawing_xaml.strip():
                    raise ConversionError(f"{_icon_label(icon)}: drawingXaml must be a non-empty DrawingGroup fragment")
                try:
                    drawing_root = ElementTree.fromstring(drawing_xaml)
                except ElementTree.ParseError as error:
                    raise ConversionError(f"{_icon_label(icon)}: drawingXaml is not valid XML: {error}") from error
                if drawing_root.tag.rsplit("}", 1)[-1] != "DrawingGroup":
                    raise ConversionError(f"{_icon_label(icon)}: drawingXaml root must be DrawingGroup")
                drawing_data = [node.attrib.get("Geometry", "") for node in drawing_root.iter() if node.tag.rsplit("}", 1)[-1] == "GeometryDrawing"]
                if not drawing_data:
                    raise ConversionError(f"{_icon_label(icon)}: drawingXaml contains no GeometryDrawing")
                if any(not FILL_RULE_PREFIX.match(data) for data in drawing_data):
                    raise ConversionError(f"{_icon_label(icon)}: drawingXaml Geometry attributes must retain literal F0/F1 prefixes")
            else:
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
        elif source_kind in {"bitmap", "fallback-png"}:
            if paths:
                raise ConversionError(f"{_icon_label(icon)}: sourceKind is {source_kind!r} but paths is non-empty")
            asset_field = "fallbackPngPath" if source_kind == "fallback-png" else "bitmapPath"
            if not isinstance(icon.get(asset_field), str) or not icon[asset_field].strip():
                raise ConversionError(f"{_icon_label(icon)}: sourceKind {source_kind!r} is missing {asset_field}")
            if source_kind == "fallback-png" and not isinstance(icon.get("fallbackReason"), str):
                raise ConversionError(f"{_icon_label(icon)}: fallback-png is missing fallbackReason")
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
    if icon.get("sourceKind") == "fallback-png":
        return "png", f"vector conversion fallback: {icon.get('fallbackReason')}"
    if icon.get("drawingXaml"):
        return "drawing-image", "svg-to-xaml-path DrawingGroup; includes vector gradient or parent coordinates"
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


def _escape_xml(value: str) -> str:
    return (
        str(value).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def render_icons_xaml(entries: list[dict[str, Any]]) -> str:
    """Assemble Icons.xaml: one Geometry per single-path entry, one DrawingImage per multi-path entry.

    PNG-format entries have no vector representation and are intentionally
    absent from this resource dictionary — they ship as loose files instead.
    """
    lines = [
        '<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">',
    ]
    for entry in entries:
        file_name = entry["fileName"]
        fmt = entry["format"]
        paths = entry.get("paths") or []
        if fmt == "path":
            key = resource_key(file_name, "Geometry")
            lines.append(f'  <Geometry x:Key="{key}">{_escape_xml(paths[0]["data"])}</Geometry>')
        elif fmt == "drawing-image":
            key = resource_key(file_name, "Image")
            lines.append(f'  <DrawingImage x:Key="{key}">')
            lines.append('    <DrawingImage.Drawing>')
            drawing_xaml = entry.get("drawingXaml")
            if drawing_xaml:
                lines.extend(f"      {line}" if line else "" for line in drawing_xaml.strip().splitlines())
            else:
                lines.append('      <DrawingGroup>')
                for path_entry in paths:
                    fill = _escape_xml(path_entry.get("fill") or "#000000")
                    data = _escape_xml(path_entry["data"])
                    lines.append(f'        <GeometryDrawing Brush="{fill}" Geometry="{data}" />')
                lines.append('      </DrawingGroup>')
            lines.append('    </DrawingImage.Drawing>')
            lines.append('  </DrawingImage>')
        # "png" entries carry no vector representation and are skipped here by design.
    lines.append("</ResourceDictionary>")
    return "\n".join(lines) + "\n"


def render_manifest(
    entries: list[dict[str, Any]],
    unnamed: list[dict[str, Any]],
    degraded: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the icons-manifest.json structure from named and needs-naming entries."""
    records: list[dict[str, Any]] = []
    for entry in entries:
        fmt = entry["format"]
        suffix = {"path": "Geometry", "drawing-image": "Image", "png": "Png"}[fmt]
        colour = None
        paths = entry.get("paths") or []
        if len(paths) == 1:
            colour = paths[0].get("fill")
        records.append({
            "svgShortKey": entry.get("svgShortKey"),
            "nodeId": entry.get("nodeId"),
            "name": entry.get("dslName"),
            "fileName": entry["fileName"],
            "resourceKey": resource_key(entry["fileName"], suffix) if fmt != "png" else None,
            "format": fmt,
            "decision": entry.get("decision", ""),
            "width": entry.get("width"),
            "height": entry.get("height"),
            "color": colour,
            "status": "exported",
            "reason": None,
            "fallbackFrom": "vector" if entry.get("sourceKind") == "fallback-png" else None,
            "fallbackReason": entry.get("fallbackReason") if entry.get("sourceKind") == "fallback-png" else None,
        })
    for icon in unnamed:
        records.append({
            "svgShortKey": icon.get("svgShortKey"),
            "nodeId": icon.get("nodeId"),
            "name": icon.get("dslName"),
            "fileName": None,
            "resourceKey": None,
            "format": "unresolved",
            "decision": None,
            "width": icon.get("width"),
            "height": icon.get("height"),
            "color": None,
            "status": "needs-manual",
            "reason": "could not derive a file name; needs a userName",
        })
    for icon in degraded or []:
        records.append({
            "svgShortKey": icon.get("svgShortKey"),
            "nodeId": icon.get("nodeId"),
            "name": icon.get("dslName"),
            "fileName": icon.get("fileName"),
            "resourceKey": None,
            "format": icon.get("format", "unresolved"),
            "decision": icon.get("decision"),
            "width": icon.get("width"),
            "height": icon.get("height"),
            "color": None,
            "status": "needs-manual",
            "reason": icon.get("reason") or "could not resolve source asset",
            "fallbackFrom": "vector" if icon.get("sourceKind") == "fallback-png" else None,
            "fallbackReason": icon.get("fallbackReason") if icon.get("sourceKind") == "fallback-png" else None,
        })
    return {"icons": records}


def merge_xaml_resources(new_xaml: str, existing_xaml: str) -> str:
    """Combine an existing Icons.xaml's resources with newly rendered ones.

    Only called after self_check has confirmed no x:Key collisions between
    new_xaml and existing_xaml, so this is always a safe non-colliding union.
    """
    def _inner(xaml: str) -> str:
        start = xaml.index(">", xaml.index("<ResourceDictionary")) + 1
        end = xaml.rindex("</ResourceDictionary>")
        return xaml[start:end].strip("\n")

    try:
        header_end = new_xaml.index(">", new_xaml.index("<ResourceDictionary")) + 1
        header = new_xaml[:header_end]
        parts = [part for part in (_inner(existing_xaml), _inner(new_xaml)) if part]
    except ValueError as error:
        raise ConversionError(f"existing Icons.xaml could not be parsed for merging: {error}") from error
    return header + "\n" + "\n".join(parts) + "\n</ResourceDictionary>\n"


_X_KEY = re.compile(r'x:Key="([^"]+)"')
_GEOMETRY_DATA = re.compile(r'<Geometry x:Key="([^"]+)">([^<]*)</Geometry>')
_GEOMETRY_DRAWING_DATA = re.compile(r'<GeometryDrawing[^>]* Geometry="([^"]*)"')


def self_check(
    icons_xaml: str,
    manifest: dict[str, Any],
    png_files: dict[str, bytes],
    existing_xaml: str | None,
) -> list[str]:
    """Check the about-to-be-written content for internal consistency.

    Every rule here maps to a named silent trap in the design doc; this
    function inspects in-memory content only and never touches disk.
    """
    violations: list[str] = []

    # Rule 1: every Geometry/GeometryDrawing Data must carry a literal F0/F1 prefix.
    for key, data in _GEOMETRY_DATA.findall(icons_xaml):
        if not FILL_RULE_PREFIX.match(data):
            violations.append(f"{key}: Data missing F0/F1 prefix")
    for data in _GEOMETRY_DRAWING_DATA.findall(icons_xaml):
        if not FILL_RULE_PREFIX.match(data):
            violations.append(f"GeometryDrawing Data missing F0/F1 prefix: {data[:40]!r}")

    # Rule 3: x:Key must be unique within the new file, and against an existing
    # file when mergeMode is "merge" (existing_xaml is only passed in that case).
    new_keys = _X_KEY.findall(icons_xaml)
    seen: set[str] = set()
    for key in new_keys:
        if key in seen:
            violations.append(f'duplicate x:Key "{key}" within the generated Icons.xaml')
        seen.add(key)
    if existing_xaml is not None:
        existing_keys = set(_X_KEY.findall(existing_xaml))
        for key in seen:
            if key in existing_keys:
                violations.append(f'duplicate x:Key "{key}" already present in the existing Icons.xaml')

    # Rule 4: every manifest resourceKey must correspond to a key actually in the XAML.
    xaml_keys = set(new_keys)
    for record in manifest.get("icons", []):
        resource_key_value = record.get("resourceKey")
        if resource_key_value and resource_key_value not in xaml_keys:
            violations.append(f"manifest references resourceKey {resource_key_value!r} not found in Icons.xaml")

    # Rule 5: needs-manual records must always carry a non-empty reason.
    for record in manifest.get("icons", []):
        if record.get("status") == "needs-manual" and not record.get("reason"):
            violations.append(f"{record.get('fileName') or record.get('nodeId')}: needs-manual record has no reason")

    # Rule 6: planned PNGs must have a determinate, positive width and height.
    def _is_positive_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0

    for record in manifest.get("icons", []):
        if (
            record.get("format") in {"png", "ico-fallback-png"}
            and record.get("fileName")
            and record.get("status") != "needs-manual"
        ):
            width, height = record.get("width"), record.get("height")
            if not _is_positive_number(width) or not _is_positive_number(height):
                violations.append(f"{record.get('fileName')}: width/height must be positive, got {width}x{height}")

    # Rule 7: an .ico that was downgraded to PNG fallback must never be reported as exported.
    for record in manifest.get("icons", []):
        if record.get("format") == "ico-fallback-png" and record.get("status") == "exported":
            violations.append(f"{record.get('fileName')}: ico fallback to PNG must be status=needs-manual, not exported")

    return violations


def synthesize_ico(png_frames: dict[int, bytes]) -> bytes | None:
    """Combine same-icon PNG frames into one .ico if Pillow is available, else None.

    Import is local and lazy: a user who never asks for .ico output must not
    need Pillow installed for the rest of the CLI to work.
    """
    try:
        import PIL  # noqa: F401
        from PIL import Image
        import io
    except ImportError:
        return None
    images = []
    for size in sorted(png_frames):
        images.append(Image.open(io.BytesIO(png_frames[size])))
    buffer = io.BytesIO()
    images[0].save(buffer, format="ICO", sizes=[(size, size) for size in sorted(png_frames)])
    return buffer.getvalue()


def atomic_write_outputs(out_dir: Path, files: dict[str, bytes | str]) -> None:
    """Write a fully rendered output set only after all validation succeeds."""
    parent = out_dir.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.", dir=parent))
    try:
        for name, content in files.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content, encoding="utf-8")
        if not out_dir.exists():
            os.replace(stage, out_dir)
            return
        for name in files:
            destination = out_dir / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage / name, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert MasterGo icon export contract JSON into WPF icon assets.")
    parser.add_argument("--input", required=True, metavar="PATH", help="path to input.json")
    parser.add_argument("--out", required=True, metavar="PATH", help="output directory")
    parser.add_argument("--source-root", metavar="PATH", help="base directory bitmapPath entries are relative to")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        payload = load_input(Path(arguments.input))
        icons = validate_contract(payload)
        meta = payload.get("meta") or {}
        merge_mode = meta.get("mergeMode", "separate")
        out_dir = Path(arguments.out)

        decided = []
        for icon in icons:
            fmt, decision = decide_format(icon)
            entry = dict(icon)
            entry["format"] = fmt
            entry["decision"] = decision
            decided.append(entry)

        named, unnamed = assign_names(decided)

        source_root = Path(arguments.source_root) if arguments.source_root else None
        resolved_named: list[dict[str, Any]] = []
        degraded: list[dict[str, Any]] = []
        png_files: dict[str, bytes] = {}
        for entry in named:
            if entry["format"] != "png":
                resolved_named.append(entry)
                continue
            asset_field = "fallbackPngPath" if entry.get("sourceKind") == "fallback-png" else "bitmapPath"
            bitmap_path = entry.get(asset_field)
            asset_kind = "PNG fallback" if entry.get("sourceKind") == "fallback-png" else "bitmap icon"
            if source_root is None:
                degraded.append({**entry, "reason": f"no --source-root provided for a {asset_kind}"})
                continue
            if not bitmap_path:
                degraded.append({**entry, "reason": f"{asset_field} is missing"})
                continue
            source_file = source_root / bitmap_path
            if not source_file.is_file():
                degraded.append({
                    **entry,
                    "reason": f"{asset_field} {bitmap_path!r} does not exist under --source-root",
                })
                continue
            png_files[f"Images/{entry['fileName']}.png"] = source_file.read_bytes()
            resolved_named.append(entry)

        icons_xaml = render_icons_xaml(resolved_named)
        manifest = render_manifest(resolved_named, unnamed, degraded)

        existing_xaml_path = out_dir / "Icons.xaml"
        existing_xaml_present = existing_xaml_path.is_file()
        if existing_xaml_present and merge_mode not in {"overwrite", "merge"}:
            raise ConversionError(
                f"{existing_xaml_path}: already exists; meta.mergeMode must be "
                "'overwrite' or 'merge' to proceed when an Icons.xaml already exists"
            )
        existing_xaml_text = existing_xaml_path.read_text(encoding="utf-8") if existing_xaml_present else None
        existing_xaml_for_check = existing_xaml_text if merge_mode == "merge" else None

        violations = self_check(icons_xaml, manifest, png_files, existing_xaml_for_check)
        if violations:
            raise ConversionError("self-check failed:\n  - " + "\n  - ".join(violations))

        final_xaml = icons_xaml
        if merge_mode == "merge" and existing_xaml_present:
            final_xaml = merge_xaml_resources(icons_xaml, existing_xaml_text)

        files: dict[str, bytes | str] = {
            "Icons.xaml": final_xaml,
            "icons-manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        }
        files.update(png_files)
        atomic_write_outputs(out_dir, files)
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
