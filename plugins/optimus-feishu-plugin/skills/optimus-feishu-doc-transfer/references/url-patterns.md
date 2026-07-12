# 飞书 URL 解析规则

## URL 结构

```
https://[tenant].feishu.cn/<type>/<token>
```

## 类型对照表

| URL 特征 | 文档类型 | lark-cli 操作 |
|---|---|---|
| `feishu.cn/docx/<TOKEN>` | docx（新版文档） | `docs +fetch` |
| `feishu.cn/doc/<TOKEN>` | doc（旧版文档） | `docs +fetch` |
| `feishu.cn/wiki/<TOKEN>` | wiki（知识库） | `docs +fetch` |
| `feishu.cn/sheets/<TOKEN>` | sheet（表格） | `sheets +read` |
| `feishu.cn/file/<TOKEN>` | file（普通文件） | `drive +export` |

## Token 提取规则

从 URL 中提取 token：取 `/` 后最后一段路径，忽略查询参数。

示例：
```
https://example.feishu.cn/docx/AbCdEfGhIjKlMnOp?from=search
                                 ↑ token = AbCdEfGhIjKlMnOp
```

## 特殊情况

- wiki URL 有时包含子页面路径：`/wiki/<space_token>/<page_token>`，取最后一段作为 token
- 飞书国内版域名：`feishu.cn`
- 飞书海外版域名：`larksuite.com`（处理方式相同）
- URL 含 `?tab=` 参数时忽略，不影响 token 提取
