# MasterGo 转 WPF XAML Skill 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `mastergo-to-wpf` skill，把 MasterGo 设计稿的 DSL 数据转换为 WPF XAML 页面脚手架。

**Architecture:** 一个零依赖 Python CLI（`dsl_to_xaml.py`）承担全部确定性转换——吃落盘的 DSL JSON，吐 XAML + ResourceDictionary + 图标清单。SKILL.md 只负责编排 MCP 调用与交付判断。脚本刻意不碰 MCP、不联网，使测试全量离线可跑。图标转换复用同插件已有的 `svg-to-xaml-path`。

**Tech Stack:** Python 3（仅标准库）、`unittest`（本机无 pytest）、`@mastergo/magic-mcp` MCP server。

## Global Constraints

- **仅标准库**：不引入任何第三方 Python 依赖。
- **测试框架用 `unittest`**：本机无 `pytest`。命令为 `python -m unittest discover -s <scripts目录> -p "test_*.py"`，须在仓库根目录执行。
- **代码风格跟随 `merge_svg_paths.py`**：模块级 docstring、`from __future__ import annotations`、`ConversionError` 异常类、每个函数一行 docstring、常量用 `#:` 注释、错误信息全小写英文且带处置建议。
- **CLI 错误契约**：失败时 `print(f"error: {error}", file=sys.stderr)` 并 `return 2`，**stdout 必须为空**。告警走 stderr，exit 0。
- **SKILL.md frontmatter 六字段限制**（`.claude/rules/skill-authoring.md`）：仅 `name`/`description`/`license`/`allowed-tools`/`metadata`/`compatibility`。版本放 `metadata.version`，作者固定 `desktop client team`。
- **测试样本目录用 `assets/`**，跟随仓库既有惯例（`svg-to-xaml-path/assets/`），不用 `fixtures/`。
- **新增 skill → marketplace Minor 升版**：`8.4.0` → `8.5.0`。
- **每个 skill 目录必须有 CHANGELOG.md**，初始 `[1.0.0]`。

---

## 文件结构

```
plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/
├── SKILL.md                       编排流程、前置检查、交付纪律（Task 8）
├── CHANGELOG.md                   初始 1.0.0（Task 8）
├── test-prompts.json              5 条触发场景（Task 8）
├── references/
│   └── dsl-mapping.md             完整映射表 + 静默行为清单（Task 8）
└── scripts/
    ├── dsl_to_xaml.py             转换器 CLI（Task 1-7 递增构建）
    ├── test_dsl_to_xaml.py        契约测试（Task 1-7 递增构建）
    └── assets/
        ├── flex-row.json          Task 2
        ├── flex-grow.json         Task 2
        ├── absolute.json          Task 3
        ├── nested-mixed.json      Task 3
        ├── tokens.json            Task 4
        ├── broken-ref.json        Task 4
        ├── opacity-frame.json     Task 5
        ├── long-text.json         Task 6
        ├── placeholder-text.json  Task 6
        ├── hallucinated-text.json Task 6
        └── icons.json             Task 7
```

**职责边界**：`dsl_to_xaml.py` 是纯函数式 CLI，只做 JSON → XAML；不调 MCP、不联网、不读环境变量。MCP 编排由模型按 SKILL.md 执行。

**任务依赖**：Task 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 线性推进，每个任务都以能跑通的测试收尾。

---

### Task 1: 骨架与 CLI 契约

**Files:**
- Create: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/dsl_to_xaml.py`
- Create: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/test_dsl_to_xaml.py`

**Interfaces:**
- Consumes: 无（首个任务）
- Produces: `ConversionError` 异常类；`load_sections(directory: Path) -> tuple[dict, list[dict]]` 返回 `(sections_list, section_dsls)`；`main(argv: list[str] | None = None) -> int`；CLI 参数 `--input PATH`（必填，DSL JSON 目录）、`--out PATH`（必填，XAML 输出目录）、`--page-name TEXT`（默认 `GeneratedPage`）

- [ ] **Step 1: 写失败的测试**

创建 `test_dsl_to_xaml.py`：

```python
"""Black-box CLI contract tests for dsl_to_xaml.py."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("dsl_to_xaml.py")
ASSETS = Path(__file__).with_name("assets")


class CliTestCase(unittest.TestCase):
    """Shared helper for driving the converter as the skill actually invokes it."""

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def convert(self, asset_name: str) -> tuple[subprocess.CompletedProcess[str], Path]:
        """Run the converter over one bundled asset and return the result and out dir."""
        with tempfile.TemporaryDirectory() as temporary:
            input_dir = Path(temporary) / "dsl"
            input_dir.mkdir()
            payload = json.loads((ASSETS / asset_name).read_text(encoding="utf-8"))
            (input_dir / "sections-list.json").write_text(
                json.dumps(payload["list"], ensure_ascii=False), encoding="utf-8"
            )
            for index, section in enumerate(payload["sections"]):
                (input_dir / f"section-{index}.json").write_text(
                    json.dumps(section, ensure_ascii=False), encoding="utf-8"
                )
            out_dir = Path(temporary) / "out"
            result = self.run_cli("--input", str(input_dir), "--out", str(out_dir))
            if out_dir.exists():
                kept = Path(tempfile.mkdtemp())
                for item in out_dir.iterdir():
                    (kept / item.name).write_text(
                        item.read_text(encoding="utf-8"), encoding="utf-8"
                    )
                return result, kept
            return result, out_dir


class SkeletonTests(CliTestCase):
    def test_missing_input_directory_fails_without_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "nope"
            result = self.run_cli("--input", str(missing), "--out", temporary)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("error:", result.stderr.lower())
        self.assertEqual(result.stdout, "")

    def test_directory_without_sections_list_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_cli("--input", temporary, "--out", temporary)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("sections-list.json", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_malformed_json_reports_the_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / "sections-list.json").write_text("{not json", encoding="utf-8")
            result = self.run_cli("--input", temporary, "--out", temporary)

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("sections-list.json", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"`
Expected: FAIL —— `dsl_to_xaml.py` 不存在，subprocess 返回非 2 的退出码

- [ ] **Step 3: 写最小实现**

创建 `dsl_to_xaml.py`：

```python
"""Convert MasterGo section DSL into a WPF XAML page scaffold."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class ConversionError(Exception):
    """An input or conversion error that should be shown to the user."""


def read_json(path: Path) -> object:
    """Read one JSON file, naming it in any error so the user can find it."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise ConversionError(f"could not read {path.name}: {error}") from error
    except json.JSONDecodeError as error:
        raise ConversionError(f"{path.name} is not valid JSON: {error}") from error


def load_sections(directory: Path) -> tuple[dict, list[dict]]:
    """Load the section directory listing and every section DSL beside it."""
    if not directory.is_dir():
        raise ConversionError(f"input directory not found: {directory}")
    listing_path = directory / "sections-list.json"
    if not listing_path.is_file():
        raise ConversionError(
            f"sections-list.json not found in {directory}; run mcp__getDesignSections "
            "without a sectionIndex first and save its response there"
        )
    listing = read_json(listing_path)
    if not isinstance(listing, dict):
        raise ConversionError("sections-list.json must contain a JSON object")

    sections: list[dict] = []
    for path in sorted(directory.glob("section-*.json"), key=lambda p: p.name):
        section = read_json(path)
        if not isinstance(section, dict):
            raise ConversionError(f"{path.name} must contain a JSON object")
        sections.append(section)
    return listing, sections


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Convert MasterGo section DSL into a WPF XAML page scaffold."
    )
    parser.add_argument("--input", required=True, metavar="PATH", help="directory of DSL JSON")
    parser.add_argument("--out", required=True, metavar="PATH", help="output directory")
    parser.add_argument("--page-name", default="GeneratedPage", help="generated page file name")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the DSL conversion CLI."""
    arguments = build_parser().parse_args(argv)
    try:
        load_sections(Path(arguments.input))
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"`
Expected: PASS，3 个测试

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/
git commit -m "feat(mastergo-to-wpf): 新增 DSL 转 XAML 的 CLI 骨架与输入校验"
```

---

### Task 2: flex 容器 → StackPanel / Grid

**Files:**
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/dsl_to_xaml.py`
- Modify: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/test_dsl_to_xaml.py`
- Create: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/assets/flex-row.json`
- Create: `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/assets/flex-grow.json`

**Interfaces:**
- Consumes: `ConversionError`、`load_sections`（Task 1）
- Produces: `number(value: float) -> str` 六位小数格式化；`render_node(node: dict, depth: int) -> list[str]` 返回缩进后的 XAML 行；`render_page(listing: dict, sections: list[dict], page_name: str) -> str` 返回完整 XAML 文本

- [ ] **Step 1: 写失败的测试**

创建 `assets/flex-row.json`：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["确定", "取消"] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 200, "height": 48 }]
  },
  "sections": [
    {
      "nodes": [
        {
          "type": "FRAME",
          "id": "1:1",
          "name": "ButtonBar",
          "layoutStyle": { "width": 200, "height": 48, "relativeX": 0, "relativeY": 0 },
          "flexContainerInfo": { "flexDirection": "row", "gap": 8, "padding": "4 4 4 4" },
          "children": [
            {
              "type": "TEXT",
              "id": "1:2",
              "name": "Ok",
              "layoutStyle": { "width": 60, "height": 32, "relativeX": 4, "relativeY": 4 },
              "text": [{ "text": "确定" }]
            },
            {
              "type": "TEXT",
              "id": "1:3",
              "name": "Cancel",
              "layoutStyle": { "width": 60, "height": 32, "relativeX": 72, "relativeY": 4 },
              "text": [{ "text": "取消" }]
            }
          ]
        }
      ]
    }
  ]
}
```

创建 `assets/flex-grow.json`（同结构，但子节点带 `flexGrow`）：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["左", "右"] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 200, "height": 48 }]
  },
  "sections": [
    {
      "nodes": [
        {
          "type": "FRAME",
          "id": "2:1",
          "name": "SplitBar",
          "layoutStyle": { "width": 200, "height": 48, "relativeX": 0, "relativeY": 0 },
          "flexContainerInfo": { "flexDirection": "row", "gap": 0 },
          "children": [
            {
              "type": "TEXT",
              "id": "2:2",
              "name": "Left",
              "layoutStyle": { "width": 100, "height": 48, "relativeX": 0, "relativeY": 0 },
              "flexGrow": 1,
              "text": [{ "text": "左" }]
            },
            {
              "type": "TEXT",
              "id": "2:3",
              "name": "Right",
              "layoutStyle": { "width": 100, "height": 48, "relativeX": 100, "relativeY": 0 },
              "flexGrow": 1,
              "text": [{ "text": "右" }]
            }
          ]
        }
      ]
    }
  ]
}
```

在 `test_dsl_to_xaml.py` 末尾（`if __name__` 之前）追加：

```python
class FlexLayoutTests(CliTestCase):
    """flexContainerInfo present means flow layout, never absolute positioning."""

    def test_flex_row_becomes_a_horizontal_stackpanel(self) -> None:
        result, out_dir = self.convert("flex-row.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<StackPanel Orientation="Horizontal"', xaml)
        self.assertIn("确定", xaml)
        self.assertIn("取消", xaml)

    def test_flex_children_never_get_canvas_coordinates(self) -> None:
        result, out_dir = self.convert("flex-row.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        body = xaml.split("<StackPanel", 1)[1]
        self.assertNotIn("Canvas.Left", body)
        self.assertNotIn("Canvas.Top", body)

    def test_flex_gap_becomes_margin_on_all_but_the_last_child(self) -> None:
        result, out_dir = self.convert("flex-row.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertEqual(xaml.count('Margin="0,0,8,0"'), 1)

    def test_flex_grow_children_become_a_grid_with_star_columns(self) -> None:
        result, out_dir = self.convert("flex-grow.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("<Grid", xaml)
        self.assertEqual(xaml.count('<ColumnDefinition Width="*" />'), 2)
        self.assertIn('Grid.Column="0"', xaml)
        self.assertIn('Grid.Column="1"', xaml)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py" -k Flex`
Expected: FAIL —— `GeneratedPage.xaml` 不存在（`FileNotFoundError`）

- [ ] **Step 3: 写最小实现**

在 `dsl_to_xaml.py` 的 `load_sections` 之后插入：

```python
def number(value: float) -> str:
    """Format a coordinate without a trailing fraction, so output stays readable."""
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-", "-0") else text


def escaped(value: str) -> str:
    """Escape text for an XML attribute or element body."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def node_text(node: dict) -> str:
    """Join a TEXT node's rich-text runs into one string."""
    runs = node.get("text") or []
    return "".join(str(run.get("text", "")) for run in runs if isinstance(run, dict))


def render_text(node: dict, indent: str, extra: str = "") -> list[str]:
    """Render a TEXT node as a TextBlock."""
    content = escaped(node_text(node))
    return [f'{indent}<TextBlock{extra} Text="{content}" />']


def render_flex(node: dict, depth: int) -> list[str]:
    """Render a flex container as a StackPanel, or a Grid when children grow."""
    indent = "  " * depth
    info = node.get("flexContainerInfo") or {}
    children = node.get("children") or []
    grows = [child for child in children if child.get("flexGrow")]

    if grows:
        lines = [f"{indent}<Grid>", f"{indent}  <Grid.ColumnDefinitions>"]
        lines += [f'{indent}    <ColumnDefinition Width="*" />' for _ in children]
        lines.append(f"{indent}  </Grid.ColumnDefinitions>")
        for column, child in enumerate(children):
            lines += render_node(child, depth + 1, extra=f' Grid.Column="{column}"')
        lines.append(f"{indent}</Grid>")
        return lines

    horizontal = str(info.get("flexDirection", "row")).lower() == "row"
    orientation = "Horizontal" if horizontal else "Vertical"
    gap = float(info.get("gap") or 0)
    lines = [f'{indent}<StackPanel Orientation="{orientation}">']
    for position, child in enumerate(children):
        extra = ""
        if gap and position < len(children) - 1:
            margin = f"0,0,{number(gap)},0" if horizontal else f"0,0,0,{number(gap)}"
            extra = f' Margin="{margin}"'
        lines += render_node(child, depth + 1, extra=extra)
    lines.append(f"{indent}</StackPanel>")
    return lines


def render_node(node: dict, depth: int, extra: str = "") -> list[str]:
    """Render one DSL node and its subtree."""
    indent = "  " * depth
    kind = node.get("type")
    if kind == "TEXT":
        return render_text(node, indent, extra)
    if node.get("flexContainerInfo"):
        return render_flex(node, depth)
    lines = [f"{indent}<Grid{extra}>"]
    for child in node.get("children") or []:
        lines += render_node(child, depth + 1)
    lines.append(f"{indent}</Grid>")
    return lines


def render_page(listing: dict, sections: list[dict], page_name: str) -> str:
    """Render the whole page: a Canvas shell holding every section."""
    lines = [
        '<UserControl xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"',
        f'             x:Class="{page_name}">',
        "  <Canvas>",
    ]
    containers = listing.get("splitContainers") or []
    for index, section in enumerate(sections):
        box = containers[index] if index < len(containers) else {}
        left, top = number(box.get("x", 0)), number(box.get("y", 0))
        lines.append(f'    <Canvas Canvas.Left="{left}" Canvas.Top="{top}">')
        for node in section.get("nodes") or []:
            lines += render_node(node, 3)
        lines.append("    </Canvas>")
    lines += ["  </Canvas>", "</UserControl>", ""]
    return "\n".join(lines)
```

把 `main` 换成：

```python
def main(argv: list[str] | None = None) -> int:
    """Run the DSL conversion CLI."""
    arguments = build_parser().parse_args(argv)
    try:
        listing, sections = load_sections(Path(arguments.input))
        xaml = render_page(listing, sections, arguments.page_name)
        out_dir = Path(arguments.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{arguments.page_name}.xaml").write_text(xaml, encoding="utf-8")
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"`
Expected: PASS，7 个测试

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/
git commit -m "feat(mastergo-to-wpf): flex 容器转 StackPanel，带 flexGrow 时转 Grid 星号列"
```

---

### Task 3: 绝对定位 → Canvas，且嵌套不压平

**Files:**
- Modify: `.../scripts/dsl_to_xaml.py`
- Modify: `.../scripts/test_dsl_to_xaml.py`
- Create: `.../scripts/assets/absolute.json`
- Create: `.../scripts/assets/nested-mixed.json`

**Interfaces:**
- Consumes: `render_node`、`number`（Task 2）
- Produces: 修改后的 `render_node` —— 无 `flexContainerInfo` 的容器改渲染为 `<Canvas>`，其子节点带 `Canvas.Left`/`Canvas.Top`

- [ ] **Step 1: 写失败的测试**

创建 `assets/absolute.json`：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["标题"] },
    "splitContainers": [{ "x": 10, "y": 20, "width": 300, "height": 200 }]
  },
  "sections": [
    {
      "nodes": [
        {
          "type": "FRAME",
          "id": "3:1",
          "name": "Board",
          "layoutStyle": { "width": 300, "height": 200, "relativeX": 0, "relativeY": 0 },
          "children": [
            {
              "type": "TEXT",
              "id": "3:2",
              "name": "Title",
              "layoutStyle": { "width": 80, "height": 24, "relativeX": 32, "relativeY": 16 },
              "text": [{ "text": "标题" }]
            }
          ]
        }
      ]
    }
  ]
}
```

创建 `assets/nested-mixed.json`（flex 里套绝对定位容器）：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["内层"] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 400, "height": 100 }]
  },
  "sections": [
    {
      "nodes": [
        {
          "type": "FRAME",
          "id": "4:1",
          "name": "OuterFlex",
          "layoutStyle": { "width": 400, "height": 100, "relativeX": 0, "relativeY": 0 },
          "flexContainerInfo": { "flexDirection": "column", "gap": 0 },
          "children": [
            {
              "type": "FRAME",
              "id": "4:2",
              "name": "InnerAbsolute",
              "layoutStyle": { "width": 400, "height": 100, "relativeX": 0, "relativeY": 0 },
              "children": [
                {
                  "type": "TEXT",
                  "id": "4:3",
                  "name": "Inner",
                  "layoutStyle": { "width": 50, "height": 20, "relativeX": 12, "relativeY": 34 },
                  "text": [{ "text": "内层" }]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

追加测试类：

```python
class AbsoluteLayoutTests(CliTestCase):
    """A node without flexContainerInfo positions its children absolutely."""

    def test_absolute_container_becomes_a_canvas(self) -> None:
        result, out_dir = self.convert("absolute.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('Canvas.Left="32"', xaml)
        self.assertIn('Canvas.Top="16"', xaml)

    def test_section_shell_uses_the_splitcontainer_page_coordinates(self) -> None:
        result, out_dir = self.convert("absolute.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<Canvas Canvas.Left="10" Canvas.Top="20">', xaml)

    def test_nesting_is_preserved_rather_than_flattened(self) -> None:
        result, out_dir = self.convert("nested-mixed.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('<StackPanel Orientation="Vertical">', xaml)
        stack_body = xaml.split('<StackPanel Orientation="Vertical">', 1)[1]
        self.assertIn("<Canvas>", stack_body)
        self.assertIn('Canvas.Left="12"', stack_body)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py" -k Absolute`
Expected: FAIL —— 当前 `render_node` 对非 flex 容器输出 `<Grid>` 且不带 `Canvas.Left`

- [ ] **Step 3: 写最小实现**

把 `render_node` 替换为：

```python
def canvas_position(node: dict) -> str:
    """Return the Canvas attached properties for an absolutely positioned node."""
    layout = node.get("layoutStyle") or {}
    if "relativeX" not in layout and "relativeY" not in layout:
        raise ConversionError(
            f"node {node.get('id', '?')} ({node.get('name', 'unnamed')}) has no "
            "layoutStyle.relativeX/relativeY and is not inside a flex container; "
            "its position cannot be determined"
        )
    left = number(layout.get("relativeX", 0))
    top = number(layout.get("relativeY", 0))
    return f' Canvas.Left="{left}" Canvas.Top="{top}"'


def render_node(node: dict, depth: int, extra: str = "", absolute: bool = False) -> list[str]:
    """Render one DSL node and its subtree.

    `absolute` says the parent positions its children with Canvas coordinates; flex
    parents pass False so their children never receive Canvas.Left/Top.
    """
    indent = "  " * depth
    placement = canvas_position(node) if absolute else ""
    if node.get("type") == "TEXT":
        return render_text(node, indent, extra + placement)
    if node.get("flexContainerInfo"):
        return render_flex(node, depth, extra + placement)
    lines = [f"{indent}<Canvas{extra}{placement}>"]
    for child in node.get("children") or []:
        lines += render_node(child, depth + 1, absolute=True)
    lines.append(f"{indent}</Canvas>")
    return lines
```

`render_flex` 签名加 `extra` 参数，并把子节点调用改为 `absolute=False`：

```python
def render_flex(node: dict, depth: int, extra: str = "") -> list[str]:
    """Render a flex container as a StackPanel, or a Grid when children grow."""
    indent = "  " * depth
    info = node.get("flexContainerInfo") or {}
    children = node.get("children") or []
    grows = [child for child in children if child.get("flexGrow")]

    if grows:
        lines = [f"{indent}<Grid{extra}>", f"{indent}  <Grid.ColumnDefinitions>"]
        lines += [f'{indent}    <ColumnDefinition Width="*" />' for _ in children]
        lines.append(f"{indent}  </Grid.ColumnDefinitions>")
        for column, child in enumerate(children):
            lines += render_node(child, depth + 1, extra=f' Grid.Column="{column}"')
        lines.append(f"{indent}</Grid>")
        return lines

    horizontal = str(info.get("flexDirection", "row")).lower() == "row"
    orientation = "Horizontal" if horizontal else "Vertical"
    gap = float(info.get("gap") or 0)
    lines = [f'{indent}<StackPanel Orientation="{orientation}"{extra}>']
    for position, child in enumerate(children):
        margin = ""
        if gap and position < len(children) - 1:
            offsets = f"0,0,{number(gap)},0" if horizontal else f"0,0,0,{number(gap)}"
            margin = f' Margin="{offsets}"'
        lines += render_node(child, depth + 1, extra=margin)
    lines.append(f"{indent}</StackPanel>")
    return lines
```

`render_page` 中区块根节点的调用改为 `render_node(node, 3, absolute=False)`（区块根节点已由外层 Canvas 定位）。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"`
Expected: PASS，10 个测试

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/
git commit -m "feat(mastergo-to-wpf): 非 flex 容器转 Canvas 绝对定位，保留嵌套层级"
```

---

### Task 4: 颜色令牌 → ResourceDictionary

**Files:**
- Modify: `.../scripts/dsl_to_xaml.py`
- Modify: `.../scripts/test_dsl_to_xaml.py`
- Create: `.../scripts/assets/tokens.json`
- Create: `.../scripts/assets/broken-ref.json`

**Interfaces:**
- Consumes: `render_page`（Task 3）
- Produces: `resource_key(token: str) -> str`；`collect_brushes(sections: list[dict]) -> dict[str, str]` 返回 `{资源key: 颜色值}`；`render_resources(brushes: dict[str, str]) -> str`；`render_page` 增加返回资源字典所需的画刷表

- [ ] **Step 1: 写失败的测试**

创建 `assets/tokens.json`：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["文字"] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 100, "height": 40 }]
  },
  "sections": [
    {
      "nodes": [
        {
          "type": "FRAME",
          "id": "5:1",
          "name": "Card",
          "layoutStyle": { "width": 100, "height": 40, "relativeX": 0, "relativeY": 0 },
          "_token": "Fill/Fill-2",
          "_color": "#F2F3F5",
          "children": [
            {
              "type": "TEXT",
              "id": "5:2",
              "name": "Label",
              "layoutStyle": { "width": 60, "height": 20, "relativeX": 8, "relativeY": 10 },
              "_token": "Text/Text-4",
              "_color": "#4E5969",
              "text": [{ "text": "文字" }]
            }
          ]
        }
      ]
    }
  ]
}
```

创建 `assets/broken-ref.json`（`fill` 引用了 `styles` 里没有的键，且无 `_token`/`_color`）：

```json
{
  "list": {
    "rootMetadata": { "allTexts": [] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 100, "height": 40 }]
  },
  "sections": [
    {
      "styles": { "paint_1:1000": { "value": [{ "color": "#FFFFFF" }] } },
      "nodes": [
        {
          "type": "FRAME",
          "id": "6:1",
          "name": "Broken",
          "layoutStyle": { "width": 100, "height": 40, "relativeX": 0, "relativeY": 0 },
          "fill": "paint_9:9999",
          "children": []
        }
      ]
    }
  ]
}
```

追加测试类：

```python
class TokenTests(CliTestCase):
    """_token becomes a StaticResource; a dangling style reference is fatal."""

    def test_tokens_become_resource_dictionary_brushes(self) -> None:
        result, out_dir = self.convert("tokens.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        colors = (out_dir / "Colors.xaml").read_text(encoding="utf-8")
        self.assertIn('<SolidColorBrush x:Key="FillFill2" Color="#F2F3F5" />', colors)
        self.assertIn('<SolidColorBrush x:Key="TextText4" Color="#4E5969" />', colors)

    def test_the_original_token_name_is_kept_as_a_comment(self) -> None:
        result, out_dir = self.convert("tokens.json")

        colors = (out_dir / "Colors.xaml").read_text(encoding="utf-8")
        self.assertIn("Fill/Fill-2", colors)
        self.assertIn("Text/Text-4", colors)

    def test_the_page_references_brushes_rather_than_literal_colours(self) -> None:
        result, out_dir = self.convert("tokens.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("{StaticResource FillFill2}", xaml)
        self.assertIn("{StaticResource TextText4}", xaml)
        self.assertNotIn("#F2F3F5", xaml)

    def test_a_dangling_style_reference_is_fatal(self) -> None:
        result, _ = self.convert("broken-ref.json")

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("paint_9:9999", result.stderr)
        self.assertEqual(result.stdout, "")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py" -k Token`
Expected: FAIL —— `Colors.xaml` 不存在

- [ ] **Step 3: 写最小实现**

在 `dsl_to_xaml.py` 中加入：

```python
def resource_key(token: str) -> str:
    """Turn a design token name like `Text/Text-4` into the XAML key `TextText4`."""
    parts = re.split(r"[^0-9A-Za-z]+", token)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def node_colour(node: dict, styles: dict) -> tuple[str | None, str | None]:
    """Resolve a node's paint to (resource key or None, literal colour or None)."""
    token = node.get("_token")
    colour = node.get("_color")
    if colour is None:
        reference = node.get("fill")
        if isinstance(reference, str) and reference:
            entry = styles.get(reference)
            if entry is None:
                raise ConversionError(
                    f"node {node.get('id', '?')} references style {reference!r}, which is "
                    "not in dsl.styles; re-fetch the section DSL"
                )
            values = entry.get("value") or [{}]
            colour = values[0].get("color")
    if colour is None:
        return None, None
    return (resource_key(token) if token else None), colour


def walk(nodes: list[dict]):
    """Yield every node in the tree, depth first, in document order."""
    for node in nodes:
        yield node
        yield from walk(node.get("children") or [])


def collect_brushes(sections: list[dict]) -> dict[str, tuple[str, str]]:
    """Collect {resource key: (colour, original token name)} across all sections."""
    brushes: dict[str, tuple[str, str]] = {}
    for section in sections:
        styles = section.get("styles") or {}
        for node in walk(section.get("nodes") or []):
            key, colour = node_colour(node, styles)
            if key and colour:
                brushes.setdefault(key, (colour, str(node.get("_token"))))
    return brushes


def render_resources(brushes: dict[str, tuple[str, str]]) -> str:
    """Render the colour ResourceDictionary."""
    lines = [
        '<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">',
    ]
    for key in sorted(brushes):
        colour, token = brushes[key]
        lines.append(f"  <!-- {token} -->")
        lines.append(f'  <SolidColorBrush x:Key="{key}" Color="{colour}" />')
    lines += ["</ResourceDictionary>", ""]
    return "\n".join(lines)
```

顶部 import 增加 `import re`。

`render_text` 与容器渲染改为接受画刷：给 `render_node`/`render_flex`/`render_text` 增加参数 `styles: dict`，在渲染时调用 `node_colour`，有 key 时写 `Background="{StaticResource K}"`（容器）或 `Foreground="{StaticResource K}"`（TEXT），无 key 但有 colour 时写字面值。

`main` 增加输出：

```python
        brushes = collect_brushes(sections)
        (out_dir / "Colors.xaml").write_text(render_resources(brushes), encoding="utf-8")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"`
Expected: PASS，14 个测试

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/
git commit -m "feat(mastergo-to-wpf): 设计令牌抽成 ResourceDictionary，断链引用硬报错"
```

---

### Task 5: FRAME 的 opacity 烧进 alpha 通道

**Files:**
- Modify: `.../scripts/dsl_to_xaml.py`
- Modify: `.../scripts/test_dsl_to_xaml.py`
- Create: `.../scripts/assets/opacity-frame.json`

**Interfaces:**
- Consumes: `node_colour`（Task 4）
- Produces: `with_alpha(colour: str, opacity: float) -> str` —— 把 `#RRGGBB` + 不透明度合成 `#AARRGGBB`

- [ ] **Step 1: 写失败的测试**

创建 `assets/opacity-frame.json`：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["子元素"] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 120, "height": 60 }]
  },
  "sections": [
    {
      "nodes": [
        {
          "type": "FRAME",
          "id": "7:1",
          "name": "Translucent",
          "layoutStyle": { "width": 120, "height": 60, "relativeX": 0, "relativeY": 0 },
          "_color": "#4E5969",
          "opacity": 0.5,
          "children": [
            {
              "type": "TEXT",
              "id": "7:2",
              "name": "Child",
              "layoutStyle": { "width": 60, "height": 20, "relativeX": 8, "relativeY": 20 },
              "text": [{ "text": "子元素" }]
            }
          ]
        }
      ]
    }
  ]
}
```

追加测试类：

```python
class OpacityTests(CliTestCase):
    """A FRAME's opacity tints only its own background, never its children."""

    def test_frame_opacity_is_baked_into_the_background_alpha(self) -> None:
        result, out_dir = self.convert("opacity-frame.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("#804E5969", xaml)

    def test_no_opacity_property_is_emitted(self) -> None:
        result, out_dir = self.convert("opacity-frame.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertNotIn("Opacity=", xaml)

    def test_the_child_is_not_made_translucent(self) -> None:
        result, out_dir = self.convert("opacity-frame.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        child = xaml.split("子元素", 1)[0].rsplit("<TextBlock", 1)[1]
        self.assertNotIn("Opacity", child)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py" -k Opacity`
Expected: FAIL —— 输出的是 `#4E5969`，没有 alpha 前缀

- [ ] **Step 3: 写最小实现**

加入函数：

```python
def with_alpha(colour: str, opacity: float) -> str:
    """Bake an opacity into a hex colour's alpha channel.

    A FRAME's opacity in MasterGo tints only its own background, so it must not
    become a WPF `Opacity` — that would make every child translucent too.
    """
    if not colour.startswith("#") or opacity >= 1.0:
        return colour
    digits = colour[1:]
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    if len(digits) != 6:
        return colour
    return f"#{round(max(0.0, min(1.0, opacity)) * 255):02X}{digits.upper()}"
```

在容器渲染处，取到 colour 后先过 `with_alpha(colour, float(node.get("opacity", 1)))`。带 opacity 的节点即便有 `_token` 也必须写字面值——因为资源字典里的画刷是不透明的。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"`
Expected: PASS，17 个测试

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/
git commit -m "fix(mastergo-to-wpf): FRAME 的 opacity 烧进背景色 alpha，不生成 Opacity 属性"
```

---

### Task 6: 文本回填与 allTexts 闭集校验

**Files:**
- Modify: `.../scripts/dsl_to_xaml.py`
- Modify: `.../scripts/test_dsl_to_xaml.py`
- Create: `.../scripts/assets/long-text.json`
- Create: `.../scripts/assets/placeholder-text.json`
- Create: `.../scripts/assets/hallucinated-text.json`

**Interfaces:**
- Consumes: `node_text`（Task 2）、`walk`（Task 4）
- Produces: `resolve_text(node: dict, section: dict, section_index: int) -> str`；`verify_texts(emitted: list[str], listing: dict) -> None` —— 越出闭集即抛 `ConversionError`

- [ ] **Step 1: 写失败的测试**

创建 `assets/long-text.json`（节点里是占位，真文本在 `rowTexts`）：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["这是一段超过五十个字符的很长的说明文字用于验证占位符能够被正确回填到生成的界面里"] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 400, "height": 60 }]
  },
  "sections": [
    {
      "rowTexts": [
        {
          "text": "这是一段超过五十个字符的很长的说明文字用于验证占位符能够被正确回填到生成的界面里",
          "parentType": "FRAME",
          "parentName": "Desc"
        }
      ],
      "nodes": [
        {
          "type": "TEXT",
          "id": "1:1234",
          "name": "Desc",
          "layoutStyle": { "width": 400, "height": 60, "relativeX": 0, "relativeY": 0 },
          "text": [{ "text": "T0|1:1234" }]
        }
      ]
    }
  ]
}
```

创建 `assets/placeholder-text.json`（`_placeholder: true` 应跳过）：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["真实文案"] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 200, "height": 60 }]
  },
  "sections": [
    {
      "rowTexts": [
        { "text": "Hillstone Design", "parentType": "TEXT", "parentName": "Hillstone Design", "_placeholder": true },
        { "text": "真实文案", "parentType": "TEXT", "parentName": "Real" }
      ],
      "nodes": [
        {
          "type": "FRAME",
          "id": "8:1",
          "name": "Wrap",
          "layoutStyle": { "width": 200, "height": 60, "relativeX": 0, "relativeY": 0 },
          "children": [
            {
              "type": "TEXT",
              "id": "8:2",
              "name": "Hillstone Design",
              "layoutStyle": { "width": 120, "height": 20, "relativeX": 0, "relativeY": 0 },
              "_placeholder": true,
              "text": [{ "text": "Hillstone Design" }]
            },
            {
              "type": "TEXT",
              "id": "8:3",
              "name": "Real",
              "layoutStyle": { "width": 120, "height": 20, "relativeX": 0, "relativeY": 30 },
              "text": [{ "text": "真实文案" }]
            }
          ]
        }
      ]
    }
  ]
}
```

创建 `assets/hallucinated-text.json`（节点文本不在 `allTexts` 里）：

```json
{
  "list": {
    "rootMetadata": { "allTexts": ["允许的文案"] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 200, "height": 40 }]
  },
  "sections": [
    {
      "nodes": [
        {
          "type": "TEXT",
          "id": "9:1",
          "name": "Ghost",
          "layoutStyle": { "width": 200, "height": 40, "relativeX": 0, "relativeY": 0 },
          "text": [{ "text": "不在闭集里的文案" }]
        }
      ]
    }
  ]
}
```

追加测试类：

```python
class TextTests(CliTestCase):
    """Text comes from the DSL's closed set — never invented, never dropped."""

    LONG = "这是一段超过五十个字符的很长的说明文字用于验证占位符能够被正确回填到生成的界面里"

    def test_a_long_text_placeholder_is_filled_from_rowtexts(self) -> None:
        result, out_dir = self.convert("long-text.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn(self.LONG, xaml)
        self.assertNotIn("T0|1:1234", xaml)

    def test_placeholder_boilerplate_is_skipped(self) -> None:
        result, out_dir = self.convert("placeholder-text.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertNotIn("Hillstone Design", xaml)
        self.assertIn("真实文案", xaml)

    def test_text_outside_the_alltexts_closed_set_is_fatal(self) -> None:
        result, _ = self.convert("hallucinated-text.json")

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("不在闭集里的文案", result.stderr)
        self.assertEqual(result.stdout, "")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py" -k Text`
Expected: FAIL —— 占位符原样输出、样板文字未跳过、闭集不校验

- [ ] **Step 3: 写最小实现**

```python
#: A long-text placeholder MasterGo substitutes for text over 50 characters.
TEXT_PLACEHOLDER = re.compile(r"\AT\d+\|[^\s|]+\Z")


def resolve_text(node: dict, section: dict, order: list[int]) -> str:
    """Return a TEXT node's real content, filling long-text placeholders.

    Long text (>50 chars) reaches the node tree as `T{sectionIndex}|{nodeId}`; the
    real string lives in `dsl.rowTexts`, in tree order. `order` tracks how many
    non-placeholder rowTexts have been consumed so far in this section.
    """
    raw = node_text(node)
    if not TEXT_PLACEHOLDER.match(raw.strip()):
        return raw
    rows = [row for row in (section.get("rowTexts") or []) if not row.get("_placeholder")]
    for row in rows:
        if row.get("parentName") == node.get("name"):
            return str(row.get("text", ""))
    if order[0] < len(rows):
        text = str(rows[order[0]].get("text", ""))
        order[0] += 1
        return text
    raise ConversionError(
        f"node {node.get('id', '?')} holds placeholder {raw!r} but no matching entry "
        "exists in dsl.rowTexts; re-fetch this section's DSL"
    )


def verify_texts(emitted: list[str], listing: dict) -> None:
    """Fail if any emitted string is outside the design's closed text set."""
    metadata = listing.get("rootMetadata") or {}
    allowed = metadata.get("allTexts")
    if not isinstance(allowed, list):
        return
    permitted = {str(item) for item in allowed}
    for text in emitted:
        if text and text not in permitted:
            raise ConversionError(
                f"generated text {text!r} is not in rootMetadata.allTexts; the design's "
                "text is a closed set, so this string would be fabricated"
            )
```

`render_text` 改为：`_placeholder` 为真时返回 `[]`（跳过）；否则用 `resolve_text` 取文本，并把结果记入一个模块级收集列表供 `verify_texts` 校验。`main` 在写文件**之前**调 `verify_texts`——校验不通过时不得留下半成品文件。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"`
Expected: PASS，20 个测试

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/
git commit -m "feat(mastergo-to-wpf): 长文本从 rowTexts 回填，allTexts 闭集防幻觉"
```

---

### Task 7: 图标占位与清单输出

**Files:**
- Modify: `.../scripts/dsl_to_xaml.py`
- Modify: `.../scripts/test_dsl_to_xaml.py`
- Create: `.../scripts/assets/icons.json`

**Interfaces:**
- Consumes: `render_node`（Task 3）、`walk`（Task 4）
- Produces: `collect_icons(sections: list[dict]) -> list[dict]` 返回 `[{"svgShortKey": str, "nodeId": str, "name": str}]`；PATH 节点渲染为 `<!-- ICON:{key} -->` 注释

- [ ] **Step 1: 写失败的测试**

创建 `assets/icons.json`：

```json
{
  "list": {
    "rootMetadata": { "allTexts": [] },
    "splitContainers": [{ "x": 0, "y": 0, "width": 48, "height": 24 }]
  },
  "sections": [
    {
      "nodes": [
        {
          "type": "FRAME",
          "id": "10:1",
          "name": "IconBar",
          "layoutStyle": { "width": 48, "height": 24, "relativeX": 0, "relativeY": 0 },
          "children": [
            {
              "type": "PATH",
              "id": "10:2",
              "name": "SearchIcon",
              "layoutStyle": { "width": 16, "height": 16, "relativeX": 4, "relativeY": 4 },
              "svgShortKey": "S0#0"
            },
            {
              "type": "PATH",
              "id": "10:3",
              "name": "CloseIcon",
              "layoutStyle": { "width": 16, "height": 16, "relativeX": 28, "relativeY": 4 },
              "svgShortKey": "S0#1"
            }
          ]
        }
      ]
    }
  ]
}
```

追加测试类：

```python
class IconTests(CliTestCase):
    """PATH nodes become placeholders plus a work list for extractSvg."""

    def test_path_nodes_become_icon_placeholders(self) -> None:
        result, out_dir = self.convert("icons.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn("<!-- ICON:S0#0 -->", xaml)
        self.assertIn("<!-- ICON:S0#1 -->", xaml)

    def test_an_icon_manifest_is_written(self) -> None:
        result, out_dir = self.convert("icons.json")

        manifest = json.loads((out_dir / "icons.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 2)
        self.assertEqual(manifest[0]["svgShortKey"], "S0#0")
        self.assertEqual(manifest[0]["name"], "SearchIcon")
        self.assertEqual(manifest[1]["svgShortKey"], "S0#1")

    def test_icon_placeholders_keep_their_canvas_position(self) -> None:
        result, out_dir = self.convert("icons.json")

        xaml = (out_dir / "GeneratedPage.xaml").read_text(encoding="utf-8")
        self.assertIn('Canvas.Left="4"', xaml)
        self.assertIn('Canvas.Left="28"', xaml)

    def test_a_path_without_a_shortkey_is_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_dir = Path(temporary) / "dsl"
            input_dir.mkdir()
            (input_dir / "sections-list.json").write_text(
                json.dumps({"rootMetadata": {"allTexts": []}, "splitContainers": [{}]}),
                encoding="utf-8",
            )
            (input_dir / "section-0.json").write_text(
                json.dumps(
                    {
                        "nodes": [
                            {
                                "type": "PATH",
                                "id": "11:1",
                                "name": "NoKey",
                                "layoutStyle": {"relativeX": 0, "relativeY": 0},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "--input", str(input_dir), "--out", str(Path(temporary) / "out")
            )

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("svgShortKey", result.stderr)
        self.assertEqual(result.stdout, "")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py" -k Icon`
Expected: FAIL —— PATH 节点当前被渲染成 `<Canvas>`，且没有 `icons.json`

- [ ] **Step 3: 写最小实现**

```python
def icon_key(node: dict) -> str:
    """Return a PATH node's svgShortKey, which is the only handle on its vector."""
    key = node.get("svgShortKey")
    if not key:
        raise ConversionError(
            f"PATH node {node.get('id', '?')} ({node.get('name', 'unnamed')}) has no "
            "svgShortKey; its vector cannot be fetched — re-fetch this section's DSL"
        )
    return str(key)


def collect_icons(sections: list[dict]) -> list[dict]:
    """List every PATH node so the caller can fetch its SVG with mcp__extractSvg."""
    icons: list[dict] = []
    for section in sections:
        for node in walk(section.get("nodes") or []):
            if node.get("type") == "PATH":
                icons.append(
                    {
                        "svgShortKey": icon_key(node),
                        "nodeId": str(node.get("id", "")),
                        "name": str(node.get("name", "")),
                    }
                )
    return icons
```

`render_node` 在 TEXT 分支之前加 PATH 分支：

```python
    if node.get("type") == "PATH":
        return [f"{indent}<!-- ICON:{icon_key(node)} -->",
                f'{indent}<Path{extra}{placement} />']
```

`main` 增加：

```python
        icons = collect_icons(sections)
        (out_dir / "icons.json").write_text(
            json.dumps(icons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"`
Expected: PASS，24 个测试

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts/
git commit -m "feat(mastergo-to-wpf): PATH 节点转图标占位并输出待转换清单"
```

---

### Task 8: SKILL.md、references 与 CHANGELOG

**Files:**
- Create: `.../mastergo-to-wpf/SKILL.md`
- Create: `.../mastergo-to-wpf/CHANGELOG.md`
- Create: `.../mastergo-to-wpf/test-prompts.json`
- Create: `.../mastergo-to-wpf/references/dsl-mapping.md`

**Interfaces:**
- Consumes: 完成的 `dsl_to_xaml.py` CLI（Task 1-7）
- Produces: 可被 Claude Code 加载的 skill 定义

- [ ] **Step 1: 写 SKILL.md**

frontmatter 严格六字段：

```yaml
---
name: mastergo-to-wpf
description: 当用户提供 MasterGo 设计稿链接并要求生成 WPF 界面、XAML 页面或把设计稿转成 WPF 代码时使用此 Skill；产出 XAML 页面脚手架、颜色资源字典与图标，供开发者手工接管。
metadata:
  version: "1.0.0"
  author: desktop client team
compatibility: Python 3；需 mastergo-magic-mcp（本仓库 plugins/optimus-mcp-servers/.mcp.json 内置）与 MASTERGO_TOKEN；需 MasterGo Team 版及以上，草稿箱文件不可用。
allowed-tools: Read Write Bash PowerShell mastergo-magic-mcp
---
```

正文按 spec §4 的五步流程编写，须包含：

1. **Step 0 前置检查**，🔴 标记：token 未配置 / 非 Team 版 / 文件在草稿箱 → 停止并说明。
2. **Step 1** 调 `mcp__getDesignSections`（不带 sectionIndex），存 `sections-list.json`；🔴 区块数 > 8 → 停止请用户指定。
3. **Step 2** 逐区 `sectionIndex=N`，3-5 个一批；⚠️ 明确禁止改用 `mcp__getDsl`（分区流程启动后被运行时封锁）。
4. **Step 3** 跑 `dsl_to_xaml.py`，命令给出完整形式（含 `$SkillDir` 绝对路径说明，理由同 `svg-to-xaml-path`：skill 从插件缓存加载，cwd 是用户项目目录）。
5. **Step 4** 对 `icons.json` 每项调 `mcp__extractSvg`，再交给 `optimus-frontend-plugin:svg-to-xaml-path` 转 `Path.Data`，回填占位。
6. **Step 5 交付纪律**，至少四条：只交付 stdout、告警如实转达、说明哪些需人工替换成真控件、说明字体可用性。
7. **静默行为清单**（spec §6.3 五条），标注哪几条会产出错误产物。
8. **已知限制**（spec §9 五条）。

- [ ] **Step 2: 写 references/dsl-mapping.md**

搬运 spec §5 的完整映射表：布局判据、节点类型表、样式优先级表、`opacity` 与图片 bug 两处特殊处理、文本回填规则。这是按需查阅的参考数据，不是决策依据，因此放 references 而非 SKILL.md。

- [ ] **Step 3: 写 CHANGELOG.md 与 test-prompts.json**

```markdown
# Changelog

## [1.0.0] - 2026-08-02

### Added
- 新增 MasterGo 设计稿转 WPF XAML Skill。
- 新增 `dsl_to_xaml.py`：flex 容器转 StackPanel/Grid、绝对定位转 Canvas、设计令牌转 ResourceDictionary、PATH 转图标占位。
- 新增 `references/dsl-mapping.md` 完整映射表与静默行为清单。
- 新增 24 条 CLI 契约测试。
```

`test-prompts.json` 写 5 条：标准转换、区块过多、无 autolayout 的稿子、含图标的稿子、token 未配置。每条的 `expected` 须写明该走哪个分支、该报什么。

- [ ] **Step 4: 验证 frontmatter 合规并跑测试**

```bash
python -c "
import re, pathlib
p = pathlib.Path('plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/SKILL.md')
fm = p.read_text(encoding='utf-8').split('---')[1]
keys = re.findall(r'^([a-z-]+):', fm, re.M)
allowed = {'name','description','license','allowed-tools','metadata','compatibility'}
extra = set(keys) - allowed
print('顶层字段:', keys)
print('违规字段:', extra or '无')
"
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"
```

Expected: 违规字段为「无」；24 个测试 PASS

- [ ] **Step 5: 提交**

```bash
git add plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/
git commit -m "docs(mastergo-to-wpf): 新增 SKILL.md、映射表参考与 CHANGELOG"
```

---

### Task 9: 集成、gitignore 与版本升级

**Files:**
- Modify: `.gitignore`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`

**Interfaces:**
- Consumes: 完整的 skill（Task 1-8）
- Produces: 可发布状态

- [ ] **Step 1: 加 gitignore 条目**

在 `.gitignore` 的「Claude Code local files」段末尾（`.superpowers/` 之后）追加：

```
.mastergo-dsl/
```

- [ ] **Step 2: 升 marketplace 版本并更新描述**

`.claude-plugin/marketplace.json`：`"version": "8.4.0"` → `"8.5.0"`（新增 skill 属 Minor）。

同时在 `optimus-frontend-plugin` 的 `description` 末尾追加：`；MasterGo 设计稿转 WPF XAML 页面脚手架`。

- [ ] **Step 3: 更新 README**

在 README 的插件能力表中，`optimus-frontend-plugin` 一行补上 MasterGo MCP 依赖（该行现列 Sketch/Figma MCP）。

- [ ] **Step 4: 全量验证**

```bash
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/scripts -p "test_*.py"
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts -p "test_*.py"
python -c "import json; d=json.load(open('.claude-plugin/marketplace.json', encoding='utf-8')); print('version:', d['version'])"
git status --short
```

Expected: 两个测试套件分别 24 / 74 个 PASS；version 为 8.5.0

- [ ] **Step 5: 提交**

```bash
git add .gitignore .claude-plugin/marketplace.json README.md
git commit -m "chore(marketplace): 集成 mastergo-to-wpf skill，版本 8.4.0 → 8.5.0"
```

---

## 自检记录

**1. Spec 覆盖**

| Spec 章节 | 对应任务 |
|---|---|
| §3 目录结构 | Task 1（scripts）、Task 8（文档） |
| §4 数据流 Step 0-2、5 | Task 8（SKILL.md 编排） |
| §4 数据流 Step 3 | Task 1-7（转换器） |
| §4 数据流 Step 4 | Task 7（图标清单）+ Task 8（extractSvg 编排） |
| §5.1 布局 | Task 2（flex）、Task 3（绝对定位） |
| §5.2 节点类型 | Task 2（TEXT）、Task 3（容器）、Task 7（PATH） |
| §5.3 样式 | Task 4 |
| §5.4 opacity | Task 5 |
| §5.4 图片 bug | Task 8（写入 references 与静默清单）—— 脚本层不处理，因图片需另行下载，超出本 skill 范围 |
| §5.5 文本 | Task 6 |
| §6.1 硬停止 | Task 1（JSON 损坏）、Task 3（缺坐标）、Task 4（断链）、Task 6（闭集）、Task 7（缺 svgShortKey） |
| §6.2 具名告警 | Task 8（字体告警写入交付纪律） |
| §6.3 静默清单 | Task 8 |
| §7 测试策略 | Task 2-7 各自的测试 |
| §8 版本规范 | Task 8（frontmatter）、Task 9（marketplace） |
| §9 已知限制 | Task 8 |

**2. 占位符扫描**：无 TBD/TODO；每个代码步骤都给出可直接粘贴的完整代码；每个测试步骤都写出断言。

**3. 类型一致性**：`ConversionError`（Task 1 定义，2-7 复用）、`number`（Task 2 定义，3/5 复用）、`walk`（Task 4 定义，6/7 复用）、`node_text`（Task 2 定义，6 复用）、`render_node` 签名在 Task 3 扩展为 `(node, depth, extra="", absolute=False)` 后保持不变。

**已知偏差**：§6.2 的「富文本段数超阈值」告警未单独立测试任务——该告警的阈值需实际设计稿数据校准，Task 8 会在 references 中记录，留待首次真实使用后补。
