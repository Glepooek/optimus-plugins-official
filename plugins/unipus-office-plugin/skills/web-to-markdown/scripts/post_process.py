#!/usr/bin/env python3
"""
后处理脚本：修复站内相对链接 + 表格分隔行格式

用法：
  python post_process.py <out_file> [--base-url <BASE_URL>]

  --base-url  站内相对链接的 URL 前缀，如 https://code.claude.com/docs
              省略时只修复表格，不修改链接

退出码：0 成功，1 失败
"""

import re
import sys
import argparse
from pathlib import Path

# 模块级编译，避免重复编译
_LINK_RE = re.compile(r'\((/[a-zA-Z][^)#\s]*)\)')
_SEP_RE  = re.compile(r'^\|[\s\-:]+\|[\s\-:|]*\s*$')
_CELL_RE = re.compile(r'^:?-{2,}:?$')


def process(content: str, base_url: str | None) -> tuple[str, int, int]:
    """
    单次遍历处理链接补全和表格修复，代码块内跳过。
    返回 (处理后内容, 链接修复数, 表格行修复数)
    """
    link_count = 0
    table_count = 0
    out_lines = []
    in_code = False

    for line in content.splitlines(keepends=True):
        stripped = line.strip()

        # 代码块边界（支持带语言标记的 ```bash 等）
        if stripped.startswith('```'):
            in_code = not in_code
            out_lines.append(line)
            continue

        if in_code:
            out_lines.append(line)
            continue

        # 链接补全（快速预判减少正则调用）
        if base_url and '](/' in line:
            def _repl(m, _base=base_url):
                nonlocal link_count
                link_count += 1
                return f'({_base}{m.group(1)})'
            line = _LINK_RE.sub(_repl, line)

        # 表格分隔行修复
        if _SEP_RE.match(line.rstrip()):
            parts = line.split('|')
            new_parts = []
            changed = False
            for p in parts:
                if _CELL_RE.match(p.strip()):
                    new_parts.append(' :--- ')
                    changed = changed or p.strip() != ':---'
                else:
                    new_parts.append(p)
            if changed:
                table_count += 1
                eol = line[len(line.rstrip()):]
                line = '|'.join(new_parts).rstrip() + eol

        out_lines.append(line)

    return ''.join(out_lines), link_count, table_count


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"警告：文件含非 UTF-8 字符，已替换处理", file=sys.stderr)
        return path.read_text(encoding='utf-8', errors='replace')


def main():
    parser = argparse.ArgumentParser(description='Markdown 后处理：链接补全 + 表格格式修复')
    parser.add_argument('out_file', help='目标 Markdown 文件路径')
    parser.add_argument('--base-url', dest='base_url',
                        help='站内相对链接的 URL 前缀，如 https://code.claude.com/docs')
    parsed = parser.parse_args()

    path = Path(parsed.out_file)
    if not path.is_file():
        print(f"错误：文件不存在或不是普通文件 — {path}", file=sys.stderr)
        sys.exit(1)

    content = read_file(path)
    base_url = parsed.base_url.rstrip('/') if parsed.base_url else None
    content, link_count, table_count = process(content, base_url)
    path.write_text(content, encoding='utf-8')

    print(f"链接修复：{link_count} 处" if base_url else "链接修复：跳过")
    print(f"表格修复：{table_count} 行")
    print("后处理完成 ✓")


if __name__ == '__main__':
    main()
