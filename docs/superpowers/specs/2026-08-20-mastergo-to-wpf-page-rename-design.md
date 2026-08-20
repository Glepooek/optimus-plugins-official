# mastergo-to-wpf 页面 Skill 重命名设计

- **日期**：2026-08-20
- **状态**：待用户审阅

## 目标

将页面组装 Skill 从 `mastergo-to-wpf` 更名为 `mastergo-to-wpf-page`，使用户可见调用名准确表达其“设计稿 → WPF 页面”的职责，并与 `mastergo-to-wpf-components` 的组件库职责区分。

## 范围

1. 将 `plugins/optimus-frontend-plugin/skills/mastergo-to-wpf/` 重命名为 `mastergo-to-wpf-page/`。
2. 将 SKILL.md frontmatter `name` 改为 `mastergo-to-wpf-page`，Skill 版本从 `1.2.0` 升至 `2.0.0`。
3. 更新现行运行文档、交叉引用、README、测试命令、市场描述和测试提示，使其使用新名称和新路径。
4. 在 CHANGELOG 记录旧调用名 `/optimus-frontend-plugin:mastergo-to-wpf` 已被新调用名 `/optimus-frontend-plugin:mastergo-to-wpf-page` 替代。
5. 将 marketplace 版本从 `8.14.3` 升至 `9.0.0`，因为这是用户可见功能重命名。

## 非范围

- 不修改 `docs/superpowers/plans/**` 或 `docs/superpowers/specs/**` 中的旧名称；它们是历史决策记录。
- 不改变 DSL 转换器、组件匹配器或组件抽取器的行为。
- 不保留旧名称的别名，以避免两个用户入口语义分叉。

## 验证

- 现行可执行文件及现行用户文档不再引用 `mastergo-to-wpf`（`mastergo-to-wpf-components` 本身及历史文档除外）。
- 新目录中的离线 unittest、JSON 校验和路径检查通过。
- 既有 `test_optimization.py` 的 9 项基线失败保持单独记录，不作为本次重命名回归。
