# Avalonia Linux 打包详解（.deb）

> 2026-09-19 · 依据 [Avalonia Linux Deployment](https://docs.avaloniaui.net/docs/deployment/linux)
> 配套：[macOS 打包详解](2026-09-19-avalonia-packaging-macos.md) · [跨平台编译总览](2026-09-19-avalonia-cross-platform-packaging.md)

## 打包在做什么

Avalonia 编译出的 Linux 产物本身就能跑——双击或终端执行即可。**做 `.deb` 的目的不是让它能运行，而是让它「像个正经应用」**：出现在应用菜单里、有图标、能从终端敲名字启动、能被 `apt remove` 干净卸载。

`.deb` 本质上是**一个带元数据的目录快照**。你搭一个目录树，里面的路径就是安装后在用户机器上的绝对路径，`dpkg-deb` 把它压成一个文件。理解这一点，整个流程就不神秘了：

```
dotnet publish 产物  ──┐
control 元数据      ──┤
启动脚本            ──┼──→ staging 目录树 ──→ dpkg-deb ──→ myprogram_3.1.0_amd64.deb
.desktop 快捷方式    ──┤
各尺寸图标           ──┘
```

---

## 第一步：dotnet publish

```bash
dotnet publish "./src/MyProgram.Desktop/MyProgram.Desktop.csproj" \
  --verbosity quiet \
  --nologo \
  --configuration Release \
  --self-contained true \
  --runtime linux-x64 \
  --output "./out/linux-x64"
```

**`--self-contained true` 是官方建议的默认值**，理由是「final users won't need to install .NET」——把运行时一起打包，用户不必先装 .NET。代价是体积明显增大（一个空白 Avalonia 模板自包含后通常在数十 MB 量级，具体取决于是否开启裁剪）。

`--output` 显式指定输出目录，避免去 `bin/Release/net10.0/linux-x64/publish/` 那种深路径里翻。

### 产物里有什么

| 文件 | 说明 |
|---|---|
| `MyProgram.Desktop` | 主可执行文件（**无扩展名**），名字等于 csproj 名去掉扩展名 |
| `MyProgram.Desktop.dll` | 托管程序集 |
| `libSkiaSharp.so` | Avalonia 渲染后端（Skia）原生库 |
| `libHarfBuzzSharp.so` | 文本排版原生库 |
| 其余 `*.so` | .NET 运行时原生部分 |
| 大量 `*.dll` | .NET 运行时托管部分 |

> **关于本文的占位符命名**：官方文档在目录树里用 `myprogram_executable` 指代主可执行文件，在正文里说它「usually matches the .NET project name」。本文沿用官方的 `myprogram_executable` 作为占位符，**实际替换成上表第一行的真实文件名**（项目叫 `MyProgram.Desktop.csproj` → 产物叫 `MyProgram.Desktop`）。

⚠️ 这些 `.so` 文件**必须保留读权限**，主可执行文件**必须有执行权限**，否则安装后启动失败。权限处理见「完整构建脚本」节的三条 `chmod`。

---

## 第二步：搭 staging 目录树

这是整个流程的核心。**目录里的每个路径 = 安装后的绝对路径。**

```
staging_folder/
├── DEBIAN/
│   └── control                        ← 包元数据，唯一不会被安装到系统的目录
└── usr/
    ├── bin/
    │   └── myprogram                  ← 启动脚本（在 PATH 里，用户敲 myprogram 就能启动）
    ├── lib/
    │   └── myprogram/                 ← dotnet publish 的全部产物都放这里
    │       ├── myprogram_executable
    │       ├── myprogram.dll
    │       ├── libSkiaSharp.so
    │       ├── libHarfBuzzSharp.so
    │       └── ...
    └── share/
        ├── applications/
        │   └── MyProgram.desktop      ← 桌面快捷方式，决定应用菜单里的样子
        ├── pixmaps/
        │   └── myprogram.png          ← 主图标，1024×1024 PNG
        └── icons/hicolor/             ← 多分辨率图标（可选，但建议）
            ├── 16x16/apps/myprogram.png
            ├── 32x32/apps/myprogram.png
            ├── 48x48/apps/myprogram.png
            ├── 64x64/apps/myprogram.png
            ├── 128x128/apps/myprogram.png
            ├── 256x256/apps/myprogram.png
            ├── 512x512/apps/myprogram.png
            └── scalable/apps/myprogram.svg
```

各目录职责：

| 路径 | 作用 | 为什么是这里 |
|---|---|---|
| `DEBIAN/` | 放 `control` 等控制文件 | `dpkg-deb` 约定的特殊目录，**不会**被安装到目标系统 |
| `/usr/bin/` | 启动脚本 | 这个目录在 `PATH` 里，所以终端敲 `myprogram` 能直接启动 |
| `/usr/lib/myprogram/` | 程序本体 | 按 FHS 规范，架构相关的私有文件放 `/usr/lib/<包名>/` |
| `/usr/share/applications/` | `.desktop` 文件 | 桌面环境（GNOME/KDE）扫描此目录构建应用菜单 |
| `/usr/share/pixmaps/` | 主图标 | 传统 Debian 图标位置，兼容性最好 |
| `/usr/share/icons/hicolor/` | 分尺寸图标 | freedesktop 图标主题规范，桌面按需挑最合适的尺寸 |

**为什么图标要放两处？** 官方引用的博文建议 `hicolor` 和 `pixmaps` 都放。`pixmaps` 是老规范、兜底用；`hicolor` 是新规范，能让桌面在不同场景（任务栏 16px、应用菜单 48px、Dock 256px）取到不缩放的原图，显示更清晰。只放 `pixmaps` 图标也能显示，但会被拉伸。

---

## 第三步：control 文件

放在 `DEBIAN/control`。这是包的身份证，`apt` 靠它判断能不能装、装了什么、依赖谁。

```
Package: myprogram
Version: 3.1.0
Section: devel
Priority: optional
Architecture: amd64
Installed-Size: 68279
Depends: libx11-6, libice6, libsm6, libfontconfig1, ca-certificates, tzdata, libc6, libgcc1 | libgcc-s1, libgssapi-krb5-2, libstdc++6, zlib1g, libssl1.0.0 | libssl1.0.2 | libssl1.1 | libssl3, libicu | libicu74 | libicu72 | libicu71 | libicu70 | libicu69 | libicu68 | libicu67 | libicu66 | libicu65 | libicu63 | libicu60 | libicu57 | libicu55 | libicu52
Maintainer: Ken Lee <ken@example.com>
Homepage: https://github.com/kenlee/myprogram
Description: This is MyProgram, great for doing X.
Copyright: 2022-2024 Ken Lee <ken@example.com>
```

逐字段说明：

| 字段 | 作用 | 注意 |
|---|---|---|
| `Package` | 包名，卸载时用的就是这个名字（`apt remove myprogram`） | 必须小写，只能用字母数字和 `-+.` |
| `Version` | 版本号 | `apt` 靠它判断是升级还是降级 |
| `Section` | 分类，如 `devel`、`utils`、`graphics`、`net` | 影响归类，不影响功能 |
| `Priority` | 优先级 | 第三方应用固定填 `optional` |
| `Architecture` | 目标架构 | **x64 写 `amd64`，不是 `x64`**；arm64 写 `arm64` |
| `Installed-Size` | 安装后占用空间，单位 **KB** | 供 `apt` 显示「将占用 X 空间」；填不准不会报错 |
| `Depends` | 依赖包列表 | 最容易出错的字段，见下 |
| `Maintainer` | 维护者，格式 `姓名 <邮箱>` | 格式错会被 lint 警告 |
| `Homepage` | 项目主页 | 可选 |
| `Description` | 描述 | 第一行是摘要；多行时后续行需**缩进一个空格** |
| `Copyright` | 版权声明 | 非标准字段，标准做法是放 `/usr/share/doc/<包>/copyright` |

### Depends 字段怎么写

这是最容易翻车的地方。语法规则：

- **逗号 `,` = 「并且」**，都必须满足
- **竖线 `|` = 「或者」**，满足任一即可

`libssl1.0.0 | libssl1.0.2 | libssl1.1 | libssl3` 这一串的含义是：**任意一个 OpenSSL 版本都行**。为什么要这么写？因为不同发行版、不同版本带的 OpenSSL 包名不同。只写 `libssl3` 会导致在旧版 Ubuntu 上装不上。同理那一长串 `libicu*`。

依赖分三部分：

1. **Avalonia 自身需要**：`libx11-6, libice6, libsm6, libfontconfig1`
2. **.NET 运行时需要**：查询命令 —— 后缀按你的 .NET 版本改

   ```bash
   apt show dotnet-runtime-deps-8.0
   ```

   读输出里的 `Depends:` 行，整段抄过来。

3. **你的应用特有的**：比如调了 `libgtk`、`libnotify` 就得加上

⚠️ **自包含发布仍然需要声明 .NET 依赖**。`--self-contained` 打包的是 .NET 运行时本身，但运行时还要链接系统的 C 库、ICU、OpenSSL——这些不在打包范围内。

---

## 第四步：启动脚本

放在 `/usr/bin/myprogram`，**文件名不带 `.sh` 后缀**——因为用户在终端里敲的就是这个名字，`myprogram.sh` 很别扭。

```bash
#!/bin/bash
# use exec to not have the wrapper script staying as a separate process
# "$@" to pass command line arguments to the app
exec /usr/lib/myprogram/myprogram_executable "$@"
```

三行，每行都有理由：

| 部分 | 作用 |
|---|---|
| `#!/bin/bash` | 声明用 bash 解释 |
| `exec` | **用目标进程替换当前 shell 进程**，而不是派生子进程。不加 `exec` 的话，进程列表里会多一个常驻的包装脚本，信号（如 `Ctrl+C`、系统关机）也无法正确传递到真正的应用 |
| `"$@"` | 把命令行参数原样转发给应用。带引号才能正确处理含空格的参数 |

**为什么需要这层包装？** 两个原因：

1. **让 `.desktop` 文件简单**。有了它，`Exec=myprogram` 就够了，不用写 `/usr/lib/myprogram/myprogram_executable` 这种长路径
2. **让终端可用**。`/usr/bin` 在 `PATH` 里，`/usr/lib/myprogram/` 不在

⚠️ 脚本里的 `myprogram_executable` 要换成**实际的可执行文件名**——通常等于 csproj 名去掉扩展名。项目叫 `MyProgram.Desktop.csproj`，产物就是 `MyProgram.Desktop`。

---

## 第五步：.desktop 快捷方式

放在 `/usr/share/applications/MyProgram.desktop`。遵循 [freedesktop Desktop Entry 规范](https://specifications.freedesktop.org/desktop-entry-spec/latest/)，决定应用在菜单里长什么样。

```ini
[Desktop Entry]
Name=MyProgram
Comment=MyProgram, great for doing X
Icon=myprogram
Exec=myprogram
StartupWMClass=myprogram
Terminal=false
Type=Application
Categories=Development
GenericName=MyProgram
Keywords=keyword1; keyword2; keyword3
```

逐键说明：

| 键 | 作用 | 注意 |
|---|---|---|
| `[Desktop Entry]` | 段头 | 必需，固定写法 |
| `Name` | 菜单里显示的名字 | 必需 |
| `Comment` | 鼠标悬停时的提示文字 | 一句话说明用途 |
| `Icon` | 图标**查找名**，不是文件路径 | 填 `myprogram`，系统自动去 `pixmaps` 和 `hicolor` 里找同名文件 |
| `Exec` | 启动命令 | 填启动脚本名即可 |
| `StartupWMClass` | 窗口类名匹配 | **容易漏但很重要**，见下 |
| `Terminal` | 是否在终端里运行 | GUI 应用填 `false` |
| `Type` | 条目类型 | GUI 应用填 `Application` |
| `Categories` | 菜单分类 | 如 `Development`、`Graphics`、`Office`、`Utility` |
| `GenericName` | 通用名 | 如应用叫 "Firefox"，通用名是 "Web Browser" |
| `Keywords` | 搜索关键词 | 分号分隔，用户在应用搜索框里输入这些词能找到 |

### StartupWMClass 为什么重要

没有它，应用启动后在 Dock / 任务栏里会**显示成一个额外的通用图标**，而不是与快捷方式合并。原因是桌面环境需要把「运行中的窗口」和「已安装的应用」对应起来，靠的就是窗口的 WM_CLASS 属性。

Avalonia 应用的 WM_CLASS 通常等于可执行文件名。**验证方法**：启动应用后执行下面的命令，光标会变成十字，点击应用窗口即输出。

```bash
xprop WM_CLASS
```

输出形如：

```
WM_CLASS(STRING) = "myprogram", "MyProgram"
                    └ instance ┘  └─ class ─┘
```

⚠️ **两个值取后一个（class name）填进 `StartupWMClass`。** 前一个是 instance name，通常是小写的可执行文件名，填错了匹配不上。

### Exec 的参数占位符

| 占位符 | 含义 | 用途 |
|---|---|---|
| `%F` | 多个文件路径 | 文件管理器「用...打开」传文件进来 |
| `%f` | 单个文件路径 | 同上，只接受一个 |
| `%U` | 多个 URL | 注册自定义协议（如 `myapp://`） |
| `%u` | 单个 URL | 同上 |

需要支持「用我的应用打开文件」时写 `Exec=myprogram %F`。

⚠️ 应用不解析命令行参数就别写。从菜单直接启动时不传参数、不受影响，但用户从文件管理器「用...打开」时，文件路径会作为参数传进来——应用若不处理，轻则忽略（用户以为没生效），重则参数解析报错退出。

---

## 第六步：图标

| 位置 | 格式 | 尺寸 | 必需性 |
|---|---|---|---|
| `/usr/share/pixmaps/myprogram.png` | PNG | **1024×1024** | 建议 |
| `/usr/share/icons/hicolor/16x16/apps/myprogram.png` | PNG | 16×16 | 可选 |
| `/usr/share/icons/hicolor/32x32/apps/myprogram.png` | PNG | 32×32 | 可选 |
| `/usr/share/icons/hicolor/48x48/apps/myprogram.png` | PNG | 48×48 | 可选 |
| `/usr/share/icons/hicolor/64x64/apps/myprogram.png` | PNG | 64×64 | 可选 |
| `/usr/share/icons/hicolor/128x128/apps/myprogram.png` | PNG | 128×128 | 可选 |
| `/usr/share/icons/hicolor/256x256/apps/myprogram.png` | PNG | 256×256 | 可选 |
| `/usr/share/icons/hicolor/512x512/apps/myprogram.png` | PNG | 512×512 | 可选 |
| `/usr/share/icons/hicolor/scalable/apps/myprogram.svg` | SVG | 矢量 | 可选 |

关键点：

- **文件名必须等于 `.desktop` 里 `Icon=` 的值**，不含扩展名。`Icon=myprogram` → 文件名 `myprogram.png`
- 路径中间那层固定是 `apps`（还有 `mimetypes`、`places` 等，应用图标用 `apps`）
- 官方给 pixmaps 的注释是「A 1024px x 1024px PNG, like VS Code uses for its icon」——直接对标 VS Code 的做法

### 查找优先级：精确尺寸优先，SVG 兜底

按 [freedesktop 图标主题规范](https://specifications.freedesktop.org/icon-theme-spec/latest/)，桌面环境的查找顺序是：

1. 在 `hicolor/<所需尺寸>/apps/` 找**精确匹配**的位图
2. 找不到则用 `scalable/apps/` 的 SVG 渲染
3. 再找不到才回退到 `pixmaps/` 并缩放

⚠️ **SVG 不是「优先级最高」，而是兜底项。** 提供了 48×48 的 PNG，桌面在需要 48px 时会用它而非渲染 SVG——位图省去了实时渲染开销。只放 SVG 能工作，但小尺寸下矢量图缩下去的观感通常不如专门优化过的位图（细节会糊成一团）。

实用建议：**SVG 必放**（覆盖任意非标准尺寸），再补 48×48 和 256×256 两档位图（应用菜单和 Dock 最常用的尺寸），性价比最高。

---

## 第七步：打包

```bash
dpkg-deb --root-owner-group --build ./staging_folder/ "./myprogram_3.1.0_amd64.deb"
```

| 参数 | 作用 |
|---|---|
| `--root-owner-group` | **把包内所有文件的属主强制设为 `root:root`**。不加的话会用当前构建用户的 uid/gid，装到别人机器上属主错乱 |
| `--build <目录> <输出文件>` | 指定 staging 目录和产出文件名 |

### 文件名约定

```
myprogram_3.1.0_amd64.deb
└─包名──┘ └版本┘ └架构┘
```

用下划线分隔，架构 **x64 写 `amd64`**（Debian 的历史命名，不是 `x64` 也不是 `x86_64`）。

---

## 完整构建脚本

```bash
#!/bin/bash

# ---------- 清理 ----------
rm -rf ./out/
rm -rf ./staging_folder/

# ---------- 发布 ----------
# self-contained 推荐开启，用户无需安装 .NET
dotnet publish "./src/MyProgram.Desktop/MyProgram.Desktop.csproj" \
  --verbosity quiet \
  --nologo \
  --configuration Release \
  --self-contained true \
  --runtime linux-x64 \
  --output "./out/linux-x64"

# ---------- staging 根目录 ----------
mkdir staging_folder

# ---------- control 文件 ----------
mkdir ./staging_folder/DEBIAN
cp ./src/MyProgram.Desktop.Debian/control ./staging_folder/DEBIAN

# ---------- 启动脚本 ----------
mkdir ./staging_folder/usr
mkdir ./staging_folder/usr/bin
cp ./src/MyProgram.Desktop.Debian/myprogram.sh ./staging_folder/usr/bin/myprogram
chmod +x ./staging_folder/usr/bin/myprogram          # 启动脚本需可执行

# ---------- 程序本体 ----------
mkdir ./staging_folder/usr/lib
mkdir ./staging_folder/usr/lib/myprogram
cp -f -a ./out/linux-x64/. ./staging_folder/usr/lib/myprogram/
chmod -R a+rX ./staging_folder/usr/lib/myprogram/     # 所有文件可读，目录可进入
chmod +x ./staging_folder/usr/lib/myprogram/myprogram_executable   # 主程序可执行

# ---------- 桌面快捷方式 ----------
mkdir ./staging_folder/usr/share
mkdir ./staging_folder/usr/share/applications
cp ./src/MyProgram.Desktop.Debian/MyProgram.desktop \
   ./staging_folder/usr/share/applications/MyProgram.desktop

# ---------- 主图标（1024×1024 PNG）----------
mkdir ./staging_folder/usr/share/pixmaps
cp ./src/MyProgram.Desktop.Debian/myprogram_icon_1024px.png \
   ./staging_folder/usr/share/pixmaps/myprogram.png

# ---------- hicolor 矢量图标 ----------
mkdir ./staging_folder/usr/share/icons
mkdir ./staging_folder/usr/share/icons/hicolor
mkdir ./staging_folder/usr/share/icons/hicolor/scalable
mkdir ./staging_folder/usr/share/icons/hicolor/scalable/apps
cp ./misc/myprogram_logo.svg \
   ./staging_folder/usr/share/icons/hicolor/scalable/apps/myprogram.svg

# ---------- 生成 .deb ----------
dpkg-deb --root-owner-group --build ./staging_folder/ ./myprogram_3.1.0_amd64.deb
```

### 三条 chmod 的分工

| 命令 | 对象 | 为什么 |
|---|---|---|
| `chmod +x .../usr/bin/myprogram` | 启动脚本 | 不可执行则终端敲名字报 Permission denied |
| `chmod -R a+rX .../usr/lib/myprogram/` | 全部文件 | `a+rX` 中**大写 `X`** 表示「只给目录和已有执行权限的文件加 x」，避免给 `.dll` 误加执行位 |
| `chmod +x .../myprogram_executable` | 主可执行文件 | 上一条的大写 `X` 不会给它加 x，需单独补 |

⚠️ **在 Windows 上跑这套脚本，这三条 chmod 全部失效**——NTFS 存不下 POSIX 权限位。这是必须在 Linux 上打包的根本原因。

---

## 安装与验证

```bash
# 安装（注意 ./ 前缀，否则 apt 会去仓库里找同名包）
sudo apt install ./myprogram_3.1.0_amd64.deb

# 卸载（用 control 里的 Package 字段值）
sudo apt remove myprogram
```

装完检查清单：

| 检查项 | 命令 / 操作 | 预期 |
|---|---|---|
| 终端能启动 | `myprogram` | 窗口出现 |
| 应用菜单里有条目 | 打开应用菜单搜索 | 名字和图标都正确 |
| Dock 图标不重复 | 启动后看任务栏 | 只有一个图标，不是两个 |
| 依赖完整 | 换一台干净机器安装 | 不报缺依赖 |
| 卸载干净 | `apt remove` 后 `ls /usr/lib/myprogram` | 目录不存在 |

查看包内容而不安装：

```bash
dpkg-deb --contents ./myprogram_3.1.0_amd64.deb   # 列出文件树和权限
dpkg-deb --info ./myprogram_3.1.0_amd64.deb       # 查看 control 内容
```

**`--contents` 是发布前最后一道自检**——它会显示每个文件的权限位，一眼就能看出 chmod 有没有生效。

---

## 常见问题

| 症状 | 原因 |
|---|---|
| 终端 `Permission denied` | 启动脚本或主程序缺执行位；多半是在 Windows 上打的包 |
| 应用菜单里没有 | `.desktop` 放错目录，或 `Type=`/`Name=` 缺失 |
| 有条目但没图标 | 图标文件名与 `Icon=` 的值不一致，或没放 `apps` 子目录 |
| Dock 里两个图标 | 缺 `StartupWMClass`，或值与实际 WM_CLASS 不符 |
| 装不上，提示缺依赖 | `Depends` 里的包名在该发行版不存在，用 `\|` 补上备选名 |
| 启动闪退无报错 | 缺 `libx11-6` / `libfontconfig1` 等 Avalonia 原生依赖 |

---

## 其他格式

本文只覆盖 `.deb`。其他 Linux 分发格式：

| 格式 | 工具 | 适用 |
|---|---|---|
| `.rpm` | `rpmbuild` | Fedora / RHEL / openSUSE |
| AppImage | `appimagetool` | 免安装单文件，全发行版通用 |
| Flatpak | `flatpak-builder` | 沙箱分发，Flathub 商店 |
| Snap | `snapcraft` | Ubuntu 商店 |

官方也推荐 [Parcel](https://docs.avaloniaui.net/tools/parcel/setup) 自动化产出 `.deb` / `.rpm` / `.zip`，但其 CLI 需付费授权。
