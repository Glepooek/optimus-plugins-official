# Sysmon

**v15.21（2026-06-17）** · 官方页：https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon

> **纯 CLI 工具（配置与安装），无 GUI。** 事件在**事件查看器**中查看，不是 Sysmon 自带界面。

## 定位与边界

**常驻的 Windows 系统服务 + 设备驱动组合**，跨重启持续把系统活动写入 Windows 事件日志。

官方明确说明两点边界：**Sysmon 本身不做事件分析，也不隐藏自身。** 它只是高质量的日志生产者，分析要靠 SIEM / Windows 事件转发 / 自建脚本。

**与 Procmon 的分工是本目录最重要的概念分野：**

| 维度 | Sysmon | [Procmon](procmon-gui.md) |
|---|---|---|
| 形态 | 常驻服务 + 驱动 | 交互式应用 |
| 时间尺度 | 长期（数天/数月） | 短时（秒/分钟） |
| 事件粒度 | 精选的安全相关事件（约 30 类） | 全量文件/注册表/进程操作（每秒数千条） |
| 输出 | Windows 事件日志 | PML 文件 / 界面 |
| 回答的问题 | **「昨天发生过什么」** | **「现在正在发生什么」** |
| 部署方式 | 批量铺开、常驻 | 临时运行、用完即走 |

**两者不是替代关系** —— 混用才能覆盖两个时间尺度。

## 命令行开关（只有 5 个）

| 开关 | 说明 |
|---|---|
| `-i [配置文件]` | **安装**服务与驱动，可带配置文件 |
| `-c [配置文件]` | **更新配置**；不带参数则**转储当前配置** |
| `-m` | 安装事件清单（`-i` 时已自动执行） |
| `-s` | 打印配置 schema 定义 |
| `-u [force]` | **卸载**服务与驱动。`-u force` 强制卸载 |
| `-accepteula` | **必需**，免交互接受 EULA |
| `-nologo` / `-nobanner` | 抑制横幅 |

**安装与卸载均不需要重启。**

```powershell
# 安装（带配置）
Sysmon64.exe -accepteula -i C:\sysmon\config.xml

# 更新配置（不重装）
Sysmon64.exe -c C:\sysmon\config.xml

# 转储当前生效的配置（排查「配置有没有生效」）
Sysmon64.exe -c

# 查询当前 schema 版本
Sysmon64.exe -s

# 卸载
Sysmon64.exe -u
Sysmon64.exe -u force      # 强制
```

## 事件在哪看

**事件写入：**

```
事件查看器 → 应用程序和服务日志 → Microsoft → Windows → Sysmon → Operational
```

（旧系统写入 System 日志。）

**时间戳为 UTC** —— 与本地时间对比时要换算，这是分析时最容易出错的地方。

**驱动以 boot-start 驱动安装，可捕获启动早期活动** —— 这是它相对用户态日志方案的关键优势。

```powershell
# PowerShell 读取（比事件查看器适合脚本化）
Get-WinEvent -LogName 'Microsoft-Windows-Sysmon/Operational' -MaxEvents 50

# 只看进程创建（Event ID 1）
Get-WinEvent -FilterHashtable @{
  LogName = 'Microsoft-Windows-Sysmon/Operational'; ID = 1
} -MaxEvents 20 | Format-List TimeCreated, Message
```

## 默认关闭的高价值事件（重要）

**几个最有价值的事件默认关闭，且官方对日志量有明确警示：**

| Event ID | 事件 | 默认状态 | 官方警示 |
|---|---|---|---|
| **3** | 网络连接 | **默认禁用** | — |
| **7** | Image loaded（DLL 加载） | **默认禁用**，需 `-l` 开启 | **全量采集会产生大量日志** |
| **10** | ProcessAccess | 需配置 | **需配合过滤器否则日志暴涨** |
| **23** | FileDelete | — | 会把删除的文件**另存到 ArchiveDirectory**（默认 `C:\Sysmon`），**目录可能膨胀到不合理大小** |

**这四个是部署 Sysmon 时最容易踩坑的地方：**

- **不开 Event ID 3** → 事后无法追溯网络连接，而这往往是应急响应最需要的
- **无过滤开 Event ID 7** → 日志几小时就把磁盘写满（每个进程加载几十个 DLL）
- **无过滤开 Event ID 10** → 同上，且正常的杀软/监控软件会大量触发
- **开 Event ID 23 不管 ArchiveDirectory** → `C:\Sysmon` 无限增长，最终占满系统盘

**Event ID 23 的取舍：** 它能保留被删除的文件（勒索软件取证的关键），但代价是磁盘。生产环境必须配窄的 include 规则（只归档特定扩展名/路径），并做定期清理。

## 配置文件规则语义

**这是写 Sysmon 配置最容易出错的地方，官方语义如下：**

| 规则 | 语义 |
|---|---|
| **同字段多条规则** | **OR** |
| **不同字段之间** | **AND** |
| **exclude 优先于 include** | exclude 命中即排除，不管 include 是否也命中 |
| `RuleGroup` 的 `groupRelation` | 可显式改为 `and` / `or` |

```xml
<Sysmon schemaversion="4.82">
  <EventFiltering>
    <!-- 同字段多条 = OR：命中任一即匹配 -->
    <RuleGroup groupRelation="or">
      <ProcessCreate onmatch="include">
        <Image condition="end with">powershell.exe</Image>
        <Image condition="end with">cmd.exe</Image>
      </ProcessCreate>
    </RuleGroup>

    <!-- 不同字段 = AND：需同时满足 -->
    <RuleGroup groupRelation="and">
      <NetworkConnect onmatch="include">
        <Image condition="end with">YourApp.exe</Image>
        <DestinationPort condition="is">443</DestinationPort>
      </NetworkConnect>
    </RuleGroup>

    <!-- exclude 优先：即使上面 include 命中，这里命中也会被排除 -->
    <ImageLoad onmatch="exclude">
      <Signature condition="contains">Microsoft Windows</Signature>
    </ImageLoad>
  </EventFiltering>
</Sysmon>
```

**降噪的正确姿势是 exclude 已知良性**（微软签名的模块、已知的监控软件），而不是 include 少数可疑项 —— 后者会漏掉未知威胁。

### schemaversion 与二进制版本独立

**配置文件的 `schemaversion`（示例中为 4.82）与 Sysmon 二进制版本号相互独立。** 用 `-s` 查询当前支持的 schema 版本：

```powershell
Sysmon64.exe -s
```

**升级 Sysmon 后旧配置通常仍可用**（schema 向后兼容），但新功能需要更高的 schemaversion。写死一个过高的版本号会导致配置加载失败。

## 部署实践

```powershell
# 单机安装
Sysmon64.exe -accepteula -i C:\sysmon\config.xml

# 验证配置真的生效了（最重要的一步）
Sysmon64.exe -c > C:\sysmon\effective-config.txt

# 确认服务与驱动状态
Get-Service Sysmon64
Get-WinEvent -LogName 'Microsoft-Windows-Sysmon/Operational' -MaxEvents 1

# 调整日志通道大小（默认可能太小，事件被快速覆盖）
wevtutil sl Microsoft-Windows-Sysmon/Operational /ms:1073741824   # 1 GB
```

**`Sysmon64.exe -c`（无参数）转储当前生效配置是最重要的排查手段** —— 「我改了配置为什么没生效」几乎总能靠它定位（改了文件但没执行 `-c`，或 XML 语法错误导致回退）。

### 配置模板来源

不要从零写配置。社区维护的成熟模板：

- **SwiftOnSecurity/sysmon-config** —— 经典基线，注释详尽
- **olafhartong/sysmon-modular** —— 模块化，按 ATT&CK 技术组织

这些不是微软官方产物，使用前应审阅其 exclude 规则是否符合你的环境（有些 exclude 可能过宽，被攻击者利用）。

## 高负载韧性

**v15.2（2026-03-26）改进了内部事件队列处理，使服务在高系统负载下对事件丢弃更具韧性。**

即：旧版本在系统繁忙时可能丢事件。如果你依赖 Sysmon 做合规审计，**应升级到 v15.2 以上**。

## 安全属性

**Sysmon 服务以「受保护进程」运行** —— 提升了被攻击者停止/篡改的门槛。

但**官方明确说明 Sysmon 不隐藏自身**：攻击者能看到它在运行（服务名、驱动名、事件日志通道都是默认值）。有对抗需求时可在安装时改服务名与驱动名（`-i` 时的高级用法，本篇未覆盖）。

## 常见坑

1. **Event ID 3（网络连接）默认禁用。** 应急响应最需要的数据默认没有。
2. **Event ID 7（DLL 加载）无过滤会写满磁盘。** 官方明确警示。
3. **Event ID 10（ProcessAccess）必须配过滤器。** 否则日志暴涨。
4. **Event ID 23（FileDelete）的 ArchiveDirectory 会无限增长。** 默认 `C:\Sysmon`，官方警示「可能膨胀到不合理大小」。
5. **时间戳是 UTC。** 与本地时间对比要换算。
6. **exclude 优先于 include。** 写规则时容易搞反导致预期事件被排除。
7. **改了配置文件不等于生效。** 必须执行 `-c`，并用 `-c`（无参数）验证。
8. **schemaversion 与二进制版本独立。** 写死过高版本会导致加载失败，用 `-s` 查。
9. **默认日志通道可能太小。** 事件被快速覆盖，用 `wevtutil sl` 调大。
10. **不做分析。** Sysmon 只产生日志，需要 SIEM 或自建脚本消费。
11. **不隐藏自身。** 攻击者可发现并尝试停止（受保护进程提高了门槛但非不可能）。
12. **生产环境无 SLA。** 官方 EULA 责任上限 5 美元直接损失 —— 长期驻留出问题无官方兜底。
13. **v15.2 前高负载可能丢事件。** 合规审计场景应升级。

## 分发

```
Sysmon.exe    6,258,072   x86      Sysmon64.exe   3,250,120   x64
（ARM64 为 Sysmon64a.exe）
```

winget 包名 `Microsoft.Sysinternals.Sysmon`。
另有 Sysmon for Linux（GitHub `microsoft/SysmonForLinux`，配置与事件不完全通用）。

## 官方文档

- 工具页：https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon（Published 2026-06-17）
- **工具自带：`Sysmon64.exe -?` 与 `-? config`** 输出完整开关与配置说明
- schema：`Sysmon64.exe -s`

> **本篇事实边界：** 5 个核心开关及语义、安装卸载不需重启、`-accepteula` 必需、事件通道路径与 UTC 时间戳、boot-start 驱动、受保护进程但不隐藏自身、不做事件分析、Event ID 3/7/10/23 的默认状态与官方警示（含 ArchiveDirectory 默认 `C:\Sysmon` 与膨胀风险）、schemaversion 与二进制版本独立、`-? config` 查 schema、规则语义（同字段 OR / 不同字段 AND / exclude 优先 / groupRelation）均来自官方页面。v15.2 的队列韧性改进来自官方索引页 What's New。配置模板推荐（SwiftOnSecurity / olafhartong）为社区项目，非微软官方产物。日志通道调大、`-c` 验证配置生效、降噪应 exclude 良性而非 include 可疑等为实践经验总结。示例 XML 中的 `schemaversion="4.82"` 取自调研素材记录的官方示例值，部署前应用 `-s` 核对本机实际支持版本。
