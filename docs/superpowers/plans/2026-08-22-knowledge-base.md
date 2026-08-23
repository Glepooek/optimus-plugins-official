# 知识库（knowledge-base）建设 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `docs/csharp_doc`、`docs/wpf_doc` 迁移为统一的、可被 skill 编程式查询的知识库 `knowledge-base/`，建立 JSONL 索引与一致性校验、`knowledge-base-maintain` 维护 skill、knowledge-base 自身版本管理，并消除 `csharp-code-review` skill 中与规范文档重复的内嵌知识。

**Architecture:** 每个领域目录（`knowledge-base/csharp/`、`knowledge-base/wpf/`）下保留原有 01-17 规范文件（MUST/SHOULD/MAY 语气不变）与新增的 `reference/` 描述性知识目录，一份 `index.jsonl`（JSON Lines，一行一条记录）做统一编目，不复制正文只做定位；`check_index.py` 做一致性自检（文件存在、锚点存在、id 不重复）；`.claude/skills/knowledge-base-maintain/` 引导新增/修改/校验流程并同步 CHANGELOG/版本号。

**Tech Stack:** Markdown（内容）、JSON Lines（索引）、Python 3 + `unittest`（校验脚本，仓库无 `pytest`）、Claude Code Skill（`.claude/skills/`）。

**Spec:** `docs/superpowers/specs/2026-08-22-knowledge-base-design.md`（Section 1-6 + 待实施清单）

> 状态：全部 Task 已执行完毕，现为历史决策记录——文档中的具体路径（如 `check_index.py`）、领域列表、skill 名称可能已随后续迭代变化，当前状态以 `knowledge-base/README.md` + `CHANGELOG.md` 为准，不要直接照抄本文档中的命令/路径

## Global Constraints

- 迁移必须用 `git mv`，不得删除重建（保留文件历史）。
- 索引文件格式固定为 JSON Lines（每行一条完整 JSON 记录），不用美化格式的 JSON 数组——供 Grep 按行检索。
- 索引字段固定：`id`、`kind`（`rule`|`reference`）、`level`（仅 rule，`MUST`|`SHOULD`|`MAY`）、`file`、`anchor`、`title`、`tags`、`summary`。
- `check_index.py` 自身的单元测试用标准库 `unittest` 编写，不引入 `pytest`（本机无 `pytest`，仓库既有校验脚本均为 `unittest` 风格）；运行方式 `python -m unittest test_check_index -v`（在 `knowledge-base/` 目录下执行）。
- `check_index.py` 作为一线校验工具（对 `index.jsonl` 做一致性检查）时，作为 CLI 脚本直接运行：`python check_index.py <domain>`（如 `python check_index.py csharp`），退出码非 0 表示发现问题。
- `.claude/skills/` 下新增的 `knowledge-base-maintain` 必须在 `.kiro/skills/` 建同名符号链接（`ln -s ../../.claude/skills/knowledge-base-maintain .kiro/skills/knowledge-base-maintain`，或 Windows 下 `New-Item -ItemType SymbolicLink`）。
- `knowledge-base/` 目录变更不触发 `.claude-plugin/marketplace.json` 版本升级；`csharp-code-review` skill 的改造按 `.claude/rules/skill-authoring.md` 规则计 Patch，升级其自身 `metadata.version` 与随之同步的仓库 `marketplace.json`。
- 所有新建/迁移的 Markdown 文件保持 UTF-8 编码、LF 换行（跟随仓库现有文件约定）；提交前检查 `git diff` 不含无关格式化改动（`.claude/rules/skill-authoring.md` 编辑铁律）。
- 本次初始 `index.jsonl` 只覆盖示范性条目（首批 5-10 条／领域），不要求覆盖全部 17 篇的所有章节——后续通过 `knowledge-base-maintain` 逐步回填，Task 中会明确标注"首批"范围。
- `reference/` 目录本次不强制创建空目录（git 不追踪空目录，创建了也不会被提交）；等第一篇 reference 内容真正产生时再建，`knowledge-base/<domain>/README.md` 中说明这一点即可。
- 索引条目的 `anchor` 字段存实际标题文本（去掉反引号/前导 `#`，如 `"2.4 var 与对象创建"`），不是 GitHub 锚点 slug——`check_index.py` 按"标准化后的标题文本包含 anchor 字符串"做子串匹配，不依赖 slug 算法。

---

## Task 1: 迁移 `docs/csharp_doc`、`docs/wpf_doc` 到 `knowledge-base/`

**Files:**
- Modify（rename）: `docs/csharp_doc/*` → `knowledge-base/csharp/*`（`git mv` 整目录）
- Modify（rename）: `docs/wpf_doc/*` → `knowledge-base/wpf/*`（`git mv` 整目录）
- Modify: `knowledge-base/csharp/17-comments-docs.md`（修正内部自引用路径）

**Interfaces:**
- Produces: `knowledge-base/csharp/` 目录（含原 `01-17*.md` + `README.md` + `refit.md`），`knowledge-base/wpf/` 目录（含原 `01-17*.md` + `README.md`）——后续所有 Task 都基于这两个路径操作。

- [ ] **Step 1: 执行迁移**

在仓库根目录运行：

```bash
git mv docs/csharp_doc knowledge-base/csharp
git mv docs/wpf_doc knowledge-base/wpf
```

- [ ] **Step 2: 验证迁移是纯重命名**

```bash
git status
```

Expected: 输出显示 `renamed: docs/csharp_doc/xxx.md -> knowledge-base/csharp/xxx.md`（及 wpf 同理）逐文件列出，不应出现 `deleted` + `new file` 的组合（那意味着 git 没识别为 rename，需检查是否用了 `git mv` 而非手动移动）。

- [ ] **Step 3: 修正内部自引用路径**

`knowledge-base/csharp/17-comments-docs.md` 第 68 行（迁移后行号不变，内容不变）当前是：

```markdown
- **应该**：规范类文档遵循团队规范（如本套 `docs/csharp_doc/` 的更新机制）
```

用 Edit 工具把 `docs/csharp_doc/` 改为 `knowledge-base/csharp/`：

```markdown
- **应该**：规范类文档遵循团队规范（如本套 `knowledge-base/csharp/` 的更新机制）
```

- [ ] **Step 4: 验证无残留自引用**

```bash
grep -rn "docs/csharp_doc\|docs/wpf_doc" knowledge-base/
```

Expected: 无输出（`knowledge-base/` 内部不再有指向旧路径的引用）。

- [ ] **Step 5: Commit**

```bash
git add docs/csharp_doc docs/wpf_doc knowledge-base/csharp knowledge-base/wpf
git commit -m "$(cat <<'EOF'
docs(knowledge-base): 迁移 csharp/wpf 规范文档集至 knowledge-base/

- git mv docs/csharp_doc -> knowledge-base/csharp，docs/wpf_doc -> knowledge-base/wpf
- 修正 17-comments-docs.md 内部自引用路径

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

（提交消息中的 Co-Authored-By 模型名按 `commit-cc-plugin` skill 要求填写当前实际使用模型，不得照抄示例。）

---

## Task 2: `check_index.py` 核心校验函数（含单元测试）

**Files:**
- Create: `knowledge-base/check_index.py`
- Test: `knowledge-base/test_check_index.py`

**Interfaces:**
- Produces:
  - `normalize_heading(line: str) -> str` —— 去掉行首 `#` 与空格、去掉反引号，折叠多余空格，返回纯文本标题
  - `find_headings(text: str) -> list[str]` —— 返回文件全文中所有 Markdown 标题行的 `normalize_heading` 结果列表
- Consumes: 无（本 Task 是最底层纯函数，不依赖其他 Task 产出）

- [ ] **Step 1: 写失败测试（`normalize_heading` / `find_headings`）**

创建 `knowledge-base/test_check_index.py`：

```python
import unittest
from check_index import normalize_heading, find_headings


class TestNormalizeHeading(unittest.TestCase):
    def test_strips_hash_and_spaces(self):
        self.assertEqual(normalize_heading("## 1. 命名规范"), "1. 命名规范")

    def test_strips_backticks(self):
        self.assertEqual(normalize_heading("### 2.4 `var` 与对象创建"), "2.4 var 与对象创建")

    def test_collapses_extra_spaces(self):
        self.assertEqual(normalize_heading("#   1.  命名规范  "), "1.  命名规范")


class TestFindHeadings(unittest.TestCase):
    def test_finds_all_heading_levels(self):
        text = "# 标题\n正文\n## 二级\n### 三级\n非标题行 # 不是标题"
        self.assertEqual(find_headings(text), ["标题", "二级", "三级"])

    def test_empty_text_returns_empty_list(self):
        self.assertEqual(find_headings(""), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd knowledge-base && python -m unittest test_check_index -v
```

Expected: `ModuleNotFoundError: No module named 'check_index'`（`check_index.py` 尚不存在）。

- [ ] **Step 3: 实现 `normalize_heading` 与 `find_headings`**

创建 `knowledge-base/check_index.py`：

```python
#!/usr/bin/env python3
"""校验 knowledge-base/<domain>/index.jsonl 与实际文件的一致性。

三类检查：file 是否存在、anchor 对应标题是否存在、id 是否全局唯一。
"""
import json
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')


def normalize_heading(line):
    m = HEADING_RE.match(line.strip())
    text = m.group(2) if m else line.strip()
    text = text.replace("`", "")
    return re.sub(r'\s+', ' ', text).strip()


def find_headings(text):
    headings = []
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            headings.append(normalize_heading(line))
    return headings
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd knowledge-base && python -m unittest test_check_index -v
```

Expected: `TestNormalizeHeading` 与 `TestFindHeadings` 全部 `ok`（5 个测试通过）。

- [ ] **Step 5: Commit**

```bash
git add knowledge-base/check_index.py knowledge-base/test_check_index.py
git commit -m "$(cat <<'EOF'
feat(knowledge-base): check_index.py 标题解析函数 + 单元测试

- normalize_heading/find_headings：解析 Markdown 标题供后续 anchor 校验复用

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `check_index.py` 内容校验函数 + CLI 入口

**Files:**
- Modify: `knowledge-base/check_index.py`
- Modify: `knowledge-base/test_check_index.py`

**Interfaces:**
- Consumes: `normalize_heading(line: str) -> str`、`find_headings(text: str) -> list[str]`（Task 2 产出，已在 `check_index.py` 中）
- Produces:
  - `parse_index_file(path: Path) -> list[dict]` —— 逐行解析 JSONL；空行跳过；非法 JSON 行抛 `ValueError(f"{path}:{行号}: JSON 解析失败：{原始异常}")`
  - `check_file_exists(domain_dir: Path, entry: dict) -> str | None` —— 返回问题描述或 `None`
  - `check_anchor_exists(domain_dir: Path, entry: dict) -> str | None` —— 返回问题描述或 `None`
  - `check_duplicate_ids(domain_entries: dict[str, list[dict]]) -> list[str]` —— 入参为 `{domain名: entry列表}`，返回重复 id 的问题描述列表
  - `run_checks(base_dir: Path, domains: list[str]) -> list[str]` —— 汇总以上三类检查，返回全部问题描述（空列表 = 全部通过）
  - CLI：`python check_index.py <domain> [<domain2> ...]`，无参数时默认扫描 `base_dir` 下所有含 `index.jsonl` 的子目录；发现问题打印到 stderr 并 `sys.exit(1)`，无问题打印 `"OK: 共检查 N 条记录，未发现问题"` 并 `sys.exit(0)`

- [ ] **Step 1: 写失败测试**

在 `knowledge-base/test_check_index.py` 追加（`import` 行替换为包含新函数，其余保留 Task 2 已有内容）：

```python
import json
import tempfile
import unittest
from pathlib import Path

from check_index import (
    check_anchor_exists,
    check_duplicate_ids,
    check_file_exists,
    find_headings,
    normalize_heading,
    parse_index_file,
    run_checks,
)


class TestParseIndexFile(unittest.TestCase):
    def test_parses_valid_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "index.jsonl"
            p.write_text(
                '{"id": "a.1", "kind": "rule"}\n{"id": "a.2", "kind": "reference"}\n',
                encoding="utf-8",
            )
            entries = parse_index_file(p)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["id"], "a.1")

    def test_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "index.jsonl"
            p.write_text('{"id": "a.1"}\n\n{"id": "a.2"}\n', encoding="utf-8")
            entries = parse_index_file(p)
            self.assertEqual(len(entries), 2)

    def test_raises_with_line_number_on_bad_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "index.jsonl"
            p.write_text('{"id": "a.1"}\n{not valid json}\n', encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_index_file(p)
            self.assertIn(":2:", str(ctx.exception))


class TestCheckFileExists(unittest.TestCase):
    def test_none_when_file_present(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "01-x.md").write_text("# 标题\n", encoding="utf-8")
            entry = {"id": "a.1", "file": "01-x.md"}
            self.assertIsNone(check_file_exists(domain_dir, entry))

    def test_message_when_file_missing(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            entry = {"id": "a.1", "file": "missing.md"}
            result = check_file_exists(domain_dir, entry)
            self.assertIsNotNone(result)
            self.assertIn("a.1", result)
            self.assertIn("missing.md", result)


class TestCheckAnchorExists(unittest.TestCase):
    def test_none_when_anchor_empty(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "01-x.md").write_text("# 标题\n", encoding="utf-8")
            entry = {"id": "a.1", "file": "01-x.md", "anchor": ""}
            self.assertIsNone(check_anchor_exists(domain_dir, entry))

    def test_none_when_anchor_matches_heading(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "01-x.md").write_text("# 标题\n## 1. 命名规范\n", encoding="utf-8")
            entry = {"id": "a.1", "file": "01-x.md", "anchor": "命名规范"}
            self.assertIsNone(check_anchor_exists(domain_dir, entry))

    def test_message_when_anchor_not_found(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "01-x.md").write_text("# 标题\n## 别的章节\n", encoding="utf-8")
            entry = {"id": "a.1", "file": "01-x.md", "anchor": "不存在的锚点"}
            result = check_anchor_exists(domain_dir, entry)
            self.assertIsNotNone(result)
            self.assertIn("a.1", result)


class TestCheckDuplicateIds(unittest.TestCase):
    def test_empty_when_all_unique(self):
        domain_entries = {"csharp": [{"id": "a.1"}, {"id": "a.2"}]}
        self.assertEqual(check_duplicate_ids(domain_entries), [])

    def test_detects_duplicate_within_domain(self):
        domain_entries = {"csharp": [{"id": "a.1"}, {"id": "a.1"}]}
        result = check_duplicate_ids(domain_entries)
        self.assertEqual(len(result), 1)
        self.assertIn("a.1", result[0])

    def test_detects_duplicate_across_domains(self):
        domain_entries = {"csharp": [{"id": "x.1"}], "wpf": [{"id": "x.1"}]}
        result = check_duplicate_ids(domain_entries)
        self.assertEqual(len(result), 1)


class TestRunChecks(unittest.TestCase):
    def test_no_problems_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            domain_dir = base / "csharp"
            domain_dir.mkdir()
            (domain_dir / "01-x.md").write_text("## 命名规范\n", encoding="utf-8")
            (domain_dir / "index.jsonl").write_text(
                json.dumps({"id": "csharp.1", "kind": "rule", "level": "MUST",
                            "file": "01-x.md", "anchor": "命名规范",
                            "title": "t", "tags": [], "summary": "s"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(run_checks(base, ["csharp"]), [])

    def test_collects_problems_from_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            domain_dir = base / "csharp"
            domain_dir.mkdir()
            (domain_dir / "index.jsonl").write_text(
                json.dumps({"id": "csharp.1", "kind": "rule", "file": "missing.md",
                            "anchor": "", "title": "t", "tags": [], "summary": "s"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            problems = run_checks(base, ["csharp"])
            self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd knowledge-base && python -m unittest test_check_index -v
```

Expected: `ImportError: cannot import name 'parse_index_file' from 'check_index'`（新函数尚未实现）。

- [ ] **Step 3: 实现内容校验函数与 CLI**

把 `knowledge-base/check_index.py` 替换为完整版本：

```python
#!/usr/bin/env python3
"""校验 knowledge-base/<domain>/index.jsonl 与实际文件的一致性。

三类检查：file 是否存在、anchor 对应标题是否存在、id 是否全局唯一。
用法：python check_index.py [domain ...]（无参数时扫描所有含 index.jsonl 的子目录）
"""
import json
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')


def normalize_heading(line):
    m = HEADING_RE.match(line.strip())
    text = m.group(2) if m else line.strip()
    text = text.replace("`", "")
    return re.sub(r'\s+', ' ', text).strip()


def find_headings(text):
    headings = []
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            headings.append(normalize_heading(line))
    return headings


def parse_index_file(path):
    entries = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{line_no}: JSON 解析失败：{e}")
    return entries


def check_file_exists(domain_dir, entry):
    target = domain_dir / entry["file"]
    if not target.exists():
        return f"[{entry['id']}] file 不存在：{entry['file']}"
    return None


def check_anchor_exists(domain_dir, entry):
    anchor = entry.get("anchor", "")
    if not anchor:
        return None
    target = domain_dir / entry["file"]
    if not target.exists():
        return None  # file 缺失已由 check_file_exists 报告，避免重复问题
    headings = find_headings(target.read_text(encoding="utf-8"))
    if not any(anchor in h for h in headings):
        return f"[{entry['id']}] anchor 未在 {entry['file']} 中找到匹配标题：{anchor}"
    return None


def check_duplicate_ids(domain_entries):
    seen = {}
    problems = []
    for domain, entries in domain_entries.items():
        for entry in entries:
            entry_id = entry["id"]
            if entry_id in seen:
                problems.append(f"重复 id：{entry_id}（{seen[entry_id]} 与 {domain}）")
            else:
                seen[entry_id] = domain
    return problems


def run_checks(base_dir, domains):
    domain_entries = {}
    problems = []
    for domain in domains:
        domain_dir = base_dir / domain
        index_path = domain_dir / "index.jsonl"
        if not index_path.exists():
            problems.append(f"[{domain}] index.jsonl 不存在：{index_path}")
            continue
        entries = parse_index_file(index_path)
        domain_entries[domain] = entries
        for entry in entries:
            for check in (check_file_exists, check_anchor_exists):
                result = check(domain_dir, entry)
                if result:
                    problems.append(f"[{domain}] {result}")
    problems.extend(check_duplicate_ids(domain_entries))
    return problems


def main():
    base_dir = Path(__file__).resolve().parent
    domains = sys.argv[1:]
    if not domains:
        domains = sorted(
            p.name for p in base_dir.iterdir()
            if p.is_dir() and (p / "index.jsonl").exists()
        )
    problems = run_checks(base_dir, domains)
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        sys.exit(1)
    total = sum(
        len(parse_index_file(base_dir / d / "index.jsonl"))
        for d in domains if (base_dir / d / "index.jsonl").exists()
    )
    print(f"OK: 共检查 {total} 条记录，未发现问题")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd knowledge-base && python -m unittest test_check_index -v
```

Expected: 全部测试 `ok`（Task 2 的 5 个 + 本 Task 新增的测试全部通过）。

- [ ] **Step 5: Commit**

```bash
git add knowledge-base/check_index.py knowledge-base/test_check_index.py
git commit -m "$(cat <<'EOF'
feat(knowledge-base): check_index.py 完整三类校验 + CLI 入口

- parse_index_file/check_file_exists/check_anchor_exists/check_duplicate_ids/run_checks
- CLI: python check_index.py [domain ...]，发现问题退出码 1

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `knowledge-base/README.md` + `CHANGELOG.md` + 两领域首批 `index.jsonl`

**Files:**
- Create: `knowledge-base/README.md`
- Create: `knowledge-base/CHANGELOG.md`
- Create: `knowledge-base/csharp/index.jsonl`
- Create: `knowledge-base/wpf/index.jsonl`
- Modify: `knowledge-base/csharp/README.md`
- Modify: `knowledge-base/wpf/README.md`

**Interfaces:**
- Consumes: Task 1 迁移后的 `knowledge-base/csharp/`、`knowledge-base/wpf/` 目录结构
- Produces: 两份首批 `index.jsonl`（各 6 条，覆盖后续 Task 5、Task 6 需要引用的条目），供 Task 5、Task 6 直接使用其中的 `id`

- [ ] **Step 1: 创建 `knowledge-base/README.md`**

```markdown
# 知识库（knowledge-base）

> 版本：1.0.0

跨插件共享的规范知识库，供人类阅读也供 skill 编程式查询。当前收纳领域：`csharp`、`wpf`。

## 目录结构

每个领域目录遵循统一模式：

```
<domain>/
├── README.md          # 领域说明、阅读路径
├── 01-*.md ... 17-*.md  # 规范条款（MUST/SHOULD/MAY 语气）
├── index.jsonl         # 索引：rule + reference 统一编目
└── reference/          # 描述性知识（无规范语气），首篇内容产生时才建
```

## 消费方式

skill 需要引用某条规范/知识时，先用 Grep 在对应领域的 `index.jsonl` 中按 `tags`/`title`/`summary` 检索，定位到 `id` 后按 `file` + `anchor` 打开原文件读取具体条款——索引不复制正文，原始 Markdown 文件始终是唯一真相源。

索引记录字段：

| 字段 | 说明 |
|---|---|
| `id` | `<domain>.<文件编号或ref>.<slug>`，全局唯一，人工手写 |
| `kind` | `"rule"` \| `"reference"` |
| `level` | 仅 `rule` 有，`MUST`/`SHOULD`/`MAY` |
| `file` | 相对领域目录的文件路径 |
| `anchor` | 文件内标题文本（非 slug），无锚点留空字符串 |
| `title` | 条目标题 |
| `tags` | 自由关键词数组 |
| `summary` | 一句话摘要 |

## 维护约定

- 新增/修改一条规范/reference 时，同一次提交里必须同步更新对应 `index.jsonl`。
- 改动后运行 `python check_index.py <domain>` 做一致性自检（file 存在、anchor 存在、id 不重复）。
- 规范条款可选择性引用 `reference/*.md` 加强依据；引用单向，reference 不反向声明被谁引用。
- 版本号见本文件顶部，变更规则与 CHANGELOG 格式见 `CHANGELOG.md`；日常新增/修改建议通过 `/knowledge-base-maintain` skill 完成，会自动同步索引与版本号。
- 不做自动生成索引的脚本——`tags`/`summary`/`level` 需要语义判断，机械提取质量不可靠。

## 与仓库已有资产的关系

- `plugins/optimus-backend-plugin/skills/csharp-code-review`：审查规则以 `knowledge-base/csharp/` 为准，见该 skill 的"权威参考"章节。
- `plugins/optimus-frontend-plugin/skills/wpf-xaml-performance`、`wpf-project-conventions`：性能与项目结构判断依据见 `knowledge-base/wpf/`。
```

- [ ] **Step 2: 创建 `knowledge-base/CHANGELOG.md`**

```markdown
# Changelog

## [1.0.0] - 2026-08-22

### Added
- 迁移 `docs/csharp_doc` → `knowledge-base/csharp`，`docs/wpf_doc` → `knowledge-base/wpf`
- 建立 JSON Lines 索引机制（`index.jsonl`）与一致性校验脚本 `check_index.py`
- csharp、wpf 两领域首批索引条目（各 6 条）
```

- [ ] **Step 3: 创建 `knowledge-base/csharp/index.jsonl`（首批 6 条）**

```jsonl
{"id": "csharp.02.naming-core", "kind": "rule", "level": "MUST", "file": "02-coding-style.md", "anchor": "1.1 核心规则表", "title": "命名规则表（接口/类/字段/参数）", "tags": ["naming", "style"], "summary": "接口 IPascalCase、私有字段 _camelCase、静态字段 s_camelCase 等核心命名规则表。"}
{"id": "csharp.02.var-usage", "kind": "rule", "level": "SHOULD", "file": "02-coding-style.md", "anchor": "2.4 var 与对象创建", "title": "var 与目标类型 new() 使用边界", "tags": ["var", "style"], "summary": "右侧类型立即可见时用 var，返回 object/基类/匿名类型不可推断时用显式类型。"}
{"id": "csharp.02.null-check-pattern", "kind": "rule", "level": "MUST", "file": "02-coding-style.md", "anchor": "2.2 类型与运算符", "title": "判空优先用 is null 模式匹配", "tags": ["null-check", "style"], "summary": "判空优先用模式匹配 is null / is not null，不用 == null（可读性更好，分析器友好）。"}
{"id": "csharp.04.cancellation-token", "kind": "rule", "level": "MUST", "file": "04-async-programming.md", "anchor": "6. CancellationToken 传播", "title": "I/O 异步方法必须接受并传播 CancellationToken", "tags": ["async", "cancellation"], "summary": "所有 I/O 绑定异步方法接受 CancellationToken cancellationToken = default 并向下传递，禁止签名有参数却不检查不传递。"}
{"id": "csharp.05.no-silent-catch", "kind": "rule", "level": "MUST", "file": "05-error-handling.md", "anchor": "4. 捕获边界与过滤", "title": "禁止静默吞异常", "tags": ["exception", "logging"], "summary": "catch 块内必须有实质处理（记录日志、包装向上抛、重试），只打印不处理视同吞异常。"}
{"id": "csharp.05.consistent-failure-semantics", "kind": "rule", "level": "MUST", "file": "05-error-handling.md", "anchor": "1. 失败表达：抛异常 vs 返回结果", "title": "同一方法内失败表达方式必须统一", "tags": ["exception", "api-design"], "summary": "一个方法内失败的表达方式统一——要么统一抛异常，要么统一返回 Result/默认值，不得混用。"}
```

- [ ] **Step 4: 创建 `knowledge-base/wpf/index.jsonl`（首批 6 条）**

```jsonl
{"id": "wpf.03.mvvm-single-framework", "kind": "rule", "level": "MUST", "file": "03-mvvm.md", "anchor": "1. MVVM 框架选型", "title": "全仓库统一一种 MVVM 框架", "tags": ["mvvm", "architecture"], "summary": "全仓库统一一种 MVVM 框架（Prism / CommunityToolkit.Mvvm / 原生），禁止混用导致基类与命令混乱。"}
{"id": "wpf.03.no-servicelocator", "kind": "rule", "level": "MUST", "file": "03-mvvm.md", "anchor": "5. 依赖注入与组合根", "title": "禁止 ServiceLocator 反模式", "tags": ["di", "mvvm"], "summary": "ViewModel 依赖通过构造函数注入接口，禁止 ServiceLocator 到处 container.Resolve<T>() 反模式。"}
{"id": "wpf.04.static-vs-dynamic-resource", "kind": "rule", "level": "MUST", "file": "04-xaml.md", "anchor": "2. 资源引用：StaticResource vs DynamicResource", "title": "默认用 StaticResource，仅主题切换场景用 DynamicResource", "tags": ["xaml", "resource"], "summary": "默认用 StaticResource（编译期解析、找不到报错），仅需响应资源运行时变化（主题切换）才用 DynamicResource。"}
{"id": "wpf.09.ui-thread-affinity", "kind": "rule", "level": "MUST", "file": "09-threading.md", "anchor": "1. UI 线程访问铁律", "title": "UI 元素只能由创建它的 UI 线程操作", "tags": ["threading", "dispatcher"], "summary": "所有 DependencyObject 只能由创建它的 UI 线程操作，后台线程更新 UI 必须经 Dispatcher 编组。"}
{"id": "wpf.09.no-sync-wait-deadlock", "kind": "rule", "level": "MUST", "file": "09-threading.md", "anchor": "5. 死锁防护", "title": "UI 线程禁止同步等待异步任务", "tags": ["threading", "deadlock", "async"], "summary": "UI 线程不 Wait()/.Result 等待异步任务，阻塞 UI 线程会导致后台任务无法回到 UI 线程造成死锁。"}
{"id": "wpf.10.virtualization", "kind": "rule", "level": "MUST", "file": "10-performance.md", "anchor": "4. 虚拟化", "title": "长列表必须开启虚拟化", "tags": ["performance", "virtualization"], "summary": "长列表（ListBox/ListView/DataGrid/TreeView）开启虚拟化，并设 VirtualizationMode=Recycling。"}
```

- [ ] **Step 5: 在两个领域 README.md 补充索引/reference 约定说明**

在 `knowledge-base/csharp/README.md` 与 `knowledge-base/wpf/README.md` 的"## 文件地图"表格之后，各追加一个新章节：

```markdown
## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。`reference/` 目录存放不带 MUST/SHOULD/MAY 语气的描述性知识（语法讲解、API 用法），与本篇编号规范文件是并列关系，不是从属关系——新增/修改任一类内容都需同步 `index.jsonl`，建议通过 `/knowledge-base-maintain` skill 完成。
```

- [ ] **Step 6: 运行一致性校验**

```bash
cd knowledge-base && python check_index.py csharp wpf
```

Expected: `OK: 共检查 12 条记录，未发现问题`。若报错，按输出的 `[domain] [id] 问题描述` 定位具体记录修正（常见问题：`anchor` 文本与实际标题不完全匹配——检查目标文件对应章节标题的准确文本）。

- [ ] **Step 7: Commit**

```bash
git add knowledge-base/README.md knowledge-base/CHANGELOG.md knowledge-base/csharp/index.jsonl knowledge-base/wpf/index.jsonl knowledge-base/csharp/README.md knowledge-base/wpf/README.md
git commit -m "$(cat <<'EOF'
docs(knowledge-base): 新增 README/CHANGELOG 与两领域首批索引

- knowledge-base/README.md：目录结构、消费方式、维护约定，版本号 1.0.0
- knowledge-base/CHANGELOG.md：初始版本记录
- csharp/wpf 各 6 条首批 index.jsonl 示范条目
- 两领域 README.md 补充索引与 reference 消费约定说明

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: 补齐 `knowledge-base/csharp/` 两条缺口规范条目

**Files:**
- Modify: `knowledge-base/csharp/02-coding-style.md`
- Modify: `knowledge-base/csharp/13-api-design.md`
- Modify: `knowledge-base/csharp/index.jsonl`

**Interfaces:**
- Consumes: `knowledge-base/check_index.py` 的 `run_checks`（Task 3 产出，用于本 Task Step 4 校验）
- Produces: 两条新增索引 `id`：`csharp.02.delegate-func-action`、`csharp.13.implicit-dependency-contract`——供 Task 6 引用

排查依据（spec Section 5）：`csharp-code-review` 第 9 类"委托与事件"（优先 `Func<>`/`Action<>`）与第 12 类"隐式依赖契约需要显式说明"，在现有规范文档中确认缺失，需先写入文档再供 skill 引用。

- [ ] **Step 1: 在 `02-coding-style.md` 补充委托选择规则**

在 `knowledge-base/csharp/02-coding-style.md` 中，用 Edit 工具定位到"### 2.5 注释风格"这个标题行，在其**之前**插入新小节（即插入在"is null"示例代码块结束之后、"### 2.5 注释风格"之前）：

```markdown
### 2.6 委托选择

- **应该**：优先使用 `Func<>` / `Action<>` 而非自定义委托类型，减少无谓的类型定义
- **应该**：仅当委托需要具名语义（提升可读性）或涉及 `ref`/`out` 参数（`Func`/`Action` 不支持）时才自定义委托类型

```csharp
// ❌ 自定义委托类型：仅为传递一个简单回调却多定义一个类型
public delegate void OrderProcessedHandler(Order order);
public event OrderProcessedHandler OrderProcessed;

// ✅ Action<> 标准化：无需额外类型定义
public event Action<Order> OrderProcessed;
```

```

（插入后原"### 2.5 注释风格"章节需重新编号为"### 2.6 注释风格"，本节新增内容改为"### 2.5 委托选择"——即插入点在原 2.4 与 2.5 之间，新节号 2.5，原 2.5 顺移为 2.6。后续 Step 3 索引记录的 `anchor` 使用最终编号"2.5 委托选择"。）

- [ ] **Step 2: 在 `13-api-design.md` 补充隐式依赖契约规则**

在 `knowledge-base/csharp/13-api-design.md` 的"## 2. 设计原则"章节末尾（"应该：返回只读/不可变视图..."这一行之后）用 Edit 追加一条：

```markdown
- **应该**：方法依赖调用方预先配置好的外部状态时（如注入的 `HttpClient` 必须已设置 `BaseAddress`），通过构造函数校验或 XML 注释明确该前提

```csharp
// ❌ 隐式依赖调用方配置：BaseAddress 未设置时运行期才报错，且报错信息与"配置遗漏"无关
public class WeatherClient(HttpClient http)
{
    public Task<string> GetAsync() => http.GetStringAsync("current");   // 依赖 http.BaseAddress 已设置
}

// ✅ 构造函数显式校验前提：配置遗漏在启动期就能定位
public class WeatherClient
{
    public WeatherClient(HttpClient http)
    {
        if (http.BaseAddress is null)
            throw new ArgumentException("HttpClient.BaseAddress 必须预先配置", nameof(http));
        _http = http;
    }
    private readonly HttpClient _http;
}
```
```

- [ ] **Step 3: 追加两条新索引记录**

在 `knowledge-base/csharp/index.jsonl` 末尾追加两行：

```jsonl
{"id": "csharp.02.delegate-func-action", "kind": "rule", "level": "SHOULD", "file": "02-coding-style.md", "anchor": "2.5 委托选择", "title": "委托优先 Func/Action", "tags": ["delegate", "func", "action"], "summary": "优先使用 Func<> 和 Action<> 而非自定义委托类型，仅具名语义或 ref/out 参数场景才自定义。"}
{"id": "csharp.13.implicit-dependency-contract", "kind": "rule", "level": "SHOULD", "file": "13-api-design.md", "anchor": "2. 设计原则", "title": "隐式依赖契约需要显式说明", "tags": ["api-design", "dependency-injection"], "summary": "方法依赖调用方预先配置好的外部状态时（如 HttpClient 需已设置 BaseAddress），应通过构造函数校验或 XML 注释明确该前提。"}
```

- [ ] **Step 4: 运行一致性校验**

```bash
cd knowledge-base && python check_index.py csharp wpf
```

Expected: `OK: 共检查 14 条记录，未发现问题`（csharp 8 条 + wpf 6 条）。

- [ ] **Step 5: 更新 `knowledge-base/CHANGELOG.md` 并升级版本号**

这是新增规范条目，按 Global Constraints 的版本升级规则（新增规范条目 = Minor）：`knowledge-base/README.md` 顶部版本号 `1.0.0` → `1.1.0`；`knowledge-base/CHANGELOG.md` 追加：

```markdown
## [1.1.0] - 2026-08-22

### Added
- `02-coding-style.md` 新增 2.5 节：委托选择规则（优先 Func/Action），原 2.5 注释风格顺移为 2.6
- `13-api-design.md` 补充隐式依赖契约需显式说明的规则
- 对应索引记录 `csharp.02.delegate-func-action`、`csharp.13.implicit-dependency-contract`
```

- [ ] **Step 6: Commit**

```bash
git add knowledge-base/csharp/02-coding-style.md knowledge-base/csharp/13-api-design.md knowledge-base/csharp/index.jsonl knowledge-base/README.md knowledge-base/CHANGELOG.md
git commit -m "$(cat <<'EOF'
feat(knowledge-base): 补齐委托选择与隐式依赖契约两条缺口规范

- 02-coding-style.md 新增 2.5 委托选择（优先 Func/Action），原 2.5 注释风格顺移为 2.6
- 13-api-design.md 补充隐式依赖契约显式说明规则
- 登记对应索引记录，knowledge-base 版本 1.0.0 -> 1.1.0（Minor：新增规范条目）

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: 改写 `csharp-code-review/SKILL.md` 为引用形式

**Files:**
- Modify: `plugins/optimus-backend-plugin/skills/csharp-code-review/SKILL.md`
- Modify: `plugins/optimus-backend-plugin/skills/csharp-code-review/CHANGELOG.md`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: `knowledge-base/csharp/index.jsonl` 中的 8 条已登记 id（Task 4、Task 5 产出：`csharp.02.naming-core`、`csharp.02.var-usage`、`csharp.02.null-check-pattern`、`csharp.02.delegate-func-action`、`csharp.04.cancellation-token`、`csharp.05.no-silent-catch`、`csharp.05.consistent-failure-semantics`、`csharp.13.implicit-dependency-contract`）；`knowledge-base/csharp/07-performance.md` 第 3 节（LINQ 边界，非索引条目，直接按文件+锚点引用）

排查依据（spec Section 5）：`csharp-code-review` 现有"审查清单"（原文件第 64-266 行，12 个类别 + 常见违规速查表 + 权威参考）与 `knowledge-base/csharp/` 规范条款存在大面积重复，改为引用形式，删除重复文本；"常见违规速查表"逐行核对后确认与"审查清单"重复（同一批规则换了个表格形式再列一遍），按"逐条删重"原则整体删除，不保留为并行拷贝；"快速审查清单"是一句话操作口诀式的速记（不重述完整规则文本），保留。

- [ ] **Step 1: 读取当前文件确认行号锚点**

先用 Read 工具读取 `plugins/optimus-backend-plugin/skills/csharp-code-review/SKILL.md` 全文，确认"## 审查清单"标题行、"## 常见违规速查表"标题行、"## 快速审查清单"标题行、"## 权威参考"标题行、"## ⛔ 不要做什么（反例黑名单）"标题行的当前行号（迁移改造过程中若前序 Task 未改动此文件，行号应与本计划撰写时读到的一致：分别为 64、234、250、261、268）。

- [ ] **Step 2: 替换"审查清单"章节为引用表**

用 Edit 工具，把从"## 审查清单"标题开始到"## 常见违规速查表"标题**之前**的全部内容（原第 64-233 行），替换为：

```markdown
## 审查清单

系统性地检查以下每个类别，标记 ✅ 已检查或 ⚠️ 发现违规。规则内容以 `knowledge-base/csharp/` 为唯一来源，本表只做定位，不重复规则文本——审查时打开对应文件锚点读取具体条款。

| # | 类别 | knowledge-base 参考 | 核对要点 |
|---|---|---|---|
| 1 | 命名约定 | `02-coding-style.md` § 1. 命名规范 | 接口/类/字段/参数命名规则、命名禁忌、布尔命名 |
| 2 | 类型使用 | `02-coding-style.md` § 2.2 类型与运算符 | C# 关键字而非 BCL 类型名 |
| 3 | 字符串处理 | `02-coding-style.md` § 2.3 字符串处理 | 插值 / StringBuilder / 原始字符串场景选择 |
| 4 | 逻辑运算符与判空 | `02-coding-style.md` § 2.2 类型与运算符 | `&&`/`\|\|` 短路运算符；判空用 `is null` |
| 5 | 代码结构 | `02-coding-style.md` § 2.1 结构与布局 | 命名空间、大括号风格、缩进、空行 |
| 6 | `var` 与对象创建 | `02-coding-style.md` § 2.4 `var` 与对象创建 | 类型可推断时用 `var`，否则显式类型；目标类型 `new()` |
| 7 | 集合与 LINQ | `07-performance.md` § 3. LINQ 边界 | 避免多次枚举、长链中间对象、逐元素高成本调用 |
| 8 | 委托与事件 | `02-coding-style.md` § 2.5 委托选择 | 优先 `Func<>`/`Action<>`，自定义委托仅限具名语义或 `ref`/`out` |
| 9 | 异常处理 | `05-error-handling.md` § 1、§ 4 | 失败表达方式统一；禁止静默吞异常 |
| 10 | 异步模式 | `04-async-programming.md` § 2、§ 6 | 禁止 `.Result`/`.Wait()`；`CancellationToken` 传播 |
| 11 | API 设计与健壮性 | `13-api-design.md` § 2；`05-error-handling.md` 全篇 | 隐式依赖契约显式说明；异常语义统一；取消令牌传播 |
```

（原表中的第 12 类"API 设计与健壮性"与原第 10/11 类内容合并到本表第 9/10/11 行，因为拆开会导致同一 `05-error-handling.md` 依据被两行分别引用——合并后不丢失任何审查维度，仅去掉编号重复引用同一依据的冗余。）

- [ ] **Step 3: 删除"常见违规速查表"整节**

用 Edit 工具，把从"## 常见违规速查表"标题到"## 快速审查清单"标题**之前**的全部内容（Step 2 替换后，原第 234-249 行对应的内容）整节删除（该表逐行重述的是"审查清单"12 类别已覆盖的规则，属于重复内容）。

- [ ] **Step 4: 更新"快速审查清单"为按类别编号引用**

把"## 快速审查清单"下的 6 条操作口诀，替换为：

```markdown
## 快速审查清单

用于时间紧迫时的快速审查（1-2 分钟），按上方审查清单表的类别编号快速过一遍：

1. **命名**（#1）：接口 `I`、私有字段 `_`、静态字段 `s_`、公共 `PascalCase`、参数 `camelCase`
2. **类型与判空**（#2、#4）：`string` 而非 `String`；`is null` 而非 `== null`
3. **运算符**（#4）：`&&`/`\|\|` 而非 `&`/`\|`
4. **字符串**（#3）：简单拼接用插值 `$""`，循环用 `StringBuilder`
5. **结构**（#5）：文件作用域 namespace、`using` 在外部、Allman 大括号
6. **健壮性**（#9、#11）：异常处理语义是否统一、异步方法是否吞没异常、`CancellationToken` 是否传播
```

- [ ] **Step 5: 更新"权威参考"章节**

把"## 权威参考"下的内容替换为：

```markdown
## 权威参考

团队规范以 [`knowledge-base/csharp/`](../../../../knowledge-base/csharp/README.md) 为准——本 skill 的审查依据直接来自该规范集，不额外维护规则文本。语言层的通用惯例背景可参考：

- [Microsoft C# 编码规范](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [Microsoft 标识符命名规则](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/identifier-names)
- [.NET Runtime 团队编码风格](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
```

- [ ] **Step 6: 验证"⛔ 不要做什么（反例黑名单）"章节未受影响**

```bash
grep -n "^## " "plugins/optimus-backend-plugin/skills/csharp-code-review/SKILL.md"
```

Expected: 输出仍包含"## 概述"、"## 审查流程"、"## 报告格式"、"## 审查清单"、"## 快速审查清单"、"## 权威参考"、"## ⛔ 不要做什么（反例黑名单）"这些标题，且"## ⛔ 不要做什么（反例黑名单）"章节下的 6 条反模式内容与改造前一致（本 Task 不涉及该章节）。

- [ ] **Step 7: 升级 SKILL.md frontmatter 版本号**

`metadata.version` 从 `"1.4.0"` 改为 `"1.4.1"`（Patch：修改已有内容，非新增功能、非破坏性变更，符合 `.claude/rules/skill-authoring.md` 版本规则）。

- [ ] **Step 8: 更新 `CHANGELOG.md`**

在 `plugins/optimus-backend-plugin/skills/csharp-code-review/CHANGELOG.md` 顶部追加：

```markdown
## [1.4.1] - 2026-08-22

### Changed
- 审查清单 12 类别改为引用 `knowledge-base/csharp/` 规范条款，不再自建重复规则文本
- 删除与审查清单重复的"常见违规速查表"整节
- 权威参考改为以 `knowledge-base/csharp/` 为团队规范准绳，Microsoft 官方文档降级为背景参考
```

- [ ] **Step 9: 升级仓库 `marketplace.json` 版本号**

按 `commit-cc-plugin` skill 的版本决策规则（`plugins/` 下更新已有内容 = Patch），编辑 `.claude-plugin/marketplace.json` 的 `"version"` 字段：`"10.0.4"` → `"10.0.5"`。

- [ ] **Step 10: Commit（走 `commit-cc-plugin` skill，不手动 git 流程）**

本 Task 涉及 `plugins/` 下用户可见 skill 的改动，执行时必须调用 `commit-cc-plugin` skill 完成提交与推送，不直接使用裸 `git commit`（`CLAUDE.md` 强制约定）。提交消息应说明：`csharp-code-review` 去重改造为引用 `knowledge-base/csharp/`，版本 1.4.0 → 1.4.1（Patch）。

---

## Task 7: `.claude/skills/knowledge-base-maintain/` 维护 skill

**Files:**
- Create: `.claude/skills/knowledge-base-maintain/SKILL.md`
- Create: `.claude/skills/knowledge-base-maintain/CHANGELOG.md`
- Create: `.kiro/skills/knowledge-base-maintain`（符号链接）

**Interfaces:**
- Consumes: `knowledge-base/check_index.py` 的 CLI（Task 3 产出：`python check_index.py [domain ...]`）
- Produces: `/knowledge-base-maintain` 触发的仓库自用 skill，无对外接口（其他 Task 不依赖它）

本 Task 是仓库自用 skill（`.claude/skills/` 下，非 `plugins/`），按 `CLAUDE.md` 版本规则不触发 `marketplace.json` 升级；按 `.claude/rules/skill-authoring.md`，`.claude/skills/` 不强制配 README.md。

- [ ] **Step 1: 创建 SKILL.md**

```markdown
---
name: knowledge-base-maintain
description: 新增、修改、迁移 knowledge-base/ 下的规范条目或 reference 条目时使用；同步更新 index.jsonl 索引、CHANGELOG.md 与版本号，并跑一致性校验。触发词："新增规范条目"、"知识库加一条"、"迁移知识库条目"、"校验知识库索引"。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要本机 Python 3（跑 knowledge-base/check_index.py 做一致性校验），无 MCP 或第三方 CLI 依赖。
allowed-tools: Read Write Edit Bash Grep Glob
---

# 知识库维护

维护 `knowledge-base/` 下的内容与索引一致性：新增条目、修改/迁移条目、仅校验三种场景。

## Step 1：确认场景与依赖

先确认 Python 3 可用：

```bash
python --version
```

不可用则提示用户安装 Python 3 后重试，终止本次操作（依赖检查失败，硬性阻断）。

确认场景：
- **新增条目**：新增一条 `rule` 或 `reference`
- **修改/迁移条目**：修改已有条目内容，或把内容从规范文件移到 `reference/`（或反之）
- **仅校验**：不新增/修改内容，只想看当前 `knowledge-base/` 一致性状态

## Step 2（新增条目）：收集条目信息

依次询问用户（已在触发语句中提供的不重复问）：

1. **`domain`**：目标领域（`csharp`/`wpf`/其他）。若目标领域目录不存在（`knowledge-base/<domain>/` 不存在），确认是新建领域——新建领域时先创建 `knowledge-base/<domain>/README.md`（参照 `knowledge-base/csharp/README.md` 的章节结构：文档目的、适用范围与读者、规范级别、阅读路径、文件地图）与空的 `knowledge-base/<domain>/index.jsonl`。
2. **`kind`**：`rule` 或 `reference`。
3. 若 `kind=rule`：追问 **`level`**（`MUST`/`SHOULD`/`MAY`）。
4. **正文归属**：`rule` 写入哪个规范文件的哪个章节（已有文件追加小节，或指出需要新建文件）；`reference` 写入 `reference/<主题slug>.md`（新文件，不编号）。
5. **`tags`**、**`summary`**、**`title`**：与用户共同确定，`summary` 一句话，不超过一行。

## Step 3（新增条目）：写入正文与索引

1. 用 Edit/Write 把正文内容写入 Step 2 确定的文件位置。
2. 生成 `id`：`<domain>.<文件编号或ref>.<slug>`（如 `csharp.02.xxx` 或 `csharp.ref.xxx`），确认在该领域 `index.jsonl` 中未出现过。
3. 用 Edit 在对应 `knowledge-base/<domain>/index.jsonl` **末尾追加一行**（不重排已有行），字段：`id`、`kind`、`level`（仅 rule）、`file`、`anchor`（标题文本，非 slug；`reference` 条目留空字符串）、`title`、`tags`、`summary`。

## Step 4（修改/迁移条目）：定位与同步

1. 用 Grep 在目标领域 `index.jsonl` 中按 `id` 或关键词定位现有记录行。
2. 修改正文内容（若涉及跨文件迁移，如从规范文件移到 `reference/`：先在新位置写入正文，再删除旧位置正文，最后更新索引行的 `file`/`anchor`/`kind` 字段——不得只改索引不改正文，也不得只改正文不改索引）。
3. 用 Edit 更新 `index.jsonl` 中对应行的变化字段。

## Step 5：运行一致性校验

```bash
cd knowledge-base && python check_index.py <domain>
```

- 输出 `OK: 共检查 N 条记录，未发现问题` → 继续 Step 6。
- 输出非零退出码 + 问题列表 → 逐条修复（常见问题：`anchor` 文本与实际标题不完全匹配、`file` 路径写错、`id` 重复），修复后重新运行本命令，直到 `OK`。

## Step 6：同步版本号与 CHANGELOG（新增/修改/迁移场景，仅校验场景跳过）

判断本次变更的版本升级级别：

| 变更类型 | 版本升级 |
|---|---|
| 新增领域、新增规范条目、新增 reference 条目 | Minor `x.X.x` |
| 修改已有规范/reference 内容、修正索引、文档优化 | Patch `x.x.X` |
| 删除领域、删除规范条目、规范措辞产生不兼容语义变化（如 SHOULD 改 MUST） | Major `X.x.x` |

用 Edit 更新 `knowledge-base/README.md` 顶部 `> 版本：x.x.x`，并在 `knowledge-base/CHANGELOG.md` 顶部追加对应版本条目（格式同 skill CHANGELOG：`## [版本号] - YYYY-MM-DD` + `### Added`/`Changed`/`Removed`/`Fixed`，只写实际发生的类别）。

## Step 7：提交

`knowledge-base/` 属于文档资产，不受 `commit-cc-plugin` 关于 `plugins/` 下 skill 改动的强制流程约束，但仍需遵循仓库通用 git 纪律（逐文件暂存、写清楚的提交信息）。若同一次改动还涉及 `plugins/` 下 skill（如某 skill 引用了新增条目），该部分改动必须走 `commit-cc-plugin`。

## 失败处理

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| `check_index.py` 报 `id` 重复 | 检查是否误用了已存在的 id 命名规则，改用更具体的 slug | 若确认是历史遗留重复，两条记录都需人工核对哪条是权威版本，不能随意删一条了事 |
| `check_index.py` 报 anchor 不匹配 | 打开目标文件确认标题文字的准确文本（含大小写、标点），更新索引 `anchor` 字段 | 若目标章节确实还不存在，先在正文补齐该章节标题，再回填索引 |
| 新建领域但用户未提供该领域的规范级别定义 | 参照 `knowledge-base/csharp/README.md` 的"规范级别"章节直接复用同一套 MUST/SHOULD/MAY 定义，无需重新设计 | 若用户希望该领域有不同的级别体系，先与用户确认具体差异再落地 |
```

- [ ] **Step 2: 创建 CHANGELOG.md**

```markdown
# Changelog

## [1.0.0] - 2026-08-22

### Added
- 初始版本：引导新增/修改/迁移 knowledge-base 条目，同步索引、CHANGELOG、版本号，调用 check_index.py 做一致性校验
```

- [ ] **Step 3: 创建 `.kiro/skills/` 符号链接**

Windows（PowerShell）：

```powershell
New-Item -ItemType SymbolicLink -Path ".kiro/skills/knowledge-base-maintain" -Target "..\..\.claude\skills\knowledge-base-maintain"
```

macOS / Linux：

```bash
ln -s ../../.claude/skills/knowledge-base-maintain .kiro/skills/knowledge-base-maintain
```

- [ ] **Step 4: 验证符号链接类型正确**

```bash
git ls-files -s .kiro/skills/knowledge-base-maintain 2>/dev/null || git add .kiro/skills/knowledge-base-maintain && git ls-files -s .kiro/skills/knowledge-base-maintain
```

Expected: 输出的文件 mode 为 `120000`（symlink blob），不是 `100644`（普通文件）。若为 `100644`，检查 `git config core.symlinks` 是否为 `true`，修正后重新创建链接。

- [ ] **Step 5: 本地测试验证 skill 可被加载**

参照 `test-locally` skill 的方式，在仓库根目录加载本仓库验证（不要求实际跑一次完整维护流程，只需确认 skill 被正确发现）：

```bash
claude --plugin-dir .
```

在新会话里输入触发词（如"知识库加一条"）确认 skill 被正确触发。确认后退出该验证会话。

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/knowledge-base-maintain .kiro/skills/knowledge-base-maintain
git commit -m "$(cat <<'EOF'
feat(knowledge-base): 新增 knowledge-base-maintain 仓库自用维护 skill

- 引导新增/修改/迁移 knowledge-base 条目，同步索引、CHANGELOG、版本号
- 调用 check_index.py 做一致性校验
- .kiro/skills/ 补同名符号链接镜像

Co-Authored-By: <当前会话实际使用的模型名> <noreply@anthropic.com>
EOF
)"
```

---

## 执行完成后的整体验证

所有 Task 完成后，运行一次全局校验确认知识库整体一致：

```bash
cd knowledge-base && python check_index.py csharp wpf
```

Expected: `OK: 共检查 14 条记录，未发现问题`。

再确认全仓无残留旧路径引用：

```bash
grep -rn "docs/csharp_doc\|docs/wpf_doc" --include="*.md" --include="*.json" . 2>/dev/null | grep -v "^./.remember/"
```

Expected: 无输出（`.remember/` 下的历史记忆文件按 spec 待实施清单第 6 项，属于历史快照，不需要更新）。

