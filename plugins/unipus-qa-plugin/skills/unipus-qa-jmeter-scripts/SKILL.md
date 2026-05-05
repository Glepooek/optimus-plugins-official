---
name: unipus:qa:jmeter-scripts
description: 根据 OpenAPI 文档自动生成具备完整接口依赖关系的 JMeter JMX 性能测试脚本。当用户需要：(1) 根据 API 文档生成 JMeter JMX 脚本；(2) 生成带认证、CRUD 串联、数据流依赖的接口测试脚本；(3) 生成包含业务断言、数据一致性验证、枚举值全覆盖的测试脚本时触发。需用户提供 JMeter 版本号（如 5.5、5.6.3）。
creator：yinxuan@unipus.cn
---

# JMeter JMX 脚本生成

## 前置：信息收集（必须按顺序询问）

在生成脚本前，**必须依次确认以下两项信息**：

### 1. 项目源码路径

首先询问用户：
> "请问是否有后端项目源码路径？如果有，请提供路径（如 `learning-management-system/backend`），我将结合源码精确生成断言；如果没有，将仅根据接口文档生成。"

**有源码路径时（推荐）**：
- 读取对应模块的 Controller、Service、DTO、Entity 源文件
- 从源码中提取**精确的返回值字符串**（如 `"Enrolled successfully"`、`"Failed to enroll"`）
- 识别**异常场景的真实 HTTP 状态码**（如缺少参数是 400 还是 500，取决于后端是否有校验）
- 识别响应体格式：纯字符串 vs JSON 对象 vs 无内容

**无源码路径时**：
- 仅根据接口文档描述生成断言
- 对响应体内容使用模糊匹配（`contains`），不做精确断言
- 在注释中标注"需根据实际响应调整断言"

### 2. JMeter 版本

**必须确认 JMeter 版本**。如果用户未提供，立即询问：
> "请提供您的 JMeter 版本号（如 5.4.1、5.5、5.6.3），脚本结构将根据版本适配。"

| 版本 | `properties` 属性 |
|------|------------------|
| 5.4.x 及以下 | `properties="4.0"` |
| 5.5.x 及以上 | `properties="5.0"` |

`jmeter="X.X.X"` 使用用户提供的准确版本号。

---

## 三阶段生成流程

### 第一阶段：分析

**有源码时**，在解析 API 文档的同时，读取源码：

```
Controller  → 确认路由、HTTP 方法、参数类型
Service     → 提取所有 return 语句的精确字符串值
             → 识别异常分支（orElse(null)、if null → 返回什么）
DTO/Entity  → 确认请求体字段名和类型（必填/选填）
```

**关键：从 Service 源码提取断言依据**

| Service 代码模式 | 断言结论 |
|----------------|---------|
| `return "Enrolled successfully"` | 响应体精确等于该字符串 |
| `return "Failed to enroll"` | user 或 course 为 null 时返回，HTTP 200 |
| `return "Course already enrolled"` | 重复操作时返回，HTTP 200 |
| `findById(null)` 无 null 检查 | 缺少该参数时 → HTTP 500 |
| `@NotNull` / `@Valid` 校验 | 缺少参数时 → HTTP 400 |
| 无返回值 `void` | HTTP 200，响应体为空 |
| 返回实体对象 | HTTP 200，响应体为 JSON，用 JSONPath 断言字段 |

**无源码时**，仅解析 API 文档：
1. **解析 API 文档**（通过 apifox-mcp-server 获取完整 OpenAPI 规范）
2. **认证识别**：查找 `/login`、`/auth`、`/signin` 等路径，识别 token/cookie 提取字段
3. **依赖关系分析**：POST 返回的 ID 用于后续 GET/PUT/DELETE
4. **枚举值识别**：识别含 `enum`、`type`、`operation`、`action`、`mode` 等多值参数

### 第二阶段：生成

按以下顺序生成 JMX 结构：
1. 基础 JMX 结构（TestPlan + HTTP 默认值 + 全局 Header）
2. 认证线程组（登录 → 提取 token）
3. 业务请求串联序列（参见下方串联顺序）
4. 每个写操作添加精确断言（有源码用精确匹配，无源码用模糊匹配）
5. 枚举值接口生成独立请求链

**CRUD 串联标准顺序**：
```
1-登录 → 提取 token
2-新增数据 → HTTP200 + 业务码=0 + 有效ID → 提取 ID
3-查询列表 → 验证包含新创建的 ID 和名称
4-查询详情 → JSONPath 逐字段验证所有提交字段 + ID 一致性
5-修改数据 → HTTP200 + 业务码=0 + value=true
5.1-验证修改后详情 → 验证已更新字段 + 未更新字段不变
6-删除数据 → HTTP200 + 业务码=0 + value=true
6.1-验证删除后详情 → 验证资源不存在
```

### 第三阶段：优化

- 添加错误处理和超时配置
- 配置查看结果树 + 聚合报告监听器
- 参数化基础配置（BASE_URL、PORT）

---

## 断言规范

### 有源码时：精确断言

响应体为**纯字符串**（Controller 直接 `return String`）：

```xml
<!-- 精确等于某个字符串 -->
<ResponseAssertion testname="断言-响应体精确值">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="1">Enrolled successfully</stringProp>
  </collectionProp>
  <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
  <intProp name="Assertion.test_type">8</intProp>  <!-- 8=equals -->
</ResponseAssertion>

<!-- OR 断言：多个合法值之一（如首次/重复操作） -->
<ResponseAssertion testname="断言-响应体为A或B">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="1">Enrolled successfully</stringProp>
    <stringProp name="2">Course already enrolled</stringProp>
  </collectionProp>
  <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
  <intProp name="Assertion.test_type">40</intProp>  <!-- 40=OR -->
</ResponseAssertion>
```

响应体为 **JSON 对象**（Controller 返回实体/DTO）：用 JSONPath 断言逐字段验证。

### 无源码时：模糊断言

```xml
<ResponseAssertion testname="断言-响应含成功关键字">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="1">success</stringProp>
  </collectionProp>
  <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
  <intProp name="Assertion.test_type">2</intProp>  <!-- 2=contains -->
</ResponseAssertion>
<!-- ⚠️ 注意：需根据实际响应调整断言 -->
```

### 异常场景断言（有源码时必须精确）

| 异常场景 | 源码特征 | 断言 |
|---------|---------|------|
| 缺少必填参数，无校验注解 | `findById(null)` 直接调用 | HTTP 500 + 含 `Internal Server Error` |
| 缺少必填参数，有 `@Valid` | DTO 字段有 `@NotNull` | HTTP 400 |
| 资源不存在，返回字符串 | `return "Failed to ..."` | HTTP 200 + 精确字符串 |
| 资源不存在，抛异常 | `orElseThrow(...)` | HTTP 404 或 500 |
| 未携带 Token | Spring Security 拦截 | HTTP 401 |

---

## 四大断言规范（每个写操作必须全部包含）

| 操作 | 必选断言 |
|------|---------|
| 创建/保存 | HTTP 200 + 业务码(code=0) + 返回有效ID + 列表存在验证 + 详情字段 JSONPath 精确验证 |
| 更新/修改 | HTTP 200 + 业务码(code=0) + value=true + 回查详情验证已更新字段 |
| 删除 | HTTP 200 + 业务码(code=0) + value=true + 回查验证资源不存在 |

详细 XML 模板见 [references/assertion-rules.md](references/assertion-rules.md)

## ⚠️ XML 硬性语法规则（违反导致脚本无法打开）

### 规则1：每个测试元件后必须紧跟 `<hashTree/>`

JMeter JMX 的树状结构要求：**凡是 `<hashTree>` 的直接子元件（Sampler / PostProcessor / Assertion / HeaderManager 等），其闭合标签后面必须紧跟一个 `<hashTree/>`**（无子节点时用自闭合形式）。缺少 `<hashTree/>` 会导致 `ClassCastException: XXX cannot be cast to HashTree`，脚本无法打开。

```xml
<!-- ❌ 错误：缺少 <hashTree/> -->
<hashTree>
  <JSONPostProcessor .../>
  <JSR223PostProcessor .../>     <!-- 解析器在此期望 hashTree，报 ClassCastException -->
  <ResponseAssertion .../>
</hashTree>

<!-- ✅ 正确：每个元件后都有 <hashTree/> -->
<hashTree>
  <JSONPostProcessor .../>
  <hashTree/>
  <JSR223PostProcessor .../>
  <hashTree/>
  <ResponseAssertion .../>
  <hashTree/>
  <JSONPathAssertion .../>
  <hashTree/>
</hashTree>
```

**受影响的所有元件类型**（不限于）：
- `HTTPSamplerProxy` → `<hashTree>...</hashTree>`（含子断言/提取器）
- `JSONPostProcessor` → `<hashTree/>`
- `JSR223PostProcessor` / `JSR223PreProcessor` → `<hashTree/>`
- `ResponseAssertion` → `<hashTree/>`
- `JSONPathAssertion` → `<hashTree/>`
- `HeaderManager` → `<hashTree/>`
- `ConfigTestElement` → `<hashTree/>`
- `ResultCollector` → `<hashTree/>`
- `Arguments` → `<hashTree/>`
- `SetupThreadGroup` / `ThreadGroup` / `TearDownThreadGroup` → `<hashTree>...</hashTree>`

### 规则2：XML 注释中不能含 `--`

XML 规范禁止注释内部出现 `--`（仅允许出现在结尾 `-->`）。使用 `<!-- ---- 标题 ---- -->` 等装饰性分隔线会导致 `XmlPullParserException`，脚本无法打开。

```xml
<!-- ❌ 错误：注释内含 -- -->
<!-- ---- 流程A：CRUD 测试 ---- -->
<!-- ================================================================ -->

<!-- ✅ 正确：用 == 或其他字符替代 -->
<!-- ==== 流程A：CRUD 测试 ==== -->
<!-- ================================================================ -->
```

> **生成脚本的分隔注释一律使用 `====` 或 `####`，禁止使用 `----`。**

---

## 脚本元件使用规范（避坑）

### ❌ 禁止使用 BeanShellPostProcessor / BeanShellPreProcessor

BeanShell 解释器对 `java.util.Properties` 的方法调用存在兼容性问题，`props.put()` 和 `props.setProperty()` 均会抛出 `Method Invocation` 错误。

**必须改用 JSR223（Groovy）**：

```xml
<!-- ✅ 正确：JSR223PostProcessor -->
<JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="保存Token到全局属性" enabled="true">
  <stringProp name="scriptLanguage">groovy</stringProp>
  <stringProp name="filename"></stringProp>
  <stringProp name="parameters"></stringProp>
  <boolProp name="cacheKey">true</boolProp>
  <stringProp name="script">props.put("g_token", vars.get("token")); props.put("g_userId", vars.get("userId"));</stringProp>
</JSR223PostProcessor>
<hashTree/>

<!-- ✅ 正确：JSR223PreProcessor -->
<JSR223PreProcessor guiclass="TestBeanGUI" testclass="JSR223PreProcessor" testname="读取全局Token" enabled="true">
  <stringProp name="scriptLanguage">groovy</stringProp>
  <stringProp name="filename"></stringProp>
  <stringProp name="parameters"></stringProp>
  <boolProp name="cacheKey">true</boolProp>
  <stringProp name="script">vars.put("token", props.get("g_token")); vars.put("userId", props.get("g_userId"));</stringProp>
</JSR223PreProcessor>
<hashTree/>
```

### ❌ PostProcessor 不能放在 Sampler 外部

PostProcessor（包括 JSR223PostProcessor、JSONPostProcessor）**必须放在对应 Sampler 的 `<hashTree>` 内部**。放在外部会在 Sampler 执行前触发，此时 `vars` 中尚无提取值，`props.put(null)` 抛 `NullPointerException`。

```xml
<!-- ❌ 错误：PostProcessor 在 Sampler 外部 -->
<HTTPSamplerProxy .../>
<hashTree>
  <JSONPostProcessor ... 提取Token/>
  <hashTree/>
</hashTree>
<JSR223PostProcessor ... 保存Token/>   <!-- 此时 vars.get("token") = null -->
<hashTree/>

<!-- ✅ 正确：PostProcessor 在 Sampler 内部 -->
<HTTPSamplerProxy .../>
<hashTree>
  <JSONPostProcessor ... 提取Token/>
  <hashTree/>
  <JSR223PostProcessor ... 保存Token/>  <!-- vars.get("token") 有值 -->
  <hashTree/>
</hashTree>
```

**规则**：凡是需要读取当前 Sampler 响应结果的 PostProcessor，一律放进该 Sampler 的 `<hashTree>` 里，紧跟在 JSONPostProcessor 之后。

## 基础 JMX 结构

见 [references/jmx-templates.md](references/jmx-templates.md)

## 命名规范

见 [references/naming-conventions.md](references/naming-conventions.md)

## 输出要求

生成的 JMX 文件必须：
- 默认保存路径为项目根目录下的 `jmeter/` 文件夹，文件名格式为 `{项目名}-{模块名}-Test.jmx`
- 使用完整缩进多行 XML 格式，禁止单行压缩格式
- `TestPlan.arguments` 的 `collectionProp` 保持空，所有变量放在独立 `Arguments` 配置元件中
- 独立 `Arguments` 元件放在 TestPlan `<hashTree>` 的第一个位置
- 监听器（察看结果树、聚合报告）与 ThreadGroup 同级，不放在 ThreadGroup 内部
- 可直接导入 JMeter 运行，无语法错误
- 包含完整的接口依赖关系处理
- 写操作包含三层断言：HTTP 状态码 + 业务码 + 业务结果
- 包含操作后回查的 JSONPath 逐字段精确验证
- 枚举参数的每个取值生成独立请求链，变量名隔离
