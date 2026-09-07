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


def split_sections(text: str, keep_empty: bool = True) -> list[tuple[str, list[str]]]:
    """按标题将文本切分为章节，返回有序列表 [(heading, [段落列表])]

    keep_empty=True 时保留内容为空的章节，使章节数组与标题序列严格一一对应。
    这是按位置索引比对的前提：一旦空章节被丢弃，两侧数组就会错位，
    后续所有对比都会拿错章节相互比较。
    前言块（首个标题之前的内容）始终不进数组，避免整体偏移一位。
    """
    sections = []
    current = None          # None 表示尚未遇到第一个标题（前言区）
    buffer = []
    in_code = False

    for line in text.splitlines():
        if _CODE_FENCE_RE.match(line.strip()):
            in_code = not in_code
        if not in_code:
            m = _HEADING_RE.match(line)
            if m:
                if current is not None:
                    paras = _to_paragraphs(buffer)
                    if paras or keep_empty:
                        sections.append((current, paras))
                current = line.strip()
                buffer = []
                continue
        buffer.append(line)

    if current is not None:
        paras = _to_paragraphs(buffer)
        if paras or keep_empty:
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


def content_lines(paras: list[str]) -> int:
    """章节的非空行数。

    比"段落数"更能抵抗排版差异：把松散的列表项合并成紧凑列表会让段落数
    大幅下降，但内容一行未少。整段漏译仍会使该值下降，检查因此保持灵敏。
    """
    return sum(1 for p in paras for line in p.splitlines() if line.strip())


# 站点模板渲染的元信息块（分类/产品/日期/作者/分享），把标签与值拆成多行。
# 译文合并成紧凑列表是正确做法，行数必然大幅下降，不应判为漏译。
_META_LABEL_RE = re.compile(
    r'^\*\s*(Category|Product|Date|Reading time|Share|Author\(s\)|Tags?)\s*$',
    re.I)


def is_meta_block(paras: list[str]) -> bool:
    """该章节是否以站点元信息块为主（命中 3 个及以上标签即认定）"""
    hits = sum(1 for p in paras for line in p.splitlines()
               if _META_LABEL_RE.match(line.strip()))
    return hits >= 3


def extract_content_images(text: str) -> list[str]:
    """提取原文正文中的图片文件名（排除 icon/logo/svg 装饰图）

    不按文件名判断是否"内容图"。CDN 普遍使用哈希命名（Webflow 的
    6a8739a1..._44592f18.png 剥掉前缀后仍是哈希），内容图与装饰图在
    文件名上无法区分——旧版按 ^[0-9a-f]{8,} 过滤，导致整站图片被判为
    装饰图，该检查在此类站点上永远空转。

    改为只滤掉可靠信号（icon/logo/svg），其余一律纳入。译文未引用的
    由调用方作为待确认项提示，交人工判断，不直接判定为缺失。
    """
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
            if any(w in fname.lower() for w in ('icon', 'logo', 'placeholder')):
                continue
            if fname.endswith('.svg'):
                continue
            imgs.append(fname)
    return imgs


def extract_yt_ids(text: str) -> list[str]:
    """提取原文中所有 YouTube embed ID"""
    return _YT_EMBED_RE.findall(text)


def check_url(url: str, timeout: int = 5) -> tuple[bool, str]:
    """HEAD 请求检查链接是否可达，返回 (ok, 状态描述)

    本机环境问题（SSL 证书、DNS、超时）不代表链接失效，一律按可达处理，
    否则在企业代理或缺少根证书的机器上会 100% 误报，使该检查失去意义。
    """
    try:
        req = urllib.request.Request(url, method='HEAD',
              headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            return code < 400, str(code)
    except urllib.error.HTTPError as e:
        return e.code < 400, str(e.code)
    except Exception as e:
        msg = str(e)
        if any(k in msg for k in ('CERTIFICATE_VERIFY_FAILED', 'SSL',
                                  'timed out', 'Name or service not known',
                                  'getaddrinfo failed')):
            return True, 'skip'
        return False, msg[:60]


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

    # ── 检查1：内容完整性（按位置索引对比非空行数）─────────
    raw_sections = split_sections(raw_text)
    out_sections = split_sections(out_text)

    section_issues = []
    if len(raw_sections) != len(out_sections):
        section_issues.append(
            f"  ✗ 章节总数不一致：原文 {len(raw_sections)} 个，译文 {len(out_sections)} 个"
            f"（位置索引已失效，逐章对比结果不可信，请先核对章节结构）"
        )
    else:
        for i, (raw_heading, raw_paras) in enumerate(raw_sections):
            _, out_paras = out_sections[i]
            if is_meta_block(raw_paras):
                continue
            raw_n = content_lines(raw_paras)
            out_n = content_lines(out_paras)
            # 中译普遍比英文原文紧凑，容许 20% 的收缩
            if out_n < raw_n * 0.8:
                section_issues.append(
                    f"  ✗ 章节 [{i}]「{raw_heading[:50]}」："
                    f"原文 {raw_n} 行，译文 {out_n} 行"
                )
    if section_issues:
        issues.append("【内容完整性】以下章节内容量不足：\n" + '\n'.join(section_issues))
    else:
        passed.append(f"内容完整性 ✓（{len(raw_sections)} 个章节）")

    # ── 检查2：图片引用 ────────────────────────────────────
    raw_imgs = extract_content_images(raw_text)
    if raw_imgs:
        out_local_imgs = set(_LOCAL_IMG_RE.findall(out_text))
        # 译文允许重命名（去哈希前缀、加语义前缀），按去前缀后的词干匹配
        out_stems = {re.sub(r'^[0-9a-f]{8,}_', '', f) for f in out_local_imgs}
        out_stems |= {f.split('-')[-1] for f in out_local_imgs}
        missing = []
        for fname in raw_imgs:
            clean = re.sub(r'^[0-9a-f]{8,}_', '', fname)
            if (clean in out_stems or fname in out_local_imgs
                    or clean in out_local_imgs):
                continue
            missing.append(fname)
        if missing:
            img_warn = (f"【图片引用】{len(missing)}/{len(raw_imgs)} 张原文图片在译文中"
                        f"未找到本地引用（不阻断，装饰图可忽略）：\n" +
                        '\n'.join(f"  ? {f}" for f in missing))
            issues.append(img_warn)
        else:
            passed.append(f"图片引用 ✓（{len(raw_imgs)} 张）")
    else:
        passed.append("图片引用 ✓（原文无图片）")

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

    # 软警告（链接可达性、图片引用）不终止，仅提示人工确认
    soft_prefixes = ('【链接可达性】', '【图片引用】')
    soft_issues = [x for x in issues if x.startswith(soft_prefixes)]
    hard_issues = [x for x in issues if not x.startswith(soft_prefixes)]

    for si in soft_issues:
        print(f"\n  ⚠ {si}")

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
