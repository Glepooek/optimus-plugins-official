#!/usr/bin/env python3
"""
fetch_swagger.py — 从 Swagger UI 地址或 OpenAPI 直链获取 API 文档并保存为 JSON 文件

用法：
  python fetch_swagger.py <url> [--output <file>]

示例：
  python fetch_swagger.py https://petstore.swagger.io/v2/swagger.json
  python fetch_swagger.py https://example.com/swagger-ui/index.html
  python fetch_swagger.py https://example.com/api --output my-api.json
  python fetch_swagger.py https://soetest.optimus.cn/api/doc.html
  python fetch_swagger.py "https://soetest.optimus.cn/api/v2/api-docs?group=SOE融合语音引擎服务"

支持：
  - 标准 Swagger UI
  - Swagger Bootstrap UI（多分组）
  - 直接 OpenAPI/Swagger JSON/YAML 链接
  - 自动处理 URL 中的中文参数编码
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote

try:
    import requests
except ImportError:
    print("缺少依赖，请先安装：pip install requests", file=sys.stderr)
    sys.exit(1)

# Swagger UI 页面下，常见的底层 spec 路径
COMMON_SPEC_PATHS = [
    "/v3/api-docs",
    "/v3/api-docs.yaml",
    "/v2/api-docs",
    "/swagger.json",
    "/swagger.yaml",
    "/openapi.json",
    "/openapi.yaml",
    "/api-docs",
    "/api/swagger.json",
    "/api/openapi.json",
]


def get(url: str, **kwargs) -> requests.Response:
    """发送 GET 请求，设置通用 headers。"""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "fetch-swagger/1.0 (python-requests)",
    }
    resp = requests.get(url, headers=headers, timeout=15, **kwargs)
    resp.raise_for_status()
    return resp


def looks_like_spec(data: dict) -> bool:
    """简单判断一个 JSON 对象是否像 OpenAPI / Swagger spec。"""
    return "paths" in data or "swagger" in data or "openapi" in data


def normalize_spec_url(url: str) -> str:
    """
    规范化 spec URL，确保 query 参数中的中文被正确 URL 编码。
    例如：/v2/api-docs?group=SOE融合语音引擎服务 → /v2/api-docs?group=SOE%E8%9E%8D%E5%90%88...
    """
    from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode

    parsed = urlsplit(url)
    if parsed.query:
        # 解析 query 参数
        params = parse_qs(parsed.query, keep_blank_values=True)
        # 重新编码，确保中文被正确编码
        encoded_query = urlencode(params, doseq=True, quote_via=quote)
        # 重建 URL
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, encoded_query, parsed.fragment))
    return url


def try_direct(url: str) -> dict | None:
    """尝试把 URL 直接当作 spec JSON 获取。"""
    try:
        resp = get(url)
        data = resp.json()
        if looks_like_spec(data):
            return data
    except Exception:
        pass
    return None


def discover_spec_from_html(html: str, base_url: str) -> list[str]:
    """
    从 Swagger UI HTML 页面内容中提取底层 spec 地址。
    支持：
      - window.onload / SwaggerUIBundle 中的 url 参数
      - <link rel="preload"> 或 <script src=> 中的 .json/.yaml 后缀
      - meta 标签中的 spec url
      - Swagger Bootstrap UI 中的 urls 数组（多分组）

    返回可能的 spec URL 列表。
    """
    spec_urls = []

    # 单个 URL 模式
    patterns = [
        # SwaggerUIBundle({ url: "..." })
        r'SwaggerUIBundle\s*\(\s*\{[^}]*?url\s*:\s*["\']([^"\']+)["\']',
        # url: "..." (更宽泛)
        r'["\s]url["\s]*:\s*["\']([^"\']+\.(?:json|yaml|yml))["\']',
        # configUrl 或 spec url 在 script 标签
        r'configUrl["\s]*:\s*["\']([^"\']+)["\']',
        # data-url 属性
        r'data-url=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if m:
            spec_url = m.group(1).strip()
            if spec_url.startswith("http"):
                spec_urls.append(spec_url)
            else:
                spec_urls.append(urljoin(base_url, spec_url))

    # Swagger Bootstrap UI 多分组模式：urls: [{url: "...", name: "..."}]
    # 匹配 urls 数组中的所有 url
    urls_array_pattern = r'urls\s*:\s*\[(.*?)\]'
    urls_match = re.search(urls_array_pattern, html, re.IGNORECASE | re.DOTALL)
    if urls_match:
        urls_content = urls_match.group(1)
        # 提取每个 url 字段
        url_pattern = r'url\s*:\s*["\']([^"\']+)["\']'
        for url_match in re.finditer(url_pattern, urls_content, re.IGNORECASE):
            spec_url = url_match.group(1).strip()
            if spec_url.startswith("http"):
                spec_urls.append(spec_url)
            else:
                spec_urls.append(urljoin(base_url, spec_url))

    return spec_urls


def try_swagger_bootstrap_ui(base_url: str) -> dict | None:
    """
    尝试 Swagger Bootstrap UI 的标准探测流程：
    1. 访问 /swagger-resources 获取分组列表
    2. 从第一个分组的 location 字段构建 spec URL

    返回 spec dict，失败返回 None
    """
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # 尝试不同的 context path
    context_paths = []
    parts = parsed.path.rstrip("/").split("/")
    while parts:
        context_paths.append("/".join(parts))
        parts.pop()
    context_paths.append("")  # root path

    for ctx in context_paths:
        resources_url = base + ctx + "/swagger-resources"
        try:
            resp = get(resources_url)
            resources = resp.json()

            if not isinstance(resources, list) or len(resources) == 0:
                continue

            print(f"      发现 Swagger Bootstrap UI 配置（{len(resources)} 个分组）")

            # 如果有多个分组，列出所有分组
            if len(resources) > 1:
                print("      API 分组列表：")
                for i, group in enumerate(resources, 1):
                    name = group.get("name", "未命名")
                    print(f"        {i}. {name}")
                print("      将获取第一个分组...")

            # 获取第一个分组的 spec
            first_group = resources[0]
            location = first_group.get("location", "")
            if not location:
                continue

            # 构建完整的 spec URL
            if location.startswith("http"):
                spec_url = location
            else:
                spec_url = base + ctx + location

            print(f"      分组：{first_group.get('name', '未命名')}")
            print(f"      地址：{spec_url}")

            # 规范化并获取 spec
            normalized = normalize_spec_url(spec_url)
            spec = try_direct(normalized)
            if spec:
                print("      获取成功！")
                return spec

        except Exception:
            continue

    return None


def fetch_spec(input_url: str) -> dict:
    """
    主流程：
    1. 直接尝试把 URL 当作 spec JSON
    2. 尝试 Swagger Bootstrap UI 的 /swagger-resources 探测
    3. 加载页面 HTML，从中提取 spec 地址
    4. 按常见路径逐一探测
    """
    print(f"[1/4] 尝试直接获取 spec：{input_url}")
    # 先规范化 URL（处理中文编码）
    normalized_url = normalize_spec_url(input_url)
    spec = try_direct(normalized_url)
    if spec:
        print("      成功！")
        return spec

    print("[2/4] 尝试 Swagger Bootstrap UI 探测…")
    spec = try_swagger_bootstrap_ui(input_url)
    if spec:
        return spec

    print("[3/4] 加载页面，从 HTML 中提取 spec 地址…")
    try:
        resp = get(input_url)
        content_type = resp.headers.get("Content-Type", "")
        if "json" in content_type or "yaml" in content_type:
            # 响应本身就是 spec（可能无法 json() 因为是 yaml）
            try:
                return resp.json()
            except Exception:
                pass

        html = resp.text
        discovered_urls = discover_spec_from_html(html, input_url)
        if discovered_urls:
            print(f"      发现 {len(discovered_urls)} 个 spec 地址")
            # 如果有多个 spec，提示用户选择或尝试第一个
            if len(discovered_urls) > 1:
                print("      发现多个 API 分组：")
                for i, url in enumerate(discovered_urls, 1):
                    print(f"        {i}. {url}")
                print("      将尝试获取第一个...")

            # 尝试每个发现的 URL
            for url in discovered_urls:
                normalized = normalize_spec_url(url)
                print(f"      尝试：{normalized}")
                spec = try_direct(normalized)
                if spec:
                    print("      获取成功！")
                    return spec
    except Exception as e:
        print(f"      加载页面失败：{e}")

    print("[4/4] 按常见路径探测…")
    parsed = urlparse(input_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # 也尝试去掉末尾路径（如 /swagger-ui/index.html → /）
    context_paths = set()
    parts = parsed.path.rstrip("/").split("/")
    while parts:
        context_paths.add("/".join(parts))
        parts.pop()
    context_paths.add("")

    for ctx in sorted(context_paths, key=len, reverse=True):
        for suffix in COMMON_SPEC_PATHS:
            candidate = base + ctx + suffix
            try:
                normalized = normalize_spec_url(candidate)
                resp = get(normalized)
                data = resp.json()
                if looks_like_spec(data):
                    print(f"      命中：{normalized}")
                    return data
            except Exception:
                continue

    raise RuntimeError(
        f"无法从以下地址获取 OpenAPI/Swagger spec：{input_url}\n"
        "请确认地址可访问，或直接传入 spec JSON 的 URL。"
    )


def default_output_name(url: str) -> str:
    """根据 URL 生成默认输出文件名。"""
    host = urlparse(url).netloc.replace(":", "_").replace(".", "-")
    return f"{host}-api.json" if host else "api.json"


def main():
    parser = argparse.ArgumentParser(
        description="从 Swagger / OpenAPI 地址获取 API 文档并保存为 JSON 文件"
    )
    parser.add_argument("url", help="Swagger UI 页面地址或 OpenAPI spec 直链")
    parser.add_argument(
        "--output", "-o", help="输出文件路径（默认根据域名自动命名）"
    )
    args = parser.parse_args()

    url = args.url.strip()
    output_path = Path(args.output) if args.output else Path(default_output_name(url))

    try:
        spec = fetch_spec(url)
    except RuntimeError as e:
        print(f"\n错误：{e}", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"\nHTTP 错误：{e}", file=sys.stderr)
        sys.exit(1)

    output_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    # 打印摘要
    title = spec.get("info", {}).get("title", "（无标题）")
    version = spec.get("info", {}).get("version", "?")
    paths_count = len(spec.get("paths", {}))
    print(f"\n保存成功：{output_path}")
    print(f"  标题：{title}  版本：{version}  接口数：{paths_count}")


if __name__ == "__main__":
    main()
