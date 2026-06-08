---
name: unipus-qa-ui-scripts
description: 快速初始化 Midscene + Playwright UI 自动化测试项目，生成完整的项目结构、配置文件和测试模板；也支持将测试用例文档转换为 UI 自动化脚本并补全缺失的项目文件。当用户说"创建 Midscene 测试项目"、"初始化 UI 自动化框架"、"搭建 Playwright + Midscene 项目"、"快速启动 UI 自动化项目"、"将测试用例转换为自动化脚本"、"把用例转成 UI 脚本"、"补全项目文件"时触发。
creator：yinxuan@unipus.cn
---

# Midscene UI 自动化测试项目启动器

本 skill 包含两个独立工作流，根据用户意图选择执行：

- **工作流 A**：初始化新项目（用户说"创建/初始化/搭建项目"）
- **工作流 B**：将测试用例文档转换为 UI 自动化脚本（用户说"转换用例/把用例转成脚本"）
- **工作流 C**：补全项目缺失文件（用户说"缺少项目文件/补全文件"）

---

## 工作流 A：初始化新项目

### 第一步：收集项目信息

询问用户以下信息（用 AskUserQuestion 逐步收集）：
1. **项目目录路径**（必填，默认 `./ui-automation`，所有 UI 自动化文件统一存放在此目录下，与业务代码隔离）
2. **登录页面 URL**（必填）
3. **测试账号**：用户名 + 密码
4. **AI 模型选择**：阿里云 Qwen（默认）/ OpenAI / 其他兼容服务
5. **API Key**（必填，提示不会保存到代码仓库）

> **重要**：UI 自动化项目作为独立子目录存在，拥有自己的 `package.json`、`tsconfig.json`、`node_modules`，不与主项目的依赖混合。

### 第二步：创建目录结构

在用户指定目录（默认 `ui-automation/`）下创建以下结构，所有 UI 自动化相关文件统一存放于此：
```
{PROJECT_DIR}/                     # 默认 ui-automation/
├── e2e/
│   ├── .auth/                     # 空目录（存储登录状态，被 .gitignore 排除）
│   ├── utils/
│   │   └── config.ts              # 配置管理器
│   ├── auth.setup.ts              # 手动登录脚本
│   ├── fixture.ts                 # Midscene AI 测试夹具
│   └── run-all-tests.spec.ts      # 全量测试运行入口
├── config/
│   └── environments.json          # 多环境配置
├── test-results/                  # 测试产物（trace/video/screenshot）
├── test-report/                   # 自定义 HTML+JSON 报告
├── test-screenshots/              # 失败截图
├── midscene_run/report/           # Midscene AI 报告
├── node_modules/                  # 独立的依赖目录（不与主项目共享）
├── .env                           # AI API 配置（不提交到 git）
├── .env.example                   # 配置示例（提交到 git）
├── .gitignore
├── package.json                   # 独立的依赖管理
├── playwright.config.ts           # 主配置（带 setup 依赖）
├── playwright-runner.config.ts    # runner 专用配置（无 setup 依赖）
├── tsconfig.json                  # TypeScript 配置（模块解析 + 类型检查）
└── package-lock.json
```

> **设计原则**：UI 自动化项目作为独立子目录，拥有自己的 `package.json` 和 `node_modules`，与主项目完全隔离。所有命令都需要先 `cd {PROJECT_DIR}` 再执行。业务测试脚本（如 `e2e/{功能模块}.spec.ts`）由用户根据测试用例自行创建，并在 `run-all-tests.spec.ts` 的 `testScripts` 数组中注册。

### 第三步：生成各文件内容

用用户提供的信息替换模板变量后，逐一创建文件。

#### package.json
读取模板：`assets/templates/package.json`，将 `{{PROJECT_NAME}}` 替换为项目目录名。
- 包含 `@playwright/test`、`@midscene/web`、`dotenv`、`typescript` 四个依赖
- 包含以下 npm scripts 快捷命令：
  - `npm test` — 运行全部测试
  - `npm run test:headed` — 有头模式运行
  - `npm run test:ui` — Playwright UI 模式
  - `npm run test:runner` — 通过 runner 运行全部测试（推荐）
  - `npm run test:auth` — 执行手动登录
  - `npm run report` — 查看 Playwright 报告

#### playwright.config.ts
直接使用：`assets/templates/playwright.config.ts`。
- 已开启 `trace: "on"`, `screenshot: "on"`, `video: "on"` 全量录制
- 包含 setup project（登录）和 chromium project（测试）
- **chromium project 不设置 `dependencies: ["setup"]`**，直接读取已保存的 `storageState`，避免每次运行都触发登录
- 登录态过期时才需手动执行 `npm run test:auth` 重新登录

#### playwright-runner.config.ts
直接使用：`assets/templates/playwright-runner.config.ts`。
- 专门用于运行 `run-all-tests.spec.ts`
- 不依赖 setup project，避免重复登录

#### .env
基于 `assets/templates/.env.example`，用用户提供的 API Key 替换占位符，并根据选择的模型调整：
- **阿里云 Qwen（默认）**：
  ```
  OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
  MIDSCENE_MODEL_NAME="qwen-vl-max-latest"
  MIDSCENE_USE_QWEN_VL=1
  ```
- **OpenAI**：
  ```
  OPENAI_BASE_URL="https://api.openai.com/v1"
  MIDSCENE_MODEL_NAME="gpt-4o"
  ```
  删除 `MIDSCENE_USE_QWEN_VL` 行

同时创建 `.env.example`（保留占位符，不含真实 Key）。

#### config/environments.json
使用 `assets/templates/environments.json`，将 `test` 环境中的：
- `loginUrl` 替换为用户提供的登录 URL
- `username` / `password` 替换为用户提供的测试账号
- home / dashboard URL 根据登录 URL 推断基础 URL

#### e2e/utils/config.ts
直接使用：`assets/templates/config.ts`（无需修改）。

#### e2e/auth.setup.ts
使用 `assets/templates/auth.setup.ts`。
- 采用**自动登录模式**：从 `config/environments.json` 读取 `loginUrl`、`username`、`password`，自动填写表单并提交
- 使用 Playwright 原生定位器匹配常见的邮箱/账号输入框、密码框和登录按钮（兼容多种 placeholder/name/type 写法）
- 等待页面跳转离开 `/login` 路径确认登录成功
- 登录状态自动保存到 `e2e/.auth/state.json`
- 若遇到验证码、SSO、扫码等特殊登录方式，可将自动填写部分替换为 `await page.pause()` 手动完成

#### e2e/fixture.ts
直接使用：`assets/templates/fixture.ts`（无需修改）。

#### e2e/run-all-tests.spec.ts
使用 `assets/templates/run-all-tests.spec.ts`。
- 全量测试运行入口，通过子进程编排所有测试脚本
- 自动生成临时 playwright config，注入 storageState（登录态）和 microphone 权限
- 开启 trace/screenshot/video 全量录制
- 生成自定义 HTML+JSON 报告（含图表统计）
- 生成 Midscene AI 报告
- 修改 `testScripts` 数组来控制要运行的测试脚本，每新增一个 spec 文件就追加路径

#### .gitignore
直接使用：`assets/templates/.gitignore`。

#### tsconfig.json
直接使用：`assets/templates/tsconfig.json`（无需修改）。
- 配置 `moduleResolution: "bundler"` 确保 TypeScript 正确解析 `./fixture` 等相对模块导入
- 配置 `strict: false` 避免隐式 `any` 类型报错（Midscene fixture 的解构参数）
- 配置 `esModuleInterop: true` 兼容 CommonJS 模块（如 dotenv）
- `include` 仅包含 `e2e/**/*.ts`，不编译其他目录

> **重要**：缺少 `tsconfig.json` 会导致所有 `.spec.ts` 文件报大量 TypeScript 错误（找不到模块、隐式 any 类型），这是项目初始化必须生成的文件。

### 第三步半：自动安装依赖并验证

文件全部生成后，**必须自动执行以下命令**确保项目可运行：

```bash
# 1. 安装 npm 依赖
cd {PROJECT_DIR}
npm install

# 2. 安装 Playwright 浏览器
npx playwright install chromium
```

安装完成后，**执行验证检查**：

1. 使用 `getDiagnostics` 工具检查 `e2e/fixture.ts` 和 `e2e/example.spec.ts` 是否有 TypeScript 错误
2. 如果仍有"找不到模块"或"隐式 any 类型"错误，按以下顺序排查：
   - 确认 `tsconfig.json` 已生成在项目根目录
   - 确认 `package.json` 中包含 `@playwright/test`、`@midscene/web`、`dotenv`、`typescript` 四个依赖
   - 确认 `npm install` 已成功执行（`node_modules` 目录存在）
   - 确认 `e2e/fixture.ts` 和 `e2e/utils/config.ts` 已生成
3. 验证通过后才进入第四步

> **常见问题**：如果跳过 `tsconfig.json` 生成或 `npm install`，所有 `.spec.ts` 文件会报 48+ 个 TypeScript 错误（找不到模块 `./fixture`、绑定元素隐式具有 `any` 类型等）。

### 第四步：输出完成提示

```
项目初始化完成！

UI 自动化项目已创建: {PROJECT_DIR}
依赖已自动安装（npm install + playwright install chromium）
TypeScript 配置已生成（tsconfig.json）

后续步骤：
1. 进入项目目录
   cd {PROJECT_DIR}

2. 执行登录设置（手动登录模式）
   npm run test:auth
   在浏览器中手动登录，完成后在 Playwright Inspector 中点击 Resume

3. 运行全量测试（推荐方式）
   npm run test:runner

4. 查看测试报告
   npm run report                                   # Playwright 报告（含 trace/video）
   打开 test-report/ 目录下的 HTML 文件              # 自定义统计报告

5. 编写你的第一个测试用例
   文件命名：e2e/{功能模块}.spec.ts
   在 e2e/run-all-tests.spec.ts 的 testScripts 数组中注册新脚本路径

常用命令（需先 cd {PROJECT_DIR}）：
  npm run test:runner                                # 通过 runner 运行全部测试
  npm run test:auth                                  # 手动登录保存状态
  npx playwright test e2e/example.spec.ts            # 运行单个测试
  npx playwright test --ui                           # 可视化 UI 模式
  npm run report                                     # 查看 Playwright HTML 报告

测试报告说明：
  - playwright-report/   Playwright HTML 报告，包含 trace viewer、视频录制、截图
  - test-report/         自定义报告，包含图表统计、通过率、耗时分析
  - midscene_run/report/ Midscene AI 操作报告

注意：
  - 所有命令需在 {PROJECT_DIR} 目录下执行（先 cd {PROJECT_DIR}）
  - .env 文件包含 API Key，已被 .gitignore 排除，请勿手动提交
  - 登录状态保存在 e2e/.auth/state.json，也被排除
  - 登录态过期后需重新运行 npm run test:auth
  - 项目拥有独立的 node_modules，不与主项目依赖冲突
```

## 注意事项

- **项目隔离**：UI 自动化项目作为独立子目录（默认 `ui-automation/`），拥有自己的 `package.json`、`tsconfig.json`、`node_modules`，不与主项目依赖混合
- **所有命令需在项目子目录下执行**：先 `cd {PROJECT_DIR}` 再运行 npm/npx 命令
- 如果目标目录已存在文件，逐一询问是否覆盖，不要静默覆盖
- auth.setup.ts 采用**自动登录模式**，从 `config/environments.json` 读取账号信息自动完成登录；若遇到验证码/SSO 等特殊场景可改为 `page.pause()` 手动登录
- **playwright.config.ts 的 chromium project 不设置 `dependencies: ["setup"]`**，直接复用已保存的 storageState，不会每次运行都触发登录
- run-all-tests.spec.ts 是测试编排入口，通过 playwright-runner.config.ts 运行，不走 setup 流程
- 子进程运行的测试会自动注入 storageState 使用已保存的登录态
- 全量录制（trace/screenshot/video）默认开启，报告中可查看完整测试过程
- 对于企业内网应用，提示用户可能需要配置 VPN 或代理

---

## 工作流 B：测试用例文档 → UI 自动化脚本

当用户提供测试用例文档（Markdown 格式），要求转换为 Playwright + Midscene 自动化脚本时执行此流程。

---

### ⚠️ 强制约束：必须使用 Midscene 自然语言 API

生成的脚本中，**所有元素定位、操作和断言必须使用 Midscene AI 自然语言 API**，以自然语言描述目标元素和预期结果。

#### ✅ 允许使用的 API

| API | 用途 | 示例 |
|-----|------|------|
| `ai(prompt)` / `aiAct(prompt)` | 复合操作（自动规划步骤） | `await ai('在搜索框输入"hello"，点击搜索按钮')` |
| `aiTap(locate)` | 点击元素 | `await aiTap('页面右上角的登录按钮')` |
| `aiInput(locate, { value })` | 输入文本 | `await aiInput('邮箱输入框', { value: 'test@example.com' })` |
| `aiHover(locate)` | 悬停元素 | `await aiHover('导航栏的"产品"菜单项')` |
| `aiScroll(locate, opts)` | 滚动页面 | `await aiScroll(undefined, { scrollType: 'scrollToBottom' })` |
| `aiKeyboardPress(locate, { keyName })` | 键盘按键 | `await aiKeyboardPress('搜索输入框', { keyName: 'Enter' })` |
| `aiAssert(assertion, errorMsg?)` | 自然语言断言 | `await aiAssert('页面展示"单词跟读练习"卡片', '未找到卡片')` |
| `aiQuery(dataDemand)` | 提取结构化数据后用 `expect` 精确断言 | `const d = await aiQuery('{ score: string }，平均分数值'); expect(d.score).toMatch(/^\d+/)` |
| `aiBoolean(prompt)` | 提取布尔值后用 `expect` 断言 | `const v = await aiBoolean('是否存在"开始练习"按钮'); expect(v).toBe(false)` |
| `aiString(prompt)` | 提取字符串 | `await aiString('当前页面主标题文字')` |
| `aiNumber(prompt)` | 提取数字 | `await aiNumber('练习进度卡中已完成次数')` |
| `aiWaitFor(assertion)` | 等待条件成立 | `await aiWaitFor('搜索结果列表已加载完成')` |
| `recordToReport(title)` | 截图记录到报告 | `await recordToReport('点击前 - 课程详情页')` |

> `page.goto(url)`、`page.waitForLoadState()`、`page.waitForURL()`、`page.reload()` 等 Playwright 原生**导航/等待**方法允许使用，但仅限于页面级操作，不用于元素定位。

#### ❌ 严禁使用的写法

以下写法**一律禁止**，出现即视为脚本不合格：

```typescript
// ❌ CSS 选择器定位
page.locator('.card-title')
page.locator('button[type="submit"]')
page.locator('div.rounded-xl')

// ❌ XPath 定位
page.locator('//button[text()="开始练习"]')

// ❌ Playwright 原生语义定位
page.getByText('开始练习')
page.getByRole('button', { name: '提交' })
page.getByTestId('submit-btn')
page.getByLabel('用户名')
page.getByPlaceholder('请输入')

// ❌ Playwright 原生断言（对 locator 的断言）
await expect(page.locator('.card')).toBeVisible()
await expect(page.locator('h1')).toHaveText('标题')
await expect(page.locator('input')).toHaveValue('xxx')

// ❌ 直接操作 DOM
page.evaluate(() => document.querySelector('.btn').click())
```

#### ✅ 正确写法对照

```typescript
// ✅ 点击：自然语言描述元素
await aiTap('口语练习卡片底部的"开始练习"按钮（紫色渐变背景）')

// ✅ 断言元素可见：自然语言描述
await aiAssert('页面右侧展示"单词跟读练习"卡片，包含麦克风图标', '未找到卡片')

// ✅ 断言元素不可见：aiBoolean + expect
const visible = await aiBoolean('页面中是否存在包含"开始练习"按钮的口语练习卡片')
expect(visible).toBe(false)

// ✅ 验证文字内容：aiQuery + expect（比 aiAssert 更可靠，避免 AI 幻觉）
const data = await aiQuery('{ progress: string }，练习进度卡中的数值文字')
expect(data.progress).toMatch(/^\d+/)

// ✅ 验证页面跳转：waitForURL（导航）+ aiAssert（内容）
await page.waitForURL(/\/speaking\//, { timeout: 10000 })
await aiAssert('当前页面是跟读练习页面，顶部导航包含"单词跟读"文字')
```

---

### 第一步：读取测试用例文档

读取用户指定的测试用例 Markdown 文件，解析以下信息：
- 功能模块名称（用于命名 spec 文件）
- 每条用例的：用例编号（如 FR-001）、优先级（P0/P1）、测试步骤、预期结果

### 第二步：确定输出路径

> **强制规则**：所有由工作流 B 生成的脚本及相关文件，必须统一输出到 `ui-automation/` 目录下，不得放在项目根目录或其他位置。

- **项目根目录**固定为 `ui-automation/`（与工作流 A 保持一致）
- spec 文件输出到 `ui-automation/e2e/{功能模块}.spec.ts`
  - 文件名取自文档标题或文件名，转为小写连字符格式
  - 例：`口语练习入口模块-测试用例-01.md` → `ui-automation/e2e/oral-practice-entry.spec.ts`
- 同步更新 `ui-automation/config/environments.json`，补充测试中涉及的页面 URL 占位符
- 如果 `ui-automation/` 目录不存在或缺少必要文件，先执行工作流 C 补全项目结构，再生成 spec 文件

### 第三步：生成 spec 文件

#### 文件结构规范

```typescript
import { test } from './fixture';
import { configManager } from './utils/config';

/**
 * 前置条件：所有测试通过 auth.setup.ts 完成登录，storageState 自动注入。
 * 特殊场景（未登录、切换账号）在用例内部单独处理。
 *
 * 断言策略：使用 soft assertion 模式，所有 aiAssert 都会执行，
 * 失败的断言收集后在用例末尾统一抛出。
 */

/** 包装 aiAssert 为 soft 模式：失败只记录不中断，最后统一报告 */
async function softAssertAll(
  aiAssert: (...args: any[]) => Promise<any>,
  assertions: string[],
): Promise<void> {
  const failures: string[] = [];
  for (const assertion of assertions) {
    try {
      await aiAssert(assertion);
    } catch (e: any) {
      failures.push(`[FAIL] ${assertion}\n   -> ${e.message || e}`);
    }
  }
  if (failures.length > 0) {
    throw new Error(
      `${failures.length}/${assertions.length} assertions failed:\n\n${failures.join('\n\n')}`
    );
  }
}

// 按文档章节划分 test.describe 块
test.describe('章节名称', () => {

  // 登录通过 storageState 全局注入，不在每个 test 里重复登录
  // 特殊场景（未登录/切换账号）在用例内部单独处理

  test('TC-01 [FR-XXX][P0] 用例标题', async ({ ai, aiAssert, page }) => {
    const { pages } = configManager.getConfig();
    try {
      await page.goto(pages.xxx);
      await page.waitForLoadState('networkidle');
      await ai('操作描述');
      await page.waitForLoadState('networkidle');
      // 多个断言使用 softAssertAll，确保所有断言都执行
      await softAssertAll(aiAssert, [
        '预期结果描述1',
        '预期结果描述2',
      ]);
    } catch (error) {
      await page.screenshot({ path: `test-screenshots/TC-01-${Date.now()}.png`, fullPage: true });
      throw error;
    }
  });

  // 特殊场景：需要清除登录态
  test('TC-02 [FR-XXX][P0] 未登录用户场景', async ({ ai, aiAssert, page }) => {
    const { pages } = configManager.getConfig();
    try {
      await page.context().clearCookies();
      await page.evaluate(() => localStorage.clear());
      await page.goto(pages.xxx);
      await page.waitForLoadState('networkidle');
      await aiAssert('页面已重定向到登录页面');
    } catch (error) {
      await page.screenshot({ path: `test-screenshots/TC-02-${Date.now()}.png`, fullPage: true });
      throw error;
    }
  });
});
```

#### 转换规则

| 测试用例内容 | 转换方式 |
|---|---|
| 点击/输入/选择等操作步骤 | `await ai('自然语言描述操作')` 或 `await aiTap('自然语言描述元素')` |
| 输入文本 | `await aiInput('输入框描述', { value: '内容' })` |
| 单个断言 | `await aiAssert('自然语言描述预期')` |
| 同一用例多个断言 | `await softAssertAll(aiAssert, ['断言1', '断言2', ...])` |
| 验证元素不可见（权限控制） | `const v = await aiBoolean('是否存在...'); expect(v).toBe(false)` |
| 验证文字/数值内容（精确） | `const d = await aiQuery('{ field: type }，描述'); expect(d.field).toMatch(...)` |
| 验证页面跳转 | `await page.waitForURL(/pattern/)` + `await aiAssert('页面内容描述')` |
| 页面跳转后等待 | `await page.waitForLoadState('networkidle')` |
| 等待某内容出现 | `await aiWaitFor('条件描述')` |
| 需要管理员后台操作的步骤 | 保留为注释 `// TODO: await adminApi.xxx()` |
| 需要清除登录态 | `await page.context().clearCookies(); await page.evaluate(() => localStorage.clear())` |
| 页面刷新 | `await page.reload(); await page.waitForLoadState('networkidle')` |
| 需要切换账号 | 先清除登录态，再 `await page.goto(auth.loginUrl)` + `await ai('使用账号xxx登录')` |

> **重要**：禁止在转换规则中使用 CSS 选择器、XPath、`page.locator()`、`getByText()`、`getByRole()` 等 Playwright 原生定位方式。所有元素定位必须通过自然语言描述传给 Midscene API。

#### 用例编号规则

- 每个 `test()` 标题以 `TC-XX` 开头（两位数字，从 01 开始，全文件连续编号）
- 格式：`TC-01 [FR-XXX][P0] 用例标题`
- 编号不带方括号，`TC-01` 而非 `[TC-01]`
- 截图文件名与编号对应：`TC-01-${Date.now()}.png`

#### 登录前置条件规则

- **默认**：登录通过 `playwright.config.ts` 的 `storageState` 全局注入，test 内不写登录代码
- **例外场景**（需在用例内部单独处理）：
  - 测试未登录行为：先 `clearCookies()` + `localStorage.clear()`
  - 测试不同角色账号：先清除登录态，再用目标账号重新登录
  - 测试登录流程本身

#### 断言策略规则

- 单个断言直接用 `await aiAssert('...')`
- 同一用例有 2 个及以上断言，统一用 `await softAssertAll(aiAssert, [...])`
- `softAssertAll` 保证所有断言都执行，失败时统一报告哪些通过、哪些失败

#### 用例分组规则

- 文档的二级标题（`##`）→ 顶层 `test.describe`
- 三级/四级标题（`###`/`####`）→ 嵌套 `test.describe`
- 每个用例条目 → 一个 `test()`
- 不使用 `beforeEach` 做页面导航，每个 test 内部自行 `page.goto()`

#### 只声明用到的 fixture 参数

- 有操作步骤才声明 `ai`
- 有断言才声明 `aiAssert`
- 有输入才声明 `aiInput`
- 避免声明后未使用导致 lint 警告

### 第四步：更新 environments.json

分析 spec 文件中所有 `pages.xxx` 引用，在 `config/environments.json` 的 `pages` 对象中补充对应的 URL 占位符：

```json
{
  "test": {
    "auth": { ... },
    "pages": {
      "home": "https://your-app.test",
      "courseDetail": "https://your-app.test/course/{courseId}",
      "courseDetailNoPractice": "https://your-app.test/course/{courseIdNoPractice}",
      "...": "根据用例涉及的页面按需添加"
    }
  }
}
```

### 第五步：注册到 run-all-tests.spec.ts

5a. 检查 `ui-automation/e2e/run-all-tests.spec.ts` 是否存在：
- **不存在**：从 `assets/templates/run-all-tests.spec.ts` 复制创建到 `ui-automation/e2e/`，然后将新 spec 路径写入 `testScripts` 数组
- **已存在**：直接将新 spec 路径追加到 `testScripts` 数组

5b. `testScripts` 数组格式：

```typescript
testScripts: [
  'e2e/word-reading-01-entry.spec.ts',   // ← 每个 spec 文件一行
  'e2e/word-reading-02-prepare.spec.ts', // ← 新增时追加
],
```

5c. 同时确认 `ui-automation/playwright-runner.config.ts` 存在，不存在则从模板复制。

### 第六步：输出完成提示

```
测试脚本生成完成！

生成文件：
  ui-automation/e2e/{功能模块}.spec.ts          （共 N 个测试用例）
  ui-automation/config/environments.json         （已补充页面 URL 占位符）

已注册到 ui-automation/e2e/run-all-tests.spec.ts 的 testScripts 数组。

运行方式（需先 cd ui-automation）：
  全量运行：npx playwright test --config=playwright-runner.config.ts
  单文件调试：npx playwright test e2e/{功能模块}.spec.ts --project=chromium

后续操作：
1. 将 ui-automation/config/environments.json 中的 URL 占位符替换为实际测试环境地址
2. 标注 ⚠️ 的用例需配合账号切换或后台数据准备
3. 运行测试前先完成登录：cd ui-automation && npm run test:auth
```

> **脚本质量自检**：输出前逐条确认以下内容，任一不符则修正后再输出：
> - [ ] 所有元素定位均使用自然语言描述，无 CSS 选择器 / XPath / `page.locator()` / `getByText()` / `getByRole()`
> - [ ] 所有断言均使用 `aiAssert` / `aiBoolean` + `expect` / `aiQuery` + `expect`，无 `expect(locator).toBeVisible()` 等 Playwright 原生断言
> - [ ] 每个测试用例有 `recordToReport` 截图记录
> - [ ] 测试用例标题包含需求 ID 和优先级（如 `[FR-001][P0]`）

---

## 工作流 C：补全项目缺失文件

当用户说"项目缺少文件"、"补全项目文件"，或项目目录下缺少必要文件时执行此流程。

### 第一步：检查现有文件

使用 `listDirectory` 扫描 `ui-automation/` 目录，与完整文件清单对比，确定缺失项：

```
必须存在的文件清单：
  package.json
  tsconfig.json
  playwright.config.ts
  playwright-runner.config.ts
  .env.example
  .gitignore
  config/environments.json
  e2e/fixture.ts
  e2e/utils/config.ts
  e2e/auth.setup.ts
  e2e/run-all-tests.spec.ts
```

### 第二步：批量创建缺失文件

对每个缺失文件，从对应模板路径复制内容并创建：

| 缺失文件 | 模板来源 |
|---|---|
| `package.json` | `assets/templates/package.json`，`{{PROJECT_NAME}}` 替换为目录名 |
| `tsconfig.json` | `assets/templates/tsconfig.json` |
| `playwright.config.ts` | `assets/templates/playwright.config.ts` |
| `playwright-runner.config.ts` | `assets/templates/playwright-runner.config.ts` |
| `.env.example` | `assets/templates/.env.example` |
| `.gitignore` | `assets/templates/.gitignore` |
| `config/environments.json` | `assets/templates/environments.json` |
| `e2e/fixture.ts` | `assets/templates/fixture.ts` |
| `e2e/utils/config.ts` | `assets/templates/config.ts` |
| `e2e/auth.setup.ts` | `assets/templates/auth.setup.ts` |
| `e2e/run-all-tests.spec.ts` | `assets/templates/run-all-tests.spec.ts` |

> 已存在的文件不覆盖，除非用户明确要求。

### 第三步：安装依赖

```bash
cd {PROJECT_DIR}
npm install
npx playwright install chromium
```

### 第四步：输出完成提示

列出已创建的文件，并提示后续步骤（同工作流 A 第四步）。
