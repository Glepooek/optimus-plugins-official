# sync-skill-symlinks

> 版本：2.0.0 | 分类：tool

将 skill 源目录中的所有 skill 子目录以符号链接分发到各 AI 工具的 skills 目录（默认 targets：`~/.claude/skills/`、`~/.kiro/skills/`、`~/.codex/skills/`），使用户只需维护单一 source of truth。

## 所处层级

本 skill 是文件系统工具类 skill，与插件业务领域正交，按工作形态归入 `tool` 层：

```
┌────────────────────────────────────────────────────────────┐
│  skill 工作形态层级（按 metadata.category 取值）            │
│                                                            │
│  workflow   流程编排 · 多阶段 pipeline / 交接式工作流       │
│  quality    质量保障 · review / 评分 / 一致性校验          │
│  generator  产物生成 · PRD / 代码 / 测试 / 报告            │
│  ★ tool     工具类 · 数据同步 / 符号链接管理 / 脚本初始化   │
│  platform   平台专项 · android / ios / harmony              │
│  decision   决策支持 · 选型结论 / 适用性判断                │
│                                                            │
│  直接上下游 skill：无上下游，独立使用                       │
│  （不被其他 skill 调度，也不调度任何 skill；仅与文件系统    │
│   和用户会话交互）                                         │
└────────────────────────────────────────────────────────────┘
```

## 触发词 / 内部触发条件

独立 skill，用户主动触发，触发语句含以下任一关键词：

同步 skills、sync skill symlinks、链接 skills、更新 skill 链接、link skills、update skill symlinks

可选参数：`source=<绝对路径>` 指定 skill 源目录（默认 `~/.agents/skills/`）；`target=<路径1,路径2,...>` 指定一个或多个目标目录（逗号分隔，默认 `~/.claude/skills/`、`~/.kiro/skills/`、`~/.codex/skills/`）。

## 业务逻辑流程图

```
Step 0  参数解析与路径验证
   │    提取 source= / target= 参数（未指定则用默认值）
   │    自定义路径边界检查：target 父目录缺失 → CHECKPOINT 询问是否创建
   │    路径是文件 → 过滤跳过
   ▼
Step 1  权限预检（仅 Windows）
   │    实测创建符号链接；失败 → 提示开发者模式/管理员并终止
   │    macOS/Linux 跳过此步
   ▼
Step 2  扫描源目录
   │    源目录不存在或无 skill 子目录 → 提前返回
   ▼
Step 3  创建符号链接（逐 target、逐 skill）
   │    链接不存在 → 新建
   │    已存在但目标不符 → 自动更新
   │    目标一致 → 跳过
   │    非符号链接 → 警告
   ▼
Step 4  检测失效链接
   │    扫描各 target 下指向不存在路径的符号链接
   ▼
Step 5  汇总 & CHECKPOINT 处理失效链接
         y → 删除失效链接
         n → 保留留待手动清理
```

## 产出物数据流

```
输入：skill 源目录（默认 ~/.agents/skills/，含若干 skill 子目录）
  │
  ▼
本 skill：符号链接分发（新建 / 更新 / 跳过 / 告警 / 失效清理）
  │
  ▼
产出：各 target 目录下的同名符号链接
      ~/.claude/skills/<skill>  → 源目录/<skill>
      ~/.kiro/skills/<skill>    → 源目录/<skill>
      ~/.codex/skills/<skill>   → 源目录/<skill>
  │
  ▼
下游消费者：各 AI 工具加载 skills 时经符号链接穿透读取源目录内容
            （单一真源：编辑源目录即同步生效，不产生独立副本）
```

## Skill 依赖关系图

```
        用户会话（触发）                    文件系统（读写）
  ┌───────────────────┐          ┌─────────────────────────────┐
  │ AI 用户会话         │ ───────▶ │ 源目录 ~/.agents/skills/    │
  └───────────────────┘   读取    │ （只读，skill 单一真源）     │
          │                       └─────────────────────────────┘
          │ 触发
          ▼
  ┌───────────────────┐           ┌─────────────────────────────┐
  │ sync-skill-symlinks│ ───────▶ │ ~/.claude/skills/            │
  │ （本 skill）        │   写入    │ ~/.kiro/skills/             │
  └───────────────────┘           │ ~/.codex/skills/            │
          │                       └─────────────────────────────┘
          │ 无 skill 级调度
          ▼
  无上下游 skill：独立使用
  （不调用其他 skill，也不被其他 skill 调度）
```

