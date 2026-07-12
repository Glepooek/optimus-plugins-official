#!/usr/bin/env python3
"""解析 docs/claude_docs/catalog.md 的分类结构，维护有道云笔记文件夹映射。"""
import difflib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = REPO_ROOT / "docs" / "claude_docs" / "catalog.md"
MAP_PATH = Path(__file__).resolve().parent.parent / "data" / "folder-map.json"
ROOT_FOLDER_ID = "WEBc1d2e6c709ed0850b09f070a86573197"

TAB_RE = re.compile(
    r'^## Tab \d+ — (.+?)（(?:对应有道笔记"(.+?)"，)?入口：`([^`]+)`）\s*$'
)
GROUP_RE = re.compile(r'^### ([^（]+?)\s*(?:（.*)?$')
PAGE_RE = re.compile(r'^- \[([ x])\] (.+?) — `([^`]+)`')


def parse_catalog(text):
    """解析 catalog.md 文本，返回 Tab 列表，每个 Tab 含 groups，每个 group 含 pages。"""
    tabs = []
    current_tab = None
    current_group = None
    for line in text.splitlines():
        m = TAB_RE.match(line)
        if m:
            current_tab = {"en": m.group(1).strip(), "zh": m.group(2), "groups": []}
            tabs.append(current_tab)
            current_group = None
            continue
        m = GROUP_RE.match(line)
        if m and current_tab is not None:
            current_group = {"en": m.group(1).strip(), "pages": []}
            current_tab["groups"].append(current_group)
            continue
        m = PAGE_RE.match(line)
        if m and current_group is not None:
            current_group["pages"].append(
                {"title": m.group(2).strip(), "url": m.group(3).strip()}
            )
            continue
    return tabs


def find_tab(tabs, folder_map, name):
    """按英文名、catalog.md 标注的中文名，或 folder-map.json 记录的中文别名查找 Tab。"""
    name = name.strip()
    for tab in tabs:
        if tab["en"].lower() == name.lower():
            return tab
        if tab["zh"] and tab["zh"] == name:
            return tab
    for zh_key, entry in folder_map.get("tabs", {}).items():
        if zh_key == name or entry.get("en", "").lower() == name.lower():
            target_en = entry.get("en", zh_key)
            for tab in tabs:
                if tab["en"].lower() == target_en.lower():
                    return tab
    return None


def find_group(tab, name):
    """按英文名查找 Tab 下的分组（大小写不敏感）。"""
    name = name.strip()
    for group in tab["groups"]:
        if group["en"].lower() == name.lower():
            return group
    return None


def tab_candidate_names(tabs, folder_map):
    """汇总所有可能被用户提及的 Tab 名称（英文名/catalog.md 中文标注/folder-map 别名），供模糊匹配用。"""
    names = []
    for tab in tabs:
        names.append(tab["en"])
        if tab["zh"]:
            names.append(tab["zh"])
    for zh_key in folder_map.get("tabs", {}):
        names.append(zh_key)
    seen = set()
    deduped = []
    for name in names:
        if name not in seen:
            seen.add(name)
            deduped.append(name)
    return deduped


def suggest_names(name, candidates, n=3, cutoff=0.4):
    """返回与 name 最接近的候选名（编辑距离），找不到已知匹配时用来提示用户，而不是让用户
    自己回 catalog.md 逐字核对拼写。"""
    return difflib.get_close_matches(name, candidates, n=n, cutoff=cutoff)


import argparse
import subprocess


def load_folder_map(path):
    if not path.exists():
        return {"tabs": {}}
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"错误：{path} 解析失败（{e}），文件可能损坏，不会自动覆盖", file=sys.stderr)
        sys.exit(1)


def save_folder_map(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_youdaonote(args_list, retries=1):
    last_err = None
    for _ in range(retries + 1):
        try:
            return subprocess.run(
                ["youdaonote", "-s", "ydn", *args_list],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
        except subprocess.CalledProcessError as e:
            last_err = e
    raise last_err


def youdaonote_list(folder_id):
    result = run_youdaonote(["list", "-f", folder_id])
    entries = []
    for line in result.stdout.splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("📁"):
            kind = "folder"
        elif line.startswith("📄"):
            kind = "note"
        else:
            continue
        rest = line[1:].strip()
        parts = rest.split("\t", 1)
        if len(parts) != 2:
            continue
        entries.append((kind, parts[0].strip(), parts[1].strip()))
    return entries


def youdaonote_mkdir(name, parent_id):
    run_youdaonote(["mkdir", name, "-f", parent_id])


def ensure_folder(name, parent_id):
    """先查父目录下是否已有同名文件夹，没有才创建，创建后重新查一次确认。"""
    for kind, entry_id, entry_name in youdaonote_list(parent_id):
        if kind == "folder" and entry_name == name:
            return entry_id
    youdaonote_mkdir(name, parent_id)
    for kind, entry_id, entry_name in youdaonote_list(parent_id):
        if kind == "folder" and entry_name == name:
            return entry_id
    raise RuntimeError(f"创建文件夹 {name!r} 后仍未在父目录 {parent_id} 下找到，mkdir 可能失败")


def cmd_resolve(args):
    catalog_text = CATALOG_PATH.read_text(encoding="utf-8")
    tabs = parse_catalog(catalog_text)
    folder_map = load_folder_map(MAP_PATH)

    tab = find_tab(tabs, folder_map, args.tab)
    if tab is None:
        msg = f"错误：未在 catalog.md 中找到 Tab {args.tab!r}"
        suggestions = suggest_names(args.tab, tab_candidate_names(tabs, folder_map))
        if suggestions:
            msg += f"\n你是不是想找：{' / '.join(suggestions)}？"
        print(msg, file=sys.stderr)
        sys.exit(1)

    group = find_group(tab, args.group)
    if group is None:
        msg = f"错误：未在 Tab {tab['en']!r} 下找到分组 {args.group!r}"
        suggestions = suggest_names(args.group, [g["en"] for g in tab["groups"]])
        if suggestions:
            msg += f"\n你是不是想找：{' / '.join(suggestions)}？"
        print(msg, file=sys.stderr)
        sys.exit(1)

    print(json.dumps(
        {"tab_en": tab["en"], "tab_zh": tab["zh"], "group_en": group["en"], "pages": group["pages"]},
        ensure_ascii=False,
        indent=2,
    ))


def cmd_get_folder(args):
    folder_map = load_folder_map(MAP_PATH)
    tabs_map = folder_map.setdefault("tabs", {})

    tab_entry = tabs_map.get(args.tab_zh)
    if tab_entry is None:
        tab_id = ensure_folder(args.tab_zh, ROOT_FOLDER_ID)
        tab_entry = {"en": args.tab_zh, "id": tab_id, "groups": {}}
        tabs_map[args.tab_zh] = tab_entry
        save_folder_map(MAP_PATH, folder_map)

    groups_map = tab_entry.setdefault("groups", {})
    group_entry = groups_map.get(args.group_en)
    if group_entry is None:
        if not args.group_zh:
            print(f"错误：分组 {args.group_en!r} 尚无中文名记录，必须提供 --group-zh", file=sys.stderr)
            sys.exit(1)
        group_id = ensure_folder(args.group_zh, tab_entry["id"])
        group_entry = {"en": args.group_en, "zh": args.group_zh, "id": group_id, "pages": {}}
        groups_map[args.group_en] = group_entry
        save_folder_map(MAP_PATH, folder_map)

    print(group_entry["id"])


def build_parser():
    parser = argparse.ArgumentParser(prog="resolve_category.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="解析分类下的页面清单")
    p_resolve.add_argument("tab")
    p_resolve.add_argument("group")

    p_folder = sub.add_parser("get-folder", help="查询/创建有道文件夹")
    p_folder.add_argument("tab_zh")
    p_folder.add_argument("group_en")
    p_folder.add_argument("--group-zh")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "resolve":
        cmd_resolve(args)
    elif args.command == "get-folder":
        cmd_get_folder(args)


if __name__ == "__main__":
    main()
