#!/usr/bin/env python3
"""报告 knowledge-base 索引中疑似语义重复的条目对，结果交由人工确认。

`check_index.py` 的 `check_duplicate_ids` 只查 `id` 字符串重复，挡不住**语义**重复：
同一条约束被两个领域各自写一遍，`id`、`file`、标题措辞全不同。这类重复本仓库踩过两次
（v1.5.0 按单个文件迁移协作条款、漏掉散落在其他文件的同类条款；3.0.0 发现
git ↔ csharp 互认权威却无单一真源的语义环），两次都靠人工通读才发现。

**为什么不能按 tags 交集筛候选：** 3.0.0 那对真实重复
（`csharp.15.quality-gate-overview` tags=[ci, quality-gate] ↔
`git.03.pr-conventions` tags=[git, pull-request]）tags 交集为空——领域名本身占了
一个 tag 位，跨领域条目的 tags 天然不相交。但两者 summary 里「禁止红灯合并」逐字相同。
所以主信号是 title+summary 的词项重叠，tags 只作加分项。

中文无空格分词，用字符 n-gram（bigram + trigram）而非 split()——
「禁止红灯合并」这类短语级重复正是 n-gram 能抓住的。

用法：
    python find_duplicates.py                  # 全库，只报跨领域候选（默认）
    python find_duplicates.py --within-domain  # 同时报领域内候选
    python find_duplicates.py --top 30         # 最多输出 30 对（默认 20）
    python find_duplicates.py --min 0.20       # 相似度下限（默认 0.10）

阈值 0.10 的来由：在 3.0.0 去重前的历史索引上回归测试，该次人工发现的 3 对重复
全部落在前 9 名（分数 0.227 / 0.158 / 0.107），第 5 名起为弱噪音。低于 0.10
的候选人工核对成本超过收益。
"""
import json
import re
import sys
from itertools import combinations
from pathlib import Path

# 结构性/评价性高频词，在规范文本里到处出现，对区分主题没有贡献
STOPWORDS = {
    "禁止", "必须", "应该", "可以", "不得", "须", "要求", "使用", "采用", "遵循",
    "所有", "任何", "每个", "统一", "明确", "保持", "确保", "避免", "优先",
    "以及", "或者", "并且", "而非", "不是", "如果", "当", "时", "的", "了", "和",
    "规范", "规则", "条款", "方式", "形式", "内容", "情况", "场景", "问题",
    "直接", "一律", "默认", "适当", "合理", "正确", "及时", "显式", "隐式",
}

TOKEN_SPLIT_RE = re.compile(r'[^\w一-鿿]+')
CJK_RE = re.compile(r'[一-鿿]')


def ngrams(text, n):
    return {text[i:i + n] for i in range(len(text) - n + 1)}


def tokenize(text):
    """把中英混排文本切成可比较的词项集合。

    英文/数字按分隔符切词；中文段落切成 2/3/4-gram。
    含 4-gram 是为了让「须立即轮换」这类短语级重复能作为**单个** term 存在——
    只有 bigram/trigram 时，长短语只以碎片形式出现，长片段加权永远不会生效。
    命中停用词的 n-gram 直接丢弃，避免"禁止 XX"里的"禁止"贡献相似度。
    """
    terms = set()
    for chunk in TOKEN_SPLIT_RE.split(text.lower()):
        if not chunk:
            continue
        if CJK_RE.search(chunk):
            for n in (2, 3, 4):
                terms |= {g for g in ngrams(chunk, n) if g not in STOPWORDS}
        elif len(chunk) > 1:
            terms.add(chunk)
    return terms


def entry_terms(entry):
    """条目的可比较词项：title + summary 为主信号，tags 单独返回作加分项。"""
    text = f"{entry.get('title', '')} {entry.get('summary', '')}"
    return tokenize(text), {t.lower() for t in entry.get("tags", [])}


def maximal(terms):
    """从 n-gram 集合里只保留极大片段——被更长片段包含的短片段丢弃。

    字符 n-gram 会把一个共现切成多个重叠片段（「禁止直接」→「止直」「止直接」
    「直接」「禁止直」），若逐个计分，一次巧合共现会被重复计四次，把无关条目
    推上榜首。只按极大片段计分，一次共现只算一次。
    """
    ordered = sorted(terms, key=len, reverse=True)
    kept = []
    for t in ordered:
        if not any(t in k for k in kept):
            kept.append(t)
    return kept


def is_structural(phrase):
    """结构性短语：由停用词加少量字构成，表达"怎么说"而非"说什么"。

    「禁止直接」「必须使用」这类在规范文本里到处出现，共现不代表主题相同。
    停用词只做等值匹配不够——得剥掉停用词前后缀后看剩下多少实质内容。
    """
    residue = phrase
    for w in STOPWORDS:
        if residue.startswith(w):
            residue = residue[len(w):]
        if residue.endswith(w):
            residue = residue[:-len(w)]
    return len(residue) < 2


def substantive_overlap(a_terms, b_terms):
    """共有片段中真正有主题含义的极大片段。

    两步过滤，顺序不能反：
    1. 先取极大片段（丢掉被更长片段包含的碎片）——此时若最长片段是结构性的
       （如「禁止直接」），它的跨词边界碎片（如「止直」）会一并被丢掉。
    2. 再剔除结构性极大片段本身。

    若反过来先剔结构性片段，「禁止直接」会被剔掉，而它的碎片「止直」因不含完整
    停用词逃过过滤，反而成为极大片段被计分——一个纯语法共现就伪装成了主题重叠。
    """
    peaks = maximal(a_terms & b_terms)
    return [p for p in peaks if not is_structural(p)]


def similarity(a_terms, b_terms, a_tags, b_tags):
    """极大共有片段的覆盖率 + 长片段加权 + tags 加分。

    不用标准 Jaccard（交集/并集）：规范 summary 长度差异大，长条目会把分母撑大，
    把真重复稀释到噪音水位以下（实测 3.0.0 那对已知重复的 Jaccard 仅 0.058，
    低于同批纯巧合词项对）。改用**重叠占较短一方的比例**，长度不再惩罚重叠本身。
    """
    if not a_terms or not b_terms:
        return 0.0
    peaks = substantive_overlap(a_terms, b_terms)
    if not peaks:
        return 0.0
    coverage = len(peaks) / min(len(maximal(a_terms)), len(maximal(b_terms)))
    long_shared = sum(1 for t in peaks if len(t) >= 4 and CJK_RE.search(t))
    phrase_weight = min(long_shared * 0.06, 0.30)
    tag_bonus = min(len(a_tags & b_tags) * 0.04, 0.08)
    return coverage + phrase_weight + tag_bonus


def stitch(fragments):
    """把首尾重叠的 n-gram 拼回连续片段，供人阅读。

    「视为已泄露须立即轮换」被切成 7 个 4-gram（视为已泄/为已泄露/…/立即轮换），
    直接展示等于给人看同一短语的 7 个滑动窗口。按重叠关系合并后只剩 1 条。
    单趟合并不够——合并产生的新片段可能又与另一段重叠，须迭代到不动点。
    计分不用这个结果——计分看片段数量，合并会改变权重语义。
    """
    parts = maximal(set(fragments))
    changed = True
    while changed:
        changed = False
        for i, j in combinations(range(len(parts)), 2):
            merged = _join(parts[i], parts[j]) or _join(parts[j], parts[i])
            if merged:
                parts = [p for k, p in enumerate(parts) if k not in (i, j)] + [merged]
                parts = maximal(set(parts))
                changed = True
                break
    return sorted(parts, key=len, reverse=True)


def _join(head, tail):
    """head 的后缀与 tail 的前缀重叠时返回拼接结果，否则 None。"""
    for k in range(min(len(head), len(tail)) - 1, 0, -1):
        if head[-k:] == tail[:k]:
            return head + tail[k:]
    return None


def shared_phrases(a_terms, b_terms, limit=5):
    """挑出共有实质片段作为人工判断依据——相似度分数本身不解释重复在哪。"""
    return stitch(substantive_overlap(a_terms, b_terms))[:limit]


def load_all(base_dir):
    """返回 [(domain, entry)]，只含 kind=rule——reference 是描述性文档，重复是正常的。"""
    records = []
    for index_path in sorted(base_dir.glob("*/index.jsonl")):
        domain = index_path.parent.name
        for line in index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("kind") == "rule":
                records.append((domain, entry))
    return records


def find_candidates(records, min_score, cross_domain_only):
    prepared = [(d, e) + entry_terms(e) for d, e in records]
    pairs = []
    for (da, ea, ta, ga), (db, eb, tb, gb) in combinations(prepared, 2):
        if cross_domain_only and da == db:
            continue
        score = similarity(ta, tb, ga, gb)
        if score >= min_score:
            pairs.append((score, da, ea, db, eb, shared_phrases(ta, tb)))
    pairs.sort(key=lambda p: -p[0])
    return pairs


def main():
    base_dir = Path(__file__).resolve().parents[4] / "knowledge-base"
    args = sys.argv[1:]
    cross_only = "--within-domain" not in args
    top = int(args[args.index("--top") + 1]) if "--top" in args else 20
    min_score = float(args[args.index("--min") + 1]) if "--min" in args else 0.10

    records = load_all(base_dir)
    pairs = find_candidates(records, min_score, cross_only)

    scope = "跨领域" if cross_only else "全部（含领域内）"
    print(f"语义重复候选（{scope}，相似度 ≥ {min_score}，共 {len(records)} 条 rule 参与比对）")
    if not pairs:
        print("未发现候选。注意：这不证明没有重复——措辞完全不同的重复无法靠词项重叠发现。")
        return 0

    print(f"命中 {len(pairs)} 对，按相似度降序输出前 {min(top, len(pairs))} 对：\n")
    for score, da, ea, db, eb, phrases in pairs[:top]:
        print(f"[{score:.3f}] {ea['id']}  ↔  {eb['id']}")
        print(f"        {da}: {ea['title']}")
        print(f"        {db}: {eb['title']}")
        if phrases:
            print(f"        共有词项：{'、'.join(phrases)}")
        print(f"        正文：{da}/{ea['file']} § {ea['anchor']}")
        print(f"              {db}/{eb['file']} § {eb['anchor']}")
        print()

    print("以上仅为候选，须人工确认。判断要点：")
    print("  - 真重复：同一条约束被两处各自完整表述 → 按领域职责归入一处，另一处改为引用")
    print("  - 非重复：通用规则在通用领域、技术特有细化在技术领域，是既定分层")
    print("  - 语义环：两处互相「联动」对方却都不承载完整规则 → 无单一真源，须打破")
    return 0


if __name__ == "__main__":
    sys.exit(main())
