# Hello 算法蒸馏 · 流水线状态

## 当前阶段
阶段 2 进行中（1/8 完成）——详见 `STAGE2_HANDOFF.md` 获取完整交接信息（frontmatter 约定、
剩余 7 个 skill 的 merged_from 映射、产出清单）

## 已完成
- [x] 阶段 0：`BOOK_OVERVIEW.md`（已获用户确认：突出工程实践决策导向）
- [x] 阶段 1：5 个并行 extractor 全部完成
  - frameworks.md（16 条）/ principles.md（36 条）/ cases.md（22 条）/
    counter-examples.md（23 条，经历一次连接中断重跑）/ glossary.md（20 条）
- [x] 阶段 1.5：三重验证 → `verified.md`
  - 8/8 skill 簇全部通过，`rejected/` 为空（已附 README 说明理由）
  - **用户轻确认已获得**：8 个 skill 列表无需合并/拆分/调整优先级
- [x] 阶段 2 · Skill 1/8：`data-structure-selection`（SKILL.md + CHANGELOG.md +
      README.md + test-prompts.json 四文件齐全，作为后续 7 个 skill 的范本）

## 待办
- [ ] 阶段 2 · Skill 2-8：complexity-analysis / sorting-algorithm-selection /
      search-algorithm-selection / dynamic-programming-problem-solving /
      greedy-algorithm-applicability / divide-and-conquer-problem-check /
      backtracking-algorithm-template（详细素材映射见 `STAGE2_HANDOFF.md`）
- [ ] 阶段 3：Zettelkasten 链接 + INDEX.md + GLOSSARY.md（整理自 candidates/glossary.md）
- [ ] 阶段 4：每个 skill 的 test-prompts.json + 盲测
- [ ] 阶段 5：DIGEST.md + 询问安装位置
- [ ] 插件基础设施：`plugins/optimus-learning-plugin/` 目录结构、
      `.codex-plugin/plugin.json`、注册到两侧 marketplace.json（Minor 版本升级）
- [ ] 跨插件重复性自检
- [ ] `commit-cc-plugin` 提交推送

## 8 个 skill 簇（优先级顺序）
1. 数据结构选型决策
2. 复杂度分析方法
3. 排序算法选型
4. 搜索算法选型
5. 动态规划解题三步法
6. 贪心算法适用性判断
7. 分治问题判断
8. 回溯算法框架模板
