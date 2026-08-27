#!/usr/bin/env python3
"""校验 knowledge-base/<domain>/index.jsonl 与实际文件的一致性。

两类作用域：
- **单领域检查**（传入 domain 参数）：负责该领域的 file 存在、anchor 匹配、schema、枚举、路径越界、孤儿文件。
- **全局检查**（始终执行）：id 全局唯一、id 前缀与领域归属一致、领域目录清单——
  即使只指定单个领域，也会读取全部领域索引来判定 id 冲突，避免"单领域通过、跨领域重复"。

用法：
    python check_index.py [domain ...]      # 无参数时扫描所有含 index.jsonl 的子目录
    python check_index.py --audit [domain ...]   # 额外输出健康报告（记录数、级别分布、覆盖率）

脚本随 knowledge-base-maintain skill 存放于 .claude/skills/knowledge-base-maintain/scripts/ 下，
运行时自动以仓库根的 knowledge-base/ 为基准目录。
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')
ID_RE = re.compile(r'^[a-z0-9-]+\.(?:\d{2}|ref)\.[a-z0-9-]+$')

REQUIRED_FIELDS = ("id", "kind", "file", "anchor", "title", "tags", "summary")
KINDS = ("rule", "reference")
LEVELS = ("MUST", "SHOULD", "MAY")
ENFORCEMENTS = ("ci", "review", "advisory")
STATUSES = ("active", "deprecated", "experimental")
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# 领域元数据文件，不参与孤儿文件判定（不属于 rules/reference 内容）
DOMAIN_META_FILES = {"00-README.md"}


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


def check_schema(domain_dir, entry):
    """校验必填字段、字段类型、枚举取值、可选治理字段格式。"""
    problems = []
    entry_id = entry.get("id", "<无 id>")

    missing = [f for f in REQUIRED_FIELDS if f not in entry]
    if missing:
        problems.append(f"[{entry_id}] 缺少必填字段：{', '.join(missing)}")

    for field in ("id", "file", "title", "summary"):
        value = entry.get(field)
        if field in entry and (not isinstance(value, str) or not value.strip()):
            problems.append(f"[{entry_id}] 字段 {field} 必须是非空字符串")

    if "anchor" in entry and not isinstance(entry["anchor"], str):
        problems.append(f"[{entry_id}] 字段 anchor 必须是字符串（无锚点用空字符串）")

    if "tags" in entry:
        tags = entry["tags"]
        if not isinstance(tags, list) or not all(isinstance(t, str) and t.strip() for t in tags):
            problems.append(f"[{entry_id}] 字段 tags 必须是非空字符串数组")

    kind = entry.get("kind")
    if kind is not None and kind not in KINDS:
        problems.append(f"[{entry_id}] 非法 kind：{kind}（允许 {'/'.join(KINDS)}）")

    level = entry.get("level")
    if kind == "rule" and level is None:
        problems.append(f"[{entry_id}] kind=rule 必须有 level 字段")
    if level is not None and level not in LEVELS:
        problems.append(f"[{entry_id}] 非法 level：{level}（允许 {'/'.join(LEVELS)}）")
    if kind == "reference" and level is not None:
        problems.append(f"[{entry_id}] kind=reference 不应有 level 字段")

    for field, allowed in (("enforcement", ENFORCEMENTS), ("status", STATUSES)):
        value = entry.get(field)
        if value is not None and value not in allowed:
            problems.append(f"[{entry_id}] 非法 {field}：{value}（允许 {'/'.join(allowed)}）")

    if "source" in entry and not isinstance(entry["source"], list):
        problems.append(f"[{entry_id}] 字段 source 必须是数组")
    if "applies_to" in entry and not isinstance(entry["applies_to"], list):
        problems.append(f"[{entry_id}] 字段 applies_to 必须是数组")

    reviewed_at = entry.get("reviewed_at")
    if reviewed_at is not None and not (isinstance(reviewed_at, str) and DATE_RE.match(reviewed_at)):
        problems.append(f"[{entry_id}] 字段 reviewed_at 必须是 ISO 日期（YYYY-MM-DD）：{reviewed_at}")

    return problems


def check_id_format(domain, entry):
    entry_id = entry.get("id")
    if not isinstance(entry_id, str) or not entry_id:
        return None  # 已由 schema 检查报告
    if not ID_RE.match(entry_id):
        return f"[{entry_id}] id 不符合 <domain>.<两位编号|ref>.<slug> 格式"
    if not entry_id.startswith(f"{domain}."):
        return f"[{entry_id}] id 前缀与所属领域不一致，应以 {domain}. 开头"
    return None


def check_file_path_safe(domain_dir, entry):
    """禁止 file 逃出领域目录（.. 越界或绝对路径）。"""
    raw = entry.get("file")
    if not isinstance(raw, str) or not raw:
        return None
    entry_id = entry.get("id", "<无 id>")
    path = Path(raw)
    if path.is_absolute() or raw.startswith("/") or re.match(r'^[A-Za-z]:', raw):
        return f"[{entry_id}] file 不允许绝对路径：{raw}"
    resolved = (domain_dir / path).resolve()
    if domain_dir.resolve() not in resolved.parents and resolved != domain_dir.resolve():
        return f"[{entry_id}] file 越出领域目录：{raw}"
    return None


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


def check_orphan_files(domain_dir, entries):
    """报告领域内未被任何索引条目引用的 Markdown 文件。"""
    indexed = {e["file"] for e in entries if isinstance(e.get("file"), str)}
    problems = []
    for md in sorted(domain_dir.rglob("*.md")):
        rel = md.relative_to(domain_dir).as_posix()
        if rel in DOMAIN_META_FILES or rel in indexed:
            continue
        problems.append(f"孤儿文件未被索引引用：{rel}")
    return problems


def collect_all_domains(base_dir):
    return sorted(
        p.name for p in base_dir.iterdir()
        if p.is_dir() and (p / "index.jsonl").exists()
    )


def check_catalog(base_dir):
    """校验 catalog.json 与实际领域目录双向一致。

    catalog 登记了不存在的领域 → 目录册腐烂；实际领域未登记 → 审计会漏掉它。
    两个方向都必须报错，否则 catalog.json 会退化成无人维护的静态文档。
    """
    catalog_path = base_dir / "catalog.json"
    if not catalog_path.exists():
        return [f"catalog.json 不存在：{catalog_path}"]
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"catalog.json JSON 解析失败：{e}"]

    problems = []
    entries = catalog.get("domains")
    if not isinstance(entries, list):
        return ["catalog.json 缺少 domains 数组"]

    listed = []
    for item in entries:
        name = item.get("domain")
        if not name:
            problems.append("catalog.json 存在缺少 domain 字段的记录")
            continue
        listed.append(name)
        for field in ("title", "categories", "owner", "status", "reviewed_at"):
            if field not in item:
                problems.append(f"catalog.json [{name}] 缺少字段：{field}")
        status = item.get("status")
        if status is not None and status not in STATUSES:
            problems.append(f"catalog.json [{name}] 非法 status：{status}")
        reviewed_at = item.get("reviewed_at")
        if reviewed_at is not None and not (isinstance(reviewed_at, str) and DATE_RE.match(reviewed_at)):
            problems.append(f"catalog.json [{name}] reviewed_at 必须是 ISO 日期：{reviewed_at}")
        cats = item.get("categories")
        if isinstance(cats, list):
            for c in cats:
                if not (base_dir / name / c).is_dir():
                    problems.append(f"catalog.json [{name}] 登记的分类目录不存在：{c}/")

    actual = collect_all_domains(base_dir)
    for name in sorted(set(listed) - set(actual)):
        problems.append(f"catalog.json 登记了不存在的领域（或该领域无 index.jsonl）：{name}")
    for name in sorted(set(actual) - set(listed)):
        problems.append(f"领域未登记到 catalog.json：{name}")
    dupes = {n for n in listed if listed.count(n) > 1}
    for name in sorted(dupes):
        problems.append(f"catalog.json 重复登记领域：{name}")
    return problems


def check_duplicate_ids(domain_entries):
    """id 全局唯一。domain_entries 应覆盖全部领域，而非仅本次校验的领域。"""
    seen = {}
    problems = []
    for domain in sorted(domain_entries):
        for entry in domain_entries[domain]:
            entry_id = entry.get("id")
            if not entry_id:
                continue
            if entry_id in seen:
                problems.append(f"重复 id：{entry_id}（{seen[entry_id]} 与 {domain}）")
            else:
                seen[entry_id] = domain
    return problems


def run_checks(base_dir, domains):
    """domains 决定检查哪些领域的文件与锚点；id 唯一性始终按全局范围判定。"""
    problems = []
    target_entries = {}

    for domain in domains:
        domain_dir = base_dir / domain
        index_path = domain_dir / "index.jsonl"
        if not index_path.exists():
            problems.append(f"[{domain}] index.jsonl 不存在：{index_path}")
            continue
        entries = parse_index_file(index_path)
        target_entries[domain] = entries

        for entry in entries:
            for msg in check_schema(domain_dir, entry):
                problems.append(f"[{domain}] {msg}")
            for check in (check_id_format_wrapper(domain), check_file_path_safe):
                result = check(domain_dir, entry)
                if result:
                    problems.append(f"[{domain}] {result}")
            if not isinstance(entry.get("file"), str) or not entry["file"]:
                continue  # 无有效 file，跳过存在性/锚点检查
            for check in (check_file_exists, check_anchor_exists):
                result = check(domain_dir, entry)
                if result:
                    problems.append(f"[{domain}] {result}")

        for msg in check_orphan_files(domain_dir, entries):
            problems.append(f"[{domain}] {msg}")

    # 全局 id 唯一性：读取全部领域，而不只是本次指定的领域
    global_entries = dict(target_entries)
    for domain in collect_all_domains(base_dir):
        if domain in global_entries:
            continue
        try:
            global_entries[domain] = parse_index_file(base_dir / domain / "index.jsonl")
        except ValueError as e:
            problems.append(f"[{domain}] {e}")
    problems.extend(check_duplicate_ids(global_entries))
    problems.extend(check_catalog(base_dir))
    return problems


def check_id_format_wrapper(domain):
    """把 domain 绑定进 check_id_format，使其与其他 (domain_dir, entry) 检查签名一致。"""
    def _check(domain_dir, entry):
        return check_id_format(domain, entry)
    return _check


def build_audit(base_dir, domains):
    """生成健康报告：记录数、kind/level 分布、规范文件的二级标题索引覆盖率。

    覆盖率只统计 kind=rule 的文件——reference 按整篇文档登记是既定约定，
    对其按标题计算覆盖率会误导出无意义的拆分需求。
    """
    report = {"domains": {}, "totals": {"entries": 0, "rules": 0, "references": 0}}
    for domain in domains:
        domain_dir = base_dir / domain
        index_path = domain_dir / "index.jsonl"
        if not index_path.exists():
            continue
        entries = parse_index_file(index_path)
        kinds = Counter(e.get("kind") for e in entries)
        levels = Counter(e.get("level") for e in entries if e.get("kind") == "rule")
        per_file = defaultdict(int)
        for e in entries:
            if isinstance(e.get("file"), str) and e.get("kind") == "rule":
                per_file[e["file"]] += 1

        coverage = {}
        eligible_total = indexed_total = 0
        for rel, count in sorted(per_file.items()):
            target = domain_dir / rel
            if not target.exists():
                continue
            headings = [
                normalize_heading(line)
                for line in target.read_text(encoding="utf-8").splitlines()
                if HEADING_RE.match(line) and len(HEADING_RE.match(line).group(1)) == 2
            ]
            eligible = len(headings)
            coverage[rel] = {"indexed": count, "eligible_headings": eligible}
            eligible_total += eligible
            indexed_total += min(count, eligible) if eligible else count

        report["domains"][domain] = {
            "entries": len(entries),
            "kinds": dict(kinds),
            "levels": dict(levels),
            "orphan_files": check_orphan_files(domain_dir, entries),
            "coverage": coverage,
            "coverage_ratio": round(indexed_total / eligible_total, 3) if eligible_total else None,
        }
        report["totals"]["entries"] += len(entries)
        report["totals"]["rules"] += kinds.get("rule", 0)
        report["totals"]["references"] += kinds.get("reference", 0)
    return report


def print_audit(report):
    t = report["totals"]
    print(f"知识库审计报告：{t['entries']} 条记录（rule {t['rules']} / reference {t['references']}）")
    for domain, data in report["domains"].items():
        ratio = data["coverage_ratio"]
        ratio_text = f"{ratio:.1%}" if ratio is not None else "n/a（无规范文件）"
        print(f"\n== {domain}：{data['entries']} 条 | kinds={data['kinds']} | levels={data['levels']}")
        print(f"   规范文件二级标题索引覆盖率：{ratio_text}")
        if data["orphan_files"]:
            print(f"   孤儿文件：{data['orphan_files']}")
        for rel, c in data["coverage"].items():
            if c["eligible_headings"] and c["indexed"] < c["eligible_headings"]:
                print(f"   - {rel}: {c['indexed']}/{c['eligible_headings']}")


def main():
    # 脚本位于 .claude/skills/knowledge-base-maintain/scripts/，parents[4] 即仓库根，再进 knowledge-base/
    base_dir = Path(__file__).resolve().parents[4] / "knowledge-base"
    args = sys.argv[1:]
    audit = "--audit" in args
    domains = [a for a in args if not a.startswith("--")]
    if not domains:
        domains = collect_all_domains(base_dir)

    problems = run_checks(base_dir, domains)
    if audit:
        print_audit(build_audit(base_dir, domains))
        print()
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
