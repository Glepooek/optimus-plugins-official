# 飞书项目测试用例字段参考

## 工作项类型信息

> 以 jsgx2023 空间为例，更新日期：2026-03-30

| 项目 | 值 |
|------|-----|
| 工作项类型名称 | 测试用例 |
| 工作项类型 key | `63fc6356a3568b3fd3800e88` |

> ⚠️ 工作项类型 key 因空间不同可能不一致，首次使用时通过 `list_workitem_types` 确认。

## 创建时字段

| 字段 | field_key | 类型 | 必填 | 说明 |
|------|-----------|------|------|------|
| 模板 | `template` | select | 是 | 通过 MQL 查询已有用例获取 |
| 用例名称 | `name` | text | 是 | `[项目名][模块名]用例标题` |
| 前置条件 | `field_f717b4` | multi-pure-text | 否 | 模块路径 + 需求 ID |
| 优先级 | `priority` | select | 否 | 见下方枚举 |
| 用例分级 | `field_ad0ad4` | select | 否 | 见下方枚举 |
| 用例类型 | `field_e42a97` | multi-select | 否 | 见下方枚举 |

## 枚举值映射

### 优先级 (priority)

| P 级 | option_id |
|------|-----------|
| P0 | `option_1` |
| P1 | `option_2` |
| P2 | `option_3` |

### 用例分级 (field_ad0ad4)

| P 级 | option_id |
|------|-----------|
| P0 | `wx10xqwo8` |
| P1 | `c0z9ko2mk` |
| P2 | `ck4xd409s` |

### 用例类型 (field_e42a97)

| 类型 | 值（multi-select 格式） |
|------|------------------------|
| 功能用例 | `[{"option_id":"testcase_function"}]` |

> ⚠️ 枚举值的 option_id 因空间配置不同可能不一致。首次导入时建议先通过 MQL 查询已有用例的字段值来确认：
> ```
> SELECT `name`, `priority`, `field_ad0ad4`, `field_e42a97` FROM `{空间}`.`测试用例` LIMIT 1
> ```

## 无法通过 MCP 写入的字段

| 字段 | 原因 | 替代方式 |
|------|------|---------|
| 测试步骤 | 内置复合字段 | 通过 XMind 导入或手动编辑 |
| 预期结果 | 内置复合字段 | 通过 XMind 导入或手动编辑 |
| 关联需求 | `relation_*` 静默失败 | 手动关联 |
| 关联测试计划 | `relation_*` 静默失败 | 手动关联 |
| 状态 | `work_item_status` 无法修改 | 手动流转 |

## 创建示例

```
工具：create_workitem
参数：
  project_key: 64891f1f69fcc11f9dee3551
  work_item_type: 63fc6356a3568b3fd3800e88
  fields:
    - field_key: template
      field_value: "{模板ID}"
    - field_key: name
      field_value: "[AI智课][数字人形象与配音设置]形象类型切换"
    - field_key: field_f717b4
      field_value: "数字人形象与配音设置 > 数字人形象选择 > 形象类型切换 [需求ID: FR-001]"
    - field_key: priority
      field_value: "option_1"
    - field_key: field_ad0ad4
      field_value: "wx10xqwo8"
    - field_key: field_e42a97
      field_value: '[{"option_id":"testcase_function"}]'
```
