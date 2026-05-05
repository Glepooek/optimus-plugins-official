# 命名规则

## 1. 服务名称（name）

**规则**：小写字母 + 数字 + 连字符，与 Git 仓库名保持一致。

- 合法：`user-service`、`api-gateway`、`auth-v2`
- 非法：`UserService`（大写）、`user_service`（下划线）、`user service`（空格）

**约束**：
- 最小长度：3 个字符
- 最大长度：63 个字符
- 不得以 `-` 开头或结尾
- 平台内唯一，注册后不可更改

---

## 2. 展示名称（displayName）

**规则**：人类可读的中文或英文名称，用于平台 UI 展示。

- 合法：`用户认证服务`、`API 网关`、`Content Management`
- 建议：中文服务用中文展示名，便于团队识别
- 最大长度：64 个字符

**推断逻辑**（仅供参考，需用户确认）：
| 服务名 | 推断展示名 |
|--------|-----------|
| user-service | 用户服务 |
| api-gateway | API 网关 |
| auth-service | 认证服务 |
| order-service | 订单服务 |
| payment-service | 支付服务 |
| notification-service | 通知服务 |

---

## 3. 域名子域名前缀（subdomain）

**规则**：小写字母 + 连字符，完整域名 = `{subdomain}.unipus.cn`。

- 合法：`user`、`user-api`、`content-v2`
- 非法：`user_api`（下划线）、`User`（大写）

**环境惯例**：
- dev 环境：`{subdomain}-dev.unipus.cn`
- test 环境：`{subdomain}-test.unipus.cn`
- prod 环境：`{subdomain}.unipus.cn`

**推断逻辑**：从服务名去掉 `-service` 后缀。
例：`user-service` → 子域名前缀：`user`

---

## 4. 团队名称（team）

**规则**：与 Git 仓库所属 Group 名称一致（小写字母 + 连字符）。

常见团队名：`backend`、`frontend`、`platform`、`data`、`mobile`

---

## 5. 数据库/Redis 标识（dependencies.db.name / dependencies.redis.name）

**规则**：`{团队}-{业务}` 格式，小写字母 + 连字符。

- 合法：`backend-user`、`backend-order`
- 命名需要向基础设施团队申请，平台会校验合法性
