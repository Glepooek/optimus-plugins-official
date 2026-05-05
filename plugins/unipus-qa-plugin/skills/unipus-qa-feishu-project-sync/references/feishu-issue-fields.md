# 飞书项目缺陷字段参考

## jsgx2023 空间字段配置

> 通过 `get_workitem_field_meta` 和 MQL 查询获取，更新日期：2026-03-30

### 必填字段

| 字段名 | field_key | 类型 | 说明 |
|--------|-----------|------|------|
| 缺陷名称 | `name` | text | 缺陷标题 |
| 缺陷描述 | `description` | multi_text | Markdown 格式 |
| 优先级 | `priority` | select | 见下方枚举 |
| 严重程度 | `severity` | select | 见下方枚举 |
| 发现阶段 | `issue_stage` | select | 见下方枚举 |
| Bug端分类 | `bug_classification` | select | 见下方枚举 |
| 报告人 | `issue_reporter` | multi-user | user_key 数组 |
| 关联需求 | `_field_linked_story` | workitem_related_select | 需求工作项 ID |
| 缺陷类型 | `template` | select | 模板 ID |

### 枚举值映射

#### 优先级 (priority)

| key | label |
|-----|-------|
| `1` | 核心 |
| `2` | 高 |
| `3` | 中 |
| `4` | 低 |

#### 严重程度 (severity)

| key | label |
|-----|-------|
| `1` | 严重 |
| `2` | 重要 |
| `3` | 一般 |
| `4` | 次要 |
| `5` | 微小 |

#### 发现阶段 (issue_stage)

| key | label |
|-----|-------|
| `stage_test` | 测试阶段 |

#### Bug端分类 (bug_classification)

| key | label |
|-----|-------|
| `fe` | 前端 (Web) |
| `server` | 后端 (Server) |
| `ios` | iOS |
| `android` | Android |
| `sczwh16sz` | 其他（自定义） |

#### 缺陷类型模板 (template)

| key | label |
|-----|-------|
| `305027` | 普通缺陷 |

### 缺陷描述模板

```markdown
## 缺陷描述

{一句话描述缺陷现象}

## 复现步骤

1. {步骤1}
2. {步骤2}
3. ...

## 预期结果

{期望的正确行为}

## 实际结果

{实际观察到的错误行为}
{错误信息/截图}

## 测试环境

- 浏览器：Chrome (Desktop)
- 分辨率：1536x864
- 测试框架：Playwright + Midscene
- 关联用例：{TC编号} @{需求ID}
- 自动化报告：{报告文件路径}
```

### create_workitem 调用示例

```
工具：create_workitem
参数：
  project_key: 64891f1f69fcc11f9dee3551
  work_item_type: issue
  fields:
    - field_key: template
      field_value: "305027"
    - field_key: name
      field_value: "【AIGC】【AI智课】上传MP4视频时页面崩溃（TC-DH-004）"
    - field_key: description
      field_value: "{Markdown 格式缺陷描述}"
    - field_key: priority
      field_value: "1"
    - field_key: severity
      field_value: "2"
    - field_key: issue_stage
      field_value: "stage_test"
    - field_key: bug_classification
      field_value: "fe"
    - field_key: issue_reporter
      field_value: '["7202805825444921372"]'
    - field_key: _field_linked_story
      field_value: "6631243219"
```
