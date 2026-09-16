---
name: avalonia-deb-release
description: Use when publishing an Avalonia desktop app for Debian or Ubuntu, creating a Linux .deb package, configuring Avalonia Parcel, or validating a Debian package on Linux/WSL. 触发词："Avalonia 发布"、"Avalonia Linux 打包"、"打 deb"、"Ubuntu 安装包"、"Parcel"。
license: MIT
compatibility: 目标项目需要匹配的 .NET SDK；手动路线需要 Debian/Ubuntu 或 WSL 中的 dpkg-deb，建议安装 lintian、desktop-file-utils 和图形会话/虚拟显示器进行验收。Parcel 路线还需要 Avalonia Plus 的 Parcel CLI 与有效许可证。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: workflow
allowed-tools: Read Write Bash Glob Grep avalonia-docs
---

# Avalonia Debian 发布

面向 Debian/Ubuntu 的发布不是只执行 `dotnet publish`：可安装的 `.deb` 还必须有正确的架构、依赖、启动器、桌面入口、图标、包元数据及干净环境验收。优先使用已获授权的 Avalonia Parcel；无 Parcel CLI 授权或需要完全控制 Debian 布局时，使用官方 `dpkg-deb` 手动路线。

## 需求预告

首次响应时一次性收集缺失信息：目标 `.csproj`、应用显示名和 Debian 包名、版本、RID/架构（如 `linux-x64`/`amd64`）、维护者与主页、图标路径、是否需要文件关联/URL scheme、发布产物目录，以及是否有 Avalonia Plus 的 Parcel CLI 许可证。已有信息不得重复询问。

默认只构建、检查和安装到隔离测试环境；上传制品、创建 Git tag、发布 GitHub Release、更新 APT 仓库或覆盖正式包都属于发布动作，必须先经 CHECKPOINT。

## Step 1：确认环境、项目和发布策略

1. 在目标项目根目录确认 `.csproj`、目标框架、应用程序集名、版本来源及发布目录。读取现有 CI/发布脚本，复用既有版本规则，不自行改写版本号。
2. 在 Linux 主机或 WSL 中检查：

   ```bash
   dotnet --info
   dpkg-deb --version
   command -v lintian || true
   command -v desktop-file-validate || true
   ```

   Windows 开发机应在 WSL2 Debian/Ubuntu 或 Linux CI 中构建和验收；不要把 Windows 上产生的 Linux 文件权限当作已验证。
3. 明确每个 RID 对应一个包：`linux-x64` → `amd64`，`linux-arm64` → `arm64`。不得把 x64 文件标成 `arm64`，也不得用一个 `.deb` 混装多个架构。
4. 选择路线：

   | 条件 | 路线 |
   |---|---|
   | 有 Avalonia Plus、`parcel --version` 可用且许可证已配置 | Parcel 自动化路线 |
   | 没有 Parcel CLI 授权、需自定义 Debian maintainer scripts/布局 | 手动 `dpkg-deb` 路线 |

   Parcel CLI 仅随 Avalonia Plus 提供；发现缺许可证时直接切换手动路线，不要尝试绕过许可证。

### 🔴 CHECKPOINT：安装构建依赖或修改发布配置

安装系统包、添加/修改 `.parcel`、Debian 控制文件、发布脚本或 CI 配置前，说明会修改的路径、执行环境和可回滚方式，取得用户确认。产物目录和临时 staging 目录可以在确认后清理重建。

## Step 2：准备可发布的 Linux 输出

1. 先运行目标项目已有的测试；失败时停止打包，报告失败测试，不用打包成功掩盖质量问题。
2. 以目标 RID 显式发布。默认使用自包含发布，避免要求最终用户预装 .NET；若项目必须 framework-dependent，则在 `Depends` 中声明匹配的 .NET runtime。

   ```bash
   dotnet publish "$PROJECT" -c Release -r "$RID" --self-contained true \
     -o "$PUBLISH_DIR"
   test -x "$PUBLISH_DIR/$EXECUTABLE"
   file "$PUBLISH_DIR/$EXECUTABLE"
   ```

3. 不要在发布时临时启用 trimming、AOT、single-file 或 ReadyToRun。它们是独立的发布模式，必须先在目标 Linux 上完成应用级回归测试。
4. 记录版本、Git revision（若项目已提供）、RID、SDK 版本和 publish 命令，供包追溯与故障复现。

## Step 3A：Parcel 自动化路线

1. 通过 `search_avalonia_docs` 查询当前 Parcel `.parcel` 配置字段；不要凭记忆生成可能已过期的 schema。
2. 配置稳定的 package name、安装目录、应用名、图标、maintainer、桌面分类、版权/许可证、可选 `/usr/bin` 链接，以及应用额外依赖和文件关联/URL scheme。
3. 不把许可证写入仓库。使用 `AVALONIA_TOOLS_LICENSE_KEY` 或受控 CI secret，并确认日志未输出其值。
4. 可预装工具并构建：

   ```bash
   parcel install-tools -r linux-x64 -p deb
   parcel pack ./MyApp.parcel -r linux-x64 -p deb -o ./artifacts
   ```

5. 继续执行 Step 4 的包检查和安装验收。Parcel 会生成 `.desktop` 文件并可注册图标、文件关联、URL scheme 与 `/usr/bin` 链接；仍必须在目标发行版实际验证。

## Step 3B：手动 `dpkg-deb` 路线

在项目中创建受版本控制的 `packaging/debian/`（名称可按现有仓库约定调整），至少包含 `control`、启动器、`.desktop` 和图标。staging 目录与 `.deb` 产物不得提交。

### 包布局

```text
staging/
├── DEBIAN/control
├── usr/bin/<package-name>
├── usr/lib/<package-name>/                 # dotnet publish 的完整输出
└── usr/share/
    ├── applications/<package-name>.desktop
    ├── pixmaps/<package-name>.png
    └── icons/hicolor/<size>/apps/<package-name>.png  # 推荐
```

`control` 必须使用实际值；不要复制过期的完整依赖清单。Avalonia 需要 `libx11-6, libice6, libsm6, libfontconfig1`；还要按目标 .NET 版本和发行版补齐 native runtime dependencies。可用 `apt show dotnet-runtime-deps-<major>` 取得目标发行版的当前基线，再以干净系统安装结果为准。

```debcontrol
Package: <package-name>
Version: <debian-compatible-version>
Section: utils
Priority: optional
Architecture: <amd64-or-arm64>
Depends: <Avalonia and target-.NET native dependencies>
Maintainer: <name <email>>
Homepage: <https-url>
Description: <one-line summary>
 <long description starts with one space>
```

启动器必须以 `exec` 替换 shell 进程，并透传参数：

```bash
#!/bin/sh
exec /usr/lib/<package-name>/<executable> "$@"
```

`.desktop` 必须引用安装后的命令与图标名，不引用构建机绝对路径：

```ini
[Desktop Entry]
Name=<display-name>
Comment=<summary>
Exec=<package-name> %F
Icon=<package-name>
Terminal=false
Type=Application
Categories=Utility;
```

仅当应用实际支持多文件打开时保留 `%F`；URL 激活使用 `%U`，两者都不适用时移除占位符。

### 构建命令

```bash
set -eu
rm -rf "$STAGING"
install -d "$STAGING/DEBIAN" "$STAGING/usr/bin" \
  "$STAGING/usr/lib/$PACKAGE" "$STAGING/usr/share/applications" \
  "$STAGING/usr/share/pixmaps"
install -m 0644 packaging/debian/control "$STAGING/DEBIAN/control"
install -m 0755 packaging/debian/$PACKAGE "$STAGING/usr/bin/$PACKAGE"
cp -a "$PUBLISH_DIR/." "$STAGING/usr/lib/$PACKAGE/"
chmod -R a+rX "$STAGING/usr/lib/$PACKAGE"
chmod 0755 "$STAGING/usr/lib/$PACKAGE/$EXECUTABLE"
install -m 0644 packaging/debian/$PACKAGE.desktop \
  "$STAGING/usr/share/applications/$PACKAGE.desktop"
install -m 0644 "$ICON" "$STAGING/usr/share/pixmaps/$PACKAGE.png"
dpkg-deb --root-owner-group --build "$STAGING" \
  "./artifacts/${PACKAGE}_${VERSION}_${DEB_ARCH}.deb"
```

增加 hicolor 图标时，为 SVG 放入 `usr/share/icons/hicolor/scalable/apps/`；PNG 放入对应 `<size>x<size>/apps/`。构建后进入 Step 4，不能以 `dpkg-deb` 退出码 0 代替安装验收。

## Step 4：按层验证包和应用

1. 检查包元数据、路径、权限与桌面入口：

   ```bash
   dpkg-deb -I "$DEB"
   dpkg-deb -c "$DEB"
   lintian "$DEB" || true
   desktop-file-validate "$STAGING/usr/share/applications/$PACKAGE.desktop"
   ```

   `lintian` 仅用于发现问题；对每条 warning 给出接受理由或修复，不得静默忽略。若没有 `lintian` 或 `desktop-file-validate`，明确记录缺失的验证及安装命令，不能声称已完成该项。
2. 在干净的、与目标版本相同的 Debian/Ubuntu VM、容器或 WSL 实例中安装，并确认依赖由 APT 解析：

   ```bash
   sudo apt install ./"$DEB"
   dpkg -s "$PACKAGE"
   command -v "$PACKAGE"
   "$PACKAGE" --help || true
   ```

3. 在真实桌面会话启动，确认 launcher 显示正确名称/图标、命令行启动有效、文件/URL 激活（若声明）有效。无图形会话时只能完成安装和命令行烟测，必须标明桌面集成尚未验证。
4. 验证卸载和升级：

   ```bash
   sudo apt remove "$PACKAGE"
   ! dpkg -s "$PACKAGE"
   # 有上一版本时：先安装旧包，再 apt install 新包，验证配置和启动行为。
   ```

5. 产出 `.deb`、SHA-256、验证矩阵与未覆盖风险；签名、上传或对外发布前进入 CHECKPOINT。

### 🔴 CHECKPOINT：对外发布

在上传、签名、创建 Release、推送 APT 仓库或替换现网安装包前，展示包名、版本、架构、SHA-256、验证结果、已知限制和目标渠道，等待用户明确批准。

## 失败处理

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| `parcel` 找不到或无有效许可证 | 检查 PATH、许可证环境变量与 Avalonia Plus 授权 | 切换官方手动 `dpkg-deb` 路线；不尝试绕过授权 |
| `dpkg-deb` 缺失或在 Windows 直接运行 | 改在 Debian/Ubuntu、WSL2 或 Linux CI 执行 | 先建立可复现的 Linux 构建环境再继续 |
| APT 依赖无法满足 | 用目标发行版查询当前包名并修正 `Depends` | 在干净目标版本中重新安装；不要删除依赖字段来“通过” |
| 包已安装但应用启动失败 | 收集终端输出、`ldd` 和图形会话日志，确认 RID/架构 | 回到 publish 选项和 native dependencies，修复后重新打包和安装验收 |
| `.desktop` 不显示或图标错误 | 检查 `desktop-file-validate`、`Exec`/`Icon` 与安装路径 | 修复入口/图标布局并在新会话复验，不把缓存偶然命中当成功 |

## 不要做什么

- 不把 Windows `win-x64` 输出、Windows 路径或 CRLF 启动器塞进 Linux `.deb`。
- 不在未确认架构、包名、版本或目标发行版时生成可发布制品。
- 不将密钥、token、Portal 会话或签名私钥写入 `.parcel`、脚本、仓库或日志。
- 不把自包含发布误称为零系统依赖，也不复制某个旧发行版的 `Depends` 清单。
- 不因 `dpkg-deb --build` 成功就声称发布通过；至少完成元数据、干净安装、启动、卸载四层验收。
- 不在未获确认时上传、签名、替换正式包或创建公开 Release。

## 官方依据

- Avalonia Desktop Linux deployment：`https://docs.avaloniaui.net/docs/deployment/linux`
- Avalonia Parcel setup：`https://docs.avaloniaui.net/tools/parcel/setup`
- Avalonia Parcel CLI：`https://docs.avaloniaui.net/tools/parcel/command-line-reference`
- Avalonia Parcel Linux packaging：`https://docs.avaloniaui.net/tools/parcel/packaging-for-linux`
