---
max_turns: 12
runs: 1
allowed_tools: [Read, Glob, Grep, Skill]
---

我在 Ubuntu 22.04 x64 上，已经 `dotnet publish` 好一份自包含产物，放在 `~/publish/acme-desktop/`（含可执行文件 `Acme.Desktop`）。图标在 `~/publish/acme-desktop.png`。包名是 `acme-desktop`，版本 `2.4.0`，架构 `amd64`，maintainer 是 `Acme <support@acme.com>`，依赖 `libx11-6, libice6, libsm6, libfontconfig1`。`.desktop` 文件还没有，希望生成到 `~/publish/acme-desktop.desktop`。打包产物想放到 `~/dist/`。请帮我打成 `.deb` 并验证能装上、能跑起来。