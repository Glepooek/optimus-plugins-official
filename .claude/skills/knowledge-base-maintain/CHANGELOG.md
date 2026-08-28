# Changelog

## [1.4.0] - 2026-08-28

### Added
- 新增 `scripts/find_duplicates.py`：报告语义重复的条目候选。`check_duplicate_ids` 只查 `id` 字符串重复，挡不住同一条约束被两个领域各自写一遍——这类重复本仓库踩过两次（v1.5.0 按单个文件迁移协作条款漏掉散落项、3.0.0 发现 git ↔ csharp 语义环），两次都靠人工通读才发现
- 新增"查重"场景（Step 1 场景表第 4 项），可独立运行不改内容；Step 2 末尾新增写入前查重与三种情形（真重复/合理分层/语义环）的处置表
- 新增 `scripts/test_find_duplicates.py`，24 个单测；其中 `TestKnownDuplicateRegression` 用 3.0.0 那次人工发现的真实条目原文做回归基准——若评分改动让它们掉出候选，等于回退到人工通读时代

### Changed
- 首次实现用标准 Jaccard 相似度，在已知答案上实测真重复仅得 0.058、低于同批纯巧合词项对。改为**重叠占较短一方的比例**（规范 summary 长度差异大，Jaccard 分母会把真重复稀释），并对 4 字以上共有片段加权。改后已知的 3 对重复排名 3/4/7（共 1488 对候选）
- 候选筛选**不按 tags 交集**：3.0.0 那对真重复的 tags 交集为空（领域名本身占一个 tag 位，跨领域条目 tags 天然不相交），按 tags 筛会一个都检不出。tags 只作加分项
- 输出的"共有词项"把滑动窗口 n-gram 拼回完整短语（7 个 4-gram → 1 条「视为已泄露须立即轮换」），否则人看到的是同一短语的碎片

## [1.3.0] - 2026-08-28

### Added
- 新增 `scripts/check_refs.py`：校验消费者 skill 中对规范文件的 `§ 章节号` 引用。补上了此前无人看守的缺口——`check_index.py` 校验的是索引 `anchor` 的标题**文本**，管不到 skill 正文里写的 `§ 7` 这类**位置引用**；章节重编号后 `§ 7` 依然「存在」，只是指向了别的内容，不会有任何报错
- `check_refs.py` 三类检查：存在性（章节号有对应标题）、一致性（引用同时写了标题时须与该章节号的标题匹配——这是唯一能挡住重编号的一环）、脆弱性报告（只写号不写标题的引用无法交叉校验，列出并建议补标题，默认只告警，`--strict` 可视为失败）
- 新增 `scripts/test_check_refs.py`，21 个单测覆盖多文件同行归属、裸文件名的同目录省略写法、`§1-§5` 范围形态、跨领域歧义时不猜、以及"重编号后标题不符必须报错"的核心负向场景
- Step 5 新增章节号引用校验命令与四类问题的成因表；Step 4 新增第 5 点，明确重排/重命名章节时须同步消费者引用

### Changed
- `compatibility` 字段同步为 `scripts/` 下两个校验脚本

## [1.2.0] - 2026-08-27

### Added
- `check_index.py` 新增 `source` 内部引用校验：`<file>#<标题文本>` 形式的文件与锚点必须真实存在，外部 URL 不做离线校验——不校验等于新增一批无人看守的引用，与规范文件迁移后失效的正文交叉引用是同一类腐烂
- `check_index.py` 新增组合约束：`level: MAY` 不得配 `enforcement: ci`（可选做法不作为 CI 拦截依据）；`kind: reference` 不得有 `enforcement`
- `--audit` 报告新增治理元数据维度：全库 `enforcement` 填写率、各领域 `enforcement` 分布
- Step 3 补充 `enforcement` 与 `source` 的填写判断依据，并明确禁止把 `reference/` 的理由复制进规范正文
- Step 5 常见问题表新增 `source` 引用失效与 `MAY`+`ci` 两类；`test_check_index.py` 从 55 个测试扩展到 66 个

### Changed
- Step 4 迁移/重命名时需同步的引用由四处增加为五处，新增"索引 `source` 字段中的内部引用"

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
