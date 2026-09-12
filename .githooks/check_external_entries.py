#!/usr/bin/env python3
"""校验 .claude-plugin/marketplace.json 里外部引用条目的结构合规与来源可追。

只查机械可判定项，一律不联网——提交门禁联网会让离线提交失败，代价大于收益。
因此本脚本保证的是「条目结构正确、来源可追」，不保证条目指向的内容真的存在、
真的是 skill、或真的还在维护；后者由实际安装验证与人承担。

设计依据：docs/superpowers/specs/2026-09-12-add-external-skill-design.md
"""
import json
import pathlib
import re
import sys

MARKETPLACE_REL = ".claude-plugin/marketplace.json"
REGISTRY_REL = ".claude/skills/add-external-skill/registry.md"
ACTIVE_MARKER = "<!-- registry:active -->"
ALLOWED_SOURCES = {"url", "github", "git-subdir"}
REQUIRED_META = ("description", "homepage", "author")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA_IN_TEXT_RE = re.compile(r"\b[0-9a-f]{40}\b")


def _load(path):
    """返回 (data, err)。err 非 None 时 data 为 None。"""
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"无法解析 JSON：{e}"
    except OSError as e:
        return None, f"无法读取：{e}"


def registry_active(repo_root):
    """取台账「已接入」表的 名字 -> sha 映射。返回 (mapping, err)。

    只认 ACTIVE_MARKER 之后、下一个 Markdown 标题之前的表格行。用锚点而不是
    章节标题的措辞定位，是因为措辞会被改；也不扫全文所有表格——「更新历史」
    行的首列同样是条目名，且一行里有旧、新两个 sha，混进来会让 sha 比对失效。

    行内没有 40 位 SHA 时值为 None，由调用方报「已接入行漏记 sha」。
    """
    path = repo_root / REGISTRY_REL
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return {}, f"无法读取 {REGISTRY_REL}：{e}"
    if ACTIVE_MARKER not in text:
        return {}, (f"{REGISTRY_REL} 缺锚点 {ACTIVE_MARKER}"
                    f"——「已接入」表前必须有它，否则无法机械定位现状行，"
                    f"台账与条目的 sha 一致性检查会整体失效")

    mapping = {}
    for line in text.split(ACTIVE_MARKER, 1)[1].splitlines():
        line = line.strip()
        if line.startswith("#"):
            break
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        name = cells[0].strip("`").strip()
        if not name or set(name) <= set("-: "):   # 跳过分隔行
            continue
        if name == "条目名":                       # 跳过表头
            continue
        found = SHA_IN_TEXT_RE.search(line)
        mapping[name] = found.group(0) if found else None
    return mapping, None


def check_entry(entry, active):
    """校验单条外部引用条目，返回问题描述列表。"""
    name = entry.get("name") or "<无 name 字段>"
    src = entry["source"]
    problems = []

    stype = src.get("source")
    if stype not in ALLOWED_SOURCES:
        problems.append(
            f"[{name}] source.source = {stype!r} 不在允许集合 "
            f"{sorted(ALLOWED_SOURCES)} 内")
    elif stype == "git-subdir" and not src.get("path"):
        problems.append(
            f"[{name}] git-subdir 源缺 path 字段"
            f"——子目录字段名是 path，不是 subdir")

    sha = src.get("sha")
    if not isinstance(sha, str) or not SHA_RE.match(sha):
        problems.append(
            f"[{name}] source.sha = {sha!r} 不是 40 位小写十六进制。"
            f"用 git ls-remote <url> <ref> 取全长值；缩写或缺失会退回"
            f"「跟随分支最新」，更新就不再是人工可控的")

    if "version" in entry:
        problems.append(
            f"[{name}] 条目内不得写 version——它会覆盖 sha 的更新信号，"
            f"且官方在 plugin.json 与 marketplace 条目同时声明时静默忽略后者")

    if entry.get("strict") is False:
        skills = entry.get("skills")
        if not isinstance(skills, list) or not skills:
            problems.append(
                f"[{name}] strict:false 时必须有非空 skills 数组，"
                f"否则外部仓无 plugin.json 时整条加载失败")

    for key in REQUIRED_META:
        if not entry.get(key):
            problems.append(f"[{name}] 缺 {key} 字段——缺失则来源不可追")

    if name not in active:
        problems.append(
            f"[{name}] 未登记在 {REGISTRY_REL} 的「已接入」表"
            f"——接进来但没有记录，下次没人知道它为什么在这里。"
            f"只出现在更新历史里不算：那张表记的是发生过什么，不是现状")
    elif active[name] is None:
        problems.append(
            f"[{name}] 台账「已接入」行没有 40 位 sha，无法与条目比对"
            f"——漏记 sha 会让「更新做了一半」这类状态无人发现")
    elif isinstance(sha, str) and SHA_RE.match(sha) and active[name] != sha:
        problems.append(
            f"[{name}] 台账 sha（{active[name]}）与条目 source.sha（{sha}）不一致。"
            f"这通常意味着上一次更新只做了一半：改了条目没记台账，或回滚了条目"
            f"没回滚台账。先判明哪一个对应实际验证过的状态，再改另一个——"
            f"不要为了消除本条报错而随手对齐")

    return problems


def check_upstream_files(repo_root):
    """拷贝模式：external_plugins/*/ 必须有 UPSTREAM.md 且含 40 位 SHA。

    该目录不存在时视为通过——拷贝模式尚未使用是正常状态。
    """
    base = repo_root / "external_plugins"
    if not base.is_dir():
        return []
    problems = []
    for sub in sorted(base.iterdir()):
        if not sub.is_dir():
            continue
        try:
            text = (sub / "UPSTREAM.md").read_text(encoding="utf-8")
        except OSError:
            problems.append(
                f"[{sub.name}] 缺 external_plugins/{sub.name}/UPSTREAM.md"
                f"——它是拷贝模式唯一的防漂移记账")
            continue
        if not SHA_IN_TEXT_RE.search(text):
            problems.append(
                f"[{sub.name}] UPSTREAM.md 里没有 40 位小写十六进制的 commit SHA，"
                f"无法确定这份副本拷自上游哪一版")
    return problems


def check_all(repo_root):
    """遍历 marketplace.json 的外部引用条目与 external_plugins/，返回全部问题。"""
    repo_root = pathlib.Path(repo_root)
    data, err = _load(repo_root / MARKETPLACE_REL)
    if err:
        return [f"{MARKETPLACE_REL} {err}"]

    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        return [f"{MARKETPLACE_REL} 的 plugins 字段不是数组"]

    # source 为本地相对路径字符串的条目不适用本检查
    external = [p for p in plugins
                if isinstance(p, dict) and isinstance(p.get("source"), dict)]
    if not external:
        return check_upstream_files(repo_root)

    names, err = registry_active(repo_root)
    if err:
        return [err] + check_upstream_files(repo_root)

    problems = []
    for e in external:
        problems.extend(check_entry(e, names))
    problems.extend(check_upstream_files(repo_root))
    return problems


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    problems = check_all(root)
    if problems:
        print("外部引用条目校验未通过：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("外部引用条目校验通过：sha 已锁定、无 version、来源可追、台账已登记且 sha 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
