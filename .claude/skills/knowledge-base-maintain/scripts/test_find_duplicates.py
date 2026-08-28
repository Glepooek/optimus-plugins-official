import unittest

from find_duplicates import (
    entry_terms,
    find_candidates,
    is_structural,
    maximal,
    shared_phrases,
    similarity,
    substantive_overlap,
    tokenize,
)


def rule(rid, title, summary, tags=(), file="rules/01-x.md", anchor="1. x"):
    return {
        "id": rid, "kind": "rule", "level": "MUST", "title": title,
        "summary": summary, "tags": list(tags), "file": file, "anchor": anchor,
    }


def score(a, b):
    ta, ga = entry_terms(a)
    tb, gb = entry_terms(b)
    return similarity(ta, tb, ga, gb)


class TestTokenize(unittest.TestCase):
    def test_splits_cjk_into_ngrams(self):
        terms = tokenize("集成测试")
        self.assertIn("集成", terms)
        self.assertIn("集成测", terms)

    def test_keeps_ascii_words_whole(self):
        self.assertIn("targetframework", tokenize("统一 TargetFramework 配置"))

    def test_drops_single_char_ascii(self):
        self.assertNotIn("a", tokenize("use a value"))

    def test_drops_stopword_ngrams(self):
        self.assertNotIn("禁止", tokenize("禁止硬编码"))


class TestIsStructural(unittest.TestCase):
    def test_stopword_prefix_leaves_no_substance(self):
        """「禁止直接」剥掉停用词只剩「直接」——纯结构，不该计分。"""
        self.assertTrue(is_structural("禁止直"))

    def test_substantive_phrase_kept(self):
        self.assertFalse(is_structural("须立即轮换"))

    def test_bare_substance_kept(self):
        self.assertFalse(is_structural("语义化版本"))


class TestMaximal(unittest.TestCase):
    def test_drops_nested_fragments(self):
        """一次共现被切成多个重叠片段时，只保留最长的那个。"""
        self.assertEqual(maximal({"止直", "止直接", "直接", "禁止直接"}), ["禁止直接"])

    def test_keeps_disjoint_fragments(self):
        self.assertEqual(set(maximal({"轮换", "语义化"})), {"轮换", "语义化"})


class TestSubstantiveOverlap(unittest.TestCase):
    def test_discards_cross_word_fragments_of_structural_phrase(self):
        """「禁止直接」的跨词碎片「止直」不含完整停用词，必须靠"先取极大、再剔结构性"
        的顺序丢掉——顺序反了它就会伪装成主题重叠被计分。"""
        a = tokenize("禁止直接抛 Exception")
        b = tokenize("禁止直接在主干提交")
        self.assertEqual(substantive_overlap(a, b), [])

    def test_keeps_real_shared_topic(self):
        a = tokenize("Git 历史中的密钥视为已泄露须立即轮换")
        b = tokenize("一旦进入 Git 历史视为已泄露须立即轮换")
        peaks = substantive_overlap(a, b)
        self.assertTrue(peaks)
        self.assertTrue(any(len(p) >= 4 for p in peaks))


class TestSimilarity(unittest.TestCase):
    def test_identical_titles_score_high(self):
        a = rule("csharp.12.it", "集成测试验证真实协作，禁止连生产资源",
                 "集成测试验证真实协作，不得连生产资源。")
        b = rule("wpf.11.it", "集成测试验证真实协作，禁止连生产资源",
                 "集成测试验证真实协作，不得连生产资源。")
        self.assertGreater(score(a, b), 0.6)

    def test_unrelated_rules_sharing_only_structural_phrase_score_low(self):
        """「禁止直接」是两条无关规则唯一的共同点，不该把它们判为重复。"""
        a = rule("csharp.05.ex", "优先内置异常类型",
                 "优先内置异常类型，禁止直接抛 Exception。")
        b = rule("git.01.branch", "主干始终保持可发布",
                 "主干始终保持可发布状态，禁止直接在主干提交。")
        self.assertLess(score(a, b), 0.10)

    def test_long_summary_does_not_dilute_real_overlap(self):
        """覆盖率而非 Jaccard：长 summary 不该把真重叠稀释掉。"""
        short = rule("a.01.x", "密钥禁止硬编码", "Git 历史中的密钥视为已泄露须立即轮换。")
        long = rule(
            "b.01.y", "禁止提交密钥",
            "密钥/密码/Token 禁止出现在提交中，一旦进入 Git 历史视为已泄露须立即轮换，"
            "禁止直接提交大体积二进制文件，仓库须配置扫描工具并在 CI 中拦截。")
        self.assertGreater(score(short, long), 0.15)

    def test_no_overlap_scores_zero(self):
        a = rule("a.01.x", "面板选型", "优先 Grid 而非嵌套 StackPanel。")
        b = rule("b.01.y", "标签命名", "tag 用 v<major>.<minor> 格式。")
        self.assertEqual(score(a, b), 0.0)

    def test_shared_tags_add_bonus_but_cannot_carry_alone(self):
        """tags 只作加分项：词项毫无重叠时，共享 tag 也不能把一对推上榜。"""
        a = rule("a.01.x", "面板选型", "优先 Grid 而非嵌套 StackPanel。", tags=["perf"])
        b = rule("b.01.y", "标签命名", "tag 用 v<major> 格式。", tags=["perf"])
        self.assertEqual(score(a, b), 0.0)


class TestSharedPhrases(unittest.TestCase):
    def test_stitches_sliding_windows_into_one_phrase(self):
        """「视为已泄露须立即轮换」被切成 7 个 4-gram，展示时须拼回一条而非 7 条碎片。"""
        a = tokenize("Git 历史中的密钥视为已泄露须立即轮换")
        b = tokenize("一旦进入 Git 历史视为已泄露须立即轮换")
        phrases = shared_phrases(a, b)
        self.assertIn("视为已泄露须立即轮换", phrases)
        self.assertFalse([p for p in phrases if p in "视为已泄露须立即轮换" and p != "视为已泄露须立即轮换" and len(p) > 2],
                         "拼接后不应残留被长片段包含的碎片")

    def test_returns_substantive_maximal_phrases(self):
        a = rule("a.01.x", "密钥管理", "Git 历史中的密钥视为已泄露须立即轮换。")
        b = rule("b.01.y", "禁止提交密钥", "一旦进入 Git 历史视为已泄露须立即轮换。")
        ta, _ = entry_terms(a)
        tb, _ = entry_terms(b)
        phrases = shared_phrases(ta, tb)
        self.assertTrue(any("轮换" in p for p in phrases))
        self.assertFalse(any(is_structural(p) for p in phrases))


class TestFindCandidates(unittest.TestCase):
    def test_cross_domain_only_skips_same_domain_pairs(self):
        recs = [
            ("csharp", rule("csharp.12.a", "集成测试验证真实协作", "集成测试验证真实协作。")),
            ("csharp", rule("csharp.12.b", "集成测试验证真实协作", "集成测试验证真实协作。")),
        ]
        self.assertEqual(find_candidates(recs, 0.0, cross_domain_only=True), [])
        self.assertEqual(len(find_candidates(recs, 0.0, cross_domain_only=False)), 1)

    def test_sorted_by_score_descending(self):
        recs = [
            ("a", rule("a.01.x", "集成测试验证真实协作", "集成测试验证真实协作禁止连生产资源。")),
            ("b", rule("b.01.y", "集成测试验证真实协作", "集成测试验证真实协作禁止连生产资源。")),
            ("c", rule("c.01.z", "面板选型矩阵", "优先 Grid 而非嵌套 StackPanel。")),
        ]
        pairs = find_candidates(recs, 0.0, cross_domain_only=True)
        self.assertEqual([p[0] for p in pairs], sorted([p[0] for p in pairs], reverse=True))

    def test_min_score_filters(self):
        recs = [
            ("a", rule("a.01.x", "面板选型", "优先 Grid。")),
            ("b", rule("b.01.y", "标签命名", "tag 用 v1 格式。")),
        ]
        self.assertEqual(find_candidates(recs, 0.05, cross_domain_only=True), [])


class TestKnownDuplicateRegression(unittest.TestCase):
    """回归 3.0.0 那次人工发现的真实重复：措辞不同、tags 交集为空，靠 summary 词项发现。

    这组数据是当时索引的原文。若评分改动让它们掉出候选，等于回退到人工通读时代。
    """

    QUALITY_GATE = rule(
        "csharp.15.quality-gate-overview", "CI 全绿才可合并，禁止个人绕过门禁",
        "CI 全绿（构建+测试+分析器）才可合并，禁止红灯合并，"
        "门禁配置随仓库提交禁止个人绕过（如 --no-verify）。",
        tags=["ci", "quality-gate"])
    COMMIT_HOOKS = rule(
        "git.02.commit-hooks", "提交前 hook 不得绕过",
        "pre-commit/commit-msg hook 不得用 --no-verify 绕过，"
        "hook 失败须修复根因而非注释掉配置。",
        tags=["git", "hooks"])
    PR_CONVENTIONS = rule(
        "git.03.pr-conventions", "PR 须关联 issue 且 CI 通过才可合并",
        "PR 标题表达变更意图，须关联 issue/需求编号，CI 通过+review 批准才可合并，"
        "禁止红灯合并，禁止把无关改动混进一个 PR。",
        tags=["git", "pull-request"])

    def test_tags_intersection_is_empty(self):
        """前提事实：这些真重复的 tags 交集为空——所以不能用 tags 做候选过滤器。"""
        _, ga = entry_terms(self.QUALITY_GATE)
        _, gb = entry_terms(self.PR_CONVENTIONS)
        self.assertEqual(ga & gb, set())

    def test_quality_gate_vs_commit_hooks_detected(self):
        self.assertGreaterEqual(score(self.QUALITY_GATE, self.COMMIT_HOOKS), 0.10)

    def test_quality_gate_vs_pr_conventions_detected(self):
        self.assertGreaterEqual(score(self.QUALITY_GATE, self.PR_CONVENTIONS), 0.10)


if __name__ == "__main__":
    unittest.main()
