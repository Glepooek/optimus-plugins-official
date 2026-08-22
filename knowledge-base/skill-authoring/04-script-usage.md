# 04 · 脚本使用

> 更新历史：2026-08-22 创建。
>
> 来源：[在 skill 中使用脚本](https://agentskills.io/skill-creation/using-scripts)。skill 可让 agent 跑 shell 命令、在 `scripts/` 捆绑可复用脚本。本篇约束 one-off 命令、自包含脚本、以及**面向 agent 运行**的脚本接口设计。

## 1. One-off 命令

当现成工具已能完成所需时，可直接在 SKILL.md 里引用，无需 `scripts/` 目录。

- **必须**：**锁版本**（如 `npx eslint@9.0.0`），保证命令行为随时间稳定
- **必须**：SKILL.md 里**声明前置条件**（如"Requires Node.js 18+"），不假设 agent 环境自带；运行时级要求在 `compatibility` frontmatter 声明
- **应该**：用自动解析依赖的工具——Python 用 `uvx`/`pipx`，npm 包用 `npx`，Bun 环境用 `bunx`，Go 用 `go run`
- **禁止**：命令复杂到首试难写对时仍用 one-off——此时应改为 `scripts/` 下的已测脚本

## 2. 引用 scripts/ 脚本

- **必须**：引用脚本用**相对路径**，基准是 skill 目录根；agent 自动解析，无需绝对路径
- **必须**：在 SKILL.md 列出可用脚本清单（`## Available scripts`），让 agent 知道存在哪些
- **必须**：指令里给出运行示例（`bash scripts/validate.sh "$INPUT_FILE"`）
- **认知**：相对路径约定同样适用于 `references/*.md` 等支撑文件——脚本执行路径相对 skill 目录根（agent 从那里运行命令）

## 3. 自包含脚本

需要可复用逻辑时，把脚本放进 `scripts/`，**内联声明依赖**，一条命令即可运行——无需独立 manifest 或安装步骤。

- **应该**：Python 脚本用 [PEP 723](https://peps.python.org/pep-0723/) 内联依赖声明，用 `uv run scripts/extract.py` 运行（pipx 也支持）；用 PEP 508 锁版本区间、`requires-python` 约束版本
- **应该**：Deno 用 `npm:`/`jsr:` import specifier，Bun 用 import 路径锁版本（`cheerio@1.0.0`），Ruby 用 `bundler/inline`
- **禁止**：依赖 `node_modules`/`Gemfile` 等外部安装步骤才可运行的脚本（破坏"一条命令运行"原则）

## 4. 面向 agent 的脚本设计

agent 读脚本的 stdout/stderr 决定下一步。以下设计让脚本对 agent 更友好：

### 4.1 禁止交互提示（硬约束）

- **必须**：**禁止**交互提示——agent 在非交互 shell 运行，无法响应 TTY prompt / 密码 / 确认菜单，会挂起
- **必须**：全部输入经命令行 flag / 环境变量 / stdin 传入

```
# ❌ 挂起等待输入
$ python scripts/deploy.py
Target environment: _

# ✅ 清晰报错并给出指引
$ python scripts/deploy.py
Error: --env is required. Options: development, staging, production.
Usage: python scripts/deploy.py --env staging --tag v1.2.3
```

### 4.2 文档化接口

- **应该**：提供 `--help`——这是 agent 学习脚本接口的主要途径；含简述、可用 flag、用法示例；保持简洁（输出会进 agent 上下文）
- **必须**：错误消息说清**什么错了、期望什么、该怎么试**，不写"Error: invalid input"这类浪费一轮的含糊消息

### 4.3 结构化输出

- **必须**：偏好结构化格式（JSON/CSV/TSV），可被 agent 和标准工具（`jq`、`cut`）共同消费，可组合进 pipeline
- **必须**：**数据与诊断分离**——结构化数据走 stdout，进度/警告/诊断走 stderr，agent 可捕获干净输出
- **禁止**：用空白对齐的表格输出（难以编程解析）

### 4.4 健壮性设计

- **必须**：**幂等**——agent 可能重试命令；"不存在才创建"优于"重复即失败"
- **应该**：拒绝歧义输入并给清晰错误，不猜；用枚举和闭合集
- **应该**：破坏性/有状态操作提供 `--dry-run`，让 agent 预览
- **应该**：不同失败类型用**不同退出码**（找不到、参数非法、鉴权失败），并在 `--help` 里文档化
- **必须**：破坏性操作考虑需显式确认 flag（`--confirm`/`--force`）或按风险等级加防护
- **必须**：控制输出大小——agent harness 常截断超阈值输出（约 10-30K 字符）；大输出默认给摘要/合理上限，支持 `--offset` 分页；不可分页的大输出要求显式 `--output` flag（输出到文件或 `-` 明确选择 stdout）

## 权威参考

- [在 skill 中使用脚本 — 完整版](https://agentskills.io/skill-creation/using-scripts)
