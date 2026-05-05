# 第十章：埋点方案（神策SDK）— 章节模板

> 本文件是 architecture-doc 第十章的输出模板。具体 SDK 配置和代码模式参见 `skills/coding-standards/references/sensors-config.md`。

```markdown
## 10. 埋点方案（神策SDK）

### 10.1 埋点策略

| 埋点类型 | 触发时机 | 实现方式 |
|---------|---------|---------|
| 页面浏览（pageview） | 路由切换时 | React Router 路由守卫统一埋点 |
| 按钮点击（click） | 用户交互时 | 组件级手动埋点 + 声明式高阶组件 |
| 表单提交（submit） | 表单成功提交后 | 统一在 API success 回调中埋点 |
| 曝光埋点（exposure） | 元素进入可视区域 | IntersectionObserver + 自定义 Hook |
| 错误埋点（error） | 全局错误捕获 | ErrorBoundary + axios 拦截器 |

### 10.2 SDK 初始化

**初始化时机：** `main.tsx` 中，在 `createRoot` 之前

[从 sensors-config.md 获取 initSensors 代码]

### 10.3 页面浏览埋点（PV）

**方案：** 在路由层统一拦截，自动上报页面浏览事件

[从 sensors-config.md 获取路由 loader 埋点代码]

### 10.4 点击埋点

[从 sensors-config.md 获取 TrackButton 组件代码]

### 10.5 曝光埋点

[从 sensors-config.md 获取 useTrackExposure Hook 代码]

### 10.6 登录用户绑定

[从 sensors-config.md 获取登录/退出代码]

### 10.7 错误埋点

[从 sensors-config.md 获取 ErrorBoundary 和接口错误埋点代码]

### 10.8 埋点清单管理

**文档化所有埋点事件：**

| 事件名 | 触发时机 | 属性字段 | 负责人 |
|--------|---------|---------|--------|
| button_click | 按钮点击 | button_name, button_id, page_name | - |
| page_view | 页面浏览 | page_name, page_path | 自动 |
| user_login | 登录成功 | login_method | - |
| form_submit | 表单提交成功 | form_name, form_data | - |
| xxx_exposure | 元素曝光 | element_id, element_name | - |

**埋点清单文件位置：** `docs/tracking/sensors-events.md`

### 10.9 测试与调试

**埋点校验清单：**
- [ ] 页面浏览事件在每个路由切换时触发
- [ ] 关键按钮点击有埋点且属性完整
- [ ] 用户登录后 userId 正确绑定
- [ ] 错误埋点能捕获 JS 错误和接口错误
- [ ] 曝光埋点不重复上报（once=true 时）
```
