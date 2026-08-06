# SVG to WPF XAML Path Skill 设计

**日期：** 2026-08-06\
**Skill 目录：** `plugins/optimus-frontend-plugin/skills/svg-to-wpf-xaml-path/`\
**调用名：** `/optimus-frontend-plugin:svg-to-wpf-xaml-path`

## 目标

按用户提供的门禁文档（`svg-to-wpf-xaml-path/门禁.md` 的初步要求）实现：输入 SVG（内联代码 / 单文件路径 / 文件夹路径），提取或合并 `<path>` 的几何数据，输出为 WPF `PathGeometry` 资源，追加或新建到目标 `Icons.xaml`。

**本版本相对首版设计做了大幅简化。** 首版让 Python 自己实现 `rect`/`circle`/`ellipse`/`polyline`/`polygon` 的 SVG 2 等价路径公式，并支持了门禁文档未提及的 `--stdin` 输入和 Icons.xaml key 冲突自动改名逻辑——审查后判断这些超出了门禁文档的最小范围，决定收窄：

- **几何转换的重活交给 Inkscape**：基本图形转 path（`object-to-path`）与多 path 同 fill 合并（`path-combine`）都通过一次 Inkscape `--actions` 调用完成，Python 不再手写几何公式。
- **业务规则判断保留在 Python**：transform 检测、fill 比对、渐变检测——这些 Inkscape 不会做，或者做了会静默丢数据，必须留在 Python 侧。
- **输入范围回归门禁文档原文**：只支持内联 SVG 代码 / 单文件路径 / 文件夹路径三种，不做 `--stdin`。
- **Icons.xaml key 冲突直接报错**，不做自动改名为数字后缀。

与已删除的 `svg-to-xaml-path`（输出 `Path.Data`/`Path` 元素，多 path 靠字符串拼接、不依赖 Inkscape）不同，本 Skill 输出格式固定为 `<PathGeometry x:Key="...">` 资源条目，与仓库现有 `references/Sample-Icons.xaml` 的写法对齐。

## 关键技术验证（实测结论）

在确定架构前，用本机 Inkscape 1.4.4 做了三组实测，结论直接决定了下面的范围划分：

1. **`object-to-path` + `path-combine` 不会展平 transform。** 对 `<g transform="translate(4 4) rotate(45)"><rect .../></g>` 跑动作链后，`<rect>` 被正确转换为 `<path>`，但外层 `<g transform="...">` 原样保留，`d` 仍是局部坐标。若只读取 `<path>` 的 `d` 拼进 `PathGeometry` 字符串，会静默丢失变换信息——**因此 transform 检测必须留在 Python，检测到就报错，不能寄望 Inkscape 处理**。
2. **无 transform 时，基本图形转换与合并是可靠的。** `<rect>` + `<circle>`（同 fill、无 transform）跑 `select-all;object-to-path;path-combine` 后正确合并为一个精确的 `<path>`，坐标无近似误差。
3. **`path-combine` 对不同 fill 的图形会静默丢色，不报错。** 把 `fill="#111111"` 的 `rect` 和 `fill="#222222"` 的 `circle` 跑同一条动作链，Inkscape 把两者合并成一个 path，**只保留后画元素的颜色（`#222222`），`#111111` 被完全丢弃，且没有任何错误或警告**。这证实了"fill 比对必须在调用 Inkscape 之前由 Python 完成，不能依赖 Inkscape 自行判断能不能合并"这一决策是必要的，不是过度设计。

## 范围

### 包含

- 三种输入：内联 SVG 代码、单个 SVG 文件路径、含多个 SVG 的文件夹路径。
- 门禁检查：Inkscape CLI 在 PATH 中可执行、输入路径有效、输出路径有效——任一不满足直接报错停止，不降级、不猜测。
- `<path>` 与基本图元（`rect`/`circle`/`ellipse`/`line`/`polyline`/`polygon`）统一视为候选转换元素；几何转换（基本图元→path、多元素合并）通过一次 Inkscape `--actions` 调用完成。
- 单个候选元素：若是 `<path>` 直接提取 `d`；若是基本图元，仍交给 Inkscape 跑一次 `object-to-path` 取得 `d`（不为"只有一个"单独写公式，复用同一条 Inkscape 调用路径）。
- 多个候选元素且 `fill` presentation attribute 全同：整份 SVG 交给 Inkscape 执行 `select-all;object-to-path;path-combine;export-filename:...;export-do`，取导出结果中合并后的单一 `<path>` 的 `d`。
- 多个候选元素且 `fill` 不同：单文件场景报错提示用户自行处理；文件夹批量场景跳过该文件，继续处理其余文件，最终汇总列出跳过清单。
- `x:Key` 命名：文件名（kebab-case/snake_case）按 `-`/`_` 分词转 PascalCase + `Geometry` 后缀；无文件名（内联 SVG 代码）时要求用户显式提供 `--key`，原样使用不加后缀。
- 输出落盘：指定输出路径且目标 `Icons.xaml` 已存在时，解析已有 `x:Key`，用文本拼接方式（在 `</ResourceDictionary>` 前插入新行）追加，不改变文件其余部分；key 冲突直接报错，不覆盖、不改名；未指定输出路径时只在对话中给出 `PathGeometry` 片段，不自动建文件。

### 不包含

- **Python 自行实现基本图元的几何等价公式**：这部分交给 Inkscape 的 `object-to-path` 完成，不复用旧 `svg-to-xaml-path` skill 的 SVG 2 公式代码。
- **`--stdin` 输入**：门禁文档未提及，不在本版本范围。
- **Icons.xaml key 冲突自动改名**：门禁文档只说"追加或新建"，未定义冲突时的改名规则；发现冲突直接报错，交给用户自行处理。
- CSS 完整级联处理：仅比对 `fill` 的 presentation attribute 本身，不解析 `style=""`、父级继承、CSS class、`<style>` 元素（含 `<style>` 时告警提示用户核实真实颜色，但不阻断转换）。
- `transform`：候选元素或其任意父级元素带 `transform` 直接报错，要求先在源 SVG 中展平——已实测证实 Inkscape 不会自动展平，且 `PathGeometry` 字符串无法携带矩阵信息。
- 布尔几何运算（Union/Difference/Intersect）：多元素不同 fill 时不允许用几何布尔或降级为单色来强行合并（且已证实 Inkscape 的 Combine 在此场景会静默丢色，必须在调用前拦截）。
- 渐变、多色图标、`DrawingGroup`/`DrawingImage`：门禁文档限定输出为单一 `PathGeometry` 字符串，不承载 Brush，遇到渐变引用直接报错。
- `.ico` 合成、PNG 降级导出：这些属于 `mastergo-icon-expoter` 的编排职责，本 Skill 只负责 SVG → PathGeometry 的单点转换。

## 架构

```
svg-to-wpf-xaml-path/
├── SKILL.md                              # 触发条件、门禁检查步骤、调用方式、输出纪律
├── CHANGELOG.md
├── scripts/
│   ├── svg_to_wpf_geometry.py            # 核心转换脚本
│   └── test_svg_to_wpf_geometry.py       # unittest
├── assets/
│   ├── sample-icon.svg                   # 已有：2 个同 fill path，覆盖 Combine 场景
│   ├── sample-icon-pause.svg             # 已有：1 个 path，覆盖单 path 场景
│   ├── sample-icon-continue.svg          # 已有：1 个 path
│   └── sample-icon-mixed-fill.svg        # 新增：2 个不同 fill path，覆盖门禁情形 3
└── references/
    ├── Sample-Icons.xaml                 # 已有：输出格式参考
    └── messages.md                       # 全部告警/错误原文清单
```

### 职责边界

本 Skill 只做「SVG → `PathGeometry` 字符串 + 写入/合并 Icons.xaml」的单点转换，不做图标发现、不做设计稿拉取。Python 侧只负责红线检查（transform/渐变/fill 比对）、命名与落盘；几何计算全部委托给 Inkscape CLI，不在 Python 中重复实现几何公式。`mastergo-icon-expoter` 未来若需要 Inkscape Combine 语义，应委派本 Skill，而不是重复实现调用逻辑。

### Python 脚本

`scripts/svg_to_wpf_geometry.py` 使用 Python 标准库 `xml.etree.ElementTree`、`argparse`、`subprocess`（调用 Inkscape CLI）：

```powershell
# 门禁检查失败时的行为一致：exit 非 0，stderr 报错原文，stdout 为空

# 内联 SVG 代码，未指定输出路径 —— 只输出到对话
python scripts/svg_to_wpf_geometry.py --svg '<svg ...>...</svg>' --key IconSampleGeometry

# 单文件路径，指定输出（若 Icons.xaml 已存在则合并）
python scripts/svg_to_wpf_geometry.py --file icon.svg --out Icons.xaml

# 文件夹路径，批量处理
python scripts/svg_to_wpf_geometry.py --folder .\icons\ --out Icons.xaml
```

`--file`、`--folder`、`--svg` 三者互斥且必须提供其一。`--out` 可选；提供时必须是有效路径（父目录存在或可创建）。`--folder` 必须搭配 `--out`。

### 转换流程

1. **门禁检查**（顺序执行，任一失败立即 exit 非 0）：
   - `shutil.which("inkscape")` 判断 CLI 可用；
   - 输入有效（`--file`/`--folder` 路径存在，`--svg` 内容可解析为合法 XML）；
   - `--out` 若提供，其父目录存在或可创建；`--folder` 若提供必须同时提供 `--out`。
2. 解析 SVG，收集 `<path>` 与基本图元（`rect`/`circle`/`ellipse`/`line`/`polyline`/`polygon`）作为候选元素，排除 `<defs>`/`<clipPath>`/`<mask>`/`<symbol>`/`<marker>`/`<pattern>` 子树内的元素（这些容器本身不直接渲染，不应参与转换/计数判定）。
3. **红线检查**（在几何处理与数量分支**之前**，对全部候选元素完成）：
   - 任意候选元素或其任意祖先带 `transform`：exit 非 0，报错提示先在源 SVG 中展平（第 2 节实测已证实 Inkscape 不会自动展平）。
   - 任意候选元素自身 `fill` 值匹配 `url(#...)`：exit 非 0，报错说明 `PathGeometry` 字符串无法承载 Brush。
   - 文档内含 `<style>` 元素：告警提示核实真实颜色（fill 比对仍只看 presentation attribute），不阻断。
4. 按候选元素数量分支：
   - 0 个：报错「无可转换几何」。
   - 1 个：若是 `<path>` 直接取 `d`；若是基本图元，用 Inkscape 跑一次 `select-all;object-to-path;export-filename:...;export-do` 取得转换后的 `d`。判定 `fill-rule`（**只读该元素自身属性，不向上继承**，默认 nonzero → `F1`，evenodd → `F0`）。
   - ≥2 个：比对各候选元素的 `fill` presentation attribute（**只读自身属性，不含 style/继承/CSS class**）。
     - 全同：整份 SVG 交给 Inkscape 执行：
       ```
       inkscape --actions="select-all;object-to-path;path-combine;export-filename:<tmp_out>.svg;export-do" <tmp_in>.svg
       ```
       从导出结果中提取合并后的单一 `<path>` 的 `d`；若合并前各元素的 `fill-rule` 不同，告警并按首个元素的规则定前缀。
     - 不同：单文件场景 exit 非 0 并提示"请自行处理"；文件夹批量场景跳过该文件、记录到跳过清单、继续处理下一个文件。
5. 拼接前把最终 `d` 的首字符规范化为大写 `M`（Inkscape 导出的合并路径可能以小写 `m` 开头，若直接拼接会被当作相对于前一路径当前点的相对移动，导致位置错位——这是旧 `svg-to-xaml-path` skill 已验证过的修正点）。
6. 生成 `x:Key`：文件名去扩展名，按 `-`/`_` 分词转 PascalCase，追加 `Geometry` 后缀（如 `icon-search.svg` → `IconSearchGeometry`）。内联 SVG 代码场景无文件名，`--key` 参数必填，缺省时报错要求用户提供；显式提供时原样使用，不自动追加后缀。
7. 落盘：
   - 未提供 `--out`：仅将 `<PathGeometry x:Key="...">...</PathGeometry>` 片段写 stdout。
   - 提供 `--out` 且文件不存在：新建 `ResourceDictionary` 并写入。
   - 提供 `--out` 且文件已存在：用文本拼接方式（在 `</ResourceDictionary>` 前插入新行）追加，不改变文件其余部分。解析现有 `x:Key` 集合，若新 key 已存在：exit 非 0，报错，不覆盖、不改名；无冲突则正常写入。

## 输出示例

单 path（`sample-icon-pause.svg`）：

```xml
<PathGeometry x:Key="SampleIconPauseGeometry">F1 M512,0C230.4,0 0,230.4 0,512s230.4,512 512,512...</PathGeometry>
```

多 path 同 fill（`sample-icon.svg`，Inkscape Combine 后）：

```xml
<PathGeometry x:Key="SampleIconGeometry">F1 M3,3H21V21H3V3zM5,5V19H19V5H5z M7,11H17V13H7V11z</PathGeometry>
```

## 错误处理

| 情况 | 脚本行为 |
|---|---|
| Inkscape 不在 PATH | stderr 报错，exit 非 0，不降级为字符串拼接 |
| 输入路径/文件夹/SVG 代码无效 | stderr 报错，exit 非 0 |
| `--out` 路径无效 | stderr 报错，exit 非 0 |
| `--folder` 未搭配 `--out` | stderr 报错，exit 非 0 |
| 无 `<path>`/基本图元（单文件） | stderr 报错「无可转换几何」，exit 非 0 |
| 多个候选元素且 fill 不同（单文件） | stderr 报错提示自行处理，exit 非 0 |
| 单文件级错误发生在文件夹批量场景（fill 不同、无可转换几何、含 transform、含渐变引用、单文件 XML 无法解析、Inkscape 调用失败） | 跳过该文件，继续其余；结束时汇总每个跳过文件及其原因，exit 0。**文件夹整体不存在/不可读，或文件夹内没有任何 `*.svg` 文件**仍属批量前置的门禁检查失败，exit 非 0 |
| 含 `transform`（单文件） | stderr 报错提示先展平，exit 非 0 |
| 含渐变引用（单文件） | stderr 报错「PathGeometry 无法承载 Brush」，exit 非 0 |
| 含 `<style>` 元素 | stderr 告警提示核实真实颜色，不阻断（文件夹批量下不跳过，仅告警） |
| fill-rule 混用（合并场景） | stderr 告警，按首个元素定前缀 |
| Inkscape 调用失败（合并或单元素 object-to-path） | stderr 报错，透传 Inkscape 的 stderr 原文，exit 非 0 |
| Icons.xaml 中 key 冲突 | stderr 报错，exit 非 0，不覆盖、不改名 |
| 内联 SVG 代码但缺 `--key` | stderr 报错要求提供，exit 非 0 |

stdout 只放产物（`PathGeometry` 片段或写入确认文本），stderr 放告警与错误，两者不得混淆。

## 测试与验证

`scripts/test_svg_to_wpf_geometry.py` 覆盖：

1. 单 path 提取 `d`，`F1`/`F0` 前缀正确（fill-rule 不继承，只读自身属性）。
2. 单个基本图元：mock Inkscape `object-to-path` 调用，验证提取转换后的 `d`。
3. 多个候选元素同 fill：mock Inkscape Combine 调用，验证提取合并后的 `d`，验证首字符大写修正。
4. 多个候选元素不同 fill：单文件报错；文件夹批量跳过并汇总，且不调用 Inkscape Combine（在调用前就应报错/跳过）。
5. 无 path/基本图元时报错。
6. 含 `transform`（元素自身或祖先）时报错，不调用 Inkscape。
7. 含渐变引用（元素自身 fill 匹配 `url(#...)`）时报错。
8. `<defs>` 等容器子树内的元素不计入候选转换范围。
9. `x:Key` 命名规则：文件名按 `-`/`_` 分词转 PascalCase + Geometry 后缀；`--key` 显式提供时原样使用。
10. `--out` 合并已有 Icons.xaml：新增 key 成功；key 冲突报错，不改名。
11. 未提供 `--out` 时只输出 stdout 片段，不建文件。
12. `--folder` 未搭配 `--out` 时报错；文件夹内无 `*.svg` 文件时报错。
13. Inkscape 不可用时报错退出（mock `shutil.which` 返回 None）。

执行：

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/svg-to-wpf-xaml-path/scripts/test_svg_to_wpf_geometry.py -v
```

## 后续步骤

- 补充 `assets/sample-icon-mixed-fill.svg`（2 个不同 fill path）用于测试门禁情形 3。
- `references/messages.md` 沿用旧 skill 纪律，列出全部告警/错误原文，供 Skill 编排层转述时照抄。
- 新增 Skill 需在 `.claude-plugin/marketplace.json` 做 Minor 版本升级（`plugins/` 下新增 skill）。
