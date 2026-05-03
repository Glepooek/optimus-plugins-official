#!/usr/bin/env python3
"""
fetch_feishu_doc.py — 通过飞书开放平台 API 获取云文档内容并保存为 Markdown 文件

用法：
  python fetch_feishu_doc.py <doc_token> [选项]

认证优先级（依次尝试）：
  1. --app-id + --app-secret    自建应用凭证，自动获取并缓存 tenant_access_token
  2. --token <access_token>     直接传入已有的 tenant_access_token 或 user_access_token
  3. --token-file <file>        从文件读取 token（文件内容为纯 token 字符串）
  4. 环境变量                   FEISHU_APP_ID + FEISHU_APP_SECRET，或 FEISHU_ACCESS_TOKEN

示例：
  # 推荐：使用 app_id + app_secret 自动获取 token（token 会缓存到本地避免重复请求）
  python fetch_feishu_doc.py B4EPdAYx8oi8HRxgPQQbM15UcBf \\
      --app-id cli_xxx --app-secret dskLLL \\
      --output cache/my-doc.md

  # 直接传已有 token
  python fetch_feishu_doc.py B4EPdAYx8oi8HRxgPQQbM15UcBf \\
      --token "t-xxx" --output cache/my-doc.md

  # 从文件读取 token
  python fetch_feishu_doc.py B4EPdAYx8oi8HRxgPQQbM15UcBf \\
      --token-file ~/.feishu_token --output cache/my-doc.md

如何获取 doc_token：
  打开飞书文档，URL 中 /docx/ 后面的部分即为 doc_token。
  例如：https://xxx.feishu.cn/docx/B4EPdAYx8oi8HRxgPQQbM15UcBf
  doc_token = B4EPdAYx8oi8HRxgPQQbM15UcBf

如何获取 app_id / app_secret：
  飞书开放平台控制台 → 选择应用 → 凭证与基础信息
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("缺少依赖，请先安装：pip install requests", file=sys.stderr)
    sys.exit(1)

FEISHU_DOC_API = "https://open.feishu.cn/open-apis/docs/v1/content"
FEISHU_TOKEN_API = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

# token 缓存文件，存放于脚本同目录下的 cache/ 中
_SCRIPT_DIR = Path(__file__).parent
_TOKEN_CACHE_FILE = _SCRIPT_DIR / "cache" / ".feishu_token_cache.json"


# ──────────────────────────────────────────────────────────────
# tenant_access_token 获取与缓存
# ──────────────────────────────────────────────────────────────

def _load_cached_token(app_id: str) -> str | None:
    """从本地缓存读取有效的 tenant_access_token（剩余有效期 > 30 分钟才使用）。"""
    if not _TOKEN_CACHE_FILE.exists():
        return None
    try:
        cache = json.loads(_TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
        entry = cache.get(app_id)
        if not entry:
            return None
        # 剩余有效期不足 30 分钟则视为失效
        if entry.get("expires_at", 0) - time.time() < 1800:
            return None
        return entry["token"]
    except Exception:
        return None


def _save_cached_token(app_id: str, token: str, expire: int) -> None:
    """将 tenant_access_token 写入本地缓存。"""
    _TOKEN_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache = {}
    if _TOKEN_CACHE_FILE.exists():
        try:
            cache = json.loads(_TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    cache[app_id] = {
        "token": token,
        "expires_at": time.time() + expire,
    }
    _TOKEN_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """
    通过 app_id + app_secret 获取 tenant_access_token。
    优先返回本地缓存中有效的 token，避免频繁调用接口。
    """
    cached = _load_cached_token(app_id)
    if cached:
        print("[认证] 使用缓存的 tenant_access_token（剩余有效期 > 30 分钟）")
        return cached

    print(f"[认证] 正在获取 tenant_access_token（app_id={app_id}）…")
    resp = requests.post(
        FEISHU_TOKEN_API,
        headers={"Content-Type": "application/json; charset=utf-8"},
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()

    code = body.get("code", -1)
    if code != 0:
        raise RuntimeError(
            f"获取 tenant_access_token 失败 code={code}: {body.get('msg', '')}\n"
            "请检查 app_id 和 app_secret 是否正确。"
        )

    token = body["tenant_access_token"]
    expire = body.get("expire", 7200)
    _save_cached_token(app_id, token, expire)
    print(f"[认证] 获取成功，有效期 {expire} 秒，已缓存到本地")
    return token


# ──────────────────────────────────────────────────────────────
# 文档获取
# ──────────────────────────────────────────────────────────────

def fetch_doc(doc_token: str, access_token: str) -> str:
    """调用飞书 API 获取文档 Markdown 内容，返回 Markdown 字符串。"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params = {
        "doc_token": doc_token,
        "doc_type": "docx",
        "content_type": "markdown",
        "lang": "zh",
    }

    print(f"[请求] GET {FEISHU_DOC_API}")
    print(f"[参数] doc_token={doc_token}, doc_type=docx, content_type=markdown")

    resp = requests.get(FEISHU_DOC_API, headers=headers, params=params, timeout=30)

    if resp.status_code == 401:
        raise RuntimeError("认证失败（401）：access_token 无效或已过期，请重新获取。")
    if resp.status_code == 403:
        raise RuntimeError(
            "无权访问（403）：\n"
            "  - 如使用 tenant_access_token，请在文档页面右上角「...」→「添加文档应用」为应用授权\n"
            "  - 如使用 user_access_token，请通过「分享」为该用户添加阅读权限"
        )
    resp.raise_for_status()

    body = resp.json()
    code = body.get("code", -1)
    msg = body.get("msg", "")

    ERROR_HINTS = {
        2889902: "无权访问：请确认操作者有文档阅读权限（详见上方 403 说明）",
        2889904: "参数无效：请检查 doc_token 格式（长度应为 22~27 字符）",
        2889906: "文档已被删除",
        2889914: "doc_token 不存在：请确认 token 是否正确",
        2889925: "文档内容超过 10 MB 限制，无法导出",
        2889901: "混部资源已过期",
        2889905: "飞书服务内部错误，请稍后重试或联系技术支持",
        2889980: "文档正在创建副本中，请稍后再试",
    }

    if code != 0:
        hint = ERROR_HINTS.get(code, "")
        raise RuntimeError(
            f"飞书 API 返回错误 code={code}: {msg}"
            + (f"\n  提示：{hint}" if hint else "")
        )

    content = body.get("data", {}).get("content", "")
    if not content:
        raise RuntimeError("API 返回成功但 content 为空，文档可能不包含内容。")

    return content


# ──────────────────────────────────────────────────────────────
# 认证解析
# ──────────────────────────────────────────────────────────────

def resolve_token(args) -> str:
    """
    按优先级解析 access_token：
    1. --app-id + --app-secret（或对应环境变量）→ 自动获取 tenant_access_token
    2. --token（或 FEISHU_ACCESS_TOKEN 环境变量）
    3. --token-file
    """
    app_id = args.app_id or os.environ.get("FEISHU_APP_ID", "")
    app_secret = args.app_secret or os.environ.get("FEISHU_APP_SECRET", "")

    if app_id and app_secret:
        return get_tenant_access_token(app_id, app_secret)

    token = args.token or os.environ.get("FEISHU_ACCESS_TOKEN", "")
    if token:
        return token.strip()

    if args.token_file:
        path = Path(args.token_file).expanduser()
        if not path.exists():
            raise RuntimeError(f"Token 文件不存在：{args.token_file}")
        return path.read_text(encoding="utf-8").strip()

    raise RuntimeError(
        "未提供认证凭证。请通过以下任意方式提供：\n"
        "  1. --app-id <id> --app-secret <secret>    （推荐，自动管理 token）\n"
        "  2. --token <tenant_access_token>\n"
        "  3. --token-file <文件路径>\n"
        "  4. 环境变量 FEISHU_APP_ID + FEISHU_APP_SECRET\n"
        "  5. 环境变量 FEISHU_ACCESS_TOKEN"
    )


# ──────────────────────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="通过飞书 API 获取云文档内容（Markdown 格式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("doc_token", help="飞书文档的唯一标识（URL 中 /docx/ 后的部分）")

    auth_group = parser.add_argument_group("认证（优先级：app凭证 > token > token文件 > 环境变量）")
    auth_group.add_argument("--app-id", help="飞书自建应用 app_id（配合 --app-secret 自动获取 token）")
    auth_group.add_argument("--app-secret", help="飞书自建应用 app_secret")
    auth_group.add_argument("--token", "-t", help="直接传入 tenant_access_token 或 user_access_token")
    auth_group.add_argument("--token-file", help="从文件读取 token（文件内容为纯 token 字符串）")

    parser.add_argument("--output", "-o", help="输出文件路径（默认：cache/feishu-<doc_token前8位>.md）")
    args = parser.parse_args()

    try:
        access_token = resolve_token(args)
    except RuntimeError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    output_path = (
        Path(args.output) if args.output
        else _SCRIPT_DIR / "cache" / f"feishu-{args.doc_token[:8]}.md"
    )

    try:
        content = fetch_doc(args.doc_token, access_token)
    except RuntimeError as e:
        print(f"\n错误：{e}", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"\nHTTP 错误：{e}", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    lines = content.count("\n") + 1
    print(f"\n保存成功：{output_path}")
    print(f"  内容行数：{lines}")


if __name__ == "__main__":
    main()
