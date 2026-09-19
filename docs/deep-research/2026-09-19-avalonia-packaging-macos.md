# Avalonia macOS 打包详解（.app / .dmg / .pkg）

> 2026-09-19 · 依据 [Avalonia macOS Deployment](https://docs.avaloniaui.net/docs/deployment/macos)
> 配套：[Linux 打包详解](2026-09-19-avalonia-packaging-linux.md) · [跨平台编译总览](2026-09-19-avalonia-cross-platform-packaging.md)

## 打包在做什么

macOS 分发比 Linux 多两层强制要求：**应用必须是 `.app` 包结构**，而且**必须经过签名和公证**，否则 Gatekeeper 会直接拦下，用户看到「无法打开，因为无法验证开发者」。

完整链路六步：

```
dotnet publish → 组装 .app → 签名 → 公证 → 装订 ticket → 封装 .dmg/.pkg
                              └─────── 需要 Apple 开发者账号（$99/年）───────┘
```

⚠️ **公证是强制的**。macOS 10.15 (Catalina) 起，所有非 App Store 分发的应用都必须公证。这不是「最好做一下」，是「不做就没人能装」。

---

## 第一步：dotnet publish

```bash
dotnet publish -r osx-x64 --configuration Release -p:UseAppHost=true
```

### `-p:UseAppHost=true` 是必需的，不是可选的

官方原文加粗强调：

> **You need this file to be generated in order for your `.app` to function properly.**

`UseAppHost` 控制是否生成**原生可执行文件**（无扩展名的 `MyApp`）。最近的 .NET 版本有时不生成它，导致 publish 目录里只有 `MyApp.dll` 而没有 `MyApp`。`.app` 包必须有一个原生可执行文件供 macOS 拉起，只有 dll 是启动不了的。

也可以写进 csproj，更稳妥：

```xml
<PropertyGroup>
  <UseAppHost>true</UseAppHost>
  <RuntimeIdentifiers>osx-x64;osx-arm64</RuntimeIdentifiers>
</PropertyGroup>
```

### 自检

publish 目录里**必须同时有** `MyApp`（无扩展名的原生可执行文件）和 `MyApp.dll`（托管程序集）。缺任何一个都说明生成不正常，补 `UseAppHost` 重跑。

> 官方在此处的措辞是「do not have both a `MyApp` (executable) and a `MyApp.dll`, things are probably not generating properly」。这句话脱离上下文读容易理解反——它的意思是「**如果你没有同时拿到**这两个文件，就是出问题了」，不是「不要同时有这两个文件」。同页上文明确写着 *Both an extension-less executable and its DLL must exist*。

### 可选参数

| 参数 | 作用 |
|---|---|
| `-p:PublishSingleFile=true` | 把 dll 合并成单文件，**大幅简化签名**——签名要逐个文件签，文件少了流程短很多 |
| `<RuntimeIdentifiers>` | 报「找不到 osx-64 目标」时在 csproj 里加，多个 RID 用分号分隔 |

---

## 第二步：.app 包结构

`.app` 不是压缩包，**就是一个普通目录**，只是 macOS 的 Finder 把它渲染成单个可双击的图标。

```
MyProgram.app/
└── Contents/
    ├── Info.plist                   ← 清单文件，必需
    ├── MacOS/                       ← dotnet publish 的全部产物
    │   ├── MyProgram                ← 原生可执行文件（Info.plist 里 CFBundleExecutable 指向它）
    │   ├── MyProgram.dll
    │   └── Avalonia.dll
    ├── Resources/
    │   └── MyProgramIcon.icns       ← 图标
    ├── _CodeSignature/
    │   └── CodeResources            ← 签名后自动生成，不要手动创建
    └── embedded.provisionprofile    ← 仅 App Store 分发需要
```

各部分职责：

| 路径 | 作用 | 何时出现 |
|---|---|---|
| `Contents/Info.plist` | 包清单：标识符、版本、可执行文件名、图标名 | **必需**，手工提供 |
| `Contents/MacOS/` | 存放 publish 产物和原生可执行文件 | **必需**，手工填充 |
| `Contents/Resources/` | 图标及其他资源文件 | 手工填充 |
| `Contents/_CodeSignature/` | 存放签名信息（`CodeResources` 是各文件的哈希清单） | **`codesign` 自动生成** |
| `Contents/embedded.provisionprofile` | 配置描述文件，含签名信息 | 仅 App Store 路线 |
| `Contents/Frameworks/` | 存放 `.dylib` | 仅 App Store 路线要求 |

⚠️ **`_CodeSignature/` 不要手动建**。它由 `codesign` 生成，内容是包内每个文件的哈希。手动放东西进去会导致签名校验失败。

---

## 第三步：Info.plist

`Contents/Info.plist` 是一份 XML 属性列表，macOS 靠它认识这个应用。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIconFile</key>
    <string>myicon-logo.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.identifier</string>
    <key>CFBundleName</key>
    <string>MyApp</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
    <key>CFBundleExecutable</key>
    <string>MyApp.Avalonia</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
```

逐键说明：

| 键 | 作用 | 约束 |
|---|---|---|
| `CFBundleExecutable` | 指向 `Contents/MacOS/` 里要启动的文件 | **必须与 publish 产出的可执行文件名完全一致**（程序集名去掉 `.dll`）。写错 = 双击无反应 |
| `CFBundleName` | 显示名称 | **最多 15 个字符**，超了要配合 `CFBundleDisplayName` |
| `CFBundleDisplayName` | 长显示名 | 仅当 `CFBundleName` 超 15 字符时才需要 |
| `CFBundleIconFile` | 图标文件名 | **要带 `.icns` 扩展名**，文件放 `Contents/Resources/` |
| `CFBundleIdentifier` | 全局唯一标识，反向 DNS 格式 | 如 `com.mycompany.myapp`。**签名、公证、沙箱、偏好设置存储都靠它**，定了就别改 |
| `NSHighResolutionCapable` | Retina 支持开关 | 填 `<true/>`。**不填会导致在 Retina 屏上模糊** |
| `CFBundleVersion` | 内部构建号 | 每次提交 App Store 必须递增 |
| `CFBundleShortVersionString` | 用户可见版本号 | 「关于」窗口里显示的就是它 |
| `LSMinimumSystemVersion` | 最低系统版本要求 | 低于此版本的 macOS 拒绝启动。⚠️ 官方示例填的 `10.12` 已经过时——**要填你所用 .NET 版本实际支持的最低 macOS 版本**，填低了等于向用户承诺一个跑不起来的兼容性 |
| `CFBundlePackageType` | 包类型 | 应用固定填 `APPL` |
| `CFBundleInfoDictionaryVersion` | plist 格式版本 | 固定填 `6.0` |

### 两组容易混淆的键

**`CFBundleVersion` vs `CFBundleShortVersionString`**

| | 用途 | 用户可见 |
|---|---|---|
| `CFBundleVersion` | 构建号，App Store 用来区分同一版本的多次提交 | 否 |
| `CFBundleShortVersionString` | 语义化版本号，如 `1.4.2` | 是 |

自行分发时两者填一样即可；提交 App Store 时 `CFBundleVersion` 每次必须比上次大。

**`CFBundleName` vs `CFBundleDisplayName`**

`CFBundleName` 有 15 字符硬限制（Finder 菜单栏空间限制）。名字短就只填它；名字长填 `CFBundleName` 为缩写、`CFBundleDisplayName` 为全称。

> 官方建议用 Xcode 编辑 plist，「as it has auto-completion for all properties」。完整键列表见 [Apple Information Property List 参考](https://developer.apple.com/documentation/bundleresources/information-property-list)。

---

## 第四步：图标（.icns）

| 项 | 要求 |
|---|---|
| 格式 | `.icns`（Apple 图标集容器格式，**一个文件内含多个尺寸**） |
| 位置 | `Contents/Resources/` |
| 文件名 | 必须与 `Info.plist` 的 `CFBundleIconFile` 一致，**含扩展名** |
| 尺寸档位 | 16 / 32 / 128 / 256 / 512 五档，每档各一份 1× 和 2×（详见下表） |

`.icns` 与 Linux 的 PNG 不同——它不是单张图，而是**一个容器**，内部打包了多个尺寸的位图。macOS 在不同场景（Dock、Finder 列表、快速查看）自动取合适的那张。

### iconset 的标准文件名

`iconutil` 只认这 10 个固定文件名，多了会被忽略，少了对应场景会降级用别的尺寸缩放：

| 文件名 | 实际像素 |
|---|---|
| `icon_16x16.png` | 16×16 |
| `icon_16x16@2x.png` | 32×32 |
| `icon_32x32.png` | 32×32 |
| `icon_32x32@2x.png` | 64×64 |
| `icon_128x128.png` | 128×128 |
| `icon_128x128@2x.png` | 256×256 |
| `icon_256x256.png` | 256×256 |
| `icon_256x256@2x.png` | 512×512 |
| `icon_512x512.png` | 512×512 |
| `icon_512x512@2x.png` | 1024×1024 |

⚠️ **没有 `icon_64x64.png` 这一档**。64×64 由 `icon_32x32@2x.png` 提供——`@2x` 后缀表示「逻辑尺寸 32pt 在 Retina 下的 2 倍位图」，文件名里的数字是逻辑尺寸不是像素数。这是最容易搞错的地方。

### 不用 Mac 也能生成

官方明确说：

> This type of icon file can be created not only on Apple devices but also on Linux devices.

并链接了 [Creating macOS Icons (icns) on Linux](https://dentrassi.de/2014/02/25/creating-mac-os-x-icons-icns-on-linux/)。

常用工具：

| 平台 | 工具 |
|---|---|
| macOS | `iconutil -c icns MyIcon.iconset` |
| Linux / Windows | `png2icns`（icnsutils 包）、ImageMagick `convert` |
| 任意 | 在线转换服务 |

macOS 原生做法是先建一个 `MyIcon.iconset/` 目录，按上表命名放入各尺寸 PNG，再用 `iconutil` 打成 `.icns`。

---

## 第五步：组装 .app

```bash
#!/bin/bash

APP_NAME="/path/to/your/output/MyApp.app"
# 指向 dotnet publish 的输出目录，注意结尾的 /.
# 例如 /path/to/your/csproj/bin/Release/net10.0/osx-x64/publish/.
PUBLISH_OUTPUT_DIRECTORY="/path/to/your/publish/output/net10.0/osx-x64/publish/."
INFO_PLIST="/path/to/your/Info.plist"
ICON_FILE="/path/to/your/myapp-logo.icns"

# 清掉上次的产物，避免残留文件被打进包里
if [ -d "$APP_NAME" ]
then
    rm -rf "$APP_NAME"
fi

# 建三层目录
mkdir "$APP_NAME"
mkdir "$APP_NAME/Contents"
mkdir "$APP_NAME/Contents/MacOS"
mkdir "$APP_NAME/Contents/Resources"

# 放清单和图标
cp "$INFO_PLIST" "$APP_NAME/Contents/Info.plist"
cp "$ICON_FILE" "$APP_NAME/Contents/Resources/$(basename "$ICON_FILE")"

# 拷贝 publish 产物，-a 保留权限位和符号链接
cp -a "$PUBLISH_OUTPUT_DIRECTORY" "$APP_NAME/Contents/MacOS"
```

🔴 **这里与官方脚本有一处刻意的改动。** 官方原文写的是：

```bash
cp "$ICON_FILE" "$APP_NAME/Contents/Resources/$ICON_FILE"
```

而 `$ICON_FILE` 是绝对路径（`/path/to/your/myapp-logo.icns`），拼接后目标变成 `.../Contents/Resources//path/to/your/myapp-logo.icns`——**该目录不存在，`cp` 必然报错**。本文用 `$(basename "$ICON_FILE")` 取文件名修正。照抄官方原版会在这一步卡住。

三个易错点：

| 位置 | 说明 |
|---|---|
| `PUBLISH_OUTPUT_DIRECTORY` 结尾的 `/.` | **不能省**。`cp -a src/. dst` 拷贝的是目录**内容**；`cp -a src dst` 拷贝的是目录**本身**，会多套一层 |
| `cp -a` 而非 `cp` | `-a` 保留权限位、时间戳和符号链接。用普通 `cp` 会丢执行位，应用启动不了 |
| 先 `rm -rf` | 不清理的话，上一版残留的文件会留在包里，签名时被一起签进去 |

⚠️ **如果在 Windows（非 WSL）上组装**，必须在 Unix 机器上补一条（`MyApp` 换成 `CFBundleExecutable` 里写的那个名字）：

```bash
chmod +x MyApp.app/Contents/MacOS/MyApp
```

官方原文：不做这步「the app will not start on macOS」。

---

## 第六步：开发者证书

没有证书，`codesign` 无从签起，官方原话是「distribution is impossible」。

### 获取流程

1. 加入 [Apple Developer Program](https://developer.apple.com/programs/)（**$99/年**）
2. Xcode → Settings → Accounts → **Download Manual Profiles**
   - 为什么走这条路：Xcode 默认用云端托管证书，官方说它「can be awkward to use with .NET command line tooling」
3. 导出为带密码的 `.p12` 文件
4. 团队成员导入：Keychain Access → File → Import Items

### 验证证书已就位

```bash
security find-identity -v
```

输出里身份名称后**括号里的就是 Team ID**，公证时要用。

### 按分发渠道选证书

| 渠道 | 签应用包 | 签 `.pkg` | 公证 |
|---|---|---|---|
| 商店外直接分发 | **Developer ID Application** | **Developer ID Installer** | 必须 |
| Mac App Store | **Apple Distribution** | **Mac Installer Distribution** | **必须关闭** |

🔴 **两类证书不能互换用途**：应用证书签不了 PKG，安装器证书签不了应用包。用错会在公证或审核阶段被拒。

---

## 第七步：签名

### entitlements 文件

先准备一份权限声明 `entitlements.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
```

| entitlement | 作用 | 必需性 |
|---|---|---|
| `com.apple.security.cs.allow-jit` | 允许 JIT 编译 | **Avalonia 必需**。.NET 运行时依赖 JIT，hardened runtime 默认禁止，不开则应用直接崩溃 |
| `com.apple.security.automation.apple-events` | 允许发送 Apple Events | 建议。官方说它「fixes an error that shows up in `Console.app`」 |

⚠️ 官方警告：微软文档里建议的其他 entitlement「may impose security risks」，**不要无脑全加**。每多开一项就多一个攻击面，公证审核也可能因此被质疑。

### 签名命令

```bash
codesign --force --timestamp --options=runtime \
         --entitlements "$ENTITLEMENTS" \
         --sign "$SIGNING_IDENTITY" "$fname"
```

| 参数 | 作用 |
|---|---|
| `--force` | 覆盖已有签名 |
| `--timestamp` | 加可信时间戳。**证书过期后已签名的应用仍然有效**，不加则证书一过期全部失效 |
| `--options=runtime` | **启用 hardened runtime**。Apple 要求所有公证应用必须开启 |
| `--entitlements` | 指定权限声明文件 |
| `--sign` | 证书身份，即 `security find-identity` 输出的名称 |

### 签名顺序：先内后外

```bash
# 1. 先逐个签 Contents/MacOS 下的每个文件
#    -print0 + read -d '' 组合用于正确处理含空格的文件名
find "MyApp.app/Contents/MacOS" -type f -print0 | while IFS= read -r -d '' fname; do
    codesign --force --timestamp --options=runtime \
             --entitlements "$ENTITLEMENTS" \
             --sign "$SIGNING_IDENTITY" "$fname"
done

# 2. 最后签整个 bundle
codesign --force --timestamp --options=runtime \
         --entitlements "$ENTITLEMENTS" \
         --sign "$SIGNING_IDENTITY" "MyApp.app"
```

⚠️ 循环里不要写成 `find ... | while read fname`——文件名含空格时会被拆成多个词，漏签的文件要到公证阶段才暴露。`-print0` 配 `read -r -d ''` 用 NUL 作分隔符，是唯一可靠的写法。

🔴 **不要用 `--deep`。** 官方引用 Apple 的建议：`--deep`「can leave nested binaries improperly signed」——它看似能一条命令递归签完，实际会漏签或错签嵌套二进制，问题要到公证时才暴露。**显式逐个签，最后签 bundle。**

### 验证签名

```bash
codesign --verify --verbose /path/to/MyApp.app
```

### 什么是 hardened runtime

一套运行时限制策略，禁止代码注入、禁止加载未签名的库、禁止 DYLD 环境变量劫持——除非你用 entitlement 显式开口子。**Apple 要求所有公证应用必须开启**，这就是为什么 `--options=runtime` 和 `allow-jit` 是绑定出现的：开了 hardened runtime 就禁 JIT，而 .NET 需要 JIT，所以必须用 entitlement 开回来。

---

## 第八步：公证与装订

公证是 Apple 的**自动化安全扫描**（不是人工审核），通过后 Apple 签发一张 ticket，macOS 在启动应用时校验它。

### 存凭据

```bash
xcrun notarytool store-credentials "AC_PASSWORD" \
  --apple-id "you@example.com" \
  --team-id "YOURTEAMID" \
  --password "your-app-specific-password"
```

⚠️ **`--password` 要的是 App 专用密码，不是 Apple ID 登录密码。** 因为账号开了双重认证，Notary API 无法走普通密码。去 [appleid.apple.com](https://appleid.apple.com) 生成。

`"AC_PASSWORD"` 是你给这份凭据起的名字，后续命令用它引用。

### 打包成 zip

```bash
ditto -c -k --sequesterRsrc --keepParent MyApp.app MyApp.zip
```

🔴 **必须用 `ditto`，不能用 `zip`。** 官方原文：`zip`「can cause notarization issues」。

| 参数 | 作用 |
|---|---|
| `-c` | 创建归档 |
| `-k` | 使用 PKZip 格式 |
| `--sequesterRsrc` | **保留 macOS 资源分支和扩展属性**，这是 `zip` 做不到的关键点 |
| `--keepParent` | 保留 `.app` 这一层目录，否则解压出来是散文件 |

### 提交公证

```bash
xcrun notarytool submit MyApp.zip --keychain-profile "AC_PASSWORD" --wait
```

`--wait` 会轮询直到出结果，官方说「no separate status check is needed」。

失败时查日志：

```bash
xcrun notarytool log <submission-id> --keychain-profile "AC_PASSWORD"
```

⚠️ 旧的 `altool --notarize-app` 流程「has been retired by Apple and no longer works」——网上大量教程还在用它，全部失效。

### 装订 ticket

```bash
xcrun stapler staple MyApp.app
xcrun stapler validate MyApp.app
```

**装订的意义**：把公证 ticket 写进应用包内。不装订的话，用户首次启动时 macOS 要联网向 Apple 查询——**离线环境下会被拦截**。装订后离线也能验证通过。

---

## 第九步：封装分发格式

### DMG（推荐用于直接分发）

DMG 是磁盘映像，双击挂载后用户把应用拖进 Applications 文件夹，是 macOS 最常见的分发形式。

⚠️ **DMG 需要额外公证一遍**，流程是套娃式的：

```
1. 签名 .app
2. 把 .app 打成 zip → 提交公证 → 装订到 .app 上
3. 创建 .dmg，把已装订的 .app 放进去
4. 把 .dmg 再提交一次公证
5. 装订到 .dmg 上
```

创建 DMG（`hdiutil` 是 macOS 自带工具）：

```bash
# 准备一个目录，放入已装订的 .app 和 Applications 的软链接
mkdir -p dmg-root
cp -a MyApp.app dmg-root/
ln -s /Applications dmg-root/Applications      # 让用户能直接拖进去

hdiutil create -volname "MyApp" \
               -srcfolder dmg-root \
               -ov -format UDZO \
               MyApp.dmg
```

| 参数 | 作用 |
|---|---|
| `-volname` | 挂载后在 Finder 侧边栏显示的卷名 |
| `-srcfolder` | 要打进映像的目录 |
| `-ov` | 覆盖已存在的输出文件 |
| `-format UDZO` | 压缩只读映像，分发用的标准格式 |

`ln -s /Applications` 那行是惯例做法：挂载后窗口里同时出现应用图标和 Applications 文件夹，用户拖一下就完成安装。

然后公证 DMG：

```bash
xcrun notarytool submit MyApp.dmg --keychain-profile "AC_PASSWORD" --wait
xcrun stapler staple MyApp.dmg
```

**为什么要两次**：第一次让 `.app` 本身获得 ticket（用户从 dmg 拖出来后仍然有效），第二次让 `.dmg` 文件本身通过 Gatekeeper（否则下载 dmg 时就被拦）。

> 官方文档只写了「把已装订的 app 放进 dmg，再用同一条 `notarytool submit` 提交 dmg」，未给出创建 dmg 的命令。上面的 `hdiutil` 用法与美化排版参数（窗口尺寸、图标坐标）属 macOS 通用实践，不在 Avalonia 文档覆盖范围内。

### PKG（用于托管安装或 App Store）

```bash
productbuild --component App/AppName.app /Applications \
             --sign "$INSTALLER_SIGNING_IDENTITY" AppName.pkg
```

注意用的是 **Installer 证书**，不是 Application 证书。

### ZIP（最简单）

直接分发 `.app` 的 zip 包，无安装流程。适合内部分发。用 `ditto` 打包以保留权限。

---

## App Store 路线的额外要求

走 Mac App Store 的约束比直接分发严格得多：

### 文件摆放规则

Apple 对包内文件位置有硬性规定：

| 文件类型 | 必须放在 | 原因 |
|---|---|---|
| `.dll` | `Contents/Resources/` | 「`.dll` files are not considered code by Apple」，**无需签名** |
| mach-o 可执行文件 | `Contents/MacOS/` | 该目录只允许放可执行文件 |
| 其他 mach-o `.dylib` | `Contents/Frameworks/` | 动态库的规定位置 |

可以用相对符号链接打通（`ln -s fromFile toFile`），但官方提醒：**优先让程序直接访问 `Resources/`**，因为符号链接在沙箱下「might get I/O access issues」。

### 瘦身

官方要求用 `lipo` 剥掉 `.dylib` 里非 ARM/x64 的架构切片。先看某个库里有哪些架构：

```bash
lipo -info libSkiaSharp.dylib
# 输出示例：Architectures in the fat file: libSkiaSharp.dylib are: x86_64 arm64
```

再剥掉不需要的那个：

```bash
lipo -remove x86_64 libSkiaSharp.dylib -output libSkiaSharp.dylib   # 只保留 arm64
```

> 官方只提到「Strip non-ARM/x64 slices from `.dylib` files using `lipo`」，未给具体命令。上面是 `lipo` 的标准用法。

### 两套 entitlements

| 对象 | entitlements |
|---|---|
| 辅助进程 | `app-sandbox` + `inherit` |
| 主包 | 额外加 `allow-unsigned-executable-memory`、`disable-library-validation`、`allow-dyld-environment-variables`，以及对 `com.apple.coreservices.launchservicesd` 的 mach-lookup 例外 |

可选项覆盖网络客户端/服务端、Apple Events、用户选择的文件、文档作用域书签、App Group。

### 其他

- 需通过人工审核与 HIG 合规检查
- 在 App Store Connect 注册应用
- 用 **Transporter** 上传 `.pkg`
- 需要配置描述文件（provisioning profile）
- 必须开启沙箱
- **必须关闭公证**（App Store 路线由 Apple 内部处理）

---

## CI 自动化（GitHub Actions）

跑在 `macos-latest` runner 上，关键步骤：

```yaml
runs-on: macos-latest
steps:
  # 1. 创建并解锁临时 keychain
  # 2. 把 base64 编码的 .p12 secret 解码落盘
  # 3. 导入证书，注意 -T /usr/bin/codesign 授权 codesign 使用
  - run: security import cert.p12 -T /usr/bin/codesign ...

  # 4. 关键：避免签名时弹授权框
  - run: security set-key-partition-list -S apple-tool:,apple:,codesign: ...

  # 5. 直接 publish 到 .app 结构里
  - run: dotnet publish -o "$RUNNER_TEMP/MyApp.app/Contents/MacOS"

  # 6. 逐文件签 → 签 bundle → ditto → notarytool submit → stapler staple
```

🔴 **`security set-key-partition-list` 这步容易漏**。官方注释：「To prevent authorisation prompt popups during code signing」——不加这条，CI 会卡在一个没人能点的 GUI 授权框上直到超时。

### 验证签名是否真的生效

官方给了个巧妙的办法：**通过邮件或 WeTransfer 下载一次应用**，触发 macOS 的隔离属性（quarantine）。如果签名和公证都正确，你会看到系统提示「未发现恶意软件」。

直接本地拷贝的文件不带隔离属性，**测不出 Gatekeeper 问题**。

---

## 常见问题

| 症状 | 原因 |
|---|---|
| 双击无反应 | `CFBundleExecutable` 与实际文件名不符；或缺执行位（Windows 上组装的） |
| publish 目录里没有无扩展名的可执行文件 | 忘了 `-p:UseAppHost=true` |
| Retina 屏上界面模糊 | `Info.plist` 缺 `NSHighResolutionCapable` |
| 启动即崩溃，无报错 | hardened runtime 开了但缺 `allow-jit` entitlement |
| 公证失败，日志报签名问题 | 用了 `--deep`，嵌套二进制未正确签名 |
| 公证失败，报归档格式问题 | 用了 `zip` 而非 `ditto` |
| 离线环境下仍被 Gatekeeper 拦 | 忘了 `stapler staple` |
| 下载 DMG 就被拦 | 只公证了 `.app`，没公证 `.dmg` |
| CI 卡住直到超时 | 缺 `security set-key-partition-list` |
| App Store 提交被拒 | 用了 Developer ID 证书而非 Apple Distribution |

---

## 完整检查清单

- [ ] csproj 里有 `<UseAppHost>true</UseAppHost>` 和 `<RuntimeIdentifiers>`
- [ ] publish 产物同时含 `MyApp` 和 `MyApp.dll`
- [ ] `Info.plist` 的 `CFBundleExecutable` 与实际文件名逐字一致
- [ ] `Info.plist` 有 `NSHighResolutionCapable = true`
- [ ] `CFBundleIconFile` 带 `.icns` 扩展名，文件在 `Contents/Resources/`
- [ ] `CFBundleIdentifier` 是反向 DNS 且全局唯一
- [ ] entitlements 含 `com.apple.security.cs.allow-jit`
- [ ] 签名用 `--options=runtime --timestamp`，**未用 `--deep`**
- [ ] 逐文件签完再签 bundle
- [ ] 用 `ditto` 而非 `zip` 打包
- [ ] 公证后执行了 `stapler staple`
- [ ] 分发 DMG 的话，`.app` 和 `.dmg` 各公证一次
- [ ] 通过网络下载测试过，确认无 Gatekeeper 拦截

---

## 自动化替代

官方推荐 [Parcel](https://docs.avaloniaui.net/tools/parcel/setup)，可自动完成包结构、`Info.plist` 生成、签名、公证、DMG 创建。支持 `dmg` / `pkg` / `zip`，并可合并 x64 与 arm64 为通用二进制（`merge-mac`）。

🔴 Parcel CLI 需 Avalonia Plus 及以上授权，免费 Community 版只有 GUI。
