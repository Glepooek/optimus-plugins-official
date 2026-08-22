#!/usr/bin/env python3
"""校验 knowledge-base/<domain>/index.jsonl 与实际文件的一致性。

三类检查：file 是否存在、anchor 对应标题是否存在、id 是否全局唯一。
"""
import json
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')


def normalize_heading(line):
    m = HEADING_RE.match(line.strip())
    text = m.group(2) if m else line.strip()
    text = text.replace("`", "")
    return re.sub(r'\s+', ' ', text).strip()


def find_headings(text):
    headings = []
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            headings.append(normalize_heading(line))
    return headings
