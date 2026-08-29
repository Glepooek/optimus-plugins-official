# 知识库分领域版本化与结构优化 — 设计

> 日期：2026-08-29 ｜ 状态：已批准，待实施

## 1. 背景与目标

知识库当前用**一个全局版本号**（根 `README.md` 顶部 `> 版本：7.2.0`）与**一份根 CHANGELOG**（491 行、34 个版本条目）管理 9 个领域。随着领域数从 1 增长到 9，这个模型出现两个问题：

- 任何一个领域的小改动都会推进全局版本号，版本号不再表达"哪个领域变了、变到什么程度"
- 单份 CHANGELOG 混合 9 个领域的历史，读者要找某领域的演进得通读全文

本次同时处理 5 项优化，其中 3 项是版本治理模型变更，2 项是内容与命名修正。

### 5 项需求

| # | 需求 | 分组 |
|---|---|---|
| 1 | 根 CHANGELOG 拆分到各领域 | C |
| 2 | 各领域独立版本号，取消全局版本号 | C |
| 3 | 各领域 `00-README.md` 重命名为 `README.md` | B |
| 4 | algorithms/reference 图解无法在预览中显示 | D |
| 5 | algorithms 领域改名为「数据结构与算法」 | A |

## 2. 执行顺序与版本落点

**顺序必须是 A → B → D → C。** 理由：B 改文件名、D 改 reference 正文，两者都产生需写入 CHANGELOG 的变更；C 负责拆 CHANGELOG 与定版本号，必须最后做，否则要写两遍。

### 版本模型

分叉点为 **7.2.0**：9 个领域全部以 7.2.0 为起始版本，此后各自独立递增。

| 领域 | 本次变更 | 落点 |
|---|---|---|
| `data-structures-algorithms` | 改名（Major）+ 图片回填（Minor）+ README 改名（Patch） | **8.0.0** |
| 其余 8 个 | 仅 `00-README.md` → `README.md`（Patch） | **7.2.1** |

`knowledge-base-maintain` skill：1.8.0 → **1.9.0**（Minor，承载版本模型变更这一新增能力）。

## 3. A 组：algorithms 领域彻底改名

**破坏性变更**（39 条 id 前缀全改），按 Major 处理。

### 3.1 定名

- 中文展示名：**数据结构与算法**（国内教材通行语序；且"先结构后算法"符合该领域四篇 rules 的实际判断链——`02` 选结构在前，`04` 判策略在后）
- 英文标识符：**`data-structures-algorithms`**（下划线不可用，`check_index.py` 的 `ID_RE` 只容许 `[a-z0-9-]`）

### 3.2 改动清单

| # | 对象 | 改动 |
|---|---|---|
| 1 | 目录 | `git mv knowledge-base/algorithms knowledge-base/data-structures-algorithms`（用 `git mv` 保留文件历史） |
| 2 | `index.jsonl` 39 行 | `"id": "algorithms.XX.yyy"` → `"data-structures-algorithms.XX.yyy"`。其余字段不动——`file` 是领域内相对路径，`source` 实测 39 条全是外部 URL（`hello-algo.com` / Microsoft Learn），零处含领域名 |
| 3 | `catalog.json` | `domain` → `data-structures-algorithms`；`title` → 数据结构与算法 |
| 4 | 根 `README.md` | 领域列表、领域职责边界两处 |
| 5 | 领域 `README.md` | 标题、开篇、文件地图中的领域名 |
| 6 | `reference/hello-algo-01-intro.md` | 1 处 `algorithms` 字样（实施时确认是领域名引用还是书名/URL 的一部分，后者不动） |

### 3.3 不改的三处（有意保留）

- `knowledge-base/CHANGELOG.md` 中 7.1.0 / 7.2.0 的 `algorithms` 字样
- `docs/sessions/`、`docs/superpowers/` 下的历史文档
- `reference/` 内 15 篇的 hello-algo 文件名与正文

依据 `knowledge-base-maintain` 现有约定：历史记录类文本记录当时事实，不改写。**已知副作用**：历史读起来会指向一个已不存在的目录名，接受此代价而非改写历史。

### 3.4 为什么此刻改名代价低

`algorithms` 的 `consumers: []`，全仓库 `plugins/`、`.claude/` 对它零引用，`source` 全为外部 URL（因 reference 是外部书籍，理由出处指向原书而非领域内文件），改 id 前缀只在领域内部循环。该领域建立于 2026-08-29（7.1.0/7.2.0 同日），尚无消费者长出。等 code-review 类 skill 开始引用后，同样的改名将需要废弃过渡期。

### 3.5 验证标准

1. `check_index.py` → **483 条 OK**（id 前缀与目录名一致性是强校验项，能自动挡住漏改）
2. `check_index.py --audit` → `catalog.json` **9 领域双向一致**
3. `check_refs.py --strict` → **140 文件 OK**
4. `grep -rn "algorithms\." knowledge-base/*/index.jsonl` → 零命中
5. `git log --follow` 能追到改名前历史

## 4. B 组：`00-README.md` → `README.md`

表面是改名，实质是**改动校验器的白名单契约**。全仓库 88 处 `00-README` 命中中，需改的远少于此。

### 4.1 分类处置

| 类别 | 数量 | 处置 |
|---|---|---|
| 9 个领域的实际文件 | 9 | `git mv` |
| `check_index.py:39` `DOMAIN_META_FILES` | 1 | `{"00-README.md"}` → `{"README.md"}`——**必改**，漏改则 9 个领域 README 全被报为孤儿文件 |
| `check_refs.py` 注释（25、35 行） | 2 | 更新注释文本；逻辑靠 glob 排除，无需改 |
| `test_check_index.py:413`、`test_check_refs.py` 6 处 | ~7 | 测试夹具文件名同步 |
| 领域正文交叉引用 | ~6 | 如 `architecture/README.md` 引 `csharp/00-README.md` |
| `commit-cc-plugin/SKILL.md:23` | 1 | Markdown 链接目标——**唯一插件侧消费者** |
| `knowledge-base-maintain/SKILL.md` | 3 | Step 2、Step 4、失败处理表 |
| CHANGELOG、`docs/`、`.remember/` | ~50 | **不改**（历史事实） |

### 4.2 两个判断

**白名单彻底替换，不留 `00-README.md` 兼容项。** 留兼容会让下次误建 `00-README.md` 时静默通过，而该白名单的作用正是划定"什么文件不算内容"，模糊它就失去意义。

**同名风险需实测**：改名后 `knowledge-base/<domain>/README.md` 与根 `knowledge-base/README.md` 同名。`check_refs.py:35` 注释提到"领域提取与文件路径提取分开"，实施时第一步先读该脚本路径解析逻辑，确认不会把领域 README 与根 README 相互误判。

### 4.3 TDD 顺序

先改 `test_check_index.py` 夹具用 `README.md` → 跑测试确认**失败**（证明白名单确实生效）→ 再改 `check_index.py` 白名单 → 测试转绿。该顺序证明改动有效，而非碰巧通过。

### 4.4 验证标准

1. `unittest` → **133 全绿**（基线已确认 133 通过）
2. `check_index.py` → 483 条 OK，`--audit` 孤儿文件 **0**（本组关键验证：白名单漏改会暴露成 9 个孤儿）
3. `check_refs.py --strict` → 140 文件 OK
4. `grep -rn "00-README" --include="*.md" --include="*.py"` 剩余命中**全部**落在 CHANGELOG / `docs/` / `.remember/`，无一落在 `knowledge-base/*/`、`plugins/`、脚本或测试

## 5. D 组：图解回填

### 5.1 问题的真实性质

**不是失效的图片引用，而是当初有意省略的内容。** `grep '!\['` 在 15 篇 reference 中命中 **0** 次——提取时刻意未导出图解，留下 235 处文本指针：

```
> 📊 原书图：数组定义与存储方式（图解见 https://www.hello-algo.com/chapter_array_and_linkedlist/array/）
```

每篇头部亦声明"图解未导出、原位置以指针指向原书"。因此本组是补做被省略的工作。

### 5.2 关键实测数据

| 事实 | 数据 | 意义 |
|---|---|---|
| 本地图指针总数 | 235 处 | 待替换量 |
| 上游 1.3.0 章节 md | 105 个，含 502 条唯一 alt | 映射来源 |
| alt 文本精确匹配率 | **231/235 = 98.3%** | 可脚本化回填，无需靠位置猜 |
| 未命中 | 4 处（2 个唯一名称） | 人工兜底 |
| 上游图片文件名唯一性 | 485 张**无一重名** | 可平铺单一 `assets/`，不必复刻上游 67 个 `*.assets/` 子目录 |
| 上游图片总体积 | 9.1 MB（485 张） | 实际只下引用到的约 200 张，预计 4-5 MB |
| 网络可达性 | **仅 PowerShell `Invoke-WebRequest` 可达**；curl 与 WebFetch 访问 raw.githubusercontent 均超时 | 实施时不要重走弯路 |

### 5.3 产物形态

```
knowledge-base/data-structures-algorithms/reference/
├── LICENSE
├── assets/                      # 新建，平铺引用到的图
│   ├── array_definition.png
│   └── ...
└── hello-algo-01-intro.md ... 15-greedy.md
```

正文替换：

```markdown
改前：> 📊 原书图：数组定义与存储方式（图解见 https://www.hello-algo.com/chapter_array_and_linkedlist/array/）
改后：![数组定义与存储方式](assets/array_definition.png)
```

用相对路径 `assets/xxx.png`：与索引 `file` 字段的路径约定同形态，且 GitHub 网页、VS Code 预览、本地 Markdown 阅读器三处均可解析。

### 5.4 回填流程

1. **抓映射**：一次性脚本从上游 1.3.0 的 105 个章节 md 提取 `alt → 图片路径`（已实测得 502 条）
2. **下载 + 改写**：按本地 235 处 alt 查映射 → 下载对应图到 `assets/` → 替换正文
3. **人工兜底 4 处**：`开放寻址`（1 处）、`在二叉搜索树中删除节点`（3 处）——上游 alt 带子标题（原书按度为 0/1/2 分了三张图），需对照原书章节确定各处配图

脚本为**一次性工具，跑完不留仓库**——不属于 `knowledge-base-maintain` 的常规能力，留下会成为无人维护的死代码。

### 5.5 许可证影响

图解是《Hello 算法》原作的一部分，CC BY-NC-SA 4.0 **允许再分发**，条件为署名（BY）、非商业（NC）、相同方式共享（SA）。现有三层隔离已覆盖：`reference/LICENSE` 全文、每篇头部 krahets 署名块、`catalog.json` 与两处 README 的目录级隔离声明。**新增图片不改变授权结构。**

须改一处：每篇头部「图解未导出、原位置以指针指向原书」的改动说明已不成立，改为「图解逐字随书提取」。

### 5.6 验证标准

1. `grep -rc '📊 原书图' <领域>/reference/*.md` → **0**（235 处全部替换）
2. `grep -rhoE '\]\(assets/[^)]+\)'` 的每个文件名在 `assets/` 下真实存在（无断链）
3. `check_index.py` → 483 条 OK，`--audit` 孤儿文件 **0**（`assets/*.png` 非 `.md`，7.1.0 已实测 `LICENSE` 不被报孤儿，图片同理）
4. 人工抽查 3 篇预览渲染，确认图显示
5. `grep -c '图解未导出'` → 0

## 6. C 组：CHANGELOG 拆分与领域独立版本号

### 6.1 版本号位置

- **各领域 `README.md` 顶部** `> 版本：x.y.z`
- 根 `README.md` 顶部**不再有版本行，也不放一览表**

### 6.2 CHANGELOG 拆分规则

根 `knowledge-base/CHANGELOG.md` **删除**。34 个历史条目：

| 处置 | 条目 | 说明 |
|---|---|---|
| **直接删除** | 2.0.0、3.0.0、4.0.0、5.0.0 | 全库治理记录（建保护网、规则质量治理、全库查重、`enforcement` 推广），不属任何单一领域 |
| **归入单一领域** | 7.1.0 / 7.2.0 → dsa；1.9.x / 1.10.x → media；其余按内容判断 | 多数历史属此类 |
| **切成两半** | 6.0.0（csharp 迁出 / architecture 迁入）、5.1.0、7.0.0 等 | 每侧标注「衍生自全局 X.Y.Z」，保留跨领域关联的可追溯性 |

各领域 `CHANGELOG.md` 结构：

```markdown
# Changelog — <领域名>

## [8.0.0] - 2026-08-29
（本次变更）

---

## 全局版本时代（2026-08-22 .. 08-29）

以下条目记录本领域在知识库使用统一全局版本号期间的变更，版本号为当时的全局版本。

### 衍生自全局 7.2.0 - 2026-08-29
（该领域相关部分）
```

### 6.3 已知损失（已确认接受）

- 跨领域条目切开后**两侧都不完整**，丢失"这几件事是同一次决策"这层信息
- 4 条全库治理记录**永久丢失**，含「level 全 MUST 的真实原因是 76% 条目小节内混级」等实测结论

**可接受的理由**：其中有价值的判断已沉淀在根 `README.md` 正文（"level 与 enforcement 的分工"、"覆盖率不追求 100%"、"reviewed_at：读过才填"等章节），删 CHANGELOG 不等于丢掉这些知识。

### 6.4 skill 同步改动（1.8.0 → 1.9.0）

| 位置 | 改动 |
|---|---|
| **Step 6 整节重写** | 「更新根 `README.md` 顶部版本 + 追加根 CHANGELOG」→「更新 `<domain>/README.md` 顶部版本 + 追加 `<domain>/CHANGELOG.md`」 |
| Step 6 新增判断 | **一次变更涉及多个领域时，每个领域各自升版本、各自写 CHANGELOG**——新模型下最易做错处 |
| Step 2 新建领域 | 须同时创建 `README.md`（含版本行）+ `CHANGELOG.md`（起始 `1.0.0`）+ 空 `index.jsonl` + `catalog.json` 登记 |
| Step 4 迁移五处 | 「领域 `00-README.md` 的文件地图」→「领域 `README.md`」 |
| 失败处理表 | `csharp/00-README.md` → `csharp/README.md` |

### 6.5 新增校验：版本号一致性

**检查内容**：每个领域 `README.md` 顶部 `> 版本：x.y.z` 必须与该领域 `CHANGELOG.md` 最新条目的版本号一致。

**理由**：旧模型只有一处版本号，靠人看就够；新模型版本号散落 9 处，必须机械校验，否则"独立版本号"会在几次提交后漂移成不可信数据。这也符合 `AGENTS.md` 的"引导器要配传感器"原则——本次给出了新的版本治理引导，须同时给出对应刹车。

**实现位置**：`check_index.py` 的全局检查部分（与 `catalog.json` 双向一致性同层），先写测试再实现。

### 6.6 验证标准

1. 9 个领域各有 `README.md`（含版本行）与 `CHANGELOG.md`；根 `CHANGELOG.md` 已删除
2. 根 `README.md` 顶部无版本行，"维护约定"中指向根 CHANGELOG 的表述已改写
3. 新增校验：故意改错某领域 README 版本 → `check_index.py` **报错**；改回 → OK
4. `unittest` 全绿（新增校验须带测试，133 → 约 136）
5. `grep -rn "knowledge-base/CHANGELOG"` 剩余命中只在 `docs/` 与 `.remember/`；`test_check_refs.py:319` 的断言需改

## 7. 基线数据（实施前实测）

| 检查 | 基线 |
|---|---|
| `check_index.py` | 483 条 OK |
| `check_refs.py --strict` | 140 文件 OK |
| `unittest` | 133 tests OK |
| 领域数 | 9（algorithms 39 / architecture 64 / csharp 143 / design-patterns 35 / dotnet 1 / git 15 / media 11 / skill-authoring 43 / wpf 132） |

## 8. 提交

按仓库 `AGENTS.md` 强制要求，走 `commit-cc-plugin` skill，不自行执行 git 工作流。

`knowledge-base/` 与 `.claude/` 下的改动**不触发 marketplace 版本升级**：`.claude/` 下任何文件按仓库 `AGENTS.md` 版本管理规则不升版本，`knowledge-base/` 不在 `plugins/` 路径下。本次全部改动均落在这两处，因此 `.claude-plugin/marketplace.json` 与各插件 `.codex-plugin/plugin.json` 都不动。

两个 skill 的自身 `metadata.version` 仍需升级（这与 marketplace 版本是两套独立编号）：

| skill | 现版本 | 升级 | 原因 |
|---|---|---|---|
| `knowledge-base-maintain` | 1.8.0 | **1.9.0**（Minor） | Step 6 版本模型重写 + 新增版本一致性校验 |
| `commit-cc-plugin` | 待读取 | **Patch** | 仅一处 Markdown 链接目标随 B 组改名 |
