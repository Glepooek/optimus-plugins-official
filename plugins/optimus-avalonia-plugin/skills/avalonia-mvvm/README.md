# avalonia-mvvm

> 版本：1.0.0 | 分类：platform

Use when implementing the MVVM pattern in Avalonia, including ViewModels, INotifyPropertyChanged, ICommand, ReactiveUI, CommunityToolkit.Mvvm, or ViewModel-first navigation.

## 所处层级

```
┌─────────────┐
│★ platform    │  avalonia-mvvm（本 skill）
├─────────────┤
│             │  ↑ 由 avalonia（master 路由）按任务调度加载
└─────────────┘
```

本 skill 属 platform 层（Avalonia 平台专项参考），由 master 路由 `avalonia` 按 description 匹配调度，无产出依赖。

## 触发词 / 调用方式

用户进行 Avalonia 相关开发、需要本 skill 覆盖的知识域时触发；或由 `avalonia` master 路由内部调度。触发场景详见 SKILL.md 的 `description`。

## 业务逻辑流程图

```
Step 1  识别任务落在本 skill 知识域
   ↓
Step 2  加载本 skill 参考知识（API / 代码模式 / 常见错误）
   ↓
Step 3  将知识应用到代码编写 / 审查 / 迁移
```

## 产出物数据流

输入（Avalonia 开发任务 / 代码）→ 本 skill（参考知识）→ 正确、地道的 Avalonia 代码或结论 → 人工接手。

## Skill 依赖关系图

```
avalonia（master 路由）──调度──▶ ★ avalonia-mvvm
                                  │
                                  └── 无下游，独立使用
```
