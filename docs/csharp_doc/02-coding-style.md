# 02 · 命名规范 + 编码风格 + 语言特性准则

> 更新历史：2026-08-21 创建。

本篇是团队编码层面的权威依据，`csharp-code-review` skill 的审查项与本章一一对应。版本中立的落地方式见第 3 章"语言特性三问"。

## 1. 命名规范

### 1.1 核心规则表

| 元素 | 规则 | 示例 |
|---|---|---|
| 接口 | `IPascalCase` | `IDataService` |
| 类 / 结构 / 记录 | `PascalCase` | `UserManager`, `Address`, `OrderItem` |
| 特性类 | `PascalCase` + `Attribute` 后缀 | `ObsoleteAttribute` |
| 枚举 | 普通枚举单数；`[Flags]` 枚举复数 | `Color`, `FileOptions` |
| 公共成员（方法 / 属性 / 公共字段） | `PascalCase` | `ProcessData()`, `UserName` |
| 私有实例字段 | `_camelCase` | `_userName` |
| 私有静态字段 | `s_camelCase` | `s_maxUsers` |
| 线程静态字段 | `t_camelCase` | `t_threadId` |
| 常量（`const`） | `PascalCase` | `DefaultTimeout` |
| 方法参数 | `camelCase` | `userName`, `maxCount` |
| 局部变量 | `camelCase` | `totalCount`, `isValid` |
| 泛型参数 | `T` 或 `TPascalCase` | `T`, `TKey`, `TItem` |
| 事件 | 动词 / 动词短语 | `RequestCompleted` |
| 命名空间 | `Company.Product.Module` | `Contoso.Orders.Api` |

**主构造函数参数（若使用）**：

- `record` 类型：`PascalCase`（自动成为公共属性）
- `class` / `struct` 类型：`camelCase`（普通参数）

### 1.2 命名禁忌

- **禁止**匈牙利命名：`strName`、`intCount`、`btnSubmit`
- **禁止**连续下划线 `__`（编译器保留标识符）
- **禁止**无意义命名：`data`、`temp`、`x`（紧密循环的循环变量可豁免）
- **禁止**公共成员使用 `_` 前缀或 `camelCase`
- **禁止**同一标识符在相邻作用域内语义漂移（同名不同义）

### 1.3 布尔命名

- **应该**：布尔属性 / 方法 / 局部变量以 `Is` / `Has` / `Can` / `Should` / `Contains` 等动词开头：`IsValid`、`HasItems`、`CanEdit`、`IsEnabled`
- **禁止**：布尔变量用无动词名词（`Flag`、`Status` 不表达真假）

### 1.4 缩写与复合词

- 两个字母的缩写全大写：`IO`、`UI`、`IP`
- 三个字母及以上按单词处理：`Xml`、`Http`、`Json`、`Dto`
- 缩写与全词组合时保持一致：`HttpClient`（非 `HTTPClient`）、`XmlSerializer`
- **禁止**：类型名出现数字缩写或拼音缩写（`Doc2`、`BmManager`）

## 2. 编码风格

### 2.1 结构与布局

- **必须**：Allman 大括号风格，`{` 另起一行
- **必须**：4 空格缩进，不使用制表符
- **必须**：每行一条语句、每行一个声明
- **必须**：成员间保留空行（字段 → 构造函数 → 属性 → 方法）
- **应该**：行过长时在运算符之前换行
- **必须**：文件作用域命名空间 `namespace X;`（若目标框架支持），`using` 指令置于命名空间之外，`System.*` 优先排序

### 2.2 类型与运算符

- **必须**：使用 C# 关键字而非 BCL 类型名：`string` / `int` / `object` / `bool` / `double` 等，不用 `String` / `Int32` / `Object` / `Boolean`
- **必须**：逻辑运算使用短路运算符 `&&` / `||`；只有真正的整数位运算才用 `&` / `|`
- **必须**：判空优先用模式匹配 `is null` / `is not null`，不用 `== null`（可读性 + 分析器友好）

### 2.3 字符串处理

| 场景 | 使用 | 避免 | 原因 |
|---|---|---|---|
| 简单拼接 | `$"Hello {name}"` | `"Hello " + name` | 插值清晰，编译器优化更优 |
| 循环 / 多次拼接 | `StringBuilder` | `result += item` | 避免 O(n²) 字符串分配 |
| 多行 / 转义密集 | 原始字符串 `"""..."""`（若支持） | `@"..."` 层层转义 | 免转义，更清晰 |
| 国际化 | `string.Format` + 资源 | 硬编码拼接 | 占位符与资源可翻译 |

### 2.4 `var` 与对象创建

- **应该**：类型从右侧立即可见时用 `var`：`var user = new User();`
- **禁止**：右侧返回 `object` / 基类 / 匿名无法推断时用 `var` 掩盖真实类型：`object data = GetComplexData();`
- **应该**：字段 / 局部变量优先目标类型 `new()`：`User user = new();`
- **禁止**：冗余类型重复：`User user = new User();`

### 2.5 注释风格

- **必须**：公共 API 使用 XML 注释 `///`（生成文档，内容规范见 `17` 章）
- **必须**：行内说明用 `//`，注释独占一行，以大写开头、句点结尾
- **禁止**：使用块注释 `/* */` 做行内说明（影响本地化工具）
- **禁止**：注释描述"是什么"，应描述"为什么"（见 `17` 章注释哲学）
- **禁止**：在注释里留未使用的过期代码（用版本控制，而非注释）

## 3. 语言特性使用准则（版本中立）

**版本中立原则**：本篇不记录"某特性属于 C# X"这类版本信息。某一特性的可用性以项目实际 `TargetFramework` / `LangVersion` 的**编译结果为准**，统一用"三问"决策：

> ① 团队是否已普遍接受？② 当前目标框架编译器是否支持（以构建通过为准）？③ 是否提升可读性或正确性？

三问全为"是"才采用。第③问由 reviewer 一票否决。

### 3.1 推荐优先使用的特性

| 特性 | 价值 | 典型场景 |
|---|---|---|
| 文件作用域命名空间 | 减少缩进 | 所有新文件 |
| 字符串插值 | 可读性 | 全部字符串拼接 |
| 模式匹配 / switch 表达式 | 表达力、穷尽性 | 类型分派、判空、解构 |
| `init` / `required` 属性 | 不可变构造 | 不可变模型、DTO |
| 目标类型 `new` | 简洁 | 字段 / 局部变量初始化 |
| 只读结构（`readonly struct`） | 语义清晰 | 小型值类型 |
| 异步流 `IAsyncEnumerable<T>` | 异步序列 | 流式数据（见 `04` 章） |

### 3.2 谨慎使用的特性

| 特性 | 风险 | 采用前提 |
|---|---|---|
| 主构造函数（class） | 字段捕获易混淆，与 DI 语义冲突 | 简单值容器；公共 API 边界慎用 |
| 记录 `record` | 值语义被误用 | 明确需要值相等 / 解构时 |
| 集合表达式 `[..]` | 可读性依赖读者熟悉度 | 简单只读集合构造 |
| 扩展属性 / 索引器 | 隐性魔术 | 理解者众且团队认可 |
| `dynamic` | 运行时错误、无编译期检查 | 几乎不用，仅限互操作场景 |

### 3.3 禁止

- **禁止**：为"炫技"使用新语法；第③问（可读性）一票否决
- **禁止**：公共 API 边界使用会破坏库消费者兼容的语法（向后兼容承诺见 `13` 章）
- **禁止**：在同一代码库内混用新旧等价写法（如部分文件用 `== null`、部分用 `is null`）

## 4. 常见违规速查

| 问题代码 | 违规 | 修复 |
|---|---|---|
| `public string userName;` | 公共字段 + 错误命名 | `public string UserName { get; set; }` |
| `if (x > 0 & y > 0)` | 位运算符误用 | `if (x > 0 && y > 0)` |
| `result = result + item`（循环内） | 低效拼接 | 使用 `StringBuilder` |
| `var data = GetComplexData();` | var 掩盖类型 | `object data = GetComplexData();` |
| `interface DataService` | 缺少 `I` 前缀 | `IDataService` |
| `private string userName` | 私有字段缺前缀 | `private string _userName` |
| `private static int MaxUsers` | 静态字段缺前缀 | `private static int s_maxUsers` |
| `String userName` | BCL 类型名 | `string userName` |
| `x == null` | 判空写法 | `x is null` |
