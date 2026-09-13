#!/usr/bin/env python3
"""检查本次改动新增的 skill 是否都带了 eval case。

只由 CI 调用（.github/workflows/ci.yml 的 new-skill-eval-case job），
**不挂进 pre-commit**：它需要两个 ref 之间的 diff，而 pre-commit 必须保持
暂存区无关——gates-hooks job 逐字执行 `sh .githooks/pre-commit`，一旦
pre-commit 引入依赖暂存区的检查，那份复用就失效（见 .githooks/README.md）。

⚠️ 文件名全程在 Python 内解析，不经 shell、不用 xargs。本仓的必需检查
不跳过 fork PR，而 fork 的文件名不可信；官方 validate-frontmatter.yml
正是靠跳过 fork 来回避这个风险，本仓不跳过，因此必须在实现层消除。

判据见 docs/superpowers/specs/2026-09-13-pr-flow-and-free-ci-design.md § 5.7。
"""
import pathlib
import subprocess
import sys

# 官方发现规则：eval 目录在 skill 文件夹下，默认名 evals/
EVAL_DIR = "evals"
# 一个子目录被认作 case 的标志（官方两种等价写法）
CASE_MARKERS = ("case.yaml", "prompt.md")


def added_files(base, head, repo_root="."):
    """取 base...head 之间**新增**（status=A）的文件，posix 相对路径列表。

    --diff-filter=A 是这里的要点：只看新增的文件，修改已有 skill 不触发。
    这是「新增必须带 case，存量不回溯」的机械表达。官方
    validate-frontmatter.yml 用 AMRC（排除删除），因为它要校验改动过的
    文件；本门禁语义不同，只要 A。
    """
    proc = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=A", f"{base}...{head}"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    return [line for line in proc.stdout.splitlines() if line]


def new_skill_dirs(paths):
    """从新增文件里筛出新增 skill 的目录。

    只认 plugins/<plugin>/skills/<skill>/SKILL.md 这一形态（恰好 5 段）：
    - .claude/skills/ 下的是本仓自用维护型 skill，不对外发布，不要求 case
    - external_plugins/ 下的是拷贝自上游的内容，替上游造 case 不合理
    - plugins/*/agents/ 是 agent，没有 eval case 的概念
    """
    out = []
    for p in paths:
        parts = pathlib.PurePosixPath(p).parts
        if (len(parts) == 5
                and parts[0] == "plugins"
                and parts[2] == "skills"
                and parts[4] == "SKILL.md"):
            out.append("/".join(parts[:4]))
    return out


def has_eval_case(repo_root, skill_dir):
    """skill_dir/evals/ 下是否有任一**子目录**含 case.yaml 或 prompt.md。

    判据是「子目录里有标志文件」而非「evals/ 非空」：官方按
    <eval dir>/**/case.yaml 发现 case，散落在 evals/ 根下的文件不构成
    case。本仓 trigger-eval.json 就是那种形态——文件在 evals/ 下，
    而 claude plugin eval 找到 0 个 case。
    """
    evals = pathlib.Path(repo_root) / skill_dir / EVAL_DIR
    if not evals.is_dir():
        return False
    for sub in sorted(evals.iterdir()):
        if sub.is_dir() and any((sub / m).is_file() for m in CASE_MARKERS):
            return True
    return False


def check(base, head, repo_root="."):
    """返回 (缺 case 的 skill 目录列表, 检查过的新增 skill 数)。"""
    skill_dirs = new_skill_dirs(added_files(base, head, repo_root))
    missing = [d for d in skill_dirs if not has_eval_case(repo_root, d)]
    return missing, len(skill_dirs)


def main():
    if len(sys.argv) < 3:
        print("用法：check_new_skill_eval_case.py <base-ref> <head-ref> "
              "[repo-root]")
        return 2
    base, head = sys.argv[1], sys.argv[2]
    root = sys.argv[3] if len(sys.argv) > 3 else "."

    missing, checked = check(base, head, root)
    if missing:
        print("新增 skill 缺少 eval case：")
        for d in missing:
            print(f"  - {d}")
            print(f"      需要 {d}/{EVAL_DIR}/<case-name>/prompt.md"
                  f"（或 case.yaml）")
        print("  可参照的样本："
              "plugins/optimus-devops-plugin/skills/jenkins-build/evals/")
        print("  判据见 docs/superpowers/specs/"
              "2026-09-13-pr-flow-and-free-ci-design.md § 5.7")
        return 1

    if checked:
        print(f"新增 skill 的 eval case 齐备：已检查 {checked} 个")
    else:
        print("本次改动无新增 skill，跳过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
