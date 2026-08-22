#!/usr/bin/env python3
"""校验 knowledge-base/<domain>/index.jsonl 与实际文件的一致性。

三类检查：file 是否存在、anchor 对应标题是否存在、id 是否全局唯一。
用法：python check_index.py [domain ...]（无参数时扫描所有含 index.jsonl 的子目录）
"""
import json
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')


def normalize_heading(line):
    m = HEADING_RE.match(line.strip())
    text = m.group(2) if m else line.strip()
    text = text.replace("`", "")
    return re.sub(r'\s+', ' ', text).strip()


def find_headings(text):
    headings = []
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            headings.append(normalize_heading(line))
    return headings


def parse_index_file(path):
    entries = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{line_no}: JSON 解析失败：{e}")
    return entries


def check_file_exists(domain_dir, entry):
    target = domain_dir / entry["file"]
    if not target.exists():
        return f"[{entry['id']}] file 不存在：{entry['file']}"
    return None


def check_anchor_exists(domain_dir, entry):
    anchor = entry.get("anchor", "")
    if not anchor:
        return None
    target = domain_dir / entry["file"]
    if not target.exists():
        return None  # file 缺失已由 check_file_exists 报告，避免重复问题
    headings = find_headings(target.read_text(encoding="utf-8"))
    if not any(anchor in h for h in headings):
        return f"[{entry['id']}] anchor 未在 {entry['file']} 中找到匹配标题：{anchor}"
    return None


def check_duplicate_ids(domain_entries):
    seen = {}
    problems = []
    for domain, entries in domain_entries.items():
        for entry in entries:
            entry_id = entry["id"]
            if entry_id in seen:
                problems.append(f"重复 id：{entry_id}（{seen[entry_id]} 与 {domain}）")
            else:
                seen[entry_id] = domain
    return problems


def run_checks(base_dir, domains):
    domain_entries = {}
    problems = []
    for domain in domains:
        domain_dir = base_dir / domain
        index_path = domain_dir / "index.jsonl"
        if not index_path.exists():
            problems.append(f"[{domain}] index.jsonl 不存在：{index_path}")
            continue
        entries = parse_index_file(index_path)
        domain_entries[domain] = entries
        for entry in entries:
            for check in (check_file_exists, check_anchor_exists):
                result = check(domain_dir, entry)
                if result:
                    problems.append(f"[{domain}] {result}")
    problems.extend(check_duplicate_ids(domain_entries))
    return problems


def main():
    base_dir = Path(__file__).resolve().parent
    domains = sys.argv[1:]
    if not domains:
        domains = sorted(
            p.name for p in base_dir.iterdir()
            if p.is_dir() and (p / "index.jsonl").exists()
        )
    problems = run_checks(base_dir, domains)
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        sys.exit(1)
    total = sum(
        len(parse_index_file(base_dir / d / "index.jsonl"))
        for d in domains if (base_dir / d / "index.jsonl").exists()
    )
    print(f"OK: 共检查 {total} 条记录，未发现问题")
    sys.exit(0)


if __name__ == "__main__":
    main()
