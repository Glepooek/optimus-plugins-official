# Changelog

## [1.2.2] - 2026-09-03

### Fixed
- 第五步同步点清单从「只有 2 处」补全为 **4 处**，新增 `plugins/optimus-devops-plugin/.codex-plugin/plugin.json`（`interface.longDescription`）与 `.kiro/steering/plugins.md` 两处——这两处随 Codex 兼容层和 Kiro steering 引入，此前从未被收录，导致 `.kiro/steering/plugins.md` 的条目数长期停在 425 而未被任何一轮同步发现
- 定位命令从「按固定文件列表 grep」改为**全仓库扫描**（`grep -rn '条技巧' --include='*.json' --include='*.md'` 并排除本 skill 自身文档），避免新增同步点后再次因清单未更新而漏改；PowerShell 的 `Select-String` 循环数组同步补齐两个新路径
- 甄别表补充 4 行：2 行新增的 ✅ 更新项，1 行 `show-tip.sh` 脚本注释的 ❌ 不动项，原有 ❌ 不动项保持不变
- 版本升级说明补充 `.codex-plugin/plugin.json` 的 `version` 须与 marketplace.json 同值（AGENTS.md 要求），并要求升级前先比对当前值——实测该文件曾落后真源两个 Patch（13.0.0 vs 13.1.2）
- 兜底表与第六步摘要模板中的「两处」措辞、「已同步」文件列表同步更新为四处

## [1.2.1] - 2026-08-30

### Added
- 新增 `known-issues.md` 使用期反馈记录机制（空模板），配套仓库新增的 skill 持续优化硬性约定，见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`

## [1.2.0] - 2026-08-18

### Added
- 新增 `.last-synced-version` 持久化状态文件，记录上次同步到的版本号，替代固定的「最近 10 个版本」窗口，避免跨间隔运行时静默漏看更早版本
- 第一步新增基于锚点的 curl\|awk 截断抓取逻辑，锚点为空时保留原有「最新 10 个版本」默认行为兜底
- 第三步新增「差异识别中间过程表」子章节：逐条 bullet 展示摘要/标识符/命中情况/判定，覆盖窗口内每一条 bullet
- 判定从三类（新增/修改/删除）扩展为四类，新增「⏭️跳过」（已覆盖 / 非用户可操作功能）
- 执行摘要新增「⏭️ 跳过 N 条」栏与「🔖 同步锚点」行

### Changed
- 第二步判重方式从「通读全文凭印象比对」改为「grep 预提取标识符清单后查表比对」，成本和漏判风险不再随 tips.txt 篇幅增长而上升
- 第四步、第五步共三处 CHECKPOINT 全部改用 `AskUserQuestion` 结构化确认，替代 y/yes/n/no 自由文本输入
- 「🚦零变更总闸」补充：全部 bullet 均判定为跳过时，仍需推进 `.last-synced-version` 并单独提交（不写 tips.txt）
- 分类清单说明去掉"现有 11 个"硬编码计数

### Notes
- `/sync-cc-tips N` 参数场景下忽略锚点截断，仅处理最新 N 个版本，且不更新 `.last-synced-version`

## [1.1.4] - 2026-08-01

### Fixed
- 第五步「批量更新 5 处数字」表格校准为实际的 **2 处**：此前列出的 `marketplace.json` 顶层 `description`、`README.md` 第 6 行、`README.md` SessionStart 行三处均不含条目数（README.md 第 6 行实为 `## 📦 插件列表`，SessionStart 行写的是无数字的「技巧轮播」），每轮执行都会空跑到「pattern 找不到」兜底分支
- 新增甄别表，显式标注 `hooks/README.md` 中「默认每次显示 2 条技巧」（单次展示条数）和「每条技巧使用 `---` 分隔」（格式说明）两处**不得误改**
- 补充定位命令，先列全部候选再按表甄别；同时给出 Bash 与 PowerShell 两种写法（本机默认 shell 为 PowerShell，无 `grep`），并提示 `Select-String` 多文件模式下 `Filename` 只取 basename、会混淆两个同名 `README.md`
- 第六步摘要模板的「已同步」行移除不参与同步的 `README.md`
- fallback 表三个分支同步改为两处口径

### Notes
- 明确「不要主动往 README.md 等位置添加条目数」——同步点越少越不易失准

## [1.1.3] - 2026-08-01

### Fixed
- 第五步条目计数规则修正：原规定「以 `---` 分隔符数量加 1 为准」，但 tips.txt 采用「每条后均跟分隔符」的追加式格式（末条后也有 `---`），分隔符数已等于条目数，加 1 会每轮多算 1 条
- 计数主口径改为统计 `^\[` 开头的行数（每条 tip 均以 `[分类]` 开头），并给出可直接执行的 `grep -c` 命令；`---` 行数降级为交叉验证手段，附加「旧数 + 新增 − 删除」第三重校验
- 同步修正第五步 fallback 表、CHECKPOINT 与反例黑名单中三处沿用旧 `---` 计数口径的表述

## [1.1.2] - 2026-07-08

### Added
- 第三步新增「触发条件/一线处理/仍失败兜底」三段式 fallback 表，覆盖完整性校验信息缺失、新增与修改条件冲突两种场景（此前第三步是全文唯一没有该表格式的步骤）

## [1.1.1] - 2026-07-08

### Fixed
- 第二步 fallback 表"文件存在但内容为空"分支补充显性 🔴 CHECKPOINT 标记（原仅靠"提示用户确认"措辞，不符合检查点显性标记要求）

## [1.1.0] - 2026-07-07

### Changed
- 第三步新增「信息补全」步骤：生成前交叉关联已有 tips、提取完整参数集、补全用法示例
- 第三步新增「完整性校验」步骤：生成后检查 settings.json 键名、环境变量、版本号、多种用法、关联功能、限制说明

## [1.0.0] - 2026-07-07

### Added
- 初始版本：从 changelog 自动同步 tips.txt 的完整工作流
