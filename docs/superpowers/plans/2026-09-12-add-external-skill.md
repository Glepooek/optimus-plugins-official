# add-external-skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把「引入外部 skill」这套判断固化为 `.claude/skills/add-external-skill/`，配一个机械传感器守住条目形态，并用该 skill 自己接入 archify 与 ppt-master 两条链接条目。

**Architecture:** 引导器（skill，注入当前对话，做形态判定与人在回路确认；`disable-model-invocation: true`，只能由人显式调用）+ 传感器（`.githooks/check_external_entries.py`，挂 pre-commit，只查机械可判定项）+ 台账（`registry.md`，与 skill 同处一地，被传感器按名称存在性 **与 sha 一致性**双向匹配）。外部内容一律不 vendor，只在 marketplace 条目里锁 40 位 `sha` 且不写 `version`——这使 harness 层面的 update 直接 skip，从根上消除重试。

**Tech Stack:** Python 3（仅标准库：`json` / `re` / `pathlib` / `unittest`）、POSIX sh（`pre-commit`）、`git ls-remote`。

**Spec:** `docs/superpowers/specs/2026-09-12-add-external-skill-design.md`

## Global Constraints

- **本机没有 `pytest`，只能用 `unittest`。** 门禁脚本测试命令固定为 `python -m unittest discover -s .githooks -p "test_*.py"`（`discover` 不递归跨目录，`-s` 必须精确指向目录）。
- **禁止手动执行 git 工作流。** 每个 Task 的提交步骤一律说「调用 `/commit-cc-plugin`」并给出该次提交要表达的要点；不要写 `git add` / `git commit` 命令。禁止 `--no-verify`。
- **禁止无关格式化。** 编辑 `SKILL.md` / `CHANGELOG.md` / `AGENTS.md` / `marketplace.json` 时只改语义相关内容，不增删空行、不做表格对齐。提交前看 `git diff`，出现大片纯空白变化即撤销重做。
- **marketplace 条目内永不写 `version`**——官方会静默忽略并优先用 `plugin.json` 的值。
- **`sha` 必须 40 位全长小写十六进制**，用 `git ls-remote <url> <ref>` 实测取得，不得手抄缩写或凭记忆填写。
- **`ref` 不得假定为 `main`**。已知反例：`alchaincyf/darwin-skill` 是 `master`，`Graphify-Labs/graphify` 是 `v8`。
- **`git-subdir` 的子目录字段名是 `path`**，不是 `subdir`。
- **传感器报错文案不得给出「以某一份为准」式指引**（沿用 `check_plugin_versions.py` 的既定原则：正确动作是回头判断该怎么改，而非拿一边覆盖另一边）。
- **传感器一律不联网**。提交门禁联网会让离线提交失败，代价大于收益。
- **`add-external-skill` 的 SKILL.md 必须带 `disable-model-invocation: true`**，并在正文写明该字段解决什么问题 + spec § 4.1 的三点连带影响。它是本 skill 唯一的 Claude Code 原生字段，不得为了让 `skills-ref validate` 转绿而删掉。
- **更新失败一律不重试**：不排定时任务、不轮询、不自动改 sha。**写入后验证失败必须把 sha 回滚到旧值**（spec § 4.5 第四格）——「旧 sha 原样保留」在这条路径上是假的。
- 本次改动**不触及任何插件的 `plugin.json`**，故两份同值规则不涉及；唯一要升的版本号是 `.claude-plugin/marketplace.json` 的**顶层** `version`，每新增一条插件条目升一次 Minor（先例 `4d741b8`：12.1.9 → 12.2.0）。当前值 `14.1.0`。

## File Structure

| 文件 | 职责 | Task |
|---|---|---|
| `.githooks/check_external_entries.py` | 传感器本体。8 项机械检查，`check_all(repo_root) -> list[str]` | 1 |
| `.githooks/test_check_external_entries.py` | 传感器单测，双向覆盖（应通过 + 应阻断） | 1 |
| `.githooks/check_plugin_versions.py` | 既有脚本，`check_all()` 扫描范围扩到 `external_plugins/` | 2 |
| `.githooks/test_check_plugin_versions.py` | 既有单测，补 `external_plugins/` 相关用例 | 2 |
| `.claude/skills/add-external-skill/SKILL.md` | 引导器正文：两模式、四类前置校验、五分支判定表、更新 U0–U8、失败处理四格 | 3 |
| `.claude/skills/add-external-skill/registry.md` | 台账：已接入（含 `状态` 列与 `<!-- registry:active -->` 锚点）/ 已排除 / 更新历史三张表 | 3 |
| `.claude/skills/add-external-skill/known-issues.md` | 使用期反馈记录（空模板） | 3 |
| `.claude/skills/add-external-skill/CHANGELOG.md` | 起始 `[1.0.0]` | 3 |
| `.claude/skills/add-external-skill/test-prompts.json` | 触发词与预期行为用例 | 3 |
| `.kiro/skills/add-external-skill`、`.agents/skills/add-external-skill` | 双 harness 符号链接镜像 | 3 |
| `.githooks/pre-commit` | 插入第 3 项检查，原第 3 项顺延为第 4 项 | 4 |
| `.githooks/README.md` | 登记新检查的由来与能力边界 | 4 |
| `.claude-plugin/marketplace.json` | 补齐 `cangjie-skill` 三字段（Task 4）；新增 archify（6）、ppt-master（7）条目并各升顶层 Minor | 4/6/7 |
| `AGENTS.md` | 触发矩阵补两行、关键文件表登记传感器、提交一节的检查项描述加第 3 项 | 5 |
| `docs/todo-list/2026-09-08-todo.md` | 勾掉「将外部skill加入本库」 | 7 |

**为什么传感器先于 skill**：传感器定义了「合法条目长什么样」，是 skill 写入步骤的验收依据。反过来先写 skill 会让「怎样算写对」只存在于 prose 里。

**为什么 `registry.md` 必须在挂载 pre-commit 之前存在**：传感器第 6、7 项要求每条外部条目在台账「已接入」表有记录且 sha 一致，而存量 `cangjie-skill` 就是一条外部条目。台账不存在时挂载门禁会立刻阻断一切提交。

---

### Task 1: 传感器 `check_external_entries.py`

**Files:**
- Create: `.githooks/check_external_entries.py`
- Test: `.githooks/test_check_external_entries.py`

**Interfaces:**
- Consumes: 无（仅标准库）
- Produces:
  - `check_all(repo_root) -> list[str]`——返回问题描述列表，空列表表示通过。**签名与返回形状必须与既有 `check_plugin_versions.check_all` 一致**，因为 `pre-commit` 对两者的调用方式相同，且单测风格照抄既有文件。
  - `check_entry(entry: dict, active: dict) -> list[str]`
  - `check_upstream_files(repo_root: pathlib.Path) -> list[str]`
  - `registry_active(repo_root: pathlib.Path) -> tuple[dict, str | None]`——返回台账「已接入」表的 `名字 → sha` 映射（该行没有 40 位 sha 时值为 `None`）；第二元为错误串，非 `None` 时第一元为空 dict
  - `main() -> int`——退出码 0 通过、1 阻断
  - 模块级常量：`MARKETPLACE_REL`、`REGISTRY_REL`、`ACTIVE_MARKER`、`ALLOWED_SOURCES`、`REQUIRED_META`、`SHA_RE`、`SHA_IN_TEXT_RE`

⚠️ **`registry_active` 取代了原设想的 `registry_names(...) -> (set, err)`**，因为 spec § 5.1 第 7 项要求按名字比对 sha，一个 set 拿不到 sha。连带两个变化，都要照做：

1. **台账「已接入」表前必须有机器可读锚点 `<!-- registry:active -->`。** 原设想「扫全文所有表格的首列」是为了不依赖章节标题的措辞，但那样无法区分「已接入」行与「更新历史」行——后者首列也是条目名，且一行里有旧、新两个 sha。锚点比措辞稳定，标题怎么改都不影响解析。
2. **登记检查因此变严：条目名必须出现在「已接入」表里**，只出现在更新历史或已排除表里不算登记。这比原设想更精确，不是放松。锚点缺失本身要报错（可机械判定），不得静默跳过——静默跳过会让第 7 项整体失效而没人知道。

- [ ] **Step 1: 写失败的测试**

创建 `.githooks/test_check_external_entries.py`：

```python
import json
import pathlib
import shutil
import tempfile
import unittest

from check_external_entries import check_all

GOOD_SHA = "b633a4fad5a02f0fc6b2524d1ddf3ed50c753a40"
OLD_SHA = "0123456789abcdef0123456789abcdef01234567"


def entry(**over):
    """一条合法的 url 型外部条目，用关键字参数覆盖任意字段。"""
    e = {
        "name": "ext-a",
        "description": "外部引入的示例 skill",
        "homepage": "https://example.com/ext-a",
        "author": {"name": "someone"},
        "source": {
            "source": "url",
            "url": "https://example.com/ext-a.git",
            "ref": "main",
            "sha": GOOD_SHA,
        },
    }
    e.update(over)
    return e


def write_marketplace(root, plugins):
    d = root / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "marketplace.json").write_text(
        json.dumps({"name": "m", "version": "1.0.0", "plugins": plugins},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_registry(root, names, sha=GOOD_SHA, marker=True, history=()):
    """造台账。names 进「已接入」表；history 里的名字只进「更新历史」表。

    sha=None 表示「已接入」行不写 sha（模拟漏记）；marker=False 表示缺锚点。
    """
    d = root / ".claude" / "skills" / "add-external-skill"
    d.mkdir(parents=True, exist_ok=True)
    head = "# 台账\n\n## 已接入\n\n"
    if marker:
        head += "<!-- registry:active -->\n"
    head += ("| 条目名 | 方式 | 上游 | ref | sha | 接入日期 | 形态分支 | 状态 |\n"
             "|---|---|---|---|---|---|---|---|\n")
    rows = "".join(
        f"| `{n}` | 链接 | https://example.com/{n} | main | "
        f"{sha if sha else '—'} | 2026-09-12 | 根目录裸 SKILL.md | 正常 |\n"
        for n in names)
    tail = ""
    if history:
        tail = ("\n## 更新历史\n\n| 条目名 | 旧 sha | 新 sha | 日期 | 结果 |\n"
                "|---|---|---|---|---|\n")
        tail += "".join(
            f"| `{n}` | {OLD_SHA} | {GOOD_SHA} | 2026-09-12 | 成功 |\n" for n in history)
    (d / "registry.md").write_text(head + rows + tail, encoding="utf-8")



def write_vendored(root, name, upstream_body):
    """在 external_plugins/ 下造一个拷贝模式插件。upstream_body 传 None 表示不建 UPSTREAM.md。"""
    d = root / "external_plugins" / name
    d.mkdir(parents=True, exist_ok=True)
    if upstream_body is not None:
        (d / "UPSTREAM.md").write_text(upstream_body, encoding="utf-8")
    return d


class TestCheckExternalEntries(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # ---------- 应通过 ----------

    def test_valid_url_entry_passes(self):
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"])
        self.assertEqual(check_all(self.root), [])

    def test_valid_git_subdir_entry_with_path_passes(self):
        e = entry(source={"source": "git-subdir", "url": "https://example.com/r.git",
                          "path": "skills", "ref": "main", "sha": GOOD_SHA})
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        self.assertEqual(check_all(self.root), [])

    def test_strict_false_with_skills_array_passes(self):
        write_marketplace(self.root, [entry(strict=False, skills=["./sub"])])
        write_registry(self.root, ["ext-a"])
        self.assertEqual(check_all(self.root), [])

    def test_entry_without_ref_passes(self):
        """ref 是可选的（官方 243 条里只有 36% 带 ref），sha 才是生效的 pin。"""
        e = entry(source={"source": "url", "url": "https://example.com/r.git", "sha": GOOD_SHA})
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        self.assertEqual(check_all(self.root), [])

    def test_local_path_string_source_is_skipped(self):
        """source 为本地相对路径字符串的条目不适用本检查，且不要求台账登记。"""
        write_marketplace(self.root, [{"name": "first-party",
                                       "source": "./plugins/first-party",
                                       "description": "d"}])
        self.assertEqual(check_all(self.root), [])

    def test_no_external_plugins_dir_passes(self):
        """拷贝模式尚未使用时该目录不存在，视为通过（保持幂等）。"""
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"])
        self.assertFalse((self.root / "external_plugins").exists())
        self.assertEqual(check_all(self.root), [])

    def test_vendored_plugin_with_upstream_sha_passes(self):
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"])
        write_vendored(self.root, "v-ok", f"# UPSTREAM\n\ncommit: {GOOD_SHA}\n")
        self.assertEqual(check_all(self.root), [])

    def test_name_in_both_active_and_history_passes(self):
        """更新过的条目会同时出现在两张表里；更新历史行里的旧 sha 不得被当成现状。"""
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"], history=["ext-a"])
        self.assertEqual(check_all(self.root), [])

    # ---------- 应阻断 ----------

    def test_missing_sha_blocked(self):
        e = entry(source={"source": "url", "url": "https://example.com/r.git", "ref": "main"})
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("sha", problems[0])

    def test_abbreviated_sha_blocked(self):
        e = entry(source={"source": "url", "url": "https://example.com/r.git",
                          "ref": "main", "sha": "b633a4f"})
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        self.assertEqual(len(check_all(self.root)), 1)

    def test_uppercase_sha_blocked(self):
        e = entry(source={"source": "url", "url": "https://example.com/r.git",
                          "ref": "main", "sha": GOOD_SHA.upper()})
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        self.assertEqual(len(check_all(self.root)), 1)

    def test_version_in_entry_blocked(self):
        write_marketplace(self.root, [entry(version="1.0.0")])
        write_registry(self.root, ["ext-a"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("version", problems[0])

    def test_strict_false_without_skills_blocked(self):
        write_marketplace(self.root, [entry(strict=False)])
        write_registry(self.root, ["ext-a"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("skills", problems[0])

    def test_strict_false_with_empty_skills_blocked(self):
        write_marketplace(self.root, [entry(strict=False, skills=[])])
        write_registry(self.root, ["ext-a"])
        self.assertEqual(len(check_all(self.root)), 1)

    def test_unknown_source_type_blocked(self):
        e = entry(source={"source": "npm", "url": "https://example.com/r.git", "sha": GOOD_SHA})
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("npm", problems[0])

    def test_git_subdir_without_path_blocked(self):
        e = entry(source={"source": "git-subdir", "url": "https://example.com/r.git",
                          "ref": "main", "sha": GOOD_SHA})
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("path", problems[0])

    def test_missing_homepage_blocked(self):
        e = entry()
        del e["homepage"]
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("homepage", problems[0])

    def test_missing_author_and_description_both_reported(self):
        e = entry()
        del e["author"]
        del e["description"]
        write_marketplace(self.root, [e])
        write_registry(self.root, ["ext-a"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 2)

    def test_entry_absent_from_registry_blocked(self):
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["someone-else"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("registry.md", problems[0])

    def test_missing_registry_file_blocked_when_external_entries_exist(self):
        write_marketplace(self.root, [entry()])
        problems = check_all(self.root)
        self.assertTrue(problems)
        self.assertIn("registry.md", problems[0])

    def test_registry_sha_mismatch_blocked(self):
        """台账 sha 与条目 sha 不一致 = 上一次更新做了一半。spec § 5.1 第 7 项。"""
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"], sha=OLD_SHA)
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("不一致", problems[0])
        # 不得给「以某一份为准」式指引——两边都可能是错的那一边
        self.assertNotIn("为准", problems[0])

    def test_registry_active_row_without_sha_blocked(self):
        """已接入行漏记 sha：第 7 项无从比对，等于这道刹车被悄悄拆了。"""
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"], sha=None)
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("sha", problems[0])

    def test_missing_active_marker_blocked(self):
        """锚点缺失必须报错而不是静默跳过——静默跳过会让第 7 项整体失效。"""
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"], marker=False)
        problems = check_all(self.root)
        self.assertTrue(problems)
        self.assertIn("registry:active", problems[0])

    def test_name_only_in_update_history_blocked(self):
        """只出现在更新历史里不算登记——那张表记的是发生过什么，不是现状。"""
        write_marketplace(self.root, [entry()])
        write_registry(self.root, [], history=["ext-a"])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("registry.md", problems[0])

    def test_vendored_plugin_without_upstream_md_blocked(self):
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"])
        write_vendored(self.root, "v-bad", None)
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("UPSTREAM.md", problems[0])

    def test_upstream_md_without_40_hex_sha_blocked(self):
        write_marketplace(self.root, [entry()])
        write_registry(self.root, ["ext-a"])
        write_vendored(self.root, "v-bad", "# UPSTREAM\n\ncommit: b633a4f\n")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("40", problems[0])

    def test_multiple_bad_entries_all_reported(self):
        e1 = entry(name="ext-a", version="1.0.0")
        e2 = entry(name="ext-b", strict=False)
        write_marketplace(self.root, [e1, e2])
        write_registry(self.root, ["ext-a", "ext-b"])
        self.assertEqual(len(check_all(self.root)), 2)

    # ---------- 健壮性与文案 ----------

    def test_invalid_json_is_reported_not_raised(self):
        d = self.root / ".claude-plugin"
        d.mkdir(parents=True)
        (d / "marketplace.json").write_text("{not json", encoding="utf-8")
        problems = check_all(self.root)   # 不得抛异常
        self.assertEqual(len(problems), 1)
        self.assertIn("无法解析", problems[0])

    def test_missing_marketplace_file_is_reported_not_raised(self):
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("无法读取", problems[0])

    def test_error_messages_do_not_name_an_authoritative_side(self):
        """沿用 check_plugin_versions 的原则：不给「以某一份为准」式指引。"""
        write_marketplace(self.root, [entry(version="1.0.0")])
        write_registry(self.root, ["ext-a"])
        for msg in check_all(self.root):
            self.assertNotIn("为准", msg)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest discover -s .githooks -p "test_check_external_entries.py"`
Expected: FAIL，报 `ModuleNotFoundError: No module named 'check_external_entries'`

- [ ] **Step 3: 写实现**

创建 `.githooks/check_external_entries.py`：

```python
#!/usr/bin/env python3
"""校验 .claude-plugin/marketplace.json 里外部引用条目的结构合规与来源可追。

只查机械可判定项，一律不联网——提交门禁联网会让离线提交失败，代价大于收益。
因此本脚本保证的是「条目结构正确、来源可追」，不保证条目指向的内容真的存在、
真的是 skill、或真的还在维护；后者由实际安装验证与人承担。

设计依据：docs/superpowers/specs/2026-09-12-add-external-skill-design.md
"""
import json
import pathlib
import re
import sys

MARKETPLACE_REL = ".claude-plugin/marketplace.json"
REGISTRY_REL = ".claude/skills/add-external-skill/registry.md"
ACTIVE_MARKER = "<!-- registry:active -->"
ALLOWED_SOURCES = {"url", "github", "git-subdir"}
REQUIRED_META = ("description", "homepage", "author")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA_IN_TEXT_RE = re.compile(r"\b[0-9a-f]{40}\b")


def _load(path):
    """返回 (data, err)。err 非 None 时 data 为 None。"""
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"无法解析 JSON：{e}"
    except OSError as e:
        return None, f"无法读取：{e}"


def registry_active(repo_root):
    """取台账「已接入」表的 名字 -> sha 映射。返回 (mapping, err)。

    只认 ACTIVE_MARKER 之后、下一个 Markdown 标题之前的表格行。用锚点而不是
    章节标题的措辞定位，是因为措辞会被改；也不扫全文所有表格——「更新历史」
    行的首列同样是条目名，且一行里有旧、新两个 sha，混进来会让 sha 比对失效。

    行内没有 40 位 SHA 时值为 None，由调用方报「已接入行漏记 sha」。
    """
    path = repo_root / REGISTRY_REL
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return {}, f"无法读取 {REGISTRY_REL}：{e}"
    if ACTIVE_MARKER not in text:
        return {}, (f"{REGISTRY_REL} 缺锚点 {ACTIVE_MARKER}"
                    f"——「已接入」表前必须有它，否则无法机械定位现状行，"
                    f"台账与条目的 sha 一致性检查会整体失效")

    mapping = {}
    for line in text.split(ACTIVE_MARKER, 1)[1].splitlines():
        line = line.strip()
        if line.startswith("#"):
            break
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        name = cells[0].strip("`").strip()
        if not name or set(name) <= set("-: "):   # 跳过分隔行
            continue
        if name == "条目名":                       # 跳过表头
            continue
        found = SHA_IN_TEXT_RE.search(line)
        mapping[name] = found.group(0) if found else None
    return mapping, None


def check_entry(entry, active):
    """校验单条外部引用条目，返回问题描述列表。"""
    name = entry.get("name") or "<无 name 字段>"
    src = entry["source"]
    problems = []

    stype = src.get("source")
    if stype not in ALLOWED_SOURCES:
        problems.append(
            f"[{name}] source.source = {stype!r} 不在允许集合 "
            f"{sorted(ALLOWED_SOURCES)} 内")
    elif stype == "git-subdir" and not src.get("path"):
        problems.append(
            f"[{name}] git-subdir 源缺 path 字段"
            f"——子目录字段名是 path，不是 subdir")

    sha = src.get("sha")
    if not isinstance(sha, str) or not SHA_RE.match(sha):
        problems.append(
            f"[{name}] source.sha = {sha!r} 不是 40 位小写十六进制。"
            f"用 git ls-remote <url> <ref> 取全长值；缩写或缺失会退回"
            f"「跟随分支最新」，更新就不再是人工可控的")

    if "version" in entry:
        problems.append(
            f"[{name}] 条目内不得写 version——它会覆盖 sha 的更新信号，"
            f"且官方在 plugin.json 与 marketplace 条目同时声明时静默忽略后者")

    if entry.get("strict") is False:
        skills = entry.get("skills")
        if not isinstance(skills, list) or not skills:
            problems.append(
                f"[{name}] strict:false 时必须有非空 skills 数组，"
                f"否则外部仓无 plugin.json 时整条加载失败")

    for key in REQUIRED_META:
        if not entry.get(key):
            problems.append(f"[{name}] 缺 {key} 字段——缺失则来源不可追")

    if name not in active:
        problems.append(
            f"[{name}] 未登记在 {REGISTRY_REL} 的「已接入」表"
            f"——接进来但没有记录，下次没人知道它为什么在这里。"
            f"只出现在更新历史里不算：那张表记的是发生过什么，不是现状")
    elif active[name] is None:
        problems.append(
            f"[{name}] 台账「已接入」行没有 40 位 sha，无法与条目比对"
            f"——漏记 sha 会让「更新做了一半」这类状态无人发现")
    elif isinstance(sha, str) and SHA_RE.match(sha) and active[name] != sha:
        problems.append(
            f"[{name}] 台账 sha（{active[name]}）与条目 source.sha（{sha}）不一致。"
            f"这通常意味着上一次更新只做了一半：改了条目没记台账，或回滚了条目"
            f"没回滚台账。先判明哪一个对应实际验证过的状态，再改另一个——"
            f"不要为了消除本条报错而随手对齐")

    return problems


def check_upstream_files(repo_root):
    """拷贝模式：external_plugins/*/ 必须有 UPSTREAM.md 且含 40 位 SHA。

    该目录不存在时视为通过——拷贝模式尚未使用是正常状态。
    """
    base = repo_root / "external_plugins"
    if not base.is_dir():
        return []
    problems = []
    for sub in sorted(base.iterdir()):
        if not sub.is_dir():
            continue
        try:
            text = (sub / "UPSTREAM.md").read_text(encoding="utf-8")
        except OSError:
            problems.append(
                f"[{sub.name}] 缺 external_plugins/{sub.name}/UPSTREAM.md"
                f"——它是拷贝模式唯一的防漂移记账")
            continue
        if not SHA_IN_TEXT_RE.search(text):
            problems.append(
                f"[{sub.name}] UPSTREAM.md 里没有 40 位小写十六进制的 commit SHA，"
                f"无法确定这份副本拷自上游哪一版")
    return problems


def check_all(repo_root):
    """遍历 marketplace.json 的外部引用条目与 external_plugins/，返回全部问题。"""
    repo_root = pathlib.Path(repo_root)
    data, err = _load(repo_root / MARKETPLACE_REL)
    if err:
        return [f"{MARKETPLACE_REL} {err}"]

    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        return [f"{MARKETPLACE_REL} 的 plugins 字段不是数组"]

    # source 为本地相对路径字符串的条目不适用本检查
    external = [p for p in plugins
                if isinstance(p, dict) and isinstance(p.get("source"), dict)]
    if not external:
        return check_upstream_files(repo_root)

    names, err = registry_active(repo_root)
    if err:
        return [err] + check_upstream_files(repo_root)

    problems = []
    for e in external:
        problems.extend(check_entry(e, names))
    problems.extend(check_upstream_files(repo_root))
    return problems


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    problems = check_all(root)
    if problems:
        print("外部引用条目校验未通过：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("外部引用条目校验通过：sha 已锁定、无 version、来源可追、台账已登记且 sha 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest discover -s .githooks -p "test_check_external_entries.py" -v`
Expected: 30 条全部 PASS——8 条应通过 + 19 条应阻断 + 3 条健壮性与文案

⚠️ **此时不要对真实仓库跑 `python .githooks/check_external_entries.py .`**——它必然失败：存量 `cangjie-skill` 条目缺 `homepage`/`author`，且 `registry.md` 尚未创建。让它转绿是 Task 3 与 Task 4 的事。

- [ ] **Step 5: 跑既有单测确认无回归**

Run: `python -m unittest discover -s .githooks -p "test_*.py"`
Expected: 新旧全部 PASS

- [ ] **Step 6: 提交**

### Task 2: `check_plugin_versions.py` 扫描范围扩到 `external_plugins/`

拷贝模式的产物是本仓自己维护的双 harness 分发单元，必须落进两份 `plugin.json` 同值的管辖范围。**先就位是为了让第一次拷贝不落进门禁盲区**——本次没有真实被测对象（首批两个目标都走链接），只有单测能覆盖。

**Files:**
- Modify: `.githooks/check_plugin_versions.py:88-99`（`check_all`）
- Test: `.githooks/test_check_plugin_versions.py`（改 `make_plugin` helper + 补 5 例）

**Interfaces:**
- Consumes: 既有 `check_plugin(plugin_dir) -> list[str]`，不改
- Produces: `check_all` 行为扩展；新增模块级常量 `SCAN_DIRS = ("plugins", "external_plugins")`

- [ ] **Step 1: 写失败的测试**

先把既有 helper 加一个默认参数（既有用例不受影响），在 `.githooks/test_check_plugin_versions.py` 中把 `make_plugin` 的前两行改为：

```python
def make_plugin(root, name, claude_ver, codex_ver, claude_extra=None, base_dir="plugins"):
    """在临时仓库里造一个插件。ver 传 None 表示不建该文件。"""
    base = root / base_dir / name
```

然后在 `TestCheckPluginVersions` 类末尾（`test_directory_without_any_plugin_json_is_skipped` 之后）追加：

```python
    def test_external_plugins_dir_absent_passes(self):
        """拷贝模式尚未使用时该目录不存在，视为通过（保持幂等）。"""
        make_plugin(self.root, "p-ok", "1.0.0", "1.0.0")
        self.assertFalse((self.root / "external_plugins").exists())
        self.assertEqual(check_all(self.root), [])

    def test_vendored_plugin_same_version_passes(self):
        make_plugin(self.root, "v-ok", "2.0.0", "2.0.0", base_dir="external_plugins")
        self.assertEqual(check_all(self.root), [])

    def test_vendored_plugin_version_mismatch_is_reported(self):
        make_plugin(self.root, "v-bad", "2.0.0", "2.0.1", base_dir="external_plugins")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("v-bad", problems[0])

    def test_vendored_plugin_missing_codex_side_is_reported(self):
        make_plugin(self.root, "v-no-codex", "2.0.0", None, base_dir="external_plugins")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn(".codex-plugin/plugin.json", problems[0])

    def test_vendored_prerelease_version_pair_passes(self):
        """有本地改动时版本形如 <上游版本>-optimus.N，两份同值即通过。"""
        make_plugin(self.root, "v-patched", "2.0.0-optimus.1", "2.0.0-optimus.1",
                    base_dir="external_plugins")
        self.assertEqual(check_all(self.root), [])

    def test_both_dirs_scanned_in_one_run(self):
        make_plugin(self.root, "p-bad", "1.0.0", "1.0.1")
        make_plugin(self.root, "v-bad", "2.0.0", "2.0.1", base_dir="external_plugins")
        self.assertEqual(len(check_all(self.root)), 2)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m unittest discover -s .githooks -p "test_check_plugin_versions.py" -v`
Expected: 6 条新用例中**恰好 3 条 FAIL**——`test_vendored_plugin_version_mismatch_is_reported`、`test_vendored_plugin_missing_codex_side_is_reported`、`test_both_dirs_scanned_in_one_run`（预期问题数 > 0，实际 0，因为 `external_plugins/` 当前完全不被扫描）。

另外 3 条会**假通过**：`test_external_plugins_dir_absent_passes` 本就该通过；`test_vendored_plugin_same_version_passes` 与 `test_vendored_prerelease_version_pair_passes` 因为目录没被扫描而返回空列表，恰好等于预期值。它们在 Step 3 之后才真正有效——**这是这两条用例的已知局限，不要因为它们一开始就绿而删掉**。

- [ ] **Step 3: 写实现**

把 `.githooks/check_plugin_versions.py` 的 `check_all` 整体替换为：

```python
SCAN_DIRS = ("plugins", "external_plugins")


def check_all(repo_root):
    """遍历 SCAN_DIRS 下所有插件目录，返回全部问题描述列表。

    external_plugins/ 是拷贝模式引入的外部 skill 的落点（见
    docs/superpowers/specs/2026-09-12-add-external-skill-design.md § 3.3）。
    它与 plugins/ 同样是双 harness 分发单元，因此同受两份同值规则约束；
    该目录不存在时跳过——拷贝模式尚未使用是正常状态。
    """
    repo_root = pathlib.Path(repo_root)
    plugins_dir = repo_root / "plugins"
    if not plugins_dir.is_dir():
        return [f"plugins/ 目录不存在：{plugins_dir}"]

    problems = []
    for rel in SCAN_DIRS:
        base = repo_root / rel
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir():
                problems.extend(check_plugin(d))
    return problems
```

`SCAN_DIRS` 放模块级常量而非写死在循环里，是为了让「哪些目录受管辖」这件事在文件顶部可见，不必读完函数体。

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m unittest discover -s .githooks -p "test_*.py" -v`
Expected: 全部 PASS——既有 12 例 + 本 Task 新增 6 例 + Task 1 的 30 例 = 48 例

- [ ] **Step 5: 对真实仓库验证无回归**

Run: `python .githooks/check_plugin_versions.py .`
Expected: 退出 0，打印「所有插件的两份 plugin.json 同值」。`external_plugins/` 在本仓不存在，被跳过。

- [ ] **Step 6: 提交**

### Task 3: skill 骨架与台账落地

**Files:**
- Create: `.claude/skills/add-external-skill/SKILL.md`
- Create: `.claude/skills/add-external-skill/registry.md`
- Create: `.claude/skills/add-external-skill/known-issues.md`
- Create: `.claude/skills/add-external-skill/CHANGELOG.md`
- Create: `.claude/skills/add-external-skill/test-prompts.json`
- Create: `.kiro/skills/add-external-skill`（符号链接）
- Create: `.agents/skills/add-external-skill`（符号链接）

**Interfaces:**
- Consumes: Task 1 的 `.githooks/check_external_entries.py`——SKILL.md 的 Step 6「验证」要求跑它，且台账路径必须与该脚本的 `REGISTRY_REL` 常量逐字一致（`.claude/skills/add-external-skill/registry.md`）
- Produces: `/add-external-skill` 可被人显式调用；`registry.md` 的「已接入」表带 `<!-- registry:active -->` 锚点，被传感器第 6、7 项按该锚点解析（见 Task 1 `registry_active` 的 docstring）——**锚点缺失会让门禁报错，不是可选装饰**

- [ ] **Step 1: 写 SKILL.md 的 frontmatter**

六字段 + **一个 Claude Code 原生字段 `disable-model-invocation`**（spec § 4.1）：

```yaml
---
name: add-external-skill
description: 把外部仓库的 Agent Skill 接入本仓库，或更新已接入条目的版本锁定。探测上游仓库形态、判定落位方式（默认链接：marketplace 条目锁 40 位 sha；例外才拷贝到 external_plugins/）、取 sha、人在回路确认、写入并验证、记台账。更新失败一次即停，不重试、不轮询。只能由人显式调用 /add-external-skill 触发。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要 git（用 git ls-remote 取上游 sha）与可达上游仓库的网络；写入后的验证步骤需要 claude CLI 的 plugin 子命令；传感器 .githooks/check_external_entries.py 需要 Python 3 标准库。
allowed-tools: Read Write Edit Bash Grep WebFetch
disable-model-invocation: true
---
```

⚠️ **`description` 里刻意不写「用户说……时使用」那串触发词**。带 `disable-model-invocation: true` 后模型不会按 description 匹配拉起本 skill，留着触发词只会让后人误以为存在自动触发路径。末句改为明写唯一入口。

⚠️ **这个字段是有意为之，不是规范偏差。** 三件事必须知道，否则会被「顺手修正」掉：

1. `skills-ref validate` 必然报 `Unexpected key(s): disable-model-invocation`，**那是预期结果**。该字段是 Claude Code 原生合法字段，不需登记豁免（口径同 `sync-cc-tips`）。
2. Codex 侧对未知顶层字段是忽略还是硬报错**未实测**。Task 3 收尾前必须在 Codex 中触发一次同名 skill 验证，结论写进 `known-issues.md`（验收第 13 项）。**若确认硬报错，停下来报告——该字段与 Codex 镜像不可兼得，需要重新裁决，不要自行取舍。**
3. 它同时使 `/loop` 等计划触发把本 skill 当纯文本而不执行。**这正是要的**：更新必须由人发起。

- [ ] **Step 2: 写 SKILL.md 正文**

按以下章节顺序，内容依据 spec 对应节展开。**写之前必须先读 spec 的 §§ 1.2、3.1–3.4、4.1–4.5、5.2**——下表「内容来源」列不是索引，是必读项；表里的「硬点」是不得遗漏的最小集，不是全部内容。**每个 Step 必须作为独立小节呈现，前置校验不得混入「失败处理」章节**（`skill-conventions.md` 明确要求两者分开：前置校验是执行前主动探测，失败处理是执行中才暴露的报错）。

| 章节 | 内容来源 | 必须写进去的硬点 |
|---|---|---|
| `## 适用范围与边界` | spec § 1.2 | 三条不做：不做 Codex 侧远程引用覆盖（结构性不可行，`cangjie-skill` 已确立先例）、不修改上游内容（需要改则由人显式决定 fork）、不建 `external_plugins/` 除非命中拷贝判据 |
| `## 触发方式` | spec § 4.1 | **本 skill 只能由人显式 `/add-external-skill` 触发**：不支持模型按 description 自主拉起，也不支持 `/loop` 等无人值守调度（`disable-model-invocation: true` 的官方行为，v2.1.196 起）。写明该字段解决什么问题：本 skill 会把能在用户权限下执行任意代码的第三方插件写进 marketplace，「是否现在讨论引入某个外部插件」应由人发起。并写明 `skills-ref validate` 报 `Unexpected key(s)` 是预期结果、**不要顺手删掉它来「修规范」** |
| `## 两个模式` | spec § 4.1 | 接入 / 更新两行表；并写明为什么更新必须与接入同处一个 skill（「更新失败不重试」是锁 sha 的直接后果，拆开会口径漂移）。**两行的「触发」列都是「人显式调用」，不得写自然语言触发词** |
| `## Step 0：需求预告` | spec § 4.2 + `skill-conventions.md`「需求预告」 | 只比对用户可提供的信息（上游 URL、条目名），**依赖状态不计入缺失项**；信息齐全则跳过本步；本步不做任何系统调用 |
| `## Step 1：执行前置校验` | spec § 4.2 的四类表 | 四类逐条列出；**运行条件的两项（License 可确认、上游存在可识别 skill 载体）都是硬约束，不是可协商风险**，并写明理由 |
| `## Step 2：形态判定` | spec § 4.3 的五分支表 | 五行表整表照搬，含「根目录是 marketplace.json 而非 plugin.json」这一易错行，与「第三行为什么选 `url` + `skills:["./<子目录>"]`」的先例论证 |
| `## Step 3：取 sha` | spec § 4.2 | 命令 `git ls-remote <url> <ref>`；写明为什么不用 GitHub API（`ls-remote` 对任意 git 主机成立，无速率限制与鉴权问题）；`ref` 不得假定为 `main`，已知反例 `master` 与 `v8` |
| `## Step 4：🔴 CHECKPOINT` | spec § 4.2 | 必须展示的五项：探测结论与所选形态、40 位 sha、License、**该 skill 会带进来什么**（`scripts/`/`hooks/`/`.mcp.json`/需装依赖）、Codex 侧是否覆盖。引官方原话「can execute arbitrary code on your machine with your user privileges」说明该确认点不可省 |
| `## Step 5：写入` | spec § 3.1、§ 8 | 四条硬规则（必锁 sha / 永不写 version / ref 与 sha 并写 / 补齐 `description`+`homepage`+`author`，`category` 建议不强制）；给出 `url` 型与 `git-subdir` 型两个条目模板 |
| `## Step 6：验证` | spec § 4.2 | `claude plugin marketplace update optimus-plugins-official` → `claude plugin install <name>@optimus-plugins-official` → 确认 skill 可列出；再跑 `python .githooks/check_external_entries.py .` |
| `## Step 7：收尾` | spec § 7、§ 9 | 记台账（**行落在 `<!-- registry:active -->` 锚点之后，含 `状态` 列**）、marketplace 顶层升 Minor（先例 `4d741b8`）、调用 `/commit-cc-plugin` 提交（禁止手动 git） |
| `## 更新模式` | spec § 4.4 + § 4.4.1–4.4.3 | 见下方展开表 |
| `## 失败处理` | spec § 4.5 + § 4.5.1–4.5.2 | 见下方展开表 |
| `## 拷贝模式` | spec § 3.2、§ 3.3、§ 3.4 | 两条正当理由 + 两条明确不构成理由（形态不适用→排除；离线可用→本仓无此约束）；落位目录树；version 两情形规则（未改动逐字等于上游／有改动加 `-optimus.N` 后缀）及其理由（缓存按 version 分目录，不变则改动装不上）。**本节末必须声明：该分支截至 1.0.0 未被任何真实用例验证，首次使用时按本节展开并在该次提交内补齐 `test-prompts.json` 用例** |
| `## 参考` | — | 指向 spec 路径与 `.githooks/check_external_entries.py` |

**确认点计数**：全文只有 2 个 🔴 CHECKPOINT（Step 4 与 U5）。若正文用中文数字复述确认点数量，必须与实际落地数一致。

#### `## 更新模式` 与 `## 失败处理` 的展开要求

这两节承载「严格把关更新，尤其是更新失败」，**是本 skill 最容易写薄的地方**——它们不能各只有一张表。逐条落地：

| 子节 | spec 出处 | 不得遗漏 |
|---|---|---|
| U0–U8 步骤表 | § 4.4 | **U0 明写本 skill 不提供任何「顺便检查有没有新版」的入口**：不扫全表、不批量更新、不因为接入了别的条目就连带检查已有条目。**U1 台账与条目 sha 不一致时立即终止**（这是上次更新做了一半的证据，不要自行对齐）。**U2 相同 sha 则报「已是最新」并结束，不做任何写入** |
| 「U6 在 U7 之前无法调换」 | § 4.4 表后的 ⚠️ | 安装验证需要条目已存在，所以「验证失败」必然发生在改了 sha 之后——**回滚是必经动作而非异常分支**。这一句是理解失败处理第四格的前提，不能省 |
| `ref` 变更处置 | § 4.4.1 | 三行表（ref 仍在 / 能认出改名后的对应 ref / 认不出）；**认不出时不猜，终止并记「ref 待选定」**；`ref` 变更必须在 CHECKPOINT 里单独列项，不与 sha 更新混为一谈 |
| 变更摘要怎么取 | § 4.4.2 | 三种手段与各自代价；首选 GitHub compare API（不落盘）；退到临时浅克隆时**克隆到系统临时目录、`--filter=blob:none`、用完即删，禁止落在仓库工作区内**（会污染 `git status`）。**取不到摘要不终止，但必须在 CHECKPOINT 如实声明「无法取得变更摘要，本次确认是在看不到改了什么的前提下做的」——绝不静默跳过确认** |
| 「不重试」不能只靠默认值 | § 4.4.3 | auto-update 关闭是**默认值不是不可变事实**：用户可能在 `/plugin` 里手动开过；`FORCE_AUTOUPDATE_PLUGINS=1` 会强制自动更新且不受 `DISABLE_AUTOUPDATER` 约束。U8 要**核实实际状态**并在发现被开启时报告给人，**不擅自改用户的全局设置** |
| 失败处理四格 | § 4.5 | 四格表（接入探测期 / 接入写入后 / **更新写入前** / **更新写入后**）。第四格必须写全：**把 sha（及 ref）回滚到 U6 记下的旧值 → 拷贝模式一并撤回目录与 version → 回滚后再跑一次验证确认已恢复可用 → 台账记「已回滚」并写明失败原因与回滚到的 sha** |
| 失败分类四类 | § 4.5.1 | 临时不可达 / **上游仓库已消失** / ref 已消失 / 安装验证失败，各自判据与处置。**「上游失联」必须落成台账的状态标记而不只是历史记录**，并写明理由：没有标记，每次更新都会把同一个已死的仓库重新试一遍，这就是「持续重试」，只不过轮询周期从定时器变成了人的记忆 |
| 记录落点 | § 4.5.2 | 上游侧的事 → `registry.md`；本 skill 自己的表现缺陷 → `known-issues.md`。判据是**谁该被改** |
| 三条共同硬规则 | § 4.5 | 不重试、不排定时任务、不自动改 sha |

- [ ] **Step 3: 写 registry.md**

```markdown
# add-external-skill · 外部 skill 接入台账

记录本仓库引入过的外部 skill。`.githooks/check_external_entries.py` 会校验
`marketplace.json` 里每条外部引用条目都在「已接入」表有记录，且**该行的 sha 与
条目的 `source.sha` 逐字一致**。

## 已接入

下面这行 HTML 注释是传感器的定位锚点，**不要删**——删掉会让台账与条目的 sha
一致性检查整体失效，门禁会直接报错。

<!-- registry:active -->
| 条目名 | 方式 | 上游 | ref | sha | 接入日期 | 形态分支 | 状态 |
|---|---|---|---|---|---|---|---|
| `cangjie-skill` | 链接 | https://github.com/kangarooking/cangjie-skill | main | b633a4fad5a02f0fc6b2524d1ddf3ed50c753a40 | 2026-08-29 | 根目录裸 SKILL.md | 正常 |

**`状态` 列取三值**，缺省 `正常`：

| 状态 | 含义 | 对下次更新的影响 |
|---|---|---|
| `正常` | 已验证可用 | 照常更新 |
| `上游失联` | 仓库 404 / 已删除 / 转为私有 | **U1 即报告并停**，不再去试。要恢复须人工重新确认上游 |
| `ref 待选定` | 仓库可达但目标 ref 认不出对应物 | 同上，须人工先定新 `ref` |

后两个状态的存在理由：没有状态列，「不重试」只能靠人记得哪个上游已经死了——
那不是不重试，只是把轮询周期换成了人的记忆。

## 已排除

两个子类的**复议条件不同**：形态不适用是技术判定，要等上游改变形态；决策暂缓是人的决定，改主意即可复议。

| 候选 | 子类 | 原因 | 复议条件 |
|---|---|---|---|
| `graphify` | 形态不适用 | Python CLI 项目（`pyproject.toml` + 51 个 .py）。skill 正文是 `graphify/skill.md`（小写）+ 15 个按 harness 分版，靠 `graphify install` 写入 harness 目录，仓库内无 `SKILL.md` 也无 `plugin.json` | 上游提供 `SKILL.md` 或 `.claude-plugin/plugin.json` 后可复议 |
| `darwin-skill` | 决策暂缓 | 2026-09-12 决定暂不引入。形态本身适用（`alchaincyf/darwin-skill` 根目录有 `SKILL.md`，无 `plugin.json`，ref 为 `master`） | 决定改变即可复议，无需等上游 |

## 更新历史

**失败与回滚的那次也必须留行**——否则「失败即停」会退化为「失败即忘」，下次仍从头试一遍同样的失败。

`结果` 取四值：`成功` / `失败（写入前）` / `已回滚（写入后验证失败）` / `已是最新`。
`已回滚` 行必须写明回滚到的 sha——它是「当前生效的 sha 为什么不是最新」的唯一答案来源。

| 日期 | 条目名 | 旧 sha | 新 sha | 结果 |
|---|---|---|---|---|
| — | 暂无记录 | — | — | — |
```

⚠️ **「已排除」与「更新历史」两张表刻意不放在锚点之后**——传感器只解析锚点到下一个 Markdown 标题之间的行，这两张表的首列同样是条目名（更新历史行里还有旧、新两个 sha），混进现状映射会让 sha 比对失效。新增章节时保持这个位置关系。

⚠️ `cangjie-skill` 那行的 sha 必须与 `marketplace.json` 里的现值逐字一致，写入前先 `grep -A6 '"name": "cangjie-skill"' .claude-plugin/marketplace.json` 核对，不要照抄本计划。

- [ ] **Step 4: 写 known-issues.md**

沿用本仓既有空模板格式：

```markdown
# add-external-skill · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-12 | 拷贝模式分支自 1.0.0 起从未被真实用例执行过——首批两个目标（archify、ppt-master）都走链接，`external_plugins/` 不会被创建 | — | 待处理 | — |
| 2026-09-12 | `disable-model-invocation: true` 在 Codex 侧的行为待实测填写：忽略未知顶层字段还是拒绝加载。风险是后者会让本 skill 在 Codex 侧整体失效，而镜像正是为 Codex 建的 | 在 Codex 中触发同名 skill | 待处理 | — |
| 2026-09-12 | 变更摘要在非 GitHub 上游上无成熟取法（compare API 绑定 GitHub，临时浅克隆要落盘）。首批目标都在 GitHub，首次引入非 GitHub 上游时须补 | 更新一个非 GitHub 上游的条目 | 待处理 | — |
```

后两条不是预留位：**第二条必须在 Task 3 收尾前实测并把结论改写进去**（验收第 13 项），不能留着「待实测」就提交。若实测为硬报错，停下来报告——该字段与 Codex 镜像不可兼得，需重新裁决。

这三条都不是凑数：第一条对应 spec § 10 第 1 项与验收第 10 项，第二、三条对应 spec § 10 新增的第 6、7 项。

- [ ] **Step 5: 写 CHANGELOG.md**

```markdown
# Changelog

## [1.0.0] - 2026-09-12

### Added
- 首个版本：把「引入外部 skill」固化为可反复执行的 skill，取代此前散落在提交信息里的一次性判断（先例 `4d741b8` 引入 `cangjie-skill`）
- 接入与更新两个模式；接入含需求预告、四类执行前置校验、五分支形态判定、`git ls-remote` 取 40 位 sha、人在回路 CHECKPOINT、写入、安装验证、台账登记
- 形态判定表覆盖五种上游形态，含「根目录是 marketplace.json 而非 plugin.json」与「靠 CLI 安装、判定不适用」两个易错分支
- 更新模式 U0–U8，含 `ref` 变更处置、变更摘要的三种取法与取不到时的如实声明、以及对 auto-update 实际状态的核实（不只依赖默认值）
- 失败处理四格：探测阶段失败即终止不留残留；接入写入后验证失败回滚本次写入；**更新写入前失败旧 sha 原样保留**；**更新写入后验证失败必须把 sha 回滚到旧值并记「已回滚」**。三条共同硬规则：不重试、不排定时任务、不自动改 sha
- 更新失败分四类（临时不可达 / 上游仓库已消失 / ref 已消失 / 安装验证失败），「上游失联」落成台账状态标记而非仅历史记录——否则每次更新都会把同一个已死的仓库重试一遍
- `disable-model-invocation: true`：本 skill 只能由人显式调用，模型不按 description 自主拉起，`/loop` 等调度亦不执行
- 拷贝模式的两条正当理由与落位规范（含 version 取值的两情形规则）
- 配套台账 `registry.md`（已接入 / 已排除 / 更新历史三张表，已接入表带 `<!-- registry:active -->` 锚点与 `状态` 列）与传感器 `.githooks/check_external_entries.py`（8 项检查）
```

- [ ] **Step 6: 写 test-prompts.json**

```json
[
  {
    "id": 1,
    "prompt": "把 https://github.com/tt-a1i/archify 这个 skill 加进本库",
    "expected": "识别为接入模式；探测出 SKILL.md 在 archify/ 子目录且全仓无 plugin.json，判定为 url + strict:false + skills:[\"./archify\"]；用 git ls-remote 取 40 位 sha；在写入前给出 CHECKPOINT 展示形态、sha、License 与该 skill 会带进来什么"
  },
  {
    "id": 2,
    "prompt": "加个外部 skill 进来",
    "expected": "识别为接入模式但信息不全，一次性问齐缺失项（上游仓库地址、条目名），不逐步卡顿式追问；不询问依赖是否就绪"
  },
  {
    "id": 3,
    "prompt": "把 https://github.com/Graphify-Labs/graphify 接进来，用 v8 分支",
    "expected": "探测出仓库无 SKILL.md、无 plugin.json，skill 正文是 graphify/skill.md 小写且按 harness 分版、靠 graphify install 落地；判定为形态不适用，终止接入并写入 registry.md 的已排除表（子类：形态不适用），不改为拷贝模式"
  },
  {
    "id": 4,
    "prompt": "更新一下 cangjie-skill",
    "expected": "识别为更新模式；从 registry.md 读当前 sha，用 git ls-remote 取上游最新 sha；两者相同则报告「已是最新」并结束，不做任何写入"
  },
  {
    "id": 5,
    "prompt": "刚才更新 archify 的时候拉取失败了，要不要设个定时任务每小时重试一次？",
    "expected": "明确拒绝：旧 sha 是已验证的可用状态、原样保留；失败原因与时间写进 registry.md 更新历史；不重试、不排定时任务、不自动改 sha。并说明锁 sha + 不写 version 已使 harness 层面的 update 直接 skip，重试机制本身不必要"
  },
  {
    "id": 6,
    "prompt": "这个外部 skill 我想直接把文件拷进来，不用链接",
    "expected": "指出默认是链接，拷贝只有两条正当理由（需要 Codex 侧生效／必须改内容且拒绝 fork）；先问清属于哪一条，不满足则仍走链接。若确认走拷贝，说明落位在 external_plugins/<name>/ 且需两份 plugin.json 同值、UPSTREAM.md 记账、version 按上游版本取值"
  },
  {
    "id": 7,
    "prompt": "archify 的 sha 我已经改成新的了，但装的时候 skill 列不出来",
    "expected": "识别为更新的写入后失败；把 sha（必要时含 ref）回滚到旧值，拷贝模式一并撤回目录与 version；回滚后再跑一次验证确认已恢复可用；在 registry.md 更新历史记「已回滚」并写明失败原因与回滚到的 sha。不重试、不尝试换个 sha 再试"
  },
  {
    "id": 8,
    "prompt": "更新 ppt-master 的时候提示仓库 404，上游好像被删了",
    "expected": "判定为「上游仓库已消失」而非临时不可达；不重试；在 registry.md 已接入行把状态标记为「上游失联」，并说明理由——只记一行历史下次还会把同一个已死的仓库重试一遍，那是把轮询周期换成了人的记忆。同时说明现有条目仍锁在旧 sha、已装好的插件不受影响"
  },
  {
    "id": 9,
    "prompt": "帮我把台账里所有外部 skill 都查一遍看有没有新版",
    "expected": "拒绝批量巡检：本 skill 不提供「顺便检查有没有新版」的入口，更新一次只处理一个明确指名的条目。可以说明为什么——批量巡检等价于人工轮询，与「更新失败不重试」的设计相抵。请用户指名要更新哪一条"
  },
  {
    "id": 10,
    "prompt": "台账里 cangjie-skill 写的 sha 和 marketplace.json 里的不一样，帮我改一致",
    "expected": "不直接对齐两边。指出这是上一次更新只做了一半的证据（改了条目没记台账，或回滚了条目没回滚台账），先判明哪一个对应实际验证过的状态，再改另一个。可提示 .githooks/check_external_entries.py 第 7 项就是拦这个"
  }
]
```

⚠️ **id 7–10 是本次新增的四条，覆盖「更新失败」的四类形态**（写入后失败要回滚、上游永久消失要标状态、拒绝批量巡检、台账与条目不一致不得随手对齐）。它们是要求「严格把关更新失败」的可测量落点——**不得因为凑数而删减**。原有 id 5 只覆盖「不要设定时任务」，不覆盖回滚。

- [ ] **Step 7: 建两处符号链接镜像**

Run:
```bash
ln -s ../../.claude/skills/add-external-skill .kiro/skills/add-external-skill
ln -s ../../.claude/skills/add-external-skill .agents/skills/add-external-skill
```

- [ ] **Step 8: 验证镜像以 `120000` 模式入库**

Run: `git add .kiro/skills/add-external-skill .agents/skills/add-external-skill && git ls-files -s .kiro/skills .agents/skills | grep add-external-skill`
Expected: 两行都以 `120000` 开头。若出现 `100644`，说明 `core.symlinks=false` 把链接存成了内容为路径字符串的普通文件——执行 `git config core.symlinks true`，删掉这两个条目重建后再 add。

- [ ] **Step 9: 实测 Codex 侧对 `disable-model-invocation` 的行为**

在 Codex 中触发一次 `add-external-skill`（同名触发），观察三种结果之一：

| 观察到 | 判定 | 动作 |
|---|---|---|
| skill 正常加载，字段被忽略 | 兼容 | 把结论写进 `known-issues.md` 第 2 条并把状态改为「已确认」 |
| 加载了但有告警 | 可接受 | 同上，附告警原文 |
| **拒绝加载 / 报错** | **不兼容** | **停下来报告**。该字段与 Codex 镜像不可兼得，需要重新裁决（保字段舍镜像，或保镜像改用别的方式约束触发）——不要自行取舍，也不要顺手删字段 |

这是验收第 13 项。**不得跳过后在 `known-issues.md` 里留「待实测」就提交**——那等于把一个可能让 skill 在半个 harness 上完全失效的未知带过验收。

- [ ] **Step 10: 提交**

### Task 4: 挂载门禁并让全仓转绿

补齐存量条目 → 挂第 3 项 → 全仓通过。**顺序不能颠倒**：先挂门禁会立刻阻断一切提交。

**Files:**
- Modify: `.claude-plugin/marketplace.json`（`cangjie-skill` 条目补三字段）
- Modify: `.githooks/pre-commit:33-35`（第 2 项之后插入第 3 项，原第 3 项注释顺延为第 4 项）
- Modify: `.githooks/README.md`

**Interfaces:**
- Consumes: Task 1 的 `check_external_entries.py`、Task 3 的 `registry.md`
- Produces: `bash .githooks/pre-commit` 退出 0，四项检查全过

- [ ] **Step 1: 补齐 `cangjie-skill` 的三个缺失字段**

先看现值：`grep -n -A10 '"name": "cangjie-skill"' .claude-plugin/marketplace.json`

在该条目的 `skills` 之后追加三个字段（**不动** `description` 与 `source`，只补缺失项）：

```jsonc
      "strict": false,
      "skills": ["./"],
      "author": { "name": "kangarooking" },
      "homepage": "https://github.com/kangarooking/cangjie-skill",
      "category": "productivity"
```

**这不是「顺手改进」。** 传感器第 5 项机械上无法区分新旧条目，上线即拦住存量条目；补齐是传感器上线的必要代价。提交信息里必须写明这一归因，否则后人会以为是范围外的顺手整理。

- [ ] **Step 2: 验证传感器对真实仓库转绿**

Run: `python .githooks/check_external_entries.py .`
Expected: 退出 0，打印「sha 已锁定、无 version、来源可追、台账已登记且 sha 一致」

若报 `cangjie-skill 未登记在 .claude/skills/add-external-skill/registry.md 的「已接入」表`，说明 Task 3 Step 3 的台账里条目名拼写与 marketplace 不一致，或该行不在 `<!-- registry:active -->` 锚点之后——回头核对。若报 sha 不一致，**不要改台账去迁就条目**，先确认 marketplace 里的现值才是实际验证过的那个（对 cangjie 而言它是，因为条目早于台账存在）。

- [ ] **Step 3: 在 pre-commit 插入第 3 项**

在第 2 项的 `fi` 之后、`# --- 3. .claude/skills 的双 harness 符号链接镜像 ---` 之前插入：

```sh
# --- 3. marketplace 外部引用条目的结构合规 ---
# 只查机械可判定项：sha 是否 40 位全长、条目是否误写 version、strict:false 是否配了
# 非空 skills 数组、source 类型与 git-subdir 的 path、展示元数据是否齐备、是否登记进
# 台账「已接入」表，以及台账 sha 与条目 sha 是否一致（不一致 = 上次更新做了一半）。
# 这些错误都不报错：漏 sha 只是静默退回「跟随分支最新」，缺 skills 数组则整条加载失败。
# 刻意不联网——不校验 sha 是否真存在于上游、上游有没有新 commit（后者正是要避免的）。
# 完整判据见 docs/superpowers/specs/2026-09-12-add-external-skill-design.md § 5。
if ! python .githooks/check_external_entries.py . ; then
  fail=1
fi
```

同时把原第 3 项的注释首行改为 `# --- 4. .claude/skills 的双 harness 符号链接镜像 ---`。**只改这一行注释编号，不动它下面的循环逻辑。**

- [ ] **Step 4: 跑完整门禁**

Run: `bash .githooks/pre-commit`
Expected: 退出 0，打印「[pre-commit] 通过」。四项检查全过。

- [ ] **Step 5: 更新 `.githooks/README.md`**

先 `Read .githooks/README.md` 看现有检查项的记述格式，照该格式追加一条。必须写到的两点：新检查的由来（条目写歪只会静默失效或整条加载失败，是需要借提交关口拦的形态），以及能力边界（不联网，因此「条目结构完美但上游仓库已删除」抓不到，只能由实际安装暴露）。

- [ ] **Step 6: 提交**

调用 `/commit-cc-plugin`。本次含 `marketplace.json`（仅 cangjie 三字段）、`pre-commit`、`.githooks/README.md`。提交要表达：挂载第 3 项门禁，补齐 cangjie 三字段作为门禁上线的必要代价（非顺手整理）。**不升 marketplace 顶层 version**——按矩阵，改插件条目的展示元数据不升顶层，且本次没有新增或删除插件。

---

### Task 5: AGENTS.md 规则登记

**Files:**
- Modify: `AGENTS.md`（版本管理触发矩阵、关键文件表、提交与推送一节）

**Interfaces:**
- Consumes: Task 4 已挂载的第 3 项检查
- Produces: 拷贝模式的版本规则有正式条款可依；Task 6/7 的顶层升版有矩阵依据

- [ ] **Step 1: 触发矩阵补三行**

在「触发矩阵：什么改动升哪一层」的表格中，`plugins/*/README.md` 行之后、`新增或删除整个插件` 行之前插入：

```markdown
| `external_plugins/*/` 内任一文件（拷贝模式引入的外部 skill） | ✅ | — | — | ❌ |
```

在 `新增或删除整个插件` 行之后插入两行：

```markdown
| **新增链接模式的外部引用条目**（marketplace 里 source 为 url/github/git-subdir） | — 无该文件 | — | — | ✅ |
| **新增拷贝模式引入的外部插件**（`external_plugins/<name>/`） | ✅ 起始值取**上游版本号**，非 `1.0.0` | — | — | ✅ |
```

- [ ] **Step 2: 矩阵下方的判读要点补两条**

在现有五条判读要点之后追加：

```markdown
6. **「新插件起 `1.0.0`」只适用于本仓自建插件**——链接模式的外部条目没有 `plugin.json`，无从起版本号（顶层仍升 Minor，先例 `4d741b8`：12.1.9 → 12.2.0）；拷贝模式的起始值取上游版本号，因为上游版本是读者判断「这份副本是哪一代内容」的唯一线索，归零会把它丢掉
7. **拷贝模式有本地改动时，version 为「上游版本 + `-optimus.N`」**——插件缓存按 version 分目录，改了 `external_plugins/` 里的内容却保持 version 逐字不变，已安装的人拿到的仍是旧缓存、改动装不上。后缀同时兼作「这不是纯上游内容」的显式标记
```

- [ ] **Step 3: 关键文件表登记传感器**

在 `.githooks/check_hook_configs.py` 行之后插入：

```markdown
| `.githooks/check_external_entries.py` | marketplace 外部引用条目机械自检（7 项），`pre-commit` 第 3 项检查 | 两者共用 |
```

并把 `.githooks/pre-commit` 那行的用途描述从「插件版本同值 + hook 配置合规 + skill 镜像完整」改为「插件版本同值 + hook 配置合规 + 外部条目合规 + skill 镜像完整」。

- [ ] **Step 4: 提交与推送一节补一项**

把该节里 pre-commit 拦截项的列举（「每插件两份 `plugin.json` 版本同值、`plugins/*/hooks/hooks.json` 与 Claude Code 契约相符、`.kiro`/`.agents` 符号链接镜像完整且以 `120000` 模式入库」）改为在第二项后插入「marketplace 外部引用条目锁 40 位 `sha`、不写 `version`、已登记台账「已接入」表且台账 sha 与条目一致」。

- [ ] **Step 5: 验证无自相矛盾**

Run: `bash .githooks/pre-commit && grep -n "external_plugins" AGENTS.md`
Expected: 门禁退出 0；`AGENTS.md` 里 `external_plugins` 的出现处彼此一致（矩阵两处 + 判读要点两条），没有一处仍说「不建 `external_plugins/`」。

- [ ] **Step 6: 提交**

### Task 6: 用 skill 自己接入 archify

**这是验收标准第 11 项的落点。禁止手工写 marketplace 条目再补一份 SKILL.md**——那等于这个 skill 从未被验证过。本 Task 的产物有两个：一条条目，以及「skill 跑起来是否真的可用」这个答案。

**Files:**
- Modify: `.claude-plugin/marketplace.json`（新增 archify 条目；顶层 `14.1.0` → `14.2.0`）
- Modify: `.claude/skills/add-external-skill/registry.md`（已接入表加一行）
- Modify: `.claude/skills/add-external-skill/known-issues.md`（仅当首跑暴露缺陷时）

**Interfaces:**
- Consumes: Task 3 的 `/add-external-skill`、Task 1 的传感器、Task 5 的矩阵条款
- Produces: `archify` 条目；命中形态判定表第三行（skill 在子目录、无 `plugin.json`）的首个真实实例

- [ ] **Step 1: 调用 skill**

在新会话中输入：

```
把 https://github.com/tt-a1i/archify 加进本库
```

**用 skill 走完全流程，不要绕过任何 Step。** 期望它：探测出 `archify/SKILL.md`、全仓无 `plugin.json` → 判定第三行 → `url` + `strict:false` + `skills:["./archify"]`；在 CHECKPOINT 展示 License、sha 与该 skill 带进来的东西（该仓 `archify/` 下有 `bin/`、`scripts/`、`package.json`，属「会带进来什么」必须点明的内容）。

- [ ] **Step 2: 独立复核 sha**

Run: `git ls-remote https://github.com/tt-a1i/archify.git main`
Expected: 输出的 40 位 sha 与 skill 写进条目的值**逐字一致**。不一致就是 skill 的取值步骤有缺陷，记 `known-issues.md`。

- [ ] **Step 3: 复核条目形态**

写入后的条目应形如（`sha` 取 Step 2 实测值，`description` 由 skill 生成、须注明外部引入与 License）：

```jsonc
    {
      "name": "archify",
      "description": "…（注明：外部引入 tt-a1i/archify，<实测 License>）",
      "source": {
        "source": "url",
        "url": "https://github.com/tt-a1i/archify.git",
        "ref": "main",
        "sha": "<Step 2 实测的 40 位>"
      },
      "strict": false,
      "skills": ["./archify"],
      "author": { "name": "tt-a1i" },
      "homepage": "https://github.com/tt-a1i/archify",
      "category": "development"
    }
```

⚠️ **`skills` 必须是 `["./archify"]` 而不是 `["./"]`**：`url` 源的插件根是仓库根，而 `SKILL.md` 在 `archify/` 子目录下。写 `["./"]` 会指向没有 `SKILL.md` 的仓库根。

⚠️ **License 据实填写**，`tt-a1i/archify` 根目录与 `archify/` 下各有一个 `LICENSE`，另有 `THIRD_PARTY_NOTICES.md`——实测取值，不要照抄本计划里的占位描述，也不要假定是 MIT。

- [ ] **Step 4: 升顶层 version**

`.claude-plugin/marketplace.json` 顶层 `version`：`14.1.0` → `14.2.0`（Minor，新增一条插件条目，依据 Task 5 补入的矩阵行与先例 `4d741b8`）。

- [ ] **Step 5: 跑传感器与门禁**

Run: `python .githooks/check_external_entries.py . && bash .githooks/pre-commit`
Expected: 两者均退出 0。若报 `archify 未登记在 …/registry.md 的「已接入」表`，说明 skill 的 Step 7 收尾没写台账——这是真实缺陷，记 `known-issues.md`。若报台账 sha 与条目 sha 不一致，同样是真实缺陷（收尾把两处写成了不同的值），一并记录。

⚠️ **新增的台账行必须落在 `<!-- registry:active -->` 锚点之后**，并带 `状态` 列（值 `正常`）。写在锚点之前会被判为「未登记」。

- [ ] **Step 6: 安装验证**

Run:
```bash
claude plugin marketplace update optimus-plugins-official
claude plugin install archify@optimus-plugins-official
```
Expected: 安装成功且 archify 的 skill 可被列出。失败则按 skill 的「写入后验证不通过 → 回滚本次写入」处置，不要留下半成品条目。

- [ ] **Step 7: 记录首跑发现**

把 Step 1–6 中 skill 表现不符预期的每一处写进 `known-issues.md`（日期 + 问题描述 + 触发 prompt + 状态「待处理」）。**没有发现也要在提交信息里说明「首跑无缺陷」**——空手通过和没检查是两回事。

- [ ] **Step 8: 提交**

调用 `/commit-cc-plugin`。本次含 `marketplace.json`（新条目 + 顶层 Minor）、`registry.md`（新增一行）、必要时 `known-issues.md`。提交要表达：用 `add-external-skill` 自身完成的首个接入，命中形态判定表第三行，sha 已独立复核。

---

### Task 7: 用 skill 接入 ppt-master 并收尾

**Files:**
- Modify: `.claude-plugin/marketplace.json`（新增 ppt-master 条目；顶层 `14.2.0` → `14.3.0`）
- Modify: `.claude/skills/add-external-skill/registry.md`
- Modify: `docs/todo-list/2026-09-08-todo.md`
- Modify: `.claude/skills/add-external-skill/known-issues.md`（按需）

**Interfaces:**
- Consumes: 同 Task 6
- Produces: `ppt-master` 条目；命中形态判定表第一行（有 `plugin.json`）与第四行（根目录是 marketplace 而非 plugin）的首个真实实例

- [ ] **Step 1: 先确认 `skills/.claude-plugin/` 里是什么**

spec § 8 把这一项列为「实施时必须先确认、不得假定」。

Run:
```bash
curl -s https://api.github.com/repos/hugohe3/ppt-master/contents/skills/.claude-plugin \
  | python -c "import json,sys; print([e['name'] for e in json.load(sys.stdin)])"
```

- 输出含 `plugin.json` → 走形态判定表**第一行**：`git-subdir` + `path: "skills"`，**不写** `strict` 与 `skills`
- 输出**不含** `plugin.json` → 退回**第三行**：`git-subdir` + `path: "skills"` + `strict: false` + `skills: ["./ppt-master"]`

- [ ] **Step 2: 调用 skill**

在新会话中输入：

```
把 https://github.com/hugohe3/ppt-master 加进本库
```

期望它识别出**根目录的 `.claude-plugin/` 里是 `marketplace.json` 而不是 `plugin.json`**（即该仓本身是一个 marketplace），因此不把根目录当 plugin 引用，而是读它的条目、照抄其 source 形态（`git-subdir` + `path: "skills"`）。**若 skill 把根目录当 plugin 引了，这是形态判定表第四行失效，必须记 known-issues.md 并修正。**

- [ ] **Step 3: CHECKPOINT 必须点明依赖安装**

上游 marketplace 条目的 setup 说明要求安装插件目录内的 `requirements.txt` 才能跑后处理脚本。这属于「该 skill 会带进来什么」必须展示的内容。若 skill 的 CHECKPOINT 没提到它，记 `known-issues.md`。

- [ ] **Step 4: 独立复核 sha 并升顶层 version**

Run: `git ls-remote https://github.com/hugohe3/ppt-master.git main`
条目 `sha` 须与输出逐字一致。顶层 `version`：`14.2.0` → `14.3.0`。

- [ ] **Step 5: 跑传感器、门禁与安装验证**

Run:
```bash
python .githooks/check_external_entries.py . && bash .githooks/pre-commit
claude plugin marketplace update optimus-plugins-official
claude plugin install ppt-master@optimus-plugins-official
```
Expected: 前两者退出 0；安装成功且 ppt-master 的 skill 可被列出。

- [ ] **Step 6: 勾掉 todo 条目**

在 `docs/todo-list/2026-09-08-todo.md` 的「## 将外部skill加入本库」一节标注完成，并写明首批实际接入 2 个（archify、ppt-master），graphify 与 darwin-skill 已排除、原因与复议条件见 `registry.md`。**不要删除该节**——它是这项工作的来源记录。

- [ ] **Step 7: 全量回归**

Run:
```bash
python -m unittest discover -s .githooks -p "test_*.py"
bash .githooks/pre-commit
python .githooks/check_external_entries.py .
python .githooks/check_plugin_versions.py .
```
Expected: 四条全过。

- [ ] **Step 8: 逐条核对验收标准**

打开 spec § 9 的 **15** 条验收标准逐条确认，尤其：

- 第 9 项（台账三类行齐备：3 条已接入含 `状态` 列 + 2 条已排除 + 更新历史表头）
- 第 11 项（至少一个接入是 skill 自己跑出来的，提交历史能体现 skill 先落地、条目后落地）
- 第 12 项（`disable-model-invocation: true` 已带，且正文写明该字段解决什么问题与三点连带影响）
- 第 13 项（Codex 侧对该字段的实际行为**已实测**并记入 `known-issues.md`，不是「待实测」）
- 第 14 项（SKILL.md 的更新一节完整落 U0–U8、§ 4.4.1–4.4.3、失败四格与四类分类，写入后失败明确要求回滚 sha）
- 第 15 项（`test-prompts.json` 的 id 7–10 齐备）

**第 13、14 项是本次最容易被跳过的两条**：一个需要切到另一个 harness 实测，一个需要逐条比对长文。都不要用「应该没问题」代替核对。

- [ ] **Step 9: 提交**

调用 `/commit-cc-plugin`。本次含 `marketplace.json`（新条目 + 顶层 Minor）、`registry.md`、`docs/todo-list/2026-09-08-todo.md`、按需的 `known-issues.md`。提交要表达：第二个接入，命中形态判定表第一与第四行；首批收尾，graphify 与 darwin-skill 的排除决策已入台账。

---
