# .NET 平台与运行时知识库

> 版本：7.2.1

> 面向 .NET Runtime、.NET Framework、SDK、目标框架、操作系统兼容性与产品生命周期的描述性知识库。

## 文档目的

本领域解释 .NET 平台与操作系统之间的兼容关系，帮助开发者判断目标框架、运行时、SDK 和 Windows 版本的组合是否满足技术要求与官方支持边界。

本领域重点回答“平台事实是什么、组合是否受支持、生命周期如何判断”，不直接规定所有项目必须采用哪个版本。

## 适用范围与读者

- **适用范围**：.NET Framework、现代 .NET（5+）、.NET Runtime、SDK、Windows 客户端与服务器版本的兼容性和生命周期
- **读者**：.NET 项目负责人、架构师、开发者、运维人员，以及负责旧系统迁移和部署的成员

## 内容边界

| 领域 | 负责内容 | 不负责内容 |
|---|---|---|
| `dotnet` | Runtime / Framework / SDK、Target Framework、OS 兼容性、LTS/STS 生命周期、安装前提与迁移背景 | C# 语言写法、通用代码风格、WPF 控件和 XAML 设计 |
| `csharp` | C# 语言特性、编码风格、设计原则、异常、异步、并发、测试和 API 设计 | 具体 Windows 版本与 .NET 运行时支持矩阵 |
| `wpf` | WPF / XAML、MVVM、绑定、控件、资源、渲染、UI 线程、桌面部署 | 通用 .NET 生命周期和 Windows 版本支持事实 |

三个领域按知识责任并列维护，不表示技术上互相独立：C# 和 WPF 项目可以依赖 .NET 领域的兼容性参考；必要时通过交叉引用使用，不复制同一事实。

## 阅读路径

| 场景 | 推荐内容 |
|---|---|
| 判断 Windows 与 .NET 版本是否兼容 | `reference/windows-dotnet-support-matrix.md` |
| 选择项目目标框架和 SDK | 本文档 + `csharp` 领域的项目结构规范 |
| 进行 .NET Framework 到现代 .NET 迁移 | 支持矩阵 reference + 迁移类 skill 的具体流程 |
| 开发 C# 代码 | `knowledge-base/csharp/` |
| 开发 WPF 桌面界面 | `knowledge-base/wpf/` |

## 内容类型

当前本领域只收录 `reference` 描述性文档，不把外部平台支持事实直接写成团队 MUST / SHOULD / MAY 规范。若未来形成团队统一的目标框架政策，应另行新增规范条款，并明确其与本领域 reference 的关系。

## 更新与维护

- 平台支持矩阵属于时效性内容，新增 .NET 或 Windows 版本、支持策略变化时应复核
- 文档必须区分“技术上可安装”“Microsoft 官方支持”和“Windows 本身仍受支持”
- 来源、审阅日期和适用版本随内容一起维护
- 新增或修改 reference 时同步更新 `index.jsonl`、本领域 `README.md` 顶部版本号和 `CHANGELOG.md`
- 校验命令：`python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet`

## 与其他领域的关系

- `csharp` 领域中的目标框架、SDK 和项目结构规则可以引用本领域的兼容性事实
- `wpf` 领域中的环境与打包部署规则可以引用本领域的 Windows / .NET 支持矩阵
- 本领域不反向复制 C# 或 WPF 的编码、架构和 UI 规范

## 权威参考

- [Microsoft .NET 文档](https://learn.microsoft.com/dotnet/)
- [.NET Support Policy](https://dotnet.microsoft.com/platform/support/policy)
- [Microsoft .NET Framework 系统要求](https://learn.microsoft.com/dotnet/framework/get-started/system-requirements)
