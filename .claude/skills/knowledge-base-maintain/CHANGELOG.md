# Changelog

## [1.1.0] - 2026-08-27

### Added
- `check_index.py` 新增校验维度：schema 必填字段与类型、`kind`/`level`/`enforcement`/`status` 枚举、`id` 格式与领域前缀一致性、`file` 路径越界（`..`/绝对路径）、孤儿文件（未被索引引用的 Markdown）、`reviewed_at` ISO 日期格式
- `check_index.py` 新增 `--audit` 健康报告：记录数、`kind`/`level` 分布、规范文件的二级标题索引覆盖率、孤儿文件清单
- `check_index.py` 新增 `catalog.json` 双向一致性校验：登记了不存在的领域、存在未登记的领域、登记的分类目录不存在、非法 `status`、重复登记均报错
- Step 2 补充索引粒度判断指引；Step 4 补充迁移/重命名时需同步的四处引用（索引 `file`、领域 README 文件地图、正文交叉引用、消费者 skill 引用含 Markdown 链接目标）
- Step 5 补充常见校验问题对照表（7 类）；失败处理新增孤儿文件与 `catalog.json` 未登记两类
- `test_check_index.py` 从 18 个测试扩展到 55 个，覆盖全部新增校验维度

### Changed
- 校验作用域说明明确化：传 domain 只缩小"文件与锚点"范围，`id` 全局唯一 / `id` 前缀归属 / `catalog.json` 一致性三项始终按全局判定（此前单领域检查会漏报跨领域重复 `id`）
- 正文归属路径改为 `<domain>/rules/`（规范）与 `<domain>/reference/`（描述性），对应知识库目录结构调整
- 新建领域时须同步在 `knowledge-base/catalog.json` 追加领域记录
- Step 7 提交规则统一为一律走 `commit-cc-plugin`，与仓库根 `AGENTS.md` 一致（此前写作 `knowledge-base/` 不受该流程约束，与仓库强制要求矛盾）

## [1.0.2] - 2026-08-22

### Changed
- 领域说明文件路径更新：`knowledge-base/<domain>/README.md` → `00-README.md`（新建领域与规范级别参照示例同步改为 `csharp/00-README.md`）

## [1.0.1] - 2026-08-22

### Changed
- 校验脚本迁入本 skill 的 `scripts/` 子目录，随 skill 分发；运行命令改为 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>`

## [1.0.0] - 2026-08-22

### Added
- 初始版本：引导新增/修改/迁移 knowledge-base 条目，同步索引、CHANGELOG、版本号，调用 check_index.py 做一致性校验
