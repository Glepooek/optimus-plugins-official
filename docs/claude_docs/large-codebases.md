# 在 monorepo 或大型代码库中设置 Claude Code

> 为 monorepo 和大型单体代码库配置 Claude Code，使用嵌套的 CLAUDE.md 文件、稀疏 worktree、代码智能以及按包划分的 skills，让 Claude 专注于你正在处理的代码。

来源：[code.claude.com/docs/en/large-codebases](https://code.claude.com/docs/en/large-codebases)

---

大型代码库可以是一个包含数百万行代码的单一仓库，也可以是包含多个包的 monorepo。Claude Code 在任何规模下都能工作，但随着代码库增长，为小型项目调优的默认设置可能会把上下文窗口填满与任务无关的指令和文件读取内容，浪费 token 并降低 Claude 的表现。

本指南向个人开发者和工程团队展示如何将 Claude 的作用范围限定在任务所涉及的代码库部分。每个章节都会说明该设置是仅限于你本机的个人设置，还是提交到仓库中的设置。

## 本指南涵盖的内容

[下方表格](#settings-on-this-page)列出了每项设置及其作用。表格之后的[文件树](#the-example-monorepo)是本页所有代码示例所引用的示例 monorepo。

### 本页设置一览

以下每项设置都是独立的。它们相互叠加而非相互替代，因此可根据你的仓库情况选择适用的设置。[选择从哪里启动 Claude](#choose-where-to-start-claude) 决定了你的设置文件存放位置，所以请先阅读该部分。[整合到一起](#put-it-together)展示了所有设置组合使用的效果。

| 我想要                                                                                           | 使用                                                                                        |
| :--- | :--- |
| 只加载我所触及代码的规范，而不是一个覆盖所有子系统的根文件 | 按目录分层的 [CLAUDE.md 文件](#layer-claude-md-files-by-directory)                       |
| 排除自己从不涉及的包的 CLAUDE.md 文件                                              | [`claudeMdExcludes`](#exclude-irrelevant-claude-md-files)                                  |
| 阻止 Claude 打开构建产物、生成代码和第三方依赖代码                                   | `permissions.deny` 中的 [`Read` 拒绝规则](#block-reads-of-generated-and-vendored-code)     |
| 通过语言服务器查找符号的定义或调用者，而不是扫描文件         | 一个[代码智能 plugin](#reduce-file-reads-with-code-intelligence)                    |
| 当 Claude 创建 worktree 时，只检出任务需要的目录                    | [`worktree.sparsePaths`](#check-out-only-the-directories-you-need)                         |
| 在同一会话中读取和编辑同级包或另一个仓库                     | [`--add-dir`](#grant-access-across-packages-or-repositories) 或 `additionalDirectories`    |
| 让 Claude 获得特定于某一区域、只在相关时才加载的操作程序              | 按目录划分的 [skills](#add-per-directory-skills)                                          |
| 用一套所有人都安装的通用规范，取代多个按目录分层的 CLAUDE.md 文件 | 内部 marketplace 中的一个[plugin](#centralize-conventions-when-layering-stops-scaling) |

> **注意：**
> 关于在任何仓库中保持上下文精简的工作流技巧，例如[在子智能体中运行探索](https://code.claude.com/docs/en/best-practices#use-subagents-for-investigation)以使文件读取不占用主对话上下文，请参阅[Claude Code 最佳实践](https://code.claude.com/docs/en/best-practices)。要为组织中的每位开发者推出基线配置，请参阅[为你的组织设置 Claude Code](https://code.claude.com/docs/en/admin-setup)。

### 示例 monorepo

本页的示例均引用一个包含三个包的 monorepo。同样的模式也适用于大型单一代码树：当示例使用 `packages/api/` 时，可替换为你自己的子系统目录，例如 `src/backend/` 或 `lib/core/`。

```text theme={null}
monorepo/
  CLAUDE.md                     # 根目录指令
  packages/
    api/
      CLAUDE.md                 # API 专属指令
      .claude/skills/
      src/
    web/
      CLAUDE.md                 # 前端专属指令
      .claude/skills/
      src/
    shared/
      CLAUDE.md                 # 共享库指令
      src/
```

## 选择从哪里启动 Claude

你启动 `claude` 的位置决定了 Claude 在不额外获得权限授予的情况下可以读取和编辑哪些文件、启动时加载哪些 CLAUDE.md 文件，以及应用哪些项目设置。

| 启动位置      | 文件访问权限                             | 启动时加载的 CLAUDE.md                                           | 适用场景                                   |
| :--- | :--- | :--- | :--- |
| 仓库根目录 | 所有文件                              | 仅根目录文件；子目录文件在 Claude 读取该处时按需加载 | 任务跨越多个包或子系统 |
| 子目录  | 仅该子树，直到你授予更多权限 | 该目录及其所有祖先目录的文件                               | 工作限定在一个包或子系统内 |

`.claude/settings.json` 中的项目设置仅从你的启动目录加载，不会像 CLAUDE.md 文件那样从父目录继承：位于仓库根目录的 `.claude/settings.json` 只有在你从根目录启动时才会生效。

下方每一节都会说明其设置文件应位于仓库根目录还是你启动所在的子目录，以及它是提交到仓库还是保留在本地。

## 按目录分层 CLAUDE.md 文件

在大型代码库中，仅在仓库根目录放置一个 CLAUDE.md，往往会导致它不断膨胀以覆盖每个子系统的规范，从而在与当前任务无关的指令上耗费上下文，或者为了保持通用而变得不够有用。将指令拆分到各个目录的文件中，意味着 Claude 只加载仓库级规则加上你正在处理代码所在区域的规范。

Claude Code 在启动时会加载你工作目录及其每个父目录中的每个 [CLAUDE.md](https://code.claude.com/docs/en/memory) 文件，然后在 Claude 读取某个子目录中的文件时按需加载该子目录的文件。根文件设定仓库级规则，每个子目录再添加自己的规则。

常见的做法是分两层：

* **根目录 `CLAUDE.md`**：适用于所有地方的指令，例如编码规范、提交规范和仓库布局
* **各子目录 `CLAUDE.md`**：特定于该区域技术栈的规范。在 monorepo 中即每个包一个；在大型单一代码树中，则是每个子系统一个，例如 `src/db/` 或 `src/api/`

将这些文件提交到仓库，以便团队成员继承它们。每个目录的负责人通常维护自己的文件。

根目录 `CLAUDE.md` 用于让 Claude 了解仓库结构：

```markdown CLAUDE.md theme={null}
This is a monorepo with three packages under packages/:

- packages/api: Node.js REST API with Express, TypeScript, and PostgreSQL
- packages/web: React frontend with Vite, TypeScript, and TailwindCSS
- packages/shared: shared TypeScript utilities used by both api and web


从包目录运行命令，而不是从 monorepo 根目录运行。
每个包都有自己的 tsconfig.json、package.json 和测试套件。
```

每个子目录的 `CLAUDE.md`（此处为 `packages/api/CLAUDE.md`）会添加该区域技术栈特有的上下文：

```markdown packages/api/CLAUDE.md theme={null}
This package is the REST API server.

- Run tests: `npm test` (uses Vitest)
- Run dev server: `npm run dev` (port 3001)
- Database migrations: `npm run migrate`
- Environment variables: copy `.env.example` to `.env`

API routes are in src/routes/. Each route file exports an Express router.
Database queries use Knex in src/db/. Never write raw SQL strings in route handlers.
```

当你从 `packages/api/` 启动 Claude 时，它会同时加载 `packages/api/CLAUDE.md` 和根目录的 `CLAUDE.md`。Claude 会在上下文中同时看到本地指令和仓库级规则,而不会加载 `packages/web/` 的任何指令。这一规则对非 monorepo 目录树中的任何子目录同样适用。

有几种方法可以让这些文件随代码库和模型的变化保持最新：

* **在 pull request 中审查**：把 CLAUDE.md 的修改当作普通文档变更来处理,使约定与代码保持同步
* **在重大模型发布后重新审视**：一些为规避旧模型局限而设的指令,在新模型能自行处理该情况后可能变成多余负担。例如,一条强制单文件重构的规则,在该局限消失后就可以删除
* **添加一个会提出更新建议的 Stop hook**：[`Stop` hook](https://code.claude.com/docs/en/hooks#stop) 在 Claude 完成响应时会收到会话 transcript 的路径,因此脚本可以在暴露出的问题还很新鲜时审查该会话并提出 CLAUDE.md 更新建议

关于 CLAUDE.md 文件如何加载与交互的更多信息,参见 [Memory and project instructions](https://code.claude.com/docs/en/memory)。

### 在按目录设置 CLAUDE.md 与路径限定规则之间做选择

按目录设置的 `CLAUDE.md` 文件与 `.claude/rules/` 下的[路径限定规则](https://code.claude.com/docs/en/memory#path-specific-rules)都能让你针对目录树的某一部分设定指令。它们的区别在于文件存放的位置以及加载的时机。

| 方式                             | 文件位置                            | 加载时机                                                                              | 适用场景                                                                                  |
| :--- | :--- | :--- | :--- |
| 按目录设置 `CLAUDE.md`            | 目录内部,与代码放在一起 | 从该目录启动时加载,或 Claude 读取该目录下文件时按需加载 | 目录所有者自行维护约定；指令与代码一起纳入版本控制 |
| `.claude/rules/` 中的路径限定规则 | 仓库根目录下的中心化 `.claude/` | 当 Claude 处理匹配该规则 `paths:` glob 的文件时 | 你希望所有约定集中在一处,或同一规则适用于多个分散的路径   |

如果还想了解与 skills 的对比,参见 [Compare similar features](https://code.claude.com/docs/en/features-overview#compare-similar-features)。

### 排除不相关的 CLAUDE.md 文件

当你从仓库根目录启动 Claude 时,每个子目录的 CLAUDE.md 会在 Claude 读取该目录下的文件时立即加载。`claudeMdExcludes` 设置可按路径或 glob 模式跳过特定文件,使其永远不会加载。

对于你从不涉及的目录（例如其他团队的包、遗留代码或第三方引入的子目录树）使用此设置。该排除列表是静态的,不是按任务切换的开关。如果你今天想专注于某个包,明天想专注于另一个包,应该[从该包的目录启动 Claude](#choose-where-to-start-claude),而不是编辑排除列表。

如果你只想为自己设置这些排除项,把该设置放进 `.claude/settings.local.json`。Claude Code 在创建该文件时会将其加入 gitignore；由于此处是你手动创建它,请自行将其加入 gitignore。模式使用 glob 语法,并与绝对文件路径匹配,因此以相对风格书写的模式要以 `**/` 开头,以便匹配目录树中的任意位置。下面的示例排除了其他团队拥有的包：

```json .claude/settings.local.json theme={null}
{
  "claudeMdExcludes": [
    "**/packages/admin-dashboard/**",
    "**/packages/legacy-*/**"
  ]
}
```

这会跳过这些包下的每一个 CLAUDE.md 和 rules 文件。根目录的 CLAUDE.md 以及你实际工作的那些包仍会正常加载。

以下模式涵盖了其他常见场景：

* `"**/packages/*/CLAUDE.md"`：排除每个包的 CLAUDE.md,同时保留根目录的
* `"**/packages/web/**"`：排除 web 包下的所有内容,包括 rules
* `"/home/user/monorepo/legacy/CLAUDE.md"`：按绝对路径排除某个特定文件

受管理策略的 CLAUDE.md 文件无法被排除,因此组织级指令始终生效。你可以在任意[设置作用域](https://code.claude.com/docs/en/settings#configuration-scopes)（user、project、local 或 managed）设置 `claudeMdExcludes`。数组会跨作用域合并,因此团队可以设置项目级默认值,个人再叠加本地覆盖项。

完整的排除文档参见 [Exclude specific CLAUDE.md files](https://code.claude.com/docs/en/memory#exclude-specific-claude-md-files)。

## 减少 Claude 读取的内容

指令只是最终进入 Claude 上下文的一部分。文件读取是另一项随代码库增长而增加的成本。下面的设置会屏蔽对不相关路径的读取,并用 language-server 查找取代穷举式的文件扫描。

### 屏蔽对生成代码和第三方引入代码的读取

Claude 的内容搜索默认遵循 `.gitignore`,因此已列在其中的路径（例如 `node_modules/`、`dist/`、`build/`）无需额外配置就不会出现在搜索结果中。

对于已纳入版本控制的路径,例如第三方引入的 SDK 或已提交的生成代码,请在 `permissions.deny` 中添加 `Read` 拒绝规则,即使搜索结果列出了这些文件,也阻止 Claude 打开它们。

要让这些排除规则对仓库中所有工作的人生效,把它们提交到 `.claude/settings.json`。如果想保持个人化,则改用 `.claude/settings.local.json`。与本页其他项目设置一样,这些文件只会从你的启动目录加载。如果你从仓库根目录启动,就把它们放在根目录；如果从子目录启动,就放在每个包各自的 `.claude/` 中。要在任何启动目录下都强制执行相同的拒绝规则,请在[受管理设置](https://code.claude.com/docs/en/settings#settings-files)中设置它们,user 和 project 设置无法覆盖受管理设置。

下面的示例屏蔽了构建产物和一个第三方引入的 SDK：

```json .claude/settings.json theme={null}
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

拒绝规则覆盖 Claude 的内置文件工具和可识别的 Bash 文件命令（包括 `cat`、`head`、`grep` 和 `find`），只要传入的参数是被拒绝的路径。这些规则不会从递归搜索的输出结果中过滤掉被拒绝的路径，也不会覆盖那些自行打开文件的任意子进程。完整的模式语法请参见 [Read and Edit permission rules](https://code.claude.com/docs/en/permissions#read-and-edit)。

### 通过代码智能减少文件读取

在大型代码库中，查找某个符号的定义位置或使用位置可能要耗费大量文件读取和 grep 调用。[Code intelligence plugins](https://code.claude.com/docs/en/discover-plugins#code-intelligence) 将 Claude 连接到语言服务器，使其可以直接跳转到定义、查找引用、发现类型错误，而不必扫描整个目录树。

官方 marketplace 提供了 TypeScript、Python、Go、Rust 等常见语言的插件。下面的示例安装了 TypeScript 插件：

```shell theme={null}
/plugin install typescript-lsp@claude-plugins-official
```

若要为仓库中的所有人启用某个插件，而不是仅为自己安装，可将其添加到 [`enabledPlugins` project setting](https://code.claude.com/docs/en/settings#plugin-settings)。

Code intelligence 插件需要在每位开发者的机器上安装对应语言的语言服务器二进制文件。参见[各语言所需的二进制文件](https://code.claude.com/docs/en/discover-plugins#code-intelligence)。从官方 marketplace 安装需要能够访问托管该 marketplace 的 GitHub 网络。在受限网络环境下，请改为[从内部 Git 主机或本地路径添加 marketplace](https://code.claude.com/docs/en/discover-plugins#add-from-other-git-hosts)。

这与上文的 `claudeMdExcludes` 和 `Read` 拒绝规则相辅相成。前者让无关内容不进入上下文，而 code intelligence 则避免 Claude 读遍剩余内容去定位某个定义。

## 限定工作树与文件访问范围

以下设置控制工作树中磁盘上的内容，以及 Claude 在起始点之外可以读写的目录。

### 只检出你需要的目录

`--worktree` 标志会在一个新的 git 工作树中启动会话，使改动与你的主检出目录相互隔离。默认情况下它会检出整个仓库。在大型仓库中，`worktree.sparsePaths` 设置会使用 git sparse-checkout，只将列出的目录以及根目录下的文件写入磁盘，从而让工作树创建更快、占用空间更少。

如果在此目录下工作的每个人都需要相同的路径，请将该设置提交到 `.claude/settings.json`。若只想为自己添加路径，请使用 `.claude/settings.local.json`：这些列表会跨作用域合并，因此本地文件可以在已提交的列表基础上新增路径，但不能移除其中的路径。下面的示例展示了已提交的文件：

```json .claude/settings.json theme={null}
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

当 Claude 创建工作树时，它只会检出 `.claude/`、`packages/api/` 和 `packages/shared/`，而不是完整的目录树。`sparsePaths` 中的路径是相对于仓库根目录的，无论你是从哪个子目录启动 Claude。这里可以填写任意目录路径，不限于 package 根目录。

这对[subagent worktree isolation](https://code.claude.com/docs/en/worktrees#isolate-subagents-with-worktrees) 尤其有用。子智能体是为子任务派生的并行 Claude 实例，其中每个在工作树中运行的子智能体获得的是一个轻量检出，而不是完整的目录树。一个会话中的所有工作树共享相同的 `sparsePaths`，因此如果一个子智能体需要 `packages/api/`，另一个需要 `packages/web/`，就要把两者都列出来。

在 `sparsePaths` 中列出目录，而不是单个文件。像 `package.json`、`tsconfig.base.json` 以及锁文件这样的根目录文件，会随你列出的目录一起被检出。根目录下的目录则不会自动检出，因此如果你希望在工作树内可以使用仓库根目录的 `.claude/settings.json`、`.claude/rules/` 或 `.claude/skills/`，需要在列表中包含 `.claude`。

为避免在各个工作树之间重复保存 `node_modules` 这类大型目录，可以将 `sparsePaths` 与同一个 `.claude/settings.json` 中的 `symlinkDirectories` 搭配使用：

```json .claude/settings.json theme={null}
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

这会创建一个从每个工作树的 `node_modules/` 指回主仓库副本的符号链接，而不是在磁盘上重复存储它。

> **注意：**
> `sparsePaths` 和 `symlinkDirectories` 设置是在创建工作树之前从你的起始目录读取的。创建完成后，会话的工作目录会变为工作树根目录，而不是你启动时所在的子目录。因此，工作树内的项目设置会从工作树根目录的 `.claude/settings.json` 加载，即仓库根目录该文件的已检出副本。如果你需要在工作树内使用其他设置，例如权限规则或 hooks，请将它们放在仓库根目录的 `.claude/settings.json` 中。

完整的工作树设置参考请参见 [Worktree settings](https://code.claude.com/docs/en/settings#worktree-settings)。

### 跨包或跨仓库授予访问权限

本节适用于你从子目录启动 Claude，或者任务跨越多个检出目录的情况。如果你是从仓库根目录启动、并在单一大型目录树中工作，Claude 已经可以访问所有文件，可以跳过本节。

当你从 `packages/api/` 启动 Claude 时，它只能读写该目录内的文件。如果某个任务需要跨包修改，例如更新一个 `api` 和 `web` 都引用的共享类型，就需要为相邻目录授予访问权限。同样的机制也适用于为一个单独检出的仓库授予访问权限。

`.claude/settings.json` 中的 `additionalDirectories` 设置可以让 Claude 访问工作目录之外的目录。下面的示例为两个相邻的 package 授予了访问权限：

```json .claude/settings.json theme={null}
{
  "permissions": {
    "additionalDirectories": [
      "../shared",

      "../web"
    ]
  }
}
```

相对路径相对于你启动 Claude 时所在的目录进行解析。使用此配置，当在 `packages/api/` 中工作时，Claude 可以读取和编辑 `packages/shared/` 和 `packages/web/` 中的文件。

你也可以在运行时授予访问权限而不修改 settings，方法是在启动 Claude 时传入 `--add-dir`：

```bash theme={null}
claude --add-dir ../shared
```

无论你以哪种方式添加目录，Claude 都可以读取和编辑该目录中的文件。该目录的 CLAUDE.md、`.claude/rules/` 文件以及 skills 是否也会加载，取决于你添加目录的方式：

| 添加方式                             | 是否加载 CLAUDE.md 和 rules                | 是否加载 skills |
| :--- | :--- | :--- |
| `additionalDirectories` 设置        | 从不                                    | 从不        |
| `--add-dir` 标志或 `/add-dir` 命令 | 仅在设置以下环境变量时 | 是          |

要从通过 `--add-dir` 或 `/add-dir` 添加的目录中加载 CLAUDE.md 和 rules 文件，需设置 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` 环境变量：

```bash theme={null}
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared
```

该环境变量对 `additionalDirectories` 设置中列出的目录没有影响。详情参见 [从额外目录加载](https://code.claude.com/docs/en/memory#load-from-additional-directories)。

对于该区域中所有人都需要的同级目录，将 `additionalDirectories` 提交到 `.claude/settings.json`。对于个人选择或一次性访问，使用 `.claude/settings.local.json` 或在启动时传入 `--add-dir`。

## 添加按目录划分的 skills

任何子目录都可以定义作用范围限定于自身技术栈的 [skills](https://code.claude.com/docs/en/skills)。skill 会在 Claude 判断其相关时按需加载，因此特定于 API 的工具不会在前端工作期间占用上下文。

Skills 位于目录内的 `.claude/skills/` 下。将它们与该区域的代码一起提交，以便任何克隆该仓库的人都能获得它们。在 monorepo 中，这可以是每个 package 一套 skills。在一个大型单一代码树中，则是每个子系统一套，例如 `src/db/.claude/skills/`。

在子目录内创建一个 skill 目录：

```bash theme={null}
mkdir -p packages/api/.claude/skills/api-testing
```

然后在该目录内编写 `SKILL.md`，此处即 `packages/api/.claude/skills/api-testing/SKILL.md`。此示例教会 Claude 该 API package 的测试模式：

```markdown packages/api/.claude/skills/api-testing/SKILL.md theme={null}
---
name: api-testing
description: Testing patterns for the API package. Use when writing or modifying tests in packages/api/.
---

## Test structure

Tests are in `src/__tests__/` mirroring the `src/` directory structure.
Each route file has a corresponding `.test.ts` file.

## Running tests

- All tests: `npm test`
- Single file: `npm test -- src/__tests__/routes/users.test.ts`
- Watch mode: `npm test -- --watch`

## Test utilities

- `src/__tests__/helpers/db.ts`: provides `setupTestDb()` and `teardownTestDb()` for database tests
- `src/__tests__/helpers/auth.ts`: provides `createTestUser()` and `getAuthToken()` for authenticated endpoints

## Patterns

- Use `supertest` for HTTP assertions, not raw fetch
- Always wrap database tests in a transaction that rolls back
- Mock external services in `src/__tests__/mocks/`
```

另一个子目录以同样的方式持有不同的 skills：`packages/web/.claude/skills/component-patterns/` 描述的是前端的组件约定而非测试。当 Claude 在 `packages/api/` 中的文件上工作时，它会加载 api-testing skill。当它在 `packages/web/` 中工作时，则会加载 component-patterns。任何一个目录的 skills 都不会在另一个目录的任务中加载。

你也可以通过文件模式而非放置位置来限定 skill 的作用范围。[`paths` frontmatter 字段](https://code.claude.com/docs/en/skills#frontmatter-reference) 接受 glob 模式，Claude 只有在处理匹配的文件时才会自动加载该 skill。这适用于位于仓库根目录 `.claude/skills/` 中，但仅适用于特定文件（无论其出现在何处）的 skill，例如作用范围限定于 `**/migrations/**` 的数据库迁移 skill。

关于创建和组织 skills 的更多内容，参见 [Skills](https://code.claude.com/docs/en/skills)。

### 保持 skills 可被发现

随着 skills 分散在多个目录中，Claude 可选择的列表会变大。Claude 通过读取每个已发现 skill 的名称和描述来选择一个 skill，只有被选中的 skill 的完整内容会加载到上下文中。本节介绍如何保持该列表精简，以及如何编写在被缩短后仍然有效的描述。

哪些 skills 处于作用范围内取决于你从何处启动 Claude：

* **从子目录（如 `packages/api/`）启动**：该目录的 skills、直到仓库根目录的每一层父目录的 skills，以及用户级和企业级的 skills
* **从仓库根目录启动**：Claude 在会话期间涉及的每个子目录的 skills，这可能累积到数百个
* **在通过 [`--add-dir`](#grant-access-across-packages-or-repositories) 添加同级目录后**：该同级目录的 skills 也会加载。`additionalDirectories` 设置仅授予文件访问权限，不会加载 skills

名称总是会加载，但[当数量较多时描述会被截短](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short)，这可能会剥离掉 Claude 用来判断某个 skill 是否适用的关键词。保持描述简短，并以请求中可能包含的词语开头，例如"writing or modifying tests in `packages/api/`"。

对于多个目录共用的 skills，例如 PR 约定或部署检查清单，将它们放在仓库根目录的 `.claude/skills/` 中，这样无论从哪个起始目录都能加载。当共享 skills 需要拥有自己的版本历史或必须跨仓库使用时，请将它们打包为 [plugin](https://code.claude.com/docs/en/plugins)。Plugin skills 使用 `plugin-name:skill-name` 命名空间，因此它们永远不会与按目录设置的 skills 冲突。平台团队可以在一个地方对其进行版本管理和更新。

要查找哪些 skills 未被使用，启用 OpenTelemetry [日志导出器](https://code.claude.com/docs/en/monitoring-usage)并设置 `OTEL_LOG_TOOL_DETAILS=1`，使 skill 名称按原样记录而不是被遮蔽。[`skill_activated` 事件](https://code.claude.com/docs/en/monitoring-usage#skill-activated-event)会在其 `skill.name` 属性中记录每一次调用，而 `invocation_trigger` 会记录是命令、Claude 还是某个嵌套的 skill 触发了该调用，这能告诉你应该整合或淘汰哪些内容。

## 当分层不再具有可扩展性时，集中化管理约定

随着代码库的增长，按目录分层的 CLAUDE.md 文件会变得难以治理。约定会逐渐偏离、文件会过时，也没有人负责根目录。解决这个问题通常落在维护仓库 Claude Code 配置的团队身上，而不是每个在自己领域工作的开发者身上。

将约定和参考内容从始终加载的 CLAUDE.md 中移出，转移到按需加载的机制中：

* [Skills](https://code.claude.com/docs/en/skills)：仅在与任务相关时 Claude 才会加载的参考资料
* [Plugins](https://code.claude.com/docs/en/plugins)：由平台团队集中拥有的、包含 skills、hooks 和 commands 的版本化包
* [MCP servers](https://code.claude.com/docs/en/mcp)：如果你的组织已经针对该仓库运行了代码搜索或 RAG 索引，将其暴露为 MCP 工具，这样 Claude 就会查询它，而不是直接读取文件

关于平台团队如何集中执行这些规则，请参阅[服务器管理或端点管理的设置](https://code.claude.com/docs/en/server-managed-settings#choose-between-server-managed-and-endpoint-managed-settings)。

### 在会话启动时推荐合适的 plugin

一旦约定存放在 plugins 中，在树中不熟悉的部分启动 Claude 的团队成员就无法知道该区域的所有者维护的是哪个 plugin。[`SessionStart` hook](https://code.claude.com/docs/en/hooks#sessionstart) 可以弥补这一空白，因为该 hook 打印到 stdout 的任何内容都会在第一条提示词之前被添加到 Claude 的上下文中。

例如，你可以编写一个脚本，从[hook 输入](https://code.claude.com/docs/en/hooks#common-input-fields)中读取启动目录，在提交到仓库中的路径到 plugin 映射表中进行查找，并打印出建议供 Claude 在其第一条回复中转达。请参阅[通过 hooks 自动化操作](https://code.claude.com/docs/en/hooks-guide)来编写和注册该 hook。

## 整合起来

下面的组合配置使用了 monorepo 布局。同样的文件也适用于任何大型单一代码树中的子目录。项目设置只会从你启动 Claude 的那个目录加载，因此每个子目录的 `.claude/settings.json` 必须自成一体，而不是分层叠加在根文件之上。

该示例将 `worktree`、`additionalDirectories` 以及 `Read` 拒绝规则提交到 `.claude/settings.json` 中，这样 `packages/api/` 中的每个开发者都能获得相同的同级访问权限、稀疏路径和排除规则。下面的文件是 `packages/api/` 提交的按区域设置文件：

```json packages/api/.claude/settings.json theme={null}
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

由于此会话是从 `packages/api/` 启动的，同级 packages 的 CLAUDE.md 文件已经不在作用范围内，因此这里不需要 `claudeMdExcludes`。如果你也会从根目录启动会话，请将其添加到仓库根目录的 `.claude/settings.local.json` 中。

`additionalDirectories` 条目适用于你直接从 `packages/api/` 启动 Claude 的情况。在从此会话创建的 worktree 内部，工作目录是 worktree 根目录，因此该设置文件不会加载。同级 packages 在 worktree 内部无需它也已经可以访问，但拒绝规则需要在仓库根目录的 `.claude/settings.json` 中再放一份副本，以便 worktree 会话能够获取它们，正如[worktree 设置说明](#check-out-only-the-directories-you-need)所述：

```json .claude/settings.json theme={null}
{
  "permissions": {
    "deny": [
      "Read(./**/dist/**)",
      "Read(./**/build/**)"
    ]
  }
}
```

设置完成后，仓库的布局如下：

```text theme={null}
monorepo/
  CLAUDE.md
  .claude/settings.json                           # worktree 会话的拒绝规则
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

在此设置下，从 `packages/api/` 启动 Claude 时：

* 加载根目录的 CLAUDE.md 和 `packages/api/CLAUDE.md`，跳过 `packages/web/CLAUDE.md`

* 可以读取和编辑 `packages/api/` 和 `packages/shared/` 中的文件
* 跳过 `packages/api/` 下 `dist/` 和 `build/` 中构建输出的读取
* 按需提供 api-testing skill
* 创建包含 `.claude/`、`packages/api/`、`packages/shared/` 以及根级文件的工作树，并在整个工作树中应用来自根设置文件的拒绝规则

## 跨包的范围与计划变更

上述配置控制的是 Claude 能看到的内容。当单次变更涉及多个包时（例如更新一个共享类型以及所有使用它的调用点），你如何界定范围并安排任务顺序同样会影响结果。

两种方法有助于保持跨包变更的一致性：

* **在一个会话中把整个变更交给 Claude**：将共享编辑及其调用点一并交出，能让每处编辑背后的决策保持一致，而不是逐个包重新推导
* **在编辑前将计划保存到文件中**：[先制定计划](https://code.claude.com/docs/en/best-practices#explore-first-then-plan-then-code)，并让 Claude 将计划写入仓库中的一个 markdown 文件。一次较长的跨包会话会在过程中[压缩其上下文](https://code.claude.com/docs/en/context-window#what-survives-compaction)，而保存下来的计划在对话历史可能无法保留时依然留存

## 后续步骤

配置完成后，你可以进一步完善：

* 使用[hooks](https://code.claude.com/docs/en/hooks-guide)在 Claude 编辑文件后运行按目录划分的 linter 或类型检查器
* 阅读[有效管理成本](https://code.claude.com/docs/en/costs)以了解代码库规模如何影响 token 使用量，以及如何在更大范围推广前设置花费上限
* 阅读 Claude 博客上的[Claude Code 如何在大型代码库中工作](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start)，了解位于本页面所述的单仓库配置之上的组织级推广模式和归属模型

