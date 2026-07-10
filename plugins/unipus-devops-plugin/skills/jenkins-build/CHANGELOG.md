# Changelog

## [1.2.2] - 2026-07-10

### Added
- 反例黑名单新增一条：项目级/用户级配置同时存在时未确认实际命中路径就直接触发（darwin-skill dim9 反例黑名单优化）

## [1.2.1] - 2026-07-10

### Changed
- "使用方法"章节重组为显式编号 Step 1-6（确认前置条件/定位配置文件/CHECKPOINT确认/执行触发/等待轮询/输出摘要），每步补充输入/输出说明，替代此前的非线性小节结构（darwin-skill dim2 工作流清晰度优化）

## [1.2.0] - 2026-07-03

### Added
- 新增触发条件评测数据集 `evals/trigger-eval.json`（10 条应触发 + 11 条不应触发场景），用于验证 description 的触发准确率

## [1.1.0] - 2026-06-30

### Added
- 构建完成后输出结构化摘要表格（Job / 构建号 / 结果 / 耗时 / 构建地址 / 配置来源）
- 失败处理表格新增"未找到配置文件"条目
- 反例黑名单新增两条：job path 编码错误、跳过 run.sh 直接运行 main.py
- 新增三段式 `jenkins-config.yaml.example`（配置模板 + 配置示例 + 查找优先级说明）
- `version` 字段写入 SKILL.md frontmatter

### Changed
- 配置文件重命名：`config.yaml` → `jenkins-config.yaml`，支持两级路径查找（项目级 / 用户级 `~/.claude/`）
- venv 固定至 `~/.claude/cache/jenkins-build/.venv`，脱离 SKILL_DIR，不污染插件仓库
- `run.sh` 删除 `cp` 配置同步逻辑，配置查找由 `main.py` 的 `CONFIG_SEARCH_PATHS` 负责
- description 按 writing-skills SDO 原则重写：改为 "Use when..." 触发条件格式，删除工作流摘要
- 合并"注意事项"章节内容进"反例黑名单"，消除重复
- 构建完成后通知从调用 `unipus-ci-notify-api-change` skill 改为直接输出摘要表格
- `.example` 文件中重复的查找优先级列表改为引用 SKILL.md

### Removed
- `disable-model-invocation: true` frontmatter 限制
- `globs: ["jenkins_build/**"]` 自动触发配置
- 外层多余的 `__init__.py`
- 旧的 `config.yaml`（本地凭证文件，已迁移至 `~/.claude/jenkins-config.yaml`）
- 旧的 `config.yaml.example`（内容合并至新的 `jenkins-config.yaml.example`）
- 对 `unipus-ci-notify-api-change` skill 的依赖

## [1.0.0] - 初始版本

- 基础 Jenkins 构建触发功能
- 支持指定 job 名称和构建参数
- 自动等待构建启动并轮询结果
