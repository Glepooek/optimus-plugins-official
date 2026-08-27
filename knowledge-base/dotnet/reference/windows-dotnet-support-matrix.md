# Windows 7/10/11 各版本 .NET Framework 与 .NET（5+）支持情况调研报告

> 类型：reference
>
> 适用范围：Windows 客户端与 .NET Framework / .NET 5+ 的兼容性和生命周期
>
> 状态：调研资料整理稿，涉及具体版本和日期的内容须以 Microsoft 官方页面复核为准
>
> 最近审阅：2026-08-27

**核心结论：**

**.NET Framework**：Win7 SP1 最高 4.8（不支持 4.8.1）；Win10 20H2+ / Win11 全系列支持 4.8.1。4.x 为就地更新，同系统仅存一个版本。

**.NET（5+）**：Win7 SP1（需 ESU）最高 .NET 6；Win10 1607+ / Win11 21H2+ 最高可装 .NET 10。.NET 为 side-by-side 安装，可同时存在多个版本。

**注意**：Win10 1507/1511 不支持任何 .NET 5+；.NET 7 起不再支持所有 Win7 版本（含 RTM/SP1）及 Win8.1。

# 核心概念说明

本报告同时覆盖两条独立的 .NET 产品线，二者机制不同，需分开理解：

## .NET Framework（Windows 专属）

- **平台**：仅 Windows，作为 Windows 组件或独立安装包分发。
- **4.x 就地更新**：从 4.0 到 4.8.1，同系统只能存在一个 4.x 版本，高版本替换低版本，不能降级。
- **3.5 SP1 可并存**：3.5 运行时独立于 4.x，可同时安装，用于运行 1.0~3.5 的旧应用。
- **支持策略**：跟随 Windows 生命周期，Windows 终止支持则 .NET Framework 不再收到更新。

## .NET（5+，跨平台，原称 .NET Core）

- **平台**：跨平台（Windows / Linux / macOS / ARM），完全开源（MIT 协议）。
- **Side-by-side 安装**：可在同一台机器上同时安装多个 .NET 版本（如 .NET 6、.NET 8、.NET 10 并存），互不影响。
- **命名演变**：.NET Core 1.0~3.1 → 从 .NET 5 起去掉 "Core" 直接叫 .NET，版本号跳过 4 以避免与 .NET Framework 4.x 混淆。
- **支持策略**：独立生命周期，偶数版本为 LTS（3年支持），奇数版本为 STS（18个月支持）。
- **当前最新**：.NET 10（2025.11 发布，LTS，支持至 2028.11）。

# 第一部分：.NET Framework 支持情况

## Windows 7

### Windows 7 RTM（无 SP1）

|维度|详情|
|---|---|
|预装 .NET|3.5.1（含 2.0 SP2 / 3.0 SP2 / 3.5 SP1）|
|可安装 4.x 最低|.NET Framework 4.0|
|可安装 4.x 最高|.NET Framework 4.0|
|能否装 4.5+|不能，安装时被阻止，提示需要 Windows 7 SP1|
|支持 4.8.1|不支持|

### Windows 7 SP1（各 SKU 版本一致）

|维度|详情|
|---|---|
|预装 .NET|3.5.1（含 2.0 SP2 / 3.0 SP2 / 3.5 SP1）|
|可安装 4.x 最低|.NET Framework 4.0|
|可安装 4.x 最高|**.NET Framework 4.8**|
|支持 4.8.1|不支持|

完整 4.x 序列：4.0 → 4.5 → 4.5.1 → 4.5.2 → 4.6 → 4.6.1 → 4.6.2 → 4.7 → 4.7.1 → 4.7.2 → **4.8**

**安装 4.8 的额外前提**：需先安装 SHA-2 代码签名支持更新（KB4474419），否则无法识别 4.8 安装包。

## Windows 10 各版本

|版本|发布时间|预装（=最低）|最高可升级|支持 4.8.1|
|---|---|---|---|---|
|1507|2015.07|4.6|4.6.2|否|
|1511|2015.11|4.6.1|4.6.2|否|
|1607|2016.08|4.6.2|4.8|否|
|1703|2017.04|4.7|4.8|否|
|1709|2017.10|4.7.1|4.8|否|
|1803|2018.04|4.7.2|4.8|否|
|1809|2018.10|4.7.2|4.8|否|
|1903|2019.05|4.8|4.8|否|
|1909|2019.11|4.8|4.8|否|
|2004|2020.05|4.8|4.8|否|
|20H2|2020.10|4.8|**4.8.1**|是|
|21H1|2021.05|4.8|**4.8.1**|是|
|21H2|2021.11|4.8|**4.8.1**|是|
|22H2|2022.10|4.8|**4.8.1**|是|

来源：Microsoft Learn - .NET Framework system requirements

## Windows 11 各版本

|版本|发布时间|预装|最高可升级|支持 4.8.1|
|---|---|---|---|---|
|21H2|2021.10|4.8|**4.8.1**|是（手动安装）|
|22H2|2022.09|**4.8.1**|4.8.1|是（已预装）|
|23H2|2023.10|**4.8.1**|4.8.1|是（已预装）|
|24H2|2024.10|**4.8.1**|4.8.1|是（已预装）|
|25H2|2025.09|**4.8.1**|4.8.1|是（已预装）|

来源：Microsoft Learn - Install .NET Framework on Windows and Windows Server

# 第二部分：.NET（5+）支持情况

## .NET 各版本概览

|版本|发布日期|类型|支持结束|最低 Windows 系统要求|
|---|---|---|---|---|
|.NET 5|2020.11|STS|2022.05.10|Win7 SP1、Win8.1、Win10 1607+、Win11 21H2+|
|.NET 6|2021.11|LTS|2024.11.12|Win7 SP1 ESU、Win8.1、Win10 1607+、Win11 21H2+|
|.NET 7|2022.11|STS|2024.05.15|Win10 1607+、Win11 21H2+（不再支持所有 Win7 版本（含 RTM/SP1）及 Win8.1）|
|.NET 8|2023.11|LTS|2026.11.10|Win10 21H2+ / 1809 LTSC / 1607 LTSC-Ent、Win11 21H2+|
|.NET 9|2024.11|STS|2026.11.10|Win10 21H2+ / 1809 LTSC / 1607 LTSC-Ent、Win11 21H2+|
|**.NET 10**|**2025.11**|**LTS**|**2028.11.14**|Win10 21H2+ / 1809 LTSC / 1607 LTSC-Ent、Win11 21H2+|

来源：Microsoft Learn - Install .NET on Windows / .NET Support Policy

**关键说明：**

- **LTS**（Long Term Support）：长期支持，3年安全更新；**STS**（Standard Term Support）：标准支持，18个月安全更新。
- .NET 采用 **side-by-side** 安装，同一台机器可同时安装多个 .NET 版本（如 .NET 6 + .NET 8 + .NET 10 并存），应用程序可指定使用哪个版本。
- .NET 8/9/10 官方文档中 Win10 仅列出 "21H2、1809 LTSC、1607 LTSC/Enterprise"，是因为其他版本（1903~21H1）已终止 Windows 支持；技术上这些版本仍可安装 .NET 8/9/10，但微软不提供官方支持。

## Windows 7 SP1 上的 .NET（5+）支持

|维度|详情|
|---|---|
|可安装 .NET 最低|.NET 5|
|可安装 .NET 最高|**.NET 6**|
|.NET 7+ 支持|不支持（.NET 7 起移除了对所有 Win7 版本（含 RTM/SP1）及 Win8.1 的支持）|
|前提条件|必须是 Win7 SP1 且安装 ESU（扩展安全更新）；需额外安装 VC++ 2015-2019 Redistributable、KB3063858 等依赖|

**重要提示**：.NET 5 和 .NET 6 均已终止支持（分别于 2022.05 和 2024.11），在 Win7 SP1 上运行 .NET 应用存在安全风险。微软官方建议迁移到 Windows 10/11 + 受支持的 .NET 版本。

## Windows 10 各版本上的 .NET（5+）支持

|Win10 版本|.NET 最低|.NET 最高|说明|
|---|---|---|---|
|1507|—|—|不支持任何 .NET 5+（最低要求 1607）|
|1511|—|—|不支持任何 .NET 5+（最低要求 1607）|
|1607 LTSC/Ent|.NET 5|**.NET 10**|LTSC/Enterprise 版本仍在支持期内，全版本支持|
|1607 普通版|.NET 5|.NET 6|普通版已终止支持，.NET 7+ 不官方支持（技术上可装）|
|1703/1709/1803|.NET 5|.NET 6|已终止 Windows 支持，.NET 7+ 不官方支持|
|1809 LTSC/Ent|.NET 5|**.NET 10**|LTSC/Enterprise 版本仍在支持期内，全版本支持|
|1809 普通版|.NET 5|.NET 7|普通版已终止支持，.NET 8+ 不官方支持|
|1903/1909/2004|.NET 5|.NET 7|已终止 Windows 支持，.NET 8+ 不官方支持|
|20H2/21H1|.NET 5|.NET 7|已终止 Windows 支持，.NET 8+ 不官方支持|
|21H2|.NET 5|**.NET 10**|Win10 最终版本（Enterprise/Education 至 2028.10），全版本支持|
|22H2|.NET 5|**.NET 10**|Win10 最终版本，全版本支持（Home/Pro 至 2025.10 已终止）|

来源：Microsoft Learn - Install .NET on Windows / Windows 生命周期

**说明**：表中“.NET 最高”指**微软官方支持**的最高版本。由于 .NET 是 side-by-side 安装，技术上在满足最低系统要求的 Win10 版本上可安装任何 .NET 版本，但若 Windows 版本本身已终止支持，微软不为该组合提供安全更新和技术支持。

## Windows 11 各版本上的 .NET（5+）支持

|Win11 版本|.NET 最低|.NET 最高|说明|
|---|---|---|---|
|21H2|.NET 5|**.NET 10**|Win11 初始版本，.NET 5 在后续更新中加入对 Win11 的支持|
|22H2|.NET 5|**.NET 10**|全版本支持（Home/Pro 已终止，Ent/Edu 至 2025.10）|
|23H2|.NET 7|**.NET 10**|.NET 5/6 已终止支持但技术上可安装（Home/Pro 已终止，Ent/Edu 至 2026.11）|
|24H2|.NET 8|**.NET 10**|当前主流版本，全版本支持（Home/Pro 至 2026.10）|
|25H2|.NET 9|**.NET 10**|最新版本，全版本支持（Home/Pro 至 2027.10）|
|26H1|.NET 10|**.NET 10**|预览版本，.NET 10 为首个官方支持的版本|

来源：Microsoft Learn - Install .NET on Windows / Windows 11 生命周期

**说明**：表中“.NET 最低”指该 Win11 版本发布时官方推荐的最低 .NET 版本。由于 .NET 是 side-by-side 安装且 Win11 21H2+ 均满足所有 .NET 版本的最低系统要求，技术上可在任何 Win11 21H2+ 版本上安装 .NET 5~10 任意版本。

# 双平台汇总速查表

以下表格按 Windows 版本汇总 .NET Framework 和 .NET（5+）的最高支持版本，便于快速查阅。

|Windows 版本|预装 .NET Framework|.NET Framework 最高|.NET（5+）最低|.NET（5+）最高|
|---|---|---|---|---|
|Win7 RTM|3.5.1|4.0|—|不支持|
|Win7 SP1|3.5.1|**4.8**|.NET 5|**.NET 6**|
|Win10 1507/1511|4.6 / 4.6.1|4.6.2|—|不支持|
|Win10 1607 LTSC/Ent|4.6.2|4.8|.NET 5|**.NET 10**|
|Win10 1703~1809|4.7~4.7.2|4.8|.NET 5|.NET 6/7*|
|Win10 1903~21H1|4.8|4.8|.NET 5|.NET 7*|
|Win10 21H2/22H2|4.8|**4.8.1**|.NET 5|**.NET 10**|
|Win11 21H2|4.8|**4.8.1**|.NET 5|**.NET 10**|
|Win11 22H2+|**4.8.1**|4.8.1|.NET 5|**.NET 10**|

* 标注 * 的版本因 Windows 本身已终止支持，.NET 更高版本技术上可安装但不被微软官方支持

# 支持生命周期与关键时间节点

## .NET Framework 支持生命周期

|版本|支持结束|说明|
|---|---|---|
|3.5 SP1|2029.01.09|独立于 4.x 的运行时，仅运行时受支持|
|4.6.2|2027.01.12|有独立支持结束日期|
|4.7 / 4.7.1 / 4.7.2|跟随父 OS|作为 Windows 组件随系统更新|
|4.8 / 4.8.1|跟随父 OS|4.8.1 为最终版本，后续仅安全修复|

## .NET（5+）支持生命周期

|版本|发布日期|类型|支持结束|状态|
|---|---|---|---|---|
|.NET 5|2020.11|STS|2022.05.10|已终止|
|.NET 6|2021.11|LTS|2024.11.12|已终止|
|.NET 7|2022.11|STS|2024.05.15|已终止|
|.NET 8|2023.11|LTS|2026.11.10|维护中|
|.NET 9|2024.11|STS|2026.11.10|维护中|
|**.NET 10**|**2025.11**|**LTS**|**2028.11.14**|当前推荐|

来源：Microsoft .NET Support Policy / Microsoft Lifecycle

## Windows 客户端支持生命周期

|Windows 版本|Home/Pro 结束|说明|
|---|---|---|
|Win7 SP1|2020.01.14|扩展支持结束，ESU 也已终止|
|Win10 22H2|2025.10.14|Win10 最终版本，全版本同日终止|
|Win11 21H2|2023.10.10|Ent/Edu 延至 2024.10|
|Win11 22H2|2024.10.08|Ent/Edu 延至 2025.10|
|Win11 23H2|2025.11.11|Ent/Edu 延至 2026.11.10|
|Win11 24H2|2026.10.13|Ent/Edu 延至 2027.10.12|
|Win11 25H2|2027.10.12|Ent/Edu 延至 2028.10.10|

# 依据来源

1. **.NET Framework 系统要求**（Microsoft Learn）— 各 Windows 版本预装与可安装的 .NET Framework 版本对照表。
	[https://learn.microsoft.com/en-us/dotnet/framework/get-started/system-requirements](https://learn.microsoft.com/en-us/dotnet/framework/get-started/system-requirements)
2. **在 Windows 和 Windows Server 上安装 .NET Framework**（Microsoft Learn）— 按 Win11/Win10/旧版 Windows 分节的预装与最高支持版本。
	[https://learn.microsoft.com/en-us/dotnet/framework/install/on-windows-and-server](https://learn.microsoft.com/en-us/dotnet/framework/install/on-windows-and-server)
3. **在 Windows 上安装 .NET**（Microsoft Learn）— .NET 8/9/10 支持的 Windows 版本、架构、前置依赖。
	[https://learn.microsoft.com/en-us/dotnet/core/install/windows](https://learn.microsoft.com/en-us/dotnet/core/install/windows)
4. **.NET 5 支持的操作系统版本**（GitHub dotnet/core）— .NET 5 官方支持的 OS 列表，含 Win7 SP1、Win10 1607+。
	[https://github.com/dotnet/core/blob/main/release-notes/5.0/5.0-supported-os.md](https://github.com/dotnet/core/blob/main/release-notes/5.0/5.0-supported-os.md)
5. **.NET 支持策略**（Microsoft .NET）— 各 .NET 版本的发布类型（LTS/STS）、支持结束日期、当前状态。
	[https://dotnet.microsoft.com/en-us/platform/support/policy](https://dotnet.microsoft.com/en-us/platform/support/policy)
6. **Microsoft .NET and .NET Core 生命周期**（Microsoft Learn）— 各 .NET 版本的开始与结束支持日期。
	[https://learn.microsoft.com/en-us/lifecycle/products/microsoft-net-and-net-core](https://learn.microsoft.com/en-us/lifecycle/products/microsoft-net-and-net-core)
7. **Windows 11 Home and Pro 生命周期**（Microsoft Learn）— Win11 各版本支持结束日期。
	[https://learn.microsoft.com/en-us/lifecycle/products/windows-11-home-and-pro](https://learn.microsoft.com/en-us/lifecycle/products/windows-11-home-and-pro)
8. **.NET Framework 安装受阻疑难解答**（Microsoft Learn）— Win7 RTM 上安装 4.5+ 失败的原因（需先升级 SP1）。
	[https://learn.microsoft.com/en-us/dotnet/framework/install/troubleshoot-blocked-installations-and-uninstallations](https://learn.microsoft.com/en-us/dotnet/framework/install/troubleshoot-blocked-installations-and-uninstallations)

> 部分内容来自原始调研报告，正式使用前应逐项复核官方来源。本 reference 不替代官方生命周期和安装要求页面；若官方页面更新，应优先修订本文件的矩阵、日期、适用范围和结论。
