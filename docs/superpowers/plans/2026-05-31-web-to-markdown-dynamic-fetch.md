# web-to-markdown 动态页面支持 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `unipus:office:web-to-markdown` skill 中引入三级抓取降级（curl → Playwright MCP → WebFetch），支持 SPA 等动态渲染页面。

**Architecture:** 仅修改单文件 `SKILL.md`，不引入脚本或外部文件。在第三节「抓取策略」替换为三级结构，在「输出格式」新增抓取路径标注，在第六节「错误处理」新增 Playwright MCP 相关行。

**Tech Stack:** Playwright MCP（`browser_navigate` / `browser_wait_for_load_state` / `browser_wait_for_selector` / `browser_wait` / `browser_snapshot` / `browser_close`）

---

## 文件变更清单

| 操作 | 文件 | 位置 |
|------|------|------|
| Modify | `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md` | 第143-175行：抓取策略 |
| Modify | `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md` | 第204-212行：输出格式 |
| Modify | `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md` | 第308-319行：错误处理表 |

---

## Task 1：替换「抓取策略」节为三级降级结构

**Files:**
- Modify: `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md:143-175`

- [ ] **Step 1: 定位现有「抓取策略」节范围**

  打开文件，确认第 143 行为 `### 抓取策略`，第 175 行为 `**内容完整性验证：** ...`（含该行），这是要替换的区域。

- [ ] **Step 2: 用新内容替换该区域**

  将第 143-175 行（`### 抓取策略` 至 `**内容完整性验证：**` 行）替换为以下内容：

  ```markdown
  ### 抓取策略

  三级降级，按顺序执行，前一级内容有效则不进入下一级：

  **一级：curl（静态 / SSR 页面，默认路径）**

  ```bash
  curl -s "<URL>" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  | python3 -c "
  import sys, re
  html = sys.stdin.read()
  html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
  html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
  text = re.sub(r'<[^>]+>', ' ', html)
  text = re.sub(r'[ \t]+', ' ', text)
  text = re.sub(r'\n{3,}', '\n\n', text)
  print(text)
  "
  ```

  若页面内容较长，分段抓取（每次偏移 8000 字符）直到内容完整：

  ```bash
  ... | python3 -c "...; print(text[:8000])"      # 第一段
  ... | python3 -c "...; print(text[8000:16000])"  # 第二段
  # 继续直到内容结束
  ```

  **curl 完成后执行动态页面判定**（满足任一条件 → 内容无效，进入二级）：

  | # | 规则 | 说明 |
  |---|------|------|
  | 1 | 正文字符数 < 200 | 基本空壳 |
  | 2 | 含 SPA 框架标记且正文 < 500 字符 | `id="root"` / `id="app"` / `id="__nuxt"` / `id="__layout"` / `data-reactroot` |
  | 3 | 含 JS 数据注入标记（无论正文长短） | `__NEXT_DATA__` / `__NUXT__` / `__REDUX_STATE__` / `window.__INITIAL_STATE__` |
  | 4 | 含骨架屏 / 加载占位符特征词 | `class="skeleton"` / `loading-placeholder` / `shimmer` / `aria-busy="true"` |
  | 5 | HTTP 非 200 且非 4xx 认证错误 | 网络错误，直接失败，不触发降级 |

  **二级：Playwright MCP（curl 内容无效时）**

  ```
  1. browser_navigate(url=<URL>)

  2. 等待策略（三层兜底）：
     a. browser_wait_for_load_state(state="networkidle", timeout=8000)
        超时 → 进入 b
     b. browser_wait_for_selector(
          selector="main, article, [role='main'], #main-content, .content",
          timeout=5000
        )
        超时 → 进入 c
     c. browser_wait(milliseconds=2000)

  3. browser_snapshot()
     → 返回 accessibility tree（渲染后语义文本，无 JS/CSS 噪音）

  4. 内容有效性二次校验（同判定规则 1-4）
     无效 → 进入三级，结果标注「Playwright 抓取内容仍为空，降级 WebFetch」
     有效 → 进入清理 / 转换 / 翻译流程（与静态路径相同）
     结果标注「动态抓取」

  5. browser_close()
  ```

  **三级：WebFetch（Playwright MCP 不可用或失败时）**

  在 prompt 中明确要求：「返回页面完整原始文本，不要省略、不要总结、不要截断任何部分」。长页面仍可能被截断，需多次调用补全。结果标注「WebFetch，内容可能不完整」。

  **内容完整性验证：** 抓取后检查是否包含文章结语/底部内容，若缺失则继续分段抓取。
  ```

- [ ] **Step 3: 验证替换结果**

  确认以下内容存在：
  - `### 抓取策略` 标题
  - `三级降级` 字样
  - `动态页面判定` 表格（5 行规则）
  - `browser_navigate` 调用
  - `browser_snapshot` 调用
  - `browser_close` 调用
  - `**内容完整性验证：**` 行仍在末尾

- [ ] **Step 4: 提交**

  ```bash
  git add plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
  git commit -m "feat(web-to-markdown): 重构抓取策略为三级降级（curl→Playwright MCP→WebFetch）"
  ```

---

## Task 2：更新「输出格式」节新增抓取路径标注

**Files:**
- Modify: `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md`（输出格式节）

- [ ] **Step 1: 定位「输出格式」节的代码块**

  搜索 `### 输出格式`，找到其下方的代码块，当前内容为：

  ```
  ✓ docs/blog/guide.md（新建，核对完整）
  ✓ docs/blog/guide.md（新建，已补全 2 处）
  ✓ docs/blog/guide.md（已存在，核对完整）
  ✓ docs/blog/guide.md（已存在，已补全 3 处）
  ✗ docs/blog/guide.md — 抓取失败 (403)
  ```

- [ ] **Step 2: 替换为包含抓取路径标注的新内容**

  将上述代码块替换为：

  ```
  ✓ docs/blog/guide.md（新建，核对完整）
  ✓ docs/blog/guide.md（新建，已补全 2 处）
  ✓ docs/blog/guide.md（新建，动态抓取，核对完整）
  ✓ docs/blog/guide.md（新建，动态抓取，已补全 2 处）
  ✓ docs/blog/guide.md（新建，WebFetch，内容可能不完整）
  ✓ docs/blog/guide.md（已存在，核对完整）
  ✓ docs/blog/guide.md（已存在，已补全 3 处）
  ✓ docs/blog/guide.md（已存在，动态抓取，核对完整）
  ✓ docs/blog/guide.md（已存在，动态抓取，已补全 2 处）
  ✓ docs/blog/guide.md（已存在，WebFetch，内容可能不完整）
  ✗ docs/blog/guide.md — 抓取失败 (403)
  ```

- [ ] **Step 3: 验证替换结果**

  确认以下行均存在：
  - `动态抓取，核对完整`
  - `动态抓取，已补全 2 处`
  - `WebFetch，内容可能不完整`
  - 存量核对（「已存在」）对应的三条变体

- [ ] **Step 4: 提交**

  ```bash
  git add plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
  git commit -m "feat(web-to-markdown): 输出格式新增动态抓取和 WebFetch 降级标注"
  ```

---

## Task 3：更新「错误处理」表新增 Playwright MCP 相关行

**Files:**
- Modify: `plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md`（第六节）

- [ ] **Step 1: 定位「错误处理」表**

  搜索 `## 六、错误处理`，找到其下方的 Markdown 表格，当前末行为：

  ```
  | 文件已存在 | 不覆盖，执行存量核对流程，结果标注"已存在，核对完整/已补全 N 处" |
  ```

- [ ] **Step 2: 在表格末尾追加两行**

  在 `| 文件已存在 | ...` 行之后追加：

  ```markdown
  | curl 不可用 | 跳过 curl，直接尝试 Playwright MCP；若 MCP 也不可用则降级 WebFetch |
  | Playwright MCP 不可用或抓取内容仍为空 | 降级使用 WebFetch，结果标注「WebFetch，内容可能不完整」 |
  ```

  同时，删除原有的 `| curl 不可用 | 降级使用 WebFetch，告知用户内容可能不完整 |` 行（已被上方新行替代）。

- [ ] **Step 3: 验证修改结果**

  确认：
  - `curl 不可用` 行已更新为新内容（包含"尝试 Playwright MCP"）
  - `Playwright MCP 不可用或抓取内容仍为空` 行存在
  - 原有其他行（4xx/5xx、内容为空、写权限等）未被改动

- [ ] **Step 4: 更新版本号**

  在 SKILL.md 第 4 行 `version: "1.1.1"` 改为 `version: "1.2.0"`（新增功能 → Minor 升级）。

- [ ] **Step 5: 更新 marketplace.json 版本号**

  打开 `.claude-plugin/marketplace.json`，将 `unipus-office-plugin` 的版本号同步更新为 `1.2.0`。

- [ ] **Step 6: 提交**

  ```bash
  git add plugins/unipus-office-plugin/skills/unipus-office-web-to-markdown/SKILL.md
  git add .claude-plugin/marketplace.json
  git commit -m "feat(web-to-markdown): 错误处理表新增 Playwright MCP 降级行，版本升至 1.2.0"
  ```

---

## 验收标准

1. SKILL.md 第三节「抓取策略」包含三级降级逻辑，curl 判定规则 5 条，Playwright MCP 调用序列完整（`browser_navigate` → 等待策略 D → `browser_snapshot` → `browser_close`）
2. 「输出格式」节包含「动态抓取」和「WebFetch，内容可能不完整」标注变体（新建 + 已存在各两条）
3. 「错误处理」表包含 Playwright MCP 不可用的处理行
4. SKILL.md `version` 字段为 `1.2.0`
5. `.claude-plugin/marketplace.json` 版本号已同步
