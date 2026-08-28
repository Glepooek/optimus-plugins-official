# architecture 与 algorithms 双领域新建实施计划

**日期：** 2026-08-29
**对应 spec：** `docs/superpowers/specs/2026-08-29-architecture-algorithms-domains.md`
**状态：** 待批准

---

## 工作量预估

| 阶段 | 内容 | 产出 | 预估 | 可独立提交 |
|---|---|---|---|---|
| A | architecture 领域骨架 + 10 篇 rules + 2 篇 reference | 38-46 条 rule + 2 条 reference（**实际 62 + 2**） | 大 | ✅ |
| B | csharp 五条架构条款迁移改造 + 查重验收 | 5 处正文收窄 + 5 条索引更新 | 中等 | ✅（须紧随 A） |
| C | hello-algo 提取（15 篇 reference） | 15 条 reference | 中等，脚本占主要工作量 | ✅ |
| D | algorithms 4 篇 rules + 查重 | 15-20 条 rule | 中等 | ✅（须紧随 C） |

**总计：** 约 94-107 条新条目，4 次提交。

**执行顺序已定：A+B 先做，C+D 后做。** 两组互不依赖，但 A+B 含迁移改造（会动到既有 `csharp` 条目），先做可让「新建领域 → 消除重复」这条链在一次连续工作中闭环，不留「新领域已建、旧重复未清」的中间态。C+D 只是纯新增，晚做无风险。

**关键路径上的不确定性**：C 阶段的提取脚本质量决定返工概率。字符修复表（`^/`→`//` 等 4 项）已从实读中确认，但 356 页里可能还有未发现的连字替换——因此 C 阶段第一步是**先提取 2 篇做抽样验证**，通过后才批量跑其余 13 篇。

---

## 阶段 A：architecture 领域骨架与规范正文

### A1. 建目录与登记

1. 创建 `knowledge-base/architecture/00-README.md`——参照 `csharp/00-README.md` 章节结构（文档目的、适用范围与读者、规范级别、阅读路径、文件地图），规范级别直接复用 csharp 的 MUST/SHOULD/MAY 定义（skill 失败处理表已明确这样做，无需重新设计）
2. 创建空的 `knowledge-base/architecture/index.jsonl`
3. 在 `knowledge-base/catalog.json` 的 `domains` 追加记录：`domain`/`title`/`categories`/`owner`/`status`/`consumers`（暂为空数组——尚无消费者 skill）/`reviewed_at`

**验证：** `check_index.py architecture` 不报「领域未登记到 catalog.json」

### A2. 写 10 篇 rules 正文

按 spec 第二节的文件清单逐篇写。每篇的撰写约束：

- **条款措辞用 MUST/SHOULD/MAY 对应的中文**（必须/禁止、应该/不应、可以/建议），与既有领域一致
- **语言无关**——正文出现 `record`、`HttpClient`、`ServiceLocator`、`IOptions<T>`、`IMemoryCache`、`DbContext` 这类 .NET 专有类型即违规，应改为引用 csharp
- 每篇头部加 `> 更新历史：2026-08-29 创建。`（与既有领域格式一致）

分两批写，批间跑一次自检（避免 10 篇写完才发现越界，返工面过大）：

**第一批（01-06，承接与基础风格）：**

- `01-layering.md`、`02-design-principles.md`、`03-ddd.md` 是 B 阶段三条迁移的落点，须先确认它们能容纳被摘除的通用条款——写的时候对照 `csharp/rules/01-project-structure.md` §6 与 `csharp/rules/03-design-principles.md` §1/§8 的实际正文，逐条判断该条款的通用部分写进这里的哪一节
- `03-ddd.md` 须区分**战术**（聚合根、值对象、领域事件——csharp 已有部分）与**战略**（限界上下文、上下文映射、通用/支撑/核心子域——csharp 完全没有），战略部分是本次新增价值的主体
- `06-style-selection.md` 必须含反向约束：小规模 CRUD 不应为「显得规范」上 DDD 战术模式；架构成本须与问题复杂度匹配。该条须与 `csharp.03.design-pattern-moderation` 建立引用而非重写（spec 第二节已注明）

**第二批（07-10，.NET 常用架构决策）：** 这四篇是本次扩充的部分，**共同风险是越界到实现层**。每篇写完立即自检「这条如果换成 Java/TypeScript 还成立吗？」——不成立则说明写的是 C# 落地，应移到 csharp 或改为引用。

| 文件 | 必须回答 | 明确不写（属 csharp） |
|---|---|---|
| `07-cqrs-and-slices.md` | 读写模型何时该分离、中介者模式的间接层成本是否值得、按功能组织 vs 按技术层组织、切片间共享代码放哪 | `MediatR` 的注册方式、`IRequestHandler<,>` 签名 |
| `08-module-boundaries.md` | 何时拆项目、单体内模块化的边界形态、循环依赖的架构级处置、拆微服务的实际门槛 | `.csproj` 的 `ProjectReference` 写法、`InternalsVisibleTo` |
| `09-composition-root.md` | 注册该不该集中、生命周期选择的架构含义、启动期是否校验依赖图 | `IServiceCollection` 扩展方法怎么写、`AddScoped` vs `AddSingleton` 的 API |
| `10-cross-cutting.md` | 日志/缓存/事务/校验/授权 各自该落在哪一层、由中间件/装饰器/拦截器中的哪个承载 | `IMemoryCache` 过期配置、`ILogger<T>` 注入方式 |

**验证（两批各跑一次）：**

```bash
# 确认是规范条款而非叙述
grep -c '必须\|禁止\|应该\|不应' knowledge-base/architecture/rules/*.md
# 确认语言无关：应无命中
grep -n 'record\|HttpClient\|ServiceLocator\|IOptions\|IMemoryCache\|DbContext\|IServiceCollection\|ILogger' knowledge-base/architecture/rules/*.md
```

### A3. 写 reference 与索引

1. `reference/architecture-styles-comparison.md`：四种风格横向对比（分层/六边形/整洁/DDD），每种给「解决什么问题、代价是什么、什么情况下不该用」
2. `reference/dotnet-architecture-decisions.md`：.NET/C# 生态的具体架构决策记录——单体 vs 微服务的实际门槛、`MediatR` 的收益与代价、Repository 在 EF Core 下是否仍必要、AutoMapper 类工具的取舍、模块化单体的落地形态。**这篇是 reference 不是 rule**，可以出现 .NET 类型名（A2 的语言无关约束只管 `rules/`）
3. 逐条写 `index.jsonl`（**末尾追加，不重排**），必填八字段 + 五个治理字段
4. `enforcement` 逐条判，按外壳检验：架构条款绝大多数是 `review`（判的是设计意图）；`ci` 仅给真能被工具判定的（如项目引用循环编译器可判、分层依赖方向可用架构测试库断言）；`advisory` 给选型对比与「什么规模下引入」这类判断题
5. `source` 指向两篇 reference 的对应标题（数组形式）——`01`-`06` 主要指向 `architecture-styles-comparison.md`，`07`-`10` 主要指向 `dotnet-architecture-decisions.md`

### A4. 阶段验收

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"          # 全库 OK
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict  # OK
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py" --top 20
```

**查重是本阶段最重要的一关**：A 写完但 B 未做时，architecture 与 csharp 必然出现高分重复候选——**这是预期的**，正是 B 阶段要消除的。记录下这批候选的分数作为 B 的基线，B 做完后应显著下降。

版本：`knowledge-base` 5.0.0 → 5.1.0（Minor，纯新增领域）。**A 单独提交时按 Minor**；若 A+B 合并提交则直接 6.0.0。

---

## ✅ 阶段 A 执行结果（2026-08-29 落地）

**验收全部通过：**

| 检查 | 结果 |
|---|---|
| `check_index.py`（全库） | OK，345 → **409** 条 |
| `check_refs.py --strict` | OK，101 → **113** 文件 |
| `unittest discover` | **133 全绿** |
| 条款密度 | 10 篇各 19-34 条规范措辞，无叙述性空篇 |
| 语言无关自检 | 条款正文零 .NET 类型名；5 处命中全为「C# 侧…见 csharp/…」跨领域引用行 |

**实际产出 62 条 rule + 2 条 reference**（高于预估 38-46）。原因是按小节登记：10 篇共 61 个二级小节，逐节实测措辞后确认每节都含至少一条「必须/禁止」，`level` 全部 MUST（实测非默认）。`enforcement` 分布 `review` 50 / `ci` 8 / `advisory` 4；16 条带 `source`。

**8 条 `ci` 均通过外壳检验**（判的是实质非外壳）：`01.dependency-direction`、`01.assembly-location`、`03.domain-purity`、`04.core-boundary`、`04.port-ownership`、`05.dependency-rule`、`09.composition-root-uniqueness`、`10.concern-ownership`。

**执行中被校验器抓到的一处自造缺陷：** 篇首写 `§ 4. 解决方案布局 与 § 7. 项目类型约定` 时，`check_refs.py` 报「引用写『解决方案布局 与』，实际为『解决方案布局』」——两个引用挤在一句里会让「与」被解析进标题。已改为两句分开。这验证了「引用必须带章节标题」的价值：只写 `§ 4`/`§ 7` 时该错误不会被检出。

**查重基线（B 阶段的消除目标）：**

| 分数 | 候选对 | 是否在原迁移清单内 |
|---|---|---|
| **0.917** | `architecture.02.composition-over-inheritance` ↔ `csharp.03.composition-over-inheritance` | ❌ **新发现**，已补入 spec 第四节第 4 项 |
| 0.691 | `architecture.03.aggregate` ↔ `csharp.03.domain-modeling-ddd` | ✅ 清单第 3 项 |
| 0.613 | `architecture.02.solid-checkpoints` ↔ `csharp.03.solid-principles` | ✅ 清单第 2 项 |
| 0.556 | `architecture.01.dependency-direction` ↔ `csharp.01.layering-direction` | ✅ 清单第 1 项 |
| **0.537** | `architecture.09.composition-root-uniqueness` ↔ `csharp.03.dependency-injection` | ❌ **新发现**，已补入 spec 第四节第 5 项 |
| 0.511 | `architecture.01.layering-model-choice` ↔ `csharp.01.layering-direction` | ✅ 清单第 1 项（同源） |
| 0.477 及以下 | `09.lifetime-architecture-impact` ↔ `csharp.09.dbcontext-lifecycle`、`03.domain-purity` ↔ `csharp.03.domain-modeling-ddd` 等 | 逐对判定，多数属合理分层 |

**两条新发现的成因**：调研阶段按「架构」「分层」「SOLID」「DDD」关键词反查迁移源，而这两条的条款措辞里没有这些词——按关键词反查会漏，与 v1.5.0 那次「按文件迁移会漏」是同一类教训的另一个变体。

版本：`knowledge-base` 5.0.0 → **5.1.0**（Minor，纯新增领域）。


---

## 阶段 B：csharp 架构条款迁移改造

按 spec 第四节的八项清单执行（**清单已由 6 项扩为 8 项，待迁移条款由 3 条扩为 5 条**——A 阶段查重实测新增两条，见上方「阶段 A 执行结果」）。逐项做法：

### B1. 五处正文收窄

对以下五条，逐条判断每条条款是**通用架构约束**还是**C# 特有落地**：

| # | 条目 | 目标章节（A 阶段已确定的实际标题） | 已初判的 C# 特有保留项 |
|---|---|---|---|
| 1 | `csharp.01.layering-direction` | `architecture/rules/01-layering.md § 1. 分层模型的选择与统一`、`§ 2. 依赖方向`、`§ 3. 跨层契约` | 「测试项目引用无关实现项目」（C# 项目引用机制特有） |
| 2 | `csharp.03.solid-principles` | `architecture/rules/02-design-principles.md § 1. SOLID 原则的可执行检查项` | 「上帝类不通过 review」（review 侧表述） |
| 3 | `csharp.03.domain-modeling-ddd` | `architecture/rules/03-ddd.md § 4. 聚合`、`§ 6. 领域事件`、`§ 7. 领域层的纯净性` | 「值对象用 `record`、实体用 `class` + 身份标识」（C# 类型选择） |
| 4 | **`csharp.03.composition-over-inheritance`**（新增，0.917） | `architecture/rules/02-design-principles.md § 2. 组合优于继承` | 「用 `sealed` 标记不打算被继承的类」（C# 关键字） |
| 5 | **`csharp.03.dependency-injection`**（新增，0.537） | `architecture/rules/09-composition-root.md § 1. 组合根的唯一性`、`§ 3. 生命周期选择的架构含义`、`§ 4. 构造期的约束` | 「`HttpClient` 注册为 `Singleton`」「`Lazy<T>` 惰性推迟」+ 两段 C# 代码示例 |

操作步骤：

1. 打开对应小节，逐条判断归属
2. 通用条款删除，节首加一行引用：`通用约束见 knowledge-base/architecture/rules/0N-xxx.md § N. <标题>。C# 侧的附加要求：`（**引用必须带章节标题**，形式与 `wpf/rules/01-environment.md:9` 已有的两处保持一致）

🔴 **CHECKPOINT — 引用写法**：一句里只放一个 `§` 引用。A 阶段实测：`§ 4. 解决方案布局 与 § 7. 项目类型约定` 会让「与」被解析进标题，`check_refs.py --strict` 报错。需要引用多个章节时分句写。

🔴 **CHECKPOINT**：若某节摘除通用部分后**无任何 C# 特有内容剩余**，不留空壳引用条目——改走 Step 4.5 废弃流程（`status: deprecated` + `summary` 指向 architecture 对应条目 `id`），并按 Major 升版。第 5 条（依赖注入）的 C# 特有内容最多（含两段代码示例），第 2 条（SOLID）最薄，收窄时须特别确认它是否还站得住。

### B2. 索引与文件地图同步

1. `csharp/index.jsonl` **五条**的 `summary` 改为反映收窄后内容；`id`/`file`/`anchor` **全部不动**
2. `csharp/00-README.md`：文件地图若因标题变化需同步；「权威参考」处提及 architecture 领域
3. `architecture/rules/*` 中需要 C# 落地细节的位置，反向引用 csharp（带章节标题）。A 阶段已在 `01`/`02`/`03`/`08`/`09` 五篇篇首写入，B 阶段核对是否还需补充

### B3. 阶段验收

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py" --top 20
```

**硬性验收：** architecture ↔ csharp 之间**不得存在 ≥0.6 的候选**。基线是 A 阶段记录的六对（最高 0.917），做完后这六对应全部降到 0.6 以下。若某对仍 ≥0.6，说明该条通用条款在两处都还写着，回到 B1 继续收窄。这是整个 B 阶段存在的唯一理由——若做完还有高分重复，等于新建领域只是把重复从一处变成两处。

版本：`knowledge-base` 5.1.0 → **6.0.0**（Major，五条 summary 与正文范围收窄属不兼容语义变化）。

---

## 阶段 C：hello-algo 提取

### C0. 许可证落地（已定：C-甲 逐字提取 + 目录级许可证隔离）

已确认 CC BY-NC-SA 4.0，SA 条款的处理方式已选定为**逐字提取 + 目录级许可证隔离**。C1 之前先把这三件做完：

1. `knowledge-base/algorithms/reference/LICENSE`：放 CC BY-NC-SA 4.0 全文
2. `algorithms/00-README.md` 中明确写出：`reference/` 目录内容为 CC BY-NC-SA 4.0 授权，独立于仓库其余部分；`rules/` 为本仓库自撰内容，不受此约束
3. 提取脚本的「来源声明头」模板须含 BY 条款要求的全部署名信息（原作者、书名、版本、章号、原书地址、许可证、提取日期）——BY 是强制条件，不可省略

🔴 **CHECKPOINT**：`reference/LICENSE` 非 Markdown，预期不在 `check_index.py` 的孤儿文件扫描范围内（该检查只看 `.md`），但须**实测确认**。若被报为孤儿，不要为它造索引条目（它不是知识内容），而是确认扫描器的文件后缀过滤逻辑。

### C1. 提取脚本

1. 写一次性脚本（**不入库**——提取是一次动作，不是可复用能力，放 `/tmp` 或临时路径）
2. 脚本职责：按章切分 → 剔页眉页脚 → 字符修复（`^/`→`//`、`^^=`→`===`、`^^.`→`...`、`‑`→`-`）→ 表格走 `extract_table` 转 Markdown → 图片位置插入指针 → 每篇加来源声明头
3. **先只跑第 2 章（复杂度分析）与第 6 章（哈希表）两篇**——一篇代码密集、一篇表格密集，覆盖两类风险

### C2. 抽样验证（门禁）

对这 2 篇逐项确认：

| 检查项 | 判据 |
|---|---|
| 代码块无损坏 | `grep -c '\^/\|\^\^' 该文件` 为 0 |
| 表格未错行 | 人工看 2-3 个表，确认表头与数据列对齐 |
| 图解指针到位 | 与 PDF 原页对照，图题与编号一致 |
| 页眉页脚已清 | `grep -c 'www.hello-algo.com <数字>'` 为 0（来源声明行除外） |
| 未发现新的连字替换 | 通读一遍，找形似乱码的 ASCII 组合 |

**不通过则修字符修复表后重跑，不进入 C3。** 宁可少几篇也不入库损坏内容。

### C3. 批量提取其余 13 篇

通过 C2 后跑完 1、3、4、5、7-15 章。每篇跑完做一次快速 `grep` 检查（`^/` 与 `^^` 残留数为 0）。

### C4. 索引登记与验收

1. 15 条 reference 逐条写 `index.jsonl`：`kind: reference`、**无 `level`**、`anchor` 为空字符串（按整篇登记）、`tags`、`summary`
2. reference 条目**不填 `enforcement`**（校验器强制：`kind: reference` 不得有 `enforcement`）
3. 填 `status`/`applies_to`/`reviewed_at`/`owner`

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" algorithms
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" --audit   # 确认无孤儿文件
```

版本：`knowledge-base` → Minor（纯新增 reference）。

---

## 阶段 D：algorithms 规范条款

### D1. 写 4 篇 rules

按 spec 第三节清单。撰写约束：

- **条款由维护者撰写，不照抄教材**——PDF 全书「禁止」0 次、「必须」15 次，没有现成条款可搬。做法是从书中事实（如「哈希表平均 O(1)、最坏 O(n)」）推出可判断的条款（如「须评估哈希冲突退化风险，禁止在对手可控输入场景依赖平均复杂度」）
- 每条须**可用于合规判断**——写不出「怎样算违反」的内容不该做成 rule，应留在 reference
- **逐条对照 `csharp.07.*` / `csharp.08.*` 查重**：`csharp.07.collection-preallocation`（预分配）、`csharp.07.boxing-avoidance`（装箱）、`csharp.08.concurrent-collections`（并发集合）与本领域「数据结构选型」天然接近，须明确分工——algorithms 说「为什么选这个结构」，csharp 说「在 C# 里怎么用不踩坑」

### D2. 索引与治理字段

`enforcement` 预期以 `review` 为主（复杂度与选型判断需人工评估）；`source` 指向 `reference/hello-algo-*.md#<标题>`。

### D3. 阶段验收

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py"
python ".claude/skills/knowledge-base-maintain/scripts/check_refs.py" --strict
python ".claude/skills/knowledge-base-maintain/scripts/find_duplicates.py" --top 20
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"
```

**硬性验收：** algorithms ↔ csharp 之间不得有 ≥0.6 候选。0.4-0.6 区间的逐对判定，属「合理分层」的记录理由后放行。

版本：`knowledge-base` → Minor。

---

## 全局验收（四阶段完成后）

| # | 检查 | 期望 |
|---|---|---|
| 1 | `check_index.py`（全库） | `OK`，记录数 345 → 约 445（A 阶段实测已到 409） |
| 2 | `check_index.py --audit` | 两新领域 `enforcement` 填写率 100%；`catalog.json` 双向一致；无孤儿文件 |
| 3 | `check_refs.py --strict` | `OK`，扫描文件 101 → 约 132（A 阶段实测已到 113） |
| 4 | `unittest discover` | 133 全绿 |
| 5 | `find_duplicates.py --top 20` | 新领域与 csharp 无 ≥0.6 候选（A 阶段基线六对最高 0.917，B 后须全部降至 0.6 以下） |
| 6 | reference 抽样 | 3 篇随机抽查，代码/表格/图解指针均正常 |
| 7 | `git diff --check` | 无空白污染 |

---

## 已定决策（不再询问）

| 项 | 结论 | 依据 |
|---|---|---|
| SA 条款处理 | **C-甲**：逐字提取 + `algorithms/reference/LICENSE` + 每篇署名 + `00-README.md` 声明该目录授权独立 | 用户 2026-08-29 明确选定 |
| 执行顺序 | **A+B 先**，C+D 后 | 同上；A+B 含迁移改造，先做可让「建领域 → 消重复」一次闭环 |
| architecture 范围 | 不限于 DDD/六边形/整洁三种，**扩充至 .NET/C# 最常用的架构决策**（10 篇 rules + 2 篇 reference），选定依据见 spec「扩充范围的选定依据（实测）」 | 同上 |
