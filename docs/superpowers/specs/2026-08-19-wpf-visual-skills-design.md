# WPF 视觉还原 skill 组（组件库 + 页面组装）— 设计文档

- **日期**：2026-08-19
- **归属插件**：`optimus-frontend-plugin`
- **涉及 skill**：`mastergo-to-wpf-components`（新增）、`mastergo-to-wpf`（改造）、`wpf-project-conventions`（新增共享参考，非 skill）
- **状态**：设计已确认，待实现
- **前序文档**：`docs/superpowers/specs/2026-08-02-mastergo-to-wpf-design.md`、`2026-08-03-mastergo-to-wpf-optimization-design.md`

## 1. 背景与目标

WPF 客户端开发中，重复性 UI 编码的痛点是"画控件、写样式、DataTemplate、动画"等视觉资产工作。设计稿来源以设计工具导出为主（MasterGo），通过仓库已有的 `mastergo-magic-mcp` 直接读取节点、图层与标注。

现有 `mastergo-to-wpf` 产出的是"页面脚手架 + 可选白名单项目映射"，缺一条完整链路：**设计稿 → 可复用组件库 → 组件组装页面**。

### 目标

1. 新增 `mastergo-to-wpf-components`：从 MasterGo 设计稿抽取可复用视觉组件（主题 token、基础控件样式、DataTemplate、自定义控件），生成/增量更新组件库。
2. 改造 `mastergo-to-wpf`：从"结构脚手架"升级为"基于组件库的页面组装"，输出直接落进现有项目，符合项目 MVVM 框架、目录结构、资源字典组织，最好能编译通过。
3. 新增 `wpf-project-conventions`：集中维护项目工程约定（MVVM 框架、解决方案路径、目录结构、资源字典合并清单、命名规范、编译命令），供上述两个 skill 共读。

### 非目标

- 不覆盖图标导出（已有 `mastergo-icon-expoter`）。
- 不覆盖 WPF 性能审查（已有 `wpf-xaml-performance`）。
- 不覆盖设计稿 vs 页面的只读校验（已有 `optimus-qa-ui-consistency-check`）。
- 不做设计稿变更的自动增量同步（沿用既有"重新生成新文件"模式）。
- 不猜测业务模型、数据源、命令或绑定语义；ViewModel 只出骨架。

## 2. 与同插件既有 skill 的边界

| Skill | 职责 | 变化 |
|---|---|---|
| `svg-to-xaml-path` | 图标 SVG → `Path.Data` | 不变，被两个新链路复用 |
| `mastergo-icon-expoter` | MasterGo 图标/背景资产导出为 WPF Icons.xaml | 不变 |
| `wpf-xaml-performance` | 已有 XAML 性能审查 | 不变 |
| `optimus-qa-ui-consistency-check` | 设计稿 vs 页面校验（只读） | 不变 |
| `optimus-fe-dev` | 5 阶段前端工作流（复合 skill） | 不变 |
| **`mastergo-to-wpf-components`（新增）** | 设计稿 → **组件库**（生成/增量更新） | 新 |
| **`mastergo-to-wpf`（改造）** | 设计稿 → **页面**：优先匹配组件库组装，缺组件返回清单 | 功能升级 |

边界规则：components 管"库"，`mastergo-to-wpf` 管"页"。components 不产出页面，`mastergo-to-wpf` 不负责建库（缺组件只报告，不就地新造内联样式，除非用户明确选择原生回退）。

## 3. 架构

```
┌─────────────────────────────┐
│ wpf-project-conventions     │  共享约定（非 skill）
│ CONVENTIONS.md + SAMPLE.md  │  MVVM 框架 / 目录 / 资源字典 / 命名 / 编译命令
└──────────────┬──────────────┘
               │ 共读
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ mastergo-to- │  │ mastergo-to- │
│ wpf-         │→ │ wpf          │
│ components   │  │ (改造)       │
└──────┬───────┘  └──────▲───────┘
       │ 维护             │ 读取
       ▼                  │
┌──────────────┐          │
│ 组件库        │──────────┘
│ Themes/*.xaml │  components-index.json
│ DataTemplates │
│ Controls/     │
└──────────────┘
```

组件库目录与 `components-index.json` 由 components skill 按约定生成并维护，`mastergo-to-wpf` 据此做组件匹配。

## 4. 目录结构

```
plugins/optimus-frontend-plugin/skills/
├── mastergo-to-wpf-components/          （新增）
│   ├── SKILL.md                         编排流程、抽取规则、交付纪律
│   ├── CHANGELOG.md
│   ├── README.md
│   ├── test-prompts.json
│   ├── references/
│   │   └── component-extraction-rules.md 组件判定与资源生成规则
│   └── scripts/
│       ├── extract_components.py         纯函数：DSL JSON → 组件清单/资源
│       └── test_extract_components.py     契约测试
├── mastergo-to-wpf/                     （改造，目录结构保留）
│   ├── SKILL.md                          ← 升级为组件优先的页面组装
│   ├── references/…                      既有 5 份参考文档保留，wpf-project-mapping.md 与约定对齐
│   └── scripts/…                         既有转换器保留，新增组件匹配逻辑
└── wpf-project-conventions/             （新增共享参考，非 skill，同 media-ffmpeg-common 模式）
    ├── CONVENTIONS.md                   约定模板（首次使用前由用户填写）
    └── SAMPLE.md                        示例填写（Prism / CommunityToolkit.Mvvm / 原生三选一）
```

### 职责切分

| 组件 | 职责 |
|---|---|
| `extract_components.py` | 纯函数：DSL JSON + 约定 → 组件清单、资源文件内容、`components-index.json` 增量。不联网、不调 MCP |
| components SKILL.md | MCP 读取、抽取规则、冲突确认、编译验证、交付说明 |
| `mastergo-to-wpf` SKILL.md | 组件匹配、页面组装、图标回填、编译验证、交付说明 |
| `CONVENTIONS.md` | 项目工程约定的事实来源，两个 skill 必须先读 |

脚本与既有 `dsl_to_xaml.py` 同样保持"不吃 MCP、只吃落盘 JSON"的离线可测设计。

## 5. 数据流

### 5.1 `mastergo-to-wpf-components`

```
Step 0  前置检查：MASTERGO_TOKEN / Team 版 / 链接可解析（沿用既有检查）
Step 1  读 wpf-project-conventions → 输出目录、资源字典合并清单、命名规范
Step 2  mcp__getDesignSections + mcp__getMeta
        → 区块目录、Design Tokens、Component 定义；存 .mastergo-dsl/
Step 3  组件抽取（规则见 §6）
        → Themes/Styles.xaml、DataTemplates.xaml、自定义控件、token 资源
Step 4  增量合并：资源 key 冲突 → 展示新旧 diff，用户确认覆盖/保留
Step 5  更新 components-index.json
Step 6  dotnet build 验证 → 失败按输出修复（最多两轮）→ 输出变更摘要
```

### 5.2 `mastergo-to-wpf`（改造后）

```
Step 0  前置检查（同前）
Step 1  读 wpf-project-conventions + components-index.json
Step 2  拉取设计稿 DSL（沿用现有分区流程，3-5 个一批）
Step 3  组件匹配：设计稿节点 → 组件库命中/缺失
        🔴 缺失 → 汇总缺失清单返回，不静默生成内联样式；
            除非用户明确选择"原生 WPF 回退"
Step 4  生成页面 XAML + ViewModel 骨架（仅当约定声明 MVVM 框架时；
        数据源/命令不猜测，属性以设计稿文本为占位并标注 TODO）
Step 5  图标回填（复用 svg-to-xaml-path 流程，沿用既有 Step 5）
Step 6  dotnet build 验证 → 失败修复（最多两轮）→ 交付摘要
```

## 6. 组件抽取规则（关键设计）

### 6.1 可复用判定

| 判据 | 结论 |
|---|---|
| 节点是组件定义（`getMeta` 的 Component / `INSTANCE` 节点） | 抽为组件 |
| 同一视觉模式在设计稿中出现 ≥2 次（如多张同构卡片） | 抽 DataTemplate / 隐式样式 |
| 单次出现且无复用迹象 | 页面内联，不抽 |
| 涉及交互/逻辑（事件、状态、依赖属性） | 抽 UserControl/CustomControl，标注人工接管点 |

### 6.2 样式 vs 控件

- 纯视觉（颜色、圆角、边框、字体）→ `Style` + `ControlTemplate`（或隐式样式）。
- 需要 code-behind 的交互逻辑 → `UserControl`/`CustomControl` 骨架 + 注释标记，不猜测业务实现。
- 主题 token 优先映射项目已有资源（读约定 + 项目资源字典），未映射的才新生成，与既有"严格映射"纪律一致。

### 6.3 命名

- 资源 key 按约定命名规范；组件名优先取自设计稿组件名，不凭空造名。
- token 名转换沿用既有规则（`Text/Text-4` → `TextText4`，保留原名注释）。

## 7. 错误处理

| 情形 | 处理 |
|---|---|
| MasterGo 前置检查失败 / MCP 不可用 | 硬停止，不读设计稿 |
| 组件资源 key 冲突 | 展示新旧 diff，用户确认覆盖/保留，不自动覆盖 |
| 页面组装时组件缺失 | 返回缺失清单，建议先跑 components skill；不静默降级 |
| 设计稿未用 autolayout | 沿用既有退化警告（全 Canvas 绝对定位） |
| 编译失败 | 按 `dotnet build` 输出修复，最多两轮；仍失败输出 diff 交人工 |
| 文本/Token 断链、幻觉文本 | 沿用既有 exit 2 硬停止契约 |

## 8. 测试策略

- 两个 skill 各配 `test-prompts.json`（仓库惯例，与 media 插件同款）。
- `extract_components.py` 为纯函数：DSL JSON + 约定 → 组件清单/资源内容，`unittest` + fixtures（复用既有 `scripts/assets/*.json` 风格），全量离线可跑。
- 组件匹配逻辑（设计稿节点 → 组件库索引命中/缺失）独立 fixture 测试。
- 验收标准：生成产物在用户环境 `dotnet build` 通过；组件库变更以 diff 形式可审查。

## 9. 版本与规范

- 新增 skill → marketplace **Minor** 升版：`8.13.0 → 8.14.0`。
- 改造 `mastergo-to-wpf`（功能增强，非删除/重命名）→ 归入同一 **Minor** 升版。
- SKILL.md frontmatter 遵循 `.claude/rules/skill-authoring.md`；`allowed-tools` 沿用既有：`Read Write Bash PowerShell mastergo-magic-mcp`。
- 同步创建/更新 CHANGELOG.md。

## 10. 已知限制

1. 组件抽取质量上限取决于设计稿是否规范使用组件与 autolayout。
2. ViewModel 只出骨架（属性占位 + TODO），业务逻辑、数据源、命令仍需人工。
3. 动画（Storyboard）初期不自动抽取：设计稿通常不携带动画定义，需用户提供动效描述后手工标注。
4. 字体、光栅图片等限制沿用既有 `mastergo-to-wpf` 的已知限制。
5. 首次使用前必须填写 `wpf-project-conventions/CONVENTIONS.md`（MVVM 框架、解决方案路径、目录结构、资源字典合并清单、编译命令），否则两个 skill 拒绝生成。
