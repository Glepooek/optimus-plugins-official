---
name: test-locally
description: 修改本仓库任何 skill / hook / command 后，用 --plugin-dir 加载本仓库进行本地测试。触发词："本地测试"、"测试这个 skill"、"加载插件测试"。
---

# 本地测试

修改任何 skill / hook / command 后，用 `--plugin-dir` 加载本仓库进行测试：

```bash
# 加载本仓库所有插件（推荐用于完整测试，需在仓库根目录执行）
claude --plugin-dir .

# 也可以只加载单个插件目录
claude --plugin-dir ./plugins/optimus-devops-plugin
```

启动新会话后，直接输入触发词验证行为（无需重启、无需重新安装）。文件改动立即生效。
