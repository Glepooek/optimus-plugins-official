"""detect_residue.py 的单元测试。

覆盖重点是原内联版的两个致命缺陷：
1. `items = []` 从未被填充，两层循环永不执行，残影检测形同不存在；
2. 中文按连续片段整取，`是完整的配置体检工具` 成为单个 token，
   与另一条的 `设置体检` 永不重合，真残影召回率为 0。
"""

import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detect_residue import (
    OVERLAP_THRESHOLD,
    detect,
    feature_terms,
    main_identifier,
    overlap_ratio,
)


class TestMainIdentifier(unittest.TestCase):
    def test_slash_command_prefix(self):
        self.assertEqual(main_identifier('/code-review-审查当前改动'), '/code-review')

    def test_ascii_phrase_prefix(self):
        self.assertEqual(main_identifier('requesting-code-review-请求代码审查'),
                         'requesting-code-review')

    def test_camel_case_lowered(self):
        self.assertEqual(main_identifier('defaultMode-权限模式'), 'defaultmode')

    def test_pure_chinese_id(self):
        """无 ASCII 前缀时退回整个 id，避免返回空串把所有中文 id 归成一组。"""
        self.assertEqual(main_identifier('插件配置安全加固'), '插件配置安全加固')

    def test_differing_prefixes_are_different_groups(self):
        """三条 /code-review 相关条目 id 前缀不同，不应归入同一主标识符组。"""
        a = main_identifier('/code-review-审查当前改动')
        b = main_identifier('requesting-code-review-请求代码审查')
        c = main_identifier('receiving-code-review-接收代码审查')
        self.assertNotEqual(a, b)
        self.assertNotEqual(b, c)


class TestFeatureTerms(unittest.TestCase):
    def test_chinese_split_into_bigrams(self):
        """回归测试：整取会让 `配置体检` 成为单 token，bigram 才能跨断句匹配。"""
        terms = feature_terms('功能：配置体检')
        self.assertIn('配置', terms)
        self.assertIn('置体', terms)
        self.assertIn('体检', terms)
        self.assertNotIn('配置体检', terms)

    def test_differing_phrasing_shares_bigrams(self):
        """不同断句讲同一件事，bigram 集合应有交集——这是召回真残影的前提。"""
        a = feature_terms('功能：是完整的配置体检工具')
        b = feature_terms('功能：运行一次设置体检')
        self.assertTrue(a & b, '相同语义的不同表述应共享 bigram')
        self.assertIn('体检', a & b)

    def test_only_feature_section_used(self):
        """只取 `功能：` 段，`效果：`/`例子：` 的词不参与——后两段常含重复措辞。"""
        terms = feature_terms('功能：压缩上下文\n效果：节省预算\n例子：/compact')
        self.assertIn('压缩', terms)
        self.assertNotIn('节省', terms)

    def test_falls_back_to_whole_body_without_marker(self):
        terms = feature_terms('没有功能标记的纯说明文本')
        self.assertTrue(terms)

    def test_english_identifiers_kept(self):
        terms = feature_terms('功能：设置 defaultMode 为 acceptEdits')
        self.assertIn('defaultmode', terms)
        self.assertIn('acceptedits', terms)


class TestOverlapRatio(unittest.TestCase):
    def test_full_containment(self):
        self.assertEqual(overlap_ratio({'a', 'b', 'c'}, {'a', 'b'}), 1.0)

    def test_partial(self):
        self.assertAlmostEqual(overlap_ratio({'a', 'b'}, {'a', 'c'}), 0.5)

    def test_empty_divisor_returns_zero(self):
        """b 为空时不能除零，也不能算作"完全覆盖"。"""
        self.assertEqual(overlap_ratio({'a'}, set()), 0.0)

    def test_no_overlap(self):
        self.assertEqual(overlap_ratio({'a'}, {'b'}), 0.0)


class TestDetect(unittest.TestCase):
    def setUp(self):
        self.paths = []

    def tearDown(self):
        for p in self.paths:
            try:
                os.unlink(p)
            except OSError:
                pass

    def make(self, entries):
        fd, path = tempfile.mkstemp(suffix='.jsonl')
        with io.open(fd, 'w', encoding='utf-8') as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + '\n')
        self.paths.append(path)
        return path

    def test_loop_actually_runs(self):
        """回归测试：内联版 `items = []` 从未填充，循环永不执行，
        候选恒为 0。这里给两条必然构成覆盖的条目，候选必须 > 0。
        """
        p = self.make([
            {'id': '/doctor-详版', 'category': 'c', 'title': 't',
             'body': '功能：运行配置体检并诊断修复问题，检查安装健康与未使用插件'},
            {'id': '/doctor-简版', 'category': 'c', 'title': 't',
             'body': '功能：运行配置体检'},
        ])
        candidates, _, stats = detect(p)
        self.assertGreater(stats['candidates'], 0, '循环未执行或阈值过高')
        self.assertEqual(candidates[0]['covers'], '/doctor-详版')
        self.assertEqual(candidates[0]['covered'], '/doctor-简版')

    def test_different_main_identifier_not_paired(self):
        """主标识符不同的条目即使措辞相近也不配对——条件 1 是硬门。"""
        p = self.make([
            {'id': '/compact-压缩', 'category': 'c', 'title': 't', 'body': '功能：运行配置体检'},
            {'id': '/doctor-体检', 'category': 'c', 'title': 't', 'body': '功能：运行配置体检'},
        ])
        _, _, stats = detect(p)
        self.assertEqual(stats['candidates'], 0)

    def test_same_main_but_disjoint_features_not_paired(self):
        """主标识符相同但功能互不覆盖，不应召回——这保护了
        requesting/receiving-code-review 这类同命令不同侧面的条目。
        """
        p = self.make([
            {'id': 'MCP-服务器', 'category': 'c', 'title': 't',
             'body': '功能：配置服务器连接地址与传输协议'},
            {'id': 'MCP-资源读取', 'category': 'c', 'title': 't',
             'body': '功能：列出并读取远端暴露的文档条目'},
        ])
        _, _, stats = detect(p)
        self.assertEqual(stats['candidates'], 0)

    def test_shorter_entry_cannot_cover_longer(self):
        """更简短者不可能"完全覆盖"更详尽者，方向必须单向。"""
        p = self.make([
            {'id': '/x-详版', 'category': 'c', 'title': 't',
             'body': '功能：压缩上下文并保留关键信息与近期消息'},
            {'id': '/x-简版', 'category': 'c', 'title': 't', 'body': '功能：压缩上下文'},
        ])
        candidates, _, _ = detect(p)
        for c in candidates:
            self.assertNotEqual(c['covers'], '/x-简版',
                                '简短条目不应被判为覆盖方')

    def test_shared_main_groups_reported(self):
        """分组按 id 的 ASCII 前缀。真实 id 形如 `MCP-服务器`（ASCII + 中文后缀），
        故 `MCP-a` 这类纯 ASCII id 的 `-a` 也算前缀的一部分，不会与 `MCP-b` 同组。
        """
        p = self.make([
            {'id': 'MCP-服务器', 'category': 'c', 'title': 't', 'body': '功能：甲'},
            {'id': 'MCP-资源读取', 'category': 'c', 'title': 't', 'body': '功能：乙'},
            {'id': '/solo-独立', 'category': 'c', 'title': 't', 'body': '功能：丙'},
        ])
        _, multi, stats = detect(p)
        self.assertEqual(stats['shared_main_groups'], 1)
        self.assertIn('mcp', multi)
        self.assertEqual(sorted(multi['mcp']), ['MCP-服务器', 'MCP-资源读取'])

    def test_pure_ascii_ids_group_separately(self):
        """纯 ASCII id 的尾段属于前缀，不同尾段即不同组——避免把
        `agent-配置` 与 `agent-指定代理` 之外的无关条目误并。
        """
        p = self.make([
            {'id': 'MCP-a', 'category': 'c', 'title': 't', 'body': '功能：甲'},
            {'id': 'MCP-b', 'category': 'c', 'title': 't', 'body': '功能：乙'},
        ])
        _, _, stats = detect(p)
        self.assertEqual(stats['shared_main_groups'], 0)

    def test_entry_without_id_skipped(self):
        p = self.make([
            {'id': '', 'category': 'c', 'title': 't', 'body': '功能：无 id'},
            {'id': '/ok-正常', 'category': 'c', 'title': 't', 'body': '功能：正常'},
        ])
        _, _, stats = detect(p)
        self.assertEqual(stats['entries'], 1)

    def test_malformed_json_raises_with_lineno(self):
        fd, p = tempfile.mkstemp(suffix='.jsonl')
        self.paths.append(p)
        with io.open(fd, 'w', encoding='utf-8') as f:
            f.write('{"id":"ok","category":"c","title":"t","body":"b"}\n')
            f.write('broken\n')
        with self.assertRaises(ValueError) as ctx:
            detect(p)
        self.assertIn(':2', str(ctx.exception))

    def test_threshold_is_recall_oriented(self):
        """阈值定位是召回而非判定，故不应设得过高——实测真残影只有 0.263。"""
        self.assertLessEqual(OVERLAP_THRESHOLD, 0.3)

    def test_missing_file_raises_oserror(self):
        with self.assertRaises(OSError):
            detect('no/such/file.jsonl')


if __name__ == '__main__':
    unittest.main(verbosity=2)
