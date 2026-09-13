import pathlib
import shutil
import subprocess
import tempfile
import unittest

from check_new_skill_eval_case import (
    check,
    has_eval_case,
    malformed_case_dirs,
    new_skill_dirs,
)


def git(root, *args):
    """在 root 里跑 git，失败即抛——测试里静默失败比报错更难查。"""
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


class TestNewSkillDirs(unittest.TestCase):
    """路径筛选是纯函数，与文件系统和 git 都无关，单独测。"""

    def test_plugin_skill_is_picked(self):
        self.assertEqual(
            new_skill_dirs(["plugins/p/skills/s/SKILL.md"]),
            ["plugins/p/skills/s"])

    def test_maintenance_skill_is_ignored(self):
        """.claude/skills/ 是本仓自用、不对外发布，不要求 case。"""
        self.assertEqual(new_skill_dirs([".claude/skills/s/SKILL.md"]), [])

    def test_external_plugin_is_ignored(self):
        """external_plugins/ 是拷贝自上游的内容，不替上游造 case。"""
        self.assertEqual(
            new_skill_dirs(["external_plugins/p/skills/s/SKILL.md"]), [])

    def test_nested_skill_md_is_ignored(self):
        """恰好 5 段才算；本仓 56 个 SKILL.md 无更深形态。"""
        self.assertEqual(
            new_skill_dirs(["plugins/p/skills/s/sub/SKILL.md"]), [])

    def test_other_file_in_skill_dir_is_ignored(self):
        self.assertEqual(new_skill_dirs(["plugins/p/skills/s/README.md"]), [])

    def test_agents_dir_is_ignored(self):
        """agent 不是 skill，没有 eval case 的概念。"""
        self.assertEqual(new_skill_dirs(["plugins/p/agents/a.md"]), [])

    def test_multiple_hits_keep_input_order(self):
        self.assertEqual(
            new_skill_dirs([
                "plugins/a/skills/x/SKILL.md",
                "docs/note.md",
                "plugins/b/skills/y/SKILL.md",
            ]),
            ["plugins/a/skills/x", "plugins/b/skills/y"])

    def test_filename_with_shell_metacharacters_is_just_text(self):
        """文件名不经 shell：含元字符只是普通字符，不解释、不注入。

        本仓的必需检查不跳过 fork PR，而 fork 的文件名不可信——这条
        测试锁住「解析全在 Python 内」这个实现约束。
        """
        self.assertEqual(
            new_skill_dirs(["plugins/p;whoami/skills/s/SKILL.md"]),
            ["plugins/p;whoami/skills/s"])


class TestHasEvalCase(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.skill = "plugins/p/skills/s"
        (self.root / self.skill).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _make_case(self, name, marker):
        d = self.root / self.skill / "evals" / name
        d.mkdir(parents=True)
        (d / marker).write_text("x", encoding="utf-8")

    def test_prompt_md_counts(self):
        self._make_case("c1", "prompt.md")
        self.assertTrue(has_eval_case(self.root, self.skill))

    def test_case_yaml_counts(self):
        """case.yaml 与 prompt.md 是官方两种等价写法。"""
        self._make_case("c1", "case.yaml")
        self.assertTrue(has_eval_case(self.root, self.skill))

    def test_no_evals_dir(self):
        self.assertFalse(has_eval_case(self.root, self.skill))

    def test_empty_evals_dir(self):
        (self.root / self.skill / "evals").mkdir()
        self.assertFalse(has_eval_case(self.root, self.skill))

    def test_loose_file_directly_under_evals_does_not_count(self):
        """官方按 <eval dir>/**/case.yaml 发现 case，散在 evals/ 根下的不算。

        这是本仓 trigger-eval.json 的原形态：文件在 evals/ 下，
        但 claude plugin eval 找到 0 个 case。
        """
        e = self.root / self.skill / "evals"
        e.mkdir()
        (e / "prompt.md").write_text("x", encoding="utf-8")
        self.assertFalse(has_eval_case(self.root, self.skill))

    def test_case_dir_without_marker_does_not_count(self):
        d = self.root / self.skill / "evals" / "c1"
        d.mkdir(parents=True)
        (d / "notes.txt").write_text("x", encoding="utf-8")
        self.assertFalse(has_eval_case(self.root, self.skill))

    def test_second_case_dir_satisfies_even_if_first_does_not(self):
        (self.root / self.skill / "evals" / "empty").mkdir(parents=True)
        self._make_case("real", "prompt.md")
        self.assertTrue(has_eval_case(self.root, self.skill))


class TestCheckAgainstRealGit(unittest.TestCase):
    """--diff-filter=A 的语义必须用真 git 验证。

    「修改已有 skill 不触发」是本门禁的核心承诺（用户拍板的「存量不回溯」），
    mock 掉 git 就等于把这条承诺假设成真，测不出它。
    """

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "t@example.com")
        git(self.root, "config", "user.name", "t")
        self._write("plugins/p/skills/old/SKILL.md", "old")
        self._commit("plugins/p/skills/old/SKILL.md")
        # 记录实际 sha——不能用字面 "HEAD"，后续提交会让它漂到新 commit
        self.base = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root,
            capture_output=True, text=True, check=True).stdout.strip()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def _commit(self, *rels):
        for r in rels:
            git(self.root, "add", r)
        git(self.root, "commit", "-q", "-m", "change")

    def test_modifying_existing_skill_does_not_trigger(self):
        """存量不回溯：old/ 至今没有 evals，改它也不该被拦。"""
        self._write("plugins/p/skills/old/SKILL.md", "old v2")
        self._commit("plugins/p/skills/old/SKILL.md")
        self.assertEqual(check(self.base, "HEAD", self.root), ([], 0))

    def test_new_skill_without_case_is_reported(self):
        self._write("plugins/p/skills/new/SKILL.md", "new")
        self._commit("plugins/p/skills/new/SKILL.md")
        self.assertEqual(check(self.base, "HEAD", self.root),
                         (["plugins/p/skills/new"], 1))

    def test_new_skill_with_case_passes(self):
        self._write("plugins/p/skills/new/SKILL.md", "new")
        self._write("plugins/p/skills/new/evals/c1/prompt.md", "q")
        self._commit("plugins/p/skills/new/SKILL.md",
                     "plugins/p/skills/new/evals/c1/prompt.md")
        self.assertEqual(check(self.base, "HEAD", self.root), ([], 1))

    def test_only_the_skill_missing_a_case_is_reported(self):
        self._write("plugins/p/skills/a/SKILL.md", "a")
        self._write("plugins/p/skills/a/evals/c1/prompt.md", "q")
        self._write("plugins/p/skills/b/SKILL.md", "b")
        self._commit("plugins/p/skills/a/SKILL.md",
                     "plugins/p/skills/a/evals/c1/prompt.md",
                     "plugins/p/skills/b/SKILL.md")
        self.assertEqual(check(self.base, "HEAD", self.root),
                         (["plugins/p/skills/b"], 2))

    def test_change_touching_no_skill_passes(self):
        self._write("docs/x.md", "x")
        self._commit("docs/x.md")
        self.assertEqual(check(self.base, "HEAD", self.root), ([], 0))

    def test_adding_eval_case_to_existing_skill_is_not_a_new_skill(self):
        """给存量 skill 补 case：SKILL.md 未新增，checked 应为 0。

        这正是迁移 jenkins-build 那批 evals 时的形态——给存量 skill
        补 case 的改动必须被本门禁放行，否则那次 PR 会被自己的门禁挡住。
        """
        self._write("plugins/p/skills/old/evals/c1/prompt.md", "q")
        self._commit("plugins/p/skills/old/evals/c1/prompt.md")
        self.assertEqual(check(self.base, "HEAD", self.root), ([], 0))


class TestMalformedCaseDirs(unittest.TestCase):
    """全量模式：evals/ 下**每个**子目录都要含 marker。

    与 TestHasEvalCase 测的是相反的量词——那里是「任一合格即可」，
    这里是「每个都要合格」。两个判据并存是刻意的，理由见
    malformed_case_dirs 的 docstring。
    """

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _case(self, skill, name, marker=None):
        d = self.root / "plugins" / skill / "skills" / "s" / "evals" / name
        d.mkdir(parents=True)
        if marker:
            (d / marker).write_text("x", encoding="utf-8")

    def test_empty_repo_reports_zero(self):
        """没有任何 case 目录时通过，且计数为 0——本仓当前正是这个状态。"""
        self.assertEqual(malformed_case_dirs(self.root), ([], 0))

    def test_all_good_dirs_pass(self):
        self._case("p", "c1", "prompt.md")
        self._case("p", "c2", "case.yaml")
        self.assertEqual(malformed_case_dirs(self.root), ([], 2))

    def test_one_bad_among_good_is_reported(self):
        """🔴 这条是本模式存在的理由：has_eval_case 在此返回 True。

        2 个合格 + 1 个缺 marker 时，「这个 skill 有 case」成立，而
        claude plugin eval 会静默少跑那一个。
        """
        self._case("p", "c1", "prompt.md")
        self._case("p", "c2", "prompt.md")
        self._case("p", "broken")
        self.assertTrue(has_eval_case(self.root, "plugins/p/skills/s"))
        self.assertEqual(
            malformed_case_dirs(self.root),
            (["plugins/p/skills/s/evals/broken"], 3))

    def test_loose_file_under_evals_is_not_flagged(self):
        """散落在 evals/ 根下的文件不构成 case 目录，本模式刻意不判它。

        这是 wpf-code-review/evals/evals.json 的形态。它遵守
        knowledge-base/skill-authoring 的 MUST 条款，两套 eval 规范谁服从谁
        待人裁决（todo A4），门禁不替人做取舍。
        """
        e = self.root / "plugins/p/skills/s/evals"
        e.mkdir(parents=True)
        (e / "evals.json").write_text("{}", encoding="utf-8")
        self.assertEqual(malformed_case_dirs(self.root), ([], 0))

    def test_maintenance_and_external_skills_are_not_scanned(self):
        """扫描范围与 new_skill_dirs 一致：只 plugins/。"""
        for base in (".claude/skills/s", "external_plugins/p/skills/s"):
            d = self.root / base / "evals" / "broken"
            d.mkdir(parents=True)
        self.assertEqual(malformed_case_dirs(self.root), ([], 0))

    def test_multiple_plugins_are_all_scanned(self):
        self._case("a", "bad1")
        self._case("b", "bad2")
        bad, total = malformed_case_dirs(self.root)
        self.assertEqual(total, 2)
        self.assertEqual(sorted(bad), [
            "plugins/a/skills/s/evals/bad1",
            "plugins/b/skills/s/evals/bad2",
        ])

    def test_file_directly_inside_case_dir_position(self):
        """marker 必须在子目录内，放在更深一层不算。"""
        d = self.root / "plugins/p/skills/s/evals/c1/graders"
        d.mkdir(parents=True)
        (d / "prompt.md").write_text("x", encoding="utf-8")
        self.assertEqual(malformed_case_dirs(self.root),
                         (["plugins/p/skills/s/evals/c1"], 1))


if __name__ == "__main__":
    unittest.main()
