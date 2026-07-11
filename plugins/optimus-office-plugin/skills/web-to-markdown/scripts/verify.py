#!/usr/bin/env python3
"""
核对脚本：对比原文与译文的结构数量

用法：
  python verify.py <raw_file> <out_file>

退出码：
  0  所有差值为零，核对通过
  1  存在差异，需补全后重跑
  2  参数错误或文件不存在
"""

import re
import sys
from pathlib import Path

# 模块级编译
_SEP_RE     = re.compile(r'^\|[\s\-:]+\|[\s\-:|]*\s*$')
_HEADING_RE = re.compile(r'^#{1,6} ')
_LIST_RE    = re.compile(r'^[*\-] ')


def count_structures(path: Path) -> dict:
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"警告：{path.name} 含非 UTF-8 字符，已替换处理", file=sys.stderr)
        text = path.read_text(encoding='utf-8', errors='replace')
    except IsADirectoryError:
        print(f"错误：{path} 是目录而非文件", file=sys.stderr)
        sys.exit(2)

    in_code = False
    counts = dict(headings=0, code_blocks=0, table_rows=0, list_items=0)

    for line in text.splitlines():
        s = line.strip()
        if s.startswith('```'):
            if not in_code:
                counts['code_blocks'] += 1
            in_code = not in_code
            continue
        if in_code:
            continue
        if _HEADING_RE.match(line):
            counts['headings'] += 1
        elif line.startswith('| ') and not _SEP_RE.match(line):
            counts['table_rows'] += 1
        elif _LIST_RE.match(line):
            counts['list_items'] += 1

    return counts


def main():
    if len(sys.argv) != 3:
        print("用法: python verify.py <raw_file> <out_file>", file=sys.stderr)
        sys.exit(2)

    raw_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    for p in (raw_path, out_path):
        if not p.is_file():
            print(f"错误：文件不存在或不是普通文件 — {p}", file=sys.stderr)
            sys.exit(2)

    raw = count_structures(raw_path)
    out = count_structures(out_path)

    labels = {'headings': '标题数', 'code_blocks': '代码块数',
              'table_rows': '表格行数', 'list_items': '列表项数'}
    all_zero = True

    print(f"  {'':2} {'检查项':<8}  {'原文':>5}  {'译文':>5}  {'差值':>5}")
    print('  ' + '-' * 32)
    for key, label in labels.items():
        diff = out[key] - raw[key]
        flag = '✓' if diff == 0 else '✗'
        print(f"  {flag} {label:<8}  {raw[key]:>5}  {out[key]:>5}  {diff:>+5}")
        if diff != 0:
            all_zero = False

    print()
    if all_zero:
        print("核对完整 ✓")
        sys.exit(0)
    else:
        print("存在差异 ✗ — 补全后重跑此脚本")
        sys.exit(1)


if __name__ == '__main__':
    main()
