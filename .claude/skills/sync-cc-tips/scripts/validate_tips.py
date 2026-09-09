#!/usr/bin/env python3
"""校验 tips.jsonl 的格式与完整性，供 sync-cc-tips 第三步与第五步共用。

一次调用跑完全部检查，输出 JSON 到 stdout；`ok` 为总判定，`checks` 逐项给结论。
调用方只需读 `ok`，需要定位问题时再看对应项的 `errors`。

## 九项检查

| key | 检查什么 | 失败是否阻断 |
|---|---|---|
| line_count | `^{` 行数 == 总行数 | 是 |
| json_valid | 逐行 JSON 合法 | 是 |
| schema | 四字段 {id, category, title, body} 齐全 | 是 |
| id_unique | id 全库唯一 | 是 |
| field_dup | body 内「功能」「效果」各恰好 1 次 | 是 |
| body_shape | body 含「功能」「效果」「例子」三段 | 是 |
| length | 超中位数 2 倍的条目清单 | **否，仅报告** |
| orphan_ref | 被删条目标识符是否仍被引用 | 是（需 --removed-ids） |
| count_match | 实测条目数 == 预期 | 是（需 --expect-entries） |

## 两条容易写错的规则

**「例子」不参与重复计数。** 允许分平台拆成多行「例子（Windows）：」
「例子（Linux/Mac）：」，故 body_shape 按**行首**匹配「例子」而不要求
「例子」与「：」紧邻。「功能」「效果」则必须各恰好 1 次——同一条内重复这两段
是语义重复。**不要用「字段段数 > 4 即报错」替代 field_dup**，那会误伤合法的
多段例子。

**length 只报告不判失败。** 长度自检约束的是改动增量（本轮有没有把某条推超阈值），
不是全库门禁。2026-09-09 实测 268 条中 20 条超阈值，其中 18 条属未被触及的存量——
按全库状态阻断会让每轮同步都被无关存量卡住。判断权在调用方。
"""

import argparse
import json
import statistics
import sys

DEFAULT_TIPS = "plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl"

REQUIRED_FIELDS = ("id", "category", "title", "body")

# 必须各恰好出现 1 次的 body 段落前缀
UNIQUE_SECTIONS = ("功能", "效果")

# body 必须具备的三段。「例子」按行首匹配，容许「例子（Windows）：」这类变体。
REQUIRED_SECTIONS = ("功能", "效果", "例子")

# 长度阈值 = 全库 body 长度中位数的倍数
LENGTH_MULTIPLIER = 2


def load(path):
    """读 tips.jsonl，返回 (entries, line_count_check, json_valid_check)。

    解析失败不抛异常——JSON 非法本身就是要报告的检查结果之一，抛出去会让
    调用方拿不到其余检查的结论。
    """
    with open(path, encoding="utf-8") as f:
        raw = f.readlines()

    total = len([l for l in raw if l.strip()])
    brace = 0
    entries = []
    bad_json = []

    for lineno, line in enumerate(raw, 1):
        s = line.strip()
        if not s:
            continue
        if s.startswith("{"):
            brace += 1
        try:
            entries.append({"lineno": lineno, "obj": json.loads(s)})
        except json.JSONDecodeError as e:
            bad_json.append({"line": lineno, "error": str(e)})

    line_count = {
        "ok": brace == total,
        "json_lines": brace,
        "total_lines": total,
    }
    if brace != total:
        line_count["hint"] = "有空行或有行不以 { 开头，格式破损"

    json_valid = {"ok": not bad_json}
    if bad_json:
        json_valid["errors"] = bad_json

    return entries, line_count, json_valid


def check_schema(entries):
    """四字段齐全。缺字段的条目在展示时会露出 KeyError 或空白。"""
    errors = []
    for e in entries:
        missing = [f for f in REQUIRED_FIELDS if not str(e["obj"].get(f, "")).strip()]
        if missing:
            errors.append({
                "line": e["lineno"],
                "id": e["obj"].get("id", "<无 id>"),
                "missing": missing,
            })
    return {"ok": not errors, "errors": errors} if errors else {"ok": True}


def check_id_unique(entries):
    """id 是稳定主键，重复会让按 id 增删改的写入脚本改错条目。"""
    seen = {}
    dups = []
    for e in entries:
        i = e["obj"].get("id", "").strip()
        if not i:
            continue
        if i in seen:
            dups.append({"id": i, "lines": [seen[i], e["lineno"]]})
        else:
            seen[i] = e["lineno"]
    return {"ok": not dups, "errors": dups} if dups else {"ok": True}


def section_counts(body):
    """统计 body 各行的段落前缀出现次数，按**行首**匹配。

    按行首而非全文 `in` 判断：正文中提到「效果：」二字（如例子里引用了别处的
    效果描述）不该被计成一个段落。
    """
    counts = {}
    for line in body.split("\n"):
        for prefix in REQUIRED_SECTIONS:
            if line.startswith(prefix):
                counts[prefix] = counts.get(prefix, 0) + 1
    return counts


def check_field_dup(entries):
    """「功能」「效果」各须恰好 1 次。

    ⚠️ 「例子」不在此列——分平台多行写法（例子（Windows）：／例子（Linux/Mac）：）
    是有意保留的例外。用「字段段数 > 4 即报错」替代本检查会误伤那种写法。
    """
    errors = []
    for e in entries:
        counts = section_counts(e["obj"].get("body", ""))
        for prefix in UNIQUE_SECTIONS:
            n = counts.get(prefix, 0)
            if n != 1:
                errors.append({
                    "line": e["lineno"],
                    "id": e["obj"].get("id", "<无 id>"),
                    "field": prefix,
                    "n": n,
                })
    return {"ok": not errors, "errors": errors} if errors else {"ok": True}


def check_body_shape(entries):
    """三段齐全。「例子」按行首匹配，不要求与「：」紧邻。"""
    errors = []
    for e in entries:
        counts = section_counts(e["obj"].get("body", ""))
        missing = [p for p in REQUIRED_SECTIONS if counts.get(p, 0) == 0]
        if missing:
            errors.append({
                "line": e["lineno"],
                "id": e["obj"].get("id", "<无 id>"),
                "missing": missing,
            })
    return {"ok": not errors, "errors": errors} if errors else {"ok": True}


def check_length(entries):
    """报告超阈值条目，**不判失败**。

    长度自检约束改动增量而非全库状态：调用方需自行比对「这条是不是本轮被推超的」。
    详见模块 docstring。
    """
    lengths = [len(e["obj"].get("body", "")) for e in entries]
    if not lengths:
        return {"ok": True, "skipped": "无条目"}
    median = statistics.median(lengths)
    threshold = median * LENGTH_MULTIPLIER
    over = [
        {"id": e["obj"].get("id", "<无 id>"), "len": len(e["obj"].get("body", ""))}
        for e in entries
        if len(e["obj"].get("body", "")) > threshold
    ]
    over.sort(key=lambda x: -x["len"])
    return {
        # 恒为 True：超阈值是待判断的信息，不是缺陷
        "ok": True,
        "median": round(median, 1),
        "threshold": round(threshold, 1),
        "over_count": len(over),
        "over": over,
        "note": "仅报告；长度自检约束改动增量，存量超阈值不阻断",
    }


def check_orphan_ref(entries, removed_ids):
    """被删条目的标识符是否仍被其他条目正文引用。

    A 条目的「效果」里引用了 B 的 flag 名，B 删除后该引用悬空。命中则须修正
    引用方措辞，而不是放着一个指向不存在功能的说明。
    """
    if not removed_ids:
        return {"ok": True, "skipped": "本轮无删除"}

    hits = []
    for e in entries:
        obj = e["obj"]
        if obj.get("id", "").strip() in removed_ids:
            continue  # 被删条目自身不算引用
        haystack = f"{obj.get('title', '')}\n{obj.get('body', '')}"
        for rid in removed_ids:
            if rid and rid in haystack:
                hits.append({
                    "line": e["lineno"],
                    "referrer": obj.get("id", "<无 id>"),
                    "removed_id": rid,
                })
    return {"ok": not hits, "hits": hits, "checked": sorted(removed_ids)}


def check_count_match(entries, expect):
    """实测条目数与预期是否一致，用于验「旧数 + 新增 − 删除 == 实得」。"""
    if expect is None:
        return {"ok": True, "skipped": "未提供 --expect-entries"}
    actual = len(entries)
    return {
        "ok": actual == expect,
        "expected": expect,
        "actual": actual,
        "delta": actual - expect,
    }


def validate(path=DEFAULT_TIPS, removed_ids=(), expect_entries=None):
    """跑全部检查，返回 (payload, ok)。"""
    entries, line_count, json_valid = load(path)

    checks = {
        "line_count": line_count,
        "json_valid": json_valid,
        "schema": check_schema(entries),
        "id_unique": check_id_unique(entries),
        "field_dup": check_field_dup(entries),
        "body_shape": check_body_shape(entries),
        "length": check_length(entries),
        "orphan_ref": check_orphan_ref(entries, set(removed_ids)),
        "count_match": check_count_match(entries, expect_entries),
    }

    failed = [k for k, v in checks.items() if not v["ok"]]
    payload = {
        "ok": not failed,
        "entries": len(entries),
        "failed": failed,
        "checks": checks,
    }
    return payload, not failed


def main(argv):
    p = argparse.ArgumentParser(
        prog="validate_tips.py",
        description="校验 tips.jsonl 的格式与完整性，输出 JSON。",
        epilog=(
            "示例：\n"
            "  python scripts/validate_tips.py\n"
            "  python scripts/validate_tips.py --removed-ids '/old,/gone' --expect-entries 271\n"
            "\n退出码：0 全部通过 / 1 有检查未通过 / 2 文件不可读\n"
            "\n注意：length 项恒为 ok——超阈值是待判断信息，长度自检约束改动增量而非全库状态。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("path", nargs="?", default=DEFAULT_TIPS, help=f"tips.jsonl 路径（默认 {DEFAULT_TIPS}）")
    p.add_argument(
        "--removed-ids",
        default="",
        metavar="IDS",
        help=(
            "本轮删除的条目 id，逗号分隔。提供后才做孤儿引用反查。"
            "⚠️ id 以 - 开头时（flag 类）须用 --removed-ids=--foo,--bar 等号形式，"
            "空格分隔会被解析成 flag。"
        ),
    )
    p.add_argument(
        "--expect-entries",
        type=int,
        metavar="N",
        help="预期条目数（旧数 + 新增 − 删除），用于核对增删账平。",
    )
    args = p.parse_args(argv[1:])

    removed = [s.strip() for s in args.removed_ids.split(",") if s.strip()]

    try:
        payload, ok = validate(args.path, removed, args.expect_entries)
    except OSError as e:
        print(f"错误: 无法读取 {args.path}: {e}", file=sys.stderr)
        return 2

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
