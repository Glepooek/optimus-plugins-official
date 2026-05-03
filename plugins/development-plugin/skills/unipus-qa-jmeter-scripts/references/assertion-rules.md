# 断言规范与 XML 模板

## 目录
- [基础断言：HTTP 状态码](#基础断言http-状态码)
- [规范3.1：数据一致性验证](#规范31数据一致性验证)
- [规范3.2：增删改业务逻辑断言](#规范32增删改业务逻辑断言)
- [规范3.3：数据结构完整性验证（JSONPath）](#规范33数据结构完整性验证jsonpath)
- [规范3.4：参数枚举值全覆盖](#规范34参数枚举值全覆盖)

---

## 基础断言：HTTP 状态码

```xml
<ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="接口成功断言">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="49586">200</stringProp>
  </collectionProp>
  <stringProp name="Assertion.custom_message">接口应该返回200状态码</stringProp>
  <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
  <boolProp name="Assertion.assume_success">false</boolProp>
  <intProp name="Assertion.test_type">1</intProp>
</ResponseAssertion>
<hashTree/>
```

---

## 规范3.1：数据一致性验证

仅验证 HTTP 200 不够，必须对 CRUD 操作结果做数据一致性验证。

### 验证时机

| 操作 | 验证时机 | 验证内容 |
|------|---------|---------|
| 创建/保存 | 保存后查列表 | 列表包含新创建的 ID 和名称 |
| 创建/保存 | 保存后查详情 | 关键字段与提交值一致 |
| 更新 | 更新后重新获取详情（序号 N.1） | 已更新字段变为新值 |
| 删除 | 删除后查列表（可选） | 列表不再包含已删除 ID |

### 列表存在性验证（test_type=2 即 Contains）

```xml
<ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="验证列表包含新保存的资源" enabled="true">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="0">${resourceId}</stringProp>
  </collectionProp>
  <stringProp name="Assertion.custom_message">列表中应包含刚保存的资源ID: ${resourceId}</stringProp>
  <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
  <boolProp name="Assertion.assume_success">false</boolProp>
  <intProp name="Assertion.test_type">2</intProp>
</ResponseAssertion>
<hashTree/>
```

### 删除后列表不存在验证（test_type=6 即 NOT Contains）

```xml
<ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="验证列表不包含已删除的资源" enabled="true">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="0">${deletedResourceId}</stringProp>
  </collectionProp>
  <stringProp name="Assertion.custom_message">列表中不应包含已删除的资源ID: ${deletedResourceId}</stringProp>
  <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
  <boolProp name="Assertion.assume_success">false</boolProp>
  <intProp name="Assertion.test_type">6</intProp>
</ResponseAssertion>
<hashTree/>
```

**test_type 值说明**：`1`=等于，`2`=包含（Contains），`6`=不包含（NOT Contains = 2+4）

### ID 一致性验证（BeanShell）

```xml
<BeanShellAssertion guiclass="BeanShellAssertionGui" testclass="BeanShellAssertion" testname="验证资源ID一致性" enabled="true">
  <stringProp name="BeanShellAssertion.query">
String savedId = vars.get("savedResourceId");
String detailId = vars.get("detailResourceId");
if (savedId == null || detailId == null || !savedId.equals(detailId)) {
    Failure = true;
    FailureMessage = "资源ID不一致: 保存返回=" + savedId + ", 详情返回=" + detailId;
}
  </stringProp>
  <stringProp name="BeanShellAssertion.filename"></stringProp>
  <stringProp name="BeanShellAssertion.parameters"></stringProp>
  <boolProp name="BeanShellAssertion.resetInterpreter">false</boolProp>
</BeanShellAssertion>
```

---

## 规范3.2：增删改业务逻辑断言

所有写操作必须验证：HTTP 200 + 业务码(code=0) + 业务结果字段。

### 完整断言清单

| 操作 | 必选断言 |
|------|---------|
| 创建/保存 | HTTP 200 + code=0 + 返回有效ID（value 不为 0/null/""） |
| 更新/修改 | HTTP 200 + code=0 + value=true + 回查详情验证字段变更 |
| 删除 | HTTP 200 + code=0 + value=true + 回查验证不存在（推荐） |

### 业务码断言（JSONPathAssertion）

```xml
<JSONPathAssertion guiclass="JSONPathAssertionGui" testclass="JSONPathAssertion" testname="保存资源业务码断言" enabled="true">
  <stringProp name="JSON_PATH">$.code</stringProp>
  <stringProp name="EXPECTED_VALUE">0</stringProp>
  <boolProp name="JSONVALIDATION">true</boolProp>
  <boolProp name="EXPECT_NULL">false</boolProp>
  <boolProp name="INVERT">false</boolProp>
  <boolProp name="ISREGEX">false</boolProp>
</JSONPathAssertion>
<hashTree/>
```

### 更新/删除接口：value=true 验证

```xml
<ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="更新资源结果断言" enabled="true">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="0">"value":true</stringProp>
  </collectionProp>
  <stringProp name="Assertion.custom_message">更新操作应返回value:true，表示更新成功</stringProp>
  <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
  <boolProp name="Assertion.assume_success">false</boolProp>
  <intProp name="Assertion.test_type">2</intProp>
</ResponseAssertion>
<hashTree/>
```

### 断言命名规范

- HTTP 状态码：`{操作}{资源名}成功断言`（如：`保存背景图成功断言`）
- 业务码：`{操作}{资源名}业务码断言`（如：`更新背景图业务码断言`）
- 业务结果：`{操作}{资源名}结果断言`（如：`删除背景图结果断言`）
- 有效ID：`验证{操作}返回有效ID`

---

## 规范3.3：数据结构完整性验证（JSONPath）

写操作后，必须通过详情接口使用 JSONPathAssertion 逐字段精确验证落库数据。

### 实施流程

```
1. 分析 API 文档 → 获取详情接口响应数据结构（字段名、路径、类型）
2. 分析写操作请求体 → 确定提交了哪些字段及值
3. 建立映射：请求字段 → 响应 JSONPath 路径
4. 生成回查请求（操作后调用详情/列表接口）
5. 为每个提交字段生成 JSONPathAssertion
```

### 字段路径映射规则

当详情接口响应结构为 `{code, msg, value: {...}}` 时：

| 请求字段 | 详情响应 JSONPath |
|---------|-----------------|
| `name` | `$.value.name` |
| `description` | `$.value.description` |
| `xxxUrl` | `$.value.xxxUrl` |
| `id`（更新/删除时传入） | `$.value.id` |
| 数值字段（`width`、`size`） | `$.value.width` |
| 嵌套字段 | `$.value.parent.child` |

### 创建后详情回查 JSONPath 断言

```xml
<!-- 验证名称字段 -->
<JSONPathAssertion guiclass="JSONPathAssertionGui" testclass="JSONPathAssertion" testname="验证详情名称字段" enabled="true">
  <stringProp name="JSON_PATH">$.value.name</stringProp>
  <stringProp name="EXPECTED_VALUE">保存时提交的名称</stringProp>
  <boolProp name="JSONVALIDATION">true</boolProp>
  <boolProp name="EXPECT_NULL">false</boolProp>
  <boolProp name="INVERT">false</boolProp>
  <boolProp name="ISREGEX">false</boolProp>
</JSONPathAssertion>
<hashTree/>

<!-- 验证 URL 类字段 -->
<JSONPathAssertion guiclass="JSONPathAssertionGui" testclass="JSONPathAssertion" testname="验证详情URL字段" enabled="true">
  <stringProp name="JSON_PATH">$.value.imageUrl</stringProp>
  <stringProp name="EXPECTED_VALUE">https://example.com/saved_resource.png</stringProp>
  <boolProp name="JSONVALIDATION">true</boolProp>
  <boolProp name="EXPECT_NULL">false</boolProp>
  <boolProp name="INVERT">false</boolProp>
  <boolProp name="ISREGEX">false</boolProp>
</JSONPathAssertion>
<hashTree/>

<!-- 验证 ID 与保存返回一致 -->
<JSONPathAssertion guiclass="JSONPathAssertionGui" testclass="JSONPathAssertion" testname="验证详情ID与保存返回一致" enabled="true">
  <stringProp name="JSON_PATH">$.value.id</stringProp>
  <stringProp name="EXPECTED_VALUE">${savedResourceId}</stringProp>
  <boolProp name="JSONVALIDATION">true</boolProp>
  <boolProp name="EXPECT_NULL">false</boolProp>
  <boolProp name="INVERT">false</boolProp>
  <boolProp name="ISREGEX">false</boolProp>
</JSONPathAssertion>
<hashTree/>
```

### 删除后验证资源不存在

**方式一**：接口对不存在资源返回非 0 错误码（`INVERT=true`）
```xml
<JSONPathAssertion testname="验证删除后详情返回错误码" enabled="true">
  <stringProp name="JSON_PATH">$.code</stringProp>
  <stringProp name="EXPECTED_VALUE">0</stringProp>
  <boolProp name="JSONVALIDATION">true</boolProp>
  <boolProp name="EXPECT_NULL">false</boolProp>
  <boolProp name="INVERT">true</boolProp>
  <boolProp name="ISREGEX">false</boolProp>
</JSONPathAssertion>
<hashTree/>
```

**方式二**：接口对不存在资源返回 `value: null`（`EXPECT_NULL=true`）
```xml
<JSONPathAssertion testname="验证删除后详情value为空" enabled="true">
  <stringProp name="JSON_PATH">$.value</stringProp>
  <stringProp name="EXPECTED_VALUE">null</stringProp>
  <boolProp name="JSONVALIDATION">false</boolProp>
  <boolProp name="EXPECT_NULL">true</boolProp>
  <boolProp name="INVERT">false</boolProp>
  <boolProp name="ISREGEX">false</boolProp>
</JSONPathAssertion>
<hashTree/>
```

### 回查请求命名规范

- 格式：`{原序号}.1-验证{操作后}资源详情`
- 示例：`5.1-验证更新后用户详情`、`6.1-验证删除后查询详情`

### 断言命名规范

- 创建后字段：`验证详情{字段名}字段`
- 更新后字段：`验证{字段名}已更新`
- 未修改字段：`验证{字段名}未被修改`
- 删除后验证：`验证删除后详情返回错误码` / `验证删除后详情value为空`

---

## 规范3.4：参数枚举值全覆盖

同一接口的同一参数如有 N 个枚举值，必须生成 N 个独立请求。

### 枚举值识别特征

| 特征 | 说明 |
|------|------|
| `enum` 定义 | OpenAPI 文档中明确定义了 enum 值 |
| 业务类型字段 | 参数名含 `type`、`operation`、`action`、`mode`、`category` |
| 文档多义说明 | 描述中列出"1-文本 2-图片 3-视频"等 |
| 状态流转字段 | 表示资源状态变化，如 `status=0` 草稿、`status=1` 发布 |

### 请求生成规则

```
原始接口：/task/submit（operation 参数有多个值）

生成请求：
  25-提交任务(数字人解析)  → operation=1
  26-提交任务(PPT解析)    → operation=3
  27-提交任务(视频合成)   → operation=5
```

**命名格式**：`{序号}-{接口功能}({枚举值业务含义})`

### 变量隔离（不同枚举值使用不同变量名）

```xml
<!-- operation=1 产生的变量 -->
<JSONPostProcessor testname="提取数字人任务ID">
  <stringProp name="JSONPostProcessor.referenceNames">digitalHumanTaskId</stringProp>
  <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.taskId</stringProp>
</JSONPostProcessor>

<!-- operation=3 产生的变量 -->
<JSONPostProcessor testname="提取PPT解析任务ID">
  <stringProp name="JSONPostProcessor.referenceNames">pptTaskId</stringProp>
  <stringProp name="JSONPostProcessor.jsonPathExprs">$.data.taskId</stringProp>
</JSONPostProcessor>
```

### 后续关联请求也需按枚举值分别覆盖

```
提交任务(数字人解析) → 查询任务状态(数字人) → 获取任务结果(数字人)
提交任务(PPT解析)   → 查询任务状态(PPT)   → 获取任务结果(PPT)
```

每条链路使用各自独立的变量，链路之间互不干扰。
