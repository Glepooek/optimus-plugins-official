# unipus:fe-dev - 复合 Skill 架构设计

> **Version:** 1.1.0  
> **Last Updated:** 2026-05-08  
> **Target Audience:** 插件开发者、架构设计师、维护者

---

## 概述

`unipus:fe-dev` 是一个**复合 skill**（Composite Skill），它不同于普通的单一功能 skill，而是一个**工作流编排器**（Workflow Orchestrator），通过协调多个子 skills 来完成复杂的前端全流程开发任务。

### 什么是复合 Skill？

**普通 skill**：
- 解决单一问题（如"优化 WPF 性能"、"生成 Word 文档"）
- 单一入口、单一职责
- 通常 <500 行代码

**复合 skill**：
- 编排多个步骤形成完整工作流
- 每个步骤由独立的子 skill 实现
- 主 skill 负责流程控制和状态管理
- 子 skills 可以被选择性复用

### 为什么需要复合 Skill？

前端开发不是单一操作，而是一个**从需求到交付的完整链路**：

```
PRD + 设计稿 + API 文档 
    ↓
需求分析 + 技术栈探测 
    ↓
任务拆分 + 实施规划
    ↓
代码生成（组件/接口/类型/埋点）
    ↓
测试交付物生成
    ↓
验证 + 完成
```

这个链路的复杂性：
- **4 种输入验证**：PRD、架构文档、设计稿、API 文档
- **技术栈自动探测**：React/Vue、状态管理、UI 组件库、埋点 SDK
- **代码风格学习**：匹配项目现有代码风格
- **Subagent 驱动生成**：并行生成多个文件，双阶段 review
- **标准化交付物**：功能说明书、接口清单、状态清单、Mock 数据

单一 skill 无法胜任（会导致 >2000 行的单文件），复合 skill 将这些能力**模块化**并**工作流化**。

---

## 架构设计

### 目录结构

```
unipus-fe-dev/                          # 复合 skill 根目录
├── SKILL.md                            # 主 skill（工作流编排器）
├── README.md                           # 用户使用手册
├── ARCHITECTURE.md                     # 本文档：架构设计说明
├── docs/                               # 文档目录
│   └── user-guide.md                   # 详细用户指南
└── skills/                             # ⭐ 子 skills 目录（关键设计）
    ├── collect-inputs/                 # 阶段 1：收集输入
    │   └── SKILL.md
    ├── analyze-and-plan/               # 阶段 2：分析规划
    │   └── SKILL.md
    ├── generate-code/                  # 阶段 3：代码生成
    │   ├── SKILL.md
    │   └── references/
    │       ├── implementer-prompt.md   # Subagent 实施者 prompt
    │       └── spec-reviewer-prompt.md # Spec reviewer prompt
    ├── generate-deliverables/          # 阶段 4：生成交付物
    │   └── SKILL.md
    ├── verify-and-finish/              # 阶段 5：验证完成
    │   └── SKILL.md
    ├── architecture-doc/               # 前置工具：生成架构文档
    │   ├── SKILL.md
    │   └── references/
    │       └── sensors-chapter-template.md
    ├── feishu-doc/                     # 前置工具：飞书文档读写
    │   └── SKILL.md
    └── coding-standards/               # 基础规范（全局生效）
        ├── SKILL.md
        └── references/
            ├── tech-stack.md           # 技术栈清单
            ├── directory-structure.md  # 目录结构规范
            ├── api-request.md          # API 层规范
            ├── api-data-types.md       # 数据类型规范
            ├── design-tokens.md        # Design tokens
            └── sensors-config.md       # 埋点规范（神策 SDK）
```

### 命名空间设计

使用**冒号分隔的命名空间**来组织主 skill 和子 skills：

| Skill 路径 | 命名空间 | 类型 | 说明 |
|-----------|---------|------|------|
| `./SKILL.md` | `unipus:fe-dev` | 主 skill | 工作流编排器 |
| `./skills/collect-inputs/SKILL.md` | `unipus:fe-dev:collect-inputs` | 子 skill | 阶段 1 |
| `./skills/analyze-and-plan/SKILL.md` | `unipus:fe-dev:analyze-and-plan` | 子 skill | 阶段 2 |
| `./skills/generate-code/SKILL.md` | `unipus:fe-dev:generate-code` | 子 skill | 阶段 3 |
| `./skills/coding-standards/SKILL.md` | `unipus:fe-dev:coding-standards` | 基础规范 | 全局生效 |
| `./skills/architecture-doc/SKILL.md` | `unipus:fe-dev:architecture-doc` | 前置工具 | 按需调用 |

**命名空间规则：**
- 使用冒号 `:` 而非斜杠 `/` 表示逻辑从属关系
- 主 skill 使用 `plugin:skill` 格式
- 子 skills 使用 `plugin:skill:substep` 格式
- 命名空间独立于文件系统路径，更灵活

**为什么使用冒号？**
```
✅ 命名空间：unipus:fe-dev:collect-inputs
   - 表示逻辑从属关系（collect-inputs 属于 fe-dev）
   - 可以映射到任意文件路径
   - 便于重构和移动

❌ 路径：plugins/unipus-frontend-plugin/skills/unipus-fe-dev/skills/collect-inputs
   - 表示物理存储位置
   - 路径变化会破坏引用
   - 不表达逻辑关系
```

### 引用机制

主 skill 通过**相对路径**引用子 skills：

```markdown
## 子 Skill 引用

| 阶段 | 子 Skill | 版本 | 路径 |
|------|---------|------|------|
| 基础规范 | `unipus:fe-dev:coding-standards` | 1.0.0 | `./skills/coding-standards/SKILL.md` |
| 1. 收集输入 | `unipus:fe-dev:collect-inputs` | 1.0.0 | `./skills/collect-inputs/SKILL.md` |
| 2. 分析规划 | `unipus:fe-dev:analyze-and-plan` | 1.0.0 | `./skills/analyze-and-plan/SKILL.md` |
```

**相对路径的优势：**
1. **封装性**：整个 unipus-fe-dev 目录可以作为一个单元移动
2. **版本化**：主 skill 和子 skills 可以独立升级版本
3. **易于测试**：可以在隔离环境测试单个子 skill
4. **避免硬编码**：不依赖绝对路径或特定目录结构

---

## 工作流设计

### 5 阶段架构图

```
┌─────────────────────────────────────────────────────────┐
│  unipus:fe-dev (主 skill)                               │
│  职责：工作流编排、状态管理、用户交互                       │
│  文件：./SKILL.md                                        │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│ 阶段 1：收集输入   │          │  前置工具         │
│ collect-inputs   │          │  architecture-doc │
│                  │          │  feishu-doc       │
│ 验证 4 种输入     │          └──────────────────┘
└──────────────────┘
        ↓
┌──────────────────┐
│ 阶段 2：分析规划   │ ← 引用 coding-standards
│ analyze-and-plan │   (识别技术栈、学习风格)
│                  │
│ 探测技术栈        │
│ 生成实施计划      │
└──────────────────┘
        ↓
┌──────────────────┐
│ 阶段 3：代码生成   │ ← 引用 coding-standards
│ generate-code    │   (所有 subagents 必须遵循)
│                  │
│ Subagent 驱动    │
│ 并行生成         │
│ 双阶段 review    │
└──────────────────┘
        ↓
┌──────────────────┐
│ 阶段 4：生成交付物 │
│ generate-        │
│ deliverables     │
│                  │
│ 5 份标准化文档    │
└──────────────────┘
        ↓
┌──────────────────┐
│ 阶段 5：验证完成   │
│ verify-and-finish│
│                  │
│ 综合验证清单      │
└──────────────────┘
```

### 关键设计模式

#### 1. 硬门控（HARD-GATE）

**问题：** 用户可能在输入不完整时就要求生成代码，导致低质量产出。

**解决方案：** 在阶段 1 和阶段 2 之间设置硬门控，**强制验证 4 种输入完整性**。

```markdown
<HARD-GATE>
在进入代码生成阶段之前，必须收集并验证全部 4 种必填输入：
1. PRD 需求文档（链接）
2. 前端架构设计文档（链接）
3. 设计稿（Figma MCP / Sketch MCP）
4. API 接口文档（链接）

缺失任何一项，必须停止并向用户索取。
</HARD-GATE>
```

**实现：**
- `collect-inputs` 子 skill 负责检查每项输入
- 未通过时不调用 `analyze-and-plan`
- 主 skill 循环等待用户补全输入

#### 2. 全局基础规范

**问题：** 每个阶段的子 skill 如果独立定义代码规范，会导致不一致。

**解决方案：** `coding-standards` 作为**全局基础规范**，所有子 skills 引用它。

```
coding-standards/               # 全局生效
├── SKILL.md                    # 9 层架构规范
└── references/
    ├── tech-stack.md           # 技术栈清单
    ├── directory-structure.md  # 目录结构
    ├── api-request.md          # API 层规范
    └── sensors-config.md       # 埋点规范
```

**9 层架构规范：**
1. 主程序（`main.tsx` / `App.tsx`）
2. 全局样式（`styles/globals.css`）
3. 页面层（`pages/xxx/index.tsx`）
4. 组件层（`components/XxxName/index.tsx`）
5. 接口层（`api/xxx.ts`）
6. 数据层（`stores/` + `hooks/`）
7. 类型层（`types/xxx.ts`）
8. 工具层（`utils/xxx.ts`）
9. 埋点层（集成在各层）

**引用方式：**
- 阶段 2：`analyze-and-plan` 读取技术栈清单，探测项目使用哪些技术
- 阶段 3：`generate-code` 所有 subagents 必须遵循完整规范
- 阶段 5：`verify-and-finish` 验证代码是否符合规范

#### 3. 前置工具模式

**问题：** 用户可能没有某些必填输入（如架构文档），需要工具辅助生成。

**解决方案：** 提供**按需调用的前置工具**。

```
前置工具：
- architecture-doc：根据 PRD 生成架构文档（11 章节）
- feishu-doc：读写飞书文档（自动替代 WebFetch）
```

**调用时机：**
- 用户明确没有架构文档时，主 skill 先调用 `architecture-doc`
- 检测到飞书链接时，自动使用 `feishu-doc` 替代 `WebFetch`

#### 4. Subagent 驱动生成

**问题：** 一次生成多个文件（20+ 文件）容易出错，单线程生成太慢。

**解决方案：** 使用 **subagent-driven-development** 模式。

**架构：**
```
generate-code (主控)
    ↓
并行启动多个 subagents
    ↓
Subagent 1: 生成 types/user.ts
Subagent 2: 生成 api/user.ts
Subagent 3: 生成 pages/UserManagement/index.tsx
    ↓
双阶段 review
    ↓
合并产出
```

**双阶段 review：**
1. **Spec review**：验证是否符合实施计划和规范
2. **Implementation review**：验证代码质量和测试覆盖

**实现文件：**
- `skills/generate-code/references/implementer-prompt.md`
- `skills/generate-code/references/spec-reviewer-prompt.md`

---

## 为什么嵌套结构是合理的？

### 对比：展平 vs 嵌套

#### ❌ 展平结构（不推荐）

```
plugins/unipus-frontend-plugin/skills/
├── unipus-fe-dev/                    # 主 skill
├── collect-inputs/                   # 看起来像独立 skill，实际是子组件
├── analyze-and-plan/
├── generate-code/
├── generate-deliverables/
├── verify-and-finish/
├── architecture-doc/
├── feishu-doc/
├── coding-standards/
├── unipus-design-ui/                 # 真正独立的 skill
└── wpf-xaml-performance/             # 真正独立的 skill
```

**问题：**
1. **破坏封装**：子 skills 看起来像独立 skill，但它们不能单独使用
2. **失去从属关系**：无法从目录结构看出哪些 skills 属于 unipus-fe-dev
3. **命名空间混乱**：`collect-inputs` 是谁的收集输入？
4. **引用路径复杂**：主 skill 需要用 `../collect-inputs/SKILL.md` 引用
5. **版本管理困难**：无法整体移动或复制 unipus-fe-dev 及其子组件
6. **污染命名空间**：8 个子 skills 占据了 skills/ 顶层命名空间

#### ✅ 嵌套结构（推荐）

```
plugins/unipus-frontend-plugin/skills/
├── unipus-fe-dev/                    # 封装完整的工作流系统
│   ├── SKILL.md                      # 主 skill
│   ├── README.md                     # 用户手册
│   ├── ARCHITECTURE.md               # 架构说明
│   └── skills/                       # 子 skills（封装在内部）
│       ├── collect-inputs/
│       ├── analyze-and-plan/
│       └── ...
├── unipus-design-ui/                 # 独立 skill
└── wpf-xaml-performance/             # 独立 skill
```

**优势：**
1. **清晰的边界**：一眼看出哪些是独立 skill，哪些是复合 skill
2. **逻辑封装**：unipus-fe-dev 是一个完整的单元，可以整体移动、复制、版本化
3. **相对引用**：`./skills/xxx/SKILL.md` 简洁且不依赖外部路径
4. **易于扩展**：添加新阶段只需在 skills/ 下新增目录
5. **命名空间清晰**：子 skills 使用 `unipus:fe-dev:xxx` 命名空间
6. **复用模板**：其他复杂 skill 可以参考这个模式

### 真实场景验证

**场景 1：添加新阶段**

嵌套结构：
```bash
# 只需在 unipus-fe-dev/skills/ 下新增目录
cd plugins/unipus-frontend-plugin/skills/unipus-fe-dev/skills
mkdir new-stage && cd new-stage
cat > SKILL.md <<EOF
---
name: unipus:fe-dev:new-stage
---
EOF
```

展平结构：
```bash
# 需要在顶层 skills/ 新增，容易与独立 skills 混淆
cd plugins/unipus-frontend-plugin/skills
mkdir new-stage  # 这看起来像独立 skill！
```

**场景 2：复制到另一个项目**

嵌套结构：
```bash
cp -r unipus-fe-dev/ ../other-project/skills/
# 完整复制，所有引用路径仍然有效
```

展平结构：
```bash
# 需要复制 9 个目录，手动调整所有引用路径
cp -r unipus-fe-dev/ collect-inputs/ analyze-and-plan/ ... ../other-project/skills/
```

**场景 3：版本管理**

嵌套结构：
```bash
git tag unipus-fe-dev-v1.1.0
# 打标签时，整个 unipus-fe-dev/ 目录作为一个单元
```

展平结构：
```bash
# 需要同时管理 9 个独立目录的版本
git tag unipus-fe-dev-v1.1.0
# 但 collect-inputs/ 的版本号是多少？
```

---

## 如何创建类似的复合 Skill？

### 决策树：是否需要复合 Skill？

```
问题：我的工作流是否需要复合 skill？

├─ 有 3 个以上明确阶段？
│  ├─ 是 → 继续
│  └─ 否 → 使用普通 skill
│
├─ 每个阶段逻辑复杂（>200 行）？
│  ├─ 是 → 继续
│  └─ 否 → 使用普通 skill
│
├─ 阶段之间有依赖关系？
│  ├─ 是 → 继续
│  └─ 否 → 使用多个独立 skills
│
└─ 需要共享全局规范？
   ├─ 是 → 使用复合 skill ✅
   └─ 否 → 使用多个独立 skills
```

### 创建步骤

#### 1. 设计工作流

先画出工作流图：
```
阶段 1 → 阶段 2 → 阶段 3 → 完成
  ↓        ↓        ↓
子skill   子skill   子skill
  ↓        ↓        ↓
共享规范 ← ← ← ← ← ←
```

#### 2. 创建目录结构

```bash
cd plugins/your-plugin/skills
mkdir -p your-complex-skill/skills

cd your-complex-skill

# 创建主 skill
cat > SKILL.md <<'EOF'
---
name: your-plugin:complex-skill
version: 1.0.0
description: Your workflow description
---

# Your Complex Skill

## 子 Skill 引用

| 阶段 | 子 Skill | 路径 |
|------|---------|------|
| 1 | `your-plugin:complex-skill:step1` | `./skills/step1/SKILL.md` |
| 2 | `your-plugin:complex-skill:step2` | `./skills/step2/SKILL.md` |
EOF

# 创建架构说明
cat > ARCHITECTURE.md <<'EOF'
# your-plugin:complex-skill Architecture

[说明为什么需要复合 skill，架构设计思路]
EOF

# 创建用户手册
cat > README.md <<'EOF'
# your-plugin:complex-skill 使用手册

[说明如何使用这个 skill]
EOF

# 创建子 skills
mkdir -p skills/step1 skills/step2
```

#### 3. 设计命名空间

使用冒号分隔：
- 主 skill：`your-plugin:complex-skill`
- 子 skills：`your-plugin:complex-skill:step1`、`your-plugin:complex-skill:step2`
- 基础规范：`your-plugin:complex-skill:standards`

#### 4. 实现子 skills

每个子 skill 独立实现，但遵循主 skill 定义的接口：
```markdown
---
name: step1
version: 1.0.0
description: Step 1 of the workflow
---

# Step 1

[实现细节]
```

#### 5. 文档化

在 ARCHITECTURE.md 中说明：
- 为什么使用复合 skill
- 各个子 skill 的职责
- 如何引用和扩展
- 为什么嵌套结构是合理的

---

## 参考案例

当前项目中，**unipus-fe-dev 是唯一的复合 skill**，其他 plugins 下的 skills 都是独立 skill。

### 独立 Skill 示例

```
plugins/unipus-frontend-plugin/skills/
├── wpf-xaml-performance/              # 独立 skill
│   ├── SKILL.md                       # 单一入口
│   └── evals/                         # 测试用例
└── unipus-design-ui/                  # 独立 skill
    └── SKILL.md                       # 单一入口
```

### 复合 Skill 示例

```
plugins/unipus-frontend-plugin/skills/
└── unipus-fe-dev/                     # 复合 skill
    ├── SKILL.md                       # 主 skill（工作流编排）
    ├── README.md                      # 用户手册
    ├── ARCHITECTURE.md                # 架构说明（本文档）
    └── skills/                        # 子 skills 封装在内部
        ├── collect-inputs/
        ├── analyze-and-plan/
        └── ...
```

**区别：**
- 独立 skill：单一 `SKILL.md` 解决单一问题
- 复合 skill：主 `SKILL.md` + 多个子 skills 解决复杂工作流

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|-----|------|---------|
| 1.1.0 | 2026-04-07 | 增强埋点集成，添加神策 SDK 规范 |
| 1.0.0 | 2026-03-15 | 初始版本，5 阶段工作流 |

---

## 维护指南

### 添加新阶段

1. 在 `skills/` 下创建新目录
2. 编写 `SKILL.md`，命名空间遵循 `unipus:fe-dev:new-stage`
3. 在主 `SKILL.md` 的"子 Skill 引用"表格中添加条目
4. 更新工作流图
5. 更新本 ARCHITECTURE.md

### 修改现有阶段

1. 修改对应子 skill 的 `SKILL.md`
2. 如果接口变化，更新主 `SKILL.md` 的引用说明
3. 更新版本号

### 删除阶段

1. 从主 `SKILL.md` 的引用表格中删除
2. 移除 `skills/` 下的对应目录
3. 更新工作流图

---

## 常见问题

### Q1: 为什么不使用绝对路径引用子 skills？

**A:** 相对路径保持封装性，整个 unipus-fe-dev 目录可以作为一个单元移动或复制，不会破坏引用。

### Q2: 子 skills 可以独立使用吗？

**A:** 理论上可以，但不推荐。子 skills 设计为工作流的一部分，独立使用可能缺少必要的上下文。

### Q3: 可以在其他 skill 中引用 unipus-fe-dev 的子 skills 吗？

**A:** 可以，但需要使用完整路径。例如：
```markdown
引用：`../unipus-fe-dev/skills/coding-standards/SKILL.md`
```

### Q4: 为什么 coding-standards 不是工作流的一个阶段？

**A:** `coding-standards` 是全局基础规范，不是工作流步骤。它在阶段 2（探测技术栈）和阶段 3（代码生成）都会被引用。

### Q5: 可以有多层嵌套吗（子 skill 下再有子 skills）？

**A:** 技术上可行，但不推荐。保持最多 2 层嵌套（主 skill → 子 skills），过深的嵌套会降低可维护性。

---

## 参考资料

- [Superpowers: Subagent-Driven Development](../../../../../../.claude/superpowers/subagent-driven-development.md)
- [Claude Code 插件开发指南](https://docs.anthropic.com/claude/docs/claude-code-plugins)
- [unipus:fe-dev 用户手册](./README.md)

---

**维护者：** Unipus 前端团队  
**问题反馈：** [GitHub Issues](https://github.com/Glepooek/unipus-plugins-official/issues)  
**最后更新：** 2026-05-08
