# 飞书项目测试计划字段参考

## 工作项类型信息

> 以 jsgx2023 空间为例，更新日期：2026-03-30

| 项目 | 值 |
|------|-----|
| 工作项类型名称 | 测试计划 |
| 工作项类型 key | `63fc6b3a842ed46a33c769cf` |
| 默认模板 ID | `410685` |
| 默认模板名称 | 默认测试计划类型 |

> ⚠️ 工作项类型 key 和模板 ID 因空间配置不同可能不一致，首次使用时需通过以下方式确认：
> 1. `list_workitem_types` 获取类型 key
> 2. MQL 查询已有测试计划获取模板 ID

## 字段说明

### 创建时必需字段

| 字段 | field_key | 类型 | 说明 |
|------|-----------|------|------|
| 模板 | `template` | select | 模板 ID |
| 名称 | `name` | text | 测试计划标题 |

### 更新时可写字段

| 字段 | field_key | 类型 | 说明 |
|------|-----------|------|------|
| 描述 | `description` | multi_text | Markdown 格式，测试计划详细内容 |

### 无法通过 MCP 写入的字段

| 字段 | 原因 | 替代方式 |
|------|------|---------|
| 负责人 | 角色字段需 `role_operate` | 手动指派 |
| 关联需求 | `relation_*` 静默失败 | 手动关联 |
| 关联测试用例 | `relation_*` 静默失败 | 手动关联 |
| 状态 | `work_item_status` 无法修改 | 手动流转 |

## 创建+更新示例

### Step 1：创建工作项

```
工具：create_workitem
参数：
  project_key: 64891f1f69fcc11f9dee3551
  work_item_type: 63fc6b3a842ed46a33c769cf
  fields:
    - field_key: template
      field_value: "410685"
    - field_key: name
      field_value: "【招采】智能评标系统测试计划"
```

返回：`{ work_item_id: 6930854546, url: "https://..." }`

### Step 2：写入描述

```
工具：update_field
参数：
  project_key: 64891f1f69fcc11f9dee3551
  work_item_id: 6930854546
  fields:
    - field_key: description
      field_value: "## 1. 项目概述\n\n### 1.1 项目背景\n..."
```

## 名称前缀约定

| 产品线 | 前缀 | 示例 |
|--------|------|------|
| 招采 | `【招采】` | 【招采】智能评标系统测试计划 |
| AI智课 | `【AI智课】` | 【AI智课】数字人智课平台测试计划 |
| AIGC | `【AIGC】` | 【AIGC】智能撰写优化测试计划 |
