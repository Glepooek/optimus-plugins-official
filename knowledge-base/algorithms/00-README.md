# 算法与数据结构规范

> 面向团队的算法与数据结构选择判据。**语言无关**——不绑定任何编程语言；只回答「该选哪个结构、复杂度是否可接受、这个策略适不适用」，不回答「在 C# 里用哪个类型怎么写」。

本领域负责复杂度判断、数据结构选型、递归与迭代取舍、算法策略适用性；C# 集合类型与 LINQ 落地细节归 `knowledge-base/csharp/`，架构级别的切分决策归 `knowledge-base/architecture/`。

## 文档目的

本规范给出算法与数据结构决策的**判断依据**，目标是让「为什么用这个结构」有可检验的答案。它不是算法教程——教学材料在 `reference/` 下（《Hello 算法》全书 15 章），`rules/` 只承载可用于 review 的判断条款。

## 适用范围与读者

- **适用范围**：所有涉及数据结构选择、性能敏感路径、算法实现的代码；语言与技术栈无关
- **读者**：写性能敏感代码或做 review 的开发者。新人用 `reference/` 补基础，`rules/` 供决策时对齐判据

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义，与 `knowledge-base/csharp/00-README.md` 同一套定义：

| 级别 | 措辞 | 含义 | 违反处置 |
|---|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 | 视为缺陷，CI / review 拦截 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 | review 说明理由后可豁免 |
| **建议 MAY** | "可以"、"建议" | 可选做法，团队不强制 | 无 |

## ⚠️ reference/ 目录的许可证独立于本仓库

`reference/` 下的 `hello-algo-*.md` 共 15 篇提取自《Hello 算法》（作者 krahets），以 **CC BY-NC-SA 4.0** 授权，**该授权独立于本仓库其余部分**，全文见 `reference/LICENSE`。这带来三项硬约束：

| 约束 | 要求 |
|---|---|
| **BY（署名）** | 每篇文件头部的来源声明块**不得删除或简化**，含原作者、书名、版本、原书地址、许可证与提取日期 |
| **NC（非商业）** | 该目录内容不得用于商业用途；本仓库为内部规范库，满足此条 |
| **SA（相同方式共享）** | 基于该目录内容的演绎作品必须同样以 CC BY-NC-SA 4.0 授权。**许可证隔离在目录级别**——`rules/` 下为自撰内容，不受 SA 传染 |

因此：`rules/` 的条款**必须自行撰写**，可以引用 `reference/` 作为理由出处（`source` 字段），但不得整段复制其正文；反向也不得把本仓库的规范内容混入 `reference/`。

`reference/` 相对原书的改动：代码示例仅保留 C# 一种语言（原书含 12 种），图解未导出、原位置以指针指向原书。

## 与相邻领域的边界

算法选择与语言落地容易混淆，三方各自回答一个不同的问题：

| 领域 | 回答的问题 | 同一主题「查找」的例子 |
|---|---|---|
| **`algorithms`（本领域）** | **该用什么结构、复杂度是否可接受** | 「线性查找退化为 $O(n)$ 的热路径必须换为哈希或有序结构」 |
| `csharp` | 在 C# 里用哪个类型怎么写 | 「用 `Dictionary<K,V>` 而非 `List<T>.Find`」 |
| `architecture` | 该放哪一层、是否该拆 | 「查询职责归应用层，领域层不感知索引结构」 |

**判据一句话**：出现复杂度量级、结构的时空取舍 → 本领域；出现具体类型名与 API → `csharp`；出现层次与边界 → `architecture`。

本领域 `rules/` 正文**禁止**出现语言专有类型名（如 `Dictionary<K,V>`、`SortedSet<T>`）——需要指明落地手段时改为引用 `csharp` 领域的章节（带章节标题）。`reference/` 不受此限，其代码示例本就是 C#。

## 规范如何执行

算法约束大多需要人工判断实际数据规模与访问模式，落地手段与编码规范不同：

1. **性能 review**：热路径的结构选择须在 review 中说明判据与预期数据规模，判据取自本规范
2. **基准测试**：复杂度声明与实测不符时以实测为准——复杂度是渐近趋势，小规模下常数项可能主导
3. **理由出处**：条款的推导过程不在 `rules/` 展开，由 `reference/` 承载（索引 `source` 字段指向具体章节）

## 阅读路径

| 读者 | 必读 | 选读 |
|---|---|---|
| 新人（补基础） | `reference/hello-algo-02-complexity.md` | `reference/` 其余各章按需 |
| 写性能敏感代码前 | `rules/` 全部 | 对应结构的 `reference/` 章节 |
| review 时 | `rules/` 全部 | — |

## 文件地图

| 编号 | 文件 | 主题 |
|---|---|---|
| 00 | `00-README.md` | 总则、级别、许可证隔离、领域边界、索引 |
| — | `reference/LICENSE` | CC BY-NC-SA 4.0 许可证全文（约束 `reference/` 全部内容） |
| — | `reference/hello-algo-01-intro.md` | 《Hello 算法》第 1 章 · 初识算法 |
| — | `reference/hello-algo-02-complexity.md` | 《Hello 算法》第 2 章 · 复杂度分析 |
| — | `reference/hello-algo-03-data-structure.md` | 《Hello 算法》第 3 章 · 数据结构 |
| — | `reference/hello-algo-04-array-linkedlist.md` | 《Hello 算法》第 4 章 · 数组与链表 |
| — | `reference/hello-algo-05-stack-queue.md` | 《Hello 算法》第 5 章 · 栈与队列 |
| — | `reference/hello-algo-06-hash-table.md` | 《Hello 算法》第 6 章 · 哈希表 |
| — | `reference/hello-algo-07-tree.md` | 《Hello 算法》第 7 章 · 树 |
| — | `reference/hello-algo-08-heap.md` | 《Hello 算法》第 8 章 · 堆 |
| — | `reference/hello-algo-09-graph.md` | 《Hello 算法》第 9 章 · 图 |
| — | `reference/hello-algo-10-search.md` | 《Hello 算法》第 10 章 · 搜索 |
| — | `reference/hello-algo-11-sort.md` | 《Hello 算法》第 11 章 · 排序 |
| — | `reference/hello-algo-12-divide-conquer.md` | 《Hello 算法》第 12 章 · 分治 |
| — | `reference/hello-algo-13-backtracking.md` | 《Hello 算法》第 13 章 · 回溯 |
| — | `reference/hello-algo-14-dynamic-programming.md` | 《Hello 算法》第 14 章 · 动态规划 |
| — | `reference/hello-algo-15-greedy.md` | 《Hello 算法》第 15 章 · 贪心 |

`rules/` 尚未建立，规范条款随后续版本补入。

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。`reference/` 存放不带 MUST/SHOULD/MAY 语气的描述性知识，与 `rules/` 是并列关系——新增/修改任一类内容都需同步 `index.jsonl`，建议通过 `/knowledge-base-maintain` skill 完成。

`reference/LICENSE` 是非 Markdown 文件，不登记索引也不计入孤儿文件。

## 更新与豁免

- `reference/` 是外部作品的提取产物，**不接受本地编辑**——需要更新时重新从上游 tag 提取，并同步各篇头部的版本与提取日期
- `rules/` 的修订走 PR，review 通过后合入，并同步更新本文件的地图与阅读路径
- **豁免**：复杂度约束的豁免须给出实际数据规模。在 PR 中注明「豁免原因」与「已知的规模上限」，超出该上限时须重新评估

## 与仓库已有资产的关系

- `knowledge-base/csharp/`：本领域的 C# 落地侧（集合类型选择、LINQ 性能、缓存策略）
- `knowledge-base/architecture/`：架构级别的切分决策，不涉及单个数据结构的时空取舍
- `knowledge-base/design-patterns/`：设计模式的选用判据。模式与算法正交——模式解决「结构怎么组织」，算法解决「计算怎么做」

## 权威参考

- [Hello 算法（krahets）](https://www.hello-algo.com/) — `reference/` 的来源，CC BY-NC-SA 4.0
- [Introduction to Algorithms（CLRS）](https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/)
- [Big-O Cheat Sheet](https://www.bigocheatsheet.com/)
- [.NET 集合类型的复杂度](https://learn.microsoft.com/zh-cn/dotnet/standard/collections/)
