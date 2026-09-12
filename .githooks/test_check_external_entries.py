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


def write_raw_marketplace(root, data):
    """按给定 dict 原样写 marketplace.json，用于覆盖顶层 name 与 metadata。"""
    d = root / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "marketplace.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def local_entry(name="first-party", source="./plugins/first-party", **over):
    """一条合法的本地相对路径条目。"""
    e = {"name": name, "source": source, "description": "d"}
    e.update(over)
    return e


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
        """本地相对路径条目不适用 sha 与台账检查，路径形态仍照查。"""
        (self.root / "plugins" / "first-party").mkdir(parents=True)
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

    # ---------- 名字：保留名与下游字符集 ----------

    def test_reserved_marketplace_name_blocked(self):
        """保留名每次加载都重新检查，用了它某个版本起会直接停止加载。"""
        write_raw_marketplace(self.root, {"name": "claude-code-plugins",
                                          "owner": {"name": "x"}, "plugins": []})
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("03.reserved-names", problems[0])

    def test_desktop_reserved_marketplace_name_blocked(self):
        """Claude Desktop 的三个保留名不分大小写，Claude Code 自己是接受的。"""
        write_raw_marketplace(self.root, {"name": "Org-Provisioned",
                                          "owner": {"name": "x"}, "plugins": []})
        problems = check_all(self.root)
        self.assertTrue(any("downstream-sync" in p for p in problems))

    def test_non_kebab_marketplace_name_blocked(self):
        write_raw_marketplace(self.root, {"name": "My_Marketplace",
                                          "owner": {"name": "x"}, "plugins": []})
        problems = check_all(self.root)
        self.assertTrue(any("kebab" in p for p in problems))

    def test_entry_name_violating_desktop_charset_blocked(self):
        """条目名不合规不会报错，而是被 Claude Desktop 静默删除——只能提交时拦。"""
        (self.root / "plugins" / "a b").mkdir(parents=True)
        write_marketplace(self.root, [local_entry(name="a b", source="./plugins/a b")])
        problems = check_all(self.root)
        self.assertTrue(any("downstream-sync" in p for p in problems))

    def test_missing_top_level_name_blocked(self):
        write_raw_marketplace(self.root, {"owner": {"name": "x"}, "plugins": []})
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("03.required-fields", problems[0])

    # ---------- 本地路径源 ----------

    def test_local_source_without_dot_slash_blocked(self):
        """裸名只在设了 metadata.pluginRoot 时成立。"""
        (self.root / "plugins").mkdir()
        write_marketplace(self.root, [local_entry(source="plugins/first-party")])
        problems = check_all(self.root)
        self.assertTrue(any("必须以 ./ 开头" in p for p in problems))

    def test_bare_name_with_plugin_root_passes(self):
        write_raw_marketplace(self.root, {
            "name": "m", "owner": {"name": "x"},
            "metadata": {"pluginRoot": "./plugins"},
            "plugins": [local_entry(source="first-party")]})
        self.assertEqual(check_all(self.root), [])

    def test_local_source_with_parent_traversal_blocked(self):
        write_marketplace(self.root, [local_entry(source="./../shared/plugin")])
        problems = check_all(self.root)
        self.assertTrue(any("02.path-escape" in p for p in problems))

    def test_local_source_with_backslash_blocked(self):
        """反斜杠路径只在 Windows 上加载，macOS 与 Linux 直接拒绝该条目。"""
        write_marketplace(self.root, [local_entry(source=".\\plugins\\first-party")])
        problems = check_all(self.root)
        self.assertTrue(any("反斜杠" in p for p in problems))

    def test_local_source_pointing_to_missing_dir_blocked(self):
        write_marketplace(self.root, [local_entry()])
        problems = check_all(self.root)
        self.assertTrue(any("不存在" in p for p in problems))

    # ---------- relevance ----------

    def test_valid_relevance_passes(self):
        (self.root / "plugins" / "first-party").mkdir(parents=True)
        write_marketplace(self.root, [local_entry(relevance={
            "topic": "Terraform",
            "signals": {"cli": ["terraform"], "filesRead": ["**/*.tf"],
                        "hosts": ["api.example.com"],
                        "manifestDeps": [{"file": r"[/\\]package\.json$",
                                          "pattern": r"\"stripe\"\s*:"}]}})])
        self.assertEqual(check_all(self.root), [])

    def test_relevance_topic_too_long_blocked(self):
        (self.root / "plugins" / "first-party").mkdir(parents=True)
        write_marketplace(self.root, [local_entry(relevance={
            "topic": "T" * 65, "signals": {"cli": ["t"]}})])
        problems = check_all(self.root)
        self.assertTrue(any("topic" in p for p in problems))

    def test_unknown_signal_name_blocked(self):
        """拼错的信号名不报错、只静默不匹配，所以必须在提交时拦。"""
        (self.root / "plugins" / "first-party").mkdir(parents=True)
        write_marketplace(self.root, [local_entry(relevance={
            "signals": {"filesRed": ["**/*.tf"]}})])
        problems = check_all(self.root)
        self.assertTrue(any("未知信号名" in p for p in problems))

    def test_too_many_cli_signals_blocked(self):
        (self.root / "plugins" / "first-party").mkdir(parents=True)
        write_marketplace(self.root, [local_entry(relevance={
            "signals": {"cli": [f"c{i}" for i in range(11)]}})])
        problems = check_all(self.root)
        self.assertTrue(any("上限 10" in p for p in problems))

    def test_hosts_with_scheme_or_port_blocked(self):
        (self.root / "plugins" / "first-party").mkdir(parents=True)
        write_marketplace(self.root, [local_entry(relevance={
            "signals": {"hosts": ["https://api.example.com", "api.example.com:443"]}})])
        problems = check_all(self.root)
        self.assertEqual(len([p for p in problems if "裸小写主机名" in p]), 2)

    def test_manifest_deps_without_end_anchor_blocked(self):
        """起始锚定的 file 模式永远不会匹配绝对路径。"""
        (self.root / "plugins" / "first-party").mkdir(parents=True)
        write_marketplace(self.root, [local_entry(relevance={
            "signals": {"manifestDeps": [{"file": r"^package\.json",
                                          "pattern": "stripe"}]}})])
        problems = check_all(self.root)
        self.assertTrue(any("末尾锚定" in p for p in problems))

    def test_relevance_without_signals_blocked(self):
        (self.root / "plugins" / "first-party").mkdir(parents=True)
        write_marketplace(self.root, [local_entry(relevance={"topic": "X"})])
        problems = check_all(self.root)
        self.assertTrue(any("signals" in p for p in problems))

    # ---------- .claude-plugin/ 目录 ----------

    def test_component_dir_inside_claude_plugin_blocked(self):
        """组件放进 .claude-plugin/ 后插件仍正常加载，组件全部不出现。"""
        (self.root / "plugins" / "p1" / ".claude-plugin" / "skills").mkdir(parents=True)
        (self.root / "plugins" / "p1" / ".claude-plugin" / "plugin.json").write_text(
            "{}", encoding="utf-8")
        write_marketplace(self.root, [])
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("02.claude-plugin-dir-only-manifest", problems[0])

    def test_claude_plugin_dir_with_only_manifest_passes(self):
        (self.root / "plugins" / "p1" / ".claude-plugin").mkdir(parents=True)
        (self.root / "plugins" / "p1" / ".claude-plugin" / "plugin.json").write_text(
            "{}", encoding="utf-8")
        write_marketplace(self.root, [])
        self.assertEqual(check_all(self.root), [])

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
