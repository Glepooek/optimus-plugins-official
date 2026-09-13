#!/usr/bin/env python3
"""校验 .claude/skills 的双 harness 符号链接镜像完整性。

三项检查，都是「失效了不报错」的形态：
  1. 正向——每个由本仓分发的 skill 都要在 .kiro/skills 与 .agents/skills 有同名镜像。
     缺了则该 skill 在对应 harness 里根本不被发现，而两个 harness 都不会因此报错。
  2. 反向——镜像指向已删除的 skill。悬空链接同样静默。
  3. 模式——镜像必须以 120000（symlink）入库。core.symlinks=false 时 git 会把它们
     存成内容为路径字符串的普通文件（100644），克隆到另一台机器就不是链接了。

🔴 「哪些目录该有镜像」有**两条正交的排除理由**，缺任何一条都会误判：

  (一) 不是一个 skill——目录里没有 SKILL.md。镜像的目的是让 skill 被两个 harness
       发现，一个没有 SKILL.md 的目录镜像过去对两侧都无意义。
       活体：.claude/skills/darwin-skill/ 是评分的**工作目录**，skill 正文装在全局
       ~/.claude/skills/darwin-skill/，本仓这个目录只承接 results.tsv 与 cards/。

  (二) 是 skill 但本仓刻意不分发——被 gitignore 排除。

两条看起来重叠，只是因为当下恰好只有一个目录同时满足两者。它们各自独立成立：
一个有 SKILL.md 却被 gitignore 的目录属 (二)，一个没有 SKILL.md 也未被忽略的
目录属 (一)。

🔴 第 (二) 条的 `--no-index` 不可省，这是本脚本存在的直接原因：
`git check-ignore` **默认也查 index**，子树内任一文件经 `git add -f` 进入 index 后，
该目录就不再被报告为已忽略。于是「把 results.tsv 判据入库」这个动作会反过来触发
本检查，要求给 darwin-skill 补两处镜像——而镜像它是错误声明。git 自己的文档正为
此列出 --no-index：「when developing patterns including negation to match a path
previously added with `git add -f`」。⚠️ 由此得到的教训比这一行开关更重要：
`git add -f` 并没有绕开 gitignore 那条边界，它只是把同一次撞击**推迟**到文件真正
进入 index 的那一刻。
"""
import pathlib
import subprocess
import sys

MIRRORS = (".kiro", ".agents")
SKILLS_DIR = ".claude/skills"


def _git(repo_root, *args):
    """在 repo_root 上跑一条 git 命令，返回 CompletedProcess。"""
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def is_ignored(repo_root, rel_path):
    """该路径是否被 .gitignore 排除，**不受 index 影响**。

    --no-index 的必要性见模块 docstring。退出码 0 = 被忽略，1 = 未被忽略，
    其余（如 128）视为未被忽略——判不出来时宁可多查一个目录，也不要静默漏查。
    """
    return _git(repo_root, "check-ignore", "-q", "--no-index", rel_path).returncode == 0


def distributed_skills(repo_root, ignored=None):
    """列出「由本仓分发、因此必须有镜像」的 skill 名，已排序。

    ignored 是一个 rel_path -> bool 的判定函数，默认走 git；单测传入替身可以
    只测选择逻辑，但**默认路径必须被真 git 覆盖**——本脚本要修的那个 bug 就在
    git 的行为里，把它替换掉的测试抓不到它。
    """
    if ignored is None:
        ignored = lambda rel: is_ignored(repo_root, rel)  # noqa: E731

    base = pathlib.Path(repo_root) / SKILLS_DIR
    if not base.is_dir():
        return []

    names = []
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        if not (d / "SKILL.md").is_file():      # 排除理由 (一)
            continue
        if ignored(f"{SKILLS_DIR}/{d.name}"):   # 排除理由 (二)
            continue
        names.append(d.name)
    return names


def check_forward(repo_root, ignored=None):
    """每个分发的 skill 在两处镜像目录都要有同名条目。"""
    problems = []
    for name in distributed_skills(repo_root, ignored):
        for mirror in MIRRORS:
            rel = f"{mirror}/skills/{name}"
            if not (pathlib.Path(repo_root) / rel).exists():
                problems.append(
                    f"缺符号链接 {rel}"
                    f"（补齐：ln -s ../../{SKILLS_DIR}/{name} {rel}）")
    return problems


def check_reverse(repo_root):
    """镜像指向已不存在的 skill。

    ⚠️ 这里不能用 exists()——悬空符号链接的 exists() 为假，而悬空正是要检出的形态。
    改为直接遍历目录项、只按名字反查源目录是否还在。
    """
    problems = []
    root = pathlib.Path(repo_root)
    for mirror in MIRRORS:
        base = root / mirror / "skills"
        if not base.is_dir():
            continue
        for m in sorted(base.iterdir()):
            if not (root / SKILLS_DIR / m.name).is_dir():
                problems.append(
                    f"{mirror}/skills/{m.name} 指向已不存在的 {SKILLS_DIR}/{m.name}"
                    f"（清理：git rm {mirror}/skills/{m.name}）")
    return problems


def bad_modes(ls_files_output):
    """从 `git ls-files -s` 输出里挑出未以 120000 模式入库的行。

    拆成纯函数是为了让「模式位判定」这一层可被单测直接覆盖——造一个
    core.symlinks=false 的真实仓库代价过高，而这一层要判的只是文本。
    """
    return [ln for ln in ls_files_output.splitlines()
            if ln.strip() and not ln.startswith("120000 ")]


def check_modes(repo_root):
    mirror_paths = [f"{m}/skills" for m in MIRRORS]
    out = _git(repo_root, "ls-files", "-s", *mirror_paths).stdout
    bad = bad_modes(out)
    if not bad:
        return []
    return ["以下镜像未以 symlink 模式入库（应为 120000）：\n"
            + "\n".join("      " + ln for ln in bad)]


def check_all(repo_root, ignored=None):
    return (check_forward(repo_root, ignored)
            + check_reverse(repo_root)
            + check_modes(repo_root))


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    problems = check_all(root)
    if problems:
        print("skill 镜像校验未通过：")
        for p in problems:
            print(f"  - {p}")
        return 1
    n = len(distributed_skills(root))
    print(f"skill 镜像校验通过：{n} 个分发的 skill 在两处镜像齐备")
    return 0


if __name__ == "__main__":
    sys.exit(main())
