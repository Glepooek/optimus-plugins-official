# 标准目录结构

```
src/
├── main.tsx                  # 主程序入口（埋点初始化）
├── App.tsx                   # 根组件（路由 + Provider）
├── styles/                   # 全局样式
│   ├── globals.css           # Tailwind 指令 + CSS 变量 + reset
│   └── themes.css            # 主题变量（可选）
├── lib/                      # 基础库封装
│   ├── cn.ts                 # tailwind-merge + clsx 工具函数
│   └── sensors.ts            # 神策 SDK 封装
├── pages/                    # 页面（按路由 1:1）
│   └── user/
│       ├── index.tsx         # 页面组件
│       ├── index.module.css  # 页面私有样式（Tailwind 不够时）
│       └── components/       # 页面私有子组件
│           ├── UserTable.tsx
│           └── UserForm.tsx
├── components/               # 全局共享组件
│   ├── PageHeader/
│   │   ├── index.tsx
│   │   └── index.module.css
│   ├── TrackButton/          # 埋点按钮组件
│   │   └── index.tsx
│   └── ErrorBoundary/        # 错误边界（含错误埋点）
│       └── index.tsx
├── api/                      # 接口层
│   ├── request.ts            # axios 实例 + 拦截器（含错误埋点）
│   └── user.ts               # 按模块拆分
├── stores/                   # 数据层（Zustand）
│   └── useUserStore.ts
├── hooks/                    # 自定义 Hooks（含 TanStack Query）
│   ├── useUser.ts
│   └── useTrackExposure.ts   # 曝光埋点 Hook
├── types/                    # 数据类型层
│   ├── user.ts               # 按业务域拆分
│   └── common.ts             # 通用类型（分页、响应包装等）
└── utils/                    # 工具层
    ├── format.ts             # 格式化
    ├── validate.ts           # 校验
    └── storage.ts            # 存储
```

## 放置规则

- 页面私有组件放 `pages/xxx/components/`，共享组件放 `components/`
- 一个业务模块对应一个 API 文件、一个类型文件、一个 Hook 文件
- 全局共享组件使用文件夹包裹：`components/XxxName/index.tsx`
