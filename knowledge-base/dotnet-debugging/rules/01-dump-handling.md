# 01 · dump 文件处置

> 更新历史：2026-09-05 创建。

> 本篇约束 dump 作为**数据资产**的处置，不约束调试技术本身。

日志侧的脱敏约束见 `knowledge-base/csharp/rules/14-security.md § 8. 日志与脱敏（联动 11 章）`。该节禁止记录密码、令牌与完整 PII，但约束的对象是日志。full dump 是整个进程内存的完整副本，其中必然含明文凭证与全量 PII，**任何脱敏中间件都无法作用于它**——统一脱敏过滤器在 dump 面前完全失效，故需本篇单独约束。

各 dump 类型的数据含量差异见 `reference/dump-types-and-capability.md`。

## 1. 生产 dump 的密级

- **必须**：生产环境抓取的 full dump 视同最高密级数据处置——它包含整个进程内存，字符串、堆对象字段中必然存在明文凭证、连接串与全量 PII
- **禁止**：把生产 dump 作为 IM、邮件附件传递，或上传到无访问控制的共享盘
- **必须**：dump 的存放、传递渠道满足与生产数据库备份同等的访问控制要求

`Mini`/`Triage` 类型虽剥离了堆对象数据，但线程栈、异常信息中仍可能残留敏感字符串（如异常消息里拼接的用户输入）——密级判断不因类型降级而自动放松，见 `reference/dump-types-and-capability.md § 1. 四种类型的能力对照`。

## 2. 版本库隔离

- **必须**：`.gitignore` 包含 dump 文件模式，防止调试产物进入版本库历史

```gitignore
*.dmp
*.dump
core.*
```

`core.*` 覆盖 Linux 下 `createdump` 与内核 core dump 的默认命名。一旦 dump 进入 git 历史，移除需要重写历史——这是该条标 `enforcement: ci` 的原因：外壳（文件是否被 ignore）可自动判定，且违反后的修复代价极高。

## 3. 对外交付的类型选择

- **应该**：向外部厂商或工单系统提交 dump 前，先评估 `Triage` 或 `Heap` 类型能否回答问题，而非默认交付 `Full`
- **应该**：明确本次交付需要回答什么问题——只需崩溃位置与线程栈选 `Triage`，需要堆对象分析选 `Heap`，两者都不满足才升级到 `Full`

`Triage` 的脱敏是「尽力而为」，不保证完全剥离敏感信息（见 `reference/dump-types-and-capability.md § 1. 四种类型的能力对照`）；选择更小的类型降低暴露面，但不能替代第 1 节的密级处置要求。

## 4. 留存期限与销毁

- **必须**：生产环境 dump 抓取后约定留存期限与销毁责任人
- **必须**：排查结束后按期销毁，不得无限期滞留在分析机本地磁盘或共享盘
- **禁止**：把 dump 当作事故复盘的"存档证据"无限期保留——留存期限应服务于排查需要，而非事后审计

## 5. 自动抓取的落盘位置

- **应该**：生产环境启用 WER LocalDumps（见 `reference/dump-capture.md § 4. WER LocalDumps（Windows，崩溃自动抓取）`）或 `DOTNET_DbgEnableMiniDump`（见 `reference/dump-capture.md § 5. DOTNET_DbgEnableMiniDump（.NET Core 3.0+，崩溃自动抓取）`）前，确认落盘目录的访问权限与磁盘容量上限
- **应该**：显式设置落盘目录（`DumpFolder`），而非依赖默认路径——默认路径（如 `%LOCALAPPDATA%\CrashDumps`）的访问控制未必符合本节第 1 条的密级要求
- **应该**：设置合理的保留份数上限（如 `DumpCount`），避免崩溃循环时敏感文件静默堆积耗尽磁盘

自动抓取一旦启用即持续生效，不像手动抓取那样有人在场判断是否该抓——这正是它容易积累密级不明、无人认领的敏感文件的原因。
