# WPF 应用程序 CPU 架构支持情况调研报告（.NET Framework / .NET）

> 类型：reference
>
> 适用范围：WPF / WinForms 桌面应用在 x86、x64、ARM32、ARM64 四种 CPU 架构上的可用性判断
>
> 状态：调研资料整理稿（部分内容由 AI 生成），涉及具体版本和日期的内容须以 Microsoft 官方页面复核为准
>
> 最近审阅：2026-09-03
>
> 相关：本文件按 **CPU 架构轴**组织；按 **Windows 版本轴**判断能装哪个 .NET 见 `windows-dotnet-support-matrix.md`。两份矩阵维度互补，判断「某台设备能不能跑这个 WPF 应用」时通常需同时查阅。

**核心结论：**

**.NET Framework**：4.8 及更早版本仅支持 x86/x64；**4.8.1 首次支持原生 ARM64**（含 WPF），但仅限 Windows 11+。从未支持 ARM32。

**.NET 5**：5.0.0~5.0.7 的 ARM64 SDK 不含 WPF；**5.0.8（2021.07）起首次支持 WPF on ARM64**。

**.NET 6+**：完整支持 x86、x64、ARM64，.NET 7 起 ARM64 性能追平 x64。

**ARM32**：WPF 从未支持 ARM32。

# 一、总览速查表

## .NET Framework

|版本|x86|x64|ARM32|ARM64|关键说明|
|---|---|---|---|---|---|
|3.0 ~ 3.5 SP1|✅|✅|❌|❌|仅 x86/x64|
|4.0 ~ 4.7.2|✅|✅|❌|❌|仅 x86/x64|
|4.8|✅|✅|❌|❌|仅 x86/x64|
|**4.8.1**|✅|✅|❌|**✅**|**首个支持原生 ARM64 的 .NET Framework 版本**（含 WPF/WinForms），仅限 Windows 11+|

## .NET（5+）

|版本|x86|x64|ARM32|ARM64|关键说明|
|---|---|---|---|---|---|
|.NET 5.0.0 ~ 5.0.7|✅|✅|❌|⚠️|SDK 支持 ARM64，但 **WPF 不包含在 ARM64 中**|
|**.NET 5.0.8+**|✅|✅|❌|**✅**|2021.07 起，ARM64 首次包含 WPF/WinForms|
|.NET 6|✅|✅|❌|✅|完整支持 WPF on ARM64|
|.NET 7|✅|✅|❌|✅|ARM64 功能与性能和 x64 持平|
|.NET 8|✅|✅|❌|✅|微软推荐用于原生 ARM64 执行|
|.NET 9|✅|✅|❌|✅|完整支持|
|.NET 10|✅|✅|❌|✅|完整支持|

✅ = 原生支持　⚠️ = 部分支持（运行时支持但 WPF 不可用）　❌ = 不支持

# 二、详细说明

## 1. .NET Framework 的 ARM64 支持（4.8.1）

- **.NET Framework 4.8.1** 于 2022 年 8 月发布，是 .NET Framework 家族中**首个支持原生 ARM64 的版本**，包含 WPF 和 WinForms 两个 UI 平台。
- ARM64 原生支持**仅限 Windows 11 及以上**。虽然 4.8.1 可安装在 Windows 10 20H2+ 上，但在 Win10 ARM64 设备上不提供原生 ARM64 运行时。
- 4.8.1 之前的所有 .NET Framework 版本（4.8 及更早）**完全不支持 ARM64**，在 ARM64 Windows 上只能通过 x64 模拟运行。
- 已知限制：.NET Framework 4.x WCF 可选组件在 Windows 11 ARM64 客户端上无法启用（MSMQ Activation 因 ARM64 上无 MSMQ 而保持禁用）。

## 2. .NET 5 的 WPF on ARM64 转折点

**背景**：.NET Core 3.0/3.1 时代 WPF 首次引入 .NET Core 平台，但 Windows Desktop Runtime 仅提供 x86/x64，不支持任何 ARM 架构。

- **.NET 5.0.0 ~ 5.0.7**（2020.11 ~ 2021.06）：SDK 已支持 Windows ARM64，但 **ARM64 SDK 中不包含 WinForms 和 WPF**，只能运行控制台、ASP.NET Core 等非桌面应用。
- **.NET 5.0.8（2021 年 7 月 13 日）** 是关键转折点：微软在该版本的 Windows ARM64 SDK 中**首次加入了 WinForms 和 WPF**，从此 WPF 应用可以原生运行在 Windows ARM64 设备上。
- 从 5.0.8 起，.NET 5 Desktop Runtime 提供 `x64 | x86 | Arm64` 三种安装包。
- 发布方式：在 x64 开发机上 targeting ARM64 时，使用 `dotnet publish -r win-arm64` 即可生成原生 ARM64 应用（支持 framework-dependent 和 self-contained 两种部署模式）。

## 3. .NET 6 及以后的成熟支持

- **.NET 6**：WPF on ARM64 进入稳定支持阶段，ARM 官方学习路径明确推荐使用 .NET 6 构建原生 Windows on ARM WPF 应用，发布时指定 `-r win-arm64` 即可。
- **.NET 7**：ARM64 的功能完整度和性能达到与 x64 持平的水平。
- **.NET 8/9/10**：持续完整支持 x86、x64、ARM64 三种架构，微软官方推荐 .NET 8+ 用于原生 ARM64 开发，并配合 ARM 原生 Visual Studio 2022 17.4+。
- .NET 6+ 的 Windows Desktop Runtime 下载均提供 `x86 | x64 | Arm64` 三种架构。

## 4. ARM32 支持情况

- **WPF 从未支持 ARM32**。
- .NET Core 2.1/2.2/3.0/3.1 的基础运行时曾支持 Windows ARM32（用于 IoT 场景），但 Windows Desktop Runtime（WPF）始终不提供 ARM32 版本。
- .NET 5 起，微软不再提供 Windows ARM32 的运行时支持，全面转向 ARM64。

## 5. x86/x64 应用在 ARM64 Windows 上的模拟运行

- Windows 11 内置了对 x86 和 x64 应用的模拟能力，因此**旧的 .NET Framework WPF 应用（编译为 x86/x64）可以在 ARM64 Windows 11 上通过模拟运行**，无需重新编译。
- 但模拟运行存在性能损耗和潜在兼容性问题，微软建议对于需要在 ARM64 设备上运行的 WPF 应用，应升级到 .NET 6+（或 .NET Framework 4.8.1）并编译为原生 ARM64 以获得最佳性能和电池续航。
- Windows 10 ARM64 仅支持 x86 模拟，不支持 x64 模拟；Windows 11 开始同时支持 x86 和 x64 模拟。

# 三、关键时间线

|时间|事件|
|---|---|
|2006 ~ 2019|.NET Framework 3.0~4.8：WPF 仅支持 x86/x64|
|2019.09|.NET Core 3.0：WPF 首次引入 .NET Core，仍仅 x86/x64|
|2020.11|.NET 5 发布：SDK 支持 ARM64，但 WPF 不含在内|
|**2021.07**|**.NET 5.0.8：WPF 首次支持 Windows ARM64**|
|2021.11|.NET 6：WPF on ARM64 稳定成熟|
|**2022.08**|**.NET Framework 4.8.1：.NET Framework 首次支持原生 ARM64（含 WPF）**|
|2022.11+|.NET 7/8/9/10：持续完善 ARM64 支持，性能追平 x64|

# 四、依据来源

1. **Announcing .NET Framework 4.8.1**（Microsoft DevBlogs）— 4.8.1 原生 ARM64 支持、支持的 Windows 版本、WPF/WinForms 包含情况、已知问题。
	[https://devblogs.microsoft.com/dotnet/announcing-dotnet-framework-481/](https://devblogs.microsoft.com/dotnet/announcing-dotnet-framework-481/)
2. **.NET July 2021 Updates – 5.0.8 and 3.1.17**（Microsoft DevBlogs）— .NET 5.0.8 首次在 ARM64 SDK 中包含 WinForms 和 WPF。
	[https://devblogs.microsoft.com/dotnet/net-july-2021/](https://devblogs.microsoft.com/dotnet/net-july-2021/)
3. **Announcing .NET Core 3.0**（Microsoft DevBlogs）— .NET Core 3.0 引入 WPF、ARM 支持范围。
	[https://devblogs.microsoft.com/dotnet/announcing-net-core-3-0/](https://devblogs.microsoft.com/dotnet/announcing-net-core-3-0/)
4. **.NET Core 3.1 - Supported OS versions**（GitHub dotnet/core）— .NET Core 3.1 各 OS 支持的架构列表，Windows 10 仅 x64/x86。
	[https://github.com/dotnet/core/blob/main/release-notes/3.1/3.1-supported-os.md](https://github.com/dotnet/core/blob/main/release-notes/3.1/3.1-supported-os.md)
5. **Download .NET 5.0**（Microsoft .NET）— .NET 5 Desktop Runtime 提供 x64/x86/Arm64 三种安装包。
	[https://dotnet.microsoft.com/en-us/download/dotnet/5.0](https://dotnet.microsoft.com/en-us/download/dotnet/5.0)
6. **Build a native windows application using .NET 6 framework for Windows on Arm**（Arm Learning Paths）— .NET 6 WPF on ARM64 开发指南，使用 win-arm64 RID 发布。
	[https://learn.arm.com/learning-paths/laptops-and-desktops/win_net/win_net/](https://learn.arm.com/learning-paths/laptops-and-desktops/win_net/win_net/)
7. **Windows on Arm 概述**（Microsoft Learn）— ARM64 设备上 x86/x64 模拟、.NET 8+ 原生 ARM64 推荐、.NET Framework WPF 应用可模拟运行。
	[https://learn.microsoft.com/en-ca/windows/arm/overview](https://learn.microsoft.com/en-ca/windows/arm/overview)
8. **Add Arm support to your Windows app**（Microsoft Learn）— 添加 ARM 原生支持的指南，性能与电池续航优势。
	[https://learn.microsoft.com/nb-no/windows/arm/add-arm-support](https://learn.microsoft.com/nb-no/windows/arm/add-arm-support)
9. **.NET 4.8.1 on M2 and Windows 11 ARM**（GitHub microsoft/dotnet）— 早期版本 .NET Framework 不支持 ARM64，需使用 4.8.x。
	[https://github.com/microsoft/dotnet/issues/1369](https://github.com/microsoft/dotnet/issues/1369)
10. **Windows on Arm（Linaro Connect 2023）**— Arm64 .NET Framework 4.8.1 含 WinForms+WPF、.NET 6 含 WPF+WinForms、.NET 7 功能与性能和 x64 持平。
	[https://hosted-files.sched.co/linaroconnect2023/3a/Linaro%20Connect%202023%20-%20WIndows%20on%20Arm.pdf](https://hosted-files.sched.co/linaroconnect2023/3a/Linaro%20Connect%202023%20-%20WIndows%20on%20Arm.pdf)

> 部分内容由 AI 生成，正式使用前应逐项复核官方来源。本 reference 不替代官方架构支持与安装要求页面；若官方页面更新，应优先修订本文件的矩阵、日期、适用范围和结论。
