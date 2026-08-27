# WPF 开发规范

> 面向团队的全覆盖 WPF 桌面应用开发总纲。**版本中立**——不绑定特定 .NET / WPF 版本，适用于所有主流版本；覆盖 XAML、MVVM、绑定、渲染、线程、性能、测试与部署的 WPF 技术栈特有实践。

本领域负责 WPF/XAML、MVVM、绑定、控件、渲染、UI 线程和桌面部署等技术栈特有规则；通用 C# 语言与工程规范归 `knowledge-base/csharp/`，.NET Runtime、SDK、目标框架、Windows 兼容性与生命周期事实归 `knowledge-base/dotnet/`。本领域不复制通用平台支持矩阵。

## 文档目的

本规范统一团队 WPF 项目的架构选型、XAML 写法与工程实践，目标是让界面代码**可读、可维护、可扩展、可测**。它聚焦 WPF 技术栈特有的事项——XAML 语法、依赖属性、绑定机制、渲染模型、Dispatcher 线程模型等；通用 C# 层面的编码与设计原则，团队另有约定，不在本篇重复。

## 适用范围与读者

- **适用范围**：所有 WPF 代码库；新增代码、存量代码改造、Code Review 与 CI 门禁均适用
- **读者**：团队全部开发者。新人用于建立 WPF 基线，资深成员用于对齐架构与性能边界

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义。各篇正文使用对应措辞，级别决定违反后的处置：

| 级别 | 措辞 | 含义 | 违反处置 |
|---|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 | 视为缺陷，CI / review 拦截 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 | review 说明理由后可豁免 |
| **建议 MAY** | "可以"、"建议" | 可选做法，团队不强制 | 无 |

## 规范如何执行

规范不是纸面文档，通过以下手段落地：

1. **XAML 编译验证**：XAML 默认编译为 BAML（`x:Class` 编译期绑定类名），绑定路径错误虽不报编译错，但应启用设计期绑定诊断与运行期跟踪（见 `05` 章）
2. **静态分析门禁**：`.editorconfig` + Roslyn 分析器 + XAML 分析器（`04` 章），严重级别告警按 **warnings-as-errors** 处理
3. **CI 校验**：`restore → build(-warnaserror) → test` 三关（见 `01` 章）
4. **Code Review**：按团队 review 约定执行；代码层面问题由 `wpf-code-review` skill 辅助检出
5. **模板兜底**：新增项目 / 页面按 `02` 章布局约定与 `wpf-project-conventions` skill 生成

## 阅读路径

| 读者 | 必读 | 选读 |
|---|---|---|
| 新人（前两周） | `01` `02` `03` `04` | `05` `09` |
| 资深成员 | `08` `10` `09` `13` | 其余 |
| 全部成员 | 本文件、`03`、`04` | — |

## 文件地图

| 编号 | 文件 | 主题 |
|---|---|---|
| 00 | `00-README.md` | 总则、级别、执行、索引 |
| 01 | `rules/01-environment.md` | 环境与技术选型 |
| 02 | `rules/02-project-structure.md` | 项目结构与布局 |
| 03 | `rules/03-mvvm.md` | MVVM 架构 |
| 04 | `rules/04-xaml.md` | XAML 编写规范 |
| 05 | `rules/05-data-binding.md` | 数据绑定 |
| 06 | `rules/06-controls.md` | 控件体系 |
| 07 | `rules/07-resources-themes.md` | 资源、样式与主题 |
| 08 | `rules/08-layout-rendering.md` | 布局与渲染 |
| 09 | `rules/09-threading.md` | 线程与调度 |
| 10 | `rules/10-performance.md` | 性能优化 |
| 11 | `rules/11-testing.md` | 测试 |
| 12 | `rules/12-exceptions-crash.md` | 异常与崩溃 |
| 13 | `rules/13-security.md` | 安全 |
| 14 | `rules/14-accessibility-localization.md` | 可访问性与本地化 |
| 15 | `rules/15-packaging-deployment.md` | 打包与部署 |
| 16 | `rules/16-interactivity.md` | XAML Behaviors 与 Interactivity |
| 17 | `rules/17-common-libraries.md` | WPF 通用库选型 |

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。`reference/` 目录存放不带 MUST/SHOULD/MAY 语气的描述性知识（语法讲解、API 用法），与 `rules/` 下的规范文件是并列关系，不是从属关系——新增/修改任一类内容都需同步 `index.jsonl`，建议通过 `/knowledge-base-maintain` skill 完成。

## 更新与豁免

- 每篇文件头部记录本文件更新历史（日期 + 变更摘要），随变更提交
- 规范修订走 PR，review 通过后合入，并同步更新本文件的地图与阅读路径
- **豁免**：遇规范与场景冲突，在 PR 中显式注明"豁免原因"，由 reviewer 裁量；系统性豁免需求应推动规范修订，而非长期例外

## 与仓库已有 WPF 资产的关系

- `knowledge-base/dotnet/`：提供 WPF 项目运行环境、目标框架和 Windows/.NET 支持矩阵的背景参考

- `wpf-code-review` skill：本规范全篇是它的审查依据，其中 `10` 章性能原则对应其「性能专项诊断速查」章节，性能问题的诊断与修复操作以该 skill 为准
- `wpf-project-conventions` skill：`02` 章目录 / 资源 / 命名约定与它互为事实来源——它是生成侧的执行工具，本篇是原则侧
- `mastergo-to-wpf-components` / `mastergo-to-wpf-page`：设计稿转 WPF 的生成工具，生成结果须符合本规范 `04` `05` `07` 章约定
- `svg-to-xaml-path` / `mastergo-icon-expoter`：图标与矢量资源生成工具，产物遵循 `07` 章资源与 `06` 章图形约定

## 权威参考

- [WPF 文档（.NET Desktop）](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/overview/index)
- [WPF 开发指南](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/)
- [优化 WPF 应用程序性能](https://learn.microsoft.com/zh-cn/dotnet/desktop/wpf/advanced/optimizing-wpf-application-performance)
- [Windows 应用兼容性与 DPI 感知](https://learn.microsoft.com/zh-cn/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows)
