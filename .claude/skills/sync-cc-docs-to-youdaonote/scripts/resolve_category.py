#!/usr/bin/env python3
"""解析 docs/claude_docs/catalog.md 的分类结构，维护有道云笔记文件夹映射。"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = REPO_ROOT / "docs" / "claude_docs" / "catalog.md"
MAP_PATH = Path(__file__).resolve().parent.parent / "folder-map.json"
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


if __name__ == "__main__":
    pass
