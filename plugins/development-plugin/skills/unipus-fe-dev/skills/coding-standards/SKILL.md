---
name: coding-standards
version: 1.0.0
description: Use when generating any frontend code to enforce coding conventions across all layers (entry, styles, pages, components, API, state, types, utils). Tech stack React 18 + TypeScript + Tailwind CSS + Zustand + TanStack Query + Vite.
---

# 前端开发规范

所有代码生成必须遵循本规范。本规范定义了 8 个分层的编码约定，技术栈选用 AI 生成质量最高的组合。

## 推荐技术栈

> 详见 [`references/tech-stack.md`](./references/tech-stack.md)。如果项目已有技术栈，以项目实际为准。

---

## 目录结构

> 详见 [`references/directory-structure.md`](./references/directory-structure.md)。

---

## 一、主程序（`main.tsx` / `App.tsx`）

### 规范

```tsx
// main.tsx — 极简，只做挂载
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles/globals.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

```tsx
// App.tsx — Provider 洋葱 + 路由
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
```

### 规则

- `main.tsx` 只做 `createRoot` + `render`，不放业务逻辑
- `App.tsx` 只放 Provider 嵌套和路由挂载
- Provider 顺序：外层通用（QueryClient）→ 内层业务（Auth、Theme）
- 全局样式在 `main.tsx` 中导入

---

## 二、全局 CSS（`styles/globals.css`）

> CSS 变量和 Tailwind Token 配置详见 [`references/design-tokens.md`](./references/design-tokens.md)。

### 规则

- 只放 Tailwind 指令、CSS 变量、全局 reset
- **禁止**在此文件写具体组件样式
- 设计 Token 统一定义为 CSS 变量，供 Tailwind `theme.extend` 引用
- 颜色值来源于设计稿，不允许硬编码 hex

---

## 二·五、Tailwind 可维护性方案

Tailwind 的三大维护痛点：**长 class 难读**、**重复 class 到处复制**、**条件样式拼接混乱**。本节定义标准解法。

### 2.1 `cn()` 工具函数 — class 合并与条件拼接

```tsx
// lib/cn.ts — 项目必备，第一天就创建
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))
```

**使用场景：**

```tsx
// 条件样式
<div className={cn(
  'p-4 rounded-lg border',
  isActive && 'ring-2 ring-blue-500 border-blue-500',
  disabled && 'opacity-50 pointer-events-none',
)} />

// 组件接收外部 className 并安全合并
function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn('rounded-lg bg-white p-4 shadow', className)}>{children}</div>
}
```

**规则：**
- 禁止手动拼接 class 字符串（`` `${base} ${active ? 'ring-2' : ''}` ``），一律用 `cn()`
- `twMerge` 自动处理冲突（`cn('p-2', 'p-4')` → `'p-4'`），避免样式覆盖 bug

### 2.2 CVA（Class Variance Authority）— 组件变体管理

当组件有 2+ 变体维度时，必须使用 CVA 管理 class：

```tsx
// components/Button/variants.ts
import { cva, type VariantProps } from 'class-variance-authority'

export const buttonVariants = cva(
  // 基础样式（所有变体共享）
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary:   'bg-blue-600 text-white hover:bg-blue-700',
        secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
        danger:    'bg-red-600 text-white hover:bg-red-700',
        ghost:     'hover:bg-gray-100 text-gray-700',
        link:      'text-blue-600 underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
```

```tsx
// components/Button/index.tsx
import { cn } from '@/lib/cn'
import { buttonVariants, type ButtonVariants } from './variants'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, ButtonVariants {
  children: React.ReactNode
}

export default function Button({ variant, size, className, children, ...props }: ButtonProps) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} {...props}>
      {children}
    </button>
  )
}

// 使用
<Button variant="primary" size="lg">提交</Button>
<Button variant="ghost" className="ml-2">取消</Button>
```

**CVA 使用规则：**

| 场景 | 方案 |
|------|------|
| 无变体或仅 1 个布尔变体 | 直接 `cn()` 条件拼接 |
| 2+ 变体维度（variant × size 等） | 必须用 CVA |
| 变体定义 | 抽到独立文件 `variants.ts`，与组件分离 |
| 组件 Props 类型 | 继承 `VariantProps<typeof xxxVariants>` |

### 2.3 设计 Token 语义化 — `tailwind.config.ts`

> 具体 Token 配置详见 [`references/design-tokens.md`](./references/design-tokens.md)。

禁止在 class 中硬编码 hex 值或 magic number，全部收敛到 Tailwind config。

```tsx
// 差 — 硬编码
<div className="bg-[#1677ff] rounded-[8px] p-[24px] text-[20px]">

// 好 — 语义化 Token
<div className="bg-brand rounded-card p-page text-page-title">
```

**规则：**
- 设计稿中出现 3 次以上的值必须提取为 Token
- Token 命名用语义（`brand`、`page`），不用视觉描述（`blue-600`、`large`）
- 改 Token 值 → 全局生效，不用逐文件搜索替换

### 2.4 Prettier 自动排序

```bash
npm i -D prettier-plugin-tailwindcss
```

```json
// .prettierrc
{
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

自动按 Tailwind 官方推荐顺序排列 class，消除团队风格差异。

### Tailwind 维护速查

| 问题 | 解法 | 工具 |
|------|------|------|
| class 串太长 | 封成组件 | React 组件 |
| 多变体组合 | 声明式变体 | CVA |
| 条件/合并 class | 安全拼接 | `cn()` = clsx + twMerge |
| 硬编码颜色/间距 | Token 语义化 | `tailwind.config.ts` |
| class 顺序不一致 | 自动排序 | prettier-plugin-tailwindcss |
| 组件接收外部 className | twMerge 解决冲突 | `cn(baseClass, className)` |

---

## 三、页面及页面 CSS（`pages/`）

### 页面组件规范

```tsx
// pages/user/index.tsx
import { useState } from 'react'
import { Button, Table, Modal, message } from 'antd'
import { useUsers, useDeleteUser } from '@/hooks/useUser'
import type { UserQueryParams } from '@/types/user'
import UserTable from './components/UserTable'
import UserForm from './components/UserForm'

export default function UserPage() {
  // --- state ---
  const [params, setParams] = useState<UserQueryParams>({ page: 1, pageSize: 20 })
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  // --- data ---
  const { data, isLoading } = useUsers(params)
  const deleteMutation = useDeleteUser()

  // --- handlers ---
  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除？',
      onOk: () => deleteMutation.mutateAsync(id).then(() => message.success('删除成功')),
    })
  }

  // --- render ---
  return (
    <div className="p-6 space-y-4">
      {/* 搜索区 */}
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">用户管理</h1>
        <Button type="primary" onClick={() => { setEditingId(null); setFormOpen(true) }}>
          新增用户
        </Button>
      </div>

      {/* 列表区 */}
      <UserTable
        data={data?.list ?? []}
        loading={isLoading}
        pagination={{ current: params.page, pageSize: params.pageSize, total: data?.total ?? 0 }}
        onPageChange={(page, pageSize) => setParams(prev => ({ ...prev, page, pageSize }))}
        onEdit={(id) => { setEditingId(id); setFormOpen(true) }}
        onDelete={handleDelete}
      />

      {/* 弹窗表单 */}
      <UserForm
        open={formOpen}
        editingId={editingId}
        onClose={() => setFormOpen(false)}
      />
    </div>
  )
}
```

### 页面 CSS 规范

```css
/* pages/user/index.module.css — 仅当 Tailwind 无法表达时使用 */
.filterBar {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
```

### 规则

- **一个路由对应一个页面文件**，文件名 `index.tsx`
- 页面内部结构：`state → data → handlers → render`，四段式
- 页面私有子组件放在 `pages/xxx/components/` 下，不放 `components/`
- **优先 Tailwind class**，只有复杂布局（grid auto-fill 等）才用 CSS Module
- CSS Module 命名 `camelCase`，文件名 `index.module.css`
- 页面不直接调用 `axios`，通过 `hooks/` 或 `api/` 间接调用

---

## 四、组件及组件 CSS（`components/`）

### 组件规范

```tsx
// components/PageHeader/index.tsx
interface PageHeaderProps {
  title: string
  description?: string
  actions?: React.ReactNode
}

export default function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex justify-between items-start pb-4 border-b border-gray-200">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
        {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  )
}
```

### 规则

| 项 | 规则 |
|----|------|
| 目录 | 全局共享 → `components/XxxName/index.tsx`；页面私有 → `pages/xxx/components/` |
| Props | 必须定义 `interface XxxProps`，写在组件文件顶部 |
| 导出 | `export default function Xxx`，一个文件一个组件 |
| 样式 | Tailwind class 优先；复杂样式用同目录 `index.module.css` |
| 状态 | 组件只管 UI 状态（open/active），业务状态从 props 或 hooks 获取 |
| 事件 | 回调 props 命名 `onXxx`：`onClose`、`onSubmit`、`onChange` |
| children | 需要插槽时用 `children` 或具名 `React.ReactNode` props |

### 组件 CSS 规范

```css
/* components/PageHeader/index.module.css */
.wrapper {
  /* 只放 Tailwind 无法表达的样式 */
}
```

- **禁止**在组件 CSS 中覆盖 UI 库组件的内部类名
- 如需定制 UI 库样式，使用 UI 库提供的 API（`className`、`style`、`token`）

---

## 五、接口层（`api/`）

> axios 实例配置、API 函数模板、通用类型定义详见 [`references/api-request.md`](./references/api-request.md)。
>
> 接口请求参数与响应数据的类型编写约束详见 [`references/api-data-types.md`](./references/api-data-types.md)。

### 规则

- **一个业务模块一个文件**：`api/user.ts`、`api/order.ts`
- 函数命名：`get / create / update / delete` + 实体名
- 参数和返回值 **必须类型化**，引用 `types/` 下的类型
- `request.ts` 负责拦截器，API 函数文件 **不放拦截逻辑**
- 禁止在 API 文件中处理 UI 逻辑（toast、redirect）

---

## 六、数据层（`stores/` + `hooks/`）

### Zustand Store（客户端状态）

```tsx
// stores/useUserStore.ts
import { create } from 'zustand'

interface UserStore {
  currentUser: { id: number; name: string } | null
  setCurrentUser: (user: UserStore['currentUser']) => void
  clear: () => void
}

export const useUserStore = create<UserStore>((set) => ({
  currentUser: null,
  setCurrentUser: (user) => set({ currentUser: user }),
  clear: () => set({ currentUser: null }),
}))
```

### TanStack Query Hooks（服务端状态）

```tsx
// hooks/useUser.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUsers, getUser, createUser, updateUser, deleteUser } from '@/api/user'
import type { UserQueryParams } from '@/types/user'

const QUERY_KEY = 'users'

/** 用户列表 */
export const useUsers = (params: UserQueryParams) =>
  useQuery({
    queryKey: [QUERY_KEY, params],
    queryFn: () => getUsers(params),
  })

/** 用户详情 */
export const useUser = (id: number) =>
  useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: () => getUser(id),
    enabled: !!id,
  })

/** 新增用户 */
export const useCreateUser = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  })
}

/** 更新用户 */
export const useUpdateUser = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof updateUser>[1] }) =>
      updateUser(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  })
}

/** 删除用户 */
export const useDeleteUser = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  })
}
```

### 规则

| 状态类型 | 存放位置 | 工具 |
|----------|---------|------|
| 服务端数据（列表/详情/CRUD） | `hooks/useXxx.ts` | TanStack Query |
| 全局客户端状态（用户信息/主题/权限） | `stores/useXxxStore.ts` | Zustand |
| 页面局部 UI 状态（弹窗/tab/loading） | 页面组件内 | `useState` |

- **服务端状态禁止放 Zustand**（缓存/重试/失效交给 TanStack Query）
- Store 命名 `useXxxStore`，Hook 命名 `useXxx` / `useCreateXxx`
- Mutation 成功后 `invalidateQueries` 刷新列表
- `queryKey` 用常量定义，避免拼写错误

---

## 七、数据类型层（`types/`）

### 通用类型

> 通用类型模板（`ApiResponse`、`PageResult`、`PageParams`）详见 [`references/api-request.md`](./references/api-request.md)。
>
> 接口数据类型约束（字段映射、分层原则、派生规则）详见 [`references/api-data-types.md`](./references/api-data-types.md)。

### 业务类型

```tsx
// types/user.ts
import type { PageParams } from './common'

/** 用户状态枚举 */
export enum UserStatus {
  Active = 1,
  Disabled = 0,
}

/** 用户列表项 */
export interface UserItem {
  id: number
  name: string
  email: string
  phone: string
  status: UserStatus
  createdAt: string
  updatedAt: string
}

/** 用户查询参数 */
export interface UserQueryParams extends PageParams {
  name?: string
  status?: UserStatus
}

/** 用户表单数据（新增/编辑共用） */
export interface UserFormData {
  name: string
  email: string
  phone: string
  status: UserStatus
}

/** 用户详情（扩展列表项） */
export type UserDetail = UserItem & {
  roles: string[]
  department: string
}
```

### 规则

- **一个业务域一个文件**：`types/user.ts`、`types/order.ts`
- 通用类型放 `types/common.ts`：`ApiResponse`、`PageResult`、`PageParams`
- 实体类型命名：列表项 `XxxItem`、表单 `XxxFormData`、查询 `XxxQueryParams`、详情 `XxxDetail`
- 枚举使用 `enum`（数值枚举）或字面量联合类型（跟随项目风格）
- 派生类型用工具类型：`Pick<UserItem, 'id' | 'name'>`、`Partial<UserFormData>`、`Omit<>`
- **禁止 `any`**，不确定时用 `unknown` + 类型守卫
- 禁止重复定义：同一实体只定义一次，其他接口通过派生获取

### 数据类型约束

以下是必须严格遵守的类型安全约束，确保类型系统在编译期最大化捕获错误。

#### 7.1 严格模式要求

`tsconfig.json` 必须开启以下选项：

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

- `strict: true` — 包含 `strictNullChecks`、`strictFunctionTypes`、`noImplicitAny` 等
- `noUncheckedIndexedAccess` — 索引访问返回 `T | undefined`，强制 null check
- `exactOptionalPropertyTypes` — 区分 `field?: string`（可省略）和 `field: string | undefined`（必须传但可为 undefined）

#### 7.2 ID 类型 — 品牌类型（Branded Types）

不同实体的 ID 不可混用，使用品牌类型在编译期防止错误传参：

```tsx
// types/branded.ts
declare const __brand: unique symbol
type Brand<T, B extends string> = T & { readonly [__brand]: B }

export type UserId = Brand<number, 'UserId'>
export type OrderId = Brand<number, 'OrderId'>
export type CourseId = Brand<number, 'CourseId'>

// 创建品牌值的工具函数（仅在 API 解包时使用）
export const asUserId = (id: number) => id as UserId
export const asOrderId = (id: number) => id as OrderId
export const asCourseId = (id: number) => id as CourseId
```

```tsx
// 使用示例
function getUser(id: UserId) { /* ... */ }
function getOrder(id: OrderId) { /* ... */ }

const userId = asUserId(1)
const orderId = asOrderId(2)

getUser(userId)   // ✅
getUser(orderId)  // ❌ 编译错误：OrderId 不能赋值给 UserId
getUser(1)        // ❌ 编译错误：number 不能赋值给 UserId
```

**规则：** 当项目有 3 个以上实体时，所有实体 ID 必须使用品牌类型。

#### 7.3 可选字段 vs 可空字段

严格区分「可省略」和「值可为空」两种语义：

```tsx
// ✅ 正确：语义清晰
interface UserFormData {
  name: string                // 必填
  nickname?: string           // 可省略（新增时可不传）
  avatar: string | null       // 必须传，但值可以为空（如未上传头像）
  deletedAt: string | null    // 服务端必返回，null 表示未删除
}

// ❌ 错误：混用
interface UserFormData {
  avatar?: string | null | undefined  // 三种「空」含义混在一起
}
```

| 写法 | 语义 | 场景 |
|------|------|------|
| `field: string` | 必填，必有值 | 主要字段 |
| `field?: string` | 可省略，调用方可不传 | 查询参数、表单可选项 |
| `field: string \| null` | 必须传/必返回，但值可为空 | API 返回的可空字段 |

**规则：** 禁止 `field?: string | null`，必须明确选择 `?` 或 `| null` 之一。

#### 7.4 枚举约束

```tsx
// ✅ 数值枚举 — 适合后端传数字状态码
export enum OrderStatus {
  Pending = 0,
  Paid = 1,
  Shipped = 2,
  Completed = 3,
  Cancelled = -1,
}

// ✅ 字面量联合 — 适合前端 UI 状态、字符串类型字段
export type TabKey = 'all' | 'active' | 'archived'
export type Theme = 'light' | 'dark' | 'system'

// ❌ 禁止：字符串枚举（tree-shaking 不友好，增加 bundle 体积）
export enum Theme {
  Light = 'light',   // ❌ 不要用字符串枚举
  Dark = 'dark',
}
```

| 场景 | 方案 |
|------|------|
| 后端返回数字状态码 | `enum`（数值枚举） |
| 前端 UI 状态、事件名、路由参数 | 字面量联合类型 |
| 需要遍历/反查的场景 | `enum` + `Object.values()` |
| 需要复杂映射（label + color + icon） | `as const` 对象 + 辅助类型 |

#### 7.5 `as const` 配置映射

用于状态 → 显示文案/颜色的映射，替代散落在组件中的 if/switch：

```tsx
// constants/orderStatus.ts
export const ORDER_STATUS_MAP = {
  [OrderStatus.Pending]:   { label: '待支付', color: 'orange', icon: 'clock' },
  [OrderStatus.Paid]:      { label: '已支付', color: 'blue',   icon: 'check' },
  [OrderStatus.Shipped]:   { label: '已发货', color: 'cyan',   icon: 'truck' },
  [OrderStatus.Completed]: { label: '已完成', color: 'green',  icon: 'check-circle' },
  [OrderStatus.Cancelled]: { label: '已取消', color: 'gray',   icon: 'x-circle' },
} as const satisfies Record<OrderStatus, { label: string; color: string; icon: string }>

// 使用
const { label, color } = ORDER_STATUS_MAP[order.status]
```

**规则：** 映射对象必须用 `as const satisfies Record<Enum, Shape>` 确保类型完整性（漏加枚举值编译报错）。

#### 7.6 判别联合（Discriminated Unions）

多态数据结构必须使用判别联合，禁止用 `type: string` + 运行时猜测：

```tsx
// ✅ 正确：判别联合
type Notification =
  | { type: 'message'; content: string; senderId: UserId }
  | { type: 'system';  content: string; level: 'info' | 'warn' | 'error' }
  | { type: 'action';  actionUrl: string; label: string }

function renderNotification(n: Notification) {
  switch (n.type) {
    case 'message': return <MessageCard senderId={n.senderId} />  // TS 自动收窄
    case 'system':  return <SystemAlert level={n.level} />
    case 'action':  return <ActionLink url={n.actionUrl} />
  }
}

// ❌ 错误：宽泛的 type 字段
interface Notification {
  type: string
  content?: string
  senderId?: number
  level?: string
  actionUrl?: string
}
```

**规则：**
- 判别字段用字面量联合，不用 `string`
- switch/if 分支必须穷举，利用 `never` 确保编译期安全：
  ```tsx
  default: {
    const _exhaustive: never = n
    throw new Error(`未处理的通知类型: ${(n as any).type}`)
  }
  ```

#### 7.7 日期与时间

```tsx
// API 层：时间字段统一为 ISO 8601 字符串
interface UserItem {
  createdAt: string   // "2024-01-15T08:30:00Z"
  updatedAt: string
}

// 展示层：使用 dayjs / date-fns 格式化，禁止 new Date() 手动处理
import { formatDate } from '@/utils/format'
<span>{formatDate(user.createdAt)}</span>
```

**规则：**
- API 类型中时间字段类型为 `string`（ISO 8601），不用 `Date`
- 禁止在组件中直接 `new Date(xxx).toLocaleDateString()`，统一走 `utils/format.ts`
- 时间比较/计算使用 dayjs 或 date-fns，不手动操作时间戳

#### 7.8 类型守卫

需要运行时类型判断时，必须使用类型守卫函数，禁止裸 `as` 断言：

```tsx
// ✅ 类型守卫
function isUserDetail(user: UserItem | UserDetail): user is UserDetail {
  return 'roles' in user && Array.isArray((user as UserDetail).roles)
}

if (isUserDetail(user)) {
  console.log(user.roles)  // TS 知道这里是 UserDetail
}

// ❌ 禁止：裸断言
const detail = user as UserDetail  // 运行时可能 crash
console.log(detail.roles)
```

**规则：**
- `as` 断言仅允许在 API 解包层（response interceptor）和品牌类型创建函数中使用
- 业务代码中需要类型收窄时，必须用类型守卫 (`is`) 或 `in` / `instanceof` 判断
- 禁止 `as any`、`as unknown as T` 等绕过型断言

#### 7.9 泛型约束

```tsx
// ✅ 有约束的泛型
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key]
}

// ✅ API 层泛型 — 约束返回类型
function useDetail<T extends { id: number }>(id: number, fetcher: (id: number) => Promise<T>) {
  return useQuery({ queryKey: ['detail', id], queryFn: () => fetcher(id) })
}

// ❌ 禁止：无约束泛型当 any 用
function process<T>(data: T): T { /* T 无任何约束，等同于 unknown */ }
```

**规则：**
- 泛型参数必须有约束（`extends`），无约束的 `<T>` 等同于 `<T extends unknown>`，需要确认是否有意为之
- 泛型命名：单参数用 `T`，多参数用语义化名称 `TData`、`TError`、`TParams`

#### 类型约束速查

| 禁止 | 替代方案 |
|------|---------|
| `any` | `unknown` + 类型守卫 |
| `as Type` 裸断言（业务层） | 类型守卫函数 / `in` / `instanceof` |
| `as any`、`as unknown as T` | 重新设计类型或使用判别联合 |
| `field?: string \| null` | 选择 `?` 或 `\| null` 之一 |
| `string` 枚举（`enum Foo { A = 'a' }`） | 字面量联合 `type Foo = 'a' \| 'b'` |
| `type: string` 多态判断 | 判别联合 + 穷举 switch |
| `new Date()` 手动格式化 | dayjs / date-fns + `utils/format.ts` |
| 裸 `number` 做跨实体 ID | 品牌类型 `Brand<number, 'XxxId'>` |
| 无约束泛型 `<T>` | `<T extends SomeBase>` |
| 索引访问不检查 undefined | 开启 `noUncheckedIndexedAccess` |

---

## 八、工具层（`utils/`）

### 规范

```tsx
// utils/format.ts

/** 格式化日期 */
export const formatDate = (dateStr: string, fmt = 'YYYY-MM-DD HH:mm:ss'): string => {
  const d = new Date(dateStr)
  // ... 实现
  return formatted
}

/** 格式化金额（分 → 元） */
export const formatMoney = (cents: number): string =>
  (cents / 100).toFixed(2)

/** 格式化文件大小 */
export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`
}
```

```tsx
// utils/validate.ts

/** 手机号校验 */
export const isPhone = (v: string): boolean => /^1[3-9]\d{9}$/.test(v)

/** 邮箱校验 */
export const isEmail = (v: string): boolean => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
```

```tsx
// utils/storage.ts

/** 带类型的 localStorage 封装 */
export const storage = {
  get<T>(key: string): T | null {
    const raw = localStorage.getItem(key)
    if (!raw) return null
    try { return JSON.parse(raw) as T } catch { return null }
  },
  set<T>(key: string, value: T): void {
    localStorage.setItem(key, JSON.stringify(value))
  },
  remove(key: string): void {
    localStorage.removeItem(key)
  },
}
```

### 规则

- **按职责拆文件**：`format.ts`、`validate.ts`、`storage.ts`、`auth.ts`
- 每个函数必须 `export`，**禁止 default export**
- 参数和返回值必须类型化
- 纯函数优先，无副作用
- 工具函数不依赖 React（不使用 hooks、state、context）
- 禁止放业务逻辑，只放通用逻辑

---

## 九、埋点规范（神策SDK）

> SDK 封装、初始化配置、各类埋点模式代码、属性命名规范、验证清单详见 [`references/sensors-config.md`](./references/sensors-config.md)。

### 规则速览

- **初始化**：`main.tsx` 中 `createRoot` 之前调用 `initSensors()`
- **PV 埋点**：统一在路由 loader 中埋点，不在组件内埋点
- **点击埋点**：优先使用 `TrackButton` 声明式组件；关键操作（删除、提交、支付）必须埋点
- **曝光埋点**：使用 `useTrackExposure` Hook，默认 `once: true`
- **表单埋点**：在 mutation `onSuccess` 中埋点，确保提交成功才上报
- **错误埋点**：全局 ErrorBoundary + axios 拦截器统一处理
- **用户绑定**：登录后 `sensors.login(userId)`，退出 `sensors.logout()`
- **属性命名**：`snake_case`，中文用 `xxx_name`，英文用 `xxx_id`，禁止拼音
- **文档化**：所有埋点记录到 `docs/tracking/sensors-events.md`

---

## 十、命名速查表

| 类别 | 命名规则 | 示例 |
|------|---------|------|
| 页面组件 | PascalCase + `Page` 后缀 | `UserPage`、`OrderListPage` |
| 共享组件 | PascalCase | `PageHeader`、`SearchForm` |
| Hook | `use` + PascalCase | `useUsers`、`useCreateUser` |
| Store | `use` + PascalCase + `Store` | `useUserStore`、`useAuthStore` |
| API 函数 | camelCase（动词 + 实体） | `getUsers`、`createOrder` |
| 类型 | PascalCase + 后缀 | `UserItem`、`UserFormData`、`UserQueryParams` |
| 工具函数 | camelCase（动词开头） | `formatDate`、`isPhone` |
| CSS Module | camelCase | `.filterBar`、`.cardWrapper` |
| 目录 | kebab-case 或 camelCase | `pages/user-management/` |
| 文件 | 组件 PascalCase，其余 camelCase | `UserTable.tsx`、`format.ts` |

## 禁止事项

| 禁止 | 替代方案 |
|------|---------|
| `any` 类型 | `unknown` + 类型守卫 |
| `as Type` 裸断言（业务代码中） | 类型守卫 / `in` / `instanceof` |
| `as any`、`as unknown as T` | 重新设计类型或使用判别联合 |
| `field?: string \| null` 混用 | 选择 `?`（可省略）或 `\| null`（可空）之一 |
| 字符串枚举 `enum Foo { A = 'a' }` | 字面量联合 `type Foo = 'a' \| 'b'` |
| `type: string` 做多态判断 | 判别联合 + 穷举 switch + `never` |
| `new Date()` 手动格式化 | dayjs / date-fns + `utils/format.ts` |
| 裸 `number` 做跨实体 ID（3+ 实体时） | 品牌类型 `Brand<number, 'XxxId'>` |
| 无约束泛型 `<T>` | `<T extends SomeBase>` 明确约束 |
| 组件内直接 `axios.get()` | 通过 `api/` + `hooks/` 调用 |
| 全局 CSS 写组件样式 | Tailwind class 或 CSS Module |
| `!important` | 调整选择器优先级或用 Tailwind 覆盖 |
| 跨层导入（page 导入另一个 page 的组件） | 提取到 `components/` 共享 |
| Store 中放服务端数据 | TanStack Query 管理服务端状态 |
| 工具函数依赖 React | 工具层保持纯函数 |
| 一个文件多个组件导出 | 一个文件一个组件 |
| 手动拼接 class 字符串 | 一律用 `cn()` |
| class 中硬编码 hex/px magic number | 提取到 `tailwind.config.ts` Token |
| 组件 2+ 变体用 if/else 拼 class | 使用 CVA 声明式变体 |
| 不接收外部 `className` 的组件 | 所有共享组件必须支持 `cn(base, className)` |
| 组件内埋点（PV） | 路由 loader 统一埋点 |
| 手动拼接埋点代码 | 使用 `TrackButton` 等声明式组件 |
| 埋点属性使用拼音或中英混合 | 统一 `snake_case`，中文用 `xxx_name` |
| 在请求前埋点（表单提交） | 在 `onSuccess` 中埋点，确保操作成功 |
| 埋点未文档化 | 所有埋点记录到 `docs/tracking/sensors-events.md` |
