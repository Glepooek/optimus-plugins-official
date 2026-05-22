# Claude Code Skill 工作流最佳实践

通用的 Claude Code skill 使用指南，适用于任何软件开发项目。

---

## 📖 目录

- [核心工作流场景](#-核心工作流场景)
- [Skill 使用技巧](#-skill-使用技巧)
- [Superpowers 深度指南](#-superpowers-深度指南)
- [跨 Skill 协作模式](#-跨-skill-协作模式)
- [团队协作最佳实践](#-团队协作最佳实践)
- [常见陷阱与规避策略](#️-常见陷阱与规避策略)
- [高级配置](#-高级配置)
- [效率提升技巧](#-效率提升技巧)

---

## 🎯 核心工作流场景

### 场景 1: 修复复杂 Bug

```bash
# 1. 系统化定位问题根源
/superpowers:systematic-debugging

# 2. 修改代码...

# 3. 确认修复生效（运行实际命令验证）
/superpowers:verification-before-completion

# 4. 生成规范的 commit message
/commit-commands:commit
```

**关键原则：**
- 重现问题（100% 复现率）
- 最小化复现步骤
- 假设验证（科学方法）
- 写回归测试防止复发

### 场景 2: 大规模重构

```bash
# 1. 规划重构方案
/superpowers:brainstorming
/superpowers:writing-plans

# 2. 创建隔离工作树
/superpowers:using-git-worktrees

# 3. TDD 驱动重构
/superpowers:test-driven-development

# 4. 应用 Karpathy 原则避免过度复杂化
/andrej-karpathy-skills:karpathy-guidelines

# 5. 增量提交
/commit-commands:commit "重构模块A - 提取公共逻辑"
/commit-commands:commit "重构模块B - 简化接口"

# 6. 代码审查
/code-review --effort max

# 7. 验证功能完整性
/verify

# 8. 创建 PR
/commit-commands:commit-push-pr
```

**关键原则：**
- **小步快跑**：每次重构一个小模块
- **测试先行**：确保有测试覆盖
- **保持可运行**：每次提交后代码都能运行
- **避免混合**：重构和功能开发分开

### 场景 3: TDD 开发新功能

```bash
# 1. 头脑风暴功能需求
/superpowers:brainstorming

# 2. TDD 流程
/superpowers:test-driven-development

# 流程：
# - RED: 先写失败的测试
# - GREEN: 写最简代码让测试通过
# - REFACTOR: 重构优化代码

# 3. 验证测试覆盖
/superpowers:verification-before-completion

# 4. 代码审查
/code-review --effort medium

# 5. 提交
/commit-commands:commit
```

**TDD 黄金法则：**
- 测试先行，代码后行
- 小步迭代，频繁运行
- 只写让测试通过的代码
- 重构时保持测试绿灯

### 场景 4: 团队协作和 PR 审查

**作为 PR 作者：**

```bash
# 1. 完成开发后请求审查
/superpowers:requesting-code-review

# 2. 自我审查
/code-review --effort high --comment

# 3. 创建 PR
/commit-commands:commit-push-pr

# 4. 生成 PR 描述（自动）
# PR 描述包含：
# - 功能摘要
# - 测试计划
# - 截图/演示（如适用）
```

**作为 PR 审查者：**

```bash
# 1. 拉取 PR 代码
git fetch origin pull/123/head:pr-123
git checkout pr-123

# 2. 系统化审查
/code-review --effort high

# 3. 特定领域审查（根据语言选择）
# C#: /unipus:csharp-code-review
# 其他语言: 使用对应的 code-review skill

# 4. 实际运行验证
/verify

# 5. 提供反馈
/superpowers:receiving-code-review
```

### 场景 5: CI/CD 集成与监控

```bash
# 1. 触发构建（根据你的 CI 系统）
# Jenkins: /unipus:ci-jenkins-build myproject-build
# GitHub Actions: gh workflow run
# 其他 CI: 对应的命令

# 2. 监控构建状态（定期轮询）
/loop 2m "检查 CI 构建状态"

# 3. 构建失败时调试
/superpowers:systematic-debugging

# 4. 停止监控
/loop stop
```

**CI/CD 最佳实践：**
- 每次 push 前本地运行测试
- 使用 loop 监控长时间构建
- 构建失败立即修复，不累积
- API 变更及时通知下游团队

### 场景 6: 性能调优完整流程

```bash
# 1. 性能分析
# .NET: /dotnet-diag:analyzing-dotnet-performance
# 其他语言: 使用对应的性能分析工具

# 2. 特定场景优化
# WPF: /wpf-xaml-performance
# 其他场景: 使用对应的优化 skill

# 3. 创建基准测试
# .NET: /dotnet-diag:microbenchmarking
# 其他语言: 使用对应的 benchmark 工具

# 4. 应用优化后对比
# 记录优化前后的性能指标

# 5. 验证优化效果
/verify --focus performance

# 6. 文档化优化方案
# 记录优化前后的性能指标
```

**性能优化金字塔：**
```
           算法优化
         /          \
    数据结构优化    编译器优化
   /                            \
代码级优化                    硬件优化
```

从上往下优化，收益递减。

### 场景 7: 并行任务处理

```bash
# 使用并行 agent 处理独立任务
/superpowers:dispatching-parallel-agents

# 或在单会话中使用 subagent 驱动开发
/superpowers:subagent-driven-development
```

**适用场景：**
- 前后端独立开发
- 多个独立模块并行实现
- 文档和代码同步编写
- 测试和实现并行

**注意事项：**
- 任务必须真正独立（无共享状态）
- 避免假并行（实际有依赖）
- 明确每个 agent 的职责边界

### 场景 8: 跨项目代码迁移

```bash
# 1. 分析源项目结构
# 使用项目分析工具了解结构

# 2. 规划迁移方案
/superpowers:writing-plans

# 3. 隔离工作环境
/superpowers:using-git-worktrees

# 4. 增量迁移 + 测试
/superpowers:test-driven-development

# 5. 验证迁移完整性
/verify --scope migration

# 6. 文档化差异
# 记录不兼容的部分和手动修改
```

---

## 💡 Skill 使用技巧

### 技巧 1: 防御性提交（三重检查）

```bash
/code-review --effort high
/superpowers:verification-before-completion
# 可选：语言特定的 code-review skill
```

### 技巧 2: code-review 生成 PR 评论

```bash
# 直接生成 PR 内联评论
/code-review --effort high --comment
```

生成的评论可以直接粘贴到 GitHub PR 中。

### 技巧 3: fewer-permission-prompts

```bash
# 自动扫描会话记录，生成权限白名单
/fewer-permission-prompts
```

### 技巧 4: loop 定期任务

```bash
# 每5分钟检查 CI 状态
/loop 5m "检查 CI 构建状态"

# 每10分钟检查 PR 状态
/loop 10m "检查所有未合并的 PR 状态"

# 停止定期任务
/loop stop
```

### 技巧 5: remember 跨会话状态保存

```bash
# 会话结束前保存状态
/remember:remember
```

**使用场景：**
- 长期任务中途需要休息
- 切换到其他项目后需要回来
- 保存复杂的调试进度

**保存内容：**
- 当前工作状态（完成了什么、未完成什么）
- 下一步计划（优先级顺序）
- 非显而易见的上下文（坑点、偏好）

### 技巧 6: update-config 高级配置

```bash
# 自动添加权限白名单
/update-config allow "Bash(dotnet *)"

# 设置环境变量
/update-config env ANTHROPIC_BASE_URL=http://your-proxy.com/

# 配置 hooks
/update-config hook PostToolUse "eslint --fix"

# 查看当前配置
/update-config show
```

### 技巧 7: verify 实战验证

```bash
# 验证 PR 修改是否符合预期
/verify

# 验证修复是否生效
/verify --focus bug-fix

# 验证功能完整性
/verify --scope feature-complete
```

**最佳实践：**
- 在声称"完成"前使用
- 与 verification-before-completion 结合
- 运行实际应用程序验证，不仅仅是测试

### 技巧 8: Git Worktree 隔离开发

```bash
# 创建独立工作树
/superpowers:using-git-worktrees

# 在隔离环境中开发新功能
# 不影响主工作区
# 可以同时处理多个功能分支

# 完成后决定如何集成
/superpowers:finishing-a-development-branch
```

**使用场景：**
- 需要同时开发多个独立功能
- 实验性功能开发
- 紧急 hotfix 不影响当前开发

---

## 🎓 Superpowers 深度指南

### superpowers:brainstorming 深度使用

**何时使用：**
- ✅ 需求不明确时
- ✅ 有多种实现方案时
- ✅ 涉及架构决策时
- ❌ 需求已经非常明确
- ❌ 简单的 bug 修复

**提问技巧：**
```
用户：添加用户登录功能

Claude 会探索：
- 认证方式？JWT / Session / OAuth？
- 存储方式？Cookie / LocalStorage / Memory？
- 安全要求？2FA / 密码强度 / 加密方式？
- 用户体验？记住我 / 自动登录 / SSO？
```

**输出期望：**
- 3-5 个可行方案
- 每个方案的优缺点
- 推荐方案及理由
- 潜在风险和缓解措施

### superpowers:writing-plans 深度使用

**计划粒度：**
- **粗粒度**：适合探索性任务
- **细粒度**：适合明确任务

**计划模板：**
```markdown
# 实施计划：添加用户登录功能

## 目标
实现基于 JWT 的用户登录认证系统

## 前置条件
- [ ] 数据库已有 users 表
- [ ] 已安装 JWT 库

## 步骤
1. **后端 API**（预计 2h）
   - [ ] 创建 /api/auth/login 端点
   - [ ] 实现密码哈希验证
   - [ ] 生成 JWT token
   - [ ] 添加单元测试

2. **前端集成**（预计 1.5h）
   - [ ] 创建 Login 组件
   - [ ] 实现表单验证
   - [ ] 集成 API 调用
   - [ ] 添加错误处理

3. **中间件**（预计 1h）
   - [ ] 创建 JWT 验证中间件
   - [ ] 实现 token 刷新逻辑
   - [ ] 添加权限检查

## 验收标准
- [ ] 用户可以成功登录
- [ ] Token 过期后自动刷新
- [ ] 所有测试通过
- [ ] 代码审查通过

## 风险
- Token 存储安全性 → 使用 HttpOnly Cookie
- XSS 攻击风险 → 输入验证 + CSP
```

### superpowers:verification-before-completion 深度使用

**验证层级：**

1. **语法层**：代码能编译/解析
2. **单元层**：单元测试通过
3. **集成层**：集成测试通过
4. **功能层**：功能符合需求
5. **性能层**：性能指标达标
6. **安全层**：无安全漏洞

**实战检查清单：**

```bash
# 1. 编译检查（根据语言）
# C#: dotnet build
# Java: mvn compile
# Python: python -m py_compile
# JavaScript: npm run build

# 2. 单元测试
# 根据你的测试框架运行

# 3. 代码审查
/code-review --effort high

# 4. 功能验证
/verify

# 5. 性能验证（如适用）
# 运行性能测试

# 6. 安全验证（如适用）
/security-review

# 全部通过后才能声称"完成"
```

### superpowers:systematic-debugging 深度使用

**系统化调试流程：**

```
1. 重现问题（100% 复现率）
   ↓
2. 最小化复现步骤（减少变量）
   ↓
3. 隔离问题（二分法定位）
   ↓
4. 假设验证（科学方法）
   ↓
5. 修复 + 测试（确认修复）
   ↓
6. 回归测试（确保无副作用）
```

**调试工具箱：**

```bash
# .NET 调试
/dotnet-diag:dump-collect          # 崩溃转储
/dotnet-diag:dotnet-trace-collect  # 性能追踪

# 通用调试
/superpowers:systematic-debugging

# 日志分析
grep -r "ERROR" logs/ | tail -100

# 网络调试
curl -v http://api.example.com/endpoint
```

**常见反模式（避免）：**
- ❌ 随机修改代码试试看
- ❌ 不重现就开始修复
- ❌ 一次改多个地方
- ❌ 不写回归测试

### superpowers:test-driven-development 深度使用

**TDD 循环：**
```
RED → GREEN → REFACTOR → RED → ...
```

**各阶段要点：**

**RED 阶段：**
- 先写测试，必须失败
- 测试要具体、可验证
- 一次只写一个测试

**GREEN 阶段：**
- 写最简单的代码让测试通过
- 不追求完美，先让它工作
- 快速迭代

**REFACTOR 阶段：**
- 保持测试绿灯
- 消除重复
- 改进设计
- 提高可读性

### superpowers:requesting-code-review 深度使用

**请求审查前的自查清单：**

```bash
# 1. 自我审查
/code-review --effort high

# 2. 运行所有测试
# 根据你的项目运行测试

# 3. 检查代码规范
# 使用对应语言的 linter

# 4. 功能验证
/verify

# 5. 性能检查（如适用）
# 运行性能测试

# 6. 安全检查（如适用）
/security-review

# 7. 文档更新
# 确保 README、API 文档等已更新

# 8. 提交信息规范
# 使用 conventional commits 格式
```

**PR 描述模板：**

```markdown
## 摘要
简要说明这个 PR 做了什么（1-2句话）

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] 性能优化

## 变更详情
### 添加
- 添加了 XXX 功能
- 添加了 YYY 测试

### 修改
- 修改了 ZZZ 逻辑

### 删除
- 删除了过期的 AAA 代码

## 测试计划
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试场景 1
- [ ] 手动测试场景 2

## 截图（如适用）
<插入截图>

## 相关 Issue
Closes #123

## 审查重点
请特别关注：
- XXX 模块的性能影响
- YYY 接口的向后兼容性
```

### superpowers:receiving-code-review 深度使用

**收到审查反馈后：**

1. **先理解，不要急于反驳**
   - 审查者可能看到你没看到的问题
   - 提问澄清而非立即否定

2. **技术验证**
   ```bash
   # 对可疑建议进行验证
   /superpowers:receiving-code-review
   ```

3. **分类处理**
   - **立即修复**：明确的 bug、安全问题
   - **讨论优化**：设计争议、性能权衡
   - **技术债**：可以单独 issue 跟踪

4. **回复规范**
   - ✅ "已修复，commit abc123"
   - ✅ "好建议，已优化"
   - ✅ "已创建 issue #456 跟踪"
   - ❌ "懂了"（无具体行动）
   - ❌ "这样也行"（含糊其辞）

---

## 🔗 跨 Skill 协作模式

### 模式 1: 研发全流程自动化

```
需求 → 设计 → 开发 → 测试 → 审查 → 发布
  ↓       ↓       ↓       ↓       ↓       ↓
brainstorm → writing-plans → TDD → verification → code-review → commit-push-pr
```

**端到端流程：**

```bash
# 阶段 1: 需求探索（10分钟）
/superpowers:brainstorming

# 阶段 2: 方案设计（15分钟）
/superpowers:writing-plans

# 阶段 3: TDD 开发（1-2小时）
/superpowers:test-driven-development

# 阶段 4: 验证（10分钟）
/superpowers:verification-before-completion

# 阶段 5: 审查（10分钟）
/code-review --effort high

# 阶段 6: 发布（5分钟）
/commit-commands:commit-push-pr
```

### 模式 2: 代码质量保障体系

```
编码规范 → 自动化测试 → 代码审查 → 持续监控
    ↓           ↓            ↓           ↓
karpathy → TDD+verification → code-review → CI/CD
```

**多层防御：**

1. **开发阶段**：Karpathy guidelines 避免复杂化
2. **提交前**：TDD + verification 确保功能正确
3. **PR 阶段**：code-review + domain-review
4. **合并后**：CI 自动运行测试 + 性能监控

### 模式 3: 性能优化闭环

```
发现 → 分析 → 优化 → 验证 → 监控
  ↓      ↓      ↓      ↓      ↓
trace → analyzing → apply → verify → loop-monitor
```

**完整流程：**

```bash
# 1. 发现性能问题
# 使用性能分析工具

# 2. 分析瓶颈
# 使用对应语言的性能分析 skill

# 3. 应用优化
# 使用对应的优化 skill

# 4. 验证改进
/verify --focus performance

# 5. 持续监控
/loop 30m "检查性能指标"
```

---

## 🏆 团队协作最佳实践

### 1. 代码审查文化

**快速审查原则（LGTM）：**
- **L**ook：仔细查看每一行
- **G**et：理解代码意图
- **T**est：确认测试覆盖
- **M**erge：满足标准后合并

**审查重点分级：**

| 优先级 | 审查内容 | 工具 |
|--------|---------|------|
| P0 | 功能正确性、安全漏洞 | verify, security-review |
| P1 | 代码规范、可维护性 | code-review |
| P2 | 性能影响、资源泄漏 | 性能分析工具 |
| P3 | 代码风格、命名 | karpathy-guidelines |

### 2. PR 管理策略

**PR 大小控制：**
- 🟢 小 PR（<200 行）：30分钟内审查
- 🟡 中 PR（200-500 行）：1-2小时审查
- 🔴 大 PR（>500 行）：拆分或安排专门审查时间

**PR 标签系统：**
```
🚀 feature  - 新功能
🐛 bugfix   - Bug修复
♻️ refactor - 重构
📝 docs     - 文档
⚡ perf     - 性能优化
🔒 security - 安全修复
```

### 3. 知识沉淀机制

**文档金字塔：**
```
      决策记录 (ADR)
     /              \
  API文档          架构文档
 /                          \
代码注释                  CLAUDE.md
```

**自动化文档生成：**

```bash
# 初始化项目文档
/init

# 更新文档（根据项目类型）
# 使用对应的文档生成工具
```

---

## ⚠️ 常见陷阱与规避策略

### 陷阱 1: 过早优化

**症状：**
- 在需求不明确时就开始优化性能
- 添加不必要的抽象层
- 过度设计

**规避：**
```bash
# 1. 先让功能工作
/superpowers:test-driven-development

# 2. 检查是否过度复杂化
/andrej-karpathy-skills:karpathy-guidelines

# 3. 基于实际瓶颈优化
# 使用性能分析工具
```

### 陷阱 2: 测试覆盖不足

**症状：**
- "看起来能工作"就提交
- 缺少边界情况测试
- 没有回归测试

**规避：**
```bash
# 强制验证流程
/superpowers:verification-before-completion

# TDD 确保测试先行
/superpowers:test-driven-development

# 代码审查检查测试
/code-review --effort high
```

### 陷阱 3: 技术债累积

**症状：**
- "先这样，以后再重构"
- 复制粘贴代码
- 硬编码配置

**规避：**
```bash
# 定期重构
/superpowers:brainstorming "如何重构模块X"

# 遵循最佳实践
/andrej-karpathy-skills:karpathy-guidelines

# 代码质量门禁
/code-review --effort max
```

### 陷阱 4: 合并冲突地狱

**症状：**
- 长期不合并的分支
- 多个分支修改相同文件
- 大规模重构与功能开发冲突

**规避：**
```bash
# 使用 worktree 隔离
/superpowers:using-git-worktrees

# 小步快跑
# 每完成一个小功能就合并

# 定期同步主分支
git fetch origin
git rebase origin/main
```

---

## 🔧 高级配置

### settings.json 核心配置

**基础配置示例：**

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Grep",
      "Glob",
      "Bash(git *)",
      "Bash(ls *)",
      "Bash(pwd)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force *)",
      "Bash(sudo *)"
    ]
  },
  "model": "sonnet[1m]",
  "outputStyle": "Explanatory"
}
```

**权限模式：**

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `auto` | 自动批准安全操作 | 日常开发 |
| `dontAsk` | 不提示，全自动 | CI/CD |
| `default` | 每次都询问 | 学习阶段 |

### Hooks 基础配置

**常用 Hooks：**

```json
{
  "postToolUse": [{
    "name": "auto-format",
    "command": "your-formatter",
    "filter": {"tool": "Write"}
  }]
}
```

**Hook 过滤器：**

```json
{
  "filter": {
    "tool": "Write",           // 只在 Write 工具后触发
    "glob": "**/*.ext",        // 只处理特定文件类型
    "exitCode": 0              // 只在工具成功时触发
  }
}
```

---

## 📈 效率提升技巧

### 1. 快捷键组合

```bash
# Ctrl+L: 重新生成响应
# Ctrl+O: 切换详细/焦点视图
# Ctrl+U: 清空输入
# /fast: 切换快速模式
# /focus: 切换焦点模式
```

### 2. 命令别名

在 `~/.bashrc` 或 `~/.zshrc` 中：

```bash
alias cr='/code-review --effort high'
alias v='/verify'
alias c='/commit-commands:commit'
alias pr='/commit-commands:commit-push-pr'
```

### 3. 批处理命令

```bash
# 一次性运行多个检查
/code-review --effort high && \
/superpowers:verification-before-completion
```

### 4. 会话保存习惯

**每个会话结束前：**
```bash
/remember:remember
```

**每个重要节点：**
- 完成一个大功能
- 遇到复杂问题需要暂停
- 切换到其他项目前

---

## 🎯 通用工作流模板

### 功能开发标准流程

```bash
# 1. 需求分析
/superpowers:brainstorming

# 2. 方案设计
/superpowers:writing-plans

# 3. 隔离开发（可选）
/superpowers:using-git-worktrees

# 4. TDD 开发
/superpowers:test-driven-development

# 5. 代码审查
/code-review --effort high

# 6. 功能验证
/verify

# 7. 提交 PR
/commit-commands:commit-push-pr
```

### Bug 修复标准流程

```bash
# 1. 系统化调试
/superpowers:systematic-debugging

# 2. 编写回归测试
# 确保 bug 不会再次出现

# 3. 修复代码

# 4. 验证修复
/superpowers:verification-before-completion

# 5. 代码审查
/code-review --effort medium

# 6. 提交
/commit-commands:commit
```

### 重构标准流程

```bash
# 1. 规划重构范围
/superpowers:brainstorming
/superpowers:writing-plans

# 2. 确保测试覆盖
# 重构前必须有测试

# 3. 小步重构
# 每次只重构一小部分

# 4. 运行测试
# 每次重构后立即运行测试

# 5. 代码审查
/code-review --effort high

# 6. 提交
/commit-commands:commit
```

---

## 📚 相关资源

- **Claude Code 官方文档**: https://docs.anthropic.com/claude/docs/claude-code
- **Conventional Commits**: https://www.conventionalcommits.org/
- **TDD 最佳实践**: https://martinfowler.com/bliki/TestDrivenDevelopment.html
- **代码审查指南**: https://google.github.io/eng-practices/review/

---

**最后更新：** 2026/05/22
**适用范围：** 所有使用 Claude Code 的软件开发项目
