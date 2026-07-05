# sync-cc-docs-to-youdaonote Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 `.claude/skills/sync-cc-docs-to-youdaonote/` 这个项目级 skill，按分类路径（如"使用ClaudeCode构建 / Guides"）核对 `docs/claude_docs/catalog.md`、抓取翻译该分类下页面、幂等同步到有道云笔记，文件夹层级与站点导航一致。

**Architecture：** 一个 Python 脚本 `resolve_category.py` 承担两类纯机械工作——① 解析 `catalog.md` 的 Tab/分组/页面结构并支持中英文名双向查找；② 通过 `youdaonote` CLI 查/建有道文件夹（`list` 先查、`mkdir` 仅在缺失时创建、再次 `list` 确认，避免与用户已手动创建的文件夹重名冲突）。页面级幂等判重（`fileId` 记录 + 与远端列表交叉验证）、抓取/翻译/上传的编排逻辑留在 `SKILL.md` 里，由执行时的 Claude 会话直接读写 `folder-map.json` 完成，不固化进脚本。

**Tech Stack：** Python 3.14（标准库 `argparse`/`json`/`re`/`subprocess`/`unittest`，无第三方依赖），`youdaonote` CLI（用户级全局 skill 提供），`markitdown`（web-to-markdown skill 已有约定）。

## Global Constraints

- 仓库根目录：`E:\ProjectxPlex\WPFCodePlex\unipus-plugins-official`
- Skill 目录：`.claude/skills/sync-cc-docs-to-youdaonote/`（项目级，不进 marketplace，`.claude/` 下改动不触发 `.claude-plugin/marketplace.json` 版本号联动）
- 站点导航目录（只读，本 skill 不负责生成/更新）：`docs/claude_docs/catalog.md`
- 有道云笔记 ClaudeCode 根文件夹 ID：`WEBc1d2e6c709ed0850b09f070a86573197`（硬编码常量，绑定个人账号）
- Skill 版本管理：`SKILL.md` frontmatter 维护 `version` 字段，同步维护 `CHANGELOG.md`，初始版本 `1.0.0`，后续新增功能 Minor、修复 Patch、破坏性变更 Major（与 `plugins/` 下 skill 一致的独立语义版本规则，用户已明确要求强制执行）
- 所有子进程调用 `youdaonote` CLI 时必须显式传 `encoding="utf-8"`，避免 Windows 控制台默认编码导致中文乱码
- 不支持一次处理整个 Tab，只支持"Tab / 单个分组"粒度
- 不负责迁移历史遗留文件、不负责维护 `catalog.md`

---

### Task 1: 创建目录骨架，种入已知历史同步状态

**Files:**
- Create: `.claude/skills/sync-cc-docs-to-youdaonote/folder-map.json`
- Create: `.claude/skills/sync-cc-docs-to-youdaonote/scripts/`（空目录，占位供 Task 2 使用）

**Interfaces:**
- Produces: `folder-map.json` 的数据结构约定——顶层 `tabs` 字典以**中文 Tab 名**为 key；每个 Tab 值含 `en`（英文名）、`id`（有道文件夹 ID）、`groups`（字典，以**英文分组名**为 key）；每个分组值含 `en`、`zh`、`id`、`pages`（字典，以页面相对 URL 为 key，值含 `title`、`fileId`）。后续所有任务均依赖此结构。

背景：本次会话已经手动完成"使用ClaudeCode构建 / Automation"分组下 4 篇文档的抓取翻译上传（goal.md→fileId `F5F3AC5D1C9A40CC8F64D5FA284C0CE5`、scheduled-tasks→`712C7470F61340BF88C5D8919C2EC6DB`、headless→`FAAD4D7FC8A64A4D8851335F38974039`、deep-links→`4FF01C36893F4024B7D58955C6DE1419`），且"自动化"文件夹（ID `WEB573ab28c9f02ee4599ace1288819807b`）已存在于"使用ClaudeCode构建"（ID `WEBb2aab5b9ec63445b0c0d299e3b36b96e`）之下。种入这些已知记录，避免未来处理 Automation 分组时对这 4 篇产生重复上传。"自定义hook.note"和"使用 hooks 自动化工作流.note"是用户手写笔记，不对应 catalog.md 的 hooks-guide/channels 页面，按用户决定不纳入映射。

- [ ] **Step 1: 创建 folder-map.json**

```bash
mkdir -p ".claude/skills/sync-cc-docs-to-youdaonote/scripts"
```

写入 `.claude/skills/sync-cc-docs-to-youdaonote/folder-map.json`：

```json
{
  "tabs": {
    "使用ClaudeCode构建": {
      "en": "Build with Claude Code",
      "id": "WEBb2aab5b9ec63445b0c0d299e3b36b96e",
      "groups": {
        "Automation": {
          "en": "Automation",
          "zh": "自动化",
          "id": "WEB573ab28c9f02ee4599ace1288819807b",
          "pages": {
            "/goal": {
              "title": "goal.md",
              "fileId": "F5F3AC5D1C9A40CC8F64D5FA284C0CE5"
            },
            "/scheduled-tasks": {
              "title": "scheduled-tasks.md",
              "fileId": "712C7470F61340BF88C5D8919C2EC6DB"
            },
            "/headless": {
              "title": "run-claude-code-programmatically.md",
              "fileId": "FAAD4D7FC8A64A4D8851335F38974039"
            },
            "/deep-links": {
              "title": "deep-links.md",
              "fileId": "4FF01C36893F4024B7D58955C6DE1419"
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 2: 验证 JSON 有效且结构正确**

Run:
```bash
python -c "
import json
d = json.load(open('.claude/skills/sync-cc-docs-to-youdaonote/folder-map.json', encoding='utf-8'))
assert d['tabs']['使用ClaudeCode构建']['id'] == 'WEBb2aab5b9ec63445b0c0d299e3b36b96e'
assert d['tabs']['使用ClaudeCode构建']['groups']['Automation']['id'] == 'WEB573ab28c9f02ee4599ace1288819807b'
assert d['tabs']['使用ClaudeCode构建']['groups']['Automation']['pages']['/goal']['fileId'] == 'F5F3AC5D1C9A40CC8F64D5FA284C0CE5'
assert len(d['tabs']['使用ClaudeCode构建']['groups']['Automation']['pages']) == 4
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ".claude/skills/sync-cc-docs-to-youdaonote/folder-map.json"
git commit -m "$(cat <<'EOF'
feat(sync-cc-docs-to-youdaonote): 初始化 skill 目录与已知历史同步状态

- 新增 folder-map.json，种入"使用ClaudeCode构建/Automation"分组已同步的 4 篇文档记录
- 避免未来处理该分组时对已上传文档产生重复

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: catalog.md 解析纯函数（TDD）

**Files:**
- Create: `.claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py`
- Test: `.claude/skills/sync-cc-docs-to-youdaonote/scripts/test_resolve_category.py`

**Interfaces:**
- Produces:
  - `parse_catalog(text: str) -> list[dict]`：返回 `[{"en": str, "zh": str|None, "groups": [{"en": str, "pages": [{"title": str, "url": str}]}]}]`
  - `find_tab(tabs: list[dict], folder_map: dict, name: str) -> dict|None`
  - `find_group(tab: dict, name: str) -> dict|None`

- [ ] **Step 1: 写失败的单元测试**

创建 `.claude/skills/sync-cc-docs-to-youdaonote/scripts/test_resolve_category.py`：

```python
import unittest
from resolve_category import parse_catalog, find_tab, find_group

SAMPLE_CATALOG = """\
## Tab 1 — Getting started（入口：`/overview`）

### Getting started
- [ ] Overview — `/overview`
- [ ] Quickstart — `/quickstart`

## Tab 2 — Build with Claude Code（对应有道笔记"使用ClaudeCode构建"，入口：`/agents`）

### Automation
- [x] Goals — `/goal`
- [ ] Launch sessions from links — `/deep-links`

### Guides
- [x] Monorepos and large repos — `/large-codebases`

### Plugin distribution（当前处理中，对应有道笔记"管理 / 插件分发"）
- [ ] Create and distribute a plugin marketplace — `/plugin-marketplaces`
"""


class TestParseCatalog(unittest.TestCase):
    def test_parses_all_tabs(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        self.assertEqual(len(tabs), 2)

    def test_tab_without_zh_annotation(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        self.assertEqual(tabs[0]["en"], "Getting started")
        self.assertIsNone(tabs[0]["zh"])

    def test_tab_with_zh_annotation(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        self.assertEqual(tabs[1]["en"], "Build with Claude Code")
        self.assertEqual(tabs[1]["zh"], "使用ClaudeCode构建")

    def test_group_with_trailing_annotation_still_parses_name(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        group_names = [g["en"] for g in tabs[1]["groups"]]
        self.assertIn("Plugin distribution", group_names)

    def test_parses_pages_under_group(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        guides = next(g for g in tabs[1]["groups"] if g["en"] == "Guides")
        self.assertEqual(
            guides["pages"],
            [{"title": "Monorepos and large repos", "url": "/large-codebases"}],
        )

    def test_parses_multiple_pages(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        automation = next(g for g in tabs[1]["groups"] if g["en"] == "Automation")
        self.assertEqual(len(automation["pages"]), 2)
        self.assertEqual(automation["pages"][0]["url"], "/goal")
        self.assertEqual(automation["pages"][1]["url"], "/deep-links")


class TestFindTab(unittest.TestCase):
    def test_find_by_english_name(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        tab = find_tab(tabs, {}, "Build with Claude Code")
        self.assertIsNotNone(tab)
        self.assertEqual(tab["en"], "Build with Claude Code")

    def test_find_by_chinese_name_from_catalog_annotation(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        tab = find_tab(tabs, {}, "使用ClaudeCode构建")
        self.assertIsNotNone(tab)
        self.assertEqual(tab["en"], "Build with Claude Code")

    def test_find_by_chinese_name_from_folder_map_alias(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        folder_map = {"tabs": {"入门": {"en": "Getting started"}}}
        tab = find_tab(tabs, folder_map, "入门")
        self.assertIsNotNone(tab)
        self.assertEqual(tab["en"], "Getting started")

    def test_not_found_returns_none(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        self.assertIsNone(find_tab(tabs, {}, "Nonexistent Tab"))


class TestFindGroup(unittest.TestCase):
    def test_find_existing_group(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        tab = find_tab(tabs, {}, "使用ClaudeCode构建")
        group = find_group(tab, "Guides")
        self.assertIsNotNone(group)
        self.assertEqual(len(group["pages"]), 1)

    def test_group_not_found_returns_none(self):
        tabs = parse_catalog(SAMPLE_CATALOG)
        tab = find_tab(tabs, {}, "使用ClaudeCode构建")
        self.assertIsNone(find_group(tab, "Nonexistent Group"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
cd ".claude/skills/sync-cc-docs-to-youdaonote/scripts" && python -m unittest test_resolve_category -v
```
Expected: `ModuleNotFoundError: No module named 'resolve_category'`（文件尚不存在）

- [ ] **Step 3: 实现 parse_catalog / find_tab / find_group**

创建 `.claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py`：

```python
#!/usr/bin/env python3
"""解析 docs/claude_docs/catalog.md 的分类结构，维护有道云笔记文件夹映射。"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = REPO_ROOT / "docs" / "claude_docs" / "catalog.md"
MAP_PATH = Path(__file__).resolve().parent.parent / "folder-map.json"
ROOT_FOLDER_ID = "WEBc1d2e6c709ed0850b09f070a86573197"

TAB_RE = re.compile(
    r'^## Tab \d+ — (.+?)（(?:对应有道笔记"(.+?)"，)?入口：`([^`]+)`）\s*$'
)
GROUP_RE = re.compile(r'^### ([^（]+?)\s*(?:（.*)?$')
PAGE_RE = re.compile(r'^- \[([ x])\] (.+?) — `([^`]+)`')


def parse_catalog(text):
    """解析 catalog.md 文本，返回 Tab 列表，每个 Tab 含 groups，每个 group 含 pages。"""
    tabs = []
    current_tab = None
    current_group = None
    for line in text.splitlines():
        m = TAB_RE.match(line)
        if m:
            current_tab = {"en": m.group(1).strip(), "zh": m.group(2), "groups": []}
            tabs.append(current_tab)
            current_group = None
            continue
        m = GROUP_RE.match(line)
        if m and current_tab is not None:
            current_group = {"en": m.group(1).strip(), "pages": []}
            current_tab["groups"].append(current_group)
            continue
        m = PAGE_RE.match(line)
        if m and current_group is not None:
            current_group["pages"].append(
                {"title": m.group(2).strip(), "url": m.group(3).strip()}
            )
            continue
    return tabs


def find_tab(tabs, folder_map, name):
    """按英文名、catalog.md 标注的中文名，或 folder-map.json 记录的中文别名查找 Tab。"""
    name = name.strip()
    for tab in tabs:
        if tab["en"].lower() == name.lower():
            return tab
        if tab["zh"] and tab["zh"] == name:
            return tab
    for zh_key, entry in folder_map.get("tabs", {}).items():
        if zh_key == name or entry.get("en", "").lower() == name.lower():
            target_en = entry.get("en", zh_key)
            for tab in tabs:
                if tab["en"].lower() == target_en.lower():
                    return tab
    return None


def find_group(tab, name):
    """按英文名查找 Tab 下的分组（大小写不敏感）。"""
    name = name.strip()
    for group in tab["groups"]:
        if group["en"].lower() == name.lower():
            return group
    return None


if __name__ == "__main__":
    pass
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
cd ".claude/skills/sync-cc-docs-to-youdaonote/scripts" && python -m unittest test_resolve_category -v
```
Expected: 全部 10 个测试用例 `OK`

- [ ] **Step 5: Commit**

```bash
git add ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" ".claude/skills/sync-cc-docs-to-youdaonote/scripts/test_resolve_category.py"
git commit -m "$(cat <<'EOF'
feat(sync-cc-docs-to-youdaonote): 新增 catalog.md 解析纯函数

- parse_catalog：解析 Tab/分组/页面结构，兼容分组标题带附加括注的情况
- find_tab/find_group：支持中英文名与 folder-map.json 别名双向查找
- 10 个单元测试覆盖标准解析、别名查找、未找到场景

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: youdaonote CLI 封装 + resolve/get-folder 子命令

**Files:**
- Modify: `.claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py`
- Modify: `.claude/skills/sync-cc-docs-to-youdaonote/scripts/test_resolve_category.py`

**Interfaces:**
- Consumes：Task 2 的 `parse_catalog`、`find_tab`、`find_group`；`REPO_ROOT`、`CATALOG_PATH`、`MAP_PATH`、`ROOT_FOLDER_ID` 常量
- Produces：
  - `load_folder_map(path) -> dict`、`save_folder_map(path, data) -> None`
  - `run_youdaonote(args_list, retries=1) -> subprocess.CompletedProcess`
  - `youdaonote_list(folder_id) -> list[tuple[str, str, str]]`（`(kind, id, name)`，`kind` 为 `"folder"` 或 `"note"`）
  - `youdaonote_mkdir(name, parent_id) -> None`
  - `ensure_folder(name, parent_id) -> str`（返回文件夹 ID，先查后建，避免重复）
  - CLI：`resolve_category.py resolve <tab> <group>`、`resolve_category.py get-folder <tab_zh> <group_en> [--group-zh <中文分组名>]`

- [ ] **Step 1: 写失败的单元测试（ensure_folder 用 mock，不触网）**

在 `test_resolve_category.py` 末尾（`if __name__ == "__main__":` 之前）追加。文件顶部原有的 `import unittest` 之后新增三行导入：

```python
import tempfile
from pathlib import Path
from unittest.mock import patch
```

然后追加以下测试类：

```python
from resolve_category import ensure_folder, load_folder_map, save_folder_map


class TestEnsureFolder(unittest.TestCase):
    @patch("resolve_category.youdaonote_mkdir")
    @patch("resolve_category.youdaonote_list")
    def test_reuses_existing_folder_without_creating(self, mock_list, mock_mkdir):
        mock_list.return_value = [("folder", "WEB123", "指南")]
        folder_id = ensure_folder("指南", "WEBparent")
        self.assertEqual(folder_id, "WEB123")
        mock_mkdir.assert_not_called()

    @patch("resolve_category.youdaonote_mkdir")
    @patch("resolve_category.youdaonote_list")
    def test_creates_when_missing_then_relists(self, mock_list, mock_mkdir):
        mock_list.side_effect = [[], [("folder", "WEB999", "指南")]]
        folder_id = ensure_folder("指南", "WEBparent")
        self.assertEqual(folder_id, "WEB999")
        mock_mkdir.assert_called_once_with("指南", "WEBparent")

    @patch("resolve_category.youdaonote_mkdir")
    @patch("resolve_category.youdaonote_list")
    def test_raises_if_still_missing_after_create(self, mock_list, mock_mkdir):
        mock_list.side_effect = [[], []]
        with self.assertRaises(RuntimeError):
            ensure_folder("指南", "WEBparent")


class TestFolderMapIO(unittest.TestCase):
    def test_load_missing_file_returns_empty_structure(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "nonexistent.json"
            result = load_folder_map(path)
            self.assertEqual(result, {"tabs": {}})

    def test_save_then_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "map.json"
            data = {"tabs": {"测试": {"id": "WEBabc"}}}
            save_folder_map(path, data)
            loaded = load_folder_map(path)
            self.assertEqual(loaded, data)

    def test_load_invalid_json_exits(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "broken.json"
            path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(SystemExit):
                load_folder_map(path)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
cd ".claude/skills/sync-cc-docs-to-youdaonote/scripts" && python -m unittest test_resolve_category -v
```
Expected: `ImportError: cannot import name 'ensure_folder' from 'resolve_category'`

- [ ] **Step 3: 实现 CLI 封装与子命令**

在 `resolve_category.py` 中，`if __name__ == "__main__": pass` 这一行**之前**插入以下内容（替换掉原来的 `if __name__ == "__main__": pass` 占位）：

```python
import argparse
import subprocess


def load_folder_map(path):
    if not path.exists():
        return {"tabs": {}}
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"错误：{path} 解析失败（{e}），文件可能损坏，不会自动覆盖", file=sys.stderr)
        sys.exit(1)


def save_folder_map(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_youdaonote(args_list, retries=1):
    last_err = None
    for _ in range(retries + 1):
        try:
            return subprocess.run(
                ["youdaonote", "-s", "ydn", *args_list],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
        except subprocess.CalledProcessError as e:
            last_err = e
    raise last_err


def youdaonote_list(folder_id):
    result = run_youdaonote(["list", "-f", folder_id])
    entries = []
    for line in result.stdout.splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("📁"):
            kind = "folder"
        elif line.startswith("📄"):
            kind = "note"
        else:
            continue
        rest = line[1:].strip()
        parts = rest.split("\t", 1)
        if len(parts) != 2:
            continue
        entries.append((kind, parts[0].strip(), parts[1].strip()))
    return entries


def youdaonote_mkdir(name, parent_id):
    run_youdaonote(["mkdir", name, "-f", parent_id])


def ensure_folder(name, parent_id):
    """先查父目录下是否已有同名文件夹，没有才创建，创建后重新查一次确认。"""
    for kind, entry_id, entry_name in youdaonote_list(parent_id):
        if kind == "folder" and entry_name == name:
            return entry_id
    youdaonote_mkdir(name, parent_id)
    for kind, entry_id, entry_name in youdaonote_list(parent_id):
        if kind == "folder" and entry_name == name:
            return entry_id
    raise RuntimeError(f"创建文件夹 {name!r} 后仍未在父目录 {parent_id} 下找到，mkdir 可能失败")


def cmd_resolve(args):
    catalog_text = CATALOG_PATH.read_text(encoding="utf-8")
    tabs = parse_catalog(catalog_text)
    folder_map = load_folder_map(MAP_PATH)

    tab = find_tab(tabs, folder_map, args.tab)
    if tab is None:
        print(f"错误：未在 catalog.md 中找到 Tab {args.tab!r}", file=sys.stderr)
        sys.exit(1)

    group = find_group(tab, args.group)
    if group is None:
        print(f"错误：未在 Tab {tab['en']!r} 下找到分组 {args.group!r}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(
        {"tab_en": tab["en"], "tab_zh": tab["zh"], "group_en": group["en"], "pages": group["pages"]},
        ensure_ascii=False,
        indent=2,
    ))


def cmd_get_folder(args):
    folder_map = load_folder_map(MAP_PATH)
    tabs_map = folder_map.setdefault("tabs", {})

    tab_entry = tabs_map.get(args.tab_zh)
    if tab_entry is None:
        tab_id = ensure_folder(args.tab_zh, ROOT_FOLDER_ID)
        tab_entry = {"en": args.tab_zh, "id": tab_id, "groups": {}}
        tabs_map[args.tab_zh] = tab_entry
        save_folder_map(MAP_PATH, folder_map)

    groups_map = tab_entry.setdefault("groups", {})
    group_entry = groups_map.get(args.group_en)
    if group_entry is None:
        if not args.group_zh:
            print(f"错误：分组 {args.group_en!r} 尚无中文名记录，必须提供 --group-zh", file=sys.stderr)
            sys.exit(1)
        group_id = ensure_folder(args.group_zh, tab_entry["id"])
        group_entry = {"en": args.group_en, "zh": args.group_zh, "id": group_id, "pages": {}}
        groups_map[args.group_en] = group_entry
        save_folder_map(MAP_PATH, folder_map)

    print(group_entry["id"])


def build_parser():
    parser = argparse.ArgumentParser(prog="resolve_category.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="解析分类下的页面清单")
    p_resolve.add_argument("tab")
    p_resolve.add_argument("group")

    p_folder = sub.add_parser("get-folder", help="查询/创建有道文件夹")
    p_folder.add_argument("tab_zh")
    p_folder.add_argument("group_en")
    p_folder.add_argument("--group-zh")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "resolve":
        cmd_resolve(args)
    elif args.command == "get-folder":
        cmd_get_folder(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
cd ".claude/skills/sync-cc-docs-to-youdaonote/scripts" && python -m unittest test_resolve_category -v
```
Expected: 全部测试用例 `OK`（新增的 6 个 mock/IO 测试 + Task 2 的 10 个，共 16 个）

- [ ] **Step 5: Commit**

```bash
git add ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" ".claude/skills/sync-cc-docs-to-youdaonote/scripts/test_resolve_category.py"
git commit -m "$(cat <<'EOF'
feat(sync-cc-docs-to-youdaonote): 新增 youdaonote CLI 封装与 resolve/get-folder 子命令

- ensure_folder：先查后建，避免与已手动创建的同名文件夹冲突（mock 测试覆盖复用/创建/异常三种场景）
- load_folder_map/save_folder_map：JSON 持久化，损坏时报错而非静默覆盖
- resolve/get-folder 两个 CLI 子命令接线完成

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: resolve 冒烟测试（真实 catalog.md）

**Files:**
- 无新增文件，验证 Task 2/3 产出的脚本对真实数据的行为

**Interfaces:**
- Consumes: Task 3 的 `resolve_category.py` CLI

- [ ] **Step 1: 对真实分类运行 resolve**

Run:
```bash
cd "E:/ProjectxPlex/WPFCodePlex/unipus-plugins-official" && python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" resolve "使用ClaudeCode构建" "Guides"
```
Expected：
```json
{
  "tab_en": "Build with Claude Code",
  "tab_zh": "使用ClaudeCode构建",
  "group_en": "Guides",
  "pages": [
    {
      "title": "Monorepos and large repos",
      "url": "/large-codebases"
    }
  ]
}
```

- [ ] **Step 2: 验证"分类不存在"路径正确报错并以非零退出**

Run:
```bash
cd "E:/ProjectxPlex/WPFCodePlex/unipus-plugins-official" && python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" resolve "使用ClaudeCode构建" "NoSuchGroup"; echo "退出码: $?"
```
Expected: stderr 打印 `错误：未在 Tab 'Build with Claude Code' 下找到分组 'NoSuchGroup'`，`退出码: 1`

- [ ] **Step 3: 无需 commit（本任务不产生代码变更，仅验证）**

---

### Task 5: get-folder 冒烟测试（真实有道账号，含幂等验证）

**Files:**
- 无新增文件，验证 Task 3 产出的 `get-folder` 对真实有道账号的行为；副作用：会在"使用ClaudeCode构建"文件夹下创建一个真实的"指南"子文件夹

**Interfaces:**
- Consumes: Task 3 的 `resolve_category.py get-folder` CLI

- [ ] **Step 1: 首次运行，创建"指南"文件夹**

Run:
```bash
cd "E:/ProjectxPlex/WPFCodePlex/unipus-plugins-official" && python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" get-folder "使用ClaudeCode构建" "Guides" --group-zh "指南"
```
Expected: 打印一个以 `WEB` 开头的文件夹 ID（记为 `<GUIDES_ID>`）

- [ ] **Step 2: 验证 folder-map.json 已写入该分组记录**

Run:
```bash
python -c "
import json
d = json.load(open('.claude/skills/sync-cc-docs-to-youdaonote/folder-map.json', encoding='utf-8'))
g = d['tabs']['使用ClaudeCode构建']['groups']['Guides']
assert g['zh'] == '指南'
assert g['id'].startswith('WEB')
print('写入正确:', g['id'])
"
```
Expected: `写入正确: WEB...`

- [ ] **Step 3: 验证有道账号中确实新建了该文件夹**

Run:
```bash
youdaonote -s ydn list -f WEBb2aab5b9ec63445b0c0d299e3b36b96e
```
Expected: 输出中包含一行 `📁 <GUIDES_ID>	指南`

- [ ] **Step 4: 幂等性验证——再次运行同一命令，不应产生重复文件夹**

Run:
```bash
cd "E:/ProjectxPlex/WPFCodePlex/unipus-plugins-official" && python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" get-folder "使用ClaudeCode构建" "Guides"
```
Expected: 打印的文件夹 ID 与 Step 1 完全相同（`--group-zh` 省略也不受影响，因为 `folder-map.json` 里已有记录）

Run:
```bash
youdaonote -s ydn list -f WEBb2aab5b9ec63445b0c0d299e3b36b96e | grep -c "指南"
```
Expected: `1`（只有一个"指南"文件夹，未重复创建）

- [ ] **Step 5: 无需 commit（本任务不产生代码变更，仅验证真实副作用）**

---

### Task 6: 编写 SKILL.md 编排指令与 CHANGELOG.md

**Files:**
- Create: `.claude/skills/sync-cc-docs-to-youdaonote/SKILL.md`
- Create: `.claude/skills/sync-cc-docs-to-youdaonote/CHANGELOG.md`

**Interfaces:**
- Consumes: Task 1-5 产出的全部脚本、数据文件、验证结果

- [ ] **Step 1: 编写 SKILL.md**

创建 `.claude/skills/sync-cc-docs-to-youdaonote/SKILL.md`：

```markdown
---
name: sync-cc-docs-to-youdaonote
version: 1.0.0
description: >
  按分类路径（如"使用ClaudeCode构建 / Guides"）核对 docs/claude_docs/catalog.md，
  抓取翻译该分类下的 Claude Code 官方文档页面，幂等同步到有道云笔记，文件夹层级
  与站点导航一致。触发词："保存 <分类路径> 文档"、"同步 <分类路径> 到有道笔记"。
---

# sync-cc-docs-to-youdaonote

将 Claude Code 官方文档站点（code.claude.com/docs/en）按 Tab/分组分类，抓取翻译
后同步到有道云笔记，文件夹层级与站点导航一致。

## 前置条件

- `docs/claude_docs/catalog.md` 必须已存在（通过 Playwright 抓取站点导航得到，
  本 skill 只读取，不负责生成或更新）
- 依赖 `youdaonote-skill`（用户级全局 skill）提供的 `youdaonote` CLI

## 使用方式

用户说"保存 <Tab 名> / <分组名> 文档"，分类路径中英文均可，如：
- "保存 使用ClaudeCode构建 / Guides 文档"
- "保存 Build with Claude Code / Guides 文档"

只支持"Tab / 单个分组"这一级粒度，不支持一次处理整个 Tab。

## 执行流程

### Step 1 — 解析分类

```bash
python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" resolve "<Tab名>" "<分组名>"
```

- 非零退出 → **立即停止**，将 stderr 的错误信息转告用户，不做任何后续操作
- 成功 → 得到 JSON：`{"tab_en", "tab_zh", "group_en", "pages": [{"title", "url"}]}`

### Step 2 — 定位/创建有道文件夹

若 `tab_zh` 为 `null`（catalog.md 未标注该 Tab 的中文名），使用用户输入的中文 Tab 名作为 `<Tab中文名>`；否则直接用 `tab_zh`。

```bash
python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" get-folder "<Tab中文名>" "<group_en>"
```

- 若报错"尚无中文名记录，必须提供 --group-zh"：将 `group_en`（英文分组名）翻译为
  中文（简短、贴合含义，如 "Guides" → "指南"），加上 `--group-zh "<译名>"` 重跑：

  ```bash
  python ".claude/skills/sync-cc-docs-to-youdaonote/scripts/resolve_category.py" get-folder "<Tab中文名>" "<group_en>" --group-zh "<译名>"
  ```

- 命令因网络等瞬时错误失败 → 重试一次，仍失败则**整个分组判定失败**，停止，告知用户
- 成功 → 得到分组文件夹 ID（记为 `<GROUP_ID>`）

### Step 3 — 拉取远端实际列表（每分组一次，供幂等交叉验证）

```bash
youdaonote -s ydn list -f <GROUP_ID>
```

记录输出中每一行 `📄 <fileId>\t<title>` 的 `fileId` 集合，供 Step 4 交叉验证。

### Step 4 — 逐篇处理

用 Read 工具读取 `.claude/skills/sync-cc-docs-to-youdaonote/folder-map.json`，定位
`tabs[<Tab中文名>].groups[<group_en>].pages` 这个字典。

对 Step 1 返回的每一篇页面（`title` + `url`）：

1. 查 `pages[<url>]` 是否有记录的 `fileId`：
   - **有记录，且该 `fileId` 出现在 Step 3 拉取的远端列表中** → 已同步，跳过，计入"已跳过"
   - **有记录，但不在远端列表中**（用户手动删除过）→ 记录已过期，按未同步处理
   - **无记录** → 按未同步处理
2. 未同步的页面，完整走一遍 `unipus-office-plugin:web-to-markdown` skill 已有的抓取
   /翻译/校验流程：
   - `python -m markitdown "https://code.claude.com/docs/en<url>" > docs/claude_docs/.raw-<slug>.md`（三级降级见 web-to-markdown SKILL.md）
   - Read 原文 → 翻译（剥离站点通用 Documentation Index 横幅、`<Note>`/`<Tip>` 转引用块）→ Write 到 `docs/claude_docs/<slug>.md`
   - `python plugins/unipus-office-plugin/skills/web-to-markdown/scripts/post_process.py "docs/claude_docs/<slug>.md" --base-url "https://code.claude.com/docs"`
   - `python plugins/unipus-office-plugin/skills/web-to-markdown/scripts/verify.py ".raw-<slug>.md" "docs/claude_docs/<slug>.md"`
   - `python plugins/unipus-office-plugin/skills/web-to-markdown/scripts/verify_quality.py ".raw-<slug>.md" "docs/claude_docs/<slug>.md" --base-url "https://code.claude.com/docs"`
   - 两轮核对通过后：`youdaonote -s ydn save --json` 上传（`contentFile` 传 `docs/claude_docs/<slug>.md`，`type: "md"`，`parentId: "<GROUP_ID>"`）
   - 清理 `.raw-<slug>.md` 临时文件
3. 上传成功 → 用 Edit 工具把 `{"title": "<slug>.md", "fileId": "<返回的fileId>"}` 写入
   `folder-map.json` 的 `pages[<url>]`（覆盖过期记录）
4. 任一环节失败（抓取/翻译/校验/上传）→ 记录该篇失败原因，**继续处理下一篇**，不阻断

### Step 5 — 汇总报告

```
✓ 已同步 N 篇
⏭ 已跳过 N 篇（本地+远端均确认存在）
↻ 重新同步 N 篇（本地记录已失效）
✗ 失败 N 篇（附原因）
```

## 边界情况

| 情况 | 处理方式 |
|---|---|
| 分类不存在于 catalog.md | 立即停止，不创建任何文件夹 |
| 有道文件夹创建失败 | 重试一次，仍失败则整个分组判定失败 |
| 单篇抓取/翻译/上传失败 | 记录原因，继续下一篇，不阻断 |
| 本地记录 fileId 但远端已被手动删除 | 判定过期，重新同步并覆盖记录 |
| folder-map.json 不存在 | 首次运行自动初始化为 `{"tabs": {}}` |
| folder-map.json 解析失败 | 报错停止，不静默覆盖 |

## 不在范围内

- 不支持一次处理整个 Tab
- 不负责迁移历史遗留文件
- 不负责维护/更新 catalog.md
- 不做 marketplace 分发
```

- [ ] **Step 2: 编写 CHANGELOG.md**

创建 `.claude/skills/sync-cc-docs-to-youdaonote/CHANGELOG.md`：

```markdown
## [1.0.0] - 2026-07-05

### Added
- 初始版本：`resolve_category.py` 提供 `resolve`/`get-folder` 两个子命令
- `folder-map.json` 持久化 Tab/分组/页面的有道文件夹映射与幂等同步记录
- SKILL.md 编排完整的解析→定位文件夹→交叉验证→逐篇同步→汇总报告流程
```

- [ ] **Step 3: 验证 SKILL.md frontmatter 可解析**

Run:
```bash
python -c "
import re
text = open('.claude/skills/sync-cc-docs-to-youdaonote/SKILL.md', encoding='utf-8').read()
assert text.startswith('---')
assert 'version: 1.0.0' in text
assert 'name: sync-cc-docs-to-youdaonote' in text
print('OK')
"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add ".claude/skills/sync-cc-docs-to-youdaonote/SKILL.md" ".claude/skills/sync-cc-docs-to-youdaonote/CHANGELOG.md"
git commit -m "$(cat <<'EOF'
feat(sync-cc-docs-to-youdaonote): 新增 SKILL.md 编排指令与 CHANGELOG

- 完整编排流程：resolve → get-folder → 拉取远端列表交叉验证 → 逐篇幂等同步 → 汇总报告
- 复用 web-to-markdown 既有的抓取/翻译/两轮校验约定，不重新实现
- 初始版本 1.0.0，随附 CHANGELOG.md

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## 收尾：推送

所有任务完成后，推送到远端：

```bash
git pull --rebase origin master && git push origin master
```
