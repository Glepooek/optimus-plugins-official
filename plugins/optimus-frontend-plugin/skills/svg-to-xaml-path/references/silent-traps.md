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

翻转条件：

| fill rule | 何时翻转 |
|---|---|
| `F0`（evenodd） | 只要重叠，**必定**翻转 |
| `F1`（nonzero） | 两 figure 绕行方向**相反**时翻转；同向则不翻转 |

`F1` 的条件看似宽松，但 Figma / Illustrator 导出的图标经常混用绕行方向（尤其是「实心形状 + 挖孔」这种设计意图本身就依赖反向绕行）。

**应对**：交付前核对源 SVG 中同色路径是否有重叠。有重叠且无法确认绕行方向时，输出多个 `Path`——各自独立填充，与源一致。

另注意 `fill-opacity` / `opacity` **不在合并键内**：一个 15% 的虚影与一个不透明形状同色时会被合并，虚影变实心。

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
