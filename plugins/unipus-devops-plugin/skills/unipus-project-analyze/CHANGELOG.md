## [1.2.0] - 2026-07-02

### Changed
- 泛化 skill 适用范围：移除"公司内部"限定，支持分析任意项目（公开/私有仓库均可）
- 错误处理中 git clone 网络失败提示区分公开/私有仓库场景
- 分析深度控制新增外部项目适配说明（第 2/10/11 章）

## [1.1.0] - 2026-07-02

### Changed
- 替换虚构工具（readCode/readMultipleFiles/readFile/fsWrite/fsAppend）为实际可用的 Claude Code 工具（Read/Glob/Grep/Write/Edit）
- 第五步格式转换改为引用 unipus-office-plugin:docx-writer skill
- 迭代优化规则中的检查方式替换为 Grep/Glob 工具

### Added
- 添加 3 个用户确认检查点（项目确认、分析确认、报告审阅）
- 添加反例与黑名单章节（8 条禁止行为）
- 添加 CHANGELOG.md
