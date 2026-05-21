# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 仓库概览

这是 **Unipus 官方 Claude Code 插件仓库**，包含 8 个领域特定插件：

- **unipus-frontend-plugin**: React/Vue 开发、WPF XAML 性能优化、UI 设计规范
- **unipus-backend-plugin**: API 开发、后端架构、数据库设计
- **unipus-qa-plugin**: 测试用例设计、JMeter 脚本、UI 自动化、飞书测试管理
- **unipus-prd-plugin**: PRD 文档创建、优化和审查
- **unipus-feishu-plugin**: 飞书文档自动化（读取/写入/上传）
- **unipus-office-plugin**: Word、Excel、PowerPoint、PDF 生成和处理
- **unipus-devops-plugin**: Jenkins CI/CD、API 变更通知、应用初始化、项目分析。包含自动加载的 Hooks：SessionStart（278条技巧智能轮播）、Notification（Windows 权限通知）
- **unipus-mcp-servers**: MCP 服务器集成（GitHub Copilot、MasterGo、飞书项目）

## 架构设计

### 插件结构

```
plugins/
├── {plugin-name}/
│   ├── skills/              # 领域特定技能
│   │   └── {skill-name}/
│   │       └── SKILL.md
│   └── hooks/               # （可选）事件钩子
│       └── hooks.json
```

### Skill 命名约定

- **简单 skill**: `plugin-name:skill-name`（例如：`unipus:fe-dev`）
- **复合 skill**: `plugin-name:skill-name:substep`（例如：`unipus:fe-dev:collect-inputs`）

使用**冒号分隔的命名空间**表达逻辑层次关系，而非文件路径。

### 复合 Skill 模式

**unipus-fe-dev** 是本仓库中**唯一的复合 skill**，作为参考实现。

复合 skill 是一个**工作流编排器**，协调多个子 skills：

```
unipus-fe-dev/                          # 主 skill（编排器）
├── SKILL.md                            # 入口点
├── README.md                           # 用户指南
├── ARCHITECTURE.md                     # 架构文档
└── skills/                             # ⭐ 子 skills（嵌套结构）
    ├── collect-inputs/                 # 阶段 1
    ├── analyze-and-plan/               # 阶段 2
    ├── generate-code/                  # 阶段 3
    ├── generate-deliverables/          # 阶段 4
    ├── verify-and-finish/              # 阶段 5
    ├── coding-standards/               # 全局规范
    ├── architecture-doc/               # 辅助工具
    └── feishu-doc/                     # 辅助工具
```

**关键特性：**
- 主 skill 使用**相对路径**引用子 skills：`./skills/{substep}/SKILL.md`
- 子 skills **封装**在复合 skill 目录内
- 整个 `unipus-fe-dev/` 目录可以作为**单一单元**移动
- 子 skills 使用命名空间格式：`unipus:fe-dev:{substep}`

**为什么使用嵌套结构？**
- 强制独立 skills 与复合 skills 之间的清晰边界
- 保持逻辑封装（可以复制整个目录而不破坏引用）
- 避免用内部组件污染顶层 skills/ 命名空间

**参考文档：** 详见 `plugins/unipus-frontend-plugin/skills/unipus-fe-dev/ARCHITECTURE.md` 了解完整的设计原理和实现细节。

### Hooks 系统

Hooks 在 `plugins/{plugin-name}/hooks/hooks.json` 中定义时**自动加载**：

```json
{
  "sessionstart": ["show-tip.sh"],
  "notification": ["notify.sh"]
}
```

- **SessionStart hook**: 从 `tips.txt` 显示轮播技巧（278条技巧通过 `.tip-state.json` 追踪）
- **Notification hook**: Windows 权限通知
- Hooks 支持 **CLAUDE_PLUGIN_ROOT** 环境变量用于插件相对路径

**Windows 编码注意事项：** SessionStart hook 使用 UTF-8 包装器处理 Windows GBK 系统上的 emoji。

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
