import pathlib
import shutil
import subprocess
import tempfile
import unittest

from check_new_skill_eval_case import (
    check,
    has_eval_case,
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


if __name__ == "__main__":
    unittest.main()
