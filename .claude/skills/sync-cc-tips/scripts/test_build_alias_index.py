"""build_alias_index.py 的单元测试。

覆盖重点是两类静默失效——它们不会报错，只会让判重结果悄悄失真：
1. 通用英文词污染 aliases 集，导致任何功能点都能命中、新增恒为 0；
2. 文件路径分量被误当斜杠命令收录。
"""

import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_alias_index import build, extract, norm_alias, semantic_group


def write_tips(entries):
    """把条目列表写成临时 jsonl，返回路径。调用方负责删除。"""
    fd, path = tempfile.mkstemp(suffix='.jsonl')
    with io.open(fd, 'w', encoding='utf-8') as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    return path


class TestNormAlias(unittest.TestCase):
    def test_slash_prefix_stripped(self):
        out = norm_alias('/code-review')
        self.assertIn('/code-review', out)
        self.assertIn('code-review', out)
        self.assertIn('code_review', out)

    def test_double_dash_prefix_stripped(self):
        out = norm_alias('--add-dir')
        self.assertIn('--add-dir', out)
        self.assertIn('add-dir', out)
        self.assertIn('add_dir', out)

    def test_case_normalized_to_lower_only(self):
        """只加小写变体。upper/title 不出现在真实标识符里，加进去只会扩大误命中面。"""
        out = norm_alias('/Doctor')
        self.assertIn('/doctor', out)
        self.assertNotIn('/DOCTOR', out)
        self.assertNotIn('/Doctor'.upper(), out)

    def test_empty_input(self):
        self.assertEqual(norm_alias(''), set())
        self.assertEqual(norm_alias('   '), set())


class TestSemanticGroup(unittest.TestCase):
    def test_known_alias_group_expands(self):
        """/stats 与 /cost、/usage 是同一功能的别名，字面无关，必须靠显式登记。"""
        self.assertEqual(semantic_group('/stats'), {'/cost', '/usage', '/stats'})
        self.assertEqual(semantic_group('/usage'), {'/cost', '/usage', '/stats'})

    def test_undo_rewind_group(self):
        self.assertEqual(semantic_group('/undo'), {'/undo', '/rewind'})

    def test_unknown_token_returns_empty(self):
        self.assertEqual(semantic_group('/compact'), set())

    def test_case_insensitive_lookup(self):
        self.assertEqual(semantic_group('/COST'), {'/cost', '/usage', '/stats'})


class TestExtractRejectsNoise(unittest.TestCase):
    """回归测试：加固版曾用 r'\\b[a-z][a-zA-Z]{3,}\\b' 收录裸英文词，
    结果 aliases 膨胀到数千个通用词，任何 changelog 功能点都能命中，
    判重恒为已覆盖、新增恒为 0。这是比报错更危险的静默失效。
    """

    def test_plain_english_words_not_extracted(self):
        text = 'This effect happens when used with the function example settings'
        found = extract(text)
        for word in ('effect', 'when', 'with', 'function', 'example', 'This'):
            self.assertNotIn(word, found, f'裸英文词 {word!r} 不应被收录')

    def test_chinese_text_yields_nothing(self):
        self.assertEqual(extract('功能：这是一段没有任何标识符的中文说明'), set())

    def test_path_components_not_treated_as_slash_command(self):
        """`.claude/settings.json` 的 `/settings`、`~/.claude` 的 `/claude`、
        URL 里的 `/example` 都是路径分量，不是斜杠命令。
        """
        cases = (
            ('.claude/settings.json', '/settings'),
            ('~/.claude', '/claude'),
            ('github.com/example/repo', '/example'),
            ('plugins/optimus-devops-plugin/hooks', '/hooks'),
        )
        for text, wrong in cases:
            with self.subTest(text=text):
                self.assertNotIn(wrong, extract(text))

    def test_real_slash_command_extracted(self):
        self.assertIn('/compact', extract('输入 /compact 压缩上下文'))

    def test_slash_command_at_line_start(self):
        self.assertIn('/doctor', extract('/doctor 运行体检'))

    def test_namespaced_skill_extracted(self):
        found = extract('例子：/superpowers:brainstorming 开始头脑风暴')
        self.assertIn('/superpowers:brainstorming', found)

    def test_long_flag_extracted(self):
        self.assertIn('--add-dir', extract('用 --add-dir 追加目录'))

    def test_short_flag_extracted(self):
        self.assertIn('-p', extract('claude -p "查询"'))

    def test_env_var_extracted(self):
        found = extract('设置 CLAUDE_CODE_MAX_OUTPUT_TOKENS 与 OTEL_LOG_USER_PROMPTS')
        self.assertIn('CLAUDE_CODE_MAX_OUTPUT_TOKENS', found)
        self.assertIn('OTEL_LOG_USER_PROMPTS', found)


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.paths = []

    def tearDown(self):
        for p in self.paths:
            try:
                os.unlink(p)
            except OSError:
                pass

    def make(self, entries):
        p = write_tips(entries)
        self.paths.append(p)
        return p

    def test_ids_and_stats(self):
        p = self.make([
            {'id': '/compact-压缩', 'category': '交互', 'title': 't1', 'body': '功能：压缩上下文'},
            {'id': '/doctor-体检', 'category': '交互', 'title': 't2', 'body': '功能：运行体检'},
        ])
        ids, aliases, stats = build(p)
        self.assertEqual(stats['entries'], 2)
        self.assertEqual(ids, {'/compact-压缩', '/doctor-体检'})

    def test_blank_lines_skipped(self):
        p = self.make([{'id': 'a', 'category': 'c', 'title': 't', 'body': 'b'}])
        with io.open(p, 'a', encoding='utf-8') as f:
            f.write('\n   \n')
        _, _, stats = build(p)
        self.assertEqual(stats['entries'], 1)

    def test_malformed_json_raises_with_lineno(self):
        fd, p = tempfile.mkstemp(suffix='.jsonl')
        self.paths.append(p)
        with io.open(fd, 'w', encoding='utf-8') as f:
            f.write('{"id":"ok","category":"c","title":"t","body":"b"}\n')
            f.write('{not json}\n')
        with self.assertRaises(ValueError) as ctx:
            build(p)
        self.assertIn(':2', str(ctx.exception))

    def test_semantic_alias_reaches_aliases_via_body(self):
        """body 里出现 /stats 时，同组的 /cost、/usage 也应进入 aliases，
        这样下次 changelog 提到 /cost 能命中已有的 /stats 条目。
        """
        p = self.make([
            {'id': '/stats-用量', 'category': '交互', 'title': 't', 'body': '功能：查看用量\n例子：/stats'},
        ])
        _, aliases, _ = build(p)
        self.assertIn('/cost', aliases)
        self.assertIn('/usage', aliases)

    def test_missing_file_raises_oserror(self):
        with self.assertRaises(OSError):
            build('no/such/file.jsonl')


if __name__ == '__main__':
    unittest.main(verbosity=2)
