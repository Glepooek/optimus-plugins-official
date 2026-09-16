# avalonia-deb-release

> 版本：1.0.0 | 分类：workflow

将 Avalonia 桌面应用发布为可安装、可验证的 Debian/Ubuntu `.deb` 包；支持已授权的 Parcel 自动化与官方 `dpkg-deb` 手动打包路线。

## 所处层级

```text
┌─────────────┐
│★ workflow   │  avalonia-deb-release（本 skill）
├─────────────┤
│ workflow    │  avalonia（通用开发与官方文档路由）
│ quality     │  avalonia-code-review（发布前 UI 代码审查）
│ platform    │  Avalonia Docs MCP（Parcel 与 Linux 官方资料）
└─────────────┘
```

本 skill 负责 Linux 包发布与验收；`avalonia` 处理通用框架问题，代码质量问题可先交由 `avalonia-code-review`。

## 触发词 / 调用方式

Avalonia 发布、Avalonia Linux 打包、打 deb、Ubuntu 安装包、Debian package、`dpkg-deb`、Parcel、Linux release。

## 业务逻辑流程图

```text
Step 1  收集项目、架构、版本和发行渠道信息
   ↓
Step 2  校验 Linux/WSL 构建环境并选择 Parcel 或手动路线
   ↓
Step 3  发布 linux RID 并生成含桌面集成的 .deb
   ↓
Step 4  静态检查、干净安装、启动、卸载和升级验收
   ↓
Step 5  生成校验和与发布记录；确认后才对外发布
```

## 产出物数据流

输入（`.csproj`、版本、RID、图标、包元数据）→ 本 skill → `packaging/debian/` 或 `.parcel` 配置 → `.deb` / SHA-256 / 验证矩阵 → 人工批准后发布渠道。

## 依赖关系图

```text
┌──────────┐       ┌──────────────────────┐       ┌─────────────────────────┐
│ 用户项目 │ ────▶ │★ avalonia-deb-release│ ────▶ │ .deb + 验证记录 + SHA256│
└──────────┘       └──────────┬───────────┘       └─────────────────────────┘
                               │
                 ┌─────────────┴──────────────┐
                 ▼                            ▼
      Avalonia Docs MCP                Parcel / dpkg-deb
```
