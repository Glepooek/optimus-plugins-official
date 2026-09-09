#!/usr/bin/env python3
"""抓取 Claude Code CHANGELOG.md 并按同步锚点截断，供 sync-cc-tips 第一步使用。

输出 JSON 到 stdout，SKILL.md 只需读几个字段决定下一步，不必自己编排取数命令。

## 为什么两跳换的是主机名而不是工具

最常见的失败不是全局断网，而是 `raw.githubusercontent.com` 单主机被阻断。
此时换工具（curl → wget → WebFetch）毫无用处，必须换主机。2026-09-09 犯过
两次同类错：先是三跳全指向 raw 域（换工具不换主机）；改用
`github.com/<repo>/raw/<file>` 后又误以为换了主机——那个 URL 返 302，跟随后
落点还是 raw 域。**字节等价对「内容」成立，对「可达性」不成立。**

`api.github.com/repos/<repo>/contents/<file>` + `Accept: application/vnd.github.raw`
零重定向、自己终止请求，与 raw 域内容字节完全一致，是真正独立的第二跳。

**不要新增「等 N 秒重试同一条命令」这类跳**：同主机同工具同参数，故障域与
第一跳完全重合，只对瞬时抖动有效，而抖动已由 timeout 覆盖。

## 为什么不落临时文件

上一版走 `curl -sf -o "$T"` 再 `awk … "$T"`，两步式是为避开
`curl … | awk …` 吞掉 curl 退出码的坑。改用 urllib 在内存中处理后，临时文件
连同它的生命周期管理（`rm -f`）一起消失，也就不存在「Bash 工具是 Git Bash、
Python 是 Windows 原生解释器，`/tmp` 对后者不可见」这类跨文件系统视图问题。

## 退出码

| 码 | 含义 | 输出的 verdict |
|---|---|---|
| 0 | 成功取到并截断 | — |
| 3 | 两跳均不可达 | network_down / single_host_blocked |
| 4 | 取到内容但解析失败（无 `## ` 版本标记） | parse_failed |
| 2 | 参数非法 | — |
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

DEFAULT_ANCHOR_FILE = ".claude/skills/sync-cc-tips/.last-synced-version"

# 首次运行（无锚点）时的默认窗口大小
DEFAULT_WINDOW = 10

# 锚点未在 changelog 中找到时，超过该版本数需人工确认
CONFIRM_THRESHOLD = 30

TIMEOUT_RAW = 15
TIMEOUT_API = 20
TIMEOUT_DIAG = 8

# 两跳。顺序即优先级，命中即停。每跳的 host 必须互不相同——这是降级的全部意义。
HOPS = (
    {
        "name": "raw",
        "host": "raw.githubusercontent.com",
        "url": "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md",
        "headers": {},
        "timeout": TIMEOUT_RAW,
    },
    {
        "name": "api",
        "host": "api.github.com",
        "url": "https://api.github.com/repos/anthropics/claude-code/contents/CHANGELOG.md",
        "headers": {"Accept": "application/vnd.github.raw"},
        "timeout": TIMEOUT_API,
    },
)

# 连通性分诊探测的主机。example.com 是对照组：它也不通才说明是全局断网。
DIAG_HOSTS = ("raw.githubusercontent.com", "api.github.com", "example.com")

VERSION_RE = re.compile(r"^## +(\d+\.\d+\.\d+)\s*$")
BULLET_RE = re.compile(r"^\s*[-*] +(.*\S)\s*$")


def read_anchor(path):
    """读同步锚点。文件不存在或为空返回 None（首次运行）。"""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip() or None
    except OSError:
        return None


def fetch_one(hop):
    """请求单跳。成功返回正文字符串，失败返回 None。

    捕获所有 OSError 子类（URLError / socket.timeout 均属之）而非只捕 HTTPError——
    降级的触发条件是「这个主机拿不到」，不区分是 DNS、超时还是 4xx。
    """
    req = urllib.request.Request(hop["url"], headers=hop["headers"])
    try:
        with urllib.request.urlopen(req, timeout=hop["timeout"]) as resp:
            if resp.status != 200:
                return None
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, ValueError):
        return None


def probe(host, timeout=TIMEOUT_DIAG):
    """探测主机可达性，返回 HTTP 状态码字符串；不可达返回 "000"。

    与 `curl -o /dev/null -w '%{http_code}'` 语义一致：连不上是 000，
    连上了但返 4xx/5xx 也算「主机活着」——分诊要区分的是网络层而非应用层。
    """
    try:
        req = urllib.request.Request(f"https://{host}/", method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except (urllib.error.URLError, OSError, ValueError):
        return "000"


def diagnose():
    """两跳全败后做连通性分诊，区分全局断网与单主机阻断。

    不做这一步就会把单主机阻断误报成断网——两者的后续处置完全不同：
    前者需要新的取数通道，后者只能等网络恢复。
    """
    results = {h: probe(h) for h in DIAG_HOSTS}
    if all(v == "000" for v in results.values()):
        verdict = "network_down"
    else:
        verdict = "single_host_blocked"
    return results, verdict


def parse_versions(text):
    """把 changelog 正文切成 [{v, bullets}]，按文件顺序（新→旧）。

    bullet 只收 `-` / `*` 开头的行；版本段内的说明性散文与嵌套缩进行不计入，
    避免把非功能点的排版内容当成待判定 bullet。
    """
    versions = []
    current = None
    for line in text.splitlines():
        m = VERSION_RE.match(line)
        if m:
            current = {"v": m.group(1), "bullets": []}
            versions.append(current)
            continue
        if current is None:
            continue
        b = BULLET_RE.match(line)
        if b:
            current["bullets"].append(b.group(1))
    return versions


def truncate(versions, anchor, limit):
    """按锚点或数量窗口截断，返回 (选中版本, anchor_found)。

    三种模式互斥，优先级 limit > anchor > 默认窗口：

    - limit 非 None：`/sync-cc-tips N`，忽略锚点取最新 N 个。anchor_found 恒为 None
      （本模式不查锚点，不能报告"找到"或"没找到"）
    - anchor 非 None：取锚点之前（更新）的全部版本。**锚点版本本身不含在结果里**
      ——它上轮已处理过
    - 两者皆 None：首次运行，取最新 DEFAULT_WINDOW 个
    """
    if limit is not None:
        return versions[:limit], None
    if anchor is None:
        return versions[:DEFAULT_WINDOW], None
    for i, item in enumerate(versions):
        if item["v"] == anchor:
            return versions[:i], True
    # 锚点没找到：相隔太久已被滚出文件，或锚点写错。返回全部可见版本，
    # 由调用方按 CONFIRM_THRESHOLD 决定是否需要人工确认。
    return versions, False


def emit(payload, code):
    """输出 JSON 到 stdout 并返回退出码。数据走 stdout，便于调用方直接解析。"""
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return code


def run(anchor_file=DEFAULT_ANCHOR_FILE, limit=None):
    """执行取数与截断，返回 (payload, exit_code)。"""
    anchor = None if limit is not None else read_anchor(anchor_file)

    text = None
    hop_used = None
    hops_failed = []
    for hop in HOPS:
        text = fetch_one(hop)
        if text is not None:
            hop_used = hop["name"]
            break
        hops_failed.append(hop["name"])

    if text is None:
        results, verdict = diagnose()
        return {
            "ok": False,
            "hops_failed": hops_failed,
            "diagnosis": results,
            "verdict": verdict,
            # network_down 时 WebFetch 同样走网络，没有再试的价值
            "next": "stop" if verdict == "network_down" else "webfetch",
        }, 3

    versions = parse_versions(text)
    if not versions:
        return {
            "ok": False,
            "hop": hop_used,
            "verdict": "parse_failed",
            "next": "stop",
            "head": text[:200],
        }, 4

    selected, anchor_found = truncate(versions, anchor, limit)
    # 判据只看版本数，不看锚点是否找到。
    #
    # 上一版隐含假设了「只有找不到锚点才会范围过大」——那来自 awk 实现的视角
    # （跑到文件末尾都没 exit 才输出全部）。实测证伪：锚点 1.0.0 在文件里真实存在，
    # 截断后仍有 351 个版本。范围过大本身就是需要确认的理由，与锚点是否命中无关。
    #
    # limit 模式不确认——用户显式指定了 N，那就是他要的范围。
    needs_confirm = limit is None and len(selected) > CONFIRM_THRESHOLD

    payload = {
        "ok": True,
        "hop": hop_used,
        "hops_failed": hops_failed,
        "anchor": anchor,
        "anchor_found": anchor_found,
        "limit": limit,
        # limit 模式是范围受限的临时查看，不代表真实同步进度，不得推进锚点
        "advance_anchor": limit is None,
        "version_count": len(selected),
        "range": [selected[-1]["v"], selected[0]["v"]] if selected else None,
        "latest_available": versions[0]["v"],
        "needs_confirm": needs_confirm,
        "bullet_count": sum(len(v["bullets"]) for v in selected),
        "versions": selected,
    }
    return payload, 0


def main(argv):
    p = argparse.ArgumentParser(
        prog="fetch_changelog.py",
        description="抓取 Claude Code CHANGELOG.md 并按同步锚点截断，输出 JSON。",
        epilog=(
            "示例：\n"
            "  python scripts/fetch_changelog.py            # 按 .last-synced-version 截断\n"
            "  python scripts/fetch_changelog.py --limit 5  # 忽略锚点，只看最新 5 个版本\n"
            "\n退出码：0 成功 / 3 两跳均不可达 / 4 解析失败 / 2 参数非法"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="忽略锚点，只取最新 N 个版本（对应 /sync-cc-tips N）。本模式不推进锚点。",
    )
    p.add_argument(
        "--anchor-file",
        default=DEFAULT_ANCHOR_FILE,
        metavar="PATH",
        help=f"同步锚点文件路径（默认 {DEFAULT_ANCHOR_FILE}）",
    )
    args = p.parse_args(argv[1:])

    if args.limit is not None and args.limit < 1:
        print("错误: --limit 必须 ≥ 1，收到 " f"{args.limit}", file=sys.stderr)
        return 2

    payload, code = run(anchor_file=args.anchor_file, limit=args.limit)
    return emit(payload, code)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
