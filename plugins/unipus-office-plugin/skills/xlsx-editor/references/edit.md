# 微创式编辑已有 xlsx 文件

对已有 xlsx 文件进行精准、手术级别的修改，同时完整保留所有未触碰的内容：样式、宏、数据透视表、图表、迷你图、命名范围、数据验证、条件格式及其他所有嵌入内容。

---

## 1. 适用场景

凡是**修改已有 xlsx 文件**的任务，均使用编辑（解包 → XML 编辑 → 重打包）路径：

- 模板填写——向指定输入单元格填入值或公式
- 数据更新——替换实时文件中的过时数字、文字或日期
- 内容纠错——修复错误值、损坏公式或错误标签
- 向已有表格添加新数据行
- 重命名工作表
- 对特定单元格应用新样式

**不适用**：从零创建新工作簿。请参阅 `create.md`。

---

## 2. 为什么禁止 openpyxl 往返读写已有文件

对任何包含高级功能的文件，openpyxl 的 `load_workbook()` 后跟 `workbook.save()` 是**破坏性操作**。该库会静默丢弃它不理解的内容：

| 功能 | openpyxl 行为 | 后果 |
|---------|-------------------|-------------|
| VBA 宏（`vbaProject.bin`） | 完全丢弃 | 所有自动化丢失；文件以 `.xlsx` 而非 `.xlsm` 保存 |
| 数据透视表（`xl/pivotTables/`） | 丢弃 | 交互分析被破坏 |
| 切片器 | 丢弃 | 筛选 UI 丢失 |
| 迷你图（`<sparklineGroups>`） | 丢弃 | 单元格内迷你图消失 |
| 图表格式细节 | 部分丢失 | 系列颜色、自定义坐标轴可能恢复默认 |
| 打印区域/分页符 | 有时丢失 | 打印布局改变 |
| 自定义 XML 部件 | 丢弃 | 第三方数据绑定损坏 |
| 主题链接颜色 | 可能去主题化 | 颜色转为绝对值，破坏主题切换 |

即使是没有这些功能的"普通"文件，openpyxl 也可能规范化 Excel 依赖的 XML 空白字符、修改命名空间声明或重置 `calcMode` 标志。

**规则绝对：永远不要用 openpyxl 打开已有文件并重新保存。**

XML 直接编辑方式是安全的，因为它操作的是原始字节。你只修改你碰到的节点，其余内容与原文件逐字节相同。

---

## 3. 标准操作流程

### 第一步 — 解包

```bash
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/
```

脚本解压 xlsx，对每个 XML 和 `.rels` 文件进行格式美化，并打印关键文件的分类清单，如检测到高风险内容（VBA、数据透视表、图表）则发出警告。

操作前仔细阅读打印输出。如脚本报告 `xl/vbaProject.bin` 或 `xl/pivotTables/`，请遵循第 7 节的约束。

### 第二步 — 侦查

操作前先了解结构。

**识别工作表名称及其 XML 文件：**

```
xl/workbook.xml  →  <sheet name="Revenue" sheetId="1" r:id="rId1"/>
xl/_rels/workbook.xml.rels  →  <Relationship Id="rId1" Target="worksheets/sheet1.xml"/>
```

名为"Revenue"的工作表在 `xl/worksheets/sheet1.xml` 中。编辑工作表前必须解析此映射关系。

**了解共享字符串表：**

```bash
# 统计 xl/sharedStrings.xml 中已有条目数
grep -c "<si>" /tmp/xlsx_work/xl/sharedStrings.xml
```

每个文字单元格使用此表中从零开始的索引。追加前要知道当前计数。

**了解样式表：**

```bash
# 统计已有 cellXfs 条目数
grep -c "<xf " /tmp/xlsx_work/xl/styles.xml
```

新样式槽追加在已有条目之后。第一个新槽的索引 = 当前计数。

**扫描目标工作表中的高风险 XML 区域：**

编辑目标 `sheet*.xml` 前，查找以下元素：

- `<mergeCell>` — 合并单元格范围；行/列插入会移动这些范围
- `<conditionalFormatting>` — 条件范围；行/列插入会移动这些范围
- `<dataValidations>` — 验证范围；行/列插入会移动这些范围
- `<tableParts>` — 表格定义；在表格内插入行需要更新 `<tableColumn>`
- `<sparklineGroups>` — 迷你图；不修改，保持原样

### 第三步 — 将意图映射为最小化 XML 修改

在写任何字符前，列出精确的 XML 节点变更清单，防止范围蔓延。

| 用户意图 | 需要修改的文件 | 需要修改的节点 |
|-------------|----------------|-----------------|
| 修改单元格的数字值 | `xl/worksheets/sheetN.xml` | 目标 `<c>` 内的 `<v>` |
| 修改单元格的文字 | `xl/sharedStrings.xml`（追加）+ `xl/worksheets/sheetN.xml` | 新 `<si>`，更新单元格 `<v>` 索引 |
| 修改单元格的公式 | `xl/worksheets/sheetN.xml` | 目标 `<c>` 内的 `<f>` 文本 |
| 在末尾添加新数据行 | `xl/worksheets/sheetN.xml` + 可能需要 `xl/sharedStrings.xml` | 追加 `<row>` 元素 |
| 对单元格应用新样式 | `xl/styles.xml` + `xl/worksheets/sheetN.xml` | 在 `<cellXfs>` 中追加 `<xf>`，更新 `<c>` 的 `s` 属性 |
| 重命名工作表 | `xl/workbook.xml` | `<sheet>` 元素的 `name` 属性 |
| 重命名工作表（含跨表公式） | `xl/workbook.xml` + 所有 `xl/worksheets/*.xml` | `name` 属性 + 引用旧名称的 `<f>` 文本 |

### 第四步 — 执行修改

使用 Edit 工具。只修改最小必要范围，不要重写整个文件。

各操作类型的精确 XML 模式见第 4 节。

### 第五步 — 级联检查

任何导致行或列位置移动的修改后，审计所有受影响的 XML 区域。见第 5 节。

### 第六步 — 打包与验证

```bash
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
python3 SKILL_DIR/scripts/formula_check.py output.xlsx
```

打包脚本在创建 ZIP 前验证 XML 格式正确性。如有解析错误则修复后再打包。打包后运行 `formula_check.py` 确认未引入公式错误。

---

## 4. 常见编辑操作的精确 XML 模式

### 4.1 修改数字单元格的值

在工作表 XML 中找到 `<c r="B5">` 元素，替换 `<v>` 中的文本。

**修改前：**
```xml
<c r="B5">
  <v>1000</v>
</c>
```

**修改后（新值 1500）：**
```xml
<c r="B5">
  <v>1500</v>
</c>
```

规则：
- 除非明确需要修改样式，不要添加或删除 `s` 属性
- 不要添加 `t` 属性——数字省略 `t` 或使用 `t="n"`
- 不要修改 `r` 属性（单元格地址）

---

### 4.2 修改文字单元格的值

文字单元格通过索引引用共享字符串表（`t="s"`）。不能在不影响所有使用相同索引的单元格的情况下就地编辑字符串。安全的做法是追加新条目。

**修改前 — 共享字符串文件（`xl/sharedStrings.xml`）：**
```xml
<sst count="4" uniqueCount="4">
  <si><t>Revenue</t></si>
  <si><t>Cost</t></si>
  <si><t>Margin</t></si>
  <si><t>Old Label</t></si>
</sst>
```

**修改后 — 追加新字符串，递增计数：**
```xml
<sst count="5" uniqueCount="5">
  <si><t>Revenue</t></si>
  <si><t>Cost</t></si>
  <si><t>Margin</t></si>
  <si><t>Old Label</t></si>
  <si><t>New Label</t></si>
</sst>
```

新字符串在索引 4（从零开始）。

**修改前 — 工作表 XML 中的单元格：**
```xml
<c r="A7" t="s">
  <v>3</v>
</c>
```

**修改后 — 指向新索引：**
```xml
<c r="A7" t="s">
  <v>4</v>
</c>
```

规则：
- 永远不要修改或删除已有的 `<si>` 条目。只允许追加。
- `count` 和 `uniqueCount` 必须同时递增。
- 如果新字符串包含 `&`、`<`、`>`，需转义：`&amp;`、`&lt;`、`&gt;`。
- 字符串有首尾空格时，在 `<t>` 上添加 `xml:space="preserve"`：
  ```xml
  <si><t xml:space="preserve">  缩进文字  </t></si>
  ```

---

### 4.3 修改公式

公式存储在 `<f>` 元素中，**不带前导 `=`**（与 Excel 界面中的输入不同）。

**修改前：**
```xml
<c r="C10">
  <f>SUM(C2:C9)</f>
  <v>4800</v>
</c>
```

**修改后（扩展范围）：**
```xml
<c r="C10">
  <f>SUM(C2:C11)</f>
  <v></v>
</c>
```

规则：
- 修改公式时将 `<v>` 清空。缓存值已过期。
- 不要给公式单元格添加 `t="s"` 或任何类型属性。`t` 属性不存在或使用结果类型值，而非公式标记。
- 跨表引用使用 `SheetName!CellRef`。工作表名称含空格时用单引号：`'Q1 Data'!B5`。
- `<f>` 文本不得包含前导 `=`。

**修改前（将硬编码值转为实时公式）：**
```xml
<c r="D15">
  <v>95000</v>
</c>
```

**修改后：**
```xml
<c r="D15">
  <f>SUM(D2:D14)</f>
  <v></v>
</c>
```

---

### 4.4 添加新数据行

追加到 `<sheetData>` 内最后一个 `<row>` 元素之后。OOXML 中行号从 1 开始且必须是连续的。

**修改前（最后一行是第 10 行）：**
```xml
  <row r="10">
    <c r="A10" t="s"><v>3</v></c>
    <c r="B10"><v>2023</v></c>
    <c r="C10"><v>88000</v></c>
    <c r="D10"><f>C10*1.1</f><v></v></c>
  </row>
</sheetData>
```

**修改后（追加新第 11 行）：**
```xml
  <row r="10">
    <c r="A10" t="s"><v>3</v></c>
    <c r="B10"><v>2023</v></c>
    <c r="C10"><v>88000</v></c>
    <c r="D10"><f>C10*1.1</f><v></v></c>
  </row>
  <row r="11">
    <c r="A11" t="s"><v>4</v></c>
    <c r="B11"><v>2024</v></c>
    <c r="C11"><v>96000</v></c>
    <c r="D11"><f>C11*1.1</f><v></v></c>
  </row>
</sheetData>
```

规则：
- 行内每个 `<c>` 必须将 `r` 设置为正确的单元格地址（如 `A11`）。
- 文字单元格需要 `t="s"` 和共享字符串索引在 `<v>` 中。数字单元格省略 `t`。
- 公式单元格使用 `<f>` 和空 `<v>`。
- 如果希望样式与上一行一致，从上一行复制 `s` 属性。不要使用 `styles.xml` 中不存在的样式索引。
- 如果工作表含有 `<dimension>` 元素（如 `<dimension ref="A1:D10"/>`），更新它以包含新行：`<dimension ref="A1:D11"/>`。
- 如果工作表含有引用表格的 `<tableparts>`，在对应的 `xl/tables/tableN.xml` 文件中更新表格的 `ref` 属性。

---

### 4.5 添加新列

向每个已有 `<row>` 追加新 `<c>` 元素，如果有 `<cols>` 部分，也需要更新。

**修改前（各行只有 A-C 列）：**
```xml
<cols>
  <col min="1" max="3" width="14" customWidth="1"/>
</cols>
<sheetData>
  <row r="1">
    <c r="A1" t="s"><v>0</v></c>
    <c r="B1" t="s"><v>1</v></c>
    <c r="C1" t="s"><v>2</v></c>
  </row>
  <row r="2">
    <c r="A2"><v>100</v></c>
    <c r="B2"><v>200</v></c>
    <c r="C2"><v>300</v></c>
  </row>
</sheetData>
```

**修改后（添加 D 列）：**
```xml
<cols>
  <col min="1" max="3" width="14" customWidth="1"/>
  <col min="4" max="4" width="14" customWidth="1"/>
</cols>
<sheetData>
  <row r="1">
    <c r="A1" t="s"><v>0</v></c>
    <c r="B1" t="s"><v>1</v></c>
    <c r="C1" t="s"><v>2</v></c>
    <c r="D1" t="s"><v>5</v></c>
  </row>
  <row r="2">
    <c r="A2"><v>100</v></c>
    <c r="B2"><v>200</v></c>
    <c r="C2"><v>300</v></c>
    <c r="D2"><f>A2+B2+C2</f><v></v></c>
  </row>
</sheetData>
```

规则：
- 在末尾（最后一列之后）添加列是安全的——不会移动任何已有公式引用。
- 在中间插入列会使右侧所有列移位，需要与行插入相同的级联更新（见第 5 节）。
- 如果有 `<dimension>` 元素，记得更新。

---

### 4.6 修改或添加样式

样式使用多级间接引用链。完整链接见 `ooxml-cheatsheet.md`。关键规则：**只追加新条目，永远不修改已有条目**。

**场景：** 添加蓝色字体样式（用于硬编码输入单元格），该样式尚不存在。

**第一步 — 检查 `xl/styles.xml` 中是否已有匹配的字体：**
```xml
<!-- 在 <fonts> 中查找已有的蓝色字体 -->
<font>
  <color rgb="000000FF"/>
  <!-- 其他属性 -->
</font>
```

如找到，记录其索引（在 `<fonts>` 列表中的从零开始的位置）。如未找到，则追加。

**第二步 — 如需追加新字体：**

修改前：
```xml
<fonts count="3">
  <font>...</font>   <!-- 索引 0 -->
  <font>...</font>   <!-- 索引 1 -->
  <font>...</font>   <!-- 索引 2 -->
</fonts>
```

修改后：
```xml
<fonts count="4">
  <font>...</font>   <!-- 索引 0 -->
  <font>...</font>   <!-- 索引 1 -->
  <font>...</font>   <!-- 索引 2 -->
  <font>
    <b/>
    <sz val="11"/>
    <color rgb="000000FF"/>
    <name val="Calibri"/>
  </font>             <!-- 索引 3（新增） -->
</fonts>
```

**第三步 — 在 `<cellXfs>` 末尾追加新 `<xf>`：**

修改前：
```xml
<cellXfs count="5">
  <xf .../>   <!-- 索引 0 -->
  <xf .../>   <!-- 索引 1 -->
  <xf .../>   <!-- 索引 2 -->
  <xf .../>   <!-- 索引 3 -->
  <xf .../>   <!-- 索引 4 -->
</cellXfs>
```

修改后：
```xml
<cellXfs count="6">
  <xf .../>   <!-- 索引 0 -->
  <xf .../>   <!-- 索引 1 -->
  <xf .../>   <!-- 索引 2 -->
  <xf .../>   <!-- 索引 3 -->
  <xf .../>   <!-- 索引 4 -->
  <xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0"
      applyFont="1"/>   <!-- 索引 5（新增） -->
</cellXfs>
```

**第四步 — 应用到目标单元格：**

修改前：
```xml
<c r="B3">
  <v>0.08</v>
</c>
```

修改后：
```xml
<c r="B3" s="5">
  <v>0.08</v>
</c>
```

规则：
- 永远不要删除或重排 `<fonts>`、`<fills>`、`<borders>`、`<cellXfs>` 中的已有条目。
- 追加时始终更新 `count` 属性。
- 新的 `cellXfs` 索引 = 追加前的旧 `count` 值（从零起始：如果 count 原来是 5，新索引是 5）。
- 自定义 `numFmt` ID 必须为 164 或以上。ID 0–163 是内置格式，不得重新声明。
- 如果所需样式在文件其他地方已存在（用于类似单元格），复用其 `s` 索引而不是创建重复样式。

---

### 4.7 重命名工作表

**只需修改 `xl/workbook.xml`**——除非跨表公式引用了旧名称。

**修改前（`xl/workbook.xml`）：**
```xml
<sheet name="Sheet1" sheetId="1" r:id="rId1"/>
```

**修改后：**
```xml
<sheet name="Revenue" sheetId="1" r:id="rId1"/>
```

**如果任何工作表中的公式引用了旧名称，也需要更新：**

修改前（`xl/worksheets/sheet2.xml`）：
```xml
<c r="B5"><f>Sheet1!C10</f><v></v></c>
```

修改后：
```xml
<c r="B5"><f>Revenue!C10</f><v></v></c>
```

如果新名称包含空格：
```xml
<c r="B5"><f>'Q1 Revenue'!C10</f><v></v></c>
```

扫描所有工作表 XML 文件中的旧名称：
```bash
grep -r "Sheet1!" /tmp/xlsx_work/xl/worksheets/
```

规则：
- `.rels` 文件和 `[Content_Types].xml` **不需要**修改——它们引用 XML 文件路径，而非工作表名称。
- `sheetId` 不能修改；它是稳定的内部标识符。
- 工作表名称在公式引用中区分大小写。

---

## 5. 高风险操作 — 级联影响

### 5.1 在中间插入行

在第 N 位置插入行会使第 N 行及以下的所有行下移。每个 XML 文件中对这些行的所有引用都必须更新。

**需要检查和更新的文件：**

| XML 区域 | 需要更新的内容 | 示例移位 |
|------------|---------------|---------------|
| 工作表 `<row r="...">` 属性 | 将 >= N 的所有行的行号递增 | `r="7"` → `r="8"` |
| 这些行内所有 `<c r="...">` | 递增单元格地址中的行号 | `r="A7"` → `r="A8"` |
| 任何工作表中所有 `<f>` 公式文本 | 移位绝对行引用 >= N | `B7` → `B8` |
| `<mergeCell ref="...">` | 移位起止行 | `A7:C7` → `A8:C8` |
| `<conditionalFormatting sqref="...">` | 移位范围 | `A5:D20` → `A5:D21` |
| `<dataValidations sqref="...">` | 移位范围 | `B6:B50` → `B7:B51` |
| `xl/charts/chartN.xml` 数据源范围 | 移位系列范围 | `Sheet1!$B$5:$B$20` → `Sheet1!$B$6:$B$21` |
| `xl/pivotTables/*.xml` 源范围 | 移位源数据范围 | 极度谨慎——见第 7 节 |
| `<dimension ref="...">` | 扩展至包含新范围 | `A1:D20` → `A1:D21` |
| `xl/tables/tableN.xml` `ref` 属性 | 扩展表格边界 | `A1:D20` → `A1:D21` |

**不要在大型或公式复杂的文件中手动尝试行插入。** 改用专用移位脚本：

```bash
# 在第 5 行插入 1 行：第 5 行及以下的所有行向下移动 1 行
python3 SKILL_DIR/scripts/xlsx_shift_rows.py /tmp/xlsx_work/ insert 5 1

# 删除第 8 行：第 9 行及以上的所有行向上移动 1 行
python3 SKILL_DIR/scripts/xlsx_shift_rows.py /tmp/xlsx_work/ delete 8 1
```

脚本一次性更新：`<row r="...">` 属性、`<c r="...">` 单元格地址、所有工作表中所有 `<f>` 公式文本、`<mergeCell>` 范围、`<conditionalFormatting sqref="...">`, `<dataValidation sqref="...">`, `<dimension ref="...">`, `xl/tables/` 中表格 `ref` 属性, `xl/charts/` 中图表系列范围, `xl/pivotCaches/` 中数据透视缓存源范围。

**运行移位脚本后，始终重新打包并验证：**
```bash
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
python3 SKILL_DIR/scripts/formula_check.py output.xlsx
```

**脚本不会更新（需手动审查）：**
- `xl/workbook.xml` `<definedNames>` 中的命名范围——检查并在它们引用被移位行时更新。
- 公式中的结构化表格引用（`Table[@Column]`）。
- `xl/externalLinks/` 中的外部工作簿链接。

### 5.2 在中间插入列

与行插入逻辑相同，但针对列。公式中的列引用（`B`、`$C` 等）以及合并单元格范围、条件格式范围和图表数据源都需要更新。

列字母移位比行移位更难以自动化处理。尽可能**在末尾追加列**。

### 5.3 删除行或列

删除比插入更危险，因为任何引用已删除行或列的公式都会变为 `#REF!`。删除前：

1. 搜索所有 `<f>` 元素中对被删除范围的引用。
2. 如有公式引用了被删除行/列中的单元格，不要删除——改为清空该行的数据或咨询用户。
3. 删除后，将所有对删除点之后的行/列的引用向下/向左移位。

---

## 6. 模板填写 — 识别和填充输入单元格

模板将某些单元格指定为输入区域。识别它们的常见模式：

### 6.1 模板如何标记输入区域

| 标记方式 | XML 表现 | 查找方式 |
|--------|-------------------|-----------------|
| 蓝色字体 | `s` 属性指向 `cellXfs` 中 `fontId` → `<color rgb="000000FF"/>` 的条目 | 检查 `styles.xml` 解码 `s` 值 |
| 黄色填充（高亮） | `s` → `fillId` → `<fill><patternFill><fgColor rgb="00FFFF00"/>` | |
| 空 `<v>` 元素 | `<c r="B5"><v></v></c>` 或行中完全不存在该单元格 | 单元格尚无值 |
| 单元格附近的批注 | `xl/comments1.xml` 中带 `ref="B5"` | 批注通常为输入字段加标注 |
| 命名范围 | `xl/workbook.xml` `<definedName>` 元素 | 模板可能定义了 `InputRevenue` 等名称 |

### 6.2 填写模板单元格

不要修改 `s` 属性，不要修改 `t` 属性（除非必须从空改为带类型），只修改 `<v>` 或添加 `<f>`。

**修改前（保留样式的空输入单元格）：**
```xml
<c r="C5" s="3">
  <v></v>
</c>
```

**修改后（填入数字，样式不变）：**
```xml
<c r="C5" s="3">
  <v>125000</v>
</c>
```

**修改后（填入文字——需要先添加共享字符串条目）：**
```xml
<!-- 1. 向 sharedStrings.xml 追加：<si><t>北区</t></si>，索引为 7 -->
<c r="C5" t="s" s="3">
  <v>7</v>
</c>
```

**修改后（填入公式，保留样式）：**
```xml
<c r="C5" s="3">
  <f>Assumptions!D12</f>
  <v></v>
</c>
```

### 6.3 不打开 Excel 定位输入区域

解包后，解码可疑输入单元格上的样式索引，以确定它们是否使用了模板的输入颜色：

1. 记录单元格的 `s` 值（如 `s="4"`）。
2. 在 `xl/styles.xml` 中找到 `<cellXfs>` 并查看第 5 条（索引 4）。
3. 记录其 `fontId`（如 `fontId="2"`）。
4. 在 `<fonts>` 中查看第 3 条（索引 2），检查是否有 `<color rgb="000000FF"/>`（蓝色）或其他输入标记。

如果模板使用命名范围作为输入字段，从 `xl/workbook.xml` 读取：
```xml
<definedNames>
  <definedName name="InputGrowthRate">Assumptions!$B$5</definedName>
  <definedName name="InputDiscountRate">Assumptions!$B$6</definedName>
</definedNames>
```

直接填写目标单元格（`Assumptions!B5`、`Assumptions!B6`）。

### 6.4 模板填写规则

- 只填写模板指定为输入的单元格，不要填写公式驱动的单元格。
- 填写时不要应用新样式，模板的格式就是交付物。
- 不要在模板数据区域内添加或删除行，除非模板明确有"在此追加"区域。
- 填写后，验证未引入公式错误：某些模板有输入验证公式，若输入了错误数据类型会产生 `#VALUE!`。

---

## 7. 绝对不能修改的文件

### 7.1 绝对禁止修改列表

| 文件/位置 | 原因 |
|-----------------|-----|
| `xl/vbaProject.bin` | 二进制 VBA 字节码。任何字节修改都会损坏宏项目。即使修改一个比特，宏也会无法加载。 |
| `xl/pivotCaches/pivotCacheDefinition*.xml` | 缓存定义将数据透视表绑定到其源数据。不同时更新对应的 `pivotTable*.xml` 就编辑它，会损坏数据透视表。 |
| `xl/pivotTables/*.xml` | 数据透视表 XML 与缓存定义及 Excel 加载时重建的内部状态紧密耦合。不要编辑。如果移行后数据透视表的源范围指向了错误数据，只更新缓存定义中的 `<cacheSource>` 范围，以及数据透视表中的 `ref` 属性——其他任何内容都不要改。 |
| `xl/slicers/*.xml` | 切片器连接到特定的缓存 ID 和数据透视字段。破坏这些连接会静默损坏文件。 |
| `xl/connections.xml` | 外部数据连接。编辑会破坏实时数据刷新。 |
| `xl/externalLinks/` | 外部工作簿链接。其中的二进制 `.bin` 文件不得修改。 |

### 7.2 有条件安全的文件（只更新特定属性）

| 文件 | 允许更新的内容 | 不能碰的内容 |
|------|--------------------|--------------------|
| `xl/charts/chartN.xml` | 行/列移位后的数据系列范围引用（`<numRef><f>`） | 图表类型、格式、布局 |
| `xl/tables/tableN.xml` | 添加行后 `<table>` 上的 `ref` 属性 | 列定义、样式信息 |
| `xl/pivotCaches/pivotCacheDefinition*.xml` | 源数据移位后 `<cacheSource><worksheetSource>` 上的 `ref` 属性 | 其他所有内容 |

---

## 8. 每次编辑后必须验证

永远不要跳过验证。即使公式改变一个字符，也可能引发级联错误。

```bash
# 打包
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx

# 静态公式验证（始终运行）
python3 SKILL_DIR/scripts/formula_check.py output.xlsx

# 动态验证（如有 LibreOffice 可用）
python3 SKILL_DIR/scripts/libreoffice_recalc.py output.xlsx /tmp/recalc.xlsx
python3 SKILL_DIR/scripts/formula_check.py /tmp/recalc.xlsx
```

如果 `formula_check.py` 报告任何错误：
1. 重新解包输出文件（这是打包后的版本）。
2. 在工作表 XML 中定位报告的单元格。
3. 修复 `<f>` 元素。
4. 重新打包并再次验证。

`formula_check.py` 报告零错误前不得交付文件。

---

## 9. 绝对规则摘要

| 规则 | 原因 |
|------|-----------|
| 不对已有文件使用 openpyxl `load_workbook` + `save` | 往返读写会破坏数据透视表、VBA、迷你图、切片器 |
| 不删除或重排 sharedStrings 中已有的 `<si>` 条目 | 会破坏所有引用该索引的单元格 |
| 不删除或重排 `<cellXfs>` 中已有的 `<xf>` 条目 | 会破坏所有使用该样式索引的单元格 |
| 不修改 `vbaProject.bin` | 二进制文件；任何修改都会破坏 VBA |
| 重命名工作表时不修改 `sheetId` | 内部 ID 是稳定的；修改它会破坏关系 |
| 不跳过编辑后验证 | 留下未发现的损坏引用 |
| 不修改超过必要范围的 XML 节点 | 额外修改存在引入细微损坏的风险 |
| 修改公式时将 `<v>` 清空为空字符串 | 防止过期的缓存值误导下游使用者 |
| sharedStrings 只追加 | 已有索引必须保持有效 |
| 样式集合只追加 | 已有样式索引必须保持有效 |
