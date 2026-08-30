# 优化 project-analyze skill：支持多平台项目分析维度

## Context

`plugins/optimus-devops-plugin/skills/project-analyze/SKILL.md`（v2.0.0）目前只有一套 14 章节报告模板，隐含假设"项目 = 前端 + 后端 + 数据库"的 Web 全栈形态（第7章ER图、第8章API接口、第9章前端页面、第13章前端状态管理均针对此形态设计）。

但用户指出实际待分析的项目类型远不止此：H5、Android 原生、iOS 原生、WPF 桌面（本仓库主业务技术栈）、纯后端（Java/Go 等无前端目录）。这些类型在"7/8/9/13"四个插槽章节上的关键信息完全不同——WPF 项目关心 View/ViewModel 绑定与 MVVM 框架而非 ER 图；Android/iOS 关心 Activity/ViewController 清单、权限声明、原生 SDK 依赖而非前端路由表；纯后端项目第9/13章应直接标注"不适用"而非空洞输出。用同一份模板机械套用，会让报告在非 Web 项目上产出大量"猜测"或"空洞"内容，直接违反该 skill 自己"反例与黑名单"表格第1条（禁止猜测数据模型）和第4条（对纯后端项目生成前端章节）的既有约束——即当前模板本身就自相矛盾。

同时经查 `.claude/rules/skill-conventions.md`，该 skill 存在合规缺口：声明了 `compatibility`（依赖 Git）且有文件输出（`doc/project-overview.md`），但没有设置独立的「执行前置校验」Step（依赖/输入/输出/运行条件四类检查）和「需求预告」环节（一次性列出缺失信息统一询问）。本次一并修复。

**调研结论（只读子代理已确认）：**
- `knowledge-base/wpf/rules/02-project-structure.md`（解决方案布局、View↔ViewModel命名配对）、`03-mvvm.md`（MVVM框架选型/DI组合根/ICommand/导航）、`17-common-libraries.md`（控件库五维评估）、`06-controls.md`、`07-resources-themes.md`、`15-packaging-deployment.md`，以及 `csharp/01-project-structure.md`、`csharp/10-dependency-management.md`、`dotnet/reference/windows-dotnet-support-matrix.md` 可直接作为 WPF 分析维度的判断依据引用，不重写规范本体，只在 SKILL.md 中点名引用路径。
- 仓库内**无**Android/iOS 项目分析先例，本次是首次涉及移动端原生维度，需要自行设计判断信号（无既有 skill 可对齐）。
- `test-prompts.json` 现有 3 例全部基于"Web/monorepo"假设，需新增覆盖 WPF/移动端/纯后端场景的用例。
- 版本号真源：`.claude-plugin/marketplace.json` 顶层 `version` 当前为 `12.3.1`；`plugins/optimus-devops-plugin/.codex-plugin/plugin.json` 当前为 `12.1.8`（已存在的历史漂移，本次顺带同步）。

## 设计方案：保持14章节编号不变，插槽章节内容按"平台画像"适配

**关键决策：不重新设计章节结构，只让第 7/8/9/13 章的内容规格随检测到的平台类型切换。** 理由：
1. 14 章节编号被"分析深度控制""迭代优化规则""质量检查"三处表格反复引用，重新编号会导致大量连带修改，且丧失既有用户对报告结构的心智模型。
2. 真正因平台而异的只有这 4 个插槽（数据模型/接口/UI/状态管理），其余 10 章（概况/业务上下文/功能清单/技术栈/架构/目录结构/部署/依赖/上手路径/风险评估）是平台无关的通用维度，本就该保持稳定。

### 新增机制：平台画像识别 + 章节适配矩阵

在"第二步：快速扫描"的第一轮目录扫描后，插入**平台画像判定**子步骤，基于文件系统信号给出五选一分类：

| 画像 | 判定信号（任一命中即可，按优先级取第一个匹配） |
|---|---|
| **WPF/桌面** | `*.csproj` 含 `<UseWPF>true</UseWPF>`，或存在 `App.xaml` + `*.xaml` 文件 |
| **Android** | 存在 `AndroidManifest.xml` 或 `build.gradle(.kts)` + `src/main/java\|kotlin` |
| **iOS** | 存在 `*.xcodeproj`/`*.xcworkspace`，或 `Podfile`/`Package.swift` + `*.swift`/`*.m` |
| **纯后端** | 存在后端框架特征（`pom.xml`/`go.mod`/Django-Flask 等）且**不存在**前端目录（`src/`下无 `views`/`pages`/`components`，无 `package.json` 的前端依赖特征） |
| **Web/H5（默认）** | 前后端信号皆有，或无法命中以上任一画像时的兜底默认 |

判定结果驱动第 7/8/9/13 章内容规格，编号和章节标题不变，但每章标题旁标注适用画像；不适用的画像下该章节内容为"不适用（{画像}项目）"（对齐现有反例表第4条）。

**四个插槽章节的平台适配矩阵**（新增到 SKILL.md"输出"章节下）：

| 章节 | Web/H5（默认，现状不变） | WPF/桌面 | Android/iOS | 纯后端 |
|---|---|---|---|---|
| 7. 数据模型 | ER 关系图（现有逻辑不变） | 若有本地DB/ORM则同现有逻辑；否则标注"不适用，桌面项目无持久层" | 本地存储模型（Room/CoreData实体，若有） | 同现有逻辑（后端本来就是ER图的主场景） |
| 8. API 接口 | 端点清单（现有逻辑不变） | 若调用后端API则列出调用清单（从HttpClient/Refit等封装提取）；否则"不适用" | 网络层封装 + 关键API调用清单（从Retrofit/Alamofire等提取） | 同现有逻辑 |
| 9. 前端页面 | 路由表（现有逻辑不变） | **替换为**：View/ViewModel 清单及绑定关系（View↔ViewModel一一配对表，引用 `knowledge-base/wpf/rules/02-project-structure.md` 命名规范判定） | **替换为**：页面清单（Activity/Fragment 或 ViewController/Scene）+ 权限声明清单 + 构建变体(flavor/scheme) | "不适用（纯后端项目）" |
| 13. 状态管理 | 数据流分析（现有逻辑不变） | **替换为**：MVVM框架识别（Prism/CommunityToolkit.Mvvm/原生，引用 `knowledge-base/wpf/rules/03-mvvm.md`）+ DI容器 + 控件库（引用 `17-common-libraries.md`） | **替换为**：本地存储与状态管理（SharedPreferences/UserDefaults等） | "不适用（纯后端项目）" |

第 5.1 节"架构模式"枚举也需补充："桌面单体（MVVM）"、"移动端原生"两个取值，与现有"单体/微服务/前后端分离/BFF"并列。

### 新增：Step 1 执行前置校验 + Step 0 需求预告

按 `.claude/rules/skill-conventions.md` 硬性要求补齐：

**Step 0（需求预告，写在"工作流程"之前）**：对比用户触发语句中是否已提供 (a) 仓库地址或本地路径【必需】(b) 关注重点【可选】。仅路径缺失时一次性询问，不逐步反应式追问。依赖检查项（Git 是否可用）不参与本环节判断。

**Step 1（原"第一步：获取项目源码"扩展为前置校验+获取源码）**：
1. 依赖检查：`git --version` 确认可用（compatibility 声明的依赖）
2. 输入参数检查：本地路径存在性 / URL 格式合法性
3. 输出参数检查：`doc/` 父目录（仓库根）存在且可写
4. 运行条件检查（可协商风险）：平台画像识别——若信号冲突或全部未命中（低置信度），🔴 CHECKPOINT 显式询问用户确认项目类型，而非报错终止（因为技术上仍可按 Web/H5 默认继续，只是章节内容可能不够精准）

原有"项目确认"CHECKPOINT 合并到此处，展示内容新增"识别到的平台画像"一项。

### frontmatter 更新

- `description`：补充"H5、Android、iOS、WPF桌面、纯后端"覆盖范围说明，帮助触发匹配
- `metadata.version`：`2.0.0` → `2.1.0`（Minor，新增平台适配能力+新增前置校验/需求预告章节）
- `compatibility` 不变（仍是 Git 依赖）

### test-prompts.json 新增用例

新增 3 例覆盖此前空白：
1. WPF 桌面项目分析（触发词示例："分析一下这个WPF桌面应用的项目结构"），期望：第9/13章替换为View/ViewModel清单和MVVM框架分析，第7/8章视是否有后端调用而定
2. Android 原生项目分析，期望：识别为Android画像，第9章输出Activity清单+权限声明，第13章"不适用"
3. 纯后端 Java 项目分析（无前端目录），期望：第9/13章标注"不适用（纯后端项目）"，其余12章正常输出

保留现有3例不变（它们仍是有效的 Web/monorepo 场景回归用例）。

### CHANGELOG.md 新增条目

```markdown
## [2.1.0] - 2026-08-30

### Added
- 新增平台画像识别机制：WPF/桌面、Android、iOS、纯后端、Web/H5（默认）五选一判定
- 第7/8/9/13章新增"平台章节适配矩阵"，插槽内容随画像切换，编号与标题保持稳定
- 新增 Step 0 需求预告环节，一次性列出缺失信息统一询问
- 新增 Step 1 执行前置校验（依赖/输入/输出/运行条件四类检查），运行条件检查（画像识别置信度低）按可协商风险处理，CHECKPOINT确认而非报错终止
- test-prompts.json 新增 WPF/Android/纯后端三例场景

### Changed
- frontmatter description 补充多平台覆盖范围说明
- 第5.1节"架构模式"枚举补充"桌面单体(MVVM)"、"移动端原生"
- 原"项目确认"CHECKPOINT 合并进 Step 1，新增展示"识别到的平台画像"
```

### 仓库级版本同步

- `.claude-plugin/marketplace.json` 顶层 `version`：`12.3.1` → `12.3.2`（Patch，plugins/下更新已有skill）
- `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` 的 `version`：同步改为 `12.3.2`（顺带修正与marketplace.json的历史漂移 12.1.8）

## 执行步骤

1. 编辑 `SKILL.md`：
   - frontmatter：`description` 扩写、`metadata.version` 改 `2.1.0`
   - "概述"段落补一句多平台覆盖范围说明
   - 新增"Step 0 需求预告"小节（插在"输入"表格后，"输出"表格前）
   - "输出"章节下新增"平台画像判定"表格 + "平台章节适配矩阵"表格
   - "第一步：获取项目源码"标题改为"第一步：前置校验与获取项目源码"，插入四类检查逻辑，CHECKPOINT内容扩充
   - 报告模板中第7/8/9/13章标题旁加画像适用范围注释（如 `## 9. 前端页面（Web/H5）/ View与ViewModel清单（WPF）/ 页面与权限清单（Android/iOS）`），章节内表格结构按画像分别给出
   - 第5.1节架构模式枚举补充两个取值
   - "反例与黑名单"表格视需要补充一条：不要对已识别为非Web画像的项目强行套用Web模板插槽
   - "质量检查"清单补充一条：平台画像识别结果已在报告开头注明
2. 编辑 `CHANGELOG.md`：追加 `[2.1.0]` 条目（内容见上）
3. 编辑 `test-prompts.json`：追加 3 个新用例（id 4/5/6）
4. 编辑 `.claude-plugin/marketplace.json`：顶层 `version` `12.3.1` → `12.3.2`
5. 编辑 `plugins/optimus-devops-plugin/.codex-plugin/plugin.json`：`version` → `12.3.2`
6. 全部编辑遵循用户全局规则"长内容分段写入"——SKILL.md 改动分多次 Edit 完成，不一次性大段替换

## 验证

- `git diff` 检查每个文件改动是否只涉及语义内容，无格式化噪音（编辑铁律）
- 人工核对新增的"平台章节适配矩阵"表格与四个已知 knowledge-base WPF 规范文件路径引用是否准确（文件路径真实存在）
- 核对 `metadata.version`（skill内）与 `marketplace.json`/`plugin.json`（仓库级）两套版本号升级逻辑不混淆——前者Minor因为skill本身新增能力，后者Patch因为是"更新已有skill"而非"新增skill"
- 建议：若 darwin-skill 可用，对改动前后的 project-analyze 评分，确保新分数不低于改动前（AGENTS.md建议项，非阻塞）

## 执行结果

计划已获批准并全部落地实施：

- `plugins/optimus-devops-plugin/skills/project-analyze/SKILL.md`：完成上述全部改动，`metadata.version` → `2.1.0`
- `plugins/optimus-devops-plugin/skills/project-analyze/CHANGELOG.md`：已追加 `[2.1.0]` 条目
- `plugins/optimus-devops-plugin/skills/project-analyze/test-prompts.json`：已追加 id 4/5/6 三个用例
- `.claude-plugin/marketplace.json` 顶层 `version`：`12.3.1` → `12.3.2`
- `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` `version`：`12.1.8` → `12.3.2`（同步版本号，修正历史漂移）

`git diff` 核查确认所有改动均为语义相关内容，无格式化噪音。
