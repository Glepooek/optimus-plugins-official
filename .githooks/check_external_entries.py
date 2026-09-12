#!/usr/bin/env python3
"""校验 .claude-plugin/marketplace.json 的条目合规，以及插件目录的机械可判约束。

只查机械可判定项，一律不联网——提交门禁联网会让离线提交失败，代价大于收益。
因此本脚本保证的是「条目结构正确、来源可追」，不保证条目指向的内容真的存在、
真的是 skill、或真的还在维护；后者由实际安装验证与人承担。

两类检查，判据不同：

- **外部引用条目**（source 为 url/github/git-subdir）：sha 锁定、无 version、
  来源可追、台账已登记且 sha 一致。设计依据
  docs/superpowers/specs/2026-09-12-add-external-skill-design.md
- **全部条目与插件目录**：marketplace 与条目名的保留名与字符集、本地路径源的
  形态、relevance 字段上限、.claude-plugin/ 目录内容。判据是
  knowledge-base/claude-code-plugin-system/ 的索引条目，报错携带条目 ID
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

# Anthropic 官方保留的 marketplace 名（claude-code-plugin-system.03.reserved-names）。
# 保留名在每次加载 marketplace 时重新检查而非只在添加时，所以用了保留名的仓库
# 会在某个版本后直接停止加载——这是提交时就该拦住的。
RESERVED_MARKETPLACE_NAMES = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
    "claude-plugins-community", "claude-community", "anthropic-marketplace",
    "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
    "knowledge-work-plugins", "life-sciences", "claude-for-legal",
    "claude-for-financial-services", "financial-services-plugins",
    "first-party-plugins", "claude-tag-plugins", "healthcare",
}
# Claude Desktop 另有三个保留 marketplace 名，任意大小写
# （claude-code-plugin-system.03.downstream-sync-name-limits）
DESKTOP_RESERVED_NAMES = {"org", "org-provisioned", "unknown"}

# Claude Desktop 托管同步的字符集：≤128 字符、字母数字与 . _ -、首字符为字母或数字
DOWNSTREAM_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
# kebab-case：claude.ai marketplace 同步的要求，Claude Code 自身只给警告
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# relevance 信号的 (条数上限, 每条字符上限)
# （claude-code-plugin-system.07.relevance-signal-semantics）
SIGNAL_LIMITS = {
    "cwd": (10, 256),
    "cli": (10, 64),
    "hosts": (20, 128),
    "filesRead": (10, 256),
    "manifestDeps": (10, 256),
}
TOPIC_MAX = 64
# 裸小写主机名：无方案、端口或路径
BARE_HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")



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


def check_marketplace_name(data):
    """校验顶层 marketplace name 的保留名与字符集。"""
    problems = []
    name = data.get("name")
    if not isinstance(name, str) or not name:
        return [f"{MARKETPLACE_REL} 缺顶层 name 字段"
                f"（判据 claude-code-plugin-system.03.required-fields）"]

    if name in RESERVED_MARKETPLACE_NAMES:
        problems.append(
            f"marketplace 名 {name!r} 是 Anthropic 官方保留名，第三方不得使用。"
            f"保留名在每次加载时重新检查而非只在添加时，所以这不是「先用着以后再说」"
            f"——某个版本起该 marketplace 会直接停止加载并报「从不受信任的来源注册」"
            f"（判据 claude-code-plugin-system.03.reserved-names）")
    if name.lower() in DESKTOP_RESERVED_NAMES:
        problems.append(
            f"marketplace 名 {name!r} 是 Claude Desktop 的保留名（任意大小写），"
            f"Claude Code 接受但 Claude Desktop 会拒绝整个 marketplace"
            f"（判据 claude-code-plugin-system.03.downstream-sync-name-limits）")
    problems.extend(_check_name_charset(name, "marketplace 名"))
    return problems


def _check_name_charset(name, label):
    """kebab-case 与 Claude Desktop 字符集，两条都只在下游同步时才致命。"""
    problems = []
    if not DOWNSTREAM_NAME_RE.match(name):
        problems.append(
            f"{label} {name!r} 不满足 Claude Desktop 托管同步的字符集"
            f"（≤128 字符、仅字母数字与 . _ -、以字母或数字开头）"
            f"（判据 claude-code-plugin-system.03.downstream-sync-name-limits）")
    if not KEBAB_RE.match(name):
        problems.append(
            f"{label} {name!r} 不是 kebab-case，claude.ai marketplace 同步会拒绝"
            f"（判据 claude-code-plugin-system.01.name-constraints）")
    return problems


def check_local_source(entry, repo_root, has_plugin_root):
    """校验 source 为本地路径字符串的条目：./ 前缀、无 ..、无反斜杠、目标存在。"""
    name = entry.get("name") or "<无 name 字段>"
    src = entry["source"]
    problems = []

    if "\\" in src:
        problems.append(
            f"[{name}] source {src!r} 含反斜杠——macOS 与 Linux 拒绝这类条目路径，"
            f"分隔符必须在每个平台都写 /"
            f"（判据 claude-code-plugin-system.04.relative-path-and-plugin-root）")
    if ".." in src.split("/"):
        problems.append(
            f"[{name}] source {src!r} 含 ..，禁止引用 marketplace 根之外的路径"
            f"（判据 claude-code-plugin-system.02.path-escape）")
    if not src.startswith("./"):
        if "/" in src or not has_plugin_root:
            problems.append(
                f"[{name}] source {src!r} 必须以 ./ 开头。裸名只在设了"
                f" metadata.pluginRoot 时成立，且含 / 的路径不是裸名"
                f"（判据 claude-code-plugin-system.04.relative-path-and-plugin-root）")

    target = (repo_root / src.lstrip("./")) if src.startswith("./") else None
    if target is not None and ".." not in src.split("/") and not target.is_dir():
        problems.append(
            f"[{name}] source {src!r} 指向的目录不存在——条目会在安装时失败"
            f"（判据 claude-code-plugin-system.04.relative-path-and-plugin-root）")
    return problems


def check_relevance(entry):
    """校验 relevance 的 topic 长度、signals 键名与各信号的条数与长度上限。"""
    name = entry.get("name") or "<无 name 字段>"
    rel = entry.get("relevance")
    if rel is None:
        return []
    tag = "（判据 claude-code-plugin-system.07.relevance-signal-semantics）"
    if not isinstance(rel, dict):
        return [f"[{name}] relevance 必须是对象{tag}"]

    problems = []
    topic = rel.get("topic")
    if topic is not None:
        if not isinstance(topic, str):
            problems.append(f"[{name}] relevance.topic 必须是字符串"
                            f"（判据 claude-code-plugin-system.07.relevance-fields-surfaces）")
        elif len(topic) > TOPIC_MAX:
            problems.append(
                f"[{name}] relevance.topic 长 {len(topic)} 字符，上限 {TOPIC_MAX}"
                f"（判据 claude-code-plugin-system.07.relevance-fields-surfaces）")

    signals = rel.get("signals")
    if not isinstance(signals, dict) or not signals:
        return problems + [
            f"[{name}] relevance.signals 必须是至少含一个信号的对象，"
            f"否则插件永不会被建议"
            f"（判据 claude-code-plugin-system.07.relevance-fields-surfaces）"]

    for key, values in signals.items():
        if key not in SIGNAL_LIMITS:
            problems.append(
                f"[{name}] 未知信号名 {key!r}（合法值：{sorted(SIGNAL_LIMITS)}）"
                f"——未知字段在加载时被忽略，拼错只会静默不匹配{tag}")
            continue
        max_count, max_len = SIGNAL_LIMITS[key]
        if not isinstance(values, list):
            problems.append(f"[{name}] signals.{key} 必须是数组{tag}")
            continue
        if len(values) > max_count:
            problems.append(
                f"[{name}] signals.{key} 有 {len(values)} 条，上限 {max_count}{tag}")
        problems.extend(_check_signal_values(name, key, values, max_len, tag))
    return problems


def _check_signal_values(name, key, values, max_len, tag):
    """逐条校验信号值：长度、hosts 的裸主机名形态、manifestDeps 的末尾锚定。"""
    problems = []
    for i, v in enumerate(values):
        if key == "manifestDeps":
            if not isinstance(v, dict):
                problems.append(f"[{name}] signals.manifestDeps[{i}] 必须是对象{tag}")
                continue
            for field in ("file", "pattern"):
                fv = v.get(field)
                if not isinstance(fv, str) or not fv:
                    problems.append(
                        f"[{name}] signals.manifestDeps[{i}].{field} 必须是非空字符串{tag}")
                elif len(fv) > max_len:
                    problems.append(
                        f"[{name}] signals.manifestDeps[{i}].{field} 长 {len(fv)} 字符，"
                        f"上限 {max_len}{tag}")
            fpat = v.get("file")
            if isinstance(fpat, str) and fpat and not fpat.endswith("$"):
                problems.append(
                    f"[{name}] signals.manifestDeps[{i}].file 未在末尾锚定（缺 $）"
                    f"——清单路径按会话状态记录，通常是绝对路径，"
                    f"起始锚定的模式永远不会匹配"
                    f"（判据 claude-code-plugin-system.07.relevance-signal-semantics）")
            continue

        if not isinstance(v, str) or not v:
            problems.append(f"[{name}] signals.{key}[{i}] 必须是非空字符串{tag}")
            continue
        if len(v) > max_len:
            problems.append(
                f"[{name}] signals.{key}[{i}] 长 {len(v)} 字符，上限 {max_len}{tag}")
        if key == "hosts" and not BARE_HOST_RE.match(v):
            problems.append(
                f"[{name}] signals.hosts[{i}] = {v!r} 必须是裸小写主机名"
                f"——不含方案、端口或路径，validate 会拒绝这类条目{tag}")
    return problems


def check_plugin_dirs(repo_root):
    """.claude-plugin/ 里只能有 plugin.json（仓库根另可有 marketplace.json）。

    放错位置的组件目录不会报错，插件照常加载、显示为启用，组件却全部不出现
    ——所以这是提交时就该拦住的一类，不能指望运行时发现。
    """
    problems = []
    allowed = {
        repo_root / ".claude-plugin": {"marketplace.json", "plugin.json"},
    }
    dirs = [repo_root / ".claude-plugin"]
    plugins_dir = repo_root / "plugins"
    if plugins_dir.is_dir():
        for sub in sorted(plugins_dir.iterdir()):
            d = sub / ".claude-plugin"
            if d.is_dir():
                dirs.append(d)
                allowed[d] = {"plugin.json"}

    for d in dirs:
        if not d.is_dir():
            continue
        for item in sorted(d.iterdir()):
            if item.name in allowed[d]:
                continue
            problems.append(
                f"[{d.parent.name}] .claude-plugin/ 内出现 {item.name}"
                f"——该目录只能放 {sorted(allowed[d])}。组件放进去后插件仍正常加载、"
                f"无报错、显示为启用，但组件全部不出现"
                f"（判据 claude-code-plugin-system.02.claude-plugin-dir-only-manifest）")
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
    """遍历 marketplace.json 的全部条目、插件目录与 external_plugins/，返回全部问题。"""
    repo_root = pathlib.Path(repo_root)
    data, err = _load(repo_root / MARKETPLACE_REL)
    if err:
        return [f"{MARKETPLACE_REL} {err}"]

    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        return [f"{MARKETPLACE_REL} 的 plugins 字段不是数组"]

    problems = check_marketplace_name(data)
    has_plugin_root = bool((data.get("metadata") or {}).get("pluginRoot"))

    # source 为本地相对路径字符串的条目不适用 sha 与台账检查，但名字、relevance
    # 与路径形态三项对每个条目一律适用
    external = []
    for p in plugins:
        if not isinstance(p, dict):
            continue
        name = p.get("name")
        if isinstance(name, str) and name:
            problems.extend(_check_name_charset(name, f"条目名"))
        problems.extend(check_relevance(p))
        src = p.get("source")
        if isinstance(src, dict):
            external.append(p)
        elif isinstance(src, str):
            problems.extend(check_local_source(p, repo_root, has_plugin_root))

    if external:
        names, reg_err = registry_active(repo_root)
        if reg_err:
            problems.append(reg_err)
        else:
            for e in external:
                problems.extend(check_entry(e, names))

    problems.extend(check_plugin_dirs(repo_root))
    problems.extend(check_upstream_files(repo_root))
    return problems


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    problems = check_all(root)
    if problems:
        print("marketplace 条目校验未通过：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("marketplace 条目校验通过：名字合规、本地源路径有效、relevance 在限内、"
          "外部条目 sha 已锁定且台账一致、.claude-plugin/ 只含清单")
    return 0


if __name__ == "__main__":
    sys.exit(main())
