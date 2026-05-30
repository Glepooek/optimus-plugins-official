#!/usr/bin/env python3
"""
批量抓取网页并保存为 Markdown 文件的辅助脚本
"""

import json
import sys


def parse_url_list(file_path: str) -> list[dict]:
    """
    解析 URL 列表文件

    格式:
        # 目标目录（完整路径，含 docs/ 前缀）
        URL [文件名.md]   （文件名可省略）
    """
    urls = []
    current_dir = "docs"  # 默认目录
    seen_urls = set()

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            if line.startswith('#'):
                current_dir = line[1:].strip()
                continue

            parts = line.split(maxsplit=1)

            if len(parts) == 1:
                url = parts[0]
                if not url.startswith('http'):
                    print(f"警告: 第 {line_num} 行格式错误，已跳过: {line}", file=sys.stderr)
                    continue
                filename = None
            else:
                url, filename = parts
                if not url.startswith('http'):
                    print(f"警告: 第 {line_num} 行 URL 格式错误，已跳过: {line}", file=sys.stderr)
                    continue
                if not filename.endswith('.md'):
                    filename = filename + '.md'

            # URL 去重
            if url in seen_urls:
                print(f"警告: 第 {line_num} 行 URL 重复，已跳过: {url}", file=sys.stderr)
                continue
            seen_urls.add(url)

            urls.append({
                'url': url,
                'filename': filename,
                'dir': current_dir,
            })

    return urls


def main():
    if len(sys.argv) < 2:
        print("用法: python batch_fetch.py <url_list_file>")
        print("URL 列表格式:")
        print("  # 目标目录（如 docs/kiro）")
        print("  URL [文件名.md]")
        sys.exit(1)

    url_file = sys.argv[1]

    try:
        urls = parse_url_list(url_file)
    except FileNotFoundError:
        print(f"错误: 文件不存在，请确认路径是否正确: {url_file}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(urls, ensure_ascii=False, indent=2))
    print(f"\n共 {len(urls)} 个 URL 待处理", file=sys.stderr)


if __name__ == '__main__':
    main()
