---
max_turns: 12
runs: 1
allowed_tools: [Read, Glob, Grep, Skill]
---

我有一个 Avalonia .NET 8 桌面应用，项目是 `src/Acme.Desktop/Acme.Desktop.csproj`。我要在 Windows 开发机的 WSL Ubuntu 中打包给 Ubuntu 22.04 x64 用户，包名是 `acme-desktop`，版本 `2.4.0`，图标为 `src/Acme.Desktop/Assets/acme.png`。我们有 Avalonia Plus 和可用的 Parcel CLI 许可证。请给我一个可执行的发布计划，并说明打包后怎么验证和发布。