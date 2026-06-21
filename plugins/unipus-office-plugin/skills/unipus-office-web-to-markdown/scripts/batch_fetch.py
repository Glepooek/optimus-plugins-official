#!/usr/bin/env python3
"""
批量抓取网页并保存为 Markdown 文件的辅助脚本

本脚本只负责解析 URL 列表文件，输出任务 JSON，不创建目录或写入文件。
目录创建由调用方（skill 执行流程）负责。
"""

import json
import sys
from pathlib import Path, PurePosixPath


DEFAULT_DIR = "docs"


def sanitize_dir(raw: str, line_num: int) -> str | None:
    """
    校验并规范化目录路径：
    - 空值 → 警告并回退到默认值
    - 包含 .. 路径遍历 → 警告并跳过该声明
    - 统一使用正斜杠，去掉末尾斜杠
    """
    path = raw.strip().replace('\\', '/')
    if not path:
        print(f"警告: 第 {line_num} 行目录声明为空，使用默认目录 '{DEFAULT_DIR}'", file=sys.stderr)
        return None
    try:
        resolved = PurePosixPath(path)
        if '..' in resolved.parts:
            print(f"警告: 第 {line_num} 行目录含路径遍历字符 '..'，已忽略该声明: {raw}", file=sys.stderr)
            return None
    except Exception:
        print(f"警告: 第 {line_num} 行目录路径无效，已忽略: {raw}", file=sys.stderr)
        return None
    return path.rstrip('/')


def parse_url_list(file_path: str) -> list[dict]:
    """
    解析 URL 列表文件

    格式:
        # 目标目录（完整路径，含 docs/ 前缀）
        URL [文件名.md]   （文件名可省略）
    """
    urls = []
    current_dir = DEFAULT_DIR
    seen_urls = set()

    try:
        f = open(file_path, 'r', encoding='utf-8-sig')
    except UnicodeDecodeError:
        print("警告：文件含非 UTF-8 字符，尝试 latin-1 编码读取", file=sys.stderr)
        f = open(file_path, 'r', encoding='latin-1')

    with f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            if line.startswith('#'):
                declared = sanitize_dir(line[1:], line_num)
                if declared is not None:
                    current_dir = declared
                continue

            parts = line.split(maxsplit=1)
            url = parts[0]

            if not url.startswith('http'):
                print(f"警告: 第 {line_num} 行 URL 格式错误，已跳过: {line}", file=sys.stderr)
                continue

            filename = None
            if len(parts) == 2:
                filename = parts[1].strip()
                if not filename.endswith('.md'):
                    filename += '.md'

            if url in seen_urls:
                print(f"警告: 第 {line_num} 行 URL 重复，已跳过: {url}", file=sys.stderr)
                continue
            seen_urls.add(url)

            urls.append({'url': url, 'filename': filename, 'dir': current_dir})

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

    if not urls:
        print("警告: 未解析到任何有效 URL，请检查文件内容", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(urls, ensure_ascii=False, indent=2))
    print(f"\n共 {len(urls)} 个 URL 待处理", file=sys.stderr)


if __name__ == '__main__':
    main()
