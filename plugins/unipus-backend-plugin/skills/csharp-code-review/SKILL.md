---
name: csharp-code-review
description: 用于审查 C# 代码的 Microsoft 编码规范、命名标准，或为代码合并做准备。触发场景包括 C# 文件审查请求、PR 审查或代码质量检查。
---

# C# 代码审查

## 概述

基于 [Microsoft 官方 C# 编码规范](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/coding-conventions) 和 [命名准则](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/identifier-names) 的系统化 C# 代码审查。

核心原则：**全面的 checklist 驱动审查可防止遗漏违规。**

## 何时使用

适用场景：
- 审查 PR 或合并的 C# 代码
- 提交前检查代码质量
- 用户要求"审查 C# 代码"或"检查 C# 规范"
- 确保团队编码标准合规性

不适用场景：
- 非 C# 语言（使用对应语言的专用 skill）
- 架构审查（重点是规范而非设计）
- 性能分析（使用 dotnet-diag skills）

## 审查清单

系统性地逐项检查每个类别，标记每项为 ✅ 已检查或 ⚠️ 发现违规。

### 1. 命名约定

| 元素 | 约定 | 示例 |
|---------|------------|---------|
| 接口 | `IPascalCase` | `IDataService` |
| 类/结构/记录 | `PascalCase` | `UserManager` |
| 特性类 | `PascalCase` + `Attribute` 后缀 | `CustomAttribute` |
| 枚举 | 单数（非标志），复数（标志） | `Color`, `FileOptions` |
| 公共成员 | `PascalCase` | `ProcessData()`, `UserName` |
| 私有实例字段 | `_camelCase` | `_userName` |
| 私有静态字段 | `s_camelCase` | `s_maxUsers` |
| 线程静态字段 | `t_camelCase` | `t_threadId` |
| 方法参数 | `camelCase` | `userName`, `maxCount` |
| 局部变量 | `camelCase` | `totalCount`, `isValid` |
| 泛型类型参数 | `T` 或 `TPascalCase` | `T`, `TItem`, `TKey` |
| 常量 | `PascalCase` | `MaxValue`, `DefaultTimeout` |

**主构造函数参数：**
- `record` 类型：`PascalCase`（成为公共属性）
- `class`/`struct` 类型：`camelCase`（标准参数）

**检查：**
- [ ] 无连续下划线 `__`（编译器保留）
- [ ] 无匈牙利命名法或类型前缀
- [ ] 有意义的描述性名称（除非在紧密循环中，否则不使用 `x`、`temp`、`data`）

### 2. 类型使用

| 使用 | 不使用 | 原因 |
|-----|-----|--------|
| `string` | `String` | C# 关键字 > BCL 类型 |
| `int` | `Int32` | C# 关键字 > BCL 类型 |
| `object` | `Object` | C# 关键字 > BCL 类型 |
| `bool` | `Boolean` | C# 关键字 > BCL 类型 |

适用于：所有具有 C# 关键字的类型（`long`、`short`、`byte`、`decimal`、`float`、`double` 等）

### 3. 字符串处理

| 场景 | 使用 | 避免 |
|----------|-----|-------|
| 简单拼接 | `$"Hello {name}"` | `"Hello " + name` |
| 循环拼接 | `StringBuilder` | `result += item` |
| 多行/大量转义 | 原始字符串 `"""..."""` | `@"..."` 或 `\"` |

### 4. 逻辑运算符

| 使用 | 不使用 | 原因 |
|-----|-----|--------|
| `&&` | `&` | 短路求值 |
| `\|\|` | `\|` | 短路求值 |

例外：对整数进行有意的位运算。

### 5. 代码结构

**命名空间：**
- [ ] 文件作用域命名空间声明：`namespace X;`（C# 10+）
- [ ] `using` 指令在命名空间外部（避免相对解析问题）
- [ ] Allman 大括号风格：大括号另起一行

**布局：**
- [ ] 每行一条语句
- [ ] 每行一个声明
- [ ] 4 空格缩进（不使用制表符）
- [ ] 方法/属性之间有空行
- [ ] 如果行太长，在运算符之前换行

**注释：**
- [ ] 单行注释用 `//`
- [ ] 公共成员使用 XML 注释 `///`
- [ ] 不使用多行注释 `/* */`（不兼容本地化）
- [ ] 注释独占一行，不放在代码行末尾
- [ ] 以大写字母开头，以句点结尾

### 6. var 使用

| 使用 `var` | 使用显式类型 |
|-----------|-------------------|
| `var list = new List<int>();` | `object data = GetComplexData();` |
| `var name = "John";` | `int count = Convert.ToInt32(input);` |
| LINQ 查询（通常是匿名类型） | 当类型从右侧不明显时 |

规则：当类型从右侧明显时使用 `var`，否则使用显式类型。

### 7. 集合与 LINQ

**初始化：**
```csharp
string[] vowels = [ "a", "e", "i", "o", "u" ];  // 集合表达式（C# 12+）
```

**LINQ：**
- [ ] 有意义的查询变量名称（不用 `q`、`result`）
- [ ] 隐式类型：`var query = from...`
- [ ] `from` 子句对齐：后续子句与 `from` 对齐
- [ ] `where` 在 `orderby`/`select` 之前（尽早过滤）
- [ ] 适合时优先使用多个 `from` 而非 `join`

### 8. 对象创建

**推荐：**
```csharp
ExampleClass instance = new();          // 目标类型（C# 9+）
var instance = new ExampleClass();      // 当类型明显时

// Required 属性（C# 11+）
public required string Name { get; init; }
```

**避免：**
- 构造函数重载膨胀（使用 `required` 属性）
- 不必要的类型重复：`ExampleClass x = new ExampleClass();`

### 9. 委托与事件

- [ ] 使用 `Func<>` 和 `Action<>` 而非自定义委托类型
- [ ] 对不需要移除的事件处理程序使用 Lambda
- [ ] 简洁语法：`Del handler = MethodName;`

### 10. 异常处理

- [ ] 对 `IDisposable` 使用 `using` 语句而非 `try-finally`
- [ ] 捕获特定异常（不捕获 `Exception`）
- [ ] 只捕获你能处理的异常
- [ ] 提供有意义的错误消息

### 11. 异步模式（如果存在）

- [ ] 对 I/O 绑定操作使用 `async`/`await`
- [ ] 在库代码中使用 `Task.ConfigureAwait(false)`
- [ ] 避免阻塞异步代码（`Task.Result`、`Task.Wait()`）

## 常见违规

| 症状 | 问题 | 修复 |
|---------|-------|-----|
| `public string userName;` | 公共字段 | 使用属性：`public string UserName { get; set; }` |
| `if(x > 0 & y > 0)` | 位运算符而非逻辑运算符 | 使用 `&&` |
| 循环中 `result = result + item` | 低效的字符串拼接 | 使用 `StringBuilder` |
| `var data = GetData();`（返回 `object`） | `var` 类型不明确 | 显式：`object data = ...` |
| 接口 `DataService` | 缺少 `I` 前缀 | `IDataService` |
| `private string userName` | 缺少 `_` 前缀 | `_userName` |

## 快速指南

快速审查要点：

1. **命名检查**：接口 `I`、特性后缀、私有 `_`、静态 `s_`、公共 `PascalCase`、参数 `camelCase`
2. **类型检查**：`string` 不用 `String`，`int` 不用 `Int32`
3. **运算符检查**：`&&` 不用 `&`，`||` 不用 `|`
4. **字符串检查**：插值 `$""`，循环中用 `StringBuilder`
5. **结构检查**：文件作用域命名空间、`using` 在外部、Allman 大括号

## 权威参考

本 skill 基于：
- [Microsoft C# 编码规范](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [Microsoft 标识符命名规则](https://learn.microsoft.com/zh-cn/dotnet/csharp/fundamentals/coding-style/identifier-names)
- [.NET Runtime 团队编码风格](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
