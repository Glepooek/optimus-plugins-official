# 三个静默陷阱

这些情形 exit 0、零告警、生成的 XAML 完全合法，但产物与源 SVG 不符。脚本无法自动检测它们——判据只能来自**转换前打开源 SVG 检查**。

判据与禁令见 SKILL.md 的速查表；此处是机理与复现。

## 陷阱一：合并键只保证颜色能共存，不保证几何能共存

合并键（`Fill`+`Stroke`+`fill-rule`+`transform` 全同）回答的是「颜色能否共存」。它不回答「几何能否共存」——而后者取决于路径是否重叠、绕行方向是否一致，这两点脚本都不检查。

串接后的 `Data` 是一个含多个 figure 的**单一** Geometry，各 figure 按 fill rule **共同**决定填充，**不是布尔并集**。源 SVG 里两个独立的 `<path>` 各自填充、相叠处叠加；合并后它们变成同一 Geometry 的两个 figure，相叠处按 fill rule 重新判定。

```bash
python scripts/merge_svg_paths.py --svg '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 H12 V12 H0 Z" fill-rule="evenodd"/><path d="M6 6 H20 V20 H6 Z" fill-rule="evenodd"/></svg>' --format xaml
```
```
<Path Fill="#000000" Data="F0 M0 0 H12 V12 H0 Z M6 6 H20 V20 H6 Z" />
```
exit 0，零 stderr。源 SVG 中两个方块的重叠区 (6,6)-(12,12) 是**实心**；合并后 `F0` 下该区域穿越两条边界，计数为偶，变成**孔洞**。

翻转条件按**覆盖计数**判定，不是「只要重叠就翻转」：

| fill rule | 判据 |
|---|---|
| `F0`（evenodd） | 覆盖数为**偶数**的区域变孔洞。两图形相叠→翻转；三个图形共同覆盖的区域仍是实心 |
| `F1`（nonzero） | 绕行数为 0 才是孔洞。两图形绕行**相反**时相叠处翻转；同向则不翻转 |

所以「重叠必翻转」并不准确——真正的判据是上表。但对最常见的两图形相叠，`F0` 下确实必定翻转。`F1` 的条件看似宽松，但 Figma / Illustrator 导出的图标经常混用绕行方向（「实心形状 + 挖孔」这种设计意图本身就依赖反向绕行）。

另有一种不翻转的情形：源 SVG 里第二条路径恰好**填补**第一条的孔洞（如 `M0 0 H20 V20 H0 Z M5 5 H15 V15 H5 Z` 加一个 `M5 5 H15 V15 H5 Z`），此时合并前后栅格完全一致。

**应对**：交付前核对源 SVG 中同色路径是否有重叠。有重叠且无法确认覆盖关系时，用 `--no-merge` 重跑——每条路径输出独立的 `Path`，各自填充，与源一致。**不要手工拆分已合并的 `Data` 字符串**。

```bash
python scripts/merge_svg_paths.py --file icon.svg --format xaml --no-merge
```

另注意 `fill-opacity` / `opacity` **不在合并键内**：一个 15% 的虚影与一个不透明形状同色时会被合并，虚影变实心。`--no-merge` 能阻止合并，但透明度本身仍不转换，须自行在 WPF 侧设 `Opacity`。

```bash
python scripts/merge_svg_paths.py --svg '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0h10v10H0z" fill="#B8C6E0"/><path d="M20 0h10v10H20z" fill="#B8C6E0" fill-opacity="0.15"/></svg>' --format xaml
```
```
<Path Fill="#B8C6E0" Data="F1 M0 0h10v10H0z M20 0h10v10H20z" />
```

## 陷阱二：`data` 格式不适用合并键

`data` 只输出几何，颜色无处安放。异色路径不会被拆分，而是被拼成一条字符串：

```bash
python scripts/merge_svg_paths.py --svg '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 0 Z" fill="#B8C6E0"/><path d="M2 0 L3 0 Z" fill="#FF0000"/></svg>' --format data
```
```
F1 M0 0 L1 0 Z M2 0 L3 0 Z
```
exit 0，零 stderr，`#FF0000` 凭空消失。

危险之处在于它**恰好满足**「合并成一个 Path」的字面要求：用户这么说时，`data` 是看起来最直接的解法。

**应对**：颜色不同时不得用 `data` 迂回。说明无法合并，输出多个 `Path`。仅在确认全部同色（或用户明确只要几何、颜色另行设置）时才用 `data`。

## 陷阱三：CSS 上色一律不生效

脚本只认两种着色方式，其余都拿不到 CSS 里的值：

| 着色方式 | 脚本行为 |
|---|---|
| `fill="#B8C6E0"`（presentation attribute） | 正常转换 |
| `style="fill:#B8C6E0"`（内联 style 属性） | 正常转换 |
| `<style>.icon{…}</style>` + `class="icon"` | 拿不到，**但有 class 告警** |
| `<style>path{…}</style>`（标签选择器） | 拿不到，**零告警** |
| 外部样式表 | 拿不到，**零告警** |

标签选择器不需要 `class` 属性，所以连 class 告警都不触发。

**判据是「源文件有没有 CSS」，不是「输出是不是黑色」**，因为有两种后果：

```bash
# 情况 A：<path> 无 fill → 落到 SVG 默认值
--svg '<svg …><style>path{fill:#4A90D9}</style><path d="M12 2L2 22h20z"/></svg>'
→ <Path Fill="#000000" …/>        实际应为 #4A90D9
```
```bash
# 情况 B：<path> 有 fill → 输出该属性值，但 CSS 优先级更高
--svg '<svg …><style>path{fill:#B8C6E0}</style><path d="M0 0 Z" fill="#FF0000"/></svg>'
→ <Path Fill="#FF0000" …/>        浏览器渲染的是 #B8C6E0
```

情况 B 输出非黑，看不出任何异常，只以「输出是否为黑」为判据的检查会完全漏掉它。CSS 层叠中作者样式表的优先级高于 presentation attribute，所以源 SVG 的真实渲染色是 CSS 里那个。

**应对**：转换前检查源文件是否含 `<style>` 元素或外链 CSS。存在即须向用户确认实际颜色，无论输出是什么颜色。iconfont、Illustrator、Figma 的部分导出配置都会产生这种 SVG。

## 附：为什么 `Data` 里的首个 `m` 会变成 `M`

这不是陷阱，是一处**已修复**的行为，记在此处以免被误认为改动了几何。

SVG 规范规定：一个 `d` 属性的**首个** moveto 无论写作 `m` 还是 `M` 都按绝对坐标处理。但串接之后，后续路径的首个 `m` 不再是「首个」——它变成了相对于前一子路径当前点的位移。

```
路径 1: M100 100 H104 V104 H100 Z     单独存在时终点回到 (100,100)
路径 2: m10 10 h2 v2 h-2 z            单独存在时方块在 (10,10)
朴素串接后 m10 10 解析为 100+10, 100+10 = (110,110)  ← 错位 100 单位
```

SVGO、Bootstrap Icons、Material Icons 压缩输出时，第一条之后的路径**都**以小写 `m` 开头，所以这曾是最常见输入上的静默错位。现在串接前会把这个首字母规范化为 `M`，坐标不变；路径**中间**的 `m` 保持原样（那里它本就是相对的）。
