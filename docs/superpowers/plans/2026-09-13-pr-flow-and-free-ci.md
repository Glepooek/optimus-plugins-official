# 主干走 PR + 零成本 CI 门禁 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让本仓库的主干只能经 PR 合入，并用五个零 token 的必需检查把既有门禁、单测、官方静态校验和「新增 skill 必须带 eval case」变成服务端强制的合并条件。

**Architecture:** 三层。**服务端** GitHub ruleset 禁止直推、要求 5 个必需检查（已配好禁直推，必需检查待 CI 跑过后勾选加回）；**CI 层** `.github/workflows/ci.yml` 五个并行 job，全部零凭据、无 `paths:` 过滤，其中三个 job 逐字复用 `.githooks/` 下已有脚本而不复制逻辑；**行为层** `skill-eval.yml` 仅手动触发，是唯一会产生费用的入口。提交流程侧把 `commit-cc-plugin` 的第五步从直推改写为「建分支 → PR → 等 CI → squash merge」。

**Tech Stack:** GitHub Actions（`actions/checkout@v5`、`actions/setup-python@v6`）、官方 composite action `anthropics/claude-plugins-community/.github/actions/validate-plugins`、`claude` CLI 2.1.270、Python 3 标准库（`unittest`、`subprocess`，**本机无 pytest**）、GitHub MCP（`create_pull_request` / `pull_request_read` / `merge_pull_request`）。

**Spec:** `docs/superpowers/specs/2026-09-13-pr-flow-and-free-ci-design.md`（已评审通过，合入 master：#1 `50e6fb6` → #2 `1a90123` → #3 `7db64b1`）

## Global Constraints

这些约束对**每一个** task 都生效，不在各 task 内重复。

### 提交与推送（本次交付起全程适用）

- **主干已锁，直推被服务端以 `GH013` 拒绝。** 每个 task 的提交都必须走 PR：`git switch -c <type>/<描述>` → 提交 → `git push -u origin <branch>` → MCP `create_pull_request` → MCP `merge_pull_request`（`merge_method: "squash"`）。
- **`commit-cc-plugin` 在 Task 8 完成前尚未改造**，因此 Task 1–7 的 PR 流程**由执行者手工执行**，不要调用该 skill（它的第五步仍是直推，会撞 `GH013`）。
- **squash merge 必须显式传 `commit_title` 与 `commit_message`**：前者自带 `(#N)` 后缀（GitHub 在传了 `commit_title` 时不再自动追加），后者含 `Co-Authored-By` 尾注（否则 squash 会丢弃它）。
- **清分支顺序是硬约束**：先 `git branch -d <branch>`，再 `git push origin --delete <branch>`。反了会撞 `not fully merged`（`-d` 的已合并判定也看远端追踪引用）。
- commit message 结尾：`Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`
- PR 描述结尾：`🤖 Generated with [Claude Code](https://claude.com/claude-code)`

### 禁止事项

- **禁止 `--no-verify`。** `pre-commit` 阻断说明仓库一致性真的坏了，按报错修因。
- **禁止 force push**（`--force` / `-f`）。push 失败最多重试一次，仍失败则报告。
- **禁止 `git add -A`。** 逐文件暂存。
- `git stash push` **必须列出具体文件路径**，裸 `git stash` 会把工作区全部改动一起挪走。
- **`.claude/settings.json` 一律不纳入任何提交**（未跟踪，版本控制归属未决，spec § 10 风险 6）。

### 环境

- **`git commit` 给 300000 ms 超时**：本机 Windows 上 `pre-commit` 可能超过默认的 120 s，超时会被误判为失败。
- 单元测试只能用 `unittest`，**本机无 `pytest`**：`python -m unittest discover -s <dir> -p "test_*.py"`。
- `unittest discover` **不跨目录递归**，9 个测试目录必须逐个调用。
- 本机 Bash 工具是 Git Bash；PowerShell 亦可用。**`rm -rf` 在本会话被拒过**，删目录用 PowerShell `Remove-Item -Recurse -Force -Confirm:$false`。

### CI 设计的三条红线（违反会锁死主干或产生费用）

- 🔴 **`skill-eval` 绝对不进必需检查列表。** 它只有 `workflow_dispatch` 触发，进了必需检查就是一项永久 `Expected — Waiting for status to be reported`，主干双向锁死；它也是唯一收费的 job。**这件事已真实发生过一次**（spec § 4.2 其四）。
- 🔴 **必需检查一律不设 `paths:` 过滤器。** 未命中 `paths:` 的 PR 会让该检查永久停在 Expected，且 `workflow_dispatch` 的 check run 不关联 PR、手动跑一次也救不了（spec § 3.4.1，官方为此打了至少 5 次补丁）。
- 🔴 **`claude plugin eval` 的 `--no-publish` 恒开。** HTML 报告默认发布到 claude.ai，而本仓 case 含内部 Jenkins job 名。同时**不开 `--scaffold`**（会执行 case 作者提供的 bash）、**不开 `--allow-real-servers`**（会在 OS 沙箱外起真实 MCP 服务器）。

### 固定取值（不得改动，不得用默认值代替）

| 项 | 值 | 原因 |
|---|---|---|
| composite action ref | `426e469f322952061102b286b378c0c9733a0934` | 40 位 SHA-pin，冻结校验逻辑 |
| `claude-cli-version` | `2.1.270` | **该 input 默认是 `latest`**，不覆盖等于接受漂移；且 spec § 3.1「零存量债务」基线正是用 2.1.270 量的 |
| `base-ref` | `${{ github.event.pull_request.base.sha }}`（**仅 `ci.yml`**） | **默认值是 `origin/main`**，本仓默认分支是 `master`。⚠️ `skill-eval.yml` 是 `workflow_dispatch` 事件、**拿不到这个表达式**，那里传 `${{ github.sha }}`，理由见 Task 4 |
| `fail-on-warnings` | `"true"` | 等价 `--strict`；不开则缺 `description` 只是 warning |
| `scope-errors-to-changed` | `"false"` | 默认值即所需，**显式写出以留痕「刻意选了严格档」** |
| `permissions` | `contents: read` | 最小权限 |
| 5 个必需检查 job 名 | `gates-hooks`、`gates-tests`、`gates-data`、`plugin-validate`、`new-skill-eval-case` | 同时被 `ci.yml` 与服务端 ruleset 引用，**改名会静默失去保护**（spec § 10 风险 2） |

---

## 文件结构

### 新建

| 文件 | 单一职责 |
|---|---|
| `.githooks/check_new_skill_eval_case.py` | 给定 base/head 两个 ref，判定本次改动新增的 SKILL.md 是否都带了 eval case。**只由 CI 调用**，不进 `pre-commit` 序列 |
| `.githooks/test_check_new_skill_eval_case.py` | 上者的单测 |
| `.github/workflows/ci.yml` | 五个零 token 必需 job |
| `.github/workflows/skill-eval.yml` | 手动行为闸，唯一收费入口 |
| `plugins/optimus-devops-plugin/skills/jenkins-build/evals/<20 个 case 目录>/prompt.md` | 每条 query 一个 case 的提问 |
| `plugins/optimus-devops-plugin/skills/jenkins-build/evals/<同上>/graders/triggered.md` | 每个 case 的触发判据（正例 `min: 1`，负例 `max: 0`） |

**为什么 diff 检查脚本放 `.githooks/` 却不挂进 `pre-commit`：** `.claude/rules/hook-conventions.md` 约定「仓库级门禁必须放 `.githooks/`」，故位置遵守该约定；但它需要两个 ref 之间的 diff，而 `gates-hooks` 要求 `pre-commit` 保持**暂存区无关**（见下）。解法是脚本接受 base/head 作参数、只由 CI 调用，两个约定都不破。

### 修改

| 文件 | 改什么 |
|---|---|
| `.claude/skills/commit-cc-plugin/SKILL.md` | 第一步加分支判定、第三步上游改判、第四步前建分支、第五步整节重写为 PR 流程、常见错误表补 4 条 |
| `AGENTS.md` | 「提交与推送」节重写（5 条）+ 版本触发矩阵补 2 行 |
| `.githooks/README.md` | 暂存区无关性约定、CI 第二执行点、新门禁登记 |
| `knowledge-base/git/rules/03-pull-requests.md` | `:25` 拆成两条（**经 `knowledge-base-maintain`**） |
| `knowledge-base/git/rules/01-branching.md` | `:17` 括号枚举、`:18` 示例（**经 `knowledge-base-maintain`**） |
| `plugins/optimus-devops-plugin/.claude-plugin/plugin.json` | `version` `1.1.17` → `1.2.0` |
| `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` | `version` `1.1.17` → `1.2.0`（**与上者同值同次提交**） |
| `plugins/optimus-devops-plugin/skills/jenkins-build/SKILL.md` | `metadata.version` `"1.2.2"` → `"1.3.0"` |
| `docs/todo-list/2026-09-12-todo.md` | 标记该条目已裁决，指向 spec |

### 删除

| 文件 | 前置条件 |
|---|---|
| `plugins/optimus-devops-plugin/skills/jenkins-build/evals/trigger-eval.json` | **必须先逐条核对 20 条 query 全部落地**。删在前、漏在后就是静默丢素材 |

### 关键的现状事实（实现时依赖，已实测）

- `.github/` 目录**当前不存在**，从零建立。
- `.githooks/pre-commit` **全程未使用 `git diff --cached`**，六项检查全部基于工作树与 `git ls-files` ⇒ CI 可以 `sh .githooks/pre-commit` 逐字执行。**这条性质必须保持**，否则 `gates-hooks` 的复用即失效。
- 9 个测试目录全部存在，共 22 个 `test_*.py`。
- `gates-data` 的三个脚本全部存在且当前无存量债务（790 条索引 / 284 个引用 / 250 条 tips 全绿）。
- `jenkins-build` 的 `allowed-tools: Bash` —— 该 skill 被触发后会调真实 Jenkins API，**这决定了 eval case 的 `allowed_tools` 不能给 Bash**（见 Task 5）。
- ruleset id `23134670`，当前 `required_status_checks` **已被整条移除**，`bypass_actors: null`。读取无需认证：`GET /repos/Glepooek/optimus-plugins-official/rulesets/23134670`。
- 全仓 56 个 `SKILL.md`，**全部是 4 段（`.claude/skills/<name>/SKILL.md`）或 5 段（`plugins/<plugin>/skills/<skill>/SKILL.md`）**，无嵌套或复合 skill 的 SKILL.md，`external_plugins/` 下当前无 SKILL.md。这决定了 Task 1 的路径匹配可以严格取 5 段。

---

## Task 1: `check_new_skill_eval_case.py` —— 「新增 skill 必须带 eval case」门禁

**Files:**
- Create: `.githooks/check_new_skill_eval_case.py`
- Create: `.githooks/test_check_new_skill_eval_case.py`
- Modify: `.githooks/README.md`（只加「新门禁登记」，另两条约定在 Task 9）

**Interfaces:**
- Consumes: 无（第一个 task）
- Produces: 供 Task 2 的 `new-skill-eval-case` job 调用的 CLI —— `python .githooks/check_new_skill_eval_case.py <base-ref> <head-ref> [repo-root]`，退出码 0=通过 / 1=有缺失 / 2=用法错。Python API：`added_files(base, head, repo_root=".") -> list[str]`、`new_skill_dirs(paths: list[str]) -> list[str]`、`has_eval_case(repo_root, skill_dir: str) -> bool`、`check(base, head, repo_root=".") -> tuple[list[str], int]`（返回 `(缺 case 的 skill 目录列表, 检查过的新增 skill 数)`）。

**为什么先做这个 task：** 它是 Task 2 里 `new-skill-eval-case` job 的唯一依赖，且**能在本机完整测通**——不需要等 CI 存在。把唯一有实质逻辑的新代码放在第一位，后续 task 就都是配置与文档。

- [ ] **Step 1: 写失败的测试**

Create `.githooks/test_check_new_skill_eval_case.py`：

```python
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest discover -s .githooks -p "test_check_new_skill_eval_case.py" -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'check_new_skill_eval_case'`

- [ ] **Step 3: 写实现**

Create `.githooks/check_new_skill_eval_case.py`：

```python
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest discover -s .githooks -p "test_check_new_skill_eval_case.py" -v`
Expected: PASS，21 个用例全绿

- [ ] **Step 5: 跑 `.githooks` 全量测试，确认没破坏既有门禁**

Run: `python -m unittest discover -s .githooks -p "test_*.py"`
Expected: PASS。基线是 18（`check_plugin_versions`）+ 21（`check_hook_configs`）+ 85（`check_external_entries`）= 124 个，加本 task 的 21 个 ⇒ **145 个**

- [ ] **Step 6: 在本仓真实历史上跑一次，确认无误报**

Run: `python .githooks/check_new_skill_eval_case.py 50e6fb6 HEAD`
Expected: `本次改动无新增 skill，跳过`，退出码 0

⚠️ 这一步是**阳性对照的反面**：它证明脚本在真实历史上不误报。验收第 5 项的阴性对照（造一个真会红的 PR）在 Task 7。

- [ ] **Step 7: 在 `.githooks/README.md` 登记新门禁**

`AGENTS.md` 要求新增门禁**脚本 + 测试 + 文档三件齐备**，因此登记跟着脚本一起提交，不留到 Task 10。

在「检查项」表格后、`python -m unittest discover` 代码块**之前**插入一段：

```markdown
### 不挂在 pre-commit 上的门禁

`check_new_skill_eval_case.py`（21 个单元测试）检查「新增 skill 是否带了 eval case」：从 `git diff --diff-filter=A base...head` 取新增文件，筛出 `plugins/<plugin>/skills/<skill>/SKILL.md`，要求同目录下 `evals/` 有子目录含 `case.yaml` 或 `prompt.md`。缺失即失败并给出应建的路径。

**它不在上面那张表里，因为它不由 `pre-commit` 调用**——它需要两个 ref 之间的 diff，而 `pre-commit` 必须保持暂存区无关（原因见「与 CI 的关系」）。它接受 base/head 两个 ref 作参数，只由 `.github/workflows/ci.yml` 的 `new-skill-eval-case` job 调用。位置仍放 `.githooks/` 是遵守 `.claude/rules/hook-conventions.md` 的「仓库级门禁必须放 `.githooks/`」。

⚠️ 文件名全程在 Python 内解析，**不经 shell、不用 `xargs`**：本仓的必需检查不跳过 fork PR，而 fork 的文件名不可信。
```

⚠️ 「与 CI 的关系」一节在 Task 9 才写入。**这里先引用它是刻意的**——两处改动属于同一件事的两半，Task 1 只装脚本自己的那一半。若执行 Task 1 时想让文档自洽，可把该引用改为「见 spec § 5.3」，Task 9 Step 5 再改回。

- [ ] **Step 8: 走 PR 提交**

```bash
git switch -c feat/new-skill-eval-case-gate
git add .githooks/check_new_skill_eval_case.py
git add .githooks/test_check_new_skill_eval_case.py
git add .githooks/README.md
git diff --staged --stat
```

确认只有 3 个文件、**不含 `.claude/settings.json`**，然后提交（**超时给 300000 ms**）：

```bash
git commit -m "$(cat <<'EOF'
feat(githooks): 新增「新增 skill 必须带 eval case」门禁

- check_new_skill_eval_case.py：从 --diff-filter=A 取新增文件，筛出
  plugins/*/skills/*/SKILL.md，要求同目录 evals/ 下有子目录含
  case.yaml 或 prompt.md；缺失时给出应建路径与可参照样本
- 只由 CI 调用、不进 pre-commit 序列：它需要两个 ref 的 diff，而
  pre-commit 必须保持暂存区无关（CI 逐字复用它）
- 文件名全程在 Python 内解析，不经 shell/xargs——必需检查不跳过
  fork PR，fork 的文件名不可信
- 21 个单元测试，其中 6 个用真 git 仓库验证 --diff-filter=A 的语义
  （「修改已有 skill 不触发」是核心承诺，mock 掉 git 就测不出）
- .githooks/README.md 登记该门禁并说明它为何不在 pre-commit 表里

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

验证 message 无字面 `\n`（必须无输出）：

```bash
git show -s --format=%B HEAD | grep -F '\n'
```

推送并开 PR：

```bash
git push -u origin feat/new-skill-eval-case-gate
```

用 MCP `create_pull_request`（`base: master`、`head: feat/new-skill-eval-case-gate`），PR body 说明三件事：脚本职责、为何不进 `pre-commit`、fork 文件名处置。⚠️ **此时 `.github/` 还不存在，所以这个 PR 没有 CI 可等**，`mergeable_state` 应直接为 `clean`。

用 MCP `merge_pull_request` 合并（`merge_method: "squash"`，`commit_title` 自带 `(#N)`，`commit_message` 含 `Co-Authored-By`），然后：

```bash
git switch master && git pull --rebase origin master
git branch -d feat/new-skill-eval-case-gate
git push origin --delete feat/new-skill-eval-case-gate
```

---

## Task 2: `.github/workflows/ci.yml` —— 五个零 token 必需检查

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: Task 1 的 `python .githooks/check_new_skill_eval_case.py <base> <head>`
- Produces: 五个 check run，名字**逐字**为 `gates-hooks`、`gates-tests`、`gates-data`、`plugin-validate`、`new-skill-eval-case`。Task 3 要按这五个名字在 GitHub UI 勾选必需检查

**实测前提（已核实，不要重新推导）：**

| 事实 | 值 |
|---|---|
| `.githooks/pre-commit` 是否依赖暂存区 | ❌ 不依赖，六项检查全基于工作树与 `git ls-files` ⇒ 可 `sh` 直接跑 |
| 三个 data 脚本的调用方式 | 从**仓库根不带参数**运行，当前均退出 0（790 条索引 / 284 个引用 / tips 九项全绿） |
| `validate_tips.py` 的 `length` 检查 | 报出 `over_count: 18` 但 `ok=True` —— **它只报告不判失败**。因此 18 个存量长条目**不会**让 CI 红，`gates-data` 设为硬失败是安全的 |
| 9 个测试目录 | 全部存在，共 22 个 `test_*.py` |

⚠️ **最后一条是 `gates-data` 能设硬失败的真正原因**，而不是「碰巧没有存量债务」：`validate_tips.py` 把「全库现状」与「本次改动是否把某条推超阈值」分成了两件事，只有后者判失败。不查这一步就写这个 job，会在将来某次新增 tips 后撞上一个看似与改动无关的红灯。

- [ ] **Step 1: 创建 `.github/workflows/ci.yml`**

```yaml
# 本仓库的必需检查（required status checks）。
#
# 🔴 下面五个 job 的名字同时被本文件与 GitHub 服务端 ruleset（id 23134670）
#    引用，而后者不在版本库里、改动不留 diff。改名必须同步改 ruleset，否则
#    那项检查会静默不再被要求——属「不报错的失效形态」。五个名字：
#      gates-hooks / gates-tests / gates-data / plugin-validate / new-skill-eval-case
#
# 🔴 一律不设 paths: 过滤器。必需检查加 paths: 会让未命中的 PR 永久停在
#    "Expected — Waiting for status to be reported"，而 workflow_dispatch 的
#    check run 不关联 PR、手动跑一次也救不了。官方 claude-plugins-official
#    为此打了至少 5 次补丁（其 validate-plugins.yml 的 paths: 长达 40 行）。
#
# 🔴 skill-eval 不在这里。它是唯一收费的 job、只有 workflow_dispatch 触发，
#    见 .github/workflows/skill-eval.yml。把它加进必需检查会让主干双向锁死
#    （已真实发生过一次）。
#
# 不跳过 fork PR：五个检查全部零凭据，fork 场景照样跑通。跳过会让 fork PR
# 的必需检查永久 Expected。
#
# 设计判据全文见
# docs/superpowers/specs/2026-09-13-pr-flow-and-free-ci-design.md § 5

name: CI

on:
  pull_request:
    branches: [master]

permissions:
  contents: read

jobs:
  # ---------------------------------------------------------------------------
  # 逐字执行本地门禁，不在 YAML 里重写一份逻辑。
  # pre-commit 靠 `git config core.hooksPath .githooks` 本机启用、不随仓库
  # 分发，因此它在任何未做该配置的环境中从未生效过。搬进 CI 后这批门禁
  # 第一次有了不依赖本机配置的执行点。
  # ---------------------------------------------------------------------------
  gates-hooks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          # ubuntu runner 默认只有 python3，pre-commit 里调的是 python
          python-version: '3.x'
      - run: sh .githooks/pre-commit

  # ---------------------------------------------------------------------------
  # unittest discover 不跨目录递归，9 个目录必须逐个调用。
  # 用循环而非 9 个 step：新增测试目录时只改一处，且失败时不必翻九个折叠块。
  # ---------------------------------------------------------------------------
  gates-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.x'
      - name: 9 个目录的单元测试
        run: |
          fail=0
          for d in \
            .githooks \
            .claude/skills/knowledge-base-maintain/scripts \
            .claude/skills/sync-cc-docs-to-youdaonote/scripts \
            .claude/skills/sync-cc-tips/scripts \
            plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts \
            plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/scripts \
            plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/scripts \
            plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts \
            plugins/optimus-mcp-servers/scripts
          do
            echo "::group::$d"
            python -m unittest discover -s "$d" -p "test_*.py" || fail=1
            echo "::endgroup::"
          done
          exit "$fail"

  # ---------------------------------------------------------------------------
  # 数据文件一致性。三项均从仓库根不带参数运行。
  # ⚠️ validate_tips.py 的 length 检查只报告不判失败（当前 over_count=18 而
  #    ok=true），所以存量长条目不会让本 job 红——硬失败是安全的。
  # ---------------------------------------------------------------------------
  gates-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.x'
      - run: python .claude/skills/knowledge-base-maintain/scripts/check_index.py
      - run: python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
      - run: python .claude/skills/sync-cc-tips/scripts/validate_tips.py

  # ---------------------------------------------------------------------------
  # 官方静态校验。不自己写 npm i -g：claude-code 把运行时作为平台原生
  # optional dependency 由 postinstall 抓取，在 hosted runner 上会间歇性
  # stall 或被跳过，留下「added 1 package」但没有可用的 claude 二进制。
  # 官方 composite action 内已有 40 行自愈逻辑（强制 optional 依赖、每步
  # 超时、重试前清包目录与 cache、postinstall 兜底）。
  # ---------------------------------------------------------------------------
  plugin-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0          # action 的 detect-changes 需要完整历史
      - uses: anthropics/claude-plugins-community/.github/actions/validate-plugins@426e469f322952061102b286b378c0c9733a0934
        with:
          marketplace-path: .claude-plugin/marketplace.json
          # ⚠️ 该 input 默认值里是 origin/main，本仓默认分支是 master
          base-ref: ${{ github.event.pull_request.base.sha }}
          # 等价于 --strict：不开则缺 description 只是 warning，而缺
          # description 的 skill 在 Claude 侧等于永不被自动触发
          fail-on-warnings: "true"
          # 默认值就是 false；显式写出以留痕「刻意选了严格档」——依赖一个
          # 不在眼前的默认值来维持严格性，等于把门禁强度交给上游下次改动
          scope-errors-to-changed: "false"
          # ⚠️ 该 input 默认是 latest，不覆盖就等于接受版本漂移。取 2.1.270
          # 是因为「本仓零存量债务」这条基线正是用它量出来的
          claude-cli-version: "2.1.270"
      # 补 action 的盲区：它按「含 .claude-plugin/plugin.json 的祖先目录」
      # 定位插件，而 .claude/skills/ 不属任何插件，完全不在其扫描范围内。
      # claude 已由 action 装到 runner 全局，同 job 后续 step 直接可用。
      - run: claude plugin validate .claude/skills --strict

  # ---------------------------------------------------------------------------
  # 「新增 skill 必须带 eval case」。纯静态 diff 检查，零 token——强制 case
  # 存在，但不在 CI 里运行 case（运行成本是机制内在的）。
  # ---------------------------------------------------------------------------
  new-skill-eval-case:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0          # 需要 base 与 head 之间的完整 diff
      - uses: actions/setup-python@v6
        with:
          python-version: '3.x'
      # 两个 sha 经 env 传入而非直接插值进 run：sha 本身不可控，但保持
      # 「不做 shell 插值」的一贯做法，与脚本内不经 shell 解析文件名同源
      - env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: python .githooks/check_new_skill_eval_case.py "$BASE_SHA" "$HEAD_SHA"
```

- [ ] **Step 2: 本机预演三个能预演的 job**

CI 首跑前先在本机把能跑的跑一遍，把「YAML 写错」与「Linux 行为差异」两类失败分开。**这一步不能证明 CI 会绿**（Linux 与 Windows 有差异，正是验收第 1 项要测的），但能挡掉命令写错。

```bash
sh .githooks/pre-commit
python .claude/skills/knowledge-base-maintain/scripts/check_index.py
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
python .claude/skills/sync-cc-tips/scripts/validate_tips.py > /dev/null && echo "tips OK"
```

Expected: 全部退出 0

- [ ] **Step 3: 本机预演 `gates-tests` 的循环体**

```bash
fail=0
for d in \
  .githooks \
  .claude/skills/knowledge-base-maintain/scripts \
  .claude/skills/sync-cc-docs-to-youdaonote/scripts \
  .claude/skills/sync-cc-tips/scripts \
  plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts \
  plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-components/scripts \
  plugins/optimus-frontend-plugin/skills/mastergo-to-wpf-page/scripts \
  plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts \
  plugins/optimus-mcp-servers/scripts
do
  echo "=== $d"
  python -m unittest discover -s "$d" -p "test_*.py" || fail=1
done
echo "汇总退出码: $fail"
```

Expected: `汇总退出码: 0`

⚠️ **不能预演的两个 job**：`plugin-validate` 依赖 composite action（只在 Actions 环境可用），`new-skill-eval-case` 依赖 PR 事件的两个 sha。前者的等效本机验证是 spec § 3.1 第 6 条已做过的全量 `--strict`；后者在 Task 1 Step 6 已用真实 ref 跑过。

- [ ] **Step 4: 走 PR 提交 —— 这个 PR 就是 CI 的首次运行**

```bash
git switch -c feat/ci-required-checks
git add .github/workflows/ci.yml
git diff --staged --stat
```

确认只有 1 个文件，然后提交（**超时 300000 ms**）：

```bash
git commit -m "$(cat <<'EOF'
feat(ci): 新增五个零 token 的必需检查

- gates-hooks：逐字执行 sh .githooks/pre-commit。该 hook 靠本机
  core.hooksPath 启用、不随仓库分发，搬进 CI 后这批门禁第一次有了
  不依赖本机配置的执行点
- gates-tests：循环遍历 9 个测试目录（unittest discover 不跨目录递归）
- gates-data：check_index / check_refs / validate_tips 三项一致性
- plugin-validate：复用官方 composite action（SHA-pin 426e469f），
  fail-on-warnings=true 等价 --strict、base-ref 覆盖其 origin/main
  默认值、claude-cli-version 钉 2.1.270 防漂移；后接一步
  claude plugin validate .claude/skills --strict 补其盲区
- new-skill-eval-case：调用 Task 1 的门禁脚本，两个 sha 经 env 传入

三条硬约束写进文件头注释：五个 job 名同时被服务端 ruleset 引用、
一律不设 paths: 过滤器、skill-eval 绝不进必需检查。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
git show -s --format=%B HEAD | grep -F '\n'
git push -u origin feat/ci-required-checks
```

- [ ] **Step 5: 开 PR 并等 CI 首次运行**

用 MCP `create_pull_request`（`base: master`）。然后用 MCP `pull_request_read`（`method: get_check_runs`）轮询，直到五个 check run 全部结束。

🔴 **这是 CI 的第一次真实运行，红是预期内的可能结果。** 出现失败时**停下报告，不自动重试、不自动改代码**——按失败内容分类：

| 失败形态 | 判断 |
|---|---|
| `gates-hooks` 红，报符号链接 / `git ls-files -s` 模式位 | **spec § 10 风险 5 的实测结果**：Windows 与 Linux 的行为差异。判断是脚本假设了 Windows 还是 CI 环境缺配置 |
| `gates-tests` 红，某目录测试在 Linux 上失败 | 同上，属真实差异，不是 YAML 问题 |
| `plugin-validate` 红，报 `native binary not installed` | composite action 的自愈逻辑也没兜住，需读其日志判断是网络还是版本 |
| `plugin-validate` 红，报某个 skill 的 warning | `fail-on-warnings: true` 生效了。⚠️ **这说明 § 3.1 第 6 条那条「零存量债务」基线在 CI 环境不成立**，须查明差异而不是降级为 `false` |
| `new-skill-eval-case` 红 | 本 PR 没新增 SKILL.md，红说明脚本有 bug，回 Task 1 修 |
| 某个 job 一直 `queued` / 不出现 | 检查 `on.pull_request.branches` 是否写对 `master` |

- [ ] **Step 6: 五个 check run 全绿后合并**

用 MCP `merge_pull_request`（`squash`，`commit_title` 带 `(#N)`，`commit_message` 含 `Co-Authored-By`），然后：

```bash
git switch master && git pull --rebase origin master
git branch -d feat/ci-required-checks
git push origin --delete feat/ci-required-checks
```

- [ ] **Step 7: 记录验收第 1、2、3、4 项的证据**

从这次 CI 运行的日志里取，四项一次到手：

| 验收项 | 证据 |
|---|---|
| 1（本地门禁在 Linux 上可跑） | `gates-hooks` 退出 0 —— 同时是 spec § 10 风险 5 的实测 |
| 2（9 个测试目录全绿） | `gates-tests` 每个 `::group::` 内退出 0，累计用例数与本机一致（`.githooks` 应为 145 个） |
| 3（官方静态校验全绿） | `plugin-validate` 退出 0，并**逐项核对 90-report**：① marketplace 已校验；② 3 个外部条目**已被 clone 并校验**（本仓此前完全没有的判据）；③ 本 PR 改动的插件目录已被 40 步命中；④ 追加步骤 `claude plugin validate .claude/skills --strict` 退出 0。⚠️ **判据不是「22 个目标全绿」**——40 步是增量校验，22 个目标的全量结果只存在于本机基线里 |
| 4（知识库与 tips 一致性） | `gates-data` 三步各自退出 0 |

- [ ] **Step 8: 顺带记下 I1–I11 不变量在本仓的实际命中情况**

`ci.yml` **刻意不设 `warn-invariants`**（spec § 5.6：「在没有实测前不预先豁免任何不变量」）。这次首跑是第一次能看到官方那 11 条策略不变量在本仓的真实表现。

从 `plugin-validate` 的 11 步日志里读：**哪几条命中、命中的是什么**。

| 观察结果 | 处置 |
|---|---|
| 全部通过 | 记一行「本仓当前满足 I1–I11」，`warn-invariants` 保持不设 |
| 某条命中且判断确实是本仓的问题 | 修本仓的内容，**不要降级该不变量** |
| 某条命中但属官方 curated marketplace 特有的策略、对个人插件仓库不适用 | 这才是 `warn-invariants` 的正当用途。⚠️ **降级前要写清是哪一条、为什么不适用**，否则下次没人知道那个豁免是有据的还是图省事加的 |

⚠️ 这一步**不阻塞合并**（若 job 已绿就是全部通过）。它的意义是：`I5`（`source.sha` 锁定）与 `.githooks/check_external_entries.py` 的重叠是刻意保留的互补关系，而**互补到底重叠了多少，只有看过一次日志才知道**。

---

## Task 3: 【需用户在 GitHub UI 操作】把 5 项必需检查勾选加回 ruleset

**Files:** 无（服务端配置，不在版本库里）

**Interfaces:**
- Consumes: Task 2 的五个 check run 名 —— **它们必须已在 GitHub 上跑过至少一次**，否则不会出现在 UI 的可选列表里
- Produces: 主干合并条件生效。Task 5 起的每个 PR 都会真正被这 5 项拦

🔴 **这个 task 必须由用户手动完成，不能由执行者代做。** GitHub MCP **没有任何 ruleset 工具**，`gh` CLI 本机也未安装（`gh api` 退出 127）。写入 ruleset 需要 PAT + 仓库 admin 权限。

⚠️ **这一步曾经出过事故，事故的形态值得先读一遍**（spec § 4.2 其四 / § 4.5）：上一次配置时 `required_status_checks` 被配成了 **6 项**，多出的 `skill-eval` 只有 `workflow_dispatch` 触发、永远不会在 PR 上产生 check run，于是那一项永久停在 Expected；同时 CI 当时根本不存在，6 项全部 Expected —— **主干既不能直推、也不能通过 PR 合并**。

事故的成因不是粗心，而是一条结构性的倒逼：**没跑过的 job 名不会出现在 UI 列表里，于是人会去手打**，而手打就绕过了「先跑一次」这道天然校验。`skill-eval` 混进必需检查正是这条路径的产物。

- [ ] **Step 1: 请用户在 UI 中操作**

告诉用户执行以下步骤（**逐字**，不要概括）：

> 仓库 → **Settings** → **Rules** → **Rulesets** → 名为 `main` 的 ruleset（id `23134670`）→ 勾选 **Require status checks to pass**，然后在搜索框里**从下拉列表中逐个勾选**这五项：
>
> 1. `gates-hooks`
> 2. `gates-tests`
> 3. `gates-data`
> 4. `plugin-validate`
> 5. `new-skill-eval-case`
>
> 🔴 **必须从列表里选，不要手打。** 手打的名字若与实际 check run 名差一个字符，那项检查会永久停在 Expected 而不报错。
>
> 🔴 **不要勾选 `skill-eval`**（若它出现在列表里）。它只有手动触发，加进来会锁死主干；它也是唯一收费的 workflow。
>
> ⚠️ **`Require branches to be up to date before merging`（即 `strict_required_status_checks_policy`）按你此前的答复不动**，由你自行决定。

- [ ] **Step 2: 用匿名 API 核实配置结果**

不要凭 UI 记忆或用户口述判断，**直接读 API**（公开仓库读取无需认证）：

```bash
curl -s https://api.github.com/repos/Glepooek/optimus-plugins-official/rulesets/23134670 \
  | python -c "
import json,sys
d=json.load(sys.stdin)
print('updated_at:', d.get('updated_at'))
for r in d.get('rules',[]):
    if r.get('type')=='required_status_checks':
        ctx=[c.get('context') for c in r['parameters']['required_status_checks']]
        print('必需检查', len(ctx), '项:')
        for c in sorted(ctx): print('   -', c)
        print('strict policy:', r['parameters'].get('strict_required_status_checks_policy'))
        break
else:
    print('!! 未找到 required_status_checks 规则')
"
```

Expected 输出：

```
必需检查 5 项:
   - gates-data
   - gates-hooks
   - gates-tests
   - new-skill-eval-case
   - plugin-validate
```

🔴 **若出现第 6 项 `skill-eval`，立即停下报告用户删除它，不要继续后续 task。** 后续每个 task 都要走 PR，而那一项会让所有 PR 永久无法合并。

- [ ] **Step 3: 记录这一步不产生提交**

本 task 无文件改动、无提交。配置变更的记录已在 spec § 4 中。

---

## Task 4: `.github/workflows/skill-eval.yml` —— 手动的行为闸

**Files:**
- Create: `.github/workflows/skill-eval.yml`

**Interfaces:**
- Consumes: 仓库 secret `ANTHROPIC_API_KEY`（需用户先添加，见 Step 1）
- Produces: 手动入口 `workflow_dispatch`，输入 `plugin`（插件目录名）。Task 6 的付费验收通过它或本机等效命令执行

🔴 **本 workflow 的 job 名是 `skill-eval`，它绝对不进必需检查列表。** Task 3 Step 2 已核对过；本 task 合并后该名字**可能开始出现在 ruleset 的 UI 列表里**，⚠️ **不要因为「看到它在列表里」就以为该勾选**。

**一处 spec 未覆盖的实现细节：** spec § 5.8 说 CLI 安装复用官方 composite action，但该 action 的 `base-ref` 默认值是 `origin/main`，而 `workflow_dispatch` 事件下**没有** `github.event.pull_request.base.sha` 可传。处置：传 `${{ github.sha }}`，让 action 的 detect-changes 得到空 diff、快速跑完，**目的只是把 `claude` CLI 装到 runner 全局**。这比自己写 `npm i -g` 好——后者是已知的非确定性失败源（spec § 3.4.2）。

- [ ] **Step 1: 请用户添加 secret**

> 仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
> Name: `ANTHROPIC_API_KEY`，Value: 你的 API key

⚠️ **fork PR 拿不到仓库 secret**，但本 workflow 只有 `workflow_dispatch` 触发、不在 PR 上跑，所以不受影响。

- [ ] **Step 2: 创建 `.github/workflows/skill-eval.yml`**

```yaml
# 手动的行为闸——本仓唯一会产生费用的 workflow。
#
# 🔴 job 名 skill-eval 绝对不进必需检查列表。两个各自充分的理由：
#    ① 它只有 workflow_dispatch 触发，永远不会在 PR 上产生 check run，
#       进了必需检查就是一项永久 Expected，主干双向锁死；
#    ② 它是唯一收费的 job，进必需检查等于每个 PR 都付费。
#    这件事已真实发生过一次，经过见 spec § 4.2 其四。
#
# 为什么仍要保留它：claude plugin validate 查的是 schema 合法性，查不了
# 行为——一个 frontmatter 完全合法的 skill 完全可能因 description 写得含糊
# 而永不被触发，或反过来在不该触发的语境下被触发。只有 eval 能发现这件事。
#
# 判据见 spec § 5.8。

name: skill-eval

on:
  workflow_dispatch:
    inputs:
      plugin:
        # 必填而非「留空跑全部」：仓库根不是合法运行位置（无 plugin.json），
        # 「全部」只能实现为按插件循环，而循环会把一次误触的成本乘以插件数。
        # 必填一个插件名 = 把成本上界写进接口本身，比在文档里叮嘱可靠。
        description: 插件目录名，如 optimus-devops-plugin
        required: true
        type: string

permissions:
  contents: read

jobs:
  skill-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      # 只为借它安装 claude CLI 的自愈逻辑（见 ci.yml 里的说明）。
      # ⚠️ base-ref 传 github.sha：workflow_dispatch 下没有
      #    pull_request.base.sha，而该 input 的默认值是 origin/main（本仓
      #    无 main 分支）。传 head 自身让 detect-changes 得到空 diff、
      #    快速跑完，CLI 则留在 runner 上供下一步使用。
      - uses: anthropics/claude-plugins-community/.github/actions/validate-plugins@426e469f322952061102b286b378c0c9733a0934
        with:
          marketplace-path: .claude-plugin/marketplace.json
          base-ref: ${{ github.sha }}
          claude-cli-version: "2.1.270"
      - name: 跑该插件的全部 eval case
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PLUGIN: ${{ inputs.plugin }}
        run: |
          test -d "plugins/$PLUGIN" \
            || { echo "plugins/$PLUGIN 不存在"; exit 1; }
          # 六个开关全部有据可依，不是保守起见：
          #   --trust-plugin      非交互环境必需，否则卡在首次信任提示
          #   --no-publish        🔴 报告默认发布到 claude.ai，而本仓 case
          #                       含内部 Jenkins job 名——发布是外发行为
          #   --ablation none     默认 with-without 是 2 臂、成本翻倍；本仓
          #                       问的是「触发得对不对」，单臂足够
          #   --runs 1            默认 3；本仓判据全是 tool_used 布尔判定，
          #                       重复不增信息。⚠️ 引入 llm grader 后须调回 ≥3
          #   --max-cost-usd 5    ⚠️ 它挡不住第一次 run，只是失控时的刹车
          # 不设 --scaffold（会执行 case 作者提供的 bash）、
          # 不设 --allow-real-servers（会在 OS 沙箱外起真实 MCP 服务器）。
          claude plugin eval "plugins/$PLUGIN" \
            --trust-plugin \
            --no-publish \
            --ablation none \
            --runs 1 \
            --max-cost-usd 5
```

- [ ] **Step 3: 走 PR 提交**

```bash
git switch -c feat/skill-eval-workflow
git add .github/workflows/skill-eval.yml
git diff --staged --stat
git commit -m "$(cat <<'EOF'
feat(ci): 新增 skill-eval 手动行为闸

- 仅 workflow_dispatch 触发，plugin 输入必填——仓库根不是合法运行位置，
  「全部」只能按插件循环，必填一个插件名等于把成本上界写进接口
- 六个开关各有判据：--trust-plugin 非交互必需、--no-publish 阻断默认
  外发到 claude.ai、--ablation none 与 --runs 1 把单价从 ≈$0.90/case
  压到 ≈$0.15/case、--max-cost-usd 5 作失控刹车（挡不住第一次 run）
- 不设 --scaffold、不设 --allow-real-servers
- base-ref 传 github.sha：workflow_dispatch 下无 pull_request.base.sha，
  而该 input 默认值是 origin/main（本仓无 main 分支）
- 🔴 job 名 skill-eval 绝不进必需检查列表，理由写进文件头注释

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
git show -s --format=%B HEAD | grep -F '\n'
git push -u origin feat/skill-eval-workflow
```

- [ ] **Step 4: 开 PR，等 5 项必需检查全绿后合并**

⚠️ **这是第一个真正受 5 项必需检查约束的 PR**（Task 3 已把它们加回）。用 MCP `pull_request_read`（`get_check_runs`）轮询。

**若某项停在 `Expected — Waiting for status to be reported` 超过几分钟**：说明 ruleset 里的名字与实际 check run 名不一致（Task 3 手打过），回 Task 3 Step 2 核对，**不要用 `-D` 之类手段绕过，也不要请求管理员 bypass**。

合并后按硬约束顺序清分支：

```bash
git switch master && git pull --rebase origin master
git branch -d feat/skill-eval-workflow
git push origin --delete feat/skill-eval-workflow
```

---

## Task 5: 迁移 `jenkins-build` 的 20 条素材成官方格式（含版本升级与 darwin-skill 门禁）

**Files:**
- Create: `plugins/optimus-devops-plugin/skills/jenkins-build/evals/<20 个 case 目录>/prompt.md`
- Create: `plugins/optimus-devops-plugin/skills/jenkins-build/evals/<同上>/graders/triggered.md`
- Modify: `plugins/optimus-devops-plugin/.claude-plugin/plugin.json`（`version` `1.1.17` → `1.2.0`）
- Modify: `plugins/optimus-devops-plugin/.codex-plugin/plugin.json`（同值同次提交）
- Modify: `plugins/optimus-devops-plugin/skills/jenkins-build/SKILL.md`（`metadata.version` `"1.2.2"` → `"1.3.0"`）
- Delete: `plugins/optimus-devops-plugin/skills/jenkins-build/evals/trigger-eval.json`

**Interfaces:**
- Consumes: 现有 `evals/trigger-eval.json`（20 元素数组，每项 `{"query": …, "should_trigger": true|false}`，10 正 10 负）
- Produces: 20 个官方格式 case，供 Task 6 的付费验收运行。目录名 `01-trigger` … `10-trigger`、`11-no-trigger` … `20-no-trigger`

**为什么版本升级、darwin-skill 评分、删原文件都折进这一个 task：** 它们不是三件可以各自被驳回的事，而是同一次交付的必要配套。`pre-commit` 会校验两份 `plugin.json` 同值，所以版本号必须与 case 文件**同一次提交**；`AGENTS.md` 要求 Minor 升级前跑 darwin-skill，所以评分是这次提交的前置条件；原文件必须在核对完 20 条落地后**同一次**删掉，留到下一个 PR 就出现「两份真源并存」的窗口。

**🔴 三处 spec 未覆盖、必须在这里定下的实现细节：**

**其一：负例的 grader 必须显式写 `min: 0`。** spec § 5.9.2 只写了「负例 `max: 0`」，但 § 3.5.2 实测记录了 `tool_used` 的**默认 `min` 是 1**（失败时渲染 `Skill called 0x (expected 1..∞)`）。只写 `max: 0` 会得到 `1..0` 这个空区间——⚠️ **它不会报错，只会让 10 条负例全部无法通过**，而失败信息看起来像是 skill 行为不对。这属于「不报错的失效形态」，必须在写文件时就消除。

**其二：case 目录名用数字前缀，让第一个跑到的是正例。** Task 6 Step 1 只花 ≈$0.15、只跑得起**一个** run（`--max-cost-usd` 挡不住第一次 run 却挡得住第二次），那一个 run 落在哪个 case 上决定了这 $0.15 买到什么信息。若按 `no-trigger-*` / `trigger-*` 命名，字典序会让**负例**排在最前——而负例是「Skill 未被调用即通过」，哪怕 `allowed_tools` 配错、Skill 根本调不出来，它照样绿。**那 $0.15 会买到一个必然通过的结果，等于什么都没验。** 数字前缀把正例排到最前，同一笔钱换来「Skill 真的能被调起」这个信息。

**其三：`allowed_tools` 只给 `Skill`，绝不给 `Bash`。** `jenkins-build` 的 frontmatter 是 `allowed-tools: Bash`，触发后会调**真实** Jenkins API。同时 `Skill` 必须在列表里——grader 量的就是 `tool_used: Skill`，不给就等于把判据本身关掉。⚠️ 「`allowed_tools` 是否真的门控 `Skill` 工具」本身未经实测，这正是上一条要让正例先跑的原因。

- [ ] **Step 1: 确认原素材仍是 20 条 10 正 10 负**

```bash
python -c "
import json,pathlib
p=pathlib.Path('plugins/optimus-devops-plugin/skills/jenkins-build/evals/trigger-eval.json')
d=json.loads(p.read_text(encoding='utf-8'))
pos=[e for e in d if e['should_trigger']]
print('总数', len(d), '正例', len(pos), '负例', len(d)-len(pos))
"
```

Expected: `总数 20 正例 10 负例 10`

⚠️ 数字不符就**停下报告**，不要按脚本里的 `assert` 静默中断——素材变了意味着 spec § 5.9.2 的迁移决策要重新评估。

- [ ] **Step 2: 生成 40 个文件**

用 heredoc 一次性执行，**不落地成脚本文件**——一次性迁移工具留在仓库里，下次有人看到会以为它是要维护的产物，而它跑第二遍就没有输入了（原文件已删）：

```bash
python - <<'PY'
import json, pathlib

SKILL = pathlib.Path("plugins/optimus-devops-plugin/skills/jenkins-build")
src = json.loads((SKILL / "evals" / "trigger-eval.json").read_text(encoding="utf-8"))
assert len(src) == 20, f"期望 20 条，实际 {len(src)}"

pos = [e for e in src if e["should_trigger"]]
neg = [e for e in src if not e["should_trigger"]]
assert len(pos) == 10 and len(neg) == 10, (len(pos), len(neg))

# 正例编号 01–10、负例 11–20：数字前缀保证字典序下正例在前，
# 于是 Task 6 那唯一一次 ≈$0.15 的 run 落在正例上（详见本 task 开头其二）
ordered = ([(i, e, True) for i, e in enumerate(pos, 1)]
           + [(i, e, False) for i, e in enumerate(neg, 11)])

PROMPT = """---
name: {name}
description: {kind}——{expect}触发 jenkins-build
max_turns: 3
allowed_tools:
  - Skill
---

{query}
"""

# min 必须显式给：tool_used 的默认 min 是 1，负例只写 max: 0 会得到
# 空区间 1..0，10 条负例会全部无法通过而且不报错（本 task 开头其一）
GRADER_POS = """---
type: tool_used
tool: Skill
min: 1
weight: 1
---

用户明确要求跑 Jenkins 构建，jenkins-build 应被触发。
"""

GRADER_NEG = """---
type: tool_used
tool: Skill
min: 0
max: 0
weight: 1
---

该语境提到 Jenkins 但并未要求跑构建，jenkins-build 不应被触发。
"""

written = []
for n, entry, positive in ordered:
    name = f"{n:02d}-{'trigger' if positive else 'no-trigger'}"
    d = SKILL / "evals" / name
    (d / "graders").mkdir(parents=True, exist_ok=True)
    (d / "prompt.md").write_text(
        PROMPT.format(name=name,
                      kind="正例" if positive else "负例",
                      expect="应" if positive else "不应",
                      query=entry["query"]),
        encoding="utf-8")
    (d / "graders" / "triggered.md").write_text(
        GRADER_POS if positive else GRADER_NEG, encoding="utf-8")
    written.append((name, entry["query"]))

print(f"写出 {len(written)} 个 case：")
for name, q in written:
    print(f"  {name}  {q}")
PY
```

Expected: `写出 20 个 case：` 后跟 20 行「目录名 + 原 query」的映射

- [ ] **Step 3: 逐条核对 20 条 query 全部落地 —— 这是删原文件的唯一前置条件**

**不要凭 Step 2 的打印判断。** 那是生成侧的自述；核对必须从**落盘的文件**反向读回来：

```bash
python - <<'PY'
import json, pathlib, sys

SKILL = pathlib.Path("plugins/optimus-devops-plugin/skills/jenkins-build")
src = json.loads((SKILL / "evals" / "trigger-eval.json").read_text(encoding="utf-8"))

# 从落盘的 prompt.md 正文反向收集，而不是信生成脚本的说法
landed = {}
for p in sorted((SKILL / "evals").glob("*/prompt.md")):
    body = p.read_text(encoding="utf-8").split("---\n", 2)[2].strip()
    landed.setdefault(body, []).append(p.parent.name)

bad = 0
for e in src:
    q = e["query"]
    hits = landed.get(q, [])
    if len(hits) != 1:
        print(f"!! {len(hits)} 处命中：{q}  {hits}")
        bad += 1

extra = set(landed) - {e["query"] for e in src}
for q in extra:
    print(f"!! 多出的 prompt，不在原素材里：{q}")
    bad += 1

# grader 的正负分档也要核，min/max 写错不报错、只会静默让一整档失败
import re
for p in sorted((SKILL / "evals").glob("*/graders/triggered.md")):
    fm = p.read_text(encoding="utf-8").split("---\n")[1]
    positive = "no-trigger" not in p.parent.parent.name
    if positive and ("max:" in fm or "min: 1" not in fm):
        print(f"!! 正例 grader 形态不对：{p}"); bad += 1
    if not positive and ("min: 0" not in fm or "max: 0" not in fm):
        print(f"!! 负例 grader 缺 min: 0 或 max: 0：{p}"); bad += 1

print("case 目录数：", len(list((SKILL / 'evals').glob('*/prompt.md'))))
print("核对结果：", "全部落地" if bad == 0 else f"{bad} 处问题")
sys.exit(1 if bad else 0)
PY
```

Expected:
```
case 目录数： 20
核对结果： 全部落地
```

🔴 **出现任何 `!!` 行就停在这里，不要进 Step 4。** 原文件此刻还在，是唯一的回退依据；删了它再发现漏条就是静默丢素材（spec § 8.2.1）。

- [ ] **Step 4: 跑 darwin-skill 评分留档（§ 8.4 门禁）**

`AGENTS.md`：「Minor/Major 升级前必须用 `darwin-skill` 对改动的 skill 评分，新分数 ≥ 改动前分数才可提交」。本次 `metadata.version` 升 Minor，字面命中。

```
/darwin-skill
```
对 `plugins/optimus-devops-plugin/skills/jenkins-build/SKILL.md` 评分。

**预期分数不变**：本次不动 SKILL.md 正文（只改 `metadata.version` 一行），而 darwin-skill 的 rubric 针对 SKILL.md 结构。

⚠️ **仍然要跑，不能因「预期不变」跳过。** 两个理由：① 门禁存在的意义正是不依赖推断；② 若分数**真的变了**，说明 rubric 会读 skill 目录下的非 SKILL.md 内容——那是一个关于门禁本身的新事实，值得记进 `docs/`。**一次预期无信息量的检查，恰好是发现判据边界的时机。**

分数**倒退**则停下报告，不要继续升版本（门禁的字面要求）。

- [ ] **Step 5: 升三处版本号**

| 文件 | 字段 | 从 | 到 | 幅度依据 |
|---|---|---|---|---|
| `.claude-plugin/plugin.json` | `version` | `1.1.17` | `1.2.0` | 矩阵「新增 skill / agent / hook / command」类比——eval 套件是新增的用户可见产物 |
| `.codex-plugin/plugin.json` | `version` | `1.1.17` | `1.2.0` | **必须同值、同次提交** |
| `skills/jenkins-build/SKILL.md` | `metadata.version` | `"1.2.2"` | `"1.3.0"` | 「新增功能 / 章节 / 参数」 |

🔴 **这是 `pre-commit` 版本同值检查第一次真的参与进来**（此前交付都不动 `plugins/`，该检查一直空转）。漏改一份会被阻断——**阻断时不要拿一份覆盖另一份**，错的可能恰好是「另一份」。

⚠️ 「只改 `evals/` 却要升 `SKILL.md` 的 `metadata.version`」读起来反直觉，但矩阵是明文（「`plugins/*/skills/<name>/` 内**任一**文件」）。判据见 spec § 8.3。

- [ ] **Step 6: 删除原文件**

Step 3 已通过，前置条件满足：

```bash
git rm plugins/optimus-devops-plugin/skills/jenkins-build/evals/trigger-eval.json
```

用 `git rm` 而非 PowerShell 删除——它同时完成删除与暂存，少一步可能漏掉的 `git add`。

- [ ] **Step 7: 逐文件暂存并确认范围**

```bash
git switch -c feat/jenkins-build-eval-cases
git add plugins/optimus-devops-plugin/skills/jenkins-build/evals
git add plugins/optimus-devops-plugin/skills/jenkins-build/SKILL.md
git add plugins/optimus-devops-plugin/.claude-plugin/plugin.json
git add plugins/optimus-devops-plugin/.codex-plugin/plugin.json
git diff --staged --stat
```

Expected: 40 个新增 + 1 个删除 + 3 个修改 = **44 项**，全部在 `plugins/optimus-devops-plugin/` 下，**不含 `.claude/settings.json`**。

⚠️ `git add <目录>` 在这里是刻意的例外（40 个新文件逐条列不现实），但目录**恰好**只含本次产物；`禁止 git add -A` 的约束不受影响——范围仍是显式的。

- [ ] **Step 8: 提交（超时 300000 ms）**

```bash
git commit -m "$(cat <<'EOF'
feat(devops-plugin): 把 jenkins-build 的 20 条触发素材迁成官方 eval 格式

- trigger-eval.json 是自定义格式，claude plugin eval 在它上面找到 0 个
  case；迁成 prompt.md + graders/triggered.md 后 20 条全部可运行
- 正例 min: 1、负例 min: 0 + max: 0。⚠️ 负例必须显式写 min: 0——
  tool_used 的默认 min 是 1，只写 max: 0 会得到空区间 1..0，
  10 条负例会全部无法通过且不报错
- 目录名用数字前缀（01-trigger…20-no-trigger），让字典序下正例在前：
  格式验收只跑得起一个 run，落在负例上会必然通过、买不到信息
- allowed_tools 只给 Skill 不给 Bash：该 skill 的 allowed-tools 是 Bash，
  触发后会调真实 Jenkins API
- 原 trigger-eval.json 删除，删前已从落盘文件反向核对 20 条全部落地
- 版本：插件两份 plugin.json 1.1.17 → 1.2.0，jenkins-build
  metadata.version 1.2.2 → 1.3.0（矩阵第一行，改动落在 skill 目录内）

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
git show -s --format=%B HEAD | grep -F '\n'
git push -u origin feat/jenkins-build-eval-cases
```

- [ ] **Step 9: 开 PR 并等 5 项检查**

⚠️ **`new-skill-eval-case` 必须是绿的。** 本 PR 没有新增任何 `SKILL.md`（只改了已有的一行），所以门禁应输出 `本次改动无新增 skill，跳过`。**若它红了，说明 Task 1 的 `--diff-filter=A` 判定有 bug**——`test_adding_eval_case_to_existing_skill_is_not_a_new_skill` 这个用例正是为本 PR 写的，红了就回 Task 1 修。

合并后清分支：

```bash
git switch master && git pull --rebase origin master
git branch -d feat/jenkins-build-eval-cases
git push origin --delete feat/jenkins-build-eval-cases
```

---

## Task 6: eval 验收 —— 唯一产生费用的两步（验收第 10、11、12 项）

**Files:** 无（只运行与记录，不改文件）

**Interfaces:**
- Consumes: Task 5 的 20 个 case、Task 4 的 `skill-eval.yml` 与 `ANTHROPIC_API_KEY` secret
- Produces: 验收第 10、11、12 项的证据。若第 11 项的负例出现假失败，产出的是「`max: 0` 语义与推断不符」这个结论，Task 5 的 grader 形式要改

💰 **本 task 合计约 $3.15，是整个交付里唯一花钱的部分。** 两步刻意排成先后：**先花 $0.15 确认格式，再花 $3 跑全量**——反过来的话，一个写错的 frontmatter 会让那 $3 白花。

**两步分别在哪跑，是刻意分开的：**

| 步 | 在哪跑 | 为什么 |
|---|---|---|
| Step 1（≈$0.15） | **本机** | 需要 `--max-cost-usd 0.01` 这个非常规取值，而 `skill-eval.yml` 里的命令是固定的；且要仔细读 load 阶段输出 |
| Step 2（≈$3） | **走 `skill-eval.yml` 的 `workflow_dispatch`** | 同一笔钱买两件事：全量验收证据 + **Task 4 那份 YAML 的首次真实执行**。否则 Task 4 交付的是一份从未跑过的 workflow |

- [ ] **Step 1: 格式验收（≈$0.15，本机）**

```bash
claude plugin eval plugins/optimus-devops-plugin \
  --trust-plugin \
  --no-publish \
  --ablation none \
  --runs 1 \
  --max-cost-usd 0.01
```

**只读 load 阶段的输出**，三项判据：

| 判据 | 期望 |
|---|---|
| case 计数 | **20** |
| `invalid case.yaml` 之类的 load 报错 | **一行都不能有** |
| 第一个启动的 run | 是 `01-trigger`（正例） |

⚠️ **`--max-cost-usd` 挡不住第一次 run**（spec § 3.5.3 第 7 条），所以这一步**必然花掉约 $0.15**，第二次 run 才被挡下。**这是本仓能做到的最便宜的格式验收，不存在零成本版本。**

⚠️ load 对**全部 20 个 case 一次性完成**、发生在第一次 run 之前，所以这一步能一次覆盖全部 20 个的格式——**花一次 run 的钱，验二十个 case 的格式**。

🔴 **顺带要看的第四件事（Task 5 其三留下的未实测项）：** 那唯一一次 run 落在正例 `01-trigger` 上，看它的 grader 结果——

| 结果 | 含义 |
|---|---|
| `min: 1` 通过（Skill 被调用 ≥1 次） | ✅ `allowed_tools: [Skill]` 确实放行了 Skill 工具，20 个 case 的 `allowed_tools` 配置成立 |
| `Skill called 0x (expected 1..∞)` | 🔴 **`allowed_tools` 把 Skill 也挡住了**。停下报告——不要进 Step 2 花那 $3，因为 10 条正例会全部假失败。处置是回 Task 5 调整 `allowed_tools`（考虑整个字段留空以放行全部工具，代价是 Bash 也放开、可能真的调 Jenkins API，需先与用户确认） |

⚠️ **若 `--max-cost-usd 0.01` 被 CLI 拒绝**（下限约束未实测），改用 `--max-cost-usd 0.2`：它同样只够放行第一次 run，判据不变。**不要因为这个参数不接受就直接跑全量**——那就是先花 $3 再验格式，正是本 task 的排序要避免的。

- [ ] **Step 2: 全量验收（≈$3，走 workflow_dispatch）**

GitHub → **Actions** → **skill-eval** → **Run workflow** → `plugin` 填 `optimus-devops-plugin` → Run。

🔴 **判据不是「全绿」，而是分档核对：**

| 档 | 数量 | 期望 |
|---|---|---|
| 正例 `01-trigger` … `10-trigger` | 10 | 全部以 `min: 1` 通过 |
| 负例 `11-no-trigger` … `20-no-trigger` | 10 | 全部以 `min: 0` + `max: 0` 通过 |

⚠️ **10 条负例全过才算 spec § 5.9.2 的迁移决策被验证。** `max: 0` 能表达「不得调用」此前只有 schema 层证据（字段合法）与渲染文本 `1..∞` 的旁证，**语义未经实跑确认**。

**若负例出现假失败**（Skill 明明没被调用却判失败）：说明 `max: 0` 的语义与推断不符，**该批 case 需改判据形式，而不是去改 skill**。这是本 task 可能产出的最有价值的结论——把它记进 spec § 3.5.2 作为对实测契约的修正。

**若某条正例失败**（Skill 未被触发）：这是 eval 的**正常产出**，不是 eval 坏了——它说明 `jenkins-build` 的 `description` 在那个语境下匹配不上。记下是哪一条，**但本次交付不改 skill 的 `description`**（超出范围）；列成一条后续项交用户。

- [ ] **Step 3: 核对报告未外发（验收第 12 项）**

在上面两步的**全部输出**里搜 claude.ai 报告链接：

```bash
# 本机那次的输出若已滚走，重看第 2 步的 Actions 日志即可
```

判据：**输出中不出现任何 claude.ai 报告链接**，`--no-publish` 生效。

⚠️ 这是 spec § 10 风险 9 唯一的验证点：**其余工具的默认值出错只影响判据强度，这一项出错是信息泄漏**——本仓 case 里含 `lms-api-test`、`uni-stu-pc`、`k12-backend` 等内部 job 名。

- [ ] **Step 4: 把三项验收结果记进 spec**

三项都通过时，在 spec § 9 的表里把第 10、11、12 项标为已达成，并补上实测数字（实际花费、正负例通过数）。这一步走 PR（改 `docs/`，不升任何版本号）。

⚠️ **若第 11 项测出 `max: 0` 语义不符**，改的不只是 § 9——§ 3.5.2 的实测契约、§ 5.9.2 的迁移决策都要同步修订。**那是一次「实测推翻设计」的记录，值得写清推翻路径**，与 spec 里已有的几处（§ 6.1、§ 6.3、§ 8.3）同一形态。

---

## Task 7: 阴性对照 —— 证明 `new-skill-eval-case` 真的会拦（验收第 5 项）

**Files:** 临时文件，**最终不入库**

**Interfaces:**
- Consumes: Task 2 的 `new-skill-eval-case` job、Task 3 已把它加进必需检查
- Produces: 验收第 5 项的证据

**为什么这一步不能省：** spec § 3.1 第 2 条那个 `contents: []` 的教训——**一个什么都不查的门禁与一个全部通过的门禁，输出无法区分**。前面每个 PR 里 `new-skill-eval-case` 都是绿的，那只证明它没误报，**完全不证明它会拦**。

- [ ] **Step 1: 造一个「新增 SKILL.md 但无 `evals/`」的 PR**

```bash
git switch -c chore/negative-control-eval-gate
mkdir -p plugins/optimus-devops-plugin/skills/negative-control-probe
```

写 `plugins/optimus-devops-plugin/skills/negative-control-probe/SKILL.md`：

```markdown
---
name: negative-control-probe
description: 临时阴性对照 skill，用于验证 new-skill-eval-case 门禁会拦住缺 eval case 的新增 skill。验证完即删除，不要基于它开发任何功能。
metadata:
  version: "0.0.0"
---

# negative-control-probe

阴性对照用的空 skill。**本文件预期在同一个 PR 内被删除**，不会合入 master。

判据见 `docs/superpowers/specs/2026-09-13-pr-flow-and-free-ci-design.md` § 9 第 5 项。
```

⚠️ **`description` 写足**：`plugin-validate` 的 `fail-on-warnings: "true"` 会把缺 `description` 判成失败，而我们要看的是 `new-skill-eval-case` 红、其余绿。**一个把两个 job 同时弄红的对照实验，证不了是哪个门禁在起作用。**

⚠️ **不升任何版本号**：这个 skill 不会合入，升了版本号反而要在 Step 4 一起回滚。**但 `pre-commit` 的版本同值检查此刻不会拦**——它只校验两份 `plugin.json` 是否同值，不校验「新增 skill 有没有升版本」。

```bash
git add plugins/optimus-devops-plugin/skills/negative-control-probe/SKILL.md
git commit -m "$(cat <<'EOF'
chore(ci): 阴性对照——新增 skill 缺 eval case 应被门禁拦下

本提交预期让 new-skill-eval-case 变红，用于验证该门禁不是只会亮绿灯的
刹车（判据见 spec § 9 第 5 项）。同一个 PR 内会补上 evals/ 并验证转绿，
之后整个 probe skill 删除，不合入 master。

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
git push -u origin chore/negative-control-eval-gate
```

- [ ] **Step 2: 开 PR，确认 `new-skill-eval-case` 红且只有它红**

用 MCP `create_pull_request`（PR 标题注明这是阴性对照、不会合并）。

🔴 **期望结果：**

| job | 期望 |
|---|---|
| `new-skill-eval-case` | ❌ **失败**，报错含 `plugins/optimus-devops-plugin/skills/negative-control-probe` 与应建的 `evals/<case-name>/prompt.md` 路径 |
| 其余四项 | ✅ 全绿 |

**若 `new-skill-eval-case` 是绿的**：门禁失效，回 Task 1 排查——最可能是 `--diff-filter=A` 在 `base...head` 三点语法下取不到本 PR 的新增文件。这正是这个 task 存在的理由。

**若另有 job 变红**：先排除干扰再看主判据（大概率是 `plugin-validate` 嫌 `description`，或 `gates-hooks` 的符号链接检查——`.claude/skills/` 下才需要镜像，`plugins/` 下不需要，若它报了说明检查范围有问题，属真实发现）。

- [ ] **Step 3: 补上 `evals/`，确认转绿**

```bash
mkdir -p plugins/optimus-devops-plugin/skills/negative-control-probe/evals/smoke/graders
```

`evals/smoke/prompt.md`：

```markdown
---
name: smoke
description: 阴性对照用的最小 case，只为让门禁转绿
max_turns: 1
allowed_tools: []
---

这是阴性对照，不会被运行。
```

`evals/smoke/graders/triggered.md`：

```markdown
---
type: tool_used
tool: Skill
min: 0
max: 0
weight: 1
---

阴性对照占位判据，本 case 不会被运行。
```

```bash
git add plugins/optimus-devops-plugin/skills/negative-control-probe/evals
git commit -m "$(cat <<'EOF'
chore(ci): 阴性对照第二段——补上 evals/ 后门禁应转绿

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

Expected: `new-skill-eval-case` 转绿，输出 `新增 skill 的 eval case 齐备：已检查 1 个`

⚠️ **这一段同时验证了门禁的判据是「子目录含标志文件」而不是「`evals/` 非空」**——`test_loose_file_directly_under_evals_does_not_count` 锁的就是这条，这里是它的活体确认。

- [ ] **Step 4: 关闭 PR 并彻底清理，不合并**

```bash
# 用 MCP update_pull_request 把 state 改为 closed，body 里记明两段结果
git switch master
git push origin --delete chore/negative-control-eval-gate
git branch -D chore/negative-control-eval-gate
```

🔴 **这里是全计划唯一允许用 `git branch -D` 的地方**，理由明确：该分支**刻意从未合并**，`-d` 必然拒绝，而「没合并」正是预期状态。⚠️ 顺序也与别处相反（先远端后本地）——因为不需要 `-d` 的已合并判定。

确认本机残留已清：

```powershell
Test-Path plugins/optimus-devops-plugin/skills/negative-control-probe
```

Expected: `False`。若为 `True`，用 `Remove-Item -Recurse -Force -Confirm:$false` 删除（**本会话 `rm -rf` 被拒过**）。

- [ ] **Step 5: 记录验收第 5 项**

把两段结果（红的报错原文、转绿的输出）记进 spec § 9 第 5 项。与 Task 6 Step 4 可合并成同一个 PR。

---

## Task 8: 重写 `commit-cc-plugin` 的提交流程

**Files:**
- Modify: `.claude/skills/commit-cc-plugin/SKILL.md`

**Interfaces:**
- Consumes: Task 2 的五个 job 名（第五步要轮询它们）、Task 3 已生效的必需检查
- Produces: 从本 task 起，日常提交可以直接说「提交」触发该 skill，不再需要手工走 PR。**Task 9–11 就是它的首次真实使用**

**为什么排在这里而不是更早：** spec § 4.5 的顺序约束。更关键的是——**现在改它已经是「补齐」而不是「解锁」**：主干从 Task 3 起就锁上了，该 skill 的直推第五步本就不可用，早改晚改都不改变可用性，晚改换来的是「PR 流程已被手工验证 7 遍」这个前提。

⚠️ **不升任何版本号**：`.claude/` 下的文件，`AGENTS.md` 矩阵明列不升。

- [ ] **Step 1: 第一步「状态检查」加分支判定**

在现有的「🔴 CHECKPOINT — 遗留暂存文件处理」**之后**追加一个 CHECKPOINT：

```markdown
🔴 **CHECKPOINT — 当前分支判定（继续前必须完成）：**

主干 `master` 已开启保护规则，直推会被服务端以 `GH013` 拒绝。提交路径是「特性分支 → PR → CI 绿 → squash merge」。

| 当前分支 | 处置 |
|---|---|
| `master` | 正常流程，第四步前新建特性分支（见「第三步之后」） |
| 已在特性分支上 | **说明上一轮流程未走完**（CI 未过，或会话中断在轮询阶段）。沿用该分支，不新建；用 MCP `list_pull_requests`（按 `head` 过滤）查是否已有开着的 PR——有则本次提交推上去后**追加进同一个 PR** |

⚠️ 第二支不是防御性设计，而是必要配套：本 skill 用「轮询 + 显式 merge」实现 auto-merge 的等效效果（见第五步），会话在等 CI 期间中断时 PR 会停在未合并状态，**必须靠下一次触发接续**。CI 变红同样会让流程停在中途。
```

- [ ] **Step 2: 第三步「Unpushed 提交检测」把比较基准从 `origin/master` 改为当前分支上游**

现状的两条命令与判定基准都写死了 `origin/master`。在特性分支上，`origin/master..HEAD` 会把「本分支全部提交」都算成未推送，从而每次都误触发 §A 的 amend 询问。

把第三步开头的命令块替换为：

```bash
# 特性分支上要相对**本分支的上游**判断，不是相对 origin/master
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)
if [ -n "$UPSTREAM" ]; then
  git fetch origin --quiet 2>/dev/null || true
  git log "$UPSTREAM"..HEAD --oneline
else
  echo "本分支尚无上游（首次推送），无未推送提交可合并"
fi
```

并把该步正文里「相对 `origin/master`」的表述改为「相对**当前分支的上游**（`@{upstream}`）」。

⚠️ **`@{upstream}` 不存在是正常状态而非错误**——特性分支首次 `push -u` 之前本就没有上游，此时「无未推送提交」是正确结论。§A 的 amend 逻辑本身**不改**。

- [ ] **Step 3: 在第三步与第四步之间插入「建分支」小节**

```markdown
## 第三步之后 — 建特性分支（仅当第一步判定为在 `master` 上时执行）

分支名按 [`knowledge-base/git/rules/01-branching.md`](../../../knowledge-base/git/rules/01-branching.md) 的 `<type>/<简短描述>`，**`type` 与本次 commit 的 Conventional Commits type 逐字对齐**：

```bash
git switch -c <type>/<简短描述>
```

示例：`fix/hook-configs-settings-json`、`feat/pr-flow-ci`、`docs/agents-commit-section`。

⚠️ **建分支排在提交之前，理由是「少一步、少一个可能记错的命令」**，不是「否则必须用破坏性命令」。**会话中途才发现忘了建分支时不必推翻重来**，两条命令即可无损补救：

```bash
git switch -c <type>/<描述>          # 新分支从当前 HEAD 拉出，已有 commit 自然归它
git branch -f master origin/master   # master 未被 checkout，-f 只改指针
```

第二条作用于一个**未被 checkout** 的分支，因此只移动引用、不触碰工作树，用不上 `--hard`。（`reset --hard` 之所以危险是它会同时重置工作树；分支指针的移动本身是无损的。）
```

- [ ] **Step 4: 第五步整节重写**

把现有「## 第五步 — 同步推送」整节（含 `git pull --rebase origin master` / `git push origin master`、三种失败处置表、「工作区不干净」小节）**整体替换**为：

```markdown
## 第五步 — 推分支、开 PR、等 CI、合并

主干只能经 PR 合入（服务端 ruleset 强制，不依赖任何 harness 的自觉）。六个动作，前两个用 git，中间三个用 GitHub MCP，最后回到 git：

| # | 动作 | 手段 |
|---|---|---|
| 1 | 推特性分支 | `git push -u origin <branch>` |
| 2 | 开 PR | MCP `create_pull_request`（`base: master`、`head: <branch>`） |
| 3 | 等 CI | MCP `pull_request_read`（`method: get_check_runs`），轮询至五个必需检查全部结束 |
| 4 | 合并 | MCP `merge_pull_request`（`merge_method: "squash"`） |
| 5 | 回主干 | `git switch master && git pull --rebase origin master` |
| 6 | 清分支 | `git branch -d <branch>` **再** `git push origin --delete <branch>` |

⚠️ 第 1 步**不用 MCP 的 `push_files`**——那是通过 API 造新 commit，会与本地已有的 commit 分叉。ruleset 只作用于 `master`，特性分支可自由推。

**第 2 步的 PR 内容：** title 取 commit 摘要行，body 取 commit 正文，结尾加 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`。该尾注**只进 PR body，不进** squash 后的 commit message。

**第 3 步等的五个必需检查**（名字逐字，同时被 `.github/workflows/ci.yml` 与服务端 ruleset 引用）：`gates-hooks`、`gates-tests`、`gates-data`、`plugin-validate`、`new-skill-eval-case`。

🔴 **第 3 步出现失败检查时：停下报告，不自动重试、不自动改代码。** CI 红说明门禁真的拦到了东西，与第四步 `pre-commit` 阻断时「禁止绕过」的处置同构。

🔴 **第 4 步必须显式传 `commit_title` 与 `commit_message`**，两处各有一个静默失效形态：

| 漏传 | 后果 |
|---|---|
| `commit_message` | GitHub 用 PR body 生成 message，**特性分支 commit 里的 `Co-Authored-By` 尾注不会进入 squash 后的 commit**——主干上的 AI 协作者标注从此静默消失 |
| `commit_title` 里的 `(#N)` | **显式传 `commit_title` 时 GitHub 不再自动追加 `(#N)` 后缀**。漏了会让主干 log 分成「带 PR 号」与「不带」两种 |

因此 `commit_title` 写成 `<type>(<scope>): <摘要> (#N)`，`commit_message` 原样带上 commit 正文与 `Co-Authored-By` 尾注。

⚠️ **第 6 步的顺序是硬约束：先删本地、后删远端。**

| 顺序 | `git branch -d` 的结果 |
|---|---|
| **先本地、后远端**（本 skill 采用） | ✅ 成功，只给一行 warning：`… has been merged to refs/remotes/origin/<branch>, but not yet merged to HEAD` |
| 先远端、后本地 | ❌ 拒绝，报 `not fully merged` |

机制是 **`-d` 的「已合并」判定不只看 HEAD，也看远端追踪引用**。顺序正确时 `origin/<branch>` 仍存在且与本地同 commit，判定通过；先删远端则该引用消失，判定只能对 HEAD 做，而 squash 产生的是一个**全新的 commit 对象**、特性分支的 commit 从未成为它的祖先，按可达性确实「未合并」。

🔴 **万一顺序反了、`-d` 已被拒，不能因此改用 `-D`**：`-D` 对「真的没合进去」和「合进去了但换了对象」一视同仁，用它等于放弃判断。正确判据是**比对树对象**：

```bash
git rev-parse <branch>^{tree}   # 与
git rev-parse master^{tree}     # 相等 ⇒ 内容已完整落地，再 -D
```

树对象相等意味着两边文件内容逐字节一致，这正是「已合并」在 squash 语境下的实质含义。

### 这是 auto-merge 的等效实现，不是 GitHub 的 auto-merge

GitHub 原生 auto-merge 是一个 GraphQL mutation（`enablePullRequestAutoMerge`），**MCP 服务器未提供对应工具**。上表用「轮询 + 显式 merge」达到同样的最终状态。实质差异只有一处：

| | 原生 auto-merge | 本流程 |
|---|---|---|
| 会话在等 CI 期间中断 | GitHub 在服务端继续等，CI 绿后自行合并 | PR 停在未合并状态，**需下次触发本 skill 时接续**（第一步 CHECKPOINT 的第二支） |

**不为此引入 `gh` CLI**——它能做到原生 auto-merge，但为「会话中断时少一次接续」的收益引入新依赖不划算，而接续逻辑本来就必须存在（CI 变红同样会让流程停在中途）。

### 工作区不干净

第一步 CHECKPOINT 明确允许把无关改动排除在本次提交外，被排除的文件就留在工作区，第 5 步的 `git pull --rebase` 会被它们挡住。**越是按第一步规范排除了无关文件，越必然撞上这个失败。**

不要为了让 rebase 通过就把无关文件一并提交——那会破坏第二步刚校验过的原子性。正确做法是只把它们临时挪走：

```bash
git stash push -m "commit-cc-plugin: 临时挪走无关改动" <排除的文件路径...>
git switch master && git pull --rebase origin master
git stash pop
```

⚠️ `git stash push` 必须**列出具体文件路径**，不加路径的裸 `git stash` 会把工作区全部改动一起挪走，`pop` 时若遇冲突更难还原。必须 `git stash pop` 原样恢复，不要留在 stash 里——用户会以为改动丢了。
```

- [ ] **Step 5: 常见错误表补 5 条**

在「## 常见错误」表末尾追加：

```markdown
| `git push origin master` 直推主干 | 主干已开保护，直推被 `GH013` 拒绝。走第五步的「分支 → PR → CI → squash merge」 |
| `merge_pull_request` 不传 `commit_message` | squash 会丢掉 `Co-Authored-By`，主干上的 AI 协作者标注静默消失（第五步第 4 步） |
| `commit_title` 不带 `(#N)` | 显式传 `commit_title` 时 GitHub 不再自动追加 PR 号，主干 log 会分成两种风格 |
| 清分支时先删远端 | `git branch -d` 的已合并判定也看远端追踪引用，反了会报 `not fully merged`。顺序：先本地、后远端 |
| `-d` 被拒就改用 `-D` | `-D` 对「真没合」与「合了但换了对象」一视同仁。先比 `<branch>^{tree}` 与 `master^{tree}`，相等才 `-D` |
| 会话中途发现忘了建分支，就推翻重做 | `git switch -c <分支>` 后 `git branch -f master origin/master` 即可无损搬运（「第三步之后」小节） |
```

⚠️ 上表实际是 6 行——最后一行「忘了建分支」是 § 6.1 那次论据被推翻后**新增的**补救路径，spec 明确要求写进常见错误表。

- [ ] **Step 6: 用改造后的 skill 自己提交这次改动 —— 首次真实使用**

🔴 **这是 dogfooding，也是验收第 7 项。** 说「提交」触发 `commit-cc-plugin`，让它按刚写好的第五步走一遍完整流程。

判据（验收第 7 项）：建分支 → push → PR → 五项 CI 绿 → squash merge → 回主干，且**主干 commit 含 `Co-Authored-By`**：

```bash
git switch master && git pull --rebase origin master
git show -s --format=%B HEAD
```

Expected: 输出末尾有 `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`，标题末尾有 `(#N)`

⚠️ **若 skill 在某一步卡住或走错**，那正是这一步要暴露的——**用它自己提交它自己的改动，是能拿到的最直接的验证**。修正后重新触发，不要绕过 skill 手工完成剩余步骤（那会掩盖问题）。

分支名建议 `feat/commit-cc-plugin-pr-flow`。

---

## Task 9: `AGENTS.md` 与 `.githooks/README.md`

**Files:**
- Modify: `AGENTS.md`（「提交与推送」节重写 + 版本矩阵补 2 行）
- Modify: `.githooks/README.md`（新增「与 CI 的关系」一节 + 「启用」一节补 CI 第二执行点）

**Interfaces:**
- Consumes: Task 1 在 `.githooks/README.md` 里留下的对「与 CI 的关系」的**前向引用**——本 task 把它坐实
- Produces: 无代码接口。这两份是 agent 每次进仓库都会读到的文件，**约束从这里开始对未来的会话生效**

**⚠️ 从本 task 起，提交走 `commit-cc-plugin`**（Task 8 已改造完并自测过）。不再手工执行 PR 流程。

- [ ] **Step 1: 重写 `AGENTS.md`「提交与推送」节**

现有该节共三段（`commit-cc-plugin` 是唯一路径 / `pre-commit` 拦什么 / 为什么挂 hook 而非 skill）。**保留第二、三段**，在第一段之后插入下面五条：

```markdown
**主干 `master` 已开启保护规则，直推会被服务端以 `GH013` 拒绝。** 提交路径是「特性分支 → PR → CI 全绿 → squash merge」，`commit-cc-plugin` 的第五步已按此改造。

**Codex 侧走标准 git 时同样必须建分支走 PR**——ruleset 是服务端强制，不依赖任何 harness 的自觉。分支名按 `knowledge-base/git/rules/01-branching.md` 的 `<type>/<简短描述>`，`type` 与本次 commit 的 Conventional Commits type 逐字对齐。

**门禁现在有两个执行点**：`.githooks/pre-commit` 在本地（需 `git config core.hooksPath .githooks`），`.github/workflows/ci.yml` 在每个 PR 上跑**同一批脚本**。后者不依赖本机配置，是 `pre-commit` 长期缺口的补齐——本地未启用 hook 仍会被 PR 上的 CI 拦住。

**五个必需检查的 job 名**（`gates-hooks`、`gates-tests`、`gates-data`、`plugin-validate`、`new-skill-eval-case`）**同时被 `ci.yml` 与 GitHub 服务端 ruleset 引用**，而后者不在版本库里、改动不留 diff。🔴 **改 job 名必须同步改 ruleset**，否则那项检查会静默不再被要求——属「不报错的失效形态」。

**新增 skill 必须带 eval case**：`plugins/<plugin>/skills/<skill>/evals/<case>/` 下需有 `prompt.md`（或 `case.yaml`），由 `new-skill-eval-case` job 强制，**存量不回溯**。可参照的活体样本是 `jenkins-build` 的 20 条（10 正例 `min: 1` / 10 负例 `min: 0` + `max: 0`）。⚠️ 门禁只查 case **存在**，不查内容有没有意义——内容质量属人工评审。
```

- [ ] **Step 2: 版本触发矩阵补 2 行**

在「| `.claude/` 下任何文件 | ❌ | — | — | ❌ |」这一行**之前**插入 evals 行，之后插入 `.github/` 行：

```markdown
| `plugins/*/skills/<name>/evals/` 内任一文件 | ✅ | ✅ | — | ❌ |
| `.github/` 下任何文件（workflow、action 配置） | ❌ | — | — | ❌ |
```

并在「七条判读要点」后追加第八条：

```markdown
8. **`.github/` 不升任何版本号**——它不在任何插件内、不随插件分发。这一条按核心规则本可推导，写成明文只为省掉下次重新推导。反过来，**`evals/` 那一行是既有第一行的特例明写**：改 eval case 要升插件两份 `plugin.json` 与该 skill 的 `metadata.version`，因为 eval 套件落在 `plugins/*/skills/<name>/` 内。⚠️ 「只改 evals/ 却要升 skill 版本」反直觉到值得一条明文——`metadata.version` 是描述性版本号，本就该反映「这个 skill 演进到哪一步」，**有行为测试的 skill 与没有的确实不是同一步**
```

⚠️ **evals 那一行不是新规则，是既有第一行（「`plugins/*/skills/<name>/` 内任一文件」）已经覆盖的情形的明写。** 之所以还要写，是因为 spec § 8.3 的推翻过程表明这一条会被漏判——**同一批文件，只因为存放位置从仓库根挪进插件目录就跨过了版本矩阵的边界**。

- [ ] **Step 3: `.githooks/README.md` 新增「与 CI 的关系」一节**

插在「## 为什么挂在 hook 而不是 skill 里」**之前**：

```markdown
## 与 CI 的关系

`.github/workflows/ci.yml` 的 `gates-hooks` job **逐字执行 `sh .githooks/pre-commit`**，不在 workflow YAML 里重写一份门禁逻辑。这是本目录唯一的第二执行点。

🔴 **由此产生一条硬约定：`pre-commit` 不得引入依赖暂存区的检查**（`git diff --cached`、`git diff --name-only --staged` 等）。当前六项检查全部基于工作树与 `git ls-files`，**这条性质必须保持**——一旦引入，CI 的逐字复用即失效，门禁判据会在两个环境间静默分叉：本地拦得住的 CI 拦不住，反之亦然。

需要 diff 的门禁改为「接受 base/head 两个 ref 作参数、只由 CI 调用、不进 `pre-commit` 序列」，`check_new_skill_eval_case.py` 就是这个形态（见上一节）。
```

- [ ] **Step 4: 「启用」一节补 CI 第二执行点**

把现有的

```markdown
未启用时 hook 静默不执行，不会有任何提示。
```

改为

```markdown
未启用时 hook 静默不执行，不会有任何提示——**但改动仍会被 PR 上的 CI 拦住**（`gates-hooks` job 跑的是同一个脚本，见「与 CI 的关系」）。这批门禁此前只在配置过 `core.hooksPath` 的机器上生效过，搬进 CI 后第一次有了不依赖本机配置的执行点。
```

- [ ] **Step 5: 坐实 Task 1 留下的前向引用**

Task 1 Step 7 写入的段落里有一句「原因见「与 CI 的关系」」。Step 3 已建出该节，**这一步只需确认引用能对上**：

```bash
grep -n "与 CI 的关系" .githooks/README.md
```

Expected: **两处**命中——一处是 Task 1 那段里的引用，一处是 Step 3 新建的标题。

⚠️ 若 Task 1 执行时把该引用临时改成了「见 spec § 5.3」（Task 1 Step 7 允许的变体），**这一步要把它改回来**：README 内部的交叉引用比指向 `docs/` 的引用更耐久——spec 是一次性的历史决策记录，README 是常读文档。

- [ ] **Step 6: 提交**

说「提交」触发 `commit-cc-plugin`。分支名建议 `docs/agents-and-hooks-readme-pr-flow`。

⚠️ **不升任何版本号**：`AGENTS.md` 与 `.githooks/` 都在矩阵的「❌」侧。

---

## Task 10: 两条知识库条款 —— 必须经 `knowledge-base-maintain`

**Files:**
- Modify: `knowledge-base/git/rules/03-pull-requests.md`（`:25` 拆成两条）
- Modify: `knowledge-base/git/rules/01-branching.md`（`:17` 括号枚举、`:18` 示例）
- Modify（由 skill 自动同步）：`knowledge-base/git/index.jsonl`、`knowledge-base/git/CHANGELOG.md`、git 领域版本号（当前 `7.2.1`）

**Interfaces:**
- Consumes: 无代码依赖
- Produces: 规范侧与配置侧的一致。⚠️ **在本 task 完成前，仓库一直处在「ruleset 已按新规矩配好、而知识库条款还写着旧规矩」的中间态**——那是把旧死结换了个方向，不是解开

🔴 **必须走 `knowledge-base-maintain` skill，禁止直接编辑条目正文。** 它负责同步 `index.jsonl`、CHANGELOG、领域版本号并跑一致性校验。直接编辑会让 `check_index.py` / `check_refs.py` 报错——⚠️ **而那两个脚本正是 `gates-data` job 跑的**，所以绕过 skill 的后果不是「以后某天发现」，而是**这个 PR 当场变红**。

- [ ] **Step 1: 触发 `knowledge-base-maintain`，两条改动在同一次维护内完成**

```
/knowledge-base-maintain
```

两条都在 `git` 领域，**一次维护处理完**——分两次会让领域版本号连升两次、CHANGELOG 出现两条本属同一件事的记录。

- [ ] **Step 2: 第一处 —— `03-pull-requests.md:25` 拆成两条**

现状（单条同时管两件事）：

```
- **必须**：主干分支要求至少一名 reviewer 批准且 CI 全绿才允许合并
```

改为：

```
- **必须**：主干分支要求 CI 全绿才允许合并
- **必须**：多人协作仓库要求至少一名 reviewer 批准才允许合并。**单人维护仓库不适用**——GitHub 不允许 PR 作者批准自己的 PR，要求 ≥1 批准会使主干永久不可合并；此类仓库以「CI 全绿 + 保护规则禁止直推」作为等效约束
```

**为什么必须拆条而不是给原条款加个括号：** 原条款把「CI 全绿」和「reviewer 批准」用「且」绑在一起。给单人仓库加作用域限定时，限定会落在整条上、**连带豁免掉 CI 要求**——而 CI 要求恰恰是本次交付要**强化**的部分。**不拆条就无法只豁免其中一半。**

⚠️ `:24`（禁止直推、禁止 force push、只能 PR）与 `:26`（`release/*` 的 SHOULD 条款）**一字不动**。

- [ ] **Step 3: 第二处 —— `01-branching.md:17` 消解条款内的措辞矛盾**

现状（正文与括号互相矛盾）：

```
- **必须**：分支名使用 `<type>/<简短描述>` 格式，`type` 取值与提交信息 `type` 对齐（`feature`/`fix`/`release`/`hotfix`/`chore` 等），`简短描述` 用小写短横线分隔，禁止拼音或无意义占位（如 `feature/temp`）
```

正文要求「与提交信息 `type` 对齐」，而本仓提交用的 Conventional Commits 类型是 `feat`；括号里给的却是 `feature`。**逐字对齐的话该叫 `feat/`，照抄括号的话该叫 `feature/`。**

裁决（spec § 7.2）：**以正文的「对齐」为准，括号内枚举改为 Conventional Commits 类型。**

🔴 **但不能照 spec 字面替换 —— 这是写计划时新发现的一处 spec 遗漏。** spec § 7.2 给的替换值是「`feat`/`fix`/`docs`/`refactor`/`chore` 等」，把 `release` 与 `hotfix` 一并删掉了。而同一份文件的：

- `:19` —— `release/*` 分支仅用于发布前收尾
- `:20` —— `hotfix/*` 分支从主干或对应发布 tag 拉出

**这两条各自引用了 `release` 与 `hotfix` 作为分支 type。** 按 spec 字面替换会**把它们的引用对象从枚举里抽掉**，留下两条指向不存在的 type 的条款——一次「改 A 破坏 B」的静默失效。

因此实际改为（`feature` → `feat`，补 `docs`/`refactor`，**保留 `release`/`hotfix`**）：

```
- **必须**：分支名使用 `<type>/<简短描述>` 格式，`type` 取值与提交信息 `type` 对齐（`feat`/`fix`/`docs`/`refactor`/`chore` 等），发布与紧急修复另用 `release`/`hotfix`（见下两条），`简短描述` 用小写短横线分隔，禁止拼音或无意义占位（如 `feat/temp`）
```

`:18` 的示例 `feature/123-add-login` 相应改为 `feat/123-add-login`。

⚠️ **`release`/`hotfix` 不是 Conventional Commits 类型，它们是分支用途而非提交类型。** 新表述把这层区别写明了（「另用」+ 指向下两条），比原先混在一个括号里更准确——**原条款的矛盾不止 `feature` vs `feat` 这一处，还有「把两类不同性质的标识符并列在同一个枚举里」**。

- [ ] **Step 4: 跑一致性校验**

`knowledge-base-maintain` 的 Step 5 会做，但**独立再跑一次**——`gates-data` job 跑的就是这两个脚本，本机先过一遍能省一次 CI 往返：

```bash
python .claude/skills/knowledge-base-maintain/scripts/check_index.py
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
```

Expected: 两者均退出 0（基线：790 条索引记录、284 个消费者引用）

⚠️ **`check_refs.py` 是这一步的关键。** `03-pull-requests.md` 从 `:25` 一条变两条后，**该文件里 `:25` 之后所有条目的行号都会 +1**——任何按「file + 行号」引用它们的消费者文件都会失效。`check_refs.py` 查的正是这个。**这也是必须走 skill 而不是手改的最实质的理由**：行号漂移是机械的、可检的，但只有在索引被同步更新后才检得出来。

- [ ] **Step 5: 提交**

说「提交」触发 `commit-cc-plugin`。分支名建议 `docs/git-kb-pr-and-branch-clauses`。

⚠️ **知识库有独立版本体系**：git 领域版本号由 skill 从 `7.2.1` 升上去（改条目正文属 Patch 还是 Minor 由 skill 判断），**插件版本一律不升**。

---

## Task 11: 标记 todo 已裁决 + 12 项验收总核对

**Files:**
- Modify: `docs/todo-list/2026-09-12-todo.md`

**Interfaces:**
- Consumes: 前十个 task 留下的全部验收证据
- Produces: 交付闭环。**若某项验收在这里发现没做到，交付不算完成**——不要在总核对里把「没跑」写成「通过」

- [ ] **Step 1: 标记 todo 已裁决**

在 `## 主干推送方式的规范冲突（待裁决作用域）` 这行标题**之下**插入裁决块，**原分析全文保留**（它记录的是当时为什么会有这个死结，是历史记录而非待办）：

```markdown
> ✅ **已裁决并落地（2026-09-13）。** 采用下方**处置 2**：承认本仓也该走 PR。
>
> - 设计判据：[`docs/superpowers/specs/2026-09-13-pr-flow-and-free-ci-design.md`](../superpowers/specs/2026-09-13-pr-flow-and-free-ci-design.md)
> - 实现计划：[`docs/superpowers/plans/2026-09-13-pr-flow-and-free-ci.md`](../superpowers/plans/2026-09-13-pr-flow-and-free-ci.md)
>
> 四项决定：① `03-pull-requests.md:24`（禁止直推、只能 PR）**原样保留并开始遵守**——该条款本身无缺陷，缺的是执行；② `:25` 的「至少一名 reviewer 批准」**拆条并加作用域限定**（GitHub 不允许 PR 作者批准自己的 PR，单人仓库该条款物理上无法满足），「CI 全绿」部分**保留且强化**为五个服务端必需检查；③ `commit-cc-plugin` 第五步整节改写为「分支 → PR → CI → squash merge」；④ `01-branching.md:17` 的分支命名条款**随之生效**——走 PR 必然要建分支，该条款不再是空转，同时消解了它自身「正文要求与提交 type 对齐、括号却写 `feature`」的措辞矛盾。
>
> ⚠️ **下方第 15 行提到的那个附带判断有了明确答案：** 分支命名条款不是「只对多人仓库生效」，而是**此前因 trunk-based 而实质空转**。走 PR 后它自动生效，无需加任何作用域限定。
>
> ⚠️ **原分析里有一处判断被后续取证推翻**：它把「加作用域限定」当作处置 1 的全部代价。实际取证发现主干上**已经存在**一个 active ruleset（id `23134670`），只是当前账号在 bypass 名单内，服务端只回一行 `Bypassed rule violations` 而放行——**保护的有效范围与实际使用者的交集是空集**。这不是「要不要加保护」的选择题，而是一个已存在却对唯一使用者无效的配置。详见 spec § 4.1。
```

⚠️ **末尾那条「原分析被推翻」不是给自己挑错，而是这份 todo 唯一值得回读的部分**：一个看起来在讨论「该选哪条路」的分析，前提本身是错的（以为主干无保护）。**下次遇到规范冲突时，先读一遍服务端实际配置**——spec § 4.4 记的「读取不需要认证，写入需要」就是这条教训的操作形式。

- [ ] **Step 2: 12 项验收总核对**

逐项回填，**每一项都要指向可核对的具体产物**，不写「已完成」这种无法复核的措辞：

| # | 验收目标 | 证据来源 | 记什么 |
|---|---|---|---|
| 1 | 本地门禁在 Linux 上可跑 | Task 2 Step 7 | `gates-hooks` 退出 0。**同时是 spec § 10 风险 5（Windows/Linux 差异）的实测** |
| 2 | 9 个测试目录全绿 | Task 2 Step 7 | 每个 `::group::` 内退出 0，`.githooks` 用例数 **145** |
| 3 | 官方静态校验全绿 | Task 2 Step 7 | 退出 0 + 90-report 四项逐项核对。⚠️ **判据不是「22 个目标全绿」**——40 步是增量校验 |
| 4 | 知识库与 tips 一致性 | Task 2 Step 7 | `gates-data` 三步各自退出 0 |
| 5 | **阴性对照**：eval case 门禁真会拦 | Task 7 | 红的报错原文 + 补 `evals/` 后转绿的输出 |
| 6 | **阴性对照**：主干真推不上去 | ✅ **spec 记录时已达成** | `GH013 … push declined due to repository rule violations`。⚠️ 判据是「拒绝」而非「有提示」 |
| 7 | 全自动流程闭环 | Task 8 Step 6 | 主干 commit 含 `Co-Authored-By` 且标题带 `(#N)` |
| 8 | 知识库改动未破坏一致性 | Task 10 Step 4 | `check_index.py` / `check_refs.py` 退出 0，领域版本与 CHANGELOG 已同步 |
| 9 | 新门禁有测试与文档 | Task 1 + Task 9 | 21 个测试通过；`.githooks/README.md` 已登记且「与 CI 的关系」引用能对上 |
| 10 | **eval 套件格式正确**（≈$0.15） | Task 6 Step 1 | case 计数 20、无 load 报错、正例先跑且 Skill 被调起 |
| 11 | **负例判据真的成立**（≈$3） | Task 6 Step 2 | **分档**：10 正例 `min: 1` 通过 / 10 负例 `min: 0`+`max: 0` 通过 |
| 12 | 报告未外发 | Task 6 Step 3 | 两次运行输出中无 claude.ai 报告链接 |

🔴 **三项要特别防止「自我确认」：**

- **第 5、6 项是阴性对照**，判据是「**红**」和「**被拒绝**」。只验证绿不能证明门禁有效——spec § 3.1 第 2 条那个 `contents: []` 就是这个教训：一个什么都不查的门禁与一个全部通过的门禁，输出无法区分。
- **第 11 项判据不是「全绿」而是分档核对**。20 个 case 全绿有一种平凡解释：`allowed_tools` 把 Skill 挡住了，于是 10 条负例平凡通过、10 条正例……不，那会红。真正要防的是反向——**若把负例的 `min` 漏写成默认 1，10 条负例会全红**，那时「10 正 10 负」的分档一眼看得出问题在哪一档。
- **第 3 项的判据被 spec 特意改窄过**（「不是 22 个目标全绿」）。官方 action 的 40 步是增量校验，全量结果只存在于本机基线里。**照着「全绿」写会记下一个 CI 从未产出过的结论。**

- [ ] **Step 3: 若有验收项未达成，如实记录并列为后续项**

可预见的两种情形，**都不构成交付失败，但必须写清**：

| 情形 | 处置 |
|---|---|
| Task 6 测出某条正例未触发（`jenkins-build` 的 `description` 在该语境匹配不上） | **这是 eval 的正常产出，不是 eval 坏了**。记下是哪一条，列为后续项——本次交付不改 `description`（超出范围） |
| Task 6 测出 `max: 0` 语义与推断不符 | 回 Task 5 改 grader 形式，**并同步修订 spec § 3.5.2 / § 5.9.2**。这是「实测推翻设计」，与 spec 里已有的几处（§ 6.1、§ 6.3、§ 8.3）同一形态 |

- [ ] **Step 4: 顺带记下三项本次刻意不做的事**

写进 todo 的裁决块末尾或另起一条，**不要让它们随会话消失**：

1. **`.claude/settings.json` 是否纳入版本库** —— 未决（spec § 10 风险 6）。它当前未跟踪，本次交付全程排除在所有提交之外。
2. **`wpf-code-review` 的 6 条素材仍是非官方格式** —— `claude plugin eval` 在它上面找到 0 个 case（spec § 5.9.3 / § 10 风险 10）。⚠️ **风险不是「暂时没迁」而是「看起来已经有 eval 了」**——目录里躺着一个名为 `evals/` 的文件夹却一个 case 都不产出。迁它需要付费 `llm` grader，而其判据措辞稳定性与 `--threshold` 默认 1.0 的适用性均未取证。
3. **`--runs 1` 在引入 `llm` grader 后不再合适** —— 当前全部判据是 `tool_used` 布尔判定，重复不增信息；`llm` 评委有抖动，单次结果不可据以判定回归。⚠️ **没有任何机制会在新增 `llm` grader 时提醒调 `--runs`**（spec § 10 风险 11）。

⚠️ 另有两项**已在本计划内处置、不必再列**：ruleset 的 `strict_required_status_checks_policy`（用户明确表示自行处理，Task 3 Step 1 已注明不动它）、ruleset 改名为 `master-protection`（spec § 4.4 的可选清理项，不影响功能）。

- [ ] **Step 5: 提交**

说「提交」触发 `commit-cc-plugin`。分支名建议 `docs/todo-adjudicated-pr-flow`。

⚠️ **不升任何版本号**：`docs/` 在矩阵的「❌」侧。

**这是交付的最后一个 PR。** 合并后主干上应当同时具备：五个服务端强制的必需检查、一个手动的行为闸、20 个可运行的 eval case、一条改造完成的提交路径、以及与之一致的规范条款。
