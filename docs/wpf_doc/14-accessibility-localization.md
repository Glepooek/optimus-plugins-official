# 14 · 可访问性与本地化

> 更新历史：2026-08-21 创建。

可访问性让所有人能用，本地化让多语言可交付。本篇约束自动化属性、键盘导航、高对比度与多语言资源。

## 1. 自动化属性（AutomationProperties）

- **必须**：关键交互元素配 `AutomationProperties.Name`（屏幕阅读器读出的名称），**禁止**图标按钮 / 纯图形无名称
- **必须**：纯装饰元素 `AutomationProperties.AutomationId` 唯一且 `Focusable="False"`（不进焦点 / 读屏）
- **必须**：组合控件（`ComboBox`、`ListBox`）提供可读的自动化名称与项文本
- **应该**：动态区域（状态文本、进度）用 `AutomationProperties.LiveSetting` 提示读屏器轮询
- **禁止**：用图片当文字且无 `AutomationProperties.Name`（读屏无法读出）

```xml
<!-- ❌ 图标按钮无名称：读屏读出"Button"却不知是什么，纯图形无法理解 -->
<Button>
  <Path Data="{StaticResource SaveIcon}" />
</Button>

<!-- ✅ 图标按钮配 AutomationProperties.Name：读屏读出"保存" -->
<Button AutomationProperties.Name="保存">
  <Path Data="{StaticResource SaveIcon}" />
</Button>
```

```xml
<!-- ❌ 装饰元素可聚焦：分隔符 / 装饰图标进 Tab 顺序，键盘用户迷失 -->
<Separator AutomationProperties.AutomationId="div1" />

<!-- ✅ 纯装饰元素：明确不可聚焦，自动化 id 唯一但无名称（不读） -->
<Separator AutomationProperties.AutomationId="divider1" Focusable="False" />
```

```xml
<Button AutomationProperties.Name="保存订单">
  <Path Data="{StaticResource SaveIcon}" />
</Button>
```

## 2. 键盘导航

- **必须**：应用完整可键盘操作（Tab 顺序、`Enter` 触发默认、`Esc` 取消），**禁止**关键功能仅鼠标可操作
- **必须**：`TabIndex` 逻辑顺序与视觉顺序一致；复杂表单设合理的焦点顺序
- **必须**：可见焦点指示（`FocusVisualStyle`）不关闭，**禁止**移除焦点边框让键盘用户迷失
- **应该**：快捷键用 `AccessKey` / `InputBindings` 声明（联动 `06` 章第 7 节），快捷键在帮助中可查
- **禁止**：键盘陷阱——`Dialog` / 模态内无法 Tab 出（`IsCancel` 兜底）

## 3. 高对比度与主题适配

- **必须**：界面适配系统高对比度模式（`SystemColors` / 系统画刷动态资源），**禁止**硬编码颜色忽略高对比
- **必须**：文本颜色与背景对比度达标（WCAG AA 级，普通文本 ≥ 4.5:1），**禁止**低对比配色
- **应该**：主题资源用系统级动态资源（`SystemColors.ControlBrushKey` 等）承接高对比切换（联动 `07` 章主题切换）
- **禁止**：仅用颜色区分状态（需辅助图标 / 形状区分，色盲友好）

## 4. 字体与缩放

- **必须**：文本用相对尺寸（系统字体大小 / `FontSize` 继承），**禁止**硬编码像素字体大小
- **必须**：界面随系统字体缩放 / DPI 缩放自适应（联动 `08` 章第 5 节），**禁止**固定尺寸导致高 DPI 裁切
- **应该**：可读性选项（字体放大、显示密度）提供应用内设置
- **禁止**：滚动容器内截断关键文本不提供完整内容访问

## 5. 本地化资源

- **必须**：用户可见文案集中资源（`resx` / 资源字典），**禁止**硬编码字符串散落 XAML / 代码
- **必须**：本地化资源统一 key 命名（`{Module}.{Control}.{Text}`），**禁止**无意义 key（`String1`）
- **必须**：`CultureInfo` / `UI Culture` 在应用启动时按系统或用户设置初始化，**禁止**不同语言混用（格式化 / 日期货币）
- **应该**：资源支持动态切换（运行期换语言），用 `DynamicResource` 引用本地化资源
- **禁止**：本地化文本用拼接占位符做复数 / 顺序调整（用 `.NET` 资源格式化的参数占位）

## 6. 日期、数字与格式

- **必须**：日期 / 时间 / 数字显示按当前 `CultureInfo` 格式化，**禁止**硬编码 `"yyyy-MM-dd"` 不随语言
- **必须**：货币 / 百分比用 `CultureInfo` 文化感知格式，**禁止**统一字符串拼接
- **应该**：转换器（`IValueConverter`）传 `CultureInfo`（`Convert` 方法参数），**禁止**转换器内硬编码文化

## 7. 可访问性验证

- **必须**：关键界面用自动化工具验证（Accessibility Insights、Narrator 手测），**禁止**上线前不做无障碍检查
- **应该**：无障碍问题随缺陷跟踪（非"以后再说"），关键路径优先修复
- **禁止**：为视觉效果牺牲键盘 / 读屏可用性（装饰元素抢焦点 / 无名称）
