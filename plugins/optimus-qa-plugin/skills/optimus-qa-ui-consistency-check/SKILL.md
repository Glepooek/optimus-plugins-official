---
name: optimus-qa-ui-consistency-check
description: 对比 Figma/MasterGo 设计稿与实际页面的 UI 一致性，生成标准格式验证报告。当用户需要：(1) 对比设计稿与实际页面的视觉还原度；(2) 检查颜色、字体、布局、尺寸、圆角、阴影等维度的偏差；(3) 生成包含差异明细、缺陷清单、截图对比的 UI 一致性验证报告；(4) 用户说"UI走查"、"视觉还原验证"、"对比设计稿"、"UI一致性检查"、"UI对比"时触发。输入：设计稿链接（Figma/MasterGo）+ 实际页面 URL。输出为 Markdown 格式报告，保存至 docs/{产品名}-UI一致性验证报告.md。
creator: yinxuan@optimus.cn
metadata:
  author: desktop client team
compatibility: 需要 Figma MCP、MasterGo MCP（本仓库内置 mastergo-magic-mcp）、Chrome DevTools MCP 均已配置（Figma/Chrome DevTools 需用户自行配置，非本仓库内置）。
allowed-tools: Write Task mastergo-magic-mcp
---

# UI 一致性验证技能

## 概述

对比设计稿（Figma / MasterGo）与实际线上/测试环境页面的视觉还原度，按 8 大验证维度逐项检查，生成结构化 UI 一致性验证报告。

## 验证维度与容差标准

| 验证维度 | 检查项 | 容差标准 |
|---------|--------|---------|
| 布局 | 元素位置、间距、对齐方式 | 位置偏差 ≤ 2px |
| 颜色 | 背景色、文字色、边框色 | 色差 ΔE ≤ 3（人眼不可感知） |
| 字体 | 字号、字重、行高、字间距 | 字号偏差 = 0，行高偏差 ≤ 1px |
| 尺寸 | 元素宽高、图标尺寸 | 尺寸偏差 ≤ 2px |
| 圆角与阴影 | 圆角半径、阴影参数 | 圆角偏差 ≤ 1px |
| 响应式 | 各断点下的布局表现 | 与设计稿定义的断点一致 |
| 交互状态 | hover / active / disabled / focus 样式 | 与设计稿状态标注一致 |
| 图标与图片 | 图标样式、图片裁剪比例 | 视觉无明显差异 |

## 工作流程

### Step 1：收集输入信息

**必需信息：**

| 信息 | 说明 | 示例 |
|------|------|------|
| 设计稿链接 | Figma 或 MasterGo 的页面/节点链接 | `https://www.figma.com/design/{fileKey}/?node-id={nodeId}` |
| 实际页面 URL | 待验证的线上或测试环境页面 | `https://example.com/page` |
| 产品名称 | 用于报告标题和文件命名 | "智课云" |

**可选信息：**
- 视口尺寸（默认取设计稿定义尺寸，常见 1440×900 或 1920×1080）
- 需重点验证的区域/模块
- 页面状态（默认态 / 空态 / 加载态 / 错误态）

**链接解析规则：**

| 设计工具 | URL 格式 | 提取参数 |
|---------|---------|---------|
| Figma | `figma.com/(file\|design)/{fileKey}/...?node-id={nodeId}` | fileKey, nodeId |
| MasterGo | `mastergo.com/goto/{shortLink}` 或 `file/{fileId}?layer_id={layerId}` | shortLink 或 fileId + layerId |

### Step 2：获取设计稿数据

#### Figma 设计稿

**2.1 获取设计稿结构与设计令牌：**

```
工具：mcp__Framelink_Figma_MCP__get_figma_data
参数：fileKey={fileKey}, nodeId={nodeId}
```

返回数据包含完整的 DSL 节点树，其中包含：
- `layout_` 前缀定义 — 布局属性（宽高、padding、gap、对齐方式）
- `fill_` 前缀定义 — 填充色（背景色、渐变色）
- `stroke_` 前缀定义 — 描边（边框颜色、宽度）
- `style_` / `font_` 前缀定义 — 字体属性（字族、字号、字重、行高）
- `effect_` 前缀定义 — 效果（阴影、模糊）

**2.2 提取关键设计令牌（Design Tokens）：**

需从返回数据的定义段中，提取并整理以下设计令牌表：

| 令牌类别 | 需提取内容 |
|---------|-----------|
| 颜色 | 所有 `fill_` 的 HEX 值、渐变参数 |
| 描边 | 所有 `stroke_` 的颜色、宽度、位置 |
| 字体 | 所有 `style_` 的 fontFamily、fontSize、fontWeight、lineHeight |
| 阴影 | 所有 `effect_` 的 boxShadow 参数 |
| 布局 | 关键容器的宽高、padding、gap |

> 💡 Figma 返回数据通常较大（50KB+），建议使用 Agent 工具并行提取设计令牌，避免阻塞主流程。

**2.3 下载设计稿截图：**

```
工具：mcp__Framelink_Figma_MCP__download_figma_images
参数：
  fileKey: {fileKey}
  nodes: [{"fileName": "figma-design-full.png", "nodeId": "{nodeId}"}]
  localPath: "docs/ui-diff"
  pngScale: 2
```

#### MasterGo 设计稿

```
工具：mcp__mastergo_magic_mcp__mcp__getDsl
参数：fileId={fileId}, layerId={layerId}
  或：shortLink={shortLink}
```

### Step 3：采集实际页面数据

**3.1 导航到目标页面：**

```
工具：mcp__chrome_devtools__navigate_page
参数：type="url", url="{实际页面URL}"
```

**3.2 截取页面截图（视口 + 全页）：**

```
工具：mcp__chrome_devtools__take_screenshot
参数：filePath="docs/ui-diff/actual-viewport.png"

工具：mcp__chrome_devtools__take_screenshot
参数：filePath="docs/ui-diff/actual-page-full.png", fullPage=true
```

**3.3 获取页面快照（a11y 树）：**

```
工具：mcp__chrome_devtools__take_snapshot
```

用于了解页面元素结构、内容文字、层级关系。

**3.4 提取实际 CSS 属性（通过 evaluate_script）：**

按以下区域分批提取 `getComputedStyle` 属性：

| 区域 | 提取属性 |
|------|---------|
| 页面全局 | body backgroundColor, fontFamily, fontSize, color |
| 导航栏 | header height, bgColor, borderBottom, padding |
| 页面标题 | h1 fontSize, fontWeight, color, lineHeight, fontFamily |
| 副标题 | fontSize, color, fontWeight |
| Tab/Radio按钮 | bgColor, border, borderRadius, fontSize, width, height, padding |
| 区块标题 | fontSize, fontWeight, color, lineHeight |
| 卡片容器 | bgColor, borderRadius, boxShadow, padding, width, height |
| CTA按钮 | bgColor, color, fontSize, fontWeight, borderRadius, width, height, padding, boxShadow |
| 输入/选择框 | bgColor, border, borderRadius, fontSize, height |

**JavaScript 提取模板：**

```javascript
() => {
  const results = {};
  // 页面背景
  const bs = getComputedStyle(document.body);
  results.body = { bgColor: bs.backgroundColor, fontFamily: bs.fontFamily, fontSize: bs.fontSize };
  // 标题
  const h1 = document.querySelector('h1');
  if (h1) {
    const s = getComputedStyle(h1);
    results.title = { fontSize: s.fontSize, fontWeight: s.fontWeight, color: s.color, lineHeight: s.lineHeight };
  }
  // ... 对每个关键区域重复此模式
  return results;
}
```

**3.5 提取交互状态样式（可选，按需执行）：**

对关键交互元素（按钮、链接、Tab），通过 hover / click 操作后再次提取 CSS：

```
工具：mcp__chrome_devtools__hover → 参数：uid={元素uid}
工具：mcp__chrome_devtools__evaluate_script → 提取 hover 态 CSS
```

### Step 4：逐维度对比分析

将设计令牌与实际 CSS 值逐项对比，按 8 大维度分类检查。

**4.1 颜色对比**

| 对比项 | 设计稿值 | 实际值 | 判定方法 |
|--------|---------|--------|---------|
| 品牌主色 | fill 定义 HEX | getComputedStyle rgb | 转换为相同格式后比较，ΔE > 3 为差异 |
| 背景色 | fill 定义 HEX | body/container bgColor | 同上 |
| 文字色 | style 定义 color | element color | 同上 |
| 边框色 | stroke 定义 color | border-color | 同上 |

**RGB 转 HEX 规则：** `rgb(r, g, b)` → `#RRGGBB`

**4.2 字体对比**

| 对比项 | 容差 |
|--------|------|
| fontSize | 必须精确匹配（0偏差） |
| fontWeight | 必须精确匹配 |
| lineHeight | 偏差 ≤ 1px |
| fontFamily | 中文环境使用系统字体栈替代 Roboto/Inter 视为合理偏差 |

**4.3 布局对比**

| 对比项 | 容差 |
|--------|------|
| 容器宽高 | ≤ 2px（需考虑视口差异） |
| padding / margin | ≤ 2px |
| gap | ≤ 2px |
| 元素相对位置 | 左右/上下结构必须一致 |
| 对齐方式 | 必须一致 |

> ⚠️ 视口差异处理：设计稿宽度（如1440px）与实际视口（如1536px）不同时，需按比例换算或标注为已知差异。

**4.4 尺寸对比**

对关键元素（按钮、卡片、图标）的 width/height 与设计稿 layout 定义对比，偏差 > 2px 记录为差异。

**4.5 圆角与阴影**

- borderRadius 偏差 > 1px 记录为差异
- boxShadow 参数（x、y、blur、spread、color）需逐项对比

**4.6 交互状态**

对比设计稿中标注的 hover/active/disabled 状态与实际页面对应状态的样式是否一致。

### Step 5：差异分级

**严重程度分级标准：**

| 级别 | 定义 | 示例 |
|------|------|------|
| P1（严重） | 布局结构性差异、品牌色错误、功能流程变更 | 面板左右反转、主色调完全不同、步骤数不一致 |
| P2（一般） | 单个元素的颜色/尺寸/间距偏差超容差 | 按钮高度差 10px、背景色偏差、阴影缺失 |
| P3（轻微） | 文案微调、合理的技术适配偏差 | 字体栈替换、文案措辞调整 |
| —（合理偏差） | 技术适配、状态不同导致 | 中文字体适配、默认态vs空态差异 |

**差异编号规则：** `UI-DIFF-{三位序号}`，如 `UI-DIFF-001`

**缺陷编号规则：** `BUG-UI-{三位序号}`，仅标记 "是否为缺陷 = 是" 的差异项

### Step 6：生成报告

按照 `references/report-template.md` 模板生成完整报告。

**输出路径：** `docs/{产品名}-UI一致性验证报告.md`

**报告章节：**

1. 文档信息表
2. 验证范围表
3. 验证结果汇总表
4. 差异明细（按维度分组的表格）
5. 确认为缺陷的差异项
6. 差异分布统计（按严重程度、按类型）
7. 截图对比（设计稿 vs 实际页面）
8. 人工审核记录
9. 关键结论与建议

**报告生成规则：**
- 所有差异项必须标注"是否为缺陷"，仅超出容差或结构性偏差标记为"是"
- 截图保存在 `docs/ui-diff/` 目录，报告中使用相对路径引用
- 结论部分需给出核心问题列表和可操作的修复建议
- 数据不足的维度（如交互状态设计稿未标注），注明"设计稿未标注，无法验证"

## 工具链总览

| 步骤 | 使用工具 | 用途 |
|------|---------|------|
| 获取 Figma 数据 | `mcp__Framelink_Figma_MCP__get_figma_data` | 获取设计稿 DSL 节点树和设计令牌 |
| 下载设计稿截图 | `mcp__Framelink_Figma_MCP__download_figma_images` | 下载设计稿 PNG 截图 |
| 获取 MasterGo 数据 | `mcp__mastergo_magic_mcp__mcp__getDsl` | 获取 MasterGo 设计稿数据 |
| 页面导航 | `mcp__chrome_devtools__navigate_page` | 打开目标页面 |
| 页面截图 | `mcp__chrome_devtools__take_screenshot` | 截取实际页面（视口/全页） |
| 页面快照 | `mcp__chrome_devtools__take_snapshot` | 获取页面 a11y 树结构 |
| CSS 属性提取 | `mcp__chrome_devtools__evaluate_script` | 执行 JS 提取 getComputedStyle |
| 交互状态模拟 | `mcp__chrome_devtools__hover` / `click` | 模拟 hover/click 后提取状态样式 |
| 设计令牌提取 | Agent 工具（general-purpose） | 从大体积 Figma 数据中并行提取设计令牌 |

## 并行执行策略

以下步骤可并行执行以提高效率：

```
并行组 1（数据采集）：
  ├── 获取 Figma 设计稿数据 + 下载截图
  └── 导航实际页面 + 截图

并行组 2（数据提取）：
  ├── Agent: 从 Figma DSL 提取设计令牌
  └── evaluate_script: 提取实际页面 CSS 属性

顺序执行：
  → 逐维度对比分析
  → 差异分级
  → 生成报告
```

## 质量检查

- [ ] 设计稿截图和实际页面截图均已保存至 `docs/ui-diff/`
- [ ] 8 大验证维度均已检查或注明"无法验证"原因
- [ ] 每个差异项包含：编号、区域、类型、描述、设计稿值、实际值、严重程度、是否为缺陷
- [ ] 确认为缺陷的差异项已独立列表，含缺陷ID和关联UI-DIFF编号
- [ ] 差异分布统计（按严重程度、按类型）已生成
- [ ] 结论包含核心问题列表和可操作修复建议
- [ ] 报告已保存至 `docs/{产品名}-UI一致性验证报告.md`

## 参考资源

- **报告格式模板**：见 `references/report-template.md`，包含完整章节结构和示例
