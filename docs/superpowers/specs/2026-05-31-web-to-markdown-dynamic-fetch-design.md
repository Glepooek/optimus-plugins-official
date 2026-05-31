# 设计文档：web-to-markdown 动态页面支持

**日期：** 2026-05-31  
**Skill：** `unipus:office:web-to-markdown`  
**目标：** 在现有 curl → WebFetch 两级降级基础上，引入 Playwright MCP 支持 SPA 等动态页面抓取

---

## 背景

现有抓取策略依赖 `curl` + Python 正则剥标签，仅能获取服务端返回的初始 HTML，对客户端渲染（CSR）页面（React SPA、Angular、Nuxt CSR 等）无法获取实际内容。运行环境已安装 Playwright MCP，可直接通过 MCP 工具调用浏览器 API，无需额外脚本。

---

## 方案选型

采用**方案 B：新增独立降级判断逻辑**，在现有抓取策略节中插入三级降级路径，各路径独立描述，与现有 skill 写法惯例一致，不引入文件结构变化。

---

## 一、抓取策略重构（三级降级）

### 一级：curl（静态 / SSR 页面，默认路径）

执行现有 curl 抓取流程，完成后执行**动态页面判定**。

**动态页面判定规则**（满足任一条件 → 内容无效，降级二级）：

| # | 规则 | 说明 |
|---|------|------|
| 1 | 正文字符数 < 200 | 基本空壳 |
| 2 | 含 SPA 框架标记且正文 < 500 字符 | `id="root"` / `id="app"` / `id="__nuxt"` / `id="__layout"` / `data-reactroot` |
| 3 | 含 JS 数据注入标记（无论正文长短） | `__NEXT_DATA__` / `__NUXT__` / `__REDUX_STATE__` / `window.__INITIAL_STATE__` |
| 4 | 含骨架屏 / 加载占位符特征词 | `class="skeleton"` / `loading-placeholder` / `shimmer` / `aria-busy="true"` |
| 5 | HTTP 非 200（排除 4xx 认证错误） | 网络错误，不触发 Playwright，直接失败 |

> 规则 4 可能对使用 `skeleton` 做 CSS 动画的页面产生误报，代价仅为多跑一次 Playwright，不影响正确性。

### 二级：Playwright MCP（curl 内容无效时）

**调用序列：**

```
1. browser_navigate(url)

2. 等待策略 D（三级兜底）：
   a. browser_wait_for_load_state(state="networkidle", timeout=8000)
      超时 → 进入 b
   b. browser_wait_for_selector(
        selector="main, article, [role='main'], #main-content, .content",
        timeout=5000
      )
      超时 → 进入 c
   c. browser_wait(milliseconds=2000)

3. browser_snapshot()
   → 返回 accessibility tree（渲染后语义文本，干净无 JS/CSS 噪音）

4. 内容有效性二次校验（同判定规则 1-4）
   无效 → 降级三级，标注「Playwright 抓取内容仍为空，降级 WebFetch」
   有效 → 进入清理 / 转换 / 翻译流程（与静态路径相同）

5. browser_close()（释放资源）
```

**结果标注：** 在输出行标注「动态抓取」。

### 三级：WebFetch（Playwright MCP 不可用或失败时）

沿用现有 WebFetch 流程，在 prompt 中明确要求返回完整原始文本，长页面多次调用补全。

**结果标注：** 标注「WebFetch，内容可能不完整」。

---

## 二、输出格式变更

| 输出行 | 触发场景 |
|--------|---------|
| `✓ docs/x.md（新建，核对完整）` | curl 成功（默认，不加标注） |
| `✓ docs/x.md（新建，动态抓取，核对完整）` | Playwright MCP 成功 |
| `✓ docs/x.md（新建，动态抓取，已补全 2 处）` | Playwright MCP 成功 + 补全 |
| `✓ docs/x.md（新建，WebFetch，内容可能不完整）` | 最终降级 WebFetch |
| `✗ docs/x.md — 抓取失败 (403)` | 认证失败，不触发动态降级 |

存量核对流程格式同理，新建 → 已存在。

---

## 三、不在此次范围内

- 需要登录后才能访问的页面（带 Cookie / Session）
- 需要用户手动点击「加载更多」的无限滚动内容
- Playwright MCP 的安装配置（已由用户环境预装）

---

## 四、实施位置

修改文件：`plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md`

改动点：
1. **第三节「抓取策略」**：替换为三级降级结构
2. **第三节「输出格式」**：新增动态抓取和 WebFetch 降级的标注行
3. **第六节「错误处理」**：新增 Playwright MCP 不可用的处理行
