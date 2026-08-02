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
```

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
```

## 没有告警的静默行为

以下情形**既不告警也不报错**，必须靠转换前检查源 SVG 发现（详见 SKILL.md 的两个静默陷阱）：

| 情形 | 后果 |
|---|---|
| `<style>` 标签选择器或外部 CSS 上色 | `Fill="#000000"`，颜色错误 |
| `--format data` 遇异色多路径 | 颜色被丢弃，几何被熔为一条 |
| `viewBox`/`width`/`height` | 尺寸信息丢失 |
| stroke width、opacity、clip/mask/filter 写作 presentation attribute | 属性丢失 |
| 未被引用的 `<defs>` 渐变 | 随 `<defs>` 跳过（此项无害） |
