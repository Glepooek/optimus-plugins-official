---
name: unipus:ci:notify-api-change
description: 构建完成后，分析 git commit 记录判断是否涉及 API 接口变动，若有则读取 TEAM.md 解析飞书群组和前端/测试人员信息，通过 lark-cli 向项目群组发送通知并 @ 相关人员
---

# API 变动飞书通知

构建完成后，根据 jenkins-build 传入的 commit 记录判断是否涉及 API 接口变动，如有则自动通知前端和测试人员。

## 输入参数

由 jenkins-build 在调用时传入：
- `job_name`：job 名称
- `build_number`：构建号
- `build_result`：构建结果（SUCCESS / FAILURE 等）
- `build_url`：构建地址（`jenkins_url/job_path/build_number/`）
- `commits`：本次 changeSet 的 commit message 列表

## 执行步骤

### 第一步：判断是否涉及 API 接口变动

分析传入的 `commits`，如果包含以下任意关键词，则认为涉及 API 变动：

- `api`、`API`、`接口`、`endpoint`、`路由`、`route`
- `controller`、`handler`、`request`、`response`
- `swagger`、`openapi`、`rest`、`http`
- `新增接口`、`修改接口`、`删除接口`、`变更接口`
- `add api`、`update api`、`delete api`、`remove api`、`change api`

**如果不涉及 API 变动或者构建失败，直接结束，不发送通知。**

### 第二步：读取 TEAM.md

在项目根目录查找 `TEAM.md` 文件（向上逐级查找直到找到为止）。

从文件中提取：
1. **飞书群组名称**：`项目信息` 表格中`飞书群组`对应的值（取第一个）
2. **前端人员**：`### 前端` 章节表格中所有有效的姓名和 `open_id`（`ou_` 开头）
3. **测试人员**：`### 测试` 章节表格中所有有效的姓名和 `open_id`（`ou_` 开头）

如果 `TEAM.md` 不存在，或没有群组名称，则跳过通知并打印提示。

### 第三步：搜索飞书群组 chat_id

```bash
lark-cli im +chat-search --query "<群组名称>" --format json --as bot
```

从结果中取第一个匹配的 `chat_id`（`oc_xxx` 格式）。

### 第四步：发送飞书通知

构建消息文本，使用 `<at user_id="ou_xxx">姓名</at>` 格式 @ 所有前端和测试人员：

```bash
lark-cli im +messages-send --chat-id <chat_id> --text "<消息内容>" --as bot
```

**消息模板：**

```
⚠️ API 接口变动通知 — <job名称> #<构建号>

构建结果：<SUCCESS/FAILURE>
构建地址：<Jenkins URL>

本次提交涉及 API 接口变动，请前端和测试同学关注：
• <commit msg 1>
• <commit msg 2>
（最多展示 5 条）

<at user_id="ou_xxx">前端姓名</at> <at user_id="ou_xxx">测试姓名</at>
```

## 注意事项

- 仅在 commit message 命中 API 关键词时才发送通知，避免噪音
- `lark-cli` 需以 bot 身份发送（`--as bot`），bot 须已加入目标群组
- 若 `open_id` 字段为"未查到"等无效值，跳过该人员的 @ 但仍发消息
- 消息发送失败时打印错误信息但不影响构建的退出码
