#!/usr/bin/env python3
"""
第二轮内容质量核对：段落完整性、图片引用、链接可达性、视频保留

用法：
  python verify_quality.py <raw_file> <out_file> [--base-url <BASE_URL>]

  --base-url  站内相对链接的 URL 前缀，用于补全链接后再校验可达性
              省略时只校验译文中已有的完整 http 链接

退出码：
  0  所有检查通过
  1  存在问题，需补全修正后重跑
  2  参数错误或文件不存在
"""

import re
import sys
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from collections import defaultdict  # noqa: F401 (保留备用)

# ── 正则（模块级编译）────────────────────────────────────
_HEADING_RE    = re.compile(r'^(#{1,6}) (.+)')
_IMG_SRC_RE    = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)
_MD_IMG_RE     = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
_MD_LINK_RE    = re.compile(r'\]\((https?://[^)#\s]+)\)')
_YT_EMBED_RE   = re.compile(r'youtube\.com/embed/([A-Za-z0-9_\-]+)')
_YT_WATCH_RE   = re.compile(r'youtube\.com/watch\?v=([A-Za-z0-9_\-]+)')
_LOCAL_IMG_RE  = re.compile(r'!\[[^\]]*\]\(\.\./assets/([^)]+)\)')
_CODE_FENCE_RE = re.compile(r'^```')


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"警告：{path.name} 含非 UTF-8 字符，已替换处理", file=sys.stderr)
        return path.read_text(encoding='utf-8', errors='replace')


def split_sections(text: str) -> list[tuple[str, list[str]]]:
    """按标题将文本切分为章节，返回有序列表 [(heading, [段落列表])]"""
    sections = []
    current = '__preamble__'
    buffer = []
    in_code = False

    for line in text.splitlines():
        if _CODE_FENCE_RE.match(line.strip()):
            in_code = not in_code
        if not in_code:
            m = _HEADING_RE.match(line)
            if m:
                paras = _to_paragraphs(buffer)
                if paras:
                    sections.append((current, paras))
                current = line.strip()
                buffer = []
                continue
        buffer.append(line)

    paras = _to_paragraphs(buffer)
    if paras:
        sections.append((current, paras))
    return sections


def _to_paragraphs(lines: list[str]) -> list[str]:
    """将行列表按空行分割成段落列表，去掉空段落"""
    paras, cur = [], []
    for line in lines:
        if line.strip():
            cur.append(line)
        else:
            if cur:
                paras.append('\n'.join(cur))
                cur = []
    if cur:
        paras.append('\n'.join(cur))
    return paras


def extract_content_images(text: str) -> list[str]:
    """提取原文中的内容图片文件名（排除纯哈希、icon/logo/svg）"""
    imgs = []
    in_code = False
    for line in text.splitlines():
        if _CODE_FENCE_RE.match(line.strip()):
            in_code = not in_code
            continue
        if in_code:
            continue
        for src in _IMG_SRC_RE.findall(line) + _MD_IMG_RE.findall(line):
            fname = src.split('/')[-1].split('?')[0]
            # 跳过装饰图标
            if re.match(r'^[0-9a-f]{8,}', fname):
                continue
            if any(w in fname.lower() for w in ('icon', 'logo')):
                continue
            if fname.endswith('.svg'):
                continue
            imgs.append(fname)
    return imgs


def extract_yt_ids(text: str) -> list[str]:
    """提取原文中所有 YouTube embed ID"""
    return _YT_EMBED_RE.findall(text)


def check_url(url: str, timeout: int = 5) -> tuple[bool, str]:
    """HEAD 请求检查链接是否可达，返回 (ok, 状态描述)"""
    try:
        req = urllib.request.Request(url, method='HEAD',
              headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            return code < 400, str(code)
    except urllib.error.HTTPError as e:
        return e.code < 400, str(e.code)
    except Exception as e:
        return False, str(e)[:60]


def main():
    parser = argparse.ArgumentParser(description='第二轮内容质量核对')
    parser.add_argument('raw_file', help='原文临时文件')
    parser.add_argument('out_file', help='译文目标文件')
    parser.add_argument('--base-url', dest='base_url',
                        help='站内相对链接的 URL 前缀')
    parsed = parser.parse_args()

    raw_path = Path(parsed.raw_file)
    out_path = Path(parsed.out_file)
    for p in (raw_path, out_path):
        if not p.is_file():
            print(f"错误：文件不存在或不是普通文件 — {p}", file=sys.stderr)
            sys.exit(2)

    raw_text = read_file(raw_path)
    out_text = read_file(out_path)
    base_url = (parsed.base_url or '').rstrip('/')

    issues = []
    passed = []

    # ── 检查1：段落完整性（按位置顺序对比，不依赖标题文字）───
    raw_sections = split_sections(raw_text)
    out_sections = split_sections(out_text)

    section_issues = []
    for i, (raw_heading, raw_paras) in enumerate(raw_sections):
        if raw_heading == '__preamble__':
            continue
        if i >= len(out_sections):
            section_issues.append(f"  ✗ 章节 [{i}]「{raw_heading[:50]}」：译文中找不到对应章节")
            continue
        _, out_paras = out_sections[i]
        if len(out_paras) < len(raw_paras):
            section_issues.append(
                f"  ✗ 章节 [{i}]「{raw_heading[:50]}」：原文 {len(raw_paras)} 段，译文 {len(out_paras)} 段"
            )
    if section_issues:
        issues.append("【段落完整性】以下章节段落数不足：\n" + '\n'.join(section_issues))
    else:
        passed.append("段落完整性 ✓")

    # ── 检查2：图片引用 ────────────────────────────────────
    raw_imgs = extract_content_images(raw_text)
    if raw_imgs:
        out_local_imgs = set(_LOCAL_IMG_RE.findall(out_text))
        missing = []
        for fname in raw_imgs:
            # 去掉哈希前缀后匹配
            clean = re.sub(r'^[0-9a-f]{8,}_', '', fname)
            if clean not in out_local_imgs and fname not in out_local_imgs:
                missing.append(fname)
        if missing:
            issues.append("【图片引用】以下原文图片在译文中未找到本地引用：\n" +
                          '\n'.join(f"  ✗ {f}" for f in missing))
        else:
            passed.append(f"图片引用 ✓（{len(raw_imgs)} 张）")
    else:
        passed.append("图片引用 ✓（原文无内容图片）")

    # ── 检查3：链接可达性 ──────────────────────────────────
    links = _MD_LINK_RE.findall(out_text)
    # 补全站内链接
    if base_url:
        rel_links = re.findall(r'\]\((/[a-zA-Z][^)#\s]*)\)', out_text)
        links += [base_url + l for l in rel_links]
    links = list(dict.fromkeys(links))  # 去重保序

    link_failures = []
    for url in links:
        ok, status = check_url(url)
        if not ok:
            link_failures.append(f"  ✗ {status}  {url}")

    if link_failures:
        issues.append(f"【链接可达性】{len(link_failures)}/{len(links)} 个链接不可达（不阻断，供人工确认）：\n" +
                      '\n'.join(link_failures))
    else:
        passed.append(f"链接可达性 ✓（{len(links)} 个）")

    # ── 检查4：视频保留 ────────────────────────────────────
    yt_ids = extract_yt_ids(raw_text)
    if yt_ids:
        out_yt_ids = set(_YT_WATCH_RE.findall(out_text))
        missing_yt = [vid for vid in yt_ids if vid not in out_yt_ids]
        if missing_yt:
            issues.append("【视频保留】以下 YouTube 视频在译文中未找到 watch?v= 链接：\n" +
                          '\n'.join(f"  ✗ https://www.youtube.com/watch?v={v}" for v in missing_yt))
        else:
            passed.append(f"视频保留 ✓（{len(yt_ids)} 个）")
    else:
        passed.append("视频保留 ✓（原文无 YouTube 视频）")

    # ── 输出结果 ───────────────────────────────────────────
    print(f"\n第二轮核对结果：")
    for p in passed:
        print(f"  ✓ {p}")

    # 链接问题单独提示（不终止，仅警告）
    link_issue = next((x for x in issues if x.startswith('【链接可达性】')), None)
    hard_issues = [x for x in issues if not x.startswith('【链接可达性】')]

    if link_issue:
        print(f"\n  ⚠ {link_issue}")

    if hard_issues:
        print("\n需要修正的问题：")
        for iss in hard_issues:
            print(f"\n{iss}")
        print("\n内容质量核对未通过 ✗ — 补全修正后重跑此脚本")
        sys.exit(1)
    else:
        print("\n内容质量核对通过 ✓")
        sys.exit(0)


if __name__ == '__main__':
    main()
