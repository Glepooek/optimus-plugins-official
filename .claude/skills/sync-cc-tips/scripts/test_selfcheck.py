#!/usr/bin/env python3
"""selfcheck.py 的单测。

按 `06-continuous-improvement.md` §6：**每一项都测两侧**——「应通过」与「应拦截」。
只测通过侧会漏掉恒通过（检查形同虚设），只测拦截侧会漏掉恒拒绝（每轮都跑不起来）。
本 skill 的历史事故里，三条高危缺陷全部是「只验了想验的那一侧」。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import selfcheck as sc  # noqa: E402

SKILL_OK = """---
name: demo
---

⚠️ **本流程含 2 个阻塞式人工确认点，不得跳过：**

两个确认点因此始终有人应答。

| 4 | 运行条件 | git 是否干净 | 🔴 **可协商风险 → CHECKPOINT**，见下 |

> 🔴 **CHECKPOINT**：写入前展示变更预览。

配套文件：`references/only-one.md`、`known-issues.md`

写入格式：`{"id":"/xxx","category":"分类","title":"标题"}`
"""


class SelfcheckCase(unittest.TestCase):
    """在临时目录里造一个最小 skill，逐项改坏一处再跑。"""

    def make(self, skill_md=SKILL_OK, known_issues="# 台账\n\n正文 499/500。\n",
             refs=("only-one.md",), tips=None):
        d = Path(tempfile.mkdtemp())
        (d / "SKILL.md").write_text(skill_md, encoding="utf-8")
        (d / "known-issues.md").write_text(known_issues, encoding="utf-8")
        (d / "references").mkdir()
        for name in refs:
            (d / "references" / name).write_text("x\n", encoding="utf-8")
        tips_path = None
        if tips is not None:
            tips_path = d / "tips.jsonl"
            tips_path.write_text(tips, encoding="utf-8")
        return d, tips_path

    def run_check(self, **kw):
        d, tips_path = self.make(**kw)
        return sc.run(d, tips_path)


class TestLineBudget(SelfcheckCase):
    def test_under_limit_passes(self):
        r = self.run_check()
        self.assertTrue(r["checks"]["skill_line_count"]["ok"])
        self.assertTrue(r["checks"]["known_issues_cap"]["ok"])

    def test_over_skill_limit_fails(self):
        long_md = SKILL_OK + "\n填充\n" * (sc.SKILL_LINE_LIMIT + 5)
        r = self.run_check(skill_md=long_md, known_issues="# 台账\n")
        self.assertFalse(r["checks"]["skill_line_count"]["ok"])
        self.assertIn("skill_line_count", r["failed"])
        self.assertLess(r["checks"]["skill_line_count"]["margin"], 0)

    def test_over_known_issues_cap_fails(self):
        big = "# 台账\n" + "行\n" * (sc.KNOWN_ISSUES_LINE_CAP + 1)
        r = self.run_check(known_issues=big)
        self.assertFalse(r["checks"]["known_issues_cap"]["ok"])


class TestCheckpointCount(SelfcheckCase):
    def test_matching_count_passes(self):
        r = self.run_check()
        chk = r["checks"]["checkpoint_count"]
        self.assertTrue(chk["ok"], chk)
        self.assertEqual(chk["declared"], 2)
        self.assertEqual(chk["landing_count"], 2)

    def test_declared_more_than_landings_fails(self):
        r = self.run_check(skill_md=SKILL_OK.replace("含 2 个", "含 3 个"))
        self.assertFalse(r["checks"]["checkpoint_count"]["ok"])

    def test_pointer_line_not_counted_as_landing(self):
        """「→ 🔴 见下方 CHECKPOINT」是指针，不是确认点本身——算进去会恒多一个。"""
        md = SKILL_OK.replace(
            "配套文件：", "| `needs_confirm` | 范围过大 | `true` → 🔴 见下方 CHECKPOINT |\n\n配套文件："
        )
        chk = self.run_check(skill_md=md)["checks"]["checkpoint_count"]
        self.assertTrue(chk["ok"], chk)
        self.assertEqual(chk["landing_count"], 2)

    def test_cn_numeral_drift_fails(self):
        """阿拉伯数字与落地点一致、但中文数字表述是旧数时也要拦——历史上正是这样漂的。"""
        md = SKILL_OK.replace("两个确认点", "三个确认点")
        self.assertFalse(self.run_check(skill_md=md)["checks"]["checkpoint_count"]["ok"])

    def test_missing_declaration_fails(self):
        md = SKILL_OK.replace("⚠️ **本流程含 2 个阻塞式人工确认点，不得跳过：**", "")
        chk = self.run_check(skill_md=md)["checks"]["checkpoint_count"]
        self.assertFalse(chk["ok"])
        self.assertIn("声明句", chk["errors"][0])


class TestDanglingRefs(SelfcheckCase):
    def test_existing_refs_pass(self):
        self.assertTrue(self.run_check()["checks"]["dangling_refs"]["ok"])

    def test_missing_file_fails(self):
        md = SKILL_OK.replace("`references/only-one.md`", "`references/not-there.md`")
        chk = self.run_check(skill_md=md)["checks"]["dangling_refs"]
        self.assertFalse(chk["ok"])
        self.assertTrue(any("not-there.md" in e for e in chk["errors"]))

    def test_unreferenced_reference_fails(self):
        """反向：references/ 下有文件而正文一次没提——外移后忘了写指针即此形态。"""
        chk = self.run_check(refs=("only-one.md", "orphan.md"))["checks"]["dangling_refs"]
        self.assertFalse(chk["ok"])
        self.assertTrue(any("orphan.md" in e for e in chk["errors"]))

    def test_external_name_not_treated_as_dangling(self):
        md = SKILL_OK.replace("`known-issues.md`", "`AGENTS.md`")
        self.assertTrue(self.run_check(skill_md=md)["checks"]["dangling_refs"]["ok"])


class TestCategoryShape(SelfcheckCase):
    def test_bracket_free_template_and_data_pass(self):
        tips = json.dumps({"id": "/a", "category": "CLI", "title": "t", "body": "b"}, ensure_ascii=False) + "\n"
        self.assertTrue(self.run_check(tips=tips)["checks"]["category_shape"]["ok"])

    def test_bracketed_template_fails(self):
        md = SKILL_OK.replace('"category":"分类"', '"category":"[分类]"')
        chk = self.run_check(skill_md=md)["checks"]["category_shape"]
        self.assertFalse(chk["ok"])
        self.assertTrue(any("模板" in e for e in chk["errors"]))

    def test_bracketed_data_fails(self):
        tips = json.dumps({"id": "/a", "category": "[CLI]", "title": "t", "body": "b"}, ensure_ascii=False) + "\n"
        chk = self.run_check(tips=tips)["checks"]["category_shape"]
        self.assertFalse(chk["ok"])
        self.assertTrue(any("tips.jsonl:1" in e for e in chk["errors"]))

    def test_broken_json_line_skipped_not_crashed(self):
        """JSON 合法性归 validate_tips.py，本项遇到坏行跳过而不是崩。"""
        self.assertTrue(self.run_check(tips="{不是 JSON\n")["checks"]["category_shape"]["ok"])


class TestLineClaims(SelfcheckCase):
    def test_accurate_claim_passes(self):
        n = len(SKILL_OK.splitlines())
        chk = self.run_check(known_issues=f"# 台账\n\n正文 {n}/500。\n")["checks"]["line_claims"]
        self.assertTrue(chk["ok"], chk)
        self.assertEqual(chk["claims"][0]["claimed"], n)

    def test_stale_claim_fails(self):
        """写死的派生值失准是静默的——这一项就是为了让它不再静默。"""
        chk = self.run_check(known_issues="# 台账\n\n正文 490/500。\n")["checks"]["line_claims"]
        self.assertFalse(chk["ok"])
        self.assertIn("490/500", chk["errors"][0])

    def test_no_claim_passes(self):
        self.assertTrue(self.run_check(known_issues="# 台账\n")["checks"]["line_claims"]["ok"])


class TestRunAndCLI(SelfcheckCase):
    def test_missing_skill_md_raises(self):
        d = Path(tempfile.mkdtemp())
        (d / "known-issues.md").write_text("x\n", encoding="utf-8")
        with self.assertRaises(FileNotFoundError):
            sc.run(d, None)

    def test_cli_exit_code_reflects_failure(self):
        d, _ = self.make(known_issues="# 台账\n\n正文 490/500。\n")
        code = sc.main(["selfcheck.py", "--skill-dir", str(d), "--tips", str(d / "nope.jsonl")])
        self.assertEqual(code, 1)

    def test_cli_exit_zero_when_clean(self):
        d, _ = self.make(known_issues="# 台账\n")
        code = sc.main(["selfcheck.py", "--skill-dir", str(d), "--tips", str(d / "nope.jsonl")])
        self.assertEqual(code, 0)

    def test_cli_unreadable_path_returns_2(self):
        code = sc.main(["selfcheck.py", "--skill-dir", str(Path(tempfile.mkdtemp()) / "absent")])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
