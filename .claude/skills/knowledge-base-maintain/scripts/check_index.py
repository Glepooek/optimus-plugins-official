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

# 废弃标记：正文小节标题与 source 目标标题都用这一个词，只认一种写法便于机械校验
DEPRECATED_MARK = "已废弃"

# 替代去向：条目 id（`git.03.pr-conventions`）或规范文件路径（`git/rules/03-pull-requests.md`）
SUCCESSOR_RE = re.compile(r'[a-z0-9-]+\.(?:\d{2}|ref)\.[a-z0-9-]+|[a-z0-9-]+/(?:rules|reference)/[a-z0-9-]+\.md')

# 领域元数据文件，不参与孤儿文件判定（不属于 rules/reference 内容）
DOMAIN_META_FILES = {"README.md"}


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

    # MAY 是可选做法，不应作为 CI 拦截依据
    if level == "MAY" and entry.get("enforcement") == "ci":
        problems.append(f"[{entry_id}] level=MAY 不得标 enforcement=ci（可选做法不作为 CI 拦截依据）")

    if entry.get("enforcement") is not None and kind == "reference":
        problems.append(f"[{entry_id}] kind=reference 不应有 enforcement 字段")

    if "source" in entry and not isinstance(entry["source"], list):
        problems.append(f"[{entry_id}] 字段 source 必须是数组")
    if "applies_to" in entry and not isinstance(entry["applies_to"], list):
        problems.append(f"[{entry_id}] 字段 applies_to 必须是数组")

    reviewed_at = entry.get("reviewed_at")
    if reviewed_at is not None and not (isinstance(reviewed_at, str) and DATE_RE.match(reviewed_at)):
        problems.append(f"[{entry_id}] 字段 reviewed_at 必须是 ISO 日期（YYYY-MM-DD）：{reviewed_at}")

    return problems


def check_source_refs(domain_dir, entry):
    """校验 source 中的内部引用（<file>#<anchor> 形式）真实存在。

    source 允许混放两类取值：外部 URL 与领域内部路径。URL 无法离线校验（也不该在
    校验期发网络请求），内部路径可以——不校验就等于新增一批无人看守的引用，
    与规范文件迁移后失效的正文交叉引用是同一类腐烂。
    """
    sources = entry.get("source")
    if not isinstance(sources, list):
        return []  # 类型问题已由 check_schema 报告
    entry_id = entry.get("id", "<无 id>")
    problems = []
    for ref in sources:
        if not isinstance(ref, str) or not ref.strip():
            problems.append(f"[{entry_id}] source 元素必须是非空字符串")
            continue
        if "://" in ref:
            continue  # 外部 URL，不做离线校验
        rel, _, anchor = ref.partition("#")
        target = domain_dir / rel
        if not target.exists():
            problems.append(f"[{entry_id}] source 引用的文件不存在：{rel}")
            continue
        if not anchor:
            continue
        matched = [h for h in find_headings(target.read_text(encoding="utf-8")) if anchor in h]
        if not matched:
            problems.append(f"[{entry_id}] source 锚点未在 {rel} 中找到匹配标题：{anchor}")
        elif all(DEPRECATED_MARK in h for h in matched):
            # 活跃规则的理由挂在已废弃小节上——该小节随时会被移除，届时 source 静默失效
            problems.append(
                f"[{entry_id}] source 指向{DEPRECATED_MARK}的小节：{rel} 的「{matched[0]}」，"
                f"须改指其替代去向"
            )
    return problems


def check_deprecated(domain_dir, entry):
    """校验 `status: deprecated` 条目的三项前提。

    `deprecated` 长期是纯枚举占位（全库无一使用），废弃只能走「删索引条目」——
    删完外部消费者拿旧 id 检索只得到「查不到」，而不是「已废弃，改用 X」。要让该状态
    真正可用，索引与正文必须同时表明废弃事实与替代去向，否则它只是个更隐蔽的死条目。
    """
    if entry.get("status") != "deprecated":
        return []
    entry_id = entry.get("id", "<无 id>")
    problems = []

    if entry.get("enforcement") == "ci":
        problems.append(f"[{entry_id}] status=deprecated 不得标 enforcement=ci（已废弃的规则不应仍在 CI 拦截）")

    summary = entry.get("summary") or ""
    if not SUCCESSOR_RE.search(summary):
        problems.append(
            f"[{entry_id}] summary 未说明替代去向——废弃条目须指明改用哪条规则"
            f"（条目 id 或 `<domain>/rules/<file>.md` 路径），只标废弃不给去向比直接删更糟"
        )

    # 正文标题须带废弃标记：索引说废弃而正文没标，按 file+anchor 读正文的人毫不知情
    anchor = entry.get("anchor") or ""
    rel = entry.get("file")
    if anchor and isinstance(rel, str) and rel:
        target = domain_dir / rel
        if target.exists():  # file 缺失由 check_file_exists 报告，此处不重复
            matched = [h for h in find_headings(target.read_text(encoding="utf-8")) if anchor in h]
            if matched and not any(DEPRECATED_MARK in h for h in matched):
                problems.append(
                    f"[{entry_id}] 正文标题未标注已废弃：{rel} 的「{matched[0]}」"
                    f"须改为「{matched[0]}（{DEPRECATED_MARK}）」"
                )
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
            for msg in check_source_refs(domain_dir, entry):
                problems.append(f"[{domain}] {msg}")
            for msg in check_deprecated(domain_dir, entry):
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


def covered_sections(target, anchors):
    """返回 (被 anchor 命中的二级章节数, 二级章节总数)。

    `anchor` 指向 h3 时归属到其父 h2——按更细粒度登记不该被算成未登记
    （`csharp/rules/02-coding-style.md` 的 15 条全部指向 h3）。

    早期实现用 `min(条目数, h2 数)` 封顶，只比数量不看落点：条目集中在同一小节时，
    多出的条目会把另一个小节的真实空缺掩盖成满分（实测 `csharp/rules/12-testing.md`
    17 条记 14/14，真实只覆盖 13 个）。覆盖率要等于"有多少小节可被检索到"，
    就必须按 anchor 落点算。
    """
    hit, current = set(), None
    h2_all = []
    for line in target.read_text(encoding="utf-8").splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        depth, text = len(m.group(1)), normalize_heading(line)
        if depth == 2:
            current = text
            h2_all.append(text)
        if depth in (2, 3) and current and any(a and a in text for a in anchors):
            hit.add(current)
    return len(hit), len(h2_all)


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
        rules = [e for e in entries if e.get("kind") == "rule"]
        enforcements = Counter(e.get("enforcement") or "(未填)" for e in rules)
        governance_filled = sum(1 for e in rules if e.get("enforcement"))
        per_file = defaultdict(list)
        for e in entries:
            if isinstance(e.get("file"), str) and e.get("kind") == "rule":
                per_file[e["file"]].append(e.get("anchor") or "")

        coverage = {}
        eligible_total = indexed_total = 0
        for rel, anchors in sorted(per_file.items()):
            target = domain_dir / rel
            if not target.exists():
                continue
            hit, eligible = covered_sections(target, anchors)
            coverage[rel] = {"indexed": hit if eligible else len(anchors),
                             "eligible_headings": eligible}
            eligible_total += eligible
            indexed_total += hit if eligible else len(anchors)

        report["domains"][domain] = {
            "entries": len(entries),
            "kinds": dict(kinds),
            "levels": dict(levels),
            "enforcements": dict(enforcements),
            "enforcement_coverage": (
                round(governance_filled / len(rules), 3) if rules else None
            ),
            "deprecated": [
                e["id"] for e in entries
                if e.get("status") == "deprecated" and isinstance(e.get("id"), str)
            ],
            "orphan_files": check_orphan_files(domain_dir, entries),
            "coverage": coverage,
            "coverage_ratio": round(indexed_total / eligible_total, 3) if eligible_total else None,
        }
        report["totals"]["entries"] += len(entries)
        report["totals"]["rules"] += kinds.get("rule", 0)
        report["totals"]["references"] += kinds.get("reference", 0)
        report["totals"]["deprecated"] = (
            report["totals"].get("deprecated", 0) + len(report["domains"][domain]["deprecated"])
        )
        report["totals"]["enforcement_filled"] = (
            report["totals"].get("enforcement_filled", 0) + governance_filled
        )
    return report


def print_audit(report):
    t = report["totals"]
    filled = t.get("enforcement_filled", 0)
    ratio = f"{filled / t['rules']:.1%}" if t["rules"] else "n/a"
    print(f"知识库审计报告：{t['entries']} 条记录（rule {t['rules']} / reference {t['references']}）")
    print(f"治理元数据：{filled}/{t['rules']} 条 rule 已填 enforcement（{ratio}）")
    if t.get("deprecated"):
        print(f"已废弃条目：{t['deprecated']} 条（正文保留、待下一个 Major 版本移除）")
    for domain, data in report["domains"].items():
        ratio = data["coverage_ratio"]
        ratio_text = f"{ratio:.1%}" if ratio is not None else "n/a（无规范文件）"
        print(f"\n== {domain}：{data['entries']} 条 | kinds={data['kinds']} | levels={data['levels']}")
        print(f"   规范文件二级标题索引覆盖率：{ratio_text}")
        if data["enforcements"]:
            print(f"   enforcement 分布：{data['enforcements']}")
        if data["deprecated"]:
            print(f"   已废弃：{', '.join(data['deprecated'])}")
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
