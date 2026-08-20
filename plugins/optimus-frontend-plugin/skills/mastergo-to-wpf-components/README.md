# mastergo-to-wpf-components

> 版本：1.0.0 | 分类：generator

从 MasterGo 设计稿抽取可复用视觉组件，生成或增量更新 WPF 组件库（组件索引、颜色与 DataTemplate 资源）。

## 所处层级

┌──────────────────────────────┐
│ workflow                     │
├──────────────────────────────┤
│ generator  ★ mastergo-to-    │
│            wpf-components   │
├──────────────────────────────┤
│ quality                      │
├──────────────────────────────┤
│ tool                         │
├──────────────────────────────┤
│ platform                     │
└──────────────────────────────┘

下游：`mastergo-to-wpf`（页面组装，读取组件索引）；上游：`mastergo-icon-expoter`（图标导出，不参与抽取）。

## 触发词 / 内部触发条件

抽取组件、生成组件库、沉淀样式、抽 DataTemplate、这些卡片做成模板、MasterGo 组件转 WPF 控件

## 业务逻辑流程图

Step 0 需求预告 → Step 1 前置检查（约定/环境） → Step 2 目录+确认门 → Step 3 逐区读 DSL
→ Step 4 `extract_components.py` → Step 5 冲突确认 → Step 6 人工接管标注 → Step 7 `dotnet build` → Step 8 交付

## 产出物数据流

MasterGo DSL → 本 Skill → `components-index.json` + `Colors.generated.xaml` + `DataTemplates.generated.xaml`
→ `mastergo-to-wpf`（读取索引组装页面）/ 人工接管（Style/Control 正文、code-behind、动画）

## Skill 依赖关系图

┌─────────────────────────┐      ┌──────────────────────┐
│ mastergo-to-wpf         │◄─────│ mastergo-to-wpf-     │
│ （页面组装）            │ 读取 │ components ★         │
└─────────────────────────┘      └──────────┬───────────┘
                                            │ 读取
                                            ▼
                          ┌─────────────────────────────┐
                          │ wpf-project-conventions     │
                          │ （共享约定，非 Skill）       │
                          └─────────────────────────────┘
