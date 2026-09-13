"""check_skill_mirrors 的单测。

🔴 本文件刻意在临时目录里跑**真 git**，不 mock `git check-ignore`。
原因是本脚本要修的那个 bug 就在 git 的行为里——`check-ignore` 默认查 index，
`git add -f` 之后目录不再被判为已忽略。把 git 换成替身的测试恰好绕过出错的
那一环，永远抓不到它。`test_add_f_does_not_make_an_ignored_skill_distributed`
就是那次事故的活体复现，去掉 `--no-index` 它必然失败。
"""
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from check_skill_mirrors import (
    bad_modes, check_all, check_forward, check_reverse, distributed_skills)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True)


def make_skill(root, name, with_skill_md=True):
    d = root / ".claude" / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    if with_skill_md:
        (d / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    return d


def make_mirrors(root, name, mirrors=(".kiro", ".agents")):
    """造镜像条目。用普通目录而非真 symlink——正向检查只判「存在」，
    而 Windows 上建符号链接需要额外权限，会让测试在本机不可跑。
    模式位那一层由 bad_modes() 的纯函数测试覆盖。"""
    for m in mirrors:
        p = root / m / "skills" / name
        p.mkdir(parents=True, exist_ok=True)


class TestSkillMirrors(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        git(self.root, "init", "-q")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # --- 正向 ---

    def test_mirrors_complete_passes(self):
        make_skill(self.root, "alpha")
        make_mirrors(self.root, "alpha")
        self.assertEqual(check_all(self.root), [])

    def test_missing_both_mirrors_reports_two_problems_with_fix_command(self):
        make_skill(self.root, "alpha")
        problems = check_forward(self.root)
        self.assertEqual(len(problems), 2)
        self.assertTrue(any(".kiro/skills/alpha" in p for p in problems))
        self.assertTrue(any(".agents/skills/alpha" in p for p in problems))
        # 报错必须自带补齐命令：commit-cc-plugin 的错误表就指望这一句
        self.assertTrue(all("ln -s" in p for p in problems))

    def test_missing_one_mirror_reports_only_that_one(self):
        make_skill(self.root, "alpha")
        make_mirrors(self.root, "alpha", mirrors=(".kiro",))
        problems = check_forward(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn(".agents/skills/alpha", problems[0])

    # --- 排除理由 (一)：不是一个 skill ---

    def test_directory_without_skill_md_needs_no_mirror(self):
        """darwin-skill 的形态：它是评分工作目录，正文装在全局，本仓这份没有
        SKILL.md。镜像一个没有 SKILL.md 的目录对两个 harness 都无意义。"""
        make_skill(self.root, "workdir-only", with_skill_md=False)
        (self.root / ".claude" / "skills" / "workdir-only" / "results.tsv").write_text(
            "x\n", encoding="utf-8")
        self.assertEqual(distributed_skills(self.root), [])
        self.assertEqual(check_forward(self.root), [])

    # --- 排除理由 (二)：是 skill 但本仓刻意不分发 ---

    def test_gitignored_skill_needs_no_mirror(self):
        make_skill(self.root, "vendored")
        (self.root / ".gitignore").write_text(
            ".claude/skills/vendored/\n", encoding="utf-8")
        self.assertEqual(distributed_skills(self.root), [])

    def test_two_exclusion_reasons_are_independent(self):
        """两条理由不是替代关系。当下本仓恰好只有一个目录同时满足两者，
        误以为它们等价正是这次判据设计里最容易犯的错。"""
        make_skill(self.root, "no-md", with_skill_md=False)       # 只满足 (一)
        make_skill(self.root, "ignored-md")                        # 只满足 (二)
        make_skill(self.root, "real")                              # 都不满足
        make_mirrors(self.root, "real")
        (self.root / ".gitignore").write_text(
            ".claude/skills/ignored-md/\n", encoding="utf-8")
        self.assertEqual(distributed_skills(self.root), ["real"])
        self.assertEqual(check_forward(self.root), [])

    def test_add_f_does_not_make_an_ignored_skill_distributed(self):
        """🔴 事故复现（去掉 --no-index 必然失败）。

        `git check-ignore` 默认也查 index：子树内任一文件经 `git add -f` 进入
        index 后，该目录就不再被报告为已忽略。于是「把判据入库」这个动作会反过来
        要求给一个刻意不分发的目录补两处镜像并阻断提交。
        """
        make_skill(self.root, "vendored")
        (self.root / ".gitignore").write_text(
            ".claude/skills/vendored/\n", encoding="utf-8")
        tsv = self.root / ".claude" / "skills" / "vendored" / "results.tsv"
        tsv.write_text("a\tb\n", encoding="utf-8")
        self.assertEqual(
            git(self.root, "add", "-f", ".claude/skills/vendored/results.tsv").returncode, 0)

        # 前置断言：证明本测试确实在守 --no-index 这个开关。
        # 不带该开关时 git 已认为该目录「未被忽略」（退出码非 0）。
        self.assertNotEqual(
            git(self.root, "check-ignore", "-q", ".claude/skills/vendored").returncode, 0)

        self.assertEqual(distributed_skills(self.root), [])
        self.assertEqual(check_forward(self.root), [])

    # --- 反向与模式位 ---

    def test_dangling_mirror_is_reported_with_cleanup_command(self):
        make_mirrors(self.root, "gone")
        problems = check_reverse(self.root)
        self.assertEqual(len(problems), 2)
        self.assertTrue(all("git rm" in p for p in problems))
        self.assertTrue(any("指向已不存在的" in p for p in problems))

    def test_bad_modes_picks_non_symlink_entries(self):
        out = ("120000 abc 0\t.kiro/skills/alpha\n"
               "100644 def 0\t.agents/skills/alpha\n")
        self.assertEqual(bad_modes(out),
                         ["100644 def 0\t.agents/skills/alpha"])

    def test_bad_modes_empty_output_is_clean(self):
        self.assertEqual(bad_modes(""), [])
        self.assertEqual(bad_modes("\n"), [])


if __name__ == "__main__":
    unittest.main()
