# 告警与错误原文

脚本的全部 stderr 输出。**转述给用户时必须完整，不得截断结尾的处置建议**——那部分正是用户需要的行动指引。

`<>` 内为按内容替换的占位；实际输出为逗号分隔、按字母排序（如 `opacity, stroke-width`、`<image>, <text>`）。

## 告警（exit 0，stdout 仍有产物）

```
warning: class attributes were encountered; CSS classes were not converted.
warning: multiple fill/stroke/fill-rule/transform combinations found; emitting separate Path elements.
warning: multiple fill rules found; data output uses the first path's rule.
warning: unconverted style declarations were ignored: <属性名>.
warning: these elements have no exact path equivalent and were skipped: <元素名>; convert them to paths in the source SVG if they are needed.
```

## 错误（exit 2，stdout 为空）

paint 值无法解析时，三种情形给出**不同**的建议句：

```
error: fill value 'currentColor' is not a WPF colour; bind the WPF brush explicitly or replace it with a concrete colour
error: fill value 'url(#g)' is not a WPF colour; flatten the gradient or pattern to a solid colour in the source SVG
error: fill value 'hsl(210,40%,80%)' is not a WPF colour; use a hex colour such as #B8C6E0, or a colour keyword
error: fill value 'rebeccapurple' is not a WPF colour; use a hex colour such as #B8C6E0, or a colour keyword
```

关键字按 CSS3 的 148 色白名单校验——`rebeccapurple` 等不在表内的一律 exit 2，不会透传。

`stroke` 出错时把 `fill value` 换成 `stroke value`。通道超范围时另有：

```
error: paint value 'rgb(300, 0, 0)' has an out-of-range channel '300'
error: paint value '<值>' has an unreadable channel '<通道>'
error: paint value '<值>' has an out-of-range alpha '<值>'
error: paint value '<值>' has an unreadable alpha '<值>'
```

其余错误：

```
error: <N> of <M> paths carry an SVG transform, which path data alone cannot express; use --format xaml to emit a MatrixTransform, or flatten the transform in the source SVG
error: <标签> has an unsupported <属性> of '<值>'; percentages need a viewport, which is not converted; use user units
error: <标签> has an unsupported <属性> of '<值>'; use a plain number in user units
error: <标签> has unreadable points '<值>'
error: transform '<值>' uses <函数>() with <N> argument(s), which is not a valid SVG transform; fix or flatten the transform in the source SVG
error: transform '<值>' could not be parsed
error: transform '<值>' has an unreadable argument in <函数>(<参数>)
error: SVG declares an internal DTD subset, whose entities are not expanded; remove the [...] block from the DOCTYPE and convert again
error: No convertible geometry found; expected <path> with a nonempty d, or a <rect>/<circle>/<ellipse>/<line>/<polyline>/<polygon>
error: invalid XML: <解析器原文>
error: could not read input file: <系统原文>
error: could not read standard input: <系统原文>
```

argparse 自身的用法错误（如三个输入参数一个都没给）也走 exit 2，格式为 `merge_svg_paths.py: error: <argparse 原文>`。

## 没有告警的静默行为

以下情形**既不告警也不报错**，必须靠转换前检查源 SVG 发现。前三项会产出**错误的产物**：

| 情形 | 后果 | 严重度 |
|---|---|---|
| 同色路径重叠后被合并 | 重叠区可能翻转为孔洞（详见 silent-traps.md），用 `--no-merge` 规避 | **像素错误** |
| `<style>` 元素或外链 CSS 上色 | 无 `fill` 时输出 `#000000`；有 `fill` 时输出该属性值，但 CSS 在层叠中优先级更高，两种情况的颜色都是错的 | **颜色错误** |
| `<switch>` | 所有分支都被转换，而 SVG 只渲染首个测试通过的分支（分支异色时会有多样式告警） | **多余图形** |
| 嵌套 `<svg>` 的 `x`/`y`/`viewBox` | 内层视口的平移缩放不转换，子图形位置错 | **位置错误** |
| `--format data` 遇异色多路径 | 颜色被丢弃，几何被熔为一条 | 颜色丢失 |
| `fill-opacity` / `opacity` 作为 presentation attribute | 不在合并键内，半透明形状会被合并成实心（`--no-merge` 可规避合并，但透明度本身仍不转换） | 透明度丢失 |
| `viewBox`/`width`/`height` | 尺寸信息丢失，产物无固有尺寸 | 尺寸丢失 |
| stroke width、clip/mask/filter 作为 presentation attribute | 属性丢失 | 样式丢失 |
| 坐标保留 6 位小数 | `12.3456789` → `12.345679`，有界且视觉无影响 | 可忽略 |
| 未被引用的 `<defs>` 渐变 | 随 `<defs>` 跳过 | 无害 |
