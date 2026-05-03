# API 请求层配置

## axios 实例（`api/request.ts`）

```tsx
import axios from 'axios'
import type { AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types/common'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
})

// 请求拦截 — 注入 Token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截 — 解包 + 统一错误处理
request.interceptors.response.use(
  (res: AxiosResponse<ApiResponse>) => {
    if (res.data.code !== 0) {
      return Promise.reject(new Error(res.data.message || '请求失败'))
    }
    return res.data.data as any
  },
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default request
```

## 配置要点

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `baseURL` | `import.meta.env.VITE_API_BASE_URL` | 通过环境变量配置 |
| `timeout` | `15000` (15s) | 请求超时时间 |
| Token 存储 | `localStorage.getItem('token')` | 存储方式和 key 名 |
| Token 注入 | `Bearer ${token}` | Authorization header 格式 |
| 业务错误码 | `code !== 0` → reject | 后端统一响应中的错误码判断 |
| 401 处理 | 跳转 `/login` | 未认证跳转页面 |

## API 函数模板

```tsx
// api/user.ts
import request from './request'
import type { UserItem, UserFormData, UserQueryParams, PageResult } from '@/types/user'

/** 用户列表 */
export const getUsers = (params: UserQueryParams) =>
  request.get<PageResult<UserItem>>('/users', { params })

/** 用户详情 */
export const getUser = (id: number) =>
  request.get<UserItem>(`/users/${id}`)

/** 新增用户 */
export const createUser = (data: UserFormData) =>
  request.post<UserItem>('/users', data)

/** 更新用户 */
export const updateUser = (id: number, data: Partial<UserFormData>) =>
  request.put<UserItem>(`/users/${id}`, data)

/** 删除用户 */
export const deleteUser = (id: number) =>
  request.delete<void>(`/users/${id}`)
```

## 第三方服务封装（`api/xxx.service.ts`）

当需要对接第三方云服务（如七牛云上传、OSS、COS 等），采用 **service 对象模式**，将获取凭证、上传文件、完整流程封装为独立 service 文件。

```tsx
// api/qiniu.service.ts
import api from './request'
import { v4 as uuidv4 } from 'uuid'

export const qiniuService = {
  /**
   * 获取七牛云上传 Token
   * @returns {{ token, key, domain, uploadUrl }}
   */
  async getUploadToken() {
    try {
      const response = await api.get('/api/lms/qiniu/upload-token')
      return { success: true, data: response.data }
    } catch (error) {
      return { success: false, error: (error as Error).message }
    }
  },

  /**
   * 上传文件到七牛云
   * @param file - 文件 Blob
   * @param token - 上传凭证
   * @param key - 文件 key
   * @param uploadUrl - 七牛云上传地址
   * @returns 文件访问 URL
   */
  async uploadFile(file: Blob, token: string, key: string, uploadUrl: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('token', token)
    formData.append('key', key)

    const response = await fetch(uploadUrl, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`)
    }

    return response.json()
  },

  /**
   * 完整上传流程：获取 token → 上传文件 → 返回访问 URL
   * @param fileBlob - 文件 Blob
   * @returns {{ success, url, error }}
   */
  async uploadRecording(fileBlob: Blob) {
    try {
      const tokenResult = await this.getUploadToken()
      if (!tokenResult.success) {
        return { success: false, error: '获取上传凭证失败' }
      }

      const { token, key, domain, uploadUrl } = tokenResult.data!
      const finalKey = `${key}/${uuidv4()}${fileBlob.type.replace('audio/', '.')}`
      await this.uploadFile(fileBlob, token, finalKey, uploadUrl)

      const url = `${domain}/${finalKey}`
      return { success: true, url }
    } catch (error) {
      return { success: false, error: (error as Error).message }
    }
  },
}
```

### Service 模式规则

| 项 | 规则 |
|----|------|
| 文件命名 | `api/xxx.service.ts`，与普通 API 文件区分 |
| 导出形式 | `export const xxxService = { ... }`，对象字面量，方法间可用 `this` 互调 |
| 凭证获取 | 统一封装为 `getUploadToken()` 等方法，不暴露给调用方 |
| 错误处理 | 返回 `{ success, data?, error? }` 结构，调用方无需 try/catch |
| 第三方上传 | 使用原生 `fetch` + `FormData`，不走 axios 拦截器（第三方域名无需注入 Token） |
| 文件 key | 使用 UUID 避免重名，拼接文件后缀 |
| 完整流程方法 | 组合内部方法，提供一步到位的 `uploadXxx()` 供业务层调用 |

---

## 通用类型（`types/common.ts`）

```tsx
/** 后端统一响应包装 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 分页响应 */
export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

/** 分页请求参数 */
export interface PageParams {
  page: number
  pageSize: number
}
```
