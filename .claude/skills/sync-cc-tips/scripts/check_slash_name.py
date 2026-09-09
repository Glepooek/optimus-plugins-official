#!/usr/bin/env python3
"""校验斜杠名在本机 claude 二进制里是否真实存在，供 sync-cc-tips 第三步使用。

**危害不在分类标签错，在斜杠名不存在。** tips 的载体是 SessionStart 单条轮播，
读者照着敲一个不存在的 `/xxx` 时既无法追问也无法查证。2026-09-04 全量核对查出
3 条问题：`statusline-setup`（内置 subagent，没有斜杠命令）、`init`（v2.1.266
已移除）、`security-review`。

输出 JSON 到 stdout，含 verdict 与**证据原文**。

## 本脚本不下最终结论

`verdict` 给的是模式匹配结果，`evidence` 给的是命中处的上下文原文。是否为注册体
须由调用方看 evidence 判断——`name:"init"` 这类短名会命中 JS 解析器的无关字符串，
只看命中数会误判。**脚本负责取证，判断留给读到证据的人。**

## 不要试图判定「是 skill 还是命令」

该区分在 v2.1.266 已不存在：`--help` 明写 "Skills still resolve via
`/skill-name`"、`--disable-slash-commands` 的说明是 "Disable all skills"，
二者是同一套注册。为此迭代四轮的判据全部被推翻，记录见 known-issues.md。
要校验的只有一件事：**这个斜杠名在本机二进制里真实存在吗。**

## 四条已踩过的坑（正则设计即由此而来）

1. **不按调用形态提取「清单」。** 泛匹配 `\\({name:"` 返回 36 项、抽样交叉验证
   也过，但按前缀分组是 12 个互不相干的函数（含 `property(`/`create(` 被吃掉
   词尾的噪音）。「命令跑通且数字属实」≠「输出能支撑那个判断」。故本脚本只做
   单名点查，不提供「列出全部命令」功能。
2. **不写死注册函数的混淆名。** `no({name:"` 在 v2.1.266 已变成 `po({name:"`
   ——短标识符每次构建都可能重命名。稳定锚点是**语义字段名**（`name:`、
   `agentType:`），源码里写死、不参与混淆。
3. **常量表不能当存在性证据。** 形如 `uL="code-review"` 的表是「需特殊处理的
   名字」，内置与插件项混在一起。故只认 `name:"x"` 形态。
4. **正则写窄会把「存在」误判成「不存在」**，方向恰好是最危险的一侧。曾用
   `name:"x",menuDescription`（要求紧邻），漏掉 `name:"doctor",aliases:[…]`
   这类中间插字段的写法。窗口取 200 正是为此——`fewer-permission-prompts` 的
   `requires:{workspace:!0}` 挡在前面，窗口 80 就漏判。

## 退出码

| 码 | 含义 |
|---|---|
| 0 | 查证完成（verdict 见输出，not_found 也算查证完成） |
| 2 | 参数非法 |
| 5 | 二进制不存在或不可读 |
"""

import argparse
import json
import os
import re
import sys

# 默认二进制路径（npm 全局安装）。找不到时输出 binary_missing 并给出定位建议。
DEFAULT_BINARY = os.path.expanduser(
    "~/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe"
)

# 命中窗口。200 是实测下限——见模块 docstring 第 4 条。
WINDOW = 200
SUBAGENT_WINDOW = 80

# 一次读入的块大小。二进制约 200MB，分块扫描避免整体载入内存。
# 块间重叠 WINDOW*2 保证跨块边界的匹配不丢。
CHUNK = 8 * 1024 * 1024

# 注册体的伴随字段。命中其一说明这是真实注册项而非无关字符串。
REGISTRY_MARKERS = (
    "description",
    "menuDescription",
    "aliases",
    "isEnabled",
    "requires",
    "argNames",
    "progressMessage",
)

def build_patterns(name):
    """按名字构造两条模式。

    语义字段名做锚点（`name:` / `agentType:`），不写死混淆过的函数名——
    后者每次构建都可能重命名（`no(` → `po(`），写死等于给自己埋一个静默失效。
    """
    q = re.escape(name)
    return {
        "name": re.compile(rf'name:"{q}"(.{{0,{WINDOW}}})', re.S),
        "agentType": re.compile(rf'agentType:"{q}"(.{{0,{SUBAGENT_WINDOW}}})', re.S),
    }


def scan(path, name, max_hits=3):
    """分块扫描二进制，返回 {"name": [...], "agentType": [...]} 的命中上下文。

    二进制约 200MB，分块读并让相邻块重叠，避免跨块边界的匹配被切断。

    去重按**全局字节偏移**而非上下文文本：重叠区里同一命中在两个块中的窗口长度
    可能不同（块尾被截断），比文本会漏掉重复，导致 hit_counts 虚高。
    """
    pats = build_patterns(name)
    hits = {"name": [], "agentType": []}
    seen = {"name": set(), "agentType": set()}
    overlap = WINDOW * 2

    with open(path, "rb") as f:
        tail = ""
        # tail 在原文件中的起始偏移，用于把块内位置换算成全局位置
        base = 0
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            text = tail + block.decode("latin-1")
            for key, pat in pats.items():
                if len(hits[key]) >= max_hits:
                    continue
                for m in pat.finditer(text):
                    pos = base + m.start()
                    if pos in seen[key]:
                        continue
                    seen[key].add(pos)
                    hits[key].append(m.group(0))
                    if len(hits[key]) >= max_hits:
                        break
            new_tail = text[-overlap:]
            base += len(text) - len(new_tail)
            tail = new_tail
            if all(len(v) >= max_hits for v in hits.values()):
                break
    return hits


def looks_like_registry(context):
    """命中处是否像注册体。

    只作为**提示**返回给调用方，不用来过滤——判断权在读到证据的人。
    `name:"init"` 会命中 JS 解析器的无关字符串，但过滤掉就可能误伤真实注册项。
    """
    return [m for m in REGISTRY_MARKERS if m in context]


# verdict → SKILL.md 的处置建议。四种取值与原表四行一一对应。
ACTIONS = {
    "command": "斜杠名存在，按功能性质选分类",
    "subagent": "是 subagent，不写斜杠形式，改述为「内置 subagent」",
    "not_found": "不写斜杠形式；若 changelog 明确提到它，可能来自插件——确认插件名后须带命名空间前缀，否则列入摘要交用户裁决",
    "binary_missing": "二进制未找到，改述为功能描述并在摘要注明「斜杠名未验证」",
}


def decide(hits):
    """由命中情况定 verdict。

    agentType 优先于 name：一个名字同时命中两者时它是 subagent，
    不该写成斜杠命令（statusline-setup 就是这种情况）。
    """
    if hits["agentType"]:
        return "subagent"
    if hits["name"]:
        return "command"
    return "not_found"


def check(name, binary=DEFAULT_BINARY):
    """查证单个斜杠名，返回 (payload, exit_code)。"""
    if not os.path.isfile(binary):
        return {
            "name": name,
            "verdict": "binary_missing",
            "binary": binary,
            "action": ACTIONS["binary_missing"],
            "hint": "用 (Get-Command claude).Source 定位实际路径后传 --binary 重试",
        }, 5

    try:
        hits = scan(binary, name)
    except OSError as e:
        return {
            "name": name,
            "verdict": "binary_missing",
            "binary": binary,
            "action": ACTIONS["binary_missing"],
            "hint": f"读取失败: {e}",
        }, 5

    verdict = decide(hits)
    evidence = []
    for key in ("name", "agentType"):
        for ctx in hits[key]:
            evidence.append({
                "anchor": f"{key}:",
                "registry_markers": looks_like_registry(ctx),
                "context": ctx,
            })

    payload = {
        "name": name,
        "verdict": verdict,
        "binary": binary,
        "action": ACTIONS[verdict],
        "hit_counts": {k: len(v) for k, v in hits.items()},
        # 证据原文交调用方判断是否为注册体——脚本不做这个判断，见模块 docstring
        "evidence": evidence,
    }
    if verdict == "command" and not any(e["registry_markers"] for e in evidence):
        payload["warning"] = (
            "命中 name: 但上下文无任何注册体伴随字段，可能是无关字符串。"
            "加长窗口复查或列入摘要交用户裁决。"
        )
    return payload, 0


def main(argv):
    p = argparse.ArgumentParser(
        prog="check_slash_name.py",
        description="校验斜杠名在本机 claude 二进制里是否真实存在，输出 JSON。",
        epilog=(
            "示例：\n"
            "  python scripts/check_slash_name.py doctor\n"
            "  python scripts/check_slash_name.py statusline-setup\n"
            "  python scripts/check_slash_name.py foo --binary /path/to/claude.exe\n"
            "\nverdict：command / subagent / not_found / binary_missing\n"
            "退出码：0 查证完成 / 2 参数非法 / 5 二进制不可读\n"
            "\n注意：本脚本只取证不下结论——evidence 里的上下文原文需调用方自行判断"
            "是否为注册体。name:\"init\" 会命中 JS 解析器的无关字符串。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("name", help="待查证的斜杠名，不带前导 /")
    p.add_argument(
        "--binary",
        default=DEFAULT_BINARY,
        metavar="PATH",
        help="claude 二进制路径（默认 npm 全局安装位置）",
    )
    args = p.parse_args(argv[1:])

    name = args.name.lstrip("/")
    if not name or not re.fullmatch(r"[A-Za-z0-9:_-]+", name):
        print(
            f"错误: 斜杠名只能含字母数字与 : _ -，收到 {args.name!r}",
            file=sys.stderr,
        )
        return 2

    payload, code = check(name, args.binary)
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
