import json
import tempfile
import unittest
from pathlib import Path

from check_index import (
    build_audit,
    check_anchor_exists,
    check_catalog,
    check_deprecated,
    check_domain_versions,
    check_duplicate_ids,
    check_file_exists,
    check_file_path_safe,
    check_id_format,
    check_orphan_files,
    check_schema,
    check_source_refs,
    find_headings,
    normalize_heading,
    parse_index_file,
    run_checks,
)


def valid_entry(**overrides):
    entry = {
        "id": "csharp.02.naming-core",
        "kind": "rule",
        "level": "MUST",
        "file": "02-coding-style.md",
        "anchor": "1.1 核心规则表",
        "title": "命名规则表",
        "tags": ["naming", "style"],
        "summary": "一句话摘要。",
    }
    entry.update(overrides)
    return entry


class TestNormalizeHeading(unittest.TestCase):
    def test_strips_hash_and_spaces(self):
        self.assertEqual(normalize_heading("## 1. 命名规范"), "1. 命名规范")

    def test_strips_backticks(self):
        self.assertEqual(normalize_heading("### 2.4 `var` 与对象创建"), "2.4 var 与对象创建")

    def test_collapses_extra_spaces(self):
        self.assertEqual(normalize_heading("#   1.  命名规范  "), "1. 命名规范")


class TestFindHeadings(unittest.TestCase):
    def test_finds_all_heading_levels(self):
        text = "# 标题\n正文\n## 二级\n### 三级\n非标题行 # 不是标题"
        self.assertEqual(find_headings(text), ["标题", "二级", "三级"])

    def test_empty_text_returns_empty_list(self):
        self.assertEqual(find_headings(""), [])


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


class TestCheckSchema(unittest.TestCase):
    def test_valid_entry_has_no_problems(self):
        self.assertEqual(check_schema(Path("."), valid_entry()), [])

    def test_reports_missing_required_fields(self):
        entry = valid_entry()
        del entry["summary"]
        del entry["tags"]
        problems = check_schema(Path("."), entry)
        self.assertEqual(len(problems), 1)
        self.assertIn("summary", problems[0])
        self.assertIn("tags", problems[0])

    def test_rejects_empty_summary(self):
        problems = check_schema(Path("."), valid_entry(summary="  "))
        self.assertTrue(any("summary" in p for p in problems))

    def test_rejects_non_list_tags(self):
        problems = check_schema(Path("."), valid_entry(tags="naming"))
        self.assertTrue(any("tags" in p for p in problems))

    def test_rejects_invalid_kind(self):
        problems = check_schema(Path("."), valid_entry(kind="guideline"))
        self.assertTrue(any("kind" in p for p in problems))

    def test_rejects_invalid_level(self):
        problems = check_schema(Path("."), valid_entry(level="REQUIRED"))
        self.assertTrue(any("level" in p for p in problems))

    def test_rule_without_level_is_reported(self):
        entry = valid_entry()
        del entry["level"]
        problems = check_schema(Path("."), entry)
        self.assertTrue(any("必须有 level" in p for p in problems))

    def test_reference_with_level_is_reported(self):
        entry = valid_entry(kind="reference", anchor="")
        problems = check_schema(Path("."), entry)
        self.assertTrue(any("不应有 level" in p for p in problems))

    def test_accepts_optional_governance_fields(self):
        entry = valid_entry(
            enforcement="review", status="active", source=["https://example.com"],
            applies_to=[".NET"], reviewed_at="2026-08-27", owner="desktop client team",
        )
        self.assertEqual(check_schema(Path("."), entry), [])

    def test_rejects_invalid_enforcement(self):
        problems = check_schema(Path("."), valid_entry(enforcement="blocking"))
        self.assertTrue(any("enforcement" in p for p in problems))

    def test_rejects_invalid_status(self):
        problems = check_schema(Path("."), valid_entry(status="draft"))
        self.assertTrue(any("status" in p for p in problems))

    def test_rejects_malformed_reviewed_at(self):
        problems = check_schema(Path("."), valid_entry(reviewed_at="2026/08/27"))
        self.assertTrue(any("reviewed_at" in p for p in problems))

    def test_rejects_may_with_ci_enforcement(self):
        """MAY 是可选做法，不应作为 CI 拦截依据。"""
        problems = check_schema(Path("."), valid_entry(level="MAY", enforcement="ci"))
        self.assertTrue(any("level=MAY" in p and "enforcement=ci" in p for p in problems))

    def test_allows_may_with_advisory_enforcement(self):
        self.assertEqual(
            check_schema(Path("."), valid_entry(level="MAY", enforcement="advisory")), [])

    def test_allows_must_with_ci_enforcement(self):
        self.assertEqual(
            check_schema(Path("."), valid_entry(level="MUST", enforcement="ci")), [])

    def test_rejects_reference_with_enforcement(self):
        entry = valid_entry(kind="reference", anchor="", enforcement="review")
        del entry["level"]
        problems = check_schema(Path("."), entry)
        self.assertTrue(any("不应有 enforcement" in p for p in problems))


class TestCheckIdFormat(unittest.TestCase):
    def test_accepts_numbered_id(self):
        self.assertIsNone(check_id_format("csharp", valid_entry()))

    def test_accepts_ref_id(self):
        entry = valid_entry(id="media.ref.video-codecs")
        self.assertIsNone(check_id_format("media", entry))

    def test_rejects_missing_middle_segment(self):
        result = check_id_format("csharp", valid_entry(id="csharp.naming"))
        self.assertIsNotNone(result)

    def test_rejects_single_digit_number(self):
        result = check_id_format("csharp", valid_entry(id="csharp.2.naming"))
        self.assertIsNotNone(result)

    def test_rejects_uppercase_slug(self):
        result = check_id_format("csharp", valid_entry(id="csharp.02.Naming"))
        self.assertIsNotNone(result)

    def test_rejects_prefix_not_matching_domain(self):
        result = check_id_format("wpf", valid_entry())
        self.assertIsNotNone(result)
        self.assertIn("wpf.", result)


class TestCheckFilePathSafe(unittest.TestCase):
    def test_allows_path_inside_domain(self):
        with tempfile.TemporaryDirectory() as d:
            entry = valid_entry(file="rules/02-coding-style.md")
            self.assertIsNone(check_file_path_safe(Path(d), entry))

    def test_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            entry = valid_entry(file="../wpf/03-mvvm.md")
            result = check_file_path_safe(Path(d), entry)
            self.assertIsNotNone(result)
            self.assertIn("越出领域目录", result)

    def test_rejects_absolute_path(self):
        with tempfile.TemporaryDirectory() as d:
            entry = valid_entry(file="C:/tmp/x.md")
            result = check_file_path_safe(Path(d), entry)
            self.assertIsNotNone(result)
            self.assertIn("绝对路径", result)


class TestCheckSourceRefs(unittest.TestCase):
    def _domain(self, base):
        (base / "reference").mkdir(parents=True, exist_ok=True)
        (base / "reference" / "workflows.md").write_text(
            "# 标题\n## 1. 三种主流分支工作流对比\n", encoding="utf-8")
        return base

    def test_no_source_field_is_ok(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(check_source_refs(Path(d), valid_entry()), [])

    def test_external_url_is_not_checked(self):
        with tempfile.TemporaryDirectory() as d:
            entry = valid_entry(source=["https://www.conventionalcommits.org/"])
            self.assertEqual(check_source_refs(Path(d), entry), [])

    def test_valid_internal_ref_is_ok(self):
        with tempfile.TemporaryDirectory() as d:
            base = self._domain(Path(d))
            entry = valid_entry(source=["reference/workflows.md#1. 三种主流分支工作流对比"])
            self.assertEqual(check_source_refs(base, entry), [])

    def test_ref_without_anchor_is_ok(self):
        with tempfile.TemporaryDirectory() as d:
            base = self._domain(Path(d))
            entry = valid_entry(source=["reference/workflows.md"])
            self.assertEqual(check_source_refs(base, entry), [])

    def test_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = self._domain(Path(d))
            entry = valid_entry(source=["reference/gone.md#某章节"])
            problems = check_source_refs(base, entry)
            self.assertTrue(any("source 引用的文件不存在" in p for p in problems))

    def test_missing_anchor_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = self._domain(Path(d))
            entry = valid_entry(source=["reference/workflows.md#不存在的章节"])
            problems = check_source_refs(base, entry)
            self.assertTrue(any("source 锚点未在" in p for p in problems))


class TestCheckDeprecated(unittest.TestCase):
    """废弃条目的看守规则。

    `deprecated` 此前是纯枚举占位——全库 326 条无一使用，废弃只能走「删索引条目」
    （3.0.0 删 csharp.15.quality-gate-overview 即是），外部消费者拿旧 id 检索只得到
    「查不到」而非「已废弃，改用 X」。这批检查是让该状态可用的前提。
    """

    def _domain(self, d, heading="## 1. 质量门禁总览（已废弃）", summary="已废弃：改用 git.03.pr-conventions。"):
        base = Path(d)
        (base / "rules").mkdir(parents=True, exist_ok=True)
        (base / "rules" / "15-quality.md").write_text(
            f"# 15 · 质量\n\n{heading}\n\n> 已废弃（2026-08-28）：本节约束迁至 git 领域。\n",
            encoding="utf-8")
        entry = valid_entry(
            id="csharp.15.quality-gate-overview", file="rules/15-quality.md",
            anchor="1. 质量门禁总览", status="deprecated", summary=summary)
        return base, entry

    def test_active_entry_is_not_checked(self):
        """缺省状态与显式 active 都不走废弃校验，避免给 314 条未标 status 的条目添负担。"""
        with tempfile.TemporaryDirectory() as d:
            base, entry = self._domain(d)
            for status in (None, "active", "experimental"):
                e = dict(entry)
                e.pop("status", None) if status is None else e.update(status=status)
                self.assertEqual(check_deprecated(base, e), [], status)

    def test_well_formed_deprecation_passes(self):
        with tempfile.TemporaryDirectory() as d:
            base, entry = self._domain(d)
            self.assertEqual(check_deprecated(base, entry), [])

    def test_requires_deprecation_marker_in_heading(self):
        """索引说废弃、正文标题没标记 → 按 file+anchor 读正文的人毫不知情。"""
        with tempfile.TemporaryDirectory() as d:
            base, entry = self._domain(d, heading="## 1. 质量门禁总览")
            problems = check_deprecated(base, entry)
            self.assertTrue(any("正文标题未标注已废弃" in p for p in problems), problems)

    def test_requires_successor_in_summary(self):
        """只标废弃不给去向，比直接删更糟——检索者拿到一条死规则且无路可走。"""
        with tempfile.TemporaryDirectory() as d:
            base, entry = self._domain(d, summary="本条已不再适用。")
            problems = check_deprecated(base, entry)
            self.assertTrue(any("summary 未说明替代去向" in p for p in problems), problems)

    def test_accepts_successor_expressed_as_path(self):
        """替代去向可以是条目 id，也可以是文件路径。"""
        with tempfile.TemporaryDirectory() as d:
            base, entry = self._domain(
                d, summary="已废弃：改见 knowledge-base/git/rules/03-pull-requests.md。")
            self.assertEqual(check_deprecated(base, entry), [])

    def test_rejects_ci_enforcement_on_deprecated(self):
        """已废弃却仍作为 CI 拦截依据是矛盾状态。"""
        with tempfile.TemporaryDirectory() as d:
            base, entry = self._domain(d)
            entry["enforcement"] = "ci"
            problems = check_deprecated(base, entry)
            self.assertTrue(any("enforcement=ci" in p for p in problems), problems)

    def test_missing_file_is_not_double_reported(self):
        """file 不存在由 check_file_exists 报告，此处不重复。"""
        with tempfile.TemporaryDirectory() as d:
            base, entry = self._domain(d)
            entry["file"] = "rules/gone.md"
            self.assertEqual([p for p in check_deprecated(base, entry) if "标题" in p], [])


class TestDeprecatedSourceRefs(unittest.TestCase):
    def test_source_pointing_at_deprecated_section_is_reported(self):
        """活跃规则的理由不得挂在已废弃小节上。"""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "reference").mkdir(parents=True)
            (base / "reference" / "tooling.md").write_text(
                "# 工具\n\n## 2. 旧方案对比（已废弃）\n\n## 3. 现方案\n", encoding="utf-8")
            entry = valid_entry(source=["reference/tooling.md#2. 旧方案对比"])
            problems = check_source_refs(base, entry)
            self.assertTrue(any("已废弃" in p for p in problems), problems)

    def test_source_pointing_at_active_section_is_ok(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "reference").mkdir(parents=True)
            (base / "reference" / "tooling.md").write_text(
                "# 工具\n\n## 2. 旧方案对比（已废弃）\n\n## 3. 现方案\n", encoding="utf-8")
            entry = valid_entry(source=["reference/tooling.md#3. 现方案"])
            self.assertEqual(check_source_refs(base, entry), [])


class TestCheckOrphanFiles(unittest.TestCase):
    def test_readme_is_not_orphan(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "README.md").write_text("# 领域说明\n", encoding="utf-8")
            self.assertEqual(check_orphan_files(domain_dir, []), [])

    def test_reports_unindexed_markdown(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "rules").mkdir()
            (domain_dir / "rules" / "01-x.md").write_text("## 章节\n", encoding="utf-8")
            problems = check_orphan_files(domain_dir, [])
            self.assertEqual(len(problems), 1)
            self.assertIn("rules/01-x.md", problems[0])

    def test_indexed_file_is_not_orphan(self):
        with tempfile.TemporaryDirectory() as d:
            domain_dir = Path(d)
            (domain_dir / "rules").mkdir()
            (domain_dir / "rules" / "01-x.md").write_text("## 章节\n", encoding="utf-8")
            entries = [valid_entry(file="rules/01-x.md")]
            self.assertEqual(check_orphan_files(domain_dir, entries), [])


def write_domain(base, domain, entries, files=None, version="7.2.1"):
    """在临时 base 目录下造一个领域：写入 index.jsonl 与 files 指定的 Markdown。"""
    domain_dir = base / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    for rel, text in (files or {}).items():
        target = domain_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    domain_dir.joinpath("index.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries),
        encoding="utf-8",
    )
    if version is not None:
        domain_dir.joinpath("README.md").write_text(
            f"# {domain}\n\n> 版本：{version}\n", encoding="utf-8")
        domain_dir.joinpath("CHANGELOG.md").write_text(
            f"# Changelog\n\n## [{version}] - 2026-08-29\n\n### Changed\n- x\n",
            encoding="utf-8",
        )
    return domain_dir


def write_catalog(base, domains, **overrides):
    """为临时 base 写一份与 domains 一致的 catalog.json，让 run_checks 的全局检查通过。"""
    entry_defaults = {
        "title": "t", "categories": [], "owner": "o",
        "status": "active", "reviewed_at": "2026-08-27",
    }
    payload = {
        "version": "1.0",
        "domains": [dict(entry_defaults, domain=d) for d in domains],
    }
    payload.update(overrides)
    base.joinpath("catalog.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class TestRunChecks(unittest.TestCase):
    def test_no_problems_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "csharp",
                [valid_entry(id="csharp.01.naming", file="rules/01-x.md", anchor="命名规范")],
                {"rules/01-x.md": "## 命名规范\n"},
            )
            write_catalog(base, ["csharp"])
            self.assertEqual(run_checks(base, ["csharp"]), [])

    def test_collects_problems_from_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "csharp",
                [valid_entry(id="csharp.01.naming", file="missing.md", anchor="")],
            )
            write_catalog(base, ["csharp"])
            problems = run_checks(base, ["csharp"])
            self.assertEqual(len(problems), 1)
            self.assertIn("missing.md", problems[0])

    def test_detects_cross_domain_duplicate_when_checking_one_domain(self):
        """单领域检查也必须发现与其他领域的 id 冲突。"""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            shared = valid_entry(id="csharp.01.naming", file="rules/01-x.md", anchor="命名规范")
            write_domain(base, "csharp", [shared], {"rules/01-x.md": "## 命名规范\n"})
            write_domain(base, "wpf", [dict(shared)], {"rules/01-x.md": "## 命名规范\n"})
            write_catalog(base, ["csharp", "wpf"])
            problems = run_checks(base, ["csharp"])
            self.assertTrue(any("重复 id" in p for p in problems))

    def test_reports_missing_index_file(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "csharp").mkdir()
            write_catalog(base, [])
            problems = run_checks(base, ["csharp"])
            self.assertTrue(any("index.jsonl 不存在" in p for p in problems))

    def test_reports_orphan_file(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "csharp",
                [valid_entry(id="csharp.01.naming", file="rules/01-x.md", anchor="命名规范")],
                {"rules/01-x.md": "## 命名规范\n", "rules/02-orphan.md": "## 未登记\n"},
            )
            write_catalog(base, ["csharp"])
            problems = run_checks(base, ["csharp"])
            self.assertTrue(any("孤儿文件" in p and "02-orphan.md" in p for p in problems))

    def test_reports_schema_and_enum_violations(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "csharp",
                [valid_entry(id="csharp.01.naming", file="rules/01-x.md",
                             anchor="命名规范", level="REQUIRED", enforcement="blocking")],
                {"rules/01-x.md": "## 命名规范\n"},
            )
            write_catalog(base, ["csharp"])
            problems = run_checks(base, ["csharp"])
            self.assertTrue(any("level" in p for p in problems))
            self.assertTrue(any("enforcement" in p for p in problems))


class TestCheckCatalog(unittest.TestCase):
    def _domain(self, base, name="csharp"):
        write_domain(
            base, name,
            [valid_entry(id=f"{name}.01.naming", file="rules/01-x.md", anchor="命名规范")],
            {"rules/01-x.md": "## 命名规范\n"},
        )

    def test_matching_catalog_has_no_problems(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            write_catalog(base, ["csharp"])
            self.assertEqual(check_catalog(base), [])

    def test_missing_catalog_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            self.assertTrue(any("catalog.json 不存在" in p for p in check_catalog(base)))

    def test_unlisted_domain_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            self._domain(base, "wpf")
            write_catalog(base, ["csharp"])
            problems = check_catalog(base)
            self.assertTrue(any("未登记到 catalog.json" in p and "wpf" in p for p in problems))

    def test_stale_catalog_entry_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            write_catalog(base, ["csharp", "deleted-domain"])
            problems = check_catalog(base)
            self.assertTrue(any("不存在的领域" in p and "deleted-domain" in p for p in problems))

    def test_missing_category_directory_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            base.joinpath("catalog.json").write_text(json.dumps({
                "domains": [{"domain": "csharp", "title": "t", "categories": ["rules", "examples"],
                             "owner": "o", "status": "active", "reviewed_at": "2026-08-27"}]
            }, ensure_ascii=False), encoding="utf-8")
            problems = check_catalog(base)
            self.assertTrue(any("分类目录不存在" in p and "examples" in p for p in problems))

    def test_invalid_status_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            base.joinpath("catalog.json").write_text(json.dumps({
                "domains": [{"domain": "csharp", "title": "t", "categories": [],
                             "owner": "o", "status": "draft", "reviewed_at": "2026-08-27"}]
            }, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(any("非法 status" in p for p in check_catalog(base)))


class TestCheckDomainVersions(unittest.TestCase):
    def _domain(self, base, name="csharp", readme_ver="7.2.1", changelog_ver="7.2.1"):
        d = base / name
        d.mkdir(parents=True, exist_ok=True)
        d.joinpath("index.jsonl").write_text("", encoding="utf-8")
        if readme_ver is not None:
            d.joinpath("README.md").write_text(
                f"# {name}\n\n> 版本：{readme_ver}\n\n正文\n", encoding="utf-8")
        else:
            d.joinpath("README.md").write_text(f"# {name}\n\n正文\n", encoding="utf-8")
        if changelog_ver is not None:
            d.joinpath("CHANGELOG.md").write_text(
                f"# Changelog\n\n## [{changelog_ver}] - 2026-08-29\n\n### Changed\n- x\n",
                encoding="utf-8")

    def test_matching_versions_have_no_problems(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            self.assertEqual(check_domain_versions(base), [])

    def test_mismatched_version_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base, readme_ver="7.2.1", changelog_ver="8.0.0")
            problems = check_domain_versions(base)
            self.assertTrue(any("版本号不一致" in p and "7.2.1" in p and "8.0.0" in p
                                for p in problems))

    def test_missing_version_line_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base, readme_ver=None)
            self.assertTrue(any("README.md 缺少版本行" in p for p in check_domain_versions(base)))

    def test_missing_changelog_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base, changelog_ver=None)
            self.assertTrue(any("CHANGELOG.md 不存在" in p for p in check_domain_versions(base)))

    def test_changelog_without_version_entry_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self._domain(base)
            (base / "csharp" / "CHANGELOG.md").write_text(
                "# Changelog\n\n还没有任何版本条目\n", encoding="utf-8")
            self.assertTrue(any("CHANGELOG.md 无版本条目" in p
                                for p in check_domain_versions(base)))


class TestBuildAudit(unittest.TestCase):
    def test_counts_entries_and_levels(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "csharp",
                [
                    valid_entry(id="csharp.01.a", file="rules/01-x.md", anchor="甲"),
                    valid_entry(id="csharp.01.b", file="rules/01-x.md", anchor="乙", level="SHOULD"),
                ],
                {"rules/01-x.md": "## 甲\n## 乙\n"},
            )
            report = build_audit(base, ["csharp"])
            self.assertEqual(report["totals"]["entries"], 2)
            self.assertEqual(report["totals"]["rules"], 2)
            self.assertEqual(report["domains"]["csharp"]["levels"], {"MUST": 1, "SHOULD": 1})
            self.assertEqual(report["domains"]["csharp"]["coverage_ratio"], 1.0)

    def test_coverage_ratio_reflects_unindexed_headings(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "csharp",
                [valid_entry(id="csharp.01.a", file="rules/01-x.md", anchor="甲")],
                {"rules/01-x.md": "## 甲\n## 乙\n## 丙\n## 丁\n"},
            )
            report = build_audit(base, ["csharp"])
            self.assertEqual(report["domains"]["csharp"]["coverage_ratio"], 0.25)

    def test_reference_only_domain_has_no_coverage_ratio(self):
        """reference 按整篇文档登记，不参与覆盖率计算。"""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            entry = valid_entry(id="media.ref.codecs", kind="reference",
                                file="reference/codecs.md", anchor="")
            del entry["level"]
            write_domain(base, "media", [entry],
                         {"reference/codecs.md": "## 一\n## 二\n## 三\n"})
            report = build_audit(base, ["media"])
            self.assertIsNone(report["domains"]["media"]["coverage_ratio"])
            self.assertEqual(report["totals"]["references"], 1)

    def test_reports_enforcement_distribution(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "git",
                [
                    valid_entry(id="git.01.a", file="rules/01-x.md", anchor="甲", enforcement="ci"),
                    valid_entry(id="git.01.b", file="rules/01-x.md", anchor="乙", enforcement="review"),
                    valid_entry(id="git.01.c", file="rules/01-x.md", anchor="丙"),
                ],
                {"rules/01-x.md": "## 甲\n## 乙\n## 丙\n"},
            )
            report = build_audit(base, ["git"])
            data = report["domains"]["git"]
            self.assertEqual(data["enforcements"], {"ci": 1, "review": 1, "(未填)": 1})
            self.assertEqual(data["enforcement_coverage"], round(2 / 3, 3))
            self.assertEqual(report["totals"]["enforcement_filled"], 2)

    def test_subsection_anchors_count_toward_parent_section(self):
        """anchor 指向 h3 时，其父 h2 视为已覆盖——按更细粒度登记不该被算成未登记。"""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "csharp",
                [
                    valid_entry(id="csharp.02.a", file="rules/02-style.md", anchor="1.1 核心规则表"),
                    valid_entry(id="csharp.02.b", file="rules/02-style.md", anchor="1.2 命名禁忌"),
                    valid_entry(id="csharp.02.c", file="rules/02-style.md", anchor="2. 编码风格"),
                ],
                {"rules/02-style.md": "## 1. 命名规范\n### 1.1 核心规则表\n### 1.2 命名禁忌\n## 2. 编码风格\n"},
            )
            c = build_audit(base, ["csharp"])["domains"]["csharp"]["coverage"]["rules/02-style.md"]
            self.assertEqual((c["indexed"], c["eligible_headings"]), (2, 2))

    def test_extra_entries_do_not_mask_an_uncovered_section(self):
        """多条目集中在同一小节时，不得让另一个空缺小节被算成已覆盖。

        旧算法用 min(条目数, h2 数) 封顶：3 条全落在「1.」上也记 2/2 满分，
        「2.」的真实空缺被条目数掩盖。实测 csharp/rules/12-testing.md 正中此形态。
        """
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "csharp",
                [
                    valid_entry(id="csharp.02.a", file="rules/02-style.md", anchor="1.1 甲"),
                    valid_entry(id="csharp.02.b", file="rules/02-style.md", anchor="1.2 乙"),
                    valid_entry(id="csharp.02.c", file="rules/02-style.md", anchor="1.3 丙"),
                ],
                {"rules/02-style.md": "## 1. 命名规范\n### 1.1 甲\n### 1.2 乙\n### 1.3 丙\n## 2. 编码风格\n"},
            )
            c = build_audit(base, ["csharp"])["domains"]["csharp"]["coverage"]["rules/02-style.md"]
            self.assertEqual((c["indexed"], c["eligible_headings"]), (1, 2))

    def test_counts_deprecated_entries(self):
        """审计不报废弃条目数，等于放任它们无声堆积——保留正文的废弃方式尤其需要这个计数。"""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            write_domain(
                base, "git",
                [
                    valid_entry(id="git.01.a", file="rules/01-x.md", anchor="甲"),
                    valid_entry(id="git.01.b", file="rules/01-x.md", anchor="乙（已废弃）",
                                status="deprecated", summary="已废弃：改用 git.01.a。"),
                ],
                {"rules/01-x.md": "## 甲\n## 乙（已废弃）\n"},
            )
            report = build_audit(base, ["git"])
            self.assertEqual(report["domains"]["git"]["deprecated"], ["git.01.b"])
            self.assertEqual(report["totals"]["deprecated"], 1)


if __name__ == "__main__":
    unittest.main()
