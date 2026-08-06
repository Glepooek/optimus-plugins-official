# WPF XAML 图标与背景资源规格

本文件是 `mastergo-icon-expoter` 的目标格式规格：**WPF 侧接受什么、不接受什么、怎么命名、怎么接入工程**。

SVG → `Path.Data` 的转换机理、告警与静默陷阱不在本文件范围内，由 `optimus-frontend-plugin:svg-to-xaml-path` 独占定义；本文件只在决策点上引用它，不复述规则，避免两处规则漂移。

## 一、WPF 原生支持哪些图标承载形式

**WPF 至今（含 .NET 10）没有原生 SVG 支持。** `Image.Source` 不接受 `.svg`格式文件。凡"在 XAML 里直接用 svg"的方案都依赖第三方库（如SharpVectors）或商业控件库——引入运行时依赖属于项目级决策，**skill 不得代替用户选择**，默认走构建期转换路线。

WPF Imaging 内置的 codec 覆盖 BMP、JPEG、PNG、TIFF、Windows Media Photo（WMP）、GIF、ICON 七种格式。**关键限制：ICON 只能解码，不能编码**——其余六种都有对应的 `XxxBitmapEncoder`，ICO 没有。

| 承载形式 | XAML 类型 | 矢量 | 可换色 | 适用 |
|---|---|---|---|---|
| 路径几何 | `Path` + `Data`，或 `Geometry` 资源 | 是 | 是（`Fill` 可绑定/换资源） | 单色图标，绝大多数场景的首选 |
| 绘图图像 | `DrawingImage` 包 `GeometryDrawing`/`DrawingGroup`，作为 `Image.Source` | 是 | 否（颜色定死在 Drawing 里） | 多色矢量图标、插画 |
| 绘图画刷 | `DrawingBrush` | 是 | 否 | 矢量背景、可平铺纹理 |
| 位图 | `BitmapImage` 作 `Image.Source` | 否 | 否 | 照片、渐变/滤镜/阴影无法矢量化的图 |
| 位图画刷 | `ImageBrush` | 否 | 否 | 位图背景、水印 |
| 窗口图标 | `Window.Icon`（`ImageSource`） | 否 | 否 | **只有这里需要 `.ico`** |
| 图标字体 | `TextBlock.Text` + `FontFamily` | 是 | 是（`Foreground`） | 复用系统图标，见第六节的授权限制 |

WPF **没有** WinUI 的 `PathIcon`、`FontIcon`、`SvgImageSource`、`Image.NineGrid`。把 WinUI 示例直接搬进 WPF 会编译失败——生成代码时不要臆造这些类型。

## 二、导出格式决策

对每个图标节点按序判定，命中即停：

```
1. 该资源是「窗口/任务栏/程序图标」？          → .ico（唯一必须用 ico 的场景，见第五节）
2. DSL 是纯色矢量（单一 fill 或多 fill 颜色相同，无渐变/位图/滤镜）？ → Path.Data（+ Geometry 资源）
3. DSL 是多色矢量（多 fill 颜色不同 或含渐变，但全是矢量图元）？ → DrawingImage / DrawingGroup
4. 该资源用作背景且需平铺？               → DrawingBrush（矢量）/ ImageBrush（位图）
5. 含位图填充、滤镜、阴影或复杂渐变网格？   → .png（带 alpha）
6. 以上都不成立（无法判定）？             → 不猜测，列入待人工确认清单
```

**第 2 步与第 3 步的分界必须看 DSL，不能看渲染结果。** MasterGo DSL 中一个 icon 组件常含多个 `PATH` 子节点，各自有独立 `_color`；`svg-to-xaml-path` 的可将单一路径或多路径 fill 颜色相同的路径转为 `Path.Data`。

**不允许的迂回：** 多色图标不得为了凑成"一个 Path"而改用 `--format data`——那会静默丢弃所有颜色。这条禁令的完整机理见 `svg-to-xaml-path` 的静默陷阱二。

**png 是兜底而非等价替代。** 选 png 就放弃了任意缩放和主题换色；缩放到非整数倍会因重采样发虚（见第七节）。判定为 png 时必须在清单中记录判定依据（哪个字段导致无法矢量化），让用户有机会推翻。

## 三、Path 与 Geometry 的落地形态

单色图标有三种写法，按复用度由高到低：

```xml
<!-- A. Geometry 资源：几何复用，颜色由使用方决定（推荐默认形态） -->
<Geometry x:Key="IconSearchGeometry">F1 M3,3 H21 V21 H3 Z</Geometry>
<!-- 使用： -->
<Path Data="{StaticResource IconSearchGeometry}"
      Fill="{DynamicResource IconBrush}"
      Width="16"
      Height="16"
      Stretch="Uniform" />

<!-- B. 就地内联：一次性使用，位置固定 -->
<Path Data="F1 M3,3 H21 V21 H3 Z"
      Fill="{DynamicResource IconBrush}"
      Width="16"
      Height="16"
      Stretch="Uniform" />

<!-- C. DrawingImage 资源：整图复用，颜色烧死 -->
<DrawingImage x:Key="IconSearchImage">
  <DrawingImage.Drawing>
    <GeometryDrawing Brush="#4E5969" Geometry="F1 M3,3 H21 V21 H3 Z" />
  </DrawingImage.Drawing>
</DrawingImage>
<!-- 使用： -->
<Image Source="{StaticResource IconSearchImage}" Width="16" Height="16" />
```

`<Geometry x:Key="...">` 能直接写迷你语言字符串，靠 `GeometryConverter` 转换——这是形态 B 成立的原因。

**三条硬约束：**

- **`F0`/`F1` 前缀必须保留，但只对 `Path.Data`/`Geometry` 资源的紧凑字符串形式有效。** 无前缀时 WPF 按 EvenOdd 解析，而 SVG 默认 nonzero；删掉前缀会改变自相交路径和孔洞的渲染结果。这套带前缀的迷你语言是 `StreamGeometry` 语法（`Path.Data`、`<Geometry x:Key="...">` 用的就是它）；如果改写成更冗长的 `<PathGeometry><PathGeometry.Figures>...</PathGeometry.Figures></PathGeometry>` 形式，`Figures` 属性用的是另一套"非常相似但不相同"的 `PathFigureCollection` 迷你语言，**不支持 `F` 前缀**——生成这类冗长形式时改用 `PathGeometry.FillRule="Nonzero"` 属性显式指定，不要把前缀字符串硬塞进 `Figures`。
- **Path.Data 没有固有尺寸。** `viewBox` 不参与转换，坐标按源图原样保留（`viewBox="0 0 1024 1024"` 的图标就是 1024 单位跨度）。必须显式给 `Width`/`Height` + `Stretch="Uniform"`，或包一层 `Viewbox`。**不要替用户臆造尺寸**——尺寸应来自 DSL 的 `layoutStyle.width/height`。
- **`Stretch` 默认值是 `None`。** 不写 `Stretch` 时 `Width`/`Height` 只裁剪不缩放，1024 单位的图标塞进 16×16 只会显示左上角一小块，且**不报任何错**。这是最容易漏的一条。

## 四、多色矢量与背景

`DrawingGroup` 把多个 `GeometryDrawing` 组合成单个 `Drawing`，是多色图标的标准容器：

```xml
<DrawingImage x:Key="IconFolderColorImage">
  <DrawingImage.Drawing>
    <DrawingGroup>
      <GeometryDrawing Brush="#FFB800" Geometry="F1 M2,4 H10 L12,7 H22 V20 H2 Z" />
      <GeometryDrawing Brush="#FFD666" Geometry="F1 M2,9 H22 V20 H2 Z" />
    </DrawingGroup>
  </DrawingImage.Drawing>
</DrawingImage>
```

`DrawingGroup` 的操作有固定顺序：`OpacityMask` → `Opacity` → `BitmapEffect` → `ClipGeometry` → `GuidelineSet` → `Transform`。生成含变换的组合时按此顺序理解结果，不要假设可交换。

**背景（`bg_*`）用画刷而不是 `Image`：**

```xml
<!-- 矢量背景，平铺 -->
<DrawingBrush x:Key="BgGridBrush" Viewport="0,0,10,10" ViewportUnits="Absolute" TileMode="Tile">
  <DrawingBrush.Drawing>
    <GeometryDrawing Brush="#F2F3F5" Geometry="M0,0 H1 V1 H0 Z" />
  </DrawingBrush.Drawing>
</DrawingBrush>

<!-- 位图背景，等比填满并裁剪 -->
<ImageBrush x:Key="BgHeaderBrush" ImageSource="/Assets/Images/bg_header.png"
            Stretch="UniformToFill" />
```

`ViewportUnits="Absolute"` 时 `Viewport` 是设备无关单位；默认的 `RelativeToBoundingBox` 下 `Viewport="0,0,0.25,0.25"` 表示"每块占容器四分之一"。两者混淆会得到尺寸完全不对的平铺，且不报错。

**WPF 没有九宫格拉伸机制**（`Image.NineGrid` 是 UWP 的）。圆角卡片、气泡等需要保持边角不变形的背景，只有三条路：改用 `Border` + `CornerRadius` + `Background` 纯样式实现（首选）、把背景拆成角/边/中心多块分别放进 `Grid`、或整块导出为矢量随容器缩放。**不要把整张位图 `Stretch="Fill"` 交付**——边角会被拉伸变形。

`Stretch` 四个取值：`None`（不缩放，超出即裁剪）、`Fill`（撑满，不保持比例）、`Uniform`（完整装入，保持比例）、`UniformToFill`（填满并裁剪，保持比例）。图标恒用 `Uniform`。

## 五、位图与 ICO

**位图统一 PNG。** 需要 alpha 通道，且 WPF 的 PNG codec 支持编解码。JPEG 无 alpha，GIF 只有 1 bit 透明和 256 色，都不适合图标；TIFF/WDP 体积与兼容性都无优势。

**`.ico` 只在 `Window.Icon` 和程序集图标（`<ApplicationIcon>` MSBuild 属性）用。** 二者是不同的东西：前者管标题栏 / 任务栏按钮 / ALT-TAB 条目，后者管桌面上的 exe 图标。

```xml
<Window Icon="WPFIcon1.ico">
```
```csharp
this.Icon = BitmapFrame.Create(new Uri("pack://application:,,,/WPFIcon2.ico", UriKind.RelativeOrAbsolute));
```

ICO 的多分辨率帧由 Windows 按用途挑选：标题栏和任务栏取 16×16，ALT-TAB 取 32×32。**缺失的尺寸会由"尺寸和色深递减"顺序里最接近的帧顶替**，官方明确说明这会造成像素化等不良视觉效果。所以一个只含 16×16 的 ico 在 ALT-TAB 里会被放大到 32×32 显示，糊掉，且不报任何错。要覆盖的尺寸至少是 16 / 32 / 48 / 256。

**skill 无法用 WPF 生成 ico——WPF 没有 ICON 编码器。** 需要 ico 时只有两条路：调用外部工具（如 ImageMagick、Pillow 的 `save(..., format='ICO', sizes=[...])`），或输出多张 png 并明确告知用户"需自行合成 ico"。**不得声称已导出 ico 而实际只产出了 png。**

`.ico` 赋给 `Image.Source` 时，具体取哪一帧不由你控制，官方未承诺行为。图标在界面内使用一律走 Path / DrawingImage / png，不要用 ico。

## 六、图标字体

`Segoe Fluent Icons` 随 Windows 11 提供，Windows 10 只有 `Segoe MDL2 Assets`。WPF 的 `FontFamily` 支持逗号分隔列表做回退：

```xml
<TextBlock Text="&#xE721;" FontFamily="Segoe Fluent Icons, Segoe MDL2 Assets" FontSize="16" />
```

自带字体（打包为 `Resource`）用 `./#FamilyName` 语法，字体名是**字体内部的 family name**，不是文件名：

```xml
<TextBlock FontFamily="/Assets/Fonts/#IconFont" Text="&#xE001;" />
```

**三条注意：**

- 这两个 Segoe 字体是专有系统字体，**随应用分发 TTF 需要向 Microsoft 单独取得授权**，不在默认许可范围内。需跨 Windows 版本保证一致渲染时，优选 MIT 许可的 Fluent UI System Icons 自带字体。
- 字形绝大多数落在 Unicode 私用区（PUA），字体缺失时字体回退拿不到字形，会显示豆腐块。
- 官方建议字号取 16 / 20 / 24 / 32 / 40 / 48 / 64，其他字号可能发虚。

**图标字体不属于本 skill 的导出目标**——它是复用系统资源，不是从设计稿导出资产。仅在用户明确要求"用系统图标替代设计稿图标"时才涉及，且必须由用户确认字形映射，**不得自行猜测哪个 glyph 对应哪个设计图标**。

## 七、清晰度与 DPI

矢量在任意 DPI 下都由渲染管线重新光栅化，不存在缩放模糊；位图在非 100% 缩放下必然重采样。这是"优先矢量"的根本原因，而不仅是体积考虑。

| 属性 | 作用 | 用法 |
|---|---|---|
| `UseLayoutRounding` | measure/arrange 得到的非整数像素值全部取整 | **设在根元素上**。父坐标不在像素边界时子坐标也不会在，逐个元素设是无效的 |
| `SnapsToDevicePixels` | 渲染时把边缘对齐设备像素 | 无法在根元素设 `UseLayoutRounding` 时的替代方案 |
| `RenderOptions.BitmapScalingMode` | 位图缩放算法 | 默认 `Linear`；`HighQuality`(=`Fant`) 更清晰更慢，`NearestNeighbor` 适合像素图放大 |
| `RenderOptions.EdgeMode` | 非文本图元边缘处理 | 设 `Aliased` 关抗锯齿，仅对刻意要硬边的 1px 线有意义 |

1px 描边落在设备像素中间时会被抗锯齿成 2px 半透明灰边——这是"图标看起来发虚"最常见的真实原因，靠换 `BitmapScalingMode` 解决不了，得靠 `UseLayoutRounding`。

`.NET Framework 4.6+` 改过 layout rounding 以减少带边框控件的裁剪，默认启用。跨框架版本比对渲染差异时要考虑这一项。

**位图必须给显式解码尺寸。** 不设 `DecodePixelWidth`/`DecodePixelHeight` 时，WPF 按原始尺寸缓存整张图，而不是按显示尺寸——一张 2000px 的图显示成 40px 也照缓存 2000px：

```xml
<Image Width="40" Height="40">
  <Image.Source>
    <!-- 只设一边以保持宽高比；两边都设会变形 -->
    <BitmapImage DecodePixelWidth="40" UriSource="/Assets/Images/avatar.png" />
  </Image.Source>
</Image>
```

`DrawingImage`、`DrawingBrush`、`Geometry` 都是 `Freezable`。作为资源交付时冻结可去掉变更监听开销：XAML 里用 `PresentationOptions:Freeze="True"`（需声明 `xmlns:PresentationOptions="http://schemas.microsoft.com/winfx/2006/xaml/presentation/options"` 并加入 `mc:Ignorable`）。**但主题切换时需要改颜色的画刷不能冻结**——冻结后任何修改都抛 `InvalidOperationException`。

## 八、命名约定

### 文件名

`snake_case`，`{分类}_{语义}[_{状态}][_{尺寸}].{ext}`，全小写，不含中文、空格和连字符。

| 分类前缀 | 用途 |
|---|---|
| `icon_` | 界面图标 |
| `bg_` | 背景、底图、纹理 |
| `logo_` | 品牌标识 |
| `illus_` | 插画、空状态图 |
| `avatar_` | 头像占位 |

状态后缀限定为 `_normal`（可省略）、`_hover`、`_pressed`、`_disabled`、`_selected`、`_checked`。尺寸后缀仅在同一图标确实存在多套不同尺寸的独立设计（而非同一图形的缩放）时使用，写作 `_16`、`_24`。

**不要用 `@2x`/`@3x` 后缀。** 那是移动端位图倍图方案；WPF 按设备无关单位布局，倍图机制不存在，`@` 在 Pack URI 中也需转义。同一图形的不同尺寸靠矢量缩放解决。

`bg_book_list_shelf.svg` 这类源文件名在导出后应换成目标扩展名（`bg_book_list_shelf.png` 或落进 XAML 资源），**产物目录里不保留 `.svg`**——WPF 不消费它，留着只会让人误以为可用。

### 资源 key

文件名 `snake_case` → 资源 key `PascalCase` + 类型后缀，机械可推导，便于校验：

| 承载形式 | 后缀 | 示例 |
|---|---|---|
| `Geometry` | `Geometry` | `icon_search.svg` → `IconSearchGeometry` |
| `DrawingImage` | `Image` | `icon_folder_color` → `IconFolderColorImage` |
| `DrawingBrush` / `ImageBrush` | `Brush` | `bg_grid` → `BgGridBrush` |
| `SolidColorBrush`（图标配色） | `Brush` | `Icon/Icon-Primary` → `IconIconPrimaryBrush` |

**资源 key 必须全局唯一。** WPF 的 `ResourceDictionary` 合并时同 key 后者覆盖前者，**静默生效、不报错**——两个模块各自定义 `IconSearchGeometry` 时，实际用哪个取决于 `MergedDictionaries` 的顺序。模块化项目应加模块前缀（`ReaderIconSearchGeometry`）。

### 目录

```
Assets/
├─ Icons/          Icons.xaml（Geometry / DrawingImage 资源字典）
├─ Images/         *.png（Build Action = Resource）
├─ Brushes/        Brushes.xaml（背景画刷）
└─ AppIcon.ico     窗口/程序集图标
```

## 九、接入工程

### Build Action

| Build Action | 结果 | 用于 |
|---|---|---|
| `Resource` | 编译进程序集 | **图标资产的默认选择**——单文件分发，不会被误删 |
| `Content` + `CopyToOutputDirectory` | 输出目录旁的松散文件 | 需要不重新编译就替换的资产 |
| `None` + `CopyToOutputDirectory` | 松散文件，程序集无记录 | 运行时才确定的资产（site of origin） |
| `Page` | XAML 编译为二进制 | `.xaml` 资源字典的默认值 |

**改了 Build Action 必须整体重新生成**（rebuild），只 build 不会生效——官方明确说明。这条会造成"我明明改了却没变"的假象。

### Pack URI

```
pack://application:,,,/Assets/Images/icon_search.png            本程序集资源（子目录）
pack://application:,,,/SharedUI;component/Assets/icon.png       被引用程序集的资源
pack://application:,,,/SharedUI;v1.0.0.0;component/Assets/x.png 指定版本（同名程序集共存时）
pack://siteoforigin:,,,/Assets/late_bound.png                   site of origin（只能用绝对形式）
/Assets/Images/icon_search.png                                  相对形式，等价于第一行
```

`,,,` 不是笔误——authority 里的 `/` 必须换成 `,`。`%`、`?` 等保留字符要转义，这也是文件名里禁止特殊字符的原因之一。

**引用其他程序集必须写 `;component`。** 漏掉时 WPF 会把它当本程序集的路径去找，找不到就是运行时资源加载失败。`siteoforigin` authority **不支持** `;component` 语法。

同一个 `pack://application:,,,/X.png` 既可能是资源也可能是内容文件，WPF 靠先探 `AssemblyAssociatedContentFileAttribute`、再探编译进的资源来消解——**副作用是把资产从 `Resource` 改成 `Content` 时 URI 和代码都不用改**，这是有意的设计，不是巧合。

### 资源字典组织

图标资源集中在 `Assets/Icons/Icons.xaml`，由使用方按需合并，**不要无脑塞进 `App.xaml`**——启动时会一次性加载全部字典，直接拖慢冷启动。模块级字典应在模块初始化时动态合入：

```csharp
Application.Current.Resources.MergedDictionaries.Add(
    new ResourceDictionary { Source = new Uri("Assets/Icons/ReaderIcons.xaml", UriKind.Relative) });
```

## 十、静默陷阱

以下情形 exit 0、无告警、XAML 完全合法，但界面上是错的：

| # | 触发条件 | 后果 | 处置 |
|---|---|---|---|
| 1 | `Path` 有 `Width`/`Height` 但没写 `Stretch` | 只显示图形左上角一块 | 图标一律显式 `Stretch="Uniform"` |
| 2 | `Data` 字符串丢了 `F0`/`F1` 前缀 | 按 EvenOdd 解析，孔洞/自相交区域填充反转 | 前缀必须原样保留 |
| 3 | 两个 `ResourceDictionary` 定义同名 `x:Key` | 后合并的静默覆盖前者 | 生成后全局校验 key 唯一性 |
| 4 | 位图未设 `DecodePixelWidth` | 按原始尺寸缓存，内存数十倍浪费 | 显式设一边 |
| 5 | ico 只含 16×16 | ALT-TAB 里被放大显示，模糊 | 至少 16/32/48/256 |
| 6 | 圆角背景整张 `Stretch="Fill"` | 边角被拉伸变形 | 改 `Border`+`CornerRadius`，或拆块，或矢量化 |
| 7 | 冻结了主题相关画刷 | 主题切换时抛 `InvalidOperationException` | 只冻结确认不再变化的对象 |
| 8 | `DrawingBrush` 的 `ViewportUnits` 用错 | 平铺尺寸完全不对 | 绝对尺寸必须显式 `ViewportUnits="Absolute"` |
| 9 | 改了 Build Action 只 build 没 rebuild | 资产仍是旧的 | 强制 rebuild |

陷阱 1 和 2 只在**目视比对**时暴露，任何静态校验都发现不了。交付时必须提示用户实际渲染确认。

## 十一、给 skill 实现的契约建议

产出清单建议沿用 `mastergo-to-wpf` 的 `icons.json` 字段风格并扩展，让两个 skill 的产物可以互相消费：

```json
{
  "svgShortKey": "S0#0",
  "nodeId": "10:2",
  "name": "SearchIcon",
  "fileName": "icon_search",
  "resourceKey": "IconSearchGeometry",
  "format": "path",
  "decision": "single fill, no gradient",
  "width": 16, "height": 16,
  "color": "#4E5969",
  "status": "exported"
}
```

- `format` 取值对应第二节决策树：`path` / `drawing-image` / `drawing-brush` / `png` / `ico` / `unresolved`。
- `decision` 记录判定依据。判为 `png`/`ico`/`unresolved` 时**必须**有依据，不能空着——这是用户推翻自动判定的唯一入口。
- `status` 区分 `exported` / `needs-manual`（如 ico 需外部工具合成）/ `failed`。**不得把 `needs-manual` 包装成 `exported`。**

与相邻 skill 的边界：本 skill 负责**格式决策、命名、清单和工程接入形态**；SVG → `Path.Data` 的实际转换调用 `svg-to-xaml-path`，不自行实现路径解析；整页 XAML 生成属于 `mastergo-to-wpf`，本 skill 不生成页面。

## 参考

- [Imaging Overview - WPF](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/graphics-multimedia/imaging-overview)（codec 清单、ICON 无编码器）
- [Path Markup Syntax](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/graphics-multimedia/path-markup-syntax)（`F0`/`F1` 与默认 EvenOdd；`StreamGeometry` 与 `PathFigureCollection` 是两套"非常相似但不相同"的迷你语言，仅前者支持 FillRule 前缀）
- [Geometry Overview](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/graphics-multimedia/geometry-overview)
- [Drawing Objects Overview](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/graphics-multimedia/drawing-objects-overview)（`DrawingGroup` 操作顺序）
- [Pack URIs in WPF](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/app-development/pack-uris-in-wpf)
- [Application Resource, Content, and Data Files](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/app-development/wpf-application-resource-content-and-data-files)（Build Action、需 rebuild）
- [Window.Icon](https://learn.microsoft.com/en-us/dotnet/api/system.windows.window.icon)（ico 多帧选择规则）
- [FrameworkElement.UseLayoutRounding](https://learn.microsoft.com/en-us/dotnet/api/system.windows.frameworkelement.uselayoutrounding)
- [BitmapScalingMode](https://learn.microsoft.com/en-us/dotnet/api/system.windows.media.bitmapscalingmode)
- [Segoe Fluent Icons font](https://learn.microsoft.com/en-us/windows/apps/design/iconography/segoe-fluent-icons-font)
- [SVG support for Image.ImageSource · dotnet/wpf#86](https://github.com/dotnet/wpf/issues/86)（原生 SVG 仍未实现）


## 十二、矢量失败的 PNG 降级契约

当 SVG 不能由 `svg-to-xaml-path` 无损转换（例如 radialGradient、pattern、filter、无法解析的外部资源），导出 Skill 必须尝试对**同一完整图标父节点**执行 MasterGo D2C PNG 导出；不得对其中一个 PATH、椭圆或局部图层截图后冒充完整图标。

成功降级的 `icons-manifest.json` 记录必须为：

```json
{
  "format": "png",
  "status": "exported",
  "fallbackFrom": "vector",
  "fallbackReason": "svg-to-xaml-path failed: ..."
}
```

D2C 无权限、不能定位完整父节点、没有返回 PNG，或返回路径不存在时，记录 `status: "needs-manual"` 和原始失败原因。PNG 降级不能让失败项显示为 `exported`。

已经转换为 `DrawingGroup` 的线性渐变仍是矢量输出，不属于 PNG 降级；其 `LinearGradientBrush` 的相对/绝对坐标和父级 `DrawingGroup.Transform` 必须由 `svg-to-xaml-path --format drawing --parent-transform ...` 的 stdout 原样保留。
