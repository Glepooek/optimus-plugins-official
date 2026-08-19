# CLAUDE.md

本文件为 Claude Code 在此仓库中工作时提供指导。

## 仓库概览

自定义的 Claude Code 插件仓库，9 个领域插件提供企业级开发工具链。

各插件职责见 `.claude-plugin/marketplace.json` 的 `description` 字段。

**两层 skill，不要混淆：**

| 位置 | 性质 | 调用方式 |
|---|---|---|
| `plugins/*/skills/` | 对外发布的插件产物 | `/plugin-name:skill-name` |
| `.claude/skills/` | 仅本仓库维护自用，不发布 | `/skill-name`（无前缀） |

`.claude/skills/` 的 skill 需在 `.kiro/skills/` 保持同名符号链接镜像（`commit-cc-plugin` 会自动补齐）。

---

## 重要约束

- **跨插件无重复 skills**：每个插件专注特定领域，新功能前先确认无跨插件重叠
- **Skills 可相互引用**：子 skill 用相对路径，跨插件用绝对命名空间
- **复合 skills 很少见**：仅在 3 个以上阶段且每阶段 >200 行时使用
- **新 skill 上线前自检**：这个 skill 是「引导器」（指导用户/agent 完成某件事）还是「传感器」（校验/检测已有产物是否合规）？有没有配对的另一半（例如有生成类 skill 却没有对应的校验类 skill）？避免只造轮子不造刹车

---

## 开发规范

### Skill 调用规则

- 简单 skill：`/plugin-name:skill-name`
- 复合 skill：`/plugin-name:skill-name:substep`
- `optimus-fe-dev` 是唯一的复合 skill（5 阶段工作流），触发词：`/optimus-frontend-plugin:optimus-fe-dev`，详见 `plugins/optimus-frontend-plugin/skills/optimus-fe-dev/ARCHITECTURE.md`

---

## 本地测试

见 `test-locally` skill（`/test-locally` 触发）。

Python 脚本单元测试（**本机无 `pytest`，只能用 `unittest`**）：

```bash
python -m unittest discover -s .claude/skills/sync-cc-docs-to-youdaonote/scripts -p "test_*.py"
```

---

## 版本管理规则

| 变更路径 | 操作类型 | 版本升级 |
|---|---|---|
| `.claude/` 下任何文件 | 任意 | **不升级** |
| `plugins/` 下新增 skill/hook/command | 新增 | **Minor** `x.X.x` |
| `plugins/` 下更新/修复已有内容 | 更新 | **Patch** `x.x.X` |
| `plugins/` 下删除/重命名用户可见功能 | 删除 | **Major** `X.x.x` |

升级时编辑 `.claude-plugin/marketplace.json` 的 `version` 字段，随本次提交一并推送。**功能变了版本号不变 = 不完整交付**——必须主动检查并升版，不等用户提醒。

Minor/Major 升级建议先用 `darwin-skill` 对改动的 skill 评分，新分数不得低于改动前（不允许倒退），否则先修正再提交。

---

## Skill frontmatter 规范

Skill frontmatter / CHANGELOG 规范见 `.claude/rules/skill-authoring.md`（编辑 SKILL.md / CHANGELOG.md / AGENT.md 时自动加载）。

---

## 提交与推送（强制）

**必须**使用 `commit-cc-plugin` skill，禁止手动执行 git 工作流。说"提交"或"推上去"即可触发。

---

## 关键文件

| 文件 | 用途 |
|---|---|
| `.claude-plugin/marketplace.json` | 插件仓库元数据和版本号 |
| `plugins/optimus-frontend-plugin/skills/optimus-fe-dev/ARCHITECTURE.md` | 复合 skill 模式参考实现 |
| `.claude/rules/skill-authoring.md` | SKILL.md frontmatter / CHANGELOG 规范（按路径自动加载） |

**已被 gitignore 的目录（有意排除，非缺失）：** `.claude/skills/darwin-skill/`（评估产物）、`.remember/`、`.codegraph/`
