"""Match MasterGo DSL nodes against a WPF component library index.

Exit contract: 0 writes a report and JSON summary; 2 writes one error line to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class MatchError(Exception):
    """Hard error that terminates with exit 2."""


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MatchError(f"cannot read {path}: {exc}") from exc


def load_index(path: Path) -> dict[str, str]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise MatchError("components-index.json must be a JSON object")
    components = payload.get("components")
    if not isinstance(components, list):
        raise MatchError("components-index.json components must be an array")
    keys: dict[str, str] = {}
    for item in components:
        if not isinstance(item, dict):
            raise MatchError("components-index.json entry must be an object")
        key = item.get("resourceKey")
        if isinstance(key, str) and key:
            keys[key] = item.get("kind", "style")
    return keys


def walk(nodes: list) -> list[dict]:
    result: list[dict] = []
    for node in nodes:
        if isinstance(node, dict):
            result.append(node)
            if isinstance(node.get("children"), list):
                result.extend(walk(node["children"]))
    return result


def load_sections(directory: Path) -> list[dict]:
    paths = sorted(directory.glob("section-*.json"), key=lambda path: int(path.stem.split("-")[1]))
    if not paths:
        raise MatchError("no section-*.json files found")
    sections: list[dict] = []
    for path in paths:
        payload = read_json(path)
        if not isinstance(payload, dict) or not isinstance(payload.get("nodes"), list):
            raise MatchError(f"{path.name} missing nodes array")
        sections.append(payload)
    return sections


def match(sections: list[dict], index_keys: dict[str, str]) -> tuple[list[dict], list[dict]]:
    matches: list[dict] = []
    missing: list[dict] = []
    for section in sections:
        for node in walk(section["nodes"]):
            node_type, name = node.get("type"), node.get("name")
            if not isinstance(name, str) or not name:
                continue
            candidate = name if node_type == "INSTANCE" else f"{node_type}.{name}"
            if node_type in ("INSTANCE", "FRAME", "GROUP") and candidate in index_keys:
                matches.append({"nodeId": node.get("id"), "nodeName": name, "resourceKey": candidate, "kind": index_keys[candidate]})
            elif node_type == "INSTANCE":
                missing.append({"nodeId": node.get("id"), "nodeName": name, "reason": "未在组件库注册的实例"})
    return matches, missing


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        input_directory = Path(args.input)
        if not input_directory.is_dir():
            raise MatchError(f"input directory not found: {input_directory}")
        matches, missing = match(load_sections(input_directory), load_index(Path(args.index)))
        output_directory = Path(args.out)
        output_directory.mkdir(parents=True, exist_ok=True)
        (output_directory / "component-match-report.json").write_text(json.dumps({"matches": matches, "missing": missing}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"matched": len(matches), "missing": len(missing)}, ensure_ascii=False))
        return 0
    except MatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
