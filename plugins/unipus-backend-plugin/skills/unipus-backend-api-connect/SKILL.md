---
name: unipus-backend-api-connect
description: 根据服务注册表自动对接后端 API，生成对接代码
globs:
  - "**/*"
alwaysApply: false
---

你正在帮助开发者对接后端 API。根据 `$ARGUMENTS` 的值，按以下阶段执行。

---

## 阶段一：读取配置

从远程地址拉取服务注册表配置：

```bash
curl -s -f https://api-doc-test.unipus.cn/api/file/api-services.yml -o .claude/skills/unipus-backend-api-connect/cache/api-services.yml
```

拉取成功后，读取 `.claude/skills/unipus-backend-api-connect/cache/api-services.yml`。

**处理以下情况：**

**情况 A — 远程拉取失败（网络错误或 HTTP 非 200）：**
- 若本地缓存 `.claude/skills/unipus-backend-api-connect/cache/api-services.yml` 已存在，使用缓存并提示用户：
  > "远程配置拉取失败，已使用本地缓存版本。"
- 若本地缓存也不存在，提示用户：
  > "无法获取服务注册表：远程地址 `https://api-doc-test.unipus.cn/api/file/api-services.yml` 不可达，且无本地缓存。请检查网络连接。"

到此结束。

**情况 B — `$ARGUMENTS` 是一个 URL（以 `http://` 或 `https://` 开头）：**
用户直接提供了文档链接。记录该 URL，跳至阶段三（作为临时单服务处理，类型未知，使用通用兜底策略）。

**情况 C — 正常使用：** 配置文件存在，`$ARGUMENTS` 是服务名或自然语言描述，继续执行阶段二。

---

## 阶段二：理解需求 & 匹配服务

将 `$ARGUMENTS` 解析为服务名或自然语言功能描述。

1. 读取 `.claude/skills/unipus-backend-api-connect/cache/api-services.yml` 中的所有服务
2. 将 `$ARGUMENTS` 与每个服务的 `name` 和 `description` 进行语义匹配，排序后取最相关结果
3. 根据匹配情况决定是否需要用户确认：
   - **唯一高度匹配**（仅一个结果且语义明确对应）→ 直接选中，告知用户并继续，无需等待确认
   - **多个候选结果** → 展示列表，等待用户选择：
     ```
     匹配到以下服务：
     1. user-service — 用户服务，负责注册、登录、鉴权  [需认证 · Bearer]
     2. order-service — 订单服务，订单创建和查询       [无需认证]

     请选择要对接的服务（输入序号或 'all'）：
     ```
   - **无匹配结果** → 列出全部可用服务，请用户手动选择

---

## 阶段三：拉取 & 解析 API 文档

针对每个选中的服务，根据 `docs[].type` 选择对应策略拉取并解析文档：

**`swagger` / `openapi`：**
优先使用项目内置脚本 `.claude/skills/unipus-backend-api-connect/fetch_swagger.py` 拉取 spec（支持自动探测底层 spec 地址）：

```bash
python .claude/skills/unipus-backend-api-connect/fetch_swagger.py <docs[].url> --output .claude/skills/unipus-backend-api-connect/cache/<服务名>.json
```

- 脚本支持以下文档类型：
  - ✅ **Swagger Bootstrap UI**（如 `/api/doc.html`）— 自动访问 `/swagger-resources` 获取分组列表
  - ✅ **标准 Swagger UI**（如 `/swagger-ui/index.html`）— 从 HTML 中提取 spec URL
  - ✅ **直接 spec 链接**（如 `/v2/api-docs`、`/swagger.json`）
  - ✅ **自动处理中文参数编码**（如 `?group=SOE融合语音引擎服务`）
- 成功后读取生成的本地 JSON 文件，解析 `paths` 对象提取接口信息
- 若脚本不存在或执行失败，回退为使用 WebFetch 直接请求 URL，按 OpenAPI `paths` 结构解析

**`markdown`：**
文档为 Markdown 文件（`.md` / `.markdown` 直链，如托管在 OSS/CDN 上的 API-Documentation.md）。
使用项目内置脚本 `.claude/skills/unipus-backend-api-connect/fetch_webpage_api.py` 获取并解析：

```bash
python .claude/skills/unipus-backend-api-connect/fetch_webpage_api.py <docs[].url> \
  --output .claude/skills/unipus-backend-api-connect/cache/<服务名>.md
```

- 脚本自动识别 Markdown 内容（通过 URL 后缀或内容特征），提取接口路径、HTTP 方法和描述
- 成功后读取生成的本地 `.md` 文件，从中提取接口信息
- 若 URL 无法访问（内网/权限限制），提示用户手动下载文档后传入本地路径：
  ```bash
  python .claude/skills/unipus-backend-api-connect/fetch_webpage_api.py <本地文件路径或 file:// URL> \
    --output .claude/skills/unipus-backend-api-connect/cache/<服务名>.md
  ```

**`feishu`：**
文档托管在飞书云文档（新版文档，URL 格式为 `https://xxx.feishu.cn/docx/<doc_token>`）。
使用项目内置脚本 `.claude/skills/unipus-backend-api-connect/fetch_feishu_doc.py` 调用飞书 API 获取：

**凭证来源（按优先级依次尝试）：**
1. `docs[].auth.app_id` + `docs[].auth.app_secret`（在服务注册表中配置，**推荐**）
2. 环境变量 `FEISHU_APP_ID` + `FEISHU_APP_SECRET`
3. `docs[].auth.token`（直接配置 access_token）
4. 环境变量 `FEISHU_ACCESS_TOKEN`

若使用 app 凭证（方式 1 或 2），脚本会自动调用飞书接口获取 `tenant_access_token`，并缓存到 `.claude/skills/unipus-backend-api-connect/cache/.feishu_token_cache.json`（缓存有效期内复用，避免重复请求）。

若均未配置，提示用户：
```
未提供飞书认证凭证。请通过以下任意方式提供：
  1. 在服务注册表的 docs[].auth 中配置 app_id + app_secret（推荐）
  2. 环境变量：export FEISHU_APP_ID=<id> && export FEISHU_APP_SECRET=<secret>
  3. 直接传 token：在 docs[].auth.token 中填写 tenant_access_token

如何获取 app_id / app_secret：
  飞书开放平台控制台 → 选择应用 → 凭证与基础信息
```

**执行命令：**
```bash
# 使用 app 凭证（自动获取 token）
python .claude/skills/unipus-backend-api-connect/fetch_feishu_doc.py <doc_token> \
  --app-id <app_id> --app-secret <app_secret> \
  --output .claude/skills/unipus-backend-api-connect/cache/<服务名>.md

# 或使用已有 token
python .claude/skills/unipus-backend-api-connect/fetch_feishu_doc.py <doc_token> \
  --token <access_token> \
  --output .claude/skills/unipus-backend-api-connect/cache/<服务名>.md
```

- `doc_token` 从 `docs[].url` 中提取：URL 中 `/docx/` 后面的部分即为 `doc_token`
  - 例如 `https://example.feishu.cn/docx/B4EPdAYx8oi8HRxgPQQbM15UcBf` → `doc_token = B4EPdAYx8oi8HRxgPQQbM15UcBf`
- 成功后读取生成的本地 `.md` 文件，从中提取接口信息（与 `markdown` 类型后续处理相同）
- 若遇到 403 权限错误，向用户展示对应提示：
  - 使用 `tenant_access_token`：需在文档页面右上角「...」→「添加文档应用」为应用授权
  - 使用 `user_access_token`：需通过「分享」为该用户添加阅读权限

**通用兜底（类型未知或直接 URL）：**
使用 WebFetch 加载页面，通过 AI 理解从内容中提取以下信息：
- 接口路径和 HTTP 方法
- 请求参数（query、body、header、path 参数）
- 响应数据结构
- 接口描述和业务说明

**解析完成后**，向用户展示接口摘要：
```
在 user-service 中发现 12 个接口：

  POST /auth/login          — 用户登录，返回 JWT Token
  POST /auth/register       — 注册新账号
  GET  /users/me            — 获取当前用户信息
  PUT  /users/me            — 更新个人信息
  POST /users/avatar        — 上传头像
  ...

请选择要对接的接口（输入序号、范围如 1-3，或 'all'）：
```

等待用户选择具体接口后再继续。

---

## 阶段四：扫描项目已有能力

使用 Glob 和 Grep 扫描当前项目，发现已有的 HTTP 基础设施和代码规范。

**扫描 HTTP 客户端封装：**
- Glob：`**/services/**`、`**/api/**`、`**/request/**`、`**/utils/http*`、`**/utils/request*`、`**/lib/http*`
- Grep 查找 axios、fetch、ky、got、superagent 等库的 import/require

**扫描已有接口调用规范：**
读取一个典型的已有接口文件，理解：
- 函数命名风格（如 `getUserInfo`、`get_user_info`、`fetchUser`）
- 函数签名（参数、返回类型、async/await）
- 错误处理方式（try/catch、.catch()、结果元组等）
- baseUrl 和认证 Header 的挂载方式

**扫描 TypeScript 类型定义：**
- Glob：`**/types/**`、`**/interfaces/**`、`**/*.d.ts`
- 记录已有的共享类型，避免重复创建

**扫描认证方式：**
- Grep 在请求拦截器或封装中查找 `Authorization`、`Bearer`、`token`、`Cookie`
- 同时读取选中服务的 `auth` 配置，若 `auth.required` 为 `true`，则在生成代码中包含认证 Header

**展示"已有能力摘要"：**
```
项目扫描结果：
- HTTP 客户端：axios（封装于 services/request.ts）
- 认证方式：Bearer Token，通过请求拦截器注入
- 已有接口文件：services/user.ts、services/order.ts
- 代码风格：TypeScript，具名导出，async/await，camelCase 命名
- 已有类型：src/types/user.ts（UserInfo、LoginParams）

目标服务认证要求：
- asr-api：需要 Bearer Token（Header: Authorization）
  申请方式：飞书联系维护人张琪玉，说明使用场景和所在项目。
```

---

## 阶段五：差距分析

将选中的目标接口与项目中已有的代码进行对比。

1. 在已有接口文件中 Grep 每个目标接口路径
2. 对每个接口进行分类：
   - **已覆盖** — 在已有代码中找到该路径 → 标记 `✓`
   - **需更新** — 找到路径但签名可能已过时 → 标记 `~`
   - **待新建** — 任何地方都未找到 → 标记 `+`

展示分析结果：
```
差距分析：

  ✓ POST /auth/login       — 已在 services/auth.ts 中（跳过）
  + POST /auth/register    — 待新建
  ~ GET  /users/me         — 已在 services/user.ts 中，可能需更新类型
  + PUT  /users/me         — 待新建
  + POST /users/avatar     — 待新建

是否继续对接：3 个新接口 + 1 个更新？（yes / 调整）
```

等待用户确认。允许用户输入调整意见（例如"跳过头像那个"）。

---

## 阶段六：生成代码

严格遵循阶段四中识别到的项目已有风格生成代码。

对每个确认的接口，生成以下内容：

**1. TypeScript interface**（请求参数 + 响应数据）：
```typescript
// 仅创建项目中尚不存在的类型
export interface RegisterParams {
  username: string
  password: string
  email: string
}

export interface RegisterResult {
  userId: string
  token: string
}
```

**2. API 函数**（复用项目已有 HTTP 客户端，若服务 `auth.required` 为 `true` 则注入认证 Header）：
```typescript
// 与 services/request.ts 的已有风格保持一致
// 若项目已有全局认证拦截器，则无需手动注入 Header
export async function register(params: RegisterParams): Promise<RegisterResult> {
  return request.post('/auth/register', params)
}

// 若服务需要独立的认证（与项目默认认证不同），则在函数内显式传入：
export async function asrTranscribe(params: AsrParams): Promise<AsrResult> {
  return request.post('/asr/transcribe', params, {
    headers: { Authorization: `Bearer ${getAsrToken()}` }
  })
}
```

**3. 推荐文件位置**（根据项目结构）：
```
新代码将写入：
  services/auth.ts        — register()、（updateProfile 合并到此）
  services/user.ts        — updateProfile()、uploadAvatar()
  types/auth.ts           — RegisterParams、RegisterResult（新文件）
```

**4. 使用示例：**
```typescript
// 在业务组件或页面中的调用示例
import { register } from '@/services/auth'

const result = await register({ username: 'alice', password: '...', email: '...' })
console.log(result.token)
```

**先将所有生成内容展示给用户**，然后询问：
```
准备将以上代码写入：
  - services/auth.ts（追加 1 个函数）
  - services/user.ts（追加 2 个函数）
  - types/auth.ts（新文件）

确认写入？（yes / no / 先看 diff）
```

用户确认后写入文件。若选择"先看 diff"，以新旧对比的形式展示已有文件的变更内容。

写入完成后：
```
完成！已从 user-service 对接 3 个新接口。

后续建议：
- 对照实际 API 响应校验生成的类型定义
- 参考上方示例代码进行测试
- 如需申请认证 Token，请联系维护人或参考服务注册表中的 auth.apply 说明
```
