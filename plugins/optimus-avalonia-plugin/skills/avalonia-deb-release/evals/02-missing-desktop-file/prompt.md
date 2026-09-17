---
max_turns: 12
runs: 1
allowed_tools: [Read, Glob, Grep, Skill]
---

我在 Debian 12 arm64 上，有一份自包含发布产物在 `/opt/build/field-console/`（可执行文件 `FieldConsole`），图标在 `/opt/build/icon.png`。包名 `field-console`，版本 `1.8.1`，maintainer `Field Team <field@acme.com>`。`.desktop` 文件还没有，希望生成到 `/opt/build/field-console.desktop`，我也不清楚需要哪些系统依赖。产物想输出到 `/opt/dist/`。帮我打包并装上验证。