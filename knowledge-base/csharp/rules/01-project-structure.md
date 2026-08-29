# 01 · 环境与技术选型 + 解决方案与项目结构

> 更新历史：2026-08-21 创建；2026-08-29 第 6 节分层与依赖方向的通用条款去重，改为引用 `knowledge-base/architecture/rules/01-layering.md`，本节仅保留 C# 项目引用机制特有约束。

**版本中立声明**：本规范不绑定具体 .NET 版本。目标框架由团队在仓库级统一决策，规范只约定"如何一致"，不约定"用哪一版"。版本升级与迁移以 `dotnet-upgrade` 系列 skills 为准。

## 1. 目标框架策略

- **必须**：全仓库统一 `TargetFramework`，主版本由团队决策，并用 `global.json` / `Directory.Build.props` 固化
- **必须**：优先选择当前处于支持期的 LTS 版本
- **应该**：多项目仓库通过 `Directory.Build.props` 集中声明目标框架，避免逐项目手写
- **禁止**：同一解决方案内混用不兼容的目标框架（除非有明确理由并在代码中注释）
- **必须**：引入新框架特性前，以该目标框架的编译器实际构建结果为准（见 `02` 章"语言特性三问"）

## 2. SDK 与工具链

- **必须**：用 `global.json` 固定 SDK 主版本，保证本地与 CI 一致
- **应该**：统一 IDE 与编辑器配置（`.editorconfig` + `.vscode` / Visual Studio 共享设置），编辑器的差异不改变产出物
- **必须**：所有项目开启可空与隐式 using：

  ```xml
  <Nullable>enable</Nullable>
  <ImplicitUsings>enable</ImplicitUsings>
  ```

  - **禁止**：用 `#nullable disable` 关闭可空分析；存量代码迁移期例外，但需登记并限期收敛（迁移方法见 `dotnet-upgrade:migrate-nullable-references`）
- **LangVersion**：不显式固定，跟随目标框架默认值；仅在确实需要（且团队认可）时经评审后调整

```csharp
// ❌ 关闭可空分析：文件内丢失所有空引用告警，可空 null 直接运行期炸
#nullable disable
public User FindUser(int id)
{
    var users = _repo.GetUsers();          // 返回 IEnumerable<User?>，被当成非空
    return users.FirstOrDefault(u => u.Id == id);   // 可能返回 null，调用方不知情
}

// ✅ 保持可空并修正确实的问题：签名诚实表达"可能为空"，调用方被迫处理
public User? FindUser(int id)
{
    var users = _repo.GetUsers();
    return users.FirstOrDefault(u => u.Id == id);   // 返回类型带 ?，调用方须判空
}
```

## 3. 静态分析与编辑配置

- **必须**：仓库根提供 `.editorconfig`，覆盖缩进（4 空格）、字符集（UTF-8）、花括号风格、`using` 排序等规则，并随 `.gitignore` 一并提交
- **必须**：启用 .NET 内置分析器（`<AnalysisLevel>latest</AnalysisLevel>`）
- **应该**：选定一个扩展分析器（StyleCop 或 SonarAnalyzer，**团队二选一，不混用**），规则集与项目模板绑定
- **必须**：构建开启 `TreatWarningsAsErrors`（含分析器告警）；确为误报时用 `#pragma warning disable` 或 `[SuppressMessage]` 处理，禁用范围最小化且必须附带理由注释
- **禁止**：为通过构建而全局关闭分析规则

## 4. 解决方案布局

标准布局，新仓库必须遵守，存量仓库逐步收敛：

```
<repo>/
├── src/
│   └── <Company>.<Product>.<Module>/
├── tests/
│   └── <Company>.<Product>.<Module>.Tests/
├── Directory.Build.props
├── Directory.Packages.props      # CPM，见 10 章
├── global.json
└── <Product>.slnx | <Product>.sln
```

- **必须**：解决方案至少包含 `src` 与 `tests` 两层
- **必须**：公共属性（目标框架、Nullable、分析级别）集中在 `Directory.Build.props`，逐项目不重复
- **禁止**：仓库根目录放置业务代码；根目录只放解决方案级文件与文档
- **应该**：测试项目与源码项目同名加 `.Tests` 后缀，并放入 `tests/` 对应子目录

## 5. 命名空间与命名

- **必须**：命名空间与程序集名一致，遵循 `<Company>.<Product>.<Module>` 三级起步，例如 `Contoso.Orders.Api`
- **必须**：文件夹层级与命名空间层级一致，新增目录不产生命名空间漂移
- **必须**：一个文件一个主类型，文件名与主类型名一致（`UserManager.cs` 内定义 `UserManager`）
- **禁止**：一个文件堆叠多个公共类型（紧密耦合的小型类型组可经 review 豁免）

## 6. 分层与依赖方向

分层模型的选择与统一等**通用**约束见 `knowledge-base/architecture/rules/01-layering.md` § 1. 分层模型的选择与统一。依赖单向向内、禁止循环引用与越层引用见同文件 § 2. 依赖方向。跨层用抽象定义契约、契约归属内层见同文件 § 3. 跨层契约。C# 侧的附加要求：

层次在 C# 中以**项目（程序集）**为承载单元，两种常见模型的项目命名：

- **领域分层**：`Domain`（实体 / 值对象 / 领域接口）→ `Application`（用例 / 应用服务）→ `Infrastructure`（数据访问、外部服务等实现细节）→ `Presentation`（API / UI）
- **简单分层**：`Core` → `Services` → `Api`

- **必须**：层与项目一一对应，依赖方向由 `ProjectReference` 承载——这样越层与循环引用由编译器直接拦截，无需额外架构测试

```csharp
// ❌ 表现层直接 new 仓储实现：越过 Application/领域接口，依赖方向被打破
// Presentation 项目引用 Infrastructure，后续替换实现要改所有调用点
public class OrderController
{
    public async Task<Order?> Get(int id)
    {
        var repo = new SqlOrderRepository();   // Infrastructure 具体类
        return await repo.FindAsync(id);
    }
}

// ✅ 跨层只依赖接口，实现由组合根（DI 注册）装配
// Presentation 只引用 Application/Domain 的 IOrderRepository
public class OrderController
{
    private readonly IOrderRepository _repo;   // 依赖抽象
    public OrderController(IOrderRepository repo) => _repo = repo;

    public async Task<Order?> Get(int id) => await _repo.FindAsync(id);
}
```
- **必须**：跨层边界的接口定义在被依赖的内层项目中，实现项目只被组合根引用
- **禁止**：测试项目引用无关实现项目；测试只引用被测项目及其必要依赖

## 7. 项目类型约定

| 项目类型 | 约定 |
|---|---|
| 类库 | 不含 `Program` / 入口点；对外 API 即程序集公共面 |
| 可执行 / Host | 入口极薄，业务逻辑在类库；启动配置走 `appsettings` + 强类型配置类 |
| 测试项目 | `xUnit` 或 `NUnit`（团队统一一种）；命名 `<被测>.Tests`；`<IsTestProject>true</IsTestProject>` |

- **必须**：可执行项目不承载业务逻辑，仅做组合根与配置
- **应该**：新增项目时优先复制既有项目骨架或使用团队项目模板，而非从零手写 csproj

## 8. 构建与 CI

- **必须**：CI 顺序执行 `dotnet restore` → `dotnet build -warnaserror` → `dotnet test`
- **必须**：CI 使用与 `global.json` 一致的 SDK；跨平台时固定同一 SDK 版本
- **应该**：CI 缓存 NuGet 包（`~/.nuget/packages` 或仓库级缓存目录），缩短还原时间
- **必须**：CI 禁止使用私有/本地独有的机器依赖，构建必须可复现
- **应该**：构建产物（`bin` / `obj`）不入库，由 `.gitignore` 统一排除

## 附录：Directory.Build.props 落地模板

本模板对应本篇第 1–3 节的约束，可直接作为仓库级 `Directory.Build.props` 的起点。条件属性（`Condition`）用于按项目类型差异化设置。

```xml
<Project>

  <!-- 公共属性：全仓库统一，项目内不重复 -->
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>          <!-- 由团队统一决策，见第 1 节 -->
    <Nullable>enable</Nullable>                        <!-- 必须，见第 2 节 -->
    <ImplicitUsings>enable</ImplicitUsings>            <!-- 必须，见第 2 节 -->
    <AnalysisLevel>latest</AnalysisLevel>              <!-- 内置分析器，见第 3 节 -->
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors> <!-- 门禁，见第 3 节 -->
    <Deterministic>true</Deterministic>                <!-- 可复现构建 -->
  </PropertyGroup>

  <!-- 测试项目差异化：不打包、采集覆盖率 -->
  <PropertyGroup Condition="'$(IsTestProject)' == 'true'">
    <IsPackable>false</IsPackable>
    <CollectCoverage>true</CollectCoverage>
  </PropertyGroup>

  <!-- 可执行/Host 项目：不产生文档，见第 7 节 -->
  <PropertyGroup Condition="'$(OutputType)' == 'Exe'">
    <GenerateDocumentationFile>false</GenerateDocumentationFile>
  </PropertyGroup>

</Project>
```

**使用说明**：

- `TargetFramework` 处按团队决策填写（见第 1 节"版本中立"），升级时只改这一处即可全仓库生效
- 新增项目**不重复**上述属性；需要覆盖时在项目内局部声明，并注释原因
- 包版本不在此文件——统一在 `Directory.Packages.props`（CPM，见 `10` 章第 1 节）
- `LangVersion` 不显式固定，跟随目标框架默认值（见第 2 节）
