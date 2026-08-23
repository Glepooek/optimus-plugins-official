> **本文件在 Git 协作规范中的定位**
>
> 本文件是分支策略与命名规范的描述性参考（讲解性质，不带 MUST/SHOULD/MAY 语气）。
> 在规范体系中，它属于 **`01-branching.md`（分支策略与命名规范）** 的配套参考，被该篇引用。
>
> - **适用场景**：团队评估该采用哪种分支模型、需要具体命名示例、或要理清分支从创建到清理的完整生命周期时查阅
> - **如何结合**：本仓库已在 `01-branching.md` 中选定 GitHub Flow 作为规范条款；本文件的工作流对比部分解释"为什么选它、其他模型适用于什么场景"，供团队评估自身场景是否仍适用
> - **维护**：本文件记录团队通用的分支实践知识，不承载特定仓库的强制约束——强制约束写在 `01-branching.md`

# 分支策略与命名：工作流对比、命名示例、生命周期管理

## 1. 三种主流分支工作流对比

| 维度 | GitHub Flow | Git Flow | Trunk-Based Development |
|---|---|---|---|
| 核心思路 | 主干 + 短命特性分支，随时可发布 | 主干（`main`）+ 长期开发分支（`develop`）+ 特性/发布/热修复分支体系 | 所有人直接（或几乎直接）在主干上开发，分支存活时间极短（数小时到一两天） |
| 分支数量 | 少（`main` + 特性分支） | 多（`main`/`develop`/`feature/*`/`release/*`/`hotfix/*`） | 极少，趋近于零 |
| 发布节奏 | 持续部署，合并即可发布 | 版本化发布，`release/*` 分支收尾 | 持续部署，依赖功能开关（Feature Flag）控制未完成功能 |
| 适用场景 | SaaS / 持续交付产品，一套代码只维护一条生产线 | 需要同时维护多个历史版本（如客户端软件、需要长期支持多个发布版本） | 团队工程成熟度高、CI/CD 完善、熟练使用功能开关 |
| 主要代价 | 需要功能开关配合未完成的大特性，否则易把半成品带入主干 | 分支多、合并链路长，`develop` 与 `main` 易产生漂移 | 对自动化测试覆盖率、功能开关基建要求高，团队纪律要求高 |
| 典型使用者 | GitHub 官方产品团队、多数 Web/SaaS 团队 | 需要多版本并行支持的桌面/嵌入式/企业软件团队 | Google、Facebook 等超大规模工程团队 |

**为什么本仓库的规范条款选 GitHub Flow**（见 `01-branching.md` §1）：本仓库是持续演进的插件仓库，不需要同时维护多个历史发布版本，Git Flow 的 `develop`/`release` 分支体系对这种场景是不必要的额外协调成本；同时团队规模与自动化测试覆盖尚不足以支撑纯粹的 Trunk-Based Development（功能开关基建缺失）。GitHub Flow 是两者之间的平衡点。

## 2. 分支命名示例大全

命名格式约定见 `01-branching.md` §2：`<type>/<简短描述>`。以下按 `type` 分类给出示例：

| type | 用途 | 命名示例 |
|---|---|---|
| `feature` | 新功能开发 | `feature/add-login`、`feature/123-user-profile-page` |
| `fix` | 非紧急 bug 修复（走正常发布节奏） | `fix/null-reference-on-logout`、`fix/456-pagination-off-by-one` |
| `hotfix` | 生产环境紧急修复（需立即发布） | `hotfix/critical-payment-timeout`、`hotfix/789-security-patch` |
| `release` | 发布收尾分支 | `release/2.3.0`、`release/v2.3.0-rc` |
| `chore` | 无业务逻辑变更（依赖升级、配置调整） | `chore/upgrade-dotnet9`、`chore/update-ci-cache` |
| `docs` | 纯文档变更 | `docs/update-readme`、`docs/api-migration-guide` |
| `refactor` | 不改变行为的内部重构 | `refactor/extract-payment-service` |

**常见团队实践变体**（非本仓库强制要求，供参考）：

- **带日期前缀**：`2026-08/feature/xxx`——适合发布节奏按日历周期的团队，但会让分支名变长且与 issue 追踪脱节，多数团队不采用
- **带作者缩写**：`feature/js-add-login`——`01-branching.md` 已明确禁止用姓名作为唯一标识，但缩写+功能描述的组合本质仍是姓名标识，同样不推荐
- **纯 issue 编号**：`feature/JIRA-1234`——editor/IDE 里排序整齐，但脱离编号系统时完全不可读，建议至少保留简短描述作为编号的补充（如 `feature/1234-add-login`）

## 3. 分支生命周期管理

一个特性分支从创建到清理的完整流程：

### 3.1 创建

```bash
git checkout main
git pull origin main          # 确保从最新主干拉分支
git checkout -b feature/add-login
```

### 3.2 与主干同步

特性分支存活期间，主干可能持续有新提交合入。为避免分支存活过久后产生大规模冲突，应定期同步：

```bash
git checkout feature/add-login
git fetch origin
git rebase origin/main         # 或 git merge origin/main，团队统一一种策略
```

- **rebase 方式**：历史线性，但已推送的分支 rebase 后需要 `git push --force-with-lease`（不要用裸 `--force`，避免覆盖他人在同一分支上的提交）
- **merge 方式**：历史保留合并节点，安全但主干历史会有额外的合并提交

多数团队对"同步自己的特性分支"用 rebase（分支通常只有自己在用，force push 风险低），对"合入主干"用团队统一的合并策略（见 `03-pull-requests.md` §2）。

### 3.3 合并后清理

PR 合并后，分支已完成使命，应及时清理，避免分支列表堆积：

```bash
git checkout main
git pull origin main
git branch -d feature/add-login              # 删除本地分支
git push origin --delete feature/add-login   # 删除远程分支（多数 Git 平台支持 PR 合并后自动删除）
```

批量清理已合并且远程已删除（显示为 `[gone]`）的本地分支：

```bash
git fetch --prune
git branch -vv | awk '/: gone]/{print $1}' | xargs -r git branch -D
```

### 3.4 生命周期健康信号

- **健康**：特性分支存活 1-3 天内完成开发并发起 PR，合并后立即删除
- **风险信号**：分支存活超过 1-2 周未合并——通常意味着任务拆分过大，应考虑拆成更小的可独立合并的分支（配合功能开关隔离未完成部分）
- **危险信号**：本地或远程堆积大量已合并却未清理的分支——不影响功能，但会让 `git branch` 列表失去导航价值，建议定期批量清理（如上述 `--prune` 命令）
