# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 仓库概览

Unipus 官方 Claude Code 插件仓库，8 个领域插件提供企业级开发工具链。详细功能见 README.md。

**操作关键点：**
- 插件通过 `/plugin-name:skill-name` 调用
- unipus-devops-plugin 自动加载 SessionStart 和 Notification hooks
- unipus-fe-dev 是唯一的复合 skill（5 阶段工作流）

## 快速参考

### 目录结构

```
plugins/{plugin-name}/
├── skills/{skill-name}/SKILL.md    # Skill 定义
└── hooks/hooks.json                # Hooks 配置（可选）
```

### Skill 调用规则

- 简单 skill: `/plugin-name:skill-name`
- 复合 skill: `/plugin-name:skill-name:substep`

**复合 skill 参考：** `unipus:fe-dev` 是唯一的复合 skill（5 阶段工作流），详见 `plugins/unipus-frontend-plugin/skills/unipus-fe-dev/ARCHITECTURE.md`

### Hooks 配置

Hooks 自动加载自 `plugins/{plugin-name}/hooks/hooks.json`。当前启用：
- **SessionStart**: 显示技巧（unipus-devops-plugin）
- **Notification**: 权限通知（unipus-devops-plugin）

## 常见开发任务

这是一个插件集合仓库，不是可构建的项目。仓库层面没有构建/测试命令。

### 插件开发

创建或修改插件时：

1. **简单 skill**: 在 `plugins/{plugin}/skills/{skill-name}/` 中添加 `SKILL.md`
2. **复合 skill**: 遵循 `unipus-fe-dev` 模式创建嵌套结构（参见 ARCHITECTURE.md）
3. **Hooks**: 在 `hooks/hooks.json` 中定义，并在 `hooks/{event}/` 中添加可执行脚本

### 测试与验证

**测试 Skill 是否正确加载：**
```bash
# 在 Claude Code 中调用 skill 测试
/your-plugin:skill-name

# 检查 skill 文件语法（确保 frontmatter 正确）
head -20 plugins/{plugin-name}/skills/{skill-name}/SKILL.md
```

**验证 Hooks 配置：**
```bash
# 检查 hooks.json 配置
cat plugins/{plugin-name}/hooks/hooks.json

# 手动测试 SessionStart hook
bash plugins/unipus-devops-plugin/hooks/sessionstart/show-tip.sh

# 检查 hook 脚本权限（Linux/Mac）
ls -l plugins/unipus-devops-plugin/hooks/sessionstart/show-tip.sh
```

**验证 Marketplace 配置：**
```bash
# 检查 JSON 格式是否正确
cat .claude-plugin/marketplace.json | python -m json.tool

# 查看当前版本
grep '"version"' .claude-plugin/marketplace.json
```

### Marketplace 配置

插件元数据在 `.claude-plugin/marketplace.json` 中定义：

- 更改时更新 `version` 字段
- 将新插件添加到 `plugins[]` 数组
- 包含清晰的 `description` 突出关键特性（尤其是 hooks）

**版本管理规范：**
- **Patch (x.x.X)**: Bug 修复、文档更新、小幅改进（如本次 Windows 编码修复）
- **Minor (x.X.x)**: 新增插件、新增 skill、新功能
- **Major (X.x.x)**: 架构变更、破坏性更新、API 变化

更新版本号后提交：
```bash
# 修改 .claude-plugin/marketplace.json 中的 version
# 提交变更
git add .claude-plugin/marketplace.json
git commit -m "chore(marketplace): bump version to X.X.X"
```

## 关键文件

- `.claude-plugin/marketplace.json`: 插件仓库元数据和插件列表
- `plugins/unipus-frontend-plugin/skills/unipus-fe-dev/ARCHITECTURE.md`: 复合 skill 模式文档（参考实现）
- `plugins/unipus-devops-plugin/hooks/sessionstart/show-tip.sh`: SessionStart hook 实现（包含 Windows 编码修复）

## 故障排查

### Hooks 调试

**SessionStart hook 失败诊断：**

1. **检查环境变量：**
   ```bash
   # 确认 CLAUDE_PLUGIN_ROOT 是否设置
   echo $CLAUDE_PLUGIN_ROOT
   ```

2. **手动运行 hook 查看错误：**
   ```bash
   cd plugins/unipus-devops-plugin/hooks/sessionstart
   bash show-tip.sh
   ```

3. **Windows 编码问题：**
   - 症状：`'gbk' codec can't encode character` 错误
   - 原因：Windows 默认使用 GBK 编码，无法处理 emoji
   - 解决：已在 show-tip.sh 中添加 UTF-8 包装器（第 34-36 行）

4. **检查 tips.txt 和状态文件：**
   ```bash
   # 确认 tips.txt 存在
   ls -l plugins/unipus-devops-plugin/hooks/sessionstart/tips.txt
   
   # 查看状态文件（如果存在）
   cat plugins/unipus-devops-plugin/hooks/sessionstart/.tip-state.json
   ```

**Hooks 未加载：**

1. **检查 hooks.json 配置：**
   ```bash
   cat plugins/unipus-devops-plugin/hooks/hooks.json
   # 确保 JSON 格式正确，事件名小写
   ```

2. **检查脚本执行权限（Linux/Mac）：**
   ```bash
   chmod +x plugins/unipus-devops-plugin/hooks/sessionstart/show-tip.sh
   ```

### Skill 加载失败

**常见原因：**

1. **Frontmatter 格式错误：**
   ```bash
   # 检查 SKILL.md 前几行
   head -10 plugins/{plugin}/skills/{skill-name}/SKILL.md
   # 确保有 --- 包裹的 YAML frontmatter
   ```

2. **命名空间不匹配：**
   - 确保 skill 名称与文件路径一致
   - 简单 skill：`plugin:skill-name`
   - 复合 skill：`plugin:skill-name:substep`

3. **相对路径引用错误：**
   - 检查主 skill 中的子 skill 引用路径
   - 例如：`./skills/collect-inputs/SKILL.md`

## 重要说明

- **跨插件无重复 skills**: 每个插件专注于特定领域
- **Hooks 是可选的**: 目前仅 unipus-devops-plugin 使用 hooks
- **Skills 可以相互引用**: 封装的子 skills 使用相对路径，跨插件引用使用绝对命名空间
- **复合 skills 很少见**: 仅在有复杂多阶段工作流时使用（3个以上阶段，每个阶段 >200 行）
