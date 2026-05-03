# 神策 SDK 配置

## SDK 封装（`lib/sensors.ts`）

```tsx
import sensors from 'sa-sdk-javascript'

/** 神策 SDK 初始化 */
export const initSensors = () => {
  const projectName = import.meta.env.VITE_PROJECT_NAME || 'default'

  sensors.init({
    server_url: `https://datasink.unipus.cn/buried-poing/data?project=${projectName}`,
    is_track_single_page: true,
    use_client_time: true,
    send_type: 'ajax',
    show_log: false,
    heatmap: {
      clickmap: 'default',
      scroll_notice_map: 'default',
    },
  })

  // 注册全局公共属性
  sensors.registerPage({
    platform_type: 'web',
    app_version: import.meta.env.VITE_APP_VERSION,
  })

  // 如果已登录，绑定用户 ID
  const userId = localStorage.getItem('user_id')
  if (userId) {
    sensors.login(userId)
  }
}

/** 页面浏览埋点 */
export const trackPageView = (pageName: string, pagePath: string) => {
  sensors.quick('autoTrackSinglePage', {
    page_name: pageName,
    page_path: pagePath,
  })
}

/** 点击埋点 */
export const trackClick = (buttonName: string, extraProps?: Record<string, any>) => {
  sensors.track('button_click', {
    button_name: buttonName,
    ...extraProps,
  })
}

/** 用户登录 */
export const trackLogin = (userId: string, userInfo: Record<string, any>) => {
  sensors.login(userId)
  sensors.setProfile(userInfo)
  sensors.track('user_login', { login_method: 'password' })
}

/** 用户退出 */
export const trackLogout = () => {
  sensors.track('user_logout')
  sensors.logout()
}

export default sensors
```

## 初始化位置

**`main.tsx`** 中，在 `createRoot` 之前调用：

```tsx
import { initSensors } from '@/lib/sensors'

initSensors() // ← 必须在应用渲染前初始化

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

## 配置要点

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `server_url` | `https://datasink.unipus.cn/buried-poing/data?project=${projectName}` | 数据上报地址，`projectName` 通过 `VITE_PROJECT_NAME` 环境变量区分项目 |
| `is_track_single_page` | `true` | 单页面应用必须开启 |
| `send_type` | `'ajax'` | 数据发送方式 |
| `show_log` | `false` | 生产环境禁止开启；调试时可临时改 `true`，不要提交 |

## 页面浏览埋点（PV）

统一在路由 loader 中埋点：

```tsx
// router/index.tsx
import { createBrowserRouter } from 'react-router-dom'
import { trackPageView } from '@/lib/sensors'

export const router = createBrowserRouter([
  {
    path: '/users',
    lazy: async () => {
      const { default: UserPage } = await import('@/pages/user')
      return {
        Component: UserPage,
        loader: () => {
          trackPageView('用户管理', '/users')
          return null
        },
      }
    },
  },
])
```

## 声明式点击埋点组件

```tsx
// components/TrackButton/index.tsx
import { Button } from 'antd'
import type { ButtonProps } from 'antd'
import sensors from '@/lib/sensors'

interface TrackButtonProps extends ButtonProps {
  trackEvent: string
  trackProps?: Record<string, any>
}

export default function TrackButton({
  trackEvent,
  trackProps,
  onClick,
  children,
  ...props
}: TrackButtonProps) {
  const handleClick = (e: React.MouseEvent<HTMLElement>) => {
    sensors.track(trackEvent, trackProps)
    onClick?.(e)
  }

  return (
    <Button {...props} onClick={handleClick}>
      {children}
    </Button>
  )
}
```

## 曝光埋点 Hook

```tsx
// hooks/useTrackExposure.ts
import { useEffect, useRef } from 'react'
import sensors from '@/lib/sensors'

interface ExposureOptions {
  event: string
  props?: Record<string, any>
  once?: boolean
  threshold?: number
}

export const useTrackExposure = ({
  event,
  props,
  once = true,
  threshold = 0.5,
}: ExposureOptions) => {
  const ref = useRef<HTMLDivElement>(null)
  const tracked = useRef(false)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && (!once || !tracked.current)) {
          sensors.track(event, props)
          tracked.current = true
          if (once) observer.disconnect()
        }
      },
      { threshold },
    )

    observer.observe(element)
    return () => observer.disconnect()
  }, [event, props, once, threshold])

  return ref
}
```

## 错误埋点

**全局 JS 错误（ErrorBoundary）：**

```tsx
// components/ErrorBoundary/index.tsx
import { Component, type ReactNode } from 'react'
import sensors from '@/lib/sensors'

export class ErrorBoundary extends Component<{ children: ReactNode }> {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    sensors.track('js_error', {
      error_message: error.message,
      error_stack: error.stack?.substring(0, 500),
      component_stack: errorInfo.componentStack?.substring(0, 500),
    })
  }

  render() {
    return this.props.children
  }
}
```

**接口错误（axios 拦截器）：**

```tsx
// api/request.ts 响应拦截器中
sensors.track('api_error', {
  api_url: error.config?.url,
  api_method: error.config?.method,
  status_code: error.response?.status,
  error_message: error.message,
})
```

## 用户登录/退出

```tsx
// 登录成功
sensors.login(userId)
sensors.setProfile({ name, email, register_time })
sensors.track('user_login', { login_method: 'password' })

// 退出登录
sensors.track('user_logout')
sensors.logout()
```

## 属性命名规范

| 属性类型 | 命名规则 | 示例 |
|---------|---------|------|
| 页面名称 | `page_name`（中文） | "用户管理" |
| 页面路径 | `page_path` | "/users" |
| 按钮名称 | `button_name`（中文） | "新增用户" |
| 按钮 ID | `button_id`（英文） | "add_user" |
| 表单名称 | `form_name`（中文） | "新增用户" |
| 元素 ID | `element_id`（英文） | "banner_home_top" |
| 元素名称 | `element_name`（中文） | "首页顶部横幅" |

- 属性名使用 `snake_case`
- 中文描述用 `xxx_name`，英文标识用 `xxx_id`
- 禁止拼音或中英混合

## 埋点清单文档

位置：`docs/tracking/sensors-events.md`，所有埋点必须文档化。

## 埋点验证清单

- [ ] 页面浏览埋点在每个路由切换时触发
- [ ] 关键按钮点击有埋点且属性完整
- [ ] 用户登录后 userId 正确绑定
- [ ] 表单提交成功后埋点触发
- [ ] 曝光埋点不重复上报（once=true）
- [ ] JS 错误和接口错误能被捕获并上报
- [ ] 所有埋点事件名和属性符合命名规范
