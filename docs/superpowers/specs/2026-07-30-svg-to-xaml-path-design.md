# SVG to XAML Path Skill 设计

**日期：** 2026-07-30\
**Skill 目录：** `plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/`\
**调用名：** `/optimus-frontend-plugin:svg-to-xaml-path`

## 目标

提供一个可重复使用的前端插件 Skill：输入 SVG 源码或本地 SVG 文件路径，按 SVG 文档顺序提取所有 `<path>` 元素的 `d` 属性，并输出可直接赋给一个 WPF `Path.Data` 的合并 Geometry 字符串和可粘贴的 XAML。

样例 `C:\Users\Administrator\Downloads\AI问答.svg` 有两个相同 `fill`（`#B8C6E0`）的 `<path>`，其两个 `d` 值可按文档顺序以空白符连接，作为同一个 WPF `Path.Data` 的多个 figure；不需要 Inkscape。

## 范围

### 包含

- SVG 文件路径、内联 SVG 源码和标准输入三种输入。
- 仅处理 `<path d="...">`，保持其在 SVG 中的原始顺序。
- 输出模式：纯 `Path.Data`、WPF XAML。
- 提取路径及其祖先元素的 `fill` 与 `stroke` 演示属性；所有路径样式一致时生成一个带样式的 WPF `Path`。
- 无路径、`d` 缺失、无效 XML、不同样式或未处理的 `transform` 等显式诊断。
- 不依赖第三方 Python 包或 Inkscape。

### 不包含

- SVG 布尔运算（Union、Difference、Intersect）或轮廓重建。
- 将 `rect`、`circle`、`ellipse`、`polygon`、`use` 等非 `<path>` SVG 元素转换为路径。
- 读取或转换 SVG 根元素的 `viewBox`，以及输出 WPF `Viewbox`。
- 展平 `transform`。检测到路径或祖先元素的 `transform` 时，默认报出无法无损转换的原因，不产出可能位置错误的单一 Geometry。
- 在单一 WPF `Path` 中保留多组不同 `fill` 或 `stroke`。这是 WPF 元素模型的限制。

## 架构

### Skill 文档

`SKILL.md` 定义触发条件、输入识别顺序、脚本调用方式、输出格式和边界处理。Skill 明确区分：

- **多 figure 合并**：把多个 SVG `d` 片段串接到一个 WPF Geometry 字符串中；这是本 Skill 的默认能力。
- **布尔合并**：把重叠轮廓计算成一个新轮廓；此操作改变几何，需专门的几何库或 Inkscape，不由本 Skill 执行。

`CHANGELOG.md` 记录初始 `1.0.0` 版本；`test-prompts.json` 放置针对文件、内联 SVG、样式冲突与限制说明的测试情景。

### Python 脚本

`scripts/merge_svg_paths.py` 使用 Python 标准库 `xml.etree.ElementTree` 和 `argparse`：

```text
python scripts/merge_svg_paths.py --file icon.svg --format xaml
python scripts/merge_svg_paths.py --svg '<svg ...>...</svg>' --format data
Get-Content icon.svg | python scripts/merge_svg_paths.py --stdin --format data
```

输入参数 `--file`、`--svg` 和 `--stdin` 互斥且必须提供其一。`--format` 值为 `data` 或 `xaml`，默认 `xaml`。

脚本遍历 XML 树并通过标签的本地名匹配命名空间 SVG 中的 `<path>`。对于每个有效 `d`，解析其祖先链中显式声明的 `fill`、`stroke` 和 `transform`。所有 path 片段以一个空格连接，确保命令边界明确。正常转换结果写入标准输出；警告和错误写入标准错误。

### 样式与变换策略

- 所有路径的有效 `fill` 与 `stroke` 相同：生成单一 XAML `Path`，并设置可确定的 `Fill`、`Stroke`。
- 路径样式不同或部分未设置：`data` 输出仍会给出可用的合并 Geometry；`xaml` 输出不伪造单一视觉样式，而是写入警告并输出按路径/样式分组的多个 `Path`。
- 检测到任何路径或祖先有 `transform`：脚本以非零退出状态终止，说明应先在 SVG 编辑器中应用变换或扩展脚本。这样不会输出错误位置的 WPF 图形。
- SVG `style="..."` 属性与 CSS class、外部样式表不在第一版支持范围内；脚本明确报告，Skill 说明需要将关键样式内联为 `fill`/`stroke` 后再转换。

## 输出示例

对样例文件，纯数据输出为：

```text
M603.428571 ... z M325.12 ... z
```

XAML 输出结构为：

```xml
<Path Fill="#B8C6E0" Data="M... z M... z" />
```

## 错误处理

| 情况 | 脚本行为 |
|---|---|
| 文件不存在、无法解码或 XML 无效 | 标准错误输出原因，返回非零状态 |
| 没有 `<path>` 或所有 path 均无 `d` | 标准错误输出原因，返回非零状态 |
| 发现 `transform` | 标准错误输出具体 path/祖先位置，返回非零状态 |
| path 样式不一致 | `data` 可继续输出；`xaml` 生成保真多 Path 并写入警告 |
| 有未处理 `style`/CSS | 保留 `d`，输出警告，禁止声称样式已保留 |

## 测试与验证

先创建并执行 `scripts/test_merge_svg_paths.py` 的失败测试，再实现脚本。测试使用 Python `unittest` 和临时 SVG 文件，覆盖：

1. 命名空间 SVG 中两个同样式 path 合并为一个 `Path.Data`。
2. 文件、内联 SVG 与标准输入三种入口。
3. 无 `<path>` 时失败且包含清晰错误。
4. 不同填充色时产生警告，且 XAML 输出多个 `Path`，不声称输出单一保真 Path。
5. `transform` 时失败，不输出误导性 Geometry。

完成后执行：

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/test_merge_svg_paths.py -v
python plugins/optimus-frontend-plugin/skills/svg-to-xaml-path/scripts/merge_svg_paths.py --file 'C:\Users\Administrator\Downloads\AI问答.svg' --format xaml
```

还会检查 `SKILL.md` YAML frontmatter、`test-prompts.json` 和 `.claude-plugin/marketplace.json` 是否可解析；新增 Skill 使 marketplace 版本从 `8.0.6` 升至 `8.1.0`。README 将补充其调用方式。
