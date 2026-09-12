# Changelog — Claude Code Hook 机制规范

本文件记录 `knowledge-base/claude-code-hooks/` 领域的变更历史。版本号按领域独立管理，与其他领域及插件版本号无对应关系。

## [1.0.0] - 2026-09-12

新建领域。索引 43 条（rule 41 / reference 2），8 个文件。

起因是一次真实事故：`optimus-devops-plugin` 的 SessionStart 技巧轮播被改为 `async: true` 以消除启动阻塞，结果轮播完全不可见——hook 照跑、状态文件照推进、技巧被静默消耗，但 `systemMessage` 被改道给了模型而非用户。排查后确认知识库对 Claude Code hook 机制**完全空白**，缺的正是可检索的判断依据。

### Added

- `rules/01-event-selection.md`（7 节）：三类 cadence 与触发频率上限、选型三问、14 个可拦截事件与三个例外、matcher 与 handler 类型的逐事件支持、选型误用四形态、静态约定归 CLAUDE.md
- `rules/02-configuration.md`（6 节）：七个定义位置的作用域与合并语义、matcher 求值的三条字符集路径、`if` 的 best-effort 性质、exec/shell form 的取舍、三个路径占位符、运行环境与无控制终端
- `rules/03-output-contract.md`（8 节，含 5 个三级小节）：exit code 0/2/其他的语义分档、stdout 的 JSON 与纯文本判定、通用 JSON 字段、**`systemMessage` 的逐事件交付去向**、`additionalContext` 的插入位置与措辞要求、`terminalSequence` 白名单、HTTP 响应映射、静默失效清单
- `rules/04-decision-control.md`（5 节）：五种决策模式与逐事件字段、顶层 `decision` 只有 `block`、五处改写能力、hook 不是安全边界的三条理由、prompt/agent handler 的 `ok:false` 逐事件语义
- `rules/05-async-execution.md`（6 节）：`async` 仅 command 可用、输出交付对象从用户变为 Claude、四项语义变化、适用判据、禁止用 async 掩盖同步成本、`asyncRewake`
- `rules/06-security-and-cost.md`（5 节）：workspace trust 的两种会话差异、五条编写实践、进程成本实测基线、PowerShell 占位符三种写法、双 harness 下的定位
- `reference/event-capability-matrix.md`：34 个事件 × 六个能力维度的完整对照，作为 rules 各篇结论的取证出处
- `README.md`、`index.jsonl`

### Notes

**三处刻意的收窄，避免制造过期风险与假条目：**

| 收窄 | 原因 |
|---|---|
| **不抄录各事件的 input 字段表** | 它是查阅型资料而非判断依据，且随版本增删频繁，抄录即制造过期风险。本领域只收契约与判据，字段明细指向官方原文 |
| **异步维度不进能力矩阵** | `async` 是 command handler 的属性而非事件属性。列进事件矩阵会暗示它逐事件不同，实际是逐 handler 不同 |
| **`§ 维度说明` 与 `阅读路径` 不登记索引** | 导航性内容不承载判断依据，按 `knowledge-base/README.md § 索引粒度规范` 有意不登记 |

**与既有领域的零重叠已核查。** 知识库内 `hook` 的既有命中全属别的语义：`git.02.commit-hooks` 与 `git.ref.commit-message-tooling` 讲 git 原生钩子；`host-diagnostics` 的 7 条讲 API Hook 注入手法（被诊断的对象而非工具）。三者的边界已在本领域 `README.md` 顶部与 `rules/06 § 5` 显式建模。

**本领域全部条款仅约束 Claude Code。** 本仓为双 harness，但 Claude 侧 hooks 在 Codex 中不生效，故 `applies_to` 一律不含 Codex。由此派生出 `rules/06 § 5` 的一条规范：仓库级一致性门禁禁止只写在 Claude hook 里，须落在 `.githooks/`。

### 依据

- [Hooks reference](https://code.claude.com/docs/en/hooks)，核对日期 2026-09-12（全文约 3700 行，本领域覆盖其规范性内容）
- 事故取证：本仓 `446328c`（改 async）→ 状态文件 `~/.claude/.tip-state.json` mtime 14:46 证明 hook 执行但输出不可见 → `1.1.16` 回退
- 进程成本实测：Windows + Git Bash，本仓排查「启动与 `/clear` 卡死」时的测量数据
