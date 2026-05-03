# 常见错误及解决方案

## 认证类错误

| 错误信息 | 原因 | 解决方案 |
|---|---|---|
| `401 Unauthorized` | token 未配置或已过期 | 运行 `npx @larksuite/cli login` 重新认证 |
| `doctor: not authenticated` | 未登录 | 运行 `npx @larksuite/cli login` |
| `invalid app credentials` | App ID/Secret 错误 | 检查 `.env` 配置 |

## 权限类错误

| 错误信息 | 原因 | 解决方案 |
|---|---|---|
| `403 Forbidden` | 无文档访问权限 | 在飞书中将文档设为"组织内可见"或手动添加权限 |
| `permission denied on folder` | 无目标文件夹写入权限 | 联系文件夹所有者添加编辑权限 |

## 文档类错误

| 错误信息 | 原因 | 解决方案 |
|---|---|---|
| `document not found` | token 错误或文档已删除 | 确认 URL 有效，重新从飞书复制链接 |
| `unsupported document type` | 文档类型不支持 | 参考 `url-patterns.md` 确认支持的类型 |

## 安装类错误

| 错误信息 | 原因 | 解决方案 |
|---|---|---|
| `npx: command not found` | Node.js 未安装 | 安装 Node.js >= 16 |
| `@larksuite/cli: not found` | lark-cli 未安装 | 运行 `npm install -g @larksuite/cli` |

## 网络类错误

| 错误信息 | 原因 | 解决方案 |
|---|---|---|
| `ECONNREFUSED` / `timeout` | 网络不通或需代理 | 检查网络连接，或配置代理 |
| `rate limit exceeded` | 请求过于频繁 | 等待 60 秒后重试 |

## 表格类错误

| 错误信息 | 原因 | 解决方案 |
|---|---|---|
| `invalid range format` | range 格式错误 | 格式应为 `sheetId!A1:Z100` |
| `sheet not found` | sheetId 不存在 | 先获取表格元信息确认 sheetId |
