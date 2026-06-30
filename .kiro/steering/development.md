# 开发规范

## 版本管理

### 仓库版本（marketplace.json）

| 变更路径 | 操作类型 | 版本升级 |
|----------|----------|----------|
| `.claude/` 下任何文件 | 任意 | 不升级 |
| `plugins/` 下新增 skill/hook/command | 新增 | Minor `x.X.x` |
| `plugins/` 下更新/修复已有内容 | 更新 | Patch `x.x.X` |
| `plugins/` 下删除/重命名用户可见功能 | 删除 | Major `X.x.x` |

### Skill 级版本（SKILL.md frontmatter）

每个 Skill 维护独立语义版本：

```yaml
---
name: my-skill
version: 1.2.0
description: ...
---
```

| 变更类型 | 升级 |
|----------|------|
| 新增功能/章节/参数 | Minor |
| 修改/修复/重构/文档优化 | Patch |
| 接口不兼容、删除用户可见功能 | Major |

### CHANGELOG.md

每个 Skill 目录必须有 CHANGELOG.md，提交前必须更新：

```markdown
## [版本号] - YYYY-MM-DD

### Added
- 新增的功能或章节

### Changed
- 修改的内容

### Fixed
- 修复的问题
```

## Git 提交规范

### 强制规则

- **必须使用 `commit-cc-plugin` Skill 进行提交**，禁止手动 git 工作流
- 说"提交"或"推上去"即可触发
- 遵循 Conventional Commits 格式
- 禁止 `git add -A`，必须逐文件暂存
- 禁止 `git push --force` 和 `--no-verify`
- 直接推送到 master 分支

### 提交消息格式

```
<类型>(<scope>): <简明摘要>

- <具体变更>
- <具体变更>

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
```

**类型**：`feat` / `fix` / `docs` / `refactor` / `chore` / `perf`

**scope 示例**：`devops-hooks`、`office-plugin`、`marketplace`、`sync-cc-tips`

## Skill 开发规范

### 新建 Skill

1. 在对应 `plugins/{plugin-name}/skills/` 下创建目录
2. 编写 SKILL.md（含 frontmatter：name, version, description）
3. 创建 CHANGELOG.md（初始版本 `[1.0.0]`）
4. 在 `.claude-plugin/marketplace.json` 中确认插件已注册
5. 提交时版本升级为 Minor

### Skill 调用规则

- 简单 Skill：`/plugin-name:skill-name`
- 复合 Skill：`/plugin-name:skill-name:substep`
- 唯一复合 Skill：`/unipus-frontend-plugin:unipus-fe-dev`（5阶段工作流）

### 跨插件约束

- 每个插件专注特定领域，无跨插件重复 Skills
- Skills 可相互引用：子 skill 用相对路径，跨插件用绝对命名空间
- 复合 Skills 只在 3+ 阶段且每阶段 >200 行时使用

## 本地测试

修改任何 skill/hook/command 后，使用 `--plugin-dir` 加载测试：

```bash
# 完整测试
claude --plugin-dir "F:\unipus-plugins-official"

# 单插件测试
claude --plugin-dir "F:\unipus-plugins-official\plugins\unipus-devops-plugin"
```

文件改动立即生效，无需重启或重装。
