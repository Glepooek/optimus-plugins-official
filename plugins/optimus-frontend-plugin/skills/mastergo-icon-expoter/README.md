# mastergo-icon-expoter

> 版本：1.0.0 | 分类：generator

从 MasterGo 设计稿导出图标、背景等视觉资产，产出 WPF 可直接引用的资源字典、位图和决策清单。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│  tool        │  svg-to-xaml-path（被委派，完成 SVG→Path.Data）
├─────────────┤
│  quality     │
├─────────────┤
│★ generator   │  mastergo-icon-expoter（本 skill）
├─────────────┤
│  workflow    │  mastergo-to-wpf（整页转换，独立流程，不消费本 skill 产物）
└─────────────┘
```

## 触发词

从 MasterGo 设计稿导出图标、导出 WPF 图标资产、导出图标资源字典、生成 Icons.xaml。

## 业务逻辑流程图

```
Step 0  前置检查（token / 文件版本 / 链接可解析）
   ↓
Step 1  拉取目录，扫描 PATH/IMAGE 节点
   ↓
Step 2  🔴 CHECKPOINT：范围 + 待命名项 + 输出目录 + 是否需要 ico
   ↓
Step 3  逐图标委派 svg-to-xaml-path，组装 input.json
   ↓
Step 4  运行 icon_exporter.py（契约校验 → 格式决策 → 命名 → 渲染 → 自检 → 原子写入）
   ↓
Step 5  交付纪律（needs-manual 转达、Stretch 提醒、ico 降级如实说明）
```

## 产出物数据流

MasterGo 设计稿链接 → 本 skill → `Icons.xaml` + `Images/*.png` + `icons-manifest.json` → 人工接手（用户在自己的 XAML 里引用 `{StaticResource IconXxxGeometry}`）。

## Skill 依赖关系图

```
用户 ──触发──▶ mastergo-icon-expoter ──委派──▶ svg-to-xaml-path
                       │
                       └──调用──▶ mastergo-magic-mcp（getDesignSections / extractSvg / getD2c）
```

不被其他 skill 调度；不消费也不产出 `mastergo-to-wpf` 的 `icons.json`（两者是不同的产物形态，互不依赖）。
