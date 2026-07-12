#!/usr/bin/env python3
"""检测 docs/claude_docs/catalog.md 是否过期，并在用户确认后完成重新核对与合并写回。

子命令：
  check-freshness  判断距离上次核对是否已超过阈值天数
  record-check     记录一次询问/核对结果
  diff-catalog     对比旧 catalog.md 与新抓取到的候选文本，输出结构化差异
  apply-diff       把候选文本合并写回 catalog.md，尽量保留旧文件里的完成标记与批注
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from resolve_category import (
    CATALOG_PATH,
    GROUP_RE,
    MAP_PATH,
    PAGE_RE,
    TAB_RE,
    load_folder_map,
    parse_catalog,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
META_PATH = DATA_DIR / "catalog-check-meta.json"

HEADING2_RE = re.compile(r'^## ')
UNVERIFIED_RE = re.compile(r'^<!--\s*unverified:\s*(.*?)\s*-->\s*$')


# ---------- 通用工具 ----------

def load_meta(path):
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"错误：{path} 解析失败（{e}），文件可能损坏，不会自动覆盖", file=sys.stderr)
        sys.exit(2)


def save_meta(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def epoch_to_iso(epoch):
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(epoch).astimezone().isoformat(timespec="seconds")
    except (OSError, OverflowError, ValueError):
        # Windows 下对过早/异常的 epoch 值做本地时区换算会抛 OSError；
        # 这个字段只是人类可读的辅助展示，换算失败不应该让整条命令崩溃。
        return None


def flatten_synced_pages(folder_map):
    """把 folder-map.json 展平成 {url: fileId}，仅保留已有 fileId 的记录。"""
    result = {}
    for tab_entry in folder_map.get("tabs", {}).values():
        for group_entry in tab_entry.get("groups", {}).values():
            for url, page in group_entry.get("pages", {}).items():
                file_id = page.get("fileId")
                if file_id:
                    result[url] = file_id
    return result


def find_unverified_tabs(text):
    """扫描文本，找出紧跟在 Tab 标题行后带 <!-- unverified: ... --> 标记的 Tab。"""
    lines = text.splitlines()
    unverified = {}
    for i, line in enumerate(lines):
        m = TAB_RE.match(line)
        if m and i + 1 < len(lines):
            um = UNVERIFIED_RE.match(lines[i + 1])
            if um:
                unverified[m.group(1).strip()] = um.group(1)
    return unverified


def locate_tab_blocks(lines):
    """定位每个 Tab 区块的起止行号。区块结束于下一个二级标题（不论是不是 Tab），
    这样能把 Tab 内部的自由文本（批注、分隔线）和文件末尾的非 Tab 章节正确划出边界。
    返回 (leading_end, blocks, trailing_start)。
    """
    heading2_idxs = [i for i, l in enumerate(lines) if HEADING2_RE.match(l)]
    if not heading2_idxs:
        return len(lines), [], len(lines)
    leading_end = heading2_idxs[0]
    tab_positions = [i for i in heading2_idxs if TAB_RE.match(lines[i])]
    blocks = []
    for start in tab_positions:
        later = [i for i in heading2_idxs if i > start]
        end = later[0] if later else len(lines)
        tab_en = TAB_RE.match(lines[start]).group(1).strip()
        blocks.append({"tab_en": tab_en, "start": start, "end": end})
    trailing_start = blocks[-1]["end"] if blocks else heading2_idxs[0]
    return leading_end, blocks, trailing_start


def scan_tab_block(lines, start, end):
    """扫描单个 Tab 区块，记录每个分组标题行、每篇页面行在原文件中的行号。"""
    groups = []
    current = None
    for i in range(start + 1, end):
        line = lines[i]
        gm = GROUP_RE.match(line)
        if gm:
            current = {"group_en": gm.group(1).strip(), "header_idx": i, "page_idxs": {}}
            groups.append(current)
            continue
        pm = PAGE_RE.match(line)
        if pm and current is not None:
            current["page_idxs"][pm.group(3)] = i
    return {"header_idx": start, "groups": groups}


def build_index(tabs):
    """把 parse_catalog 的结果按 (tab_en, url) 建索引，供 diff 使用。"""
    idx = {}
    tab_names = set()
    group_index = {}
    for tab in tabs:
        tab_en = tab["en"]
        tab_names.add(tab_en)
        group_index.setdefault(tab_en, set())
        for group in tab["groups"]:
            group_en = group["en"]
            group_index[tab_en].add(group_en)
            for page in group["pages"]:
                idx[(tab_en, page["url"])] = {
                    "tab": tab_en, "group": group_en,
                    "title": page["title"], "url": page["url"],
                }
    return idx, tab_names, group_index


# ---------- check-freshness ----------

def compute_freshness(meta, now, threshold_days):
    """纯函数：根据 meta 状态 + 当前时间 + 阈值天数，判定是否需要询问用户。"""
    last_verified = meta.get("last_verified_epoch")
    last_prompted = meta.get("last_prompted_epoch")
    unverified_tabs = meta.get("unverified_tabs", [])

    if last_prompted is not None and (now - last_prompted) < 86400:
        status = "recently_prompted"
    elif last_verified is None:
        status = "never_checked"
    elif (now - last_verified) >= threshold_days * 86400:
        status = "stale"
    else:
        status = "fresh"

    days_since_verified = (
        int((now - last_verified) // 86400) if last_verified is not None else None
    )

    return {
        "status": status,
        "last_verified_epoch": last_verified,
        "last_verified_at": epoch_to_iso(last_verified),
        "last_prompted_epoch": last_prompted,
        "last_prompted_at": epoch_to_iso(last_prompted),
        "days_since_verified": days_since_verified,
        "threshold_days": threshold_days,
        "unverified_tabs": unverified_tabs,
    }


def cmd_check_freshness(args):
    now = args.now_epoch if args.now_epoch is not None else time.time()
    meta = load_meta(META_PATH)
    result = compute_freshness(meta, now, args.threshold_days)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["status"] in ("fresh", "recently_prompted") else 1)


# ---------- record-check ----------

def apply_record_check(meta, result, unverified_tabs, now):
    """纯函数：返回更新后的 meta（不做文件 IO）。"""
    meta = dict(meta)
    meta["last_prompted_epoch"] = now
    meta["last_prompted_at"] = epoch_to_iso(now)
    meta["last_prompt_response"] = result
    if unverified_tabs is not None:
        meta["unverified_tabs"] = unverified_tabs
    if result == "verified":
        meta["last_verified_epoch"] = now
        meta["last_verified_at"] = epoch_to_iso(now)
    return meta


def cmd_record_check(args):
    now = args.now_epoch if args.now_epoch is not None else time.time()
    meta = load_meta(META_PATH)
    unverified_tabs = None
    if args.unverified_tabs is not None:
        unverified_tabs = [t.strip() for t in args.unverified_tabs.split(",") if t.strip()]
    meta = apply_record_check(meta, args.result, unverified_tabs, now)
    save_meta(META_PATH, meta)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


# ---------- diff-catalog ----------

def compute_diff(old_text, new_text, synced_pages):
    """纯函数：对比新旧 catalog 文本，返回结构化差异（不做文件 IO）。
    synced_pages: {url: fileId}，来自 flatten_synced_pages(load_folder_map(...))。
    """
    unverified = find_unverified_tabs(new_text)

    new_tabs_all = parse_catalog(new_text)
    if len(new_tabs_all) == 0:
        raise ValueError("--new 内容解析出 0 个 Tab，抓取内容可能异常")
    old_tabs_all = parse_catalog(old_text)

    old_tabs = [t for t in old_tabs_all if t["en"] not in unverified]
    new_tabs = [t for t in new_tabs_all if t["en"] not in unverified]

    old_idx, old_tab_names, old_group_idx = build_index(old_tabs)
    new_idx, new_tab_names, new_group_idx = build_index(new_tabs)

    tabs_added = sorted(new_tab_names - old_tab_names)
    tabs_removed = sorted(old_tab_names - new_tab_names)

    groups_added = []
    groups_removed = []
    for tab_en in sorted(old_tab_names & new_tab_names):
        old_groups = old_group_idx.get(tab_en, set())
        new_groups = new_group_idx.get(tab_en, set())
        for g in sorted(new_groups - old_groups):
            groups_added.append({"tab": tab_en, "group": g})
        for g in sorted(old_groups - new_groups):
            groups_removed.append({"tab": tab_en, "group": g})

    old_keys = set(old_idx)
    new_keys = set(new_idx)

    pages_added = []
    for key in sorted(new_keys - old_keys):
        e = new_idx[key]
        pages_added.append({"tab": e["tab"], "group": e["group"], "title": e["title"], "url": e["url"]})

    pages_removed = []
    for key in sorted(old_keys - new_keys):
        e = old_idx[key]
        item = {"tab": e["tab"], "group": e["group"], "title": e["title"], "url": e["url"]}
        file_id = synced_pages.get(e["url"])
        item["had_synced_record"] = file_id is not None
        if file_id is not None:
            item["synced_file_id"] = file_id
        pages_removed.append(item)

    pages_moved = []
    pages_retitled = []
    for key in sorted(old_keys & new_keys):
        old_e = old_idx[key]
        new_e = new_idx[key]
        if old_e["group"] != new_e["group"]:
            pages_moved.append({
                "url": key[1], "title": new_e["title"],
                "from": {"tab": old_e["tab"], "group": old_e["group"]},
                "to": {"tab": new_e["tab"], "group": new_e["group"]},
            })
        elif old_e["title"] != new_e["title"]:
            pages_retitled.append({
                "url": key[1], "old_title": old_e["title"], "new_title": new_e["title"],
                "tab": new_e["tab"], "group": new_e["group"],
            })

    has_changes = any([
        tabs_added, tabs_removed, groups_added, groups_removed,
        pages_added, pages_removed, pages_moved, pages_retitled,
    ])

    return {
        "has_changes": has_changes,
        "tabs_added": tabs_added,
        "tabs_removed": tabs_removed,
        "tabs_skipped_unverified": sorted(unverified.keys()),
        "groups_added": groups_added,
        "groups_removed": groups_removed,
        "pages_added": pages_added,
        "pages_removed": pages_removed,
        "pages_moved": pages_moved,
        "pages_retitled": pages_retitled,
    }


def cmd_diff_catalog(args):
    old_text = Path(args.old).read_text(encoding="utf-8")
    new_text = Path(args.new).read_text(encoding="utf-8")
    folder_map = load_folder_map(MAP_PATH)
    synced = flatten_synced_pages(folder_map)
    try:
        result = compute_diff(old_text, new_text, synced)
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if result["has_changes"] else 0)


# ---------- apply-diff ----------

def build_tab_patch(old_lines, old_scan, new_tab):
    """就地修正 old_lines 中需要改标题的行；返回 (delete_idxs, insertions)。

    核心原则：不做"parse → 重新序列化"，只在 (1) 页面被删除 (2) 页面跨组搬家
    (3) 标题文字变化 (4) 分组/页面全新出现 这四种情况下才触碰具体的行，
    其余内容（[x]/[ ] 状态、行尾批注、分组标题的括注文字）原样保留。
    """
    delete_idxs = set()
    insertions = {}

    def queue(anchor, line):
        insertions.setdefault(anchor, []).append(line)

    old_group_by_name = {g["group_en"]: g for g in old_scan["groups"]}
    new_group_names = {g["en"] for g in new_tab["groups"]}

    old_page_idx = {}
    for g in old_scan["groups"]:
        for url, idx in g["page_idxs"].items():
            old_page_idx[url] = (g["group_en"], idx)

    def line_with_title(idx, new_title):
        line = old_lines[idx]
        m = PAGE_RE.match(line)
        if m.group(2) == new_title:
            return line
        return line[:m.start(2)] + new_title + line[m.end(2):]

    to_insert_by_group = {}
    new_urls_seen = set()

    for g in new_tab["groups"]:
        group_en = g["en"]
        for p in g["pages"]:
            url = p["url"]
            new_urls_seen.add(url)
            if url in old_page_idx:
                old_group_en, old_idx = old_page_idx[url]
                patched = line_with_title(old_idx, p["title"])
                if old_group_en == group_en:
                    if patched != old_lines[old_idx]:
                        old_lines[old_idx] = patched
                else:
                    delete_idxs.add(old_idx)
                    to_insert_by_group.setdefault(group_en, []).append(patched)
            else:
                to_insert_by_group.setdefault(group_en, []).append(
                    f"- [ ] {p['title']} — `{url}`"
                )

    # 旧有新无的页面 → 删除
    for url, (group_en, idx) in old_page_idx.items():
        if url not in new_urls_seen:
            delete_idxs.add(idx)

    # 旧有新无的组 → 整组删除（含标题行和仍残留的页面行）
    for group_en, g in old_group_by_name.items():
        if group_en not in new_group_names:
            delete_idxs.add(g["header_idx"])
            for idx in g["page_idxs"].values():
                delete_idxs.add(idx)
            to_insert_by_group.pop(group_en, None)

    # 已存在的组：把待插入页面挂到该组现存未删除内容的最后一行之后
    for group_en, g in old_group_by_name.items():
        if group_en not in new_group_names:
            continue
        pending = to_insert_by_group.pop(group_en, None)
        if not pending:
            continue
        remaining_idxs = [idx for idx in g["page_idxs"].values() if idx not in delete_idxs]
        anchor = max(remaining_idxs) if remaining_idxs else g["header_idx"]
        for line in pending:
            queue(anchor, line)

    # 全新出现的组：整组（标题+页面）打包插在这个 Tab 已有内容的最后一行之后
    if to_insert_by_group:
        all_old_idxs = [old_scan["header_idx"]]
        for g in old_scan["groups"]:
            all_old_idxs.append(g["header_idx"])
            all_old_idxs.extend(g["page_idxs"].values())
        tab_end_anchor = max(all_old_idxs)
        for g in new_tab["groups"]:
            group_en = g["en"]
            if group_en not in to_insert_by_group:
                continue
            pending = to_insert_by_group.pop(group_en)
            queue(tab_end_anchor, f"### {group_en}")
            for line in pending:
                queue(tab_end_anchor, line)

    return delete_idxs, insertions


def reconstruct(old_lines, leading_end, blocks, trailing_start,
                 tabs_added_chunks, per_tab_patches, tabs_removed_set):
    delete_idxs = set()
    insertions = {}
    for block in blocks:
        tab_en = block["tab_en"]
        if tab_en in tabs_removed_set:
            for i in range(block["start"], block["end"]):
                delete_idxs.add(i)
            continue
        if tab_en in per_tab_patches:
            d, ins = per_tab_patches[tab_en]
            delete_idxs |= d
            for k, v in ins.items():
                insertions.setdefault(k, []).extend(v)

    out = list(old_lines[:leading_end])
    for i in range(leading_end, trailing_start):
        if i not in delete_idxs:
            out.append(old_lines[i])
        # 插入内容不依赖锚点本身是否被删除，避免锚点恰好是被删除的行时插入丢失
        if i in insertions:
            out.extend(insertions[i])
    for chunk in tabs_added_chunks:
        out.extend(chunk)
    out.extend(old_lines[trailing_start:])
    return out


def compute_apply(old_text, new_text):
    """纯函数：合并新旧 catalog 文本，返回 (合并后完整文本, summary dict)。不做文件 IO。"""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    new_tabs_all = parse_catalog(new_text)
    if len(new_tabs_all) == 0:
        raise ValueError("--new 内容解析出 0 个 Tab，拒绝写入")
    unverified = find_unverified_tabs(new_text)

    old_leading_end, old_blocks, old_trailing_start = locate_tab_blocks(old_lines)
    _, new_blocks, _ = locate_tab_blocks(new_lines)
    new_blocks_by_name = {b["tab_en"]: b for b in new_blocks}

    old_tab_names = {b["tab_en"] for b in old_blocks}
    new_tab_names = {t["en"] for t in new_tabs_all}
    new_tabs_by_name = {t["en"]: t for t in new_tabs_all}

    tabs_removed_set = old_tab_names - new_tab_names - set(unverified.keys())
    tabs_added_names = new_tab_names - old_tab_names

    per_tab_patches = {}
    for block in old_blocks:
        tab_en = block["tab_en"]
        if tab_en in unverified or tab_en not in new_tabs_by_name:
            continue
        old_scan = scan_tab_block(old_lines, block["start"], block["end"])
        per_tab_patches[tab_en] = build_tab_patch(old_lines, old_scan, new_tabs_by_name[tab_en])

    tabs_added_chunks = []
    for name in sorted(tabs_added_names):
        nb = new_blocks_by_name.get(name)
        if nb is not None:
            tabs_added_chunks.append(new_lines[nb["start"]:nb["end"]])

    result_lines = reconstruct(
        old_lines, old_leading_end, old_blocks, old_trailing_start,
        tabs_added_chunks, per_tab_patches, tabs_removed_set,
    )

    summary = {
        "tabs_added": sorted(tabs_added_names),
        "tabs_removed": sorted(tabs_removed_set),
        "tabs_skipped_unverified": sorted(unverified.keys()),
        "tabs_touched": sorted(per_tab_patches.keys()),
    }
    return "\n".join(result_lines) + "\n", summary


def cmd_apply_diff(args):
    old_path = Path(args.old)
    new_path = Path(args.new)
    if not new_path.exists():
        print(f"错误：--new 文件不存在：{new_path}", file=sys.stderr)
        sys.exit(2)
    if not old_path.exists():
        print(f"错误：--old 文件不存在：{old_path}", file=sys.stderr)
        sys.exit(2)
    if not args.write:
        print("错误：必须显式传入 --write 才会真正写入文件（防止误触发覆写）", file=sys.stderr)
        sys.exit(2)

    old_text = old_path.read_text(encoding="utf-8")
    new_text = new_path.read_text(encoding="utf-8")
    try:
        merged_text, summary = compute_apply(old_text, new_text)
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(2)

    tmp_path = old_path.with_name(old_path.name + ".tmp")
    tmp_path.write_text(merged_text, encoding="utf-8")
    os.replace(tmp_path, old_path)

    summary["written"] = True
    print(json.dumps(summary, ensure_ascii=False, indent=2))


# ---------- CLI ----------

def build_parser():
    parser = argparse.ArgumentParser(prog="catalog_freshness.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check-freshness", help="判断 catalog.md 是否需要重新核对")
    p_check.add_argument("--threshold-days", type=int, default=14)
    p_check.add_argument("--now-epoch", type=float, default=None)

    p_record = sub.add_parser("record-check", help="记录一次询问/核对结果")
    p_record.add_argument("--result", required=True, choices=["verified", "declined", "failed"])
    p_record.add_argument("--unverified-tabs", default=None)
    p_record.add_argument("--now-epoch", type=float, default=None)

    p_diff = sub.add_parser("diff-catalog", help="对比新旧导航结构")
    p_diff.add_argument("--new", required=True)
    p_diff.add_argument("--old", default=str(CATALOG_PATH))

    p_apply = sub.add_parser("apply-diff", help="合并写回 catalog.md")
    p_apply.add_argument("--new", required=True)
    p_apply.add_argument("--old", default=str(CATALOG_PATH))
    p_apply.add_argument("--write", action="store_true")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "check-freshness":
        cmd_check_freshness(args)
    elif args.command == "record-check":
        cmd_record_check(args)
    elif args.command == "diff-catalog":
        cmd_diff_catalog(args)
    elif args.command == "apply-diff":
        cmd_apply_diff(args)


if __name__ == "__main__":
    main()
