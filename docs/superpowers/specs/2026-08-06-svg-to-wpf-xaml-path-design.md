# SVG to WPF XAML Path Skill 设计

**日期：** 2026-08-06\
**Skill 目录：** `plugins/optimus-frontend-plugin/skills/svg-to-wpf-xaml-path/`\
**调用名：** `/optimus-frontend-plugin:svg-to-wpf-xaml-path`

## 目标

按用户提供的门禁文档（`svg-to-wpf-xaml-path/门禁.md` 的初步要求）实现：输入 SVG（文件代码 / 单文件路径 / 文件夹路径），提取或合并 `<path>` 的几何数据，输出为 WPF `PathGeometry` 资源，追加或新建到目标 `Icons.xaml`。

与已删除的 `svg-to-xaml-path`（输出 `Path.Data`/`Path` 元素，多 path 靠字符串拼接、不依赖 Inkscape）不同，本 Skill：
- 输出格式固定为 `<PathGeometry x:Key="...">` 资源条目，与仓库现有 `references/Sample-Icons.xaml` 的写法对齐；
- 多 path 同 fill 时依赖 **Inkscape CLI 的 Combine 语义**（结构拼接，不重算几何），而不是自行拼接字符串或做布尔运算；
- 面向"批量产出图标资源字典"场景，支持文件夹批量与 Icons.xaml 合并写入。

## 范围

### 包含

- 三种输入：内联 SVG 代码、单个 SVG 文件路径、含多个 SVG 的文件夹路径。
- 门禁检查：Inkscape CLI 在 PATH 中可执行、输入路径有效、输出路径有效——任一不满足直接报错停止，不降级、不猜测。
- `<path>` 与基本图元（`rect`/`circle`/`ellipse`/`line`/`polyline`/`polygon`）等价转换为 path `d` 数据后统一处理。
- 单 path：直接提取 `d`，按 `fill-rule` 加 `F0`/`F1` 前缀。
- 多 path 且 `fill` presentation attribute 全同：调用 Inkscape 1.x `--actions` 系列命令执行 `path-combine`（结构拼接，非布尔 Union），取合并后的 `d`。
- 多 path 且 `fill` 不同：单文件场景报错提示用户自行处理；文件夹批量场景跳过该文件，继续处理其余文件，最终汇总列出跳过清单。
- `x:Key` 命名：文件名（kebab-case/snake_case）转 PascalCase + `Geometry` 后缀；无文件名（内联 SVG 代码）时要求用户显式提供 key 名。
- 输出落盘：指定输出路径且目标 `Icons.xaml` 已存在时，解析已有 `x:Key` 并合并追加，key 冲突报错不覆盖；未指定输出路径时只在对话中给出 `PathGeometry` 片段，不自动建文件。

### 不包含

- CSS 完整级联处理：仅比对 `fill` 的 presentation attribute 本身，不解析 `style=""`、父级继承、CSS class、`<style>` 元素（含 `<style>` 时告警提示用户核实真实颜色，但不阻断转换）。
- `transform`：path 或其任意父级元素带 `transform` 直接报错，要求先在源 SVG 中展平——`PathGeometry` 字符串无法携带矩阵信息，与门禁文档限定的输出格式互斥。
- 布尔几何运算（Union/Difference/Intersect）：多 path 不同 fill 时不允许用几何布尔或降级为单色来强行合并。
- 渐变、多色图标、`DrawingGroup`/`DrawingImage`：门禁文档限定输出为单一 `PathGeometry` 字符串，不承载 Brush，遇到渐变引用直接报错（与旧 skill 一致的红线）。
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

本 Skill 只做「SVG → `PathGeometry` 字符串 + 写入/合并 Icons.xaml」的单点转换，不做图标发现、不做设计稿拉取。`mastergo-icon-expoter` 未来若需要 Inkscape Combine 语义（结构拼接而非布尔并集），应委派本 Skill，而不是重复实现字符串拼接逻辑。

### Python 脚本

`scripts/svg_to_wpf_geometry.py` 使用 Python 标准库 `xml.etree.ElementTree`、`argparse`、`subprocess`（调用 Inkscape CLI）：

```powershell
# 门禁检查失败时的行为一致：exit 非 0，stderr 报错原文，stdout 为空

# 内联 SVG 代码，未指定输出路径 —— 只输出到对话
python scripts/svg_to_wpf_geometry.py --svg '<svg ...>...</svg>' --key IconSample

# 单文件路径，指定输出（若 Icons.xaml 已存在则合并）
python scripts/svg_to_wpf_geometry.py --file icon.svg --out Icons.xaml

# 文件夹路径，批量处理
python scripts/svg_to_wpf_geometry.py --folder .\icons\ --out Icons.xaml
```

`--file`、`--folder`、`--svg`、`--stdin` 四者互斥且必须提供其一。`--out` 可选；提供时必须是有效路径（父目录存在或可创建）。

### 转换流程

1. **门禁检查**（顺序执行，任一失败立即 exit 非 0）：
   - `shutil.which("inkscape")` 判断 CLI 可用；
   - 输入（`--file`/`--folder` 路径存在，`--svg` 内容可解析为合法 XML）；
   - `--out` 若提供，其父目录存在或可创建。
2. 解析 SVG，收集 `<path>` 与基本图元，基本图元按 SVG 2 等价公式转换为 path `d`（复用旧 skill 已验证的转换公式）。
3. 按 path 数量分支：
   - 0 个：报错「无可转换几何」。
   - 1 个：提取 `d`，判定 `fill-rule`（含继承，默认 nonzero → `F1`，`evenodd` → `F0`）。
   - ≥2 个：比对各 path 的 `fill` presentation attribute。
     - 全同：写临时 SVG，调用：
       ```
       inkscape --actions="select-all;path-combine;export-filename:<tmp_out>.svg;export-do" <tmp_in>.svg
       ```
       从导出结果中提取合并后的单一 `d`；若合并前各 path 的 `fill-rule` 不同，告警并按首条 path 的规则定前缀（与旧 skill 一致）。
     - 不同：单文件场景 exit 非 0 并提示"请自行处理"；文件夹批量场景跳过该文件、记录到跳过清单、继续处理下一个文件。
4. 遇 `transform`（path 或任意祖先）：exit 非 0，报错提示先展平源 SVG。
5. 遇 `<style>` 元素或外链样式表：告警提示用户核实真实颜色（fill 比对仍只看 presentation attribute），不阻断。
6. 遇渐变引用（`url(#...)`）：exit 非 0，报错说明 `PathGeometry` 字符串无法承载 Brush。
7. 生成 `x:Key`：文件名去扩展名，kebab-case/snake_case 转 PascalCase，追加 `Geometry` 后缀（如 `icon-search.svg` → `IconSearchGeometry`）。内联 SVG 代码场景无文件名，`--key` 参数必填，缺省时报错要求用户提供。
8. 落盘：
   - 未提供 `--out`：仅将 `<PathGeometry x:Key="...">...</PathGeometry>` 片段写 stdout。
   - 提供 `--out` 且文件不存在：新建 `ResourceDictionary` 并写入。
   - 提供 `--out` 且文件已存在：解析现有 `x:Key` 集合，新 key 追加进 `<ResourceDictionary>`；发现 key 冲突 exit 非 0，不静默覆盖。

## 输出示例

单 path（`sample-icon-pause.svg`）：

```xml
<PathGeometry x:Key="SampleIconPauseGeometry">F1 M512,0C230.4,0 0,230.4 0,512s230.4,512 512,512...</PathGeometry>
```

多 path 同 fill（`sample-icon.svg`，Combine 后）：

```xml
<PathGeometry x:Key="SampleIconGeometry">F1 M3,3H21V21H3V3zM5,5V19H19V5H5z M7,11H17V13H7V11z</PathGeometry>
```

## 错误处理

| 情况 | 脚本行为 |
|---|---|
| Inkscape 不在 PATH | stderr 报错，exit 非 0，不降级为字符串拼接 |
| 输入路径/文件夹/SVG 代码无效 | stderr 报错，exit 非 0 |
| `--out` 路径无效 | stderr 报错，exit 非 0 |
| 无 `<path>`/基本图元 | stderr 报错「无可转换几何」，exit 非 0 |
| 多 path 且 fill 不同（单文件） | stderr 报错提示自行处理，exit 非 0 |
| 多 path 且 fill 不同（文件夹批量） | 跳过该文件，继续其余；结束时汇总跳过清单，exit 0 |
| 含 `transform` | stderr 报错提示先展平，exit 非 0 |
| 含渐变引用 | stderr 报错「PathGeometry 无法承载 Brush」，exit 非 0 |
| 含 `<style>` 元素/外链 CSS | stderr 告警提示核实真实颜色，不阻断 |
| fill-rule 混用（合并场景） | stderr 告警，按首条 path 定前缀 |
| Icons.xaml 中 key 冲突 | stderr 报错，exit 非 0，不覆盖 |
| 内联 SVG 代码但缺 `--key` | stderr 报错要求提供，exit 非 0 |

stdout 只放产物（`PathGeometry` 片段或合并结果），stderr 放告警与错误，两者不得混淆。

## 测试与验证

`scripts/test_svg_to_wpf_geometry.py` 覆盖：

1. 单 path 提取 `d`，`F1`/`F0` 前缀正确。
2. 多 path 同 fill：mock Inkscape Combine 调用，验证提取合并后的 `d`。
3. 多 path 不同 fill：单文件报错；文件夹批量跳过并汇总。
4. 无 path/基本图元时报错。
5. 含 `transform` 时报错。
6. 含渐变引用时报错。
7. 基本图元（rect/circle 等）等价转换为 path 后正确处理。
8. `x:Key` 命名规则：文件名转 PascalCase + Geometry 后缀。
9. `--out` 合并已有 Icons.xaml：新增 key 成功；key 冲突报错。
10. 未提供 `--out` 时只输出 stdout 片段，不建文件。
11. Inkscape 不可用时报错退出（mock `shutil.which` 返回 None）。

执行：

```powershell
python -m unittest plugins/optimus-frontend-plugin/skills/svg-to-wpf-xaml-path/scripts/test_svg_to_wpf_geometry.py -v
```

## 后续步骤

- 补充 `assets/sample-icon-mixed-fill.svg`（2 个不同 fill path）用于测试门禁情形 3。
- `references/messages.md` 沿用旧 skill 纪律，列出全部告警/错误原文，供 Skill 编排层转述时照抄。
- 新增 Skill 需在 `.claude-plugin/marketplace.json` 做 Minor 版本升级（`plugins/` 下新增 skill）。
