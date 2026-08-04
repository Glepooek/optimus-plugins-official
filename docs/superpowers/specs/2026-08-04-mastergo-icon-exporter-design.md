# mastergo-icon-expoter Skill 设计

## 背景

`optimus-frontend-plugin` 已有 `mastergo-to-wpf`（整页转换）和 `svg-to-xaml-path`（SVG→WPF Path 转换器），但没有专门处理"从 MasterGo 设计稿导出图标/背景资产供 WPF XAML 项目使用"的 skill。`references/wpf-xaml-icon-sepc.md`（已在本次会话前完善）定义了目标格式规格：WPF 侧接受什么承载形式、命名约定、静默陷阱清单。本设计确定如何实现导出这份规格所要求的资产。

## 产物边界

只产出资源字典 + 位图 + 决策清单，不碰用户项目里已有的页面代码：

```
Assets/
├─ Icons/Icons.xaml      ← Geometry / DrawingImage 资源
├─ Images/*.png          ← 位图兜底
└─ icons-manifest.json   ← 决策依据 + 待人工处理项
```

用户在自己的页面里引用 `{StaticResource IconSearchGeometry}`。与 `mastergo-to-wpf` 的图标回填（Step 5：把 `<!-- ICON:key -->` 占位替换为真实 `Path.Data`）是不同的产物形态，两者不合并——那属于另一条已有流程，不在本 skill 范围内。

## 架构：厚脚本 + 薄编排

agent 负责需要判断力的部分，脚本负责需要确定性的部分，两者靠 JSON 契约解耦。

```
┌─ agent 侧（SKILL.md 编排）──────────────────────┐
│                                                  │
│  MasterGo 链接                                   │
│      ↓ mcp__getDesignSections（不带 sectionIndex）│
│  分区目录 → 扫出 PATH / IMAGE 节点               │
│      ↓                                           │
│  🔴 CHECKPOINT：范围 + 待命名项 + 输出目录       │
│      ↓ mcp__extractSvg（分页）                   │
│  逐个图标的 SVG 标记                             │
│      ↓ 委派 svg-to-xaml-path skill               │
│  Path.Data / 多个 Path（含 Fill、告警）          │
│      ↓                                           │
│  写入 .mastergo-icons/input.json  ← 中间契约     │
└──────────────────┬───────────────────────────────┘
                   ↓
┌─ 脚本侧（icon_exporter.py，零 MCP、零网络）─────┐
│  读 input.json                                   │
│    ├─ validate   契约校验                        │
│    ├─ decide     格式决策                        │
│    ├─ name       命名推导 + key 生成             │
│    ├─ render     组装 Icons.xaml + manifest      │
│    └─ selfcheck  写盘前一致性闸门                │
└──────────────────┬───────────────────────────────┘
                   ↓
        Assets/Icons/Icons.xaml
        Assets/Images/*.png
        icons-manifest.json
```

### 职责边界

| 归属 | 内容 | 理由 |
|---|---|---|
| agent 独占 | MCP 调用、CHECKPOINT、委派 `svg-to-xaml-path`、解读其 stderr 告警 | 脚本进程拿不到 MCP；告警需要判断力 |
| 脚本独占 | 格式决策、命名、XAML 组装、清单、自检 | 需要确定性和可测试性 |
| **禁止 agent 做** | 修改几何字符串、手拼 XAML、发明尺寸/颜色 | 静默陷阱的源头 |
| **禁止脚本做** | 联网、读 token、调 MCP、写用户页面代码 | 与 `mastergo-to-wpf` 转换器同一纪律 |

**红线：** `svg-to-xaml-path` 返回的 `Data` 字符串必须逐字写进 `input.json`，包括 `F0`/`F1` 前缀。agent 不得删改、不得补全、不得为了"看起来整齐"重排。此条由脚本 `validate` 层强制校验（缺前缀即 exit 2）。

位图分支走 `mcp__getD2c`（自带落盘能力），不经过 `svg-to-xaml-path`——数据来源不同，不是同一条流水线上的分支。

## 中间契约（`input.json`）

agent 与脚本唯一的接口。

```json
{
  "meta": {
    "fileId": "176452330285910",
    "layerId": "2:2845",
    "outDir": "src/Assets",
    "mergeMode": "merge"
  },
  "icons": [
    {
      "svgShortKey": "S0#0",
      "nodeId": "10:2",
      "dslName": "SearchIcon",
      "userName": null,
      "width": 16,
      "height": 16,
      "paths": [
        { "data": "F1 M3,3 H21 V21 H3 Z", "fill": "#4E5969", "stroke": null }
      ],
      "warnings": [],
      "sourceKind": "vector"
    },
    {
      "svgShortKey": "S0#3",
      "nodeId": "10:9",
      "dslName": "搜索图标",
      "userName": "icon_search_alt",
      "width": 24,
      "height": 24,
      "paths": [
        { "data": "F1 M2,4 H10 L12,7 H22 V20 H2 Z", "fill": "#FFB800", "stroke": null },
        { "data": "F1 M2,9 H22 V20 H2 Z", "fill": "#FFD666", "stroke": null }
      ],
      "warnings": ["class attributes were encountered; CSS classes were not converted."],
      "sourceKind": "vector"
    },
    {
      "nodeId": "i:1",
      "dslName": "Avatar",
      "userName": null,
      "width": 40,
      "height": 40,
      "paths": [],
      "warnings": [],
      "sourceKind": "bitmap",
      "bitmapPath": ".mastergo-icons/raw/avatar.png"
    }
  ]
}
```

### 设计要点

- **`paths` 是数组，长度即决策依据。** `svg-to-xaml-path` 已按合并键（`Fill`+`Stroke`+`fill-rule`+`transform`）判定过能否合并。长度 1 → 单色 → `Geometry`；长度 >1 → 多色 → `DrawingImage`+`DrawingGroup`。脚本不重新判断颜色，只数长度——判断权留在已被 74 条测试锤过的实现里。
- **`userName` 与 `dslName` 分离。** `dslName` 是 DSL 原值，永远原样保留供人工对照；`userName` 只在 CHECKPOINT 用户补名后填。命名优先级：`userName` → 从 `dslName` 推导 → 推导失败则 exit 2（不该走到这一步，CHECKPOINT 应已拦住）。
- **`warnings` 原文照搬**，由 agent 从 `svg-to-xaml-path` 的 stderr 抄入，脚本只透传不解读，避免两处对告警的理解漂移。
- **`sourceKind` 只有 `vector` / `bitmap`。** 更细的格式（`path`/`drawing-image`/`drawing-brush`/`png`）由脚本推导后写进清单，不在输入里——输入描述事实，输出描述决策。
- **`meta.mergeMode` 取值 `merge`/`overwrite`/`separate`。** 对应 CHECKPOINT 里"已存在 `Icons.xaml` 时如何处理"的用户决定（见「错误处理与边界场景」）。`merge` 时自检第 3 条的 `x:Key` 唯一性校验要连同已存在文件的 key 一起比对；`overwrite`/`separate` 时只比对本次新增内容。缺省为 `separate`（不确定时最安全，绝不静默覆盖旧文件）。

### 契约违规即硬失败

缺 `svgShortKey`（矢量项）、缺 `nodeId`、`paths` 为空但 `sourceKind` 是 `vector`、`data` 不以 `F0`/`F1` 开头——全部 exit 2、stdout 为空、stderr 单行 `error: ...`，且不创建任何输出文件。

## 脚本内部五层

```
input.json
    ↓
1. validate   契约校验；违规 → exit 2，不进入后续任何一层
    ↓ 校验通过的 icons[]
2. decide     纯函数：bitmap→png；vector,len(paths)==1→path；vector,len(paths)>1→drawing-image
    ↓ [(icon, format, decision)]
3. name       userName/dslName → fileName + resourceKey；冲突检测；纯函数
    ↓ 带命名的条目
4. render     组装 Icons.xaml 文本 + manifest 字典；纯字符串生成，不落盘
    ↓ {文件名: 内容}
5. selfcheck  对"即将写入的内容"自检；不通过 → exit 2，一个文件都不写
    ↓ 全部通过
原子写入：全部文件一起落盘
```

两条设计纪律：

1. **先全部渲染校验，再一起写入**（沿用 `mastergo-to-wpf` 转换器做法）——硬错误不产生半成品目录。
2. **自检对象是内存里的待写内容，不是磁盘文件**——这样自检才有阻止写入的权力。

### ico 分支（Pillow 可选依赖）

```
需要 ico（用户明确要求窗口/程序集图标）
    ↓
try import PIL
  ├─ 成功 → 从矢量渲染或位图合成 16/32/48/256 四帧 → app_icon.ico
  │         manifest: status=exported
  └─ ImportError → 输出 4 张独立 png
            manifest: status=needs-manual
            reason="WPF 无 ICON 编码器且未检测到 Pillow；请用外部工具合成 ico"
```

降级路径必须在 stderr 打一行告警，manifest 的 `status` 如实为 `needs-manual`，不得包装成成功。`import PIL` 放在 ico 分支函数内部，不放模块顶部——不要 ico 的用户不因未装 Pillow 而跑不起来。

## 命名推导规则

`dslName` → `fileName` 的算法：

```
1. 去掉常见图形容器噪音词：Frame/Group/Vector/Rectangle/Ellipse（不区分大小写，整词匹配）
2. 剩余文本全部非 ASCII 字母数字字符 → 判定失败
3. camelCase / kebab-case / PascalCase → snake_case
4. 前缀规则：
   - 名称含 icon/图标 → icon_ 前缀（去掉该词本身，避免 icon_icon_search）
   - 名称含 bg/background/背景 → bg_ 前缀
   - 名称含 logo → logo_ 前缀
   - 都不含 → 不臆造分类，判定失败，等用户在 CHECKPOINT 里给完整名（含前缀）
5. 结果为空、或推导后与已有 fileName 冲突 → 判定失败
```

示例（同时是测试用例）：

| dslName | 推导结果 | 说明 |
|---|---|---|
| `SearchIcon` | `icon_search` | camelCase 拆分 + icon 前缀 |
| `search-icon` | `icon_search` | kebab-case 拆分 |
| `Icon/Search` | `icon_search` | 分隔符视为词界 |
| `bg-header-gradient` | `bg_header_gradient` | 已有前缀词，不重复加 |
| `搜索图标` | 失败 | 非 ASCII，交给用户 |
| `Frame 427` | 失败 | 去噪音词后只剩数字，无法判定分类 |
| `CloseButton` | 失败 | 没有 icon/bg/logo 关键词，不臆造分类 |

推导只做词法匹配，不做语义猜测（`CloseButton` 显然是图标但仍判定失败）——这是刻意收紧：让推导行为对 agent、对用户都可解释、可预测，宁可多问一次也不让"AI 猜的"和"规则推的"混淆。

资源 key 由 `fileName` 机械推导（`icon_search` → `IconSearchGeometry`/`IconSearchImage`），100% 确定性，不需要用户确认，只在 CHECKPOINT 的命名表里一并展示供核对。

### CHECKPOINT 展示格式

```
以下 2 个图标无法自动命名，请补充文件名（snake_case，含分类前缀 icon_/bg_/logo_）：

| svgShortKey | DSL 名称 | 尺寸 | 建议 |
|---|---|---|---|
| S0#3 | 搜索图标 | 24×24 | ? |
| S0#7 | CloseButton | 16×16 | ? |

其余 8 个图标已自动推导命名，将在下方一并展示供确认。
```

## 自检规则

写盘前的最后一道闸门，检查对象是内存中即将写入的内容，任一条不通过则 exit 2、不落任何文件。

| # | 检查项 | 对应静默陷阱 |
|---|---|---|
| 1 | 每个 `Geometry`/`GeometryDrawing.Geometry` 的 `Data` 都以 `F0 `或`F1 `开头 | 丢前缀导致填充反转 |
| 2 | 每个矢量图标在使用处都带 `Stretch="Uniform"` | 不写 Stretch 默认 None，只显示左上角一块 |
| 3 | `Icons.xaml` 内 `x:Key` 两两不同；`mergeMode: merge` 时还需与已存在的 `Icons.xaml` 比对不冲突 | 后合并的字典静默覆盖同名 key |
| 4 | manifest 里每条记录的 `resourceKey`/`fileName` 与实际写入内容一一对应，无遗漏、无多余 | 清单与产物脱节 |
| 5 | 所有 `status: needs-manual` 的记录都有非空 `reason` | 判定依据不能空着 |
| 6 | 位图输出前，png 都有确定宽高（非 0、非负） | 防止下游 `DecodePixelWidth` 类问题从源头产生 |
| 7 | ico 分支：降级为 png 时，manifest 状态不得为 `exported` | 不得把降级包装成成功 |

自检失败报错格式（多条一次性列出，因均为静态检查、无先后依赖）：

```
error: self-check failed:
  - IconSearchGeometry: Data missing F0/F1 prefix
  - duplicate x:Key "IconCloseGeometry" (icon_close, icon_close_alt)
```

**边界：** 不检查用户项目里已有的 XAML 是否正确使用了这些资源（属于"另建校验 skill"的范围，本次已决定不做，记录为已知取舍）；不检查视觉还原度（需要截图比对，超出范围）。自检严格限定在"脚本自己产出的文件内部一致、自洽"。

## 错误处理与边界场景

| 场景 | 处置 |
|---|---|
| `getDesignSections` 区块数过多 | 沿用 `mastergo-to-wpf` 规则：超过 8 个区块停止，请用户指定范围 |
| 图标节点不是 `PATH` 也不是 `IMAGE`（如 `INSTANCE`） | 列入 CHECKPOINT 的"未识别节点"清单，不猜测类型，不产出 |
| `extractSvg` 对某个 `svgShortKey` 返回空/404 | 标记 `sourceKind: "unresolved"`，写入 manifest 但不进入 `decide`，不中断整批 |
| 委派后收到"多路径异色"的多个 `Path` | agent 按 `paths` 数组逐条填入 input.json，不要求用户在这一步二次确认——决策已在脚本 `decide` 层自动走向 `drawing-image` |
| `svg-to-xaml-path` 遇到 `currentColor`/渐变 URL 报错（exit 2） | 原样转达错误给用户，该图标标记 `unresolved`，reason 抄自兄弟 skill 的错误原文，不中断整批 |
| ico 目标同时含矢量和位图来源 | 优先取矢量渲染，位图仅作 fallback；决策依据写入 manifest |
| `--out` 目录已有同名 `Icons.xaml` | 默认不覆盖，询问用户覆盖/合并/另存（CHECKPOINT 环节的一部分），选择结果写入 `meta.mergeMode` 供脚本读取 |
| MasterGo 草稿箱文件 / 无 `MASTERGO_TOKEN` | 沿用 `mastergo-to-wpf` Step 0 前置检查 |

**统一原则：** 单个图标失败不中断整批（降级为 `unresolved`）；只有契约校验或自检失败才整体 exit 2。

### CHECKPOINT 完整结构

```
🔴 CHECKPOINT（一次性展示，等待用户确认或修正）：
1. 待处理范围：N 个图标节点（矢量 M 个 / 位图 K 个 / 未识别 J 个）
2. 待人工命名：2 项（见表）
3. 输出目录：src/Assets（已存在 Icons.xaml，将合并 / 覆盖 / 另存 —— 请选择）
4. 是否需要 ico：否 / 是（涉及哪些图标）
```

## 测试策略

对齐仓库惯例（`svg-to-xaml-path` 74 条、`mastergo-to-wpf` 同等量级），本机只有 `unittest`。

测试文件：`scripts/test_icon_exporter.py`，按五层结构覆盖：

| 层 | 覆盖重点 |
|---|---|
| `validate` | 缺字段、`data` 无前缀、`sourceKind` 与 `paths` 不一致 → 均 exit 2 且零输出 |
| `decide` | `paths` 长度 1→path，>1→drawing-image，`sourceKind:bitmap`→png；边界：2 条同色仍走 drawing-image（决策只看长度） |
| `name` | 命名推导表全部案例逐条断言；冲突检测 |
| `render` | `Icons.xaml` 结构断言（`Geometry`/`DrawingImage`/`DrawingGroup` 各一例）；manifest 字段完整性 |
| `selfcheck` | 七条规则各构造一个刻意违反的样例，断言被拦截且不写盘 |
| 集成 | 完整 `input.json`（矢量单色/多色、位图、待命名、unresolved 各一条）跑全流程，断言产物目录结构 |

关键回归用例：

1. `data` 前缀大小写变体（如 `f1`）判定为无效，不做大小写兼容——WPF 迷你语言本身区分大小写。
2. ico 降级路径：mock `import PIL` 失败 → 断言产出 4 张 png、manifest `status=needs-manual`，且没有 `app_icon.ico` 被创建。
3. 自检失败时，断言 `Assets/` 目录下没有任何新文件被写入（临时目录前后快照比对）。

**不测的部分：** MCP 调用——脚本本身不碰 MCP，正确性依赖 agent 编排和真实环境验证，与 `mastergo-to-wpf` 转换器"不联网、不测 MCP"的测试哲学一致。

本地测试命令：

```bash
python -m unittest discover -s plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/scripts -p "test_*.py"
```

## 文件结构

```
plugins/optimus-frontend-plugin/skills/mastergo-icon-expoter/
├─ SKILL.md                          编排步骤 + CHECKPOINT + 红线 + 交付纪律
├─ CHANGELOG.md                      [1.0.0]，本次新建
├─ README.md                         按 skill-authoring.md 规范补全五章节
├─ references/
│  └─ wpf-xaml-icon-sepc.md          已完善，SKILL.md 引用它
└─ scripts/
   ├─ icon_exporter.py               五层实现
   └─ test_icon_exporter.py          测试
```

### SKILL.md frontmatter

```yaml
---
name: mastergo-icon-expoter
description: 当用户要求从 MasterGo 设计稿导出图标、背景等视觉资产用于 WPF XAML 项目时使用此 Skill；产出 Geometry/DrawingImage 资源字典、位图与决策清单，不生成页面代码。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: generator
compatibility: Python 3 标准库；可选 Pillow（用于 .ico 合成，未安装时降级为多张 png）；需 mastergo-magic-mcp（本仓库 plugins/optimus-mcp-servers/.mcp.json 内置）与 MASTERGO_TOKEN；委派 optimus-frontend-plugin:svg-to-xaml-path 完成 SVG→Path.Data 转换。
allowed-tools: Read Write Bash PowerShell Skill mastergo-magic-mcp
---
```

### SKILL.md 正文骨架

1. Step 0：前置检查（同 `mastergo-to-wpf`：token、文件版本、可解析链接）
2. Step 1：拉取目录，扫 PATH/IMAGE 节点
3. Step 2：🔴 CHECKPOINT
4. Step 3：逐图标委派 `svg-to-xaml-path`，组装 `input.json`
5. Step 4：运行 `icon_exporter.py`
6. Step 5：交付纪律（needs-manual 项必须转达、不得声称降级为成功）
7. 参考：链接 `references/wpf-xaml-icon-sepc.md`

## 跨插件/跨 skill 检查

- 无跨插件重复——仓库内没有其他 skill 做"MasterGo → WPF 图标资产"。
- 配对检查：本 skill 是生成器（generator）；对应的校验器已明确排除（"不检查用户已有 XAML"），记录为已知取舍，不视为缺口。
- 版本管理：`plugins/` 下新增 skill → marketplace.json Minor 版本升级（`8.5.3` → `8.6.0`），随实现一起提交。

## 已知取舍（非缺口，供未来参考）

- 不校验用户现有 XAML 是否正确使用产出的资源——超出本 skill 边界，需要时应另建校验 skill。
- 不做视觉还原度校验——需要截图比对能力，超出范围。
- ico 合成依赖可选的 Pillow，未安装时功能降级而非报错，接受这一权衡以避免强制引入第三方依赖。
