# Changelog

## [1.0.1] - 2026-07-12

### Fixed
- Step 3 补充"用户描述 vs 抓取内容冲突时以谁为准"的裁决规则：以抓取内容为准，但用户描述中抓取未覆盖的信息仍需保留进备注字段（darwin-skill 实测发现该空白）

## [1.0.0] - 2026-07-11

### Added
- 初始创建：将工具/资源信息抓取整理并归档到仓库根目录 tools.md 的工作流
- 支持 playwright-cli 优先抓取（JS渲染SPA页面）、WebFetch 降级
- 写入前重复检测 CHECKPOINT、分类不确定 CHECKPOINT
- 异常处理表（4类失败场景）与 Red Flags 反例清单（5条）
