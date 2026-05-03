# 设计 Token

## CSS 变量（`styles/globals.css`）

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-primary: #1677ff;
  --color-success: #52c41a;
  --color-warning: #faad14;
  --color-error: #ff4d4f;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  --spacing-page: 24px;
  --spacing-card: 16px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}

#root {
  min-height: 100vh;
}
```

### 规则

- 只放 Tailwind 指令、CSS 变量、全局 reset
- **禁止**在此文件写具体组件样式
- 设计 Token 统一定义为 CSS 变量，供 Tailwind `theme.extend` 引用
- 颜色值来源于设计稿，不允许硬编码 hex

## Tailwind Token 配置（`tailwind.config.ts`）

```ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand:   { DEFAULT: '#1677ff', light: '#4096ff', dark: '#0958d9' },
        success: { DEFAULT: '#52c41a' },
        warning: { DEFAULT: '#faad14' },
        danger:  { DEFAULT: '#ff4d4f' },
      },
      spacing: {
        page: '24px',
        card: '16px',
        section: '32px',
      },
      borderRadius: {
        card: '8px',
        button: '6px',
      },
      fontSize: {
        'page-title': ['20px', { lineHeight: '28px', fontWeight: '600' }],
        'section-title': ['16px', { lineHeight: '24px', fontWeight: '600' }],
      },
    },
  },
} satisfies Config
```

### 规则

- 设计稿中出现 3 次以上的值必须提取为 Token
- Token 命名用语义（`brand`、`page`），不用视觉描述（`blue-600`、`large`）
- 改 Token 值 → 全局生效，不用逐文件搜索替换

### 对比

```tsx
// 差 — 硬编码
<div className="bg-[#1677ff] rounded-[8px] p-[24px] text-[20px]">

// 好 — 语义化 Token
<div className="bg-brand rounded-card p-page text-page-title">
```
