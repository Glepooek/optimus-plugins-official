# Changelog

## [1.4.0] - 2026-08-02

对抗性验收（独立 agent，45 次工具调用）在文档四轮优化后转而攻击脚本，
找到 3 个会产出错误结果的实现缺陷。本次修脚本，不只是记录限制。

### Fixed
- **串接会重新锚定相对 moveto**。SVG 规定 `d` 的首个 moveto 无论大小写都按绝对处理，但串接后，后续路径的首个 `m` 变成相对于前一子路径当前点的位移——`M100 100…Z` + `m10 10…` 会把第二个图形从 (10,10) 挪到 (110,110)，exit 0 零告警。SVGO / Bootstrap Icons / Material Icons 压缩输出时第一条之后的路径**都**以小写 `m` 开头，这是最常见输入上的静默错位。串接前规范化首字母为 `M`，路径中间的 `m` 保持不变。
- **颜色白名单含 7 个 WPF 不支持的拼写**。用的是 CSS3 的 148 色表，而 WPF 只有 141 色且无 `grey` 变体：`grey`/`darkgrey`/`dimgrey`/`lightgrey`/`slategrey`/`lightslategrey`/`darkslategrey` 会原样透传，在 XAML 加载时才失败——正是这个白名单本该拦住的情形。改为映射到对应的 `gray` 拼写。
- **字面 4/8 位 hex 的通道序与 WPF 相反**。CSS/SVG 写 `#RGBA`/`#RRGGBBAA`，WPF 读 `#ARGB`/`#AARRGGBB`。`#F00A`（红，67% 不透明）被原样输出后在 WPF 中解析为蓝色。改为按 CSS 语义解析后重排。3/6 位无 alpha，两边一致，不受影响。

### Added
- 新增 `--no-merge`：每条路径单独输出一个 `Path`，即使绘制样式相同。此前文档要求「重叠时输出多个 Path」，但 CLI 无此开关，助手只能手工拆分 `Data` 字符串——那既违反「不发明几何」的纪律，拆出来的坐标还带着上述 moveto 缺陷。
- 新增 10 条测试（共 74 条），覆盖 moveto 规范化、hex 通道序、grey 拼写与 `--no-merge`。

### Changed
- 修正 `silent-traps.md` 中「`F0` 下重叠必定翻转」的断言：真正的判据是覆盖计数的奇偶（三图形共同覆盖区仍为实心），且存在「第二条路径恰好填补第一条的孔洞」这种合并前后完全一致的情形。`F1` 的绕行方向判据经数值验证无误。
- 修正陷阱编号的交叉引用错误（CSS 上色是陷阱三，文档误指陷阱二）。
- 修正 `<switch>` 的「零告警」表述：仅分支同色时无告警，异色时会触发多样式告警。

## [1.3.0] - 2026-08-02

经 darwin-skill 三轮优化（`full_test` 实测，独立子 agent 评分），基线
68.3 → 79.3。三处会导致「照做的助手交出错误答案」的缺陷已修复。

### Added
- 新增 `references/messages.md`：全部 5 条告警、20 条错误的逐字原文，以及「既不告警也不报错」的静默行为清单。此前错误原文一条未记载，而文档要求「如实转达」。
- 新增「🔴 静默陷阱二」：颜色由 `<style>` 元素或外部 CSS 提供时，脚本输出 `Fill="#000000"`、exit 0 且零告警。标签选择器（`<style>path{…}</style>`）连 class 告警都不触发。附着色方式对照表与输出纪律第 5 条强制回查。
- 新增「交付给 WPF 时的三个约束」：产物无固有尺寸、`RenderTransform` 不参与布局测量（含 `LayoutTransform` 对纯平移无效的推论）、多 `Path` 是无根元素的裸序列。
- 新增 stdout/stderr 分流说明与 `2>$null` 配方——此前未记载，告警行可能被贴进 `.xaml`。

### Fixed
- 修复合并键被写成全局规则：实际只对 `xaml` 成立，`data` 格式会把异色路径静默熔为一条（exit 0、零告警）。助手为满足「合并成一个」而改用 `data` 时会丢色。
- 修复「告警原文，须如实转述」章节自身改写了两条原文：`skipped` 告警丢了结尾的处置建议从句，`unconverted style` 告警少了句号。
- 修复渐变描述的方向性错误：被 `fill`/`stroke` 引用的渐变是 exit 2 硬失败，只有未被引用的 `<defs>` 渐变才静默跳过；原文两处均写作「不转换，无告警」。
- 修复 `$SkillDir` 的理由「相对路径会直接 FileNotFoundError」不实（cwd 恰在 skill 目录时可用）；规则本身正确，换为真实理由。
- 补记 `--format` 缺省值为 `xaml`、`data` 格式丢弃 `Fill`/`Stroke`、颜色关键字不做校验、`data` 遇混合 fill-rule 的告警与首条优先规则。

### Changed
- 三种 paint 错误的建议句不同（绑定画刷 / 展平渐变 / 改用 hex），错误表由一行拆为三行。
- 删除三处重复表述（对照表与「支持边界」、错误表的 CSS/渐变/视觉保真各重复 2-3 次），信息无删减。

## [1.2.0] - 2026-08-02

### Added
- 新增基本图元转换：`rect`（含 `rx`/`ry` 圆角与超限钳制）、`circle`、`ellipse`、`line`、`polyline`、`polygon` 按 SVG 2 规范的等价路径精确转换，无任何近似。
- 新增 `transform` 转换：`translate`/`scale`/`rotate`（含旋转中心）/`skewX`/`skewY`/`matrix` 及函数列表合成为单一仿射矩阵，输出 WPF `MatrixTransform`；坐标不被烘焙。
- 新增 paint 值校验：hex 与颜色关键字放行，`rgb()`/`rgba()` 换算为 WPF hex，`currentColor`/`url(#…)`/`hsl()` 硬报错并给出预处理建议。
- 新增 `text`/`tspan`/`textPath`/`image`/`use`/`foreignObject` 的具名跳过告警，替代此前的静默丢弃。
- 新增内部 DTD 子集拦截，零依赖防范实体展开攻击。
- 新增 SKILL.md 的「错误与告警」表，逐条说明 exit 2 的成因与处理方式。
- 新增 30 条 CLI 契约测试（共 64 条），覆盖图元几何、矩阵合成顺序、paint 校验与编码。

### Changed
- `transform` 由硬停止改为转换：合并键扩展为 `Fill` + `Stroke` + `fill-rule` + `transform` 四项。
- `--format data` 遇到 transform 时报错——路径数据无法承载变换，提示改用 `xaml` 或先展平。
- 无可转换几何时的错误信息列出全部受支持的图元，不再只提 `<path>`。

### Fixed
- 修复 stdin 走 locale 编码：显式 `utf-8-sig`，与 `--file` 对齐；此前中文环境下经 PowerShell 管道传入含非 ASCII 的 SVG 会乱码。

## [1.1.0] - 2026-08-02

### Added
- 新增解析 `style` 内联声明的能力：`fill`/`stroke`/`fill-rule`/`display`/`visibility`/`transform` 六个属性按 CSS 优先级覆盖同名 presentation attribute。
- 新增 `Data` 的 fill rule 前缀（`F1` nonzero / `F0` evenodd），对齐 SVG 的 nonzero 默认值与 WPF 迷你语言的 EvenOdd 默认值差异。
- 新增 `assets/sample-icon.svg` 示例文件，替代原先指向个人下载目录的示例路径。
- 新增「已转换 / 未转换」对照表，并明确点名 `currentColor`、`url(#gradient)`、`rgb()` 等 WPF 无法解析的 paint 值。
- 新增 14 条 CLI 契约测试，覆盖非渲染子树、隐藏元素、`style` 解析与 fill rule。

### Changed
- 脚本调用路径改为基于本 skill 的 base directory；原先的仓库相对路径在插件缓存加载时会失败。
- fill-rule 纳入 `xaml` 的合并判据：`Fill`/`Stroke`/`fill-rule` 三者全同才合并为一个 `Path`。
- 拆分原先的 `style or class` 合并警告：`class` 单独告警，`style` 中未识别的声明按名称告警。

### Fixed
- 修复 `<defs>`/`<clipPath>`/`<mask>`/`<symbol>`/`<marker>`/`<pattern>` 内的路径被当作可见图形串入几何的问题。
- 修复 `display:none` 子树与 `visibility:hidden` 路径被输出的问题。
- 修复填充写在 `style` 中时静默退化为 `#000000` 的问题。
- 移除违反开放 Agent Skills 规范六字段限制的顶层 `version` 字段。

## [1.0.0] - 2026-07-30

### Added
- 新增 SVG 转 WPF XAML Path Skill。
- 新增无需第三方依赖、兼容 Python 3 的命令行工具说明。
- 新增 `data` 和 `xaml` 输出格式说明。
- 新增转换警告与错误诊断说明。
