---
max_turns: 12
runs: 1
allowed_tools: [Read, Glob, Grep, Skill]
---

我的 Avalonia .NET 8 应用需要发给 Debian 12 arm64 用户。项目没有 Avalonia Plus，因此不能使用 Parcel CLI。请说明怎样在 Linux CI 中生成包名为 `field-console`、版本 `1.8.1` 的 `.deb`，以及需要提交什么打包文件、如何处理依赖并怎样做最小但可信的安装验收。