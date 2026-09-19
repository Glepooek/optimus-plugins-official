# Changelog

## [1.2.0] - 2026-09-19

### Changed
- 写入目标从仓库根目录 `tools.md` 单文件改为 `knowledge-base/tools` 领域：每个工具登记为一条独立 `kind: reference` 条目，五个固定分类（Skill/MCP/CLI/Agent/Plugin）改为不互斥的 `tags` 数组，允许合理新增类别标签
- Step 4 查重从"读取 tools.md 全文比对"改为 Grep 检索 `knowledge-base/tools/index.jsonl`（`knowledge-base-maintain` 的 `find_duplicates.py` 只处理 `kind: rule`，不适用于本 skill 全为 reference 的条目）
- Step 6 写入流程改为**强制调用** `knowledge-base-maintain` skill 完成落地（`allowed-tools` 新增 `Skill`），不再手动内联复制其字段/版本号同步步骤——避免该 skill 演进时两处静默失配；本 skill 只决定"写什么"（领域固定 `tools`，`kind` 固定 `reference`），不重复实现"怎么安全写进知识库"
- 原根目录 `tools.md` 已删除，历史内容迁移至 `knowledge-base/tools/`；`AGENTS.md` 新增"引入新工具前先查已有记录"的触发规则，使这份记录能在决策场景被主动检索，而非仅靠人工翻阅

## [1.1.1] - 2026-08-30

### Added
- 新增 `known-issues.md` 使用期反馈记录机制（空模板），配套仓库新增的 skill 持续优化硬性约定，见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`

## [1.1.0] - 2026-07-12

### Added
- 条目格式新增"更新方式"、"移除方式"两个可选字段（Step3提取信息、Step6写入模板同步更新）
- 明确要求：更新/移除方式必须来自官方文档明确说明，不得凭包管理器通用惯例推断填写，找不到就整项省略

## [1.0.2] - 2026-07-12

### Added
- 异常处理表新增"抓取成功但内容与目标工具不符"分支（链接跳转错误/产品改名下线等场景），要求STOP而非按错误内容继续填写（darwin-skill round2 补充：round1裁判指出的独立失败模式）

## [1.0.1] - 2026-07-12

### Fixed
- Step 3 补充"用户描述 vs 抓取内容冲突时以谁为准"的裁决规则：以抓取内容为准，但用户描述中抓取未覆盖的信息仍需保留进备注字段（darwin-skill 实测发现该空白）

## [1.0.0] - 2026-07-11

### Added
- 初始创建：将工具/资源信息抓取整理并归档到仓库根目录 tools.md 的工作流
- 支持 playwright-cli 优先抓取（JS渲染SPA页面）、WebFetch 降级
- 写入前重复检测 CHECKPOINT、分类不确定 CHECKPOINT
- 异常处理表（4类失败场景）与 Red Flags 反例清单（5条）
