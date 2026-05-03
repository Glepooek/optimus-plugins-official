# 接口数据类型约束规范

本规范定义 API 请求参数与响应数据的 TypeScript 类型编写约束，确保前后端数据契约清晰、类型安全。

---

## 一、响应数据类型

### 1.1 统一响应包装

所有 API 响应必须通过 `ApiResponse<T>` 包装，禁止直接使用裸类型：

```tsx
// types/common.ts
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}
```

### 1.2 列表接口响应

列表接口必须使用 `PageResult<T>` 泛型，禁止在各业务类型中重复定义分页字段：

```tsx
// ✅ 正确
export const getUsers = (params: UserQueryParams) =>
  request.get<PageResult<UserItem>>('/users', { params })

// ❌ 错误：每个接口自定义分页结构
interface UserListResponse {
  users: UserItem[]      // 字段名不统一
  totalCount: number     // 命名不统一
}
```

### 1.3 详情接口响应

详情接口直接返回实体类型，不需要额外包装：

```tsx
export const getUser = (id: number) =>
  request.get<UserDetail>(`/users/${id}`)
```

### 1.4 写操作响应

| 操作 | 返回类型 | 说明 |
|------|---------|------|
| 新增 | `T`（创建后的完整实体） | 用于前端免刷新追加到列表 |
| 更新 | `T`（更新后的完整实体） | 用于前端免刷新更新列表项 |
| 删除 | `void` | 无返回数据 |
| 批量操作 | `{ successCount: number; failedIds?: number[] }` | 需要反馈操作结果 |

```tsx
export const createUser = (data: UserFormData) =>
  request.post<UserItem>('/users', data)

export const deleteUser = (id: number) =>
  request.delete<void>(`/users/${id}`)

export const batchDeleteUsers = (ids: number[]) =>
  request.post<{ successCount: number; failedIds?: number[] }>('/users/batch-delete', { ids })
```

---

## 二、请求参数类型

### 2.1 查询参数（GET）

查询参数必须继承 `PageParams`（分页接口），筛选字段全部可选：

```tsx
// ✅ 正确
export interface UserQueryParams extends PageParams {
  name?: string
  status?: UserStatus
  dateRange?: [string, string]
}

// ❌ 错误：筛选字段设为必填
export interface UserQueryParams extends PageParams {
  name: string    // 不应该必填，用户可能不筛选
}
```

### 2.2 创建/编辑参数（POST/PUT）

创建和编辑共用同一 `FormData` 类型，编辑时使用 `Partial` 包装：

```tsx
// 新增 — 全量必填
export const createUser = (data: UserFormData) =>
  request.post<UserItem>('/users', data)

// 编辑 — 部分更新
export const updateUser = (id: number, data: Partial<UserFormData>) =>
  request.put<UserItem>(`/users/${id}`, data)
```

**禁止**为创建和编辑分别定义两个几乎相同的类型：

```tsx
// ❌ 错误：重复定义
interface CreateUserData { name: string; email: string; phone: string }
interface UpdateUserData { name?: string; email?: string; phone?: string }
```

### 2.3 路径参数

路径参数通过函数参数传入，不定义独立类型（除非需要品牌类型约束）：

```tsx
// ✅ 简单场景 — 直接用参数
export const getUser = (id: number) =>
  request.get<UserDetail>(`/users/${id}`)

// ✅ 品牌类型场景 — 使用品牌 ID
export const getUser = (id: UserId) =>
  request.get<UserDetail>(`/users/${id}`)

// ❌ 错误：过度封装
interface GetUserParams { id: number }
export const getUser = (params: GetUserParams) =>
  request.get<UserDetail>(`/users/${params.id}`)
```

---

## 三、类型分层原则

### 3.1 请求类型与实体类型分离

接口请求参数类型和实体数据类型必须分离定义，禁止混用：

```tsx
// types/user.ts

// --- 实体类型（后端返回的数据结构） ---
export interface UserItem {
  id: number
  name: string
  email: string
  status: UserStatus
  createdAt: string
  updatedAt: string
}

// --- 请求类型（前端发送的参数结构） ---
export interface UserFormData {
  name: string
  email: string
  status: UserStatus
}

export interface UserQueryParams extends PageParams {
  name?: string
  status?: UserStatus
}
```

**规则：**
- 实体类型包含 `id`、`createdAt`、`updatedAt` 等服务端生成字段
- 表单类型 **不包含** 服务端生成字段
- 表单类型从实体类型派生时使用 `Omit`：`type UserFormData = Omit<UserItem, 'id' | 'createdAt' | 'updatedAt'>`

### 3.2 类型派生优先

从已有类型派生新类型，禁止重复定义同一字段：

```tsx
// ✅ 正确：派生
export type UserFormData = Omit<UserItem, 'id' | 'createdAt' | 'updatedAt'>
export type UserBrief = Pick<UserItem, 'id' | 'name' | 'avatar'>
export type UserDetail = UserItem & { roles: string[]; department: string }

// ❌ 错误：手动重写所有字段
export interface UserFormData {
  name: string      // 与 UserItem.name 重复
  email: string     // 与 UserItem.email 重复
  status: UserStatus // 与 UserItem.status 重复
}
```

### 3.3 嵌套数据类型

后端返回的嵌套结构，每层必须独立定义类型：

```tsx
// ✅ 正确：嵌套层级独立定义
export interface OrderItem {
  id: number
  orderNo: string
  status: OrderStatus
  items: OrderProductItem[]    // 独立类型
  address: OrderAddress        // 独立类型
  payment: OrderPayment        // 独立类型
}

export interface OrderProductItem {
  productId: number
  name: string
  quantity: number
  price: number
}

export interface OrderAddress {
  province: string
  city: string
  district: string
  detail: string
}

// ❌ 错误：内联匿名类型
export interface OrderItem {
  id: number
  items: { productId: number; name: string; quantity: number; price: number }[]
  address: { province: string; city: string; detail: string }
}
```

**规则：** 嵌套对象超过 2 个字段时必须抽取为独立 `interface`。

---

## 四、字段类型映射

### 4.1 后端字段 → 前端类型映射表

| 后端类型 | 前端 TypeScript 类型 | 说明 |
|---------|---------------------|------|
| `int` / `long` | `number` | 整数 |
| `float` / `double` / `decimal` | `number` | 浮点数（金额用分，避免精度问题） |
| `string` / `varchar` / `text` | `string` | 字符串 |
| `boolean` / `tinyint(1)` | `boolean` | 布尔值，禁止用 `0 \| 1` |
| `datetime` / `timestamp` | `string` | ISO 8601 格式字符串 |
| `date` | `string` | `"YYYY-MM-DD"` 格式 |
| `json` / `jsonb` | 具体类型 `T` | 必须定义具体结构，禁止 `any` |
| `enum` | 数值枚举或字面量联合 | 见枚举约束规范 |
| `null` / 可空字段 | `T \| null` | 禁止用 `undefined` 表示空值 |
| `array` | `T[]` | 必须声明元素类型 |
| `bigint` / 超大 ID | `string` | JS Number 精度不够时用 string |

### 4.2 金额字段

金额必须以 **分（整数）** 为单位传输和存储，展示时转换为元：

```tsx
export interface OrderItem {
  totalAmount: number    // 单位：分（如 9900 = 99.00 元）
  discountAmount: number // 单位：分
}

// 展示时使用工具函数
import { formatMoney } from '@/utils/format'
<span>{formatMoney(order.totalAmount)}</span>  // "99.00"
```

**禁止**在类型中用浮点数表示金额（`price: 99.99`），精度丢失会导致计算错误。

### 4.3 文件/图片字段

文件相关字段统一为 URL 字符串或文件对象类型：

```tsx
export interface FileInfo {
  url: string         // 文件访问地址（完整 URL）
  name: string        // 原始文件名
  size: number        // 文件大小（字节）
  mimeType: string    // MIME 类型
}

export interface UserItem {
  avatar: string | null    // 头像 URL，未上传为 null
  attachments: FileInfo[]  // 附件列表
}
```

---

## 五、接口版本与兼容

### 5.1 字段废弃

后端废弃字段时，前端类型使用 `@deprecated` 标记，不立即删除：

```tsx
export interface UserItem {
  id: number
  name: string
  /** @deprecated 使用 avatarUrl 替代，将在 v3.0 移除 */
  avatar?: string
  avatarUrl: string | null
}
```

### 5.2 新增可选字段

后端新增字段时，前端类型必须标记为可选（`?`），直到确认所有环境已部署：

```tsx
export interface UserItem {
  id: number
  name: string
  // v2.1 新增，过渡期标记可选
  department?: string
}
```

---

## 六、速查表

### 命名规范

| 类型用途 | 命名模式 | 示例 |
|---------|---------|------|
| 列表项 | `XxxItem` | `UserItem`、`OrderItem` |
| 详情 | `XxxDetail` | `UserDetail`、`CourseDetail` |
| 表单数据 | `XxxFormData` | `UserFormData`、`OrderFormData` |
| 查询参数 | `XxxQueryParams` | `UserQueryParams`、`OrderQueryParams` |
| 简要信息 | `XxxBrief` | `UserBrief`、`CourseBrief` |
| 嵌套子项 | `XxxYyyItem` | `OrderProductItem`、`CourseChapterItem` |
| 状态枚举 | `XxxStatus` | `UserStatus`、`OrderStatus` |

### 禁止清单

| 禁止 | 替代方案 |
|------|---------|
| 列表接口自定义分页结构 | 统一使用 `PageResult<T>` |
| 创建/编辑定义两个独立类型 | 共用 `FormData` + `Partial` |
| 嵌套对象用内联匿名类型 | 超过 2 个字段时抽取为独立 `interface` |
| 金额用浮点数（`99.99`） | 统一用整数分（`9900`） |
| API 可空字段用 `undefined` | 统一用 `T \| null` |
| `json` 字段类型写 `any` | 定义具体结构类型 |
| 超大 ID 用 `number` | JS 精度不够时用 `string` |
| `boolean` 字段用 `0 \| 1` | 统一用 `boolean` |
| 为路径参数定义独立 interface | 直接用函数参数 |
| 不同模块重复定义相同字段 | 从基础类型派生（`Pick`、`Omit`、`extends`） |
