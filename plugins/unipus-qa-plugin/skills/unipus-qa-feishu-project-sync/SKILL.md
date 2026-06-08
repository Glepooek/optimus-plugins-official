---
name: unipus-qa-feishu-project-sync
description: 将测试产物同步到飞书项目的统一工具，支持三种模式：(1) 同步测试计划——用户说"同步测试计划"、"上传测试计划到飞书"、"创建飞书测试计划"时触发，输入为 docs/ 下的测试计划 Markdown；(2) 导入测试用例——用户说"导入用例到飞书"、"同步测试用例"、"上传用例到飞书项目"时触发，输入为 testcases/ 下的测试用例 Markdown；(3) 提交失败缺陷——用户说"提交缺陷"、"提交bug"、"把失败用例提交到飞书"、"自动提bug"时触发，输入为 Playwright/Midscene 测试报告。
creator：yinxuan@unipus.cn
---

# 飞书项目同步（统一入口）

## 概述

本 skill 是三类飞书项目同步操作的统一入口：

| 模式 | 触发词 | 输入 | 输出 |
|------|--------|------|------|
| **A：同步测试计划** | 同步测试计划、上传测试计划到飞书、创建飞书测试计划 | `docs/*.md` | 飞书测试计划工作项 |
| **B：导入测试用例** | 导入用例到飞书、同步测试用例、上传用例到飞书项目 | `testcases/*.md` | 飞书测试用例工作项（批量） |
| **C：提交失败缺陷** | 提交缺陷、提交bug、把失败用例提交到飞书、自动提bug | 测试报告 JSON/HTML | 飞书缺陷工作项 |

---

## Step 0：识别模式

根据用户的触发词和输入类型，判断执行哪个模式，然后跳转到对应章节：

- 提到"测试计划" → **模式 A**
- 提到"测试用例"/"用例"导入 → **模式 B**
- 提到"缺陷"/"bug"/"失败用例" → **模式 C**

若无法判断，询问用户：「请问您要：(A) 同步测试计划、(B) 导入测试用例，还是 (C) 提交失败缺陷？」

---

## 模式 A：同步测试计划

### A-Step 1：读取并解析测试计划文档

1a. 读取用户指定的测试计划 Markdown 文件（通常在 `docs/` 目录下）

1b. 从文档中提取以下关键信息：

| 信息 | 提取方式 | 写入飞书 | 示例 |
|------|---------|---------|------|
| 计划名称 | H1 标题 | ✓ 工作项名称 | LMS口语练习管理功能 测试计划 |
| 测试范围 | §2 测试范围 | ✓ 描述字段 | 功能测试 + 非功能测试 + 范围外 |
| 项目背景 | §1 项目概述 | ✗ 仅本地 | 系统功能概述和测试目标 |
| 测试策略 | §3 测试策略 | ✗ 仅本地 | 测试类型、优先级划分 |
| 时间安排 | §5/§6 测试计划安排 | ✗ 仅本地 | 阶段划分、详细时间表 |
| 风险评估 | §8 风险评估 | ✗ 仅本地 | 风险项和应对措施 |

> 仅"计划名称"和"测试范围"写入飞书，其余章节保留在本地 Markdown 文档中。

1c. 验证文档结构：至少包含测试范围章节（含功能测试和非功能测试小节）

### A-Step 2：确认飞书项目信息

收集以下信息（优先从上下文或记忆中获取）：

| 信息 | 必要性 | 说明 |
|------|--------|------|
| 飞书项目空间 | 必需 | project_key 或 simpleName（如 `jsgx2023`） |
| 计划名称前缀 | 推荐 | 如 `【招采】`，便于在飞书中识别归属 |
| 关联需求 ID | 可选 | 需要手动关联（MCP 限制） |

查询空间信息确认 project_key：
```
工具：search_project_info
参数：project_key: {空间simpleName}
```

### A-Step 3：获取测试计划模板 ID

通过 MQL 查询已有测试计划获取模板 ID：
```
工具：search_by_mql
mql: SELECT `work_item_id`, `name`, `template`
     FROM `{空间}`.`测试计划` LIMIT 1
```

若无已有测试计划，通过 `get_workitem_field_meta` 获取：
```
工具：get_workitem_field_meta
参数：
  project_key: {空间key}
  work_item_type: {测试计划类型key}
```

> ⚠️ 工作项类型 key 因空间不同而异，不可硬编码，首次使用时通过 `list_workitem_types` 查询。

### A-Step 4：创建测试计划工作项

```
工具：create_workitem
参数：
  project_key: {空间key}
  work_item_type: {测试计划类型key}
  fields:
    - field_key: template
      field_value: "{模板ID}"
    - field_key: name
      field_value: "{前缀}{测试计划名称}"
```

记录返回的 `work_item_id` 和 `url`。

### A-Step 5：写入测试范围内容

从测试计划文档中提取"测试范围"章节（通常为 §2），写入描述字段：
```
工具：update_field
参数：
  project_key: {空间key}
  work_item_id: {刚创建的ID}
  fields:
    - field_key: description
      field_value: "{测试范围章节的 Markdown 内容}"
```

写入内容结构：
```markdown
## 测试范围

### 功能测试
- **模块A**：功能点列表...

### 非功能测试
- **性能测试**：指标列表...
- **安全测试**：测试项列表...
- **兼容性测试**：浏览器/设备列表...

### 测试范围外
- 排除项列表...
```

> 代码块省略（飞书描述不支持代码块渲染）

### A-Step 6：记录同步结果

在测试计划 Markdown 文件**开头**添加同步记录：

```markdown
## 飞书项目同步记录

> 空间：{simpleName} ({空间全名})
> 测试计划 ID：{work_item_id}
> 飞书链接：[查看](https://project.feishu.cn/{simpleName}/test_plans/detail/{work_item_id})
> 同步时间：{YYYY-MM-DD}
> 同步状态：已创建
```

展示创建结果并提示需手动完成的操作：

> 以下操作需在飞书项目页面手动完成：
> 1. **关联需求** — 在测试计划详情页添加关联需求
> 2. **指派负责人** — 设置测试计划负责人
> 3. **状态流转** — 从"未开始"流转为"进行中"
> 4. **关联测试用例** — 如已导入测试用例，在计划中添加关联

---

## 模式 B：导入测试用例

### B-Step 1：读取并解析测试用例文档

1a. 读取输入文件（`testcases/*.md`）

1b. 逐行解析 Markdown 结构，提取每条用例：
- 用例标题（H5）
- 功能模块（H2）、测试点（H3）、验证点（H4）
- 需求 ID、优先级、测试步骤、预期结果（H6 下的列表项）

1c. 同时支持解析表格格式的测试用例（如 `.kiro/specs/` 下的文件）：
- 从表格列中提取：用例编号、用例名称、前置条件、测试步骤、预期结果、优先级
- 从 H2 标题中提取模块名和需求编号

1d. 如果文件中已有"飞书项目导入记录"，提示用户是否跳过已导入的用例

### B-Step 2：收集飞书项目信息

收集以下信息（优先从文件导入记录或上下文中获取）：

| 信息 | 必要性 | 说明 |
|------|--------|------|
| 飞书项目空间 | 必需 | project_key 或 simpleName |
| 项目名称前缀 | 推荐 | 如 `AI智课`，用于生成 `[AI智课][模块名]` 格式标题 |
| 关联需求 ID | 可选 | 创建后需手动关联 |
| 关联测试计划 ID | 可选 | 创建后需手动关联 |

查询空间信息：
```
工具：search_project_info
参数：project_key: {空间simpleName}
```

### B-Step 3：获取测试用例模板和字段配置

3a. 获取工作项类型 key：
```
工具：list_workitem_types
参数：project_key: {空间key}
```

3b. 获取模板 ID（查询已有测试用例）：
```
工具：search_by_mql
mql: SELECT `name`, `work_item_id` FROM `{空间}`.`测试用例` LIMIT 1
```
然后通过 `get_workitem_brief` 获取模板 ID。

3c. 确认字段枚举值（首次使用时）：
```
工具：search_by_mql
mql: SELECT `name`, `priority`, `field_ad0ad4`, `field_e42a97` FROM `{空间}`.`测试用例` LIMIT 1
```

> 详细字段映射见 [references/testcase-fields.md](references/testcase-fields.md)

### B-Step 4：逐条创建测试用例

对每条用例调用 `create_workitem`：

```
工具：create_workitem
参数：
  project_key: {空间key}
  work_item_type: {测试用例类型key}
  fields:
    - template: {模板ID}
    - name: "[{项目名}][{模块名}]{用例标题}"
    - field_f717b4（前置条件）: "{模块路径} [需求ID: {需求ID}]"
    - priority（优先级）: 根据用例优先级映射
    - field_ad0ad4（用例分级）: 根据用例优先级映射
    - field_e42a97（用例类型）: '[{"option_id":"testcase_function"}]'
```

> ⚠️ **前置条件字段仅填写模块路径和需求 ID**，不要把测试步骤和预期结果写入前置条件。

每创建 5 条用例输出一次进度：
```
已创建 5/32 条用例...
已创建 10/32 条用例...
```

### B-Step 5：回写飞书 ID 到源文件

5a. 在每条用例的 H6 区域追加飞书 ID：

```markdown
##### 用例场景描述
###### 飞书ID
- {飞书工作项ID}
###### 需求ID
- FR-001
###### 测试步骤
- 1. xxx
```

5b. 在文件开头添加导入记录汇总表：

```markdown
## 飞书项目导入记录

> 空间：{simpleName} ({空间全名})
> 关联需求：{需求ID}（{需求名称}）
> 关联测试计划：{测试计划ID}（{测试计划名称}）

| 用例标题 | 飞书工作项ID | 飞书链接 | 导入时间 |
|---------|------------|---------|---------|
| {用例标题1} | {ID1} | [查看](https://project.feishu.cn/{simpleName}/testCase/detail/{ID1}) | {日期} |
```

### B-Step 6：汇总输出

展示创建结果并提示需手动完成的操作：

> 以下操作需在飞书项目页面手动完成：
> 1. **关联测试计划** — 打开测试计划页面 → 添加关联测试用例
> 2. **关联需求** — 打开需求页面 → 添加关联测试用例
> 3. **状态流转** — 将状态从"待评审"改为"评审通过"
> 4. **补充步骤和预期结果** — 推荐通过飞书项目 XMind 导入或手动编辑

---

## 模式 C：提交失败缺陷

### C-Step 1：定位并解析测试结果

1a. 确定测试结果来源（按优先级）：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | 用户提供的报告路径 | 如 `midscene_run/report/playwright-merged-*.html` |
| 2 | Playwright JSON 结果 | `test-results/*-result.json` |
| 3 | 自定义报告 JSON | `test-report/test-report-*.json` |

1b. 递归遍历 `suites` 结构，提取每条用例的 `title`、`status`、`duration`、`error.message`

1c. 从用例标题中提取元数据：

| 标签 | 正则 | 示例 |
|------|------|------|
| 用例编号 | `(TC-\w+-\d+)` | TC-DH-004 |
| 需求ID | `@(FR-\d+)` | FR-003 |
| 飞书用例ID | `@feishu:(\d+)` | 6930726641 |

1d. 筛选失败用例：仅处理 `status === 'failed'` 的用例。

### C-Step 2：确认提交信息

2a. 展示失败用例列表供用户确认：

```
检测到以下失败用例：

| # | 用例 | 错误摘要 | 飞书用例ID |
|---|------|---------|-----------|
| 1 | TC-DH-004: 上传MP4视频生成形象 @FR-003 | worker process exited unexpectedly | - |

是否全部提交为缺陷？（全部提交 / 选择提交 / 取消）
```

2b. 收集飞书项目信息（如用户未提供则询问）：

| 信息 | 必要性 | 默认值 |
|------|--------|--------|
| 飞书项目空间 | 必需 | 从测试用例 Markdown 的飞书导入记录中读取 |
| 关联需求 ID | 推荐 | 从用例标题 `@FR-xxx` 反查 |
| 报告人 | 必需 | 询问用户姓名/邮箱，通过 `search_user_info` 获取 user_key |
| 缺陷严重程度 | 可选 | 默认"重要"（severity=2） |
| Bug 端分类 | 可选 | 默认"前端"（fe） |

### C-Step 3：获取飞书项目字段配置

3a. 查询空间信息：
```
工具：search_project_info
参数：project_key: {空间simpleName}
```

3b. 通过 MQL 查询已有缺陷获取字段枚举值：
```
工具：search_by_mql
mql: SELECT `work_item_id`, `name`, `priority`, `severity`, `issue_stage`, `bug_classification`, `template`
     FROM `{空间}`.`缺陷` LIMIT 1
```

**常用字段枚举值参考**（以 jsgx2023 空间为例）：

| 字段 | field_key | 枚举值 |
|------|-----------|--------|
| 优先级 | `priority` | `1`=核心, `2`=高, `3`=中, `4`=低 |
| 严重程度 | `severity` | `1`=严重, `2`=重要, `3`=一般, `4`=次要, `5`=微小 |
| 发现阶段 | `issue_stage` | `stage_test`=测试阶段 |
| Bug端分类 | `bug_classification` | `fe`=前端, `server`=后端, `ios`=iOS, `android`=Android |
| 缺陷类型(模板) | `template` | `305027`=普通缺陷 |

> ⚠️ 枚举值因空间配置不同可能不一致，首次使用时通过 MQL 查询确认。

3c. 获取报告人 user_key：
```
工具：search_user_info
参数：project_key: {空间key}, user_keys: ["{用户姓名或邮箱}"]
```

### C-Step 4：逐条创建缺陷

对每条确认提交的失败用例，调用 `create_workitem`：

```
工具：create_workitem
参数：
  project_key: {空间key}
  work_item_type: issue
  fields:
    - template: {模板ID}（如 305027）
    - name: "【{产品标签}】{缺陷标题}（{用例编号}）"
    - description: {缺陷描述，Markdown 格式}
    - priority: {优先级}（默认 1=核心）
    - severity: {严重程度}（默认 2=重要）
    - issue_stage: "stage_test"
    - bug_classification: {Bug端分类}（默认 fe）
    - issue_reporter: ["{报告人user_key}"]
    - _field_linked_story: {关联需求ID}（如有）
```

缺陷描述模板：
```markdown
## 缺陷描述
{根据用例标题和错误信息生成的缺陷描述}

## 复现步骤
{从测试用例 Markdown 中提取对应用例的测试步骤}

## 预期结果
{从测试用例 Markdown 中提取预期结果}

## 实际结果
{测试执行的错误信息}

## 测试环境
- 浏览器：Chrome (Desktop)
- 分辨率：{从 Playwright 配置中读取}
- 测试框架：Playwright + Midscene
- 关联用例：{用例编号} @{需求ID}
- 自动化报告：{报告文件路径}
```

缺陷标题格式：`【{产品标签}】{缺陷描述}（{用例编号}）`

产品标签来源：① 测试用例 Markdown H1 标题 → ② 用例标题前缀 → ③ 用户手动指定

### C-Step 5：汇总输出

展示创建结果：
```
缺陷提交完成：

| 用例 | 缺陷ID | 飞书链接 | 状态 |
|------|--------|---------|------|
| TC-DH-004 上传MP4视频生成形象 | 6930697901 | [查看](...) | 已创建 |
```

> 以下操作需在飞书项目页面手动完成：
> - 指派处理人（MCP 无法设置 `assignee` 角色字段）
> - 关联测试计划（`relation_*` 字段写入会静默失败）
> - 上传截图/录屏附件（MCP 不支持文件上传）

---

## 已知限制（所有模式通用）

| 限制 | 说明 | 应对方式 |
|------|------|---------|
| 关联关系字段 | `relation_*` 字段写入静默失败 | 手动关联需求/测试计划 |
| 状态流转 | `work_item_status` 无法通过 API 修改 | 手动流转状态 |
| 附件上传 | MCP 不支持文件附件 | 手动上传 |
| 枚举值差异 | option_id 因空间不同可能不一致 | 首次使用时 MQL 确认 |
| 描述长度 | 飞书描述字段有长度限制 | 模式 A 仅写入测试范围章节 |
| 测试步骤/预期结果 | 内置复合字段，MCP 无法写入 | 通过 XMind 导入或手动编辑 |

## 质量检查

**模式 A（测试计划）**
- [ ] 正确读取测试计划 Markdown 文件
- [ ] 空间信息和模板 ID 获取正确
- [ ] 测试计划工作项创建成功
- [ ] 描述字段仅包含测试范围章节
- [ ] 同步记录已写入源 Markdown 文件
- [ ] 已向用户展示飞书链接

**模式 B（测试用例）**
- [ ] 正确解析测试用例文档（支持六级 Markdown 和表格两种格式）
- [ ] 每条用例创建成功，名称格式正确
- [ ] 前置条件包含模块路径和需求 ID（不含测试步骤）
- [ ] 优先级和用例分级字段映射正确
- [ ] 飞书 ID 已回写到源 Markdown 文件
- [ ] 导入记录汇总表已写入文件开头

**模式 C（失败缺陷）**
- [ ] 正确解析测试结果文件，提取所有失败用例
- [ ] 从用例标题中正确提取 TC 编号、需求 ID、飞书用例 ID
- [ ] 缺陷标题包含产品标签和用例编号
- [ ] 缺陷描述包含复现步骤、预期/实际结果、测试环境
- [ ] 报告人 user_key 通过 search_user_info 获取（非硬编码）
- [ ] 关联需求 ID 正确填写

## 参考资源

- [飞书缺陷字段参考](references/feishu-issue-fields.md)
- [测试用例字段参考](references/testcase-fields.md)
- [测试计划字段参考](references/testplan-fields.md)
