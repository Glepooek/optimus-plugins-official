# 01 · 环境与技术选型

> 更新历史：2026-08-21 创建。

**版本中立声明**：本规范不绑定具体 .NET / WPF 版本。目标框架与 SDK 由团队在仓库级统一决策，规范只约定"如何一致"，不约定"用哪一版"。版本升级与迁移以官方升级指南为准。

## 1. 目标框架策略

- **必须**：全仓库统一 `TargetFramework`（WPF 必含 `-windows` 后缀，如 `net8.0-windows`），主版本由团队决策，并用 `global.json` / `Directory.Build.props` 固化
- **必须**：优先选择当前处于支持期的 LTS 版本；WPF 的修复与安全更新只在支持期内提供
- **必须**：目标框架含 `-windows` 后缀（`netX.Y-windows`），纯 `netX.Y` 无法启用 WPF 与 Windows 桌面 API
- **应该**：多项目仓库通过 `Directory.Build.props` 集中声明目标框架，避免逐项目手写
- **禁止**：同一解决方案内混用不兼容的目标框架（除非有明确理由并在代码中注释）

## 2. SDK 与工具链

- **必须**：用 `global.json` 固定 SDK 主版本，保证本地与 CI 一致
- **必须**：SDK 安装 Windows Desktop workload（WPF 项目依赖），CI 用 `dotnet workload install desktop` 或带 Desktop 的镜像
- **应该**：统一 IDE 与编辑器配置（`.editorconfig` + `.vscode` / Visual Studio 共享设置），编辑器的差异不改变产出物
- **应该**：启用 XAML 设计器与 XAML 编译（BAML）的默认校验，设计期错误不拖到运行期

## 3. WPF 项目基础配置

新 WPF 项目必须开启以下属性（`Directory.Build.props` 或项目内）：

```xml
<TargetFramework>net8.0-windows</TargetFramework>  <!-- 由团队统一决策，见第 1 节 -->
<UseWPF>true</UseWPF>                              <!-- 启用 WPF 引用与 XAML 编译 -->
<Nullable>enable</Nullable>                        <!-- 可空分析 -->
<ImplicitUsings>enable</ImplicitUsings>
<AnalysisLevel>latest</AnalysisLevel>
<TreatWarningsAsErrors>true</TreatWarningsAsErrors>
```

- **必须**：`UseWPF` 为 `true`；同时想用 WinForms 控件（`WindowsFormsHost`）时再开 `UseWindowsForms`，**禁止**为不用 WinForms 而开它
- **必须**：开启 `Nullable`，XAML 绑定目标属性缺失会得到编译期告警，不关闭可空分析
- **禁止**：`EnableDefaultItems` 关闭导致的 XAML 文件不自动编译（XAML 默认作为 `Page` 项编译进 BAML）

```xml
<!-- ❌ 不必要地引入 WinForms 引用：只为看个零头功能，拖入整个 WinForms 程序集 -->
<PropertyGroup>
  <UseWPF>true</UseWPF>
  <UseWindowsForms>true</UseWindowsForms>   <!-- 但项目根本没用到 WinForms 控件 -->
</PropertyGroup>

<!-- ✅ 只用 WPF 就不开 WinForms；确实要用 WindowsFormsHost 时才开 -->
<PropertyGroup>
  <UseWPF>true</UseWPF>
</PropertyGroup>
```

```xml
<!-- ❌ 关闭默认项导致 XAML 不编译：Build 通过但资源不生效，运行期才暴露 -->
<PropertyGroup>
  <EnableDefaultItems>false</EnableDefaultItems>   <!-- 连锁关闭 XAML 自动编入 Page -->
</PropertyGroup>

<!-- ✅ 保持默认项开启：XAML 自动作为 Page 编译进 BAML -->
<!-- EnableDefaultItems=false 时须手动补 <Page Include="*.xaml"/> 才能恢复 -->
```

## 4. WPF 特性可用性判断（"三问"）

引入某个 WPF 版本特性前，用三问决策（团队统一口径）：

1. 团队当前目标框架是否包含该特性？
2. 编译器 / XAML 编译器是否支持该语法？
3. 该特性是否显著提升可读性或正确性，值得引入？

三问全"是"才引入；否则降级到当前版本可用写法。**禁止**为目标框架不支持的特性打补丁式 workaround——应更新框架或放弃该特性。

## 5. 平台差异与兼容性

- **必须**：WPF 依赖 Windows 桌面平台，不适用于跨平台目标；需跨平台时另行评估（如 Avalonia / Uno），不在 WPF 项目内做平台抽象
- **应该**：明确支持的最低 Windows 版本（如 Win10 1809 / Win11），据此决定可用的 WPF 与系统 API（联动 `08` 章 DPI 与 `15` 章部署）
- **禁止**：不经确认直接调用高版本 Windows API（会抛异常或降级），涉及系统能力时先查目标系统支持情况

## 6. 依赖管理与包源

- **必须**：第三方包（MVVM 框架、控件库）版本统一管理，不各自为政（包管理约定见团队统一策略）
- **必须**：控件库 / 主题库与目标框架版本兼容性核对，升级框架时同步升级控件库
- **应该**：控件库引入前评估包体积与启动开销（重控件库影响冷启动，联动 `10` 章）

## 7. 构建与 CI

- **必须**：CI 顺序执行 `dotnet restore` → `dotnet build -warnaserror` → `dotnet test`
- **必须**：CI 使用与 `global.json` 一致的 SDK，并安装 Desktop workload；构建必须可复现
- **应该**：CI 缓存 NuGet 包与 workload，缩短还原时间
- **应该**：构建产物（`bin` / `obj`）不入库，由 `.gitignore` 统一排除
- **禁止**：CI 使用私有 / 本地独有的机器依赖（XAML 编译不依赖本地设计器）
