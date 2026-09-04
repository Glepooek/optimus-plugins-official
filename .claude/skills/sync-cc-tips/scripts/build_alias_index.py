#!/usr/bin/env python3
"""从 tips.jsonl 构建「已覆盖标识符集」，供 sync-cc-tips 第二步判重使用。

输出 JSON 到 stdout：{"ids": [...], "aliases": [...], "stats": {...}}

判重基准：一个 changelog 功能点的任意主标识符命中 ids/aliases 即视为已覆盖。
只收录**带语法标记**的标识符（斜杠命令、长短 flag、大写环境变量、反引号内的
settings 键、skill 命名空间），不收裸英文单词——后者会让 aliases 膨胀到数千个
通用词，导致任何功能点都能"命中"，判重恒为已覆盖、新增恒为 0。
"""

import json
import re
import sys

DEFAULT_TIPS = "plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl"

# 带语法标记的标识符模式。每一项都要求存在无法与自然语言混淆的前缀/形态。
PATTERNS = (
    # 斜杠命令，含 /plugin:skill 命名空间。前置断言排除路径分量——
    # `.claude/settings.json` 的 `/settings`、`~/.claude` 的 `/claude`、
    # `github.com/example/repo` 的 `/example` 都不是命令，斜杠命令只出现在
    # 词首或空白/中文标点之后。
    r'(?<![\w./~-])/[a-z][a-z0-9-]*(?::[a-z][a-z0-9-]*)*',
    r'--[a-z][a-z0-9-]*',                       # 长 flag
    r'(?<![\w-])-[a-zA-Z](?![\w-])',            # 短 flag，如 -p -c
    r'\b(?:CLAUDE|CLAUDE_CODE|OTEL|ANTHROPIC|AWS|GOOGLE|DISABLE|MAX)_[A-Z0-9_]+\b',
)


def norm_alias(s):
    """返回一个标识符的等价变体集合。

    别名字面不同时判重会失效（/cost 与 /usage、/review 与 /code-review 等 4 组
    历史重复即因此产生）。这里归一化能覆盖的是**形变**：斜杠前缀、连字符与下划线、
    大小写。语义别名（/undo 与 /rewind 是两个不同词）归一化覆盖不到，需靠
    SEMANTIC_ALIASES 显式登记。
    """
    s = s.strip()
    if not s:
        return set()
    out = {s}
    if s.startswith('/'):
        out.add(s[1:])
    elif s.startswith('--'):
        out.add(s[2:])
    # 连字符 / 下划线互换
    for v in list(out):
        out.add(v.replace('-', '_'))
        out.add(v.replace('_', '-'))
    # 大小写归一：只加小写，不加 upper/title——后两者不会出现在真实标识符里，
    # 只会让集合规模翻三倍并增加误命中面
    out |= {v.lower() for v in out}
    return {v for v in out if v}


# 语义别名：字面无关但指同一功能，归一化覆盖不到，必须显式登记。
# 来源是 known-issues.md 记录的 4 组历史重复，以及后续核对新发现的等价关系。
SEMANTIC_ALIASES = (
    ('/cost', '/usage', '/stats'),
    ('/review', '/code-review'),
    ('/plugin', '/plugins'),
    ('/undo', '/rewind'),
)


def semantic_group(token):
    """token 命中某个语义别名组时，返回该组全部成员；否则返回空集。"""
    t = token.strip().lower()
    for group in SEMANTIC_ALIASES:
        if t in group:
            return set(group)
    return set()


def extract(text):
    """从一段文本中提取全部带语法标记的标识符。"""
    found = set()
    for pat in PATTERNS:
        found.update(re.findall(pat, text))
    return found


def build(path=DEFAULT_TIPS):
    """读 tips.jsonl，返回 (ids, aliases, stats)。"""
    ids, aliases = set(), set()
    entries = 0

    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno} JSON 解析失败: {e}") from e
            entries += 1

            id_ = obj.get('id', '').strip()
            if id_:
                ids.add(id_)
                aliases |= norm_alias(id_)
                aliases |= semantic_group(id_)

            text = f"{obj.get('title', '')}\n{obj.get('body', '')}"
            for token in extract(text):
                aliases |= norm_alias(token)
                aliases |= semantic_group(token)

    stats = {'entries': entries, 'ids': len(ids), 'aliases': len(aliases)}
    return ids, aliases, stats


def main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT_TIPS
    try:
        ids, aliases, stats = build(path)
    except (OSError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    json.dump(
        {'ids': sorted(ids), 'aliases': sorted(aliases), 'stats': stats},
        sys.stdout,
        ensure_ascii=False,
        indent=None,
    )
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
