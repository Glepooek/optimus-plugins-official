# Changelog

## [1.3.0] - 2026-09-04

### Changed
- **存储格式从 `tips.txt` 迁移为 `tips.jsonl`**：每行一个 JSON 对象 `{id, category, title, body}`，`id` 为稳定主键（命令/参数/功能名），`body` 内用真实换行。原格式靠 `---` 分隔行 + 字面量 `\n` 拼接字段，判重需正则提取、计数需数分隔符，两者都易错；JSONL 下判重是查 `id` 集合、计数是数行数
- 第二步判重从「grep 正则提取标识符」改为「读 JSONL 构建 `ids` 与 `aliases` 两个集合」，新增 `norm_alias()` 归一化：去斜杠前缀、`-`→`_`、统一小写，使 `/code-review`≡`code-review`≡`code_review`、`--flag`≡`flag` 能命中同一键
- 第四步写入方式改为行级操作：新增=追加一行 JSON、修改=整行替换、删除=移除该行，不再需要处理 `---` 分隔符的成对增删
- 第五步条目计数从「数 `^\[` 开头行」改为「数 JSON 行」（`grep -c '^{'` 与 `wc -l` 交叉验证）

### Added
- **新增 `scripts/` 目录**，把第二步的两个内联 Python 块抽为可测脚本，配 46 个 unittest（本机无 pytest，与仓库另两个维护型 skill 一致）：
  - `build_alias_index.py` — 读 tips.jsonl 构建 `{ids, aliases}` 标识符集，输出 JSON
  - `detect_residue.py` — 库内残影召回，输出待人工裁决的候选
  - `test_build_alias_index.py` / `test_detect_residue.py` — 22 + 24 tests
- 第二步新增「辅助：库内残影检测」小节：对已有条目做主标识符分组 + 功能描述重叠召回，捕捉历次 sync 累积产生的互相覆盖冗余——此前判重是单向的（新条目 vs 已有），库内互相覆盖永远检测不到
- 第三步新增「环境可用性门」：条目须在本机 harness 下确实能跑，mac/Linux 专属、Enterprise 席位、需组织管理员权限、云厂商 SDK、claude.ai 账号会话类一律判 ⏭️ 跳过。判据是「有无硬性阻断」而非「听起来像不像企业向」——本机走自定义网关，网关类条目反而可用
- 第三步完整性校验的「完整可执行形式」从只覆盖 CLI 命令扩展为三种形态：CLI 命令、斜杠命令、skill 名（须写触发形式），并显式禁止裸缩写（不得写 `/tdd`、`debugging`、`parallel-agents` 这类敲不出来的简称）
- 第四步「修改」补充两条约束：覆盖旧语义而非在原句后追加版本沿革从句；长度自检不超过 body 中位数的 2 倍
- 第五步格式校验从「验前 4 字段前缀顺序」改为「验 `{id,category,title,body}` 四字段齐全 + 统计 body 内 `功能：`/`效果：`/`例子：` 各前缀出现次数，任一 > 1 即报错」，捕捉同一条内字段语义重复
- `known-issues.md` 新增「2026-09-04 JSONL 迁移后的实测复核」小节，用脚本复核数据层现状并与台账记录值对照

### Fixed
- **修复内联版残影检测形同不存在**：`items = []` 从未被填充，两层循环永不执行，候选恒为 0。脚本化后实测召回 5 个候选，其中 `/doctor` 那两条经人工确认是真残影（后者完整覆盖前者的别名、CLAUDE.md 裁剪、版本信息，还多出安装健康/未用 skill/慢 hook 等内容）
- **修复 aliases 集被通用英文词污染**：加固版曾用 `\b[a-z][a-zA-Z]{3,}\b` 收录正文所有 4 字母以上小写词，集合膨胀到数千个通用词（`effect`、`when`、`with`…），任何 changelog 功能点都能"命中"→ 判重恒为已覆盖、新增恒为 0。改为只收带语法标记的标识符后 aliases 从 1622 收敛到 1475，通用词清零。这是不报错的静默失效，已被 `TestExtractRejectsNoise` 锁住
- **修复文件路径被误当斜杠命令**：`.claude/settings.json` 的 `/settings`、`~/.claude` 的 `/claude`、`github.com/example/repo` 的 `/example` 均被收录为命令。斜杠命令模式加前置断言 `(?<![\w./~-])` 排除路径分量，真 flag（`--settings`）与真命令（`/cost`、`/superpowers:brainstorming`）全部保留
- **修复中文按连续片段整取导致真残影召回率为 0**：`是完整的配置体检工具` 被当成单个 token，与另一条的 `设置体检` 永不重合。改为 bigram（2-gram）切分，`/doctor` 那两条的重叠率从 0 变为可测的 0.263
- 残影检测阈值按实测分布定为 0.25 并明确「只召回不判定」定位：真残影（0.263）与非残影（`MCP-资源列出 ⊇ MCP-服务器`，0.333）在数值上交叠，纯词频无法可靠区分，最终取舍交由第四步 CHECKPOINT 由用户裁决
- **第五步同步点从 4 处补全为 6 处**：扫描正则由 `条技巧`（要求两词紧邻）放宽为 `条[^，。|]*技巧`，随即发现 `.kiro/steering/structure.md` 与 `.kiro/steering/product.md` 两处措辞为「N **条使用技巧**」——中间插了「使用」二字，旧正则永不命中，两处数字从未被任何一轮 sync 更新过，长期停在 425（真实 276）。甄别表补两行 ✅、PowerShell 循环补两个路径、兜底表与第六步摘要口径同步改为 6 处
- 甄别表 ❌ 不动项「默认每次显示 2 条技巧」更正为「6 条技巧」，与 show-tip.sh 本次的默认值变更对齐
- `test-prompts.json` 的 id 1 expected 中「同步 5 处文档数字」校正为实际处数（SKILL.md 第五步已是 4 处，仅测试素材残留旧数字）。改的是对事实的描述而非期望的行为，不属于「重写既有测试条目」
- `known-issues.md` 7 条「待处理」标记为「已修复」（1.3.0）。剩余 1 条（分类标签是未经验证的事实断言）规则未加固，如实保留待处理

### Notes
- 本次 SKILL.md 属 `.claude/` 下改动，不触发仓库 marketplace 版本升级
- 同批次的 `plugins/optimus-devops-plugin/hooks/` 改动另按仓库规则升版：show-tip.sh 读 JSONL + 默认显示条数 2→6（Patch）、**删除 `install.ps1`**（删除用户可见功能 → Major）。install.sh 已完全覆盖其能力且内置 Windows 下的 BurntToast 检测，唯一差异是 ps1 曾提供交互式 `Install-Module`，现改为打印命令由用户自行执行——交互式安装不适合放在安装脚本里，跨 shell 传 stdin 也不可靠

## [1.2.3] - 2026-09-04

### Added
- `known-issues.md` 新增 8 条待处理问题，来自 tips.txt 三轮全量人工核对（315→297→293→267）：分类标签是未经验证的事实断言、例子字段的标识符使用照抄敲不出来的简称、同一条内字段语义重复能通过格式校验、别名字面不同导致判重失效、库内已存在条目之间的互相覆盖不被检查、「修改」实际执行时变成追加版本沿革、新增判定缺少「本机环境能否使用」这道门、同步点处数在 SKILL.md 与 test-prompts.json 中说法不一
- `known-issues.md` 新增「取证方法备注」小节：判定名字归属的一手证据源是本机原生二进制（文档滞后于发布），附内置 skill/subagent/命令三种注册形态的提取命令，以及两个已踩过的坑——常量表混有插件项不能作内置证据、正则写窄会把「存在」误判成「不存在」
- `test-prompts.json` 追加 7 条测试 prompt（id 10-16），与上述前 7 条待处理问题一一对应，供后续 darwin-skill 优化循环作为验证素材

### Changed
- 无 SKILL.md 行为变更——本次仅补台账与测试素材。8 条"待处理"已超过 `06-continuous-improvement.md` 规定的 3 条阈值，需人工显式发起一次 darwin-skill 优化循环后才会落到 SKILL.md 的检测逻辑上

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
