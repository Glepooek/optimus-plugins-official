#!/usr/bin/env python3
"""
fetch_webpage_api.py — 抓取网页或 Markdown 文件中的 API 接口信息

用法：
  python fetch_webpage_api.py <url> [选项]

支持格式：
  - HTML 页面（Confluence、Wiki 等）
  - Markdown 文件（.md / .markdown，含直链 Markdown 文本）

认证方式（三选一）：
  --cookie "JSESSIONID=abc123; ..."   直接传 Cookie 字符串
  --cookie-file cookies.txt            从文件读取 Cookie（Netscape 格式或 key=value 行）
  --basic-auth user:pass               HTTP Basic Auth

示例：
  # Markdown 文档直链
  python fetch_webpage_api.py "https://example.com/ai/doc/API-Documentation.md" --output api.md

  # Confluence 页面（需登录）
  python fetch_webpage_api.py "https://confluence.example.com/pages/viewpage.action?pageId=123" \\
      --cookie "JSESSIONID=xxx; confluence.list.pages.cookie=yyy" \\
      --output zt-api.md

  # 不需要登录的普通页面
  python fetch_webpage_api.py "https://example.com/api-docs" --output api.md

  # 使用 curl 导出的 cookie 文件
  python fetch_webpage_api.py <url> --cookie-file ~/cookies.txt
"""

import argparse
import http.cookiejar
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    missing = str(e).split("'")[-2] if "'" in str(e) else str(e)
    print(f"缺少依赖：{missing}，请先安装：pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────────────────────
# Markdown 检测与解析
# ──────────────────────────────────────────────────────────────

def is_markdown_url(url: str) -> bool:
    """判断 URL 是否指向 Markdown 文件。"""
    path = urlparse(url).path.lower()
    return path.endswith(".md") or path.endswith(".markdown")


def is_markdown_content(text: str, content_type: str = "") -> bool:
    """判断响应内容是否为 Markdown（通过 Content-Type 或内容特征）。"""
    if "markdown" in content_type.lower() or "text/plain" in content_type.lower():
        # text/plain 时进一步通过内容特征判断
        pass
    md_indicators = ["# ", "## ", "```", "**", "| --- |", "- [ ]"]
    matched = sum(1 for sig in md_indicators if sig in text)
    return matched >= 2


def extract_api_from_markdown(text: str, source_url: str) -> dict:
    """
    从 Markdown 文本中提取 API 接口信息。
    识别以下模式：
      - `METHOD /path` 或 **METHOD** /path 在标题/正文中
      - 代码块（curl、JSON 示例）
      - 表格（Markdown 表格）
    """
    result = {
        "title": "",
        "source_url": source_url,
        "apis": [],
        "raw_tables": [],
        "raw_code_blocks": [],
    }

    lines = text.splitlines()

    # 页面标题（第一个 # 标题）
    for line in lines:
        if line.startswith("# "):
            result["title"] = line[2:].strip()
            break

    # ── 1. 代码块
    in_code = False
    code_buf = []
    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                block = "\n".join(code_buf).strip()
                if block:
                    result["raw_code_blocks"].append(block)
                code_buf = []
                in_code = False
            else:
                in_code = True
        elif in_code:
            code_buf.append(line)

    # ── 2. Markdown 表格
    table_buf = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_buf.append(stripped)
        else:
            if len(table_buf) >= 2:
                result["raw_tables"].append("\n".join(table_buf))
            table_buf = []
    if len(table_buf) >= 2:
        result["raw_tables"].append("\n".join(table_buf))

    # ── 3. 识别接口条目
    http_method_pattern = re.compile(
        r'`?(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)`?\s+([/`\w\-\.\{\}:?=&%]+)',
        re.IGNORECASE
    )
    seen = set()

    # 按标题分节，关联接口描述
    current_section = ""
    for line in lines:
        if re.match(r'^#{1,4} ', line):
            current_section = line.lstrip("#").strip()

        for m in http_method_pattern.finditer(line):
            method = m.group(1).upper()
            path = m.group(2).strip("`")
            key = f"{method} {path}"
            if key not in seen:
                seen.add(key)
                result["apis"].append({
                    "method": method,
                    "path": path,
                    "description": current_section,
                })

    return result


# ──────────────────────────────────────────────────────────────
# HTTP 工具
# ──────────────────────────────────────────────────────────────

def build_session(cookie_str: str | None, cookie_file: str | None, basic_auth: str | None) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })

    if cookie_str:
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                session.cookies.set(k.strip(), v.strip())

    if cookie_file:
        path = Path(cookie_file)
        if not path.exists():
            print(f"[警告] Cookie 文件不存在：{cookie_file}", file=sys.stderr)
        else:
            jar = http.cookiejar.MozillaCookieJar(str(path))
            try:
                jar.load(ignore_discard=True, ignore_expires=True)
                session.cookies.update(jar)
                print(f"[认证] 从文件加载 Cookie：{cookie_file}")
            except Exception:
                # 尝试按 key=value 格式读取
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        session.cookies.set(k.strip(), v.strip())
                print(f"[认证] 从文件读取 key=value Cookie：{cookie_file}")

    if basic_auth:
        if ":" in basic_auth:
            user, password = basic_auth.split(":", 1)
            session.auth = (user, password)
            print(f"[认证] Basic Auth：{user}")
        else:
            print(f"[警告] --basic-auth 格式应为 user:password", file=sys.stderr)

    return session


def fetch_html(url: str, session: requests.Session) -> str:
    resp = session.get(url, timeout=20, allow_redirects=True)
    if resp.status_code == 401:
        raise RuntimeError("需要登录（401）。请提供 --cookie 或 --basic-auth 参数。")
    if resp.status_code == 403:
        raise RuntimeError("无权访问（403）。请检查 Cookie 是否有效或已过期。")
    resp.raise_for_status()
    # 自动处理编码
    if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1"):
        resp.encoding = resp.apparent_encoding
    return resp.text


def fetch_content(url: str, session: requests.Session) -> tuple[str, str]:
    """
    获取 URL 内容，返回 (文本内容, 内容类型)。
    内容类型为 'markdown' 或 'html'。
    """
    resp = session.get(url, timeout=20, allow_redirects=True)
    if resp.status_code == 401:
        raise RuntimeError("需要登录（401）。请提供 --cookie 或 --basic-auth 参数。")
    if resp.status_code == 403:
        raise RuntimeError("无权访问（403）。请检查 Cookie 是否有效或已过期。")
    resp.raise_for_status()
    if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1"):
        resp.encoding = resp.apparent_encoding
    text = resp.text
    content_type = resp.headers.get("Content-Type", "")
    if is_markdown_url(url) or is_markdown_content(text, content_type):
        return text, "markdown"
    return text, "html"


# ──────────────────────────────────────────────────────────────
# API 信息提取
# ──────────────────────────────────────────────────────────────

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


def extract_api_from_html(html: str, source_url: str) -> dict:
    """
    从 HTML 中提取所有 API 接口相关信息。
    返回结构化数据，包含：
      - title: 页面标题
      - source_url
      - apis: [{ method, path, description, params, response, raw_text }]
      - raw_tables: 原始表格数据（Markdown 格式）
      - raw_code_blocks: 代码块文本列表
    """
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "title": "",
        "source_url": source_url,
        "apis": [],
        "raw_tables": [],
        "raw_code_blocks": [],
    }

    # 页面标题
    title_tag = soup.find("title")
    if title_tag:
        result["title"] = title_tag.get_text(strip=True)

    # ── 1. 代码块（可能包含 curl / JSON 示例）
    for code in soup.find_all(["code", "pre"]):
        text = code.get_text(strip=True)
        if text and len(text) > 10:
            result["raw_code_blocks"].append(text)

    # ── 2. 表格 → Markdown
    for table in soup.find_all("table"):
        md = _table_to_markdown(table)
        if md:
            result["raw_tables"].append(md)

    # ── 3. 识别 API 条目
    #    策略 A：查找包含 HTTP 方法 + 路径的文本行
    apis_from_text = _extract_apis_from_text(soup)
    result["apis"].extend(apis_from_text)

    #    策略 B：识别 Confluence/Wiki 常见的接口文档结构（h2/h3 + 表格）
    if not result["apis"]:
        apis_from_sections = _extract_apis_from_sections(soup)
        result["apis"].extend(apis_from_sections)

    return result


def _table_to_markdown(table) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True).replace("|", "\\|") for td in tr.find_all(["th", "td"])]
        if cells:
            rows.append("| " + " | ".join(cells) + " |")
    if len(rows) < 2:
        return ""
    # 插入分隔行
    header = rows[0]
    cols = header.count("|") - 1
    sep = "| " + " | ".join(["---"] * cols) + " |"
    rows.insert(1, sep)
    return "\n".join(rows)


def _extract_apis_from_text(soup) -> list[dict]:
    """扫描全文，用正则识别 HTTP 方法 + 路径。"""
    apis = []
    # 匹配 GET /api/xxx 或 POST https://...
    pattern = re.compile(
        r'\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b\s+([/\w\-\.\{\}:?=&%]+)',
        re.IGNORECASE
    )
    seen = set()
    for tag in soup.find_all(string=True):
        text = tag.strip()
        for m in pattern.finditer(text):
            method = m.group(1).upper()
            path = m.group(2)
            key = f"{method} {path}"
            if key not in seen:
                seen.add(key)
                # 尝试找最近的描述文字
                parent = tag.parent
                desc = ""
                if parent:
                    desc = parent.get_text(" ", strip=True)[:200]
                apis.append({"method": method, "path": path, "description": desc})
    return apis


def _extract_apis_from_sections(soup) -> list[dict]:
    """
    针对 Confluence 文档风格：
    h2/h3 标题往往是接口名，紧跟的 table 是参数说明。
    """
    apis = []
    for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = heading.get_text(" ", strip=True)
        # 判断标题是否像接口名（包含 / 或 API 关键词）
        if "/" not in text and not re.search(r'\bAPI\b|\b接口\b|\b请求\b', text, re.IGNORECASE):
            continue
        api_entry = {"title": text, "description": text, "sections": []}
        # 收集标题后面的内容直到下一个同级标题
        for sibling in heading.find_next_siblings():
            if sibling.name in ["h1", "h2", "h3", "h4"]:
                break
            sibling_text = sibling.get_text(" ", strip=True)
            if sibling_text:
                api_entry["sections"].append(sibling_text[:500])
        if api_entry["sections"]:
            apis.append(api_entry)
    return apis


# ──────────────────────────────────────────────────────────────
# 输出格式化
# ──────────────────────────────────────────────────────────────

def format_as_markdown(data: dict) -> str:
    lines = []
    lines.append(f"# {data['title']}")
    lines.append(f"\n> 来源：{data['source_url']}\n")

    if data["apis"]:
        lines.append("## 识别到的接口\n")
        for i, api in enumerate(data["apis"], 1):
            method = api.get("method", "")
            path = api.get("path", "")
            desc = api.get("description", api.get("title", ""))
            if method and path:
                lines.append(f"### {i}. `{method} {path}`")
            elif api.get("title"):
                lines.append(f"### {i}. {api['title']}")
            else:
                continue
            if desc and desc != f"{method} {path}":
                # 截取合理长度避免重复
                short_desc = desc[:150].replace("\n", " ").strip()
                lines.append(f"\n{short_desc}\n")
            for section in api.get("sections", []):
                lines.append(f"\n{section[:300]}\n")
            lines.append("")

    if data["raw_tables"]:
        lines.append("## 原始表格\n")
        for i, table in enumerate(data["raw_tables"], 1):
            lines.append(f"### 表格 {i}\n")
            lines.append(table)
            lines.append("")

    if data["raw_code_blocks"]:
        lines.append("## 代码/示例\n")
        for block in data["raw_code_blocks"][:10]:  # 最多显示 10 个
            lines.append("```")
            lines.append(block[:800])
            lines.append("```\n")

    return "\n".join(lines)


def format_as_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="抓取网页中的 API 接口信息（支持需要登录的 Confluence 等）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("url", help="目标网页 URL")
    parser.add_argument("--cookie", "-c", help='Cookie 字符串，如 "JSESSIONID=xxx; token=yyy"')
    parser.add_argument("--cookie-file", help="Cookie 文件路径（Netscape 格式或 key=value 行）")
    parser.add_argument("--basic-auth", help="HTTP Basic Auth，格式：user:password")
    parser.add_argument("--output", "-o", help="输出文件路径（默认打印到终端）")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="输出格式（默认 markdown）")
    args = parser.parse_args()

    session = build_session(args.cookie, args.cookie_file, args.basic_auth)

    print(f"[抓取] {args.url}")
    try:
        content, content_type = fetch_content(args.url, session)
    except RuntimeError as e:
        print(f"\n错误：{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n请求失败：{e}", file=sys.stderr)
        sys.exit(1)

    print(f"[解析] 内容类型：{content_type}，提取 API 信息…")
    if content_type == "markdown":
        data = extract_api_from_markdown(content, args.url)
    else:
        data = extract_api_from_html(content, args.url)

    api_count = len(data["apis"])
    table_count = len(data["raw_tables"])
    code_count = len(data["raw_code_blocks"])
    print(f"[结果] 识别接口：{api_count} 个，表格：{table_count} 个，代码块：{code_count} 个")

    if args.format == "json":
        output = format_as_json(data)
    else:
        output = format_as_markdown(data)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"[保存] 已写入：{args.output}")
    else:
        print("\n" + "─" * 60)
        print(output)


if __name__ == "__main__":
    main()
