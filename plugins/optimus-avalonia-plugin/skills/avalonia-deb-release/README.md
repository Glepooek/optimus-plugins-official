# avalonia-deb-release

> 版本：2.0.1 | 分类：workflow

把已发布好的 Avalonia Linux 产物打成可安装的 `.deb` 包，并完成命令行与图形界面两种安装验收；不负责 publish、Parcel 或对外发布。

## 所处层级

```text
┌─────────────┐
│★ workflow   │  avalonia-deb-release（本 skill）
├─────────────┤
│ workflow    │  avalonia（通用开发与官方文档路由）
│ quality     │  avalonia-code-review（打包前 UI 代码审查）
└─────────────┘
```

本 skill 只负责"从已发布产物到能装上并跑起来"这一段；`dotnet publish`、发布策略、对外发布确认均不在范围内，交由用户或其他流程完成。

## 触发词 / 调用方式

Avalonia Linux 打包、打 deb、Ubuntu 安装包、Debian package、`dpkg-deb`。

## 业务逻辑流程图

```text
Step 1  确认 Linux 环境与 dpkg-deb 已就绪
   ↓
Step 2  收集并校验产物目录、图标、.desktop、产出目录
   ↓
Step 3  调用自带的 scripts/build-deb.sh 执行打包
   ↓
Step 4  命令行安装验收 + 图形界面安装验收 + 卸载验证
```

## 产出物数据流

输入（待打包产物目录、图标、`.desktop` 落盘路径、产出目录）→ 本 skill 调用自带 `scripts/build-deb.sh` → `.deb` → 命令行/图形安装验收结果 → 用户接手后续发布。

## 依赖关系图

```text
┌──────────┐       ┌──────────────────────┐       ┌─────────────────────────┐
│ 已发布产物│ ────▶ │★ avalonia-deb-release│ ────▶ │ .deb + 安装验收结果    │
└──────────┘       └──────────┬───────────┘       └─────────────────────────┘
                               │
                               ▼
                          dpkg-deb
```
