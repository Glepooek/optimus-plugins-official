# Changelog

## [1.0.1] - 2026-08-22

### Changed
- 校验脚本迁入本 skill 的 `scripts/` 子目录，随 skill 分发；运行命令改为 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>`

## [1.0.0] - 2026-08-22

### Added
- 初始版本：引导新增/修改/迁移 knowledge-base 条目，同步索引、CHANGELOG、版本号，调用 check_index.py 做一致性校验
