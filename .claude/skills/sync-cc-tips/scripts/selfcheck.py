#!/usr/bin/env python3
"""机械自检：把「不需要人读就能判定」的一致性检查从评审阶段拿走。

依据 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md` §7：
人工评审的成本与**语料总量**成正比，机械检查的成本与**检查项数**成正比。
以下六类历史上全部真实发生过，且**失准都是静默的**——没有任何报错。

| key | 检查什么 | 历史事故 |
|---|---|---|
| skill_line_count | SKILL.md 正文 ≤ 500 行 | 555 行时才被发现越界 |
| known_issues_cap | known-issues.md ≤ 150 行 | 491 行、超过它所描述的正文 |
| checkpoint_count | 声明的确认点数 == 实际落地点数 | 声明 4 个实为 5 个；「3 个增至 4」是旧数 |
| dangling_refs | 正文提到的同级文件真实存在，且 references/ 无没人引用的死文件 | 外移后漏提交 reference 会让引用悬空 |
| category_shape | JSON 模板与真实数据的 category 形态一致 | 模板带方括号、数据不带，跨两个 commit 固化 |
| line_claims | known-issues.md 里的 `N/500` 声明 == 实测行数 | 记 490 实为 497，方向还写反了 |

## 判据设计上的两处刻意收窄

**`checkpoint_count` 区分「落地点」与「指针」。** 正文里 🔴 出现 6 次，其中一处是
「→ 🔴 见下方 CHECKPOINT」的**指针**，不是确认点本身。故落地点判据要求 🔴 后 30
字符内出现 `**CHECKPOINT**` / `CHECKPOINT：` / `可协商风险`，指针行不匹配。
拿 🔴 总数当判据会恒多算一个。

**`line_claims` 只查 known-issues.md，不查 CHANGELOG。** CHANGELOG 按补记约定
保留历史行数（「555 → 497 行」），那些是当时的事实，跟改即伪造记录。

退出码：0 全过 / 1 有项未过 / 2 路径不可读。
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL_LINE_LIMIT = 500
KNOWN_ISSUES_LINE_CAP = 150

CN_NUM = {1: ("一",), 2: ("二", "两"), 3: ("三",), 4: ("四",), 5: ("五",),
          6: ("六",), 7: ("七",), 8: ("八",), 9: ("九",)}
CN_TO_INT = {form: n for n, forms in CN_NUM.items() for form in forms}

# 中文数字复述句。**只在正文确实有这种复述时才校验**——没有复述不构成缺陷，
# 强制要求它会让所有不用这种措辞的 skill 恒报错（初版即如此，被单测的通过侧抓出）
CN_RESTATE_RE = re.compile(r"([一二三四五六七八九两])个(?:确认点|阻塞)")

# 🔴 后 30 字符内出现这三种形态之一才算确认点落地点；「见下方 CHECKPOINT」是指针
CHECKPOINT_RE = re.compile(r"🔴[^|]{0,30}(\*\*CHECKPOINT\*\*|CHECKPOINT[：:]|可协商风险)")
DECLARE_DIGIT_RE = re.compile(r"含\s*(\d+)\s*个阻塞式人工确认点")
BACKTICK_FILE_RE = re.compile(r"`((?:references/|scripts/)?[A-Za-z0-9][A-Za-z0-9._-]*\.(?:md|json|py|sh|jsonl))`")
JSON_CATEGORY_RE = re.compile(r'"category"\s*:\s*"([^"]*)"')

# 不属本 skill 目录的文件名，正文提到它们是正常引用，不参与悬空判定
EXTERNAL_NAMES = {
    "AGENTS.md", "CLAUDE.md", "README.md",
    "tips.jsonl", "tips.txt", "plugin.json", "marketplace.json",
    "skill-conventions.md", "doc-conventions.md", "agent-conventions.md",
    "01-skill-format.md", "06-continuous-improvement.md",
    "show-tip.sh", "install.sh", "package_skill.py",
}


def _lines(path):
    return path.read_text(encoding="utf-8").split("\n")


def check_line_budget(skill_md, known_issues):
    """SKILL.md 与 known-issues.md 各自的行数上限。"""
    n_skill = len(skill_md.read_text(encoding="utf-8").splitlines())
    n_known = len(known_issues.read_text(encoding="utf-8").splitlines())
    return (
        {"ok": n_skill <= SKILL_LINE_LIMIT, "actual": n_skill, "limit": SKILL_LINE_LIMIT,
         "margin": SKILL_LINE_LIMIT - n_skill},
        {"ok": n_known <= KNOWN_ISSUES_LINE_CAP, "actual": n_known, "limit": KNOWN_ISSUES_LINE_CAP,
         "margin": KNOWN_ISSUES_LINE_CAP - n_known},
        n_skill,
    )


def check_checkpoints(skill_md):
    """声明的确认点数（阿拉伯数字与中文数字两处）== 实际落地点数。"""
    text = skill_md.read_text(encoding="utf-8")
    landings = [i + 1 for i, line in enumerate(text.split("\n")) if CHECKPOINT_RE.search(line)]
    m = DECLARE_DIGIT_RE.search(text)
    res = {"ok": False, "landings": landings, "landing_count": len(landings)}
    if not m:
        res["errors"] = ["正文未找到「含 N 个阻塞式人工确认点」声明句"]
        return res
    declared = int(m.group(1))
    res["declared"] = declared
    errors = []
    if declared != len(landings):
        errors.append(f"声明 {declared} 个，实际落地点 {len(landings)} 个（行号 {landings}）")
    cn_found = sorted({CN_TO_INT[m.group(1)] for m in CN_RESTATE_RE.finditer(text)})
    res["cn_restated"] = cn_found
    for n in cn_found:
        if n != len(landings):
            errors.append(f"中文数字复述与实际不符：正文写「{CN_NUM[n][0]}个确认点」，实际 {len(landings)} 个")
    res["ok"] = not errors
    if errors:
        res["errors"] = errors
    return res


def check_dangling_refs(skill_dir, skill_md):
    """正文提到的同级/子目录文件真实存在；references/ 下没有无人引用的死文件。"""
    text = skill_md.read_text(encoding="utf-8")
    errors = []
    mentioned = set()
    for tok in BACKTICK_FILE_RE.findall(text):
        name = tok.rsplit("/", 1)[-1]
        if name in EXTERNAL_NAMES:
            continue
        cands = [skill_dir / tok, skill_dir / "references" / name, skill_dir / "scripts" / name]
        if not any(c.exists() for c in cands):
            errors.append(f"正文引用 `{tok}` 但文件不存在（已试 ./、references/、scripts/）")
        mentioned.add(name)
    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for f in sorted(refs_dir.glob("*.md")):
            if f.name not in mentioned:
                errors.append(f"references/{f.name} 无人引用——正文一次都没提到它")
    return {"ok": not errors, "errors": errors, "mentioned": sorted(mentioned)}


def check_category_shape(skill_md, tips_path):
    """JSON 模板里的 category 与真实数据的形态一致（都不带方括号）。"""
    errors = []
    for val in JSON_CATEGORY_RE.findall(skill_md.read_text(encoding="utf-8")):
        if "[" in val or "]" in val:
            errors.append(f"SKILL.md 的 JSON 模板 category 带方括号：\"{val}\"")
    if tips_path and tips_path.exists():
        for i, line in enumerate(tips_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                cat = json.loads(line).get("category", "")
            except json.JSONDecodeError:
                continue  # JSON 合法性归 validate_tips.py，此处不重复判
            if "[" in cat or "]" in cat:
                errors.append(f"tips.jsonl:{i} 的 category 带方括号：\"{cat}\"")
    return {"ok": not errors, "errors": errors}


def check_line_claims(known_issues, actual_skill_lines):
    """known-issues.md 里的 `N/500` 声明必须等于实测行数。"""
    errors = []
    claims = []
    for i, line in enumerate(_lines(known_issues), start=1):
        for m in re.finditer(rf"(\d+)\s*/\s*{SKILL_LINE_LIMIT}\b", line):
            claimed = int(m.group(1))
            claims.append({"line": i, "claimed": claimed})
            if claimed != actual_skill_lines:
                errors.append(
                    f"known-issues.md:{i} 声明正文 {claimed}/{SKILL_LINE_LIMIT}，实测 {actual_skill_lines}"
                )
    return {"ok": not errors, "errors": errors, "claims": claims}


def run(skill_dir, tips_path):
    skill_dir = Path(skill_dir)
    skill_md = skill_dir / "SKILL.md"
    known_issues = skill_dir / "known-issues.md"
    for required in (skill_md, known_issues):
        if not required.exists():
            raise FileNotFoundError(required)

    budget_skill, budget_known, n_skill = check_line_budget(skill_md, known_issues)
    checks = {
        "skill_line_count": budget_skill,
        "known_issues_cap": budget_known,
        "checkpoint_count": check_checkpoints(skill_md),
        "dangling_refs": check_dangling_refs(skill_dir, skill_md),
        "category_shape": check_category_shape(skill_md, Path(tips_path) if tips_path else None),
        "line_claims": check_line_claims(known_issues, n_skill),
    }
    failed = [k for k, v in checks.items() if not v["ok"]]
    return {"ok": not failed, "failed": failed, "checks": checks}


DEFAULT_SKILL_DIR = ".claude/skills/sync-cc-tips"
DEFAULT_TIPS = "plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl"


def main(argv):
    p = argparse.ArgumentParser(
        prog="selfcheck.py",
        description="机械自检：行数上限、确认点计数、悬空引用、模板形态、派生值声明。",
        epilog=(
            "示例：\n"
            "  python .claude/skills/sync-cc-tips/scripts/selfcheck.py\n"
            "\n退出码：0 全过 / 1 有项未过 / 2 路径不可读\n"
            "\n⚠️ 本脚本只查机械可判定项。判据是否写宽到形同虚设、"
            "分支处置是否正确一类问题它查不出，仍需人工评审——"
            "但那份评审不该再花在本脚本能查的六项上。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--skill-dir", default=DEFAULT_SKILL_DIR, help=f"skill 目录（默认 {DEFAULT_SKILL_DIR}）")
    p.add_argument("--tips", default=DEFAULT_TIPS, help=f"tips.jsonl 路径（默认 {DEFAULT_TIPS}）")
    args = p.parse_args(argv[1:])
    try:
        payload = run(args.skill_dir, args.tips)
    except (FileNotFoundError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
