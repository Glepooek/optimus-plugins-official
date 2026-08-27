> **本文件在 Git 协作规范中的定位**
>
> 本文件是提交信息规范的描述性参考（讲解性质，不带 MUST/SHOULD/MAY 语气）。
> 在规范体系中，它属于 **`rules/02-commit-messages.md`（提交信息规范与敏感信息防护）** 的配套参考，被该篇引用。
>
> - **适用场景**：需要 Conventional Commits 完整规范细节、要为仓库配置 commit-msg 校验 hook、或要为敏感信息防护选型扫描工具时查阅
> - **如何结合**：`rules/02-commit-messages.md` §1 的格式要求源自本文件第 1 节；§2 的 hook 不可绕过要求，实现方式见本文件第 2 节；§3 的 secret scanning 建议，工具选型见本文件第 3 节
> - **维护**：本文件记录团队通用的工具与规范知识，不承载特定仓库的强制约束——强制约束写在 `rules/02-commit-messages.md`

# 提交信息规范：Conventional Commits 完整规范、Hook 实现、敏感信息扫描工具

## 1. Conventional Commits 完整规范

### 1.1 基本结构

```
<type>[(<scope>)][!]: <description>

[body]

[footer(s)]
```

- **`type`**：变更类型，必填，见下表
- **`scope`**（可选）：变更影响范围，用括号包裹，如模块名、包名——`feat(auth): ...`
- **`!`**（可选）：紧跟 `type`/`scope` 后，标记这是破坏性变更（等价于 footer 里写 `BREAKING CHANGE`）
- **`description`**：一行简述，祈使语气（"add" 而非 "added"），首字母小写，结尾不加句号
- **`body`**（可选）：详细说明变更动机与实现方式，与 description 之间空一行
- **`footer`**（可选）：额外元信息，如 `BREAKING CHANGE: <说明>`、`Refs: #123`、`Reviewed-by: ...`，每个 footer 独占一行

### 1.2 完整 type 清单

| type | 说明 | 触发的 semver 变更（配合自动化发布工具时） |
|---|---|---|
| `feat` | 新功能 | minor |
| `fix` | bug 修复 | patch |
| `docs` | 仅文档变更 | 无 |
| `style` | 不影响代码逻辑的格式变更（空格、格式化、缺少分号等） | 无 |
| `refactor` | 既不是新功能也不是修复的代码重构 | 无 |
| `perf` | 性能优化 | patch |
| `test` | 新增或修正测试 | 无 |
| `build` | 构建系统或外部依赖变更（如 npm、webpack、gradle） | 无 |
| `ci` | CI 配置文件与脚本变更 | 无 |
| `chore` | 其他不修改 src 或 test 文件的杂项变更 | 无 |
| `revert` | 回退此前的提交 | 视被回退提交而定 |

### 1.3 破坏性变更（BREAKING CHANGE）

破坏性变更可以伴随任意 `type`，有两种等价写法：

```
feat(api)!: 移除废弃的 v1 端点

BREAKING CHANGE: /api/v1/* 端点已移除，请迁移至 /api/v2/*
```

或不用 `!`，只在 footer 声明：

```
feat(api): 移除废弃的 v1 端点

BREAKING CHANGE: /api/v1/* 端点已移除，请迁移至 /api/v2/*
```

配合自动化发布工具（如 semantic-release）时，footer 中出现 `BREAKING CHANGE:` 会强制触发 major 版本升级，无论 `type` 是什么。

### 1.4 多行 body 写法

body 支持多段落，段落间空行分隔；也可用 `-` 列表罗列多个变更点：

```
fix(parser): 修正嵌套括号解析导致的栈溢出

此前递归下降解析器对深度嵌套的括号表达式没有深度限制，
超过约 1000 层嵌套时会触发 StackOverflowException。

- 将递归改为显式栈迭代
- 新增最大嵌套深度配置项，超限时抛出可捕获的 ParseException

Refs: #234
```

### 1.5 与语义化版本（SemVer）的关联

Conventional Commits 的设计初衷之一是让提交历史可以被机器解析，自动推导下一个版本号：

- 仅有 `fix` 类型提交 → patch 版本递增
- 包含 `feat` 类型提交 → minor 版本递增
- 包含 `BREAKING CHANGE` footer 或 `!` 标记 → major 版本递增

这也是为什么 `rules/02-commit-messages.md` 强调"禁止无意义提交"——如果提交信息不能准确反映变更类型，自动化版本推导与 CHANGELOG 生成都会失真。

## 2. commit-msg Hook 实现讲解

`rules/02-commit-messages.md` §2 要求 pre-commit / commit-msg hook 不可绕过。以下是两种常见实现方式：

### 2.1 commitlint + husky（Node.js 生态）

安装：

```bash
npm install --save-dev @commitlint/cli @commitlint/config-conventional husky
```

配置 `commitlint.config.js`：

```js
module.exports = { extends: ['@commitlint/config-conventional'] };
```

用 husky 挂载 `commit-msg` hook（`.husky/commit-msg`）：

```bash
#!/usr/bin/env sh
npx --no -- commitlint --edit "$1"
```

`husky install` 会把这个脚本注册到 `.git/hooks/commit-msg`，提交信息格式不符时 commit 直接被拒绝，退出码非零。

### 2.2 纯 Shell 脚本（无 Node.js 依赖场景）

`.git/hooks/commit-msg`（需 `chmod +x`）：

```bash
#!/usr/bin/env sh
commit_msg_file="$1"
first_line=$(head -n1 "$commit_msg_file")

pattern='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9_-]+\))?!?: .+'

if ! echo "$first_line" | grep -qE "$pattern"; then
  echo "提交信息不符合 Conventional Commits 格式：$first_line"
  echo "期望格式：type(scope): description"
  exit 1
fi
```

### 2.3 为什么不能靠"团队自觉"代替 hook

`.git/hooks/` 下的脚本不会被 Git 提交追踪（默认不进版本库），团队成员本地环境不一致时容易出现"有人装了 hook 有人没装"的情况。**必须**级要求落地方式：

- 用 husky 之类的工具把 hook 脚本纳入版本控制并在 `npm install` 时自动挂载，或
- CI 侧对已推送的提交信息做二次校验（即使本地 hook 被绕过，CI 仍会拦截），这一层是本地 hook 被 `--no-verify` 绕过后的兜底

## 3. 敏感信息扫描工具讲解

`rules/02-commit-messages.md` §3 要求 CI 集成 secret scanning。常见工具对比：

| 工具 | 定位 | 特点 |
|---|---|---|
| [gitleaks](https://github.com/gitleaks/gitleaks) | 开源 secret 扫描 CLI | 规则库丰富（覆盖各大云厂商密钥格式），可扫描工作区或完整 Git 历史，易接入 CI/pre-commit |
| [git-secrets](https://github.com/awslabs/git-secrets)（AWS Labs） | 面向 AWS 凭证的扫描工具 | 专注 AWS Access Key 等模式，规则集较窄，适合以 AWS 为主的技术栈 |
| [truffleHog](https://github.com/trufflesecurity/trufflehog) | 深度扫描 Git 历史 + 密钥有效性验证 | 除了模式匹配还会尝试验证密钥是否仍然有效（对已泄露但已失效的密钥可降低误报优先级） |
| GitHub 原生 secret scanning | 平台托管方案 | GitHub 仓库（含私有仓库企业版）内置，检测到已知服务商密钥格式会自动通知并可联动吊销 |

### 3.1 典型集成方式：CI + pre-commit 双层防护

```yaml
# .github/workflows/secret-scan.yml（示例）
name: secret-scan
on: [pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
```

pre-commit 侧（本地提交前拦截，减少污染历史的机会）：

```yaml
# .pre-commit-config.yaml（示例）
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

两层不是互斥关系：pre-commit 层拦截大多数误提交（更早发现、成本更低），CI 层是绕过本地 hook（如 clone 后未装 pre-commit，或 `--no-verify`）之后的最后防线——这与 `rules/02-commit-messages.md` §2 "CI 侧二次校验"是同一防护思路的延伸。

### 3.2 已泄露密钥的处理原则

无论用哪种工具检测到密钥泄露，处理顺序遵循 `rules/02-commit-messages.md` §3 的原则：**先轮换，再清理历史**。清理 Git 历史（如 `git filter-repo`、BFG Repo-Cleaner）只是减少该密钥在历史中被扫描到的次数，不能撤销"密钥已被暴露过"这一事实——只要密钥已推送到任何远程（即使私有仓库），就应视为已泄露。

## 4. AI 协作者标注

`rules/02-commit-messages.md` §1 要求提交中若有 AI 协作者须在提交信息中标注。这不是格式偏好，而是提交历史的可追溯性要求——`git blame`/`git log` 是团队回溯"这段代码为什么这样写、当时依据什么信息做的判断"的第一手工具，隐去 AI 参与事实会让后续排查者误判决策链路（例如误以为是人工逐行推敲的结果，而实际上是模型基于当时的上下文生成，可能存在模型幻觉或过时假设）。

### 4.1 标注格式：Git 原生 Co-Authored-By

Git/GitHub/GitLab 等平台原生支持的多作者标注方式是在提交信息末尾追加一个或多个 `Co-Authored-By` footer（与 `BREAKING CHANGE` 同属 footer，位置在提交信息最后，前面空一行）：

```
feat(auth): 新增基于 JWT 的登录接口

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
```

- 邮箱部分不要求是真实可达邮箱，`noreply@<厂商域名>` 是 GitHub 等平台的通行写法（与人类协作者用真实邮箱不同，AI 协作者没有可关联的真实身份邮箱）
- 一次提交有多个协作者（人类 + AI，或多个 AI 会话）时，每人一行 `Co-Authored-By`，不合并写在一行
- **名称必须写实际使用的模型**（如 `Claude Sonnet 5`、`Claude Opus 4.6`、`GPT-5` 等），不得写工具品牌名代替模型名（如笼统写 "Claude Code" 而不写具体模型），也不得照抄历史提交里的旧模型名——模型是随会话变化的，硬编码会导致标注失真

### 4.2 为什么用 Co-Authored-By 而非在 body 里写一句话说明

`Co-Authored-By` 是 Git 生态的**结构化**约定，而不是自由文本：

- GitHub/GitLab 等平台会解析这个 footer，把对应账号/名称展示在提交的 "Co-authored by" 区域，可见性高于淹没在长 body 里的一句话
- 结构化 footer 便于脚本化统计（如"本季度多少提交有 AI 参与"），自由文本描述做不到可靠的机器提取
- 与 `BREAKING CHANGE:` footer 是同一机制的一致用法，团队只需理解一套"footer 规则"，不必为 AI 标注发明新格式

### 4.3 常见误区

- **误区："AI 只是辅助，没有直接生成代码，不用标"**——只要提交内容（代码或文档）由 AI 生成或经 AI 大幅改写，即应标注；人类只是审阅通过、未逐行重写的场景同样算"AI 协作"
- **误区："标了 Co-Authored-By 会让人觉得代码质量不可靠"**——标注的是协作事实，不是质量声明；隐藏协作事实一旦被追查到（如模型行为异常需要溯源），信任成本远高于如实标注
- **误区："本地随手 commit，正式 PR 前再补标注"**——`Co-Authored-By` 应随提交本身产生，事后补写依赖记忆且容易遗漏；已推送的提交若发现漏标，只能用 `git commit --amend`（未推送）或说明性后续提交（已推送且不便改写历史时）补充，不能空等到 PR 阶段一次性回填
