# 公式验证与重算指南

在交付前确保 xlsx 文件中每个公式都经过证明。没有可见错误的文件不算通过——只有清除了两层验证的文件才算通过。

---

## 基本规则

- **永远不要在未运行 `formula_check.py` 的情况下声明通过。** 目视检查电子表格不是验证。
- **第一层（静态）在每种场景下都是必须的。** 第二层（动态）在 LibreOffice 可用时也是必须的。若不可用，必须在报告中明确说明——不得静默跳过。
- **永远不要用 openpyxl 的 `data_only=True` 检查公式值。** 以 `data_only=True` 模式打开并保存工作簿会永久将所有公式替换为最后缓存的值，公式无法恢复。
- **只自动修复确定性错误。** 需要理解业务逻辑的任何修复都必须标记供人工审查。

---

## 两层验证架构

```
第一层 — 静态验证（XML 扫描，无需外部工具）
  │
  ├── 检测：已缓存在 <v> 元素中的全部 7 种 Excel 错误类型
  ├── 检测：指向不存在工作表的跨表引用
  ├── 检测：带 t="e" 属性的公式单元格（错误类型标记）
  └── 工具：formula_check.py + 手动 XML 检查
        │
        ▼（如有 LibreOffice）
第二层 — 动态验证（LibreOffice 无界面重算）
  │
  ├── 通过 LibreOffice Calc 引擎执行所有公式
  ├── 将真实计算结果填入 <v> 缓存值
  ├── 暴露重算前不可见的运行时错误
  └── 后续：对重算后的文件再次运行第一层验证
```

**为什么需要两层？**

openpyxl 和所有 Python xlsx 库只写入公式字符串（如 `=SUM(B2:B9)`），不执行公式。新生成的文件中每个公式单元格的 `<v>` 缓存都是空的。第一层只能捕获已编码在 XML 中的错误；第二层使用 LibreOffice 作为真正的计算引擎，执行每个公式，暴露运行时错误。两层缺一不可。

---

## 第一层 — 静态验证

### 运行 formula_check.py

```bash
python3 SKILL_DIR/scripts/formula_check.py /path/to/file.xlsx
python3 SKILL_DIR/scripts/formula_check.py /path/to/file.xlsx --json
python3 SKILL_DIR/scripts/formula_check.py /path/to/file.xlsx --sheet Summary
python3 SKILL_DIR/scripts/formula_check.py /path/to/file.xlsx --summary
```

退出代码：
- `0` — 无严重错误（通过，或通过但有启发式警告）
- `1` — 检测到严重错误，或文件无法打开（失败）

#### 脚本检查的内容

脚本将 xlsx 作为 ZIP 压缩包打开，执行以下五项检查：

1. **错误值检测**：若单元格有 `t="e"`，其 `<v>` 元素含有 Excel 错误字符串。
2. **损坏跨表引用检测**：若单元格有 `<f>` 元素，提取公式中所有工作表名称并与 `workbook.xml` 的工作表列表对比。
3. **未知命名范围检测（启发式）**：公式中不是函数名、不是单元格引用、且不在 `<definedNames>` 中的标识符会被标记为 `unknown_name_ref` 警告。这是启发式检测——可能有误报，需手动验证。
4. **共享公式完整性**：只检查带 `ref="..."` 属性的主单元格；仅含 `<f t="shared" si="N"/>` 的消费者单元格跳过检查。
5. **格式错误的错误单元格**：有 `t="e"` 但无 `<v>` 子元素的单元格标记为结构性 XML 问题。

严重错误（退出代码 1）：`error_value`、`broken_sheet_ref`、`malformed_error_cell`、`file_error`
软警告（退出代码 0）：`unknown_name_ref` — 必须手动验证，但单独存在时不阻止交付

#### 输出示例

无错误文件：
```
File   : /tmp/budget_2024.xlsx
Sheets : Summary, Q1, Q2, Q3, Q4, Assumptions
Formulas checked      : 312 distinct formula cells
Errors found          : 0

PASS — No formula errors detected
```

有错误文件：
```
── Error Details ──
  [FAIL] [Summary!C12] contains #REF! (formula: Q1!A0/Q1!A1)
  [FAIL] [Summary!D15] references missing sheet 'Q5'
  [FAIL] [Q1!F8] contains #DIV/0!
  [WARN] [Q2!B10] uses unknown name 'GrowthAssumptions' (heuristic — verify manually)

FAIL — 3 error(s) must be fixed before delivery
```

---

## 第二层 — 动态验证（LibreOffice 无界面）

### 检查 LibreOffice 可用性

```bash
which soffice
libreoffice --version
```

如果命令无输出，LibreOffice 未安装。在报告中记录"第二层：已跳过——LibreOffice 不可用"，仅凭第一层结果继续交付。

### 运行无界面重算

```bash
# 检查可用性
python3 SKILL_DIR/scripts/libreoffice_recalc.py --check

# 运行重算（默认超时 60 秒）
python3 SKILL_DIR/scripts/libreoffice_recalc.py /path/to/input.xlsx /tmp/recalculated.xlsx

# 大型或复杂文件，延长超时
python3 SKILL_DIR/scripts/libreoffice_recalc.py /path/to/input.xlsx /tmp/recalculated.xlsx --timeout 120
```

退出代码：
- `0` — 重算成功，已写入输出文件
- `2` — LibreOffice 未找到（在报告中记为已跳过）
- `1` — LibreOffice 找到但失败（超时、崩溃、文件格式错误）

### 重算后再次运行第一层

```bash
python3 SKILL_DIR/scripts/formula_check.py /tmp/recalculated.xlsx
```

这次第一层检查是确定性的运行时错误检查。发现的任何错误都是必须修复的真实计算失败。

---

## 全部 7 种错误类型 — 原因与修复策略

### #REF! — 无效单元格引用

**含义**：公式引用了不再存在或从未存在的单元格、范围或工作表。

**常见原因**：行/列计算中的差一错误（如引用不存在的第 0 行）、列字母计算错误、公式引用了从未创建或已重命名的工作表。

**修复**：
```xml
<!-- 错误 -->
<c r="D5" t="e"><f>Sheet2!A0</f><v>#REF!</v></c>

<!-- 修复：删除 t="e"，更正引用，清空 <v> -->
<c r="D5"><f>Sheet2!A1</f><v></v></c>
```

**可自动修复？** 只有当正确目标可从上下文明确确定时。否则标记供人工审查。

---

### #DIV/0! — 除以零

**含义**：公式除以一个为零或空单元格的值（空单元格在算术中求值为 0）。

**修复**：
```xml
<!-- 错误 -->
<c r="C8" t="e"><f>B8/B7</f><v>#DIV/0!</v></c>

<!-- 修复：用 IFERROR 包裹 -->
<c r="C8"><f>IFERROR(B8/B7,0)</f><v></v></c>
```

**可自动修复？** 是。用 `IFERROR(...,0)` 包裹对大多数财务公式是安全的。

---

### #VALUE! — 数据类型错误

**含义**：公式对错误类型的值进行了算术或逻辑运算（如对文字字符串做加法）。

**修复**：将源单元格类型从文字改为数字，或用 `VALUE()` 转换：
```xml
<!-- 错误：数字值存储为字符串 -->
<c r="D3" t="inlineStr"><is><t>1000</t></is></c>

<!-- 修复：数字值存储为数字（省略 t 属性） -->
<c r="D3"><v>1000</v></c>
```

**可自动修复？** 部分可以。若源单元格类型明显错误（数字存为字符串），修复类型。若原因不明，标记供人工审查。

---

### #NAME? — 未知名称

**含义**：公式含有 Excel 不识别的标识符——函数名拼写错误、未定义的命名范围，或目标 Excel 版本不支持的函数。

**修复**：检查 `xl/workbook.xml` 中的命名范围，修正拼写错误：
```xml
<!-- 修复 -->
<c r="B2"><f>SUM(RevenueRange)</f><v></v></c>
```

**可自动修复？** 只有当正确名称明确无误时（如存在唯一的相近匹配）。否则标记供人工审查。

---

### #N/A — 值不可用

**含义**：查找函数（VLOOKUP、MATCH、INDEX/MATCH、XLOOKUP）未找到要搜索的值。

**修复**：用 IFERROR 包裹以容忍缺失匹配：
```xml
<c r="G5"><f>IFERROR(VLOOKUP(F5,Assumptions!$A$2:$B$20,2,0),0)</f><v></v></c>
```

**可自动修复？** 添加 IFERROR 是安全的（若零值默认可接受）。若查找失败表明数据完整性问题，不要自动修复——标记供人工审查。

---

### #NULL! — 空交集

**含义**：空格运算符（计算两个范围的交集）应用于不相交的两个范围。

**修复**：将空格替换为逗号（联合）或冒号（范围）：
```xml
<c r="H10"><f>SUM(A1:A5,C1:C5)</f><v></v></c>
```

**可自动修复？** 是。生成的公式中空格运算符几乎从不是故意的。

---

### #NUM! — 数值错误

**含义**：公式产生了 Excel 无法表示的数字，或数学上无实数解的运算（负数开方、零的对数）。

**修复**：添加条件防护：
```xml
<c r="J15"><f>IFERROR(IRR(B5:B15),"")</f><v></v></c>
```

**可自动修复？** 部分可以。用 IFERROR 抑制显示，但同时标记单元格供人工审查。

---

## 自动修复 vs 人工审查决策矩阵

| 错误类型 | 可自动修复？ | 条件 | 操作 |
|------------|---------------|-----------|--------|
| `#DIV/0!` | 是 | 始终 | 用 `IFERROR(formula,0)` 包裹 |
| `#NULL!` | 是 | 始终 | 将空格运算符替换为逗号 |
| `#REF!` | 是 | 仅当正确目标从上下文明确时 | 修正引用；否则标记 |
| `#NAME?` | 是 | 仅当拼写错误有唯一合理修正时 | 修正名称；否则标记 |
| `#N/A` | 有条件 | 若零值/空值默认在业务上可接受 | 添加 IFERROR 包裹，记录假设 |
| `#VALUE!` | 有条件 | 仅当源单元格类型明显错误时 | 修复类型；否则标记 |
| `#NUM!` | 否 | 始终 | 添加 IFERROR 抑制显示，然后标记 |
| 损坏的工作表引用 | 是 | 仅当能从 workbook.xml 识别重命名工作表时 | 修正名称 |
| 业务逻辑错误 | 永不 | 任何情况 | 仅供人工审查 |

---

## 交付标准 — 验证报告

每个验证任务都必须产生一份结构化报告。无论是否发现错误，报告都是可交付成果。

### 必需报告格式

```markdown
## 公式验证报告

**文件**：/path/to/filename.xlsx
**日期**：YYYY-MM-DD
**已检查工作表**：Sheet1、Sheet2、Sheet3
**已扫描公式总数**：N

---

### 第一层 — 静态验证

**状态**：通过 / 失败
**工具**：formula_check.py（直接 XML 扫描）

| 工作表 | 单元格 | 错误类型 | 详情 | 已应用修复 |
|-------|------|-----------|--------|-------------|
| Summary | C12 | #REF! | 公式：Q1!A0 | 已更正为 Q1!A1 |

_（如无错误："未检测到错误。"）_

---

### 第二层 — 动态验证

**状态**：通过 / 失败 / 已跳过
**工具**：LibreOffice 无界面（版本 X.Y.Z）/ 不可用

_（如已跳过：说明原因——LibreOffice 未安装、超时等）_

---

### 摘要

- **发现错误总数**：N
- **已自动修复**：N（列出类型）
- **标记供人工审查**：N（列出单元格和原因）
- **最终状态**：通过（可交付）/ 失败（待处理）
```

---

## 关键陷阱

**陷阱 1：openpyxl `data_only=True` 会销毁公式。**
以 `data_only=True` 模式打开工作簿会读取缓存值而不是公式。若随后保存，所有 `<f>` 元素被永久删除。永远不要在验证工作流中使用此模式。

**陷阱 2：空 `<v>` 不等于公式通过。**
新生成的文件中所有公式单元格的 `<v>` 都是空的。formula_check.py 不会将这些报告为错误——重算前它们还不是错误。这正是第二层验证必须执行的原因。

**陷阱 3：共享公式错误影响整个范围。**
若共享公式的主单元格有损坏的引用，`ref="D2:D100"` 范围内的每个单元格都继承该损坏引用。修复时修改主单元格的 `<f t="shared" ref="...">` 元素即可；消费者单元格（`<f t="shared" si="N"/>`）自动继承修正后的公式。

**陷阱 4：工作表名称区分大小写。**
`=q1!B5` 和 `=Q1!B5` 是不同的引用。formula_check.py 的字符串比较区分大小写。若公式使用小写工作表名而工作簿中是大写，会被标记为损坏引用。修复方法是与 `workbook.xml` 中的精确大小写一致。

**陷阱 5：`--convert-to xlsx` 不保证公式完整保留。**
LibreOffice 的转换偶尔会修改某些公式类型（数组公式、动态数组函数如 `SORT`、`UNIQUE`）。第二层验证后，若重算文件显示与错误修复无关的公式变化，不要直接交付重算文件——使用原始文件进行针对性 XML 修复。
