# JMX 基础结构模板

## 目录
- [测试计划基础结构](#测试计划基础结构)
- [线程组配置](#线程组配置)
- [HTTP 请求配置](#http-请求配置)
- [变量提取器](#变量提取器)
- [监听器配置](#监听器配置)

---

## 测试计划基础结构

> **⚠️ GUI 显示规则（必须遵守）**
>
> 1. **`TestPlan.arguments` 必须留空**：`<collectionProp name="Arguments.arguments"/>` 不放任何变量，否则变量会被合并进 TestPlan 节点，GUI 树中不会单独显示
> 2. **独立 `Arguments` 元件放在 TestPlan 的 `<hashTree>` 第一个位置**，后面紧跟 `<hashTree/>`，这样 GUI 树中才会显示为独立的 `User Defined Variables` 节点
> 3. **监听器必须与 ThreadGroup 同级**，放在 ThreadGroup 的 `</hashTree>` 之后，不能放在 ThreadGroup 内部，否则 hashTree 层级错乱导致整个树渲染异常
> 4. **使用完整缩进多行格式**，不使用单行压缩格式，避免 hashTree 层级计数错误
> 5. **每个测试元件后必须紧跟 `<hashTree/>`**：`JSONPostProcessor`、`JSR223PostProcessor`、`ResponseAssertion`、`JSONPathAssertion`、`HeaderManager` 等所有直接子元件，缺少时报 `ClassCastException: XXX cannot be cast to HashTree`，脚本无法打开
> 6. **XML 注释中禁止出现 `--`**：`<!-- ---- 标题 ---- -->` 是非法 XML，改用 `<!-- ==== 标题 ==== -->`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="{USER_PROVIDED_VERSION}">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="API接口测试计划" enabled="true">
      <stringProp name="TestPlan.comments">基于OpenAPI文档自动生成的JMeter测试脚本</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">true</boolProp>
      <!-- TestPlan.arguments 必须留空，变量统一放下方独立 Arguments 元件 -->
      <elementProp name="TestPlan.arguments" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>

      <!-- ① 独立 User Defined Variables（GUI树中可见，必须放第一位） -->
      <Arguments guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments">
          <elementProp name="BASE_URL" elementType="Argument">
            <stringProp name="Argument.name">BASE_URL</stringProp>
            <stringProp name="Argument.value">localhost</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="PORT" elementType="Argument">
            <stringProp name="Argument.name">PORT</stringProp>
            <stringProp name="Argument.value">8080</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="BASE_PATH" elementType="Argument">
            <stringProp name="Argument.name">BASE_PATH</stringProp>
            <stringProp name="Argument.value">/api</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
        </collectionProp>
      </Arguments>
      <hashTree/>

      <!-- ② HTTP 请求默认值，domain 引用变量 -->
      <ConfigTestElement guiclass="HttpDefaultsGui" testclass="ConfigTestElement" testname="HTTP Request Defaults" enabled="true">
        <stringProp name="HTTPSampler.domain">${BASE_URL}</stringProp>
        <stringProp name="HTTPSampler.port">${PORT}</stringProp>
        <stringProp name="HTTPSampler.protocol">http</stringProp>
        <stringProp name="HTTPSampler.contentEncoding">UTF-8</stringProp>
        <intProp name="HTTPSampler.connect_timeout">10000</intProp>
        <intProp name="HTTPSampler.response_timeout">30000</intProp>
        <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
          <collectionProp name="Arguments.arguments"/>
        </elementProp>
      </ConfigTestElement>
      <hashTree/>

      <!-- ③ 全局请求头 -->
      <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="Global Headers" enabled="true">
        <collectionProp name="HeaderManager.headers">
          <elementProp name="" elementType="Header">
            <stringProp name="Header.name">Content-Type</stringProp>
            <stringProp name="Header.value">application/json;charset=UTF-8</stringProp>
          </elementProp>
          <elementProp name="" elementType="Header">
            <stringProp name="Header.name">Accept</stringProp>
            <stringProp name="Header.value">application/json</stringProp>
          </elementProp>
        </collectionProp>
      </HeaderManager>
      <hashTree/>

      <!-- ④ ThreadGroup 在此生成 -->
      <ThreadGroup ...>...</ThreadGroup>
      <hashTree>
        <!-- 请求放这里 -->
      </hashTree>

      <!-- ⑤ 监听器与 ThreadGroup 同级，不能放在 ThreadGroup 内部 -->
      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="察看结果树" enabled="true">
        ...
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="StatVisualizer" testclass="ResultCollector" testname="聚合报告" enabled="true">
        ...
      </ResultCollector>
      <hashTree/>

    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

---

## 线程组配置

```xml
<ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="API测试线程组">
  <intProp name="ThreadGroup.num_threads">1</intProp>
  <intProp name="ThreadGroup.ramp_time">1</intProp>
  <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
  <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
  <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="循环控制器">
    <stringProp name="LoopController.loops">1</stringProp>
    <boolProp name="LoopController.continue_forever">false</boolProp>
  </elementProp>
</ThreadGroup>
```

---

## HTTP 请求配置

### POST 请求（JSON Body）

```xml
<elementProp name="HTTPsampler.Arguments" elementType="Arguments">
  <collectionProp name="Arguments.arguments">
    <elementProp name="" elementType="HTTPArgument">
      <boolProp name="HTTPArgument.always_encode">false</boolProp>
      <stringProp name="Argument.value">{JSON_BODY}</stringProp>
      <stringProp name="Argument.metadata">=</stringProp>
    </elementProp>
  </collectionProp>
</elementProp>
```

### GET 请求（Query 参数）

```xml
<elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
  <collectionProp name="Arguments.arguments">
    <elementProp name="paramName" elementType="HTTPArgument">
      <boolProp name="HTTPArgument.always_encode">false</boolProp>
      <stringProp name="Argument.value">paramValue</stringProp>
      <stringProp name="Argument.metadata">=</stringProp>
      <boolProp name="HTTPArgument.use_equals">true</boolProp>
      <stringProp name="Argument.name">paramName</stringProp>
    </elementProp>
  </collectionProp>
</elementProp>
```

---

## 变量提取器

### JSON 提取器（提取 token / ID）

```xml
<JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="提取Token">
  <stringProp name="JSONPostProcessor.referenceNames">token</stringProp>
  <stringProp name="JSONPostProcessor.jsonPathExprs">$.token</stringProp>
  <stringProp name="JSONPostProcessor.match_numbers">1</stringProp>
  <stringProp name="JSONPostProcessor.defaultValues">NOT_FOUND</stringProp>
</JSONPostProcessor>
<hashTree/>
```

**变量命名规范**：
- 认证令牌：`token`
- 新创建资源ID：`newResourceId`（按资源类型命名，如 `newUserId`）
- 枚举值产生的变量需隔离命名（如 `digitalHumanTaskId`、`pptTaskId`）

---

## 监听器配置

### 查看结果树

```xml
<ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="察看结果树">
  <boolProp name="ResultCollector.error_logging">false</boolProp>
  <objProp>
    <name>saveConfig</name>
    <value class="SampleSaveConfiguration">
      <time>true</time>
      <latency>true</latency>
      <timestamp>true</timestamp>
      <success>true</success>
      <label>true</label>
      <code>true</code>
      <message>true</message>
      <threadName>true</threadName>
      <dataType>true</dataType>
      <encoding>false</encoding>
      <assertions>true</assertions>
      <subresults>true</subresults>
      <responseData>false</responseData>
      <samplerData>false</samplerData>
      <xml>false</xml>
      <fieldNames>true</fieldNames>
      <responseHeaders>false</responseHeaders>
      <requestHeaders>false</requestHeaders>
      <responseDataOnError>false</responseDataOnError>
      <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
      <assertionsResultsToSave>0</assertionsResultsToSave>
      <bytes>true</bytes>
      <sentBytes>true</sentBytes>
      <url>true</url>
      <threadCounts>true</threadCounts>
      <idleTime>true</idleTime>
      <connectTime>true</connectTime>
    </value>
  </objProp>
  <stringProp name="filename"></stringProp>
</ResultCollector>
```

### 聚合报告

```xml
<ResultCollector guiclass="StatVisualizer" testclass="ResultCollector" testname="聚合报告">
  <boolProp name="ResultCollector.error_logging">false</boolProp>
  <objProp>
    <name>saveConfig</name>
    <value class="SampleSaveConfiguration">
      <!-- 同查看结果树配置 -->
    </value>
  </objProp>
  <stringProp name="filename"></stringProp>
</ResultCollector>
```
