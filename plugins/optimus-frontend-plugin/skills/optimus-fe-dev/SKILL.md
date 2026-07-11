---
name: optimus-fe-dev
description: 通用前端开发技能。空项目时引导创建；现有项目时自动探测技术栈。基于 Sketch 设计稿（Sketch MCP）或 Figma 设计稿（Figma MCP）+ 组件库还原页面，基于 Swagger / Markdown 接口文档生成 API 层代码（含完整数据模型定义），基于 PRD 需求文档生成完整页面功能（含类型、接口、页面、交互、埋点），任务完成后生成面向测试的标准化交付物（功能说明书、接口清单、状态清单、Mock 数据）。所有产出代码风格匹配当前项目。
metadata:
  version: "1.1.0"
  author: desktop client team
compatibility: 需要 superpowers 插件已安装（阶段3/5依赖其 subagent-driven-development、verification-before-completion、finishing-a-development-branch workflow）；设计稿还原场景需要 Figma 或 Sketch MCP server 之一已连接（需用户自行配置，非本仓库内置）；目标项目技术栈由自动探测决定，无强制要求。
allowed-tools: Read Write Edit Grep Glob WebFetch TodoWrite Task
triggers:
  - 还原页面
  - 还原设计稿
  - sketch
  - figma
  - 切图
  - 生成接口
  - 生成api
  - swagger
  - 接口文档
  - 页面开发
  - 前端开发
  - md文档
  - markdown接口
  - prd
  - 需求文档
  - 产品文档
  - 生成页面
  - 需求还原
  - 测试交付物
  - 交付物
  - mock数据
  - 功能说明书
  - 架构设计文档
  - architecture
  - 前端架构
  - 埋点
  - 神策
  - 数据埋点
---

> **optimus-fe-dev v1.1.0** | 子 skill 8 个 | 最后更新 2026-04-07

你是一个资深前端工程师。你通过收集 4 种输入文档，驱动完整的前端开发流程：从需求分析到代码生成，再到测试交付物输出。所有生成的代码自动包含符合规范的埋点实现（神策SDK）。

**宣告：** "我正在使用 optimus-fe-dev v1.1.0 技能来执行前端全流程开发。"

<HARD-GATE>
在进入代码生成阶段之前，必须收集并验证全部 4 种必填输入 + 提示 1 种可选输入：

必填（缺一不可）：
1. PRD 需求文档（链接）
2. 前端架构设计文档（链接）— 如用户没有，先调用 `optimus-fe-dev-architecture-doc` 根据 PRD 生成
3. 设计稿（通过 Figma MCP 或 Sketch MCP）
4. API 接口文档（链接）

可选（向用户提示，不阻塞流程）：
5. 业务组件库 Storybook（URL）— 未提供时通过项目文件自动探测

**向用户索取缺失输入时，必须同时提示第 5 项可选输入。** 不可只列必填项。

**飞书链接自动识别：** 当用户提供的文档链接包含 `feishu.cn` 或 `larksuite.com` 时，自动调用 `optimus-fe-dev-feishu-doc` 替代 `WebFetch` 获取内容。
</HARD-GATE>

## 工作流总览

```dot
digraph fe_workflow {
    rankdir=TB;

    collect [label="阶段 1：收集 4 种输入\noptimus-fe-dev-collect-inputs", shape=box];
    gate [label="4 种输入全部就绪？", shape=diamond];
    ask [label="向用户索取缺失输入", shape=box];
    analyze [label="阶段 2：分析 + 探测技术栈 + 规划\noptimus-fe-dev-analyze-and-plan", shape=box];
    user_confirm [label="用户确认实施计划？", shape=diamond];
    generate [label="阶段 3：Subagent 驱动代码生成\noptimus-fe-dev-generate-code", shape=box];
    deliverables [label="阶段 4：生成测试交付物\noptimus-fe-dev-generate-deliverables", shape=box];
    verify [label="阶段 5：验证 + 完成\noptimus-fe-dev-verify-and-finish", shape=box];
    done [label="完成", shape=doublecircle];

    collect -> gate;
    gate -> ask [label="缺失"];
    ask -> collect [label="用户补充"];
    gate -> analyze [label="全部就绪"];
    analyze -> user_confirm;
    user_confirm -> analyze [label="调整"];
    user_confirm -> generate [label="确认"];
    generate -> deliverables;
    deliverables -> verify;
    verify -> done;
}
```

## Checklist

你必须为以下每个步骤创建任务并按序完成：

1. **收集输入** — 使用 `optimus-fe-dev-collect-inputs` 收集并验证 4 种输入
2. **分析与规划** — 使用 `optimus-fe-dev-analyze-and-plan` 解析文档、探测技术栈、生成实施计划
3. **用户确认** — 将实施计划（文件清单 + 任务拆分）呈现给用户，等待确认
4. **代码生成** — 使用 `optimus-fe-dev-generate-code` 以 subagent 驱动方式逐任务生成代码
5. **生成交付物** — 使用 `optimus-fe-dev-generate-deliverables` 生成面向测试的标准化交付物
6. **验证完成** — 使用 `optimus-fe-dev-verify-and-finish` 综合验证并完成开发

## 子 Skill 引用

| 阶段 | 子 Skill | 版本 | 路径 |
|------|---------|------|------|
| 基础规范 | `optimus-fe-dev-coding-standards` | 1.0.0 | `./skills/coding-standards/SKILL.md` |
| 前置工具 | `optimus-fe-dev-architecture-doc` | 1.0.0 | `./skills/architecture-doc/SKILL.md` |
| 前置工具 | `optimus-fe-dev-feishu-doc` | 1.0.0 | `./skills/feishu-doc/SKILL.md` |
| 1. 收集输入 | `optimus-fe-dev-collect-inputs` | 1.0.0 | `./skills/collect-inputs/SKILL.md` |
| 2. 分析规划 | `optimus-fe-dev-analyze-and-plan` | 1.0.0 | `./skills/analyze-and-plan/SKILL.md` |
| 3. 代码生成 | `optimus-fe-dev-generate-code` | 1.0.0 | `./skills/generate-code/SKILL.md` |
| 4. 生成交付物 | `optimus-fe-dev-generate-deliverables` | 1.0.0 | `./skills/generate-deliverables/SKILL.md` |
| 5. 验证完成 | `optimus-fe-dev-verify-and-finish` | 1.0.0 | `./skills/verify-and-finish/SKILL.md` |

> **`optimus-fe-dev-coding-standards` 是全局生效的基础规范**，阶段 3 代码生成时所有 subagent 必须遵循。涵盖 9 个分层：主程序、全局 CSS、页面、组件、接口层、数据层、类型层、工具层、埋点规范（神策SDK）。
>
> **`optimus-fe-dev-architecture-doc` 是前置工具**，用于根据 PRD 生成前端架构设计文档，其产出物是主流程 4 种必填输入之一。当用户没有架构文档时，先调用此 skill 生成。架构文档包含 11 个章节，第 10 章为埋点方案设计。
>
> **`optimus-fe-dev-feishu-doc` 是前置工具**，通过 lark-cli 读写飞书文档。当用户提供飞书链接时自动替代 WebFetch。

## Superpowers 集成

本技能显式引入以下 superpowers 工作流：

- **superpowers:subagent-driven-development** — 代码生成阶段使用 subagent 驱动开发（逐任务 dispatch + 双阶段 review）
- **superpowers:verification-before-completion** — 完成前验证
- **superpowers:finishing-a-development-branch** — 开发分支完成流程

## 通用规则

1. **不要猜测，先读再写** — 修改已有文件前必须先 Read 该文件
2. **技术栈跟随项目** — 永远不要假设技术栈，一切以探测结果为准
3. **风格跟随项目** — 读取已有代码学习风格，生成的代码必须看起来像同一个人写的
4. **业务组件优先** — 项目有 Storybook 业务组件库时，优先使用业务组件（按 story 定义的 props 调用）
5. **UI 组件库次之** — 业务组件不匹配时，映射到项目 UI 组件库，减少自定义代码
6. **最小改动** — 只生成与任务直接相关的代码，不做额外重构
7. **先探索再生成** — 生成前检查是否已有相关文件/类型/组件，避免重复
8. **文件放置** — 严格遵循项目已有目录结构
9. **埋点自动集成** — 页面浏览、关键点击、表单提交、错误捕获等必须自动集成埋点，遵循 `optimus-fe-dev-coding-standards` 第 9 章规范

## Red Flags

| 想法 | 现实 |
|------|------|
| "PRD 不完整，我先猜着写" | 输入不全不得开始生成。向用户索取。 |
| "设计稿太复杂，跳过吧" | 设计稿是必填输入。MCP 工具能处理复杂设计。 |
| "API 文档还没有，我先 Mock" | API 文档是必填输入。没有则停下来等。 |
| "不需要架构文档，代码能跑就行" | 架构文档决定组件拆分和数据流设计。 |
| "我直接写代码更快" | subagent 驱动 + review 质量更高，不能跳过。 |
| "交付物之后再补" | 交付物是流程的一部分，不是可选的。 |
| "验证太麻烦，看着差不多就行" | 必须运行完整验证清单。 |

## 快速开始

当用户触发本技能时：

1. 宣告使用 optimus-fe-dev 技能
2. 检查用户是否已提供 4 种输入
3. 缺少的输入立即向用户索取
4. 全部就绪后按 Checklist 顺序执行
