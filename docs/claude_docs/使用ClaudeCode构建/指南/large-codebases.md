# 在 monorepo 或大型代码库中设置 Claude Code

> 为 monorepo 和大型单代码树配置 Claude Code，使用嵌套 CLAUDE.md 文件、稀疏工作树、代码智能和按包加载的 skills，让 Claude 专注于你正在处理的代码。

大型代码库可以是拥有数百万行代码的单一仓库，也可以是包含多个包的 monorepo。Claude Code 可以在任何规模下工作，但随着代码库增长，为小型项目调优的默认设置可能会用与任务无关的指令和文件读取填满上下文窗口，消耗 token 并降低 Claude 的性能。

本指南向个人开发者和工程团队展示如何将 Claude 的作用范围限定到任务涉及的代码部分。每个章节都会说明某个设置是个人本地的还是提交到仓库的。

## 本指南涵盖的内容

[下方表格](#本页设置)列出了每项设置及其作用。[其后的文件树](#示例-monorepo)是本页每个代码示例所引用的示例 monorepo。

### 本页设置

以下每项设置都是独立的。它们是分层叠加的而非相互替代，所以只需应用适合你仓库的那些。[选择从哪里启动 Claude](#选择从哪里启动-claude)决定了你的设置文件存放位置，所以请先阅读它。[整合配置](#整合配置)展示了所有设置的组合。

| 我想要 | 使用 |
| :--- | :--- |
| 只加载你接触的代码的约定，而非一个覆盖所有子系统的根文件 | 按目录分层的 [CLAUDE.md 文件](#按目录分层-claude-md-文件) |
| 排除你从不工作的包的 CLAUDE.md 文件 | [`claudeMdExcludes`](#排除无关的-claude-md-文件) |
| 阻止 Claude 打开构建输出、生成代码和供应商依赖 | `permissions.deny` 中的 [`Read` 拒绝规则](#阻止读取生成代码和供应商代码) |
| 通过语言服务器查找符号的定义或调用者，而非扫描文件 | [代码智能插件](#通过代码智能减少文件读取) |
| 当 Claude 创建工作树时只检出任务需要的目录 | [`worktree.sparsePaths`](#只检出你需要的目录) |
| 从同一会话中读取和编辑兄弟包或另一个仓库 | [`--add-dir`](#跨包或跨仓库授权访问) 或 `additionalDirectories` |
| 给 Claude 特定于某个区域的过程，只在相关时加载 | 按目录的 [skills](#添加按目录的-skills) |
| 用一套大家安装的约定替代多个按目录的 CLAUDE.md 文件 | 内部 marketplace 中的 [插件](#当分层停止扩展时集中管理约定) |

> **提示**：关于在任何仓库中保持上下文小巧的工作流技术（如[在子 agent 中运行探索](https://code.claude.com/docs/en/best-practices#use-subagents-for-investigation)以使文件读取不进入主对话），请参阅 [Claude Code 最佳实践](https://code.claude.com/docs/en/best-practices)。要为组织中的每位开发者推出基线配置，请参阅[为组织设置 Claude Code](https://code.claude.com/docs/en/admin-setup)。

### 示例 monorepo

本页的示例引用了一个包含三个包的 monorepo。相同的模式适用于大型单代码树：示例使用 `packages/api/` 的地方，替换为你自己的子系统目录如 `src/backend/` 或 `lib/core/`。

```text
monorepo/
  CLAUDE.md                     # 根指令
  packages/
    api/
      CLAUDE.md                 # API 特定指令
      .claude/skills/
      src/
    web/
      CLAUDE.md                 # 前端特定指令
      .claude/skills/
      src/
    shared/
      CLAUDE.md                 # 共享库指令
      src/
```

## 选择从哪里启动 Claude

你启动 `claude` 的位置决定了哪些文件无需额外授权即可读取和编辑，哪些 CLAUDE.md 文件在启动时加载到上下文中，以及哪些项目设置生效。

| 从哪里启动 | 文件访问权限 | 启动时加载的 CLAUDE.md | 适用场景 |
| :--- | :--- | :--- | :--- |
| 仓库根目录 | 所有文件 | 仅根目录的；子目录文件在 Claude 读取时按需加载 | 任务跨越多个包或子系统 |
| 子目录 | 仅该子树，直到你授权更多 | 该目录的加上每个祖先目录的 | 工作限定在一个包或子系统内 |

`.claude/settings.json` 中的项目设置仅从你的启动目录加载，不会像 CLAUDE.md 文件那样从父目录继承：仓库根目录的 `.claude/settings.json` 仅在从根目录启动时生效。

以下每节都会说明其设置文件属于仓库根目录还是你启动的子目录，以及是提交的还是本地保留的。

## 按目录分层 CLAUDE.md 文件

在大型代码库中，仓库根目录的单个 CLAUDE.md 往往会膨胀到覆盖每个子系统的约定，消耗与当前任务无关的指令上下文，或者保持太通用而没有用处。将指令分散到按目录的文件中意味着 Claude 加载仓库范围的规则加上你正在处理的代码的约定。

Claude Code 在启动时加载你工作目录和每个父目录中的每个 [CLAUDE.md](https://code.claude.com/docs/en/memory) 文件，然后在读取子目录中的文件时按需加载该子目录的文件。根文件设置仓库范围的规则，每个子目录添加自己的规则。

常见的分层是两级：

* **根 `CLAUDE.md`**：适用于所有地方的指令，如编码标准、提交约定和仓库布局
* **按子目录的 `CLAUDE.md`**：特定于该区域技术栈的约定。在 monorepo 中每个包一个。在大型单代码树中每个子系统一个，如 `src/db/` 或 `src/api/`

将这些文件提交到仓库，以便队友继承它们。每个目录的所有者通常维护其文件。

根 `CLAUDE.md` 让 Claude 了解仓库结构：

```markdown CLAUDE.md
这是一个包含三个包的 monorepo，位于 packages/ 下：

- packages/api：使用 Express、TypeScript 和 PostgreSQL 的 Node.js REST API
- packages/web：使用 Vite、TypeScript 和 TailwindCSS 的 React 前端
- packages/shared：api 和 web 共用的 TypeScript 工具库

从包目录运行命令，而不是从 monorepo 根目录。
每个包有自己的 tsconfig.json、package.json 和测试套件。
```

每个子目录的 `CLAUDE.md`（这里是 `packages/api/CLAUDE.md`）添加特定于该区域技术栈的上下文：

```markdown packages/api/CLAUDE.md
此包是 REST API 服务器。

- 运行测试：`npm test`（使用 Vitest）
- 运行开发服务器：`npm run dev`（端口 3001）
- 数据库迁移：`npm run migrate`
- 环境变量：复制 `.env.example` 为 `.env`

API 路由在 src/routes/ 中。每个路由文件导出一个 Express 路由器。
数据库查询在 src/db/ 中使用 Knex。永远不要在路由处理程序中编写原始 SQL 字符串。
```

当你从 `packages/api/` 启动 Claude 时，它会加载 `packages/api/CLAUDE.md` 和根 `CLAUDE.md`。Claude 看到本地指令和仓库范围的规则，上下文中没有来自 `packages/web/` 的指令。这同样适用于非 monorepo 树中的任何子目录。

保持文件与代码库和模型同步的几种方法：

* **在 pull request 中审查**：将 CLAUDE.md 编辑视为任何其他文档变更，使约定与代码保持同步
* **在重大模型发布后重新审视**：针对旧模型限制的指令在新模型自行处理该情况后可能变成开销。例如，强制单文件重构的规则在限制消失后可以删除
* **添加一个 Stop hook 来提议更新**：[`Stop` hook](https://code.claude.com/docs/en/hooks#stop) 在 Claude 完成响应时接收会话记录的路径，因此脚本可以在会话审查后提议 CLAUDE.md 更新，趁差距还新鲜

有关 CLAUDE.md 文件如何加载和交互的更多信息，请参阅[记忆和项目指令](https://code.claude.com/docs/en/memory)。

### 选择按目录 CLAUDE.md 还是路径范围规则

按目录的 `CLAUDE.md` 文件和 `.claude/rules/` 下的[路径范围规则](https://code.claude.com/docs/en/memory#path-specific-rules)都可以将指令定向到树的某个部分。它们在文件位置和加载时机上有所不同。

| 方法 | 文件位置 | 何时加载 | 适用场景 |
| :--- | :--- | :--- | :--- |
| 按目录 `CLAUDE.md` | 目录内，与其代码并列 | 从该目录启动时在启动时加载，或在 Claude 读取该目录文件时按需加载 | 目录所有者维护自己的约定；指令与代码一起版本化 |
| `.claude/rules/` 中的路径范围规则 | 仓库根目录的中央 `.claude/` | 当 Claude 处理匹配规则 `paths:` glob 的文件时 | 你想将所有约定放在一个地方，或同一规则适用于多个分散路径 |

有关包含 skills 的比较，请参阅[比较类似功能](https://code.claude.com/docs/en/features-overview#compare-similar-features)。

### 排除无关的 CLAUDE.md 文件

当你从仓库根目录启动 Claude 时，每个子目录的 CLAUDE.md 会在 Claude 读取该目录中的文件时加载。`claudeMdExcludes` 设置通过路径或 glob 模式跳过特定文件，使它们永不加载。

将其用于你从不工作的目录，如其他团队的包、遗留代码或供应商子树。排除列表是静态的，不是按任务切换的。要今天专注于一个包，明天专注于另一个包，[从该包的目录启动 Claude](#选择从哪里启动-claude) 而不是编辑排除项。

如果你只想对自己应用这些排除项，请将设置放在 `.claude/settings.local.json` 中。Claude Code 在创建该文件时会将其加入 gitignore；由于你这里是手动创建的，请将其添加到你的 gitignore 中。模式使用 glob 语法匹配绝对文件路径，所以以 `**/` 开头的相对风格模式可以匹配树中的任何位置。以下示例排除了其他团队拥有的包：

```json .claude/settings.local.json
{
  "claudeMdExcludes": [
    "**/packages/admin-dashboard/**",
    "**/packages/legacy-*/**"
  ]
}
```

这会跳过这些包下的每个 CLAUDE.md 和规则文件。根 CLAUDE.md 和你确实工作的包仍然正常加载。

这些模式涵盖其他常见情况：

* `"**/packages/*/CLAUDE.md"`：排除每个包的 CLAUDE.md 同时保留根目录的
* `"**/packages/web/**"`：排除 web 包下的所有内容，包括规则
* `"/home/user/monorepo/legacy/CLAUDE.md"`：通过绝对路径排除一个特定文件

托管策略 CLAUDE.md 文件不能被排除，所以组织范围的指令始终适用。你可以在任何[设置范围](https://code.claude.com/docs/en/settings#configuration-scopes)设置 `claudeMdExcludes`：用户、项目、本地或托管。数组跨范围合并，所以团队可以设置项目级默认值，而个人添加本地覆盖。

有关完整的排除文档，请参阅[排除特定 CLAUDE.md 文件](https://code.claude.com/docs/en/memory#exclude-specific-claude-md-files)。

## 减少 Claude 的读取量

指令只是进入 Claude 上下文的内容的一部分。文件读取是另一项成本，随代码库增长而增加。以下设置阻止读取不相关路径，并用语言服务器查找替代详尽的文件扫描。

### 阻止读取生成代码和供应商代码

Claude 的内容搜索默认尊重 `.gitignore`，所以已列出的路径如 `node_modules/`、`dist/` 和 `build/` 无需额外配置即可排除在搜索结果之外。

对于已检入的路径，如供应商 SDK 或已提交的生成代码，在 `permissions.deny` 中添加 `Read` 拒绝规则，以阻止 Claude 即使在搜索列出时也打开这些文件。

要为仓库中的每个人应用这些排除项，请将它们提交到 `.claude/settings.json`。要保持个人使用，请改用 `.claude/settings.local.json`。像本页的其他项目设置一样，这些文件仅从你的启动目录加载。如果你从仓库根目录启动，请将它们放在那里；如果你从子目录启动，请放在每个包的 `.claude/` 中。要在任何会话中强制执行相同的拒绝规则（无论从哪个目录启动），请在[托管设置](https://code.claude.com/docs/en/settings#settings-files)中设置它们，用户和项目设置无法覆盖托管设置。

以下示例阻止构建产物和供应商 SDK：

```json .claude/settings.json
{
  "permissions": {
    "deny": [
      "Read(./**/dist/**)",
      "Read(./**/build/**)",
      "Read(./**/*.generated.*)",
      "Read(./vendor/**)"
    ]
  }
}
```

拒绝规则覆盖 Claude 的内置文件工具和可识别的 Bash 文件命令（包括 `cat`、`head`、`grep` 和 `find`），当拒绝的路径作为参数传递时生效。它们不会从递归搜索的输出中过滤掉被拒绝的路径，也不覆盖自行打开文件的任意子进程。有关完整的模式语法，请参阅 [Read 和 Edit 权限规则](https://code.claude.com/docs/en/permissions#read-and-edit)。

### 通过代码智能减少文件读取

在大型代码库中，查找符号的定义或使用位置可能需要多次文件读取和 grep 调用。[代码智能插件](https://code.claude.com/docs/en/discover-plugins#code-intelligence)将 Claude 连接到语言服务器，使其能够跳转到定义、查找引用和显示类型错误，而无需扫描整个树。

官方 marketplace 有适用于 TypeScript、Python、Go、Rust 和其他常见语言的插件。以下示例安装 TypeScript 插件：

```shell
/plugin install typescript-lsp@claude-plugins-official
```

要为仓库中的每个人启用插件（而不是自己安装），请将其添加到 [`enabledPlugins` 项目设置](https://code.claude.com/docs/en/settings#plugin-settings)中。

代码智能插件需要每台开发者机器上安装对应语言的语言服务器二进制文件。请参阅[每种语言需要哪个二进制文件](https://code.claude.com/docs/en/discover-plugins#code-intelligence)。从官方 marketplace 安装需要访问 GitHub 的网络，因为 marketplace 托管在那里。在受限网络上，[从内部 Git 主机或本地路径添加 marketplace](https://code.claude.com/docs/en/discover-plugins#add-from-other-git-hosts)。

这与 `claudeMdExcludes` 和上面的 `Read` 拒绝规则配合得很好。前者将不相关内容排除在上下文之外，而代码智能阻止 Claude 阅读剩余内容来定位定义。

## 限定工作树和文件访问

这些设置控制工作树中磁盘上的内容，以及 Claude 在你的起点之外可以读写哪些目录。

### 只检出你需要的目录

`--worktree` 标志在新的 git 工作树中启动会话，使更改与你的主检出隔离。默认情况下它会检出整个仓库。在大型仓库中，`worktree.sparsePaths` 设置使用 git 稀疏检出，只将列出的目录加上根级文件写入磁盘，因此工作树启动更快且占用更少空间。

如果在此目录中工作的每个人都需要相同的路径，请将设置提交到 `.claude/settings.json`。要为自己添加路径，请使用 `.claude/settings.local.json`：列表跨范围合并，因此本地文件可以向提交的列表添加路径但不能移除。以下示例展示了提交的文件：

```json .claude/settings.json
{
  "worktree": {
    "sparsePaths": [
      ".claude",
      "packages/api",
      "packages/shared"
    ]
  }
}
```

当 Claude 创建工作树时，它只检出 `.claude/`、`packages/api/` 和 `packages/shared/`，而不是整个树。`sparsePaths` 中的路径相对于仓库根目录，无论你从哪个子目录启动 Claude。任何目录路径都可以在这里使用，不仅仅是包根目录。

这对[子 agent 工作树隔离](https://code.claude.com/docs/en/worktrees#isolate-subagents-with-worktrees)特别有用。子 agent 是为子任务生成的并行 Claude 实例，每个在工作树中运行的子 agent 获得轻量级检出而不是整个树。会话中的所有工作树共享相同的 `sparsePaths`，所以如果一个子 agent 需要 `packages/api/` 而另一个需要 `packages/web/`，请将两者都列出。

在 `sparsePaths` 中列出目录，而不是单个文件。根级文件如 `package.json`、`tsconfig.base.json` 和锁文件始终与你列出的目录一起检出。根级目录不会，所以如果你想让仓库根目录的 `.claude/settings.json`、`.claude/rules/` 或 `.claude/skills/` 在工作树中可用，请在列表中包含 `.claude`。

要避免在工作树之间复制 `node_modules` 等大型目录，请在同一 `.claude/settings.json` 中将 `sparsePaths` 与 `symlinkDirectories` 配对：

```json .claude/settings.json
{
  "worktree": {
    "sparsePaths": [
      ".claude",
      "packages/api",
      "packages/shared"
    ],
    "symlinkDirectories": [
      "node_modules"
    ]
  }
}
```

这会从每个工作树的 `node_modules/` 创建一个指向主仓库副本的符号链接，而不是在磁盘上复制它。

> **注意**：`sparsePaths` 和 `symlinkDirectories` 设置在创建工作树之前从你的启动目录读取。创建后，会话的工作目录是工作树根目录，而不是你启动的子目录。因此工作树内的项目设置从工作树根目录的 `.claude/settings.json`（仓库根目录文件的检出副本）加载。将你需要的其他设置（如权限规则或 hooks）放在仓库根目录的 `.claude/settings.json` 中。

有关完整的工作树设置参考，请参阅[工作树设置](https://code.claude.com/docs/en/settings#worktree-settings)。

### 跨包或跨仓库授权访问

本节适用于你从子目录启动 Claude 的情况，或任务跨越多个检出的情况。如果你从单一大型树的仓库根目录启动，Claude 已经可以访问每个文件，可以跳过本节。

当你从 `packages/api/` 启动 Claude 时，它可以在该目录内读写文件。如果任务需要跨包更改，如更新 `api` 和 `web` 都导入的共享类型，你需要授权访问兄弟目录。相同的机制授权访问单独检出的仓库。

`.claude/settings.json` 中的 `additionalDirectories` 设置赋予 Claude 访问工作目录之外目录的权限。以下示例授权访问两个兄弟包：

```json .claude/settings.json
{
  "permissions": {
    "additionalDirectories": [
      "../shared",
      "../web"
    ]
  }
}
```

相对路径从你启动 Claude 的目录解析。使用此配置，Claude 可以从 `packages/api/` 工作时读取和编辑 `packages/shared/` 和 `packages/web/` 中的文件。

你也可以在运行时通过在启动 Claude 时传递 `--add-dir` 来授权访问，无需编辑设置：

```bash
claude --add-dir ../shared
```

无论你如何添加目录，Claude 都可以读取和编辑其中的文件。该目录的 CLAUDE.md、`.claude/rules/` 文件和 skills 是否也会加载取决于你如何添加它：

| 添加方式 | 加载 CLAUDE.md 和规则 | 加载 skills |
| :--- | :--- | :--- |
| `additionalDirectories` 设置 | 永不 | 永不 |
| `--add-dir` 标志或 `/add-dir` 命令 | 仅在设置以下环境变量时 | 是 |

要加载通过 `--add-dir` 或 `/add-dir` 添加的目录的 CLAUDE.md 和规则文件，请设置 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` 环境变量：

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared
```

该环境变量对 `additionalDirectories` 设置中列出的目录没有影响。详情请参阅[从附加目录加载](https://code.claude.com/docs/en/memory#load-from-additional-directories)。

对于此区域中每个人都需要的兄弟目录，请将 `additionalDirectories` 提交到 `.claude/settings.json`。对于个人选择或一次性访问，请使用 `.claude/settings.local.json` 或在启动时传递 `--add-dir`。

## 添加按目录的 skills

任何子目录都可以定义限定于自己技术栈的 [skills](https://code.claude.com/docs/en/skills)。skill 在 Claude 确定其相关时按需加载，因此 API 特定的工具在前端工作期间不会消耗上下文。

Skills 位于目录内的 `.claude/skills/` 下。将它们与该区域的代码一起提交，以便克隆仓库的每个人都获得它们。在 monorepo 中，这可以是每个包一套 skills。在大型单代码树中，每个子系统一套，如 `src/db/.claude/skills/`。

在子目录内创建 skill 目录：

```bash
mkdir -p packages/api/.claude/skills/api-testing
```

然后在该目录内写入 `SKILL.md`，这里是 `packages/api/.claude/skills/api-testing/SKILL.md`。此示例教 Claude API 包的测试模式：

```markdown packages/api/.claude/skills/api-testing/SKILL.md
---
name: api-testing
description: API 包的测试模式。在 packages/api/ 中编写或修改测试时使用。
---

## 测试结构

测试在 `src/__tests__/` 中，镜像 `src/` 目录结构。
每个路由文件都有对应的 `.test.ts` 文件。

## 运行测试

- 所有测试：`npm test`
- 单个文件：`npm test -- src/__tests__/routes/users.test.ts`
- 监视模式：`npm test -- --watch`

## 测试工具

- `src/__tests__/helpers/db.ts`：提供 `setupTestDb()` 和 `teardownTestDb()` 用于数据库测试
- `src/__tests__/helpers/auth.ts`：提供 `createTestUser()` 和 `getAuthToken()` 用于需要认证的端点

## 模式

- 使用 `supertest` 进行 HTTP 断言，不要使用原始 fetch
- 始终将数据库测试包装在会回滚的事务中
- 在 `src/__tests__/mocks/` 中模拟外部服务
```

不同的子目录以相同方式持有不同的 skills：`packages/web/.claude/skills/component-patterns/` 描述前端的组件约定而非测试。当 Claude 处理 `packages/api/` 中的文件时，它加载 api-testing skill。当它在 `packages/web/` 中工作时，它加载 component-patterns。在另一个的任务期间，两者的 skills 都不会加载。

你也可以通过文件模式而非放置位置来限定 skill 的范围。[`paths` frontmatter 字段](https://code.claude.com/docs/en/skills#frontmatter-reference)接受 glob 模式，Claude 仅在处理匹配文件时自动加载 skill。将其用于位于仓库根目录 `.claude/skills/` 中但仅适用于特定文件（无论它们出现在哪里）的 skill，如限定于 `**/migrations/**` 的数据库迁移 skill。

有关创建和组织 skills 的更多信息，请参阅 [Skills](https://code.claude.com/docs/en/skills)。

### 保持 skills 可发现

当 skills 分布在多个目录中时，Claude 选择的列表可能会变得很大。Claude 通过读取每个已发现 skill 的名称和描述来选择 skill，只有被选中的 skill 的完整内容才会加载到上下文中。本节介绍如何保持该列表小巧，以及如何编写经得起截断的描述。

哪些 skills 在范围内取决于你从哪里启动 Claude：

* **从子目录如 `packages/api/` 启动**：来自该目录、每个父目录直到仓库根目录、以及用户和企业级别的 skills
* **从仓库根目录启动**：来自会话期间 Claude 触及的每个子目录的 skills，可能累积到数百个
* **使用 `--add-dir` 添加兄弟目录后**：该兄弟目录的 skills 也会加载。`additionalDirectories` 设置仅授权文件访问，不加载 skills

名称总是加载的，但[当有很多时描述会被截断](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short)，这可能会剥离 Claude 用于决定 skill 是否适用的关键词。保持描述简短，并以请求中会包含的词开头，如"在 `packages/api/` 中编写或修改测试"。

对于许多目录共享的 skills，如 PR 约定或部署检查列表，将它们放在仓库根目录的 `.claude/skills/` 中，以便从任何启动目录加载。当共享 skills 需要自己的版本历史或必须跨仓库工作时，请将它们打包为[插件](https://code.claude.com/docs/en/plugins)。插件 skills 使用 `plugin-name:skill-name` 命名空间，因此永远不会与按目录的 skills 冲突。平台团队可以在一个地方进行版本控制和更新。

要查找哪些 skills 未使用，请启用 OpenTelemetry [日志导出器](https://code.claude.com/docs/en/monitoring-usage)并设置 `OTEL_LOG_TOOL_DETAILS=1`，以便 skill 名称被逐字记录而不是被编辑。[`skill_activated` 事件](https://code.claude.com/docs/en/monitoring-usage#skill-activated-event)在其 `skill.name` 属性中记录每次调用，`invocation_trigger` 记录是命令、Claude 还是嵌套 skill 调用了它，这告诉你应该整合或淘汰什么。

## 当分层停止扩展时集中管理约定

按目录的 CLAUDE.md 文件随着代码库增长可能变得难以管理。约定漂移，文件变得过时，没有人拥有根文件。解决这个问题通常落在维护仓库 Claude Code 设置的团队身上，而不是每个在自己区域工作的开发者。

将约定和参考内容从始终加载的 CLAUDE.md 移出，转移到按需加载的机制中：

* [Skills](https://code.claude.com/docs/en/skills)：Claude 仅在与任务相关时加载的参考材料
* [插件](https://code.claude.com/docs/en/plugins)：skills、hooks 和命令的版本化包，由平台团队集中拥有
* [MCP 服务器](https://code.claude.com/docs/en/mcp)：如果你的组织已经在仓库上运行代码搜索或 RAG 索引，请将其作为 MCP 工具暴露，以便 Claude 直接查询而不是读取文件

有关平台团队如何集中强制执行这些设置，请参阅[服务器管理或端点管理设置](https://code.claude.com/docs/en/server-managed-settings#choose-between-server-managed-and-endpoint-managed-settings)。

### 在会话开始时推荐正确的插件

一旦约定存在于插件中，队友在树中不熟悉的区域启动 Claude 时，就没有关于该区域所有者维护哪个插件的信号。[`SessionStart` hook](https://code.claude.com/docs/en/hooks#sessionstart) 可以弥合这一差距，因为 hook 打印到 stdout 的任何内容都会在第一个提示之前添加到 Claude 的上下文中。

例如，你可以编写一个脚本，从 [hook 输入](https://code.claude.com/docs/en/hooks#common-input-fields)中读取启动目录，在提交到仓库的路径到插件映射中查找它，并打印推荐供 Claude 在其第一次回复中传达。请参阅[使用 hooks 自动化操作](https://code.claude.com/docs/en/hooks-guide)来编写和注册 hook。

## 整合配置

以下组合配置使用 monorepo 布局。相同的文件适用于大型单代码树中的任何子目录。项目设置仅从你启动 Claude 的目录加载，因此每个子目录的 `.claude/settings.json` 必须是自包含的，而不是分层在根文件之上。

以下示例将 `worktree`、`additionalDirectories` 和 `Read` 拒绝规则提交到 `.claude/settings.json`，以便 `packages/api/` 中的每位开发者获得相同的兄弟访问权限、稀疏路径和排除项。以下是 `packages/api/` 的提交的按区域设置文件：

```json packages/api/.claude/settings.json
{
  "worktree": {
    "sparsePaths": [
      ".claude",
      "packages/api",
      "packages/shared"
    ],
    "symlinkDirectories": [
      "node_modules"
    ]
  },
  "permissions": {
    "additionalDirectories": [
      "../shared"
    ],
    "deny": [
      "Read(./**/dist/**)",
      "Read(./**/build/**)"
    ]
  }
}
```

由于此会话从 `packages/api/` 启动，兄弟包的 CLAUDE.md 文件已在范围之外，所以这里不需要 `claudeMdExcludes`。如果你也从根目录启动会话，请将其添加到仓库根目录的 `.claude/settings.local.json` 中。

`additionalDirectories` 条目在你直接从 `packages/api/` 启动 Claude 时适用。在此会话创建的工作树内部，工作目录是工作树根目录，所以此设置文件不会加载。兄弟包在工作树内部无需它即可访问，但拒绝规则需要在仓库根目录的 `.claude/settings.json` 中有第二个副本，以便工作树会话能够获取它们，如[工作树设置说明](#只检出你需要的目录)所述：

```json .claude/settings.json
{
  "permissions": {
    "deny": [
      "Read(./**/dist/**)",
      "Read(./**/build/**)"
    ]
  }
}
```

设置完成后，仓库具有以下布局：

```text
monorepo/
  CLAUDE.md
  .claude/settings.json                           # 工作树的拒绝规则
  packages/
    api/
      CLAUDE.md
      .claude/settings.json                       # worktree、additionalDirectories、拒绝规则
      .claude/skills/api-testing/SKILL.md
    web/
      CLAUDE.md
      .claude/skills/component-patterns/SKILL.md
    shared/
      CLAUDE.md
```

使用此设置，从 `packages/api/` 启动 Claude 时：

* 加载根 CLAUDE.md 和 `packages/api/CLAUDE.md`，跳过 `packages/web/CLAUDE.md`
* 可以读取和编辑 `packages/api/` 和 `packages/shared/` 中的文件
* 跳过 `packages/api/` 下 `dist/` 和 `build/` 中的构建输出读取
* 可以按需使用 api-testing skill
* 创建包含 `.claude/`、`packages/api/`、`packages/shared/` 和根级文件的工作树，并从根设置文件对工作树应用拒绝规则

## 限定和规划跨包更改

上述配置控制 Claude 看到的内容。当单个更改涉及多个包时（如更新共享类型及其所有使用它的调用点），你如何限定和排序任务也会影响结果。

两种技术有助于保持跨包更改的一致性：

* **在一个会话中交给 Claude 整个更改**：将共享编辑及其调用点一起处理，保持每个编辑背后的决策一致，而不是按包重新推导
* **在编辑前将计划保存到文件**：[先计划](https://code.claude.com/docs/en/best-practices#explore-first-then-plan-then-code)并要求 Claude 将计划写入仓库中的 markdown 文件。长时间的跨包会话会[压缩其上下文](https://code.claude.com/docs/en/context-window#what-survives-compaction)，保存的计划会保留下来，而对话历史可能不会

## 后续步骤

配置完成后，你可以进行细化：

* 使用 [hooks](https://code.claude.com/docs/en/hooks-guide) 在 Claude 编辑文件后运行按目录的 linter 或类型检查器
* 阅读[有效管理成本](https://code.claude.com/docs/en/costs)以了解代码库大小如何影响 token 使用，以及在更广泛推出之前设置支出限制
* 在 Claude 博客上阅读[Claude Code 如何在大型代码库中工作](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start)，了解组织推出模式和所有权模型，这些模型位于本页的每仓库配置之上
