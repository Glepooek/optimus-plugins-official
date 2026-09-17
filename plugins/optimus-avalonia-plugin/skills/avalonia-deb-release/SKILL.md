---
name: avalonia-deb-release
description: Use when packaging an already-published Avalonia Linux build into a `.deb` with `dpkg-deb`, or validating that package via command-line/GUI install. 触发词："Avalonia Linux 打包"、"打 deb"、"Ubuntu 安装包"、"dpkg-deb"。
license: MIT
compatibility: 当前环境需已是 Linux（或 WSL2 Debian/Ubuntu），需已安装或可安装 `dpkg-deb`；图形安装验收需要图形桌面会话，无图形会话时该项验收会如实标注未覆盖。
metadata:
  version: "2.0.1"
  author: desktop client team
  category: workflow
allowed-tools: Read Write Bash Glob Grep
---

# Avalonia Debian 打包

把已经发布好的 Avalonia Linux 产物打成可安装的 `.deb` 包，并完成命令行与图形界面两种安装验收。不负责 `dotnet publish`、Parcel 自动化、发布策略选择或对外发布——待打包产物由用户提供，本 skill 只管"从产物到能装上并跑起来"这一段。

## 需求预告

首次响应时一次性收集缺失信息：包名、版本号、目标架构（如 `amd64`/`arm64`）、maintainer、`Depends` 依赖列表、**待打包产物目录**（已发布好的可执行文件所在目录）、**图标文件路径**（可选，没有则跳过）、**`.desktop` 文件落盘路径**（该文件由本 skill 按模板生成，用户只需给出目标路径，需用户确认字段）、**产出目录**。已有信息不得重复询问。

`dpkg-deb` 是否已安装属依赖检查项，不计入本环节缺失项判断，由 Step 1 实际检测。

## Step 1：确认 Linux 环境与 dpkg-deb

```bash
uname -s            # 应为 Linux
dpkg-deb --version  # 必须可执行
```

`dpkg-deb` 缺失时提示安装命令（如 `sudo apt-get install -y dpkg-dev`）后终止——不擅自执行系统级安装，由用户自行决定并执行。在 Windows 原生环境（非 WSL）下直接终止，说明需切换到 Linux 或 WSL2 Debian/Ubuntu。

## Step 2：收集与校验三类路径输入

1. **待打包产物目录**：确认存在且非空；已知可执行文件名时用 `test -x "$PUBLISH_DIR/$EXECUTABLE"` 确认可执行权限。目录为空或找不到可执行文件时报错终止，要求用户确认路径，不猜测。
2. **图标文件**：提供了就校验文件存在；用户明确没有图标时跳过转换，告知安装后应用将使用系统默认图标。
3. **`.desktop` 文件路径**：用户提供的是**待生成的目标落盘路径**，不是已存在的文件——按下方模板生成内容。

   🔴 **CHECKPOINT：落盘前必须请用户确认字段内容**（尤其 `Exec`/`Categories`），不得替用户假设。

   🔴 **CHECKPOINT：目标路径已有同名文件时，先请用户确认是否覆盖**，未确认不得覆盖。

   确认后写入该路径，装有 `desktop-file-validate` 则顺带校验一次：

   ```ini
   [Desktop Entry]
   Type=Application
   Name=<display-name>
   Comment=<summary>
   Exec=<package-name>
   Icon=<package-name>
   Terminal=false
   Categories=Utility;
   ```

4. **产出目录**：确认父目录存在且可写；不检查目标 `.deb` 文件本身是否已存在——尚未生成前不存在是正常状态。

## Available scripts

- `scripts/build-deb.sh` — 非交互式打包脚本，见 Step 3 用法与参数说明；`--help` 查看完整接口。

## Step 3：调用自带的 build-deb.sh 执行打包

使用本 skill 自带于 `scripts/build-deb.sh` 的固定脚本执行打包，不在用户项目中生成或复用打包脚本。脚本自身不依赖 `$SkillDir` 之外的任何路径假设，用 skill 加载时提供的绝对 base directory 拼出脚本路径调用：

```bash
"$SkillDir/scripts/build-deb.sh" \
  --name <package-name> \
  --version <version> \
  --arch <amd64-or-arm64> \
  --maintainer "<name <email>>" \
  --publish-dir <待打包产物目录> \
  --out-dir <产出目录> \
  --executable <可执行文件名，默认同 package-name> \
  --desktop-file <Step 2 生成的 .desktop 路径> \
  --icon <图标路径，可选> \
  --depends "<真实依赖列表，逗号分隔>" \
  --description "<one-line summary>"
```

脚本行为（无需重新实现，仅供理解其产出）：非交互、全部输入走 flag；校验产物目录非空、可执行文件存在、`.desktop`/图标路径存在；按 `DEBIAN/`、`usr/bin/`、`usr/lib/<pkg>/`、`usr/share/applications/`、`usr/share/icons/hicolor/256x256/apps/` 搭建 staging 布局并生成 `/usr/bin/<pkg>` 的 exec 包装脚本；`Installed-Size` 用 `du -sk` 实测得出，不使用占位值；成功时把生成的 `.deb` 绝对路径打印到 stdout，诊断信息在 stderr，非零退出码表示失败并附带具体原因。`--help` 可查看完整参数说明。**不包含 `dotnet publish` 步骤**——产物已由用户在 Step 2 提供。

## Step 4：安装验收（命令行 + 图形界面）

1. **元数据检查**：`dpkg-deb -I "$DEB"`、`dpkg-deb -c "$DEB"`；有 `lintian`/`desktop-file-validate` 则跑，没有就如实标注该项未覆盖，不得声称已完成。
2. **命令行安装验收**：

   ```bash
   sudo apt install ./"$DEB"   # 不用 dpkg -i，它不解析依赖
   dpkg -s "$PACKAGE"
   command -v "$PACKAGE"
   "$PACKAGE"                  # 实际启动，确认核心功能路径，不能止步于进程存在
   ```

3. **图形界面安装验收**：有图形桌面会话时，通过桌面文件管理器双击或系统包管理器 GUI（GNOME Software / GDebi 等）安装 `.deb`。

   🔴 **CHECKPOINT：请用户确认应用图标、名称显示正确、点击启动正常**，不得替用户断言验收结果。

   **无图形会话时明确标注该项未覆盖**，不得替用户断言"图形安装可行"。
4. **卸载验证**：区分 `sudo apt remove "$PACKAGE"`（只删应用本身）与 `sudo apt autoremove "$PACKAGE"`（连带清理因它被拉入、现无其他程序依赖的孤立包），按场景选择，`dpkg -s` 确认已卸载。

## 失败处理

| 触发条件 | 处理 |
|---|---|
| `dpkg-deb` 缺失或在非 Linux/WSL 环境执行 | 提示安装命令或切换环境，终止，不擅自安装 |
| 待打包目录为空/无可执行文件 | 报错，要求用户确认产物路径，不猜测 |
| `.desktop` 目标路径已有同名文件且用户未确认覆盖 | 停止，先请用户确认覆盖或改用其他路径 |
| 用户未确认生成的 `.desktop` 字段内容 | 停止，先请用户确认模板字段再落盘 |
| APT 依赖无法满足 | 按目标发行版查询实际包名修正 `Depends`，干净环境重装验证，不删依赖字段"通过" |
| 无图形会话导致图形安装验收无法执行 | 明确标注该项未覆盖，不得替用户断言 |

## 不要做什么

- 不执行 `dotnet publish` 或任何应用构建/发布步骤——待打包产物由用户提供。
- 不使用/推荐 Parcel——不在本 skill 范围内。
- 不复制过期的 `Depends` 清单，必须基于真实依赖收集。
- 不用 `dpkg -i` 做安装验收（不解析依赖）。
- 不在无图形会话时声称图形安装已验证。
- 不擅自执行 `apt-get install` 安装系统级构建依赖，只报告命令并终止，交由用户决定。

## 官方依据

- Avalonia Desktop Linux deployment：`https://docs.avaloniaui.net/docs/deployment/linux`
