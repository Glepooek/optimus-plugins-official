# Changelog

## [2.1.0] - 2026-07-11

### Added
- Step5新增🔴CHECKPOINT显性标记，用户未回答时禁止自行假设答案继续执行
- "异常处理"表：覆盖references缺失、内容为空/非PRD、路径不存在、Step5未给出明确选项四类场景
- Step6新增🔴CHECKPOINT：补全内容间/与原文矛盾时不得自行选边，须在优化说明标注"⚠️矛盾待确认"；Step7优化说明模板同步新增矛盾标注位
- Red Flags新增2条：矛盾自行选边定案、越权扩大优化范围；并在Step6原则中补上范围限定的对应约束

### Changed
- 统一"内容非PRD"异常处理行的STOP语义（原为软确认，改为需用户明确确认才可继续），与其余行强度一致

## [2.0.0] - 2026-07-10

### Changed
- Skill 重命名：`optimus-prd-optimize` → `prd-optimizer`（破坏性变更，需使用新名称调用）
