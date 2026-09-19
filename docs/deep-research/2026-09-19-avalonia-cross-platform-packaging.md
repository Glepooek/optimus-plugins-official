# Avalonia 跨平台编译与打包

> 2026-09-19 · 目标：Windows 上开发，发布 Windows / Linux / macOS 安装程序

**配套详解文档**（本篇是总览，具体打包步骤见）：

- [Linux 打包详解（.deb）](2026-09-19-avalonia-packaging-linux.md) —— 目录树、control 字段、.desktop 快捷方式、图标规格
- [macOS 打包详解（.app / .dmg / .pkg）](2026-09-19-avalonia-packaging-macos.md) —— bundle 结构、Info.plist 键、签名、公证

## 结论

**编译可以在 Windows 上完成，打包必须在各自平台上完成。**

| 阶段 | 能否在 Windows 做 | 说明 |
|---|---|---|
| 编译（`dotnet publish`） | ✅ 六个 RID 全可以 | 唯一例外：Native AOT 不能跨 OS |
| 打包成安装程序 | ❌ 不要这么做 | 见下文「为什么不用 Windows 单机打包」 |
| 签名 | ❌ 不要这么做 | 同上 |

落地方式：**CI 三平台矩阵**。Windows 包在 Windows runner 打，Linux 包在 Linux runner 打，macOS 包在 macOS runner 打。

---

## 一、编译：dotnet publish 命令

### 六个目标平台

```bash
# Windows
dotnet publish -c Release -r win-x64    --self-contained true
dotnet publish -c Release -r win-arm64  --self-contained true

# Linux
dotnet publish -c Release -r linux-x64   --self-contained true
dotnet publish -c Release -r linux-arm64 --self-contained true

# macOS（必须加 UseAppHost，否则不生成可执行文件，.app 无法运行）
dotnet publish -c Release -r osx-x64   --self-contained true -p:UseAppHost=true
dotnet publish -c Release -r osx-arm64 --self-contained true -p:UseAppHost=true
```

### csproj 声明 RID（按需）

`dotnet publish -r <RID>` 通常无需预先声明。**遇到「找不到目标」类报错时**，在 csproj 里补上：

```xml
<PropertyGroup>
  <RuntimeIdentifiers>win-x64;win-arm64;linux-x64;linux-arm64;osx-x64;osx-arm64</RuntimeIdentifiers>
</PropertyGroup>
```

多个 RID 用分号分隔。显式声明的好处是 IDE 能正确还原各平台的运行时包。

### 常用参数

| 参数 | 作用 | 何时用 |
|---|---|---|
| `--self-contained true` | 打包 .NET 运行时，用户无需安装 | 桌面分发**建议默认开** |
| `-p:UseAppHost=true` | 生成原生可执行文件 | **macOS 必需** |
| `-p:PublishSingleFile=true` | 合并成单文件 | 简化 macOS 签名流程 |
| `-p:PublishReadyToRun=true` | 预编译，加快启动 | 可跨 OS，Windows 上能给 Linux 用 |
| `-p:PublishTrimmed=true` | 裁剪未用代码，减小体积 | 需测试，反射可能被裁掉 |
| `<PublishAot>true</PublishAot>` | 原生 AOT | ⚠️ **不能跨 OS**，只能在目标平台构建 |

### macOS 通用二进制

Apple Silicon 与 Intel 都要覆盖时，可以分别发布后用 `lipo` 合并：

```bash
lipo -create -output MyApp \
     ./publish/osx-x64/MyApp \
     ./publish/osx-arm64/MyApp
```

⚠️ **合并主可执行文件是不够的。** 自包含发布里还有一批原生库（`libSkiaSharp.dylib`、`libHarfBuzzSharp.dylib` 以及 .NET 运行时的 `.dylib`），每一个都要单独 `lipo -create`，否则应用在另一架构上加载原生库时崩溃。Parcel 的 `merge-mac` 步骤做的就是遍历整个目录逐个合并。

体积约为单架构的两倍。**不需要就分开发两个包**——这也是更常见的做法。

### AOT 与 R2R 的区别

| | 跨 OS | 跨架构 |
|---|---|---|
| **ReadyToRun** | ✅ .NET 6 起支持 | ✅ |
| **Native AOT** | ❌ 明确不支持 | ✅ 装好工具链即可 |

微软文档原文：*Native AOT does not support cross-OS compilation.*
要启动加速又想保持单机编译能力，用 R2R 而非 AOT。

---

## 二、为什么不用 Windows 单机打包

技术上「可以」，但有四个不可靠因素，任一个都会导致用户拿到装不上或打不开的包：

| 问题 | 后果 |
|---|---|
| **NTFS 存不下可执行位** | Linux/macOS 上双击没反应，`.so` 也丢权限 |
| **NTFS 存不下符号链接** | Windows 工具解包时替换成零字节占位文件 |
| **DMG 需要 WSL2** | 多一层环境依赖，CI 上难复现 |
| **无法在 Windows 上测试产物** | 签名对不对、能不能启动，构建完全不知道 |

最后一条是关键：**前三条可以靠工具绕，第四条绕不过。** 在 Windows 上产出一个「看起来完整」的 `.dmg`，Gatekeeper 是否放行、Retina 渲染是否正常、菜单栏是否正确，只有真机能验证。构建出来却不敢发，等于没构建。

AppImage / Flatpak / Snap 更是直接依赖 Linux 原生二进制，Windows 上无解。

---

## 三、打包：各平台在自己的 runner 上做

### Windows

| 格式 | 工具 |
|---|---|
| `.exe` 安装器 | Inno Setup / NSIS |
| `.msi` | WiX Toolset |
| `.msix` | Windows SDK / Parcel |
| 免安装 | ZIP |

签名：`signtool`（Windows SDK）+ Authenticode 证书。

### Linux

| 格式 | 工具 | 适用 |
|---|---|---|
| `.deb` | `dpkg-deb --root-owner-group --build` | Debian / Ubuntu |
| `.rpm` | `rpmbuild` | Fedora / RHEL / openSUSE |
| AppImage | `appimagetool` | 免安装，全发行版通用 |
| Flatpak | `flatpak-builder` | 沙箱分发 |

`.deb` 的依赖声明里，Avalonia 自身需要：`libx11-6, libice6, libsm6, libfontconfig1`，再加上 .NET 的依赖（`apt show dotnet-runtime-deps-8.0` 查 *Depends:* 行）。

注意 `.desktop` 桌面快捷方式与图标（`/usr/share/pixmaps/` + `/usr/share/icons/hicolor/`），否则装完在应用菜单里看不到。

### macOS

流程：`.app` 包 → 签名 → 公证 → 装订 → `.dmg` / `.pkg`

```bash
# 1. 签名：先逐个签 Contents/MacOS 下的文件，最后签 bundle（不要用 --deep）
find "MyApp.app/Contents/MacOS" -type f -print0 | while IFS= read -r -d '' f; do
    codesign --force --timestamp --options=runtime \
             --entitlements entitlements.plist \
             --sign "Developer ID Application: ..." "$f"
done
codesign --force --timestamp --options=runtime \
         --entitlements entitlements.plist \
         --sign "Developer ID Application: ..." MyApp.app

# 2. 压缩（用 ditto，zip 会导致公证失败）
ditto -c -k --sequesterRsrc --keepParent MyApp.app MyApp.zip

# 3. 公证并等待结果
xcrun notarytool submit MyApp.zip --keychain-profile "AC_PASSWORD" --wait

# 4. 装订 ticket
xcrun stapler staple MyApp.app
```

完整步骤与各参数含义见 [macOS 打包详解](2026-09-19-avalonia-packaging-macos.md)。

必需项：

- **Apple Developer Program 会员（$99/年）**
- **Developer ID Application** 证书签应用，**Developer ID Installer** 证书签 `.pkg`——两者不能互换
- 必须开启 hardened runtime（`--options=runtime`）
- entitlement 至少需要 `com.apple.security.cs.allow-jit`（Avalonia 运行必需）
- macOS 10.15+ 商店外分发**强制公证**

---

## 四、CI 矩阵配置

```yaml
strategy:
  matrix:
    include:
      - { os: windows-latest, rid: win-x64    }
      - { os: windows-latest, rid: win-arm64  }
      - { os: ubuntu-latest,  rid: linux-x64  }
      - { os: ubuntu-latest,  rid: linux-arm64 }
      - { os: macos-latest,   rid: osx-x64    }
      - { os: macos-latest,   rid: osx-arm64  }

runs-on: ${{ matrix.os }}
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-dotnet@v4
  - run: dotnet publish -c Release -r ${{ matrix.rid }} --self-contained true
  # 后续步骤按 matrix.os 分支，调各平台原生打包工具
```

成本：公开仓库免费；私有仓库按分钟计费，**macOS runner 倍率 10×**，是主要开销。

---

## 五、可选：Avalonia Parcel

官方打包工具，一条命令覆盖全平台，省去自己维护七种格式的胶水脚本：

```bash
dotnet tool install --global AvaloniaUI.Parcel
parcel pack MyApp.parcel -r win-x64 -r osx-x64 -r linux-x64 -p nsis -p dmg -p deb
```

支持 `deb` `rpm` `dmg` `pkg` `msix` `nsis` `zip`（无 MSI）。

🔴 **CLI 需 Avalonia Plus 及以上授权，免费 Community 版只有 GUI。**

即便用 Parcel，**仍建议在各自平台的 runner 上跑**——它虽支持跨平台打包，但测试问题依旧存在。

---

## 六、待确认

- Parcel 每席位价格（定价页调研时无法访问）
- Velopack（安装+自动更新框架）消费侧的跨平台打包能力，文档未明确

---

## 来源

- [Avalonia — macOS Deployment](https://docs.avaloniaui.net/docs/deployment/macos) · [Linux Deployment](https://docs.avaloniaui.net/docs/deployment/linux)
- [Avalonia Parcel — macOS](https://docs.avaloniaui.net/tools/parcel/packaging-for-macos) · [Windows](https://docs.avaloniaui.net/tools/parcel/packaging-for-windows) · [Setup](https://docs.avaloniaui.net/tools/parcel/setup) · [CLI](https://docs.avaloniaui.net/tools/parcel/command-line-reference/)
- [Microsoft — Native AOT Cross-compilation](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/cross-compile) · [ReadyToRun](https://learn.microsoft.com/en-us/dotnet/core/deploying/ready-to-run)
