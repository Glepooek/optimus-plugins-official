#!/usr/bin/env python3
"""检查 eval case 的两件事，两种模式各自独立。

**增量模式**（`<base-ref> <head-ref>`）：本次改动新增的 skill 是否都带了
eval case。只由 CI 调用（.github/workflows/ci.yml 的 new-skill-eval-case
job），**不挂进 pre-commit**：它需要两个 ref 之间的 diff，而 pre-commit 必须
保持暂存区无关——gates-hooks job 逐字执行 `sh .githooks/pre-commit`，一旦
pre-commit 引入依赖暂存区的检查，那份复用就失效（见 .githooks/README.md）。

**全量模式**（`--all`）：已有的 case 目录有没有建了一半的。它不看 diff，
因此**可以且已经挂进 pre-commit**，同时也在 CI 里跑。

⚠️ 两种模式查的不是同一件事，缺一不可：
  增量模式只在**新增 SKILL.md** 时触发，所以「给存量 skill 补 case 但补错
  形态」完全落在它的射程外——单测
  test_adding_eval_case_to_existing_skill_is_not_a_new_skill 明确锁定了这条
  放行。全量模式补的正是这个缺口。

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


def malformed_case_dirs(repo_root="."):
    """全量扫描：返回 (不合格的 case 目录列表, 扫过的 case 目录总数)。

    判据是「evals/ 下**每个**子目录都含 case.yaml 或 prompt.md」，与
    has_eval_case 的「**任一**子目录合格即可」刻意不同——后者回答「这个 skill
    有没有 case」，本函数回答「有没有哪个 case 只建了一半」。

    🔴 两者不能互相取代：一个 evals/ 下有 3 个子目录、其中 2 个合格 1 个缺
    marker 时，has_eval_case 返回 True，而 claude plugin eval 会**静默少跑
    那一个 case**——总数只出现在 verbose 输出里，日常读到的是「跑完了、全绿」。
    这正是本仓反复撞到的那类形态：少查一件事与全部通过，在退出码上不可区分。

    ⚠️ 只扫 plugins/*/skills/*/evals/，与 new_skill_dirs 的范围一致：
      .claude/skills/ 不对外发布、external_plugins/ 是上游拷贝。

    ⚠️ **不判定「有 evals/ 却一个合格子目录都没有」**，尽管那正是
    plugins/optimus-frontend-plugin/skills/wpf-code-review/evals/ 的现状
    （只有一个散落的 evals.json，claude plugin eval 在它上面找到 0 个 case）。
    原因是那不是错误，而是**另一套规范的合规产物**：
    knowledge-base/skill-authoring/rules/03-skill-evaluation.md 有一条 MUST
    「测试用例存到 evals/evals.json」，并配 reference/eval-workspace-structure.md
    描述整个工作区。本仓因此有两套 eval 规范并存，谁服从谁需要人裁决——
    已登记 docs/todo-list/2026-09-12-todo.md 的 A4。**在裁决前把它判失败，
    等于用一个门禁替人做了规范取舍。**
    """
    root = pathlib.Path(repo_root)
    bad, total = [], 0
    for evals in sorted(root.glob(f"plugins/*/skills/*/{EVAL_DIR}")):
        if not evals.is_dir():
            continue
        for sub in sorted(evals.iterdir()):
            if not sub.is_dir():
                continue
            total += 1
            if not any((sub / m).is_file() for m in CASE_MARKERS):
                bad.append(sub.relative_to(root).as_posix())
    return bad, total


def main_all(repo_root="."):
    bad, total = malformed_case_dirs(repo_root)
    if bad:
        print("以下 eval case 目录缺 case.yaml 或 prompt.md：")
        for d in bad:
            print(f"  - {d}")
        print("  这样的目录会被 claude plugin eval 静默忽略——它不报错，"
              "只是少跑一个 case。")
        print("  判据与文件形态见 docs/superpowers/specs/"
              "2026-09-13-pr-flow-and-free-ci-design.md § 5.9.1")
        return 1
    print(f"eval case 目录校验通过：已检查 {total} 个")
    return 0


def main():
    # 全量模式：不需要 diff，因此挂在 pre-commit 上也不违反暂存区无关性
    if len(sys.argv) >= 2 and sys.argv[1] == "--all":
        return main_all(sys.argv[2] if len(sys.argv) > 2 else ".")

    if len(sys.argv) < 3:
        print("用法：check_new_skill_eval_case.py <base-ref> <head-ref> "
              "[repo-root]")
        print("　　　check_new_skill_eval_case.py --all [repo-root]")
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
        print("  判据与文件形态见 docs/superpowers/specs/"
              "2026-09-13-pr-flow-and-free-ci-design.md § 5.7、§ 5.9.1")
        return 1

    if checked:
        print(f"新增 skill 的 eval case 齐备：已检查 {checked} 个")
    else:
        print("本次改动无新增 skill，跳过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
