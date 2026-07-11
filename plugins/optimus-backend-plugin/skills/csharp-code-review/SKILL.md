---
name: csharp-code-review
description: 用于审查 C# 代码的 Microsoft 编码规范、命名标准、代码质量，以及异常处理/取消令牌传播等 API 健壮性问题。当用户提到：审查/检查/review C# 代码、.cs 文件、C# 项目代码规范、准备合并/PR、代码质量检查、命名约定问题、代码风格统一时，务必使用此 skill。也适用于用户询问"这段 C# 代码有什么问题"、"帮我看看这个类的命名"、"检查一下代码规范"等场景。
metadata:
  version: "1.4.0"
  author: desktop client team
compatibility: 纯知识型审查 skill，基于用户粘贴/提供的代码文本分析，无外部 CLI/MCP 依赖。
allowed-tools: Read
---

# C# 代码审查

## 概述

基于 [Microsoft 官方 C# 编码规范](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/coding-conventions) 和 [命名准则](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/identifier-names) 的系统化代码审查。

**核心原则**：通过全面的 checklist 驱动审查，确保不遗漏任何违规。规范不是约束，而是帮助团队写出一致、可维护、专业的代码。

## 审查流程

按以下顺序进行审查，确保系统性：

1. **快速扫描（30 秒）**：先看整体结构和明显问题
2. **分类检查（5-10 分钟）**：逐项检查下面的 12 个类别
3. **生成报告**：使用标准报告格式（见下方模板）

## 报告格式

**务必使用此标准模板**，便于用户快速理解问题：

```markdown
# C# 代码审查报告

## 审查摘要
- 审查范围：[文件名或代码片段描述]
- 发现问题：[总数] 个
- 严重级别分布：🔴 严重 [X]个 / 🟡 重要 [X]个 / 🟢 建议 [X]个

## 问题清单

### 🔴 严重问题（必须修复）
[列出可能导致 bug 或严重违反规范的问题]

### 🟡 重要问题（建议修复）
[列出影响可维护性或明显违规的问题]

### 🟢 改进建议（可选）
[列出可以提升代码质量的建议]

## 修正后的代码
[提供完整的修正版本]
```

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 用户未提供代码，只是询问规范/建议本身 | 直接解答具体规范问题，不套用完整报告模板 | 若问题范围不清，询问用户想了解哪个类别 |
| 代码片段不完整（缺少上下文，如引用的类型未定义） | 基于可见部分审查，报告中标注"因缺少上下文，以下判断基于可见代码" | 不臆测缺失部分的实现细节，只审查确实可见的代码 |
| 提供的代码不是 C#（如 Java/TypeScript 等其他语言） | 明确提示"这不是 C# 代码"，不强行套用 C# 规则审查 | 若用户坚持要求审查，说明本 skill 规则不适用后停止，不产出误导性报告 |
| 代码完整核对 12 个类别后未发现任何违规 | 如实报告"发现问题：0 个"，说明已完整核对 12 个类别 | 不为了让报告显得"有产出"而编造 🟢 建议凑数 |
| 某问题的严重级别判定存在歧义（如"公共字段未封装"介于严重与重要之间） | 按"是否可能导致运行时错误/安全问题"区分：会导致 bug、崩溃、安全漏洞 → 🔴；仅影响可维护性/风格一致性，不会立即出错 → 🟡 | 若判定依据仍不充分，在该问题旁注明"级别存疑"并列出支持两种级别的理由，交由用户判断 |
| "修正后的代码"用到了 C# 9+ 新语法（`required` 属性、主构造函数、集合表达式 `[...]`、原始字符串 `"""..."""` 等），但不确定用户项目的目标 `.NET`/langVersion | 在修正代码旁注明该语法所需的最低 C#/.NET 版本（如"集合表达式需要 C# 12 / .NET 8+"） | 若确实无法确认版本，额外提供一份兼容更早版本（C# 8 及以下）的替代写法，避免用户直接照搬导致编译不通过 |

## 审查清单

系统性地检查以下每个类别，标记 ✅ 已检查或 ⚠️ 发现违规。

### 1. 命名约定

**为什么重要**：一致的命名让代码自文档化，降低认知负担。团队成员可以立即识别变量的作用域和用途。

| 元素 | 约定 | 示例 | 原因 |
|---------|------------|---------|--------|
| 接口 | `IPascalCase` | `IDataService` | `I` 前缀让接口一眼可识别 |
| 类/结构/记录 | `PascalCase` | `UserManager` | 与 .NET Framework 一致 |
| 特性类 | `PascalCase` + `Attribute` 后缀 | `CustomAttribute` | 明确表明这是特性类 |
| 枚举 | 单数（非标志），复数（标志） | `Color`, `FileOptions` | 反映枚举的使用方式 |
| 公共成员 | `PascalCase` | `ProcessData()`, `UserName` | API 的标准约定 |
| 私有实例字段 | `_camelCase` | `_userName` | `_` 区分字段和属性/参数 |
| 私有静态字段 | `s_camelCase` | `s_maxUsers` | `s_` 表明静态作用域 |
| 线程静态字段 | `t_camelCase` | `t_threadId` | `t_` 标识线程局部存储 |
| 方法参数 | `camelCase` | `userName`, `maxCount` | 与局部变量一致 |
| 局部变量 | `camelCase` | `totalCount`, `isValid` | 标准约定 |
| 泛型类型参数 | `T` 或 `TPascalCase` | `T`, `TItem`, `TKey` | `T` 前缀表明是类型参数 |
| 常量 | `PascalCase` | `MaxValue`, `DefaultTimeout` | 与公共成员一致 |

**主构造函数参数（C# 12+）**：
- `record` 类型：`PascalCase`（自动成为公共属性）
- `class`/`struct` 类型：`camelCase`（标准参数）

**检查项**：
- [ ] 无连续下划线 `__`（编译器保留）
- [ ] 无匈牙利命名法（如 `strName`、`intCount`）
- [ ] 名称有实际意义（避免 `x`、`temp`、`data` 等无意义名称，除非在紧密循环中）

### 2. 类型使用

**为什么重要**：使用 C# 关键字而非 BCL 类型名称，代码更简洁一致，这是 C# 社区的标准做法。

| 使用 | 不使用 | 原因 |
|-----|-----|--------|
| `string` | `String` | C# 关键字更简洁 |
| `int` | `Int32` | 统一风格 |
| `object` | `Object` | 与语言习惯一致 |
| `bool` | `Boolean` | 更符合 C# 风格 |

适用于所有具有 C# 关键字的类型：`long`, `short`, `byte`, `decimal`, `float`, `double` 等。

### 3. 字符串处理

**为什么重要**：正确的字符串处理直接影响性能和可读性。

| 场景 | 使用 | 避免 | 原因 |
|----------|-----|-------|--------|
| 简单拼接 | `$"Hello {name}"` | `"Hello " + name` | 插值更清晰，编译器优化更好 |
| 循环拼接 | `StringBuilder` | `result += item` | 避免每次拼接都创建新字符串（O(n²) → O(n)） |
| 多行/转义 | 原始字符串 `"""..."""` | `@"..."` 或 `\"` | C# 11+ 特性，更清晰无转义 |

### 4. 逻辑运算符

**为什么重要**：正确的运算符选择影响程序逻辑和性能。

| 使用 | 不使用 | 原因 |
|-----|-----|--------|
| `&&` | `&` | 短路求值，右侧可能不执行，避免不必要计算和潜在的空引用 |
| `\|\|` | `\|` | 同上，找到 true 就停止 |

**例外**：对整数进行位运算时使用 `&` 和 `|` 是正确的。

### 5. 代码结构

#### 命名空间
- [ ] 使用文件作用域命名空间：`namespace X;`（C# 10+）
  - **为什么**：减少一层缩进，代码更清爽
- [ ] `using` 指令在命名空间外部
  - **为什么**：避免相对命名空间解析的歧义和意外行为
- [ ] Allman 大括号风格：大括号另起一行
  - **为什么**：.NET 生态系统的标准，提高可读性

#### 布局
- [ ] 每行一条语句
- [ ] 每行一个声明
- [ ] 4 空格缩进（不使用制表符）
- [ ] 方法/属性之间有空行
- [ ] 如果行太长，在运算符之前换行

#### 注释
- [ ] 简短说明用 `//`
- [ ] 公共 API 使用 XML 注释 `///`（生成文档）
- [ ] 不使用多行注释 `/* */`（影响本地化工具）
- [ ] 注释独占一行，不放在代码行末尾
- [ ] 以大写字母开头，以句点结尾

### 6. var 使用

**为什么重要**：`var` 平衡简洁性和可读性，规则是"当类型明显时用 `var`"。

| 使用 `var` | 使用显式类型 |
|-----------|-------------------|
| `var list = new List<int>();` | `object data = GetComplexData();` |
| `var name = "John";` | `int count = Convert.ToInt32(input);` |
| `var user = new User();` | `IEnumerable<T> items = GetItems();` |
| LINQ 查询（常为匿名类型） | 方法返回类型不明显时 |

**规则**：从赋值右侧能立即看出类型时用 `var`，否则显式声明。

### 7. 集合与 LINQ

**集合初始化（C# 12+）**：
```csharp
string[] vowels = [ "a", "e", "i", "o", "u" ];  // 集合表达式
```

**LINQ 检查项**：
- [ ] 查询变量名有意义（不用 `q`、`query`、`result`）
  - **为什么**：查询变量是业务逻辑的一部分，应该表达意图
- [ ] 使用隐式类型：`var query = from...`
- [ ] `from` 子句对齐：后续子句与 `from` 对齐
- [ ] `where` 在 `orderby`/`select` 之前
  - **为什么**：尽早过滤减少后续操作的数据量
- [ ] 适合时优先使用多个 `from` 而非 `join`（更清晰）

### 8. 对象创建

**推荐模式**：
```csharp
ExampleClass instance = new();          // 目标类型推断（C# 9+）
var instance = new ExampleClass();      // var + 完整类型

// Required 属性（C# 11+）强制初始化
public required string Name { get; init; }
```

**避免**：
- 构造函数重载膨胀（用 `required` 属性替代）
- 冗余类型重复：`ExampleClass x = new ExampleClass();`

### 9. 委托与事件

- [ ] 优先使用 `Func<>` 和 `Action<>` 而非自定义委托
  - **为什么**：标准化，不需要定义额外类型
- [ ] 不需要移除的事件处理程序用 Lambda
- [ ] 简洁语法：`Del handler = MethodName;`

### 10. 异常处理

- [ ] `IDisposable` 对象用 `using` 语句而非 `try-finally`
  - **为什么**：更简洁，编译器保证 Dispose 被调用
- [ ] 捕获特定异常类型（不捕获泛型 `Exception`）
  - **为什么**：只处理你能处理的异常，让意外异常暴露
- [ ] 提供有意义的错误消息

### 11. 异步模式

- [ ] I/O 绑定操作使用 `async`/`await`
- [ ] 库代码中使用 `Task.ConfigureAwait(false)`
  - **为什么**：避免死锁，提升性能
- [ ] 避免阻塞异步代码（`Task.Result`、`Task.Wait()`）
  - **为什么**：阻塞会导致线程池饥饿和死锁

### 12. API 设计与健壮性

**为什么重要**：命名/风格类问题多数能被 linter 自动检查，但异常语义、取消传播这类问题需要理解调用链路才会暴露，往往是代码风格满分但可靠性不及格的重灾区。

- [ ] **异常处理语义统一**：同一个方法内"失败"的表达方式不能混用——要么统一返回 `null`/默认值，要么统一抛异常。常见反模式：非成功状态码返回 `null`，但网络异常（如 `HttpRequestException`）、反序列化异常（如 `JsonException`）却完全未捕获，直接裸抛给调用方
  - **为什么**：调用方如果只判断返回值是否为 `null`，遇到未捕获异常时会直接崩溃或让异常传播到不该处理它的层
- [ ] **取消令牌传播**：I/O 绑定的异步方法（尤其是库代码/公共 API）应接受并向下传递 `CancellationToken cancellationToken = default`
  - **为什么**：省略取消令牌会导致调用链上无法做超时控制或主动取消，后续想补是破坏性变更
- [ ] **隐式依赖契约需要显式说明**：如果方法依赖调用方预先配置好的外部状态（如注入的 `HttpClient` 必须已设置 `BaseAddress`），应通过构造函数校验或 XML 注释明确该前提
  - **为什么**：隐式约定一旦被违反（如 DI 注册方式变了），只会在运行时才暴露为难以定位的异常
- [ ] **异常不能被静默吞没**：`catch` 块内必须有实质处理（记录日志、重试、向上抛），不能只 `Console.WriteLine` 或空着
  - **为什么**：静默吞掉异常会让调用方以为操作成功，故障排查时也没有日志可查

## 常见违规速查表

| 问题代码 | 违规类型 | 修复方式 |
|---------|-------|-----|
| `public string userName;` | 公共字段 | `public string UserName { get; set; }` |
| `if(x > 0 & y > 0)` | 位运算符误用 | `if(x > 0 && y > 0)` |
| 循环中 `result = result + item` | 低效字符串拼接 | 使用 `StringBuilder` |
| `var data = GetData();`（返回 `object`） | var 类型不明确 | `object data = GetData();` |
| 接口 `DataService` | 缺少 I 前缀 | `IDataService` |
| `private string userName` | 私有字段缺少前缀 | `private string _userName` |
| `private static int MaxUsers` | 静态字段缺少前缀 | `private static int s_maxUsers` |
| `String userName` | BCL 类型名 | `string userName` |
| `public bool isActive;` | 公共字段 + 错误命名 | `public bool IsActive { get; set; }` |
| `catch (Exception ex) { Console.WriteLine(ex.Message); }` | 异常被静默吞没 | 记录完整日志并按业务决定是否 `throw` |
| 异步方法无 `CancellationToken` 参数 | 缺少取消传播 | `Task Foo(..., CancellationToken cancellationToken = default)` |

## 快速审查清单

用于时间紧迫时的快速审查（1-2 分钟）：

1. **命名**：接口 `I` ✓、特性 `Attribute` 后缀 ✓、私有字段 `_` ✓、静态字段 `s_` ✓、公共 `PascalCase` ✓、参数 `camelCase` ✓
2. **类型**：`string` 而非 `String`，`int` 而非 `Int32`
3. **运算符**：`&&` 和 `||` 而非 `&` 和 `|`
4. **字符串**：简单拼接用插值 `$""`，循环用 `StringBuilder`
5. **结构**：文件作用域 namespace、`using` 在外部、Allman 大括号
6. **健壮性**：异常处理语义是否统一（不要一半返回 null 一半裸抛异常）、异步方法是否吞没了异常

## 权威参考

本 skill 基于以下权威来源：
- [Microsoft C# 编码规范](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [Microsoft 标识符命名规则](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/identifier-names)
- [.NET Runtime 团队编码风格](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)

## ⛔ 不要做什么（反例黑名单）

| 反模式 | 原因 | 替代做法 |
|---|---|---|
| 代码本身已合规时，为了让报告"显得有产出"而编造或吹毛求疵到无意义程度的违规 | 制造噪音，浪费用户时间去反驳不成立的问题，损害审查报告的可信度 | 如实报告"发现问题：0 个"，只列出真正命中 12 个类别的违规 |
| 只审查命名/风格类问题（第 1-11 类），忽视第 12 类"API 设计与健壮性" | 会导致"代码风格满分、可靠性不及格"的代码被判定为合规，实测证实这会让审查表现弱于不用任何工具的裸审查 | 12 个类别逐一核对，不能因为前 11 类已发现问题就跳过第 12 类 |
| 严重级别凭直觉打分，不说明判定依据 | 同一问题在不同执行中被判成不同级别（实测中"公共字段未封装"曾一次判🔴一次判🟡），报告不可复现、不可信任 | 套用"会导致bug/崩溃/安全漏洞→🔴，仅影响可维护性/风格→🟡"的二分测试，并在报告中说明判定理由 |
| 代码片段明显不完整（如引用了未定义的类型/方法）时，臆测缺失部分的实现并据此下结论 | 基于猜测的审查结论可能完全偏离真实代码，误导用户做出错误修改 | 只审查确实可见的代码，在报告中注明"因缺少上下文，以下判断基于可见代码" |
| 报告只给问题清单，省略"修正后的代码"部分 | 报告格式模板明确要求提供修正版本，用户往往需要直接参考可用的正确写法，而非自己重新实现 | 即使问题很少，也提供完整的修正后代码块，哪怕改动只有一两行 |
| 把仅影响风格一致性的 🟢/🟡 问题包装成"必须修复"的阻塞项 | 过度严格会让代码审查变成摩擦源，团队会开始抵触甚至绕过这个 skill | 严格按报告模板的三级分类展示，只有 🔴 才标注"必须修复"，🟡/🟢 保持"建议"措辞 |
