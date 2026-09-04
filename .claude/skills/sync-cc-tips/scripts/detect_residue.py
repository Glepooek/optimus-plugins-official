#!/usr/bin/env python3
"""检测 tips.jsonl 库内已有条目之间的互相覆盖（"残影"），供 sync-cc-tips 第二步使用。

判重是单向的（changelog 新条目 vs 已有条目），检测不到**已有条目之间**的冗余。
这类冗余由历次 sync 累积产生，每次单看都不重复——三条 `/code-review` 中一条纯
泛述被另两条完全覆盖，就是这样攒出来的。

召回需同时满足两个条件，缺一不可：
1. 主标识符相同（从 id 提取的核心命令名）——只有讲同一个东西才谈得上覆盖；
2. 功能描述有实质重叠（`功能：` 段落的 bigram 集合达到阈值包含关系）。

只用条件 1 会把讲同一命令不同侧面的条目全部召回（requesting-code-review 与
receiving-code-review 主标识符相同但功能互不覆盖）；只用条件 2 会把泛泛而谈的
不同功能条目凑成一对。

**输出是待人工裁决的候选，不是判定结果。** 实测表明真残影与非残影的重叠率在
数值上有交叠区（见 OVERLAP_THRESHOLD 注释），纯词频无法可靠区分，故本脚本
只保证召回，最终取舍由 SKILL.md 第四步的 CHECKPOINT 交给用户。

输出 JSON 到 stdout：{"candidates": [{"covers": id, "covered": id, "overlap": 0.0}], "stats": {...}}
"""

import json
import re
import sys

DEFAULT_TIPS = "plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl"

# 功能描述重叠比例阈值。
#
# 该值按实测分布选定，不是凭感觉给的：276 条库内同主标识符分组的两两覆盖率
# 落在 0.037~0.875 之间，人工确认的真残影（/doctor 那两条互为详略版本）只有
# 0.263，而非残影的 MCP-资源列出 ⊇ MCP-服务器 却有 0.333——**两类在数值上重叠**。
#
# 纯词频方法到此为止：同一功能的不同详略版本用词可以差很远，不同功能的同域
# 条目用词可以很接近。因此本检测器只做**召回**，阈值取到能捞出真残影为止，
# 输出一律是「待人工裁决的候选」而非「确认残影」——工具负责别漏，人负责别错杀。
OVERLAP_THRESHOLD = 0.25

# 实词提取时剔除的高频虚词，它们在任何两条之间都重叠，会抬高相似度
STOPWORDS = frozenset("""
的 了 在 是 与 和 或 把 从 到 对 为 用 可 会 不 也 都 就 只 而 等 时 后 前
起 过 中 上 下 内 外 个 条 次 种 类 些 该 其 此 这 那 你 我 它 们 更 再 已
支持 使用 可以 能够 需要 通过 进行 提供 表示 例如 如下 以及 或者 而是 不是
""".split())


def main_identifier(entry_id):
    """从 id 提取主标识符：首个斜杠命令 / flag / 英文短语，用于判断"是否在讲同一个东西"。

    id 形如 `/code-review-审查当前改动`、`requesting-code-review-请求代码审查`、
    `defaultMode-权限模式`。取其中的 ASCII 部分作为主标识符。
    """
    ascii_part = re.match(r'^[\x00-\x7f]+', entry_id.strip())
    if not ascii_part:
        return entry_id.strip().lower()
    return ascii_part.group(0).strip('-_ ').lower()


def feature_terms(body):
    """提取 `功能：` 段落的实词集合。没有该段落时退回整个 body。

    中文按 **bigram（2-gram）** 切分而非按连续片段整取：无分词器时，
    `是完整的配置体检工具` 整取会成为单个 token，与另一条的 `设置体检` 永不重合；
    切成 `配置`/`置体`/`体检` 后，断句差异不再影响重叠度。
    英文与标识符按词切。
    """
    m = re.search(r'功能：(.*?)(?:\n效果：|\n例子：|$)', body, re.S)
    text = m.group(1) if m else body

    terms = set()
    # 英文单词与标识符
    for tok in re.findall(r'[A-Za-z_][\w.-]{2,}', text):
        t = tok.lower()
        if t not in STOPWORDS:
            terms.add(t)
    # 中文 bigram
    for run in re.findall(r'[一-鿿]{2,}', text):
        for i in range(len(run) - 1):
            bg = run[i:i + 2]
            if bg not in STOPWORDS:
                terms.add(bg)
    return terms


def overlap_ratio(a, b):
    """b 被 a 覆盖的比例：|a∩b| / |b|。b 为空时返回 0。"""
    if not b:
        return 0.0
    return len(a & b) / len(b)


def detect(path=DEFAULT_TIPS, threshold=OVERLAP_THRESHOLD):
    """读 tips.jsonl，返回 (candidates, stats)。"""
    items = []
    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno} JSON 解析失败: {e}") from e
            entry_id = obj.get('id', '').strip()
            if not entry_id:
                continue
            items.append({
                'id': entry_id,
                'main': main_identifier(entry_id),
                'terms': feature_terms(obj.get('body', '')),
            })

    candidates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i == j:
                continue
            a, b = items[i], items[j]
            # 条件 1：主标识符相同
            if a['main'] != b['main']:
                continue
            # 条件 2：a 的功能描述覆盖 b 达到阈值
            ratio = overlap_ratio(a['terms'], b['terms'])
            if ratio < threshold:
                continue
            # a 覆盖 b 且 a 不比 b 更简短——更简短者不可能"完全覆盖"更详尽者
            if len(a['terms']) < len(b['terms']):
                continue
            candidates.append({
                'covers': a['id'],
                'covered': b['id'],
                'overlap': round(ratio, 3),
            })

    # 同一 main 分组统计，便于人工快速定位
    groups = {}
    for it in items:
        groups.setdefault(it['main'], []).append(it['id'])
    multi = {k: v for k, v in groups.items() if len(v) > 1}

    stats = {
        'entries': len(items),
        'candidates': len(candidates),
        'shared_main_groups': len(multi),
        'threshold': threshold,
    }
    return candidates, multi, stats


def main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT_TIPS
    try:
        candidates, multi, stats = detect(path)
    except (OSError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    json.dump(
        {'candidates': candidates, 'shared_main': multi, 'stats': stats},
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
